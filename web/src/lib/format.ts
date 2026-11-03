const mwFormat = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });
const rupeeFormat = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

export const formatMw = (mw: number) => `${mwFormat.format(mw)} MW`;

/** ₹ with Indian digit grouping, e.g. ₹3,47,500. */
export const formatRupees = (rupees: number) => rupeeFormat.format(rupees);

/** ₹ in lakh, e.g. 347500 -> "₹3.475 lakh" (trailing zeros dropped). */
export const formatLakh = (rupees: number) =>
  `₹${Number((rupees / 1e5).toFixed(3)).toLocaleString("en-IN")} lakh`;

export const formatPct = (fraction: number, digits = 1) => `${(fraction * 100).toFixed(digits)}%`;

/** "HH:MM" from an ISO timestamp that already carries the IST offset (no tz conversion). */
export const hhmm = (iso: string) => iso.slice(11, 16);

/** "12 Jan 2026" from an ISO date string, without timezone shifts. */
export function formatDate(isoDate: string) {
  const [y, m, d] = isoDate.slice(0, 10).split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d)).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  });
}
