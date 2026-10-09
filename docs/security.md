# NexusOps Security Guide

How NexusOps protects credentials, tenants, and infrastructure — what is enforced in
code, what was verified by the security audit (2026-09), and which limits remain.
Every control named here points at the module that implements it.

## Threat model in one paragraph

NexusOps holds the keys to infrastructure: user credentials, agent enrollment tokens,
deployment secrets, Docker endpoints, and notification-channel credentials. The
adversaries considered are (1) an internet attacker probing the edge, (2) a malicious
or compromised *agent* host, (3) a curious *operator* inside the platform who should
see less than an owner, (4) a leaked API key or token, (5) SSRF pivoting through
platform features that fetch user-supplied URLs, and (6) **a legitimate member of
one organization reaching another organization's data** — with a known object id, a
crafted header, a search term, a WebSocket subscription, a background job or a raw
SQL statement. Out of scope: host-level compromise of the server running the compose
stack, and physical access.

## Authentication and sessions

| Control | Implementation |
| --- | --- |
| Password hashing | Argon2id (`PasswordHasher()` defaults: m=64 MiB, t=3, p=4) — `backend/app/core/security.py` |
| Access tokens | JWT, 15-minute TTL (`access_token_ttl_minutes`) |
| Refresh tokens | Opaque, 14-day TTL, **rotated on every use**; rotation locks the row (`with_for_update`) and only supersedes it when still current, so a replayed refresh token is detected and the whole family revoked. One bounded exception (OAuth BCP-style grace): a replay of the *immediately* superseded token within `refresh_grace_seconds` (30s, one shot per token, audited as `auth.token_grace_reuse`) is rescued instead — a browser navigation can abort an in-flight refresh after the server committed the rotation, losing the response cookie; a second replay, or one after the window, is theft again — `backend/app/services/auth_service.py` |
| Brute force | 5 failed logins (`login_max_attempts`) locks the account for 15 minutes (`login_lockout_seconds`) |
| Enumeration resistance | Locked accounts, unknown accounts and wrong passwords all return the same generic `Invalid email or password` (`_INVALID_CREDENTIALS_MESSAGE`); lock details stay server-side |
| Registration | Open only until the first user exists (bootstrap); afterwards **invite-only**. The count-then-create bootstrap decision runs inside a `pg_advisory_xact_lock`, so two concurrent registrations cannot both claim owner — `auth_service.py` |
| Sessions | Server-side session rows; users list and revoke their sessions, and password change revokes others |
| API keys | Hashed at rest, shown once at creation, and **scoped**: an API key's effective permission is the intersection of its scope grant and the owner's role. The scope check runs *before* the superadmin shortcut, so even a superadmin-owned key can never exceed its grant — `backend/app/api/deps.py` |

## Authorization (RBAC)

Roles are `Owner`, `Admin`, `Operator`, `Developer`, `Viewer` — five, mapped to
wildcard permission strings in `backend/app/core/permissions.py` (30 codenames,
now under the `node.*` naming; the planned `Operator` → `DevOps` rename and the new
codenames in `authorization.md` §2 are **not** in this release). Every route declares the codename
it requires; `has_permission` evaluates wildcard matches plus the API-key
intersection above.

**Authority is per organization.** The permission set comes from the caller's
`Membership.role` **in the active organization** (`app/api/deps.py`,
`_load_permissions`), not from a single account-level role: the same person is an
Admin in one tenant and a Viewer in another, and no active membership means no
authority at all. `User.is_superadmin` remains an instance-operator escape hatch,
but it does not widen tenancy: a superadmin still has to name an organization they
belong to, and the header is validated against their memberships on every request.
Object-ownership boundaries are enforced in the service layer queries, never in the
frontend.

## Tenant isolation (Phase 1)

Tenant boundaries are enforced by three independent nets, and the design intent is
that **any one of them alone would still hold** — `docs/multi-tenancy.md` is the
full record:

1. **SQLAlchemy session guard** (`app/core/tenancy.py`, a `do_orm_execute`
   listener). Every ORM SELECT that touches an organization-owned table is filtered
   to the active organization. Unscoped DML, bulk `UPDATE`/`DELETE` without an
   `org_id` predicate, and Core/raw statements are **refused** (a
   `TenancyScopeError`, i.e. a 500), because SQLAlchemy's loader criteria do not
   apply to them and a silent unfiltered write is worse than a loud failure. A
   `before_flush` listener stamps `org_id` on new rows and rejects a row that tries
   to change hands between tenants.
