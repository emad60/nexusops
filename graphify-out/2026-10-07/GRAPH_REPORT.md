# Graph Report - nexusops  (2026-10-07)

## Corpus Check
- 298 files · ~274,647 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: (none) 8, .example 1, .service 1)

## Summary
- 4268 nodes · 12638 edges · 166 communities (145 shown, 21 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1062 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7a92b064`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- AuthContext.tsx
- v1/auth.py
- App.tsx
- apiGet
- user_service.py
- typing
- resolve_client_ip
- DeploymentListPage.tsx
- useAuth
- test_operations.py
- org_scope
- ServerDetailPage.tsx
- v1/health.py
- client.ts
- project_service.py
- incidents.py
- deployment_engine.py
- SimulatedDockerProvider
- run_async
- v1/agent.py
- test_deployments_simulated.py
- containers.py
- metrics_service.py
- seed.py
- Domain Routing — NexusOps
- monitor_service.py
- Node & Agent Architecture
- test_agent_backoff.py
- SimulatedDeploymentRunner
- nexusops_agent.py
- integration/conftest.py
- auth_service.py
- container_service.py
- docker_host_service.py
- get_host
- test_operation_registry.py
- monitors.py
- v1/search.py
- server_service.py
- test_channel
- DockerProvider
- test_monitor_transport.py
- AgentContainerIn
- types.ts
- docker_real.py
- test_permissions.py
- Conflict
- update_server
- BadRequest
- create_secret
- create_role
- test_schemas_server.py
- create_api_key
- DashboardPage.tsx
- login
- core/tenancy.py
- list_operations
- alembic
- notification_service.py
- helpers.py
- compilerOptions
- v1/deployments.py
- middleware.py
- organizations.py
- StepLine
- notification_sender.py
- monitor.py
- test_pagination.py
- test_tenancy_allowlist.py
- package.json
- list_events
- test_secrets.py
- README.md - NexusOps overview
- models/__init__.py
- api service (FastAPI / uvicorn :8000)
- resolve_secrets_for_environment
- monitor_transport.py
- enums.py
- redact_mapping
- me
- test_event_registry.py
- Settings
- UserOut
- tests/conftest.py
- Hub
- list_sessions
- devDependencies
- operation_service.py
- AppError
- test_migration_drift.py
- client_ip.py
- Deployment Architecture — NexusOps (target state)
- test_notifications.py
- test_tenant_isolation.py
- bearer
- ensure_dispatchable
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- journey.spec.ts
- DockerProviderError
- 2. Entities
- register
- _is_same_origin
- alert_service.py
- router.py
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- viewer_in_a
- test_error_logging.py
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- _transport_is_https
- AuthContext
- test_app_gating.py
- log_service.py
- scripts
- _containers_for
- ScopedSession
- Multi-Tenancy Architecture
- dependencies
- DeploymentDetailPage.tsx
- generate_secrets.sh
- rate_limit.py
- server_payload
- Product Roadmap — NexusOps Multi-Tenant Platform
- 4. Operations framework (added in this pass)
- .__init__
- APIModel
- install.sh
- docker-entrypoint.sh
- integration/__init__.py
- test_ws_hub.py
- CLAUDE.md - project graphify rules
- Graphify query workflow (query / path / explain / update)
- frontend/index.html - SPA shell
- NexusOps Favicon — stylized letter 'N' lettermark in sky blue (#38bdf8) on a dark navy rounded square (#0b1120, 7px corner radius)
- nexusops-backend
- Any
- hub.py
- postgres service (PostgreSQL 17, loopback :5433)
- assert_error_code
- nexusops-understand.mjs
- Invisible account lockout (5 fails -> 15 min, enumeration resistance)
- client_ip
- instant_pacing
- nexusops-draft.mjs
- nexusops-challenge.mjs
- pytest
- AgentClient
- scope_matches
- _FakeAsyncClient
- Authorization Architecture
- sweep_deployments
- get_meta
- validate_endpoint_url
- UUID
- 4. DNS ownership verification
- _FakeSession

## God Nodes (most connected - your core abstractions)
1. `AuthContext` - 140 edges
2. `APIModel` - 117 edges
3. `apiGet()` - 76 edges
4. `get_settings()` - 69 edges
5. `NotFound` - 64 edges
6. `record()` - 64 edges
7. `publish()` - 60 edges
8. `PageParams` - 55 edges
9. `apiPost()` - 55 edges
10. `Server` - 54 edges

## Surprising Connections (you probably didn't know these)
- `0. What shipped (Phase 1)` --references--> `resolve_auth()`  [INFERRED]
  docs/authorization.md → backend/app/api/deps.py
- `6. Enforcement mechanics (unchanged patterns, one addition)` --references--> `resolve_auth()`  [INFERRED]
  docs/authorization.md → backend/app/api/deps.py
- `3. Cross-cutting decisions` --references--> `require_permission()`  [INFERRED]
  docs/domain-model.md → backend/app/api/deps.py
- `10. Phase 7 — Teams, grants & custom roles` --references--> `require_permission()`  [INFERRED]
  docs/product-roadmap.md → backend/app/api/deps.py
- `3.2 Enrollment v2` --references--> `require_server()`  [INFERRED]
  docs/node-agent-architecture.md → backend/app/api/v1/agent.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three authentication credential families with centralized permission checks** — docs_api_md_auth, docs_api_md_refresh_rotation, docs_api_md_api_keys, docs_agent_md_enrollment_token, docs_api_md_permission_model [EXTRACTED 1.00]
- **NexusOps compose stack services** — docker_compose_yml_nexusops_stack, docker_compose_yml_postgres_service, docker_compose_yml_redis_service, docker_compose_yml_mailpit_service, docker_compose_yml_api_service, docker_compose_yml_worker_service, docker_compose_yml_scheduler_service, docker_compose_yml_frontend_service, docker_compose_yml_nginx_service [EXTRACTED 1.00]
- **WebSocket real-time fan-out spine** — docs_architecture_md_websocket_hub, docs_api_md_websocket_channels, docker_compose_yml_redis_service, docs_architecture_md_event_bus, readme_react_spa [INFERRED 0.85]

## Communities (166 total, 21 thin omitted)

### Community 0 - "AuthContext.tsx"
Cohesion: 0.05
Nodes (29): Membership, User, AuthContext, AuthProvider(), AuthState, isOrgSelectionError(), MeResponse, ORG_SELECTION_FAILURES (+21 more)

### Community 1 - "v1/auth.py"
Cohesion: 0.16
Nodes (18): Authentication routes: register, login, refresh rotation, logout, me, password., LoginRequest, MeOut, PasswordChangeRequest, Authentication request/response schemas., Optional body for non-browser clients; the cookie takes precedence., Token response, plus everything a client needs to pick an organization. The JWT…, Caller identity, their organizations, and their authority in the active one.… (+10 more)

### Community 2 - "App.tsx"
Cohesion: 0.04
Nodes (80): ApiKeyOut, EnvironmentOut, EventItem, Page, ProjectOut, AlertsPage, ApiKeysPage, AuditLogPage (+72 more)

### Community 3 - "apiGet"
Cohesion: 0.06
Nodes (73): apiDelete(), apiGet(), apiPatch(), apiPost(), ApplicationOut, DeliveryOut, IncidentEventOut, IncidentDetailPage (+65 more)

### Community 4 - "user_service.py"
Cohesion: 0.11
Nodes (40): UserStatus, _apply_deactivation(), _assert_not_last_active_member(), _assert_not_last_active_superadmin(), create_user(), deactivate_user(), get_by_email(), get_member() (+32 more)

### Community 5 - "typing"
Cohesion: 0.07
Nodes (59): permission_dep(), Any, Dependency factory enforcing a permission; returns 403 when denied., require_permission(), list_alerts(), Depends, Alert inbox endpoints. Authenticated users see the shared operator feed., Unread alerts first, then newest first. (+51 more)

### Community 6 - "resolve_client_ip"
Cohesion: 0.28
Nodes (15): Request, Real client address for *request* per the trust model above., resolve_client_ip(), make_request(), Request, Unit tests for the chained-proxy client-IP resolver (app/core/client_ip.py)., test_all_trusted_entries_fall_back_to_peer(), test_empty_header_value_falls_back_to_peer() (+7 more)

### Community 7 - "DeploymentListPage.tsx"
Cohesion: 0.09
Nodes (18): DeploymentOut, DeploymentListPage, formatDurationMs(), AppOption, DEPLOYMENT_STATUSES, DeploymentListPage(), DeploymentRow, errorMessage() (+10 more)

### Community 8 - "useAuth"
Cohesion: 0.05
Nodes (47): SearchResult, LoginPage, OrganizationRequiredPage, UsersPage, mocks, Probe(), USER, useAuth() (+39 more)

### Community 9 - "test_operations.py"
Cohesion: 0.08
Nodes (49): expire_operations(), Expire node operations past their deadline — pending and claimed alike. A…, _dispatch(), _dispatch_body(), _enrolled_node(), _mutate_in_system_scope(), MonkeyPatch, Node operations: the compare-and-set state machine and its tenant boundary.… (+41 more)

### Community 10 - "org_scope"
Cohesion: 0.06
Nodes (70): current_scope(), org_scope(), ``'org'``, ``'system'`` or ``'unset'``., Run the enclosed block as a single organization. Nesting the *same* org is a…, _run(), _collect_logs(), _run(), _run() (+62 more)

### Community 11 - "ServerDetailPage.tsx"
Cohesion: 0.09
Nodes (35): MetricPoint, ServerListPage, CheckboxField(), ChartSeries, LineChart(), LineChartProps, PAD, buildServerPayload() (+27 more)

### Community 12 - "v1/health.py"
Cohesion: 0.20
Nodes (13): liveness(), get, Response, Health probes: liveness (always cheap) and readiness (checks dependencies).…, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness(), HealthOut (+5 more)

### Community 13 - "client.ts"
Cohesion: 0.07
Nodes (38): API_BASE, apiRequest(), buildUrl(), extractError(), getAccessToken(), getActiveOrgId(), onActiveOrgChange(), ORGANIZATION_HEADER (+30 more)

### Community 14 - "project_service.py"
Cohesion: 0.06
Nodes (105): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+97 more)

### Community 15 - "incidents.py"
Cohesion: 0.14
Nodes (32): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+24 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.11
Nodes (56): deployment_log_channel(), Deployment, DeploymentStep, AlertSeverity, DeploymentStatus, DeploymentTrigger, StepStatus, _after_commit_enqueue() (+48 more)

### Community 17 - "SimulatedDockerProvider"
Cohesion: 0.09
Nodes (29): Any, Plausible numbers derived from the row plus time-based sine noise., Implements :class:`DockerProvider` semantics against DB rows., Make a container row visible to this provider instance., Attach already-fetched log rows so ``logs()`` can replay them., _seed_int(), SimulatedDockerProvider, _log_entry() (+21 more)

### Community 18 - "run_async"
Cohesion: 0.14
Nodes (22): aggregate_metrics(), expire_sessions(), _run(), task, Revoke sessions past their expiry and purge dead refresh tokens., Reconcile every registered Docker host; pull recent logs from real ones., Time-based retention per source plus a per-container row cap., retry_notifications() (+14 more)

### Community 19 - "v1/agent.py"
Cohesion: 0.11
Nodes (30): agent_heartbeat(), agent_hello(), claim_operation(), _presented_token(), DbDep, post, Request, Response (+22 more)

### Community 20 - "test_deployments_simulated.py"
Cohesion: 0.15
Nodes (27): execute_deployment(), Run one deployment to a terminal state. Never raises; safe to re-run., _as_worker(), _delivery_chain(), _owner_ctx(), _queue(), _queued_with_recorder(), Deployment engine over the simulated runner: success, failure, rollback. (+19 more)

### Community 21 - "containers.py"
Cohesion: 0.06
Nodes (62): _action_route(), _endpoint(), _container_out(), _decode_frame(), _ev(), get_container(), _like_pattern(), list_containers() (+54 more)

### Community 22 - "metrics_service.py"
Cohesion: 0.06
Nodes (53): get_dashboard_summary(), get_latest_server_metrics(), get_server_metrics(), CurrentUser, DbDep, Depends, get, UUID (+45 more)

### Community 23 - "seed.py"
Cohesion: 0.05
Nodes (85): argon2, argon2_exceptions, fail_on_bad_config(), get_settings(), Central configuration. All runtime configuration flows through this module so…, Return the cached settings singleton., Exit immediately with a readable message if configuration is invalid. Also…, Unauthorized (+77 more)

### Community 24 - "Domain Routing — NexusOps"
Cohesion: 0.08
Nodes (24): 10. Wildcards and catch-all, 11. User journey, 12. API surface, permissions, audit, 13. Monitoring tie-in, 1. Scope and current state, 2. Where nginx runs, 3.1 Domain, 3.2 Route (+16 more)

### Community 25 - "monitor_service.py"
Cohesion: 0.14
Nodes (39): MonitorStatus, Monitor, get_transport(), Pick the transport matching the monitor URL scheme., MonitorCreate, MonitorUpdate, Payload for POST /monitors., Partial update; ``url`` changes are re-validated against the SSRF guard. (+31 more)

### Community 26 - "Node & Agent Architecture"
Cohesion: 0.09
Nodes (23): Mark the agent enrolled and persist its static host facts., register_agent_hello(), 1. Scope and stance, 3.1 Current state (real), 3.2 Enrollment v2, 3.3 Token storage & rotation with dual-token grace, 3.4 Revocation semantics — fixing the 401 hot-loop, 3.5 Reconnect / offline states (+15 more)

### Community 27 - "test_agent_backoff.py"
Cohesion: 0.15
Nodes (21): agent_fixture(), _install_sleep(), fake_sleep(), _load_agent(), _patch_host(), Any, fixture, MonkeyPatch (+13 more)

### Community 28 - "SimulatedDeploymentRunner"
Cohesion: 0.25
Nodes (23): Staged docker-style simulation used by v1 deployments., Canonical step identifiers stored on :class:`DeploymentStep` rows., SimulatedDeploymentRunner, StepName, _collect(), _ctx(), Unit tests for SimulatedDeploymentRunner (async generators, no broker)., RESOLVE_CONFIG is planned by the engine, not produced by a runner. (+15 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.10
Nodes (29): build_heartbeat(), collect_container_stats(), collect_containers(), cpu_percent_since(), disk_stats(), _docker_request(), _interruptible_sleep(), load1() (+21 more)

### Community 30 - "integration/conftest.py"
Cohesion: 0.14
Nodes (20): alembic_config, client(), _ensure_database(), _migrated_database(), org_db(), owner(), AsyncClient, fixture (+12 more)

### Community 31 - "auth_service.py"
Cohesion: 0.11
Nodes (47): active_memberships(), Membership, The user's memberships in non-suspended organizations, oldest first. Reads only…, System scope bound to *db*, for rows that have no organization. Used by exactly…, system_write_scope(), ActorType, AuditResult, Opaque refresh token; only its SHA-256 hash is stored. Rotation chain: on… (+39 more)

### Community 32 - "container_service.py"
Cohesion: 0.10
Nodes (40): ContainerHealth, ContainerStatus, Container, Observed container state mirrored from an agent or docker provider., clip(), Truncate *text* to *limit* characters, stripping control chars., describe_provider_error(), is_simulated() (+32 more)

### Community 33 - "docker_host_service.py"
Cohesion: 0.12
Nodes (37): DockerHostStatus, DockerHost, DockerHostCreate, DockerHostPingOut, DockerHostUpdate, Result of probing a host's provider endpoint., Payload for registering a docker host., Partial update payload; only supplied fields change. (+29 more)

### Community 34 - "get_host"
Cohesion: 0.12
Nodes (30): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+22 more)

### Community 35 - "test_operation_registry.py"
Cohesion: 0.12
Nodes (20): OperationType, The whitelist. Nothing outside this enum ships as an exec surface. Each type…, OperationCreate, Any, Validate *params* against the type's model and return the stored form.…, Request one whitelisted action on one node., validate_params(), MonkeyPatch (+12 more)

### Community 36 - "monitors.py"
Cohesion: 0.16
Nodes (33): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+25 more)

### Community 37 - "v1/search.py"
Cohesion: 0.13
Nodes (31): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+23 more)

### Community 38 - "server_service.py"
Cohesion: 0.06
Nodes (70): _detail(), AsyncSession, Canonical Redis pub/sub channel names shared by API, workers and WS hub., server_metrics_channel(), ServerStatus, Server, _actor_kwargs(), _apply_agent_entry() (+62 more)

### Community 39 - "test_channel"
Cohesion: 0.19
Nodes (19): create_channel(), delete_channel(), get_channel(), DbDep, delete, ManageCtx, post, Request (+11 more)

### Community 40 - "DockerProvider"
Cohesion: 0.08
Nodes (14): ContainerInfo, DockerProvider, Any, datetime, Protocol, List containers visible to the provider., Inspect a single container by id (short ids allowed)., List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``. (+6 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.13
Nodes (34): CheckResult, HTTPMonitorTransport, Deterministic fake checker for ``sim://`` monitors and demo environments.…, Real HTTP(S) probe using httpx with per-monitor settings. Redirects are…, SimulatedTransport, _check(), clock(), FakeClock (+26 more)

### Community 42 - "AgentContainerIn"
Cohesion: 0.09
Nodes (43): AgentContainerIn, AgentHeartbeatIn, AgentHelloIn, field_validator, First contact from an agent after enrollment; fills static host facts., Observed container state reported by an agent., Periodic metrics + observed containers from an enrolled agent., agent_fixture() (+35 more)

### Community 43 - "types.ts"
Cohesion: 0.02
Nodes (105): ApiError, AlertOut, AuditEntry, ChannelOut, CheckOut, ContainerOut, CursorPage, DeploymentLogLine (+97 more)

### Community 44 - "docker_real.py"
Cohesion: 0.09
Nodes (25): ContainerStats, Point-in-time resource usage snapshot., _as_float(), _compute_stats(), _cpu_percent(), _network_bytes(), parse_log_line(), parse_rfc3339() (+17 more)

### Community 45 - "test_permissions.py"
Cohesion: 0.12
Nodes (15): permission_exists(), _auth_context(), _FakeCtx, Unit tests for the permission registry, scope matching and RBAC gate., Duck-typed stand-in for AuthContext., A fake context in the given organization. ``membership_status=None`` models a…, test_api_key_scope_intersects_role_permissions(), test_membership_is_required_for_authority() (+7 more)

### Community 46 - "Conflict"
Cohesion: 0.20
Nodes (20): Conflict, create_role(), delete_role(), get_role(), list_roles(), AsyncSession, Request, Role (+12 more)

### Community 47 - "update_server"
Cohesion: 0.13
Nodes (24): create_server(), delete_server(), get_server(), list_tags(), DbDep, delete, get, post (+16 more)

### Community 48 - "BadRequest"
Cohesion: 0.08
Nodes (58): BadRequest, UnprocessableEntity, assert_safe_tcp_endpoint(), assert_safe_url(), _is_forbidden_address(), is_simulation_url(), _raise_block(), Validate *url* for outbound requests; return the parsed URL or raise 422.… (+50 more)

### Community 49 - "create_secret"
Cohesion: 0.06
Nodes (59): create_secret(), delete_secret(), get_secret(), list_secrets(), DbSession, delete, Depends, get (+51 more)

### Community 50 - "create_role"
Cohesion: 0.13
Nodes (22): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, delete, get (+14 more)

### Community 51 - "test_schemas_server.py"
Cohesion: 0.21
Nodes (22): Payload for registering a server., Partial update. ``tags`` replaces the full set when provided., ServerCreate, ServerUpdate, _base(), parametrize, Unit tests for app.schemas.server (validation only, no I/O)., test_empty_ip_is_allowed_but_whitespace_collapses() (+14 more)

### Community 52 - "create_api_key"
Cohesion: 0.16
Nodes (17): create_api_key(), list_api_keys(), CurrentUser, DbSessionDep, delete, get, post, Request (+9 more)

### Community 53 - "DashboardPage.tsx"
Cohesion: 0.12
Nodes (14): DashboardSummary, DashboardPage, asFeedItem(), badgeLevel(), DashboardPage(), FeedItem, formatTimestamp(), MetaInfo (+6 more)

### Community 54 - "login"
Cohesion: 0.21
Nodes (19): change_password(), _clear_refresh_cookie(), _cookies_secure(), login(), logout(), DbSessionDep, IdentityUser, post (+11 more)

### Community 55 - "core/tenancy.py"
Cohesion: 0.09
Nodes (35): _apply_scope_guc(), _desired_guc(), _guard(), _has_org_predicate(), install_tenancy_guards(), _mappers_of(), _org_scoped_classes(), org_scoped_table_names() (+27 more)

### Community 56 - "list_operations"
Cohesion: 0.18
Nodes (19): cancel_operation(), create_operation(), get_operation(), list_operations(), DbDep, Depends, get, post (+11 more)

### Community 57 - "alembic"
Cohesion: 0.05
Nodes (22): alembic, _app_role_credentials(), _assert_fully_backfilled(), _backfill_org_ids(), _drop_constraint(), add tenancy foundation Phase 1 of the platform roadmap: organizations,…, Carry a value into a PL/pgSQL block. ``CREATE ROLE``/``ALTER ROLE`` are utility…, Application role name/password from settings (never hard-coded). (+14 more)

### Community 58 - "notification_service.py"
Cohesion: 0.10
Nodes (50): ChannelType, DeliveryStatus, NotificationChannel, NotificationDelivery, A delivery target (email address / webhook endpoint). ``config_ciphertext``…, ChannelCreate, ChannelUpdate, EmailConfig (+42 more)

### Community 59 - "helpers.py"
Cohesion: 0.11
Nodes (33): cookie_attributes(), login_account(), AsyncClient, Response, Pure helpers for journey tests: payloads, auth shortcuts, cookie parsing., Login and unpack tokens, the raw cookie header and the user object., Bootstrap owner account + session; returns ``(credentials, login_result)``. The…, A fresh, deliverable-shaped address unique to a single test. ``example.com`` is… (+25 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "v1/deployments.py"
Cohesion: 0.11
Nodes (37): cancel_deployment(), _emails_for(), get_deployment(), list_application_deployments(), _list_deployments(), _parse_sort(), _parse_statuses(), alias (+29 more)

### Community 62 - "middleware.py"
Cohesion: 0.09
Nodes (26): ASGIApp, _error_payload(), FastAPI, Request, register_exception_handlers(), handle_app_error(), handle_http_exception(), handle_unexpected() (+18 more)

### Community 63 - "organizations.py"
Cohesion: 0.16
Nodes (17): create_organization(), list_my_organizations(), CurrentUser, DbSessionDep, get, IdentityUser, post, Request (+9 more)

### Community 64 - "StepLine"
Cohesion: 0.10
Nodes (23): _commit_short(), DeploymentRunner, _pace(), Exception, Protocol, Deployment runner port plus a faithful simulated implementation.…, Stream output lines for *step_name*; raise StepFailure to fail it., Deterministic per-line delay between 0.05s and 0.35s. (+15 more)

### Community 65 - "notification_sender.py"
Cohesion: 0.16
Nodes (16): NotificationError, Any, BaseException, Exception, Low-level notification transports: SMTP email and outgoing webhooks. These…, POST *payload* as JSON to *url*; 2xx is success, anything else raises. Response…, Raised when a delivery attempt fails. Message is safe to persist., Bounded, single-line, content-free error reason. (+8 more)

### Community 66 - "monitor.py"
Cohesion: 0.11
Nodes (24): is_sensitive_header(), mask_sensitive_headers(), MonitorBase, MonitorSortField, Schemas for uptime monitors and their check history., Aggregated availability over a lookback window., Whitelist of sortable columns exposed as query parameters., True when *name* looks like it carries a credential (Authorization etc.). (+16 more)

### Community 67 - "test_pagination.py"
Cohesion: 0.08
Nodes (40): list_channels(), list_deliveries(), Depends, get, ReadCtx, Keyset-paged delivery log (most recently scheduled first)., list_container_logs(), Keyset-paginated log rows ordered newest-first (ts DESC, id DESC). (+32 more)

### Community 68 - "test_tenancy_allowlist.py"
Cohesion: 0.20
Nodes (14): AST, _actual_callers(), _calls_system_scope(), _module_path(), The system-scope allowlist is the only fence around the tenancy carve-out.…, Every module that could open a system scope: ``app/`` plus the scripts., No module may lift tenant isolation without being named in the list., Every listed module must still be a real caller, so the list stays short. (+6 more)

### Community 69 - "package.json"
Cohesion: 0.13
Nodes (15): name, private, type, version, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom (+7 more)

### Community 70 - "list_events"
Cohesion: 0.22
Nodes (13): _decode_cursor(), _encode_cursor(), list_event_types(), list_events(), datetime, DbSession, Depends, get (+5 more)

### Community 71 - "test_secrets.py"
Cohesion: 0.18
Nodes (15): _create(), _environment_config(), Secrets: metadata-only reads, rotation versioning, deploy-time resolution., Project → application → environment carrying *config*; returns its id., A reference naming no secret must abort, not resolve to an empty value.…, A row this ENCRYPTION_KEY cannot decrypt must abort, not yield ``""``., ${secret:KEY} placeholders resolve through decrypt at deploy time., test_create_and_list_return_metadata_only() (+7 more)

### Community 72 - "README.md - NexusOps overview"
Cohesion: 0.06
Nodes (57): docker-compose.dev.yml - dev overlay, docker-compose.docker-sock.yml - docker socket override, docker-compose.yml - full stack definition, docs/agent.md - agent guide, docs/api.md - API guide, Append-only audit log (Postgres BEFORE UPDATE OR DELETE trigger), docs/architecture.md - system architecture, 10. Status/expiry tracking and monitor tie-in (+49 more)

### Community 73 - "models/__init__.py"
Cohesion: 0.06
Nodes (79): _database_url(), Alembic environment: metadata comes from app.models, URL from app settings., Migrations run as the table **owner**, never as the application role. The owner…, Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online(), Owner-role DSN for Alembic and the container entrypoint. Migrations… (+71 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "resolve_secrets_for_environment"
Cohesion: 0.17
Nodes (14): Exception, A ``${secret:KEY}`` reference could not be resolved. Fail-closed. Carries…, One successfully resolved reference: metadata for audit, no value., Outcome of resolving an environment's config references., Resolve every ``${secret:KEY}`` reference in an environment's config. INTERNAL…, resolve_secrets_for_environment(), ResolvedSecrets, SecretReference (+6 more)

### Community 76 - "monitor_transport.py"
Cohesion: 0.08
Nodes (27): assert_safe_url_async(), SSRF guard applied to every operator-supplied outbound URL. Monitors and…, Async wrapper around :func:`assert_safe_url`; DNS runs off the loop., CheckOutcome, coerce_headers(), _decode(), MonitorTransport, Any (+19 more)

### Community 77 - "enums.py"
Cohesion: 0.12
Nodes (39): CredentialKind, EventLevel, IncidentEventKind, IncidentSeverity, IncidentStatus, LogLevel, Closed registries of domain enumerations. Member names equal their values…, String enum; member names equal values so name/value storage never disagrees. (+31 more)

### Community 78 - "redact_mapping"
Cohesion: 0.22
Nodes (13): _is_sensitive_key(), Substring match on a normalised key so header-style names are caught too.…, Return a copy of *data* with sensitive values replaced. Used by audit metadata…, redact_mapping(), parametrize, Unit tests for app.core.logging redaction (pure functions only)., test_case_insensitive_substring_match(), test_flat_sensitive_keys_redacted() (+5 more)

### Community 79 - "me"
Cohesion: 0.18
Nodes (10): me(), get, The caller's identity, organizations, and authority in the active one.…, Membership, Organization, effective_permissions(), permissions_for_role(), User (+2 more)

### Community 80 - "test_event_registry.py"
Cohesion: 0.21
Nodes (8): event_type_catalogue(), is_known_event_type(), Canonical registry of system-event types. Single source of truth shared by…, Return True when *event_type* is part of the canonical registry., Serialise the registry for the ``/events/types`` endpoint., Registry coherence: schema-advertised event types must equal the canonical…, test_catalogue_serialises_every_entry(), test_known_event_lookup()

### Community 81 - "Settings"
Cohesion: 0.14
Nodes (6): field_validator, model_validator, Username from :attr:`database_url`, or ``None`` if it is unparseable., Validated application settings (loaded from environment / .env)., Settings, BaseSettings

### Community 82 - "UserOut"
Cohesion: 0.13
Nodes (23): create_user(), deactivate_user(), get_user(), CurrentUser, DbSessionDep, delete, get, post (+15 more)

### Community 83 - "tests/conftest.py"
Cohesion: 0.22
Nodes (7): configure_test_env(), Test bootstrap: pin every cached setting BEFORE the first ``app`` import. The…, KEY=VALUE pairs from the repo .env (first definition wins); never logged., Export the exact settings the app caches; host values cannot leak through., _read_dot_env(), os, pathlib

### Community 84 - "Hub"
Cohesion: 0.14
Nodes (14): _close_socket(), Connection, Hub, _params_key(), WebSocket, Connection registry, Redis fan-in listener and per-socket pumps., Spawn the Redis fan-in listener (idempotent)., Cancel the listener and close every socket (service restart). (+6 more)

### Community 85 - "list_sessions"
Cohesion: 0.19
Nodes (12): list_sessions(), CurrentUser, DbSessionDep, delete, get, Request, UUID, Active sessions of this organization's members. Defaults to the caller's own;… (+4 more)

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "operation_service.py"
Cohesion: 0.16
Nodes (30): OperationStatus, Lifecycle of one node operation (node-agent-architecture.md §5.1).…, Operation, One whitelisted action for one node, with a CAS lifecycle. ``attempts`` is…, _active_org(), cancel_operation(), claim_operation(), create_operation() (+22 more)

### Community 88 - "AppError"
Cohesion: 0.20
Nodes (16): AppError, Exception, Base class for expected, client-facing errors., _authenticate_api_key(), _authenticate_jwt(), _bind_organization(), _load_permissions(), _org_id_from_frame() (+8 more)

### Community 89 - "test_migration_drift.py"
Cohesion: 0.25
Nodes (7): alembic_autogenerate, alembic_migration, Model / migration drift: the schema in the database must match the models.…, ``Base.metadata`` and the migrated database must describe the same schema., The DB whitelist and ``OperationType`` are the same closed set. The migration…, test_models_and_migrations_do_not_drift(), test_operations_type_check_matches_the_enum()

### Community 90 - "client_ip.py"
Cohesion: 0.29
Nodes (7): _is_trusted(), _parse_networks(), Client-IP resolution behind chained reverse proxies. The API never takes TCP…, Parse a comma-separated CIDR list; malformed entries are skipped., test_parse_networks_skips_malformed_entries(), functools, _Network

### Community 91 - "Deployment Architecture — NexusOps (target state)"
Cohesion: 0.15
Nodes (13): 10. Events and WS during runs, 11. Post-deploy hooks, 12. Rollback semantics (existing behavior kept), 13. The simulated runner stays — labeled, 14. Open questions, 3. Target pipeline, 4. Runner registry — the DI fix, 6. Phased scope (+5 more)

### Community 92 - "test_notifications.py"
Cohesion: 0.39
Nodes (8): _channel(), _delivery(), UUID, Notification channel + delivery-log endpoints. Regression coverage for GET…, The same event frame consumed twice queues ONE delivery per channel. Every API…, test_dispatch_frame_is_idempotent_across_workers(), test_list_deliveries_filters_by_channel(), test_list_deliveries_serializes_rows()

### Community 93 - "test_tenant_isolation.py"
Cohesion: 0.06
Nodes (48): dispose_engine(), get_engine(), get_sessionmaker(), async_sessionmaker, AsyncEngine, AsyncSession, apply_scope_to_session(), Run the enclosed block with tenant filtering off (maintenance only). ``reason``… (+40 more)

### Community 94 - "bearer"
Cohesion: 0.08
Nodes (27): bearer(), error_of(), login_headers(), Any, Headers for a logged-in caller, including its active organization., Unwrap an API error envelope., Bearer header, optionally naming the active organization. Every org-scoped…, Sessions must carry the real client address, not the proxy hop's peer. Behind… (+19 more)

### Community 95 - "ensure_dispatchable"
Cohesion: 0.33
Nodes (7): _bounded(), ensure_dispatchable(), Any, Keep one agent report from becoming an unbounded row. The agent is…, The registry entry for *op_type* (KeyError is a programming error)., Refuse a type whose capability this deployment cannot confirm. The capability…, spec_for()

### Community 96 - "NexusOps (self-hosted infrastructure management and monitoring platform)"
Cohesion: 0.20
Nodes (10): mailpit service (dev SMTP sink + web UI :8025), NexusOps compose stack (8 services on one network), HIGH finding: redirect-following SSRF in uptime monitors (fixed: follow_redirects=False + per-hop guard), SSRF guard (assert_safe_url, per-redirect-hop validation, assert_safe_tcp_endpoint), Mailpit SMTP port internal-only (host-side injection needs extra mapping), Host port knobs (NEXUSOPS_HTTP_PORT/POSTGRES/REDIS/MAILPIT/VITE), SPA entry point (loads /src/main.tsx, dark color-scheme), Uptime monitors -> incidents -> notifications flow (+2 more)

### Community 97 - "REST API surface (/api/v1)"
Cohesion: 0.29
Nodes (7): Cursor (keyset) and offset pagination envelopes, Permission model (data-driven registry, require_permission, wildcard scopes), REST API surface (/api/v1), RBAC registry (PERMISSIONS + ROLE_MATRIX + scope_matches), Adding a new resource: 7-step checklist (model -> migration -> schemas -> service -> router -> tests -> frontend), Alembic migration workflow (autogenerate, models __init__ export, entrypoint apply), Command palette (Ctrl/Cmd+K)

### Community 98 - "journey.spec.ts"
Cohesion: 0.18
Nodes (11): EDGE, MAILPIT, ADMIN, Bootstrap, bootstrapVia(), test, ADMIN, formLogin() (+3 more)

### Community 99 - "DockerProviderError"
Cohesion: 0.14
Nodes (15): DockerProviderError, Exception, Provider abstraction for docker hosts (real daemon or simulated). Providers are…, A provider operation failed. ``str()`` is safe to show/log., Build a compact, secret-free description of a provider failure. Only the…, sanitize_error(), Provider selection based on a docker host's endpoint URL. Mapping: *…, _iterate() (+7 more)

### Community 100 - "2. Entities"
Cohesion: 0.14
Nodes (14): 0. Design stance, 1.1 ER diagram, 1. The hierarchy, 2.1.1 ApiKey org binding detail, 2.2.1 Environment promotion detail, 2.2 Delivery (existing models, extended), 2.3 Infrastructure — Nodes, 2.4 Routing & TLS (new subsystem) (+6 more)

### Community 101 - "register"
Cohesion: 0.33
Nodes (6): _optional_actor(), AsyncSession, Bootstrap the first owner account or accept an authenticated invitation., Resolve credentials if presented; None for truly anonymous calls., register(), UserEnvelope

### Community 102 - "_is_same_origin"
Cohesion: 0.40
Nodes (5): _is_same_origin(), Browsers always send Origin on WS handshakes, even same-origin ones. When it…, The proxy must forward the Host the browser actually used. A browser sends…, test_same_origin_compares_the_full_authority_including_port(), 7. Known limitations and unresolved issues

### Community 103 - "alert_service.py"
Cohesion: 0.12
Nodes (24): mark_all_read(), mark_read(), CurrentUser, DbDep, get, post, UUID, Mark every unread alert read; returns how many rows changed. (+16 more)

### Community 104 - "router.py"
Cohesion: 0.40
Nodes (4): websocket, WebSocket endpoint. Mounted by the app factory under ``/api/v1``., Hand the socket to the hub (auth handshake handled there)., websocket_endpoint()

### Community 105 - "redis service (Redis 7, no persistence, loopback :6390)"
Cohesion: 0.22
Nodes (11): redis service (Redis 7, no persistence, loopback :6390), WebSocket API (/api/v1/ws handshake, frames, limits), WebSocket channels (global, server-metrics, container-logs, deployment-logs, incidents), Deployment engine (queue_deployment / execute_deployment / sweeper backstop), Real-time spine: PostgreSQL system_events + Redis pub/sub, Rollback as a new deployment (rollback_of_id), WebSocket hub (framework-thin, Redis fan-in, per-socket queues), Test suites (pytest unit+integration, vitest, Playwright e2e) (+3 more)

### Community 106 - "NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)"
Cohesion: 0.18
Nodes (12): Agent security model (one-way telemetry, no command channel), Agent enrollment token (X-Agent-Token, nxa_..., SHA-256 at rest), Agent heartbeat exponential backoff (cap 5 min, exit 1 on revoked token), agent/install.sh (enrollment installer), Agent metrics collection (/proc statvfs Docker socket), NexusOps agent (stdlib-only Python, agent/nexusops_agent.py), Agent systemd hardening (ProtectSystem=strict, NoNewPrivileges), Agent ingest API (POST /agent/hello, POST /agent/heartbeat) (+4 more)

### Community 107 - "viewer_in_a"
Cohesion: 0.40
Nodes (5): org_a(), fixture, A least-privileged, **non-superadmin** member of organization A. Used to show…, The bootstrap organization plus a few resources created inside it., viewer_in_a()

### Community 108 - "test_error_logging.py"
Cohesion: 0.22
Nodes (4): Regression: the catch-all 500 handler must not log raw exception text.…, _SpyLogger, test_unhandled_exception_handler_logs_class_not_message(), fastapi_testclient

### Community 109 - "Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)"
Cohesion: 0.25
Nodes (9): API keys (X-API-Key, nxo_..., scope intersection), First boot sequence (api entrypoint migrates, compose never seeds), Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test), Makefile workflows (up/test/lint/typecheck/migrate/seed), HIGH finding: API-key scope bypass for superadmin-owned keys (fixed: scope intersection first), Security audit 2026-09 (26 raw findings -> 20 confirmed, all fixed), HIGH finding: known seed superadmin + API key backdoor (fixed: NEXUSOPS_ALLOW_SEED opt-in, one-time password), Threat model (edge attacker, malicious agent, curious operator, leaked token, SSRF) (+1 more)

### Community 110 - "_transport_is_https"
Cohesion: 0.50
Nodes (4): Whether this request's cookie will travel over https. The edge always…, _transport_is_https(), The Secure-cookie decision follows the wire, not the environment label.…, test_transport_is_https_decision()

### Community 111 - "AuthContext"
Cohesion: 0.06
Nodes (66): _attach_organization(), AuthContext, get_current_user(), get_identity(), get_optional_user(), _load_organization(), _load_permissions(), membership_for_org() (+58 more)

### Community 112 - "test_app_gating.py"
Cohesion: 0.44
Nodes (8): _app_for_environment(), MonkeyPatch, ENVIRONMENT gating contract: docs exposure and HSTS (see .env.example).…, create_app() with get_settings() patched to the given environment., test_non_production_does_not_emit_hsts(), test_non_production_keeps_docs_and_schema(), test_production_emits_hsts(), test_production_hides_docs_and_schema()

### Community 113 - "log_service.py"
Cohesion: 0.07
Nodes (39): container_log_channel(), current_org(), The organization this unit of work is acting for, if any., LogSource, create_api_key(), list_api_keys(), AsyncSession, Request (+31 more)

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "_containers_for"
Cohesion: 0.50
Nodes (4): _containers_for(), Deterministic smooth value in [base-amplitude, base+amplitude]., Stable per-server container set; one container cycles EXITED occasionally., _wave()

### Community 117 - "Multi-Tenancy Architecture"
Cohesion: 0.18
Nodes (10): Whether the runtime connection is the RLS-enforced application role. False…, 10. Migration (Phase 1), 1. Tenancy invariants, 2.1 Org creation — v1 decision, 4. Background jobs, 6. Agents, 7. The IDOR suite, 8. What stays global (+2 more)

### Community 118 - "dependencies"
Cohesion: 0.33
Nodes (6): dependencies, lucide-react, react, react-dom, react-router-dom, @tanstack/react-query

### Community 119 - "DeploymentDetailPage.tsx"
Cohesion: 0.09
Nodes (17): DeploymentStepOut, DeploymentDetailPage, ACTIVE_STATUSES, DeploymentDetailRow, DeploymentLogRow, formatLogTime(), LogLines(), StepCard() (+9 more)

### Community 120 - "generate_secrets.sh"
Cohesion: 0.47
Nodes (3): existing_real_keys(), replace_or_append(), generate_secrets.sh script

### Community 121 - "rate_limit.py"
Cohesion: 0.17
Nodes (18): RateLimited, _memory_count_and_ttl(), rate_limit(), _dependency(), Redis-backed fixed-window rate limiting as a FastAPI dependency factory. Auth-…, Fixed-window counter backed by process memory. Returns (count, ttl)., Return a dependency enforcing *limit* requests per window per IP. With…, _clean_memory_windows() (+10 more)

### Community 122 - "server_payload"
Cohesion: 0.13
Nodes (22): A valid POST /servers body with per-test overrides., server_payload(), _create_server(), Server CRUD, cascade delete, audit trail rows and audit immutability., The HTTP listing path — schema serialization is exercised end-to-end. A…, ``/servers`` is a temporary alias for pre-rename clients. It must keep working…, test_agent_token_rotation_invalidates_previous(), test_audit_log_api_serializes_and_filters() (+14 more)

### Community 123 - "Product Roadmap — NexusOps Multi-Tenant Platform"
Cohesion: 0.13
Nodes (15): 0. Stance, 10. Phase 7 — Teams, grants & custom roles, 11. Phase 8 — Backups, 12. Phase 9 — Billing & metering, 14. Biggest risks (short form), 15. Reading order, 2. Phase plan, 4. Phase 1 — Tenancy foundation (+7 more)

### Community 124 - "4. Operations framework (added in this pass)"
Cohesion: 0.67
Nodes (3): OperationSpec, Everything the control plane needs to know about one operation type.…, 4. Operations framework (added in this pass)

### Community 126 - "APIModel"
Cohesion: 0.04
Nodes (87): Agent-facing schemas. Payloads are data only — never executed., AlertOut, Schemas for operator-facing alerts., ApiKeyCreateRequest, API key schemas. Raw keys appear exactly once, at creation., AuditOut, Schemas for the read-only audit log API. The audit table is append-only; these…, One audit trail entry (no write routes ever exist for this resource).… (+79 more)

### Community 137 - "test_ws_hub.py"
Cohesion: 0.19
Nodes (22): _connection(), _drain(), _event_frame(), _fake_sessionmaker(), hub(), _Org, Any, fixture (+14 more)

### Community 146 - "Any"
Cohesion: 0.36
Nodes (6): _frame_org(), _parse_payload(), Any, Deliver one Redis message to every matching subscription., The organization an event frame belongs to, or ``None`` when it has none., Decode a Redis-published body into a JSON-safe object.

### Community 147 - "hub.py"
Cohesion: 0.06
Nodes (52): asyncio, configure_logging(), get_logger(), _orjson_dumps(), Any, Structured logging via structlog. Every log record carries timestamp, level,…, Configure structlog + stdlib logging once at process start. Everything…, PermissionSpec (+44 more)

### Community 148 - "postgres service (PostgreSQL 17, loopback :5433)"
Cohesion: 0.29
Nodes (7): postgres service (PostgreSQL 17, loopback :5433), Fernet encryption at rest (ENCRYPTION_KEY, write-once), Backups (pgdata volume, nightly pg_dump, ephemeral Redis), Required secrets (POSTGRES_PASSWORD, JWT_SECRET >= 32 chars, ENCRYPTION_KEY Fernet), Production hardening checklist (secrets, ENVIRONMENT, no seed, TLS, rotation), Compose vs host network namespaces (postgres:5432 vs 127.0.0.1:5433), Simulation mode (SIMULATION_MODE)

### Community 149 - "assert_error_code"
Cohesion: 0.20
Nodes (14): assert_error_code(), Assert envelope shape + code; returns the inner error object., Regression: lockout must not leak which emails exist. After login_max_attempts…, test_locked_account_response_is_indistinguishable(), test_metadata_endpoint_and_private_target_blocked(), _invite_user(), _org_headers(), Role-based access control: least-privileged users are properly boxed in. (+6 more)

### Community 150 - "nexusops-understand.mjs"
Cohesion: 0.33
Nodes (5): COMMON, meta, out, READERS, SCHEMA

### Community 151 - "Invisible account lockout (5 fails -> 15 min, enumeration resistance)"
Cohesion: 0.33
Nodes (6): Invisible account lockout (5 fails -> 15 min, enumeration resistance), Unified error envelope (code, message, request_id), Per-IP rate limiting (Redis fixed window), Request lifecycle (edge -> middleware -> rate limit -> deps -> router), Client IP resolution (resolve_client_ip, TRUSTED_PROXY_CIDRS, XFF overwrite), EmailStr rejects reserved domains (login 422 on .test/.local/.arpa)

### Community 152 - "client_ip"
Cohesion: 0.29
Nodes (6): Request, Response, client_ip(), Request, Best-effort client IP; honours X-Forwarded-For from trusted proxies. Delegates…, RequestResponseEndpoint

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

### Community 160 - "AgentClient"
Cohesion: 0.29
Nodes (3): AgentClient, Flag plain-HTTP transports that expose the enrollment token. The X-Agent-Token…, _UnixHTTPConnection

### Community 164 - "scope_matches"
Cohesion: 0.20
Nodes (9): Check an API-key scope list against a required permission. Supports exact match…, scope_matches(), parametrize, test_scope_matches_truth_table(), 1. Principles (already true in the codebase, kept), 5. API keys, 2.1 Identity & tenancy (new), 4.1 Audit event at resolution time (+1 more)

### Community 165 - "_FakeAsyncClient"
Cohesion: 0.22
Nodes (3): _FakeAsyncClient, _FakeRequestObj, Scripted httpx.AsyncClient: responses keyed by absolute request URL.

### Community 167 - "Authorization Architecture"
Cohesion: 0.25
Nodes (8): 0. What shipped (Phase 1), 2. Registry changes (Phase 1 + new subsystems), 3. The five system roles (target), 4. Grants (resource-level access; design now, later phase), 6. Enforcement mechanics (unchanged patterns, one addition), 7. Custom roles (later phase), 8. Permission-change audit, Authorization Architecture

### Community 168 - "sweep_deployments"
Cohesion: 0.29
Nodes (7): task, Execute one queued deployment. The engine owns all state transitions., Re-enqueue deployments the broker lost; fail ones whose worker died.…, run_deployment(), _run(), sweep_deployments(), _run()

### Community 171 - "get_meta"
Cohesion: 0.40
Nodes (5): get_meta(), DbSessionDep, get, Public metadata; identity fields appear only for valid credentials., OptionalUser

### Community 173 - "validate_endpoint_url"
Cohesion: 0.50
Nodes (3): model_validator, Validate/normalize an endpoint URL against the scheme allowlist., validate_endpoint_url()

### Community 175 - "4. DNS ownership verification"
Cohesion: 0.40
Nodes (5): 4.1 The token, 4.2 The check (control-plane side), 4.3 Anti-takeover rules, 4.4 Sequence: add-domain → verified, 4. DNS ownership verification

## Knowledge Gaps
- **409 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+404 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1737 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `6. Tooling: reproducible e2e` connect `org_scope` to `_is_same_origin`, `client.ts`, `core/tenancy.py`, `auth_service.py`, `ensure_dispatchable`?**
  _High betweenness centrality (0.248) - this node is a cross-community bridge._
- **Why does `useEventStream()` connect `client.ts` to `App.tsx`, `apiGet`, `useAuth`, `org_scope`, `types.ts`, `ServerDetailPage.tsx`, `DashboardPage.tsx`, `DeploymentDetailPage.tsx`?**
  _High betweenness centrality (0.247) - this node is a cross-community bridge._
- **Why does `TenancyScopeError` connect `core/tenancy.py` to `test_operations.py`, `org_scope`, `AuthContext`, `log_service.py`, `hub.py`, `test_tenant_isolation.py`?**
  _High betweenness centrality (0.118) - this node is a cross-community bridge._
- **Are the 83 inferred relationships involving `AuthContext` (e.g. with `TenancyScopeError` and `MembershipStatus`) actually correct?**
  _`AuthContext` has 83 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `APIModel` (e.g. with `OperationSpec` and `test_specs_reject_unknown_params()`) actually correct?**
  _`APIModel` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `apiGet()` (e.g. with `ContainerDetailPage.test.tsx` and `mockApi()`) actually correct?**
  _`apiGet()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `meta`, `SCHEMA`, `RESEARCH_COMMON` to the rest of the system?**
  _409 weakly-connected nodes found - possible documentation gaps or missing edges._