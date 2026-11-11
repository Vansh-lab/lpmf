"""sgcc.load: date-column sorting, paper validation, all-missing drop."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from lpmf.sgcc.load import (
    SgccDataset,
    drop_all_missing_consumers,
    load_raw,
    validate_against_paper,
)


def _write_csv(tmp_path, rows):
    path = tmp_path / "data.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def test_load_raw_sorts_date_columns_chronologically(tmp_path):
    # Columns deliberately out of chronological (but valid string-sort)
    # order, mirroring the real file's "2014/1/10" before "2014/1/2" quirk.
    csv = "CONS_NO,FLAG,2014/1/10,2014/1/2,2014/1/1\nC1,0,30,20,10\n"
    path = tmp_path / "data.csv"
    path.write_text(csv)
    data = load_raw(path)
    assert list(data.dates) == sorted(data.dates)
    assert data.kwh[0].tolist() == [10.0, 20.0, 30.0]


def test_load_raw_missing_file_gives_a_helpful_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="henryRDlab"):
        load_raw(tmp_path / "nope.csv")


def test_validate_against_paper_flags_mismatches(tmp_path):
    csv = "CONS_NO,FLAG,2014/1/1,2014/1/2\nC1,0,10,20\nC2,1,15,25\n"
    path = tmp_path / "data.csv"
    path.write_text(csv)
    data = load_raw(path)
    out = validate_against_paper(data)
    assert out["n_consumers"] == 2
    assert out["n_consumers_matches_paper"] is False  # tiny fixture, not the real 42,372
    assert out["theft_rate"] == pytest.approx(0.5)


def test_drop_all_missing_consumers():
    data = SgccDataset(
        cons_no=np.array(["A", "B", "C"]),
        flag=np.array([0, 1, 0]),
        dates=pd.DatetimeIndex(["2014-01-01", "2014-01-02"]),
        kwh=np.array([[1.0, 2.0], [np.nan, np.nan], [3.0, np.nan]]),
    )
    filtered, n_dropped = drop_all_missing_consumers(data)
    assert n_dropped == 1
    assert filtered.cons_no.tolist() == ["A", "C"]
    assert filtered.kwh.shape == (2, 2)
