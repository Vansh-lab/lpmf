"""Causal cleaning for SGCC: every fill value and every outlier cap is
fitted on the TRAIN split only, then applied unchanged to train, val and
test. No statistic here is ever computed from val or test rows — that is
what "causal" means in this cross-sectional (not time-series) setting:
not leaking the held-out split into the numbers used to clean the data.

    for each calendar day d:
        median_d = median of non-missing, non-negative TRAIN readings on day d
        cap_d    = p99 of non-missing, non-negative TRAIN readings on day d
    apply median_d (fill) and cap_d (clip) to every split, column by column
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np

from lpmf.sgcc.load import SgccDataset

OUTLIER_PERCENTILE = 99.0


@dataclass(frozen=True)
class CleaningStats:
    """Fitted on train only; `apply` uses these on any split."""

    fill_value: np.ndarray  # (d,) per-day median, train only
    cap_value: np.ndarray  # (d,) per-day p99, train only


def fit_cleaning(train: SgccDataset) -> CleaningStats:
    kwh = train.kwh.copy()
    kwh[kwh < 0] = np.nan  # negative readings are not physically meaningful here either
    # A day with every train reading missing can't give that day its own
    # fill/cap (nanmedian/nanpercentile warn and return NaN); the fallback
    # below replaces those NaNs, so the warning is expected, not a bug.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        fill = np.nanmedian(kwh, axis=0)
        cap = np.nanpercentile(kwh, OUTLIER_PERCENTILE, axis=0)
    global_fill = float(np.nanmedian(kwh))
    global_cap = float(np.nanpercentile(kwh, OUTLIER_PERCENTILE))
    fill = np.where(np.isnan(fill), global_fill, fill)
    cap = np.where(np.isnan(cap), global_cap, cap)
    return CleaningStats(fill_value=fill, cap_value=cap)


def apply_cleaning(data: SgccDataset, stats: CleaningStats) -> SgccDataset:
    """Fill missing/negative readings with the train median for that day,
    then cap at the train p99 for that day. Column order must match what
    `stats` was fitted on (both come from the same chronologically-sorted
    `dates`)."""
    if data.kwh.shape[1] != stats.fill_value.shape[0]:
        raise ValueError(
            f"column count {data.kwh.shape[1]} does not match the fitted stats "
            f"({stats.fill_value.shape[0]}); clean with the same date columns used to fit."
        )
    kwh = data.kwh.copy()
    missing = np.isnan(kwh) | (kwh < 0)
    fill_grid = np.broadcast_to(stats.fill_value, kwh.shape)
    kwh = np.where(missing, fill_grid, kwh)
    cap_grid = np.broadcast_to(stats.cap_value, kwh.shape)
    kwh = np.minimum(kwh, cap_grid)
    return SgccDataset(cons_no=data.cons_no, flag=data.flag, dates=data.dates, kwh=kwh)
