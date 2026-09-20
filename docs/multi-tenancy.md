# Multi-Tenancy Architecture

**Status:** Proposal for review — not yet approved for implementation.
**Date:** 2026-09-20

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
  Missing header with multiple orgs → 403 with guidance. Single-org users: header
  optional (defaults to their only org) — spares the SPA during migration.
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

## 3. The session guard (the mechanical layer)

The core mechanism (SQLAlchemy `with_loader_criteria`), applied in ONE place:

```python
# backend/app/core/tenancy.py (new module)
_current_org: ContextVar[uuid.UUID | None] = ContextVar("current_org", default=None)
_current_scope: ContextVar[str] = ContextVar("current_scope", default="org")
# scope: "org" (tenant guard active) | "system" (maintenance sweeps, agent ingestion writes)

@asynccontextmanager
async def org_scope(org_id): ...      # sets contextvar + guard via event listener
@asynccontextmanager
async def system_scope(): ...         # sweeps and agent ingestion write with explicit org from the row's org
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

## 4. Background jobs

- Task payloads carry org_id; a Celery base task opens the session inside
  `org_scope(org_id)`; system tasks (metric aggregation, retention, monitor checks,
  cert renewal scan) run `system_scope()` and explicitly iterate orgs
  (maintenance.py already iterates servers → becomes iterate orgs → servers).
- Agent ingestion (heartbeat/hello) runs under the **node's org scope** (§6), so
  writes and event emission are tenant-correct even though the trigger is a machine.
- Cross-org data (platform stats) — none today; if needed later, system_scope with audit.

## 5. WebSockets

- Connect auth unchanged (JWT/API key + active membership check added).
- Channels become `org:{org_id}:{...}` prefixed (`backend/app/core/channels.py` naming helpers already exist: container_log_channel etc. → gain org prefix).
- Subscribe frames: after the existing permission re-check, also validate the channel's org == active org (from connection auth context).
- Publish helpers (event_bus.publish) stamp the org into the channel name from the row's org_id — no publisher can forget it (channels.py helper signatures gain a required org_id parameter).
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
WS subscriptions, and (later) operation results. The existing fixtures
(db fixture, auth helpers, seed matrix) extend with a two-org fixture; the
existing RBAC tests provide the pattern. File:
`backend/tests/integration/test_tenancy_isolation.py`.

## 8. What stays global

- `users`, `sessions`, `refresh_tokens` — platform identity.
- `permissions` registry templates (org_id NULL templates), platform config.
- Platform ops tables (later phases): enrollment token objects are org-scoped, but
  the registry itself is platform data.

## 9. Migration (Phase 1)

1. Create `organizations`, `memberships`, role org_id column.
2. Backfill: single auto-provisioned org ("NexusOps") owned by the first user; all
   existing rows get that org (server_default during backfill, then NOT NULL).
3. Codename rename server.*→node.* + API path alias, roles data migration.
4. Add `X-Org-Id` handling to the auth dependency (header optional while single-org).
5. Session guard + scoped helpers + IDOR suite green before any other work.

The production contabo instance migrates in place: one org, one membership, zero
user-visible change on day one — then the org switcher appears when the second org
arrives.