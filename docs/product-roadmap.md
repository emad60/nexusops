# Product Roadmap — NexusOps Multi-Tenant Platform

**Status:** Phases 0–4 **delivered** (0 on 2026-09-22, 1 on 2026-09-24, 2 on
2026-10-08, 2.1 on 2026-10-09, 3 on 2026-10-09, 4 on 2026-10-10 — HTTP routing
only; certificates and TLS are Phase 5). Phases 5–9 are **proposals for review** —
none is approved or implemented.
**Date:** 2026-09-20 (status updated 2026-10-10)
**Companions:** [platform-vision.md](platform-vision.md) · [domain-model.md](domain-model.md) · [multi-tenancy.md](multi-tenancy.md) · [authorization.md](authorization.md) · [platform-security-model.md](platform-security-model.md)

## 0. Stance

Evolution, not rewrite. Every phase ships value; the production contabo instance
upgrades in place through every phase with zero data loss. Phase numbering here is
authoritative for all companion docs (domains/certs/ops/deployments reference it).

## 1. Migration strategy: what happens to what

Four-way classification, grounded in the subsystem analysis (the harness under
`.claude/workflows/` — `nexusops-understand.mjs`, `nexusops-draft.mjs`,
`nexusops-challenge.mjs` — and the companion docs).

**Remains as-is (verified real, load-bearing):**

- Auth stack: argon2id, session+refresh rotation with reuse detection, login
  lockout, bootstrap advisory lock (`backend/app/api/v1/auth.py`,
  `backend/app/core/security.py`).
- Permission registry + `ROLE_MATRIX` + `require_permission()` + the WS
  subscribe re-check (`backend/app/core/permissions.py`, `backend/app/api/deps.py`,
  `backend/app/ws/hub.py`) — the registry *grows* (authorization.md §2), the
  gate does not change.
- Append-only audit (DB trigger blocks UPDATE/DELETE) — gains `org_id` +
  `request_id` columns, trigger untouched.
- WS hub + Redis channel mechanics (`backend/app/ws/hub.py`,
  `backend/app/core/channels.py`) — channel names gain an org prefix.
- Monitor → check → incident → notification pipeline — targets become
  polymorphic, pipeline itself unchanged.
- Container inventory upserts, docker-host sweep, host-wide incremental log
  collection (matured across recent commits: host sweep concurrency fixes,
  concurrent-insert adoption, incremental logs).
- Secrets: Fernet at rest, metadata-only API, deploy-time `${secret:KEY}`
  resolution syntax.
- Frontend primitives (Page/PageParams, WS hooks) — org switcher added later.
- Tests: 337 unit + 54 integration backend, 109 frontend, 10-step Playwright
  journey — all carried forward, IDOR suite added on top.

**Extends (existing tables, additive columns/rows):**

- `Server` → exposed as Node: + `org_id`, capabilities JSONB, facts,
  `agent_version`.
- `Project`: + `org_id`; name unique → per-org.
- `DeploymentEnvironment`: **promoted** `application_id` → `project_id`.
- `Secret`: + `org_id`, layered scope; + new `secret_versions` rows.
- `Monitor`: + polymorphic target (`target_type`/`target_id`).
- `AuditLog`: + `org_id`, `request_id`.
- `ApiKey`: + `org_id` binding.
- `NotificationChannel`: + `org_id`.

**Refactors (existing code, changed mechanics):**

- Deployment engine: the runner is hard-instantiated at two sites
  (`backend/app/services/deployment_engine.py`, queue time and execute time) → a
  runner registry with DI; `AgentDeploymentRunner` added beside the simulated one.
- `resolve_auth`: gains active-org validation (`core/tenancy.py` guard).
- Secret resolution: silent-degrade-to-empty → **fail-closed** + audit event
  at resolution time. *(Shipped in Phase 0 — §3; the explicit persisted
  `RESOLVE_CONFIG` step remains Phase 2.)*
- Rate limiter: IP-only dimension → org+IP (NAT agent fleets share one bucket
  today).
- `Server.name`: platform-global unique → per-org.
- Agent: 401→`exit(1)` hot-loop → auth-failure backoff with full revocation
  semantics; transport HTTPS-only.
- Deployment cancel: cooperative-between-steps only → per-step timeouts with
  forced transitions.

**Deprecates / removes:**

- Per-server enrollment tokens (minted via the servers API, delivered to the agent
  via its env var) → org-scoped `enrollment_tokens` rows with lifecycle
  (single-use, expiry, revocation). **Shipped Phase 3** (the legacy per-node
  `POST /nodes/{id}/agent-token` remains as a rotation/compat path).
- `--allow-insecure-transport` (plain-HTTP agent option) — removed (**shipped Phase 3**, along with `--insecure`).
- `server.*` permission codenames → `node.*` (one migration — **shipped**,
  `20260923_1000-c4e2a1f7b9d3`).
- `/v1/servers` paths → `/v1/nodes` (**shipped**; `/v1/servers` kept as a schema-
  hidden alias in Phase 1, removal in cleanup).
- Platform-global `Server.name` uniqueness → per-org.
- The `-broken` health-check demo hook → real healthcheck gating in Phase 6a
  (demo-labeled until then).
- **Kept, not removed:** `sim://` monitors and `docker_sim` stay as
  explicitly-labeled demo/CI tooling (platform-vision §3 honesty principle).

## 2. Phase plan

