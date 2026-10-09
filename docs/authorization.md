# Authorization Architecture

**Status:** Partly implemented. The org-aware authorization half shipped with
Phase 1 (§0); the registry changes in §2 and the grants/custom-role work in
§4 and §7 remain design.
**Date:** 2026-09-20 (authorization change implemented 2026-09-24)

## 0. What shipped (Phase 1)

**Authority is the membership, not the user.** A request's permissions come from
`Membership.role` **in the active organization** (`app/api/deps.py`
`_load_permissions`); `User.role_id` survives only as the default applied when a
membership is created. The consequences are load-bearing:

- a person can be an Admin in one organization and a Viewer in another, and the
  same access token means different things in each;
- `ctx.has_permission()` returns **False** whenever the request has no active
  membership — including for a user whose account-level role would have granted
  the codename;
- an API key still passes its own scope check *first*, so a least-privilege key
  stays least-privilege even if its owner is a superadmin;
- `User.is_superadmin` remains an instance-operator escape hatch and bypasses the
  membership check (deliberately: it is how the bootstrap owner administers a
  fresh instance), but it does **not** widen tenancy — every read still has to
  name an organization the user belongs to, so a superadmin in org B cannot see
  org A's rows.

**One gate, one org check.** `require_permission(...)` is unchanged and remains
the only HTTP gate; the active organization is resolved once per request in
`resolve_auth` (`X-Org-Id` for humans, `api_keys.org_id` for machine keys — the
header is *ignored* for key auth so a key cannot be reinterpreted into another
tenant). WS subscribe frames re-check permissions **and** the channel's
organization against the socket's binding (`app/ws/hub.py`).

**Member management is organization-local.** `PATCH /users/{id}` writes the role
held in the active organization and `DELETE /users/{id}` suspends that
membership; neither touches the account or its sessions. An organization's last
active member cannot be suspended (`LAST_MEMBER_PROTECTED`), the multi-tenant
successor to the last-superadmin guard.

**Shipped from this document:** the `server.*` → `node.*` registry rename
(including `credential.write` → `node.credential.write`) and the `/v1/nodes`
API surface, applied in one migration (`20260923_1000-c4e2a1f7b9d3`) that also
rewrites the stored API-key scope strings. **Not shipped:** the `Operator` →
`DevOps` role rename, the new codenames (`member.invite`, `org.manage`, …) and
everything in §4/§7. Permission codenames today are exactly the ones in
`backend/app/core/permissions.py`; the registry is still instance-wide
(`roles.org_id` is NULL for every row in v1).

## 1. Principles (already true in the codebase, kept)

1. **Permissions are data.** Every capability is a `PermissionSpec` in
   `backend/app/core/permissions.py`; seeded into `permissions` rows; checks resolve
   against role→permission rows. `if user.role == "admin"` is banned — the only
   gates are `user_has_permission()` / `require_permission()` / the WS subscribe
   re-check.
2. **One gate.** `require_permission()` stays the single HTTP gate; the WS hub
   re-checks permissions on every subscribe frame (backend/app/ws/hub.py).
3. **Wildcards** (`*`, `node.*`) exist via `scope_matches`/`fnmatch` — reused for
   API-key scopes and role wildcards.

## 2. Registry changes (Phase 1 + new subsystems)

**Renamed (shipped):** `server.*` → `node.*` across the registry, seeded
permission rows, `ROLE_MATRIX`, stored API-key scope strings, code, routes, SPA
strings and docs (migration `c4e2a1f7b9d3`). `credential.write` became
`node.credential.write`; the old `/v1/servers` routes remain as a schema-hidden
compatibility alias.

**Add:** `member.invite`, `member.remove`, `org.manage`, `billing.manage`,
`domain.read`, `domain.manage`, `certificate.read`, `certificate.manage`,
`backup.read`, `backup.create`, `backup.restore`, `operation.read`. Plus
`deployment.build` (Phase 6b git builds — DevOps holds it via the `deployment.*`
wildcard, Developer explicitly; 6b ships only after this codename exists).

**Deliberately NOT added: `node.execute`.** There is no remote shell. Operations are
whitelisted types, each mapping to an existing or new codename (container lifecycle
→ `container.lifecycle`; nginx apply → `domain.manage`). If a legitimate need for
general exec ever appears, it gets its own codename + stricter approval — never a
generic execute permission.

