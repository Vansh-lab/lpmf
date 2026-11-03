"use client";

import { motion } from "framer-motion";

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.05 } },
};

export const rise = {
  hidden: { opacity: 0, y: 8 },
  show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 300, damping: 30 } },
};

/**
 * Dashboard page frame: title, the page's governing equation (rendered on the
 * server and passed in), then the page content, staggered in with a spring.
 */
export function PageShell({
  title,
  equation,
  children,
}: {
  title: string;
  equation: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <motion.div
      className="mx-auto max-w-6xl space-y-5 p-4 sm:p-6 lg:p-8"
      variants={container}
      initial="hidden"
      animate="show"
    >
      <motion.h1 variants={rise} className="text-lg font-semibold text-[color:var(--foreground)]">
        {title}
      </motion.h1>
      <motion.div variants={rise}>{equation}</motion.div>
      <motion.div variants={rise} className="space-y-5">
        {children}
      </motion.div>
    </motion.div>
  );
}
