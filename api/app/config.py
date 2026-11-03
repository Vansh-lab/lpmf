"""Application settings, loaded from the environment (see .env.example)."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "LPMF API"
    environment: str = "development"

    # Comma-separated list of allowed CORS origins. Defaults to the Next.js
    # dev server.
    cors_origins: str = "http://localhost:3000"

    database_url: str = "sqlite:///../web/prisma/dev.db"

    # Monorepo root holding data/ and models/ (the ML pipeline's outputs).
    repo_root: Path = Path(__file__).resolve().parents[2]

    # Overview alert threshold: Delhi's all-time peak demand, 8,748 MW on
    # 29 Jun 2026 (Delhi SLDC). Tomorrow's forecast above it is a new record.
    overview_alert_limit_mw: float = 8748.0

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
