# Product Roadmap — NexusOps Multi-Tenant Platform

**Status:** Proposal for review — not yet approved for implementation.
**Date:** 2026-09-20
**Companions:** [platform-vision.md](platform-vision.md) · [domain-model.md](domain-model.md) · [multi-tenancy.md](multi-tenancy.md) · [authorization.md](authorization.md) · [platform-security-model.md](platform-security-model.md)

## 0. Stance

Evolution, not rewrite. Every phase ships value; the production contabo instance
upgrades in place through every phase with zero data loss. Phase numbering here is
authoritative for all companion docs (domains/certs/ops/deployments reference it).

## 1. Migration strategy: what happens to what

Four-way classification, grounded in the subsystem analysis (evidence in
`.claude/workflows/findings.json` and the companion docs).

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
  (`backend/app/services/deployment/engine.py` ~194 and ~345) → a runner
  registry with DI; `AgentDeploymentRunner` added beside the simulated one.
- `resolve_auth`: gains active-org validation (`core/tenancy.py` guard).
- Secret resolution: silent-degrade-to-empty → **fail-closed** + audit event
  at resolution time.
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
  (single-use, expiry, revocation).
- `--allow-insecure-transport` (plain-HTTP agent option) — removed.
- `server.*` permission codenames → `node.*` (one migration).
- `/v1/servers` paths → `/v1/nodes` (alias in Phase 1, removal in cleanup).
- Platform-global `Server.name` uniqueness → per-org.
- The `-broken` health-check demo hook → real healthcheck gating in Phase 6a
  (demo-labeled until then).
- **Kept, not removed:** `sim://` monitors and `docker_sim` stay as
  explicitly-labeled demo/CI tooling (platform-vision §3 honesty principle).

## 2. Phase plan

| # | Phase | Ships | Depends on |
|---|---|---|---|
| 0 | Truth pass & hardening | docs fixed against code; fail-closed secret resolution; agent backoff | — |
| 1 | Tenancy foundation | orgs/memberships/roles, org_id backfill, X-Org-Id + session guard, node rename, IDOR suite green | 0 |
| 2 | Projects & environments | env promotion to project scope, SecretVersion, layered secret scope | 1 |
| 3 | Nodes & agent v2 | capabilities+facts, enrollment v2, Operations framework, HTTPS-only agent | 1 |
| 4 | Domains & routes | Domain/Route entities, DNS verification, NginxProvider, apply pipeline, polymorphic monitors | 3 |
| 5 | Certificates | ACME DNS-01, DNSProvider (Cloudflare first), renewal scan, encrypted delivery, TLS-expiry monitors | 4 |
| 6 | Real deployments | 6a image-based via agent ops; 6b git→build on node | 3 (6a), 3+4 (6b) |
| 7 | Teams, grants & custom roles | teams, resource-level grants, custom roles | 2 |
| 8 | Backups | policies/runs/destinations, verify + restore drill | 3, 7 |
| 9 | Billing & metering | usage-counter enforcement, plan gates | 1, 2 |

## 3. Phase 0 — Truth pass & hardening

**Why first:** the docs contradict shipped behavior (Secure-cookie descriptions,
role counts, limiter algorithm), and three correctness bugs are known: secret
resolution silently degrades to empty on failure, a revoked agent hot-loops
401→exit(1) every ~10s, and the agent install hint emits `NEXUSOPS_URL` where the
agent process reads `NEXUSOPS_SERVER` (`backend/app/api/v1/servers.py:188-192`) —
a fresh install that never connects until the env var is corrected by hand.
Cheap, de-risks everything after; no schema change.

- **Docs:** fix the four Secure-cookie descriptions against
  `backend/app/api/v1/auth.py:27-43`; role counts (5, not 4); fixed-window
  limiter (not token bucket); disclose simulated deployments/sim:// in README +
  architecture.md.
- **API:** no new routes. Deployment trigger fails fast on secret-resolution
  errors instead of deploying with empty values.
- **Frontend:** honesty labels — a "Simulated" chip on deploy/run views until
  Phase 6.
- **Security:** fail-closed resolution + audit event (no values) at resolution
  time; agent auth-failure backoff instead of hot-loop exit.
