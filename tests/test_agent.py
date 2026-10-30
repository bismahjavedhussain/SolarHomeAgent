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
    edges = run["planner"].guard_edges()
    assert any(str(edge) in guard_messages[0]["message"] for edge in edges)


def test_guard_mode_stays_off_when_the_home_is_comfortably_under(config, weather):
    """The guard is a safety net, not always-on: it must not fire for a frugal home."""
    scenario = base_scenario(config, household="low_use", has_battery=True, export_mode="none")
    run = run_month(config, scenario, "agent", weather)
    assert run["hourly"]["grid_import_kwh"].sum() < config["agent"]["guard_threshold_units"]
    assert run["planner"].guard_days == 0


def test_guard_defends_band_edges_for_unprotected_homes_too(config, weather):
    """Every non-telescopic band edge is a cliff, so an unprotected home gets guarded as well."""
    scenario = base_scenario(config, household="high_use", has_battery=False, export_mode="none")
    run = run_month(config, scenario, "agent", weather)
    planner = run["planner"]
    assert not planner.profile["protected_eligible"]
    assert planner.guard_days > 0

    guard_messages = [m for m in run["notifications"] if m["kind"] == "guard"]
    edges = planner.guard_edges()
    tokens = (t.rstrip(".") for m in guard_messages for t in m["message"].split())
    targeted = {int(t) for t in tokens if t.isdigit() and int(t) in edges}
    assert targeted, "no band edge was named in any guard message"
    # A projection-based warning may bracket the final total, but must stay near it:
    # naming an edge several bands away would be a false alarm.
    final = run["hourly"]["grid_import_kwh"].sum()
    band_width = edges[1] - edges[0]
    assert all(abs(edge - final) <= 1.5 * band_width for edge in targeted), (
        f"guard named {sorted(targeted)} for a month that ended at {final:.0f} units")


def test_guard_waits_for_enough_days_before_projecting(config, weather):
    """A projection from a handful of days is unreliable, so the guard stays quiet early on."""
    scenario = base_scenario(config, household="high_use", has_battery=False, export_mode="none")
    run = run_month(config, scenario, "agent", weather)
    guard_days = [int(m["date"][-2:]) for m in run["notifications"] if m["kind"] == "guard"]
    assert guard_days
    assert min(guard_days) > config["agent"]["guard_min_days"]


def test_forecast_error_is_real(config, weather):
    """The agent's self-check must record a non-zero forecast error."""
    scenario = base_scenario(config, household="low_use", has_battery=True, export_mode="none")
    planner = run_month(config, scenario, "agent", weather)["planner"]
    assert planner.mean_forecast_error() > 1.0, "forecast error is ~0; the forecast may be the actuals"
    assert planner.mean_margin_kw() > 0.0


def test_compliance_rate_matches_the_config(config, weather):
    """The family acts on advice on the configured share of days, deterministically."""
    scenario = base_scenario(config, household="low_use", has_battery=True, export_mode="none")
    planner = run_month(config, scenario, "agent", weather)["planner"]
    configured = config["agent"]["suggestions_followed_pct"]
    assert planner.followed_pct() == pytest.approx(configured, abs=5)
    assert 0 < planner.followed_days < planner.planned_days


def test_full_compliance_beats_partial(config, weather):
    """Following every suggestion must do at least as well as following some of them."""
    scenario = base_scenario(config, household="low_use", has_battery=True, export_mode="none")
    full = dict(config, agent=dict(config["agent"], suggestions_followed_pct=100))
    partial = dict(config, agent=dict(config["agent"], suggestions_followed_pct=50))
    units = {
        label: run_month(cfg, scenario, "agent", weather)["hourly"]["grid_import_kwh"].sum()
        for label, cfg in (("full", full), ("partial", partial))
    }
    assert units["full"] <= units["partial"] + TOLERANCE


def test_ignored_days_fall_back_to_usual_times(config, weather):
    """On a day nobody acts, the agent says so and the appliances revert to habit."""
    scenario = base_scenario(config, household="low_use", has_battery=True, export_mode="none")
    notifications = run_month(config, scenario, "agent", weather)["notifications"]
    ignored = [m for m in notifications if m["kind"] == "ignored"]
    assert ignored, "partial compliance should produce ignored days"
    assert all("usual times" in m["message"] for m in ignored)


def test_promises_are_recorded_and_checked(config, weather):
    """Every shift the family acted on becomes a promise that is later judged against real solar."""
    scenario = base_scenario(config, household="low_use", has_battery=True, export_mode="none")
    planner = run_month(config, scenario, "agent", weather)["planner"]
    assert planner.promises
    judged = [p for p in planner.promises if "kept" in p]
    assert judged
    for promise in judged:
        assert promise["needed_kw"] > 0
        assert promise["kept"] == (promise["actual_solar_kw"] >= promise["needed_kw"])
    assert 0 <= planner.promises_kept_pct() <= 100


def test_message_wording_gets_more_cautious_as_confidence_falls(config, weather):
    """A shaky forecast must not be described in the same words as a confident one."""
    scenario = base_scenario(config, household="low_use", has_battery=True, export_mode="none")
    planner = run_month(config, scenario, "agent", weather)["planner"]
    assert "should cover" in planner._coverage_phrase(90)
    assert "probably" in planner._coverage_phrase(70)
    assert "shaky" in planner._coverage_phrase(30)
    assert len({planner._coverage_phrase(c) for c in (90, 70, 30)}) == 3
