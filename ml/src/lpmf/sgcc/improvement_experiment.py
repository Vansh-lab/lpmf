"""Honest, val-only improvement attempt for the locked SGCC theft model.

Three candidates, compared ONLY on val PR-AUC (the same metric the locked
model's own Optuna search already optimizes against -- pre-registered
here, not picked after seeing results, to avoid choosing whichever metric
makes an improvement look best):

  1. Baseline: the already-locked LightGBM (`models/artifacts/sgcc/lightgbm_sgcc.txt`
     + its best_params from results.json), scored on val -- no retraining.
  2. Extended features: the locked feature set + two new features
     (`weekly_pattern_break`, `recent_volatility_ratio`), Optuna-retuned
     with a WIDER search space (more trials, wider regularisation range).
  3. Ensemble: average of the logistic-regression baseline's probability
     and whichever LightGBM (1 or 2) scores higher alone on val.

Whichever of the three has the best val PR-AUC is the winner. If the
winner is #1 (baseline unchanged), test is NEVER touched and nothing is
saved -- the original locked model and its test score stand as-is. If #2
or #3 wins, THAT ONE candidate is scored on test exactly once, and the
result is reported honestly either way (even if it's worse than the
baseline's own test score, which can happen since val and test are
different samples).

Run from the repo root:
    python -m lpmf.sgcc.improvement_experiment
"""

from __future__ import annotations

import json
import logging
import pickle
from pathlib import Path

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd

from lpmf.sgcc import clean, split
from lpmf.sgcc.features_experimental import build_additional_features
from lpmf.sgcc.load import drop_all_missing_consumers, load_raw
from lpmf.sgcc.metrics import best_f1_threshold, evaluate
from lpmf.sgcc.models import RNG_SEED, train_logistic_regression

logger = logging.getLogger(__name__)
ARTIFACTS_DIR = Path("models/artifacts/sgcc")
optuna.logging.set_verbosity(optuna.logging.WARNING)


def _pr_auc_feval(y_pred: np.ndarray, data: lgb.Dataset) -> tuple[str, float, bool]:
    from sklearn.metrics import average_precision_score

    return "pr_auc", float(average_precision_score(data.get_label(), y_pred)), True


def _wide_lgb_params(trial: optuna.Trial, scale_pos_weight: float) -> dict:
    """Same shape as the locked model's search space, but wider: more
    num_leaves headroom and a much wider regularisation range, as
    requested -- still tuned against val PR-AUC only."""
    return {
        "objective": "binary",
        "metric": "None",
        "verbosity": -1,
        "seed": RNG_SEED,
        "scale_pos_weight": scale_pos_weight,
        "feature_pre_filter": False,
        "num_leaves": trial.suggest_int("num_leaves", 8, 256, log=True),
        "max_depth": trial.suggest_int("max_depth", 3, 12),
        "learning_rate": trial.suggest_float("learning_rate", 0.005, 0.3, log=True),
        "min_child_samples": trial.suggest_int("min_child_samples", 5, 150, log=True),
        "feature_fraction": trial.suggest_float("feature_fraction", 0.5, 1.0),
        "bagging_fraction": trial.suggest_float("bagging_fraction", 0.5, 1.0),
        "bagging_freq": 1,
        "lambda_l1": trial.suggest_float("lambda_l1", 1e-8, 50.0, log=True),
        "lambda_l2": trial.suggest_float("lambda_l2", 1e-8, 50.0, log=True),
    }


def _tune_wide(X_train, y_train, X_val, y_val, n_trials: int) -> optuna.Study:
    scale_pos_weight = float((y_train == 0).sum() / max((y_train == 1).sum(), 1))
    dtrain = lgb.Dataset(X_train, label=y_train)
    dval = lgb.Dataset(X_val, label=y_val, reference=dtrain)

    def objective(trial: optuna.Trial) -> float:
        params = _wide_lgb_params(trial, scale_pos_weight)
        booster = lgb.train(
            params,
            dtrain,
            num_boost_round=500,
            valid_sets=[dval],
            feval=_pr_auc_feval,
            callbacks=[lgb.early_stopping(30, verbose=False)],
        )
        return booster.best_score["valid_0"]["pr_auc"]

    study = optuna.create_study(
        direction="maximize", sampler=optuna.samplers.TPESampler(seed=RNG_SEED)
    )
    study.optimize(objective, n_trials=n_trials)
    return study


def _train_final(X_train, y_train, X_val, y_val, best_params: dict) -> lgb.Booster:
    scale_pos_weight = float((y_train == 0).sum() / max((y_train == 1).sum(), 1))
    dtrain = lgb.Dataset(X_train, label=y_train)
    dval = lgb.Dataset(X_val, label=y_val, reference=dtrain)
    params = {
        "objective": "binary",
        "metric": "None",
        "verbosity": -1,
        "seed": RNG_SEED,
        "scale_pos_weight": scale_pos_weight,
        "bagging_freq": 1,
        **best_params,
    }
    return lgb.train(
        params,
        dtrain,
        num_boost_round=2000,
        valid_sets=[dval],
        feval=_pr_auc_feval,
        callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(0)],
    )


