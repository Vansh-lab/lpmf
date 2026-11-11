
# All Pages — Accuracy Summary

One row per dashboard page: what kind of model (if any) backs it, what data
it runs on, its provenance tag(s), its metric, the train/val/test numbers,
and an overfitting verdict. Pages with no model (a formula applied to an
input) are marked "formula, unit-tested" rather than given train/val/test
numbers, since there is nothing to overfit.

| # | Page | Model or formula | Data | Provenance | Metric | Train | Val | Test | Overfitting verdict |
|---|---|---|---|---|---|---|---|---|---|
| 01 | Overview | LightGBM (shared forecast) | Delhi SLDC + Open-Meteo | REAL | MAPE | 2.29% | 4.29% | 3.93% | Not harmful — see row 04 |
| 02 | Load Analytics | Formula (LF, PAR), unit-tested | Delhi SLDC | REAL | — | — | — | — | N/A, no model |
| 03 | Weather Impact | OLS (1 predictor), unit-tested | Delhi SLDC + Open-Meteo | REAL | r² | — | — | 0.61 | N/A, refit each run, no train/val/test split |
| 04 | Forecast | LightGBM, multi-horizon | Delhi SLDC + Open-Meteo | REAL | MAPE / band coverage | 2.29% | 4.29% | 3.93% / 84.4% | Not harmful (docs/MODEL_RESULTS.md): gap is real but benign, early stopping at 436/3,000, val & test flat |
| 05 | DSM ₹ Calculator | Formula, unit-tested | User what-if | ILLUSTRATIVE | — | — | — | — | N/A, no model |
| 06 | Transformer Health | Formula (IEC 60076-7), unit-tested | User what-if | ILLUSTRATIVE | — | — | — | — | N/A, no model |
| 07 | IEX Price | Formula + real historical block-of-day average price, unit-tested | Delhi SLDC (load) + real IEX DAM history (Kaggle, 2018-2024) | REAL (FOREIGN benchmark: EAC-PM price range) | — | — | — | — | N/A, no model |
| 08 | ToD Bill Simulator | Formula, unit-tested | Illustrative profile | ILLUSTRATIVE (REAL: DERC rates, corrected 2026-11-11 — see docs/DATA_SOURCES_LOG.md) | — | — | — | — | N/A, no model |
| 09 | Solar & Net Load | Formula (PVWatts-style), unit-tested | Open-Meteo GHI + forecast | MODELLED (FOREIGN benchmark: rooftop capacity + real-plant r²/MAPE validation) | — | — | — | — | N/A, no model |
| 10 | Losses & PF | Formula, unit-tested | User what-if | ILLUSTRATIVE (REAL: BRPL/TPDDL AT&C FY2023-24; FOREIGN: national AT&C) | — | — | — | — | N/A, no model |
| 11a | Theft & Segments — demo fleet | Isolation Forest + K-means | Synthetic smart-meter fleet | SYNTHETIC | precision@k | — | — | 50% @k=6 | N/A, generated data, no train/val/test |
| 11b | Theft & Segments — SGCC | Logistic regression -> LightGBM | SGCC (Zheng et al., IEEE TII 2018) | FOREIGN | AUC-ROC, PR-AUC, MAP@100/200 | 0.9174 | 0.7511 | 0.7585 | Train/val gap is real but expected for tree models on ~30k consumers with ~10 engineered features; val≈test (no leakage); below paper's stated AUC, not above, so no leakage red flag |
| 12 | Data & Model Card | None — static summary | docs/MODEL_RESULTS.md, API responses | REAL | — | — | — | — | N/A, documentation only |

Rows 01–04 share the same model (one multi-horizon LightGBM); see
docs/MODEL_RESULTS.md for the full writeup. Row 11b detail is below, from
the completed `ml/src/lpmf/sgcc/pipeline.py` run — see its full output at
models/artifacts/sgcc/results.json.

## Row 11b detail — SGCC theft detection (real pipeline run, 2026-11-11)

Numbers below are read directly from `models/artifacts/sgcc/results.json`
and `models/artifacts/sgcc/dataset_validation.json` after the full pipeline
(`python -m lpmf.sgcc.pipeline --n-trials 25`) completed in 170s.

