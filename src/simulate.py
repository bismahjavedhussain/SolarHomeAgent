"""Run the month hour by hour, in usual mode and agent mode, across the scenario matrix."""
from __future__ import annotations

import argparse
import itertools
import json

import pandas as pd

from .agent import AgentPlanner
from .baseline import usual_plan
from .battery import Battery
from .fetch_weather import ROOT, load_config, load_weather
from .home import ac_component_kw, build_appliances, fixed_load_kw
from .metrics import summarise
from .solar import solar_kw

RESULTS_DIR = ROOT / "results"
CALIBRATION_PATH = ROOT / "config" / "calibration.json"
EXPORT_MODES = ["none", "net_billing", "net_metering"]


def dispatch_hour(load_kwh: float, solar_kwh: float, battery: Battery | None, in_outage: bool,
                  export_mode: str, reserve_floor: float | None = None) -> dict:
    """Resolve one hour: solar first, then battery, then grid. Returns every energy component."""
    solar_to_load = min(solar_kwh, load_kwh)
    surplus = solar_kwh - solar_to_load
    unserved = load_kwh - solar_to_load

    battery_charge = 0.0
    if battery is not None and surplus > 0:
        battery_charge = battery.charge(surplus)
        surplus -= battery_charge

    # The grid is down during an outage, so nothing can be exported then.
    can_export = export_mode in ("net_billing", "net_metering") and not in_outage
    exported = surplus if can_export else 0.0
    wasted = 0.0 if can_export else surplus

    battery_discharge = 0.0
    if battery is not None and unserved > 0:
        floor = None if in_outage else reserve_floor  # the reserve exists to be spent in an outage
        battery_discharge = battery.discharge(unserved, floor_kwh=floor)
        unserved -= battery_discharge

    grid_import = 0.0 if in_outage else unserved
    unmet = unserved if in_outage else 0.0

    return {
        "load_kwh": load_kwh,
        "solar_kwh": solar_kwh,
        "solar_to_load_kwh": solar_to_load,
        "solar_used_kwh": solar_to_load + battery_charge,
        "battery_charge_kwh": battery_charge,
        "battery_discharge_kwh": battery_discharge,
        "exported_kwh": exported,
        "wasted_kwh": wasted,
        "grid_import_kwh": grid_import,
        "unmet_kwh": unmet,
        "soc_kwh": battery.soc_kwh if battery is not None else 0.0,
    }


def in_power_cut(hour: int, windows: list) -> bool:
    """True if this hour falls inside any configured outage window."""
    return any(start <= hour < end for start, end in windows)


def household_profile(config: dict, household: str) -> dict:
    """Household settings, with the calibrated load scale applied when one exists."""
    profile = dict(config["households"][household])
    if CALIBRATION_PATH.exists():
        calibration = json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))
        profile["load_scale"] = calibration.get("load_scale", {}).get(household, profile["load_scale"])
    return profile


def apply_precooling(load_kwh: float, hour: int, plan: dict, ac_kwh: float) -> float:
    """Add pre-cooling in the afternoon and take the assumed relief off the evening AC."""
    load_kwh += plan["precool_kwh"].get(hour, 0.0)
    relief = min(plan["evening_relief_kwh"].get(hour, 0.0), ac_kwh)
    return load_kwh - relief


def run_month(config: dict, scenario: dict, mode: str, weather: tuple | None = None,
              profile: dict | None = None) -> dict:
    """Simulate one month in 'usual' or 'agent' mode; returns hourly rows, notifications and the planner."""
    actual, forecast = weather if weather is not None else load_weather(config)
    if profile is None:
        profile = household_profile(config, scenario["household"])
    appliances = build_appliances(config)
    battery = Battery(config["battery"]) if scenario["has_battery"] else None
    cuts = config["power_cuts"] if scenario.get("power_cuts", True) else []
    days_in_month = len(actual) // 24

    planner = AgentPlanner(config, scenario, profile, appliances) if mode == "agent" else None
    rows, notifications, month_units = [], [], 0.0

    for day, day_actual in actual.groupby(actual["time"].dt.date, sort=True):
        timestamp = pd.Timestamp(day)
        day_forecast = forecast[forecast["time"].dt.date == day]

        if planner is not None:
            plan = planner.plan_day(timestamp, day_forecast, month_units, days_in_month)
        else:
            plan = usual_plan(appliances, timestamp)
        notifications.extend(plan["notifications"])

        for _, record in day_actual.iterrows():
            hour = record["time"].hour
            ac_kwh = ac_component_kw(hour, record["temp_c"], profile, config)
            load = fixed_load_kw(hour, record["temp_c"], profile, config) + plan["appliance_kw"].get(hour, 0.0)
            load = apply_precooling(load, hour, plan, ac_kwh)

            generation = solar_kw(record["ghi_wm2"], scenario["solar_kw"], config["solar"]["derate"])
            outage = in_power_cut(hour, cuts)

            reserve_floor = plan["reserve_kwh"].get(hour) if planner is not None else None
            result = dispatch_hour(load, generation, battery, outage, scenario["export_mode"], reserve_floor)
            result.update(time=record["time"], hour=hour, temp_c=record["temp_c"], in_outage=outage)
            rows.append(result)
            month_units += result["grid_import_kwh"]

        if planner is not None:
            planner.learn_from_day(day_actual, day_forecast)

    return {
        "hourly": pd.DataFrame(rows),
        "notifications": notifications,
        "refusals": planner.refusals if planner is not None else 0,
        "planner": planner,
        "profile": profile,
    }


