# Platform Vision — NexusOps

**Status:** Proposal for review — not yet approved for implementation.
**Date:** 2026-09-20
**Reads best after:** [domain-model.md](domain-model.md) · [multi-tenancy.md](multi-tenancy.md) · [authorization.md](authorization.md)

---

## 1. Where NexusOps is today

NexusOps is a working, deployed product: a FastAPI + PostgreSQL + Celery/Redis control
plane with a React dashboard and a stdlib-Python agent. The dashboards' monitoring,
container inventory, metrics, logs, events, audit, secrets, and team access control are
**real** and running in production on a shared server, watching itself (server
"contabo" enrolled via its own agent).

Three things are deliberately simulated today, and honesty about them anchors this
proposal:

1. **Deployments are a staged simulation.** `SimulatedDeploymentRunner` renders
   realistic docker-style logs for 7 steps (pull → checkout → build → stop → start →
   health check → finalize) but performs no real work (`backend/app/providers/deployment_runner.py:107`).
2. `sim://` monitor transports and the `docker_sim` provider exist for demo/CI (SIMULATION_MODE).
3. There is **no domains/certificates/reverse-proxy subsystem at all** — nothing to
   simulate; it must be built.

Everything else — auth, sessions with refresh rotation + reuse detection, the
permission registry, agents reporting real heartbeats/container stats/logs over
dormant-but-real Redis pub/sub + WS fan-out, Fernet-encrypted secrets with deploy-time
resolution, append-only audit, incident/notification pipeline — is real, tested
(337 unit + 54 integration backend tests, 109 frontend tests, a 10-step Playwright
journey), and deployed.

## 2. The direction

> NexusOps becomes a **control plane for self-hosted infrastructure**: connect any
> Linux machine with a lightweight agent, organize machines/projects/domains under
> organizations, and make SSH+Nginx+Certbot+Docker CLI work possible from one
> coherent, permissioned, audited platform.

The product boundary — "simple for the customer, sophisticated underneath":

| The customer sees | NexusOps handles underneath |
|---|---|
| **Nodes** — any Linux machine in ~60 seconds | enrollment, agent identity, capabilities, heartbeats, upgrades |
| **Projects** — an app or system as the unit of work | environment config layering, secret refs, deploy orchestration |
| **Deployments** — click Deploy, watch steps | build/run orchestration on the node, health checks, rollback |
| **Domains** — add api.example.com → service | DNS verification, nginx rendering, TLS, redirects |
| **HTTPS** — automatic | ACME issuance/renewal (DNS-01), key protection, expiry monitoring |
| **Monitoring** — automatic for everything you add | polymorphic monitors, incidents, notifications |
| **Team** — invite, roles, least privilege | RBAC, grants, audit of every mutation |
| **Backups** — schedule and forget | policies, destinations, encryption, verification, restore |

## 2.1 What we are NOT building

Explicitly out of scope, to protect the boundary:

- **Not Kubernetes.** Docker(+compose) on single machines is the supported runtime.
- **Not CI.** Deployments trigger from the platform or API; build orchestration is
  minimal (docker build on the node), not a pipeline engine.
- **Not a log platform at scale.** Bounded retention, tail/follow of containers; not
  ELK. (Long-term: ship-to-object-storage export.)
- **Not arbitrary remote shell.** The agent exposes a **fixed allowlist** of operation
  types; never a tunnel. (See [node-agent-architecture.md](node-agent-architecture.md).)
- **Not a rewrite.** The existing codebase is the foundation — see
  [product-roadmap.md](product-roadmap.md) for the migration strategy.

## 2.2 The wedge (differentiation)

Existing tools cluster at extremes:

- **Single-server PaaS** (Coolify, Dokploy, Dokku): easy deploys, but one server, weak
  teams/multi-tenancy, no cross-node view.
- **Container dashboards** (Portainer): container ops, no projects/deployments/domains.
- **Cloud-native** (Vercel/Render/Fly): great DX, but cloud-only — home servers, RPis,
  and dedicated boxes are second-class or unsupported.

The wedge: **multi-node + multi-tenant + self-hostable control plane + agent-based**.
One place where a person with three VPSes, a Raspberry Pi and a home server — or a
team of five — runs containers, gets HTTPS automatically, and shares access safely.

The smallest coherent first sellable version (the "instantly valuable" demo):

> Sign up → create org → install agent on your box → node appears with live stats →
> create a project → deploy an image → add `api.example.com` → HTTPS works →
> uptime + TLS-expiry monitoring on by default → invite a teammate with Viewer role.

## 3. Guiding principles

1. **Simple surface, sophisticated underneath.** Customer-visible concepts: Nodes,
   Projects, Domains, Deployments, Monitoring, Backups, Team. Complexity lives in
   providers, operations, and the agent protocol.
2. **Pull, not push, toward the agent; allowlist, not tunnel.** Agents fetch desired
   state and report results. Remote operations are explicit objects with permissions,
   audit, and timeouts. No raw command execution.
3. **Honesty in the product.** Simulated capabilities are labeled in the UI; the
   roadmap distinguishes "real today" vs "planned". (The current `-broken` demo hook
   and sim runner stay — as explicitly-labeled demo tooling.)
4. **One permission registry.** Every capability is a codename in
   `backend/app/core/permissions.py`; no scattered role checks.
