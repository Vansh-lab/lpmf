"""Feature-importance and event-flag diagnostics for the trained LightGBM
model, compared against seasonal-naive.

Three questions, answered separately:
  1. What does the model lean on? Gain importance + mean |SHAP| (LightGBM's
     built-in TreeSHAP via pred_contrib), overall and per horizon bucket.
  2. Do the event flags carry real signal in the DATA, independent of the
     model? Model-free effect sizes: holiday load vs the same block one week
     earlier, and IPL-window evening uplift vs same-month non-IPL days.
  3. Where does the model lose to naive? Test MAPE for LightGBM vs
     seasonal_naive_daily by horizon bucket and by target-is-holiday.

SHAP is computed on VAL, not test: the test split contains no IPL-season
rows at all, so IPL's contribution can't be seen there.

Question 3 reads TEST predictions. Use it for final reporting only: every
design decision taken from it spends the test set as a holdout.
"""

from __future__ import annotations

import json
import logging

import lightgbm as lgb
import pandas as pd

from lpmf.models.common import ARTIFACTS_DIR, load_features_and_boundaries, load_predictions
from lpmf.models.lightgbm import (
    ALL_FEATURE_NAMES,
    RNG_SEED,
    TARGET_ALIGNED_FEATURES,
    build_long_format,
    feature_matrix,
)

logger = logging.getLogger(__name__)

# TreeSHAP costs a few ms per row; 50k rows already pins mean |SHAP| down.
SHAP_SAMPLE_ROWS = 50_000
HORIZON_BUCKETS = [
    (1, 4, "h01-04 (<=1h)"),
    (5, 24, "h05-24 (1-6h)"),
    (25, 48, "h25-48 (6-12h)"),
    (49, 96, "h49-96 (12-24h)"),
]
EVENING_BLOCKS = range(79, 93)  # 19:30-23:00, the IPL night-match window
FEATURE_GROUPS = {
    "origin load lags/rolling": [
        f for f in ALL_FEATURE_NAMES if f.startswith("load_") and f not in TARGET_ALIGNED_FEATURES
    ],
    "target-aligned load": TARGET_ALIGNED_FEATURES,
    "weather": [
        "temp_roll_mean_24h",
        "night_temp_c",
        "temp_c",
        "rh_pct",
        "dewpoint_c",
        "ghi_wm2",
        "wind_ms",
        "cloud_pct",
        "heat_index_c",
    ],
    "origin calendar": [
        "sin_hour",
        "cos_hour",
        "sin_dow",
        "cos_dow",
        "sin_doy",
        "cos_doy",
        "is_holiday",
        "is_weekend",
        "is_ipl_season",
    ],
    "target calendar": [f for f in ALL_FEATURE_NAMES if f.startswith("target_")],
    "horizon": ["horizon"],
}


def _bucket(h: pd.Series) -> pd.Series:
    out = pd.Series(index=h.index, dtype=object)
    for lo, hi, name in HORIZON_BUCKETS:
        out[(h >= lo) & (h <= hi)] = name
    return out


def _pct(s: pd.Series) -> pd.Series:
    return (100 * s / s.sum()).round(2)


def gain_and_shap(booster: lgb.Booster, val_long: pd.DataFrame) -> dict:
    gain = pd.Series(booster.feature_importance("gain"), index=booster.feature_name())

    sample = val_long.sample(n=min(SHAP_SAMPLE_ROWS, len(val_long)), random_state=RNG_SEED)
    contrib = booster.predict(feature_matrix(sample), pred_contrib=True)
    shap_df = pd.DataFrame(contrib[:, :-1], columns=ALL_FEATURE_NAMES, index=sample.index)
    mean_abs = shap_df.abs().mean()

    by_bucket = {}
    buckets = _bucket(sample["horizon"])
    for _, _, name in HORIZON_BUCKETS:
        rows = shap_df[buckets == name].abs().mean()
        by_bucket[name] = {
            g: round(float(100 * rows[cols].sum() / rows.sum()), 2)
            for g, cols in FEATURE_GROUPS.items()
        }

    # How much the model actually moves its prediction for flagged rows,
    # in MW and as % of actual load: the model's "learned effect size".
    flag_shap = {}
    for flag in [
        "target_is_holiday",
        "target_is_ipl_season",
        "is_holiday",
        "is_ipl_season",
        "target_is_weekend",
    ]:
        on = sample[flag] == 1
        if on.sum() == 0:
            flag_shap[flag] = {"n_rows": 0}
            continue
        mw = shap_df.loc[on, flag]
        flag_shap[flag] = {
            "n_rows": int(on.sum()),
            "mean_shap_mw_when_on": round(float(mw.mean()), 1),
            "mean_shap_pct_of_load_when_on": round(
                float(100 * (mw / sample.loc[on, "actual_mw"]).mean()), 2
            ),
            "mean_shap_mw_when_off": round(float(shap_df.loc[~on, flag].mean()), 1),
        }

    return {
        "gain_pct": _pct(gain).sort_values(ascending=False).to_dict(),
        "mean_abs_shap_mw": mean_abs.round(1).sort_values(ascending=False).to_dict(),
        "shap_group_share_pct_by_horizon": by_bucket,
        "flag_shap": flag_shap,
    }


