"""tod_bill.tod_bill, tod_bill.shift_load: formula and worked examples."""

from __future__ import annotations

import pytest

from lpmf.engines.tod_bill import DERC_TOD_RATES, HOURS_PER_DAY, shift_load, tod_bill
from lpmf.provenance import ProvenanceKind

PEAK = [17, 18, 19, 20, 21]
OFF_PEAK = [22, 23, 0, 1, 2, 3, 4, 5]


def test_flat_1kwh_profile_matches_hand_computed_tod_bill():
    # 24 x 1 kWh at Rs 8/kWh: flat = 192. ToD: 5 peak h x 8 x 1.3 = 52,
    # 8 off-peak h x 8 x 0.75 = 48, 11 normal h x 8 = 88 -> 188.
    out = tod_bill([1.0] * HOURS_PER_DAY, 8.0, PEAK, OFF_PEAK, 30.0, 25.0)
    assert out["flat_bill_rupees"] == pytest.approx(192.0)
    assert out["tod_bill_rupees"] == pytest.approx(188.0)
    assert out["savings_rupees"] == pytest.approx(4.0)
    assert out["is_illustrative"] is True
    assert out["provenance"] == ProvenanceKind.ILLUSTRATIVE


def test_all_load_in_peak_hours_costs_more_under_tod():
    profile = [0.0] * HOURS_PER_DAY
    for h in PEAK:
        profile[h] = 10.0
    out = tod_bill(profile, 8.0, PEAK, OFF_PEAK, 30.0, 25.0)
    assert out["savings_rupees"] < 0  # ToD costs MORE: no reason to shift away from peak here
    assert out["tod_bill_rupees"] == pytest.approx(out["flat_bill_rupees"] * 1.3)


def test_all_load_in_off_peak_hours_is_cheaper_under_tod():
    profile = [0.0] * HOURS_PER_DAY
    for h in OFF_PEAK:
        profile[h] = 10.0
    out = tod_bill(profile, 8.0, PEAK, OFF_PEAK, 30.0, 25.0)
    assert out["savings_rupees"] > 0
    assert out["tod_bill_rupees"] == pytest.approx(out["flat_bill_rupees"] * 0.75)


def test_derc_tod_rates_are_real_and_sourced():
    assert DERC_TOD_RATES["provenance"] == ProvenanceKind.REAL
    assert DERC_TOD_RATES["peak_surcharge_pct"] == pytest.approx(20.0)
    assert DERC_TOD_RATES["off_peak_rebate_pct"] == pytest.approx(20.0)
    assert "DERC" in DERC_TOD_RATES["source"]
    assert "clause 3(d)" in DERC_TOD_RATES["source"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "hourly_kwh": [1.0] * 23,
            "base_rate_per_kwh": 8.0,
            "peak_hours": PEAK,
            "off_peak_hours": OFF_PEAK,
            "peak_surcharge_pct": 30.0,
            "off_peak_rebate_pct": 25.0,
        },
        {
            "hourly_kwh": [-1.0] * 24,
            "base_rate_per_kwh": 8.0,
            "peak_hours": PEAK,
            "off_peak_hours": OFF_PEAK,
            "peak_surcharge_pct": 30.0,
            "off_peak_rebate_pct": 25.0,
        },
        {
            "hourly_kwh": [1.0] * 24,
            "base_rate_per_kwh": -8.0,
            "peak_hours": PEAK,
            "off_peak_hours": OFF_PEAK,
            "peak_surcharge_pct": 30.0,
            "off_peak_rebate_pct": 25.0,
        },
        {
            "hourly_kwh": [1.0] * 24,
            "base_rate_per_kwh": 8.0,
            "peak_hours": [25],
            "off_peak_hours": OFF_PEAK,
            "peak_surcharge_pct": 30.0,
            "off_peak_rebate_pct": 25.0,
        },
        {
            "hourly_kwh": [1.0] * 24,
            "base_rate_per_kwh": 8.0,
            "peak_hours": [5],
            "off_peak_hours": [5],
            "peak_surcharge_pct": 30.0,
            "off_peak_rebate_pct": 25.0,
        },
        {
            "hourly_kwh": [1.0] * 24,
            "base_rate_per_kwh": 8.0,
            "peak_hours": PEAK,
            "off_peak_hours": OFF_PEAK,
            "peak_surcharge_pct": 200.0,
            "off_peak_rebate_pct": 25.0,
        },
    ],
)
def test_rejects_invalid_tod_bill_inputs(kwargs):
    with pytest.raises(ValueError):
        tod_bill(**kwargs)


def test_shift_load_moves_energy_and_conserves_total():
    profile = [0.0] * HOURS_PER_DAY
    profile[18] = 10.0
    shifted = shift_load(profile, [18], [2, 3], 0.5)
    assert shifted[18] == pytest.approx(5.0)
    assert shifted[2] == pytest.approx(2.5)
    assert shifted[3] == pytest.approx(2.5)
    assert sum(shifted) == pytest.approx(sum(profile))


def test_shift_load_rejects_bad_fraction_or_empty_destination():
    with pytest.raises(ValueError):
        shift_load([1.0] * HOURS_PER_DAY, [18], [2], 1.5)
    with pytest.raises(ValueError):
        shift_load([1.0] * HOURS_PER_DAY, [18], [], 0.5)
