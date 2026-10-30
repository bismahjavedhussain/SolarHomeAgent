"""Summarise the Google Forms survey export into survey/survey_summary.md.

Matches columns by keywords because the question titles are long. Never prints personal data.
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import pandas as pd

OUT_PATH = Path(__file__).resolve().parent / "survey_summary.md"

# Columns are found by keyword, so small edits to question wording still match.
QUESTIONS = {
    "city": ["which city"],
    "units": ["electricity units", "units does your home"],
    "power_cuts": ["power cuts", "hours of power cut"],
    "has_solar": ["have solar panels", "home have solar"],
    "net_metering": ["net metering", "registered for net"],
    "battery": ["battery that stores", "have a battery"],
    "appliance_times": ["water motor", "usually run the water"],
    "net_billing_awareness": ["net billing", "replaced net metering"],
    "no_solar_reason": ["main reason", "does not have solar"],
    "would_follow": ["sent a message", "imagine your home had solar"],
    "would_automate": ["automatically decide", "let an app automatically"],
    "trust": ["need to trust", "what would you need"],
}

# Anything that looks like a person rather than an answer is dropped before analysis.
PERSONAL_HINTS = ["email", "name", "phone", "contact", "address", "timestamp"]

MULTI_SELECT = {"appliance_times", "net_billing_awareness"}

# Naming a town with one respondent can identify them in a sample this small,
# so answers below this count are pooled for free-text-ish questions.
SMALL_CELL = 3
POOLED = {"city": "Other cities", "no_solar_reason": "Other reasons"}


def find_columns(frame: pd.DataFrame) -> dict[str, str]:
    """Map each question key to the first matching column title."""
    found = {}
    for key, keywords in QUESTIONS.items():
        for column in frame.columns:
            lowered = str(column).lower()
            if any(keyword in lowered for keyword in keywords):
                found[key] = column
                break
    return found


def drop_personal_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Remove any column that could carry personal data."""
    keep = [c for c in frame.columns if not any(hint in str(c).lower() for hint in PERSONAL_HINTS)]
    return frame[keep]


def tally(frame: pd.DataFrame, column: str | None, split: bool = False) -> tuple[Counter, int]:
    """Count answers, excluding blanks from the denominator."""
    if column is None or column not in frame.columns:
        return Counter(), 0
    answers = frame[column].dropna().astype(str).str.strip()
    answers = answers[answers != ""]
    if not split:
        return Counter(answers), len(answers)
    counts: Counter = Counter()
    for cell in answers:  # checkboxes arrive comma-separated in one cell
        for part in (p.strip() for p in cell.split(",")):
            if part:
                counts[part] += 1
    return counts, len(answers)


def pool_small_cells(counts: Counter, label: str) -> Counter:
    """Pool answers given by fewer than SMALL_CELL people, so no one is pinpointable."""
    kept, pooled = Counter(), 0
    for answer, count in counts.items():
        if count < SMALL_CELL:
            pooled += count
        else:
            kept[answer] = count
    if pooled:
        kept[f"{label} ({pooled} people, pooled)"] = pooled
    return kept


def format_counts(counts: Counter, responded: int, note: str = "") -> list[str]:
    """Render counts as 'X of N' plus the share of those who answered."""
    if not responded:
        return ["_No responses to this question yet._", ""]
    lines = ["| Answer | Count | Share of those who answered |", "|---|---|---|"]
    for answer, count in counts.most_common():
        lines.append(f"| {answer} | **{count} of {responded}** | {100 * count / responded:.0f}% |")
    lines.append("")
    lines.append(f"_Answered by {responded} of the respondents.{(' ' + note) if note else ''}_")
    lines.append("")
    return lines


def most_common(counts: Counter) -> str | None:
    """The single most common answer, if there is one."""
    return counts.most_common(1)[0][0] if counts else None


def suggest_scenario(frame: pd.DataFrame, columns: dict[str, str]) -> list[str]:
    """Suggest config/scenario.yaml settings from what solar homes reported."""
    solar_column = columns.get("has_solar")
    solar_homes = frame
    if solar_column:
        solar_homes = frame[frame[solar_column].astype(str).str.strip().str.lower().str.startswith("yes")]

    battery_counts, battery_n = tally(solar_homes, columns.get("battery"))
    metering_counts, metering_n = tally(solar_homes, columns.get("net_metering"))
    units_counts, _ = tally(frame, columns.get("units"))
    cuts_counts, _ = tally(frame, columns.get("power_cuts"))
    times_counts, _ = tally(frame, columns.get("appliance_times"), split=True)

    battery_answer = most_common(battery_counts)
    metering_answer = most_common(metering_counts)
    has_battery = str(battery_answer).lower().startswith("yes") if battery_answer else None
    registered = str(metering_answer).lower().startswith("yes") if metering_answer else None

    lines = [
        "## Suggested scenario settings",
        "",
        f"Based on the **{len(solar_homes)} respondents who reported having solar**"
        f"{' (of ' + str(len(frame)) + ' in total)' if solar_column else ''}.",
        "",
        "| Setting | Suggested | Based on |",
        "|---|---|---|",
    ]
    if has_battery is not None:
        lines.append(f"| `has_battery` | `{str(has_battery).lower()}` | most common answer: {battery_answer} "
                     f"({battery_n} answered) |")
    if registered is not None:
        export_mode = "net_billing" if registered else "none"
        # "Don't know" is treated as unregistered: a registered home normally knows it is.
        reason = (f"most common answer was \"{metering_answer}\", treated as not registered, since a "
                  f"home that is registered normally knows it" if "know" in str(metering_answer).lower()
                  else f"most common answer: {metering_answer}")
        lines.append(f"| `export_mode` | `{export_mode}` | {reason} ({metering_n} answered) |")
    if units_counts:
        band = most_common(units_counts)
        lines.append(f"| `household` | see note below | most common units band: {band} |")
    if cuts_counts:
        lines.append(f"| `power_cuts` | see note below | most common: {most_common(cuts_counts)} |")
    if times_counts:
        lines.append(f"| `usual_times` | see note below | most common time: {most_common(times_counts)} |")

    lines += [
        "",
        "Notes for translating these into the config:",
        "",
        "- `household` is `low_use` for bands up to 200 units and `high_use` above that. If the most "
        "common band is 201-300, consider setting `calibration.low_use_target_units` from a real bill "
        "instead of switching profile.",
        "- `power_cuts` takes hour windows, for example `[[20, 21]]` for one evening hour. Convert the "
        "reported duration into the hours your area actually loses.",
        "- `usual_times` takes a start hour per appliance, for example `water_motor: 19`.",
        "",
        "After editing `config/scenario.yaml`, rerun everything with:",
        "",
        "```bash",
        "python -m src.simulate --all --calibrate",
        "```",
        "",
    ]
    return lines


