# NexusOps Security Guide

How NexusOps protects credentials, tenants, and infrastructure — what is enforced in
code, what was verified by the security audit (2026-09), and which limits remain.
Every control named here points at the module that implements it.

## Threat model in one paragraph

NexusOps holds the keys to infrastructure: user credentials, agent enrollment tokens,
deployment secrets, Docker endpoints, and notification-channel credentials. The
adversaries considered are (1) an internet attacker probing the edge, (2) a malicious
or compromised *agent* host, (3) a curious *operator* inside the platform who should
see less than an owner, (4) a leaked API key or token, and (5) SSRF pivoting through
platform features that fetch user-supplied URLs. Out of scope: host-level compromise
of the server running the compose stack, and physical access.

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

Roles are `Owner`, `Admin`, `Operator`, `Viewer`, mapped to wildcard permission
strings in `backend/app/core/permissions.py`. Every route declares the codename it
requires; `has_permission` evaluates wildcard matches plus the API-key intersection
above. Ownership boundaries (e.g. non-owners cannot read other tenants' resources)
are enforced in the service layer queries, not in the frontend.

## Transport and headers

- Single nginx edge terminates traffic (`nginx/default.conf.template`): `server_tokens off`, HSTS emitted in production, `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, a strict referrer policy, and a restrictive CSP for the SPA
  (`default-src 'self'; script-src 'self'; …; frame-ancestors 'none'; base-uri 'none'; form-action 'self'`).
  The identical header set is also applied by `SecurityHeadersMiddleware(is_production=…)` so a deployment without the edge is still hardened — `backend/app/middleware/security_headers.py`.
- API documentation (`/api/docs`, `openapi.json`) is disabled when `ENVIRONMENT=production` (`backend/app/main.py`).
- Internally, services communicate on a private compose network; only the edge publishes a host port.

## Secrets handling

- **Never returned after creation.** Agent enrollment tokens, API keys and notification-channel credentials are shown once in the UI with an explicit "stored only as a hash" notice; only a salted hash is persisted.
- `digest_of` (`backend/app/core/security.py`) renders a short, server-keyed HMAC digest for change-detection UI — a leaked digest is useless without the app secret, unlike a plain SHA-256.
- Secret *values* never appear in logs, audit records, or API responses; the redaction layer (`backend/app/core/redaction.py`) scrubs configured keys from structured payloads before they are persisted or logged.
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

`backend/app/core/rate_limit.py` implements token buckets in Redis. The
auth-sensitive limiters **fail closed** (Redis outage ⇒ requests rejected, not
allowed through): login 10/min/IP, register 5 per 5 min/IP, refresh 30/min/IP.
General API traffic fails open for availability, as documented in the module.

## Audit log

Every mutating request writes an append-only audit row (`backend/app/services/audit_service.py`)
with actor, action codename, target, request id, and redacted metadata. The API for
reading audit entries is read-only; there is no update or delete path.

## The agent (least privilege by construction)

`agent/nexusops_agent.py` uses only the Python standard library, authenticates with a
per-server enrollment token, and executes **no arbitrary commands** — its capabilities
are heartbeat metrics, container inventory, and log tailing of containers it can see.
It refuses cleartext `http://` transport unless `--allow-insecure-transport` is passed
explicitly (documented for lab use; TLS terminates at the edge in real deployments).
`agent/install.sh` writes the token file with `umask 077` semantics and `chmod 600`
*before* the secret is written into it.

## Production hardening checklist

1. Generate real secrets: `./scripts/generate_secrets.sh` (writes `.env`; refuses overwrite).
2. Set `ENVIRONMENT=production` — enables HSTS, disables OpenAPI/docs, switches cookie/transport flags.
3. Do not seed: `make seed` requires explicit `NEXUSOPS_ALLOW_SEED=1` and is meant for demo stacks. Seeded demo credentials (documented in the README) must never exist in production.
4. Keep `SIMULATION_MODE=false` — the badge in the UI must be off so operators know they are looking at live data.
5. Terminate TLS in front of the edge (the compose file exposes plain HTTP on `:8080` for lab use).
6. Rotate: refresh tokens rotate automatically; rotate API keys and agent tokens from their settings pages (issuing a new agent token invalidates the old one immediately).

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
- Rate limiting is per-IP at the application layer; a reverse proxy must forward real client IPs (`X-Forwarded-For` handling in `backend/app/middleware/`).
- Notification-channel and secret values are masked but the database stores them encrypted-at-rest only via disk-level encryption of the host volume; application-level envelope encryption is future work.
- The agent trusts the server for its configuration (poll interval, log tail limits); a compromised server can direct an agent to read container logs of anything visible to its Docker socket — by design, but worth knowing.
