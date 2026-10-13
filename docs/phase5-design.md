# Phase 5 — HTTPS, Certificates and Private-Key Delivery — Design

**Status:** Authoritative Phase 5 design. **Phase 5.1 is shipped; everything else in
Phase 5 is design only.** Shipped (2026-10-12, `37b7211`): the `certificates` and
`certificate_generations` tables, the pre-issuance generation lifecycle, the
`certificate.read`/`certificate.manage` codenames with the role matrix, both tables'
RLS policies and grants, and the metadata-only certificate API — see §1.1 for the
verified inventory. **Not shipped:** the organization DEK envelope and its KEK
provider, DNS-provider credentials, ACME accounts and issuance, private-key delivery,
HTTPS activation, renewal, expiry monitoring and revocation (§6, §7, §8, §9, §10.1).
**Key-management gate closed 2026-10-12:** the KEK provider direction is approved (§6.7)
and its operational custody specified (§6.9), which unblocks 5.2.1 — the provider adapter
and the organization DEK envelope, planned in §10.5. Approved is not implemented: no
provider, adapter, key or envelope column exists in the tree.
Every schema, endpoint, operation type and agent behavior below outside the §1.1
Phase 5.1 block is labelled *design* and is not implemented; the documents that
describe the other shipped subsystems — domains/routes/nginx (Phase 4) and the
operation control plane (Phase 1/3) — are [domain-routing.md](domain-routing.md) and
[node-agent-architecture.md](node-agent-architecture.md).
**Date:** 2026-10-12 (implementation status reconciled with the shipped tree; KEK
key-management decision approved)
**Baseline:** Phase 4.4 `ddd9727` (the Phase 4 starting point recorded in §1.1) +
**Phase 5.1 `37b7211`** (certificate metadata, pre-issuance lifecycle, org-scoped
metadata API — the current baseline for every later slice).
**Companions:** [certificate-management.md](certificate-management.md) ·
[domain-routing.md](domain-routing.md) · [node-agent-architecture.md](node-agent-architecture.md) ·
[secrets-architecture.md](secrets-architecture.md) · [platform-security-model.md](platform-security-model.md) ·
[multi-tenancy.md](multi-tenancy.md) · [authorization.md](authorization.md) · [domain-model.md](domain-model.md)
**Supersedes for Phase 5 decisions:** the per-decision open questions in
certificate-management.md (ACME client, per-org account, wildcard bind error shape,
renewal window) are resolved here; that document remains the subsystem overview and
is corrected to agree with the shipped tree in the same change.

This document introduces no migration, no endpoint, no dependency and no agent protocol
change of its own — including in this reconciliation. Where it says "add", it means "the
slice that implements that part of Phase 5 will add", not "this change adds". The one
slice that has shipped (5.1) is recorded by reference to its own commit and migration in
§1.1; its schema is described here as *as built*, and every other description below is
*design*, labelled as such.

---

## 1. Architecture and trust boundaries

### 1.1 What actually shipped (the starting point)

Two baselines matter to this document: the Phase 4 HTTP half (where the design
started, verified at `ddd9727`) and the shipped Phase 5.1 slice (the current starting
point for 5.2, verified at `37b7211`).

**Phase 4 (HTTP half) — verified at `ddd9727`:**

| Fact | Ground |
|---|---|
| `domains` and `routes` are tenant tables (`OrgScoped` → session guard + RLS) | `backend/app/models/routing.py` |
| `routes.scheme` is a closed CHECK of `'http'`; there is **no** `certificate_id` column | `backend/app/models/routing.py` (`scheme_http_only`) |
| A route's `redirect` is host-only — no `to_scheme`, so no HTTPS redirect is representable | `backend/app/models/routing.py`, `backend/app/schemas/proxy.py` (`RouteRedirect`) |
| One verified name platform-wide, via partial unique index `lower(name) WHERE status='VERIFIED'` | `backend/app/models/routing.py` (`uq_domains_verified_name`) |
| One nginx answer per name+prefix per node, among enabled routes only | `backend/app/models/routing.py` (`uq_routes_node_host_path`) |
| The bundle is a **closed tree**: fingerprint, template version, manifest, allowlisted files. No certificate/key field, no managed path for one | `backend/app/schemas/proxy.py` (`NginxBundle`, `MANAGED_ROOT`) |
| The renderer is pure; same node + same enabled routes ⇒ same fingerprint | `backend/app/providers/proxy.py`, `backend/app/providers/nginx.py` |
| Three whitelisted ops — `nginx.bootstrap` (120s), `nginx.apply` (180s), `nginx.status` (60s) — gated by `domain.manage` + the `nginx` capability | `backend/app/schemas/operation.py` (`OPERATION_SPECS`), `backend/app/models/enums.py` (`OperationType`) |
| Agent apply pipeline: stage → `nginx -t` → backup + atomic swap → reload → rollback | `agent/nexusops_agent.py` (`_stage_bundle`, `_staged_test_conf`, `_swap_tree`, `_restore_tree`, `_nginx_apply`) |
| Delivery is pull-based: the v2 heartbeat returns pending op ids; the agent claims (CAS) and receives `params` in the claim response | `backend/app/api/v1/agent.py` (`agent_heartbeat`, `claim_operation`), `backend/app/services/operation_service.py` |
| `proxy_state` has **one writer per transaction**, behind `SELECT … FOR UPDATE` taken before the read; lock order `servers → routes → monitors` | `backend/app/services/proxy_service.py` (Phase 4.4) |
| Redaction recurses dicts/lists/tuples at any depth **and** matches PEM armored content; it runs on every structlog record | `backend/app/core/logging.py` (Phase 4.4, S8) |
| There is a single platform-wide Fernet key, `ENCRYPTION_KEY`; decrypt fails closed on mismatch | `backend/app/core/security.py` (`_fernet`, `encrypt_str`, `decrypt_str`) |
| `certificate.read` / `certificate.manage` are **not** in the permission registry; only `domain.read` / `domain.manage` exist *(the Phase 4 baseline — both codenames are registered in 5.1, below)* | `backend/app/core/permissions.py` |
| There is no ACME client, no `dns_providers` table, and the agent registry has no `certificate.*` handler | `agent/nexusops_agent.py` (`OPERATION_REGISTRY`) |

**Phase 5.1 (certificate metadata and pre-issuance lifecycle) — shipped, verified at
`37b7211`:**

| Fact | Ground |
|---|---|
| `certificates` and `certificate_generations` exist as tenant tables (`OrgScoped` → session guard + RLS) with the `certificates_tenant`/`certificates_system` and `certificate_generations_tenant`/`certificate_generations_system` policies and app-role grants | `backend/alembic/versions/20261012_1200-c8d9e0f1a2b3_phase5_certificate_metadata.py`; `backend/app/models/certificate.py` |
| The generation `state` CHECK is limited to `PENDING`/`ORDERING`/`CHALLENGE_PUBLISHED`/`VALIDATING`/`FAILED`, so a material-less `ISSUED` generation is refused by the database | same migration (`ck_certificate_generations_state_valid`, asserted by `backend/tests/integration/test_migration_drift.py`) |
| The one-live-generation partial unique index exists over exactly those four mutable states | `uq_cert_generations_one_live`; `backend/tests/unit/test_certificate_lifecycle.py` |
| Certificate status is **derived** on read from the newest generation; `current_generation_id` is NULL until an issuance exists, and the read model reports `issued: false` | `backend/app/services/certificate_lifecycle.py`, `backend/app/services/certificate_service.py` |
| `certificate.read` / `certificate.manage` are registered with the approved role matrix (Owner wildcard, Admin/Operator read+manage, Developer/Viewer read) | `backend/app/core/permissions.py`; `test_the_registry_and_the_committed_role_matrix_agree` |
| The metadata API exists: `POST`/`GET`/`GET {id}`/`PATCH`/`DELETE /certificates`, metadata-only, no material fields in any response schema | `backend/app/api/v1/certificates.py`, `backend/app/schemas/certificate.py`, [api.md](api.md) |
| **Not** shipped in 5.1: `organizations.dek_ciphertext`/`dek_generation`, the KEK provider, `dns_providers`, `acme_accounts`, `certificates.dns_provider_id`, the generation material columns and `deke_id`, the widened `state` vocabulary, the material guard CHECK, `routes.certificate_id`, the agent `certificate.*` handlers, and every worker/beat task | verified by `backend/tests/integration/test_migration_phase5.py` (`test_the_slice_boundary_is_not_forward_referenced`) |

### 1.2 Phase 5 in one sentence

Phase 5 makes a **verified Domain** able to serve its routes over **HTTPS** by issuing
a certificate at the control plane, delivering the private key to exactly the nodes
that serve routes using it, and applying a configuration the node has validated —
while keeping **HTTP working until the new HTTPS endpoint has been independently
tested**, and keeping **every lifecycle stage separately observable** (issued ≠
delivered ≠ installed ≠ applied ≠ verified ≠ active).

### 1.3 Trust boundaries Phase 5 adds

The existing boundary set is in platform-security-model.md §3. Phase 5 changes three
things and must not change others:

```mermaid
flowchart LR
    subgraph CP["CONTROL PLANE (platform-trusted)"]
        API[API]
        WRK[worker + beat]
        ACME["ACME client<br/>(new, control-plane only)"]
        KEK["ENCRYPTION_KEY (KEK)<br/>wraps org DEK"]
        DEK["org DEK (wrapped on organizations row)"]
        PG[(Postgres: certificates, cert_generations, dns_providers)]
    end
    subgraph EXT["EXTERNAL"]
        LE[("Let's Encrypt<br/>ACME directory")]
        DNS[("Customer DNS API<br/>Cloudflare v1")]
    end
    subgraph DP["DATA PLANE (customer nodes)"]
        AG[Agent]
        NG[nginx + ssl_certificate]
    end
    WRK --> ACME --> LE
    ACME --> DNS
    API <--> PG
    WRK <--> PG
    KEK --> DEK
    AG -->|"pull + claim (X-Agent-Token, TLS)"| API
    API -->|"claim response: chain + key, in-memory assembly"| AG
    AG --> NG
```

| # | Boundary | Direction | Rule |
|---|---|---|---|
| B8 | Control plane → ACME CA | outbound HTTPS | The ACME client lives in the API/worker. Nodes never talk to the CA (certificate-management.md §4). |
| B9 | Control plane → customer DNS API | outbound HTTPS | Customer DNS tokens are written once, stored encrypted, **never delivered to a node**, and never returned by any API (metadata-only reads). |
| B10 | Control plane → node, certificate material | pull-only | The agent pulls; private key material exists in the claim response body assembled at read time, and is never persisted in the operation row, its result, events, audit or logs. |
| B11 | KEK → org DEK → certificate key/chain | in-process | Key hierarchy on the control plane; `ENCRYPTION_KEY` remains the root (§6). |

### 1.4 Non-goals for Phase 5

- **No node-side key generation.** v1 generates keys control-plane-side (the platform
  is the CA client and key custodian). Node-side keygen/CSR is a later phase and is
  called out as an accepted trust concentration here (§1.5), not silently dropped.
- **No re-encryption of the existing secret store.** `secrets`, `secret_versions`,
  `server_credentials` and `notification_channels.config_ciphertext` keep using the
  current single-key path. Moving them to the org-DEK envelope is a separate reviewed
  migration (§6.4), not a Phase 5 side effect.
- No custom CA / private PKI, no HTTP-01 in v1, no multi-cert-per-route, no
  `node.execute`, no shell.
- No HTTP→HTTPS redirect until the HTTPS endpoint is verified active (§5.6).

### 1.5 Trust concentration: centralized key custody, accepted **conditionally** (decided)

**Decision (approved design direction):** v1 uses **centralized control-plane custody**
of TLS private keys. Accepted **conditionally** — the conditions are in §6.6, and
Phase 5.4 must not ship until they are met.

What this buys and what it costs, stated plainly:

- The control plane generates, stores and delivers every customer TLS private key, and
  can silently impersonate any domain at the CA. Phase 5 narrows the *blast radius of a
  database-only compromise* (§6) but does **not** remove this concentration.
- The **global KEK (`ENCRYPTION_KEY`) is a single point of total compromise**: it
  unwraps every organization's DEK, so its exposure (or an application-runtime
  compromise that can read it) means every certificate private key, every org DEK, and
  every existing Fernet ciphertext is compromised at once. Per-organization DEKs
  protect the *database-only* case and give per-org rotation/recovery; they do **not**
  bound a KEK or runtime compromise, and no document may claim they do (§6.1).
- Node-side keygen/CSR would remove the concentration structurally and is deliberately
  **out of scope for v1**; it remains the later-phase answer.
- Recorded in platform-security-model.md §5.3, which must be re-read before 5.4 ships.

---

## 2. Certificate lifecycle and state transitions

### 2.1 The six stages, kept distinct

These are six different facts. The platform must never collapse them, because the
control plane can only *know* three of them by itself; the last three exist only when
a node reports them.

| # | Stage | Who can assert it | Where it is recorded |
|---|---|---|---|
| 1 | **Issued** — the CA returned a chain for the identifiers | control plane (ACME) | `certificate_generations.state = ISSUED`, `issued_at`, `chain_ciphertext`/`key_ciphertext` written |
| 2 | **Delivered** — a node claimed the delivery operation and the material entered its TLS transport | control plane (claim CAS) | `certificate_deliveries.state = DELIVERED` on the claim transition |
| 3 | **Installed** — the node wrote the files and reported success | agent (asserted) | `certificate_deliveries.state = INSTALLED`, agent result |
| 4 | **Applied** — the node's nginx is running a configuration that references this material | agent (asserted, via `nginx.apply` result) | route `config_state = IN_SYNC` + `last_bundle_id`; node `proxy_state.live_bundle_id` |
| 5 | **Verified** — an independent HTTPS probe of the hostname from the control plane succeeded | control plane | `certificate_deliveries.state = VERIFIED_ACTIVE` + a stored probe result |
| 6 | **Active** — the route's `scheme` is `https` and the endpoint is verified | control plane | `routes.scheme = 'https'`, HTTPS uptime monitor green |

**Delivery ≠ installation, installation ≠ activation.** Stages 3–5 are agent/network
*facts about a running node*, not consequences of issuance. A certificate can be
`ISSUED` on the control plane while every serving node is offline, and the platform
must say exactly that.

### 2.2 Certificate generation state machine

A **certificate generation** is one ACME order + one key pair. Renewal creates a
*new generation*; it does not overwrite the old one in place (contrast the current
certificate-management.md §7 draft, corrected in §9 below). Keeping generations
separate is what makes "an older generation must not replace a newer one"
representable.

```mermaid
stateDiagram-v2
    [*] --> PENDING: generation created (certificate.manage)
    PENDING --> ORDERING: ACME order created
    ORDERING --> CHALLENGE_PUBLISHED: DNS-01 TXT published
    CHALLENGE_PUBLISHED --> VALIDATING: challenge accepted by CA
    VALIDATING --> ISSUED: finalize OK, chain+key stored, expires_at set
    VALIDATING --> FAILED: invalid / DNS / CA error
    ORDERING --> FAILED: order or auth error
    FAILED --> ORDERING: retry (bounded backoff)
    ISSUED --> SUPERSEDED: a newer generation became ISSUED
    ISSUED --> SUSPENDED: ownership lost for all its identifiers
    SUPERSEDED --> SUSPENDED: ownership lost for some identifiers
    ISSUED --> EXPIRED: notAfter passed (from CA material)
    SUSPENDED --> REVOCATION_PENDING: impact check passed (or split complete)
    ISSUED --> REVOCATION_PENDING: manual revoke (certificate.manage)
    REVOCATION_PENDING --> REVOKED: ACME revocation acknowledged
    REVOCATION_PENDING --> REVOCATION_FAILED: CA unreachable / rejected (retried)
    REVOCATION_FAILED --> REVOCATION_PENDING: bounded retry
    REVOCATION_FAILED --> REVOKED_LOCAL_ONLY: material removed, CA never answered
    FAILED --> [*]: deleted with its certificate once unreferenced (no key material)
```

Two independent axes, deliberately separate so the CA cannot gate the
security-relevant step:

- **`state`** — whether the generation is usable as material (`ISSUED`/`SUPERSEDED`/
  `EXPIRED`/`SUSPENDED`). `SUSPENDED` means “not authorized to serve its affected
  identifiers”, and is set the moment ownership is lost (§9.3).
- **`revocation_state`** — the asynchronous CA conversation (`NOT_REQUESTED` →
  `PENDING` → `REVOKED`, or `FAILED`/`REVOKED_LOCAL_ONLY`). Removal of the old
  configuration is **never** gated on this axis (§9.3 Stage 4).

`REVOKED` records the CA's acknowledgement. `REVOKED_LOCAL_ONLY` records that the
platform removed the material but the CA revocation did not succeed — the two are
distinct (see §9, “Removing ≠ revoking”), and the UI must show the local-only state
as a warning with a retry.

### 2.3 Delivery/activation state machine (per certificate × node)

