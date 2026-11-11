"""Load the real India "Solar Power Generation Data" (Kaggle
anikannal/solar-power-generation-data): 2 plants, 15-min generation
(per-inverter) and weather-sensor (per-plant) data, May-June 2020.

Used to validate `lpmf.engines.solar`'s PVWatts-style formula
(P_solar = GHI/1000 * C_kWp * PR) against real paired irradiance/power
data, before applying that formula to Delhi's Open-Meteo GHI.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

RAW_DIR = Path("data/raw/solar")

# Each plant's generation file uses a different DATE_TIME format in this
# dataset (confirmed by inspection); the weather files are both ISO.
_GEN_DATE_FORMAT = {1: "%d-%m-%Y %H:%M", 2: "%Y-%m-%d %H:%M:%S"}
_WEATHER_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


@dataclass(frozen=True)
class PlantDataset:
    plant: int
    merged: pd.DataFrame  # DATE_TIME, ac_power_kw (summed over inverters), irradiation_kw_m2


def load_plant(plant: int, raw_dir: Path = RAW_DIR) -> PlantDataset:
    if plant not in (1, 2):
        raise ValueError(f"plant must be 1 or 2, got {plant}.")

    gen = pd.read_csv(raw_dir / f"Plant_{plant}_Generation_Data.csv")
    weather = pd.read_csv(raw_dir / f"Plant_{plant}_Weather_Sensor_Data.csv")
    gen["DATE_TIME"] = pd.to_datetime(gen["DATE_TIME"], format=_GEN_DATE_FORMAT[plant])
    weather["DATE_TIME"] = pd.to_datetime(weather["DATE_TIME"], format=_WEATHER_DATE_FORMAT)

    total_ac = gen.groupby("DATE_TIME")["AC_POWER"].sum().reset_index()
    merged = total_ac.merge(weather[["DATE_TIME", "IRRADIATION"]], on="DATE_TIME", how="inner")
    merged = merged.rename(columns={"AC_POWER": "ac_power_kw", "IRRADIATION": "irradiation_kw_m2"})
    return PlantDataset(plant=plant, merged=merged)
