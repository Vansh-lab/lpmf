import { EquationBlock } from "@/components/EquationBlock";
import { PageShell } from "@/components/dashboard/PageShell";
import { OverviewView } from "./OverviewView";

export default function OverviewPage() {
  return (
    <PageShell
      title="01 · Overview"
      equation={
        <EquationBlock
          latex="\hat{P}_{peak} = \max_{t}\,\hat{P}(t), \qquad \text{alert if } \hat{P}_{peak} > P_{limit}"
          caption="The day-ahead forecast's peak, and an alert when it crosses the limit."
        />
      }
    >
      <OverviewView />
    </PageShell>
  );
}
