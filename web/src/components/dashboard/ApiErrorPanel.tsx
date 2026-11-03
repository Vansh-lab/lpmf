import type { ApiError } from "@/lib/api";

/** Shown instead of a chart when its API call failed — never a blank chart. */
export function ApiErrorPanel({
  error,
  onRetry,
  minHeight = 256,
}: {
  error: ApiError;
  onRetry: () => void;
  minHeight?: number;
}) {
  const unreachable = error.status === null;
  return (
    <div
      role="alert"
      className="flex flex-col items-center justify-center gap-3 rounded-md border border-[color:var(--lpmf-red)]/40 bg-[color:var(--lpmf-red)]/5 p-6 text-center"
      style={{ minHeight }}
    >
      <p className="text-sm font-semibold text-[color:var(--lpmf-red)]">
        {unreachable ? "API not reachable" : `API error${error.status ? ` (${error.status})` : ""}`}
      </p>
      <p className="max-w-md text-sm text-[color:var(--foreground)]">{error.message}</p>
      <button
        type="button"
        onClick={onRetry}
        className="rounded-md border border-[color:var(--border-subtle)] px-3 py-1.5 text-xs font-medium text-[color:var(--foreground)] transition hover:bg-[color:var(--border-faint)]"
      >
        Retry
      </button>
    </div>
  );
}
