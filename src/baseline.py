"""Usual behaviour: appliances run at their habitual times, battery acts as a plain inverter."""
from __future__ import annotations

import pandas as pd

from .home import Appliance, appliance_hours, runs_today


def usual_plan(appliances: list[Appliance], day: pd.Timestamp) -> dict:
    """Place every appliance at its usual start hour, with no forecast and no pre-cooling."""
    draw: dict[int, float] = {}
    for appliance in appliances:
        if not runs_today(appliance, day):
            continue
        for hour, kw in appliance_hours(appliance.usual_start, appliance).items():
            draw[hour] = draw.get(hour, 0.0) + kw
    return {
        "appliance_kw": draw,
        "precool_kwh": {},
        "evening_relief_kwh": {},
        "reserve_kwh": 0.0,
        "notifications": [],
        "refusals": 0,
    }
