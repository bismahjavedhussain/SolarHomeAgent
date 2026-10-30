"""The same inputs must always give the same outputs."""
from __future__ import annotations

import pandas as pd

from src.metrics import summarise
from src.simulate import base_scenario, run_month


def test_repeated_runs_are_identical(config, weather):
    """Running the same scenario twice produces identical hourly results."""
    scenario = base_scenario(config, household="low_use", has_battery=True, export_mode="none")
    for mode in ("usual", "agent"):
        first = run_month(config, scenario, mode, weather)["hourly"]
        second = run_month(config, scenario, mode, weather)["hourly"]
        pd.testing.assert_frame_equal(first, second)


def test_repeated_metrics_are_identical(config, weather):
    """Summary metrics are reproducible too."""
    scenario = base_scenario(config, household="high_use", has_battery=True, export_mode="net_billing")
    first = summarise(run_month(config, scenario, "agent", weather), config, scenario)
    second = summarise(run_month(config, scenario, "agent", weather), config, scenario)
    assert first == second


def test_notifications_are_reproducible(config, weather):
    """The agent's message log is identical across runs."""
    scenario = base_scenario(config, household="low_use", has_battery=True, export_mode="none")
    first = run_month(config, scenario, "agent", weather)["notifications"]
    second = run_month(config, scenario, "agent", weather)["notifications"]
    assert first == second
