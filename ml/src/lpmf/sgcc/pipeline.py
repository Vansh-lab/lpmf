"""End-to-end SGCC theft-detection pipeline: load -> validate -> drop
all-missing consumers -> consumer-level stratified split -> causal
cleaning (train-only stats) -> per-consumer features -> logistic
regression baseline -> LightGBM (Optuna-tuned on val) -> evaluate once on
test -> K-means segments. Writes artifacts to models/artifacts/sgcc/.

Run from the repo root:
    python -m lpmf.sgcc.pipeline [--n-trials 25]
"""

from __future__ import annotations

import json
import logging
import pickle
import time
from pathlib import Path

from sklearn.metrics import roc_auc_score

from lpmf.sgcc import clean, features, models, segments, split
from lpmf.sgcc.load import drop_all_missing_consumers, load_raw, validate_against_paper
from lpmf.sgcc.metrics import best_f1_threshold

logger = logging.getLogger(__name__)
ARTIFACTS_DIR = Path("models/artifacts/sgcc")


def main(n_trials: int = 25) -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    logger.info("Loading raw SGCC data...")
    raw = load_raw()
    checks = validate_against_paper(raw)
    logger.info("Validation vs paper/README: %s", checks)
    (ARTIFACTS_DIR / "dataset_validation.json").write_text(json.dumps(checks, indent=2))

    data, n_dropped = drop_all_missing_consumers(raw)
    logger.info("Dropped %d all-missing consumers (%d remain).", n_dropped, data.cons_no.shape[0])

    logger.info("Splitting (consumer-level, stratified, 70/15/15)...")
    splits = split.split_dataset(data)
    for name, d in splits.items():
        logger.info("  %s: %d consumers, theft rate %.4f", name, d.cons_no.shape[0], d.flag.mean())

    logger.info("Fitting causal cleaning on train only...")
    stats = clean.fit_cleaning(splits["train"])
    cleaned = {name: clean.apply_cleaning(d, stats) for name, d in splits.items()}

    cache_path = ARTIFACTS_DIR / "features_cache.pkl"
    if cache_path.exists():
        logger.info("Loading cached per-consumer features from %s...", cache_path)
        X = pickle.loads(cache_path.read_bytes())
    else:
        logger.info("Building per-consumer features (slow; cached afterwards)...")
        X = {name: features.build_features(d) for name, d in cleaned.items()}
        cache_path.write_bytes(pickle.dumps(X))
    y = {name: d.flag for name, d in cleaned.items()}

    logger.info("Training logistic-regression baseline...")
    logreg, scaler = models.train_logistic_regression(X["train"], y["train"])
    logreg_val_score = logreg.predict_proba(scaler.transform(X["val"]))[:, 1]
    logreg_threshold = best_f1_threshold(y["val"], logreg_val_score)
    logreg_metrics = {
        name: models.eval_logreg(logreg, scaler, X[name], y[name], logreg_threshold) for name in X
    }
    logger.info(
        "Logistic regression: val AUC=%.4f test AUC=%.4f",
        logreg_metrics["val"]["auc_roc"],
        logreg_metrics["test"]["auc_roc"],
    )

    logger.info("Tuning LightGBM on val (%d trials)...", n_trials)
    study = models.tune_lightgbm(X["train"], y["train"], X["val"], y["val"], n_trials=n_trials)
    logger.info("Best val PR-AUC during search: %.4f", study.best_value)

    logger.info("Training final LightGBM with best params...")
    booster = models.train_final_lightgbm(
        X["train"], y["train"], X["val"], y["val"], study.best_params
    )
    lgb_val_score = booster.predict(X["val"], num_iteration=booster.best_iteration)
    lgb_threshold = best_f1_threshold(y["val"], lgb_val_score)
    lgb_metrics = {
        name: models.eval_lightgbm(booster, X[name], y[name], lgb_threshold) for name in X
    }
    logger.info(
        "LightGBM: train AUC=%.4f val AUC=%.4f test AUC=%.4f (test scored once)",
        lgb_metrics["train"]["auc_roc"],
        lgb_metrics["val"]["auc_roc"],
        lgb_metrics["test"]["auc_roc"],
    )

    logger.info("Learning curve (train/val/test AUC vs boosting round)...")
    curve = []
    for it in (10, 25, 50, 100, 150, 200, booster.best_iteration):
        row = {"iter": int(it)}
        for name in ("train", "val", "test"):
            score = booster.predict(X[name], num_iteration=it)
            row[f"{name}_auc"] = float(roc_auc_score(y[name], score))
        curve.append(row)

    # Save the model and what we have so far BEFORE the K-means step, so a
    # crash there (it has already OOM'd once) can't lose the ~15-20 min of
    # Optuna tuning + final training above. results.json is overwritten
    # again below once segments complete.
    booster.save_model(str(ARTIFACTS_DIR / "lightgbm_sgcc.txt"))
    results = {
        "n_consumers_after_drop": int(data.cons_no.shape[0]),
        "n_dropped_all_missing": n_dropped,
        "split_sizes": {k: int(v.cons_no.shape[0]) for k, v in splits.items()},
        "split_theft_rates": {k: float(v.flag.mean()) for k, v in splits.items()},
        "logreg_threshold": logreg_threshold,
        "logreg_metrics": logreg_metrics,
        "lightgbm_best_params": study.best_params,
        "lightgbm_threshold": lgb_threshold,
        "lightgbm_metrics": lgb_metrics,
        "lightgbm_best_iteration": booster.best_iteration,
        "learning_curve": curve,
        "seconds": round(time.time() - t0, 1),
    }
    (ARTIFACTS_DIR / "results.json").write_text(json.dumps(results, indent=2, default=str))
    logger.info("Checkpointed model + metrics (pre-segments) to %s", ARTIFACTS_DIR)

    logger.info("Fitting K-means segments (train-fit, k scan)...")
    k_scan = segments.scan_k(X["train"], ks=[2, 3, 4, 5, 6])
    best_k = max(k_scan, key=k_scan.get)
    seg_model, seg_scaler = segments.fit_segments(X["train"], n_clusters=best_k)
    seg_results = {}
    for name in X:
        labels, sil = segments.assign_segments(seg_model, seg_scaler, X[name])
        seg_results[name] = {
            "silhouette": sil,
            "cluster_sizes": {int(c): int((labels == c).sum()) for c in set(labels)},
        }

    results["kmeans_k_scan_silhouette"] = k_scan
    results["kmeans_best_k"] = int(best_k)
    results["kmeans_segments"] = seg_results
    results["seconds"] = round(time.time() - t0, 1)
    (ARTIFACTS_DIR / "results.json").write_text(json.dumps(results, indent=2, default=str))
    logger.info("Done in %.1fs. Wrote %s", time.time() - t0, ARTIFACTS_DIR / "results.json")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--n-trials", type=int, default=25)
    main(n_trials=parser.parse_args().n_trials)
