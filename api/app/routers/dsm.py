"""DSM ₹ Calculator page (05): illustrative deviation charge.

Defaults reproduce the deck's worked example: 60 MW deviation held for an hour
(4 blocks) against a 41 MW limit at ₹5,000/MWh, k = 1.5 -> ₹3,47,500.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from lpmf.engines.dsm import dsm_penalty

from app.schemas import DsmResponse

router = APIRouter()

NonNegative = Query(ge=0, allow_inf_nan=False)


@router.get("", response_model=DsmResponse)
def dsm(
    deviation_mw: Annotated[
        float, Query(allow_inf_nan=False, description="Per 15-min block, ±.")
    ] = 60.0,
    schedule_limit_mw: Annotated[float, NonNegative] = 41.0,
    normal_rate_per_mwh: Annotated[float, NonNegative] = 5000.0,
    excess_multiplier: Annotated[float, NonNegative] = 1.5,
    blocks: Annotated[
        int, Query(ge=1, le=96, description="Blocks the deviation lasts (4 = 1 hour).")
    ] = 4,
) -> DsmResponse:
    try:
        out = dsm_penalty(
            [deviation_mw] * blocks, normal_rate_per_mwh, schedule_limit_mw, excess_multiplier
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    return DsmResponse(
        deviation_mw=deviation_mw,
        schedule_limit_mw=schedule_limit_mw,
        normal_rate_per_mwh=normal_rate_per_mwh,
        excess_multiplier=excess_multiplier,
        n_blocks=out["n_blocks"],
        penalty_rupees=out["penalty_rupees"],
        per_block_rupees=out["per_block_rupees"],
        is_illustrative=out["is_illustrative"],
        note=out["note"],
        provenance=out["provenance"],
        source="Illustrative DSM formula (CERC DSM Regulations 2024 structure)",
    )
