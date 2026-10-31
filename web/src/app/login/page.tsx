import { Suspense } from "react";
import { LoadCurveArt } from "./LoadCurveArt";
import { LoginForm } from "./LoginForm";
import { TiltPanel } from "@/components/TiltPanel";

export default function LoginPage() {
  return (
    <div className="flex min-h-screen flex-col bg-[var(--lpmf-recessed)] md:flex-row">
      {/* Left: dark instrument panel with live animated load-curve artwork */}
      <div className="relative flex min-h-[220px] flex-1 flex-col justify-between overflow-hidden bg-[#0c0e11] p-8 text-white md:min-h-screen md:p-12">
        <div>
          <div className="text-sm font-semibold tracking-wide text-white/70">LPMF</div>
          <div className="text-xs text-white/40">Load Profile Management &amp; Forecasting</div>
        </div>

        <TiltPanel className="my-6 flex-1 [perspective:1000px]">
          <LoadCurveArt />
        </TiltPanel>

        <div className="lpmf-mono flex items-center gap-4 text-xs text-white/50">
          <span className="flex items-center gap-1.5">
            <span className="inline-block size-2 rounded-full bg-[#8b929b]" /> Gross load
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block size-2 rounded-full bg-[color:var(--lpmf-amber)]" /> Net
            load after solar
          </span>
        </div>
      </div>

      {/* Right: form panel, elevated off the recessed frame with real depth */}
      <div className="flex flex-1 items-center justify-center bg-[var(--lpmf-base)] p-8 md:p-12">
        <TiltPanel
          className="w-full max-w-sm rounded-xl border border-[color:var(--border-subtle)] bg-[color:var(--surface)] p-8 [perspective:1000px]"
          style={{ boxShadow: "var(--lpmf-shadow-card)" }}
        >
          <Suspense fallback={null}>
            <LoginForm />
          </Suspense>
        </TiltPanel>
      </div>
    </div>
  );
}
