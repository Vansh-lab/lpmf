"""Forecast page (04): a test day's 96-block day-ahead forecast, its
split-conformal P10-P90 band and, where precomputed, the day's top TreeSHAP
contributors."""

from __future__ import annotations

from datetime import date
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from lpmf.provenance import ProvenanceKind

from app.data import (
    SOURCE_FORECAST,
    conformal_summary,
    forecast_dates,
    forecast_day,
    shap_days,
    shap_matrix,
)
from app.schemas import (
    BandInfo,
    ForecastBlock,
    ForecastDatesResponse,
    ForecastResponse,
    ShapContributor,
    ShapSummary,
)

router = APIRouter()

TOP_SHAP = 5
_NOT_FEATURES = {"block_horizon", "base_value", "predicted_mw", "actual_mw"}


@router.get("/dates", response_model=ForecastDatesResponse)
def available_dates() -> ForecastDatesResponse:
    return ForecastDatesResponse(
        dates=forecast_dates(),
        shap_dates={label: day for day, label in shap_days().items()},
    )


@router.get("", response_model=ForecastResponse)
def forecast(
    day: Annotated[
        date | None, Query(alias="date", description="Test-set day; default latest.")
    ] = None,
) -> ForecastResponse:
    rows = forecast_day(day)
    if rows is None:
        dates = forecast_dates()
        raise HTTPException(
            404,
            f"No day-ahead forecast for {day}; test days run "
            f"{dates[0]} to {dates[-1]} (see /forecast/dates).",
        )
    summary = conformal_summary()
    the_day = rows["date"].iloc[0]
    return ForecastResponse(
        date=the_day,
        issued_at=rows["ts_origin"].iloc[0],
        blocks=[
            ForecastBlock(
                block=int(r.horizon),
                ts_target=r.ts_target,
                predicted_mw=round(r.predicted_mw, 1),
                p10_mw=round(r.lower_mw, 1),
                p90_mw=round(r.upper_mw, 1),
                actual_mw=None if pd.isna(r.actual_mw) else round(float(r.actual_mw), 1),
            )
            for r in rows.itertuples(index=False)
        ],
        band=BandInfo(
            method="split-conformal (MAPIE), absolute score, calibrated on val",
            confidence_level=summary["confidence_level"],
            empirical_test_coverage=summary["absolute"]["overall"],
        ),
        shap=_shap_summary(the_day),
        provenance=ProvenanceKind.REAL,
        source=SOURCE_FORECAST,
    )


def _shap_summary(day: date) -> ShapSummary | None:
    label = shap_days().get(day)
    if label is None:
        return None
    sv = shap_matrix(label)
    features = sv[[c for c in sv.columns if c not in _NOT_FEATURES]]
    mean_abs = features.abs().mean().sort_values(ascending=False).head(TOP_SHAP)
    signed = features.mean()
    return ShapSummary(
        day_label=label,
        top_contributors=[
            ShapContributor(
                feature=f, mean_abs_shap_mw=round(v, 1), mean_shap_mw=round(signed[f], 1)
            )
            for f, v in mean_abs.items()
        ],
    )
