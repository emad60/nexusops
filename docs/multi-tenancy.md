# Multi-Tenancy Architecture

**Status:** Implemented (Phase 1) — the sections below are the design record; §0
records what actually shipped and where it differs from the plan.
**Date:** 2026-09-20 (implemented 2026-09-24)

## 0. As-built record

Every invariant in §1 has an enforcement point in the code, and each one is
covered by a test in `backend/tests/integration/test_tenant_isolation.py` (24
tests) plus `test_rls_policies`-style catalog assertions in the same file.

**The module map.**

| Concern | Where |
|---|---|
| Scope ContextVars, guard, stamping, GUC writer | `backend/app/core/tenancy.py` |
| Organization + Membership models | `backend/app/models/tenancy.py` |
| `org_id` mixin / column helper | `backend/app/models/base.py` (`OrgScoped`, `org_id_column`) |
| Scope resolution per request | `backend/app/api/deps.py` (`resolve_auth`, `org_scope`) |
| RLS roles, policies, backfill, trigger for node tags | `backend/alembic/versions/20260922_1000-a3f1c8d24b6e_add_tenancy_foundation.py` |
| Org API (list/create/rename) | `backend/app/api/v1/organizations.py` |
| Org-prefixed channel naming helpers | `backend/app/core/channels.py` (see delta 2) |
| Socket binding + frame partitioning | `backend/app/ws/hub.py` |
| Worker scoping helpers | `backend/app/tasks/_util.py` (`sweep_session`, `org_session`, `org_for`) |
| SPA org bootstrap + switcher | `frontend/src/auth/AuthContext.tsx`, `components/OrganizationSwitcher.tsx` |

**Three nets, deliberately not interchangeable.** (1) The SQLAlchemy session
guard filters every ORM SELECT and *refuses* unscoped DML and Core statements;
(2) `before_flush` owns new rows and rejects rows that change hands; (3)
PostgreSQL RLS is the backstop for bulk DML, identity-map hits and raw SQL. The
guard raises `TenancyScopeError` (a 500) rather than filtering on `org_id IS
NULL` — a missing scope is a bug, never a silent empty result.

**Deltas from the plan.** Recorded because the plan is the reviewed design and a
future reader deserves to know where the code intentionally differs.

1. **The GUC is re-issued per transaction and is transaction-local
   (`set_config(..., is_local => true)`).** SQLAlchemy begins transactions
   lazily, so a statement-level `SET LOCAL` executed outside an explicit block is
   a no-op; an `after_begin` listener writes the value at every transaction
   boundary instead. The value is deliberately **transaction-local**: a
   session-level `set_config(..., false)` survives the pool's checkin reset (a
   plain `rollback`, which does not undo `set_config`), so a returned connection
   could still carry the previous request's organization. Local scope clears it
   at commit/rollback, so a pooled connection is tenant-free the moment it is
   handed back — proven by
   `backend/tests/integration/test_tenant_concurrency.py`.
2. **Redis channel names are not org-prefixed.** Frames carry their organization
   and the hub drops every frame whose org is not the socket's; entity-existence
   checks run inside the socket's org scope. Prefixing the channel *as well*
   would create a second source of truth for the same UUID while the hub still
   had to filter (the `global`/`incidents` channels are shared by every tenant by
   design), so the filter is the single enforcement point.
3. **`X-Org-Id` is always required** for authenticated human requests — there is
   no single-org exemption (§2 updated). The SPA bootstraps by reading
   `GET /organizations` and stores the chosen org; the client sends the header on
   every request, and a missing header is a 403 with the membership count for
   guidance. This removes a branch that would otherwise have to be re-argued per
   endpoint.
4. **The `_search_users` cut (§7) is closed rather than kept.** The users section
   of the command palette is scoped by joining the caller's memberships, so it
   searches *this organization's members* — a global user search never becomes a
   global resource search.
5. **`users` and `sessions` are membership-scoped at the API level too.** The
   directory (`GET /users`), the single-user read, and the mutating routes act on
   a **membership**: `PATCH` changes the role held in the active organization,
   `DELETE` suspends that membership (it does *not* disable the account or revoke
   its sessions, which are instance-wide credentials and would have made tenant
   administration a cross-tenant denial of service). `GET /sessions?all=true`
   lists sessions of the organization's members only. Both are covered in §7 of
   the test suite.
