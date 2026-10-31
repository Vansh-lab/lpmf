"""Strict chronological train/val/test split — never shuffled.

  train = start .. (end - 12 months)
  val   = next 6 months   (conformal calibration later)
  test  = final 6 months  (held out; must contain one full summer)

The resulting boundaries are persisted to data/processed/splits.json so
every later script reads them instead of recomputing (and risking drift).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class SplitBoundaries:
    train_start: str
    train_end: str
    val_start: str
    val_end: str
    test_start: str
    test_end: str

    def to_dict(self) -> dict:
        return asdict(self)


def compute_split_boundaries(ts: pd.Series) -> SplitBoundaries:
    start = ts.min()
    end = ts.max()

    test_start = end - pd.DateOffset(months=6)
    val_start = end - pd.DateOffset(months=12)
    train_start = start

    return SplitBoundaries(
        train_start=train_start.isoformat(),
        train_end=(val_start - pd.Timedelta(minutes=5)).isoformat(),
        val_start=val_start.isoformat(),
        val_end=(test_start - pd.Timedelta(minutes=5)).isoformat(),
        test_start=test_start.isoformat(),
        test_end=end.isoformat(),
    )


def save_split_boundaries(boundaries: SplitBoundaries, path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(boundaries.to_dict(), indent=2))


def load_split_boundaries(path: str | Path) -> SplitBoundaries:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"Split boundaries file not found at {p}. Run `python -m lpmf.pipeline "
            "--step split` first — downstream scripts must read boundaries from "
            "this file rather than recomputing them."
        )
    data = json.loads(p.read_text())
    return SplitBoundaries(**data)


def apply_split(df: pd.DataFrame, boundaries: SplitBoundaries) -> dict[str, pd.DataFrame]:
    ts = df["ts_ist"]
    train = df[(ts >= boundaries.train_start) & (ts <= boundaries.train_end)]
    val = df[(ts >= boundaries.val_start) & (ts <= boundaries.val_end)]
    test = df[(ts >= boundaries.test_start) & (ts <= boundaries.test_end)]
    return {"train": train, "val": val, "test": test}
