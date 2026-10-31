"use client";

import clsx from "clsx";
import { motion } from "framer-motion";
import { useTilt } from "@/lib/useTilt";

/**
 * Wraps children in a barely-perceptible spring-damped 3D tilt that
 * follows the mouse (disabled under prefers-reduced-motion — see useTilt).
 */
export function TiltPanel({
  children,
  className,
  style,
}: {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}) {
  const { ref, rotateX, rotateY, onMouseMove, onMouseLeave } = useTilt();

  return (
    <motion.div
      ref={ref}
      onMouseMove={onMouseMove}
      onMouseLeave={onMouseLeave}
      style={{ ...style, rotateX, rotateY, transformPerspective: 1000 }}
      className={clsx("will-change-transform", className)}
    >
      {children}
    </motion.div>
  );
}
