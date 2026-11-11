import clsx from "clsx";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { Panel } from "@/components/dashboard/Panel";
import { SourceBadge } from "@/components/SourceBadge";
import { ProvenanceKind } from "@/lib/provenance";

/*
 * Static on purpose: no API call. Every figure is a static copy of one of
 * these sources, and each block names its source in a SourceBadge:
 * - the repo's results files: docs/MODEL_RESULTS.md, docs/DATA_QUALITY.md,
 *   data/processed/splits.json;
 * - API responses, copied by hand, not fetched: /weather (beta, r^2) and
 *   /analytics (LF, PAR);
 * - the deck's worked examples that the Phase-5 DSM and transformer engines
 *   are tested against, plus the deck's load-factor example (illustrative).
 * If the model is retrained or the data changes, update this page from them.
 * No hooks, so it renders on the server.
 */

export function DataModelCardView() {
  return (
    <>
      <p className="text-sm text-[color:var(--lpmf-muted)]">
        What the dashboard is built on, how well the forecast does, and where it falls short. A
        static summary of the project&apos;s result files, API responses and worked examples, not
        live data: every figure names its source.
      </p>
      <DataSources />
      <ModelCard />
      <Validation />
      <Limitations />
    </>
  );
}

// ---------------------------------------------------------------------------
// 1. Data sources

interface Fact {
  label: string;
  value: string;
  note?: string;
  /** Only where the figure comes from somewhere other than the row's badge. */
  badge?: { kind: ProvenanceKind; source: string };
}

interface DataSource {
  name: string;
  kind: ProvenanceKind;
  source: string;
  what: React.ReactNode;
  facts?: Fact[];
}

const DATA_SOURCES: DataSource[] = [
  {
    name: "Delhi system load",
    kind: ProvenanceKind.REAL,
    source: "Delhi SLDC (Kaggle)",
    what: (
      <>
        5-min Delhi system load published by Delhi SLDC (delhisldc.org), via the Kaggle mirror{" "}
        <code className="lpmf-mono break-all text-xs">
          prash4nt/delhi-sldc-load-data-5-min-resolution
        </code>
        , resampled to 15-min blocks. The forecast target, and the data behind the Overview, Load
        Analytics, Weather Impact and Forecast pages.
      </>
    ),
    facts: [
      { label: "Coverage", value: "1 Apr 2023 – 12 Jan 2026", note: "last block 23:45 IST" },
      {
        label: "5-min rows present",
        value: "285,252 / 293,184",
        note: "2.705% missing before imputation",
      },
      {
        label: "15-min blocks",
        value: "97,728",
        note: "1,330 still missing after imputation (1.361%), left as gaps",
      },
      {
        label: "Dataset maximum",
        value: "8,581.6 MW",
        note: "15-min average, 19 Jun 2024, 15:30 IST",
      },
    ],
  },
  {
    name: "Weather",
    kind: ProvenanceKind.REAL,
    source: "Open-Meteo Archive API",
    what: "Hourly temperature and relative humidity for Delhi, combined into a heat index. Used as forecast features and in the Weather Impact fit.",
    facts: [
      {
        label: "Heat sensitivity (own OLS fit)",
        value: "β = 112.0 MW/°C, r² = 0.61",
        note: "Every 15-min block (96,398). CSE (2025, ‘How Delhi is losing its cool’) reports that heat index explains 67% of Delhi's daily-peak variation: a different metric on different data, not comparable with this r² and not this project's result.",
        badge: { kind: ProvenanceKind.REAL, source: "docs/DATA_QUALITY.md, API /weather" },
      },
    ],
  },
  {
    name: "Calendar flags",
    kind: ProvenanceKind.REAL,
    source: "holidays (IN-DL), ipl_seasons.csv",
    what: "Delhi public holidays from the holidays package, and IPL season flags. The IPL flag covers each tournament's start-to-end window, not individual match days.",
  },
  {
    name: "Consumer-category loads",
    kind: ProvenanceKind.SYNTHETIC,
    source: "lpmf.synthetic.generate",
    what: "Residential, commercial, industrial, agricultural and EV-charging loads from a parametric generator (base + daily + weekly + heat effect + noise + event bumps). Delhi SLDC publishes no per-category feed, so these stand in for it. Not a forecast input and not plotted on any dashboard page.",
  },
  {
    name: "DSM ₹ Calculator",
    kind: ProvenanceKind.ILLUSTRATIVE,
    source: "Worked example",
    what: "One flat normal rate and one excess multiplier; the CERC frequency-linked rate tables are not encoded. Shows how the charge scales, not what a DISCOM would pay.",
    facts: [
      {
        label: "Deck example",
        value: "₹3.475 lakh/hr",
        note: "60 MW deviation for 1 h against the 41 MW BRPL limit, at ₹5,000/MWh and k = 1.5. Not a real penalty.",
      },
    ],
  },
  {
    name: "Transformer Health",
    kind: ProvenanceKind.ILLUSTRATIVE,
    source: "IEC 60076-7 what-if",
    what: "IEC 60076-7 relative ageing for a hot-spot temperature you choose. A what-if calculator, not readings from a real transformer.",
    facts: [
      {
        label: "Deck example",
        value: "118 °C → V = 10.08",
        note: "1 h at 118 °C uses 10.08 h of insulation life",
      },
    ],
  },
  {
    name: "Load-factor worked example",
    kind: ProvenanceKind.ILLUSTRATIVE,
    source: "Project deck worked example",
    what: "The deck's single-day load-factor example. A worked example, not a measured day.",
    facts: [
      { label: "Example day", value: "530 / 820 MW", note: "LF 0.646, PAR 1.55" },
      {
        label: "Measured, whole period",
        value: "LF 0.503, PAR 1.99",
        note: "Load Analytics page, 1 Apr 2023 – 12 Jan 2026",
        badge: { kind: ProvenanceKind.REAL, source: "API /analytics" },
      },
    ],
  },
];

