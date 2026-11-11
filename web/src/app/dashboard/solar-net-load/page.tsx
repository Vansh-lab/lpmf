import { EquationBlock } from "@/components/EquationBlock";
import { PageShell } from "@/components/dashboard/PageShell";
import { SolarView } from "./SolarView";

export default function SolarNetLoadPage() {
  return (
    <PageShell
      title="09 · Solar & Net Load"
      equation={
        <EquationBlock
          latex="P_{solar}(t) = \frac{GHI(t)}{1000}\cdot C_{kWp}\cdot PR, \qquad P_{net} = P_{load} - P_{solar}"
          caption="Rooftop solar output from real Open-Meteo irradiance and a capacity figure, then net load. Kothari & Nagrath, Modern Power System Analysis, Ch. 5."
        />
      }
    >
      <SolarView />
    </PageShell>
  );
}
