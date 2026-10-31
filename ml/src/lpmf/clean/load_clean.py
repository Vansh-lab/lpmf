"""Clean raw 5-minute Delhi SLDC load data into an analysis-ready frame.

This module is deliberately conservative: every correction is logged, every
imputed value is flagged (`imputed`, `impute_method`), and nothing is
fabricated across gaps longer than 3 hours — those are left as NaN and
excluded from training.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

IST = "Asia/Kolkata"
FIVE_MIN = pd.Timedelta(minutes=5)

MAX_PLAUSIBLE_LOAD_MW = 12000.0
MIN_PLAUSIBLE_LOAD_MW = 0.0  # load <= 0 is impossible
MAX_FIVE_MIN_JUMP_MW = 800.0

HAMPEL_WINDOW = 25
HAMPEL_N_SIGMA = 3.0

IMPUTE_LINEAR = "linear_interpolation"
IMPUTE_TOD_MEDIAN = "time_of_day_median_7day"
IMPUTE_NONE = "none"


@dataclass
class CleaningLog:
    duplicate_timestamps_dropped: int = 0
    missing_slots_exposed: int = 0
    physically_impossible_flagged: int = 0
    jump_violations_flagged: list[pd.Timestamp] = field(default_factory=list)
    impossible_value_timestamps: list[pd.Timestamp] = field(default_factory=list)
    outliers_flagged: int = 0
    gaps_short_linear: int = 0
    gaps_medium_tod_median: int = 0
    gaps_long_left_nan: int = 0

    def summary(self) -> dict:
        return {
            "duplicate_timestamps_dropped": self.duplicate_timestamps_dropped,
            "missing_slots_exposed": self.missing_slots_exposed,
            "physically_impossible_flagged": self.physically_impossible_flagged,
            "outliers_flagged": self.outliers_flagged,
            "gaps_short_linear": self.gaps_short_linear,
            "gaps_medium_tod_median": self.gaps_medium_tod_median,
            "gaps_long_left_nan": self.gaps_long_left_nan,
        }


def drop_duplicate_timestamps(df: pd.DataFrame, log: CleaningLog) -> pd.DataFrame:
    """Step 1: drop exact duplicate timestamps, keeping the first occurrence."""
    dup_mask = df["ts_ist"].duplicated(keep="first")
    n_dupes = int(dup_mask.sum())
    log.duplicate_timestamps_dropped = n_dupes
    if n_dupes:
        logger.info("Dropped %d exact duplicate timestamp(s).", n_dupes)
    return df.loc[~dup_mask].reset_index(drop=True)


def reindex_complete(df: pd.DataFrame, log: CleaningLog) -> pd.DataFrame:
    """Step 2: reindex onto a complete 5-minute DatetimeIndex so every
    missing slot becomes an explicit NaN row rather than simply absent."""
    full_index = pd.date_range(
        df["ts_ist"].min(), df["ts_ist"].max(), freq="5min", tz=IST, name="ts_ist"
    )
    before_rows = len(df)
    out = df.set_index("ts_ist").reindex(full_index).reset_index()
    exposed = len(out) - before_rows
    log.missing_slots_exposed = max(exposed, 0)
    logger.info("Reindexed to complete 5-min grid: %d slot(s) exposed as missing.", exposed)
    return out


def flag_physically_impossible(df: pd.DataFrame, log: CleaningLog) -> pd.DataFrame:
    """Step 3: load <= 0, load > 12000 MW, or a 5-min jump > 800 MW are
    physically impossible for the Delhi grid. Mark as NaN, keep a log of
    each flagged timestamp (do not silently delete the row)."""
    out = df.copy()
    load = out["load_mw"]

    impossible_value = (load <= MIN_PLAUSIBLE_LOAD_MW) | (load > MAX_PLAUSIBLE_LOAD_MW)
    jump = load.diff().abs()
    impossible_jump = jump > MAX_FIVE_MIN_JUMP_MW

    flagged = impossible_value | impossible_jump.fillna(False)

    log.impossible_value_timestamps = out.loc[impossible_value, "ts_ist"].tolist()
    log.jump_violations_flagged = out.loc[impossible_jump.fillna(False), "ts_ist"].tolist()
    log.physically_impossible_flagged = int(flagged.sum())

    for ts in out.loc[impossible_value, "ts_ist"]:
        logger.info("Impossible load value at %s", ts)
    for ts in out.loc[impossible_jump.fillna(False), "ts_ist"]:
        logger.info("Impossible 5-min jump (> %sMW) ending at %s", MAX_FIVE_MIN_JUMP_MW, ts)

    out.loc[flagged, "load_mw"] = np.nan
    out["is_outlier"] = flagged
    return out


def hampel_flag_outliers(df: pd.DataFrame, log: CleaningLog) -> pd.DataFrame:
    """Step 4: rolling-median Hampel filter (window=25, 3-sigma). Flags,
    does not delete — flagged points are added to `is_outlier` and their
    load is set to NaN so they are handled by the gap-filling step below."""
    out = df.copy()
    load = out["load_mw"]

    rolling_median = load.rolling(window=HAMPEL_WINDOW, center=True, min_periods=5).median()
    abs_dev = (load - rolling_median).abs()
    # 1.4826 scales the MAD to be a consistent estimator of sigma under
    # normality — the standard Hampel-filter constant.
    mad = abs_dev.rolling(window=HAMPEL_WINDOW, center=True, min_periods=5).median()
    sigma_hat = 1.4826 * mad

    with np.errstate(invalid="ignore"):
        is_hampel_outlier = abs_dev > (HAMPEL_N_SIGMA * sigma_hat)
    is_hampel_outlier = is_hampel_outlier.fillna(False) & load.notna()

    n_new = int((is_hampel_outlier & ~out["is_outlier"]).sum())
    log.outliers_flagged = int(out["is_outlier"].sum()) + n_new
    logger.info("Hampel filter flagged %d additional outlier(s).", n_new)

    out["is_outlier"] = out["is_outlier"] | is_hampel_outlier
    out.loc[is_hampel_outlier, "load_mw"] = np.nan
    return out


def _gap_lengths_minutes(na_mask: pd.Series) -> pd.Series:
    """Return, for every row, the length (in minutes) of the contiguous NaN
    run it belongs to (0 for non-NaN rows). Assumes a regular 5-min grid."""
    group = (na_mask != na_mask.shift()).cumsum()
    run_len = na_mask.groupby(group).transform("size")
    return np.where(na_mask, run_len * 5, 0)


def _time_of_day_median_fill(df: pd.DataFrame) -> pd.Series:
    """Fill using the same-time-of-day median of the 7 nearest same-weekday
    days (i.e. same HH:MM, same day-of-week, 7 closest occurrences by date
    distance)."""
    out = df["load_mw"].copy()
    ts = df["ts_ist"]
    tod = ts.dt.strftime("%H:%M")
    dow = ts.dt.day_of_week
    dates = ts.dt.date

    missing_idx = out[out.isna()].index
    for idx in missing_idx:
        same_slot = (tod == tod.loc[idx]) & (dow == dow.loc[idx]) & (out.notna())
        if not same_slot.any():
            continue
        candidate_dates = pd.Series(dates.loc[same_slot].values)
        target_date = dates.loc[idx]
        distances = candidate_dates.apply(lambda d: abs((d - target_date).days))
        nearest_idx = distances.nsmallest(7).index
        candidate_values = out.loc[same_slot].reset_index(drop=True).loc[nearest_idx]
        if len(candidate_values):
            out.loc[idx] = candidate_values.median()
    return out


def fill_gaps(df: pd.DataFrame, log: CleaningLog) -> pd.DataFrame:
    """Step 5: gap filling by contiguous-gap length.

    <= 30 min   -> linear interpolation
    30 min-3 hr -> same-time-of-day median of the 7 nearest same-weekday days
    > 3 hr      -> left as NaN, excluded from training
    """
    out = df.sort_values("ts_ist").reset_index(drop=True)
    na_mask = out["load_mw"].isna()
    gap_len_min = _gap_lengths_minutes(na_mask)

    out["imputed"] = False
    out["impute_method"] = IMPUTE_NONE

    short_mask = na_mask & (gap_len_min > 0) & (gap_len_min <= 30)
    medium_mask = na_mask & (gap_len_min > 30) & (gap_len_min <= 180)
    long_mask = na_mask & (gap_len_min > 180)

    log.gaps_short_linear = int(short_mask.sum())
    log.gaps_medium_tod_median = int(medium_mask.sum())
    log.gaps_long_left_nan = int(long_mask.sum())

    # Linear interpolation for short gaps only: interpolate on the full
    # series, then only keep the interpolated values where the gap was
    # actually short (otherwise pandas would happily interpolate long gaps
    # too, which we explicitly do not want).
    interpolated_all = out["load_mw"].interpolate(method="linear", limit_area="inside")
    out.loc[short_mask, "load_mw"] = interpolated_all.loc[short_mask]
    out.loc[short_mask, "imputed"] = True
    out.loc[short_mask, "impute_method"] = IMPUTE_LINEAR

    if medium_mask.any():
        tod_filled = _time_of_day_median_fill(out)
        out.loc[medium_mask, "load_mw"] = tod_filled.loc[medium_mask]
        out.loc[medium_mask, "imputed"] = True
        out.loc[medium_mask, "impute_method"] = IMPUTE_TOD_MEDIAN

    # long_mask rows: leave load_mw as NaN, imputed stays False.
    logger.info(
        "Gap fill: %d short (linear), %d medium (tod-median), %d long (left NaN).",
        log.gaps_short_linear,
        log.gaps_medium_tod_median,
        log.gaps_long_left_nan,
    )
    return out


def resample_blocks(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Step 6: resample 5-min -> 15-min (mean) tagged with block 1..96, and
    emit an hourly version too."""
    base = df.set_index("ts_ist")

    agg = {
        "load_mw": "mean",
        "imputed": "max",
        "is_outlier": "max",
    }
    numeric_passthrough = [c for c in base.columns if c not in agg and c != "impute_method"]
    for c in numeric_passthrough:
        if pd.api.types.is_numeric_dtype(base[c]):
            agg[c] = "mean"

    fifteen = base.resample("15min").agg(agg).reset_index()
    fifteen["block"] = (
        fifteen["ts_ist"].dt.hour * 4 + fifteen["ts_ist"].dt.minute // 15 + 1
    ).astype(int)
    fifteen["imputed"] = fifteen["imputed"].astype(bool)
    fifteen["is_outlier"] = fifteen["is_outlier"].astype(bool)
    fifteen["impute_method"] = np.where(fifteen["imputed"], IMPUTE_TOD_MEDIAN, IMPUTE_NONE)

    hourly = base.resample("1h").agg(agg).reset_index()
    hourly["imputed"] = hourly["imputed"].astype(bool)
    hourly["is_outlier"] = hourly["is_outlier"].astype(bool)

    return fifteen, hourly