5. **Tenancy at the data layer, not sprinkled checks.** org_id on every tenant table +
   a session-scoped query guard; direct-ID lookups go through scoped helpers.
6. **Providers over couplings.** Docker, nginx, ACME, DNS, S3, git, registries are
   provider interfaces with a first implementation each — never hard-coded vendors.
7. **The agent is privileged, so it is constrained.** Whitelisted ops only, versioned
   protocol, audit on the control plane, capability-based dispatch (docker ops only
   dispatched to nodes reporting docker capability).
8. **Audit everything that touches customer infrastructure.** Every mutation emits an
   append-only audit row: actor, org, action, resource, IP, request id, result.
9. **Billing-ready, not billing-driven.** Org-scoped metering counters from day one;
   plans enforcement later.
10. **Migration over rewrite.** Every phase ships value; the production instance
    (contabo) upgrades in place through every phase.

## 4. Customer journey (target)

1. Sign up → create organization (or accept an invite).
2. Install the agent (one curl-pipe-bash command with an org-scoped enrollment token).
3. Node appears in seconds — OS, arch, CPU/mem/disk, **capabilities** (Docker ✓ Nginx ✓
   Systemd ✓ GPU ✓), live stats.
4. Create a project → environment (staging/production) → service (image + config).
5. Deploy — watch steps stream live; health check gates routing.
6. Add domain `api.example.com` → verify via DNS → route → upstream (node:container:port).
7. HTTPS on by default: DNS-01 issuance, auto-renewal, expiry monitored.
8. Monitoring auto-attaches: uptime + TLS expiry per domain, container health, node
   heartbeat.
9. Invite the team; roles like DevOps (can deploy staging, not production) come from
   org roles + resource grants.
10. Everything audited; events feed; notification channels on incidents.

## 5. Control plane / data plane boundary

```
┌─────────────────────────── CONTROL PLANE (this repo) ───────────────────────────┐
│  api (FastAPI)  worker+beat (Celery)  postgres  redis  edge (dashboard only)     │
│  owns: orgs, projects, nodes, domains, routes, certs, secrets, audit, billing    │
└───────────────┬─────────────────────────────────────────────┬───────────────────┘
        auth'd HTTPS (agents, SPA)                    Redis pub/sub / op queue
┌───────────────┴───────────────┐                 ┌─────────────┴───────────────────┐
│  DATA PLANE (customer nodes)  │                 │  DATA PLANE (customer nodes)    │
│  agent (systemd, stdlib py)   │                 │  agent (same)                   │
│  docker (+compose optional)   │ customer-owned  │  nginx (agent-managed)          │ packages
│  apps/containers              │ machines        │  apps/containers                │
└───────────────────────────────┴─────────────────┴─────────────────────────────────┘
```

- The control plane **never sits in the customer traffic path**. Customer HTTP(S)
  traffic terminates on the customer's node nginx (agent-managed).
- The control plane never trusts a node: agent tokens are per-node, scoped to that
  node's org, and every agent call is authenticated+audited. A compromised node
  cannot read other nodes' operations, other orgs' data, or secrets it doesn't need
  (secret delivery is per-route minimization — see platform-security-model.md).
- The dashboard edge only serves the dashboard; it is *not* the customer proxy.

## 5.1 Architecture overview (target)

```
                    ┌─────────────────────────────────────────────┐
                    │                 SPA (dashboard)             │
                    │  org switcher · nodes · projects · domains  │
                    └────────────────────┬────────────────────────┘
                             REST + WS │ (JWT / API key, active-org header)
                    ┌──────────────────┴──────────────────────────┐
                    │              API (FastAPI)                  │
                    │  tenant guard (org-scoped sessions)         │
                    │  permission deps (require_permission)       │
                    │  routers → services → models (org-scoped)   routers
                    └───┬──────────┬──────────┬──────────┬────────┘
                        │          │          │          │
             ┌──────────┴──┐  ┌────┴─────┐  ┌─┴────────┐ ┌┴───────────────┐
             │ PostgreSQL  │  │  Redis   │  │ Providers │ │ Celery worker  │
             │ org-scoped  │  │ pub/sub, │  │ docker /  │ │ sweeps, checks,│
             │ rows        │  │ op queue │  │ nginx /   │ │ renewal, ops   │
             └─────────────┘  └────┬─────┘  │ acme/dns  │ └───────┬────────┘
                                   │        └───────────┘         │
                                   │ ops / events / logs          │
                    ┌──────────────┴──────────────────────────────┴────────┐
                    │   AGENTS on customer nodes (systemd, stdlib python)  │
                    │   facts+capabilities · heartbeats · container ops    │
                    │   nginx render/apply · log tailing · op executor     │
                    └──────────────────────────────────────────────────────┘
```

## 6. Success criteria for v1 (first sellable version)

- **Time-to-value < 10 minutes** from signup to a deployed, HTTPS-served, monitored
  service on your own hardware — no SSH required for the happy path.
- **Zero cross-tenant access** — proven by a CI IDOR suite (see platform-security-model.md).
- Agent install works on Debian/Ubuntu, Fedora, Arch, Alpine (agent is stdlib-only).
- Every destructive/remote operation is permissioned, audited, and reversible where
  possible.
- The production contabo instance migrates in place through every phase with zero
  data loss (the migration strategy is proven on it first).
