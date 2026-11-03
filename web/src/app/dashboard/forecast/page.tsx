import { EquationBlock } from "@/components/EquationBlock";
import { PageShell } from "@/components/dashboard/PageShell";
import { ForecastView } from "./ForecastView";

export default function ForecastPage() {
  return (
    <PageShell
      title="04 · Forecast"
      equation={
        <EquationBlock
          latex="\hat{L}_{t+h} \pm q_{1-\alpha}"
          caption="Day-ahead point forecast with its split-conformal P10–P90 interval (1−α = 80%)."
        />
      }
    >
      <ForecastView />
    </PageShell>
  );
}
