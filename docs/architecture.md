# NexusOps Architecture

NexusOps is a self-hosted infrastructure management and monitoring platform. It
ships as a small constellation of containers: a FastAPI modular monolith, a
Celery worker and beat scheduler, PostgreSQL, Redis, an nginx edge, a static
SPA frontend — plus a dependency-free Python agent installed on managed hosts.

Everything in this document is derived from the code in this repository. Where
the platform is honest about a limitation (simulated deployments, SSRF DNS
rebinding), the limitation is documented here rather than papered over.

## 1. System overview

```mermaid
flowchart LR
    subgraph browser["Browser"]
        SPA["React SPA<br/>(TanStack Query + WS client)"]
    end

    subgraph edge["Edge :8080"]
        NGINX["nginx<br/>(nginx/default.conf.template)"]
    end

    subgraph apiPod["api container (uvicorn, API_WORKERS=2)"]
        APP["FastAPI app<br/>backend/app/main.py"]
        HUB["WebSocket hub<br/>backend/app/ws/hub.py"]
        DISP["notification dispatcher_loop<br/>(lifespan task)"]
    end

    subgraph bg["Backend containers"]
        WORKER["worker<br/>celery worker --concurrency=4"]
        BEAT["scheduler<br/>celery beat"]
    end

    PG[("PostgreSQL 17<br/>host 127.0.0.1:5433")]
    RD[("Redis 7<br/>host 127.0.0.1:6390<br/>broker + pub/sub + rate limits")]
    MP["Mailpit<br/>SMTP sink :1025, UI :8025"]
    AGENT["nexusops-agent<br/>on managed servers<br/>(agent/nexusops_agent.py)"]

    SPA -- "GET /            (SPA assets)" --> NGINX
    SPA -- "/api/*, /api/v1/ws  (WS upgrade)" --> NGINX
    NGINX -- "WEB_UPSTREAM frontend:8080" --> APP
    NGINX -- "API_UPSTREAM api:8000" --> APP
    APP --> PG
    APP <--> RD
    HUB -- "fan-in subscribe" --> RD
    WORKER --> PG
    WORKER <--> RD
    BEAT -- "enqueue fixed cadences" --> RD
    WORKER -- "SMTP (dev sink)" --> MP
    APP -- "SMTP (dev sink)" --> MP
    AGENT -- "POST /api/v1/agent/hello<br/>POST /api/v1/agent/heartbeat<br/>(X-Agent-Token)" --> NGINX
```

Wiring lives in `docker-compose.yml`:

- **nginx** is the only host-exposed port (`NEXUSOPS_HTTP_PORT`, default
  **8080**). `/` proxies to the frontend container (built static assets; in the
  dev profile `docker-compose.dev.yml` swaps in the Vite dev server on
  **:5173**). `/api/` proxies to the API with WebSocket upgrade headers and
  `proxy_buffering off` so log streams arrive live.
- **api** runs `uvicorn app.main:app` behind `backend/docker-entrypoint.sh`,
  which applies Alembic migrations before serving. The container entrypoint
  migrates but **never seeds** — there are no default credentials in a
  production-shaped stack. `make up` wraps build + up + `wait-ready` + `seed`
  for development.
- **worker** runs `celery -A app.tasks.celery_app:app worker
  --concurrency=4 --max-tasks-per-child=200`; **scheduler** runs `celery beat`.
  Both depend on the api healthcheck, which guarantees migrations are applied
  before any task runs.
- **postgres** (17) and **redis** (7) are published on loopback only
  (`127.0.0.1:5433`, `127.0.0.1:6390`) so host-run tooling (`make test-backend`,
  `make migrate`) can reach them without exposing them to the network.
- **mailpit** captures all outbound email in development (SMTP on the compose
  network, web UI on `127.0.0.1:8025`).
- **agent** (`agent/nexusops_agent.py`) is stdlib-only Python that reports
  metrics from `/proc` and Docker container state over the Docker socket. It
  enrolls once (`POST /api/v1/agent/hello`) and then heartbeats
  (`POST /api/v1/agent/heartbeat`) with a per-server `nxa_...` token. It only
  ever *reports*; the server cannot execute commands through it.

The API process itself hosts two long-lived tasks started in
`backend/app/main.py::lifespan`: the **WebSocket hub** (Redis fan-in listener)
and the **notification dispatcher loop** (`backend/app/services/notification_service.py::dispatcher_loop`,
which consumes `nx:events` and sweeps due retries). Background work that must
survive process restarts or parallelism (monitor checks, metric rollups,
deployment execution) belongs to Celery instead.

