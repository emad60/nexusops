# Graph Report - nexusops  (2026-09-22)

## Corpus Check
- 271 files · ~225,956 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: (none) 8, .example 1, .service 1)

## Summary
- 3633 nodes · 10654 edges · 170 communities (146 shown, 24 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 874 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7a92b064`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ApiError
- v1/auth.py
- App.tsx
- apiGet
- NotFound
- deps.py
- resolve_client_ip
- docker_hosts.py
- RunContext
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
- v1/deployments.py
- test_deployments_simulated.py
- containers.py
- metrics_service.py
- get_settings
- test_rate_limit.py
- monitor_service.py
- Node & Agent Architecture
- test_agent_backoff.py
- UnprocessableEntity
- nexusops_agent.py
- integration/conftest.py
- auth_service.py
- container_service.py
- types.ts
- docker_host_service.py
- resolve_auth
- monitors.py
- v1/search.py
- server_service.py
- v1/channels.py
- DockerProvider
- test_monitor_transport.py
- test_agent_contract.py
- trigger_deployment
- docker_real.py
- require_permission
- DockerHostsPage.tsx
- servers.py
- test_ssrf.py
- secret_service.py
- role_service.py
- test_schemas_server.py
- apikeys.py
- publish
- test_schemas_agent.py
- monitor_transport.py
- AuthContext
- alembic
- channel.py
- test_auth_journey.py
- compilerOptions
- enums.py
- main.py
- alert_service.py
- SimulatedDeploymentRunner
- notification_sender.py
- test_schema_redaction.py
- NotificationChannel
- Hub
- package.json
- events.py
- test_secrets.py
- Platform Security Model — NexusOps
- notification_service.py
- api service (FastAPI / uvicorn :8000)
- config.py
- alerts.py
- login
- roles.py
- ApiKeysPage.tsx
- scope_matches
- Settings
- .from_user
- readiness
- container.py
- Product Roadmap — NexusOps Multi-Tenant Platform
- devDependencies
- redact_mapping
- seed.py
- get_meta
- _validate_resolution
- Deployment Architecture — NexusOps (target state)
- test_notifications.py
- test_event_registry.py
- deployment.py
- pytest
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- journey.spec.ts
- README.md - NexusOps overview
- 2. Entities
- Secrets Architecture
- Certificate Management — NexusOps
- sessions.py
- tests/conftest.py
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- hash_token
- test_error_logging.py
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- _FakeAsyncClient
- .dispatch
- test_app_gating.py
- log_service.py
- scripts
- ContainerListPage.tsx
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
- docs/engineering-report.md - build and verification report
- postgres service (PostgreSQL 17, loopback :5433)
- Platform Vision — NexusOps
- nexusops-understand.mjs
- Invisible account lockout (5 fails -> 15 min, enumeration resistance)
- client_ip
- instant_pacing
- nexusops-draft.mjs
- assert_error_code
- nexusops-challenge.mjs
- test_agent_ingestion.py
- record
- lax
- AgentClient
- validate_endpoint_url
- ApplicationBase
- _transport_is_https
- configure_logging
- agent_heartbeat
- ._redact
- effective_permissions
- _pace
- .__init__

## God Nodes (most connected - your core abstractions)
1. `AuthContext` - 121 edges
2. `APIModel` - 102 edges
3. `apiGet()` - 75 edges
4. `get_settings()` - 62 edges
5. `record()` - 55 edges
6. `publish()` - 54 edges
7. `NotFound` - 53 edges
8. `PageParams` - 53 edges
9. `apiPost()` - 53 edges
10. `EventLevel` - 51 edges

## Surprising Connections (you probably didn't know these)
- `6. Enforcement mechanics (unchanged patterns, one addition)` --references--> `resolve_auth()`  [INFERRED]
  docs/authorization.md → backend/app/api/deps.py
- `3. Cross-cutting decisions` --references--> `require_permission()`  [INFERRED]
  docs/domain-model.md → backend/app/api/deps.py
- `10. Phase 7 — Teams, grants & custom roles` --references--> `require_permission()`  [INFERRED]
  docs/product-roadmap.md → backend/app/api/deps.py
- `7. The IDOR suite` --references--> `_search_users()`  [INFERRED]
  docs/multi-tenancy.md → backend/app/api/v1/search.py
- `1.1 Storage and crypto` --references--> `encrypt_str()`  [INFERRED]
  docs/secrets-architecture.md → backend/app/core/security.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three authentication credential families with centralized permission checks** — docs_api_md_auth, docs_api_md_refresh_rotation, docs_api_md_api_keys, docs_agent_md_enrollment_token, docs_api_md_permission_model [EXTRACTED 1.00]
- **NexusOps compose stack services** — docker_compose_yml_nexusops_stack, docker_compose_yml_postgres_service, docker_compose_yml_redis_service, docker_compose_yml_mailpit_service, docker_compose_yml_api_service, docker_compose_yml_worker_service, docker_compose_yml_scheduler_service, docker_compose_yml_frontend_service, docker_compose_yml_nginx_service [EXTRACTED 1.00]
- **WebSocket real-time fan-out spine** — docs_architecture_md_websocket_hub, docs_api_md_websocket_channels, docker_compose_yml_redis_service, docs_architecture_md_event_bus, readme_react_spa [INFERRED 0.85]

## Communities (170 total, 24 thin omitted)

### Community 0 - "ApiError"
Cohesion: 0.02
Nodes (101): ApiError, setAccessToken(), DockerHostOut, Role, SearchResult, SessionInfo, User, AuthContext (+93 more)

### Community 1 - "v1/auth.py"
Cohesion: 0.17
Nodes (20): change_password(), me(), CurrentUser, get, Authentication routes: register, login, refresh rotation, logout, me, password., The caller's identity, role name and effective permission list., Change own password; other sessions are revoked, current one survives., Bootstrap the first owner account or accept an authenticated invitation. (+12 more)

### Community 2 - "App.tsx"
Cohesion: 0.05
Nodes (70): DeploymentStepOut, EnvironmentOut, IncidentEventOut, ProjectOut, AuditLogPage, ContainerDetailPage, DeploymentDetailPage, DeploymentListPage (+62 more)

### Community 3 - "apiGet"
Cohesion: 0.06
Nodes (64): apiDelete(), apiGet(), apiPatch(), apiPost(), ApplicationOut, AlertsPage, ProjectDetailPage, RolesPage (+56 more)

### Community 4 - "NotFound"
Cohesion: 0.14
Nodes (33): NotFound, _apply_deactivation(), _assert_not_last_active_superadmin(), create_user(), deactivate_user(), get_by_email(), get_user(), list_sessions() (+25 more)

### Community 5 - "deps.py"
Cohesion: 0.07
Nodes (44): async_sessionmaker, AsyncEngine, FastAPI dependencies: database session, authentication context, RBAC gate.…, Agent ingest endpoints: enrollment handshake and periodic heartbeats.…, Audit log API. Strictly read-only: the table is append-only by design., Health probes: liveness (always cheap) and readiness (checks dependencies).…, Instance metadata: version, mode, and the caller's effective capabilities. The…, Metrics query API: server timeseries, latest snapshot, dashboard summary. (+36 more)

### Community 6 - "resolve_client_ip"
Cohesion: 0.17
Nodes (22): _is_trusted(), _parse_networks(), Request, Client-IP resolution behind chained reverse proxies. The API never takes TCP…, Parse a comma-separated CIDR list; malformed entries are skipped., Real client address for *request* per the trust model above., resolve_client_ip(), make_request() (+14 more)

### Community 7 - "docker_hosts.py"
Cohesion: 0.11
Nodes (39): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+31 more)

### Community 8 - "RunContext"
Cohesion: 0.22
Nodes (10): LogLevel, _commit_short(), Deployment runner port plus a faithful simulated implementation.…, Everything a runner needs to execute one deployment., One streamed output line for a step., RunContext, _slug(), StepLine (+2 more)

### Community 9 - "models/__init__.py"
Cohesion: 0.10
Nodes (48): Base, big_serial_pk(), json_column(), datetime, UUID, Declarative base, shared mixins and column helpers., Base for all ORM models with stable constraint naming for Alembic., Identity PK for very high-volume tables (metrics, logs). (+40 more)

### Community 10 - "project_service.py"
Cohesion: 0.16
Nodes (39): Application, EnvironmentCreate, Payload to create an environment under an application., actor_of(), _apply_update(), _check_server(), create_application(), create_environment() (+31 more)

### Community 11 - "ServerDetailPage.tsx"
Cohesion: 0.09
Nodes (34): MetricPoint, ServerDetailPage, ChartSeries, LineChart(), LineChartProps, PAD, buildServerPayload(), EMPTY_SERVER_FORM (+26 more)

### Community 12 - "APIModel"
Cohesion: 0.05
Nodes (42): ApiKeyCreateRequest, APIModel, BaseModel, Base for request/response models: ORM mode + strict-ish population., EventTypeOut, Canonical event type with its human description., HealthOut, Health / readiness schemas. (+34 more)

### Community 13 - "client.ts"
Cohesion: 0.05
Nodes (47): API_BASE, apiRequest(), buildUrl(), extractError(), getAccessToken(), refreshToken(), RequestOptions, DashboardSummary (+39 more)

### Community 14 - "projects.py"
Cohesion: 0.11
Nodes (49): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+41 more)

### Community 15 - "incident_service.py"
Cohesion: 0.10
Nodes (53): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+45 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.11
Nodes (58): deployment_log_channel(), Deployment, DeploymentStep, DeploymentStatus, EventLevel, StepStatus, _after_commit_enqueue(), _after_rollback_drop() (+50 more)

### Community 17 - "SimulatedDockerProvider"
Cohesion: 0.07
Nodes (36): ContainerHealth, ContainerStatus, Container, Observed container state mirrored from an agent or docker provider., Any, datetime, Simulated docker provider for demo and test environments. The provider is…, Plausible numbers derived from the row plus time-based sine noise. (+28 more)

### Community 18 - "maintenance.py"
Cohesion: 0.07
Nodes (48): _run(), task, Flag silent servers OFFLINE, recover returning ones. Safe to overlap., sweep_servers(), _run(), aggregate_metrics(), _run(), _collect_logs() (+40 more)

### Community 19 - "v1/deployments.py"
Cohesion: 0.08
Nodes (54): _attribute_step_idx(), _emails_for(), get_deployment(), list_application_deployments(), list_deployment_logs(), _list_deployments(), _parse_sort(), _parse_statuses() (+46 more)

### Community 20 - "test_deployments_simulated.py"
Cohesion: 0.15
Nodes (26): execute_deployment(), Run one deployment to a terminal state. Never raises; safe to re-run., get_environment(), _delivery_chain(), _owner_ctx(), _queue(), _queued_with_recorder(), Deployment engine over the simulated runner: success, failure, rollback. (+18 more)

### Community 21 - "containers.py"
Cohesion: 0.09
Nodes (46): _action_route(), _endpoint(), _container_out(), _ev(), get_container(), _like_pattern(), list_container_logs(), list_containers() (+38 more)

### Community 22 - "metrics_service.py"
Cohesion: 0.09
Nodes (41): get_dashboard_summary(), get_latest_server_metrics(), get_server_metrics(), CurrentUser, DbDep, Depends, get, UUID (+33 more)

### Community 23 - "get_settings"
Cohesion: 0.09
Nodes (43): argon2, argon2_exceptions, get_settings(), Return the cached settings singleton., Unauthorized, create_access_token(), decode_access_token(), decrypt_str() (+35 more)

### Community 24 - "test_rate_limit.py"
Cohesion: 0.05
Nodes (47): Any, RateLimited, _memory_count_and_ttl(), rate_limit(), _dependency(), Fixed-window counter backed by process memory. Returns (count, ttl)., Return a dependency enforcing *limit* requests per window per IP. With…, _clean_memory_windows() (+39 more)

### Community 25 - "monitor_service.py"
Cohesion: 0.14
Nodes (39): AppError, Exception, Base class for expected, client-facing errors., MonitorStatus, Monitor, MonitorCheck, _active_incident(), _audit() (+31 more)

### Community 26 - "Node & Agent Architecture"
Cohesion: 0.08
Nodes (24): 1. Scope and stance, 2.1 Current shape (real), 2.2 Changes for the target model, 2.3 Capabilities (target), 2.4 DockerEndpoint — the 0..1 relation, 2. The Node concept, 3.1 Current state (real), 3.3 Token storage & rotation with dual-token grace (+16 more)

### Community 27 - "test_agent_backoff.py"
Cohesion: 0.14
Nodes (22): agent_fixture(), _install_sleep(), fake_sleep(), _load_agent(), _patch_host(), Any, fixture, MonkeyPatch (+14 more)

### Community 28 - "UnprocessableEntity"
Cohesion: 0.17
Nodes (22): UnprocessableEntity, assert_safe_url(), _raise_block(), Validate *url* for outbound requests; return the parsed URL or raise 422.…, Reject non-empty values that are not valid IPv4/IPv6 addresses., _validate_ip(), Validate + normalise scopes; returns the deduplicated list. Accepts exact…, validate_scopes() (+14 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.09
Nodes (30): build_heartbeat(), collect_container_stats(), collect_containers(), cpu_percent_since(), disk_stats(), _docker_request(), _interruptible_sleep(), load1() (+22 more)

### Community 30 - "integration/conftest.py"
Cohesion: 0.16
Nodes (17): alembic_config, _clean_slate(), client(), _ensure_database(), _migrated_database(), owner(), AsyncClient, fixture (+9 more)

### Community 31 - "auth_service.py"
Cohesion: 0.13
Nodes (36): ActorType, AuditResult, _audit(), change_own_password(), count_users(), _event(), _grace_successor(), _issue_access() (+28 more)

### Community 32 - "container_service.py"
Cohesion: 0.09
Nodes (44): clip(), DockerProviderError, Exception, Provider abstraction for docker hosts (real daemon or simulated). Providers are…, A provider operation failed. ``str()`` is safe to show/log., Build a compact, secret-free description of a provider failure. Only the…, Truncate *text* to *limit* characters, stripping control chars., sanitize_error() (+36 more)

### Community 33 - "types.ts"
Cohesion: 0.05
Nodes (45): AlertOut, AuditEntry, ChannelOut, CheckOut, ContainerOut, CursorPage, DeliveryOut, DeploymentLogLine (+37 more)

### Community 34 - "docker_host_service.py"
Cohesion: 0.09
Nodes (43): asyncio, DockerHostStatus, DockerHost, DockerHostCreate, DockerHostPingOut, DockerHostUpdate, Result of probing a host's provider endpoint., Payload for registering a docker host. (+35 more)

### Community 35 - "resolve_auth"
Cohesion: 0.11
Nodes (19): _load_permissions(), AsyncSession, Resolve Bearer JWT or X-API-Key into an :class:`AuthContext`., resolve_auth(), _optional_actor(), AsyncSession, Resolve credentials if presented; None for truly anonymous calls., 10. Migration (Phase 1) (+11 more)

### Community 36 - "monitors.py"
Cohesion: 0.14
Nodes (38): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+30 more)

### Community 37 - "v1/search.py"
Cohesion: 0.14
Nodes (30): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+22 more)

### Community 38 - "server_service.py"
Cohesion: 0.08
Nodes (55): server_metrics_channel(), ServerStatus, Server, MetricSnapshot, _actor_kwargs(), _apply_agent_entry(), container_counts(), create_server() (+47 more)

### Community 39 - "v1/channels.py"
Cohesion: 0.17
Nodes (25): create_channel(), delete_channel(), get_channel(), list_channels(), list_deliveries(), DbDep, delete, Depends (+17 more)

### Community 40 - "DockerProvider"
Cohesion: 0.09
Nodes (12): DockerProvider, Any, datetime, Protocol, List containers visible to the provider., Inspect a single container by id (short ids allowed)., List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``., List volumes: keys ``name``, ``driver``, ``mountpoint``. (+4 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.13
Nodes (34): CheckResult, HTTPMonitorTransport, Deterministic fake checker for ``sim://`` monitors and demo environments.…, Real HTTP(S) probe using httpx with per-monitor settings. Redirects are…, SimulatedTransport, _check(), clock(), FakeClock (+26 more)

### Community 42 - "test_agent_contract.py"
Cohesion: 0.20
Nodes (15): agent_fixture(), _load_agent(), _patch_stats(), Any, fixture, MonkeyPatch, Contract tests: the shipped agent's payloads must satisfy the ingest schemas.…, One-shot docker stats reduce to cpu/mem/limit fields the schema accepts, with… (+7 more)

### Community 43 - "trigger_deployment"
Cohesion: 0.16
Nodes (17): cancel_deployment(), post, Request, Queue a new deployment for an application/environment pair., Cancel a QUEUED deployment immediately or flag a RUNNING one., Queue a rollback to the last good version of this app/environment., rollback_deployment(), trigger_deployment() (+9 more)

### Community 44 - "docker_real.py"
Cohesion: 0.09
Nodes (27): ContainerInfo, ContainerStats, Normalized view of a container as reported by any provider., Point-in-time resource usage snapshot., _as_float(), _compute_stats(), _cpu_percent(), _network_bytes() (+19 more)

### Community 45 - "require_permission"
Cohesion: 0.08
Nodes (23): permission_dep(), Any, Dependency factory enforcing a permission; returns 403 when denied., require_permission(), _check(), Forbidden, permission_exists(), PermissionSpec (+15 more)

### Community 46 - "DockerHostsPage.tsx"
Cohesion: 0.05
Nodes (43): SecretRow, App(), DockerHostsPage, LoginPage, SecretsPage, CheckboxField(), CheckboxFieldProps, FieldAria (+35 more)

### Community 47 - "servers.py"
Cohesion: 0.09
Nodes (37): create_server(), delete_server(), _detail(), get_server(), list_servers(), list_tags(), AsyncSession, DbDep (+29 more)

### Community 48 - "test_ssrf.py"
Cohesion: 0.17
Nodes (21): BadRequest, assert_safe_tcp_endpoint(), SSRF guard applied to every operator-supplied outbound URL. Monitors and…, Validate a ``tcp://`` docker host endpoint for outbound connection. Docker…, Internal signal: a specific SSRF rule matched (never shown to clients)., UrlRejected, _validate_syntax(), Unit tests for the SSRF guard — fully offline via injected DNS answers. (+13 more)

### Community 49 - "secret_service.py"
Cohesion: 0.12
Nodes (33): digest_of(), encrypt_str(), Short server-verifiable digest used for change detection display. HMAC-SHA256…, _actor_type(), _collect_refs(), create_secret(), delete_secret(), _detail() (+25 more)

### Community 50 - "role_service.py"
Cohesion: 0.20
Nodes (20): Conflict, create_role(), delete_role(), get_role(), list_roles(), AsyncSession, Request, Role (+12 more)

### Community 51 - "test_schemas_server.py"
Cohesion: 0.21
Nodes (22): Payload for registering a server., Partial update. ``tags`` replaces the full set when provided., ServerCreate, ServerUpdate, _base(), parametrize, Unit tests for app.schemas.server (validation only, no I/O)., test_empty_ip_is_allowed_but_whitespace_collapses() (+14 more)

### Community 52 - "apikeys.py"
Cohesion: 0.16
Nodes (18): create_api_key(), list_api_keys(), CurrentUser, DbSessionDep, delete, get, post, Request (+10 more)

### Community 53 - "publish"
Cohesion: 0.15
Nodes (20): create_api_key(), AsyncSession, Request, UUID, Revoke a key owned by *owner_id*. Foreign keys look like NotFound (no leak)., Revoke every live key of a user (used on deactivation). Returns count., Create a key for *user_id*. Returns ``(row, raw_key)`` — raw shown once., revoke_all_for_user() (+12 more)

### Community 54 - "test_schemas_agent.py"
Cohesion: 0.15
Nodes (27): AgentContainerIn, AgentHeartbeatIn, AgentHelloIn, field_validator, First contact from an agent after enrollment; fills static host facts., Observed container state reported by an agent., Periodic metrics + observed containers from an enrolled agent., _container() (+19 more)

### Community 55 - "monitor_transport.py"
Cohesion: 0.08
Nodes (25): assert_safe_url_async(), Async wrapper around :func:`assert_safe_url`; DNS runs off the loop., CheckOutcome, coerce_headers(), _decode(), get_transport(), MonitorTransport, Any (+17 more)

### Community 56 - "AuthContext"
Cohesion: 0.15
Nodes (23): AuthContext, Resolved identity attached to every authenticated request., create_secret(), delete_secret(), get_secret(), list_secrets(), DbSession, delete (+15 more)

### Community 58 - "channel.py"
Cohesion: 0.17
Nodes (15): ChannelType, DeliveryStatus, ChannelBase, ChannelCreate, ChannelUpdate, DeliveryOut, EmailConfig, BaseModel (+7 more)

### Community 59 - "test_auth_journey.py"
Cohesion: 0.16
Nodes (18): cookie_attributes(), Response, The raw Set-Cookie header carrying the refresh token., Extract just the opaque token from a Set-Cookie header., Parse Set-Cookie attributes (lowercased keys, empty string for flags)., refresh_cookie_header(), refresh_cookie_value(), _cookie_name() (+10 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "enums.py"
Cohesion: 0.24
Nodes (11): CredentialKind, DeploymentTrigger, LogSource, Closed registries of domain enumerations. Member names equal their values…, String enum; member names equal values so name/value storage never disagrees., StrEnum, UserStatus, append_lines() (+3 more)

### Community 62 - "main.py"
Cohesion: 0.15
Nodes (20): dispose_engine(), AccessLogMiddleware, HTTP middleware: request ids, security headers, structured access logs., Baseline hardening headers on every API response., RequestIDMiddleware, SecurityHeadersMiddleware, close_redis(), create_app() (+12 more)

### Community 63 - "alert_service.py"
Cohesion: 0.21
Nodes (16): AlertSeverity, Alert, create_alert(), get_alert(), mark_all_read(), mark_read(), AsyncSession, UUID (+8 more)

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
Cohesion: 0.26
Nodes (16): NotificationChannel, A delivery target (email address / webhook endpoint). ``config_ciphertext``…, _audit(), create_channel(), decrypt_channel_config(), delete_channel(), encrypt_config(), _normalize_events() (+8 more)

### Community 68 - "Hub"
Cohesion: 0.08
Nodes (31): _authenticate_api_key(), _authenticate_jwt(), _close_socket(), Connection, _entity_exists(), Hub, _is_same_origin(), _load_permissions() (+23 more)

### Community 69 - "package.json"
Cohesion: 0.13
Nodes (15): name, private, type, version, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom (+7 more)

### Community 70 - "events.py"
Cohesion: 0.21
Nodes (15): _decode_cursor(), _encode_cursor(), list_event_types(), list_events(), datetime, DbSession, Depends, get (+7 more)

### Community 71 - "test_secrets.py"
Cohesion: 0.10
Nodes (31): DeploymentEnvironment, _audit_secret_resolution(), Resolve the environment's secret references, failing closed on error. Returns…, Audit every resolved reference before any step executes. One row per secret,…, _resolve_secrets_or_fail(), Exception, A ``${secret:KEY}`` reference could not be resolved. Fail-closed. Carries…, Outcome of resolving an environment's config references. (+23 more)

### Community 72 - "Platform Security Model — NexusOps"
Cohesion: 0.11
Nodes (18): 10.1 Node revocation playbook (compromised node / leaked agent token), 10.2 Key compromise playbook, 10. Incident response, 1.1 Real vs simulated today (do not mistake one for the other), 1. Scope, stance, and simulation honesty, 2. Assets, 3. Trust boundaries, 4. Tenant isolation model (summary) (+10 more)

### Community 73 - "notification_service.py"
Cohesion: 0.18
Nodes (21): _as_uuid(), decode_delivery_cursor(), dispatch_event_frame(), _send(), dispatcher_loop(), encode_delivery_cursor(), list_deliveries(), _now() (+13 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "config.py"
Cohesion: 0.15
Nodes (14): _database_url(), Alembic environment: metadata comes from app.models, URL from app settings., Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online(), fail_on_bad_config(), Central configuration. All runtime configuration flows through this module so… (+6 more)

### Community 76 - "alerts.py"
Cohesion: 0.22
Nodes (15): list_alerts(), mark_all_read(), mark_read(), CurrentUser, DbDep, Depends, get, post (+7 more)

### Community 77 - "login"
Cohesion: 0.25
Nodes (16): _clear_refresh_cookie(), _cookies_secure(), login(), logout(), DbSessionDep, post, Request, Response (+8 more)

### Community 78 - "roles.py"
Cohesion: 0.11
Nodes (28): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, delete, get (+20 more)

### Community 79 - "ApiKeysPage.tsx"
Cohesion: 0.13
Nodes (15): ApiKeyOut, ApiKeysPage, ApiKeyCreatedOut, handleCopyKey(), copyText(), describeError(), EMPTY_FORM, GROUP_STYLE (+7 more)

### Community 80 - "scope_matches"
Cohesion: 0.14
Nodes (14): Check an API-key scope list against a required permission. Supports exact match…, scope_matches(), parametrize, test_scope_matches_truth_table(), 1. Principles (already true in the codebase, kept), 2. Registry changes (Phase 1 + new subsystems), 3. The five system roles (target), 4. Grants (resource-level access; design now, later phase) (+6 more)

### Community 81 - "Settings"
Cohesion: 0.16
Nodes (5): field_validator, model_validator, Validated application settings (loaded from environment / .env)., Settings, BaseSettings

### Community 82 - ".from_user"
Cohesion: 0.18
Nodes (15): create_user(), deactivate_user(), get_user(), CurrentUser, DbSessionDep, delete, get, post (+7 more)

### Community 83 - "readiness"
Cohesion: 0.33
Nodes (6): liveness(), get, Response, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness()

### Community 84 - "container.py"
Cohesion: 0.25
Nodes (10): ContainerRemoveOut, host_ref(), HostRef, UUID, Container schemas: list/detail read models, log entries, action results., Summary of the docker host a container runs on., Summary of the server associated with a container., Acknowledgement of a destructive removal. (+2 more)

### Community 85 - "Product Roadmap — NexusOps Multi-Tenant Platform"
Cohesion: 0.15
Nodes (13): 0. Stance, 10. Phase 7 — Teams, grants & custom roles, 11. Phase 8 — Backups, 12. Phase 9 — Billing & metering, 14. Biggest risks (short form), 15. Reading order, 2. Phase plan, 5. Phase 2 — Projects & environments (+5 more)

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "redact_mapping"
Cohesion: 0.22
Nodes (13): _is_sensitive_key(), Substring match on a normalised key so header-style names are caught too.…, Return a copy of *data* with sensitive values replaced. Used by audit metadata…, redact_mapping(), parametrize, Unit tests for app.core.logging redaction (pure functions only)., test_case_insensitive_substring_match(), test_flat_sensitive_keys_redacted() (+5 more)

### Community 88 - "seed.py"
Cohesion: 0.25
Nodes (15): LogEntry, _lock(), datetime, User, Idempotent demo seed: roles, admin user, simulated fleet, monitors, history.…, Two finished deployments + one open incident so pages have substance., (admin_password, viewer_password): deterministic in test, random otherwise., seed() (+7 more)

### Community 89 - "get_meta"
Cohesion: 0.40
Nodes (5): get_meta(), DbSessionDep, get, Public metadata; identity fields appear only for valid credentials., OptionalUser

### Community 90 - "_validate_resolution"
Cohesion: 0.17
Nodes (14): _is_forbidden_address(), is_simulation_url(), True when *url* targets the built-in simulated checker (``sim://``)., True when *addr* points into a network the server must never contact.…, Resolve *hostname* (AF_UNSPEC) and refuse any non-public answer., _validate_resolution(), parametrize, test_non_simulation_urls() (+6 more)

### Community 91 - "Deployment Architecture — NexusOps (target state)"
Cohesion: 0.14
Nodes (14): 10. Events and WS during runs, 11. Post-deploy hooks, 12. Rollback semantics (existing behavior kept), 13. The simulated runner stays — labeled, 14. Open questions, 1. Current state — what is real and what is simulated, 3. Target pipeline, 4. Runner registry — the DI fix (+6 more)

### Community 92 - "test_notifications.py"
Cohesion: 0.26
Nodes (12): NotificationDelivery, SystemEvent, event_frame_from_row(), Serialize a persisted event for WS delivery (used on replay/backfill)., _channel(), _delivery(), UUID, Notification channel + delivery-log endpoints. Regression coverage for GET… (+4 more)

### Community 93 - "test_event_registry.py"
Cohesion: 0.21
Nodes (8): event_type_catalogue(), is_known_event_type(), Canonical registry of system-event types. Single source of truth shared by…, Return True when *event_type* is part of the canonical registry., Serialise the registry for the ``/events/types`` endpoint., Registry coherence: schema-advertised event types must equal the canonical…, test_catalogue_serialises_every_entry(), test_known_event_lookup()

### Community 94 - "deployment.py"
Cohesion: 0.15
Nodes (12): DeploymentApplicationRef, DeploymentCreate, DeploymentEnvironmentRef, DeploymentStepOut, LogOut, Deployment API schemas: requests, outputs, step and log items., Persisted deployment log line., Request body for triggering a deployment of an application. (+4 more)

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

### Community 100 - "2. Entities"
Cohesion: 0.14
Nodes (14): 0. Design stance, 1.1 ER diagram, 1. The hierarchy, 2.1.1 ApiKey org binding detail, 2.2.1 Environment promotion detail, 2.2 Delivery (existing models, extended), 2.3 Infrastructure — Nodes, 2.4 Routing & TLS (new subsystem) (+6 more)

### Community 101 - "Secrets Architecture"
Cohesion: 0.11
Nodes (18): 10. Resolution flow at deploy time, 1.1 Storage and crypto, 1.2 Data model, 1.3 API surface (metadata-only reads), 1.6 Current-state gap list, 1. Current state, 2.1 Resolution runs inside org scope, 2.2 Migration mapping (+10 more)

### Community 102 - "Certificate Management — NexusOps"
Cohesion: 0.13
Nodes (15): 10. Status/expiry tracking and monitor tie-in, 12. Audit and events, 13. Non-goals, 3. API surface and permissions, 4.1 DNS-01 first (the default and the wedge), 4.2 DNSProvider interface, 4.3 ACME account and directory, 4.4 HTTP-01 via node nginx (later fallback) (+7 more)

### Community 103 - "sessions.py"
Cohesion: 0.23
Nodes (11): list_sessions(), CurrentUser, DbSessionDep, delete, get, Request, UUID, Session routes: list active sessions, revoke own or (with user.manage) any. (+3 more)

### Community 104 - "tests/conftest.py"
Cohesion: 0.20
Nodes (9): configure_test_env(), Test bootstrap: pin every cached setting BEFORE the first ``app`` import. The…, KEY=VALUE pairs from the repo .env (first definition wins); never logged., Export the exact settings the app caches; host values cannot leak through., _read_dot_env(), base64, os, sys (+1 more)

### Community 105 - "redis service (Redis 7, no persistence, loopback :6390)"
Cohesion: 0.22
Nodes (11): redis service (Redis 7, no persistence, loopback :6390), WebSocket API (/api/v1/ws handshake, frames, limits), WebSocket channels (global, server-metrics, container-logs, deployment-logs, incidents), Deployment engine (queue_deployment / execute_deployment / sweeper backstop), Real-time spine: PostgreSQL system_events + Redis pub/sub, Rollback as a new deployment (rollback_of_id), WebSocket hub (framework-thin, Redis fan-in, per-socket queues), Test suites (pytest unit+integration, vitest, Playwright e2e) (+3 more)

### Community 106 - "NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)"
Cohesion: 0.18
Nodes (12): Agent security model (one-way telemetry, no command channel), Agent enrollment token (X-Agent-Token, nxa_..., SHA-256 at rest), Agent heartbeat exponential backoff (cap 5 min, exit 1 on revoked token), agent/install.sh (enrollment installer), Agent metrics collection (/proc statvfs Docker socket), NexusOps agent (stdlib-only Python, agent/nexusops_agent.py), Agent systemd hardening (ProtectSystem=strict, NoNewPrivileges), Agent ingest API (POST /agent/hello, POST /agent/heartbeat) (+4 more)

### Community 107 - "hash_token"
Cohesion: 0.26
Nodes (12): generate_agent_token(), generate_api_key(), generate_refresh_token(), hash_token(), Return ``(raw_token, sha256_hex_hash)``., Return ``(raw_key, prefix, hash)``. Keys look like ``nxo_live_<random>``., test_agent_token_prefix_convention(), test_api_and_agent_prefixes_differ() (+4 more)

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

### Community 112 - "test_app_gating.py"
Cohesion: 0.44
Nodes (8): _app_for_environment(), MonkeyPatch, ENVIRONMENT gating contract: docs exposure and HSTS (see .env.example).…, create_app() with get_settings() patched to the given environment., test_non_production_does_not_emit_hsts(), test_non_production_keeps_docs_and_schema(), test_production_emits_hsts(), test_production_hides_docs_and_schema()

### Community 113 - "log_service.py"
Cohesion: 0.09
Nodes (33): _decode_frame(), _poll_new_lines(), Parse a Redis pub/sub frame ``{ts, stream, message}`` into a LogLine., Fetch log rows persisted after ``last_seen['id']`` (poll fallback)., Live-tail a container's logs. Primary source is the Redis pub/sub channel…, stream_container_logs(), container_log_channel(), Canonical Redis pub/sub channel names shared by API, workers and WS hub. (+25 more)

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "ContainerListPage.tsx"
Cohesion: 0.16
Nodes (11): ContainerListPage, ContainerListPage(), ContainerRef, formatCpu(), formatMemory(), formatUtc(), SORT_OPTIONS, STATUS_OPTIONS (+3 more)

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
Cohesion: 0.15
Nodes (13): list_audit_logs(), datetime, DbSession, Depends, get, PageParamsDep, Newest-first audit trail with optional filters. No write routes exist for this…, paginate() (+5 more)

### Community 125 - "DeploymentRunner"
Cohesion: 0.25
Nodes (6): DeploymentRunner, Protocol, Adapter interface implemented by real (future) and simulated runners., Return the ordered step names for this run., Stream output lines for *step_name*; raise StepFailure to fail it., 2. What survives unchanged

### Community 126 - "OutModel"
Cohesion: 0.07
Nodes (40): Agent-facing schemas. Payloads are data only — never executed., AlertOut, Schemas for operator-facing alerts., API key schemas. Raw keys appear exactly once, at creation., AuditOut, Schemas for the read-only audit log API. The audit table is append-only; these…, One audit trail entry (no write routes ever exist for this resource)., OutModel (+32 more)

### Community 146 - "helpers.py"
Cohesion: 0.18
Nodes (16): error_of(), login_account(), login_headers(), Any, AsyncClient, Pure helpers for journey tests: payloads, auth shortcuts, cookie parsing., Bootstrap owner account + session; returns ``(credentials, login_result)``., Unwrap an API error envelope. (+8 more)

### Community 147 - "docs/engineering-report.md - build and verification report"
Cohesion: 0.27
Nodes (12): docker-compose.dev.yml - dev overlay, docker-compose.docker-sock.yml - docker socket override, docker-compose.yml - full stack definition, docs/agent.md - agent guide, docs/api.md - API guide, Append-only audit log (Postgres BEFORE UPDATE OR DELETE trigger), docs/deployment.md - deployment and operations guide, docs/development.md - developer guide (+4 more)

### Community 148 - "postgres service (PostgreSQL 17, loopback :5433)"
Cohesion: 0.29
Nodes (7): postgres service (PostgreSQL 17, loopback :5433), Fernet encryption at rest (ENCRYPTION_KEY, write-once), Backups (pgdata volume, nightly pg_dump, ephemeral Redis), Required secrets (POSTGRES_PASSWORD, JWT_SECRET >= 32 chars, ENCRYPTION_KEY Fernet), Production hardening checklist (secrets, ENVIRONMENT, no seed, TLS, rotation), Compose vs host network namespaces (postgres:5432 vs 127.0.0.1:5433), Simulation mode (SIMULATION_MODE)

### Community 149 - "Platform Vision — NexusOps"
Cohesion: 0.20
Nodes (10): 1. Where NexusOps is today, 2.1 What we are NOT building, 2.2 The wedge (differentiation), 2. The direction, 3. Guiding principles, 4. Customer journey (target), 5.1 Architecture overview (target), 5. Control plane / data plane boundary (+2 more)

### Community 150 - "nexusops-understand.mjs"
Cohesion: 0.33
Nodes (5): COMMON, meta, out, READERS, SCHEMA

### Community 151 - "Invisible account lockout (5 fails -> 15 min, enumeration resistance)"
Cohesion: 0.33
Nodes (6): Invisible account lockout (5 fails -> 15 min, enumeration resistance), Unified error envelope (code, message, request_id), Per-IP rate limiting (Redis fixed window), Request lifecycle (edge -> middleware -> rate limit -> deps -> router), Client IP resolution (resolve_client_ip, TRUSTED_PROXY_CIDRS, XFF overwrite), EmailStr rejects reserved domains (login 422 on .test/.local/.arpa)

### Community 152 - "client_ip"
Cohesion: 0.28
Nodes (9): get_current_user(), get_optional_user(), DbSessionDep, Request, Standard authentication dependency. Also records client IP for logs/audit., Like :func:`get_current_user` but returns ``None`` for anonymous callers., client_ip(), Request (+1 more)

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

### Community 158 - "record"
Cohesion: 0.33
Nodes (6): Any, AsyncSession, Request, UUID, Append an audit row using the caller's transaction (no commit here). Sensitive…, record()

### Community 159 - "lax"
Cohesion: 0.40
Nodes (5): lax(), fixture, Production posture: private targets are NOT allowed (resolution runs)., Simulation posture: resolution skipped, syntax still enforced., strict()

### Community 161 - "validate_endpoint_url"
Cohesion: 0.50
Nodes (3): model_validator, Validate/normalize an endpoint URL against the scheme allowlist., validate_endpoint_url()

### Community 162 - "ApplicationBase"
Cohesion: 0.40
Nodes (4): ApplicationBase, Any, field_validator, Shared application fields; ``build_config`` is a free-form dict.

### Community 163 - "_transport_is_https"
Cohesion: 0.50
Nodes (4): Whether this request's cookie will travel over https. The edge always…, _transport_is_https(), The Secure-cookie decision follows the wire, not the environment label.…, test_transport_is_https_decision()

### Community 164 - "configure_logging"
Cohesion: 0.50
Nodes (4): configure_logging(), _orjson_dumps(), Any, Configure structlog + stdlib logging once at process start. Everything…

### Community 165 - "agent_heartbeat"
Cohesion: 0.18
Nodes (14): agent_heartbeat(), agent_hello(), DbDep, post, Request, Response, Resolve ``X-Agent-Token`` to an enrolled server or raise 401., First contact after enrollment: persist static host facts, negotiate cadence. (+6 more)

### Community 166 - "._redact"
Cohesion: 0.50
Nodes (3): field_serializer, Mask any userinfo credentials before the URL leaves the API., redact_endpoint_url()

### Community 167 - "effective_permissions"
Cohesion: 0.67
Nodes (3): effective_permissions(), User, Sorted explicit permission codenames for a user; ``*`` expands to the registry.

### Community 168 - "_pace"
Cohesion: 0.67
Nodes (3): _pace(), Deterministic per-line delay between 0.05s and 0.35s., test_pace_bounds()

## Knowledge Gaps
- **397 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+392 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1455 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **24 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AuthContext` connect `AuthContext` to `v1/auth.py`, `NotFound`, `deps.py`, `docker_hosts.py`, `project_service.py`, `projects.py`, `incident_service.py`, `deployment_engine.py`, `v1/deployments.py`, `test_deployments_simulated.py`, `containers.py`, `metrics_service.py`, `client_ip`, `monitor_service.py`, `record`, `auth_service.py`, `container_service.py`, `docker_host_service.py`, `resolve_auth`, `monitors.py`, `server_service.py`, `v1/channels.py`, `require_permission`, `servers.py`, `secret_service.py`, `role_service.py`, `publish`, `NotificationChannel`, `Hub`, `events.py`, `notification_service.py`, `scope_matches`, `.dispatch`, `paginate`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Why does `README.md - NexusOps overview` connect `README.md - NexusOps overview` to `docs/engineering-report.md - build and verification report`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Why does `docs/troubleshooting.md - symptom -> cause -> fix runbook` connect `docs/engineering-report.md - build and verification report` to `README.md - NexusOps overview`, `Invisible account lockout (5 fails -> 15 min, enumeration resistance)`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Are the 73 inferred relationships involving `AuthContext` (e.g. with `list_audit_logs()` and `_optional_actor()`) actually correct?**
  _`AuthContext` has 73 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `apiGet()` (e.g. with `ContainerDetailPage.test.tsx` and `mockApi()`) actually correct?**
  _`apiGet()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `meta`, `SCHEMA`, `RESEARCH_COMMON` to the rest of the system?**
  _397 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ApiError` be split into smaller, more focused modules?**
  _Cohesion score 0.02147074610842727 - nodes in this community are weakly interconnected._