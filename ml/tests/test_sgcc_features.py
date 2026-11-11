"""sgcc.features: per-consumer features on small, hand-checkable series."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from lpmf.sgcc.features import FEATURE_NAMES, build_features
from lpmf.sgcc.load import SgccDataset


def _dataset(rows: list[list[float]]) -> SgccDataset:
    kwh = np.array(rows)
    n, d = kwh.shape
    return SgccDataset(
        cons_no=np.array([f"C{i}" for i in range(n)]),
        flag=np.zeros(n, dtype=int),
        dates=pd.DatetimeIndex(pd.date_range("2014-01-01", periods=d)),
        kwh=kwh,
    )


def test_output_shape_and_column_names():
    data = _dataset([[1.0, 2.0, 3.0, 4.0]] * 3)
    out = build_features(data)
    assert list(out.columns) == FEATURE_NAMES
    assert len(out) == 3
    assert out.index.tolist() == data.cons_no.tolist()


def test_mean_std_median_on_a_simple_series():
    out = build_features(_dataset([[10.0, 20.0, 30.0, 40.0]]))
    row = out.iloc[0]
    assert row["mean_kwh"] == pytest.approx(25.0)
    assert row["median_kwh"] == pytest.approx(25.0)
    assert row["std_kwh"] == pytest.approx(np.std([10, 20, 30, 40]))


def test_zero_day_frac_counts_exact_zeros():
    out = build_features(_dataset([[0.0, 0.0, 10.0, 10.0]]))
    assert out.iloc[0]["zero_day_frac"] == pytest.approx(0.5)


def test_constant_series_has_zero_std_and_zero_cv_and_zero_trend():
    out = build_features(_dataset([[5.0] * 20]))
    row = out.iloc[0]
    assert row["std_kwh"] == pytest.approx(0.0, abs=1e-9)
    assert row["cv"] == pytest.approx(0.0, abs=1e-9)
    assert row["trend_slope_per_rel"] == pytest.approx(0.0, abs=1e-9)
    assert row["max_drop_frac"] == pytest.approx(0.0, abs=1e-9)


def test_trend_slope_is_negative_for_a_declining_series():
    out = build_features(_dataset([list(np.linspace(100, 10, 60))]))
    assert out.iloc[0]["trend_slope_per_rel"] < 0


def test_sudden_drop_is_caught_by_max_drop_frac_and_drop_count():
    series = [10.0] * 10 + [1.0] * 10  # a sustained ~90% drop after day 10
    out = build_features(_dataset([series]))
    row = out.iloc[0]
    assert row["max_drop_frac"] > 0.5
    assert row["n_drops_over_50pct"] >= 1
