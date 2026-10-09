# NexusOps — Phase 1 (Multi-Tenancy) Report

Companion to [multi-tenancy.md](multi-tenancy.md) (design + as-built deltas),
[security.md](security.md) (the tenant security review), and
[architecture.md](architecture.md). Written 2026-10-04; §2 and §4–§8 updated
2026-10-06 for the Phase 1 **hardening pass** (no Phase 2 work was started).
This is the deliverable summary the Phase 1 brief asked for; the design record
stays in the docs above and this does not replace them.

## 1. What Phase 1 delivered

The foundation only: organizations, memberships, tenant-scoped everything, and
PostgreSQL row-level security behind an application role that cannot bypass it.
No Phase 2 work (domains, TLS, billing, backups, Git builds, Kubernetes) was
started.

The core chain is `User → Organization → Membership → tenant-scoped resources`,
enforced at four independent layers:

| Layer | Mechanism | Source |
|---|---|---|
| Request | active org resolved from the caller's **membership** + validated `X-Org-Id`; a JWT is never the tenant boundary | `app/api/deps.py` |
| ORM | session guard: filters every SELECT on an `OrgScoped` mapper, refuses DML without an `org_id` predicate, refuses Core statements | `app/core/tenancy.py` |
| Write stamping | `before_flush` owns new rows and rejects a row that changes hands | `app/core/tenancy.py` |
| Database | RLS `USING` **and** `WITH CHECK` per org-scoped table, under `nexusops_app` (`NOSUPERUSER NOBYPASSRLS`) | tenancy migration |

## 2. Migrations (4, single head)

| Revision | Purpose |
|---|---|
| `a3f1c8d24b6e` | Tenancy foundation: `organizations`, `memberships`, `org_id` on every tenant table with backfill, per-org uniqueness, app role, policies, `app_current_org()`, `server_tags` org trigger |
| `c4e2a1f7b9d3` | Rename `server.*` permission codenames to `node.*`, including stored `api_keys.scopes` |
| `e7c4a2b9d1f3` | Operations framework table + tenant/system RLS policies + explicit app-role grant |
| `f1a2b3c4d5e6` | **Hardening pass: schema-drift repair** — creates the missing `applications.current_deployment_id → deployments` FK and the missing `ix_deployment_steps_created_at`; NULLs orphaned `current_deployment_id` values first; normalises the two doubled `ck_operations_*` constraint names written by the previous revision |

`backend/alembic heads` prints a single head (`f1a2b3c4d5e6`); the whole chain was
applied from empty during the e2e run, so "migrations work from a clean
database" is verified empirically, not by inspection. A committed drift test
(§5) now keeps the models and the migrated schema in lockstep.

**Existing-data strategy (explicit, not arbitrary).** The foundation migration
provisions one bootstrap organization owned by the first user, named after that
person, flagged `is_provisional`, and backfills every pre-existing row to it. It
refuses to guess: `_assert_fully_backfilled` raises with a specific message if a
table has rows but no organization can be provisioned, rather than silently
attributing history to a tenant nobody chose.

## 3. Security mechanisms (per brief requirement)

- **RLS with both directions** — `USING` and `WITH CHECK` on every org table,
  asserted from `pg_policy.polqual`/`polwithcheck`.
- **Catalog completeness test** — any table carrying `org_id` without a policy
  fails the suite, so a new tenant table cannot ship unprotected.
- **RLS bypass probes** — raw `psycopg` as `nexusops_app` with no ORM and no
  guard: cross-tenant reads return nothing, cross-tenant writes are refused.
- **Session guard retained** for developer ergonomics, and its failure mode is a
  loud `TenancyScopeError` (500), never a silent empty result.
- **Identity map** — a single scopes-never-share-a-session test plus the
  guard/RLS combination; `expire_on_commit=False` and relationship/eager loading
  are exercised by the shared session in the suite.
- **WebSockets** — one socket, one organization; frames carry their org and the
  hub drops foreign ones; subscribe-time permission checks on every frame.
- **Redis** — frames are org-tagged and filtered at the hub. Channel names are
  *not* org-prefixed, deliberately (delta 2 in multi-tenancy.md): the global and
  `incidents` channels are shared by every tenant by design, so the filter is the
  single enforcement point rather than a second source of truth.
- **Celery** — no ambient task-level organization. A sweep claims a row, resolves
  its owner, then re-enters that organization (`sweep_session`/`org_for`/
  `org_session`); `SYSTEM_SCOPE_ALLOWED_MODULES` is AST-asserted by
  `tests/unit/test_tenancy_allowlist.py`.
- **Search** — the users section joins `memberships` for the active org, so a
  global user search never becomes a global resource search.
- **Audit** — append-only trigger still rejects UPDATE/DELETE after the tenant
  column was added; every tenant event carries its organization.