| # | Phase | Status | Ships | Depends on |
|---|---|---|---|---|
| 0 | Truth pass & hardening | ✅ delivered 2026-09-22 | docs fixed against code; fail-closed secret resolution; agent backoff | — |
| 1 | Tenancy foundation | ✅ delivered 2026-09-24 | orgs/memberships/roles, org_id backfill, X-Org-Id + session guard, node rename, IDOR suite green, **operations control plane + fail-closed capability gate (CAS state machine; per-node capability advertisement + delivery land in phase 3)** | 0 |
| 2 | Projects & environments | ✅ delivered 2026-10-08 | env promotion to project scope, SecretVersion, layered secret scope | 1 |
| 2.1 | Hardening | ✅ delivered 2026-10-09 | `secret_versions` immutability at the database, legacy environment typing, deploy-chain gate recorded | 2 |
| 3 | Nodes & agent v2 | ✅ delivered 2026-10-09 | capabilities+facts, enrollment v2, **per-node capability advertisement + operations delivery** (the control plane and the fail-closed gate are already in), HTTPS-only agent | 1 |
| 4 | Domains & routes | ✅ delivered 2026-10-10 — **HTTP only** | Domain/Route entities, DNS verification, NginxProvider, apply pipeline, polymorphic monitors. Certificates and TLS are **not** in it | 3 |
| 5 | Certificates | proposal | ACME DNS-01, DNSProvider (Cloudflare first), TLS listener + `scheme=https` on routes, renewal scan, encrypted delivery, TLS-expiry monitors | 4 |
| 6 | Real deployments | proposal | 6a image-based via agent ops; 6b git→build on node | 3 (6a), 3+4 (6b) — **and the deployment-secret authorization gate (§9.0), which must close before 6a ships** |
| 7 | Teams, grants & custom roles | proposal | teams, resource-level grants, custom roles | 2 |
| 8 | Backups | proposal | policies/runs/destinations, verify + restore drill | 3, 7 |
| 9 | Billing & metering | proposal | usage-counter enforcement, plan gates | 1, 2 |

**Status of the plan:** phases 0–4 are **delivered**. Phases 5–9 are
**proposals** — not approved and not implemented; their "Ships" cells describe
intended work, not current behaviour. The only code that exists is what the
delivered sections below record. Phase 4 delivered the HTTP half of
[domain-routing.md](domain-routing.md): there is **no certificate issuance, no TLS
listener and no HTTPS redirect**, and every certificate shape in the design docs is
Phase 5 target design.

## 3. Phase 0 — Truth pass & hardening

**Status: DELIVERED** (2026-09-22). No schema change, as planned. What landed:

| Item | Where |
|---|---|
| Fail-closed secret resolution + resolution audit | `secret_service.resolve_secrets_for_environment` raises `SecretResolutionError`; the engine-owned `RESOLVE_CONFIG` step (planned first, executed by the engine, refused by any runner) fails the deployment through the standard `_finalize_failed` path, with `secret.resolve_failed` (DENIED) naming the keys and one `secret.resolve` row per resolved key+version |
| Agent auth-failure backoff (no 401 hot-loop) | `agent/nexusops_agent.py` parks in `REVOKED_POLL_SECONDS` (900) instead of `exit(1)`; `--once` still fails loudly |
| Install-hint env-var bug | `backend/app/api/v1/servers.py` now says `--server/--token` (or `NEXUSOPS_SERVER`/`NEXUSOPS_TOKEN`) instead of the never-read `NEXUSOPS_URL` |
| Simulated-deployment honesty chip | `frontend/src/components/SimulatedChip.tsx`, rendered on the deployment list + detail views, gated on the runtime `/meta` flag |
| Docs truth pass | Secure-cookie descriptions (api/deployment/development/security/troubleshooting), role count (5), fixed-window limiter (not token bucket), dead module paths in `security.md`, `make dev` `dev.conf` claim, agent 401 behavior; simulated deployments / `sim://` disclosed in README + architecture §12 |
| Tests | 5 agent-backoff unit tests; fail-closed resolution + audit assertions in `test_secrets.py` / `test_deployments_simulated.py` |

**Why first (as planned):** the docs contradicted shipped behavior (Secure-cookie
descriptions, role counts, limiter algorithm), and three correctness bugs were
known. Cheap, de-risks everything after.

Delivered as scoped: no new routes; the deployment run fails fast on
secret-resolution errors instead of deploying with empty values; the honesty
chip is gated on the runtime `/meta` flag so a real instance never shows it.

**The hardening list** (kept consistent with platform-security-model.md; items
land in their natural phase — column 3). ✅ = delivered in Phase 0:

| # | Known issue | Lands in |
|---|---|---|
| 1 ✅ | Silent secret-resolution degradation (empty dict on failure) | Phase 0 |
| 2 ✅ | Agent 401→exit(1) hot-loop on revocation | Phase 0 (backoff), **Phase 3 — separate revoke action + bounded dual-token rotation grace** |
| 3 ✅ | Agent plain-HTTP option (`--allow-insecure-transport`) | **Phase 3 — removed; non-loopback plain HTTP refused before any credential is sent** |
| 4 ✅ | WS global channel exposure | Phase 1 — event frames carry their organization and the hub drops cross-org frames (not channel-prefixed; multi-tenancy.md §0 delta 2) |
| 5 ✅ (agent routes) / ⏳ (human routes) | Rate limits keyed by IP only (NAT fleets share a bucket) | **Phase 3 — authenticated agent routes key on the node**; per-org/per-user keys on human routes still open |
| 6 ✅ | `Server.name` platform-global uniqueness | Phase 1 — `uq_servers_org_name` (and the same for tags/projects) |
| 7 ✅ | Audit rows lacking org / request-id | Phase 1 — `audit_logs.org_id`, tenant-scoped reads, append-only trigger unchanged |
| 8 ✅ (fail-closed + audit) / ⏳ (authorization) | Secret resolution lacking per-user authorization on the engine path | Phase 0 (fail-closed + audit), Phase 2 (deploy-chain authorization) |
| 9 ✅ | Install hint emitted `NEXUSOPS_URL`; the agent reads `NEXUSOPS_SERVER` — fresh installs never connected | Phase 0 |

