"""overview.peak_and_alert against the PPT worked example (slide 7):
"820 kW at 19:00 > 800 kW limit -> alert"."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from lpmf.engines.overview import peak_and_alert
from lpmf.provenance import ProvenanceKind


def _forecast_peaking_at_1900(peak: float = 820.0) -> np.ndarray:
    values = np.full(96, 600.0)
    values[19 * 4] = peak  # block 77 = 19:00-19:15
    return values


def test_ppt_example_820_at_1900_over_800_limit_alerts():
    out = peak_and_alert(_forecast_peaking_at_1900(), limit_mw=800.0)
    assert out["peak_mw"] == 820.0
    assert out["peak_time"] == "19:00"
    assert out["peak_block"] == 77
    assert out["alert"] is True
    assert out["provenance"] == ProvenanceKind.REAL


def test_no_alert_at_or_below_the_limit():
    assert peak_and_alert(_forecast_peaking_at_1900(), limit_mw=820.0)["alert"] is False
    assert peak_and_alert(_forecast_peaking_at_1900(), limit_mw=900.0)["alert"] is False


def test_peak_time_read_from_a_datetime_index():
    index = pd.date_range("2026-06-12", periods=96, freq="15min", tz="Asia/Kolkata")
    out = peak_and_alert(pd.Series(_forecast_peaking_at_1900(), index=index), limit_mw=800.0)
    assert out["peak_time"] == "19:00"


def test_provenance_follows_the_input():
    out = peak_and_alert(
        _forecast_peaking_at_1900(), limit_mw=800.0, provenance=ProvenanceKind.SYNTHETIC
    )
    assert out["provenance"] == ProvenanceKind.SYNTHETIC


@pytest.mark.parametrize("bad", [np.full(95, 1.0), np.r_[np.full(95, 1.0), np.nan]])
def test_rejects_anything_but_96_finite_blocks(bad):
    with pytest.raises(ValueError, match="96 finite values"):
        peak_and_alert(bad, limit_mw=1.0)
