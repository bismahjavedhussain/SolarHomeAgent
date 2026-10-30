# Build brief: Solar Home Agent (Pakistan): prototype v0

> **For Claude Code.** Read this whole file before writing any code. It explains who this is for, why it matters, the exact problem, and what to build. Plan first, then build in milestones, keeping the project runnable after each one.

---

## 0. Who you're building for, and the deadline

- **Owner:** Bismah Javed, 19, first-year BS Computer Science at COMSATS University Islamabad, Pakistan. She's a strong programmer: she built *Agentic-Arbiter* solo, which placed 2nd of 842 teams (nearly 4,000 participants, 50+ countries) at the FortyGuard Hackathon '26 and was featured by the UNEP-led Cool Coalition. **She's a beginner in energy systems**, so every explanation of energy concepts must be in plain language.
- **Why:** she's been shortlisted for the **IRENA Youth Forum 2027** (Abu Dhabi, January 2027; theme: *Grids, Storage and Flexibility for Renewable Energy Systems*). Her final application is due **today (30 Oct 2026)**. She'll describe this prototype honestly as "currently being built," show it in a 2-minute video, and link the public GitHub repo.
- **Time budget:** about 4–5 hours of building. Favour simple, readable, correct code over clever code. **The must-haves are Milestones 1–4 plus the docs (Milestone 6).** The Streamlit app (Milestone 5) is high value for the video if there's time.
- **Do NOT** write any of her IRENA application answers or her video script. Build the software and its documentation only.

---

## 1. The problem, in plain words

**Pakistan's rooftop solar is invisible and badly timed.**

- **At home:** solar panels make the most power around noon, when families need little of it. In the evening, when the sun is gone and the AC switches on, families buy power from the grid.
  - Most Pakistani solar homes **aren't registered for net metering**, so they **can't sell extra noon power**. Whatever isn't used right away is **wasted** (the inverter cuts back its output).
  - Homes registered under the new 2026 **net billing** rules get only about Rs 11 per unit they send to the grid, much less than the price of buying.
- **Price bands:** a home that stays at or under **200 units a month** (for 6 consecutive months) gets a cheap "protected" rate. Going over 200 even once makes the home "unprotected" for the next 6 months, and unprotected pricing is **non-telescopic**: the band the month reaches sets the price for *every* unit.
- **For the grid:** the grid can't see most of this solar, so demand forecasts are off. Official long-term demand forecasts have been criticised for leaving out rooftop solar, which leads to over-building power plants that are paid whether they run or not ("capacity payments"). That raises tariffs for everyone, including families without solar.

**What this prototype addresses:**
1. **Household (built and measured in v0):** an agent that reads the weather forecast and, for each hour, decides when to run flexible appliances, when to pre-cool, and how to use a battery if there is one, so the home uses more of its own solar, buys fewer grid units (especially in the evening), and stays under the 200-unit threshold where possible. **It refuses to change the plan when its forecast confidence is low**, and explains every decision in a plain-language message to the family.
2. **Grid (stretch demo only):** many homes' forecasts combined into one neighbourhood solar forecast *with a confidence band*. That's the "help the grid see it and trust it" idea.

### Credibility of the background claims (keep docs consistent with this)
| Claim | Strength | Notes |
|---|---|---|
| Huge rooftop solar, mostly unregistered | Strong | Estimates about 27–33 GW of small-scale solar; only about 7 GW net-metered (official, June 2026). Exact total uncertain. |
| Unregistered homes can't sell, so extra noon solar is wasted | Strong | Most systems don't exchange power with the grid. |
| Band pricing and 200-unit protected rule | Strong | 2026 tariff (S.R.O. 279(I)/2026). Rates may be revised. |
| Evening spike ("duck curve") stresses the grid | Strong | The regulator (NEPRA) cited it when making batteries mandatory for new solar and wind projects (Sept 2026). |
| Invisible solar distorts planning | Moderate–strong | National demand-forecast plan criticised for omitting rooftop solar; NEPRA warned over-optimistic forecasts raise tariffs. |
| Net billing pays about Rs 11/unit | Weak–moderate | Applies to *new* users from Feb 2026; existing users keep old terms until their 7-year contracts end; the rate and the rules are contested. **Not the headline claim.** |
| Share of solar homes with batteries | Unknown | Her survey tests this. |
| About 1 in 4–5 Pakistani households have some solar | Moderate | Gallup 2023 about 20%; PBS survey reported 2026 about 25%; census 2023 "access" 7.4% (different definition). |

