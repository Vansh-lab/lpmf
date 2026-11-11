"""Validate the solar formula against real plant data (both plants),
including per-inverter data-quality diagnostics for Plant 2, and write the
result to models/artifacts/solar/validation.json.

Run from the repo root:
    python -m lpmf.solar.pipeline
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from lpmf.solar.diagnostics import dc_ac_ratio, iqr_outlier_inverters, per_inverter_zero_rate
from lpmf.solar.load import load_plant, load_plant_raw
from lpmf.solar.validate import fit_and_validate

logger = logging.getLogger(__name__)
ARTIFACTS_DIR = Path("models/artifacts/solar")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    results = {}
    diagnostics = {}
    for plant in (1, 2):
        logger.info("Validating formula against Plant %d...", plant)
        ds = load_plant(plant)
        out = fit_and_validate(ds)
        logger.info(
            "Plant %d: r2=%.4f (daytime %.4f), MAPE=%.2f%%, WAPE=%.2f%%, nMAE=%.2f%%, n=%d",
            plant,
            out["r_squared"],
            out["r_squared_daytime"],
            out["mape_daytime_pct"],
            out["wape_daytime_pct"],
            out["nmae_daytime_pct"],
            out["n_blocks_merged"],
        )
        results[f"plant_{plant}"] = out

        gen, weather = load_plant_raw(plant)
        ratio = dc_ac_ratio(gen)
        zero_rates = per_inverter_zero_rate(gen, weather)
        flagged = iqr_outlier_inverters(zero_rates["frac_zero_at_strong_irradiation"])
        logger.info("Plant %d: DC/AC ratio=%.4f, IQR-flagged inverters=%s", plant, ratio, flagged)
        diagnostics[f"plant_{plant}"] = {
            "dc_ac_ratio": ratio,
            "iqr_flagged_inverters": flagged,
            "per_inverter_zero_rate_at_strong_irradiation": zero_rates[
                "frac_zero_at_strong_irradiation"
            ].to_dict(),
        }

    results["source"] = (
        "Kaggle anikannal/solar-power-generation-data (India, 2 plants, May-Jun 2020)"
    )
    results["diagnostics"] = diagnostics
    results["diagnostics_note"] = (
        "Plant 2's per-inverter zero-output rate during strong irradiance (>0.6 kW/m^2) "
        "forms a smooth continuum (~4%-49% across 22 inverters) with no statistically "
        "distinguishable faulty subset by the Tukey IQR rule (applied to the data's own "
        "spread, not to how exclusion would affect the fit) -- so no inverters are excluded. "
        "Plant 1's own DC_POWER/AC_POWER ratio is ~0.10, a real units/scaling quirk in that "
        "file (not touched here since the formula validation only ever used AC_POWER); "
        "Plant 2's ratio (~0.98) shows no such mismatch, a plausible real inverter efficiency."
    )
    (ARTIFACTS_DIR / "validation.json").write_text(json.dumps(results, indent=2))
    logger.info("Wrote %s", ARTIFACTS_DIR / "validation.json")


if __name__ == "__main__":
    main()
