"""Central configuration.

All runtime configuration flows through this module so that invalid
configuration fails loudly at process start instead of at request time.
"""

from __future__ import annotations

import sys
from functools import lru_cache
from typing import Literal
from urllib.parse import quote_plus

from cryptography.fernet import Fernet
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE_CANDIDATES = (".env", "../.env")


class Settings(BaseSettings):
    """Validated application settings (loaded from environment / .env)."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE_CANDIDATES,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Core ---------------------------------------------------------
    environment: Literal["development", "production", "test"] = "development"
    log_level: str = "INFO"
    api_name: str = "nexusops"

    # --- Database -----------------------------------------------------
    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5433
    postgres_db: str = "nexusops"
    postgres_user: str = "nexusops"
    postgres_password: str = "change-me-postgres"  # noqa: S105 - dev fallback, override via env
    database_url: str | None = None
    db_pool_size: int = Field(default=10, ge=1, le=100)
    db_max_overflow: int = Field(default=20, ge=0, le=200)
    db_echo: bool = False

    # --- Redis --------------------------------------------------------
    redis_url: str = "redis://127.0.0.1:6390/0"

    # --- Security ------------------------------------------------------
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = Field(default=15, ge=1, le=1440)
    refresh_token_ttl_days: int = Field(default=14, ge=1, le=180)
    encryption_key: str
    cors_origins: str = "http://localhost:8080,http://localhost:5173"
    login_max_attempts: int = Field(default=5, ge=1, le=50)
    login_lockout_seconds: int = Field(default=900, ge=10)
    session_idle_timeout_days: int = Field(default=30, ge=1)

    # --- Simulation mode ----------------------------------------------
    simulation_mode: bool = False

    # --- Heartbeats & scheduling ---------------------------------------
    server_offline_after_seconds: int = Field(default=90, ge=30)
    monitor_dispatch_interval_seconds: int = Field(default=10, ge=5)
    metrics_aggregation_interval_seconds: int = Field(default=60, ge=10)
    raw_metric_retention_hours: int = Field(default=24, ge=1)
    hourly_metric_retention_days: int = Field(default=30, ge=1)

    # --- SMTP -----------------------------------------------------------
    smtp_host: str = "127.0.0.1"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "nexusops@example.com"
    smtp_tls: bool = False

    # --- Network guards --------------------------------------------------
    allow_private_targets: bool = True

    # --- HTTP server ------------------------------------------------------
    api_host: str = "0.0.0.0"  # noqa: S104 - container binding is intentional
    api_port: int = 8000
    api_workers: int = 2

    # --- Derived flags ----------------------------------------------------
    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_testing(self) -> bool:
        return self.environment == "test"

    @property
    def cookies_secure(self) -> bool:
        """Secure flag for auth cookies (browsers refuse Secure cookies over http)."""
        return self.is_production

    @property
    def access_token_ttl(self) -> int:
        return self.access_token_ttl_minutes * 60

    @property
    def refresh_token_ttl(self) -> int:
        return self.refresh_token_ttl_days * 86400

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.cors_origins.split(",") if o.strip()]

    @field_validator("cors_origins")
    @classmethod
    def _validate_cors(cls, v: str) -> str:
        origins = [o.strip().rstrip("/") for o in v.split(",") if o.strip()]
        if not origins:
            raise ValueError("CORS_ORIGINS must contain at least one origin")
        return ",".join(origins)

    @field_validator("jwt_secret")
    @classmethod
    def _validate_jwt_secret(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(
                "JWT_SECRET must be at least 32 characters. Generate one with: openssl rand -hex 32"
            )
        return v

    @field_validator("encryption_key")
    @classmethod
    def _validate_encryption_key(cls, v: str) -> str:
        try:
            Fernet(v.encode())
        except Exception as exc:
            raise ValueError(
                "ENCRYPTION_KEY must be a valid Fernet key. "
                "Generate one with: python -c 'from cryptography.fernet import Fernet;"
                " print(Fernet.generate_key().decode())'"
            ) from exc
        return v

    @field_validator("log_level")
    @classmethod
    def _validate_log_level(cls, v: str) -> str:
        allowed = {"TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"LOG_LEVEL must be one of {sorted(allowed)}")
        return upper

    @model_validator(mode="after")
    def _assemble_database_url(self) -> Settings:
        if not self.database_url:
            pwd = quote_plus(self.postgres_password)
            self.database_url = (
                f"postgresql+psycopg://{quote_plus(self.postgres_user)}:{pwd}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        if not self.database_url.startswith(("postgresql+psycopg://", "postgresql://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached settings singleton."""
    return Settings()  # type: ignore[call-arg]


def fail_on_bad_config() -> None:
    """Exit immediately with a readable message if configuration is invalid."""
    try:
        get_settings()
    except Exception as exc:
        # pydantic ValidationError and friends; print a short, actionable message.
        lines = str(exc).splitlines()
        interesting = "\n".join(lines[:25])
        print(
            f"\n[nexusops] Invalid configuration:\n{interesting}\n"
            "Fix the variables above (see .env.example), then restart.\n",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc
