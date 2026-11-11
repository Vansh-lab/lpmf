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


class TodRates(BaseModel):
    peak_surcharge_pct: float
    off_peak_rebate_pct: float
    order_year: str
    peak_hours: list[int]
    off_peak_hours: list[int]
    note: str
    provenance: ProvenanceKind
    source: str


class SuspiciousMeter(BaseModel):
    meter_id: str
    category: str
    anomaly_score: float
    is_theft_ground_truth: bool = Field(
        description="Only meaningful on this synthetic demo fleet, never a real theft finding."
    )


class MeterCluster(BaseModel):
    cluster: int
    n_meters: int
    mean_shape_pct: list[float] = Field(description="Mean normalised 24h shape, % of daily energy.")
    meter_ids: list[str]


class SgccDataset(BaseModel):
    n_consumers: int
    n_days: int
    theft_rate: float


class SgccMetrics(BaseModel):
    auc_roc: float
    pr_auc: float
    precision: float
    recall: float
    f1: float
    accuracy: float
    all_normal_baseline_accuracy: float
    map_at_100: float
    map_at_200: float


class SgccSummary(BaseModel):
    provenance: ProvenanceKind
    note: str = Field(description="Required FOREIGN-data disclosure for this page.")
    dataset: SgccDataset
    logreg_test: SgccMetrics
    lightgbm_test: SgccMetrics
    lightgbm_train_auc_roc: float
    lightgbm_val_auc_roc: float
    paper_test_auc_roc: float = Field(
        description="Zheng et al. 2018, as stated in the brief — not independently verified."
    )
    kmeans_best_k: int
    kmeans_silhouette: dict[str, float]


class TheftSegmentsResponse(Tagged):
    n_meters: int
    n_theft_ground_truth: int
    precision_at_k: float
    k: int
    ranking: list[SuspiciousMeter]
    clusters: list[MeterCluster]
    is_synthetic: Literal[True]
    sgcc: SgccSummary | None = Field(
        default=None,
        description="Real SGCC benchmark model-ladder + segments summary, if the "
        "pipeline has been run; None otherwise. Separate from the synthetic demo "
        "fleet above, which this page demos live.",
    )


class IexPriceRange(BaseModel):
    midday_price_per_unit: float
    night_price_per_unit: float
    month: str
    note: str
    provenance: ProvenanceKind
    source: str


class IexBlock(BaseModel):
    block: int = Field(ge=1, le=96)
    ts_target: datetime
    load_mw: float
    price_per_mwh: float
    cost_rupees: float
    is_expensive: bool = Field(description="Price in the top quartile of this day's curve.")


class IexPriceResponse(Tagged):
    date: date
    issued_at: datetime
    min_price_per_mwh: float
    max_price_per_mwh: float
    expensive_hour: int
    blocks: list[IexBlock]
    total_cost_rupees: float
    is_illustrative: Literal[True]
    manual_download_note: str
    price_range_benchmark: IexPriceRange


class SolarCapacityBenchmark(BaseModel):
    capacity_mwp: float
    as_of: str
    note: str
    provenance: ProvenanceKind
    source: str


class SolarBlock(BaseModel):
    block: int = Field(ge=1, le=96)
    ts_target: datetime
    load_mw: float
    ghi_wm2: float
    solar_mw: float
    net_load_mw: float


class SolarResponse(Tagged):
    date: date
    issued_at: datetime
    capacity_mwp: float
    performance_ratio: float
    blocks: list[SolarBlock]
    peak_load_mw: float
    peak_net_load_mw: float
    midday_solar_peak_mw: float
    evening_ramp_mw: float = Field(
        description="Net load rise from the midday solar trough to the evening peak."
    )
    capacity_benchmark: SolarCapacityBenchmark


class TodBillResponse(Tagged):
    flat_bill_rupees: float
    tod_bill_rupees: float
    savings_rupees: float
    hourly_cost_rupees: list[float]
    hourly_kwh: list[float]
    total_kwh: float
    shifted_tod_bill_rupees: float = Field(
        description="ToD bill after shift_fraction of the evening-peak energy moves to off-peak."
    )
    shifted_savings_rupees: float = Field(
        description="tod_bill_rupees - shifted_tod_bill_rupees: what shifting load saves, on top "
        "of just being on ToD."
    )
    is_illustrative: Literal[True]
    rates: TodRates
