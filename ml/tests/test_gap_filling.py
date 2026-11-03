"""Tests for the causal gap-filling rules in lpmf.clean.load_clean.

<= 30 min   -> forward fill from the last observed reading
30 min-3 hr -> past-5-day same-slot median profile, scaled to the last
               observed reading before the gap (NaN without that history)
> 3 hr      -> left as NaN, never fabricated
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from lpmf.clean.load_clean import (
    IMPUTE_FFILL,
    IMPUTE_NONE,
    IMPUTE_TOD_PROFILE,
    CleaningLog,
    clean_load,
    fill_gaps,
    resample_blocks,
)

SLOTS_PER_DAY = 288


def _make_regular_frame(n_days: int = 21, start="2024-01-01 00:00") -> pd.DataFrame:
    ts = pd.date_range(start, periods=n_days * SLOTS_PER_DAY, freq="5min", tz="Asia/Kolkata")
    # Smooth, deterministic synthetic-for-testing load curve with an exact
    # one-day period (not shipped — purely a test fixture).
    load = 4000 + 500 * np.sin(np.arange(len(ts)) * 2 * np.pi / SLOTS_PER_DAY)
    df = pd.DataFrame({"ts_ist": ts, "load_mw": load})
    df["is_outlier"] = False
    return df


def _knock_out(df: pd.DataFrame, start: int, length: int) -> pd.DataFrame:
    out = df.copy()
    out.loc[start : start + length - 1, "load_mw"] = np.nan
    return out


def test_short_gap_forward_filled():
    df = _make_regular_frame()
    gap_start = 500
    holed = _knock_out(df, gap_start, 4)  # 20 minutes

    out = fill_gaps(holed, log=CleaningLog())
    filled = out.loc[gap_start : gap_start + 3]
    assert np.allclose(filled["load_mw"], df.loc[gap_start - 1, "load_mw"])
    assert (filled["impute_method"] == IMPUTE_FFILL).all()
    assert filled["imputed"].all()


def test_short_gap_fill_ignores_the_future():
    df = _make_regular_frame()
    gap_start = 500
    holed = _knock_out(df, gap_start, 4)
    tampered = holed.copy()
    tampered.loc[gap_start + 4 :, "load_mw"] *= 3.0

    base = fill_gaps(holed, log=CleaningLog()).loc[gap_start : gap_start + 3, "load_mw"]
    after = fill_gaps(tampered, log=CleaningLog()).loc[gap_start : gap_start + 3, "load_mw"]
    assert np.allclose(base, after)


def test_medium_gap_filled_with_past_profile():
    df = _make_regular_frame(n_days=21)
    gap_start = SLOTS_PER_DAY * 10 + 100
    gap_len = 12  # 1 hour
    holed = _knock_out(df, gap_start, gap_len)

    out = fill_gaps(holed, log=CleaningLog())
    filled = out.loc[gap_start : gap_start + gap_len - 1]
    truth = df.loc[gap_start : gap_start + gap_len - 1, "load_mw"]
    # Every day of the fixture is identical, so the past profile is exact.
    assert np.allclose(filled["load_mw"], truth)
    assert (filled["impute_method"] == IMPUTE_TOD_PROFILE).all()
    assert filled["imputed"].all()


def test_medium_gap_scales_profile_to_current_level():
    df = _make_regular_frame(n_days=21)
    # A 10% level shift two days before the gap: the past-5-day median still
    # sits at the old level, so only the anchor can recover the new one.
    df.loc[SLOTS_PER_DAY * 8 :, "load_mw"] *= 1.10
    gap_start = SLOTS_PER_DAY * 10 + 100
    gap_len = 12
    holed = _knock_out(df, gap_start, gap_len)

    out = fill_gaps(holed, log=CleaningLog())
    filled = out.loc[gap_start : gap_start + gap_len - 1, "load_mw"]
    truth = df.loc[gap_start : gap_start + gap_len - 1, "load_mw"]
    assert np.allclose(filled, truth)


def test_medium_gap_fill_ignores_the_future():
    df = _make_regular_frame(n_days=21)
    gap_start = SLOTS_PER_DAY * 10 + 100
    gap_len = 12
    holed = _knock_out(df, gap_start, gap_len)
    tampered = holed.copy()
    # Everything after the gap, including the same slots on later days that
    # a two-sided same-slot median would have borrowed.
    tampered.loc[gap_start + gap_len :, "load_mw"] *= 3.0

    base = fill_gaps(holed, log=CleaningLog()).loc[gap_start : gap_start + gap_len - 1, "load_mw"]
    after = fill_gaps(tampered, log=CleaningLog()).loc[
        gap_start : gap_start + gap_len - 1, "load_mw"
    ]
    assert np.allclose(base, after)


def test_medium_gap_profile_pairs_slot_and_anchor_from_the_same_day():
    # Regression test: separate medians for the slot and the anchor, taken
    # over different subsets of days, invented values (incl. a fake annual
    # peak). Days 7-8 run 50% hot and day 9 lacks the gap's slots, so the two
    # medians disagree; per-day scaling stays exact.
    df = _make_regular_frame(n_days=21)
    for day in (7, 8):
        df.loc[SLOTS_PER_DAY * day : SLOTS_PER_DAY * (day + 1) - 1, "load_mw"] *= 1.5
    gap_start = SLOTS_PER_DAY * 10 + 100
    gap_len = 12
    truth = df.loc[gap_start : gap_start + gap_len - 1, "load_mw"].copy()
    holed = _knock_out(df, gap_start, gap_len)
    holed = _knock_out(holed, gap_start - SLOTS_PER_DAY, gap_len)

    out = fill_gaps(holed, log=CleaningLog())
    assert np.allclose(out.loc[gap_start : gap_start + gap_len - 1, "load_mw"], truth)


def test_medium_gap_fill_ignores_days_beyond_the_lookback():
    df = _make_regular_frame(n_days=21)
    gap_start = SLOTS_PER_DAY * 10 + 100
    gap_len = 12
    holed = _knock_out(df, gap_start, gap_len)
    tampered = holed.copy()
    tampered.loc[SLOTS_PER_DAY * 4 : SLOTS_PER_DAY * 5 - 1, "load_mw"] *= 3.0  # 6 days back

    base = fill_gaps(holed, log=CleaningLog()).loc[gap_start : gap_start + gap_len - 1, "load_mw"]
    after = fill_gaps(tampered, log=CleaningLog()).loc[
        gap_start : gap_start + gap_len - 1, "load_mw"
    ]
    assert np.allclose(base, after)


def test_leading_short_gap_left_nan_and_counted():
    holed = _knock_out(_make_regular_frame(), 0, 4)

    log = CleaningLog()
    out = fill_gaps(holed, log=log)
    assert out.loc[:3, "load_mw"].isna().all()
    assert not out.loc[:3, "imputed"].any()
    assert log.gaps_short_left_nan == 4


def test_medium_gap_without_history_left_nan():
    df = _make_regular_frame(n_days=21)
    gap_start = 100  # day 0: there is no earlier day to build a profile from
    gap_len = 12
    holed = _knock_out(df, gap_start, gap_len)

    log = CleaningLog()
    out = fill_gaps(holed, log=log)
    filled = out.loc[gap_start : gap_start + gap_len - 1]
    assert filled["load_mw"].isna().all()
    assert (filled["impute_method"] == IMPUTE_NONE).all()
    assert not filled["imputed"].any()
    assert log.gaps_medium_left_nan == gap_len


def test_long_gap_left_as_nan():
    df = _make_regular_frame(n_days=21)
    gap_start = SLOTS_PER_DAY * 10
    gap_len = 48  # 4 hours -> must be left as NaN
    holed = _knock_out(df, gap_start, gap_len)

    out = fill_gaps(holed, log=CleaningLog())
    filled = out.loc[gap_start : gap_start + gap_len - 1]
    assert filled["load_mw"].isna().all()
    assert (filled["impute_method"] == IMPUTE_NONE).all()
    assert not filled["imputed"].any()


def test_physically_impossible_values_flagged_and_nanned():
    from lpmf.clean.load_clean import flag_physically_impossible

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
    from lpmf.clean.load_clean import drop_duplicate_timestamps

    df = _make_regular_frame(n_days=1)
    dup_row = df.iloc[[5]]
    df_with_dupe = pd.concat([df, dup_row], ignore_index=True)
    log = CleaningLog()
    out = drop_duplicate_timestamps(df_with_dupe, log)
    assert log.duplicate_timestamps_dropped == 1
    assert not out["ts_ist"].duplicated().any()


def test_full_clean_load_no_dst_anomalies():
    df = _make_regular_frame(n_days=14)[["ts_ist", "load_mw"]]
    cleaned, log = clean_load(df)
    assert not cleaned["ts_ist"].duplicated().any()
    full_grid = pd.date_range(
        cleaned["ts_ist"].min(), cleaned["ts_ist"].max(), freq="5min", tz="Asia/Kolkata"
    )
    assert len(full_grid) == len(cleaned)


def test_clean_load_output_before_a_cutoff_ignores_readings_after_it():
    # End-to-end causality: cleaning the raw feed only up to T must give the
    # same values before T as cleaning the full feed — including the outlier
    # verdicts, which a centred window would base on readings after T.
    rng = np.random.default_rng(0)
    df = _make_regular_frame(n_days=8)[["ts_ist", "load_mw"]]
    df["load_mw"] += rng.normal(0, 15, len(df))
    cut = SLOTS_PER_DAY * 7 + 140
    df.loc[[cut - 3, cut - 1, cut + 1], "load_mw"] *= [1.12, 0.88, 1.15]

    full, _ = clean_load(df)
    partial, _ = clean_load(df.iloc[:cut].copy())
    pd.testing.assert_frame_equal(
        full.iloc[:cut][["ts_ist", "load_mw", "is_outlier", "imputed"]].reset_index(drop=True),
        partial[["ts_ist", "load_mw", "is_outlier", "imputed"]].reset_index(drop=True),
    )
    assert full.loc[[cut - 3, cut - 1], "is_outlier"].all()


def test_resample_blocks_hourly_has_block_and_impute_method():
    # Regression test: the hourly frame used to be missing `block` and
    # `impute_method` entirely, which the final schema requires for both
    # the 15-min and hourly outputs — caught running the real pipeline.
    df = _make_regular_frame(n_days=2)
    df["imputed"] = False
    df["impute_method"] = IMPUTE_NONE

    fifteen, hourly = resample_blocks(df)

    for frame in (fifteen, hourly):
        assert "block" in frame.columns
        assert "impute_method" in frame.columns
        assert frame["block"].between(1, 96).all()

    # Hourly block is the 15-min block of that hour's first slot: 1, 5, 9, ...
    assert set(hourly["block"].unique()) <= set(range(1, 97, 4))


def test_resample_blocks_reports_the_most_invasive_fill_method():
    # Regression test: every imputed block used to be labelled with the
    # time-of-day method, even when its only fill was a short one.
    df = _make_regular_frame(n_days=1)
    df["imputed"] = False
    df["impute_method"] = IMPUTE_NONE
    df.loc[1, ["imputed", "impute_method"]] = [True, IMPUTE_FFILL]  # block 1
    df.loc[3, ["imputed", "impute_method"]] = [True, IMPUTE_FFILL]  # block 2
    df.loc[4, ["imputed", "impute_method"]] = [True, IMPUTE_TOD_PROFILE]  # block 2

    fifteen, _hourly = resample_blocks(df)

    assert fifteen.loc[0, "impute_method"] == IMPUTE_FFILL
    assert fifteen.loc[1, "impute_method"] == IMPUTE_TOD_PROFILE
    assert (fifteen.loc[2:, "impute_method"] == IMPUTE_NONE).all()
    assert fifteen.loc[:1, "imputed"].all() and not fifteen.loc[2:, "imputed"].any()


def test_resample_blocks_hourly_reports_forward_fill_only_hour():
    df = _make_regular_frame(n_days=1)
    df["imputed"] = False
    df["impute_method"] = IMPUTE_NONE
    df.loc[13, ["imputed", "impute_method"]] = [True, IMPUTE_FFILL]  # hour 1 only

    _fifteen, hourly = resample_blocks(df)
    assert hourly.loc[1, "impute_method"] == IMPUTE_FFILL
    assert (hourly.drop(index=1)["impute_method"] == IMPUTE_NONE).all()


def test_resample_blocks_leaves_partially_missing_blocks_nan():
    df = _make_regular_frame(n_days=1)
    df["imputed"] = False
    df["impute_method"] = IMPUTE_NONE
    df.loc[4, "load_mw"] = np.nan  # one unfilled slot in 15-min block 2 / hour 0

    fifteen, hourly = resample_blocks(df)
    assert np.isnan(fifteen.loc[1, "load_mw"]) and np.isnan(hourly.loc[0, "load_mw"])
    assert fifteen.drop(index=1)["load_mw"].notna().all()


def test_resample_blocks_rejects_methods_from_an_older_cleaner():
    df = _make_regular_frame(n_days=1)
    df["imputed"] = False
    df["impute_method"] = IMPUTE_NONE
    df.loc[0, "impute_method"] = "linear_interpolation"

    with pytest.raises(ValueError, match="re-run"):
        resample_blocks(df)
