/**
 * Shared Recharts styling. Colors are the theme's CSS variables, so charts
 * follow light/dark mode without re-rendering.
 */

export const chartColors = {
  amber: "var(--lpmf-amber)",
  green: "var(--lpmf-green)",
  red: "var(--lpmf-red)",
  ink: "var(--foreground)",
  muted: "var(--lpmf-muted)",
  grid: "var(--border-subtle)",
};

export const axisProps = {
  stroke: "var(--border-subtle)",
  tick: { fill: "var(--lpmf-muted)", fontSize: 11 },
  tickLine: false,
} as const;

export const gridProps = {
  stroke: "var(--border-subtle)",
  strokeDasharray: "3 3",
  vertical: false,
} as const;

export const tooltipProps = {
  contentStyle: {
    background: "var(--surface)",
    border: "1px solid var(--border-subtle)",
    borderRadius: 6,
    color: "var(--foreground)",
    fontSize: 12,
  },
  labelStyle: { color: "var(--lpmf-muted)", marginBottom: 2 },
  itemStyle: { color: "var(--foreground)", padding: 0 },
  cursor: { stroke: "var(--lpmf-muted)", strokeDasharray: "3 3" },
} as const;
