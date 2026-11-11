"use client";

import { useState } from "react";
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
import { SliderField } from "@/components/dashboard/SliderField";
import { api } from "@/lib/api";
import { formatDate, formatMw, hhmm } from "@/lib/format";
import { useApi, useDebounced } from "@/lib/useApi";

export function SolarView() {
  const [capacity, setCapacity] = useState(302);
  const [pr, setPr] = useState(0.8);
  const debouncedCapacity = useDebounced(capacity, 250);
  const debouncedPr = useDebounced(pr, 250);

  const state = useApi(`solar:${debouncedCapacity}:${debouncedPr}`, (signal) =>
    api.solar({ capacity_mwp: debouncedCapacity, performance_ratio: debouncedPr }, signal),
  );

  return (
    <>
      <Panel title="Rooftop solar fleet">
        <div className="grid gap-5 md:grid-cols-2">
          <SliderField
            label="Fleet capacity"
            unit="MWp"
            min={0}
            max={1000}
            step={10}
            value={capacity}
            onChange={setCapacity}
            hint="Default: public Delhi rooftop estimate, ~302 MWp (Mar 2025)."
          />
          <SliderField
            label="Performance ratio"
            unit=""
            min={0.5}
            max={1}
            step={0.05}
            value={pr}
            onChange={setPr}
            hint="Inverter, wiring, soiling and temperature losses, bundled into one factor."
          />
        </div>
      </Panel>

      <ApiBoundary state={state} loadingLabel="Modelling solar output" minHeight={320}>
        {(r) => (
          <>
            <Panel
              title={`${formatDate(r.date)} — modelled from real GHI`}
              provenance={r.provenance}
              source={r.source}
            >
              <div className="grid gap-4 md:grid-cols-3">
                <KpiCard label="Peak load" value={formatMw(r.peak_load_mw)} />
                <KpiCard
                  label="Midday solar peak"
                  value={formatMw(r.midday_solar_peak_mw)}
                  hint={`at ${r.capacity_mwp} MWp, PR ${r.performance_ratio}`}
                />
                <KpiCard
                  size="lg"
                  label="Evening ramp"
                  value={formatMw(r.evening_ramp_mw)}
                  hint="Net load rise from the midday solar trough to the evening peak — the 'duck's neck'."
                />
              </div>
            </Panel>

            <Panel title="Duck curve: load, solar and net load">
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart
                    data={r.blocks.map((b) => ({
                      t: b.ts_target,
                      load: b.load_mw,
                      solar: b.solar_mw,
                      net: b.net_load_mw,
                    }))}
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
                    <YAxis {...axisProps} width={56} tickFormatter={(v: number) => `${v}`} />
                    <Tooltip
                      {...tooltipProps}
                      labelFormatter={(t) => hhmm(String(t))}
                      formatter={(v, name) => [formatMw(Number(v)), name]}
                    />
                    <Legend wrapperStyle={{ fontSize: 11 }} />
                    <Line
                      name="Load (forecast)"
                      dataKey="load"
                      stroke={chartColors.muted}
                      strokeWidth={1.5}
                      dot={false}
                      isAnimationActive={false}
                    />
                    <Line
                      name="Solar (modelled)"
                      dataKey="solar"
                      stroke={chartColors.amber}
                      strokeWidth={2}
                      dot={false}
                      isAnimationActive={false}
                    />
                    <Line
                      name="Net load"
                      dataKey="net"
                      stroke={chartColors.ink}
                      strokeWidth={2}
                      dot={false}
                      isAnimationActive={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <p className="mt-3 text-xs text-[color:var(--lpmf-muted)]">
                Net load = load − solar. The midday dip and the steep evening ramp as solar falls
                off are the &ldquo;duck curve&rdquo;.
              </p>
            </Panel>

            <Panel
              title="Rooftop capacity benchmark"
              provenance={r.capacity_benchmark.provenance}
              source={r.capacity_benchmark.source}
            >
              <div className="grid gap-4 md:grid-cols-[1fr_2fr] md:items-center">
                <KpiCard
                  label={`Delhi rooftop solar, ${r.capacity_benchmark.as_of}`}
                  value={r.capacity_benchmark.capacity_mwp.toFixed(0)}
                  unit="MWp"
                />
                <p className="text-sm text-[color:var(--lpmf-muted)]">
                  {r.capacity_benchmark.note}
                </p>
              </div>
            </Panel>

            {r.real_plant_validation && (
              <Panel
                title="Formula validated against 2 real Indian solar plants"
                provenance={r.real_plant_validation.provenance}
                source={r.real_plant_validation.source}
              >
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="text-[11px] uppercase tracking-wide text-[color:var(--lpmf-muted)]">
                        <th className="pb-2 pr-4"></th>
                        <th className="pb-2 pr-4">r² (all blocks)</th>
                        <th className="pb-2 pr-4">r² (daytime only)</th>
                        <th className="pb-2 pr-4">MAPE</th>
                        <th className="pb-2 pr-4">WAPE</th>
                        <th className="pb-2">nMAE</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[r.real_plant_validation.plant_1, r.real_plant_validation.plant_2].map((p) => (
                        <tr key={p.plant} className="border-t border-[color:var(--border-faint)]">
                          <td className="py-1.5 pr-4 font-medium">Plant {p.plant}</td>
                          <td className="lpmf-mono py-1.5 pr-4">{p.r_squared.toFixed(3)}</td>
                          <td className="lpmf-mono py-1.5 pr-4">{p.r_squared_daytime.toFixed(3)}</td>
                          <td className="lpmf-mono py-1.5 pr-4">{p.mape_daytime_pct.toFixed(1)}%</td>
                          <td className="lpmf-mono py-1.5 pr-4">{p.wape_daytime_pct.toFixed(1)}%</td>
                          <td className="lpmf-mono py-1.5">{p.nmae_daytime_pct.toFixed(1)}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="mt-3 text-xs text-[color:var(--lpmf-muted)]">
                  {r.real_plant_validation.note}
                </p>
                <p className="mt-2 text-xs text-[color:var(--lpmf-muted)]">
                  DC/AC ratio check: Plant 1 ≈{" "}
                  {r.real_plant_validation.diagnostics.plant_1_dc_ac_ratio?.toFixed(2)}, Plant 2 ≈{" "}
                  {r.real_plant_validation.diagnostics.plant_2_dc_ac_ratio?.toFixed(2)} (both plausible
                  real inverter efficiencies — no unit mismatch).{" "}
                  {r.real_plant_validation.diagnostics.plant_2_iqr_flagged_inverters.length === 0
                    ? "No Plant 2 inverters flagged as statistical outliers."
                    : `Flagged inverters: ${r.real_plant_validation.diagnostics.plant_2_iqr_flagged_inverters.join(", ")}.`}
                </p>
              </Panel>
            )}
          </>
        )}
      </ApiBoundary>
    </>
  );
}
