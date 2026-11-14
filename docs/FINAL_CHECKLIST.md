# Final submission checklist

Last verified: 2026-11-14, branch `master`, commit `bed7171` (tag `v1.0-final`).

## Automated — done ✅

- ✅ **API fresh start** — `uvicorn app.main:app --port 8000` comes up clean, `/health` returns `{"status":"ok"}`.
- ✅ **Web fresh start** — `npm run dev` on a cleared `.next` cache binds cleanly to port 3000, no stale-cache issues.
- ✅ **Google OAuth login** — full flow verified live in-browser: redirect → account chooser → password → callback → `/dashboard/overview`. Fixed after a Google Cloud Console redirect-URI update.
- ✅ **Email-OTP login** — full flow verified live in-browser: code sent via Gmail SMTP, entered, verified, redirected to `/dashboard/overview`.
- ✅ **All 12 dashboard pages load with no console/network errors** (fresh session, post-login): Overview, Load Analytics, Weather Impact, Forecast, DSM Calculator, Transformer Health, IEX Price, ToD Bill, Solar & Net Load, Losses & PF, Theft & Segments, Data & Model Card.
- ✅ **Stale doc bug fixed** — Data & Model Card's "Known limitations" no longer claims pages 07–11 are unbuilt (they are, and were just verified working).
- ✅ **Model backup for pen drive** — `docs/MODEL_BACKUP_FOR_PENDRIVE.zip` (model file + SHA256 + README), ready to copy off the laptop.
- ✅ **Tests** — 243/243 passing (47 API + 196 ML).
- ✅ **Lint** — `npm run lint` clean.
- ✅ **Build** — `npm run build` succeeds (only pre-existing, unrelated next-auth/jose Edge Runtime warnings).
- ✅ **`docs/SUBMISSION/`** — all 5 files (report docx+pdf, pptx, script docx+pdf) confirmed byte-identical to their latest source files; no stale copies.
- ✅ **Repo hygiene** — no secrets committed (`.env`/`dev.db` never tracked), `.env.example` accurate, no oversized files added to git, 4 stale backup decks previously untracked.
- ✅ **Git tag `v1.0-final`** — annotated tag on commit `fa41dc8`, pushed to `origin`.

## Manual only — you must do these ⬜

- ⬜ **Sign the physical certificate** (supervisor/department form).
- ⬜ **Copy `docs/MODEL_BACKUP_FOR_PENDRIVE.zip` onto a pen drive.**
- ⬜ **Do one full live demo run-through before the viva** — both logins + a few dashboard pages, on the actual laptop you'll present with.
- ⬜ **Charge the laptop fully and bring the charger.**
- ⬜ **Have a backup internet connection ready** (phone hotspot) — Google sign-in needs internet even though the rest of the app is local.
- ⬜ **Free port 3000 before starting** — check for/kill any stale `node.exe` left over from a previous session (see `docs/README_DEMO.md` §1).
- ⬜ **Re-verify Google sign-in on the exact laptop/browser profile you'll demo with** — the redirect-URI fix was tested here, but Google sometimes shows a one-time account "change password" prompt on first use of a new OAuth consent, which only you can clear.
