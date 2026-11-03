"""Seasonal-naive baseline: predicted load at block t = same time-of-day
block, N days ago. Two variants, both reported — neither is "the" model,
they're the floor every other model must beat.

    daily:  predicted(t) = load(t - 1 day)
    weekly: predicted(t) = load(t - 7 days)

This needs no training: for every origin row in the TEST split and every
horizon h in 1..96, the prediction for ts_target = ts_origin + h*15min is
just the real load at ts_target - 1 day (or - 7 days), read directly off
the full (train+val+test) series — using the actual historical load at an
already-past timestamp relative to ts_target is not leakage (it never
reads anything at or after ts_target), same as any lag feature in
features.parquet.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from lpmf.models.common import HORIZONS, block_of_timestamp, save_predictions

logger = logging.getLogger(__name__)


def _predict_variant(df: pd.DataFrame, test_mask: pd.Series, offset_days: int) -> pd.DataFrame:
    load_by_ts = df.set_index("ts_ist")["load_mw"]
    test_origins = df.loc[test_mask, "ts_ist"].reset_index(drop=True)

    rows = []
    offset = pd.Timedelta(days=offset_days)
    for h in HORIZONS:
        ts_target = test_origins + pd.Timedelta(minutes=15 * h)
        ts_lookup = ts_target - offset
        predicted = ts_lookup.map(load_by_ts)
        actual = ts_target.map(load_by_ts)
        rows.append(
            pd.DataFrame(
                {
                    "ts_origin": test_origins,
                    "horizon": h,
                    # .array, not .values: .values drops the IST tz and
                    # silently converts to naive UTC (5h30m off).
                    "ts_target": ts_target.array,
                    "target_block": block_of_timestamp(ts_target).values,
                    "actual_mw": actual.values,
                    "predicted_mw": predicted.values,
                }
            )
        )
    out = pd.concat(rows, ignore_index=True)
    out = out.dropna(subset=["actual_mw", "predicted_mw"])
    return out


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    from lpmf.models.common import load_features_and_boundaries

    df, _ = load_features_and_boundaries()
    test_mask = df["split"] == "test"

    daily = _predict_variant(df, test_mask, offset_days=1)
    weekly = _predict_variant(df, test_mask, offset_days=7)

    path_daily = save_predictions("seasonal_naive_daily", daily)
    path_weekly = save_predictions("seasonal_naive_weekly", weekly)

    for name, preds in [("daily", daily), ("weekly", weekly)]:
        err = np.abs(preds["actual_mw"] - preds["predicted_mw"])
        logger.info(
            "seasonal_naive_%s: %d predictions, MAE=%.1f MW, MAPE=%.2f%%",
            name,
            len(preds),
            err.mean(),
            float(np.mean(err / preds["actual_mw"]) * 100),
        )
    logger.info("Wrote %s and %s", path_daily, path_weekly)


if __name__ == "__main__":
    main()
