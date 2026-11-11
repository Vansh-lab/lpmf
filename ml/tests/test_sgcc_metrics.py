"""sgcc.metrics: precision@k, threshold selection, the full evaluate() dict."""

from __future__ import annotations

import numpy as np
import pytest

from lpmf.sgcc.metrics import best_f1_threshold, evaluate, precision_at_k


def test_precision_at_k_on_a_perfectly_ranked_list():
    y_true = np.array([1, 1, 0, 0, 0])
    y_score = np.array([0.9, 0.8, 0.3, 0.2, 0.1])
    assert precision_at_k(y_true, y_score, 2) == pytest.approx(1.0)
    assert precision_at_k(y_true, y_score, 5) == pytest.approx(0.4)


def test_precision_at_k_clips_k_to_the_available_rows():
    y_true = np.array([1, 0])
    y_score = np.array([0.9, 0.1])
    assert precision_at_k(y_true, y_score, 100) == pytest.approx(0.5)


def test_best_f1_threshold_prefers_the_separating_point():
    y_true = np.array([0, 0, 0, 1, 1, 1])
    y_score = np.array([0.1, 0.2, 0.3, 0.7, 0.8, 0.9])
    t = best_f1_threshold(y_true, y_score)
    y_pred = (y_score >= t).astype(int)
    assert y_pred.tolist() == y_true.tolist()  # a clean separation is achievable here


def test_evaluate_reports_all_pages_metrics_and_the_all_normal_baseline():
    y_true = np.array([0] * 90 + [1] * 10)
    y_score = np.r_[
        np.random.default_rng(0).uniform(0, 0.4, 90), np.random.default_rng(1).uniform(0.6, 1, 10)
    ]
    out = evaluate(y_true, y_score, threshold=0.5)
    for key in (
        "auc_roc",
        "pr_auc",
        "precision",
        "recall",
        "f1",
        "accuracy",
        "map_at_100",
        "map_at_200",
    ):
        assert key in out
    assert out["all_normal_baseline_accuracy"] == pytest.approx(0.9)
    assert out["theft_rate"] == pytest.approx(0.1)
    assert out["auc_roc"] > 0.9  # scores are well-separated by construction


def test_evaluate_handles_a_threshold_that_rejects_everyone():
    y_true = np.array([0, 0, 1])
    y_score = np.array([0.1, 0.2, 0.3])
    out = evaluate(y_true, y_score, threshold=0.99)
    assert out["precision"] == 0.0
    assert out["recall"] == 0.0
    assert out["f1"] == 0.0
