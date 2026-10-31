import { PlaceholderPage } from "@/components/PlaceholderPage";

export default function OverviewPage() {
  return (
    <PlaceholderPage
      title="01 · Overview"
      equation="E = \int_{0}^{24} L(t)\,dt"
      equationCaption="Daily energy is the integral of the load curve over 24 hours."
      chartLabel="Load overview"
    />
  );
}
