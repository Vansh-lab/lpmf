import { EquationBlock } from "@/components/EquationBlock";
import { PageShell } from "@/components/dashboard/PageShell";
import { TodBillView } from "./TodBillView";

export default function TodBillPage() {
  return (
    <PageShell
      title="08 · ToD Bill Simulator"
      equation={
        <EquationBlock
          latex="\text{bill} = \sum_{h=0}^{23} \text{kWh}(h)\cdot\text{rate}\cdot m(h), \quad m(h)=\begin{cases}1+s & \text{peak}\\ 1-r & \text{off-peak}\\ 1 & \text{otherwise}\end{cases}"
          caption="Flat vs Time-of-Day bill: s = peak surcharge, r = off-peak rebate (DERC FY 2025-26 order). Electricity (Rights of Consumers) Amendment Rules, 2023."
        />
      }
    >
      <TodBillView />
    </PageShell>
  );
}
