# NexusOps Troubleshooting Runbook

Symptom → cause → fix guides for the common failure modes of a composed NexusOps
stack (`docker-compose.yml`, driven by the repo `Makefile`). Every command below
runs from the repo root unless noted.

## 1. How to read this runbook

Start every investigation with three commands:

```bash
docker compose ps                 # health state per service
docker compose logs api           # or: make logs (tails every service)
curl -fsS http://127.0.0.1:8080/api/v1/ready | jq .   # dependency-level readiness
```

Keep the three health surfaces apart — they answer different questions:

| Probe | Where | Answers |
|---|---|---|
| compose healthcheck | container-internal `http://127.0.0.1:8000/health` (`docker-compose.yml` `api.healthcheck`) | "Is the uvicorn process serving at all?" (liveness only — no dependency checks) |
| `GET /api/v1/ready` | through the edge | "Can the API reach Postgres and Redis?" — 503 with `components.database` / `components.redis` error names when not (`backend/app/api/v1/health.py`) |
| `GET /health` on :8080 | nginx edge | Nothing about the stack: `nginx/default.conf.template` answers `return 200 "edge ok\n"` locally, without proxying. Useful only to prove nginx itself is up |

All API failures use the envelope `{"error":{"code","message","request_id"}}`
(`backend/app/core/errors.py`). When you escalate a problem, include the
`request_id` — it is present on every log line for that request.

### Stack topology and ports

```mermaid
flowchart LR
    subgraph host["Host machine (published ports)"]
        B["Browser / curl / make targets"]
        P5433["127.0.0.1:5433"]
        R6390["127.0.0.1:6390"]
        M8025["127.0.0.1:8025 (Mailpit UI)"]
        V5173[":5173 (Vite, dev profile — all interfaces)"]
    end
    E["nginx edge<br/>:8080 published"]
    A["api (uvicorn :8000)"]
    W["worker (celery)"]
    S["scheduler (beat)"]
    F["frontend"]
    PG[("postgres<br/>internal :5432")]
    RD[("redis<br/>internal :6379")]
    MP[("mailpit<br/>SMTP :1025 internal only")]

    B --> E
    E -- "/api/ → api:8000" --> A
    E -- "/ → frontend:8080" --> F
    V5173 -- "proxies /api → 127.0.0.1:8080" --> E
    P5433 --> PG
    R6390 --> RD
    M8025 --> MP
    A --> PG
    A --> RD
    A -- "SMTP mailpit:1025" --> MP
    W --> PG
    W --> RD
    S --> RD
```

Two namespaces matter constantly:

- **Inside the compose network**, services address each other by name on
  internal ports: `postgres:5432`, `redis:6379`, `mailpit:1025` (these are the
  defaults in `.env.example` and are what the containers use).
- **From the host**, the published ports are: `5433`, `6390` and `8025`
  bound to loopback (`127.0.0.1`), while `8080` and (dev profile) `5173` are
  published on **all interfaces** (`docker-compose.yml` `ports:`,
  `.env.example` "Ports" section). `postgres` and `redis` are *not*
  resolvable from the host.

---

## 2. API container unhealthy on first boot

**Symptom.** `docker compose ps` shows `api` as `unhealthy` (or
`Restarting`) right after `make up`; `make up` then fails at `wait-ready` with
`API did not become ready in time`. Postgres and redis are healthy.

**Diagnose.**

```bash
docker compose logs api | tail -50
docker inspect --format '{{json .State.Health.Log}}' nexusops-api-1 | jq .
```

**Cause A — an import-time `ModuleNotFoundError` (the email-validator class of
bug).** The API's request schemas annotate email fields with pydantic `EmailStr`
(`backend/app/schemas/auth.py`, `backend/app/schemas/user.py`), and pydantic
resolves that type only if the `email-validator` package is importable. If the
dependency is missing from the image, uvicorn dies the moment `app.schemas` is
imported, the container's healthcheck (`python -c "... urlopen(.../health)"`)
never sees a 200, and the service flips unhealthy. The fix pattern — which the
repo applied for this exact case by declaring `pydantic[email]>=2.11` in
`backend/pyproject.toml` (pinned in `backend/uv.lock` as `email-validator`) —
is:

