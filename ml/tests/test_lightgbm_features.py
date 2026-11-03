"""Alignment and look-ahead tests for the LightGBM long-format builder's
target-aligned load features."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from lpmf.features.build import HORIZONS
from lpmf.models.lightgbm import (
    ORIGIN_FEATURES,
    ORIGIN_FLAG_FEATURES,
    TARGET_ALIGNED_FEATURES,
    TARGET_CALENDAR_COLS,
    build_long_format,
)

BLOCK = pd.Timedelta(minutes=15)


def _features_frame(n_days: int = 30) -> pd.DataFrame:
    n = n_days * 96
    ts = pd.date_range("2024-01-01", periods=n, freq="15min", tz="Asia/Kolkata")
    # load == 1000 + row position, so every feature value names the exact
    # row it was read from.
    load = pd.Series(1000.0 + np.arange(n))
    df = pd.DataFrame({"ts_ist": ts, "load_mw": load, "split": "train"})
    for col in ORIGIN_FEATURES + ORIGIN_FLAG_FEATURES + TARGET_CALENDAR_COLS:
        df[col] = 0.0
    targets = pd.concat({f"target_h{h:02d}": load.shift(-h) for h in HORIZONS}, axis=1)
    return pd.concat([df, targets], axis=1)


def _positions(long_df: pd.DataFrame, ts0: pd.Timestamp) -> tuple[np.ndarray, np.ndarray]:
    origin = ((long_df["ts_origin"] - ts0) // BLOCK).to_numpy()
    return origin, long_df["horizon"].to_numpy()


def test_target_aligned_lags_point_at_the_target_block():
    df = _features_frame()
    long_df = build_long_format(df, "train")
    origin, h = _positions(long_df, df["ts_ist"].iloc[0])
    target = origin + h

    assert np.array_equal(long_df["actual_mw"], 1000.0 + target)
    assert np.array_equal(long_df["load_now"], 1000.0 + origin)

    day_ok = target - 96 >= 0
    assert np.array_equal(long_df["tlag_1day"][day_ok], 1000.0 + (target - 96)[day_ok])
    assert long_df["tlag_1day"][~day_ok].isna().all()

    week_ok = target - 672 >= 0
    assert np.array_equal(long_df["tlag_1week"][week_ok], 1000.0 + (target - 672)[week_ok])
    assert long_df["tlag_1week"][~week_ok].isna().all()

    # Trailing 4 weeks: mean over whichever of the 4 same-block weeks exist.
    weeks = np.stack([target - 672 * k for k in (1, 2, 3, 4)])
    expected_4w = np.array(
        [np.mean(1000.0 + col[col >= 0]) if (col >= 0).any() else np.nan for col in weeks.T]
    )
    assert np.allclose(long_df["tlag_4w_avg"], expected_4w, equal_nan=True)

    shift_ok = origin - 96 >= 0
    assert np.all(long_df["level_shift_1day"][shift_ok] == 96.0)
    assert long_df["level_shift_1day"][~shift_ok].isna().all()


def test_target_aligned_lags_never_read_past_the_origin():
    df = _features_frame()
    origin_ts = df["ts_ist"].iloc[20 * 96 + 37]
    tampered = df.copy()
    tampered.loc[tampered["ts_ist"] > origin_ts, "load_mw"] *= 5.0

    def rows_for_origin(frame: pd.DataFrame) -> pd.DataFrame:
        long_df = build_long_format(frame, "train")
        return long_df[long_df["ts_origin"] == origin_ts].reset_index(drop=True)

    before, after = rows_for_origin(df), rows_for_origin(tampered)
    assert len(before) == len(HORIZONS)
    pd.testing.assert_frame_equal(before[TARGET_ALIGNED_FEATURES], after[TARGET_ALIGNED_FEATURES])


def test_labels_come_from_target_columns_and_split_nulls_are_dropped():
    df = _features_frame()
    n = len(df)
    df["split"] = np.where(np.arange(n) < 20 * 96, "train", "val")
    df.loc[[300, 301, 2500], "load_mw"] = np.nan
    load = df["load_mw"]
    # Labels deliberately differ from load (negated) and are nulled wherever
    # the target crosses the split boundary, as features.parquet does.
    for h in HORIZONS:
        target = -load.shift(-h)
        crosses = df["split"] != df["split"].shift(-h)
        df[f"target_h{h:02d}"] = target.where(~crosses)

    for split in ("train", "val"):
        long_df = build_long_format(df, split)
        rows = df["split"] == split
        expected = int(df.loc[rows, [f"target_h{h:02d}" for h in HORIZONS]].notna().sum().sum())
        assert len(long_df) == expected
        assert long_df["actual_mw"].notna().all()
        origin, h = _positions(long_df, df["ts_ist"].iloc[0])
        assert np.allclose(long_df["actual_mw"], -(1000.0 + origin + h))


def test_target_calendar_is_read_at_the_target_row():
    df = _features_frame(n_days=10)
    df["dow"] = df["ts_ist"].dt.day_of_week.astype(float)
    df["sin_hour"] = np.arange(len(df)) % 96 / 96.0

    long_df = build_long_format(df, "train")
    origin, h = _positions(long_df, df["ts_ist"].iloc[0])
    target = origin + h
    assert np.array_equal(long_df["target_dow"], df["dow"].to_numpy()[target])
    assert np.allclose(long_df["target_sin_hour"], df["sin_hour"].to_numpy()[target])


def test_build_long_format_rejects_a_gappy_grid():
    df = _features_frame(n_days=10).drop(index=500)
    with pytest.raises(ValueError, match="gap-free 15-min grid"):
        build_long_format(df, "train")