```mermaid
stateDiagram-v2
    [*] --> NOT_NEEDED: node serves no route using this cert
    NOT_NEEDED --> PENDING: node gains a route using this cert
    PENDING --> DELIVERED: agent claimed the delivery op
    DELIVERED --> INSTALLED: agent reported files written
    DELIVERED --> FAILED: agent reported failure
    FAILED --> PENDING: bounded retry
    INSTALLED --> APPLIED: nginx.apply succeeded with the new paths
    APPLIED --> VERIFIED_ACTIVE: control-plane HTTPS probe OK
    APPLIED --> APPLY_FAILED: nginx.apply failed / rolled back
    APPLY_FAILED --> INSTALLED: re-apply (material still on disk)
    VERIFIED_ACTIVE --> PENDING: cert generation superseded (new material to deliver)
    VERIFIED_ACTIVE --> REMOVAL_PENDING: node no longer serves a route using this cert
    REMOVAL_PENDING --> REMOVED: agent applied a bundle that omits the cert paths
```

### 2.4 End-to-end sequence (control plane is the ACME client)

```mermaid
sequenceDiagram
    autonumber
    participant U as DevOps (certificate.manage)
    participant API as API
    participant W as Celery worker (ACME client)
    participant AC as ACME CA
    participant DNS as DNSProvider (Cloudflare)
    participant AG as Node agent
    participant NG as nginx on node

    U->>API: POST /certificates {domain_id, identifiers[], dns_provider_id?, auto_renew}
    API->>API: certificate row + generation PENDING, audit certificate.created
    API->>W: enqueue nx.issue_certificate (idempotent)
    W->>W: load org DEK (unwrap with KEK) + org ACME account
    W->>AC: newOrder(identifiers)
    AC-->>W: authorizations + dns-01 challenges
    W->>DNS: create_txt(_acme-challenge.<name>, digest)
    W->>DNS: propagation check until authoritative answer or deadline
    W->>AC: challenge ready (notify)
    W->>AC: poll authorization
    AC-->>W: valid
    W->>W: generate key pair + CSR (control-plane memory)
    W->>AC: finalize(CSR)
    AC-->>W: certificate chain
    W->>W: encrypt chain+key under org DEK; store generation ISSUED + fingerprint
    W->>W: audit certificate.issued; delivery fan-out (derived target set)
    Note over AG: delivery is PULL-based
    AG->>API: heartbeat → pending operation ids
    AG->>API: POST /agent/certificates/{id}/deliver (claim; mTLS-less but agent TLS + token)
    API-->>AG: {generation, chain, key, install_path, fingerprint} — assembled at read time, never stored
    AG->>AG: write key 0600, chain 0644 under content-addressed dir; report DELIVERED→INSTALLED
    API->>API: delivery INSTALLED; queue nginx.apply referencing the new paths
    AG->>NG: stage → nginx -t → atomic swap → reload (Phase 4 pipeline, reused)
    AG->>API: nginx.apply result (applied | rolled_back | rollback_failed)
    API->>API: route config_state; delivery APPLIED
    API->>API: control-plane HTTPS probe → VERIFIED_ACTIVE → route scheme=https
```

### 2.5 Failure at any stage

| Stage | Failure | Handling |
|---|---|---|
| Order / challenge | CA or DNS error | generation `FAILED`, sanitized `last_error`, bounded backoff; TXT cleanup best-effort; alert after budget |
| Issue | CA rejects finalize | same; a retry only after the challenge is re-established |
| Delivery | node offline / claim expired | the delivery op stays `PENDING` and re-queues while the node is offline; no partial install |
| Install | agent write fails | delivery `FAILED`; the previously-installed material is untouched (the install is staged + atomically swapped, §8) |
| Apply | `nginx -t` or reload fails | Phase 4 rollback path: previous known-good config restored, route `FAILED`, material stays on disk for retry |
| Verify | HTTPS probe fails after a successful apply | stage stays `APPLIED`, route HTTPS monitor pages, `config_state` may be `IN_SYNC` while the endpoint is unreachable — *applied ≠ verified*; the divergence is surfaced, never hidden |

---

## 3. Database entities, ownership, indexes, constraints, lifecycle fields

All Phase 5 tables are `OrgScoped` (session guard + RLS + `org_id`), following
`domains`/`routes`; all tables and columns below are **new** in Phase 5.

**Slice column.** Each table below has a **Slice** column naming the migration that
introduces that column, because the schema is delivered in two schema migrations, not
one: Phase 5.1 (certificate metadata and lifecycle foundations) and Phase 5.2 (key
envelope, DNS providers, ACME accounts, and the issuance/material columns). The
dependency order and the constraint that ties `state` to material are in §3.7. **There
is no placeholder provider and no placeholder DEK:** a column that references a table
or an envelope is introduced in the same slice that creates it.

### 3.1 `certificates` — the identity (one row per requested certificate)

| Column | Slice | Notes |
|---|---|---|
| `id`, `org_id`, `created_at`, `updated_at` | 5.1 | `OrgScoped` + `TimestampMixin` |
| `domain_id` | 5.1 | UUID FK → `domains.id`, NOT NULL; the verified name this certificate is for; `ON DELETE RESTRICT` while any generation is live |
| `primary_cn` | 5.1 | String(253); canonical (same form as `domains.name`) |
| `sans` | 5.1 | JSONB list; additional identifiers on the order (apex + wildcard share one generation) |
| `status` | 5.1 | String(**24**) + CHECK; certificate-level view: `PENDING`/`ISSUED`/`FAILED`/`EXPIRED`/`SUSPENDED`/`REVOCATION_PENDING`/`REVOKED`/`REVOKED_LOCAL_ONLY`. Widened from the design's original String(16) before 5.1 shipped, because `REVOCATION_PENDING` is 18 characters — the column the design specified could not have held its own vocabulary. **Derived** on read by the service: from the *current* generation once one is issued, otherwise from the newest generation (which is what Phase 5.1 can have); the *enforceable* material constraint lives on `certificate_generations` (§3.2/§3.7) |
| `current_generation_id` | 5.1 | UUID FK → `certificate_generations.id`, nullable; the generation a *new* bind should reference. NULL before the first `ISSUED`. |
| `challenge_type` | 5.1 | String(8) + CHECK; `dns-01` only in v1 (`http-01` is rejected at create for wildcards and not offered in the UI) |
| `auto_renew` | 5.1 | Boolean, default true; the renewal sweep skips `false` |
| `key_algorithm` | 5.1 | String(16); v1 fixed `ecdsa-p256` |
| `expires_at` | 5.1 | DateTime, nullable; denormalized from the current generation's `notAfter` for list/sort; unset until a generation is issued |
| `last_error` | 5.1 | String(500); sanitized reason of the current generation's last failure |
| `dns_provider_id` | **5.2** | UUID FK → `dns_providers.id`, nullable; overrides the Domain's provider. Added **with** `dns_providers` — no forward reference, no placeholder provider row |
| `suspended_at`, `suspension_reason` | **5.2** | DateTime / String(64); set on ownership loss (`domain_ownership_lost`) or an operator suspension; cleared when the certificate is rebound or revoked |

Indexes / constraints (**as built in 5.1**, migration `c8d9e0f1a2b3`):

- `uq_certificates_org_cn` UNIQUE `(org_id, primary_cn)` — one certificate row per
  name per org; renewal reuses it with a new generation.
- `ix_certificates_org_status` `(org_id, status)`.
- `ix_certificates_expiry_sweep` `(status, expires_at)` — the renewal sweep.
- `ck_certificates_status_valid`, `ck_certificates_challenge_type_valid`,
  `ck_certificates_key_algorithm_valid` — the closed vocabularies, by literal (a new
  value is a new migration).
- `ck_certificates_primary_cn_length` (`char_length(primary_cn) BETWEEN 4 AND 253`) and
  `ck_certificates_sans_shape` (`jsonb_typeof(sans) = 'array' AND
  jsonb_array_length(sans) <= 100`). The array constraint checks shape only; element
  canonicality (lowercase, punycode, no IP literal) is enforced on every write through
  `canonicalize_name` in `backend/app/core/dnsname.py`, because SQL cannot run IDNA —
  a constraint that pretended to would be worse than one that states its limit.
- The `OrgScoped`/`TimestampMixin` conventions add `ix_certificates_org_id` and
  `ix_certificates_created_at`; the same two exist on `certificate_generations`.
- A certificate row is **never hard-deleted while `routes.certificate_id` references
  it** (RESTRICT). Deletion is allowed only when orphaned *and* no generation is
  `ISSUED`: 5.1 implements the second half through `current_generation_id` (non-NULL ⇒
  material exists ⇒ 409 `CERTIFICATE_HAS_ISSUED_GENERATION`), and the first half
  arrives with its column in 5.5 — the FK there is RESTRICT, so the database refuses a
  delete a bound route makes invalid rather than the service guessing.

### 3.2 `certificate_generations` — one ACME order + one key pair

| Column | Slice | Notes |
|---|---|---|
| `id`, `org_id`, `created_at`, `updated_at` | 5.1 | |
| `certificate_id` | 5.1 | UUID FK → `certificates.id`, `ON DELETE CASCADE` |
| `generation` | 5.1 | Integer, `>= 1`; monotonic per certificate; the *generation number* is what delivery binds to |
| `state` | 5.1 → **widened 5.2** | String(24) + CHECK. **5.1** holds only the pre-issuance lifecycle: `PENDING`/`ORDERING`/`CHALLENGE_PUBLISHED`/`VALIDATING`/`FAILED` (so an issued generation is *unrepresentable* before the envelope exists). **5.2** widens it to the full vocabulary (§2.2) once material can be stored. |
| `order_state` | 5.1 | JSONB; ACME order/challenge URLs, key authorizations, DNS record names/values — **public ACME data only, never the account key** (no key material, so it may exist before the envelope) |
| `last_error`, `next_attempt_at`, `attempt_count` | 5.1 | Backoff cursors of the *generation* |
| `key_ciphertext` | **5.2** | Text; Fernet(org DEK) of the PKCS#8 private key |
| `chain_ciphertext` | **5.2** | Text; Fernet(org DEK) of the full chain |
| `fingerprint` | **5.2** | String(64); SHA-256 of the leaf DER (display + change detection, never a decryption oracle) |
| `not_before`, `not_after` | **5.2** | DateTime; from the issued material |
| `deke_id` | **5.2** | Integer, **nullable** (pre-issuance rows have none); which org-DEK generation encrypted the material, so a DEK rotation can find rows to re-wrap (§6.3). Made effectively mandatory for material-bearing states by the guard CHECK below. |
| `issued_at`, `revoked_at`, `revocation_state` | **5.2** | DateTime / String(24); `NOT_REQUESTED` / `PENDING` / `REVOKED` / `FAILED` / `REVOKED_LOCAL_ONLY` — the CA axis, separate from `state` (§2.2, §9.3). Unused until 5.6 |
| `suspended_at`, `suspension_reason` | **5.2** | DateTime / String(64); generation-level suspension (a shared generation may be suspended for *some* identifiers only) — §9.3. Unused until 5.6 |

Indexes / constraints:

- `uq_certificate_generations_cert_number` UNIQUE `(certificate_id, generation)` (5.1) —
  the backstop against a rewound/duplicated renewal.
- `ix_certificate_generations_sweep` `(state, next_attempt_at)` (5.1).
- **At most one pre-issuance generation per certificate** (5.1) —
  `CREATE UNIQUE INDEX uq_cert_generations_one_live ON certificate_generations
  (certificate_id) WHERE state IN ('PENDING','ORDERING','CHALLENGE_PUBLISHED','VALIDATING')`.
  A second concurrent issuance is therefore a database error, not two racing orders.
  As built, the predicate is generated from
  `CertificateGenerationState.live_pre_issuance()` in `backend/app/models/certificate.py`,
  so widening the live set cannot silently leave the index behind; `FAILED` is
  deliberately outside it, so a retry can insert its own row.
- `ck_certificate_generations_generation_positive` (`generation >= 1`) and
  `ck_certificate_generations_attempt_count_non_negative` (`attempt_count >= 0`) —
  the counters this table's cursors depend on cannot go negative (5.1).
- **Material guard CHECK (added in 5.2, with the columns and the envelope).** A
  generation in any post-issuance state must carry its material *and* the DEK generation
  that encrypted it:

  ```sql
  CHECK (state IN ('PENDING','ORDERING','CHALLENGE_PUBLISHED','VALIDATING','FAILED')
         OR (key_ciphertext IS NOT NULL AND chain_ciphertext IS NOT NULL
             AND deke_id IS NOT NULL AND issued_at IS NOT NULL
             AND not_before IS NOT NULL AND not_after IS NOT NULL))
  ```

  `SUPERSEDED`, `SUSPENDED`, `EXPIRED`, `REVOCATION_PENDING`, `REVOKED`,
  `REVOCATION_FAILED` and `REVOKED_LOCAL_ONLY` are all material-bearing, so none of them
  can exist without ciphertext and a DEK generation. This is the constraint the
  dependency-ordering in §3.7 relies on: it is introduced **exactly when** the
  envelope and the material columns are, not before (no placeholder `deke_id`).
- Existing `ISSUED` generations are **never updated in place**: renewal inserts a new
  generation and flips the old one to `SUPERSEDED` in one transaction. This is what
  makes "an older generation must not replace a newer one" a structural property
  (§8.5), not a comparison the code must remember to do.

### 3.3 `certificate_deliveries` — per certificate × node, material-free

**Slice: 5.4.** Depends on the `certificate_generations` material from 5.2; it adds no
material of its own.

| Column | Type | Notes |
|---|---|---|
| `id`, `org_id`, `servers_id` *(FK `servers.id`)*, `certificate_id`, `generation_id` | UUID FKs | The tuple binds delivery to a specific generation |
| `state` | String(24) + CHECK | §2.3 |
| `delivery_operation_id` | UUID FK → `operations.id`, nullable | The ordinary op that carries the *claim*; the material rides the claim **response**, not the row (§7) |
| `installed_fingerprint` | String(64), nullable | Fingerprint the agent reported installing |
| `applied_bundle_id` | String(64), nullable | Bundle the node applied that references this material |
| `verified_at`, `verify_error` | DateTime / String(500), nullable | Result of the control-plane HTTPS probe |
| `last_error`, `attempt_count` | — | Bounded retry |

Constraints:

- `uq_certificate_deliveries_generation_node` UNIQUE `(generation_id, servers_id)` —
  at most one delivery row per generation per node; the identity of a delivery is
  `(certificate, generation, node)`.
- Partial index `ix_cert_deliveries_pending` on `(state)` where state is non-terminal.
- The delivery row **never stores key or chain material** — only references. Enforced
  by the absence of any ciphertext column and by the data-path rules in §7.6.

### 3.4 `dns_providers` — customer DNS credentials (metadata-only reads)

**Slice: 5.2.** Created together with `certificates.dns_provider_id`'s FK (§3.7) — the
reference never precedes its target table.

A **dedicated table**, not a reuse of deployment-resolvable secrets and not a
notification channel (rationale in §5.3).

| Column | Type | Notes |
|---|---|---|
| `id`, `org_id`, `created_at`, `updated_at` | — | |
| `name` | String(120) | Operator label; `uq_dns_providers_org_name` `(org_id, name)` |
| `kind` | String(32) + CHECK | `cloudflare` (v1; the enum is the seam for Route53/DO later) |
| `credentials_ciphertext` | Text | Fernet(org DEK) of the provider credential blob (API token); **write-only via the API** |
| `credential_fingerprint` | String(64) | SHA-256 of a canonical serialization — display + change detection, not a decryption oracle |
| `scopes` | JSONB | Provider-declared scope summary, e.g. `{zone_id, zone_name, permissions: ["dns_records:edit"]}` |
| `zone_allowlist` | JSONB list | Zones this credential is permitted to touch; challenges for names outside it are refused pre-flight |
| `verified_at`, `verify_error` | — | Last `verify_creds()` result |
| `auto_cleanup` | Boolean, default true | Whether TXT cleanup runs after validation |
| `last_used_at` | DateTime, nullable | |

Reads are metadata-only: no endpoint returns `credentials_ciphertext`. The API
exposes `name`, `kind`, `scopes`, `zone_allowlist`, `verified_at`, `credential_fingerprint`.

### 3.5 Reused / changed existing entities

- **`routes`** gains `certificate_id` (UUID FK → `certificates.id`,
  `ON DELETE RESTRICT`, nullable) and a CHECK widened to
  `scheme IN ('http','https')` with the pairing rule:
  `(scheme='http' AND certificate_id IS NULL) OR (scheme='https' AND certificate_id IS NOT NULL)`.
  `scheme='https'` is **only** settable through the activation path in §5.6, never
  by a plain PATCH. **Slice: 5.5.**
- **`servers.proxy_state`** gains `tls` keys: the desired/confirmed certificate
  fingerprint set per node, written under the Phase 4.4 single-writer lock. No new
  column. **Slice: 5.5.**
- **`monitors.target_type`** gains `CERTIFICATE` (currently only `URL`/`ROUTE`), for
  the TLS-expiry monitor (§3.6). This is a CHECK-widening. **Slice: 5.6.**

### 3.6 Monitors

One `certificate`-target monitor per certificate row, auto-created at the first
`ISSUED` generation (opt-out honored). It evaluates `not_after - now()` against
warning/critical thresholds (default warn 30d, critical 7d) on the existing engine and
fails independently of the route's HTTPS uptime monitor. The route's HTTPS **uptime**
monitor (probe success/failure) is a separate monitor and a separate incident path:
"the certificate is expiring" and "the endpoint is not answering" must not be the same
alert.

