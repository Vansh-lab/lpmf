"""iex.profile: block-of-day averaging on the real IEX dataset."""

from __future__ import annotations

import pandas as pd
import pytest

from lpmf.iex.load import IexDataset
from lpmf.iex.profile import (
    BLOCKS_PER_DAY,
    build_block_of_day_profile,
    hourly_from_block_profile,
    yearly_mean_price,
)


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


def test_block_profile_restricted_to_one_year():
    ts = list(pd.date_range("2023-01-01", periods=96, freq="15min")) + list(
        pd.date_range("2024-01-01", periods=96, freq="15min")
    )
    prices = [1000.0] * 96 + [3000.0] * 96
    ds = IexDataset(df=pd.DataFrame({"TimeStamp": ts, "price_per_mwh": prices}))

    profile_2024 = build_block_of_day_profile(ds, year=2024)
    assert all(p == pytest.approx(3000.0) for p in profile_2024)

    profile_all = build_block_of_day_profile(ds)
    assert all(p == pytest.approx(2000.0) for p in profile_all)


def test_block_profile_raises_for_a_year_with_no_rows():
    ts = pd.date_range("2024-01-01", periods=96, freq="15min")
    ds = IexDataset(df=pd.DataFrame({"TimeStamp": ts, "price_per_mwh": [500.0] * 96}))
    with pytest.raises(ValueError):
        build_block_of_day_profile(ds, year=2019)


def test_yearly_mean_price_averages_each_calendar_year_separately():
    ts = list(pd.date_range("2023-06-01", periods=4, freq="D")) + list(
        pd.date_range("2024-06-01", periods=2, freq="D")
    )
    prices = [100.0, 200.0, 300.0, 400.0, 1000.0, 2000.0]
    ds = IexDataset(df=pd.DataFrame({"TimeStamp": ts, "price_per_mwh": prices}))

    out = yearly_mean_price(ds)

    assert out == {2023: pytest.approx(250.0), 2024: pytest.approx(1500.0)}
