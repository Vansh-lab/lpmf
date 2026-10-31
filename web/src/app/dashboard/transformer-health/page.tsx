import { PlaceholderPage } from "@/components/PlaceholderPage";

export default function TransformerHealthPage() {
  return (
    <PlaceholderPage
      title="06 · Transformer Health"
      equation="\theta_H = \theta_A + \Delta\theta_{TO} + \Delta\theta_H"
      equationCaption="Hot-spot winding temperature: ambient + top-oil rise + hot-spot-to-top-oil gradient (IEEE C57.91)."
      chartLabel="Transformer thermal loading"
    />
  );
}
