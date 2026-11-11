"""Validate the solar formula against real plant data (both plants) and
write the result to models/artifacts/solar/validation.json.

Run from the repo root:
    python -m lpmf.solar.pipeline
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from lpmf.solar.load import load_plant
from lpmf.solar.validate import fit_and_validate

logger = logging.getLogger(__name__)
ARTIFACTS_DIR = Path("models/artifacts/solar")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    results = {}
    for plant in (1, 2):
        logger.info("Validating formula against Plant %d...", plant)
        ds = load_plant(plant)
        out = fit_and_validate(ds)
        logger.info(
            "Plant %d: r2=%.4f, MAPE(daytime)=%.2f%%, n=%d",
            plant,
            out["r_squared"],
            out["mape_daytime_pct"],
            out["n_blocks_merged"],
        )
        results[f"plant_{plant}"] = out

    results["source"] = (
        "Kaggle anikannal/solar-power-generation-data (India, 2 plants, May-Jun 2020)"
    )
    (ARTIFACTS_DIR / "validation.json").write_text(json.dumps(results, indent=2))
    logger.info("Wrote %s", ARTIFACTS_DIR / "validation.json")


if __name__ == "__main__":
    main()