6. **RLS exempt set (exactly five tables).** `organizations`, `memberships`,
   `api_keys`, `roles` (instance-wide templates; `org_id` is NULL in v1) and
   `agent_credentials` — the tiny credential-routing table the plan called for in
   §9, which is why `servers` itself is under full RLS. The exemptions are data
   in `app.core.tenancy.RLS_EXEMPT_ORG_TABLES`, and the catalog test fails if the
   set of tables carrying `org_id` diverges from the set with policies plus that
   list.
7. **Every system scope is fenced by an allowlist.**
   `SYSTEM_SCOPE_ALLOWED_MODULES` names the ten modules permitted to switch
   tenant isolation off; `tests/unit/test_tenancy_allowlist.py` AST-scans the
   source and fails in both directions (a module opening a scope outside the set,
   or a listed module that no longer does).
8. **Verification status.** 481 backend tests (unit + integration, RLS probes
   against the real `nexusops_app` role, WS hub, worker sweeps, a
   tenant-concurrency suite and a model/migration drift test) and 176 frontend
   tests pass; ruff, mypy, `tsc` and eslint are clean; the Playwright journey is
   11/11. The isolation suite is 24 tests. Full Phase 1 deliverables and the
   hardening pass: [phase1-report.md](phase1-report.md).
9. **Done: the `server.*` → `node.*` vocabulary rename** (§10 step 3). Codenames,
   routes (`/v1/nodes`, with a schema-hidden `/v1/servers` alias), the SPA and the
   docs all use Node; the `servers` table keeps its name until the cleanup phase
   (domain-model.md §2.3). One data migration (`c4e2a1f7b9d3`) renames the stored
   permission rows and API-key scope strings.
10. **Added after the first pass: the node operations framework**
    (node-agent-architecture.md §5). A new tenant-owned `operations` table
    (migration `e7c4a2b9d1f3`, RLS policies + explicit app-role grant) and the
    compare-and-set state machine — claim/result/cancel/expiry — with per-type
    permissions reusing the existing `container.*` codenames. The capability
    gate is now **enforced fail-closed** (`409 NODE_CAPABILITY_UNVERIFIED` for
    any type whose capability cannot be verified — see
    node-agent-architecture.md §5.4); heartbeat delivery of pending op ids is
    still not implemented. See §7 of [phase1-report.md](phase1-report.md).

## 1. Tenancy invariants

Every channel through which tenant data can flow must be org-scoped. The complete
list, each with its enforcement point:

| # | Channel | Enforcement point | Spec section |
|---|---|---|---|
| 1 | REST reads/writes | session guard + scoped helpers (§3) | §3 |
| 2 | Direct object IDs (IDOR) | scoped helpers + IDOR suite (§7) | §3, §7 |
| 3 | WebSockets | org-scoped channel naming + subscribe check (§5) | §5 |
| 4 | Background jobs (Celery) | org context in task payload + contextvar (§4) | §4 |
| 5 | Agent connections | node→org binding; ingestion sets org context (§6) | §6 |
| 6 | Search | org-scoped via session guard | §3 |
| 7 | Metrics/logs/events/audit | org_id columns + session guard | §3 |
| 8 | Secrets resolution | scoping rules in the secret service | §3 + secrets-architecture.md |
| 9 | Notifications (outbound) | channels are org rows; sends carry org context | §3 |

## 2. Org resolution on every request

- **The JWT carries identity, not tenancy.** Access tokens keep `sub` (user) only.
  Active org is chosen per request via the `X-Org-Id` header (SPA stores last-used
  org; switch = UI state, no re-login).
- **Validated on every request:** the auth dependency (extend `resolve_auth`) checks
  the header against the caller's `active` memberships. No membership → 403.
  Missing header → 403 `ORGANIZATION_HEADER_REQUIRED` (as shipped: always
  required, for single-org users too — the SPA bootstraps from `GET
  /organizations`, so the header is never unknown to a client that can act).
  (Alternative rejected: org claim inside the JWT — forces token re-mint on every
  switch and complicates API keys; header + per-request validation is stateless and
  cheap: one indexed memberships query, cacheable per request.)
