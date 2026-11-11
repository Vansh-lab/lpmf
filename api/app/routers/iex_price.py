"""IEX Price page (07): an illustrative day-ahead price curve (cheap midday,
costly evening) and the power-purchase cost it implies against the real
day-ahead load forecast.

IEX's own DAM market-snapshot page (iexindia.com/market-data/day-ahead-
market/market-snapshot) is a client-rendered app; a direct fetch returns
only the page shell with no embedded data or discoverable public API, so
this page is ILLUSTRATIVE rather than live IEX data. To make it real: hand-
download the DAM CSV from that page's "Reports" / export control (date
range picker, then whatever export option it currently offers — it was not
reachable programmatically when this was checked) for the days you want,
save as data/raw/iex/dam_<date>.csv, and replace `_illustrative_price` in
this router with a reader for that file.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from lpmf.engines.iex_price import (
    EAC_PM_PRICE_RANGE,
    illustrative_hourly_price_per_mwh,
    load_real_price_profile,
    purchase_cost,
)

from app.config import settings
from app.data import SOURCE_FORECAST, forecast_dates, forecast_day
from app.schemas import IexBlock, IexPriceRange, IexPriceResponse, RealPriceProfileInfo

router = APIRouter()

IEX_ARTIFACTS_DIR = settings.repo_root / "models" / "artifacts" / "iex"

MANUAL_DOWNLOAD_NOTE = (
    "Real IEX DAM prices were not reachable programmatically (client-rendered page, no public "
    "API found). To use real prices: download the DAM CSV for the dates you need from "
    "https://iexindia.com/market-data/day-ahead-market/market-snapshot, save it under "
    "data/raw/iex/, and wire it into this endpoint in place of the illustrative curve."
)


@router.get("", response_model=IexPriceResponse)
def iex_price(
    day: Annotated[
        date | None, Query(alias="date", description="Test-set day; default latest.")
    ] = None,
    min_price_per_mwh: Annotated[float, Query(ge=0, allow_inf_nan=False)] = EAC_PM_PRICE_RANGE[
        "midday_price_per_unit"
    ]
    * 1000,
    max_price_per_mwh: Annotated[float, Query(ge=0, allow_inf_nan=False)] = EAC_PM_PRICE_RANGE[
        "night_price_per_unit"
    ]
    * 1000,
    expensive_hour: Annotated[int, Query(ge=0, le=23)] = 20,
) -> IexPriceResponse:
    if max_price_per_mwh < min_price_per_mwh:
        raise HTTPException(
            422,
            f"max_price_per_mwh ({max_price_per_mwh}) must be >= "
            f"min_price_per_mwh ({min_price_per_mwh}).",
        )
    rows = forecast_day(day)
    if rows is None:
        dates = forecast_dates()
        raise HTTPException(
            404, f"No day-ahead forecast for {day}; test days run {dates[0]} to {dates[-1]}."
        )

    real_profile = load_real_price_profile(IEX_ARTIFACTS_DIR)
    using_real = real_profile is not None

    try:
        if using_real:
            hourly_price = real_profile["hourly_profile_per_mwh"]
        else:
            hourly_price = illustrative_hourly_price_per_mwh(
                min_price_per_mwh, max_price_per_mwh, expensive_hour
            )
        price_by_block = [hourly_price[ts.hour] for ts in rows["ts_target"]]
        out = purchase_cost(rows["predicted_mw"].to_numpy(), price_by_block)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

    threshold = sorted(hourly_price)[int(0.75 * (len(hourly_price) - 1))]
    blocks = [
        IexBlock(
            block=i + 1,
            ts_target=ts,
            load_mw=round(float(load), 1),
            price_per_mwh=round(price, 1),
            cost_rupees=round(cost, 1),
            is_expensive=price >= threshold,
        )
        for i, (ts, load, price, cost) in enumerate(
            zip(
                rows["ts_target"],
                rows["predicted_mw"],
                price_by_block,
                out["cost_per_block_rupees"],
            )
        )
    ]

    return IexPriceResponse(
        date=rows["date"].iloc[0],
        issued_at=rows["ts_origin"].iloc[0],
        min_price_per_mwh=min(hourly_price) if using_real else min_price_per_mwh,
        max_price_per_mwh=max(hourly_price) if using_real else max_price_per_mwh,
        expensive_hour=expensive_hour,
        blocks=blocks,
        total_cost_rupees=out["total_cost_rupees"],
        is_illustrative=not using_real,
        manual_download_note=None if using_real else MANUAL_DOWNLOAD_NOTE,
        price_range_benchmark=IexPriceRange(**EAC_PM_PRICE_RANGE),
        real_price_profile=RealPriceProfileInfo(**real_profile) if using_real else None,
        provenance=real_profile["provenance"] if using_real else out["provenance"],
        source=(
            f"{SOURCE_FORECAST}; real historical IEX DAM block-of-day average price"
            if using_real
            else f"{SOURCE_FORECAST}; illustrative price curve (IEX DAM not reachable)"
        ),
    )