1. Add the dependency (with the correct extra) to `dependencies` in
   `backend/pyproject.toml`.
2. Refresh the lockfile and your local venv: `cd backend && uv lock && uv sync`.
   The image builds with `uv sync --frozen --no-dev` (`backend/Dockerfile`), so
   a stale `uv.lock` means the fix never reaches the container — the lockfile
   change is mandatory, not optional.
3. Rebuild: `docker compose build api worker scheduler` (all three share one
   image), then `make up`.

Do not "fix" this by pip-installing into a running container — the next rebuild
silently loses it.

**Cause B — invalid configuration.** `backend/app/core/config.py` validates
settings at import and `fail_on_bad_config()` prints
`[nexusops] Invalid configuration: …` and exits with code 2 *before* serving.
Common triggers: `JWT_SECRET` shorter than 32 chars, `ENCRYPTION_KEY` that is
not a valid Fernet key, a bad `LOG_LEVEL`. The log output names the offending
variable and the generator command (`openssl rand -hex 32`,
`./scripts/generate_secrets.sh`). Fix `.env`, restart the service.

**Cause C — postgres refuses to start at all.** `docker-compose.yml` requires
`POSTGRES_PASSWORD` (`:?set POSTGRES_PASSWORD in .env`); compose aborts before
any service starts if it is unset. Copy `.env.example` to `.env` first.

---

## 3. Worker container stays unhealthy

**Symptom.** `worker` shows `unhealthy` in `docker compose ps` even though
`docker compose logs worker` shows a normal celery startup (`ready`), and tasks
appear to run.

**Cause.** The healthcheck targets one specific celery node by name:

```yaml
# docker-compose.yml, worker.healthcheck
test: ["CMD-SHELL", "celery -A app.tasks.celery_app:app inspect ping -d celery@$$HOSTNAME --timeout=8"]
```

`celery inspect ping -d celery@<name>` only replies from the node whose
nodename matches. Nodenames are derived from the container hostname
(`celery@$HOSTNAME`), so the `$HOSTNAME` expansion **must happen inside the
container shell at check time**. The `CMD-SHELL` form does that. The plain
array form (`test: ["CMD", "celery", ..., "-d", "celery@$HOSTNAME"]`) passes
`$HOSTNAME` through literally, `-d celery@$HOSTNAME` matches no node, celery
reports `No nodes replied within time constraint`, and the container is marked
unhealthy forever. `docker-compose.yml` carries a comment on exactly this trap —
preserve it.

**Diagnose / fix.**

```bash
docker inspect --format '{{json .State.Health.Log}}' nexusops-worker-1 | jq .[-1]
# "Output" containing "No nodes replied" → the target name never matched
docker compose exec worker celery -A app.tasks.celery_app:app inspect ping
```

If the ping answers `celery@<id> -> pong`, the worker is fine and the
healthcheck form is the problem: keep `CMD-SHELL` with `$$HOSTNAME` (double
`$` in compose is correct — one `$` is consumed by compose interpolation).

Timing expectations so you do not chase a non-problem: interval 30s, timeout
10s, retries 5, `start_period` 20s — the worker can legitimately sit in
`health: starting` for roughly two minutes after boot. The `scheduler` (beat)
service deliberately has **no** healthcheck; it will always look plain
`running`. Related note: the beat entry `simulation-tick` (every 20s) is the
driver of the simulated fleet and self-disables when `SIMULATION_MODE` is not
`true` (`backend/app/tasks/celery_app.py`) — with simulation off, expect quiet
metrics unless real agents are enrolled.

---