2. **PostgreSQL row-level security.** Tenant tables carry `USING` **and**
   `WITH CHECK` policies keyed on `app.current_org`, re-issued at every transaction
   boundary. The runtime connects as `nexusops_app` (`NOSUPERUSER NOBYPASSRLS`,
   not the table owner), so the policies bind; migrations run as
   `nexusops_owner` and never serve request traffic. An unset or malformed GUC
   denies everything rather than erroring mid-query, and the application refuses to
   start against an owner DSN.
3. **Membership checks at every entry point.** `X-Org-Id` is validated against the
   caller's active memberships (`memberships` is deliberately RLS-exempt precisely
   because that validation is a cross-organization read); API keys are bound to the
   organization they were created in and the header is ignored for key auth; a WS
   socket is bound to one organization at connect time and every subscribe frame
   re-checks both permission and organization; agent tokens resolve to exactly one
   node and that node's organization; worker tasks either claim a row and resolve
   its organization (`org_for`) or run their claim under a logged, allowlisted
   system scope.

**Surfaces with no `org_id` column** — `users`, `sessions`, `refresh_tokens` — are
bounded by the **membership of the row's owner** instead: the user directory, the
single-user read, member updates/removal, the session listing and session
revocation all intersect with the active organization's members, and a row outside
it is reported *not found* (indistinguishable from a non-existent id, so the API
is not an existence oracle). Three consequences worth stating plainly:

- Tenant member management cannot disable an account or revoke its credentials —
  those are instance-wide, and using them to punish one tenant's member would be a
  cross-tenant denial of service. `DELETE /users/{id}` suspends the **membership**.
- A suspended membership is not authority: `X-Org-Id` validation reads only active
  memberships, so the removed member immediately loses that organization and keeps
  every other one.
- The last active member of an organization cannot be removed
  (`LAST_MEMBER_PROTECTED`), the multi-tenant successor to the last-superadmin
  guard.

**What is deliberately RLS-exempt** (five tables, enumerated in
`app.core.tenancy.RLS_EXEMPT_ORG_TABLES`): `organizations` (the tenant itself),
`memberships` (read before an organization is known), `api_keys` and
`agent_credentials` (a credential hash has to resolve before the tenant is known —
the row's own `org_id` is then the boundary), and `roles` (instance-wide templates
in v1). This class has **no database-level tenancy net**; the `system_scope`
module allowlist is the fence, and `tests/unit/test_tenancy_allowlist.py` fails if a
module outside that allowlist opens a system scope.

**Verification.** `backend/tests/integration/test_tenant_isolation.py` is the exit
gate: IDOR (read, update, delete, search, session, agent, operation) across two
organizations that differ *only* in `X-Org-Id`; raw-SQL RLS probes connecting as
`nexusops_app` with no ORM and no guard; a catalog test asserting every table with
an `org_id` column has a policy; unscoped-access, bulk-DML/Core-rejection and
identity-map cross-scope tests; Redis frame delivery; worker sweeps; and an
append-only check on the audit trail. 437 backend tests and 172 frontend tests pass.

## Second security review — multi-tenancy (2026-09-24)

An independent pass over the tenancy change set, aimed specifically at IDOR, broken
access control, tenant confusion, raw-SQL/RLS bypass, WebSocket and worker
authorization, Redis cross-tenant delivery, agent impersonation, operation replay
and privilege escalation. Two confirmed cross-tenant defects were found and fixed in
this change set; both are covered by tests.

| # | Severity | Finding | Fix |
| --- | --- | --- | --- |
| 1 | HIGH | `GET /users` and `GET /users/{id}` selected from `users` without a tenant predicate. `users` is instance-level (Membership is the boundary), so any member holding `user.read` — including a Viewer invited into a second tenant — could enumerate every account on the instance: emails, names, and the role column. `PATCH`/`DELETE /users/{id}` had the same shape, letting one organization rewrite or remove another tenant's member, and `GET /search?q=` returned the same list through the command palette | Directory, single-user read, search, role change and removal now join `memberships` on the active organization; a foreign user id is a 404 with the same envelope as a random uuid; tests `test_member_directory_only_ever_shows_the_active_tenant`, plus the suspension-containment test proving a removal in one tenant leaves the account, its sessions and its other membership intact |
| 2 | MEDIUM | `sessions` has no `org_id`. `?all=true` listed every session on the instance (IP address, device label, user agent) to any `user.manage` holder, and `DELETE /sessions/{id}` revoked a session belonging to another tenant's user — a cross-tenant denial of service from a plain organization administrator | Listing and revocation intersect with the active organization's memberships; `user_id` filtering for a non-member is a 404 and revocation of a foreign session is indistinguishable from a bogus id; tests `test_one_tenants_session_list_and_revocation_stop_at_its_members`. (`?all=true` also turned out to be a no-op — it returned only the caller's own sessions — and now does what its name says, inside the tenant.) |

Everything else in the review held: the 24-test cross-tenant suite, the raw-SQL RLS
probes, the WebSocket subscribe/fan-out checks, worker sweeps, agent token binding,
and the audit trail's append-only trigger (verified to still reject `UPDATE` and
`DELETE` after the tenant column was added). The residual risks that remain are
listed under Known limitations.

