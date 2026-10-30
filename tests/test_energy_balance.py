"""The hourly energy balance must hold in both modes."""
from __future__ import annotations

TOLERANCE = 1e-9


def test_supply_meets_demand_every_hour(runs):
    """Solar to load, battery, grid and unmet load must add up to the load."""
    for key, run in runs.items():
        hourly = run["hourly"]
        supply = (
            hourly["solar_to_load_kwh"]
            + hourly["battery_discharge_kwh"]
            + hourly["grid_import_kwh"]
            + hourly["unmet_kwh"]
        )
        residual = (supply - hourly["load_kwh"]).abs().max()
        assert residual < TOLERANCE, f"{key}: supply/demand mismatch of {residual}"


def test_brief_balance_form(runs):
    """The brief's form: solar_used + discharge + import = load - unmet + charge."""
    for key, run in runs.items():
        hourly = run["hourly"]
        left = hourly["solar_used_kwh"] + hourly["battery_discharge_kwh"] + hourly["grid_import_kwh"]
        right = hourly["load_kwh"] - hourly["unmet_kwh"] + hourly["battery_charge_kwh"]
        residual = (left - right).abs().max()
        assert residual < TOLERANCE, f"{key}: balance mismatch of {residual}"


def test_every_generated_unit_is_accounted_for(runs):
    """Generated solar is either used, stored, exported or wasted - nothing vanishes."""
    for key, run in runs.items():
        hourly = run["hourly"]
        accounted = (
            hourly["solar_to_load_kwh"]
            + hourly["battery_charge_kwh"]
            + hourly["exported_kwh"]
            + hourly["wasted_kwh"]
        )
        residual = (accounted - hourly["solar_kwh"]).abs().max()
        assert residual < TOLERANCE, f"{key}: solar accounting mismatch of {residual}"


def test_no_negative_energy(runs):
    """No energy component may go negative."""
    columns = [
        "load_kwh", "solar_kwh", "solar_to_load_kwh", "battery_charge_kwh",
        "battery_discharge_kwh", "exported_kwh", "wasted_kwh", "grid_import_kwh", "unmet_kwh",
    ]
    for key, run in runs.items():
        for column in columns:
            assert run["hourly"][column].min() >= -TOLERANCE, f"{key}: {column} went negative"


def test_battery_does_not_charge_and_discharge_in_the_same_hour(runs):
    """Charging and discharging are mutually exclusive within an hour."""
    for key, run in runs.items():
        hourly = run["hourly"]
        both = (hourly["battery_charge_kwh"] > TOLERANCE) & (hourly["battery_discharge_kwh"] > TOLERANCE)
        assert not both.any(), f"{key}: battery charged and discharged in the same hour"
