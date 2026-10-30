"""Monthly electricity bill under Pakistan's protected and unprotected bands.

Rates are as reported for 2026 (S.R.O. 279(I)/2026) and must be verified against NEPRA.
"""
from __future__ import annotations

RATES_NOTE = "reported S.R.O. 279(I)/2026 - verify against NEPRA"


def band_limits(cfg: dict) -> list[int]:
    """The non-telescopic band edges, where crossing re-prices every unit."""
    return [limit for limit, _ in cfg["unprotected_bands"]]


def band_index(units: float, cfg: dict) -> int:
    """Which unprotected band a month's usage lands in."""
    for index, (limit, _) in enumerate(cfg["unprotected_bands"]):
        if units <= limit:
            return index
    return len(cfg["unprotected_bands"]) - 1


def protected_cost(units: float, cfg: dict) -> float:
    """Telescopic protected pricing: each slice of units is charged at its own rate."""
    cost, previous = 0.0, 0
    for limit, rate in cfg["protected_bands"]:
        cost += max(0.0, min(units, limit) - previous) * rate
        previous = limit
    if units > previous:  # above the protected ceiling, keep the top protected rate
        cost += (units - previous) * cfg["protected_bands"][-1][1]
    return cost


def unprotected_cost(units: float, cfg: dict) -> tuple[float, float]:
    """Non-telescopic pricing: the band the month reaches sets the rate for every unit."""
    rate = cfg["unprotected_bands"][band_index(units, cfg)][1]
    return units * rate, rate


def fixed_charge(units: float, protected: bool, cfg: dict) -> float:
    """Fixed charge in Rs, from sanctioned load and the band reached."""
    if protected and not cfg.get("fixed_charge_applies_to_protected", False):
        return 0.0
    per_kw = cfg["fixed_charge_per_kw"][band_index(units, cfg)]
    return per_kw * cfg["sanctioned_load_kw"]


def protected_loss_cost(future_units: float, cfg: dict) -> float:
    """Cost of the months spent on unprotected rates after crossing, at a later month's usage.

    A month over the limit cannot itself be priced as protected, so the penalty is not that
    month's gap. It is what the following months cost while the home is still unprotected,
    even once its usage is back under the limit.
    """
    unprotected_energy, _ = unprotected_cost(future_units, cfg)
    monthly_extra = (
        (unprotected_energy - protected_cost(future_units, cfg)) * cfg["taxes_multiplier"]
        + fixed_charge(future_units, False, cfg) - fixed_charge(future_units, True, cfg)
    )
    return max(0.0, monthly_extra) * cfg["protected_status_months"]


def estimate_bill(import_units: float, export_units: float, export_mode: str,
                  protected_eligible: bool, cfg: dict) -> dict:
    """Estimate the month's bill and report which pricing applied."""
    billed_units = import_units
    if export_mode == "net_metering":  # 1:1 offset, for comparison only
        billed_units = max(0.0, import_units - export_units)

    over_limit = billed_units > cfg["protected_limit_units"]
    use_protected = protected_eligible and not over_limit

    if use_protected:
        energy_cost, rate_used = protected_cost(billed_units, cfg), None
    else:
        energy_cost, rate_used = unprotected_cost(billed_units, cfg)

    fixed = fixed_charge(billed_units, use_protected, cfg)
    export_credit = export_units * cfg["export_rate_net_billing"] if export_mode == "net_billing" else 0.0

    energy_total = energy_cost * cfg["taxes_multiplier"] + fixed
    return {
        "billed_units": billed_units,
        "energy_cost_rs": energy_total,
        "fixed_charge_rs": fixed,
        "export_credit_rs": export_credit,
        "bill_rs": energy_total - export_credit,
        "pricing": "protected" if use_protected else "unprotected",
        "unprotected_rate_rs": rate_used,
        "band_index": band_index(billed_units, cfg),
        "rates_note": RATES_NOTE,
        "protected_kept": bool(use_protected),
        "loses_protected_status_for_6_months": bool(protected_eligible and over_limit),
    }
