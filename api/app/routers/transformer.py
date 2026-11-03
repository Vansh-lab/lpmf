"""Transformer Health page (06): IEC 60076-7 insulation ageing for a hot-spot
temperature. The temperature is a what-if input, not a measurement, so the
result is tagged ILLUSTRATIVE."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Query
from lpmf.engines.transformer import transformer_ageing
from lpmf.provenance import ProvenanceKind

from app.schemas import TransformerResponse

router = APIRouter()


@router.get("", response_model=TransformerResponse)
def transformer(
    hotspot_temp_c: Annotated[
        float,
        Query(
            ge=-50,
            le=250,
            allow_inf_nan=False,
            description="Winding hot-spot temperature; default = the deck's 40 °C full-load case.",
        ),
    ] = 118.0,
    hours: Annotated[
        float, Query(gt=0, le=8760, allow_inf_nan=False, description="Hours held.")
    ] = 1.0,
) -> TransformerResponse:
    out = transformer_ageing(
        hotspot_temp_c, hours_per_step=hours, provenance=ProvenanceKind.ILLUSTRATIVE
    )
    return TransformerResponse(
        hotspot_temp_c=hotspot_temp_c,
        hours=hours,
        ageing_rate_v=out["ageing_rate_v"],
        life_hours_used=out["life_hours_used"],
        hours_elapsed=out["hours_elapsed"],
        provenance=out["provenance"],
        source="What-if hot-spot temperature, IEC 60076-7:2018 ageing model",
    )
