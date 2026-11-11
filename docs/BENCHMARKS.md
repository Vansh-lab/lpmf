# Benchmarks — all 12 pages

One row per page: its data source, provenance, model/formula, the external
benchmark it's checked against (if any), our result, train/val/test
numbers (if any), and an overfitting verdict. Every benchmark number below
names its source — see `docs/DATA_SOURCES_LOG.md` for the search process
behind each one.

| # | Page | Data source | Provenance | Model/formula | Benchmark | Our result | Train/Val/Test | Overfitting verdict |
|---|---|---|---|---|---|---|---|---|
| 01 | Overview | Delhi SLDC (Kaggle mirror) + Open-Meteo | REAL | LightGBM (shared forecast) | — | Peak-demand KPI, forecast MAPE 3.93% test | 2.29% / 4.29% / 3.93% | Not harmful — see row 04 |
| 02 | Load Analytics | Delhi SLDC | REAL | Formula (LF, PAR), unit-tested | — | LF 0.503, PAR 1.99 (whole period) | — | N/A, no model |
| 03 | Weather Impact | Delhi SLDC + Open-Meteo | REAL | OLS (1 predictor), unit-tested | — | β=112.0 MW/°C, r²=0.61 | — | N/A, refit each run |
| 04 | Forecast | Delhi SLDC + Open-Meteo | REAL | LightGBM, multi-horizon + MAPIE conformal bands | Persistence (h=1): 1.44%/3.18% | Test MAPE 3.93%, band coverage 84.4% (target 80%) | 2.29% / 4.29% / 3.93% | Not harmful (docs/MODEL_RESULTS.md): early stop 436/3,000, val/test flat |
| 05 | DSM ₹ Calculator | User what-if | ILLUSTRATIVE | Formula, unit-tested | — | Deviation charge worked example | — | N/A, no model |
| 06 | Transformer Health | User what-if | ILLUSTRATIVE | Formula (IEC 60076-7), unit-tested | — | Ageing-rate worked example | — | N/A, no model |
| 07 | IEX Price | Delhi SLDC (load) + real IEX DAM price history (Kaggle `mukund604/...`, 2018-2024) | REAL (FOREIGN benchmark) | Formula + real historical block-of-day average price, unit-tested | EAC-PM WP 53/2026: ₹1.11-9.71/unit (May 2026) | Real historical hourly range ₹3.05-6.13/unit (6.7-yr average, narrower than EAC-PM's one-month snapshot) | — | N/A, no model. Falls back to the old illustrative curve if the pipeline hasn't been run (gitignored artifacts) |
| 08 | ToD Bill Simulator | Illustrative profile | ILLUSTRATIVE (REAL: DERC rates) | Formula, unit-tested | DERC Tariff Schedule FY 2020-21, clause 3(d), p.2 (directly read) | Peak 20% surcharge, off-peak 20% rebate, 14-17h & 22-01h / 04-10h, May-Sep | — | N/A, no model. Rates/hours corrected 2026-11-11 (were unverified 30%/25%, 17-22h/22-6h) |
| 09 | Solar & Net Load | Open-Meteo GHI + forecast | MODELLED (FOREIGN benchmark + FOREIGN real-plant validation) | Formula (PVWatts-style), unit-tested | MNRE/Renewable Watch: ~302 MWp Delhi rooftop (Mar 2025); real-plant validation (Kaggle `anikannal/solar-power-generation-data`) | Midday solar peak 149 MW at PR=0.8; formula validated r²=0.99/MAPE 6.3% (Plant 1), r²=0.82/MAPE 36.0% (Plant 2, weaker fit not root-caused) | — | N/A, no model |
| 10 | Losses & PF | User what-if | ILLUSTRATIVE (REAL: BRPL/TPDDL AT&C) | Formula, unit-tested | National AT&C 15.37% (FY2023, Rajya Sabha PQ 266); BRPL 6.58% / TPDDL 5.91% (FY2023-24, PFC via Power Line) | PF-correction/I²R worked examples | — | N/A, no model. BYPL unconfirmed — not guessed |
| 11a | Theft & Segments — demo fleet | Synthetic smart-meter fleet | SYNTHETIC | Isolation Forest + K-means | — | precision@6 = 50% | — | N/A, generated data |
| 11b | Theft & Segments — SGCC | SGCC (Zheng et al., IEEE TII 2018) | FOREIGN | Logistic regression → LightGBM | Paper: ~0.78 AUC-ROC (as stated in the brief; not independently verified) | Test AUC-ROC 0.7585 (below paper — no leakage flag) | 0.9174 / 0.7511 / 0.7585 | Train/val gap expected for tree model capacity; val≈test, no leakage |
| 12 | Data & Model Card | docs/MODEL_RESULTS.md, API responses | REAL | None — static summary | — | — | — | N/A, documentation only |

## Notes

- **FY2020-21 DERC schedule still operative:** DERC has not issued a new
  base tariff order since 30.09.2021; later orders (including any dated
  "FY 2025-26") only adjust the fuel-cost (PPAC) surcharge, not the ToD
  structure, hours, or percentages.
- **BYPL AT&C:** genuinely absent from the one directly-read secondary
  source (Power Line's summary of PFC's FY2023-24 report); two conflicting
  unverified numbers turned up in search snippets but were not confirmed
  by reading a source directly, so BYPL is reported as unavailable rather
  than guessed.
- **IEX / Solar real-data upgrades (done 2026-11-11):** both downloaded
  from Kaggle after resolving a token-format issue (the token was in the
  newer `~/.kaggle/access_token` format, not `kaggle.json`). IEX now uses
  a real historical block-of-day average price (2018-2024, 233,760 blocks,
  fully continuous); Solar's formula is now validated against two real
  Indian plants' paired irradiance/power data. See docs/DATA_SOURCES_LOG.md
  for the full search/validation detail.
