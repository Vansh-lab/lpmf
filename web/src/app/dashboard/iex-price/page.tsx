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
          caption="Power-purchase cost: 15-min load x price, summed over the day. IEX DAM/RTM market data (illustrative here — see the page note); EAC-PM WP 53/2026."
        />
      }
    >
      <IexPriceView />
    </PageShell>
  );
}
