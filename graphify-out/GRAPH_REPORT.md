# Graph Report - nexusops  (2026-10-09)

## Corpus Check
- 309 files · ~277,218 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: (none) 8, .example 1, .service 1)

## Summary
- 4483 nodes · 13215 edges · 184 communities (159 shown, 25 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1084 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0261fdb0`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- AuthContext.tsx
- project_service.py
- App.tsx
- apiGet
- user_service.py
- types.ts
- resolve_client_ip
- apiPost
- UsersPage.tsx
- models/__init__.py
- test_operations.py
- ServerDetailPage.tsx
- APIModel
- client.ts
- projects.py
- incidents.py
- deployment_engine.py
- SimulatedDockerProvider
- test_tasks_util.py
- rollback_secret
- test_deployments_simulated.py
- list_containers
- metrics_service.py
- get_settings
- test_rate_limit.py
- monitor_service.py
- Node & Agent Architecture
- test_agent_backoff.py
- SimulatedDeploymentRunner
- nexusops_agent.py
- integration/conftest.py
- auth_service.py
- container_service.py
- docker_host_service.py
- docker_hosts.py
- test_ws_hub.py
- monitors.py
- v1/search.py
- AuthContext
- v1/channels.py
- DockerProvider
- test_monitor_transport.py
- AgentContainerIn
- @tanstack/react-query
- docker_real.py
- test_permissions.py
- Conflict
- ServerOut
- BadRequest
- secret_service.py
- roles.py
- test_schemas_server.py
- apikeys.py
- test_migration_phase2.py
- v1/auth.py
- _guard
- incident_service.py
- alembic
- notification_service.py
- helpers.py
- compilerOptions
- v1/deployments.py
- test_error_logging.py
- OrganizationStatus
- test_phase2_environments.py
- seed.py
- test_schema_redaction.py
- pagination.py
- encrypt_str
- package.json
- list_events
- test_secrets.py
- README.md - NexusOps overview
- models/base.py
- api service (FastAPI / uvicorn :8000)
- UnprocessableEntity
- monitor_transport.py
- pytest
- redact_mapping
- test_phase2_secrets.py
- queue_deployment
- Settings
- PageParams
- tests/conftest.py
- test_agent_contract.py
- list_sessions
- devDependencies
- NotFound
- list_audit_logs
- test_migration_drift.py
- container.py
- validate_config
- _apply_agent_entry
- test_tenant_isolation.py
- error_of
- alerts.py
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- fixtures.ts
- DockerProviderError
- AppError
- Secrets Architecture
- env.py
- alert_service.py
- EnvironmentBase
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- _validate_resolution
- enums.py
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- ScopedSession
- create_organization
- test_app_gating.py
- log_service.py
- scripts
- deps.py
- test_tenancy_allowlist.py
- _entity_exists
- dependencies
- DeploymentDetailPage.test.tsx
- generate_secrets.sh
- notification_sender.py
- test_servers_and_audit.py
- bearer
- middleware.py
- .__init__
- uuid
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
- flush_pending_publishes
- publish
- postgres service (PostgreSQL 17, loopback :5433)
- assert_error_code
- nexusops-understand.mjs
- Invisible account lockout (5 fails -> 15 min, enumeration resistance)
- .dispatch
- test_notifications.py
- nexusops-draft.mjs
- 20261004_1200-e7c4a2b9d1f3_add_operations_framework.py
- nexusops-challenge.mjs
- test_agent_ingestion.py
- test_schemas_agent.py
- Session
- AgentClient
- register_exception_handlers
- lax
- Domain Model — NexusOps as a Multi-Tenant Platform
- journey.spec.ts
- _FakeAsyncClient
- create_app
- resolve_auth
- AgentHelloIn
- .__tablename__
- ProjectUpdate
- get_meta
- ApplicationBase
- NexusOps — Phase 1 (Multi-Tenancy) Report
- 3. Agent lifecycle
- big_serial_pk
- validate_endpoint_url
- scratch_database
- UUID
- schemas/meta.py
- websocket_endpoint
- _FakeSession
- ApplicationCreate
- ApplicationUpdate

## God Nodes (most connected - your core abstractions)
1. `AuthContext` - 136 edges
2. `APIModel` - 118 edges
3. `apiGet()` - 82 edges
4. `get_settings()` - 72 edges
5. `NotFound` - 67 edges
6. `record()` - 65 edges
7. `publish()` - 61 edges
8. `apiPost()` - 60 edges
9. `useToast()` - 58 edges
10. `ApiError` - 57 edges

## Surprising Connections (you probably didn't know these)
- `0. What shipped (Phase 1)` --references--> `resolve_auth()`  [INFERRED]
  docs/authorization.md → backend/app/api/deps.py
- `6. Enforcement mechanics (unchanged patterns, one addition)` --references--> `resolve_auth()`  [INFERRED]
  docs/authorization.md → backend/app/api/deps.py
- `2. Org resolution on every request` --references--> `resolve_auth()`  [INFERRED]
  docs/multi-tenancy.md → backend/app/api/deps.py
- `3. Cross-cutting decisions` --references--> `require_permission()`  [INFERRED]
  docs/domain-model.md → backend/app/api/deps.py
- `10. Phase 7 — Teams, grants & custom roles` --references--> `require_permission()`  [INFERRED]
  docs/product-roadmap.md → backend/app/api/deps.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three authentication credential families with centralized permission checks** — docs_api_md_auth, docs_api_md_refresh_rotation, docs_api_md_api_keys, docs_agent_md_enrollment_token, docs_api_md_permission_model [EXTRACTED 1.00]
- **NexusOps compose stack services** — docker_compose_yml_nexusops_stack, docker_compose_yml_postgres_service, docker_compose_yml_redis_service, docker_compose_yml_mailpit_service, docker_compose_yml_api_service, docker_compose_yml_worker_service, docker_compose_yml_scheduler_service, docker_compose_yml_frontend_service, docker_compose_yml_nginx_service [EXTRACTED 1.00]
- **WebSocket real-time fan-out spine** — docs_architecture_md_websocket_hub, docs_api_md_websocket_channels, docker_compose_yml_redis_service, docs_architecture_md_event_bus, readme_react_spa [INFERRED 0.85]

## Communities (184 total, 25 thin omitted)

### Community 0 - "AuthContext.tsx"
Cohesion: 0.04
Nodes (47): getActiveOrgId(), setAccessToken(), setActiveOrgId(), Membership, SearchResult, User, LoginRoute(), RequireAuth() (+39 more)

### Community 1 - "project_service.py"
Cohesion: 0.11
Nodes (55): paginate(), AsyncSession, Execute *stmt* with limit/offset and return ``(rows, total)``., Application, DeploymentEnvironment, Project, A **project-scoped** deployment environment (Phase 2 promotion). The…, Any (+47 more)

### Community 2 - "App.tsx"
Cohesion: 0.04
Nodes (95): DashboardSummary, DeploymentOut, DeploymentStepOut, Page, ProjectOut, AlertsPage, ApiKeysPage, App() (+87 more)

### Community 3 - "apiGet"
Cohesion: 0.09
Nodes (36): apiGet(), IncidentEventOut, MonitorDetailPage, formatDateTime(), formatDurationMs(), formatRelative(), truncate(), AlertsPage() (+28 more)

### Community 4 - "user_service.py"
Cohesion: 0.12
Nodes (40): MembershipStatus, _apply_deactivation(), _assert_not_last_active_member(), _assert_not_last_active_superadmin(), create_user(), deactivate_user(), get_by_email(), get_member() (+32 more)

### Community 5 - "types.ts"
Cohesion: 0.04
Nodes (43): AlertOut, ApiKeyOut, ChannelOut, ContainerOut, DeliveryOut, DeploymentLogLine, DeploymentStatus, DockerHostOut (+35 more)

### Community 6 - "resolve_client_ip"
Cohesion: 0.17
Nodes (22): _is_trusted(), _parse_networks(), Request, Client-IP resolution behind chained reverse proxies. The API never takes TCP…, Parse a comma-separated CIDR list; malformed entries are skipped., Real client address for *request* per the trust model above., resolve_client_ip(), make_request() (+14 more)

### Community 7 - "apiPost"
Cohesion: 0.06
Nodes (55): apiDelete(), apiPatch(), apiPost(), ApplicationOut, ENVIRONMENT_TYPE_LABELS, EnvironmentDetailOut, EnvironmentOut, EnvironmentType (+47 more)

### Community 8 - "UsersPage.tsx"
Cohesion: 0.07
Nodes (30): LoginPage, OrganizationRequiredPage, UsersPage, CheckboxField(), CheckboxFieldProps, FieldAria, FieldBaseProps, PasswordField() (+22 more)

### Community 9 - "models/__init__.py"
Cohesion: 0.18
Nodes (25): _org_scoped_classes(), Mapped classes marked :class:`~app.models.base.OrgScoped`. Reads the mapper…, Base, OrgScoped, Base for all ORM models with stable constraint naming for Alembic., Mixin marking a table as **organization-owned** (Phase 1 tenancy). Set the…, TimestampMixin, RolePermission (+17 more)

### Community 10 - "test_operations.py"
Cohesion: 0.03
Nodes (119): dispose_engine(), get_engine(), get_sessionmaker(), async_sessionmaker, AsyncEngine, AsyncSession, apply_scope_to_session(), current_org() (+111 more)

### Community 11 - "ServerDetailPage.tsx"
Cohesion: 0.09
Nodes (36): MetricPoint, ServerDetailPage, ServerListPage, ChartSeries, LineChart(), LineChartProps, PAD, buildServerPayload() (+28 more)

### Community 12 - "APIModel"
Cohesion: 0.03
Nodes (63): ApiKeyCreateRequest, APIModel, BaseModel, Base for request/response models: ORM mode + strict-ish population., EventTypeOut, Canonical event type with its human description., HealthOut, Health / readiness schemas. (+55 more)

### Community 13 - "client.ts"
Cohesion: 0.05
Nodes (46): API_BASE, ApiError, apiRequest(), buildUrl(), extractError(), getAccessToken(), onActiveOrgChange(), ORGANIZATION_HEADER (+38 more)

### Community 14 - "projects.py"
Cohesion: 0.13
Nodes (45): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+37 more)

### Community 15 - "incidents.py"
Cohesion: 0.14
Nodes (32): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+24 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.14
Nodes (45): deployment_log_channel(), Deployment, DeploymentStep, AlertSeverity, DeploymentStatus, EventLevel, StepStatus, _audit_resolution_failed() (+37 more)

### Community 17 - "SimulatedDockerProvider"
Cohesion: 0.08
Nodes (31): LogEntry, Any, Plausible numbers derived from the row plus time-based sine noise., Implements :class:`DockerProvider` semantics against DB rows., Attach already-fetched log rows so ``logs()`` can replay them., _seed_int(), SimulatedDockerProvider, _log_entry() (+23 more)

### Community 18 - "test_tasks_util.py"
Cohesion: 0.36
Nodes (8): _answer(), _boom(), _nested(), Unit tests for the Celery-task async bridge (pure asyncio, no broker)., test_run_async_awaits_nested_coroutines(), test_run_async_is_repeatable_per_invocation(), test_run_async_propagates_exceptions(), test_run_async_returns_coroutine_result()

### Community 19 - "rollback_secret"
Cohesion: 0.14
Nodes (26): create_secret(), delete_secret(), get_secret(), list_secret_versions(), list_secrets(), DbSession, delete, get (+18 more)

### Community 20 - "test_deployments_simulated.py"
Cohesion: 0.15
Nodes (28): execute_deployment(), Run one deployment to a terminal state. Never raises; safe to re-run., get_environment(), _as_worker(), _delivery_chain(), _owner_ctx(), _queue(), _queued_with_recorder() (+20 more)

### Community 21 - "list_containers"
Cohesion: 0.09
Nodes (34): _action_route(), _endpoint(), _ev(), get_container(), _like_pattern(), list_container_logs(), list_containers(), _load_container() (+26 more)

### Community 22 - "metrics_service.py"
Cohesion: 0.09
Nodes (41): get_dashboard_summary(), get_latest_server_metrics(), get_server_metrics(), CurrentUser, DbDep, Depends, get, UUID (+33 more)

### Community 23 - "get_settings"
Cohesion: 0.07
Nodes (58): argon2, argon2_exceptions, fail_on_bad_config(), get_settings(), Central configuration. All runtime configuration flows through this module so…, Return the cached settings singleton., Exit immediately with a readable message if configuration is invalid. Also…, Runtime DSN (application role, RLS enforced) for Celery/script sync paths. (+50 more)

### Community 24 - "test_rate_limit.py"
Cohesion: 0.05
Nodes (47): RateLimited, _memory_count_and_ttl(), Request, rate_limit(), _dependency(), Fixed-window counter backed by process memory. Returns (count, ttl)., Return a dependency enforcing *limit* requests per window per IP. With…, _clean_memory_windows() (+39 more)

### Community 25 - "monitor_service.py"
Cohesion: 0.16
Nodes (35): MonitorStatus, Monitor, _active_incident(), _audit(), claim_due_monitors(), create_monitor(), delete_monitor(), _emit() (+27 more)

### Community 26 - "Node & Agent Architecture"
Cohesion: 0.14
Nodes (14): 1. Scope and stance, 6.1 Token scope, 6.2 docker.sock is root-equivalent, 6.3 Transport: HTTPS-only, 6.4 No arbitrary exec, 6. Agent security, 7.2 Out-of-date handling, 7.3 Future: self-update (+6 more)

### Community 27 - "test_agent_backoff.py"
Cohesion: 0.16
Nodes (20): agent_fixture(), _install_sleep(), fake_sleep(), _load_agent(), _patch_host(), Any, fixture, MonkeyPatch (+12 more)

### Community 28 - "SimulatedDeploymentRunner"
Cohesion: 0.06
Nodes (64): LogLevel, _commit_short(), DeploymentRunner, _pace(), Exception, Protocol, Deployment runner port plus a faithful simulated implementation.…, Stream output lines for *step_name*; raise StepFailure to fail it. (+56 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.09
Nodes (30): build_heartbeat(), collect_container_stats(), collect_containers(), cpu_percent_since(), disk_stats(), _docker_request(), _interruptible_sleep(), load1() (+22 more)

### Community 30 - "integration/conftest.py"
Cohesion: 0.16
Nodes (18): close_redis(), _clean_slate(), client(), _ensure_database(), _migrated_database(), org_db(), fixture, Integration fixtures: migrated test database, per-test clean slate, API client.… (+10 more)

### Community 31 - "auth_service.py"
Cohesion: 0.10
Nodes (49): active_memberships(), Membership, The user's memberships in non-suspended organizations, oldest first. Reads only…, System scope bound to *db*, for rows that have no organization. Used by exactly…, system_write_scope(), ActorType, Opaque refresh token; only its SHA-256 hash is stored. Rotation chain: on…, RefreshToken (+41 more)

### Community 32 - "container_service.py"
Cohesion: 0.11
Nodes (35): AuditResult, ContainerHealth, ContainerStatus, Container, Observed container state mirrored from an agent or docker provider., is_simulated(), provider_for(), Return the provider matching *host*'s endpoint configuration. (+27 more)

### Community 33 - "docker_host_service.py"
Cohesion: 0.12
Nodes (37): DockerHostStatus, DockerHost, DockerHostCreate, DockerHostPingOut, DockerHostUpdate, Result of probing a host's provider endpoint., Payload for registering a docker host., Partial update payload; only supplied fields change. (+29 more)

### Community 34 - "docker_hosts.py"
Cohesion: 0.09
Nodes (46): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+38 more)

### Community 35 - "test_ws_hub.py"
Cohesion: 0.19
Nodes (22): _connection(), _drain(), _event_frame(), _fake_sessionmaker(), hub(), _Org, Any, fixture (+14 more)

### Community 36 - "monitors.py"
Cohesion: 0.14
Nodes (36): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+28 more)

### Community 37 - "v1/search.py"
Cohesion: 0.09
Nodes (40): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+32 more)

### Community 38 - "AuthContext"
Cohesion: 0.05
Nodes (82): AuthContext, Resolved identity plus the organization this request acts in.…, agent_heartbeat(), agent_hello(), claim_operation(), _presented_token(), DbDep, post (+74 more)

### Community 39 - "v1/channels.py"
Cohesion: 0.15
Nodes (27): create_channel(), delete_channel(), get_channel(), list_channels(), list_deliveries(), DbDep, delete, Depends (+19 more)

### Community 40 - "DockerProvider"
Cohesion: 0.09
Nodes (12): DockerProvider, Any, datetime, Protocol, List containers visible to the provider., Inspect a single container by id (short ids allowed)., List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``., List volumes: keys ``name``, ``driver``, ``mountpoint``. (+4 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.13
Nodes (34): CheckResult, HTTPMonitorTransport, Deterministic fake checker for ``sim://`` monitors and demo environments.…, Real HTTP(S) probe using httpx with per-monitor settings. Redirects are…, SimulatedTransport, _check(), clock(), FakeClock (+26 more)

### Community 42 - "AgentContainerIn"
Cohesion: 0.26
Nodes (12): AgentContainerIn, field_validator, Observed container state reported by an agent., _container(), parametrize, test_allowed_container_statuses(), test_bogus_status_string_rejected(), test_container_id_pattern_accepts() (+4 more)

### Community 43 - "@tanstack/react-query"
Cohesion: 0.03
Nodes (80): CheckOut, IncidentOut, MonitorOut, Role, MetaInfo, SimulatedChip(), mocks, Toast (+72 more)

### Community 44 - "docker_real.py"
Cohesion: 0.09
Nodes (28): ContainerInfo, ContainerStats, Normalized view of a container as reported by any provider., Point-in-time resource usage snapshot., _as_float(), _compute_stats(), _cpu_percent(), _network_bytes() (+20 more)

### Community 45 - "test_permissions.py"
Cohesion: 0.05
Nodes (38): permission_exists(), Check an API-key scope list against a required permission. Supports exact match…, scope_matches(), _auth_context(), _FakeCtx, parametrize, Unit tests for the permission registry, scope matching and RBAC gate., Duck-typed stand-in for AuthContext. (+30 more)

### Community 46 - "Conflict"
Cohesion: 0.15
Nodes (25): Conflict, create_role(), delete_role(), effective_permissions(), get_role(), list_roles(), permissions_for_role(), AsyncSession (+17 more)

### Community 47 - "ServerOut"
Cohesion: 0.33
Nodes (5): Full server view with recent timeline events and container counts., Server as listed in collections. Never exposes the agent token hash., ServerDetail, ServerOut, computed_field

### Community 48 - "BadRequest"
Cohesion: 0.17
Nodes (20): BadRequest, assert_safe_tcp_endpoint(), ValueError, SSRF guard applied to every operator-supplied outbound URL. Monitors and…, Validate a ``tcp://`` docker host endpoint for outbound connection. Docker…, Internal signal: a specific SSRF rule matched (never shown to clients)., UrlRejected, _validate_syntax() (+12 more)

### Community 49 - "secret_service.py"
Cohesion: 0.13
Nodes (37): An encrypted configuration value, scoped to org, project or environment.…, One immutable value of a :class:`Secret` — append-only history. A row is…, Secret, SecretVersion, _actor_type(), create_secret(), delete_secret(), _detail() (+29 more)

### Community 50 - "roles.py"
Cohesion: 0.11
Nodes (29): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, delete, get (+21 more)

### Community 51 - "test_schemas_server.py"
Cohesion: 0.09
Nodes (43): create_server(), delete_server(), get_server(), list_tags(), DbDep, delete, get, post (+35 more)

### Community 52 - "apikeys.py"
Cohesion: 0.16
Nodes (18): create_api_key(), list_api_keys(), CurrentUser, DbSessionDep, delete, get, post, Request (+10 more)

### Community 53 - "test_migration_phase2.py"
Cohesion: 0.15
Nodes (23): alembic_config, alembic_script, _alembic_config(), _exec(), _migration_dsn(), _owner_dsn(), Phase 2 migration (`b2c3d4e5f6a7`) against realistic legacy data. The promotion…, Upgrade ``database`` to ``revision`` through the app's own settings path.… (+15 more)

### Community 54 - "v1/auth.py"
Cohesion: 0.09
Nodes (46): change_password(), _clear_refresh_cookie(), _cookies_secure(), login(), logout(), me(), _optional_actor(), AsyncSession (+38 more)

### Community 55 - "_guard"
Cohesion: 0.11
Nodes (23): _apply_scope_guc(), _desired_guc(), _guard(), _has_org_predicate(), install_tenancy_guards(), _mappers_of(), org_scoped_table_names(), Any (+15 more)

### Community 56 - "incident_service.py"
Cohesion: 0.22
Nodes (23): IncidentEventKind, IncidentSeverity, IncidentStatus, Incident, acknowledge(), _add_event(), add_note(), get_incident() (+15 more)

### Community 57 - "alembic"
Cohesion: 0.05
Nodes (24): alembic, _app_role_credentials(), _assert_fully_backfilled(), _backfill_org_ids(), _drop_constraint(), add tenancy foundation Phase 1 of the platform roadmap: organizations,…, Carry a value into a PL/pgSQL block. ``CREATE ROLE``/``ALTER ROLE`` are utility…, Application role name/password from settings (never hard-coded). (+16 more)

### Community 58 - "notification_service.py"
Cohesion: 0.08
Nodes (58): ChannelType, DeliveryStatus, NotificationChannel, A delivery target (email address / webhook endpoint). ``config_ciphertext``…, ChannelBase, ChannelCreate, ChannelUpdate, EmailConfig (+50 more)

### Community 59 - "helpers.py"
Cohesion: 0.12
Nodes (30): cookie_attributes(), login_account(), AsyncClient, Response, Pure helpers for journey tests: payloads, auth shortcuts, cookie parsing., Login and unpack tokens, the raw cookie header and the user object., Bootstrap owner account + session; returns ``(credentials, login_result)``. The…, Register a user; returns ``(request_payload, response_body)``. (+22 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "v1/deployments.py"
Cohesion: 0.10
Nodes (44): _attribute_step_idx(), cancel_deployment(), _emails_for(), get_deployment(), list_application_deployments(), list_deployment_logs(), _list_deployments(), _parse_sort() (+36 more)

### Community 62 - "test_error_logging.py"
Cohesion: 0.22
Nodes (4): Regression: the catch-all 500 handler must not log raw exception text.…, _SpyLogger, test_unhandled_exception_handler_logs_class_not_message(), fastapi_testclient

### Community 63 - "OrganizationStatus"
Cohesion: 0.12
Nodes (21): create_organization(), list_my_organizations(), CurrentUser, DbSessionDep, get, IdentityUser, patch, post (+13 more)

### Community 64 - "test_phase2_environments.py"
Cohesion: 0.18
Nodes (22): _environment(), _project(), parametrize, Phase 2: project-scoped environments, config layering, and their isolation. The…, Uniqueness is ``(project_id, slug)`` — not instance-wide., The update path is validated too (the pre-Phase-2 gap)., Knowing an environment UUID is not access: the project link must hold., Another tenant cannot reach the project, its environments, or its detail. (+14 more)

### Community 65 - "seed.py"
Cohesion: 0.13
Nodes (27): UserStatus, ApiKey, Permission, Machine credential. Raw key shown once at creation; hash stored. A key is bound…, A named permission set. ``org_id`` is NULL for every row in v1 — the five…, Role, User, Membership (+19 more)

### Community 66 - "test_schema_redaction.py"
Cohesion: 0.18
Nodes (17): is_sensitive_header(), mask_sensitive_headers(), True when *name* looks like it carries a credential (Authorization etc.)., Return a copy of *headers* with sensitive values replaced by a mask., mask_target(), Human-readable masked target safe to expose over the API. For webhook families…, _monitor_out(), Outbound-schema redaction: monitor probe credentials and webhook targets.… (+9 more)

### Community 67 - "pagination.py"
Cohesion: 0.15
Nodes (25): Cursor, cursor_params(), CursorPage, CursorParams, decode_cursor(), encode_cursor(), page_params(), datetime (+17 more)

### Community 68 - "encrypt_str"
Cohesion: 0.09
Nodes (28): decrypt_str(), digest_of(), encrypt_str(), _fernet(), Short server-verifiable digest used for change detection display. HMAC-SHA256…, parametrize, test_decrypt_with_wrong_ciphertext_raises_value_error(), test_digest_length_and_determinism() (+20 more)

### Community 69 - "package.json"
Cohesion: 0.13
Nodes (15): name, private, type, version, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom (+7 more)

### Community 70 - "list_events"
Cohesion: 0.11
Nodes (20): _decode_cursor(), _encode_cursor(), list_event_types(), list_events(), datetime, DbSession, Depends, get (+12 more)

### Community 71 - "test_secrets.py"
Cohesion: 0.10
Nodes (28): _collect_refs(), Exception, A ``${secret:KEY}`` reference could not be resolved. Fail-closed. Carries…, One successfully resolved reference: metadata for audit, no value., Backwards-compatible wrapper around :func:`config_service.collect_secret_refs`., Resolve every ``${secret:KEY}`` reference an environment's config names.…, resolve_secrets_for_environment(), SecretReference (+20 more)

### Community 72 - "README.md - NexusOps overview"
Cohesion: 0.06
Nodes (58): make(), docker-compose.dev.yml - dev overlay, docker-compose.docker-sock.yml - docker socket override, docker-compose.yml - full stack definition, docs/agent.md - agent guide, docs/api.md - API guide, Append-only audit log (Postgres BEFORE UPDATE OR DELETE trigger), docs/architecture.md - system architecture (+50 more)

### Community 73 - "models/base.py"
Cohesion: 0.15
Nodes (20): json_column(), org_id_column(), datetime, UUID, Declarative base, shared mixins and column helpers., A plain ``org_id`` column for the few tables that carry one without taking part…, status_check(), _utcnow() (+12 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "UnprocessableEntity"
Cohesion: 0.18
Nodes (21): UnprocessableEntity, assert_safe_url(), _raise_block(), Validate *url* for outbound requests; return the parsed URL or raise 422.…, Reject non-empty values that are not valid IPv4/IPv6 addresses., _validate_ip(), install_dns(), Exception (+13 more)

### Community 76 - "monitor_transport.py"
Cohesion: 0.09
Nodes (25): assert_safe_url_async(), Async wrapper around :func:`assert_safe_url`; DNS runs off the loop., CheckOutcome, coerce_headers(), _decode(), get_transport(), MonitorTransport, Any (+17 more)

### Community 77 - "pytest"
Cohesion: 0.18
Nodes (12): created_at server defaults must evaluate per insert, not at table creation., Regression: system_events and audit_logs shipped with DEFAULT 'now()' (quoted…, test_audit_and_event_created_at_defaults_are_dynamic(), _create_monitor(), Monitor checks driving the full down -> incident -> recovery lifecycle., Regression: probe headers and URL query credentials never leave the API. Probe…, A monitor's checks, incidents and timeline all live in its organization, so the…, test_check_now_endpoint_runs_immediately() (+4 more)

### Community 78 - "redact_mapping"
Cohesion: 0.22
Nodes (13): _is_sensitive_key(), Substring match on a normalised key so header-style names are caught too.…, Return a copy of *data* with sensitive values replaced. Used by audit metadata…, redact_mapping(), parametrize, Unit tests for app.core.logging redaction (pure functions only)., test_case_insensitive_substring_match(), test_flat_sensitive_keys_redacted() (+5 more)

### Community 79 - "test_phase2_secrets.py"
Cohesion: 0.19
Nodes (21): _env(), _project(), Phase 2 secrets: layered scope, immutable versions, rollback, isolation. Two…, Two racing rotations must both be kept and never share a version number., Another tenant cannot read, rotate, roll back or even enumerate the secret., The documented example: same key at three scopes; most specific wins., A ref declared in the project base config resolves for its environments., _resolved() (+13 more)

### Community 80 - "queue_deployment"
Cohesion: 0.12
Nodes (20): _after_commit_enqueue(), _after_rollback_drop(), _enqueue_after_commit(), _enqueue_task(), Any, queue_deployment(), Hand the deployment to Celery; broker downtime is tolerated (beat sweeps)., Drop stashed ids on rollback — otherwise a LATER, unrelated commit on the same… (+12 more)

### Community 81 - "Settings"
Cohesion: 0.12
Nodes (7): field_validator, model_validator, Whether the runtime connection is the RLS-enforced application role. False…, Username from :attr:`database_url`, or ``None`` if it is unparseable., Validated application settings (loaded from environment / .env)., Settings, BaseSettings

### Community 82 - "PageParams"
Cohesion: 0.13
Nodes (26): list_servers(), Depends, List servers with filters, search and pagination., create_user(), deactivate_user(), get_user(), list_users(), CurrentUser (+18 more)

### Community 83 - "tests/conftest.py"
Cohesion: 0.20
Nodes (8): configure_test_env(), Test bootstrap: pin every cached setting BEFORE the first ``app`` import. The…, KEY=VALUE pairs from the repo .env (first definition wins); never logged., Export the exact settings the app caches; host values cannot leak through., _read_dot_env(), base64, os, sys

### Community 84 - "test_agent_contract.py"
Cohesion: 0.18
Nodes (16): agent_fixture(), _load_agent(), _patch_stats(), Any, fixture, MonkeyPatch, Contract tests: the shipped agent's payloads must satisfy the ingest schemas.…, One-shot docker stats reduce to cpu/mem/limit fields the schema accepts, with… (+8 more)

### Community 85 - "list_sessions"
Cohesion: 0.20
Nodes (11): list_sessions(), CurrentUser, DbSessionDep, delete, get, Request, UUID, Active sessions of this organization's members. Defaults to the caller's own;… (+3 more)

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "NotFound"
Cohesion: 0.04
Nodes (93): cancel_operation(), create_operation(), get_operation(), list_operations(), DbDep, Depends, get, post (+85 more)

### Community 88 - "list_audit_logs"
Cohesion: 0.29
Nodes (7): list_audit_logs(), datetime, DbSession, Depends, get, PageParamsDep, Newest-first audit trail with optional filters. No write routes exist for this…

### Community 89 - "test_migration_drift.py"
Cohesion: 0.25
Nodes (7): alembic_autogenerate, alembic_migration, Model / migration drift: the schema in the database must match the models.…, ``Base.metadata`` and the migrated database must describe the same schema., The DB whitelist and ``OperationType`` are the same closed set. The migration…, test_models_and_migrations_do_not_drift(), test_operations_type_check_matches_the_enum()

### Community 90 - "container.py"
Cohesion: 0.15
Nodes (18): _container_out(), Serialize one row; env values never leave the database (keys only)., ContainerDetailOut, ContainerOut, ContainerRemoveOut, host_ref(), HostRef, LogEntryOut (+10 more)

### Community 91 - "validate_config"
Cohesion: 0.08
Nodes (33): field_validator, collect_secret_refs(), walk(), ConfigValidationError, effective_config(), merge_config(), Any, ValueError (+25 more)

### Community 92 - "_apply_agent_entry"
Cohesion: 0.29
Nodes (7): _apply_agent_entry(), Write one heartbeat entry onto a container row. Kept complete at every call…, 2.1 Current shape (real), 2.2 Changes for the target model, 2.3 Capabilities (target), 2.4 DockerEndpoint — the 0..1 relation, 2. The Node concept

### Community 93 - "test_tenant_isolation.py"
Cohesion: 0.08
Nodes (35): A valid POST /servers body with per-test overrides., server_payload(), test_invalid_ip_rejected(), _app_role_dsn(), org_a(), fixture, Cross-tenant isolation: the Phase 1 exit gate. Every test here answers one of…, A least-privileged, **non-superadmin** member of organization A. Used to show… (+27 more)

### Community 94 - "error_of"
Cohesion: 0.14
Nodes (14): error_of(), Unwrap an API error envelope., _invite(), Removing someone from A must not reach their account or their other tenant. The…, ``sessions`` has no tenant column: the owning membership is the boundary.…, Knowing an id is not authority — not even for an instance operator. The caller…, The write side of the boundary: every mutating route misses for a foreign…, Invite a fresh account into the caller's organization and log it in. (+6 more)

### Community 95 - "alerts.py"
Cohesion: 0.22
Nodes (15): list_alerts(), mark_all_read(), mark_read(), CurrentUser, DbDep, Depends, get, post (+7 more)

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
Cohesion: 0.11
Nodes (21): clip(), DockerProviderError, Exception, Provider abstraction for docker hosts (real daemon or simulated). Providers are…, A provider operation failed. ``str()`` is safe to show/log., Build a compact, secret-free description of a provider failure. Only the…, Truncate *text* to *limit* characters, stripping control chars., sanitize_error() (+13 more)

### Community 100 - "AppError"
Cohesion: 0.17
Nodes (18): AppError, Exception, Base class for expected, client-facing errors., _authenticate_api_key(), _authenticate_jwt(), _bind_organization(), _frame_org(), _load_permissions() (+10 more)

### Community 101 - "Secrets Architecture"
Cohesion: 0.11
Nodes (19): 10. Resolution flow at deploy time, 1.1 Storage and crypto, 1.2 Data model, 1.3 API surface (metadata-only reads), 1.6 Gap list (Phase 2 status), 1. Current state, 2.1 Resolution runs inside org scope, 2.2 Migration mapping (applied by `b2c3d4e5f6a7`) (+11 more)

### Community 102 - "env.py"
Cohesion: 0.24
Nodes (10): _database_url(), Alembic environment: metadata comes from app.models, URL from app settings., Migrations run as the table **owner**, never as the application role. The owner…, Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online(), Owner-role DSN for Alembic and the container entrypoint. Migrations… (+2 more)

### Community 103 - "alert_service.py"
Cohesion: 0.23
Nodes (14): Alert, create_alert(), get_alert(), mark_all_read(), mark_read(), AsyncSession, UUID, Alert inbox: insert-only creation plus read/unread bookkeeping. (+6 more)

### Community 104 - "EnvironmentBase"
Cohesion: 0.32
Nodes (4): EnvironmentBase, _normalise_environment_type(), field_validator, Shared environment fields.

### Community 105 - "redis service (Redis 7, no persistence, loopback :6390)"
Cohesion: 0.22
Nodes (11): redis service (Redis 7, no persistence, loopback :6390), WebSocket API (/api/v1/ws handshake, frames, limits), WebSocket channels (global, server-metrics, container-logs, deployment-logs, incidents), Deployment engine (queue_deployment / execute_deployment / sweeper backstop), Real-time spine: PostgreSQL system_events + Redis pub/sub, Rollback as a new deployment (rollback_of_id), WebSocket hub (framework-thin, Redis fan-in, per-socket queues), Test suites (pytest unit+integration, vitest, Playwright e2e) (+3 more)

### Community 106 - "NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)"
Cohesion: 0.18
Nodes (12): Agent security model (one-way telemetry, no command channel), Agent enrollment token (X-Agent-Token, nxa_..., SHA-256 at rest), Agent heartbeat exponential backoff (cap 5 min, exit 1 on revoked token), agent/install.sh (enrollment installer), Agent metrics collection (/proc statvfs Docker socket), NexusOps agent (stdlib-only Python, agent/nexusops_agent.py), Agent systemd hardening (ProtectSystem=strict, NoNewPrivileges), Agent ingest API (POST /agent/hello, POST /agent/heartbeat) (+4 more)

### Community 107 - "_validate_resolution"
Cohesion: 0.16
Nodes (15): _is_forbidden_address(), is_simulation_url(), True when *url* targets the built-in simulated checker (``sim://``)., True when *addr* points into a network the server must never contact.…, Resolve *hostname* (AF_UNSPEC) and refuse any non-public answer., _validate_resolution(), parametrize, test_non_simulation_urls() (+7 more)

### Community 108 - "enums.py"
Cohesion: 0.13
Nodes (17): CredentialKind, EnvironmentType, LogSource, Closed registries of domain enumerations. Member names equal their values…, String enum; member names equal values so name/value storage never disagrees., Kind of a project-scoped deployment environment (Phase 2). Descriptive only —…, StrEnum, DeploymentApplicationRef (+9 more)

### Community 109 - "Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)"
Cohesion: 0.25
Nodes (9): API keys (X-API-Key, nxo_..., scope intersection), First boot sequence (api entrypoint migrates, compose never seeds), Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test), Makefile workflows (up/test/lint/typecheck/migrate/seed), HIGH finding: API-key scope bypass for superadmin-owned keys (fixed: scope intersection first), Security audit 2026-09 (26 raw findings -> 20 confirmed, all fixed), HIGH finding: known seed superadmin + API key backdoor (fixed: NEXUSOPS_ALLOW_SEED opt-in, one-time password), Threat model (edge attacker, malicious agent, curious operator, leaked token, SSRF) (+1 more)

### Community 111 - "create_organization"
Cohesion: 0.16
Nodes (23): add_member(), create_organization(), get_organization(), membership_for_user(), AsyncSession, Membership, Organization, Request (+15 more)

### Community 112 - "test_app_gating.py"
Cohesion: 0.44
Nodes (8): _app_for_environment(), MonkeyPatch, ENVIRONMENT gating contract: docs exposure and HSTS (see .env.example).…, create_app() with get_settings() patched to the given environment., test_non_production_does_not_emit_hsts(), test_non_production_keeps_docs_and_schema(), test_production_emits_hsts(), test_production_hides_docs_and_schema()

### Community 113 - "log_service.py"
Cohesion: 0.06
Nodes (50): _decode_frame(), _max_log_id(), _poll_new_lines(), UUID, Parse a Redis pub/sub frame ``{ts, stream, message}`` into a LogLine., Highest persisted log id for a container (poll fallback watermark)., Fetch log rows persisted after ``last_seen['id']`` (poll fallback)., Live-tail a container's logs. Primary source is the Redis pub/sub channel… (+42 more)

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "deps.py"
Cohesion: 0.04
Nodes (113): asyncio, permission_dep(), Any, FastAPI dependencies: database session, authenticated tenant context, RBAC…, Dependency factory enforcing a permission; returns 403 when denied., require_permission(), _check(), Agent ingest endpoints: enrollment handshake and periodic heartbeats.… (+105 more)

### Community 116 - "test_tenancy_allowlist.py"
Cohesion: 0.18
Nodes (15): AST, _actual_callers(), _calls_system_scope(), _module_path(), The system-scope allowlist is the only fence around the tenancy carve-out.…, Every module that could open a system scope: ``app/`` plus the scripts., No module may lift tenant isolation without being named in the list., Every listed module must still be a real caller, so the list stays short. (+7 more)

### Community 117 - "_entity_exists"
Cohesion: 0.40
Nodes (6): _entity_exists(), Whether *id_* exists **for this organization**. Runs inside the socket's…, The hub's subscribe-time existence check under concurrent orgs.…, test_websocket_entity_checks_stay_inside_their_socket_org(), check(), 5. WebSockets

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
Cohesion: 0.17
Nodes (15): NotificationError, Any, BaseException, Exception, Low-level notification transports: SMTP email and outgoing webhooks. These…, POST *payload* as JSON to *url*; 2xx is success, anything else raises. Response…, Raised when a delivery attempt fails. Message is safe to persist., Bounded, single-line, content-free error reason. (+7 more)

### Community 122 - "test_servers_and_audit.py"
Cohesion: 0.27
Nodes (11): _create_server(), Server CRUD, cascade delete, audit trail rows and audit immutability., The HTTP listing path — schema serialization is exercised end-to-end. A…, ``/servers`` is a temporary alias for pre-rename clients. It must keep working…, test_agent_token_rotation_invalidates_previous(), test_audit_log_api_serializes_and_filters(), test_audit_log_is_append_only(), test_audit_rows_written_for_server_actions() (+3 more)

### Community 123 - "bearer"
Cohesion: 0.14
Nodes (16): owner(), AsyncClient, A second organization the owner also belongs to. Both tenants are owned by the…, Bootstrap owner credentials for this test (fresh DB => first user). ``headers``…, second_org(), bearer(), login_headers(), Any (+8 more)

### Community 124 - "middleware.py"
Cohesion: 0.18
Nodes (11): ASGIApp, AccessLogMiddleware, HTTP middleware: request ids, security headers, structured access logs., Baseline hardening headers on every API response., RequestIDMiddleware, SecurityHeadersMiddleware, BaseHTTPMiddleware, starlette_middleware_base (+3 more)

### Community 126 - "uuid"
Cohesion: 0.09
Nodes (31): Agent-facing schemas. Payloads are data only — never executed., AlertOut, Schemas for operator-facing alerts., API key schemas. Raw keys appear exactly once, at creation., Application API schemas., AuditOut, Schemas for the read-only audit log API. The audit table is append-only; these…, One audit trail entry (no write routes ever exist for this resource).… (+23 more)

### Community 127 - "AuditLogPage.tsx"
Cohesion: 0.19
Nodes (8): AuditEntry, AuditLogPage, AuditLogPage(), AuditRow, formatTimestamp(), RESULTS, shortId(), mockedGet

### Community 137 - "Hub"
Cohesion: 0.14
Nodes (16): _close_socket(), Connection, Hub, _params_key(), _parse_payload(), Any, WebSocket, Connection registry, Redis fan-in listener and per-socket pumps. (+8 more)

### Community 146 - "flush_pending_publishes"
Cohesion: 0.18
Nodes (10): flush_pending_publishes(), Wait for frames scheduled by ``after_commit`` hooks to reach Redis. The commit…, _drained(), _is_same_origin(), Browsers always send Origin on WS handshakes, even same-origin ones. When it…, The drain must not become a delay on the hot path for quiet tasks., test_flush_is_a_noop_when_nothing_is_pending(), The proxy must forward the Host the browser actually used. A browser sends… (+2 more)

### Community 147 - "publish"
Cohesion: 0.10
Nodes (28): create_api_key(), list_api_keys(), AsyncSession, Request, UUID, Live (non-revoked) keys owned by *owner_id*, newest first., Revoke a key owned by *owner_id*. Foreign keys look like NotFound (no leak)., Revoke every live key of a user (used on deactivation). Returns count. (+20 more)

### Community 148 - "postgres service (PostgreSQL 17, loopback :5433)"
Cohesion: 0.29
Nodes (7): postgres service (PostgreSQL 17, loopback :5433), Fernet encryption at rest (ENCRYPTION_KEY, write-once), Backups (pgdata volume, nightly pg_dump, ephemeral Redis), Required secrets (POSTGRES_PASSWORD, JWT_SECRET >= 32 chars, ENCRYPTION_KEY Fernet), Production hardening checklist (secrets, ENVIRONMENT, no seed, TLS, rotation), Compose vs host network namespaces (postgres:5432 vs 127.0.0.1:5433), Simulation mode (SIMULATION_MODE)

### Community 149 - "assert_error_code"
Cohesion: 0.16
Nodes (18): assert_error_code(), Assert envelope shape + code; returns the inner error object., A fresh, deliverable-shaped address unique to a single test. ``example.com`` is…, unique_email(), Regression: lockout must not leak which emails exist. After login_max_attempts…, test_locked_account_response_is_indistinguishable(), test_second_register_without_invite_is_rejected(), Authorisation is per type — a Viewer cannot start containers. The codename… (+10 more)

### Community 150 - "nexusops-understand.mjs"
Cohesion: 0.33
Nodes (5): COMMON, meta, out, READERS, SCHEMA

### Community 151 - "Invisible account lockout (5 fails -> 15 min, enumeration resistance)"
Cohesion: 0.33
Nodes (6): Invisible account lockout (5 fails -> 15 min, enumeration resistance), Unified error envelope (code, message, request_id), Per-IP rate limiting (Redis fixed window), Request lifecycle (edge -> middleware -> rate limit -> deps -> router), Client IP resolution (resolve_client_ip, TRUSTED_PROXY_CIDRS, XFF overwrite), EmailStr rejects reserved domains (login 422 on .test/.local/.arpa)

### Community 152 - ".dispatch"
Cohesion: 0.60
Nodes (3): Request, Response, RequestResponseEndpoint

### Community 153 - "test_notifications.py"
Cohesion: 0.36
Nodes (9): NotificationDelivery, _channel(), _delivery(), UUID, Notification channel + delivery-log endpoints. Regression coverage for GET…, The same event frame consumed twice queues ONE delivery per channel. Every API…, test_dispatch_frame_is_idempotent_across_workers(), test_list_deliveries_filters_by_channel() (+1 more)

### Community 154 - "nexusops-draft.mjs"
Cohesion: 0.40
Nodes (4): DOCS, meta, SPINE, VERIFY_RULES

### Community 155 - "20261004_1200-e7c4a2b9d1f3_add_operations_framework.py"
Cohesion: 0.50
Nodes (3): _quoted_list(), Add the operations framework table (node-agent-architecture.md §5). One tenant-…, upgrade()

### Community 156 - "nexusops-challenge.mjs"
Cohesion: 0.33
Nodes (5): CHALLENGE_COMMON, meta, RESEARCH_COMMON, SCHEMA, TASKS

### Community 157 - "test_agent_ingestion.py"
Cohesion: 0.30
Nodes (10): _enrolled(), _heartbeat(), Agent ingest pipeline: hello, heartbeat, staleness transitions, events., A container absent from a later heartbeat is gone from the daemon., A payload at the agent's cap may be truncated — absence proves nothing., test_heartbeat_at_container_cap_skips_reconciliation(), test_heartbeat_removes_vanished_containers(), test_heartbeat_updates_status_metrics_and_containers() (+2 more)

### Community 158 - "test_schemas_agent.py"
Cohesion: 0.42
Nodes (9): AgentHeartbeatIn, Periodic metrics + observed containers from an enrolled agent., _heartbeat(), Unit tests for agent-facing schemas (heartbeat + container payloads)., test_minimal_heartbeat_accepted(), test_missing_required_metric_rejected(), test_more_than_200_containers_rejected(), test_out_of_range_metrics_rejected() (+1 more)

### Community 159 - "Session"
Cohesion: 0.22
Nodes (7): A login session binding refresh tokens to a device/context., Session, _FakeDb, Stands in for an ``AsyncSession`` whose only job here is ``sync_session``. A…, The shape of a worker task whose last statement is a commit., test_run_async_publishes_frames_scheduled_by_the_commit_hook(), commit_then_return()

### Community 161 - "register_exception_handlers"
Cohesion: 0.36
Nodes (8): _error_payload(), FastAPI, Request, register_exception_handlers(), handle_app_error(), handle_http_exception(), handle_unexpected(), handle_validation_error()

### Community 162 - "lax"
Cohesion: 0.40
Nodes (5): lax(), fixture, Production posture: private targets are NOT allowed (resolution runs)., Simulation posture: resolution skipped, syntax still enforced., strict()

### Community 163 - "Domain Model — NexusOps as a Multi-Tenant Platform"
Cohesion: 0.50
Nodes (4): 0. Design stance, 1. The hierarchy, 3. Cross-cutting decisions, Domain Model — NexusOps as a Multi-Tenant Platform

### Community 164 - "journey.spec.ts"
Cohesion: 0.29
Nodes (4): ADMIN, formLogin(), uiGoto(), UNIQUE

### Community 165 - "_FakeAsyncClient"
Cohesion: 0.22
Nodes (3): _FakeAsyncClient, _FakeRequestObj, Scripted httpx.AsyncClient: responses keyed by absolute request URL.

### Community 166 - "create_app"
Cohesion: 0.38
Nodes (6): create_app(), _include_routers(), lifespan(), FastAPI, Mount every domain router. Router variables follow the module contract., Start the WS hub + notification dispatcher; tear them down cleanly.

### Community 167 - "resolve_auth"
Cohesion: 0.09
Nodes (31): _attach_organization(), get_current_user(), get_identity(), get_optional_user(), _load_organization(), _load_permissions(), membership_for_org(), _org_id_from_header() (+23 more)

### Community 168 - "AgentHelloIn"
Cohesion: 0.29
Nodes (7): AgentHelloIn, First contact from an agent after enrollment; fills static host facts., test_agent_hello_bounds(), test_agent_hello_minimal(), 4.1 Wire contract today (real, pinned by tests), 4.2 v2 additions, 4. Heartbeat contract v2

### Community 170 - "ProjectUpdate"
Cohesion: 0.29
Nodes (7): EnvironmentCreate, Payload to create an environment under a project., ProjectCreate, ProjectUpdate, Payload to create a project; owner defaults to the caller., Partial project update; omitted fields are left untouched., 1.4 Deploy-time resolution (shipped)

### Community 171 - "get_meta"
Cohesion: 0.40
Nodes (5): get_meta(), DbSessionDep, get, Public metadata; identity fields appear only for valid credentials., OptionalUser

### Community 172 - "ApplicationBase"
Cohesion: 0.40
Nodes (4): ApplicationBase, Any, field_validator, Shared application fields; ``build_config`` is a free-form dict.

### Community 173 - "NexusOps — Phase 1 (Multi-Tenancy) Report"
Cohesion: 0.29
Nodes (7): OperationSpec, Everything the control plane needs to know about one operation type.…, 1. What Phase 1 delivered, 4. Operations framework (added in this pass), 5. Tests, 8. Position, NexusOps — Phase 1 (Multi-Tenancy) Report

### Community 174 - "3. Agent lifecycle"
Cohesion: 0.33
Nodes (6): 3.1 Current state (real), 3.2 Enrollment v2, 3.3 Token storage & rotation with dual-token grace, 3.4 Revocation semantics — fixing the 401 hot-loop, 3.5 Reconnect / offline states, 3. Agent lifecycle

### Community 175 - "big_serial_pk"
Cohesion: 0.40
Nodes (4): big_serial_pk(), Identity PK for very high-volume tables (metrics, logs)., declared_attr, Mapped

### Community 176 - "validate_endpoint_url"
Cohesion: 0.50
Nodes (3): model_validator, Validate/normalize an endpoint URL against the scheme allowlist., validate_endpoint_url()

### Community 177 - "scratch_database"
Cohesion: 0.50
Nodes (5): _admin_dsn(), fixture, An empty database on the same server, dropped again afterwards., _recreate_database(), scratch_database()

### Community 179 - "schemas/meta.py"
Cohesion: 0.50
Nodes (3): MetaOut, Public metadata schema + the canonical system-event type registry., Instance metadata. Identity fields are populated only when the caller presents…

### Community 180 - "websocket_endpoint"
Cohesion: 0.67
Nodes (3): websocket, Hand the socket to the hub (auth handshake handled there)., websocket_endpoint()

## Knowledge Gaps
- **420 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+415 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1817 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **25 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `6. Tooling: reproducible e2e` connect `NotFound` to `test_operations.py`, `client.ts`, `NexusOps — Phase 1 (Multi-Tenancy) Report`, `flush_pending_publishes`, `deps.py`, `_entity_exists`, `auth_service.py`?**
  _High betweenness centrality (0.231) - this node is a cross-community bridge._
- **Why does `useEventStream()` connect `client.ts` to `AuthContext.tsx`, `App.tsx`, `apiGet`, `ServerDetailPage.tsx`, `NotFound`?**
  _High betweenness centrality (0.230) - this node is a cross-community bridge._
- **Why does `TenancyScopeError` connect `test_operations.py` to `AuthContext`, `resolve_auth`, `log_service.py`, `deps.py`, `publish`, `_guard`, `NotFound`, `test_tenant_isolation.py`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._
- **Are the 79 inferred relationships involving `AuthContext` (e.g. with `TenancyScopeError` and `MembershipStatus`) actually correct?**
  _`AuthContext` has 79 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `APIModel` (e.g. with `OperationSpec` and `test_specs_reject_unknown_params()`) actually correct?**
  _`APIModel` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `apiGet()` (e.g. with `ContainerDetailPage.test.tsx` and `mockApi()`) actually correct?**
  _`apiGet()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `meta`, `SCHEMA`, `RESEARCH_COMMON` to the rest of the system?**
  _420 weakly-connected nodes found - possible documentation gaps or missing edges._