def scenario_key(scenario: dict) -> str:
    """Short filename-safe name for a scenario."""
    battery = "battery" if scenario["has_battery"] else "nobattery"
    return f"{scenario['household']}_{battery}_{scenario['export_mode']}"


def base_scenario(config: dict, **overrides) -> dict:
    """A scenario dict from the config defaults, with optional overrides."""
    scenario = {
        "has_battery": config["has_battery"],
        "export_mode": config["export_mode"],
        "household": config["household"],
        "solar_kw": config["solar_kw"],
        "power_cuts": True,
    }
    scenario.update(overrides)
    return scenario


def main_scenario(config: dict) -> dict:
    """The scenario reported in HEADLINE.md."""
    return base_scenario(config, **config["main_scenario"])


def build_scenarios(config: dict) -> list[dict]:
    """The full matrix: household x battery x export mode."""
    return [
        base_scenario(config, household=household, has_battery=battery, export_mode=export)
        for household, battery, export in itertools.product(config["households"], [False, True], EXPORT_MODES)
    ]


def calibrate(config: dict, weather: tuple | None = None, verbose: bool = True) -> dict:
    """Find the load scale that puts a household's usual-mode grid units on its configured target."""
    weather = weather if weather is not None else load_weather(config)
    targets = {"low_use": config["calibration"]["low_use_target_units"]}
    scales, achieved = {}, {}

    for household, target in targets.items():
        reference = base_scenario(config, household=household, has_battery=False, export_mode="none")

        def units_at(scale: float) -> float:
            profile = dict(config["households"][household], load_scale=scale)
            run = run_month(config, reference, "usual", weather, profile=profile)
            return run["hourly"]["grid_import_kwh"].sum()

        low, high = 0.0, 3.0
        for _ in range(30):  # bisection; grid units rise monotonically with the load scale
            mid = (low + high) / 2
            low, high = (mid, high) if units_at(mid) < target else (low, mid)
        scale = round((low + high) / 2, 4)
        scales[household] = scale
        achieved[household] = round(units_at(scale), 1)
        if verbose:
            print(f"  calibrated {household}: load_scale={scale}  "
                  f"target={target} units  achieved={achieved[household]} units")

    payload = {
        "load_scale": scales,
        "target_units": targets,
        "achieved_units": achieved,
        "note": "Assumed target, not measured. Update calibration.low_use_target_units from a real bill.",
    }
    CALIBRATION_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def run_pair(config: dict, scenario: dict, weather: tuple) -> dict:
    """Run one scenario in both modes and summarise each."""
    runs = {mode: run_month(config, scenario, mode, weather) for mode in ("usual", "agent")}
    return {
        "scenario": scenario,
        "runs": runs,
        "metrics": {mode: summarise(run, config, scenario) for mode, run in runs.items()},
    }


def typical_day(hourly: pd.DataFrame) -> str:
    """The day whose total solar is closest to the month's median, as a stand-in for a normal day."""
    daily = hourly.groupby(hourly["time"].dt.date)["solar_kwh"].sum()
    return str((daily - daily.median()).abs().idxmin())


def save_notifications(notifications: list[dict], key: str) -> None:
    """Write one scenario's agent messages to CSV."""
    frame = pd.DataFrame(notifications)
    frame.to_csv(RESULTS_DIR / f"notifications_{key}.csv", index=False)


