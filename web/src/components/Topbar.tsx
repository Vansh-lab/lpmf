"use client";

import { signOut } from "next-auth/react";
import { motion, useReducedMotion } from "framer-motion";
import { SourceBadge } from "@/components/SourceBadge";
import { ProvenanceKind } from "@/lib/provenance";

export function Topbar({
  user,
}: {
  user: { name?: string | null; email?: string | null; image?: string | null } | null;
}) {
  const prefersReducedMotion = useReducedMotion();

  return (
    <header className="relative flex h-14 shrink-0 items-center justify-between gap-4 overflow-hidden bg-[color:var(--surface)] px-6">
      <div className="flex min-w-0 items-center gap-3">
        <span className="shrink-0 font-semibold text-[color:var(--foreground)]">LPMF</span>
        <span className="hidden truncate text-sm text-[color:var(--lpmf-muted)] lg:inline">
          Load Profile Management &amp; Forecasting
        </span>
      </div>

      <div className="flex shrink-0 items-center gap-4">
        {/* Global data-provenance legend — see docs/PROVENANCE.md */}
        <div className="hidden items-center gap-1.5 rounded-full border border-[color:var(--border-subtle)] px-2.5 py-1 text-xs text-[color:var(--lpmf-muted)] sm:flex">
          <span>Data:</span>
          <SourceBadge kind={ProvenanceKind.REAL} source="measured" />
          <span>/</span>
          <SourceBadge kind={ProvenanceKind.SYNTHETIC} source="generated" />
        </div>

        <div className="flex items-center gap-2">
          {user?.image ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={user.image}
              alt={user.name ?? user.email ?? "Account"}
              className="size-7 rounded-full"
            />
          ) : (
            <div className="flex size-7 items-center justify-center rounded-full bg-[color:var(--lpmf-ink)] text-xs font-medium text-white">
              {(user?.name ?? user?.email ?? "?").charAt(0).toUpperCase()}
            </div>
          )}
          <span className="hidden text-sm text-[color:var(--foreground)] sm:inline">
            {user?.name ?? user?.email}
          </span>
          <button
            type="button"
            onClick={() => signOut({ callbackUrl: "/login" })}
            className="rounded-md border border-[color:var(--border-subtle)] px-2.5 py-1 text-xs font-medium text-[color:var(--foreground)] transition hover:bg-[color:var(--border-faint)]"
          >
            Sign out
          </button>
        </div>
      </div>

      {/* Status-LED line: a thin amber-to-transparent gradient that drifts
          slowly, like current on a live rail. Ambient only — very low
          opacity, slow loop. */}
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-px overflow-hidden">
        <motion.div
          className="h-full w-1/3"
          style={{
            background:
              "linear-gradient(90deg, transparent, rgba(var(--lpmf-amber-rgb), 0.9), transparent)",
          }}
          animate={prefersReducedMotion ? undefined : { x: ["-100%", "400%"] }}
          transition={{ duration: 7, repeat: Infinity, ease: "linear" }}
        />
      </div>
    </header>
  );
}
