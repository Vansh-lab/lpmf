"""Clean raw 5-minute Delhi SLDC load data into an analysis-ready frame.

This module is deliberately conservative: every correction is logged, every
imputed value is flagged (`imputed`, `impute_method`), and nothing is
fabricated across gaps longer than 3 hours — those are left as NaN and
excluded from training.

Outlier flagging and gap filling are causal: whether a reading is thrown
out, and what replaces it, depend only on readings at or before it. The same
load series feeds both the lag/rolling features and the forecast targets, so
anything two-sided leaks the future into the features — e.g. the 23:55 slot
interpolated from the next day's 00:00 reading, a week-ago lag that contains
the target's own load, or a centred outlier window whose verdict on a
reading reveals which way the load moved next.

One hindsight remains: a gap's fill method is chosen from its total length,
so a slot early in what becomes a long gap is left NaN, not forward-filled.
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

# Trailing 35-min window. A centred 25-slot window, with no floor on sigma,
# flagged 11.5% of all real readings (the MAD collapses to ~0 on smooth
# load) and decided each verdict with readings up to 2 h ahead. This setting
# flags 0.1% and only 0.5% of the slots right after a real level shift.
HAMPEL_WINDOW = 7
HAMPEL_N_SIGMA = 3.0
HAMPEL_SIGMA_FLOOR_FRAC = 0.02

IMPUTE_FFILL = "forward_fill"
IMPUTE_TOD_PROFILE = "time_of_day_profile_past_5d"
IMPUTE_NONE = "none"

# A 15-min/hourly block that mixes fill methods reports the most invasive one.
_IMPUTE_RANK = {IMPUTE_NONE: 0, IMPUTE_FFILL: 1, IMPUTE_TOD_PROFILE: 2}
_RANK_TO_IMPUTE = {rank: method for method, rank in _IMPUTE_RANK.items()}

# Backtested on held-out real 5-min readings: 3 days fits the 22:35-23:55
# gaps best but leaves a quarter unfilled, 7 days fills more but drifts with
# the season; 5 days balances the two.
PROFILE_LOOKBACK_DAYS = 5


@dataclass
class CleaningLog:
    duplicate_timestamps_dropped: int = 0
    missing_slots_exposed: int = 0
    physically_impossible_flagged: int = 0
    jump_violations_flagged: list[pd.Timestamp] = field(default_factory=list)
    impossible_value_timestamps: list[pd.Timestamp] = field(default_factory=list)
    outliers_flagged: int = 0
    gaps_short_ffill: int = 0
    gaps_short_left_nan: int = 0
    gaps_medium_profile: int = 0
    gaps_medium_left_nan: int = 0
    gaps_long_left_nan: int = 0

    def summary(self) -> dict:
        return {
            "duplicate_timestamps_dropped": self.duplicate_timestamps_dropped,
            "missing_slots_exposed": self.missing_slots_exposed,
            "physically_impossible_flagged": self.physically_impossible_flagged,
            "outliers_flagged": self.outliers_flagged,
            "gaps_short_ffill": self.gaps_short_ffill,
            "gaps_short_left_nan": self.gaps_short_left_nan,
            "gaps_medium_profile": self.gaps_medium_profile,
            "gaps_medium_left_nan": self.gaps_medium_left_nan,
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
    """Step 4: trailing rolling-median Hampel filter (3-sigma, sigma floored
    at 2% of the rolling median). Flags, does not delete — flagged points are
    added to `is_outlier` and their load is set to NaN so they are handled by
    the gap-filling step below."""
    out = df.copy()
    load = out["load_mw"]

    rolling_median = load.rolling(window=HAMPEL_WINDOW, min_periods=5).median()
    abs_dev = (load - rolling_median).abs()
    # 1.4826 scales the MAD to be a consistent estimator of sigma under
    # normality — the standard Hampel-filter constant.
    mad = abs_dev.rolling(window=HAMPEL_WINDOW, min_periods=5).median()
    sigma_hat = np.maximum(1.4826 * mad, HAMPEL_SIGMA_FLOOR_FRAC * rolling_median)

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


def _time_of_day_profile_fill(observed: pd.Series, ts: pd.Series) -> np.ndarray:
    """Causal fill value for every row. For each of the previous
    PROFILE_LOOKBACK_DAYS days, scale that day's reading at this slot by the
    ratio of the last observed reading at or before the row (the anchor) to
    that same day's reading at the anchor's slot; take the median over the
    days where both readings were observed. Slot and anchor always come from
    the same day, so a day missing one of them cannot skew the ratio. Uses
    observed readings only (never other fills); NaN without history/anchor."""
    obs = observed.to_numpy()
    by_ts = pd.Series(obs, index=pd.DatetimeIndex(ts))

    positions = np.arange(len(obs), dtype=float)
    anchor_pos = pd.Series(np.where(np.isnan(obs), np.nan, positions)).ffill().to_numpy()
    has_anchor = ~np.isnan(anchor_pos)
    anchor_idx = np.where(has_anchor, anchor_pos, 0).astype(int)
    anchor_obs = np.where(has_anchor, obs[anchor_idx], np.nan)
    anchor_ts = ts.take(anchor_idx).reset_index(drop=True)

    estimates = []
    for k in range(1, PROFILE_LOOKBACK_DAYS + 1):
        lag = pd.Timedelta(days=k)
        slot_k = by_ts.reindex(ts - lag).to_numpy()
        anchor_k = by_ts.reindex(anchor_ts - lag).to_numpy()
        with np.errstate(divide="ignore", invalid="ignore"):
            estimates.append(np.where(anchor_k > 0, anchor_obs * slot_k / anchor_k, np.nan))
    return pd.DataFrame(np.column_stack(estimates)).median(axis=1).to_numpy()


def fill_gaps(df: pd.DataFrame, log: CleaningLog) -> pd.DataFrame:
    """Step 5: causal gap filling by contiguous-gap length (see the module
    docstring for why every fill looks backwards only).

    <= 30 min   -> forward fill from the last observed reading
    30 min-3 hr -> same-slot median profile of the previous 5 days, scaled
                   to the last observed reading before the gap; left NaN
                   when that history or anchor is missing
    > 3 hr      -> left as NaN, excluded from training
    """
    out = df.sort_values("ts_ist").reset_index(drop=True)
    observed = out["load_mw"].copy()
    na_mask = observed.isna()
    gap_len_min = _gap_lengths_minutes(na_mask)

    out["imputed"] = False
    out["impute_method"] = IMPUTE_NONE

    short_mask = na_mask & (gap_len_min > 0) & (gap_len_min <= 30)
    medium_mask = na_mask & (gap_len_min > 30) & (gap_len_min <= 180)
    long_mask = na_mask & (gap_len_min > 180)

    forward_filled = observed.ffill()
    short_fill = short_mask & forward_filled.notna()
    out.loc[short_fill, "load_mw"] = forward_filled.loc[short_fill]
    out.loc[short_fill, "imputed"] = True
    out.loc[short_fill, "impute_method"] = IMPUTE_FFILL

    profile_filled = pd.Series(_time_of_day_profile_fill(observed, out["ts_ist"]), index=out.index)
    medium_fill = medium_mask & np.isfinite(profile_filled)
    out.loc[medium_fill, "load_mw"] = profile_filled.loc[medium_fill]
    out.loc[medium_fill, "imputed"] = True
    out.loc[medium_fill, "impute_method"] = IMPUTE_TOD_PROFILE

    log.gaps_short_ffill = int(short_fill.sum())
    log.gaps_short_left_nan = int((short_mask & ~short_fill).sum())
    log.gaps_medium_profile = int(medium_fill.sum())
    log.gaps_medium_left_nan = int((medium_mask & ~medium_fill).sum())
    log.gaps_long_left_nan = int(long_mask.sum())
    logger.info(
        "Gap fill: %d short (forward fill), %d short left NaN (no prior reading), "
        "%d medium (past-5-day profile), %d medium left NaN (no history), %d long (left NaN).",
        log.gaps_short_ffill,
        log.gaps_short_left_nan,
        log.gaps_medium_profile,
        log.gaps_medium_left_nan,
        log.gaps_long_left_nan,
    )
    return out


def resample_blocks(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Step 6: resample 5-min -> 15-min (mean) tagged with block 1..96, and
    emit an hourly version too. A block with any still-missing 5-min slot is
    left NaN rather than averaged from the slots that happen to remain."""
    unknown = set(df["impute_method"].unique()) - set(_IMPUTE_RANK)
    if unknown:
        raise ValueError(
            f"Unknown impute_method value(s) {sorted(unknown)}: the 5-min file was written by an "
            "older cleaner; re-run `python -m lpmf.pipeline --step clean` first."
        )
    base = df.set_index("ts_ist")
    base["_impute_rank"] = base["impute_method"].map(_IMPUTE_RANK)
    base["_n_missing"] = base["load_mw"].isna().astype(int)

    agg = {
        "load_mw": "mean",
        "imputed": "max",
        "is_outlier": "max",
        "_impute_rank": "max",
        "_n_missing": "sum",
    }
    numeric_passthrough = [c for c in base.columns if c not in agg and c != "impute_method"]
    for c in numeric_passthrough:
        if pd.api.types.is_numeric_dtype(base[c]):
            agg[c] = "mean"

    fifteen = base.resample("15min").agg(agg).reset_index()
    fifteen.loc[fifteen.pop("_n_missing") > 0, "load_mw"] = np.nan
    fifteen["block"] = (
        fifteen["ts_ist"].dt.hour * 4 + fifteen["ts_ist"].dt.minute // 15 + 1
    ).astype(int)
    fifteen["imputed"] = fifteen["imputed"].astype(bool)
    fifteen["is_outlier"] = fifteen["is_outlier"].astype(bool)
    fifteen["impute_method"] = fifteen.pop("_impute_rank").astype(int).map(_RANK_TO_IMPUTE)

    hourly = base.resample("1h").agg(agg).reset_index()
    hourly.loc[hourly.pop("_n_missing") > 0, "load_mw"] = np.nan
    hourly["imputed"] = hourly["imputed"].astype(bool)
    hourly["is_outlier"] = hourly["is_outlier"].astype(bool)
    # `block` (1-96) is a 15-min-grid concept; for the hourly frame we tag
    # each row with the block number of that hour's first 15-min slot, so
    # it stays within the same 1-96 numbering and the final schema (which
    # both frames share) doesn't need an hourly-specific field.
    hourly["block"] = (hourly["ts_ist"].dt.hour * 4 + 1).astype(int)
    hourly["impute_method"] = hourly.pop("_impute_rank").astype(int).map(_RANK_TO_IMPUTE)

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
