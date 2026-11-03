# PPT presentation guide with counter questions (final viva guide)

> **Final version, Phase 8.** Yeh wahi purana guide hai: same structure, same Hinglish, same slide-by-slide flow. Fark sirf itna hai ki purane illustrative ya stale numbers ki jagah ab real numbers hain, har slide pe likha hai ki kya sach mein bana hai aur kya abhi roadmap pe hai, aur end mein naye counter-questions add kiye hain jo Phase 3 se 8 tak ke kaam se aayenge.
>
> **Deck ke baare mein:** yeh guide `docs/LPMF_Project_Presentation.pptx` (repo wala deck) ke hisaab se hai. Deck ka wording thoda-bahut badal sakta hai (jaise planned items pe "planned" ya "Phase 2" tag), isliye har slide ko uske **content** se describe kiya hai, exact quotes se nahi. Slide pe jo bhi wording ho, status wahi bolna jo is guide mein likha hai.
>
> Har number repo ki in files se liya gaya hai: `docs/MODEL_RESULTS.md`, `docs/DATA_QUALITY.md`, `docs/PROVENANCE.md`, `api/app/config.py`. Jahan koi number repo mein verify nahi ho saka, wahan **[TODO: verify]** likha hai. Viva se pehle ek baar uska source khol ke check kar lena, aur agar check nahi hua to woh number bolna hi mat.
>
> **Teen golden rules:**
> 1. Illustrative number ko hamesha "illustrative" bolo, kabhi real result ki tarah mat bolo.
> 2. Humara r² = 0.61 aur CSE ka 67% kabhi mix mat karna. Dono alag metric hain.
> 3. Koi limitation poochhe to seedha maan lo. Is project ki honesty hi uski sabse badi strength hai.

---

## Pehle: 30-second pitch (agar seedha bolein "apna project batao")

"Humne Delhi ke electricity grid ke liye ek AI-integrated load intelligence dashboard banaya hai. Real Delhi SLDC 5-min load data (Apr 2023 se Jan 2026) aur free Open-Meteo archive weather pe humne ek multi-horizon LightGBM train kiya jo agle din ke 96 blocks ka forecast deta hai: poore test set pe **3.93% MAPE**, jo seasonal-naive baseline (5.16%) se 24% better hai, saath mein 80% P10–P90 uncertainty band (test pe 84.4% coverage) aur chune hue dino ke liye SHAP explanation. Yahi forecast Overview page pe kal ka peak aur overload alert deta hai. DSM penalty (₹) aur transformer ageing ke pages abhi illustrative what-if calculators hain jo same engine formulas pe bane hain; unhe forecast error se jodna agla step hai, aur IEX, ToD bill, solar aur theft wale pages Phase 2 roadmap pe hain. Har panel pe REAL, SYNTHETIC ya ILLUSTRATIVE tag dikhta hai, aur poora system free/open-source tools pe bana hai."

Isse ratt lo. Panel jab bhi bole "one line mein / two minutes mein batao," yehi bologe.

---

## Yaad rakhne wale numbers (cold), aur unka tag

| Kya | Number | Tag |
|---|---|---|
| Final test MAPE (LightGBM, saare test origins × horizons 1–96, n = 1,672,080 forecasts) | **3.93%** (3.926%) | REAL backtest |
| Seasonal-naive (same block kal) test MAPE | 5.16%, matlab model 24% better | REAL backtest |
| Train / val / test MAPE | 2.29% / 4.29% / 3.93% | REAL |
| Horizon ke hisaab se (test) | h1–12: 3.30%, h85–96: 4.38% | REAL |
| P10–P90 band | **80%** interval (90% nahi). Target 80%, test coverage **84.4%** (usi 1,672,080 test forecasts pe; yeh count forecasts ka hai, blocks ka nahi), mean width 602 MW | REAL backtest |
| Heat sensitivity β | **112.0 MW/°C** (112.044), r² = **0.61**, intercept 1,342 MW. +3 °C heat index ≈ +336 MW | REAL, apna OLS fit, 96,398 blocks |
| CSE 2025 | Heat index Delhi ke **daily peak** variation ka 67% explain karta hai. Yeh CSE ka metric hai, humara nahi | External |
| Load factor / PAR (poora period) | LF **0.503**, PAR **1.99** (average 4,316 MW, peak 8,582 MW) | REAL |
| Load factor / PAR (deck ka worked example) | 530/820 MW din: LF **0.646**, PAR **1.55** | ILLUSTRATIVE |
| DSM worked example | 60 MW deviation vs 41 MW BRPL limit, NR ₹5,000/MWh, k = 1.5: **₹3.475 lakh/hr** | ILLUSTRATIVE |
| Transformer ageing | Hot-spot 118 °C: V = **10.08** (1 ghanta = 10.08 ghante ki insulation life) | ILLUSTRATIVE what-if |
| Data range | 1 Apr 2023 se 12 Jan 2026 23:45 IST. Raw 5-min mein 2.705% missing, 15-min pe imputation ke baad 1.361% missing hi chhoda | REAL |
| Test window | Pehla forecast origin 12 Jul 2025 23:45. Target days 13 Jul 2025 se 12 Jan 2026: 184 calendar din, jinme se 183 pe data hai (8 Jan 2026 ka koi test target nahi) | REAL |
| Dataset ka maximum | 8,581.6 MW (15-min average), 19 Jun 2024 15:30. Raw 5-min data mein usi din ka max 8,631.5 MW | REAL |
| Pichhla Delhi record (2024) | **[TODO: verify]** 8,656 MW, 19 Jun 2024 (external sources; report mein ref [2] ke saath, bina date ke; 19 June report se nahi aata). Hamare data ke dono max isse thoda neeche hain | External |
| Delhi all-time peak | 8,748 MW, 29 Jun 2026 (Delhi SLDC). **Dataset ke bahar hai**, sirf Overview alert threshold hai | External |
| Diwali (2025-10-20) | Day MAPE 8.65%, band coverage 49.3%. Sabse saaf weakness | REAL |
| h = 1–2 (15–30 min aage) | h = 1 pe simple persistence ~1.4% vs model ~3.1%. 23:45 origin pe h = 1–2 forecast din ke 00:00 aur 00:15 blocks hain, yaani dashboard ke schedule ke andar. Documented limitation | REAL |
| Ablation (pass-1 improvement) | 4.96% se 4.02% (−0.94 pp, iid-day 95% CI [−1.20, −0.68]; week-block bootstrap ~2x wide). Is −0.94 pp ka: lags ~64% (~0.61 pp; order ke hisaab se 54–74%), cleaning ~25% (~0.23 pp), re-tuning ~10% (~0.10 pp) | REAL |

**Ek chhota gotcha:** 3.93%, 3.92% aur 3.95% teeno sahi hain, bas alag row sets pe hain. 3.93% poore test set pe hai (headline yahi hai). 3.92% ladder ke common real-row set pe hai (n = 1,267,749). 3.95% ablation ke common row set pe hai (n = 1,279,461). Agar koi poochhe, yahi bolna.

**Doosra gotcha:** 3.93% aur 84.4% **saare** test origins × horizons 1–96 ka average hain (1,672,080 forecasts), sirf 23:45 wale day-ahead forecasts ka nahi. Dashboard jo 23:45-origin day-ahead view dikhata hai, woh inhi rows ka ek subset hai. Sirf-23:45 ka alag number docs mein nahi hai, isliye koi aur number mat bolna.

---

## Honest status: kya bana hai, kya nahi (yeh pehle hi clear rakho)

**Bana hua hai (dashboard pe live, login ke baad):**
- **01 Overview:** test window ke aakhri din (12 Jan 2026) ka day-ahead forecast peak (11 Jan 23:45 pe issue hua), aur 8,748 MW limit ke against alert. Din choose nahi hota, hamesha yahi latest test day dikhta hai.
- **02 Load Analytics:** poore period (1 Apr 2023 se 12 Jan 2026) ka LF, PAR, average/peak aur load-duration curve, real SLDC load pe. API date range le sakti hai, lekin page pe abhi koi date control nahi hai.
- **03 Weather Impact:** β ka OLS fit (saare 15-min blocks pe), aur daily-mean load vs heat index ka scatter.
- **04 Forecast:** test window ka koi din chuno: 96 blocks, P10–P90 band, LightGBM vs seasonal-naive MAPE comparison, aur sirf 4 precomputed dino ke liye SHAP.
- **05 DSM ₹ Calculator:** ILLUSTRATIVE what-if calculator (sliders). Forecast error nahi padhta.
- **06 Transformer Health:** ILLUSTRATIVE what-if (IEC 60076-7, hot-spot slider). Forecast nahi padhta.
- **12 Data & Model Card:** sources (har ek apne badge ke saath), splits, accuracy, coverage, ablation summary aur known limitations (Phase 8 mein bana).

**Abhi roadmap pe hai ("Phase 2", bana nahi):** 07 IEX price, 08 ToD bill, 09 Solar & net load, 10 Losses & PF, 11 Theft & segments. App ke nav mein yeh Phase 2 ke taur pe disabled dikhte hain.

**Models:** seasonal-naive aur LightGBM (final model) bane hain aur test pe score hue hain. SARIMAX (hourly) code mein implemented hai, lekin uska sirf validation pe order search hua; **koi test result nahi hai**, isliye woh reported ladder mein nahi hai. N-HiTS, TFT, Chronos, XGBoost, NeuralForecast aur TimesFM proposal-stage ideas the, **run nahi hue**.

**Data:** SLDC load (REAL), Open-Meteo **archive** weather (REAL, historical hourly; live feed nahi) aur calendar/holiday/IPL flags (REAL) use hue hain. Consumer categories SYNTHETIC hain: generator 5 categories banata hai (residential, commercial, industrial, agricultural, EV charging; "public utilities" nahi). Yeh forecast input nahi hain aur kisi page pe plot nahi hoti, sirf Data & Model Card pe listed hain. IEX prices, London Smart Meters, SGCC aur IoT hardware abhi use nahi hue.

**Aur kya nahi bana:** forecast se chalne wale DSM/transformer pages (abhi manual what-if hain), har forecast ke liye SHAP (sirf 4 precomputed din), live weather feed, aur GitHub remote (repo sirf local hai).

**Dashboard live feed nahi hai.** Yeh backtest ke test window (pehla origin 12 Jul 2025 23:45; target days 13 Jul 2025 se 12 Jan 2026) ke din replay karta hai. Overview page khud yeh likhta hai.

**Numbering:** deck ka Slide 8 aur app ka nav ab same numbering use karte hain (01–12; 06 = Transformer Health, 07 = IEX price, 12 = Data & Model Card). Built pages 01–06 aur 12 hain.

---

## Slide 1: Title Slide

**Kya hai:** University of Delhi ka logo, Faculty of Technology aur Department of Electrical Engineering. Phir project ka naam (Load Profile Management & Forecasting) aur tagline (Delhi grid ke liye ek AI-integrated load intelligence dashboard). Neeche "Presented by" mein team (tum, Animish, Ayush, Lavish) aur "Under the guidance of" mein supervisors (Dr. Ujjal Sur, Supervisor; Dr. Arjun Tyagi, Co-Supervisor). **Is slide pe koi chart ya graph nahi hai**, sirf text aur logo.

**Kyun hai:** Pehla impression. Naam aur tagline se hi panel ko pata chal jaata hai ki yeh sirf forecasting nahi, ek "intelligence dashboard" hai jo forecast ko engineering use tak le jaata hai.

**Bolne ka tareeka:** "Humara project Load Profile Management & Forecasting hai: Delhi grid ke liye ek AI-integrated load intelligence dashboard. Hum real Delhi SLDC data pe agle din ka 96-block forecast banate hain aur use engineering formulas se jodte hain." Bas itna bolke seedha Slide 2 pe chalo.

**Counter-questions ready rakho:**
- **"Title mein 'AI-integrated' kyun, sirf 'forecasting' kyun nahi?"** → Kyunki sirf forecast karna kaafi nahi hai. Idea yeh hai ki AI forecast ko engineering formulas (peak alert, DSM, transformer ageing) se jodkar ek "intelligence" layer banayi jaaye. Abhi ke build mein forecast seedha Overview ka peak alert chalata hai; DSM aur transformer pages illustrative what-if calculators hain.
- *(Optional, agar Slide 2 ke solar point pe "duck curve" poochhe)* **"Duck curve kya hai?"** → Jab dopahar mein solar zyada hota hai to net load (demand − solar) dopahar mein gir jaata hai aur sunset ke baad tezi se chadhta hai, to graph ka shape duck jaisa lagta hai. Humne rooftop solar aur net load abhi model nahi kiya: model mein solar irradiance (GHI) sirf ek weather feature hai, aur Solar & net load page (09) Phase 2 mein hai.

---

## Slide 2: Problem Statement

**Kya hai:** upar 4 stat tiles, phir ek chhota problem paragraph (DISCOMs ko kal ka demand 96 blocks mein forecast karna padta hai; existing monitoring sirf batata hai ki kya ho chuka), phir 4 "Problem" points aur neeche "Who is affected".

**4 numbers yaad rakhna, cold:**
- **256.1 GW:** India ka all-time peak (25 Apr 2026, Ministry of Power/PIB)
- **8,748 MW:** Delhi ka all-time peak (29 Jun 2026, Delhi SLDC)
- **67%:** Delhi ke **daily peak** variation ka itna hissa heat index se explain hota hai (CSE 2025 study). Yeh CSE ka number hai, humara nahi.
- **₹1.11 → ₹9.71:** IEX price per unit, midday vs night (May 2026, EAC-PM)

4 "Problem" points:
1. **Forecast error = penalty:** CERC DSM Regs 2024 ke under har MW deviation pe charge lagta hai.
2. **Transformers overheat:** 40 °C ambient pe full load chalane se insulation ~10x tezi se age karta hai (IEC 60076-7). Yeh "10x" kahan se aata hai, neeche counter-question mein hai.
3. **Solar shaam ko steep bana deta hai:** May 2026 mein ~24 GWh/day solar curtail hua.
4. **Losses & theft:** AT&C loss FY25 mein national level pe abhi bhi 15.04% hai.

Neeche: DISCOMs (BRPL, BYPL, TPDDL), SLDC operators aur 70+ lakh Delhi consumers affected hain.

**Sources:** Slide ke external stats (256.1 GW, ₹1.11/₹9.71, ~24 GWh/day, 15.04%, 70+ lakh) deck ke references se hain (Slide 10 ke refs 1, 4, 5). Yeh repo ke data se nahi aaye. **[TODO: verify]** Viva se pehle in sabke source links ek baar khol ke dekh lena.

