"""A simple battery that respects capacity, power limits, efficiency and a minimum charge level."""
from __future__ import annotations


class Battery:
    """Tracks stored energy and enforces the physical limits. One hour per step, so kW equals kWh."""

    def __init__(self, cfg: dict):
        self.capacity_kwh = cfg["capacity_kwh"]
        self.max_charge_kw = cfg["max_charge_kw"]
        self.max_discharge_kw = cfg["max_discharge_kw"]
        self.min_soc_kwh = cfg["min_soc_frac"] * self.capacity_kwh
        self.efficiency = cfg["round_trip_efficiency"] ** 0.5  # split evenly across charge and discharge
        self.soc_kwh = cfg["start_soc_frac"] * self.capacity_kwh

    @property
    def usable_kwh(self) -> float:
        """Energy that could still be delivered to the home above the minimum charge level."""
        return max(0.0, self.soc_kwh - self.min_soc_kwh) * self.efficiency

    @property
    def is_full(self) -> bool:
        """True when the battery cannot take any more charge."""
        return self.soc_kwh >= self.capacity_kwh - 1e-9

    def charge(self, offered_kwh: float) -> float:
        """Store what it can from the energy offered; returns the kWh actually taken."""
        headroom = self.capacity_kwh - self.soc_kwh
        taken = min(max(0.0, offered_kwh), self.max_charge_kw, headroom / self.efficiency)
        self.soc_kwh += taken * self.efficiency
        return taken

    def discharge(self, requested_kwh: float, floor_kwh: float | None = None) -> float:
        """Deliver what it can, never going below the minimum charge level or a reserve floor."""
        floor = self.min_soc_kwh if floor_kwh is None else max(self.min_soc_kwh, floor_kwh)
        available = max(0.0, self.soc_kwh - floor) * self.efficiency
        given = min(max(0.0, requested_kwh), self.max_discharge_kw, available)
        self.soc_kwh -= given / self.efficiency
        return given
