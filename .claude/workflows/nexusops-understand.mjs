export const meta = {
  name: 'nexusops-understand',
  description: 'Parallel subsystem readers produce structured maturity/tenancy reports of the NexusOps repo for the multi-tenant architecture design',
  phases: [
    { title: 'Understand', detail: '11 parallel readers over backend, frontend, agent, infra, docs, tests' },
  ],
}

const SCHEMA = {
  type: 'object',
  required: ['subsystem', 'components', 'tenancy_gaps', 'docs_needs', 'key_contracts', 'risks'],
  properties: {
    subsystem: { type: 'string' },
    components: {
      type: 'array',
      maxItems: 18,
      items: {
        type: 'object',
        required: ['name', 'maturity', 'evidence'],
        properties: {
          name: { type: 'string' },
          maturity: { type: 'string', enum: ['production', 'partial', 'simulated', 'stub'] },
          evidence: { type: 'string' },
          notes: { type: 'string' },
        },
      },
    },
    tenancy_gaps: { type: 'array', maxItems: 12, items: { type: 'string' } },
    docs_needs: { type: 'array', maxItems: 10, items: { type: 'string' } },
    key_contracts: { type: 'array', maxItems: 12, items: { type: 'string' } },
    extension_points: { type: 'array', maxItems: 10, items: { type: 'string' } },
    risks: { type: 'array', maxItems: 11, items: { type: 'string' } },
  },
}

const COMMON = [
  'You are analyzing the NexusOps repository at /home/emad/projects/nexusops (FastAPI async backend in backend/app,',
  'Celery worker, React SPA in frontend/src, stdlib Python agent in agent/, docker-compose infra).',
  'Your findings feed a MULTI-TENANT PLATFORM REDESIGN, so precision matters.',
  '',
  'MANDATORY first step: the repo has a knowledge graph at graphify-out/graph.json. From the repo root, orient with:',
  '  $(cat graphify-out/.graphify_python) -m graphify query "<your question>" --budget 2500',
  'also: graphify path "A" "B", graphify explain "concept".',
  'Only grep/read raw files AFTER graphify has oriented you, or for specific lines.',
  '',
  'Rules:',
  '- Every claim needs evidence as path:line references.',
  '- Classify each component maturity HONESTLY: production (works for real today), partial (works with gaps),',
  '  simulated (fabricated output), stub (placeholder).',
  '- Be terse: arrays max ~12 items, each item one line. No prose paragraphs.',
  '- Report only what IS, not recommendations — a separate phase designs the future.',
  '- Read files selectively (targeted ranges), do not dump whole files.',
  '- Do NOT modify any files. Your final output is the structured report only.',
].join('\n')

