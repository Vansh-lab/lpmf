"use client";

import { motion, useReducedMotion } from "framer-motion";
import { SourceBadge } from "@/components/SourceBadge";
import { ProvenanceKind } from "@/lib/provenance";

/**
 * An empty chart slot. Phase 0 has no data to show, and per
 * docs/PROVENANCE.md this still carries a SourceBadge — it is deliberately
 * empty, not faked. The slow diagonal scan-line reads as an instrument
 * waiting for a signal, not as a loading or fake-data state.
 */
export function ChartSlotEmpty({ label }: { label: string }) {
  const prefersReducedMotion = useReducedMotion();

  return (
    <div
      className="relative flex min-h-64 flex-col items-center justify-center gap-3 overflow-hidden rounded-md border border-dashed border-[color:var(--border-subtle)] bg-[color:var(--surface-sunken)] text-center"
      style={{ boxShadow: "var(--lpmf-shadow-recessed)" }}
    >
      {!prefersReducedMotion && (
        <motion.div
          aria-hidden="true"
          className="pointer-events-none absolute -inset-y-full -left-1/3 w-1/4 rotate-12"
          style={{
            background:
              "linear-gradient(90deg, transparent, rgba(var(--lpmf-amber-rgb), 0.06), transparent)",
          }}
          animate={{ x: ["0%", "420%"] }}
          transition={{ duration: 5, repeat: Infinity, ease: "linear" }}
        />
      )}
      <p className="relative text-sm text-[color:var(--lpmf-muted)]">{label} — no data yet</p>
      <SourceBadge
        kind={ProvenanceKind.ILLUSTRATIVE}
        source="Placeholder — wired up in Phase 2"
        className="relative"
      />
    </div>
  );
}
