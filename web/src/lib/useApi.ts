"use client";

import { useEffect, useRef, useState } from "react";
import { ApiError } from "@/lib/api";

export type ApiState<T> =
  | { status: "loading"; data?: T }
  | { status: "error"; error: ApiError; data?: T }
  | { status: "ready"; data: T };

/**
 * Runs `fetcher` whenever `key` changes, aborting the previous request.
 * While a refetch is in flight the previous `data` is kept, so controls
 * like sliders update a chart instead of blanking it.
 */
export function useApi<T>(
  key: string,
  fetcher: (signal: AbortSignal) => Promise<T>,
): ApiState<T> & { retry: () => void } {
  const [state, setState] = useState<ApiState<T>>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;

  useEffect(() => {
    const controller = new AbortController();
    setState((prev) => ({ status: "loading", data: prev.data }));
    fetcherRef
      .current(controller.signal)
      .then((data) => setState({ status: "ready", data }))
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        const error = err instanceof ApiError ? err : new ApiError(String(err), null);
        setState((prev) => ({ status: "error", error, data: prev.data }));
      });
    return () => controller.abort();
  }, [key, attempt]);

  return { ...state, retry: () => setAttempt((n) => n + 1) };
}

/** `value`, but only after it has stopped changing for `ms` milliseconds. */
export function useDebounced<T>(value: T, ms = 200): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), ms);
    return () => clearTimeout(id);
  }, [value, ms]);
  return debounced;
}
