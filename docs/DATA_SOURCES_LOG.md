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

### Dataset owner, source, licence (per explicit follow-up request, 2026-11-11)

- **Owner (Kaggle username):** `mukund604` (no real name given on the
  dataset page).
- **Original source / provenance:** **not documented anywhere** —
  confirmed by expanding every metadata field on the Kaggle page itself
  (not just the API metadata): "Authors" empty, "Coverage" empty, "DOI
  Citation" empty, and "Provenance → Sources" / "Collection Methodology" /
  "Citations" all literally "—" / "-". The dataset's own description says
  only "exchange price of electricity for the day ahead market (DAM) from
  2019 to 2024" (the file's actual data starts 2018-01-01, a day outside
  that stated range).
- **Licence:** Apache 2.0 (per Kaggle's own licence field).
- **Dataset ID:** 5757060, title "Indian Energy Exchange - Time Series
  Forecasting", 1 file (`DAM.xlsx`), 233,760 rows x 7 columns.

### Spot-check against the official IEX website (per explicit follow-up request)

IEX's own Market Snapshot page (iexindia.com/market-data/day-ahead-market/
market-snapshot) states "Data in 15-minute time block format is available
from delivery day 1st April 2022 onwards" — so only dates from Apr 2022
onward can be checked against it directly. Checked **4 random dates**
(00:00-02:00 IST block prices, MCP Rs/MWh) by reading the live site and
comparing to the Kaggle file:

| Date | Site vs Kaggle |
|---|---|
| 2024-03-15 | **Exact match**, all 8 checked blocks (e.g. 00:00 4649.15, 01:00 3901.98) |
| 2023-07-20 | **Exact match**, all 8 checked blocks (e.g. 00:00 8000.07, 00:45 4999.87) |
| 2022-06-10 | **Exact match**, all 8 checked blocks (e.g. 00:00 12000.00, 01:30 8390.42) |
| 2024-08-25 | **Exact match**, all 8 checked blocks (e.g. 00:00 3350.26, 01:45 2900.63) |

**4 for 4 exact matches** (to 2 decimal places, the site's own precision) —
strong direct confirmation this is genuine real IEX DAM data, despite the
uploader leaving every provenance field blank. Dates before 1 Apr 2022
(the file has data back to 2018-01-01) could not be checked this way since
the official site itself doesn't offer 15-min data that far back; no
alternative official source for that older period was found.

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

### Is this schedule still the one applicable now? (confirmed 2026-11-11, per explicit follow-up request)

Searched specifically for whether a newer DERC tariff order or ToD rule
has superseded it. Found, across several independently-dated DERC/BSES/
Tata Power DDL documents:
- A DERC short-term-procurement order (05.03.2025) states explicitly:
  **"there is no ARR Order passed by the Commission for FY 2025-26"** as
  of that date.
- A DERC order from January 2025 likewise states the base **Tariff Order
  for 2024-25 is yet to be determined** by the Commission.
- Every Power Purchase Cost Adjustment (PPAC/FPPAS) filing found from
  2024 through the latest located (a DERC order dated 10 Nov 2026 on
  September 2026 FPPAS recovery for BRPL/BYPL/TPDDL) is a **fuel-cost
  surcharge adjustment only**, filed quarterly/monthly on top of the
  existing base tariff — none of them revise the ToD structure, hours, or
  percentages. Several explicitly cite **"Tariff Order dated 30.09.2021"**
  as the base order a specific charge line was allowed under.
- **Conclusion: the DERC base tariff schedule (whose ToD clause we read
  directly, clause 3(d), p.2) remains the operative one** — no newer base
  ARR/tariff order revising ToD has been issued as of the most recent
  document found (Nov 2026). This is reported with the caveat that DERC's
  own tariff-orders index page (derc.gov.in/tarriff-orders) was not
  exhaustively paged through document-by-document; what's confirmed is
  that no PPAC/FPPAS filing — which would be expected to reference a newer
  base order if one existed — mentions one, and two explicit DERC
  statements (Jan 2025, Mar 2025) confirm no new ARR/tariff order has been
  passed since.
- **Page citation added:** the ToD Bill page's rates panel and
  `DERC_TOD_RATES["order_year"]` now state this confirmation explicitly,
  with the date it was last checked.

## Losses & PF

- **Searched (first pass):** PFC "Report on Performance of Power Utilities"
  (latest) for real, DISCOM-specific (BRPL/BYPL/TPDDL) AT&C loss figures,
  to add alongside the existing national FY2023 benchmark.
- **First-pass outcome:** the primary PDF (pfcindia.co.in) could not be
  fetched by the fetch tool used at the time (TLS certificate chain
  error). Used a secondary source instead, read directly (not a search
  snippet): Power Line, 8 Jul 2025, "Widening Losses: Key highlights of
  PFC's report on discom performance" (powerline.net.in), which quotes the
  report's figures verbatim for **BRPL (6.58%) and TPDDL (5.91%),
  FY2023-24**. BYPL was genuinely not mentioned in that article (confirmed
  by reading the full text, not a snippet) — two conflicting, unverified
  figures (6.9%/7.25%) turned up in other search snippets but were not
  confirmed by reading a source directly, so BYPL was reported as
  unavailable (`None`) rather than guessed.
- **Re-investigated (2026-11-11):** per this round's instruction to find
  the primary PDF directly and re-confirm BRPL/TPDDL from it too. The TLS
  error turned out to be specific to the one fetch tool tried first —
  plain `curl` reached `pfcindia.co.in` with `HTTP 200`, and PFC's
  performance-report page (`pfcindia.co.in/en/pages/operations/`
  `performance-report-of-power-utilities`) is a JS single-page app whose
  document links only render client-side, so the primary PDF's direct URL
  was found by loading the page in the built-in browser. Downloaded and
  read directly (`pymupdf`, not just metadata) the primary PDF: PFC,
  **"Report on Performance of Power Utilities 2023-24"** (published Oct
  2025), from
  `cms.pfcindia.co.in/media/documents/Report%20on%20Perfromance%20of%20Power%20Utilities%202023-24(1).pdf`.
  Its **Section 1, Annexure 1.8 "AT&C Losses" table (2023-24 columns, PDF
  page 102 / printed page 76)**, Delhi state-sector rows, gives:
  **BRPL 6.58%, BYPL 7.84%, TPDDL 5.91%**. BRPL and TPDDL exactly match
  the earlier secondary-source figures (re-confirmed from the primary
  source as requested); **BYPL's figure is now confirmed for the first
  time, directly from the primary report, not guessed.**
- **Outcome: REAL**, all three DISCOMs (BRPL, BYPL, TPDDL), now sourced
  directly from the primary PFC PDF rather than a secondary summary. PF
  formula inputs remain ILLUSTRATIVE (user what-ifs), unchanged. DERC's
  tariff/ARR orders were not needed as a fallback since the primary PFC
  PDF was found directly.
- Wired into `ml/src/lpmf/engines/losses.py`'s `DISCOM_AT_C_FY2023_24`,
  the API response, and the page.
