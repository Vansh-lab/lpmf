"""Load Analytics page (02): load factor, PAR and the load-duration curve of
the real SLDC load, over the whole series or a date range."""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from lpmf.engines.load_analytics import load_factor_and_par

from app.data import SOURCE_SLDC, fifteen_min, ldc_points
from app.schemas import AnalyticsResponse, LdcPoint

router = APIRouter()


@router.get("", response_model=AnalyticsResponse)
def analytics(
    start: Annotated[
        date | None, Query(description="First day (inclusive); default series start.")
    ] = None,
    end: Annotated[
        date | None, Query(description="Last day (inclusive); default series end.")
    ] = None,
    points: Annotated[
        int, Query(ge=2, le=1001, description="LDC points returned for charting.")
    ] = 101,
) -> AnalyticsResponse:
    return _analytics(start, end, points)


# Cached per (start, end, points): the full-series sort runs once, not per request.
@lru_cache(maxsize=64)
def _analytics(start: date | None, end: date | None, points: int) -> AnalyticsResponse:
    df = fifteen_min()
    start = start or df["date"].min()
    end = end or df["date"].max()
    if start > end:
        raise HTTPException(422, f"start ({start}) is after end ({end}).")
    load = df.loc[(df["date"] >= start) & (df["date"] <= end), "load_mw"]
    if load.notna().sum() == 0:
        raise HTTPException(404, f"No load data between {start} and {end}.")

    out = load_factor_and_par(load)
    ldc = out["load_duration_curve"]["load_mw"]
    return AnalyticsResponse(
        start=start,
        end=end,
        load_factor=out["load_factor"],
        par=out["par"],
        p_avg_mw=out["p_avg_mw"],
        p_max_mw=out["p_max_mw"],
        n_blocks=out["n_values"],
        load_duration_curve=[LdcPoint(rank_pct=p, load_mw=v) for p, v in ldc_points(ldc, points)],
        provenance=out["provenance"],
        source=SOURCE_SLDC,
    )
