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


def test_only_essential_load_is_served_during_an_outage(runs, config):
    """AC and flexible appliances do not run on backup; only fans, lights and the router."""
    essential = config["power_cut_essential_load_kw"]
    for key, run in runs.items():
        outage = run["hourly"][run["hourly"]["in_outage"]]
        assert (outage["load_kwh"] - essential).abs().max() < TOLERANCE, f"{key}: full load during an outage"


def test_usual_mode_defers_appliances_out_of_outages(config, weather):
    """A habitual time inside an outage is pushed to when power returns, not silently dropped."""
    from src.baseline import usual_plan
    from src.home import build_appliances
    import pandas as pd

    appliances = build_appliances(config)
    cut_hours = [h for start, end in config["power_cuts"] for h in range(start, end)]
    assert cut_hours, "this test needs a configured outage"
    plan = usual_plan(appliances, pd.Timestamp("2025-06-02"), cut_hours)
    assert not set(plan["appliance_kw"]) & set(cut_hours)
    expected = sum(a.energy_kwh for a in appliances if a.days_per_week >= 7)
    assert sum(plan["appliance_kw"].values()) >= expected - TOLERANCE


def test_both_modes_want_a_comparable_amount_of_energy(config, weather):
    """Usual and agent must not differ in total load except by the pre-cooling trade."""
    from src.simulate import base_scenario, run_month

    scenario = base_scenario(config, household="low_use", has_battery=True, export_mode="none")
    wanted = {m: run_month(config, scenario, m, weather)["hourly"]["load_kwh"].sum()
              for m in ("usual", "agent")}
    precool_budget = 31 * config["precooling"]["extra_kwh"]
    assert wanted["agent"] - wanted["usual"] <= precool_budget + TOLERANCE
    assert wanted["agent"] >= wanted["usual"] - TOLERANCE