## 4. Login returns 422 instead of "invalid credentials"

**Symptom.** `POST /api/v1/auth/login` answers HTTP 422 with
`code: "VALIDATION_ERROR"` and details on the `body.email` field, before any
password check happens:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "request_id": "…",
    "details": [{
      "loc": ["body", "email"],
      "msg": "value is not a valid email address: The part after the @-sign is a special-use or reserved name that cannot be used with email.",
      "type": "value_error"
    }]
  }
}
```

**Cause.** `LoginRequest.email` is a pydantic `EmailStr`
(`backend/app/schemas/auth.py`), which runs the `email-validator` library at
request-parse time. That library rejects reserved/special-use domains.
Verified against the pinned versions (`pydantic` 2.13.4, `email-validator`
2.3.0, `backend/uv.lock`):

- **Rejected as special-use or reserved:** addresses under the TLDs `.test`,
  `.invalid`, `.local`, `.localhost`, `.onion`, `.arpa` — *including their
  subdomains* (e.g. `ops@mx.server.test`, `a@thing.arpa`), and dotless hosts
  such as `ops@localhost`.
- **Accepted:** `admin@nexusops.example.com` (the seeded admin),
  `ops@example.com`, and even `user@nexusops.example` — `email-validator`
  deliberately does *not* treat the RFC 6761 `example` family as special (see
  the commented-out entries in its `SPECIAL_USE_DOMAIN_NAMES`).

So the seeded address `admin@nexusops.example.com`
(`backend/scripts/seed.py`, `ADMIN_EMAIL`) survives validation by design; the
422 bites when accounts use lab-style mail domains such as `.test`, `.local`
or `.arpa` subdomains. The fix is to send an address on a routable domain —
there is no configuration switch to relax it.

Note the practical consequences: a 422 happens during request validation, so it
does **not** touch the lockout counters, the audit log, or the login rate
limiter — only syntactically valid emails can produce those.

---

## 5. Port conflicts on 8080 / 5433 / 6390 / 8025 / 5173

**Symptom.** `docker compose up` fails with
`Error starting userland proxy: listen tcp4 0.0.0.0:8080: bind: address already in use`
(or the same for another port), or the UI loads but API calls fail.

**Diagnose.**

```bash
sudo lsof -i :8080 -sTCP:LISTEN      # repeat for 5433, 6390, 8025, 5173
docker compose ps                     # is it your own previous stack?
```

**Cause / fix.** Every host port is a knob in `.env.example`; override it there
and `docker compose up -d` again:

| Knob | Default | Notes |
|---|---|---|
| `NEXUSOPS_HTTP_PORT` | 8080 | nginx edge — the UI and `/api` |
| `NEXUSOPS_POSTGRES_PORT` | 5433 | bound to `127.0.0.1` only |
| `NEXUSOPS_REDIS_PORT` | 6390 | bound to `127.0.0.1` only |
| `NEXUSOPS_MAILPIT_HTTP_PORT` | 8025 | Mailpit web UI |
| `NEXUSOPS_VITE_PORT` | 5173 | dev profile only (`docker-compose.dev.yml`) |

Two follow-throughs when you change `NEXUSOPS_HTTP_PORT`:

1. **Vite dev proxy targets the edge by absolute URL.**
   `frontend/vite.config.ts` proxies `/api` to `http://127.0.0.1:8080` —
   update that constant too, or the dev UI serves a page whose API calls fail.
2. **CORS is origin-allowlisted.** `CORS_ORIGINS` in `.env.example` lists
   `http://localhost:8080` and `http://localhost:5173`; the API enforces it
   with credentials (`backend/app/main.py`). A browser on a moved port gets
   CORS-rejected requests until you add the new origin to `CORS_ORIGINS`.

The container-internal ports never change — `api` always talks to
`postgres:5432` / `redis:6379` via the environment compose injects
(`docker-compose.yml` `api.environment`), so moving host ports does not affect
the running stack, only host-side tooling (see section 9).