def write_headline(summary: dict, config: dict) -> str:
    """Generate HEADLINE.md from summary.json; every number comes from the results."""
    key = summary["main_scenario_key"]
    entry = summary["scenarios"][key]
    usual, agent, scenario = entry["usual"], entry["agent"], entry["scenario"]
    threshold = config["agent"]["guard_threshold_units"]

    def change(metric: str, unit: str = "units") -> str:
        before, after = usual[metric], agent[metric]
        delta = before - after
        pct = f" ({100 * delta / before:.0f}% less)" if before else ""
        return f"**{before:g} -> {after:g} {unit}**, a fall of {delta:.1f}{pct}"

    battery = "with a battery" if scenario["has_battery"] else "with no battery"
    export = {"none": "not registered to sell power (surplus is wasted)",
              "net_billing": "on net billing", "net_metering": "on net metering (comparison only)"}

    lines = [
        "# Headline results",
        "",
        "<!-- Generated by src/simulate.py from results/summary.json. Do not edit by hand. -->",
        "",
        f"**Simulated month:** {summary['month']} - **Location:** {config['location']['name']}",
        f"**Main scenario:** a {scenario['household'].replace('_', ' ')} home, {scenario['solar_kw']} kW of panels, "
        f"{battery}, {export[scenario['export_mode']]}.",
        "",
        "These are results from a **simulation**, not measurements from a real home. "
        "They depend on the assumptions in ASSUMPTIONS.md, several of which are rough estimates.",
        "",
        "## What the agent changed",
        "",
        f"1. **Units bought from the grid:** {change('grid_units_month')}.",
        f"2. **Evening units (18:00-22:00), the hours that strain the grid:** {change('evening_grid_units')}.",
        f"3. **Highest single-hour grid draw:** {change('peak_grid_kw', 'kW')}.",
        f"4. **Power-cut shortfall:** {change('unmet_kwh', 'kWh')} "
        f"({usual['unmet_hours']} hours without backup, down to {agent['unmet_hours']}).",
        "",
        "### Reading those numbers fairly",
        "",
        f"During a power cut a home with nothing left in the battery simply goes dark, and load it never "
        f"served never appears on the bill. So units bought must be read next to load actually served: "
        f"**{usual['load_served_kwh']:g} kWh usual vs {agent['load_served_kwh']:g} kWh agent**, out of "
        f"{agent['load_wanted_kwh']:g} kWh the home wanted. Per 100 kWh actually served, grid units go "
        f"**{usual['grid_units_per_100kwh_served']:g} -> {agent['grid_units_per_100kwh_served']:g}**.",
        "",
        f"Estimated bill: **Rs {usual['bill_rs']:,.0f} -> Rs {agent['bill_rs']:,.0f}** "
        f"on {usual['pricing']} pricing. Tariff values are approximate and partly placeholders.",
        "",
        "## How much the agent trusted itself",
        "",
        f"- Average day-ahead forecast error: **{agent['mean_forecast_error_wm2']} W/m2**; "
        f"average solar held back as a safety margin: **{agent['mean_margin_kw']} kW per hour**.",
        f"- The agent sent **{agent['notifications']} messages** and "
        f"**refused to move an appliance {agent['refusals']} times** because it was not confident enough.",
        "",
        "## Solar that still goes to waste",
        "",
        f"- Generated: **{agent['solar_generated_kwh']:g} kWh**. "
        f"Used on site: **{usual['solar_used_kwh']:g} -> {agent['solar_used_kwh']:g} kWh** "
        f"({usual['self_consumption_pct']}% -> {agent['self_consumption_pct']}% of generation).",
        f"- Still wasted: **{usual['solar_wasted_kwh']:g} -> {agent['solar_wasted_kwh']:g} kWh**. "
        "Most noon solar is still thrown away, because an unregistered home cannot sell it "
        "and a 5 kWh battery cannot hold a whole sunny day.",
        "",
        "## The 200-unit threshold",
        "",
    ]

    if agent["grid_units_month"] < threshold and usual["grid_units_month"] < threshold:
        lines.append(
            f"In this scenario both modes stay under the {threshold}-unit protected limit "
            f"({usual['grid_units_month']:g} and {agent['grid_units_month']:g} units), so the agent's guard mode "
            "was never needed. It is a safety net, not something this scenario demonstrates. "
            "Tests confirm it activates when a protected-eligible home is on course to cross."
        )
    elif usual["grid_units_month"] > threshold >= agent["grid_units_month"]:
        lines.append(
            f"Usual behaviour crosses the {threshold}-unit limit ({usual['grid_units_month']:g} units) "
            f"and the agent stays under it ({agent['grid_units_month']:g} units), keeping protected pricing."
        )
    else:
        lines.append(
            f"Both modes exceed the {threshold}-unit limit "
            f"({usual['grid_units_month']:g} and {agent['grid_units_month']:g} units), so this home pays "
            "unprotected rates either way."
        )

    lines += ["", "---", "", f"Reproduce with `python -m src.simulate --all`. "
              f"Full per-scenario numbers are in `results/summary.csv`."]
    text = "\n".join(lines) + "\n"
    (RESULTS_DIR / "HEADLINE.md").write_text(text, encoding="utf-8")
    return text


