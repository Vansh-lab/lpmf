# Demo-day runbook

Read this once before the viva, and keep it open on a second screen during the demo.

## 1. Before you even open a terminal

- **Free up port 3000.** `next dev` silently falls back to 3001/3002/... if
  port 3000 is already taken (e.g. a dev server left running from a
  previous session). If that happens, **Google sign-in will fail**
  (`redirect_uri_mismatch` — see §4) because the registered OAuth redirect
  URI is hardcoded to port 3000.
  - Windows: open Task Manager → search `node.exe` → if one is running and
    you don't recognise it, end it. Or in PowerShell:
    ```powershell
    Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
    ```
    If that prints a process, note its `OwningProcess` id and
    `Stop-Process -Id <id> -Force`.
- **Charge the laptop and have the charger plugged in.** Don't rely on battery.
- **Have a backup internet connection ready** (phone hotspot) in case the
  room Wi-Fi drops — the forecast/API pages are all local (`localhost`), so
  the app itself doesn't need internet, but Google sign-in does.

## 2. Starting the app (exact commands)

Open two terminals in the repo root (`C:\SEC PROJECT\lpmf`).

**Terminal 1 — API:**
```bash
cd api
.venv/Scripts/python -m uvicorn app.main:app --port 8000
```
Wait for `Uvicorn running on http://127.0.0.1:8000`. Verify it's alive:
```bash
curl http://localhost:8000/health
```
should print `{"status":"ok","environment":"development"}`.

**Terminal 2 — Web:**
```bash
cd web
npm run dev
```
Wait for `✓ Ready` and confirm it says `Local: http://localhost:3000` (not
3001/3002 — if it says a different port, go back to §1 and free port 3000,
then restart `npm run dev`).

Open **http://localhost:3000** in a normal (non-incognito) browser window.

## 3. Logging in

Two options are wired up:

- **Google sign-in** ("Continue with Google") — works once the redirect URI
  is registered correctly in Google Cloud Console (see §4 if it errors).
- **Email sign-in code** — type an email, click "Send sign-in code". This
  needs a working Gmail App Password in `web/.env`
  (`SMTP_USER` / `SMTP_APP_PASSWORD`); if that's not set, it fails with
  "Could not send the code" (a clean error, not a crash) — just use Google
  sign-in instead.

**Recommendation: sign in once, well before the demo starts**, and don't
sign out. The session cookie lasts across page reloads, so you only need to
log in once per browser session.

## 4. If Google sign-in shows "Error 400: redirect_uri_mismatch"

This means the OAuth client's **Authorized redirect URIs** in Google Cloud
Console don't include the URL this app is actually running on.

1. Go to https://console.cloud.google.com/apis/credentials
2. Open the OAuth 2.0 Client used for `GOOGLE_CLIENT_ID` in `web/.env`.
3. Under **Authorized redirect URIs**, make sure this exact entry exists:
   `http://localhost:3000/api/auth/callback/google`
4. Save. Changes can take a few minutes to propagate.
5. Make sure the app is actually running on port 3000 (§1) — the redirect
   URI must match the port exactly, `127.0.0.1` and `localhost` are treated
   as different origins by Google.

If you can't fix this before the demo, **use email sign-in** instead (§3),
or sign in once ahead of time on the browser/laptop you'll actually demo
with and don't sign out.

## 5. If a page crashes or shows an error during the demo

- **"API not reachable"** banner → Terminal 1 (API) probably died or isn't
  started. Check Terminal 1 for a stack trace; restart with the command in
  §2. Click the page's "Retry" button once it's back up.
- **A single dashboard page is blank/stuck "Computing…"** → this is almost
  always a first-visit compile delay in dev mode (Next.js compiles each
  route on first request). Wait 10–15 seconds and it resolves. If it's
  genuinely stuck after 30s, refresh the page (F5).
- **Any other crash** → don't panic, don't try to debug live. Switch to the
  presentation deck (`docs/LPMF_Project_Presentation.pptx`) and use the
  backup screenshots in `docs/demo_backup_screenshots/` (one per dashboard
  page, numbered 01–12) to walk through the pages verbally instead.
- **Whole laptop/app frozen** → close and reopen both terminals, re-run §2.
  The dev database (`web/prisma/dev.db`) and all data files are untouched
  by a restart — nothing is lost.

## 6. Known, already-labelled limitations (don't be caught off guard)

These are intentional and explained on the pages themselves — mentioned
here so you don't get flustered if an examiner points at one:

- DSM ₹ Calculator, Transformer Health, ToD Bill Simulator's load profile,
  and Losses & PF's PF/current inputs are **illustrative what-ifs**, not
  real metered readings — each page says so explicitly.
- Theft & Segments' demo meter fleet is **synthetic**; only the underlying
  SGCC benchmark the model is trained on is real.
- Solar Plant 2's daytime r² (0.21) is genuinely weak — the page explains
  the four hypotheses investigated and why it's a data limitation, not a
  bug.
