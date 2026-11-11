"""Validate the PVWatts-style formula (P = GHI/1000 * C_kWp * PR) against
real paired irradiance/power data: fit the combined C_kWp*PR slope by
ordinary least squares through the origin (P = slope * GHI), then report
r^2, MAPE, WAPE and nMAE on daytime blocks.

MAPE alone is unreliable here: at low-but-still-"daytime" irradiance the
true power can be a handful of kW, so a small absolute error becomes a
huge percentage error and MAPE balloons. WAPE (sum of absolute errors over
sum of actuals) and nMAE (mean absolute error over mean actual) are not
dominated by individual near-zero rows the same way, so both are reported
alongside MAPE rather than instead of it.
"""

from __future__ import annotations

import numpy as np

from lpmf.solar.load import PlantDataset

# "Clearly daytime": well above the ~0.1 kW/m^2 (100 W/m^2) floor where a
# healthy panel is unambiguously producing current, not dawn/dusk noise.
DAYTIME_IRRADIATION_FLOOR = 0.1


def fit_and_validate(
    ds: PlantDataset, daytime_irradiation_floor: float = DAYTIME_IRRADIATION_FLOOR
) -> dict:
    x = ds.merged["irradiation_kw_m2"].to_numpy()
    y = ds.merged["ac_power_kw"].to_numpy()

    slope = float((x * y).sum() / (x * x).sum())
    pred = slope * x

    ss_res_all = float(((y - pred) ** 2).sum())
    ss_tot_all = float(((y - y.mean()) ** 2).sum())
    r_squared_all_blocks = 1.0 - ss_res_all / ss_tot_all if ss_tot_all > 0 else float("nan")

    daytime = x > daytime_irradiation_floor
    yd, predd = y[daytime], pred[daytime]
    ss_res_day = float(((yd - predd) ** 2).sum())
    ss_tot_day = float(((yd - yd.mean()) ** 2).sum())
    r_squared_daytime = 1.0 - ss_res_day / ss_tot_day if ss_tot_day > 0 else float("nan")

    nonzero = daytime & (y > 0)
    mape_daytime_pct = float(np.abs((y[nonzero] - pred[nonzero]) / y[nonzero]).mean() * 100.0)

    abs_err_day = np.abs(yd - predd)
    wape_daytime_pct = float(abs_err_day.sum() / yd.sum() * 100.0) if yd.sum() > 0 else float("nan")
    nmae_daytime_pct = (
        float(abs_err_day.mean() / yd.mean() * 100.0) if yd.mean() > 0 else float("nan")
    )

    return {
        "plant": ds.plant,
        "n_blocks_merged": int(len(ds.merged)),
        "n_daytime_blocks": int(daytime.sum()),
        "n_daytime_zero_actual_blocks": int((daytime & (y == 0)).sum()),
        "fitted_capacity_x_pr_kw": slope,
        "r_squared": r_squared_all_blocks,
        "r_squared_daytime": r_squared_daytime,
        "mape_daytime_pct": mape_daytime_pct,
        "wape_daytime_pct": wape_daytime_pct,
        "nmae_daytime_pct": nmae_daytime_pct,
    }
