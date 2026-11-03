"""Overview page engine: tomorrow's peak and the overload alert.

    P̂_peak = max_t P̂(t)        alert = P̂_peak > limit

Ref: V.K. Mehta, Principles of Power System, Ch. 3.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from lpmf.provenance import ProvenanceKind

BLOCKS_PER_DAY = 96


def peak_and_alert(
    forecast_96_blocks: pd.Series | np.ndarray | list[float],
    limit_mw: float,
    *,
    provenance: ProvenanceKind = ProvenanceKind.REAL,
) -> dict:
    """Peak of a 96-block day-ahead forecast and whether it exceeds `limit_mw`.

    `forecast_96_blocks` is ordered block 1 (00:00-00:15) .. block 96. If it is
    a Series with a DatetimeIndex, peak_time is read from the index; otherwise
    it is the start time of the peak block. Ties go to the earliest block.
    """
    values = np.asarray(forecast_96_blocks, dtype=float)
    if values.shape != (BLOCKS_PER_DAY,) or not np.isfinite(values).all():
        raise ValueError(
            f"forecast_96_blocks must hold {BLOCKS_PER_DAY} finite values, got shape "
            f"{values.shape} with {int((~np.isfinite(values)).sum())} non-finite."
        )

    peak_idx = int(np.argmax(values))
    peak_mw = float(values[peak_idx])
    if isinstance(forecast_96_blocks, pd.Series) and isinstance(
        forecast_96_blocks.index, pd.DatetimeIndex
    ):
        peak_time = forecast_96_blocks.index[peak_idx].strftime("%H:%M")
    else:
        minutes = peak_idx * 15
        peak_time = f"{minutes // 60:02d}:{minutes % 60:02d}"

    return {
        "peak_mw": peak_mw,
        "peak_time": peak_time,
        "peak_block": peak_idx + 1,
        "limit_mw": float(limit_mw),
        "alert": bool(peak_mw > limit_mw),
        "provenance": provenance,
    }