function DataSources() {
  // No panel-level badge: the rows mix real, synthetic and illustrative sources.
  return (
    <Panel title="Data sources">
      <p className="mb-4 text-xs text-[color:var(--lpmf-muted)]">
        The kinds are mixed, so each source carries its own badge: real data feeds the model and
        pages 01–04, synthetic data stands in where no real feed exists, and illustrative numbers
        are worked examples. No page is a live SLDC feed: Overview shows the last test day (12 Jan
        2026) and Forecast replays days from the test-window backtest.
      </p>
      <ul className="space-y-3">
        {DATA_SOURCES.map((s) => (
          <li
            key={s.name}
            className="rounded-md border border-[color:var(--border-faint)] bg-[color:var(--surface-sunken)] p-3 sm:p-4"
            style={{ boxShadow: "var(--lpmf-shadow-recessed)" }}
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="text-sm font-semibold text-[color:var(--foreground)]">{s.name}</h3>
              <SourceBadge kind={s.kind} source={s.source} />
            </div>
            <p className="mt-1.5 text-sm text-[color:var(--lpmf-muted)]">{s.what}</p>
            {s.facts && (
              <dl className="mt-3 grid gap-x-6 gap-y-3 sm:grid-cols-2">
                {s.facts.map((f) => (
                  <FactItem key={f.label} fact={f} />
                ))}
              </dl>
            )}
          </li>
        ))}
      </ul>
    </Panel>
  );
}

function FactItem({ fact }: { fact: Fact }) {
  return (
    <div className="min-w-0">
      <dt className="text-[11px] font-medium uppercase tracking-wide text-[color:var(--lpmf-muted)]">
        {fact.label}
      </dt>
      <dd className="mt-0.5">
        <span className="lpmf-mono text-sm font-semibold text-[color:var(--foreground)]">
          {fact.value}
        </span>
        {fact.note && (
          <span className="block text-xs text-[color:var(--lpmf-muted)]">{fact.note}</span>
        )}
        {fact.badge && (
          <span className="mt-1.5 block">
            <SourceBadge kind={fact.badge.kind} source={fact.badge.source} />
          </span>
        )}
      </dd>
    </div>
  );
}

// ---------------------------------------------------------------------------
// 2. Model card

/** A KpiCard hint with the figure's own SourceBadge under it. */
function SourcedHint({ children, source }: { children: React.ReactNode; source: string }) {
  return (
    <>
      <span>{children}</span>
      <span className="mt-1.5 block">
        <SourceBadge kind={ProvenanceKind.REAL} source={source} />
      </span>
    </>
  );
}

