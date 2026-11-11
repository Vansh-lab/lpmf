"""Theft & Segments page (11): demo on a SYNTHETIC smart-meter fleet — no
public, consumer-level Delhi meter data exists. Isolation Forest ranks
suspicious meters; K-means groups meters by load shape. Nothing here is a
real consumer or a real theft finding.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from lpmf.engines.theft_segments import (
    generate_synthetic_meters,
    rank_suspicious_meters,
    segment_load_shapes,
)

from app.schemas import MeterCluster, SuspiciousMeter, TheftSegmentsResponse

router = APIRouter()

SOURCE = "Synthetic smart-meter fleet (lpmf.engines.theft_segments) — a demo, not real consumers"


@lru_cache(maxsize=16)
def _fleet(n_meters: int, n_theft: int):
    return generate_synthetic_meters(n_meters=n_meters, n_theft=n_theft)


@router.get("", response_model=TheftSegmentsResponse)
def theft_segments(
    n_meters: Annotated[int, Query(ge=5, le=500)] = 60,
    n_theft: Annotated[int, Query(ge=0, le=50)] = 6,
    n_clusters: Annotated[int, Query(ge=1, le=10)] = 3,
    contamination: Annotated[float, Query(gt=0, lt=0.5)] = 0.1,
) -> TheftSegmentsResponse:
    if n_theft > n_meters:
        raise HTTPException(422, f"n_theft ({n_theft}) cannot exceed n_meters ({n_meters}).")
    if n_clusters > n_meters:
        raise HTTPException(422, f"n_clusters ({n_clusters}) cannot exceed n_meters ({n_meters}).")

    fleet = _fleet(n_meters, n_theft)
    try:
        ranked = rank_suspicious_meters(fleet, contamination=contamination)
        segmented = segment_load_shapes(fleet, n_clusters=n_clusters)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

    return TheftSegmentsResponse(
        n_meters=n_meters,
        n_theft_ground_truth=n_theft,
        precision_at_k=ranked["precision_at_k"],
        k=ranked["k"],
        ranking=[SuspiciousMeter(**r) for r in ranked["ranking"]],
        clusters=[MeterCluster(**c) for c in segmented["clusters"]],
        is_synthetic=True,
        provenance=ranked["provenance"],
        source=SOURCE,
    )