def run_all(config: dict, do_calibrate: bool = False, verbose: bool = True) -> dict:
    """Run every scenario in both modes, then write metrics, charts and HEADLINE.md."""
    from . import plots

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    weather = load_weather(config)
    if do_calibrate:
        if verbose:
            print("Calibrating household load scales:")
        calibrate(config, weather, verbose)

    target = main_scenario(config)
    target_key = scenario_key(target)
    scenarios_out, flat_rows, main_runs = {}, [], None

    for scenario in build_scenarios(config):
        key = scenario_key(scenario)
        pair = run_pair(config, scenario, weather)
        scenarios_out[key] = {"scenario": scenario, **pair["metrics"]}
        flat_rows.append({
            "scenario": key, "household": scenario["household"],
            "has_battery": scenario["has_battery"], "export_mode": scenario["export_mode"],
            **{f"{mode}_{name}": value for mode, metrics in pair["metrics"].items()
               for name, value in metrics.items()},
        })
        save_notifications(pair["runs"]["agent"]["notifications"], key)
        if key == target_key:
            main_runs = pair["runs"]
        if verbose:
            usual, agent = pair["metrics"]["usual"], pair["metrics"]["agent"]
            print(f"  {key:34s} grid {usual['grid_units_month']:6.1f} -> {agent['grid_units_month']:6.1f} u   "
                  f"evening {usual['evening_grid_units']:6.1f} -> {agent['evening_grid_units']:5.1f} u")

    summary = {
        "month": str(config["month"]),
        "location": config["location"]["name"],
        "main_scenario_key": target_key,
        "forecast_source": "Open-Meteo historical-forecast API, *_previous_day1 (day-ahead forecast)",
        "calibration": json.loads(CALIBRATION_PATH.read_text(encoding="utf-8")) if CALIBRATION_PATH.exists() else None,
        "scenarios": scenarios_out,
    }
    (RESULTS_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    frame = pd.DataFrame(flat_rows)
    frame.to_csv(RESULTS_DIR / "summary.csv", index=False)

    usual_hourly, agent_hourly = main_runs["usual"]["hourly"], main_runs["agent"]["hourly"]
    day = typical_day(agent_hourly)
    plots.day_chart(usual_hourly, agent_hourly, day, RESULTS_DIR / "day.png", target["export_mode"])
    plots.month_chart(usual_hourly, agent_hourly, config["agent"]["guard_threshold_units"],
                      RESULTS_DIR / "month.png")
    plots.scenario_chart(frame, RESULTS_DIR / "scenarios.png")
    write_headline(summary, config)

    if verbose:
        print(f"\nwrote results/summary.csv, summary.json, HEADLINE.md, "
              f"day.png (typical day {day}), month.png, scenarios.png")
        print(f"wrote {len(scenarios_out)} notification logs")
    return summary


def main() -> None:
    """Command line entry point."""
    parser = argparse.ArgumentParser(description="Simulate a solar home in usual and agent modes.")
    parser.add_argument("--all", action="store_true", help="run every scenario and write all results")
    parser.add_argument("--calibrate", action="store_true", help="recalibrate household load scales first")
    parser.add_argument("--scenario", help="run a single scenario by key and print its metrics")
    args = parser.parse_args()

    config = load_config()
    if args.scenario:
        matches = [s for s in build_scenarios(config) if scenario_key(s) == args.scenario]
        if not matches:
            raise SystemExit(f"unknown scenario '{args.scenario}'")
        weather = load_weather(config)
        for mode, metrics in run_pair(config, matches[0], weather)["metrics"].items():
            print(f"\n[{mode}]")
            for name, value in metrics.items():
                print(f"  {name:32s} {value}")
        return
    if args.calibrate and not args.all:
        calibrate(config, load_weather(config))
        return
    run_all(config, do_calibrate=args.calibrate)


if __name__ == "__main__":
    main()
