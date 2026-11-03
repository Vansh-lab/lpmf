"""LightGBM: the main model. Multi-horizon (96 blocks ahead) forecast.

Design choice — ONE model with horizon as a feature, not 96 separate
models:
  - 96 separate models would multiply the Optuna search cost 96x (or force
    skipping search for most horizons, which isn't a real search).
  - A single model shares what it learns about load dynamics across
    horizons instead of relearning it 96 times independently from the
    same ~63k training rows.
  - The real risk of one shared model is that near-term lag features are
    highly informative at h=1 and nearly useless at h=96, while what
    matters for h=96 — the TARGET's own time-of-day/day-of-week/holiday
    status — is invisible if the model only sees the ORIGIN's calendar
    features. Both features.parquet's own cyclical encodings and
    is_holiday/is_weekend are computed for the ORIGIN timestamp, which is
    the wrong clock for a long-horizon target. We fix this here by also
    deriving target_* calendar features (what day/time is actually being
    predicted) and handing the model `horizon` directly, so it can learn
    horizon-dependent behaviour (e.g. "trust the lag less, trust
    target_is_holiday more, as horizon grows") instead of guessing it.
  - The same clock problem applies to load: load_lag_1day etc. describe the
    ORIGIN's block, while the strongest signal for a long-horizon target is
    the target block's own history (seasonal-naive is literally "load at
    target - 1 day"). TARGET_ALIGNED_FEATURES supplies that history
    (tlag_*: load at target - 1 day / - 1 week / trailing 4 weeks, all at or
    before the origin because h <= 96 blocks) plus the current load and its
    day-over-day shift.

Training data is built in long format: one row per (origin, horizon) pair
that has a real target (features.parquet already nulls any target that
crosses a split boundary — we just inherit that by using its target_h*
columns directly, so the leakage check for this model reduces to "did we
read target_h* instead of recomputing the future ourselves", which the
code below does).

Optuna searches hyperparameters on a VAL-only MAPE objective (never
touches test); the search runs on a random subsample of the long-format
train/val rows to keep a few dozen trials tractable, and the final model is then
retrained on the FULL long-format train set with the winning params.
"""

from __future__ import annotations

import json
import logging
import time

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd

from lpmf.features.build import BLOCKS_PER_DAY, HORIZONS
from lpmf.models.common import (
    ARTIFACTS_DIR,
    block_of_timestamp,
    load_features_and_boundaries,
    mape,
    save_predictions,
)

logger = logging.getLogger(__name__)
optuna.logging.set_verbosity(optuna.logging.INFO)

OPTUNA_STORAGE = f"sqlite:///{(ARTIFACTS_DIR / 'optuna_lightgbm.db').as_posix()}"
# Bump whenever the feature set or the cleaned data changes: trials scored on
# different inputs are not comparable, and load_if_exists would mix them.
OPTUNA_STUDY_NAME = "lightgbm_mape_search_v3"

ORIGIN_FEATURES = [
    "load_lag_1block",
    "load_lag_1day",
    "load_lag_1week",
    "load_avg_same_block_trailing_4w",
    "load_roll_mean_24h",
    "load_roll_std_24h",
    "temp_roll_mean_24h",
    "night_temp_c",
    "temp_c",
    "rh_pct",
    "dewpoint_c",
    "ghi_wm2",
    "wind_ms",
    "cloud_pct",
    "heat_index_c",
    "sin_hour",
    "cos_hour",
    "sin_dow",
    "cos_dow",
    "sin_doy",
    "cos_doy",
]
ORIGIN_FLAG_FEATURES = ["is_holiday", "is_weekend", "is_ipl_season"]
TARGET_CALENDAR_COLS = [
    "dow",
    "month",
    "is_weekend",
    "is_holiday",
    "sin_hour",
    "cos_hour",
    "is_ipl_season",
]
TARGET_ALIGNED_FEATURES = ["load_now", "tlag_1day", "tlag_1week", "tlag_4w_avg", "level_shift_1day"]

ALL_FEATURE_NAMES = (
    ORIGIN_FEATURES
    + ORIGIN_FLAG_FEATURES
    + [f"target_{c}" for c in TARGET_CALENDAR_COLS]
    + TARGET_ALIGNED_FEATURES
    + ["horizon"]
)

RNG_SEED = 20261101
DEFAULT_N_TRIALS = 25
SEARCH_SAMPLE_FRAC = 0.15


def _load_at(load: np.ndarray, positions: np.ndarray) -> np.ndarray:
    out = np.full(positions.shape, np.nan, dtype=np.float32)
    valid = positions >= 0
    out[valid] = load[positions[valid]]
    return out


