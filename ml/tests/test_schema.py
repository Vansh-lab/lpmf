"""Tests for the final schema contract in lpmf.schema."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pandera.errors
import pytest

from lpmf.schema import FINAL_COLUMNS, validate_final_schema


def _valid_frame(n: int = 10) -> pd.DataFrame:
    ts = pd.date_range("2024-01-01", periods=n, freq="15min", tz="Asia/Kolkata")
    return pd.DataFrame(
        {
            "ts_ist": ts,
            "block": (np.arange(n) % 96) + 1,
            "date": ts.date,
            "load_mw": np.linspace(3000, 3100, n),
            "imputed": [False] * n,
            "impute_method": ["none"] * n,
            "is_outlier": [False] * n,
            "temp_c": np.linspace(20, 25, n),
            "rh_pct": np.linspace(40, 60, n),
            "dewpoint_c": np.linspace(10, 15, n),
            "ghi_wm2": np.linspace(0, 500, n),
            "wind_ms": np.linspace(1, 5, n),
            "cloud_pct": np.linspace(0, 100, n),
            "heat_index_c": np.linspace(20, 30, n),
            "is_holiday": [False] * n,
            "holiday_name": [None] * n,
            "dow": ts.day_of_week,
            "month": ts.month,
            "is_weekend": ts.day_of_week.isin([5, 6]),
            "data_source": ["Delhi SLDC (Kaggle mirror)"] * n,
            "is_synthetic": [False] * n,
        }
    )


def test_valid_frame_passes_schema():
    df = _valid_frame()
    validated = validate_final_schema(df)
    assert list(validated.columns) == FINAL_COLUMNS


def test_missing_column_raises():
    df = _valid_frame().drop(columns=["heat_index_c"])
    with pytest.raises(ValueError):
        validate_final_schema(df)


def test_null_data_source_raises():
    df = _valid_frame()
    df.loc[0, "data_source"] = None
    with pytest.raises(ValueError):
        validate_final_schema(df)


def test_null_is_synthetic_raises():
    df = _valid_frame()
    df["is_synthetic"] = df["is_synthetic"].astype(object)
    df.loc[0, "is_synthetic"] = None
    with pytest.raises(ValueError):
        validate_final_schema(df)


def test_block_out_of_range_raises():
    df = _valid_frame()
    df.loc[0, "block"] = 97
    with pytest.raises(pandera.errors.SchemaError):
        validate_final_schema(df)
