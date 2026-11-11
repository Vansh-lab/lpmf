"""iex.load: validation checks against the real IEX DAM dataset's expected shape."""

from __future__ import annotations

import pandas as pd

from lpmf.iex.load import IexDataset, validate_against_expectations


def _make_dataset(n_days: int, hour_price: dict[int, float]) -> IexDataset:
    ts = pd.date_range("2024-01-01", periods=n_days * 96, freq="15min")
    prices = [hour_price.get(t.hour, 3000.0) for t in ts]
    return IexDataset(df=pd.DataFrame({"TimeStamp": ts, "price_per_mwh": prices}))


def test_detects_a_fully_continuous_15min_series():
    ds = _make_dataset(5, {19: 6000.0, 13: 3000.0})
    out = validate_against_expectations(ds)
    assert out["is_15min_continuous"] is True
    assert out["n_missing_blocks"] == 0
    assert out["n_duplicate_timestamps"] == 0


def test_detects_missing_blocks():
    ds = _make_dataset(5, {19: 6000.0, 13: 3000.0})
    ds = IexDataset(df=ds.df.drop(index=10))
    out = validate_against_expectations(ds)
    assert out["is_15min_continuous"] is False
    assert out["n_missing_blocks"] == 1


def test_evening_peak_check_passes_for_a_real_shaped_series():
    ds = _make_dataset(5, {19: 6000.0, 13: 3000.0})
    out = validate_against_expectations(ds)
    assert out["evening_peak_above_midday_trough"] is True


def test_evening_peak_check_fails_for_a_flat_series():
    ds = _make_dataset(5, {})
    out = validate_against_expectations(ds)
    assert out["evening_peak_above_midday_trough"] is False


def test_price_per_unit_conversion():
    ds = _make_dataset(1, {})
    out = validate_against_expectations(ds)
    assert out["mean_price_per_unit"] == 3.0