The README should present the problem with careful wording ("estimates range…", "reported…") and **must not overclaim**.

---

## 2. What to build (scope of v0)

A **Python simulation** of a solar home in **Islamabad** for **one real summer month (June 2025)**, run twice:

- **Usual mode (baseline):** how the family behaves today.
- **Agent mode:** the agent plans each day from the forecast.

The two runs are compared under several **scenarios** (switches). Outputs: metrics, charts, a notification log, and (if time) a Streamlit page for the demo video.

### Scenario switches (all in `config/scenario.yaml`)
- `has_battery`: true / false
- `export_mode`: `none` (unregistered, so extra solar is wasted) | `net_billing` (extra solar sold at about Rs 11) | optionally `net_metering` (old 1:1 offset, for comparison only)
- `household`: `low_use` (about 150–200 units/month, protected-eligible, 1 AC) | `high_use` (about 400+ units/month, unprotected, 2 ACs)
- `solar_kw`: default 5
- `power_cuts`: list of daily outage windows (default: one hour at 20:00–21:00); `[]` allowed
- `usual_times`: usual start hours for the water motor, washing machine and iron (defaults below; will later be set from survey results)
- `month`: default 2025-06

Run a **scenario matrix** (battery × export_mode × household) and save the combined results.

---

## 3. Data

### 3.1 Real data (download once, cache to `data/`, then work offline)
- **Open-Meteo Historical Weather API** (free, no key). Verify the endpoint and parameters against the current Open-Meteo docs before relying on them:
  `https://archive-api.open-meteo.com/v1/archive?latitude=33.6844&longitude=73.0479&start_date=2025-06-01&end_date=2025-06-30&hourly=shortwave_radiation,temperature_2m,cloud_cover&timezone=Asia%2FKarachi`
  - Check the docs for how `shortwave_radiation` is aligned in time (Open-Meteo hourly radiation is typically the mean over the *preceding* hour), and handle it consistently.
