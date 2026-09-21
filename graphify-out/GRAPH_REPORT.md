# Graph Report - nexusops  (2026-09-21)

## Corpus Check
- 268 files · ~222,416 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: (none) 8, .example 1, .service 1)

## Summary
- 3572 nodes · 10486 edges · 172 communities (150 shown, 22 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 850 edges (avg confidence: 0.94)
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
- errors.py
- resolve_client_ip
- docker_hosts.py
- RunContext
- models/__init__.py
- AuthContext
- ServerDetailPage.tsx
- APIModel
- client.ts
- projects.py
- incidents.py
- deployment_engine.py
- SimulatedDockerProvider
- maintenance.py
- test_pagination.py
- docker_real.py
- containers.py
- get_latest_server_metrics
- get_settings
- Domain Routing — NexusOps
- monitor_service.py
- Node & Agent Architecture
- deps.py
- AuthContext.tsx
- nexusops_agent.py
- integration/conftest.py
- auth_service.py
- Container
- types.ts
- docker_host_service.py
- CheckResult
- monitors.py
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
- role_service.py
- test_schemas_server.py
- create_api_key
- publish
- test_schemas_agent.py
- monitor_transport.py
- rotate_secret
- collections_abc
- test_rate_limit.py
- test_auth_journey.py
- compilerOptions
- enums.py
- middleware.py
- api_key_service.py
- SimulatedDeploymentRunner
- notification_sender.py
- test_schema_redaction.py
- NotificationChannel
- Hub
- package.json
- list_events
- test_secrets.py
- README.md - NexusOps overview
- notification_service.py
- api service (FastAPI / uvicorn :8000)
- env.py
- list_alerts
- get_redis
- create_role
- ApiKeysPage.tsx
- scope_matches
- Settings
- AgentContainerIn
- v1/health.py
- container.py
- Product Roadmap — NexusOps Multi-Tenant Platform
- devDependencies
- redact_mapping
- config.py
- get_meta
- check_now
- Deployment Architecture — NexusOps (target state)
- test_notifications.py
- test_event_registry.py
- run_async
- pytest
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- journey.spec.ts
- ProjectDetailPage.test.tsx
- 2. Entities
- Secrets Architecture
- digest_of
- list_sessions
- tests/conftest.py
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- providers/base.py
- test_error_logging.py
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- _FakeAsyncClient
- .dispatch
- create_app
- log_service.py
- scripts
- ContainerListPage.test.tsx
- EnvironmentUpdate
- register_exception_handlers
- dependencies
- FakeWebSocket
- generate_secrets.sh
- StepFailure
- test_servers_and_audit.py
- router.py
- paginate
- DeploymentRunner
- OutModel
- .__tablename__
- install.sh
- docker-entrypoint.sh
- integration/__init__.py
- CLAUDE.md - project graphify rules
- Graphify query workflow (query / path / explain / update)
- frontend/index.html - SPA shell
- NexusOps Favicon — stylized letter 'N' lettermark in sky blue (#38bdf8) on a dark navy rounded square (#0b1120, 7px corner radius)
- nexusops-backend
- helpers.py
- simulation_tick
- postgres service (PostgreSQL 17, loopback :5433)
- get_sessionmaker
- nexusops-understand.mjs
- Invisible account lockout (5 fails -> 15 min, enumeration resistance)
- permissions.py
- instant_pacing
- nexusops-draft.mjs
- assert_error_code
- nexusops-challenge.mjs
- test_agent_ingestion.py
- collect_container_stats
- 8. Upstream binding and re-render triggers
- AgentClient
- validate_endpoint_url
- ApplicationBase
- .__init__
- configure_logging
- agent_heartbeat
- ._redact
- MonitorCreate
- _pace
- coerce_headers
- _order_clause
- 6. Config rendering — strict allowlists

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

## Communities (172 total, 22 thin omitted)

### Community 0 - "ApiError"
Cohesion: 0.03
Nodes (63): ApiError, DockerHostOut, SecretRow, SessionInfo, ME, mocks, Toast, TOAST_ARIA_LABEL (+55 more)

### Community 1 - "v1/auth.py"
Cohesion: 0.05
Nodes (76): get_current_user(), get_optional_user(), _load_permissions(), AsyncSession, DbSessionDep, Request, Standard authentication dependency. Also records client IP for logs/audit., Like :func:`get_current_user` but returns ``None`` for anonymous callers. (+68 more)

### Community 2 - "@tanstack/react-query"
Cohesion: 0.05
Nodes (59): AuditEntry, DeploymentOut, EnvironmentOut, Page, ProjectOut, AuditLogPage, ContainerListPage, DeploymentListPage (+51 more)

### Community 3 - "apiGet"
Cohesion: 0.08
Nodes (58): apiDelete(), apiGet(), apiPatch(), apiPost(), ApplicationOut, MonitorListPage, ProjectDetailPage, useAuth() (+50 more)

### Community 4 - "App.tsx"
Cohesion: 0.04
Nodes (57): DashboardSummary, DeploymentStepOut, IncidentEventOut, SearchResult, AlertsPage, App(), DashboardPage, DeploymentDetailPage (+49 more)

### Community 5 - "errors.py"
Cohesion: 0.08
Nodes (32): asyncio, AppError, Exception, Error taxonomy and the single place where API error envelopes are shaped. Every…, Base class for expected, client-facing errors., get_logger(), Structured logging via structlog. Every log record carries timestamp, level,…, UUID (+24 more)

### Community 6 - "resolve_client_ip"
Cohesion: 0.18
Nodes (21): _is_trusted(), _parse_networks(), Request, Client-IP resolution behind chained reverse proxies. The API never takes TCP…, Parse a comma-separated CIDR list; malformed entries are skipped., Real client address for *request* per the trust model above., resolve_client_ip(), make_request() (+13 more)

### Community 7 - "docker_hosts.py"
Cohesion: 0.09
Nodes (48): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+40 more)

### Community 8 - "RunContext"
Cohesion: 0.26
Nodes (8): LogLevel, _commit_short(), Deployment runner port plus a faithful simulated implementation.…, Everything a runner needs to execute one deployment., One streamed output line for a step., RunContext, _slug(), StepLine

### Community 9 - "models/__init__.py"
Cohesion: 0.08
Nodes (61): Base, big_serial_pk(), json_column(), datetime, UUID, Declarative base, shared mixins and column helpers., Base for all ORM models with stable constraint naming for Alembic., Identity PK for very high-volume tables (metrics, logs). (+53 more)

### Community 10 - "AuthContext"
Cohesion: 0.13
Nodes (48): AuthContext, Resolved identity attached to every authenticated request., NotFound, Application, Revoke a key owned by *owner_id*. Foreign keys look like NotFound (no leak)., revoke_api_key(), Any, AsyncSession (+40 more)

### Community 11 - "ServerDetailPage.tsx"
Cohesion: 0.07
Nodes (45): ContainerOut, MetricPoint, ServerDetail, ServerSummary, ServerDetailPage, ServerListPage, ChartSeries, LineChart() (+37 more)

### Community 12 - "APIModel"
Cohesion: 0.04
Nodes (47): ApiKeyCreateRequest, APIModel, BaseModel, Base for request/response models: ORM mode + strict-ish population., DeploymentApplicationRef, DeploymentCreate, DeploymentEnvironmentRef, Request body for triggering a deployment of an application. (+39 more)

### Community 13 - "client.ts"
Cohesion: 0.06
Nodes (43): API_BASE, apiRequest(), buildUrl(), extractError(), getAccessToken(), refreshToken(), RequestOptions, EventItem (+35 more)

### Community 14 - "projects.py"
Cohesion: 0.12
Nodes (45): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+37 more)