---

## 6. `make up` fails with "API did not become ready in time"

**Symptom.** The build succeeds, containers start, but the `wait-ready` step
(`Makefile` — it polls `http://127.0.0.1:8080/api/v1/ready` every 2s for 60
attempts, ≈2 minutes) times out and `make up` exits 1 before seeding.

**Diagnose.**

```bash
docker compose ps
curl -s http://127.0.0.1:8080/api/v1/ready | jq .
docker compose logs api | tail -100
```

The `/ready` response tells you which dependency is broken —
`components.database: "error: OperationalError"` means Postgres connectivity,
`components.redis: "error: …"` means Redis (`backend/app/api/v1/health.py`).

```mermaid
flowchart TD
    W["make up: wait-ready failing"] --> P{"docker compose ps: api state?"}
    P -- "unhealthy / restarting" --> L["docker compose logs api"]
    L --> C1{"ModuleNotFoundError?"} -- yes --> F1["Section 2: declare dep + uv lock + rebuild"]
    L --> C2{"Invalid configuration?"} -- yes --> F2["Fix .env (JWT_SECRET / ENCRYPTION_KEY)"]
    L --> C3{"alembic error in output?"} -- yes --> F3["Section 7: DB out of sync"]
    P -- "healthy but /ready 503" --> R{"components?"}
    R -- "database: error" --> F4["Check postgres: logs, password, volume"]
    R -- "redis: error" --> F5["Check redis container + REDIS_URL"]
    P -- "curl: connection refused on 8080" --> F6["Section 5: port conflict / nginx not up"]
```

Calibrate your patience: the api healthcheck allows `start_period` 15s plus 12
retries at 10s intervals, so a normal cold start consumes a good chunk of the
`wait-ready` budget before anything is wrong. `make up` also runs
`wait-ready` *before* `seed`, so a timeout always means the API is genuinely
not serving — seeding has not been attempted yet.

If `docker compose logs api` shows the entrypoint line
`[nexusops] applying database migrations...` followed by an alembic traceback,
the migration failed and nothing after it will come up — go to section 7.

---

## 7. Database out of sync (migrations)

**Symptom.** API logs show alembic errors at boot, or `/ready` fails on the
database component, or a fresh feature errors with "relation does not exist".

**Diagnose.**

```bash
# Against the container — it already carries the correct DATABASE_URL:
docker compose exec api alembic current
docker compose exec api alembic heads
```

`current` below `head` (or `None` on an empty database) means the schema is
behind. Today there is a single head: `b5866787bde4` (initial schema,
`backend/alembic/versions/`).

**Fix.**

```bash
make migrate        # alembic upgrade head from the host (Makefile)
```

Who migrates what: the `api` container runs `alembic upgrade head` on start via
`backend/docker-entrypoint.sh`, so a plain `docker compose up` auto-migrates.
`worker` and `scheduler` run with `RUN_MIGRATIONS_ON_START: "false"` and are
gated on the api healthcheck in compose, so **the api is the only migrator**.
Implications:

- If the api fails its migration, it never turns healthy, and `worker` /
  `scheduler` never start at all (they wait on `api: condition: service_healthy`).
  Fix the api first; the rest follows.
- New migrations must be committed for image rebuilds: the Dockerfile copies
  `alembic/` into the image, so a migration that exists only on your disk is
  invisible to a rebuilt container.
- To author one: `make makemigrations m="describe change"` (also host-side,
  stack up).

---

## 8. E2E suite fails (`make e2e`)

**Symptom.** `make e2e` (which runs `cd frontend && npx playwright install
chromium; npx playwright test`) reports connection refused, a bootstrap
failure, or timeouts.

