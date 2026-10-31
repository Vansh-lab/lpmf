# LPMF — Load Profile Management & Forecasting

AI load-intelligence dashboard for the Delhi grid.

```
lpmf/
├── web/    Next.js 15 App Router + TypeScript + Tailwind — the dashboard
├── api/    FastAPI + SQLAlchemy-ready + Pydantic v2 — serving layer
├── ml/     Python package (src layout): ingest, clean, features, models, engines
├── data/   raw/ interim/ processed/ synthetic/   (gitignored, kept with .gitkeep)
└── docs/   PROVENANCE.md, DATA_QUALITY.md, ...
```

**Phase 0** scope (this commit): auth + app shell only. No charts, no ML
wired into the UI yet. See `docs/PROVENANCE.md` for the data-provenance
convention every later phase must follow.

## Prerequisites

- Node.js 20+ and npm
- Python 3.11+
- (optional, for `ml/`) a Kaggle account + API token, for the Delhi SLDC dataset

## Setup

### 1. Clone and configure environment

```bash
cp .env.example .env
```

Fill in `.env`:

- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — from
  https://console.cloud.google.com/apis/credentials (OAuth 2.0 Client ID,
  web application, redirect URI `http://localhost:3000/api/auth/callback/google`)
- `AUTH_SECRET` — generate with `openssl rand -base64 32`
- `DATABASE_URL` — leave as the SQLite default for local dev
- `SMTP_USER` / `SMTP_APP_PASSWORD` — a Gmail address and an
  [App Password](https://myaccount.google.com/apppasswords) for it (used to
  send the 6-digit OTP email)

### 2. Web app (Next.js + Auth.js + Prisma)

```bash
cd web
npm install
npx prisma migrate dev --name init   # creates prisma/dev.db (SQLite)
npm run dev                          # http://localhost:3000
```

To run against Postgres instead of SQLite, change only `DATABASE_URL` in
`.env` to a `postgresql://...` URL and `provider` in
`web/prisma/schema.prisma` from `sqlite` to `postgresql`, then re-run
`npx prisma migrate dev`.

### 3. API (FastAPI)

```bash
cd api
python -m venv .venv
.venv/Scripts/activate          # Windows; use `source .venv/bin/activate` on macOS/Linux
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000   # http://localhost:8000/health
```

### 4. ML package (ingest / clean / features / models / engines)

```bash
cd ml
python -m venv .venv
.venv/Scripts/activate
pip install -e ".[dev]"
pytest                            # unit tests (heat index, gap filling, schema)
```

To run the full data pipeline you also need the Kaggle CLI and the Delhi
SLDC dataset (see `ml/src/lpmf/ingest/sldc.py` for exact steps):

```bash
pip install kaggle
# place your token at ~/.kaggle/kaggle.json
kaggle datasets download -d prash4nt/delhi-sldc-load-data-5-min-resolution \
    -p data/raw/sldc --unzip

python -m lpmf.pipeline --step all
```

Outputs land in `data/processed/` (`delhi_15min.parquet`,
`delhi_hourly.parquet`, `splits.json`) and `docs/DATA_QUALITY.md`.

### Makefile shortcuts

```bash
make install    # installs web, api, ml dependencies
make dev-web    # npm run dev
make dev-api    # uvicorn --reload
```

## Tooling

- `web/`: ESLint + Prettier (`npm run lint`)
- `api/`, `ml/`: ruff + black + pytest (`ruff check .`, `black --check .`, `pytest`)

## Data provenance

Every chart and every number in this app is tagged `REAL`, `SYNTHETIC`,
`FOREIGN`, or `ILLUSTRATIVE` and renders a `<SourceBadge>`. See
`docs/PROVENANCE.md`. Placeholders in Phase 0 look empty, not fake — nothing
in this repo stubs fabricated data.
