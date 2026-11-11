"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  ComposedChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ApiBoundary } from "@/components/dashboard/ApiBoundary";
import { axisProps, chartColors, gridProps, tooltipProps } from "@/components/dashboard/chartTheme";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { Panel } from "@/components/dashboard/Panel";
import { api } from "@/lib/api";
import type { IexPriceResponse } from "@/lib/api";
import { formatDate, formatLakh, formatMw, hhmm } from "@/lib/format";
import { useApi } from "@/lib/useApi";

export function IexPriceView() {
  const state = useApi("iex", (signal) => api.iex({}, signal));

  return (
    <ApiBoundary state={state} loadingLabel="Modelling the price profile" minHeight={320}>
      {(r) => (
        <>
          {r.is_illustrative ? (
            <IllustrativeBanner note={r.manual_download_note ?? ""} />
          ) : (
            <RealDataBanner profile={r.real_price_profile} />
          )}

          <Panel
            title={`${formatDate(r.date)} — ${r.is_illustrative ? "illustrative" : "real historical"} price curve`}
            provenance={r.provenance}
            source={r.source}
          >
            <div className="grid gap-4 md:grid-cols-3">
              <KpiCard
                size="lg"
                label="Day's power purchase cost"
                value={formatLakh(r.total_cost_rupees)}
                hint={`${r.is_illustrative ? "Illustrative" : "Real historical average"} price x day-ahead load, summed over 96 blocks.`}
              />
              <KpiCard
                label="Price range used"
                value={`₹${(r.min_price_per_mwh / 1000).toFixed(2)}–₹${(r.max_price_per_mwh / 1000).toFixed(2)}`}
                unit="/unit"
                hint={r.is_illustrative ? `Peaks at ${r.expensive_hour}:00` : "Hourly min/max of the real historical average"}
              />
              <KpiCard
                label="Expensive blocks"
                value={r.blocks.filter((b) => b.is_expensive).length.toString()}
                unit="/ 96"
                hint="Top quartile of the day's price curve."
              />
            </div>
          </Panel>

          <Panel title="Load and price, cheap midday vs costly evening">
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart
                  data={r.blocks.map((b) => ({ t: b.ts_target, load: b.load_mw, price: b.price_per_mwh }))}
                  margin={{ top: 8, right: 8, left: 0, bottom: 16 }}
                >
                  <CartesianGrid {...gridProps} />
                  <XAxis
                    {...axisProps}
                    dataKey="t"
                    tickFormatter={hhmm}
                    minTickGap={40}
                    label={{
                      value: "Hour of day (IST)",
                      position: "insideBottom",
                      offset: -8,
                      fill: "var(--lpmf-muted)",
                      fontSize: 11,
                    }}
                  />
                  <YAxis {...axisProps} yAxisId="load" width={52} tickFormatter={(v: number) => `${v}`} />
                  <YAxis
                    {...axisProps}
                    yAxisId="price"
                    orientation="right"
                    width={52}
                    tickFormatter={(v: number) => `₹${(v / 1000).toFixed(1)}`}
                  />
                  <Tooltip
                    {...tooltipProps}
                    labelFormatter={(t) => hhmm(String(t))}
                    formatter={(v, name) =>
                      name === "Load"
                        ? [formatMw(Number(v)), name]
                        : [`₹${(Number(v) / 1000).toFixed(2)}/unit`, name]
                    }
                  />
                  <Line
                    yAxisId="load"
                    name="Load"
                    dataKey="load"
                    stroke={chartColors.muted}
                    strokeWidth={1.5}
                    dot={false}
                    isAnimationActive={false}
                  />
                  <Line
                    yAxisId="price"
                    name="Price"
                    dataKey="price"
                    stroke={chartColors.amber}
                    strokeWidth={2}
                    dot={false}
                    isAnimationActive={false}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </Panel>

          <Panel title="Hourly cost (expensive blocks highlighted)">
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={r.blocks.map((b) => ({ t: b.ts_target, cost: b.cost_rupees, expensive: b.is_expensive }))}
                  margin={{ top: 8, right: 8, left: 0, bottom: 16 }}
                >
                  <CartesianGrid {...gridProps} />
                  <XAxis {...axisProps} dataKey="t" tickFormatter={hhmm} minTickGap={40} />
                  <YAxis {...axisProps} width={52} tickFormatter={(v: number) => `₹${v}`} />
                  <Tooltip
                    {...tooltipProps}
                    labelFormatter={(t) => hhmm(String(t))}
                    formatter={(v) => [`₹${Number(v).toFixed(0)}`, "Cost"]}
                  />
                  <Bar dataKey="cost" isAnimationActive={false}>
                    {r.blocks.map((b, i) => (
                      <Cell key={i} fill={b.is_expensive ? chartColors.red : chartColors.amber} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Panel>
        </>
      )}
    </ApiBoundary>
  );
}

function IllustrativeBanner({ note }: { note: string }) {
  return (
    <div
      role="note"
      className="rounded-lg border-2 border-[color:var(--lpmf-amber)] bg-[color:var(--lpmf-amber)]/10 p-4"
    >
      <p className="text-sm font-semibold uppercase tracking-wide text-[color:var(--lpmf-amber-text)]">
        Illustrative price curve — not real IEX data
      </p>
      <p className="mt-1 text-sm text-[color:var(--foreground)]">{note}</p>
    </div>
  );
}

function RealDataBanner({ profile }: { profile: IexPriceResponse["real_price_profile"] }) {
  if (!profile) return null;
  return (
    <div
      role="note"
      className="rounded-lg border-2 border-[color:var(--lpmf-green)] bg-[color:var(--lpmf-green)]/10 p-4"
    >
      <p className="text-sm font-semibold uppercase tracking-wide text-[color:var(--lpmf-green-text)]">
        Real IEX DAM price data ({profile.n_days_averaged} days, {profile.date_range[0].slice(0, 10)} to{" "}
        {profile.date_range[1].slice(0, 10)})
      </p>
      <p className="mt-1 text-sm text-[color:var(--foreground)]">{profile.note}</p>
    </div>
  );
}