def _target_aligned_features(
    load: np.ndarray, origin_positions: np.ndarray, target_positions: np.ndarray
) -> dict[str, np.ndarray]:
    """Long-format (origin-major) columns of TARGET_ALIGNED_FEATURES. Every
    position read is <= its origin: target - 96 blocks is at most the origin
    itself, since h <= 96."""
    n_h = target_positions.shape[1]
    week = 7 * BLOCKS_PER_DAY
    weekly = np.stack(
        [_load_at(load, target_positions - week * k).reshape(-1) for k in (1, 2, 3, 4)]
    )
    n_weeks = (~np.isnan(weekly)).sum(axis=0)
    weekly_sum = np.nansum(weekly, axis=0)
    del weekly

    load_now = np.repeat(load[origin_positions], n_h)
    return {
        "load_now": load_now,
        "tlag_1day": _load_at(load, target_positions - BLOCKS_PER_DAY).reshape(-1),
        "tlag_1week": _load_at(load, target_positions - week).reshape(-1),
        "tlag_4w_avg": np.where(n_weeks > 0, weekly_sum / np.maximum(n_weeks, 1), np.nan).astype(
            np.float32
        ),
        "level_shift_1day": load_now
        - np.repeat(_load_at(load, origin_positions - BLOCKS_PER_DAY), n_h),
    }


def build_long_format(df: pd.DataFrame, split_name: str) -> pd.DataFrame:
    """One row per (origin, horizon) pair for all origins in `split_name`,
    using features.parquet's own target_h* columns (already nulled across
    split boundaries) as the label — never recomputed here."""
    df = df.reset_index(drop=True)
    steps = df["ts_ist"].diff().iloc[1:]
    if not (steps == pd.Timedelta(minutes=15)).all():
        raise ValueError(
            "build_long_format needs a gap-free 15-min grid: the target-aligned "
            "lags are read by row offset, which is only a time offset on such a grid."
        )
    mask = (df["split"] == split_name).to_numpy()
    origin_positions = np.flatnonzero(mask)
    n_origin = len(origin_positions)
    horizons = np.array(HORIZONS)
    n_h = len(horizons)

    origin_block = df.loc[mask, ORIGIN_FEATURES + ORIGIN_FLAG_FEATURES].to_numpy(dtype=np.float32)
    long_features = np.repeat(origin_block, n_h, axis=0)

    horizon_long = np.tile(horizons, n_origin)

    target_cols = [f"target_h{h:02d}" for h in horizons]
    y_wide = df.loc[mask, target_cols].to_numpy(dtype=np.float32)
    y_long = y_wide.reshape(-1)

    target_positions = origin_positions[:, None] + horizons[None, :]
    n_total = len(df)
    safe_positions = np.clip(target_positions, 0, n_total - 1)
    in_range = (target_positions < n_total).reshape(-1)

    # .astype(float) matters: these columns are a mix of int/bool/float,
    # and DataFrame.to_numpy() on a mixed-dtype frame silently casts the
    # whole block to `object`, which LightGBM then rejects outright.
    calendar_lookup = df[TARGET_CALENDAR_COLS].astype(np.float32).to_numpy()
    target_calendar = calendar_lookup[safe_positions.reshape(-1)]

    target_aligned = _target_aligned_features(
        df["load_mw"].to_numpy(dtype=np.float32), origin_positions, target_positions
    )

    # Build the keep mask on raw numpy arrays and filter BEFORE assembling
    # the DataFrame: filtering a ~6M-row DataFrame with pandas boolean
    # indexing materializes a second full-size copy on top of the
    # unfiltered one, which is what drove this past available memory.
    # Slicing the numpy arrays first means only the (usually much smaller)
    # filtered arrays ever get wrapped in a DataFrame.
    keep = in_range & ~np.isnan(y_long)
    long_features = long_features[keep]
    target_calendar = target_calendar[keep]
    target_aligned = {name: values[keep] for name, values in target_aligned.items()}
    horizon_long = horizon_long[keep]
    y_long = y_long[keep]
    origin_long = np.repeat(origin_positions, n_h)[keep]

    long_df = pd.DataFrame(long_features, columns=ORIGIN_FEATURES + ORIGIN_FLAG_FEATURES)
    for i, col in enumerate(TARGET_CALENDAR_COLS):
        long_df[f"target_{col}"] = target_calendar[:, i]
    for name in TARGET_ALIGNED_FEATURES:
        long_df[name] = target_aligned[name]
    long_df["horizon"] = horizon_long
    long_df["actual_mw"] = y_long
    # take() keeps the tz-aware dtype; to_numpy() on a tz-aware column would
    # materialise one Python Timestamp object per row (millions of them).
    long_df["ts_origin"] = df["ts_ist"].take(origin_long).reset_index(drop=True)
    long_df["ts_target"] = long_df["ts_origin"] + pd.to_timedelta(
        long_df["horizon"] * 15, unit="min"
    )
    long_df["target_block"] = block_of_timestamp(long_df["ts_target"])
    return long_df.reset_index(drop=True)