- **API keys bind to one org** (§2.1 of domain-model.md): `org = key.org_id`,
  header ignored, active membership required at key creation.
- **WS connections** authenticate exactly like HTTP, with the same header semantics.
- **Agent calls** (heartbeat/ops): org comes from the authenticated **node** row —
  never from payload, header, or lookup by untrusted input.
- **Metrics/logs/events listing routes** that exist today without pagination
  defaults: add org filter + pagination enforcement via the existing
  Page/PageParams primitives (invariant 7).

## 2.1 Org creation — v1 decision

Who may create organizations is a product decision, so it is decided here rather
than left to implementation:

- **v1 onboards via operator-issued invites to pre-created orgs.** The instance
  operator (bootstrap owner) creates orgs and invites members — admin-gated user
  creation exists today (backend/app/api/v1/users.py:69-90, password generated and
  shown once, delivered out-of-band). No self-serve signup ships in v1; the UI's
  Register tab already appears only while `/meta` advertises bootstrap availability.
- **Why self-serve is cut from v1:** registration today is invite/bootstrap-only
  (INVITATION_REQUIRED, backend/app/services/auth_service.py:157-160), and open
  registration drags in email verification, abuse control, and plan gating — a
  product surface, not a Phase 1 tenancy primitive. When self-serve arrives it
  needs an open-registration flag, org auto-creation on signup, and plan
  enforcement — its own phase, gated on the billing plan work.
- **Consequence for the journey:** platform-vision.md §4 step 1 is "accept an
  invite", and the first user of a fresh deployment bootstraps as owner of the
  first organization (§10, migration step 2).

## 3. The session guard (the mechanical layer)

The core mechanism (SQLAlchemy `with_loader_criteria`), applied in ONE place:

```python
# backend/app/core/tenancy.py (as shipped)
_current_org: ContextVar[uuid.UUID | None] = ContextVar("nexusops_current_org", default=None)
_current_scope: ContextVar[str] = ContextVar("nexusops_current_scope", default="unset")
# three scopes: "org" (tenant guard active) | "system" (allowlisted maintenance
# modules only) | "unset" (fail-loud: touching tenant data raises, and RLS denies
# it because the GUC is left empty)

@contextmanager
def org_scope(org_id): ...       # sync: entering a scope is not IO, and the
@contextmanager                   # contextmanager has to wrap non-await code too

def system_scope(reason): ...    # reason is required and logged; sweeps only —
                                 # agent ingestion always runs under
                                 # org_scope(node.org_id) (§6)
```

```python
# session factory event listener (one place, core/db.py):
@event.listens_for(Session, "do_orm_execute")
def _add_tenant_filter(exe_info):
    if _current_scope.get() under system scope, skip;
    for base in OrgScoped (mixin on every tenant model):
        add with_loader_criteria(OrgScoped, lambda cls: cls.org_id == _current_org.get(), include_aliases=True)
    also null-org rows are invisible under org scope (no orphan reads)
    system scope skips the guard (sweeps iterate orgs explicitly: for org in orgs: with org_scope(o.id): ...)
```

**Guard coverage limits (verified on the pinned SQLAlchemy 2.0.52).**

- `with_loader_criteria` filters SELECTs only. ORM-enabled UPDATE/DELETE are NOT
  filtered (empirically: cross-org UPDATE/DELETE rowcount=1 on 2.0.52). Rule:
  every tenant-table DML must carry `org_id` in its WHERE; the RLS `WITH CHECK`
  policy (§9) is the backstop. The codebase's sweep/ingestion idiom is exactly
  bulk DML on tenant models: `update(Server)` at server_service.py:391,404;
  `delete(LogEntry)` at log_service.py:140,156 and tasks/maintenance.py:57,82;
  `delete(MetricSnapshot)` at metrics_service.py:228,256.
- Core (non-ORM) statements bypass the guard entirely (precedent:
  tasks/maintenance.py:128 `cast(Table, Session.__table__).update()`). Under org
  scope, the guard listener must REJECT (raise) any execution where
  `is_orm_statement` is False and the statement references an `OrgScoped` table
  (`do_orm_execute` fires for Core statements too; `is_orm_statement`
  distinguishes them). Test added to the §7 list.
