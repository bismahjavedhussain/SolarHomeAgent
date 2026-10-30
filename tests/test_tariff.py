"""Protected and unprotected pricing, band behaviour, fixed charges and export values."""
from __future__ import annotations

import pytest

from src.tariff import (band_index, band_limits, estimate_bill, fixed_charge,
                        protected_cost, protected_loss_cost, unprotected_cost)


def test_protected_pricing_is_telescopic(config):
    """Each slice of units is charged at its own protected rate."""
    cfg = config["tariff"]
    first, second = cfg["protected_bands"][0][1], cfg["protected_bands"][1][1]
    assert protected_cost(100, cfg) == pytest.approx(100 * first)
    assert protected_cost(200, cfg) == pytest.approx(100 * first + 100 * second)
    assert protected_cost(150, cfg) == pytest.approx(100 * first + 50 * second)


def test_unprotected_pricing_is_not_telescopic(config):
    """The band the month reaches sets the rate for every unit."""
    cfg = config["tariff"]
    cost, rate = unprotected_cost(250, cfg)
    assert cost == pytest.approx(250 * rate)
    _, lower_rate = unprotected_cost(150, cfg)
    assert lower_rate < rate  # a higher band means a higher rate on all units


def test_reported_band_rates_are_used_verbatim(config):
    """Rates come straight from config; none are interpolated any more."""
    cfg = config["tariff"]
    for limit, rate in cfg["unprotected_bands"]:
        units = min(limit, limit - 0.5) if limit < 999999 else 1000
        _, applied = unprotected_cost(units, cfg)
        assert applied == pytest.approx(rate)


def test_rates_increase_with_each_band(config):
    """Bands must be monotonically more expensive."""
    rates = [rate for _, rate in config["tariff"]["unprotected_bands"]]
    assert rates == sorted(rates)


def test_band_index_and_limits_line_up(config):
    """band_index picks the band whose limit first covers the usage."""
    cfg = config["tariff"]
    limits = band_limits(cfg)
    assert band_index(1, cfg) == 0
    assert band_index(limits[0], cfg) == 0
    assert band_index(limits[0] + 1, cfg) == 1
    assert band_index(10**9, cfg) == len(limits) - 1


def test_crossing_200_units_costs_far_more(config):
    """One unit over the protected ceiling moves the home to unprotected pricing."""
    cfg = config["tariff"]
    under = estimate_bill(199, 0, "none", True, cfg)
    over = estimate_bill(201, 0, "none", True, cfg)
    assert under["pricing"] == "protected"
    assert over["pricing"] == "unprotected"
    assert over["bill_rs"] > under["bill_rs"] * 2
    assert over["loses_protected_status_for_6_months"]
    assert not under["loses_protected_status_for_6_months"]


def test_protected_flag_only_applies_to_eligible_homes(config):
    """A home that was never protected cannot lose the status."""
    result = estimate_bill(150, 0, "none", False, config["tariff"])
    assert result["pricing"] == "unprotected"
    assert not result["loses_protected_status_for_6_months"]


def test_fixed_charge_scales_with_sanctioned_load(config):
    """Fixed charge is Rs per kW of sanctioned load, for the band reached."""
    cfg = dict(config["tariff"])
    heavy = 350  # a band that carries a fixed charge
    per_kw = cfg["fixed_charge_per_kw"][band_index(heavy, cfg)]
    assert per_kw > 0
    assert fixed_charge(heavy, False, cfg) == pytest.approx(per_kw * cfg["sanctioned_load_kw"])

    doubled = dict(cfg, sanctioned_load_kw=cfg["sanctioned_load_kw"] * 2)
    assert fixed_charge(heavy, False, doubled) == pytest.approx(2 * fixed_charge(heavy, False, cfg))


def test_protected_homes_pay_no_fixed_charge_by_default(config):
    """Protected consumers are exempt unless the config says otherwise."""
    cfg = config["tariff"]
    assert not cfg["fixed_charge_applies_to_protected"]
    assert fixed_charge(150, True, cfg) == 0.0
    assert estimate_bill(150, 0, "none", True, cfg)["fixed_charge_rs"] == 0.0


def test_fixed_charge_appears_in_the_bill(config):
    """A high-use month's bill includes the fixed charge on top of energy."""
    cfg = config["tariff"]
    result = estimate_bill(450, 0, "none", False, cfg)
    energy, _ = unprotected_cost(450, cfg)
    assert result["fixed_charge_rs"] > 0
    assert result["energy_cost_rs"] == pytest.approx(energy * cfg["taxes_multiplier"] + result["fixed_charge_rs"])


def test_six_month_loss_is_the_monthly_gap_times_the_months(config):
    """Losing protected status costs the protected-to-unprotected gap, every month it lasts."""
    cfg = config["tariff"]
    units = 210
    unprotected, _ = unprotected_cost(units, cfg)
    gap = unprotected + fixed_charge(units, False, cfg) - protected_cost(units, cfg)
    expected = gap * cfg["taxes_multiplier"] * cfg["protected_status_months"]
    assert protected_loss_cost(units, cfg) == pytest.approx(expected)
    assert protected_loss_cost(units, cfg) > 0


def test_export_values_by_mode(config):
    """Wasted solar earns nothing, net billing earns the reported rate, net metering offsets units."""
    cfg = config["tariff"]
    none = estimate_bill(300, 100, "none", False, cfg)
    billing = estimate_bill(300, 100, "net_billing", False, cfg)
    metering = estimate_bill(300, 100, "net_metering", False, cfg)

    assert none["export_credit_rs"] == 0.0
    assert billing["export_credit_rs"] == pytest.approx(100 * cfg["export_rate_net_billing"])
    assert billing["bill_rs"] < none["bill_rs"]

    assert metering["billed_units"] == pytest.approx(200)  # 1:1 offset
    assert metering["bill_rs"] < billing["bill_rs"]


def test_net_metering_cannot_make_units_negative(config):
    """Exporting more than you import floors the billed units at zero."""
    result = estimate_bill(50, 500, "net_metering", False, config["tariff"])
    assert result["billed_units"] == 0.0