- **Testing:** unit tests for fail-closed resolution; agent backoff test.

**The hardening list** (kept consistent with platform-security-model.md; items
land in their natural phase — column 3):

| # | Known issue | Lands in |
|---|---|---|
| 1 | Silent secret-resolution degradation (empty dict on failure) | Phase 0 |
| 2 | Agent 401→exit(1) hot-loop on revocation | Phase 0 (backoff), Phase 3 (full revocation semantics) |
| 3 | Agent plain-HTTP option (`--allow-insecure-transport`) | Phase 3 (HTTPS-only) |
| 4 | WS global channel exposure | Phase 1 (org-prefixed channels) |
| 5 | Rate limits keyed by IP only (NAT fleets share a bucket) | Phase 1 (org+IP dimension) |
| 6 | `Server.name` platform-global uniqueness | Phase 1 (per-org) |
| 7 | Audit rows lacking org / request-id | Phase 1 |
| 8 | Secret resolution lacking per-user authorization on the engine path | Phase 0 (fail-closed + audit), Phase 2 (deploy-chain authorization) |
| 9 | Install hint emits `NEXUSOPS_URL`; the agent reads `NEXUSOPS_SERVER` (servers.py:188-192) — fresh installs never connect | Phase 0 |

**Exit:** docs spot-check clean; fail-closed + backoff tested.

## 4. Phase 1 — Tenancy foundation

**Why first (after 0):** every later phase scopes to an org; mechanical
enforcement must exist before resources multiply. Full spec:
[multi-tenancy.md](multi-tenancy.md).

- **DB:** `organizations`, `memberships`; `roles.org_id` (nullable = system
  template); org_id backfill with `server_default` → NOT NULL on projects,
  servers, secrets, monitors, incidents, notification_channels, api_keys,
  deployments (denormalized), audit_logs (+`request_id`), system_events.
- **API:** `X-Org-Id` validation in `resolve_auth` (optional while single-org);
  scoped helpers; codename rename `server.*`→`node.*` (registry, seeded rows,
  ROLE_MATRIX, stored key scopes, code, UI strings); `/v1/nodes` +
  deprecated `/v1/servers` alias; ApiKey org binding.
- **Frontend:** single-org UX unchanged day one; org switcher appears with the
  second org.
- **Security:** `core/tenancy.py` session guard (`with_loader_criteria`) +
  scoped helpers; IDOR suite
  (`backend/tests/integration/test_tenancy_isolation.py`); org+IP limiter
  dimension.
- **Testing:** parametrized cross-tenant suite over every org-scoped listing
  and detail route; two-org fixtures extend the existing RBAC fixtures.
- **Exit:** IDOR suite green; one-org backfill proven on production contabo in
  place; zero user-visible change beyond the rename.

## 5. Phase 2 — Projects & environments

**Why:** the project-centric product model ("Ymart → Production") needs
environments at project scope; per-env config/secrets/grants all anchor here.
Spec: domain-model.md §2.2.1.

- **DB:** `deployment_environments.application_id` → `project_id`
  (NOT NULL after backfill; unique `(project_id, slug)`; slug-collision
  suffix during migration); `environment_type` (dev/staging/prod); `node_id`;
  `projects.config` JSONB (config-layering base). `secret_versions` table
  (append-only); `secrets` layered scope (org / project / environment).
