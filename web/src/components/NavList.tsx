"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import { motion } from "framer-motion";
import { NAV_ITEMS } from "@/lib/nav";

/**
 * The dashboard's page list, shared by the desktop sidebar and the mobile
 * drawer. `indicatorId` must differ per mounted list: framer-motion animates
 * every element sharing a layoutId as one.
 */
export function NavList({
  indicatorId,
  onNavigate,
}: {
  indicatorId: string;
  onNavigate?: () => void;
}) {
  const pathname = usePathname();

  return (
    <ul className="flex-1 space-y-0.5 px-2">
      {NAV_ITEMS.map((item) => {
        const isActive = pathname?.startsWith(item.href);
        const disabled = item.phase === 2;

        if (disabled) {
          return (
            <li key={item.href}>
              <span
                className="flex cursor-not-allowed items-center gap-3 rounded-md px-3 py-2 text-sm text-[color:var(--lpmf-muted)] opacity-50"
                title="Coming in Phase 2"
              >
                <span className="lpmf-mono w-5 shrink-0 text-xs">{item.order}</span>
                <span className="flex-1">{item.label}</span>
                <span className="rounded border border-[color:var(--border-subtle)] px-1.5 py-0.5 text-[10px] uppercase tracking-wide">
                  Phase 2
                </span>
              </span>
            </li>
          );
        }

        return (
          <li key={item.href} className="relative">
            {isActive && (
              <motion.span
                layoutId={indicatorId}
                transition={{ type: "spring", stiffness: 300, damping: 30 }}
                className="absolute inset-y-1 left-0 w-0.5 rounded-r-full bg-[color:var(--lpmf-amber)]"
                style={{ boxShadow: "0 0 10px rgba(var(--lpmf-amber-rgb), 0.7)" }}
              />
            )}
            <Link
              href={item.href}
              onClick={onNavigate}
              aria-current={isActive ? "page" : undefined}
              className={clsx(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                isActive
                  ? "bg-[color:var(--lpmf-amber)]/10 font-medium text-[color:var(--foreground)]"
                  : "text-[color:var(--foreground)] hover:bg-[color:var(--border-faint)]",
              )}
            >
              <span className="lpmf-mono w-5 shrink-0 text-xs text-[color:var(--lpmf-muted)]">
                {item.order}
              </span>
              <span className="flex-1">{item.label}</span>
            </Link>
          </li>
        );
      })}
    </ul>
  );
}
