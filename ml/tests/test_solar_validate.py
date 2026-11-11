"""solar.validate: OLS-through-origin fit of GHI -> AC power, r^2/MAPE."""

from __future__ import annotations

import pandas as pd
import pytest

from lpmf.solar.load import PlantDataset
from lpmf.solar.validate import fit_and_validate


def test_perfect_linear_relationship_gives_r2_one_and_zero_mape():
    irradiation = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    true_slope = 1000.0
    ds = PlantDataset(
        plant=1,
        merged=pd.DataFrame(
            {
                "irradiation_kw_m2": irradiation,
                "ac_power_kw": [true_slope * x for x in irradiation],
            }
        ),
    )
    out = fit_and_validate(ds)
    assert out["fitted_capacity_x_pr_kw"] == pytest.approx(true_slope, rel=1e-6)
    assert out["r_squared"] == pytest.approx(1.0, abs=1e-9)
    assert out["mape_daytime_pct"] == pytest.approx(0.0, abs=1e-6)


def test_noisy_relationship_gives_a_worse_but_bounded_fit():
    irradiation = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0] * 4
    noise = [0, 50, -80, 30, -40, 60] * 4
    ds = PlantDataset(
        plant=2,
        merged=pd.DataFrame(
            {
                "irradiation_kw_m2": irradiation,
                "ac_power_kw": [
                    max(1000.0 * x + n, 0.0) for x, n in zip(irradiation, noise, strict=True)
                ],
            }
        ),
    )
    out = fit_and_validate(ds)
    assert 0.0 < out["r_squared"] < 1.0
    assert out["mape_daytime_pct"] > 0.0


def test_n_blocks_and_daytime_counts_are_reported():
    ds = PlantDataset(
        plant=1,
        merged=pd.DataFrame(
            {
                "irradiation_kw_m2": [0.0, 0.0, 0.3, 0.6],
                "ac_power_kw": [0.0, 0.0, 300.0, 600.0],
            }
        ),
    )
    out = fit_and_validate(ds)
    assert out["n_blocks_merged"] == 4
    assert out["n_daytime_blocks"] == 2
    assert out["plant"] == 1
