"""sgcc.summary: read-only loader of the already-trained pipeline's
artifacts for the Theft & Segments page."""

from __future__ import annotations

import json

from lpmf.provenance import ProvenanceKind
from lpmf.sgcc.summary import REQUIRED_FOREIGN_NOTE, load_sgcc_summary

_RESULTS = {
    "logreg_metrics": {"test": {"auc_roc": 0.71, "precision": 0.2}},
    "lightgbm_metrics": {
        "train": {"auc_roc": 0.91},
        "val": {"auc_roc": 0.75},
        "test": {"auc_roc": 0.76, "precision": 0.29},
    },
    "kmeans_best_k": 3,
    "kmeans_segments": {
        "train": {"silhouette": 0.54},
        "val": {"silhouette": 0.55},
        "test": {"silhouette": 0.54},
    },
}
_VALIDATION = {"n_consumers": 42372, "n_day_columns": 1034, "theft_rate": 0.0853}


def test_returns_none_when_artifacts_are_missing(tmp_path):
    assert load_sgcc_summary(tmp_path / "does-not-exist") is None


def test_loads_and_shapes_the_real_artifacts(tmp_path):
    (tmp_path / "results.json").write_text(json.dumps(_RESULTS))
    (tmp_path / "dataset_validation.json").write_text(json.dumps(_VALIDATION))

    out = load_sgcc_summary(tmp_path)

    assert out["provenance"] == ProvenanceKind.FOREIGN
    assert out["note"] == REQUIRED_FOREIGN_NOTE
    assert out["dataset"]["n_consumers"] == 42372
    assert out["lightgbm_test"]["auc_roc"] == 0.76
    assert out["lightgbm_train_auc_roc"] == 0.91
    assert out["lightgbm_val_auc_roc"] == 0.75
    assert out["kmeans_best_k"] == 3
    assert out["kmeans_silhouette"] == {"train": 0.54, "val": 0.55, "test": 0.54}
    assert out["paper_test_auc_roc"] == 0.78
