import clsx from "clsx";

/** A large instrument reading. `tone="alert"` adds the red alert glow. */
export function KpiCard({
  label,
  value,
  unit,
  hint,
  tone = "default",
  size = "md",
}: {
  label: React.ReactNode;
  value: string;
  unit?: string;
  hint?: React.ReactNode;
  tone?: "default" | "alert";
  size?: "md" | "lg";
}) {
  const alert = tone === "alert";
  return (
    <div
      className={clsx(
        "rounded-lg border bg-[color:var(--surface-sunken)] p-4",
        alert ? "border-[color:var(--lpmf-red)]/60" : "border-[color:var(--border-faint)]",
      )}
      style={{
        boxShadow: alert
          ? "0 0 0 1px rgba(var(--lpmf-red-rgb), 0.45), 0 0 26px rgba(var(--lpmf-red-rgb), 0.35)"
          : "var(--lpmf-shadow-recessed)",
      }}
    >
      <p className="text-xs font-medium uppercase tracking-wide text-[color:var(--lpmf-muted)]">
        {label}
      </p>
      <p
        className={clsx(
          "lpmf-mono mt-1 font-semibold leading-tight",
          size === "lg" ? "text-4xl sm:text-5xl" : "text-2xl sm:text-3xl",
          alert ? "text-[color:var(--lpmf-red)]" : "text-[color:var(--foreground)]",
        )}
      >
        {value}
        {unit && (
          <span className="ml-1.5 text-base font-medium text-[color:var(--lpmf-muted)]">
            {unit}
          </span>
        )}
      </p>
      {hint && <div className="mt-1.5 text-xs text-[color:var(--lpmf-muted)]">{hint}</div>}
    </div>
  );
}
