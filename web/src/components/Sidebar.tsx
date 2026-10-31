"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import { NAV_ITEMS } from "@/lib/nav";

export function Sidebar() {
  const pathname = usePathname();

  return (
    <nav className="hidden h-full w-64 shrink-0 flex-col overflow-y-auto border-r border-[color:var(--border-subtle)] bg-[color:var(--surface)] py-4 md:flex">
      <div className="px-5 pb-4 text-sm font-semibold tracking-wide text-[color:var(--foreground)]">
        LPMF
      </div>
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
                  <span className="w-5 shrink-0 font-mono text-xs">{item.order}</span>
                  <span className="flex-1">{item.label}</span>
                  <span className="rounded border border-[color:var(--border-subtle)] px-1.5 py-0.5 text-[10px] uppercase tracking-wide">
                    Phase 2
                  </span>
                </span>
              </li>
            );
          }

          return (
            <li key={item.href}>
              <Link
                href={item.href}
                className={clsx(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition",
                  isActive
                    ? "bg-[color:var(--lpmf-amber)]/10 font-medium text-[color:var(--foreground)]"
                    : "text-[color:var(--foreground)] hover:bg-[color:var(--border-subtle)]/60",
                )}
              >
                <span className="w-5 shrink-0 font-mono text-xs text-[color:var(--lpmf-muted)]">
                  {item.order}
                </span>
                <span className="flex-1">{item.label}</span>
              </Link>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