## 2. Request lifecycle

1. **nginx** terminates the connection, applies security headers
   (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` in
   `nginx/default.conf.template`) and proxies to the API with
   `X-Forwarded-For`/`X-Forwarded-Proto`.
2. **Middleware** (`backend/app/core/middleware.py`, registered in
   `main.py`; registration order is reversed on the way in, so the outermost
   middleware is first in the list):
   `RequestIDMiddleware` (assigns/propagates `X-Request-ID`, binds it to
   structlog context) → `SecurityHeadersMiddleware` → `AccessLogMiddleware`
   (duration + actor + status) → `CORSMiddleware` (strict allowlist from
   `CORS_ORIGINS`, credentials allowed).
3. **Rate limiting** on sensitive endpoints via
   `backend/app/core/rate_limit.py` — a Redis *fixed-window* counter per
   (limiter name, client IP). Pre-built limiters: auth 10/min, register
   5/5 min, refresh 30/min, deployment trigger 20/min, agent hello 30/min,
   agent heartbeat 600/min. The auth-facing limiters (register / login /
   refresh) **fail closed**: if Redis is unavailable they degrade to an
   in-process fixed-window counter (approximate across workers); the general
   and agent limiters **fail open** (request allowed, warning logged).
4. **Dependencies** (`backend/app/api/deps.py`): `get_session` opens an
   `AsyncSession`; `get_current_user` resolves the caller into an
   `AuthContext` from either `Authorization: Bearer <jwt>` or
   `X-API-Key: nxo_...`. Every authenticated request re-checks that the JWT's
   `sid` session exists, is unrevoked and unexpired — so revoking a session
   kills its access tokens immediately, before their 15-minute expiry.
5. **Router** (`backend/app/api/v1/*`) parses a Pydantic v2 schema, delegates
   to a service, serializes. Authorization is enforced with
   `require_permission("codename")` (see [RBAC](#8-rbac-registry)).
6. **Success** returns the router's response model; **failure** is an
   `AppError` subclass (`backend/app/core/errors.py`) rendered by the single
   exception-handler registry into the uniform envelope:

   ```json
   {"error": {"code": "NOT_FOUND", "message": "Deployment not found", "request_id": "…"}}
   ```

   Stack traces never reach the client; they are logged under the request id.
   The interactive OpenAPI surface is served by FastAPI at `/api/docs`, with
   the schema JSON at `/api/v1/openapi.json` (both configured in `main.py`).

## 3. Backend module map

```
backend/app/
  main.py               app factory + lifespan (hub, dispatcher); config fails fast
  api/
    deps.py             DB session, AuthContext, require_permission
    v1/                 one router module per domain:
                        agent alerts apikeys audit auth channels containers
                        deployments docker_hosts events health incidents meta
                        metrics monitors projects roles search secrets servers
                        sessions users
  core/
    config.py           pydantic-settings; fail_on_bad_config() aborts startup
    db.py               async engine + sessionmaker (SQLAlchemy 2, psycopg3)
    redis_client.py     shared Redis client
    security.py         Argon2id hashing, JWT encode/decode, Fernet, token utils
    permissions.py      PERMISSIONS registry + ROLE_MATRIX + scope matching
    errors.py           AppError taxonomy → error envelope
    middleware.py       RequestID / SecurityHeaders / AccessLog
    rate_limit.py       Redis fixed-window limiter factory
    pagination.py       shared paging helpers
    channels.py         canonical Redis channel names (nx:events, nx:logs:*, …)
    ssrf.py             outbound URL guard for monitors + webhooks
    logging.py          structlog JSON with central secret redaction
  models/               SQLAlchemy 2 declarative models, one file per domain
  schemas/              Pydantic v2 request/response models
  services/             business logic (auth_service, deployment_engine,
                        monitor_service, incident_service, event_bus,
                        audit_service, notification_service, secret_service, …)
  providers/            ports & adapters:
                          docker_factory → RealDockerProvider | SimulatedDockerProvider
                          monitor_transport → HTTPMonitorTransport | SimulatedTransport
                          notification_sender → smtp | webhook
                          deployment_runner → SimulatedDeploymentRunner (v1 only)
  tasks/                celery_app (beat schedule) + heartbeat, monitoring,
                        deployments, maintenance, simulation
  ws/                   router (/api/v1/ws) + hub (auth, subscriptions, fan-in)
```

Layering rules, visible in the imports: routers stay thin and never contain
business logic; services never import FastAPI request objects (they take an
`AsyncSession` first); providers never import services. Cross-domain calls
inside `backend/app/services/` (e.g. the deployment engine reaching into
`secret_service`) are late-imported inside functions with fallbacks so a
failure in one domain degrades instead of breaking the caller.

## 4. Data model overview

All models are declared in `backend/app/models/` (`identity.py`, `infra.py`,
`observability.py`, `delivery.py`, `notify.py`, `secrets.py`, `enums.py`) and
registered on one `Base.metadata`. Conventions: UUID v4 primary keys exposed
in APIs; `timestamptz` with `TimestampMixin` (`created_at`/`updated_at`);
status columns are strings constrained by `CheckConstraint`s generated from
Python enums (`models/base.py::status_check`); high-volume tables
(`monitor_checks`, `metric_snapshots`, `log_entries`) use bigserial integer
PKs; `JSONB` for flexible payloads.

```mermaid
erDiagram
    User }o--|| Role : "role_id (RESTRICT)"
    User ||--o{ Session : "sessions"
    Session ||--o{ RefreshToken : "rotation chain (superseded_by_id)"
    User ||--o{ ApiKey : "scoped machine keys"
    Server ||--o| DockerHost : "docker_host (1:0..1)"
    Server ||--o{ ServerCredential : "Fernet-encrypted"
    Server }o--o{ Tag : "server_tags"
    DockerHost ||--o{ Container : "observed state"
    Project ||--o{ Application : "applications"
    Application ||--o{ DeploymentEnvironment : "environments"
    Application ||--o{ Deployment : "numbered per app"
    Deployment ||--o{ DeploymentStep : "ordered steps"
    Monitor ||--o{ MonitorCheck : "check results"
    Monitor ||--o{ Incident : "opened per failure threshold"
    Incident ||--o{ IncidentEvent : "timeline"
    Server ||--o{ MetricSnapshot : "raw + rollups"
    Container ||--o{ LogEntry : "stdout/stderr"
    NotificationChannel ||--o{ NotificationDelivery : "delivery attempts"
```

Entity inventory by domain:

- **Identity** (`models/identity.py`): `User` (Argon2 hash, `is_superadmin`
  bootstrap flag, login-lockout counters), `Role`, `Permission`,
  `RolePermission` (join table), `Session` (device context, revocation),
  `RefreshToken` (SHA-256 hash only, `superseded_by_id` rotation pointer),
  `ApiKey` (`key_hash` unique, JSONB `scopes`).
- **Infrastructure** (`models/infra.py`): `Server` (agent enrollment token
  hash, heartbeat interval, `simulated` flag), `ServerCredential` (Fernet
  ciphertext), `Tag`/`ServerTag`, `DockerHost` (one optional per server),
  `Container` (mirrored observed state, unique per host+container_id),
  `ContainerImage`.
- **Delivery** (`models/delivery.py`): `Project` → `Application` →
  `DeploymentEnvironment` → `Deployment` (per-application sequential
  `number`, `is_rollback`, `rollback_of_id`) → `DeploymentStep` (ordered by
  `idx`, capped `output`). `Application.current_deployment_id` uses
  `use_alter` to break the circular FK.
- **Observability** (`models/observability.py`): `Monitor` (thresholds:
  `failure_threshold` consecutive failures open an incident, `success_threshold`
  recover it), `MonitorCheck`, `Incident` + `IncidentEvent` timeline,
  `MetricSnapshot` (granularity raw/hourly), `LogEntry` (source container /
  deployment / server), `SystemEvent` (the event-bus table, with
  `dedup_key` unique constraint), `AuditLog`, `Alert`.
- **Notifications** (`models/notify.py`): `NotificationChannel` (Fernet
  encrypted provider config + pre-masked `display_target`, subscribed event
  types — empty list means all), `NotificationDelivery` (status, attempts,
  `next_retry_at`).
- **Secrets** (`models/secrets.py`): `Secret` (Fernet ciphertext, `version`,
  non-reversible `digest` for change display; project-scoped with a partial
  unique index for global keys; plaintext never returned after creation).

Retention is enforced by `backend/app/tasks/maintenance.py`: raw metric
snapshots and hourly rollups are trimmed per `RAW_METRIC_RETENTION_HOURS`
(24 h) and `HOURLY_METRIC_RETENTION_DAYS` (30 d); `log_entries` follow
per-source retention (containers 3 d, servers 7 d, deployments 30 d) plus a
5 000-row cap per container.

## 5. Authentication and token lifecycle

Three credential families coexist:

1. **Users** — Argon2id password (`backend/app/core/security.py`,
   `PasswordHasher` defaults) + short-lived JWT access token + opaque refresh
   token.
2. **API keys** — `nxo_...` opaque keys for machine clients; only the SHA-256
   hash is stored, with JSONB scope patterns (e.g. `server.*`).
3. **Agent tokens** — `nxa_...` per-server enrollment tokens, also
   hash-at-rest, resolved by `X-Agent-Token` in `backend/app/api/v1/agent.py`.

```mermaid
sequenceDiagram
    autonumber
    participant B as SPA (browser)
    participant A as API /api/v1/auth
    participant DB as PostgreSQL

    B->>A: POST /auth/login {email, password}
    A->>DB: load User, check locked_until
    A->>A: Argon2 verify (fails increment counter, >=5 → lock 900 s)
    A->>DB: INSERT Session + RefreshToken (sha256 hash stored)
    A-->>B: {access_token (JWT, 15 min)}<br/>Set-Cookie: nxo_rt=… (HttpOnly, SameSite=Strict, Path=/api/v1/auth)
    Note over B: token held in module memory only<br/>(frontend/src/api/client.ts)

    B->>A: GET /api/v1/… (Authorization: Bearer)
    A->>DB: JWT ok AND session live? → AuthContext + permissions

    Note over B: on 401 (or page reload): POST /auth/refresh with cookie
    B->>A: POST /auth/refresh (HttpOnly cookie)
    A->>DB: lookup token_hash, supersede old row (superseded_by_id)
    A-->>B: new access_token + rotated nxo_rt cookie

    Note over A,DB: replay of a superseded token = theft signal:<br/>revoke the whole Session, audit auth.token_reuse_detected, 401 TOKEN_REUSE

    B->>A: POST /auth/logout
    A->>DB: revoke Session (reason=logout) → all tokens die immediately
```

Design points, all traceable in code:

- **Access token** (`create_access_token`): HS256 JWT with claims
  `sub`, `sid` (session id), `email`, `jti`, `typ=access`, `iat`, `exp`,
  `iss=nexusops`; TTL from `ACCESS_TOKEN_TTL_MINUTES` (15). The SPA keeps it
  in memory — never `localStorage` — and renews it transparently: on a 401
  the client calls `/auth/refresh` once and retries
  (`frontend/src/api/client.ts`), coalescing concurrent refreshes into one
  network call.
- **Refresh token**: `secrets.token_urlsafe(48)`, stored as SHA-256
  (`refresh_tokens.token_hash` unique), TTL `REFRESH_TOKEN_TTL_DAYS` (14).
  The cookie (`nxo_rt`) is `HttpOnly`, `SameSite=Strict`, scoped to
  `/api/v1/auth`, and `Secure` in production
  (`config.Settings.cookies_secure`), which reduces the CSRF surface to the
  refresh endpoint alone.
- **Rotation with reuse detection** (`auth_service.refresh`): every use
  issues a fresh row and marks the old one `superseded_by_id` + `revoked_at`.
  Presenting a superseded or revoked token is treated as theft: the entire
  session (all chained tokens) is revoked, a DENIED audit row is written, and
  a `401 TOKEN_REUSE` is returned. The revocation is committed explicitly
  because the request dependency would otherwise roll it back alongside the
  raised exception.
- **Session revocation is instant**: `deps.resolve_auth` validates the `sid`
  claim against the live `sessions` row on every request, so logout, password
  change (which revokes *other* sessions) and admin revocation take effect
  before the access token expires.
- **Lockout**: `LOGIN_MAX_ATTEMPTS` (5) failed passwords set `locked_until`
  for `LOGIN_LOCKOUT_SECONDS` (900) and flip the user to LOCKED; failures are
  audited with a generic "Invalid email or password" response.
- **Bootstrap**: the very first registered account (when `users` is empty)
  becomes a superadmin bound to the system `Owner` role; afterwards
  registration requires `user.manage`. `is_superadmin` is never grantable via
  the API. In development, `make seed` (`backend/scripts/seed.py`) creates
  the demo admin **admin@nexusops.example.com** — dev convenience only, and
  only because seeding is an explicit opt-in step. The password is the
  deterministic `nexusops-admin` only when `ENVIRONMENT=test` (what the
  pytest and E2E suites rely on); any other non-production seed generates a
  random one-time password that is printed once on stderr.
- **API keys** intersect two grant sets: the key's `scopes` patterns AND the
  owning user's role permissions (`deps.AuthContext.has_permission`).

## 6. WebSocket hub

Endpoint `GET /api/v1/ws` (`backend/app/ws/router.py`) hands each socket to
`Hub` in `backend/app/ws/hub.py`. The hub is deliberately framework-thin: no
FastAPI request stack, just sockets, a Redis listener and its own DB
sessions, so the same code would run in a dedicated process.

**Protocol** (JSON frames):

1. Client connects; the hub checks `Origin` against the CORS allowlist
   (mismatch → close `4403`).
2. Client must send within 10 s either
   `{"action":"auth","token":"<jwt>"}` or
   `{"action":"auth_apikey","key":"nxo_..."}`. Auth mirrors the HTTP path:
   JWT validity **and** a live session are required; failure closes `4401`.
   Success replies `auth_ok`.
3. Client subscribes: `{"action":"subscribe","channel":"...","params":{...}}`.
   Permissions are **re-checked on every subscribe frame** and entity
   existence is validated against the database, so a demoted user or a stale
   id cannot slip through mid-connection.

| Channel | Params | Required permission | Redis source |
|---|---|---|---|
| `global` | — | `event.read` | `nx:events` |
| `incidents` | — | `monitor.read` | `nx:events` (only `INCIDENT_*`/`MONITOR_*` types) |
| `server-metrics` | `server_id` | `metric.read` + `server.read` | `nx:metrics:<server_id>` |
| `container-logs` | `container_id` | `container.logs` | `nx:logs:<container_id>` |
| `deployment-logs` | `deployment_id` | `deployment.read` | `nx:deploy:<deployment_id>` |

**Fan-in**: producers (API services, Celery tasks) publish to the canonical
channels in `backend/app/core/channels.py`. The hub subscribes to `nx:events`
plus the `nx:logs:* / nx:deploy:* / nx:metrics:*` patterns and routes each
message to matching local subscriptions — a single process-per-socket model
would miss events emitted by workers; Redis pub/sub decouples them. Each
connection has a bounded queue (1 000 frames); on overflow the oldest frame
is dropped and a `SLOW_CONSUMER_DROPPED` notice is sent. Idle sockets are
reaped after 120 s (watchdog every 15 s), subscriptions are capped at 50 per
connection (close `4408`), and a service shutdown closes sockets with
`1012 service restart`.

**Client side** (`frontend/src/hooks/useEventStream.ts`): connects to
`/api/v1/ws`, authenticates with the in-memory access token (refreshing it
first via the cookie if the token was lost on reload), resubscribes
everything after `auth_ok`, and reconnects with capped exponential backoff
(1 s → 15 s), re-authenticating and resubscribing on each reconnect.

## 7. Deployment engine

`backend/app/services/deployment_engine.py` owns the deployment lifecycle
(`QUEUED → RUNNING → SUCCESS | FAILED | CANCELLED`), and
`backend/app/providers/deployment_runner.py` defines the runner port.

**Queueing** (`queue_deployment`): validates the version string, takes
`SELECT … FOR UPDATE` on the application row so per-application deployment
numbers are race-safe, inserts the `Deployment` plus one PENDING
`DeploymentStep` per planned step, publishes `DEPLOYMENT_QUEUED`, writes the
audit row, and hands off to Celery (`nx.run_deployment`). If the broker is
down the enqueue failure is *tolerated*: the periodic `nx.sweep_deployments`
task re-enqueues `QUEUED` rows older than 5 minutes, so a lost enqueue is
repaired rather than fatal.

**Execution** (`execute_deployment`, own session on the worker):

1. Claim the row while still `QUEUED` under `FOR UPDATE`, mark `RUNNING`,
   publish `DEPLOYMENT_STARTED`, then **commit immediately** — no row lock is
   held during slow work.
2. For each step: poll `cancel_requested` (a cancel from the API is honored
   between steps, never blocked behind one), mark the step `RUNNING`, and
   stream output lines from the runner.
3. Lines are buffered 20 at a time, then flushed in one transaction:
   appended to `LogEntry` rows (via `log_service`, with a direct-insert
   fallback), appended to the step's `output` column (capped at 60 KB), and
   published to Redis `nx:deploy:<deployment_id>` so subscribed browser
   sockets get live log frames.
4. Terminal transitions: on success the application's
   `current_version`/`current_deployment_id` are advanced, `DEPLOYMENT_SUCCEEDED`
   is emitted and an INFO alert row is created; on failure the failed step
   records its error, remaining steps become `SKIPPED`, `DEPLOYMENT_FAILED`
   is emitted with a CRITICAL alert; on cancellation remaining steps become
   `SKIPPED` and `DEPLOYMENT_CANCELLED` is emitted. A last-resort handler
   marks crashed deployments FAILED in a fresh session so a deployment can
   never be stranded RUNNING (the 30-minute sweeper is the backstop).
5. `nx.sweep_deployments` also fails `RUNNING` rows older than 30 minutes
   whose worker died.

**Cancellation** is two-phase: a `QUEUED` deployment is cancelled
immediately; a `RUNNING` one gets `cancel_requested = true` and the
cooperative cancel in step 2 turns it into `CANCELLED` at the next step
boundary.

**Rollback is a new deployment** (`rollback_deployment`): only `SUCCESS` or
`FAILED` deployments can be rolled back; the target is the most recent
successful *non-rollback* deployment of the same application + environment;
the engine then queues a fresh deployment of that old version with
`trigger=ROLLBACK`, `is_rollback=true` and `rollback_of_id` set. History
therefore stays append-only — nothing is re-run in place, and the rollback
itself has a number, logs and steps like any other deployment.

**Honest limitation**: v1 ships `SimulatedDeploymentRunner` only. The seven
canonical steps (`PULL_REPO → CHECKOUT → BUILD_IMAGE → STOP_OLD_CONTAINER →
START_NEW_CONTAINER → HEALTH_CHECK → FINALIZE`) execute with per-line pacing,
health-check gating and injectable failure, so queueing, streaming logs,
cancellation, rollback, alerting and audit are all exercised for real — but
no shell command runs anywhere. A real runner (docker SDK / SSH) is a
reserved interface that is deliberately not implemented rather than
half-shipped; the docstring in `deployment_runner.py` says exactly this.

## 8. RBAC registry

Authorization is data, not code paths. `backend/app/core/permissions.py`
defines:

- `PERMISSIONS` — a tuple of 30 `PermissionSpec(codename, group, description)`
  entries across eight groups (Access Control, Servers, Containers, Delivery,
  Monitoring, Notifications, Observability, Secrets), e.g.
  `server.update`, `container.lifecycle`, `deployment.rollback`,
  `secret.write`. The registry is seeded into the `permissions` table.
- `ROLE_MATRIX` — seed grants for the five built-in roles:

| Role | Grants |
|---|---|
| `Owner` | `*` (wildcard — implies every permission, including `role.manage`) |
| `Admin` | Operator's set plus `user.manage`, `role.read`, `project.manage`, `secret.write` |
| `Operator` | full fleet lifecycle (`server.*` writes, `credential.write`), containers, delivery (deploy/cancel/rollback), monitoring + incident action, channels, observability reads, `secret.read`; **no** `user.manage`, `role.read`/`role.manage`, `secret.write` |
| `Developer` | read-mostly, plus `deployment.create`/`cancel` and `monitor.manage`/`incident.action`; **no** `server.*` writes, `credential.write`, `container.lifecycle`/`remove`, `secret.write`, `channel.manage` |
| `Viewer` | read-only codenames (`*.read` across servers, containers, delivery, monitoring, channels, observability) plus `container.logs` |

- `scope_matches` — API-key scope patterns: exact match, `*`, or prefix
  wildcards like `server.*`.

Checks are centralized: `require_permission("codename")`
(`backend/app/api/deps.py`) is a dependency factory used by routers; it
resolves the caller's permission set (role permissions, or `*` for the
superadmin bootstrap user) and returns `403 PERMISSION_DENIED` on miss. For
API-key callers the check is an **intersection**: both the key's scopes and
the owner's role must allow the codename. `AuthContext.has_permission` also
honours trailing-`*` prefixes in a role's permission set. Custom roles are
first-class (`role.manage` creates them), and the codebase convention bans
`if user.role == "admin"`-style checks entirely — the registry docstring says
so and review enforces it.

## 9. Audit log append-only trigger

`backend/app/services/audit_service.py::record` appends an `AuditLog` row
inside the caller's transaction: actor (user or `"system"`), action codename
(e.g. `deployment.queue`, `auth.token_reuse_detected`), resource type/id, IP
+ user agent, `SUCCESS`/`DENIED` result, and a metadata dict passed through
`redact_mapping` so secrets never reach the trail (or logs — the same
redactor guards structlog output in `core/logging.py`).

Immutability is enforced by the database, not the app. The initial Alembic
migration (`backend/alembic/versions/20260823_2225-b5866787bde4_initial_schema.py`)
creates:

```sql
CREATE OR REPLACE FUNCTION nexusops_block_audit_mutation() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'audit_logs is append-only (attempted %)', TG_OP;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_logs_no_update BEFORE UPDATE OR DELETE ON audit_logs
FOR EACH ROW EXECUTE FUNCTION nexusops_block_audit_mutation();
```

So even a compromised or buggy application role cannot rewrite or erase
history; corrections are new rows. There is intentionally no API surface for
editing audit entries — `audit.read` is read-only.

## 10. Scheduling and simulation mode

Celery beat (`backend/app/tasks/celery_app.py`) fires only fixed cadences;
anything stateful claims its work atomically (`FOR UPDATE SKIP LOCKED` in
`monitor_service.claim_due_monitors`) so overlapping ticks or extra workers
partition work instead of duplicating it:

| Task | Cadence | Purpose |
|---|---|---|
| `nx.sweep_servers` | 15 s | mark silent servers OFFLINE / recover returning ones |
| `nx.run_due_monitors` | `MONITOR_DISPATCH_INTERVAL_SECONDS` (10 s) | claim up to 50 due monitors, one short transaction per check |
| `nx.sync_docker_hosts` | 30 s | reconcile every registered Docker host (status, pull recent logs from real ones) |
| `nx.sweep_deployments` | 120 s | re-enqueue lost QUEUED, fail dead RUNNING |
| `nx.retry_notifications` | 60 s | retry due `notification_deliveries` |
| `nx.expire_sessions` | 600 s | revoke sessions past expiry, purge dead refresh tokens |
| `nx.aggregate_metrics` | `METRICS_AGGREGATION_INTERVAL_SECONDS` (60 s) | raw → hourly rollups |
| `nx.trim_logs` | 15 min | per-source log retention |
| `nx.simulation_tick` | 20 s | synthetic fleet driver (self-disables unless `SIMULATION_MODE=true`) |

`SIMULATION_MODE=true` (set in `.env.example`) makes the platform
laptop-runnable with no real infrastructure: `backend/app/tasks/simulation.py`
synthesizes heartbeats for every server flagged `simulated` — deterministic
sine-wave CPU/memory keyed by server id, a stable container set whose members
occasionally cycle EXITED to exercise diff events, and one designated
`-flaky` node that goes silent for two minutes each hour so OFFLINE → ONLINE
transitions are demonstrable. Provider selection
(`backend/app/providers/docker_factory.py`) routes `sim://` endpoints (or
anything, in simulation mode) to `SimulatedDockerProvider`, and
`backend/app/providers/monitor_transport.py` does the same for `sim://`
monitor URLs. The UI renders a badge whenever the backend reports simulation
mode. Everything else — incidents, notifications, WebSocket fan-out, audit —
runs the real code paths.

## 11. Known limitations

Documented rather than hidden:

- **Deployments are simulated** (see [§7](#7-deployment-engine)); no real
  code ships anywhere in v1.
- **SSRF guard DNS-rebinding window** (`backend/app/core/ssrf.py`): URLs are
  validated (scheme allowlist, no userinfo, all resolved addresses public,
  fail-closed on unresolvable hosts), but validation and the actual request
  use separate DNS lookups, so an attacker controlling authoritative DNS
  could pass validation with a public address and connect privately later.
  Pinning the validated IP at connect time is tracked as follow-up work.
- **Rate-limiting degrades when Redis is unavailable**
  (`core/rate_limit.py`): the auth-facing limiters fail closed via an
  in-process fixed-window fallback (approximate across workers), while the
  general and agent limiters fail open — availability is prioritized over
  throttling there. The limiter is a fixed window (bursty at window edges
  by design).
- **Agent is pull-only reporting** (`agent/nexusops_agent.py`): no command
  execution from the server, which also means the platform cannot remediate
  anything on a host — it observes and alerts.
- **Single Redis** doubles as broker, result backend, pub/sub and rate-limit
  store; it is run without persistence (`--appendonly no --save ""`), which
  is fine for pub/sub semantics and acceptable because durable state (events,
  deliveries, deployments) lives in PostgreSQL, but a Redis restart loses
  in-flight task messages until the deployment/monitor sweepers repair them.
- **`task_acks_late=False`**: periodic sweeps are idempotent and cheap, so
  early-ack is chosen deliberately to avoid Redis visibility-timeout
  redelivery loops (documented in `celery_app.py`).

## 12. Key design decisions

| Decision | Choice | Rationale (one line) |
|---|---|---|
| Topology | Modular monolith (one API image, Celery worker/beat) | One codebase, two entrypoints (`backend/app/main.py` and `backend/app/tasks/celery_app.py`); microservice split would add ops cost with no benefit at this scale. |
| Async stack | FastAPI + SQLAlchemy 2 async (psycopg3) | WebSocket hub and streaming endpoints need an async core; one pooled engine per process. |
| Config | pydantic-settings validated at import (`fail_on_bad_config`) | Invalid secrets/URLs abort startup with an actionable message instead of failing on first request. |
| Job system | Celery + beat, beat fires fixed cadences only | Dynamic scheduling (monitor intervals) lives in the DB and is claimed with `FOR UPDATE SKIP LOCKED`; beat stays dumb and restartable. |
| Real-time spine | PostgreSQL `system_events` + Redis pub/sub → in-API WS hub | The DB row is the source of truth and replayable; Redis carries only best-effort live fan-out, so a Redis outage never loses history. |
| AuthN | 15-min JWT in memory + opaque rotated refresh token in a scoped HttpOnly cookie | No ambient credential on regular API calls (no CSRF on them); the cookie is scoped to `/api/v1/auth` and `SameSite=Strict`. |
| AuthZ | DB-backed permission registry + `ROLE_MATRIX`, wildcard support | Permissions are data, so custom roles are first-class and no `role ==` string checks exist anywhere. |
| Session handling | `sid` claim validated against the live session row on every request | Logout/revocation is instant even while access tokens are still unexpired. |
| Secrets at rest | Fernet per-value encryption (`ENCRYPTION_KEY`), never returned after creation, digests for change display | Compromise of a DB dump alone is not enough; consumers resolve values server-side. |
| Audit | Append-only table + `BEFORE UPDATE OR DELETE` Postgres trigger | History cannot be rewritten even by the application's own DB role. |
| Observability writes | Batched inserts + retention tasks (`tasks/maintenance.py`) | High-volume tables (checks, metrics, logs) get integer PKs, indexes tuned per query, and hard caps instead of unbounded growth. |
| Simulation mode | First-class beat-driven synthetic fleet through the same provider interfaces | The whole product (offline detection, incidents, deployments) demos on a laptop with zero infrastructure and no forked code paths. |
| Deployment model | Rollback = new deployment referencing `rollback_of_id` | Deployment history stays append-only; rollbacks have their own numbers, logs and audit entries. |
| Error surface | Single `AppError` taxonomy → `{"error":{code,message,request_id}}` | Clients branch on stable machine codes; support can correlate via request id; stack traces stay in logs. |

## 13. Where to verify

- Stack wiring: `docker-compose.yml`, `docker-compose.dev.yml`, `nginx/default.conf.template`
- API assembly: `backend/app/main.py`, `backend/app/api/v1/`
- Models/migrations: `backend/app/models/`, `backend/alembic/versions/`
- Auth: `backend/app/services/auth_service.py`, `backend/app/core/security.py`, `frontend/src/api/client.ts`
- WebSocket: `backend/app/ws/hub.py`, `frontend/src/hooks/useEventStream.ts`
- Deployments: `backend/app/services/deployment_engine.py`, `backend/app/providers/deployment_runner.py`
- Background cadences: `backend/app/tasks/celery_app.py`
- Agent: `agent/nexusops_agent.py`, `agent/install.sh`, `agent/nexusops-agent.service`
- Tests: `backend/tests/` (pytest unit + integration against the dockerized
  Postgres :5433 / Redis :6390), `frontend/src/**/*.test.tsx` (vitest),
  `frontend/e2e/journey.spec.ts` (Playwright; run via `make e2e`)
