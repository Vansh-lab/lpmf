"""load_analytics.load_factor_and_par against the PPT worked example
(slide 7: "530 / 820 = 0.646"; slide 4: "LF 0.646, PAR 1.55")."""

from __future__ import annotations

import numpy as np
import pytest

from lpmf.engines.load_analytics import load_factor_and_par

# A day averaging 530 MW with an 820 MW peak.
PPT_DAY = [820.0, 240.0]


def test_ppt_example_load_factor_is_530_over_820():
    out = load_factor_and_par(PPT_DAY)
    assert out["p_avg_mw"] == 530.0 and out["p_max_mw"] == 820.0
    assert out["load_factor"] == pytest.approx(530 / 820)


def test_ppt_example_par_rounds_to_1_55():
    assert round(load_factor_and_par(PPT_DAY)["par"], 2) == 1.55


def test_ppt_example_load_factor_reads_0_646():
    # The deck said 0.647 until it was corrected: 530/820 = 0.6463.
    assert round(load_factor_and_par(PPT_DAY)["load_factor"], 3) == 0.646


def test_load_duration_curve_is_sorted_descending_with_percent_of_time():
    ldc = load_factor_and_par([300.0, 500.0, 400.0, 200.0])["load_duration_curve"]
    assert ldc["load_mw"] == [500.0, 400.0, 300.0, 200.0]
    assert ldc["pct_time"] == [25.0, 50.0, 75.0, 100.0]


def test_missing_blocks_are_skipped_not_counted_as_zero():
    out = load_factor_and_par([820.0, np.nan, 240.0])
    assert out["load_factor"] == pytest.approx(530 / 820)
    assert out["n_values"] == 2


def test_rejects_an_empty_or_non_positive_day():
    with pytest.raises(ValueError):
        load_factor_and_par([np.nan, np.nan])
    with pytest.raises(ValueError):
        load_factor_and_par([0.0, 0.0])
