import { EquationBlock } from "@/components/EquationBlock";
import { PageShell } from "@/components/dashboard/PageShell";
import { WeatherView } from "./WeatherView";

export default function WeatherImpactPage() {
  return (
    <PageShell
      title="03 · Weather Impact"
      equation={
        <EquationBlock
          latex="P = \alpha + \beta \cdot HI, \qquad HI = f(T, RH)"
          caption="Ordinary least squares of load on heat index over every 15-min block."
        />
      }
    >
      <WeatherView />
    </PageShell>
  );
}
