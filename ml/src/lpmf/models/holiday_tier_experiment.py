"""Phase-4 experiment: does a holiday_tier (major/minor) feature beat the
plain target_is_holiday flag the final model already has?

Motivation (docs/MODEL_RESULTS.md): Diwali was the weakest of the four SHAP
example days (8.65% day MAPE) because target_is_holiday treats every
holiday alike. holiday_tier (0/1/2, see features.build.MAJOR_HOLIDAYS)
distinguishes major festivals/national holidays from minor observances.

Strict discipline, per the brief: every keep/discard decision uses VAL MAPE
only; TEST is read once, at the end, and reported honestly whatever it
says — including if it is worse than the locked final model's 3.93%. The
locked model/artifacts are never touched by this script; if the feature is
kept, the new model is saved under a different filename and the decision
is left to a human (see main()'s final log line).

Implementation note: lpmf.models.lightgbm.build_long_format and
feature_matrix read the module-level TARGET_CALENDAR_COLS/ALL_FEATURE_NAMES
constants, not parameters, so this script monkeypatches them for the
duration of long-format building only, then restores the originals —
reusing the already-tested long-format logic instead of duplicating it.
"""

from __future__ import annotations

import contextlib
import json
import logging

import lightgbm as lgb

from lpmf.models import lightgbm as lgb_module
from lpmf.models.common import ARTIFACTS_DIR, load_features_and_boundaries, mape

logger = logging.getLogger(__name__)
NEW_FEATURE = "target_holiday_tier"
RESULTS_PATH = ARTIFACTS_DIR / "holiday_tier_experiment.json"
NEW_MODEL_PATH = ARTIFACTS_DIR / "lightgbm_model_holiday_tier.txt"


@contextlib.contextmanager
def _with_holiday_tier_feature():
    """Temporarily extends TARGET_CALENDAR_COLS/ALL_FEATURE_NAMES so
    build_long_format/feature_matrix include target_holiday_tier, then
    restores both exactly — the locked 37-feature model is never affected
    by this script running."""
    orig_cols = lgb_module.TARGET_CALENDAR_COLS
    orig_names = lgb_module.ALL_FEATURE_NAMES
    try:
        lgb_module.TARGET_CALENDAR_COLS = [*orig_cols, "holiday_tier"]
        insert_at = orig_names.index(f"target_{orig_cols[-1]}") + 1
        lgb_module.ALL_FEATURE_NAMES = [
            *orig_names[:insert_at],
            NEW_FEATURE,
            *orig_names[insert_at:],
        ]
        yield lgb_module.ALL_FEATURE_NAMES
    finally:
        lgb_module.TARGET_CALENDAR_COLS = orig_cols
        lgb_module.ALL_FEATURE_NAMES = orig_names


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    df, _ = load_features_and_boundaries()
    search = json.loads((ARTIFACTS_DIR / "lightgbm_search.json").read_text())
    params = {
        "objective": "regression",
        "metric": "None",
        "verbosity": -1,
        "seed": lgb_module.RNG_SEED,
        "bagging_freq": 1,
        **search["best_params"],
    }

    with _with_holiday_tier_feature() as feature_names:
        logger.info("Feature set: %d features (37 + %s).", len(feature_names), NEW_FEATURE)
        train_long = lgb_module.build_long_format(df, "train")
        val_long = lgb_module.build_long_format(df, "val")
        test_long = lgb_module.build_long_format(df, "test")

        X = lambda long_df: long_df[feature_names].astype({"horizon": "float32"})  # noqa: E731
        dtrain = lgb.Dataset(X(train_long), label=train_long["actual_mw"])
        dval = lgb.Dataset(X(val_long), label=val_long["actual_mw"], reference=dtrain)

        logger.info("Training with holiday_tier (locked hyperparameters, early-stopped on val)...")
        booster = lgb.train(
            params,
            dtrain,
            num_boost_round=3000,
            valid_sets=[dval],
            feval=lgb_module._mape_feval,
            callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(0)],
        )
        val_mape_new = booster.best_score["valid_0"]["mape_pct"]

    baseline_val_mape = search["final_model_val_mape"]  # 4.29%, locked model, already reported
    logger.info(
        "VAL MAPE: baseline (37 features) %.4f%% vs with holiday_tier (38 features) %.4f%%.",
        baseline_val_mape,
        val_mape_new,
    )

    keep = val_mape_new < baseline_val_mape
    result = {
        "baseline_val_mape": baseline_val_mape,
        "holiday_tier_val_mape": val_mape_new,
        "val_improved": keep,
        "best_iteration": booster.best_iteration,
    }

    if not keep:
        logger.info(
            "Val MAPE did not improve (%.4f%% >= %.4f%%). Discarding: not run on test, not saved, "
            "the locked 37-feature model (models/artifacts/lightgbm_model.txt) is unchanged.",
            val_mape_new,
            baseline_val_mape,
        )
        result["test_mape"] = None
        result["note"] = "Discarded on val; test intentionally not run for a discarded feature."
    else:
        logger.info("Val MAPE improved. Scoring test ONCE (reported regardless of the result)...")
        with _with_holiday_tier_feature() as feature_names:
            test_long = lgb_module.build_long_format(df, "test")
            X_test = test_long[feature_names].astype({"horizon": "float32"})
        test_pred = booster.predict(X_test, num_iteration=booster.best_iteration)
        test_mape_new = mape(test_long["actual_mw"].to_numpy(), test_pred)
        baseline_test_mape = 3.93  # locked model, docs/MODEL_RESULTS.md
        result["test_mape"] = test_mape_new
        result["baseline_test_mape"] = baseline_test_mape
        result["test_improved"] = test_mape_new < baseline_test_mape
        logger.info(
            "TEST MAPE: baseline %.2f%% vs with holiday_tier %.4f%% (%s).",
            baseline_test_mape,
            test_mape_new,
            "better" if result["test_improved"] else "WORSE — reporting honestly, not hiding it",
        )
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        booster.save_model(str(NEW_MODEL_PATH))
        logger.info(
            "Saved candidate model to %s (separate file; models/artifacts/lightgbm_model.txt, "
            "the locked final model, was not touched). Ask the user before replacing it.",
            NEW_MODEL_PATH,
        )

    RESULTS_PATH.write_text(json.dumps(result, indent=2))
    logger.info("Wrote %s", RESULTS_PATH)


if __name__ == "__main__":
    main()