**Preconditions.** The Playwright config (`frontend/playwright.config.ts`)
targets `http://127.0.0.1:8080` — the composed stack, workers = 1, 120s test
timeout. It is not a unit suite; run it against a live stack. The fixture
(`frontend/e2e/fixtures.ts`) logs in first as `admin@nexusops.example.com` /
`nexusops-admin` and only falls back to registering (bootstrapping the first
Owner on an empty `users` table) if that login fails.

| Failure | Cause | Fix |
|---|---|---|
| `Error: connect ECONNREFUSED 127.0.0.1:8080` | stack down or edge port moved | `make up`; if you moved `NEXUSOPS_HTTP_PORT`, `baseURL` in `playwright.config.ts` must change too |
| `bootstrap register failed: 403 … INVITATION_REQUIRED` | the database has users, but the seeded admin's password is not `nexusops-admin`. This happens with the default `ENVIRONMENT=development`: `make seed` then generates a **random one-time password** instead of the deterministic one (`backend/scripts/seed.py`, `_seed_credentials` — the `nexusops-admin` pair exists only when `ENVIRONMENT=test`), and on an already-seeded DB `make seed` skips entirely (`seed_skipped`) | set `ENVIRONMENT=test` in `.env`, then `make clean && make up` (drops all data, re-seeds deterministically). Alternatively wipe to an empty DB and let the fixture's register call bootstrap the admin itself |
| `Invalid email or password` on the *first* fixture login, then the same via register | same root cause as above (or the lockout in section 11) | as above |
| Browser executable missing | Playwright browser not installed | `cd frontend && npx playwright install chromium` (`make e2e` attempts this itself) |
| Random mid-journey 401s | access token expired mid-test (15 min TTL default) — rare at 120s test timeout; more often it signals the API restarting under the suite | check `docker compose ps` for restart loops before blaming the test |

For a fully deterministic run the config header recommends
`make clean && make up` first — `make clean` is destructive (drops the
`pgdata` volume). Note vitest does *not* collect `frontend/e2e/**` (excluded in
`frontend/vite.config.ts`) — a failing E2E spec never shows up in
`make test-frontend`.

---

## 9. Host scripts cannot reach Postgres / Redis

**Symptom.** Running a backend script or pytest from your laptop fails with
name-resolution or connection errors like
`Connect call failed - getaddrinfo failed for postgres` or
`Error -2 connecting to redis:6379`.

**Cause.** Two namespaces, one trap:

- Inside compose: `postgres:5432`, `redis:6379` — these are the defaults in
  `.env.example` (`POSTGRES_HOST=postgres`, `REDIS_URL=redis://redis:6379/0`)
  because that file feeds the *containers*.
- From the host: only the published loopback ports exist —
  `127.0.0.1:5433` and `127.0.0.1:6390` (`docker-compose.yml` publishes
  `127.0.0.1:${NEXUSOPS_POSTGRES_PORT:-5433}:5432` etc.).

