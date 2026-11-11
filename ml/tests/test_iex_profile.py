"""iex.profile: block-of-day averaging on the real IEX dataset."""

from __future__ import annotations

import pandas as pd
import pytest

from lpmf.iex.load import IexDataset
from lpmf.iex.profile import BLOCKS_PER_DAY, build_block_of_day_profile, hourly_from_block_profile


def test_block_profile_averages_the_same_block_across_days():
    # Two days, block 0 (00:00) alternates 1000/3000 -> mean 2000; every
    # other block is constant 500.
    ts = pd.date_range("2024-01-01", periods=2 * 96, freq="15min")
    prices = [500.0] * (2 * 96)
    prices[0] = 1000.0
    prices[96] = 3000.0
    ds = IexDataset(df=pd.DataFrame({"TimeStamp": ts, "price_per_mwh": prices}))

    profile = build_block_of_day_profile(ds)
    assert len(profile) == BLOCKS_PER_DAY
    assert profile[0] == pytest.approx(2000.0)
    assert profile[1] == pytest.approx(500.0)


def test_block_profile_raises_on_missing_blocks():
    ts = pd.date_range("2024-01-01", periods=48, freq="15min")  # only half a day
    ds = IexDataset(df=pd.DataFrame({"TimeStamp": ts, "price_per_mwh": [500.0] * 48}))
    with pytest.raises(ValueError):
        build_block_of_day_profile(ds)


def test_hourly_from_block_profile_collapses_4_blocks_per_hour():
    block_profile = [100.0, 200.0, 300.0, 400.0] + [0.0] * (BLOCKS_PER_DAY - 4)
    hourly = hourly_from_block_profile(block_profile)
    assert len(hourly) == 24
    assert hourly[0] == pytest.approx(250.0)
    assert hourly[1] == pytest.approx(0.0)
