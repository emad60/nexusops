# Graph Report - nexusops  (2026-09-22)

## Corpus Check
- 271 files · ~226,498 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: (none) 8, .example 1, .service 1)

## Summary
- 3638 nodes · 10666 edges · 170 communities (147 shown, 23 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 876 edges (avg confidence: 0.94)
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
- StepLine
- models/__init__.py
- AuthContext
- ServerDetailPage.tsx
- v1/health.py
- client.ts
- projects.py
- incidents.py
- deployment_engine.py
- SimulatedDockerProvider
- maintenance.py
- v1/deployments.py
- test_deployments_simulated.py
- list_containers
- metrics_service.py
- get_settings
- Domain Routing — NexusOps
- monitor_service.py
- Node & Agent Architecture
- test_agent_backoff.py
- containers.py
- nexusops_agent.py
- integration/conftest.py
- auth_service.py
- container_service.py
- types.ts
- docker_host_service.py
- test_pagination.py
- monitors.py
- v1/search.py
- server_service.py
- list_deliveries
- DockerProvider
- test_monitor_transport.py
- test_agent_contract.py
- cancel_deployment
- docker_real.py
- test_permissions.py
- DockerHostsPage.tsx
- servers.py
- test_ssrf.py
- create_secret
- role_service.py
- test_schemas_server.py
- create_api_key
- publish
- test_schemas_agent.py
- monitor_transport.py
- rotate_secret
- alembic
- v1/channels.py
- test_auth_journey.py
- compilerOptions
- enums.py
- middleware.py
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
- list_alerts
- incident_service.py
- role.py
- ApiKeysPage.tsx
- scope_matches
- Settings
- .from_user
- rate_limit.py
- container.py
- Product Roadmap — NexusOps Multi-Tenant Platform
- devDependencies
- logging.py
- seed.py
- get_meta
- get_logger
- Deployment Architecture — NexusOps (target state)
- test_notifications.py
- get_redis
- get_sessionmaker
- pytest
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- journey.spec.ts
- README.md - NexusOps overview
- 2. Entities
- Secrets Architecture
- encrypt_str
- list_sessions
- tests/conftest.py
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- run_async
- register_exception_handlers
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- _FakeAsyncClient
- require_permission
- create_app
- log_service.py
- scripts
- ContainerListPage.tsx
- EnvironmentUpdate
- simulation.py
- dependencies
- FakeWebSocket
- generate_secrets.sh
- StepFailure
- test_servers_and_audit.py
- hub.py
- list_audit_logs
- DeploymentRunner
- APIModel
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
- resolve_auth
- instant_pacing
- nexusops-draft.mjs
- assert_error_code
- nexusops-challenge.mjs
- test_agent_ingestion.py
- tasks/deployments.py
- collect_container_stats
- AgentClient
- validate_endpoint_url
- 8. Upstream binding and re-render triggers
- _transport_is_https
- permissions.py
- agent_heartbeat
- 4. ACME architecture
- me
- _pace
- 1. Current state

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
10. `@tanstack/react-query` - 51 edges

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

## Communities (170 total, 23 thin omitted)

### Community 0 - "ApiError"
Cohesion: 0.02
Nodes (101): ApiError, setAccessToken(), DockerHostOut, Role, SearchResult, SessionInfo, User, AuthContext (+93 more)

### Community 1 - "v1/auth.py"
Cohesion: 0.15
Nodes (32): change_password(), _clear_refresh_cookie(), _cookies_secure(), login(), logout(), DbSessionDep, post, Request (+24 more)

### Community 2 - "App.tsx"
Cohesion: 0.05
Nodes (70): DeploymentStepOut, EnvironmentOut, IncidentEventOut, ProjectOut, AuditLogPage, ContainerDetailPage, DeploymentDetailPage, DeploymentListPage (+62 more)

### Community 3 - "apiGet"
Cohesion: 0.06
Nodes (64): apiDelete(), apiGet(), apiPatch(), apiPost(), ApplicationOut, AlertsPage, ProjectDetailPage, RolesPage (+56 more)

### Community 4 - "NotFound"
Cohesion: 0.09
Nodes (47): NotFound, paginate(), AsyncSession, Execute *stmt* with limit/offset and return ``(rows, total)``., EventLevel, list_api_keys(), AsyncSession, UUID (+39 more)

### Community 5 - "deps.py"
Cohesion: 0.11
Nodes (37): FastAPI dependencies: database session, authentication context, RBAC gate.…, Agent ingest endpoints: enrollment handshake and periodic heartbeats.…, Alert inbox endpoints. Authenticated users see the shared operator feed., API key routes — self-service management of the caller's own machine…, Audit log API. Strictly read-only: the table is append-only by design., Instance metadata: version, mode, and the caller's effective capabilities. The…, Metrics query API: server timeseries, latest snapshot, dashboard summary., Role management and permission-registry routes (role.read / role.manage). (+29 more)

### Community 6 - "resolve_client_ip"
Cohesion: 0.17
Nodes (22): _is_trusted(), _parse_networks(), Request, Client-IP resolution behind chained reverse proxies. The API never takes TCP…, Parse a comma-separated CIDR list; malformed entries are skipped., Real client address for *request* per the trust model above., resolve_client_ip(), make_request() (+14 more)

### Community 7 - "docker_hosts.py"
Cohesion: 0.09
Nodes (47): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+39 more)

