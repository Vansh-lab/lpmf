"use client";

import { useRef, useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter, useSearchParams } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";

type Step = "email" | "code";

const OTP_LENGTH = 6;

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") || "/dashboard";

  const [step, setStep] = useState<Step>("email");
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [otpResetKey, setOtpResetKey] = useState(0);

  async function handleSendCode(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch("/api/auth/otp/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Could not send the code.");
        return;
      }
      setStep("code");
    } catch {
      setError("Network error. Try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleVerifyCode(code: string) {
    setError(null);
    setLoading(true);
    try {
      const res = await fetch("/api/auth/otp/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, code }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Incorrect or expired code.");
        setOtpResetKey((k) => k + 1);
        return;
      }
      router.push(callbackUrl);
      router.refresh();
    } catch {
      setError("Network error. Try again.");
      setOtpResetKey((k) => k + 1);
    } finally {
      setLoading(false);
    }
  }

  async function handleGoogleSignIn() {
    setGoogleLoading(true);
    await signIn("google", { callbackUrl });
  }

  return (
    <div className="w-full">
      <h1 className="text-xl font-semibold text-[color:var(--foreground)]">Sign in to LPMF</h1>
      <p className="mt-1 text-sm text-[color:var(--lpmf-muted)]">
        Load Profile Management &amp; Forecasting
      </p>

      <motion.button
        type="button"
        onClick={handleGoogleSignIn}
        disabled={googleLoading}
        whileTap={{ scale: 0.98 }}
        transition={{ type: "spring", stiffness: 400, damping: 25 }}
        style={{ boxShadow: "var(--lpmf-shadow-card)" }}
        className="mt-6 flex w-full items-center justify-center gap-2 rounded-md border border-[color:var(--border-subtle)] bg-[color:var(--surface)] px-4 py-2.5 text-sm font-medium text-[color:var(--foreground)] transition hover:brightness-105 disabled:opacity-60"
      >
        <GoogleIcon />
        {googleLoading ? "Redirecting…" : "Continue with Google"}
      </motion.button>

      <div className="my-6 flex items-center gap-3">
        <div className="h-px flex-1 bg-[color:var(--border-subtle)]" />
        <span className="text-xs uppercase tracking-wide text-[color:var(--lpmf-muted)]">or</span>
        <div className="h-px flex-1 bg-[color:var(--border-subtle)]" />
      </div>

      <AnimatePresence mode="wait" initial={false}>
        {step === "email" && (
          <motion.form
            key="email"
            onSubmit={handleSendCode}
            className="space-y-3"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
          >
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-[color:var(--foreground)]">
                Work email
              </span>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                className="w-full rounded-md border border-[color:var(--border-subtle)] bg-[color:var(--background)] px-3 py-2.5 text-sm text-[color:var(--foreground)] outline-none transition focus:border-[color:var(--lpmf-amber)] focus:shadow-[0_0_0_1px_rgba(227,155,22,0.35),0_0_14px_rgba(227,155,22,0.2)]"
              />
            </label>
            {error && <p className="text-sm text-[color:var(--lpmf-red)]">{error}</p>}
            <motion.button
              type="submit"
              disabled={loading}
              whileTap={{ scale: 0.98 }}
              transition={{ type: "spring", stiffness: 400, damping: 25 }}
              className="w-full rounded-md bg-[color:var(--lpmf-ink)] px-4 py-2.5 text-sm font-medium text-white transition hover:brightness-110 disabled:opacity-60"
            >
              {loading ? "Sending…" : "Send sign-in code"}
            </motion.button>
          </motion.form>
        )}

        {step === "code" && (
          <motion.div
            key="code"
            className="space-y-3"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
          >
            <p className="text-sm text-[color:var(--lpmf-muted)]">
              Enter the 6-digit code sent to <span className="font-medium">{email}</span>.
            </p>
            <OtpInput
              key={otpResetKey}
              length={OTP_LENGTH}
              onComplete={handleVerifyCode}
              disabled={loading}
            />
            {error && <p className="text-sm text-[color:var(--lpmf-red)]">{error}</p>}
            {loading && (
              <p className="text-center text-sm text-[color:var(--lpmf-muted)]">Verifying…</p>
            )}
            <button
              type="button"
              onClick={() => {
                setStep("email");
                setError(null);
              }}
              className="w-full text-center text-sm text-[color:var(--lpmf-muted)] underline-offset-2 hover:underline"
            >
              Use a different email
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function OtpInput({
  length,
  onComplete,
  disabled,
}: {
  length: number;
  onComplete: (code: string) => void;
  disabled?: boolean;
}) {
  const [digits, setDigits] = useState<string[]>(() => Array(length).fill(""));
  const [bounceIndex, setBounceIndex] = useState<number | null>(null);
  const inputsRef = useRef<(HTMLInputElement | null)[]>([]);

  function commitIfComplete(next: string[]) {
    if (next.every((d) => d !== "")) {
      onComplete(next.join(""));
    }
  }

  function setDigit(i: number, raw: string) {
    // Deliberately not a functional setState updater: React (Strict Mode
    // in particular) may invoke that updater more than once per event to
    // detect impure updaters, and calling .focus() as a side effect
    // inside it was double-advancing focus and dropping keystrokes. This
    // reads `digits` from the render closure instead, which is fine since
    // a fresh handler closure is created every render.
    const d = raw.replace(/\D/g, "").slice(-1);
    const next = [...digits];
    next[i] = d;
    setDigits(next);
    if (d) {
      setBounceIndex(i);
      if (i < length - 1) inputsRef.current[i + 1]?.focus();
    }
    commitIfComplete(next);
  }

  function handleKeyDown(i: number, e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Backspace" && !digits[i] && i > 0) {
      inputsRef.current[i - 1]?.focus();
    }
  }

  function handlePaste(e: React.ClipboardEvent<HTMLInputElement>) {
    const text = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, length);
    if (!text) return;
    e.preventDefault();
    const next = Array(length).fill("");
    for (let i = 0; i < text.length; i++) next[i] = text[i];
    setDigits(next);
    const lastIndex = Math.min(text.length, length) - 1;
    inputsRef.current[Math.max(lastIndex, 0)]?.focus();
    commitIfComplete(next);
  }

  return (
    <div className="flex justify-between gap-2">
      {digits.map((d, i) => (
        <motion.input
          key={i}
          ref={(el) => {
            inputsRef.current[i] = el;
          }}
          value={d}
          disabled={disabled}
          onChange={(e) => setDigit(i, e.target.value)}
          onKeyDown={(e) => handleKeyDown(i, e)}
          onPaste={handlePaste}
          animate={bounceIndex === i ? { scale: [1, 1.18, 1] } : { scale: 1 }}
          onAnimationComplete={() => setBounceIndex((cur) => (cur === i ? null : cur))}
          transition={{ duration: 0.22, ease: "easeOut" }}
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={1}
          className="lpmf-mono h-12 w-full rounded-md border border-[color:var(--border-subtle)] bg-[color:var(--background)] text-center text-lg text-[color:var(--foreground)] outline-none transition-[transform,box-shadow,border-color] focus:-translate-y-0.5 focus:border-[color:var(--lpmf-amber)] focus:shadow-[0_0_0_1px_rgba(227,155,22,0.4),0_0_16px_rgba(227,155,22,0.25)] disabled:opacity-60"
        />
      ))}
    </div>
  );
}

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden="true">
      <path
        fill="#FFC107"
        d="M43.6 20.5H42V20H24v8h11.3C33.7 32.9 29.3 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.6 6 29.6 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.7-.4-3.5z"
      />
      <path
        fill="#FF3D00"
        d="M6.3 14.7l6.6 4.8C14.5 15.9 18.9 13 24 13c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34.6 6 29.6 4 24 4c-7.7 0-14.4 4.4-17.7 10.7z"
      />
      <path
        fill="#4CAF50"
        d="M24 44c5.5 0 10.4-1.8 14.3-5l-6.6-5.6C29.6 35 26.9 36 24 36c-5.3 0-9.7-3.1-11.3-7.6l-6.6 5.1C9.5 39.6 16.2 44 24 44z"
      />
      <path
        fill="#1976D2"
        d="M43.6 20.5H42V20H24v8h11.3c-.8 2.3-2.3 4.3-4.3 5.7l6.6 5.6C41.9 36 44 30.5 44 24c0-1.3-.1-2.7-.4-3.5z"
      />
    </svg>
  );
}
