# NexusOps — Engineering Report

Status report for the complete build of NexusOps (self-hosted infrastructure
management & monitoring platform), covering what was delivered, how it was
verified, what the security audit found, and what remains imperfect. Written
2026-09-11. Companion docs: [architecture](architecture.md),
[api](api.md), [deployment](deployment.md), [security](security.md),
[development](development.md), [troubleshooting](troubleshooting.md),
[agent](agent.md).

## 1. Executive summary

NexusOps is delivered as a running, tested, audited system:

- **Full stack**: FastAPI modular monolith (Python 3.13, SQLAlchemy 2 async,
  PostgreSQL 17, Redis 7, Celery worker + beat, Pydantic v2, Alembic), React SPA
  (TypeScript, Vite, TanStack Query, custom design system — no component
  framework), stdlib-only agent, nginx edge. Eight services on one compose
  network; `make up` builds, boots, migrates and seeds with zero manual steps.
- **Tests**: 368 backend pytest, 113 frontend vitest, and a 10-step Playwright
  journey that walks the real product loop — register → login → enroll a server
  → heartbeat ONLINE → monitor fails → incident opens → email delivered →
  monitor recovers → incident resolves → deploy succeeds → broken deploy fails
  → audit trail → live event stream.
- **Security audit**: an adversarial, multi-agent review produced 26 raw
  findings; 20 survived adversarial verification (3 HIGH, 5 MEDIUM, 12 LOW).
  All 20 were fixed and covered with regression tests. The audit also
  independently surfaced and fixed a further class of defects (see §5).
- **Honest gaps** are listed in §6 — nothing in this report should be read as
  "everything is perfect".

## 2. What was built

### Backend (FastAPI)

~28 entities across infra, observability, delivery, secrets and RBAC domains.
Highlights:

- **Auth**: Argon2id passwords; 15-minute JWT access tokens; opaque refresh
  tokens (SHA-256 at rest) rotated on every use with `SELECT … FOR UPDATE`
  serialization and reuse detection that revokes the session family; lockout
  (5 fails → 15 min) with enumeration-resistant responses; invite-only
  registration after an advisory-locked bootstrap; server-side sessions with
  revocation; hashed, scoped API keys whose effective permission is the
  intersection of key scope and owner role (evaluated *before* the superadmin
  shortcut).
- **RBAC**: DB-backed permission registry, wildcard codenames, four seeded
  roles plus custom roles; every route declares its codename.
- **Agent ingest**: heartbeat endpoint upserts metrics + container inventory;
  servers go OFFLINE after a configurable silence window; enrollment tokens are
  shown once, stored hashed, revocable.
- **Docker management**: host registry with `tcp://` SSRF-guarded endpoints;
  container lifecycle actions and live log streaming over the `container-logs`
  WebSocket channel (real Docker SDK provider or simulation).
- **Monitors → incidents → notifications**: HTTP checks dispatched on a dynamic
  cadence; configurable failure/success thresholds drive DOWN/UP transitions,
  incident open/acknowledge/resolve, and email/webhook deliveries with retries
  (Mailpit as the dev sink).
- **Deployments**: multi-step engine with per-step logs streamed live,
  cancellation and rollback; projects/applications/environments model.
- **Secrets store**: Fernet-encrypted at rest, versioned, resolvable by the
  deployment engine, never returned after creation; HMAC-based change-detection
  digests.
- **Observability**: immutable audit log, system events with dedup, alerts,
  per-server metrics history, five WebSocket channels fanned out through Redis
  pub/sub.
- **Cross-cutting**: single error envelope
  (`{"error":{code,message,request_id}}`), keyset + offset pagination, secret
  redaction, SSRF guards (URL, per-redirect-hop, `tcp://`), fail-closed
  auth rate limiting, security headers (edge + middleware), immutable audit on
  every mutation, `request_id` correlation end to end.

### Frontend (React SPA)

23 pages under a custom design system (no Bootstrap/Tailwind): dashboard with
live event feed, servers + server detail (metrics charts, containers, agent
enrollment, live WS metric stream), containers + detail with log streaming,
docker hosts, projects/applications/environments, deployments + detail with
step logs, monitors + detail, incidents + detail, alerts, events, audit log,
secrets, settings (users & roles, API keys, sessions). `Ctrl/Cmd+K` command
palette, SIMULATION MODE badge, error states and empty states throughout.

### Agent

`agent/nexusops_agent.py` — Python stdlib only, zero dependencies, no shell
execution: heartbeat metrics, container inventory, log tailing. Refuses
cleartext transport unless explicitly overridden; installer writes the token
with `chmod 600` semantics; systemd unit included.

