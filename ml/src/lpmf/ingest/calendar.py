"""Calendar features: India / Delhi public holidays (REAL, via `holidays`)."""

from __future__ import annotations

from datetime import date

import holidays as holidays_pkg
import pandas as pd


def build_calendar(start: date, end: date) -> pd.DataFrame:
    """Return a daily frame with `date`, `is_holiday`, `holiday_name` for
    every day in [start, end] inclusive, using India / Delhi (subdiv "DL")
    public holidays.
    """
    years = list(range(start.year, end.year + 1))
    in_holidays = holidays_pkg.country_holidays("IN", subdiv="DL", years=years)

    dates = pd.date_range(start, end, freq="D").date
    rows = []
    for d in dates:
        name = in_holidays.get(d)
        rows.append({"date": d, "is_holiday": name is not None, "holiday_name": name})
    return pd.DataFrame(rows)