- **Agent/node** — token hash resolves to exactly one `(node, org)`; everything
  after resolves inside that org, and the loader re-checks that the credential's
  org agrees with the node's.

## 4. Operations framework (added in this pass)

`node-agent-architecture.md` §5 describes a pull-based, compare-and-set work
queue for whitelisted node actions. The **control plane is now implemented**:

- `operations` table (`OrgScoped`, so guard + RLS cover it), with a DB-level
  `type` whitelist check and a `status` check.
- **Claim** is a single conditional `UPDATE` (`PENDING → CLAIMED`) carrying
  ownership **and** `expires_at`; a second claimant loses and is told the state.
  `attempts` is incremented inside the same statement.
- **Result** is `CLAIMED|RUNNING → SUCCEEDED|FAILED`, same guards. A duplicate
  report against a terminal row is a **200 no-op**; a report against a still
  `PENDING` row is refused (409). Terminal states never transition.
- **Cancel** only from `PENDING` — a claimed op is out of reach by design, since
  recalling it would need the connection to the node this design refuses to open.
- **Expiry sweep** (`nx.expire_operations`, beat every 60s) covers pending and
  claimed alike and audits each transition.
- Whitelist: `container.start|stop|restart|remove`, `logs.tail`, each reusing an
  **existing** codename (`container.lifecycle`/`container.remove`/`container.logs`)
  — no generic `node.execute` grant was added. Params are per-type models with
  `extra="forbid"`; an invalid payload is a 422, not a 500.
- Audit: `operation.create|claim|result|cancel|expire`. Agent-driven rows are
  attributed `agent:<node>` via a new optional `actor_email` on
  `audit_service.record`.
- **The capability gate is enforced, fail-closed (hardening pass).**
  `OperationSpec` records the required capability (`docker` for all five types),
  but a node has no capability column yet — per-node capability advertisement is
  the Phase 2/3 enrollment negotiation and is not built. Rather than dispatch on
  a claim it cannot check, `create_operation` refuses any type whose capability
  is not in `UNIVERSAL_CAPABILITIES` (`{"docker"}`, which enrollment itself
  guarantees) with `409 NODE_CAPABILITY_UNVERIFIED`. Every implemented type is
  universal, so the whitelist is unchanged, and the boundary is proven by
  `test_operation_registry.py` (registry shape) plus
  `test_dispatch_refuses_a_type_whose_capability_cannot_be_verified`
  (integration). A type needing a non-universal capability is refused until the
  negotiation exists.

Reserved types from the companion documents (`secret.env.apply`,
`certificate.*`, the `nginx.*` family) are deliberately **not** implemented, so
no pass-through exists for them. The boundary between operation creation, the
agent claim/result path, and delivery is written out in
`node-agent-architecture.md` §5.4.

## 5. Tests

| Suite | Result |
|---|---|
| `pytest` (whole backend) | **483 passed** (481 + the 2 drain tests) |
| `tests/integration/test_tenant_isolation.py` | **24 passed** |
| `tests/integration/test_operations.py` | **19 passed** (was 16) |
| `tests/integration/test_tenant_concurrency.py` | **9 passed** (new) |
| `tests/integration/test_migration_drift.py` | **2 passed** (new) |
| `tests/unit/test_operation_registry.py` | **8 passed** (new) |
| `tests/unit/test_ws_hub.py` | **9 passed** (was 8) |
| `tests/unit/test_event_publish_drain.py` | **2 passed** (new — integrity pass) |
| frontend `vitest` | **176 passed** (32 files) |
| `ruff format --check` / `ruff check` / `mypy app` | clean (171 files / 125 sources) |
| `tsc --noEmit` / `eslint --max-warnings=0` | clean |
| Playwright journey | **11 passed** — from a **removed volume**, i.e. a database built from zero |

Added in the first pass:

- **Write-side IDOR matrix** — the mutation test now covers all ten mutating
  routes across five resources (nodes, secrets, monitors, projects,
  notification-channels), each probed twice (real id vs random uuid) with the two
  responses required to be identical, plus an immutability control per resource.
- **Secret-boundary test** — another tenant sees neither the key, the digest, nor
  the value, and the 404 body echoes nothing from the row.
- **Operations suite** — CAS (loser learns the state), duplicate-result no-op,
  result-before-claim refusal, cancel semantics, expiry gating claim, sweep
  across two tenants, operator IDOR (read + cancel), agent token cross-node in
  another org *and* in the same org, dispatch preconditions (unenrolled → 400,
  OFFLINE → 409), per-type permission (Viewer denied `container.lifecycle` but
  allowed `node.read`), filter/pagination, raw-SQL RLS probes, and the
  no-scope-fails-loudly guard.

## 6. Tooling: reproducible e2e

