import { EquationBlock } from "@/components/EquationBlock";
import { PageShell } from "@/components/dashboard/PageShell";
import { LossesView } from "./LossesView";

export default function LossesPfPage() {
  return (
    <PageShell
      title="10 · Losses & PF"
      equation={
        <EquationBlock
          latex="Q_c = P(\tan\varphi_1 - \tan\varphi_2), \qquad P_{loss} = 3 I^2 R"
          caption="Capacitor kVAR to raise power factor from φ1 to φ2, and three-phase I²R feeder loss. V.K. Mehta, Principles of Power System, Ch. 6."
        />
      }
    >
      <LossesView />
    </PageShell>
  );
}