### Community 8 - "StepLine"
Cohesion: 0.26
Nodes (8): LogLevel, _commit_short(), Deployment runner port plus a faithful simulated implementation.…, Everything a runner needs to execute one deployment., One streamed output line for a step., RunContext, _slug(), StepLine

### Community 9 - "models/__init__.py"
Cohesion: 0.11
Nodes (40): Base, big_serial_pk(), json_column(), datetime, UUID, Declarative base, shared mixins and column helpers., Base for all ORM models with stable constraint naming for Alembic., Identity PK for very high-volume tables (metrics, logs). (+32 more)

### Community 10 - "AuthContext"
Cohesion: 0.14
Nodes (43): AuthContext, Resolved identity attached to every authenticated request., EnvironmentCreate, Payload to create an environment under an application., Any, AsyncSession, Request, Append an audit row using the caller's transaction (no commit here). Sensitive… (+35 more)

### Community 11 - "ServerDetailPage.tsx"
Cohesion: 0.09
Nodes (34): MetricPoint, ServerDetailPage, ChartSeries, LineChart(), LineChartProps, PAD, buildServerPayload(), EMPTY_SERVER_FORM (+26 more)

### Community 12 - "v1/health.py"
Cohesion: 0.20
Nodes (13): liveness(), get, Response, Health probes: liveness (always cheap) and readiness (checks dependencies).…, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness(), HealthOut (+5 more)

### Community 13 - "client.ts"
Cohesion: 0.05
Nodes (47): API_BASE, apiRequest(), buildUrl(), extractError(), getAccessToken(), refreshToken(), RequestOptions, DashboardSummary (+39 more)

### Community 14 - "projects.py"
Cohesion: 0.10
Nodes (53): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+45 more)

### Community 15 - "incidents.py"
Cohesion: 0.13
Nodes (34): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+26 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.11
Nodes (54): deployment_log_channel(), Deployment, DeploymentStep, DeploymentStatus, StepStatus, _after_commit_enqueue(), _after_rollback_drop(), _audit_resolution_failed() (+46 more)

### Community 17 - "SimulatedDockerProvider"
Cohesion: 0.07
Nodes (36): ContainerHealth, ContainerStatus, Container, Observed container state mirrored from an agent or docker provider., Any, datetime, Simulated docker provider for demo and test environments. The provider is…, Plausible numbers derived from the row plus time-based sine noise. (+28 more)

### Community 18 - "maintenance.py"
Cohesion: 0.15
Nodes (23): _run(), _run(), aggregate_metrics(), _run(), _collect_logs(), expire_sessions(), _run(), task (+15 more)

### Community 19 - "v1/deployments.py"
Cohesion: 0.17
Nodes (24): _attribute_step_idx(), _emails_for(), get_deployment(), list_application_deployments(), list_deployment_logs(), _list_deployments(), _parse_sort(), _parse_statuses() (+16 more)

### Community 20 - "test_deployments_simulated.py"
Cohesion: 0.15
Nodes (26): execute_deployment(), Run one deployment to a terminal state. Never raises; safe to re-run., get_environment(), _delivery_chain(), _owner_ctx(), _queue(), _queued_with_recorder(), Deployment engine over the simulated runner: success, failure, rollback. (+18 more)

### Community 21 - "list_containers"
Cohesion: 0.12
Nodes (23): get_container(), _like_pattern(), list_container_logs(), list_containers(), alias, DbSessionDep, delete, Depends (+15 more)

### Community 22 - "metrics_service.py"
Cohesion: 0.09
Nodes (41): get_dashboard_summary(), get_latest_server_metrics(), get_server_metrics(), CurrentUser, DbDep, Depends, get, UUID (+33 more)

### Community 23 - "get_settings"
Cohesion: 0.08
Nodes (47): argon2, argon2_exceptions, AsyncEngine, get_settings(), Return the cached settings singleton., get_engine(), Unauthorized, create_access_token() (+39 more)

### Community 24 - "Domain Routing — NexusOps"
Cohesion: 0.09
Nodes (23): 10. Wildcards and catch-all, 11. User journey, 12. API surface, permissions, audit, 13. Monitoring tie-in, 1. Scope and current state, 2. Where nginx runs, 3.1 Domain, 3.2 Route (+15 more)

### Community 25 - "monitor_service.py"
Cohesion: 0.15
Nodes (38): assert_safe_url_async(), Async wrapper around :func:`assert_safe_url`; DNS runs off the loop., MonitorStatus, Monitor, MonitorCheck, _active_incident(), _audit(), claim_due_monitors() (+30 more)