`make e2e` is now self-contained: it brings up its own compose project
(`nexusops-e2e`) on its own host ports with `ENVIRONMENT=test` — which is what
makes the seeded admin password deterministic — waits for the **edge and the
Celery worker**, seeds, runs the journey, then tears everything down including
the volume. A dev stack on the default ports is untouched. `make e2e-stack`
leaves it running for debugging; `make e2e-down` removes it.

`docker-compose.e2e.yml` is committed (it used to be an untracked throwaway), and
the edge/mailpit addresses are overridable via `E2E_BASE_URL` / `E2E_MAILPIT_URL`
so the journey is not pinned to port 8080.

Two harness bugs were found and fixed while proving this: the seed was silently
connecting to the *dev* port (a `VAR=1 OTHER=${VAR:-x} cmd` shell subtlety), and
`wait-ready` only checked the edge, so the journey could outrun worker warm-up.

Also fixed: `docs/*` claimed the isolation suite had 22 tests when it had 23
(now 24), and three docs pointed at a filename that does not exist
(`test_tenancy_isolation.py` → `test_tenant_isolation.py`).

Added in the hardening pass (P1–P5 of the hardening brief):

- **P1 — WebSocket event-stream failure, root-caused and fixed.** The handshake
  was rejected `403` by the origin check and the SPA reconnect-looped. Root
  cause: nginx forwarded `Host $host`, which drops the port, while a browser at
  `http://127.0.0.1:8090` sends `Origin` with a netloc of `127.0.0.1:8090` — so
  `_is_same_origin` could never match off the default port, and the e2e
  `:8090` edge was not in `CORS_ORIGINS`. Fixed in `nginx/default.conf.template`
  (forward `$http_host`, falling back to `$host`), proven by curl (`:8090 →
  101`, `http://evil.example → 403`) and by the journey. A second, real defect
  was found alongside it: the SPA never proved liveness after subscribing while
  the hub reaps sockets idle for 120 s, so a 30 s client keepalive was added.
  Tests: a `_is_same_origin` port unit test; `useEventStream` reconnect +
  heartbeat tests; journey test 11 (deterministic socket-drop → reconnect);
  journey test 10 now gates on an observed subscribe ack rather than a fixed
  wait.
- **P2 — tenant context under concurrency and connection pooling.**
  `test_tenant_concurrency.py` (9 tests): a reused pooled connection carries no
  tenant GUC; a failed transaction/rollback leaves no scope; ContextVars are
  restored after an exception; 12 concurrent tasks over a 2-connection pool never
  see each other's org; concurrent `_entity_exists` WS subscribe checks; explicit
  re-arm across scopes on one session; `system_write_scope` restores the tenant;
  an unscoped read after scoped work raises `TenancyScopeError`; and the worker
  `sweep_session` → `org_for` → `org_session` path.
- **P3/P4 — operations boundary + capability gate.** `test_operation_registry.py`
  (8 tests) pins the registry shape, that every declared permission is a real
  codename, that no `node.execute`/`*.execute` exists, that no reserved Phase-2
  type is registered, that every params model is `extra="forbid"`, and that
  `ensure_dispatchable` refuses a non-universal capability. `test_operations.py`
  gained the reserved-type `422`, the DB-`CHECK` refusal of `nginx.reload`, and
  the capability `409`.
- **P5 — model/migration drift test.** `test_migration_drift.py` runs Alembic's
  own `compare_metadata` against the migrated database and requires an empty
  diff, and asserts the operations `type` CHECK is exactly the enum.

## 7. Known limitations and unresolved issues

1. **RESOLVED (hardening pass): the WebSocket event-stream failure was the
   origin check, not socket liveness.** Root-caused empirically — the handshake
   was rejected `403` because nginx's `proxy_set_header Host $host` drops the
   port, so the browser's `Origin` netloc `127.0.0.1:8090` never matched `Host`
   `127.0.0.1` and `_is_same_origin` failed on the non-default e2e port. Fixed by
   forwarding `$http_host` (see §6). A secondary defect was found and fixed too:
   the SPA never sent anything after subscribing while the hub reaps sockets
   idle for 120 s. Journey test 11 now proves reconnect-after-drop
   deterministically, and test 10 gates on an observed subscribe ack.
2. **RESOLVED (hardening pass): the capability gate is now enforced,
   fail-closed.** Nodes still have no capability column — per-node capability
   advertisement is the enrollment negotiation that lands with Phase 2/3 — so
   `create_operation` refuses any type whose capability is not in
   `UNIVERSAL_CAPABILITIES` (`{"docker"}`, guaranteed by enrollment) with
   `409 NODE_CAPABILITY_UNVERIFIED`, rather than assuming an unverifiable claim.
   All five implemented types are universal, so nothing regressed; a future type
   needing a non-universal capability is refused until the negotiation exists.
   What was already enforced: the node exists in the caller's org, is enrolled
   (`agent_enrolled_at`), and is not OFFLINE.