const MODEL_DETAILS: { label: string; value: string }[] = [
  {
    label: "Model",
    value: "One multi-horizon LightGBM: horizon is a feature, 96 blocks (24 h) ahead, 37 features.",
  },
  {
    label: "Tuning",
    value:
      "Optuna, 25 trials on validation MAPE; early stopping on validation (436 rounds kept of a 3,000 limit).",
  },
  {
    label: "Dashboard framing",
    value:
      "The dashboard shows the day-ahead forecast issued at 23:45 IST the evening before. Test MAPE, coverage, split and ablation scores average every 15-min origin; the SHAP example days (limitation 03) are scored on the 23:45 forecast.",
  },
  {
    label: "Bands",
    value:
      "Split-conformal (MAPIE 1.6, absolute score), calibrated on all validation rows. Constant width.",
  },
  {
    label: "Error by horizon (test)",
    value:
      "3.21% at h1–4, 3.48% at h5–24, 3.84% at h25–48, 4.22% at h49–96 (naive ~5.16% throughout).",
  },
  {
    label: "Largest feature",
    value: "tlag_1day (same block yesterday): 66.5% of gain importance.",
  },
];

const SPLITS: {
  name: string;
  dates: string;
  note: string;
  mape: string;
  accuracy: string;
  naive: string;
}[] = [
  {
    name: "Train",
    dates: "1 Apr 2023 – 12 Jan 2025",
    note: "Model fitting.",
    mape: "2.29%",
    accuracy: "97.71%",
    naive: "5.44%",
  },
  {
    name: "Validation",
    dates: "13 Jan 2025 – 12 Jul 2025",
    note: "Tuning objective, early stopping and band calibration, so not untouched. Contains the Mar–Jun 2025 summer (May 5.5%, Jun 6.0% MAPE), which is therefore not independent evidence of summer accuracy.",
    mape: "4.29%",
    accuracy: "95.71%",
    naive: "5.97%",
  },
  {
    name: "Test",
    dates: "13 Jul 2025 – 12 Jan 2026",
    note: "Target days; first origin 12 Jul 2025, 23:45. 184 calendar days, 183 with data (8 Jan 2026 has no test targets). Never used for tuning or early stopping, but it informed the feature design (limitation 01). Contains no Mar–Jun summer.",
    mape: "3.93%",
    accuracy: "96.07%",
    naive: "5.16%",
  },
];

