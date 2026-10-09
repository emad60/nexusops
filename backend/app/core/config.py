"""Central configuration.

All runtime configuration flows through this module so that invalid
configuration fails loudly at process start instead of at request time.
"""

from __future__ import annotations

import sys
from functools import lru_cache
from typing import Literal
from urllib.parse import quote_plus, unquote_plus

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
    #: The **owner** role: it owns every table and is the only role that runs
    #: migrations. It bypasses RLS by virtue of ownership, which is exactly why
    #: it never serves request traffic.
    postgres_user: str = "nexusops_owner"
    postgres_password: str = "change-me-postgres"  # noqa: S105 - dev fallback, override via env
    #: The **application** role: the only role the API/workers connect as. It
    #: owns nothing, has no BYPASSRLS, and is filtered by the tenant policies.
    postgres_app_user: str = "nexusops_app"
    postgres_app_password: str | None = None
    #: Explicit DSN overrides. ``database_url`` is the runtime (application
    #: role) DSN; ``migration_database_url`` is used by Alembic and the container
    #: entrypoint (owner role). When unset both are assembled from POSTGRES_*.
    database_url: str | None = None
    migration_database_url: str | None = None
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
    # Replays of the *immediately* superseded refresh token inside this window
    # are rescued instead of treated as theft (see auth_service.refresh): a
    # browser navigation can abort an in-flight refresh after the server
    # committed the rotation, losing the response cookie. 0 disables the grace
    # path entirely.
    refresh_grace_seconds: int = Field(default=30, ge=0, le=3600)
    encryption_key: str
    cors_origins: str = "http://localhost:8080,http://localhost:5173"
    # Reverse proxies whose X-Forwarded-For entries are trusted when resolving
    # the real client address (see app/core/client_ip.py for the trust model).
    # Default: loopback + RFC1918 — the compose edge and docker gateway land
    # here without configuration.
    trusted_proxy_cidrs: str = "127.0.0.0/8,::1/128,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"
    login_max_attempts: int = Field(default=5, ge=1, le=50)
    login_lockout_seconds: int = Field(default=900, ge=10)
    session_idle_timeout_days: int = Field(default=30, ge=1)

    # --- Simulation mode ----------------------------------------------
    simulation_mode: bool = False

    # --- Heartbeats & scheduling ---------------------------------------
    server_offline_after_seconds: int = Field(default=90, ge=30)

    # --- Agent credential rotation & operation timing -------------------
    #: Dual-token grace after a rotation (docs/node-agent-architecture.md §3.3).
    #: The old token keeps authenticating for this long so a running agent can
    #: fetch its replacement on the next beat. 0 disables the grace entirely
    #: (immediate switch). Compromise response is *revoke*, not a long grace.
    agent_rotation_grace_seconds: int = Field(default=24 * 3600, ge=0, le=7 * 86400)
    #: How long a claimed operation may still report a result after its execution
    #: deadline, absorbing one slow heartbeat without letting a node act forever.
    agent_result_grace_seconds: int = Field(default=30, ge=0, le=3600)
    #: Floor for the operation *availability* window: the queue deadline is never
    #: shorter than this even for a fast-heartbeat node, which is what guarantees
    #: an operation created just after a beat survives until the next one.
    agent_delivery_min_seconds: int = Field(default=120, ge=10, le=86400)
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
    def rls_enforced(self) -> bool:
        """Whether the runtime connection is the RLS-enforced application role.

        False means the app is connected as the table owner, whose queries
        bypass row security entirely: the ORM guard still applies, but the
        database-level net is inert. Production refuses to start in that state
        (see :func:`fail_on_bad_config`); development logs a warning.

        The decision is made from the **user in the DSN**, not from the presence
        of ``POSTGRES_APP_PASSWORD``: an explicit ``DATABASE_URL`` naming the
        owner role would otherwise look enforced while every policy is inert —
        exactly the silent degradation this property exists to catch.
        """
        user = self.database_user
        return bool(user) and user != self.postgres_user

    @property
    def database_user(self) -> str | None:
        """Username from :attr:`database_url`, or ``None`` if it is unparseable."""
        if not self.database_url:
            return None
        _, _, remainder = self.database_url.partition("://")
        userinfo, sep, _ = remainder.partition("@")
        if not sep:  # no credentials embedded: libpq defaults apply (not our role)
            return None
        user = unquote_plus(userinfo.split(":", 1)[0])
        return user or None

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

    def _dsn(self, user: str, password: str) -> str:
        return (
            f"postgresql+psycopg://{quote_plus(user)}:{quote_plus(password)}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @model_validator(mode="after")
    def _assemble_database_url(self) -> Settings:
        if not self.migration_database_url:
            self.migration_database_url = self._dsn(self.postgres_user, self.postgres_password)
        if not self.database_url:
            # Prefer the RLS-enforced application role; fall back to the owner
            # only when no application password is configured (development),
            # which ``fail_on_bad_config`` refuses to allow in production.
            if self.postgres_app_password:
                self.database_url = self._dsn(self.postgres_app_user, self.postgres_app_password)
            else:
                self.database_url = self._dsn(self.postgres_user, self.postgres_password)
        for url in (self.database_url, self.migration_database_url):
            if not url.startswith(("postgresql+psycopg://", "postgresql://")):
                raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        if self.postgres_app_password and not self.postgres_app_user:
            raise ValueError(
                "POSTGRES_APP_USER must be set when POSTGRES_APP_PASSWORD is: "
                "the runtime connects as that role so row-level security applies"
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached settings singleton."""
    return Settings()


def fail_on_bad_config() -> None:
    """Exit immediately with a readable message if configuration is invalid.

    Also refuses to start production without the RLS-enforced application role:
    connecting as the owner makes every tenant policy inert, and a tenancy
    guarantee that silently degrades is worse than one that is absent.
    """
    try:
        settings = get_settings()
        if settings.is_production and not settings.rls_enforced:
            raise ValueError(
                "POSTGRES_APP_PASSWORD (or an explicit DATABASE_URL for the "
                "application role) is required in production: connecting as the "
                "table owner bypasses PostgreSQL row-level security"
            )
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
