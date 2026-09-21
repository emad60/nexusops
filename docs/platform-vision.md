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
> Linux machine with a lightweight outbound-only agent, organize machines/projects/
> domains under organizations, and do the Nginx+Certbot+Docker CLI work you do today
> over SSH from one coherent, permissioned, audited platform — without the SSH part.

The product boundary — "simple for the customer, sophisticated underneath":

| The customer sees | NexusOps handles underneath |
|---|---|
| **Nodes** — any Linux machine in ~60 seconds | enrollment, agent identity, capabilities, heartbeats, upgrades |
| **Projects** — an app or system as the unit of work | environment config layering, secret refs, deploy orchestration |
| **Deployments** — click Deploy, watch steps | build/run orchestration on the node, health checks, rollback |
| **Domains** — add api.example.com → application | DNS verification, nginx rendering, TLS, redirects |
| **HTTPS** — automatic issuance + renewal after a one-time DNS-provider integration | ACME issuance/renewal (DNS-01), key protection, expiry monitoring |
| **Monitoring** — auto-attached to everything you add; alert delivery needs one configured channel | polymorphic monitors, incidents, notifications |
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

A September 2026 competitive review (Coolify, Portainer, Dokploy, Dokku, CapRover,
EasyPanel, Kamal, Komodo, Sliplane — facts with source URLs, no exaggeration in either
direction) found:

- **Coolify / Dokploy / Dokku / CapRover / Kamal** — the turnkey PaaS class — all reach
  servers over **SSH**. Coolify v4 stores a passphrase-less private key per server and
  needs port 22 open; Dokploy and CapRover require root SSH keys; Dokku and Kamal are
  SSH throughout. Coolify's shipped multi-server model is "same app, N servers" with
  documented limitations (same-arch nodes, external registry required, no compose /
  persistent storage / traffic distribution on additional servers). Its v5 redesign
  (`coold`, a Rust agent dialing outbound over gRPC, SSH demoted to bootstrap) adopts
  exactly this outbound-agent architecture but is **announced, not shipped** — v5 date
  TBD as of September 2026.
- **Portainer** is a container-management layer, not a PaaS: no per-app domains, no
  certificate issuance, no git→image builds. Its Edge Agent has done outbound-only,
  no-inbound-ports node onboarding for years (load-tested at 15,000 environments);
  tunnel configuration and fleet conveniences are Business-edition-gated, and CE is
  deliberately missing RBAC/audit/backup destinations.
- **Komodo** (free, GPL-3.0) ships an outbound-only, NAT-friendly agent since v2.0.0
  (March 2026) with the most granular per-resource permissions in the space — but no
  built-in domain/TLS/reverse-proxy management.
- **Cloud platforms** (Vercel/Render/Fly): great DX, but cloud-only — home servers,
  RPis, and dedicated boxes are second-class.

The wedge, stated precisely so it survives scrutiny:

> **The first turnkey self-hosted PaaS — deploys + domains + TLS + monitoring in one
> product — where every server onboards via an outbound-only agent: zero SSH, zero
> inbound ports, NAT-friendly.**

Scope notes that keep the claim honest:

- **"First" scopes to the turnkey PaaS class.** Komodo v2 and Portainer's Edge Agent
  are real precedents for the transport pattern in adjacent categories (deploy
  automation and container management respectively) — "nobody does outbound agents"
  would be false and is not the claim. The defensible moat is the **bundle**: agent
  transport + turnkey domains/TLS + multi-tenant RBAC + monitoring + secrets/audit in
  one product. Coolify v5's `coold` validates the architecture; when it ships, the
  transport alone stops differentiating, and the bundle + permissions carry positioning.
- **The transport is also the trust story:** no stored SSH keys anywhere, no port-22
  requirement, no root login for the control plane, and root-equivalent docker.sock
  access bounded by a compile-time op allowlist ([node-agent-architecture.md](node-agent-architecture.md)).
- **ARM64 agent + installer from day one** is table stakes, not a differentiator
  (Coolify officially supports Pi Zero 2 W–5; Dokploy builds amd64-only images and
  cross-arch deploys fail — support ARM64 without overclaiming).

The smallest coherent first sellable version (the "instantly valuable" demo):

