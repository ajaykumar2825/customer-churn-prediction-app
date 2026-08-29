"""Application settings, read from environment variables with sane defaults.

Never commit secrets here â€” the production deployment must provide
``SECRET_KEY``, ``DATABASE_URL`` and ``REDIS_URL``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """All environment-driven knobs for the API service."""

    # --- general ----------------------------------------------------------------
    app_name: str = "Churn Intelligence API"
    api_prefix: str = "/api/v1"
    debug: bool = False
    environment: str = "development"

    # --- security ---------------------------------------------------------------
    secret_key: str = "dev-only-not-for-production"
    api_key: str | None = None
    allowed_origins: str = "*"
    cors_allow_credentials: bool = True

    # --- infra -------------------------------------------------------------------
    database_url: str = ""
    redis_url: str = ""
    cache_ttl_seconds: int = 300

    # --- model artifacts ----------------------------------------------------------
    model_dir: Path = REPO_ROOT / "models"
    precomputed_dir: Path = REPO_ROOT / "data" / "precomputed"

    # --- feature / prediction policy ----------------------------------------------
    default_threshold: float = 0.5
    high_risk_threshold: float = 0.7
    min_batch_size: int = 1
    max_batch_size: int = 10_000

    # --- rate limiting --------------------------------------------------------------
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60

    # --- seeding --------------------------------------------------------------------
    seed_on_startup: bool = True

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env", str(REPO_ROOT / ".env")),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}

    @property
    def use_postgres(self) -> bool:
        return self.database_url.startswith("postgresql")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