- **API:** env CRUD under `/v1/projects/{id}/environments`; config layering
  (project config ⊕ environment config ⊕ `${secret:KEY}` refs — most specific
  wins); SecretVersion append-only rotation + rollback; deploy-chain
  authorization for resolution (Phase 0's fail-closed policy carries over).
- **Frontend:** environments on the project page; env config editor; secret
  version history with rotation rollback.
- **Security:** resolution authorization = deploy permission chain (never
  `secret.read`); rotation audited.
- **Testing:** promotion-migration round-trip incl. slug-collision suffix;
  layering precedence unit tests; rotation rollback test.
- **Exit:** "Ymart → Production" env config in one place; non-destructive
  rotation with rollback proven.

## 6. Phase 3 — Nodes & agent v2

**Why:** nodes are the data plane; org-scoped enrollment and the whitelisted
Operations framework must exist before nginx or deploy work rides on them.
Spec: [node-agent-architecture.md](node-agent-architecture.md).

- **DB:** `servers` + capabilities JSONB + facts + `agent_version`;
  `enrollment_tokens` (org_id, single-use flag, expires_at, created_by_id,
  revoked_at); `operations` table.
- **API:** `/v1/nodes` extensions (capabilities, facts, version); enrollment
  token lifecycle (create/revoke/list); ops queue (create/status/list, org-
  scoped listing); heartbeat v2 (hello/heartbeat + capabilities + agent
  version via hello).
- **Agent:** capabilities+facts reporting; op executor (pull model) with
  whitelist v1: `container.start/stop/restart/remove`, `logs.tail`
  (`nginx.*` ops arrive in Phase 4 with the provider); token stored 0600;
  auth-failure backoff; HTTPS-only (`--allow-insecure-transport` removed).
- **Security:** stolen-token blast radius = one node; revocation kills token
  acceptance immediately (per-node hash); every op maps to a codename
  (container lifecycle → `container.lifecycle`; `logs.tail` → `log.read`);
  op rows audited; enrollment throttles.
- **Testing:** enrollment e2e (single-use, expiry, revocation); op lifecycle
  (queued→claimed→running→succeeded/failed/expired); agent unit tests.
- **Exit:** second machine enrolled via one-liner; ops audited; revocation
  immediate.

## 7. Phase 4 — Domains & routes

**Why:** the wedge feature — container:port → URL. No code exists today; the
nginx/ dir in the repo serves only the dashboard. Spec:
[domain-routing.md](domain-routing.md).

- **DB:** `domains`, `routes` tables; monitors become polymorphic
  (`target_type`/`target_id`), URL monitors backfilled as `target_type=url`.
- **API:** domains (create/verify/re-verify/delete), routes CRUD, provider
  status; domain/route events org-scoped.
- **Providers:** `ProxyProvider` interface (render/apply/status);
  `NginxProvider` first — renders from STRICT templates (no user-supplied raw
  nginx directives in v1); apply pipeline via agent op: stage → `nginx -t` →
  atomic swap → reload → rollback on failure.
- **Frontend:** Domains page (add domain, DNS TXT instructions + status,
  routes editor with upstream picker: node + container:port).
- **Security:** anti-takeover — verify before any route goes live, re-verify
  on apex change; upstream must live on the route's node; header/rate-limit
  config from an allowlist; injection threat modeled in
  platform-security-model.md.
- **Testing:** verification flow (mock DNS), render snapshots, apply pipeline
  with failing `nginx -t` → rollback.
- **Exit:** a route serving real traffic on a node; re-verify on apex change.

## 8. Phase 5 — Certificates

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

## 9. Phase 6 — Real deployments

**Why:** the sim runner's promise, made real — the runner protocol
(`plan_steps`/`execute_step`/`StepLine`) survives; the simulation becomes one
registered runner among two. Spec: [deployment-architecture.md](deployment-architecture.md).

- **DB:** minimal — deployments gain image/git columns in 6a/6b respectively.
- **API:** deploy trigger takes an image (6a) or git source (6b); step lines
  stream over the existing Redis deployment channel; per-step timeouts +
  cancel.
- **Refactor:** runner registry replaces the two hard-instantiation sites in
  `backend/app/services/deployment/engine.py`; `AgentDeploymentRunner`
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
  simulated runner consumes them. 6a wires them in.
- **Testing:** e2e against `docker_sim` in CI; real-node e2e manual; rollback
  = new deployment re-deploying last good version (existing behavior kept).
- **Exit:** image deploy on a real node; health gate blocks routing on
  failure; rollback proven.

## 10. Phase 7 — Teams, grants & custom roles

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

## 11. Phase 8 — Backups

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

## 12. Phase 9 — Billing & metering

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

**Waits until later (each behind its gate above):** 6b (git→build), 7
(teams/grants/custom roles), 8 (backups), 9 (billing enforcement). **Stays out
entirely** (non-goals, platform-vision §2.1): Kubernetes as the primary runtime,
a CI engine, a log platform at scale, arbitrary remote shell, multi-region
control plane.

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
