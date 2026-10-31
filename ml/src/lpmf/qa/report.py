"""Data-quality report: docs/DATA_QUALITY.md + a PNG panel figure.

Run via `python -m lpmf.pipeline --step qa` (after clean+join), or directly:
    python -m lpmf.qa.report --input data/processed/delhi_15min.parquet
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

KNOWN_ALL_TIME_PEAK_MW = 8748.0
KNOWN_ALL_TIME_PEAK_DATE = "2026-06-29"

SLOTS_PER_DAY_15MIN = 96


def _missing_pct(series: pd.Series) -> float:
    return float(series.isna().mean() * 100.0)


def compute_rows_expected_vs_present(df_raw_5min: pd.DataFrame) -> dict:
    expected = len(
        pd.date_range(df_raw_5min["ts_ist"].min(), df_raw_5min["ts_ist"].max(), freq="5min")
    )
    present = int(df_raw_5min["load_mw"].notna().sum())
    total_rows = len(df_raw_5min)
    return {
        "rows_expected": expected,
        "rows_present_non_null": present,
        "rows_in_frame": total_rows,
        "pct_missing_before_impute": (
            round(100.0 * (1 - present / expected), 3) if expected else None
        ),
    }


def compute_missing_after_impute(df_15min: pd.DataFrame) -> dict:
    still_missing = int(df_15min["load_mw"].isna().sum())
    total = len(df_15min)
    return {
        "rows_total_15min": total,
        "rows_still_missing_after_impute": still_missing,
        "pct_missing_after_impute": round(100.0 * still_missing / total, 3) if total else None,
    }


def plot_missing_calendar_heatmap(df_15min: pd.DataFrame, ax) -> None:
    df = df_15min.copy()
    df["date"] = pd.to_datetime(df["ts_ist"]).dt.date
    pivot = df.pivot_table(
        index="date", columns="block", values="load_mw", aggfunc=lambda s: s.isna().mean()
    )
    ax.imshow(pivot.values, aspect="auto", cmap="Reds", vmin=0, vmax=1)
    ax.set_title("Missing-data calendar heatmap (day x 15-min block)")
    ax.set_xlabel("Block (1-96)")
    ax.set_ylabel("Day index")


def plot_load_timeseries(df_15min: pd.DataFrame, ax) -> None:
    ax.plot(pd.to_datetime(df_15min["ts_ist"]), df_15min["load_mw"], linewidth=0.3)
    ax.set_title("Full load time series (15-min)")
    ax.set_ylabel("Load (MW)")


def plot_distribution(df_15min: pd.DataFrame, ax) -> None:
    ax.hist(df_15min["load_mw"].dropna(), bins=60)
    ax.set_title("Load distribution")
    ax.set_xlabel("Load (MW)")


def plot_boxplot_by_month(df_15min: pd.DataFrame, ax) -> None:
    df = df_15min.copy()
    df["month"] = pd.to_datetime(df["ts_ist"]).dt.month
    data = [df.loc[df["month"] == m, "load_mw"].dropna() for m in range(1, 13)]
    month_labels = [str(m) for m in range(1, 13)]
    try:
        # matplotlib >= 3.9 renamed `labels` -> `tick_labels`.
        ax.boxplot(data, tick_labels=month_labels)
    except TypeError:
        ax.boxplot(data, labels=month_labels)
    ax.set_title("Load by month (boxplot)")
    ax.set_xlabel("Month")


def _season(month: int) -> str:
    if month in (12, 1, 2):
        return "winter"
    if month in (3, 4, 5):
        return "summer"
    if month in (6, 7, 8, 9):
        return "monsoon"
    return "autumn"


def plot_avg_daily_curve_by_season(df_15min: pd.DataFrame, ax) -> None:
    df = df_15min.copy()
    df["month"] = pd.to_datetime(df["ts_ist"]).dt.month
    df["season"] = df["month"].apply(_season)
    for season, g in df.groupby("season"):
        curve = g.groupby("block")["load_mw"].mean()
        ax.plot(curve.index, curve.values, label=season)
    ax.set_title("Average daily load curve by season")
    ax.set_xlabel("Block (1-96)")
    ax.set_ylabel("Load (MW)")
    ax.legend(fontsize=6)


def plot_avg_daily_curve_weekday_weekend(df_15min: pd.DataFrame, ax) -> None:
    df = df_15min.copy()
    df["is_weekend"] = pd.to_datetime(df["ts_ist"]).dt.dayofweek.isin([5, 6])
    for is_weekend, g in df.groupby("is_weekend"):
        curve = g.groupby("block")["load_mw"].mean()
        label = "weekend" if is_weekend else "weekday"
        ax.plot(curve.index, curve.values, label=label)
    ax.set_title("Average daily load curve: weekday vs weekend")
    ax.set_xlabel("Block (1-96)")
    ax.legend(fontsize=6)


def compute_annual_peaks(df_15min: pd.DataFrame) -> pd.DataFrame:
    df = df_15min.copy()
    df["ts_ist"] = pd.to_datetime(df["ts_ist"])
    df["year"] = df["ts_ist"].dt.year
    idx = df.groupby("year")["load_mw"].idxmax()
    peaks = df.loc[idx.dropna(), ["year", "ts_ist", "load_mw"]].reset_index(drop=True)
    return peaks


def check_known_peak_discrepancy(peaks: pd.DataFrame, dataset_end: pd.Timestamp) -> str:
    known_peak_date = pd.Timestamp(KNOWN_ALL_TIME_PEAK_DATE, tz=dataset_end.tz)
    if dataset_end < known_peak_date:
        observed_max = peaks["load_mw"].max() if len(peaks) else float("nan")
        return (
            f"**DISCREPANCY**: the dataset ends at {dataset_end} which is *before* "
            f"the known Delhi all-time peak of {KNOWN_ALL_TIME_PEAK_MW} MW on "
            f"{KNOWN_ALL_TIME_PEAK_DATE}. The observed maximum in this dataset is "
            f"{observed_max:.1f} MW. This is expected and NOT silently adjusted for — "
            "the known peak simply falls outside the dataset's coverage window."
        )
    observed_max = peaks["load_mw"].max() if len(peaks) else float("nan")
    diff = observed_max - KNOWN_ALL_TIME_PEAK_MW
    return (
        f"Dataset covers the known peak date. Observed max {observed_max:.1f} MW vs "
        f"known peak {KNOWN_ALL_TIME_PEAK_MW} MW (diff {diff:+.1f} MW)."
    )


def plot_load_vs_heat_index(df_15min: pd.DataFrame, ax) -> float:
    df = df_15min.dropna(subset=["load_mw", "heat_index_c"])
    x = df["heat_index_c"].to_numpy()
    y = df["load_mw"].to_numpy()
    ax.scatter(x, y, s=1, alpha=0.2)
    if len(x) > 1:
        slope, intercept = np.polyfit(x, y, 1)
        xs = np.linspace(x.min(), x.max(), 100)
        ax.plot(xs, slope * xs + intercept, color="red", linewidth=1.5)
    else:
        slope = float("nan")
    ax.set_title(f"Load vs heat index (OLS slope = {slope:.2f} MW/°C)")
    ax.set_xlabel("Heat index (°C)")
    ax.set_ylabel("Load (MW)")
    return float(slope)


def compute_autocorrelation(df_15min: pd.DataFrame, lags: list[int]) -> dict[int, float]:
    series = df_15min.sort_values("ts_ist")["load_mw"].interpolate()
    out = {}
    for lag in lags:
        out[lag] = float(series.autocorr(lag=lag))
    return out


def generate_qa_report(
    df_5min_raw: pd.DataFrame,
    df_15min: pd.DataFrame,
    output_md: str | Path = "docs/DATA_QUALITY.md",
    output_png: str | Path = "docs/data_quality_panel.png",
) -> None:
    output_md = Path(output_md)
    output_png = Path(output_png)
    output_md.parent.mkdir(parents=True, exist_ok=True)

    before = compute_rows_expected_vs_present(df_5min_raw)
    after = compute_missing_after_impute(df_15min)

    fig, axes = plt.subplots(4, 2, figsize=(14, 20))
    plot_missing_calendar_heatmap(df_15min, axes[0, 0])
    plot_load_timeseries(df_15min, axes[0, 1])
    plot_distribution(df_15min, axes[1, 0])
    plot_boxplot_by_month(df_15min, axes[1, 1])
    plot_avg_daily_curve_by_season(df_15min, axes[2, 0])
    plot_avg_daily_curve_weekday_weekend(df_15min, axes[2, 1])
    slope = plot_load_vs_heat_index(df_15min, axes[3, 0])
    axes[3, 1].axis("off")
    fig.tight_layout()
    fig.savefig(output_png, dpi=120)
    plt.close(fig)

    peaks = compute_annual_peaks(df_15min)
    dataset_end = pd.to_datetime(df_15min["ts_ist"]).max()
    peak_note = check_known_peak_discrepancy(peaks, dataset_end)

    acf = compute_autocorrelation(df_15min, lags=[1, 96, 672])

    peaks_table = "\n".join(
        f"| {int(r.year)} | {r.ts_ist} | {r.load_mw:.1f} |" for r in peaks.itertuples()
    )

    md = f"""# Data Quality Report

