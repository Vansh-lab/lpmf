"""Load the SGCC electricity-theft dataset (Zheng et al., IEEE TII 2018).

Source: github.com/henryRDlab/ElectricityTheftDetection — 42,372 consumers,
daily kWh from 2014-01-01 to 2016-10-31 (a 1,035-day span; only 1,034
distinct daily columns are present, so one calendar day in that span has
no column at all, not just missing values). FOREIGN provenance: this is a
China (State Grid Corporation of China) benchmark, not Delhi data.

Known quirk of the raw CSV, confirmed on this copy: the date columns are
in lexicographic (string) order, not chronological order (e.g. "2014/1/10"
sorts before "2014/1/2"). Every function here that touches day order sorts
by the parsed date first.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

RAW_PATH = Path("data/raw/sgcc/data.csv")

EXPECTED_N_CONSUMERS = 42372
EXPECTED_N_DAYS = 1034
EXPECTED_SPAN_DAYS = 1035
EXPECTED_THEFT_RATE = 0.0853  # ~8.53%, within rounding of commonly-cited SGCC figures


@dataclass(frozen=True)
class SgccDataset:
    cons_no: np.ndarray  # (n,) consumer id
    flag: np.ndarray  # (n,) 0/1 theft label
    dates: pd.DatetimeIndex  # (d,) chronologically sorted
    kwh: np.ndarray  # (n, d) daily consumption, chronological column order, NaN = missing


def load_raw(path: str | Path = RAW_PATH) -> SgccDataset:
    """Read the raw CSV and sort its date columns chronologically. Does not
    clean, impute or drop anything — see sgcc.clean for that, which must
    run after the split so cleaning statistics never see val/test rows."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Download the SGCC dataset from "
            "github.com/henryRDlab/ElectricityTheftDetection (data.zip + data.z01 + data.z02, "
            "concatenate then unzip) and place data.csv there."
        )
    df = pd.read_csv(path)
    date_cols = [c for c in df.columns if c not in ("CONS_NO", "FLAG")]
    dates = pd.to_datetime(date_cols)
    order = np.argsort(dates.values)
    sorted_dates = dates[order]
    sorted_cols = [date_cols[i] for i in order]

    return SgccDataset(
        cons_no=df["CONS_NO"].to_numpy(),
        flag=df["FLAG"].to_numpy(dtype=int),
        dates=pd.DatetimeIndex(sorted_dates),
        kwh=df[sorted_cols].to_numpy(dtype=float),
    )


def validate_against_paper(data: SgccDataset) -> dict:
    """Checks this copy's shape and theft rate against the upstream README
    and commonly-cited SGCC statistics. Does not raise: callers decide what
    to do with a mismatch."""
    n, d = data.kwh.shape
    span = (data.dates.max() - data.dates.min()).days + 1
    theft_rate = float(data.flag.mean())
    return {
        "n_consumers": n,
        "n_consumers_matches_paper": n == EXPECTED_N_CONSUMERS,
        "n_day_columns": d,
        "n_day_columns_matches_expected": d == EXPECTED_N_DAYS,
        "date_span_days": span,
        "date_span_matches_paper": span == EXPECTED_SPAN_DAYS,
        "theft_rate": theft_rate,
        "theft_rate_within_1pt_of_expected": abs(theft_rate - EXPECTED_THEFT_RATE) < 0.01,
        "date_range": (str(data.dates.min().date()), str(data.dates.max().date())),
    }


def drop_all_missing_consumers(data: SgccDataset) -> tuple[SgccDataset, int]:
    """Drops consumers with zero non-missing readings (5 of them in this
    copy) — nothing can be imputed or engineered from an all-NaN row, and
    keeping them would force every downstream statistic to special-case
    them. Returns the filtered dataset and how many were dropped."""
    keep = ~np.isnan(data.kwh).all(axis=1)
    dropped = int((~keep).sum())
    filtered = SgccDataset(
        cons_no=data.cons_no[keep],
        flag=data.flag[keep],
        dates=data.dates,
        kwh=data.kwh[keep],
    )
    return filtered, dropped
