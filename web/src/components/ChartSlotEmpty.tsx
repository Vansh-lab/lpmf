import { SourceBadge } from "@/components/SourceBadge";
import { ProvenanceKind } from "@/lib/provenance";

/**
 * An empty chart slot. Phase 0 has no data to show, and per
 * docs/PROVENANCE.md this still carries a SourceBadge — it is deliberately
 * empty, not faked.
 */
export function ChartSlotEmpty({ label }: { label: string }) {
  return (
    <div className="flex min-h-64 flex-col items-center justify-center gap-3 rounded-md border border-dashed border-[color:var(--border-subtle)] text-center">
      <p className="text-sm text-[color:var(--lpmf-muted)]">{label} — no data yet</p>
      <SourceBadge kind={ProvenanceKind.ILLUSTRATIVE} source="Placeholder — wired up in Phase 2" />
    </div>
  );
}
