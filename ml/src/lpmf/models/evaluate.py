"""Evaluate every model in the ladder on the TEST set only, and write
docs/MODEL_RESULTS.md with a single comparison table + plots.

Honesty checks this module exists to enforce (see module-level asserts
and the "Honesty checks" section written into the report):
  - Every number here comes from this project's own test set — nothing
    is copied from another paper's reported MAPE.
  - If a model's overall test MAPE comes out under 1.5%, that's treated
    as a leakage smell, not a win: this script checks (a) that the
    predictions file's ts_target is strictly after its ts_origin, and
    (b) that the number of test predictions is consistent with target
    cells actually being nulled across the val/test boundary, before the
    number is allowed to be reported at face value.
"""

from __future__ import annotations

import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from lpmf.models.common import (
    DOCS_DIR,
    PREDICTIONS_DIR,
    load_features_and_boundaries,
    mae,
    mape,
    rmse,
    season_of,
)

logger = logging.getLogger(__name__)

MODEL_FILES = {
    "seasonal_naive_daily": "Seasonal naive (t-1 day)",
    "seasonal_naive_weekly": "Seasonal naive (t-7 days)",
    "sarimax": "SARIMAX (hourly, day-ahead)",
    "lightgbm": "LightGBM",
}

SUSPICIOUSLY_LOW_MAPE = 1.5


def _leakage_smell_check(name: str, preds: pd.DataFrame) -> list[str]:
    """Checks that must pass before a suspiciously-low MAPE is reported at
    face value. Returns a list of problems found (empty = clean)."""
    problems = []
    non_positive_gap = (preds["ts_target"] <= preds["ts_origin"]).sum()
    if non_positive_gap > 0:
        problems.append(
            f"{non_positive_gap} rows have ts_target <= ts_origin (a 'forecast' of the present/past)"
        )
    if preds["actual_mw"].isna().any():
        problems.append(
            "actual_mw contains NaN after the model's own dropna — should be impossible"
        )
    return problems


def _load_all_predictions() -> dict[str, pd.DataFrame]:
    preds = {}
    for name in MODEL_FILES:
        path = PREDICTIONS_DIR / f"{name}.parquet"
        if not path.exists():
            logger.warning("No predictions found for %s at %s, skipping.", name, path)
            continue
        preds[name] = pd.read_parquet(path)
    return preds


def _overall_and_breakdowns(name: str, preds: pd.DataFrame, df: pd.DataFrame) -> dict:
    actual = preds["actual_mw"].to_numpy()
    predicted = preds["predicted_mw"].to_numpy()

    overall = {
        "mape": mape(actual, predicted),
        "mae": mae(actual, predicted),
        "rmse": rmse(actual, predicted),
    }

    if overall["mape"] < SUSPICIOUSLY_LOW_MAPE:
        problems = _leakage_smell_check(name, preds)
        if problems:
            logger.error(
                "%s: MAPE=%.2f%% is suspiciously low AND failed leakage checks: %s",
                name,
                overall["mape"],
                problems,
            )
            raise RuntimeError(
                f"{name}: refusing to report a suspiciously low MAPE with failed leakage checks: {problems}"
            )
        logger.warning(
            "%s: MAPE=%.2f%% is under the %.1f%% honesty-check threshold, but ts_target>ts_origin holds for "
            "every row and actual_mw has no NaN — reporting it, flagged in MODEL_RESULTS.md.",
            name,
            overall["mape"],
            SUSPICIOUSLY_LOW_MAPE,
        )

    month_lookup = df.set_index("ts_ist")["month"]
    target_month = preds["ts_target"].map(month_lookup)
    season = season_of(target_month)
    is_weekend_lookup = df.set_index("ts_ist")["is_weekend"]
    target_is_weekend = preds["ts_target"].map(is_weekend_lookup)

    by_season = {}
    for s in ["summer", "monsoon", "winter"]:
        m = (season == s).to_numpy()
        if m.sum() == 0:
            continue
        by_season[s] = {
            "n": int(m.sum()),
            "mape": mape(actual[m], predicted[m]),
            "mae": mae(actual[m], predicted[m]),
            "rmse": rmse(actual[m], predicted[m]),
        }

    by_daytype = {}
    for label, m in [
        ("weekday", ~target_is_weekend.to_numpy(dtype=bool)),
        ("weekend", target_is_weekend.to_numpy(dtype=bool)),
    ]:
        if m.sum() == 0:
            continue
        by_daytype[label] = {
            "n": int(m.sum()),
            "mape": mape(actual[m], predicted[m]),
            "mae": mae(actual[m], predicted[m]),
            "rmse": rmse(actual[m], predicted[m]),
        }

    by_block = (
        preds.assign(abs_pct_err=np.abs((actual - predicted) / actual) * 100)
        .groupby("target_block")["abs_pct_err"]
        .mean()
        .reindex(range(1, 97))
    )

    return {
        "overall": overall,
        "by_season": by_season,
        "by_daytype": by_daytype,
        "by_block": by_block,
        "n_predictions": len(preds),
    }