### Infrastructure

`docker-compose.yml`: nginx edge (`:8080`), api, Celery worker (with a real
`celery inspect ping` healthcheck), Celery beat, frontend (built assets),
PostgreSQL (`127.0.0.1:5433`), Redis (`127.0.0.1:6390`), Mailpit (`:8025`).
`SIMULATION_MODE=true` (default) makes the entire platform laptop-runnable —
simulated agents, containers, deployments and monitor targets — with a UI
badge so nobody mistakes simulated data for real. `make up` = build + boot +
wait-for-ready + seed; the API container applies Alembic migrations on start;
seeding is opt-in (`NEXUSOPS_ALLOW_SEED` / `ENVIRONMENT=test`) so no default
credentials ever exist by accident.

## 3. How it was built

The build ran as a series of multi-agent engineering workflows under
continuous integration-by-me: architecture plan → scaffolding → backend
implementation → frontend implementation (23 pages, 7 parallel author agents) →
adversarial review + fixer passes → security audit (5 sweep dimensions ×
adversarial verifiers × fixer) → docs authoring + claim-by-claim consistency
pass → E2E stabilization. Every substantive step was reviewed and verified by
agents separate from the author; test suites were re-run after every fix wave.

## 4. Verification

| Suite | Command | Result |
| --- | --- | --- |
| Backend (unit + integration) | `make test-backend` | **368 passed** (incl. security + E2E-defect regression tests) |
| Frontend unit | `make test-frontend` | **113 passed** (23 files) |
| Playwright journey | `make e2e` | 10-step journey, green (see §5.3 for the defects it flushed out) |
| Lint | `make lint` | ruff clean (147 files formatted); eslint clean |
| Types | `make typecheck` | tsc clean; mypy 0 errors across 115 files (see §5.4) |

The backend integration suite runs against a dedicated `nexusops_test`
database (session-scoped migrations, per-test truncation) so it never touches
the running stack's data. The Playwright journey runs against the real
compose stack through the nginx edge, with Mailpit verified by API.

## 5. Security audit and quality findings

### 5.1 Method

Five sweep dimensions (auth/authz, injection/SSRF, secrets/redaction,
infra/scripts, frontend/transport) each produced candidate findings; every
candidate was independently adversarially verified by a separate agent that
had to reproduce or refute it with evidence; confirmed findings were fixed by
a dedicated fixer pass and re-proven with regression tests.

### 5.2 Results — 26 raw → 20 confirmed, all fixed

Severity split of confirmed findings: **3 HIGH, 5 MEDIUM, 12 LOW**. The three
HIGHs:

1. **API-key scope bypass for superadmin-owned keys** (`app/api/deps.py`) —
   the superadmin shortcut ran before the API-key scope intersection, so a
   least-privilege machine key owned by the superadmin could do anything.
   Fixed by evaluating the scope intersection first; regression tests assert
   a scoped key gets 403 outside its grant.
2. **Redirect-following SSRF in uptime monitors**
   (`app/providers/monitor_transport.py`) — httpx followed redirects
   internally, bypassing the pre-flight SSRF guard. Fixed with
   `follow_redirects=False` + a manual per-hop guard; repro-based regression
   test included.
3. **Known seed superadmin + API key** (`scripts/seed.py`) — the demo
   credential pair was created whenever `ENVIRONMENT != production`, a
   standing backdoor on staging-like deployments. Fixed: seeding outside the
   test environment requires explicit `NEXUSOPS_ALLOW_SEED=1` and generates a
   random one-time password; `scripts/generate_secrets.sh` refuses silent
   secret rotation.

MEDIUMs fixed: refresh-rotation race (row-lock serialization), unsalted
secret digests (now keyed HMAC), monitor probe headers/URL credential echo
(now masked), webhook `display_target` path credentials (now pre-masked),
HSTS never emitted (middleware now production-aware). LOWs included: bootstrap
registration TOCTOU (now advisory-locked), lockout response enumeration,
docker `tcp://` SSRF guard, OpenAPI gating in production, nginx
`server_tokens`, missing SPA CSP, fail-open auth rate limiting, agent install
token window, agent cleartext transport, `--force` defaults, error-log
redaction. Full detail: [security.md §audit](security.md).

### 5.3 Defects found by the E2E journey (and fixed)

The 10-step journey earned its keep — the following were real product bugs,
not test bugs:

