# Graph Report - nexusops  (2026-09-24)

## Corpus Check
- 284 files · ~257,087 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: (none) 8, .example 1, .service 1)

## Summary
- 4018 nodes · 11867 edges · 172 communities (145 shown, 27 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 975 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7a92b064`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- client.ts
- v1/auth.py
- types.ts
- apiGet
- NotFound
- deps.py
- resolve_client_ip
- docker_hosts.py
- App.tsx
- enums.py
- AuthContext
- ServerDetailPage.tsx
- v1/health.py
- ContainerDetailPage.tsx
- projects.py
- incidents.py
- deployment_engine.py
- SimulatedDockerProvider
- maintenance.py
- v1/deployments.py
- test_deployments_simulated.py
- containers.py
- metrics_service.py
- get_settings
- Domain Routing — NexusOps
- monitor_service.py
- Node & Agent Architecture
- test_agent_backoff.py
- APIModel
- nexusops_agent.py
- integration/conftest.py
- auth_service.py
- container_service.py
- AlertsPage.test.tsx
- docker_host_service.py
- PageParams
- monitors.py
- v1/search.py
- server_service.py
- list_deliveries
- DockerProvider
- test_monitor_transport.py
- test_agent_contract.py
- toast.tsx
- docker_real.py
- require_permission
- UsersPage.tsx
- servers.py
- test_ssrf.py
- secret_service.py
- Conflict
- test_schemas_server.py
- api_key_service.py
- publish
- test_schemas_agent.py
- core/tenancy.py
- rotate_secret
- alembic
- notification_service.py
- test_auth_journey.py
- compilerOptions
- test_tenant_isolation.py
- main.py
- alert_service.py
- SimulatedDeploymentRunner
- asyncio
- test_schema_redaction.py
- organization.py
- Hub
- package.json
- events.py
- test_secrets.py
- Platform Security Model — NexusOps
- models/__init__.py
- api service (FastAPI / uvicorn :8000)
- env.py
- SecretsPage.tsx
- incident_service.py
- roles.py
- ApiKeysPage.tsx
- scope_matches
- Settings
- users.py
- rate_limit.py
- ScopedSession
- Product Roadmap — NexusOps Multi-Tenant Platform
- devDependencies
- redact_mapping
- seed.py
- get_meta
- _validate_resolution
- Deployment Architecture — NexusOps (target state)
- test_monitors_incidents.py
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
- fastapi
- tests/conftest.py
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- Any
- register_exception_handlers
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- 20260922_1000-a3f1c8d24b6e_add_tenancy_foundation.py
- organization_service.py
- config.py
- log_service.py
- scripts
- ssrf.py
- resolve_secrets_for_environment
- Multi-Tenancy Architecture
- dependencies
- @tanstack/react-query
- generate_secrets.sh
- hash_token
- server_payload
- AppError
- list_audit_logs
- DockerHostsPage.test.tsx
- uuid
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
- sweep_deployments
- BadRequest
- AgentClient
- big_serial_pk
- 8. Upstream binding and re-render triggers
- ApplicationBase
- viewer_in_a
- require_server
- UUID
- MonitorCreate
- _FakeSession
- _validate_ip
- _collect_refs
- SecretReference

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
- `3.2 Route` --references--> `rate_limit()`  [INFERRED]
  docs/domain-routing.md → backend/app/core/rate_limit.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three authentication credential families with centralized permission checks** — docs_api_md_auth, docs_api_md_refresh_rotation, docs_api_md_api_keys, docs_agent_md_enrollment_token, docs_api_md_permission_model [EXTRACTED 1.00]
- **NexusOps compose stack services** — docker_compose_yml_nexusops_stack, docker_compose_yml_postgres_service, docker_compose_yml_redis_service, docker_compose_yml_mailpit_service, docker_compose_yml_api_service, docker_compose_yml_worker_service, docker_compose_yml_scheduler_service, docker_compose_yml_frontend_service, docker_compose_yml_nginx_service [EXTRACTED 1.00]
- **WebSocket real-time fan-out spine** — docs_architecture_md_websocket_hub, docs_api_md_websocket_channels, docker_compose_yml_redis_service, docs_architecture_md_event_bus, readme_react_spa [INFERRED 0.85]

## Communities (172 total, 27 thin omitted)

### Community 0 - "client.ts"
Cohesion: 0.03
Nodes (73): API_BASE, ApiError, buildUrl(), extractError(), getActiveOrgId(), ORGANIZATION_HEADER, RequestOptions, setAccessToken() (+65 more)

### Community 1 - "v1/auth.py"
Cohesion: 0.08
Nodes (49): change_password(), _clear_refresh_cookie(), _cookies_secure(), login(), logout(), me(), _optional_actor(), AsyncSession (+41 more)

### Community 2 - "types.ts"
Cohesion: 0.05
Nodes (49): AuditEntry, DeploymentLogLine, DeploymentOut, DeploymentStatus, EnvironmentOut, MetricsResponse, Organization, Page (+41 more)

### Community 3 - "apiGet"
Cohesion: 0.09
Nodes (55): apiDelete(), apiGet(), apiPatch(), apiPost(), apiRequest(), ApplicationOut, ProjectDetailPage, SelectField() (+47 more)

### Community 4 - "NotFound"
Cohesion: 0.12
Nodes (41): NotFound, MembershipStatus, _apply_deactivation(), _assert_not_last_active_member(), _assert_not_last_active_superadmin(), create_user(), deactivate_user(), get_by_email() (+33 more)

### Community 5 - "deps.py"
Cohesion: 0.09
Nodes (33): FastAPI dependencies: database session, authenticated tenant context, RBAC…, Agent ingest endpoints: enrollment handshake and periodic heartbeats.…, Audit log API. Strictly read-only: the table is append-only by design., Metrics query API: server timeseries, latest snapshot, dashboard summary., get_session(), Async SQLAlchemy engine and session management., FastAPI dependency yielding an async session., Error taxonomy and the single place where API error envelopes are shaped. Every… (+25 more)

### Community 6 - "resolve_client_ip"
Cohesion: 0.17
Nodes (22): _is_trusted(), _parse_networks(), Request, Client-IP resolution behind chained reverse proxies. The API never takes TCP…, Parse a comma-separated CIDR list; malformed entries are skipped., Real client address for *request* per the trust model above., resolve_client_ip(), make_request() (+14 more)

### Community 7 - "docker_hosts.py"
Cohesion: 0.13
Nodes (22): Docker host API: CRUD, ping and provider-backed inventory reads. Permission…, DockerHostCreate, DockerHostOut, DockerHostUpdate, DockerImageOut, DockerNetworkOut, DockerVolumeOut, image_out() (+14 more)

### Community 8 - "App.tsx"
Cohesion: 0.05
Nodes (50): DashboardSummary, SearchResult, AlertsPage, App(), AuditLogPage, DashboardPage, LoginRoute(), MonitorDetailPage (+42 more)

### Community 9 - "enums.py"
Cohesion: 0.14
Nodes (26): json_column(), org_id_column(), datetime, UUID, Declarative base, shared mixins and column helpers., A plain ``org_id`` column for the few tables that carry one without taking part…, status_check(), TimestampMixin (+18 more)

### Community 10 - "AuthContext"
Cohesion: 0.13
Nodes (46): AuthContext, Resolved identity plus the organization this request acts in.…, paginate(), AsyncSession, Execute *stmt* with limit/offset and return ``(rows, total)``., Application, Any, AsyncSession (+38 more)

### Community 11 - "ServerDetailPage.tsx"
Cohesion: 0.07
Nodes (45): ContainerOut, MetricPoint, ServerDetail, ServerSummary, ServerDetailPage, ServerListPage, ChartSeries, LineChart() (+37 more)

### Community 12 - "v1/health.py"
Cohesion: 0.20
Nodes (13): liveness(), get, Response, Health probes: liveness (always cheap) and readiness (checks dependencies).…, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness(), HealthOut (+5 more)

### Community 13 - "ContainerDetailPage.tsx"
Cohesion: 0.07
Nodes (38): getAccessToken(), refreshToken(), CursorPage, EventItem, ContainerDetailPage, EventsPage, Subscription, useEventStream() (+30 more)

### Community 14 - "projects.py"
Cohesion: 0.11
Nodes (49): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+41 more)

### Community 15 - "incidents.py"
Cohesion: 0.20
Nodes (24): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+16 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.10
Nodes (61): deployment_log_channel(), Deployment, DeploymentEnvironment, DeploymentStep, AlertSeverity, DeploymentStatus, DeploymentTrigger, EventLevel (+53 more)

### Community 17 - "SimulatedDockerProvider"
Cohesion: 0.09
Nodes (29): Any, Plausible numbers derived from the row plus time-based sine noise., Implements :class:`DockerProvider` semantics against DB rows., Make a container row visible to this provider instance., Attach already-fetched log rows so ``logs()`` can replay them., _seed_int(), SimulatedDockerProvider, _log_entry() (+21 more)

### Community 18 - "maintenance.py"
Cohesion: 0.06
Nodes (62): Celery application: periodic cadences live here, dynamic work is claimed…, _run(), task, Heartbeat sweeps: offline detection and recovery for servers., Flag silent servers OFFLINE, recover returning ones. Safe to overlap., sweep_servers(), _run(), aggregate_metrics() (+54 more)

### Community 19 - "v1/deployments.py"
Cohesion: 0.10
Nodes (41): _attribute_step_idx(), cancel_deployment(), _emails_for(), get_deployment(), list_application_deployments(), list_deployment_logs(), _list_deployments(), _parse_sort() (+33 more)

### Community 20 - "test_deployments_simulated.py"
Cohesion: 0.15
Nodes (28): execute_deployment(), Run one deployment to a terminal state. Never raises; safe to re-run., get_environment(), _as_worker(), _delivery_chain(), _owner_ctx(), _queue(), _queued_with_recorder() (+20 more)

### Community 21 - "containers.py"
Cohesion: 0.06
Nodes (64): _action_route(), _endpoint(), _container_out(), _decode_frame(), _ev(), get_container(), _like_pattern(), list_container_logs() (+56 more)

### Community 22 - "metrics_service.py"
Cohesion: 0.09
Nodes (41): get_dashboard_summary(), get_latest_server_metrics(), get_server_metrics(), CurrentUser, DbDep, Depends, get, UUID (+33 more)

### Community 23 - "get_settings"
Cohesion: 0.10
Nodes (39): argon2, argon2_exceptions, AsyncEngine, get_settings(), Return the cached settings singleton., get_engine(), Runtime DSN (application role, RLS enforced) for Celery/script sync paths., sync_database_url() (+31 more)

### Community 24 - "Domain Routing — NexusOps"
Cohesion: 0.09
Nodes (23): 10. Wildcards and catch-all, 11. User journey, 12. API surface, permissions, audit, 13. Monitoring tie-in, 1. Scope and current state, 2. Where nginx runs, 3.1 Domain, 3.2 Route (+15 more)

### Community 25 - "monitor_service.py"
Cohesion: 0.15
Nodes (36): MonitorStatus, Monitor, Drop the query string so signed tokens never appear in error text., Public alias: redact any query string from a URL before display/persist., strip_query(), _active_incident(), _audit(), claim_due_monitors() (+28 more)

### Community 26 - "Node & Agent Architecture"
Cohesion: 0.10
Nodes (20): 1. Scope and stance, 2.1 Current shape (real), 2.2 Changes for the target model, 2.3 Capabilities (target), 2.4 DockerEndpoint — the 0..1 relation, 2. The Node concept, 5.1 Model and lifecycle, 5.2 Whitelisted operation types (+12 more)

### Community 27 - "test_agent_backoff.py"
Cohesion: 0.08
Nodes (36): AST, agent_fixture(), _install_sleep(), fake_sleep(), _load_agent(), _patch_host(), Any, fixture (+28 more)

### Community 28 - "APIModel"
Cohesion: 0.04
Nodes (57): ApiKeyCreateRequest, APIModel, BaseModel, Base for request/response models: ORM mode + strict-ish population., DeploymentApplicationRef, DeploymentCreate, DeploymentEnvironmentRef, LogOut (+49 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.09
Nodes (30): build_heartbeat(), collect_container_stats(), collect_containers(), cpu_percent_since(), disk_stats(), _docker_request(), _interruptible_sleep(), load1() (+22 more)

### Community 30 - "integration/conftest.py"
Cohesion: 0.16
Nodes (18): alembic_config, client(), _ensure_database(), _migrated_database(), org_db(), owner(), AsyncClient, fixture (+10 more)

### Community 31 - "auth_service.py"
Cohesion: 0.11
Nodes (48): active_memberships(), The user's memberships in non-suspended organizations, oldest first. Reads only…, System scope bound to *db*, for rows that have no organization. Used by exactly…, system_write_scope(), ActorType, AuditResult, OrganizationStatus, _audit() (+40 more)

### Community 32 - "container_service.py"
Cohesion: 0.09
Nodes (47): ContainerHealth, ContainerStatus, Container, Observed container state mirrored from an agent or docker provider., clip(), DockerProviderError, Exception, Provider abstraction for docker hosts (real daemon or simulated). Providers are… (+39 more)

### Community 33 - "AlertsPage.test.tsx"
Cohesion: 0.13
Nodes (13): AlertOut, ChannelOut, DeliveryOut, delivery, mockedGet, mockedPatch, mockedPost, mockHasPermission (+5 more)

### Community 34 - "docker_host_service.py"
Cohesion: 0.07
Nodes (63): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+55 more)

### Community 35 - "PageParams"
Cohesion: 0.08
Nodes (44): list_alerts(), mark_all_read(), mark_read(), CurrentUser, DbDep, Depends, get, post (+36 more)

### Community 36 - "monitors.py"
Cohesion: 0.14
Nodes (36): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+28 more)

### Community 37 - "v1/search.py"
Cohesion: 0.13
Nodes (31): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+23 more)

### Community 38 - "server_service.py"
Cohesion: 0.10
Nodes (48): server_metrics_channel(), ServerStatus, Server, _actor_kwargs(), _apply_agent_entry(), container_counts(), create_server(), delete_server() (+40 more)

### Community 39 - "list_deliveries"
Cohesion: 0.18
Nodes (19): create_channel(), delete_channel(), get_channel(), list_channels(), list_deliveries(), DbDep, delete, Depends (+11 more)

### Community 40 - "DockerProvider"
Cohesion: 0.08
Nodes (14): ContainerInfo, DockerProvider, Any, datetime, Protocol, List containers visible to the provider., Inspect a single container by id (short ids allowed)., List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``. (+6 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.06
Nodes (57): CheckResult, CheckOutcome, coerce_headers(), _decode(), get_transport(), HTTPMonitorTransport, MonitorTransport, Any (+49 more)

### Community 42 - "test_agent_contract.py"
Cohesion: 0.20
Nodes (15): agent_fixture(), _load_agent(), _patch_stats(), Any, fixture, MonkeyPatch, Contract tests: the shipped agent's payloads must satisfy the ingest schemas.…, One-shot docker stats reduce to cpu/mem/limit fields the schema accepts, with… (+7 more)

### Community 43 - "toast.tsx"
Cohesion: 0.05
Nodes (35): CheckOut, IncidentEventOut, IncidentOut, MonitorOut, SessionInfo, IncidentDetailPage, Toast, TOAST_ARIA_LABEL (+27 more)

### Community 44 - "docker_real.py"
Cohesion: 0.09
Nodes (25): ContainerStats, Point-in-time resource usage snapshot., _as_float(), _compute_stats(), _cpu_percent(), _network_bytes(), parse_log_line(), parse_rfc3339() (+17 more)

### Community 45 - "require_permission"
Cohesion: 0.10
Nodes (19): permission_dep(), Any, Dependency factory enforcing a permission; returns 403 when denied., require_permission(), permission_exists(), _auth_context(), _FakeCtx, Unit tests for the permission registry, scope matching and RBAC gate. (+11 more)

### Community 46 - "UsersPage.tsx"
Cohesion: 0.06
Nodes (33): DockerHostsPage, LoginPage, UsersPage, CheckboxField(), CheckboxFieldProps, FieldAria, FieldBaseProps, PasswordField() (+25 more)

### Community 47 - "servers.py"
Cohesion: 0.10
Nodes (35): create_server(), delete_server(), _detail(), get_server(), list_servers(), list_tags(), AsyncSession, DbDep (+27 more)

### Community 48 - "test_ssrf.py"
Cohesion: 0.17
Nodes (25): UnprocessableEntity, assert_safe_url(), _raise_block(), Validate *url* for outbound requests; return the parsed URL or raise 422.…, install_dns(), lax(), Exception, fixture (+17 more)

### Community 49 - "secret_service.py"
Cohesion: 0.19
Nodes (23): An encrypted configuration value. The plaintext is never returned by the API…, Secret, _actor_type(), create_secret(), delete_secret(), _detail(), get_secret(), get_secret_detail() (+15 more)

### Community 50 - "Conflict"
Cohesion: 0.15
Nodes (25): Conflict, create_role(), delete_role(), effective_permissions(), get_role(), list_roles(), permissions_for_role(), AsyncSession (+17 more)

### Community 51 - "test_schemas_server.py"
Cohesion: 0.21
Nodes (22): Payload for registering a server., Partial update. ``tags`` replaces the full set when provided., ServerCreate, ServerUpdate, _base(), parametrize, Unit tests for app.schemas.server (validation only, no I/O)., test_empty_ip_is_allowed_but_whitespace_collapses() (+14 more)

### Community 52 - "api_key_service.py"
Cohesion: 0.10
Nodes (32): create_api_key(), list_api_keys(), CurrentUser, DbSessionDep, delete, get, post, Request (+24 more)

### Community 53 - "publish"
Cohesion: 0.25
Nodes (14): _after_commit_publish(), _after_rollback_drop(), event_frame_from_row(), publish(), _publish_after_commit(), _publish_redis(), Any, AsyncSession (+6 more)

### Community 54 - "test_schemas_agent.py"
Cohesion: 0.15
Nodes (27): AgentContainerIn, AgentHeartbeatIn, AgentHelloIn, field_validator, First contact from an agent after enrollment; fills static host facts., Observed container state reported by an agent., Periodic metrics + observed containers from an enrolled agent., _container() (+19 more)

### Community 55 - "core/tenancy.py"
Cohesion: 0.08
Nodes (37): _apply_scope_guc(), current_scope(), _desired_guc(), _guard(), _has_org_predicate(), install_tenancy_guards(), _mappers_of(), _org_scoped_classes() (+29 more)

### Community 56 - "rotate_secret"
Cohesion: 0.15
Nodes (22): create_secret(), delete_secret(), get_secret(), list_secrets(), DbSession, delete, Depends, get (+14 more)

### Community 58 - "notification_service.py"
Cohesion: 0.08
Nodes (59): Notification channel endpoints. Config is write-only; never echoed back., # NOTE: /deliveries is declared before /{channel_id} so the literal wins., update_channel(), ChannelType, DeliveryStatus, NotificationChannel, A delivery target (email address / webhook endpoint). ``config_ciphertext``…, ChannelBase (+51 more)

### Community 59 - "test_auth_journey.py"
Cohesion: 0.16
Nodes (22): cookie_attributes(), login_account(), Response, Login and unpack tokens, the raw cookie header and the user object., The raw Set-Cookie header carrying the refresh token., Extract just the opaque token from a Set-Cookie header., Parse Set-Cookie attributes (lowercased keys, empty string for flags)., refresh_cookie_header() (+14 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "test_tenant_isolation.py"
Cohesion: 0.07
Nodes (33): _app_role_dsn(), _invite(), Cross-tenant isolation: the Phase 1 exit gate. Every test here answers one of…, ``sessions`` has no tenant column: the owning membership is the boundary.…, Knowing an id is not authority — not even for an instance operator. The caller…, A tenant sees its own rows and nobody else's, on every listing surface., Every security event identifies its organization, and only that one., A machine credential's organization is its own, not whatever it claims.… (+25 more)

### Community 62 - "main.py"
Cohesion: 0.09
Nodes (31): ASGIApp, dispose_engine(), AccessLogMiddleware, Request, Response, HTTP middleware: request ids, security headers, structured access logs., Baseline hardening headers on every API response., RequestIDMiddleware (+23 more)

### Community 63 - "alert_service.py"
Cohesion: 0.26
Nodes (12): Alert, get_alert(), mark_all_read(), mark_read(), AsyncSession, UUID, Alert inbox: insert-only creation plus read/unread bookkeeping., Map a system event type to the alert severity it deserves. (+4 more)

### Community 64 - "SimulatedDeploymentRunner"
Cohesion: 0.12
Nodes (39): LogLevel, _commit_short(), _pace(), Exception, Deployment runner port plus a faithful simulated implementation.…, Stream output lines for *step_name*; raise StepFailure to fail it., Staged docker-style simulation used by v1 deployments., Deterministic per-line delay between 0.05s and 0.35s. (+31 more)

### Community 65 - "asyncio"
Cohesion: 0.16
Nodes (16): asyncio, NotificationError, Any, BaseException, Exception, Low-level notification transports: SMTP email and outgoing webhooks. These…, POST *payload* as JSON to *url*; 2xx is success, anything else raises. Response…, Raised when a delivery attempt fails. Message is safe to persist. (+8 more)

### Community 66 - "test_schema_redaction.py"
Cohesion: 0.18
Nodes (17): is_sensitive_header(), mask_sensitive_headers(), True when *name* looks like it carries a credential (Authorization etc.)., Return a copy of *headers* with sensitive values replaced by a mask., mask_target(), Human-readable masked target safe to expose over the API. For webhook families…, _monitor_out(), Outbound-schema redaction: monitor probe credentials and webhook targets.… (+9 more)

### Community 67 - "organization.py"
Cohesion: 0.13
Nodes (22): create_organization(), list_my_organizations(), CurrentUser, DbSessionDep, get, IdentityUser, post, Request (+14 more)

### Community 68 - "Hub"
Cohesion: 0.15
Nodes (15): _close_socket(), Connection, Hub, _is_same_origin(), _params_key(), WebSocket, Browsers always send Origin on WS handshakes, even same-origin ones. When it…, Connection registry, Redis fan-in listener and per-socket pumps. (+7 more)

### Community 69 - "package.json"
Cohesion: 0.13
Nodes (15): name, private, type, version, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom (+7 more)

### Community 70 - "events.py"
Cohesion: 0.11
Nodes (22): _decode_cursor(), _encode_cursor(), list_event_types(), list_events(), datetime, DbSession, Depends, get (+14 more)

### Community 71 - "test_secrets.py"
Cohesion: 0.18
Nodes (15): _create(), _environment_config(), Secrets: metadata-only reads, rotation versioning, deploy-time resolution., Project → application → environment carrying *config*; returns its id., A reference naming no secret must abort, not resolve to an empty value.…, A row this ENCRYPTION_KEY cannot decrypt must abort, not yield ``""``., ${secret:KEY} placeholders resolve through decrypt at deploy time., test_create_and_list_return_metadata_only() (+7 more)

### Community 72 - "Platform Security Model — NexusOps"
Cohesion: 0.11
Nodes (18): 10.1 Node revocation playbook (compromised node / leaked agent token), 10.2 Key compromise playbook, 10. Incident response, 1.1 Real vs simulated today (do not mistake one for the other), 1. Scope, stance, and simulation honesty, 2. Assets, 3. Trust boundaries, 4. Tenant isolation model (summary) (+10 more)

### Community 73 - "models/__init__.py"
Cohesion: 0.19
Nodes (21): Base, OrgScoped, Base for all ORM models with stable constraint naming for Alembic., Mixin marking a table as **organization-owned** (Phase 1 tenancy). Set the…, Opaque refresh token; only its SHA-256 hash is stored. Rotation chain: on…, RefreshToken, RolePermission, AgentCredential (+13 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "env.py"
Cohesion: 0.24
Nodes (10): _database_url(), Alembic environment: metadata comes from app.models, URL from app settings., Migrations run as the table **owner**, never as the application role. The owner…, Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online(), Owner-role DSN for Alembic and the container entrypoint. Migrations… (+2 more)

### Community 76 - "SecretsPage.tsx"
Cohesion: 0.15
Nodes (11): SecretRow, SecretsPage, CreateSecretModal(), DeleteSecretModal(), errorMessage(), formatTimestamp(), RotateSecretModal(), SecretsPage() (+3 more)

### Community 77 - "incident_service.py"
Cohesion: 0.22
Nodes (24): IncidentEventKind, IncidentSeverity, IncidentStatus, Incident, IncidentEvent, acknowledge(), _add_event(), add_note() (+16 more)

### Community 78 - "roles.py"
Cohesion: 0.11
Nodes (28): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, delete, get (+20 more)

### Community 79 - "ApiKeysPage.tsx"
Cohesion: 0.09
Nodes (20): ApiKeyOut, ApiKeysPage, ApiKeyCreatedOut, ApiKeysPage(), handleCopyKey(), copyText(), describeError(), EMPTY_FORM (+12 more)

### Community 80 - "scope_matches"
Cohesion: 0.13
Nodes (15): Check an API-key scope list against a required permission. Supports exact match…, scope_matches(), parametrize, test_scope_matches_truth_table(), 1. Principles (already true in the codebase, kept), 2. Registry changes (Phase 1 + new subsystems), 3. The five system roles (target), 4. Grants (resource-level access; design now, later phase) (+7 more)

### Community 81 - "Settings"
Cohesion: 0.14
Nodes (6): field_validator, model_validator, Username from :attr:`database_url`, or ``None`` if it is unparseable., Validated application settings (loaded from environment / .env)., Settings, BaseSettings

### Community 82 - "users.py"
Cohesion: 0.12
Nodes (28): create_user(), deactivate_user(), get_user(), list_users(), CurrentUser, DbSessionDep, delete, get (+20 more)

### Community 83 - "rate_limit.py"
Cohesion: 0.15
Nodes (21): RateLimited, client_ip(), _memory_count_and_ttl(), Request, rate_limit(), _dependency(), Redis-backed fixed-window rate limiting as a FastAPI dependency factory. Auth-…, Best-effort client IP; honours X-Forwarded-For from trusted proxies. Delegates… (+13 more)

### Community 85 - "Product Roadmap — NexusOps Multi-Tenant Platform"
Cohesion: 0.13
Nodes (15): 0. Stance, 10. Phase 7 — Teams, grants & custom roles, 11. Phase 8 — Backups, 12. Phase 9 — Billing & metering, 14. Biggest risks (short form), 15. Reading order, 2. Phase plan, 4. Phase 1 — Tenancy foundation (+7 more)

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "redact_mapping"
Cohesion: 0.22
Nodes (13): _is_sensitive_key(), Substring match on a normalised key so header-style names are caught too.…, Return a copy of *data* with sensitive values replaced. Used by audit metadata…, redact_mapping(), parametrize, Unit tests for app.core.logging redaction (pure functions only)., test_case_insensitive_substring_match(), test_flat_sensitive_keys_redacted() (+5 more)

### Community 88 - "seed.py"
Cohesion: 0.11
Nodes (32): Project, ApiKey, Permission, Machine credential. Raw key shown once at creation; hash stored. A key is bound…, A named permission set. ``org_id`` is NULL for every row in v1 — the five…, Role, User, Membership (+24 more)

### Community 89 - "get_meta"
Cohesion: 0.40
Nodes (5): get_meta(), DbSessionDep, get, Public metadata; identity fields appear only for valid credentials., OptionalUser

### Community 90 - "_validate_resolution"
Cohesion: 0.17
Nodes (14): _is_forbidden_address(), is_simulation_url(), True when *url* targets the built-in simulated checker (``sim://``)., True when *addr* points into a network the server must never contact.…, Resolve *hostname* (AF_UNSPEC) and refuse any non-public answer., _validate_resolution(), parametrize, test_non_simulation_urls() (+6 more)

### Community 91 - "Deployment Architecture — NexusOps (target state)"
Cohesion: 0.09
Nodes (22): DeploymentRunner, Protocol, Adapter interface implemented by real (future) and simulated runners., Return the ordered step names for this run., 10. Events and WS during runs, 11. Post-deploy hooks, 12. Rollback semantics (existing behavior kept), 13. The simulated runner stays — labeled (+14 more)

### Community 92 - "test_monitors_incidents.py"
Cohesion: 0.18
Nodes (16): NotificationDelivery, _create_monitor(), Monitor checks driving the full down -> incident -> recovery lifecycle., Regression: probe headers and URL query credentials never leave the API. Probe…, A monitor's checks, incidents and timeline all live in its organization, so the…, test_check_now_endpoint_runs_immediately(), test_down_then_recover_lifecycle(), test_monitor_responses_mask_probe_credentials() (+8 more)

### Community 93 - "get_redis"
Cohesion: 0.26
Nodes (11): get_redis(), ping(), Shared async Redis client., _next_data_message(), Event bus fan-out ordering: a frame follows its transaction, never leads it.…, Regression: a rollback must drop stashed frames, not defer them. The stash…, test_frame_published_only_after_commit(), test_rolled_back_event_never_publishes() (+3 more)

### Community 94 - "get_sessionmaker"
Cohesion: 0.09
Nodes (34): async_sessionmaker, The active organization, or raise if this request has none., get_sessionmaker(), AsyncSession, apply_scope_to_session(), org_scope(), Raised when a unit of work touches tenant data with no valid org scope. This is…, Run the enclosed block as a single organization. Nesting the *same* org is a… (+26 more)

### Community 95 - "pytest"
Cohesion: 0.40
Nodes (4): created_at server defaults must evaluate per insert, not at table creation., Regression: system_events and audit_logs shipped with DEFAULT 'now()' (quoted…, test_audit_and_event_created_at_defaults_are_dynamic(), pytest

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
Cohesion: 0.10
Nodes (20): EnvironmentBase, field_validator, Shared environment fields., 10. Resolution flow at deploy time, 1.1 Storage and crypto, 1.2 Data model, 1.4 Deploy-time resolution today, 1.6 Current-state gap list (+12 more)

### Community 102 - "encrypt_str"
Cohesion: 0.09
Nodes (29): decrypt_str(), digest_of(), encrypt_str(), _fernet(), Short server-verifiable digest used for change detection display. HMAC-SHA256…, parametrize, test_decrypt_with_wrong_ciphertext_raises_value_error(), test_digest_length_and_determinism() (+21 more)

### Community 103 - "fastapi"
Cohesion: 0.12
Nodes (17): list_sessions(), CurrentUser, DbSessionDep, delete, get, Request, UUID, Session routes: list active sessions, revoke own or (with user.manage) any. (+9 more)

### Community 104 - "tests/conftest.py"
Cohesion: 0.18
Nodes (9): configure_test_env(), Test bootstrap: pin every cached setting BEFORE the first ``app`` import. The…, KEY=VALUE pairs from the repo .env (first definition wins); never logged., Export the exact settings the app caches; host values cannot leak through., _read_dot_env(), base64, os, sys (+1 more)

### Community 105 - "redis service (Redis 7, no persistence, loopback :6390)"
Cohesion: 0.22
Nodes (11): redis service (Redis 7, no persistence, loopback :6390), WebSocket API (/api/v1/ws handshake, frames, limits), WebSocket channels (global, server-metrics, container-logs, deployment-logs, incidents), Deployment engine (queue_deployment / execute_deployment / sweeper backstop), Real-time spine: PostgreSQL system_events + Redis pub/sub, Rollback as a new deployment (rollback_of_id), WebSocket hub (framework-thin, Redis fan-in, per-socket queues), Test suites (pytest unit+integration, vitest, Playwright e2e) (+3 more)

### Community 106 - "NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)"
Cohesion: 0.18
Nodes (12): Agent security model (one-way telemetry, no command channel), Agent enrollment token (X-Agent-Token, nxa_..., SHA-256 at rest), Agent heartbeat exponential backoff (cap 5 min, exit 1 on revoked token), agent/install.sh (enrollment installer), Agent metrics collection (/proc statvfs Docker socket), NexusOps agent (stdlib-only Python, agent/nexusops_agent.py), Agent systemd hardening (ProtectSystem=strict, NoNewPrivileges), Agent ingest API (POST /agent/hello, POST /agent/heartbeat) (+4 more)

### Community 107 - "Any"
Cohesion: 0.19
Nodes (10): _entity_exists(), _frame_org(), _parse_payload(), Any, Whether *id_* exists **for this organization**. Runs inside the socket's…, Spawn the Redis fan-in listener (idempotent)., Deliver one Redis message to every matching subscription., The organization an event frame belongs to, or ``None`` when it has none. (+2 more)

### Community 108 - "register_exception_handlers"
Cohesion: 0.12
Nodes (13): _error_payload(), Any, FastAPI, Request, register_exception_handlers(), handle_app_error(), handle_http_exception(), handle_unexpected() (+5 more)

### Community 109 - "Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)"
Cohesion: 0.25
Nodes (9): API keys (X-API-Key, nxo_..., scope intersection), First boot sequence (api entrypoint migrates, compose never seeds), Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test), Makefile workflows (up/test/lint/typecheck/migrate/seed), HIGH finding: API-key scope bypass for superadmin-owned keys (fixed: scope intersection first), Security audit 2026-09 (26 raw findings -> 20 confirmed, all fixed), HIGH finding: known seed superadmin + API key backdoor (fixed: NEXUSOPS_ALLOW_SEED opt-in, one-time password), Threat model (edge attacker, malicious agent, curious operator, leaked token, SSRF) (+1 more)

### Community 110 - "20260922_1000-a3f1c8d24b6e_add_tenancy_foundation.py"
Cohesion: 0.22
Nodes (11): _app_role_credentials(), _assert_fully_backfilled(), _backfill_org_ids(), _drop_constraint(), add tenancy foundation Phase 1 of the platform roadmap: organizations,…, Carry a value into a PL/pgSQL block. ``CREATE ROLE``/``ALTER ROLE`` are utility…, Application role name/password from settings (never hard-coded)., Point every pre-existing row at the bootstrap organization. ``audit_logs`` is… (+3 more)

### Community 111 - "organization_service.py"
Cohesion: 0.16
Nodes (26): _check(), Forbidden, add_member(), create_organization(), get_organization(), membership_for_user(), AsyncSession, Membership (+18 more)

### Community 112 - "config.py"
Cohesion: 0.18
Nodes (14): Instance metadata: version, mode, and the caller's effective capabilities. The…, fail_on_bad_config(), Central configuration. All runtime configuration flows through this module so…, Exit immediately with a readable message if configuration is invalid. Also…, _app_for_environment(), MonkeyPatch, ENVIRONMENT gating contract: docs exposure and HSTS (see .env.example).…, create_app() with get_settings() patched to the given environment. (+6 more)

### Community 113 - "log_service.py"
Cohesion: 0.10
Nodes (28): current_org(), The organization this unit of work is acting for, if any., LogSource, LogLine, One parsed log record from a container log stream., datetime, Replay registered LogEntry rows ordered by ts (tail N). ``follow`` is ignored…, append_lines() (+20 more)

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "ssrf.py"
Cohesion: 0.19
Nodes (12): assert_safe_url_async(), SSRF guard applied to every operator-supplied outbound URL. Monitors and…, Async wrapper around :func:`assert_safe_url`; DNS runs off the loop., Internal signal: a specific SSRF rule matched (never shown to clients)., UrlRejected, _validate_syntax(), test_syntax_accepts_wellformed_http_urls(), test_syntax_rejects_bad_urls() (+4 more)

### Community 116 - "resolve_secrets_for_environment"
Cohesion: 0.21
Nodes (12): Exception, A ``${secret:KEY}`` reference could not be resolved. Fail-closed. Carries…, Outcome of resolving an environment's config references., Resolve every ``${secret:KEY}`` reference in an environment's config. INTERNAL…, resolve_secrets_for_environment(), ResolvedSecrets, SecretResolutionError, 1.1 The honest defect list (+4 more)

### Community 117 - "Multi-Tenancy Architecture"
Cohesion: 0.17
Nodes (11): Whether the runtime connection is the RLS-enforced application role. False…, 10. Migration (Phase 1), 1. Tenancy invariants, 2.1 Org creation — v1 decision, 2. Org resolution on every request, 4. Background jobs, 6. Agents, 7. The IDOR suite (+3 more)

### Community 118 - "dependencies"
Cohesion: 0.33
Nodes (6): dependencies, lucide-react, react, react-dom, react-router-dom, @tanstack/react-query

### Community 119 - "@tanstack/react-query"
Cohesion: 0.08
Nodes (21): DeploymentStepOut, DeploymentDetailPage, MetaInfo, SimulatedChip(), mocks, ACTIVE_STATUSES, DeploymentDetailRow, DeploymentLogRow (+13 more)

### Community 120 - "generate_secrets.sh"
Cohesion: 0.47
Nodes (3): existing_real_keys(), replace_or_append(), generate_secrets.sh script

### Community 121 - "hash_token"
Cohesion: 0.26
Nodes (12): generate_agent_token(), generate_api_key(), generate_refresh_token(), hash_token(), Return ``(raw_token, sha256_hex_hash)``., Return ``(raw_key, prefix, hash)``. Keys look like ``nxo_live_<random>``., test_agent_token_prefix_convention(), test_api_and_agent_prefixes_differ() (+4 more)

### Community 122 - "server_payload"
Cohesion: 0.27
Nodes (12): A valid POST /servers body with per-test overrides., server_payload(), _create_server(), Server CRUD, cascade delete, audit trail rows and audit immutability., The HTTP listing path — schema serialization is exercised end-to-end. A…, test_agent_token_rotation_invalidates_previous(), test_audit_log_api_serializes_and_filters(), test_audit_log_is_append_only() (+4 more)

### Community 123 - "AppError"
Cohesion: 0.20
Nodes (16): AppError, Exception, Base class for expected, client-facing errors., _authenticate_api_key(), _authenticate_jwt(), _bind_organization(), _load_permissions(), _org_id_from_frame() (+8 more)

### Community 124 - "list_audit_logs"
Cohesion: 0.29
Nodes (7): list_audit_logs(), datetime, DbSession, Depends, get, PageParamsDep, Newest-first audit trail with optional filters. No write routes exist for this…

### Community 125 - "DockerHostsPage.test.tsx"
Cohesion: 0.18
Nodes (8): DockerHostOut, ApiError, failingHost, host, hostsPage, mockCountApi(), server, serversPage

### Community 126 - "uuid"
Cohesion: 0.08
Nodes (37): Agent-facing schemas. Payloads are data only — never executed., AlertOut, Schemas for operator-facing alerts., API key schemas. Raw keys appear exactly once, at creation., ApplicationSummary, Application API schemas., Application as embedded in project outputs (no deployment summary)., AuditOut (+29 more)

### Community 137 - "test_ws_hub.py"
Cohesion: 0.19
Nodes (22): _connection(), _drain(), _event_frame(), _fake_sessionmaker(), hub(), _Org, Any, fixture (+14 more)

### Community 146 - "helpers.py"
Cohesion: 0.14
Nodes (19): bearer(), error_of(), login_headers(), Any, AsyncClient, Pure helpers for journey tests: payloads, auth shortcuts, cookie parsing., Headers for a logged-in caller, including its active organization., Bootstrap owner account + session; returns ``(credentials, login_result)``. The… (+11 more)

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
Cohesion: 0.10
Nodes (29): _attach_organization(), get_current_user(), get_identity(), get_optional_user(), _load_organization(), _load_permissions(), membership_for_org(), _org_id_from_header() (+21 more)

### Community 153 - "instant_pacing"
Cohesion: 0.40
Nodes (4): instant_pacing(), fixture, MonkeyPatch, Remove the per-line sleeps; pacing bounds are asserted separately.

### Community 154 - "nexusops-draft.mjs"
Cohesion: 0.40
Nodes (4): DOCS, meta, SPINE, VERIFY_RULES

### Community 155 - "assert_error_code"
Cohesion: 0.10
Nodes (25): assert_error_code(), Assert envelope shape + code; returns the inner error object., A fresh, deliverable-shaped address unique to a single test. ``example.com`` is…, unique_email(), Regression: lockout must not leak which emails exist. After login_max_attempts…, test_locked_account_response_is_indistinguishable(), test_second_register_without_invite_is_rejected(), test_metadata_endpoint_and_private_target_blocked() (+17 more)

### Community 156 - "nexusops-challenge.mjs"
Cohesion: 0.33
Nodes (5): CHALLENGE_COMMON, meta, RESEARCH_COMMON, SCHEMA, TASKS

### Community 157 - "test_agent_ingestion.py"
Cohesion: 0.30
Nodes (10): _enrolled(), _heartbeat(), Agent ingest pipeline: hello, heartbeat, staleness transitions, events., A container absent from a later heartbeat is gone from the daemon., A payload at the agent's cap may be truncated — absence proves nothing., test_heartbeat_at_container_cap_skips_reconciliation(), test_heartbeat_removes_vanished_containers(), test_heartbeat_updates_status_metrics_and_containers() (+2 more)

### Community 158 - "sweep_deployments"
Cohesion: 0.33
Nodes (6): task, Execute one queued deployment. The engine owns all state transitions., Re-enqueue deployments the broker lost; fail ones whose worker died.…, run_deployment(), _run(), sweep_deployments()

### Community 159 - "BadRequest"
Cohesion: 0.36
Nodes (9): BadRequest, assert_safe_tcp_endpoint(), Validate a ``tcp://`` docker host endpoint for outbound connection. Docker…, test_tcp_endpoint_lax_mode_skips_resolution(), test_tcp_endpoint_rejects_embedded_credentials(), test_tcp_endpoint_rejects_non_tcp_schemes(), test_tcp_endpoint_requires_explicit_port(), test_tcp_endpoint_to_metadata_ip_is_blocked() (+1 more)

### Community 161 - "big_serial_pk"
Cohesion: 0.40
Nodes (4): big_serial_pk(), Identity PK for very high-volume tables (metrics, logs)., declared_attr, Mapped

### Community 162 - "8. Upstream binding and re-render triggers"
Cohesion: 0.33
Nodes (6): 8.1 Binding rules, 8.2 Certificate selection rule (this doc owns it), 8.3 Re-render triggers, 8.4 Drift, 8.5 How deployments hook routing (post-deploy route sync), 8. Upstream binding and re-render triggers

### Community 163 - "ApplicationBase"
Cohesion: 0.40
Nodes (4): ApplicationBase, Any, field_validator, Shared application fields; ``build_config`` is a free-form dict.

### Community 164 - "viewer_in_a"
Cohesion: 0.40
Nodes (5): org_a(), fixture, A least-privileged, **non-superadmin** member of organization A. Used to show…, The bootstrap organization plus a few resources created inside it., viewer_in_a()

### Community 165 - "require_server"
Cohesion: 0.09
Nodes (26): agent_heartbeat(), agent_hello(), _presented_token(), DbDep, post, Request, Response, First contact after enrollment: persist static host facts, negotiate cadence. (+18 more)

### Community 167 - "MonitorCreate"
Cohesion: 0.50
Nodes (4): MonitorBase, MonitorCreate, Shared validation bounds for monitor configuration., Payload for POST /monitors.

## Knowledge Gaps
- **405 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+400 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1628 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AuthContext` connect `AuthContext` to `v1/auth.py`, `NotFound`, `deps.py`, `docker_hosts.py`, `projects.py`, `incidents.py`, `deployment_engine.py`, `v1/deployments.py`, `test_deployments_simulated.py`, `containers.py`, `metrics_service.py`, `resolve_auth`, `monitor_service.py`, `auth_service.py`, `container_service.py`, `docker_host_service.py`, `PageParams`, `monitors.py`, `server_service.py`, `require_permission`, `servers.py`, `secret_service.py`, `Conflict`, `api_key_service.py`, `rotate_secret`, `notification_service.py`, `Hub`, `events.py`, `incident_service.py`, `scope_matches`, `get_sessionmaker`, `organization_service.py`, `AppError`, `list_audit_logs`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Why does `get_settings()` connect `get_settings` to `v1/auth.py`, `deps.py`, `resolve_client_ip`, `maintenance.py`, `metrics_service.py`, `monitor_service.py`, `assert_error_code`, `auth_service.py`, `container_service.py`, `BadRequest`, `server_service.py`, `test_ssrf.py`, `notification_service.py`, `test_auth_journey.py`, `main.py`, `Hub`, `env.py`, `Settings`, `seed.py`, `get_meta`, `get_redis`, `encrypt_str`, `20260922_1000-a3f1c8d24b6e_add_tenancy_foundation.py`, `config.py`, `ssrf.py`?**
  _High betweenness centrality (0.026) - this node is a cross-community bridge._
- **Why does `README.md - NexusOps overview` connect `README.md - NexusOps overview` to `docs/engineering-report.md - build and verification report`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **Are the 81 inferred relationships involving `AuthContext` (e.g. with `TenancyScopeError` and `MembershipStatus`) actually correct?**
  _`AuthContext` has 81 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `apiGet()` (e.g. with `ContainerDetailPage.test.tsx` and `mockApi()`) actually correct?**
  _`apiGet()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `meta`, `SCHEMA`, `RESEARCH_COMMON` to the rest of the system?**
  _405 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `client.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.02745995423340961 - nodes in this community are weakly interconnected._