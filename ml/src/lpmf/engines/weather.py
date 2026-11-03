"""Weather impact page engine: heat sensitivity of load.

    load = β · heat_index + α      (ordinary least squares, one predictor)

β is recomputed from whatever data is passed in, never stored as a constant.
This is the method docs/DATA_QUALITY.md reports: lpmf.qa.report calls this
function on every non-missing 15-min row of data/processed/delhi_15min.parquet.

Ref: own backtest on Delhi SLDC data; heat index per Rothfusz, NWS SR 90-23.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from lpmf.provenance import ProvenanceKind


def heat_sensitivity(
    load_series: pd.Series | np.ndarray | list[float],
    heat_index_series: pd.Series | np.ndarray | list[float],
    *,
    provenance: ProvenanceKind = ProvenanceKind.REAL,
) -> dict:
    """OLS slope of load (MW) on heat index (°C), over rows where both are
    present. Two Series are aligned on their index first."""
    if isinstance(load_series, pd.Series) and isinstance(heat_index_series, pd.Series):
        load_series, heat_index_series = load_series.align(heat_index_series, join="inner")
    y = np.asarray(load_series, dtype=float)
    x = np.asarray(heat_index_series, dtype=float)
    if x.shape != y.shape:
        raise ValueError(f"load and heat index lengths differ: {y.shape} vs {x.shape}.")
    both = ~np.isnan(x) & ~np.isnan(y)
    x, y = x[both], y[both]
    if x.size < 2 or np.ptp(x) == 0:
        raise ValueError("need at least two rows with distinct heat index values.")

    slope, intercept = np.polyfit(x, y, 1)
    residuals = y - (slope * x + intercept)
    r_squared = 1.0 - float(residuals @ residuals) / float(((y - y.mean()) ** 2).sum())
    return {
        "beta_mw_per_c": float(slope),
        "intercept_mw": float(intercept),
        "r_squared": r_squared,
        "n_rows": int(x.size),
        "provenance": provenance,
    }
