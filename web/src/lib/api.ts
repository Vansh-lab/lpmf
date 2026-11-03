/**
 * Typed client for the LPMF FastAPI service (api/). Response and parameter
 * types come from api/openapi.json via `npm run api-types` — regenerate them
 * whenever the API's contract changes.
 */

import type { components, paths } from "@/lib/api-types";

type Schemas = components["schemas"];
export type OverviewResponse = Schemas["OverviewResponse"];
export type AnalyticsResponse = Schemas["AnalyticsResponse"];
export type WeatherResponse = Schemas["WeatherResponse"];
export type ForecastResponse = Schemas["ForecastResponse"];
export type ForecastDatesResponse = Schemas["ForecastDatesResponse"];
export type DsmResponse = Schemas["DsmResponse"];
export type TransformerResponse = Schemas["TransformerResponse"];

type Query<P extends keyof paths> = paths[P] extends {
  get: { parameters: { query?: infer Q } };
}
  ? NonNullable<Q>
  : never;

export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

/** A failed API call. `status` is null when the API could not be reached at all. */
export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number | null,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function get<T>(
  path: string,
  query: Record<string, string | number | null | undefined> | undefined,
  signal?: AbortSignal,
): Promise<T> {
  const url = new URL(API_BASE_URL + path);
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== null) url.searchParams.set(key, String(value));
  }

  let response: Response;
  try {
    response = await fetch(url, { signal, headers: { Accept: "application/json" } });
  } catch (err) {
    if (signal?.aborted) throw err;
    throw new ApiError(
      `Cannot reach the LPMF API at ${API_BASE_URL}. Start it with \`make dev-api\` and retry.`,
      null,
    );
  }
  if (!response.ok) throw new ApiError(await errorDetail(response), response.status);
  return (await response.json()) as T;
}

/** FastAPI errors carry `detail`: a string, or a list of validation issues. */
async function errorDetail(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail
        .map((d: { loc?: unknown[]; msg?: string }) => `${d.loc?.at(-1) ?? "input"}: ${d.msg}`)
        .join("; ");
    }
  } catch {
    // Not JSON: fall through to the status line.
  }
  return `The API returned ${response.status} ${response.statusText}.`;
}

export const api = {
  overview: (q: Query<"/overview">, signal?: AbortSignal) =>
    get<OverviewResponse>("/overview", q, signal),
  analytics: (q: Query<"/analytics">, signal?: AbortSignal) =>
    get<AnalyticsResponse>("/analytics", q, signal),
  weather: (signal?: AbortSignal) => get<WeatherResponse>("/weather", undefined, signal),
  forecastDates: (signal?: AbortSignal) =>
    get<ForecastDatesResponse>("/forecast/dates", undefined, signal),
  forecast: (q: Query<"/forecast">, signal?: AbortSignal) =>
    get<ForecastResponse>("/forecast", q, signal),
  dsm: (q: Query<"/dsm">, signal?: AbortSignal) => get<DsmResponse>("/dsm", q, signal),
  transformer: (q: Query<"/transformer">, signal?: AbortSignal) =>
    get<TransformerResponse>("/transformer", q, signal),
};
