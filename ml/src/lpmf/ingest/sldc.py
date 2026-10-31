"""Ingest raw Delhi SLDC load data (5-minute resolution).

Source (REAL, primary): Kaggle dataset
    prash4nt/delhi-sldc-load-data-5-min-resolution
Coverage: 2023-04-01 .. 2026-01-12, 5-minute resolution, scraped from
delhisldc.org.

The raw CSV(s) are NOT checked into this repo (see data/raw/.gitkeep). To
fetch them:

    pip install kaggle
    # place your Kaggle API token at ~/.kaggle/kaggle.json (chmod 600),
    # downloaded from https://www.kaggle.com/settings -> API -> Create New Token
    kaggle datasets download -d prash4nt/delhi-sldc-load-data-5-min-resolution \
        -p data/raw/sldc --unzip

NOTE (verified against the actual downloaded file, 2026-10-31): the current
Kaggle export's header is `timestamp,load_MW` and timestamps are ISO
`YYYY-MM-DD HH:MM:SS` (unambiguous, year-first) — e.g. `2023-04-01 00:00:00`.
This differs from an earlier assumption that the export was day-first
(`dd-mm-yyyy HH:MM`); that format is kept below as a fallback in case a
future revision of the dataset reverts to it, but is no longer the primary
candidate. Either way, this module always parses with an explicit format
list and never calls `pd.to_datetime` without one — never trusting pandas'
format inference, which silently guesses wrong on ambiguous day/month
values.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

IST = "Asia/Kolkata"

# Candidate column names seen in Delhi-SLDC-style exports; the first match in
# each list wins, matched case-insensitively (the current export uses
# "load_MW", mixed case). Keeping this as a lookup (rather than hard failing
# on exact names) makes the ingester resilient to minor header variations
# between dataset revisions.
_TIMESTAMP_CANDIDATES = ["timestamp", "datetime", "date_time"]
_LOAD_CANDIDATES = ["load_mw", "load", "delhi", "delhi_load_mw", "demand_mw"]

# Explicit formats to try, most specific/unambiguous first. We never pass
# `dayfirst=True` alone to `pd.to_datetime` and rely on inference — we try
# exact formats so a parse failure is loud rather than silently wrong.
# ISO (year-first) is what the current export actually uses; the day-first
# variants are kept as a fallback only.
_DATETIME_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%d-%m-%Y %H:%M",
    "%d-%m-%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%d/%m/%Y %H:%M:%S",
    "%d-%m-%Y %H:%M:%S.%f",
]


class SldcDataMissingError(FileNotFoundError):
    """Raised when the raw Delhi SLDC CSV(s) cannot be found on disk."""


@dataclass(frozen=True)
class SldcIngestResult:
    frame: pd.DataFrame
    source_files: list[Path]


def _find_raw_files(raw_dir: Path) -> list[Path]:
    if not raw_dir.exists():
        return []
    return sorted(raw_dir.rglob("*.csv"))


def _resolve_column(df: pd.DataFrame, candidates: list[str], role: str) -> str:
    lower_to_actual = {c.lower(): c for c in df.columns}
    for name in candidates:
        actual = lower_to_actual.get(name.lower())
        if actual is not None:
            return actual
    raise ValueError(
        f"Could not find a {role} column in SLDC export. "
        f"Looked for any of {candidates!r} (case-insensitive), "
        f"found columns {list(df.columns)!r}."
    )


def _parse_day_first(series: pd.Series) -> pd.Series:
    """Parse a timestamp column that is known to be day-first, trying a
    fixed list of explicit formats. Never falls back to free inference.
    """
    raw = series.astype(str).str.strip()
    last_error: Exception | None = None
    for fmt in _DATETIME_FORMATS:
        try:
            parsed = pd.to_datetime(raw, format=fmt, errors="raise")
            return parsed
        except (ValueError, TypeError) as exc:
            last_error = exc
            continue
    raise ValueError(
        "Could not parse SLDC timestamps with any known day-first format "
        f"{_DATETIME_FORMATS!r}. Sample values: {raw.head(5).tolist()!r}. "
        f"Last error: {last_error}"
    )


def load_sldc_raw(data_raw_dir: str | Path = "data/raw/sldc") -> SldcIngestResult:
    """Load and concatenate all raw Delhi SLDC CSV(s) under `data_raw_dir`.

    Returns a frame with columns `ts_ist` (tz-aware, Asia/Kolkata) and
    `load_mw` (float), sorted by timestamp. Raises `SldcDataMissingError`
    with setup instructions if no files are found.
    """
    raw_dir = Path(data_raw_dir)
    files = _find_raw_files(raw_dir)
    if not files:
        raise SldcDataMissingError(
            f"No Delhi SLDC CSV files found under '{raw_dir}'.\n\n"
            "This dataset is not checked into the repo. Fetch it with:\n\n"
            "    pip install kaggle\n"
            "    # place your token at ~/.kaggle/kaggle.json (see\n"
            "    # https://www.kaggle.com/settings -> API -> Create New Token)\n"
            "    kaggle datasets download -d "
            "prash4nt/delhi-sldc-load-data-5-min-resolution \\\n"
            f"        -p {raw_dir} --unzip\n"
        )

    frames = []
    for f in files:
        df = pd.read_csv(f)
        ts_col = _resolve_column(df, _TIMESTAMP_CANDIDATES, "timestamp")
        load_col = _resolve_column(df, _LOAD_CANDIDATES, "load")

        parsed_ts = _parse_day_first(df[ts_col])
        out = pd.DataFrame(
            {
                "ts_ist": parsed_ts,
                "load_mw": pd.to_numeric(df[load_col], errors="coerce"),
            }
        )
        frames.append(out)

    combined = pd.concat(frames, ignore_index=True)
    # Localise naive timestamps to IST. SLDC publishes in local (IST) time
    # with no UTC offset in the file, so this is a localisation, not a
    # conversion.
    combined["ts_ist"] = combined["ts_ist"].dt.tz_localize(
        IST, ambiguous="raise", nonexistent="raise"
    )
    combined = combined.sort_values("ts_ist").reset_index(drop=True)
    return SldcIngestResult(frame=combined, source_files=files)
