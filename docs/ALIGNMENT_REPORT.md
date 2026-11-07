# Report ↔ PPT alignment (Task C)

Files under review: `LPMF_Project_Report.docx` / `.pdf` (9 pages), `LPMF_Project_Presentation.pptx` (14 slides) and `LPMF_Presentation_Script.docx` / `.pdf`.
Repo numbers are recomputed by `docs/report_assets/make_charts.py` → `docs/report_assets/verified_numbers.json`. The 34 engine tests (`ml/tests/test_engine_*.py`) pass.

## Content mismatches

| # | Item | Report (draft) | PPT (before) | Repo truth | Fix |
|---|---|---|---|---|---|
| 1 | Naive MAPE | 5.22% in the ladder, 5.16% in the text, neither labelled | 5.16%, no label | 5.16% on the full test set (1,656,240 rows with a naive forecast); 5.22% on the 1,267,749 common real rows | Headline 5.16% "(full test set)" in both files; 5.22% appears only in the report's ladder, labelled "common real test rows" |
| 2 | LF / PAR | "Illustrative day … Whole period (measured)" | "Illustrative day: 530 / 820 → …", "Live page, whole period" | 0.646 / 1.55 is only the 530/820 example; measured value is 0.503 / 1.99 over 96,398 blocks | Same wording in both: "Illustrative day (530 / 820)" and "Whole period, measured (Apr 2023 – Jan 2026, 96,398 blocks)" |
| 3 | Persistence at h = 1 | ~1.4% vs ~3.1% | "persistence still wins at h = 1–2" | 1.44% vs 3.18% (h = 2: 2.77% vs 3.20%) | 1.44% vs 3.18% in the report, deck (slide 6) and script; no other figure is used anywhere |
| 4 | "177 MW miss" | — | "Meaning: … about 177 MW" | Not measured: 4,500 × 3.93% | Labelled "Derived arithmetic, not measured" in both |
| 5 | Live pages | "Seven implemented", including Data & Model Card | 6 live + 6 future | The app has a data-model-card route, but the brief counts it as future scope | Report now says 6 live + 6 future, same as the PPT |
| 6 | Page names | Title Case | Slide 4 lower case ("Load analytics", "DSM ₹ calculator") | — | Slide 4 uses Title Case; page descriptions in the report's Table 4 copied from slide 4 |
| 7 | "Phase 2" | — | Slide 3: "losses in Phase 2", "Built now: the forecast plus DSM and transformer…" | 6 live pages | Slide 3 says "future scope" and "Built now: six live pages …" |
| 8 | Lags' share of the gain | "~64% (61–83% depending on order)" | — | MODEL_RESULTS: 54–74% as a share of −0.94 pp (61–83% is the share of the fixed-parameter −0.84 pp) | Report: 54–74% |
| 9 | Animish's roll no. | Cover 23295918010, table 23295919010 | — | Brief: 23295919010 | 23295919010 everywhere |
| 10 | SARIMAX | "Implemented, no test result" | — | Only an order search on validation (val MAPE about 25%) | Report says this. Work Distribution still lists SARIMAX, as the brief asked |
| 11 | Data sources | IEX, London smart meters, ESP32 listed as sources | — | Not in the pipeline | Removed; §7 lists only the files the six live pages use |
| 12 | Formula names | Named in the equations table | No names on feature slides | — | Each formula card on slides 6–11 is labelled with the report's equation name |
| 13 | Section order | — | Dashboard (slide 4) → Dataset (slide 5) | — | Report §6 Dashboard → §7 Dataset |

Note: MODEL_RESULTS gives 93.5% band coverage for 15 Oct 2025. Recomputing from `conformal_bands.parquet` gives 92.7%. Neither file quotes this number.

## Visual fixes

**PPT**
- Header was at (18.4, 13.3) pt on slides 4–11, (36, 22.3) on slide 3 and (36, 16.6) on slide 2. All are now at (36, 16.6), on the 0.5" margin.
- Title was at (97.2, 52.2) on slide 2 and (115.2, 52.9) on slide 3. Both now match the rest at (112.4, 49.0).
- Slide 2 had no footer. It now has "02 / 14". The footer text was not added because it would overlap the "Who is affected" oval.
- Slides 6–11 sit on the same grid: every panel and card has the same x, y, w and h (checked with python-pptx).

**Report**
- Figure tables were merging with the table above them, which repeated a header row on the next page. Separated.
- A table header row was left alone at a page bottom. Rows are now kept together.
- Length cut from 10 pages to 8.
- Contents page numbers are read from the rendered PDF.
- Figures 1–9 and Tables 1–8 are numbered in order (new Figure 3 and Table 4 in §5.2; later ones shifted by one).

## Accuracy and fit check (Task D)

Numbers re-scored live from the saved model `models/artifacts/lightgbm_model.txt` (no retraining), every origin × horizon row per split:

| Split | Rows | MAPE | Accuracy (100 − MAPE) | Seasonal-naive MAPE | Gain over naive |
|---|---|---|---|---|---|
| Train | 5,910,864 | 2.29% | 97.71% | 5.44% | 58% |
| Validation | 1,657,296 | 4.29% | 95.71% | 5.97% | 28% |
| Test | 1,672,080 | 3.93% | 96.07% | 5.16% | 24% |

- Test MAPE by horizon: h1–4 3.21%, h5–24 3.48%, h25–48 3.84%, h49–96 4.22% (naive ≈ 5.16% at every horizon).
- Early stopping: 436 rounds kept, limit 3,000 (patience 50). Validation and test MAPE are flat from round 300; only train keeps falling.
- Gain = 1 − model MAPE ÷ naive MAPE, model on all rows (test 23.9%; 24.5% if restricted to the 1,656,240 rows naive can score).
- Persistence at h = 1: 1.44% vs model 3.18%.
- Verdict (same wording in all files): "Overfitting: small train–test gap, early stopping at 436/3000, val & test flat → not harmful. Underfitting: no — beats naive by 24% on test at every horizon."
- Headline (same wording in abstract, conclusion, slide 6 and script): test accuracy ≈ 96% (MAPE 3.93%).

| File | What changed |
|---|---|
| Report | New §5.2 "Accuracy and Fit Check (Overfitting / Underfitting)" with Table 4 and Figure 3 (`accuracy_check.png`); old §5.2 is now §5.3; the overfitting paragraph in §5.1 moved into §5.2; §5.1 horizon sentence uses the four buckets; Figure 2 regenerated from the same test data with the bucket means drawn on it; test accuracy line in Abstract and Conclusion. Figures 1–2 and 4–6 are drawn slightly smaller to stay at 9 pages. Contents page numbers re-read from the rendered PDF (unchanged). |
| PPT | New slide 6 "Model Accuracy & Fit Check" after Dataset (slide 5 had no room): chart, accuracy tiles, MAPE/accuracy/naive/gain table, horizon table, verdict, two caveats. Header, title, footer and number at the same positions as slide 5. Footers now "NN / 14". |
| Script | New "Slide 6 — Model Accuracy & Fit Check" section with script, formulas and viva Q&A; later slides renumbered 7–14; timing table (total 805 s, ≈ 13.4 min); slide previews re-rendered from the new deck; Forecast horizon answer uses the four buckets; viva Q13 "Overfitting hai ya nahi?" updated and Q15 "96% accuracy kaise nikali?" added. |

Older numbers still present outside these files (not edited here): `MODEL_RESULTS.md` line 23 and `VIVA_GUIDE.md` line 31 give horizon bands as h1–12 3.30% / h85–96 4.38%. These are correct for those bands but use different buckets from the deck and report.
