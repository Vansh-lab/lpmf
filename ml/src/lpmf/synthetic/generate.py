"""Parametric synthetic load generator for consumer categories Delhi SLDC's
aggregate feed has no per-category breakdown for: residential, commercial,
industrial, agricultural, EV charging.

This is explicitly a stand-in, not measured data — every row is tagged
data_source="synthetic_parametric" and is_synthetic=True (reusing the
Phase-0 provenance enum, see lpmf.provenance), and nothing here should be
read as "what Delhi's residential load actually is."

Model (per category, additive, matching the brief):

    load(t) = base + daily_pattern(t) + weekly_pattern(hour, dow)
              + heat_effect(heat_index) + noise + event_bumps

All terms are MW; `daily_pattern` and `weekly_pattern` are built to average
to ~0 over a day/week so `base` is the category's genuine mean load. The
time backbone (ts_ist, heat_index_c, is_holiday, dow, month, is_ipl_season)
is read from the real cleaned+joined frame, so the categories can be summed
and compared against the real aggregate on identical timestamps.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from lpmf.provenance import ProvenanceKind

logger = logging.getLogger(__name__)

RNG_SEED = 20260101  # fixed seed: synthetic output is reproducible, not re-rolled each run


def _wrapped_gaussian(hour: np.ndarray, center: float, width: float, amp: float) -> np.ndarray:
    """A Gaussian bump on a 24h wrapped clock (so a bump near midnight does
    not get artificially cut off at the 0h/24h boundary)."""
    d = np.abs(hour - center)
    d = np.minimum(d, 24 - d)
    return amp * np.exp(-0.5 * (d / width) ** 2)


def _center(shape: np.ndarray) -> np.ndarray:
    """Recentre a shape function to mean 0 so `base` carries the category's
    true average load."""
    return shape - shape.mean()


@dataclass(frozen=True)
class CategoryResult:
    name: str
    frame: pd.DataFrame


def _residential_daily(hour: np.ndarray) -> np.ndarray:
    # Bimodal, deliberately: a daytime/afternoon AC bump (dominant on hot
    # days, once heat_effect() is added on top of this) competing with an
    # evening lighting/entertainment peak (dominant on cooler days). A
    # single evening-only bump made the v1 model's peak land ~5h later
    # than Delhi's real aggregate, which actually peaks mid-afternoon on
    # the many hot days in the dataset — this shape plus heat_effect is
    # what lets which-peak-wins vary day to day instead of being fixed.
    shape = (
        _wrapped_gaussian(hour, center=15.0, width=2.8, amp=260)  # afternoon AC
        + _wrapped_gaussian(hour, center=21.5, width=2.2, amp=320)  # evening lighting/AC
        + _wrapped_gaussian(hour, center=8.0, width=1.3, amp=160)  # morning routine bump
        - _wrapped_gaussian(hour, center=4.0, width=1.8, amp=220)  # pre-dawn trough
    )
    return _center(shape)


def _commercial_daily(hour: np.ndarray) -> np.ndarray:
    # Plateau 10:00-22:00 (shops & offices), low overnight, with an
    # afternoon AC bump on top (malls/offices run heaviest cooling
    # 13:00-17:00, not just "on" uniformly through the plateau).
    plateau = 220 * (1 / (1 + np.exp(-(hour - 9.5)))) * (1 / (1 + np.exp(hour - 22.0)))
    afternoon_ac = _wrapped_gaussian(hour, center=15.0, width=2.5, amp=90)
    shape = plateau + afternoon_ac
    return _center(shape)


def _industrial_daily(hour: np.ndarray) -> np.ndarray:
    # Relatively flat (continuous process load), small dip on the
    # late-night shift (02:00-04:00) when the smallest crew runs.
    shape = -_wrapped_gaussian(hour, center=3.0, width=2.0, amp=60)
    return _center(shape)


def _agricultural_daily(hour: np.ndarray) -> np.ndarray:
    # Two pump-hour windows: early morning and evening irrigation.
    shape = _wrapped_gaussian(hour, center=5.5, width=1.6, amp=90) + _wrapped_gaussian(
        hour, center=19.5, width=1.6, amp=80
    )
    return _center(shape)


def _ev_daily(hour: np.ndarray) -> np.ndarray:
    # Home charging overnight after the evening commute, smaller
    # workplace-charging bump at midday.
    shape = _wrapped_gaussian(hour, center=21.0, width=3.0, amp=28) + _wrapped_gaussian(
        hour, center=13.0, width=2.5, amp=10
    )
    return _center(shape)


@dataclass(frozen=True)
class CategorySpec:
    name: str
    base_mw: float
    daily_fn: callable
    weekend_factor: float  # multiplier on daily_pattern amplitude for Sat/Sun
    sunday_dip_mw: float  # flat MW reduction on Sundays (industrial shift-down etc.)
    heat_cool_coef: float  # MW per degC of heat_index above 25degC (AC load)
    heat_heat_coef: float  # MW per degC of heat_index below 15degC (space heating)
    holiday_delta_mw: float  # flat MW shift on holidays (+ or -)
    ipl_evening_bump_mw: float  # extra MW 19:00-23:00 on IPL-season days
    noise_sd_mw: float
    monsoon_factor: float  # multiplier applied Jun-Sep (1.0 = no change)
    growth_per_year: float  # fractional growth in base_mw per year since dataset start (EV)


CATEGORY_SPECS = [
    CategorySpec(
        name="residential",
        base_mw=1800.0,
        daily_fn=_residential_daily,
        weekend_factor=1.08,
        sunday_dip_mw=0.0,
        heat_cool_coef=22.0,
        heat_heat_coef=6.0,
        holiday_delta_mw=40.0,  # people home -> slightly higher
        ipl_evening_bump_mw=25.0,
        noise_sd_mw=35.0,
        monsoon_factor=1.0,
        growth_per_year=0.0,
    ),
    CategorySpec(
        name="commercial",
        base_mw=1000.0,
        daily_fn=_commercial_daily,
        weekend_factor=0.9,
        sunday_dip_mw=90.0,
        heat_cool_coef=13.0,
        heat_heat_coef=2.0,
        holiday_delta_mw=-60.0,  # many offices/shops closed
        ipl_evening_bump_mw=8.0,  # restaurants/bars a little busier
        noise_sd_mw=25.0,
        monsoon_factor=1.0,
        growth_per_year=0.0,
    ),
    CategorySpec(
        name="industrial",
        base_mw=500.0,
        daily_fn=_industrial_daily,
        weekend_factor=0.85,
        sunday_dip_mw=180.0,  # strong Sunday dip
        heat_cool_coef=2.0,
        heat_heat_coef=0.0,
        holiday_delta_mw=-140.0,  # plant holidays
        ipl_evening_bump_mw=0.0,
        noise_sd_mw=15.0,
        monsoon_factor=1.0,
        growth_per_year=0.0,
    ),
    CategorySpec(
        name="agricultural",
        base_mw=150.0,
        daily_fn=_agricultural_daily,
        weekend_factor=1.0,
        sunday_dip_mw=0.0,
        heat_cool_coef=1.2,  # hotter -> more irrigation (outside monsoon)
        heat_heat_coef=0.0,
        holiday_delta_mw=0.0,  # farm operations do not follow holidays
        ipl_evening_bump_mw=0.0,
        noise_sd_mw=8.0,
        monsoon_factor=0.55,  # rain reduces pumping need Jun-Sep
        growth_per_year=0.0,
    ),
    CategorySpec(
        name="ev",
        base_mw=50.0,
        daily_fn=_ev_daily,
        weekend_factor=0.9,
        sunday_dip_mw=0.0,
        heat_cool_coef=0.3,  # battery thermal management, minor
        heat_heat_coef=0.1,
        holiday_delta_mw=5.0,  # more home charging on days off
        ipl_evening_bump_mw=0.0,
        noise_sd_mw=3.0,
        monsoon_factor=1.0,
        growth_per_year=0.35,  # EV adoption growing ~35%/yr over 2023-2026
    ),
]


def _heat_effect(heat_index_c: np.ndarray, cool_coef: float, heat_coef: float) -> np.ndarray:
    cooling = np.clip(heat_index_c - 25.0, 0, None) * cool_coef
    heating = np.clip(15.0 - heat_index_c, 0, None) * heat_coef
    return cooling + heating


def generate_category(
    backbone: pd.DataFrame, spec: CategorySpec, rng: np.random.Generator
) -> pd.DataFrame:
    ts = backbone["ts_ist"]
    hour = ts.dt.hour.to_numpy() + ts.dt.minute.to_numpy() / 60.0
    dow = backbone["dow"].to_numpy()
    month = backbone["month"].to_numpy()
    is_weekend = backbone["is_weekend"].to_numpy()
    is_holiday = backbone["is_holiday"].to_numpy()
    is_ipl = (
        backbone["is_ipl_season"].to_numpy()
        if "is_ipl_season" in backbone
        else np.zeros(len(backbone), dtype=bool)
    )
    heat_index = backbone["heat_index_c"].to_numpy()

    daily = spec.daily_fn(hour)
    weekly = np.where(is_weekend, daily * (spec.weekend_factor - 1.0), 0.0)
    weekly = weekly - np.where(dow == 6, spec.sunday_dip_mw, 0.0)  # dow==6 -> Sunday

    heat = _heat_effect(heat_index, spec.heat_cool_coef, spec.heat_heat_coef)
    holiday_term = np.where(is_holiday, spec.holiday_delta_mw, 0.0)

    evening = (hour >= 19.0) & (hour <= 23.0)
    ipl_term = np.where(is_ipl & evening, spec.ipl_evening_bump_mw, 0.0)

    monsoon = np.isin(month, [6, 7, 8, 9])
    season_mult = np.where(monsoon, spec.monsoon_factor, 1.0)

    years_since_start = (ts - ts.min()).dt.days.to_numpy() / 365.25
    growth_mult = (1.0 + spec.growth_per_year) ** years_since_start

    noise = rng.normal(0.0, spec.noise_sd_mw, size=len(backbone))

    base_term = spec.base_mw * growth_mult
    seasonal_daily = daily * season_mult
    load = base_term + seasonal_daily + weekly + heat + holiday_term + ipl_term + noise
    load = np.clip(load, 0.0, None)  # load cannot be physically negative

    out = pd.DataFrame(
        {
            # NOT ts.values: .values on a tz-aware Series silently drops
            # the tz (numpy has no tz-aware dtype), which broke reindexing
            # this against the tz-aware real backbone downstream.
            "ts_ist": ts.reset_index(drop=True),
            "block": backbone["block"].values,
            "date": backbone["date"].values,
            "category": spec.name,
            "load_mw": load,
            "data_source": "synthetic_parametric",
            "is_synthetic": True,
        }
    )
    assert out["is_synthetic"].all() and (out["data_source"] == "synthetic_parametric").all()
    return out


def generate_all(backbone: pd.DataFrame, seed: int = RNG_SEED) -> dict[str, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    results: dict[str, pd.DataFrame] = {}
    for spec in CATEGORY_SPECS:
        # A fresh child RNG per category keeps each category's noise
        # reproducible independent of iteration order.
        child_rng = np.random.default_rng(rng.integers(0, 2**32 - 1))
        results[spec.name] = generate_category(backbone, spec, child_rng)
    return results


# --- Shape-realism validation against the real aggregate -------------------


def _load_duration_curve(load: pd.Series) -> np.ndarray:
    """Normalised (0-1 of own peak) load duration curve: sorted load,
    descending, as a fraction of time."""
    sorted_load = np.sort(load.dropna().to_numpy())[::-1]
    peak = sorted_load[0] if len(sorted_load) and sorted_load[0] > 0 else 1.0
    return sorted_load / peak


def _ldc_shape_distance(real: np.ndarray, synth: np.ndarray, n_points: int = 200) -> float:
    """Mean absolute difference between the two normalised LDCs, resampled
    onto a common 0-1 time-fraction grid. 0 = identical shape, larger =
    more different. Scale-free (both curves normalised to their own peak
    first), so this compares *shape*, not absolute MW."""
    x_common = np.linspace(0, 1, n_points)
    real_frac = np.linspace(0, 1, len(real))
    synth_frac = np.linspace(0, 1, len(synth))
    real_interp = np.interp(x_common, real_frac, real)
    synth_interp = np.interp(x_common, synth_frac, synth)
    return float(np.mean(np.abs(real_interp - synth_interp)))


def _peak_timing(backbone_ts: pd.Series, load: pd.Series) -> tuple[float, float]:
    """Mean time-of-day (hour, 0-24) of the daily peak, and its circular
    std (hours), averaged across all days in the series. Days with no
    valid load at all (long-gap leftovers, never fabricated) are skipped
    rather than erroring — there is no "peak" to time on a day with no
    data."""
    df = pd.DataFrame({"ts": backbone_ts, "load": load}).dropna(subset=["load"])
    df["date"] = df["ts"].dt.date
    df["hour"] = df["ts"].dt.hour + df["ts"].dt.minute / 60.0
    peak_hours = df.loc[df.groupby("date")["load"].idxmax(), "hour"].to_numpy()
    # Circular mean/std on a 24h clock.
    angles = peak_hours / 24.0 * 2 * np.pi
    mean_angle = np.arctan2(np.mean(np.sin(angles)), np.mean(np.cos(angles)))
    mean_hour = (mean_angle / (2 * np.pi) * 24.0) % 24.0
    circ_std_hour = (
        np.sqrt(-2 * np.log(np.hypot(np.mean(np.sin(angles)), np.mean(np.cos(angles)))))
        / (2 * np.pi)
        * 24.0
    )
    return float(mean_hour), float(circ_std_hour)


def _lag1day_autocorr(load: pd.Series) -> float:
    return float(load.interpolate().autocorr(lag=96))


def compare_shape_to_real(backbone: pd.DataFrame, synthetic_sum: pd.Series) -> dict:
    """Compare the sum of all synthetic categories against the real
    aggregate on peak timing, load-duration-curve shape, and lag-1-day
    autocorrelation. Returns the raw numbers for both sides — this reports
    the comparison, it does not grade it."""
    real_load = backbone["load_mw"]

    real_peak_hour, real_peak_std = _peak_timing(backbone["ts_ist"], real_load)
    synth_peak_hour, synth_peak_std = _peak_timing(backbone["ts_ist"], synthetic_sum)

    real_ldc = _load_duration_curve(real_load)
    synth_ldc = _load_duration_curve(synthetic_sum)
    ldc_distance = _ldc_shape_distance(real_ldc, synth_ldc)

    real_acf = _lag1day_autocorr(real_load)
    synth_acf = _lag1day_autocorr(synthetic_sum)

    return {
        "real_peak_hour": real_peak_hour,
        "synthetic_peak_hour": synth_peak_hour,
        "peak_hour_diff_hours": abs(real_peak_hour - synth_peak_hour),
        "real_peak_timing_std_hours": real_peak_std,
        "synthetic_peak_timing_std_hours": synth_peak_std,
        "ldc_shape_mean_abs_diff": ldc_distance,
        "real_lag1day_autocorr": real_acf,
        "synthetic_lag1day_autocorr": synth_acf,
        "lag1day_autocorr_diff": abs(real_acf - synth_acf),
    }


def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    backbone = pd.read_parquet("data/processed/delhi_15min.parquet")
    # is_ipl_season isn't in the plain 15-min frame; pull it from features
    # if available, else fall back to all-False.
    try:
        features = pd.read_parquet(
            "data/processed/features.parquet", columns=["ts_ist", "is_ipl_season"]
        )
        backbone = backbone.merge(features, on="ts_ist", how="left")
        backbone["is_ipl_season"] = backbone["is_ipl_season"].fillna(False)
    except FileNotFoundError:
        backbone["is_ipl_season"] = False

    results = generate_all(backbone)

    # Reusing the Phase-0 provenance enum, not inventing a new tagging scheme.
    assert ProvenanceKind.SYNTHETIC.value == "SYNTHETIC"

    out_dir = Path("data/synthetic")
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in results.items():
        path = out_dir / f"{name}_load.parquet"
        frame.to_parquet(path, index=False)
        logger.info("Wrote %s: %d rows, mean %.1f MW", path, len(frame), frame["load_mw"].mean())

    synthetic_sum = sum(frame.set_index("ts_ist")["load_mw"] for frame in results.values())
    synthetic_sum = synthetic_sum.reindex(backbone["ts_ist"]).reset_index(drop=True)
    comparison = compare_shape_to_real(backbone, synthetic_sum)
    logger.info("Synthetic-vs-real shape comparison: %s", comparison)

    comparison_path = out_dir / "shape_comparison.json"
    import json

    comparison_path.write_text(json.dumps(comparison, indent=2))
    logger.info("Wrote %s", comparison_path)


if __name__ == "__main__":
    main()
