# Graph Report - nexusops  (2026-10-09)

## Corpus Check
- 313 files · ~281,719 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: (none) 8, .example 1, .service 1)

## Summary
- 4525 nodes · 13299 edges · 191 communities (168 shown, 23 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1084 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `effa6b5f`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- AuthContext.tsx
- project_service.py
- App.tsx
- apiGet
- operation.py
- types.ts
- resolve_client_ip
- apiPost
- UsersPage.tsx
- list_servers
- test_operations.py
- ServerDetailPage.tsx
- APIModel
- client.ts
- projects.py
- incidents.py
- deployment_engine.py
- SimulatedDockerProvider
- run_async
- Secrets Architecture
- test_deployments_simulated.py
- containers.py
- metrics_service.py
- get_settings
- Domain Routing — NexusOps
- monitor_service.py
- Node & Agent Architecture
- test_agent_backoff.py
- SimulatedDeploymentRunner
- nexusops_agent.py
- get_sessionmaker
- auth_service.py
- docker_host_service.py
- rate_limit.py
- docker_hosts.py
- test_ws_hub.py
- monitors.py
- v1/search.py
- server_service.py
- v1/channels.py
- DockerProvider
- test_monitor_transport.py
- Deployment Architecture — NexusOps (target state)
- @tanstack/react-query
- RealDockerProvider
- test_permissions.py
- record
- maintenance.py
- test_ssrf.py
- NotFound
- roles.py
- test_schemas_server.py
- apikey.py
- test_migration_phase2.py
- v1/auth.py
- core/tenancy.py
- sweep_session
- alembic
- notification_service.py
- helpers.py
- compilerOptions
- v1/deployments.py
- test_error_logging.py
- organization.py
- test_phase2_environments.py
- seed.py
- test_schema_redaction.py
- Page
- encrypt_str
- package.json
- list_events
- test_secrets.py
- README.md - NexusOps overview
- models/__init__.py
- api service (FastAPI / uvicorn :8000)
- UnprocessableEntity
- monitor_transport.py
- test_monitors_incidents.py
- redact_mapping
- test_phase2_secrets.py
- sweep_deployments
- docker_real.py
- users.py
- tests/conftest.py
- test_agent_contract.py
- list_sessions
- devDependencies
- operation_service.py
- list_audit_logs
- test_migration_drift.py
- container.py
- validate_config
- require_server
- test_tenant_isolation.py
- test_phase21_secret_version_integrity.py
- list_alerts
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- fixtures.ts
- sanitize_error
- AppError
- scope_matches
- _database_url
- Platform Security Model — NexusOps
- EnvironmentUpdate
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- _validate_resolution
- channel.py
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- ScopedSession
- organization_service.py
- create_app
- get_redis
- scripts
- enums.py
- test_tenancy_allowlist.py
- _entity_exists
- dependencies
- DeploymentDetailPage.test.tsx
- generate_secrets.sh
- notification_sender.py
- server_payload
- list_operations
- middleware.py
- ._resolve
- resolve_secrets_for_environment
- AuditLogPage.tsx
- install.sh
- docker-entrypoint.sh
- integration/__init__.py
- Hub
- CLAUDE.md - project graphify rules
- Graphify query workflow (query / path / explain / update)
- frontend/index.html - SPA shell
- NexusOps Favicon — stylized letter 'N' lettermark in sky blue (#38bdf8) on a dark navy rounded square (#0b1120, 7px corner radius)
- nexusops-backend
- test_same_origin_compares_the_full_authority_including_port
- 20260922_1000-a3f1c8d24b6e_add_tenancy_foundation.py
- postgres service (PostgreSQL 17, loopback :5433)
- test_rbac.py
- nexusops-understand.mjs
- Invisible account lockout (5 fails -> 15 min, enumeration resistance)
- test_event_registry.py
- test_notifications.py
- nexusops-draft.mjs
- hash_token
- nexusops-challenge.mjs
- pytest
- test_schemas_agent.py
- test_run_async_publishes_frames_scheduled_by_the_commit_hook
- AgentClient
- register_exception_handlers
- lax
- 2. Entities
- journey.spec.ts
- _FakeAsyncClient
- dispatch_event_frame
- AuthContext
- AgentHelloIn
- .__tablename__
- require_permission
- get_meta
- ApplicationBase
- 6. Tooling: reproducible e2e
- get_latest_server_metrics
- ensure_dispatchable
- celery_app.py
- config.py
- ContainerInfo
- simulation.py
- websocket_endpoint
- 20261009_1000-c3d4e5f6a7b8_enforce_secret_version_integrity.py
- ApplicationCreate
- ApplicationUpdate
- 20261008_1200-b2c3d4e5f6a7_add_projects_and_environments.py
- 20261009_1100-d4e5f6a7b8c9_correct_legacy_environment_types.py
- permissions.py
- permissions_for_role
- instant_pacing
- configure_logging
- .logs

## God Nodes (most connected - your core abstractions)
1. `AuthContext` - 136 edges
2. `APIModel` - 118 edges
3. `apiGet()` - 82 edges
4. `get_settings()` - 74 edges
5. `NotFound` - 67 edges
6. `record()` - 65 edges
7. `publish()` - 61 edges
8. `apiPost()` - 60 edges
9. `useToast()` - 58 edges
10. `ApiError` - 57 edges

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

## Communities (191 total, 23 thin omitted)

### Community 0 - "AuthContext.tsx"
Cohesion: 0.04
Nodes (47): getActiveOrgId(), setAccessToken(), setActiveOrgId(), Membership, SearchResult, User, LoginRoute(), RequireAuth() (+39 more)

### Community 1 - "project_service.py"
Cohesion: 0.15
Nodes (42): Application, Project, _apply_update(), _check_server(), create_application(), create_environment(), create_project(), delete_application() (+34 more)

### Community 2 - "App.tsx"
Cohesion: 0.04
Nodes (95): DashboardSummary, DeploymentOut, DeploymentStepOut, Page, ProjectOut, AlertsPage, ApiKeysPage, App() (+87 more)

### Community 3 - "apiGet"
Cohesion: 0.09
Nodes (36): apiGet(), IncidentEventOut, MonitorDetailPage, formatDateTime(), formatDurationMs(), formatRelative(), truncate(), AlertsPage() (+28 more)

### Community 4 - "operation.py"
Cohesion: 0.08
Nodes (31): OperationType, The whitelist. Nothing outside this enum ships as an exec surface. Each type…, AgentOperationClaimOut, AgentOperationResultOut, ContainerActionParams, LogsTailParams, OperationCreate, OperationOut (+23 more)

### Community 5 - "types.ts"
Cohesion: 0.04
Nodes (43): AlertOut, ApiKeyOut, ChannelOut, ContainerOut, DeliveryOut, DeploymentLogLine, DeploymentStatus, DockerHostOut (+35 more)

### Community 6 - "resolve_client_ip"
Cohesion: 0.17
Nodes (22): _is_trusted(), _parse_networks(), Request, Client-IP resolution behind chained reverse proxies. The API never takes TCP…, Parse a comma-separated CIDR list; malformed entries are skipped., Real client address for *request* per the trust model above., resolve_client_ip(), make_request() (+14 more)

### Community 7 - "apiPost"
Cohesion: 0.06
Nodes (55): apiDelete(), apiPatch(), apiPost(), ApplicationOut, ENVIRONMENT_TYPE_LABELS, EnvironmentDetailOut, EnvironmentOut, EnvironmentType (+47 more)

### Community 8 - "UsersPage.tsx"
Cohesion: 0.07
Nodes (30): LoginPage, OrganizationRequiredPage, UsersPage, CheckboxField(), CheckboxFieldProps, FieldAria, FieldBaseProps, PasswordField() (+22 more)

### Community 9 - "list_servers"
Cohesion: 0.10
Nodes (30): create_server(), delete_server(), _detail(), get_server(), list_servers(), list_tags(), AsyncSession, DbDep (+22 more)

### Community 10 - "test_operations.py"
Cohesion: 0.08
Nodes (48): assert_error_code(), Assert envelope shape + code; returns the inner error object., _dispatch(), _dispatch_body(), _enrolled_node(), _mutate_in_system_scope(), MonkeyPatch, Node operations: the compare-and-set state machine and its tenant boundary.… (+40 more)

### Community 11 - "ServerDetailPage.tsx"
Cohesion: 0.09
Nodes (36): MetricPoint, ServerDetailPage, ServerListPage, ChartSeries, LineChart(), LineChartProps, PAD, buildServerPayload() (+28 more)

### Community 12 - "APIModel"
Cohesion: 0.05
Nodes (68): AlertOut, Schemas for operator-facing alerts., ApplicationSummary, Application API schemas., Application as embedded in project outputs (no deployment summary)., AuditOut, Schemas for the read-only audit log API. The audit table is append-only; these…, One audit trail entry (no write routes ever exist for this resource).… (+60 more)

### Community 13 - "client.ts"
Cohesion: 0.05
Nodes (46): API_BASE, ApiError, apiRequest(), buildUrl(), extractError(), getAccessToken(), onActiveOrgChange(), ORGANIZATION_HEADER (+38 more)

### Community 14 - "projects.py"
Cohesion: 0.14
Nodes (42): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+34 more)

### Community 15 - "incidents.py"
Cohesion: 0.07
Nodes (56): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+48 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.11
Nodes (56): deployment_log_channel(), Deployment, DeploymentEnvironment, DeploymentStep, A **project-scoped** deployment environment (Phase 2 promotion). The…, DeploymentStatus, StepStatus, _after_commit_enqueue() (+48 more)

### Community 17 - "SimulatedDockerProvider"
Cohesion: 0.13
Nodes (25): Implements :class:`DockerProvider` semantics against DB rows., Make a container row visible to this provider instance., Attach already-fetched log rows so ``logs()`` can replay them., SimulatedDockerProvider, _log_entry(), datetime, Unit tests for the simulated docker provider (in-memory rows, no docker)., _row() (+17 more)

### Community 18 - "run_async"
Cohesion: 0.18
Nodes (16): flush_pending_publishes(), Wait for frames scheduled by ``after_commit`` hooks to reach Redis. The commit…, T, Run *coroutine* on a dedicated event loop (Celery workers are sync). The loop…, run_async(), _drained(), The drain must not become a delay on the hot path for quiet tasks., test_flush_is_a_noop_when_nothing_is_pending() (+8 more)

### Community 19 - "Secrets Architecture"
Cohesion: 0.07
Nodes (44): create_secret(), delete_secret(), get_secret(), list_secret_versions(), list_secrets(), DbSession, delete, get (+36 more)

### Community 20 - "test_deployments_simulated.py"
Cohesion: 0.15
Nodes (28): execute_deployment(), Run one deployment to a terminal state. Never raises; safe to re-run., get_environment(), _as_worker(), _delivery_chain(), _owner_ctx(), _queue(), _queued_with_recorder() (+20 more)

### Community 21 - "containers.py"
Cohesion: 0.05
Nodes (77): _action_route(), _endpoint(), _container_out(), _decode_frame(), _ev(), get_container(), _like_pattern(), list_container_logs() (+69 more)

### Community 22 - "metrics_service.py"
Cohesion: 0.19
Nodes (14): ensure_server(), _extra_object(), granularity_for_range(), Any, UUID, Metrics pipeline: timeseries queries, rollup aggregation, retention, dashboard., Return ``{range, granularity, points}`` for one server. A single grouped query…, JSONB object mapping every metric to its min/max aggregate. (+6 more)

### Community 23 - "get_settings"
Cohesion: 0.09
Nodes (43): argon2, argon2_exceptions, get_settings(), Return the cached settings singleton., get_engine(), AsyncEngine, Runtime DSN (application role, RLS enforced) for Celery/script sync paths., sync_database_url() (+35 more)

### Community 24 - "Domain Routing — NexusOps"
Cohesion: 0.07
Nodes (29): 10. Wildcards and catch-all, 11. User journey, 12. API surface, permissions, audit, 13. Monitoring tie-in, 1. Scope and current state, 2. Where nginx runs, 3.1 Domain, 3.2 Route (+21 more)

### Community 25 - "monitor_service.py"
Cohesion: 0.15
Nodes (38): MonitorStatus, Monitor, MonitorCheck, get_transport(), Pick the transport matching the monitor URL scheme., _active_incident(), _audit(), claim_due_monitors() (+30 more)

### Community 26 - "Node & Agent Architecture"
Cohesion: 0.07
Nodes (28): 1. Scope and stance, 2.1 Current shape (real), 2.2 Changes for the target model, 2.3 Capabilities (target), 2. The Node concept, 3.1 Current state (real), 3.2 Enrollment v2, 3.3 Token storage & rotation with dual-token grace (+20 more)

### Community 27 - "test_agent_backoff.py"
Cohesion: 0.14
Nodes (22): agent_fixture(), _install_sleep(), fake_sleep(), _load_agent(), _patch_host(), Any, fixture, MonkeyPatch (+14 more)

### Community 28 - "SimulatedDeploymentRunner"
Cohesion: 0.11
Nodes (40): LogLevel, _commit_short(), _pace(), Exception, Deployment runner port plus a faithful simulated implementation.…, Stream output lines for *step_name*; raise StepFailure to fail it., Staged docker-style simulation used by v1 deployments., Deterministic per-line delay between 0.05s and 0.35s. (+32 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.10
Nodes (29): build_heartbeat(), collect_container_stats(), collect_containers(), cpu_percent_since(), disk_stats(), _docker_request(), _interruptible_sleep(), load1() (+21 more)

### Community 30 - "get_sessionmaker"
Cohesion: 0.08
Nodes (36): get_sessionmaker(), async_sessionmaker, AsyncSession, close_redis(), lifespan(), Start the WS hub + notification dispatcher; tear them down cleanly., _admin_dsn(), _clean_slate() (+28 more)

### Community 31 - "auth_service.py"
Cohesion: 0.10
Nodes (49): active_memberships(), The user's memberships in non-suspended organizations, oldest first. Reads only…, System scope bound to *db*, for rows that have no organization. Used by exactly…, system_write_scope(), ActorType, AuditResult, OrganizationStatus, _audit() (+41 more)

### Community 32 - "docker_host_service.py"
Cohesion: 0.06
Nodes (85): asyncio, BadRequest, ContainerStatus, DockerHostStatus, Container, DockerHost, Observed container state mirrored from an agent or docker provider., LogEntry (+77 more)

### Community 33 - "rate_limit.py"
Cohesion: 0.15
Nodes (21): RateLimited, client_ip(), _memory_count_and_ttl(), Request, rate_limit(), _dependency(), Redis-backed fixed-window rate limiting as a FastAPI dependency factory. Auth-…, Best-effort client IP; honours X-Forwarded-For from trusted proxies. Delegates… (+13 more)

### Community 34 - "docker_hosts.py"
Cohesion: 0.07
Nodes (55): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+47 more)

### Community 35 - "test_ws_hub.py"
Cohesion: 0.14
Nodes (25): _connection(), _drain(), _event_frame(), _fake_sessionmaker(), _FakeSession, hub(), _Org, Any (+17 more)

### Community 36 - "monitors.py"
Cohesion: 0.11
Nodes (44): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+36 more)

