"""Load and validate the real IEX Day-Ahead Market (DAM) price dataset.

Source: Kaggle `mukund604/indian-energy-exchange-time-series-forecasting`
(DAM.xlsx), Apache 2.0. The uploader's own provenance/citation fields are
empty, so this is validated here against what IEX's own live Market
Snapshot shows (15-min blocks, a strong evening-peak / midday-trough
pattern, and a plausible all-India price range) rather than trusted blind.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

RAW_PATH = Path("data/raw/iex/DAM.xlsx")

PRICE_COL = "MCP (Rs/MWh) *"
TIME_COL = "TimeStamp"
BLOCKS_PER_DAY = 96


@dataclass(frozen=True)
class IexDataset:
    df: pd.DataFrame  # columns: TimeStamp, price_per_mwh


def load_raw(path: Path = RAW_PATH) -> IexDataset:
    raw = pd.read_excel(path)
    df = raw[[TIME_COL, PRICE_COL]].rename(columns={PRICE_COL: "price_per_mwh"})
    df = df.sort_values(TIME_COL).reset_index(drop=True)
    return IexDataset(df=df)


def validate_against_expectations(ds: IexDataset) -> dict:
    df = ds.df
    full_range = pd.date_range(df[TIME_COL].min(), df[TIME_COL].max(), freq="15min")
    missing = full_range.difference(df[TIME_COL])
    duplicates = int(df[TIME_COL].duplicated().sum())

    return {
        "n_blocks": int(len(df)),
        "date_range": [str(df[TIME_COL].min()), str(df[TIME_COL].max())],
        "n_missing_blocks": int(len(missing)),
        "n_duplicate_timestamps": duplicates,
        "is_15min_continuous": len(missing) == 0 and duplicates == 0,
        "min_price_per_unit": float(df["price_per_mwh"].min() / 1000.0),
        "max_price_per_unit": float(df["price_per_mwh"].max() / 1000.0),
        "mean_price_per_unit": float(df["price_per_mwh"].mean() / 1000.0),
        "evening_peak_above_midday_trough": _evening_peak_above_midday(df),
    }


def _evening_peak_above_midday(df: pd.DataFrame) -> bool:
    """Sanity check against the live IEX pattern (confirmed by browsing
    iexindia.com's Market Snapshot): the 19:00 evening peak should be
    noticeably pricier than the 13:00 midday (solar) trough."""
    hour = df[TIME_COL].dt.hour
    evening = df.loc[hour == 19, "price_per_mwh"].mean()
    midday = df.loc[hour == 13, "price_per_mwh"].mean()
    return bool(evening > midday * 1.2)
