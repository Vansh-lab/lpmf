"use client";

import clsx from "clsx";
import { useState } from "react";
import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ApiBoundary } from "@/components/dashboard/ApiBoundary";
import { axisProps, chartColors, gridProps, tooltipProps } from "@/components/dashboard/chartTheme";
import { Panel } from "@/components/dashboard/Panel";
import { api, type ForecastResponse } from "@/lib/api";
import { formatDate, formatMw, formatPct, hhmm } from "@/lib/format";
import { ProvenanceKind } from "@/lib/provenance";
import { useApi } from "@/lib/useApi";

const DEFAULT_SHAP_LABEL = "normal";
const SHAP_LABELS: Record<string, string> = {
  hot_summer: "Hot day",
  normal: "Normal weekday",
  festival: "Diwali",
  oct_nov_evening: "Oct–Nov evening",
};

export function ForecastView() {
  const datesState = useApi("forecast-dates", (signal) => api.forecastDates(signal));
  const [picked, setPicked] = useState<string | null>(null);
  const shapDates = datesState.data?.shap_dates ?? {};
  const selected = picked ?? shapDates[DEFAULT_SHAP_LABEL] ?? datesState.data?.dates.at(-1) ?? null;

  return (
    <ApiBoundary state={datesState} loadingLabel="Listing the forecast days" minHeight={120}>
      {(d) => (
        <>
          <Panel title="Day">
            <div className="flex flex-wrap items-center gap-2">
              {Object.entries(d.shap_dates).map(([label, day]) => (
                <button
                  key={label}
                  type="button"
                  onClick={() => setPicked(day)}
                  className={clsx(
                    "rounded-full border px-3 py-1 text-xs font-medium transition",
                    day === selected
                      ? "border-[color:var(--lpmf-amber)] bg-[color:var(--lpmf-amber)]/15 text-[color:var(--foreground)]"
                      : "border-[color:var(--border-subtle)] text-[color:var(--lpmf-muted)] hover:bg-[color:var(--border-faint)]",
                  )}
                >
                  {SHAP_LABELS[label] ?? label} · {formatDate(day)}
                </button>
              ))}
              <label className="ml-auto flex items-center gap-2 text-xs text-[color:var(--lpmf-muted)]">
                Any test day
                <select
                  value={selected ?? ""}
                  onChange={(e) => setPicked(e.target.value)}
                  className="lpmf-mono rounded-md border border-[color:var(--border-subtle)] bg-[color:var(--surface-sunken)] px-2 py-1 text-xs text-[color:var(--foreground)]"
                >
                  {d.dates.map((day) => (
                    <option key={day} value={day}>
                      {day}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </Panel>
          {selected && <DayForecast day={selected} />}
        </>
      )}
    </ApiBoundary>
  );
}

function DayForecast({ day }: { day: string }) {
  const state = useApi(`forecast:${day}`, (signal) => api.forecast({ date: day }, signal));

  return (
    <ApiBoundary state={state} loadingLabel={`Loading the forecast for ${formatDate(day)}`}>
      {(f) => (
        <>
          <ForecastChart f={f} />
          <ModelComparison />
          <ShapPanel f={f} />
        </>
      )}
    </ApiBoundary>
  );
}

function ForecastChart({ f }: { f: ForecastResponse }) {
  const data = f.blocks.map((b) => ({
    time: hhmm(b.ts_target),
    band: [b.p10_mw, b.p90_mw] as [number, number],
    predicted: b.predicted_mw,
    actual: b.actual_mw ?? undefined,
  }));

  return (
    <Panel
      title={`96-block forecast · ${formatDate(f.date)}`}
      provenance={f.provenance}
      source={f.source}
    >
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 4 }}>
            <CartesianGrid {...gridProps} />
            <XAxis {...axisProps} dataKey="time" interval={11} minTickGap={8} />
            <YAxis
              {...axisProps}
              width={52}
              domain={["auto", "auto"]}
              tickFormatter={(v: number) => `${(v / 1000).toFixed(1)}k`}
            />
            <Tooltip
              {...tooltipProps}
              formatter={(v, name) =>
                Array.isArray(v)
                  ? [`${formatMw(Number(v[0]))} – ${formatMw(Number(v[1]))}`, name]
                  : [formatMw(Number(v)), name]
              }
            />
            <Area
              dataKey="band"
              name="P10–P90"
              stroke="none"
              fill={chartColors.amber}
              fillOpacity={0.18}
              isAnimationActive={false}
            />
            <Line
              dataKey="predicted"
              name="Forecast"
              stroke={chartColors.amber}
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
            <Line
              dataKey="actual"
              name="Actual"
              stroke={chartColors.ink}
              strokeWidth={1.5}
              strokeDasharray="4 3"
              dot={false}
              connectNulls={false}
              isAnimationActive={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-[color:var(--lpmf-muted)]">
        <LegendSwatch className="h-0.5 bg-[color:var(--lpmf-amber)]" label="Forecast" />
        <LegendSwatch
          className="h-0.5 border-t border-dashed border-[color:var(--foreground)]"
          label="Actual"
        />
        <LegendSwatch className="h-2.5 bg-[color:var(--lpmf-amber)]/25" label="P10–P90 band" />
        <span>
          Issued {formatDate(f.issued_at)} {hhmm(f.issued_at)} IST · {f.band.method} · test coverage{" "}
          {formatPct(f.band.empirical_test_coverage)} (target{" "}
          {formatPct(f.band.confidence_level, 0)})
        </span>
      </div>
    </Panel>
  );
}

function LegendSwatch({ className, label }: { className: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={clsx("inline-block w-5", className)} aria-hidden />
      {label}
    </span>
  );
}

/** Static, from docs/MODEL_RESULTS.md (test split, 13 Jul 2025 – 12 Jan 2026). */
function ModelComparison() {
  return (
    <Panel
      title="Model comparison · test set"
      provenance={ProvenanceKind.REAL}
      source="docs/MODEL_RESULTS.md, test 13 Jul 2025 – 12 Jan 2026"
    >
      <div className="grid gap-3 sm:grid-cols-2">
        <MapeBar label="LightGBM (final model)" mape={3.93} best />
        <MapeBar label="Seasonal naive (same block yesterday)" mape={5.16} />
      </div>
      <p className="mt-3 text-xs text-[color:var(--lpmf-muted)]">
        MAPE over every test block and horizon. The feature design was informed by test-set error
        diagnostics, so the test set is no longer a fully untouched holdout.
      </p>
    </Panel>
  );
}

function MapeBar({ label, mape, best }: { label: string; mape: number; best?: boolean }) {
  return (
    <div>
      <div className="flex items-baseline justify-between text-sm">
        <span className="text-[color:var(--foreground)]">{label}</span>
        <span className="lpmf-mono font-semibold text-[color:var(--foreground)]">
          {mape.toFixed(2)}%
        </span>
      </div>
      <div className="mt-1.5 h-2 rounded-full bg-[color:var(--surface-recessed)]">
        <div
          className={clsx(
            "h-2 rounded-full",
            best ? "bg-[color:var(--lpmf-amber)]" : "bg-[color:var(--lpmf-muted)]/60",
          )}
          style={{ width: `${(mape / 6) * 100}%` }}
        />
      </div>
    </div>
  );
}

function ShapPanel({ f }: { f: ForecastResponse }) {
  if (!f.shap) {
    return (
      <Panel title="Why this forecast (SHAP)">
        <p className="text-sm text-[color:var(--lpmf-muted)]">
          No SHAP explanation was precomputed for {formatDate(f.date)}. Explanations exist for the
          four labelled days above.
        </p>
      </Panel>
    );
  }
  const data = f.shap.top_contributors.map((c) => ({ feature: c.feature, value: c.mean_shap_mw }));

  return (
    <Panel
      title={`Why this forecast · top ${data.length} SHAP contributors`}
      provenance={f.provenance}
      source="TreeSHAP on the final LightGBM, mean over the day's 96 blocks"
    >
      <div className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            layout="vertical"
            margin={{ top: 4, right: 16, left: 8, bottom: 4 }}
          >
            <CartesianGrid {...gridProps} vertical horizontal={false} />
            <XAxis {...axisProps} type="number" tickFormatter={(v: number) => `${v.toFixed(0)}`} />
            <YAxis
              {...axisProps}
              type="category"
              dataKey="feature"
              width={128}
              tick={{ fill: "var(--foreground)", fontSize: 11 }}
            />
            <ReferenceLine x={0} stroke="var(--lpmf-muted)" />
            <Tooltip
              {...tooltipProps}
              cursor={{ fill: "var(--border-faint)" }}
              formatter={(v) => [
                `${Number(v) > 0 ? "+" : ""}${Number(v).toFixed(1)} MW`,
                "Mean SHAP",
              ]}
            />
            <Bar dataKey="value" isAnimationActive={false} radius={2}>
              {data.map((d) => (
                <Cell key={d.feature} fill={d.value >= 0 ? chartColors.amber : chartColors.muted} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <p className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-[color:var(--lpmf-muted)]">
        <LegendSwatch
          className="h-2.5 bg-[color:var(--lpmf-amber)]"
          label="pushes the forecast up"
        />
        <LegendSwatch className="h-2.5 bg-[color:var(--lpmf-muted)]" label="pushes it down" />
        <span>
          Mean SHAP value in MW over the day ({SHAP_LABELS[f.shap.day_label] ?? f.shap.day_label}),
          ranked by mean |SHAP|.
        </span>
      </p>
    </Panel>
  );
}
