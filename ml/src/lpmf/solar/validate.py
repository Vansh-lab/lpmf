"""Validate the PVWatts-style formula (P = GHI/1000 * C_kWp * PR) against
real paired irradiance/power data: fit the combined C_kWp*PR slope by
ordinary least squares through the origin (P = slope * GHI), then report
r^2 and MAPE on daytime blocks.
"""

from __future__ import annotations

import numpy as np

from lpmf.solar.load import PlantDataset


def fit_and_validate(ds: PlantDataset, daytime_irradiation_floor: float = 0.05) -> dict:
    x = ds.merged["irradiation_kw_m2"].to_numpy()
    y = ds.merged["ac_power_kw"].to_numpy()

    slope = float((x * y).sum() / (x * x).sum())
    pred = slope * x
    ss_res = float(((y - pred) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")

    daytime = (x > daytime_irradiation_floor) & (y > 0)
    mape = float(np.abs((y[daytime] - pred[daytime]) / y[daytime]).mean() * 100.0)

    return {
        "plant": ds.plant,
        "n_blocks_merged": int(len(ds.merged)),
        "n_daytime_blocks": int(daytime.sum()),
        "fitted_capacity_x_pr_kw": slope,
        "r_squared": r_squared,
        "mape_daytime_pct": mape,
    }
