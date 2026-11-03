"use client";

import { ApiBoundary } from "@/components/dashboard/ApiBoundary";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { Panel } from "@/components/dashboard/Panel";
import { api } from "@/lib/api";
import { formatDate, formatMw, hhmm } from "@/lib/format";
import { useApi } from "@/lib/useApi";

export function OverviewView() {
  const state = useApi("overview", (signal) => api.overview({}, signal));

  return (
    <ApiBoundary state={state} loadingLabel="Reading the latest day-ahead forecast">
      {(o) => (
        <Panel
          title={`Forecast peak · ${formatDate(o.date)}`}
          provenance={o.provenance}
          source={o.source}
        >
          <div className="grid gap-4 md:grid-cols-[2fr_1fr_1fr]">
            <KpiCard
              size="lg"
              label="Peak demand"
              value={formatMw(o.peak_mw).replace(" MW", "")}
              unit="MW"
              tone={o.alert ? "alert" : "default"}
              hint={`Block ${o.peak_block} of 96`}
            />
            <KpiCard label="Peak time" value={o.peak_time} unit="IST" />
            <KpiCard
              label="Alert"
              value={o.alert ? "ALERT" : "Clear"}
              tone={o.alert ? "alert" : "default"}
              hint={
                o.alert
                  ? `${formatMw(o.peak_mw - o.limit_mw)} over the ${formatMw(o.limit_mw)} limit`
                  : `${formatMw(o.limit_mw - o.peak_mw)} below the ${formatMw(o.limit_mw)} limit`
              }
            />
          </div>
          <p className="mt-4 text-xs text-[color:var(--lpmf-muted)]">
            Day-ahead forecast issued {formatDate(o.issued_at)} at {hhmm(o.issued_at)} IST — the
            latest day of the test-period backtest, not a live forecast for tomorrow. The limit is
            Delhi&apos;s all-time peak ({formatMw(o.limit_mw)}, Delhi SLDC).
          </p>
        </Panel>
      )}
    </ApiBoundary>
  );
}
