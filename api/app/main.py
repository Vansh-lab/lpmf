"""LPMF FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import data
from app.config import settings
from app.data import DataNotBuilt
from app.routers import (
    analytics,
    dsm,
    forecast,
    iex_price,
    losses,
    overview,
    solar,
    tod_bill,
    transformer,
    weather,
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Reading the 1.7M-row conformal bands file takes ~1.5 s; do it (and the
    # other cached reads) at startup rather than in the first request.
    try:
        data.day_ahead_forecasts()
        data.conformal_summary()
        weather._weather()
        analytics._analytics(None, None, 101)
    except DataNotBuilt as exc:
        logger.warning("Starting with cold caches: %s", exc)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.exception_handler(DataNotBuilt)
def data_not_built(_: Request, exc: DataNotBuilt) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(exc)})


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "environment": settings.environment}


app.include_router(overview.router, prefix="/overview", tags=["overview"])
app.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
app.include_router(weather.router, prefix="/weather", tags=["weather"])
app.include_router(forecast.router, prefix="/forecast", tags=["forecast"])
app.include_router(dsm.router, prefix="/dsm", tags=["dsm"])
app.include_router(transformer.router, prefix="/transformer", tags=["transformer"])
app.include_router(losses.router, prefix="/losses", tags=["losses"])
app.include_router(tod_bill.router, prefix="/tod", tags=["tod"])
app.include_router(solar.router, prefix="/solar", tags=["solar"])
app.include_router(iex_price.router, prefix="/iex", tags=["iex"])
