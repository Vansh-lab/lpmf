"""Build the real, empirical block-of-day price profile from the full IEX
DAM history: the mean MCP for each of the day's 96 fifteen-minute blocks,
averaged over every day in the dataset (2018-2024). This is a REAL,
directly-computed statistic of the real dataset -- not a forecast and not
an illustration -- used as the day's "typical" price curve in place of the
old illustrative cosine wave.
"""

from __future__ import annotations

import pandas as pd

from lpmf.iex.load import IexDataset

BLOCKS_PER_DAY = 96


def build_block_of_day_profile(ds: IexDataset, year: int | None = None) -> list[float]:
    """Mean price_per_mwh for each of the 96 blocks-of-day, in order
    (block 0 = 00:00-00:15, ..., block 95 = 23:45-00:00). Pass `year` to
    restrict to one calendar year (e.g. the latest year alone, for
    comparison against the full-history average)."""
    df = ds.df.copy()
    if year is not None:
        df = df[df["TimeStamp"].dt.year == year]
        if df.empty:
            raise ValueError(f"no rows for year {year} in this dataset.")
    df["block"] = df["TimeStamp"].dt.hour * 4 + df["TimeStamp"].dt.minute // 15
    profile = df.groupby("block")["price_per_mwh"].mean().reindex(range(BLOCKS_PER_DAY))
    if profile.isna().any():
        missing = profile[profile.isna()].index.tolist()
        raise ValueError(f"missing blocks in the block-of-day profile: {missing}")
    return profile.tolist()


def hourly_from_block_profile(block_profile: list[float]) -> list[float]:
    """Collapse the 96-block profile to 24 hourly means (for pages that
    work in hourly resolution, e.g. the ToD/solar pages' convention)."""
    s = pd.Series(block_profile)
    return s.groupby(s.index // 4).mean().tolist()


def yearly_mean_price(ds: IexDataset) -> dict[int, float]:
    """Mean price_per_mwh for each calendar year present in the dataset --
    a small year-wise average, distinct from the block-of-day profile."""
    df = ds.df.copy()
    df["year"] = df["TimeStamp"].dt.year
    return {
        int(year): float(mean) for year, mean in df.groupby("year")["price_per_mwh"].mean().items()
    }
