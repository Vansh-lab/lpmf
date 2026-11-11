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
- **Status: in progress** — see update below once research completes.

## Solar & Net Load

- **Searched:** Kaggle "Solar Power Generation Data" (India, 2 plants) for
  irradiance→power model validation.
- **Status: blocked** — Kaggle API token (`~/.kaggle/kaggle.json`) was not
  actually present on this machine despite being believed set up; user is
  adding it. Will resume once confirmed.
- Existing page already uses REAL Open-Meteo GHI for Delhi + a FOREIGN
  rooftop-capacity benchmark; the Kaggle dataset would additionally
  validate the PVWatts-style formula itself (r², MAPE) against measured
  plant output before applying it to Delhi.

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
  real, DISCOM-specific (BRPL/BYPL/TPDDL) AT&C loss figures.
- **Status:** in progress — see update below once research completes.