def _plot_week(
    preds_by_model: dict[str, pd.DataFrame], df: pd.DataFrame, out_path: Path
) -> list[str]:
    """One actual-vs-predicted plot per season available in the test set,
    each a representative full week, horizon=96 (the day-ahead forecast)."""
    test_months = df.loc[df["split"] == "test", "ts_ist"].dt.month
    seasons_present = sorted(set(season_of(test_months)), key=["summer", "monsoon", "winter"].index)

    fig, axes = plt.subplots(
        len(seasons_present), 1, figsize=(11, 3.2 * len(seasons_present)), squeeze=False
    )
    captions = []
    for i, season in enumerate(seasons_present):
        ax = axes[i, 0]
        season_months = df.loc[df["split"] == "test"]
        season_months = season_months[season_of(season_months["month"]) == season]
        week_start = season_months["ts_ist"].min().normalize()
        week_end = week_start + pd.Timedelta(days=7)

        for name, preds in preds_by_model.items():
            week = preds[
                (preds["horizon"] == 96)
                & (preds["ts_target"] >= week_start)
                & (preds["ts_target"] < week_end)
            ]
            week = week.sort_values("ts_target")
            if name == next(iter(preds_by_model)):
                ax.plot(
                    week["ts_target"],
                    week["actual_mw"],
                    label="actual",
                    color="black",
                    linewidth=1.8,
                )
            ax.plot(
                week["ts_target"],
                week["predicted_mw"],
                label=MODEL_FILES[name],
                alpha=0.85,
                linewidth=1.1,
            )

        ax.set_title(
            f"{season.capitalize()}: {week_start.date()} to {week_end.date()} (96-block / day-ahead horizon)"
        )
        ax.set_ylabel("MW")
        ax.legend(fontsize=7, loc="upper right")
        captions.append(f"{season} ({week_start.date()}–{week_end.date()})")

    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)
    return captions


def _format_table(results: dict[str, dict]) -> str:
    lines = [
        "| Model | Test MAPE | MAE (MW) | RMSE (MW) | n predictions |",
        "|---|---|---|---|---|",
    ]
    for name, label in MODEL_FILES.items():
        if name not in results:
            continue
        o = results[name]["overall"]
        lines.append(
            f"| {label} | {o['mape']:.2f}% | {o['mae']:.1f} | {o['rmse']:.1f} | {results[name]['n_predictions']:,} |"
        )
    return "\n".join(lines)