### Community 26 - "Node & Agent Architecture"
Cohesion: 0.09
Nodes (22): 1. Scope and stance, 2.1 Current shape (real), 2.2 Changes for the target model, 2.3 Capabilities (target), 2. The Node concept, 5.1 Model and lifecycle, 5.2 Whitelisted operation types, 5.3 Result reporting and audit (+14 more)

### Community 27 - "test_agent_backoff.py"
Cohesion: 0.16
Nodes (20): agent_fixture(), _install_sleep(), fake_sleep(), _load_agent(), _patch_host(), Any, fixture, MonkeyPatch (+12 more)

### Community 28 - "containers.py"
Cohesion: 0.15
Nodes (23): _action_route(), _endpoint(), _decode_frame(), _ev(), _load_container(), _max_log_id(), _perform_action(), _poll_new_lines() (+15 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.11
Nodes (24): build_heartbeat(), cpu_percent_since(), disk_stats(), _interruptible_sleep(), load1(), main(), memory_stats(), memory_total_mb() (+16 more)

### Community 30 - "integration/conftest.py"
Cohesion: 0.16
Nodes (17): alembic_config, _clean_slate(), client(), _ensure_database(), _migrated_database(), owner(), AsyncClient, fixture (+9 more)

### Community 31 - "auth_service.py"
Cohesion: 0.12
Nodes (36): Opaque refresh token; only its SHA-256 hash is stored. Rotation chain: on…, RefreshToken, _audit(), change_own_password(), count_users(), _event(), _grace_successor(), _issue_access() (+28 more)

### Community 32 - "container_service.py"
Cohesion: 0.09
Nodes (41): clip(), DockerProviderError, Exception, Provider abstraction for docker hosts (real daemon or simulated). Providers are…, A provider operation failed. ``str()`` is safe to show/log., Build a compact, secret-free description of a provider failure. Only the…, Truncate *text* to *limit* characters, stripping control chars., sanitize_error() (+33 more)

### Community 33 - "types.ts"
Cohesion: 0.05
Nodes (45): AlertOut, AuditEntry, ChannelOut, CheckOut, ContainerOut, CursorPage, DeliveryOut, DeploymentLogLine (+37 more)

### Community 34 - "docker_host_service.py"
Cohesion: 0.13
Nodes (35): DockerHostStatus, DockerHost, DockerHostPingOut, DockerHostUpdate, Result of probing a host's provider endpoint., Partial update payload; only supplied fields change., _assert_endpoint_allowed(), _assert_name_free() (+27 more)

### Community 35 - "test_pagination.py"
Cohesion: 0.15
Nodes (22): Cursor, cursor_params(), CursorPage, CursorParams, decode_cursor(), encode_cursor(), BaseModel, datetime (+14 more)

### Community 36 - "monitors.py"
Cohesion: 0.14
Nodes (38): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+30 more)

### Community 37 - "v1/search.py"
Cohesion: 0.09
Nodes (41): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+33 more)

### Community 38 - "server_service.py"
Cohesion: 0.08
Nodes (55): server_metrics_channel(), generate_agent_token(), ServerStatus, Server, Tag, _actor_kwargs(), _apply_agent_entry(), container_counts() (+47 more)

### Community 39 - "list_deliveries"
Cohesion: 0.19
Nodes (21): create_channel(), delete_channel(), get_channel(), list_channels(), list_deliveries(), DbDep, delete, Depends (+13 more)