**FOREIGN data.** Method demonstrated on public SGCC benchmark; Delhi
DISCOM meter data would be needed for deployment.

### Dataset validation

| Check | This copy | Paper / README |
|---|---|---|
| Consumers | 42,372 (42,367 after dropping 5 all-missing) | 42,372 |
| Days (distinct columns) | 1,034 (1,035-day span, 2014-01-01 to 2016-10-31) | 1,034 (1,035-day span) |
| Theft rate | 8.53% | ~8.5% (commonly cited) |

All three checks pass (`dataset_validation.json`: `n_consumers_matches_paper`,
`n_day_columns_matches_expected`, `date_span_matches_paper`,
`theft_rate_within_1pt_of_expected` all `true`).

Consumer-level stratified split (seed 20261111, one consumer in exactly one
split — enforced by `ml/tests/test_sgcc_split.py`): train 29,656 (70.0%,
theft rate 8.52%), val 6,355 (15.0%, 8.53%), test 6,356 (15.0%, 8.53%).

### Model ladder (test, scored once)

| Model | AUC-ROC | PR-AUC | Precision | Recall | F1 | Accuracy | All-normal baseline accuracy | MAP@100 | MAP@200 |
|---|---|---|---|---|---|---|---|---|---|
| Logistic regression (baseline) | 0.7179 | 0.2327 | 0.2437 | 0.3764 | 0.2959 | 0.8472 | 0.9147 | 0.50 | 0.365 |
| LightGBM (Optuna-tuned on val, 25 trials) | 0.7585 | 0.2905 | 0.2933 | 0.3967 | 0.3373 | 0.8671 | 0.9147 | 0.57 | 0.47 |
| Zheng et al. 2018 (paper, AUC only) | ~0.78 (as stated in the brief; not independently verified — the paper is paywalled and no accessible source confirmed this exact figure) | — | — | — | — | — | — | — | — |

LightGBM beats the logistic-regression baseline on every test metric (model
ladder respected — the more complex model earned its place). Threshold for
precision/recall/F1/accuracy chosen on val (`best_f1_threshold`), never on
test. Note the "all-normal" baseline accuracy (91.47%, i.e. always predict
"not theft") is *higher* than both models' accuracy — expected given the
8.5% class imbalance, and the reason accuracy is reported only alongside
this baseline rather than as a headline metric.

**Paper comparison:** our LightGBM test AUC (0.7585) is *below* the paper's
stated ~0.78, not suspiciously above it, so there is no leakage red flag
per the check rule (leakage would show up as *our* number being
implausibly higher). The gap is plausible: our feature set is 10
hand-engineered per-consumer statistics (mean/std/zero-days/weekly
pattern/drops/trend) vs. the paper's CNN operating on the raw daily
sequence, so some sequential signal is not captured here.

### Overfitting check

| Split | AUC-ROC |
|---|---|
| Train | 0.9174 |
| Val | 0.7511 |
| Test | 0.7585 |

Train/val gap (0.9174 vs 0.7511) reflects real overfitting capacity of a
68-leaf, depth-9 LightGBM on ~30k rows with only 10 features per consumer —
expected for this model class, not a leakage artifact, since val and test
AUC are close to each other (0.7511 vs 0.7585) and test was scored exactly
once, after tuning. Best boosting iteration: 58 (early-stopped). Learning
curve (AUC vs boosting round, train/val/test all plateau by ~iteration 50-100
with no val/test divergence): see `models/artifacts/sgcc/results.json`'s
`learning_curve` array.

### Segments (K-means on SGCC features)

Best k (by silhouette scan over k=2..6, train-fit): **k=3** (silhouette
0.540, vs 0.504 at k=2, 0.286-0.321 for k=4-6). Silhouette score computed
on a 5,000-row random sample (`SILHOUETTE_SAMPLE_SIZE`) for memory reasons
— standard practice at this scale, still an honest, comparable-across-k
estimate.

