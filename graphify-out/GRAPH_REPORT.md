# Graph Report - nexusops  (2026-10-07)

## Corpus Check
- 298 files · ~258,656 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: (none) 8, .example 1, .service 1)

## Summary
- 4284 nodes · 12671 edges · 176 communities (153 shown, 23 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1064 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7e19d60a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- AuthContext.tsx
- project_service.py
- App.tsx
- apiGet
- NotFound
- deps.py
- resolve_client_ip
- DeploymentListPage.tsx
- useAuth
- test_operations.py
- test_tenant_isolation.py
- ServerDetailPage.tsx
- v1/health.py
- client.ts
- projects.py
- incident_service.py
- deployment_engine.py
- SimulatedDockerProvider
- run_async
- Server
- test_deployments_simulated.py
- containers.py
- enums.py
- get_settings
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
- docker_hosts.py
- test_operation_registry.py
- monitors.py
- v1/search.py
- server_service.py
- v1/channels.py
- DockerProvider
- test_monitor_transport.py
- AgentContainerIn
- types.ts
- docker_real.py
- test_permissions.py
- Conflict
- servers.py
- BadRequest
- secret_service.py
- create_role
- test_schemas_server.py
- apikeys.py
- DashboardPage.tsx
- v1/auth.py
- core/tenancy.py
- create_operation
- alembic
- notification_service.py
- test_auth_journey.py
- compilerOptions
- v1/deployments.py
- errors.py
- organization.py
- StepLine
- seed.py
- monitor.py
- PageParams
- digest_of
- package.json
- events.py
- test_secrets.py
- README.md - NexusOps overview
- models/__init__.py
- api service (FastAPI / uvicorn :8000)
- UnprocessableEntity
- monitor_transport.py
- test_monitors_incidents.py
- redact_mapping
- get_latest_server_metrics
- test_event_registry.py
- Settings
- create_user
- tests/conftest.py
- test_agent_contract.py
- list_sessions
- devDependencies
- operation_service.py
- paginate
- test_migration_drift.py
- client_ip.py
- Deployment Architecture — NexusOps (target state)
- upsert_containers
- _raw_probe
- helpers.py
- list_alerts
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- journey.spec.ts
- sanitize_error
- 2. Entities
- Secrets Architecture
- env.py
- alert_service.py
- EnvironmentUpdate
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- _validate_resolution
- DeploymentRunner
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- StepFailure
- organization_service.py
- config.py
- log_service.py
- scripts
- logging.py
- process_heartbeat
- _entity_exists
- dependencies
- DeploymentDetailPage.tsx
- generate_secrets.sh
- rate_limit.py
- server_payload
- Product Roadmap — NexusOps Multi-Tenant Platform
- middleware.py
- .__init__
- APIModel
- permissions.py
- install.sh
- docker-entrypoint.sh
- integration/__init__.py
- test_ws_hub.py
- CLAUDE.md - project graphify rules
- Graphify query workflow (query / path / explain / update)
- frontend/index.html - SPA shell
- NexusOps Favicon — stylized letter 'N' lettermark in sky blue (#38bdf8) on a dark navy rounded square (#0b1120, 7px corner radius)
- nexusops-backend
- 8. Upstream binding and re-render triggers
- hub.py
- postgres service (PostgreSQL 17, loopback :5433)
- login_account
- nexusops-understand.mjs
- Invisible account lockout (5 fails -> 15 min, enumeration resistance)
- .dispatch
- instant_pacing
- nexusops-draft.mjs
- 20261004_1200-e7c4a2b9d1f3_add_operations_framework.py
- nexusops-challenge.mjs
- test_agent_ingestion.py
- create_api_key
- _FakeCtx
- AgentClient
- redis_down
- lax
- Domain Model — NexusOps as a Multi-Tenant Platform
- scope_matches
- _FakeAsyncClient
- test_created_at_defaults.py
- AuthContext
- membership_for_org
- .__tablename__
- _pace
- get_meta
- ._shallow_validate
- test_collect_recent_logs_is_incremental
- list_permissions
- 4. DNS ownership verification

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
- `2. Org resolution on every request` --references--> `resolve_auth()`  [INFERRED]
  docs/multi-tenancy.md → backend/app/api/deps.py
- `3. Cross-cutting decisions` --references--> `require_permission()`  [INFERRED]
  docs/domain-model.md → backend/app/api/deps.py
- `10. Phase 7 — Teams, grants & custom roles` --references--> `require_permission()`  [INFERRED]
  docs/product-roadmap.md → backend/app/api/deps.py
- `3.2 Enrollment v2` --references--> `require_server()`  [INFERRED]
  docs/node-agent-architecture.md → backend/app/api/v1/agent.py
- `7. The IDOR suite` --references--> `_search_users()`  [INFERRED]
  docs/multi-tenancy.md → backend/app/api/v1/search.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three authentication credential families with centralized permission checks** — docs_api_md_auth, docs_api_md_refresh_rotation, docs_api_md_api_keys, docs_agent_md_enrollment_token, docs_api_md_permission_model [EXTRACTED 1.00]
- **NexusOps compose stack services** — docker_compose_yml_nexusops_stack, docker_compose_yml_postgres_service, docker_compose_yml_redis_service, docker_compose_yml_mailpit_service, docker_compose_yml_api_service, docker_compose_yml_worker_service, docker_compose_yml_scheduler_service, docker_compose_yml_frontend_service, docker_compose_yml_nginx_service [EXTRACTED 1.00]
- **WebSocket real-time fan-out spine** — docs_architecture_md_websocket_hub, docs_api_md_websocket_channels, docker_compose_yml_redis_service, docs_architecture_md_event_bus, readme_react_spa [INFERRED 0.85]

## Communities (176 total, 23 thin omitted)

### Community 0 - "AuthContext.tsx"
Cohesion: 0.05
Nodes (29): Membership, User, AuthContext, AuthProvider(), AuthState, isOrgSelectionError(), MeResponse, ORG_SELECTION_FAILURES (+21 more)

### Community 1 - "project_service.py"
Cohesion: 0.15
Nodes (40): Any, AsyncSession, Request, UUID, Append an audit row using the caller's transaction (no commit here). The…, record(), actor_of(), _apply_update() (+32 more)

### Community 2 - "App.tsx"
Cohesion: 0.04
Nodes (80): ApiKeyOut, EnvironmentOut, EventItem, Page, ProjectOut, AlertsPage, ApiKeysPage, AuditLogPage (+72 more)

### Community 3 - "apiGet"
Cohesion: 0.06
Nodes (73): apiDelete(), apiGet(), apiPatch(), apiPost(), ApplicationOut, DeliveryOut, IncidentEventOut, IncidentDetailPage (+65 more)

### Community 4 - "NotFound"
Cohesion: 0.12
Nodes (41): NotFound, MembershipStatus, _apply_deactivation(), _assert_not_last_active_member(), _assert_not_last_active_superadmin(), create_user(), deactivate_user(), get_by_email() (+33 more)

### Community 5 - "deps.py"
Cohesion: 0.11
Nodes (33): _load_organization(), permission_dep(), Any, Organization, FastAPI dependencies: database session, authenticated tenant context, RBAC…, Dependency factory enforcing a permission; returns 403 when denied., require_permission(), _check() (+25 more)

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
Nodes (50): assert_error_code(), Assert envelope shape + code; returns the inner error object., test_metadata_endpoint_and_private_target_blocked(), _dispatch(), _dispatch_body(), _enrolled_node(), _mutate_in_system_scope(), MonkeyPatch (+42 more)

### Community 10 - "test_tenant_isolation.py"
Cohesion: 0.06
Nodes (76): dispose_engine(), get_sessionmaker(), async_sessionmaker, AsyncSession, apply_scope_to_session(), current_org(), current_scope(), org_scope() (+68 more)

### Community 11 - "ServerDetailPage.tsx"
Cohesion: 0.09
Nodes (35): MetricPoint, ServerListPage, CheckboxField(), ChartSeries, LineChart(), LineChartProps, PAD, buildServerPayload() (+27 more)

### Community 12 - "v1/health.py"
Cohesion: 0.20
Nodes (13): liveness(), get, Response, Health probes: liveness (always cheap) and readiness (checks dependencies).…, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness(), HealthOut (+5 more)

### Community 13 - "client.ts"
Cohesion: 0.07
Nodes (38): API_BASE, apiRequest(), buildUrl(), extractError(), getAccessToken(), getActiveOrgId(), onActiveOrgChange(), ORGANIZATION_HEADER (+30 more)

### Community 14 - "projects.py"
Cohesion: 0.11
Nodes (43): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+35 more)

### Community 15 - "incident_service.py"
Cohesion: 0.12
Nodes (48): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+40 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.08
Nodes (73): cancel_deployment(), post, Request, Queue a new deployment for an application/environment pair., Cancel a QUEUED deployment immediately or flag a RUNNING one., Queue a rollback to the last good version of this app/environment., rollback_deployment(), trigger_deployment() (+65 more)

### Community 17 - "SimulatedDockerProvider"
Cohesion: 0.07
Nodes (38): ContainerHealth, ContainerStatus, Container, Observed container state mirrored from an agent or docker provider., DockerProviderError, A provider operation failed. ``str()`` is safe to show/log., Any, datetime (+30 more)

### Community 18 - "run_async"
Cohesion: 0.07
Nodes (35): asyncio, flush_pending_publishes(), Wait for frames scheduled by ``after_commit`` hooks to reach Redis. The commit…, task, Execute one queued deployment. The engine owns all state transitions., Re-enqueue deployments the broker lost; fail ones whose worker died.…, run_deployment(), _run() (+27 more)

### Community 19 - "Server"
Cohesion: 0.14
Nodes (26): agent_heartbeat(), agent_hello(), claim_operation(), _presented_token(), DbDep, post, Request, Response (+18 more)

### Community 20 - "test_deployments_simulated.py"
Cohesion: 0.15
Nodes (29): execute_deployment(), Run one deployment to a terminal state. Never raises; safe to re-run., get_application(), get_environment(), _as_worker(), _delivery_chain(), _owner_ctx(), _queue() (+21 more)

### Community 21 - "containers.py"
Cohesion: 0.06
Nodes (62): _action_route(), _endpoint(), _container_out(), _ev(), get_container(), _like_pattern(), list_container_logs(), list_containers() (+54 more)

### Community 22 - "enums.py"
Cohesion: 0.10
Nodes (34): CredentialKind, MetricGranularity, Closed registries of domain enumerations. Member names equal their values…, String enum; member names equal values so name/value storage never disagrees., StrEnum, aggregate_rollups(), dashboard_summary(), ensure_server() (+26 more)

### Community 23 - "get_settings"
Cohesion: 0.07
Nodes (60): argon2, argon2_exceptions, AsyncSession, User, Resolve the caller's identity only (no organization)., _resolve_identity(), _user_from_api_key(), get_settings() (+52 more)

### Community 24 - "Domain Routing — NexusOps"
Cohesion: 0.11
Nodes (18): 10. Wildcards and catch-all, 11. User journey, 12. API surface, permissions, audit, 13. Monitoring tie-in, 1. Scope and current state, 2. Where nginx runs, 3.1 Domain, 3.2 Route (+10 more)

### Community 25 - "monitor_service.py"
Cohesion: 0.15
Nodes (38): MonitorStatus, Monitor, MonitorCheck, get_transport(), Pick the transport matching the monitor URL scheme., _active_incident(), _audit(), claim_due_monitors() (+30 more)

### Community 26 - "Node & Agent Architecture"
Cohesion: 0.12
Nodes (17): 1. Scope and stance, 3.1 Current state (real), 3.2 Enrollment v2, 3.3 Token storage & rotation with dual-token grace, 3.4 Revocation semantics — fixing the 401 hot-loop, 3.5 Reconnect / offline states, 3. Agent lifecycle, 6.1 Token scope (+9 more)

### Community 27 - "test_agent_backoff.py"
Cohesion: 0.08
Nodes (36): AST, agent_fixture(), _install_sleep(), fake_sleep(), _load_agent(), _patch_host(), Any, fixture (+28 more)

### Community 28 - "SimulatedDeploymentRunner"
Cohesion: 0.25
Nodes (23): Staged docker-style simulation used by v1 deployments., Canonical step identifiers stored on :class:`DeploymentStep` rows., SimulatedDeploymentRunner, StepName, _collect(), _ctx(), Unit tests for SimulatedDeploymentRunner (async generators, no broker)., RESOLVE_CONFIG is planned by the engine, not produced by a runner. (+15 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.09
Nodes (30): build_heartbeat(), collect_container_stats(), collect_containers(), cpu_percent_since(), disk_stats(), _docker_request(), _interruptible_sleep(), load1() (+22 more)

### Community 30 - "integration/conftest.py"
Cohesion: 0.08
Nodes (27): alembic_config, close_redis(), _clean_slate(), client(), _ensure_database(), _migrated_database(), org_db(), owner() (+19 more)

### Community 31 - "auth_service.py"
Cohesion: 0.11
Nodes (46): active_memberships(), The user's memberships in non-suspended organizations, oldest first. Reads only…, ActorType, AuditResult, _audit(), _bootstrap_organization(), change_own_password(), count_users() (+38 more)

### Community 32 - "container_service.py"
Cohesion: 0.11
Nodes (34): clip(), Provider abstraction for docker hosts (real daemon or simulated). Providers are…, Truncate *text* to *limit* characters, stripping control chars., describe_provider_error(), is_simulated(), provider_for(), Exception, Provider selection based on a docker host's endpoint URL. Mapping: *… (+26 more)

### Community 33 - "docker_host_service.py"
Cohesion: 0.15
Nodes (31): DockerHostStatus, DockerHost, _assert_endpoint_allowed(), _assert_name_free(), create_host(), delete_host(), endpoint_scheme(), list_hosts() (+23 more)

### Community 34 - "docker_hosts.py"
Cohesion: 0.07
Nodes (54): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+46 more)

### Community 35 - "test_operation_registry.py"
Cohesion: 0.12
Nodes (20): OperationType, The whitelist. Nothing outside this enum ships as an exec surface. Each type…, Any, Validate *params* against the type's model and return the stored form.…, validate_params(), ensure_dispatchable(), Refuse a type whose capability this deployment cannot confirm. The capability…, MonkeyPatch (+12 more)

### Community 36 - "monitors.py"
Cohesion: 0.16
Nodes (34): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+26 more)

