import { PlaceholderPage } from "@/components/PlaceholderPage";

export default function ForecastPage() {
  return (
    <PlaceholderPage
      title="04 · Forecast"
      equation="\hat{L}_{t+h} \pm q_{1-\alpha}"
      equationCaption="Point forecast with a conformal prediction interval at level 1−α."
      chartLabel="Forecast with prediction interval"
    />
  );
}
