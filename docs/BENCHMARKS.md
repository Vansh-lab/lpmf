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
| 10 | Losses & PF | User what-if | ILLUSTRATIVE (REAL: BRPL/BYPL/TPDDL AT&C) | Formula, unit-tested | National AT&C 15.37% (FY2023, Rajya Sabha PQ 266); BRPL 6.58% / BYPL 7.84% / TPDDL 5.91% (FY2023-24, PFC primary PDF, Annexure 1.8, p.76) | PF-correction/I²R worked examples | — | N/A, no model. All three DISCOMs now from the primary source |
| 11a | Theft & Segments — demo fleet | Synthetic smart-meter fleet | SYNTHETIC | Isolation Forest + K-means | — | precision@6 = 50% | — | N/A, generated data |
| 11b | Theft & Segments — SGCC | SGCC (Zheng et al., IEEE TII 2018) | FOREIGN | Logistic regression → LightGBM | Paper: ~0.78 AUC-ROC (as stated in the brief; not independently verified) | **Test AUC-ROC 0.7585** (below paper — no leakage flag); improvement attempt (new features + wider search) tried, val improved but test was mixed (AUC-ROC down 0.7568) — **no improvement adopted, original kept** | 0.9174 / 0.7511 / 0.7585 | Train/val gap expected for tree model capacity; val≈test, no leakage |
| 12 | Data & Model Card | docs/MODEL_RESULTS.md, API responses | REAL | None — static summary | — | — | — | N/A, documentation only |

## Notes

- **FY2020-21 DERC schedule still operative:** DERC has not issued a new
  base tariff order since 30.09.2021; later orders (including any dated
  "FY 2025-26") only adjust the fuel-cost (PPAC) surcharge, not the ToD
  structure, hours, or percentages.
- **BYPL AT&C — now confirmed (2026-11-11):** the primary PFC PDF
  ("Report on Performance of Power Utilities 2023-24", cms.pfcindia.co.in,
  published Oct 2025) was located and fetched directly (an earlier TLS
  cert error was tooling-specific — plain `curl` and the built-in browser
  both reached it fine). Its Annexure 1.8 "AT&C Losses" table (PDF p.102 /
  printed p.76, 2023-24 columns) gives BRPL 6.58%, BYPL 7.84%, TPDDL 5.91%
  — BRPL and TPDDL exactly match the earlier secondary-source figures, and
  BYPL's 7.84% is now a primary-source-confirmed number, not a guess.
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

### Root cause — actively investigated (2026-11-11), not just hypothesized

**Plant 2 has a genuinely weak fit; this reflects a limitation of real-world data, not a mistake in the formula or a removable bug.** The formula itself is sound — Plant 1's data fits it very well (daytime r²=0.970) under the exact same code. Per this round's explicit instruction ("only change the number if a real bug is found — never remove an inverter without data-quality proof"), four concrete hypotheses were tested against the raw data, not just listed. **No fixable bug was found in any of them, so r²=0.208 stands unchanged as final.**

