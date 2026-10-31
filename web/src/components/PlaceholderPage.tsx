import { EquationBlock } from "@/components/EquationBlock";
import { ChartSlotEmpty } from "@/components/ChartSlotEmpty";

export function PlaceholderPage({
  title,
  equation,
  equationCaption,
  chartLabel,
}: {
  title: string;
  equation: string;
  equationCaption?: string;
  chartLabel: string;
}) {
  return (
    <div className="space-y-6 p-8">
      <h1 className="text-lg font-semibold text-[color:var(--foreground)]">{title}</h1>
      <EquationBlock latex={equation} caption={equationCaption} />
      <ChartSlotEmpty label={chartLabel} />
    </div>
  );
}
