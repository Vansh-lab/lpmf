"""Per-consumer features from a cleaned daily kWh series. Every feature is
computed from one consumer's own row — nothing here looks across
consumers or across splits, so it is safe to compute on train, val and
test independently (unlike sgcc.clean's fill/cap values, which must come
from train only).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from lpmf.sgcc.load import SgccDataset

FEATURE_NAMES = [
    "mean_kwh",
    "std_kwh",
    "cv",
    "median_kwh",
    "iqr_kwh",
    "zero_day_frac",
    "weekly_std",
    "max_drop_frac",
    "n_drops_over_50pct",
    "trend_slope_per_rel",
]


def _max_drop_and_count(
    row: np.ndarray, window: int = 7, threshold: float = 0.5
) -> tuple[float, int]:
    """Largest day-over-day fall relative to the trailing `window`-day mean
    (a sudden, sustained drop is the classic theft signature), and how many
    days fall by more than `threshold` (e.g. 50%) that way."""
    s = pd.Series(row)
    trailing_mean = s.rolling(window, min_periods=window).mean().shift(1)
    with np.errstate(divide="ignore", invalid="ignore"):
        drop_frac = 1.0 - s / trailing_mean
    drop_frac = drop_frac.replace([np.inf, -np.inf], np.nan).dropna()
    if drop_frac.empty:
        return 0.0, 0
    return float(drop_frac.max()), int((drop_frac > threshold).sum())


def _weekly_std(row: np.ndarray, dates: pd.DatetimeIndex) -> float:
    """Std of mean consumption by day-of-week, relative to the overall
    mean — a consumer with a strong weekly rhythm has a low value here; a
    flat or erratic one has a high (or near-zero, if constant) value."""
    by_dow = pd.Series(row).groupby(dates.day_of_week.values).mean()
    mean = row.mean()
    return float(by_dow.std() / mean) if mean > 0 else 0.0


def _trend_slope(row: np.ndarray) -> float:
    """Linear-fit slope of consumption over the period, as a fraction of
    the mean per day — a sustained decline (meter tampering ramping up)
    shows up as a negative value here."""
    t = np.arange(row.shape[0], dtype=float)
    slope = np.polyfit(t, row, 1)[0]
    mean = row.mean()
    return float(slope / mean) if mean > 0 else 0.0


def build_features(data: SgccDataset) -> pd.DataFrame:
    """One row per consumer, columns = FEATURE_NAMES, index = cons_no."""
    rows = []
    for row in data.kwh:
        mean = float(row.mean())
        std = float(row.std())
        median = float(np.median(row))
        q75, q25 = np.percentile(row, [75, 25])
        zero_frac = float((row == 0).mean())
        weekly_std = _weekly_std(row, data.dates)
        max_drop, n_drops = _max_drop_and_count(row)
        trend = _trend_slope(row)
        rows.append(
            {
                "mean_kwh": mean,
                "std_kwh": std,
                "cv": std / mean if mean > 0 else 0.0,
                "median_kwh": median,
                "iqr_kwh": float(q75 - q25),
                "zero_day_frac": zero_frac,
                "weekly_std": weekly_std,
                "max_drop_frac": max_drop,
                "n_drops_over_50pct": n_drops,
                "trend_slope_per_rel": trend,
            }
        )
    return pd.DataFrame(rows, index=data.cons_no, columns=FEATURE_NAMES)
