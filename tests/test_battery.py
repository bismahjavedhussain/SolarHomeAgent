"""The battery must stay inside its capacity, charge level and power limits."""
from __future__ import annotations

import pytest

from src.battery import Battery

TOLERANCE = 1e-9


def test_state_of_charge_stays_in_range(runs, config):
    """Stored energy never drops below the minimum or exceeds capacity."""
    cfg = config["battery"]
    floor = cfg["min_soc_frac"] * cfg["capacity_kwh"]
    for key, run in runs.items():
        soc = run["hourly"]["soc_kwh"]
        if soc.max() == 0.0:
            continue  # no battery in this scenario
        assert soc.min() >= floor - TOLERANCE, f"{key}: fell below minimum charge ({soc.min()})"
        assert soc.max() <= cfg["capacity_kwh"] + TOLERANCE, f"{key}: exceeded capacity ({soc.max()})"


def test_power_limits_are_respected(runs, config):
    """Hourly charge and discharge never exceed the rated power."""
    cfg = config["battery"]
    for key, run in runs.items():
        hourly = run["hourly"]
        assert hourly["battery_charge_kwh"].max() <= cfg["max_charge_kw"] + TOLERANCE, f"{key}: charge too fast"
        assert hourly["battery_discharge_kwh"].max() <= cfg["max_discharge_kw"] + TOLERANCE, f"{key}: discharge too fast"


def test_charging_cannot_exceed_headroom(config):
    """A full battery accepts nothing more."""
    battery = Battery(config["battery"])
    for _ in range(20):
        battery.charge(100.0)
    assert battery.is_full
    assert battery.charge(100.0) == pytest.approx(0.0)
    assert battery.soc_kwh <= config["battery"]["capacity_kwh"] + TOLERANCE


def test_discharge_stops_at_the_floor(config):
    """An empty battery delivers nothing more, and respects a reserve floor."""
    battery = Battery(config["battery"])
    for _ in range(20):
        battery.discharge(100.0)
    assert battery.soc_kwh == pytest.approx(battery.min_soc_kwh)
    assert battery.discharge(100.0) == pytest.approx(0.0)

    battery = Battery(config["battery"])
    reserve = 0.9 * config["battery"]["capacity_kwh"]
    battery.charge(100.0)
    battery.discharge(100.0, floor_kwh=reserve)
    assert battery.soc_kwh >= reserve - TOLERANCE


def test_round_trip_loses_energy(config):
    """Energy out is less than energy in, by the configured efficiency."""
    battery = Battery(config["battery"])
    battery.soc_kwh = battery.min_soc_kwh
    taken = battery.charge(2.0)
    given = battery.discharge(10.0)
    assert given == pytest.approx(taken * config["battery"]["round_trip_efficiency"], rel=1e-6)
    assert given < taken