### Community 15 - "incidents.py"
Cohesion: 0.13
Nodes (33): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+25 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.07
Nodes (76): deployment_log_channel(), Deployment, DeploymentStep, DeploymentStatus, DeploymentTrigger, EventLevel, StepStatus, _after_commit_enqueue() (+68 more)

### Community 17 - "SimulatedDockerProvider"
Cohesion: 0.10
Nodes (29): DockerProviderError, A provider operation failed. ``str()`` is safe to show/log., Any, Plausible numbers derived from the row plus time-based sine noise., Implements :class:`DockerProvider` semantics against DB rows., _seed_int(), SimulatedDockerProvider, _log_entry() (+21 more)

### Community 18 - "maintenance.py"
Cohesion: 0.15
Nodes (23): _run(), _run(), aggregate_metrics(), _run(), _collect_logs(), expire_sessions(), _run(), task (+15 more)

### Community 19 - "test_pagination.py"
Cohesion: 0.13
Nodes (25): Cursor, cursor_params(), CursorPage, CursorParams, decode_cursor(), encode_cursor(), BaseModel, datetime (+17 more)

### Community 20 - "docker_real.py"
Cohesion: 0.14
Nodes (21): ContainerStats, Point-in-time resource usage snapshot., _as_float(), _compute_stats(), _cpu_percent(), _network_bytes(), parse_log_line(), parse_rfc3339() (+13 more)

### Community 21 - "containers.py"
Cohesion: 0.08
Nodes (51): _action_route(), _endpoint(), _container_out(), _decode_frame(), _ev(), get_container(), _like_pattern(), list_container_logs() (+43 more)

### Community 22 - "get_latest_server_metrics"
Cohesion: 0.08
Nodes (34): get_dashboard_summary(), get_latest_server_metrics(), get_server_metrics(), CurrentUser, DbDep, Depends, get, UUID (+26 more)

### Community 23 - "get_settings"
Cohesion: 0.10
Nodes (39): argon2, argon2_exceptions, get_settings(), Return the cached settings singleton., Unauthorized, create_access_token(), decode_access_token(), generate_api_key() (+31 more)

### Community 24 - "Domain Routing — NexusOps"
Cohesion: 0.10
Nodes (20): 10. Wildcards and catch-all, 11. User journey, 12. API surface, permissions, audit, 13. Monitoring tie-in, 1. Scope and current state, 2. Where nginx runs, 3.1 Domain, 3.2 Route (+12 more)

### Community 25 - "monitor_service.py"
Cohesion: 0.16
Nodes (36): update_monitor(), MonitorStatus, Monitor, MonitorCheck, _active_incident(), _audit(), claim_due_monitors(), create_monitor() (+28 more)

### Community 26 - "Node & Agent Architecture"
Cohesion: 0.11
Nodes (19): 1. Scope and stance, 2.1 Current shape (real), 2.2 Changes for the target model, 2.3 Capabilities (target), 2.4 DockerEndpoint — the 0..1 relation, 2. The Node concept, 6.1 Token scope, 6.2 docker.sock is root-equivalent (+11 more)

### Community 27 - "deps.py"
Cohesion: 0.12
Nodes (34): permission_dep(), Any, FastAPI dependencies: database session, authentication context, RBAC gate.…, Dependency factory enforcing a permission; returns 403 when denied., require_permission(), _check(), Alert inbox endpoints. Authenticated users see the shared operator feed., API key routes — self-service management of the caller's own machine… (+26 more)