**Exit criteria met:** docs spot-check clean; fail-closed resolution and agent
backoff covered by tests (403 backend / 164 frontend green).

One scoping decision worth recording: the plan said the *trigger* would fail
fast, but resolution runs on the worker at execution time. Phase 0 therefore
fails the deployment at its **first step** — the engine-owned `RESOLVE_CONFIG`
step, planned ahead of every runner step (secrets-architecture.md §5) — rather
than at `POST /deployments`. A queue-time *preflight* (so the API rejects an
unresolvable config before queuing) is still open, and is where the remaining
half of hardening item 8 (deploy-chain authorization) belongs.

## 4. Phase 1 — Tenancy foundation

**Why first (after 0):** every later phase scopes to an org; mechanical
enforcement must exist before resources multiply. Full spec:
[multi-tenancy.md](multi-tenancy.md).

- **DB:** `organizations`, `memberships`; `roles.org_id` (nullable = system
  template); org_id backfill with `server_default` → NOT NULL on projects,
  servers, secrets, monitors, incidents, notification_channels, api_keys,
  deployments (denormalized), audit_logs (+`request_id`), system_events.
- **API:** `X-Org-Id` validation in `resolve_auth` (always required — shipped);
  scoped helpers; codename rename `server.*`→`node.*` (registry, seeded rows,
  ROLE_MATRIX, stored key scopes, code, UI strings — shipped); `/v1/nodes` +
  deprecated `/v1/servers` alias (shipped); ApiKey org binding.
- **Frontend:** single-org UX unchanged day one; org switcher appears with the
  second org.
- **Security:** `core/tenancy.py` session guard (`with_loader_criteria`) +
  scoped helpers; IDOR suite
  (`backend/tests/integration/test_tenant_isolation.py`); org+IP limiter
  dimension.
- **Testing:** parametrized cross-tenant suite over every org-scoped listing
  and detail route; two-org fixtures extend the existing RBAC fixtures.
- **Exit:** IDOR suite green; one-org backfill proven on production contabo in
  place; zero user-visible change beyond the rename.

### Delivered (2026-09-24)

Phase 1 shipped as specified, with the deltas recorded in `multi-tenancy.md` §0:

- **DB/migration:** `20260922_1000-a3f1c8d24b6e_add_tenancy_foundation.py` —
  `organizations` + `memberships`, `org_id` on every tenant table (indexed,
  NOT NULL after a deterministic backfill), `roles.org_id`, `audit_logs.org_id`,
  per-organization uniqueness for servers/tags/projects, the `agent_credentials`
  routing table, the `nexusops_owner`/`nexusops_app` role split, row-level-security
  policies with `USING` **and** `WITH CHECK`, and a trigger keeping `server_tags`
  inside the tag's own organization.
- **Backfill:** one organization per instance, named after the oldest user,
  `is_provisional = true`, renameable via `PATCH /organizations/{id}` — never a
  vendor-named or arbitrary tenant.
- **API:** `X-Org-Id` **always** required for human callers (validated against active
  memberships), API keys bound to their own organization, `/organizations` for
  discovery, membership-scoped user directory and session listing/revocation.
- **Enforcement:** session guard (`with_loader_criteria` for reads, refusal for
  unscoped DML/Core), `before_flush` ownership stamping, PostgreSQL RLS behind the
  app role, allowlisted `system_scope`, and organization-bound WS/Celery/Redis/agent
  paths.
- **Frontend:** org bootstrap from `GET /organizations`, persisted selection, org
  requirement gate, and a switcher in the shell.
- **Tests:** 24 cross-tenant isolation tests (IDOR by read/update/delete/search/
  session/agent/operation, raw-SQL RLS probes as the app role, catalog coverage,
  unscoped-access and identity-map tests, worker and Redis delivery), plus the
  system-scope allowlist and WS-hub unit tests. 437 backend / 172 frontend, all green.

The `server.*` → `node.*` rename and the `/v1/nodes` surface (with the
`/v1/servers` compatibility alias) landed after this date as the phase's last
follow-up (migration `20260923_1000-c4e2a1f7b9d3`); see `multi-tenancy.md` §0
delta 9. **Still open from this phase:** hardening item 5 (org+IP rate limiting)
moved to Phase 2, and the queue-time deployment preflight (with deploy-chain
authorization) remains open from Phase 0.

## 5. Phase 2 — Projects & environments — **DELIVERED 2026-10-08**

**Why:** the project-centric product model ("Ymart → Production") needs
environments at project scope; per-env config/secrets/grants all anchor here.
Spec: domain-model.md §2.2.1.

**Delivered:**