- `Session.get()` identity-map hits return before any SQL (`Session._get_impl`
  checks the identity map first), and the app sets `expire_on_commit=False`
  (core/db.py:46). Rule: a FRESH session (or `expire_all()`) at every
  `org_scope()` entry whenever the session already touched another scope;
  regression test: two scopes in one session.
- Fail-loud scope: when scope='org' and org is None the guard must RAISE — the
  naive `cls.org_id == _current_org.get()` compiles to `org_id IS NULL`, which
  silently matches only orphan rows. Never fail-empty.
- `is_column_load` loads (Session.refresh / expired-attribute loads) must stay
  filtered, not skipped.

**System scope is constrained.** `system_scope()` is allowed only in
backend/app/tasks/ modules plus the pre-org credential lookups (carve-out
below); enforced with an import-time/lint allowlist in core/tenancy.py, and
every entry is logged with task/route identity.

**Pre-org credential lookups (carve-out).** These run before any org is known
and must keep working under a fail-closed default: agent token hash lookup
(api/v1/agent.py:43-45), API-key hash lookup (api/deps.py:88), user/session JWT
lookups (api/deps.py:116-121), WS auth (ws/hub.py:136-174). Scope: narrow
hash-predicate reads on `users`, `sessions`, `refresh_tokens`, `api_keys`,
`servers`, `enrollment_tokens`, `memberships`, `roles` ONLY — never for tenant
data.

## 4. Background jobs

- Task payloads carry org_id; a Celery base task opens the session inside
  `org_scope(org_id)`. Task granularity follows the claim shape: tasks that CLAIM
  cross-org batches (run_due_monitors, tasks/monitoring.py:27-40) claim under
  system scope, then execute each claimed row under `org_scope(row.org_id)` in a
  FRESH session per row; only genuinely org-shaped sweeps (e.g. metric rollups)
  iterate orgs. Fresh-session-per-org is mandatory — reusing one session across
  scopes hits the identity-map bypass (§3).
- Agent ingestion (heartbeat/hello) runs under the **node's org scope** (§6), so
  writes and event emission are tenant-correct even though the trigger is a machine.
- Cross-org data (platform stats) — none today; if needed later, system_scope with audit.

## 5. WebSockets

- Connect auth unchanged (JWT/API key + active membership check added).
- Channels become `org:{org_id}:{...}` prefixed (`backend/app/core/channels.py` naming helpers already exist: container_log_channel etc. → gain org prefix).
- Subscribe frames: after the existing permission re-check, also validate the channel's org == active org (from connection auth context).
- Publish helpers (event_bus.publish) stamp the org into the channel name from the row's org_id — no publisher can forget it (channels.py helper signatures gain a required org_id parameter).
- event_bus.publish() gains a REQUIRED org parameter — it currently has none and
  the `nx:events` frame carries none (services/event_bus.py:78-135), so the
  notification dispatcher consumes raw frames cross-org
  (notification_service.py:424). Making org a required argument is deliberately a
  compile error at every call site until stamped: org goes into SystemEvent.org_id
  and the Redis frame; the dispatcher matches notification channels by frame org.
- Hub reality check: hub sessions are created outside the FastAPI dependency
  chain (ws/hub.py:234,331), so the hub must set the org ContextVar itself;
  `_entity_exists` does bare-PK existence checks on tenant tables
  (hub.py:177-180,331-336) — a cross-org IDOR oracle via WS subscribe until
  org-filtered; the Redis fan-in `_route` matches by channel prefix only
  (hub.py:462-489) and global/incidents deliver by permission alone
  (hub.py:467-475) — both must partition by frame org_id.
- Subscribe-time permission checks validate the CONNECT-time cached permission
  set (hub.py:151,170,313-317): membership suspension or role change
  mid-connection is invisible until reconnect. Follow-up: bounded connection TTL
  / periodic revalidation, and drop-on-revocation via event.
- **Redis trust boundary.** Redis is control-plane-internal: all orgs' container
  logs, metric frames, deployment logs and event frames flow through one pub/sub
  to every backend instance (hub.py:67, event_bus.py:140). Compromise of Redis =
  cross-tenant visibility. Tenant controls there are channel org-prefixing +
  hub-side filtering only; optional Redis ACLs (separate WS-reader vs publisher
  roles) later.
