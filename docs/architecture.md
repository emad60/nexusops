# NexusOps Architecture

NexusOps is a self-hosted infrastructure control center: a modular-monolith API with
worker processes, a real-time event backbone, an SPA frontend, and a lightweight
agent installed on managed servers.

## 1. System overview

```
                    ┌────────────────────────────────────────────────────┐
                    │                      nginx :8080                   │
                    │  /        → static SPA (or vite dev server)        │
                    │  /api/    → api:8000                               │
                    │  /ws/     → api:8000 (WebSocket upgrade)           │
                    └─────────┬──────────────────────────┬───────────────┘
                              │                          │
                    ┌─────────▼─────────┐      ┌─────────▼─────────┐
                    │   api (FastAPI)   │      │ frontend (React)  │
                    │  REST + WS hub    │◄─────│  TanStack Query   │
                    └───┬────────┬──────┘      └───────────────────┘
                        │        │
             ┌──────────▼──┐  ┌──▼───────────────┐      ┌──────────────────┐
             │ PostgreSQL  │  │ Redis            │◄─────│ worker(s) x2     │
             │ state       │  │ pub/sub + queues │      │ beat scheduler   │
             └─────────────┘  └──────────────────┘      └──────┬───────────┘
                                                               │ providers
                                              ┌────────────────┼───────────────┐
                                        docker SDK          HTTP            SMTP
                                        / simulation      monitor checks    email
                                              ▲
                                    agent (on managed servers)
                                    heartbeat + metrics + containers
```

**Processes**: `api` (uvicorn, REST + WebSocket hub), `worker` (Celery), `beat`
(Celery beat dynamic dispatcher), `postgres`, `redis`, `nginx`, `frontend`
(dev: Vite; prod: static assets served by nginx), plus `agent` on managed hosts.

## 2. Key decisions

| Decision | Choice | Rationale |
|---|---|---|
| Topology | Modular monolith | One deployable API + workers; domains are packages with explicit boundaries. Microservices would add operational cost with no benefit at this scale. |
| Async DB | SQLAlchemy 2 async + psycopg3 | WebSockets and fan-out benefit from async; one engine, pooled. |
| Job system | Celery + Celery beat | Battle-tested retries/backoff; beat used only as a *fixed-cadence dispatcher* that fans out due work (dynamic intervals live in the DB). |
| Real-time bus | Redis pub/sub → in-API WS hub | Events can be published from any process (API or worker); hub fans out to subscribed sockets after permission filtering. |
| Auth | Argon2id + short JWT access token **in memory** + opaque rotated refresh token in HttpOnly `SameSite=Strict` cookie scoped to `/api/v1/auth` | Refresh-token CSRF surface is reduced to a single endpoint protected by SameSite=Strict + Origin checks; no ambient credential on regular API calls means no CSRF on them. |
| RBAC | DB-backed permission registry, role→permission matrix, `require_permission(...)` dependency | Permissions are data, not scattered `if role ==` checks; custom roles are first-class. |
| Secrets | Fernet (AES128-CBC+HMAC) envelope per value, versioned, never returned after creation | Server-side consumers (deployment engine) resolve values; API exposes rotate/reveal-metadata only. |
| Docker access | Provider protocol: `RealDockerProvider` (docker SDK over TCP/TLS/socket) and `SimulatedDockerProvider` | Tests and demo mode run without a daemon; dangerous ops go through permission + confirmation gates. |
| Metrics storage | Raw snapshots ≤24h, hourly rollups ≤30d, daily rollups beyond | Charts query aggregates by range; raw data never floods the browser or the DB. |
| Audit immutability | Append-only table + Postgres trigger blocking UPDATE/DELETE | Even a buggy code path cannot rewrite history. |
| Simulation mode | First-class: seeded fleet driven by beat tasks through the same provider interfaces | Whole product demonstrable on a laptop; UI shows a "Simulated" badge. |

### Deviations from the suggested layout

- `worker/` is **not** a separate top-level package duplicating backend code.
  Celery lives at `backend/app/tasks/`; the worker container runs
  `celery -A app.tasks.celery_app.worker`. One codebase, two entrypoints.
- The agent lives in `agent/` as a **stdlib-only** Python program (no pip install
  required on targets beyond Python itself); metrics come from `/proc`.

## 3. Backend layout

```
backend/app/
  main.py               app factory: middleware, routers, lifespan
  core/
    config.py           pydantic-settings; fail-fast validation of secrets/URLs
    db.py               async engine + session factory
    redis.py            shared Redis client
    security.py         argon2 hashing, JWT encode/decode, Fernet box, token utils
    permissions.py      Permission registry + role matrix + require_permission()
    errors.py           AppError taxonomy → {"error": {code,message,request_id}}
    middleware.py       RequestID, security headers, access log w/ duration+actor
    rate_limit.py       Redis sliding-window dependency factory
    pagination.py       offset Page[T] + keyset CursorPage helpers
    logging.py          structlog JSON config
    ws_hub.py           WebSocket hub: auth, subscriptions, Redis fan-out
  models/               SQLAlchemy 2.0 declarative models (one file per domain)
  schemas/              Pydantic v2 request/response models
  api/v1/               routers: auth users roles apikeys sessions servers
                        containers deployments projects monitors incidents
                        notifications alerts metrics events audit secrets
                        search meta health
  services/             business logic (auth_service, deployment_engine,
                        monitor_engine, incident_service, notification_service,
                        event_bus, audit_service, secret_service, ...)
  providers/            ports & adapters:
                          DockerProvider      → real (SDK) | simulated
                          MonitorTransport    → httpx | simulated flaky
                          NotificationSender  → smtp | webhook | noop(log)
                          DeploymentRunner    → simulated | local-docker
  tasks/                celery_app + task modules (monitoring, heartbeat,
                        metrics, notifications, deployments, cleanup, simulate)
alembic/                migration env + versions
tests/                  unit + integration (pytest, httpx ASGI transport)
```

