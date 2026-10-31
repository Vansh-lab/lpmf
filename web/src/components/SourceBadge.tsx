import clsx from "clsx";
import { PROVENANCE_LABELS, ProvenanceKind } from "@/lib/provenance";

/**
 * Renders the data-provenance tag every chart and number in LPMF must carry.
 * See docs/PROVENANCE.md.
 */
export function SourceBadge({
  kind,
  source,
  className,
}: {
  kind: ProvenanceKind;
  source: string;
  className?: string;
}) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[11px] font-medium leading-tight",
        kindStyles[kind],
        className,
      )}
      title={`Data source: ${source}`}
    >
      <span className={clsx("size-1.5 rounded-full", dotStyles[kind])} aria-hidden />
      {PROVENANCE_LABELS[kind]}
      <span className="text-[color:var(--lpmf-muted)]">· {source}</span>
    </span>
  );
}

const kindStyles: Record<ProvenanceKind, string> = {
  [ProvenanceKind.REAL]:
    "border-[color:var(--lpmf-green)]/30 bg-[color:var(--lpmf-green)]/10 text-[color:var(--lpmf-green)]",
  [ProvenanceKind.SYNTHETIC]:
    "border-[color:var(--lpmf-amber)]/30 bg-[color:var(--lpmf-amber)]/10 text-[color:var(--lpmf-amber)]",
  [ProvenanceKind.FOREIGN]:
    "border-[color:var(--lpmf-muted)]/30 bg-[color:var(--lpmf-muted)]/10 text-[color:var(--lpmf-muted)]",
  [ProvenanceKind.ILLUSTRATIVE]:
    "border-[color:var(--lpmf-muted)]/30 bg-transparent text-[color:var(--lpmf-muted)] italic",
};

const dotStyles: Record<ProvenanceKind, string> = {
  [ProvenanceKind.REAL]: "bg-[color:var(--lpmf-green)]",
  [ProvenanceKind.SYNTHETIC]: "bg-[color:var(--lpmf-amber)]",
  [ProvenanceKind.FOREIGN]: "bg-[color:var(--lpmf-muted)]",
  [ProvenanceKind.ILLUSTRATIVE]: "bg-[color:var(--lpmf-muted)]",
};
