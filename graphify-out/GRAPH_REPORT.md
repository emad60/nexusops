# Graph Report - nexusops  (2026-10-09)

## Corpus Check
- 315 files · ~283,491 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: (none) 8, .example 1, .service 1)

## Summary
- 4540 nodes · 13327 edges · 184 communities (162 shown, 22 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1084 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `31c0b98b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- AuthContext.tsx
- project_service.py
- App.tsx
- apiGet
- test_operation_registry.py
- types.ts
- resolve_client_ip
- apiPost
- UsersPage.tsx
- list_servers
- test_operations.py
- ServerDetailPage.tsx
- APIModel
- client.ts
- projects.py
- incidents.py
- deployment_engine.py
- SimulatedDockerProvider
- run_async
- Secrets Architecture
- test_deployments_simulated.py
- list_containers
- dashboard_summary
- test_security.py
- Domain Routing — NexusOps
- monitor_service.py
- Node & Agent Architecture
- test_agent_backoff.py
- SimulatedDeploymentRunner
- nexusops_agent.py
- fixture
- login
- sync_host_state
- test_rate_limit.py
- docker_hosts.py
- test_ws_hub.py
- monitors.py
- search
- server_service.py
- list_deliveries
- DockerProvider
- test_monitor_transport.py
- StepFailure
- @tanstack/react-query
- RealDockerProvider
- test_permissions.py
- publish
- task
- BadRequest
- create_secret
- roles.py
- test_schemas_server.py
- apikeys.py
- test_migration_phase2.py
- v1/auth.py
- test_tenant_concurrency.py
- sweep_session
- alembic
- update_channel
- helpers.py
- compilerOptions
- _list_deployments
- test_error_logging.py
- organizations.py
- test_phase2_environments.py
- uuid
- test_schema_redaction.py
- PageParams
- decrypt_str
- package.json
- list_events
- test_secrets.py
- README.md - NexusOps overview
- models/__init__.py
- api service (FastAPI / uvicorn :8000)
- core/tenancy.py
- .check
- _create_monitor
- enums.py
- test_phase2_secrets.py
- sweep_deployments
- docker_real.py
- users.py
- tests/conftest.py
- test_agent_contract.py
- create_user
- devDependencies
- operation_service.py
- log_service.py
- Settings
- container.py
- environment.py
- require_server
- notification_service.py
- test_phase21_secret_version_integrity.py
- alerts.py
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- fixtures.ts
- DockerProviderError
- AppError
- Product Roadmap — NexusOps Multi-Tenant Platform
- env.py
- Platform Security Model — NexusOps
- StepLine
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- rollback_secret
- channel.py
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- ScopedSession
- Conflict
- create_app
- v1/health.py
- scripts
- AuthContext
- test_tenancy_allowlist.py
- _entity_exists
- dependencies
- DeploymentDetailPage.test.tsx
- generate_secrets.sh
- notification_sender.py
- server_payload
- pytest
- middleware.py
- docker_sim.py
- list_secrets
- AuditLogPage.tsx
- install.sh
- docker-entrypoint.sh
- integration/__init__.py
- Hub
- CLAUDE.md - project graphify rules
- Graphify query workflow (query / path / explain / update)
- frontend/index.html - SPA shell
- NexusOps Favicon — stylized letter 'N' lettermark in sky blue (#38bdf8) on a dark navy rounded square (#0b1120, 7px corner radius)
- nexusops-backend
- _is_same_origin
- 20260922_1000-a3f1c8d24b6e_add_tenancy_foundation.py
- postgres service (PostgreSQL 17, loopback :5433)
- viewer_in_a
- nexusops-understand.mjs
- Invisible account lockout (5 fails -> 15 min, enumeration resistance)
- _raw_probe
- get_secret_detail
- nexusops-draft.mjs
- SecretOut
- nexusops-challenge.mjs
- test_agent_ingestion.py
- AgentContainerIn
- test_run_async_publishes_frames_scheduled_by_the_commit_hook
- strip_query
- register_exception_handlers
- register_agent_hello
- _invite
- journey.spec.ts
- _FakeAsyncClient
- UUID
- resolve_auth
- AgentHelloIn
- .__tablename__
- 3. Agent lifecycle
- get_meta
- ApplicationBase
- _pace
- 4. Operations framework (added in this pass)
- _FakeSession
- sweep_servers
- ._check_status
- _run
- websocket_endpoint
- 20261009_1000-c3d4e5f6a7b8_enforce_secret_version_integrity.py
- get_settings
- permissions_for_role
- instant_pacing

## God Nodes (most connected - your core abstractions)
1. `AuthContext` - 136 edges
2. `APIModel` - 118 edges
3. `apiGet()` - 82 edges
4. `get_settings()` - 74 edges
5. `NotFound` - 67 edges
6. `record()` - 65 edges
7. `publish()` - 61 edges
8. `apiPost()` - 60 edges
9. `useToast()` - 58 edges
10. `ApiError` - 57 edges

## Surprising Connections (you probably didn't know these)
- `2. Org resolution on every request` --references--> `resolve_auth()`  [INFERRED]
  docs/multi-tenancy.md → backend/app/api/deps.py
- `3. Cross-cutting decisions` --references--> `require_permission()`  [INFERRED]
  docs/domain-model.md → backend/app/api/deps.py
- `10. Phase 7 — Teams, grants & custom roles` --references--> `require_permission()`  [INFERRED]
  docs/product-roadmap.md → backend/app/api/deps.py
- `3.2 Route` --references--> `rate_limit()`  [INFERRED]
  docs/domain-routing.md → backend/app/core/rate_limit.py
- `6.2 The allowlist (the injection defense)` --references--> `rate_limit()`  [INFERRED]
  docs/domain-routing.md → backend/app/core/rate_limit.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three authentication credential families with centralized permission checks** — docs_api_md_auth, docs_api_md_refresh_rotation, docs_api_md_api_keys, docs_agent_md_enrollment_token, docs_api_md_permission_model [EXTRACTED 1.00]
- **NexusOps compose stack services** — docker_compose_yml_nexusops_stack, docker_compose_yml_postgres_service, docker_compose_yml_redis_service, docker_compose_yml_mailpit_service, docker_compose_yml_api_service, docker_compose_yml_worker_service, docker_compose_yml_scheduler_service, docker_compose_yml_frontend_service, docker_compose_yml_nginx_service [EXTRACTED 1.00]
- **WebSocket real-time fan-out spine** — docs_architecture_md_websocket_hub, docs_api_md_websocket_channels, docker_compose_yml_redis_service, docs_architecture_md_event_bus, readme_react_spa [INFERRED 0.85]

## Communities (184 total, 22 thin omitted)

### Community 0 - "AuthContext.tsx"
Cohesion: 0.04
Nodes (47): getActiveOrgId(), setAccessToken(), setActiveOrgId(), Membership, SearchResult, User, LoginRoute(), RequireAuth() (+39 more)

### Community 1 - "project_service.py"
Cohesion: 0.13
Nodes (44): Any, AsyncSession, Request, UUID, Append an audit row using the caller's transaction (no commit here). The…, record(), _apply_update(), _check_server() (+36 more)

### Community 2 - "App.tsx"
Cohesion: 0.04
Nodes (95): DashboardSummary, DeploymentOut, DeploymentStepOut, Page, ProjectOut, AlertsPage, ApiKeysPage, App() (+87 more)

### Community 3 - "apiGet"
Cohesion: 0.09
Nodes (36): apiGet(), IncidentEventOut, MonitorDetailPage, formatDateTime(), formatDurationMs(), formatRelative(), truncate(), AlertsPage() (+28 more)

### Community 4 - "test_operation_registry.py"
Cohesion: 0.09
Nodes (26): Record the agent's outcome for an operation it claimed. The report is…, report_operation_result(), OperationType, The whitelist. Nothing outside this enum ships as an exec surface. Each type…, AgentOperationClaimOut, AgentOperationResultIn, AgentOperationResultOut, Any (+18 more)

### Community 5 - "types.ts"
Cohesion: 0.04
Nodes (43): AlertOut, ApiKeyOut, ChannelOut, ContainerOut, DeliveryOut, DeploymentLogLine, DeploymentStatus, DockerHostOut (+35 more)

### Community 6 - "resolve_client_ip"
Cohesion: 0.18
Nodes (21): _is_trusted(), _parse_networks(), Request, Client-IP resolution behind chained reverse proxies. The API never takes TCP…, Parse a comma-separated CIDR list; malformed entries are skipped., Real client address for *request* per the trust model above., resolve_client_ip(), make_request() (+13 more)

### Community 7 - "apiPost"
Cohesion: 0.06
Nodes (55): apiDelete(), apiPatch(), apiPost(), ApplicationOut, ENVIRONMENT_TYPE_LABELS, EnvironmentDetailOut, EnvironmentOut, EnvironmentType (+47 more)

### Community 8 - "UsersPage.tsx"
Cohesion: 0.07
Nodes (30): LoginPage, OrganizationRequiredPage, UsersPage, CheckboxField(), CheckboxFieldProps, FieldAria, FieldBaseProps, PasswordField() (+22 more)

### Community 9 - "list_servers"
Cohesion: 0.11
Nodes (28): create_server(), delete_server(), get_server(), list_servers(), list_tags(), DbDep, delete, Depends (+20 more)

### Community 10 - "test_operations.py"
Cohesion: 0.08
Nodes (51): expire_operations(), Expire node operations past their deadline — pending and claimed alike. A…, assert_error_code(), Assert envelope shape + code; returns the inner error object., test_metadata_endpoint_and_private_target_blocked(), _dispatch(), _dispatch_body(), _enrolled_node() (+43 more)

### Community 11 - "ServerDetailPage.tsx"
Cohesion: 0.09
Nodes (36): MetricPoint, ServerDetailPage, ServerListPage, ChartSeries, LineChart(), LineChartProps, PAD, buildServerPayload() (+28 more)

### Community 12 - "APIModel"
Cohesion: 0.04
Nodes (64): Node endpoints: CRUD, tags, agent enrollment tokens. The domain entity is the…, AgentHelloOut, Tells the agent how often to report., APIModel, BaseModel, Base for request/response models: ORM mode + strict-ish population., DeploymentCreate, DeploymentEnvironmentRef (+56 more)

### Community 13 - "client.ts"
Cohesion: 0.05
Nodes (46): API_BASE, ApiError, apiRequest(), buildUrl(), extractError(), getAccessToken(), onActiveOrgChange(), ORGANIZATION_HEADER (+38 more)

### Community 14 - "projects.py"
Cohesion: 0.12
Nodes (44): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+36 more)

### Community 15 - "incidents.py"
Cohesion: 0.23
Nodes (22): ActionCtx, acknowledge_incident(), add_incident_note(), get_incident(), list_incidents(), DbDep, Depends, get (+14 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.07
Nodes (75): _attribute_step_idx(), _parse_statuses(), datetime, Queue a new deployment for an application/environment pair., trigger_deployment(), deployment_log_channel(), Deployment, DeploymentEnvironment (+67 more)

### Community 17 - "SimulatedDockerProvider"
Cohesion: 0.11
Nodes (26): ContainerStatus, Implements :class:`DockerProvider` semantics against DB rows., Make a container row visible to this provider instance., Attach already-fetched log rows so ``logs()`` can replay them., SimulatedDockerProvider, _log_entry(), datetime, Unit tests for the simulated docker provider (in-memory rows, no docker). (+18 more)

### Community 18 - "run_async"
Cohesion: 0.18
Nodes (17): flush_pending_publishes(), Wait for frames scheduled by ``after_commit`` hooks to reach Redis. The commit…, T, Run *coroutine* on a dedicated event loop (Celery workers are sync). The loop…, run_async(), _drained(), The drain must not become a delay on the hot path for quiet tasks., test_flush_is_a_noop_when_nothing_is_pending() (+9 more)

### Community 19 - "Secrets Architecture"
Cohesion: 0.13
Nodes (15): 10. Resolution flow at deploy time, 2.1 Resolution runs inside org scope, 2.2 Migration mapping (applied by `b2c3d4e5f6a7`), 2. Scope model (org / project / environment layering) — **shipped**, 3.1 What this fixed, 3. SecretVersion — append-only history (**shipped in Phase 2**), 4.1 Audit event at resolution time, 4. Resolution authorization (+7 more)

### Community 20 - "test_deployments_simulated.py"
Cohesion: 0.13
Nodes (31): execute_deployment(), Run one deployment to a terminal state. Never raises; safe to re-run., get_application(), get_environment(), _run(), _as_worker(), _delivery_chain(), _owner_ctx() (+23 more)

### Community 21 - "list_containers"
Cohesion: 0.09
Nodes (41): _action_route(), _endpoint(), _container_out(), _ev(), get_container(), _like_pattern(), list_container_logs(), list_containers() (+33 more)

### Community 22 - "dashboard_summary"
Cohesion: 0.07
Nodes (38): get_dashboard_summary(), get_latest_server_metrics(), get_server_metrics(), CurrentUser, DbDep, Depends, get, UUID (+30 more)

### Community 23 - "test_security.py"
Cohesion: 0.11
Nodes (34): argon2, argon2_exceptions, generate_agent_token(), generate_api_key(), generate_refresh_token(), hash_password(), hash_token(), password_needs_rehash() (+26 more)

### Community 24 - "Domain Routing — NexusOps"
Cohesion: 0.07
Nodes (29): 10. Wildcards and catch-all, 11. User journey, 12. API surface, permissions, audit, 13. Monitoring tie-in, 1. Scope and current state, 2. Where nginx runs, 3.1 Domain, 3.2 Route (+21 more)

### Community 25 - "monitor_service.py"
Cohesion: 0.11
Nodes (45): MonitorStatus, Monitor, MonitorCheck, CheckOutcome, get_transport(), MonitorTransport, Protocol, Pick the transport matching the monitor URL scheme. (+37 more)

### Community 26 - "Node & Agent Architecture"
Cohesion: 0.12
Nodes (16): 1. Scope and stance, 2.1 Current shape (real), 2.2 Changes for the target model, 2.3 Capabilities (target), 2.4 DockerEndpoint — the 0..1 relation, 2. The Node concept, 6.1 Token scope, 6.2 docker.sock is root-equivalent (+8 more)

### Community 27 - "test_agent_backoff.py"
Cohesion: 0.15
Nodes (21): agent_fixture(), _install_sleep(), fake_sleep(), _load_agent(), _patch_host(), Any, fixture, MonkeyPatch (+13 more)

### Community 28 - "SimulatedDeploymentRunner"
Cohesion: 0.25
Nodes (23): Staged docker-style simulation used by v1 deployments., Canonical step identifiers stored on :class:`DeploymentStep` rows., SimulatedDeploymentRunner, StepName, _collect(), _ctx(), Unit tests for SimulatedDeploymentRunner (async generators, no broker)., RESOLVE_CONFIG is planned by the engine, not produced by a runner. (+15 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.08
Nodes (32): AgentClient, build_heartbeat(), collect_container_stats(), collect_containers(), cpu_percent_since(), disk_stats(), _docker_request(), _interruptible_sleep() (+24 more)

### Community 30 - "fixture"
Cohesion: 0.13
Nodes (17): _admin_dsn(), client(), _ensure_database(), _migrated_database(), owner(), AsyncClient, fixture, A session scoped to the system scope — how a maintenance sweep runs. Sweeps are… (+9 more)

### Community 31 - "login"
Cohesion: 0.10
Nodes (41): active_memberships(), The user's memberships in non-suspended organizations, oldest first. Reads only…, System scope bound to *db*, for rows that have no organization. Used by exactly…, system_write_scope(), _audit(), change_own_password(), count_users(), _event() (+33 more)

### Community 32 - "sync_host_state"
Cohesion: 0.10
Nodes (26): is_simulated(), True when *provider* is the simulated implementation., _as_health(), _as_status(), collect_recent_logs(), _daily_dedup(), _dispatch(), _emit() (+18 more)

### Community 33 - "test_rate_limit.py"
Cohesion: 0.15
Nodes (20): RateLimited, client_ip(), _memory_count_and_ttl(), Request, rate_limit(), _dependency(), Best-effort client IP; honours X-Forwarded-For from trusted proxies. Delegates…, Fixed-window counter backed by process memory. Returns (count, ttl). (+12 more)

### Community 34 - "docker_hosts.py"
Cohesion: 0.05
Nodes (77): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+69 more)

### Community 35 - "test_ws_hub.py"
Cohesion: 0.19
Nodes (22): _connection(), _drain(), _event_frame(), _fake_sessionmaker(), hub(), _Org, Any, fixture (+14 more)

### Community 36 - "monitors.py"
Cohesion: 0.19
Nodes (31): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+23 more)

### Community 37 - "search"
Cohesion: 0.08
Nodes (39): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+31 more)

### Community 38 - "server_service.py"
Cohesion: 0.06
Nodes (73): asyncio, _detail(), AsyncSession, Canonical Redis pub/sub channel names shared by API, workers and WS hub., server_metrics_channel(), ContainerHealth, DockerHostStatus, ServerStatus (+65 more)

### Community 39 - "list_deliveries"
Cohesion: 0.16
Nodes (24): create_channel(), delete_channel(), get_channel(), list_channels(), list_deliveries(), DbDep, delete, Depends (+16 more)

### Community 40 - "DockerProvider"
Cohesion: 0.09
Nodes (12): DockerProvider, Any, datetime, Protocol, List containers visible to the provider., Inspect a single container by id (short ids allowed)., List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``., List volumes: keys ``name``, ``driver``, ``mountpoint``. (+4 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.10
Nodes (40): CheckResult, coerce_headers(), HTTPMonitorTransport, Any, Deterministic fake checker for ``sim://`` monitors and demo environments.…, Normalise arbitrary JSON-ish header input into a plain str->str dict., Real HTTP(S) probe using httpx with per-monitor settings. Redirects are…, SimulatedTransport (+32 more)

### Community 42 - "StepFailure"
Cohesion: 0.08
Nodes (25): DeploymentRunner, Exception, Protocol, Raised by a runner when a step fails irrecoverably., Adapter interface implemented by real (future) and simulated runners., Return the ordered step names for this run., StepFailure, 10. Events and WS during runs (+17 more)

### Community 43 - "@tanstack/react-query"
Cohesion: 0.03
Nodes (80): CheckOut, IncidentOut, MonitorOut, Role, MetaInfo, SimulatedChip(), mocks, Toast (+72 more)

### Community 44 - "RealDockerProvider"
Cohesion: 0.14
Nodes (7): ContainerInfo, Normalized view of a container as reported by any provider., T, Execute an SDK call with one short retry, normalizing failures., Two short samples give real cpu/net deltas without streaming., Talks to a real docker daemon over ``unix://`` or ``tcp://``., RealDockerProvider

### Community 45 - "test_permissions.py"
Cohesion: 0.06
Nodes (34): permission_exists(), PermissionSpec, Permission registry and role matrix. Permissions are *data*: the registry below…, Check an API-key scope list against a required permission. Supports exact match…, scope_matches(), _auth_context(), _FakeCtx, parametrize (+26 more)

### Community 46 - "publish"
Cohesion: 0.09
Nodes (35): get_redis(), ping(), Shared async Redis client., SystemEvent, _after_commit_publish(), _after_rollback_drop(), event_frame_from_row(), publish() (+27 more)

### Community 47 - "task"
Cohesion: 0.18
Nodes (11): aggregate_metrics(), _run(), expire_sessions(), _run(), task, Revoke sessions past their expiry and purge dead refresh tokens., Time-based retention per source plus a per-container row cap., retry_notifications() (+3 more)

### Community 48 - "BadRequest"
Cohesion: 0.07
Nodes (64): BadRequest, UnprocessableEntity, assert_safe_tcp_endpoint(), assert_safe_url(), assert_safe_url_async(), _is_forbidden_address(), is_simulation_url(), ValueError (+56 more)

### Community 49 - "create_secret"
Cohesion: 0.22
Nodes (16): create_secret(), delete_secret(), get_secret(), list_secret_versions(), list_secrets(), _project_exists(), AsyncSession, Request (+8 more)

### Community 50 - "roles.py"
Cohesion: 0.11
Nodes (29): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, delete, get (+21 more)

### Community 51 - "test_schemas_server.py"
Cohesion: 0.23
Nodes (20): Payload for registering a server., ServerCreate, _base(), parametrize, Unit tests for app.schemas.server (validation only, no I/O)., test_empty_ip_is_allowed_but_whitespace_collapses(), test_empty_name_or_hostname_rejected(), test_heartbeat_interval_bounds_inclusive() (+12 more)

### Community 52 - "apikeys.py"
Cohesion: 0.09
Nodes (31): create_api_key(), list_api_keys(), CurrentUser, DbSessionDep, delete, get, post, Request (+23 more)

### Community 53 - "test_migration_phase2.py"
Cohesion: 0.11
Nodes (34): alembic_config, alembic_script, Phase 2.1 corrective migration: legacy ``environment_type`` classification.…, Every case is classified as documented, ids and ownership intact., An explicit non-DEV classification survives the corrective migration. The…, The correction is part of ``head`` and adds no extra Alembic head., Insert one legacy environment per case, in two organizations., _seed_typed_environments() (+26 more)

### Community 54 - "v1/auth.py"
Cohesion: 0.08
Nodes (52): change_password(), _clear_refresh_cookie(), _cookies_secure(), login(), logout(), me(), _optional_actor(), AsyncSession (+44 more)

### Community 55 - "test_tenant_concurrency.py"
Cohesion: 0.12
Nodes (33): current_scope(), ``'org'``, ``'system'`` or ``'unset'``., _create_server(), _guc(), _maker(), pooled_engine(), async_sessionmaker, AsyncEngine (+25 more)

### Community 56 - "sweep_session"
Cohesion: 0.12
Nodes (30): _collect_logs(), _run(), _run(), _sync_one(), task, Monitor dispatch: claim due monitors atomically, run their checks., Claim up to CLAIM_BATCH due monitors and execute each check.…, run_due_monitors() (+22 more)

### Community 57 - "alembic"
Cohesion: 0.05
Nodes (13): alembic, downgrade(), rename ``server.*`` permission codenames to ``node.*`` The Node/Server…, _rename_permissions(), upgrade(), Fix pre-existing model/migration drift (surfaced by the new drift check). Two…, downgrade(), Phase 2.1 — correct legacy ``environment_type`` classification. The Phase 2… (+5 more)

### Community 58 - "update_channel"
Cohesion: 0.23
Nodes (16): _audit(), create_channel(), decrypt_channel_config(), delete_channel(), encrypt_config(), _normalize_events(), Any, AsyncSession (+8 more)

### Community 59 - "helpers.py"
Cohesion: 0.06
Nodes (59): bearer(), cookie_attributes(), error_of(), login_account(), login_headers(), Any, AsyncClient, Response (+51 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "_list_deployments"
Cohesion: 0.11
Nodes (32): cancel_deployment(), _emails_for(), get_deployment(), list_application_deployments(), list_deployment_logs(), _list_deployments(), _parse_sort(), alias (+24 more)

### Community 62 - "test_error_logging.py"
Cohesion: 0.22
Nodes (4): Regression: the catch-all 500 handler must not log raw exception text.…, _SpyLogger, test_unhandled_exception_handler_logs_class_not_message(), fastapi_testclient

### Community 63 - "organizations.py"
Cohesion: 0.15
Nodes (18): create_organization(), list_my_organizations(), CurrentUser, DbSessionDep, get, IdentityUser, patch, post (+10 more)

### Community 64 - "test_phase2_environments.py"
Cohesion: 0.18
Nodes (22): _environment(), _project(), parametrize, Phase 2: project-scoped environments, config layering, and their isolation. The…, Uniqueness is ``(project_id, slug)`` — not instance-wide., The update path is validated too (the pre-Phase-2 gap)., Knowing an environment UUID is not access: the project link must hold., Another tenant cannot reach the project, its environments, or its detail. (+14 more)

### Community 65 - "uuid"
Cohesion: 0.06
Nodes (43): Agent-facing schemas. Payloads are data only — never executed., AuditOut, Schemas for the read-only audit log API. The audit table is append-only; these…, One audit trail entry (no write routes ever exist for this resource).…, OutModel, Shared Pydantic v2 base schemas., Response model base — timestamps serialized as ISO-8601 UTC., DeploymentApplicationRef (+35 more)

### Community 66 - "test_schema_redaction.py"
Cohesion: 0.18
Nodes (17): is_sensitive_header(), mask_sensitive_headers(), True when *name* looks like it carries a credential (Authorization etc.)., Return a copy of *headers* with sensitive values replaced by a mask., mask_target(), Human-readable masked target safe to expose over the API. For webhook families…, _monitor_out(), Outbound-schema redaction: monitor probe credentials and webhook targets.… (+9 more)

### Community 67 - "PageParams"
Cohesion: 0.12
Nodes (32): list_applications(), list_environments(), list_projects(), Depends, get, ReadUser, Cursor, CursorPage (+24 more)

### Community 68 - "decrypt_str"
Cohesion: 0.08
Nodes (28): decrypt_str(), digest_of(), _fernet(), Short server-verifiable digest used for change detection display. HMAC-SHA256…, parametrize, test_decrypt_with_wrong_ciphertext_raises_value_error(), test_digest_is_keyed_not_plain_sha256(), test_digest_length_and_determinism() (+20 more)

### Community 69 - "package.json"
Cohesion: 0.13
Nodes (15): name, private, type, version, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom (+7 more)

### Community 70 - "list_events"
Cohesion: 0.10
Nodes (21): _decode_cursor(), _encode_cursor(), list_event_types(), list_events(), datetime, DbSession, Depends, get (+13 more)

### Community 71 - "test_secrets.py"
Cohesion: 0.11
Nodes (26): Exception, A ``${secret:KEY}`` reference could not be resolved. Fail-closed. Carries…, One successfully resolved reference: metadata for audit, no value., Resolve every ``${secret:KEY}`` reference an environment's config names.…, resolve_secrets_for_environment(), SecretReference, SecretResolutionError, _create() (+18 more)

### Community 72 - "README.md - NexusOps overview"
Cohesion: 0.17
Nodes (24): docker-compose.dev.yml - dev overlay, docker-compose.docker-sock.yml - docker socket override, docker-compose.yml - full stack definition, docs/agent.md - agent guide, docs/api.md - API guide, Append-only audit log (Postgres BEFORE UPDATE OR DELETE trigger), docs/architecture.md - system architecture, docs/deployment.md - deployment and operations guide (+16 more)

### Community 73 - "models/__init__.py"
Cohesion: 0.05
Nodes (109): encrypt_str(), Base, big_serial_pk(), json_column(), org_id_column(), OrgScoped, datetime, UUID (+101 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "core/tenancy.py"
Cohesion: 0.09
Nodes (36): The active organization, or raise if this request has none., _apply_scope_guc(), _desired_guc(), _guard(), _has_org_predicate(), install_tenancy_guards(), _mappers_of(), _org_scoped_classes() (+28 more)

### Community 76 - ".check"
Cohesion: 0.33
Nodes (5): _decode(), BaseException, Flatten an exception into a bounded single-line string. The request URL is…, _sanitize_error(), test_sanitize_error_flattens_and_bounds()

### Community 77 - "_create_monitor"
Cohesion: 0.33
Nodes (6): _create_monitor(), Regression: probe headers and URL query credentials never leave the API. Probe…, A monitor's checks, incidents and timeline all live in its organization, so the…, test_check_now_endpoint_runs_immediately(), test_down_then_recover_lifecycle(), test_monitor_responses_mask_probe_credentials()

### Community 78 - "enums.py"
Cohesion: 0.13
Nodes (34): AckResponse, BaseModel, AuditResult, CredentialKind, IncidentEventKind, IncidentSeverity, IncidentStatus, LogLevel (+26 more)

### Community 79 - "test_phase2_secrets.py"
Cohesion: 0.19
Nodes (21): _env(), _project(), Phase 2 secrets: layered scope, immutable versions, rollback, isolation. Two…, Two racing rotations must both be kept and never share a version number., Another tenant cannot read, rotate, roll back or even enumerate the secret., The documented example: same key at three scopes; most specific wins., A ref declared in the project base config resolves for its environments., _resolved() (+13 more)

### Community 80 - "sweep_deployments"
Cohesion: 0.33
Nodes (6): task, Execute one queued deployment. The engine owns all state transitions., Re-enqueue deployments the broker lost; fail ones whose worker died.…, run_deployment(), sweep_deployments(), _run()

### Community 81 - "docker_real.py"
Cohesion: 0.21
Nodes (16): _as_float(), _compute_stats(), _cpu_percent(), _network_bytes(), parse_rfc3339(), Any, datetime, Real docker provider backed by the docker SDK against a live daemon. Every SDK… (+8 more)

### Community 82 - "users.py"
Cohesion: 0.14
Nodes (24): create_user(), deactivate_user(), get_user(), list_users(), CurrentUser, DbSessionDep, delete, get (+16 more)

### Community 83 - "tests/conftest.py"
Cohesion: 0.12
Nodes (13): alembic_autogenerate, alembic_migration, configure_test_env(), Test bootstrap: pin every cached setting BEFORE the first ``app`` import. The…, KEY=VALUE pairs from the repo .env (first definition wins); never logged., Export the exact settings the app caches; host values cannot leak through., _read_dot_env(), Model / migration drift: the schema in the database must match the models.… (+5 more)

### Community 84 - "test_agent_contract.py"
Cohesion: 0.20
Nodes (15): agent_fixture(), _load_agent(), _patch_stats(), Any, fixture, MonkeyPatch, Contract tests: the shipped agent's payloads must satisfy the ingest schemas.…, One-shot docker stats reduce to cpu/mem/limit fields the schema accepts, with… (+7 more)

### Community 85 - "create_user"
Cohesion: 0.07
Nodes (50): list_sessions(), CurrentUser, DbSessionDep, delete, get, Request, UUID, Active sessions of this organization's members. Defaults to the caller's own;… (+42 more)

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "operation_service.py"
Cohesion: 0.06
Nodes (73): cancel_operation(), create_operation(), get_operation(), list_operations(), DbDep, Depends, get, post (+65 more)

### Community 88 - "log_service.py"
Cohesion: 0.10
Nodes (33): _decode_frame(), _max_log_id(), _poll_new_lines(), Parse a Redis pub/sub frame ``{ts, stream, message}`` into a LogLine., Highest persisted log id for a container (poll fallback watermark)., Fetch log rows persisted after ``last_seen['id']`` (poll fallback)., Live-tail a container's logs. Primary source is the Redis pub/sub channel…, stream_container_logs() (+25 more)

### Community 89 - "Settings"
Cohesion: 0.12
Nodes (7): field_validator, model_validator, Whether the runtime connection is the RLS-enforced application role. False…, Username from :attr:`database_url`, or ``None`` if it is unparseable., Validated application settings (loaded from environment / .env)., Settings, BaseSettings

### Community 90 - "container.py"
Cohesion: 0.21
Nodes (12): ContainerRemoveOut, host_ref(), HostRef, LogEntryOut, UUID, Container schemas: list/detail read models, log entries, action results., Summary of the docker host a container runs on., Summary of the server associated with a container. (+4 more)

### Community 91 - "environment.py"
Cohesion: 0.06
Nodes (44): EnvironmentType, Kind of a project-scoped deployment environment (Phase 2). Descriptive only —…, EnvironmentBase, EnvironmentCreate, EnvironmentUpdate, _normalise_environment_type(), field_validator, Deployment-environment API schemas (Phase 2: **project-scoped**). An… (+36 more)

### Community 92 - "require_server"
Cohesion: 0.19
Nodes (15): agent_heartbeat(), agent_hello(), claim_operation(), _presented_token(), DbDep, post, Request, Response (+7 more)

### Community 93 - "notification_service.py"
Cohesion: 0.05
Nodes (77): dispose_engine(), get_engine(), get_sessionmaker(), async_sessionmaker, AsyncEngine, AsyncSession, close_redis(), apply_scope_to_session() (+69 more)

### Community 94 - "test_phase21_secret_version_integrity.py"
Cohesion: 0.18
Nodes (18): _app_role_dsn(), _owner_dsn(), _probe(), Phase 2.1 — ``secret_versions`` is append-only in the **database**, not just in…, Immutability is a database guarantee, not merely a missing code path. The owner…, The legitimate append paths keep working under the guard., The documented deletion policy: purging a Secret cascades its history., RLS is preserved: another tenant cannot see a version row, even by id. (+10 more)

### Community 95 - "alerts.py"
Cohesion: 0.13
Nodes (25): list_alerts(), mark_all_read(), mark_read(), CurrentUser, DbDep, Depends, get, post (+17 more)

### Community 96 - "NexusOps (self-hosted infrastructure management and monitoring platform)"
Cohesion: 0.20
Nodes (10): mailpit service (dev SMTP sink + web UI :8025), NexusOps compose stack (8 services on one network), HIGH finding: redirect-following SSRF in uptime monitors (fixed: follow_redirects=False + per-hop guard), SSRF guard (assert_safe_url, per-redirect-hop validation, assert_safe_tcp_endpoint), Mailpit SMTP port internal-only (host-side injection needs extra mapping), Host port knobs (NEXUSOPS_HTTP_PORT/POSTGRES/REDIS/MAILPIT/VITE), SPA entry point (loads /src/main.tsx, dark color-scheme), Uptime monitors -> incidents -> notifications flow (+2 more)

### Community 97 - "REST API surface (/api/v1)"
Cohesion: 0.29
Nodes (7): Cursor (keyset) and offset pagination envelopes, Permission model (data-driven registry, require_permission, wildcard scopes), REST API surface (/api/v1), RBAC registry (PERMISSIONS + ROLE_MATRIX + scope_matches), Adding a new resource: 7-step checklist (model -> migration -> schemas -> service -> router -> tests -> frontend), Alembic migration workflow (autogenerate, models __init__ export, entrypoint apply), Command palette (Ctrl/Cmd+K)

### Community 98 - "fixtures.ts"
Cohesion: 0.23
Nodes (11): EDGE, MAILPIT, ADMIN, Bootstrap, bootstrapVia(), test, ADMIN, openProject() (+3 more)

### Community 99 - "DockerProviderError"
Cohesion: 0.13
Nodes (18): clip(), DockerProviderError, Exception, A provider operation failed. ``str()`` is safe to show/log., Build a compact, secret-free description of a provider failure. Only the…, Truncate *text* to *limit* characters, stripping control chars., sanitize_error(), describe_provider_error() (+10 more)

### Community 100 - "AppError"
Cohesion: 0.20
Nodes (16): AppError, Exception, Base class for expected, client-facing errors., _authenticate_api_key(), _authenticate_jwt(), _bind_organization(), _load_permissions(), _org_id_from_frame() (+8 more)

### Community 101 - "Product Roadmap — NexusOps Multi-Tenant Platform"
Cohesion: 0.11
Nodes (19): 0. Stance, 10. Phase 7 — Teams, grants & custom roles, 11. Phase 8 — Backups, 12. Phase 9 — Billing & metering, 13.1 Scope-creep gates — what must be true before each expansion, 13. First commercially meaningful version, 14. Biggest risks (short form), 15. Reading order (+11 more)

### Community 102 - "env.py"
Cohesion: 0.24
Nodes (10): _database_url(), Alembic environment: metadata comes from app.models, URL from app settings., Migrations run as the table **owner**, never as the application role. The owner…, Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online(), Owner-role DSN for Alembic and the container entrypoint. Migrations… (+2 more)

### Community 103 - "Platform Security Model — NexusOps"
Cohesion: 0.10
Nodes (20): make(), 10.1 Node revocation playbook (compromised node / leaked agent token), 10.2 Key compromise playbook, 10. Incident response, 1.1 Real vs simulated today (do not mistake one for the other), 1. Scope, stance, and simulation honesty, 2. Assets, 3. Trust boundaries (+12 more)

### Community 104 - "StepLine"
Cohesion: 0.24
Nodes (7): _commit_short(), Stream output lines for *step_name*; raise StepFailure to fail it., Everything a runner needs to execute one deployment., One streamed output line for a step., RunContext, _slug(), StepLine

### Community 105 - "redis service (Redis 7, no persistence, loopback :6390)"
Cohesion: 0.22
Nodes (11): redis service (Redis 7, no persistence, loopback :6390), WebSocket API (/api/v1/ws handshake, frames, limits), WebSocket channels (global, server-metrics, container-logs, deployment-logs, incidents), Deployment engine (queue_deployment / execute_deployment / sweeper backstop), Real-time spine: PostgreSQL system_events + Redis pub/sub, Rollback as a new deployment (rollback_of_id), WebSocket hub (framework-thin, Redis fan-in, per-socket queues), Test suites (pytest unit+integration, vitest, Playwright e2e) (+3 more)

### Community 106 - "NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)"
Cohesion: 0.18
Nodes (12): Agent security model (one-way telemetry, no command channel), Agent enrollment token (X-Agent-Token, nxa_..., SHA-256 at rest), Agent heartbeat exponential backoff (cap 5 min, exit 1 on revoked token), agent/install.sh (enrollment installer), Agent metrics collection (/proc statvfs Docker socket), NexusOps agent (stdlib-only Python, agent/nexusops_agent.py), Agent systemd hardening (ProtectSystem=strict, NoNewPrivileges), Agent ingest API (POST /agent/hello, POST /agent/heartbeat) (+4 more)

### Community 107 - "rollback_secret"
Cohesion: 0.26
Nodes (13): create_secret(), delete_secret(), DbSession, delete, post, Request, Append a new version with a new value and make it current., Make a previous version current by appending a new version (non-destructive). (+5 more)

### Community 108 - "channel.py"
Cohesion: 0.17
Nodes (14): ChannelType, ChannelBase, ChannelCreate, ChannelUpdate, DeliveryOut, EmailConfig, BaseModel, model_validator (+6 more)

### Community 109 - "Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)"
Cohesion: 0.25
Nodes (9): API keys (X-API-Key, nxo_..., scope intersection), First boot sequence (api entrypoint migrates, compose never seeds), Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test), Makefile workflows (up/test/lint/typecheck/migrate/seed), HIGH finding: API-key scope bypass for superadmin-owned keys (fixed: scope intersection first), Security audit 2026-09 (26 raw findings -> 20 confirmed, all fixed), HIGH finding: known seed superadmin + API key backdoor (fixed: NEXUSOPS_ALLOW_SEED opt-in, one-time password), Threat model (edge attacker, malicious agent, curious operator, leaked token, SSRF) (+1 more)

### Community 111 - "Conflict"
Cohesion: 0.09
Nodes (48): _check(), Conflict, Forbidden, ActorType, add_member(), create_organization(), get_organization(), membership_for_user() (+40 more)

### Community 112 - "create_app"
Cohesion: 0.22
Nodes (14): create_app(), _include_routers(), lifespan(), FastAPI, Mount every domain router. Router variables follow the module contract., Start the WS hub + notification dispatcher; tear them down cleanly., _app_for_environment(), MonkeyPatch (+6 more)

### Community 113 - "v1/health.py"
Cohesion: 0.20
Nodes (13): liveness(), get, Response, Health probes: liveness (always cheap) and readiness (checks dependencies).…, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness(), HealthOut (+5 more)

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "AuthContext"
Cohesion: 0.05
Nodes (98): AuthContext, get_current_user(), _load_permissions(), permission_dep(), Any, FastAPI dependencies: database session, authenticated tenant context, RBAC…, Effective permissions come from the **membership's** role, not the user's. A…, Org-scoped authentication: identity + validated active organization. Also… (+90 more)

### Community 116 - "test_tenancy_allowlist.py"
Cohesion: 0.18
Nodes (15): AST, _actual_callers(), _calls_system_scope(), _module_path(), The system-scope allowlist is the only fence around the tenancy carve-out.…, Every module that could open a system scope: ``app/`` plus the scripts., No module may lift tenant isolation without being named in the list., Every listed module must still be a real caller, so the list stays short. (+7 more)

### Community 117 - "_entity_exists"
Cohesion: 0.15
Nodes (13): _entity_exists(), _frame_org(), _parse_payload(), Any, Whether *id_* exists **for this organization**. Runs inside the socket's…, Spawn the Redis fan-in listener (idempotent)., Deliver one Redis message to every matching subscription., The organization an event frame belongs to, or ``None`` when it has none. (+5 more)

### Community 118 - "dependencies"
Cohesion: 0.33
Nodes (6): dependencies, lucide-react, react, react-dom, react-router-dom, @tanstack/react-query

### Community 119 - "DeploymentDetailPage.test.tsx"
Cohesion: 0.13
Nodes (9): ACTIVE_MEMBERSHIP, ApiError, deploymentDetail(), EMPTY_LOGS, FakeWebSocket, get, ME, post (+1 more)

### Community 120 - "generate_secrets.sh"
Cohesion: 0.47
Nodes (3): existing_real_keys(), replace_or_append(), generate_secrets.sh script

### Community 121 - "notification_sender.py"
Cohesion: 0.15
Nodes (18): NotificationError, Any, BaseException, Exception, Low-level notification transports: SMTP email and outgoing webhooks. These…, POST *payload* as JSON to *url*; 2xx is success, anything else raises. Response…, Raised when a delivery attempt fails. Message is safe to persist., Bounded, single-line, content-free error reason. (+10 more)

### Community 122 - "server_payload"
Cohesion: 0.10
Nodes (26): A valid POST /servers body with per-test overrides., server_payload(), Regression: a superadmin-owned key is still limited to its scope list. The…, test_scoped_api_key_cannot_exceed_its_grant(), _create_server(), Server CRUD, cascade delete, audit trail rows and audit immutability., The HTTP listing path — schema serialization is exercised end-to-end. A…, ``/servers`` is a temporary alias for pre-rename clients. It must keep working… (+18 more)

### Community 123 - "pytest"
Cohesion: 0.20
Nodes (10): created_at server defaults must evaluate per insert, not at table creation., Regression: system_events and audit_logs shipped with DEFAULT 'now()' (quoted…, test_audit_and_event_created_at_defaults_are_dynamic(), UUID, Phase 2.2 — the environment-type correction follows the documented precedence.…, Create one legacy (application-scoped) environment per case., Every branch of the slug-first rule, end to end through ``head``., _seed_legacy() (+2 more)

### Community 124 - "middleware.py"
Cohesion: 0.15
Nodes (14): ASGIApp, AccessLogMiddleware, Request, Response, HTTP middleware: request ids, security headers, structured access logs., Baseline hardening headers on every API response., RequestIDMiddleware, SecurityHeadersMiddleware (+6 more)

### Community 125 - "docker_sim.py"
Cohesion: 0.15
Nodes (9): ContainerStats, Point-in-time resource usage snapshot., Any, datetime, Simulated docker provider for demo and test environments. The provider is…, Plausible numbers derived from the row plus time-based sine noise., Replay registered LogEntry rows ordered by ts (tail N). ``follow`` is ignored…, _seed_int() (+1 more)

### Community 126 - "list_secrets"
Cohesion: 0.29
Nodes (10): get_secret(), list_secret_versions(), list_secrets(), get, PageParamsDep, UUID, Paginated secret metadata (keys, versions, digests — never values)., One secret's metadata. (+2 more)

### Community 127 - "AuditLogPage.tsx"
Cohesion: 0.19
Nodes (8): AuditEntry, AuditLogPage, AuditLogPage(), AuditRow, formatTimestamp(), RESULTS, shortId(), mockedGet

### Community 137 - "Hub"
Cohesion: 0.20
Nodes (11): _close_socket(), Connection, Hub, _params_key(), WebSocket, Connection registry, Redis fan-in listener and per-socket pumps., Cancel the listener and close every socket (service restart)., Origin check → accept → auth handshake → message loop. (+3 more)

### Community 146 - "_is_same_origin"
Cohesion: 0.50
Nodes (4): _is_same_origin(), Browsers always send Origin on WS handshakes, even same-origin ones. When it…, The proxy must forward the Host the browser actually used. A browser sends…, test_same_origin_compares_the_full_authority_including_port()

### Community 147 - "20260922_1000-a3f1c8d24b6e_add_tenancy_foundation.py"
Cohesion: 0.20
Nodes (12): _app_role_credentials(), _assert_fully_backfilled(), _backfill_org_ids(), _drop_constraint(), add tenancy foundation Phase 1 of the platform roadmap: organizations,…, Carry a value into a PL/pgSQL block. ``CREATE ROLE``/``ALTER ROLE`` are utility…, Application role name/password from settings (never hard-coded)., Point every pre-existing row at the bootstrap organization. ``audit_logs`` is… (+4 more)

### Community 148 - "postgres service (PostgreSQL 17, loopback :5433)"
Cohesion: 0.29
Nodes (7): postgres service (PostgreSQL 17, loopback :5433), Fernet encryption at rest (ENCRYPTION_KEY, write-once), Backups (pgdata volume, nightly pg_dump, ephemeral Redis), Required secrets (POSTGRES_PASSWORD, JWT_SECRET >= 32 chars, ENCRYPTION_KEY Fernet), Production hardening checklist (secrets, ENVIRONMENT, no seed, TLS, rotation), Compose vs host network namespaces (postgres:5432 vs 127.0.0.1:5433), Simulation mode (SIMULATION_MODE)

### Community 149 - "viewer_in_a"
Cohesion: 0.40
Nodes (5): org_a(), fixture, A least-privileged, **non-superadmin** member of organization A. Used to show…, The bootstrap organization plus a few resources created inside it., viewer_in_a()

### Community 150 - "nexusops-understand.mjs"
Cohesion: 0.33
Nodes (5): COMMON, meta, out, READERS, SCHEMA

### Community 151 - "Invisible account lockout (5 fails -> 15 min, enumeration resistance)"
Cohesion: 0.33
Nodes (6): Invisible account lockout (5 fails -> 15 min, enumeration resistance), Unified error envelope (code, message, request_id), Per-IP rate limiting (Redis fixed window), Request lifecycle (edge -> middleware -> rate limit -> deps -> router), Client IP resolution (resolve_client_ip, TRUSTED_PROXY_CIDRS, XFF overwrite), EmailStr rejects reserved domains (login 422 on .test/.local/.arpa)

### Community 152 - "_raw_probe"
Cohesion: 0.20
Nodes (10): _app_role_dsn(), A libpq DSN for the RLS-enforced application role (no ORM, no guard)., Run one statement as ``nexusops_app`` with an explicit GUC. Parameterized like…, Raw SQL as the application role: the policies alone return nothing. Written…, Adding ``org_id`` to ``audit_logs`` must not have opened a way to edit it. The…, ``WITH CHECK`` is not decoration: an unlucky INSERT cannot cross tenants., _raw_probe(), test_audit_trail_is_still_append_only_after_tenancy() (+2 more)

### Community 153 - "get_secret_detail"
Cohesion: 0.25
Nodes (9): _collect_refs(), _detail(), get_secret_detail(), Any, Serialise one version's metadata. ``ciphertext`` is never included., Metadata for one secret including the rotator's email when known., Backwards-compatible wrapper around :func:`config_service.collect_secret_refs`., Serialise secret metadata. No value-bearing field may appear here. (+1 more)

### Community 154 - "nexusops-draft.mjs"
Cohesion: 0.40
Nodes (4): DOCS, meta, SPINE, VERIFY_RULES

### Community 155 - "SecretOut"
Cohesion: 0.25
Nodes (8): Secret metadata — deliberately excludes any value-bearing field., SecretOut, 1.1 Storage and crypto, 1.2 Data model, 1.3 API surface (metadata-only reads), 1.6 Gap list (Phase 2 status), 1. Current state, 9. Leak-path table

### Community 156 - "nexusops-challenge.mjs"
Cohesion: 0.33
Nodes (5): CHALLENGE_COMMON, meta, RESEARCH_COMMON, SCHEMA, TASKS

### Community 157 - "test_agent_ingestion.py"
Cohesion: 0.30
Nodes (10): _enrolled(), _heartbeat(), Agent ingest pipeline: hello, heartbeat, staleness transitions, events., A container absent from a later heartbeat is gone from the daemon., A payload at the agent's cap may be truncated — absence proves nothing., test_heartbeat_at_container_cap_skips_reconciliation(), test_heartbeat_removes_vanished_containers(), test_heartbeat_updates_status_metrics_and_containers() (+2 more)

### Community 158 - "AgentContainerIn"
Cohesion: 0.23
Nodes (20): AgentContainerIn, AgentHeartbeatIn, Observed container state reported by an agent., Periodic metrics + observed containers from an enrolled agent., _container(), _heartbeat(), parametrize, Unit tests for agent-facing schemas (heartbeat + container payloads). (+12 more)

### Community 159 - "test_run_async_publishes_frames_scheduled_by_the_commit_hook"
Cohesion: 0.29
Nodes (5): _FakeDb, Stands in for an ``AsyncSession`` whose only job here is ``sync_session``. A…, The shape of a worker task whose last statement is a commit., test_run_async_publishes_frames_scheduled_by_the_commit_hook(), commit_then_return()

### Community 160 - "strip_query"
Cohesion: 0.33
Nodes (4): Drop the query string so signed tokens never appear in error text., Public alias: redact any query string from a URL before display/persist., strip_query(), field_serializer

### Community 161 - "register_exception_handlers"
Cohesion: 0.24
Nodes (9): _error_payload(), Any, FastAPI, Request, register_exception_handlers(), handle_app_error(), handle_http_exception(), handle_unexpected() (+1 more)

### Community 162 - "register_agent_hello"
Cohesion: 0.33
Nodes (6): Mark the agent enrolled and persist its static host facts., register_agent_hello(), 7.1 Version visibility (fix the stub), 7.2 Out-of-date handling, 7.3 Future: self-update, 7. Versioning & upgrades

### Community 163 - "_invite"
Cohesion: 0.33
Nodes (6): _invite(), ``sessions`` has no tenant column: the owning membership is the boundary.…, Invite a fresh account into the caller's organization and log it in., The user directory is "who is in this organization", not "who exists".…, test_member_directory_only_ever_shows_the_active_tenant(), test_one_tenants_session_list_and_revocation_stop_at_its_members()

### Community 164 - "journey.spec.ts"
Cohesion: 0.29
Nodes (4): ADMIN, formLogin(), uiGoto(), UNIQUE

### Community 165 - "_FakeAsyncClient"
Cohesion: 0.22
Nodes (3): _FakeAsyncClient, _FakeRequestObj, Scripted httpx.AsyncClient: responses keyed by absolute request URL.

### Community 167 - "resolve_auth"
Cohesion: 0.09
Nodes (31): _attach_organization(), get_identity(), get_optional_user(), _load_organization(), membership_for_org(), _org_id_from_header(), AsyncSession, DbSessionDep (+23 more)

### Community 168 - "AgentHelloIn"
Cohesion: 0.29
Nodes (7): AgentHelloIn, First contact from an agent after enrollment; fills static host facts., test_agent_hello_bounds(), test_agent_hello_minimal(), 4.1 Wire contract today (real, pinned by tests), 4.2 v2 additions, 4. Heartbeat contract v2

### Community 170 - "3. Agent lifecycle"
Cohesion: 0.40
Nodes (5): 3.1 Current state (real), 3.3 Token storage & rotation with dual-token grace, 3.4 Revocation semantics — fixing the 401 hot-loop, 3.5 Reconnect / offline states, 3. Agent lifecycle

### Community 171 - "get_meta"
Cohesion: 0.40
Nodes (5): get_meta(), DbSessionDep, get, Public metadata; identity fields appear only for valid credentials., OptionalUser

### Community 172 - "ApplicationBase"
Cohesion: 0.40
Nodes (4): ApplicationBase, Any, field_validator, Shared application fields; ``build_config`` is a free-form dict.

### Community 173 - "_pace"
Cohesion: 0.67
Nodes (3): _pace(), Deterministic per-line delay between 0.05s and 0.35s., test_pace_bounds()

### Community 174 - "4. Operations framework (added in this pass)"
Cohesion: 0.67
Nodes (3): OperationSpec, Everything the control plane needs to know about one operation type.…, 4. Operations framework (added in this pass)

### Community 176 - "sweep_servers"
Cohesion: 0.50
Nodes (4): task, Flag silent servers OFFLINE, recover returning ones. Safe to overlap., sweep_servers(), _run()

### Community 179 - "_run"
Cohesion: 0.33
Nodes (7): _containers_for(), task, Deterministic smooth value in [base-amplitude, base+amplitude]., Stable per-server container set; one container cycles EXITED occasionally., simulation_tick(), _run(), _wave()

### Community 180 - "websocket_endpoint"
Cohesion: 0.67
Nodes (3): websocket, Hand the socket to the hub (auth handshake handled there)., websocket_endpoint()

### Community 181 - "20261009_1000-c3d4e5f6a7b8_enforce_secret_version_integrity.py"
Cohesion: 0.48
Nodes (6): _clear_app_role_guc(), downgrade(), Phase 2.1 — enforce append-only ``secret_versions`` in the database. Phase 2…, Publish the app-role name to the migration GUC the revoke block reads., _set_app_role_in_guc(), upgrade()

### Community 184 - "get_settings"
Cohesion: 0.11
Nodes (26): _quoted_list(), Add the operations framework table (node-agent-architecture.md §5). One tenant-…, upgrade(), downgrade(), _drop_constraint(), _quoted_list(), Phase 2 — projects & environments: env promotion, config, secret versions. This…, upgrade() (+18 more)

### Community 187 - "permissions_for_role"
Cohesion: 0.40
Nodes (5): effective_permissions(), permissions_for_role(), User, Sorted permission codenames a role grants; ``*`` expands to the registry.…, Instance-level permissions for a user (legacy default-role view). Deliberately…

### Community 188 - "instant_pacing"
Cohesion: 0.40
Nodes (4): instant_pacing(), fixture, MonkeyPatch, Remove the per-line sleeps; pacing bounds are asserted separately.

## Knowledge Gaps
- **421 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+416 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1845 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `6. Tooling: reproducible e2e` connect `sweep_session` to `core/tenancy.py`, `client.ts`, `_is_same_origin`, `_entity_exists`, `operation_service.py`, `login`?**
  _High betweenness centrality (0.235) - this node is a cross-community bridge._
- **Why does `useEventStream()` connect `client.ts` to `AuthContext.tsx`, `App.tsx`, `apiGet`, `ServerDetailPage.tsx`, `sweep_session`?**
  _High betweenness centrality (0.235) - this node is a cross-community bridge._
- **Why does `TenancyScopeError` connect `core/tenancy.py` to `test_operations.py`, `publish`, `AuthContext`, `test_tenant_concurrency.py`, `log_service.py`, `sweep_session`, `notification_service.py`?**
  _High betweenness centrality (0.103) - this node is a cross-community bridge._
- **Are the 79 inferred relationships involving `AuthContext` (e.g. with `TenancyScopeError` and `MembershipStatus`) actually correct?**
  _`AuthContext` has 79 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `APIModel` (e.g. with `OperationSpec` and `test_specs_reject_unknown_params()`) actually correct?**
  _`APIModel` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `apiGet()` (e.g. with `ContainerDetailPage.test.tsx` and `mockApi()`) actually correct?**
  _`apiGet()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `meta`, `SCHEMA`, `RESEARCH_COMMON` to the rest of the system?**
  _421 weakly-connected nodes found - possible documentation gaps or missing edges._