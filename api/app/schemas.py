"""Response models: the typed contract the web/ frontend codes against.

Every response carries `provenance` (a ProvenanceKind, straight from the
engine) and `source` (the human string a SourceBadge shows), per
docs/PROVENANCE.md.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from lpmf.provenance import ProvenanceKind
from pydantic import BaseModel, Field


class Tagged(BaseModel):
    provenance: ProvenanceKind
    source: str


class OverviewResponse(Tagged):
    date: date
    issued_at: datetime = Field(description="Forecast origin: 23:45 the evening before.")
    peak_mw: float
    peak_time: str = Field(description="Start of the peak 15-min block, HH:MM IST.")
    peak_block: int = Field(ge=1, le=96)
    limit_mw: float
    alert: bool = Field(description="True when peak_mw > limit_mw.")


class LdcPoint(BaseModel):
    rank_pct: float = Field(description="% of time the load is at or above load_mw.")
    load_mw: float


class AnalyticsResponse(Tagged):
    start: date
    end: date
    load_factor: float
    par: float
    p_avg_mw: float
    p_max_mw: float
    n_blocks: int
    load_duration_curve: list[LdcPoint]


class ScatterPoint(BaseModel):
    date: date
    heat_index_c: float
    load_mw: float


class WeatherResponse(Tagged):
    beta_mw_per_c: float
    intercept_mw: float
    r_squared: float
    n_blocks: int = Field(description="15-min blocks the OLS fit used.")
    scatter_granularity: Literal["daily_mean"]
    scatter: list[ScatterPoint]


class ForecastBlock(BaseModel):
    block: int = Field(ge=1, le=96)
    ts_target: datetime
    predicted_mw: float
    p10_mw: float
    p90_mw: float
    actual_mw: float | None


class BandInfo(BaseModel):
    method: str
    confidence_level: float
    empirical_test_coverage: float


class ShapContributor(BaseModel):
    feature: str
    mean_abs_shap_mw: float
    mean_shap_mw: float = Field(description="Signed: + pushes the forecast up.")


class ShapSummary(BaseModel):
    day_label: str
    top_contributors: list[ShapContributor]


class ForecastResponse(Tagged):
    date: date
    issued_at: datetime
    blocks: list[ForecastBlock]
    band: BandInfo
    shap: ShapSummary | None = Field(
        description="Only for days with a precomputed TreeSHAP explanation."
    )


class ForecastDatesResponse(BaseModel):
    dates: list[date]
    shap_dates: dict[str, date]


class DsmResponse(Tagged):
    deviation_mw: float
    schedule_limit_mw: float
    normal_rate_per_mwh: float
    excess_multiplier: float
    n_blocks: int
    penalty_rupees: float
    per_block_rupees: list[float]
    is_illustrative: Literal[True]
    note: str


class TransformerResponse(Tagged):
    hotspot_temp_c: float
    hours: float
    ageing_rate_v: float = Field(description="Relative ageing rate, 1.0 at 98 °C.")
    life_hours_used: float = Field(description="Equivalent hours of life at 98 °C.")
    hours_elapsed: float


class AtcBenchmark(BaseModel):
    at_c_loss_pct: float
    year: str
    note: str
    provenance: ProvenanceKind
    source: str


class LossesResponse(Tagged):
    active_power_kw: float
    pf1: float
    pf2: float
    capacitor_kvar: float
    current_a: float
    resistance_ohm: float
    loss_kw: float
    loss_reduction_pct: float
    is_illustrative: Literal[True]
    at_c_benchmark: AtcBenchmark