3. **Operations: delivery to the agent is not wired — RESOLVED (Phase 3).**
   *(At the time of this report, the architecture's "pending op ids in the
   heartbeat response" (§5.1) would change the heartbeat's 204 contract, which
   agents and the journey assert, so claim/result were reachable by id but nothing
   handed the agent its ids, and the reference agent did not poll or execute
   operations.)* Phase 3 resolved it exactly as the architecture proposed, without
   breaking v1: negotiation is explicit, a **protocol-2** heartbeat returns
   `200` + `pending_operations` while a protocol-1 agent still gets the original
   `204`, and the reference agent claims, executes (closed registry) and reports
   those operations. See `node-agent-architecture.md` §4.1/§5.
4. **`Operator → DevOps` role rename remains deferred** (documented as pending in
   authorization.md), as does `servers` table / Python-internal renaming to
   `nodes`.
5. **RESOLVED (hardening pass): a drift test now exists.**
   `tests/integration/test_migration_drift.py` compares `Base.metadata` with the
   migrated database via Alembic's `compare_metadata` and requires an empty diff,
   so a model change without a migration fails immediately and locally rather
   than late in an unrelated integration test. Writing it surfaced four real
   schema defects, all fixed by `f1a2b3c4d5e6`: a `use_alter` FK that was never
   emitted (no `applications → deployments` FK existed in the database), a
   missing `ix_deployment_steps_created_at`, and two operations CHECK constraints
   whose names were doubled by the naming convention.
6. **`ENVIRONMENT=test` is required for deterministic e2e seeding** and that
   coupling is now documented in `docker-compose.e2e.yml` and the Makefile rather
   than being an undocumented precondition.
7. **RESOLVED (integrity pass, 2026-10-07): every worker-published event frame was
   being dropped, so no monitor or incident notification ever reached Redis.**
   `event_bus` cannot publish inside the transaction (the row is not visible yet,
   and a rollback must announce nothing), so its `after_commit` hook schedules the
   publish as a task on the running loop. A Celery task ran its coroutine under
   `asyncio.run`, which closes that loop — and cancels what is still pending — the
   instant the coroutine returns, so a task whose last statement is a commit lost
   its   own frame. Proven by an A/B probe against a live worker: the identical publish
   committed with no further `await` never reached Redis (`[]`), while the same
   commit with one extra loop turn delivered it (`['MONITOR_DOWN']`) and produced a
   `SENT` delivery plus the email. `event_bus.flush_pending_publishes()` now drains
   the in-flight frames (bounded, and it logs any that do not make it) and
   `run_async` / `scripts/seed.py` await it before their loop closes;
   `tests/unit/test_event_publish_drain.py` pins it. This was invisible to the suite
   and to the e2e run while the e2e database was a recycled volume — the stale
   delivery rows were re-sent by the retry sweep, which is exactly why the fresh
   database (no rows to retry) failed test 5 and the recycled one passed.
8. **An organisation or user hard-delete is not implemented, and would be blocked
   if it were.** `Base.metadata.sorted_tables` warns about a real FK cycle
   (`organizations → users → roles → organizations`), which only matters to
   `create_all`/`drop_all` — nothing in the repo calls either, teardown TRUNCATEs
   and migrations are explicit Alembic ops. The concrete consequence measured on
   the throwaway stack: `DELETE FROM organizations` first trips the append-only
   audit trigger (`audit_logs is append-only (attempted DELETE)`) and would then
   meet `users.role_id → roles.id ON DELETE RESTRICT`. Whoever builds deletion has
   to handle both deliberately.

## 8. Position

This is a foundation, not a product. The hardening pass closed the two most
serious open items — the WebSocket event-stream defect (root-caused, fixed, with
a deterministic reconnect test) and the unenforced capability gate (now a
fail-closed boundary) — added a tenant-concurrency suite and a model/migration
drift test, and repaired four real schema defects the drift test surfaced.

The integrity pass that followed (2026-10-07) re-ran everything against a database
built from zero and **found a fifth, worse defect**: no worker-published event frame
reached Redis, so monitor/incident notifications never left the process (item 7 in
§7). It hid behind a recycled e2e volume — the retry sweep re-sent the previous
run's stale delivery rows, which satisfied the assertion — so the fresh database was
what surfaced it. That, plus the WebSocket origin fix, is the whole reason `make e2e`
is now run from a removed volume rather than "a stack that happens to be up".

What remains open is Phase 2 by design: per-node capability advertisement,
operations *delivery* to the agent (which changes the heartbeat contract), the
deferred renames, and organisation/user deletion (item 8). The honest summary is
that the *tenant boundary and the event spine* are done and evidenced end to end,
the *operations surface* is a fully-gated control plane still waiting for its agent,
and no Phase 2 work was started.
