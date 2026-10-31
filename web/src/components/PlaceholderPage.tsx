"use client";

import { motion } from "framer-motion";
import { EquationBlock } from "@/components/EquationBlock";
import { ChartSlotEmpty } from "@/components/ChartSlotEmpty";

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.04 } },
};

const item = {
  hidden: { opacity: 0, y: 8 },
  show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 300, damping: 30 } },
};

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
    <motion.div className="space-y-6 p-8" variants={container} initial="hidden" animate="show">
      <motion.h1 variants={item} className="text-lg font-semibold text-[color:var(--foreground)]">
        {title}
      </motion.h1>
      <motion.div variants={item}>
        <EquationBlock latex={equation} caption={equationCaption} />
      </motion.div>
      <motion.div variants={item}>
        <ChartSlotEmpty label={chartLabel} />
      </motion.div>
    </motion.div>
  );
}
