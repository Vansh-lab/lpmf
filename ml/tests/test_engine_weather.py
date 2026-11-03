"""weather.heat_sensitivity: exact OLS recovery, agreement with the β that
docs/DATA_QUALITY.md reports for the real data, and the PPT's published
β ≈ 112.0 MW/°C ("+3 °C heat index ≈ +336 MW")."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from lpmf.engines.weather import heat_sensitivity

REPO = Path(__file__).resolve().parents[2]
FIFTEEN_MIN = REPO / "data" / "processed" / "delhi_15min.parquet"
DATA_QUALITY = REPO / "docs" / "DATA_QUALITY.md"
needs_real_data = pytest.mark.skipif(
    not FIFTEEN_MIN.exists(), reason="data/processed/delhi_15min.parquet not built"
)


def _real_beta() -> float:
    df = pd.read_parquet(FIFTEEN_MIN, columns=["load_mw", "heat_index_c"])
    return heat_sensitivity(df["load_mw"], df["heat_index_c"])["beta_mw_per_c"]


def test_recovers_an_exact_line():
    hi = np.linspace(20, 50, 200)
    out = heat_sensitivity(1300 + 112.0 * hi, hi)
    assert out["beta_mw_per_c"] == pytest.approx(112.0)
    assert out["intercept_mw"] == pytest.approx(1300.0)
    assert out["r_squared"] == pytest.approx(1.0)


def test_rows_missing_either_value_are_dropped_and_series_aligned():
    hi = pd.Series([30.0, 31.0, np.nan, 33.0], index=[0, 1, 2, 3])
    load = pd.Series([4000.0, np.nan, 4300.0, 4400.0, 9999.0], index=[3, 1, 2, 0, 7])
    out = heat_sensitivity(load, hi)
    assert out["n_rows"] == 2  # index 0 and 3: the only rows present in both
    assert out["beta_mw_per_c"] == pytest.approx((4000.0 - 4400.0) / (33.0 - 30.0))


def test_rejects_a_constant_heat_index():
    with pytest.raises(ValueError):
        heat_sensitivity([1.0, 2.0, 3.0], [30.0, 30.0, 30.0])


@needs_real_data
def test_real_data_beta_matches_the_data_quality_report():
    # Same function, same rows as lpmf.qa.report; the doc prints 3 decimals.
    published = float(
        re.search(r"OLS slope \(β\): \*\*([\d.]+)", DATA_QUALITY.read_text("utf-8")).group(1)
    )
    assert round(_real_beta(), 3) == pytest.approx(published)


@needs_real_data
def test_ppt_published_beta_112_0_and_plus_336_mw():
    # The deck said 111.6 / +335 MW until it was updated: that β predated the
    # Phase 3 causal cleaning. If the data changes again, update the deck too.
    beta = _real_beta()
    assert round(beta, 1) == 112.0
    assert round(3 * beta) == 336
