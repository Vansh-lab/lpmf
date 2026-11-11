"""sgcc.features_experimental: the two candidate improvement features."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from lpmf.sgcc.features_experimental import (
    ADDITIONAL_FEATURE_NAMES,
    _recent_volatility_ratio,
    _weekly_pattern_break,
    build_additional_features,
)
from lpmf.sgcc.load import SgccDataset


def test_weekly_pattern_break_is_near_zero_for_a_stable_weekly_rhythm():
    dates = pd.date_range("2014-01-01", periods=70, freq="D")  # 10 full weeks
    dow = dates.day_of_week.values
    base = np.array([10.0, 10.0, 10.0, 10.0, 10.0, 20.0, 20.0])  # weekday/weekend split
    row = base[dow]
    assert _weekly_pattern_break(row, dates) == pytest.approx(0.0, abs=1e-6)


def test_weekly_pattern_break_is_high_when_the_rhythm_flips():
    dates = pd.date_range("2014-01-01", periods=70, freq="D")
    dow = dates.day_of_week.values
    first_half_shape = np.array([10.0, 10.0, 10.0, 10.0, 10.0, 20.0, 20.0])
    second_half_shape = np.array([20.0, 20.0, 20.0, 20.0, 20.0, 10.0, 10.0])  # inverted
    row = np.concatenate([first_half_shape[dow[:35]], second_half_shape[dow[35:]]])
    out = _weekly_pattern_break(row, dates)
    assert out > 1.0  # anticorrelated shapes -> break score above 1


def test_recent_volatility_ratio_above_one_when_recent_days_are_more_erratic():
    rng = np.random.default_rng(1)
    earlier = 10.0 + rng.normal(0, 0.5, 70)  # mildly noisy
    recent = np.array([5.0, 15.0, 5.0, 15.0, 5.0, 15.0, 5.0, 15.0, 5.0, 15.0] * 3)
    row = np.concatenate([earlier, recent])
    assert _recent_volatility_ratio(row, recent_frac=0.3) > 1.0


def test_recent_volatility_ratio_is_one_when_window_covers_everything():
    row = np.arange(10.0)
    assert _recent_volatility_ratio(row, recent_frac=1.5) == pytest.approx(1.0)


def test_build_additional_features_returns_expected_shape():
    dates = pd.date_range("2014-01-01", periods=30, freq="D")
    ds = SgccDataset(
        cons_no=np.array(["c1", "c2"]),
        dates=dates,
        kwh=np.random.default_rng(0).random((2, 30)),
        flag=np.array([0, 1]),
    )
    out = build_additional_features(ds)
    assert list(out.columns) == ADDITIONAL_FEATURE_NAMES
    assert list(out.index) == ["c1", "c2"]
    assert out.shape == (2, 2)
