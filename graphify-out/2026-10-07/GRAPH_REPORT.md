# Graph Report - nexusops  (2026-10-04)

## Corpus Check
- 294 files · ~268,894 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: (none) 8, .example 1, .service 1)

## Summary
- 4188 nodes · 12407 edges · 181 communities (155 shown, 26 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1031 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7a92b064`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- AuthContext.tsx
- v1/auth.py
- DockerHostsPage.tsx
- apiPost
- user_service.py
- typing
- resolve_client_ip
- apiGet
- App.tsx
- test_operations.py
- project_service.py
- ServerDetailPage.tsx
- v1/health.py
- client.ts
- projects.py
- incidents.py
- deployment_engine.py
- SimulatedDockerProvider
- logging.py
- v1/deployments.py
- test_deployments_simulated.py
- list_containers
- metrics_service.py
- get_settings
- Domain Routing — NexusOps
- monitor_service.py
- Node & Agent Architecture
- test_agent_backoff.py
- server.py
- nexusops_agent.py
- integration/conftest.py
- auth_service.py
- docker_host_service.py
- AuthContext
- docker_hosts.py
- alerts.py
- monitors.py
- v1/search.py
- server_service.py
- list_deliveries
- DockerProvider
- test_monitor_transport.py
- test_agent_contract.py
- types.ts
- RealDockerProvider
- test_permissions.py
- RolesPage.tsx
- servers.py
- UnprocessableEntity
- secret_service.py
- role_service.py
- test_schemas_server.py
- api_key_service.py
- publish
- AgentContainerIn
- Session
- rotate_secret
- collections_abc
- notification_service.py
- test_auth_journey.py
- compilerOptions
- deployment.py
- middleware.py
- test_monitors_incidents.py
- SimulatedDeploymentRunner
- notification_sender.py
- monitor.py
- PageParams
- update_channel
- package.json
- events.py
- test_secrets.py
- README.md - NexusOps overview
- models/__init__.py
- api service (FastAPI / uvicorn :8000)
- env.py
- monitor_transport.py
- enums.py
- v1/channels.py
- ApiKeysPage.tsx
- test_event_registry.py
- Settings
- users.py
- containers.py
- Hub
- paginate
- devDependencies
- operation_service.py
- AppError
- register_exception_handlers
- _validate_resolution
- Deployment Architecture — NexusOps (target state)
- test_notifications.py
- main.py
- error_of
- AgentHelloIn
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- journey.spec.ts
- LogLine
- 2. Entities
- Secrets Architecture
- docker_real.py
- alert_service.py
- DockerProviderError
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- lax
- test_error_logging.py
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- FakeSocket
- get_sessionmaker
- test_app_gating.py
- core/tenancy.py
- scripts
- BadRequest
- ScopedSession
- system_scope
- dependencies
- DeploymentDetailPage.test.tsx
- generate_secrets.sh
- test_rate_limit.py
- test_tenant_isolation.py
- Product Roadmap — NexusOps Multi-Tenant Platform
- list_audit_logs
- .__init__
- APIModel
- .__tablename__
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
- get_redis
- postgres service (PostgreSQL 17, loopback :5433)
- test_rbac.py
- nexusops-understand.mjs
- Invisible account lockout (5 fails -> 15 min, enumeration resistance)
- deps.py
- instant_pacing
- nexusops-draft.mjs
- require_permission
- nexusops-challenge.mjs
- pytest
- parametrize
- get_latest_server_metrics
- AgentClient
- ContainerStats
- ContainerInfo
- ._shallow_validate
- scope_matches
- _FakeAsyncClient
- AgentHeartbeatIn
- Authorization Architecture
- sweep_deployments
- redis_down
- 8. Upstream binding and re-render triggers
- get_meta
- permissions.py
- validate_endpoint_url
- UUID
- 4. DNS ownership verification
- 6. Agent security
- ._redact
- _FakeSession
- 3. Entities (per domain-model.md §2.4)
- .__init__

## God Nodes (most connected - your core abstractions)
1. `AuthContext` - 140 edges
2. `APIModel` - 115 edges
3. `apiGet()` - 76 edges
4. `get_settings()` - 67 edges
5. `NotFound` - 64 edges
6. `record()` - 64 edges
7. `publish()` - 60 edges
8. `PageParams` - 55 edges
9. `apiPost()` - 55 edges
10. `ApiError` - 54 edges

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

## Communities (181 total, 26 thin omitted)

### Community 0 - "AuthContext.tsx"
Cohesion: 0.05
Nodes (33): Membership, User, LoginPage, AuthContext, AuthProvider(), AuthState, isOrgSelectionError(), MeResponse (+25 more)

### Community 1 - "v1/auth.py"
Cohesion: 0.06
Nodes (70): change_password(), _clear_refresh_cookie(), _cookies_secure(), login(), logout(), me(), _optional_actor(), AsyncSession (+62 more)

### Community 2 - "DockerHostsPage.tsx"
Cohesion: 0.06
Nodes (51): AuditEntry, Page, AuditLogPage, ContainerListPage, DockerHostsPage, EventsPage, IncidentListPage, SecretsPage (+43 more)

### Community 3 - "apiPost"
Cohesion: 0.07
Nodes (53): apiDelete(), apiPatch(), apiPost(), DeliveryOut, MonitorOut, AlertsPage, MonitorDetailPage, MonitorListPage (+45 more)

### Community 4 - "user_service.py"
Cohesion: 0.10
Nodes (33): MembershipStatus, UserStatus, User, Membership, Binds a user to an organization with a role *inside that organization*.…, User request/response schemas., _apply_deactivation(), _assert_not_last_active_superadmin() (+25 more)

### Community 5 - "typing"
Cohesion: 0.06
Nodes (45): AsyncEngine, agent_heartbeat(), agent_hello(), claim_operation(), _presented_token(), DbDep, post, Request (+37 more)

### Community 6 - "resolve_client_ip"
Cohesion: 0.20
Nodes (19): _parse_networks(), Request, Parse a comma-separated CIDR list; malformed entries are skipped., Real client address for *request* per the trust model above., resolve_client_ip(), make_request(), Request, Unit tests for the chained-proxy client-IP resolver (app/core/client_ip.py). (+11 more)

### Community 7 - "apiGet"
Cohesion: 0.06
Nodes (35): apiGet(), DeploymentOut, DeploymentStepOut, EnvironmentOut, ProjectOut, DeploymentDetailPage, DeploymentListPage, MetaInfo (+27 more)

### Community 8 - "App.tsx"
Cohesion: 0.04
Nodes (62): DashboardSummary, SearchResult, App(), DashboardPage, LoginRoute(), OrganizationRequiredPage, ProjectDetailPage, ProjectListPage (+54 more)

### Community 9 - "test_operations.py"
Cohesion: 0.09
Nodes (43): expire_operations(), Expire node operations past their deadline — pending and claimed alike. A…, assert_error_code(), Assert envelope shape + code; returns the inner error object., _dispatch(), _dispatch_body(), _enrolled_node(), _mutate_in_system_scope() (+35 more)

### Community 10 - "project_service.py"
Cohesion: 0.16
Nodes (41): NotFound, Application, DeploymentEnvironment, EnvironmentCreate, Payload to create an environment under an application., actor_of(), _apply_update(), _check_server() (+33 more)

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
Cohesion: 0.10
Nodes (51): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+43 more)

### Community 15 - "incidents.py"
Cohesion: 0.15
Nodes (30): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+22 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.11
Nodes (54): deployment_log_channel(), Deployment, DeploymentStep, DeploymentStatus, StepStatus, _after_commit_enqueue(), _after_rollback_drop(), _audit_resolution_failed() (+46 more)

### Community 17 - "SimulatedDockerProvider"
Cohesion: 0.13
Nodes (25): Implements :class:`DockerProvider` semantics against DB rows., Make a container row visible to this provider instance., Attach already-fetched log rows so ``logs()`` can replay them., SimulatedDockerProvider, _log_entry(), datetime, Unit tests for the simulated docker provider (in-memory rows, no docker)., _row() (+17 more)

### Community 18 - "logging.py"
Cohesion: 0.05
Nodes (76): configure_logging(), get_logger(), _orjson_dumps(), Any, Structured logging via structlog. Every log record carries timestamp, level,…, Configure structlog + stdlib logging once at process start. Everything…, Celery application: periodic cadences live here, dynamic work is claimed…, Deployment execution task + stuck-deployment sweeper. (+68 more)

### Community 19 - "v1/deployments.py"
Cohesion: 0.15
Nodes (26): _attribute_step_idx(), _emails_for(), get_deployment(), list_application_deployments(), list_deployment_logs(), _list_deployments(), _parse_sort(), _parse_statuses() (+18 more)

### Community 20 - "test_deployments_simulated.py"
Cohesion: 0.15
Nodes (27): execute_deployment(), Run one deployment to a terminal state. Never raises; safe to re-run., _as_worker(), _delivery_chain(), _owner_ctx(), _queue(), _queued_with_recorder(), Deployment engine over the simulated runner: success, failure, rollback. (+19 more)

### Community 21 - "list_containers"
Cohesion: 0.09
Nodes (37): _endpoint(), get_container(), _like_pattern(), list_container_logs(), list_containers(), _load_container(), _max_log_id(), _perform_action() (+29 more)

### Community 22 - "metrics_service.py"
Cohesion: 0.12
Nodes (30): MetricGranularity, aggregate_rollups(), dashboard_summary(), ensure_server(), _extra_object(), granularity_for_range(), latest_for_servers(), _prune() (+22 more)

### Community 23 - "get_settings"
Cohesion: 0.06
Nodes (71): argon2, argon2_exceptions, _is_trusted(), Client-IP resolution behind chained reverse proxies. The API never takes TCP…, fail_on_bad_config(), get_settings(), Central configuration. All runtime configuration flows through this module so…, Return the cached settings singleton. (+63 more)

### Community 24 - "Domain Routing — NexusOps"
Cohesion: 0.13
Nodes (15): 10. Wildcards and catch-all, 11. User journey, 12. API surface, permissions, audit, 13. Monitoring tie-in, 1. Scope and current state, 2. Where nginx runs, 5. ProxyProvider interface, 6.1 What is rendered (+7 more)

### Community 25 - "monitor_service.py"
Cohesion: 0.15
Nodes (35): MonitorStatus, MonitorCheck, _active_incident(), _audit(), claim_due_monitors(), create_monitor(), delete_monitor(), _emit() (+27 more)

### Community 26 - "Node & Agent Architecture"
Cohesion: 0.11
Nodes (19): 1. Scope and stance, 3.1 Current state (real), 3.2 Enrollment v2, 3.3 Token storage & rotation with dual-token grace, 3.4 Revocation semantics — fixing the 401 hot-loop, 3.5 Reconnect / offline states, 3. Agent lifecycle, 5.1 Model and lifecycle (+11 more)

### Community 27 - "test_agent_backoff.py"
Cohesion: 0.07
Nodes (42): AST, configure_test_env(), Test bootstrap: pin every cached setting BEFORE the first ``app`` import. The…, KEY=VALUE pairs from the repo .env (first definition wins); never logged., Export the exact settings the app caches; host values cannot leak through., _read_dot_env(), agent_fixture(), _install_sleep() (+34 more)

### Community 28 - "server.py"
Cohesion: 0.25
Nodes (7): _clean_tag_names(), DockerHostSummary, Server API schemas: create/update payloads, list/detail outputs, enrollment., Strip, drop empties and de-duplicate tag names case-insensitively., ServerCounts, Minimal tag reference embedded in server payloads., TagRef

### Community 29 - "nexusops_agent.py"
Cohesion: 0.09
Nodes (30): build_heartbeat(), collect_container_stats(), collect_containers(), cpu_percent_since(), disk_stats(), _docker_request(), _interruptible_sleep(), load1() (+22 more)

### Community 30 - "integration/conftest.py"
Cohesion: 0.15
Nodes (19): alembic_config, client(), _ensure_database(), _migrated_database(), org_db(), owner(), AsyncClient, fixture (+11 more)

### Community 31 - "auth_service.py"
Cohesion: 0.10
Nodes (47): active_memberships(), The user's memberships in non-suspended organizations, oldest first. Reads only…, System scope bound to *db*, for rows that have no organization. Used by exactly…, system_write_scope(), _audit(), _bootstrap_organization(), change_own_password(), count_users() (+39 more)

### Community 32 - "docker_host_service.py"
Cohesion: 0.07
Nodes (64): ContainerStatus, DockerHostStatus, Container, DockerHost, Observed container state mirrored from an agent or docker provider., describe_provider_error(), is_simulated(), provider_for() (+56 more)

### Community 33 - "AuthContext"
Cohesion: 0.09
Nodes (29): AuthContext, Resolved identity plus the organization this request acts in.…, The active organization, or raise if this request has none., Request, Revoke a key owned by *owner_id*. Foreign keys look like NotFound (no leak)., revoke_api_key(), Any, AsyncSession (+21 more)

### Community 34 - "docker_hosts.py"
Cohesion: 0.09
Nodes (48): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+40 more)

### Community 35 - "alerts.py"
Cohesion: 0.22
Nodes (15): list_alerts(), mark_all_read(), mark_read(), CurrentUser, DbDep, Depends, get, post (+7 more)

### Community 36 - "monitors.py"
Cohesion: 0.16
Nodes (34): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+26 more)

### Community 37 - "v1/search.py"
Cohesion: 0.11
Nodes (34): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+26 more)

### Community 38 - "server_service.py"
Cohesion: 0.06
Nodes (67): Canonical Redis pub/sub channel names shared by API, workers and WS hub., server_metrics_channel(), ActorType, ServerStatus, Server, AgentHelloOut, Tells the agent how often to report., _actor_kwargs() (+59 more)

### Community 39 - "list_deliveries"
Cohesion: 0.19
Nodes (21): create_channel(), delete_channel(), get_channel(), list_channels(), list_deliveries(), DbDep, delete, Depends (+13 more)

### Community 40 - "DockerProvider"
Cohesion: 0.11
Nodes (9): DockerProvider, Any, Protocol, List containers visible to the provider., List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``., List volumes: keys ``name``, ``driver``, ``mountpoint``., List networks: keys ``name``, ``driver``, ``scope``., Structural interface implemented by real and simulated providers. (+1 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.13
Nodes (34): CheckResult, HTTPMonitorTransport, Deterministic fake checker for ``sim://`` monitors and demo environments.…, Real HTTP(S) probe using httpx with per-monitor settings. Redirects are…, SimulatedTransport, _check(), clock(), FakeClock (+26 more)

### Community 42 - "test_agent_contract.py"
Cohesion: 0.18
Nodes (16): agent_fixture(), _load_agent(), _patch_stats(), Any, fixture, MonkeyPatch, Contract tests: the shipped agent's payloads must satisfy the ingest schemas.…, One-shot docker stats reduce to cpu/mem/limit fields the schema accepts, with… (+8 more)

### Community 43 - "types.ts"
Cohesion: 0.02
Nodes (102): ApiError, AlertOut, ApplicationOut, ChannelOut, CheckOut, ContainerOut, CursorPage, DeploymentLogLine (+94 more)

### Community 44 - "RealDockerProvider"
Cohesion: 0.19
Nodes (5): T, Execute an SDK call with one short retry, normalizing failures., Two short samples give real cpu/net deltas without streaming., Talks to a real docker daemon over ``unix://`` or ``tcp://``., RealDockerProvider

### Community 45 - "test_permissions.py"
Cohesion: 0.16
Nodes (11): permission_exists(), _auth_context(), Unit tests for the permission registry, scope matching and RBAC gate., A fake context in the given organization. ``membership_status=None`` models a…, test_api_key_scope_intersects_role_permissions(), test_membership_is_required_for_authority(), test_permission_exists_helper(), test_plain_user_without_permissions_is_denied() (+3 more)

### Community 46 - "RolesPage.tsx"
Cohesion: 0.11
Nodes (15): Role, RolesPage, describeError(), GROUP_STYLE, LEGEND_STYLE, OPTION_STYLE, PermissionSpec, roleAllows() (+7 more)

### Community 47 - "servers.py"
Cohesion: 0.08
Nodes (41): create_server(), delete_server(), _detail(), get_server(), list_servers(), list_tags(), AsyncSession, DbDep (+33 more)

### Community 48 - "UnprocessableEntity"
Cohesion: 0.18
Nodes (21): UnprocessableEntity, assert_safe_url(), _raise_block(), Validate *url* for outbound requests; return the parsed URL or raise 422.…, Reject non-empty values that are not valid IPv4/IPv6 addresses., _validate_ip(), install_dns(), Exception (+13 more)

### Community 49 - "secret_service.py"
Cohesion: 0.17
Nodes (24): _actor_type(), _collect_refs(), create_secret(), delete_secret(), _detail(), get_secret(), get_secret_detail(), list_secrets() (+16 more)

### Community 50 - "role_service.py"
Cohesion: 0.07
Nodes (47): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, delete, get (+39 more)

### Community 51 - "test_schemas_server.py"
Cohesion: 0.21
Nodes (22): Payload for registering a server., Partial update. ``tags`` replaces the full set when provided., ServerCreate, ServerUpdate, _base(), parametrize, Unit tests for app.schemas.server (validation only, no I/O)., test_empty_ip_is_allowed_but_whitespace_collapses() (+14 more)

### Community 52 - "api_key_service.py"
Cohesion: 0.10
Nodes (31): create_api_key(), list_api_keys(), CurrentUser, DbSessionDep, delete, get, post, Request (+23 more)

### Community 53 - "publish"
Cohesion: 0.29
Nodes (11): _after_commit_publish(), _after_rollback_drop(), publish(), _publish_after_commit(), _publish_redis(), Any, AsyncSession, UUID (+3 more)

### Community 54 - "AgentContainerIn"
Cohesion: 0.29
Nodes (13): AgentContainerIn, field_validator, Observed container state reported by an agent., _container(), parametrize, Unit tests for agent-facing schemas (heartbeat + container payloads)., test_allowed_container_statuses(), test_bogus_status_string_rejected() (+5 more)

### Community 55 - "Session"
Cohesion: 0.22
Nodes (11): _apply_scope_guc(), _desired_guc(), install_tenancy_guards(), Any, The ``app.current_org`` value implied by the current scopes., ``before_flush`` handler: own new rows, and refuse rows that change hands.…, ``after_begin`` handler: (re)issue the RLS GUC for this transaction., Attach the guard and the GUC writer to the ORM session class. Idempotent, and… (+3 more)

### Community 56 - "rotate_secret"
Cohesion: 0.16
Nodes (21): create_secret(), delete_secret(), get_secret(), list_secrets(), DbSession, delete, Depends, get (+13 more)

### Community 57 - "collections_abc"
Cohesion: 0.09
Nodes (10): alembic, downgrade(), rename ``server.*`` permission codenames to ``node.*`` The Node/Server…, _rename_permissions(), upgrade(), _quoted_list(), Add the operations framework table (node-agent-architecture.md §5). One tenant-…, upgrade() (+2 more)

### Community 58 - "notification_service.py"
Cohesion: 0.14
Nodes (27): _as_uuid(), _attempt_delivery(), decode_delivery_cursor(), decrypt_channel_config(), dispatch_event_frame(), _send(), dispatcher_loop(), encode_delivery_cursor() (+19 more)

### Community 59 - "test_auth_journey.py"
Cohesion: 0.09
Nodes (41): bearer(), cookie_attributes(), login_account(), login_headers(), Any, AsyncClient, Response, Pure helpers for journey tests: payloads, auth shortcuts, cookie parsing. (+33 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "deployment.py"
Cohesion: 0.09
Nodes (28): cancel_deployment(), post, Request, Queue a new deployment for an application/environment pair., Cancel a QUEUED deployment immediately or flag a RUNNING one., Queue a rollback to the last good version of this app/environment., rollback_deployment(), trigger_deployment() (+20 more)

### Community 62 - "middleware.py"
Cohesion: 0.15
Nodes (14): AccessLogMiddleware, Request, Response, HTTP middleware: request ids, security headers, structured access logs., Baseline hardening headers on every API response., RequestIDMiddleware, SecurityHeadersMiddleware, BaseHTTPMiddleware (+6 more)

### Community 63 - "test_monitors_incidents.py"
Cohesion: 0.27
Nodes (9): _create_monitor(), Monitor checks driving the full down -> incident -> recovery lifecycle., Regression: probe headers and URL query credentials never leave the API. Probe…, A monitor's checks, incidents and timeline all live in its organization, so the…, test_check_now_endpoint_runs_immediately(), test_down_then_recover_lifecycle(), test_metadata_endpoint_and_private_target_blocked(), test_monitor_responses_mask_probe_credentials() (+1 more)

### Community 64 - "SimulatedDeploymentRunner"
Cohesion: 0.12
Nodes (38): LogLevel, _commit_short(), _pace(), Exception, Deployment runner port plus a faithful simulated implementation.…, Stream output lines for *step_name*; raise StepFailure to fail it., Staged docker-style simulation used by v1 deployments., Deterministic per-line delay between 0.05s and 0.35s. (+30 more)

### Community 65 - "notification_sender.py"
Cohesion: 0.16
Nodes (17): NotificationError, Any, BaseException, Exception, Low-level notification transports: SMTP email and outgoing webhooks. These…, POST *payload* as JSON to *url*; 2xx is success, anything else raises. Response…, Raised when a delivery attempt fails. Message is safe to persist., Bounded, single-line, content-free error reason. (+9 more)

### Community 66 - "monitor.py"
Cohesion: 0.09
Nodes (27): is_sensitive_header(), mask_sensitive_headers(), MonitorBase, MonitorCreate, MonitorSortField, MonitorUpdate, field_serializer, Schemas for uptime monitors and their check history. (+19 more)

### Community 67 - "PageParams"
Cohesion: 0.15
Nodes (26): Cursor, cursor_params(), CursorParams, decode_cursor(), encode_cursor(), page_params(), PageParams, datetime (+18 more)

### Community 68 - "update_channel"
Cohesion: 0.25
Nodes (15): EmailConfig, WebhookConfig, _audit(), create_channel(), delete_channel(), encrypt_config(), _normalize_events(), AsyncSession (+7 more)

### Community 69 - "package.json"
Cohesion: 0.13
Nodes (15): name, private, type, version, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom (+7 more)

### Community 70 - "events.py"
Cohesion: 0.16
Nodes (20): _decode_cursor(), _encode_cursor(), list_event_types(), list_events(), datetime, DbSession, Depends, get (+12 more)

### Community 71 - "test_secrets.py"
Cohesion: 0.09
Nodes (29): Exception, A ``${secret:KEY}`` reference could not be resolved. Fail-closed. Carries…, One successfully resolved reference: metadata for audit, no value., Outcome of resolving an environment's config references., Resolve every ``${secret:KEY}`` reference in an environment's config. INTERNAL…, resolve_secrets_for_environment(), ResolvedSecrets, SecretReference (+21 more)

### Community 72 - "README.md - NexusOps overview"
Cohesion: 0.06
Nodes (58): _app_role_credentials(), _assert_fully_backfilled(), _backfill_org_ids(), _drop_constraint(), add tenancy foundation Phase 1 of the platform roadmap: organizations,…, Carry a value into a PL/pgSQL block. ``CREATE ROLE``/``ALTER ROLE`` are utility…, Application role name/password from settings (never hard-coded)., Point every pre-existing row at the bootstrap organization. ``audit_logs`` is… (+50 more)

### Community 73 - "models/__init__.py"
Cohesion: 0.08
Nodes (72): Base, big_serial_pk(), json_column(), org_id_column(), OrgScoped, datetime, UUID, Declarative base, shared mixins and column helpers. (+64 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "env.py"
Cohesion: 0.24
Nodes (10): _database_url(), Alembic environment: metadata comes from app.models, URL from app settings., Migrations run as the table **owner**, never as the application role. The owner…, Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online(), Owner-role DSN for Alembic and the container entrypoint. Migrations… (+2 more)

### Community 76 - "monitor_transport.py"
Cohesion: 0.09
Nodes (24): assert_safe_url_async(), Async wrapper around :func:`assert_safe_url`; DNS runs off the loop., CheckOutcome, coerce_headers(), _decode(), get_transport(), MonitorTransport, Any (+16 more)

### Community 77 - "enums.py"
Cohesion: 0.13
Nodes (36): Conflict, AuditResult, ContainerHealth, CredentialKind, EventLevel, IncidentEventKind, IncidentSeverity, IncidentStatus (+28 more)

### Community 78 - "v1/channels.py"
Cohesion: 0.19
Nodes (15): Notification channel endpoints. Config is write-only; never echoed back., # NOTE: /deliveries is declared before /{channel_id} so the literal wins., ChannelType, DeliveryStatus, ChannelBase, ChannelCreate, ChannelOut, ChannelUpdate (+7 more)

### Community 79 - "ApiKeysPage.tsx"
Cohesion: 0.09
Nodes (20): ApiKeyOut, ApiKeysPage, ApiKeyCreatedOut, ApiKeysPage(), handleCopyKey(), copyText(), describeError(), EMPTY_FORM (+12 more)

### Community 80 - "test_event_registry.py"
Cohesion: 0.21
Nodes (8): event_type_catalogue(), is_known_event_type(), Canonical registry of system-event types. Single source of truth shared by…, Return True when *event_type* is part of the canonical registry., Serialise the registry for the ``/events/types`` endpoint., Registry coherence: schema-advertised event types must equal the canonical…, test_catalogue_serialises_every_entry(), test_known_event_lookup()

### Community 81 - "Settings"
Cohesion: 0.14
Nodes (6): field_validator, model_validator, Username from :attr:`database_url`, or ``None`` if it is unparseable., Validated application settings (loaded from environment / .env)., Settings, BaseSettings

### Community 82 - "users.py"
Cohesion: 0.15
Nodes (23): create_user(), deactivate_user(), get_user(), list_users(), CurrentUser, DbSessionDep, delete, get (+15 more)

### Community 83 - "containers.py"
Cohesion: 0.13
Nodes (25): _action_route(), _container_out(), _decode_frame(), _ev(), Any, Container API: listing/detail, lifecycle actions, removal, logs, streaming.…, Serialize one row; env values never leave the database (keys only)., Parse a Redis pub/sub frame ``{ts, stream, message}`` into a LogLine. (+17 more)

### Community 84 - "Hub"
Cohesion: 0.15
Nodes (15): _close_socket(), Connection, Hub, _is_same_origin(), _params_key(), WebSocket, Browsers always send Origin on WS handshakes, even same-origin ones. When it…, Connection registry, Redis fan-in listener and per-socket pumps. (+7 more)

### Community 85 - "paginate"
Cohesion: 0.11
Nodes (19): list_sessions(), CurrentUser, DbSessionDep, delete, get, Request, UUID, Active sessions of this organization's members. Defaults to the caller's own;… (+11 more)

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "operation_service.py"
Cohesion: 0.06
Nodes (68): cancel_operation(), create_operation(), get_operation(), list_operations(), DbDep, Depends, get, post (+60 more)

### Community 88 - "AppError"
Cohesion: 0.20
Nodes (16): AppError, Exception, Base class for expected, client-facing errors., _authenticate_api_key(), _authenticate_jwt(), _bind_organization(), _load_permissions(), _org_id_from_frame() (+8 more)

### Community 89 - "register_exception_handlers"
Cohesion: 0.36
Nodes (8): _error_payload(), FastAPI, Request, register_exception_handlers(), handle_app_error(), handle_http_exception(), handle_unexpected(), handle_validation_error()

### Community 90 - "_validate_resolution"
Cohesion: 0.24
Nodes (9): _is_forbidden_address(), True when *addr* points into a network the server must never contact.…, Resolve *hostname* (AF_UNSPEC) and refuse any non-public answer., _validate_resolution(), test_private_and_special_addresses_are_forbidden(), test_public_addresses_are_allowed(), test_validate_resolution_passes_hostname_through(), IPv4Address (+1 more)

### Community 91 - "Deployment Architecture — NexusOps (target state)"
Cohesion: 0.09
Nodes (22): DeploymentRunner, Protocol, Adapter interface implemented by real (future) and simulated runners., Return the ordered step names for this run., 10. Events and WS during runs, 11. Post-deploy hooks, 12. Rollback semantics (existing behavior kept), 13. The simulated runner stays — labeled (+14 more)

### Community 92 - "test_notifications.py"
Cohesion: 0.36
Nodes (9): NotificationDelivery, _channel(), _delivery(), UUID, Notification channel + delivery-log endpoints. Regression coverage for GET…, The same event frame consumed twice queues ONE delivery per channel. Every API…, test_dispatch_frame_is_idempotent_across_workers(), test_list_deliveries_filters_by_channel() (+1 more)

### Community 93 - "main.py"
Cohesion: 0.21
Nodes (13): dispose_engine(), close_redis(), create_app(), _include_routers(), lifespan(), FastAPI, NexusOps API entrypoint. Wires middleware, error handling, REST routers and the…, Mount every domain router. Router variables follow the module contract. (+5 more)

### Community 94 - "error_of"
Cohesion: 0.14
Nodes (14): error_of(), Unwrap an API error envelope., _invite(), Removing someone from A must not reach their account or their other tenant. The…, ``sessions`` has no tenant column: the owning membership is the boundary.…, Knowing an id is not authority — not even for an instance operator. The caller…, The write side of the boundary: every mutating route misses for a foreign…, Invite a fresh account into the caller's organization and log it in. (+6 more)

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
Nodes (11): EDGE, MAILPIT, ADMIN, Bootstrap, bootstrapVia(), test, ADMIN, formLogin() (+3 more)

### Community 99 - "LogLine"
Cohesion: 0.15
Nodes (12): clip(), LogLine, datetime, Provider abstraction for docker hosts (real daemon or simulated). Providers are…, Yield parsed log lines. With ``follow=True`` the stream never ends., Truncate *text* to *limit* characters, stripping control chars., One parsed log record from a container log stream., Provider selection based on a docker host's endpoint URL. Mapping: *… (+4 more)

### Community 100 - "2. Entities"
Cohesion: 0.15
Nodes (13): 0. Design stance, 1. The hierarchy, 2.1.1 ApiKey org binding detail, 2.2.1 Environment promotion detail, 2.2 Delivery (existing models, extended), 2.3 Infrastructure — Nodes, 2.4 Routing & TLS (new subsystem), 2.5 Secrets (existing, re-scoped) (+5 more)

### Community 101 - "Secrets Architecture"
Cohesion: 0.09
Nodes (23): EnvironmentBase, EnvironmentUpdate, field_validator, Shared environment fields., Partial environment update; omitted fields are left untouched., 10. Resolution flow at deploy time, 1.1 Storage and crypto, 1.2 Data model (+15 more)

### Community 102 - "docker_real.py"
Cohesion: 0.21
Nodes (16): _as_float(), _compute_stats(), _cpu_percent(), _network_bytes(), parse_rfc3339(), Any, datetime, Real docker provider backed by the docker SDK against a live daemon. Every SDK… (+8 more)

### Community 103 - "alert_service.py"
Cohesion: 0.23
Nodes (15): AlertSeverity, Alert, create_alert(), get_alert(), mark_all_read(), mark_read(), AsyncSession, UUID (+7 more)

### Community 104 - "DockerProviderError"
Cohesion: 0.15
Nodes (8): DockerProviderError, Exception, A provider operation failed. ``str()`` is safe to show/log., Build a compact, secret-free description of a provider failure. Only the…, sanitize_error(), parse_log_line(), Split one raw log record into a :class:`LogLine`., _iterate()

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

### Community 111 - "get_sessionmaker"
Cohesion: 0.08
Nodes (48): async_sessionmaker, get_sessionmaker(), AsyncSession, Forbidden, apply_scope_to_session(), org_scope(), Run the enclosed block as a single organization. Nesting the *same* org is a…, Push the current scope onto *db*'s connection immediately. Needed only when a… (+40 more)

### Community 112 - "test_app_gating.py"
Cohesion: 0.44
Nodes (8): _app_for_environment(), MonkeyPatch, ENVIRONMENT gating contract: docs exposure and HSTS (see .env.example).…, create_app() with get_settings() patched to the given environment., test_non_production_does_not_emit_hsts(), test_non_production_keeps_docs_and_schema(), test_production_emits_hsts(), test_production_hides_docs_and_schema()

### Community 113 - "core/tenancy.py"
Cohesion: 0.05
Nodes (58): asyncio, container_log_channel(), current_org(), current_scope(), _guard(), _has_org_predicate(), _mappers_of(), _org_scoped_classes() (+50 more)

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "BadRequest"
Cohesion: 0.24
Nodes (14): BadRequest, assert_safe_tcp_endpoint(), SSRF guard applied to every operator-supplied outbound URL. Monitors and…, Validate a ``tcp://`` docker host endpoint for outbound connection. Docker…, Unit tests for the SSRF guard — fully offline via injected DNS answers., test_tcp_endpoint_lax_mode_skips_resolution(), test_tcp_endpoint_rejects_embedded_credentials(), test_tcp_endpoint_rejects_non_tcp_schemes() (+6 more)

### Community 117 - "system_scope"
Cohesion: 0.05
Nodes (37): Whether the runtime connection is the RLS-enforced application role. False…, Run the enclosed block with tenant filtering off (maintenance only). ``reason``…, system_scope(), Insert permissions + system roles exactly like scripts/seed.py does., _seed_rbac_registry(), Loader criteria do not apply to DML — so the guard refuses instead. A silent…, test_bulk_dml_and_core_statements_are_refused_under_org_scope(), 10. Migration (Phase 1) (+29 more)

### Community 118 - "dependencies"
Cohesion: 0.33
Nodes (6): dependencies, lucide-react, react, react-dom, react-router-dom, @tanstack/react-query

### Community 119 - "DeploymentDetailPage.test.tsx"
Cohesion: 0.13
Nodes (9): ACTIVE_MEMBERSHIP, ApiError, deploymentDetail(), EMPTY_LOGS, FakeWebSocket, get, ME, post (+1 more)

### Community 120 - "generate_secrets.sh"
Cohesion: 0.47
Nodes (3): existing_real_keys(), replace_or_append(), generate_secrets.sh script

### Community 121 - "test_rate_limit.py"
Cohesion: 0.26
Nodes (13): RateLimited, _memory_count_and_ttl(), Request, rate_limit(), _dependency(), Fixed-window counter backed by process memory. Returns (count, ttl)., Return a dependency enforcing *limit* requests per window per IP. With…, _FakeRequest (+5 more)

### Community 122 - "test_tenant_isolation.py"
Cohesion: 0.06
Nodes (46): A valid POST /servers body with per-test overrides., server_payload(), _create_server(), Server CRUD, cascade delete, audit trail rows and audit immutability., The HTTP listing path — schema serialization is exercised end-to-end. A…, ``/servers`` is a temporary alias for pre-rename clients. It must keep working…, test_agent_token_rotation_invalidates_previous(), test_audit_log_api_serializes_and_filters() (+38 more)

### Community 123 - "Product Roadmap — NexusOps Multi-Tenant Platform"
Cohesion: 0.13
Nodes (15): 0. Stance, 10. Phase 7 — Teams, grants & custom roles, 11. Phase 8 — Backups, 12. Phase 9 — Billing & metering, 14. Biggest risks (short form), 15. Reading order, 2. Phase plan, 4. Phase 1 — Tenancy foundation (+7 more)

### Community 124 - "list_audit_logs"
Cohesion: 0.29
Nodes (7): list_audit_logs(), datetime, DbSession, Depends, get, PageParamsDep, Newest-first audit trail with optional filters. No write routes exist for this…

### Community 126 - "APIModel"
Cohesion: 0.05
Nodes (65): Record the agent's outcome for an operation it claimed. The report is…, report_operation_result(), OperationType, The whitelist. Nothing outside this enum ships as an exec surface. Each type…, AlertOut, Schemas for operator-facing alerts., ApiKeyCreateRequest, API key schemas. Raw keys appear exactly once, at creation. (+57 more)

### Community 137 - "test_ws_hub.py"
Cohesion: 0.19
Nodes (22): _connection(), _drain(), _event_frame(), _fake_sessionmaker(), hub(), _Org, Any, fixture (+14 more)

### Community 146 - "Any"
Cohesion: 0.19
Nodes (10): _entity_exists(), _frame_org(), _parse_payload(), Any, Whether *id_* exists **for this organization**. Runs inside the socket's…, Spawn the Redis fan-in listener (idempotent)., Deliver one Redis message to every matching subscription., The organization an event frame belongs to, or ``None`` when it has none. (+2 more)

### Community 147 - "get_redis"
Cohesion: 0.26
Nodes (11): get_redis(), ping(), Shared async Redis client., _next_data_message(), Event bus fan-out ordering: a frame follows its transaction, never leads it.…, Regression: a rollback must drop stashed frames, not defer them. The stash…, test_frame_published_only_after_commit(), test_rolled_back_event_never_publishes() (+3 more)

### Community 148 - "postgres service (PostgreSQL 17, loopback :5433)"
Cohesion: 0.29
Nodes (7): postgres service (PostgreSQL 17, loopback :5433), Fernet encryption at rest (ENCRYPTION_KEY, write-once), Backups (pgdata volume, nightly pg_dump, ephemeral Redis), Required secrets (POSTGRES_PASSWORD, JWT_SECRET >= 32 chars, ENCRYPTION_KEY Fernet), Production hardening checklist (secrets, ENVIRONMENT, no seed, TLS, rotation), Compose vs host network namespaces (postgres:5432 vs 127.0.0.1:5433), Simulation mode (SIMULATION_MODE)

### Community 149 - "test_rbac.py"
Cohesion: 0.22
Nodes (12): A fresh, deliverable-shaped address unique to a single test. ``example.com`` is…, unique_email(), test_second_register_without_invite_is_rejected(), _invite_user(), _org_headers(), Role-based access control: least-privileged users are properly boxed in., Admin invites a user with *role_name*; returns their credentials dict., Headers for an invited user, scoped to the organization they joined. An account… (+4 more)

### Community 150 - "nexusops-understand.mjs"
Cohesion: 0.33
Nodes (5): COMMON, meta, out, READERS, SCHEMA

### Community 151 - "Invisible account lockout (5 fails -> 15 min, enumeration resistance)"
Cohesion: 0.33
Nodes (6): Invisible account lockout (5 fails -> 15 min, enumeration resistance), Unified error envelope (code, message, request_id), Per-IP rate limiting (Redis fixed window), Request lifecycle (edge -> middleware -> rate limit -> deps -> router), Client IP resolution (resolve_client_ip, TRUSTED_PROXY_CIDRS, XFF overwrite), EmailStr rejects reserved domains (login 422 on .test/.local/.arpa)

### Community 152 - "deps.py"
Cohesion: 0.12
Nodes (31): _attach_organization(), get_current_user(), get_identity(), get_optional_user(), _load_organization(), _load_permissions(), membership_for_org(), _org_id_from_header() (+23 more)

### Community 153 - "instant_pacing"
Cohesion: 0.40
Nodes (4): instant_pacing(), fixture, MonkeyPatch, Remove the per-line sleeps; pacing bounds are asserted separately.

### Community 154 - "nexusops-draft.mjs"
Cohesion: 0.40
Nodes (4): DOCS, meta, SPINE, VERIFY_RULES

### Community 155 - "require_permission"
Cohesion: 0.18
Nodes (10): permission_dep(), Any, Dependency factory enforcing a permission; returns 403 when denied., require_permission(), _check(), _FakeCtx, Duck-typed stand-in for AuthContext., test_require_permission_raises_forbidden_when_denied() (+2 more)

### Community 156 - "nexusops-challenge.mjs"
Cohesion: 0.33
Nodes (5): CHALLENGE_COMMON, meta, RESEARCH_COMMON, SCHEMA, TASKS

### Community 157 - "pytest"
Cohesion: 0.18
Nodes (14): _enrolled(), _heartbeat(), Agent ingest pipeline: hello, heartbeat, staleness transitions, events., A container absent from a later heartbeat is gone from the daemon., A payload at the agent's cap may be truncated — absence proves nothing., test_heartbeat_at_container_cap_skips_reconciliation(), test_heartbeat_removes_vanished_containers(), test_heartbeat_updates_status_metrics_and_containers() (+6 more)

### Community 158 - "parametrize"
Cohesion: 0.21
Nodes (12): is_simulation_url(), True when *url* targets the built-in simulated checker (``sim://``)., Internal signal: a specific SSRF rule matched (never shown to clients)., UrlRejected, _validate_syntax(), parametrize, test_non_simulation_urls(), test_simulation_url_detection() (+4 more)

### Community 159 - "get_latest_server_metrics"
Cohesion: 0.25
Nodes (11): get_dashboard_summary(), get_latest_server_metrics(), get_server_metrics(), CurrentUser, DbDep, Depends, get, UUID (+3 more)

### Community 161 - "ContainerStats"
Cohesion: 0.22
Nodes (6): ContainerStats, Point-in-time resource usage snapshot., Any, Plausible numbers derived from the row plus time-based sine noise., _seed_int(), test_seed_int_is_deterministic_and_spread()

### Community 162 - "ContainerInfo"
Cohesion: 0.29
Nodes (3): ContainerInfo, Inspect a single container by id (short ids allowed)., Normalized view of a container as reported by any provider.

### Community 164 - "scope_matches"
Cohesion: 0.22
Nodes (8): Check an API-key scope list against a required permission. Supports exact match…, scope_matches(), parametrize, test_scope_matches_truth_table(), 5. API keys, 2.1 Identity & tenancy (new), 4.1 Audit event at resolution time, 4. Resolution authorization

### Community 165 - "_FakeAsyncClient"
Cohesion: 0.22
Nodes (3): _FakeAsyncClient, _FakeRequestObj, Scripted httpx.AsyncClient: responses keyed by absolute request URL.

### Community 166 - "AgentHeartbeatIn"
Cohesion: 0.39
Nodes (8): AgentHeartbeatIn, Periodic metrics + observed containers from an enrolled agent., _heartbeat(), test_minimal_heartbeat_accepted(), test_missing_required_metric_rejected(), test_more_than_200_containers_rejected(), test_out_of_range_metrics_rejected(), test_upper_bounds_are_inclusive()

### Community 167 - "Authorization Architecture"
Cohesion: 0.25
Nodes (8): 0. What shipped (Phase 1), 2. Registry changes (Phase 1 + new subsystems), 3. The five system roles (target), 4. Grants (resource-level access; design now, later phase), 6. Enforcement mechanics (unchanged patterns, one addition), 7. Custom roles (later phase), 8. Permission-change audit, Authorization Architecture

### Community 168 - "sweep_deployments"
Cohesion: 0.33
Nodes (6): task, Execute one queued deployment. The engine owns all state transitions., Re-enqueue deployments the broker lost; fail ones whose worker died.…, run_deployment(), _run(), sweep_deployments()

### Community 169 - "redis_down"
Cohesion: 0.33
Nodes (5): _clean_memory_windows(), fixture, MonkeyPatch, redis_down(), test_memory_counter_resets_per_window()

### Community 170 - "8. Upstream binding and re-render triggers"
Cohesion: 0.33
Nodes (6): 8.1 Binding rules, 8.2 Certificate selection rule (this doc owns it), 8.3 Re-render triggers, 8.4 Drift, 8.5 How deployments hook routing (post-deploy route sync), 8. Upstream binding and re-render triggers

### Community 171 - "get_meta"
Cohesion: 0.40
Nodes (5): get_meta(), DbSessionDep, get, Public metadata; identity fields appear only for valid credentials., OptionalUser

### Community 172 - "permissions.py"
Cohesion: 0.40
Nodes (3): PermissionSpec, Permission registry and role matrix. Permissions are *data*: the registry below…, fnmatch

### Community 173 - "validate_endpoint_url"
Cohesion: 0.50
Nodes (3): model_validator, Validate/normalize an endpoint URL against the scheme allowlist., validate_endpoint_url()

### Community 175 - "4. DNS ownership verification"
Cohesion: 0.40
Nodes (5): 4.1 The token, 4.2 The check (control-plane side), 4.3 Anti-takeover rules, 4.4 Sequence: add-domain → verified, 4. DNS ownership verification

### Community 176 - "6. Agent security"
Cohesion: 0.40
Nodes (5): 6.1 Token scope, 6.2 docker.sock is root-equivalent, 6.3 Transport: HTTPS-only, 6.4 No arbitrary exec, 6. Agent security

### Community 177 - "._redact"
Cohesion: 0.50
Nodes (3): field_serializer, Mask any userinfo credentials before the URL leaves the API., redact_endpoint_url()

### Community 179 - "3. Entities (per domain-model.md §2.4)"
Cohesion: 0.67
Nodes (3): 3.1 Domain, 3.2 Route, 3. Entities (per domain-model.md §2.4)

## Knowledge Gaps
- **410 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+405 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1701 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AuthContext` connect `AuthContext` to `v1/auth.py`, `user_service.py`, `typing`, `project_service.py`, `projects.py`, `incidents.py`, `deployment_engine.py`, `v1/deployments.py`, `test_deployments_simulated.py`, `list_containers`, `metrics_service.py`, `deps.py`, `monitor_service.py`, `require_permission`, `get_latest_server_metrics`, `auth_service.py`, `docker_host_service.py`, `docker_hosts.py`, `scope_matches`, `monitors.py`, `server_service.py`, `test_permissions.py`, `servers.py`, `secret_service.py`, `role_service.py`, `api_key_service.py`, `rotate_secret`, `notification_service.py`, `middleware.py`, `update_channel`, `events.py`, `enums.py`, `v1/channels.py`, `containers.py`, `Hub`, `operation_service.py`, `AppError`, `get_sessionmaker`, `core/tenancy.py`, `list_audit_logs`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `get_settings()` connect `get_settings` to `v1/auth.py`, `user_service.py`, `typing`, `logging.py`, `get_redis`, `metrics_service.py`, `monitor_service.py`, `auth_service.py`, `docker_host_service.py`, `server_service.py`, `get_meta`, `UnprocessableEntity`, `collections_abc`, `notification_service.py`, `test_auth_journey.py`, `notification_sender.py`, `README.md - NexusOps overview`, `models/__init__.py`, `env.py`, `Settings`, `Hub`, `main.py`, `LogLine`, `test_app_gating.py`, `BadRequest`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Are the 83 inferred relationships involving `AuthContext` (e.g. with `TenancyScopeError` and `MembershipStatus`) actually correct?**
  _`AuthContext` has 83 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `APIModel` (e.g. with `OperationSpec` and `6.4 No arbitrary exec`) actually correct?**
  _`APIModel` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `apiGet()` (e.g. with `ContainerDetailPage.test.tsx` and `mockApi()`) actually correct?**
  _`apiGet()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `meta`, `SCHEMA`, `RESEARCH_COMMON` to the rest of the system?**
  _410 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `AuthContext.tsx` be split into smaller, more focused modules?**
  _Cohesion score 0.05319148936170213 - nodes in this community are weakly interconnected._