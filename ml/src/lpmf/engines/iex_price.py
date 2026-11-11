"""IEX Price page engine: an illustrative day-ahead price curve (cheap
midday solar hours, costly evening ramp) and the power-purchase cost it
implies against a load series.

    cost = Σ_t load_mw(t) · 0.25 h · price_per_mwh(t)

IEX's Day-Ahead Market publishes real 15-min MCP (market-clearing price)
data at iexindia.com/market-data/day-ahead-market/market-snapshot, but
that page is a client-rendered app with no public CSV/API found (checked:
a direct fetch returns the shell only, no embedded data or discoverable
endpoint). This engine is therefore always ILLUSTRATIVE; see
docs/DATA_QUALITY.md or the page's own note for how to plug in a real
download.

The one REAL number here is a reported price range, not this project's
own measurement: EAC_PM_PRICE_RANGE below.

Ref: IEX DAM/RTM market data (not fetched here); EAC-PM WP 53/2026.
"""

from __future__ import annotations

import numpy as np

from lpmf.provenance import ProvenanceKind

BLOCKS_PER_HOUR = 4
HOURS_PER_DAY = 24

# S. Sanyal & S. Dev, "The Duck and the Camel: Tracing the Net Load on the
# Indian Power Grid", EAC-PM Working Paper 53/2026: midday exchange prices
# near Rs 1.11/unit and night prices near Rs 9.71/unit, May 2026. A
# reported range, not measured by this project, and not Delhi-specific.
EAC_PM_PRICE_RANGE = {
    "midday_price_per_unit": 1.11,
    "night_price_per_unit": 9.71,
    "month": "May 2026",
    "note": "All-India IEX price range reported by EAC-PM, not this project's own measurement.",
    "source": "EAC-PM Working Paper 53/2026",
    "provenance": ProvenanceKind.FOREIGN,
}


def illustrative_hourly_price_per_mwh(
    min_price_per_mwh: float,
    max_price_per_mwh: float,
    expensive_hour: int = 20,
) -> list[float]:
    """A smooth 24-value illustrative price curve: one cosine cycle peaking
    at `expensive_hour` (the evening ramp) and troughing 12h later (the
    midday solar hours, for the default 20:00 peak -> 08:00 trough). A
    single sinusoid cannot put its peak and trough at two independently
    chosen hours, so only the peak is a parameter. Not a real IEX price
    series."""
    if min_price_per_mwh < 0 or max_price_per_mwh < min_price_per_mwh:
        raise ValueError(
            f"need 0 <= min_price_per_mwh ({min_price_per_mwh}) <= max_price_per_mwh "
            f"({max_price_per_mwh})."
        )
    if not (0 <= expensive_hour < HOURS_PER_DAY):
        raise ValueError(f"expensive_hour must be in 0..23, got {expensive_hour}.")

    hours = np.arange(HOURS_PER_DAY)
    shape = (1 + np.cos(2 * np.pi * (hours - expensive_hour) / HOURS_PER_DAY)) / 2.0
    price = min_price_per_mwh + shape * (max_price_per_mwh - min_price_per_mwh)
    return price.tolist()


def purchase_cost(
    load_mw: list[float] | np.ndarray, price_per_mwh_by_block: list[float] | np.ndarray
) -> dict:
    """Cost (Rs) of buying `load_mw[i]` at 15-min block i, charged at
    `price_per_mwh_by_block[i]` (same length, one price per block)."""
    load = np.atleast_1d(np.asarray(load_mw, dtype=float))
    price = np.atleast_1d(np.asarray(price_per_mwh_by_block, dtype=float))
    if load.shape != price.shape:
        raise ValueError(
            f"load_mw and price_per_mwh_by_block lengths differ: {load.shape} vs {price.shape}."
        )
    if (load < 0).any():
        raise ValueError("load_mw must be non-negative.")
    if (price < 0).any():
        raise ValueError("price_per_mwh_by_block must be non-negative.")

    cost_per_block = load * 0.25 * price
    return {
        "cost_per_block_rupees": cost_per_block.tolist(),
        "total_cost_rupees": float(cost_per_block.sum()),
        "is_illustrative": True,
        "provenance": ProvenanceKind.ILLUSTRATIVE,
    }
