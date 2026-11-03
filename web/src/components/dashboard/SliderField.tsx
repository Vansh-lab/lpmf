"use client";

import { useId } from "react";

/** A labelled range slider with a synced number box, for what-if inputs. */
export function SliderField({
  label,
  unit,
  min,
  max,
  step,
  value,
  onChange,
  hint,
}: {
  label: string;
  unit: string;
  min: number;
  max: number;
  step: number;
  value: number;
  onChange: (value: number) => void;
  hint?: string;
}) {
  const id = useId();
  const set = (raw: string) => {
    const n = Number(raw);
    if (raw !== "" && Number.isFinite(n)) onChange(Math.min(max, Math.max(min, n)));
  };

  return (
    <div>
      <div className="flex items-center justify-between gap-3">
        <label htmlFor={id} className="text-sm font-medium text-[color:var(--foreground)]">
          {label}
        </label>
        <span className="flex items-center gap-1.5">
          <input
            type="number"
            aria-label={`${label} (${unit})`}
            min={min}
            max={max}
            step={step}
            value={value}
            onChange={(e) => set(e.target.value)}
            className="lpmf-mono w-24 rounded-md border border-[color:var(--border-subtle)] bg-[color:var(--surface-sunken)] px-2 py-1 text-right text-sm text-[color:var(--foreground)]"
          />
          <span className="text-xs text-[color:var(--lpmf-muted)]">{unit}</span>
        </span>
      </div>
      <input
        id={id}
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => set(e.target.value)}
        className="mt-2 w-full accent-[color:var(--lpmf-amber)]"
      />
      <div className="lpmf-mono flex justify-between text-[10px] text-[color:var(--lpmf-muted)]">
        <span>{min}</span>
        <span>{max}</span>
      </div>
      {hint && <p className="mt-1 text-xs text-[color:var(--lpmf-muted)]">{hint}</p>}
    </div>
  );
}
