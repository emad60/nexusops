# Graph Report - nexusops  (2026-10-10)

## Corpus Check
- 324 files · ~305,868 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: (none) 8, .example 1, .service 1)

## Summary
- 4843 nodes · 14115 edges · 200 communities (177 shown, 23 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1125 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9ba728eb`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- apiGet
- AuthContext
- App.tsx
- types.ts
- operation.py
- AlertsPage.tsx
- resolve_client_ip
- useToast
- form.tsx
- test_agent_v2.py
- test_operations.py
- ServerDetailPage.tsx
- APIModel
- client.ts
- projects.py
- models/__init__.py
- deployment_engine.py
- SimulatedDockerProvider
- NotFound
- v1/secrets.py
- _delivery_chain
- list_containers
- dashboard_summary
- test_security.py
- Domain Routing — NexusOps
- monitor_service.py
- Node & Agent Architecture
- test_agent_backoff.py
- SimulatedDeploymentRunner
- nexusops_agent.py
- integration/conftest.py
- login
- container_service.py
- rate_limit.py
- docker_hosts.py
- test_ws_hub.py
- Hub
- search
- enums.py
- typing
- DockerProvider
- HTTPMonitorTransport
- StepFailure
- toast.tsx
- docker_real.py
- test_permissions.py
- list_events
- test_phase3_nodes.py
- BadRequest
- secret_service.py
- roles.py
- update_server
- apikeys.py
- test_migration_phase2.py
- v1/auth.py
- test_auth_journey.py
- sweep_session
- collections_abc
- notification_service.py
- helpers.py
- compilerOptions
- _list_deployments
- register_exception_handlers
- organizations.py
- test_phase2_environments.py
- mark_all_read
- test_schema_redaction.py
- PageParams
- decrypt_str
- package.json
- test_event_registry.py
- test_secrets.py
- v1/agent.py
- create_host
- api service (FastAPI / uvicorn :8000)
- deps.py
- AsyncSession
- DockerProviderError
- incidents.py
- test_phase2_secrets.py
- AuthContext.tsx
- publish
- users.py
- tests/conftest.py
- test_schemas_server.py
- create_user
- devDependencies
- operation_service.py
- log_service.py
- Settings
- container.py
- validate_config
- Path
- test_tenant_concurrency.py
- test_phase21_secret_version_integrity.py
- StepLine
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- journey.spec.ts
- run_async
- Secrets Architecture
- README.md - NexusOps overview
- v1/operations.py
- test_tenant_isolation.py
- AppError
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- @tanstack/react-query
- RolesPage.tsx
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- ScopedSession
- create_organization
- main.py
- schemas/health.py
- scripts
- get_redis
- test_tenancy_allowlist.py
- _monitor
- dependencies
- DeploymentDetailPage.test.tsx
- generate_secrets.sh
- ServerOut
- server_payload
- test_migration_phase22.py
- middleware.py
- _run_docker_action
- list_operations
- v1/audit.py
- install.sh
- docker-entrypoint.sh
- integration/__init__.py
- ContainerListPage.tsx
- CLAUDE.md - project graphify rules
- Graphify query workflow (query / path / explain / update)
- frontend/index.html - SPA shell
- NexusOps Favicon — stylized letter 'N' lettermark in sky blue (#38bdf8) on a dark navy rounded square (#0b1120, 7px corner radius)
- nexusops-backend
- test_auth_multi_org.py
- 20260922_1000-a3f1c8d24b6e_add_tenancy_foundation.py
- postgres service (PostgreSQL 17, loopback :5433)
- phase3.spec.ts
- nexusops-understand.mjs
- Invisible account lockout (5 fails -> 15 min, enumeration resistance)
- _raw_probe
- _docker_request
- nexusops-draft.mjs
- notification_sender.py
- nexusops-challenge.mjs
- test_agent_ingestion.py
- test_schemas_agent.py
- test_run_async_publishes_frames_scheduled_by_the_commit_hook
- main
- test_monitor_transport.py
- test_notifications.py
- redact_mapping
- AgentClient
- build_heartbeat
- celery_app.py
- resolve_auth
- simulation.py
- .__tablename__
- .state
- get_settings
- _FakeAsyncClient
- permissions.py
- logging.py
- 2. Entities
- DeploymentRunner
- create_operation
- network_rates
- test_migration_phase21.py
- websocket_endpoint
- get_transport
- require_permission
- 8. Upstream binding and re-render triggers
- _entity_exists
- coerce_headers
- maintenance.py
- Conflict
- instant_pacing
- servers.py
- EnvironmentUpdate
- permissions_for_role
- list_servers
- pytest
- upsert_tag
- NexusOps — Phase 1 (Multi-Tenancy) Report
- _pace
- test_same_origin_compares_the_full_authority_including_port
- 9. Phase 6 — Real deployments
- ._shallow_validate

## God Nodes (most connected - your core abstractions)
1. `AuthContext` - 140 edges
2. `APIModel` - 125 edges
3. `apiGet()` - 82 edges
4. `get_settings()` - 80 edges
5. `NotFound` - 73 edges
6. `record()` - 69 edges
7. `Server` - 63 edges
8. `publish()` - 61 edges
9. `apiPost()` - 60 edges
10. `useToast()` - 58 edges

## Surprising Connections (you probably didn't know these)
- `2. Org resolution on every request` --references--> `resolve_auth()`  [INFERRED]
  docs/multi-tenancy.md → backend/app/api/deps.py
- `3. Cross-cutting decisions` --references--> `require_permission()`  [INFERRED]
  docs/domain-model.md → backend/app/api/deps.py
- `10. Phase 7 — Teams, grants & custom roles` --references--> `require_permission()`  [INFERRED]
  docs/product-roadmap.md → backend/app/api/deps.py
- `3.2 Route` --references--> `rate_limit()`  [INFERRED]
  docs/domain-routing.md → backend/app/core/rate_limit.py
- `6.2 The allowlist (the injection defense)` --references--> `rate_limit()`  [INFERRED]
  docs/domain-routing.md → backend/app/core/rate_limit.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three authentication credential families with centralized permission checks** — docs_api_md_auth, docs_api_md_refresh_rotation, docs_api_md_api_keys, docs_agent_md_enrollment_token, docs_api_md_permission_model [EXTRACTED 1.00]
- **NexusOps compose stack services** — docker_compose_yml_nexusops_stack, docker_compose_yml_postgres_service, docker_compose_yml_redis_service, docker_compose_yml_mailpit_service, docker_compose_yml_api_service, docker_compose_yml_worker_service, docker_compose_yml_scheduler_service, docker_compose_yml_frontend_service, docker_compose_yml_nginx_service [EXTRACTED 1.00]
- **WebSocket real-time fan-out spine** — docs_architecture_md_websocket_hub, docs_api_md_websocket_channels, docker_compose_yml_redis_service, docs_architecture_md_event_bus, readme_react_spa [INFERRED 0.85]

## Communities (200 total, 23 thin omitted)

### Community 0 - "apiGet"
Cohesion: 0.05
Nodes (56): apiGet(), apiPost(), MonitorOut, SessionInfo, MonitorDetailPage, MonitorListPage, ProjectListPage, SessionsPage (+48 more)

### Community 1 - "AuthContext"
Cohesion: 0.11
Nodes (51): AuthContext, Resolved identity plus the organization this request acts in.…, Any, AsyncSession, Request, UUID, Append an audit row using the caller's transaction (no commit here). The…, record() (+43 more)

### Community 2 - "App.tsx"
Cohesion: 0.05
Nodes (82): ApiKeyOut, DeploymentOut, DeploymentStepOut, IncidentEventOut, Page, ProjectOut, SecretRow, ApiKeysPage (+74 more)

### Community 3 - "types.ts"
Cohesion: 0.06
Nodes (29): AuditEntry, CapabilityReport, CheckOut, DeploymentLogLine, DeploymentStatus, EnrollmentTokenCreated, EnrollmentTokenItem, EnrollmentTokenState (+21 more)

### Community 4 - "operation.py"
Cohesion: 0.07
Nodes (35): Record the agent's outcome for an operation it claimed. The report is…, report_operation_result(), OperationType, The whitelist. Nothing outside this enum ships as an exec surface. Each type…, AgentOperationClaimOut, AgentOperationResultIn, AgentOperationResultOut, ContainerActionParams (+27 more)

### Community 5 - "AlertsPage.tsx"
Cohesion: 0.11
Nodes (21): AlertOut, ChannelOut, DeliveryOut, AlertsPage, AlertsPage(), ChannelDialog(), DeleteChannelDialog(), describeError() (+13 more)

### Community 6 - "resolve_client_ip"
Cohesion: 0.18
Nodes (21): _is_trusted(), _parse_networks(), Request, Client-IP resolution behind chained reverse proxies. The API never takes TCP…, Parse a comma-separated CIDR list; malformed entries are skipped., Real client address for *request* per the trust model above., resolve_client_ip(), make_request() (+13 more)

### Community 7 - "useToast"
Cohesion: 0.11
Nodes (32): apiDelete(), apiPatch(), ApplicationOut, ENVIRONMENT_TYPE_LABELS, EnvironmentDetailOut, EnvironmentOut, EnvironmentType, ProjectDetailPage (+24 more)

### Community 8 - "form.tsx"
Cohesion: 0.09
Nodes (20): LoginPage, OrganizationRequiredPage, CheckboxField(), CheckboxFieldProps, FieldAria, FieldBaseProps, PasswordFieldProps, SearchInput() (+12 more)

### Community 9 - "test_agent_v2.py"
Cohesion: 0.08
Nodes (36): agent_fixture(), _load_agent(), Any, fixture, parametrize, Agent protocol v2: honest metrics, capability detection, and the executor. The…, Trusting a private CA must not weaken verification., No CLI switch may disable TLS verification. (+28 more)

### Community 10 - "test_operations.py"
Cohesion: 0.08
Nodes (53): assert_error_code(), Assert envelope shape + code; returns the inner error object., test_metadata_endpoint_and_private_target_blocked(), _dispatch(), _dispatch_body(), _enrolled_node(), _mutate_in_system_scope(), MonkeyPatch (+45 more)

### Community 11 - "ServerDetailPage.tsx"
Cohesion: 0.09
Nodes (29): MetricPoint, OperationItem, OperationType, ServerDetailPage, ServerListPage, ChartSeries, LineChart(), LineChartProps (+21 more)

### Community 12 - "APIModel"
Cohesion: 0.04
Nodes (85): AgentEnrollIn, AgentEnrollOut, AgentHeartbeatOut, AgentTokenRotation, CapabilityReport, Agent-facing schemas. Payloads are data only — never executed. Wire protocol v2…, A pending credential rotation, delivered on the agent's next beat. Served…, v2 heartbeat response: cadence, work to pull, and any pending rotation. A v1… (+77 more)

### Community 13 - "client.ts"
Cohesion: 0.05
Nodes (45): API_BASE, ApiError, apiRequest(), buildUrl(), extractError(), getAccessToken(), getActiveOrgId(), onActiveOrgChange() (+37 more)

### Community 14 - "projects.py"
Cohesion: 0.11
Nodes (50): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+42 more)

### Community 15 - "models/__init__.py"
Cohesion: 0.06
Nodes (79): _org_scoped_classes(), Mapped classes marked :class:`~app.models.base.OrgScoped`. Reads the mapper…, Base, big_serial_pk(), json_column(), org_id_column(), OrgScoped, datetime (+71 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.09
Nodes (63): deployment_log_channel(), Deployment, DeploymentStep, DeploymentStatus, DeploymentTrigger, EventLevel, StepStatus, _after_commit_enqueue() (+55 more)

### Community 17 - "SimulatedDockerProvider"
Cohesion: 0.09
Nodes (33): ContainerHealth, ContainerStatus, Container, Observed container state mirrored from an agent or docker provider., Any, Plausible numbers derived from the row plus time-based sine noise., Implements :class:`DockerProvider` semantics against DB rows., Make a container row visible to this provider instance. (+25 more)

### Community 18 - "NotFound"
Cohesion: 0.10
Nodes (36): NotFound, generate_agent_token(), generate_enrollment_token(), hash_token(), A per-node credential (``nxa_``): long-lived, node-scoped, never shared., An enrollment credential (``nxk_``): single-use, short-lived, org-scoped.…, Return the active org id or raise; used by services that need it explicitly., require_org() (+28 more)

### Community 19 - "v1/secrets.py"
Cohesion: 0.13
Nodes (30): create_secret(), delete_secret(), get_secret(), list_secret_versions(), list_secrets(), DbSession, delete, get (+22 more)

### Community 20 - "_delivery_chain"
Cohesion: 0.13
Nodes (23): _as_worker(), _delivery_chain(), _owner_ctx(), _queue(), _queued_with_recorder(), Regression: the trigger route must re-read the queued row eagerly.…, Enter the organization scope the worker would be running in. The engine opens…, queue_deployment with the Celery handoff recorded instead of dispatched. (+15 more)

### Community 21 - "list_containers"
Cohesion: 0.08
Nodes (41): _action_route(), _endpoint(), _decode_frame(), _ev(), get_container(), _like_pattern(), list_container_logs(), list_containers() (+33 more)

### Community 22 - "dashboard_summary"
Cohesion: 0.07
Nodes (38): get_dashboard_summary(), get_latest_server_metrics(), get_server_metrics(), CurrentUser, DbDep, Depends, get, UUID (+30 more)

### Community 23 - "test_security.py"
Cohesion: 0.08
Nodes (40): Whether this request's cookie will travel over https. The edge always…, _transport_is_https(), Unauthorized, create_access_token(), decode_access_token(), generate_api_key(), generate_refresh_token(), password_needs_rehash() (+32 more)

### Community 24 - "Domain Routing — NexusOps"
Cohesion: 0.09
Nodes (22): 10. Wildcards and catch-all, 11. User journey, 12. API surface, permissions, audit, 13. Monitoring tie-in, 1. Scope and current state, 2. Where nginx runs, 3.1 Domain, 3.2 Route (+14 more)

### Community 25 - "monitor_service.py"
Cohesion: 0.06
Nodes (91): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+83 more)

### Community 26 - "Node & Agent Architecture"
Cohesion: 0.09
Nodes (22): install_hint(), The one-liner an operator pastes, without the raw token in argv. The token…, 1. Scope and stance, 3.2 Enrollment v2, 3.3 Token storage & rotation with dual-token grace, 3.4 Revocation semantics — fixing the 401 hot-loop, 3.5 Reconnect / offline states, 3. Agent lifecycle (+14 more)

### Community 27 - "test_agent_backoff.py"
Cohesion: 0.14
Nodes (22): agent_fixture(), _install_sleep(), fake_sleep(), _load_agent(), _patch_host(), Any, fixture, MonkeyPatch (+14 more)

### Community 28 - "SimulatedDeploymentRunner"
Cohesion: 0.25
Nodes (23): Staged docker-style simulation used by v1 deployments., Canonical step identifiers stored on :class:`DeploymentStep` rows., SimulatedDeploymentRunner, StepName, _collect(), _ctx(), Unit tests for SimulatedDeploymentRunner (async generators, no broker)., RESOLVE_CONFIG is planned by the engine, not produced by a runner. (+15 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.13
Nodes (19): build_capabilities(), _build_hello_payload(), docker_capability(), _docker_socket(), _enroll(), memory_total_mb(), os_info(), NexusOps host agent — protocol v2. Reports host metrics and Docker container… (+11 more)

### Community 30 - "integration/conftest.py"
Cohesion: 0.11
Nodes (26): dispose_engine(), _admin_dsn(), _clean_slate(), client(), _ensure_database(), _migrated_database(), org_db(), AsyncClient (+18 more)

### Community 31 - "login"
Cohesion: 0.10
Nodes (43): active_memberships(), The user's memberships in non-suspended organizations, oldest first. Reads only…, System scope bound to *db*, for rows that have no organization. Used by exactly…, system_write_scope(), _audit(), _auth_event_scope(), change_own_password(), count_users() (+35 more)

### Community 32 - "container_service.py"
Cohesion: 0.12
Nodes (32): clip(), Truncate *text* to *limit* characters, stripping control chars., describe_provider_error(), is_simulated(), provider_for(), Exception, Return the provider matching *host*'s endpoint configuration., True when *provider* is the simulated implementation. (+24 more)

### Community 33 - "rate_limit.py"
Cohesion: 0.12
Nodes (26): RateLimited, client_ip(), _enforce(), _memory_count_and_ttl(), node_rate_limit(), _dependency(), Request, rate_limit() (+18 more)

### Community 34 - "docker_hosts.py"
Cohesion: 0.07
Nodes (55): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+47 more)

### Community 35 - "test_ws_hub.py"
Cohesion: 0.14
Nodes (25): _connection(), _drain(), _event_frame(), _fake_sessionmaker(), _FakeSession, hub(), _Org, Any (+17 more)

### Community 36 - "Hub"
Cohesion: 0.13
Nodes (18): _close_socket(), Connection, _frame_org(), Hub, _params_key(), _parse_payload(), Any, WebSocket (+10 more)

### Community 37 - "search"
Cohesion: 0.08
Nodes (41): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+33 more)

### Community 38 - "enums.py"
Cohesion: 0.06
Nodes (60): Canonical Redis pub/sub channel names shared by API, workers and WS hub., server_metrics_channel(), AlertSeverity, AuditResult, CredentialKind, DockerHostStatus, EnrollmentTokenState, EnvironmentType (+52 more)

### Community 39 - "typing"
Cohesion: 0.08
Nodes (43): asyncio, Alert inbox endpoints. Authenticated users see the shared operator feed., create_channel(), delete_channel(), get_channel(), list_channels(), list_deliveries(), DbDep (+35 more)

### Community 40 - "DockerProvider"
Cohesion: 0.08
Nodes (14): ContainerInfo, DockerProvider, Any, datetime, Protocol, List containers visible to the provider., Inspect a single container by id (short ids allowed)., List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``. (+6 more)

### Community 41 - "HTTPMonitorTransport"
Cohesion: 0.21
Nodes (12): HTTPMonitorTransport, Real HTTP(S) probe using httpx with per-monitor settings. Redirects are…, _FakeResponse, MonkeyPatch, A 302 from a public URL into link-local/metadata space must be refused., Defense in depth: even the httpx client must never auto-follow., _script_client(), test_httpx_client_is_created_without_auto_redirects() (+4 more)

### Community 42 - "StepFailure"
Cohesion: 0.11
Nodes (19): Exception, Raised by a runner when a step fails irrecoverably., StepFailure, 10. Events and WS during runs, 11. Post-deploy hooks, 12. Rollback semantics (existing behavior kept), 13. The simulated runner stays — labeled, 14. Open questions (+11 more)

### Community 43 - "toast.tsx"
Cohesion: 0.03
Nodes (67): ContainerOut, DockerHostOut, ServerDetail, ServerSummary, ACTIVE_MEMBERSHIP, ME, mocks, Toast (+59 more)

### Community 44 - "docker_real.py"
Cohesion: 0.09
Nodes (25): ContainerStats, Point-in-time resource usage snapshot., _as_float(), _compute_stats(), _cpu_percent(), _network_bytes(), parse_log_line(), parse_rfc3339() (+17 more)

### Community 45 - "test_permissions.py"
Cohesion: 0.16
Nodes (11): permission_exists(), _auth_context(), Unit tests for the permission registry, scope matching and RBAC gate., A fake context in the given organization. ``membership_status=None`` models a…, test_api_key_scope_intersects_role_permissions(), test_membership_is_required_for_authority(), test_permission_exists_helper(), test_plain_user_without_permissions_is_denied() (+3 more)

### Community 46 - "list_events"
Cohesion: 0.22
Nodes (13): _decode_cursor(), _encode_cursor(), list_event_types(), list_events(), datetime, DbSession, Depends, get (+5 more)

### Community 47 - "test_phase3_nodes.py"
Cohesion: 0.15
Nodes (33): _create_token(), _dispatch(), _enroll(), _enrolled_node(), _load_agent_module(), _mutate_in_system_scope(), Phase 3 — Nodes & Agent v2 end-to-end behaviour. Grouped by the question each…, Import the shipped agent source (sync, so async tests never touch Path). (+25 more)

### Community 48 - "BadRequest"
Cohesion: 0.07
Nodes (63): BadRequest, UnprocessableEntity, assert_safe_tcp_endpoint(), assert_safe_url(), _is_forbidden_address(), is_simulation_url(), ValueError, _raise_block() (+55 more)

### Community 49 - "secret_service.py"
Cohesion: 0.10
Nodes (43): An encrypted configuration value, scoped to org, project or environment.…, One immutable value of a :class:`Secret` — append-only history. A row is…, Secret, SecretVersion, _actor_type(), _collect_refs(), create_secret(), delete_secret() (+35 more)

### Community 50 - "roles.py"
Cohesion: 0.11
Nodes (29): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, delete, get (+21 more)

### Community 51 - "update_server"
Cohesion: 0.15
Nodes (20): delete_server(), delete, patch, post, Request, UUID, Create a tag or update its colour (idempotent on name)., Revoke an unused enrollment token immediately. (+12 more)

### Community 52 - "apikeys.py"
Cohesion: 0.16
Nodes (18): create_api_key(), list_api_keys(), CurrentUser, DbSessionDep, delete, get, post, Request (+10 more)

### Community 53 - "test_migration_phase2.py"
Cohesion: 0.12
Nodes (34): alembic_config, alembic_script, An explicit non-DEV classification survives the corrective migration. The…, test_only_dev_defaulted_rows_are_corrected(), _alembic_config(), _exec(), _migration_dsn(), _owner_dsn() (+26 more)

### Community 54 - "v1/auth.py"
Cohesion: 0.09
Nodes (47): change_password(), _clear_refresh_cookie(), _cookies_secure(), login(), logout(), me(), _optional_actor(), AsyncSession (+39 more)

### Community 55 - "test_auth_journey.py"
Cohesion: 0.10
Nodes (27): cookie_attributes(), Response, The raw Set-Cookie header carrying the refresh token., Extract just the opaque token from a Set-Cookie header., Parse Set-Cookie attributes (lowercased keys, empty string for flags)., refresh_cookie_header(), refresh_cookie_value(), _cookie_name() (+19 more)

### Community 56 - "sweep_session"
Cohesion: 0.17
Nodes (22): _run(), task, Monitor dispatch: claim due monitors atomically, run their checks., Claim up to CLAIM_BATCH due monitors and execute each check.…, run_due_monitors(), _run(), org_for(), org_session() (+14 more)

### Community 57 - "collections_abc"
Cohesion: 0.06
Nodes (14): alembic, downgrade(), rename ``server.*`` permission codenames to ``node.*`` The Node/Server…, _rename_permissions(), upgrade(), Fix pre-existing model/migration drift (surfaced by the new drift check). Two…, downgrade(), Phase 2.1 — correct legacy ``environment_type`` classification. The Phase 2… (+6 more)

### Community 58 - "notification_service.py"
Cohesion: 0.07
Nodes (66): patch, update_channel(), encrypt_str(), ChannelType, DeliveryStatus, NotificationChannel, NotificationDelivery, A delivery target (email address / webhook endpoint). ``config_ciphertext``… (+58 more)

### Community 59 - "helpers.py"
Cohesion: 0.07
Nodes (45): owner(), Bootstrap owner credentials for this test (fresh DB => first user). ``headers``…, bearer(), error_of(), login_account(), login_headers(), Any, AsyncClient (+37 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "_list_deployments"
Cohesion: 0.10
Nodes (37): cancel_deployment(), _emails_for(), get_deployment(), list_application_deployments(), list_deployment_logs(), _list_deployments(), _parse_sort(), alias (+29 more)

### Community 62 - "register_exception_handlers"
Cohesion: 0.12
Nodes (13): _error_payload(), Any, FastAPI, Request, register_exception_handlers(), handle_app_error(), handle_http_exception(), handle_unexpected() (+5 more)

### Community 63 - "organizations.py"
Cohesion: 0.15
Nodes (17): create_organization(), list_my_organizations(), CurrentUser, DbSessionDep, get, IdentityUser, patch, post (+9 more)

### Community 64 - "test_phase2_environments.py"
Cohesion: 0.18
Nodes (22): _environment(), _project(), parametrize, Phase 2: project-scoped environments, config layering, and their isolation. The…, Uniqueness is ``(project_id, slug)`` — not instance-wide., The update path is validated too (the pre-Phase-2 gap)., Knowing an environment UUID is not access: the project link must hold., Another tenant cannot reach the project, its environments, or its detail. (+14 more)

### Community 65 - "mark_all_read"
Cohesion: 0.25
Nodes (11): mark_all_read(), mark_read(), CurrentUser, DbDep, get, post, UUID, Mark every unread alert read; returns how many rows changed. (+3 more)

### Community 66 - "test_schema_redaction.py"
Cohesion: 0.15
Nodes (18): is_sensitive_header(), mask_sensitive_headers(), field_serializer, True when *name* looks like it carries a credential (Authorization etc.)., Return a copy of *headers* with sensitive values replaced by a mask., mask_target(), Human-readable masked target safe to expose over the API. For webhook families…, _monitor_out() (+10 more)

### Community 67 - "PageParams"
Cohesion: 0.12
Nodes (27): list_alerts(), Depends, Unread alerts first, then newest first., Cursor, decode_cursor(), encode_cursor(), Page, page_params() (+19 more)

### Community 68 - "decrypt_str"
Cohesion: 0.08
Nodes (29): decrypt_str(), digest_of(), Short server-verifiable digest used for change detection display. HMAC-SHA256…, parametrize, test_decrypt_with_wrong_ciphertext_raises_value_error(), test_digest_is_keyed_not_plain_sha256(), test_digest_length_and_determinism(), test_encrypt_decrypt_roundtrip() (+21 more)

### Community 69 - "package.json"
Cohesion: 0.13
Nodes (15): name, private, type, version, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom (+7 more)

### Community 70 - "test_event_registry.py"
Cohesion: 0.21
Nodes (8): event_type_catalogue(), is_known_event_type(), Canonical registry of system-event types. Single source of truth shared by…, Return True when *event_type* is part of the canonical registry., Serialise the registry for the ``/events/types`` endpoint., Registry coherence: schema-advertised event types must equal the canonical…, test_catalogue_serialises_every_entry(), test_known_event_lookup()

### Community 71 - "test_secrets.py"
Cohesion: 0.10
Nodes (28): Exception, A ``${secret:KEY}`` reference could not be resolved. Fail-closed. Carries…, One successfully resolved reference: metadata for audit, no value., Outcome of resolving an environment's config references., Resolve every ``${secret:KEY}`` reference an environment's config names.…, resolve_secrets_for_environment(), ResolvedSecrets, SecretReference (+20 more)

### Community 72 - "v1/agent.py"
Cohesion: 0.14
Nodes (23): agent_enroll(), agent_heartbeat(), agent_hello(), claim_operation(), _presented_token(), DbDep, post, Request (+15 more)

### Community 73 - "create_host"
Cohesion: 0.13
Nodes (26): _assert_endpoint_allowed(), _assert_name_free(), create_host(), delete_host(), endpoint_scheme(), list_images(), list_networks(), list_volumes() (+18 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "deps.py"
Cohesion: 0.05
Nodes (93): argon2, argon2_exceptions, FastAPI dependencies: database session, authenticated tenant context, RBAC…, Cross-entity global search powering the Ctrl+K command palette. Every section…, Error taxonomy and the single place where API error envelopes are shaped. Every…, get_logger(), _fernet(), hash_password() (+85 more)

### Community 76 - "AsyncSession"
Cohesion: 0.13
Nodes (29): _detail(), AsyncSession, acknowledge_rotation(), _actor_kwargs(), container_counts(), create_server(), delete_server(), get_server() (+21 more)

### Community 77 - "DockerProviderError"
Cohesion: 0.13
Nodes (16): DockerProviderError, Exception, Provider abstraction for docker hosts (real daemon or simulated). Providers are…, A provider operation failed. ``str()`` is safe to show/log., Build a compact, secret-free description of a provider failure. Only the…, sanitize_error(), Provider selection based on a docker host's endpoint URL. Mapping: *…, _iterate() (+8 more)

### Community 78 - "incidents.py"
Cohesion: 0.12
Nodes (37): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+29 more)

### Community 79 - "test_phase2_secrets.py"
Cohesion: 0.19
Nodes (21): _env(), _project(), Phase 2 secrets: layered scope, immutable versions, rollback, isolation. Two…, Two racing rotations must both be kept and never share a version number., Another tenant cannot read, rotate, roll back or even enumerate the secret., The documented example: same key at three scopes; most specific wins., A ref declared in the project base config resolves for its environments., _resolved() (+13 more)

### Community 80 - "AuthContext.tsx"
Cohesion: 0.04
Nodes (39): setAccessToken(), setActiveOrgId(), Membership, User, AuthContext, AuthProvider(), AuthState, isOrgSelectionError() (+31 more)

### Community 81 - "publish"
Cohesion: 0.13
Nodes (21): create_api_key(), Request, Create a key for *user_id*. Returns ``(row, raw_key)`` — raw shown once. The…, _after_commit_publish(), _after_rollback_drop(), publish(), _publish_after_commit(), _publish_redis() (+13 more)

### Community 82 - "users.py"
Cohesion: 0.12
Nodes (28): create_user(), deactivate_user(), get_user(), list_users(), CurrentUser, DbSessionDep, delete, get (+20 more)

### Community 83 - "tests/conftest.py"
Cohesion: 0.25
Nodes (6): configure_test_env(), Test bootstrap: pin every cached setting BEFORE the first ``app`` import. The…, KEY=VALUE pairs from the repo .env (first definition wins); never logged., Export the exact settings the app caches; host values cannot leak through., _read_dot_env(), os

### Community 84 - "test_schemas_server.py"
Cohesion: 0.21
Nodes (22): Payload for registering a server., Partial update. ``tags`` replaces the full set when provided., ServerCreate, ServerUpdate, _base(), parametrize, Unit tests for app.schemas.server (validation only, no I/O)., test_empty_ip_is_allowed_but_whitespace_collapses() (+14 more)

### Community 85 - "create_user"
Cohesion: 0.07
Nodes (49): list_sessions(), CurrentUser, DbSessionDep, delete, get, Request, UUID, Active sessions of this organization's members. Defaults to the caller's own;… (+41 more)

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "operation_service.py"
Cohesion: 0.17
Nodes (27): OperationStatus, Lifecycle of one node operation (node-agent-architecture.md §5.1).…, Operation, One whitelisted action for one node, with a CAS lifecycle. ``attempts`` is…, _active_org(), cancel_operation(), claim_operation(), expire_one() (+19 more)

### Community 88 - "log_service.py"
Cohesion: 0.12
Nodes (27): container_log_channel(), current_org(), The organization this unit of work is acting for, if any., LogSource, LogLine, One parsed log record from a container log stream., append_lines(), count_container_logs() (+19 more)

### Community 89 - "Settings"
Cohesion: 0.14
Nodes (6): field_validator, model_validator, Username from :attr:`database_url`, or ``None`` if it is unparseable., Validated application settings (loaded from environment / .env)., Settings, BaseSettings

### Community 90 - "container.py"
Cohesion: 0.15
Nodes (18): _container_out(), Serialize one row; env values never leave the database (keys only)., ContainerDetailOut, ContainerOut, ContainerRemoveOut, host_ref(), HostRef, LogEntryOut (+10 more)

### Community 91 - "validate_config"
Cohesion: 0.08
Nodes (31): field_validator, collect_secret_refs(), walk(), ConfigValidationError, effective_config(), merge_config(), Any, ValueError (+23 more)

### Community 92 - "Path"
Cohesion: 0.12
Nodes (14): Path, An unloadable CA file must error, never silently fall back to no verify., A throwaway key + self-signed cert for ``localhost`` (real handshakes)., A one-shot HTTPS server; records a failed handshake instead of crashing., A real handshake against a self-signed server must fail verification., Trusting that same cert as a CA lets the identical handshake through., A link-local URL over plain HTTP must fail before any request or write., _self_signed_cert() (+6 more)

### Community 93 - "test_tenant_concurrency.py"
Cohesion: 0.11
Nodes (34): current_scope(), ``'org'``, ``'system'`` or ``'unset'``., _create_server(), _guc(), _maker(), pooled_engine(), async_sessionmaker, AsyncEngine (+26 more)

### Community 94 - "test_phase21_secret_version_integrity.py"
Cohesion: 0.18
Nodes (18): _app_role_dsn(), _owner_dsn(), _probe(), Phase 2.1 — ``secret_versions`` is append-only in the **database**, not just in…, Immutability is a database guarantee, not merely a missing code path. The owner…, The legitimate append paths keep working under the guard., The documented deletion policy: purging a Secret cascades its history., RLS is preserved: another tenant cannot see a version row, even by id. (+10 more)

### Community 95 - "StepLine"
Cohesion: 0.26
Nodes (8): LogLevel, _commit_short(), Deployment runner port plus a faithful simulated implementation.…, Everything a runner needs to execute one deployment., One streamed output line for a step., RunContext, _slug(), StepLine

### Community 96 - "NexusOps (self-hosted infrastructure management and monitoring platform)"
Cohesion: 0.20
Nodes (10): mailpit service (dev SMTP sink + web UI :8025), NexusOps compose stack (8 services on one network), HIGH finding: redirect-following SSRF in uptime monitors (fixed: follow_redirects=False + per-hop guard), SSRF guard (assert_safe_url, per-redirect-hop validation, assert_safe_tcp_endpoint), Mailpit SMTP port internal-only (host-side injection needs extra mapping), Host port knobs (NEXUSOPS_HTTP_PORT/POSTGRES/REDIS/MAILPIT/VITE), SPA entry point (loads /src/main.tsx, dark color-scheme), Uptime monitors -> incidents -> notifications flow (+2 more)

### Community 97 - "REST API surface (/api/v1)"
Cohesion: 0.29
Nodes (7): Cursor (keyset) and offset pagination envelopes, Permission model (data-driven registry, require_permission, wildcard scopes), REST API surface (/api/v1), RBAC registry (PERMISSIONS + ROLE_MATRIX + scope_matches), Adding a new resource: 7-step checklist (model -> migration -> schemas -> service -> router -> tests -> frontend), Alembic migration workflow (autogenerate, models __init__ export, entrypoint apply), Command palette (Ctrl/Cmd+K)

### Community 98 - "journey.spec.ts"
Cohesion: 0.14
Nodes (16): EDGE, MAILPIT, ADMIN, Bootstrap, bootstrapVia(), test, ADMIN, formLogin() (+8 more)

### Community 99 - "run_async"
Cohesion: 0.12
Nodes (23): flush_pending_publishes(), Wait for frames scheduled by ``after_commit`` hooks to reach Redis. The commit…, task, Re-enqueue deployments the broker lost; fail ones whose worker died.…, sweep_deployments(), _run(), T, Run *coroutine* on a dedicated event loop (Celery workers are sync). The loop… (+15 more)

### Community 100 - "Secrets Architecture"
Cohesion: 0.11
Nodes (18): 10. Resolution flow at deploy time, 1.1 Storage and crypto, 1.2 Data model, 1.3 API surface (metadata-only reads), 1.6 Gap list (Phase 2 status), 1. Current state, 2.1 Resolution runs inside org scope, 2.2 Migration mapping (applied by `b2c3d4e5f6a7`) (+10 more)

### Community 101 - "README.md - NexusOps overview"
Cohesion: 0.06
Nodes (59): docker-compose.dev.yml - dev overlay, docker-compose.docker-sock.yml - docker socket override, docker-compose.yml - full stack definition, docs/agent.md - agent guide, docs/api.md - API guide, Append-only audit log (Postgres BEFORE UPDATE OR DELETE trigger), docs/architecture.md - system architecture, docs/deployment.md - deployment and operations guide (+51 more)

### Community 102 - "v1/operations.py"
Cohesion: 0.11
Nodes (20): _database_url(), Alembic environment: metadata comes from app.models, URL from app settings., Migrations run as the table **owner**, never as the application role. The owner…, Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online(), Metrics query API: node timeseries, latest snapshot, dashboard summary. (+12 more)

### Community 103 - "test_tenant_isolation.py"
Cohesion: 0.09
Nodes (38): _max_log_id(), Highest persisted log id for a container (poll fallback watermark)., get_sessionmaker(), async_sessionmaker, apply_scope_to_session(), org_scope(), UUID, Run the enclosed block as a single organization. Nesting the *same* org is a… (+30 more)

### Community 104 - "AppError"
Cohesion: 0.20
Nodes (16): AppError, Exception, Base class for expected, client-facing errors., _authenticate_api_key(), _authenticate_jwt(), _bind_organization(), _load_permissions(), _org_id_from_frame() (+8 more)

### Community 105 - "redis service (Redis 7, no persistence, loopback :6390)"
Cohesion: 0.22
Nodes (11): redis service (Redis 7, no persistence, loopback :6390), WebSocket API (/api/v1/ws handshake, frames, limits), WebSocket channels (global, server-metrics, container-logs, deployment-logs, incidents), Deployment engine (queue_deployment / execute_deployment / sweeper backstop), Real-time spine: PostgreSQL system_events + Redis pub/sub, Rollback as a new deployment (rollback_of_id), WebSocket hub (framework-thin, Redis fan-in, per-socket queues), Test suites (pytest unit+integration, vitest, Playwright e2e) (+3 more)

### Community 106 - "NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)"
Cohesion: 0.18
Nodes (12): Agent security model (one-way telemetry, no command channel), Agent enrollment token (X-Agent-Token, nxa_..., SHA-256 at rest), Agent heartbeat exponential backoff (cap 5 min, exit 1 on revoked token), agent/install.sh (enrollment installer), Agent metrics collection (/proc statvfs Docker socket), NexusOps agent (stdlib-only Python, agent/nexusops_agent.py), Agent systemd hardening (ProtectSystem=strict, NoNewPrivileges), Agent ingest API (POST /agent/hello, POST /agent/heartbeat) (+4 more)

### Community 107 - "@tanstack/react-query"
Cohesion: 0.05
Nodes (36): DashboardSummary, SearchResult, App(), DashboardPage, Command, CommandPalette(), CommandPaletteProps, STATIC_COMMANDS (+28 more)

### Community 108 - "RolesPage.tsx"
Cohesion: 0.11
Nodes (15): Role, RolesPage, describeError(), GROUP_STYLE, LEGEND_STYLE, OPTION_STYLE, PermissionSpec, roleAllows() (+7 more)

### Community 109 - "Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)"
Cohesion: 0.25
Nodes (9): API keys (X-API-Key, nxo_..., scope intersection), First boot sequence (api entrypoint migrates, compose never seeds), Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test), Makefile workflows (up/test/lint/typecheck/migrate/seed), HIGH finding: API-key scope bypass for superadmin-owned keys (fixed: scope intersection first), Security audit 2026-09 (26 raw findings -> 20 confirmed, all fixed), HIGH finding: known seed superadmin + API key backdoor (fixed: NEXUSOPS_ALLOW_SEED opt-in, one-time password), Threat model (edge attacker, malicious agent, curious operator, leaked token, SSRF) (+1 more)

### Community 111 - "create_organization"
Cohesion: 0.16
Nodes (23): add_member(), create_organization(), get_organization(), membership_for_user(), AsyncSession, Membership, Organization, Request (+15 more)

### Community 112 - "main.py"
Cohesion: 0.11
Nodes (26): fail_on_bad_config(), Central configuration. All runtime configuration flows through this module so…, Exit immediately with a readable message if configuration is invalid. Also…, close_redis(), create_app(), _include_routers(), lifespan(), FastAPI (+18 more)

### Community 113 - "schemas/health.py"
Cohesion: 0.29
Nodes (6): HealthOut, Health / readiness schemas., Liveness body — always 200 while the process can serve at all., Readiness body; 503 with the failing components when not ready., ReadyComponents, ReadyOut

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "get_redis"
Cohesion: 0.15
Nodes (18): liveness(), get, Response, Health probes: liveness (always cheap) and readiness (checks dependencies).…, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness(), get_redis() (+10 more)

### Community 116 - "test_tenancy_allowlist.py"
Cohesion: 0.20
Nodes (14): AST, _actual_callers(), _calls_system_scope(), _module_path(), Path, The system-scope allowlist is the only fence around the tenancy carve-out.…, Every module that could open a system scope: ``app/`` plus the scripts., No module may lift tenant isolation without being named in the list. (+6 more)

### Community 117 - "_monitor"
Cohesion: 0.26
Nodes (15): Deterministic fake checker for ``sim://`` monitors and demo environments.…, SimulatedTransport, _check(), FakeClock, _monitor(), parametrize, Stands in for time.time() so sim buckets are fully deterministic., test_always_down_carries_error_text() (+7 more)

### Community 118 - "dependencies"
Cohesion: 0.33
Nodes (6): dependencies, lucide-react, react, react-dom, react-router-dom, @tanstack/react-query

### Community 119 - "DeploymentDetailPage.test.tsx"
Cohesion: 0.13
Nodes (9): ACTIVE_MEMBERSHIP, ApiError, deploymentDetail(), EMPTY_LOGS, FakeWebSocket, get, ME, post (+1 more)

### Community 120 - "generate_secrets.sh"
Cohesion: 0.47
Nodes (3): existing_real_keys(), replace_or_append(), generate_secrets.sh script

### Community 121 - "ServerOut"
Cohesion: 0.28
Nodes (6): computed_field, Whether the node has reported capabilities at all (v2 hello)., Full server view with recent timeline events and container counts., Server as listed in collections. Never exposes the agent token hash., ServerDetail, ServerOut

### Community 122 - "server_payload"
Cohesion: 0.08
Nodes (31): A valid POST /servers body with per-test overrides., server_payload(), test_token_cannot_claim_a_foreign_tenants_node(), test_v1_heartbeat_keeps_the_204_contract(), Regression: a superadmin-owned key is still limited to its scope list. The…, test_scoped_api_key_cannot_exceed_its_grant(), _create_server(), Server CRUD, cascade delete, audit trail rows and audit immutability. (+23 more)

### Community 123 - "test_migration_phase22.py"
Cohesion: 0.28
Nodes (8): UUID, Phase 2.2 — the environment-type correction follows the documented precedence.…, Only the previous migration's ``PROD`` output is corrected. A row already…, Create one legacy (application-scoped) environment per case., Every branch of the slug-first rule, end to end through ``head``., _seed_legacy(), test_correction_preserves_operator_set_values(), test_recognised_slug_alias_wins_over_a_conflicting_name()

### Community 124 - "middleware.py"
Cohesion: 0.15
Nodes (14): ASGIApp, AccessLogMiddleware, Request, Response, HTTP middleware: request ids, security headers, structured access logs., Baseline hardening headers on every API response., RequestIDMiddleware, SecurityHeadersMiddleware (+6 more)

### Community 125 - "_run_docker_action"
Cohesion: 0.18
Nodes (15): _demux_docker_stream(), _docker_error(), execute_operation(), OperationError, Exception, A stable, sanitized failure contract for the control plane., Re-validate the operation's parameters locally, against a closed shape., Make control characters safe and bound the result. Never touches container… (+7 more)

### Community 126 - "list_operations"
Cohesion: 0.17
Nodes (18): cancel_operation(), create_operation(), get_operation(), list_operations(), DbDep, Depends, get, post (+10 more)

### Community 127 - "v1/audit.py"
Cohesion: 0.11
Nodes (20): list_audit_logs(), datetime, DbSession, Depends, get, PageParamsDep, Audit log API. Strictly read-only: the table is append-only by design., Newest-first audit trail with optional filters. No write routes exist for this… (+12 more)

### Community 137 - "ContainerListPage.tsx"
Cohesion: 0.16
Nodes (11): ContainerListPage, ContainerListPage(), ContainerRef, formatCpu(), formatMemory(), formatUtc(), SORT_OPTIONS, STATUS_OPTIONS (+3 more)

### Community 146 - "test_auth_multi_org.py"
Cohesion: 0.24
Nodes (17): _latest_audit(), _latest_event(), _list_ids(), Any, UUID, Phase 3.1 — pre-organization auth events are instance-level and tenant-…, No account => no actor => a system instance-level row, as before., A NULL-org auth fact is not reachable through either organization. (+9 more)

### Community 147 - "20260922_1000-a3f1c8d24b6e_add_tenancy_foundation.py"
Cohesion: 0.22
Nodes (11): _app_role_credentials(), _assert_fully_backfilled(), _backfill_org_ids(), _drop_constraint(), add tenancy foundation Phase 1 of the platform roadmap: organizations,…, Carry a value into a PL/pgSQL block. ``CREATE ROLE``/``ALTER ROLE`` are utility…, Application role name/password from settings (never hard-coded)., Point every pre-existing row at the bootstrap organization. ``audit_logs`` is… (+3 more)

### Community 148 - "postgres service (PostgreSQL 17, loopback :5433)"
Cohesion: 0.29
Nodes (7): postgres service (PostgreSQL 17, loopback :5433), Fernet encryption at rest (ENCRYPTION_KEY, write-once), Backups (pgdata volume, nightly pg_dump, ephemeral Redis), Required secrets (POSTGRES_PASSWORD, JWT_SECRET >= 32 chars, ENCRYPTION_KEY Fernet), Production hardening checklist (secrets, ENVIRONMENT, no seed, TLS, rotation), Compose vs host network namespaces (postgres:5432 vs 127.0.0.1:5433), Simulation mode (SIMULATION_MODE)

### Community 149 - "phase3.spec.ts"
Cohesion: 0.13
Nodes (13): 5. ProxyProvider interface, 2.3 Capabilities (implemented, Phase 3), frontend_e2e_fixtures_expect, AGENT, docker(), NodeDetail, OperationRow, REPO_ROOT (+5 more)

### Community 150 - "nexusops-understand.mjs"
Cohesion: 0.33
Nodes (5): COMMON, meta, out, READERS, SCHEMA

### Community 151 - "Invisible account lockout (5 fails -> 15 min, enumeration resistance)"
Cohesion: 0.33
Nodes (6): Invisible account lockout (5 fails -> 15 min, enumeration resistance), Unified error envelope (code, message, request_id), Per-IP rate limiting (Redis fixed window), Request lifecycle (edge -> middleware -> rate limit -> deps -> router), Client IP resolution (resolve_client_ip, TRUSTED_PROXY_CIDRS, XFF overwrite), EmailStr rejects reserved domains (login 422 on .test/.local/.arpa)

### Community 152 - "_raw_probe"
Cohesion: 0.20
Nodes (10): _app_role_dsn(), A libpq DSN for the RLS-enforced application role (no ORM, no guard)., Run one statement as ``nexusops_app`` with an explicit GUC. Parameterized like…, Raw SQL as the application role: the policies alone return nothing. Written…, Adding ``org_id`` to ``audit_logs`` must not have opened a way to edit it. The…, ``WITH CHECK`` is not decoration: an unlucky INSERT cannot cross tenants., _raw_probe(), test_audit_trail_is_still_append_only_after_tenancy() (+2 more)

### Community 153 - "_docker_request"
Cohesion: 0.18
Nodes (9): collect_container_stats(), collect_containers(), _container_status(), _docker_raw(), _docker_request(), One raw Docker API call; returns ``(status, body_bytes)``., Best-effort container list; empty when no docker socket is present., One-shot docker stats for running containers, CPU diffed across cycles.… (+1 more)

### Community 154 - "nexusops-draft.mjs"
Cohesion: 0.40
Nodes (4): DOCS, meta, SPINE, VERIFY_RULES

### Community 155 - "notification_sender.py"
Cohesion: 0.19
Nodes (13): NotificationError, BaseException, Exception, Low-level notification transports: SMTP email and outgoing webhooks. These…, Raised when a delivery attempt fails. Message is safe to persist., Bounded, single-line, content-free error reason., Send a plain-text email via SMTP. Raises :class:`NotificationError`. The…, _safe_reason() (+5 more)

### Community 156 - "nexusops-challenge.mjs"
Cohesion: 0.33
Nodes (5): CHALLENGE_COMMON, meta, RESEARCH_COMMON, SCHEMA, TASKS

### Community 157 - "test_agent_ingestion.py"
Cohesion: 0.30
Nodes (10): _enrolled(), _heartbeat(), Agent ingest pipeline: hello, heartbeat, staleness transitions, events., A container absent from a later heartbeat is gone from the daemon., A payload at the agent's cap may be truncated — absence proves nothing., test_heartbeat_at_container_cap_skips_reconciliation(), test_heartbeat_removes_vanished_containers(), test_heartbeat_updates_status_metrics_and_containers() (+2 more)

### Community 158 - "test_schemas_agent.py"
Cohesion: 0.07
Nodes (52): AgentContainerIn, AgentHeartbeatIn, AgentHelloIn, Any, field_validator, Observed container state reported by an agent., Periodic metrics + observed containers from an enrolled agent. Network counters…, First contact from an agent after enrollment; fills static host facts. (+44 more)

### Community 159 - "test_run_async_publishes_frames_scheduled_by_the_commit_hook"
Cohesion: 0.29
Nodes (5): _FakeDb, Stands in for an ``AsyncSession`` whose only job here is ``sync_session``. A…, The shape of a worker task whose last statement is a commit., test_run_async_publishes_frames_scheduled_by_the_commit_hook(), commit_then_return()

### Community 160 - "main"
Cohesion: 0.20
Nodes (10): _interruptible_sleep(), main(), persist_token(), _process_pending_operations(), Atomically store *token* at 0600. Temp file in the same directory + fsync +…, Sleep in short slices so SIGTERM/SIGINT stop the agent promptly., Print the revoked-state notice once per entry; return True thereafter., Claim, execute and report operations — strictly one at a time. (+2 more)

### Community 161 - "test_monitor_transport.py"
Cohesion: 0.21
Nodes (10): BaseException, Flatten an exception into a bounded single-line string. The request URL is…, _sanitize_error(), _strip_query(), clock(), fixture, Unit tests for monitor check transports (simulated + URL hygiene helpers)., test_sanitize_error_flattens_and_bounds() (+2 more)

### Community 162 - "test_notifications.py"
Cohesion: 0.39
Nodes (8): _channel(), _delivery(), UUID, Notification channel + delivery-log endpoints. Regression coverage for GET…, The same event frame consumed twice queues ONE delivery per channel. Every API…, test_dispatch_frame_is_idempotent_across_workers(), test_list_deliveries_filters_by_channel(), test_list_deliveries_serializes_rows()

### Community 163 - "redact_mapping"
Cohesion: 0.22
Nodes (13): _is_sensitive_key(), Substring match on a normalised key so header-style names are caught too.…, Return a copy of *data* with sensitive values replaced. Used by audit metadata…, redact_mapping(), parametrize, Unit tests for app.core.logging redaction (pure functions only)., test_case_insensitive_substring_match(), test_flat_sensitive_keys_redacted() (+5 more)

### Community 164 - "AgentClient"
Cohesion: 0.25
Nodes (5): AgentClient, A verifying TLS context. Verification is never disabled. A private/self-hosted…, Refuse to send credentials over plain HTTP to a non-loopback server. The…, _tls_context(), SSLContext

### Community 165 - "build_heartbeat"
Cohesion: 0.20
Nodes (10): build_heartbeat(), cpu_percent_since(), disk_stats(), load1(), memory_stats(), Return (used_gb, used_percent)., Return (busy, total) jiffies from /proc/stat., Return (used_mb, used_percent) from /proc/meminfo. (+2 more)

### Community 166 - "celery_app.py"
Cohesion: 0.20
Nodes (8): Celery application: periodic cadences live here, dynamic work is claimed…, task, Heartbeat sweeps: offline detection and recovery for servers., Flag silent servers OFFLINE, recover returning ones. Safe to overlap., sweep_servers(), _run(), celery, celery_schedules

### Community 167 - "resolve_auth"
Cohesion: 0.07
Nodes (36): _attach_organization(), get_current_user(), get_identity(), get_optional_user(), _load_organization(), _load_permissions(), membership_for_org(), _org_id_from_header() (+28 more)

### Community 168 - "simulation.py"
Cohesion: 0.31
Nodes (8): _containers_for(), task, Simulation mode: drive the seeded fleet so dashboards stay alive on a laptop.…, Deterministic smooth value in [base-amplitude, base+amplitude]., Stable per-server container set; one container cycles EXITED occasionally., simulation_tick(), _run(), _wave()

### Community 171 - "get_settings"
Cohesion: 0.09
Nodes (26): _quoted_list(), Add the operations framework table (node-agent-architecture.md §5). One tenant-…, upgrade(), downgrade(), _drop_constraint(), _quoted_list(), Phase 2 — projects & environments: env promotion, config, secret versions. This…, upgrade() (+18 more)

### Community 172 - "_FakeAsyncClient"
Cohesion: 0.22
Nodes (3): _FakeAsyncClient, _FakeRequestObj, Scripted httpx.AsyncClient: responses keyed by absolute request URL.

### Community 173 - "permissions.py"
Cohesion: 0.15
Nodes (10): PermissionSpec, Permission registry and role matrix. Permissions are *data*: the registry below…, Check an API-key scope list against a required permission. Supports exact match…, scope_matches(), parametrize, test_scope_matches_truth_table(), 1. Principles (already true in the codebase, kept), 5. API keys (+2 more)

### Community 174 - "logging.py"
Cohesion: 0.29
Nodes (7): configure_logging(), _orjson_dumps(), Any, Structured logging via structlog. Every log record carries timestamp, level,…, Configure structlog + stdlib logging once at process start. Everything…, structlog, sys

### Community 175 - "2. Entities"
Cohesion: 0.17
Nodes (11): Alias for :attr:`extra`, so the API can expose open-ended agent facts. The…, 2.1.1 ApiKey org binding detail, 2.2.1 Environment promotion detail — **shipped in Phase 2**, 2.2 Delivery (existing models, extended), 2.3 Infrastructure — Nodes, 2.4 Routing & TLS (new subsystem), 2.5 Secrets (re-scoped — **shipped in Phase 2**), 2.6 Observability (existing, org-scoped via parents) (+3 more)

### Community 176 - "DeploymentRunner"
Cohesion: 0.25
Nodes (6): DeploymentRunner, Protocol, Stream output lines for *step_name*; raise StepFailure to fail it., Adapter interface implemented by real (future) and simulated runners., Return the ordered step names for this run., 2. What survives unchanged

### Community 177 - "create_operation"
Cohesion: 0.16
Nodes (15): _bounded(), create_operation(), ensure_dispatchable(), ensure_node_can_run(), Any, Request, Queue one whitelisted action for one node in the caller's organization.…, Keep one agent report from becoming an unbounded row. The agent is… (+7 more)

### Community 178 - "network_rates"
Cohesion: 0.33
Nodes (6): build_facts(), network_rates(), network_total_bytes(), Sum rx/tx bytes over non-loopback interfaces from /proc/net/dev., Return (rx_kb_s, tx_kb_s) or ``(None, None)`` when not measurable., Open-ended host facts, stored in the node's flexible JSONB blob. Deliberately…

### Community 179 - "test_migration_phase21.py"
Cohesion: 0.29
Nodes (7): Phase 2.1 corrective migration: legacy ``environment_type`` classification.…, Every case is classified as documented, ids and ownership intact., The correction is part of ``head`` and adds no extra Alembic head., Insert one legacy environment per case, in two organizations., _seed_typed_environments(), test_corrective_migration_is_reachable_from_head(), test_corrects_legacy_environment_types()

### Community 180 - "websocket_endpoint"
Cohesion: 0.67
Nodes (3): websocket, Hand the socket to the hub (auth handshake handled there)., websocket_endpoint()

### Community 181 - "get_transport"
Cohesion: 0.33
Nodes (6): get_transport(), MonitorTransport, Protocol, Pick the transport matching the monitor URL scheme., Anything that can execute a check for a monitor., test_get_transport_selects_by_scheme()

### Community 182 - "require_permission"
Cohesion: 0.21
Nodes (10): permission_dep(), Any, Dependency factory enforcing a permission; returns 403 when denied., require_permission(), _check(), Forbidden, _FakeCtx, Duck-typed stand-in for AuthContext. (+2 more)

### Community 183 - "8. Upstream binding and re-render triggers"
Cohesion: 0.33
Nodes (6): 8.1 Binding rules, 8.2 Certificate selection rule (this doc owns it), 8.3 Re-render triggers, 8.4 Drift, 8.5 How deployments hook routing (post-deploy route sync), 8. Upstream binding and re-render triggers

### Community 184 - "_entity_exists"
Cohesion: 0.40
Nodes (6): _entity_exists(), Whether *id_* exists **for this organization**. Runs inside the socket's…, The hub's subscribe-time existence check under concurrent orgs.…, test_websocket_entity_checks_stay_inside_their_socket_org(), check(), 5. WebSockets

### Community 185 - "coerce_headers"
Cohesion: 0.40
Nodes (5): coerce_headers(), Any, Normalise arbitrary JSON-ish header input into a plain str->str dict., Any, test_coerce_headers()

### Community 186 - "maintenance.py"
Cohesion: 0.13
Nodes (21): aggregate_metrics(), _run(), _collect_logs(), expire_operations(), expire_sessions(), _run(), task, Housekeeping: metric rollups, log trims, notification retries, session expiry. (+13 more)

### Community 187 - "Conflict"
Cohesion: 0.19
Nodes (19): Conflict, create_role(), delete_role(), get_role(), list_roles(), AsyncSession, Request, Role (+11 more)

### Community 188 - "instant_pacing"
Cohesion: 0.40
Nodes (4): instant_pacing(), fixture, MonkeyPatch, Remove the per-line sleeps; pacing bounds are asserted separately.

### Community 189 - "servers.py"
Cohesion: 0.14
Nodes (26): create_enrollment_token(), create_server(), _enrollment_created(), _enrollment_out(), get_server(), list_enrollment_tokens(), list_servers(), list_tags() (+18 more)

### Community 190 - "EnvironmentUpdate"
Cohesion: 0.14
Nodes (14): EnvironmentBase, EnvironmentCreate, EnvironmentUpdate, _normalise_environment_type(), field_validator, Shared environment fields., Payload to create an environment under a project., Partial environment update; omitted fields are left untouched. Config is… (+6 more)

### Community 191 - "permissions_for_role"
Cohesion: 0.40
Nodes (5): effective_permissions(), permissions_for_role(), User, Sorted permission codenames a role grants; ``*`` expands to the registry.…, Instance-level permissions for a user (legacy default-role view). Deliberately…

### Community 192 - "list_servers"
Cohesion: 0.40
Nodes (5): list_servers(), _order_clause(), ColumnElement, Filter + paginate servers. Returns ``(rows, total)``., Translate ``name`` / ``-created_at`` style sort keys to ORDER BY.

### Community 193 - "pytest"
Cohesion: 0.15
Nodes (11): alembic_autogenerate, alembic_migration, created_at server defaults must evaluate per insert, not at table creation., Regression: system_events and audit_logs shipped with DEFAULT 'now()' (quoted…, test_audit_and_event_created_at_defaults_are_dynamic(), Model / migration drift: the schema in the database must match the models.…, ``Base.metadata`` and the migrated database must describe the same schema., The DB whitelist and ``OperationType`` are the same closed set. The migration… (+3 more)

### Community 194 - "upsert_tag"
Cohesion: 0.40
Nodes (5): list_tags_with_usage(), All tags ordered by name with their server usage counts., Create a tag or update its colour; names are matched exactly., upsert_tag(), Tag

### Community 195 - "NexusOps — Phase 1 (Multi-Tenancy) Report"
Cohesion: 0.40
Nodes (5): 1. What Phase 1 delivered, 2. Migrations (4, single head), 5. Tests, 8. Position, NexusOps — Phase 1 (Multi-Tenancy) Report

### Community 196 - "_pace"
Cohesion: 0.67
Nodes (3): _pace(), Deterministic per-line delay between 0.05s and 0.35s., test_pace_bounds()

## Knowledge Gaps
- **425 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+420 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1956 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `6. Tooling: reproducible e2e` connect `sweep_session` to `run_async`, `NexusOps — Phase 1 (Multi-Tenancy) Report`, `deps.py`, `client.ts`, `create_operation`, `_entity_exists`, `login`?**
  _High betweenness centrality (0.199) - this node is a cross-community bridge._
- **Why does `useEventStream()` connect `client.ts` to `apiGet`, `App.tsx`, `@tanstack/react-query`, `ServerDetailPage.tsx`, `sweep_session`?**
  _High betweenness centrality (0.198) - this node is a cross-community bridge._
- **Why does `TenancyScopeError` connect `deps.py` to `AuthContext`, `test_tenant_isolation.py`, `resolve_auth`, `test_operations.py`, `publish`, `NotFound`, `log_service.py`, `sweep_session`, `test_tenant_concurrency.py`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Are the 82 inferred relationships involving `AuthContext` (e.g. with `TenancyScopeError` and `MembershipStatus`) actually correct?**
  _`AuthContext` has 82 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `APIModel` (e.g. with `OperationSpec` and `test_specs_reject_unknown_params()`) actually correct?**
  _`APIModel` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `apiGet()` (e.g. with `ContainerDetailPage.test.tsx` and `mockApi()`) actually correct?**
  _`apiGet()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `meta`, `SCHEMA`, `RESEARCH_COMMON` to the rest of the system?**
  _425 weakly-connected nodes found - possible documentation gaps or missing edges._