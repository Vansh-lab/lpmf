"""LPMF FastAPI application entry point.

Run with:
    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import analytics, dsm, forecast, overview, transformer, weather

app = FastAPI(title=settings.app_name)

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
