import { EquationBlock } from "@/components/EquationBlock";
import { PageShell } from "@/components/dashboard/PageShell";
import { DataModelCardView } from "./DataModelCardView";

export default function DataModelCardPage() {
  return (
    <PageShell
      title="12 · Data & Model Card"
      equation={
        <EquationBlock
          latex="\text{coverage} = \tfrac{1}{N}\sum_{i=1}^{N} \mathbf{1}[P_{10,i} \le y_i \le P_{90,i}]"
          caption="Band coverage: the share of test forecasts (every origin × horizon, N = 1,672,080) whose actual load y lands inside the P10–P90 band. P10–P90 is an 80% interval, so the target is 0.80."
        />
      }
    >
      <DataModelCardView />
    </PageShell>
  );
}
