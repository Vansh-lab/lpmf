"use client";

import { useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ApiBoundary } from "@/components/dashboard/ApiBoundary";
import { axisProps, chartColors, gridProps, tooltipProps } from "@/components/dashboard/chartTheme";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { Panel } from "@/components/dashboard/Panel";
import { SliderField } from "@/components/dashboard/SliderField";
import { formatRupees } from "@/lib/format";
import { api } from "@/lib/api";
import { useApi, useDebounced } from "@/lib/useApi";

export function TodBillView() {
  const [totalKwh, setTotalKwh] = useState(10);
  const [peakFraction, setPeakFraction] = useState(0.4);
  const [shiftFraction, setShiftFraction] = useState(0.3);

  const d = {
    totalKwh: useDebounced(totalKwh, 250),
    peakFraction: useDebounced(peakFraction, 250),
    shiftFraction: useDebounced(shiftFraction, 250),
  };
  const state = useApi(`tod:${d.totalKwh}:${d.peakFraction}:${d.shiftFraction}`, (signal) =>
    api.tod(
      {
        total_daily_kwh: d.totalKwh,
        evening_peak_fraction: d.peakFraction,
        shift_fraction: d.shiftFraction,
      },
      signal,
    ),
  );

  return (
    <>
      <IllustrativeBanner />

      <Panel title="Illustrative daily profile">
        <div className="grid gap-5 md:grid-cols-3">
          <SliderField
            label="Daily energy"
            unit="kWh"
            min={1}
            max={50}
            step={1}
            value={totalKwh}
            onChange={setTotalKwh}
          />
          <SliderField
            label="Evening-peak share"
            unit=""
            min={0}
            max={1}
            step={0.05}
            value={peakFraction}
            onChange={setPeakFraction}
            hint="Share of the day's kWh used 17:00–22:00."
          />
          <SliderField
            label="Shift to off-peak"
            unit=""
            min={0}
            max={1}
            step={0.05}
            value={shiftFraction}
            onChange={setShiftFraction}
            hint="Share of that peak energy moved to 22:00–06:00."
          />
        </div>
      </Panel>

      <ApiBoundary state={state} loadingLabel="Computing the ToD bill" minHeight={260}>
        {(r) => (
          <>
            <Panel
              title={`DERC ToD rates, ${r.rates.order_year}`}
              provenance={r.rates.provenance}
              source={r.rates.source}
            >
              <div className="grid gap-4 md:grid-cols-2">
                <KpiCard
                  label="Peak surcharge (17:00–22:00)"
                  value={`+${r.rates.peak_surcharge_pct}`}
                  unit="%"
                />
                <KpiCard
                  label="Off-peak rebate (22:00–06:00)"
                  value={`-${r.rates.off_peak_rebate_pct}`}
                  unit="%"
                />
              </div>
              <p className="mt-3 text-xs text-[color:var(--lpmf-muted)]">{r.rates.note}</p>
            </Panel>

            <Panel title="Flat vs ToD vs shifted" provenance={r.provenance} source={r.source}>
              <div className="grid gap-4 md:grid-cols-3">
                <KpiCard label="Flat-rate bill" value={formatRupees(r.flat_bill_rupees)} />
                <KpiCard
                  label="ToD bill, as used"
                  value={formatRupees(r.tod_bill_rupees)}
                  tone={r.tod_bill_rupees > r.flat_bill_rupees ? "alert" : "default"}
                  hint={
                    r.savings_rupees >= 0
                      ? `${formatRupees(r.savings_rupees)} cheaper than flat`
                      : `${formatRupees(-r.savings_rupees)} more than flat — this profile is peak-heavy`
                  }
                />
                <KpiCard
                  size="lg"
                  label="ToD bill after shifting"
                  value={formatRupees(r.shifted_tod_bill_rupees)}
                  hint={`${formatRupees(r.shifted_savings_rupees)}/day saved by shifting · ${formatRupees(r.shifted_savings_rupees * 30)}/month`}
                />
              </div>
            </Panel>

            <Panel title="Hourly cost, as used (illustrative profile)">
              <div className="h-72">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={r.hourly_cost_rupees.map((cost, h) => ({ h, cost }))}
                    margin={{ top: 8, right: 8, left: 0, bottom: 16 }}
                  >
                    <CartesianGrid {...gridProps} />
                    <XAxis
                      {...axisProps}
                      dataKey="h"
                      tickFormatter={(h: number) => `${h}:00`}
                      interval={2}
                      label={{
                        value: "Hour of day",
                        position: "insideBottom",
                        offset: -8,
                        fill: "var(--lpmf-muted)",
                        fontSize: 11,
                      }}
                    />
                    <YAxis {...axisProps} width={44} tickFormatter={(v: number) => `₹${v}`} />
                    <Tooltip
                      {...tooltipProps}
                      labelFormatter={(h) => `${h}:00–${(Number(h) + 1) % 24}:00`}
                      formatter={(v) => [formatRupees(Number(v)), "Cost"]}
                    />
                    <Bar dataKey="cost" isAnimationActive={false}>
                      {r.hourly_cost_rupees.map((_, h) => (
                        <Cell
                          key={h}
                          fill={
                            r.rates.peak_hours.includes(h)
                              ? chartColors.red
                              : r.rates.off_peak_hours.includes(h)
                                ? chartColors.green
                                : chartColors.amber
                          }
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <p className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-[color:var(--lpmf-muted)]">
                <Legend color={chartColors.red} label="Peak" />
                <Legend color={chartColors.green} label="Off-peak" />
                <Legend color={chartColors.amber} label="Normal" />
              </p>
            </Panel>
          </>
        )}
      </ApiBoundary>
    </>
  );
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className="size-2 rounded-full" style={{ background: color }} aria-hidden />
      {label}
    </span>
  );
}

function IllustrativeBanner() {
  return (
    <div
      role="note"
      className="rounded-lg border-2 border-[color:var(--lpmf-amber)] bg-[color:var(--lpmf-amber)]/10 p-4"
    >
      <p className="text-sm font-semibold uppercase tracking-wide text-[color:var(--lpmf-amber-text)]">
        Illustrative household — not a real metered consumer
      </p>
      <p className="mt-1 text-sm text-[color:var(--foreground)]">
        The DERC surcharge/rebate percentages are real; the 24-hour load shape is a slider-built
        illustration, not a measured bill.
      </p>
    </div>
  );
}
