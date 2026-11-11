# Data Sources Log

For each page, what we searched for, where we looked, what we found, and
whether the result is REAL (a genuine public dataset/document), FOREIGN
(real but not Delhi-specific), MODELLED (our formula validated against a
real benchmark), or SYNTHETIC (no public source exists — generated).

Rule: look for real open data first; synthetic only when no public source
exists. Every entry below names what was searched, where, and the outcome.

## Theft & Segments (SGCC)

- **Searched:** public, consumer-level electricity-theft datasets.
- **Found:** SGCC dataset (State Grid Corporation of China), via Zheng et
  al., IEEE TII 2018, mirrored at GitHub `henryRDlab/ElectricityTheftDetection`.
- **Outcome: REAL (FOREIGN).** 42,372 consumers, 1,034 days, 8.53% theft
  rate — verified against the paper's own figures. No Delhi-specific,
  consumer-level smart-meter theft dataset is public (confirmed earlier in
  this project: no such source exists for Delhi DISCOMs).
- Full pipeline, metrics, and paper comparison: `docs/ALL_PAGES_METRICS.md`
  row 11b.

## IEX Price

- **Searched:** real IEX (Indian Energy Exchange) Day-Ahead Market price
  data — iexindia.com Market Snapshot/Area Price exports, Kaggle/Mendeley
  mirrors.
- **Found:**
  - iexindia.com's own Market Snapshot page: 15-min blocks from 1 Apr 2022,
    but the "Export" button's Delivery Period selector appears to support
    only single-day exports (no multi-day/range found), and no public
    JSON/CSV API — not practically scriptable for a year of history
    (~365 manual exports).
  - energymap.in sells a commercial IEX historical dataset — paid, not
    freely downloadable.
  - **Best candidate: Kaggle `mukund604/indian-energy-exchange-time-series-forecasting`**
    — `DAM.xlsx`, 233,760 rows x 7 cols, 2019-2024, MCP (Rs/MWh) target,
    Apache 2.0 license. Caveat: the dataset's own provenance/citation
    fields are empty on Kaggle — claims to be real IEX DAM data but isn't
    independently documented by the uploader; plan is to validate it after
    download by spot-checking its price range/pattern against the live
    IEX snapshot before trusting it fully.
- **Resolved (2026-11-11):** Kaggle token was in a newer format
  (`~/.kaggle/access_token`, not `kaggle.json`) that the installed `kaggle`
  package (2.2.5) already supports — confirmed with a small metadata-only
  test download before downloading the full dataset.
- **Downloaded:** `DAM.xlsx`, 233,760 rows, 15-min resolution, 2018-01-01
  to 2024-08-31 (2,435 days). Validated: fully continuous (no missing
  blocks, no duplicate timestamps), plausible price range (Rs 0.30-20.00/
  unit, mean 4.23), and the expected evening-peak/midday-trough shape
  (hour 19 mean > 20% above hour 13's) — consistent with IEX's real
  behavior, despite the uploader's own Kaggle metadata leaving provenance
  fields empty.
- **Outcome: REAL.** Built a block-of-day (96-value) historical average
  price profile (`lpmf.iex.pipeline`) and wired it into the IEX Price
  page/engine/API in place of the old illustrative cosine curve. Tagged
  REAL with an honest caveat: it's the historical *typical-day* average,
  not that specific day's actual real-time price. The EAC-PM FOREIGN
  benchmark stays alongside it unchanged. Old illustrative-mode code path
  (`illustrative_hourly_price_per_mwh`) kept as a fallback for when the
  pipeline hasn't been run (artifacts are gitignored).

## Solar & Net Load

- **Searched:** Kaggle "Solar Power Generation Data" (India, 2 plants) for
  irradiance→power model validation.
- **Resolved (2026-11-11):** same Kaggle token fix as IEX. Downloaded
  `anikannal/solar-power-generation-data` (2 plants, 22 inverters each,
  15-min generation + weather sensor data, May-Jun 2020).
- **Outcome: REAL validation added.** Fit the formula's combined
  capacity x PR slope by OLS through the origin against each plant's real
  paired irradiance/power data.
- **Diagnosed further (2026-11-11), per explicit follow-up request** —
  see `docs/BENCHMARKS.md`'s "Solar Plant 2 diagnosis" section for the
  full old-vs-new table and reasoning. Summary:
  - **DC/AC unit-mismatch check**: Plant 2's AC/DC ratio ≈0.978 (plausible
    real efficiency) — no Plant-1-style mismatch (Plant 1's own ratio
    ≈0.098 is a real quirk in that file, unrelated and untouched).
  - **MAPE methodology fixed**: daytime floor raised to 0.1 kW/m² (100
    W/m²) as requested; added WAPE and nMAE (not dominated by near-zero
    rows the way MAPE can be); added a **daytime-only r²** alongside the
    full-period one.
  - **Key finding**: Plant 2's full-period r²=0.8215 was mostly the model
    trivially getting night right — **daytime-only r²=0.208**. MAPE
    36.20%, WAPE/nMAE 28.71% (daytime, floor 0.1).
  - **Faulty-inverter rule written before checking its effect on the
    fit**: flag an inverter only if its zero-output rate during strong
    irradiance (>0.6 kW/m²) is a Tukey IQR outlier against the *other*
    inverters' own spread. Plant 2's 22 inverters' zero-rates (4.4%-49.3%)
    form a smooth continuum with **zero IQR outliers** — so no inverters
    are excluded; doing so without this rule would be cherry-picking data
    to fit the model. (Same rule on Plant 1, for consistency, flags 2 of
    22 inverters at only ≈2.5% zero-rate — noted, not acted on.)
  - Plant 1 after the same re-diagnosis: r²=0.9915 (all) / 0.9698
    (daytime), MAPE 6.23%, WAPE/nMAE 5.67% — still strong, confirming the
    formula itself is fine; Plant 2's weakness is plant-specific.
  - Full per-inverter table: `models/artifacts/solar/validation.json`
    (gitignored; regenerate via `python -m lpmf.solar.pipeline`).
  - Wired into the Solar & Net Load page as a FOREIGN "real plant
    validation" panel with the full metric table and diagnostics summary,
    alongside the existing REAL Open-Meteo GHI + MODELLED Delhi-formula
    output and the FOREIGN rooftop-capacity benchmark, all unchanged.