- **WebSocket `auth_ok` gate**: the hub never sends that frame, so every live
  stream waited forever. The client now authenticates and subscribes
  immediately after connecting.
- **Stale out-of-band data**: server status, container inventory and the
  incident list were fetched once and never refreshed although heartbeats,
  agent inventory and incident transitions arrive from the worker, not from
  page actions. All three now poll gently (TanStack Query `refetchInterval`)
  on top of their WS-driven invalidation.
- **Deliveries endpoint 500** (`GET /notification-channels/deliveries`): the
  response model required `created_at`, which the delivery table never had —
  every listing crashed with a pydantic `ValidationError`. Fixed with a new
  column + Alembic migration + two regression tests.
- **Deployment trigger 500 on every call** (`POST …/deployments`): the route
  serialized the freshly flushed `Deployment` row, whose `steps` /
  `application` / `environment` relationships were not loaded — the lazy load
  on an `AsyncSession` raised `MissingGreenlet`. The trigger now re-reads the
  row eagerly, matching the cancel/rollback routes. The journey's "deploy
  succeeds" step had been passing against a *seeded* success row; it now
  anchors on the deployment it queued. Regression test added at the HTTP
  layer (the existing engine-level tests never serialized the response, which
  is how this escaped the suite).
- **Deployment detail would 500** (latent sibling of the deliveries bug):
  `DeploymentStepOut` requires `created_at` but `deployment_steps` never had
  timestamp columns — any detail serialization crashed. Fixed with
  `TimestampMixin` + Alembic migration `c7e8b4f2a6d1`.
- **`GET /api/v1/meta` 500 for every non-superadmin**: the route called
  `cast("AsyncAttrs", ctx.user).awaitable_attrs.role` — `cast` is a type-check
  fiction, not a runtime conversion, so the attribute lookup raised
  `AttributeError` for any non-superadmin (the superadmin branch returned
  early, masking the bug in admin-only testing). Consequence: non-admin SPAs
  silently lost their dashboard metadata and permission awareness after
  login. Fixed to read the `selectin`-loaded role directly, mirroring the
  permission loader in `deps`.
- **Refresh-token lost-response race revoked innocent sessions**: a browser
  navigation that aborts an in-flight `POST /auth/refresh` *after* the server
  committed the rotation (nginx logs 499) loses the rotated `Set-Cookie` —
  the next boot replays the already-consumed token, reuse detection revoked
  the whole family, and the user was logged out everywhere. Now an OAuth-BCP
  style grace window (`refresh_grace_seconds`, 30s, one-shot): replay of the
  *immediately* superseded token inside the window is rescued — re-rotated,
  the orphaned successor collapsed into the new chain, audited as
  `auth.token_grace_reuse`; a second or late replay is still theft
  (TOKEN_REUSE + family revocation). Three regression tests cover rescue,
  post-window theft and the disabled-window path.
- **WebSocket origin check rejected same-origin browsers**: browsers always
  send `Origin` on WS handshakes, and the hub only allowed origins from
  `CORS_ORIGINS` — which listed `localhost` while the edge was served at
  `127.0.0.1:8080`. Every browser WS died with a 403 at the edge (a
  close-before-accept surfaces as an HTTP error), so live updates were
  silently broken platform-wide while HTTP worked fine. The hub now allows
  any origin whose netloc matches the request `Host` (same-origin is
  inherently trustworthy); the allowlist still governs cross-origin clients,
  and cross-origin rejection keeps its test.
- **Monitor detail page went stale mid-incident**: it fetched only on mount —
  no `refetchInterval` — so the PENDING badge and "no checks yet" view sat
  frozen while checks ran. Now polls gently (10s) like the other live detail
  pages, on top of WS-driven invalidation.
- **nginx edge went 502 after any container recreation**: static
  `proxy_pass http://api:8000` hostnames are resolved once at config load and
  cached forever — `compose up -d` recreations handed out new container IPs
  and every route through the edge 502'd until nginx restarted. Upstreams now
  resolve at request time via Docker's embedded DNS (`resolver … valid=10s`),
  and `make wait-ready` gates on the SPA *and* the API so journeys never
  start against a half-recreated stack.
- **WS live updates blacked out ~half the time**: the Redis fan-in listener
  used `pubsub.listen()`, which raises on the client's 5s idle socket timeout;
  the handler resubscribed on every idle cycle, and every event published
  during a reconnect gap reached no WebSocket at all — recurring multi-second
  delivery gaps, plus a warning every ~10s per worker. The listener now uses
  a `get_message` loop that keeps ONE subscription open across idle windows
  (real connection failures still resubscribe with backoff).