function ModelCard() {
  return (
    <Panel
      title="Model card · multi-horizon LightGBM"
      provenance={ProvenanceKind.REAL}
      source="docs/MODEL_RESULTS.md"
    >
      <div className="grid gap-4 sm:grid-cols-2">
        <KpiCard
          label="Test accuracy"
          value="96.07"
          unit="%"
          hint={
            <SourcedHint source="docs/MODEL_RESULTS.md · test">
              100 − MAPE. Train 97.71%, validation 95.71% (see the split table below).
            </SourcedHint>
          }
        />
        <KpiCard
          label="Test MAPE"
          value="3.93"
          unit="%"
          hint={
            <SourcedHint source="docs/MODEL_RESULTS.md · test">
              Final model, averaged over every 15-min test origin and horizons 1–96 (n = 1,672,080
              forecasts), not only the 23:45 forecast.
            </SourcedHint>
          }
        />
        <KpiCard
          label="Seasonal-naive MAPE"
          value="5.16"
          unit="%"
          hint={
            <SourcedHint source="docs/MODEL_RESULTS.md · test">
              Same block yesterday. The model&apos;s error is 24% lower.
            </SourcedHint>
          }
        />
        <KpiCard
          label="Band coverage"
          value="84.4"
          unit="%"
          hint={
            <SourcedHint source="docs/MODEL_RESULTS.md · conformal">
              Target 80%: P10–P90 is an 80% interval. Share of the same 1,672,080 test forecasts
              (origin × horizon) inside the band. Over target means the band is conservative on this
              test window.
            </SourcedHint>
          }
        />
        <KpiCard
          label="Mean band width"
          value="602"
          unit="MW"
          hint={
            <SourcedHint source="docs/MODEL_RESULTS.md · conformal">
              P90 minus P10, the same for every forecast.
            </SourcedHint>
          }
        />
      </div>

      <dl className="mt-5 grid gap-x-6 gap-y-3 sm:grid-cols-2">
        {MODEL_DETAILS.map((d) => (
          <div key={d.label} className="min-w-0">
            <dt className="text-[11px] font-medium uppercase tracking-wide text-[color:var(--lpmf-muted)]">
              {d.label}
            </dt>
            <dd className="mt-0.5 text-sm text-[color:var(--foreground)]">{d.value}</dd>
          </div>
        ))}
      </dl>

      <div className="mt-5 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-[color:var(--foreground)]">
          Chronological split, never shuffled
        </h3>
        {/* Dates only; the per-split MAPEs carry the panel's MODEL_RESULTS badge. */}
        <SourceBadge kind={ProvenanceKind.REAL} source="data/processed/splits.json" />
      </div>
      <div className="mt-3 grid gap-3 md:grid-cols-3">
        {SPLITS.map((s) => (
          <div
            key={s.name}
            className="rounded-md border border-[color:var(--border-faint)] bg-[color:var(--surface-sunken)] p-3"
            style={{ boxShadow: "var(--lpmf-shadow-recessed)" }}
          >
            <p className="text-xs font-medium uppercase tracking-wide text-[color:var(--lpmf-muted)]">
              {s.name}
            </p>
            <p className="lpmf-mono mt-1 text-sm font-semibold text-[color:var(--foreground)]">
              {s.dates}
            </p>
            <p className="mt-1 text-xs text-[color:var(--lpmf-muted)]">{s.note}</p>
            <p className="mt-2 text-xs text-[color:var(--foreground)]">
              LightGBM <span className="lpmf-mono font-semibold">{s.mape}</span>
              <span className="text-[color:var(--lpmf-muted)]"> MAPE · </span>
              <span className="lpmf-mono font-semibold">{s.accuracy}</span>
              <span className="text-[color:var(--lpmf-muted)]"> acc. · naive </span>
              <span className="lpmf-mono">{s.naive}</span>
            </p>
          </div>
        ))}
      </div>
    </Panel>
  );
}

// ---------------------------------------------------------------------------
// 3. Validation

const ATTRIBUTION: { label: string; share: number; pp: string; note?: string; lead?: boolean }[] = [
  {
    label: "Target-aligned lags",
    share: 64,
    pp: "~0.61 pp",
    note: "54–74% of the −0.94 pp, depending on the order the two fixes are added",
    lead: true,
  },
  { label: "Causal cleaning (imputer)", share: 25, pp: "~0.23 pp" },
  { label: "Hyperparameter re-tuning", share: 10, pp: "~0.10 pp" },
];

const OVERFITTING_CHECKS: { title: string; body: string }[] = [
  {
    title: "The train–test gap is real but benign.",
    body: "Gain over seasonal-naive is 58% on train and 24% on test, and held-out error is not hurt by it.",
  },
  {
    title: "Early stopping is healthy.",
    body: "Validation and test error never rise; only training error keeps falling.",
  },
  {
    title: "Validation (4.29%) above test (3.93%) is mostly window difficulty.",
    body: "Two-thirds of validation is Mar–Jun and test has none; the naive baseline shows the same gap (5.97% vs 5.16%). A small val-selection advantage can't be ruled out without a fresh holdout.",
  },
  {
    title: "tlag_1day is not a leak.",
    body: "Every source timestamp is at or before the forecast origin; permuting it raises test MAPE from 3.93% to 23.4%.",
  },
];

