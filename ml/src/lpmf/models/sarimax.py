"""SARIMAX classical benchmark, fit on the HOURLY-aggregated series (15-min
is too slow for repeated MLE fits/forecasts at this data size).

Two different forecast protocols are used on purpose, for two different
jobs:

  - Order selection (on val): one static multi-step forecast per candidate
    order (fit once on train, forecast the whole val window in one shot,
    no peeking at val's actual values along the way). Cheap, so we can
    afford a real grid search; a fair, if conservative, way to rank orders
    against each other.
  - Final test reporting: a realistic rolling day-ahead scheme for the one
    chosen order — fit once on train+val, then walk day by day through
    test: forecast the next 24h, record it, then feed that day's real
    values back in with refit=False (a cheap Kalman-filter state update,
    not a re-optimization) before forecasting the next day. This is what
    "day-ahead SARIMAX" means operationally and is worth the extra compute
    for the one model that actually gets reported.

Predictions are broadcast from hourly to the shared 15-min (ts_origin,
horizon, ts_target) grid so evaluate.py can compare this model to the
others on identical footing — each hourly forecast value is repeated
across its 4 contained 15-min blocks. That's a real approximation
(SARIMAX never actually resolves sub-hourly structure) and is called out
in MODEL_RESULTS.md, not hidden.
"""

from __future__ import annotations

import itertools
import json
import logging

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX

from lpmf.models.common import (
    ARTIFACTS_DIR,
    HOURLY_PATH,
    block_of_timestamp,
    mape,
    save_predictions,
)
from lpmf.split import load_split_boundaries

logger = logging.getLogger(__name__)

SEASONAL_PERIOD = 24  # daily seasonality on hourly data

# Small, deliberately coarse grid — D=1 (seasonal differencing handles the
# daily cycle) and d=0 fixed, to keep the search in a handful of fits.
ORDER_GRID = [
    {"order": (p, 0, q), "seasonal_order": (P, 1, Q, SEASONAL_PERIOD)}
    for p, q, P, Q in itertools.product([1, 2], [1, 2], [0, 1], [1])
]


def _load_hourly_splits() -> tuple[pd.Series, pd.Series, pd.Series]:
    # Missing hours stay NaN: the Kalman filter treats them as missing
    # observations, while interpolating would feed the next day's readings
    # into the state used to forecast that day.
    df = pd.read_parquet(HOURLY_PATH).sort_values("ts_ist").reset_index(drop=True)
    boundaries = load_split_boundaries("data/processed/splits.json")
    ts = df["ts_ist"]
    series = df.set_index("ts_ist")["load_mw"]
    train = series.loc[(ts >= boundaries.train_start).values & (ts <= boundaries.train_end).values]
    val = series.loc[(ts >= boundaries.val_start).values & (ts <= boundaries.val_end).values]
    test = series.loc[(ts >= boundaries.test_start).values & (ts <= boundaries.test_end).values]
    return train, val, test


# Bump whenever the hourly data changes, like the LightGBM Optuna study name:
# checkpointed val MAPEs from different data must not be reused.
CHECKPOINT_PATH = ARTIFACTS_DIR / "sarimax_order_search_checkpoint_v2.jsonl"


def _spec_key(spec: dict) -> str:
    return f"{spec['order']}|{spec['seasonal_order']}"


def _load_checkpoint() -> dict[str, dict]:
    if not CHECKPOINT_PATH.exists():
        return {}
    done = {}
    for line in CHECKPOINT_PATH.read_text().splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if "error" in record:  # a failed fit (e.g. OOM) is retried, not skipped forever
            continue
        record["order"] = tuple(record["order"])
        record["seasonal_order"] = tuple(record["seasonal_order"])
        done[_spec_key(record)] = record
    return done