const READERS = [
  {
    key: 'auth-rbac',
    prompt: [
      'Subsystem: authentication, sessions, RBAC, permissions, API keys.',
      'Scope: backend/app/api/deps.py, api/v1/auth.py, users.py, roles.py, apikeys.py,',
      'services/auth_service.py, user_service.py, role_service.py, api_key_service.py,',
      'core/security.py, core/rate_limit.py, core/client_ip.py, related models and rbac/auth tests.',
      'Answer precisely:',
      '1. Full auth flow: access+refresh tokens, cookie rotation, reuse detection, session family revocation.',
      '2. Where is the permission registry defined? List ALL permission codenames that exist today (verbatim).',
      '3. How does require_permission() resolve permissions? What roles exist (seed)? Are permissions global or per-resource?',
      '4. ApiKey model: hashing, scoping, permission binding, single-use display of the raw key.',
      '5. Any existing organization/tenant concept anywhere? Any owner/creator user_id columns on resources?',
      '6. Rate limiter design and client IP resolution.',
      '7. Exactly what breaks if a second tenant is added (name the checks/queries assuming one global namespace).',
    ].join('\n'),
  },
  {
    key: 'models-db',
    prompt: [
      'Subsystem: complete SQLAlchemy data model + migration inventory.',
      'Scope: backend/app/models/*.py (ALL), models/base.py, alembic/versions/ (list all, skim structural ones),',
      'core/db.py, core/pagination.py.',
      'Answer precisely:',
      '1. Full entity inventory: every table, key columns, FKs, unique constraints — compact list.',
      '   Note the Server vs DockerHost relationship exactly (1:1? optional?).',
      '2. Which tables have any owner/creator/actor column? Which have NONE (fully global)?',
      '3. PK strategy per table (UUID vs bigserial), JSONB columns, enum types.',
      '4. Highest-volume tables (metrics, logs) and how they are pruned.',
      '5. Current alembic head + migration count.',
      '6. Which existing unique constraints would need to become per-org composite when org_id is added',
      '   (project slugs, secret names, monitor names, container uq, channel names).',
      '7. Anything that hard-blocks multi-tenancy (global unique constraints, global sequence assumptions).',
    ].join('\n'),
  },
  {
    key: 'agent',
    prompt: [
      'Subsystem: the NexusOps agent and enrollment.',
      'State: the repo has a graphify knowledge graph; orient first with graphify query (see COMMON rules).',
      'Scope: agent/ directory (nexusops_agent.py, install.sh, everything), api/v1/agent.py, schemas/agent.py,',
      'services/server_service.py heartbeat parts, tests/test_agent_contract.py, tests/integration agent tests.',
      'Answer precisely:',
      '1. Enrollment flow end-to-end: token source, hello payload, what persists, agent-side token storage perms, systemd unit.',
      '2. Heartbeat contract: exact fields, cadence, container cap, observed_at semantics.',
      '3. What the agent reports today and what it does NOT (capabilities, versions, services, nginx, disks).',
      '4. How the agent authenticates every call (header, token hashing server-side).',
      '5. Docker socket use from the agent: how, what it allows.',
      '6. Reconnect/offline behavior, clock handling, error handling, self-update if any.',
      '7. Agent identity: one token per server? rotation/revocation possible today?',
      '8. Security: what a stolen agent token can do today.',
    ].join('\n'),
  },
  {
    key: 'docker-containers',
    prompt: [
      'Subsystem: docker providers, container inventory, logs, stats, sweeps.',
      'Scope: providers (docker base/real/sim), services/container_service.py, server_service.py sweep,',
      'tasks/maintenance.py, services/log_service.py, container schemas, tests/integration/test_maintenance_sweep.py.',
      'Answer precisely:',
      '1. DockerProvider interface: exact methods; how docker_real connects; ssrf/endpoint guards.',
      '2. Full-host sweep: cadence, what it syncs, incremental log watermark, retention, adoption of agent containers.',
      '3. Heartbeat upsert path and the concurrent-insert savepoint pattern.',
      '4. Container lifecycle actions exposed (start/stop/restart/remove) — real or simulated? where implemented?',
      '5. Log streaming: Redis channel design, poll fallback, WS delivery.',
      '6. Metrics pipeline: agent samples -> storage -> aggregates -> retention.',
      '7. What assumes a single global docker-host namespace today.',
    ].join('\n'),
  },
  {
    key: 'deployments',
    prompt: [
      'Subsystem: projects, applications, environments, deployments end-to-end.',
      'Scope: models/delivery.py, services/project_service.py, deployment_engine.py, providers/deployment_runner.py,',
      'tasks/deployments.py, api/v1/projects.py, api/v1/deployments.py, deployment schemas,',
      'tests/integration/test_deployments_simulated.py, frontend Project*/Deployment* pages.',
      'Answer precisely:',
      '1. Exact model relationships: Project -> Application -> DeploymentEnvironment -> Deployment -> DeploymentStep, fields of each.',
      '2. Deployment state machine: statuses, transitions, queue path, sweeper backstop.',
      '3. Runner contract (plan_steps/execute_step/StepLine) and the simulated implementation — is ANYTHING real in deployments today?',
      '4. Environment config + secret refs (dollar-brace secret-colon KEY pattern) — where resolved, how audited.',
      '5. Trigger types, permissions required, rate limiting.',
      '6. Rollback/cancel semantics.',
      '7. Events/WS emitted during runs; log persistence and streaming channel.',
      '8. Seams for a REAL runner: what interface would an agent-backed runner implement; what inputs it needs.',
    ].join('\n'),
  },
  {
    key: 'monitoring-alerts',
    prompt: [
      'Subsystem: uptime monitors, checks, incidents, alerts, notification channels.',
      'Scope: monitor models/service/routes, monitor transports (sim + http), incident service/routes, alerts,',
      'notification_service + sender + delivery records, celery beat schedule, tests.',
      'Answer precisely:',
      '1. Monitor fields, check scheduling (claim_due_monitors), transport scheme dispatch, what sim:// does.',
      '2. Incident lifecycle (open/ack/resolved), transition-only events, notes.',
      '3. Alert rules (thresholds?) vs pure uptime.',
      '4. Notification channel types, delivery records, retries, secret header handling.',
      '5. What targets a monitor can point at today (URL only?) and what polymorphic targets need.',
      '6. What is real vs simulated here today.',
    ].join('\n'),
  },
  {
    key: 'core-secrets-ws',
    prompt: [
      'Subsystem: secrets, audit, events, event bus, WebSockets, config, errors.',
      'Scope: services/secret_service.py + secrets routes + Secret model, audit_service.py + models/observability.py,',
      'services/event_bus.py, ws/hub.py, ws routes, core/config.py, core/errors.py, core/logging.py, core/redis_client.py.',
      'Answer precisely:',
      '1. Secret storage today: encrypted at rest or plaintext? table shape, versioning, rotation, who reads values, leak paths.',
      '2. AuditLog shape: actor/action/resource/ip/metadata/request id; immutability; who writes it.',
      '3. SystemEvent shape/levels.',
      '4. Event bus + WS hub: publish/subscribe, Redis channels, WS connection auth, channel naming,',
      '   subscription authorization — would tenant B see tenant A events?',
      '5. Config surface: all env vars, SIMULATION_MODE, ALLOW_PRIVATE_TARGETS, TRUSTED_PROXY_CIDRS, encryption keys.',
      '6. Error envelope + exception hierarchy.',
    ].join('\n'),
  },
  {
    key: 'frontend',
    prompt: [
      'Subsystem: React SPA.',
      'Answer precisely (single-tenancy assumptions included):',
      'Scope: frontend/src/App.tsx (route map), api/client.ts, api/types.ts, auth/AuthContext.tsx, ws client,',
      'components/layout sidebar, lib/format, ALL pages (one-line purpose each), e2e journey, package.json deps.',
      'Answer precisely:',
      '1. Complete route map and sidebar nav structure.',
      '2. Client auth: storage, refresh, 401 handling; how hasPermission() gates UI.',
      '3. WS usage: which pages subscribe, reconnect behavior.',
      '4. TanStack Query patterns: query keys, invalidation conventions.',
      '5. Single-tenancy assumptions baked into the SPA.',
      '6. Per-page user-facing maturity (which flows work end-to-end).',
      '7. types.ts: hand-written vs backend-synced.',
    ].join('\n'),
  },
  {
    'key': 'infra-compose',
    prompt: [
      'Subsystem: compose topology, nginx edge, entrypoints, deploy flow.',
      'Scope: docker-compose.yml, docker-compose.docker-sock.yml, other compose files, nginx/ dir,',
      'backend/docker-entrypoint.sh, Makefile, .env.sample, scripts/, CI files, docs/deployment.md, docs/development.md.',
      'Answer precisely:',
      '1. Service topology: every service, image, ports, volumes, depends_on, healthchecks; loopback publishing (8090?).',
      '2. Proxy chain: Cloudflare -> host nginx -> edge -> api/frontend; WS upgrade map; cloudflare-ips.conf.',
      '3. Worker + beat config, queues, concurrency.',
      '4. Entrypoint: alembic on start, seeding gates, ENVIRONMENT modes.',
      '5. Docker socket mount override + DOCKER_GID mechanism.',
      '6. Control-plane vs data-plane split today — anything besides the agent running on customer servers?',
      '7. What compose changes a multi-tenant SaaS needs (or is the stack already cleanly separated?).',
    ].join('\n'),
  },
  {
    key: 'docs-reality',
    prompt: [
      'Subsystem: documentation vs implementation reality check.',
      'Scope: README.md and EVERY file in docs/ (list them all).',
      'Answer precisely:',
      '1. Inventory every doc with a one-line summary.',
      '2. Per doc: claims that are STALE or WRONG vs code (doc line + code path), features promised but absent/simulated,',
      '   claims that are accurate.',
      '3. Docs promises about deployments, monitoring, nodes/servers, domains/TLS that are actually simulated or missing.',
      '4. Important behavior that is undocumented (the -broken deployment demo hook, simulated runner, sim:// monitors).',
      '5. Anything in README that would mislead a new contributor about today capabilities.',
    ].join('\n'),
  },
  {
    key: 'tests',
    prompt: [
      'Subsystem: test suites and coverage shape.',
      'Scope: backend/tests/** (unit + integration), tests/test_agent_contract.py, frontend src tests, frontend/e2e/**,',
      'Makefile test targets, conftest patterns.',
      '1. Inventory: tests per area, unit vs integration split, markers, integration DB provisioning, fixture pattern.',
      '2. E2E journey steps and auth/refresh rotation handling.',
      '3. Agent contract test approach.',
      '4. Regression test conventions from recent fixes (flush-hook injection, DDL default assertions).',
      '5. What test infra multi-tenancy needs: cross-tenant IDOR suite, org fixtures — name existing helpers to extend.',
      '6. CI: any automated CI config in-repo, or purely local make targets?',
    ].join('\n'),
  },
]

phase('Understand')
log('Dispatching 11 subsystem readers in parallel')
const results = await parallel(READERS.map(r => () =>
  agent(COMMON + '\n\n' + r.prompt, { label: 'read:' + r.key, phase: 'Understand', schema: SCHEMA })
))

const out = []
for (let i = 0; i < READERS.length; i++) {
  out.push({ key: READERS[i].key, report: results[i] })
}
return out
