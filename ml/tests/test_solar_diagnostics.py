"""solar.diagnostics: DC/AC ratio check, per-inverter zero-rate, IQR rule."""

from __future__ import annotations

import pandas as pd
import pytest

from lpmf.solar.diagnostics import dc_ac_ratio, iqr_outlier_inverters, per_inverter_zero_rate


def test_dc_ac_ratio_near_one_for_a_normal_inverter():
    gen = pd.DataFrame({"DC_POWER": [100.0, 200.0], "AC_POWER": [97.0, 196.0]})
    assert dc_ac_ratio(gen) == pytest.approx(293.0 / 300.0)


def test_dc_ac_ratio_flags_a_plant1_style_mismatch():
    # DC roughly 10x AC: a units/scaling mismatch, not a plausible efficiency.
    gen = pd.DataFrame({"DC_POWER": [1000.0, 2000.0], "AC_POWER": [100.0, 200.0]})
    assert dc_ac_ratio(gen) == pytest.approx(0.1)


def test_per_inverter_zero_rate_flags_the_inverter_that_is_zero_in_strong_sun():
    ts = pd.date_range("2020-05-15", periods=3, freq="15min")
    weather = pd.DataFrame({"DATE_TIME": ts, "IRRADIATION": [0.8, 0.8, 0.8]})
    gen = pd.DataFrame(
        {
            "DATE_TIME": list(ts) * 2,
            "SOURCE_KEY": ["healthy"] * 3 + ["faulty"] * 3,
            "AC_POWER": [600.0, 610.0, 590.0] + [0.0, 0.0, 0.0],
        }
    )
    out = per_inverter_zero_rate(gen, weather, irradiation_floor=0.6)
    assert out.loc["faulty", "frac_zero_at_strong_irradiation"] == pytest.approx(1.0)
    assert out.loc["healthy", "frac_zero_at_strong_irradiation"] == pytest.approx(0.0)


def test_iqr_outlier_inverters_flags_only_the_clear_outlier():
    rates = pd.Series(
        {"a": 0.05, "b": 0.08, "c": 0.06, "d": 0.07, "e": 0.09, "f": 0.95},
    )
    flagged = iqr_outlier_inverters(rates)
    assert flagged == ["f"]


def test_iqr_outlier_inverters_flags_nothing_on_a_smooth_spread():
    rates = pd.Series({f"inv{i}": v for i, v in enumerate([0.05, 0.1, 0.15, 0.2, 0.25, 0.3])})
    assert iqr_outlier_inverters(rates) == []