function Validation() {
  return (
    <Panel
      title="Validation · ablation and overfitting check"
      provenance={ProvenanceKind.REAL}
      source="docs/MODEL_RESULTS.md · Ablation, Overfitting check"
    >
      <h3 className="text-sm font-semibold text-[color:var(--foreground)]">
        Ablation: where the gain came from
      </h3>
      <p className="mt-1.5 text-sm text-[color:var(--lpmf-muted)]">
        The first round of fixes (a causal imputer, target-aligned lag features, re-tuning) took
        test MAPE from <span className="lpmf-mono text-[color:var(--foreground)]">4.96%</span> to{" "}
        <span className="lpmf-mono text-[color:var(--foreground)]">4.02%</span>, tuned model to
        tuned model (−0.94 pp; 95% CI [−1.20, −0.68] from an iid-day bootstrap, which understates
        the uncertainty: a week-block bootstrap is about twice as wide). A 2×2(+1) factorial
        ablation (old vs causal cleaning, with vs without the lags, hyperparameters fixed at the
        final model&apos;s, every arm scored on the same 1,279,461 test rows) splits that gain:
      </p>

      <div className="mt-4 space-y-3">
        {ATTRIBUTION.map((a) => (
          <ShareBar key={a.label} {...a} />
        ))}
      </div>
      <p className="mt-3 text-xs text-[color:var(--lpmf-muted)]">
        Shares of the tuned-to-tuned −0.94 pp. On the fixed-parameter −0.84 pp alone (no re-tuning),
        the lags&apos; share is 61% if added after the cleaning and 83% if added first (Shapley
        average ~72%). The lags and the cleaning overlap (interaction ~0.18 pp), so the split is a
        rough estimate, not separable effects. &ldquo;Most of the gain came from the lags&rdquo; is
        robust: the lags beat the cleaning in ~90% of week-block bootstrap draws.
      </p>

      <ul className="mt-4 space-y-2 text-sm text-[color:var(--foreground)]">
        <li>
          <span className="font-medium">Removing the lags from the final model costs 0.58 pp</span>{" "}
          <span className="text-[color:var(--lpmf-muted)]">
            (3.95% → 4.53%; 95% CI [0.31, 0.84] iid-day, [0.02, 1.08] week-block). Ablation MAPEs
            use the 1,279,461-row set, so the final model reads 3.95% there rather than 3.93%;
            compare figures within one row set only.
          </span>
        </li>
        <li>
          <span className="font-medium">
            The second fix (causal Hampel filter, profile-fill date fix) is worth ~0.07 pp
          </span>{" "}
          <span className="text-[color:var(--lpmf-muted)]">
            — small and uncertain (95% CI about [−0.13, 0.00] once day-to-day correlation and
            training noise are included).
          </span>
        </li>
        <li>
          <span className="font-medium">
            Removing the leak improved MAPE rather than hurting it.
          </span>{" "}
          <span className="text-[color:var(--lpmf-muted)]">
            The old imputer used future data (two-sided interpolation, an uncapped same-weekday
            median). That was a real look-ahead, but its main effect was wrong training labels: it
            inflated Oct/Nov late-night targets by ~25%. Fixing it removed corrupted targets, so
            held-out error fell.
          </span>
        </li>
        <li>
          <span className="font-medium">Independently reproduced (AI-assisted).</span>{" "}
          <span className="text-[color:var(--lpmf-muted)]">
            Two independent audit runs by separate AI review agents re-ran the ablation and
            reproduced the arm results, deltas and iid-day confidence intervals exactly; the
            week-block and training-noise figures come from one statistics audit only and were not
            independently reproduced.
          </span>
        </li>
      </ul>

      <div
        className="mt-5 rounded-md border border-[color:var(--border-faint)] bg-[color:var(--surface-sunken)] p-3 sm:p-4"
        style={{ boxShadow: "var(--lpmf-shadow-recessed)" }}
      >
        <h3 className="text-sm font-semibold text-[color:var(--foreground)]">
          Overfitting check · verdict: no harmful overfitting
        </h3>
        <ul className="mt-2 space-y-2 text-sm">
          {OVERFITTING_CHECKS.map((c) => (
            <li key={c.title}>
              <span className="font-medium text-[color:var(--foreground)]">{c.title}</span>{" "}
              <span className="text-[color:var(--lpmf-muted)]">{c.body}</span>
            </li>
          ))}
        </ul>
      </div>
    </Panel>
  );
}