def build_report(frame: pd.DataFrame) -> str:
    """Assemble the whole markdown report."""
    frame = drop_personal_columns(frame)
    columns = find_columns(frame)
    total = len(frame)

    missing = [key for key in QUESTIONS if key not in columns]
    # Counted here so the caveat quotes a computed figure rather than a typed one.
    city_column = columns.get("city")
    TWIN_CITY = 0
    if city_column:
        cities = frame[city_column].dropna().astype(str).str.strip().str.lower()
        TWIN_CITY = int(cities.isin(["islamabad", "rawalpindi"]).sum())

    lines = [
        "# Survey summary",
        "",
        "<!-- Generated by survey/survey_summary.py. Do not edit by hand. -->",
        "",
        f"**Responses: {total}**",
        "",
        f"> **A small, non-representative sample, and I want to say exactly how.** These "
        f"{total} households came from my own student network and are mostly better-off homes; "
        f"{TWIN_CITY} of the {total} are in Islamabad or Rawalpindi. They are not a random or "
        f"weighted sample of Pakistani households, so every figure below describes only the people "
        f"who answered. **Next I want to survey beyond my own network, including renters and "
        f"families with no solar at all**, because those are the homes this is least likely to fit "
        f"today. These answers are used to choose plausible settings for the simulation, not to "
        f"make claims about the country.",
        "",
    ]
    if missing:
        lines += [f"_Questions not found in this export: {', '.join(missing)}._", ""]

    sections = [
        ("city", "Which city", ""),
        ("units", "Monthly grid units", ""),
        ("power_cuts", "Hours of power cuts", ""),
        ("has_solar", "Has solar panels", ""),
        ("net_metering", "Registered for net metering", "Counted among solar homes only."),
        ("battery", "Has a battery", "Counted among solar homes only."),
        ("appliance_times", "When the water motor and washing machine usually run", "Multiple answers allowed."),
        ("net_billing_awareness", "Awareness of the 2026 net-billing change", "Multiple answers allowed."),
        ("no_solar_reason", "Main reason for not having solar", ""),
        ("would_follow", "Would follow a message like this", ""),
        ("would_automate", "Would allow automatic decisions", ""),
    ]

    solar_column = columns.get("has_solar")
    solar_homes = frame
    if solar_column:
        solar_homes = frame[frame[solar_column].astype(str).str.strip().str.lower().str.startswith("yes")]

    for key, title, note in sections:
        lines.append(f"## {title}")
        lines.append("")
        source = solar_homes if key in ("net_metering", "battery") else frame
        counts, responded = tally(source, columns.get(key), split=key in MULTI_SELECT)
        if key in POOLED:
            counts = pool_small_cells(counts, POOLED[key])
        if key == "net_metering" and counts:
            unsure = sum(c for a, c in counts.items() if "know" in a.lower())
            note = (note + f" **{unsure} of {responded} said they do not know** whether they are "
                    f"registered"
                    + (", which is itself a finding about how visible registration is."
                       if unsure else
                       " - so in this sample, solar owners did know their own status.")).strip()
        lines += format_counts(counts, responded, note)

    if "trust" in columns:
        answers = frame[columns["trust"]].dropna().astype(str).str.strip()
        answers = answers[answers != ""]
        lines += [
            "## What people would need in order to trust the app",
            "",
            f"_{len(answers)} people answered this free-text question. Responses are not reproduced "
            "here, to avoid republishing anything identifying. Read them in the spreadsheet._",
            "",
        ]

    lines += suggest_scenario(frame, columns)
    return "\n".join(lines) + "\n"


def main() -> None:
    """Read the survey CSV and write the markdown summary."""
    parser = argparse.ArgumentParser(description="Summarise the survey CSV export.")
    parser.add_argument("csv", help="path to the Google Forms CSV export")
    parser.add_argument("--out", default=str(OUT_PATH), help="where to write the summary")
    args = parser.parse_args()

    frame = pd.read_csv(args.csv)
    report = build_report(frame)
    Path(args.out).write_text(report, encoding="utf-8")
    print(f"{len(frame)} responses -> {args.out}")


if __name__ == "__main__":
    main()
