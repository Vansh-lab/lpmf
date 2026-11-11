"""SGCC model ladder: logistic regression baseline, then LightGBM on the
engineered features, each beating the simpler one is the bar to clear
(same ladder discipline as the main load-forecast model). A 1D-CNN on the
raw daily series was in scope only if time allowed; it was not run here
(see docs/ALL_PAGES_METRICS.md) — the ladder stops at LightGBM.

Standardisation (logistic regression) and hyperparameters (LightGBM, via
Optuna) are both fitted/tuned on train+val only; test is scored once,
at the end, with the already-fixed scaler and parameters.
"""

from __future__ import annotations

import logging

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from lpmf.sgcc.metrics import evaluate

logger = logging.getLogger(__name__)
optuna.logging.set_verbosity(optuna.logging.WARNING)

RNG_SEED = 20261111


def train_logistic_regression(
    X_train: pd.DataFrame, y_train: np.ndarray
) -> tuple[LogisticRegression, StandardScaler]:
    scaler = StandardScaler().fit(X_train)
    model = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=RNG_SEED)
    model.fit(scaler.transform(X_train), y_train)
    return model, scaler


def _lgb_params(trial: optuna.Trial, scale_pos_weight: float) -> dict:
    return {
        "objective": "binary",
        "metric": "None",
        "verbosity": -1,
        "seed": RNG_SEED,
        "scale_pos_weight": scale_pos_weight,
        # dtrain/dval are built once and reused across all trials; feature_pre_filter
        # (on by default) bakes the FIRST trial's min_child_samples into the cached
        # feature bins and rejects later trials that pick a different value.
        "feature_pre_filter": False,
        "num_leaves": trial.suggest_int("num_leaves", 8, 128, log=True),
        "max_depth": trial.suggest_int("max_depth", 3, 10),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
        "min_child_samples": trial.suggest_int("min_child_samples", 5, 100, log=True),
        "feature_fraction": trial.suggest_float("feature_fraction", 0.6, 1.0),
        "bagging_fraction": trial.suggest_float("bagging_fraction", 0.6, 1.0),
        "bagging_freq": 1,
        "lambda_l1": trial.suggest_float("lambda_l1", 1e-8, 10.0, log=True),
        "lambda_l2": trial.suggest_float("lambda_l2", 1e-8, 10.0, log=True),
    }


def _pr_auc_feval(y_pred: np.ndarray, data: lgb.Dataset) -> tuple[str, float, bool]:
    from sklearn.metrics import average_precision_score

    return "pr_auc", float(average_precision_score(data.get_label(), y_pred)), True


def tune_lightgbm(
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    X_val: pd.DataFrame,
    y_val: np.ndarray,
    n_trials: int = 25,
) -> optuna.Study:
    """Optuna tuning against VAL PR-AUC only; test is never touched here."""
    scale_pos_weight = float((y_train == 0).sum() / max((y_train == 1).sum(), 1))
    dtrain = lgb.Dataset(X_train, label=y_train)
    dval = lgb.Dataset(X_val, label=y_val, reference=dtrain)

    def objective(trial: optuna.Trial) -> float:
        params = _lgb_params(trial, scale_pos_weight)
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


def train_final_lightgbm(
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    X_val: pd.DataFrame,
    y_val: np.ndarray,
    best_params: dict,
) -> lgb.Booster:
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


def eval_logreg(
    model: LogisticRegression,
    scaler: StandardScaler,
    X: pd.DataFrame,
    y: np.ndarray,
    threshold: float,
) -> dict:
    score = model.predict_proba(scaler.transform(X))[:, 1]
    return evaluate(y, score, threshold)


def eval_lightgbm(booster: lgb.Booster, X: pd.DataFrame, y: np.ndarray, threshold: float) -> dict:
    score = booster.predict(X, num_iteration=booster.best_iteration)
    return evaluate(y, score, threshold)