1. **Timestamp misalignment — ruled out.** Shifted Plant 2's irradiance series by -4 to +4 fifteen-minute blocks relative to AC power and refit at each shift. Daytime-only r² peaks exactly at shift=0 (**0.2085**) and falls at every other shift (e.g. 0.0585 at -1, 0.0604 at +1, down to about -0.02 at ±4); daytime MAPE likewise bottoms out at shift=0 (36.21%) and rises sharply elsewhere (51–157% at ±3/±4). The data is already correctly time-aligned.
2. **Capacity mismatch / clipping — ruled out.** Per-inverter max(AC)/max(DC) ratio is flat at ≈0.975 (std 7.6e-5) across all 22 inverters — not the inverter-to-inverter spread a clipping fault would produce. Pooled ratio-by-DC-power-decile is a smooth curve (0.966 → peak 0.982 at mid-range → 0.975 at the top decile), the normal shape of inverter efficiency vs. load, not the sharp top-decile collapse a real clipping signature would show. **Independent corroboration:** a Kaggle community thread on this exact dataset ("Let's Discuss the Outliers", user ElbioPeña) found the same ≈97.5% AC/DC ratio for Plant 2 and states it sits within the normal 93–98% real-world inverter-efficiency range — confirming the well-known decimal-point DC_POWER bug (≈9.75% ratio) is Plant-1-specific only and never touched Plant 2.
3. **Sensor placement / calibration — structural, not a fixable bug.** The dataset documents one weather-sensor array per plant, shared by that plant's 22 physically-distributed inverters (confirmed directly from the dataset's own structure, not inferred). A second Kaggle discussion thread on this dataset ("DC power variation among different inverters at the same timestamp", user Rajas Bhingarde) independently explains that disagreement between inverters under one shared sensor is expected — from per-string wiring/config differences, uneven irradiation across the array, and local temperature effects near some strings — which is exactly the structural mismatch (1 sensor vs. 22 inverters) this page's formula can't correct for. This is a property of the public dataset, not something to patch.
4. **Soiling / shading day pattern — checked, no discrete fault found.** Per-day WAPE (using the single globally-fit slope) across all 34 days ranges continuously from 10.5% to 85.8% (mean 30.1%, std 13.0%) — a smooth spread, not two separable "good days" vs. "bad days" clusters, so there's no single faulty day/equipment event to isolate. The worst days do concentrate in the back half of the 34-day window (11–17 June 2020 among them) and show amplified swings in *both* directions (actual/predicted ratio from 0.65× to 1.6×) rather than a one-way decline — the signature of increasing patchy-cloud variability (Nasik's monsoon onset is early-to-mid June, right where this window's worst days sit), not progressive soiling or equipment degradation, both of which would show a one-directional drift instead.

**Conclusion:** no genuine bug was found — timestamp alignment, inverter capacity, and the AC/DC ratio are all exactly as they should be, and the weak fit traces to the dataset's own structural limitation (one shared weather sensor for 22 spatially spread inverters), compounded by rising cloud-pattern variability later in the sampling window. This matches the real-world-data-limitation pattern noted independently by other users analysing this same public dataset. Per the "no removal without data-quality proof" rule, **zero Plant 2 inverters are excluded** (the Tukey IQR check on per-inverter zero-rate, documented below, found no statistical outlier either).

Full per-inverter table: `models/artifacts/solar/validation.json` (gitignored; regenerate with `python -m lpmf.solar.pipeline`).

### Losses & PF — BYPL AT&C confirmed from the primary PFC PDF (2026-11-11)

| DISCOM | Old (secondary source) | New (primary PFC PDF, Annexure 1.8, p.76) | Change |
|---|---|---|---|
| BRPL | 6.58% | **6.58%** | Unchanged — exact match, now primary-sourced |
| BYPL | unconfirmed (`None`) | **7.84%** | **Newly confirmed** — was genuinely absent from the secondary source |
| TPDDL | 5.91% | **5.91%** | Unchanged — exact match, now primary-sourced |

The primary PDF — PFC, "Report on Performance of Power Utilities 2023-24"
(published Oct 2025) — was located via PFC's own performance-report page
(`pfcindia.co.in/en/pages/operations/performance-report-of-power-utilities`,
a JS single-page app; the direct PDF link was only visible after rendering
it in a browser) and fetched directly from
`cms.pfcindia.co.in/media/documents/Report%20on%20Perfromance%20of%20Power%20Utilities%202023-24(1).pdf`
(the earlier TLS-cert failure was specific to one fetch tool — plain
`curl` and the browser both reached the same host without issue). All
three figures are read from Section 1, Annexure 1.8 "AT&C Losses", 2023-24
columns, PDF page 102 (printed page 76), Delhi state-sector rows
(BRPL/BYPL/TPDDL). DERC's tariff/ARR orders were not needed as a fallback
since the primary PFC PDF was found directly.
