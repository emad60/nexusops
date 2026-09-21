# Graph Report - nexusops  (2026-09-21)

## Corpus Check
- 268 files · ~219,932 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: (none) 8, .example 1, .service 1)

## Summary
- 3570 nodes · 10483 edges · 169 communities (147 shown, 22 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 849 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7116d7d4`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ApiError
- v1/auth.py
- @tanstack/react-query
- apiGet
- App.tsx
- containers.py
- resolve_client_ip
- docker_host_service.py
- SimulatedDeploymentRunner
- models/__init__.py
- project_service.py
- ServerDetailPage.tsx
- APIModel
- client.ts
- projects.py
- incident_service.py
- deployment_engine.py
- SimulatedDockerProvider
- maintenance.py
- pagination.py
- docker_real.py
- list_containers
- metrics_service.py
- test_security.py
- Domain Routing — NexusOps
- monitor_service.py
- Node & Agent Architecture
- deps.py
- AuthContext.tsx
- nexusops_agent.py
- integration/conftest.py
- auth_service.py
- container_service.py
- types.ts
- AuthContext
- NotFound
- PageParams
- v1/search.py
- server_service.py
- v1/channels.py
- DockerProvider
- test_monitor_transport.py
- test_agent_contract.py
- v1/deployments.py
- RealDockerProvider
- test_permissions.py
- form.tsx
- servers.py
- test_ssrf.py
- secret_service.py
- publish
- test_schemas_server.py
- create_api_key
- users.py
- test_schemas_agent.py
- CheckOutcome
- require_permission
- alembic
- rate_limit.py
- test_auth_journey.py
- compilerOptions
- enums.py
- middleware.py
- observability.py
- test_deployment_runner.py
- notification_sender.py
- test_schema_redaction.py
- NotificationChannel
- Hub
- package.json
- events.py
- test_deployments_simulated.py
- Platform Security Model — NexusOps
- send_delivery
- api service (FastAPI / uvicorn :8000)
- config.py
- alerts.py
- event_bus.py
- roles.py
- ApiKeysPage.tsx
- scope_matches
- Settings
- resolve_auth
- v1/health.py
- hub.py
- Product Roadmap — NexusOps Multi-Tenant Platform
- devDependencies
- redact_mapping
- docs/engineering-report.md - build and verification report
- get_settings
- notification_service.py
- Deployment Architecture — NexusOps (target state)
- test_notifications.py
- test_event_registry.py
- run_async
- test_monitors_incidents.py
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- journey.spec.ts
- ProjectDetailPage.test.tsx
- 2. Entities
- Secrets Architecture
- encrypt_str
- sessions.py
- Container
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- DockerProviderError
- errors.py
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- _FakeAsyncClient
- README.md - NexusOps overview
- create_app
- log_service.py
- scripts
- ContainerListPage.test.tsx
- EnvironmentUpdate
- Platform Vision — NexusOps
- dependencies
- FakeWebSocket
- generate_secrets.sh
- tasks/deployments.py
- test_servers_and_audit.py
- router.py
- list_audit_logs
- DeploymentRunner
- monitor.py
- .__tablename__
- install.sh
- docker-entrypoint.sh
- integration/__init__.py
- CLAUDE.md - project graphify rules
- Graphify query workflow (query / path / explain / update)
- frontend/index.html - SPA shell
- NexusOps Favicon — stylized letter 'N' lettermark in sky blue (#38bdf8) on a dark navy rounded square (#0b1120, 7px corner radius)
- nexusops-backend
- register_account
- simulation_tick
- postgres service (PostgreSQL 17, loopback :5433)
- get_sessionmaker
- nexusops-understand.mjs
- Invisible account lockout (5 fails -> 15 min, enumeration resistance)
- permissions.py
- instant_pacing
- nexusops-draft.mjs
- helpers.py
- nexusops-challenge.mjs
- test_agent_ingestion.py
- effective_permissions
- 8. Upstream binding and re-render triggers
- 1. Current state
- paginate
- ApplicationBase
- _FakeCtx
- AppError
- agent_heartbeat
- pytest
- 4. ACME architecture
- 4. DNS ownership verification

## God Nodes (most connected - your core abstractions)
1. `AuthContext` - 121 edges
2. `APIModel` - 102 edges
3. `apiGet()` - 73 edges
4. `get_settings()` - 62 edges
5. `publish()` - 54 edges
6. `NotFound` - 53 edges
7. `PageParams` - 53 edges
8. `record()` - 53 edges
9. `apiPost()` - 53 edges
10. `ApiError` - 51 edges

## Surprising Connections (you probably didn't know these)
- `6. Enforcement mechanics (unchanged patterns, one addition)` --references--> `resolve_auth()`  [INFERRED]
  docs/authorization.md → backend/app/api/deps.py
- `2. Org resolution on every request` --references--> `resolve_auth()`  [INFERRED]
  docs/multi-tenancy.md → backend/app/api/deps.py
- `4. Phase 1 — Tenancy foundation` --references--> `resolve_auth()`  [INFERRED]
  docs/product-roadmap.md → backend/app/api/deps.py
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

## Communities (169 total, 22 thin omitted)

### Community 0 - "ApiError"
Cohesion: 0.03
Nodes (63): ApiError, DockerHostOut, SecretRow, SessionInfo, ME, mocks, Toast, TOAST_ARIA_LABEL (+55 more)

### Community 1 - "v1/auth.py"
Cohesion: 0.10
Nodes (44): change_password(), _clear_refresh_cookie(), _cookies_secure(), login(), logout(), me(), _optional_actor(), AsyncSession (+36 more)

### Community 2 - "@tanstack/react-query"
Cohesion: 0.05
Nodes (59): AuditEntry, DeploymentOut, EnvironmentOut, Page, ProjectOut, AuditLogPage, ContainerListPage, DeploymentListPage (+51 more)

### Community 3 - "apiGet"
Cohesion: 0.08
Nodes (58): apiDelete(), apiGet(), apiPatch(), apiPost(), ApplicationOut, MonitorListPage, ProjectDetailPage, useAuth() (+50 more)

### Community 4 - "App.tsx"
Cohesion: 0.04
Nodes (57): DashboardSummary, DeploymentStepOut, IncidentEventOut, SearchResult, AlertsPage, App(), DashboardPage, DeploymentDetailPage (+49 more)

### Community 5 - "containers.py"
Cohesion: 0.12
Nodes (22): asyncio, Container API: listing/detail, lifecycle actions, removal, logs, streaming.…, configure_logging(), get_logger(), _orjson_dumps(), Any, Structured logging via structlog. Every log record carries timestamp, level,…, Configure structlog + stdlib logging once at process start. Everything… (+14 more)

### Community 6 - "resolve_client_ip"
Cohesion: 0.18
Nodes (21): _is_trusted(), _parse_networks(), Request, Client-IP resolution behind chained reverse proxies. The API never takes TCP…, Parse a comma-separated CIDR list; malformed entries are skipped., Real client address for *request* per the trust model above., resolve_client_ip(), make_request() (+13 more)

### Community 7 - "docker_host_service.py"
Cohesion: 0.05
Nodes (83): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+75 more)

### Community 8 - "SimulatedDeploymentRunner"
Cohesion: 0.22
Nodes (13): LogLevel, _commit_short(), Deployment runner port plus a faithful simulated implementation.…, Staged docker-style simulation used by v1 deployments., Everything a runner needs to execute one deployment., One streamed output line for a step., RunContext, SimulatedDeploymentRunner (+5 more)

### Community 9 - "models/__init__.py"
Cohesion: 0.11
Nodes (45): Base, Base for all ORM models with stable constraint naming for Alembic., TimestampMixin, DeploymentEnvironment, Project, UserStatus, ApiKey, Permission (+37 more)

### Community 10 - "project_service.py"
Cohesion: 0.17
Nodes (37): Application, EnvironmentCreate, Payload to create an environment under an application., _apply_update(), _check_server(), create_application(), create_environment(), create_project() (+29 more)

### Community 11 - "ServerDetailPage.tsx"
Cohesion: 0.07
Nodes (45): ContainerOut, MetricPoint, ServerDetail, ServerSummary, ServerDetailPage, ServerListPage, ChartSeries, LineChart() (+37 more)

### Community 12 - "APIModel"
Cohesion: 0.06
Nodes (46): ApiKeyCreateRequest, API key schemas. Raw keys appear exactly once, at creation., AuditOut, Schemas for the read-only audit log API. The audit table is append-only; these…, One audit trail entry (no write routes ever exist for this resource)., APIModel, OutModel, BaseModel (+38 more)

### Community 13 - "client.ts"
Cohesion: 0.06
Nodes (43): API_BASE, apiRequest(), buildUrl(), extractError(), getAccessToken(), refreshToken(), RequestOptions, EventItem (+35 more)

### Community 14 - "projects.py"
Cohesion: 0.11
Nodes (49): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+41 more)

### Community 15 - "incident_service.py"
Cohesion: 0.10
Nodes (55): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+47 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.13
Nodes (49): deployment_log_channel(), Deployment, DeploymentStep, DeploymentStatus, EventLevel, StepStatus, _after_commit_enqueue(), _after_rollback_drop() (+41 more)

### Community 17 - "SimulatedDockerProvider"
Cohesion: 0.09
Nodes (29): ContainerHealth, Any, Plausible numbers derived from the row plus time-based sine noise., Implements :class:`DockerProvider` semantics against DB rows., Attach already-fetched log rows so ``logs()`` can replay them., _seed_int(), SimulatedDockerProvider, _log_entry() (+21 more)

### Community 18 - "maintenance.py"
Cohesion: 0.16
Nodes (21): _run(), _run(), aggregate_metrics(), _run(), _collect_logs(), expire_sessions(), _run(), task (+13 more)

### Community 19 - "pagination.py"
Cohesion: 0.15
Nodes (25): Cursor, cursor_params(), CursorPage, CursorParams, decode_cursor(), encode_cursor(), Page, BaseModel (+17 more)

### Community 20 - "docker_real.py"
Cohesion: 0.14
Nodes (22): ContainerStats, Point-in-time resource usage snapshot., _as_float(), _compute_stats(), _cpu_percent(), _network_bytes(), parse_log_line(), parse_rfc3339() (+14 more)

### Community 21 - "list_containers"
Cohesion: 0.06
Nodes (61): _action_route(), _endpoint(), _container_out(), _decode_frame(), _ev(), get_container(), _like_pattern(), list_container_logs() (+53 more)

### Community 22 - "metrics_service.py"
Cohesion: 0.08
Nodes (42): get_dashboard_summary(), get_latest_server_metrics(), get_server_metrics(), CurrentUser, DbDep, Depends, get, UUID (+34 more)

### Community 23 - "test_security.py"
Cohesion: 0.13
Nodes (31): argon2, argon2_exceptions, generate_agent_token(), generate_api_key(), generate_refresh_token(), hash_password(), hash_token(), password_needs_rehash() (+23 more)

### Community 24 - "Domain Routing — NexusOps"
Cohesion: 0.11
Nodes (18): 10. Wildcards and catch-all, 11. User journey, 12. API surface, permissions, audit, 13. Monitoring tie-in, 1. Scope and current state, 2. Where nginx runs, 3.1 Domain, 3.2 Route (+10 more)

### Community 25 - "monitor_service.py"
Cohesion: 0.15
Nodes (38): MonitorStatus, Monitor, MonitorCheck, MonitorUpdate, Partial update; ``url`` changes are re-validated against the SSRF guard., _active_incident(), _audit(), claim_due_monitors() (+30 more)

### Community 26 - "Node & Agent Architecture"
Cohesion: 0.11
Nodes (19): 1. Scope and stance, 2.1 Current shape (real), 2.2 Changes for the target model, 2.3 Capabilities (target), 2.4 DockerEndpoint — the 0..1 relation, 2. The Node concept, 6.1 Token scope, 6.2 docker.sock is root-equivalent (+11 more)

### Community 27 - "deps.py"
Cohesion: 0.19
Nodes (16): FastAPI dependencies: database session, authentication context, RBAC gate.…, Agent ingest endpoints: enrollment handshake and periodic heartbeats.…, API key routes — self-service management of the caller's own machine…, Audit log API. Strictly read-only: the table is append-only by design., Instance metadata: version, mode, and the caller's effective capabilities. The…, Metrics query API: server timeseries, latest snapshot, dashboard summary., Secrets manager API. Reads return metadata only; plaintext values are accepted…, get_session() (+8 more)

### Community 28 - "AuthContext.tsx"
Cohesion: 0.07
Nodes (28): setAccessToken(), Role, User, AuthContext, AuthProvider(), AuthState, MeResponse, permissionMatches() (+20 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.06
Nodes (37): AgentClient, build_heartbeat(), collect_container_stats(), collect_containers(), cpu_percent_since(), disk_stats(), _docker_request(), load1() (+29 more)

### Community 30 - "integration/conftest.py"
Cohesion: 0.16
Nodes (17): alembic_config, _clean_slate(), client(), _ensure_database(), _migrated_database(), owner(), AsyncClient, fixture (+9 more)

### Community 31 - "auth_service.py"
Cohesion: 0.13
Nodes (36): ActorType, AuditResult, _audit(), change_own_password(), count_users(), _event(), _grace_successor(), _issue_access() (+28 more)

### Community 32 - "container_service.py"
Cohesion: 0.14
Nodes (33): ContainerStatus, DockerHostStatus, DockerHost, describe_provider_error(), is_simulated(), provider_for(), Exception, Return the provider matching *host*'s endpoint configuration. (+25 more)

### Community 33 - "types.ts"
Cohesion: 0.07
Nodes (31): AlertOut, ChannelOut, CheckOut, CursorPage, DeliveryOut, DeploymentLogLine, DeploymentStatus, IncidentOut (+23 more)

### Community 34 - "AuthContext"
Cohesion: 0.12
Nodes (21): AuthContext, Resolved identity attached to every authenticated request., create_api_key(), list_api_keys(), AsyncSession, Request, UUID, Live (non-revoked) keys owned by *owner_id*, newest first. (+13 more)

### Community 35 - "NotFound"
Cohesion: 0.14
Nodes (33): NotFound, _apply_deactivation(), _assert_not_last_active_superadmin(), create_user(), deactivate_user(), get_by_email(), get_user(), list_sessions() (+25 more)

### Community 36 - "PageParams"
Cohesion: 0.14
Nodes (36): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+28 more)

### Community 37 - "v1/search.py"
Cohesion: 0.09
Nodes (41): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+33 more)

### Community 38 - "server_service.py"
Cohesion: 0.09
Nodes (53): server_metrics_channel(), ServerStatus, Server, _actor_kwargs(), _apply_agent_entry(), container_counts(), create_server(), delete_server() (+45 more)

### Community 39 - "v1/channels.py"
Cohesion: 0.15
Nodes (27): create_channel(), delete_channel(), get_channel(), list_channels(), list_deliveries(), DbDep, delete, Depends (+19 more)

### Community 40 - "DockerProvider"
Cohesion: 0.08
Nodes (12): DockerProvider, Any, datetime, Protocol, List containers visible to the provider., Inspect a single container by id (short ids allowed)., List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``., List volumes: keys ``name``, ``driver``, ``mountpoint``. (+4 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.08
Nodes (48): CheckResult, coerce_headers(), _decode(), get_transport(), HTTPMonitorTransport, Any, BaseException, Pluggable monitor check transports (real HTTP + deterministic simulator). A… (+40 more)

### Community 42 - "test_agent_contract.py"
Cohesion: 0.18
Nodes (16): agent_fixture(), _load_agent(), _patch_stats(), Any, fixture, MonkeyPatch, Contract tests: the shipped agent's payloads must satisfy the ingest schemas.…, One-shot docker stats reduce to cpu/mem/limit fields the schema accepts, with… (+8 more)

### Community 43 - "v1/deployments.py"
Cohesion: 0.09
Nodes (45): _attribute_step_idx(), cancel_deployment(), _emails_for(), get_deployment(), list_application_deployments(), list_deployment_logs(), _list_deployments(), _parse_sort() (+37 more)

### Community 44 - "RealDockerProvider"
Cohesion: 0.18
Nodes (6): ContainerInfo, Normalized view of a container as reported by any provider., T, Execute an SDK call with one short retry, normalizing failures., Talks to a real docker daemon over ``unix://`` or ``tcp://``., RealDockerProvider

### Community 45 - "test_permissions.py"
Cohesion: 0.17
Nodes (9): permission_exists(), _auth_context(), Unit tests for the permission registry, scope matching and RBAC gate., test_api_key_scope_intersects_role_permissions(), test_permission_exists_helper(), test_plain_user_without_permissions_is_denied(), test_superadmin_bypasses_everything(), test_superadmin_owned_api_key_is_limited_to_its_scope() (+1 more)

### Community 46 - "form.tsx"
Cohesion: 0.10
Nodes (17): LoginPage, CheckboxField(), CheckboxFieldProps, FieldAria, FieldBaseProps, PasswordField(), PasswordFieldProps, SearchInputProps (+9 more)

### Community 47 - "servers.py"
Cohesion: 0.07
Nodes (52): create_server(), delete_server(), _detail(), get_server(), list_servers(), list_tags(), AsyncSession, DbDep (+44 more)

### Community 48 - "test_ssrf.py"
Cohesion: 0.08
Nodes (61): BadRequest, UnprocessableEntity, assert_safe_tcp_endpoint(), assert_safe_url(), assert_safe_url_async(), _is_forbidden_address(), is_simulation_url(), _raise_block() (+53 more)

### Community 49 - "secret_service.py"
Cohesion: 0.15
Nodes (26): _actor_type(), _collect_refs(), create_secret(), delete_secret(), _detail(), get_secret(), get_secret_detail(), list_secrets() (+18 more)

### Community 50 - "publish"
Cohesion: 0.17
Nodes (23): Conflict, publish(), UUID, Persist an event and fan it out to Redis. Returns None when deduplicated., create_role(), delete_role(), get_role(), list_roles() (+15 more)

### Community 51 - "test_schemas_server.py"
Cohesion: 0.23
Nodes (20): Payload for registering a server., ServerCreate, _base(), parametrize, Unit tests for app.schemas.server (validation only, no I/O)., test_empty_ip_is_allowed_but_whitespace_collapses(), test_empty_name_or_hostname_rejected(), test_heartbeat_interval_bounds_inclusive() (+12 more)

### Community 52 - "create_api_key"
Cohesion: 0.16
Nodes (17): create_api_key(), list_api_keys(), CurrentUser, DbSessionDep, delete, get, post, Request (+9 more)

### Community 53 - "users.py"
Cohesion: 0.14
Nodes (24): create_user(), deactivate_user(), get_user(), list_users(), CurrentUser, DbSessionDep, delete, get (+16 more)

### Community 54 - "test_schemas_agent.py"
Cohesion: 0.12
Nodes (31): AgentContainerIn, AgentHeartbeatIn, AgentHelloIn, AgentHelloOut, field_validator, Agent-facing schemas. Payloads are data only — never executed., First contact from an agent after enrollment; fills static host facts., Tells the agent how often to report. (+23 more)

### Community 55 - "CheckOutcome"
Cohesion: 0.29
Nodes (5): CheckOutcome, MonitorTransport, Protocol, Result of a single monitor check., Anything that can execute a check for a monitor.

### Community 56 - "require_permission"
Cohesion: 0.12
Nodes (28): permission_dep(), Any, Dependency factory enforcing a permission; returns 403 when denied., require_permission(), _check(), create_secret(), delete_secret(), get_secret() (+20 more)

### Community 58 - "rate_limit.py"
Cohesion: 0.15
Nodes (21): RateLimited, client_ip(), _memory_count_and_ttl(), Request, rate_limit(), _dependency(), Redis-backed fixed-window rate limiting as a FastAPI dependency factory. Auth-…, Best-effort client IP; honours X-Forwarded-For from trusted proxies. Delegates… (+13 more)

### Community 59 - "test_auth_journey.py"
Cohesion: 0.14
Nodes (26): assert_error_code(), cookie_attributes(), login_account(), Response, Assert envelope shape + code; returns the inner error object., The raw Set-Cookie header carrying the refresh token., Extract just the opaque token from a Set-Cookie header., Parse Set-Cookie attributes (lowercased keys, empty string for flags). (+18 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "enums.py"
Cohesion: 0.12
Nodes (26): big_serial_pk(), json_column(), datetime, UUID, Declarative base, shared mixins and column helpers., Identity PK for very high-volume tables (metrics, logs)., status_check(), _utcnow() (+18 more)

### Community 62 - "middleware.py"
Cohesion: 0.13
Nodes (16): ASGIApp, UUID, AccessLogMiddleware, Request, Response, HTTP middleware: request ids, security headers, structured access logs., Baseline hardening headers on every API response., RequestIDMiddleware (+8 more)

### Community 63 - "observability.py"
Cohesion: 0.17
Nodes (19): AlertSeverity, Alert, Observability: monitors, checks, incidents, metrics, logs, events, audit., create_alert(), get_alert(), mark_all_read(), mark_read(), AsyncSession (+11 more)

### Community 64 - "test_deployment_runner.py"
Cohesion: 0.25
Nodes (19): _pace(), Deterministic per-line delay between 0.05s and 0.35s., Canonical step identifiers stored on :class:`DeploymentStep` rows., StepName, _collect(), _ctx(), Unit tests for SimulatedDeploymentRunner (async generators, no broker)., test_broken_version_does_not_affect_other_steps() (+11 more)

### Community 65 - "notification_sender.py"
Cohesion: 0.15
Nodes (18): NotificationError, Any, BaseException, Exception, Low-level notification transports: SMTP email and outgoing webhooks. These…, POST *payload* as JSON to *url*; 2xx is success, anything else raises. Response…, Raised when a delivery attempt fails. Message is safe to persist., Bounded, single-line, content-free error reason. (+10 more)

### Community 66 - "test_schema_redaction.py"
Cohesion: 0.18
Nodes (17): is_sensitive_header(), mask_sensitive_headers(), True when *name* looks like it carries a credential (Authorization etc.)., Return a copy of *headers* with sensitive values replaced by a mask., mask_target(), Human-readable masked target safe to expose over the API. For webhook families…, _monitor_out(), Outbound-schema redaction: monitor probe credentials and webhook targets.… (+9 more)

### Community 67 - "NotificationChannel"
Cohesion: 0.22
Nodes (18): NotificationChannel, A delivery target (email address / webhook endpoint). ``config_ciphertext``…, _audit(), create_channel(), decrypt_channel_config(), delete_channel(), encrypt_config(), _normalize_events() (+10 more)

### Community 68 - "Hub"
Cohesion: 0.13
Nodes (18): _close_socket(), Connection, _entity_exists(), Hub, _params_key(), _parse_payload(), Any, WebSocket (+10 more)

### Community 69 - "package.json"
Cohesion: 0.13
Nodes (15): name, private, type, version, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom (+7 more)

### Community 70 - "events.py"
Cohesion: 0.16
Nodes (19): _decode_cursor(), _encode_cursor(), list_event_types(), list_events(), datetime, DbSession, Depends, get (+11 more)

### Community 71 - "test_deployments_simulated.py"
Cohesion: 0.18
Nodes (19): execute_deployment(), Run one deployment to a terminal state. Never raises; safe to re-run., _delivery_chain(), _owner_ctx(), _queue(), _queued_with_recorder(), Deployment engine over the simulated runner: success, failure, rollback., queue_deployment with the Celery handoff recorded instead of dispatched. (+11 more)

### Community 72 - "Platform Security Model — NexusOps"
Cohesion: 0.11
Nodes (19): 10.1 Node revocation playbook (compromised node / leaked agent token), 10.2 Key compromise playbook, 10. Incident response, 1.1 Real vs simulated today (do not mistake one for the other), 1. Scope, stance, and simulation honesty, 2. Assets, 3. Trust boundaries, 4. Tenant isolation model (summary) (+11 more)

### Community 73 - "send_delivery"
Cohesion: 0.17
Nodes (18): _as_uuid(), decode_delivery_cursor(), dispatch_event_frame(), _send(), dispatcher_loop(), encode_delivery_cursor(), list_deliveries(), _now() (+10 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "config.py"
Cohesion: 0.14
Nodes (15): _database_url(), Alembic environment: metadata comes from app.models, URL from app settings., Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online(), fail_on_bad_config(), Central configuration. All runtime configuration flows through this module so… (+7 more)

### Community 76 - "alerts.py"
Cohesion: 0.19
Nodes (17): list_alerts(), mark_all_read(), mark_read(), CurrentUser, DbDep, Depends, get, post (+9 more)

### Community 77 - "event_bus.py"
Cohesion: 0.14
Nodes (22): get_redis(), ping(), Shared async Redis client., _after_commit_publish(), _after_rollback_drop(), event_frame_from_row(), _publish_after_commit(), _publish_redis() (+14 more)

### Community 78 - "roles.py"
Cohesion: 0.11
Nodes (26): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, delete, get (+18 more)

### Community 79 - "ApiKeysPage.tsx"
Cohesion: 0.13
Nodes (15): ApiKeyOut, ApiKeysPage, ApiKeyCreatedOut, handleCopyKey(), copyText(), describeError(), EMPTY_FORM, GROUP_STYLE (+7 more)

### Community 80 - "scope_matches"
Cohesion: 0.14
Nodes (14): Check an API-key scope list against a required permission. Supports exact match…, scope_matches(), parametrize, test_scope_matches_truth_table(), 1. Principles (already true in the codebase, kept), 2. Registry changes (Phase 1 + new subsystems), 3. The five system roles (target), 4. Grants (resource-level access; design now, later phase) (+6 more)

### Community 81 - "Settings"
Cohesion: 0.16
Nodes (5): field_validator, model_validator, Validated application settings (loaded from environment / .env)., Settings, BaseSettings

### Community 82 - "resolve_auth"
Cohesion: 0.29
Nodes (10): get_current_user(), get_optional_user(), _load_permissions(), AsyncSession, DbSessionDep, Request, Standard authentication dependency. Also records client IP for logs/audit., Like :func:`get_current_user` but returns ``None`` for anonymous callers. (+2 more)

### Community 83 - "v1/health.py"
Cohesion: 0.20
Nodes (13): liveness(), get, Response, Health probes: liveness (always cheap) and readiness (checks dependencies).…, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness(), HealthOut (+5 more)

### Community 84 - "hub.py"
Cohesion: 0.17
Nodes (14): _authenticate_api_key(), _authenticate_jwt(), _is_same_origin(), _load_permissions(), AsyncSession, User, WebSocket hub: authenticated live streams fanned in from Redis pub/sub.…, Browsers always send Origin on WS handshakes, even same-origin ones. When it… (+6 more)

### Community 85 - "Product Roadmap — NexusOps Multi-Tenant Platform"
Cohesion: 0.13
Nodes (15): 0. Stance, 10. Phase 7 — Teams, grants & custom roles, 11. Phase 8 — Backups, 12. Phase 9 — Billing & metering, 13. First commercially meaningful version, 14. Biggest risks (short form), 15. Reading order, 2. Phase plan (+7 more)

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "redact_mapping"
Cohesion: 0.22
Nodes (13): _is_sensitive_key(), Substring match on a normalised key so header-style names are caught too.…, Return a copy of *data* with sensitive values replaced. Used by audit metadata…, redact_mapping(), parametrize, Unit tests for app.core.logging redaction (pure functions only)., test_case_insensitive_substring_match(), test_flat_sensitive_keys_redacted() (+5 more)

### Community 88 - "docs/engineering-report.md - build and verification report"
Cohesion: 0.27
Nodes (12): docker-compose.dev.yml - dev overlay, docker-compose.docker-sock.yml - docker socket override, docker-compose.yml - full stack definition, docs/agent.md - agent guide, docs/api.md - API guide, Append-only audit log (Postgres BEFORE UPDATE OR DELETE trigger), docs/deployment.md - deployment and operations guide, docs/development.md - developer guide (+4 more)

### Community 89 - "get_settings"
Cohesion: 0.15
Nodes (21): get_meta(), DbSessionDep, get, Public metadata; identity fields appear only for valid credentials., get_settings(), Return the cached settings singleton., Unauthorized, create_access_token() (+13 more)

### Community 90 - "notification_service.py"
Cohesion: 0.21
Nodes (13): ChannelType, ChannelBase, ChannelCreate, ChannelOut, ChannelUpdate, EmailConfig, model_validator, Schemas for notification channels and delivery records. Channel configuration… (+5 more)

### Community 91 - "Deployment Architecture — NexusOps (target state)"
Cohesion: 0.11
Nodes (20): Exception, Raised by a runner when a step fails irrecoverably., StepFailure, 10. Events and WS during runs, 11. Post-deploy hooks, 12. Rollback semantics (existing behavior kept), 13. The simulated runner stays — labeled, 14. Open questions (+12 more)

### Community 92 - "test_notifications.py"
Cohesion: 0.33
Nodes (10): NotificationDelivery, SystemEvent, _channel(), _delivery(), UUID, Notification channel + delivery-log endpoints. Regression coverage for GET…, The same event frame consumed twice queues ONE delivery per channel. Every API…, test_dispatch_frame_is_idempotent_across_workers() (+2 more)

### Community 93 - "test_event_registry.py"
Cohesion: 0.21
Nodes (8): event_type_catalogue(), is_known_event_type(), Canonical registry of system-event types. Single source of truth shared by…, Return True when *event_type* is part of the canonical registry., Serialise the registry for the ``/events/types`` endpoint., Registry coherence: schema-advertised event types must equal the canonical…, test_catalogue_serialises_every_entry(), test_known_event_lookup()

### Community 94 - "run_async"
Cohesion: 0.16
Nodes (18): task, Flag silent servers OFFLINE, recover returning ones. Safe to overlap., sweep_servers(), task, Claim up to CLAIM_BATCH due monitors and execute each check.…, run_due_monitors(), Any, T (+10 more)

### Community 95 - "test_monitors_incidents.py"
Cohesion: 0.36
Nodes (7): _create_monitor(), Monitor checks driving the full down -> incident -> recovery lifecycle., Regression: probe headers and URL query credentials never leave the API. Probe…, test_check_now_endpoint_runs_immediately(), test_down_then_recover_lifecycle(), test_metadata_endpoint_and_private_target_blocked(), test_monitor_responses_mask_probe_credentials()

### Community 96 - "NexusOps (self-hosted infrastructure management and monitoring platform)"
Cohesion: 0.20
Nodes (10): mailpit service (dev SMTP sink + web UI :8025), NexusOps compose stack (8 services on one network), HIGH finding: redirect-following SSRF in uptime monitors (fixed: follow_redirects=False + per-hop guard), SSRF guard (assert_safe_url, per-redirect-hop validation, assert_safe_tcp_endpoint), Mailpit SMTP port internal-only (host-side injection needs extra mapping), Host port knobs (NEXUSOPS_HTTP_PORT/POSTGRES/REDIS/MAILPIT/VITE), SPA entry point (loads /src/main.tsx, dark color-scheme), Uptime monitors -> incidents -> notifications flow (+2 more)

### Community 97 - "REST API surface (/api/v1)"
Cohesion: 0.29
Nodes (7): Cursor (keyset) and offset pagination envelopes, Permission model (data-driven registry, require_permission, wildcard scopes), REST API surface (/api/v1), RBAC registry (PERMISSIONS + ROLE_MATRIX + scope_matches), Adding a new resource: 7-step checklist (model -> migration -> schemas -> service -> router -> tests -> frontend), Alembic migration workflow (autogenerate, models __init__ export, entrypoint apply), Command palette (Ctrl/Cmd+K)

### Community 98 - "journey.spec.ts"
Cohesion: 0.21
Nodes (9): ADMIN, Bootstrap, bootstrapVia(), test, ADMIN, formLogin(), uiGoto(), UNIQUE (+1 more)

### Community 99 - "ProjectDetailPage.test.tsx"
Cohesion: 0.15
Nodes (8): ApiError, EMPTY_SERVERS, get, ME, patch, post, PROD_ENV, PROJECT

### Community 100 - "2. Entities"
Cohesion: 0.14
Nodes (14): 0. Design stance, 1.1 ER diagram, 1. The hierarchy, 2.1.1 ApiKey org binding detail, 2.2.1 Environment promotion detail, 2.2 Delivery (existing models, extended), 2.3 Infrastructure — Nodes, 2.4 Routing & TLS (new subsystem) (+6 more)

### Community 101 - "Secrets Architecture"
Cohesion: 0.15
Nodes (13): 10. Resolution flow at deploy time, 2.1 Resolution runs inside org scope, 2.2 Migration mapping, 2. Target scope model (org / project / environment layering), 3.1 What this fixes, 3. SecretVersion — append-only history, 4.1 Audit event at resolution time, 4. Resolution authorization (+5 more)

### Community 102 - "encrypt_str"
Cohesion: 0.08
Nodes (33): decrypt_str(), digest_of(), encrypt_str(), _fernet(), Short server-verifiable digest used for change detection display. HMAC-SHA256…, _create(), Secrets: metadata-only reads, rotation versioning, deploy-time resolution., ${secret:KEY} placeholders resolve through decrypt at deploy time. (+25 more)

### Community 103 - "sessions.py"
Cohesion: 0.19
Nodes (13): list_sessions(), CurrentUser, DbSessionDep, delete, get, Request, UUID, Session routes: list active sessions, revoke own or (with user.manage) any. (+5 more)

### Community 104 - "Container"
Cohesion: 0.17
Nodes (11): dispose_engine(), Container, Observed container state mirrored from an agent or docker provider., Make a container row visible to this provider instance., Reconcile every registered Docker host; pull recent logs from real ones., sync_docker_hosts(), The docker-host maintenance sweep must actually reach real hosts., Re-collection stores only lines newer than the newest stored row. The sweep re-… (+3 more)

### Community 105 - "redis service (Redis 7, no persistence, loopback :6390)"
Cohesion: 0.22
Nodes (11): redis service (Redis 7, no persistence, loopback :6390), WebSocket API (/api/v1/ws handshake, frames, limits), WebSocket channels (global, server-metrics, container-logs, deployment-logs, incidents), Deployment engine (queue_deployment / execute_deployment / sweeper backstop), Real-time spine: PostgreSQL system_events + Redis pub/sub, Rollback as a new deployment (rollback_of_id), WebSocket hub (framework-thin, Redis fan-in, per-socket queues), Test suites (pytest unit+integration, vitest, Playwright e2e) (+3 more)

### Community 106 - "NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)"
Cohesion: 0.18
Nodes (12): Agent security model (one-way telemetry, no command channel), Agent enrollment token (X-Agent-Token, nxa_..., SHA-256 at rest), Agent heartbeat exponential backoff (cap 5 min, exit 1 on revoked token), agent/install.sh (enrollment installer), Agent metrics collection (/proc statvfs Docker socket), NexusOps agent (stdlib-only Python, agent/nexusops_agent.py), Agent systemd hardening (ProtectSystem=strict, NoNewPrivileges), Agent ingest API (POST /agent/hello, POST /agent/heartbeat) (+4 more)

### Community 107 - "DockerProviderError"
Cohesion: 0.15
Nodes (15): clip(), DockerProviderError, Exception, Provider abstraction for docker hosts (real daemon or simulated). Providers are…, A provider operation failed. ``str()`` is safe to show/log., Build a compact, secret-free description of a provider failure. Only the…, Truncate *text* to *limit* characters, stripping control chars., sanitize_error() (+7 more)

### Community 108 - "errors.py"
Cohesion: 0.10
Nodes (17): _error_payload(), Any, FastAPI, Request, Error taxonomy and the single place where API error envelopes are shaped. Every…, register_exception_handlers(), handle_app_error(), handle_http_exception() (+9 more)

### Community 109 - "Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)"
Cohesion: 0.25
Nodes (9): API keys (X-API-Key, nxo_..., scope intersection), First boot sequence (api entrypoint migrates, compose never seeds), Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test), Makefile workflows (up/test/lint/typecheck/migrate/seed), HIGH finding: API-key scope bypass for superadmin-owned keys (fixed: scope intersection first), Security audit 2026-09 (26 raw findings -> 20 confirmed, all fixed), HIGH finding: known seed superadmin + API key backdoor (fixed: NEXUSOPS_ALLOW_SEED opt-in, one-time password), Threat model (edge attacker, malicious agent, curious operator, leaked token, SSRF) (+1 more)

### Community 110 - "_FakeAsyncClient"
Cohesion: 0.22
Nodes (3): _FakeAsyncClient, _FakeRequestObj, Scripted httpx.AsyncClient: responses keyed by absolute request URL.

### Community 112 - "create_app"
Cohesion: 0.20
Nodes (15): close_redis(), create_app(), _include_routers(), lifespan(), FastAPI, Mount every domain router. Router variables follow the module contract., Start the WS hub + notification dispatcher; tear them down cleanly., _app_for_environment() (+7 more)

### Community 113 - "log_service.py"
Cohesion: 0.12
Nodes (25): container_log_channel(), Canonical Redis pub/sub channel names shared by API, workers and WS hub., LogSource, LogLine, One parsed log record from a container log stream., datetime, Replay registered LogEntry rows ordered by ts (tail N). ``follow`` is ignored…, append_lines() (+17 more)

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "ContainerListPage.test.tsx"
Cohesion: 0.29
Nodes (3): ApiError, server, serversPage

### Community 116 - "EnvironmentUpdate"
Cohesion: 0.29
Nodes (7): EnvironmentBase, EnvironmentUpdate, field_validator, Shared environment fields., Partial environment update; omitted fields are left untouched., 1.4 Deploy-time resolution today, 8. Environment config vs secrets boundary

### Community 117 - "Platform Vision — NexusOps"
Cohesion: 0.20
Nodes (10): 1. Where NexusOps is today, 2.1 What we are NOT building, 2.2 The wedge (differentiation), 2. The direction, 3. Guiding principles, 4. Customer journey (target), 5.1 Architecture overview (target), 5. Control plane / data plane boundary (+2 more)

### Community 118 - "dependencies"
Cohesion: 0.33
Nodes (6): dependencies, lucide-react, react, react-dom, react-router-dom, @tanstack/react-query

### Community 120 - "generate_secrets.sh"
Cohesion: 0.47
Nodes (3): existing_real_keys(), replace_or_append(), generate_secrets.sh script

### Community 121 - "tasks/deployments.py"
Cohesion: 0.29
Nodes (7): task, Deployment execution task + stuck-deployment sweeper., Execute one queued deployment. The engine owns all state transitions., Re-enqueue deployments the broker lost; fail ones whose worker died.…, run_deployment(), _run(), sweep_deployments()

### Community 122 - "test_servers_and_audit.py"
Cohesion: 0.22
Nodes (14): A valid POST /servers body with per-test overrides., server_payload(), Regression: a superadmin-owned key is still limited to its scope list. The…, test_scoped_api_key_cannot_exceed_its_grant(), _create_server(), Server CRUD, cascade delete, audit trail rows and audit immutability., The HTTP listing path — schema serialization is exercised end-to-end. A…, test_agent_token_rotation_invalidates_previous() (+6 more)

### Community 123 - "router.py"
Cohesion: 0.40
Nodes (4): websocket, WebSocket endpoint. Mounted by the app factory under ``/api/v1``., Hand the socket to the hub (auth handshake handled there)., websocket_endpoint()

### Community 124 - "list_audit_logs"
Cohesion: 0.29
Nodes (7): list_audit_logs(), datetime, DbSession, Depends, get, PageParamsDep, Newest-first audit trail with optional filters. No write routes exist for this…

### Community 125 - "DeploymentRunner"
Cohesion: 0.22
Nodes (7): DeploymentRunner, Protocol, Adapter interface implemented by real (future) and simulated runners., Return the ordered step names for this run., Stream output lines for *step_name*; raise StepFailure to fail it., test_runner_satisfies_protocol(), 2. What survives unchanged

### Community 126 - "monitor.py"
Cohesion: 0.17
Nodes (12): Drop the query string so signed tokens never appear in error text., Public alias: redact any query string from a URL before display/persist., strip_query(), MonitorBase, MonitorCheckOut, MonitorCreate, MonitorSortField, Schemas for uptime monitors and their check history. (+4 more)

### Community 146 - "register_account"
Cohesion: 0.22
Nodes (11): error_of(), Any, AsyncClient, Bootstrap owner account + session; returns ``(credentials, login_result)``., Unwrap an API error envelope., Register a user; returns ``(request_payload, response_body)``., register_account(), register_and_login() (+3 more)

### Community 147 - "simulation_tick"
Cohesion: 0.33
Nodes (7): _containers_for(), task, Deterministic smooth value in [base-amplitude, base+amplitude]., Stable per-server container set; one container cycles EXITED occasionally., simulation_tick(), _run(), _wave()

### Community 148 - "postgres service (PostgreSQL 17, loopback :5433)"
Cohesion: 0.29
Nodes (7): postgres service (PostgreSQL 17, loopback :5433), Fernet encryption at rest (ENCRYPTION_KEY, write-once), Backups (pgdata volume, nightly pg_dump, ephemeral Redis), Required secrets (POSTGRES_PASSWORD, JWT_SECRET >= 32 chars, ENCRYPTION_KEY Fernet), Production hardening checklist (secrets, ENVIRONMENT, no seed, TLS, rotation), Compose vs host network namespaces (postgres:5432 vs 127.0.0.1:5433), Simulation mode (SIMULATION_MODE)

### Community 149 - "get_sessionmaker"
Cohesion: 0.33
Nodes (6): async_sessionmaker, AsyncEngine, get_engine(), get_sessionmaker(), AsyncSession, racing_flush()

### Community 150 - "nexusops-understand.mjs"
Cohesion: 0.33
Nodes (5): COMMON, meta, out, READERS, SCHEMA

### Community 151 - "Invisible account lockout (5 fails -> 15 min, enumeration resistance)"
Cohesion: 0.33
Nodes (6): Invisible account lockout (5 fails -> 15 min, enumeration resistance), Unified error envelope (code, message, request_id), Per-IP rate limiting (Redis fixed window), Request lifecycle (edge -> middleware -> rate limit -> deps -> router), Client IP resolution (resolve_client_ip, TRUSTED_PROXY_CIDRS, XFF overwrite), EmailStr rejects reserved domains (login 422 on .test/.local/.arpa)

### Community 152 - "permissions.py"
Cohesion: 0.33
Nodes (4): PermissionSpec, Permission registry and role matrix. Permissions are *data*: the registry below…, dataclasses, fnmatch

### Community 153 - "instant_pacing"
Cohesion: 0.40
Nodes (4): instant_pacing(), fixture, MonkeyPatch, Remove the per-line sleeps; pacing bounds are asserted separately.

### Community 154 - "nexusops-draft.mjs"
Cohesion: 0.40
Nodes (4): DOCS, meta, SPINE, VERIFY_RULES

### Community 155 - "helpers.py"
Cohesion: 0.19
Nodes (14): bearer(), login_headers(), Pure helpers for journey tests: payloads, auth shortcuts, cookie parsing., A fresh, deliverable-shaped address unique to a single test. ``example.com`` is…, unique_email(), Sessions must carry the real client address, not the proxy hop's peer. Behind…, Client-injected leftmost XFF entries must not poison the session IP., test_login_ignores_spoofed_forwarded_entries() (+6 more)

### Community 156 - "nexusops-challenge.mjs"
Cohesion: 0.33
Nodes (5): CHALLENGE_COMMON, meta, RESEARCH_COMMON, SCHEMA, TASKS

### Community 157 - "test_agent_ingestion.py"
Cohesion: 0.30
Nodes (10): _enrolled(), _heartbeat(), Agent ingest pipeline: hello, heartbeat, staleness transitions, events., A container absent from a later heartbeat is gone from the daemon., A payload at the agent's cap may be truncated — absence proves nothing., test_heartbeat_at_container_cap_skips_reconciliation(), test_heartbeat_removes_vanished_containers(), test_heartbeat_updates_status_metrics_and_containers() (+2 more)

### Community 158 - "effective_permissions"
Cohesion: 0.67
Nodes (3): effective_permissions(), User, Sorted explicit permission codenames for a user; ``*`` expands to the registry.

### Community 159 - "8. Upstream binding and re-render triggers"
Cohesion: 0.33
Nodes (6): 8.1 Binding rules, 8.2 Certificate selection rule (this doc owns it), 8.3 Re-render triggers, 8.4 Drift, 8.5 How deployments hook routing (post-deploy route sync), 8. Upstream binding and re-render triggers

### Community 160 - "1. Current state"
Cohesion: 0.33
Nodes (6): 1.1 Storage and crypto, 1.2 Data model, 1.3 API surface (metadata-only reads), 1.5 SILENT DEGRADE BUG (must-fix), 1.6 Current-state gap list, 1. Current state

### Community 161 - "paginate"
Cohesion: 0.40
Nodes (5): paginate(), AsyncSession, Execute *stmt* with limit/offset and return ``(rows, total)``., list_projects(), Select

### Community 162 - "ApplicationBase"
Cohesion: 0.40
Nodes (4): ApplicationBase, Any, field_validator, Shared application fields; ``build_config`` is a free-form dict.

### Community 163 - "_FakeCtx"
Cohesion: 0.40
Nodes (3): _FakeCtx, Duck-typed stand-in for AuthContext., test_require_permission_returns_ctx_when_allowed()

### Community 164 - "AppError"
Cohesion: 0.67
Nodes (3): AppError, Exception, Base class for expected, client-facing errors.

### Community 165 - "agent_heartbeat"
Cohesion: 0.15
Nodes (16): agent_heartbeat(), agent_hello(), DbDep, post, Request, Response, Resolve ``X-Agent-Token`` to an enrolled server or raise 401., First contact after enrollment: persist static host facts, negotiate cadence. (+8 more)

### Community 166 - "pytest"
Cohesion: 0.40
Nodes (4): created_at server defaults must evaluate per insert, not at table creation., Regression: system_events and audit_logs shipped with DEFAULT 'now()' (quoted…, test_audit_and_event_created_at_defaults_are_dynamic(), pytest

### Community 167 - "4. ACME architecture"
Cohesion: 0.40
Nodes (5): 4.1 DNS-01 first (the default and the wedge), 4.2 DNSProvider interface, 4.3 ACME account and directory, 4.4 HTTP-01 via node nginx (later fallback), 4. ACME architecture

### Community 168 - "4. DNS ownership verification"
Cohesion: 0.40
Nodes (5): 4.1 The token, 4.2 The check (control-plane side), 4.3 Anti-takeover rules, 4.4 Sequence: add-domain → verified, 4. DNS ownership verification

## Knowledge Gaps
- **396 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+391 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1429 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AuthContext` connect `AuthContext` to `v1/auth.py`, `containers.py`, `docker_host_service.py`, `project_service.py`, `projects.py`, `incident_service.py`, `deployment_engine.py`, `list_containers`, `metrics_service.py`, `monitor_service.py`, `deps.py`, `auth_service.py`, `container_service.py`, `NotFound`, `PageParams`, `server_service.py`, `v1/channels.py`, `v1/deployments.py`, `test_permissions.py`, `servers.py`, `secret_service.py`, `publish`, `require_permission`, `middleware.py`, `NotificationChannel`, `Hub`, `events.py`, `test_deployments_simulated.py`, `scope_matches`, `resolve_auth`, `hub.py`, `notification_service.py`, `list_audit_logs`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Why does `README.md - NexusOps overview` connect `README.md - NexusOps overview` to `docs/engineering-report.md - build and verification report`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `APIModel` connect `APIModel` to `v1/auth.py`, `docker_host_service.py`, `projects.py`, `incident_service.py`, `list_containers`, `monitor_service.py`, `Node & Agent Architecture`, `ApplicationBase`, `PageParams`, `v1/search.py`, `v1/deployments.py`, `servers.py`, `test_schemas_server.py`, `users.py`, `test_schemas_agent.py`, `enums.py`, `events.py`, `roles.py`, `v1/health.py`, `notification_service.py`, `EnvironmentUpdate`, `monitor.py`?**
  _High betweenness centrality (0.031) - this node is a cross-community bridge._
- **Are the 73 inferred relationships involving `AuthContext` (e.g. with `list_audit_logs()` and `_optional_actor()`) actually correct?**
  _`AuthContext` has 73 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `apiGet()` (e.g. with `ContainerDetailPage.test.tsx` and `mockApi()`) actually correct?**
  _`apiGet()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `meta`, `SCHEMA`, `RESEARCH_COMMON` to the rest of the system?**
  _396 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ApiError` be split into smaller, more focused modules?**
  _Cohesion score 0.02635529608006672 - nodes in this community are weakly interconnected._