"""Tests for the gap-filling rules in lpmf.clean.load_clean.

<= 30 min   -> linear interpolation
30 min-3 hr -> same-time-of-day median of the 7 nearest same-weekday days
> 3 hr      -> left as NaN, never fabricated
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from lpmf.clean.load_clean import (
    IMPUTE_LINEAR,
    IMPUTE_NONE,
    IMPUTE_TOD_MEDIAN,
    clean_load,
    fill_gaps,
    resample_blocks,
)


def _make_regular_frame(n_days: int = 21, start="2024-01-01 00:00") -> pd.DataFrame:
    ts = pd.date_range(start, periods=n_days * 288, freq="5min", tz="Asia/Kolkata")
    # Smooth, deterministic synthetic-for-testing load curve (not shipped —
    # purely a test fixture).
    load = 4000 + 500 * np.sin(np.arange(len(ts)) * 2 * np.pi / 288)
    return pd.DataFrame({"ts_ist": ts, "load_mw": load})


def test_short_gap_linearly_interpolated():
    df = _make_regular_frame()
    df["is_outlier"] = False
    # Knock out a 20-minute gap (4 consecutive 5-min slots).
    gap_start = 500
    df.loc[gap_start : gap_start + 3, "load_mw"] = np.nan

    out = fill_gaps(df, log=_fresh_log())
    filled = out.loc[gap_start : gap_start + 3]
    assert filled["load_mw"].notna().all()
    assert (filled["impute_method"] == IMPUTE_LINEAR).all()
    assert filled["imputed"].all()


def test_medium_gap_filled_with_time_of_day_median():
    df = _make_regular_frame(n_days=21)
    df["is_outlier"] = False
    # Knock out a 1-hour gap (12 slots) in the middle of the series so there
    # are same-weekday neighbours on both sides.
    gap_start = 288 * 10 + 100
    gap_len = 12
    df.loc[gap_start : gap_start + gap_len - 1, "load_mw"] = np.nan

    out = fill_gaps(df, log=_fresh_log())
    filled = out.loc[gap_start : gap_start + gap_len - 1]
    assert filled["load_mw"].notna().all()
    assert (filled["impute_method"] == IMPUTE_TOD_MEDIAN).all()


def test_long_gap_left_as_nan():
    df = _make_regular_frame(n_days=21)
    df["is_outlier"] = False
    # Knock out a 4-hour gap (48 slots) -> must be left as NaN.
    gap_start = 288 * 10
    gap_len = 48
    df.loc[gap_start : gap_start + gap_len - 1, "load_mw"] = np.nan

    out = fill_gaps(df, log=_fresh_log())
    filled = out.loc[gap_start : gap_start + gap_len - 1]
    assert filled["load_mw"].isna().all()
    assert (filled["impute_method"] == IMPUTE_NONE).all()
    assert not filled["imputed"].any()


def _fresh_log():
    from lpmf.clean.load_clean import CleaningLog

    return CleaningLog()


def test_physically_impossible_values_flagged_and_nanned():
    from lpmf.clean.load_clean import CleaningLog, flag_physically_impossible

    df = _make_regular_frame(n_days=2)
    df["load_mw"] = df["load_mw"].astype(float)
    df.loc[10, "load_mw"] = -5.0  # impossible: <= 0
    df.loc[20, "load_mw"] = 50000.0  # impossible: > 12000 MW
    log = CleaningLog()
    out = flag_physically_impossible(df, log)

    assert pd.isna(out.loc[10, "load_mw"])
    assert pd.isna(out.loc[20, "load_mw"])
    assert out.loc[10, "is_outlier"]
    assert out.loc[20, "is_outlier"]
    # The implanted values also create impossible 5-min jumps on their
    # neighbouring slots, so the total flagged count is >= the 2 directly
    # implanted impossible values.
    assert log.physically_impossible_flagged >= 2


def test_duplicate_timestamps_dropped():
    from lpmf.clean.load_clean import CleaningLog, drop_duplicate_timestamps

    df = _make_regular_frame(n_days=1)
    dup_row = df.iloc[[5]]
    df_with_dupe = pd.concat([df, dup_row], ignore_index=True)
    log = CleaningLog()
    out = drop_duplicate_timestamps(df_with_dupe, log)
    assert log.duplicate_timestamps_dropped == 1
    assert not out["ts_ist"].duplicated().any()


def test_full_clean_load_no_dst_anomalies():
    df = _make_regular_frame(n_days=14)
    cleaned, log = clean_load(df)
    assert not cleaned["ts_ist"].duplicated().any()
    full_grid = pd.date_range(
        cleaned["ts_ist"].min(), cleaned["ts_ist"].max(), freq="5min", tz="Asia/Kolkata"
    )
    assert len(full_grid) == len(cleaned)


def test_resample_blocks_hourly_has_block_and_impute_method():
    # Regression test: the hourly frame used to be missing `block` and
    # `impute_method` entirely, which the final schema requires for both
    # the 15-min and hourly outputs — caught running the real pipeline.
    df = _make_regular_frame(n_days=2)
    df["is_outlier"] = False
    df["imputed"] = False
    df["impute_method"] = IMPUTE_NONE

    fifteen, hourly = resample_blocks(df)

    for frame in (fifteen, hourly):
        assert "block" in frame.columns
        assert "impute_method" in frame.columns
        assert frame["block"].between(1, 96).all()

    # Hourly block is the 15-min block of that hour's first slot: 1, 5, 9, ...
    assert set(hourly["block"].unique()) <= set(range(1, 97, 4))
