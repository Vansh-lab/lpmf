"""Phase 4a: split-conformal prediction bands around the final LightGBM.

MAPIE split-conformal, calibrated on the VAL split (every val (origin,
horizon) row, ~1.66M), evaluated on TEST. The point model is frozen (it is
already early-stopped on val; conformalizing on the same val rows is the
documented Phase-3 protocol, and the lightgbm tuning leakage into val is
small — see MODEL_RESULTS.md).

P10-P90 is, by construction, an 80% central interval: confidence_level=0.80.
Marginal coverage is guaranteed only under exchangeability of val and test
residuals. They are NOT exchangeable here (val is Jan-Jul, test is
Jul-Jan, and error depends on season and horizon), so the empirical test
coverage is the honest number and is reported overall and sliced by
horizon bucket and month, not just marginally.

Two nonconformity scores are run:
  absolute  -- |y - yhat|; constant-width band in MW (the primary, pre-declared)
  gamma     -- |y - yhat| / yhat; band width proportional to the forecast,
               which matches the MAPE metric and the load's heteroscedasticity
The primary columns (lower_mw / upper_mw) are the absolute score.

Output: models/artifacts/conformal_bands.parquet (TEST rows only).
"""

from __future__ import annotations

import json
import logging

import lightgbm as lgb
import pandas as pd
from mapie.regression import SplitConformalRegressor
from sklearn.base import BaseEstimator, RegressorMixin

from lpmf.models.common import ARTIFACTS_DIR, load_features_and_boundaries, season_of
from lpmf.models.lightgbm import build_long_format, feature_matrix

logger = logging.getLogger(__name__)

CONFIDENCE = 0.80
MODEL_PATH = ARTIFACTS_DIR / "lightgbm_model.txt"
BANDS_PATH = ARTIFACTS_DIR / "conformal_bands.parquet"
SUMMARY_PATH = ARTIFACTS_DIR / "conformal_summary.json"
BUCKETS = [(1, 4, "h01-04"), (5, 24, "h05-24"), (25, 48, "h25-48"), (49, 96, "h49-96")]


class BoosterRegressor(BaseEstimator, RegressorMixin):
    """Thin sklearn face over a fitted lgb.Booster, so MAPIE can run prefit."""

    def __init__(self, booster: lgb.Booster):
        self.booster = booster

    def fit(self, X, y=None):  # never called: prefit
        return self

    def __sklearn_is_fitted__(self) -> bool:
        return True

    def predict(self, X):
        return self.booster.predict(X, num_iteration=self.booster.best_iteration or None)


def _interval(booster: lgb.Booster, score: str, X_cal, y_cal, X_test):
    mapie = SplitConformalRegressor(
        estimator=BoosterRegressor(booster),
        confidence_level=CONFIDENCE,
        conformity_score=score,
        prefit=True,
    )
    mapie.conformalize(X_cal, y_cal)
    point, bands = mapie.predict_interval(X_test)
    return point, bands[:, 0, 0], bands[:, 1, 0]


def _coverage_table(df: pd.DataFrame, lo: str, hi: str) -> dict:
    inside = ((df["actual_mw"] >= df[lo]) & (df["actual_mw"] <= df[hi])).to_numpy()
    out = {"overall": float(inside.mean()), "mean_width_mw": float((df[hi] - df[lo]).mean())}
    for a, b, name in BUCKETS:
        m = df["horizon"].between(a, b).to_numpy()
        out[name] = float(inside[m].mean())
    month = df["ts_target"].dt.month
    out["by_month"] = {
        int(k): float(inside[(month == k).to_numpy()].mean()) for k in sorted(month.unique())
    }
    season = season_of(month)
    out["by_season"] = {
        s: float(inside[(season == s).to_numpy()].mean()) for s in sorted(set(season))
    }
    return out


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    df, _ = load_features_and_boundaries()
    booster = lgb.Booster(model_file=str(MODEL_PATH))
    val_long = build_long_format(df, "val")
    test_long = build_long_format(df, "test")
    X_val, y_val = feature_matrix(val_long), val_long["actual_mw"].to_numpy()
    X_test = feature_matrix(test_long)

    bands = test_long[["ts_origin", "horizon", "ts_target", "target_block", "actual_mw"]].copy()
    summary: dict = {
        "confidence_level": CONFIDENCE,
        "n_cal": len(val_long),
        "n_test": len(test_long),
    }
    for score, suffix in (("absolute", ""), ("gamma", "_rel")):
        point, lo, hi = _interval(booster, score, X_val, y_val, X_test)
        if suffix == "":
            bands["predicted_mw"] = point
        bands[f"lower_mw{suffix}"] = lo
        bands[f"upper_mw{suffix}"] = hi
        summary[score] = _coverage_table(bands, f"lower_mw{suffix}", f"upper_mw{suffix}")
        logger.info(
            "%s: test coverage %.3f (target %.2f), mean width %.0f MW",
            score,
            summary[score]["overall"],
            CONFIDENCE,
            summary[score]["mean_width_mw"],
        )
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    bands.to_parquet(BANDS_PATH, index=False)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2))
    logger.info("Wrote %s (%d rows) and %s", BANDS_PATH, len(bands), SUMMARY_PATH)


if __name__ == "__main__":
    main()