### Community 37 - "v1/search.py"
Cohesion: 0.05
Nodes (50): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+42 more)

### Community 38 - "server_service.py"
Cohesion: 0.07
Nodes (63): server_metrics_channel(), ContainerHealth, MetricGranularity, String enum; member names equal values so name/value storage never disagrees., ServerStatus, StrEnum, Server, AgentContainerIn (+55 more)

### Community 39 - "v1/channels.py"
Cohesion: 0.13
Nodes (30): create_channel(), delete_channel(), get_channel(), list_channels(), list_deliveries(), DbDep, delete, Depends (+22 more)

### Community 40 - "DockerProvider"
Cohesion: 0.10
Nodes (10): DockerProvider, Any, datetime, Protocol, List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``., List volumes: keys ``name``, ``driver``, ``mountpoint``., List networks: keys ``name``, ``driver``, ``scope``., Yield parsed log lines. With ``follow=True`` the stream never ends. (+2 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.13
Nodes (34): CheckResult, HTTPMonitorTransport, Deterministic fake checker for ``sim://`` monitors and demo environments.…, Real HTTP(S) probe using httpx with per-monitor settings. Redirects are…, SimulatedTransport, _check(), clock(), FakeClock (+26 more)

### Community 42 - "Deployment Architecture — NexusOps (target state)"
Cohesion: 0.09
Nodes (22): DeploymentRunner, Protocol, Adapter interface implemented by real (future) and simulated runners., Return the ordered step names for this run., 10. Events and WS during runs, 11. Post-deploy hooks, 12. Rollback semantics (existing behavior kept), 13. The simulated runner stays — labeled (+14 more)

### Community 43 - "@tanstack/react-query"
Cohesion: 0.03
Nodes (80): CheckOut, IncidentOut, MonitorOut, Role, MetaInfo, SimulatedChip(), mocks, Toast (+72 more)

### Community 44 - "RealDockerProvider"
Cohesion: 0.17
Nodes (5): T, Execute an SDK call with one short retry, normalizing failures., Two short samples give real cpu/net deltas without streaming., Talks to a real docker daemon over ``unix://`` or ``tcp://``., RealDockerProvider

### Community 45 - "test_permissions.py"
Cohesion: 0.16
Nodes (11): permission_exists(), _auth_context(), Unit tests for the permission registry, scope matching and RBAC gate., A fake context in the given organization. ``membership_status=None`` models a…, test_api_key_scope_intersects_role_permissions(), test_membership_is_required_for_authority(), test_permission_exists_helper(), test_plain_user_without_permissions_is_denied() (+3 more)

### Community 46 - "record"
Cohesion: 0.07
Nodes (65): Conflict, EventLevel, IncidentEventKind, Incident, IncidentEvent, SystemEvent, create_api_key(), Request (+57 more)

### Community 47 - "maintenance.py"
Cohesion: 0.13
Nodes (22): aggregate_metrics(), _run(), _collect_logs(), expire_operations(), _run(), expire_sessions(), _run(), task (+14 more)

### Community 48 - "test_ssrf.py"
Cohesion: 0.14
Nodes (21): assert_safe_tcp_endpoint(), is_simulation_url(), ValueError, SSRF guard applied to every operator-supplied outbound URL. Monitors and…, Validate a ``tcp://`` docker host endpoint for outbound connection. Docker…, True when *url* targets the built-in simulated checker (``sim://``)., Internal signal: a specific SSRF rule matched (never shown to clients)., UrlRejected (+13 more)

### Community 49 - "NotFound"
Cohesion: 0.14
Nodes (36): NotFound, An encrypted configuration value, scoped to org, project or environment.…, Secret, _actor_type(), create_secret(), delete_secret(), _detail(), get_secret() (+28 more)

### Community 50 - "roles.py"
Cohesion: 0.11
Nodes (29): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, delete, get (+21 more)

### Community 51 - "test_schemas_server.py"
Cohesion: 0.21
Nodes (22): Payload for registering a server., Partial update. ``tags`` replaces the full set when provided., ServerCreate, ServerUpdate, _base(), parametrize, Unit tests for app.schemas.server (validation only, no I/O)., test_empty_ip_is_allowed_but_whitespace_collapses() (+14 more)

### Community 52 - "apikey.py"
Cohesion: 0.14
Nodes (19): create_api_key(), list_api_keys(), CurrentUser, DbSessionDep, delete, get, post, Request (+11 more)

### Community 53 - "test_migration_phase2.py"
Cohesion: 0.11
Nodes (32): alembic_config, alembic_script, Phase 2.1 corrective migration: legacy ``environment_type`` classification.…, Every case is classified as documented, ids and ownership intact., An explicit non-DEV classification survives the corrective migration. The…, The correction is part of ``head`` and adds no extra Alembic head., Insert one legacy environment per case, in two organizations., _seed_typed_environments() (+24 more)

### Community 54 - "v1/auth.py"
Cohesion: 0.09
Nodes (46): change_password(), _clear_refresh_cookie(), _cookies_secure(), login(), logout(), me(), _optional_actor(), AsyncSession (+38 more)

### Community 55 - "core/tenancy.py"
Cohesion: 0.06
Nodes (65): get_logger(), _apply_scope_guc(), apply_scope_to_session(), current_org(), current_scope(), _desired_guc(), _guard(), _has_org_predicate() (+57 more)

### Community 56 - "sweep_session"
Cohesion: 0.18
Nodes (19): task, Monitor dispatch: claim due monitors atomically, run their checks., Claim up to CLAIM_BATCH due monitors and execute each check.…, run_due_monitors(), _run(), org_for(), org_session(), Any (+11 more)

### Community 57 - "alembic"
Cohesion: 0.06
Nodes (10): alembic, downgrade(), rename ``server.*`` permission codenames to ``node.*`` The Node/Server…, _rename_permissions(), upgrade(), _quoted_list(), Add the operations framework table (node-agent-architecture.md §5). One tenant-…, upgrade() (+2 more)

### Community 58 - "notification_service.py"
Cohesion: 0.17
Nodes (29): NotificationChannel, A delivery target (email address / webhook endpoint). ``config_ciphertext``…, _attempt_delivery(), _audit(), create_channel(), decode_delivery_cursor(), decrypt_channel_config(), delete_channel() (+21 more)

### Community 59 - "helpers.py"
Cohesion: 0.08
Nodes (43): bearer(), cookie_attributes(), error_of(), login_account(), login_headers(), Any, AsyncClient, Response (+35 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "v1/deployments.py"
Cohesion: 0.07
Nodes (55): _attribute_step_idx(), cancel_deployment(), _emails_for(), get_deployment(), list_application_deployments(), list_deployment_logs(), _list_deployments(), _parse_sort() (+47 more)

### Community 62 - "test_error_logging.py"
Cohesion: 0.22
Nodes (4): Regression: the catch-all 500 handler must not log raw exception text.…, _SpyLogger, test_unhandled_exception_handler_logs_class_not_message(), fastapi_testclient

### Community 63 - "organization.py"
Cohesion: 0.11
Nodes (24): create_organization(), list_my_organizations(), CurrentUser, DbSessionDep, get, IdentityUser, patch, post (+16 more)

### Community 64 - "test_phase2_environments.py"
Cohesion: 0.18
Nodes (22): _environment(), _project(), parametrize, Phase 2: project-scoped environments, config layering, and their isolation. The…, Uniqueness is ``(project_id, slug)`` — not instance-wide., The update path is validated too (the pre-Phase-2 gap)., Knowing an environment UUID is not access: the project link must hold., Another tenant cannot reach the project, its environments, or its detail. (+14 more)

### Community 65 - "seed.py"
Cohesion: 0.18
Nodes (20): EnvironmentType, Kind of a project-scoped deployment environment (Phase 2). Descriptive only —…, _lock(), _organization_name(), _organization_slug(), datetime, User, Idempotent demo seed: roles, admin user, simulated fleet, monitors, history.… (+12 more)

### Community 66 - "test_schema_redaction.py"
Cohesion: 0.14
Nodes (18): is_sensitive_header(), mask_sensitive_headers(), field_serializer, True when *name* looks like it carries a credential (Authorization etc.)., Return a copy of *headers* with sensitive values replaced by a mask., mask_target(), Human-readable masked target safe to expose over the API. For webhook families…, _monitor_out() (+10 more)

### Community 67 - "Page"
Cohesion: 0.13
Nodes (22): Cursor, CursorPage, decode_cursor(), encode_cursor(), Page, BaseModel, datetime, _constraint() (+14 more)

### Community 68 - "encrypt_str"
Cohesion: 0.09
Nodes (29): decrypt_str(), digest_of(), encrypt_str(), _fernet(), Short server-verifiable digest used for change detection display. HMAC-SHA256…, parametrize, test_decrypt_with_wrong_ciphertext_raises_value_error(), test_digest_length_and_determinism() (+21 more)

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
Cohesion: 0.09
Nodes (40): docker-compose.dev.yml - dev overlay, docker-compose.docker-sock.yml - docker socket override, docker-compose.yml - full stack definition, docs/agent.md - agent guide, docs/api.md - API guide, Append-only audit log (Postgres BEFORE UPDATE OR DELETE trigger), docs/architecture.md - system architecture, docs/deployment.md - deployment and operations guide (+32 more)

### Community 73 - "models/__init__.py"
Cohesion: 0.06
Nodes (79): Alembic environment: metadata comes from app.models, URL from app settings., Owner-role DSN for Alembic and the container entrypoint. Migrations…, sync_migration_url(), _org_scoped_classes(), Mapped classes marked :class:`~app.models.base.OrgScoped`. Reads the mapper…, ``before_flush`` handler: own new rows, and refuse rows that change hands.…, _stamp_org_on_flush(), Base (+71 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "UnprocessableEntity"
Cohesion: 0.17
Nodes (23): UnprocessableEntity, assert_safe_url(), _raise_block(), Validate *url* for outbound requests; return the parsed URL or raise 422.…, Reject non-empty values that are not valid IPv4/IPv6 addresses., _validate_ip(), install_dns(), Exception (+15 more)

### Community 76 - "monitor_transport.py"
Cohesion: 0.10
Nodes (21): CheckOutcome, coerce_headers(), _decode(), MonitorTransport, Any, BaseException, Protocol, Pluggable monitor check transports (real HTTP + deterministic simulator). A… (+13 more)

### Community 77 - "test_monitors_incidents.py"
Cohesion: 0.27
Nodes (9): _create_monitor(), Monitor checks driving the full down -> incident -> recovery lifecycle., Regression: probe headers and URL query credentials never leave the API. Probe…, A monitor's checks, incidents and timeline all live in its organization, so the…, test_check_now_endpoint_runs_immediately(), test_down_then_recover_lifecycle(), test_metadata_endpoint_and_private_target_blocked(), test_monitor_responses_mask_probe_credentials() (+1 more)

### Community 78 - "redact_mapping"
Cohesion: 0.22
Nodes (13): _is_sensitive_key(), Substring match on a normalised key so header-style names are caught too.…, Return a copy of *data* with sensitive values replaced. Used by audit metadata…, redact_mapping(), parametrize, Unit tests for app.core.logging redaction (pure functions only)., test_case_insensitive_substring_match(), test_flat_sensitive_keys_redacted() (+5 more)

### Community 79 - "test_phase2_secrets.py"
Cohesion: 0.19
Nodes (21): _env(), _project(), Phase 2 secrets: layered scope, immutable versions, rollback, isolation. Two…, Two racing rotations must both be kept and never share a version number., Another tenant cannot read, rotate, roll back or even enumerate the secret., The documented example: same key at three scopes; most specific wins., A ref declared in the project base config resolves for its environments., _resolved() (+13 more)

### Community 80 - "sweep_deployments"
Cohesion: 0.29
Nodes (7): task, Execute one queued deployment. The engine owns all state transitions., Re-enqueue deployments the broker lost; fail ones whose worker died.…, run_deployment(), _run(), sweep_deployments(), _run()

### Community 81 - "docker_real.py"
Cohesion: 0.17
Nodes (18): ContainerStats, Point-in-time resource usage snapshot., _as_float(), _compute_stats(), _cpu_percent(), _network_bytes(), parse_rfc3339(), Any (+10 more)

### Community 82 - "users.py"
Cohesion: 0.12
Nodes (28): create_user(), deactivate_user(), get_user(), list_users(), CurrentUser, DbSessionDep, delete, get (+20 more)

### Community 83 - "tests/conftest.py"
Cohesion: 0.22
Nodes (7): configure_test_env(), Test bootstrap: pin every cached setting BEFORE the first ``app`` import. The…, KEY=VALUE pairs from the repo .env (first definition wins); never logged., Export the exact settings the app caches; host values cannot leak through., _read_dot_env(), os, sys

### Community 84 - "test_agent_contract.py"
Cohesion: 0.20
Nodes (15): agent_fixture(), _load_agent(), _patch_stats(), Any, fixture, MonkeyPatch, Contract tests: the shipped agent's payloads must satisfy the ingest schemas.…, One-shot docker stats reduce to cpu/mem/limit fields the schema accepts, with… (+7 more)

### Community 85 - "list_sessions"
Cohesion: 0.20
Nodes (11): list_sessions(), CurrentUser, DbSessionDep, delete, get, Request, UUID, Active sessions of this organization's members. Defaults to the caller's own;… (+3 more)

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "operation_service.py"
Cohesion: 0.16
Nodes (30): OperationStatus, Lifecycle of one node operation (node-agent-architecture.md §5.1).…, Operation, One whitelisted action for one node, with a CAS lifecycle. ``attempts`` is…, _active_org(), cancel_operation(), claim_operation(), create_operation() (+22 more)

### Community 88 - "list_audit_logs"
Cohesion: 0.29
Nodes (7): list_audit_logs(), datetime, DbSession, Depends, get, PageParamsDep, Newest-first audit trail with optional filters. No write routes exist for this…

### Community 89 - "test_migration_drift.py"
Cohesion: 0.25
Nodes (7): alembic_autogenerate, alembic_migration, Model / migration drift: the schema in the database must match the models.…, ``Base.metadata`` and the migrated database must describe the same schema., The DB whitelist and ``OperationType`` are the same closed set. The migration…, test_models_and_migrations_do_not_drift(), test_operations_type_check_matches_the_enum()

### Community 90 - "container.py"
Cohesion: 0.21
Nodes (12): ContainerRemoveOut, host_ref(), HostRef, LogEntryOut, UUID, Container schemas: list/detail read models, log entries, action results., Summary of the docker host a container runs on., Summary of the server associated with a container. (+4 more)

### Community 91 - "validate_config"
Cohesion: 0.08
Nodes (31): field_validator, collect_secret_refs(), walk(), ConfigValidationError, effective_config(), merge_config(), Any, ValueError (+23 more)

### Community 92 - "require_server"
Cohesion: 0.16
Nodes (19): agent_heartbeat(), agent_hello(), claim_operation(), _presented_token(), DbDep, post, Request, Response (+11 more)

### Community 93 - "test_tenant_isolation.py"
Cohesion: 0.05
Nodes (51): dispose_engine(), Raised when a unit of work touches tenant data with no valid org scope. This is…, Run the enclosed block with tenant filtering off (maintenance only). ``reason``…, system_scope(), TenancyScopeError, _app_role_dsn(), _invite(), Cross-tenant isolation: the Phase 1 exit gate. Every test here answers one of… (+43 more)

### Community 94 - "test_phase21_secret_version_integrity.py"
Cohesion: 0.18
Nodes (18): _app_role_dsn(), _owner_dsn(), _probe(), Phase 2.1 — ``secret_versions`` is append-only in the **database**, not just in…, Immutability is a database guarantee, not merely a missing code path. The owner…, The legitimate append paths keep working under the guard., The documented deletion policy: purging a Secret cascades its history., RLS is preserved: another tenant cannot see a version row, even by id. (+10 more)

### Community 95 - "list_alerts"
Cohesion: 0.13
Nodes (22): list_alerts(), mark_all_read(), mark_read(), CurrentUser, DbDep, Depends, get, post (+14 more)

### Community 96 - "NexusOps (self-hosted infrastructure management and monitoring platform)"
Cohesion: 0.20
Nodes (10): mailpit service (dev SMTP sink + web UI :8025), NexusOps compose stack (8 services on one network), HIGH finding: redirect-following SSRF in uptime monitors (fixed: follow_redirects=False + per-hop guard), SSRF guard (assert_safe_url, per-redirect-hop validation, assert_safe_tcp_endpoint), Mailpit SMTP port internal-only (host-side injection needs extra mapping), Host port knobs (NEXUSOPS_HTTP_PORT/POSTGRES/REDIS/MAILPIT/VITE), SPA entry point (loads /src/main.tsx, dark color-scheme), Uptime monitors -> incidents -> notifications flow (+2 more)

### Community 97 - "REST API surface (/api/v1)"
Cohesion: 0.29
Nodes (7): Cursor (keyset) and offset pagination envelopes, Permission model (data-driven registry, require_permission, wildcard scopes), REST API surface (/api/v1), RBAC registry (PERMISSIONS + ROLE_MATRIX + scope_matches), Adding a new resource: 7-step checklist (model -> migration -> schemas -> service -> router -> tests -> frontend), Alembic migration workflow (autogenerate, models __init__ export, entrypoint apply), Command palette (Ctrl/Cmd+K)

### Community 98 - "fixtures.ts"
Cohesion: 0.23
Nodes (11): EDGE, MAILPIT, ADMIN, Bootstrap, bootstrapVia(), test, ADMIN, openProject() (+3 more)

### Community 99 - "sanitize_error"
Cohesion: 0.29
Nodes (6): Exception, Build a compact, secret-free description of a provider failure. Only the…, sanitize_error(), parse_log_line(), Split one raw log record into a :class:`LogLine`., _iterate()

### Community 100 - "AppError"
Cohesion: 0.20
Nodes (16): AppError, Exception, Base class for expected, client-facing errors., _authenticate_api_key(), _authenticate_jwt(), _bind_organization(), _load_permissions(), _org_id_from_frame() (+8 more)

### Community 101 - "scope_matches"
Cohesion: 0.12
Nodes (17): Check an API-key scope list against a required permission. Supports exact match…, scope_matches(), parametrize, test_scope_matches_truth_table(), 0. What shipped (Phase 1), 1. Principles (already true in the codebase, kept), 2. Registry changes (Phase 1 + new subsystems), 3. The five system roles (target) (+9 more)

### Community 102 - "_database_url"
Cohesion: 0.33
Nodes (6): _database_url(), Migrations run as the table **owner**, never as the application role. The owner…, Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online()

### Community 103 - "Platform Security Model — NexusOps"
Cohesion: 0.11
Nodes (19): make(), 10.1 Node revocation playbook (compromised node / leaked agent token), 10.2 Key compromise playbook, 10. Incident response, 1.1 Real vs simulated today (do not mistake one for the other), 1. Scope, stance, and simulation honesty, 2. Assets, 3. Trust boundaries (+11 more)

### Community 104 - "EnvironmentUpdate"
Cohesion: 0.15
Nodes (13): EnvironmentBase, EnvironmentCreate, EnvironmentUpdate, _normalise_environment_type(), field_validator, Shared environment fields., Payload to create an environment under a project., Partial environment update; omitted fields are left untouched. Config is… (+5 more)

### Community 105 - "redis service (Redis 7, no persistence, loopback :6390)"
Cohesion: 0.22
Nodes (11): redis service (Redis 7, no persistence, loopback :6390), WebSocket API (/api/v1/ws handshake, frames, limits), WebSocket channels (global, server-metrics, container-logs, deployment-logs, incidents), Deployment engine (queue_deployment / execute_deployment / sweeper backstop), Real-time spine: PostgreSQL system_events + Redis pub/sub, Rollback as a new deployment (rollback_of_id), WebSocket hub (framework-thin, Redis fan-in, per-socket queues), Test suites (pytest unit+integration, vitest, Playwright e2e) (+3 more)

### Community 106 - "NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)"
Cohesion: 0.18
Nodes (12): Agent security model (one-way telemetry, no command channel), Agent enrollment token (X-Agent-Token, nxa_..., SHA-256 at rest), Agent heartbeat exponential backoff (cap 5 min, exit 1 on revoked token), agent/install.sh (enrollment installer), Agent metrics collection (/proc statvfs Docker socket), NexusOps agent (stdlib-only Python, agent/nexusops_agent.py), Agent systemd hardening (ProtectSystem=strict, NoNewPrivileges), Agent ingest API (POST /agent/hello, POST /agent/heartbeat) (+4 more)

### Community 107 - "_validate_resolution"
Cohesion: 0.24
Nodes (9): _is_forbidden_address(), True when *addr* points into a network the server must never contact.…, Resolve *hostname* (AF_UNSPEC) and refuse any non-public answer., _validate_resolution(), test_private_and_special_addresses_are_forbidden(), test_public_addresses_are_allowed(), test_validate_resolution_passes_hostname_through(), IPv4Address (+1 more)

### Community 108 - "channel.py"
Cohesion: 0.19
Nodes (13): ChannelType, ChannelBase, ChannelCreate, ChannelOut, ChannelUpdate, EmailConfig, model_validator, Schemas for notification channels and delivery records. Channel configuration… (+5 more)

### Community 109 - "Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)"
Cohesion: 0.25
Nodes (9): API keys (X-API-Key, nxo_..., scope intersection), First boot sequence (api entrypoint migrates, compose never seeds), Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test), Makefile workflows (up/test/lint/typecheck/migrate/seed), HIGH finding: API-key scope bypass for superadmin-owned keys (fixed: scope intersection first), Security audit 2026-09 (26 raw findings -> 20 confirmed, all fixed), HIGH finding: known seed superadmin + API key backdoor (fixed: NEXUSOPS_ALLOW_SEED opt-in, one-time password), Threat model (edge attacker, malicious agent, curious operator, leaked token, SSRF) (+1 more)

### Community 111 - "organization_service.py"
Cohesion: 0.15
Nodes (26): add_member(), create_organization(), get_organization(), membership_for_user(), AsyncSession, Membership, Organization, Request (+18 more)

### Community 112 - "create_app"
Cohesion: 0.25
Nodes (12): create_app(), _include_routers(), FastAPI, Mount every domain router. Router variables follow the module contract., _app_for_environment(), MonkeyPatch, ENVIRONMENT gating contract: docs exposure and HSTS (see .env.example).…, create_app() with get_settings() patched to the given environment. (+4 more)

### Community 113 - "get_redis"
Cohesion: 0.12
Nodes (24): liveness(), get, Response, Health probes: liveness (always cheap) and readiness (checks dependencies).…, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness(), get_redis() (+16 more)

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "enums.py"
Cohesion: 0.05
Nodes (95): _load_organization(), Organization, FastAPI dependencies: database session, authenticated tenant context, RBAC…, Agent ingest endpoints: enrollment handshake and periodic heartbeats.…, Alert inbox endpoints. Authenticated users see the shared operator feed., API key routes — self-service management of the caller's own machine…, Audit log API. Strictly read-only: the table is append-only by design., System events API: cursor-paginated feed + canonical type catalogue. (+87 more)

### Community 116 - "test_tenancy_allowlist.py"
Cohesion: 0.20
Nodes (14): AST, _actual_callers(), _calls_system_scope(), _module_path(), The system-scope allowlist is the only fence around the tenancy carve-out.…, Every module that could open a system scope: ``app/`` plus the scripts., No module may lift tenant isolation without being named in the list., Every listed module must still be a real caller, so the list stays short. (+6 more)

### Community 117 - "_entity_exists"
Cohesion: 0.40
Nodes (6): _entity_exists(), Whether *id_* exists **for this organization**. Runs inside the socket's…, The hub's subscribe-time existence check under concurrent orgs.…, test_websocket_entity_checks_stay_inside_their_socket_org(), check(), 5. WebSockets

### Community 118 - "dependencies"
Cohesion: 0.33
Nodes (6): dependencies, lucide-react, react, react-dom, react-router-dom, @tanstack/react-query

### Community 119 - "DeploymentDetailPage.test.tsx"
Cohesion: 0.13
Nodes (9): ACTIVE_MEMBERSHIP, ApiError, deploymentDetail(), EMPTY_LOGS, FakeWebSocket, get, ME, post (+1 more)

### Community 120 - "generate_secrets.sh"
Cohesion: 0.47
Nodes (3): existing_real_keys(), replace_or_append(), generate_secrets.sh script

### Community 121 - "notification_sender.py"
Cohesion: 0.16
Nodes (17): NotificationError, Any, BaseException, Exception, Low-level notification transports: SMTP email and outgoing webhooks. These…, POST *payload* as JSON to *url*; 2xx is success, anything else raises. Response…, Raised when a delivery attempt fails. Message is safe to persist., Bounded, single-line, content-free error reason. (+9 more)

### Community 122 - "server_payload"
Cohesion: 0.11
Nodes (24): A valid POST /servers body with per-test overrides., server_payload(), _create_server(), Server CRUD, cascade delete, audit trail rows and audit immutability., The HTTP listing path — schema serialization is exercised end-to-end. A…, ``/servers`` is a temporary alias for pre-rename clients. It must keep working…, test_agent_token_rotation_invalidates_previous(), test_audit_log_api_serializes_and_filters() (+16 more)

### Community 123 - "list_operations"
Cohesion: 0.21
Nodes (15): cancel_operation(), create_operation(), get_operation(), list_operations(), DbDep, Depends, get, post (+7 more)

### Community 124 - "middleware.py"
Cohesion: 0.14
Nodes (15): ASGIApp, AccessLogMiddleware, Request, Response, HTTP middleware: request ids, security headers, structured access logs., Baseline hardening headers on every API response., RequestIDMiddleware, SecurityHeadersMiddleware (+7 more)

### Community 125 - "._resolve"
Cohesion: 0.15
Nodes (4): Any, Plausible numbers derived from the row plus time-based sine noise., _seed_int(), test_seed_int_is_deterministic_and_spread()

### Community 126 - "resolve_secrets_for_environment"
Cohesion: 0.17
Nodes (14): Exception, A ``${secret:KEY}`` reference could not be resolved. Fail-closed. Carries…, One successfully resolved reference: metadata for audit, no value., Outcome of resolving an environment's config references., Resolve every ``${secret:KEY}`` reference an environment's config names.…, resolve_secrets_for_environment(), ResolvedSecrets, SecretReference (+6 more)

### Community 127 - "AuditLogPage.tsx"
Cohesion: 0.19
Nodes (8): AuditEntry, AuditLogPage, AuditLogPage(), AuditRow, formatTimestamp(), RESULTS, shortId(), mockedGet

### Community 137 - "Hub"
Cohesion: 0.13
Nodes (18): _close_socket(), Connection, _frame_org(), Hub, _params_key(), _parse_payload(), Any, WebSocket (+10 more)

### Community 147 - "20260922_1000-a3f1c8d24b6e_add_tenancy_foundation.py"
Cohesion: 0.20
Nodes (12): _app_role_credentials(), _assert_fully_backfilled(), _backfill_org_ids(), _drop_constraint(), add tenancy foundation Phase 1 of the platform roadmap: organizations,…, Carry a value into a PL/pgSQL block. ``CREATE ROLE``/``ALTER ROLE`` are utility…, Application role name/password from settings (never hard-coded)., Point every pre-existing row at the bootstrap organization. ``audit_logs`` is… (+4 more)

### Community 148 - "postgres service (PostgreSQL 17, loopback :5433)"
Cohesion: 0.29
Nodes (7): postgres service (PostgreSQL 17, loopback :5433), Fernet encryption at rest (ENCRYPTION_KEY, write-once), Backups (pgdata volume, nightly pg_dump, ephemeral Redis), Required secrets (POSTGRES_PASSWORD, JWT_SECRET >= 32 chars, ENCRYPTION_KEY Fernet), Production hardening checklist (secrets, ENVIRONMENT, no seed, TLS, rotation), Compose vs host network namespaces (postgres:5432 vs 127.0.0.1:5433), Simulation mode (SIMULATION_MODE)

### Community 149 - "test_rbac.py"
Cohesion: 0.14
Nodes (17): A fresh, deliverable-shaped address unique to a single test. ``example.com`` is…, unique_email(), test_second_register_without_invite_is_rejected(), _invite_user(), _org_headers(), Role-based access control: least-privileged users are properly boxed in., Admin invites a user with *role_name*; returns their credentials dict., Headers for an invited user, scoped to the organization they joined. An account… (+9 more)

### Community 150 - "nexusops-understand.mjs"
Cohesion: 0.33
Nodes (5): COMMON, meta, out, READERS, SCHEMA

### Community 151 - "Invisible account lockout (5 fails -> 15 min, enumeration resistance)"
Cohesion: 0.33
Nodes (6): Invisible account lockout (5 fails -> 15 min, enumeration resistance), Unified error envelope (code, message, request_id), Per-IP rate limiting (Redis fixed window), Request lifecycle (edge -> middleware -> rate limit -> deps -> router), Client IP resolution (resolve_client_ip, TRUSTED_PROXY_CIDRS, XFF overwrite), EmailStr rejects reserved domains (login 422 on .test/.local/.arpa)

### Community 152 - "test_event_registry.py"
Cohesion: 0.21
Nodes (8): event_type_catalogue(), is_known_event_type(), Canonical registry of system-event types. Single source of truth shared by…, Return True when *event_type* is part of the canonical registry., Serialise the registry for the ``/events/types`` endpoint., Registry coherence: schema-advertised event types must equal the canonical…, test_catalogue_serialises_every_entry(), test_known_event_lookup()

### Community 153 - "test_notifications.py"
Cohesion: 0.36
Nodes (9): NotificationDelivery, _channel(), _delivery(), UUID, Notification channel + delivery-log endpoints. Regression coverage for GET…, The same event frame consumed twice queues ONE delivery per channel. Every API…, test_dispatch_frame_is_idempotent_across_workers(), test_list_deliveries_filters_by_channel() (+1 more)

### Community 154 - "nexusops-draft.mjs"
Cohesion: 0.40
Nodes (4): DOCS, meta, SPINE, VERIFY_RULES

### Community 155 - "hash_token"
Cohesion: 0.26
Nodes (12): generate_agent_token(), generate_api_key(), generate_refresh_token(), hash_token(), Return ``(raw_token, sha256_hex_hash)``., Return ``(raw_key, prefix, hash)``. Keys look like ``nxo_live_<random>``., test_agent_token_prefix_convention(), test_api_and_agent_prefixes_differ() (+4 more)

### Community 156 - "nexusops-challenge.mjs"
Cohesion: 0.33
Nodes (5): CHALLENGE_COMMON, meta, RESEARCH_COMMON, SCHEMA, TASKS

### Community 157 - "pytest"
Cohesion: 0.18
Nodes (14): _enrolled(), _heartbeat(), Agent ingest pipeline: hello, heartbeat, staleness transitions, events., A container absent from a later heartbeat is gone from the daemon., A payload at the agent's cap may be truncated — absence proves nothing., test_heartbeat_at_container_cap_skips_reconciliation(), test_heartbeat_removes_vanished_containers(), test_heartbeat_updates_status_metrics_and_containers() (+6 more)

### Community 158 - "test_schemas_agent.py"
Cohesion: 0.23
Nodes (18): AgentHeartbeatIn, Periodic metrics + observed containers from an enrolled agent., _container(), _heartbeat(), parametrize, Unit tests for agent-facing schemas (heartbeat + container payloads)., test_allowed_container_statuses(), test_bogus_status_string_rejected() (+10 more)

### Community 159 - "test_run_async_publishes_frames_scheduled_by_the_commit_hook"
Cohesion: 0.29
Nodes (5): _FakeDb, Stands in for an ``AsyncSession`` whose only job here is ``sync_session``. A…, The shape of a worker task whose last statement is a commit., test_run_async_publishes_frames_scheduled_by_the_commit_hook(), commit_then_return()

### Community 160 - "AgentClient"
Cohesion: 0.29
Nodes (3): AgentClient, Flag plain-HTTP transports that expose the enrollment token. The X-Agent-Token…, _UnixHTTPConnection

### Community 161 - "register_exception_handlers"
Cohesion: 0.24
Nodes (9): _error_payload(), Any, FastAPI, Request, register_exception_handlers(), handle_app_error(), handle_http_exception(), handle_unexpected() (+1 more)

### Community 162 - "lax"
Cohesion: 0.40
Nodes (5): lax(), fixture, Production posture: private targets are NOT allowed (resolution runs)., Simulation posture: resolution skipped, syntax still enforced., strict()

### Community 163 - "2. Entities"
Cohesion: 0.15
Nodes (13): 0. Design stance, 1. The hierarchy, 2.1.1 ApiKey org binding detail, 2.2.1 Environment promotion detail — **shipped in Phase 2**, 2.2 Delivery (existing models, extended), 2.3 Infrastructure — Nodes, 2.4 Routing & TLS (new subsystem), 2.5 Secrets (re-scoped — **shipped in Phase 2**) (+5 more)

### Community 164 - "journey.spec.ts"
Cohesion: 0.29
Nodes (4): ADMIN, formLogin(), uiGoto(), UNIQUE

### Community 165 - "_FakeAsyncClient"
Cohesion: 0.22
Nodes (3): _FakeAsyncClient, _FakeRequestObj, Scripted httpx.AsyncClient: responses keyed by absolute request URL.

### Community 166 - "dispatch_event_frame"
Cohesion: 0.20
Nodes (12): _as_uuid(), dispatch_event_frame(), _send(), dispatcher_loop(), Any, Render an event frame into an ASCII-safe ``(subject, body)`` pair., Queue an event frame to every subscribed enabled channel; send immediately.…, Consume ``nx:events`` and sweep due retries forever. Runs as a lifespan task. (+4 more)

### Community 167 - "AuthContext"
Cohesion: 0.10
Nodes (28): _attach_organization(), AuthContext, get_current_user(), get_identity(), get_optional_user(), _load_permissions(), membership_for_org(), _org_id_from_header() (+20 more)

### Community 168 - "AgentHelloIn"
Cohesion: 0.29
Nodes (7): AgentHelloIn, First contact from an agent after enrollment; fills static host facts., test_agent_hello_bounds(), test_agent_hello_minimal(), 4.1 Wire contract today (real, pinned by tests), 4.2 v2 additions, 4. Heartbeat contract v2

### Community 170 - "require_permission"
Cohesion: 0.20
Nodes (9): permission_dep(), Any, Dependency factory enforcing a permission; returns 403 when denied., require_permission(), _check(), _FakeCtx, Duck-typed stand-in for AuthContext., test_require_permission_raises_forbidden_when_denied() (+1 more)

### Community 171 - "get_meta"
Cohesion: 0.40
Nodes (5): get_meta(), DbSessionDep, get, Public metadata; identity fields appear only for valid credentials., OptionalUser

### Community 172 - "ApplicationBase"
Cohesion: 0.40
Nodes (4): ApplicationBase, Any, field_validator, Shared application fields; ``build_config`` is a free-form dict.

### Community 173 - "6. Tooling: reproducible e2e"
Cohesion: 0.25
Nodes (9): _is_same_origin(), Browsers always send Origin on WS handshakes, even same-origin ones. When it…, 1. What Phase 1 delivered, 3. Security mechanisms (per brief requirement), 5. Tests, 6. Tooling: reproducible e2e, 7. Known limitations and unresolved issues, 8. Position (+1 more)

### Community 174 - "get_latest_server_metrics"
Cohesion: 0.25
Nodes (11): get_dashboard_summary(), get_latest_server_metrics(), get_server_metrics(), CurrentUser, DbDep, Depends, get, UUID (+3 more)

### Community 175 - "ensure_dispatchable"
Cohesion: 0.22
Nodes (10): _bounded(), ensure_dispatchable(), Any, Keep one agent report from becoming an unbounded row. The agent is…, The registry entry for *op_type* (KeyError is a programming error)., Refuse a type whose capability this deployment cannot confirm. The capability…, spec_for(), MonkeyPatch (+2 more)

### Community 176 - "celery_app.py"
Cohesion: 0.20
Nodes (8): Celery application: periodic cadences live here, dynamic work is claimed…, task, Heartbeat sweeps: offline detection and recovery for servers., Flag silent servers OFFLINE, recover returning ones. Safe to overlap., sweep_servers(), _run(), celery, celery_schedules

### Community 177 - "config.py"
Cohesion: 0.19
Nodes (8): fail_on_bad_config(), Central configuration. All runtime configuration flows through this module so…, Exit immediately with a readable message if configuration is invalid. Also…, assert_safe_url_async(), Async wrapper around :func:`assert_safe_url`; DNS runs off the loop., ParseResult, pydantic_settings, urllib_parse

### Community 178 - "ContainerInfo"
Cohesion: 0.28
Nodes (4): ContainerInfo, List containers visible to the provider., Inspect a single container by id (short ids allowed)., Normalized view of a container as reported by any provider.

### Community 179 - "simulation.py"
Cohesion: 0.31
Nodes (8): _containers_for(), task, Simulation mode: drive the seeded fleet so dashboards stay alive on a laptop.…, Deterministic smooth value in [base-amplitude, base+amplitude]., Stable per-server container set; one container cycles EXITED occasionally., simulation_tick(), _run(), _wave()

### Community 180 - "websocket_endpoint"
Cohesion: 0.67
Nodes (3): websocket, Hand the socket to the hub (auth handshake handled there)., websocket_endpoint()

### Community 181 - "20261009_1000-c3d4e5f6a7b8_enforce_secret_version_integrity.py"
Cohesion: 0.48
Nodes (6): _clear_app_role_guc(), downgrade(), Phase 2.1 — enforce append-only ``secret_versions`` in the database. Phase 2…, Publish the app-role name to the migration GUC the revoke block reads., _set_app_role_in_guc(), upgrade()

### Community 184 - "20261008_1200-b2c3d4e5f6a7_add_projects_and_environments.py"
Cohesion: 0.53
Nodes (5): downgrade(), _drop_constraint(), _quoted_list(), Phase 2 — projects & environments: env promotion, config, secret versions. This…, upgrade()

### Community 185 - "20261009_1100-d4e5f6a7b8c9_correct_legacy_environment_types.py"
Cohesion: 0.33
Nodes (3): downgrade(), Phase 2.1 — correct legacy ``environment_type`` classification. The Phase 2…, No-op: the correction is a best-effort classification, not reversible.…

### Community 186 - "permissions.py"
Cohesion: 0.40
Nodes (3): PermissionSpec, Permission registry and role matrix. Permissions are *data*: the registry below…, fnmatch

### Community 187 - "permissions_for_role"
Cohesion: 0.40
Nodes (5): effective_permissions(), permissions_for_role(), User, Sorted permission codenames a role grants; ``*`` expands to the registry.…, Instance-level permissions for a user (legacy default-role view). Deliberately…

### Community 188 - "instant_pacing"
Cohesion: 0.40
Nodes (4): instant_pacing(), fixture, MonkeyPatch, Remove the per-line sleeps; pacing bounds are asserted separately.

### Community 189 - "configure_logging"
Cohesion: 0.50
Nodes (4): configure_logging(), _orjson_dumps(), Any, Configure structlog + stdlib logging once at process start. Everything…

## Knowledge Gaps
- **420 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+415 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1837 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `6. Tooling: reproducible e2e` connect `6. Tooling: reproducible e2e` to `client.ts`, `ensure_dispatchable`, `_entity_exists`, `sweep_session`, `test_tenant_isolation.py`, `auth_service.py`?**
  _High betweenness centrality (0.226) - this node is a cross-community bridge._
- **Why does `useEventStream()` connect `client.ts` to `AuthContext.tsx`, `App.tsx`, `apiGet`, `ServerDetailPage.tsx`, `6. Tooling: reproducible e2e`?**
  _High betweenness centrality (0.226) - this node is a cross-community bridge._
- **Why does `TenancyScopeError` connect `test_tenant_isolation.py` to `v1/search.py`, `AuthContext`, `models/__init__.py`, `test_operations.py`, `6. Tooling: reproducible e2e`, `record`, `enums.py`, `containers.py`, `core/tenancy.py`, `sweep_session`, `get_sessionmaker`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
- **Are the 79 inferred relationships involving `AuthContext` (e.g. with `TenancyScopeError` and `MembershipStatus`) actually correct?**
  _`AuthContext` has 79 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `APIModel` (e.g. with `OperationSpec` and `test_specs_reject_unknown_params()`) actually correct?**
  _`APIModel` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `apiGet()` (e.g. with `ContainerDetailPage.test.tsx` and `mockApi()`) actually correct?**
  _`apiGet()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `meta`, `SCHEMA`, `RESEARCH_COMMON` to the rest of the system?**
  _420 weakly-connected nodes found - possible documentation gaps or missing edges._