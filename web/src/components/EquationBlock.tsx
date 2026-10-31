import katex from "katex";

/** Renders a governing equation with KaTeX (server-side, no client JS). */
export function EquationBlock({ latex, caption }: { latex: string; caption?: string }) {
  const html = katex.renderToString(latex, { throwOnError: false, displayMode: true });

  return (
    <div className="rounded-md border border-[color:var(--border-subtle)] bg-[color:var(--surface)] px-4 py-3">
      <div dangerouslySetInnerHTML={{ __html: html }} />
      {caption && (
        <p className="mt-1 text-center text-xs text-[color:var(--lpmf-muted)]">{caption}</p>
      )}
    </div>
  );
}
