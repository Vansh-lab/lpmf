"""Feature engineering for the LPMF forecasting target.

Builds, from the cleaned real SLDC+weather+calendar frame
(data/processed/delhi_15min.parquet), everything a multi-horizon
next-day forecaster needs: lag features, rolling stats, night
temperature, cyclical calendar encodings, an IPL event flag, and the
96-block-ahead multi-horizon target.

Output: data/processed/features.parquet

Design decisions worth knowing about (see also the module docstring in
lpmf.pipeline and the Phase-2 summary this was built for):

- Lag/rolling features are computed on the full, continuous time series
  with plain backward-looking shift()/rolling() — never a centred or
  forward window. By construction a feature for row t can only depend on
  rows <= t, so it can never leak future information into that row,
  regardless of which split t happens to fall in. A val/test row's lag
  feature legitimately reaching back into train-period history is not
  leakage — it is real, already-available history, exactly as it would
  be at deployment time.
- The *targets* (load_mw at t+1..t+96) are the one place leakage across
  a split boundary is real: a horizon-h target for a row near the end of
  a split literally points at a timestamp a different split owns. Those
  target cells are set to NaN rather than filled with the true (but
  wrong-split) future value — see `_null_targets_crossing_split`.
- Lag/rolling features are NaN for the first ~1 week of the series
  (nothing to look back on yet) and never backfilled/fabricated; this is
  reported, not hidden (see the pipeline step's log output).
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd
import pandera.pandas as pa

from lpmf.split import SplitBoundaries, load_split_boundaries

logger = logging.getLogger(__name__)

BLOCKS_PER_DAY = 96
IPL_SEASONS_CSV = Path(__file__).parent / "data" / "ipl_seasons.csv"

# Multi-horizon target: next-day, all 96 blocks ahead.
HORIZONS = list(range(1, BLOCKS_PER_DAY + 1))


def _add_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    load = out["load_mw"]

    out["load_lag_1block"] = load.shift(1)
    out["load_lag_1day"] = load.shift(BLOCKS_PER_DAY)
    out["load_lag_1week"] = load.shift(BLOCKS_PER_DAY * 7)

    # Same block-of-day, trailing 4 weeks (1,2,3,4 weeks back), averaged —
    # a smoothed generalisation of the 1-week lag.
    trailing_weeks = [load.shift(BLOCKS_PER_DAY * 7 * k) for k in (1, 2, 3, 4)]
    out["load_avg_same_block_trailing_4w"] = pd.concat(trailing_weeks, axis=1).mean(axis=1)

    return out


def _add_rolling_features(df: pd.DataFrame, window: int = BLOCKS_PER_DAY) -> pd.DataFrame:
    out = df.copy()
    min_periods = window // 2
    out["load_roll_mean_24h"] = out["load_mw"].rolling(window, min_periods=min_periods).mean()
    out["load_roll_std_24h"] = out["load_mw"].rolling(window, min_periods=min_periods).std()
    out["temp_roll_mean_24h"] = out["temp_c"].rolling(window, min_periods=min_periods).mean()
    return out


def _add_night_temp(df: pd.DataFrame) -> pd.DataFrame:
    """Mean temp_c over that calendar day's 00:00-05:00 blocks, broadcast
    to every row of that day.

    Note: for a row that itself falls inside 00:00-05:00, this technically
    includes a few blocks later that same night (i.e. slightly ahead of
    that row's own timestamp) — a known, narrow leakage window limited to
    the first 20 blocks of each day, kept because the spec asks for
    exactly this definition (whole-night mean broadcast across the day).
    """
    out = df.copy()
    is_night = out["ts_ist"].dt.hour < 5
    night_means = out.loc[is_night].groupby("date")["temp_c"].mean()
    out["night_temp_c"] = out["date"].map(night_means)
    return out


def _add_cyclical_encodings(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    hour_frac = out["ts_ist"].dt.hour + out["ts_ist"].dt.minute / 60.0
    doy = out["ts_ist"].dt.day_of_year

    out["sin_hour"] = np.sin(2 * np.pi * hour_frac / 24.0)
    out["cos_hour"] = np.cos(2 * np.pi * hour_frac / 24.0)
    out["sin_dow"] = np.sin(2 * np.pi * out["dow"] / 7.0)
    out["cos_dow"] = np.cos(2 * np.pi * out["dow"] / 7.0)
    out["sin_doy"] = np.sin(2 * np.pi * doy / 365.25)
    out["cos_doy"] = np.cos(2 * np.pi * doy / 365.25)
    return out


def _load_ipl_seasons() -> pd.DataFrame:
    seasons = pd.read_csv(IPL_SEASONS_CSV, comment="#")
    seasons["start_date"] = pd.to_datetime(seasons["start_date"]).dt.date
    seasons["end_date"] = pd.to_datetime(seasons["end_date"]).dt.date
    return seasons


def _add_ipl_flag(df: pd.DataFrame) -> pd.DataFrame:
    """`is_ipl_season`: True for any day inside a known IPL tournament
    window (see data/ipl_seasons.csv — season-level windows, not verified
    per-match dates; documented there)."""
    out = df.copy()
    seasons = _load_ipl_seasons()

    dates = out["date"]
    flag = pd.Series(False, index=out.index)
    for _, row in seasons.iterrows():
        flag |= (dates >= row["start_date"]) & (dates <= row["end_date"])
    out["is_ipl_season"] = flag
    return out


def _confirm_festival_overlap(df: pd.DataFrame) -> None:
    """Diwali and Holi are already produced by the `holidays` package
    (is_holiday/holiday_name). This just logs that overlap rather than
    adding duplicate flag columns, per the brief."""
    names = df.loc[df["is_holiday"], "holiday_name"].dropna().unique()
    has_diwali = any("diwali" in str(n).lower() for n in names)
    has_holi = any(str(n).lower() == "holi" for n in names)
    logger.info(
        "Festival overlap check: Diwali in holiday_name=%s, Holi in holiday_name=%s "
        "(both from the `holidays` package already; no duplicate flags added).",
        has_diwali,
        has_holi,
    )


def _add_targets(df: pd.DataFrame) -> pd.DataFrame:
    load = df["load_mw"]
    targets = pd.concat(
        {f"target_h{h:02d}": load.shift(-h) for h in HORIZONS},
        axis=1,
    )
    return pd.concat([df, targets], axis=1)


def _row_split(ts: pd.Series, boundaries: SplitBoundaries) -> pd.Series:
    train_start, train_end = pd.Timestamp(boundaries.train_start), pd.Timestamp(
        boundaries.train_end
    )
    val_start, val_end = pd.Timestamp(boundaries.val_start), pd.Timestamp(boundaries.val_end)
    test_start, test_end = pd.Timestamp(boundaries.test_start), pd.Timestamp(boundaries.test_end)

    split = pd.Series(pd.NA, index=ts.index, dtype="object")
    split = split.mask((ts >= train_start) & (ts <= train_end), "train")
    split = split.mask((ts >= val_start) & (ts <= val_end), "val")
    split = split.mask((ts >= test_start) & (ts <= test_end), "test")
    return split


def _null_targets_crossing_split(df: pd.DataFrame, boundaries: SplitBoundaries) -> pd.DataFrame:
    """Set target_h{h} to NaN wherever its target timestamp (t + h blocks)
    falls in a different split than row t itself — see module docstring.
    """
    out = df.copy()
    row_split = _row_split(out["ts_ist"], boundaries)
    out["split"] = row_split

    n_nulled = 0
    for h in HORIZONS:
        target_ts = out["ts_ist"] + pd.Timedelta(minutes=15 * h)
        target_split = _row_split(target_ts, boundaries)
        crosses = (row_split != target_split) | target_split.isna() | row_split.isna()
        col = f"target_h{h:02d}"
        n_nulled += int((crosses & out[col].notna()).sum())
        out.loc[crosses, col] = np.nan

    logger.info(
        "Nulled %d target cells (out of %d rows x %d horizons) that would have crossed a "
        "split boundary.",
        n_nulled,
        len(out),
        len(HORIZONS),
    )
    return out


FeatureSchema = pa.DataFrameSchema(
    {
        "ts_ist": pa.Column(nullable=False),
        "load_mw": pa.Column(float, nullable=True),
        "load_lag_1block": pa.Column(float, nullable=True),
        "load_lag_1day": pa.Column(float, nullable=True),
        "load_lag_1week": pa.Column(float, nullable=True),
        "load_avg_same_block_trailing_4w": pa.Column(float, nullable=True),
        "load_roll_mean_24h": pa.Column(float, nullable=True),
        "load_roll_std_24h": pa.Column(float, nullable=True),
        "temp_roll_mean_24h": pa.Column(float, nullable=True),
        "night_temp_c": pa.Column(float, nullable=True),
        "heat_index_c": pa.Column(float, nullable=True),
        "sin_hour": pa.Column(float, checks=pa.Check.in_range(-1.0001, 1.0001)),
        "cos_hour": pa.Column(float, checks=pa.Check.in_range(-1.0001, 1.0001)),
        "sin_dow": pa.Column(float, checks=pa.Check.in_range(-1.0001, 1.0001)),
        "cos_dow": pa.Column(float, checks=pa.Check.in_range(-1.0001, 1.0001)),
        "sin_doy": pa.Column(float, checks=pa.Check.in_range(-1.0001, 1.0001)),
        "cos_doy": pa.Column(float, checks=pa.Check.in_range(-1.0001, 1.0001)),
        "is_ipl_season": pa.Column(bool),
        "is_holiday": pa.Column(bool),
        "is_weekend": pa.Column(bool),
        "split": pa.Column(str, nullable=True),
        "data_source": pa.Column(str, nullable=False),
        "is_synthetic": pa.Column(bool, nullable=False),
    },
    strict=False,  # the 96 target_h.. columns and passthrough columns ride along unchecked
    coerce=False,
)


def build_features(
    df_15min: pd.DataFrame,
    boundaries: SplitBoundaries,
) -> pd.DataFrame:
    df = df_15min.sort_values("ts_ist").reset_index(drop=True)

    df = _add_lag_features(df)
    df = _add_rolling_features(df)
    df = _add_night_temp(df)
    df = _add_cyclical_encodings(df)
    df = _add_ipl_flag(df)
    _confirm_festival_overlap(df)
    df = _add_targets(df)
    df = _null_targets_crossing_split(df, boundaries)

    FeatureSchema.validate(df)
    return df


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    df_15min = pd.read_parquet("data/processed/delhi_15min.parquet")
    boundaries = load_split_boundaries("data/processed/splits.json")
    features = build_features(df_15min, boundaries)
    out_path = Path("data/processed/features.parquet")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    features.to_parquet(out_path, index=False)
    logger.info("Wrote %d rows x %d cols to %s", len(features), features.shape[1], out_path)


if __name__ == "__main__":
    main()
