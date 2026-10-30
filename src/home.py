"""Household electricity demand: base load, temperature-driven AC, and flexible appliances."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


def base_load_kw(hour: int, levels: dict, scale: float = 1.0) -> float:
    """Fridge, fans and lights, by time of day."""
    if hour < 6:
        value = levels["night"]
    elif hour < 18:
        value = levels["day"]
    else:
        value = levels["evening"]
    return value * scale


def _in_window(hour: int, window: list) -> bool:
    """True if hour is in [start, end), handling windows that wrap past midnight."""
    start, end = window
    return start <= hour < end if start < end else (hour >= start or hour < end)


def ac_duty(temp_c: float, cfg: dict) -> float:
    """Fraction of the hour the AC runs: 0 below the threshold, rising to 1.0 at the full-duty temp."""
    if temp_c <= cfg["temp_threshold_c"]:
        return 0.0
    span = cfg["full_duty_temp_c"] - cfg["temp_threshold_c"]
    return min(1.0, 0.5 + 0.5 * (temp_c - cfg["temp_threshold_c"]) / span)


def ac_load_kw(hour: int, temp_c: float, ac_count: int, cfg: dict) -> float:
    """AC demand in kW for one hour: half duty in the afternoon, full duty overnight."""
    duty = ac_duty(temp_c, cfg)
    if duty == 0.0:
        return 0.0
    rated = cfg["kw_per_unit"] * ac_count
    if _in_window(hour, cfg["day_window"]):
        return rated * duty * cfg["day_duty_factor"]
    if _in_window(hour, cfg["night_window"]):
        return rated * duty
    return 0.0


def ac_component_kw(hour: int, temp_c: float, profile: dict, config: dict) -> float:
    """The AC part of demand on its own, after the household's load scale."""
    return ac_load_kw(hour, temp_c, profile["ac_count"], config["ac"]) * profile["load_scale"]


def fixed_load_kw(hour: int, temp_c: float, profile: dict, config: dict) -> float:
    """Base load plus AC: the part of demand the family cannot move."""
    base = base_load_kw(hour, config["base_load_kw"], profile["load_scale"])
    return base + ac_component_kw(hour, temp_c, profile, config)


@dataclass(frozen=True)
class Appliance:
    """A shiftable appliance and the window it may run in."""

    name: str
    kw: float
    hours: float
    days_per_week: int
    allowed_start: int
    allowed_end: int
    usual_start: int

    @property
    def energy_kwh(self) -> float:
        """Energy used per run."""
        return self.kw * self.hours


def build_appliances(config: dict) -> list[Appliance]:
    """Read the appliance list from config."""
    usual = config["usual_times"]
    out = []
    for name, spec in config["appliances"].items():
        out.append(
            Appliance(
                name=name,
                kw=spec["kw"],
                hours=spec["hours"],
                days_per_week=spec["days_per_week"],
                allowed_start=spec["allowed"][0],
                allowed_end=spec["allowed"][1],
                usual_start=usual[name],
            )
        )
    return out


def runs_today(appliance: Appliance, day: pd.Timestamp) -> bool:
    """Whether an appliance runs on a given date; fixed rule, so results are reproducible."""
    if appliance.days_per_week >= 7:
        return True
    if appliance.days_per_week == 4:
        return day.day % 7 in (0, 2, 4, 6)
    return day.day % 7 < appliance.days_per_week


def appliance_hours(start_hour: int, appliance: Appliance) -> dict[int, float]:
    """Spread an appliance's run over whole hours, returning {hour: kW drawn}."""
    remaining, hour, draw = appliance.hours, start_hour, {}
    while remaining > 1e-9:
        share = min(1.0, remaining)
        draw[hour % 24] = draw.get(hour % 24, 0.0) + appliance.kw * share
        remaining -= share
        hour += 1
    return draw
