"""The agent: plans tomorrow from the forecast, keeps a safety margin, and explains itself.

It refuses to move an appliance when the forecast is not confident enough. See HOW_IT_WORKS.md.
"""
from __future__ import annotations

import pandas as pd

from .baseline import usual_plan
from .home import Appliance, ac_component_kw, appliance_hours, base_load_kw, runs_today
from .solar import solar_kw

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
            cloud = float(row["cloud_pct"]) / 100.0
            margins[hour] = self.margin(hour, solar[hour], cloud)
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

    def place_appliance(self, appliance: Appliance, surplus: dict[int, float],
                        committed: dict[int, float]) -> int | None:
        """Pick the hour in the allowed window whose confident surplus covers this appliance."""
        candidates = []
        for hour in range(appliance.allowed_start, appliance.allowed_end):
            hours_needed = appliance_hours(hour, appliance)
            if max(hours_needed) >= appliance.allowed_end:
                continue  # the run would spill past the allowed window
            headroom = min(surplus.get(h, 0.0) - committed.get(h, 0.0) - kw
                           for h, kw in hours_needed.items())
            if headroom >= 0:
                candidates.append((headroom, -hour, hour))
        if not candidates:
            return None
        return max(candidates)[2]

    def plan_day(self, day: pd.Timestamp, day_forecast: pd.DataFrame,
                 month_units_so_far: float, days_in_month: int) -> dict:
        """Decide tomorrow's appliance times, pre-cooling and battery reserve, with messages."""
        if day_forecast.empty:
            return usual_plan(self.appliances, day)

        surplus, margins = self.conservative_surplus(day_forecast)
        confidence = self.confidence(day_forecast, margins)
        guard_on = self._guard_active(day, month_units_so_far, days_in_month)

        draw: dict[int, float] = {}
        committed: dict[int, float] = {}
        messages: list[dict] = []

        if guard_on:
            self.guard_days += 1
            messages.append(self._message(
                day, PLANNING_HOUR, "guard",
                f"{month_units_so_far:.0f} units used with {self._days_left(day, days_in_month)} days left. "
                f"Moving more jobs into the sun to try to stay under "
                f"{self.agent_cfg['guard_threshold_units']} units.",
                confidence,
            ))

        for appliance in self.appliances:
            if not runs_today(appliance, day):
                continue
            hour = self.place_appliance(appliance, surplus, committed)
            if hour is None and guard_on:
                hour = self._best_effort_hour(appliance, surplus, committed)
            if hour is None:
                self.refusals += 1
                messages.append(self._message(
                    day, appliance.usual_start, "refused",
                    f"Keeping the {self._label(appliance)} at its usual "
                    f"{appliance.usual_start}:00. Not enough sun expected tomorrow to be confident "
                    f"about moving it (confidence {confidence}%).",
                    confidence, appliance.name,
                ))
                hour = appliance.usual_start
            elif hour != appliance.usual_start:
                messages.append(self._message(
                    day, hour, "shifted",
                    f"Run the {self._label(appliance)} at {hour}:00 instead of "
                    f"{appliance.usual_start}:00. Your panels should cover it then "
                    f"(confidence {confidence}%).",
                    confidence, appliance.name,
                ))
            for run_hour, kw in appliance_hours(hour, appliance).items():
                draw[run_hour] = draw.get(run_hour, 0.0) + kw
                committed[run_hour] = committed.get(run_hour, 0.0) + kw

        precool, relief, precool_message = self._plan_precooling(day, day_forecast, surplus, committed,
                                                                 confidence, guard_on)
        messages.extend(precool_message)
        reserve = self._plan_reserve(day_forecast, confidence, guard_on)
        daytime_reserve = reserve.get(0, 0.0)
        if daytime_reserve > 0:
            messages.append(self._message(
                day, 16, "battery",
                f"Holding {daytime_reserve:.1f} kWh in the battery for this evening"
                f"{' and the power cut' if self.config['power_cuts'] else ''} "
                f"(confidence {confidence}%).",
                confidence,
            ))

        self.margins_used.append(sum(margins.values()) / max(1, len(margins)))
        return {
            "appliance_kw": draw,
            "precool_kwh": precool,
            "evening_relief_kwh": relief,
            "reserve_kwh": reserve,
            "notifications": messages,
            "refusals": self.refusals,
            "confidence": confidence,
            "guard_mode": guard_on,
        }

    # --- individual decisions ---------------------------------------------

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
        window_hours = list(range(start, end + 1))
        available = sum(max(0.0, surplus.get(h, 0.0) - committed.get(h, 0.0)) for h in window_hours)
        if available < cfg["extra_kwh"]:
            return {}, {}, []

        share = cfg["extra_kwh"] / len(window_hours)
        precool = {h: share for h in window_hours}
        evening_hours = [h for h in EVENING_HOURS if h < 24]
        relief = {h: cfg["evening_saving_kwh"] / len(evening_hours) for h in evening_hours}
        message = self._message(
            day, start, "precool",
            f"Pre-cooling the house between {start}:00 and {end}:00 while the sun is strong. "
            f"Tomorrow evening should reach {evening_temp:.0f}C, so this should take about "
            f"{cfg['evening_saving_kwh']} kWh off the evening AC (rough estimate, confidence {confidence}%).",
            confidence,
        )
        return precool, relief, [message]

    def _plan_reserve(self, day_forecast: pd.DataFrame, confidence: int, guard_on: bool) -> dict[int, float]:
        """Battery floor for each hour: saved up during the day, then spent in the evening."""
        if not self.scenario["has_battery"]:
            return {hour: 0.0 for hour in range(24)}

        fixed = self.predicted_fixed_load(day_forecast)
        solar = self.predicted_solar(day_forecast)
        evening_deficit = sum(max(0.0, fixed.get(h, 0.0) - solar.get(h, 0.0)) for h in EVENING_HOURS)
        cut_hours = [h for start, end in self.config["power_cuts"] for h in range(start, end)]
        cut_need = sum(fixed.get(h, 0.0) for h in cut_hours)

        capacity = self.config["battery"]["capacity_kwh"]
        daytime_floor = min(evening_deficit + cut_need, capacity)
        if confidence < 60:
            daytime_floor = min(capacity, daytime_floor * 1.2)  # less sure, so hold a little more back
        if guard_on:
            daytime_floor = min(capacity, daytime_floor * 1.1)

        # Hold the reserve back until the evening, then keep only what the coming power cut needs.
        first_cut = min(cut_hours) if cut_hours else 24
        floors = {}
        for hour in range(24):
            if hour < EVENING_HOURS.start:
                floors[hour] = daytime_floor
            elif hour < first_cut:
                floors[hour] = min(cut_need, capacity)
            else:
                floors[hour] = 0.0
        return {hour: round(value, 3) for hour, value in floors.items()}

    def _guard_active(self, day: pd.Timestamp, month_units_so_far: float, days_in_month: int) -> bool:
        """True when a protected-eligible home is on course to cross the 200-unit threshold."""
        if not self.profile["protected_eligible"]:
            return False
        days_done = day.day - 1
        if days_done < 1:
            return False
        projected = month_units_so_far / days_done * days_in_month
        return projected > self.agent_cfg["guard_threshold_units"]

    def _best_effort_hour(self, appliance: Appliance, surplus: dict[int, float],
                          committed: dict[int, float]) -> int | None:
        """In guard mode, accept the sunniest allowed hour even if the margin is not fully covered."""
        options = []
        for hour in range(appliance.allowed_start, appliance.allowed_end):
            hours_needed = appliance_hours(hour, appliance)
            if max(hours_needed) >= appliance.allowed_end:
                continue
            headroom = min(surplus.get(h, 0.0) - committed.get(h, 0.0) for h in hours_needed)
            options.append((headroom, -hour, hour))
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
        """Compare what was forecast with what happened and update the error history."""
        if day_forecast.empty:
            return
        merged = day_actual.merge(day_forecast, on="time", suffixes=("_act", "_fc"))
        derate = self.config["solar"]["derate"]
        rating = self.scenario["solar_kw"]
        for _, row in merged.iterrows():
            hour = int(row["time"].hour)
            error = solar_kw(row["ghi_wm2_fc"], rating, derate) - solar_kw(row["ghi_wm2_act"], rating, derate)
            self.errors_by_hour.setdefault(hour, []).append(error)
        daily = (merged["ghi_wm2_fc"] - merged["ghi_wm2_act"]).abs().mean()
        self.daily_errors.append(float(daily))
        self.days_seen += 1

    def mean_forecast_error(self) -> float:
        """Average absolute day-ahead radiation error over the month, in W/m2."""
        return sum(self.daily_errors) / len(self.daily_errors) if self.daily_errors else 0.0

    def mean_margin_kw(self) -> float:
        """Average hourly margin held back, in kW."""
        return sum(self.margins_used) / len(self.margins_used) if self.margins_used else 0.0
