# LightGBM — Phase 3 model results

Final model: single multi-horizon LightGBM (horizon as a feature, 96 blocks
ahead), `models/artifacts/lightgbm_model.txt`. Tuned with Optuna (25 trials,
val-MAPE objective); final fit on the full train set, early-stopped on val.

**Final test MAPE: 3.93%, i.e. test accuracy 96.07%** (test = 2025-07-12 23:45 .. 2026-01-12, i.e. first
forecast origin 12 Jul 23:45 and first target day 13 Jul; every origin x horizon
1-96, n = 1,672,080, not only the dashboard's 23:45 day-ahead view). The test split
was never used for hyperparameter tuning or early stopping. **Caveat:** the
feature design was not blind to test. The target-aligned lag features were
designed after reading test-set error diagnostics (where the first LightGBM lost
to seasonal-naive at long horizons), so test is no longer a fully untouched
holdout and this figure may be slightly optimistic (caveat 3).

## Train / val / test

| Split | Rows (origin x horizon) | LightGBM MAPE | Accuracy (100 − MAPE) | Seasonal-naive (`tlag_1day`) MAPE | Gain over naive |
|---|---|---|---|---|---|
| Train | 5,910,864 | 2.29% | 97.71% | 5.44% | 58% |
| Val | 1,657,296 | 4.29% | 95.71% | 5.97% | 28% |
| Test | 1,672,080 | **3.93%** | **96.07%** | 5.16% | 24% |

Test MAPE by horizon (the buckets used in the report, deck and script):
h1-4 3.21%, h5-24 3.48%, h25-48 3.84%, h49-96 4.22%; seasonal-naive is about
5.16% in every bucket. Error rises with horizon, as expected.

Same model, different horizon grouping: an earlier version of this file
reported h1-12 = 3.30% (3.58% val) and h85-96 = 4.38% (4.77% val). Those
numbers are still correct for those bands; they are not a different result.

At h = 1 simple persistence (next block = last block) beats the model:
1.44% vs 3.18% (h = 2: 2.77% vs 3.20%).

## Overfitting check — verdict: no harmful overfitting

- **Train-test gap is real but benign.** Gain over naive shrinks from 58%
  (train) to 24% (test); date-like features (day-of-year, target month,
  weather) likely let the trees partly memorise the two training years.
  Held-out error is not hurt by it (below), so it is not being pursued further.
- **Early stopping is healthy.** 436 rounds kept (486 run) of a 3000-round
  limit. Val goes 4.298% (round 300) to 4.290% (436); test 3.949% to 3.926%.
  Neither rises; only train keeps falling (2.60% to 2.29%).
- **Val (4.29%) > test (3.93%) is mostly window difficulty.** Val is
  two-thirds Mar-Jun (May 5.5%, Jun 6.0%); test has no Mar-Jun. The naive
  baseline shows the same gap (5.97% val vs 5.16% test). LightGBM/naive is
  0.72 on val vs 0.76 on test, so a small val-selection advantage is possible
  but not separable without a fresh holdout. Early stopping on val has
  negligible effect (test flat from round 400 to 436).
- **`tlag_1day` is not a leak.** It is load at target - 96 blocks; every
  source timestamp is <= the origin (max offset 0, at h=96). Correlation with
  the target is 0.963 (same at h=1/24/48/96), exact-equality fraction is 0,
  and permuting it raises test MAPE from 3.93% to 23.4% (genuine signal).
  Plot: `tlag_1day_sanity.png`.

## Documented caveats

1. **h=96 block-boundary assumption (to verify, no bug found).** At h=96,
   `tlag_1day` (and `load_now`) is the load at the origin timestamp itself,
   whereas `load_lag_1block` treats the previous block as the latest known
   value. This is only valid if `ts_ist` marks block *end* or the origin
   block's load is complete when the forecast is issued. If `ts_ist` is block
   *start*, that block is incomplete at forecast time. Verify against how the
   deployment API timestamps incoming data. Error rising with horizon gives no
   sign the assumption is being exploited.
2. **`night_temp_c` look-ahead for 00:00-05:00 origins.** The feature is the
   whole-night (00:00-05:00) mean broadcast across the day, so for origins in
   that window it includes up to a few hours of later temperature. Minor;
   already flagged in `features/build.py`.
3. **Test set is no longer a fully untouched holdout.** The target-aligned lag
   features were designed after reading the first model's test-set error
   breakdown (it lost to seasonal-naive at the longest horizons). Hyperparameters and early
   stopping never saw test, but the reported test gains carry some selection
   bias. Future design decisions should be taken on val (or a rolling-origin
   backtest inside train+val), with test kept for the final report only.

## Summary of the Phase 3 model ladder

Scored on the 1,267,749 test rows whose actual is a real reading in every data
version and that have a seasonal-naive forecast, seasonal-naive scored 5.22%
MAPE and the first LightGBM 4.93%; that model lost to naive at the 23 horizons
h = 74-96. Diagnostics found two problems. First, the data pipeline's imputer
used future data (two-sided interpolation, and a same-weekday median with no
distance cap), which inflated the Oct/Nov late-night training labels by about
25%. Second, the load features were aligned to the origin time, so the model
ignored the horizon. Making the imputer causal and adding target-aligned lag
features brought MAPE to 4.00%. A 2x2 ablation (below) attributes most of that
improvement to the target-aligned lags (~64%), ~25% to the cleaning fix, and
the remaining ~10% to hyperparameter re-tuning; the lag and cleaning effects
overlap, so their exact shares depend on the order in which they are added. An independent review then found two more issues: the Hampel outlier
filter looked at future readings, and the new profile fill paired the slot and
its anchor from different dates. Fixing them brought MAPE to 3.92%, a small and
uncertain step (~0.07pp). In the final model `tlag_1day` is the largest
contributor (66.5% of gain), and the model beats seasonal-naive at every
horizon.

Read alongside three caveats. Removing the leaks improved the score rather than
hurting it because the old imputer also produced wrong (inflated) labels. At
h = 1-2 simple persistence still beats the model (h = 1: 1.44% vs 3.18%). The
test split informed the feature design (caveat 3).

## Ablation results

2x2(+1) factorial: data version (old = leaky imputer, pass1 = causal imputer
v1, final = current) x features (32 = without target-aligned lags, 37 = with).
Identical hyperparameters (the final model's tuned params), full train set,
early stopping on each version's own val. All arms are scored on the same rows:
test targets that are real (not imputed, not outlier) in all three data
versions (n = 1,279,461). This is a different row set from the summary above
(it also keeps the 11,808 rows with no seasonal-naive forecast, which are hard
rows), so absolute MAPEs differ by ~0.03pp (final model: 3.95% here vs 3.92%);
numbers from the two row sets should not be compared directly. Two independent
audit runs (separate AI review agents) reproduced the arm results, deltas and
iid-day CIs exactly; the week-block and training-noise figures come from the
statistics audit alone. Script:
`ablation_attribution/run.py` (scratchpad of the earlier session); per-arm
results in its `results.json`.

**Pass-1 improvement, tuned model to tuned model on these rows: 4.96% -> 4.02%
(-0.94pp, 95% CI [-1.20, -0.68]).** (The same step reads 4.93% -> 4.00% on the
summary's row set.) Attribution:

| Source | Share of -0.94pp | pp |
|---|---|---|
| Target-aligned lags | ~64% (54-74% depending on order, see below) | ~0.61 |
| Causal cleaning (imputer v1) | ~25% | ~0.23 |
| Hyperparameter re-tuning | ~10% | ~0.10 |

The lags and cleaning shares are Shapley averages from the fixed-parameter arms
(old_f32 -> pass1_f37 = -0.84pp); re-tuning is the remaining gap to the
tuned-to-tuned -0.94pp. The two effects overlap (interaction ~0.18pp): cleaning
is worth 0.33pp without the lags but only 0.14pp with them, and the lags are
worth 0.70pp on old data but 0.51pp on pass1 data. So the lags' share of the
fixed-parameter -0.84pp is 61% if they are added after cleaning and 83% if added
first (Shapley average ~72%); as a share of the tuned-to-tuned -0.94pp, which
also contains the ~0.10pp re-tuning, the same range is 54-74% around ~64%. "Most of the gain came from the lags" is robust (lags exceed cleaning in
~90% of week-block bootstrap draws); "64%" is a rough estimate, not a separable
effect.

**Step 2 (causal Hampel + profile-fill fix): ~0.07pp, small and uncertain.**
With the lags it is -0.065pp (-0.077pp against pass1's own tuned model); once
day-to-day correlation and training noise are included its 95% CI is about
[-0.13, 0.00]. Without the lags it is +0.003pp, indistinguishable from zero,
and the difference between the two is not significant, so no claim is made
that the fix depends on the lags.

**Removing the lags from the final model raises test MAPE by 0.58pp** (3.95%
-> 4.53%; day-bootstrap CI [0.31, 0.84], week-block [0.02, 1.08]). The effect
is seasonal: about 0.2pp in Jul-Aug and about 0.7-0.9pp in Oct-Dec.

| Arm | Features | Best iter | Test MAPE | Val MAPE |
|---|---|---|---|---|
| old_f32 | 32 | 427 | 4.85% | 5.04% |
| old_f37 | 37 | 293 | 4.15% | 4.38% |
| pass1_f32 | 32 | 566 | 4.53% | 4.96% |
| pass1_f37 | 37 | 296 | 4.01% | 4.30% |
| final_f32 | 32 | 915 | 4.53% | 4.93% |
| final_f37 (saved model) | 37 | 436 | 3.95% | 4.27% |

Arm table above uses fixed hyperparameters throughout. Paired deltas (test
MAPE, percentage points; negative = better). CIs resample target days
independently (183 days, 2000 draws); daily deltas are autocorrelated (lag-1
~0.6), so these understate the uncertainty, and a week-block bootstrap is
roughly twice as wide:

| Effect | Delta | 95% CI (iid days) |
|---|---|---|
| Cleaning v1, 32 feats (old to pass1) | -0.33 | [-0.40, -0.26] |
| Cleaning v1, 37 feats | -0.14 | [-0.22, -0.07] |
| Target-aligned lags, old data | -0.70 | [-0.99, -0.41] |
| Target-aligned lags, pass1 data | -0.51 | [-0.76, -0.25] |
| Target-aligned lags, final data | -0.58 | [-0.84, -0.31] |
| Step 2 (Hampel + profile fix), 37 feats | -0.07 | [-0.11, -0.02] |
| Step 2, 32 feats | +0.00 | [-0.06, +0.06] |
| Total, old_f32 to final_f37 (fixed params) | -0.91 | [-1.17, -0.65] |

## Out of scope / not pursued

Day-of-year regularization to narrow the train-test gap: diminishing returns,
learning curves show no held-out harm. Phase 3 model changes are stopped.

## Phase 4 — Uncertainty and explainability

Built on the frozen final LightGBM (test MAPE 3.926%, i.e. 3.93%). Code:
`ml/src/lpmf/models/conformal.py`, `shap_examples.py`. Not wired into the
API or dashboard.

### Conformal bands (P10-P90)

MAPIE 1.6 `SplitConformalRegressor`, prefit, calibrated on all val
(origin, horizon) rows (1,657,296) and evaluated on test (1,672,080).
P10-P90 is an **80%** central interval (an early deck draft labelled it "~90%"; the deck now says 80%).
Output: `models/artifacts/conformal_bands.parquet` (test rows; primary
`lower_mw`/`upper_mw`, plus a relative-score variant `*_rel`) and
`conformal_summary.json`.

| Score | Test coverage | Mean width | h01-04 | h05-24 | h25-48 | h49-96 |
|---|---|---|---|---|---|---|
| absolute (primary) | **84.4%** | 602 MW (constant) | 89.9% | 87.6% | 84.8% | 82.3% |
| gamma (relative) | 83.5% | 562 MW | 89.3% | 86.9% | 84.1% | 81.4% |

- Marginal coverage is **above** the 80% target (84.4%): val residuals are
  larger than test residuals (val is Mar-Jun heavy, MAPE 4.29% vs 3.93%), so
  the calibrated width is conservative for this test window. Misses are
  symmetric (7.9% below, 7.8% above).
- Coverage is **not uniform**, so treat 80% as a marginal, not conditional,
  statement. Absolute score by month: Jan 91%, Jul 77%, Aug 73%, Sep 77%,
  Oct 80%, Nov 98%, Dec 96%; by horizon: 90% at h1-4 falling to 82% at
  h49-96. The constant-width band is too wide in calm winter months and
  too narrow in Jul-Sep. The relative score evens the months out for
  Jul-Sep (85%, 79%, 84%) but undercovers Oct (73%) — neither is
  conditionally calibrated.
- Exchangeability between val and test does not hold (different seasons);
  the empirical coverage above is the number to quote.

### TreeSHAP examples

`shap` 0.54 TreeExplainer on the saved model; base value 4314 MW.
Each day is a day-ahead explanation: origin 23:45 the evening before, 96
blocks. Additivity (base + sum SHAP = prediction) holds to 1e-11 MW on all
four days. Files: `models/artifacts/shap_examples/<day>.png`,
`<day>_waterfall.png`, `<day>_shap.parquet`, `index.json`. Days were picked
by rule, not by error.

| Day | Date | Day MAPE | Band coverage | Largest drivers (mean abs SHAP, MW) |
|---|---|---|---|---|
| hot_summer | 2025-07-28 | 2.63% | 89.7% | tlag_1day 1033, load_roll_mean_24h 190, target_dow 179, night_temp_c 142 |
| normal | 2025-10-15 | 2.24% | 93.5% | tlag_1day 378, tlag_4w_avg 102, night_temp_c 84 |
| festival (Diwali) | 2025-10-20 | 8.65% | 49.3% | tlag_1day 426, target_is_holiday 222, target_dow 120 |
| oct_nov_evening | 2025-10-27 | 4.12% | 96.2% | tlag_1day 657, target_dow 118, load_roll_mean_24h 110, night_temp_c 87 |

What SHAP shows:
- **`tlag_1day` dominates every day**, as in the importance ranking. Its
  contribution swings from about -1200 MW at the overnight trough to
  about -200 MW at midday on 2025-10-27: it carries the daily shape, with
  other features adjusting around it.
- **Hot day (07-28):** the day has the highest heat index in the test set
  but is a late-July monsoon day, not a Mar-Jun peak; the test window
  contains no real pre-monsoon summer. Weather features (`night_temp_c`,
  `temp_roll_mean_24h`) add roughly +100-170 MW each, small next to the lag.
- **Festival (Diwali):** the model sees the holiday (`target_is_holiday`
  is the second-largest driver, -272 MW at 12:30), but that is far too small:
  actual load was roughly 2000 MW below the 4-week same-block average
  (5530 MW), and the forecast overshoots the whole day (MAPE 8.65%, only
  49% inside the band). This is the clearest weakness found: holiday
  effects are learned from very few training holidays and a single
  indicator. This is a diagnosis, not acted on (Phase 3 stopped).
- **Oct/Nov evening (10-27):** evening forecast is high by ~100-250 MW
  after 19:00; `tlag_1day` pulls the forecast down toward the falling
  evening and `target_cos_hour` goes negative after 18:00, consistent with
  the evening ramp-down. I did not have the context for the "hour-23
  history" mentioned in the brief, so no hour-23-specific analysis was done.
