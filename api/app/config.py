"""Application settings, loaded from the environment (see .env.example)."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "LPMF API"
    environment: str = "development"

    # Comma-separated list of allowed CORS origins. Defaults to the Next.js
    # dev server.
    cors_origins: str = "http://localhost:3000"

    database_url: str = "sqlite:///../web/prisma/dev.db"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
