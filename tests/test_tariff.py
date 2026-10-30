"""Protected and unprotected pricing, band behaviour and export values."""
from __future__ import annotations

import pytest

from src.tariff import estimate_bill, protected_cost, unprotected_cost, unprotected_rates


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
    cost, rate, _ = unprotected_cost(250, cfg)
    assert cost == pytest.approx(250 * rate)
    cheaper, lower_rate, _ = unprotected_cost(150, cfg)
    assert lower_rate < rate  # a higher band means a higher rate on all units


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
    cfg = config["tariff"]
    result = estimate_bill(150, 0, "none", False, cfg)
    assert result["pricing"] == "unprotected"
    assert not result["loses_protected_status_for_6_months"]


def test_intermediate_bands_are_flagged_as_placeholders(config):
    """Only the lowest and highest unprotected bands are reported values."""
    bands = unprotected_rates(config["tariff"])
    assert not bands[0][2]
    assert not bands[-1][2]
    assert all(band[2] for band in bands[1:-1])
    assert bands[0][1] == config["tariff"]["unprotected_lowest"]
    assert bands[-1][1] == pytest.approx(config["tariff"]["unprotected_highest"])


def test_rates_increase_with_each_band(config):
    """Bands must be monotonically more expensive."""
    rates = [rate for _, rate, _ in unprotected_rates(config["tariff"])]
    assert rates == sorted(rates)


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