def main(n_trials: int = 60) -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    locked_results = json.loads((ARTIFACTS_DIR / "results.json").read_text())
    baseline_val_pr_auc = locked_results["lightgbm_metrics"]["val"]["pr_auc"]
    logger.info("Baseline (locked model) val PR-AUC: %.4f", baseline_val_pr_auc)

    logger.info("Rebuilding splits/cleaning (cheap) and loading cached base features...")
    raw = load_raw()
    data, _ = drop_all_missing_consumers(raw)
    splits = split.split_dataset(data)
    stats = clean.fit_cleaning(splits["train"])
    cleaned = {name: clean.apply_cleaning(d, stats) for name, d in splits.items()}
    base_X = pickle.loads((ARTIFACTS_DIR / "features_cache.pkl").read_bytes())
    y = {name: d.flag for name, d in cleaned.items()}

    logger.info(
        "Building the 2 additional features (weekly_pattern_break, recent_volatility_ratio)..."
    )
    extra = {name: build_additional_features(d) for name, d in cleaned.items()}
    extended_X = {name: pd.concat([base_X[name], extra[name]], axis=1) for name in base_X}

    # --- Candidate 1: baseline, no retraining -------------------------------
    baseline_booster = lgb.Booster(model_file=str(ARTIFACTS_DIR / "lightgbm_sgcc.txt"))
    baseline_val_score = baseline_booster.predict(
        base_X["val"], num_iteration=baseline_booster.best_iteration
    )

    # --- Candidate 2: extended features, wider Optuna search ----------------
    logger.info("Tuning extended-feature LightGBM (%d trials, wider search space)...", n_trials)
    study = _tune_wide(
        extended_X["train"], y["train"], extended_X["val"], y["val"], n_trials=n_trials
    )
    logger.info("Extended-feature search best val PR-AUC: %.4f", study.best_value)
    extended_booster = _train_final(
        extended_X["train"], y["train"], extended_X["val"], y["val"], study.best_params
    )
    extended_val_score = extended_booster.predict(
        extended_X["val"], num_iteration=extended_booster.best_iteration
    )
    from sklearn.metrics import average_precision_score

    extended_val_pr_auc = float(average_precision_score(y["val"], extended_val_score))

    # --- logistic regression baseline (unchanged, on base features) --------
    logreg, scaler = train_logistic_regression(base_X["train"], y["train"])
    logreg_val_score = logreg.predict_proba(scaler.transform(base_X["val"]))[:, 1]

    # --- Candidate 3: ensemble (logreg + whichever LightGBM is better solo) -
    best_lgb_name, best_lgb_val_score = (
        ("extended", extended_val_score)
        if extended_val_pr_auc > baseline_val_pr_auc
        else ("baseline", baseline_val_score)
    )
    ensemble_val_score = (logreg_val_score + best_lgb_val_score) / 2.0
    ensemble_val_pr_auc = float(average_precision_score(y["val"], ensemble_val_score))

    candidates = {
        "baseline": baseline_val_pr_auc,
        "extended_features": extended_val_pr_auc,
        f"ensemble_logreg_plus_{best_lgb_name}": ensemble_val_pr_auc,
    }
    logger.info("Val PR-AUC by candidate: %s", candidates)
    winner = max(candidates, key=candidates.get)
    logger.info("Winner (val PR-AUC): %s (%.4f)", winner, candidates[winner])

    result = {
        "pre_registered_decision_metric": "val_pr_auc",
        "baseline_val_pr_auc": baseline_val_pr_auc,
        "extended_features_val_pr_auc": extended_val_pr_auc,
        "ensemble_val_pr_auc": ensemble_val_pr_auc,
        "ensemble_uses_lightgbm": best_lgb_name,
        "extended_features_best_params": study.best_params,
        "winner": winner,
        "improved_over_baseline": winner != "baseline",
    }

    if winner == "baseline":
        logger.info(
            "No candidate beat the baseline on val. Test NOT touched; original result stands."
        )
        result["test_run"] = False
    else:
        logger.info("Winner '%s' beats baseline on val -- scoring test ONCE now.", winner)
        if winner == "extended_features":
            test_score = extended_booster.predict(
                extended_X["test"], num_iteration=extended_booster.best_iteration
            )
        else:  # ensemble
            lgb_test_score = (
                extended_booster.predict(
                    extended_X["test"], num_iteration=extended_booster.best_iteration
                )
                if best_lgb_name == "extended"
                else baseline_booster.predict(
                    base_X["test"], num_iteration=baseline_booster.best_iteration
                )
            )
            logreg_test_score = logreg.predict_proba(scaler.transform(base_X["test"]))[:, 1]
            test_score = (logreg_test_score + lgb_test_score) / 2.0

        threshold = best_f1_threshold(
            y["val"], ensemble_val_score if winner != "extended_features" else extended_val_score
        )
        test_metrics = evaluate(y["test"], test_score, threshold)
        baseline_test_auc = locked_results["lightgbm_metrics"]["test"]["auc_roc"]
        logger.info(
            "Test AUC-ROC: winner=%.4f vs locked baseline=%.4f (reported honestly either way)",
            test_metrics["auc_roc"],
            baseline_test_auc,
        )
        result["test_run"] = True
        result["test_metrics"] = test_metrics
        result["baseline_test_auc_roc_for_comparison"] = baseline_test_auc

    (ARTIFACTS_DIR / "improvement_experiment.json").write_text(
        json.dumps(result, indent=2, default=str)
    )
    logger.info("Wrote %s", ARTIFACTS_DIR / "improvement_experiment.json")


if __name__ == "__main__":
    main()
