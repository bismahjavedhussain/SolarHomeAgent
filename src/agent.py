"""The agent: plans tomorrow from the forecast, keeps a safety margin, and explains itself.

It refuses to move an appliance when the forecast is not confident enough. See HOW_IT_WORKS.md.
"""
from __future__ import annotations

import pandas as pd

from .baseline import usual_hour_after_outages, usual_plan
from .home import Appliance, ac_component_kw, appliance_hours, base_load_kw, runs_today
from .solar import solar_kw
from .tariff import band_limits

PLANNING_HOUR = 20  # the evening it plans the next day
EVENING_HOURS = range(18, 24)


class AgentPlanner:
    """Plans each day ahead, learns its own forecast error, and writes plain-language messages."""

    def __init__(self, config: dict, scenario: dict, profile: dict, appliances: list[Appliance]):
        self.config = config
        self.scenario = scenario
        self.profile = profile
        self.appliances = appliances
        self.agent_cfg = config["agent"]
        self.errors_by_hour: dict[int, list[float]] = {}
        self.days_seen = 0
        self.refusals = 0
        self.daily_errors: list[float] = []
        self.margins_used: list[float] = []
        self.guard_days = 0
        self.followed_days = 0
        self.planned_days = 0
        self.promises: list[dict] = []
        self.pending_promises: list[dict] = []
        cuts = config["power_cuts"] if scenario.get("power_cuts", True) else []
        self.cut_hours = [h for start, end in cuts for h in range(start, end)]

    # --- forecasting -------------------------------------------------------

    def predicted_solar(self, day_forecast: pd.DataFrame) -> dict[int, float]:
        """Tomorrow's hourly solar output from the forecast radiation."""
        derate = self.config["solar"]["derate"]
        return {
            int(row["time"].hour): solar_kw(row["ghi_wm2"], self.scenario["solar_kw"], derate)
            for _, row in day_forecast.iterrows()
        }

    def predicted_fixed_load(self, day_forecast: pd.DataFrame) -> dict[int, float]:
        """Tomorrow's unavoidable load (base plus AC) from the forecast temperature."""
        return {
            int(row["time"].hour): (
                base_load_kw(int(row["time"].hour), self.config["base_load_kw"], self.profile["load_scale"])
                + ac_component_kw(int(row["time"].hour), row["temp_c"], self.profile, self.config)
            )
            for _, row in day_forecast.iterrows()
        }

    def margin(self, hour: int, predicted_kw: float, cloud_fraction: float) -> float:
        """How much solar to hold back at this hour, learned from past errors once enough days exist."""
        history = self.errors_by_hour.get(hour, [])
        if self.days_seen >= self.agent_cfg["min_history_days"] and history:
            percentile = self.agent_cfg["margin_percentile"] / 100.0
            return float(pd.Series(history).abs().quantile(percentile))
        return predicted_kw * cloud_fraction  # fallback until the agent has its own error history

    def margin_source(self) -> str:
        """Which margin rule is currently in force."""
        return "learned" if self.days_seen >= self.agent_cfg["min_history_days"] else "cloud-cover"

    def conservative_surplus(self, day_forecast: pd.DataFrame) -> tuple[dict[int, float], dict[int, float]]:
        """Solar we are confident of, after the margin and the unavoidable load."""
        solar = self.predicted_solar(day_forecast)
        fixed = self.predicted_fixed_load(day_forecast)
        surplus, margins = {}, {}
        for _, row in day_forecast.iterrows():
            hour = int(row["time"].hour)
            margins[hour] = self.margin(hour, solar[hour], float(row["cloud_pct"]) / 100.0)
            surplus[hour] = solar[hour] - margins[hour] - fixed[hour]
        return surplus, margins

    def confidence(self, day_forecast: pd.DataFrame, margins: dict[int, float]) -> int:
        """Daily confidence as a percentage, from the margin relative to predicted solar."""
        solar = self.predicted_solar(day_forecast)
        daylight = [h for h, kw in solar.items() if kw > 0.05]
        if not daylight:
            return 0
        total_solar = sum(solar[h] for h in daylight)
        total_margin = sum(margins[h] for h in daylight)
        return int(round(100 * max(0.0, 1 - total_margin / max(1e-9, total_solar))))

    # --- planning ----------------------------------------------------------

    def _usable_hours(self, appliance: Appliance) -> list[int]:
        """Hours in the allowed window where a full run fits and the grid is up."""
        hours = []
        for hour in range(appliance.allowed_start, appliance.allowed_end):
            needed = appliance_hours(hour, appliance)
            if max(needed) >= appliance.allowed_end:
                continue  # the run would spill past the allowed window
            if any(h in self.cut_hours for h in needed):
                continue  # nothing but essentials runs during an outage
            hours.append(hour)
        return hours

    def place_appliance(self, appliance: Appliance, surplus: dict[int, float],
                        committed: dict[int, float]) -> int | None:
        """Pick the hour in the allowed window whose confident surplus covers this appliance."""
        candidates = []
        for hour in self._usable_hours(appliance):
            headroom = min(surplus.get(h, 0.0) - committed.get(h, 0.0) - kw
                           for h, kw in appliance_hours(hour, appliance).items())
            if headroom >= 0:
                candidates.append((headroom, -hour, hour))
        return max(candidates)[2] if candidates else None

    def plan_day(self, day: pd.Timestamp, day_forecast: pd.DataFrame,
                 month_units_so_far: float, days_in_month: int) -> dict:
        """Decide tomorrow's appliance times, pre-cooling and battery reserve, with messages."""
        if day_forecast.empty:
            return usual_plan(self.appliances, day, self.cut_hours)

        self.planned_days += 1
        surplus, margins = self.conservative_surplus(day_forecast)
        confidence = self.confidence(day_forecast, margins)
        guard_edge = self._guard_target(day, month_units_so_far, days_in_month)
        followed = self._family_follows(day)

        draw: dict[int, float] = {}
        committed: dict[int, float] = {}
        messages: list[dict] = []
        promises: list[dict] = []

        if guard_edge is not None:
            self.guard_days += 1
            messages.append(self._message(day, PLANNING_HOUR, "guard", self._guard_text(
                day, month_units_so_far, days_in_month, guard_edge), confidence))

        for appliance in self.appliances:
            if not runs_today(appliance, day):
                continue
            hour = self.place_appliance(appliance, surplus, committed)
            if hour is None and guard_edge is not None:
                hour = self._best_effort_hour(appliance, surplus, committed)
            if hour is None:
                self.refusals += 1
                messages.append(self._message(
                    day, appliance.usual_start, "refused",
                    f"Keeping the {self._label(appliance)} at its usual {appliance.usual_start}:00. "
                    f"Not enough sun expected tomorrow to be confident about moving it "
                    f"(confidence {confidence}%).",
                    confidence, appliance.name))
                hour = usual_hour_after_outages(appliance, self.cut_hours)
            elif hour != appliance.usual_start:
                messages.append(self._message(
                    day, hour, "shifted",
                    f"Run the {self._label(appliance)} at {hour}:00 instead of "
                    f"{appliance.usual_start}:00. {self._coverage_phrase(confidence)} "
                    f"(confidence {confidence}%).",
                    confidence, appliance.name))
                promises.append({"date": day.date().isoformat(), "hour": hour,
                                 "appliance": appliance.name, "needed_kw": appliance.kw,
                                 "confidence_pct": confidence})
            for run_hour, kw in appliance_hours(hour, appliance).items():
                draw[run_hour] = draw.get(run_hour, 0.0) + kw
                committed[run_hour] = committed.get(run_hour, 0.0) + kw

        precool, relief, precool_message = self._plan_precooling(
            day, day_forecast, surplus, committed, confidence, guard_edge is not None)
        messages.extend(precool_message)

        reserve = self._plan_reserve(day_forecast, confidence, guard_edge is not None)
        if reserve.get(0, 0.0) > 0:
            cut_note = " and the power cut" if self.cut_hours else ""
            messages.append(self._message(
                day, 16, "battery",
                f"Holding {reserve[0]:.1f} kWh in the battery for this evening{cut_note} "
                f"(confidence {confidence}%).",
                confidence))

        if followed:
            self.followed_days += 1
            self.pending_promises = promises
            self.promises.extend(promises)
        else:
            # Nobody acted today, so appliances fall back to habit. The battery still plans itself.
            draw = usual_plan(self.appliances, day, self.cut_hours)["appliance_kw"]
            precool, relief = {}, {}
            self.pending_promises = []
            messages.append(self._message(
                day, PLANNING_HOUR, "ignored",
                "Nobody was able to act on today's suggestions, so the appliances ran at their "
                "usual times. The battery still followed its plan.", confidence))

        self.margins_used.append(sum(margins.values()) / max(1, len(margins)))
        return {
            "appliance_kw": draw,
            "precool_kwh": precool,
            "evening_relief_kwh": relief,
            "reserve_kwh": reserve,
            "notifications": messages,
            "refusals": self.refusals,
            "confidence": confidence,
            "guard_mode": guard_edge is not None,
            "followed": followed,
        }

    # --- individual decisions ---------------------------------------------

    def _family_follows(self, day: pd.Timestamp) -> bool:
        """Deterministic pattern of days on which somebody acts on the advice."""
        share = max(0, min(100, int(self.agent_cfg["suggestions_followed_pct"]))) // 10
        return ((day.day - 1) % 10) < share

    def _coverage_phrase(self, confidence: int) -> str:
        """Wording that gets more cautious as confidence falls."""
        if confidence >= 80:
            return "Your panels should cover it then."
        if confidence >= 60:
            return "Your panels will probably cover it, though the forecast is less certain today."
        return "Your panels might cover it, but tomorrow's forecast is shaky, so keep an eye on it."

    def _plan_precooling(self, day: pd.Timestamp, day_forecast: pd.DataFrame, surplus: dict[int, float],
                         committed: dict[int, float], confidence: int, guard_on: bool) -> tuple[dict, dict, list]:
        """Cool the house early on hot days, if the confident surplus can pay for it."""
        cfg = self.config["precooling"]
        evening = day_forecast[day_forecast["time"].dt.hour.isin(EVENING_HOURS)]
        if evening.empty:
            return {}, {}, []
        evening_temp = float(evening["temp_c"].max())
        if evening_temp < cfg["trigger_evening_temp_c"] and not guard_on:
            return {}, {}, []

        start, end = cfg["window"]
        window_hours = [h for h in range(start, end + 1) if h not in self.cut_hours]
        available = sum(max(0.0, surplus.get(h, 0.0) - committed.get(h, 0.0)) for h in window_hours)
        if not window_hours or available < cfg["extra_kwh"]:
            return {}, {}, []

        precool = {h: cfg["extra_kwh"] / len(window_hours) for h in window_hours}
        evening_hours = [h for h in EVENING_HOURS if h not in self.cut_hours]
        relief = ({h: cfg["evening_saving_kwh"] / len(evening_hours) for h in evening_hours}
                  if evening_hours else {})
        message = self._message(
            day, start, "precool",
            f"Pre-cooling the house between {start}:00 and {end}:00 while the sun is strong. "
            f"Tomorrow evening should reach {evening_temp:.0f}C, so this should take about "
            f"{cfg['evening_saving_kwh']} kWh off the evening AC (rough estimate, confidence {confidence}%).",
            confidence)
        return precool, relief, [message]

    def _plan_reserve(self, day_forecast: pd.DataFrame, confidence: int, guard_on: bool) -> dict[int, float]:
        """Battery floor for each hour: saved up during the day, then spent in the evening."""
        if not self.scenario["has_battery"]:
            return {hour: 0.0 for hour in range(24)}

        fixed = self.predicted_fixed_load(day_forecast)
        solar = self.predicted_solar(day_forecast)
        evening_deficit = sum(max(0.0, fixed.get(h, 0.0) - solar.get(h, 0.0)) for h in EVENING_HOURS)
        # Only essential loads run on backup, so the cut needs far less than the full load.
        cut_need = self.config["power_cut_essential_load_kw"] * len(self.cut_hours)

        capacity = self.config["battery"]["capacity_kwh"]
        daytime_floor = min(evening_deficit + cut_need, capacity)
        if confidence < 60:
            daytime_floor = min(capacity, daytime_floor * 1.2)  # less sure, so hold a little more back
        if guard_on:
            daytime_floor = min(capacity, daytime_floor * 1.1)

        # Hold the reserve back until the evening, then keep only what the coming power cut needs.
        first_cut = min(self.cut_hours) if self.cut_hours else 24
        floors = {}
        for hour in range(24):
            if hour < EVENING_HOURS.start:
                floors[hour] = daytime_floor
            elif hour < first_cut:
                floors[hour] = min(cut_need, capacity)
            else:
                floors[hour] = 0.0
        return {hour: round(value, 3) for hour, value in floors.items()}

    def guard_edges(self) -> list[int]:
        """Unit totals where crossing re-prices every unit, so staying under one saves money."""
        edges = {self.agent_cfg["guard_threshold_units"]} if self.profile["protected_eligible"] else set()
        if self.agent_cfg.get("guard_all_band_edges", True):
            edges.update(band_limits(self.config["tariff"])[:-1])  # the open-ended top band has no edge
        return sorted(edges)

    def projected_units(self, day: pd.Timestamp, month_units_so_far: float,
                        days_in_month: int) -> float | None:
        """Project the month's total from the rate so far, or None if too few days to tell."""
        days_done = day.day - 1
        if days_done < self.agent_cfg["guard_min_days"]:
            return None  # a projection from a handful of days is far too unreliable
        return month_units_so_far / days_done * days_in_month

    def _guard_target(self, day: pd.Timestamp, month_units_so_far: float,
                      days_in_month: int) -> int | None:
        """The band edge worth defending, if the month is projected to cross one."""
        projected = self.projected_units(day, month_units_so_far, days_in_month)
        if projected is None:
            return None
        below = [edge for edge in self.guard_edges() if edge < projected]
        if not below:
            return None
        edge = max(below)
        if projected > edge * (1 + self.agent_cfg["guard_max_overshoot_frac"]):
            return None  # already too far past this edge to claw back
        return edge

    def _guard_text(self, day: pd.Timestamp, month_units_so_far: float,
                    days_in_month: int, edge: int) -> str:
        """Plain-language warning about an approaching band edge."""
        left = self._days_left(day, days_in_month)
        if self.profile["protected_eligible"] and edge == self.agent_cfg["guard_threshold_units"]:
            why = (f"Going over {edge} units moves you to unprotected rates, which re-price every "
                   f"unit for six months.")
        else:
            why = f"Going over {edge} units re-prices every unit you used this month at a higher rate."
        return (f"{month_units_so_far:.0f} units used with {left} days left. {why} "
                f"Moving more jobs into the sun to try to stay under {edge}.")

    def _best_effort_hour(self, appliance: Appliance, surplus: dict[int, float],
                          committed: dict[int, float]) -> int | None:
        """In guard mode, accept the sunniest allowed hour even if the margin is not fully covered."""
        options = [
            (min(surplus.get(h, 0.0) - committed.get(h, 0.0) for h in appliance_hours(hour, appliance)),
             -hour, hour)
            for hour in self._usable_hours(appliance)
        ]
        return max(options)[2] if options else None

    def _days_left(self, day: pd.Timestamp, days_in_month: int) -> int:
        """Days remaining in the billing month."""
        return days_in_month - day.day + 1

    def _label(self, appliance: Appliance) -> str:
        """Appliance name in plain words."""
        return appliance.name.replace("_", " ")

    def _message(self, day: pd.Timestamp, hour: int, kind: str, text: str,
                 confidence: int, appliance: str = "") -> dict:
        """One notification for the family."""
        return {
            "date": day.date().isoformat(),
            "hour": hour,
            "time": f"{hour:02d}:00",
            "kind": kind,
            "appliance": appliance,
            "message": text,
            "confidence_pct": confidence,
            "margin_source": self.margin_source(),
        }

    # --- learning ----------------------------------------------------------

    def learn_from_day(self, day_actual: pd.DataFrame, day_forecast: pd.DataFrame) -> None:
        """Compare what was forecast with what happened, and check the promises made."""
        if day_forecast.empty:
            return
        merged = day_actual.merge(day_forecast, on="time", suffixes=("_act", "_fc"))
        derate, rating = self.config["solar"]["derate"], self.scenario["solar_kw"]
        actual_solar = {}
        for _, row in merged.iterrows():
            hour = int(row["time"].hour)
            actual_solar[hour] = solar_kw(row["ghi_wm2_act"], rating, derate)
            error = solar_kw(row["ghi_wm2_fc"], rating, derate) - actual_solar[hour]
            self.errors_by_hour.setdefault(hour, []).append(error)

        for promise in self.pending_promises:  # did the sun actually show up as promised?
            promise["actual_solar_kw"] = round(actual_solar.get(promise["hour"], 0.0), 3)
            promise["kept"] = promise["actual_solar_kw"] >= promise["needed_kw"]
        self.pending_promises = []

        self.daily_errors.append(float((merged["ghi_wm2_fc"] - merged["ghi_wm2_act"]).abs().mean()))
        self.days_seen += 1

    def mean_forecast_error(self) -> float:
        """Average absolute day-ahead radiation error over the month, in W/m2."""
        return sum(self.daily_errors) / len(self.daily_errors) if self.daily_errors else 0.0

    def mean_margin_kw(self) -> float:
        """Average hourly margin held back, in kW."""
        return sum(self.margins_used) / len(self.margins_used) if self.margins_used else 0.0

    def promises_kept_pct(self) -> float | None:
        """Of the hours it promised solar would cover an appliance, how often it did."""
        judged = [p for p in self.promises if "kept" in p]
        if not judged:
            return None
        return round(100 * sum(1 for p in judged if p["kept"]) / len(judged), 1)

    def followed_pct(self) -> float | None:
        """Share of planned days on which the family acted on the advice."""
        if not self.planned_days:
            return None
        return round(100 * self.followed_days / self.planned_days, 1)
