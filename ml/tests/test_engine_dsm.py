"""dsm.dsm_penalty: the per-block formula by hand, the PPT worked example, and
the always-illustrative tag."""

from __future__ import annotations

import pytest

from lpmf.engines.dsm import dsm_penalty
from lpmf.provenance import ProvenanceKind


def test_ppt_example_60mw_over_41mw_limit_costs_3_475_lakh_per_hour():
    # Slides 4 and 7 (replaces the earlier ₹4.03 lakh/hr, whose inputs were
    # never published). An illustrative scenario: 60 MW deviation held for an
    # hour, 41 MW volume limit, ₹5,000/MWh normal rate, k = 1.5.
    out = dsm_penalty([60.0] * 4, 5000.0, 41.0, excess_multiplier=1.5)
    # 41 MW x ₹5,000 / 4 = ₹51,250 plus 19 MW x 1.5 x ₹5,000 / 4 = ₹35,625.
    assert out["per_block_rupees"] == pytest.approx([86_875.0] * 4)
    assert out["penalty_rupees"] == pytest.approx(347_500.0)
    assert out["penalty_rupees"] / 1e5 == pytest.approx(3.475)
    assert out["provenance"] == ProvenanceKind.ILLUSTRATIVE


def test_within_limit_is_charged_at_the_normal_rate():
    # 80 MW for one 15-min block = 20 MWh at ₹4,000/MWh.
    assert dsm_penalty(80.0, 4000.0, 100.0)["penalty_rupees"] == pytest.approx(80_000.0)


def test_excess_over_the_limit_is_charged_at_k_times_the_rate():
    # 100 MW within (₹1,00,000) + 20 MW excess x 1.5 x ₹4,000 / 4 (₹30,000).
    assert dsm_penalty(120.0, 4000.0, 100.0)["penalty_rupees"] == pytest.approx(130_000.0)
    assert dsm_penalty(120.0, 4000.0, 100.0, excess_multiplier=2.0)[
        "penalty_rupees"
    ] == pytest.approx(140_000.0)


def test_over_and_under_drawal_are_charged_alike():
    assert dsm_penalty(-120.0, 4000.0, 100.0)["penalty_rupees"] == pytest.approx(130_000.0)


def test_an_hour_of_blocks_is_summed():
    out = dsm_penalty([120.0, -120.0, 80.0, 0.0], 4000.0, 100.0)
    assert out["per_block_rupees"] == pytest.approx([130_000.0, 130_000.0, 80_000.0, 0.0])
    assert out["penalty_rupees"] == pytest.approx(340_000.0)
    assert out["n_blocks"] == 4


def test_always_flagged_illustrative():
    out = dsm_penalty(50.0, 4000.0, 100.0)
    assert out["is_illustrative"] is True
    assert out["provenance"] == ProvenanceKind.ILLUSTRATIVE
    assert "Illustrative" in out["note"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"normal_rate_per_mwh": -1.0, "schedule_limit_mw": 100.0},
        {"normal_rate_per_mwh": 4000.0, "schedule_limit_mw": -1.0},
        {"normal_rate_per_mwh": 4000.0, "schedule_limit_mw": 100.0, "excess_multiplier": -1.0},
    ],
)
def test_rejects_negative_rates_limits_and_multipliers(kwargs):
    with pytest.raises(ValueError):
        dsm_penalty(50.0, **kwargs)
