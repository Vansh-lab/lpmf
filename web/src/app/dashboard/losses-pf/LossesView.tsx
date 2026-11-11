"use client";

import { useState } from "react";
import { ApiBoundary } from "@/components/dashboard/ApiBoundary";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { Panel } from "@/components/dashboard/Panel";
import { SliderField } from "@/components/dashboard/SliderField";
import { ProvenanceKind } from "@/lib/provenance";
import { api } from "@/lib/api";
import { useApi, useDebounced } from "@/lib/useApi";

export function LossesView() {
  const [power, setPower] = useState(1000);
  const [pf1, setPf1] = useState(0.75);
  const [pf2, setPf2] = useState(0.95);
  const [current, setCurrent] = useState(300);
  const [resistance, setResistance] = useState(0.1);

  const d = {
    power: useDebounced(power, 250),
    pf1: useDebounced(pf1, 250),
    pf2: useDebounced(pf2, 250),
    current: useDebounced(current, 250),
    resistance: useDebounced(resistance, 250),
  };
  const state = useApi(
    `losses:${d.power}:${d.pf1}:${d.pf2}:${d.current}:${d.resistance}`,
    (signal) =>
      api.losses(
        {
          active_power_kw: d.power,
          pf1: d.pf1,
          pf2: d.pf2,
          current_a: d.current,
          resistance_ohm: d.resistance,
        },
        signal,
      ),
  );

  return (
    <>
      <IllustrativeBanner />

      <Panel title="Load and power factor">
        <div className="grid gap-5 md:grid-cols-2">
          <SliderField
            label="Active power"
            unit="kW"
            min={0}
            max={5000}
            step={10}
            value={power}
            onChange={setPower}
          />
          <SliderField
            label="Present PF"
            unit=""
            min={0.5}
            max={1}
            step={0.01}
            value={pf1}
            onChange={(v) => setPf1(Math.min(v, pf2))}
            hint="Lagging power factor before correction."
          />
          <SliderField
            label="Target PF"
            unit=""
            min={0.5}
            max={1}
            step={0.01}
            value={pf2}
            onChange={(v) => setPf2(Math.max(v, pf1))}
            hint="What the capacitor bank should raise PF to."
          />
        </div>
      </Panel>

      <Panel title="Feeder, before correction">
        <div className="grid gap-5 md:grid-cols-2">
          <SliderField
            label="Feeder current"
            unit="A"
            min={0}
            max={1000}
            step={5}
            value={current}
            onChange={setCurrent}
            hint="Per phase, at the present PF."
          />
          <SliderField
            label="Feeder resistance"
            unit="Ω/phase"
            min={0}
            max={2}
            step={0.01}
            value={resistance}
            onChange={setResistance}
          />
        </div>
      </Panel>

      <ApiBoundary state={state} loadingLabel="Computing PF correction and I²R loss" minHeight={220}>
        {(r) => (
          <>
            <Panel title="Illustrative result" provenance={r.provenance} source={r.source}>
              <div className="grid gap-4 md:grid-cols-3">
                <KpiCard
                  size="lg"
                  label={`Capacitor bank, PF ${r.pf1} → ${r.pf2}`}
                  value={r.capacitor_kvar.toFixed(0)}
                  unit="kVAR"
                  hint="Q_c = P · (tan φ1 − tan φ2)"
                />
                <KpiCard
                  label="I²R loss before correction"
                  value={r.loss_kw.toFixed(2)}
                  unit="kW"
                  hint={`${r.current_a} A at ${r.resistance_ohm} Ω/phase, 3-phase`}
                />
                <KpiCard
                  label="Loss saved after correction"
                  value={r.loss_reduction_pct.toFixed(1)}
                  unit="%"
                  hint="Current falls as PF rises (I ∝ 1/PF at constant P, V), so I²R loss falls as (PF1/PF2)²."
                />
              </div>
            </Panel>

            <Panel
              title="AT&C loss benchmark"
              provenance={r.at_c_benchmark.provenance as ProvenanceKind}
              source={r.at_c_benchmark.source}
            >
              <div className="grid gap-4 md:grid-cols-[1fr_2fr] md:items-center">
                <KpiCard
                  label={`National AT&C loss, ${r.at_c_benchmark.year}`}
                  value={r.at_c_benchmark.at_c_loss_pct.toFixed(2)}
                  unit="%"
                />
                <p className="text-sm text-[color:var(--lpmf-muted)]">{r.at_c_benchmark.note}</p>
              </div>
            </Panel>
          </>
        )}
      </ApiBoundary>
    </>
  );
}

function IllustrativeBanner() {
  return (
    <div
      role="note"
      className="rounded-lg border-2 border-[color:var(--lpmf-amber)] bg-[color:var(--lpmf-amber)]/10 p-4"
    >
      <p className="text-sm font-semibold uppercase tracking-wide text-[color:var(--lpmf-amber-text)]">
        Illustrative what-if — not a reading from a real feeder
      </p>
      <p className="mt-1 text-sm text-[color:var(--foreground)]">
        Power, PF, current and resistance are inputs you choose. Only the AT&C benchmark below is a
        real, sourced figure — and it is national, not Delhi-specific.
      </p>
    </div>
  );
}