The `Makefile` encodes exactly this at the top (`PG_URL`, `REDIS` — "Host-run
connections (containers use the compose network instead)") and passes them into
`make migrate`, `make seed`, and `make test-backend` (integration tests run
against those same dockerized instances). If you bypass those targets, you must
override both URLs yourself. Watch a second trap: the backend `Settings` object
also reads `../.env` when run from `backend/`
(`backend/app/core/config.py`), so a script that does not get an explicit
`DATABASE_URL` inherits the container-internal hostnames and fails from the
host.

**Fix.**

```bash
# Match the Makefile (adjust credentials to your .env):
export DATABASE_URL="postgresql+psycopg://nexusops:change-me-postgres@127.0.0.1:5433/nexusops"
export REDIS_URL="redis://127.0.0.1:6390/0"
# or simply use the make targets, which wire these for you
```

The published ports are loopback-only by design, so this works from the same
machine and nothing is exposed to the network. If the postgres URL is rejected
with authentication failure, the password must equal `POSTGRES_PASSWORD` from
`.env` — it is required for the stack to start at all.

---

## 10. Mailpit UI shows no email

**Symptom.** You expected a notification email; http://127.0.0.1:8025 is empty.

**Diagnose, in order:**

1. Was a notification actually produced? Check `docker compose logs worker`
   for delivery errors (the sender raises `NotificationError` on SMTP failure,
   `backend/app/providers/notification_sender.py`) and look at the
   notifications state in the UI/API. Failed sends are retried by the beat
   entry `retry-notifications` every 60s (`backend/app/tasks/celery_app.py`).
2. Is the dispatcher running? It is an in-API background loop started in the
   app lifespan (`backend/app/main.py` →
   `notification_service.dispatcher_loop`); an API that is crash-looping
   dispatches nothing.
3. TLS mismatch: Mailpit speaks plain SMTP; `SMTP_TLS=true` would make the
   sender attempt STARTTLS and fail. Keep `SMTP_TLS=false` for Mailpit
   (default in `.env.example`).

**Cause (the common one): wrong host/port namespace.** Compose injects
`SMTP_HOST: mailpit` into `api`/`worker`/`scheduler`
(`docker-compose.yml`), overriding whatever is in `.env`, and the port is the
settings default `SMTP_PORT=1025` (`backend/app/core/config.py`). Both names
resolve **only inside the compose network**. Mailpit's SMTP listener on 1025 is
*not published to the host* — only the HTTP UI on 8025 is — so a host-side
script pointed at `127.0.0.1:1025` will never connect, and that is not the
API's problem.

**Fix.** For platform-generated mail, nothing to do beyond ensuring
`SIMULATION_MODE`/monitors actually fire events; verify via the UI on :8025. If
you need to inject test mail *from the host*, add a publish mapping to the
`mailpit` service in `docker-compose.yml`:

```yaml
    ports:
      - "127.0.0.1:${NEXUSOPS_MAILPIT_HTTP_PORT:-8025}:8025"
      - "127.0.0.1:${NEXUSOPS_MAILPIT_SMTP_PORT:-1025}:1025"   # optional, host-side injection only
```

(`NEXUSOPS_MAILPIT_SMTP_PORT` already exists in `.env.example`; as shipped it is
not wired to a port mapping — that is a deliberate minimal surface, not a bug.)

---

## 11. Seeded admin locked out after failed logins

**Symptom.** Logging in as `admin@nexusops.example.com` returns 401 with
`code: "INVALID_CREDENTIALS"` and the message `Invalid email or password` —
*even with the correct password*.

**Important:** there is no client-visible "account locked" response. The login
flow (`backend/app/services/auth_service.py`) deliberately answers lockouts
with the **same generic envelope** as unknown users and bad passwords — a
distinct response would let an attacker enumerate registered emails. The lock
detail (reason `account_locked`, `ACCOUNT_LOCKED` code, minutes remaining) is
written only to the server-side audit/event trail.

**Cause.** Every bad password increments `users.failed_login_attempts`
(`backend/app/models/identity.py`); at `LOGIN_MAX_ATTEMPTS` (default **5**,
`.env.example`) it sets `users.locked_until = now + LOGIN_LOCKOUT_SECONDS`
(default **900 s = 15 minutes**) and flips `users.status` to `LOCKED`
(`backend/app/models/enums.py`). A separate, unrelated limiter also exists:
more than 10 login *requests* per minute from one IP gets 429 `RATE_LIMITED`
with a `Retry-After` header (`backend/app/core/rate_limit.py`, `auth_limiter`)
— that one clears by itself and does not lock the account.

**How to confirm it is a lockout, not a wrong password:** you were failing
logins right before (5+ attempts), or the audit trail shows
`reason=account_locked`. Then pick one:

1. **Wait.** The lockout is time-boxed; after 15 minutes a successful login
   resets `failed_login_attempts` and `status` automatically.
2. **Reset the row directly** (dev/staging, destructive only to lockout state):

   ```bash
   docker compose exec postgres psql -U nexusops -d nexusops -c \
     "UPDATE users SET failed_login_attempts = 0, locked_until = NULL, status = 'ACTIVE' \
      WHERE email = 'admin@nexusops.example.com';"
   ```

3. **Nuclear reset of the dev database** (destroys all data):

   ```bash
   docker compose down -v     # or: make clean (drops the pgdata volume)
   make up                    # rebuilds, waits for readiness, re-seeds
   ```

   `make up` re-runs `make seed` at the end, which recreates the admin — the
   seed is guarded by a Postgres advisory lock and skips (`seed_skipped`) when
   any user already exists, which is why a plain re-seed cannot fix a used
   database. Password discipline after a reset: under `ENVIRONMENT=test` the
   deterministic dev credentials apply (`admin@nexusops.example.com` /
   `nexusops-admin` — dev/test only, `backend/scripts/seed.py`); under the
   default `ENVIRONMENT=development` the seed prints a **random one-time
   password to stderr** (`make up` reminds you of this) and it is never shown
   again. Remember `docker compose up` alone migrates but **does not seed** —
   that is deliberate so production never gets default credentials.

---

## 12. Login succeeds but the session drops after every reload

**Symptom.** `POST /api/v1/auth/login` returns 200 and the UI works, but after
a page reload (once the 15-minute access token expires) you are logged out and
the refresh call fails.

**Cause.** The refresh token lives in an HttpOnly cookie
(`nxo_rt`, `backend/app/services/auth_service.py`) whose `Secure` flag follows
`ENVIRONMENT`: `cookies_secure` is true in `production`
(`backend/app/core/config.py`). Browsers refuse to store `Secure` cookies over
plain HTTP, and the composed stack serves plain HTTP on :8080 — so in
`ENVIRONMENT=production` behind no TLS, the cookie is silently discarded.

**Fix.** Run with `ENVIRONMENT=development` when testing over
`http://localhost:8080`, or put real TLS in front of nginx in production. This
is intentional fail-safe behavior, not a bug to work around by editing the
cookie flags.

---

## 13. Known rough edges (honest limitations)

- **`make dev` (dev profile) is currently broken at build time.**
  `docker-compose.dev.yml` builds the `frontend` service with `target: develop`,
  but `frontend/Dockerfile` defines only the `build` and `runtime` stages —
  compose fails with a missing-target error before anything starts. On top of
  that, the same file bind-mounts `./nginx/dev.conf` over the nginx template,
  and `nginx/` contains only `default.conf.template` and a `Dockerfile` — on
  Linux, Docker would materialize the missing source as an empty directory and
  nginx would start without a usable config. Until a `develop` stage and
  `nginx/dev.conf` are added, use `make up` (the production-shaped stack) for
  local work.
- **No host-side SMTP endpoint by default.** See section 10 — Mailpit's SMTP
  port is internal-only as shipped.
- **First-admin bootstrap and seeding do not compose after the fact.** The
  first account bootstraps only while the `users` table is empty
  (`backend/app/services/auth_service.py` — `INVITATION_REQUIRED` otherwise),
  and `make seed` skips whenever any user exists. If someone registered before
  you ran `make seed`, the seeded admin will never appear on that database —
  reset with `make clean && make up` (section 11).
- **No simulator without the worker.** The simulated fleet, simulated monitor
  probes and simulated deployments are driven by celery beat / worker tasks
  (`backend/app/tasks/simulation.py` via the `simulation-tick` and monitor
  sweeps in `backend/app/tasks/celery_app.py`). If the `worker` or `scheduler`
  container is down, servers go `OFFLINE` after
  `SERVER_OFFLINE_AFTER_SECONDS` (default 90s) and monitors stop checking even
  though `SIMULATION_MODE=true` and the UI shows the SIMULATION MODE badge
  (`frontend/src/components/Layout.tsx`) — check `docker compose ps` before
  assuming the platform is broken.