Generated by `lpmf.qa.report`. See `{output_png.name}` for the plot panel.

## Rows expected vs present (before imputation, 5-min raw)

| Metric | Value |
|---|---|
| Rows expected (complete 5-min grid) | {before['rows_expected']} |
| Rows present (non-null load) | {before['rows_present_non_null']} |
| % missing before imputation | {before['pct_missing_before_impute']}% |

## Missing after imputation (15-min)

| Metric | Value |
|---|---|
| Rows total (15-min) | {after['rows_total_15min']} |
| Rows still missing (long gaps, left as NaN) | {after['rows_still_missing_after_impute']} |
| % missing after imputation | {after['pct_missing_after_impute']}% |

## Annual peaks

| Year | Timestamp | Peak load (MW) |
|---|---|---|
{peaks_table}

{peak_note}

## Load vs heat index

OLS slope (β): **{slope:.3f} MW/°C** — this is the β used on the Weather Impact page.

## Autocorrelation

| Lag | Description | ACF |
|---|---|---|
| 1 block | 15 min | {acf[1]:.4f} |
| 96 blocks | 1 day | {acf[96]:.4f} |
| 672 blocks | 1 week | {acf[672]:.4f} |
"""
    output_md.write_text(md, encoding="utf-8")
    logger.info("Wrote QA report to %s and %s", output_md, output_png)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the LPMF data quality report.")
    parser.add_argument(
        "--input-5min",
        default="data/interim/delhi_5min_raw.parquet",
        help="The true raw (pre-cleaning) 5-min frame, used for the before-imputation stats.",
    )
    parser.add_argument("--input-15min", default="data/processed/delhi_15min.parquet")
    parser.add_argument("--output-md", default="docs/DATA_QUALITY.md")
    parser.add_argument("--output-png", default="docs/data_quality_panel.png")
    args = parser.parse_args()

    df_5min = pd.read_parquet(args.input_5min)
    df_15min = pd.read_parquet(args.input_15min)
    generate_qa_report(df_5min, df_15min, args.output_md, args.output_png)


if __name__ == "__main__":
    main()
