.PHONY: install dev-web dev-api dev-ml-shell test-web test-api test-ml lint-web lint-api lint-ml

install:
	cd web && npm install
	cd api && python -m venv .venv && .venv/Scripts/python -m pip install -e ".[dev]" || .venv/bin/python -m pip install -e ".[dev]"
	cd ml && python -m venv .venv && .venv/Scripts/python -m pip install -e ".[dev]" || .venv/bin/python -m pip install -e ".[dev]"

dev-web:
	cd web && npm run dev

dev-api:
	cd api && (.venv/Scripts/uvicorn app.main:app --reload --port 8000 || .venv/bin/uvicorn app.main:app --reload --port 8000)

test-web:
	cd web && npm test

test-api:
	cd api && (.venv/Scripts/python -m pytest || .venv/bin/python -m pytest)

test-ml:
	cd ml && (../ml/.venv/Scripts/python -m pytest || ../ml/.venv/bin/python -m pytest)

lint-web:
	cd web && npm run lint

lint-api:
	cd api && (.venv/Scripts/python -m ruff check app tests && .venv/Scripts/python -m black --check app tests)

lint-ml:
	cd ml && (.venv/Scripts/python -m ruff check src tests && .venv/Scripts/python -m black --check src tests)
