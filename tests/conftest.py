"""Shared fixtures: load the config and cached weather once for the whole test session."""
from __future__ import annotations

import pytest

from src.fetch_weather import load_config, load_weather
from src.simulate import base_scenario, run_month

MODES = ["usual", "agent"]


@pytest.fixture(scope="session")
def config() -> dict:
    """The scenario config."""
    return load_config()


@pytest.fixture(scope="session")
def weather(config) -> tuple:
    """Cached actual and forecast weather for the simulation month."""
    return load_weather(config)


@pytest.fixture(scope="session")
def scenarios(config) -> list[dict]:
    """A representative spread of scenarios, kept small so the suite stays fast."""
    return [
        base_scenario(config, household="low_use", has_battery=True, export_mode="none"),
        base_scenario(config, household="low_use", has_battery=False, export_mode="net_billing"),
        base_scenario(config, household="high_use", has_battery=True, export_mode="net_billing"),
        base_scenario(config, household="high_use", has_battery=False, export_mode="none"),
    ]


@pytest.fixture(scope="session")
def runs(config, weather, scenarios) -> dict:
    """Every test scenario run in both modes, computed once."""
    return {
        (scenario_index, mode): run_month(config, scenario, mode, weather)
        for scenario_index, scenario in enumerate(scenarios)
        for mode in MODES
    }
