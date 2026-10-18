"""Central configuration.

All runtime configuration flows through this module so that invalid
configuration fails loudly at process start instead of at request time.
"""

from __future__ import annotations

import sys
from functools import lru_cache
from typing import Literal
from urllib.parse import quote_plus, unquote_plus, urlsplit

from cryptography.fernet import Fernet
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.models.enums import AcmeDirectory

_ENV_FILE_CANDIDATES = (".env", "../.env")

#: The accepted ``ACME_DIRECTORY`` values, taken from the vocabulary itself so a new
#: member cannot be forgotten here (the enum is the closed set; this is a lookup of
#: its values, never a second list).
_ACME_DIRECTORY_VALUES: frozenset[str] = frozenset(member.value for member in AcmeDirectory)


class Settings(BaseSettings):
    """Validated application settings (loaded from environment / .env)."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE_CANDIDATES,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        # A settings object holds every credential the process has (the signing
        # key, the database password, the AppRole secret id). Pydantic renders the
        # offending *input* into a validation error by default, and
        # ``fail_on_bad_config`` prints that text to stderr — so a mistyped
        # variable would echo the very secret it is complaining about. Hiding the
        # input keeps the message (which names variables, never values) and drops
        # the echo.
        hide_input_in_errors=True,
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

    # --- Key management (Phase 5.2.1) ----------------------------------
    #: Which root-key provider wraps organization DEKs. **Explicitly selected**:
    #: there is no detection, no default and no fallback. ``vault-transit`` is the
    #: production provider; ``test`` is the deterministic in-process provider for
    #: tests and explicitly configured development, and it is refused in
    #: production (see :func:`validate_key_management` below and
    #: ``app/services/kek/factory.py``). Empty means "no key management", which is
    #: tolerated outside production so the rest of the platform can serve while
    #: key-dependent operations fail closed.
    kek_provider: str = ""
    kek_vault_addr: str | None = None
    kek_vault_namespace: str | None = None
    #: The transit key name. It must be created with ``derived=true``: the
    #: organization/purpose/generation binding travels as the derivation context,
    #: which is the only parameter Transit accepts on encrypt, decrypt *and*
    #: rewrap.
    kek_vault_transit_key: str | None = None
    #: AppRole credentials for a policy scoped to that one transit key. No root
    #: token, and no key-administration capability, ever reaches this process.
    kek_vault_role_id: str | None = None
    kek_vault_secret_id: str | None = None
    #: CA bundle used to verify Vault's certificate. Unset means the system trust
    #: store; there is deliberately no way to disable verification.
    kek_vault_ca_bundle: str | None = None
    kek_vault_timeout_seconds: float = Field(default=5.0, ge=0.5, le=60)
    #: How long a provider health probe is reused. Readiness probes are frequent,
    #: and a health check is a provider round-trip; caching the *answer* (never key
    #: material) keeps probing from becoming provider load.
    kek_health_cache_seconds: int = Field(default=30, ge=0, le=600)

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
    #: --- Domain routing (Phase 4) ---------------------------------------
    #: How often the domain sweep runs. Rows carry their own ``next_check_at``
    #: (hourly re-check, bounded failure backoff and the 72h stale grace), so this
    #: tick only decides how promptly a due row is picked up.
    domain_sweep_interval_seconds: int = Field(default=300, ge=30, le=86400)
    #: How often routed nodes are asked for their live proxy state, and re-applied
    #: when the desired bundle differs. Applies are deduplicated, so this cannot
    #: flood a node's operation queue.
    route_sweep_interval_seconds: int = Field(default=60, ge=15, le=3600)
    #: DNS timeouts for ownership verification. Bounded so an unresponsive
    #: authoritative server cannot hold a worker open.
    dns_query_timeout_seconds: float = Field(default=3.0, ge=0.5, le=30)
    dns_total_budget_seconds: float = Field(default=12.0, ge=1, le=120)
    metrics_aggregation_interval_seconds: int = Field(default=60, ge=10)
    raw_metric_retention_hours: int = Field(default=24, ge=1)
    hourly_metric_retention_days: int = Field(default=30, ge=1)

    # --- Certificate issuance & ACME (Phase 5.3) ------------------------
    #: Which ACME directory issuance uses. **Empty is a real value**: outside
    #: production it means "the non-production default" (staging), and in
    #: production it is refused — production issuance requires the operator to name
    #: ``production`` explicitly (phase5-design.md §5.4). Accepted values are the
    #: :class:`~app.models.enums.AcmeDirectory` members: ``staging``, ``production``
    #: and ``pebble`` (the local test CA the integration suite runs). There is no
    #: silent fallback in either direction: an unknown value, Pebble in production
    #: and production outside production all fail at process start.
    acme_directory: str = ""
    #: Contact address registered with the CA. Optional: the CA does not require it
    #: and this platform tracks expiry itself, but a staging/production account with
    #: no contact gets no expiry warning from the CA either.
    acme_account_email: str = ""
    #: How long one attempt may wait for the TXT record to appear on the zone's
    #: authoritative nameservers, and how long it may then wait for the CA to
    #: validate the challenge. Both are wall-clock deadlines inside a worker whose
    #: soft limit is 540s, and the three below plus overhead must fit inside it —
    #: which is why they are settings with upper bounds and not loose numbers.
    certificate_propagation_timeout_seconds: int = Field(default=120, ge=10, le=600)
    certificate_validation_timeout_seconds: int = Field(default=240, ge=30, le=480)
    certificate_finalization_timeout_seconds: int = Field(default=60, ge=10, le=240)
    #: How long a generation may sit in ORDERING/CHALLENGE_PUBLISHED/VALIDATING
    #: before the sweep treats it as abandoned by a crashed worker and recovers it
    #: (best-effort TXT cleanup, then a failure with the backoff). Deliberately much
    #: longer than an attempt can legitimately take: recovering a live attempt would
    #: be a second order for one generation.
    certificate_order_ttl_seconds: int = Field(default=3600, ge=300, le=86400)
    #: How often the issuance sweep looks for due and abandoned generations.
    certificate_sweep_interval_seconds: int = Field(default=60, ge=15, le=900)
    #: TTL of the ``_acme-challenge`` TXT records this platform publishes. Short on
    #: purpose: a record left behind by a crash expires on its own, which is the
    #: failure mode whose cleanup we cannot guarantee.
    certificate_dns_ttl_seconds: int = Field(default=60, ge=30, le=3600)

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

    @field_validator("kek_vault_addr")
    @classmethod
    def _reject_vault_addr_credentials(cls, v: str | None) -> str | None:
        """Refuse a Vault address that carries userinfo (Phase 5.2.1.2, F4).

        ``https://user:password@vault:8200`` puts a credential in a place nothing
        here reads: Vault access is AppRole, through ``KEK_VAULT_ROLE_ID`` and
        ``KEK_VAULT_SECRET_ID``. Such an address is at best a mistake — the
        credentials are silently dropped by the HTTP client's base URL rules — and
        at worst a password sitting in a shell history, a compose file and a log
        line. It is rejected for that reason.

        The message names the variables and never the value: a validation error is
        startup output, and the input is exactly what must not appear in it (see
        ``hide_input_in_errors`` above). A path prefix is untouched —
        ``https://vault.example:8200/team`` stays valid, since only the *authority*
        component is inspected.
        """
        if v is None or not v.strip():
            return v
        try:
            parts = urlsplit(v)
        except ValueError:
            # Not parseable as a URL at all; the https:// check reports that with a
            # message that does not quote the value either.
            return v
        if parts.username is not None or parts.password is not None or "@" in parts.netloc:
            raise ValueError(
                "KEK_VAULT_ADDR must not embed a username or password: Vault access "
                "is authenticated with KEK_VAULT_ROLE_ID and KEK_VAULT_SECRET_ID. "
                "Remove the credentials from the address."
            )
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

    @model_validator(mode="after")
    def _validate_acme_policy(self) -> Settings:
        """Refuse to start with an ACME directory selection that is unsafe or ambiguous.

        The whole matrix is decided here so that a misconfigured deployment fails
        before it serves a request, and so that the *same* rule cannot be applied
        inconsistently by a task later:

        * an unknown name is refused in every environment — the accepted set is the
          :class:`AcmeDirectory` vocabulary, and there is no fallback member;
        * ``pebble`` is refused in production: it is a test CA behind a self-signed
          certificate, and a production deployment that trusted it would mint
          unrunnable certificates;
        * ``production`` is refused outside production: production issuance is an
          explicit, deliberate act, and a development or CI process that can reach
          the real CA burns real rate limits;
        * unset means the non-production default (staging), and is **refused in
          production**, where naming the directory is what makes the choice
          explicit.

        The stored value is canonicalised (lower-case, stripped) so the enum lookup
        later is total, and the message names the variable and the accepted values —
        never a value that could be a credential.
        """
        name = (self.acme_directory or "").strip().lower()
        self.acme_directory = name
        if not name:
            if self.is_production:
                raise ValueError(
                    "ACME_DIRECTORY is required in production (set 'production'). "
                    "Issuance would otherwise have to guess which certificate authority "
                    "to use, and neither guess is safe."
                )
            self.acme_directory = AcmeDirectory.STAGING.value
            return self
        if name not in _ACME_DIRECTORY_VALUES:
            raise ValueError(
                f"ACME_DIRECTORY must be one of {sorted(_ACME_DIRECTORY_VALUES)} "
                "(the ACME directory vocabulary); there is no fallback directory"
            )
        if name == AcmeDirectory.PEBBLE.value and self.is_production:
            raise ValueError(
                "ACME_DIRECTORY=pebble is refused in production: Pebble is the local "
                "test certificate authority and its certificates are signed by a CA "
                "no client trusts. Use 'production'."
            )
        if name == AcmeDirectory.PRODUCTION.value and not self.is_production:
            raise ValueError(
                "ACME_DIRECTORY=production is refused outside production: issuance from "
                "this environment must never reach the real certificate authority. "
                "Use 'staging' or 'pebble'."
            )
        return self

    @model_validator(mode="after")
    def _validate_key_management(self) -> Settings:
        """Refuse to start with an unusable or unsafe key source.

        Two failures are worth exiting the process for rather than reporting at
        request time: a production deployment that names no provider (nothing can
        ever unwrap a DEK), and any environment that names the deterministic test
        provider *and* production. The latter is the important one — an unsafe key
        source must be unreachable by configuration, not by convention — and it is
        enforced here as well as in the provider factory, because this is the
        validation a container runs before it serves anything.
        """
        name = (self.kek_provider or "").strip().lower()
        self.kek_provider = name
        if not name:
            if self.is_production:
                raise ValueError(
                    "KEK_PROVIDER is required in production (set 'vault-transit'). "
                    "Organization DEKs would be unwrappable without a root-key provider."
                )
            return self
        if name not in ("vault-transit", "test"):
            raise ValueError(
                f"KEK_PROVIDER must be one of 'vault-transit', 'test' (got {name!r}); "
                "there is no fallback provider"
            )
        if name == "test":
            if self.is_production:
                raise ValueError(
                    "KEK_PROVIDER=test is refused in production: the deterministic "
                    "provider is a test fixture, not key custody. Use 'vault-transit'."
                )
            return self
        # vault-transit: a half-configured provider is a startup error in every
        # environment, because discovering it at the first unwrap would be a data
        # availability incident instead of a deployment mistake.
        missing = [
            variable
            for variable, value in (
                ("KEK_VAULT_ADDR", self.kek_vault_addr),
                ("KEK_VAULT_TRANSIT_KEY", self.kek_vault_transit_key),
                ("KEK_VAULT_ROLE_ID", self.kek_vault_role_id),
                ("KEK_VAULT_SECRET_ID", self.kek_vault_secret_id),
            )
            if not value
        ]
        if missing:
            raise ValueError("KEK_PROVIDER=vault-transit requires " + ", ".join(missing))
        assert self.kek_vault_addr is not None
        if not self.kek_vault_addr.startswith("https://"):
            raise ValueError(
                "KEK_VAULT_ADDR must use https:// — Vault carries the root key and "
                "certificate verification is mandatory"
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