### Community 40 - "DockerProvider"
Cohesion: 0.08
Nodes (12): DockerProvider, Any, datetime, Protocol, List containers visible to the provider., Inspect a single container by id (short ids allowed)., List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``., List volumes: keys ``name``, ``driver``, ``mountpoint``. (+4 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.13
Nodes (34): CheckResult, HTTPMonitorTransport, Deterministic fake checker for ``sim://`` monitors and demo environments.…, Real HTTP(S) probe using httpx with per-monitor settings. Redirects are…, SimulatedTransport, _check(), clock(), FakeClock (+26 more)

### Community 42 - "test_agent_contract.py"
Cohesion: 0.18
Nodes (16): agent_fixture(), _load_agent(), _patch_stats(), Any, fixture, MonkeyPatch, Contract tests: the shipped agent's payloads must satisfy the ingest schemas.…, One-shot docker stats reduce to cpu/mem/limit fields the schema accepts, with… (+8 more)

### Community 43 - "cancel_deployment"
Cohesion: 0.21
Nodes (10): cancel_deployment(), post, Request, Cancel a QUEUED deployment immediately or flag a RUNNING one., Queue a rollback to the last good version of this app/environment., rollback_deployment(), Any, Serialize a deployment ORM row; ``dep.steps`` must be pre-loaded. (+2 more)

### Community 44 - "docker_real.py"
Cohesion: 0.09
Nodes (27): ContainerInfo, ContainerStats, Normalized view of a container as reported by any provider., Point-in-time resource usage snapshot., _as_float(), _compute_stats(), _cpu_percent(), _network_bytes() (+19 more)

### Community 45 - "test_permissions.py"
Cohesion: 0.17
Nodes (9): permission_exists(), _auth_context(), Unit tests for the permission registry, scope matching and RBAC gate., test_api_key_scope_intersects_role_permissions(), test_permission_exists_helper(), test_plain_user_without_permissions_is_denied(), test_superadmin_bypasses_everything(), test_superadmin_owned_api_key_is_limited_to_its_scope() (+1 more)

### Community 46 - "DockerHostsPage.tsx"
Cohesion: 0.05
Nodes (43): SecretRow, App(), DockerHostsPage, LoginPage, SecretsPage, CheckboxField(), CheckboxFieldProps, FieldAria (+35 more)

### Community 47 - "servers.py"
Cohesion: 0.09
Nodes (37): create_server(), delete_server(), _detail(), get_server(), list_servers(), list_tags(), AsyncSession, DbDep (+29 more)

### Community 48 - "test_ssrf.py"
Cohesion: 0.07
Nodes (61): BadRequest, UnprocessableEntity, assert_safe_tcp_endpoint(), assert_safe_url(), _is_forbidden_address(), is_simulation_url(), _raise_block(), SSRF guard applied to every operator-supplied outbound URL. Monitors and… (+53 more)

### Community 49 - "create_secret"
Cohesion: 0.16
Nodes (22): _actor_type(), _collect_refs(), create_secret(), delete_secret(), _detail(), get_secret(), get_secret_detail(), list_secrets() (+14 more)

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
Cohesion: 0.17
Nodes (21): ActorType, SystemEvent, create_api_key(), Request, Validate + normalise scopes; returns the deduplicated list. Accepts exact…, Create a key for *user_id*. Returns ``(row, raw_key)`` — raw shown once., validate_scopes(), _after_commit_publish() (+13 more)

### Community 54 - "test_schemas_agent.py"
Cohesion: 0.15
Nodes (27): AgentContainerIn, AgentHeartbeatIn, AgentHelloIn, field_validator, First contact from an agent after enrollment; fills static host facts., Observed container state reported by an agent., Periodic metrics + observed containers from an enrolled agent., _container() (+19 more)

### Community 55 - "monitor_transport.py"
Cohesion: 0.08
Nodes (24): CheckOutcome, coerce_headers(), _decode(), get_transport(), MonitorTransport, Any, BaseException, Protocol (+16 more)

### Community 56 - "rotate_secret"
Cohesion: 0.16
Nodes (21): create_secret(), delete_secret(), get_secret(), list_secrets(), DbSession, delete, Depends, get (+13 more)

### Community 58 - "v1/channels.py"
Cohesion: 0.19
Nodes (15): Notification channel endpoints. Config is write-only; never echoed back., # NOTE: /deliveries is declared before /{channel_id} so the literal wins., ChannelType, DeliveryStatus, ChannelBase, ChannelCreate, ChannelOut, ChannelUpdate (+7 more)

### Community 59 - "test_auth_journey.py"
Cohesion: 0.16
Nodes (22): cookie_attributes(), login_account(), Response, The raw Set-Cookie header carrying the refresh token., Extract just the opaque token from a Set-Cookie header., Parse Set-Cookie attributes (lowercased keys, empty string for flags)., Login and unpack tokens, the raw cookie header and the user object., refresh_cookie_header() (+14 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "enums.py"
Cohesion: 0.25
Nodes (10): Queue a new deployment for an application/environment pair., trigger_deployment(), AuditResult, CredentialKind, DeploymentTrigger, Closed registries of domain enumerations. Member names equal their values…, String enum; member names equal values so name/value storage never disagrees., StrEnum (+2 more)

### Community 62 - "middleware.py"
Cohesion: 0.13
Nodes (15): ASGIApp, UUID, AccessLogMiddleware, Request, Response, HTTP middleware: request ids, security headers, structured access logs., Baseline hardening headers on every API response., RequestIDMiddleware (+7 more)

### Community 63 - "alert_service.py"
Cohesion: 0.21
Nodes (16): AlertSeverity, Alert, create_alert(), get_alert(), mark_all_read(), mark_read(), AsyncSession, UUID (+8 more)

### Community 64 - "SimulatedDeploymentRunner"
Cohesion: 0.25
Nodes (23): Staged docker-style simulation used by v1 deployments., Canonical step identifiers stored on :class:`DeploymentStep` rows., SimulatedDeploymentRunner, StepName, _collect(), _ctx(), Unit tests for SimulatedDeploymentRunner (async generators, no broker)., RESOLVE_CONFIG is planned by the engine, not produced by a runner. (+15 more)

### Community 65 - "notification_sender.py"
Cohesion: 0.16
Nodes (17): NotificationError, Any, BaseException, Exception, Low-level notification transports: SMTP email and outgoing webhooks. These…, POST *payload* as JSON to *url*; 2xx is success, anything else raises. Response…, Raised when a delivery attempt fails. Message is safe to persist., Bounded, single-line, content-free error reason. (+9 more)

### Community 66 - "test_schema_redaction.py"
Cohesion: 0.18
Nodes (17): is_sensitive_header(), mask_sensitive_headers(), True when *name* looks like it carries a credential (Authorization etc.)., Return a copy of *headers* with sensitive values replaced by a mask., mask_target(), Human-readable masked target safe to expose over the API. For webhook families…, _monitor_out(), Outbound-schema redaction: monitor probe credentials and webhook targets.… (+9 more)

### Community 67 - "NotificationChannel"
Cohesion: 0.20
Nodes (20): NotificationChannel, A delivery target (email address / webhook endpoint). ``config_ciphertext``…, EmailConfig, WebhookConfig, _audit(), create_channel(), decrypt_channel_config(), delete_channel() (+12 more)

### Community 68 - "Hub"
Cohesion: 0.10
Nodes (23): _close_socket(), Connection, _entity_exists(), Hub, _is_same_origin(), _params_key(), _parse_payload(), Any (+15 more)

### Community 69 - "package.json"
Cohesion: 0.13
Nodes (15): name, private, type, version, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom (+7 more)

### Community 70 - "events.py"
Cohesion: 0.10
Nodes (26): _decode_cursor(), _encode_cursor(), list_event_types(), list_events(), datetime, DbSession, Depends, get (+18 more)

### Community 71 - "test_secrets.py"
Cohesion: 0.10
Nodes (28): Exception, A ``${secret:KEY}`` reference could not be resolved. Fail-closed. Carries…, One successfully resolved reference: metadata for audit, no value., Outcome of resolving an environment's config references., Resolve every ``${secret:KEY}`` reference in an environment's config. INTERNAL…, resolve_secrets_for_environment(), ResolvedSecrets, SecretReference (+20 more)

### Community 72 - "Platform Security Model — NexusOps"
Cohesion: 0.11
Nodes (18): 10.1 Node revocation playbook (compromised node / leaked agent token), 10.2 Key compromise playbook, 10. Incident response, 1.1 Real vs simulated today (do not mistake one for the other), 1. Scope, stance, and simulation honesty, 2. Assets, 3. Trust boundaries, 4. Tenant isolation model (summary) (+10 more)

### Community 73 - "notification_service.py"
Cohesion: 0.20
Nodes (20): _as_uuid(), decode_delivery_cursor(), dispatch_event_frame(), _send(), dispatcher_loop(), encode_delivery_cursor(), list_deliveries(), _now() (+12 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "config.py"
Cohesion: 0.15
Nodes (14): _database_url(), Alembic environment: metadata comes from app.models, URL from app settings., Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online(), fail_on_bad_config(), Central configuration. All runtime configuration flows through this module so… (+6 more)

### Community 76 - "list_alerts"
Cohesion: 0.21
Nodes (14): list_alerts(), mark_all_read(), mark_read(), CurrentUser, DbDep, Depends, get, post (+6 more)

### Community 77 - "incident_service.py"
Cohesion: 0.23
Nodes (22): IncidentEventKind, IncidentStatus, Incident, acknowledge(), _add_event(), add_note(), get_incident(), list_incidents() (+14 more)

### Community 78 - "role.py"
Cohesion: 0.10
Nodes (27): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, delete, get (+19 more)

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
Nodes (18): create_user(), deactivate_user(), get_user(), list_users(), CurrentUser, DbSessionDep, delete, get (+10 more)

### Community 83 - "rate_limit.py"
Cohesion: 0.17
Nodes (18): RateLimited, _memory_count_and_ttl(), rate_limit(), _dependency(), Redis-backed fixed-window rate limiting as a FastAPI dependency factory. Auth-…, Fixed-window counter backed by process memory. Returns (count, ttl)., Return a dependency enforcing *limit* requests per window per IP. With…, _clean_memory_windows() (+10 more)

### Community 84 - "container.py"
Cohesion: 0.15
Nodes (18): _container_out(), Serialize one row; env values never leave the database (keys only)., ContainerDetailOut, ContainerOut, ContainerRemoveOut, host_ref(), HostRef, LogEntryOut (+10 more)

### Community 85 - "Product Roadmap — NexusOps Multi-Tenant Platform"
Cohesion: 0.14
Nodes (14): 0. Stance, 10. Phase 7 — Teams, grants & custom roles, 11. Phase 8 — Backups, 12. Phase 9 — Billing & metering, 14. Biggest risks (short form), 15. Reading order, 2. Phase plan, 4. Phase 1 — Tenancy foundation (+6 more)

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "logging.py"
Cohesion: 0.14
Nodes (19): configure_logging(), _is_sensitive_key(), _orjson_dumps(), Any, Structured logging via structlog. Every log record carries timestamp, level,…, Substring match on a normalised key so header-style names are caught too.…, Return a copy of *data* with sensitive values replaced. Used by audit metadata…, Configure structlog + stdlib logging once at process start. Everything… (+11 more)

### Community 88 - "seed.py"
Cohesion: 0.19
Nodes (20): DeploymentEnvironment, Project, ApiKey, Machine credential. Raw key shown once at creation; hash stored., An encrypted configuration value. The plaintext is never returned by the API…, Secret, _lock(), datetime (+12 more)

### Community 89 - "get_meta"
Cohesion: 0.40
Nodes (5): get_meta(), DbSessionDep, get, Public metadata; identity fields appear only for valid credentials., OptionalUser

### Community 90 - "get_logger"
Cohesion: 0.12
Nodes (15): asyncio, get_logger(), Celery application: periodic cadences live here, dynamic work is claimed…, task, Heartbeat sweeps: offline detection and recovery for servers., Flag silent servers OFFLINE, recover returning ones. Safe to overlap., sweep_servers(), task (+7 more)

### Community 91 - "Deployment Architecture — NexusOps (target state)"
Cohesion: 0.14
Nodes (14): 10. Events and WS during runs, 11. Post-deploy hooks, 12. Rollback semantics (existing behavior kept), 13. The simulated runner stays — labeled, 14. Open questions, 1. Current state — what is real and what is simulated, 3. Target pipeline, 4. Runner registry — the DI fix (+6 more)

### Community 92 - "test_notifications.py"
Cohesion: 0.36
Nodes (9): NotificationDelivery, _channel(), _delivery(), UUID, Notification channel + delivery-log endpoints. Regression coverage for GET…, The same event frame consumed twice queues ONE delivery per channel. Every API…, test_dispatch_frame_is_idempotent_across_workers(), test_list_deliveries_filters_by_channel() (+1 more)

### Community 93 - "get_redis"
Cohesion: 0.23
Nodes (12): get_redis(), ping(), Shared async Redis client., _next_data_message(), Event bus fan-out ordering: a frame follows its transaction, never leads it.…, Regression: a rollback must drop stashed frames, not defer them. The stash…, test_frame_published_only_after_commit(), test_rolled_back_event_never_publishes() (+4 more)

### Community 94 - "get_sessionmaker"
Cohesion: 0.18
Nodes (11): async_sessionmaker, get_sessionmaker(), AsyncSession, The docker-host maintenance sweep must actually reach real hosts., Re-collection stores only lines newer than the newest stored row. The sweep re-…, Regression: the sweep called asyncio.run() inside its own running loop, so…, The sweep and a heartbeat can both see a brand-new container in the same…, test_collect_recent_logs_is_incremental() (+3 more)

### Community 95 - "pytest"
Cohesion: 0.21
Nodes (10): created_at server defaults must evaluate per insert, not at table creation., Regression: system_events and audit_logs shipped with DEFAULT 'now()' (quoted…, test_audit_and_event_created_at_defaults_are_dynamic(), _create_monitor(), Monitor checks driving the full down -> incident -> recovery lifecycle., Regression: probe headers and URL query credentials never leave the API. Probe…, test_check_now_endpoint_runs_immediately(), test_down_then_recover_lifecycle() (+2 more)

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
Cohesion: 0.15
Nodes (13): 10. Resolution flow at deploy time, 2.1 Resolution runs inside org scope, 2.2 Migration mapping, 2. Target scope model (org / project / environment layering), 3.1 What this fixes, 3. SecretVersion — append-only history, 4.1 Audit event at resolution time, 4. Resolution authorization (+5 more)

### Community 102 - "encrypt_str"
Cohesion: 0.10
Nodes (26): decrypt_str(), digest_of(), encrypt_str(), _fernet(), Short server-verifiable digest used for change detection display. HMAC-SHA256…, test_notification_pipeline_queues_delivery_for_down_event(), parametrize, test_decrypt_with_wrong_ciphertext_raises_value_error() (+18 more)

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

### Community 107 - "run_async"
Cohesion: 0.27
Nodes (12): Any, T, Run *coroutine* on a dedicated event loop (Celery workers are sync)., run_async(), _answer(), _boom(), _nested(), Unit tests for the Celery-task async bridge (pure asyncio, no broker). (+4 more)

### Community 108 - "register_exception_handlers"
Cohesion: 0.12
Nodes (13): _error_payload(), Any, FastAPI, Request, register_exception_handlers(), handle_app_error(), handle_http_exception(), handle_unexpected() (+5 more)

### Community 109 - "Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)"
Cohesion: 0.25
Nodes (9): API keys (X-API-Key, nxo_..., scope intersection), First boot sequence (api entrypoint migrates, compose never seeds), Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test), Makefile workflows (up/test/lint/typecheck/migrate/seed), HIGH finding: API-key scope bypass for superadmin-owned keys (fixed: scope intersection first), Security audit 2026-09 (26 raw findings -> 20 confirmed, all fixed), HIGH finding: known seed superadmin + API key backdoor (fixed: NEXUSOPS_ALLOW_SEED opt-in, one-time password), Threat model (edge attacker, malicious agent, curious operator, leaked token, SSRF) (+1 more)

### Community 110 - "_FakeAsyncClient"
Cohesion: 0.22
Nodes (3): _FakeAsyncClient, _FakeRequestObj, Scripted httpx.AsyncClient: responses keyed by absolute request URL.

### Community 111 - "require_permission"
Cohesion: 0.21
Nodes (10): permission_dep(), Any, Dependency factory enforcing a permission; returns 403 when denied., require_permission(), _check(), Forbidden, _FakeCtx, Duck-typed stand-in for AuthContext. (+2 more)

### Community 112 - "create_app"
Cohesion: 0.20
Nodes (15): close_redis(), create_app(), _include_routers(), lifespan(), FastAPI, Mount every domain router. Router variables follow the module contract., Start the WS hub + notification dispatcher; tear them down cleanly., _app_for_environment() (+7 more)

### Community 113 - "log_service.py"
Cohesion: 0.13
Nodes (24): container_log_channel(), Canonical Redis pub/sub channel names shared by API, workers and WS hub., LogSource, LogEntry, _persist_log_lines(), Write LogEntry rows via log_service.append_lines, falling back to direct…, append_lines(), count_container_logs() (+16 more)

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "ContainerListPage.tsx"
Cohesion: 0.16
Nodes (11): ContainerListPage, ContainerListPage(), ContainerRef, formatCpu(), formatMemory(), formatUtc(), SORT_OPTIONS, STATUS_OPTIONS (+3 more)

### Community 116 - "EnvironmentUpdate"
Cohesion: 0.29
Nodes (7): EnvironmentBase, EnvironmentUpdate, field_validator, Shared environment fields., Partial environment update; omitted fields are left untouched., 1.4 Deploy-time resolution today, 8. Environment config vs secrets boundary

### Community 117 - "simulation.py"
Cohesion: 0.27
Nodes (9): _containers_for(), task, Simulation mode: drive the seeded fleet so dashboards stay alive on a laptop.…, Deterministic smooth value in [base-amplitude, base+amplitude]., Stable per-server container set; one container cycles EXITED occasionally., simulation_tick(), _run(), _wave() (+1 more)

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

### Community 123 - "hub.py"
Cohesion: 0.12
Nodes (19): AppError, Exception, Base class for expected, client-facing errors., _authenticate_api_key(), _authenticate_jwt(), _load_permissions(), AsyncSession, User (+11 more)

### Community 124 - "list_audit_logs"
Cohesion: 0.29
Nodes (7): list_audit_logs(), datetime, DbSession, Depends, get, PageParamsDep, Newest-first audit trail with optional filters. No write routes exist for this…

### Community 125 - "DeploymentRunner"
Cohesion: 0.25
Nodes (6): DeploymentRunner, Protocol, Stream output lines for *step_name*; raise StepFailure to fail it., Adapter interface implemented by real (future) and simulated runners., Return the ordered step names for this run., 2. What survives unchanged

### Community 126 - "APIModel"
Cohesion: 0.04
Nodes (80): Agent-facing schemas. Payloads are data only — never executed., AlertOut, Schemas for operator-facing alerts., ApiKeyCreateRequest, API key schemas. Raw keys appear exactly once, at creation., AuditOut, Schemas for the read-only audit log API. The audit table is append-only; these…, One audit trail entry (no write routes ever exist for this resource). (+72 more)

### Community 146 - "helpers.py"
Cohesion: 0.22
Nodes (12): error_of(), login_headers(), Any, AsyncClient, Pure helpers for journey tests: payloads, auth shortcuts, cookie parsing., Bootstrap owner account + session; returns ``(credentials, login_result)``., Unwrap an API error envelope., Register a user; returns ``(request_payload, response_body)``. (+4 more)

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

### Community 152 - "resolve_auth"
Cohesion: 0.17
Nodes (16): get_current_user(), get_optional_user(), _load_permissions(), AsyncSession, DbSessionDep, Request, Standard authentication dependency. Also records client IP for logs/audit., Like :func:`get_current_user` but returns ``None`` for anonymous callers. (+8 more)

### Community 153 - "instant_pacing"
Cohesion: 0.40
Nodes (4): instant_pacing(), fixture, MonkeyPatch, Remove the per-line sleeps; pacing bounds are asserted separately.

### Community 154 - "nexusops-draft.mjs"
Cohesion: 0.40
Nodes (4): DOCS, meta, SPINE, VERIFY_RULES

### Community 155 - "assert_error_code"
Cohesion: 0.14
Nodes (20): assert_error_code(), bearer(), Assert envelope shape + code; returns the inner error object., A fresh, deliverable-shaped address unique to a single test. ``example.com`` is…, unique_email(), Regression: lockout must not leak which emails exist. After login_max_attempts…, Sessions must carry the real client address, not the proxy hop's peer. Behind…, Client-injected leftmost XFF entries must not poison the session IP. (+12 more)

### Community 156 - "nexusops-challenge.mjs"
Cohesion: 0.33
Nodes (5): CHALLENGE_COMMON, meta, RESEARCH_COMMON, SCHEMA, TASKS

### Community 157 - "test_agent_ingestion.py"
Cohesion: 0.30
Nodes (10): _enrolled(), _heartbeat(), Agent ingest pipeline: hello, heartbeat, staleness transitions, events., A container absent from a later heartbeat is gone from the daemon., A payload at the agent's cap may be truncated — absence proves nothing., test_heartbeat_at_container_cap_skips_reconciliation(), test_heartbeat_removes_vanished_containers(), test_heartbeat_updates_status_metrics_and_containers() (+2 more)

### Community 158 - "tasks/deployments.py"
Cohesion: 0.29
Nodes (7): task, Deployment execution task + stuck-deployment sweeper., Execute one queued deployment. The engine owns all state transitions., Re-enqueue deployments the broker lost; fail ones whose worker died.…, run_deployment(), _run(), sweep_deployments()

### Community 159 - "collect_container_stats"
Cohesion: 0.29
Nodes (6): collect_container_stats(), collect_containers(), _docker_request(), Best-effort container list; empty when no docker socket is present., One-shot docker stats for running containers, CPU diffed across cycles.…, _UnixHTTPConnection

### Community 161 - "validate_endpoint_url"
Cohesion: 0.50
Nodes (3): model_validator, Validate/normalize an endpoint URL against the scheme allowlist., validate_endpoint_url()

### Community 162 - "8. Upstream binding and re-render triggers"
Cohesion: 0.33
Nodes (6): 8.1 Binding rules, 8.2 Certificate selection rule (this doc owns it), 8.3 Re-render triggers, 8.4 Drift, 8.5 How deployments hook routing (post-deploy route sync), 8. Upstream binding and re-render triggers

### Community 163 - "_transport_is_https"
Cohesion: 0.50
Nodes (4): Whether this request's cookie will travel over https. The edge always…, _transport_is_https(), The Secure-cookie decision follows the wire, not the environment label.…, test_transport_is_https_decision()

### Community 164 - "permissions.py"
Cohesion: 0.40
Nodes (3): PermissionSpec, Permission registry and role matrix. Permissions are *data*: the registry below…, fnmatch

### Community 165 - "agent_heartbeat"
Cohesion: 0.12
Nodes (19): agent_heartbeat(), agent_hello(), DbDep, post, Request, Response, Resolve ``X-Agent-Token`` to an enrolled server or raise 401., First contact after enrollment: persist static host facts, negotiate cadence. (+11 more)

### Community 166 - "4. ACME architecture"
Cohesion: 0.40
Nodes (5): 4.1 DNS-01 first (the default and the wedge), 4.2 DNSProvider interface, 4.3 ACME account and directory, 4.4 HTTP-01 via node nginx (later fallback), 4. ACME architecture

### Community 167 - "me"
Cohesion: 0.29
Nodes (7): me(), CurrentUser, get, The caller's identity, role name and effective permission list., effective_permissions(), User, Sorted explicit permission codenames for a user; ``*`` expands to the registry.

### Community 168 - "_pace"
Cohesion: 0.67
Nodes (3): _pace(), Deterministic per-line delay between 0.05s and 0.35s., test_pace_bounds()

### Community 169 - "1. Current state"
Cohesion: 0.40
Nodes (5): 1.1 Storage and crypto, 1.2 Data model, 1.3 API surface (metadata-only reads), 1.6 Current-state gap list, 1. Current state

## Knowledge Gaps
- **397 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+392 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1459 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AuthContext` connect `AuthContext` to `v1/auth.py`, `NotFound`, `deps.py`, `docker_hosts.py`, `projects.py`, `incidents.py`, `deployment_engine.py`, `v1/deployments.py`, `test_deployments_simulated.py`, `metrics_service.py`, `resolve_auth`, `monitor_service.py`, `containers.py`, `auth_service.py`, `container_service.py`, `docker_host_service.py`, `monitors.py`, `server_service.py`, `test_permissions.py`, `servers.py`, `create_secret`, `role_service.py`, `publish`, `rotate_secret`, `v1/channels.py`, `middleware.py`, `NotificationChannel`, `Hub`, `events.py`, `notification_service.py`, `incident_service.py`, `scope_matches`, `require_permission`, `hub.py`, `list_audit_logs`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Why does `README.md - NexusOps overview` connect `README.md - NexusOps overview` to `docs/engineering-report.md - build and verification report`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Why does `docs/troubleshooting.md - symptom -> cause -> fix runbook` connect `docs/engineering-report.md - build and verification report` to `README.md - NexusOps overview`, `Invisible account lockout (5 fails -> 15 min, enumeration resistance)`?**
  _High betweenness centrality (0.040) - this node is a cross-community bridge._
- **Are the 73 inferred relationships involving `AuthContext` (e.g. with `list_audit_logs()` and `_optional_actor()`) actually correct?**
  _`AuthContext` has 73 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `apiGet()` (e.g. with `ContainerDetailPage.test.tsx` and `mockApi()`) actually correct?**
  _`apiGet()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `meta`, `SCHEMA`, `RESEARCH_COMMON` to the rest of the system?**
  _397 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ApiError` be split into smaller, more focused modules?**
  _Cohesion score 0.02147074610842727 - nodes in this community are weakly interconnected._