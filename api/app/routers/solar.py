"""Solar & Net Load page (09): rooftop solar output modelled from real
Open-Meteo irradiance (same day the Forecast page shows), and the
resulting net load (duck curve). Solar capacity is a what-if slider,
defaulting to the public Delhi rooftop estimate.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from lpmf.engines.solar import (
    DEFAULT_PERFORMANCE_RATIO,
    DELHI_ROOFTOP_CAPACITY_MWP,
    load_real_plant_validation,
    net_load_mw,
    solar_output_mw,
)

from app.config import settings
from app.data import SOURCE_FORECAST, fifteen_min, forecast_dates, forecast_day
from app.schemas import SolarBlock, SolarCapacityBenchmark, SolarRealPlantValidation, SolarResponse

router = APIRouter()

SOLAR_ARTIFACTS_DIR = settings.repo_root / "models" / "artifacts" / "solar"


@router.get("", response_model=SolarResponse)
def solar(
    day: Annotated[
        date | None, Query(alias="date", description="Test-set day; default latest.")
    ] = None,
    capacity_mwp: Annotated[
        float, Query(ge=0, allow_inf_nan=False, description="Rooftop fleet capacity, MWp.")
    ] = DELHI_ROOFTOP_CAPACITY_MWP["capacity_mwp"],
    performance_ratio: Annotated[
        float, Query(gt=0, le=1, allow_inf_nan=False)
    ] = DEFAULT_PERFORMANCE_RATIO,
) -> SolarResponse:
    rows = forecast_day(day)
    if rows is None:
        dates = forecast_dates()
        raise HTTPException(
            404, f"No day-ahead forecast for {day}; test days run {dates[0]} to {dates[-1]}."
        )

    ghi = fifteen_min().set_index("ts_ist")["ghi_wm2"]
    ghi_values = ghi.reindex(rows["ts_target"].to_numpy())
    if ghi_values.isna().any():
        raise HTTPException(503, "GHI data missing for part of this forecast day.")

    try:
        solar_mw = solar_output_mw(ghi_values.to_numpy(), capacity_mwp, performance_ratio)[
            "output_mw"
        ]
        net_mw = net_load_mw(rows["predicted_mw"].to_numpy(), solar_mw)["net_load_mw"]
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

    blocks = [
        SolarBlock(
            block=i + 1,
            ts_target=ts,
            load_mw=round(float(load), 1),
            ghi_wm2=round(float(g), 1),
            solar_mw=round(float(s), 2),
            net_load_mw=round(float(n), 1),
        )
        for i, (ts, load, g, s, n) in enumerate(
            zip(rows["ts_target"], rows["predicted_mw"], ghi_values, solar_mw, net_mw)
        )
    ]
    midday = [b for b in blocks if 10 <= b.ts_target.hour <= 15]
    evening = [b for b in blocks if 18 <= b.ts_target.hour <= 21]
    midday_trough = min((b.net_load_mw for b in midday), default=min(b.net_load_mw for b in blocks))
    evening_peak = max((b.net_load_mw for b in evening), default=max(b.net_load_mw for b in blocks))

    return SolarResponse(
        date=rows["date"].iloc[0],
        issued_at=rows["ts_origin"].iloc[0],
        capacity_mwp=capacity_mwp,
        performance_ratio=performance_ratio,
        blocks=blocks,
        peak_load_mw=round(float(rows["predicted_mw"].max()), 1),
        peak_net_load_mw=round(max(b.net_load_mw for b in blocks), 1),
        midday_solar_peak_mw=round(max(b.solar_mw for b in blocks), 2),
        evening_ramp_mw=round(evening_peak - midday_trough, 1),
        capacity_benchmark=SolarCapacityBenchmark(**DELHI_ROOFTOP_CAPACITY_MWP),
        real_plant_validation=(
            SolarRealPlantValidation(**validation)
            if (validation := load_real_plant_validation(SOLAR_ARTIFACTS_DIR))
            else None
        ),
        provenance="MODELLED",
        source=f"{SOURCE_FORECAST}; Open-Meteo GHI; modelled solar (PR={performance_ratio})",
    )