def feature_matrix(long_df: pd.DataFrame) -> pd.DataFrame:
    """Model input in ALL_FEATURE_NAMES order. horizon is int64 for
    bookkeeping; cast it so LightGBM does not upcast the whole matrix to
    float64 (twice the memory of the float32 features)."""
    return long_df[ALL_FEATURE_NAMES].astype({"horizon": np.float32})


def _lgb_datasets(
    train_long: pd.DataFrame, val_long: pd.DataFrame
) -> tuple[lgb.Dataset, lgb.Dataset]:
    X_train = feature_matrix(train_long)
    y_train = train_long["actual_mw"]
    X_val = feature_matrix(val_long)
    y_val = val_long["actual_mw"]
    dtrain = lgb.Dataset(X_train, label=y_train)
    dval = lgb.Dataset(X_val, label=y_val, reference=dtrain)
    return dtrain, dval


def _mape_feval(y_pred: np.ndarray, data: lgb.Dataset) -> tuple[str, float, bool]:
    y_true = data.get_label()
    return "mape_pct", mape(y_true, y_pred), False


def _objective(trial: optuna.Trial, dtrain: lgb.Dataset, dval: lgb.Dataset) -> float:
    params = {
        "objective": "regression",
        "metric": "None",
        "verbosity": -1,
        "seed": RNG_SEED,
        # dtrain/dval are built once and reused across all trials, but each
        # trial suggests its own min_child_samples. feature_pre_filter
        # (on by default) bakes the FIRST trial's min_child_samples into
        # the Dataset's cached feature bins and then rejects later trials
        # that pick a different value, so it has to be off here.
        "feature_pre_filter": False,
        "num_leaves": trial.suggest_int("num_leaves", 16, 255, log=True),
        "max_depth": trial.suggest_int("max_depth", 3, 12),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
        "min_child_samples": trial.suggest_int("min_child_samples", 10, 200, log=True),
        "feature_fraction": trial.suggest_float("feature_fraction", 0.6, 1.0),
        "bagging_fraction": trial.suggest_float("bagging_fraction", 0.6, 1.0),
        "bagging_freq": 1,
        "lambda_l1": trial.suggest_float("lambda_l1", 1e-8, 10.0, log=True),
        "lambda_l2": trial.suggest_float("lambda_l2", 1e-8, 10.0, log=True),
    }
    booster = lgb.train(
        params,
        dtrain,
        num_boost_round=500,
        valid_sets=[dval],
        feval=_mape_feval,
        callbacks=[lgb.early_stopping(30, verbose=False)],
    )
    return booster.best_score["valid_0"]["mape_pct"]


def run_search(
    train_long: pd.DataFrame,
    val_long: pd.DataFrame,
    n_trials: int = DEFAULT_N_TRIALS,
    search_sample_frac: float = SEARCH_SAMPLE_FRAC,
) -> optuna.Study:
    """Bring the persistent study up to `n_trials` COMPLETED trials in total
    (resuming whatever already exists), not `n_trials` new ones."""
    rng = np.random.default_rng(RNG_SEED)
    train_sample = train_long.sample(
        frac=search_sample_frac, random_state=rng.integers(0, 2**32 - 1)
    )
    val_sample = val_long.sample(
        frac=min(1.0, search_sample_frac * 2), random_state=rng.integers(0, 2**32 - 1)
    )
    dtrain, dval = _lgb_datasets(train_sample, val_sample)

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    study = optuna.create_study(
        study_name=OPTUNA_STUDY_NAME,
        storage=OPTUNA_STORAGE,
        load_if_exists=True,
        direction="minimize",
    )
    # Offset the seed by the trials already stored: a resumed study with the
    # same seed replays the exact parameters of its first (random) trials.
    study.sampler = optuna.samplers.TPESampler(seed=RNG_SEED + len(study.trials))
    n_done = sum(1 for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE)
    n_remaining = max(0, n_trials - n_done)
    logger.info(
        "Optuna study '%s' at %s: %d/%d trials already completed, running %d more.",
        OPTUNA_STUDY_NAME,
        OPTUNA_STORAGE,
        n_done,
        n_trials,
        n_remaining,
    )

    def _progress_callback(study: optuna.Study, trial: optuna.trial.FrozenTrial) -> None:
        done_now = sum(1 for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE)
        logger.info(
            "trial %d/%d done (value=%.3f%%) -- best so far: %.3f%%",
            done_now,
            n_trials,
            trial.value if trial.value is not None else float("nan"),
            study.best_value,
        )

    start = time.time()
    if n_remaining > 0:
        study.optimize(
            lambda t: _objective(t, dtrain, dval),
            n_trials=n_remaining,
            callbacks=[_progress_callback],
        )
    logger.info(
        "Optuna search: %d new trials in %.1fs, best val MAPE=%.3f%%",
        n_remaining,
        time.time() - start,
        study.best_value,
    )
    return study


