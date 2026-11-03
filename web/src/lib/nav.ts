export interface NavItem {
  order: string; // "01".."12"
  label: string;
  href: string;
  phase: 1 | 2;
}

export const NAV_ITEMS: NavItem[] = [
  { order: "01", label: "Overview", href: "/dashboard/overview", phase: 1 },
  { order: "02", label: "Load Analytics", href: "/dashboard/load-analytics", phase: 1 },
  { order: "03", label: "Weather Impact", href: "/dashboard/weather-impact", phase: 1 },
  { order: "04", label: "Forecast", href: "/dashboard/forecast", phase: 1 },
  { order: "05", label: "DSM ₹ Calculator", href: "/dashboard/dsm-calculator", phase: 1 },
  { order: "06", label: "Transformer Health", href: "/dashboard/transformer-health", phase: 1 },
  { order: "07", label: "IEX Price", href: "/dashboard/iex-price", phase: 2 },
  { order: "08", label: "ToD Bill", href: "/dashboard/tod-bill", phase: 2 },
  { order: "09", label: "Solar & Net Load", href: "/dashboard/solar-net-load", phase: 2 },
  { order: "10", label: "Losses & PF", href: "/dashboard/losses-pf", phase: 2 },
  { order: "11", label: "Theft & Segments", href: "/dashboard/theft-segments", phase: 2 },
  { order: "12", label: "Data & Model Card", href: "/dashboard/data-model-card", phase: 1 },
];