Rules enforced in review: routers stay thin (parse → service → serialize);
services never import FastAPI; providers never import services; all writes to
high-volume tables are batched and paginated reads are mandatory.

## 4. Data model (core tables)

Identity: `users`, `roles`, `permissions`, `role_permissions`, `sessions`,
`refresh_tokens`, `api_keys`.
Infrastructure: `servers`, `server_credentials`, `docker_hosts`, `containers`,
`container_images`, `tags`, `server_tags`, `metric_snapshots`, `log_entries`.
Delivery pipeline: `projects`, `applications`, `deployment_environments`,
`deployments`, `deployment_steps`.
Observability: `monitors`, `monitor_checks`, `incidents`, `incident_events`,
`system_events`, `audit_logs`, `alerts`.
Notifications: `notification_channels`, `notification_deliveries`.
Secrets: `secrets` (ciphertext, version, rotated_at).

Conventions: UUID v4 PKs exposed in APIs (no enumeration oracle); timezone-aware
timestamps (`timestamptz`, server default `now()`); status fields are
`VARCHAR` + `CheckConstraint` backed by Python `StrEnum`s; FKs explicitly indexed;
soft delete only where it carries meaning (`users.is_active`) — everything else
deletes hard and leaves audit history behind.

## 5. Event flow (the spine)

1. A domain service calls `event_bus.publish(type, payload, resource...)` inside
   or right after its transaction.
2. `event_bus` writes a `system_events` row and publishes a compact JSON message
   to Redis channel `nx:events` (best-effort; the row is the source of truth).
3. Workers/API subscribe once; the WS hub matches each client's subscriptions +
   permissions and forwards `{type, channel, data}` frames.
4. `notification_dispatcher` (Celery) matches channels by subscribed event types,
   renders and sends via provider adapters, recording `notification_deliveries`;
   failures retry with exponential backoff (max 5).
5. `alerts` rows are created for user-facing severity so the UI bell works offline.

Event types are a closed registry (`core/events.py`): `SERVER_ONLINE`,
`SERVER_OFFLINE`, `CONTAINER_*`, `DEPLOYMENT_*`, `MONITOR_DOWN`,
`MONITOR_RECOVERED`, `USER_LOGIN`, `USER_LOGOUT`, `PERMISSION_CHANGED`,
`SECRET_UPDATED`, `INCIDENT_OPENED`, `INCIDENT_RESOLVED`, …

## 6. Scheduling model

Celery beat fires only fixed cadences; everything dynamic is dispatched from DB:

- `dispatch-due-checks` (every `MONITOR_DISPATCH_INTERVAL_SECONDS`): selects
  monitors where `next_check_at <= now()` → enqueues one idempotent check task
  per monitor and bumps `next_check_at` (claim via `UPDATE ... WHERE next_check_at = old`)
  so overlapping beats cannot double-fire.
- `process-heartbeats` (every 30s): marks stale servers OFFLINE / recovered ONLINE,
  emitting events once via state guards.
- `aggregate-metrics` (every minute): rolls raw → hourly/daily, prunes expired.
- `simulate-tick` (every 15s when SIMULATION_MODE): advances simulated CPU/mem,
  occasionally flips containers, drives a deliberately flaky monitor and demo
  deployments.
- `cleanup` (hourly): expired refresh tokens/sessions, old log_entries ring buffers.

## 7. Frontend

React 19 + TypeScript + Vite, TanStack Query for all server state (no global
store; component-local state where possible), React Router with lazy routes.
Design system: hand-rolled Tailwind-based component kit (dark-first developer
aesthetic, dense data tables, monospace numerics). Charts are custom SVG
components (area/sparkline/bar) chosen for full aesthetic control and zero chart-lib
weight; they follow the dataviz guidance (consistent palette, accessible contrast,
never color-alone encoding).

WebSocket client (`useEventStream`) handles: auth handshake as first frame,
subscribe/unsubscribe multiplexing, ping/pong keepalive, exponential-backoff
reconnect with resubscription, and exposes connection status consumed by a
global "disconnected" banner.

## 8. Security posture (summary)

Argon2id hashes; login lockout + IP rate limits; JWT HS256 (secret ≥32 bytes,
validated at boot); refresh rotation with reuse detection (revoke whole session);
session list/revoke; API keys hashed-at-rest with scopes; double-check
authorization at router boundary via `require_permission`; object-level checks
(IDOR guard in services); SSRF guard on monitor/webhook URLs (scheme allowlist +
IP-range block unless `ALLOW_PRIVATE_TARGETS`); strict CORS allowlist; security
headers via middleware; secrets Fernet-encrypted and redacted by a central
`redact()` used by logs and error payloads; audit trail on every sensitive action;
Postgres trigger enforcing audit immutability. See `docs/security.md`.

## 9. Failure handling

Every external interaction has: timeout, retry policy, and a degraded-mode path —
Docker host unreachable → host marked UNAVAILABLE, containers shown stale;
Redis down → API still serves reads, events buffer loss accepted (DB rows remain);
Postgres down → `/ready` fails, nginx keeps serving cached SPA; worker crash →
Celery acks_late + idempotent tasks make redelivery safe; monitor timeout counts
as failure with bounded incident escalation; duplicate events deduped by
`(type, resource_type, resource_id, dedup_key)` unique constraint where relevant.