def _append_checkpoint(record: dict) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(CHECKPOINT_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")
        f.flush()


def _select_order(train: pd.Series, val: pd.Series) -> dict:
    done = _load_checkpoint()
    if done:
        logger.info(
            "Resuming order search: %d/%d orders already checkpointed at %s",
            len(done),
            len(ORDER_GRID),
            CHECKPOINT_PATH,
        )

    results = list(done.values())
    for spec in ORDER_GRID:
        key = _spec_key(spec)
        if key in done:
            logger.info(
                "order=%s seasonal_order=%s -> SKIPPED (already checkpointed, val MAPE=%.2f%%)",
                spec["order"],
                spec["seasonal_order"],
                done[key]["val_mape"],
            )
            continue
        try:
            model = SARIMAX(
                train.to_numpy(),
                order=spec["order"],
                seasonal_order=spec["seasonal_order"],
                enforce_stationarity=False,
                enforce_invertibility=False,
            )
            fit = model.fit(disp=False, maxiter=50)
            forecast = fit.forecast(steps=len(val))
            observed = val.notna().to_numpy()
            val_mape = mape(val.to_numpy()[observed], forecast[observed])
            record = {**spec, "val_mape": val_mape, "aic": float(fit.aic)}
            results.append(record)
            _append_checkpoint(record)
            logger.info(
                "order=%s seasonal_order=%s -> val MAPE=%.2f%%",
                spec["order"],
                spec["seasonal_order"],
                val_mape,
            )
        except Exception as exc:  # statsmodels can raise on ill-conditioned orders
            logger.warning("order=%s failed: %s", spec, exc)
            _append_checkpoint({**spec, "val_mape": float("inf"), "aic": None, "error": str(exc)})
    if not results:
        raise RuntimeError("Every candidate SARIMAX order failed to fit.")
    results = [r for r in results if np.isfinite(r["val_mape"])]
    best = min(results, key=lambda r: r["val_mape"])
    return {"best": best, "all_results": results}


def _rolling_day_ahead_test(
    train: pd.Series, val: pd.Series, test: pd.Series, order: dict
) -> pd.DataFrame:
    history = pd.concat([train, val])
    model = SARIMAX(
        history.to_numpy(),
        order=order["order"],
        seasonal_order=order["seasonal_order"],
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    fit = model.fit(disp=False, maxiter=50)

    test_df = test.reset_index()
    test_df.columns = ["ts_ist", "load_mw"]
    n_days = len(test_df) // 24
    rows = []
    for day in range(n_days):
        day_slice = test_df.iloc[day * 24 : (day + 1) * 24]
        if len(day_slice) < 24:
            break
        day_start = day_slice["ts_ist"].iloc[0]
        forecast = fit.forecast(steps=24)
        rows.append(
            pd.DataFrame(
                {
                    "ts_origin": day_start - pd.Timedelta(hours=1),
                    "hour_of_day": range(24),
                    "ts_target": day_slice["ts_ist"].array,
                    "actual_mw": day_slice["load_mw"].values,
                    "predicted_mw": forecast,
                }
            )
        )
        fit = fit.append(day_slice["load_mw"].to_numpy(), refit=False)

    return pd.concat(rows, ignore_index=True)


def _broadcast_to_15min(hourly_preds: pd.DataFrame) -> pd.DataFrame:
    expanded = hourly_preds.loc[hourly_preds.index.repeat(4)].reset_index(drop=True)
    sub_block = np.tile(np.arange(4), len(hourly_preds))
    expanded["ts_target"] = expanded["ts_target"] + pd.to_timedelta(sub_block * 15, unit="min")
    expanded["ts_origin"] = expanded["ts_origin"] + pd.Timedelta(
        minutes=45
    )  # align to a 15-min grid point
    expanded["horizon"] = expanded["hour_of_day"] * 4 + sub_block + 1
    expanded["target_block"] = block_of_timestamp(expanded["ts_target"])
    return expanded[
        ["ts_origin", "horizon", "ts_target", "target_block", "actual_mw", "predicted_mw"]
    ]


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    train, val, test = _load_hourly_splits()
    logger.info("Hourly series: train=%d val=%d test=%d", len(train), len(val), len(test))

    search = _select_order(train, val)
    best = search["best"]
    logger.info(
        "Selected order=%s seasonal_order=%s (val MAPE=%.2f%%)",
        best["order"],
        best["seasonal_order"],
        best["val_mape"],
    )

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS_DIR / "sarimax_order_search.json").write_text(json.dumps(search, indent=2))

    hourly_preds = _rolling_day_ahead_test(train, val, test, best)
    preds_15min = _broadcast_to_15min(hourly_preds)
    preds_15min = preds_15min.dropna(subset=["actual_mw", "predicted_mw"])

    scored = hourly_preds.dropna(subset=["actual_mw"])
    test_mape = mape(scored["actual_mw"].to_numpy(), scored["predicted_mw"].to_numpy())
    logger.info("Rolling day-ahead TEST MAPE (hourly): %.2f%%", test_mape)

    path = save_predictions("sarimax", preds_15min)
    logger.info("Wrote %s (%d rows)", path, len(preds_15min))


if __name__ == "__main__":
    main()
