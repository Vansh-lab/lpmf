"""Read-only summary of the trained SGCC theft-detection pipeline, for
display on the Theft & Segments page. Never retrains anything — reads the
artifacts `lpmf.sgcc.pipeline.main()` already wrote to
models/artifacts/sgcc/ (dataset_validation.json, results.json).
"""

from __future__ import annotations

import json
from pathlib import Path

from lpmf.provenance import ProvenanceKind

ARTIFACTS_DIR = Path("models/artifacts/sgcc")

REQUIRED_FOREIGN_NOTE = (
    "Method demonstrated on public SGCC benchmark; Delhi DISCOM meter data "
    "would be needed for deployment."
)

PAPER_TEST_AUC_ROC = 0.78  # Zheng et al. 2018, as stated in the brief — not independently
# verified (paywalled paper, no accessible source confirmed this exact figure).


def load_sgcc_summary(artifacts_dir: Path = ARTIFACTS_DIR) -> dict | None:
    """The real-SGCC model-ladder + segments summary, or None if the
    pipeline hasn't been run yet (artifacts missing).

    `artifacts_dir` defaults to a path relative to the process's cwd (the
    repo root, as `lpmf.sgcc.pipeline` is run) — callers with a different
    cwd (e.g. the API, started from `api/`) must pass the resolved path
    explicitly (see `app.config.settings.repo_root`).
    """
    results_path = artifacts_dir / "results.json"
    validation_path = artifacts_dir / "dataset_validation.json"
    if not results_path.exists() or not validation_path.exists():
        return None

    results = json.loads(results_path.read_text())
    validation = json.loads(validation_path.read_text())

    lgb_test = results["lightgbm_metrics"]["test"]
    return {
        "provenance": ProvenanceKind.FOREIGN,
        "note": REQUIRED_FOREIGN_NOTE,
        "dataset": {
            "n_consumers": validation["n_consumers"],
            "n_days": validation["n_day_columns"],
            "theft_rate": validation["theft_rate"],
        },
        "logreg_test": results["logreg_metrics"]["test"],
        "lightgbm_test": lgb_test,
        "lightgbm_train_auc_roc": results["lightgbm_metrics"]["train"]["auc_roc"],
        "lightgbm_val_auc_roc": results["lightgbm_metrics"]["val"]["auc_roc"],
        "paper_test_auc_roc": PAPER_TEST_AUC_ROC,
        "kmeans_best_k": results["kmeans_best_k"],
        "kmeans_silhouette": {
            name: seg["silhouette"] for name, seg in results["kmeans_segments"].items()
        },
    }
