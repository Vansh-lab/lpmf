"""Phase 4b: TreeSHAP explanations of the final LightGBM for four test days.

Each day is explained as a day-ahead forecast: origin = 23:45 the evening
before, horizons 1..96 = the 96 blocks of the day itself. That is one
explained row per block of the day (96 rows per day).

Days (picked by rule from the TEST split, not by looking at errors):
  hot_summer -- highest-heat-index complete non-holiday day. The test window
                has no Mar-Jun, so this is the late-July monsoon heat peak,
                not a true pre-monsoon scorcher.
  normal     -- non-holiday weekday whose mean load is closest to the test median.
  festival   -- Diwali (2025-10-20).
  oct_nov_evening -- non-holiday weekday in 21 Oct - 20 Nov whose evening
                (18:00-23:45) mean load is closest to the median of that
                set; the evening is highlighted and the waterfall is taken at
        f"{name} {day}: peak block {int(hh):02d}:{int(hh % 1 * 60):02d} "
        f"(h={int(rows['horizon'].iloc[k])})"

Outputs under models/artifacts/shap_examples/:
  <day>.png          forecast+band, mean |SHAP| top features, SHAP-by-hour lines,
                     waterfall at the chosen block
  <day>_shap.parquet 96 x 37 SHAP matrix (+ base value, prediction, actual)
  index.json         the selected dates and the additivity check
"""

from __future__ import annotations

import json
import logging

import lightgbm as lgb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import shap  # noqa: E402

from lpmf.models.common import ARTIFACTS_DIR, load_features_and_boundaries  # noqa: E402
from lpmf.models.conformal import BANDS_PATH, MODEL_PATH  # noqa: E402
from lpmf.models.lightgbm import ALL_FEATURE_NAMES, build_long_format, feature_matrix  # noqa: E402

logger = logging.getLogger(__name__)
OUT_DIR = ARTIFACTS_DIR / "shap_examples"
DIWALI = pd.Timestamp("2025-10-20").date()


def select_days(df: pd.DataFrame) -> dict[str, tuple]:
    t = df[df["split"] == "test"]
    g = t.groupby("date").agg(
        n=("load_mw", "count"),
        mean=("load_mw", "mean"),
        hi=("heat_index_c", "max"),
        hol=("is_holiday", "max"),
        wk=("is_weekend", "max"),
    )
    g = g[g["n"] == 96]
    plain = g[~g["hol"]]
    weekdays = plain[~plain["wk"]]
    hot = plain["hi"].idxmax()
    normal = (weekdays["mean"] - g["mean"].median()).abs().idxmin()

    ev = t[t["ts_ist"].dt.hour >= 18].groupby("date")["load_mw"].mean()
    dates = pd.to_datetime(pd.Series(weekdays.index))
    window = weekdays.index[((dates >= "2025-10-21") & (dates <= "2025-11-20")).to_numpy()]
    ev = ev.loc[window]
    evening = (ev - ev.median()).abs().idxmin()
    return {
        "hot_summer": (hot, None),
        "normal": (normal, None),
        "festival": (DIWALI, None),
        "oct_nov_evening": (evening, "evening"),
    }


def day_rows(test_long: pd.DataFrame, day) -> pd.DataFrame:
    origin = pd.Timestamp(day).tz_localize("Asia/Kolkata") - pd.Timedelta(minutes=15)
    rows = test_long[test_long["ts_origin"] == origin].sort_values("horizon")
    if len(rows) != 96:
        raise ValueError(f"{day}: expected 96 horizons from origin {origin}, got {len(rows)}")
    return rows


