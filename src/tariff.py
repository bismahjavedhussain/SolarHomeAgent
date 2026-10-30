"""Monthly electricity bill under Pakistan's protected and unprotected bands.

Rates are approximate and configurable; intermediate unprotected bands are placeholders.
"""
from __future__ import annotations


def unprotected_rates(cfg: dict) -> list[tuple[int, float, bool]]:
    """Per-band unprotected rates as (upper unit limit, Rs/unit, is_placeholder)."""
    limits = cfg["unprotected_band_limits"]
    lowest, highest = cfg["unprotected_lowest"], cfg["unprotected_highest"]
    step = (highest - lowest) / (len(limits) - 1)
    # Only the lowest and highest bands are reported values; the rest are interpolated.
    return [(limit, lowest + step * i, 0 < i < len(limits) - 1) for i, limit in enumerate(limits)]


def protected_cost(units: float, cfg: dict) -> float:
    """Telescopic protected pricing: each slice of units is charged at its own rate."""
    cost, previous = 0.0, 0
    for limit, rate in cfg["protected_bands"]:
        slice_units = max(0.0, min(units, limit) - previous)
        cost += slice_units * rate
        previous = limit
    if units > previous:  # above the protected ceiling, keep the top protected rate
        cost += (units - previous) * cfg["protected_bands"][-1][1]
    return cost


def unprotected_cost(units: float, cfg: dict) -> tuple[float, float, bool]:
    """Non-telescopic pricing: the band the month reaches sets the rate for every unit."""
    for limit, rate, placeholder in unprotected_rates(cfg):
        if units <= limit:
            return units * rate, rate, placeholder
    limit, rate, placeholder = unprotected_rates(cfg)[-1]
    return units * rate, rate, placeholder


def estimate_bill(import_units: float, export_units: float, export_mode: str,
                  protected_eligible: bool, cfg: dict) -> dict:
    """Estimate the month's bill and report which pricing applied."""
    billed_units = import_units
    if export_mode == "net_metering":  # 1:1 offset, for comparison only
        billed_units = max(0.0, import_units - export_units)

    over_limit = billed_units > cfg["protected_limit_units"]
    use_protected = protected_eligible and not over_limit

    if use_protected:
        energy_cost, rate_used, placeholder = protected_cost(billed_units, cfg), None, False
    else:
        energy_cost, rate_used, placeholder = unprotected_cost(billed_units, cfg)

    export_credit = 0.0
    if export_mode == "net_billing":
        export_credit = export_units * cfg["export_rate_net_billing"]

    bill = energy_cost * cfg["taxes_multiplier"] - export_credit
    return {
        "billed_units": billed_units,
        "energy_cost_rs": energy_cost * cfg["taxes_multiplier"],
        "export_credit_rs": export_credit,
        "bill_rs": bill,
        "pricing": "protected" if use_protected else "unprotected",
        "unprotected_rate_rs": rate_used,
        "rate_is_placeholder": placeholder,
        "protected_kept": bool(use_protected),
        "loses_protected_status_for_6_months": bool(protected_eligible and over_limit),
    }
