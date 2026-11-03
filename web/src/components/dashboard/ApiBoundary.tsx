"use client";

import { ApiErrorPanel } from "@/components/dashboard/ApiErrorPanel";
import { ScanLoading } from "@/components/dashboard/ScanLoading";
import type { ApiState } from "@/lib/useApi";

/**
 * Renders the scan-line while the first response loads, the error panel if
 * the call failed, and `children(data)` once data exists. A refetch keeps the
 * previous data on screen, dimmed, rather than flashing the loader.
 */
export function ApiBoundary<T>({
  state,
  loadingLabel,
  minHeight,
  children,
}: {
  state: ApiState<T> & { retry: () => void };
  loadingLabel: string;
  minHeight?: number;
  children: (data: T) => React.ReactNode;
}) {
  if (state.status === "error") {
    return <ApiErrorPanel error={state.error} onRetry={state.retry} minHeight={minHeight} />;
  }
  if (state.data === undefined) {
    return <ScanLoading label={loadingLabel} minHeight={minHeight} />;
  }
  return (
    <div
      aria-busy={state.status === "loading"}
      className={
        state.status === "loading"
          ? "space-y-5 opacity-70 transition-opacity"
          : "space-y-5 transition-opacity"
      }
    >
      {children(state.data)}
    </div>
  );
}