function ShareBar({
  label,
  share,
  pp,
  note,
  lead,
}: {
  label: string;
  share: number;
  pp: string;
  note?: string;
  lead?: boolean;
}) {
  return (
    <div>
      <div className="flex flex-wrap items-baseline justify-between gap-x-3 text-sm">
        <span className="text-[color:var(--foreground)]">{label}</span>
        <span className="lpmf-mono font-semibold text-[color:var(--foreground)]">
          ~{share}% <span className="font-normal text-[color:var(--lpmf-muted)]">· {pp}</span>
        </span>
      </div>
      <div className="mt-1.5 h-2 rounded-full bg-[color:var(--surface-recessed)]" aria-hidden>
        <div
          className={clsx(
            "h-2 rounded-full",
            lead ? "bg-[color:var(--lpmf-amber)]" : "bg-[color:var(--lpmf-muted)]/60",
          )}
          style={{ width: `${share}%` }}
        />
      </div>
      {note && <p className="mt-1 text-xs text-[color:var(--lpmf-muted)]">{note}</p>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// 4. Known limitations

const LIMITATIONS: { title: string; body: string }[] = [
  {
    title: "The test set is no longer a fully untouched holdout.",
    body: "The target-aligned lag features were designed after reading the first model's test-set error breakdown. Hyperparameters and early stopping never saw test, but 3.93% may be slightly optimistic.",
  },
  {
    title: "Persistence beats the model at the shortest horizons.",
    body: "At h = 1–2, simply repeating the latest block is more accurate: at h = 1 it scores 1.44% MAPE against the model's 3.18%. With the 23:45 origin these are the 00:00 and 00:15 blocks of the forecast day, so they are inside the dashboard's schedule. Using persistence (or a short-horizon model) there would fix it; not done.",
  },
  {
    title: "Diwali was the weakest of the four SHAP example days.",
    body: "The four days were picked by rule, not by error. On Diwali (20 Oct 2025) the 23:45 forecast's day MAPE was 8.65%, and only about half of the forecasts for that day fell inside the P10–P90 band (49% of all origin × horizon forecasts targeting it). SHAP shows the model does see the holiday (target_is_holiday is the second-largest driver, −272 MW at 12:30), but far too weakly: actual load was ~2,000 MW below the 4-week same-block average and the forecast overshot all day. The holiday effect is learned from very few training holidays and a single indicator, so other holidays are likely weak too, though only this one was examined. Not fixed.",
  },
  {
    title: "No summer peak in the test window.",
    body: "The dataset ends on 12 Jan 2026, so it holds neither the 29 Jun 2026 all-time peak nor a Mar–Jun pre-monsoon summer in the test window. Every Mar–Jun summer in the data falls in train or validation, and validation was used for tuning, early stopping and band calibration, so its May–Jun MAPE (5.5%, 6.0%) is not independent evidence. Summer-peak accuracy is untested.",
  },
  {
    title: "Band coverage is marginal only.",
    body: "84.4% over the whole test set, but 73% in August and 98% in November, and 90% at h1–4 falling to 82% at h49–96: the constant-width band is too narrow in Jul–Sep and too wide in calm winter months.",
  },
  {
    title: "One timing assumption to verify, and one known minor look-ahead.",
    body: "At h = 96, tlag_1day is the load at the origin timestamp itself, which is valid only if that block is complete when the forecast is issued (true if timestamps mark block end); this needs checking against the live data feed (no bug found). Separately, night_temp_c is the whole-night (00:00–05:00) mean, so for origins in that window it includes up to a few hours of later temperature: a known, minor look-ahead, already flagged in the feature code.",
  },
  {
    title: "The DSM and transformer pages are illustrative calculators.",
    body: "Their outputs are not regulatory figures or measurements.",
  },
  {
    title: "Five dashboard items are not built.",
    body: "07 IEX price, 08 ToD bill, 09 solar & net load, 10 losses & PF and 11 theft & segments are still on the Phase 2 roadmap.",
  },
];

function Limitations() {
  return (
    <Panel
      title="Known limitations"
      provenance={ProvenanceKind.REAL}
      source="docs/MODEL_RESULTS.md, docs/DATA_QUALITY.md"
    >
      <ol className="space-y-3">
        {LIMITATIONS.map((l, i) => (
          <li key={l.title} className="flex gap-3">
            <span className="lpmf-mono w-5 shrink-0 pt-0.5 text-xs text-[color:var(--lpmf-amber-text)]">
              {String(i + 1).padStart(2, "0")}
            </span>
            <p className="min-w-0 text-sm">
              <span className="font-medium text-[color:var(--foreground)]">{l.title}</span>{" "}
              <span className="text-[color:var(--lpmf-muted)]">{l.body}</span>
            </p>
          </li>
        ))}
      </ol>
    </Panel>
  );
}
