"""Validate the Rothfusz heat-index regression against known NOAA/NWS
heat-index chart values (https://www.weather.gov/safety/heat-index).

The published chart is rounded to the nearest whole °F, so we allow a
1.5°F tolerance against the raw regression output.
"""

from __future__ import annotations

import numpy as np
import pytest

from lpmf.clean.heat_index import heat_index_c


def _f_to_c(f: float) -> float:
    return (f - 32.0) * 5.0 / 9.0


def _c_to_f(c: float) -> float:
    return c * 9.0 / 5.0 + 32.0


# (temp_F, rh_pct, expected_heat_index_F) from the NWS chart.
NOAA_TABLE_CASES = [
    (80.0, 40.0, 80.0),
    (90.0, 40.0, 91.0),
    (90.0, 60.0, 100.0),
]


@pytest.mark.parametrize("temp_f,rh_pct,expected_hi_f", NOAA_TABLE_CASES)
def test_heat_index_matches_noaa_table(temp_f, rh_pct, expected_hi_f):
    hi_c = heat_index_c(_f_to_c(temp_f), rh_pct)
    hi_f = _c_to_f(hi_c)
    assert abs(hi_f - expected_hi_f) <= 1.5


def test_heat_index_vectorised():
    temps_c = np.array([_f_to_c(80.0), _f_to_c(90.0), _f_to_c(90.0)])
    rh = np.array([40.0, 40.0, 60.0])
    result = heat_index_c(temps_c, rh)
    assert result.shape == (3,)
    assert np.all(np.isfinite(result))


def test_heat_index_low_temp_uses_simple_formula():
    # At low temperatures the simple formula applies and heat index should
    # be close to (but not wildly different from) air temperature.
    hi_c = heat_index_c(15.0, 50.0)
    assert abs(hi_c - 15.0) < 5.0