## Third security review — projects, environments & secrets (2026-10-08)

An adversarial pass over the Phase 2 change set: IDOR, cross-project and
cross-organization access, project/environment confusion, secret scope confusion,
plaintext leakage, rollback authorization, concurrent rotation, raw-SQL paths, RLS
bypass, worker/WebSocket scope, and privilege escalation. It was written against
the delivered code, not the plan.

| # | Surface | Finding | Status |
| --- | --- | --- | --- |
| 1 | Environment routes | Every environment route resolves `project_id` **and** `environment_id` inside the active organization before use; a foreign or mismatched pair is a 404 identical to a random uuid. Knowing a project uuid or an environment uuid grants nothing. | Closed — regression tests in `test_phase2_environments.py` (IDOR, cross-org) |
| 2 | Secret scope | Creating an environment-scoped secret validates that the environment belongs to the given project in the same organization; the model CHECK makes "environment-scoped without project" unrepresentable. | Closed — `test_phase2_secrets.py` (scope confusion, cross-tenant) |
| 3 | Rotation race | `rotate_secret`/`rollback_secret` take the secret row `FOR UPDATE` and insert version `parent.version + 1` under the uq `(secret_id, version)` constraint, so two concurrent rotations serialize: distinct version numbers, no lost update, exactly one current version. | Closed — concurrency test drives two real concurrent rotations |
| 4 | Rollback authorization | Rollback requires `secret.write` and only accepts a version that exists **for that secret**; it appends a new version rather than rewriting history, so it can never destroy the pre-rollback value. | Closed |
| 5 | Plaintext leakage | No secret-bearing schema has a value field; project/environment detail returns references and key **names** only; resolution runs inside the deployment's worker and never returns through a response. The SPA renders no value column anywhere, including version history. | Closed — API tests assert the response bodies carry no value; SPA tests assert no value column |
| 6 | Secret consumption vs metadata | `secret.read` (metadata) stays separate from the deploy chain. No endpoint resolves a secret on request. | Closed — but see the limitation below on grant narrowing |
| 7 | Raw SQL / RLS | `secret_versions` carries `org_id` with the standard tenant + system policies and is in the catalog test's scope. The tenant-scoped SQL uses ORM selects (the tenancy guard rejected a Core `select(1)` probe during development, confirming the guard applies to the new code paths). Since Phase 2.1 the append-only guarantee is **database-enforced** — the runtime role holds `SELECT`/`INSERT` only and a guard trigger refuses `UPDATE` and non-cascade `DELETE` (fourth review below). | Closed — catalog + raw-SQL probes unchanged and green |
| 8 | Environment type | `environment_type` is descriptive only. Nothing in the authorization path reads it. | Closed by construction |
| 9 | Config as a channel | Config is a flat, bounded `string → string` map; malformed secret refs are rejected; nothing in config is interpolated or executed. | Closed |

