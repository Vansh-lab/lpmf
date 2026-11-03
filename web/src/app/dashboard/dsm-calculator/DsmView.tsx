"use client";

import { useState } from "react";
import { ApiBoundary } from "@/components/dashboard/ApiBoundary";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { Panel } from "@/components/dashboard/Panel";
import { SliderField } from "@/components/dashboard/SliderField";
import { api } from "@/lib/api";
import { formatLakh, formatRupees } from "@/lib/format";
import { useApi, useDebounced } from "@/lib/useApi";

export function DsmView() {
  const [deviation, setDeviation] = useState(60);
  const [limit, setLimit] = useState(41);
  const debouncedDeviation = useDebounced(deviation, 250);
  const debouncedLimit = useDebounced(limit, 250);
  const state = useApi(`dsm:${debouncedDeviation}:${debouncedLimit}`, (signal) =>
    api.dsm({ deviation_mw: debouncedDeviation, schedule_limit_mw: debouncedLimit }, signal),
  );

  const absDev = Math.abs(deviation);
  const excess = Math.max(absDev - limit, 0);

  return (
    <>
      <IllustrativeBanner note={state.data?.note} />

      <Panel title="Inputs">
        <div className="grid gap-5 md:grid-cols-2">
          <SliderField
            label="Deviation from schedule"
            unit="MW"
            min={-200}
            max={200}
            step={1}
            value={deviation}
            onChange={setDeviation}
            hint="Per 15-min block; over- and under-drawal are charged alike."
          />
          <SliderField
            label="Volume limit"
            unit="MW"
            min={0}
            max={200}
            step={1}
            value={limit}
            onChange={setLimit}
            hint="Deviation up to this is charged at the normal rate."
          />
        </div>
        <p className="mt-4 text-xs text-[color:var(--lpmf-muted)]">
          {Math.min(absDev, limit)} MW within the limit
          {excess > 0 ? `, ${excess} MW above it at the higher rate` : ", nothing above it"}.
        </p>
      </Panel>

      <ApiBoundary state={state} loadingLabel="Computing the deviation charge" minHeight={180}>
        {(d) => (
          <Panel title="Illustrative charge" provenance={d.provenance} source={d.source}>
            <div className="grid gap-4 md:grid-cols-[2fr_1fr_1fr]">
              <KpiCard
                size="lg"
                label={`Charge for ${d.n_blocks} blocks (${d.n_blocks / 4} h)`}
                value={formatRupees(d.penalty_rupees)}
                hint={`${formatLakh(d.penalty_rupees)} · illustrative, not a real penalty`}
              />
              <KpiCard
                label="Per 15-min block"
                value={formatRupees(d.per_block_rupees[0] ?? 0)}
                hint={`× ${d.n_blocks} blocks`}
              />
              <KpiCard
                label="Assumed rates"
                value={`₹${d.normal_rate_per_mwh.toLocaleString("en-IN")}`}
                unit="/MWh"
                hint={`Excess at k = ${d.excess_multiplier} × the normal rate`}
              />
            </div>
          </Panel>
        )}
      </ApiBoundary>
    </>
  );
}

function IllustrativeBanner({ note }: { note?: string }) {
  return (
    <div
      role="note"
      className="rounded-lg border-2 border-[color:var(--lpmf-amber)] bg-[color:var(--lpmf-amber)]/10 p-4"
    >
      <p className="text-sm font-semibold uppercase tracking-wide text-[color:var(--lpmf-amber-text)]">
        Illustrative calculator — these are not real DSM penalties
      </p>
      <p className="mt-1 text-sm text-[color:var(--foreground)]">
        {note ??
          "The charge uses one flat normal rate and one excess multiplier; the CERC frequency-linked normal-rate tables are not encoded."}{" "}
        Use it to see how the charge scales with deviation, never as a figure a DISCOM would pay.
      </p>
    </div>
  );
}