### Community 28 - "AuthContext.tsx"
Cohesion: 0.07
Nodes (28): setAccessToken(), Role, User, AuthContext, AuthProvider(), AuthState, MeResponse, permissionMatches() (+20 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.13
Nodes (20): build_heartbeat(), cpu_percent_since(), disk_stats(), load1(), main(), memory_stats(), memory_total_mb(), os_info() (+12 more)

### Community 30 - "integration/conftest.py"
Cohesion: 0.14
Nodes (20): alembic_config, close_redis(), lifespan(), Start the WS hub + notification dispatcher; tear them down cleanly., _clean_slate(), client(), _ensure_database(), _migrated_database() (+12 more)

### Community 31 - "auth_service.py"
Cohesion: 0.07
Nodes (71): Forbidden, hash_password(), ActorType, AuditResult, UserStatus, _audit(), change_own_password(), count_users() (+63 more)

### Community 32 - "Container"
Cohesion: 0.08
Nodes (33): ContainerHealth, ContainerStatus, Container, Observed container state mirrored from an agent or docker provider., LogEntry, is_simulated(), True when *provider* is the simulated implementation., Simulated docker provider for demo and test environments. The provider is… (+25 more)

### Community 33 - "types.ts"
Cohesion: 0.07
Nodes (31): AlertOut, ChannelOut, CheckOut, CursorPage, DeliveryOut, DeploymentLogLine, DeploymentStatus, IncidentOut (+23 more)

### Community 34 - "docker_host_service.py"
Cohesion: 0.14
Nodes (33): DockerHostStatus, DockerHost, provider_for(), Return the provider matching *host*'s endpoint configuration., _assert_endpoint_allowed(), _assert_name_free(), create_host(), delete_host() (+25 more)

### Community 35 - "CheckResult"
Cohesion: 0.22
Nodes (13): CheckResult, HTTPMonitorTransport, Real HTTP(S) probe using httpx with per-monitor settings. Redirects are…, _FakeResponse, MonkeyPatch, A 302 from a public URL into link-local/metadata space must be refused., Defense in depth: even the httpx client must never auto-follow., _script_client() (+5 more)

### Community 36 - "monitors.py"
Cohesion: 0.21
Nodes (19): create_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), DbDep, Depends, get (+11 more)

### Community 37 - "v1/search.py"
Cohesion: 0.09
Nodes (41): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+33 more)

### Community 38 - "server_service.py"
Cohesion: 0.07
Nodes (59): agent_hello(), Agent ingest endpoints: enrollment handshake and periodic heartbeats.…, First contact after enrollment: persist static host facts, negotiate cadence., Canonical Redis pub/sub channel names shared by API, workers and WS hub., server_metrics_channel(), generate_agent_token(), generate_refresh_token(), hash_token() (+51 more)

### Community 39 - "v1/channels.py"
Cohesion: 0.11
Nodes (36): create_channel(), delete_channel(), get_channel(), list_channels(), list_deliveries(), DbDep, delete, Depends (+28 more)

