"""Losses & PF page (10): illustrative PF-correction kVAR and I²R feeder loss,
alongside one REAL benchmark (national AT&C loss) for context.

PF, current and resistance are what-if inputs (ILLUSTRATIVE), not a reading
from a real feeder.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from lpmf.engines.losses import (
    AT_C_BENCHMARK,
    DISCOM_AT_C_FY2023_24,
    current_after_pf_correction,
    i2r_loss,
    loss_reduction_pct,
    pf_correction,
)

from app.schemas import AtcBenchmark, DiscomAtcBenchmark, LossesResponse

router = APIRouter()

NonNegative = Query(ge=0, allow_inf_nan=False)
UnityPf = Query(gt=0, le=1, allow_inf_nan=False)


@router.get("", response_model=LossesResponse)
def losses(
    # Clean illustrative defaults, not the deck's "844 kVAR" example: that
    # example's P was never published, so it can't be reproduced exactly
    # (same approach test_engine_dsm.py already took for its own example).
    active_power_kw: Annotated[float, NonNegative] = 1000.0,
    pf1: Annotated[float, UnityPf] = 0.75,
    pf2: Annotated[float, UnityPf] = 0.95,
    current_a: Annotated[float, NonNegative] = 300.0,
    resistance_ohm: Annotated[float, NonNegative] = 0.1,
) -> LossesResponse:
    try:
        pf_out = pf_correction(active_power_kw, pf1, pf2)
        current_reduced = current_after_pf_correction(current_a, pf1, pf2)
        loss_out = i2r_loss(current_a, resistance_ohm)
        reduction = loss_reduction_pct(current_a, resistance_ohm, current_reduced)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

    return LossesResponse(
        active_power_kw=active_power_kw,
        pf1=pf1,
        pf2=pf2,
        capacitor_kvar=pf_out["capacitor_kvar"],
        current_a=current_a,
        resistance_ohm=resistance_ohm,
        loss_kw=loss_out["loss_kw"],
        loss_reduction_pct=reduction,
        is_illustrative=True,
        at_c_benchmark=AtcBenchmark(**AT_C_BENCHMARK),
        discom_at_c_benchmark=DiscomAtcBenchmark(**DISCOM_AT_C_FY2023_24),
        provenance=pf_out["provenance"],
        source="Illustrative PF-correction/I²R what-if (V.K. Mehta, Ch. 6)",
    )
