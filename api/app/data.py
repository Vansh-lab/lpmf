"""Read-only access to the ML pipeline's outputs.

Each file is read once per process and kept in memory: the outputs only change
when the pipeline is re-run, so restart the API after a rebuild.
"""

from __future__ import annotations

import json
from datetime import date
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from app.config import settings

ROOT = settings.repo_root
FIFTEEN_MIN = ROOT / "data" / "processed" / "delhi_15min.parquet"
BANDS = ROOT / "models" / "artifacts" / "conformal_bands.parquet"
CONFORMAL_SUMMARY = ROOT / "models" / "artifacts" / "conformal_summary.json"
SHAP_DIR = ROOT / "models" / "artifacts" / "shap_examples"

BLOCKS_PER_DAY = 96

SOURCE_SLDC = "Delhi SLDC 15-min load (cleaned) + Open-Meteo heat index"
SOURCE_FORECAST = "LightGBM day-ahead forecast, Delhi SLDC test-period backtest"


class DataNotBuilt(RuntimeError):
    """A pipeline output the endpoint needs has not been built yet."""


def _require(path: Path) -> Path:
    if not path.exists():
        shown = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
        raise DataNotBuilt(
            f"{shown} is missing; run the ML pipeline (see README, section 4) to build it."
        )
    return path


@lru_cache(maxsize=1)
def fifteen_min() -> pd.DataFrame:
    """Real Delhi SLDC load joined with weather, one row per 15-min block."""
    return pd.read_parquet(
        _require(FIFTEEN_MIN),
        columns=["ts_ist", "date", "load_mw", "heat_index_c", "ghi_wm2"],
    )


@lru_cache(maxsize=1)
def day_ahead_forecasts() -> pd.DataFrame:
    """The day-ahead forecast for every complete test day: issued at 23:45
    the evening before, horizons 1..96 = the 96 blocks of the day, with the
    primary (absolute-score) split-conformal P10-P90 band."""
    bands = pd.read_parquet(
        _require(BANDS),
        columns=[
            "ts_origin",
            "horizon",
            "ts_target",
            "actual_mw",
            "predicted_mw",
            "lower_mw",
            "upper_mw",
        ],
    )
    origin = bands["ts_origin"]
    bands = bands[(origin.dt.hour == 23) & (origin.dt.minute == 45)].copy()
    bands["date"] = (bands["ts_origin"] + pd.Timedelta(minutes=15)).dt.date
    complete = bands.groupby("date")["horizon"].transform("size") == BLOCKS_PER_DAY
    return bands[complete].sort_values(["date", "horizon"]).reset_index(drop=True)


@lru_cache(maxsize=1)
def forecast_dates() -> list[date]:
    return sorted(day_ahead_forecasts()["date"].unique())


def forecast_day(day: date | None) -> pd.DataFrame | None:
    """The 96 rows of `day`'s day-ahead forecast (the latest day if None),
    or None when that day is not in the test set."""
    day = day or forecast_dates()[-1]
    rows = day_ahead_forecasts()
    rows = rows[rows["date"] == day]
    return rows if len(rows) == BLOCKS_PER_DAY else None


@lru_cache(maxsize=1)
def conformal_summary() -> dict:
    return json.loads(_require(CONFORMAL_SUMMARY).read_text())


@lru_cache(maxsize=1)
def shap_days() -> dict[date, str]:
    """Days with a precomputed TreeSHAP explanation, date -> label."""
    index = SHAP_DIR / "index.json"
    if not index.exists():
        return {}
    days = json.loads(index.read_text())["days"]
    return {date.fromisoformat(info["date"]): label for label, info in days.items()}


@lru_cache(maxsize=8)
def shap_matrix(label: str) -> pd.DataFrame:
    return pd.read_parquet(_require(SHAP_DIR / f"{label}_shap.parquet"))


def ldc_points(load_mw: list[float], n_points: int) -> list[tuple[float, float]]:
    """Downsample a load-duration curve (loads sorted descending) to
    `n_points` evenly spaced % of time; point p is the load exceeded p% of
    the time (0% = the peak, 100% = the minimum)."""
    loads = np.asarray(load_mw)
    pct = np.linspace(0.0, 100.0, n_points)
    idx = np.clip(np.ceil(pct / 100.0 * loads.size).astype(int) - 1, 0, loads.size - 1)
    return list(zip(pct.tolist(), loads[idx].tolist()))
