"""losses.pf_correction, losses.i2r_loss: textbook worked examples."""

from __future__ import annotations

import pytest

from lpmf.engines.losses import (
    AT_C_BENCHMARK,
    current_after_pf_correction,
    i2r_loss,
    loss_reduction_pct,
    pf_correction,
)
from lpmf.provenance import ProvenanceKind


def test_pf_correction_to_unity_matches_textbook_formula():
    # P.V.K. Mehta Ch. 6: Q_c = P(tan phi1 - tan phi2). 100 kW at 0.8 lag PF,
    # corrected to unity: tan(acos 0.8) = 0.75, tan(acos 1.0) = 0.
    out = pf_correction(100.0, 0.8, 1.0)
    assert out["capacitor_kvar"] == pytest.approx(75.0)
    assert out["tan_phi2"] == pytest.approx(0.0, abs=1e-9)
    assert out["provenance"] == ProvenanceKind.ILLUSTRATIVE


def test_pf_correction_to_a_partial_target():
    out = pf_correction(100.0, 0.8, 0.95)
    assert out["capacitor_kvar"] == pytest.approx(42.1316, rel=1e-4)


def test_pf_correction_at_unity_already_needs_no_capacitor():
    assert pf_correction(500.0, 1.0, 1.0)["capacitor_kvar"] == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"active_power_kw": -1.0, "pf1": 0.8, "pf2": 0.95},
        {"active_power_kw": 100.0, "pf1": 0.0, "pf2": 0.95},
        {"active_power_kw": 100.0, "pf1": 0.8, "pf2": 1.5},
        {"active_power_kw": 100.0, "pf1": 0.95, "pf2": 0.8},  # pf2 < pf1
    ],
)
def test_rejects_invalid_pf_correction_inputs(kwargs):
    with pytest.raises(ValueError):
        pf_correction(**kwargs)


def test_i2r_loss_three_phase_formula():
    # 100 A per phase through a 0.5 ohm/phase feeder: 3 x 100^2 x 0.5 = 15,000 W.
    out = i2r_loss(100.0, 0.5)
    assert out["loss_w"] == pytest.approx(15_000.0)
    assert out["loss_kw"] == pytest.approx(15.0)
    assert out["provenance"] == ProvenanceKind.ILLUSTRATIVE


def test_i2r_loss_single_phase():
    assert i2r_loss(100.0, 0.5, phases=1)["loss_w"] == pytest.approx(5_000.0)


def test_i2r_loss_rejects_negative_or_bad_phase_count():
    with pytest.raises(ValueError):
        i2r_loss(-1.0, 0.5)
    with pytest.raises(ValueError):
        i2r_loss(100.0, -0.5)
    with pytest.raises(ValueError):
        i2r_loss(100.0, 0.5, phases=2)


def test_current_after_pf_correction_scales_inversely_with_pf():
    # P = sqrt(3) V I PF held constant: I2 = I1 x pf1 / pf2.
    assert current_after_pf_correction(100.0, 0.8, 1.0) == pytest.approx(80.0)
    assert current_after_pf_correction(100.0, 1.0, 1.0) == pytest.approx(100.0)


def test_current_after_pf_correction_rejects_bad_pf():
    with pytest.raises(ValueError):
        current_after_pf_correction(100.0, 0.0, 1.0)
    with pytest.raises(ValueError):
        current_after_pf_correction(-1.0, 0.8, 1.0)


def test_loss_reduction_pct_scales_with_current_squared():
    # Current drops 100 A -> 80 A (20% drop): loss drops 1 - 0.8^2 = 36%.
    assert loss_reduction_pct(100.0, 0.5, 80.0) == pytest.approx(36.0)


def test_loss_reduction_pct_zero_current_is_100_percent_saved():
    assert loss_reduction_pct(100.0, 0.5, 0.0) == pytest.approx(100.0)


def test_loss_reduction_pct_rejects_increase_or_bad_base():
    with pytest.raises(ValueError):
        loss_reduction_pct(0.0, 0.5, 0.0)
    with pytest.raises(ValueError):
        loss_reduction_pct(100.0, 0.5, 120.0)


def test_at_c_benchmark_is_tagged_foreign_not_delhi_specific():
    # National figure (Rajya Sabha PQ 266, 27 Nov 2024), not a Delhi/BRPL
    # measurement, so it must not be tagged REAL.
    assert AT_C_BENCHMARK["provenance"] == ProvenanceKind.FOREIGN
    assert AT_C_BENCHMARK["at_c_loss_pct"] == pytest.approx(15.37)
