import clsx from "clsx";
import { SourceBadge } from "@/components/SourceBadge";
import type { ProvenanceKind } from "@/lib/provenance";

/**
 * A raised instrument-panel surface. When it shows data it carries that
 * data's SourceBadge in its header (docs/PROVENANCE.md).
 */
export function Panel({
  title,
  provenance,
  source,
  actions,
  className,
  children,
}: {
  title?: string;
  provenance?: ProvenanceKind | `${ProvenanceKind}`;
  source?: string;
  actions?: React.ReactNode;
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <section
      className={clsx(
        "rounded-lg border border-[color:var(--border-faint)] bg-[color:var(--surface)] p-4 sm:p-5",
        className,
      )}
      style={{ boxShadow: "var(--lpmf-shadow-card)" }}
    >
      {(title || provenance || actions) && (
        <header className="mb-4 flex flex-wrap items-center justify-between gap-2">
          {title && (
            <h2 className="text-sm font-semibold text-[color:var(--foreground)]">{title}</h2>
          )}
          <div className="flex flex-wrap items-center gap-2">
            {actions}
            {provenance && source && (
              <SourceBadge kind={provenance as ProvenanceKind} source={source} />
            )}
          </div>
        </header>
      )}
      {children}
    </section>
  );
}