### Community 40 - "DockerProvider"
Cohesion: 0.09
Nodes (12): DockerProvider, Any, datetime, Protocol, List containers visible to the provider., Inspect a single container by id (short ids allowed)., List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``., List volumes: keys ``name``, ``driver``, ``mountpoint``. (+4 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.20
Nodes (21): Deterministic fake checker for ``sim://`` monitors and demo environments.…, SimulatedTransport, _check(), clock(), FakeClock, _monitor(), Any, fixture (+13 more)

### Community 42 - "test_agent_contract.py"
Cohesion: 0.18
Nodes (16): agent_fixture(), _load_agent(), _patch_stats(), Any, fixture, MonkeyPatch, Contract tests: the shipped agent's payloads must satisfy the ingest schemas.…, One-shot docker stats reduce to cpu/mem/limit fields the schema accepts, with… (+8 more)

### Community 43 - "v1/deployments.py"
Cohesion: 0.10
Nodes (43): _attribute_step_idx(), cancel_deployment(), _emails_for(), get_deployment(), list_application_deployments(), list_deployment_logs(), _list_deployments(), _parse_sort() (+35 more)

### Community 44 - "RealDockerProvider"
Cohesion: 0.14
Nodes (7): ContainerInfo, Normalized view of a container as reported by any provider., T, Execute an SDK call with one short retry, normalizing failures., Two short samples give real cpu/net deltas without streaming., Talks to a real docker daemon over ``unix://`` or ``tcp://``., RealDockerProvider

### Community 45 - "test_permissions.py"
Cohesion: 0.14
Nodes (11): _auth_context(), _FakeCtx, Unit tests for the permission registry, scope matching and RBAC gate., Duck-typed stand-in for AuthContext., test_api_key_scope_intersects_role_permissions(), test_plain_user_without_permissions_is_denied(), test_require_permission_raises_forbidden_when_denied(), test_require_permission_returns_ctx_when_allowed() (+3 more)

### Community 46 - "form.tsx"
Cohesion: 0.10
Nodes (17): LoginPage, CheckboxField(), CheckboxFieldProps, FieldAria, FieldBaseProps, PasswordField(), PasswordFieldProps, SearchInputProps (+9 more)

### Community 47 - "servers.py"
Cohesion: 0.08
Nodes (45): create_server(), delete_server(), _detail(), get_server(), list_tags(), AsyncSession, DbDep, delete (+37 more)

### Community 48 - "test_ssrf.py"
Cohesion: 0.07
Nodes (61): BadRequest, UnprocessableEntity, assert_safe_tcp_endpoint(), assert_safe_url(), _is_forbidden_address(), is_simulation_url(), _raise_block(), SSRF guard applied to every operator-supplied outbound URL. Monitors and… (+53 more)

### Community 49 - "secret_service.py"
Cohesion: 0.14
Nodes (29): encrypt_str(), _actor_type(), _collect_refs(), create_secret(), delete_secret(), _detail(), get_secret(), get_secret_detail() (+21 more)

### Community 50 - "role_service.py"
Cohesion: 0.20
Nodes (20): Conflict, create_role(), delete_role(), get_role(), list_roles(), AsyncSession, Request, Role (+12 more)

### Community 51 - "test_schemas_server.py"
Cohesion: 0.21
Nodes (22): Payload for registering a server., Partial update. ``tags`` replaces the full set when provided., ServerCreate, ServerUpdate, _base(), parametrize, Unit tests for app.schemas.server (validation only, no I/O)., test_empty_ip_is_allowed_but_whitespace_collapses() (+14 more)

### Community 52 - "create_api_key"
Cohesion: 0.16
Nodes (17): create_api_key(), list_api_keys(), CurrentUser, DbSessionDep, delete, get, post, Request (+9 more)

### Community 53 - "publish"
Cohesion: 0.20
Nodes (17): SystemEvent, Destructive removal requiring exact-name confirmation. Deletes via the provider…, remove_container(), _after_commit_publish(), _after_rollback_drop(), event_frame_from_row(), publish(), _publish_after_commit() (+9 more)

### Community 54 - "test_schemas_agent.py"
Cohesion: 0.21
Nodes (16): AgentHeartbeatIn, AgentHelloIn, First contact from an agent after enrollment; fills static host facts., Periodic metrics + observed containers from an enrolled agent., _heartbeat(), Unit tests for agent-facing schemas (heartbeat + container payloads)., test_agent_hello_bounds(), test_agent_hello_minimal() (+8 more)

### Community 55 - "monitor_transport.py"
Cohesion: 0.10
Nodes (21): assert_safe_url_async(), Async wrapper around :func:`assert_safe_url`; DNS runs off the loop., CheckOutcome, _decode(), get_transport(), MonitorTransport, BaseException, Protocol (+13 more)

### Community 56 - "rotate_secret"
Cohesion: 0.16
Nodes (21): create_secret(), delete_secret(), get_secret(), list_secrets(), DbSession, delete, Depends, get (+13 more)

### Community 57 - "collections_abc"
Cohesion: 0.12
Nodes (3): alembic, collections_abc, sqlalchemy_dialects

### Community 58 - "test_rate_limit.py"
Cohesion: 0.18
Nodes (17): RateLimited, _memory_count_and_ttl(), rate_limit(), _dependency(), Fixed-window counter backed by process memory. Returns (count, ttl)., Return a dependency enforcing *limit* requests per window per IP. With…, _clean_memory_windows(), _FakeRequest (+9 more)

### Community 59 - "test_auth_journey.py"
Cohesion: 0.16
Nodes (18): cookie_attributes(), Response, The raw Set-Cookie header carrying the refresh token., Extract just the opaque token from a Set-Cookie header., Parse Set-Cookie attributes (lowercased keys, empty string for flags)., refresh_cookie_header(), refresh_cookie_value(), _cookie_name() (+10 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "enums.py"
Cohesion: 0.12
Nodes (37): CredentialKind, IncidentEventKind, IncidentSeverity, IncidentStatus, MetricGranularity, Closed registries of domain enumerations. Member names equal their values…, String enum; member names equal values so name/value storage never disagrees., StrEnum (+29 more)

### Community 62 - "middleware.py"
Cohesion: 0.16
Nodes (12): ASGIApp, AccessLogMiddleware, HTTP middleware: request ids, security headers, structured access logs., Baseline hardening headers on every API response., RequestIDMiddleware, SecurityHeadersMiddleware, BaseHTTPMiddleware, starlette_middleware_base (+4 more)

### Community 63 - "api_key_service.py"
Cohesion: 0.11
Nodes (28): AlertSeverity, Alert, create_alert(), get_alert(), mark_all_read(), mark_read(), AsyncSession, UUID (+20 more)

### Community 64 - "SimulatedDeploymentRunner"
Cohesion: 0.31
Nodes (19): Staged docker-style simulation used by v1 deployments., Canonical step identifiers stored on :class:`DeploymentStep` rows., SimulatedDeploymentRunner, StepName, _collect(), _ctx(), Unit tests for SimulatedDeploymentRunner (async generators, no broker)., test_broken_version_does_not_affect_other_steps() (+11 more)

### Community 65 - "notification_sender.py"
Cohesion: 0.15
Nodes (18): NotificationError, Any, BaseException, Exception, Low-level notification transports: SMTP email and outgoing webhooks. These…, POST *payload* as JSON to *url*; 2xx is success, anything else raises. Response…, Raised when a delivery attempt fails. Message is safe to persist., Bounded, single-line, content-free error reason. (+10 more)

### Community 66 - "test_schema_redaction.py"
Cohesion: 0.18
Nodes (17): is_sensitive_header(), mask_sensitive_headers(), True when *name* looks like it carries a credential (Authorization etc.)., Return a copy of *headers* with sensitive values replaced by a mask., mask_target(), Human-readable masked target safe to expose over the API. For webhook families…, _monitor_out(), Outbound-schema redaction: monitor probe credentials and webhook targets.… (+9 more)

### Community 67 - "NotificationChannel"
Cohesion: 0.20
Nodes (20): NotificationChannel, A delivery target (email address / webhook endpoint). ``config_ciphertext``…, EmailConfig, WebhookConfig, _audit(), create_channel(), decrypt_channel_config(), delete_channel() (+12 more)

### Community 68 - "Hub"
Cohesion: 0.10
Nodes (24): _close_socket(), Connection, _entity_exists(), Hub, _is_same_origin(), _params_key(), _parse_payload(), Any (+16 more)

### Community 69 - "package.json"
Cohesion: 0.13
Nodes (15): name, private, type, version, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom (+7 more)

### Community 70 - "list_events"
Cohesion: 0.22
Nodes (13): _decode_cursor(), _encode_cursor(), list_event_types(), list_events(), datetime, DbSession, Depends, get (+5 more)

### Community 71 - "test_secrets.py"
Cohesion: 0.20
Nodes (13): decrypt_str(), _fernet(), _create(), Secrets: metadata-only reads, rotation versioning, deploy-time resolution., test_create_and_list_return_metadata_only(), test_delete_removes_metadata_row(), test_detail_endpoint_never_carries_the_value(), test_rotate_bumps_version_changes_digest_and_ciphertext() (+5 more)

### Community 72 - "README.md - NexusOps overview"
Cohesion: 0.09
Nodes (43): docker-compose.dev.yml - dev overlay, docker-compose.docker-sock.yml - docker socket override, docker-compose.yml - full stack definition, docs/agent.md - agent guide, docs/api.md - API guide, Append-only audit log (Postgres BEFORE UPDATE OR DELETE trigger), docs/architecture.md - system architecture, docs/deployment.md - deployment and operations guide (+35 more)

### Community 73 - "notification_service.py"
Cohesion: 0.18
Nodes (21): _as_uuid(), decode_delivery_cursor(), dispatch_event_frame(), _send(), dispatcher_loop(), encode_delivery_cursor(), list_deliveries(), _now() (+13 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "env.py"
Cohesion: 0.27
Nodes (9): _database_url(), Alembic environment: metadata comes from app.models, URL from app settings., Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online(), Return a psycopg3-compatible URL usable by Alembic/Celery sync paths., sync_database_url() (+1 more)

### Community 76 - "list_alerts"
Cohesion: 0.21
Nodes (14): list_alerts(), mark_all_read(), mark_read(), CurrentUser, DbDep, Depends, get, post (+6 more)

### Community 77 - "get_redis"
Cohesion: 0.22
Nodes (12): Redis-backed fixed-window rate limiting as a FastAPI dependency factory. Auth-…, get_redis(), ping(), Shared async Redis client., _next_data_message(), Event bus fan-out ordering: a frame follows its transaction, never leads it.…, Regression: a rollback must drop stashed frames, not defer them. The stash…, test_frame_published_only_after_commit() (+4 more)

### Community 78 - "create_role"
Cohesion: 0.13
Nodes (22): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, delete, get (+14 more)

### Community 79 - "ApiKeysPage.tsx"
Cohesion: 0.13
Nodes (15): ApiKeyOut, ApiKeysPage, ApiKeyCreatedOut, handleCopyKey(), copyText(), describeError(), EMPTY_FORM, GROUP_STYLE (+7 more)

### Community 80 - "scope_matches"
Cohesion: 0.14
Nodes (14): Check an API-key scope list against a required permission. Supports exact match…, scope_matches(), parametrize, test_scope_matches_truth_table(), 1. Principles (already true in the codebase, kept), 2. Registry changes (Phase 1 + new subsystems), 3. The five system roles (target), 4. Grants (resource-level access; design now, later phase) (+6 more)

### Community 81 - "Settings"
Cohesion: 0.16
Nodes (5): field_validator, model_validator, Validated application settings (loaded from environment / .env)., Settings, BaseSettings

### Community 82 - "AgentContainerIn"
Cohesion: 0.26
Nodes (12): AgentContainerIn, field_validator, Observed container state reported by an agent., _container(), parametrize, test_allowed_container_statuses(), test_bogus_status_string_rejected(), test_container_id_pattern_accepts() (+4 more)

### Community 83 - "v1/health.py"
Cohesion: 0.20
Nodes (13): liveness(), get, Response, Health probes: liveness (always cheap) and readiness (checks dependencies).…, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness(), HealthOut (+5 more)

### Community 84 - "container.py"
Cohesion: 0.21
Nodes (12): ContainerRemoveOut, host_ref(), HostRef, LogEntryOut, UUID, Container schemas: list/detail read models, log entries, action results., Summary of the docker host a container runs on., Summary of the server associated with a container. (+4 more)

### Community 85 - "Product Roadmap — NexusOps Multi-Tenant Platform"
Cohesion: 0.13
Nodes (15): 0. Stance, 10. Phase 7 — Teams, grants & custom roles, 11. Phase 8 — Backups, 12. Phase 9 — Billing & metering, 14. Biggest risks (short form), 15. Reading order, 2. Phase plan, 3. Phase 0 — Truth pass & hardening (+7 more)

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "redact_mapping"
Cohesion: 0.22
Nodes (13): _is_sensitive_key(), Substring match on a normalised key so header-style names are caught too.…, Return a copy of *data* with sensitive values replaced. Used by audit metadata…, redact_mapping(), parametrize, Unit tests for app.core.logging redaction (pure functions only)., test_case_insensitive_substring_match(), test_flat_sensitive_keys_redacted() (+5 more)

### Community 88 - "config.py"
Cohesion: 0.18
Nodes (9): fail_on_bad_config(), Central configuration. All runtime configuration flows through this module so…, Exit immediately with a readable message if configuration is invalid., Celery application: periodic cadences live here, dynamic work is claimed…, celery, celery_schedules, cryptography_fernet, functools (+1 more)

### Community 89 - "get_meta"
Cohesion: 0.40
Nodes (5): get_meta(), DbSessionDep, get, Public metadata; identity fields appear only for valid credentials., OptionalUser

### Community 90 - "check_now"
Cohesion: 0.29
Nodes (10): check_now(), delete_monitor(), pause_monitor(), delete, ManageCtx, post, Request, Response (+2 more)

### Community 91 - "Deployment Architecture — NexusOps (target state)"
Cohesion: 0.13
Nodes (15): 10. Events and WS during runs, 11. Post-deploy hooks, 12. Rollback semantics (existing behavior kept), 13. The simulated runner stays — labeled, 14. Open questions, 1.1 The honest defect list, 1. Current state — what is real and what is simulated, 3. Target pipeline (+7 more)

### Community 92 - "test_notifications.py"
Cohesion: 0.36
Nodes (9): NotificationDelivery, _channel(), _delivery(), UUID, Notification channel + delivery-log endpoints. Regression coverage for GET…, The same event frame consumed twice queues ONE delivery per channel. Every API…, test_dispatch_frame_is_idempotent_across_workers(), test_list_deliveries_filters_by_channel() (+1 more)

### Community 93 - "test_event_registry.py"
Cohesion: 0.21
Nodes (8): event_type_catalogue(), is_known_event_type(), Canonical registry of system-event types. Single source of truth shared by…, Return True when *event_type* is part of the canonical registry., Serialise the registry for the ``/events/types`` endpoint., Registry coherence: schema-advertised event types must equal the canonical…, test_catalogue_serialises_every_entry(), test_known_event_lookup()

### Community 94 - "run_async"
Cohesion: 0.16
Nodes (18): task, Flag silent servers OFFLINE, recover returning ones. Safe to overlap., sweep_servers(), task, Claim up to CLAIM_BATCH due monitors and execute each check.…, run_due_monitors(), Any, T (+10 more)

### Community 95 - "pytest"
Cohesion: 0.19
Nodes (11): created_at server defaults must evaluate per insert, not at table creation., Regression: system_events and audit_logs shipped with DEFAULT 'now()' (quoted…, test_audit_and_event_created_at_defaults_are_dynamic(), _create_monitor(), Monitor checks driving the full down -> incident -> recovery lifecycle., Regression: probe headers and URL query credentials never leave the API. Probe…, test_check_now_endpoint_runs_immediately(), test_down_then_recover_lifecycle() (+3 more)

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
Cohesion: 0.15
Nodes (13): 0. Design stance, 1. The hierarchy, 2.1.1 ApiKey org binding detail, 2.2.1 Environment promotion detail, 2.2 Delivery (existing models, extended), 2.3 Infrastructure — Nodes, 2.4 Routing & TLS (new subsystem), 2.5 Secrets (existing, re-scoped) (+5 more)

### Community 101 - "Secrets Architecture"
Cohesion: 0.11
Nodes (19): 10. Resolution flow at deploy time, 1.1 Storage and crypto, 1.2 Data model, 1.3 API surface (metadata-only reads), 1.5 SILENT DEGRADE BUG (must-fix), 1.6 Current-state gap list, 1. Current state, 2.1 Resolution runs inside org scope (+11 more)

### Community 102 - "digest_of"
Cohesion: 0.10
Nodes (21): digest_of(), Short server-verifiable digest used for change detection display. HMAC-SHA256…, test_digest_is_keyed_not_plain_sha256(), test_digest_length_and_determinism(), 10. Status/expiry tracking and monitor tie-in, 12. Audit and events, 13. Non-goals, 2. Certificate entity (+13 more)

### Community 103 - "list_sessions"
Cohesion: 0.19
Nodes (12): list_sessions(), CurrentUser, DbSessionDep, delete, get, Request, UUID, Active sessions. Defaults to the caller's own; ``all``/``user_id`` need… (+4 more)

### Community 104 - "tests/conftest.py"
Cohesion: 0.22
Nodes (8): configure_test_env(), Test bootstrap: pin every cached setting BEFORE the first ``app`` import. The…, KEY=VALUE pairs from the repo .env (first definition wins); never logged., Export the exact settings the app caches; host values cannot leak through., _read_dot_env(), os, pathlib, sys

### Community 105 - "redis service (Redis 7, no persistence, loopback :6390)"
Cohesion: 0.22
Nodes (11): redis service (Redis 7, no persistence, loopback :6390), WebSocket API (/api/v1/ws handshake, frames, limits), WebSocket channels (global, server-metrics, container-logs, deployment-logs, incidents), Deployment engine (queue_deployment / execute_deployment / sweeper backstop), Real-time spine: PostgreSQL system_events + Redis pub/sub, Rollback as a new deployment (rollback_of_id), WebSocket hub (framework-thin, Redis fan-in, per-socket queues), Test suites (pytest unit+integration, vitest, Playwright e2e) (+3 more)

### Community 106 - "NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)"
Cohesion: 0.18
Nodes (12): Agent security model (one-way telemetry, no command channel), Agent enrollment token (X-Agent-Token, nxa_..., SHA-256 at rest), Agent heartbeat exponential backoff (cap 5 min, exit 1 on revoked token), agent/install.sh (enrollment installer), Agent metrics collection (/proc statvfs Docker socket), NexusOps agent (stdlib-only Python, agent/nexusops_agent.py), Agent systemd hardening (ProtectSystem=strict, NoNewPrivileges), Agent ingest API (POST /agent/hello, POST /agent/heartbeat) (+4 more)

### Community 107 - "providers/base.py"
Cohesion: 0.15
Nodes (14): clip(), Exception, Provider abstraction for docker hosts (real daemon or simulated). Providers are…, Build a compact, secret-free description of a provider failure. Only the…, Truncate *text* to *limit* characters, stripping control chars., sanitize_error(), describe_provider_error(), Exception (+6 more)

### Community 108 - "test_error_logging.py"
Cohesion: 0.22
Nodes (4): Regression: the catch-all 500 handler must not log raw exception text.…, _SpyLogger, test_unhandled_exception_handler_logs_class_not_message(), fastapi_testclient

### Community 109 - "Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)"
Cohesion: 0.25
Nodes (9): API keys (X-API-Key, nxo_..., scope intersection), First boot sequence (api entrypoint migrates, compose never seeds), Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test), Makefile workflows (up/test/lint/typecheck/migrate/seed), HIGH finding: API-key scope bypass for superadmin-owned keys (fixed: scope intersection first), Security audit 2026-09 (26 raw findings -> 20 confirmed, all fixed), HIGH finding: known seed superadmin + API key backdoor (fixed: NEXUSOPS_ALLOW_SEED opt-in, one-time password), Threat model (edge attacker, malicious agent, curious operator, leaked token, SSRF) (+1 more)

### Community 110 - "_FakeAsyncClient"
Cohesion: 0.22
Nodes (3): _FakeAsyncClient, _FakeRequestObj, Scripted httpx.AsyncClient: responses keyed by absolute request URL.

### Community 111 - ".dispatch"
Cohesion: 0.39
Nodes (4): UUID, Request, Response, RequestResponseEndpoint

### Community 112 - "create_app"
Cohesion: 0.25
Nodes (12): create_app(), _include_routers(), FastAPI, Mount every domain router. Router variables follow the module contract., _app_for_environment(), MonkeyPatch, ENVIRONMENT gating contract: docs exposure and HSTS (see .env.example).…, create_app() with get_settings() patched to the given environment. (+4 more)

### Community 113 - "log_service.py"
Cohesion: 0.13
Nodes (24): container_log_channel(), LogSource, LogLine, One parsed log record from a container log stream., datetime, Replay registered LogEntry rows ordered by ts (tail N). ``follow`` is ignored…, append_lines(), count_container_logs() (+16 more)

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "ContainerListPage.test.tsx"
Cohesion: 0.29
Nodes (3): ApiError, server, serversPage

### Community 116 - "EnvironmentUpdate"
Cohesion: 0.29
Nodes (7): EnvironmentBase, EnvironmentUpdate, field_validator, Shared environment fields., Partial environment update; omitted fields are left untouched., 1.4 Deploy-time resolution today, 8. Environment config vs secrets boundary

### Community 117 - "register_exception_handlers"
Cohesion: 0.36
Nodes (8): _error_payload(), FastAPI, Request, register_exception_handlers(), handle_app_error(), handle_http_exception(), handle_unexpected(), handle_validation_error()

### Community 118 - "dependencies"
Cohesion: 0.33
Nodes (6): dependencies, lucide-react, react, react-dom, react-router-dom, @tanstack/react-query

### Community 120 - "generate_secrets.sh"
Cohesion: 0.47
Nodes (3): existing_real_keys(), replace_or_append(), generate_secrets.sh script

### Community 121 - "StepFailure"
Cohesion: 0.25
Nodes (7): Exception, Raised by a runner when a step fails irrecoverably., StepFailure, 5.1 Operation whitelist additions (deployments), 5.2 `RunContext` extension, 5. `AgentDeploymentRunner` — real execution over agent operations, 9. Cancellation and per-step timeouts

### Community 122 - "test_servers_and_audit.py"
Cohesion: 0.27
Nodes (12): A valid POST /servers body with per-test overrides., server_payload(), _create_server(), Server CRUD, cascade delete, audit trail rows and audit immutability., The HTTP listing path — schema serialization is exercised end-to-end. A…, test_agent_token_rotation_invalidates_previous(), test_audit_log_api_serializes_and_filters(), test_audit_log_is_append_only() (+4 more)

### Community 123 - "router.py"
Cohesion: 0.40
Nodes (4): websocket, WebSocket endpoint. Mounted by the app factory under ``/api/v1``., Hand the socket to the hub (auth handshake handled there)., websocket_endpoint()

### Community 124 - "paginate"
Cohesion: 0.12
Nodes (16): list_audit_logs(), datetime, DbSession, Depends, get, PageParamsDep, Newest-first audit trail with optional filters. No write routes exist for this…, list_servers() (+8 more)

### Community 125 - "DeploymentRunner"
Cohesion: 0.25
Nodes (6): DeploymentRunner, Protocol, Adapter interface implemented by real (future) and simulated runners., Return the ordered step names for this run., Stream output lines for *step_name*; raise StepFailure to fail it., 2. What survives unchanged

### Community 126 - "OutModel"
Cohesion: 0.09
Nodes (33): Agent-facing schemas. Payloads are data only — never executed., AlertOut, Schemas for operator-facing alerts., API key schemas. Raw keys appear exactly once, at creation., ApplicationSummary, Application API schemas., Application as embedded in project outputs (no deployment summary)., AuditOut (+25 more)

### Community 146 - "helpers.py"
Cohesion: 0.18
Nodes (16): error_of(), login_account(), login_headers(), Any, AsyncClient, Pure helpers for journey tests: payloads, auth shortcuts, cookie parsing., Bootstrap owner account + session; returns ``(credentials, login_result)``., Unwrap an API error envelope. (+8 more)

### Community 147 - "simulation_tick"
Cohesion: 0.33
Nodes (7): _containers_for(), task, Deterministic smooth value in [base-amplitude, base+amplitude]., Stable per-server container set; one container cycles EXITED occasionally., simulation_tick(), _run(), _wave()

### Community 148 - "postgres service (PostgreSQL 17, loopback :5433)"
Cohesion: 0.29
Nodes (7): postgres service (PostgreSQL 17, loopback :5433), Fernet encryption at rest (ENCRYPTION_KEY, write-once), Backups (pgdata volume, nightly pg_dump, ephemeral Redis), Required secrets (POSTGRES_PASSWORD, JWT_SECRET >= 32 chars, ENCRYPTION_KEY Fernet), Production hardening checklist (secrets, ENVIRONMENT, no seed, TLS, rotation), Compose vs host network namespaces (postgres:5432 vs 127.0.0.1:5433), Simulation mode (SIMULATION_MODE)

### Community 149 - "get_sessionmaker"
Cohesion: 0.19
Nodes (12): async_sessionmaker, AsyncEngine, dispose_engine(), get_engine(), get_sessionmaker(), AsyncSession, The docker-host maintenance sweep must actually reach real hosts., Regression: the sweep called asyncio.run() inside its own running loop, so… (+4 more)

### Community 150 - "nexusops-understand.mjs"
Cohesion: 0.33
Nodes (5): COMMON, meta, out, READERS, SCHEMA

### Community 151 - "Invisible account lockout (5 fails -> 15 min, enumeration resistance)"
Cohesion: 0.33
Nodes (6): Invisible account lockout (5 fails -> 15 min, enumeration resistance), Unified error envelope (code, message, request_id), Per-IP rate limiting (Redis fixed window), Request lifecycle (edge -> middleware -> rate limit -> deps -> router), Client IP resolution (resolve_client_ip, TRUSTED_PROXY_CIDRS, XFF overwrite), EmailStr rejects reserved domains (login 422 on .test/.local/.arpa)

### Community 152 - "permissions.py"
Cohesion: 0.29
Nodes (5): permission_exists(), PermissionSpec, Permission registry and role matrix. Permissions are *data*: the registry below…, test_permission_exists_helper(), fnmatch

### Community 153 - "instant_pacing"
Cohesion: 0.40
Nodes (4): instant_pacing(), fixture, MonkeyPatch, Remove the per-line sleeps; pacing bounds are asserted separately.

### Community 154 - "nexusops-draft.mjs"
Cohesion: 0.40
Nodes (4): DOCS, meta, SPINE, VERIFY_RULES

### Community 155 - "assert_error_code"
Cohesion: 0.15
Nodes (19): assert_error_code(), bearer(), Assert envelope shape + code; returns the inner error object., A fresh, deliverable-shaped address unique to a single test. ``example.com`` is…, unique_email(), Regression: lockout must not leak which emails exist. After login_max_attempts…, Sessions must carry the real client address, not the proxy hop's peer. Behind…, Client-injected leftmost XFF entries must not poison the session IP. (+11 more)

### Community 156 - "nexusops-challenge.mjs"
Cohesion: 0.33
Nodes (5): CHALLENGE_COMMON, meta, RESEARCH_COMMON, SCHEMA, TASKS

### Community 157 - "test_agent_ingestion.py"
Cohesion: 0.30
Nodes (10): _enrolled(), _heartbeat(), Agent ingest pipeline: hello, heartbeat, staleness transitions, events., A container absent from a later heartbeat is gone from the daemon., A payload at the agent's cap may be truncated — absence proves nothing., test_heartbeat_at_container_cap_skips_reconciliation(), test_heartbeat_removes_vanished_containers(), test_heartbeat_updates_status_metrics_and_containers() (+2 more)

### Community 158 - "collect_container_stats"
Cohesion: 0.29
Nodes (6): collect_container_stats(), collect_containers(), _docker_request(), Best-effort container list; empty when no docker socket is present., One-shot docker stats for running containers, CPU diffed across cycles.…, _UnixHTTPConnection

### Community 159 - "8. Upstream binding and re-render triggers"
Cohesion: 0.33
Nodes (6): 8.1 Binding rules, 8.2 Certificate selection rule (this doc owns it), 8.3 Re-render triggers, 8.4 Drift, 8.5 How deployments hook routing (post-deploy route sync), 8. Upstream binding and re-render triggers

### Community 161 - "validate_endpoint_url"
Cohesion: 0.50
Nodes (3): model_validator, Validate/normalize an endpoint URL against the scheme allowlist., validate_endpoint_url()

### Community 162 - "ApplicationBase"
Cohesion: 0.40
Nodes (4): ApplicationBase, Any, field_validator, Shared application fields; ``build_config`` is a free-form dict.

### Community 164 - "configure_logging"
Cohesion: 0.50
Nodes (4): configure_logging(), _orjson_dumps(), Any, Configure structlog + stdlib logging once at process start. Everything…

### Community 165 - "agent_heartbeat"
Cohesion: 0.15
Nodes (14): agent_heartbeat(), DbDep, post, Request, Response, Resolve ``X-Agent-Token`` to an enrolled server or raise 401., Ingest one metrics sample + observed containers. Returns 204 when applied., require_server() (+6 more)

### Community 166 - "._redact"
Cohesion: 0.50
Nodes (3): field_serializer, Mask any userinfo credentials before the URL leaves the API., redact_endpoint_url()

### Community 167 - "MonitorCreate"
Cohesion: 0.50
Nodes (4): MonitorBase, MonitorCreate, Shared validation bounds for monitor configuration., Payload for POST /monitors.

### Community 168 - "_pace"
Cohesion: 0.67
Nodes (3): _pace(), Deterministic per-line delay between 0.05s and 0.35s., test_pace_bounds()

### Community 169 - "coerce_headers"
Cohesion: 0.67
Nodes (3): coerce_headers(), Any, Normalise arbitrary JSON-ish header input into a plain str->str dict.

### Community 170 - "_order_clause"
Cohesion: 0.67
Nodes (3): _order_clause(), ColumnElement, Translate ``name`` / ``-created_at`` style sort keys to ORDER BY.

### Community 171 - "6. Config rendering — strict allowlists"
Cohesion: 0.67
Nodes (3): 6.1 What is rendered, 6.2 The allowlist (the injection defense), 6. Config rendering — strict allowlists

## Knowledge Gaps
- **397 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+392 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1430 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AuthContext` connect `AuthContext` to `v1/auth.py`, `errors.py`, `docker_hosts.py`, `projects.py`, `incidents.py`, `deployment_engine.py`, `containers.py`, `get_latest_server_metrics`, `monitor_service.py`, `deps.py`, `auth_service.py`, `Container`, `docker_host_service.py`, `monitors.py`, `server_service.py`, `v1/channels.py`, `v1/deployments.py`, `test_permissions.py`, `servers.py`, `secret_service.py`, `role_service.py`, `publish`, `rotate_secret`, `enums.py`, `api_key_service.py`, `NotificationChannel`, `Hub`, `list_events`, `notification_service.py`, `scope_matches`, `.dispatch`, `paginate`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Why does `APIModel` connect `APIModel` to `v1/auth.py`, `docker_hosts.py`, `projects.py`, `incidents.py`, `containers.py`, `Node & Agent Architecture`, `ApplicationBase`, `v1/search.py`, `server_service.py`, `v1/channels.py`, `MonitorCreate`, `v1/deployments.py`, `servers.py`, `test_schemas_server.py`, `test_schemas_agent.py`, `NotificationChannel`, `AgentContainerIn`, `v1/health.py`, `container.py`, `EnvironmentUpdate`, `OutModel`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Are the 73 inferred relationships involving `AuthContext` (e.g. with `list_audit_logs()` and `_optional_actor()`) actually correct?**
  _`AuthContext` has 73 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `apiGet()` (e.g. with `ContainerDetailPage.test.tsx` and `mockApi()`) actually correct?**
  _`apiGet()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `meta`, `SCHEMA`, `RESEARCH_COMMON` to the rest of the system?**
  _397 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ApiError` be split into smaller, more focused modules?**
  _Cohesion score 0.02635529608006672 - nodes in this community are weakly interconnected._
- **Should `v1/auth.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05128205128205128 - nodes in this community are weakly interconnected._