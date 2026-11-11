"""SGCC theft-detection metrics, including MAP@k as the theft-detection
literature (Zheng et al. 2018 and follow-ups) defines it for one ranked
list: precision among the top k highest-scored consumers, not the
multi-query mean-average-precision from information retrieval. With one
list the two definitions coincide, which is what "MAP@k" means here.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)


def precision_at_k(y_true: np.ndarray, y_score: np.ndarray, k: int) -> float:
    k = min(k, y_true.shape[0])
    order = np.argsort(y_score)[::-1][:k]
    return float(y_true[order].mean())


def best_f1_threshold(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """The score threshold maximising F1, chosen on whatever split is
    passed in (must be val, never test)."""
    precision, recall, thresholds = precision_recall_curve(y_true, y_score)
    f1 = np.divide(
        2 * precision * recall,
        precision + recall,
        out=np.zeros_like(precision),
        where=(precision + recall) > 0,
    )
    # precision_recall_curve returns one more point than thresholds (the
    # all-reject point with no threshold); drop it to align the arrays.
    best = int(np.argmax(f1[:-1])) if len(thresholds) else 0
    return float(thresholds[best]) if len(thresholds) else 0.5


def evaluate(y_true: np.ndarray, y_score: np.ndarray, threshold: float) -> dict:
    """y_score: predicted probability of theft (class 1). `threshold` must
    be chosen on val (see best_f1_threshold) and then reused as-is on test
    — never re-optimised per split."""
    y_pred = (y_score >= threshold).astype(int)
    all_normal_accuracy = float(1.0 - y_true.mean())  # the "predict nothing" baseline
    return {
        "n": int(y_true.shape[0]),
        "theft_rate": float(y_true.mean()),
        "auc_roc": float(roc_auc_score(y_true, y_score)),
        "pr_auc": float(average_precision_score(y_true, y_score)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "all_normal_baseline_accuracy": all_normal_accuracy,
        "map_at_100": precision_at_k(y_true, y_score, 100),
        "map_at_200": precision_at_k(y_true, y_score, 200),
        "threshold": float(threshold),
    }
