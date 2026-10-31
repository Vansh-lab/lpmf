"""Join cleaned load with weather and calendar onto the IST timestamp."""

from __future__ import annotations

import numpy as np
import pandas as pd

from lpmf.clean.heat_index import heat_index_c

IST = "Asia/Kolkata"


def join_weather(load_df: pd.DataFrame, weather_hourly: pd.DataFrame) -> pd.DataFrame:
    """Forward-fill hourly weather onto the (15-min or hourly) load grid.
    Adds a `weather_interpolated` flag marking rows that did not land on an
    exact hourly weather reading."""
    out = load_df.sort_values("ts_ist").copy()
    w = weather_hourly.sort_values("ts_ist").copy()

    weather_cols = [c for c in w.columns if c != "ts_ist"]

    merged = pd.merge_asof(
        out,
        w[["ts_ist", *weather_cols]],
        on="ts_ist",
        direction="backward",
    )
    # Exact-hour matches are not "interpolated"; anything resolved via the
    # backward as-of join from an earlier hour is forward-filled.
    exact_hour = out["ts_ist"].isin(w["ts_ist"])
    merged["weather_interpolated"] = ~exact_hour.values
    return merged


def join_calendar(df: pd.DataFrame, calendar_df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["date"] = out["ts_ist"].dt.date
    merged = out.merge(calendar_df, on="date", how="left")
    merged["is_holiday"] = merged["is_holiday"].fillna(False)
    return merged


def add_heat_index(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["heat_index_c"] = heat_index_c(out["temp_c"].to_numpy(), out["rh_pct"].to_numpy())
    return out


def add_calendar_derived(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["dow"] = out["ts_ist"].dt.day_of_week
    out["month"] = out["ts_ist"].dt.month
    out["is_weekend"] = out["dow"].isin([5, 6])
    return out


def build_joined_frame(
    load_df: pd.DataFrame,
    weather_hourly: pd.DataFrame,
    calendar_df: pd.DataFrame,
    data_source: str = "Delhi SLDC (Kaggle mirror)",
    is_synthetic: bool = False,
) -> pd.DataFrame:
    """Full join pipeline: weather -> calendar -> heat index -> calendar
    derived fields -> provenance columns, in the exact final schema order
    (see lpmf.schema)."""
    out = join_weather(load_df, weather_hourly)
    out = join_calendar(out, calendar_df)
    out = add_heat_index(out)
    out = add_calendar_derived(out)
    out["data_source"] = data_source
    out["is_synthetic"] = is_synthetic
    out["holiday_name"] = out.get("holiday_name", pd.Series(np.nan, index=out.index))
    return out
