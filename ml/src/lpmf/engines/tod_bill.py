"""ToD Bill Simulator page engine: flat vs Time-of-Day bill for a 24-hour
consumer load profile.

    bill = Σ_h kWh(h) · rate · multiplier(h)
    multiplier(h) = 1 + surcharge   if h in peak hours
                  = 1 - rebate      if h in off-peak hours
                  = 1               otherwise

The surcharge/rebate percentages are REAL (DERC's own tariff order); the
hour windows below are the commonly cited BRPL peak/off-peak slots, not
independently re-verified against the live DERC order for every year. The
24-hour load profile itself is always a user input or an illustrative
shape, never a real metered consumer — so the bill this produces is
ILLUSTRATIVE even though the rates are real.

Ref: Electricity (Rights of Consumers) Amendment Rules, 2023 (mandates
ToD metering/tariffs); DERC tariff order, FY 2025-26 (peak surcharge /
off-peak rebate percentages).
"""

from __future__ import annotations

import numpy as np

from lpmf.provenance import ProvenanceKind

HOURS_PER_DAY = 24

# DERC progressively raised the off-peak rebate (15% -> 20% -> 25%) and has
# held a 30% peak surcharge; both held steady into the FY 2025-26 order.
# Slot hours are the commonly cited BRPL peak/off-peak windows, not
# re-verified against every year's order.
DERC_TOD_RATES = {
    "peak_surcharge_pct": 30.0,
    "off_peak_rebate_pct": 25.0,
    "order_year": "FY 2025-26",
    "peak_hours": [17, 18, 19, 20, 21],  # 17:00-22:00
    "off_peak_hours": [22, 23, 0, 1, 2, 3, 4, 5],  # 22:00-06:00
    "note": (
        "Surcharge/rebate percentages are DERC's own figures for the FY 2025-26 tariff order; "
        "the specific peak/off-peak hour windows are the commonly cited BRPL slots and were not "
        "independently re-verified against that order."
    ),
    "source": "DERC tariff order, FY 2025-26",
    "provenance": ProvenanceKind.REAL,
}


def tod_bill(
    hourly_kwh: list[float] | np.ndarray,
    base_rate_per_kwh: float,
    peak_hours: list[int],
    off_peak_hours: list[int],
    peak_surcharge_pct: float,
    off_peak_rebate_pct: float,
) -> dict:
    """Flat-rate vs Time-of-Day bill for one day's 24 hourly kWh readings.

    `hourly_kwh[h]` is the energy used in hour `h` (0 = 00:00-01:00, ...,
    23 = 23:00-00:00). Always ILLUSTRATIVE: the profile is never a real
    metered consumer.
    """
    kwh = np.asarray(hourly_kwh, dtype=float)
    if kwh.shape != (HOURS_PER_DAY,):
        raise ValueError(f"hourly_kwh must have {HOURS_PER_DAY} values, got {kwh.shape[0]}.")
    if not np.isfinite(kwh).all() or (kwh < 0).any():
        raise ValueError("hourly_kwh must be finite and non-negative.")
    if base_rate_per_kwh < 0:
        raise ValueError(f"base_rate_per_kwh must be >= 0, got {base_rate_per_kwh}.")
    for name, pct in (
        ("peak_surcharge_pct", peak_surcharge_pct),
        ("off_peak_rebate_pct", off_peak_rebate_pct),
    ):
        if not (0 <= pct <= 100):
            raise ValueError(f"{name} must be in [0, 100], got {pct}.")
    for name, hours in (("peak_hours", peak_hours), ("off_peak_hours", off_peak_hours)):
        bad = [h for h in hours if not (0 <= h < HOURS_PER_DAY)]
        if bad:
            raise ValueError(f"{name} has hours outside 0..23: {bad}.")
    overlap = set(peak_hours) & set(off_peak_hours)
    if overlap:
        raise ValueError(f"peak_hours and off_peak_hours overlap: {sorted(overlap)}.")

    multiplier = np.ones(HOURS_PER_DAY)
    multiplier[list(peak_hours)] = 1.0 + peak_surcharge_pct / 100.0
    multiplier[list(off_peak_hours)] = 1.0 - off_peak_rebate_pct / 100.0

    flat_bill = float(kwh.sum() * base_rate_per_kwh)
    hourly_cost = kwh * base_rate_per_kwh * multiplier
    tod_total = float(hourly_cost.sum())

    return {
        "flat_bill_rupees": flat_bill,
        "tod_bill_rupees": tod_total,
        "savings_rupees": flat_bill - tod_total,
        "hourly_cost_rupees": hourly_cost.tolist(),
        "hourly_multiplier": multiplier.tolist(),
        "total_kwh": float(kwh.sum()),
        "is_illustrative": True,
        "provenance": ProvenanceKind.ILLUSTRATIVE,
    }


def shift_load(
    hourly_kwh: list[float] | np.ndarray,
    from_hours: list[int],
    to_hours: list[int],
    fraction: float,
) -> list[float]:
    """Move `fraction` of the energy used in `from_hours` to `to_hours`
    (spread evenly across the destination hours) — the "shift advice"
    what-if. `fraction` in [0, 1]."""
    if not (0 <= fraction <= 1):
        raise ValueError(f"fraction must be in [0, 1], got {fraction}.")
    if not to_hours:
        raise ValueError("to_hours must not be empty.")
    kwh = np.asarray(hourly_kwh, dtype=float).copy()
    if kwh.shape != (HOURS_PER_DAY,):
        raise ValueError(f"hourly_kwh must have {HOURS_PER_DAY} values, got {kwh.shape[0]}.")

    moved = kwh[list(from_hours)].sum() * fraction
    kwh[list(from_hours)] *= 1.0 - fraction
    for h in to_hours:
        kwh[h] += moved / len(to_hours)
    return kwh.tolist()
