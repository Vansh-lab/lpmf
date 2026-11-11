"""Consumer-level stratified train/val/test split for the SGCC dataset.

Splits are by CONS_NO (every row of a consumer's series goes to exactly one
split — there is one row per consumer here, but the function is written so
that invariant is explicit and tested) and stratified on FLAG, so each
split keeps close to the overall theft rate. Fixed seed: reproducible, not
re-rolled per run.
"""

from __future__ import annotations

import numpy as np
from sklearn.model_selection import train_test_split

from lpmf.sgcc.load import SgccDataset

RNG_SEED = 20261111
TRAIN_FRAC, VAL_FRAC, TEST_FRAC = 0.70, 0.15, 0.15


def split_indices(flag: np.ndarray, seed: int = RNG_SEED) -> dict[str, np.ndarray]:
    """Row indices for train/val/test, stratified on `flag`, 70/15/15.
    Every index appears in exactly one split."""
    assert abs(TRAIN_FRAC + VAL_FRAC + TEST_FRAC - 1.0) < 1e-9
    n = flag.shape[0]
    idx = np.arange(n)

    train_idx, rest_idx = train_test_split(
        idx, test_size=(VAL_FRAC + TEST_FRAC), stratify=flag, random_state=seed
    )
    val_idx, test_idx = train_test_split(
        rest_idx,
        test_size=TEST_FRAC / (VAL_FRAC + TEST_FRAC),
        stratify=flag[rest_idx],
        random_state=seed,
    )
    return {"train": train_idx, "val": val_idx, "test": test_idx}


def split_dataset(data: SgccDataset, seed: int = RNG_SEED) -> dict[str, SgccDataset]:
    idx = split_indices(data.flag, seed)
    return {
        name: SgccDataset(
            cons_no=data.cons_no[rows],
            flag=data.flag[rows],
            dates=data.dates,
            kwh=data.kwh[rows],
        )
        for name, rows in idx.items()
    }