- **Every live WebSocket crashed on first message-ready connection**
  (`TypeError: unhashable type: 'Connection'`): the hub's `Connection` is a
  dataclass whose generated `__eq__` sets `__hash__ = None`, so the moment a
  live socket was added to the connection set it exploded. Latent since the
  hub was written — the origin bug above rejected browsers before that line,
  masking it. Fix: `eq=False` (identity semantics, which is what a connection
  registry needs anyway). Fixing the origin bug is what exposed it — these
  two had to be found in sequence.
- **The audit trail API 500'd on every non-empty listing**
  (`GET /api/v1/audit-logs`): `AuditOut` accepted `metadata` as a validation
  alias, and `metadata` is a *reserved* attribute on SQLAlchemy declarative
  models — `from_attributes` resolved it to the declarative `MetaData`
  registry object instead of the JSONB column (mapped as `metadata_`), and
  pydantic refused it. Empty results passed, which is how this survived:
  no backend test had ever fetched the listing with rows. Fixed to validate
  from the ORM attribute only (the wire key stays `metadata`), with a
  regression test exercising the actual HTTP path.
- **Notifications duplicated and raced**: the dispatcher runs in *every* API
  worker and Redis pubsub broadcasts each event frame to all of them, so each
  worker queued — and emailed — its own delivery for the same event; and
  frames were published before the event row's transaction committed, so the
  dispatcher's insert raced the commit and FK-failed, silently losing the
  notification (it never reached the retry sweep). Two structural fixes:
  `event_bus.publish` now defers the Redis frame to the session's
  after-commit hook (a rollback drops the frame — phantom events over WS are
  gone too), and a `(channel_id, event_id)` unique constraint + idempotent
  `ON CONFLICT` insert makes double-consumption a no-op (migration dedupes
  the duplicate rows first).
- **Deployments stuck QUEUED forever**: same publish-before-commit disease,
  third site. The trigger path enqueued the Celery task *before* the API
  transaction committed, and the worker's claim query filters on
  `status == QUEUED` — so when the worker won the race it read before the
  row existed, no-op'd in ~4ms (`succeeded in 0.0039s` in the logs), and the
  deployment sat QUEUED until the 5-minute sweep, far past any interactive
  timeout. Whether a given deployment ran was up to a scheduling race, which
  is why earlier E2E runs passed intermittently. The handoff is now deferred
  to the session's after-commit hook like the event bus — and writing the
  regression test exposed a second layer: a stash that survives `rollback()`
  gets flushed by the session's *next, unrelated* commit (my own rollback
  test failed against my first fix, resurrecting a deployment whose row
  never existed). Both stashes now also drop on `after_rollback`; the
  event-bus variant of the same hole got the same fix and its own test.
- **WebSocket 1005 traceback spam**: a client navigating away during the
  auth handshake disconnects with close code 1005, which
  `receive_json()` surfaces as `WebSocketDisconnect` — not in the hub's
  except tuple, so uvicorn printed a scary stack trace for what is a
  routine browser navigation. Harmless, but noise that would have buried a
  real error; the disconnect is now caught and the socket released quietly.
- **Production over plain HTTP was unusable — the login bounce loop**: the
  refresh cookie's `Secure` flag was tied to `ENVIRONMENT=production`
  (`Settings.cookies_secure`), and browsers silently refuse Secure cookies
  over plain HTTP. On the default http://localhost:8080 with production
  settings, every login returned 200 but the session cookie never stuck, so
  the silent refresh failed on the next boot and the SPA bounced back to
  /login forever. The flag now follows the actual transport —
  `X-Forwarded-Proto`, which the nginx edge always overwrites with its own
  scheme (so it is not client-spoofable) — and flips on automatically once
  TLS terminates in front of the edge. Regression-tested at both layers: a
  pure decision function, and the real login route asserting `Secure`
  appears exactly when the edge reports https.
- **A fresh instance had no way to create its first user from the UI**: the
  login page deliberately shipped no sign-up surface (registration is
  invite-only once an owner exists) — but on an empty database the only
  route to the bootstrap owner was a hand-rolled API call, and the E2E
  suite's register branch pointed at a Register tab that did not exist (it
  never ran, because the test stack was always seeded). `/meta` now
  advertises `bootstrap_available` while no user exists, and the login page
  grows a Register tab for exactly that window; the first account becomes
  the Owner superadmin and is signed straight in.

### 5.4 Defects surfaced by driving mypy to zero (and fixed)

