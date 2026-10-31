"use client";

import { useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";

/**
 * Live, animated left-panel artwork: a day-shaped demand curve (grey) plus
 * an amber "net load after solar" curve with a midday dip. Draws itself in
 * on mount, then settles into a slow ambient "current flowing" glow along
 * the amber curve, with a couple of pulsing data-point markers. All of it
 * is inert data for decoration — not a real chart, so it is intentionally
 * never wired to a SourceBadge.
 */
const W = 960;
const H = 320;
const MAX_VALUE = 320;

const GROSS_LOAD = [
  190, 175, 165, 160, 162, 175, 205, 240, 262, 270, 268, 260, 255, 258, 262, 268, 278, 292, 300,
  295, 278, 250, 225, 205, 190,
];
const NET_LOAD = [
  190, 175, 165, 160, 162, 175, 205, 232, 220, 190, 150, 118, 100, 95, 102, 130, 175, 240, 300, 295,
  278, 250, 225, 205, 190,
];

function points(values: number[]) {
  const step = W / (values.length - 1);
  return values.map((v, i) => ({ x: i * step, y: H - (v / MAX_VALUE) * H }));
}

function toPath(pts: { x: number; y: number }[]) {
  return pts.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(" ");
}

const grossPoints = points(GROSS_LOAD);
const netPoints = points(NET_LOAD);

const MARKERS = [
  { index: 12, label: "Solar dip", value: `${NET_LOAD[12]} MW` },
  { index: 18, label: "Evening peak", value: `${NET_LOAD[18]} MW` },
  { index: 7, label: "Morning ramp", value: `${NET_LOAD[7]} MW` },
];

export function LoadCurveArt() {
  const prefersReducedMotion = useReducedMotion();
  const [hovered, setHovered] = useState<number | null>(null);

  const drawTransition = prefersReducedMotion
    ? { duration: 0 }
    : { duration: 1.8, ease: [0.16, 1, 0.3, 1] as const };

  return (
    <div className="relative h-full w-full">
      <svg
        viewBox={`0 0 ${W} ${H}`}
        className="h-full w-full overflow-visible"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden="true"
      >
        <defs>
          <filter id="lpmf-glow-blur" x="-100%" y="-100%" width="300%" height="300%">
            <feGaussianBlur stdDeviation="8" />
          </filter>
        </defs>

        {/* Baseline grid */}
        {[0, 1, 2, 3].map((i) => (
          <line
            key={i}
            x1="0"
            x2={W}
            y1={(H / 3) * i}
            y2={(H / 3) * i}
            stroke="currentColor"
            strokeOpacity="0.06"
            strokeWidth="1"
            className="text-white"
          />
        ))}

        {/* Gross load (grey), draws in on mount */}
        <motion.path
          d={toPath(grossPoints)}
          stroke="#8b929b"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={drawTransition}
        />

        {/* Net load after solar (amber), draws in slightly after */}
        <motion.path
          d={toPath(netPoints)}
          stroke="var(--lpmf-amber)"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={prefersReducedMotion ? { duration: 0 } : { ...drawTransition, delay: 0.25 }}
        />

        {/* Ambient "current flowing" glow travelling along the amber curve */}
        {!prefersReducedMotion && (
          <motion.circle
            r="7"
            fill="var(--lpmf-amber)"
            filter="url(#lpmf-glow-blur)"
            opacity={0.55}
            initial={{ cx: netPoints[0].x, cy: netPoints[0].y, opacity: 0 }}
            animate={{
              cx: netPoints.map((p) => p.x),
              cy: netPoints.map((p) => p.y),
              opacity: 0.55,
            }}
            transition={{
              cx: { duration: 6, repeat: Infinity, ease: "linear", delay: 2 },
              cy: { duration: 6, repeat: Infinity, ease: "linear", delay: 2 },
              opacity: { duration: 1, delay: 2 },
            }}
          />
        )}

        {/* Data-point markers: pulse softly, show a tooltip on hover */}
        {MARKERS.map((m, i) => {
          const p = netPoints[m.index];
          return (
            <g key={m.index}>
              {!prefersReducedMotion && (
                <motion.circle
                  cx={p.x}
                  cy={p.y}
                  r="10"
                  fill="var(--lpmf-amber)"
                  opacity={0.18}
                  animate={{ scale: [1, 1.6, 1], opacity: [0.18, 0.02, 0.18] }}
                  transition={{
                    duration: 2.6,
                    repeat: Infinity,
                    ease: "easeInOut",
                    delay: 2 + i * 0.5,
                  }}
                  style={{ transformOrigin: `${p.x}px ${p.y}px` }}
                />
              )}
              <circle
                cx={p.x}
                cy={p.y}
                r="4"
                fill="var(--lpmf-amber)"
                stroke="#0c0e11"
                strokeWidth="1.5"
                className="cursor-default"
                style={{ pointerEvents: "all" }}
                onMouseEnter={() => setHovered(i)}
                onMouseLeave={() => setHovered(null)}
              />
            </g>
          );
        })}
      </svg>

      {/* HTML tooltip overlay, positioned from the same data coordinates */}
      <AnimatePresence>
        {hovered !== null && (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 4 }}
            transition={{ duration: 0.15 }}
            className="pointer-events-none absolute z-10 -translate-x-1/2 -translate-y-full rounded-md border border-white/10 bg-[#0c0e11] px-2.5 py-1.5 text-xs shadow-lg"
            style={{
              left: `${(netPoints[MARKERS[hovered].index].x / W) * 100}%`,
              top: `${(netPoints[MARKERS[hovered].index].y / H) * 100}%`,
              marginTop: "-10px",
            }}
          >
            <div className="font-medium text-white">{MARKERS[hovered].label}</div>
            <div className="lpmf-mono text-[color:var(--lpmf-amber)]">{MARKERS[hovered].value}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
