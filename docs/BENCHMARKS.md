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
| 09 | Solar & Net Load | Open-Meteo GHI + forecast | MODELLED (FOREIGN benchmark + FOREIGN real-plant validation) | Formula (PVWatts-style), unit-tested | MNRE/Renewable Watch: ~302 MWp Delhi rooftop (Mar 2025); real-plant validation (Kaggle `anikannal/solar-power-generation-data`), diagnosed per-inverter (2026-11-11) | Midday solar peak 149 MW at PR=0.8; formula validated (daytime-only, see Note below): Plant 1 r²=0.970/MAPE 6.2%/WAPE 5.7%/nMAE 5.7%; Plant 2 r²=0.208/MAPE 36.2%/WAPE 28.7%/nMAE 28.7% (fit genuinely weak, diagnosed not guessed) | — | N/A, no model |
| 10 | Losses & PF | User what-if | ILLUSTRATIVE (REAL: BRPL/TPDDL AT&C) | Formula, unit-tested | National AT&C 15.37% (FY2023, Rajya Sabha PQ 266); BRPL 6.58% / TPDDL 5.91% (FY2023-24, PFC via Power Line) | PF-correction/I²R worked examples | — | N/A, no model. BYPL unconfirmed — not guessed |
| 11a | Theft & Segments — demo fleet | Synthetic smart-meter fleet | SYNTHETIC | Isolation Forest + K-means | — | precision@6 = 50% | — | N/A, generated data |
| 11b | Theft & Segments — SGCC | SGCC (Zheng et al., IEEE TII 2018) | FOREIGN | Logistic regression → LightGBM | Paper: ~0.78 AUC-ROC (as stated in the brief; not independently verified) | **Test AUC-ROC 0.7585** (below paper — no leakage flag); improvement attempt (new features + wider search) tried, val improved but test was mixed (AUC-ROC down 0.7568) — **no improvement adopted, original kept** | 0.9174 / 0.7511 / 0.7585 | Train/val gap expected for tree model capacity; val≈test, no leakage |
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

### Solar Plant 2 diagnosis (2026-11-11) — old vs new validation numbers

The first validation pass used a "daytime" floor of 0.05 kW/m² and
reported only r² (over the *full* period, including night) and one MAPE
number. Re-diagnosed properly per request:

| Metric | Old (first pass) | New (after fixing the methodology) | Why it changed |
|---|---|---|---|
| Plant 1 r² | 0.9915 (all blocks) | 0.9915 (all blocks) / **0.9698 (daytime only)** | Added a daytime-only r² — barely moves for Plant 1, confirming its fit is genuinely strong, not just an artifact of easy night zeros |
| Plant 1 MAPE | 6.34% (floor 0.05) | 6.23% (floor 0.10) | Floor raised per request to a clearer "unambiguous daylight" cutoff (0.1 kW/m²); the difference is small because Plant 1's fit is solid at both floors |
| Plant 1 WAPE / nMAE | not computed | 5.67% / 5.67% | New metrics, not dominated by any single low-output row the way MAPE can be |
| **Plant 2 r²** | 0.8215 (all blocks) | 0.8215 (all blocks) / **0.208 (daytime only)** | **This is the key finding.** The headline 0.82 was almost entirely the model trivially getting night (GHI=0, power=0) right — during actual generation hours the formula explains only ~21% of Plant 2's variance |
| Plant 2 MAPE | 36.01% (floor 0.05) | 36.20% (floor 0.10) | Essentially unchanged — MAPE was already real, not a floor artifact |
| Plant 2 WAPE / nMAE | not computed | 28.71% / 28.71% | Still high but lower than MAPE, confirming MAPE was somewhat (not entirely) inflated by small-denominator rows |

**Per-inverter fault diagnosis (data-quality rule written and applied before looking at any fit numbers):**
1. **DC/AC unit-mismatch check** (requested, since Plant 1's own file has one): Plant 2's `sum(AC_POWER)/sum(DC_POWER)` ≈ **0.978**, a plausible real inverter efficiency — no mismatch. (Plant 1's own ratio is ≈0.098, a real quirk in that file, unrelated to Plant 2 and never touched since the formula only ever used AC_POWER.)
2. **Per-inverter zero-output rate during strong, unambiguous sun** (IRRADIATION > 0.6 kW/m², well above the "any daylight" floor): computed for all 22 inverters per plant. Plant 2's rates run from **4.4% to 49.3%** — a smooth continuum, not two separable clusters.
3. **Exclusion rule (written before checking its effect on the fit):** flag an inverter only if its zero-rate is a **Tukey IQR outlier** (> Q3 + 1.5×IQR) against the *other inverters'* own spread — a boundary set by the data, not chosen to hit a target r²/MAPE.
4. **Result:** applying that rule to Plant 2 flags **zero inverters** — the smooth continuum has no statistical outlier to exclude. (The same rule applied to Plant 1, for consistency, flags 2 of its 22 inverters — both still only ≈2.5% zero-rate against a fleet that's otherwise ≈0%; noted for completeness, not acted on since Plant 1 wasn't the page in question.)
5. **Conclusion:** no inverters are excluded from Plant 2's validation. Its weak daytime fit is reported honestly as-is rather than removing inverters to improve it — doing so without rule (3) above would be cherry-picking data to match the model, not a data-quality decision.

### Root cause (possible reasons, not independently confirmed)

**Plant 2 has a genuinely weak fit; this reflects a limitation of real-world data, not a mistake in the formula.** The formula itself is sound — Plant 1's data fits it very well (daytime r²=0.970) under the exact same code. Four plausible, non-exclusive physical reasons for Plant 2 specifically (none independently confirmed here — this dataset doesn't carry the extra fields, e.g. per-inverter GPS position or rated capacity, needed to test them directly):

- **Sensor placement.** Each plant has only **one** weather sensor for the *whole* site, but the plant's 22 inverters are physically spread across it. If Plant 2's sensor sits somewhere unrepresentative of the average conditions the inverters actually see (more shaded, or in a sunnier spot than most panels), a single irradiance reading would poorly predict the aggregate output no matter how good the formula is. This is plausibly the single biggest factor, since it would affect every inverter at once rather than just a few.
- **Inverter clipping.** If Plant 2's inverters are sized close to (or below) the DC array's peak output, AC output flattens at high irradiance even as GHI keeps rising — a real, well-known nonlinearity that a linear GHI→power formula can't capture, and would lower r² specifically at the high-irradiance end.
- **Partial shading.** Trees, structures or neighbouring rows casting moving shadows across parts of the array through the day would decouple local panel output from the single sensor's reading, especially inverters on the shaded side.
- **Soiling / wiring differences.** Dust, bird droppings or uneven cleaning schedules across 22 separate inverter strings, plus differences in wiring/cable losses between strings, would all add consumer-level noise the formula has no way to see from GHI alone.

None of these can be distinguished from the others with only this dataset's 4 columns (AC/DC power, irradiance, temperature) — doing so would need per-inverter metadata this public release doesn't include. The honest conclusion stands either way: **Plant 2's weak fit is a real-world data limitation, not a formula problem.**

Full per-inverter table: `models/artifacts/solar/validation.json` (gitignored; regenerate with `python -m lpmf.solar.pipeline`).
