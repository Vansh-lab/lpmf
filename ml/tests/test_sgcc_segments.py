"""sgcc.segments: K-means fit on train, applied unchanged to other splits."""

from __future__ import annotations

import numpy as np
import pandas as pd

from lpmf.sgcc.segments import assign_segments, fit_segments, scan_k


def _two_blob_features(seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    blob_a = rng.normal(loc=0.0, scale=0.3, size=(50, 2))
    blob_b = rng.normal(loc=10.0, scale=0.3, size=(50, 2))
    data = np.vstack([blob_a, blob_b])
    return pd.DataFrame(data, columns=["f1", "f2"])


def test_fit_segments_separates_two_clear_blobs():
    X = _two_blob_features()
    model, scaler = fit_segments(X, n_clusters=2)
    labels, sil = assign_segments(model, scaler, X)
    assert len(set(labels)) == 2
    assert sil > 0.8  # well-separated blobs should give a high silhouette


def test_assign_segments_on_new_data_uses_the_fitted_centroids_not_a_refit():
    X_train = _two_blob_features(seed=1)
    model, scaler = fit_segments(X_train, n_clusters=2)
    X_new = _two_blob_features(seed=2)  # same two blobs, different draw
    labels, sil = assign_segments(model, scaler, X_new)
    assert len(labels) == len(X_new)
    assert sil > 0.5


def test_scan_k_returns_one_silhouette_score_per_k():
    X = _two_blob_features()
    out = scan_k(X, ks=[2, 3, 4])
    assert set(out.keys()) == {2, 3, 4}
    assert max(out, key=out.get) == 2  # the data is genuinely 2 clusters
