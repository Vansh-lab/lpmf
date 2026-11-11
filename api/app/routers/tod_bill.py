"""ToD Bill Simulator page (08): flat vs Time-of-Day bill for an illustrative
24-hour household profile, built from three sliders rather than 24 raw
numbers: how much daily energy, how evening-peaked it is, and how much of
that peak a consumer could shift to off-peak hours. The DERC surcharge/
rebate percentages are real; the profile is always illustrative.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from lpmf.engines.tod_bill import DERC_TOD_RATES, HOURS_PER_DAY, shift_load, tod_bill

from app.schemas import TodBillResponse, TodRates

router = APIRouter()

Fraction = Query(ge=0, le=1, allow_inf_nan=False)


def _build_profile(total_kwh: float, evening_peak_fraction: float) -> list[float]:
    peak_hours = DERC_TOD_RATES["peak_hours"]
    other_hours = [h for h in range(HOURS_PER_DAY) if h not in peak_hours]
    peak_total = total_kwh * evening_peak_fraction
    other_total = total_kwh - peak_total
    profile = [0.0] * HOURS_PER_DAY
    for h in peak_hours:
        profile[h] = peak_total / len(peak_hours)
    for h in other_hours:
        profile[h] = other_total / len(other_hours)
    return profile


@router.get("", response_model=TodBillResponse)
def tod(
    total_daily_kwh: Annotated[
        float, Query(ge=0, allow_inf_nan=False, description="Illustrative household profile.")
    ] = 10.0,
    evening_peak_fraction: Annotated[
        float,
        Fraction,
        Query(
            description="Share of the day's kWh used in the DERC peak hours (14:00-17:00 & 22:00-01:00, May-Sep)."
        ),
    ] = 0.4,
    shift_fraction: Annotated[
        float, Fraction, Query(description="Share of that peak energy shifted to off-peak hours.")
    ] = 0.3,
) -> TodBillResponse:
    rates = DERC_TOD_RATES
    try:
        profile = _build_profile(total_daily_kwh, evening_peak_fraction)
        base_rate = 8.0  # Illustrative Delhi domestic blended rate (Rs/kWh), not a DERC slab table.
        before = tod_bill(
            profile,
            base_rate,
            rates["peak_hours"],
            rates["off_peak_hours"],
            rates["peak_surcharge_pct"],
            rates["off_peak_rebate_pct"],
        )
        shifted_profile = shift_load(
            profile, rates["peak_hours"], rates["off_peak_hours"], shift_fraction
        )
        after = tod_bill(
            shifted_profile,
            base_rate,
            rates["peak_hours"],
            rates["off_peak_hours"],
            rates["peak_surcharge_pct"],
            rates["off_peak_rebate_pct"],
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

    return TodBillResponse(
        flat_bill_rupees=before["flat_bill_rupees"],
        tod_bill_rupees=before["tod_bill_rupees"],
        savings_rupees=before["savings_rupees"],
        hourly_cost_rupees=before["hourly_cost_rupees"],
        hourly_kwh=profile,
        total_kwh=before["total_kwh"],
        shifted_tod_bill_rupees=after["tod_bill_rupees"],
        shifted_savings_rupees=before["tod_bill_rupees"] - after["tod_bill_rupees"],
        is_illustrative=True,
        rates=TodRates(**rates),
        provenance=before["provenance"],
        source="Illustrative household profile; DERC FY 2020-21 tariff schedule ToD rates (operative, no base order since)",
    )
