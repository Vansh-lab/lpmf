"""Shared constants, I/O paths, and metrics for the Phase-3 model ladder.

Every model script in this package reads the processed data (features.parquet,
or delhi_hourly.parquet for SARIMAX) + the pre-computed split.json boundaries
(never recomputes a split), writes its test-set predictions to
data/predictions/<model>.parquet in one shared long format, and evaluate.py
(plus the importance.py diagnostics) reads those back.

Prediction format (one row per origin/horizon pair, TEST split only):
    ts_origin      -- the timestamp features were computed as of
    horizon         -- 1..96, blocks-ahead being predicted
    ts_target       -- ts_origin + horizon * 15min (the time being predicted)
    target_block    -- 1..96, time-of-day slot of ts_target (reuses the
                        `block` convention used everywhere else in LPMF)
    actual_mw       -- ground truth load at ts_target
    predicted_mw    -- the model's forecast
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from lpmf.features.build import BLOCKS_PER_DAY, HORIZONS
from lpmf.split import SplitBoundaries, load_split_boundaries

DATA_PROCESSED = Path("data/processed")
FEATURES_PATH = DATA_PROCESSED / "features.parquet"
HOURLY_PATH = DATA_PROCESSED / "delhi_hourly.parquet"
SPLITS_PATH = DATA_PROCESSED / "splits.json"

PREDICTIONS_DIR = Path("data/predictions")
ARTIFACTS_DIR = Path("models/artifacts")
DOCS_DIR = Path("docs")

# Delhi's three-way seasonal split as used throughout this project's docs.
# Oct-Feb is grouped as "winter" (post-monsoon Delhi is already cool by
# November); documented here since the eval breakdown depends on it.
SEASON_MONTHS: dict[str, tuple[int, ...]] = {
    "summer": (3, 4, 5, 6),
    "monsoon": (7, 8, 9),
    "winter": (10, 11, 12, 1, 2),
}
MONTH_TO_SEASON: dict[int, str] = {
    m: season for season, months in SEASON_MONTHS.items() for m in months
}


def season_of(month: pd.Series | np.ndarray | int) -> pd.Series | np.ndarray | str:
    if isinstance(month, int):
        return MONTH_TO_SEASON[month]
    if isinstance(month, pd.Series):
        return month.map(MONTH_TO_SEASON)
    return np.vectorize(MONTH_TO_SEASON.get)(month)


def load_features_and_boundaries() -> tuple[pd.DataFrame, SplitBoundaries]:
    df = pd.read_parquet(FEATURES_PATH)
    boundaries = load_split_boundaries(SPLITS_PATH)
    return df, boundaries


def block_of_timestamp(ts: pd.Series) -> pd.Series:
    """1..96 time-of-day slot, matching the `block` column convention used
    across the codebase (block 1 = 00:00-00:15, ..., block 96 = 23:45-00:00)."""
    minutes_since_midnight = ts.dt.hour * 60 + ts.dt.minute
    return (minutes_since_midnight // 15 + 1).astype(int)


def mape(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.mean(np.abs((actual - predicted) / actual)) * 100.0)


def mae(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.mean(np.abs(actual - predicted)))


def rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
    return float(np.sqrt(np.mean((actual - predicted) ** 2)))


def save_predictions(name: str, predictions: pd.DataFrame) -> Path:
    # Series.values silently turns IST timestamps into naive UTC, which breaks
    # every month/weekend lookup in evaluate.py; refuse to write such a file.
    for col in ("ts_origin", "ts_target"):
        dtype = predictions[col].dtype
        if not (isinstance(dtype, pd.DatetimeTZDtype) and str(dtype.tz) == "Asia/Kolkata"):
            raise ValueError(f"{name}: {col} must be tz-aware Asia/Kolkata, got {dtype}.")
    PREDICTIONS_DIR.mkdir(parents=True, exist_ok=True)
    path = PREDICTIONS_DIR / f"{name}.parquet"
    predictions.to_parquet(path, index=False)
    return path


def load_predictions(name: str) -> pd.DataFrame:
    return pd.read_parquet(PREDICTIONS_DIR / f"{name}.parquet")


__all__ = [
    "ARTIFACTS_DIR",
    "BLOCKS_PER_DAY",
    "DOCS_DIR",
    "FEATURES_PATH",
    "HORIZONS",
    "HOURLY_PATH",
    "PREDICTIONS_DIR",
    "SPLITS_PATH",
    "block_of_timestamp",
    "load_features_and_boundaries",
    "load_predictions",
    "mae",
    "mape",
    "rmse",
    "save_predictions",
    "season_of",
]