def assert_no_dst_anomalies(df: pd.DataFrame) -> None:
    """Step 7: India has no DST, but assert there are no duplicate or
    missing local timestamps regardless (defensive — catches upstream data
    bugs, tz-database changes, etc.)."""
    ts = df["ts_ist"]
    n_dupes = int(ts.duplicated().sum())
    if n_dupes:
        raise AssertionError(f"Found {n_dupes} duplicate local timestamp(s) after reindexing.")

    expected = pd.date_range(ts.min(), ts.max(), freq="5min", tz=IST)
    if len(expected) != len(ts):
        raise AssertionError(
            f"Expected {len(expected)} timestamps on a complete 5-min grid, got {len(ts)}."
        )


def clean_load(raw: pd.DataFrame) -> tuple[pd.DataFrame, CleaningLog]:
    """Run the full cleaning pipeline (steps 1-5 + the DST assertion) on a
    raw frame with columns `ts_ist`, `load_mw`. Returns the cleaned 5-min
    frame plus a `CleaningLog` of everything that was done."""
    log = CleaningLog()
    out = drop_duplicate_timestamps(raw, log)
    out = reindex_complete(out, log)
    out["is_outlier"] = False
    out = flag_physically_impossible(out, log)
    out = hampel_flag_outliers(out, log)
    out = fill_gaps(out, log)
    assert_no_dst_anomalies(out)
    return out, log