- **DB (migration `20261008_1200-b2c3d4e5f6a7`):**
  `deployment_environments.application_id` → `project_id` (derived through
  `application → project`, then NOT NULL), `environment_type` (DEV/STAGING/PROD
  with a CHECK constraint), unique `uq_envs_project_slug (project_id, slug)`,
  indexes on `project_id` and `environment_type`; `projects.config` JSONB;
  `secrets.environment_id` + the scope CHECK and three per-level partial unique
  indexes; `secret_versions` (append-only, `org_id`, RLS tenant + system
  policies, version-1 backfill for existing secrets).
- **Migration behaviour — no slug-suffix:** where two applications of one project
  had same-named environments, the plan's "`production-2` suffix" was replaced by
  a **deterministic merge** (earliest `created_at`, tie-broken by `id`) —
  deployments re-pointed to the survivor before the duplicate is deleted, fields
  and config unioned. A suffix would have invented a name nobody asked for and
  split one environment's history in two; merging keeps one environment per real
  environment. Details: domain-model.md §2.2.1.
- **API:** environment CRUD under `/v1/projects/{project_id}/environments`
  (`project.read` / `project.manage`); project `config` on create/update;
  environment detail returns base, overrides and effective config separately;
  `GET /secrets/{id}/versions`, `POST /secrets/{id}/rotate`,
  `POST /secrets/{id}/rollback`.
- **Layering:** project base ⊕ environment overrides, **shallow** merge; secret
  resolution prefers environment > project > organization and fails closed.
- **Frontend:** the project page lists project environments and links each to a
  detail page (configuration layers, override editor, secret metadata + version
  history); the secrets manager gains scope display, version history, rotation and
  rollback.
- **Security:** Phase 1 tenancy untouched — every new path goes through
  membership → active org → project-in-org → environment-in-project → permission;
  `secret.read` (metadata) and secret *consumption* (the deploy chain) stay
  distinct; no endpoint returns a value.
- **Testing:** promotion-migration round-trip on realistic legacy fixtures
  (multi-app projects, duplicate slugs, multiple orgs/projects, existing secrets),
  layering precedence unit tests, secret scope/precedence/rotation/rollback/
  concurrency/IDOR/cross-tenant tests, RLS catalog coverage, SPA tests.

**Deviations from the plan at the time of writing:**

- **Deploy-chain (grant-narrowed) authorization is NOT implemented** — grants are
  a later phase (§10). Today a principal holding `deployment.create` may deploy
  any environment of its organization. The `secret.read` ≠ secret-consumption
  split *is* enforced. **This is now a hard gate on real deployments and secret
  delivery (§9.0): it must be reviewed and enforced before 6a, never after.**
- The project page shows environments but no per-environment deployment actions —
  deployments stay on the existing pages.

**Exit:** "Ymart → Production" config in one place; non-destructive rotation with
rollback proven; tenant isolation and RLS extended to the new tables.

## 5.1 Phase 2.1 — Hardening — **DELIVERED 2026-10-09**

A narrowly scoped hardening pass on top of Phase 2; no product features. What
landed (migrations `c3d4e5f6a7b8`, `d4e5f6a7b8c9`, `e5f6a7b8c9d0`):

- **`secret_versions` immutability is enforced by the database**, not only by the
  service layer. The runtime app role's `UPDATE`/`DELETE` were revoked (it keeps
  `SELECT`/`INSERT`) and a cascade-aware `BEFORE UPDATE OR DELETE` trigger refuses
  `UPDATE` for every role and refuses `DELETE` unless the parent Secret is being
  deleted. The deletion policy is now explicit: deleting a Secret is a hard delete
  that cascades its history (audited as `secret.delete`) — history is retained for
  the lifetime of the Secret, not in perpetuity. RLS and the runtime/migration role
  split are untouched. See secrets-architecture.md §3.
- **Legacy environment typing corrected.** Phase 2 had defaulted every pre-existing
  environment to `DEV`; `d4e5f6a7b8c9` reclassified the unambiguous slug/name
  aliases, and `e5f6a7b8c9d0` corrected it to the documented **slug-first**
  precedence (a recognised slug alias wins over a conflicting name; otherwise the
  name decides; otherwise `DEV`). Only rows still carrying the migration's own
  output are rewritten, so an operator's explicit value is preserved. See
  domain-model.md §2.2.1.
- **Deployment-secret authorization gate** recorded as a hard prerequisite on
  real deployments/secret delivery (§9.0): the four boundaries — view secret
  metadata, create a deployment, deploy to a specific environment, consume that
  environment's secrets — must be reviewed and enforced before 6a ships.
- **Consistency follow-up (2.2):** roadmap phases/sources of truth corrected;
  the immutability docs now state the protection boundary and its privileged
  database-administrator limits.

**Exit:** the append-only guarantee holds against ordinary SQL for every role;
confirmed by runtime-role and owner-role database probes, migration round-trips,
the drift check, the full backend suite and a fresh-volume E2E run.

## 6. Phase 3 — Nodes & agent v2 ✅ **delivered (2026-10-09)**

**Why:** nodes are the data plane; org-scoped enrollment and the whitelisted
Operations framework must exist before nginx or deploy work rides on them.
Spec: [node-agent-architecture.md](node-agent-architecture.md).

Delivered:

- **DB:** `enrollment_tokens` (org-scoped, single-use, expiring, revocable, hashed),
  RLS + app-role grant; `servers` + `capabilities` JSONB (`{}` = unreported) +
  `protocol_version` + `credential_revoked_at`; `agent_credentials` rotation-grace
  columns; `operations.available_until` / `execution_deadline`; one
  `UNIQUE(docker_hosts.server_id)`. One migration, single head (`a1b2c3d4e5f6`).
