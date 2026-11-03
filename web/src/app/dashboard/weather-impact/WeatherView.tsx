"use client";

import {
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ApiBoundary } from "@/components/dashboard/ApiBoundary";
import { axisProps, chartColors, gridProps, tooltipProps } from "@/components/dashboard/chartTheme";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { Panel } from "@/components/dashboard/Panel";
import { SourceBadge } from "@/components/SourceBadge";
import { api, type WeatherResponse } from "@/lib/api";
import { ProvenanceKind } from "@/lib/provenance";
import { formatMw } from "@/lib/format";
import { useApi } from "@/lib/useApi";

type Point = { x: number; y: number };

function fittedLine(w: WeatherResponse): [Point, Point] {
  const xs = w.scatter.map((p) => p.heat_index_c);
  const [x0, x1] = [Math.min(...xs), Math.max(...xs)];
  return [
    { x: x0, y: w.intercept_mw + w.beta_mw_per_c * x0 },
    { x: x1, y: w.intercept_mw + w.beta_mw_per_c * x1 },
  ];
}

export function WeatherView() {
  const state = useApi("weather", (signal) => api.weather(signal));

  return (
    <ApiBoundary state={state} loadingLabel="Fitting load against heat index">
      {(w) => (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
            {/* normal-case keeps the Greek letters from uppercasing into look-alike Latin ones. */}
            <KpiCard
              label={
                <>
                  Heat sensitivity <span className="normal-case">β</span>
                </>
              }
              value={w.beta_mw_per_c.toFixed(1)}
              unit="MW/°C"
              hint={`+3 °C heat index ≈ +${Math.round(3 * w.beta_mw_per_c)} MW`}
            />
            <KpiCard
              label={<span className="normal-case">r²</span>}
              value={w.r_squared.toFixed(2)}
              hint="Own OLS fit, all 15-min blocks"
            />
            <KpiCard
              label="Blocks in the fit"
              value={w.n_blocks.toLocaleString("en-IN")}
              hint={`${w.scatter.length.toLocaleString("en-IN")} days plotted`}
            />
          </div>

          <Panel title="Load vs heat index" provenance={w.provenance} source={w.source}>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 8, right: 12, left: 0, bottom: 16 }}>
                  <CartesianGrid {...gridProps} vertical />
                  <XAxis
                    {...axisProps}
                    type="number"
                    dataKey="heat_index_c"
                    name="Heat index"
                    unit=" °C"
                    domain={["dataMin - 1", "dataMax + 1"]}
                    tickFormatter={(v: number) => v.toFixed(0)}
                    label={{
                      value: "Daily mean heat index (°C)",
                      position: "insideBottom",
                      offset: -10,
                      fill: "var(--lpmf-muted)",
                      fontSize: 11,
                    }}
                  />
                  <YAxis
                    {...axisProps}
                    type="number"
                    dataKey="load_mw"
                    name="Load"
                    width={52}
                    domain={["auto", "auto"]}
                    tickFormatter={(v: number) => `${(v / 1000).toFixed(1)}k`}
                  />
                  <Tooltip
                    {...tooltipProps}
                    formatter={(v, name) =>
                      name === "Load" ? [formatMw(Number(v)), name] : [`${v} °C`, name]
                    }
                  />
                  <Scatter
                    data={w.scatter}
                    fill={chartColors.amber}
                    fillOpacity={0.45}
                    isAnimationActive={false}
                  />
                  <ReferenceLine
                    segment={fittedLine(w)}
                    stroke={chartColors.ink}
                    strokeWidth={2}
                    ifOverflow="extendDomain"
                  />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-3 text-xs text-[color:var(--lpmf-muted)]">
              One point per day (daily means); the line is the OLS fit over every 15-min block, load
              = {w.intercept_mw.toFixed(0)} + {w.beta_mw_per_c.toFixed(1)} × heat index.
            </p>
          </Panel>

          <Panel title="Two different “explained by heat” numbers">
            <div className="grid gap-4 text-sm text-[color:var(--foreground)] md:grid-cols-2">
              <div>
                <p className="lpmf-mono text-2xl font-semibold">r² = {w.r_squared.toFixed(2)}</p>
                <p className="mt-1 text-[color:var(--lpmf-muted)]">
                  This project&apos;s own fit: the share of the variance of{" "}
                  <strong>every 15-min block&apos;s load</strong> that heat index explains.
                </p>
                <SourceBadge
                  kind={w.provenance as ProvenanceKind}
                  source="Own OLS fit"
                  className="mt-2"
                />
              </div>
              <div>
                <p className="lpmf-mono text-2xl font-semibold">67%</p>
                <p className="mt-1 text-[color:var(--lpmf-muted)]">
                  CSE (2025): the share of Delhi&apos;s <strong>daily peak variation</strong>{" "}
                  explained by heat index. A different quantity on different data — not comparable
                  with this project&apos;s r².
                </p>
                <SourceBadge
                  kind={ProvenanceKind.REAL}
                  source="CSE, “How Delhi is losing its cool” (2025)"
                  className="mt-2"
                />
              </div>
            </div>
          </Panel>
        </>
      )}
    </ApiBoundary>
  );
}