The pre-existing backend carried 101 mypy errors. A dedicated fix pass
(four partitioned fixer agents → independent verifier → repair agent, all
gates re-run) took it to **0 errors across 115 files** — and in doing so
flagged several genuine runtime bugs, since a type error that "can't happen"
often means code that never ran:

- **Every search crashed**: 19 call sites used `ilike(pattern, autoescape=…)`
  but SQLAlchemy 2.0's `ilike()` has no `autoescape` parameter — any global
  search or server-list `q` filter raised `TypeError` at runtime. Kwarg
  removed; pattern handling matches the other list filters.
- **The deployment sweep task never ran**: `app/tasks/deployments.py` imported
  an enum from a module that does not re-export it, raising `ImportError` on
  every execution — queued deployments were never picked up by the worker.
  Import corrected; the E2E journey's deploy steps now execute for real.
- **Project detail 500**: pydantic 2.13 removed `model_validate(..., update=)`;
  the route now validates then `model_copy(update=…)`.
- **Server tags 500**: `TagOut` was constructed without `id`/`created_at`,
  which the OutModel contract requires.
- **`/meta` + permission loader `AttributeError`**: `awaitable_attrs` was used
  via a bare `cast` that adds nothing at runtime (see §5.3); both sites now
  read the `selectin`-loaded role directly.
- Plus mechanical fixes: `Field(default=dict)` → `default_factory=dict`, a
  pointless `await` on a sync call, and ~80 typing-only corrections (no
  `# type: ignore` suppressions were added to hide real errors).

The full backend suite (368 tests), ruff and mypy were re-run green after the
pass; nothing was weakened to satisfy the type checker.

## 6. Known limitations (honest list)

- **The mypy gate covers `app/` only** (115 files, zero errors, no
  suppressions). `tests/` carries ~38 pre-existing typing errors — real but
  cosmetic (fixture typing, stub shapes) — and was left outside the gate
  rather than papered over with suppressions.
- **No fleet-wide metrics history endpoint yet** — the dashboard shows live
  counters and events but charts nothing fleet-wide; per-server timeseries
  live on each server's detail page.
- **`make dev` (hot-reload overlay) is broken at build time** — it targets a
  `develop` stage the frontend Dockerfile does not define and mounts a
  nonexistent `nginx/dev.conf`. Interim path documented in
  [development.md §4.2](development.md); fix tracked as follow-up work.
- **Rate limiting nuance**: the fail-closed auth limiters fall back to an
  in-process fixed window during a Redis outage — enforced, but approximate
  across multiple workers; general limiters deliberately fail open.
- **Secrets encryption is app-layer at rest (Fernet) with disk-level
  encryption left to the host volume**; envelope rotation tooling is future
  work.
- **The agent trusts the platform** for poll intervals and log-tail scope; a
  compromised platform can direct agents to read any container logs visible
  to their Docker socket — by design, but worth knowing.
- **Single-node compose** — no HA story, no external TLS (terminate TLS in
  front of the edge; HSTS is emitted when `ENVIRONMENT=production`).
- **E2E seeding contract**: `make e2e` expects the fixed test credentials,
  which only `ENVIRONMENT=test` seeding creates; against a database seeded in
  `development` (random one-time password) the journey would need its
  bootstrap fallback on a truly fresh database. Documented in
  [development.md §6](development.md).
- **Webhook display targets and monitor URLs are masked in responses**, but
  the underlying values remain visible to platform admins by design (they are
  platform configuration, not per-tenant secrets).

## 7. Reproducing the results

```bash
cp .env.example .env          # set POSTGRES_PASSWORD; ENVIRONMENT=test for E2E
make up                       # build + boot + migrate + seed
make test                     # backend unit + frontend vitest
make test-backend             # full backend suite (needs stack up)
make e2e                      # Playwright journey (needs stack up)
make lint && make typecheck   # ruff/eslint + mypy/tsc
```

Seeded demo data (5 servers, monitors with a flaky probe, a project with an
application + production environment, deployments, an email channel) appears
after `make up`; the admin password is printed once on stderr
(`ENVIRONMENT=test` uses the documented deterministic pair).

## 8. If I had another week

1. Fleet-wide metrics rollups + dashboard charts.
2. Fix the dev overlay properly (`develop` Docker stage + dev nginx conf).
3. Notification escalation policies (repeat reminders, on-call rotations).
4. Per-tenant envelope encryption keys for the secrets store.
5. OpenTelemetry traces across api → worker → providers.