- **API:** `/v1/nodes` capability/fact/version exposure; enrollment-token lifecycle
  (`POST/GET /nodes/enrollment-tokens`, `POST …/{id}/revoke`); `POST /agent/enroll`;
  heartbeat v2 (200 + `pending_operations` + `token_rotation` for protocol-2 agents,
  204 unchanged for v1); credential rotate/revoke.
- **Agent:** open-ended capability + fact reporting; a closed pull-model executor
  (`container.start/stop/restart/remove`, `logs.tail` — `nginx.*` arrives in Phase 4);
  honest `/proc/net/dev` network metrics (`null`, never a fabricated `0.0`); Docker
  capability proven by a real `/version` call; token stored 0600; HTTPS-only
  (`--allow-insecure-transport` removed).
- **Security:** stolen-token blast radius = one node; revocation kills acceptance
  immediately (per-node hash, no grace), rotation survives via a bounded dual-token
  grace delivered on the heartbeat; every op maps to a codename (container lifecycle
  → `container.lifecycle`; `logs.tail` → `container.logs`); capability gate on both
  sides; op rows + enrollment audited; per-node agent rate limits.
- **Testing:** enrollment e2e (single-use, expiry, revocation, concurrency); op
  lifecycle and the queue-vs-execution deadline split; agent unit tests; frontend
  enrollment + operation tests.
- **Exit:** a machine enrolls through the one-liner path; ops are audited from
  `pending` to `succeeded`; revocation is immediate.

## 7. Phase 4 — Domains & routes ✅ **delivered (2026-10-10)**

**Why:** the wedge feature — container:port → URL. Spec:
[domain-routing.md](domain-routing.md) (marked implemented for HTTP).

**Shipped (2026-10-10), HTTP only — TLS is Phase 5.** Routes are rendered, applied
and served over plain HTTP; the schema cannot express a TLS listener or an HTTPS
redirect, and nothing in the renderer can emit one (`CHECK (scheme = 'http')`, no
`certificate_id`, no `ssl_*` directive in any template).

- **DB:** `domains` + `routes` (migration `f4a5b6c7d8e9`), tenant RLS and the
  anti-takeover partial unique index on the verified name; monitors became
  polymorphic as `target_type` (`URL`/`ROUTE`) + `route_id`, with every existing
  row backfilled to `URL`; `servers.proxy_state`; the operation whitelist gained
  the three `nginx.*` types.
- **API:** domains (create/list/detail/verify/re-verify/delete, routes-by-domain),
  routes CRUD + enable/disable, node proxy status/refresh/apply and the
  route-target upstream picker; `domain.read`/`domain.manage` codenames; every
  domain/route mutation audited and published as an org-scoped event.
- **Providers:** the nginx renderer (strict templates, `extra=forbid` schemas, no
  user-supplied raw directives) produces a fingerprint + manifest + allowlisted
  file tree; the agent stages → `nginx -t` → atomically swaps → reloads, and
  reports `applied`/`failed`/`rolled_back`/`rollback_failed`. The control plane
  attributes the outcome to routes from the bundle manifest, so state is never
  guessed from config text.
- **Frontend:** Domains list/detail (TXT instructions, reachability warning,
  re-verify, delete-blocked-while-enabled) and a Routes page with the upstream
  picker (node → container → published port), enable/disable and delete.
- **Security:** verification before any route goes live, re-verification and NS
  snapshots, upstream must live on the route's node, header/rate-limit/redirect
  inputs from closed allowlists, and the listener pre-flight (domain-routing.md §5).
  Injection threat modeled in platform-security-model.md.
- **Ownership revocation (hardening pass, same phase).** The cross-org flip is not
  just a row change: the worker discovers the losing organization's nodes inside the
  same system-scoped release step — the only scope that can see another tenant's
  routes — then re-renders and applies **inside each node's own organization**, so
  discovery is cross-tenant and the write is not. The losing organization gets an
  audit row and an org-scoped event that says why without naming the winner. A node
  that is offline or failing stays visibly unresolved and is retried by the
  reconciler; the route is never reported as removed before a node confirms it.
- **Drift reconciliation (same pass).** `sweep-routes` no longer merely re-asks: it
  compares the desired bundle with the node's last known live one, and queues
  exactly one `nginx.apply` when they differ, with a bounded exponential retry for a
  node that keeps failing and a fingerprint refresh interval for one that is
  converged. `NGINX_DRIFT_RECOVERED` is published only from an applied outcome.
- **Testing:** mock-DNS unit + integration suites (verification lifecycle, grace
  window, cross-org flip), a 66-test HTTP integration suite for domains/routes/
  apply/rollback/drift/tenancy — including the ownership-transfer scenario with the
  previous owner's node (online, and separately offline-then-recovered) and the
  reconciler's bounds — render snapshots, agent contract tests (including the
  removal-only bundle that carries no fragment at all), and a Phase 3→4 migration
  test over a populated database. The revocation and reconciliation fixes
  were first reproduced against the pre-fix code: with the old code the released
  organization's domain read `UNVERIFIED` while its API still reported the route
  `IN_SYNC`, **no** apply was queued for its node, and three sweep ticks left a
  drifted node untouched.
