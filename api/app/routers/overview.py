"""Overview page (01): the day-ahead forecast's peak and the overload alert."""

from __future__ import annotations

from datetime import date
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from lpmf.engines.overview import peak_and_alert

from app.config import settings
from app.data import SOURCE_FORECAST, forecast_dates, forecast_day
from app.schemas import OverviewResponse

router = APIRouter()


@router.get("", response_model=OverviewResponse)
def overview(
    day: Annotated[
        date | None, Query(alias="date", description="Test-set day; default latest.")
    ] = None,
    limit_mw: Annotated[
        float,
        Query(
            gt=0,
            allow_inf_nan=False,
            description="Alert threshold; default Delhi's all-time peak (8,748 MW).",
        ),
    ] = settings.overview_alert_limit_mw,
) -> OverviewResponse:
    rows = forecast_day(day)
    if rows is None:
        dates = forecast_dates()
        raise HTTPException(
            404, f"No day-ahead forecast for {day}; test days run " f"{dates[0]} to {dates[-1]}."
        )
    out = peak_and_alert(
        pd.Series(rows["predicted_mw"].to_numpy(), index=pd.DatetimeIndex(rows["ts_target"])),
        limit_mw,
    )
    return OverviewResponse(
        date=rows["date"].iloc[0],
        issued_at=rows["ts_origin"].iloc[0],
        peak_mw=out["peak_mw"],
        peak_time=out["peak_time"],
        peak_block=out["peak_block"],
        limit_mw=out["limit_mw"],
        alert=out["alert"],
        provenance=out["provenance"],
        source=SOURCE_FORECAST,
    )