- **Forecasts (for the agent's "what it thought would happen"):** prefer the **Open-Meteo Historical Forecast API**, which gives archived past forecasts. Again, verify against the docs:
  `https://historical-forecast-api.open-meteo.com/v1/forecast?latitude=33.6844&longitude=73.0479&start_date=2025-06-01&end_date=2025-06-30&hourly=shortwave_radiation,temperature_2m,cloud_cover&timezone=Asia%2FKarachi`
  - **Fallback** if it's unavailable or inconsistent: use the actual weather as the forecast, with confidence derived from cloud cover. **State clearly in the README and ASSUMPTIONS.md which approach was used.**
- Save raw responses as CSV in `data/`, and commit them so the repo runs offline.

### 3.2 Assumptions (all configurable; all listed in ASSUMPTIONS.md with "assumed" or a source)
| Item | Default |
|---|---|
| Solar output | `solar_kw × GHI/1000 × 0.80` (losses from heat, dust, wiring). No tilt model in v0. |
| Base load | 0.30 kW (00–06), 0.40 kW (06–18), 0.60 kW (18–24): fridge, fans, lights |
| AC | 1.5 kW per AC; runs when temp > 30°C during 13–17 (half duty) and 18–06 (full duty); duty scales linearly from 0.5 at 30°C to 1.0 at ≥40°C. `low_use` = 1 AC, `high_use` = 2 ACs. |
| Water motor | 0.75 kW × 1 h/day; usual start 19:00; allowed window for shifting 08:00–18:00 |
| Washing machine | 0.5 kW × 1 h on 4 days/week; usual start 18:00; allowed 09:00–17:00 |
| Iron | 1.0 kW × 0.5 h/day; usual start 20:00; allowed 09:00–18:00 |
| Pre-cooling | Extra 1.0 kWh of AC in 14:00–17:00 reduces evening AC by 0.6 kWh (assumed; label as a rough estimate) |
| Battery | 5 kWh; max charge/discharge 2.5 kW; 90% round-trip efficiency; min state of charge 20%; starts the month at 50% |
| Low-use scaling | Tune base load and AC so `low_use` baseline lands near 150–200 grid units/month and `high_use` near 400+ (report the actual values) |

### 3.3 Prices (approximate, configurable; label as approximate; to be calibrated from a real bill)
- **Protected** (month ≤ 200 units and protected-eligible): 1–100 units Rs 10.54; 101–200 units Rs 13.01 (2026 tariff, as reported).
- **Unprotected:** non-telescopic bands. Default lowest band Rs 22.44, highest band Rs 47.20. **Intermediate band values are placeholders** (linear interpolation across bands 1–100, 101–200, 201–300, 301–400, 401–500, 501–600, 601–700, 700+). Mark them as placeholders to be replaced from her real bill or the official notification.
- `taxes_multiplier`: default 1.0 (GST, duty and fuel adjustments are not included in v0; say so).
- Export value: `none` → Rs 0 (curtailed/wasted); `net_billing` → Rs 11/unit (reported, contested); `net_metering` → 1:1 offset (comparison only).
- Protected-status rule: if a protected-eligible home's month exceeds 200 units, price at unprotected rates and set the flag `loses_protected_status_for_6_months = true`.

---

## 4. The models

Hourly time step. For every hour, the **energy balance must hold**:

`solar_used + battery_discharge + grid_import = load + battery_charge` and `solar_generated = solar_used + battery_charge_from_solar + exported + wasted`

- **Solar model:** from GHI as above.
- **Home model:** base load + AC (temperature-driven) + flexible appliances (placed at usual times in baseline, at agent-chosen times in agent mode) + pre-cooling adjustments.
- **Battery model:** respects capacity, power limits, efficiency and min state of charge.
- **Power cuts:** during an outage window, grid import = 0. Load is served by solar plus battery; any remainder is **unmet load** (count "hours/kWh without backup").
- **Export handling:** surplus after load and battery charging is either wasted (`none`) or exported (`net_billing`).

### Baseline ("usual") behaviour
- Flexible appliances at usual times.
- Battery (if any) behaves like a simple inverter: solar first, charge from surplus, discharge whenever load > solar until min state of charge. **No forecast, no reserve planning.**
- No pre-cooling.

---

## 5. The agent (simple, explainable rules; no ML needed)

Every evening at 20:00 it plans **tomorrow** using that day's forecast. Next day it executes, then checks itself.

1. **Predict** tomorrow's hourly solar and load from the forecast.
2. **Confidence / margin** (the same idea as Agentic-Arbiter: the margin is learned from its own past errors):
   - Keep a rolling history of `forecast_solar − actual_solar` per hour of day.
   - `margin[h]` = 80th percentile of absolute past errors for hour `h` (once ≥ 5 days of history exist). Before that, use a cloud-cover-based margin (e.g. `predicted_solar × cloud_cover_fraction`) and say so.
   - `conservative_surplus[h] = predicted_solar[h] − margin[h] − predicted_base_and_ac_load[h]`.
   - Daily confidence (0–100%) for messages, e.g. derived from margin relative to predicted solar.
3. **Shift flexible appliances:** place each into the allowed-window hour(s) with the largest conservative surplus that can cover its power. **If no hour qualifies, refuse:** keep the usual time and log the reason ("cloudy forecast, not confident enough to move it").
4. **Pre-cool:** if tomorrow's forecast evening temperature ≥ 35°C and conservative surplus in 14:00–17:00 can cover 1 kWh, schedule pre-cooling.
5. **Battery plan** (if any):
   - Charge from surplus first (never export to the grid while the battery isn't full).
   - Hold a **reserve** before the evening: expected evening deficit plus any power-cut energy need, increased when confidence is low.
   - Don't discharge during the day below the reserve.
   - Before a scheduled power cut, keep enough charge to cover it.
6. **200-unit guard:**
   - For protected-eligible homes, track month-to-date grid units and project month-end.
   - If projected > 200, switch to "guard mode": shift more aggressively, use the reserve in the evening, pre-cool on more days.
   - Notify the family (e.g. "170 units used, 8 days left: running the motor at noon keeps you under 200").
7. **Messages:** every decision produces a plain-language notification with time, action, reason and confidence. Example:
   > 11:00 — Run the water motor now. Strong sun expected until 14:00 (confidence 85%).
   Save them to `results/notifications_<scenario>.csv`.
8. **Self-check:** after each day, compare predicted and actual solar, update the error history, and log the day's forecast error.

Keep the agent in one readable module with small, clearly named functions, so a beginner can follow it.

**Comment style (whole repo):**
- Keep comments brief: one short line, only where the code isn't obvious.
- Docstrings are one line.
- No essay-style comments or long explanations in code.
- Longer explanations go in HOW_IT_WORKS.md, not in the code.

---

## 6. Outputs

### Metrics (per scenario, usual vs agent) → `results/summary.csv` and `results/summary.json`
- Grid units bought in the month
- Evening (18:00–22:00) grid units
- Peak hourly grid draw (kW)
- Solar wasted (`none`) or exported (`net_billing`)
- Estimated bill (Rs), and whether protected status was kept
- Hours and kWh without backup during power cuts
- Number of agent refusals, and number of notifications
- Average forecast error, and the margin used

### Charts → `results/*.png`
1. **A typical day:** solar, load, grid import, export or waste, and battery state of charge, for usual vs agent, side by side or toggleable.
2. **The month:** cumulative grid units for usual vs agent, with a horizontal line at **200 units**.
3. **Scenario summary:** bar chart of monthly grid units and evening grid units across scenarios.

### Headline numbers
- Write `results/HEADLINE.md`, generated by code from `summary.json` (no hand-typed numbers): the 3–4 most important comparisons for the main scenario, each with "simulation" caveats.

---

## 7. Streamlit demo (Milestone 5, important for the video)
`app.py`:
- Sidebar switches: battery on/off, export mode, household, solar size, power cuts on/off.
- Main area:
  - headline metric cards (usual vs agent)
  - the day chart with a date picker
  - the month cumulative chart with the 200-unit line
  - a **notification feed** showing the agent's messages for the selected day
- Runs from the cached data and needs no API calls.
- Short "This is a simulation" note at the top.

---

## 8. Survey helper (Milestone 7)
Bismah is running a Google Forms survey. Its responses export as CSV from the linked Google Sheet. Write `survey/survey_summary.py`:

- **Input:** path to the CSV.
- **Match columns by keywords** in the question titles (the titles are long). Current questions:
  - "Which city is your home in?"
  - "…how many electricity units does your home use from the grid each month?" (Under 100 / 100-200 / 201-300 / 301-500 / Over 500)
  - "…how many hours of power cuts does your area get?" (None / Less than 2 hours / 2-4 hours / More than 4 hours)
  - "Does your home have solar panels?" (Yes / No / Planning to get solar)
  - "Is your solar system registered for net metering?…" (Yes / No / Don't know)
  - "Does your home have a battery that stores electricity?…" (Yes / No / Planning to get one)
  - "When does your family usually run the water motor and washing machine?…" (checkboxes, comma-separated in one cell)
  - "In 2026, Pakistan replaced net metering with net billing…" (checkboxes)
  - "What is the main reason your home does not have solar panels?"
  - "Imagine your home had solar and an app sent a message like…" (Usually / Sometimes / Rarely)
  - "Would you let an app automatically decide things…" (Yes / Only if it explains why it made each decision / No)
  - "What would you need to trust an app like that?" (open text)
- **Output:** `survey/survey_summary.md` with N, counts and percentages. Exclude blanks from denominators. Report "Don't know" for net metering as its own figure.
- **Suggest a main scenario** for `config/scenario.yaml`: most common battery and registration status among solar homes, most common usual appliance time, most common units band, typical power-cut hours.
- Include a short "small, non-representative sample" caveat in the output.
- Never print or store any personal data.

---

## 9. Stretch (only if everything else is done): neighbourhood forecast
Simulate about 50 homes with varied solar sizes (3–10 kW). Sum each home's forecast and margin into a neighbourhood forecast with a confidence band. Plot forecast ± band against actual for one week. Label it clearly as a concept demo of "helping the grid see rooftop solar."

---

## 10. Repo structure
```
solar-home-agent-pk/
  README.md            # problem, what v0 does, how to run, results (from HEADLINE.md), limits, next steps
  ASSUMPTIONS.md       # every number + source or "assumed"/"placeholder"
  HOW_IT_WORKS.md      # beginner-friendly explanation of the energy concepts and the agent, for Bismah
  requirements.txt     # pandas, numpy, requests, matplotlib, pyyaml, streamlit, pytest
  config/scenario.yaml
  data/                # cached weather + forecast CSVs (committed)
  src/
    fetch_weather.py   # download + cache; offline-first
    solar.py  home.py  battery.py  tariff.py
    baseline.py  agent.py  simulate.py  metrics.py  plots.py
  app.py               # Streamlit demo
  survey/survey_summary.py
  results/             # generated outputs
  tests/               # pytest
```
Single command to reproduce everything, e.g. `python -m src.simulate --all`, which writes everything in `results/`.

---

## 11. Correctness checks (write as pytest tests and run them)
- The energy balance holds every hour (within a small tolerance) in both modes.
- Battery state of charge always stays within [min_soc, capacity]; power limits are never exceeded.
- There is no grid import during power-cut windows.
- Flexible appliances are always scheduled inside their allowed windows, and each runs the required duration.
- Tariff: protected vs unprotected switching at 200 units; non-telescopic band pricing; export values per mode.
- The agent never exports while the battery is below full (when a battery exists).
- Simulation results are deterministic (same inputs give the same outputs).

---

## 12. Honesty rules (non-negotiable)
- Everything is a **simulation** with stated assumptions. **No claims of real-world savings.**
- **Every number in the README and HEADLINE.md comes from generated results**, not typed by hand.
- Approximate or placeholder values are labelled as such in ASSUMPTIONS.md and in the app.
- If an API or data source fails or differs from what this brief says, **say so plainly** and use the documented fallback. Don't invent data.
- Don't present the Rs 11 net-billing rate or tariff placeholders as certain.

---

## 13. How to work
1. **Read this file fully.** Briefly check the environment (Windows, Python version) and confirm the Open-Meteo endpoints work.
2. **Write a plan first:** milestones, files, key design choices, risks. Show it to Bismah before coding. Ask questions **only** if something blocks you; otherwise pick sensible defaults from this brief and note them.
3. **Build in milestones.** After each one, run it, show the output, and briefly explain in plain language what was added:
   - **M1:** fetch and cache data, plus a quick plot of solar vs temperature for a few days.
   - **M2:** solar, home, battery and tariff models, plus the baseline simulation and tests.
   - **M3:** the agent (rules, margin, refusals, 200-unit guard, messages), plus tests.
   - **M4:** metrics, the scenario matrix, charts, HEADLINE.md.
   - **M5:** Streamlit app.
   - **M6:** README, ASSUMPTIONS.md, HOW_IT_WORKS.md.
   - **M7:** survey helper.
   - **Stretch:** neighbourhood forecast.
4. Commit after each milestone with a clear message. Initialise git. **No secrets** (none are needed).
5. **At the end, give Bismah:**
   - A plain-language walkthrough of how the agent decides, short enough to explain in 60 seconds.
   - What v0 does and does **not** do.
   - The headline results for the main scenario, with caveats.
   - A suggested 30–40-second screen-recording flow of the Streamlit app for her video (which switches to flip, which chart to show, which notification to read).
   - The exact commands to rerun after she updates `config/scenario.yaml` from her survey results.
   - Steps to push the repo to GitHub as a public repo.
