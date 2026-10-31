"""Ingest hourly weather for Delhi from the Open-Meteo Archive API (REAL).

Location: lat 28.6139, lon 77.2090 (Delhi / Connaught Place reference point).
No API key required. Responses are cached to data/raw/weather/ as parquet,
chunked by calendar year, so repeated pipeline runs do not re-hit the API.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd
import requests

IST = "Asia/Kolkata"
LAT = 28.6139
LON = 77.2090

HOURLY_VARS = [
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "shortwave_radiation",
    "wind_speed_10m",
    "cloud_cover",
]

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


@dataclass(frozen=True)
class WeatherFetchResult:
    frame: pd.DataFrame
    cached_years: list[int]
    fetched_years: list[int]


def _cache_path(cache_dir: Path, year: int) -> Path:
    return cache_dir / f"weather_{year}.parquet"


def _fetch_year(year: int, timeout: int = 60) -> pd.DataFrame:
    start = date(year, 1, 1)
    end = date(year, 12, 31)
    params = {
        "latitude": LAT,
        "longitude": LON,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "hourly": ",".join(HOURLY_VARS),
        "timezone": IST,
    }
    resp = requests.get(ARCHIVE_URL, params=params, timeout=timeout)
    resp.raise_for_status()
    payload = resp.json()
    hourly = payload.get("hourly", {})
    if not hourly or "time" not in hourly:
        raise ValueError(f"Open-Meteo response for {year} missing 'hourly.time': {payload!r}")

    df = pd.DataFrame({"ts_ist": pd.to_datetime(hourly["time"])})
    for var in HOURLY_VARS:
        df[var] = hourly.get(var)
    df["ts_ist"] = df["ts_ist"].dt.tz_localize(IST, ambiguous="raise", nonexistent="raise")
    return df


def fetch_weather(
    start_year: int,
    end_year: int,
    cache_dir: str | Path = "data/raw/weather",
    force_refresh: bool = False,
) -> WeatherFetchResult:
    """Fetch (or load from cache) hourly weather for every year in
    [start_year, end_year] inclusive, concatenated and sorted by ts_ist.
    """
    cache_path_dir = Path(cache_dir)
    cache_path_dir.mkdir(parents=True, exist_ok=True)

    frames: list[pd.DataFrame] = []
    cached_years: list[int] = []
    fetched_years: list[int] = []

    for year in range(start_year, end_year + 1):
        cpath = _cache_path(cache_path_dir, year)
        if cpath.exists() and not force_refresh:
            frames.append(pd.read_parquet(cpath))
            cached_years.append(year)
            continue

        df = _fetch_year(year)
        df.to_parquet(cpath, index=False)
        frames.append(df)
        fetched_years.append(year)

    combined = pd.concat(frames, ignore_index=True).sort_values("ts_ist").reset_index(drop=True)
    combined = combined.rename(
        columns={
            "temperature_2m": "temp_c",
            "relative_humidity_2m": "rh_pct",
            "dew_point_2m": "dewpoint_c",
            "shortwave_radiation": "ghi_wm2",
            "wind_speed_10m": "wind_ms",
            "cloud_cover": "cloud_pct",
        }
    )
    return WeatherFetchResult(
        frame=combined, cached_years=cached_years, fetched_years=fetched_years
    )
