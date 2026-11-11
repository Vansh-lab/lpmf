import { EquationBlock } from "@/components/EquationBlock";
import { PageShell } from "@/components/dashboard/PageShell";
import { IexPriceView } from "./IexPriceView";

export default function IexPricePage() {
  return (
    <PageShell
      title="07 · IEX Price"
      equation={
        <EquationBlock
          latex="\text{cost} = \sum_{t} P_{load}(t)\cdot 0.25\,\text{h}\cdot \text{price}(t)"
          caption="Power-purchase cost: 15-min load x price, summed over the day. Price is the real historical IEX DAM block-of-day average (2018-2024) when built, else an illustrative curve bounded by EAC-PM WP 53/2026 — see the page note."
        />
      }
    >
      <IexPriceView />
    </PageShell>
  );
}
