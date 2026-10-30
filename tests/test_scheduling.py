"""Flexible appliances must run for their full duration, inside their allowed window when moved.

A refused appliance deliberately stays at its usual time, which may sit outside the window.
"""
from __future__ import annotations

import pandas as pd
import pytest

from src.agent import AgentPlanner
from src.home import build_appliances, runs_today
from src.simulate import base_scenario, household_profile


@pytest.fixture(scope="module")
def plans(config, weather):
    """The agent's plan for every day of the month, with the matching notifications."""
    actual, forecast = weather
    scenario = base_scenario(config, household="low_use", has_battery=True, export_mode="none")
    profile = household_profile(config, scenario["household"])
    appliances = build_appliances(config)
    planner = AgentPlanner(config, scenario, profile, appliances)

    out = []
    for day, day_actual in actual.groupby(actual["time"].dt.date, sort=True):
        day_forecast = forecast[forecast["time"].dt.date == day]
        plan = planner.plan_day(pd.Timestamp(day), day_forecast, 0.0, len(actual) // 24)
        out.append((pd.Timestamp(day), plan))
        planner.learn_from_day(day_actual, day_forecast)
    return out, appliances


def test_each_appliance_runs_its_full_duration(plans, config):
    """The energy drawn each day equals the sum of the appliances due to run that day."""
    day_plans, appliances = plans
    for day, plan in day_plans:
        expected = sum(a.energy_kwh for a in appliances if runs_today(a, day))
        actual = sum(plan["appliance_kw"].values())
        assert actual == pytest.approx(expected), f"{day.date()}: appliance energy {actual} != {expected}"


def test_moved_appliances_land_inside_their_window(plans):
    """Any appliance the agent shifts must start inside its allowed window."""
    day_plans, appliances = plans
    by_name = {a.name: a for a in appliances}
    for day, plan in day_plans:
        for message in plan["notifications"]:
            if message["kind"] != "shifted":
                continue
            appliance = by_name[message["appliance"]]
            assert appliance.allowed_start <= message["hour"] < appliance.allowed_end, (
                f"{day.date()}: {appliance.name} moved to {message['hour']}:00, "
                f"outside [{appliance.allowed_start}, {appliance.allowed_end})"
            )


def test_refused_appliances_keep_their_usual_time(plans):
    """A refusal means the usual time is kept, and the reason is recorded."""
    day_plans, appliances = plans
    by_name = {a.name: a for a in appliances}
    for _, plan in day_plans:
        for message in plan["notifications"]:
            if message["kind"] != "refused":
                continue
            assert message["hour"] == by_name[message["appliance"]].usual_start
            assert message["message"].strip()


def test_appliance_draw_never_lands_outside_a_known_hour(plans):
    """Every hour with appliance draw is either an allowed hour or a usual time."""
    day_plans, appliances = plans
    allowed = set()
    for appliance in appliances:
        allowed.update(range(appliance.allowed_start, appliance.allowed_end + 1))
        allowed.add(appliance.usual_start)
    for day, plan in day_plans:
        for hour in plan["appliance_kw"]:
            assert hour in allowed, f"{day.date()}: appliance ran at {hour}:00"


def test_the_agent_does_move_some_appliances(plans):
    """Sanity check that shifting actually happens, so the other tests are meaningful."""
    day_plans, _ = plans
    shifted = sum(1 for _, plan in day_plans for m in plan["notifications"] if m["kind"] == "shifted")
    assert shifted > 0
