"""Tests for lpmf.synthetic.generate: provenance tagging, schema shape,
and sanity checks on the shape-comparison metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from lpmf.provenance import ProvenanceKind
from lpmf.synthetic.generate import (
    CATEGORY_SPECS,
    _ldc_shape_distance,
    _load_duration_curve,
    compare_shape_to_real,
    generate_all,
    generate_category,
)


def _make_backbone(n_days: int = 21) -> pd.DataFrame:
    ts = pd.date_range("2024-01-01", periods=n_days * 96, freq="15min", tz="Asia/Kolkata")
    n = len(ts)
    hour = ts.hour + ts.minute / 60.0
    # A deliberately evening-peaked real series, so the residential-heavy
    # synthetic sum (also evening-peaked) should land close in timing.
    load = 4000 + 600 * np.exp(-0.5 * ((np.array(hour) - 20.0) / 2.5) ** 2)
    return pd.DataFrame(
        {
            "ts_ist": ts,
            "block": (np.arange(n) % 96) + 1,
            "date": ts.date,
            "load_mw": load,
            "temp_c": 28.0,
            "heat_index_c": 30.0,
            "dow": ts.day_of_week,
            "month": ts.month,
            "is_weekend": ts.day_of_week.isin([5, 6]),
            "is_holiday": False,
            "is_ipl_season": False,
        }
    )


def test_every_category_tagged_synthetic_and_provenance_reused():
    backbone = _make_backbone()
    results = generate_all(backbone, seed=1)

    assert set(results.keys()) == {spec.name for spec in CATEGORY_SPECS}
    for name, frame in results.items():
        assert (frame["data_source"] == "synthetic_parametric").all()
        assert frame["is_synthetic"].all()
        # Reuses the Phase-0 enum rather than a new string literal scheme.
        assert ProvenanceKind.SYNTHETIC.value == "SYNTHETIC"
        assert (frame["load_mw"] >= 0).all(), f"{name} produced a negative load"
        assert frame["load_mw"].notna().all()
        assert len(frame) == len(backbone)


def test_generate_category_reproducible_with_same_seed():
    backbone = _make_backbone()
    spec = CATEGORY_SPECS[0]
    a = generate_category(backbone, spec, np.random.default_rng(42))
    b = generate_category(backbone, spec, np.random.default_rng(42))
    pd.testing.assert_series_equal(a["load_mw"], b["load_mw"])


def test_generate_category_preserves_timezone():
    backbone = _make_backbone()
    spec = CATEGORY_SPECS[0]
    out = generate_category(backbone, spec, np.random.default_rng(1))
    assert out["ts_ist"].dt.tz is not None
    assert str(out["ts_ist"].dt.tz) == "Asia/Kolkata"


def test_ldc_shape_distance_zero_for_identical_curves():
    load = pd.Series(np.linspace(1000, 5000, 500))
    ldc = _load_duration_curve(load)
    assert _ldc_shape_distance(ldc, ldc) == pytest.approx(0.0, abs=1e-9)


def test_compare_shape_to_real_runs_and_returns_expected_keys():
    backbone = _make_backbone()
    results = generate_all(backbone, seed=7)
    synthetic_sum = sum(f.set_index("ts_ist")["load_mw"] for f in results.values())
    synthetic_sum = synthetic_sum.reindex(backbone["ts_ist"]).reset_index(drop=True)

    comparison = compare_shape_to_real(backbone, synthetic_sum)
    expected_keys = {
        "real_peak_hour",
        "synthetic_peak_hour",
        "peak_hour_diff_hours",
        "real_peak_timing_std_hours",
        "synthetic_peak_timing_std_hours",
        "ldc_shape_mean_abs_diff",
        "real_lag1day_autocorr",
        "synthetic_lag1day_autocorr",
        "lag1day_autocorr_diff",
    }
    assert set(comparison.keys()) == expected_keys
    for v in comparison.values():
        assert np.isfinite(v)