**Pichhla record (2024):** external sources batate hain ki 8,748 MW ne 8,656 MW (19 Jun 2024) ka pichhla record toda. Report ke Introduction mein yahi number ref [2] (Delhi SLDC, Business Standard ki reporting) ke saath likha hai. **[TODO: verify]** Viva se pehle ref [2] ek baar khol ke 8,656 MW aur 19 June ki date confirm kar lena; agar wahan na mile to report aur viva dono se hata dena. Humare SLDC dataset mein usi din ka max raw 5-min data mein 8,631.5 MW aur 15-min average mein 8,581.6 MW (15:30) hai, dono thoda neeche. Iska reason neeche counter-question mein hai.

**Kyun hai:** Yeh slide problem establish karta hai, aur bina strong problem ke koi bhi solution impressive nahi lagta. Panel yahi dekhta hai ki tumne sirf assume nahi kiya, actual data aur regulation padha hai.

**Counter-questions:**
- **"DSM Regulation exactly kya hai?"** → CERC ka Deviation Settlement Mechanism (2024). Agar DISCOM ka actual demand uske day-ahead 15-min schedule se deviate karta hai, to us deviation pe financial penalty ya credit lagta hai. Isse DISCOMs ko accurate forecast karne ka incentive milta hai.
- **"AT&C loss kya hota hai?"** → Aggregate Technical & Commercial loss. Technical losses (I²R heating, transformer aur line losses) aur commercial losses (theft, galat billing, meter errors) dono ko milakar ek % nikalta hai: kitni energy generate/purchase hui jiska revenue nahi bana.
- **"Heat index temperature se alag kaise hai?"** → Heat index temperature aur humidity dono ko combine karke "feels like" temperature deta hai. Hum NWS ka Rothfusz regression use karte hain (deck ref 13). High humidity mein same temperature pe body ko zyada garmi lagti hai aur AC load usi hisaab se badhta hai, isliye sirf temperature se heat index better predictor hai.
- **"96 blocks of 15 minutes kyun?"** → Indian grid scheduling (SLDC/RLDC level) 15-min blocks mein hoti hai. 24 hours ÷ 15 min = 96 blocks, yahi regulatory standard granularity hai.
- **"8,748 MW tumhare data mein hai? Tumhara model usse test hua?"** → Nahi. Humara data 12 Jan 2026 pe khatam hota hai, aur yeh record 29 Jun 2026 ka hai, yaani dataset ke bahar. Hum ise sirf Overview page ke alert threshold ki tarah use karte hain (`api/app/config.py`). Agar kal ka forecast isse upar jaaye, to woh naya record hoga.
- **"Tumhare data ka max 8,582 MW hai, par 2024 ka record 8,656 MW tha. Kyun?"** → 8,581.6 MW 15-min **average** hai, aur raw 5-min data mein usi din (19 Jun 2024) ka max 8,631.5 MW hai, dono reported 8,656 MW se thoda neeche. Averaging chhote spikes smooth kar deti hai, aur yeh gap is baat se consistent hai ki record ek finer-resolution reading ho. Lekin yeh humne verify nahi kiya, isliye "consistent hai" hi bolna, "yahi wajah hai" nahi. 29 Jun 2026 wala 8,748 MW record to dataset ke bahar hi hai.
- **"40 °C din pe 10x ageing kaise?"** → Humare transformer engine mein IEC 60076-7 ke distribution-transformer ONAN defaults hain: top-oil rise 55 K aur hot-spot gradient 23 K. Full load pe hot-spot ambient se 78 K upar hota hai, to 40 °C + 78 K = 118 °C. Ageing rate V = 2^((118 − 98)/6) = **10.08**, yaani wahi "~10x". Yeh illustrative what-if hai, kisi real transformer ka measurement nahi.

---

## Slide 3: Gap and USP

**Kya hai:** Ek side-by-side comparison, paanch rows mein.
- *Typical load-forecasting projects:* sirf ek graph, one model/one accuracy number, foreign ya toy datasets, tariff/regulation/equipment se koi link nahi, uncertainty band aur explanation nahi.
- *Our system:* forecast error ko ₹ DSM penalty (CERC 2024 + DERC limits) se jodna; model ladder, jahan har naya model simple wale ko beat kare tabhi use hoga; real Delhi SLDC 5-min data aur weather; ToD bills, transformer life, solar ramp aur losses se link; P10–P90 band aur SHAP reason.

Neeche ek highlighted USP box: ek hi Delhi forecast se six engineering engines (DSM ₹, IEX cost, ToD bill, transformer ageing, solar ramp, theft ranking) chalane ka idea, aur yeh ki Delhi forecasting, theft detection aur ToD calculators alag-alag milte hain, unka real Indian regulation pe integration naya hai. Deck ke updated version mein inme se planned items ke saath "planned" ya "Phase 2" tag ho sakta hai.

**Kyun hai:** Yeh slide tumhari "novelty" ka proof hai. Sirf "yeh unique hai" keh dena kaafi nahi; yeh slide point-by-point dikhati hai KAISE unique hai.

**Bolne ka tareeka:** "Zyada tar Delhi load-forecasting projects sirf ek graph tak ruk jaate hain. Humara forecast abhi Overview pe kal ka peak aur overload alert deta hai, aur DSM penalty aur transformer ageing ke illustrative what-if calculators usi engine ke formulas pe bane hain; unhe forecast error se jodna agla step hai. Bill, solar aur theft wale pages Phase 2 mein hain. Yeh pieces GitHub/Kaggle pe alag-alag milte hain, lekin ek hi forecast ko current Indian regulation ke against in sabse jodna, aur har number pe REAL/ILLUSTRATIVE tag lagana, yahi naya hai."

**Zaroor dhyan rakhna (slide pe jo bhi wording ho, status yahi hai):**
- **Weather:** hum Open-Meteo **archive** (historical hourly temperature aur humidity) use karte hain, live feed nahi. Agar slide ya koi purana printout "live weather" bole, to yahi correct karna.
- **SHAP:** "har forecast ka SHAP reason" abhi nahi hai. SHAP sirf 4 rule-picked dino ke liye precomputed hai; baaki dino pe Forecast page saaf likhta hai ki SHAP precompute nahi hua.
- **₹ DSM penalty from forecast error:** yeh roadmap hai. Aaj ka DSM page ek illustrative what-if calculator hai jo user ke inputs leta hai, forecast error nahi.
- **Six engines:** in mein se sirf DSM aur transformer bane hain (dono what-if); IEX, ToD, solar aur theft Phase 2 hain.

**Counter-questions (yeh sabse important hain, kyunki tumhari apni priority hai ki uniqueness sach mein check ki jaaye):**
- **"Tumne kaise confirm kiya ki yeh unique hai, sirf assume to nahi kar liya?"** → Deck (Slide 3) aur report (Section 6) kehte hain ki yeh pieces open-source (GitHub/Kaggle) pe alag-alag milte hain: Delhi load forecasting, theft detection aur ToD calculators teeno **alag-alag** projects ki tarah milte hain, lekin ek hi Delhi forecast se in sabko **CERC 2024 aur DERC limits ke against ek saath** nikalne wala koi open/published project nahi mila. Novelty yeh integration hai, individual pieces nahi. (Search kaise kiya, yeh tabhi batana jab tumne sach mein kiya ho.)
- **"Tum khud bhi London Smart Meters aur SGCC (foreign) dataset use karoge, phir doosron ko 'foreign dataset' bolke criticize kaise kar sakte ho?"** (Yeh sharp catch hai, ready raho.) → Abhi tak jo bana hai usme koi foreign dataset use hi nahi hua: built pages (01–06 aur 12) REAL SLDC + Open-Meteo data aur ILLUSTRATIVE calculators pe chalte hain, aur synthetic categories sirf Data & Model Card pe listed hain. London aur SGCC sirf Theft & segments (page 11) ke plan mein hain, jo abhi bana nahi, kyunki India mein consumer-level labelled data public nahi hai. Jab use honge, tab dashboard pe `FOREIGN` badge ke saath dikhenge (`docs/PROVENANCE.md` ka rule). Yahi transparency fark hai.
- **"'Model ladder' ka matlab practically kya hai?"** → Har naya, zyada complex model tabhi include hota hai jab woh apne se simple baseline ko beat kare. Humare case mein ladder aisa chala, common real-row test set pe: seasonal-naive 5.22% → pehla LightGBM 4.93% (jo h = 74–96 pe naive se haar raha tha, isliye hum ruk ke debug kiye) → causal imputer + target-aligned lags 4.00% → causal Hampel + profile-fill fix 3.92%. Poore test set pe final model 3.93% hai, naive 5.16%. SARIMAX (hourly) code mein implemented hai, lekin uska sirf validation pe order search hua; test result nahi hai, isliye woh ladder ke reported numbers mein nahi hai, aur uska koi number mat bolna. N-HiTS aur Chronos proposal-stage ideas hain, run nahi hue; banenge to unhe 3.93% beat karna padega.
- **"'Six engineering engines' mein se kitne bane?"** → Un six (DSM, IEX, ToD, transformer, solar, theft) mein se DSM aur transformer bane hain, dono illustrative what-if calculators ki tarah. Baaki chaar roadmap pe hain. Iske alawa overview (peak/alert), load analytics (LF/PAR) aur weather (β) ke engines bhi bane hain, aur sab deck ke worked examples ke against test kiye gaye hain.

---

## Slide 4: Proposed Solution (System Workflow), YEH SABSE IMPORTANT SLIDE HAI

Poora system architecture ek hi jagah hai, aur panel iski sabse zyada grilling karega, isliye extra dhyan se padho. Yaad rakho: yeh slide **design** dikhati hai. Har box ke saath bolna padega ki usme se kitna bana hai.

**Flow:** `1 DATA → 2 PREPARE + CHARACTERISE → 3 AI FORECAST → 4 FORMULA ENGINE → 5 OUTPUT → 6 DASHBOARD`

**Step 1, Data (4 sources):** slide pe Delhi SLDC 5-min load, Open-Meteo weather, IEX 15-min prices aur IoT meter (ESP32+PZEM) dikhte hain.
- *Bana:* SLDC (Kaggle mirror `prash4nt/delhi-sldc-load-data-5-min-resolution`, delhisldc.org) aur Open-Meteo archive (hourly temperature, humidity → heat index), saath mein holiday aur IPL calendar.
- *Nahi bana (planned):* IEX prices aur IoT meter.

**Step 2, Prepare + Characterise:**
- Clean: IST timezone, gaps fill karna, 15-min blocks banana (5-min ka mean), weather join karna. Slide pe "prices" ka join bhi design mein hai; prices abhi join nahi hote. Cleaning **causal** hai: imputer aur Hampel outlier filter sirf peeche ka data dekhte hain. Yeh Phase 3 ka bada fix tha.
- Features: lags (purane values), heat index, night temp, holidays aur IPL season. Festivals sirf holiday flag (`is_holiday`, `target_is_holiday`) ke through aate hain; **alag festival feature nahi hai**.
- **Consumer category ke hisaab se characterise karna:** slide pe 6 categories hain: Residential (AC-driven night peak, weekends), Industrial (shift hours, Sunday dip), Public utilities (Metro, water pumping, street lights), Commercial (10am–10pm), Agricultural (pump hours, rabi/kharif), EV charging (evening/night clusters).
  - *Honest status:* SLDC ke paas per-category feed hai hi nahi. Isliye categories ek **SYNTHETIC** parametric generator se bani hain (load = base + daily + weekly + heat effect + noise + event bumps). Built generator sirf **5 categories** banata hai (residential, commercial, industrial, agricultural, EV); public utilities nahi hai. In categories ka sum real aggregate ke saath peak timing, LDC shape aur lag-1-day autocorrelation pe compare hota hai. Yeh forecast input nahi hain aur kisi page pe plot nahi hoti.

**Step 3, AI Forecast P̂(t)** (green box): slide pe model LightGBM hai, N-HiTS aur Chronos planned ke taur pe; output next day ke 96 blocks, Delhi total load; saath mein P10–P90 band aur SHAP reason; aur yeh forecast dashboard pages ko feed karta hai.
- *Jo bana:* ek **single multi-horizon LightGBM** (horizon bhi ek feature hai, 37 features), jo **poore Delhi ka total load** agle din ke 96 blocks ke liye forecast karta hai. Dashboard pe origin pichhli shaam 23:45 hai. Saath mein split-conformal P10–P90 (80%) band hai, aur sirf 4 rule-picked dino ke liye TreeSHAP.
- Per-category forecast nahi hai, aur N-HiTS/Chronos run nahi hue. Forecast abhi Overview aur Forecast page ko feed karta hai; baaki pages ka link design hai (neeche "Forecast kaunse pages ko feed karta hai" dekho).

**Step 4, Formula Engine (12 equations):** slide pe 12 rows ka grid hai: har row mein equation image, ek output example aur dashboard page ka naam. Equations: peak & alert, LF & PAR, heat sensitivity, MAPE, DSM charge, power purchase cost, ToD bill, transformer ageing, voltage rise & net load, PF correction & loss, energy balance + theft, band coverage. Detail Slide 7 mein hai. In 12 mein se **7 bane hain**: peak/alert, LF/PAR, heat sensitivity, MAPE, DSM, transformer ageing aur band coverage.

**Step 5, Output:** har formula ka plain-English result. Built rows ke real/illustrative numbers: MAPE 3.93% (full test set, Jul 2025–Jan 2026), LF 0.503 / PAR 1.99 (real, poora period), +3 °C heat index ≈ +336 MW, ₹3.475 lakh/hr penalty (illustrative), hot-spot 118 °C → ~10x ageing (illustrative), aur band coverage: 80% band, test pe 84.4%. ToD (₹117/month), solar (+5.2% voltage) aur losses (844 kVAR) wale outputs deck ke worked examples hain un pages ke liye jo Phase 2 mein hain.

**Step 6, Dashboard:** 12 named pages, jinka detail Slide 8 mein hai. Bane hain 01–06 aur 12 (Data & Model Card); 07–11 Phase 2 hain.

**Bolne ka tareeka (ek baar zaroor bolke practice karo, kyunki panel literally bol sakta hai "pipeline explain karo"):** "Data real Delhi SLDC 5-min load aur Open-Meteo archive weather se aata hai. Usse causally clean karte hain, matlab gap bharte waqt sirf peeche ka data dekhte hain. Phir 15-min blocks banake features banate hain: lags, heat index, calendar. Yeh data ek multi-horizon LightGBM mein jaata hai jo agle din ke 96 blocks predict karta hai, ek 80% band ke saath, aur chune hue dino pe SHAP reason ke saath. Wahi forecast Overview pe peak aur alert nikalta hai. DSM aur transformer pages abhi illustrative what-if calculators hain jinke formulas same engine mein hain. Design mein yahi forecast baaki pages (IEX, ToD, solar, theft) ko bhi feed karega, jo Phase 2 mein hain."