def plot_day(name, day, rows, bands, sv, base, focus, out_path) -> int:
    hours = rows["ts_target"].dt.hour + rows["ts_target"].dt.minute / 60
    pred = base + sv.sum(axis=1)
    fig = plt.figure(figsize=(15, 9))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.1])

    ax = fig.add_subplot(gs[0, :])
    ax.fill_between(
        hours, bands["lower_mw"], bands["upper_mw"], alpha=0.25, label="80% conformal band"
    )
    ax.plot(hours, rows["actual_mw"], "k", lw=1.6, label="actual")
    ax.plot(hours, pred, "C3", lw=1.6, label="forecast")
    if focus == "evening":
        ax.axvspan(18, 24, color="C1", alpha=0.12, label="evening (18-24h)")
    ape = float(np.mean(np.abs(pred - rows["actual_mw"]) / rows["actual_mw"]) * 100)
    ax.set_title(f"{name}: {day}  (day-ahead from 23:45 prior evening, MAPE {ape:.2f}%)")
    ax.set_xlabel("target hour (IST)")
    ax.set_ylabel("MW")
    ax.legend(ncol=4, loc="upper left")

    mean_abs = np.abs(sv).mean(axis=0)
    top = np.argsort(mean_abs)[::-1][:10]
    ax = fig.add_subplot(gs[1, 0])
    ax.barh([ALL_FEATURE_NAMES[i] for i in top][::-1], mean_abs[top][::-1], color="C0")
    ax.set_title("mean |SHAP| over the day's 96 blocks (MW)")

    ax = fig.add_subplot(gs[1, 1])
    for i in top[:6]:
        ax.plot(hours, sv[:, i], lw=1.3, label=ALL_FEATURE_NAMES[i])
    ax.axhline(0, color="k", lw=0.6)
    if focus == "evening":
        ax.axvspan(18, 24, color="C1", alpha=0.12)
    ax.set_title("signed SHAP by target hour (top 6)")
    ax.set_xlabel("target hour (IST)")
    ax.legend(fontsize=7, ncol=2)

    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)

    if focus == "evening":
        cand = np.flatnonzero((hours >= 18).to_numpy())
    else:
        cand = np.arange(len(hours))
    k = int(cand[np.argmax(pred[cand])])
    expl = shap.Explanation(
        values=sv[k],
        base_values=base,
        data=rows[ALL_FEATURE_NAMES].iloc[k].to_numpy(dtype=float),
        feature_names=ALL_FEATURE_NAMES,
    )
    # shap.plots.waterfall manages its own figure, so it is saved separately.
    shap.plots.waterfall(expl, max_display=10, show=False)
    hh = hours.iloc[k]
    plt.title(
        f"{name} {day}: peak block {int(hh):02d}:{int(hh % 1 * 60):02d} "
        f"(h={int(rows['horizon'].iloc[k])})"
    )
    plt.gcf().savefig(out_path.with_name(f"{name}_waterfall.png"), dpi=110, bbox_inches="tight")
    plt.close("all")
    return k


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    df, _ = load_features_and_boundaries()
    booster = lgb.Booster(model_file=str(MODEL_PATH))
    explainer = shap.TreeExplainer(booster)
    base = float(np.ravel(explainer.expected_value)[0])
    picks = select_days(df)
    test_long = build_long_format(df, "test")
    bands_all = pd.read_parquet(BANDS_PATH)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    index: dict = {"base_value_mw": base, "days": {}}
    for name, (day, focus) in picks.items():
        rows = day_rows(test_long, day).reset_index(drop=True)
        X = feature_matrix(rows)
        sv = explainer.shap_values(X)
        pred = booster.predict(X, num_iteration=booster.best_iteration)
        err = float(np.abs(base + sv.sum(axis=1) - pred).max())
        b = rows[["ts_origin", "horizon"]].merge(bands_all, on=["ts_origin", "horizon"], how="left")
        assert len(b) == 96 and b["lower_mw"].notna().all()
        k = plot_day(name, day, rows, b, sv, base, focus, OUT_DIR / f"{name}.png")
        out = pd.DataFrame(sv, columns=ALL_FEATURE_NAMES)
        # "horizon" is itself a feature column (holding its SHAP value), so the
        # block identifier gets a different name.
        out.insert(0, "block_horizon", rows["horizon"].to_numpy())
        out["base_value"] = base
        out["predicted_mw"] = pred
        out["actual_mw"] = rows["actual_mw"].to_numpy()
        out.to_parquet(OUT_DIR / f"{name}_shap.parquet", index=False)
        mean_abs = pd.Series(np.abs(sv).mean(axis=0), index=ALL_FEATURE_NAMES).sort_values(
            ascending=False
        )
        index["days"][name] = {
            "date": str(day),
            "max_additivity_error_mw": err,
            "mape_pct": float(np.mean(np.abs(pred - rows["actual_mw"]) / rows["actual_mw"]) * 100),
            "waterfall_horizon": int(rows["horizon"].iloc[k]),
            "top_mean_abs_shap": {k_: round(float(v), 1) for k_, v in mean_abs.head(8).items()},
        }
        logger.info(
            "%s %s additivity err %.2e MW; top: %s", name, day, err, list(mean_abs.index[:4])
        )
    (OUT_DIR / "index.json").write_text(json.dumps(index, indent=2))


if __name__ == "__main__":
    main()