- 204-vs-event gotcha: transition-only events unchanged in behavior, now org-scoped.
- The events page caps its first page; a live WS prepend drops the oldest row —
  preserved behavior, org-scoped.

## 6. Agents

- Enrollment tokens become org-scoped rows (`enrollment_tokens`: org_id, single-use
  or multi-use flag, expires_at, created_by_id, revoked_at). Today's enrollment is
  already per-server — an `nxa_` token minted via the servers API and delivered to
  the agent through its env var on the node; tenancy adds org scoping and lifecycle
  (single-use, expiry, revocation) to those tokens.
- The agent's org is derived from the authenticated node row — never from payload.
- Agent ingestion (hello/heartbeat/ops) executes under the node's org scope, so
  writes, events, and emitted audit rows are tenant-correct.
- Revocation: revoking a node kills its token's acceptance immediately (token hash
  lookup is per-node); the org's other nodes are unaffected.

## 7. The IDOR suite

A parametrized cross-tenant test suite is a **Phase 1 exit criterion** (no phase
ships without it): for every org-scoped listing and detail endpoint, tests assert
that org B's user gets 404/403 on org A's objects — REST detail routes, search hits,
WS subscriptions, and (later) operation results. The suite also covers: cross-org
write probes (UPDATE/DELETE via every API route), the two-scopes-one-session
identity-map test, the Core-statement rejection test, and the raw-SQL RLS probe
suite (§9). The existing fixtures
(db fixture, auth helpers, seed matrix) extend with a two-org fixture; the
existing RBAC tests provide the pattern. File:
`backend/tests/integration/test_tenant_isolation.py`.

**Closed in Phase 1:** `_search_users` used to search ALL users platform-wide,
contradicting the search invariant (§1 #6). Users are global by design (§8 class
(a)) so the session guard could not fix it; the query now joins `memberships` for
the active organization (`Membership.org_id == require_org()`) and returns only
members. The same join now bounds the user directory, the single-user read and
the session listing — the three surfaces whose boundary is a membership rather
than an `org_id` column on the row.

## 8. What stays global

Two classes, split by whether a legitimate read can precede org knowledge:

**(a) Pre-org credential/identity tables** — `users`, `sessions`,
`refresh_tokens`, `permissions`, `roles`, `organizations`, `memberships`,
`api_keys`, `servers`, `enrollment_tokens`: app-layer guarded, RLS-exempt
(§9), reads precede org knowledge by design — auth must find the caller before
any org is known; their tenancy is derived from the row itself (`key.org_id`,
`node.org_id`). Memberships must NOT be org-guarded: X-Org-Id validation reads
the caller's memberships across orgs (§2). Residual risk, plainly: this class
has no DB-level tenancy net — a stray query or guard bug here is cross-org by
definition; the carve-out allowlist (§3) is the only fence.
`servers` + `enrollment_tokens` are tenant-but-pre-org (the token-hash lookup
runs before the org is known): §9 moves the token hashes into a tiny un-RLS'd
credential-routing table so `servers` itself gets full RLS.

**(b) Tenant data tables** — everything else carrying org_id: the tenant tables
this doc already scopes (containers, deployments, log entries, metric
snapshots, monitors, incidents, secrets, notification channels, events/audit —
among others), plus the future domains, routes, certificates, operations,
grants. Session guard + RLS.

- Platform ops tables (later phases): enrollment token objects are org-scoped, but
  the registry itself is platform data.

## 9. PostgreSQL Row Level Security — defense in depth (adopted in Phase 1)

**Ruling: ADOPT.** The ORM guard provably covers SELECTs only; the codebase's
dominant write idiom is bulk DML (§3); a Core-statement precedent exists
(tasks/maintenance.py:128); identity-map hits bypass the guard entirely. RLS is
the second net that catches DML, Core, identity-map, and raw-SQL mistakes — it
does not replace the guard.

