import katex from "katex";

/** Renders a governing equation with KaTeX (server-side, no client JS). */
export function EquationBlock({ latex, caption }: { latex: string; caption?: string }) {
  const html = katex.renderToString(latex, { throwOnError: false, displayMode: true });

  return (
    <div className="group rounded-md border-l-2 border-l-[color:var(--lpmf-amber)] bg-[color:var(--surface)] px-4 py-3 shadow-[var(--lpmf-shadow-recessed)] transition-shadow duration-300 hover:shadow-[0_0_0_1px_rgba(var(--lpmf-amber-rgb),0.25),0_0_22px_rgba(var(--lpmf-amber-rgb),0.12),var(--lpmf-shadow-recessed)]">
      <div dangerouslySetInnerHTML={{ __html: html }} />
      {caption && (
        <p className="mt-1 text-center text-xs text-[color:var(--lpmf-muted)]">{caption}</p>
      )}
    </div>
  );
}
