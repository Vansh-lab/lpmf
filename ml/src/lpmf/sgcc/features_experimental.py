"""Two additional per-consumer features tried in the honest val-only
improvement experiment (see `lpmf.sgcc.improvement_experiment`). Kept
separate from the locked `features.py` so the production feature set is
never touched unless the experiment actually earns a place for them (val
PR-AUC improvement) -- same discipline as the main forecast model's
`holiday_tier_experiment.py`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from lpmf.sgcc.load import SgccDataset

ADDITIONAL_FEATURE_NAMES = ["weekly_pattern_break", "recent_volatility_ratio"]


def _weekly_pattern_break(row: np.ndarray, dates: pd.DatetimeIndex) -> float:
    """1 - correlation between the first-half and second-half day-of-week
    consumption profile. A consumer whose weekly rhythm changes partway
    through the period (a pattern break, not just a level shift) scores
    high here; existing features only look at the whole-period weekly
    pattern or the overall level/trend, not whether the *shape* changes."""
    n = row.shape[0]
    split = n // 2
    dow = dates.day_of_week.values
    first = pd.Series(row[:split]).groupby(dow[:split]).mean()
    second = pd.Series(row[split:]).groupby(dow[split:]).mean()
    common = first.index.intersection(second.index)
    if len(common) < 2:
        return 0.0
    with np.errstate(invalid="ignore"):
        corr = np.corrcoef(first.loc[common], second.loc[common])[0, 1]
    if np.isnan(corr):
        return 0.0
    return float(1.0 - corr)


def _recent_volatility_ratio(row: np.ndarray, recent_frac: float = 0.3) -> float:
    """std of the most recent `recent_frac` of days, relative to std of the
    earlier days -- a consumer who becomes much more erratic later in the
    period (e.g. after tampering begins) scores > 1 here. `cv` (in the
    locked features) is a single whole-period ratio and can't see this
    kind of change over time."""
    n = row.shape[0]
    k = max(1, int(round(n * recent_frac)))
    if k >= n:
        return 1.0
    recent, earlier = row[-k:], row[:-k]
    earlier_std = float(earlier.std())
    if earlier_std <= 0:
        return 0.0
    return float(recent.std() / earlier_std)


def build_additional_features(data: SgccDataset) -> pd.DataFrame:
    """One row per consumer, columns = ADDITIONAL_FEATURE_NAMES, index =
    cons_no -- concatenate with the locked `features.build_features()`
    output to get the extended feature set tried in the experiment."""
    rows = [
        {
            "weekly_pattern_break": _weekly_pattern_break(row, data.dates),
            "recent_volatility_ratio": _recent_volatility_ratio(row),
        }
        for row in data.kwh
    ]
    return pd.DataFrame(rows, index=data.cons_no, columns=ADDITIONAL_FEATURE_NAMES)