**Residual risk carried forward:** resource-level grants do not exist yet, so a
principal holding `deployment.create` may deploy *any* environment of its own
organization, and therefore can cause any referenced secret of that organization to
be consumed by a deployment. That is a known, documented gap — not an accidental
hole — and it is why resolution is audited per reference. Since Phase 2.1 it is
pinned as a **hard gate** on real deployments and secret delivery
(product-roadmap.md §9.0): the four boundaries (view metadata / create a
deployment / deploy to an environment / consume that environment's secrets) must be
reviewed and enforced before 6a, not after.

## Fourth security review — secret-version integrity (Phase 2.1, 2026-10-09)

A narrow, database-level review prompted by one inconsistency: Phase 2 called
`secret_versions` append-only but granted the runtime role `UPDATE`/`DELETE` on it,
so the guarantee lived only in the service layer having no mutation path.

| # | Surface | Finding | Status |
| --- | --- | --- | --- |
| 1 | Runtime mutation | The app role's `UPDATE`/`DELETE` on `secret_versions` are revoked; it holds `SELECT`/`INSERT` only. A raw-SQL probe as the app role is refused on both statements. | Closed — `test_phase21_secret_version_integrity.py` |
| 2 | Privileged rewrite | A `BEFORE UPDATE OR DELETE` trigger refuses `UPDATE` for every role (owner included) and refuses `DELETE` unless the parent Secret is already gone — i.e. only the FK cascade. Immutability does not rest on grants alone. | Closed — owner-role probe asserts the trigger message |
| 3 | Cascade / purge | Deleting a Secret still purges its versions (the documented hard-delete policy); the trigger allows the cascade and refuses a direct delete. Rotation and rollback still append. | Closed — API tests + direct-delete probe |
| 4 | RLS preserved | No RLS bypass introduced; the app role stays `NOBYPASSRLS`, and version rows remain tenant-scoped (org A sees its row; org B and an unset GUC see nothing). | Closed |
| 5 | Role separation | The guard is a plain trigger firing for the invoking role — no `SECURITY DEFINER`, no owner-role request path. | Closed by construction |

**Residual / open:** history is retained only for the life of its Secret —
deleting the Secret destroys it (and is audited). A tombstone/grace period remains
an open question, not a shipped control; the §3 prune job still does not exist.
**Boundary:** the guard constrains row-level DML for *every* role, but it is not a
defense against a privileged database administrator — an owner/superuser can
disable the trigger, `TRUNCATE`, or read ciphertext directly (secrets-architecture.md
§3). It is a correctness control against application bugs and compromised
application credentials, not a control against control of the database server.

## Transport and headers

- Single nginx edge terminates traffic (`nginx/default.conf.template`): `server_tokens off`, HSTS emitted in production, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, a strict referrer policy, and a restrictive CSP for the SPA
  (`default-src 'self'; script-src 'self'; …; frame-ancestors 'none'; base-uri 'none'; form-action 'self'`).
  The identical header set is also applied by `SecurityHeadersMiddleware(is_production=…)` so a deployment without the edge is still hardened — `backend/app/core/middleware.py`.
- API documentation (`/api/docs`, `openapi.json`) is disabled when `ENVIRONMENT=production` (`backend/app/main.py`).
- Internally, services communicate on a private compose network; only the edge publishes a host port.

## Secrets handling

- **Never returned after creation.** Agent enrollment tokens, API keys and notification-channel credentials are shown once in the UI with an explicit "stored only as a hash" notice; only a salted hash is persisted.
- `digest_of` (`backend/app/core/security.py`) renders a short, server-keyed HMAC digest for change-detection UI — a leaked digest is useless without the app secret, unlike a plain SHA-256.
- Secret *values* never appear in logs, audit records, or API responses; the redaction layer (`redact_mapping` in `backend/app/core/logging.py`) scrubs sensitive-named keys from structured payloads before they are persisted or logged. Caveat: it recurses dicts but not lists (platform-security-model.md S8).
- **Scopes and history (Phase 2; append-only enforced in the database since Phase 2.1).** A secret is org-, project- or environment-scoped, resolved most-specific-first (environment > project > organization). Rotation appends an immutable version; rollback re-appends an older value as a *new* version, so history is never rewritten or deleted. Since Phase 2.1 the runtime role holds `SELECT`/`INSERT` only on `secret_versions` and a trigger refuses `UPDATE`/non-cascade `DELETE`, so history cannot be rewritten even by a privileged SQL path. Version history exposes version numbers, digests and actors only. Deleting a secret cascades its history — the one destructive secret operation, gated by `secret.write` and audited.
- **Fail-closed resolution.** An unresolvable reference fails the deployment before its first step instead of substituting an empty value; the failure reason names the key, never the value.
- Probe headers on uptime monitors are echoed back **masked** (`mask_sensitive_headers` in `backend/app/schemas/monitor.py`) and monitor URL query strings are redacted in responses (`_redact_url_query`).
- Notification channels expose only a pre-masked `display_target` (e.g. `sm******@example.com`, path-stripped URLs) — `backend/app/schemas/channel.py`.
- `scripts/generate_secrets.sh` refuses to overwrite existing real values unless `--force` is passed explicitly.

## SSRF protection

User-supplied URLs are fetched by uptime monitors and notification webhooks — the
classic SSRF surface. `backend/app/core/ssrf.py` provides:

- `assert_safe_url` — DNS-resolves the host and rejects loopback, RFC 1918/link-local, ULA, and other non-global targets, plus non-HTTP(S) schemes.
- Monitors run with `follow_redirects=False` and validate **every redirect hop** through the same guard before following it (`backend/app/providers/monitor_transport.py`) — redirect-based bypass is closed.
- Docker host `tcp://` endpoints are validated with `assert_safe_tcp_endpoint` before save and before use (`backend/app/services/docker_host_service.py`).

## Rate limiting and abuse

`backend/app/core/rate_limit.py` implements **fixed-window counters** in Redis
(`INCR` + `EXPIRE`, keyed `nx:rl:{limiter}:{client_ip}`) — not token buckets, so
bursts at a window edge are by design. The
auth-sensitive limiters **fail closed** (Redis outage ⇒ requests rejected, not
allowed through): login 10/min/IP, register 5 per 5 min/IP, refresh 30/min/IP.
General API traffic fails open for availability, as documented in the module.

## Audit log

Every mutating request writes an append-only audit row (`backend/app/services/audit_service.py`)
with actor, action codename, target, request id, **organization**, and redacted
metadata. Reads are tenant-scoped: the audit API returns only the active
organization's rows. A **pre-organization security event** — a failed login for an
unknown address, a refresh-token replay, or a sign-in/sign-out/password change for
an account whose memberships are none or several — is written with a NULL
organization, visible to system scope only and never to a tenant. Such an event
keeps its **identity** (the user is the actor) but is *not* attributed to any one
tenant: picking an organization for a user who belongs to two would be a guess, and
filing it under no tenant is the honest answer. The event bus enforces this: a
named-actor event without an organization raises unless the call site explicitly
declares it instance-level, and the WS hub drops a NULL-org frame for every org
subscriber. The API is read-only; there is
no update or delete path, and the database trigger that blocks `UPDATE`/`DELETE` on
`audit_logs` predates tenancy and is unchanged — tenant scoping narrows who can
*read* the trail, it does not widen who can rewrite it.

## The agent (least privilege by construction)

`agent/nexusops_agent.py` uses only the Python standard library and authenticates
with a per-node `nxa_` credential (minted by redeeming an organization-scoped,
single-use, expiring `nxk_` enrollment token). It executes **no arbitrary commands**:
metrics, container inventory and log tailing are reads, and the only writes are the
closed registry (`container.start/stop/restart/remove`, `logs.tail`) — each a fixed
Docker API call over the unix socket, re-validated locally against the same shape
the server checked. There is no `shell=True`, no `/containers/{id}/exec`, and no way
for a control-plane payload to introduce a new type. Transport is **HTTPS-only**: a
non-loopback plain `http://` URL is refused *before* any credential is sent, the
`--insecure` TLS-bypass flag is gone, and a private CA is trusted via
`NEXUSOPS_CA_BUNDLE` (verification is never disabled). Docker capability is proven
by a real `/version` call, not by a binary on PATH.
`agent/install.sh` writes the credential file with `umask 077` semantics and
`chmod 600` *before* the secret is written into it, and reads the token from the
environment (never argv, which `ps` exposes).

## Production hardening checklist

1. Generate real secrets: `./scripts/generate_secrets.sh` (writes `.env`; refuses overwrite).
2. Set `ENVIRONMENT=production` — enables HSTS and disables OpenAPI/docs. It does **not** control the refresh cookie's `Secure` flag: that follows the request transport (`X-Forwarded-Proto`, `backend/app/api/v1/auth.py`), so it turns on by itself once TLS terminates in front of the edge.
3. Do not seed: `make seed` requires explicit `NEXUSOPS_ALLOW_SEED=1` and is meant for demo stacks. Seeded demo credentials (documented in the README) must never exist in production.
4. Keep `SIMULATION_MODE=false` — the badge in the UI must be off so operators know they are looking at live data.
5. Terminate TLS in front of the edge (the compose file exposes plain HTTP on `:8080` for lab use).
6. Rotate: refresh tokens rotate automatically; rotate API keys and agent credentials from their settings pages, or revoke a node credential immediately (`POST /nodes/{id}/agent-token/revoke`, no grace). A **rotation** keeps the previous credential valid for a bounded grace window so a running agent can pick up the replacement on its next heartbeat; a **revocation** stops acceptance at once.

## Security audit (2026-09)

A three-lens adversarial review (exploit-oriented, correctness, hardening) over the
full backend, frontend, nginx config, scripts, and agent produced 26 candidate
findings; 20 were confirmed by adversarial verification. Severity split: **3 HIGH**,
5 MEDIUM, 12 LOW. All 20 were fixed and covered by regression tests before this
document was written; the full backend suite (368 tests, including the
regression tests added since the audit) passes:

| # | Severity | Finding | Fix |
| --- | --- | --- | --- |
| 1 | HIGH | API-key permission check consulted the superadmin shortcut before the key's scope, so a superadmin-owned key could exceed its grant | Scope intersection evaluated **first** in `has_permission`; regression test asserts a scoped key of a superadmin is still limited |
| 2 | HIGH | Uptime monitors followed redirects inside httpx, so a monitor pointing at an attacker host could be redirected to internal targets (SSRF bypass) | `follow_redirects=False` with a manual per-hop `assert_safe_url` loop; regression test reproduces the original bypass |
| 3 | HIGH | Demo seed created a known superadmin + API key whenever `ENVIRONMENT != production`, a footgun for staging deploys | Seeding requires explicit `NEXUSOPS_ALLOW_SEED=1`; `generate_secrets.sh` refuses silent overwrites |
| 4–20 | MEDIUM/LOW | Refresh-rotation race (rows now selected `with_for_update`, so a replayed token takes the TOKEN_REUSE path), auth rate limiter failed open when Redis was down (now fail-closed), secret digests were unsalted SHA-256 (now keyed HMAC), monitor probe headers/URL credentials echoed verbatim (now masked), webhook `display_target` revealed path-embedded credentials (now pre-masked), lockout response distinguished valid emails (now the generic envelope), bootstrap registration TOCTOU (now behind a `pg_advisory_xact_lock`), docker `tcp://` endpoints skipped the SSRF guard (now `assert_safe_tcp_endpoint`), HSTS never emitted (middleware now production-aware), agent install wrote the token before `chmod 600`, agent accepted plain-HTTP transport silently (now requires `--allow-insecure-transport`), nginx `server_tokens`, missing SPA CSP, OpenAPI/Swagger exposed in production, 500-handler logged raw exception text (now the exception class name only), `generate_secrets.sh` silently rotated secrets (now refuses without `--force`) | All fixed as described in the sections above; each has a regression test or an explicit lint-checked guard |

The full itemized finding list with reproduction notes lives in the engineering
report accompanying this release.

## Known limitations

- The compose stack ships for lab/self-hosted use: TLS termination, external WAF, and SMTP relay hardening are deployment concerns (documented in `docs/deployment.md`).
- Rate limiting is per-IP at the application layer for human routes — a reverse proxy must forward real client IPs (`X-Forwarded-For` handling). Authenticated agent routes instead key on the resolved **node**, so NAT'd fleets do not share a bucket (Phase 3).
- Notification-channel and secret values are masked but the database stores them encrypted-at-rest only via disk-level encryption of the host volume; application-level envelope encryption is future work.
- **Deploying is not grant-narrowed.** `deployment.create` authorizes a deployment into any environment of the organization; resource-level grants ("Ali deploys staging but not production") are a later phase. Until then, permission to deploy implies permission to consume the secrets that environment references.
- **Secret history is unbounded.** There is no prune policy for `secret_versions` — retention beats an arbitrary window for now; a maintenance job is a follow-up (secrets-architecture.md §3).
- **The RLS-exempt class has no database-level tenancy net.** `organizations`, `memberships`, `api_keys`, `agent_credentials` and `roles` are filtered only in the application, because each is legitimately read before an organization is known. A stray query or guard bug in those five is cross-tenant by definition; the `system_scope` allowlist and the catalog test are the fences, not the database.
- **Redis is control-plane-internal.** Container logs, metric frames, deployment logs and event frames from every organization share one pub/sub; the hub drops frames whose organization is not the socket's, but compromise of Redis itself is cross-tenant visibility. The channels are not org-prefixed by design (`docs/multi-tenancy.md` §0 delta 2).
- **A live WebSocket keeps the permission set it connected with.** A suspended membership or a changed role is not visible until the socket reconnects (HTTP requests are unaffected — the org check runs per request). Bounded connection TTL plus drop-on-revocation is the designed follow-up.
- **A tenant administrator can see their own organization's member list and session metadata.** That is the point of `user.read`/`user.manage`, but it means email addresses and device labels for those members are visible to whoever holds that permission in the tenant.
- The agent trusts the server for its configuration (poll interval, log tail limits); a compromised server can direct an agent to read container logs of anything visible to its Docker socket — by design, but worth knowing.