- **E2E:** `frontend/e2e/phase4.spec.ts` runs the whole wedge against the throwaway
  stack — a node container that really runs nginx, the real agent enrolled inside
  it, a real authoritative mock nameserver (`e2e/dnsmock`) serving the minted TXT
  record, and an HTTP request through the node's port 80 that reaches the upstream
  container. It asserts the rendered fragment, the 444 catch-all for an unmapped
  Host, `drift: false` with matching bundle ids, and the dashboard's own view. It
  found two real defects while it was being written: bootstrap could not write the
  system `nginx.conf` at all (the managed-tree guard rejected the one path outside
  the tree), and the include it added had no target, so `nginx -t` failed; both are
  fixed and pinned by contract tests.
- **E2E, ownership transfer:** a second scenario in the same spec gives a name to a
  second organization (its own node, its own container, the same mock DNS fixture)
  and proves on the wire that the first organization's route stops being served: the
  old domain goes `UNVERIFIED` and the old owner's audit/event trail says why without
  naming the winner, the old route is excluded from the desired configuration, the
  old node — held unreachable for part of the run — applies the bundle without the
  fragment, an HTTP request with the old Host gets the managed 444 instead of the
  old upstream, no success is claimed while the node cannot apply, the new owner
  serves the name from its own node, and neither organization can read or modify the
  other's rows. It also found the second real defect of this pass, on the agent side:
  a bundle containing **no route fragments** — what every revocation of the last route
  on a node renders to — could not be staged, so the apply failed and rolled back and
  the routes stayed live on the node. The stage writer now creates `routes.d`
  unconditionally, the validation reader treats a missing one as an empty tree, and
  contract tests pin both plus the fingerprint the node reports after a removal.
- **Exit:** met — a route's desired configuration reaches a node as a whitelisted
  op, is applied atomically with rollback, and its outcome is reflected on the
  route; re-verification on apex change pulls the routes; a lost name is removed
  from every node that served it; and the cross-container journeys above prove the
  loop end to end.

## 8. Phase 5 — Certificates — **proposal, not implemented**

**Why:** "HTTPS on by default" is the promise; DNS-01 works for NAT-ed home
servers and wildcards. Spec: [certificate-management.md](certificate-management.md).

- **DB:** `certificates` (ciphertext key+chain, challenge type, auto_renew,
  expires_at); `integrations` for DNS creds (encrypted).
- **API:** cert request/renew/delete + status; renewal scan (celery beat,
  `expires_at < 30d`) with failure alerts + incidents.
- **Providers:** ACME client with DNS-01 first (HTTP-01 via node nginx later);
  `DNSProvider` interface — Cloudflare first, creds from `integrations`.
- **Delivery:** only nodes serving routes that use the cert; encrypted agent
  op delivery; private keys never in API responses/logs/WS/audit/frontend.
- **Frontend:** HTTPS card per domain; expiry visible; failure alerts.
- **Security:** issuance gated on `domains.verified_at`; Let's Encrypt
  **staging** first, rate-limit aware; audit issued/renewed/failed/deployed.
- **Testing:** ACME against pebble/staging; renewal scan; delivery-to-serving-
  nodes-only test.
- **Exit:** auto-renewed cert on a real domain; TLS-expiry monitor attached.

## 9. Phase 6 — Real deployments — **proposal, not implemented**

**Why:** the sim runner's promise, made real — the runner protocol
(`plan_steps`/`execute_step`/`StepLine`) survives; the simulation becomes one
registered runner among two. Spec: [deployment-architecture.md](deployment-architecture.md).

### 9.0 Authorization gate — a prerequisite, NOT a follow-up

**No real deployment execution and no secret delivery to a customer node may
ship before this gate closes.** It is written first, and as a gate rather than a
hardening note, because the feature needs it — scheduling the authorization
review *after* real deploys or secret delivery would ship the exposure first and
close it later.

Today a principal holding `deployment.create` may deploy **any** environment of
its organization (see §5 "Deviations"; [secrets-architecture.md](secrets-architecture.md)
§4/§5). With the simulated runner that is tolerable — nothing leaves the control
plane. The moment 6a executes on a real node, the same permission begins
*delivering that environment's secrets to that node*. Four boundaries that are
today collapsed into one must be reviewed and enforced, each as its own decision:

| Boundary | Question it must answer | Today |
|---|---|---|
| **View secret metadata** (`secret.read`) | Who may see key names, versions, digests and scope? | Enforced; no endpoint returns a value |
| **Create a deployment** (`deployment.create`) | Who may queue a deployment run at all? | Enforced, organization-wide |
| **Deploy to a specific environment** | Who may target *this* environment (e.g. staging but not production)? | **Not enforced** — `deployment.create` is a blanket org permission (resource-level grants are §10 / Phase 7) |
| **Consume that environment's secrets** | Who may cause this environment's referenced secrets to be resolved and delivered to its node? | **Implicit** — follows the deploy; must become an explicit, audited consequence of the environment-target boundary, never a side effect |

The gate closes only when all of the following hold:

- (a) the **environment-target** boundary is *enforced*, not merely documented,
at the moment a deployment is created or executed — the minimal mechanism is the
environment-scoped grant from §10, which may be pulled forward for this purpose;
- (b) **secret consumption** is authorized *through* that boundary, so neither
`secret.read` nor any unrelated permission can trigger resolution or delivery;
- (c) the four boundaries are written down in [authorization.md](authorization.md)
and exercised by an integration test — the Ali/Ahmed scenario currently listed as
§10's *exit* becomes a gate test here;
- (d) resolution and delivery remain audited per
[secrets-architecture.md](secrets-architecture.md) §4.1/§7.

