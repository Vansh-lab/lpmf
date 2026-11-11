"""ToD Bill Simulator page engine: flat vs Time-of-Day bill for a 24-hour
consumer load profile.

    bill = Σ_h kWh(h) · rate · multiplier(h)
    multiplier(h) = 1 + surcharge   if h in peak hours
                  = 1 - rebate      if h in off-peak hours
                  = 1               otherwise

The surcharge/rebate percentages and hour windows below are REAL — read
directly from the DERC tariff schedule PDF itself (not a secondary
citation), clause 3(d), page 2. DERC's ToD slots only apply May-September
(no ToD in the other 6 months) and only to non-Domestic consumers with
sanctioned load/MDI >= 10kW/11kVA (optional for everyone else). This is a
materially different structure than a flat, year-round schedule — captured
honestly in the `note` field below. DERC has not issued a new base tariff
order since 30.09.2021; later DERC orders (e.g. FY 2025-26) only adjust the
fuel-cost (PPAC) surcharge on top of this schedule, not the ToD structure
itself, so this remains the operative ToD schedule. The 24-hour load
profile itself is always a user input or an illustrative shape, never a
real metered consumer — so the bill this produces is ILLUSTRATIVE even
though the rates are real.

Ref: Electricity (Rights of Consumers) Amendment Rules, 2023 (mandates
ToD metering/tariffs); DERC "Electricity Tariff Schedule for FY 2020-21 —
BRPL, BYPL, TPDDL & NDMC", clause 3(d), page 2 (read directly from the PDF
at tatapower-ddl.com/Editor_UploadedDocuments/Content/Tariff_Schedule_2020-21.pdf).
"""

from __future__ import annotations

import numpy as np

from lpmf.provenance import ProvenanceKind

HOURS_PER_DAY = 24

# Read directly from the DERC tariff schedule PDF, clause 3(d), page 2:
# "The Commission has decided to retain the Rebate during the Off Peak
# hours and Peak hours Surcharge at 20%... retained the time slots for
# Peak and Off-Peak hours as follows: MONTHS: May-September, PEAK HOURS:
# 1400-1700 & 2200-0100, OFF-PEAK HOURS: 0400-1000." Applies jointly to
# BRPL, BYPL and TPDDL. The 2200-0100 peak window wraps past midnight —
# represented here as hours 22, 23, 0.
DERC_TOD_RATES = {
    "peak_surcharge_pct": 20.0,
    "off_peak_rebate_pct": 20.0,
    "order_year": "FY 2020-21 (DERC's last base tariff order was 30.09.2021; "
    "later orders adjust only the fuel-cost surcharge, not ToD structure)",
    "peak_hours": [14, 15, 16, 22, 23, 0],  # 14:00-17:00 & 22:00-01:00
    "off_peak_hours": [4, 5, 6, 7, 8, 9],  # 04:00-10:00
    "note": (
        "ToD applies only May-September (no ToD the other 6 months), and only to "
        "non-Domestic consumers with sanctioned load/MDI >= 10kW/11kVA (optional for "
        "everyone else). This simulator applies the rates year-round for illustration; "
        "a real bill would not carry ToD outside that season/eligibility."
    ),
    "source": "DERC Tariff Schedule FY 2020-21 (BRPL, BYPL, TPDDL & NDMC), clause 3(d), page 2",
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
