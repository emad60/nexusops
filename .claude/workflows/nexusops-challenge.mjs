export const meta = {
  name: 'nexusops-challenge-review',
  description: 'Adversarial challenge pass: competitor facts + hostile doc/code review of the platform proposal',
  phases: [
    { title: 'Challenge', detail: '4 competitor researchers + 5 hostile reviewers' },
  ],
}

const SCHEMA = {
  type: 'object',
  required: ['area', 'key_facts', 'issues', 'recommendations'],
  properties: {
    area: { type: 'string' },
    key_facts: { type: 'array', maxItems: 28, items: { type: 'string' } },
    issues: { type: 'array', maxItems: 15, items: {
      type: 'object',
      required: ['severity', 'doc', 'problem', 'fix'],
      properties: {
        severity: { type: 'string', enum: ['blocker', 'major', 'minor'] },
        doc: { type: 'string' },
        section: { type: 'string' },
        problem: { type: 'string' },
        fix: { type: 'string' },
      },
    } },
    recommendations: { type: 'array', maxItems: 12, items: { type: 'string' } },
    sources: { type: 'array', maxItems: 25, items: { type: 'string' } },
  },
}

const RESEARCH_COMMON = [
  'You are researching a competitor for an HONEST competitive analysis of NexusOps, a',
  'self-hosted infrastructure platform (FastAPI control plane + agent) being designed as:',
  'multi-tenant orgs/projects, agent-based nodes (outbound HTTPS, no SSH), docker containers,',
  'projects/environments, image deploys (git-build later), domains+nginx+TLS, monitoring,',
  'RBAC, secrets, audit. Current date: September 2026. Use WebSearch/WebFetch aggressively.',
  '',
  'RULES:',
  '- FACTS ONLY, each with a source URL. Check official docs, changelog/release notes, GitHub.',
  '- Where a capability is PARTIAL or PAID-ONLY, say exactly that. No exaggeration in either',
  '  direction - if the competitor does something well, say so plainly.',
  '- Mark anything you could not verify as UNVERIFIED.',
  '- Cover these dimensions: multiple servers; teams; roles/permissions granularity; deployments',
  '  (git? image? compose?); docker management; domains; reverse proxy; TLS/ certificates;',
  '  monitoring; backups; public API; self-hosting; hosted/cloud offering + price; agent vs SSH',
  '  architecture; ARM/Raspberry Pi support.',
].join('\n')

const CHALLENGE_COMMON = [
  'You are a hostile reviewer for the NexusOps platform proposal (docs in /home/emad/projects/nexusops/docs).',
  'The proposal: multi-tenant orgs, session-guard tenancy, agent-pull operations, whitelisted op types,',
  'DNS-01-first certificates, image-based deploys first. Read the spine docs (platform-vision.md,',
  'domain-model.md, multi-tenancy.md, authorization.md, product-roadmap.md) plus the docs named in',
  'your task. Verify code claims in the repo (backend/, agent/, frontend/) - orient with:',
  '$(cat graphify-out/.graphify_python) -m graphify query "<question>" --budget 1200',
  '',
  'HARD RULE: you may NOT propose new features or expansions. Every recommendation must make the',
  'product CLEARER, SAFER, MORE FOCUSED, EASIER TO USE, or EASIER TO TRUST - remove, constrain,',
  'honestly label, or simplify. Cutting scope is always an acceptable recommendation.',
  'Report issues with severity / doc / section / problem / concrete fix. Facts need path:line or doc-section evidence.',
].join('\n')