Until the gate closes, 6a stays behind the simulated runner and the honesty chip:
no real node execution, no secret delivery. This is why grants (§10) and real
deploys (§9) are no longer independently schedulable — the gate couples them.

- **DB:** minimal — deployments gain image/git columns in 6a/6b respectively.
- **API:** deploy trigger takes an image (6a) or git source (6b); step lines
  stream over the existing Redis deployment channel; per-step timeouts +
  cancel.
- **Refactor:** runner registry replaces the two hard-instantiation sites in
  `backend/app/services/deployment_engine.py`; `AgentDeploymentRunner`
  implements the existing protocol, dispatching steps as agent operations and
  streaming StepLines back; `SimulatedDeploymentRunner` stays, demo/CI-labeled.
- **6a steps:** resolve → pull image → stop old → run new (env from Phase 2
  layering + secrets) → health check (real gate, `-broken` hook retired) →
  route sync (Phase 4 hook) → finalize.
- **6b steps:** checkout → build (`docker build` on node) → stop → run →
  health → route sync → finalize.
- **Security:** node receives only the secrets its deployment references
  (minimization); deploy permission chain authorizes resolution; ops audited.
  Current gap (security-model H2): the real runner path never receives resolved
  secrets today — `docker_real.py` has zero `ctx.secrets` references; only the
  simulated runner consumes them. 6a wires them in — **after §9.0 closes**.
- **Testing:** e2e against `docker_sim` in CI; real-node e2e manual; rollback
  = new deployment re-deploying last good version (existing behavior kept).
- **Exit:** image deploy on a real node; health gate blocks routing on
  failure; rollback proven.

## 10. Phase 7 — Teams, grants & custom roles — **proposal, not implemented**