### Community 37 - "v1/search.py"
Cohesion: 0.13
Nodes (31): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+23 more)

### Community 38 - "server_service.py"
Cohesion: 0.12
Nodes (35): ServerStatus, _actor_kwargs(), container_counts(), create_server(), delete_server(), get_server(), list_servers(), list_tags_with_usage() (+27 more)

### Community 39 - "v1/channels.py"
Cohesion: 0.15
Nodes (28): create_channel(), delete_channel(), get_channel(), list_channels(), list_deliveries(), DbDep, delete, Depends (+20 more)

### Community 40 - "DockerProvider"
Cohesion: 0.09
Nodes (12): DockerProvider, Any, datetime, Protocol, List containers visible to the provider., Inspect a single container by id (short ids allowed)., List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``., List volumes: keys ``name``, ``driver``, ``mountpoint``. (+4 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.13
Nodes (34): CheckResult, HTTPMonitorTransport, Deterministic fake checker for ``sim://`` monitors and demo environments.…, Real HTTP(S) probe using httpx with per-monitor settings. Redirects are…, SimulatedTransport, _check(), clock(), FakeClock (+26 more)

### Community 42 - "AgentContainerIn"
Cohesion: 0.14
Nodes (28): AgentContainerIn, AgentHeartbeatIn, AgentHelloIn, field_validator, First contact from an agent after enrollment; fills static host facts., Observed container state reported by an agent., Periodic metrics + observed containers from an enrolled agent., _container() (+20 more)

### Community 43 - "types.ts"
Cohesion: 0.02
Nodes (105): ApiError, AlertOut, AuditEntry, ChannelOut, CheckOut, ContainerOut, CursorPage, DeploymentLogLine (+97 more)

### Community 44 - "docker_real.py"
Cohesion: 0.09
Nodes (28): ContainerInfo, ContainerStats, Normalized view of a container as reported by any provider., Point-in-time resource usage snapshot., _as_float(), _compute_stats(), _cpu_percent(), _network_bytes() (+20 more)

### Community 45 - "test_permissions.py"
Cohesion: 0.17
Nodes (9): _auth_context(), Unit tests for the permission registry, scope matching and RBAC gate., A fake context in the given organization. ``membership_status=None`` models a…, test_api_key_scope_intersects_role_permissions(), test_membership_is_required_for_authority(), test_plain_user_without_permissions_is_denied(), test_superadmin_bypasses_everything(), test_superadmin_owned_api_key_is_limited_to_its_scope() (+1 more)

### Community 46 - "Conflict"
Cohesion: 0.14
Nodes (27): Conflict, create_role(), delete_role(), effective_permissions(), get_role(), list_roles(), permission_registry(), permissions_for_role() (+19 more)

### Community 47 - "servers.py"
Cohesion: 0.08
Nodes (41): create_server(), delete_server(), _detail(), get_server(), list_servers(), list_tags(), AsyncSession, DbDep (+33 more)

### Community 48 - "BadRequest"
Cohesion: 0.14
Nodes (27): BadRequest, assert_safe_tcp_endpoint(), is_simulation_url(), SSRF guard applied to every operator-supplied outbound URL. Monitors and…, Validate a ``tcp://`` docker host endpoint for outbound connection. Docker…, True when *url* targets the built-in simulated checker (``sim://``)., Internal signal: a specific SSRF rule matched (never shown to clients)., UrlRejected (+19 more)

### Community 49 - "secret_service.py"
Cohesion: 0.09
Nodes (45): create_secret(), delete_secret(), get_secret(), list_secrets(), DbSession, delete, Depends, get (+37 more)

### Community 50 - "create_role"
Cohesion: 0.16
Nodes (18): create_role(), delete_role(), list_roles(), CurrentUser, DbSessionDep, delete, get, post (+10 more)

### Community 51 - "test_schemas_server.py"
Cohesion: 0.21
Nodes (22): Payload for registering a server., Partial update. ``tags`` replaces the full set when provided., ServerCreate, ServerUpdate, _base(), parametrize, Unit tests for app.schemas.server (validation only, no I/O)., test_empty_ip_is_allowed_but_whitespace_collapses() (+14 more)

### Community 52 - "apikeys.py"
Cohesion: 0.16
Nodes (18): create_api_key(), list_api_keys(), CurrentUser, DbSessionDep, delete, get, post, Request (+10 more)

### Community 53 - "DashboardPage.tsx"
Cohesion: 0.12
Nodes (14): DashboardSummary, DashboardPage, asFeedItem(), badgeLevel(), DashboardPage(), FeedItem, formatTimestamp(), MetaInfo (+6 more)

### Community 54 - "v1/auth.py"
Cohesion: 0.08
Nodes (51): change_password(), _clear_refresh_cookie(), _cookies_secure(), login(), logout(), me(), _optional_actor(), AsyncSession (+43 more)

### Community 55 - "core/tenancy.py"
Cohesion: 0.09
Nodes (34): _apply_scope_guc(), _desired_guc(), _guard(), _has_org_predicate(), install_tenancy_guards(), _mappers_of(), org_scoped_table_names(), Any (+26 more)

### Community 56 - "create_operation"
Cohesion: 0.15
Nodes (20): cancel_operation(), create_operation(), get_operation(), list_operations(), DbDep, Depends, get, post (+12 more)

### Community 57 - "alembic"
Cohesion: 0.05
Nodes (23): alembic, _app_role_credentials(), _assert_fully_backfilled(), _backfill_org_ids(), _drop_constraint(), add tenancy foundation Phase 1 of the platform roadmap: organizations,…, Carry a value into a PL/pgSQL block. ``CREATE ROLE``/``ALTER ROLE`` are utility…, Application role name/password from settings (never hard-coded). (+15 more)

### Community 58 - "notification_service.py"
Cohesion: 0.06
Nodes (75): ChannelType, DeliveryStatus, NotificationError, Any, BaseException, Exception, Low-level notification transports: SMTP email and outgoing webhooks. These…, POST *payload* as JSON to *url*; 2xx is success, anything else raises. Response… (+67 more)

### Community 59 - "test_auth_journey.py"
Cohesion: 0.11
Nodes (26): cookie_attributes(), Response, Register a user; returns ``(request_payload, response_body)``., The raw Set-Cookie header carrying the refresh token., Extract just the opaque token from a Set-Cookie header., Parse Set-Cookie attributes (lowercased keys, empty string for flags)., refresh_cookie_header(), refresh_cookie_value() (+18 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "v1/deployments.py"
Cohesion: 0.19
Nodes (22): _attribute_step_idx(), _emails_for(), get_deployment(), list_application_deployments(), list_deployment_logs(), _list_deployments(), _parse_sort(), _parse_statuses() (+14 more)

### Community 62 - "errors.py"
Cohesion: 0.07
Nodes (30): ASGIApp, _error_payload(), FastAPI, Request, Error taxonomy and the single place where API error envelopes are shaped. Every…, register_exception_handlers(), handle_app_error(), handle_http_exception() (+22 more)

### Community 63 - "organization.py"
Cohesion: 0.13
Nodes (22): create_organization(), list_my_organizations(), CurrentUser, DbSessionDep, get, IdentityUser, post, Request (+14 more)

### Community 64 - "StepLine"
Cohesion: 0.26
Nodes (8): LogLevel, _commit_short(), Deployment runner port plus a faithful simulated implementation.…, Everything a runner needs to execute one deployment., One streamed output line for a step., RunContext, _slug(), StepLine

### Community 65 - "seed.py"
Cohesion: 0.13
Nodes (28): encrypt_str(), OrganizationStatus, UserStatus, A named permission set. ``org_id`` is NULL for every row in v1 — the five…, Role, User, Membership, Organization (+20 more)

### Community 66 - "monitor.py"
Cohesion: 0.09
Nodes (27): is_sensitive_header(), mask_sensitive_headers(), MonitorBase, MonitorCreate, MonitorSortField, MonitorUpdate, field_serializer, Schemas for uptime monitors and their check history. (+19 more)

### Community 67 - "PageParams"
Cohesion: 0.15
Nodes (25): list_applications(), list_environments(), list_projects(), Depends, get, ReadUser, CursorPage, page_params() (+17 more)

### Community 68 - "digest_of"
Cohesion: 0.08
Nodes (27): decrypt_str(), digest_of(), _fernet(), Short server-verifiable digest used for change detection display. HMAC-SHA256…, parametrize, test_decrypt_with_wrong_ciphertext_raises_value_error(), test_digest_length_and_determinism(), test_encrypt_decrypt_roundtrip() (+19 more)

### Community 69 - "package.json"
Cohesion: 0.13
Nodes (15): name, private, type, version, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom (+7 more)

### Community 70 - "events.py"
Cohesion: 0.19
Nodes (16): _decode_cursor(), _encode_cursor(), list_event_types(), list_events(), datetime, DbSession, Depends, get (+8 more)

### Community 71 - "test_secrets.py"
Cohesion: 0.09
Nodes (29): Exception, A ``${secret:KEY}`` reference could not be resolved. Fail-closed. Carries…, Resolve every ``${secret:KEY}`` reference in an environment's config. INTERNAL…, resolve_secrets_for_environment(), SecretResolutionError, _create(), _environment_config(), Secrets: metadata-only reads, rotation versioning, deploy-time resolution. (+21 more)

### Community 72 - "README.md - NexusOps overview"
Cohesion: 0.09
Nodes (42): docker-compose.dev.yml - dev overlay, docker-compose.docker-sock.yml - docker socket override, docker-compose.yml - full stack definition, docs/agent.md - agent guide, docs/api.md - API guide, Append-only audit log (Postgres BEFORE UPDATE OR DELETE trigger), docs/architecture.md - system architecture, docs/deployment.md - deployment and operations guide (+34 more)

### Community 73 - "models/__init__.py"
Cohesion: 0.08
Nodes (64): _org_scoped_classes(), Mapped classes marked :class:`~app.models.base.OrgScoped`. Reads the mapper…, Base, big_serial_pk(), json_column(), org_id_column(), OrgScoped, datetime (+56 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "UnprocessableEntity"
Cohesion: 0.17
Nodes (22): UnprocessableEntity, assert_safe_url(), _raise_block(), Validate *url* for outbound requests; return the parsed URL or raise 422.…, Reject non-empty values that are not valid IPv4/IPv6 addresses., _validate_ip(), Validate + normalise scopes; returns the deduplicated list. Accepts exact…, validate_scopes() (+14 more)

### Community 76 - "monitor_transport.py"
Cohesion: 0.09
Nodes (23): assert_safe_url_async(), Async wrapper around :func:`assert_safe_url`; DNS runs off the loop., CheckOutcome, coerce_headers(), _decode(), MonitorTransport, Any, BaseException (+15 more)

### Community 77 - "test_monitors_incidents.py"
Cohesion: 0.31
Nodes (8): _create_monitor(), Monitor checks driving the full down -> incident -> recovery lifecycle., Regression: probe headers and URL query credentials never leave the API. Probe…, A monitor's checks, incidents and timeline all live in its organization, so the…, test_check_now_endpoint_runs_immediately(), test_down_then_recover_lifecycle(), test_monitor_responses_mask_probe_credentials(), test_notification_pipeline_queues_delivery_for_down_event()

### Community 78 - "redact_mapping"
Cohesion: 0.22
Nodes (13): _is_sensitive_key(), Substring match on a normalised key so header-style names are caught too.…, Return a copy of *data* with sensitive values replaced. Used by audit metadata…, redact_mapping(), parametrize, Unit tests for app.core.logging redaction (pure functions only)., test_case_insensitive_substring_match(), test_flat_sensitive_keys_redacted() (+5 more)

### Community 79 - "get_latest_server_metrics"
Cohesion: 0.14
Nodes (18): get_dashboard_summary(), get_latest_server_metrics(), get_server_metrics(), CurrentUser, DbDep, Depends, get, UUID (+10 more)

### Community 80 - "test_event_registry.py"
Cohesion: 0.21
Nodes (8): event_type_catalogue(), is_known_event_type(), Canonical registry of system-event types. Single source of truth shared by…, Return True when *event_type* is part of the canonical registry., Serialise the registry for the ``/events/types`` endpoint., Registry coherence: schema-advertised event types must equal the canonical…, test_catalogue_serialises_every_entry(), test_known_event_lookup()

### Community 81 - "Settings"
Cohesion: 0.12
Nodes (7): field_validator, model_validator, Whether the runtime connection is the RLS-enforced application role. False…, Username from :attr:`database_url`, or ``None`` if it is unparseable., Validated application settings (loaded from environment / .env)., Settings, BaseSettings

### Community 82 - "create_user"
Cohesion: 0.14
Nodes (21): create_user(), deactivate_user(), get_user(), list_users(), CurrentUser, DbSessionDep, delete, get (+13 more)

### Community 83 - "tests/conftest.py"
Cohesion: 0.20
Nodes (8): configure_test_env(), Test bootstrap: pin every cached setting BEFORE the first ``app`` import. The…, KEY=VALUE pairs from the repo .env (first definition wins); never logged., Export the exact settings the app caches; host values cannot leak through., _read_dot_env(), os, sys, urllib_parse

### Community 84 - "test_agent_contract.py"
Cohesion: 0.20
Nodes (15): agent_fixture(), _load_agent(), _patch_stats(), Any, fixture, MonkeyPatch, Contract tests: the shipped agent's payloads must satisfy the ingest schemas.…, One-shot docker stats reduce to cpu/mem/limit fields the schema accepts, with… (+7 more)

### Community 85 - "list_sessions"
Cohesion: 0.24
Nodes (10): list_sessions(), CurrentUser, DbSessionDep, delete, get, Request, UUID, Active sessions of this organization's members. Defaults to the caller's own;… (+2 more)

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "operation_service.py"
Cohesion: 0.14
Nodes (32): OperationStatus, Lifecycle of one node operation (node-agent-architecture.md §5.1).…, Operation, One whitelisted action for one node, with a CAS lifecycle. ``attempts`` is…, _active_org(), _bounded(), cancel_operation(), claim_operation() (+24 more)

### Community 88 - "paginate"
Cohesion: 0.12
Nodes (17): list_audit_logs(), datetime, DbSession, Depends, get, PageParamsDep, Newest-first audit trail with optional filters. No write routes exist for this…, paginate() (+9 more)

### Community 89 - "test_migration_drift.py"
Cohesion: 0.25
Nodes (7): alembic_autogenerate, alembic_migration, Model / migration drift: the schema in the database must match the models.…, ``Base.metadata`` and the migrated database must describe the same schema., The DB whitelist and ``OperationType`` are the same closed set. The migration…, test_models_and_migrations_do_not_drift(), test_operations_type_check_matches_the_enum()

### Community 90 - "client_ip.py"
Cohesion: 0.29
Nodes (7): _is_trusted(), _parse_networks(), Client-IP resolution behind chained reverse proxies. The API never takes TCP…, Parse a comma-separated CIDR list; malformed entries are skipped., test_parse_networks_skips_malformed_entries(), functools, _Network

### Community 91 - "Deployment Architecture — NexusOps (target state)"
Cohesion: 0.14
Nodes (14): 10. Events and WS during runs, 11. Post-deploy hooks, 12. Rollback semantics (existing behavior kept), 13. The simulated runner stays — labeled, 14. Open questions, 1. Current state — what is real and what is simulated, 3. Target pipeline, 4. Runner registry — the DI fix (+6 more)

### Community 92 - "upsert_containers"
Cohesion: 0.13
Nodes (17): server_metrics_channel(), _apply_agent_entry(), ensure_docker_host(), _publish_live_frame(), datetime, Best-effort push of a lightweight metric frame for live dashboards., Return the agent-backed Docker host for a server, creating it if needed. The…, Write one heartbeat entry onto a container row. Kept complete at every call… (+9 more)

### Community 93 - "_raw_probe"
Cohesion: 0.20
Nodes (10): _app_role_dsn(), A libpq DSN for the RLS-enforced application role (no ORM, no guard)., Run one statement as ``nexusops_app`` with an explicit GUC. Parameterized like…, Raw SQL as the application role: the policies alone return nothing. Written…, Adding ``org_id`` to ``audit_logs`` must not have opened a way to edit it. The…, ``WITH CHECK`` is not decoration: an unlucky INSERT cannot cross tenants., _raw_probe(), test_audit_trail_is_still_append_only_after_tenancy() (+2 more)

### Community 94 - "helpers.py"
Cohesion: 0.08
Nodes (28): bearer(), error_of(), login_headers(), Any, Pure helpers for journey tests: payloads, auth shortcuts, cookie parsing., Headers for a logged-in caller, including its active organization., Unwrap an API error envelope., Bearer header, optionally naming the active organization. Every org-scoped… (+20 more)

### Community 95 - "list_alerts"
Cohesion: 0.21
Nodes (14): list_alerts(), mark_all_read(), mark_read(), CurrentUser, DbDep, Depends, get, post (+6 more)

### Community 96 - "NexusOps (self-hosted infrastructure management and monitoring platform)"
Cohesion: 0.20
Nodes (10): mailpit service (dev SMTP sink + web UI :8025), NexusOps compose stack (8 services on one network), HIGH finding: redirect-following SSRF in uptime monitors (fixed: follow_redirects=False + per-hop guard), SSRF guard (assert_safe_url, per-redirect-hop validation, assert_safe_tcp_endpoint), Mailpit SMTP port internal-only (host-side injection needs extra mapping), Host port knobs (NEXUSOPS_HTTP_PORT/POSTGRES/REDIS/MAILPIT/VITE), SPA entry point (loads /src/main.tsx, dark color-scheme), Uptime monitors -> incidents -> notifications flow (+2 more)

### Community 97 - "REST API surface (/api/v1)"
Cohesion: 0.29
Nodes (7): Cursor (keyset) and offset pagination envelopes, Permission model (data-driven registry, require_permission, wildcard scopes), REST API surface (/api/v1), RBAC registry (PERMISSIONS + ROLE_MATRIX + scope_matches), Adding a new resource: 7-step checklist (model -> migration -> schemas -> service -> router -> tests -> frontend), Alembic migration workflow (autogenerate, models __init__ export, entrypoint apply), Command palette (Ctrl/Cmd+K)

### Community 98 - "journey.spec.ts"
Cohesion: 0.18
Nodes (11): EDGE, MAILPIT, ADMIN, Bootstrap, bootstrapVia(), test, ADMIN, formLogin() (+3 more)

### Community 99 - "sanitize_error"
Cohesion: 0.25
Nodes (7): Exception, Build a compact, secret-free description of a provider failure. Only the…, sanitize_error(), 5.1 Model and lifecycle, 5.2 Whitelisted operation types, 5.3 Result reporting and audit, 5. The Operations framework

### Community 100 - "2. Entities"
Cohesion: 0.22
Nodes (9): 2.1.1 ApiKey org binding detail, 2.2.1 Environment promotion detail, 2.2 Delivery (existing models, extended), 2.3 Infrastructure — Nodes, 2.4 Routing & TLS (new subsystem), 2.5 Secrets (existing, re-scoped), 2.6 Observability (existing, org-scoped via parents), 2.7 Backups, connections, billing (new subsystems, design-only in early phases) (+1 more)

### Community 101 - "Secrets Architecture"
Cohesion: 0.14
Nodes (14): 10. Resolution flow at deploy time, 2.1 Resolution runs inside org scope, 2.2 Migration mapping, 2. Target scope model (org / project / environment layering), 3.1 What this fixes, 3. SecretVersion — append-only history, 4.1 Audit event at resolution time, 4. Resolution authorization (+6 more)

### Community 102 - "env.py"
Cohesion: 0.24
Nodes (10): _database_url(), Alembic environment: metadata comes from app.models, URL from app settings., Migrations run as the table **owner**, never as the application role. The owner…, Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online(), Owner-role DSN for Alembic and the container entrypoint. Migrations… (+2 more)

### Community 103 - "alert_service.py"
Cohesion: 0.21
Nodes (17): AlertSeverity, Alert, create_alert(), get_alert(), mark_all_read(), mark_read(), AsyncSession, UUID (+9 more)

### Community 104 - "EnvironmentUpdate"
Cohesion: 0.22
Nodes (9): EnvironmentBase, EnvironmentCreate, EnvironmentUpdate, field_validator, Shared environment fields., Payload to create an environment under an application., Partial environment update; omitted fields are left untouched., 1.4 Deploy-time resolution today (+1 more)

### Community 105 - "redis service (Redis 7, no persistence, loopback :6390)"
Cohesion: 0.22
Nodes (11): redis service (Redis 7, no persistence, loopback :6390), WebSocket API (/api/v1/ws handshake, frames, limits), WebSocket channels (global, server-metrics, container-logs, deployment-logs, incidents), Deployment engine (queue_deployment / execute_deployment / sweeper backstop), Real-time spine: PostgreSQL system_events + Redis pub/sub, Rollback as a new deployment (rollback_of_id), WebSocket hub (framework-thin, Redis fan-in, per-socket queues), Test suites (pytest unit+integration, vitest, Playwright e2e) (+3 more)

### Community 106 - "NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)"
Cohesion: 0.18
Nodes (12): Agent security model (one-way telemetry, no command channel), Agent enrollment token (X-Agent-Token, nxa_..., SHA-256 at rest), Agent heartbeat exponential backoff (cap 5 min, exit 1 on revoked token), agent/install.sh (enrollment installer), Agent metrics collection (/proc statvfs Docker socket), NexusOps agent (stdlib-only Python, agent/nexusops_agent.py), Agent systemd hardening (ProtectSystem=strict, NoNewPrivileges), Agent ingest API (POST /agent/hello, POST /agent/heartbeat) (+4 more)

### Community 107 - "_validate_resolution"
Cohesion: 0.28
Nodes (8): _is_forbidden_address(), True when *addr* points into a network the server must never contact.…, Resolve *hostname* (AF_UNSPEC) and refuse any non-public answer., _validate_resolution(), test_validate_resolution_dedupes_and_returns_addresses(), test_validate_resolution_passes_hostname_through(), IPv4Address, IPv6Address

### Community 108 - "DeploymentRunner"
Cohesion: 0.25
Nodes (6): DeploymentRunner, Protocol, Stream output lines for *step_name*; raise StepFailure to fail it., Adapter interface implemented by real (future) and simulated runners., Return the ordered step names for this run., 2. What survives unchanged

### Community 109 - "Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)"
Cohesion: 0.25
Nodes (9): API keys (X-API-Key, nxo_..., scope intersection), First boot sequence (api entrypoint migrates, compose never seeds), Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test), Makefile workflows (up/test/lint/typecheck/migrate/seed), HIGH finding: API-key scope bypass for superadmin-owned keys (fixed: scope intersection first), Security audit 2026-09 (26 raw findings -> 20 confirmed, all fixed), HIGH finding: known seed superadmin + API key backdoor (fixed: NEXUSOPS_ALLOW_SEED opt-in, one-time password), Threat model (edge attacker, malicious agent, curious operator, leaked token, SSRF) (+1 more)

### Community 110 - "StepFailure"
Cohesion: 0.25
Nodes (7): Exception, Raised by a runner when a step fails irrecoverably., StepFailure, 5.1 Operation whitelist additions (deployments), 5.2 `RunContext` extension, 5. `AgentDeploymentRunner` — real execution over agent operations, 9. Cancellation and per-step timeouts

### Community 111 - "organization_service.py"
Cohesion: 0.16
Nodes (25): add_member(), create_organization(), get_organization(), membership_for_user(), AsyncSession, Membership, Organization, Request (+17 more)

### Community 112 - "config.py"
Cohesion: 0.21
Nodes (13): fail_on_bad_config(), Central configuration. All runtime configuration flows through this module so…, Exit immediately with a readable message if configuration is invalid. Also…, _app_for_environment(), MonkeyPatch, ENVIRONMENT gating contract: docs exposure and HSTS (see .env.example).…, create_app() with get_settings() patched to the given environment., test_non_production_does_not_emit_hsts() (+5 more)

### Community 113 - "log_service.py"
Cohesion: 0.10
Nodes (32): _decode_frame(), _max_log_id(), _poll_new_lines(), Parse a Redis pub/sub frame ``{ts, stream, message}`` into a LogLine., Highest persisted log id for a container (poll fallback watermark)., Fetch log rows persisted after ``last_seen['id']`` (poll fallback)., Live-tail a container's logs. Primary source is the Redis pub/sub channel…, stream_container_logs() (+24 more)

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "logging.py"
Cohesion: 0.06
Nodes (63): configure_logging(), get_logger(), _orjson_dumps(), Any, Structured logging via structlog. Every log record carries timestamp, level,…, Configure structlog + stdlib logging once at process start. Everything…, Celery application: periodic cadences live here, dynamic work is claimed…, Deployment execution task + stuck-deployment sweeper. (+55 more)

### Community 116 - "process_heartbeat"
Cohesion: 0.25
Nodes (8): process_heartbeat(), Mark the agent enrolled and persist its static host facts., Apply a heartbeat: refresh facts, store a RAW metric, mirror containers.…, register_agent_hello(), 7.1 Version visibility (fix the stub), 7.2 Out-of-date handling, 7.3 Future: self-update, 7. Versioning & upgrades

### Community 117 - "_entity_exists"
Cohesion: 0.14
Nodes (15): _entity_exists(), Whether *id_* exists **for this organization**. Runs inside the socket's…, The hub's subscribe-time existence check under concurrent orgs.…, test_websocket_entity_checks_stay_inside_their_socket_org(), check(), 10. Migration (Phase 1), 1. Tenancy invariants, 2.1 Org creation — v1 decision (+7 more)

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
Cohesion: 0.24
Nodes (14): RateLimited, _memory_count_and_ttl(), rate_limit(), _dependency(), Redis-backed fixed-window rate limiting as a FastAPI dependency factory. Auth-…, Fixed-window counter backed by process memory. Returns (count, ttl)., Return a dependency enforcing *limit* requests per window per IP. With…, _FakeRequest (+6 more)

### Community 122 - "server_payload"
Cohesion: 0.13
Nodes (22): A valid POST /servers body with per-test overrides., server_payload(), _create_server(), Server CRUD, cascade delete, audit trail rows and audit immutability., The HTTP listing path — schema serialization is exercised end-to-end. A…, ``/servers`` is a temporary alias for pre-rename clients. It must keep working…, test_agent_token_rotation_invalidates_previous(), test_audit_log_api_serializes_and_filters() (+14 more)

### Community 123 - "Product Roadmap — NexusOps Multi-Tenant Platform"
Cohesion: 0.12
Nodes (17): 0. Stance, 10. Phase 7 — Teams, grants & custom roles, 11. Phase 8 — Backups, 12. Phase 9 — Billing & metering, 13.1 Scope-creep gates — what must be true before each expansion, 13. First commercially meaningful version, 14. Biggest risks (short form), 15. Reading order (+9 more)

### Community 124 - "middleware.py"
Cohesion: 0.29
Nodes (6): HTTP middleware: request ids, security headers, structured access logs., starlette_middleware_base, starlette_requests, starlette_responses, starlette_types, time

### Community 126 - "APIModel"
Cohesion: 0.04
Nodes (89): AgentHelloOut, Agent-facing schemas. Payloads are data only — never executed., Tells the agent how often to report., AlertOut, Schemas for operator-facing alerts., ApiKeyCreateRequest, API key schemas. Raw keys appear exactly once, at creation., AuditOut (+81 more)

### Community 127 - "permissions.py"
Cohesion: 0.29
Nodes (5): permission_exists(), PermissionSpec, Permission registry and role matrix. Permissions are *data*: the registry below…, test_permission_exists_helper(), fnmatch

### Community 137 - "test_ws_hub.py"
Cohesion: 0.05
Nodes (64): AppError, Exception, Base class for expected, client-facing errors., _authenticate_api_key(), _authenticate_jwt(), _bind_organization(), _close_socket(), Connection (+56 more)

### Community 146 - "8. Upstream binding and re-render triggers"
Cohesion: 0.33
Nodes (6): 8.1 Binding rules, 8.2 Certificate selection rule (this doc owns it), 8.3 Re-render triggers, 8.4 Drift, 8.5 How deployments hook routing (post-deploy route sync), 8. Upstream binding and re-render triggers

### Community 147 - "hub.py"
Cohesion: 0.09
Nodes (35): get_redis(), ping(), Shared async Redis client., SystemEvent, _after_commit_publish(), _after_rollback_drop(), event_frame_from_row(), publish() (+27 more)

### Community 148 - "postgres service (PostgreSQL 17, loopback :5433)"
Cohesion: 0.29
Nodes (7): postgres service (PostgreSQL 17, loopback :5433), Fernet encryption at rest (ENCRYPTION_KEY, write-once), Backups (pgdata volume, nightly pg_dump, ephemeral Redis), Required secrets (POSTGRES_PASSWORD, JWT_SECRET >= 32 chars, ENCRYPTION_KEY Fernet), Production hardening checklist (secrets, ENVIRONMENT, no seed, TLS, rotation), Compose vs host network namespaces (postgres:5432 vs 127.0.0.1:5433), Simulation mode (SIMULATION_MODE)

### Community 149 - "login_account"
Cohesion: 0.12
Nodes (22): login_account(), AsyncClient, Login and unpack tokens, the raw cookie header and the user object., Bootstrap owner account + session; returns ``(credentials, login_result)``. The…, A fresh, deliverable-shaped address unique to a single test. ``example.com`` is…, register_and_login(), unique_email(), test_second_register_without_invite_is_rejected() (+14 more)

### Community 150 - "nexusops-understand.mjs"
Cohesion: 0.33
Nodes (5): COMMON, meta, out, READERS, SCHEMA

### Community 151 - "Invisible account lockout (5 fails -> 15 min, enumeration resistance)"
Cohesion: 0.33
Nodes (6): Invisible account lockout (5 fails -> 15 min, enumeration resistance), Unified error envelope (code, message, request_id), Per-IP rate limiting (Redis fixed window), Request lifecycle (edge -> middleware -> rate limit -> deps -> router), Client IP resolution (resolve_client_ip, TRUSTED_PROXY_CIDRS, XFF overwrite), EmailStr rejects reserved domains (login 422 on .test/.local/.arpa)

### Community 152 - ".dispatch"
Cohesion: 0.60
Nodes (3): Request, Response, RequestResponseEndpoint

### Community 153 - "instant_pacing"
Cohesion: 0.40
Nodes (4): instant_pacing(), fixture, MonkeyPatch, Remove the per-line sleeps; pacing bounds are asserted separately.

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

### Community 158 - "create_api_key"
Cohesion: 0.40
Nodes (5): create_api_key(), Request, Revoke a key owned by *owner_id*. Foreign keys look like NotFound (no leak)., Create a key for *user_id*. Returns ``(row, raw_key)`` — raw shown once. The…, revoke_api_key()

### Community 159 - "_FakeCtx"
Cohesion: 0.40
Nodes (3): _FakeCtx, Duck-typed stand-in for AuthContext., test_require_permission_returns_ctx_when_allowed()

### Community 161 - "redis_down"
Cohesion: 0.40
Nodes (4): _clean_memory_windows(), fixture, MonkeyPatch, redis_down()

### Community 162 - "lax"
Cohesion: 0.40
Nodes (5): lax(), fixture, Production posture: private targets are NOT allowed (resolution runs)., Simulation posture: resolution skipped, syntax still enforced., strict()

### Community 163 - "Domain Model — NexusOps as a Multi-Tenant Platform"
Cohesion: 0.40
Nodes (5): 0. Design stance, 1.1 ER diagram, 1. The hierarchy, 3. Cross-cutting decisions, Domain Model — NexusOps as a Multi-Tenant Platform

### Community 164 - "scope_matches"
Cohesion: 0.25
Nodes (7): Check an API-key scope list against a required permission. Supports exact match…, scope_matches(), parametrize, test_scope_matches_truth_table(), 1. Principles (already true in the codebase, kept), 5. API keys, 2.1 Identity & tenancy (new)

### Community 165 - "_FakeAsyncClient"
Cohesion: 0.22
Nodes (3): _FakeAsyncClient, _FakeRequestObj, Scripted httpx.AsyncClient: responses keyed by absolute request URL.

### Community 166 - "test_created_at_defaults.py"
Cohesion: 0.50
Nodes (3): created_at server defaults must evaluate per insert, not at table creation., Regression: system_events and audit_logs shipped with DEFAULT 'now()' (quoted…, test_audit_and_event_created_at_defaults_are_dynamic()

### Community 167 - "AuthContext"
Cohesion: 0.08
Nodes (31): _attach_organization(), AuthContext, get_current_user(), get_identity(), get_optional_user(), _load_permissions(), _org_id_from_header(), DbSessionDep (+23 more)

### Community 168 - "membership_for_org"
Cohesion: 0.67
Nodes (3): membership_for_org(), Membership, The user's active membership in *org_id*, if any. This single indexed read is…

### Community 170 - "_pace"
Cohesion: 0.67
Nodes (3): _pace(), Deterministic per-line delay between 0.05s and 0.35s., test_pace_bounds()

### Community 171 - "get_meta"
Cohesion: 0.40
Nodes (5): get_meta(), DbSessionDep, get, Public metadata; identity fields appear only for valid credentials., OptionalUser

### Community 175 - "4. DNS ownership verification"
Cohesion: 0.40
Nodes (5): 4.1 The token, 4.2 The check (control-plane side), 4.3 Anti-takeover rules, 4.4 Sequence: add-domain → verified, 4. DNS ownership verification

## Knowledge Gaps
- **409 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+404 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1744 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `6. Tooling: reproducible e2e` connect `logging.py` to `test_operation_registry.py`, `test_ws_hub.py`, `test_tenant_isolation.py`, `client.ts`, `_entity_exists`, `core/tenancy.py`, `alembic`?**
  _High betweenness centrality (0.247) - this node is a cross-community bridge._
- **Why does `useEventStream()` connect `client.ts` to `App.tsx`, `apiGet`, `useAuth`, `types.ts`, `ServerDetailPage.tsx`, `logging.py`, `DashboardPage.tsx`, `DeploymentDetailPage.tsx`?**
  _High betweenness centrality (0.247) - this node is a cross-community bridge._
- **Why does `TenancyScopeError` connect `core/tenancy.py` to `deps.py`, `AuthContext`, `test_operations.py`, `test_tenant_isolation.py`, `log_service.py`, `hub.py`, `logging.py`?**
  _High betweenness centrality (0.123) - this node is a cross-community bridge._
- **Are the 83 inferred relationships involving `AuthContext` (e.g. with `TenancyScopeError` and `MembershipStatus`) actually correct?**
  _`AuthContext` has 83 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `APIModel` (e.g. with `OperationSpec` and `test_specs_reject_unknown_params()`) actually correct?**
  _`APIModel` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `apiGet()` (e.g. with `ContainerDetailPage.test.tsx` and `mockApi()`) actually correct?**
  _`apiGet()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `meta`, `SCHEMA`, `RESEARCH_COMMON` to the rest of the system?**
  _409 weakly-connected nodes found - possible documentation gaps or missing edges._