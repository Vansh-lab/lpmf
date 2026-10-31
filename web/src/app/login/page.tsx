import { Suspense } from "react";
import { LoadCurveArt } from "./LoadCurveArt";
import { LoginForm } from "./LoginForm";

export default function LoginPage() {
  return (
    <div className="flex min-h-screen flex-col md:flex-row">
      {/* Left: dark panel with animated load-curve artwork */}
      <div className="relative flex min-h-[220px] flex-1 flex-col justify-between overflow-hidden bg-[color:var(--lpmf-graphite)] p-8 text-white md:min-h-screen md:p-12">
        <div>
          <div className="text-sm font-semibold tracking-wide text-white/70">LPMF</div>
          <div className="text-xs text-white/40">Load Profile Management &amp; Forecasting</div>
        </div>

        <div className="my-6 flex-1">
          <LoadCurveArt />
        </div>

        <div className="flex items-center gap-4 text-xs text-white/50">
          <span className="flex items-center gap-1.5">
            <span className="inline-block size-2 rounded-full bg-[#8b929b]" /> Gross load
          </span>
          <span className="flex items-center gap-1.5">
            <span className="inline-block size-2 rounded-full bg-[color:var(--lpmf-amber)]" /> Net
            load after solar
          </span>
        </div>
      </div>

      {/* Right: white panel with the sign-in form */}
      <div className="flex flex-1 items-center justify-center bg-white p-8 md:p-12">
        <Suspense fallback={null}>
          <LoginForm />
        </Suspense>
      </div>
    </div>
  );
}
