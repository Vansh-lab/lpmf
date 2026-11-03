"use client";

import { motion, useReducedMotion } from "framer-motion";

/**
 * Loading state for a chart or reading: the instrument-panel scan-line
 * sweeping an empty recessed slot, like a scope waiting for its signal.
 */
export function ScanLoading({ label, minHeight = 256 }: { label: string; minHeight?: number }) {
  const prefersReducedMotion = useReducedMotion();

  return (
    <div
      role="status"
      aria-busy="true"
      className="relative flex flex-col items-center justify-center gap-2 overflow-hidden rounded-md border border-dashed border-[color:var(--border-subtle)] bg-[color:var(--surface-sunken)] text-center"
      style={{ boxShadow: "var(--lpmf-shadow-recessed)", minHeight }}
    >
      {!prefersReducedMotion && (
        <motion.div
          aria-hidden="true"
          className="pointer-events-none absolute -inset-y-full -left-1/3 w-1/4 rotate-12"
          style={{
            background:
              "linear-gradient(90deg, transparent, rgba(var(--lpmf-amber-rgb), 0.10), transparent)",
          }}
          animate={{ x: ["0%", "420%"] }}
          transition={{ duration: 2.4, repeat: Infinity, ease: "linear" }}
        />
      )}
      <p className="lpmf-mono relative text-xs tracking-wide text-[color:var(--lpmf-muted)]">
        {label}…
      </p>
    </div>
  );
}
