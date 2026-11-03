import { EquationBlock } from "@/components/EquationBlock";
import { PageShell } from "@/components/dashboard/PageShell";
import { LoadAnalyticsView } from "./LoadAnalyticsView";

export default function LoadAnalyticsPage() {
  return (
    <PageShell
      title="02 · Load Analytics"
      equation={
        <EquationBlock
          latex="LF = \frac{P_{avg}}{P_{max}}, \qquad PAR = \frac{1}{LF}"
          caption="Load factor and peak-to-average ratio: how peaky demand is."
        />
      }
    >
      <LoadAnalyticsView />
    </PageShell>
  );
}