## ToD Bill Simulator

- **Searched:** DERC tariff order (latest FY) for exact ToD hour-windows
  and surcharge/rebate %. The page previously cited "FY 2025-26, 30%/25%,
  17-22h/22-6h" — flagged in the code as *not independently re-verified*.
- **Found:** DERC has not issued a new base tariff order since 30.09.2021;
  later orders (including FY 2025-26 ones) only adjust the fuel-cost
  (PPAC) surcharge, not the ToD structure. Downloaded and directly read
  (via `pypdf`, not just metadata) the DERC "Electricity Tariff Schedule
  for FY 2020-21 — BRPL, BYPL, TPDDL & NDMC"
  (tatapower-ddl.com/Editor_UploadedDocuments/Content/Tariff_Schedule_2020-21.pdf),
  clause 3(d), page 2: **peak surcharge 20%, off-peak rebate 20%**, peak
  hours **14:00-17:00 & 22:00-01:00**, off-peak **04:00-10:00**, **May-
  September only**, applicable only to non-Domestic consumers with
  sanctioned load/MDI >= 10kW/11kVA. The previously-coded 30%/25%,
  17-22h/22-6h, year-round figures do not match any document found and
  have been corrected.
- **Outcome: REAL**, corrected and page-cited. `ml/src/lpmf/engines/tod_bill.py`'s
  `DERC_TOD_RATES`, its test, and the page's displayed hours/rates were
  all updated accordingly.

## Losses & PF

- **Searched:** PFC "Report on Performance of Power Utilities" (latest) for
  real, DISCOM-specific (BRPL/BYPL/TPDDL) AT&C loss figures, to add
  alongside the existing national FY2023 benchmark.
- **Found:** PFC's "Report on Performance of State Power Utilities 2023-24"
  — the primary PDF (pfcindia.co.in) could not be fetched (TLS certificate
  chain error, not transient). Used a secondary source instead, read
  directly (not a search snippet): Power Line, 8 Jul 2025, "Widening
  Losses: Key highlights of PFC's report on discom performance"
  (powerline.net.in), which quotes the report's figures verbatim for
  **BRPL (6.58%) and TPDDL (5.91%), FY2023-24**. **BYPL is genuinely not
  mentioned in that article** (confirmed by reading the full text, not a
  snippet) — two conflicting, unverified figures (6.9%/7.25%) turned up in
  other search snippets but were not confirmed by reading a source
  directly, so BYPL is reported as unavailable (`None`) rather than
  guessed.
- **Outcome: REAL** (BRPL, TPDDL) via a secondary source quoting the
  primary report; **BYPL: unavailable**, honestly reported as such. PF
  formula inputs remain ILLUSTRATIVE (user what-ifs), unchanged.
- Wired into `ml/src/lpmf/engines/losses.py`'s new `DISCOM_AT_C_FY2023_24`,
  the API response, and the page.