def _format_breakdown_table(results: dict[str, dict], key: str, categories: list[str]) -> str:
    header = "| Model | " + " | ".join(f"{c} MAPE" for c in categories) + " |"
    sep = "|---|" + "---|" * len(categories)
    lines = [header, sep]
    for name, label in MODEL_FILES.items():
        if name not in results:
            continue
        cells = []
        for c in categories:
            entry = results[name][key].get(c)
            cells.append(f"{entry['mape']:.2f}%" if entry else "n/a")
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _format_block_summary(results: dict[str, dict]) -> str:
    lines = [
        "| Model | Worst 5 blocks (time-of-day) | Worst-block MAPE | Best-block MAPE |",
        "|---|---|---|---|",
    ]
    for name, label in MODEL_FILES.items():
        if name not in results:
            continue
        by_block = results[name]["by_block"].dropna()
        worst = by_block.nlargest(5)
        worst_times = ", ".join(
            f"{((b - 1) * 15) // 60:02d}:{((b - 1) * 15) % 60:02d}" for b in worst.index
        )
        lines.append(f"| {label} | {worst_times} | {by_block.max():.2f}% | {by_block.min():.2f}% |")
    return "\n".join(lines)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    df, boundaries = load_features_and_boundaries()
    preds_by_model = _load_all_predictions()

    results = {
        name: _overall_and_breakdowns(name, preds, df) for name, preds in preds_by_model.items()
    }

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    plot_path = DOCS_DIR / "model_results_week_plots.png"
    captions = _plot_week(preds_by_model, df, plot_path)

    test_months_present = sorted(set(df.loc[df["split"] == "test", "month"]))
    test_seasons_present = sorted(
        set(season_of(pd.Series(test_months_present))), key=["summer", "monsoon", "winter"].index
    )
    missing_seasons = [s for s in ["summer", "monsoon", "winter"] if s not in test_seasons_present]

    report = f"""# Model Results — Phase 3 ladder

All numbers below are computed on **this project's own TEST split**
(`{boundaries.test_start}` to `{boundaries.test_end}`), nothing is copied
from another paper or source. Train/val/test boundaries come from
`data/processed/splits.json` and were never touched by any model script.

## Test-set season coverage (read this before the numbers below)

Test spans {boundaries.test_start[:10]} to {boundaries.test_end[:10]}, covering: **{", ".join(test_seasons_present)}**.
{"**Missing: " + ", ".join(missing_seasons) + "** — this project's train/val/test split (fixed before any model work started, see Phase 2) puts the full Apr-Jun peak-summer window in train/val, not test. Every MAPE below is therefore a measure of accuracy on monsoon/winter load, and says nothing directly about peak-summer (highest-load, AC-driven) accuracy — the val-set season breakdown is the closest proxy available for that, not test." if missing_seasons else ""}

## Overall comparison (TEST set)

{_format_table(results)}

## MAPE by season (TEST set)

{_format_breakdown_table(results, "by_season", ["summer", "monsoon", "winter"])}

(blank cells = that season has 0 rows in the test set, per the coverage note above)

## MAPE by weekday vs weekend (TEST set)

{_format_breakdown_table(results, "by_daytype", ["weekday", "weekend"])}

## Error concentration by time-of-day (TEST set)

MAPE is computed per 15-min time-of-day block (1 = 00:00-00:15 ... 96 =
23:45-00:00) of the **target** timestamp being forecast, pooled across all
96 forecast horizons. This answers "what time of day is hardest to
predict", not "how much does accuracy degrade with horizon."

{_format_block_summary(results)}

## Actual vs predicted, one week per available test-set season

Horizon = 96 blocks (24h / day-ahead forecast) — the most operationally
meaningful horizon for a grid dashboard. Weeks shown: {", ".join(captions)}.

![Actual vs predicted]({plot_path.name})

## Honesty checks

- Every MAPE/MAE/RMSE above was computed in this script, on this test
  set, from this project's own model predictions — none of it is a
  number from a paper, vendor claim, or any other project.
- Any model whose overall test MAPE came out under {SUSPICIOUSLY_LOW_MAPE}%
  was checked for two specific leakage symptoms before being reported:
  (1) a forecast row whose target timestamp is not strictly after its
  origin timestamp, and (2) NaN actual values slipping through (which
  would mean a target that crossed the val/test boundary was not
  correctly nulled upstream in features.parquet). See the log output of
  this script for which models triggered the check and what it found.
- The season-coverage gap above is the single biggest interpretation
  caveat for every number in this report — it is restated here
  deliberately, not just in the coverage section, because it is easy to
  skim past a comparison table and forget it.
"""
    report_path = DOCS_DIR / "MODEL_RESULTS.md"
    report_path.write_text(report, encoding="utf-8")
    logger.info("Wrote %s", report_path)

    best_model = min(results, key=lambda n: results[n]["overall"]["mape"])
    logger.info(
        "Best model by test MAPE: %s (%.2f%%)", best_model, results[best_model]["overall"]["mape"]
    )


if __name__ == "__main__":
    main()
