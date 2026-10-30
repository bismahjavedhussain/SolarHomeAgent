"""Usual behaviour: appliances run at their habitual times, battery acts as a plain inverter."""
from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from .home import Appliance, appliance_hours, runs_today


def usual_hour_after_outages(appliance: Appliance, cut_hours: Sequence[int]) -> int:
    """Push the usual start past an outage, since only essentials run on backup."""
    hour = appliance.usual_start
    for _ in range(24):
        if not any(h in cut_hours for h in appliance_hours(hour, appliance)):
            return hour
        hour = (hour + 1) % 24
    return appliance.usual_start


def usual_plan(appliances: list[Appliance], day: pd.Timestamp,
               cut_hours: Sequence[int] = ()) -> dict:
    """Place every appliance at its usual hour, with no forecast and no pre-cooling."""
    draw: dict[int, float] = {}
    for appliance in appliances:
        if not runs_today(appliance, day):
            continue
        for hour, kw in appliance_hours(usual_hour_after_outages(appliance, cut_hours), appliance).items():
            draw[hour] = draw.get(hour, 0.0) + kw
    return {
        "appliance_kw": draw,
        "precool_kwh": {},
        "evening_relief_kwh": {},
        "reserve_kwh": 0.0,
        "notifications": [],
        "refusals": 0,
    }
