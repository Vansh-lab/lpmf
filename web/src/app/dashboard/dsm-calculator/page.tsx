import { EquationBlock } from "@/components/EquationBlock";
import { PageShell } from "@/components/dashboard/PageShell";
import { DsmView } from "./DsmView";

export default function DsmCalculatorPage() {
  return (
    <PageShell
      title="05 · DSM ₹ Calculator"
      equation={
        <EquationBlock
          latex="C_b = \min(|D_b|, V_L)\,\frac{NR}{4} + \max(|D_b| - V_L,\, 0)\,\frac{k \cdot NR}{4}"
          caption="Deviation charge per 15-min block: within the volume limit at the normal rate, the excess at k times it."
        />
      }
    >
      <DsmView />
    </PageShell>
  );
}