const TASKS = [
  {
    key: 'coolify',
    prompt: RESEARCH_COMMON + '\n\nSUBJECT: Coolify (coolify.io, docs.coolify.io, github.com/coollabsio/coolify).\n' + [
      'Specifically determine: multi-server support mechanics (SSH? agent? since when), team/role',
      'granularity (owner/admin/member? finer RBAC?), deployment sources (git, dockerfile, compose,',
      'image, preview deployments), domains/TLS mechanics (integrated proxy? HTTP-01? wildcard via',
      'DNS API?), monitoring (Sentinel? server metrics?), backups (S3? scheduled? what scope), API',
      'surface, Coolify Cloud hosted offering + pricing, license terms (the 2024 license changes -',
      'current state), ARM support, and how a NEW server is onboarded (exact steps: SSH keys? ports?).',
      'Also: what happened with the Coolify agent if anything was announced.',
    ].join('\n'),
  },
  {
    key: 'portainer',
    prompt: RESEARCH_COMMON + '\n\nSUBJECT: Portainer (portainer.io) - CE vs Business Edition.\n' + [
      'Specifically determine: what RBAC/teams features are CE vs paid BE, Edge Agent architecture',
      '(polling vs tunnel, does it work behind NAT without inbound ports), multi-server (Edge groups),',
      'what Portainer does NOT do (git-to-build deploys? domains? certificates? app-level deploys?),',
      'monitoring scope, backup features CE vs BE, API, hosted offering existence, pricing tiers,',
      'license (CE Zlib? BE commercial), ARM support, and honest assessment: is Portainer a PaaS or',
      'a container dashboard?',
    ].join('\n'),
  },
  {
    key: 'dokploy-others',
    prompt: RESEARCH_COMMON + '\n\nSUBJECTS: Dokploy (primary), plus brief: Dokku, CapRover, EasyPanel, Kamal.\n' + [
      'For Dokploy specifically: multi-server mechanics (SSH), teams/roles, deployment sources,',
      'domains/TLS (Traefik? HTTP-01? DNS challenge?), monitoring/backups, API, hosted offering',
      '(Dokploy Cloud?) + pricing, license, ARM, maturity/red flags (data-loss incidents, security',
      'advisories). For the others: 3-5 facts each, same dimensions, especially how they onboard a',
      'server and whether any work behind NAT without SSH.',
    ].join('\n'),
  },
  {
    key: 'cross-cutting',
    prompt: RESEARCH_COMMON + '\n\nSUBJECT: the cross-cutting question - does ANY self-hosted PaaS/infra product in this space onboard servers WITHOUT SSH/inbound access (outbound-only agent dial-home)?\n' + [
      'Check: Coolify (agent announcements/status), Dokploy, CapRover, Dokku, Kamal (SSH-based deploys),',
      'Portainer Edge Agent, Cloudflare Tunnels-based patterns, Komodo (komo.do), Sliplane, Railway/',
      'Render self-host clones (Dokploy-likes), Nestri, Otomi, Acorn, k3s-adjacent tools. Also research:',
      'home-server/CGNAT pain points with these tools (forum/reddit/github issues - is "works behind',
      'NAT" a real user complaint?), Raspberry Pi/ARM support claims per product, and which products',
      'have fine-grained per-resource permissions (not just owner/admin/member).',
      'THE QUESTION TO ANSWER: is "outbound-only agent, zero SSH, NAT-friendly multi-server PaaS"',
      'genuinely unoccupied as of 2026, or does someone do it? Name names with sources.',
    ].join('\n'),
  },
  {
    key: 'journey',
    prompt: CHALLENGE_COMMON + '\n\nTASK: challenge the FIRST CUSTOMER JOURNEY (platform-vision.md section 4, product-roadmap.md section 13, domain-routing.md, certificate-management.md).\n' + [
      'Enumerate EVERY hidden dependency in: signup, org, agent install, node appears, project,',
      'deploy image, add domain, HTTPS works, monitoring, invite teammate. For the domain/HTTPS steps',
      'specifically analyze: domain ownership, DNS record creation (A/AAAA), DNS provider API',
      'requirements (Cloudflare token), public IP vs NAT vs CGNAT vs IPv6-only homes, port forwarding',
      '80/443, firewall, HTTP-01 vs DNS-01 prerequisites, what happens when the user has NO domain',
      'yet, nginx ALREADY RUNNING on the node (port 80/443 conflict - detect? refuse?), docker',
      'networking (how nginx reaches the container: published port? docker network?), and whether the',
      'agent can help with ANY of this at all (it cannot configure the router - say so).',
      'Then produce the SIMPLEST GENUINELY WORKING onboarding: what can honestly work in 10 minutes',
      'for (a) a VPS with public IP, (b) a home server behind NAT - and what must be labeled as',
      'prerequisites the user does outside NexusOps. Every "automatic" claim must be audited.',
    ].join('\n'),
  },
  {
    key: 'agent-security',
    prompt: CHALLENGE_COMMON + '\n\nTASK: review docs/node-agent-architecture.md + docs/platform-security-model.md + agent/nexusops_agent.py AS A SECURITY ENGINEER reviewing software that will hold privileged access to customer infrastructure.\n' + [
      'Analyze each of: initial enrollment (token exchange, single-use, delivery), agent authn',
      '(bearer nxa_ token), token theft (blast radius, detection), node compromise, replay (heartbeat',
      'and OPERATION replay - is there op-id idempotency? can a restored DB row re-trigger execution?),',
      'revocation (immediate? backoff?), rotation (dual-token grace - window, race), upgrades (agent',
      'update mechanism, who approves), downgrade attacks (protocol version negotiation - can a',
      'compromised server force an older weaker protocol? can the AGENT pin a minimum?), malicious',
      'control-plane responses (op tampering - is signing needed given TLS? what exactly does TLS not',
      'cover?), malicious org members (who can create ops, nginx config injection via templates),',
      'agent impersonation (another node claiming my identity), secrets delivery (op params at rest,',
      'claim-time decryption, minimization), certificate private keys (delivery, storage on node,',
      'permissions), nginx config generation (template allowlist, injection).',
      'VERDICT REQUIRED: (1) is the pull model sufficient - yes/no + why; (2) the EXACT list of what',
      'must be cryptographically signed/authenticated beyond TLS+per-node-token - and what must NOT',
      'be (do not add complexity reflexively); (3) any v1 blockers.',
    ].join('\n'),
  },
  {
    key: 'tenancy',
    prompt: CHALLENGE_COMMON + '\n\nTASK: challenge docs/multi-tenancy.md (session guard + ContextVar model) by enumerating EVERY bypass vector.\n' + [
      'Check each against the ACTUAL repo: raw SQL (grep backend/app for text( / execute( usage in',
      'services and routes - do any touch tenant tables?), background jobs (which tasks set scope?',
      'celery base task?), WebSockets (hub.py subscribe paths), Redis (raw pub/sub data), cached',
      'objects (any process-level caches of ORM objects?), joins/eager loading (with_loader_criteria',
      'include_aliases - does it cover selectinload/joinedload on this SQLAlchemy version - check',
      'requirements), session.get() direct PK lookups (does with_loader_criteria apply to Session.get',
      'in the pinned SQLAlchemy version? check), admin/system jobs (system_scope whitelist - who can',
      'enter it), migrations, agent ingestion (org from node row), scheduled jobs (maintenance.py,',
      'monitor checks, sweeper), search (search.py - ORM or raw?), exports.',
      'Then RULE on PostgreSQL Row Level Security: should it be adopted as defense in depth for',
      'Phase 1? If yes: exact mechanism (GUC app.current_org, roles: app vs system/migration), WHICH',
      'tables get RLS (tenant) and which must NOT (global), how system jobs bypass (separate role),',
      'interaction with the ORM guard (keep both? error semantics 404-vs-empty), and the CI test',
      '(raw-SQL probe suite). If no: what compensates for raw-SQL bypass. Be decisive.',
    ].join('\n'),
  },
  {
    key: 'terminology',
    prompt: CHALLENGE_COMMON + '\n\nTASK: challenge docs/domain-model.md TERMINOLOGY for a normal developer using the product.\n' + [
      'Define precisely, and check for overlap/ambiguity: Organization, Membership, Team, Role,',
      'Permission, Project, Environment, Application, Service (NOTE: the proposal has no Service',
      'entity - is Application enough? would a developer expect "Service"? decide and be explicit),',
      'Node, DockerEndpoint (should this even be user-visible?), Container, Deployment, Domain,',
      'Route (is "Route" the right user-facing word? too network-y?), Certificate, Secret,',
      'SecretVersion, Operation (is "Operation" clear? or is "Task/Action" better? do not rename for',
      'fashion - only if genuinely confusing), Backup*.',
      'Answer exactly: what IS an Application vs a Container vs a Deployment in one sentence each,',
      'from a USER perspective. Produce ONE canonical hierarchy in developer language. Flag any',
      'enterprise-speak that exists only to look sophisticated and propose the plainer word. Check',
      'frontend/src/pages for what the UI already calls things (naming drift = real cost). NO new',
      'entities allowed.',
    ].join('\n'),
  },
  {
    key: 'deploy-contract',
    prompt: CHALLENGE_COMMON + '\n\nTASK: challenge docs/deployment-architecture.md - is "deploy prebuilt Docker image" enough for an initial product, and what is the MINIMUM TRUSTWORTHY deployment contract?\n' + [
      'Evaluate each: docker registry support (public only? private auth - per org? per project?),',
      'image authentication (registry creds storage/encryption), immutable tags vs digests (pin at',
      'deploy? record digest on the deployment row?), health checks (what gate marks healthy - real',
      'check or naming only?), rollback (what exactly re-deploys - previous digest?), persistent',
      'volumes (named volumes? bind mounts policy - host paths are a footgun via agent), environment',
      'variables (source layering), secrets (fail-closed), zero-downtime behavior (is stop-then-start',
      'honestly labeled? what WOULD zero-downtime need - two containers + route switch - and is that',
      'explicitly deferred?), port conflicts (platform validates host-port collisions on the node?',
      'check what exists - container inventory has ports), container naming (deterministic',
      '{project}-{app}-{env}? collisions with user-created containers?), project networking (shared',
      'docker network per project/environment? or published ports only?).',
      'Deliver: the minimum contract that a careful engineer would call trustworthy for v1, marked',
      'as MUST / SHOULD / DEFERRED, each grounded in what the repo already has.',
    ].join('\n'),
  },
]

phase('Challenge')
log('4 competitor researchers + 5 hostile reviewers in parallel')
const results = await parallel(TASKS.map(t => () => agent(t.prompt, { label: t.key, phase: 'Challenge', schema: SCHEMA })))
return TASKS.map((t, i) => ({ key: t.key, finding: results[i] })).filter(r => r.finding)
