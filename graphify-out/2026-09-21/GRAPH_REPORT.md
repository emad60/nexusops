# Graph Report - nexusops  (2026-09-21)

## Corpus Check
- 267 files · ~215,013 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: (none) 8, .example 1, .service 1)

## Summary
- 3562 nodes · 10462 edges · 163 communities (139 shown, 24 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 846 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cacdbc89`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ApiError
- APIModel
- @tanstack/react-query
- apiGet
- App.tsx
- deps.py
- resolve_client_ip
- get_host
- RunContext
- models/__init__.py
- incident.py
- ServerDetailPage.tsx
- OutModel
- client.ts
- project_service.py
- incidents.py
- deployment_engine.py
- SimulatedDockerProvider
- maintenance.py
- PageParams
- docker_real.py
- containers.py
- get_latest_server_metrics
- test_security.py
- Domain Routing — NexusOps
- monitor_service.py
- Node & Agent Architecture
- _order_clause
- AuthContext.tsx
- nexusops_agent.py
- main.py
- auth_service.py
- container_service.py
- types.ts
- DockerHost
- NotFound
- monitors.py
- v1/search.py
- server_service.py
- v1/channels.py
- DockerProvider
- test_monitor_transport.py
- pytest
- v1/deployments.py
- RealDockerProvider
- test_permissions.py
- form.tsx
- servers.py
- test_ssrf.py
- AuthContext
- role_service.py
- test_schemas_server.py
- apikeys.py
- users.py
- NotificationChannel
- monitor_transport.py
- rotate_secret
- collections_abc
- test_rate_limit.py
- test_auth_journey.py
- compilerOptions
- enums.py
- middleware.py
- digest_of
- SimulatedDeploymentRunner
- notification_sender.py
- test_schema_redaction.py
- notification_service.py
- Hub
- package.json
- require_permission
- docker_hosts.py
- Platform Security Model — NexusOps
- timeseries
- api service (FastAPI / uvicorn :8000)
- env.py
- alerts.py
- get_redis
- roles.py
- ApiKeysPage.tsx
- scope_matches
- Settings
- resolve_auth
- v1/health.py
- publish
- Product Roadmap — NexusOps Multi-Tenant Platform
- devDependencies
- redact_mapping
- docs/engineering-report.md - build and verification report
- get_settings
- channel.py
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
- test_secrets.py
- list_docker_hosts
- create_host
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- DockerProviderError
- register_exception_handlers
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- _FakeAsyncClient
- docs/architecture.md - system architecture
- create_app
- collect_recent_logs
- scripts
- ContainerListPage.test.tsx
- config.py
- Platform Vision — NexusOps
- dependencies
- FakeWebSocket
- generate_secrets.sh
- get_meta
- SecretOut
- router.py
- Multi-Tenancy Architecture
- DeploymentRunner
- MonitorBase
- .__tablename__
- install.sh
- docker-entrypoint.sh
- integration/__init__.py
- CLAUDE.md - project graphify rules
- Graphify query workflow (query / path / explain / update)
- frontend/index.html - SPA shell
- NexusOps Favicon — stylized letter 'N' lettermark in sky blue (#38bdf8) on a dark navy rounded square (#0b1120, 7px corner radius)
- nexusops-backend
- StepFailure
- simulation_tick
- postgres service (PostgreSQL 17, loopback :5433)
- role.py
- nexusops-understand.mjs
- Invisible account lockout (5 fails -> 15 min, enumeration resistance)
- validate_endpoint_url
- instant_pacing
- nexusops-draft.mjs
- 6. Agent security
- create_docker_host
- configure_logging
- effective_permissions
- sweep_servers
- run_due_monitors
- Timeseries
- SecretRotate

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
- `3. Cross-cutting decisions` --references--> `require_permission()`  [INFERRED]
  docs/domain-model.md → backend/app/api/deps.py
- `10. Phase 7 — Teams, grants & custom roles` --references--> `require_permission()`  [INFERRED]
  docs/product-roadmap.md → backend/app/api/deps.py
- `3.2 Enrollment v2` --references--> `require_server()`  [INFERRED]
  docs/node-agent-architecture.md → backend/app/api/v1/agent.py
- `3.2 Route` --references--> `rate_limit()`  [INFERRED]
  docs/domain-routing.md → backend/app/core/rate_limit.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three authentication credential families with centralized permission checks** — docs_api_md_auth, docs_api_md_refresh_rotation, docs_api_md_api_keys, docs_agent_md_enrollment_token, docs_api_md_permission_model [EXTRACTED 1.00]
- **NexusOps compose stack services** — docker_compose_yml_nexusops_stack, docker_compose_yml_postgres_service, docker_compose_yml_redis_service, docker_compose_yml_mailpit_service, docker_compose_yml_api_service, docker_compose_yml_worker_service, docker_compose_yml_scheduler_service, docker_compose_yml_frontend_service, docker_compose_yml_nginx_service [EXTRACTED 1.00]
- **WebSocket real-time fan-out spine** — docs_architecture_md_websocket_hub, docs_api_md_websocket_channels, docker_compose_yml_redis_service, docs_architecture_md_event_bus, readme_react_spa [INFERRED 0.85]

## Communities (163 total, 24 thin omitted)

### Community 0 - "ApiError"
Cohesion: 0.03
Nodes (63): ApiError, DockerHostOut, SecretRow, SessionInfo, ME, mocks, Toast, TOAST_ARIA_LABEL (+55 more)

### Community 1 - "APIModel"
Cohesion: 0.08
Nodes (54): change_password(), _clear_refresh_cookie(), _cookies_secure(), login(), logout(), me(), _optional_actor(), AsyncSession (+46 more)

### Community 2 - "@tanstack/react-query"
Cohesion: 0.05
Nodes (59): AuditEntry, DeploymentOut, EnvironmentOut, Page, ProjectOut, AuditLogPage, ContainerListPage, DeploymentListPage (+51 more)

### Community 3 - "apiGet"
Cohesion: 0.08
Nodes (58): apiDelete(), apiGet(), apiPatch(), apiPost(), ApplicationOut, MonitorListPage, ProjectDetailPage, useAuth() (+50 more)

### Community 4 - "App.tsx"
Cohesion: 0.04
Nodes (57): DashboardSummary, DeploymentStepOut, IncidentEventOut, SearchResult, AlertsPage, App(), DashboardPage, DeploymentDetailPage (+49 more)

### Community 5 - "deps.py"
Cohesion: 0.07
Nodes (43): asyncio, FastAPI dependencies: database session, authentication context, RBAC gate.…, Agent ingest endpoints: enrollment handshake and periodic heartbeats.…, Canonical Redis pub/sub channel names shared by API, workers and WS hub., AppError, Exception, Error taxonomy and the single place where API error envelopes are shaped. Every…, Base class for expected, client-facing errors. (+35 more)

### Community 6 - "resolve_client_ip"
Cohesion: 0.17
Nodes (22): _is_trusted(), _parse_networks(), Request, Client-IP resolution behind chained reverse proxies. The API never takes TCP…, Parse a comma-separated CIDR list; malformed entries are skipped., Real client address for *request* per the trust model above., resolve_client_ip(), make_request() (+14 more)

### Community 7 - "get_host"
Cohesion: 0.21
Nodes (20): delete_docker_host(), get_docker_host(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host(), DbSessionDep, delete (+12 more)

### Community 8 - "RunContext"
Cohesion: 0.21
Nodes (11): LogLevel, _commit_short(), _pace(), Deployment runner port plus a faithful simulated implementation.…, Deterministic per-line delay between 0.05s and 0.35s., Everything a runner needs to execute one deployment., One streamed output line for a step., RunContext (+3 more)

### Community 9 - "models/__init__.py"
Cohesion: 0.08
Nodes (52): Base, big_serial_pk(), json_column(), datetime, UUID, Declarative base, shared mixins and column helpers., Base for all ORM models with stable constraint naming for Alembic., Identity PK for very high-volume tables (metrics, logs). (+44 more)

### Community 10 - "incident.py"
Cohesion: 0.20
Nodes (9): IncidentAcknowledge, IncidentEventOut, IncidentNote, IncidentResolve, IncidentSortField, Schemas for incidents and their timeline., Payload for POST /incidents/{id}/acknowledge., Payload for POST /incidents/{id}/resolve. (+1 more)

### Community 11 - "ServerDetailPage.tsx"
Cohesion: 0.07
Nodes (45): ContainerOut, MetricPoint, ServerDetail, ServerSummary, ServerDetailPage, ServerListPage, ChartSeries, LineChart() (+37 more)

### Community 12 - "OutModel"
Cohesion: 0.05
Nodes (50): AlertOut, Schemas for operator-facing alerts., ApiKeyCreateRequest, API key schemas. Raw keys appear exactly once, at creation., AuditOut, Schemas for the read-only audit log API. The audit table is append-only; these…, One audit trail entry (no write routes ever exist for this resource)., OutModel (+42 more)

### Community 13 - "client.ts"
Cohesion: 0.06
Nodes (43): API_BASE, apiRequest(), buildUrl(), extractError(), getAccessToken(), refreshToken(), RequestOptions, EventItem (+35 more)

### Community 14 - "project_service.py"
Cohesion: 0.06
Nodes (102): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+94 more)

### Community 15 - "incidents.py"
Cohesion: 0.20
Nodes (24): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+16 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.07
Nodes (76): deployment_log_channel(), Deployment, DeploymentStep, DeploymentStatus, StepStatus, _after_commit_enqueue(), _after_rollback_drop(), cancel_deployment() (+68 more)

### Community 17 - "SimulatedDockerProvider"
Cohesion: 0.08
Nodes (30): ContainerStatus, Any, Plausible numbers derived from the row plus time-based sine noise., Implements :class:`DockerProvider` semantics against DB rows., Make a container row visible to this provider instance., Attach already-fetched log rows so ``logs()`` can replay them., _seed_int(), SimulatedDockerProvider (+22 more)

### Community 18 - "maintenance.py"
Cohesion: 0.14
Nodes (25): _run(), _run(), aggregate_metrics(), _run(), _collect_logs(), expire_sessions(), _run(), task (+17 more)

### Community 19 - "PageParams"
Cohesion: 0.07
Nodes (48): Secrets manager API. Reads return metadata only; plaintext values are accepted…, list_servers(), Depends, List servers with filters, search and pagination., list_sessions(), CurrentUser, DbSessionDep, delete (+40 more)

### Community 20 - "docker_real.py"
Cohesion: 0.15
Nodes (20): ContainerStats, Point-in-time resource usage snapshot., _as_float(), _compute_stats(), _cpu_percent(), _network_bytes(), parse_log_line(), parse_rfc3339() (+12 more)

### Community 21 - "containers.py"
Cohesion: 0.06
Nodes (63): _action_route(), _endpoint(), _container_out(), _decode_frame(), _ev(), get_container(), _like_pattern(), list_container_logs() (+55 more)

### Community 22 - "get_latest_server_metrics"
Cohesion: 0.16
Nodes (17): get_dashboard_summary(), get_latest_server_metrics(), get_server_metrics(), CurrentUser, DbDep, Depends, get, UUID (+9 more)

### Community 23 - "test_security.py"
Cohesion: 0.14
Nodes (18): password_needs_rehash(), tokens_equal(), verify_password(), Unit tests for app.core.security — no database or Redis required., The Secure-cookie decision follows the wire, not the environment label.…, test_encryption_is_non_deterministic(), test_fresh_hash_does_not_need_rehash(), test_garbage_token_rejected() (+10 more)

### Community 24 - "Domain Routing — NexusOps"
Cohesion: 0.07
Nodes (29): 10. Wildcards and catch-all, 11. User journey, 12. API surface, permissions, audit, 13. Monitoring tie-in, 1. Scope and current state, 2. Where nginx runs, 3.1 Domain, 3.2 Route (+21 more)

### Community 25 - "monitor_service.py"
Cohesion: 0.13
Nodes (40): MonitorStatus, Monitor, MonitorCheck, MonitorCreate, MonitorUpdate, Payload for POST /monitors., Partial update; ``url`` changes are re-validated against the SSRF guard., _active_incident() (+32 more)

### Community 26 - "Node & Agent Architecture"
Cohesion: 0.08
Nodes (24): 1. Scope and stance, 2.1 Current shape (real), 2.2 Changes for the target model, 2.3 Capabilities (target), 2.4 DockerEndpoint — the 0..1 relation, 2. The Node concept, 3.1 Current state (real), 3.2 Enrollment v2 (+16 more)

### Community 27 - "_order_clause"
Cohesion: 0.67
Nodes (3): _order_clause(), ColumnElement, Translate ``name`` / ``-created_at`` style sort keys to ORDER BY.

### Community 28 - "AuthContext.tsx"
Cohesion: 0.07
Nodes (28): setAccessToken(), Role, User, AuthContext, AuthProvider(), AuthState, MeResponse, permissionMatches() (+20 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.07
Nodes (35): AgentClient, build_heartbeat(), collect_container_stats(), collect_containers(), cpu_percent_since(), disk_stats(), _docker_request(), load1() (+27 more)

### Community 30 - "main.py"
Cohesion: 0.07
Nodes (38): alembic_config, async_sessionmaker, AsyncEngine, Instance metadata: version, mode, and the caller's effective capabilities. The…, Metrics query API: server timeseries, latest snapshot, dashboard summary., dispose_engine(), get_engine(), get_session() (+30 more)

### Community 31 - "auth_service.py"
Cohesion: 0.08
Nodes (54): argon2, argon2_exceptions, Unauthorized, generate_agent_token(), generate_api_key(), generate_refresh_token(), hash_password(), hash_token() (+46 more)

### Community 32 - "container_service.py"
Cohesion: 0.13
Nodes (32): DockerHostStatus, Container, Observed container state mirrored from an agent or docker provider., LogEntry, describe_provider_error(), is_simulated(), Exception, True when *provider* is the simulated implementation. (+24 more)

### Community 33 - "types.ts"
Cohesion: 0.07
Nodes (31): AlertOut, ChannelOut, CheckOut, CursorPage, DeliveryOut, DeploymentLogLine, DeploymentStatus, IncidentOut (+23 more)

### Community 34 - "DockerHost"
Cohesion: 0.21
Nodes (17): DockerHost, provider_for(), Return the provider matching *host*'s endpoint configuration., list_hosts(), list_images(), list_networks(), list_volumes(), ping_host() (+9 more)

### Community 35 - "NotFound"
Cohesion: 0.13
Nodes (34): Forbidden, NotFound, _apply_deactivation(), _assert_not_last_active_superadmin(), create_user(), deactivate_user(), get_by_email(), get_user() (+26 more)

### Community 36 - "monitors.py"
Cohesion: 0.15
Nodes (35): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+27 more)

### Community 37 - "v1/search.py"
Cohesion: 0.13
Nodes (31): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+23 more)

### Community 38 - "server_service.py"
Cohesion: 0.07
Nodes (61): agent_heartbeat(), agent_hello(), DbDep, post, Request, Response, Resolve ``X-Agent-Token`` to an enrolled server or raise 401., First contact after enrollment: persist static host facts, negotiate cadence. (+53 more)

### Community 39 - "v1/channels.py"
Cohesion: 0.17
Nodes (25): create_channel(), delete_channel(), get_channel(), list_channels(), list_deliveries(), DbDep, delete, Depends (+17 more)

### Community 40 - "DockerProvider"
Cohesion: 0.10
Nodes (10): DockerProvider, Any, Protocol, List containers visible to the provider., Inspect a single container by id (short ids allowed)., List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``., List volumes: keys ``name``, ``driver``, ``mountpoint``., List networks: keys ``name``, ``driver``, ``scope``. (+2 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.11
Nodes (37): CheckResult, coerce_headers(), HTTPMonitorTransport, Any, Deterministic fake checker for ``sim://`` monitors and demo environments.…, Normalise arbitrary JSON-ish header input into a plain str->str dict., Real HTTP(S) probe using httpx with per-monitor settings. Redirects are…, SimulatedTransport (+29 more)

### Community 42 - "pytest"
Cohesion: 0.07
Nodes (50): ContainerHealth, AgentContainerIn, AgentHeartbeatIn, AgentHelloIn, field_validator, Agent-facing schemas. Payloads are data only — never executed., First contact from an agent after enrollment; fills static host facts., Observed container state reported by an agent. (+42 more)

### Community 43 - "v1/deployments.py"
Cohesion: 0.09
Nodes (48): _attribute_step_idx(), cancel_deployment(), _emails_for(), get_deployment(), list_application_deployments(), list_deployment_logs(), _list_deployments(), _parse_sort() (+40 more)

### Community 44 - "RealDockerProvider"
Cohesion: 0.16
Nodes (7): ContainerInfo, Normalized view of a container as reported by any provider., T, Execute an SDK call with one short retry, normalizing failures., Two short samples give real cpu/net deltas without streaming., Talks to a real docker daemon over ``unix://`` or ``tcp://``., RealDockerProvider

### Community 45 - "test_permissions.py"
Cohesion: 0.13
Nodes (13): permission_exists(), _auth_context(), _FakeCtx, Unit tests for the permission registry, scope matching and RBAC gate., Duck-typed stand-in for AuthContext., test_api_key_scope_intersects_role_permissions(), test_permission_exists_helper(), test_plain_user_without_permissions_is_denied() (+5 more)

### Community 46 - "form.tsx"
Cohesion: 0.10
Nodes (17): LoginPage, CheckboxField(), CheckboxFieldProps, FieldAria, FieldBaseProps, PasswordField(), PasswordFieldProps, SearchInputProps (+9 more)

### Community 47 - "servers.py"
Cohesion: 0.09
Nodes (38): create_server(), delete_server(), _detail(), get_server(), list_tags(), AsyncSession, DbDep, delete (+30 more)

### Community 48 - "test_ssrf.py"
Cohesion: 0.08
Nodes (56): BadRequest, UnprocessableEntity, assert_safe_tcp_endpoint(), assert_safe_url(), _is_forbidden_address(), is_simulation_url(), _raise_block(), Validate *url* for outbound requests; return the parsed URL or raise 422.… (+48 more)

### Community 49 - "AuthContext"
Cohesion: 0.11
Nodes (34): AuthContext, Resolved identity attached to every authenticated request., An encrypted configuration value. The plaintext is never returned by the API…, Secret, Any, AsyncSession, Request, UUID (+26 more)

### Community 50 - "role_service.py"
Cohesion: 0.20
Nodes (20): Conflict, create_role(), delete_role(), get_role(), list_roles(), AsyncSession, Request, Role (+12 more)

### Community 51 - "test_schemas_server.py"
Cohesion: 0.21
Nodes (22): Payload for registering a server., Partial update. ``tags`` replaces the full set when provided., ServerCreate, ServerUpdate, _base(), parametrize, Unit tests for app.schemas.server (validation only, no I/O)., test_empty_ip_is_allowed_but_whitespace_collapses() (+14 more)

### Community 52 - "apikeys.py"
Cohesion: 0.16
Nodes (18): create_api_key(), list_api_keys(), CurrentUser, DbSessionDep, delete, get, post, Request (+10 more)

### Community 53 - "users.py"
Cohesion: 0.17
Nodes (20): create_user(), deactivate_user(), get_user(), list_users(), CurrentUser, DbSessionDep, delete, get (+12 more)

### Community 54 - "NotificationChannel"
Cohesion: 0.22
Nodes (19): NotificationChannel, A delivery target (email address / webhook endpoint). ``config_ciphertext``…, EmailConfig, _audit(), create_channel(), decrypt_channel_config(), delete_channel(), encrypt_config() (+11 more)

### Community 55 - "monitor_transport.py"
Cohesion: 0.08
Nodes (27): assert_safe_url_async(), SSRF guard applied to every operator-supplied outbound URL. Monitors and…, Async wrapper around :func:`assert_safe_url`; DNS runs off the loop., CheckOutcome, _decode(), get_transport(), MonitorTransport, BaseException (+19 more)

### Community 56 - "rotate_secret"
Cohesion: 0.18
Nodes (18): create_secret(), delete_secret(), get_secret(), list_secrets(), DbSession, delete, Depends, get (+10 more)

### Community 57 - "collections_abc"
Cohesion: 0.12
Nodes (3): alembic, collections_abc, sqlalchemy_dialects

### Community 58 - "test_rate_limit.py"
Cohesion: 0.18
Nodes (17): RateLimited, _memory_count_and_ttl(), rate_limit(), _dependency(), Fixed-window counter backed by process memory. Returns (count, ttl)., Return a dependency enforcing *limit* requests per window per IP. With…, _clean_memory_windows(), _FakeRequest (+9 more)

### Community 59 - "test_auth_journey.py"
Cohesion: 0.05
Nodes (75): assert_error_code(), bearer(), cookie_attributes(), error_of(), login_account(), login_headers(), Any, AsyncClient (+67 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "enums.py"
Cohesion: 0.09
Nodes (52): AlertSeverity, CredentialKind, EventLevel, IncidentEventKind, IncidentSeverity, IncidentStatus, LogSource, MetricGranularity (+44 more)

### Community 62 - "middleware.py"
Cohesion: 0.13
Nodes (15): ASGIApp, UUID, AccessLogMiddleware, Request, Response, HTTP middleware: request ids, security headers, structured access logs., Baseline hardening headers on every API response., RequestIDMiddleware (+7 more)

### Community 63 - "digest_of"
Cohesion: 0.10
Nodes (21): digest_of(), Short server-verifiable digest used for change detection display. HMAC-SHA256…, test_digest_is_keyed_not_plain_sha256(), test_digest_length_and_determinism(), 10. Status/expiry tracking and monitor tie-in, 12. Audit and events, 13. Non-goals, 2. Certificate entity (+13 more)

### Community 64 - "SimulatedDeploymentRunner"
Cohesion: 0.31
Nodes (19): Staged docker-style simulation used by v1 deployments., Canonical step identifiers stored on :class:`DeploymentStep` rows., SimulatedDeploymentRunner, StepName, _collect(), _ctx(), Unit tests for SimulatedDeploymentRunner (async generators, no broker)., test_broken_version_does_not_affect_other_steps() (+11 more)

### Community 65 - "notification_sender.py"
Cohesion: 0.16
Nodes (17): NotificationError, Any, BaseException, Exception, Low-level notification transports: SMTP email and outgoing webhooks. These…, POST *payload* as JSON to *url*; 2xx is success, anything else raises. Response…, Raised when a delivery attempt fails. Message is safe to persist., Bounded, single-line, content-free error reason. (+9 more)

### Community 66 - "test_schema_redaction.py"
Cohesion: 0.18
Nodes (17): is_sensitive_header(), mask_sensitive_headers(), True when *name* looks like it carries a credential (Authorization etc.)., Return a copy of *headers* with sensitive values replaced by a mask., mask_target(), Human-readable masked target safe to expose over the API. For webhook families…, _monitor_out(), Outbound-schema redaction: monitor probe credentials and webhook targets.… (+9 more)

### Community 67 - "notification_service.py"
Cohesion: 0.20
Nodes (20): _as_uuid(), decode_delivery_cursor(), dispatch_event_frame(), _send(), dispatcher_loop(), encode_delivery_cursor(), list_deliveries(), _now() (+12 more)

### Community 68 - "Hub"
Cohesion: 0.11
Nodes (21): _close_socket(), Connection, _entity_exists(), Hub, _is_same_origin(), _params_key(), _parse_payload(), Any (+13 more)

### Community 69 - "package.json"
Cohesion: 0.13
Nodes (15): name, private, type, version, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom (+7 more)

### Community 70 - "require_permission"
Cohesion: 0.08
Nodes (35): permission_dep(), Any, Dependency factory enforcing a permission; returns 403 when denied., require_permission(), _check(), list_audit_logs(), datetime, DbSession (+27 more)

### Community 71 - "docker_hosts.py"
Cohesion: 0.20
Nodes (16): Docker host API: CRUD, ping and provider-backed inventory reads. Permission…, DockerHostCreate, DockerHostPingOut, DockerHostUpdate, DockerImageOut, DockerNetworkOut, DockerVolumeOut, image_out() (+8 more)

### Community 72 - "Platform Security Model — NexusOps"
Cohesion: 0.11
Nodes (18): 10.1 Node revocation playbook (compromised node / leaked agent token), 10.2 Key compromise playbook, 10. Incident response, 1.1 Real vs simulated today (do not mistake one for the other), 1. Scope, stance, and simulation honesty, 2. Assets, 3. Trust boundaries, 4. Tenant isolation model (summary) (+10 more)

### Community 73 - "timeseries"
Cohesion: 0.15
Nodes (17): aggregate_rollups(), _extra_object(), granularity_for_range(), _prune(), Any, AsyncSession, Return ``{range, granularity, points}`` for one server. A single grouped query…, JSONB object mapping every metric to its min/max aggregate. (+9 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "env.py"
Cohesion: 0.27
Nodes (9): _database_url(), Alembic environment: metadata comes from app.models, URL from app settings., Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online(), Return a psycopg3-compatible URL usable by Alembic/Celery sync paths., sync_database_url() (+1 more)

### Community 76 - "alerts.py"
Cohesion: 0.14
Nodes (23): list_alerts(), mark_all_read(), mark_read(), CurrentUser, DbDep, Depends, get, post (+15 more)

### Community 77 - "get_redis"
Cohesion: 0.22
Nodes (12): Redis-backed fixed-window rate limiting as a FastAPI dependency factory. Auth-…, get_redis(), ping(), Shared async Redis client., _next_data_message(), Event bus fan-out ordering: a frame follows its transaction, never leads it.…, Regression: a rollback must drop stashed frames, not defer them. The stash…, test_frame_published_only_after_commit() (+4 more)

### Community 78 - "roles.py"
Cohesion: 0.13
Nodes (23): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, delete, get (+15 more)

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
Cohesion: 0.18
Nodes (15): get_current_user(), get_optional_user(), _load_permissions(), AsyncSession, DbSessionDep, Request, Standard authentication dependency. Also records client IP for logs/audit., Like :func:`get_current_user` but returns ``None`` for anonymous callers. (+7 more)

### Community 83 - "v1/health.py"
Cohesion: 0.20
Nodes (13): liveness(), get, Response, Health probes: liveness (always cheap) and readiness (checks dependencies).…, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness(), HealthOut (+5 more)

### Community 84 - "publish"
Cohesion: 0.13
Nodes (23): create_api_key(), AsyncSession, Request, UUID, API key lifecycle: creation with scope validation, listing, revocation., Revoke a key owned by *owner_id*. Foreign keys look like NotFound (no leak)., Revoke every live key of a user (used on deactivation). Returns count., Validate + normalise scopes; returns the deduplicated list. Accepts exact… (+15 more)

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
Cohesion: 0.32
Nodes (13): docker-compose.dev.yml - dev overlay, docker-compose.docker-sock.yml - docker socket override, docker-compose.yml - full stack definition, docs/agent.md - agent guide, docs/api.md - API guide, Append-only audit log (Postgres BEFORE UPDATE OR DELETE trigger), docs/deployment.md - deployment and operations guide, docs/development.md - developer guide (+5 more)

### Community 89 - "get_settings"
Cohesion: 0.21
Nodes (14): get_settings(), Return the cached settings singleton., create_access_token(), decode_access_token(), Any, UUID, Return ``(token, jti)`` for a short-lived access token., Decode + validate an access token or raise :class:`Unauthorized`. (+6 more)

### Community 90 - "channel.py"
Cohesion: 0.22
Nodes (11): ChannelType, DeliveryStatus, ChannelBase, ChannelCreate, ChannelUpdate, DeliveryOut, BaseModel, model_validator (+3 more)

### Community 91 - "Deployment Architecture — NexusOps (target state)"
Cohesion: 0.14
Nodes (14): 10. Events and WS during runs, 11. Post-deploy hooks, 12. Rollback semantics (existing behavior kept), 13. The simulated runner stays — labeled, 14. Open questions, 1.1 The honest defect list, 1. Current state — what is real and what is simulated, 3. Target pipeline (+6 more)

### Community 92 - "test_notifications.py"
Cohesion: 0.36
Nodes (9): NotificationDelivery, _channel(), _delivery(), UUID, Notification channel + delivery-log endpoints. Regression coverage for GET…, The same event frame consumed twice queues ONE delivery per channel. Every API…, test_dispatch_frame_is_idempotent_across_workers(), test_list_deliveries_filters_by_channel() (+1 more)

### Community 93 - "test_event_registry.py"
Cohesion: 0.21
Nodes (8): event_type_catalogue(), is_known_event_type(), Canonical registry of system-event types. Single source of truth shared by…, Return True when *event_type* is part of the canonical registry., Serialise the registry for the ``/events/types`` endpoint., Registry coherence: schema-advertised event types must equal the canonical…, test_catalogue_serialises_every_entry(), test_known_event_lookup()

### Community 94 - "run_async"
Cohesion: 0.27
Nodes (12): Any, T, Run *coroutine* on a dedicated event loop (Celery workers are sync)., run_async(), _answer(), _boom(), _nested(), Unit tests for the Celery-task async bridge (pure asyncio, no broker). (+4 more)

### Community 95 - "test_monitors_incidents.py"
Cohesion: 0.29
Nodes (9): encrypt_str(), _create_monitor(), Monitor checks driving the full down -> incident -> recovery lifecycle., Regression: probe headers and URL query credentials never leave the API. Probe…, test_check_now_endpoint_runs_immediately(), test_down_then_recover_lifecycle(), test_metadata_endpoint_and_private_target_blocked(), test_monitor_responses_mask_probe_credentials() (+1 more)

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
Cohesion: 0.15
Nodes (13): 10. Resolution flow at deploy time, 2.1 Resolution runs inside org scope, 2.2 Migration mapping, 2. Target scope model (org / project / environment layering), 3.1 What this fixes, 3. SecretVersion — append-only history, 4.1 Audit event at resolution time, 4. Resolution authorization (+5 more)

### Community 102 - "test_secrets.py"
Cohesion: 0.13
Nodes (19): decrypt_str(), _fernet(), _collect_refs(), Recursively collect ``${secret:KEY}`` references from config values., Resolve every ``${secret:KEY}`` reference in an environment's config. INTERNAL…, resolve_secrets_for_environment(), _create(), Secrets: metadata-only reads, rotation versioning, deploy-time resolution. (+11 more)

### Community 103 - "list_docker_hosts"
Cohesion: 0.17
Nodes (11): list_docker_hosts(), alias, Depends, max_length, Query, Offset-paginated docker host listing; exposes status and last_error., DockerHostOut, field_serializer (+3 more)

### Community 104 - "create_host"
Cohesion: 0.24
Nodes (12): _assert_endpoint_allowed(), _assert_name_free(), create_host(), endpoint_scheme(), Request, UUID, Register a docker host; names are unique across hosts., Apply a partial update built from an ``exclude_unset`` payload. (+4 more)

### Community 105 - "redis service (Redis 7, no persistence, loopback :6390)"
Cohesion: 0.22
Nodes (11): redis service (Redis 7, no persistence, loopback :6390), WebSocket API (/api/v1/ws handshake, frames, limits), WebSocket channels (global, server-metrics, container-logs, deployment-logs, incidents), Deployment engine (queue_deployment / execute_deployment / sweeper backstop), Real-time spine: PostgreSQL system_events + Redis pub/sub, Rollback as a new deployment (rollback_of_id), WebSocket hub (framework-thin, Redis fan-in, per-socket queues), Test suites (pytest unit+integration, vitest, Playwright e2e) (+3 more)

### Community 106 - "NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)"
Cohesion: 0.18
Nodes (12): Agent security model (one-way telemetry, no command channel), Agent enrollment token (X-Agent-Token, nxa_..., SHA-256 at rest), Agent heartbeat exponential backoff (cap 5 min, exit 1 on revoked token), agent/install.sh (enrollment installer), Agent metrics collection (/proc statvfs Docker socket), NexusOps agent (stdlib-only Python, agent/nexusops_agent.py), Agent systemd hardening (ProtectSystem=strict, NoNewPrivileges), Agent ingest API (POST /agent/hello, POST /agent/heartbeat) (+4 more)

### Community 107 - "DockerProviderError"
Cohesion: 0.13
Nodes (17): clip(), DockerProviderError, LogLine, datetime, Exception, Provider abstraction for docker hosts (real daemon or simulated). Providers are…, Yield parsed log lines. With ``follow=True`` the stream never ends., A provider operation failed. ``str()`` is safe to show/log. (+9 more)

### Community 108 - "register_exception_handlers"
Cohesion: 0.12
Nodes (13): _error_payload(), Any, FastAPI, Request, register_exception_handlers(), handle_app_error(), handle_http_exception(), handle_unexpected() (+5 more)

### Community 109 - "Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)"
Cohesion: 0.25
Nodes (9): API keys (X-API-Key, nxo_..., scope intersection), First boot sequence (api entrypoint migrates, compose never seeds), Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test), Makefile workflows (up/test/lint/typecheck/migrate/seed), HIGH finding: API-key scope bypass for superadmin-owned keys (fixed: scope intersection first), Security audit 2026-09 (26 raw findings -> 20 confirmed, all fixed), HIGH finding: known seed superadmin + API key backdoor (fixed: NEXUSOPS_ALLOW_SEED opt-in, one-time password), Threat model (edge attacker, malicious agent, curious operator, leaked token, SSRF) (+1 more)

### Community 110 - "_FakeAsyncClient"
Cohesion: 0.22
Nodes (3): _FakeAsyncClient, _FakeRequestObj, Scripted httpx.AsyncClient: responses keyed by absolute request URL.

### Community 112 - "create_app"
Cohesion: 0.35
Nodes (9): create_app(), _app_for_environment(), MonkeyPatch, ENVIRONMENT gating contract: docs exposure and HSTS (see .env.example).…, create_app() with get_settings() patched to the given environment., test_non_production_does_not_emit_hsts(), test_non_production_keeps_docs_and_schema(), test_production_emits_hsts() (+1 more)

### Community 113 - "collect_recent_logs"
Cohesion: 0.09
Nodes (21): collect_recent_logs(), Pull recent logs from running containers of a real host. Simulated hosts are…, append_lines(), count_container_logs(), detect_level(), _entry_values(), ingest_provider_lines(), publish_log_line() (+13 more)

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "ContainerListPage.test.tsx"
Cohesion: 0.29
Nodes (3): ApiError, server, serversPage

### Community 116 - "config.py"
Cohesion: 0.20
Nodes (8): fail_on_bad_config(), Central configuration. All runtime configuration flows through this module so…, Exit immediately with a readable message if configuration is invalid., Celery application: periodic cadences live here, dynamic work is claimed…, celery, celery_schedules, cryptography_fernet, pydantic_settings

### Community 117 - "Platform Vision — NexusOps"
Cohesion: 0.20
Nodes (10): 1. Where NexusOps is today, 2.1 What we are NOT building, 2.2 The wedge (differentiation), 2. The direction, 3. Guiding principles, 4. Customer journey (target), 5.1 Architecture overview (target), 5. Control plane / data plane boundary (+2 more)

### Community 118 - "dependencies"
Cohesion: 0.33
Nodes (6): dependencies, lucide-react, react, react-dom, react-router-dom, @tanstack/react-query

### Community 120 - "generate_secrets.sh"
Cohesion: 0.47
Nodes (3): existing_real_keys(), replace_or_append(), generate_secrets.sh script

### Community 121 - "get_meta"
Cohesion: 0.40
Nodes (5): get_meta(), DbSessionDep, get, Public metadata; identity fields appear only for valid credentials., OptionalUser

### Community 122 - "SecretOut"
Cohesion: 0.22
Nodes (9): Secret metadata — deliberately excludes any value-bearing field., SecretOut, 1.1 Storage and crypto, 1.2 Data model, 1.3 API surface (metadata-only reads), 1.5 SILENT DEGRADE BUG (must-fix), 1.6 Current-state gap list, 1. Current state (+1 more)

### Community 123 - "router.py"
Cohesion: 0.40
Nodes (4): websocket, WebSocket endpoint. Mounted by the app factory under ``/api/v1``., Hand the socket to the hub (auth handshake handled there)., websocket_endpoint()

### Community 124 - "Multi-Tenancy Architecture"
Cohesion: 0.22
Nodes (9): 1. Tenancy invariants, 3. The session guard (the mechanical layer), 4. Background jobs, 5. WebSockets, 6. Agents, 7. The IDOR suite, 8. What stays global, 9. Migration (Phase 1) (+1 more)

### Community 125 - "DeploymentRunner"
Cohesion: 0.25
Nodes (6): DeploymentRunner, Protocol, Adapter interface implemented by real (future) and simulated runners., Return the ordered step names for this run., Stream output lines for *step_name*; raise StepFailure to fail it., 2. What survives unchanged

### Community 146 - "StepFailure"
Cohesion: 0.25
Nodes (7): Exception, Raised by a runner when a step fails irrecoverably., StepFailure, 5.1 Operation whitelist additions (deployments), 5.2 `RunContext` extension, 5. `AgentDeploymentRunner` — real execution over agent operations, 9. Cancellation and per-step timeouts

### Community 147 - "simulation_tick"
Cohesion: 0.33
Nodes (7): _containers_for(), task, Deterministic smooth value in [base-amplitude, base+amplitude]., Stable per-server container set; one container cycles EXITED occasionally., simulation_tick(), _run(), _wave()

### Community 148 - "postgres service (PostgreSQL 17, loopback :5433)"
Cohesion: 0.29
Nodes (7): postgres service (PostgreSQL 17, loopback :5433), Fernet encryption at rest (ENCRYPTION_KEY, write-once), Backups (pgdata volume, nightly pg_dump, ephemeral Redis), Required secrets (POSTGRES_PASSWORD, JWT_SECRET >= 32 chars, ENCRYPTION_KEY Fernet), Production hardening checklist (secrets, ENVIRONMENT, no seed, TLS, rotation), Compose vs host network namespaces (postgres:5432 vs 127.0.0.1:5433), Simulation mode (SIMULATION_MODE)

### Community 149 - "role.py"
Cohesion: 0.33
Nodes (5): PermissionOut, Role and permission-registry schemas., PATCH semantics: ``None`` means "leave unchanged"., RoleCreateRequest, RoleUpdateRequest

### Community 150 - "nexusops-understand.mjs"
Cohesion: 0.33
Nodes (5): COMMON, meta, out, READERS, SCHEMA

### Community 151 - "Invisible account lockout (5 fails -> 15 min, enumeration resistance)"
Cohesion: 0.33
Nodes (6): Invisible account lockout (5 fails -> 15 min, enumeration resistance), Unified error envelope (code, message, request_id), Per-IP rate limiting (Redis fixed window), Request lifecycle (edge -> middleware -> rate limit -> deps -> router), Client IP resolution (resolve_client_ip, TRUSTED_PROXY_CIDRS, XFF overwrite), EmailStr rejects reserved domains (login 422 on .test/.local/.arpa)

### Community 152 - "validate_endpoint_url"
Cohesion: 0.50
Nodes (3): model_validator, Validate/normalize an endpoint URL against the scheme allowlist., validate_endpoint_url()

### Community 153 - "instant_pacing"
Cohesion: 0.40
Nodes (4): instant_pacing(), fixture, MonkeyPatch, Remove the per-line sleeps; pacing bounds are asserted separately.

### Community 154 - "nexusops-draft.mjs"
Cohesion: 0.40
Nodes (4): DOCS, meta, SPINE, VERIFY_RULES

### Community 155 - "6. Agent security"
Cohesion: 0.40
Nodes (5): 6.1 Token scope, 6.2 docker.sock is root-equivalent, 6.3 Transport: HTTPS-only, 6.4 No arbitrary exec, 6. Agent security

### Community 156 - "create_docker_host"
Cohesion: 0.50
Nodes (4): create_docker_host(), post, Register a host. Endpoint allowlist: unix://, tcp://, sim:// or ''., _CreatePerm

### Community 157 - "configure_logging"
Cohesion: 0.50
Nodes (4): configure_logging(), _orjson_dumps(), Any, Configure structlog + stdlib logging once at process start. Everything…

### Community 158 - "effective_permissions"
Cohesion: 0.67
Nodes (3): effective_permissions(), User, Sorted explicit permission codenames for a user; ``*`` expands to the registry.

### Community 159 - "sweep_servers"
Cohesion: 0.67
Nodes (3): task, Flag silent servers OFFLINE, recover returning ones. Safe to overlap., sweep_servers()

### Community 160 - "run_due_monitors"
Cohesion: 0.67
Nodes (3): task, Claim up to CLAIM_BATCH due monitors and execute each check.…, run_due_monitors()

## Knowledge Gaps
- **391 isolated node(s):** `meta`, `SPINE`, `VERIFY_RULES`, `DOCS`, `meta` (+386 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1424 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **24 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AuthContext` connect `AuthContext` to `APIModel`, `deps.py`, `project_service.py`, `incidents.py`, `deployment_engine.py`, `PageParams`, `containers.py`, `get_latest_server_metrics`, `monitor_service.py`, `main.py`, `auth_service.py`, `container_service.py`, `DockerHost`, `NotFound`, `monitors.py`, `server_service.py`, `v1/channels.py`, `v1/deployments.py`, `test_permissions.py`, `servers.py`, `role_service.py`, `NotificationChannel`, `rotate_secret`, `enums.py`, `middleware.py`, `notification_service.py`, `Hub`, `require_permission`, `docker_hosts.py`, `scope_matches`, `resolve_auth`, `publish`, `create_host`?**
  _High betweenness centrality (0.050) - this node is a cross-community bridge._
- **Why does `docs/architecture.md - system architecture` connect `docs/architecture.md - system architecture` to `docs/engineering-report.md - build and verification report`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Why does `docs/troubleshooting.md - symptom -> cause -> fix runbook` connect `docs/engineering-report.md - build and verification report` to `Invisible account lockout (5 fails -> 15 min, enumeration resistance)`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Are the 73 inferred relationships involving `AuthContext` (e.g. with `list_audit_logs()` and `_optional_actor()`) actually correct?**
  _`AuthContext` has 73 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `apiGet()` (e.g. with `ContainerDetailPage.test.tsx` and `mockApi()`) actually correct?**
  _`apiGet()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `meta`, `SPINE`, `VERIFY_RULES` to the rest of the system?**
  _391 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ApiError` be split into smaller, more focused modules?**
  _Cohesion score 0.02635529608006672 - nodes in this community are weakly interconnected._