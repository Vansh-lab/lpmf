"""LPMF data pipeline CLI.

    python -m lpmf.pipeline --step all
    python -m lpmf.pipeline --step ingest
    python -m lpmf.pipeline --step clean
    python -m lpmf.pipeline --step join
    python -m lpmf.pipeline --step qa
    python -m lpmf.pipeline --step split

Each step writes its outputs to disk so steps can be re-run independently.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

from lpmf.clean.load_clean import clean_load
from lpmf.ingest.calendar import build_calendar
from lpmf.ingest.sldc import SldcDataMissingError, load_sldc_raw
from lpmf.ingest.weather import fetch_weather
from lpmf.join import build_joined_frame
from lpmf.qa.report import generate_qa_report
from lpmf.schema import validate_final_schema
from lpmf.split import compute_split_boundaries, save_split_boundaries

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

DATA_RAW = Path("data/raw")
DATA_INTERIM = Path("data/interim")
DATA_PROCESSED = Path("data/processed")


def step_ingest() -> pd.DataFrame:
    logger.info("Ingesting raw Delhi SLDC load data...")
    try:
        result = load_sldc_raw(DATA_RAW / "sldc")
    except SldcDataMissingError as exc:
        logger.error(str(exc))
        raise SystemExit(1) from exc
    DATA_INTERIM.mkdir(parents=True, exist_ok=True)
    result.frame.to_parquet(DATA_INTERIM / "delhi_5min_raw.parquet", index=False)
    logger.info(
        "Ingested %d raw 5-min rows from %d file(s).", len(result.frame), len(result.source_files)
    )
    return result.frame


def step_clean(raw: pd.DataFrame | None = None) -> pd.DataFrame:
    if raw is None:
        raw = pd.read_parquet(DATA_INTERIM / "delhi_5min_raw.parquet")
    logger.info("Cleaning raw load data...")
    cleaned, log = clean_load(raw)
    DATA_INTERIM.mkdir(parents=True, exist_ok=True)
    cleaned.to_parquet(DATA_INTERIM / "delhi_5min_clean.parquet", index=False)
    logger.info("Cleaning summary: %s", log.summary())
    return cleaned


def step_join(cleaned: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    if cleaned is None:
        cleaned = pd.read_parquet(DATA_INTERIM / "delhi_5min_clean.parquet")

    from lpmf.clean.load_clean import resample_blocks

    fifteen, hourly = resample_blocks(cleaned)

    start = cleaned["ts_ist"].min().date()
    end = cleaned["ts_ist"].max().date()
    calendar_df = build_calendar(start, end)

    weather_result = fetch_weather(start.year, end.year)

    fifteen_joined = build_joined_frame(fifteen, weather_result.frame, calendar_df)
    hourly_joined = build_joined_frame(hourly, weather_result.frame, calendar_df)

    fifteen_valid = validate_final_schema(fifteen_joined)
    hourly_valid = validate_final_schema(hourly_joined)

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    fifteen_valid.to_parquet(DATA_PROCESSED / "delhi_15min.parquet", index=False)
    hourly_valid.to_parquet(DATA_PROCESSED / "delhi_hourly.parquet", index=False)
    logger.info(
        "Wrote %d 15-min rows and %d hourly rows to data/processed/.",
        len(fifteen_valid),
        len(hourly_valid),
    )
    return fifteen_valid, hourly_valid


def step_split(fifteen: pd.DataFrame | None = None) -> None:
    if fifteen is None:
        fifteen = pd.read_parquet(DATA_PROCESSED / "delhi_15min.parquet")
    boundaries = compute_split_boundaries(fifteen["ts_ist"])
    save_split_boundaries(boundaries, DATA_PROCESSED / "splits.json")
    logger.info("Saved split boundaries: %s", boundaries.to_dict())


def step_qa() -> None:
    df_5min = pd.read_parquet(DATA_INTERIM / "delhi_5min_clean.parquet")
    df_15min = pd.read_parquet(DATA_PROCESSED / "delhi_15min.parquet")
    generate_qa_report(df_5min, df_15min)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="LPMF data pipeline.")
    parser.add_argument(
        "--step",
        choices=["ingest", "clean", "join", "split", "qa", "all"],
        default="all",
    )
    args = parser.parse_args(argv)

    if args.step in ("ingest", "all"):
        raw = step_ingest()
    else:
        raw = None

    if args.step in ("clean", "all"):
        cleaned = step_clean(raw)
    else:
        cleaned = None

    if args.step in ("join", "all"):
        fifteen, _hourly = step_join(cleaned)
    else:
        fifteen = None

    if args.step in ("split", "all"):
        step_split(fifteen)

    if args.step in ("qa", "all"):
        step_qa()


if __name__ == "__main__":
    main(sys.argv[1:])
