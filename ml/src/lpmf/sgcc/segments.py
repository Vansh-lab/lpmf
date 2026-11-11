"""K-means load-shape segments on real SGCC consumers (contrast with the
synthetic demo fleet in lpmf.engines.theft_segments: same method, real
FOREIGN data this time). Clustering runs on the engineered features
(sgcc.features), standardised, fit on train only; val/test consumers are
assigned with the same fitted scaler and centroids, never used to refit
either.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

RNG_SEED = 20261111
# silhouette_score computes a full pairwise-distance matrix: on the ~30k-row
# train split that is an O(n^2) array too large to allocate (confirmed:
# crashes with a ~1 GiB chunk allocation error). sample_size makes it an
# estimate on a random subset instead, which is standard practice at this
# scale and still gives an honest, comparable-across-k number.
SILHOUETTE_SAMPLE_SIZE = 5000


def fit_segments(X_train: pd.DataFrame, n_clusters: int = 4) -> tuple[KMeans, StandardScaler]:
    scaler = StandardScaler().fit(X_train)
    model = KMeans(n_clusters=n_clusters, n_init=10, random_state=RNG_SEED)
    model.fit(scaler.transform(X_train))
    return model, scaler


def assign_segments(
    model: KMeans, scaler: StandardScaler, X: pd.DataFrame
) -> tuple[np.ndarray, float]:
    """Cluster labels for `X` under the already-fitted model/scaler, plus
    this X's own silhouette score (computed on X, so val/test get an
    honest score under centroids they never influenced)."""
    scaled = scaler.transform(X)
    labels = model.predict(scaled)
    sample_size = min(SILHOUETTE_SAMPLE_SIZE, scaled.shape[0] - 1)
    score = (
        float(silhouette_score(scaled, labels, sample_size=sample_size, random_state=RNG_SEED))
        if len(set(labels)) > 1
        else float("nan")
    )
    return labels, score


def scan_k(X_train: pd.DataFrame, ks: list[int]) -> dict[int, float]:
    """Silhouette score on train for each candidate k, to justify the
    chosen n_clusters rather than picking it arbitrarily."""
    scaler = StandardScaler().fit(X_train)
    scaled = scaler.transform(X_train)
    sample_size = min(SILHOUETTE_SAMPLE_SIZE, scaled.shape[0] - 1)
    out = {}
    for k in ks:
        model = KMeans(n_clusters=k, n_init=10, random_state=RNG_SEED)
        labels = model.fit_predict(scaled)
        out[k] = float(
            silhouette_score(scaled, labels, sample_size=sample_size, random_state=RNG_SEED)
        )
    return out
