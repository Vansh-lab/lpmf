"""iex_price.illustrative_hourly_price_per_mwh, iex_price.purchase_cost,
iex_price.load_real_price_profile."""

from __future__ import annotations

import json

import pytest

from lpmf.engines.iex_price import (
    EAC_PM_PRICE_RANGE,
    HOURS_PER_DAY,
    illustrative_hourly_price_per_mwh,
    load_real_price_profile,
    purchase_cost,
)
from lpmf.provenance import ProvenanceKind


def test_price_curve_peaks_at_the_expensive_hour_and_troughs_12h_later():
    curve = illustrative_hourly_price_per_mwh(1000.0, 9000.0, expensive_hour=20)
    assert len(curve) == HOURS_PER_DAY
    assert curve[20] == pytest.approx(9000.0)
    assert curve[8] == pytest.approx(1000.0)


def test_price_curve_stays_within_min_and_max():
    curve = illustrative_hourly_price_per_mwh(1000.0, 9000.0)
    assert all(1000.0 - 1e-9 <= p <= 9000.0 + 1e-9 for p in curve)


def test_price_curve_rejects_bad_range_or_hour():
    with pytest.raises(ValueError):
        illustrative_hourly_price_per_mwh(9000.0, 1000.0)
    with pytest.raises(ValueError):
        illustrative_hourly_price_per_mwh(-1.0, 1000.0)
    with pytest.raises(ValueError):
        illustrative_hourly_price_per_mwh(1000.0, 9000.0, expensive_hour=24)


def test_purchase_cost_matches_hand_computation():
    # 100 MW for one 15-min block at Rs 5,000/MWh: 100 x 0.25 x 5000 = 125,000.
    out = purchase_cost([100.0], [5000.0])
    assert out["cost_per_block_rupees"] == pytest.approx([125_000.0])
    assert out["total_cost_rupees"] == pytest.approx(125_000.0)
    assert out["is_illustrative"] is True
    assert out["provenance"] == ProvenanceKind.ILLUSTRATIVE


def test_purchase_cost_sums_over_blocks():
    out = purchase_cost([100.0, 200.0], [1000.0, 9000.0])
    assert out["total_cost_rupees"] == pytest.approx(100 * 0.25 * 1000 + 200 * 0.25 * 9000)


def test_purchase_cost_rejects_mismatched_lengths_or_negatives():
    with pytest.raises(ValueError):
        purchase_cost([100.0, 200.0], [1000.0])
    with pytest.raises(ValueError):
        purchase_cost([-1.0], [1000.0])
    with pytest.raises(ValueError):
        purchase_cost([100.0], [-1.0])


def test_eac_pm_price_range_is_tagged_foreign_and_matches_the_report():
    assert EAC_PM_PRICE_RANGE["provenance"] == ProvenanceKind.FOREIGN
    assert EAC_PM_PRICE_RANGE["midday_price_per_unit"] == pytest.approx(1.11)
    assert EAC_PM_PRICE_RANGE["night_price_per_unit"] == pytest.approx(9.71)


def test_load_real_price_profile_returns_none_when_artifacts_are_missing(tmp_path):
    assert load_real_price_profile(tmp_path / "does-not-exist") is None


def test_load_real_price_profile_loads_and_shapes_the_real_artifact(tmp_path):
    data = {
        "block_profile_per_mwh": [3000.0] * 96,
        "hourly_profile_per_mwh": [3000.0] * 24,
        "n_days_averaged": 2435,
        "date_range": ["2018-01-01 00:00:00", "2024-08-31 23:45:00"],
        "source": "Kaggle mukund604/indian-energy-exchange-time-series-forecasting",
    }
    (tmp_path / "price_profile.json").write_text(json.dumps(data))

    out = load_real_price_profile(tmp_path)

    assert out["provenance"] == ProvenanceKind.REAL
    assert out["n_days_averaged"] == 2435
    assert len(out["hourly_profile_per_mwh"]) == 24
    assert "typical-day" in out["note"]