**Shipped (2026-10-04):** the operations control plane, authorised exactly as
above — dispatch and cancel check the codename the operation *type* declares
(`container.lifecycle`, `container.remove`, `container.logs`), which is why the
route cannot express it as a static FastAPI dependency. **`operation.read` was
not added:** listing and reading operations uses `node.read`, since an operation
is a node-scoped artifact and no separate read grant is needed yet. Only the
`container.*` types are whitelisted; `nginx.*` and the reserved secret/cert types
ship with their subsystems. Dispatch is additionally **capability-gated,
fail-closed** (Phase 3): a node that has not reported a capability is refused
`409 NODE_CAPABILITY_UNVERIFIED`, and a node that reports it absent is refused
`409 NODE_CAPABILITY_MISSING` (see node-agent-architecture.md §5.4). The agent
re-checks its own registry and local capability before executing, so a stale
server-side claim cannot cause an unsafe run.

**One name: DevOps.** *(Not shipped.)* The stored system-role row will be renamed
`Operator` → `DevOps` (the FK-facing change is the `roles.name` value on the
org-NULL template rows; membership rows reference role IDs, so the rename is a seed
update, not a data migration). Until it lands the seeded role is still `Operator`.
No display-vs-stored split: docs, API, and DB use one name.

## 3. The five system roles (target)

Per-role permission sets (authoritative source after migration: `ROLE_MATRIX` in
`backend/app/core/permissions.py`):

- **Owner** — wildcard `*`. Plus: sole holder of `billing.manage`; org transfer
  requires Owner. Exactly one active Owner per org.
- **Admin** — everything except: `billing.manage`, and Owner-only actions
  (org transfer, org delete). All registry groups read+manage.
- **DevOps** — all `node.*`, `container.*`, `domain.*`, `certificate.*`,
  `deployment.*` incl. rollback, `monitor.*` incl. incident.action, `backup.*`
  (read/create/restore), `project.read` + `project.manage`,
  `operation.read`, `secret.read` (metadata), `metric/log/event.read`,
  NO user/role/member/org/billing manage, NO `secret.write`.
  This is the "Ali deploys staging" role *without* grants; grants narrow it further
  (§4).
- **Developer** — `node.read`, `container.read`, `container.logs`,
  `project.read`, `deployment.read/create/cancel`, `monitor.read` +
  `monitor.manage` + `incident.action`, `domain.read`, `certificate.read`,
  `metric/log/event.read`, `secret.read` (metadata), `operation.read`.
- **Viewer** — all `*.read` codenames incl. `audit.read`? No — `audit.read` stays
  Admin+: Viewer = `node.read`, `container.read`, `container.logs`, `project.read`,
  `deployment.read`, `monitor.read`, `domain.read`, `certificate.read`,
  `metric/log/event.read`, `operation.read`. No actions anywhere.

## 4. Grants (resource-level access; design now, later phase)

- Shape (from domain-model.md §2.1): `org_id, principal (user|team), principal_id,
  scope (project|environment|node), scope_id, role_id`.
- Effective permissions = org role ∪ grants, resolved in ONE function next to
  `user_has_permission()`; require_permission needs no changes.
- Example: Ali = Developer org-role + Grant(staging env → DevOps) → can deploy
  staging, cannot touch production. Ahmed = Viewer + Grant(node-3 → DevOps) → can
  restart containers on node-3 only.
- Environments are the natural grant scope because Phase 2 promotes them to
  project level — the Ali example needs env-level grants.

## 5. API keys

- Bind to ONE org (`org = key.org_id`; header ignored for key auth).
- Scope lists keep the existing wildcard semantics (`scope_matches`); effective
  scope = stored scopes ∩ org-role permissions of the key's creator-role... (no: keys
  are independent principals) — effective = stored scopes only, but never exceeding
  the org's registry; key creation requires `apikey.write`... (design detail: keep
  current creation flow, add org binding + membership check).
- One key per automation purpose; rotation = new key + swap + revoke old.

## 6. Enforcement mechanics (unchanged patterns, one addition)

1. HTTP: `require_permission(...)` — unchanged.
2. WS: per-subscribe permission re-check — unchanged, plus org check (§5 of
   multi-tenancy.md).
3. NEW: active-org validation in `resolve_auth` (X-Org-Id header vs active
   memberships) — one place, every request (multi-tenancy.md §2).
4. Background jobs: permission-less by design; the *action* that queued them was
   permissioned; task base re-asserts org scope (multi-tenancy.md §4).

## 7. Custom roles (later phase)

- `roles.org_id` rows; permissions must be a subset of the registry (validated at
  save); system templates stay org_id NULL.
- Custom-role changes are audited; role rows are never deleted while referenced
  (memberships FK protect); rename = display only.

## 8. Permission-change audit

Registry migrations are audited like any migration: the migration script writes
audit rows (actor: system) for registry diffs (codename renames, matrix changes),
so an org's role history is reconstructable from the audit log.
