"""sgcc.split: consumer-level stratified 70/15/15, no consumer in two
splits — the explicit check the brief asked for."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from lpmf.sgcc.load import SgccDataset
from lpmf.sgcc.split import split_dataset, split_indices


def _fake_dataset(n: int, theft_rate: float, seed: int = 0) -> SgccDataset:
    rng = np.random.default_rng(seed)
    n_theft = int(round(n * theft_rate))
    flag = np.array([1] * n_theft + [0] * (n - n_theft))
    rng.shuffle(flag)
    return SgccDataset(
        cons_no=np.array([f"C{i}" for i in range(n)]),
        flag=flag,
        dates=pd.DatetimeIndex(pd.date_range("2014-01-01", periods=10)),
        kwh=rng.random((n, 10)),
    )


def test_every_consumer_appears_in_exactly_one_split():
    data = _fake_dataset(2000, 0.1)
    idx = split_indices(data.flag)
    all_idx = np.concatenate(list(idx.values()))
    assert len(all_idx) == data.cons_no.shape[0]
    assert len(set(all_idx.tolist())) == len(all_idx)  # no index repeated across splits


def test_split_sizes_are_approximately_70_15_15():
    data = _fake_dataset(2000, 0.1)
    idx = split_indices(data.flag)
    n = data.cons_no.shape[0]
    assert idx["train"].shape[0] == pytest.approx(0.70 * n, abs=2)
    assert idx["val"].shape[0] == pytest.approx(0.15 * n, abs=2)
    assert idx["test"].shape[0] == pytest.approx(0.15 * n, abs=2)


def test_split_is_stratified_on_theft_rate():
    data = _fake_dataset(3000, 0.1)
    splits = split_dataset(data)
    for d in splits.values():
        assert d.flag.mean() == pytest.approx(0.1, abs=0.02)


def test_split_is_reproducible_with_the_same_seed():
    data = _fake_dataset(1000, 0.1)
    a = split_indices(data.flag, seed=42)
    b = split_indices(data.flag, seed=42)
    for name in a:
        assert a[name].tolist() == b[name].tolist()


def test_split_cons_no_never_duplicated_across_splits():
    data = _fake_dataset(1500, 0.08)
    splits = split_dataset(data)
    seen = {}
    for name, d in splits.items():
        for cons_no in d.cons_no:
            assert cons_no not in seen, f"{cons_no} appears in both {seen[cons_no]} and {name}"
            seen[cons_no] = name
