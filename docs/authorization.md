# Authorization Architecture

**Status:** Proposal for review — not yet approved for implementation.
**Date:** 2026-09-20

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

**Rename in one migration:** `server.*` → `node.*` (registry, seeded permission
rows, ROLE_MATRIX, stored API-key scope strings, code, UI strings). `credential.write`
becomes `node.credential.write`.

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

**One name: DevOps.** The stored system-role row is renamed `Operator` → `DevOps`
in the Phase 1 seed migration (the FK-facing change is the `roles.name` value on
the org-NULL template rows; membership rows reference role IDs, so the rename is
a seed update, not a data migration). No display-vs-stored split: docs, API, and
DB use one name.

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
