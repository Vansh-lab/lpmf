# Open-Source Data Audit — all 12 pages

For every page: where the data came from (exact URL/dataset ID), its
licence, and how we verified it's genuine — not just trusted. Where a
page uses synthetic or illustrative data, what open-source alternative we
looked for and why it wasn't used instead. Anything whose source or
licence isn't fully clear is flagged explicitly rather than glossed over.

## 01–04 · Overview, Load Analytics, Weather Impact, Forecast

- **Data:** Delhi 5-min system load + Open-Meteo weather (heat index, GHI).
- **Source / dataset ID:** Kaggle `prash4nt/delhi-sldc-load-data-5-min-resolution`
  (https://www.kaggle.com/datasets/prash4nt/delhi-sldc-load-data-5-min-resolution),
  scraped from the public Delhi SLDC (State Load Dispatch Centre) website;
  Open-Meteo historical weather API (open-meteo.com), no key required.
- **Licence:** **CC BY-NC-SA 4.0** (Delhi SLDC mirror) — non-commercial,
  share-alike. Fine for this academic/educational project; **would need
  separate permission for any commercial use.** Open-Meteo's own terms
  permit free non-commercial use.
- **Verification:** the mirror's own page states it's "scraped from the
  Delhi SLDC public website" and repeats SLDC's own disclaimer that the
  source site "does not guarantee correctness" and the data "has no
  commercial value" — i.e. even the primary utility doesn't warrant
  perfect accuracy. We did not independently re-scrape delhisldc.org to
  cross-check timestamps; this is a real source traced to a named,
  identifiable government utility and a named uploader, which is our
  basis for calling it REAL, but it is a mirror, not the primary site
  itself.
- **Flag:** none beyond the above — source and licence are both clear.

## 05 · DSM ₹ Calculator

- **Data:** none — user-supplied what-if inputs (deviation, volume limit).
- **Source:** N/A. The *formula* (CERC DSM Regulations 2024 structure) is
  a public regulation, cited in `docs/MODEL_RESULTS.md`/page references,
  but no consumption dataset backs this page.
- **Open-source search:** not applicable — this page was designed as an
  illustrative calculator from the start, not a data page.
- **Flag:** none — correctly tagged ILLUSTRATIVE throughout.

## 06 · Transformer Health

- **Data:** none — user-supplied what-if (hot-spot temperature).
- **Source:** the ageing-rate formula is from IEC 60076-7:2018 (a
  published international standard, not a dataset).
- **Open-source search:** not applicable, same as DSM Calculator.
- **Flag:** none.

## 07 · IEX Price

- **Data:** real IEX Day-Ahead Market MCP, 15-min, 2018-01-01 to
  2024-08-31 (233,760 rows).
- **Source / dataset ID:** Kaggle
  `mukund604/indian-energy-exchange-time-series-forecasting`
  (https://www.kaggle.com/datasets/mukund604/indian-energy-exchange-time-series-forecasting),
  file `DAM.xlsx`, Kaggle dataset ID 5757060.
- **Licence:** Apache 2.0 (per the dataset's own licence field).
- **Verification:** the uploader's own "Authors", "Coverage", "DOI
  Citation" and "Provenance → Sources/Collection Methodology/Citations"
  fields are all genuinely blank (confirmed by expanding each one on the
  Kaggle page itself, not just the API metadata) — **this dataset's
  origin is not documented by its uploader.** We verified it independently
  instead: full 15-min continuity over 6.7 years, a plausible price range,
  the expected evening-peak/midday-trough shape, and — the strongest
  check — **4 random dates spot-checked directly against IEX's own live
  Market Snapshot page, with an exact match on every 15-min block** (see
  `docs/DATA_SOURCES_LOG.md`).
- **Flag:** **the uploader's identity and original collection method are
  unverified** — we trust the data because it matches the authoritative
  source exactly, not because of anything the uploader documented.

## 08 · ToD Bill Simulator

- **Data:** DERC's own Time-of-Day tariff structure (not a dataset — a
  regulatory document).
- **Source:** DERC "Electricity Tariff Schedule for FY 2020-21 — BRPL,
  BYPL, TPDDL & NDMC" PDF, hosted at
  tatapower-ddl.com/Editor_UploadedDocuments/Content/Tariff_Schedule_2020-21.pdf,
  clause 3(d), page 2. This is a primary government-regulator document.
- **Licence:** N/A — a public regulatory order, not a licensed dataset.
- **Verification:** downloaded and read the PDF's actual text directly
  (via `pypdf`, not metadata or a secondary summary) — the exact clause
  is quoted in the engine's source comment. Separately confirmed
  (2026-11-11) that no newer DERC base/ARR tariff order has superseded it,
  via DERC's own Jan 2025 and 05.03.2025 orders stating no FY 2024-25/
  2025-26 ARR order exists yet.
- **Flag:** none — directly read primary source, re-confirmed current.

## 09 · Solar & Net Load

- **Data (production use):** real Open-Meteo GHI for Delhi (REAL), a
  Delhi rooftop capacity estimate (FOREIGN), and now a real-plant
  validation dataset (FOREIGN).
- **Source / dataset ID (validation only):** Kaggle
  `anikannal/solar-power-generation-data`
  (https://www.kaggle.com/datasets/anikannal/solar-power-generation-data),
  2 plants, 22 inverters each, 15-min, 34 days.
- **Licence:** **"Data files © Original Authors"** — **not an open
  licence** (not MIT/Apache/CC-BY); the uploader retains copyright with no
  explicit reuse grant beyond Kaggle's own hosting terms. Used here for
  one-off, non-redistributed formula validation (we publish only the
  resulting r²/MAPE numbers, not the raw file), which is standard
  practice for Kaggle research datasets, but this is **flagged** since
  it's a materially different (more restrictive) licence than IEX's or
  SGCC's.
- **Capacity benchmark source:** MNRE, reported by Renewable Watch
  (~302 MWp, Mar 2025) — a secondary citation of a primary-agency figure,
  not independently re-verified against an MNRE document directly.
- **Verification:** validated the formula's functional form against real
  paired irradiance/power data (see `docs/BENCHMARKS.md`'s Solar Plant 2
  diagnosis); Plant 1 fits very well, Plant 2 does not (see Part 3 of this
  round's work for the honest root-cause note).
- **Flag:** solar validation dataset's licence is more restrictive than
  the project's other Kaggle sources; capacity benchmark is a secondary
  citation, not a primary MNRE document.

## 10 · Losses & PF

- **Data:** none for the formula itself (user what-if); two real
  benchmark figures alongside it.
- **Source:** national AT&C 15.37% (FY2023) from Rajya Sabha unstarred
  question 266, 27 Nov 2024 — a primary government record, publicly
  published, no licence concerns. BRPL (6.58%) / BYPL (7.84%) / TPDDL
  (5.91%), FY2023-24, from PFC's own primary PDF, "Report on Performance
  of Power Utilities 2023-24" (cms.pfcindia.co.in, published Oct 2025),
  Annexure 1.8 "AT&C Losses", PDF p.102 / printed p.76.
- **Verification (updated 2026-11-11):** the national figure was read
  from the primary parliamentary record, as before. The DISCOM-specific
  figures were re-investigated this round and are now read directly from
  PFC's own primary report, not a secondary summary — the earlier TLS
  error was specific to the fetch tool first tried; plain `curl` and the
  built-in browser both reached the PDF without issue. BRPL and TPDDL
  exactly match the previously-used secondary source; BYPL's figure
  (previously unconfirmed) is now read directly from the primary PDF.
- **Flag: resolved.** All three DISCOM AT&C figures are now from PFC's
  primary report, directly read (not a secondary summary, not guessed).

## 11a · Theft & Segments — demo fleet

- **Data:** synthetic smart-meter fleet, generated by this project.
- **Open-source search:** explicitly searched for a public, consumer-level
  Delhi (or any Indian DISCOM) smart-meter dataset with theft/anomaly
  labels. **None found** — Delhi DISCOMs (BRPL/BYPL/TPDDL) do not publish
  consumer-level meter data, and no third-party open dataset for an
  Indian utility was located either. This is why the demo fleet is
  SYNTHETIC rather than using a real (even if foreign) consumer dataset —
  that role is filled instead by the SGCC dataset below, used for the
  actual trained model rather than this demo.
- **Flag:** none — synthetic status is correctly disclosed on the page
  with the reason (no public source exists).

## 11b · Theft & Segments — SGCC (trained model)

- **Data:** real State Grid Corporation of China consumption data, 42,372
  consumers, 1,034 days, used for the actual logreg→LightGBM model.
- **Source / dataset ID:** GitHub `henryRDlab/ElectricityTheftDetection`
  (https://github.com/henryRDlab/ElectricityTheftDetection), files
  `data.zip` + `data.z01` + `data.z02`. Paper: Zheng, Yang, Niu, Dai & Zhou,
  "Wide and Deep Convolutional Neural Networks for Electricity-Theft
  Detection to Secure Smart Grids", IEEE Transactions on Industrial
  Informatics, vol. 14, no. 4, pp. 1606-1615, April 2018
  (ieeexplore.ieee.org/document/8233155/).
- **Licence:** **the GitHub repo carries no LICENSE file and states no
  licence** — only "please cite our paper when you use this dataset."
  This is **not a formally open-licensed dataset**; it's an academic
  data-release with a citation request, standard for research reuse but
  without an explicit permissive grant. **Flagged.**
- **Correction made during this audit:** an earlier commit's PPT slide
  cited this paper's authors incorrectly as "Zheng, Yang, Chen, Huang &
  Zhu" — the real author list (confirmed directly from the GitHub repo's
  own README) is **Zheng, Yang, Niu, Dai, Zhou**. Fixed in this round
  (see commit for `LPMF_Project_Presentation_v2.pptx`).
- **Verification:** downloaded and validated row/day/theft-rate counts
  directly against the paper's and README's own stated figures (all
  matched); full pipeline and metrics in `docs/ALL_PAGES_METRICS.md`.
- **Flag:** no formal open-source licence on the dataset itself (citation-
  only norm); author citation error found and corrected.

## 12 · Data & Model Card

- **Data:** none directly — a static summary of every other page's
  sources, pulled from `docs/MODEL_RESULTS.md`, `docs/ALL_PAGES_METRICS.md`,
  this audit, and live API responses for headline numbers.
- **Flag:** none — by construction, any gap here is a gap in one of the
  rows above, not a new one.

## Summary of flags

| # | Page | Flag |
|---|---|---|
| 07 | IEX Price | Uploader's identity/collection method undocumented (mitigated by a 4/4 exact match against the official site) |
| 09 | Solar & Net Load | Validation dataset's licence is "© Original Authors" (not an open licence); capacity benchmark is a secondary citation |
| 10 | Losses & PF | ~~BRPL/TPDDL AT&C from a secondary source; BYPL genuinely unconfirmed~~ — **resolved 2026-11-11**, all three now from PFC's primary PDF |
| 11b | Theft & Segments (SGCC) | No formal licence on the GitHub data release (citation-only norm); an author-citation error in the PPT was found and corrected this round |

No other page carries an unresolved source or licence flag.

## Leakage + sanity sweep (2026-11-11)

Checked across all 12 pages:

1. **Train-only cleaning statistics.** SGCC (11b): `clean.fit_cleaning()`
   fits fill/cap values from the train split only (enforced in code and
   tested in `test_sgcc_clean.py`). Main forecast model (01-04): uses a
   different but equally correct discipline for a time series —
   *temporal* causality (every cleaning/imputation decision depends only
   on readings at or before it, never on the future), documented in
   `ml/src/lpmf/clean/load_clean.py`'s own module docstring. No scaler is
   fit anywhere in the main pipeline (tree models don't need one), so no
   cross-split scaling leakage is possible there.
2. **No test-set number used in a feature-design decision.** SGCC: Optuna
   tuning and the F1-threshold choice are both against val only, test
   scored exactly once (`ml/src/lpmf/sgcc/pipeline.py`, confirmed by
   grepping every `["test"]` usage — all inside the final metrics-
   computation block, none earlier). The conformal-band calibration
   (Forecast page) is fit on val, evaluated on test, matching its own
   documented protocol. The main forecast model carries one **pre-
   existing, already-disclosed** caveat (`docs/MODEL_RESULTS.md`,
   "Test set is no longer a fully untouched holdout" — the target-aligned
   lag feature design was informed by test-period behaviour before this
   project's own audit flagged it); nothing new found here, re-confirmed
   still accurate. This round's own new work (Solar Plant 2 diagnosis,
   SGCC improvement experiment) followed the same discipline throughout
   — see their own sections above.
3. **Provenance tags.** Cross-checked every router's `provenance=` value
   against its engine's actual tag (`grep -n "provenance=" api/app/routers/*.py`
   and each engine source): all 12 pages' top-level and nested provenance
   tags match what's actually REAL/SYNTHETIC/ILLUSTRATIVE/MODELLED/FOREIGN
   about their data. No mismatches found.
4. **Citation error found and fixed.** The SGCC paper's authors were
   misquoted on one PPT slide (`Zheng, Yang, Chen, Huang & Zhu` instead of
   the real `Zheng, Yang, Niu, Dai, Zhou`, per the GitHub repo's own
   README) — corrected in `docs/LPMF_Project_Presentation_v2.pptx`.