def model_free_flag_effects(df: pd.DataFrame) -> dict:
    """Effect sizes measured on train+val load data, no model involved."""
    d = df[
        (df["split"] != "test") & ~df["imputed"].astype(bool) & ~df["is_synthetic"].astype(bool)
    ].copy()
    d["wow_dev_pct"] = 100 * (d["load_mw"] / d["load_lag_1week"] - 1)

    # Holiday: same block one week earlier is (almost always) a normal day,
    # so deviation on holidays minus deviation on normal days = holiday effect.
    # The baseline is per (year, month): in Mar-May load grows week over week
    # with the heat, which otherwise shows up as a fake positive holiday effect.
    d["ym"] = pd.to_datetime(d["date"]).dt.to_period("M")
    base_by_ym = d[d["is_holiday"] == 0].groupby("ym")["wow_dev_pct"].mean()
    d["effect_pct"] = d["wow_dev_pct"] - d["ym"].map(base_by_ym)
    hol = d[d["is_holiday"] == 1]
    per_holiday = (
        hol.groupby("holiday_name")["effect_pct"]
        .agg(["mean", "count"])
        .assign(
            effect_pct=lambda x: x["mean"].round(2), n_days=lambda x: (x["count"] / 96).round(1)
        )[["effect_pct", "n_days"]]
        .sort_values("effect_pct")
    )

    # IPL: the season window coincides with Delhi's summer ramp, so a raw
    # season-on vs season-off comparison just measures summer. Instead look
    # at evening share of daily load (match hours), and only within the same
    # months (Mar-Jun) so season-on and season-off days share a climate.
    m = d[d["month"].isin([3, 4, 5, 6])].copy()
    daily_mean = m.groupby("date")["load_mw"].transform("mean")
    m["rel_load"] = m["load_mw"] / daily_mean
    ev = (
        m[m["block"].isin(EVENING_BLOCKS)]
        .groupby(["date", "is_ipl_season"])["rel_load"]
        .mean()
        .reset_index()
    )
    ipl_on = ev.loc[ev["is_ipl_season"] == 1, "rel_load"]
    ipl_off = ev.loc[ev["is_ipl_season"] == 0, "rel_load"]

    return {
        "holiday_overall_effect_pct": round(float(hol["effect_pct"].mean()), 2),
        "holiday_n_days": round(len(hol) / 96, 1),
        "per_holiday_effect_pct": per_holiday.to_dict(orient="index"),
        "ipl_evening_rel_load_on": round(float(ipl_on.mean()), 4),
        "ipl_evening_rel_load_off": round(float(ipl_off.mean()), 4),
        "ipl_evening_uplift_pct": round(float(100 * (ipl_on.mean() / ipl_off.mean() - 1)), 2),
        "ipl_n_days_on": int(len(ipl_on)),
        "ipl_n_days_off": int(len(ipl_off)),
    }


def error_breakdown(df: pd.DataFrame) -> dict:
    lgbm = load_predictions("lightgbm")
    naive = load_predictions("seasonal_naive_daily")
    key = ["ts_origin", "horizon"]
    j = lgbm[key + ["actual_mw", "predicted_mw"]].merge(
        naive[key + ["predicted_mw"]].rename(columns={"predicted_mw": "naive_mw"}), on=key
    )
    j["ape_lgbm"] = 100 * (j["actual_mw"] - j["predicted_mw"]).abs() / j["actual_mw"]
    j["ape_naive"] = 100 * (j["actual_mw"] - j["naive_mw"]).abs() / j["actual_mw"]
    j["bucket"] = _bucket(j["horizon"])

    target_ts = j["ts_origin"] + pd.to_timedelta(j["horizon"] * 15, unit="min")
    holiday_by_ts = df.set_index("ts_ist")["is_holiday"]
    j["target_is_holiday"] = target_ts.map(holiday_by_ts).fillna(0).astype(int)

    by_bucket = j.groupby("bucket")[["ape_lgbm", "ape_naive"]].mean().round(3)
    by_h = j.groupby("horizon")[["ape_lgbm", "ape_naive"]].mean()
    by_hol = j.groupby("target_is_holiday")[["ape_lgbm", "ape_naive"]].mean().round(3)
    selected = [h for h in (1, 2, 4, 8, 16, 24, 32, 48, 64, 80, 96) if h in by_h.index]
    return {
        "n_joined_rows": int(len(j)),
        "overall": {
            "lightgbm": round(float(j["ape_lgbm"].mean()), 3),
            "naive_daily": round(float(j["ape_naive"].mean()), 3),
        },
        "by_horizon_bucket": by_bucket.to_dict(orient="index"),
        "by_selected_horizon": by_h.loc[selected].round(3).to_dict(orient="index"),
        "by_target_is_holiday": by_hol.to_dict(orient="index"),
        "horizons_where_naive_wins": [
            int(h) for h in by_h.index[by_h["ape_naive"] < by_h["ape_lgbm"]]
        ],
    }


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    df, _ = load_features_and_boundaries()
    booster = lgb.Booster(model_file=str(ARTIFACTS_DIR / "lightgbm_model.txt"))
    if booster.feature_name() != ALL_FEATURE_NAMES:
        raise ValueError(
            "lightgbm_model.txt was trained on a different feature list than ALL_FEATURE_NAMES; "
            "retrain it (python -m lpmf.models.lightgbm) before running diagnostics."
        )

    logger.info("Test error breakdown (LightGBM vs seasonal_naive_daily)...")
    errors = error_breakdown(df)
    logger.info("Model-free flag effect sizes...")
    effects = model_free_flag_effects(df)
    logger.info("Building val long-format for SHAP...")
    val_long = build_long_format(df, "val")
    importance = gain_and_shap(booster, val_long)

    report = {"errors": errors, "flag_effects_model_free": effects, "importance": importance}
    out = ARTIFACTS_DIR / "lightgbm_importance.json"
    out.write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps(report, indent=2, default=str))
    logger.info("Wrote %s", out)


if __name__ == "__main__":
    main()
