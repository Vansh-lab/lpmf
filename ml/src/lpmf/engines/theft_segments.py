"""Theft & Segments page engine: SYNTHETIC smart-meter profiles (no public,
consumer-level Delhi meter data exists), Isolation Forest to rank
suspicious meters, and K-means to group meters by load shape.

Everything here is a demo on generated data, never real consumers. Every
meter's 24-hour profile is a noisy, scaled version of one of four category
shapes (residential/commercial/industrial/agricultural — the same shapes
lpmf.synthetic.generate uses for the aggregate stand-in), with a handful
of meters given a theft-like anomaly (a sustained, unexplained energy
drop, as if part of the load were being diverted around the meter).

Ref: Liu, Ting & Zhou, "Isolation Forest", ICDM 2008 (anomaly ranking);
scikit-learn KMeans (load-shape segments).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from lpmf.provenance import ProvenanceKind

HOURS_PER_DAY = 24
RNG_SEED = 20261111  # fixed: the demo fleet is reproducible, not re-rolled each run

# (peak_hour, peak_width, base_kwh, peak_kwh) — rough, illustrative shapes,
# not fitted to any real category data.
CATEGORY_SHAPES: dict[str, tuple[float, float, float, float]] = {
    "residential": (20.0, 3.0, 0.3, 1.2),
    "commercial": (14.0, 5.0, 0.2, 1.0),
    "industrial": (12.0, 8.0, 0.6, 0.9),
    "agricultural": (4.0, 2.0, 0.1, 0.8),
}


def _category_profile(peak_hour: float, width: float, base: float, peak: float) -> np.ndarray:
    hours = np.arange(HOURS_PER_DAY)
    # Wrapped Gaussian bump on a 24h clock (so a peak near midnight is not
    # artificially cut off at the 0h/24h boundary).
    delta = np.minimum(np.abs(hours - peak_hour), HOURS_PER_DAY - np.abs(hours - peak_hour))
    return base + peak * np.exp(-0.5 * (delta / width) ** 2)


@dataclass(frozen=True)
class SyntheticFleet:
    meter_ids: list[str]
    categories: list[str]
    is_theft: np.ndarray  # bool, ground truth (never shown as a "detection")
    hourly_kwh: np.ndarray  # (n_meters, 24)


def generate_synthetic_meters(
    n_meters: int = 60, n_theft: int = 6, noise_sd: float = 0.08, seed: int = RNG_SEED
) -> SyntheticFleet:
    """A fleet of `n_meters` synthetic 24h profiles, `n_theft` of them
    carrying a theft-like sustained energy drop. SYNTHETIC end to end —
    no real meter contributes anything here."""
    if n_meters < 1:
        raise ValueError(f"n_meters must be >= 1, got {n_meters}.")
    if not (0 <= n_theft <= n_meters):
        raise ValueError(f"n_theft must be in [0, n_meters], got {n_theft}.")
    rng = np.random.default_rng(seed)
    categories = list(CATEGORY_SHAPES)

    meter_ids, cats, profiles = [], [], []
    for i in range(n_meters):
        cat = categories[i % len(categories)]
        peak_hour, width, base, peak = CATEGORY_SHAPES[cat]
        scale = rng.uniform(0.7, 1.3)
        profile = _category_profile(peak_hour, width, base, peak) * scale
        profile = profile * (1.0 + rng.normal(0, noise_sd, HOURS_PER_DAY))
        meter_ids.append(f"M{i + 1:03d}")
        cats.append(cat)
        profiles.append(np.clip(profile, 0.0, None))

    is_theft = np.zeros(n_meters, dtype=bool)
    theft_idx = rng.choice(n_meters, size=n_theft, replace=False)
    for idx in theft_idx:
        # A theft-like signature: energy under-reported by 30-60% across
        # most hours (as if load were diverted around the meter), not a
        # full blackout (which would look like an outage, not theft).
        drop = rng.uniform(0.3, 0.6)
        profiles[idx] = profiles[idx] * (1.0 - drop)
    is_theft[theft_idx] = True

    return SyntheticFleet(
        meter_ids=meter_ids,
        categories=cats,
        is_theft=is_theft,
        hourly_kwh=np.vstack(profiles),
    )


def _meter_features(hourly_kwh: np.ndarray) -> np.ndarray:
    """Simple per-meter features for anomaly detection: daily total, the
    load-factor-like ratio, and night/day energy split — a theft-like drop
    changes the total without changing the shape much, which these catch."""
    total = hourly_kwh.sum(axis=1)
    peak = hourly_kwh.max(axis=1)
    mean = hourly_kwh.mean(axis=1)
    load_factor = np.divide(mean, peak, out=np.zeros_like(mean), where=peak > 0)
    night = hourly_kwh[:, list(range(0, 6)) + list(range(22, 24))].mean(axis=1)
    day = hourly_kwh[:, 6:22].mean(axis=1)
    night_day_ratio = np.divide(night, day, out=np.zeros_like(night), where=day > 0)
    return np.column_stack([total, load_factor, night_day_ratio])


def rank_suspicious_meters(fleet: SyntheticFleet, contamination: float = 0.1) -> dict:
    """Isolation Forest anomaly score per meter (more negative = more
    anomalous); returns meters ranked most-suspicious first, plus
    precision@k against the (synthetic) ground-truth theft flags — for
    diagnosing the demo, never shown as if it worked on real consumers."""
    if not (0 < contamination < 0.5):
        raise ValueError(f"contamination must be in (0, 0.5), got {contamination}.")
    features = _meter_features(fleet.hourly_kwh)
    scaled = StandardScaler().fit_transform(features)
    model = IsolationForest(n_estimators=200, contamination=contamination, random_state=RNG_SEED)
    model.fit(scaled)
    scores = model.score_samples(scaled)  # higher = more normal
    order = np.argsort(scores)  # most anomalous first

    k = max(1, int(round(fleet.is_theft.sum())))
    top_k = order[:k]
    precision_at_k = float(fleet.is_theft[top_k].mean()) if k else 0.0

    return {
        "ranking": [
            {
                "meter_id": fleet.meter_ids[i],
                "category": fleet.categories[i],
                "anomaly_score": float(scores[i]),
                "is_theft_ground_truth": bool(fleet.is_theft[i]),
            }
            for i in order
        ],
        "precision_at_k": precision_at_k,
        "k": k,
        "provenance": ProvenanceKind.SYNTHETIC,
    }


def segment_load_shapes(fleet: SyntheticFleet, n_clusters: int = 3) -> dict:
    """K-means on each meter's normalised (shape-only) daily profile, so
    clusters group by *when* a meter uses energy, not how much."""
    if n_clusters < 1:
        raise ValueError(f"n_clusters must be >= 1, got {n_clusters}.")
    if n_clusters > fleet.hourly_kwh.shape[0]:
        raise ValueError(
            f"n_clusters ({n_clusters}) cannot exceed the number of meters "
            f"({fleet.hourly_kwh.shape[0]})."
        )
    totals = fleet.hourly_kwh.sum(axis=1, keepdims=True)
    shapes = np.divide(
        fleet.hourly_kwh, totals, out=np.zeros_like(fleet.hourly_kwh), where=totals > 0
    )
    model = KMeans(n_clusters=n_clusters, n_init=10, random_state=RNG_SEED)
    labels = model.fit_predict(shapes)

    clusters = []
    for c in range(n_clusters):
        members = np.flatnonzero(labels == c)
        clusters.append(
            {
                "cluster": c,
                "n_meters": int(members.size),
                "mean_shape_pct": (model.cluster_centers_[c] * 100).round(2).tolist(),
                "meter_ids": [fleet.meter_ids[i] for i in members],
            }
        )
    return {
        "labels": labels.tolist(),
        "clusters": clusters,
        "provenance": ProvenanceKind.SYNTHETIC,
    }