> Accept an operator-issued invite → install the agent on your box → node appears with
> live stats → create a project → deploy an image → add `api.example.com` → HTTPS
> issuance + auto-renewal → uptime + TLS-expiry monitoring auto-attached → invite a
> teammate with Viewer role.

For the first version, onboarding is via **operator-issued invites to pre-created
orgs** — self-serve signup is a product decision deliberately deferred, not an
implementation detail (see [multi-tenancy.md](multi-tenancy.md) §2.1).

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

**Prerequisites the user brings — NexusOps and the agent cannot create these.** The
agent, by design, cannot buy domains, create DNS records, configure routers or
firewalls, or install packages:

- A domain whose DNS you control — **v1 certificates require the DNS hosted on
  Cloudflare** plus a scoped API token (other providers are later phases).
- An **A/AAAA record** pointing your hostname at the node's public IP.
- **Public reachability**: a VPS with a public IP, or a home server with a working
  port-forward of 80/443. **CGNAT nodes cannot serve customer traffic in v1** — there
  is no tunnel, by design (§2.1). Certificate issuance still works there (DNS-01 needs
  no inbound connectivity at issuance time); serving does not.
- **nginx installed on the node, ports 80/443 free** — routing takes exclusive use;
  the routing pre-flight refuses nodes that fail it with a named error.
- A **public container image** (v1 deploys pull from public registries only).

1. **Join** — accept an operator-issued invite; the first user of a fresh deployment
   bootstraps as owner of the first organization ([multi-tenancy.md](multi-tenancy.md) §2.1).
2. **Install the agent** — one command with a per-node enrollment token (env-delivered,
   not argv). Node appears in ~60 seconds: OS, arch, CPU/mem/disk, capabilities
   (Docker ✓ Nginx ✓ Systemd ✓ — GPU is not a v1 capability), live stats.
3. **Create a project** → environment (staging/production) → **application** (image + config).
4. **Deploy** — watch steps stream live; the health check gates routing.
5. **Add domain** `api.example.com` → verify via DNS TXT → point an A/AAAA record →
   route → upstream (node:container:port). Route creation is refused with a named error
   if the node fails the routing pre-flight.
6. **HTTPS**: DNS-01 issuance + auto-renewal, after the one-time Cloudflare-token
   integration. Issuance works from any network; serving requires the reachability
   prerequisite above.
7. **Monitoring auto-attaches**: uptime (probed from the control plane — see the
   vantage-point note in domain-routing.md §13) + TLS expiry per domain, container
   health, node heartbeat. **Add a notification channel** (and control-plane SMTP for
   email) so alerts actually reach someone.
8. **Invite the team**; roles like DevOps (can deploy staging, not production) come from
   org roles + resource grants.
9. **Everything audited**; events feed; notification channels fire on incidents.

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

- **Time-to-value < 10 minutes** from agent install to a deployed, HTTPS-served,
  monitored application — **given the §4 prerequisite checklist**. Honest by path:
  - *VPS with public IP, Cloudflare DNS, nginx preinstalled, public image:* the
    10-minute claim is credible after prerequisites are in hand.
  - *Home server behind NAT:* everything above plus a user-configured port-forward of
    80/443 (and DDNS if the IP is dynamic); certificate issuance works regardless;
    CGNAT = unsupported, labeled as such.
  - *First-timer buying a domain and setting up Cloudflare mid-journey:* expect an
    hour+ — that setup is outside NexusOps and never claimed otherwise.
- **No SSH for the happy path given the pre-flight passes.** The agent cannot install
  packages, edit DNS, or configure routers; the routing pre-flight surfaces what it
  finds (nginx missing, 80/443 busy) as named errors, and resolving those is
  user-side, by design.
- **Zero cross-tenant access** — proven by the CI IDOR suite extended with write-path,
  identity-map, Core-statement, and raw-SQL RLS probes ([multi-tenancy.md](multi-tenancy.md) §7).
- Agent install works on Debian/Ubuntu, Fedora, Arch, Alpine, **ARM64** (agent is
  stdlib-only; ARM64 is table stakes per the competitive review).
- Every destructive/remote operation is permissioned, audited, and reversible where
  possible.
- The production contabo instance migrates in place through every phase with zero
  data loss (the migration strategy is proven on it first).
