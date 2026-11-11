"""Tests for lpmf.features.build: no leakage across split boundaries, and
schema validation on the engineered output."""

from __future__ import annotations

import numpy as np
import pandas as pd

from lpmf.features.build import HORIZONS, MAJOR_HOLIDAYS, build_features
from lpmf.split import SplitBoundaries


def _make_frame(n_days: int = 30, start: str = "2024-01-01 00:00") -> pd.DataFrame:
    ts = pd.date_range(start, periods=n_days * 96, freq="15min", tz="Asia/Kolkata")
    n = len(ts)
    load = 4000 + 500 * np.sin(np.arange(n) * 2 * np.pi / 96) + np.arange(n) * 0.01
    temp = 25 + 8 * np.sin(np.arange(n) * 2 * np.pi / 96 - np.pi / 2)
    return pd.DataFrame(
        {
            "ts_ist": ts,
            "block": (np.arange(n) % 96) + 1,
            "date": ts.date,
            "load_mw": load,
            "imputed": False,
            "impute_method": "none",
            "is_outlier": False,
            "temp_c": temp,
            "rh_pct": 50.0,
            "dewpoint_c": 15.0,
            "ghi_wm2": 200.0,
            "wind_ms": 2.0,
            "cloud_pct": 30.0,
            "heat_index_c": temp,
            "is_holiday": False,
            "holiday_name": None,
            "dow": ts.day_of_week,
            "month": ts.month,
            "is_weekend": ts.day_of_week.isin([5, 6]),
            "data_source": "test-fixture",
            "is_synthetic": False,
        }
    )


def _even_split(df: pd.DataFrame) -> SplitBoundaries:
    ts = df["ts_ist"]
    n = len(ts)
    train_end_idx = n // 2
    val_end_idx = (3 * n) // 4
    return SplitBoundaries(
        train_start=ts.iloc[0].isoformat(),
        train_end=ts.iloc[train_end_idx].isoformat(),
        val_start=ts.iloc[train_end_idx + 1].isoformat(),
        val_end=ts.iloc[val_end_idx].isoformat(),
        test_start=ts.iloc[val_end_idx + 1].isoformat(),
        test_end=ts.iloc[-1].isoformat(),
    )


def test_build_features_schema_and_shape():
    df = _make_frame(n_days=30)
    boundaries = _even_split(df)
    features = build_features(df, boundaries)

    assert len(features) == len(df)
    for h in HORIZONS:
        assert f"target_h{h:02d}" in features.columns
    for col in [
        "load_lag_1block",
        "load_lag_1day",
        "load_lag_1week",
        "load_avg_same_block_trailing_4w",
        "load_roll_mean_24h",
        "load_roll_std_24h",
        "temp_roll_mean_24h",
        "night_temp_c",
        "sin_hour",
        "cos_hour",
        "sin_dow",
        "cos_dow",
        "sin_doy",
        "cos_doy",
        "is_ipl_season",
        "split",
    ]:
        assert col in features.columns


def test_no_target_leakage_across_split_boundary():
    df = _make_frame(n_days=30)
    boundaries = _even_split(df)
    features = build_features(df, boundaries)

    val_start = pd.Timestamp(boundaries.val_start)

    # Any train-split row whose horizon-h target timestamp lands at or
    # after val_start must have that target cell nulled, not the real
    # (val-period) future value.
    train_rows = features[features["split"] == "train"]
    for h in HORIZONS:
        target_ts = train_rows["ts_ist"] + pd.Timedelta(minutes=15 * h)
        crosses = target_ts >= val_start
        col = f"target_h{h:02d}"
        assert (
            train_rows.loc[crosses, col].isna().all()
        ), f"target_h{h:02d} leaked a val-period value into a train row"

    # And a target that does NOT cross the boundary should generally be
    # populated (not spuriously nulled), for at least one mid-train row.
    mid_train = train_rows.iloc[len(train_rows) // 2]
    assert pd.notna(mid_train["target_h01"])


def test_lag_features_match_manual_shift():
    df = _make_frame(n_days=14)
    boundaries = _even_split(df)
    features = build_features(df, boundaries)

    # Pick a row safely past all lookback windows (1 week = 672 blocks).
    idx = 800
    assert np.isclose(features.loc[idx, "load_lag_1block"], df.loc[idx - 1, "load_mw"])
    assert np.isclose(features.loc[idx, "load_lag_1day"], df.loc[idx - 96, "load_mw"])
    assert np.isclose(features.loc[idx, "load_lag_1week"], df.loc[idx - 672, "load_mw"])


def test_lag_features_nan_at_series_start_not_fabricated():
    df = _make_frame(n_days=14)
    boundaries = _even_split(df)
    features = build_features(df, boundaries)

    # The very first row cannot know anything about the past — these must
    # be NaN, never a fabricated/backfilled value.
    assert pd.isna(features.loc[0, "load_lag_1block"])
    assert pd.isna(features.loc[0, "load_lag_1day"])
    assert pd.isna(features.loc[0, "load_lag_1week"])


def test_cyclical_encodings_bounded():
    df = _make_frame(n_days=7)
    boundaries = _even_split(df)
    features = build_features(df, boundaries)

    for col in ["sin_hour", "cos_hour", "sin_dow", "cos_dow", "sin_doy", "cos_doy"]:
        assert features[col].between(-1.0001, 1.0001).all()


def test_holiday_tier_zero_for_non_holidays():
    df = _make_frame(n_days=7)
    boundaries = _even_split(df)
    features = build_features(df, boundaries)
    assert (features["holiday_tier"] == 0).all()


def test_holiday_tier_two_for_a_major_festival_and_one_for_a_minor_one():
    df = _make_frame(n_days=3)
    day0 = df["date"] == df["date"].iloc[0]
    day1 = df["date"] == df["date"].iloc[96]  # second day's blocks
    df.loc[day0, "is_holiday"] = True
    df.loc[day0, "holiday_name"] = "Diwali (Deepavali)"
    assert "Diwali (Deepavali)" in MAJOR_HOLIDAYS
    df.loc[day1, "is_holiday"] = True
    df.loc[day1, "holiday_name"] = "Ram Navami"  # not in MAJOR_HOLIDAYS
    boundaries = _even_split(df)
    features = build_features(df, boundaries)
    assert (features.loc[day0.to_numpy(), "holiday_tier"] == 2).all()
    assert (features.loc[day1.to_numpy(), "holiday_tier"] == 1).all()