**Mechanism.** GUC `app.current_org` is (re-)issued at the start of every
transaction from the tenancy ContextVars: `org_scope(org)` → the org uuid;
`system_scope()` → the reserved sentinel uuid; neither → the empty string. As
shipped it is `set_config('app.current_org', $1, is_local => true)` in an
`after_begin` listener rather than a statement-level `SET LOCAL` — SQLAlchemy
opens transactions lazily, so the listener is how the value lands at every
transaction boundary, and `is_local => true` keeps it transaction-scoped so a
returned pooled connection is tenant-free (§0 delta 1). Policy per tenant table: `USING (app_current_org() = org_id)` /
`WITH CHECK (same)`, where the SQL helper returns NULL unless the GUC holds a
well-formed uuid or the system sentinel — so an unset or malformed value denies
everything instead of raising a cast error mid-query. The DB mirrors — and
independently enforces — what the ContextVar claims.

**Roles.** Tenant tables owned by `nexusops_owner`; the app connects as
`nexusops_app` (RLS enforced: `NOSUPERUSER NOBYPASSRLS`, and not the owner);
alembic + the entrypoint bootstrap connect as `nexusops_owner` — migrations
bypass by role, by design, and never serve request traffic. As shipped:
`alembic/env.py` builds its URL from `POSTGRES_OWNER_PASSWORD` (falling back to
`POSTGRES_PASSWORD`), `alembic/env.py`'s offline mode included, and
`docker-compose.yml` gives the runtime services the app role while the migration
step runs as the owner. The application refuses to start RLS-enforced against an
owner DSN (`config.rls_enforced` compares the DSN's user against the owner role).

**Table set.** All tenant data tables per §8 class (b). NOT under RLS: the §8
class (a) pre-org credential/identity tables. `servers` + `enrollment_tokens`
are tenant-but-pre-org (the token-hash lookup): move agent/enrollment token
hashes into a tiny un-RLS'd credential-routing table `(node_id, token_hash)` so
`servers` itself gets full RLS; the lookup joins once pre-org and everything
downstream is DB-enforced.

**Error semantics.** SELECT outside org → 0 rows (the API maps that to 404, so
the IDOR model is unchanged). INSERT/UPDATE/DELETE violating `WITH CHECK` →
loud error + audit event — a bug signal, never silently narrowed. The ORM guard
remains the UX/semantic layer (404s, scoped helpers).

**CI gate.** A raw-SQL probe suite connecting as `nexusops_app` via psycopg
directly (no ORM, no guard): per tenant table, assert (1) cross-org SELECT
returns 0 rows, (2) cross-org INSERT/UPDATE/DELETE rejected or affects 0 rows,
(3) the 'system' GUC sees all rows, (4) catalog completeness — every table with
an org_id column must have an RLS policy (pg_class/pg_policy join) so new
tables cannot ship unprotected. Same Phase 1 exit gate as the IDOR suite (§7).

## 10. Migration (Phase 1)

1. Create `organizations`, `memberships`, role org_id column. **Shipped.**
2. Backfill: single auto-provisioned org owned by the first user — named after
   the instance creator or something obviously provisional and editable, never
   "NexusOps" (a tenant named after the vendor); all existing rows get that org
   (server_default during backfill, then NOT NULL). Same migration: org_id
   index on every tenant table (the guard adds `org_id = $1` to every query)
   and the RLS role split (`nexusops_owner` vs `nexusops_app`, §9) wired into
   alembic/env.py and docker-entrypoint.sh. **Shipped.** The backfill creates one
   organization per instance, named `"<first user's name> (provisional)"`,
   `is_provisional = true`, owned by the oldest user, and every pre-existing row
   is attributed to it; the row is kept in the audit trail and the rename path is
   `PATCH /organizations/{id}`.
3. Codename rename server.*→node.* + API path alias, roles data migration.
   **Shipped** — see §0 delta 9. The roles data migration itself was unnecessary
   in v1 (there is no deployed `Operator` row to rename; the seed registry defines
   the system roles from scratch), so migration `c4e2a1f7b9d3` only rewrites the
   `permissions` rows and the stored API-key scopes.
4. Add `X-Org-Id` handling to the auth dependency. **Shipped**, always required
   (§0 delta 3, §2).
5. Session guard + scoped helpers + IDOR suite green before any other work.
   **Shipped**: the guard, the stamping listener, the RLS policies and 22
   cross-tenant tests, plus the catalog test that fails when an organization-
   owned table has no policy.

The production contabo instance migrates in place: one org, one membership, zero
user-visible change on day one — then the org switcher appears when the second org
arrives.