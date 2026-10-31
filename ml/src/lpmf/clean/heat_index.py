"""NWS Rothfusz heat-index regression (NOAA Technical Attachment SR 90-23).

Implements the full regression plus the low-humidity and high-humidity
adjustments described in the attachment, operating in Fahrenheit internally
(as the regression's coefficients were fit in °F) with a Celsius-in,
Celsius-out public API.

Reference: https://www.weather.gov/ama/heatindex (Rothfusz 1990).
"""

from __future__ import annotations

import numpy as np


def _c_to_f(temp_c: np.ndarray) -> np.ndarray:
    return temp_c * 9.0 / 5.0 + 32.0


def _f_to_c(temp_f: np.ndarray) -> np.ndarray:
    return (temp_f - 32.0) * 5.0 / 9.0


def _heat_index_f(temp_f: np.ndarray, rh_pct: np.ndarray) -> np.ndarray:
    t = np.asarray(temp_f, dtype=float)
    r = np.asarray(rh_pct, dtype=float)

    # Step 1: simple formula (Steadman's approximation).
    simple = 0.5 * (t + 61.0 + ((t - 68.0) * 1.2) + (r * 0.094))

    # Step 2: full Rothfusz regression.
    full = (
        -42.379
        + 2.04901523 * t
        + 10.14333127 * r
        - 0.22475541 * t * r
        - 0.00683783 * t * t
        - 0.05481717 * r * r
        + 0.00122874 * t * t * r
        + 0.00085282 * t * r * r
        - 0.00000199 * t * t * r * r
    )

    # Step 3: low-humidity adjustment — subtract when RH < 13% and
    # 80 <= T <= 112 (°F).
    low_rh_mask = (r < 13.0) & (t >= 80.0) & (t <= 112.0)
    with np.errstate(invalid="ignore"):
        low_rh_adj = ((13.0 - r) / 4.0) * np.sqrt(
            np.clip((17.0 - np.abs(t - 95.0)) / 17.0, 0, None)
        )

    # Step 4: high-humidity adjustment — add when RH > 85% and
    # 80 <= T <= 87 (°F).
    high_rh_mask = (r > 85.0) & (t >= 80.0) & (t <= 87.0)
    high_rh_adj = ((r - 85.0) / 10.0) * ((87.0 - t) / 5.0)

    adjusted_full = full - np.where(low_rh_mask, low_rh_adj, 0.0)
    adjusted_full = adjusted_full + np.where(high_rh_mask, high_rh_adj, 0.0)

    # Step 5: if the average of the simple formula and the air temperature
    # is below 80°F, the simple formula is the answer — the full
    # regression is not valid in that range.
    use_simple = ((simple + t) / 2.0) < 80.0

    return np.where(use_simple, simple, adjusted_full)


def heat_index_c(temp_c: np.ndarray, rh_pct: np.ndarray) -> np.ndarray:
    """Heat index in °C, given air temperature in °C and relative humidity
    in percent (0-100). Vectorised: accepts scalars, lists, or arrays.
    """
    temp_f = _c_to_f(np.asarray(temp_c, dtype=float))
    hi_f = _heat_index_f(temp_f, np.asarray(rh_pct, dtype=float))
    return _f_to_c(hi_f)
