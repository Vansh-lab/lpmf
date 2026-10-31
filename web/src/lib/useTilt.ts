"use client";

import { useRef } from "react";
import { useMotionValue, useReducedMotion, useSpring } from "framer-motion";

const MAX_TILT_DEG = 5;
const SPRING = { stiffness: 300, damping: 30 };

/**
 * Barely-perceptible 3D tilt-on-mouse-move for a panel, spring-damped.
 * Disabled entirely under prefers-reduced-motion. Attach `ref` to the
 * tilted element, spread the motion values into its `style`, and wire up
 * `onMouseMove` / `onMouseLeave`.
 */
export function useTilt() {
  const ref = useRef<HTMLDivElement>(null);
  const prefersReducedMotion = useReducedMotion();

  const rotateXRaw = useMotionValue(0);
  const rotateYRaw = useMotionValue(0);
  const rotateX = useSpring(rotateXRaw, SPRING);
  const rotateY = useSpring(rotateYRaw, SPRING);

  function onMouseMove(e: React.MouseEvent<HTMLDivElement>) {
    if (prefersReducedMotion || !ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const px = (e.clientX - rect.left) / rect.width;
    const py = (e.clientY - rect.top) / rect.height;
    rotateYRaw.set((px - 0.5) * 2 * MAX_TILT_DEG);
    rotateXRaw.set(-(py - 0.5) * 2 * MAX_TILT_DEG);
  }

  function onMouseLeave() {
    rotateXRaw.set(0);
    rotateYRaw.set(0);
  }

  return { ref, rotateX, rotateY, onMouseMove, onMouseLeave };
}