| Split | Silhouette | Cluster sizes (0 / 1 / 2) |
|---|---|---|
| Train | 0.540 | 2,765 / 25,711 / 1,180 |
| Val | 0.554 | 595 / 5,501 / 259 |
| Test | 0.545 | 523 / 5,593 / 240 |

Val/test consumers are assigned under the train-fitted scaler/centroids
(never used to refit either), and their silhouette scores are close to
train's — consistent, not an artifact of overfitting the clustering to
train.

### SGCC improvement attempt (2026-11-11, honest val-only protocol)

Tried to beat the locked model (val PR-AUC 0.2536) with: (a) two new
engineered features (`weekly_pattern_break`, `recent_volatility_ratio` —
see `ml/src/lpmf/sgcc/features_experimental.py`), (b) a wider Optuna
search (60 trials vs 25, regularisation range widened 10x to [1e-8, 50]),
and (c) a logreg+LightGBM ensemble. **Pre-registered decision metric: val
PR-AUC** (the same metric the locked model's own Optuna search already
optimizes against — chosen before running anything, not after seeing
results, to avoid picking whichever metric makes an improvement look
best).

| Candidate | Val PR-AUC |
|---|---|
| Baseline (locked model, no retraining) | 0.2536 |
| **Extended features (wider search)** | **0.2676** (winner) |
| Ensemble (logreg + extended-feature LightGBM) | 0.2562 |

Extended features won on val (+5.5% relative), so — per the protocol —
it was scored on test **exactly once**:

| Metric | Locked model (test) | Extended features (test, this experiment) |
|---|---|---|
| AUC-ROC | **0.7585** | 0.7568 (down) |
| PR-AUC | 0.2905 | 0.2939 (up) |
| Precision | 0.2933 | 0.2872 (down) |
| Recall | 0.3967 | 0.4022 (up) |
| F1 | 0.3373 | 0.3351 (down) |
| MAP@100 | 0.57 | 0.52 (down) |
| MAP@200 | 0.47 | 0.46 (down) |

**Verdict: no clean improvement — kept the original locked model.** The
extended-feature model beat the pre-registered val metric, but test is a
genuinely mixed result: PR-AUC and recall ticked up, while AUC-ROC (the
headline metric used everywhere else in this project), precision, F1,
MAP@100 and MAP@200 all moved slightly the other way. Rather than declare
victory on the one metric that improved, or quietly bury the result, the
honest call is that this isn't a convincing overall win, so **the locked
model (test AUC-ROC 0.7585) remains the page's production result,
unchanged.** Full numbers for both candidates: `models/artifacts/sgcc/improvement_experiment.json`.

## Phase 4 forecast experiment — holiday tier (optional, strict)

A `holiday_tier` (0/1/2: none/minor/major) feature was tried against
Diwali-style weakness (docs/MODEL_RESULTS.md limitation: Diwali day MAPE
8.65%, the weakest of four SHAP example days). Decision rule: keep only if
val MAPE improves over the locked model's 4.29%; test run once regardless
of outcome if kept, reported honestly either way.

| | Val MAPE | Kept? | Test MAPE |
|---|---|---|---|
| Locked final model (37 features) | 4.2899% | — | 3.93% |
| + holiday_tier (38 features) | 4.3058% | **No — worse** | not run (discarded before touching test, per the rule) |

**Result: discarded.** Adding holiday_tier made validation MAPE *worse*
(4.3058% vs 4.2899%, +0.016 pp), so per the keep-only-if-val-improves rule
it was never scored on test and nothing was saved. The locked model
(`models/artifacts/lightgbm_model.txt`) is unchanged and no
`lightgbm_model_holiday_tier.txt` file was written. Best iteration reached:
289 (vs the locked model's 436), for reference only.

A plausible reason: `target_is_holiday` (already a feature) and
`holiday_tier` are highly correlated — tier is really a refinement of the
same signal on very few rows (only 20 of the ~96,398 blocks' calendar days
are holidays at all), so the split likely added variance without enough
holiday examples to learn a stable major/minor distinction, rather than
giving the model new information. The Diwali-specific weakness
(docs/MODEL_RESULTS.md) remains open; this one experiment did not fix it.
See `models/artifacts/holiday_tier_experiment.json` for the raw numbers.
