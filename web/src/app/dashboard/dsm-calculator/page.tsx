import { PlaceholderPage } from "@/components/PlaceholderPage";

export default function DsmCalculatorPage() {
  return (
    <PlaceholderPage
      title="05 · DSM ₹ Calculator"
      equation="\mathrm{DSM} = \sum_{i} (A_i - S_i) \times R_i"
      equationCaption="DSM charge: sum of (actual − scheduled) deviation × applicable rate, per block."
      chartLabel="DSM deviation & charge"
    />
  );
}
