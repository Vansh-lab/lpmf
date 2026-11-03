"""Weather Impact page (03): heat sensitivity β of the real load.

β is the OLS fit over every 15-min block (the method docs/DATA_QUALITY.md
reports). The scatter is one point per day (daily means of load and heat
index) — ~1,000 points instead of ~96,000 blocks. Means of a linear fit's
inputs lie around the same line, so the fitted line can be drawn over them.
"""

from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter
from lpmf.engines.weather import heat_sensitivity

from app.data import SOURCE_SLDC, fifteen_min
from app.schemas import ScatterPoint, WeatherResponse

router = APIRouter()


@router.get("", response_model=WeatherResponse)
def weather() -> WeatherResponse:
    return _weather()


@lru_cache(maxsize=1)
def _weather() -> WeatherResponse:
    df = fifteen_min()
    fit = heat_sensitivity(df["load_mw"], df["heat_index_c"])
    daily = (
        df.dropna(subset=["load_mw", "heat_index_c"])
        .groupby("date")[["heat_index_c", "load_mw"]]
        .mean()
    )
    return WeatherResponse(
        beta_mw_per_c=fit["beta_mw_per_c"],
        intercept_mw=fit["intercept_mw"],
        r_squared=fit["r_squared"],
        n_blocks=fit["n_rows"],
        scatter_granularity="daily_mean",
        scatter=[
            ScatterPoint(date=d, heat_index_c=round(h, 2), load_mw=round(v, 1))
            for d, h, v in zip(daily.index, daily["heat_index_c"], daily["load_mw"])
        ],
        provenance=fit["provenance"],
        source=SOURCE_SLDC,
    )