### 3.7 Chosen migration sequence and dependency order (decided)

The dependencies are real: `certificates.dns_provider_id` references `dns_providers`,
and `certificate_generations`' encrypted material references the organization DEK
envelope. Both arrive in Phase 5.2. The chosen sequence is **two schema migrations**,
sized so each slice introduces a column in the same slice that creates what it
references — no forward reference, no placeholder DEK id, no artificial provider row.

| Migration | Creates | Alters | Why this boundary |
|---|---|---|---|
| **5.1** — certificate metadata & lifecycle foundations — **SHIPPED 2026-10-12 (`37b7211`, migration `c8d9e0f1a2b3`)** | `certificates` (identity + lifecycle metadata, **including `domain_id`, `status`, `current_generation_id`, `challenge_type`, `auto_renew`, `key_algorithm`, `expires_at`**), `certificate_generations` (pre-issuance states + cursors), RLS policies + grants, the two codenames and their role grants | — | 5.1 performs **no issuance**, so it needs no providers, no ACME account and no key material. The generation `state` CHECK is deliberately limited to pre-issuance states, so a material-less `ISSUED` generation is unrepresentable rather than merely discouraged. |
| **5.2** — key envelope, providers, ACME accounts, material | `dns_providers`, `acme_accounts`; `organizations.dek_ciphertext` / `organizations.dek_generation` | `certificates`: `+dns_provider_id` (FK → `dns_providers`), `+suspended_at`, `+suspension_reason`. `certificate_generations`: `+key_ciphertext`, `+chain_ciphertext`, `+fingerprint`, `+not_before`, `+not_after`, `+deke_id`, `+issued_at`, `+revoked_at`, `+revocation_state`, `+suspended_at`, `+suspension_reason`; **widen `state`** to the full vocabulary; **add the material guard CHECK** | The FK target, the envelope and the material columns land together, so the reference is always satisfiable and the guard CHECK can be written once. |
| 5.4 / 5.5 / 5.6 | `certificate_deliveries` (5.4); `routes.certificate_id` + widened `scheme` (5.5); `monitors.target_type` + `CERTIFICATE` (5.6) | as scoped in §10.1 | Each consumes the 5.1/5.2 foundations; none introduces an earlier dependency. |

**Where the 5.2 row's envelope actually landed (2026-10-14):** the row above names
`organizations.dek_ciphertext` / `organizations.dek_generation`, which is the plan as it
stood — 5.2.1 shipped exactly those two columns, and 5.2.1.2 then moved them to the tenant
table `organization_dek_envelopes` because `organizations` is RLS-exempt (§10.6, audit
finding F1). The boundary the table argues for is unchanged; only the table the envelope
lives in moved, and the row is kept as the plan it was rather than silently rewritten.

