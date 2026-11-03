"""save_predictions refuses timestamps that lost their IST timezone."""

from __future__ import annotations

import pandas as pd
import pytest

from lpmf.models.common import save_predictions


def test_save_predictions_rejects_naive_utc_ts_target():
    ts = pd.date_range("2025-07-13", periods=2, freq="15min", tz="Asia/Kolkata")
    preds = pd.DataFrame(
        {
            "ts_origin": ts,
            "horizon": [1, 1],
            # What `Series.values` produces from tz-aware IST timestamps.
            "ts_target": ts.tz_convert(None),
            "target_block": [1, 2],
            "actual_mw": [1.0, 2.0],
            "predicted_mw": [1.0, 2.0],
        }
    )
    with pytest.raises(ValueError, match="ts_target must be tz-aware Asia/Kolkata"):
        save_predictions("should_not_be_written", preds)
