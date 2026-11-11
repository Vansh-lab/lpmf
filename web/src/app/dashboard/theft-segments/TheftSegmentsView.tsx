"use client";

import clsx from "clsx";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ApiBoundary } from "@/components/dashboard/ApiBoundary";
import { axisProps, chartColors, gridProps, tooltipProps } from "@/components/dashboard/chartTheme";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { Panel } from "@/components/dashboard/Panel";
import { formatPct } from "@/lib/format";
import { api } from "@/lib/api";
import { useApi } from "@/lib/useApi";

const CLUSTER_COLORS = [chartColors.amber, chartColors.green, chartColors.red, chartColors.muted];

export function TheftSegmentsView() {
  const state = useApi("theft", (signal) => api.theft({}, signal));

  return (
    <ApiBoundary state={state} loadingLabel="Scoring the synthetic fleet" minHeight={320}>
      {(r) => (
        <>
          <SyntheticBanner />

          <Panel title="Isolation Forest: suspicious meters" provenance={r.provenance} source={r.source}>
            <div className="mb-4 grid gap-4 md:grid-cols-3">
              <KpiCard label="Meters in the demo fleet" value={r.n_meters.toString()} />
              <KpiCard
                label="Flagged as theft (ground truth)"
                value={r.n_theft_ground_truth.toString()}
                hint="Injected by the generator — never shown to the model."
              />
              <KpiCard
                size="lg"
                label={`Precision@${r.k}`}
                value={formatPct(r.precision_at_k, 0)}
                hint="Share of the top-k most-anomalous meters that are actually theft meters, on this one synthetic fleet."
              />
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="text-[11px] uppercase tracking-wide text-[color:var(--lpmf-muted)]">
                    <th className="pb-2 pr-4">Rank</th>
                    <th className="pb-2 pr-4">Meter</th>
                    <th className="pb-2 pr-4">Category</th>
                    <th className="pb-2 pr-4">Anomaly score</th>
                    <th className="pb-2">Ground truth</th>
                  </tr>
                </thead>
                <tbody>
                  {r.ranking.slice(0, 10).map((m, i) => (
                    <tr key={m.meter_id} className="border-t border-[color:var(--border-faint)]">
                      <td className="lpmf-mono py-1.5 pr-4 text-[color:var(--lpmf-muted)]">{i + 1}</td>
                      <td className="lpmf-mono py-1.5 pr-4">{m.meter_id}</td>
                      <td className="py-1.5 pr-4 text-[color:var(--lpmf-muted)]">{m.category}</td>
                      <td className="lpmf-mono py-1.5 pr-4">{m.anomaly_score.toFixed(3)}</td>
                      <td className="py-1.5">
                        <span
                          className={clsx(
                            "rounded-full px-2 py-0.5 text-[11px] font-medium",
                            m.is_theft_ground_truth
                              ? "bg-[color:var(--lpmf-red)]/10 text-[color:var(--lpmf-red)]"
                              : "text-[color:var(--lpmf-muted)]",
                          )}
                        >
                          {m.is_theft_ground_truth ? "Theft (synthetic)" : "Normal"}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="mt-3 text-xs text-[color:var(--lpmf-muted)]">
              Top 10 of {r.n_meters} meters, most anomalous first. &ldquo;Ground truth&rdquo; exists
              only because this fleet is synthetic — a real deployment would not have it.
            </p>
          </Panel>

          <Panel
            title="K-means: load-shape segments"
            provenance={r.provenance}
            source="Synthetic smart-meter fleet"
          >
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart margin={{ top: 8, right: 8, left: 0, bottom: 16 }}>
                  <CartesianGrid {...gridProps} />
                  <XAxis
                    {...axisProps}
                    type="number"
                    dataKey="h"
                    domain={[0, 23]}
                    ticks={[0, 4, 8, 12, 16, 20, 23]}
                    allowDuplicatedCategory={false}
                    label={{
                      value: "Hour of day",
                      position: "insideBottom",
                      offset: -8,
                      fill: "var(--lpmf-muted)",
                      fontSize: 11,
                    }}
                  />
                  <YAxis
                    {...axisProps}
                    width={48}
                    tickFormatter={(v: number) => `${v}%`}
                    label={{
                      value: "Share of daily energy",
                      angle: -90,
                      position: "insideLeft",
                      fill: "var(--lpmf-muted)",
                      fontSize: 11,
                    }}
                  />
                  <Tooltip
                    {...tooltipProps}
                    labelFormatter={(h) => `${h}:00`}
                    formatter={(v, name) => [`${Number(v).toFixed(2)}%`, name]}
                  />
                  <Legend wrapperStyle={{ fontSize: 11 }} />
                  {r.clusters.map((c, i) => (
                    <Line
                      key={c.cluster}
                      name={`Cluster ${c.cluster} (${c.n_meters} meters)`}
                      data={c.mean_shape_pct.map((v, h) => ({ h, [`c${c.cluster}`]: v }))}
                      dataKey={`c${c.cluster}`}
                      stroke={CLUSTER_COLORS[i % CLUSTER_COLORS.length]}
                      strokeWidth={2}
                      dot={false}
                      isAnimationActive={false}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-3 text-xs text-[color:var(--lpmf-muted)]">
              Each line is a cluster&apos;s mean normalised 24h shape (K-means on shape, not scale),
              grouping meters by <em>when</em> they use energy.
            </p>
          </Panel>
        </>
      )}
    </ApiBoundary>
  );
}

function SyntheticBanner() {
  return (
    <div
      role="note"
      className="rounded-lg border-2 border-[color:var(--lpmf-amber)] bg-[color:var(--lpmf-amber)]/10 p-4"
    >
      <p className="text-sm font-semibold uppercase tracking-wide text-[color:var(--lpmf-amber-text)]">
        Demo on synthetic meters — not real consumers
      </p>
      <p className="mt-1 text-sm text-[color:var(--foreground)]">
        No public, consumer-level Delhi smart-meter data exists. This fleet is generated: four
        illustrative category shapes, scaled and noised, with a few meters given a theft-like
        energy drop so precision@k has something to measure. The method (Isolation Forest, K-means)
        is real; the meters are not.
      </p>
    </div>
  );
}
