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

            result = dispatch_hour(load, generation, battery, outage, scenario["export_mode"],
                                   plan["reserve_kwh"] if planner is not None else None)
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
