"""Pandera schema enforcing the final analysis-ready column contract.

This is the one place that defines the exact columns (and types) every
downstream feature/model/engine module may rely on. Any change here is a
breaking change to the whole ml/ package.
"""

from __future__ import annotations

import pandas as pd
import pandera.pandas as pa
from pandera.typing import Series

FINAL_COLUMNS = [
    "ts_ist",
    "block",
    "date",
    "load_mw",
    "imputed",
    "impute_method",
    "is_outlier",
    "temp_c",
    "rh_pct",
    "dewpoint_c",
    "ghi_wm2",
    "wind_ms",
    "cloud_pct",
    "heat_index_c",
    "is_holiday",
    "holiday_name",
    "dow",
    "month",
    "is_weekend",
    "data_source",
    "is_synthetic",
]


class LoadFrameSchema(pa.DataFrameModel):
    # `ts_ist` is deliberately NOT declared here: its dtype/tz contract is
    # asserted explicitly in `validate_final_schema` instead, because
    # pandas 2.x and 3.x default to different datetime64 units ("ns" vs
    # "us") and pinning a unit here would make this schema pandas-version
    # dependent. `strict=False` below lets it ride through unvalidated by
    # pandera while still being required (checked explicitly below).
    block: Series[int] = pa.Field(ge=1, le=96)
    date: Series[object]
    load_mw: Series[float] = pa.Field(nullable=True)
    imputed: Series[bool]
    impute_method: Series[str]
    is_outlier: Series[bool]
    temp_c: Series[float] = pa.Field(nullable=True)
    rh_pct: Series[float] = pa.Field(nullable=True)
    dewpoint_c: Series[float] = pa.Field(nullable=True)
    ghi_wm2: Series[float] = pa.Field(nullable=True)
    wind_ms: Series[float] = pa.Field(nullable=True)
    cloud_pct: Series[float] = pa.Field(nullable=True)
    heat_index_c: Series[float] = pa.Field(nullable=True)
    is_holiday: Series[bool]
    holiday_name: Series[object] = pa.Field(nullable=True)
    dow: Series[int] = pa.Field(ge=0, le=6)
    month: Series[int] = pa.Field(ge=1, le=12)
    is_weekend: Series[bool]
    data_source: Series[str] = pa.Field(nullable=False)
    is_synthetic: Series[bool] = pa.Field(nullable=False)

    class Config:
        strict = False  # extra helper columns (e.g. weather_interpolated) may ride along
        coerce = True  # normalise int32/int64 etc. platform width differences


def validate_final_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Validate (and return) `df` against the final schema contract.
    `data_source` and `is_synthetic` must never be null — enforced here as
    an explicit extra check beyond pandera's nullable=False, since pandera
    treats an all-non-null column as satisfying that already; this is kept
    as a readable, explicit guard for the two provenance columns the spec
    calls out by name.
    """
    missing = [c for c in FINAL_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Frame is missing required final columns: {missing}")

    if df["data_source"].isna().any():
        raise ValueError("data_source must never be null.")
    if df["is_synthetic"].isna().any():
        raise ValueError("is_synthetic must never be null.")

    if not isinstance(df["ts_ist"].dtype, pd.DatetimeTZDtype):
        raise ValueError(f"ts_ist must be tz-aware datetime, got dtype {df['ts_ist'].dtype!r}.")
    if str(df["ts_ist"].dtype.tz) != "Asia/Kolkata":
        raise ValueError(
            f"ts_ist must be tz-localised to Asia/Kolkata, got {df['ts_ist'].dtype.tz!r}."
        )

    validated = LoadFrameSchema.validate(df[FINAL_COLUMNS])
    return validated
