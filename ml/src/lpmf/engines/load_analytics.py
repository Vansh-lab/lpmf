"""Load analytics page engine: load factor, peak-to-average ratio and the
load-duration curve.

    LF  = P_avg / P_max        PAR = 1 / LF = P_max / P_avg
    LDC = loads sorted descending; each point's x is the % of time the load
          is at or above that value (rank / n * 100)

Ref: V.K. Mehta, Principles of Power System, Ch. 3.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from lpmf.provenance import ProvenanceKind


def load_factor_and_par(
    load_series: pd.Series | np.ndarray | list[float],
    *,
    provenance: ProvenanceKind = ProvenanceKind.REAL,
) -> dict:
    """LF, PAR and LDC over the non-missing values of `load_series` (missing
    blocks are skipped, not treated as zero load)."""
    values = np.asarray(load_series, dtype=float)
    values = values[~np.isnan(values)]
    if values.size == 0:
        raise ValueError("load_series has no non-missing values.")
    p_max = float(values.max())
    if p_max <= 0:
        raise ValueError(f"peak load must be positive, got {p_max}.")
    p_avg = float(values.mean())
    load_factor = p_avg / p_max

    ldc = np.sort(values)[::-1]
    pct_time = np.arange(1, ldc.size + 1) / ldc.size * 100.0
    return {
        "load_factor": load_factor,
        "par": 1.0 / load_factor,
        "p_avg_mw": p_avg,
        "p_max_mw": p_max,
        "n_values": int(values.size),
        "load_duration_curve": {"load_mw": ldc.tolist(), "pct_time": pct_time.tolist()},
        "provenance": provenance,
    }
