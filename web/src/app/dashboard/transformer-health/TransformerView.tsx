"use client";

import { useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceDot,
  ReferenceLine,
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
import { useApi, useDebounced } from "@/lib/useApi";

const EXAMPLE_HOTSPOT_C = 118;
const CURVE_MIN = 40;
const CURVE_MAX = 180;
const CURVE_TEMPS = [
  ...Array.from({ length: (CURVE_MAX - CURVE_MIN) / 10 + 1 }, (_, i) => CURVE_MIN + i * 10),
  EXAMPLE_HOTSPOT_C,
].sort((a, b) => a - b);

const formatV = (v: number) => (v >= 100 ? v.toFixed(0) : v >= 1 ? v.toFixed(2) : v.toPrecision(2));

export function TransformerView() {
  const [hotspot, setHotspot] = useState(EXAMPLE_HOTSPOT_C);
  const [hours, setHours] = useState(1);
  const debouncedHotspot = useDebounced(hotspot, 200);
  const debouncedHours = useDebounced(hours, 200);

  const reading = useApi(`transformer:${debouncedHotspot}:${debouncedHours}`, (signal) =>
    api.transformer({ hotspot_temp_c: debouncedHotspot, hours: debouncedHours }, signal),
  );
  // The curve is drawn from the API too (one call per temperature), so the
  // page never re-implements the ageing formula.
  const curve = useApi("transformer-curve", (signal) =>
    Promise.all(CURVE_TEMPS.map((t) => api.transformer({ hotspot_temp_c: t }, signal))),
  );

  return (
    <>
      <Panel title="Hot-spot temperature">
        <div className="grid gap-5 md:grid-cols-2">
          <SliderField
            label="Winding hot-spot"
            unit="°C"
            min={-50}
            max={250}
            step={1}
            value={hotspot}
            onChange={setHotspot}
            hint={`Default ${EXAMPLE_HOTSPOT_C} °C: the deck's example of a 40 °C day at full load.`}
          />
          <SliderField
            label="Held for"
            unit="h"
            min={1}
            max={24}
            step={1}
            value={hours}
            onChange={setHours}
            hint="Life used = ageing rate × hours held."
          />
        </div>
      </Panel>

      <ApiBoundary state={reading} loadingLabel="Computing the ageing rate" minHeight={150}>
        {(r) => (
          <Panel title="Insulation ageing" provenance={r.provenance} source={r.source}>
            <div className="grid gap-4 md:grid-cols-[2fr_1fr]">
              <KpiCard
                size="lg"
                label={`Ageing rate at ${r.hotspot_temp_c} °C`}
                value={`${formatV(r.ageing_rate_v)}×`}
                tone={r.ageing_rate_v > 1 ? "alert" : "default"}
                hint="1× is normal ageing (98 °C); every +6 °C doubles it."
              />
              <KpiCard
                label="Life used"
                value={
                  r.life_hours_used >= 100
                    ? r.life_hours_used.toFixed(0)
                    : r.life_hours_used.toFixed(2)
                }
                unit="h"
                hint={`of insulation life in ${r.hours_elapsed} h at this hot-spot`}
              />
            </div>
          </Panel>
        )}
      </ApiBoundary>

      <ApiBoundary state={curve} loadingLabel="Tracing the ageing curve">
        {(points) => {
          const data = points.map((p) => ({ t: p.hotspot_temp_c, v: p.ageing_rate_v }));
          const example = data.find((p) => p.t === EXAMPLE_HOTSPOT_C);
          const current = reading.data;
          const currentOnChart =
            current && current.hotspot_temp_c >= CURVE_MIN && current.hotspot_temp_c <= CURVE_MAX;
          return (
            <Panel
              title="Ageing rate vs hot-spot temperature"
              provenance={points[0]?.provenance}
              source={points[0]?.source}
            >
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={data} margin={{ top: 12, right: 16, left: 0, bottom: 16 }}>
                    <CartesianGrid {...gridProps} vertical />
                    <XAxis
                      {...axisProps}
                      type="number"
                      dataKey="t"
                      domain={[CURVE_MIN, CURVE_MAX]}
                      ticks={[40, 60, 80, 98, 120, 140, 160, 180]}
                      label={{
                        value: "Hot-spot temperature (°C)",
                        position: "insideBottom",
                        offset: -10,
                        fill: "var(--lpmf-muted)",
                        fontSize: 11,
                      }}
                    />
                    <YAxis
                      {...axisProps}
                      scale="log"
                      domain={[0.001, 20000]}
                      ticks={[0.001, 0.01, 0.1, 1, 10, 100, 1000, 10000]}
                      allowDataOverflow
                      width={52}
                      tickFormatter={(v: number) => `${v}×`}
                    />
                    <Tooltip
                      {...tooltipProps}
                      labelFormatter={(t) => `${t} °C`}
                      formatter={(v) => [`${formatV(Number(v))}×`, "Ageing rate"]}
                    />
                    <ReferenceLine
                      y={1}
                      stroke={chartColors.green}
                      strokeDasharray="4 3"
                      label={{
                        value: "V = 1, normal ageing",
                        position: "insideTopLeft",
                        fill: "var(--lpmf-green-text)",
                        fontSize: 11,
                      }}
                    />
                    <Line
                      dataKey="v"
                      stroke={chartColors.amber}
                      strokeWidth={2}
                      dot={false}
                      isAnimationActive={false}
                    />
                    {example && (
                      <ReferenceDot
                        x={example.t}
                        y={example.v}
                        r={5}
                        fill="var(--surface)"
                        stroke={chartColors.ink}
                        strokeWidth={2}
                        label={{
                          // Kept short so it clears the y-axis at phone width; the caption names it.
                          value: `${example.t} °C → ${formatV(example.v)}×`,
                          position: "left",
                          fill: "var(--foreground)",
                          fontSize: 11,
                        }}
                      />
                    )}
                    {currentOnChart && (
                      <ReferenceDot
                        x={current.hotspot_temp_c}
                        y={current.ageing_rate_v}
                        r={6}
                        fill={chartColors.amber}
                        stroke="var(--surface)"
                        strokeWidth={2}
                      />
                    )}
                  </LineChart>
                </ResponsiveContainer>
              </div>
              <p className="mt-3 text-xs text-[color:var(--lpmf-muted)]">
                Log scale. The amber dot is the slider&apos;s value
                {currentOnChart ? "" : " (outside the 40–180 °C range shown)"}; the hollow dot is
                the deck&apos;s worked example.
              </p>
            </Panel>
          );
        }}
      </ApiBoundary>
    </>
  );
}
