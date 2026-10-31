import { PlaceholderPage } from "@/components/PlaceholderPage";

export default function WeatherImpactPage() {
  return (
    <PlaceholderPage
      title="03 · Weather Impact"
      equation="L = \beta_0 + \beta_1 \cdot \mathrm{HI} + \varepsilon"
      equationCaption="Load regressed on heat index (HI); β₁ is the MW/°C sensitivity."
      chartLabel="Load vs heat index"
    />
  );
}