def train_final_model(
    train_long: pd.DataFrame, val_long: pd.DataFrame, best_params: dict
) -> lgb.Booster:
    dtrain, dval = _lgb_datasets(train_long, val_long)
    params = {
        "objective": "regression",
        "metric": "None",
        "verbosity": -1,
        "seed": RNG_SEED,
        "bagging_freq": 1,
        **best_params,
    }
    booster = lgb.train(
        params,
        dtrain,
        num_boost_round=3000,
        valid_sets=[dval],
        feval=_mape_feval,
        callbacks=[lgb.early_stopping(50, verbose=True), lgb.log_evaluation(100)],
    )
    return booster


def main(n_trials: int = DEFAULT_N_TRIALS) -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    df, boundaries = load_features_and_boundaries()

    logger.info("Building long-format train/val/test sets...")
    train_long = build_long_format(df, "train")
    val_long = build_long_format(df, "val")
    test_long = build_long_format(df, "test")
    logger.info(
        "train_long=%d val_long=%d test_long=%d rows",
        len(train_long),
        len(val_long),
        len(test_long),
    )

    logger.info("Running Optuna search (%d trials, val MAPE objective)...", n_trials)
    study = run_search(train_long, val_long, n_trials=n_trials)

    logger.info("Training final model on full train set with best params...")
    booster = train_final_model(train_long, val_long, study.best_params)

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    booster.save_model(str(ARTIFACTS_DIR / "lightgbm_model.txt"))

    search_record = {
        "search_space": {
            "num_leaves": "int[16,255] log",
            "max_depth": "int[3,12]",
            "learning_rate": "float[0.01,0.2] log",
            "min_child_samples": "int[10,200] log",
            "feature_fraction": "float[0.6,1.0]",
            "bagging_fraction": "float[0.6,1.0]",
            "lambda_l1": "float[1e-8,10] log",
            "lambda_l2": "float[1e-8,10] log",
        },
        "study_name": OPTUNA_STUDY_NAME,
        "n_trials_target": n_trials,
        "n_completed_trials": sum(
            1 for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE
        ),
        "search_sample_frac": SEARCH_SAMPLE_FRAC,
        "best_params": study.best_params,
        "best_val_mape_on_search_sample": study.best_value,
        "final_model_best_iteration": booster.best_iteration,
        "final_model_val_mape": booster.best_score["valid_0"]["mape_pct"],
        "features": ALL_FEATURE_NAMES,
    }
    (ARTIFACTS_DIR / "lightgbm_search.json").write_text(json.dumps(search_record, indent=2))
    logger.info(
        "Final model: best_iteration=%d, full-val MAPE=%.3f%%",
        booster.best_iteration,
        booster.best_score["valid_0"]["mape_pct"],
    )

    test_pred = booster.predict(feature_matrix(test_long), num_iteration=booster.best_iteration)
    test_predictions = test_long[
        ["ts_origin", "horizon", "ts_target", "target_block", "actual_mw"]
    ].copy()
    test_predictions["predicted_mw"] = test_pred
    path = save_predictions("lightgbm", test_predictions)

    test_mape = mape(
        test_predictions["actual_mw"].to_numpy(), test_predictions["predicted_mw"].to_numpy()
    )
    logger.info("LightGBM TEST MAPE: %.2f%%", test_mape)
    logger.info("Wrote %s (%d rows)", path, len(test_predictions))


if __name__ == "__main__":
    import argparse

    def _positive_int(value: str) -> int:
        n = int(value)
        if n < 1:
            raise argparse.ArgumentTypeError("must be >= 1")
        return n

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--n-trials",
        type=_positive_int,
        default=DEFAULT_N_TRIALS,
        help="target TOTAL of completed trials in the persistent Optuna study (resumes it)",
    )
    main(n_trials=parser.parse_args().n_trials)
