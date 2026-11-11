"""theft_segments: synthetic fleet generation, anomaly ranking, clustering."""

from __future__ import annotations

import numpy as np
import pytest

from lpmf.engines.theft_segments import (
    generate_synthetic_meters,
    rank_suspicious_meters,
    segment_load_shapes,
)
from lpmf.provenance import ProvenanceKind


def test_generate_synthetic_meters_is_reproducible():
    a = generate_synthetic_meters(n_meters=20, n_theft=3, seed=1)
    b = generate_synthetic_meters(n_meters=20, n_theft=3, seed=1)
    assert np.allclose(a.hourly_kwh, b.hourly_kwh)
    assert a.is_theft.tolist() == b.is_theft.tolist()


def test_generate_synthetic_meters_shapes_and_theft_count():
    fleet = generate_synthetic_meters(n_meters=30, n_theft=5)
    assert fleet.hourly_kwh.shape == (30, 24)
    assert len(fleet.meter_ids) == 30
    assert fleet.is_theft.sum() == 5
    assert (fleet.hourly_kwh >= 0).all()


def test_generate_synthetic_meters_rejects_bad_counts():
    with pytest.raises(ValueError):
        generate_synthetic_meters(n_meters=0)
    with pytest.raises(ValueError):
        generate_synthetic_meters(n_meters=10, n_theft=11)


def test_rank_suspicious_meters_scores_theft_meters_as_more_anomalous_on_average():
    # Not a hard per-meter guarantee (it's an unsupervised model on noisy
    # synthetic data), but the theft meters' MEAN score should be clearly
    # lower (more anomalous) than the honest meters' mean score.
    fleet = generate_synthetic_meters(n_meters=60, n_theft=6, seed=7)
    out = rank_suspicious_meters(fleet, contamination=0.1)
    scores = {r["meter_id"]: r["anomaly_score"] for r in out["ranking"]}
    theft_scores = [
        scores[mid] for mid, t in zip(fleet.meter_ids, fleet.is_theft, strict=True) if t
    ]
    honest_scores = [
        scores[mid] for mid, t in zip(fleet.meter_ids, fleet.is_theft, strict=True) if not t
    ]
    assert np.mean(theft_scores) < np.mean(honest_scores)
    assert out["provenance"] == ProvenanceKind.SYNTHETIC
    assert 0.0 <= out["precision_at_k"] <= 1.0
    assert out["k"] == 6


def test_rank_suspicious_meters_ranking_is_sorted_most_anomalous_first():
    fleet = generate_synthetic_meters(n_meters=40, n_theft=4, seed=3)
    out = rank_suspicious_meters(fleet)
    scores = [r["anomaly_score"] for r in out["ranking"]]
    assert scores == sorted(scores)


def test_rank_suspicious_meters_rejects_bad_contamination():
    fleet = generate_synthetic_meters(n_meters=20, n_theft=2)
    with pytest.raises(ValueError):
        rank_suspicious_meters(fleet, contamination=0.0)
    with pytest.raises(ValueError):
        rank_suspicious_meters(fleet, contamination=0.6)


def test_segment_load_shapes_groups_by_shape_not_scale():
    fleet = generate_synthetic_meters(n_meters=40, n_theft=0, seed=5)
    out = segment_load_shapes(fleet, n_clusters=4)
    assert len(out["labels"]) == 40
    assert len(out["clusters"]) == 4
    assert sum(c["n_meters"] for c in out["clusters"]) == 40
    for c in out["clusters"]:
        assert pytest.approx(sum(c["mean_shape_pct"]), abs=0.5) == 100.0
    assert out["provenance"] == ProvenanceKind.SYNTHETIC


def test_segment_load_shapes_rejects_too_many_clusters():
    fleet = generate_synthetic_meters(n_meters=5, n_theft=0)
    with pytest.raises(ValueError):
        segment_load_shapes(fleet, n_clusters=6)
    with pytest.raises(ValueError):
        segment_load_shapes(fleet, n_clusters=0)
