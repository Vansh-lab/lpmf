import { EquationBlock } from "@/components/EquationBlock";
import { PageShell } from "@/components/dashboard/PageShell";
import { TheftSegmentsView } from "./TheftSegmentsView";

export default function TheftSegmentsPage() {
  return (
    <PageShell
      title="11 · Theft & Segments"
      equation={
        <EquationBlock
          latex="\text{anomaly}(i) = -\,\text{IsolationForest.score}(x_i), \qquad \text{cluster}(i) = \arg\min_k \lVert x_i - \mu_k \rVert^2"
          caption="Isolation Forest ranks meters by how isolated their features are; K-means groups normalised load shapes. Liu, Ting & Zhou, ICDM 2008."
        />
      }
    >
      <TheftSegmentsView />
    </PageShell>
  );
}
