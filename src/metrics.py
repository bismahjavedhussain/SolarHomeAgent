"""Summarise one simulated month into the numbers the brief asks for."""
from __future__ import annotations

import pandas as pd

from .tariff import estimate_bill

EVENING_START, EVENING_END = 18, 22


def summarise(run: dict, config: dict, scenario: dict) -> dict:
    """Turn an hourly run into monthly metrics, including the estimated bill."""
    hourly: pd.DataFrame = run["hourly"]
    evening = hourly[(hourly["hour"] >= EVENING_START) & (hourly["hour"] < EVENING_END)]
    outage = hourly[hourly["in_outage"]]

    import_units = hourly["grid_import_kwh"].sum()
    export_units = hourly["exported_kwh"].sum()
    # Unmet load must be reported with grid units: a home that goes dark looks artificially frugal.
    load_served = hourly["load_kwh"].sum() - hourly["unmet_kwh"].sum()
    bill = estimate_bill(
        import_units, export_units, scenario["export_mode"],
        run["profile"]["protected_eligible"], config["tariff"],
    )

    planner = run.get("planner")
    return {
        "grid_units_month": round(import_units, 1),
        "evening_grid_units": round(evening["grid_import_kwh"].sum(), 1),
        "peak_grid_kw": round(hourly["grid_import_kwh"].max(), 2),
        "load_wanted_kwh": round(hourly["load_kwh"].sum(), 1),
        "load_served_kwh": round(load_served, 1),
        "grid_units_per_100kwh_served": round(100 * import_units / max(1e-9, load_served), 1),
        "solar_generated_kwh": round(hourly["solar_kwh"].sum(), 1),
        "solar_used_kwh": round(hourly["solar_used_kwh"].sum(), 1),
        "solar_wasted_kwh": round(hourly["wasted_kwh"].sum(), 1),
        "solar_exported_kwh": round(export_units, 1),
        "self_consumption_pct": round(
            100 * hourly["solar_used_kwh"].sum() / max(1e-9, hourly["solar_kwh"].sum()), 1
        ),
        "bill_rs": round(bill["bill_rs"], 0),
        "energy_cost_rs": round(bill["energy_cost_rs"], 0),
        "fixed_charge_rs": round(bill["fixed_charge_rs"], 0),
        "export_credit_rs": round(bill["export_credit_rs"], 0),
        "pricing": bill["pricing"],
        "protected_kept": bill["protected_kept"],
        "loses_protected_status_for_6_months": bill["loses_protected_status_for_6_months"],
        "crosses_protected_limit": bill["loses_protected_status_for_6_months"],
        "unmet_kwh": round(outage["unmet_kwh"].sum(), 2),
        "unmet_hours": int((outage["unmet_kwh"] > 1e-6).sum()),
        "notifications": len(run["notifications"]),
        "refusals": run["refusals"],
        "mean_forecast_error_wm2": round(planner.mean_forecast_error(), 1) if planner else None,
        "mean_margin_kw": round(planner.mean_margin_kw(), 3) if planner else None,
        "promises_made": len(planner.promises) if planner else 0,
        "promises_kept_pct": planner.promises_kept_pct() if planner else None,
        "suggestions_followed_pct": planner.followed_pct() if planner else None,
        "guard_days": planner.guard_days if planner else 0,
    }
