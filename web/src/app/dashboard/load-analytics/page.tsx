import { PlaceholderPage } from "@/components/PlaceholderPage";

export default function LoadAnalyticsPage() {
  return (
    <PlaceholderPage
      title="02 · Load Analytics"
      equation="L(t) = T(t) + S(t) + R(t)"
      equationCaption="Load decomposed into trend, seasonal, and residual components."
      chartLabel="Load decomposition"
    />
  );
}