**Why:** a five-person team needs resource-level access ("Ali deploys staging,
not production"); org roles alone cannot express it. Spec: authorization.md §4.

- **DB:** `teams`, `team_members`; `grants` (org_id, principal `user|team`,
  principal_id, scope `project|environment|node`, scope_id, role_id);
  `roles.org_id` custom rows (subset of registry, validated).
- **API:** team CRUD, grant CRUD; effective-permission resolution = org role
  ∪ grants, resolved in ONE function next to `user_has_permission()`;
  `require_permission` needs no changes.
- **Frontend:** team management; member detail with per-resource grants
  editor.
- **Security:** custom-role permissions validated ⊆ registry at save; role
  rows FK-protected while referenced; grant changes audited; API keys never
  receive grants (keys are org-bound automation identities).
- **Testing:** effective-permission resolution matrix; grant × environment
  isolation tests (Ali/Ahmed examples as e2e).
- **Exit:** the Ali scenario green as e2e: Developer org-role + staging-env
  grant → deploys staging, blocked on production.

## 11. Phase 8 — Backups — **proposal, not implemented**

**Why:** the "schedule and forget" promise; the design exists
(domain-model.md §2.7). Spec per this section (build phase).

- **DB:** `backup_policies`, `backup_runs`, `backup_destinations`.
- **Providers:** `BackupDestination` interface — local-directory first (keeps
  v1 self-hostable without cloud creds), S3-compatible next; creds in
  `integrations`, encrypted.
- **Ops:** two new whitelisted agent op types: `volume.backup` (tar of named
  volumes), `db.dump` (fixed-param `pg_dump` via docker exec — no shell
  string, container+database params only).
- **Flow:** policy → scheduled op on node → run row → artifact + checksum →
  **verify** (restore test into a scratch container) → retention pruning →
  restore flow (a run of kind `restore`, gated on `backup.restore`).
- **Security:** artifacts encrypted with an org-scoped key before leaving the
  node; destination creds never in API/logs; restore audited; node blast
  radius rule still applies (node gets only its own policies).
- **Testing:** verify step; retention; restore-drill e2e.
- **Exit:** scheduled verified backup + green restore drill on a real node.

## 12. Phase 9 — Billing & metering — **proposal, not implemented**

**Why:** billing attaches to the Organization (design-only until here); the
counters accumulate from Phase 1 so enforcement is a gate, not a backfill.

- **DB:** `usage_counters` materialized (dimensions: nodes, projects,
  deployments, retention GB); org `plan` placeholder from Phase 1 becomes
  enforced.
- **API:** usage endpoints; server-side plan gates (node count, project count,
  retention) — enforced in the service layer, not the UI; audit of gate hits.
- **Frontend:** usage page; limits surfaced *before* the action fails.
- **Security:** gates server-side only; no card data anywhere in the platform
  (payment processing is an external provider integration, out of scope for
  the control plane).
- **Testing:** gate unit tests; counter accuracy vs audit rows.
- **Exit:** free-plan limits enforced with graceful limit UI.

## 13. First commercially meaningful version

**Phases 0–6a.** The demo that sells (platform-vision §2.2):

> Accept an operator-issued invite → org → agent one-liner → node appears with
> live stats → project → deploy an image → `api.example.com` verified → HTTPS
> auto → uptime + TLS-expiry monitoring on by default → invite a teammate (Viewer).

Why this boundary: it is the smallest loop where every promise in the vision
doc is *real* (no simulation), each ingredient maps to a shipped phase, and
nothing in it depends on teams/grants, backups, or billing. (Onboarding is
operator-issued invites, not signup — multi-tenancy.md §2.1.)

**What the customer must bring** — the demo does not work without these, and
every sales conversation states them up front (full checklist: platform-vision
§4):

| Prerequisite | VPS path (credible day one) | Home-server/NAT path |
|---|---|---|
| Domain + DNS | hosted on **Cloudflare** (v1 cert constraint) + scoped API token | same, plus DDNS if the IP is dynamic |
| A/AAAA record → node IP | trivial (static public IP) | user-configured port-forward of 80/443 |
| Reachability | public IP by construction | **CGNAT = unsupported in v1** (no tunnel, by design) |
| nginx on the node, 80/443 free | one apt/yum line | same |
| Public container image | any Docker Hub image | same |

**API note:** the permissioned REST API already exists — the sellable version
ships with a *documented, frozen v1 subset* of it (the endpoints the dashboard
uses), because integrators build against undocumented behavior and competitors'
missing/broken API tokens are a documented blocker (competitive review). This is
a documentation + freeze commitment, not a new workstream.

### 13.1 Scope-creep gates — what must be true before each expansion

Challenge §9 asked for gates, not "later." Each line is the condition under
which the category earns a phase of its own:

| Category | It becomes justified when… |
|---|---|
| **Git builds (6b)** | `deployment.build` codename exists + build isolation is bounded by the op whitelist (authorization.md §2) — **and** trial loss to git-first competitors is measured, not assumed. |
| **Kubernetes runtime** | A paying customer needs scheduling/scaling docker+nginx cannot deliver, **and** the deploy contract (digest pinning, container identity, health gates) has held unchanged for a full release cycle; K8s arrives as a second runtime provider, never a product fork. |
| **SSH terminal / webshell** | **Never while the allowlist holds** — a webshell is `node.execute` under another name and voids the transport trust story. Revisit only if legitimate ops prove the allowlist insufficient, with its own threat-model chapter. |
| **Log platform at scale** | The ship-to-object-storage export is live **and** retention/search complaints come from paying orgs the export does not satisfy. The export is the release valve; a query engine is not. |
| **More DNS providers** | Two implementations minimum to keep the DNSProvider interface honest (Cloudflare + one more) — driven by measured onboarding drop-off at the Cloudflare step. |
| **Private registries** | The registry `Connection` kind + pull-secret delivery design exists (deployment-architecture.md §6a deferral; node-agent-architecture.md secret-delivery path). |
| **Zero-downtime deploys** | Brief-downtime honesty measurably loses deals **and** the two-container health-gated switch + rollback orchestration is designed against the 6a contract. |
| **Cloud provisioning (buy VPS)** | Agent-onboarded (customer-brought) nodes are the saturated path — provisioning re-introduces credential blast radius and needs its own security review. |
| **IaC (Terraform provider)** | The frozen public API v1 has been stable for ≥2 releases — a TF provider is a stability commitment, not a feature. |
| **Plugin marketplace** | Multiple third parties actually ask to extend the op whitelist; until then it stays compile-time-closed (node-agent-architecture.md §5.2). |
| **AI ops** | After the operation registry has a production audit history; read-side suggestions only, never actions. |
| **Multi-region control plane** | Measured agent-pull/monitor-cadence latency from one region harms real customers — nodes are already region-independent (outbound-only). |
| **Enterprise SSO (SAML/OIDC)** | With billing: a paying org with large seat counts demands it; federation grows the auth surface and takes its own platform-security-model.md review. |
| **Self-serve signup** | Gated on billing plans (multi-tenancy.md §2.1): open registration + abuse control + plan enforcement ship together, as one phase. |
| **Usage-tier billing** | The Phase 1 metering counters (domain-model.md §2.7) have accumulated real usage cycles — rates need data to be defensible. |

**Waits until later (each behind its gate above):** 6b (git→build), the remainder
of 7 (teams/custom roles — the environment-scoped grant the §9.0 gate needs may
ship early), 8 (backups), 9 (billing enforcement). **Stays out entirely**
(non-goals, platform-vision §2.1): Kubernetes as the primary runtime, a CI
engine, a log platform at scale, arbitrary remote shell, multi-region control
plane.

## 14. Biggest risks (short form)

- **Technical:** tenancy regression in long-lived code paths (mitigation:
  session guard + IDOR suite as a CI gate); migrating the existing production
  agent to protocol v2 (mitigation: dual-token grace during rotation); nginx
  rendering safety (strict templates, `nginx -t`, atomic apply + rollback);
  Let's Encrypt rate limits (staging-first, DNS-provider reuse); single Fernet
  `ENCRYPTION_KEY` today vs per-org DEK envelope later (KMS-ready design in
  secrets-architecture.md).
- **Product:** scope creep toward CI/K8s (non-goals list + the §13.1 gates are
  the defense); the
  deployment expectation gap — before 6b, image-based deploys must be honestly
  labeled so "Deploy" doesn't imply git-push; trust in a young agent (version
  reporting + out-of-date warnings now, self-update later); supporting a
  heterogeneous Linux fleet (stdlib-only agent mitigates).

## 15. Reading order

[platform-vision.md](platform-vision.md) (why + wedge) →
[domain-model.md](domain-model.md) (entities) →
[multi-tenancy.md](multi-tenancy.md) (enforcement) →
[authorization.md](authorization.md) (permissions) →
this doc (phasing) → the subsystem specs:
[node-agent-architecture.md](node-agent-architecture.md) ·
[domain-routing.md](domain-routing.md) ·
[certificate-management.md](certificate-management.md) ·
[deployment-architecture.md](deployment-architecture.md) ·
[secrets-architecture.md](secrets-architecture.md) ·
[platform-security-model.md](platform-security-model.md).
