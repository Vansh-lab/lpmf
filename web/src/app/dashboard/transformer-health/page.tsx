import { EquationBlock } from "@/components/EquationBlock";
import { PageShell } from "@/components/dashboard/PageShell";
import { TransformerView } from "./TransformerView";

export default function TransformerHealthPage() {
  return (
    <PageShell
      title="06 · Transformer Health"
      equation={
        <EquationBlock
          latex="V = 2^{(\theta_h - 98)/6}, \qquad L = \sum_n V_n\,\Delta t"
          caption="IEC 60076-7 relative ageing rate from the winding hot-spot temperature, and the insulation life used."
        />
      }
    >
      <TransformerView />
    </PageShell>
  );
}