**The rule the sequence encodes:** a nullable column introduced early is acceptable
only when a constraint makes its absence invalid in every state that requires it. Here
`deke_id` is nullable (pre-issuance rows legitimately have no DEK), but the 5.2 guard
CHECK makes it and the ciphertext **mandatory for every material-bearing state** — so
there is no window in which an issued generation can lack its key material or its DEK
generation. `dns_provider_id` is nullable by design (a certificate may inherit the
Domain's provider), and its FK is created with its target table.

**No placeholder identifiers.** `deke_id` is never seeded with a dummy generation, and
no provider row is invented to satisfy the FK; if issuance is attempted before 5.2,
the generation `state` CHECK rejects it because `ISSUED` is not in the 5.1 vocabulary.

**Intra-5.2 order (added 2026-10-12, after 5.1 shipped).** One migration is correct,
but the *work inside it* has an order, and the first step is external:

| # | Step | Depends on |
|---|---|---|
| 1 | **KEK provider adapter** behind the seam in §6.7 (`wrap_dek`/`unwrap_dek`/`rewrap_dek`), first implementation **Vault Transit** (approved; §10.5 is its plan) | Nothing — the decision is in. **Blocks steps 2–6**: without it there is no key the org DEK may be wrapped under, and an env-var fallback is exactly the unsafe source §6.7 forbids |
| 2 | The organization DEK envelope — `organization_dek_envelopes.dek_ciphertext` / `dek_generation` (planned on `organizations`; moved in 5.2.1.2, §10.6) + org-DEK creation and **operation-scoped unwrap** (no long-lived plaintext-DEK cache) — the **only** place a DEK is wrapped or unwrapped | Step 1 |
| 3 | `dns_providers` table + its metadata-only API, then credential *acceptance* (`credentials_ciphertext`, `credential_fingerprint`) | Step 2 — the credential blob is wrapped under the org DEK, so accepting one without the envelope would be a partially working store |
| 4 | `acme_accounts` + per-org account-key protection | Step 2 (same envelope); independent of step 3 |
| 5 | `certificates.dns_provider_id` FK (lands **with** its target table), generation material columns, widened `state`, the material guard CHECK, `deke_id` | Steps 2–4 |
| 6 | *Issuance itself* (5.3): the maintained ACME client, the order/challenge flow, `verify_creds`/`zone_allowlist` enforcement | Steps 1–5 |

**What cannot be implemented safely before the KMS choice is approved:** steps 1–6 as
listed — that is the org-DEK envelope, everything wrapped under it (DNS credentials,
ACME account keys, certificate key/chain), and therefore any issuance, delivery or
verification path. What *can* proceed without it: the non-credential half of step 3
(the `dns_providers` row, its metadata read model, and zone-allowlist validation as a
pure function) and the widened `state` vocabulary *if* it ships with the material
columns — no placeholder keys, no placeholder provider rows, no credential storage
without an envelope, no partially working issuance path (§3.7's no-placeholder rule
applies to the whole slice, not just 5.1).

---

## 4. Authorization and tenant isolation

### 4.1 CodenamesPhase 5 adds the two codenames already listed in authorization.md §2 — they are **not**
registered today (`backend/app/core/permissions.py`):

- `certificate.read` — metadata, fingerprints, delivery state, monitor state.
- `certificate.manage` — create/renew/revoke/delete; bind a certificate to a route;
  manage `dns_providers` (create/rotate/delete/verify).

**Role matrix (O3, decided — resolved 2026-10-12).** The target matrix in
authorization.md §3 is adopted, with the **current stored role names** — the
`Operator` → `DevOps` rename is *not* implemented in Phase 5 and must not be implied:

| Stored role (today) | `certificate.read` | `certificate.manage` | Note |
|---|---|---|---|
| Owner | ✓ (via `*`) | ✓ (via `*`) | wildcard, unchanged |
| Admin | ✓ | ✓ | matches every other registry group |
| **Operator** (future `DevOps`) | ✓ | ✓ | both; the rename is a separate change |
| Developer | ✓ | — | read-only |
| Viewer | ✓ | — | read-only |

`certificate.manage` is **not** granted to Developer or Viewer; `certificate.read` is
not action-bearing. Both codenames are **organization-scoped** (resolved from the
active membership, like every Phase 1 codename) and reads stay **metadata-only**:
`certificate.read` must never expose a private key, plaintext certificate material, or
ciphertext — `certificate.manage` likewise never returns key material through any
endpoint (management is create/renew/revoke/bind, not read).

`dns_providers` deliberately has **no separate codename in v1**: managing a DNS
credential is part of `certificate.manage`, because the credential exists only to
serve issuance. (If DNS credentials later power TXT auto-publish for domain
verification, that is the point to split out `dns.manage` — recorded in §10.)

The Phase 5 operation types reuse these codenames — no `node.execute`, no
`certificate.execute`.

### 4.2 Per-type permission and capability gating

Following the shipped registry pattern (`OPERATION_SPECS`): each new op type names a
permission codename and a capability, validated at registry load.

| Phase 5 op type | Permission | Capability | Notes |
|---|---|---|---|
| `certificate.install` | `certificate.manage` | `nginx` | Params are reference-only; material is in the claim **response** (§7) |
| `certificate.remove` | `certificate.manage` | `nginx` | Params reference-only |
| `nginx.apply` (existing) | `domain.manage` | `nginx` | Reused unchanged to render the TLS server block |

A new capability key `tls` is **not** introduced: TLS is a property of the nginx
instance the Phase 4 pre-flight already validates. The pre-flight's port-443 rule
(`MANAGED` or `FREE`) already gates eligibility (domain-routing.md §5), so a node that
cannot own 443 is refused before any certificate work.

### 4.3 Tenant isolation

- Every Phase 5 table is `OrgScoped`; reads/writes are session-guarded and
  RLS-backed. A foreign id is a 404 with the same envelope as a random uuid.
- The ACME account is per-organization (§5.4): an org's rate-limit budget and
  revocation ownership are its own.
- The delivery endpoint resolves the node from `X-Agent-Token` (existing
  `require_server`) and acts inside that node's org scope; the CAS additionally
  requires `node_id == this node`, so a token cannot retrieve another node's material
  even in the same org.
- The IDOR suite (platform-security-model.md §8) gains cases for
  `/certificates`, `/certificates/{id}`, `/dns-providers`, the delivery
  endpoint (foreign node) and the certificate-target monitor.

### 4.4 Route → certificate binding at write time

`POST /routes/{id}/certificate` (and the request-body field on create) validates:

1. the certificate is in the caller's org and its current generation is `ISSUED`;
2. the certificate **covers** the route hostname — exact CN/SAN, or a wildcard SAN
   **one label deep** (`*.example.com` covers `api.example.com`, not
   `a.b.example.com`), matching domain-routing.md §10's route-coverage depth rule so
   hostname and cert coverage cannot diverge;
3. the route's domain is `VERIFIED` **now**;
4. the node passes the Phase 4 routing pre-flight.

A mismatch is a 422 naming the field. The covering check is owned by the certificate
service (domain-routing.md §8.2); the error shape is `CERTIFICATE_DOES_NOT_COVER_HOSTNAME`
with the hostname and the available identifiers.

---

## 5. ACME issuance and DNS-01 handling

### 5.1 Decision: maintained ACME client library (josepy/`acme`), not a hand-rolled RFC 8555 client

**Recommended:** depend on the maintained ACME client library (`acme`, the library
behind Certbot, with `josepy`), pinned, wrapped behind an internal `AcmeProvider`
seam. A minimal in-repo RFC 8555 implementation is **rejected**.

| Criterion | Maintained library (`acme` + `josepy`) | Minimal in-repo RFC 8555 |
|---|---|---|
| Correctness of JWS/ES256 + key rollover | Battle-tested, used by Certbot at scale | Every JWS detail (protected header ordering, nonce handling, `kid` vs `jwk`, badNonce retry) must be re-derived |
| Maintenance / security history | Actively maintained; security fixes flow to a pinned version | The platform owns CFRG/JWS drift and any future RFC errata |
| Async HTTP fit | Pure-Python, synchronous `requests`-based client; wrap calls in `asyncio.to_thread` inside Celery tasks (the API never issues inline) | Same async wrapping problem, plus hand-written HTTP |
| Dependency weight | New deps: `acme`, `josepy`, `cryptography` (already a transitive dep for Fernet), `requests` (likely already present) | Only `cryptography`, but re-implements protocol |
| Challenge support | `dns-01` (and `http-01` for the later fallback) supported today | Must implement `dns-01` key authorization + base64url digest by hand |
| Staging / pebble testing | `directory_url` is a parameter; `pebble` is the standard test CA and the library already speaks to it | Would need its own staging harness |
| Operational complexity | Version pin + upgrade cadence | Protocol drift owned forever; "fewer lines today, more bugs tomorrow" |
| Licensing | Apache-2.0 / Apache-2.0 (compatible with the project) | n/a |

The choice is not made to minimize line count; it is made because a hand-rolled ACS
client re-derives security-critical JWS/nonce logic that the ecosystem has already
hardened. The `AcmeProvider` seam keeps the library swappable and keeps the tests
pointed at `pebble` / the CA's staging directory.

Open sub-decision for the slice: exact pin and whether to use `acme`'s
`ClientNetwork` directly or its higher-level `messages` helpers — resolved at
implementation, not load-bearing for this design.

### 5.2 Challenge: DNS-01 only in v1

DNS-01 is the only challenge type. Rationale (unchanged from certificate-management.md
§4.1): it is the only one that works for NAT-ed home servers, Raspberry Pis and
wildcards, and it needs no inbound connectivity to the node at issuance. `http-01` is
designed as a later fallback (§5.7) and is not offered in the v1 UI.

### 5.3 DNS provider abstraction and the DNS-01 flow

**A dedicated `dns_providers` table is required** (decided here). Reuse rejected:

| Candidate reuse | Why rejected |
|---|---|
| Deployment-resolvable secrets (`${secret:KEY}`) | Those values are *delivered to nodes* at deploy time (secrets-architecture.md §7). A customer's DNS API token must **never** reach a node — putting it in the secret store conflates "may be delivered to a node" with "control-plane-only CA/DNS credential". |
| Notification-channel config | A channel's config is a webhook URL/headers, validated at create/update and used by the alert pipeline. It has no zone scope, no `verify_creds`, no allowlist semantics, and reusing it would couple alerts to issuance. |
| A generic `integrations` table (the earlier draft's "Connection") | That table does not exist in the shipped tree; introducing a generic integration entity for exactly one consumer adds an abstraction without a second user. A purpose-built `dns_providers` table is smaller and can be generalized later if a real second consumer appears. |

**Provider interface** (one implementation in v1 — Cloudflare):

| Method | Purpose | Notes |
|---|---|---|
| `verify_creds()` | Health/scope check on save and before use | Result stored as `verified_at`/`verify_error`; UI surfaces a broken credential rather than failing at request time |
| `create_txt(zone, name, value, ttl)` | Publish `_acme-challenge.<name>` | Returns the provider record id for deterministic cleanup |
| `delete_txt(zone, name, value)` | Remove the TXT record | Best-effort; cleanup state tracked so a stuck record is visible |
| `propagation_check(name, value, deadline)` | Query the zone's **authoritative** nameservers until the value is observed or the deadline passes | Reuses the control-plane DNS resolver decided for verification (domain-routing.md Open Q1); a hard deadline so a slow provider cannot hang the task |

**Credential scope, zone restrictions, validation, cleanup:**

- The Cloudflare credential is a **zone-scoped API token** (`Zone:DNS:Edit` on the
  specific zone), never a global key. The UI's setup instructions say so
  (certificate-management.md §1's "surfaced in the add-domain flow" requirement).
- `zone_allowlist` is enforced **before** any provider call: a challenge name outside
  the allowed zones is refused with a named error, so a compromised/wrong credential
  cannot be used to write records in a zone the customer did not authorize.
- `create_txt` records a `dns_record_ref` in `order_state`; cleanup deletes by that
  reference, not by re-deriving the name — a delete that names the wrong record is
  itself a way to destroy a customer's DNS.
- Credentials are Fernet(org DEK) at rest, metadata-only via the API, and **never**
  logged (they are key-named `token`/`api_key`, which the Phase 4.4 recursive redaction
  already scrubs — defense in depth, not the control).

### 5.4 ACME account

One ACME account per **organization per directory** (staging vs production are
separate accounts). The account key pair is generated control-plane-side and stored
Fernet(org DEK) in a dedicated `acme_accounts` row (org-scoped, `directory_url`,
`account_url`, `key_ciphertext`). Rationale: rate-limit blast radius and revocation
ownership are scoped to the tenant; a shared platform account would let one tenant's
issuance exhaust another's budget.

**Directory selection (decided).** The directory URL is explicit configuration, not an
inferred default:

| Context | Directory | Rule |
|---|---|---|
| Development, tests, CI, pebble | **staging** | Default. Tests must never contact the production CA. |
| Non-production deployment | **staging** | Default; matches the certificate-is-staging expectation. |
| Production deployment | **production** | Requires **explicit** production configuration (e.g. `ACME_DIRECTORY=production`); it is never inferred from `ENVIRONMENT` alone. |

**No silent fallback.** A production-configured issuance never falls back to the
staging directory, and a staging-issued certificate is never presented as a
production certificate. The generation records which directory issued it
(`directory_url`), the API exposes it, and the UI labels a staging certificate as
staging. If production configuration is missing, production issuance **fails closed**
with a named error rather than quietly minting a staging cert that browsers distrust.
Conversely, a non-production deployment must not be able to request a production
certificate by accident: production issuance requires the explicit flag, so the
default is the safe one.

The environment still defaults the *display* expectation (a dev deployment shows
staging), but the switch is configuration, not environment sniffing.

### 5.5 Issuance task and idempotency

`nx.issue_certificate(generation_id)` is one Celery task per attempt, idempotent on
the generation row: it reads `state` + `next_attempt_at`, refuses to run against a
terminal generation, and drives the state machine. Secrets are never in the task
payload — only ids. The task runs inside `org_scope(org_id)` per the task base
(multi-tenancy.md §4).

- **Attempt budget:** 5 attempts per generation, exponential backoff
  (`2^n × 5 min`, cap 24h). Exhaustion → generation `FAILED`, alert + incident via the
  existing pipeline.
- **Stuck-state sweep:** a generation in `ORDERING`/`CHALLENGE_PUBLISHED`/`VALIDATING`
  older than the order TTL (~1h) with no heartbeat is marked `FAILED` with a reason,
  best-effort TXT cleanup runs, and normal backoff resumes.
- **Rate limits:** honor `Retry-After` exactly; staging directory for all
  pre-production use keeps the production budget clean.

### 5.6 HTTPS activation (the "HTTP keeps serving" rule)

Activation is a deliberate, verified step, not a side effect of issuance:

1. Material is delivered and installed on every serving node (§7, §8).
2. The control plane renders a **TLS server block** for the route in addition to the
   existing HTTP block — both listen, on 80 and 443. HTTP is **not** removed at this
   step.
3. The node applies the bundle with the Phase 4 stage → `nginx -t` → swap → reload →
   rollback pipeline. The TLS block is part of the validated tree, so a bad
   certificate path or a broken `ssl_*` directive fails validation and the previous
   (HTTP-only) configuration stays live.
4. The control plane runs an **independent HTTPS probe** of the hostname: TLS
   handshake against the node, verify the presented leaf fingerprint equals the
   generation's `fingerprint`, and a request that reaches the upstream. Only a
   successful probe moves the delivery to `VERIFIED_ACTIVE`.
5. Only then does the route flip to `scheme='https'` and (optionally) a host→HTTPS
   redirect become allowed. **Removing HTTP or adding a redirect is the last step**,
   after verification, so a failure at any earlier step never takes the working HTTP
   service down.
6. If step 4 fails: `config_state` may be `IN_SYNC` (the node applied what was asked)
   while the endpoint is unreachable — the divergence is surfaced as
   `APPLIED ≠ VERIFIED_ACTIVE`, the HTTPS monitor pages, and HTTP keeps serving.

### 5.7 HTTP-01 (later fallback, design only)

For orgs unwilling to hand over DNS credentials, a later slice may render a temporary
`/.well-known/acme-challenge/` location into the node's config through the existing
ProxyProvider path, have the node answer the probe, and proceed identically from
finalization onward. DNS-01 remains the default; the template owner for the
challenge fragment is recorded in domain-routing.md Open Q6.

---

## 6. Private-key encryption and key management

### 6.1 Threat model — what each envelope actually protects against

The decision below is only meaningful if the limits are stated first. The proposed
per-organization DEK is evaluated against each threat:

| Threat | What a per-org DEK changes | What it does **not** change |
|---|---|---|
| **Database-only compromise** (attacker reads the DB, not the process/env) | Nothing is readable: `key_ciphertext`/`chain_ciphertext` are ciphertext under DEKs that are themselves wrapped under the KEK. Same as today's single-key posture. | — |
| **Exposure of one organization's DEK** (a leaked unwrapped DEK, or an operator error) | Limits the attacker to *that org's* certificate keys, secrets written under the same envelope, and DNS credentials. Cross-org compromise is **not** implied. | If the leaked value is actually the *KEK*, see the next row. |
| **Compromise of the global KEK or `ENCRYPTION_KEY`** | **No cross-org protection.** The KEK unwraps every org's DEK, so a KEK compromise is a total compromise of all certificate private keys (and every Fernet ciphertext). The per-org envelope does **not** reduce this — it concentrates less material under one *data* key but the root still unlocks all of it. | Any claim that per-org envelopes bound a KEK/root compromise is false and must not be documented. |
| **Application-runtime compromise** (RCE in the API/worker) | **No protection.** The process holds the KEK and unwraps DEKs on demand; whoever can run code in the process can decrypt every certificate key it can reach, and can request any node to accept material. The org boundary is not an execution boundary. | This is the accepted concentration (§1.5). Node-side keygen is the only structural answer and is out of scope. |
| **Backup loss / DR** | Wrapped DEKs live in DB backups; the KEK must be in break-glass storage *separately* from those backups or a stolen backup is a decryption kit. Restoring the DB without the KEK permanently strands every certificate key. | — |

**Honest summary:** the per-org DEK is worth building because it gives (a)
defense-in-depth for the DB-only case, (b) per-org rotation and per-org recovery, and
(c) a clean seam to a KMS. It does **not** prevent cross-organization compromise when
the KEK or the application runtime is compromised, and no document may claim it does.

### 6.2 Recommended v1 design

```mermaid
flowchart LR
    KEK["ENCRYPTION_KEY (KEK, env)<br/>wraps DEKs only"] -->|wrap/unwrap| D1["Org A DEK (wrapped,<br/>organization_dek_envelopes)"]
    KEK --> D2["Org B DEK (wrapped)"]
    D1 -->|"Fernet"| C1["Org A: certificate key/chain,<br/>dns_providers creds, acme account key"]
    D2 --> C2["Org B: certificate key/chain,<br/>dns_providers creds, acme account key"]
```

- **KEK source:** `ENCRYPTION_KEY` remains the root for v1, unchanged. It is already
  required, Fernet-validity checked and fail-fast at import
  (`backend/app/core/config.py`). v1 does not move it to a KMS — but the preferred
  production source is an external **KMS / secret manager**, and the `unwrap` call is
  the single seam that swap replaces (§6.6).
- **DEK:** one Fernet key per organization, generated lazily at the first Phase-5 write
  and stored **wrapped** in that organization's own row of
  `organization_dek_envelopes` (`dek_ciphertext`, with a `dek_generation` integer). The
  design originally put these two columns on `organizations` itself; 5.2.1.2 moved them
  into a tenant table, because `organizations` is RLS-exempt and the envelope therefore
  sat outside every database-level tenant net (§10.6). A plaintext DEK exists only for the operation that
  unwrapped it and is dropped when that operation ends: **operation-scoped unwrap, no
  long-lived plaintext-DEK cache** (§6.7 approved point 5, §6.9). This is deliberately
  *not* the module-global `_fernet_cache` pattern the secret store uses, and it applies
  to certificate/DNS material only — the existing store keeps its current key path
  (§6.4).
- **Scope of the envelope in v1:** certificate `key_ciphertext`/`chain_ciphertext`,
  `dns_providers.credentials_ciphertext`, and `acme_accounts.key_ciphertext`. Existing
  `secrets`, `secret_versions`, `server_credentials` and channel configs keep the
  single-key path (§6.4).
- **`deke_id`** on each ciphertext row records which DEK generation encrypted it, so a
  future rotation can find exactly the rows to re-wrap.
- **Access boundary:** unwrap happens only in the worker/API path that needs the
  material. There is no endpoint that unwraps for a human; the DNS credential is
  write-only and the certificate key never leaves the delivery path (§7).

### 6.3 Rotation

| Rotation | Procedure | Cost |
|---|---|---|
| Org DEK | Generate a new DEK, wrap under the KEK, bump the organization's `dek_generation`, then background re-encrypt rows whose `deke_id` is older — per-org batches, resumable, using an explicit `state=ROTATING` marker so a half-rotated org is visible. Old DEK kept until the last row is migrated, then cleared. | Re-encrypts that org's cert/DNS material |
| KEK (`ENCRYPTION_KEY`) | Rotate by re-wrapping every org DEK only — **touches no ciphertext rows**, fast, and the reason the envelope exists. Today's single-key design cannot do this (S5). | Re-wrap ~1 row per org |
| Certificate key (per cert) | Generate a new generation (renewal); the old generation is `SUPERSEDED`. Keys are per-certificate, so this is the normal renewal path. | One ACME order |
| ACME account key | Generate a new account key, re-register, and roll the old key out per RFC 8555 key-rollover; the old key stays until rollover completes. | One CA round-trip |

`ENCRYPTION_KEY` is currently **write-once** in practice; this design makes the KEK
rotation a *supported* operation for the Phase-5 scope, without claiming the secret
store can be rotated (it still cannot — that is §6.4).

### 6.4 No secret-store migration (explicit scope boundary)

Migrating `secrets`, `secret_versions`, `server_credentials` and
`notification_channels.config_ciphertext` to the org-DEK envelope is **not** part of
Phase 5. It would re-encrypt every existing secret, need its own rollback plan, and
is not required for HTTPS. It is recorded as a **separate reviewed change** in §10.
The two envelopes coexist by construction: `deke_id` is set only on Phase-5 rows, and
the existing `_fernet()` path is untouched.

### 6.5 Backups, recovery, and consequences of key loss

| Asset | Backup requirement | Loss consequence |
|---|---|---|
| `ENCRYPTION_KEY` (KEK) | Break-glass storage **separate** from DB backups; two-person access | Total loss of all Phase-5 material and all existing Fernet ciphertext — unrecoverable |
| Wrapped org DEKs | They live in the DB backup | Loss of one org's wrapped DEK ⇒ that org only; recover by re-issuing its certificates (material is reproducible from the CA, unlike user secrets) |
| Certificate material | Not separately backed up — reproducible by re-issuance | A certificate key is **reproducible**: worst case is a new generation and a re-delivery. This is why certs can take a stronger envelope without a recovery ceremony. |
| Customer DNS tokens | Not separately backed up; re-enterable | A lost DNS token is re-entered by the operator; existing certificates keep working |

Emergency recovery: restore the KEK, restore the DB, unwrap DEKs, then re-issue any
generation whose material is unreadable. A generation that cannot be decrypted is
marked `FAILED` with a reason and re-issued — never served with a broken payload
(delivery fails closed on `decrypt_str` mismatch, matching today's behavior).

### 6.6 Production-readiness requirements for centralized custody (conditions of §1.5)

Centralized custody is approved **conditionally**. These are the conditions; Phase 5.4
must not ship to production until they are met and evidenced in the deployment
runbook.

| # | Requirement | Why / mechanism |
|---|---|---|
| C1 | **Preferred external KMS / secret manager for the KEK** | The KEK (and ideally the unwrap operation) should live in an external KMS or secret manager (e.g. a cloud KMS/HSM-backed key, or Vault) so the root never sits in a plaintext env var or the application filesystem. The decision is **made**: §6.7 selects Vault Transit by default and the deployment cloud's managed KMS as the first-class alternative, behind one provider interface; §6.8 lists the vendor approval still outstanding. Until an adapter exists, `ENCRYPTION_KEY` from env remains the only source *and its blast radius is total* (§6.1). |
| C2 | **Access restrictions** | The KEK/DEK material and the unwrap path are reachable only from the API/worker runtime, never from the SPA, the agent, or a public endpoint. Unwrap happens only in the control-plane code path that needs the material (§6.2 “access boundary”). No human-facing endpoint decrypts. Host access to the env/file holding `ENCRYPTION_KEY` is restricted to the control-plane service account; containers run non-root (platform-security-model.md §7). |
| C3 | **Rotation is exercised, not just designed** | The KEK re-wrap (§6.3) and the org-DEK rotation must be **tested in a non-production environment** before production. “Write-once with no path” (S5) is the status quo this design replaces for the Phase-5 scope; a rotation that has never been run is not a rotation. |
| C4 | **Backup / recovery is rehearsed** | The KEK is in break-glass storage **separate** from DB backups with two-person access (§6.5), and an emergency recovery drill has been run: restore KEK + DB, unwrap DEKs, re-issue any unreadable generation. |
| C5 | **Detection and revocation are operable** | An operator has a documented path to (a) re-issue/suspend/revoke any certificate after a suspected key compromise and (b) rotate the KEK and every org DEK; the incident-response section (§9, platform-security-model.md §10) names the actions. |
| C6 | **No claim of protection that does not exist** | Documentation and the UI must state that per-org DEKs do **not** bound a KEK or application-runtime compromise. This row exists because the failure mode of overstating this is a false sense of tenant isolation. |

Until C1–C6 are met, centralized custody is an **accepted risk for non-production**
and a **blocker for production**.

### 6.7 KEK provider decision — **approved 2026-10-12**

**Status: approved.** The direction below was approved explicitly before any provider
adapter or envelope code is written. This document still adds no dependency, no adapter,
no credential and no configuration key: approval settles *what* to build, not that this
change built it.

The approved decision, in the words it was approved in:

1. **Vault Transit is the first production `KEKProvider` implementation** for
   self-hosted deployments.
2. **Managed cloud KMS providers remain possible future adapters behind the same
   interface.** They are **not** implemented in v1 without a concrete deployment
   requirement — the seam exists so that decision stays cheap, not so that every vendor
   is built speculatively.
3. **Test and development providers are explicitly selected and cannot serve as
   production fallbacks.**
4. **The root KEK never enters NexusOps application code or the database in plaintext.**
5. **DEK unwrapping is operation-scoped initially; no long-lived plaintext-DEK LRU cache
   until measurements justify one.**
6. **Rewrapping is delegated to the provider where supported, with no plaintext DEK
   returned to the application during KEK-only rotation.**

It exists because the production unwrap path (Phase 5.2.1, §10.5) must not be written
before the key it unwraps under is chosen; until then the org-DEK envelope would
inevitably be built against a plaintext env key that §6.1 calls a total-compromise
source.

**What a KEK provider must do.** Hold one root key the application can never read;
wrap and unwrap a 32-byte organization DEK on demand; let the wrapped value live in the
database while the plaintext DEK lives only in process memory; rotate the root key
without touching a single ciphertext row (§6.3); be reachable only from the API/worker
runtime (C2); and fail closed when it is unreachable — never decrypt from a weaker
source to keep serving.

**Options.** (List prices are anchors, not quotes; re-check before contracting.)

| Option | Where the root key lives | Rotation | Access control | Recovery / availability | Operational cost | Notes |
|---|---|---|---|---|---|---|
| **Managed cloud KMS** (AWS KMS / GCP KMS / Azure Key Vault) | Vendor HSM-backed key that never leaves the boundary | Versioned key versions; re-wrap DEKs in place | IAM on the key plus a per-call audit log | Managed SLA; unavailability means no unwrap | ~$1 per key-month and ~$0.03 per 10k key-use operations at AWS/GCP list prices — negligible at one wrap/unwrap per org-DEK lifecycle | The right answer *when* the control plane already lives in that cloud; otherwise it pins the deployment to one vendor |
| **HashiCorp Vault Transit** (self-hosted or HCP) | Inside Vault's barrier; never returned | `transit/keys/<k>/rotate` plus `rewrap` of stored ciphertexts — built for exactly this envelope | Vault policies + an AppRole token scoped to one transit key, with an audit device | Auto-unseal (cloud KMS/HSM) or Shamir shares in break-glass custody; Vault down means no unwrap | One more stateful service **and its unseal custody**; OSS free, enterprise optional | Cloud-agnostic, and it fits the shipped docker-compose deployment model and on-prem/VPS installs |
| **KEK in the environment** (`ENCRYPTION_KEY` today) | Plaintext in the process env / compose file | Not possible without re-encrypting every ciphertext | Anyone who can read the env or `exec` into the container | Trivial | None | **Status quo — not acceptable for production custody (C1)**; this is the source §6.1 measures as total blast radius |
| **Sealed file (SOPS/age) on the host** | A file the service account can read | Rotate the file, then re-wrap DEKs | Filesystem permissions; no per-call audit, no independent boundary | File must be kept separate from DB backups | Low | Fine for **dev/test** and single-operator installs; not custody for a multi-tenant production platform |
| **HSM / PKCS#11 appliance** | A hardware appliance | Vendor-specific | PKCS#11 + appliance ACLs | Appliance availability plus key escrow | High (hardware, skills, cost) | Only worth it for a compliance requirement that names it; cloud KMS and Vault already give HSM-backed keys |

**The approved approach.** **One external KEK provider behind the interface below, whose
first production implementation is HashiCorp Vault Transit** — the deployment that
matters is the self-hosted docker-compose install the platform ships and supports, so the
choice must not require a specific cloud. Vault Transit provides the wrap/unwrap and
rotation semantics this envelope needs, a per-call audit trail, and token-scoped access
narrowed to the one transit key, and its cost is one more service in a stack that already
runs several. **Managed cloud KMS adapters (AWS KMS / GCP KMS / Azure Key Vault) are
follow-ups behind the same seam**, built when a deployment actually requires one — the
interface is what keeps that cheap, not a speculative multi-cloud adapter matrix.

**The honest costs of that decision.**

- Vault does not remove the root-of-trust problem, it **relocates** it: the unseal
  material becomes the top secret. The approved arrangement is **auto-unseal through a
  cloud KMS** (§6.9), which is the lowest-friction operation and makes that cloud KMS a
  documented availability dependency for Vault start-up (C4, §6.5).
- Every unwrap is a network call. The approved policy is **operation-scoped unwrap with
  no long-lived plaintext-DEK cache** (§6.9): a request that needs a DEK unwraps it,
  uses it, and drops it. If measurements show that cost matters, a short-lived cache is a
  *measured* follow-up, not a default — and it would still never cache the KEK.
- Provider unavailability **fails closed**: no issuance, no delivery, no DNS-credential
  read. That is the correct direction, and it must surface as a named operator-visible
  error rather than a retry storm.

**Provider interface (normative — one seam).** The envelope talks to exactly this, and
no other module may touch the KEK:

```python
class KEKProvider(Protocol):
    name: str  # "vault-transit" | "aws-kms" | "gcp-kms" | "azure-kv" | "test"

    async def wrap_dek(self, dek: bytes, ctx: EncryptionContext) -> WrappedKey: ...
    async def unwrap_dek(self, wrapped: WrappedKey, ctx: EncryptionContext) -> bytes: ...
    async def rewrap_dek(self, wrapped: WrappedKey, ctx: EncryptionContext) -> WrappedKey: ...
    async def health(self) -> KEKProviderStatus: ...
```

with two value objects it exchanges:

- `EncryptionContext(org_id, purpose, dek_generation)` — **cryptographically bound into
the ciphertext**, not stored beside it, so a wrapped DEK cannot be replayed under a
  different organization, purpose or generation. For Vault that binding is the
  **derivation context** of a `derived=true` transit key (§6.7 amendment below) — *not*
  `associated_data`. A provider without an equivalent context parameter implements the
  binding provider-side (or the limit is documented explicitly) rather than weakening
  the invariant; see the amendment for why AAD cannot serve.
- `WrappedKey(provider, key_id, key_version, ciphertext)` — recorded next to the
  ciphertext so a rotation can decide what to re-wrap without guessing who wrapped it.

Rules that make the seam real rather than decorative:

1. **The organization envelope stores a self-describing value**
   (`provider:key_id:key_version:<base64 ciphertext>`, versioned). It is one Text
   column in 5.2, so adding a provider must not require a migration, and a row always
   says which provider can unwrap it. *(Decided here; implemented in 5.2 — on
   `organizations` at first, relocated to the RLS-scoped `organization_dek_envelopes`
   in 5.2.1.2, §10.6.)*
2. **`rewrap_dek` is a provider operation**, so §6.3's "KEK rotation = re-wrap every org
   DEK" never decrypts a DEK into application memory to re-encrypt it.
3. **No provider may return the root key**, and no application code path reads, logs or
   serializes one; `unwrap_dek` is the only way material becomes readable.
4. **No fallback chain.** One configured provider; if it is unavailable or misconfigured,
   the operation fails closed with a named error. There is no "if the KMS is down, use
   the env key" path — that path is the vulnerability, not the recovery.
5. **Unwrap is operation-scoped** (approved point 5): the adapter returns a plaintext DEK
   to its caller and holds it nowhere. No module keeps a plaintext DEK in a process-wide
   cache, keyed by org or otherwise; the LRU that §6.2 originally sketched is **not** part
   of 5.2.1 and needs a measurement before it is reconsidered.
6. **Rewrap delegates to the provider** (approved point 6), which is the only way
   `rewrap_dek` can honour "no plaintext DEK during KEK-only rotation": for Vault that is
   `transit/rewrap` against the stored ciphertext, so the DEK never becomes visible to
   NexusOps code. A provider without a rewrap primitive must implement the operation
   provider-side (bring-your-own-key import or an equivalent) rather than decrypting into
   the application.

**Amendment — the binding is the provider's derivation context, not AAD (approved
2026-10-12).** The bullet above originally said "associated data wherever the provider
supports it". Implementing the Vault adapter against a real Vault 1.15 transit key showed
that this cannot hold, so the binding is re-specified here rather than quietly worked
around:

- **What was measured.** `transit/encrypt` and `transit/decrypt` accept both
  `associated_data` (AAD) and a derived-key `context`, but **`transit/rewrap` has no
  `associated_data` parameter at all**. A ciphertext encrypted with AAD therefore fails
to rewrap — Vault returns `message authentication failed`, because the AAD cannot be
  supplied on that path. An AAD binding makes an envelope **un-rotatable provider-side**,
  which would force a KEK rotation to unwrap every DEK in the application — precisely
  what approved point 6 forbids. The two parameters are not interchangeable, and neither
  is "authenticated context" merely because it is stored next to the ciphertext.
- **What the binding is, therefore.** The organization, purpose and DEK generation travel
  as the **derivation context** (base64) of a transit key created with **`derived=true`**.
  Vault accepts that context on `encrypt`, `decrypt` *and* `rewrap`, a wrong value fails
  authentication, and the binding survives provider-side rewrapping intact. `derived=true`
  is a **hard requirement of the deployment**, not a preference: a key created without it
  cannot satisfy the binding, and the platform reports that as an *invalid configuration*
  (with the fix in the message) and refuses to wrap — it never falls back to a weaker
  binding, and it never stores the context beside the ciphertext as though it were
  authenticated.
- **How it is proven.** The repo carries tests for both halves: wrong organization,
purpose and generation each fail to unwrap; rewrap preserves the binding and moves the key
  version with no plaintext DEK returned; and the AAD failure above is asserted against a
  real Vault container, so the reason for the choice stays measured rather than
  remembered (`backend/tests/integration/test_kek_vault_transit_live.py`). A future
  provider that offers only AAD must implement an equivalent provider-side rewrap before
  it can be selected — adding it to a fallback chain is not an option (rule 4).

**Development and tests: a deterministic provider, and no way to reach it in production.**

| Requirement | How it is satisfied |
|---|---|
| Deterministic wrap/unwrap for tests and fixtures | `DeterministicKEKProvider` (provider name `test`): a fixed test root key, deterministic ciphertext, so a fixture's wrapped DEK is reproducible run to run. It implements the same interface and nothing else — no vendor SDK, no network. |
| Explicit selection only | A single settings field names the provider. There is no environment sniffing and no auto-detection; dev/test set it to `test`, non-production deployments that want fidelity set the real provider. |
| Production cannot select it | Startup validation **aborts at import** if the provider is unset, unknown, or `test` in a production configuration — the same fail-fast path `ENCRYPTION_KEY` uses today (`backend/app/core/config.py`, exit 2). An unsafe key source is therefore unreachable *by configuration*, not by convention. |
| No silent degradation | A provider error is raised, never converted into a different key source, and never into a plaintext-or-nothing decision. |
| Real-provider coverage without production secrets | CI may run a Vault transit instance (or a cloud KMS emulator) against the same interface; the production key and the production ACME directory are never contacted (§10.2). |

### 6.8 Decisions closed here, and what remains an operator choice

Settled on 2026-10-12, so §3.7 step 1 and §10.5 are unblocked:

| # | Decision | Outcome |
|---|---|---|
| K1 | Which provider the first production deployment uses | **Vault Transit** (approved). Cloud KMS adapters are future work behind the same interface, not part of 5.2.1 |
| K2 | Root/unseal custody | **Auto-unseal through a cloud KMS**, with the unseal material itself in break-glass custody separate from DB backups (C4). The Vault data at rest is protected by Vault's storage plus that KMS; the residual choice is *which* cloud KMS provides auto-unseal (§6.9) |
| K3 | Audit retention | **Specified** in §6.9: the transit audit trail is enabled, exported off the Vault host, and retained ≥ 13 months with a quarterly access review |
| K4 | Caching policy | **Decided against caching**: operation-scoped unwrap, no long-lived plaintext-DEK cache until a measurement justifies one (approved point 5). This supersedes the LRU sketch in §6.2 |
| K5 | Cost envelope | Recorded, not a blocker: Vault OSS is free but needs a host and its unseal KMS (~$1 per cloud KMS key-month plus ~$0.03 per 10k key-use operations at list price) |

**Still an operator decision inside the approved direction** (each is recorded in the
deployment runbook, and none reopens the six approved points): which cloud KMS provides
Vault auto-unseal; the exact `transit` key name and mount path per environment; the
audit log destination; and the named holders of break-glass material. None of these
blocks writing 5.2.1 — the adapter takes them from configuration.

### 6.9 Operational key-custody requirements (approved with §6.7)

These are requirements on the *deployment*, not code to write: they are what makes C1–C6
provable rather than asserted. They are written down here, next to the decision they
implement, because an approved KMS direction without them is a plan to have a KMS
somewhere.

**Vault authentication, TLS and least privilege.**

| Requirement | Specification |
|---|---|
| Auth method | **AppRole** (approved): the API/worker receives a `role-id` and a wrapped/response-limited `secret-id` through the environment; no root token, ever, on an application host. The token TTL is short (hours) with renewal, so a leaked token expires without human action |
| Policy scope | One policy per environment, granting `update` on `transit/rewrap/<k>`, `update` on `transit/encrypt/<k>` and `update` on `transit/decrypt/<k>` for **one** key name, plus `read` of that key's metadata. No `sys/*`, no `transit/keys/*` create/rotate in the application policy — those are operator actions |
| TLS | Vault speaks TLS with a verified certificate (no `-tls-skip-verify`), reached over a private network path where the topology allows; the client validates the CA explicitly and the configuration names it |
| Separation | The application's policy cannot rotate keys, cannot list other mounts, and cannot read the unseal material; rotation is an operator/runbook action that the application only *observes* (`key_version` changes) |
| No bypass | The KEK never lands in application code, the database, a log, an event, an audit row, or an API response (approved point 4). The adapter holds no root key and no unwrap path outside `unwrap_dek` |

**Storage protection, availability, recovery.**

| Requirement | Specification |
|---|---|
| Storage at rest | Vault's own storage backend is encrypted (integrated storage with auto-unseal, or a storage backend whose encryption key is KMS-managed); the snapshot/backup of that storage is exactly as sensitive as the KEK it holds |
| Availability | Vault is a **hard dependency of issuance, delivery and DNS-credential reads** — it is not on the request path of anything else. An outage degrades those features and nothing more; the API must stay up and report the provider as unavailable rather than fail requests it can serve |
| Recovery | Restore = Vault storage restore + auto-unseal KMS availability, then verify a known-wrapped DEK unwraps. The recovery target is recorded (RTO/RPO) and the drill in the row below measures it |
| Key-loss consequence | Losing the Vault KEK (and its unseal KMS key) makes every wrapped DEK permanently unreadable: all certificate material, DNS credentials and ACME account keys are unrecoverable and must be re-created. Certificate material is **reproducible** (re-issue, §6.5); DNS credentials are re-enterable; ACME account keys require re-registration. Losing one org's wrapped DEK is bounded to that org |

**Root/unseal custody and the auto-unseal dependency.**

- **Approved: auto-unseal via a cloud KMS.** Its cost is stated where it belongs: Vault cannot start without that cloud KMS being reachable and authorized, so the KMS becomes a documented availability dependency of the certificate subsystem. The KMS key's own policy grants decrypt/unwrap to **Vault's identity only**, never to the application.
- Break-glass material — the auto-unseal KMS credentials *and* the recovery keys/snapshots needed to rebuild Vault — is stored **separately from DB backups**, with two-person access (C4). If the same compromise window reaches the DB backup and the break-glass store, the envelope has bought nothing.
- Rekeying/recovery of Vault itself (root token regeneration, rekey) is an operator ceremony with its own runbook; the application has no path to perform it.

**Backup and restore exercises.**

- A **non-production drill** is part of the exit criteria for 5.2.1's production readiness: restore Vault storage, confirm a wrapped DEK from a snapshot unwraps, then run the org-DEK rotation path (§6.3) end to end.
- A **DB-restore drill** additionally proves the pairing: database restored from backup + Vault restored ⇒ material readable; either one alone ⇒ nothing readable (this is the property §6.1 claims for the DB-only case, and the drill is what makes it evidence rather than a claim).
- Drills are recorded in the runbook with dates and the operator who ran them; C4 is not satisfied by a written procedure alone.

**Audit logging, retention and access review.**

- Vault's **audit device is enabled on every path** (file/syslog to an off-host sink) so every encrypt/decrypt/rewrap is attributable to a role and a time; the application additionally records *its own* one-line audit for the operation it performed, without the DEK or ciphertext.
- Retention: **≥ 13 months**, long enough to cover a full annual cycle plus the investigation window; a compliance regime that demands longer raises this and nothing else (§6.8 K3).
- **Quarterly access review**: who holds the AppRole `secret-id`s, who can read the audit sink, who holds break-glass material. A review that has not run is a finding against C5.

**DEK generation, wrapping, rotation, recovery.**

| Stage | Requirement |
|---|---|
| Generation | The DEK is generated **in the application** with a CSPRNG (Fernet-compatible key), then wrapped by the provider. The DEK is never *derived* from anything, never reused across organizations, and never re-wrapped twice with the same `dek_generation` recorded |
| Key creation (operator) | The transit key is created **once, by the operator**, with **`derived=true`** and a type that supports a derivation context (`aes256-gcm96`). The application never creates or configures keys, so `derived=true` belongs in the provisioning runbook (§6.7 amendment) |
| Wrapping | `wrap_dek` with the `EncryptionContext` bound as the **derivation context** of a `derived=true` key (§6.7 amendment) — not as AAD, which rewrap cannot carry. The stored value is the self-describing envelope, so the row states which provider, key and version can unwrap it |
| Rotation (KEK-only) | **`rewrap_dek` provider-side** (approved point 6): Vault `transit/rewrap` rewrites each stored ciphertext under the new key version with no plaintext DEK returned to the application. It is idempotent per row and resumable |
| Rotation (org DEK) | New DEK generation → wrapped → the organization's `dek_generation` bumped → the org's Phase-5 rows re-encrypted in background batches, each row's `deke_id` updated as it is re-encrypted. A half-rotated org is visible (mixed `deke_id`), never silently half-readable |
| Recovery | A generation whose ciphertext cannot be unwrapped is **not** served and **not** guessed at: it is marked failed with a reason and re-issued (§6.5), matching the fail-closed behaviour of `decrypt_str` today |
| Key loss | Stated above, and stated in the UI/docs (C6): per-org DEKs do **not** bound a KEK compromise or an application-runtime compromise (§6.1). Nothing in this section changes that, and no document or interface may imply it does |

**Startup behaviour.**

| Configuration | Behaviour |
|---|---|
| Provider unset, unknown, or `test` in a production configuration | **Abort at import** (exit 2), the same fail-fast path `ENCRYPTION_KEY` uses today |
| Provider configured but unreachable (Vault down, KMS unreachable, AppRole secret expired) | The API **starts** and serves everything that does not need a DEK; certificate issuance, material delivery and DNS-credential reads fail closed with a named error, are visible to the operator (health reporting), and are **not** retried into a storm. No fallback to an env key, ever |
| Provider reachable but the role lacks the policy | Fail closed with the provider's own denial surfaced, and a health check that distinguishes "unreachable" from "unauthorized" — the two need different operator actions |
| Provider reachable but the transit key is **not derivable** | **Invalid configuration**, reported as its own state (not "unhealthy"): the provider is fine, the key cannot satisfy the binding, and the fix is to re-create it with `derived=true`. Key-management operations refuse; the API keeps serving |
| Non-production implementation (`test`) in a non-production environment | Allowed, loudly: it is logged at startup and reported in health, so an environment can never be *mistaken* for production custody |

---

## 7. Secure delivery of certificate material to authorized nodes

### 7.1 The requirement

The existing operation transport is **not** an acceptable channel for private keys:

- `operations.params` is a JSONB column returned by `OperationOut` and the
  operation-history API, copied into `AgentOperationClaimOut`, and (today) the whole
  params blob flows to the agent on claim.
- Params sit at rest in the DB and in any backup; results and audit metadata are read
  by humans; events carry payloads to WS subscribers.

Redaction (Phase 4.4) is **defense in depth**, not permission to put a key in an unsafe
data path. Phase 5 therefore builds a **dedicated, narrowly scoped delivery
mechanism** and keeps key material out of the ordinary operation data entirely.

### 7.2 The mechanism: reference-only op + material in the claim response

`certificate.install` / `certificate.remove` are ordinary whitelisted Operation rows
so they inherit the pull model, CAS, expiry, capability gating, audit and tenancy. Their
**params are reference-only** (`{certificate_id, generation, fingerprint}`). The key
material is **never** in `params`, never in `result`, never in `order_state`, never in
events, audit or logs.

Material reaches the node through a **dedicated delivery endpoint** authenticated the
same way as claim/result:

```
POST /agent/certificates/{delivery_id}/material   X-Agent-Token
```

Bound by every one of:

- **Authenticated node + org** — `require_server` resolves the node from the token and
  acts in that node's org scope; the CAS additionally requires
  `delivery.servers_id == this node`.
- **Specific certificate + operation + generation** — the request carries the
  `delivery_id`, which is `(certificate, generation, node)` unique (§3.3); a request
  for a generation that is not the node's current target is refused.
- **No ordinary-data path** — the material is assembled at read time
  (`decrypt_str(key_ciphertext)` under the org DEK) inside the request, written to the
  response body only, and dropped.
- **`Cache-Control: no-store`** and an explicit response policy: the response is
  assembled fresh per request, never cached, never compressed in a way that leaves it
  in a proxy buffer, and the API writes no access-log body for this route (the existing
  middleware logs method/path/status only).

### 7.3 Authorization binding

| Property | Enforcement |
|---|---|
| Node identity | `X-Agent-Token` → node + org (existing `require_server`) |
| Delivery exists for this node | `delivery.servers_id == node.id` in the CAS |
| Generation is current | `delivery.generation_id` is the certificate's `current_generation_id` **and** its state is `ISSUED` |
| Certificate is bound to a route on this node | The delivery row only exists because a route on this node references the certificate (derived target set, §7.4) |
| Not superseded | A generation flipped to `SUPERSEDED` refuses delivery |

### 7.4 Derived (never configured) target set

The set of nodes that may receive a certificate is derived, never entered:

```
targets(cert) = distinct node_id of routes
                where routes.certificate_id = cert.id AND routes.enabled AND domain VERIFIED
```

A node receives a certificate **only** if it serves a route using it. Gaining a route
creates a delivery row; losing the last route creates a removal. This is the secret
minimization rule (secrets-architecture.md §7, domain-model.md §3.7) applied to TLS.

### 7.5 Recovery for an interrupted delivery

A claimed delivery whose response was lost (agent crashed mid-download) must be
recoverable **without** re-running issuance and **without** a stale-window replay hole:

- The material endpoint is idempotent: a repeated request for the same still-current
  delivery returns the same material and does not create a new delivery row.
- The delivery op has a bounded recovery window (one execution deadline + result grace,
  the existing Phase 4 timing model). After it, a **new** delivery operation is queued
  by the reconciler with a fresh `delivery_id`, so there is no unbounded window in
  which an old delivery id returns material.
- A delivery is **replay-bounded**: the endpoint refuses when the delivery's generation
  is no longer current, when the op is terminal, or when the recovery window has passed.

### 7.6 Material never persists in ordinary data

> **Normative rule.** **No certificate private key — and no certificate chain — may
> enter ordinary operation parameters, operation results, audit metadata, event
> payloads, or logs.** The only transport for private key material is the dedicated
> authenticated delivery endpoint of §7.2, whose response is assembled at read time
> and never stored; ordinary operation rows carry references only. This is a hard
> boundary, not a redaction expectation: redaction (§7.6 row below, Phase 4.4) is
> defense in depth and must never be relied on as the control that keeps a key out of
> these paths. Contract tests assert the absence on every path listed here.

| Path | Rule |
|---|---|
| `operations.params` / `result` | Reference-only; enforced by the params model and a contract test |
| `certificate_deliveries` | No ciphertext column at all |
| `certificate_generations` | Ciphertext, decryptable only by the control plane; never in API responses |
| Events / WS | ids + fingerprint + state only |
| Audit metadata | ids + fingerprint + state only |
| Logs | never; the recursive PEM-aware redaction (Phase 4.4) is the backstop, not the control |
| Operation-history API (`GET /operations/{id}`) | Returns reference-only params (they *are* reference-only) |
| Frontend | no field to hold key material |

This is the explicit separation the acceptance criteria require: certificate
private-key delivery is a distinct mechanism from ordinary operation data, even though
it reuses the operation *claim* for scheduling.

---

## 8. Agent changes, installation, atomic activation, rollback

### 8.1 New agent-side registry entries

The agent's `OPERATION_REGISTRY` is compile-time (`agent/nexusops_agent.py`). Phase 5
adds two entries and one delivery handler:

```python
"certificate.install": {"capability": "nginx", "timeout": 180, "action": "cert_install"},
"certificate.remove":  {"capability": "nginx", "timeout": 120, "action": "cert_remove"},
```

The install action:

1. validates params (reference-only: certificate id, generation, fingerprint, expected
   paths) against a closed model, exactly like the bundle validator;
2. fetches material from `POST /agent/certificates/{delivery_id}/material` over the
   authenticated channel;
3. verifies the **fingerprint** of the fetched leaf against the params — a mismatch is
   refused before anything is written;
4. writes `privkey.pem` (0600, root) and `fullchain.pem` (0644) into a
   **content-addressed** directory: `/etc/nexusops/tls/<fingerprint>/` (§8.4);
5. atomically swaps the directory into place (temp + fsync + rename, Phase 4's
   `_write_file`/`_fsync_dir` discipline);
6. reports `INSTALLED` with the fingerprint.

The remove action deletes the certificate's managed directory and reports
`REMOVED`; it never touches a directory another generation still references.

### 8.2 Reuse of the Phase 4 apply pipeline

Installation does **not** itself reload nginx. Rendering the TLS server block and
applying it is the existing `nginx.apply` path (bootstrap the managed tree if needed,
then stage → `nginx -t` → backup + atomic swap → reload → rollback). This is what
makes activation atomic with rollback: the node never runs a half-written TLS
configuration, and a failure restores the previous HTTP-only tree.

The renderer must emit `ssl_certificate`/`ssl_certificate_key` pointing at the
**content-addressed** path, and the bundle's managed allowlist must be extended to
permit exactly `/etc/nexusops/tls/<64-hex>/fullchain.pem` and `.../privkey.pem` — a
closed path shape, not a free path field.

### 8.3 Certificate identity is content-addressed

Replacing certificate material must change the rendered configuration's fingerprint so
desired-vs-applied drift is detectable. Because the bundle fingerprint is a hash over
the rendered file *contents* (`backend/app/schemas/proxy.py`), referencing the
material by its **fingerprint in the path** means:

- a new generation produces a different `ssl_certificate` path ⇒ a different rendered
  file ⇒ a different `bundle_id`;
- the node's next `nginx.status` reports a `live_bundle_id` that differs from the
  desired one until it applies, so drift is visible in the existing Phase 4.4
  reconciler with no new mechanism;
- the desired-vs-applied comparison cannot be fooled by same-path, different-content
  material, because the path itself encodes the content identity.

`proxy_state.tls` records the desired/confirmed fingerprint set per node, written
under the Phase 4.4 single-writer lock (taken before the read; lock order
`servers → routes → monitors`).

### 8.4 Backup, staging, validation, atomic swap, rollback (as they exist today)

The agent's current behavior, which Phase 5 inherits rather than re-derives:

| Step | Current implementation | Phase 5 use |
|---|---|---|
| Stage | `_stage_bundle` writes to `staged/<bundle_id>/`, creating `routes.d` unconditionally | Unchanged; the TLS tree is staged the same way |
| Validate | `_staged_test_conf` renders a self-contained config and runs `nginx -t` | The TLS block is part of the staged tree, so an invalid certificate path fails validation before going live |
| Backup | `_swap_tree` copies the current tree to `NGINX_BACKUP_DIR` before swapping | Unchanged |
| Swap | `_swap_tree` atomically moves routes then the http-level file | Unchanged |
| Reload | `_reload_nginx` (`nginx -s reload`, SIGHUP fallback) | Unchanged |
| Rollback | `_restore_tree` + reload; `ROLLBACK_FAILED` is a defined terminal state | Unchanged |

Certificate **files** are written before the apply, not during it, so a re-apply after
a failed reload does not need to re-fetch material.

### 8.5 Older generation must not replace a newer one

Three independent guards, so no single bug wins:

1. **Generation immutability** — renewal inserts a new generation and marks the old
   `SUPERSEDED`; the material endpoint refuses `SUPERSEDED` (§7.3).
2. **Content-addressed paths** — even if an old install op were replayed, it would write
   a different directory and the renderer would still reference the current
   fingerprint, so the applied config could not regress to old material.
3. **Delivery identity** — a delivery row is `(generation, node)` unique; the
   reconciler only queues deliveries for the **current** generation, and a terminal
   old delivery is never reopened.

### 8.6 Renewal when a node is offline

Renewal: a new generation is issued and a delivery is queued per serving node. A node
that is offline keeps its delivery `PENDING` while the old material remains installed
and serving (renewal starts ≥30 days before expiry). The node converges on its next
heartbeat. The certificate's `expires_at` still reflects the **current**
generation, so an offline node is visible as "renewed, delivery pending" rather than a
silent success. If the old material expires before the node returns, the HTTPS endpoint
degrades and the expiry monitor pages — honestly, not silently.

---

## 9. Renewal, expiration, ownership loss, removal, revocation

These are **four distinct operations** and the design must not conflate them:

| Operation | What it changes | What it does **not** do |
|---|---|---|
| **Removal** (from a route/node) | The route/node stops being *allowed* to serve the material; the node applies a config without it | Does not invalidate the certificate at the CA |
| **Suspension** (association with an org/domain) | The certificate is marked not-authorized-for-serving; deliveries stop | Does not remove material already on nodes until they apply; does not revoke at the CA |
| **Revocation** (with the CA) | The CA marks the cert revoked; the served material is publicly distrusted | Does not reach every node immediately; local refresh is a best-effort follow-up |
| **Local-only removal** | Material deleted on nodes; CA revocation failed or was not attempted | Is **not** revocation; recorded as `REVOKED_LOCAL_ONLY` with a warning and a retry |

### 9.1 Renewal

- **Sweep:** hourly, claim certificates `auto_renew AND current generation ISSUED AND
  not_after < now() + 30 days` (`FOR UPDATE SKIP LOCKED`); enqueue a new generation
  (same flow as §5, new generation row). Staging directory default for non-production.
- **Failure:** an attempt that exhausts its budget raises `certificate.failed` →
  CRITICAL alert + incident through the existing pipeline; resolution is automatic when
  a later attempt succeeds (mirrors monitor auto-resolve).
- **Expiry breach:** if `not_after` passes with renewal still failing, the sweep flips
  the status to `EXPIRED` — a CRITICAL state surfaced by the TLS-expiry monitor rather
  than a second incident path.
- **Manual** `POST /certificates/{id}/renew` forces a new generation outside the
  window; audited like any issuance.

### 9.2 Expiration monitoring

The certificate-target monitor (§3.6) evaluates `not_after - now()` and pages through
the existing engine. It is independent of the route's HTTPS uptime monitor: a valid
certificate with a dead endpoint and a live endpoint with an expired certificate are
different incidents.

### 9.3 Ownership loss (a verified Domain changes owners)

The platform already handles the *HTTP* half of this: a domain verified by another org
flips the previous owner to `UNVERIFIED` immediately, its routes leave the desired
configuration (`REQUESTED`), and each serving node is told to drop the name
(domain-routing.md §4.3, §8.4). Phase 5 extends the same discipline to certificates:

The five stages below are **decoupled on purpose**: suspending authority and removing
config are immediate and must not wait on the CA; CA revocation is important but is an
asynchronous follow-up that must never gate the security-relevant step.

**Stage 1 — immediate suspension (automatic).** On the cross-org flip, every
certificate bound to the losing domain is **suspended**: certificate `status=SUSPENDED`,
`suspended_at`, `suspension_reason=domain_ownership_lost`, audit `certificate.suspended`.
A suspended certificate is no longer authorized to serve the affected identifiers: the
API refuses new binds to it for those identifiers and refuses renewal for them.

**Stage 2 — immediate reconcile of the old configuration (automatic).** Every served
node is re-rendered **without** the affected route and **without** its TLS block; the
removal is `REQUESTED` until an agent applies (requested ≠ confirmed, Phase 4.4). The
route left the *desired* configuration at the suspension moment, so the previous owner's
configuration is no longer authorized to serve the name **before** any node applies;
the node converges on its next successful apply. A node that cannot be reached stays
`REMOVAL_PENDING` and the state is visible, never assumed.

**Stage 3 — automated CA revocation, subject to a certificate-impact safeguard
(decided).** Once ownership loss is **confirmed** (the losing org's proof is gone / the
name is verified by another org) and the suspension is recorded, the platform
**automatically** queues revocation of the affected certificate generation — but only
after an impact check that prevents collateral damage:

| Situation | Automatic action |
|---|---|
| **All** of the certificate's identifiers are affected by the ownership loss | Revoke the generation (nothing legitimate remains on it). |
| The certificate covers **multiple identifiers**, some **not** affected (e.g. a shared `[example.com, *.example.com]`, or one cert across several owned domains) | **Do not revoke the shared certificate.** It must first be **replaced or split**: issue a new certificate for the still-owned identifiers, bind the surviving routes to it, deliver + apply, and only then revoke the old shared generation. Until the replacement is active, the old generation is `SUSPENDED` for the lost identifiers only — routes using the lost identifiers are already out of the desired configuration, and routes using the retained identifiers keep serving under the not-yet-revoked generation. |
| The certificate has already been replaced/split and its affected identifiers are gone | Revoke the superseded generation. |
| The impact check cannot determine safety (missing metadata, unclear bindings) | **Fail closed: do not revoke automatically.** Raise an operator-visible item instead of guessing. |

The **replacement/split-before-revoke** rule is the safeguard the approved direction
requires: a shared certificate is never revoked while it still legitimately serves an
identifier the organization continues to own.

**Stage 4 — revocation must not block removal.** Revocation is an asynchronous,
retryable CA call with its own state (`revocation_state`: `PENDING` → `REVOKED`, or
`FAILED` retried with bounded backoff, or `REVOKED_LOCAL_ONLY` when the CA is
unreachable). Old-configuration removal (Stage 2) is **never** gated on revocation
succeeding: the node stops serving the lost name as soon as it applies, whether or not
the CA has answered. A pending or failed revocation is visible (incident + audit) but
does not stall the step that actually protects the name. The manual
`POST /certificates/{id}/revoke` remains available for operator-initiated revocation,
and uses the same safeguard (a manual revoke of a still-serving shared certificate is
refused with a named error unless the caller confirms the impact).

**Stage 5 — visibility and audit.** `certificate.suspended`,
`certificate.ownership_lost`, `certificate.revocation_requested`,
`certificate.revoked`, `certificate.revocation_failed`, `certificate.split`, together
with the Phase 4.4 `route.removal_requested`/`route.removal_confirmed` pair; events are
org-scoped, and the losing organization is told the reason without being told the winner
(mirroring domain-routing.md §4.3). **Desired state, confirmation evidence, retries and
failure visibility are exactly the Phase 4.4 removal semantics.**

### 9.4 Removal

Disabling/deleting the last route using a certificate, or unbinding it, creates a
delivery removal for the affected nodes. The node applies a bundle whose manifest omits
the certificate paths; `certificate_deliveries.state = REMOVED` is written **only** from
an applied-result (never from a queued or attempted apply). An offline node reads
`REMOVAL_PENDING`, and the node stays in the reconcile sweep through
`proxy_state.reconcile_required` even after its last route is gone (Phase 4.4).

### 9.5 Revocation

Revocation has **two entry points** but **one path and one safeguard**:

- **Automated** (ownership loss, §9.3 Stage 3): queued automatically only after the
  impact check passes or the certificate has been replaced/split.
- **Manual** (`POST /certificates/{id}/revoke`, `certificate.manage`): operator-initiated;
  refuses to revoke a still-serving shared certificate unless the caller confirms the
  impact (same safeguard).

Both call the CA's revoke endpoint for the target generation using the org's ACME
account, and both write `revocation_state` (`PENDING` → `REVOKED`). Because revocation
is an irreversible CA action, the platform never reports it optimistically:

| Outcome | Recorded | Retry |
|---|---|---|
| CA acknowledges | `revocation_state=REVOKED`, `revoked_at` | — |
| CA unreachable / rejects | `revocation_state=FAILED` with a sanitized reason; material may already be removed locally | bounded exponential backoff; after the budget, `REVOKED_LOCAL_ONLY` with an operator-visible incident |
| Splitting/replacing a shared cert (multi-identifier, §9.3) | `certificate.split` audit; the old generation is `SUSPENDED` for the lost identifiers until the replacement is active | n/a |

**Removal of the old configuration is never gated on revocation.** A node stops serving
the lost name as soon as it applies (Stage 2), whether the CA has answered or not. The
three states — `REVOKED`, `REVOCATION_FAILED`/`REVOKED_LOCAL_ONLY`, and
`SUSPENDED`-but-not-yet-revoked — are distinct in the API, the UI and the audit trail,
so an operator is never told a certificate is revoked when it is not.

---

## 10. Implementation slices, acceptance criteria, tests, limitations

### 10.1 Slices (each independently reviewable, in order)

| Slice | Scope | Ships | Acceptance criteria |
|---|---|---|---|
| **5.1 — Certificate metadata & lifecycle foundations — SHIPPED 2026-10-12 (`37b7211`)** | `certificates` + `certificate_generations` **first** migration (identity + pre-issuance lifecycle only — **no `dns_provider_id`, no material columns, no `deke_id`**), `certificate.read`/`certificate.manage` codenames **+ the role matrix (§4.1, O3 resolved)**, RLS/grant pattern from the Phase 4 migration, metadata-only CRUD (no issuance) | Migration + API + IDOR cases | A `certificates` row is org-scoped; a foreign id is 404; `GET` returns no ciphertext field; the one-live-generation unique index rejects a second concurrent issuance; **the generation `state` CHECK is limited to pre-issuance states, so an `ISSUED` row is rejected** (no forward dependency on 5.2); no `dns_providers` table exists yet and nothing references one; no `deke_id` column exists, so no placeholder can be written; role matrix matches §4.1; drift test green. |
| **5.2.1 — KEK provider and organization DEK envelope — SHIPPED 2026-10-12 (`06e8c52`); storage relocated by **5.2.1.2** (`a7b8c9d0e1f2`, §10.6)* | The `KEKProvider` seam with the **Vault Transit** adapter and the deterministic test provider; the organization envelope (`organization_dek_envelopes.dek_ciphertext` / `dek_generation` — the plan put these on `organizations`; §10.6 moved them); org-DEK create/wrap/unwrap/rewrap; provider configuration + fail-fast startup validation; operation-scoped unwrap (no LRU) | Migration (`organization_dek_envelopes` + the `organizations` columns it retires) + provider module + envelope service + config + tests | A production configuration cannot select or fall back to a non-production provider (abort at import); the KEK never reaches application code, the DB plaintext, logs or responses; a wrap/unwrap round-trip is bound to `(org_id, purpose, dek_generation)` so a moved ciphertext is rejected; `rewrap_dek` leaves no plaintext DEK in the application; provider outage fails closed with a named error while the API stays up; **no certificate/DNS material column exists yet, so nothing can be written with a placeholder key** |
| **5.2.2 — Providers, ACME accounts and material columns** — *after 5.2.1* | `dns_providers` + its metadata-only API and credential storage, `acme_accounts`, the generation material columns + `deke_id`, `certificates.dns_provider_id` **FK added with its target table**, widened `state` vocabulary, **material guard CHECK**; `verify_creds` + zone allowlist | Migration + service + write-only API | **An issued (or superseded/suspended/expired/revoked) generation cannot exist without `key_ciphertext`, `chain_ciphertext`, `deke_id`, `issued_at` and `not_after`** (guard CHECK rejects it); `dns_provider_id` FK resolves to a real row (no artificial provider); DNS credential never returned by any endpoint; a challenge outside `zone_allowlist` is refused; DEK rotation re-encrypts only Phase-5 rows; no existing secret re-encrypted; a `decrypt_str` mismatch fails closed |
| **5.3 — ACME issuance (staging + pebble)** | `acme`/`josepy` dependency behind `AcmeProvider`; per-org account; DNS-01 order → publish → propagate → validate → finalize → store; state machine; backoff | Worker task + tests against pebble | Issue a certificate for a name whose TXT record the test publishes; generation reaches `ISSUED` with `not_after` set; retry/backoff and stuck-state sweep pinned; **no production CA traffic in tests** |
| **5.4 — Secure delivery** | `certificate_deliveries`, `POST /agent/certificates/{id}/material`, `certificate.install`/`.remove` op types + agent handlers, content-addressed paths, fingerprint check, no-store response policy | Endpoint + op types + agent + contract tests | **No certificate private key or chain appears in operation params, results, audit metadata, events or logs** (asserted by tests over each path, §7.6); a foreign node's delivery is 404; a superseded generation is refused; a duplicate claim is idempotent; interrupted delivery recovers within the window and not after. **Non-production only until C1–C6 (§6.6) are met.** |
| **5.5 — HTTPS activation & verification** | Renderer TLS block, allowlisted `tls` paths, `routes.certificate_id` + widen `scheme`, `proxy_state.tls`, activation endpoint, control-plane HTTPS probe | Migration + renderer + API | HTTP keeps serving until the probe succeeds; a bad cert path fails `nginx -t` and rolls back to the HTTP tree; `scheme` flips to `https` only after `VERIFIED_ACTIVE`; content-addressed path change ⇒ different `bundle_id` ⇒ drift detected |
| **5.6 — Renewal, expiry monitor, removal, revocation** | Hourly sweep, `CERTIFICATE` monitor target, removal/`REMOVED` state, suspension on ownership loss, automated revocation with the impact safeguard, replace/split for shared certs, `REVOKED_LOCAL_ONLY` + retry | Beat schedule + monitors + API | Renewal produces a new generation and supersedes the old; an offline node stays `PENDING` without a false success; expiry monitor pages independently of uptime; ownership loss suspends + re-renders + removes-on-confirm; a shared multi-identifier cert is **never** auto-revoked while a retained identifier still serves — it is replaced/split first; removal is **never** gated on CA revocation; revoked vs local-only vs suspended are distinct |
| **5.7 — Hardening pass** | Redaction extended to cert material (already PEM-aware), rate-limit/CAA handling, operational runbooks, backfill of docs | Docs + tests | Redaction tests cover chain+key; the platform-security-model threat rows are updated; no key material in any asserted path |

#### 10.1.1 Phase 5.1 acceptance criteria — met, with the evidence

Each criterion from the 5.1 row above, and the test that substantiates it. Nothing
here is claimed on the strength of the migration alone.

| 5.1 acceptance criterion | Evidence |
|---|---|
| A `certificates` row is organization-scoped | `tests/integration/test_certificates.py::test_a_certificate_is_tenant_owned_and_unreachable_without_a_scope`; `::test_both_new_tables_carry_a_tenant_and_a_system_policy` |
| A foreign id is 404 (no existence oracle, no 403) | `::test_a_foreign_certificate_id_is_the_same_404_as_a_random_one`; `::test_listing_and_filtering_never_cross_tenants`; `::test_rls_blocks_cross_tenant_certificate_reads_without_the_orm` |
| `GET` returns no ciphertext field (nor key material, nor an internal cursor) | `tests/unit/test_certificate_lifecycle.py::test_the_response_models_expose_exactly_the_approved_fields`; `::test_no_response_field_can_hold_key_material`; `::test_the_request_body_rejects_fields_this_phase_does_not_have` |
| The one-live-generation unique index rejects a second concurrent issuance | `tests/integration/test_certificates.py::test_a_second_in_flight_generation_is_refused_but_a_failed_one_is_not`; `::test_duplicate_requests_are_refused`; `tests/unit/test_certificate_lifecycle.py::test_the_one_live_generation_index_covers_exactly_the_live_states` |
| The generation `state` CHECK is limited to pre-issuance states, so an `ISSUED` row is rejected | `tests/integration/test_migration_phase5.py::test_an_issued_generation_is_rejected_and_a_pre_issuance_one_is_not`; `tests/integration/test_certificates.py::test_an_issued_generation_is_unrepresentable`; `tests/unit/test_certificate_lifecycle.py::test_issued_is_not_a_generation_state`; `::test_handing_a_material_state_to_the_lifecycle_is_refused_loudly` |
| No `dns_providers` table exists and nothing references one; no `deke_id` column exists, so no placeholder can be written | `tests/integration/test_migration_phase5.py::test_the_slice_boundary_is_not_forward_referenced`; `::test_the_two_tables_carry_the_specified_columns` |
| The role matrix matches §4.1, and `certificate.read` alone grants nothing else | `tests/unit/test_certificate_lifecycle.py::test_the_registry_and_the_committed_role_matrix_agree`; `::test_certificate_read_does_not_carry_management_authority`; `::test_the_registry_adds_exactly_the_two_certificate_codenames`; `tests/integration/test_migration_phase5.py::test_the_codenames_and_their_grants_land_with_the_migration`; `tests/integration/test_certificates.py::test_certificate_read_alone_does_not_authorize_management` |
| Migration upgrade/downgrade on a populated instance, and a single Alembic head | `tests/integration/test_migration_phase5.py::test_a_populated_instance_migrates_without_losing_anything`; `::test_the_migration_is_reversible_and_reappliable`; `::test_the_phase5_revision_extends_the_phase4_chain` |
| Drift test green (models and migrations agree) | `tests/integration/test_migration_drift.py::test_models_and_migrations_do_not_drift`; `::test_the_certificate_vocabularies_match_the_enums` |

Two design statements were **corrected by what 5.1 actually built** and are recorded above
rather than quietly left inconsistent: `certificates.status` is String(24) (String(16)
cannot hold `REVOCATION_PENDING`), and status derivation falls back to the *newest*
generation until a *current* one exists (§3.1). Everything else in §3.1/§3.2 that is
marked 5.1 is present in migration `c8d9e0f1a2b3`; everything marked 5.2 is absent from
it.

### 10.2 Test requirements (what "done" means per slice)

- **Contract tests** for each new op type and its params model (mirroring
  `backend/tests/unit/test_operation_registry.py`), including "a reserved/unknown
  type is a 422 and a raw insert is refused by the type CHECK".
- **Agent contract tests** (mirroring `backend/tests/test_agent_nginx_contract.py`) that
  load the real agent module and prove: the cert install validates paths against the
  closed shape, a fingerprint mismatch refuses, a foreign path is refused, and the
  removal bundle leaves other generations' directories untouched.
- **Redaction/leak tests** hitting every path named in §7.6 — operation params, the
  operation result via the API, the delivery responses, audit metadata, events, and the
  operation-history endpoint — asserting that **no certificate private key or chain**
  ever appears. These tests are the evidence for the §7.6 normative rule; they are not
  optional and are gated before 5.4.
- **Tenant-isolation tests** for every new endpoint (IDOR suite; multi-tenancy.md §7).
- **ACME/pebble integration** in CI, never against the production CA.
- **Drift/migration tests** (the project's `test_migration_drift.py` pattern): the
  migration and the models agree.
- **End-to-end** (later, in the Docker/Playwright suite): issue → deliver → install →
  apply → verified HTTPS endpoint on a real node, and the HTTP-stays-up property.

### 10.3 Decisions and known limitations

#### 10.3.1 Approved decisions (previously open)

| # | Decision | Consequence |
|---|---|---|
| D1 | **Centralized control-plane custody** of TLS private keys for v1, accepted **conditionally**. | Conditions C1–C6 in §6.6. Production 5.4 is blocked until they are met; non-production accepts the risk. Node-side keygen stays out of scope. |
| D2 | **ACME staging by default** for dev/tests/non-production; **production requires explicit configuration**; no silent fallback in either direction. | §5.4. A missing production config fails closed; a staging cert is labeled staging and never presented as production. |
| D3 | **Ownership loss → immediate suspension + automatic reconcile, then automated CA revocation** subject to a certificate-impact safeguard; shared multi-identifier certificates are replaced/split **before** revocation; CA revocation never blocks removal. | §9.3 Stages 1–5. |
| D4 | **Certificate role matrix (O3) resolved** per authorization.md §3, using the **current stored role name `Operator`** (no `Operator`→`DevOps` rename): Owner/Admin/Operator hold `certificate.read` + `certificate.manage`; Developer/Viewer hold `certificate.read`. Both org-scoped; reads metadata-only, never key material. | §4.1; authorization.md §2/§3. Registered with 5.1. |

#### 10.3.2 Known limitations (accepted, not blockers)

| # | Item | Status |
|---|---|---|
| L1 | Control plane holds all TLS private keys; a runtime compromise owns every certificate. | Accepted **conditionally** (D1, §1.5, §6.6); node-side keygen out of scope. |
| L2 | Per-org DEK does **not** bound a KEK/`ENCRYPTION_KEY` compromise or a runtime compromise. | Documented in §6.1; no v1 mitigation; must be stated in docs/UI (§6.6 C6). |
| L3 | Existing secret store is not migrated to the org DEK in Phase 5. | Deferred to a separate reviewed change (§6.4). |
| L4 | `dns_providers` has no separate permission codename in v1; managing it rides `certificate.manage`. | Recorded; revisit if TXT auto-publish for domain verification ships. |
| L5 | Per-org ACME account key (vs one platform account). | Chosen for rate-limit/revocation isolation; revisit at multi-org scale. |
| L6 | Redaction cannot recognize a bare JWT or embedded DSN password. | Inherited Phase 4.4 limitation; delivery never relies on redaction (§7.6 normative rule). |
| L7 | Delivery (5.4) must not ship before the leak-path tests for the paths it introduces exist. | Sequencing constraint, not a separate task. |
| L8 | Node-side key generation / CSR. | Out of scope for v1; the structural answer to D1's concentration. |

#### 10.3.3 Open items and what they block now

Phase 5.1 — the data model and read API only, **no key material, no CA, no delivery** —
**shipped 2026-10-12** (§1.1, §10.1.1). The table below is therefore about 5.2 and
later; each item is genuinely unresolved and is **not** invented away.

| # | Open item | Blocks what? |
|---|---|---|
| O1 | **KMS / secret-manager vendor for the KEK (C1).** **Closed 2026-10-12**: approved in §6.7 (Vault Transit first; cloud KMS adapters later behind the same interface; test providers never a production fallback; no plaintext KEK in code or DB; operation-scoped unwrap; provider-side rewrap). Operational custody is specified in §6.9. | **No longer blocks anything.** §3.7 step 1 and §10.5 are unblocked; the residual items are operator choices inside the approved direction (auto-unseal KMS vendor, transit key name, audit destination, break-glass holders — §6.8). |
| O2 | **Exact `acme`/`josepy` versions and pin policy**, and whether to use `acme`'s `ClientNetwork` or its higher-level message helpers. | **No** — needed at 5.3. |
| O4 | **`REVOCATION_FAILED` → operator action vs extended automatic retry budget.** The bounded-budget default is designed (§9.5); the exact budget/threshold is a tuning decision. | **No** — 5.6. |
| O5 | **Expiry-monitor thresholds** (warn/critical days) — defaults proposed (30/7) but org-configurability is undecided. | **No** — 5.6. |
| O6 | **Whether the multi-identifier split is automatic or operator-confirmed** when the replacement issuance itself needs DNS credentials for a still-owned zone. | **No** — 5.6; the safeguard (never revoke a still-serving shared cert) holds either way. |
| O7 | **CAA record handling** — honor/refuse at issuance. Not designed here. | **No** — 5.3/5.7 hardening. |

**Bottom line after 5.1 shipped:** **O3 is resolved (D4, §4.1)** and is implemented —
the two codenames are registered with the matrix Owner/Admin/Operator = read+manage,
Developer/Viewer = read, using the current stored role name, and the tests in §10.1.1
prove it. **O1 is the one item that gates a slice rather than a feature**: 5.2 step 1 is
the KEK provider, and it needs the K1 approval in §6.8 before it is written. O2 is
bounded to 5.3, O4–O7 to 5.6/5.7, and none of them changes the 5.1 schema that is now in
the database. No item on this list is a reason to write a placeholder key, a placeholder
provider row or a partially working issuance path.

### 10.4 Reserved-operation-type lists — one source of truth (required consolidation)

The repository currently enumerates "reserved / not-yet-shipped operation types" in
**five divergent places**, and they disagree (notably, node-agent-architecture.md's
note still lists `nginx.*` as reserved after it shipped):

| Location | Current statement | Divergence |
|---|---|---|
| `backend/app/models/enums.py` (`OperationType` docstring) | "`certificate.*` and `secret.env.apply` stay absent" | Authoritative enum; 8 shipped types |
| `backend/app/schemas/operation.py` (`OPERATION_SPECS`) | Registry; no reserved entries | Registry holds only shipped types |
| `docs/node-agent-architecture.md` §5.2 table + §5.4 note | Lists `secret.env.apply`, `certificate.install`/`certificate.remove` as reserved rows | §5.4's "`nginx.*` … reserved" is **stale**: `nginx.*` shipped in Phase 4 (corrected in this change) |
| `docs/certificate-management.md` §6 | `certificate.install` / `certificate.remove` | Duplicate list |
| `docs/secrets-architecture.md` §7 | `secret.env.apply` | Duplicate list |
| `docs/phase1-report.md` §4 | `secret.env.apply`, `certificate.*`, `nginx.*` | Historical report; `nginx.*` since shipped |
| `backend/tests/unit/test_operation_registry.py` (`RESERVED_LATER_PHASE_TYPES`) | `certificate.issue`, `certificate.renew`, `certificate.install`, `secret.env.apply` | Reserves `certificate.issue`/`.renew` — names the docs do **not** have |
| `backend/tests/integration/test_operations.py` (`RESERVED`) | `certificate.issue`, `certificate.install`, `certificate.renew`, `nginx.reload`, `secret.env.apply` | Adds `nginx.reload`; includes `.issue`/`.renew` |
| `backend/tests/integration/test_migration_drift.py` | `nginx.reload`, `certificate.install`, `secret.env.apply` | Different subset again |
| `backend/tests/unit/test_agent_v2.py` | `secret.env.apply`, `certificate.install`, `node.execute` | Includes `node.execute` (not a reserved type at all — it is a forbidden codename) |

**The lists disagree in substance, not just location:** the tests reserve
`certificate.issue` and `certificate.renew` as future *operation types*, while the
designs reserve `certificate.install`/`certificate.remove`. The Phase 5 design needs
only `certificate.install`/`certificate.remove` as node operations: **issuance and
renewal run control-plane-side as Celery tasks, never as node operations** (§5.5,
§9.1). `certificate.issue`/`certificate.renew` should therefore **not** be introduced
as operation types, and the tests that reserve them should be corrected to the design's
list when the consolidation lands.

**Recommendation (single source of truth):** the `OperationType` enum plus
`OPERATION_SPECS` in `backend/app/schemas/operation.py` is authoritative. Documentation
**and tests** must **reference** it and must not each re-enumerate shipped or reserved
types. A single "reserved names" list, if maintained at all, lives in one comment
beside the enum and is guarded by one registry contract test; the registry test already
fails if a type names an unknown codename or capability
(`backend/tests/unit/test_operation_registry.py`). The four test-local reserved tuples
in the table above collapse into that one list.

**Consolidation required before new certificate operation types are introduced** — not
in this change. Concretely: collapse the five lists above to a pointer at the enum +
registry, and add one assertion that no documented reserved name is also a shipped
type. **This task adds no operation type.**

### 10.5 Phase 5.2.1 — narrow implementation plan (KEK provider + organization DEK envelope)

**Scope.** Exactly two things: the `KEKProvider` seam with its first production adapter, and
the organization DEK envelope that uses it. **Out of scope, deliberately:** DNS-provider
credentials, ACME account storage, certificate material columns, issuance, and agent
delivery (each named in the last table below). No placeholder key, no placeholder provider
row, no partially working path — the module ships with nothing that *stores* a certificate
key, because no column exists to store one in.

**Schema plan, verified against the shipped tree** (checked 2026-10-12 at `307c5e1`):

| Check | Result |
|---|---|
| Current Alembic head | `c8d9e0f1a2b3` — **single head**, no branch points (`uv run alembic heads`) |
| 5.1 revision chain | `c8d9e0f1a2b3` revises `b7c8d9e0f1a2`; the 5.2.1 migration must set `down_revision = "c8d9e0f1a2b3"` |
| Do the 5.2.1 columns already exist? | **No.** `dek_ciphertext`, `dek_generation`, `dns_providers`, `acme_accounts`, `key_ciphertext` and `deke_id` appear in 5.1 only as prose stating their absence — no column, no table, no index |
| Does 5.2.1 conflict with 5.1's constraints? | No. It **alters `organizations`** only, and 5.1 touched `certificates`/`certificate_generations` |

#### 10.5.1 Migration (one, additive, `down_revision = c8d9e0f1a2b3`)

| Change | Detail |
|---|---|
| `organizations.dek_ciphertext` | `Text`, **nullable** — an organization has no DEK until its first Phase-5 write, and a nullable column here is honest rather than a placeholder value |
| `organizations.dek_generation` | `Integer`, **NOT NULL, default 0**, CHECK `dek_generation >= 0`. `0` means "no DEK yet"; the first generated DEK is generation `1`. A wrapped ciphertext with generation `0` is therefore contradictory, and a CHECK may enforce the pair: `(dek_ciphertext IS NULL) = (dek_generation = 0)` |
| Downgrade | Drops both columns. It **must fail loudly** rather than silently discard material that exists: if any row has `dek_ciphertext IS NOT NULL`, the downgrade refuses with a message naming the affected organizations (a downgrade that destroys the only copy of a wrapped DEK is not a routine operation) |
| Not in this migration | No `dns_providers`, no `acme_accounts`, no material columns, no guard CHECK, no RLS change (an existing tenant column on an existing RLS-governed table needs none) |

> **Superseded in 5.2.1.2 (§10.6, 2026-10-14).** The two column rows above are the plan as
> it stood at 5.2.1 and are kept as the record of it. The audit of that slice found the
> placement itself was the defect — `organizations` is RLS-exempt, so the envelope had no
> database-level tenant net — and the envelope now lives in the tenant table
> `organization_dek_envelopes`. Read §10.6 for the shipped schema; the nullable/generation
> semantics and the pair invariant are unchanged, only relocated (plus the missing
> `dek_generation >= 0` bound).

#### 10.5.2 Modules, interfaces and configuration

| Artifact | Contents |
|---|---|
| `app/services/kek/__init__.py` | The `KEKProvider` protocol, `EncryptionContext`, `WrappedKey`, `KEKProviderStatus`, `KEKError` (named: `KEK_UNAVAILABLE`, `KEK_UNAUTHORIZED`, `KEK_CONFIG_INVALID`), and the envelope codec for the self-describing stored value |
| `app/services/kek/vault_transit.py` | `VaultTransitKEKProvider` — AppRole login with token renewal, `wrap_dek` → `transit/encrypt`, `unwrap_dek` → `transit/decrypt` (with the `context` derived from `EncryptionContext`), `rewrap_dek` → `transit/rewrap`, `health` → a cheap key-metadata read. Built on the already-present `httpx`; **no new dependency** |
| `app/services/kek/deterministic.py` | `DeterministicKEKProvider` (provider name `test`) — fixed test root key, deterministic ciphertext, in-process only. Not importable into a production code path by configuration (below) |
| `app/services/kek/factory.py` | `build_kek_provider(settings) → KEKProvider`, the **only** construction site. Explicit selection, no detection, no fallback chain |
| `app/services/dek_envelope.py` | `org_dek(db, org_id, purpose)` context manager: read `dek_ciphertext`/`dek_generation`, unwrap through the provider, yield the Fernet key for the duration of **one operation**, drop it on exit (approved point 5). Lazily generates + wraps on first use; serializes concurrent first-use with a row-level lock so two requests cannot create two DEKs for one organization |
| `app/services/kek/rewrap.py` (or a function on the envelope) | `rewrap_org_deks(db, batch)`: the KEK-rotation path through `rewrap_dek`, resumable, per-row idempotent, **never** returning a DEK to its caller. An operator-invoked script/CLI entry, not a beat task in this slice |
| `app/core/config.py` | `kek_provider` (unset by default), `kek_vault_addr`, `kek_vault_namespace` (optional), `kek_vault_role_id`, `kek_vault_secret_id`, `kek_vault_transit_key`, `kek_vault_ca_bundle`, `kek_vault_timeout_seconds`. Validation: production **aborts** on unset/unknown/`test`; the `test` provider is accepted only outside production |
| `app/api/v1/health.py` (or the existing health surface) | Report provider name + reachability, distinguishing unreachable from unauthorized, so the §6.9 startup table is observable rather than theoretical |

**Interface decisions fixed here, so the adapter cannot drift:**

- The stored value is exactly `provider:key_id:key_version:base64(ciphertext)` — one `Text` column, self-describing, versioned by a leading format tag so a future change is parseable rather than guessed at. Adding a provider is not a migration.
- `EncryptionContext(org_id, purpose, dek_generation)` is bound as provider associated data wherever supported; the adapter **refuses** to operate if the provider cannot bind it (rather than silently dropping the binding).
- `unwrap_dek` is the only function that returns key material; it is called from the envelope context manager only. No module-level cache, no `lru_cache`, no module global — grep-able and asserted by a test.
- A provider error is raised as a `KEKError` with a named code; nothing downgrades it to a warning or retries it into another source.

#### 10.5.3 Tests (planned, in `backend/tests/`)

| Area | What is asserted |
|---|---|
| Envelope codec | Round-trip of the stored value; unknown format tag, missing fields and trailing garbage are refused with a named error rather than parsed optimistically |
| Deterministic provider | Deterministic ciphertext across runs (fixtures stay stable); implements the same interface; performs no network I/O |
| Configuration | Production + unset/unknown/`test` ⇒ startup abort (the same fail-fast test shape `ENCRYPTION_KEY` already has in `tests/unit/test_security.py`); non-production + `test` ⇒ allowed and reported |
| No-fallback property | With the provider configured to fail, the code path raises `KEK_UNAVAILABLE` — it never falls back to `ENCRYPTION_KEY`, never returns a default, and never caches a DEK across operations |
| Operation scope | Two sequential envelope operations on the same org unwrap twice (no cross-operation cache), and no plaintext DEK survives the context manager (assert by inspecting the object graph / provider call count) |
| Context binding | A ciphertext wrapped for org A is rejected when presented with org B's context; a generation mismatch is rejected |
| Migration | Upgrade adds both columns with the documented nullability/CHECK; the populated-instance downgrade refuses while wrapped DEKs exist and succeeds after they are cleared; single head preserved; model↔migration drift stays green |
| Tenancy | `dek_ciphertext` is not reachable through any API read model — asserted by the same response-allowlist style used for the certificate models, so the column cannot leak by default |
| Vault adapter (integration, non-production) | Against a real Vault transit instance in CI: login, wrap, unwrap, rewrap, key rotation observed via `key_version`, denied policy ⇒ `KEK_UNAUTHORIZED`. Runs only where Vault is available; the production key and CA directory are never contacted |

#### 10.5.4 What each later step adds (and where it stays out of scope)

| Step | Adds | Explicitly not in this plan |
|---|---|---|
| 5.2.2 | `dns_providers` table, its metadata-only API, credential storage under the org DEK, `verify_creds` + `zone_allowlist`; `acme_accounts`; `certificates.dns_provider_id` FK; generation material columns + `deke_id`; widened `state`; material guard CHECK | No issuance logic, no CA contact |
| 5.3 | The `acme`/`josepy` dependency behind an ACME-provider seam, the order/challenge/validate/finalize flow, key pair generation, encrypt-and-store, issuance task + backoff | No delivery, no activation |
| 5.4 | `certificate_deliveries`, the material endpoint, `certificate.install`/`certificate.remove` op types and agent handlers | No HTTPS activation |
| 5.5 | Route binding (`routes.certificate_id`, widened `scheme`), the TLS renderer block, HTTPS activation + probe | No renewal/revocation |
| 5.6 | Renewal sweep, expiry monitor, removal, revocation (CA axis + `REVOKED_LOCAL_ONLY`) | — |

**Exit condition for 5.2.1:** the migration is applied and reversible (with the refusal above),
the seam and envelope are covered by the tests in §10.5.3, a production configuration
cannot select a non-production provider, and the Adapter operates against Vault Transit in
CI. **No certificate has been issued, no key material exists, and no DNS or ACME record has
been created** when this slice is done — by construction, since none of those columns exist
yet.

### 10.6 Phase 5.2.1.2 — envelope isolation, rewrap safety, address hygiene (audit remediation)

**Scope.** Exactly the four findings of the independent security audit of 5.2.1
(`ba4de5e8e7b7e45e294dee55de4f38983ad885f6`). **Out of scope, deliberately:** DNS-provider
credentials, ACME accounts, certificate material, issuance and agent delivery — none of
them exist, and none of them are introduced here. This slice hardens the custody path that
5.2.1 built, before the first key it will hold exists.

| Finding | What was wrong | Fix |
|---|---|---|
| **F1** — the envelope sat outside every database-level tenant net | `dek_ciphertext`/`dek_generation` lived on `organizations`, a documented RLS-exempt table (it *is* the tenant). Any read path that could reach an organization row could read another tenant's wrapped DEK, and PostgreSQL would not have refused — confidentiality rested on the KEK provider alone | The envelope moved to `organization_dek_envelopes`: `org_id` NOT NULL with a `ON DELETE CASCADE` FK, `uq_organization_dek_envelopes_org_id` making "one authoritative envelope per organization" a schema guarantee, the same tenant + system policies as every other tenant table, and the explicit app-role grant (the tenancy migration's blanket `GRANT ... ON ALL TABLES` predates the table). Envelope reads and writes go through that table only; the RLS-exempt path no longer holds key material at all. Populated envelopes are copied before the source columns are dropped, and the migration raises if the counts disagree |
| **F2** — a concurrent or stale rewrap could overwrite a newer envelope | `rewrap_org_deks` updated the row by organization id alone, so a rewrap that read version *n* could land after one that read *n+1* and silently regress the stored envelope to an older, still-readable — and therefore *valid-looking* — value | The update is compare-and-set on the exact envelope value **and** generation read before the provider call (`... WHERE org_id = $1 AND dek_ciphertext = $old AND dek_generation = $gen`). A losing writer updates zero rows, reloads the authoritative state, and either re-attempts under a bounded retry budget or exits without writing. KEK-only rotation still delegates to the provider's rewrap, so no plaintext DEK enters the process, and the DEK generation is not incremented merely because the KEK version moved (a rewrap moves the *key version* carried inside the envelope) |
| **F3** — the documented generation bound was never created | 5.2.1 documented `dek_generation >= 0` and shipped only the pair invariant, so a negative generation was representable by any writer that bypassed the model | `ck_organization_dek_envelopes_dek_generation_non_negative` alongside the relocated pair CHECK, both declared in the model metadata so the drift check stays green. Valid: the initial state (`NULL` ciphertext, generation `0`) and a populated envelope (generation `≥ 1`); rejected: a negative generation, a ciphertext at generation `0`, a generation without ciphertext, and either half of any inconsistent pair |
| **F4** — a Vault address could carry HTTP credentials | `KEK_VAULT_ADDR=https://user:password@vault:8200` was accepted. Vault access here is AppRole, so those credentials are read by nothing — the HTTP client drops them from a base URL — while they sit in a compose file, a shell history and any startup output | Rejected in both places that can construct a Vault client: settings validation at startup and the adapter's own constructor. Only the authority component is inspected, so a path prefix (`https://vault.example:8200/team`) stays valid, and neither message quotes the address or its contents (settings errors also set `hide_input_in_errors`, so pydantic does not echo the rejected input). https-only and mandatory TLS verification are unchanged |

**Access model after this slice.** One row per organization, in a tenant table, behind two
RLS policies, reachable by the application role with the four DML verbs and *not* as owner
(`NOSUPERUSER NOBYPASSRLS`). Tenant scope reads and writes only its own envelope; the
system scope (the sentinel GUC) is the sweep/administrative path and is unchanged from every
other tenant table. The RLS-exempt `organizations` table holds no key material. The
compare-and-set predicate is the only write path, so "the value I wrote is the value I
read" is enforced by the database rather than by the ordering of two application calls.

**Verification.** `backend/tests/integration/test_migration_phase5212.py` (the move, the
data preservation, the constraint pair, the RLS/grant shape, the constraint names, and the
downgrade that restores or stops with the key material still in place),
`backend/tests/integration/test_org_dek_envelope.py` (scoped access, cross-tenant refusal,
concurrent rewrap, stale snapshot, duplicate attempt, provider failure between rewrap and
update), `backend/tests/integration/test_tenant_isolation.py` (raw SQL under the runtime
role), and `backend/tests/unit/test_kek_selection.py` /
`backend/tests/unit/test_kek_vault_transit.py` (the address rule, at both construction
sites).

**Not in this slice, and unchanged by it:** no certificate material column, no
dns_providers credential, no ACME account key, no issuance, no delivery. 5.2.2 remains the
next step, and this slice is the precondition for it rather than a part of it.

---

## Appendix A — Decisions resolved here (that certificate-management.md left open)

| certificate-management.md open question | Decision |
|---|---|
| ACME client library vs in-repo | **Library** (`acme` + `josepy`) behind an `AcmeProvider` seam (§5.1) |
| Per-org vs single platform ACME account | **Per-org per-directory** account (§5.4) |
| Wildcard-vs-exact matching at bind time | Exact CN/SAN, else wildcard one label deep; error `CERTIFICATE_DOES_NOT_COVER_HOSTNAME` (§4.4) |
| Renewal window vs shorter-lived certs / ARI | Fixed 30-day sweep in v1; the **generation** model leaves room for an ARI-driven second trigger without a schema change (§3.2, §9.1) |
| Delivery pull-response persistence | Resolved by **not** persisting: a dedicated material endpoint assembled at read time, `no-store`, bounded recovery (§7) |
| DNS credentials home ("Integration"/"Connection") | **Dedicated `dns_providers` table** (§3.4, §5.3) |

### Approved in the Phase 5.0 finalization (2026-10-12)

| Decision | Where |
|---|---|
| D1 — Centralized control-plane custody accepted **conditionally** (KEK blast radius, preferred external KMS, access restrictions, rotation, backup recovery, production-readiness C1–C6) | §1.5, §6.1, §6.3, §6.5, §6.6, §10.3.1 |
| D2 — ACME **staging by default**; production explicit; **no silent fallback** either direction | §5.4 |
| D3 — Ownership loss → immediate suspension + automatic reconcile, then **automated CA revocation** with an impact safeguard; shared multi-identifier certs are **replaced/split before revocation**; revocation **never blocks removal** | §9.3, §9.5 |

These supersede the corresponding “needs human approval” items in earlier revisions of
this document. The remaining open items for Phase 5.1 and beyond are listed in §10.3.3.

### Approved and recorded in the Phase 5.1 closeout (2026-10-12)

| Decision | Where |
|---|---|
| Phase 5.1 implementation status — what shipped, what did not, and the evidence for each acceptance criterion | §1.1, §10.1, §10.1.1 |
| KEK provider direction (C1): Vault Transit as the self-hosted default, the deployment cloud's managed KMS as the alternative, one provider interface, a deterministic test provider that production cannot select — with the vendor/custody/audit/caching approvals still outstanding | §6.7, §6.8 |
| Intra-5.2 implementation order, with the KEK provider first, and the explicit statement of what may not be built before the KMS choice | §3.7 |
| `certificates.status` widened String(16) → String(24) and status derived from the newest generation until a current one exists | §3.1 |

### Approved in the Phase 5.2 key-management decision gate (2026-10-12)

| Decision | Where |
|---|---|
| The six-point KEK direction: Vault Transit as the first production `KEKProvider`; cloud KMS as possible future adapters behind the same interface, **not** built in v1 without a concrete deployment requirement; test/dev providers explicitly selected and never production fallbacks; the root KEK never in application code or the database in plaintext; **operation-scoped DEK unwrap with no long-lived plaintext-DEK LRU until measurements justify one**; rewrap delegated to the provider with no plaintext DEK returned during KEK-only rotation | §6.7 |
| Vault root/unseal custody: **auto-unseal through a cloud KMS**, with break-glass material stored separately from DB backups and two-person access | §6.8 K2, §6.9 |
| Vault application authentication: **AppRole**, one policy per environment scoped to a single transit key, TLS with a verified CA, no root token on an application host | §6.9 |
| Operational custody requirements written down as requirements rather than intentions: storage protection, availability, recovery, backup/restore drills, audit retention ≥ 13 months with quarterly access review, DEK generation/wrapping/rotation/recovery and key-loss consequences, startup behaviour per misconfiguration | §6.9 |
| The narrow 5.2.1 implementation plan (migration, modules, interfaces, configuration, tests, later steps) with the schema plan verified against the shipped 5.1 migration and the single Alembic head | §10.5 |

These settle the decision gate. They authorize **5.2.1 only** — the provider adapter and the
organization DEK envelope. They do not authorize DNS-provider credentials, ACME account
storage, certificate material columns, issuance or agent delivery, and no key, credential
or provider row is created by recording them.

No application behavior is changed by these notes: they record what 5.1 built, and set
the order and the gates for 5.2. No dependency, adapter, credential or configuration key
is added — the KEK vendor is explicitly still an approval (§6.8, K1).