**Counter-questions:**
- **"Consumer category-wise kyun, ek hi generic model kyun nahi?"** → Design intent yeh hai ki residential, industrial, commercial, agricultural aur EV, sabka timing aur driver alag hota hai. Lekin honest answer: SLDC sirf aggregate load deta hai, isliye humara built forecast poore Delhi ka total hai. Category curves synthetic hain (5 categories), aur synthetic data ka forecast karna apne hi generator ko predict karna hota, isliye woh na forecast input hain na kisi page pe plot hoti hain.
- **"LightGBM, N-HiTS, Chronos, teeno kyun? Ek hi kaafi nahi?"** → Yeh "model ladder" ka plan tha. LightGBM tree-based hai: features (lags, weather, calendar) leta hai, fast aur interpretable hai. N-HiTS ek deep-learning time-series model hai, aur Chronos ek pretrained foundation model jo zero-shot forecast deta hai. Abhi tak seasonal-naive aur LightGBM test pe score hue hain (SARIMAX code mein hai par test pe score nahi hua). Rule yeh hai ki N-HiTS ya Chronos tabhi aayenge jab woh 3.93% ko beat karein.
- **"P10–P90 band ka matlab kya hai, sirf ek number kyun nahi?"** → Point forecast ki jagah ek range dete hain. P10 woh value hai jiske neeche actual aane ka 10% chance hai, aur P90 ke neeche 90% chance. Isliye P10–P90 ek **80%** central interval hai. Humara target 80% tha, aur test pe 84.4% forecasts (origin × horizon) ka actual band ke andar aaya.
- **"SHAP kya hai?"** → SHapley Additive exPlanations: game theory ki Shapley value pe based explainability method. Yeh batata hai ki forecast mein har feature (past load, heat, din) ne kitna contribute kiya. Humare 4 precomputed dino pe `tlag_1day` (same block, kal) har din sabse bada driver hai. "Kya" ke saath "kyun" bhi milta hai.
- **"Formula engine ka forecast se connection exactly kaise hai?"** → Jab P̂(t) ke 96 values ban jaate hain, to Overview engine unme se max leta hai aur 8,748 MW limit se compare karta hai. Forecast page wahi 96 values band ke saath dikhata hai. DSM aur transformer engines abhi user ke what-if inputs lete hain (defaults deck ke worked examples hain), forecast error nahi. Unhe forecast se jodna roadmap pe hai.

---

## Slide 5: Data Strategy

**Kya hai:** 3 types of data, har chart pe label karke:
1. **Online open data (primary, real):** Delhi SLDC 5-min (Kaggle mirror, delhisldc.org), Open-Meteo (free, no key), IEX prices, Grid-India/CEA reports, London Smart Meters + SGCC theft set (jahan Indian consumer data public nahi hai).
   - *Use hue:* SLDC aur Open-Meteo (archive). Baaki (IEX, Grid-India/CEA, London, SGCC) abhi nahi; deck pe inke saath "planned" tag ho sakta hai.
2. **Synthetic data:** Formula "Load = base + daily + weekly + heat effect + noise + events". Slide ki tools line mein LoadProfileGenerator aur demandlib likhe ho sakte hain (yeh proposal ke tools the); asal mein humne apna parametric generator likha (`lpmf.synthetic`, numpy/pandas), aur woh tools use nahi hue. Deck ne feeder, transformer aur household scenarios plan kiye the, lekin built generator sirf **5 consumer categories** banata hai (residential, commercial, industrial, agricultural, EV). Inka sum real aggregate se peak timing, LDC shape aur autocorrelation pe compare hota hai. Yeh dashboard pe plot nahi hoti; sirf Data & Model Card pe SYNTHETIC badge ke saath listed hain.
3. **Physical data:** ESP32+PZEM-004T lab/hostel circuit pe. Har minute V, I, P, PF, kWh aur frequency log hota, 3 meters se R-Y-B phase imbalance milta, aur live tab MQTT ke through chalta. *Status:* optional hai aur abhi bana nahi.

Neeche pipeline: Collect → Clean (IST, gaps) → Resample 15-min → Join weather → Engineer features → Train/test split.

**Real numbers jo is slide pe kaam aayenge:**
- Coverage: 1 Apr 2023 se 12 Jan 2026 23:45 IST.
- 5-min grid pe 293,184 rows expected the, 285,252 present the (**2.705% missing** imputation se pehle).
- 15-min pe 97,728 rows hain, jinme se 1,330 rows (**1.361%**) imputation ke baad bhi missing hi chhodi. Unhe fake value se nahi bhara.
- Split strictly chronological hai, kabhi shuffle nahi kiya: train 2023-04-01 se 2025-01-12, val 2025-01-13 se 2025-07-12 (Mar–Jun 2025 ki garmi isi mein hai), test ke target days 2025-07-13 se 2026-01-12 (pehla origin 12 Jul 23:45; 184 calendar din, 183 pe data, 8 Jan 2026 ka koi test target nahi).

**Kyun hai:** Yeh transparency dikhata hai ki kaunsa number real hai aur kaunsa nahi. Academic aur engineering rigor ke liye yeh zaroori hai.

**Counter-questions:**
- **"Consumer-level real Delhi data nahi hai, phir 'real data' ka dava kaise?"** → Grid-level demand (SLDC 5-min) real hai, aur humara poora forecast usi pe hai. Individual-household granularity India mein public nahi hai, isliye wahan synthetic (aur aage chal ke foreign) data hai, aur woh clearly label hota hai.
- **"Synthetic data ko validate kaise karte ho ki realistic hai?"** → Saari categories ka sum real Delhi aggregate ke saath same timestamps pe compare hota hai: peak timing, load duration curve ka shape aur lag-1-day autocorrelation. Code yeh comparison numbers report karta hai, koi pass/fail grade nahi deta. Aur kyunki yeh data kisi forecast ya page mein use nahi hota, iska kaam sirf ek labelled stand-in hai.
- **"Missing data kaise handle kiya?"** → Raw 5-min data mein 2.705% gaps the. Imputer **causal** hai, yaani gap bharne ke liye sirf us time se pehle ka data dekhta hai. Jo bach gaye (15-min pe 1.361%), unhe fake value se bharne ki jagah NaN hi chhoda. Model ladder aur ablation ke comparisons sirf un test rows pe hue jinka actual real reading tha, imputed nahi.
- **"Physical IoT setup ka role sirf ek 'live tab' hai?"** → Haan, aur woh bhi abhi bana nahi, yeh optional hai. Iska scale Delhi grid jaisa nahi hai. Purpose sirf yeh prove karna hai ki pipeline (sensor → MQTT → InfluxDB → dashboard) real hardware pe end-to-end kaam karti hai.

---

## Slide 6: Physical Data Collection (Hardware)

> **Status:** yeh poora slide proposed/optional hardware ka hai. Repo mein abhi koi IoT code nahi hai. Agar poochhe "yeh bana hai?", to seedha bolo: "Nahi, yeh optional proof-of-concept hai jo agla step hai. Humara poora result SLDC data pe hai."

**Kya hai:** Pipeline: `230V load → PZEM-004T+CT → ESP32 → MQTT broker (Mosquitto) → InfluxDB → Dashboard`. DHT22/BME280 (temp+humidity → heat index) ESP32 ko feed karta hai. Component table (prices deck ke approximate market estimates hain):
- PZEM-004T v3 (₹500–800): V/I/P/energy/PF/frequency napta hai, UART/Modbus se bhejta hai
- SCT-013 CT clamp (₹300–600): bina wire kaate current sense karta hai
- ESP32 (₹350–600): har minute meter padhta hai, WiFi/MQTT se JSON publish karta hai
- DHT22/BME280 (₹250–300): local temp/humidity
- Smart plug Shelly/Tasmota (₹800–1,500): appliance-level, no wiring, safest
- Raspberry Pi optional (₹4,000+): local Mosquitto+InfluxDB server

Safety box: 230V mains khatarnak hai. Clamp-on sensing only, saare terminals enclosed, aur AC side qualified electrician wire karega. Core kit ≈ ₹1,500–4,000.

