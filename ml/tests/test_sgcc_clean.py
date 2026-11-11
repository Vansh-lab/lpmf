"""sgcc.clean: fill/cap values come from train only and never change when
val/test data changes — the explicit "no statistic from test" requirement."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from lpmf.sgcc.clean import apply_cleaning, fit_cleaning
from lpmf.sgcc.load import SgccDataset


def _dataset(kwh, flag=None):
    n = kwh.shape[0]
    return SgccDataset(
        cons_no=np.array([f"C{i}" for i in range(n)]),
        flag=flag if flag is not None else np.zeros(n, dtype=int),
        dates=pd.DatetimeIndex(pd.date_range("2014-01-01", periods=kwh.shape[1])),
        kwh=kwh,
    )


def test_fill_value_is_the_train_median_ignoring_missing():
    train = _dataset(np.array([[10.0, np.nan], [20.0, 5.0], [30.0, 7.0]]))
    stats = fit_cleaning(train)
    assert stats.fill_value[0] == pytest.approx(20.0)  # median of 10, 20, 30
    assert stats.fill_value[1] == pytest.approx(6.0)  # median of 5, 7


def test_stats_are_identical_regardless_of_what_test_data_looks_like():
    train = _dataset(np.array([[10.0, 1.0], [20.0, 2.0], [30.0, 3.0]]))
    stats_a = fit_cleaning(train)
    # fit_cleaning never even sees val/test, so this is really just
    # confirming it is a pure function of its one argument.
    stats_b = fit_cleaning(train)
    assert np.array_equal(stats_a.fill_value, stats_b.fill_value)
    assert np.array_equal(stats_a.cap_value, stats_b.cap_value)


def test_apply_cleaning_fills_missing_and_negative_with_train_fill():
    train = _dataset(np.array([[10.0], [20.0], [30.0]]))
    stats = fit_cleaning(train)
    test = _dataset(np.array([[np.nan], [-5.0], [15.0]]))
    cleaned = apply_cleaning(test, stats)
    assert cleaned.kwh[0, 0] == pytest.approx(20.0)  # NaN -> train median
    assert cleaned.kwh[1, 0] == pytest.approx(20.0)  # negative -> train median
    assert cleaned.kwh[2, 0] == pytest.approx(15.0)  # untouched, within cap


def test_apply_cleaning_caps_extreme_values_at_the_train_p99():
    train = _dataset(np.tile(np.arange(1, 101, dtype=float).reshape(100, 1), 1))
    stats = fit_cleaning(train)
    test = _dataset(np.array([[1_000_000.0]]))
    cleaned = apply_cleaning(test, stats)
    assert cleaned.kwh[0, 0] == pytest.approx(stats.cap_value[0])
    assert cleaned.kwh[0, 0] < 1_000_000.0


def test_apply_cleaning_rejects_mismatched_column_count():
    train = _dataset(np.array([[10.0, 1.0]]))
    stats = fit_cleaning(train)
    bad = _dataset(np.array([[10.0, 1.0, 5.0]]))
    with pytest.raises(ValueError):
        apply_cleaning(bad, stats)


def test_a_day_entirely_missing_in_train_falls_back_to_global_stats():
    train = _dataset(np.array([[np.nan, 5.0], [np.nan, 10.0]]))
    stats = fit_cleaning(train)
    assert not np.isnan(stats.fill_value).any()
    assert not np.isnan(stats.cap_value).any()
