# Graph Report - nexusops  (2026-10-02)

## Corpus Check
- 286 files · ~259,222 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: (none) 8, .example 1, .service 1)

## Summary
- 4039 nodes · 11915 edges · 160 communities (139 shown, 21 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 975 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7a92b064`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- AuthContext.tsx
- login
- DockerHostsPage.tsx
- apiPost
- NotFound
- deps.py
- resolve_client_ip
- apiGet
- App.tsx
- models/base.py
- project_service.py
- ServerDetailPage.tsx
- v1/health.py
- client.ts
- projects.py
- incidents.py
- deployment_engine.py
- SimulatedDockerProvider
- maintenance.py
- _list_deployments
- test_deployments_simulated.py
- list_containers
- metrics_service.py
- test_security.py
- test_rate_limit.py
- monitor_service.py
- Node & Agent Architecture
- test_agent_backoff.py
- server.py
- nexusops_agent.py
- integration/conftest.py
- auth_service.py
- container_service.py
- create_host
- docker_hosts.py
- alert_service.py
- monitors.py
- v1/search.py
- server_service.py
- v1/channels.py
- DockerProvider
- test_monitor_transport.py
- test_agent_contract.py
- types.ts
- docker_real.py
- test_permissions.py
- RolesPage.tsx
- servers.py
- UnprocessableEntity
- create_secret
- role_service.py
- test_schemas_server.py
- create_api_key
- publish
- AgentContainerIn
- _guard
- rotate_secret
- 20260922_1000-a3f1c8d24b6e_add_tenancy_foundation.py
- notification_service.py
- test_auth_journey.py
- compilerOptions
- v1/auth.py
- middleware.py
- NotificationChannel
- SimulatedDeploymentRunner
- notification_sender.py
- test_schema_redaction.py
- me
- update_channel
- package.json
- events.py
- DeploymentEnvironment
- README.md - NexusOps overview
- models/__init__.py
- api service (FastAPI / uvicorn :8000)
- get_settings
- test_tenancy_allowlist.py
- AuthContext
- channel.py
- ApiKeysPage.tsx
- test_event_registry.py
- Settings
- .from_user
- EnvironmentUpdate
- test_tasks_util.py
- client_ip.py
- devDependencies
- redact_mapping
- seed.py
- register_exception_handlers
- _validate_resolution
- Deployment Architecture — NexusOps (target state)
- test_notifications.py
- create_app
- test_tenant_isolation.py
- AgentHelloIn
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- journey.spec.ts
- upsert_tag
- Domain Model — NexusOps as a Multi-Tenant Platform
- Secrets Architecture
- Certificate Management — NexusOps
- websocket_endpoint
- tests/conftest.py
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- lax
- test_error_logging.py
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- FakeSocket
- organization_service.py
- test_app_gating.py
- LogLine
- scripts
- test_ssrf.py
- resolve_secrets_for_environment
- Multi-Tenancy Architecture
- dependencies
- DeploymentDetailPage.test.tsx
- generate_secrets.sh
- hash_token
- server_payload
- _transport_is_https
- paginate
- .__init__
- APIModel
- .__tablename__
- install.sh
- docker-entrypoint.sh
- integration/__init__.py
- Hub
- CLAUDE.md - project graphify rules
- Graphify query workflow (query / path / explain / update)
- frontend/index.html - SPA shell
- NexusOps Favicon — stylized letter 'N' lettermark in sky blue (#38bdf8) on a dark navy rounded square (#0b1120, 7px corner radius)
- nexusops-backend
- _optional_actor
- ProjectCreate
- postgres service (PostgreSQL 17, loopback :5433)
- nexusops-understand.mjs
- Invisible account lockout (5 fails -> 15 min, enumeration resistance)
- resolve_auth
- instant_pacing
- nexusops-draft.mjs
- nexusops-challenge.mjs
- pytest
- AgentClient
- ApplicationCreate
- require_server
- get_secret_detail

## God Nodes (most connected - your core abstractions)
1. `AuthContext` - 136 edges
2. `APIModel` - 107 edges
3. `apiGet()` - 76 edges
4. `get_settings()` - 65 edges
5. `publish()` - 60 edges
6. `record()` - 59 edges
7. `NotFound` - 58 edges
8. `apiPost()` - 55 edges
9. `ApiError` - 54 edges
10. `PageParams` - 53 edges

## Surprising Connections (you probably didn't know these)
- `2. Org resolution on every request` --references--> `resolve_auth()`  [INFERRED]
  docs/multi-tenancy.md → backend/app/api/deps.py
- `3. Cross-cutting decisions` --references--> `require_permission()`  [INFERRED]
  docs/domain-model.md → backend/app/api/deps.py
- `10. Phase 7 — Teams, grants & custom roles` --references--> `require_permission()`  [INFERRED]
  docs/product-roadmap.md → backend/app/api/deps.py
- `7. The IDOR suite` --references--> `_search_users()`  [INFERRED]
  docs/multi-tenancy.md → backend/app/api/v1/search.py
- `6. Key hierarchy` --references--> `digest_of()`  [INFERRED]
  docs/secrets-architecture.md → backend/app/core/security.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three authentication credential families with centralized permission checks** — docs_api_md_auth, docs_api_md_refresh_rotation, docs_api_md_api_keys, docs_agent_md_enrollment_token, docs_api_md_permission_model [EXTRACTED 1.00]
- **NexusOps compose stack services** — docker_compose_yml_nexusops_stack, docker_compose_yml_postgres_service, docker_compose_yml_redis_service, docker_compose_yml_mailpit_service, docker_compose_yml_api_service, docker_compose_yml_worker_service, docker_compose_yml_scheduler_service, docker_compose_yml_frontend_service, docker_compose_yml_nginx_service [EXTRACTED 1.00]
- **WebSocket real-time fan-out spine** — docs_architecture_md_websocket_hub, docs_api_md_websocket_channels, docker_compose_yml_redis_service, docs_architecture_md_event_bus, readme_react_spa [INFERRED 0.85]

## Communities (160 total, 21 thin omitted)

### Community 0 - "AuthContext.tsx"
Cohesion: 0.05
Nodes (33): Membership, User, LoginPage, AuthContext, AuthProvider(), AuthState, isOrgSelectionError(), MeResponse (+25 more)

### Community 1 - "login"
Cohesion: 0.19
Nodes (21): change_password(), _clear_refresh_cookie(), _cookies_secure(), login(), logout(), DbSessionDep, post, Request (+13 more)

### Community 2 - "DockerHostsPage.tsx"
Cohesion: 0.06
Nodes (51): AuditEntry, Page, AuditLogPage, ContainerListPage, DockerHostsPage, EventsPage, IncidentListPage, SecretsPage (+43 more)

### Community 3 - "apiPost"
Cohesion: 0.07
Nodes (53): apiDelete(), apiPatch(), apiPost(), DeliveryOut, MonitorOut, AlertsPage, MonitorDetailPage, MonitorListPage (+45 more)

### Community 4 - "NotFound"
Cohesion: 0.08
Nodes (53): list_sessions(), CurrentUser, DbSessionDep, delete, get, Request, UUID, Active sessions of this organization's members. Defaults to the caller's own;… (+45 more)

### Community 5 - "deps.py"
Cohesion: 0.06
Nodes (81): asyncio, permission_dep(), Any, FastAPI dependencies: database session, authenticated tenant context, RBAC…, Dependency factory enforcing a permission; returns 403 when denied., require_permission(), Agent ingest endpoints: enrollment handshake and periodic heartbeats.…, API key routes — self-service management of the caller's own machine… (+73 more)

### Community 6 - "resolve_client_ip"
Cohesion: 0.28
Nodes (15): Request, Real client address for *request* per the trust model above., resolve_client_ip(), make_request(), Request, Unit tests for the chained-proxy client-IP resolver (app/core/client_ip.py)., test_all_trusted_entries_fall_back_to_peer(), test_empty_header_value_falls_back_to_peer() (+7 more)

### Community 7 - "apiGet"
Cohesion: 0.06
Nodes (35): apiGet(), DeploymentOut, DeploymentStepOut, EnvironmentOut, ProjectOut, DeploymentDetailPage, DeploymentListPage, MetaInfo (+27 more)

### Community 8 - "App.tsx"
Cohesion: 0.04
Nodes (62): DashboardSummary, SearchResult, App(), DashboardPage, LoginRoute(), OrganizationRequiredPage, ProjectDetailPage, ProjectListPage (+54 more)

### Community 9 - "models/base.py"
Cohesion: 0.15
Nodes (18): big_serial_pk(), json_column(), datetime, UUID, Declarative base, shared mixins and column helpers., Identity PK for very high-volume tables (metrics, logs)., status_check(), _utcnow() (+10 more)

### Community 10 - "project_service.py"
Cohesion: 0.14
Nodes (42): Any, AsyncSession, Request, UUID, Append an audit row using the caller's transaction (no commit here). The…, record(), actor_of(), _apply_update() (+34 more)

### Community 11 - "ServerDetailPage.tsx"
Cohesion: 0.09
Nodes (37): MetricPoint, ServerListPage, CheckboxField(), TextAreaField(), ChartSeries, LineChart(), LineChartProps, PAD (+29 more)

### Community 12 - "v1/health.py"
Cohesion: 0.20
Nodes (13): liveness(), get, Response, Health probes: liveness (always cheap) and readiness (checks dependencies).…, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness(), HealthOut (+5 more)

### Community 13 - "client.ts"
Cohesion: 0.08
Nodes (38): API_BASE, apiRequest(), buildUrl(), extractError(), getAccessToken(), getActiveOrgId(), onActiveOrgChange(), ORGANIZATION_HEADER (+30 more)

### Community 14 - "projects.py"
Cohesion: 0.14
Nodes (41): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+33 more)

### Community 15 - "incidents.py"
Cohesion: 0.13
Nodes (33): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+25 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.11
Nodes (54): deployment_log_channel(), Deployment, DeploymentStep, AlertSeverity, DeploymentStatus, StepStatus, _after_commit_enqueue(), _after_rollback_drop() (+46 more)

### Community 17 - "SimulatedDockerProvider"
Cohesion: 0.08
Nodes (34): ContainerHealth, ContainerStatus, Container, Observed container state mirrored from an agent or docker provider., Any, Simulated docker provider for demo and test environments. The provider is…, Plausible numbers derived from the row plus time-based sine noise., Implements :class:`DockerProvider` semantics against DB rows. (+26 more)

### Community 18 - "maintenance.py"
Cohesion: 0.06
Nodes (62): Celery application: periodic cadences live here, dynamic work is claimed…, task, Deployment execution task + stuck-deployment sweeper., Execute one queued deployment. The engine owns all state transitions., Re-enqueue deployments the broker lost; fail ones whose worker died.…, run_deployment(), _run(), sweep_deployments() (+54 more)

### Community 19 - "_list_deployments"
Cohesion: 0.09
Nodes (41): _attribute_step_idx(), cancel_deployment(), _emails_for(), get_deployment(), list_application_deployments(), list_deployment_logs(), _list_deployments(), _parse_sort() (+33 more)

### Community 20 - "test_deployments_simulated.py"
Cohesion: 0.15
Nodes (28): execute_deployment(), Run one deployment to a terminal state. Never raises; safe to re-run., get_environment(), _as_worker(), _delivery_chain(), _owner_ctx(), _queue(), _queued_with_recorder() (+20 more)

### Community 21 - "list_containers"
Cohesion: 0.06
Nodes (53): _action_route(), _endpoint(), _container_out(), _decode_frame(), get_container(), list_containers(), _load_container(), _max_log_id() (+45 more)

### Community 22 - "metrics_service.py"
Cohesion: 0.09
Nodes (41): get_dashboard_summary(), get_latest_server_metrics(), get_server_metrics(), CurrentUser, DbDep, Depends, get, UUID (+33 more)

### Community 23 - "test_security.py"
Cohesion: 0.11
Nodes (34): argon2, argon2_exceptions, Unauthorized, create_access_token(), decode_access_token(), hash_password(), password_needs_rehash(), Any (+26 more)

### Community 24 - "test_rate_limit.py"
Cohesion: 0.06
Nodes (46): RateLimited, _memory_count_and_ttl(), rate_limit(), _dependency(), Fixed-window counter backed by process memory. Returns (count, ttl)., Return a dependency enforcing *limit* requests per window per IP. With…, _clean_memory_windows(), _FakeRequest (+38 more)

### Community 25 - "monitor_service.py"
Cohesion: 0.16
Nodes (37): AppError, BadRequest, Exception, Base class for expected, client-facing errors., MonitorStatus, Monitor, _active_incident(), _audit() (+29 more)

### Community 26 - "Node & Agent Architecture"
Cohesion: 0.11
Nodes (19): 1. Scope and stance, 2.1 Current shape (real), 2.2 Changes for the target model, 2.3 Capabilities (target), 2. The Node concept, 6.1 Token scope, 6.2 docker.sock is root-equivalent, 6.3 Transport: HTTPS-only (+11 more)

### Community 27 - "test_agent_backoff.py"
Cohesion: 0.14
Nodes (22): agent_fixture(), _install_sleep(), fake_sleep(), _load_agent(), _patch_host(), Any, fixture, MonkeyPatch (+14 more)

### Community 28 - "server.py"
Cohesion: 0.14
Nodes (14): _clean_tag_names(), DockerHostSummary, Server API schemas: create/update payloads, list/detail outputs, enrollment., Compact system event projection for server timelines., Full server view with recent timeline events and container counts., Strip, drop empties and de-duplicate tag names case-insensitively., Server as listed in collections. Never exposes the agent token hash., ServerCounts (+6 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.09
Nodes (30): build_heartbeat(), collect_container_stats(), collect_containers(), cpu_percent_since(), disk_stats(), _docker_request(), _interruptible_sleep(), load1() (+22 more)

### Community 30 - "integration/conftest.py"
Cohesion: 0.08
Nodes (26): alembic_config, close_redis(), _clean_slate(), client(), _ensure_database(), _migrated_database(), org_db(), owner() (+18 more)

### Community 31 - "auth_service.py"
Cohesion: 0.10
Nodes (47): active_memberships(), Membership, The user's memberships in non-suspended organizations, oldest first. Reads only…, System scope bound to *db*, for rows that have no organization. Used by exactly…, system_write_scope(), AuditResult, _audit(), _bootstrap_organization() (+39 more)

### Community 32 - "container_service.py"
Cohesion: 0.09
Nodes (47): DockerHostStatus, DockerHost, clip(), DockerProviderError, Exception, Provider abstraction for docker hosts (real daemon or simulated). Providers are…, A provider operation failed. ``str()`` is safe to show/log., Build a compact, secret-free description of a provider failure. Only the… (+39 more)

### Community 33 - "create_host"
Cohesion: 0.15
Nodes (22): _assert_endpoint_allowed(), _assert_name_free(), create_host(), endpoint_scheme(), list_images(), list_networks(), list_volumes(), _provider_inventory() (+14 more)

### Community 34 - "docker_hosts.py"
Cohesion: 0.07
Nodes (54): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+46 more)

### Community 35 - "alert_service.py"
Cohesion: 0.11
Nodes (30): list_alerts(), mark_all_read(), mark_read(), CurrentUser, DbDep, Depends, get, post (+22 more)

### Community 36 - "monitors.py"
Cohesion: 0.06
Nodes (76): _ev(), _like_pattern(), list_container_logs(), Keyset-paginated log rows ordered newest-first (ts DESC, id DESC)., String form of an enum-typed column value (str at runtime)., check_now(), create_monitor(), delete_monitor() (+68 more)

### Community 37 - "v1/search.py"
Cohesion: 0.12
Nodes (33): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+25 more)

### Community 38 - "server_service.py"
Cohesion: 0.10
Nodes (48): _detail(), AsyncSession, server_metrics_channel(), ServerStatus, Server, _actor_kwargs(), _apply_agent_entry(), container_counts() (+40 more)

### Community 39 - "v1/channels.py"
Cohesion: 0.17
Nodes (25): create_channel(), delete_channel(), get_channel(), list_channels(), list_deliveries(), DbDep, delete, Depends (+17 more)

### Community 40 - "DockerProvider"
Cohesion: 0.09
Nodes (12): DockerProvider, Any, datetime, Protocol, List containers visible to the provider., Inspect a single container by id (short ids allowed)., List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``., List volumes: keys ``name``, ``driver``, ``mountpoint``. (+4 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.05
Nodes (61): CheckResult, CheckOutcome, coerce_headers(), _decode(), get_transport(), HTTPMonitorTransport, MonitorTransport, Any (+53 more)

### Community 42 - "test_agent_contract.py"
Cohesion: 0.20
Nodes (15): agent_fixture(), _load_agent(), _patch_stats(), Any, fixture, MonkeyPatch, Contract tests: the shipped agent's payloads must satisfy the ingest schemas.…, One-shot docker stats reduce to cpu/mem/limit fields the schema accepts, with… (+7 more)

### Community 43 - "types.ts"
Cohesion: 0.02
Nodes (102): ApiError, AlertOut, ApplicationOut, ChannelOut, CheckOut, ContainerOut, CursorPage, DeploymentLogLine (+94 more)

### Community 44 - "docker_real.py"
Cohesion: 0.09
Nodes (28): ContainerInfo, ContainerStats, Normalized view of a container as reported by any provider., Point-in-time resource usage snapshot., _as_float(), _compute_stats(), _cpu_percent(), _network_bytes() (+20 more)

### Community 45 - "test_permissions.py"
Cohesion: 0.06
Nodes (33): permission_exists(), PermissionSpec, Permission registry and role matrix. Permissions are *data*: the registry below…, Check an API-key scope list against a required permission. Supports exact match…, scope_matches(), _auth_context(), _FakeCtx, parametrize (+25 more)

### Community 46 - "RolesPage.tsx"
Cohesion: 0.11
Nodes (15): Role, RolesPage, describeError(), GROUP_STYLE, LEGEND_STYLE, OPTION_STYLE, PermissionSpec, roleAllows() (+7 more)

### Community 47 - "servers.py"
Cohesion: 0.11
Nodes (32): create_server(), delete_server(), get_server(), list_servers(), list_tags(), DbDep, delete, Depends (+24 more)

### Community 48 - "UnprocessableEntity"
Cohesion: 0.15
Nodes (25): UnprocessableEntity, assert_safe_url(), assert_safe_url_async(), _raise_block(), Validate *url* for outbound requests; return the parsed URL or raise 422.…, Async wrapper around :func:`assert_safe_url`; DNS runs off the loop., Reject non-empty values that are not valid IPv4/IPv6 addresses., _validate_ip() (+17 more)

### Community 49 - "create_secret"
Cohesion: 0.25
Nodes (15): _actor_type(), create_secret(), delete_secret(), get_secret(), list_secrets(), _project_exists(), AsyncSession, Request (+7 more)

### Community 50 - "role_service.py"
Cohesion: 0.07
Nodes (45): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, delete, get (+37 more)

### Community 51 - "test_schemas_server.py"
Cohesion: 0.21
Nodes (22): Payload for registering a server., Partial update. ``tags`` replaces the full set when provided., ServerCreate, ServerUpdate, _base(), parametrize, Unit tests for app.schemas.server (validation only, no I/O)., test_empty_ip_is_allowed_but_whitespace_collapses() (+14 more)

### Community 52 - "create_api_key"
Cohesion: 0.16
Nodes (17): create_api_key(), list_api_keys(), CurrentUser, DbSessionDep, delete, get, post, Request (+9 more)

### Community 53 - "publish"
Cohesion: 0.17
Nodes (20): get_redis(), ping(), _after_commit_publish(), _after_rollback_drop(), publish(), _publish_after_commit(), _publish_redis(), Any (+12 more)

### Community 54 - "AgentContainerIn"
Cohesion: 0.20
Nodes (21): AgentContainerIn, AgentHeartbeatIn, field_validator, Observed container state reported by an agent., Periodic metrics + observed containers from an enrolled agent., _container(), _heartbeat(), parametrize (+13 more)

### Community 55 - "_guard"
Cohesion: 0.12
Nodes (22): _apply_scope_guc(), _desired_guc(), _guard(), _has_org_predicate(), install_tenancy_guards(), _mappers_of(), org_scoped_table_names(), Any (+14 more)

### Community 56 - "rotate_secret"
Cohesion: 0.16
Nodes (21): create_secret(), delete_secret(), get_secret(), list_secrets(), DbSession, delete, Depends, get (+13 more)

### Community 57 - "20260922_1000-a3f1c8d24b6e_add_tenancy_foundation.py"
Cohesion: 0.06
Nodes (17): alembic, _app_role_credentials(), _assert_fully_backfilled(), _backfill_org_ids(), _drop_constraint(), add tenancy foundation Phase 1 of the platform roadmap: organizations,…, Carry a value into a PL/pgSQL block. ``CREATE ROLE``/``ALTER ROLE`` are utility…, Application role name/password from settings (never hard-coded). (+9 more)

### Community 58 - "notification_service.py"
Cohesion: 0.16
Nodes (24): _as_uuid(), _attempt_delivery(), decode_delivery_cursor(), dispatch_event_frame(), _send(), dispatcher_loop(), encode_delivery_cursor(), list_deliveries() (+16 more)

### Community 59 - "test_auth_journey.py"
Cohesion: 0.06
Nodes (68): assert_error_code(), bearer(), cookie_attributes(), error_of(), login_account(), login_headers(), Any, AsyncClient (+60 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "v1/auth.py"
Cohesion: 0.18
Nodes (17): Authentication routes: register, login, refresh rotation, logout, me, password., LoginRequest, MeOut, PasswordChangeRequest, Authentication request/response schemas., Optional body for non-browser clients; the cookie takes precedence., Token response, plus everything a client needs to pick an organization. The JWT…, Caller identity, their organizations, and their authority in the active one.… (+9 more)

### Community 62 - "middleware.py"
Cohesion: 0.15
Nodes (14): ASGIApp, AccessLogMiddleware, Request, Response, HTTP middleware: request ids, security headers, structured access logs., Baseline hardening headers on every API response., RequestIDMiddleware, SecurityHeadersMiddleware (+6 more)

### Community 63 - "NotificationChannel"
Cohesion: 0.15
Nodes (16): encrypt_str(), NotificationChannel, A delivery target (email address / webhook endpoint). ``config_ciphertext``…, _create_monitor(), Monitor checks driving the full down -> incident -> recovery lifecycle., Regression: probe headers and URL query credentials never leave the API. Probe…, A monitor's checks, incidents and timeline all live in its organization, so the…, test_check_now_endpoint_runs_immediately() (+8 more)

### Community 64 - "SimulatedDeploymentRunner"
Cohesion: 0.11
Nodes (40): LogLevel, _commit_short(), _pace(), Exception, Deployment runner port plus a faithful simulated implementation.…, Stream output lines for *step_name*; raise StepFailure to fail it., Staged docker-style simulation used by v1 deployments., Deterministic per-line delay between 0.05s and 0.35s. (+32 more)

### Community 65 - "notification_sender.py"
Cohesion: 0.16
Nodes (17): NotificationError, Any, BaseException, Exception, Low-level notification transports: SMTP email and outgoing webhooks. These…, POST *payload* as JSON to *url*; 2xx is success, anything else raises. Response…, Raised when a delivery attempt fails. Message is safe to persist., Bounded, single-line, content-free error reason. (+9 more)

### Community 66 - "test_schema_redaction.py"
Cohesion: 0.18
Nodes (17): is_sensitive_header(), mask_sensitive_headers(), True when *name* looks like it carries a credential (Authorization etc.)., Return a copy of *headers* with sensitive values replaced by a mask., mask_target(), Human-readable masked target safe to expose over the API. For webhook families…, _monitor_out(), Outbound-schema redaction: monitor probe credentials and webhook targets.… (+9 more)

### Community 67 - "me"
Cohesion: 0.12
Nodes (19): me(), get, IdentityUser, The caller's identity, organizations, and authority in the active one.…, create_organization(), list_my_organizations(), CurrentUser, DbSessionDep (+11 more)

### Community 68 - "update_channel"
Cohesion: 0.23
Nodes (17): EmailConfig, _audit(), create_channel(), decrypt_channel_config(), delete_channel(), encrypt_config(), _normalize_events(), Any (+9 more)

### Community 69 - "package.json"
Cohesion: 0.13
Nodes (15): name, private, type, version, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom (+7 more)

### Community 70 - "events.py"
Cohesion: 0.16
Nodes (17): _decode_cursor(), _encode_cursor(), list_event_types(), list_events(), datetime, DbSession, Depends, get (+9 more)

### Community 71 - "DeploymentEnvironment"
Cohesion: 0.15
Nodes (19): DeploymentEnvironment, An encrypted configuration value. The plaintext is never returned by the API…, Secret, _create(), _environment_config(), Secrets: metadata-only reads, rotation versioning, deploy-time resolution., Project → application → environment carrying *config*; returns its id., A reference naming no secret must abort, not resolve to an empty value.… (+11 more)

### Community 72 - "README.md - NexusOps overview"
Cohesion: 0.06
Nodes (59): docker-compose.dev.yml - dev overlay, docker-compose.docker-sock.yml - docker socket override, docker-compose.yml - full stack definition, docs/agent.md - agent guide, docs/api.md - API guide, Append-only audit log (Postgres BEFORE UPDATE OR DELETE trigger), docs/architecture.md - system architecture, docs/deployment.md - deployment and operations guide (+51 more)

### Community 73 - "models/__init__.py"
Cohesion: 0.15
Nodes (29): _org_scoped_classes(), Mapped classes marked :class:`~app.models.base.OrgScoped`. Reads the mapper…, Base, OrgScoped, Base for all ORM models with stable constraint naming for Alembic., Mixin marking a table as **organization-owned** (Phase 1 tenancy). Set the…, CredentialKind, Opaque refresh token; only its SHA-256 hash is stored. Rotation chain: on… (+21 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "get_settings"
Cohesion: 0.08
Nodes (30): AsyncEngine, _database_url(), Alembic environment: metadata comes from app.models, URL from app settings., Migrations run as the table **owner**, never as the application role. The owner…, Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online() (+22 more)

### Community 76 - "test_tenancy_allowlist.py"
Cohesion: 0.20
Nodes (14): AST, _actual_callers(), _calls_system_scope(), _module_path(), The system-scope allowlist is the only fence around the tenancy carve-out.…, Every module that could open a system scope: ``app/`` plus the scripts., No module may lift tenant isolation without being named in the list., Every listed module must still be a real caller, so the list stays short. (+6 more)

### Community 77 - "AuthContext"
Cohesion: 0.06
Nodes (67): _attach_organization(), AuthContext, _load_organization(), _load_permissions(), membership_for_org(), _org_id_from_header(), Organization, UUID (+59 more)

### Community 78 - "channel.py"
Cohesion: 0.20
Nodes (12): ChannelType, DeliveryStatus, ChannelBase, ChannelCreate, ChannelUpdate, DeliveryOut, BaseModel, model_validator (+4 more)

### Community 79 - "ApiKeysPage.tsx"
Cohesion: 0.09
Nodes (20): ApiKeyOut, ApiKeysPage, ApiKeyCreatedOut, ApiKeysPage(), handleCopyKey(), copyText(), describeError(), EMPTY_FORM (+12 more)

### Community 80 - "test_event_registry.py"
Cohesion: 0.22
Nodes (7): event_type_catalogue(), is_known_event_type(), Return True when *event_type* is part of the canonical registry., Serialise the registry for the ``/events/types`` endpoint., Registry coherence: schema-advertised event types must equal the canonical…, test_catalogue_serialises_every_entry(), test_known_event_lookup()

### Community 81 - "Settings"
Cohesion: 0.14
Nodes (6): field_validator, model_validator, Username from :attr:`database_url`, or ``None`` if it is unparseable., Validated application settings (loaded from environment / .env)., Settings, BaseSettings

### Community 82 - ".from_user"
Cohesion: 0.16
Nodes (20): create_user(), deactivate_user(), get_user(), list_users(), CurrentUser, DbSessionDep, delete, get (+12 more)

### Community 83 - "EnvironmentUpdate"
Cohesion: 0.22
Nodes (9): EnvironmentBase, EnvironmentCreate, EnvironmentUpdate, field_validator, Shared environment fields., Payload to create an environment under an application., Partial environment update; omitted fields are left untouched., 1.4 Deploy-time resolution today (+1 more)

### Community 84 - "test_tasks_util.py"
Cohesion: 0.36
Nodes (8): _answer(), _boom(), _nested(), Unit tests for the Celery-task async bridge (pure asyncio, no broker)., test_run_async_awaits_nested_coroutines(), test_run_async_is_repeatable_per_invocation(), test_run_async_propagates_exceptions(), test_run_async_returns_coroutine_result()

### Community 85 - "client_ip.py"
Cohesion: 0.29
Nodes (7): _is_trusted(), _parse_networks(), Client-IP resolution behind chained reverse proxies. The API never takes TCP…, Parse a comma-separated CIDR list; malformed entries are skipped., test_parse_networks_skips_malformed_entries(), functools, _Network

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "redact_mapping"
Cohesion: 0.22
Nodes (13): _is_sensitive_key(), Substring match on a normalised key so header-style names are caught too.…, Return a copy of *data* with sensitive values replaced. Used by audit metadata…, redact_mapping(), parametrize, Unit tests for app.core.logging redaction (pure functions only)., test_case_insensitive_substring_match(), test_flat_sensitive_keys_redacted() (+5 more)

### Community 88 - "seed.py"
Cohesion: 0.11
Nodes (35): TimestampMixin, Application, Project, UserStatus, ApiKey, Permission, Identity & access models: users, roles, permissions, sessions, tokens., A login session binding refresh tokens to a device/context. (+27 more)

### Community 89 - "register_exception_handlers"
Cohesion: 0.36
Nodes (8): _error_payload(), FastAPI, Request, register_exception_handlers(), handle_app_error(), handle_http_exception(), handle_unexpected(), handle_validation_error()

### Community 90 - "_validate_resolution"
Cohesion: 0.24
Nodes (9): _is_forbidden_address(), True when *addr* points into a network the server must never contact.…, Resolve *hostname* (AF_UNSPEC) and refuse any non-public answer., _validate_resolution(), test_private_and_special_addresses_are_forbidden(), test_public_addresses_are_allowed(), test_validate_resolution_passes_hostname_through(), IPv4Address (+1 more)

### Community 91 - "Deployment Architecture — NexusOps (target state)"
Cohesion: 0.10
Nodes (21): DeploymentRunner, Protocol, Adapter interface implemented by real (future) and simulated runners., Return the ordered step names for this run., 10. Events and WS during runs, 11. Post-deploy hooks, 12. Rollback semantics (existing behavior kept), 13. The simulated runner stays — labeled (+13 more)

### Community 92 - "test_notifications.py"
Cohesion: 0.36
Nodes (9): NotificationDelivery, _channel(), _delivery(), UUID, Notification channel + delivery-log endpoints. Regression coverage for GET…, The same event frame consumed twice queues ONE delivery per channel. Every API…, test_dispatch_frame_is_idempotent_across_workers(), test_list_deliveries_filters_by_channel() (+1 more)

### Community 93 - "create_app"
Cohesion: 0.38
Nodes (6): create_app(), _include_routers(), lifespan(), FastAPI, Mount every domain router. Router variables follow the module contract., Start the WS hub + notification dispatcher; tear them down cleanly.

### Community 94 - "test_tenant_isolation.py"
Cohesion: 0.06
Nodes (54): async_sessionmaker, dispose_engine(), get_sessionmaker(), AsyncSession, apply_scope_to_session(), org_scope(), Run the enclosed block as a single organization. Nesting the *same* org is a…, Run the enclosed block with tenant filtering off (maintenance only). ``reason``… (+46 more)

### Community 95 - "AgentHelloIn"
Cohesion: 0.29
Nodes (7): AgentHelloIn, First contact from an agent after enrollment; fills static host facts., test_agent_hello_bounds(), test_agent_hello_minimal(), 4.1 Wire contract today (real, pinned by tests), 4.2 v2 additions, 4. Heartbeat contract v2

### Community 96 - "NexusOps (self-hosted infrastructure management and monitoring platform)"
Cohesion: 0.20
Nodes (10): mailpit service (dev SMTP sink + web UI :8025), NexusOps compose stack (8 services on one network), HIGH finding: redirect-following SSRF in uptime monitors (fixed: follow_redirects=False + per-hop guard), SSRF guard (assert_safe_url, per-redirect-hop validation, assert_safe_tcp_endpoint), Mailpit SMTP port internal-only (host-side injection needs extra mapping), Host port knobs (NEXUSOPS_HTTP_PORT/POSTGRES/REDIS/MAILPIT/VITE), SPA entry point (loads /src/main.tsx, dark color-scheme), Uptime monitors -> incidents -> notifications flow (+2 more)

### Community 97 - "REST API surface (/api/v1)"
Cohesion: 0.29
Nodes (7): Cursor (keyset) and offset pagination envelopes, Permission model (data-driven registry, require_permission, wildcard scopes), REST API surface (/api/v1), RBAC registry (PERMISSIONS + ROLE_MATRIX + scope_matches), Adding a new resource: 7-step checklist (model -> migration -> schemas -> service -> router -> tests -> frontend), Alembic migration workflow (autogenerate, models __init__ export, entrypoint apply), Command palette (Ctrl/Cmd+K)

### Community 98 - "journey.spec.ts"
Cohesion: 0.21
Nodes (9): ADMIN, Bootstrap, bootstrapVia(), test, ADMIN, formLogin(), uiGoto(), UNIQUE (+1 more)

### Community 99 - "upsert_tag"
Cohesion: 0.40
Nodes (5): list_tags_with_usage(), All tags ordered by name with their server usage counts., Create a tag or update its colour; names are matched exactly., upsert_tag(), Tag

### Community 100 - "Domain Model — NexusOps as a Multi-Tenant Platform"
Cohesion: 0.25
Nodes (8): org_id_column(), A plain ``org_id`` column for the few tables that carry one without taking part…, 0.1 Shipped tenant layer (Phase 1), 0. Design stance, 1.1 ER diagram, 1. The hierarchy, 3. Cross-cutting decisions, Domain Model — NexusOps as a Multi-Tenant Platform

### Community 101 - "Secrets Architecture"
Cohesion: 0.15
Nodes (13): 10. Resolution flow at deploy time, 2.1 Resolution runs inside org scope, 2.2 Migration mapping, 2. Target scope model (org / project / environment layering), 3.1 What this fixes, 3. SecretVersion — append-only history, 4.1 Audit event at resolution time, 4. Resolution authorization (+5 more)

### Community 102 - "Certificate Management — NexusOps"
Cohesion: 0.09
Nodes (24): decrypt_str(), _fernet(), parametrize, test_decrypt_with_wrong_ciphertext_raises_value_error(), test_encrypt_decrypt_roundtrip(), 10. Status/expiry tracking and monitor tie-in, 11. Failure handling, 12. Audit and events (+16 more)

### Community 103 - "websocket_endpoint"
Cohesion: 0.67
Nodes (3): websocket, Hand the socket to the hub (auth handshake handled there)., websocket_endpoint()

### Community 104 - "tests/conftest.py"
Cohesion: 0.20
Nodes (8): configure_test_env(), Test bootstrap: pin every cached setting BEFORE the first ``app`` import. The…, KEY=VALUE pairs from the repo .env (first definition wins); never logged., Export the exact settings the app caches; host values cannot leak through., _read_dot_env(), os, sys, urllib_parse

### Community 105 - "redis service (Redis 7, no persistence, loopback :6390)"
Cohesion: 0.22
Nodes (11): redis service (Redis 7, no persistence, loopback :6390), WebSocket API (/api/v1/ws handshake, frames, limits), WebSocket channels (global, server-metrics, container-logs, deployment-logs, incidents), Deployment engine (queue_deployment / execute_deployment / sweeper backstop), Real-time spine: PostgreSQL system_events + Redis pub/sub, Rollback as a new deployment (rollback_of_id), WebSocket hub (framework-thin, Redis fan-in, per-socket queues), Test suites (pytest unit+integration, vitest, Playwright e2e) (+3 more)

### Community 106 - "NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)"
Cohesion: 0.18
Nodes (12): Agent security model (one-way telemetry, no command channel), Agent enrollment token (X-Agent-Token, nxa_..., SHA-256 at rest), Agent heartbeat exponential backoff (cap 5 min, exit 1 on revoked token), agent/install.sh (enrollment installer), Agent metrics collection (/proc statvfs Docker socket), NexusOps agent (stdlib-only Python, agent/nexusops_agent.py), Agent systemd hardening (ProtectSystem=strict, NoNewPrivileges), Agent ingest API (POST /agent/hello, POST /agent/heartbeat) (+4 more)

### Community 107 - "lax"
Cohesion: 0.40
Nodes (5): lax(), fixture, Production posture: private targets are NOT allowed (resolution runs)., Simulation posture: resolution skipped, syntax still enforced., strict()

### Community 108 - "test_error_logging.py"
Cohesion: 0.22
Nodes (4): Regression: the catch-all 500 handler must not log raw exception text.…, _SpyLogger, test_unhandled_exception_handler_logs_class_not_message(), fastapi_testclient

### Community 109 - "Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)"
Cohesion: 0.25
Nodes (9): API keys (X-API-Key, nxo_..., scope intersection), First boot sequence (api entrypoint migrates, compose never seeds), Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test), Makefile workflows (up/test/lint/typecheck/migrate/seed), HIGH finding: API-key scope bypass for superadmin-owned keys (fixed: scope intersection first), Security audit 2026-09 (26 raw findings -> 20 confirmed, all fixed), HIGH finding: known seed superadmin + API key backdoor (fixed: NEXUSOPS_ALLOW_SEED opt-in, one-time password), Threat model (edge attacker, malicious agent, curious operator, leaked token, SSRF) (+1 more)

### Community 111 - "organization_service.py"
Cohesion: 0.14
Nodes (28): _check(), Forbidden, add_member(), create_organization(), get_organization(), membership_for_user(), AsyncSession, Membership (+20 more)

### Community 112 - "test_app_gating.py"
Cohesion: 0.44
Nodes (8): _app_for_environment(), MonkeyPatch, ENVIRONMENT gating contract: docs exposure and HSTS (see .env.example).…, create_app() with get_settings() patched to the given environment., test_non_production_does_not_emit_hsts(), test_non_production_keeps_docs_and_schema(), test_production_emits_hsts(), test_production_hides_docs_and_schema()

### Community 113 - "LogLine"
Cohesion: 0.10
Nodes (23): LogSource, LogLine, One parsed log record from a container log stream., datetime, Replay registered LogEntry rows ordered by ts (tail N). ``follow`` is ignored…, append_lines(), count_container_logs(), _entry_values() (+15 more)

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "test_ssrf.py"
Cohesion: 0.14
Nodes (22): assert_safe_tcp_endpoint(), is_simulation_url(), SSRF guard applied to every operator-supplied outbound URL. Monitors and…, Validate a ``tcp://`` docker host endpoint for outbound connection. Docker…, True when *url* targets the built-in simulated checker (``sim://``)., Internal signal: a specific SSRF rule matched (never shown to clients)., UrlRejected, _validate_syntax() (+14 more)

### Community 116 - "resolve_secrets_for_environment"
Cohesion: 0.19
Nodes (13): Exception, A ``${secret:KEY}`` reference could not be resolved. Fail-closed. Carries…, One successfully resolved reference: metadata for audit, no value., Outcome of resolving an environment's config references., Resolve every ``${secret:KEY}`` reference in an environment's config. INTERNAL…, resolve_secrets_for_environment(), ResolvedSecrets, SecretReference (+5 more)

### Community 117 - "Multi-Tenancy Architecture"
Cohesion: 0.17
Nodes (11): Whether the runtime connection is the RLS-enforced application role. False…, 10. Migration (Phase 1), 1. Tenancy invariants, 2.1 Org creation — v1 decision, 2. Org resolution on every request, 4. Background jobs, 6. Agents, 7. The IDOR suite (+3 more)

### Community 118 - "dependencies"
Cohesion: 0.33
Nodes (6): dependencies, lucide-react, react, react-dom, react-router-dom, @tanstack/react-query

### Community 119 - "DeploymentDetailPage.test.tsx"
Cohesion: 0.13
Nodes (9): ACTIVE_MEMBERSHIP, ApiError, deploymentDetail(), EMPTY_LOGS, FakeWebSocket, get, ME, post (+1 more)

### Community 120 - "generate_secrets.sh"
Cohesion: 0.47
Nodes (3): existing_real_keys(), replace_or_append(), generate_secrets.sh script

### Community 121 - "hash_token"
Cohesion: 0.17
Nodes (17): AsyncSession, User, Resolve the caller's identity only (no organization)., _resolve_identity(), _user_from_api_key(), generate_agent_token(), generate_api_key(), generate_refresh_token() (+9 more)

### Community 122 - "server_payload"
Cohesion: 0.10
Nodes (27): A valid POST /servers body with per-test overrides., server_payload(), _create_server(), Server CRUD, cascade delete, audit trail rows and audit immutability., The HTTP listing path — schema serialization is exercised end-to-end. A…, ``/servers`` is a temporary alias for pre-rename clients. It must keep working…, test_agent_token_rotation_invalidates_previous(), test_audit_log_api_serializes_and_filters() (+19 more)

### Community 123 - "_transport_is_https"
Cohesion: 0.50
Nodes (4): Whether this request's cookie will travel over https. The edge always…, _transport_is_https(), The Secure-cookie decision follows the wire, not the environment label.…, test_transport_is_https_decision()

### Community 124 - "paginate"
Cohesion: 0.15
Nodes (13): list_audit_logs(), datetime, DbSession, Depends, get, PageParamsDep, Newest-first audit trail with optional filters. No write routes exist for this…, paginate() (+5 more)

### Community 126 - "APIModel"
Cohesion: 0.04
Nodes (78): Agent-facing schemas. Payloads are data only — never executed., ApiKeyCreateRequest, API key schemas. Raw keys appear exactly once, at creation., ApplicationSummary, Application API schemas., Application as embedded in project outputs (no deployment summary)., AuditOut, Schemas for the read-only audit log API. The audit table is append-only; these… (+70 more)

### Community 137 - "Hub"
Cohesion: 0.06
Nodes (55): _authenticate_api_key(), _close_socket(), Connection, _entity_exists(), _frame_org(), Hub, _is_same_origin(), _org_id_from_frame() (+47 more)

### Community 146 - "_optional_actor"
Cohesion: 0.67
Nodes (3): _optional_actor(), AsyncSession, Resolve credentials if presented; None for truly anonymous calls.

### Community 147 - "ProjectCreate"
Cohesion: 0.67
Nodes (3): ProjectBase, ProjectCreate, Payload to create a project; owner defaults to the caller.

### Community 148 - "postgres service (PostgreSQL 17, loopback :5433)"
Cohesion: 0.29
Nodes (7): postgres service (PostgreSQL 17, loopback :5433), Fernet encryption at rest (ENCRYPTION_KEY, write-once), Backups (pgdata volume, nightly pg_dump, ephemeral Redis), Required secrets (POSTGRES_PASSWORD, JWT_SECRET >= 32 chars, ENCRYPTION_KEY Fernet), Production hardening checklist (secrets, ENVIRONMENT, no seed, TLS, rotation), Compose vs host network namespaces (postgres:5432 vs 127.0.0.1:5433), Simulation mode (SIMULATION_MODE)

### Community 150 - "nexusops-understand.mjs"
Cohesion: 0.33
Nodes (5): COMMON, meta, out, READERS, SCHEMA

### Community 151 - "Invisible account lockout (5 fails -> 15 min, enumeration resistance)"
Cohesion: 0.33
Nodes (6): Invisible account lockout (5 fails -> 15 min, enumeration resistance), Unified error envelope (code, message, request_id), Per-IP rate limiting (Redis fixed window), Request lifecycle (edge -> middleware -> rate limit -> deps -> router), Client IP resolution (resolve_client_ip, TRUSTED_PROXY_CIDRS, XFF overwrite), EmailStr rejects reserved domains (login 422 on .test/.local/.arpa)

### Community 152 - "resolve_auth"
Cohesion: 0.13
Nodes (21): get_current_user(), get_identity(), get_optional_user(), DbSessionDep, Request, Resolve credentials **and** the active organization. ``require_org=False`` is…, Org-scoped authentication: identity + validated active organization. Also…, Identity-only authentication for the pre-org exemptions (no scope). (+13 more)

### Community 153 - "instant_pacing"
Cohesion: 0.40
Nodes (4): instant_pacing(), fixture, MonkeyPatch, Remove the per-line sleeps; pacing bounds are asserted separately.

### Community 154 - "nexusops-draft.mjs"
Cohesion: 0.40
Nodes (4): DOCS, meta, SPINE, VERIFY_RULES

### Community 156 - "nexusops-challenge.mjs"
Cohesion: 0.33
Nodes (5): CHALLENGE_COMMON, meta, RESEARCH_COMMON, SCHEMA, TASKS

### Community 157 - "pytest"
Cohesion: 0.18
Nodes (14): _enrolled(), _heartbeat(), Agent ingest pipeline: hello, heartbeat, staleness transitions, events., A container absent from a later heartbeat is gone from the daemon., A payload at the agent's cap may be truncated — absence proves nothing., test_heartbeat_at_container_cap_skips_reconciliation(), test_heartbeat_removes_vanished_containers(), test_heartbeat_updates_status_metrics_and_containers() (+6 more)

### Community 163 - "ApplicationCreate"
Cohesion: 0.29
Nodes (6): ApplicationBase, ApplicationCreate, Any, field_validator, Shared application fields; ``build_config`` is a free-form dict., Payload to register an application under a project.

### Community 165 - "require_server"
Cohesion: 0.13
Nodes (19): agent_heartbeat(), agent_hello(), _presented_token(), DbDep, post, Request, Response, First contact after enrollment: persist static host facts, negotiate cadence. (+11 more)

### Community 170 - "get_secret_detail"
Cohesion: 0.33
Nodes (7): _collect_refs(), _detail(), get_secret_detail(), Any, Recursively collect ``${secret:KEY}`` references from config values., Serialise secret metadata. No value-bearing field may appear here., Metadata for one secret including the rotator's email when known.

## Knowledge Gaps
- **408 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+403 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1639 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AuthContext` connect `AuthContext` to `NotFound`, `deps.py`, `Hub`, `project_service.py`, `projects.py`, `incidents.py`, `deployment_engine.py`, `_optional_actor`, `test_deployments_simulated.py`, `list_containers`, `metrics_service.py`, `resolve_auth`, `monitor_service.py`, `auth_service.py`, `container_service.py`, `create_host`, `docker_hosts.py`, `monitors.py`, `server_service.py`, `v1/channels.py`, `test_permissions.py`, `servers.py`, `create_secret`, `role_service.py`, `rotate_secret`, `notification_service.py`, `v1/auth.py`, `update_channel`, `events.py`, `organization_service.py`, `hash_token`, `paginate`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Why does `docs/troubleshooting.md - symptom -> cause -> fix runbook` connect `README.md - NexusOps overview` to `Invisible account lockout (5 fails -> 15 min, enumeration resistance)`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Are the 81 inferred relationships involving `AuthContext` (e.g. with `TenancyScopeError` and `MembershipStatus`) actually correct?**
  _`AuthContext` has 81 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `apiGet()` (e.g. with `ContainerDetailPage.test.tsx` and `mockApi()`) actually correct?**
  _`apiGet()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `meta`, `SCHEMA`, `RESEARCH_COMMON` to the rest of the system?**
  _408 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `AuthContext.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.05319148936170213 - nodes in this community are weakly interconnected._
- **Should `DockerHostsPage.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.06013986013986014 - nodes in this community are weakly interconnected._