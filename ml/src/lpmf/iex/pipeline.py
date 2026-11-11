"""Build the real IEX DAM price profile artifacts from data/raw/iex/DAM.xlsx.

Run from the repo root:
    python -m lpmf.iex.pipeline
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from lpmf.iex.load import load_raw, validate_against_expectations
from lpmf.iex.profile import build_block_of_day_profile, hourly_from_block_profile

logger = logging.getLogger(__name__)
ARTIFACTS_DIR = Path("models/artifacts/iex")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    logger.info("Loading real IEX DAM dataset...")
    ds = load_raw()
    checks = validate_against_expectations(ds)
    logger.info("Validation: %s", checks)
    (ARTIFACTS_DIR / "dataset_validation.json").write_text(json.dumps(checks, indent=2))

    block_profile = build_block_of_day_profile(ds)
    hourly_profile = hourly_from_block_profile(block_profile)

    result = {
        "block_profile_per_mwh": block_profile,
        "hourly_profile_per_mwh": hourly_profile,
        "n_days_averaged": checks["n_blocks"] // 96,
        "date_range": checks["date_range"],
        "source": (
            "Kaggle mukund604/indian-energy-exchange-time-series-forecasting (DAM.xlsx), "
            "IEX Day-Ahead Market MCP"
        ),
    }
    (ARTIFACTS_DIR / "price_profile.json").write_text(json.dumps(result, indent=2))
    logger.info("Wrote %s", ARTIFACTS_DIR / "price_profile.json")


if __name__ == "__main__":
    main()
