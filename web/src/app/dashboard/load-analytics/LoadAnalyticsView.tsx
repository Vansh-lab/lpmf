"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
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
import { formatDate, formatMw } from "@/lib/format";
import { useApi } from "@/lib/useApi";

export function LoadAnalyticsView() {
  const state = useApi("analytics", (signal) => api.analytics({}, signal));

  return (
    <ApiBoundary state={state} loadingLabel="Sorting the load-duration curve">
      {(a) => (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <KpiCard label="Load factor" value={a.load_factor.toFixed(3)} />
            <KpiCard label="PAR" value={a.par.toFixed(2)} />
            <KpiCard
              label="Average load"
              value={formatMw(a.p_avg_mw).replace(" MW", "")}
              unit="MW"
            />
            <KpiCard label="Peak load" value={formatMw(a.p_max_mw).replace(" MW", "")} unit="MW" />
          </div>

          <Panel title="Load-duration curve" provenance={a.provenance} source={a.source}>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart
                  data={a.load_duration_curve}
                  margin={{ top: 8, right: 8, left: 0, bottom: 4 }}
                >
                  <defs>
                    <linearGradient id="ldcFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={chartColors.amber} stopOpacity={0.35} />
                      <stop offset="100%" stopColor={chartColors.amber} stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid {...gridProps} />
                  <XAxis
                    {...axisProps}
                    dataKey="rank_pct"
                    type="number"
                    domain={[0, 100]}
                    ticks={[0, 25, 50, 75, 100]}
                    tickFormatter={(v: number) => `${v}%`}
                  />
                  <YAxis
                    {...axisProps}
                    width={52}
                    tickFormatter={(v: number) => `${(v / 1000).toFixed(1)}k`}
                  />
                  <Tooltip
                    {...tooltipProps}
                    labelFormatter={(v) => `At or above for ${Number(v).toFixed(0)}% of the time`}
                    formatter={(v) => [formatMw(Number(v)), "Load"]}
                  />
                  <Area
                    type="monotone"
                    dataKey="load_mw"
                    stroke={chartColors.amber}
                    strokeWidth={2}
                    fill="url(#ldcFill)"
                    isAnimationActive={false}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-3 text-xs text-[color:var(--lpmf-muted)]">
              Every 15-min block from {formatDate(a.start)} to {formatDate(a.end)} (
              {a.n_blocks.toLocaleString("en-IN")} blocks), sorted from highest to lowest load. LF
              and PAR here are for that whole period, not one day.
            </p>
          </Panel>
        </>
      )}
    </ApiBoundary>
  );
}
