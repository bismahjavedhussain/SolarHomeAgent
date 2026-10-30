"""The agent's rules: export discipline, refusals, margins and messages."""
from __future__ import annotations

import pytest

from src.simulate import base_scenario, run_month

TOLERANCE = 1e-9


def test_never_exports_while_the_battery_is_not_full(config, weather):
    """Surplus solar must fill the battery before any of it goes to the grid."""
    capacity = config["battery"]["capacity_kwh"]
    scenario = base_scenario(config, household="low_use", has_battery=True, export_mode="net_billing")
    hourly = run_month(config, scenario, "agent", weather)["hourly"]
    exporting = hourly[hourly["exported_kwh"] > TOLERANCE]
    assert not exporting.empty, "no exporting hours, so the rule is untested"
    assert (exporting["soc_kwh"] >= capacity - 1e-6).all(), "exported while the battery had room"


def test_refusals_are_counted_and_explained(config, weather):
    """Refusals appear in the message log with a reason and a confidence figure."""
    scenario = base_scenario(config, household="low_use", has_battery=True, export_mode="none")
    run = run_month(config, scenario, "agent", weather)
    refusals = [m for m in run["notifications"] if m["kind"] == "refused"]
    assert run["refusals"] == len(refusals)
    for message in refusals:
        assert "not enough sun" in message["message"].lower()
        assert 0 <= message["confidence_pct"] <= 100


def test_every_notification_is_complete(config, weather):
    """Each message carries a time, an action, a reason and a confidence."""
    scenario = base_scenario(config, household="low_use", has_battery=True, export_mode="none")
    notifications = run_month(config, scenario, "agent", weather)["notifications"]
    assert notifications
    for message in notifications:
        assert message["date"] and message["time"] and message["kind"]
        assert len(message["message"]) > 20
        assert 0 <= message["confidence_pct"] <= 100
        assert message["margin_source"] in ("learned", "cloud-cover")


def test_margin_switches_from_cloud_cover_to_learned(config, weather):
    """Early days use a cloud-based margin; later days use the agent's own error history."""
    scenario = base_scenario(config, household="low_use", has_battery=True, export_mode="none")
    notifications = run_month(config, scenario, "agent", weather)["notifications"]
    sources = {m["margin_source"] for m in notifications}
    assert sources == {"cloud-cover", "learned"}

    min_days = config["agent"]["min_history_days"]
    early = [m for m in notifications if int(m["date"][-2:]) <= min_days]
    assert all(m["margin_source"] == "cloud-cover" for m in early)


def test_agent_beats_usual_on_evening_grid_units(config, weather):
    """The agent should cut evening grid purchases, which is its main job."""
    for household in ("low_use", "high_use"):
        scenario = base_scenario(config, household=household, has_battery=True, export_mode="none")
        usual = run_month(config, scenario, "usual", weather)["hourly"]
        agent = run_month(config, scenario, "agent", weather)["hourly"]
        evening = lambda frame: frame[(frame["hour"] >= 18) & (frame["hour"] < 22)]["grid_import_kwh"].sum()
        assert evening(agent) <= evening(usual) + TOLERANCE, f"{household}: agent bought more in the evening"


def test_agent_does_not_increase_unmet_load(config, weather):
    """Planning a reserve must never leave the family with less backup than usual behaviour."""
    scenario = base_scenario(config, household="low_use", has_battery=True, export_mode="none")
    usual = run_month(config, scenario, "usual", weather)["hourly"]["unmet_kwh"].sum()
    agent = run_month(config, scenario, "agent", weather)["hourly"]["unmet_kwh"].sum()
    assert agent <= usual + TOLERANCE


def test_guard_mode_triggers_when_a_protected_home_is_on_course_to_cross(config, weather):
    """A protected-eligible home heading past 200 units gets guard-mode messages."""
    scenario = base_scenario(config, household="low_use", has_battery=False, export_mode="none")
    heavy = dict(config["households"]["low_use"], load_scale=1.0)  # uses well over 200 units
    run = run_month(config, scenario, "agent", weather, profile=heavy)

    assert run["hourly"]["grid_import_kwh"].sum() > config["agent"]["guard_threshold_units"]
    assert run["planner"].guard_days > 0
    guard_messages = [m for m in run["notifications"] if m["kind"] == "guard"]
    assert guard_messages
    assert str(config["agent"]["guard_threshold_units"]) in guard_messages[0]["message"]


def test_guard_mode_stays_off_when_the_home_is_comfortably_under(config, weather):
    """The guard is a safety net, not always-on: it must not fire for a frugal home."""
    scenario = base_scenario(config, household="low_use", has_battery=True, export_mode="none")
    run = run_month(config, scenario, "agent", weather)
    assert run["hourly"]["grid_import_kwh"].sum() < config["agent"]["guard_threshold_units"]
    assert run["planner"].guard_days == 0


def test_guard_mode_never_applies_to_unprotected_homes(config, weather):
    """A home that was never protected has no threshold to defend."""
    scenario = base_scenario(config, household="high_use", has_battery=False, export_mode="none")
    run = run_month(config, scenario, "agent", weather)
    assert run["planner"].guard_days == 0


def test_forecast_error_is_real(config, weather):
    """The agent's self-check must record a non-zero forecast error."""
    scenario = base_scenario(config, household="low_use", has_battery=True, export_mode="none")
    planner = run_month(config, scenario, "agent", weather)["planner"]
    assert planner.mean_forecast_error() > 1.0, "forecast error is ~0; the forecast may be the actuals"
    assert planner.mean_margin_kw() > 0.0
