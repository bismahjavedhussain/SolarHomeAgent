"""During a power cut the home cannot buy anything from the grid."""
from __future__ import annotations

from src.simulate import in_power_cut

TOLERANCE = 1e-9


def test_no_grid_import_during_outages(runs):
    """Grid import must be exactly zero in every outage hour."""
    for key, run in runs.items():
        outage = run["hourly"][run["hourly"]["in_outage"]]
        assert not outage.empty, f"{key}: no outage hours were simulated"
        assert outage["grid_import_kwh"].max() <= TOLERANCE, f"{key}: bought power during an outage"


def test_nothing_is_exported_during_outages(runs):
    """A dead grid cannot absorb exports either."""
    for key, run in runs.items():
        outage = run["hourly"][run["hourly"]["in_outage"]]
        assert outage["exported_kwh"].max() <= TOLERANCE, f"{key}: exported during an outage"


def test_unmet_load_only_occurs_during_outages(runs):
    """Load can only go unserved when the grid is down."""
    for key, run in runs.items():
        served = run["hourly"][~run["hourly"]["in_outage"]]
        assert served["unmet_kwh"].max() <= TOLERANCE, f"{key}: unmet load outside an outage"


def test_outage_window_matches_config(config):
    """The configured window is read as [start, end)."""
    windows = config["power_cuts"]
    start, end = windows[0]
    assert in_power_cut(start, windows)
    assert not in_power_cut(end, windows)
    assert not in_power_cut(start - 1, windows)


def test_battery_reduces_unmet_load(runs, scenarios):
    """A battery should cover at least some of the outage that an identical home without one cannot."""
    by_scenario = {}
    for (index, mode), run in runs.items():
        key = (scenarios[index]["household"], scenarios[index]["export_mode"], mode)
        by_scenario.setdefault(key, {})[scenarios[index]["has_battery"]] = run["hourly"]["unmet_kwh"].sum()
    compared = [pair for pair in by_scenario.values() if len(pair) == 2]
    for pair in compared:
        assert pair[True] <= pair[False] + TOLERANCE