**Counter-questions:**
- **"CT clamp bina wire cut kiye current kaise measure karta hai?"** → SCT-013 wire ke around clip hota hai. Jab wire mein current flow karta hai, ek changing magnetic field banta hai. Electromagnetic induction (Faraday's law) se yeh field CT ki secondary coil mein proportional chhota current induce kar deta hai, isliye koi direct contact ya cutting nahi chahiye.
- **"MQTT hi kyun, direct database write kyun nahi?"** → MQTT ek lightweight publish-subscribe protocol hai jo low-power IoT devices ke liye bana hai. Yeh reliable aur real-time hai, aur ek hi published data ko dashboard, database aur alerts, sab ek saath use kar sakte hain.
- **"Lab-scale setup Delhi grid ka scale kaise represent karta hai?"** → Nahi karta. Iska maksad scale nahi, sirf pipeline proof hai. Grid-scale forecasting ke liye actual Delhi SLDC bulk data use hota hai.

---

## Slide 7: Mathematical Model (12 equations)

**Kya hai:** 12 equation tiles; subtitle batata hai ki yeh dashboard ke peeche ki engineering equations hain. Har tile mein What, Why, Ref, ek Ex (worked example) aur "Shown on" (kaunse page pe) hai. Speaker notes mein DSM worked example ka poora hisaab, β fit ka detail aur band coverage ka detail hai.

Har equation ke saath ek page ka naam hai, lekin honestly bolna: 12 mein se sirf **7 ke pages bane hain** (neeche table). Baaki 5 equations ke pages Phase 2 hain, to unke Ex values deck ke worked examples hain, kisi built page ka output nahi. "Har equation ka result dashboard pe dikhta hai" sirf in 7 ke liye sach hai.

| Equation | Kya karta hai | Example (tag) | Dashboard page (status) |
|---|---|---|---|
| Peak & overload alert: P̂peak = max P̂(t) | Din ka highest forecast load, aur kab aata hai | Deck ka Ex ek chhota illustrative example hai (jaise 820 kW at 19:00 > 800 kW limit → alert). Live page pe limit = 8,748 MW Delhi record | Overview (bana) |
| Load factor & PAR: LF = Pavg/Pmax, PAR = 1/LF | Load kitna "peaky" hai | Deck: 530/820 = **0.646**, PAR 1.55 (ILLUSTRATIVE). Real poora period: **LF 0.503, PAR 1.99** | Load analytics (bana) |
| Heat sensitivity: ΔP ≈ β·ΔHI (saare 15-min blocks pe, sirf peak pe nahi) | Har °C heat index badhne pe kitna extra MW | **β = 112.0 MW/°C, r² = 0.61** (apna OLS, saare 96,398 15-min blocks). +3 °C ≈ +336 MW (REAL) | Weather impact (bana) |
| MAPE: (100/n)Σ\|y−ŷ\|/y | Forecast accuracy % | **3.93%** full test set (Jul 2025–Jan 2026), naive 5.16% (REAL) | Forecast (bana) |
| DSM deviation charge | Deviation ka ₹ penalty | 60 MW vs 41 MW limit → **₹3.475 lakh/hr** (ILLUSTRATIVE) | DSM ₹ calculator (bana, what-if) |
| Power purchase cost: Σ pb·Eb | Har block ki price × energy | 100 MWh ≈ ₹9.7 lakh night vs ₹1.1 lakh midday (deck example, EAC-PM prices) | IEX price (roadmap) |
| ToD bill: ΣEh·r0·mband(h) | Peak/solar/normal rate se bill | ₹117/month saved (deck worked example) | ToD bill simulator (roadmap) |
| Transformer ageing: V = 2^((θh−98)/6) | Hot-spot temp se relative ageing rate | Hot-spot **118 °C → V = 10.08** (40 °C ambient, full load, IEC ONAN defaults) (ILLUSTRATIVE) | Transformer health (bana, what-if) |
| Voltage rise: ΔV ≈ (PR+QX)/V | Solar export se voltage change | 30 kW export → +5.2% (deck worked example) | Solar & net load (roadmap) |
| PF correction: Qc = P(tanφ1−tanφ2) | Capacitor size + copper loss saving | 844 kVAR → −16% loss (deck worked example) | Losses & PF (roadmap) |
| Energy balance + theft: Eloss = EDT−ΣEi−Etech | Non-technical loss, Isolation Forest se ranking | Top-k ko precision@k se rank karna | Theft & segments (roadmap) |
| Band coverage: N(P10≤y≤P90)/n | Kitne actuals band ke andar aaye | **Target 80%, test pe 84.4%** (REAL) | Forecast + Data & model card (bana) |

**Quick mental math jo panel ke saamne bol sakte ho (impressive lagta hai):**
- **Transformer:** (118 − 98)/6 = 3.33, aur 2^3.33 ≈ 10.08. Hot-spot 118 °C pe ek ghanta chalana insulation ki ~10 ghante ki life kha jaata hai.
- **PAR:** 1/0.646 = 1.548 ≈ 1.55. (Purane guide mein 0.647 likha tha, jo galat rounding tha. 530/820 = 0.6463, to sahi value 0.646 hai.)
- **Real LF:** 4,316/8,582 = 0.503, aur PAR = 8,582/4,316 = 1.99.
- **Heat:** 3 × 112.0 = 336 MW.
- **DSM:** har block mein 41 × 5,000/4 = ₹51,250, plus 19 × 1.5 × 5,000/4 = ₹35,625, total ₹86,875. Ek ghante (4 blocks) mein 4 × ₹86,875 = ₹3,47,500 = ₹3.475 lakh/hr.

**Pehle yeh gotcha tha, ab nahi hai:** P10–P90 by definition **80% interval** hai (90th − 10th percentile). Purane deck pe target "~90%" likha tha. Ab deck (Slide 4 ki band-coverage row aur Slide 7 ka band-coverage tile) dono pe **target 80%, test pe 84.4%** hai, aur yahi `docs/MODEL_RESULTS.md` mein hai. Agar koi purana printout ya purana deck "~90%" dikhaye, to seedha correct kar do: "Woh purana text hai. P10–P90 ek 80% interval hai, humara target 80% tha aur test pe 84.4% mila." Yahan "safety margin" ya "rounded target" wala bahana mat dena, sach yahi hai.

**β ke baare mein:** purane guide mein "β ≈ 140–150 MW/°C" likha tha, aur purane report/deck text mein 111.6. Ab locked value **112.0 MW/°C** (112.044) hai, `docs/DATA_QUALITY.md` se. Wahi number Weather Impact page use karta hai. Slide 7 ka equation ab **ΔP ≈ β·ΔHI** padhta hai (purani image pe ΔP_peak tha). Yeh sahi hai, kyunki fit saare 15-min blocks pe hai, sirf daily peak pe nahi. Isi wajah se humara r² = 0.61, CSE ke daily-peak 67% se compare nahi hota.

**Aur ek honest point:** agar poochhe "₹3.475 lakh/hr real number hai?", to seedha bolo: "Nahi, yeh formula ka worked example hai. 60 MW deviation ek ghante tak, BRPL ki 41 MW volume limit (DERC), flat normal rate ₹5,000/MWh aur excess pe 1.5x assume kiya hai. Real number tabhi aayega jab CERC 2024 ke frequency-linked normal-rate tables encode karenge."


**Report ke Table 4 mein ek extra formula:** LLF = 0.3·LF + 0.7·LF² (Gönen, loss load factor). Yeh deck ke 12 equations mein nahi hai aur kisi page pe implemented nahi hai; report mein reference formula ki tarah hai. Poochhe to seedha bolo: "LLF losses ke estimate ke liye standard formula hai, Phase 2 ke Losses & PF page ke liye; abhi built nahi."
---

## Slide 8: Dashboard (12 Pages)

**Kya hai:** 12 cards, 01 se 12 tak, har ek ek operational question ka jawab deta hai. Numbering app ke nav jaisi hi hai. Forecast (04) wala card green highlight hai. Deck pe 07–11 ke saath "Phase 2" tag ho sakta hai.

- **01 Overview:** abhi ka load, aaj ka peak, kal ka forecast, alerts. *Bana:* test window ke aakhri din (12 Jan 2026) ka day-ahead peak, peak time + 8,748 MW alert. "Load now" aur "today's peak" nahi bane.
- **02 Load analytics:** load curve, duration curve, LF, PAR, heatmap. *Bana:* poore period ka LF, PAR, average/peak aur duration curve. Load curve, heatmap aur date control nahi bane.
- **03 Weather impact:** load vs heat index, what-if slider. *Bana:* β fit aur daily-mean scatter. What-if slider nahi bana.
- **04 Forecast** (highlighted, sabse important): 96 blocks, P10–P90, model comparison, SHAP. *Bana* (SHAP sirf 4 precomputed din).
- **05 DSM ₹ calculator:** design mein "har model ki error kitni penalty banaegi". *Bana:* sirf illustrative what-if, forecast error nahi padhta.
- **06 Transformer health:** hot-spot temp, life used, overload hour. *Bana:* illustrative what-if (hot-spot slider: ageing rate + life used), forecast se nahi juda. "Overload hour" nahi bana.
- **07 IEX price:** mehenge blocks, purchase cost profile. *Phase 2.*
- **08 ToD bill simulator:** flat vs ToD vs optimised bill, shift advice. *Phase 2.*
- **09 Solar & net load:** duck curve, evening ramp, voltage risk. *Phase 2.*
- **10 Losses & PF:** I²R loss, kVAR needed, phase imbalance. *Phase 2.*
- **11 Theft & segments:** suspicious meters, consumer load-shape groups. *Phase 2.*
- **12 Data & model card:** source, real vs synthetic, accuracy, limits. *Bana (Phase 8).*

**Counter-questions:**
- **"Forecast page hi highlight kyun hai?"** → Kyunki design mein yahi central page hai: baaki pages ka data isi forecast se derive hona hai (Slide 4 ka green AI Forecast box bhi yahi dikhata hai). Abhi ke build mein yeh Overview ko seedha feed karta hai, aur baaki pages us design ke hisaab se aage judenge.
- **"Load duration curve kya hoti hai?"** → Load values ko time-sequence ki jagah descending order mein plot karte hain. Usse dikhta hai ki kitne ghante load ek certain level se upar raha, jo capacity planning ke liye useful hai.
- **"Data & Model card page kis liye hai, normal user ko iski zarurat kya?"** → Yeh transparency aur accountability page hai, ML model ke liye ek "nutrition label" jaisa. Isse engineer ko pata rehta hai ki kis result pe kitna trust karna hai. Ismein kya dikhta hai, woh neeche naye questions wale section mein hai.
- **"Sirf 7 pages kyun bane, 12 kyun nahi?"** → Humne pehle core chain banayi: data → forecast → uncertainty → explanation, do engineering calculators (DSM, transformer) aur ek Data & Model Card. Kyunki baaki sab pages isi pe khade honge, forecast ka sahi hona pehle zaroori tha, aur wahi Phase 3 ka bada kaam tha. Baaki 5 pages (07–11) roadmap pe hain, aur nav mein "Phase 2" ki tarah clearly marked hain.

---

## Slide 9: Technology Stack

**Kya hai:** Layered stack, "100% free and open-source". Yeh slide proposal-stage ka poora stack dikhati hai; deck ke updated version mein built aur planned items alag ya tag ke saath ho sakte hain. Proposal list yeh thi:
- **Frontend:** React, Plotly.js, Streamlit (prototype)
- **API:** FastAPI (Python), REST + WebSocket
- **AI/ML:** LightGBM, XGBoost, NeuralForecast, Chronos-Bolt, MAPIE, SHAP, scikit-learn
- **Engineering engines:** pandapower, pvlib, PuLP, IEC 60076-7 model, DSM/ToD calculators
- **Data:** pandas, PostgreSQL/DuckDB, InfluxDB (IoT)
- **IoT + infra:** ESP32, MQTT (Mosquitto), Docker, GitHub, H200 GPU (training)

"Why this stack" box: same FastAPI+React pattern jo TPIOS platform mein use hua; koi paid API/licence nahi; heavy training H200 pe, light models CPU pe; Chronos/TimesFM Apache-2.0 licence.

**Asal mein kya use hua (yeh pehle se ready rakho):**
- *Frontend:* Next.js 15 (React 19), Tailwind, Recharts (charts), KaTeX (equations). NextAuth (Auth.js v5) se Google login aur email OTP, Prisma + SQLite.
- *API:* FastAPI + Pydantic v2, sirf REST.
- *ML:* LightGBM, Optuna (tuning), MAPIE 1.6 (conformal), SHAP 0.54 (TreeSHAP), statsmodels (SARIMAX code, test pe score nahi hua), pandas/pyarrow (parquet pipeline), pandera (schema checks), pytest.
- *Engines:* apne Python engines (overview, load analytics, weather, DSM, transformer IEC 60076-7).
- *Abhi use nahi hue:* NASA POWER (report Table 1 mein naam hai, data use nahi hua), Plotly.js, Streamlit, WebSocket, XGBoost, NeuralForecast, Chronos-Bolt, TimesFM, pandapower, pvlib, PuLP, PostgreSQL/DuckDB, InfluxDB, MQTT, Docker, **GitHub** (repo local hai, abhi koi remote nahi) aur **H200** (abhi kisi built model ke liye use nahi hua). Yeh roadmap pages ke saath aayenge.

**Counter-questions:**
- **"Streamlit aur React dono kyun, ek kaafi nahi?"** → Plan mein Streamlit rapid prototype ke liye tha. Practically humne seedha Next.js (React) pe production-style dashboard bana diya, isliye Streamlit ki zarurat nahi padi.
- **"WebSocket ki zarurat kyun, REST kaafi nahi?"** → WebSocket live IoT data ke liye plan tha, taaki dashboard baar-baar poll kiye bina updates le sake. Abhi koi live feed nahi hai (dashboard backtest replay karta hai), isliye abhi sirf REST hai.
- **"H200 GPU kahan se, paid resource to nahi?"** → Yeh apna hi available H200 server hai, koi cloud rental nahi. (Yeh tumhari apni detail hai, bolne se pehle khud confirm kar lena.) Abhi tak kisi built model ke liye H200 use nahi hua: LightGBM jaise tree model ko GPU ki zarurat hi nahi, woh CPU pe bhi aaram se train ho jaata hai. H200 heavy deep-learning models (N-HiTS, Chronos) ke liye plan mein hai, jo abhi bane nahi.
- **"TPIOS kya hai jo yahan reference kiya hai?"** → Woh production platform hai jo tumne Salasar ke liye banaya hai. FastAPI + Next.js + MySQL stack pe hai, 28+ projects track karta hai senior management ke liye, aur salasarepc.in pe live hai. Isi proven architecture pattern ko yahan reuse kiya, taaki architecture mein naya risk na lena pade. (Yeh tumhari apni details hain, bolne se pehle khud confirm kar lena.)

---

## Slide 10: References

**Kya hai:** 20 references. Government/regulatory sources (PIB, Delhi SLDC, CERC, DERC, IEC, EAC-PM, PFC/MoP), textbooks (Kothari & Nagrath, Mehta, Gönen), aur research papers (Hyndman & Athanasopoulos forecasting book, Chronos arXiv paper, Conformal Prediction paper, pandapower IEEE paper, Isolation Forest ICDM paper).

**Kyun hai:** Har number aur equation ka source hai, koi claim "hawa mein" nahi hai.

**Counter-questions:**
- **"Sabse important 2–3 reference kaunse hain?"** → CERC DSM Regulations 2024 (penalty formula ka legal basis), CSE 2025 report (problem statement ka 67% heat-index number; yeh unka daily-peak metric hai, humara result nahi), aur IEC 60076-7:2018 (transformer ageing formula ka industry standard).
- **"Tumhare apne numbers (3.93%, 112.0 MW/°C, 84.4%) ka reference?"** → Yeh hamara apna backtest hai, kisi paper ka number nahi. Poora method aur numbers `docs/MODEL_RESULTS.md` aur `docs/DATA_QUALITY.md` mein documented hain. Ablation ke arm results, deltas aur iid-day CIs do alag audit runs ne exactly reproduce kiye; yeh dono runs separate AI review agents the (AI-assisted, log nahi).
- **"Chronos ka paper?"** → A.F. Ansari et al., "Chronos: Learning the Language of Time Series," arXiv 2403.07815, 2024. Yeh Amazon Science ka paper hai, jisme language-model jaisi approach se time series forecast kiya jaata hai. (Chronos abhi humne implement nahi kiya, yeh reference plan ke liye hai.)

---

## Slide 11: Thank You

Sirf closing hai: project ka naam, "Thank you", "we welcome your questions and feedback", team ke naam aur guides ke naam. Koi chart nahi hai. Yahan koi technical grilling nahi hoti. Bas confident smile ke saath khatam karo aur Q&A ke liye ready ho jao. Yeh transition point hai, isliye "chalo khatam hua" wala relief mat dikhana. Panel ko lagna chahiye ki tum aage aane wale questions ke liye bhi utne hi ready ho.

---

## Cross-cutting questions: kisi bhi slide ke baad aa sakte hain

- **"Yeh abhi ban chuka hai ya sirf proposal/plan hai?"** → Ab exact honest status hai (upar "Honest status" section dekho). Bolna aise: "Data pipeline, forecasting model, uncertainty band, 4 dino ka SHAP, aur 6 dashboard pages plus Data & Model Card bane hain aur chal rahe hain, login ke saath. Forecast real backtest hai: 3.93% MAPE on test. DSM aur transformer pages what-if calculators hain. IEX, ToD, solar, losses aur theft wale 5 pages, N-HiTS/Chronos, aur IoT hardware abhi roadmap pe hain."
- **"Tumne individually kya kiya?"** → Report ke Work Distribution section (Section 7, Table 5) ke hisaab se tum (group leader): literature/policy research, problem identification/USP, system architecture/workflow, mathematical modelling (DSM, ToD, ageing, voltage, losses), forecasting model & validation design, aur report+PPT preparation. (Yeh list purane guide se aayi hai; bolne se pehle report ki table se khud confirm kar lena.) Yeh crisp bolke ready rakho.
- **"AI/ML aur EE dono kaise mix hue isme?"** → EE side: power system equations (LF, PAR, IEC ageing, DSM; voltage rise aur PF correction roadmap pe), grid regulation knowledge, aur hardware measurement (plan). AI/ML side: forecasting model (LightGBM), SHAP explainability, conformal prediction (uncertainty), aur aage Isolation Forest (anomaly detection). Poore project ka USP yahi hai ki AI forecast tabhi useful banta hai jab woh EE domain equations se guzre.
- **"Total cost kitna aayega?"** → Software ₹0, kyunki sab free/open-source hai. Hardware (optional IoT proof-of-concept, abhi bana nahi) ka core kit ₹1,500–4,000.
- **"Agla step kya hai?"**
  1. Baaki 5 pages (IEX, ToD, solar, losses, theft) banana.
  2. Jan 2026 ke baad ka naya data lekar ek **fresh holdout** banana jisme 2026 ki garmi bhi ho, taaki summer-peak accuracy test ho sake.
  3. Diwali jaise festivals ke liye better holiday features.
  4. Very short horizons (h = 1–2) ke liye persistence ya intraday model.
  5. CERC ke frequency-linked DSM rate tables encode karna, aur DSM ko actual forecast error se jodna.
  6. Ladder pe N-HiTS/Chronos try karna.
  7. IoT proof-of-concept.

---

## Theft & segments: deep dive

> **Status:** page 11 abhi **bana nahi hai** (roadmap, Phase 2). Neeche jo hai woh plan hai. Bolte waqt future tense hi use karna ("karenge"), "kar rahe hain" nahi.

"Theft & segments" wala page poore dashboard mein sabse technical hai aur isme bahut grilling ho sakti hai. Poora breakdown:

### Yeh page do kaam karega (yeh pehle clear kar do)

1. **Non-technical loss/theft detection:** kaunse feeder ya meter mein energy "gayab" ho rahi hai.
2. **Consumer segmentation:** consumers ko unke load-shape ke hisaab se groups mein baantna.

Dono alag techniques hain, lekin ek hi page pe hain kyunki dono "consumer-level behaviour" analyse karte hain.

### Kaise karenge: step by step pipeline

**Step 1, feeder-level energy balance (macro check):**
`E_loss = E_DT − ΣE_i − E_tech`
- E_DT = feeder/transformer ne kitni energy deliver ki
- ΣE_i = sab consumers ka combined billed energy
- E_tech = **expected** technical loss (I²R heating). Yeh **pandapower** (Python power-flow simulation library) se nikalenge, feeder ki known topology (conductor length, resistance, load points) daal ke.
- Jo bacha (E_loss) woh non-technical loss hai, yaani theft ya meter-tampering ka suspect zone. Agar E_loss, E_tech se kaafi zyada hai to woh feeder "red flag" ban jaata hai.

**Step 2, meter-level ranking (micro check):** Har individual meter ke consumption pattern pe **Isolation Forest** (unsupervised anomaly detection algorithm) chalayenge, jo har meter ko ek "suspicious score" dega.

**Step 3, consumer segmentation:** Har consumer ka normalized daily/weekly load-shape leke uspe **clustering** (k-means jaisa) lagayenge, taaki similar-pattern consumers ek group (segment) mein aa jaayen, jaise "raat-heavy AC users", "flat industrial 24x7", "daytime commercial".

**Step 4, cross-check:** Agar koi consumer apne segment ke typical pattern se bahut door hai (jaise "residential" segment mein hoke bhi industrial jaisa flat load), to woh bhi ek additional red flag ban jaata hai.

### Isolation Forest kaam kaise karta hai (yeh definitely poochha jaayega)

Random tree-based algorithm hai. Random feature aur random split value choose karke data ko baar-baar partition karta hai. Normal points (jo dense cluster mein hote hain) ko isolate karne mein zyada splits lagte hain, jabki anomalies ("few and different") bahut **kam splits mein hi isolate** ho jaate hain. Kai random trees ke across har point ka average path length uska anomaly score banta hai: **chhota path length = zyada suspicious**. Isiliye yeh unsupervised hai aur bina labels ke bhi outliers dhundh leta hai. Delhi jaisi jagah ke liye yeh perfect hai jahan real theft labels available nahi hain.

### Data kahan se

> **[TODO: verify]** Neeche ke dataset numbers purane guide mein web search se aaye the. Yeh datasets abhi repo mein download ya use nahi hue, isliye in numbers ko repo se verify nahi kiya ja saka. Viva se pehle Kaggle page khol ke confirm kar lena.

**1. SGCC (State Grid Corporation of China) Electricity Theft Detection dataset:**
- **42,372 consumers**, daily consumption **Jan 2014 se Oct 2016 tak** (~1,035 days / ~147 weeks)
- CSV format, ~167 MB
- Columns: Consumer ID + daily consumption values + last column **FLAG** (0 = normal, 1 = theft)
- **3,615 consumers (8.55%)** theft labelled hain. Yeh **real ground-truth-labelled dataset hai**, aur India mein aisa kahin nahi milta.
- ~25% missing data hai, jise handle karna padega
- **Kaggle pe free aur public**, koi cost ya login restriction nahi

**2. London Smart Meters (Low Carbon London project):**
- **~5,567 households** (Kaggle version mein common count ~5,560), half-hourly readings, **Nov 2011 se Feb 2014 tak**, kWh mein
- UK Power Networks ne isse **CC-BY licence (open)** ke under release kiya hai
- Kaggle pe "Smart meters in London" naam se freely available
- Bonus fact: isme ~1,100 households ka ek sub-group **Dynamic Time-of-Use tariff** pe tha. Yeh tumhare ToD bill module se ek natural parallel hai.
- Yeh dataset **theft-labelled nahi hai**. Iska use sirf realistic, diverse household load-shapes ke liye hoga (segmentation), theft ke liye nahi.

**Isliye dono dataset alag role play karenge:** SGCC theft-detection algorithm ko **train/validate** karne ke liye (kyunki labels hain), aur London segmentation ko **real diverse shapes pe test** karne ke liye. Dono dashboard pe `FOREIGN` badge ke saath dikhenge.

### Kya use karenge: sab 100% open-source

| Kaam | Tool | Licence |
|---|---|---|
| Anomaly detection | scikit-learn `IsolationForest` | BSD (free) |
| Segmentation/clustering | scikit-learn `KMeans` | BSD (free) |
| Feeder technical-loss estimate | `pandapower` (power-flow simulation) | BSD (free) |
| Data handling | `pandas` | BSD (free) |
| Compute | Isolation Forest/KMeans lightweight hain, CPU pe hi chal jaate hain | Apna machine, no cloud cost |

Isme koi paid API ya proprietary tool nahi hai. Poori pipeline free/open-source stack pe chalegi, jaisa Slide 9 claim karta hai.

### Extra counter-questions jo yahan zaroor aa sakte hain

- **"Yeh page bana hai?"** → Nahi, yeh roadmap pe hai. Humne pehle forecast chain sahi ki, kyunki theft ka energy balance bhi aage chal ke usi data aur pipeline pe khada hoga.
- **"Precision@k kya hota hai?"** → Model top-k sabse suspicious meters ko rank karta hai, aur precision@k batata hai ki un top-k mein se kitne % actually theft nikle (SGCC labels ke against). Jaise top-20 flagged mein se 15 sach mein theft nikle, to precision@20 = 75%. Yeh isliye important hai kyunki DISCOM ke paas limited field inspectors hote hain, aur unhe sabse promising leads deni hoti hain.
- **"Delhi ke liye labelled data nahi hai, to accuracy kaise pata chalegi?"** → SGCC pe train/validate karke methodology (algorithm + features) prove karenge. Phir wahi approach Delhi ke unlabelled feeder data pe lagegi, jahan sirf "suspicious rank" milega, "confirmed theft" nahi, jab tak field inspection na ho. Yeh honestly ek limitation hai, ise chhupana nahi.
- **"Isolation Forest hi kyun, supervised model (Random Forest/XGBoost) kyun nahi?"** → Supervised models ko training ke liye labels chahiye, jo Delhi mein nahi hain. SGCC pe validation ke time supervised baselines se compare kar sakte hain, lekin production mein Delhi data unlabelled hai, isliye unsupervised hi realistic choice hai.
- **"E_tech (expected technical loss) galat estimate hui to poora result galat ho jaayega?"** → Haan, yeh ek genuine dependency hai. Agar pandapower ka feeder model (topology, resistance values) accurate nahi hai, to E_loss bhi skew hoga. Isiliye output ko "suspicious" bolte hain, "confirmed" nahi.
- **"SGCC mein ~25% missing data, isse bias nahi aayega?"** → Imputation karenge, lekin wahi rule rakhenge jo SLDC pe seekha: gap bharte waqt **future data nahi**. Saath mein ek "missingness flag" feature bhi add kar sakte hain, kyunki kabhi-kabhi jaan-boojhkar readings gayab hona (meter tampering) khud ek theft signal hota hai.
- **"Segments banane ka business value kya hai, theft ke alawa?"** → Tariff design aur demand-response targeting ke liye bhi useful hai. DISCOM alag segments ko alag incentive ya ToD offer de sakti hai, jo tumhare ToD bill module ko bhi support karta hai.

---

## LightGBM, N-HiTS, Chronos, P10–P90, SHAP: kya hai, kya karta hai

Yeh 5 cheezein "AI Forecast" engine (Slide 4 ka green box) ka core hain, aur yahi sabse zyada poochha jaayega. Pehle status yaad rakho: **LightGBM, P10–P90 aur SHAP bane hain. N-HiTS aur Chronos abhi bane nahi.**

### 1. LightGBM (bana hai, yahi final model hai)

**Full form:** Light Gradient Boosting Machine (Microsoft, 2017).

**Kya hai:** Ek "gradient boosting" tree-based ML algorithm, yaani bahut saare chhote decision trees ka ensemble jo **sequentially** (ek ke baad ek) banaye jaate hain.

**Kaise kaam karta hai:** Pehla tree ek rough prediction deta hai. Doosra tree pehle tree ki **galti (residual error)** ko target karke banta hai, matlab "pehla tree jahan galat tha, wahan improve karo." Yeh process baar-baar repeat hota hai, aur final prediction sab trees ke outputs ka sum hota hai. Analogy: teachers ki ek team ek student ka answer check kar rahi hai. Pehla teacher rough marking karta hai, doosra sirf pehle ki galtiyan fix karta hai, teesra unki galtiyan, aur end mein sabki marking milake final score aata hai.

**LightGBM specifically kyun alag hai (XGBoost se bhi):** Yeh "leaf-wise" tree growth karta hai: jo leaf sabse zyada error kam karegi, sirf wahi split hoti hai, traditional "level-wise" ki jagah. Isse yeh fast aur accurate hai, lekin overfitting se bachne ke liye depth control karni padti hai. Histogram-based binning ki wajah se bade data pe training bahut fast hoti hai.

**Is project mein role (real numbers):**
- Ek **single multi-horizon** model hai. Horizon (1–96 blocks aage) khud ek feature hai, to 96 alag models nahi banane pade.
- 37 features hain:
  - origin time ka load, weather aur calendar;
  - target block ka calendar (din, ghanta, holiday);
  - **target-aligned lags**, jaise `tlag_1day` = jis block ka forecast hai usi ka kal ka load.
- Tuning Optuna se hui (25 trials, val MAPE pe). Early stopping val pe hui: 3,000 ki limit mein se 436 rounds rakhe.
- Result: test MAPE **3.93%**, naive 5.16%.
- Load forecasting mein exogenous features (weather, calendar) ke saath gradient boosting aksar deep learning ko match ya beat kar deta hai, isiliye primary model yahi hai.

**Puchh sakte hain:**
- **"Bagging aur boosting mein farak?"** → Bagging (Random Forest) mein trees **parallel aur independent** bante hain, alag random data subsets pe, aur final answer unka average/vote hota hai, jo variance kam karta hai. Boosting mein trees **sequential** hote hain, har naya tree pichhle sabki combined galti target karta hai, jo bias kam karta hai.
- **"LightGBM SHAP ke saath kyun perfect fit hai?"** → Kyunki TreeSHAP (SHAP ka fast, exact version) tree-based models pe kaam karta hai. Humne yahi use kiya, aur additivity (base + sum of SHAP = prediction) 1e-11 MW tak hold karti hai.
- **"Overfit to nahi hua? Train 2.29% aur test 3.93%?"** → Gap real hai par harmful nahi. Early stopping healthy hai: val aur test kabhi upar nahi gaye, sirf train girta raha. Gain over naive train pe 58% aur test pe 24% hai, aur held-out error pe koi nuksan nahi dikha. Detail neeche naye questions mein hai.

### 2. N-HiTS (plan mein hai, abhi bana nahi)

**Full form:** Neural Hierarchical Interpolation for Time Series. Paper Challu et al., AAAI 2023 hai, aur yeh Nixtla ki `NeuralForecast` library mein milta hai.

**Kya hai:** Ek deep learning architecture jo **specially long-horizon time-series forecasting** ke liye design hua hai.

**Kaise kaam karta hai:** Model multiple "stacks" mein baanta jaata hai, aur har stack **alag time-resolution** pe kaam karta hai. Ek stack coarse, lambe-term pattern dekhta hai (jaise weekly trend), doosra fine, short-term fluctuations (jaise hourly spikes). Har stack apna signal predict karta hai (interpolation + pooling se), phir sab stacks ke outputs **hierarchically add** hoke final forecast banta hai. Analogy: ek camera ke alag zoom levels. Ek lens poori city ka wide shot leta hai, doosra ek gali ka close-up, aur dono milke poori picture banti hai.

**Kyun socha tha:** Transformer-based models (jaise TFT) se **kam compute mein** similar ya better accuracy deta hai, aur multiple seasonalities (daily + weekly) efficiently pakadta hai.

**Is project mein role:** "Model ladder" ka **deep-learning step**. Ladder rule ke hisaab se yeh tabhi aayega jab LightGBM ke 3.93% ko genuinely beat kare.

**Puchh sakte hain:**
- **"Hierarchical ka exact matlab?"** → Different stacks different time-resolutions pe kaam karte hain: ek "zoom-out," doosra "zoom-in," phir dono combine hote hain.
- **"N-HiTS ko LightGBM se better kab expect karte ho?"** → Jab load pattern mein aisi complex, multi-scale seasonality ho jo lag-features se poori capture na ho. Lekin humare LightGBM mein target-aligned lags pehle se daily shape pakadte hain, isliye N-HiTS ko yeh bar cross karna mushkil hoga. Rule wahi hai: beat karega tabhi use hoga.
- **"Bana kyun nahi?"** → Pehle baseline model ko sahi aur honest banana zyada zaroori tha. Phase 3 mein data leakage aur feature alignment ke bugs fix karne mein hi asli kaam tha. Deep models ek fixed, trustworthy baseline ke against hi compare karne chahiye.

### 3. Chronos (Chronos-Bolt) (plan mein hai, abhi bana nahi)

**Kya hai:** Amazon Science ka banaya hua ek **time-series foundation model**. Jaise GPT text ke liye foundation model hai, waise Chronos time-series numbers ke liye hai.

**Kaise kaam karta hai:** Time series ki continuous numeric values ko discrete "tokens" mein convert (quantize) kiya jaata hai, jaise language model words ko tokens mein todta hai. Phir ek transformer (T5-jaisa encoder-decoder) **bahut saare alag domains** ki time series pe train hota hai (finance, weather, energy, retail, etc.), taaki woh time-series ka generic "pattern/grammar" seekh le.

**Sabse bada point, zero-shot forecasting:** Model ko **Delhi-specific data pe bilkul train kiye bina**, sirf historical values context ki tarah de do, aur woh seedha agla forecast de deta hai. Bilkul waise jaise ek pretrained ChatGPT-jaisa model naye topic pe bhi bina fine-tuning ke reasonable jawab de deta hai.

**Chronos-Bolt:** Original Chronos ka **faster, lightweight variant**, jo kam compute aur latency mein chalta hai. Licence Apache-2.0 hai (open-source, free).

**Is project mein role:** "Model ladder" ka top step, jo test karega ki ek generic pretrained model bina Delhi training ke custom models ke against kitna competitive hai.

**Puchh sakte hain:**
- **"Zero-shot ka exact matlab kya hai?"** → Model ko koi task-specific training nahi di jaati. Sirf naye data ka historical context input hota hai, aur woh seedha forecast deta hai.
- **"Delhi ka heat/IPL/festival jaisa pattern Chronos kaise samjhega agar train hi nahi hua?"** (**Yeh genuine limitation hai, honestly maanna.**) → Zero-shot mode mein Chronos sirf numeric shape (trend, seasonality, past values) pakadta hai. Explicit external features (weather, IPL flag, holiday) aasani se input nahi le sakta jaise LightGBM leta hai. Humne dekha ki Diwali jaise din pe LightGBM bhi, holiday feature hone ke bawajood, 8.65% tak chala gaya, to bina holiday info ke Chronos ke liye yeh aur mushkil hoga. Isiliye yeh sirf comparison baseline hoga, production model nahi.

### 4. P10–P90 band (bana hai)

**Kya hai:** Single number ("kal ka peak itna hoga") ki jagah ek **range/uncertainty band**, yaani probabilistic forecasting ka concept.

**Percentile ka matlab:**
- **P10** = woh value jiske neeche actual aane ka sirf 10% chance hai (yaani 90% chance actual isse **zyada** hoga).
- **P90** = woh value jiske neeche actual aane ka 90% chance hai (yaani sirf 10% chance actual isse zyada hoga).

To P10 se P90 tak ka range woh zone hai jisme model ke hisaab se actual value girni chahiye: ek **80% central interval**.

**Kaise banate hain (do tareeke):**
1. **Quantile regression:** model ko directly specific percentiles predict karne ke liye train karte hain, ek special "pinball/quantile loss" function se.
2. **Conformal prediction:** ek statistical calibration technique jo kisi bhi point-forecast model ke upar "wrap" hoti hai. Held-out data pe error dekhke ek calibrated range bana deti hai.

**Humne kya kiya:** Option 2. MAPIE 1.6 ka `SplitConformalRegressor` (prefit, absolute residual score) use kiya, jo saare val rows (1,657,296) pe calibrate hua aur test (1,672,080 rows, har row ek origin × horizon forecast) pe evaluate hua. Band ki width constant **602 MW** hai. Test coverage **84.4%** hai (un forecasts ka share jinka actual band ke andar aaya), jabki target 80% tha. Misses symmetric hain: 7.9% neeche, 7.8% upar.

**Kyun important:** Operator ko sirf ek number dena risky hai, kyunki pata hi nahi kitna galat ho sakta hai. Range milne se risk-aware planning hoti hai, jaise "worst-case P90 tak capacity plan karo."

**Purana nuance ab fix ho gaya hai:** pehle deck "target ~90%" bolta tha. Ab deck (Slide 4 aur Slide 7), dashboard aur MODEL_RESULTS teeno ek hi baat bolte hain: **target 80%, achieved 84.4%**. Agar kisi purane printout pe "~90%" dikhe to correct kar dena, bahana mat banana.

**Puchh sakte hain:**
- **"Conformal prediction ki guarantee exactly kya hai?"** → Agar calibration aur naya data exchangeable hain (yaani ek jaise distribution se aaye hain), to 80% conformal interval long-run mein ~80% naye actuals ko cover karega. Yeh guarantee model-agnostic hai. Lekin humare case mein val (Mar–Jun heavy) aur test (Jul–Jan) alag seasons hain, to exchangeability strictly hold nahi karti. Isiliye hum empirical number quote karte hain: 84.4%. Aur yeh guarantee **marginal** hai, har month ya har horizon ke liye nahi.

### 5. SHAP (bana hai, 4 dino ke liye)

**Full form:** SHapley Additive exPlanations.

**Kya hai:** Ek **model-explainability technique** jo batati hai ki har ek prediction mein **har feature ka kitna contribution** tha.

**Base concept, Shapley value:** Yeh cooperative game theory se aaya hai. Lloyd Shapley ne 1953 mein ise define kiya. (Unhe 2012 mein Alvin Roth ke saath Economics ka Nobel mila, lekin stable allocations aur market design ke kaam ke liye, Shapley value ke liye nahi. Agar Nobel ka zikr karo to yeh fark dhyan rakhna.) Original idea: kuch log team mein kaam karke ek total reward kamate hain, to fairly kaise decide karein kisne kitna contribute kiya? Formula har player ki "average marginal contribution" nikalta hai. Saare possible orders mein team banake dekhte hain ki us player ko add karne se result kitna badla, aur uska average uski Shapley value hai.

**ML mein kaise apply hota hai:** Features "players" hain aur model ki prediction "reward". SHAP value batata hai ki har feature ne is **specific** prediction ko baseline (average prediction) ke comparison mein kitna **upar ya neeche push kiya**. Value positive (upar push) ya negative (neeche push) ho sakti hai.

**TreeSHAP:** Tree-based models (LightGBM) ke liye ek fast, exact algorithm. Isiliye LightGBM+SHAP combination especially practical hai.

**Is project mein role (real findings, `shap` 0.54, base value 4,314 MW):** 4 din rule se chune gaye the, error dekh ke nahi. Har din pe 96-block day-ahead explanation hai (origin 23:45 pichhli shaam).
- **`tlag_1day`** (same block, kal) har din sabse bada driver hai. Yahi daily shape carry karta hai.
- **Hot day (2025-07-28):** weather features (`night_temp_c`, `temp_roll_mean_24h`) +100–170 MW each add karte hain, jo lag ke saamne chhota hai.
- **Diwali (2025-10-20):** model ne holiday dekha (`target_is_holiday` second-largest driver hai, 12:30 pe −272 MW), lekin effect bahut chhota tha. Isliye day MAPE 8.65% aaya.

Is tarah forecast black-box number nahi rehta, explainable ban jaata hai, jo grid operators ke trust aur audit ke liye important hai.

**Puchh sakte hain:**
- **"SHAP value negative bhi ho sakti hai?"** → Haan. Agar koi feature (jaise "aaj holiday hai") prediction ko baseline se **neeche** push karta hai, to uski SHAP value negative hogi. Diwali pe `target_is_holiday` ki −272 MW isi ka example hai.
- **"SHAP sabhi models pe kaam karta hai?"** → KernelSHAP model-agnostic hai (kisi bhi model pe chalta hai, par slow hai). TreeSHAP sirf tree models ke liye hai (exact aur fast), isiliye LightGBM ke saath use kiya.
- **"SHAP sirf 4 dino ke liye kyun?"** → Yeh representative examples hain jo rule se chune gaye: normal, hot, festival aur Oct/Nov evening. Har din ke liye precompute karna possible hai, par viva/dashboard ke liye 4 representative din kaafi the. Forecast page pe baaki dino ke liye clearly likha aata hai ki SHAP precompute nahi hua.

### Sab kaise ek saath fit hote hain (yeh line zaroor bolna)

"Humne pehle simple baseline rakha: seasonal-naive (same block kal). SARIMAX bhi code mein implemented hai, lekin test pe score nahi hua, isliye hum uska koi number claim nahi karte. Phir ek multi-horizon LightGBM banaya, jo tabhi rakha jab woh naive ko har horizon pe beat kare (test pe 3.93% vs 5.16%). Us final model ke around MAPIE se split-conformal P10–P90 band lagaya (80% target, 84.4% mila). Aur TreeSHAP se batate hain ki forecast **kyun** aaya, sirf 'kya' nahi. N-HiTS aur Chronos isi ladder pe agle step hain, aur unhe 3.93% beat karna hoga."

---

## Hardware components: easy way mein

> **Status:** yeh hardware optional hai aur abhi bana nahi. Neeche yeh samjhaya hai ki banne pe har part kya karega.

Ek dum simple bhasha mein: socho yeh ek **chain** hai, jisme bijli ka current tumhare phone/laptop ke dashboard tak pahunchta hai, aur har part ka apna kaam hai.

### Poori chain ek line mein
**Bijli ka current → napna → padhna → bhejna → store karna → dikhana**

#### 1. PZEM-004T v3 (₹500–800): "Napne wala"
**Kaam:** Yeh asli **meter** hai. Bijli ki line pe laga ke voltage, current, power, energy (kitni units khaayi), power factor aur frequency, sab kuch napta hai. Bilkul ghar ke electricity meter jaisa, bas chhota aur programmable.
**Project mein role:** Yahi asli "sensor" hai jo raw electrical readings deta hai.
**Kaise bhejta hai:** UART/Modbus naam ki ek simple wired communication language se apni readings agle device (ESP32) ko bhejta hai.

#### 2. SCT-013 CT Clamp (₹300–600): "Bina cut kiye current pakadne wala"
**Kaam:** Ek chhota clip jo **live wire ke around lagta hai**, bina wire kaate aur bina usse chhue. Current flow hone pe magnetic field banti hai, aur clip usi field se current "sense" kar leta hai.
**Project mein role:** PZEM ko current napne ke liye yahi CT clamp chahiye. High-current wire ko napne ka yeh safe tareeka hai, bina wire kaate aur bina shock ke risk ke.
**Simple analogy:** Jaise doctor stethoscope se bina cheera lagaye dil ki dhadkan sun leta hai, waise hi CT clamp bina wire kaate current "sun" leta hai.

#### 3. ESP32 (₹350–600): "Dimaag aur messenger"
**Kaam:** Ek chhota WiFi-enabled microcontroller (mini computer). Har minute PZEM se readings **poochhta** hai ("abhi kitna current hai?"), unhe JSON format mein badalta hai, aur WiFi se aage bhej deta hai.
**Project mein role:** Poore hardware setup ka "connector", yaani sensor aur internet ke beech ka pul. Iske bina PZEM ka data wahin atka reh jaata.

#### 4. DHT22 / BME280 (₹250–300): "Mausam batane wala"
**Kaam:** Yeh chhote sensors setup wali jagah ka local **temperature aur humidity** naapte hain.
**Project mein role:** Yeh reading bhi ESP32 ko milti hai, jisse heat index calculate hota hai. Forecasting mein yeh important feature hai, kyunki garmi zyada = AC zyada = load zyada. (Grid level pe hum β = 112.0 MW/°C measure kar chuke hain.)

#### 5. MQTT broker + InfluxDB (software, ESP32 ke aage): "Post office aur record room"
(Yeh hardware nahi, software hai, lekin chain ka agla step samajhne ke liye zaroori hai.)
- **MQTT broker (Mosquitto):** ESP32 apna data yahan "post" karta hai, jaise post office mein letter daalna. Yeh Raspberry Pi pe, laptop pe ya cloud pe kahin bhi ho sakta hai.
- **InfluxDB:** Ek **time-series database** jo poora history save rakhta hai (jaise "10:05 AM pe itna load tha, 10:06 AM pe itna...").

#### 6. Smart Plug, Shelly/Tasmota (₹800–1,500): "Aasan aur safe alternative"
**Kaam:** Ready-made smart plug. Kisi bhi appliance (fridge, AC, etc.) ko isme plug karo, aur yeh khud apna power consumption napta hai.
**Project mein role:** PZEM+CT+ESP32 ke poore jhanjhat ka **shortcut**. Koi wiring nahi karni padti, seedha plug karo. Isliye ise "safest option" bola gaya hai: high-voltage wire ko haath lagane ki zarurat hi nahi.
**Kab use karenge:** Appliance-level data (jaise sirf AC ka) chahiye to yeh; poori circuit/panel ka data chahiye to PZEM+CT wala setup.

#### 7. Raspberry Pi (₹4,000+, optional): "Apna khud ka chhota server"
**Kaam:** Ek chhota computer jispe MQTT broker aur InfluxDB **locally install** kar sakte ho, bina kisi cloud company pe depend kiye.
**Project mein role:** Optional. Pi na ho to yeh software laptop pe ya free cloud tier pe bhi chal sakta hai. Pi ka fayda yeh hai ki ek dedicated, hamesha-on device milta hai jo bijli bhi kam khaata hai.

### Poora flow ek dum simple tareeke se bolne ka script

"230V wire pe CT clamp lagayenge jo bina wire kaate current pakadta hai. Yeh reading PZEM meter naapta hai: voltage, current, power, sab. ESP32 har minute yeh reading PZEM se leke WiFi ke through MQTT pe bhejega. Ek DHT22 sensor alag se temperature aur humidity bhejega. MQTT se data InfluxDB mein history ki tarah store hoga, aur wahan se dashboard pe live dikhega. Yeh optional proof-of-concept hai aur abhi bana nahi. Humara forecasting result poori tarah SLDC data pe hai."

### Chhote easy Q&A jo poochhe ja sakte hain

- **"Yeh sab kyun chahiye, sirf ek smart meter kaafi nahi?"** → Smart plug sirf ek appliance ka data deta hai, jabki PZEM+CT poori circuit/panel ka. Dono alag scale ke liye hain, aur project dono options dikhata hai taaki flexibility rahe.
- **"CT clamp safe hai na?"** → Haan, kyunki yeh sirf wire ke bahar clip hota hai aur andar ka conductor kabhi nahi chhuta. Isliye 230V jaisi khatarnak voltage ke saath bhi yeh method safe hai. Bas AC-side ki actual wiring qualified electrician se karwani chahiye.
- **"Yeh sab kitna paisa lagega total?"** → Core kit (PZEM+CT+ESP32+DHT22) ≈ ₹1,500–4,000. Raspberry Pi bhi lo to ₹4,000+ extra.
- **"Isse Delhi ke poore grid ka data mil jaayega?"** → Nahi, yeh sirf ek chhoti lab/hostel circuit ke liye hai. Iska purpose sirf yeh dikhana hai ki sensor se dashboard tak poora system real hardware pe kaam karta hai. Asli Delhi-scale forecast ke liye SLDC ka bulk data use hota hai.

---

## Forecasting: badhiya se samjho

Chalo "Forecast" wale part ko ek flow ki tarah samjhte hain: raw data se final 96-block forecast tak kaise pahunchte hain. Yeh section ab **jo actually bana hai** wahi bolta hai.

### Forecasting engine ka poora safar, step by step

**Step 1, input ready karna**
Cleaned data (Delhi SLDC load + Open-Meteo weather + calendar) se **features** bante hain. Total 37 features hain:
- *Origin ke time pe jo pata hai:* abhi ka load aur lags, rolling averages, weather (temperature, humidity, dew point, solar irradiance GHI, wind, cloud, heat index, night temperature), aur holiday/weekend/IPL-season flags.
- *Jis block ka forecast hai uska calendar:* din, ghanta, holiday.
- *Target-aligned lags:* `tlag_1day` (us block ka kal ka load), `tlag_1week`, `tlag_4w_avg` (pichhle 4 hafton ka same-block average), aur kuch aur.
- *Horizon:* kitne blocks aage ka forecast hai.

Har lag ka source timestamp origin se pehle ya barabar hai, yaani koi future data nahi. Consumer category feature nahi hai, kyunki forecast poore Delhi ke total load ka hai.

**Step 2, ladder pe models compete karte hain**
Pehle simple baseline bana: seasonal-naive (same block kal). SARIMAX (hourly classical benchmark) code mein implemented hai, lekin uska sirf val pe order search hua, test pe score nahi hua, isliye woh reported ladder mein nahi hai. Phir LightGBM bana. Pehla LightGBM lambe horizons (h = 74–96) pe naive se haar raha tha, aur wahi signal humein bugs tak le gaya (neeche naye questions mein detail hai). Fixes ke baad final LightGBM har horizon pe seasonal-naive ko beat karta hai. N-HiTS aur Chronos ladder ke agle steps hain, abhi bane nahi.

**Step 3, model select aur tune karna**
Selection aur tuning **val pe** hui: Optuna ke 25 trials val MAPE pe chale, aur early stopping bhi val pe hui (436 rounds rakhe). Isliye val bhi untouched nahi hai: woh Optuna objective, early-stopping set aur conformal calibration set teeno hai. Test set sirf final report ke liye hai. Ek honest caveat hai: pehle model ke test-set error breakdown ne feature design ko inform kiya tha, isliye test bhi ab poori tarah untouched holdout nahi hai.

**Step 4, uncertainty band lagana**
Final model ke point-forecast ke around MAPIE (split-conformal) se **P10–P90 band** lagta hai: 80% target, test pe 84.4% coverage, 602 MW width.

**Step 5, explanation lagana**
**TreeSHAP** se batate hain ki kaunsa factor (kal ka same-block load, heat, din, holiday) kitna contribute kar raha hai. Yeh 4 representative dino ke liye precompute kiya gaya hai.

**Step 6, output nikalna**
Final result: **agle din ke 96 blocks (15-15 minute ke), poore Delhi ke total load ka forecast**, jo pichhli shaam 23:45 pe issue hota hai, P10–P90 band aur SHAP reason ke saath. Accuracy: test MAPE **3.93%** (saare test origins × horizons 1–96 pe; dashboard ka 23:45 view isi ka subset hai). Horizon ke saath error badhta hai: h1–12 pe 3.30% aur h85–96 pe 4.38%.

---

### "Next day, 96 blocks, Delhi total load": yeh exactly kyun

- **Next day (agla din):** DISCOMs ko har din apna **day-ahead schedule** SLDC ko submit karna hota hai, isliye "kal ka poora din" hi practically useful horizon hai. Dashboard pe origin 23:45 hai, matlab pichhli shaam ko kal ke 96 blocks.
- **96 blocks:** 24 ghante ÷ 15 minute = 96. Indian grid scheduling isi 15-min granularity mein hoti hai (Slide 2 jaisa).
- **Delhi total load:** forecast poore Delhi ke aggregate load ka hai, kyunki SLDC sirf yahi deta hai. Original design idea per-category forecast ka tha (residential, industrial, commercial, agricultural, EV), kyunki sabka pattern alag hai, lekin SLDC per-category data deta hi nahi. Category curves synthetic hain (5 categories), forecast input nahi hain aur kisi page pe plot nahi hoti.

---

### Forecast kaunse pages ko feed karta hai: design vs build

Slide 4 ka AI Forecast box dikhata hai ki forecast dashboard pages ko feed karta hai. Yeh line design ki hai; neeche har page ka asli status hai.

Design mein yeh forecast P̂(t) poore system ka **central engine** hai. 96 values bante hi yeh formulas mein input jaate hain:
- Peak value → **Overview** *(bana: forecast se seedha)*
- Load factor/PAR → **Load analytics** *(bana: abhi real historical load pe, forecast pe nahi)*
- Heat-sensitivity → **Weather impact** *(bana: real historical fit)*
- Forecast + accuracy → **Forecast page** *(bana)*
- Actual-vs-forecast deviation se DSM penalty → **DSM ₹ calculator** *(bana, lekin abhi what-if inputs leta hai, forecast error nahi)*
- Har block ki price se cost → **IEX price** *(roadmap)*
- Hourly energy se bill → **ToD bill simulator** *(roadmap)*
- Peak load se hot-spot temp/ageing → **Transformer health** *(bana, lekin abhi what-if hot-spot input leta hai)*
- Forecast − solar generation = net load → **Solar & net load** *(roadmap)*
- Current/PF se loss → **Losses & PF** *(roadmap)*
- Actual vs expected energy se theft → **Theft & segments** *(roadmap)*
- Band coverage → **Data & model card** *(bana)*

Isliye Slide 8 mein sirf **Forecast** page green highlight hai: yeh "source of truth" hai, aur baaki pages iske downstream consequences hain.

---

### Forecast dashboard page (04) khud kya dikhata hai (jo bana hai)

1. Test window ke kisi bhi din ke 96 blocks ka chart (forecast vs actual).
2. Har block ke around P10–P90 shaded band, aur neeche "test coverage 84.4% (target 80%)".
3. Model comparison: LightGBM 3.93% vs seasonal-naive 5.16%, aur saath mein note ki test set ab fully untouched holdout nahi hai.
4. SHAP chart: 4 precomputed dino ke liye top-5 contributors (mean SHAP, MW).

---

### Bolne ka ready script (agar seedha "forecasting kaise karte ho" poochhe)

"Hum real SLDC load aur weather se features banate hain: kal ke same block ka load, pichhle hafte ka, heat index, calendar aur holiday. Yeh sab ek multi-horizon LightGBM mein jaata hai jo pichhli shaam 23:45 pe agle din ke 96 blocks forecast karta hai. Model ko val pe tune kiya, aur test pe uska MAPE 3.93% hai, jabki seasonal-naive ka 5.16%. Uske around split-conformal P10–P90 band lagate hain (80% target, 84.4% mila), aur SHAP se batate hain forecast kyun aaya. Yahi forecast Overview pe peak aur alert deta hai, aur design mein baaki pages ko bhi feed karega."

---

### Counter-questions jo yahan aa sakte hain

- **"Har din ke liye alag model select hoga, ya ek fix ho jaayega?"** → Ek fixed model hai: final LightGBM jo val pe tune hua. Har din model badalna noise pe overfit karna hoga. Baselines (naive) comparison ke liye saath rehte hain, taaki accuracy drift track ho sake.
- **"Agar do models same answer dein to?"** → Ladder rule ke hisaab se simpler aur interpretable model ko priority milti hai. Complex model tabhi aata hai jab woh clearly better ho.
- **"Forecast galat nikla to saare pages galat ho jaayenge?"** → Haan, yeh central dependency hai, isiliye forecast accuracy (MAPE) aur band coverage khud dedicated pages (Forecast + Data & model card) pe track hoti hai, taaki koi isse blindly trust na kare. Known weak spots bhi wahan likhe hain: Diwali, h = 1–2 aur summer peak.
- **"Category-wise 5 alag forecasts chalane mein compute cost zyada nahi lagega?"** → Abhi per-category forecast hai hi nahi. Design mein bhi LightGBM jaisa lightweight model CPU pe fast chal jaata hai, to 5 categories × 96 blocks manageable hai. Heavy models (N-HiTS/Chronos) ke liye GPU socha tha.
- **"Kal ka weather forecast kahan se laate ho?"** → Hum weather forecast input use hi nahi karte. Weather features origin ke time tak ka **observed** weather hain (temperature, humidity, heat index, irradiance, night temperature, 24-h rolling mean), isliye real deployment mein bhi koi future weather nahi chahiye. Ek minor caveat documented hai: `night_temp_c` 00:00–05:00 ki origins ke liye kuch ghante aage ka temperature include karta hai. Weather forecast ko input banana future improvement ho sakta hai, khaaskar summer peaks ke liye.

---

## Naye counter-questions: model validation, honesty aur limitations (Phase 3–8 ke kaam se)

Yeh section sabse naya hai. Panel ko jab pata chalega ki tumne apne hi model mein bugs pakde aur ablation kiya, to yahan se deep questions aayenge. Har jawab 2–5 sentence ka hai aur ek main number ke saath. "Follow-up" tabhi bolna jab woh aur detail maangein.

### A. Leakage, ablation aur bugs

**Q1. "Leakage hatane se MAPE improve kaise hua? Leak hatane se to score girna chahiye tha."**
→ Purana imputer gaps bharne ke liye future data use karta tha: two-sided interpolation aur bina distance cap ka same-weekday median. Yeh cleaning step mein ek **real look-ahead** tha, isliye hum "leak tha hi nahi" nahi bolte. Lekin uska main asar optimistic score nahi, **galat training labels** the: Oct/Nov ke late-night targets ~25% inflate ho gaye the. Causal imputer ne yeh corrupted targets hata diye, model ne sahi pattern seekha, aur held-out error gira. Comparison sirf real (non-imputed) test readings pe hua, isliye galat training labels seedha test error badha rahe the.
*Follow-up ("kitna improve hua?"):* cleaning ka Shapley share ~0.23 pp (−0.94 pp ka ~25%) hai; akele (bina lags) 0.33 pp, lags ke saath sirf 0.14 pp. Zyada gain target-aligned lags se aaya (~0.61 pp, ~64%; Q2 dekho), isliye "leak hatane se 4.93% → 4.00% hua" mat bolna.
*Follow-up:* "Normal leak test pe score ko jhootha accha dikhata hai. Yeh wala leak training labels ko kharab kar raha tha, isliye use hatane se score real mein behtar hua."

**Q2. "Tumhari ablation methodology kya hai?"**
→ 2×2(+1) factorial design: data version (old leaky / pass-1 causal / final) × features (32 bina target-aligned lags / 37 lags ke saath). Saare arms mein **same fixed hyperparameters** the (final model wale), aur sab ek hi **common real-row test set** pe score hue (n = 1,279,461). Shares Shapley-style averaging se nikale, kyunki lags aur cleaning overlap karte hain (interaction ~0.18 pp). Main CIs day-level (iid-day) bootstrap hain (183 din, 2,000 draws); daily errors autocorrelated hain, isliye yeh uncertainty ko kam dikhate hain, aur week-block bootstrap ~2x wide aata hai. Arm results, deltas aur iid-day CIs do alag audit runs ne exactly reproduce kiye, jo separate AI review agents the; week-block aur training-noise figures ek statistics audit se hain.
*Follow-up (result):* pass-1 improvement, tuned-to-tuned, 4.96% → 4.02% (−0.94 pp, iid-day CI [−1.20, −0.68]). Is −0.94 pp ka: target-aligned lags ~64% (~0.61 pp; add karne ke order ke hisaab se 54–74%), causal cleaning ~25% (~0.23 pp), hyperparameter re-tuning ~10% (~0.10 pp). "Zyada gain lags se aaya" robust hai, kyunki ~90% week-block bootstrap draws mein lags > cleaning tha. Lekin "64%" ek rough estimate hai, alag-se-measure hone wala effect nahi.

**Q3. "Shapley-style share kyun, simple 'ek hatao, farak dekho' kyun nahi?"**
→ Kyunki dono effects overlap karte hain: cleaning lags ke bina 0.33 pp ka hai, lekin lags ke saath sirf 0.14 pp. Isliye jo pehle add karo usko zyada credit milta hai. Fixed-parameter arms ka gain −0.84 pp hai (old_f32 → pass1_f37), aur uska lags wala share 61% (cleaning ke baad add karne pe) se 83% (pehle add karne pe) tak jaata hai; Shapley dono orders ka average leta hai, ~72%. Tuned-to-tuned −0.94 pp mein ~0.10 pp re-tuning bhi hai, isliye wahi lags ~0.61 pp uska ~64% (range 54–74%) banta hai.
*Follow-up ("61 aur 83 ka average 72 hai, phir 64 kyun?"):* alag denominator. 72% fixed-parameter −0.84 pp ka share hai, 64% tuned-to-tuned −0.94 pp ka. Dono ko mix karke "64% (61–83%)" kabhi mat bolna.

**Q4. "Step 2 (Hampel + profile-fill fix) ka kya asar tha?"**
→ Chhota aur uncertain: ~0.07 pp, aur jab day-to-day correlation aur training noise bhi include karo to CI lagbhag [−0.13, 0.00] aata hai. Ladder pe 4.00% → 3.92%. Hum ispe koi bada claim nahi karte. Fix sahi tha kyunki filter future readings dekh raha tha, lekin uska score pe asar marginal hai.

**Q5. "Lags hata do to kya hota hai?"**
→ Final model se target-aligned lags hatane pe test MAPE **+0.58 pp** badhta hai (3.95% → 4.53%). Day-bootstrap CI [0.31, 0.84] hai, aur week-block CI [0.02, 1.08], jo kaafi wide hai par zero ke upar rehta hai. Effect seasonal hai: Jul–Aug mein ~0.2 pp aur Oct–Dec mein ~0.7–0.9 pp. Matlab lags sabse zyada wahan madad karte hain jahan load ka daily shape tezi se badalta hai.

**Q6. "Target-aligned lag kya hota hai, aur purane lags mein kya galat tha?"**
→ Purane lags origin ke time pe aligned the: "abhi ka load, ek block pehle ka load". Isliye 96 blocks aage ke target ke liye model horizon ko practically ignore kar raha tha. Target-aligned lag us block ko dekhta hai jiska forecast ho raha hai: `tlag_1day` = target se theek 96 blocks (1 din) pehle ka load, `tlag_1week` = 1 hafta pehle ka. Har source timestamp origin se pehle ya barabar hai, to yeh legal hai, aur ab model jaanta hai ki "kal 7 baje ka load" kaisa tha.

**Q7. "`tlag_1day` khud leak to nahi? Woh 66.5% importance le raha hai."**
→ Nahi. Har source timestamp origin se pehle ya barabar hai (max offset 0, h = 96 pe). Target ke saath exact-equality fraction 0 hai. Use permute karne pe test MAPE **3.93% → 23.4%** ho jaata hai, jo dikhata hai ki yeh genuine signal hai, chori ka data nahi. 66.5% gain importance isliye hai kyunki kal ka same-block load din ka shape carry karta hai (lag-1-day ACF 0.9625).

**Q8. "Yeh bugs tumne khud kaise pakde? Kisi aur ne flag kyun nahi kiye?"**
→ Pehla signal diagnostics se aaya: pehla LightGBM h = 74–96 pe seasonal-naive se haar raha tha, aur wahi error breakdown future-looking imputer aur origin-aligned lags tak le gaya. Uske baad AI-assisted code-review passes, test suite pe mutation checks aur ablation ka independent re-run hua, jo do alag AI agent runs the. Yeh reviews AI tools se assisted the, aur yeh hum openly bolte hain.
*Follow-up (agar detail maangein):*
1. *Diagnostics:* ek accha model naive se haarna nahi chahiye. h = 74–96 pe haarna hi pehla red flag tha.
2. *Independent code-review passes:* yeh **AI-assisted review agents** the, aur har finding ko fix se pehle alag AI verifier agents ne dobara check kiya. Inhone future-looking Hampel filter aur profile-fill ka date mismatch pakda.
3. *Mutation checks:* LightGBM feature builder mein 10 jaan-boojh ke daale gaye bugs mein se 9 test suite ne pakde. Jo bacha (split boundary pe NaN labels drop karna), usne ek test gap dikhaya, jiske liye ab dedicated test hai. Cleaning code ke mutations ne bhi gaps dikhaye.
4. *Independent audit:* do alag audit runs (separate AI review agents) ne ablation re-run karke arm results, deltas aur iid-day CIs exactly reproduce kiye. Week-block aur training-noise figures ek statistics audit se hain.

*Note for yourself:* yahan kabhi mat bolna ki review "humne manually line-by-line kiya", ya ki har finding humne khud verify ki, jab tak tumne sach mein khud check na kiya ho. Agar poochhe "AI ne kiya?", to seedha bolna: "Haan, AI-assisted review tha. Har finding ko alag verifier agents ne dobara check kiya, phir fix hua, aur auditors bhi alag AI agent runs the."

**Q9. "Mutation testing kya hota hai?"**
→ Code mein jaan-boojh ke chhoti galti daalte hain (jaise lag ko ek block shift kar dena) aur dekhte hain ki test suite fail hota hai ya nahi. Agar test phir bhi pass ho jaaye, to test suite mein gap hai: woh us bug ko kabhi nahi pakdega. Humare case mein 10 mein se 9 mutations pakde gaye, aur bache hue ek ne `test_labels_come_from_target_columns_and_split_nulls_are_dropped` naam ka naya test dilwaya.

### B. Overfitting aur test set

**Q10. "Overfitting hua hai? Train 2.29% aur test 3.93%."**
→ Gap real hai par harmful nahi. Early stopping healthy hai: 436 rounds pe ruka, val aur test kabhi upar nahi gaye, sirf train girta raha. Naive se gain train pe 58% aur test pe 24% hai. Shayad date-like features (day-of-year, month, weather) trees ko training ke do saal thoda yaad karne dete hain, lekin held-out error pe koi nuksan nahi dikha. Isliye verdict hai: no harmful overfitting.

**Q11. "Val MAPE (4.29%) test (3.93%) se zyada kyun? Ulta hona chahiye tha."**
→ Yeh **mostly** window ki difficulty hai. Val ka do-tihai hissa Mar–Jun garmi hai (val pe May 5.5%, Jun 6.0%), jabki test mein Mar–Jun hai hi nahi. Seasonal-naive mein bhi yahi pattern hai: 5.97% val vs 5.16% test. Lekin LightGBM/naive ratio val pe 0.72 aur test pe 0.76 hai, to ek chhota val-selection advantage bhi ho sakta hai; fresh holdout ke bina use alag nahi kar sakte.

**Q12. "Tumhara test set pure holdout kyun nahi hai?"**
→ Hyperparameters aur early stopping ne test kabhi nahi dekha. Lekin pehle model ke **test-set error breakdown** dekh ke hi humne target-aligned lags design kiye, to feature design test se informed hai. Isliye 3.93% thoda optimistic ho sakta hai, aur yeh caveat MODEL_RESULTS, dashboard aur model card teeno pe likha hai. Sahi fix hai Jan 2026 ke baad ke naye data pe ek fresh holdout. Aage se design decisions val pe (ya train+val ke andar rolling-origin backtest pe) hi lenge.
*Follow-up ("to val untouched hai?"):* Nahi. Val Optuna ka objective tha, early stopping ka set tha aur conformal band ka calibration set bhi. Isliye val ke numbers bhi independent evidence nahi hain.

**Q13. "Test mein garmi kyun nahi hai? 29 Jun 2026 ka 8,748 MW peak test hua?"**
→ Data 12 Jan 2026 pe khatam hota hai, aur split strictly chronological hai: test ke target days 13 Jul 2025 se 12 Jan 2026 hain (183 din jinke test targets hain). `split.py` ka intent tha ki test mein ek poori garmi ho, lekin data January mein khatam hone ki wajah se test mein Mar–Jun pre-monsoon summer aaya hi nahi. 8,748 MW record dataset ke bahar hai, aur sirf Overview alert threshold ki tarah use hota hai. To **summer-peak accuracy untested hai**. Mar–Jun 2025 val mein hai (May 5.5%, Jun 6.0%), lekin val pe hi tuning, early stopping aur calibration hui, isliye woh summer accuracy ka independent evidence nahi; bas itna dikhata hai ki garmi mushkil hai.
*Follow-up:* "Hot day" SHAP example (2025-07-28) late-July monsoon ka din hai, pre-monsoon peak nahi. Hum use summer peak bolke present nahi karte.

**Q14. "Kahin 3.93%, kahin 3.92%, kahin 3.95%. Kaunsa sahi hai?"**
→ Teeno sahi hain, bas alag row sets pe hain. 3.93% poore test set pe headline number hai. 3.92% ladder ke common real-row set pe hai (1,267,749 rows, jahan har data version mein actual real tha aur naive forecast available tha). 3.95% ablation ke row set pe hai (1,279,461 rows, jisme bina naive-forecast wali hard rows bhi hain). Alag row sets ke numbers ko seedha compare nahi karte.

### C. Short horizon, Diwali, coverage

**Q15. "h = 1 pe simple persistence tumhare model ko kyun hara deta hai?"**
→ 15 minute mein load bahut kam badalta hai (lag-1-block ACF 0.998), isliye "agla block = abhi wala block" bolna hi h = 1 pe ~1.4% MAPE de deta hai, jabki model ~3.1% deta hai. Humara single multi-horizon model poore 96 blocks ke liye ek saath optimise hua hai. 23:45 origin pe h = 1–2 forecast din ke 00:00 aur 00:15 blocks hain, yaani yeh dashboard ke schedule ke **andar** hain, isliye yeh real limitation hai. Hum abhi persistence ke saath blend nahi karte; fix hai un blocks pe persistence ya alag short-horizon model lagana, aur yeh documented limitation hai. (Dhyan rakhna: model **seasonal-naive** ko har horizon pe beat karta hai; h = 1–2 pe sirf **persistence** se haarta hai. Dono alag baselines hain.)

**Q16. "Diwali pe 8.65% error kyun? Yeh bahut zyada hai."**
→ Haan, yeh sabse saaf weakness hai. Diwali (2025-10-20) pe actual load 4-week same-block average (5,530 MW) se ~2,000 MW neeche tha. Model ne holiday dekha (`target_is_holiday` second-largest driver, 12:30 pe −272 MW), lekin effect bahut chhota tha, isliye forecast poore din overshoot karta raha: day MAPE 8.65% aur sirf 49.3% blocks band ke andar. Wajah yeh hai ki holiday effect bahut kam training holidays aur ek single indicator se seekha gaya. Fix idea festival-specific features (Diwali window, festival type) hain, lekin abhi yeh sirf diagnosis hai, implement nahi kiya.

**Q17. "P10–P90 80% hona chahiye, tumhara 84.4% kyun? Aur month ke hisaab se kyun badalta hai?"**
→ Band val pe calibrate hua tha, aur val Mar–Jun heavy hai jahan errors bade hote hain. Isliye band is test window ke liye thoda conservative (chauda) nikla aur 84.4% cover hua, jo target 80% se upar hai. Coverage marginal hai, conditional nahi: kyunki band ki width constant 602 MW hai, calm winter mahino mein woh zyada chauda padta hai (Nov 98%, Dec 96%, Jan 91%) aur monsoon mahino mein patla (Jul 77%, Aug 73%, Sep 77%). Horizon ke hisaab se h1–4 pe 90% aur h49–96 pe 82% hai.
*Follow-up:* relative (gamma) score try kiya tha. Usne Jul–Sep ko barabar kiya (85%, 79%, 84%), lekin Oct ko undercover kar diya (73%). Koi bhi conditionally calibrated nahi hai, isliye hum empirical numbers quote karte hain.

### D. Weather, load factor, illustrative pages

**Q18. "Tumhara r² 0.61 hai aur CSE 67% bolta hai. To tumhara model CSE se kharab hai?"**
→ Nahi, dono compare hi nahi hote. Humara r² = 0.61 ek OLS fit hai: **har 15-min block** ka load vs heat index, 96,398 blocks pe, jisse β = 112.0 MW/°C aata hai. CSE ka 67% Delhi ke **daily peak** variation ke baare mein hai: alag metric, alag data, alag period. Isliye 67% hamara result nahi hai, woh sirf problem statement ka motivation hai.
*Follow-up:* "β pehle 111.6 likha tha?" → Woh purana text tha. Locked value 112.0 (112.044) hai, `docs/DATA_QUALITY.md` se.

**Q19. "β = 112 MW/°C ka practical matlab kya hai?"**
→ Heat index 1 °C badhne pe Delhi ka load average ~112 MW badhta hai, yaani +3 °C ≈ +336 MW. Yeh poore period ke saare blocks ka linear average effect hai. Peak hours ya garmi ke mahino mein sensitivity alag ho sakti hai, aur hum ise "har situation ka exact number" bolke present nahi karte.

**Q20. "Load Analytics pe LF 0.503 hai, slide pe 0.646. Kaunsa sahi hai?"**
→ Dono sahi hain, bas alag cheezein hain. 0.646 (530/820 MW) deck ka **worked example** hai jo ek din ka formula samjhata hai. Woh measured din nahi, ILLUSTRATIVE hai. 0.503 **real** hai: poore period (Apr 2023 se Jan 2026) ka average 4,316 MW ÷ peak 8,582 MW, aur PAR 1.99. Poore period ka LF kam hona natural hai, kyunki ~2.8 saal ka average ek single sabse bade peak se divide hota hai, aur seasons ka swing bhi usme aa jaata hai.

**Q21. "DSM aur transformer pages ko 'illustrative' kyun bolte ho? Real kyun nahi banaya?"**
→ DSM mein flat normal rate ₹5,000/MWh aur ek single excess multiplier k = 1.5 assume kiya hai. CERC 2024 ke frequency-linked rate tables abhi encode nahi kiye, aur 41 MW volume limit (BRPL, DERC) bhi assumed input hai. Isliye ₹3.475 lakh/hr formula ka demo hai, real penalty nahi. Transformer page pe hot-spot temperature user ka what-if input hai, kisi real transformer ka measurement nahi (IEC 60076-7, ONAN defaults). Dono pages ke results ILLUSTRATIVE tag ke saath dikhte hain (DSM pe ek "not real penalties" banner bhi hai), kyunki real jaisa dikhne wala fake number dashboard ki sabse badi galti hogi (`docs/PROVENANCE.md`).

**Q22. "DSM page 'har model ki error kitni penalty banaegi' kab dikhayega?"**
→ Abhi DSM page user ke what-if inputs leta hai (default = deck ka 60 MW worked example). Agla step hai ki forecast ki real block-wise deviation aur CERC ke actual rate tables ko jodein, tabhi woh "LightGBM vs naive ki ₹ penalty" honestly dikha payega. Usse pehle koi number dikhana illustrative ko real banake bechna hota.

### E. Data & Model Card, aur dashboard

**Q23. "Data & Model Card page pe kya dikhta hai?"**
→ Yeh ek page ka "nutrition label" hai. Ismein data sources apne-apne badge ke saath hain: REAL (SLDC load, Open-Meteo archive weather, holiday/IPL calendar), SYNTHETIC (5 consumer categories, kisi page pe plot nahi) aur ILLUSTRATIVE (DSM calculator, transformer what-if, LF worked example). Phir splits (val aur test kyun untouched nahi hain), accuracy (3.93% vs naive 5.16%), band coverage (84.4% vs 80% target), ablation summary aur overfitting checks hain. Aakhir mein known limitations khulke likhe hain: test pure holdout nahi, h = 1–2 persistence gap, Diwali 8.65%, test mein summer peak nahi, coverage sirf marginal, h = 96 timing assumption, illustrative calculators, aur 5 unbuilt pages. Matlab user ko pata rehta hai ki kis number pe kitna trust karna hai.

**Q24. "Dashboard live hai? 'Load now' real-time hai?"**
→ Nahi. "Load now" page pe hai hi nahi; Overview sirf day-ahead forecast peak, peak time aur alert dikhata hai. Dashboard backtest ke test window (target days 13 Jul 2025 se 12 Jan 2026) ke din replay karta hai: Overview hamesha aakhri test day (12 Jan 2026) dikhata hai, aur Overview page khud likhta hai ki yeh "latest day of the test-period backtest, not a live forecast for tomorrow" hai. Live SLDC feed se jodna deployment ka step hai, aur uske liye h = 96 block-boundary timestamp assumption ko live feed ke against verify karna padega (MODEL_RESULTS caveat 1).

**Q25. "Login kaise kaam karta hai? Secure hai?"**
→ Do tareeke hain: Google login (OAuth, Auth.js) ya email pe 6-digit OTP. OTP database mein plain nahi, bcrypt hash karke store hota hai. Woh 10 minute mein expire hota hai, ek code pe max 5 attempts allowed hain, aur 15 minute mein ek email pe 3 se zyada OTP nahi bheje ja sakte (rate limit). Bina login ke koi dashboard page nahi khulta, kyunki middleware seedha /login pe bhej deta hai.

**Q26. "Purane deck/guide mein 'MAPE 2.01%' tha. Woh kahan gaya?"**
→ Woh purane deck mein MAPE formula ka **worked example** tha ("6 ghante pe 2.01%" jaisa), bilkul 820 kW ya 530/820 jaise doosre "Ex:" values ki tarah. Woh ILLUSTRATIVE tha aur kisi model ke banne se pehle likha gaya tha, kisi trained model ka result nahi. Real backtest ka number **3.93%** hai: poora test set (183 din), saare origins × horizons 1–96. Isliye hum sirf yahi number quote karte hain.

**Q27. "Agar kal Delhi ka load 8,748 MW cross kare, to tumhara system kya karega?"**
→ Overview engine forecast ke 96 blocks ka max leta hai aur use 8,748 MW (Delhi all-time peak, `api/app/config.py`) se compare karta hai. Upar gaya to page "ALERT" dikhata hai, aur saath mein kitne MW upar hai. Lekin honestly bolna: summer-peak accuracy untested hai, kyunki test mein garmi nahi thi, isliye itne high load pe forecast ki reliability abhi proven nahi hai.

---

## Last-minute checklist (viva se ek din pehle)

- [ ] 30-second pitch bolke practice karo (3.93%, 5.16%, 80%/84.4%).
- [ ] Golden numbers table ek baar padh lo. Khaaskar 112.0 MW/°C, r² 0.61 aur CSE 67% ka fark.
- [ ] Har **[TODO: verify]** wala number (Slide 2 ke external stats, 8,656 MW ka report ref [2], SGCC/London dataset numbers) ya to source se check karo, ya bolna band karo.
- [ ] Apni personal details confirm karo: Work Distribution table (report Section 7) mein tumhara contribution, TPIOS/Salasar, aur H200 server.
- [ ] Sirf repo wala deck (`docs/LPMF_Project_Presentation.pptx`) present karna, koi purana copy nahi. Usme band coverage 80% target / 84.4% test hai; kisi purane printout pe "~90%" dikhe to correct karke bolna.
- [ ] Q1 (leak se MAPE improve), Q2–Q3 (ablation aur dono denominators) aur Q8 (bugs kaise pakde, AI-assisted honestly, auditors bhi AI agent runs) bolke practice karo. Yahi naye examiners ke favourite honge.
- [ ] Har illustrative number ke saath "illustrative" shabd bolna yaad rakho: ₹3.475 lakh/hr, 10.08x, 0.646.
