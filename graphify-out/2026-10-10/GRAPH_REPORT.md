# Graph Report - nexusops  (2026-10-10)

## Corpus Check
- 324 files · ~305,462 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: (none) 8, .example 1, .service 1)

## Summary
- 4831 nodes · 14090 edges · 208 communities (183 shown, 25 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1125 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e57dada9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- apiGet
- project_service.py
- @tanstack/react-query
- App.tsx
- test_operation_registry.py
- AlertsPage.tsx
- resolve_client_ip
- useToast
- react
- test_agent_v2.py
- test_operations.py
- types.ts
- APIModel
- client.ts
- projects.py
- models/__init__.py
- deployment_engine.py
- SimulatedDockerProvider
- EnrollmentToken
- v1/secrets.py
- test_deployments_simulated.py
- list_containers
- MetricGranularity
- test_security.py
- Domain Routing — NexusOps
- monitor_service.py
- Node & Agent Architecture
- test_agent_backoff.py
- SimulatedDeploymentRunner
- nexusops_agent.py
- get_sessionmaker
- auth_service.py
- docker_host_service.py
- test_rate_limit.py
- docker_hosts.py
- test_ws_hub.py
- monitors.py
- v1/search.py
- Server
- list_deliveries
- DockerProvider
- test_monitor_transport.py
- Deployment Architecture — NexusOps (target state)
- toast.tsx
- docker_real.py
- test_permissions.py
- events.py
- test_phase3_nodes.py
- test_ssrf.py
- NotFound
- update_role
- update_server
- apikey.py
- test_migration_phase2.py
- v1/auth.py
- test_auth_journey.py
- sweep_session
- collections_abc
- dispatch_event_frame
- test_tenant_isolation.py
- compilerOptions
- _list_deployments
- test_error_logging.py
- update_organization
- test_phase2_environments.py
- OutModel
- test_schema_redaction.py
- containers.py
- digest_of
- package.json
- test_event_registry.py
- test_secrets.py
- enums.py
- seed.py
- api service (FastAPI / uvicorn :8000)
- core/tenancy.py
- AsyncSession
- DockerProviderError
- incident_service.py
- test_phase2_secrets.py
- AuthContext.tsx
- AuthContext
- .from_user
- tests/conftest.py
- test_agent_contract.py
- user_service.py
- devDependencies
- operation_service.py
- LogLine
- Settings
- container.py
- validate_config
- ApiKeysPage.tsx
- apply_scope_to_session
- test_phase21_secret_version_integrity.py
- alert_service.py
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- journey.spec.ts
- run_async
- big_serial_pk
- README.md - NexusOps overview
- env.py
- system_scope
- apiPost
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- DashboardPage.tsx
- RolesPage.tsx
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- ScopedSession
- create_organization
- pytest
- schemas/health.py
- scripts
- server_service.py
- test_tenancy_allowlist.py
- Multi-Tenancy Architecture
- dependencies
- DeploymentDetailPage.test.tsx
- generate_secrets.sh
- server.py
- server_payload
- test_migration_phase22.py
- main.py
- _run_docker_action
- list_operations
- list_audit_logs
- install.sh
- docker-entrypoint.sh
- integration/__init__.py
- list_sessions
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
- register_exception_handlers
- NotificationChannel
- redact_mapping
- AgentClient
- deployment.py
- _enforce
- resolve_auth
- ._check_status
- .__tablename__
- list_enrollment_tokens
- get_meta
- Domain Model — NexusOps as a Multi-Tenant Platform
- scope_matches
- Authorization Architecture
- 2. Entities
- permissions.py
- record_result
- network_rates
- 20261009_1100-d4e5f6a7b8c9_correct_legacy_environment_types.py
- router.py
- docker_sim.py
- _FakeCtx
- 8. Upstream binding and re-render triggers
- EnrollmentTokenCreated
- AgentContainerIn
- maintenance.py
- EventLevel
- instant_pacing
- list_servers
- EnvironmentUpdate
- test_rbac.py
- ContainerInfo
- test_migration_drift.py
- _memory_count_and_ttl
- 4. Operations framework (added in this pass)
- docker_capability
- create_operation
- sweep_deployments
- 6. Agent security
- _transport_is_https
- delete_server
- .__init__
- .register_container
- ._shallow_validate
- 6. Config rendering — strict allowlists
- .register_log_rows
- severity_for_event

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

## Communities (208 total, 25 thin omitted)

### Community 0 - "apiGet"
Cohesion: 0.05
Nodes (30): apiGet(), ProjectOut, ProjectListPage, Command, CommandPalette(), CommandPaletteProps, STATIC_COMMANDS, Layout() (+22 more)

### Community 1 - "project_service.py"
Cohesion: 0.10
Nodes (55): Application, DeploymentEnvironment, A **project-scoped** deployment environment (Phase 2 promotion). The…, ApplicationUpdate, Partial application update; omitted fields are left untouched., EnvironmentCreate, Payload to create an environment under a project., ProjectCreate (+47 more)

### Community 2 - "@tanstack/react-query"
Cohesion: 0.05
Nodes (61): AuditEntry, DeploymentOut, Page, SessionInfo, ContainerListPage, DeploymentListPage, EventsPage, IncidentListPage (+53 more)

### Community 3 - "App.tsx"
Cohesion: 0.07
Nodes (39): DeploymentStepOut, IncidentEventOut, AuditLogPage, DeploymentDetailPage, EnvironmentDetailPage, IncidentDetailPage, LoginPage, LoginRoute() (+31 more)

### Community 4 - "test_operation_registry.py"
Cohesion: 0.13
Nodes (18): OperationType, The whitelist. Nothing outside this enum ships as an exec surface. Each type…, Any, Validate *params* against the type's model and return the stored form.…, validate_params(), MonkeyPatch, The operation dispatch whitelist is a contract, not a convention.…, The framework reuses existing codenames; a generic exec grant must not exist. (+10 more)

### Community 5 - "AlertsPage.tsx"
Cohesion: 0.11
Nodes (21): AlertOut, ChannelOut, DeliveryOut, AlertsPage, AlertsPage(), ChannelDialog(), DeleteChannelDialog(), describeError() (+13 more)

### Community 6 - "resolve_client_ip"
Cohesion: 0.20
Nodes (19): _parse_networks(), Request, Parse a comma-separated CIDR list; malformed entries are skipped., Real client address for *request* per the trust model above., resolve_client_ip(), make_request(), Request, Unit tests for the chained-proxy client-IP resolver (app/core/client_ip.py). (+11 more)

### Community 7 - "useToast"
Cohesion: 0.09
Nodes (42): apiDelete(), apiPatch(), ApplicationOut, ENVIRONMENT_TYPE_LABELS, EnvironmentDetailOut, EnvironmentOut, EnvironmentType, MonitorDetailPage (+34 more)

### Community 8 - "react"
Cohesion: 0.08
Nodes (27): DockerHostsPage, OrganizationRequiredPage, CheckboxField(), CheckboxFieldProps, FieldAria, FieldBaseProps, PasswordFieldProps, SearchInput() (+19 more)

### Community 9 - "test_agent_v2.py"
Cohesion: 0.07
Nodes (41): agent_fixture(), _load_agent(), Any, fixture, parametrize, Path, Agent protocol v2: honest metrics, capability detection, and the executor. The…, Trusting a private CA must not weaken verification. (+33 more)

### Community 10 - "test_operations.py"
Cohesion: 0.07
Nodes (54): expire_operations(), Expire node operations past their deadline — pending and claimed alike. A…, assert_error_code(), Assert envelope shape + code; returns the inner error object., _dispatch(), _dispatch_body(), _enrolled_node(), _mutate_in_system_scope() (+46 more)

### Community 11 - "types.ts"
Cohesion: 0.05
Nodes (59): CapabilityReport, ContainerOut, DeploymentLogLine, DeploymentStatus, EnrollmentTokenCreated, EnrollmentTokenItem, EnrollmentTokenState, MetricPoint (+51 more)

### Community 12 - "APIModel"
Cohesion: 0.06
Nodes (46): CapabilityReport, One node-reported capability. ``present`` defaults to false, and a capability…, Schemas for the read-only audit log API. The audit table is append-only; these…, APIModel, BaseModel, Shared Pydantic v2 base schemas., Base for request/response models: ORM mode + strict-ish population., Operator-facing schemas for organization-scoped enrollment tokens. The raw… (+38 more)

### Community 13 - "client.ts"
Cohesion: 0.06
Nodes (42): API_BASE, ApiError, apiRequest(), buildUrl(), extractError(), getAccessToken(), getActiveOrgId(), onActiveOrgChange() (+34 more)

### Community 14 - "projects.py"
Cohesion: 0.11
Nodes (49): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+41 more)

### Community 15 - "models/__init__.py"
Cohesion: 0.08
Nodes (60): _org_scoped_classes(), Mapped classes marked :class:`~app.models.base.OrgScoped`. Reads the mapper…, Base, json_column(), OrgScoped, datetime, Declarative base, shared mixins and column helpers., Base for all ORM models with stable constraint naming for Alembic. (+52 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.10
Nodes (60): deployment_log_channel(), Deployment, DeploymentStep, AlertSeverity, DeploymentStatus, LogSource, String enum; member names equal values so name/value storage never disagrees., StepStatus (+52 more)

### Community 17 - "SimulatedDockerProvider"
Cohesion: 0.11
Nodes (25): ContainerStatus, Plausible numbers derived from the row plus time-based sine noise., Implements :class:`DockerProvider` semantics against DB rows., SimulatedDockerProvider, _log_entry(), datetime, Unit tests for the simulated docker provider (in-memory rows, no docker)., _row() (+17 more)

### Community 18 - "EnrollmentToken"
Cohesion: 0.15
Nodes (19): EnrollmentToken, One single-use credential that enrolls (or claims) exactly one node., Whether the row could still be redeemed (not a race-safe check)., _claim_and_consume(), enroll(), get_token(), list_tokens(), AsyncSession (+11 more)

### Community 19 - "v1/secrets.py"
Cohesion: 0.06
Nodes (53): create_secret(), delete_secret(), get_secret(), list_secret_versions(), list_secrets(), DbSession, delete, get (+45 more)

### Community 20 - "test_deployments_simulated.py"
Cohesion: 0.15
Nodes (27): execute_deployment(), Run one deployment to a terminal state. Never raises; safe to re-run., _as_worker(), _delivery_chain(), _owner_ctx(), _queue(), _queued_with_recorder(), Deployment engine over the simulated runner: success, failure, rollback. (+19 more)

### Community 21 - "list_containers"
Cohesion: 0.09
Nodes (39): _action_route(), _endpoint(), _ev(), get_container(), _like_pattern(), list_container_logs(), list_containers(), _load_container() (+31 more)

### Community 22 - "MetricGranularity"
Cohesion: 0.08
Nodes (39): get_dashboard_summary(), get_latest_server_metrics(), get_server_metrics(), CurrentUser, DbDep, Depends, get, UUID (+31 more)

### Community 23 - "test_security.py"
Cohesion: 0.08
Nodes (49): argon2, argon2_exceptions, Unauthorized, create_access_token(), decode_access_token(), decrypt_str(), _fernet(), generate_api_key() (+41 more)

### Community 24 - "Domain Routing — NexusOps"
Cohesion: 0.11
Nodes (19): 10. Wildcards and catch-all, 11. User journey, 12. API surface, permissions, audit, 13. Monitoring tie-in, 1. Scope and current state, 2. Where nginx runs, 3.1 Domain, 3.2 Route (+11 more)

### Community 25 - "monitor_service.py"
Cohesion: 0.10
Nodes (49): AppError, BadRequest, Exception, Base class for expected, client-facing errors., assert_safe_url_async(), Async wrapper around :func:`assert_safe_url`; DNS runs off the loop., CheckResult, MonitorStatus (+41 more)

### Community 26 - "Node & Agent Architecture"
Cohesion: 0.12
Nodes (16): 1. Scope and stance, 3.2 Enrollment v2, 3.3 Token storage & rotation with dual-token grace, 3.4 Revocation semantics — fixing the 401 hot-loop, 3.5 Reconnect / offline states, 3. Agent lifecycle, 5.1 Model and lifecycle, 5.2 Whitelisted operation types (+8 more)

### Community 27 - "test_agent_backoff.py"
Cohesion: 0.16
Nodes (20): agent_fixture(), _install_sleep(), fake_sleep(), _load_agent(), _patch_host(), Any, fixture, MonkeyPatch (+12 more)

### Community 28 - "SimulatedDeploymentRunner"
Cohesion: 0.09
Nodes (47): LogLevel, _commit_short(), DeploymentRunner, _pace(), Exception, Protocol, Deployment runner port plus a faithful simulated implementation.…, Stream output lines for *step_name*; raise StepFailure to fail it. (+39 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.12
Nodes (19): build_heartbeat(), cpu_percent_since(), disk_stats(), load1(), memory_stats(), Return (used_gb, used_percent)., NexusOps host agent — protocol v2. Reports host metrics and Docker container…, Return (busy, total) jiffies from /proc/stat. (+11 more)

### Community 30 - "get_sessionmaker"
Cohesion: 0.11
Nodes (27): get_sessionmaker(), async_sessionmaker, AsyncSession, _admin_dsn(), client(), _ensure_database(), _migrated_database(), org_db() (+19 more)

### Community 31 - "auth_service.py"
Cohesion: 0.10
Nodes (51): active_memberships(), Membership, The user's memberships in non-suspended organizations, oldest first. Reads only…, System scope bound to *db*, for rows that have no organization. Used by exactly…, system_write_scope(), AuditResult, OrganizationStatus, UserStatus (+43 more)

### Community 32 - "docker_host_service.py"
Cohesion: 0.10
Nodes (38): ContainerHealth, DockerHostStatus, clip(), Provider abstraction for docker hosts (real daemon or simulated). Providers are…, Truncate *text* to *limit* characters, stripping control chars., describe_provider_error(), is_simulated(), provider_for() (+30 more)

### Community 33 - "test_rate_limit.py"
Cohesion: 0.36
Nodes (9): RateLimited, rate_limit(), Return a dependency enforcing *limit* requests per window per IP. With…, _FakeRequest, Unit tests for the Redis-backed rate limiter's failure modes. Regression…, test_auth_limiter_is_fail_closed(), test_fail_closed_fallback_is_per_ip(), test_fail_closed_limiter_still_limits_when_redis_down() (+1 more)

### Community 34 - "docker_hosts.py"
Cohesion: 0.05
Nodes (77): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+69 more)

### Community 35 - "test_ws_hub.py"
Cohesion: 0.06
Nodes (57): _authenticate_api_key(), _authenticate_jwt(), _bind_organization(), _close_socket(), Connection, _frame_org(), Hub, _load_permissions() (+49 more)

### Community 36 - "monitors.py"
Cohesion: 0.10
Nodes (45): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+37 more)

### Community 37 - "v1/search.py"
Cohesion: 0.13
Nodes (31): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+23 more)

### Community 38 - "Server"
Cohesion: 0.06
Nodes (52): agent_heartbeat(), agent_hello(), _presented_token(), Request, Response, First contact after enrollment: persist static host facts, negotiate cadence., Ingest one metrics sample and hand the agent its next work. A protocol-1 agent…, Resolve ``X-Agent-Token`` to the node it identifies, inside its own org. The… (+44 more)

### Community 39 - "list_deliveries"
Cohesion: 0.15
Nodes (23): create_channel(), delete_channel(), get_channel(), list_deliveries(), DbDep, delete, Depends, get (+15 more)

### Community 40 - "DockerProvider"
Cohesion: 0.10
Nodes (10): DockerProvider, Any, datetime, Protocol, List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``., List volumes: keys ``name``, ``driver``, ``mountpoint``., List networks: keys ``name``, ``driver``, ``scope``., Yield parsed log lines. With ``follow=True`` the stream never ends. (+2 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.06
Nodes (51): coerce_headers(), get_transport(), HTTPMonitorTransport, MonitorTransport, Any, BaseException, Protocol, Deterministic fake checker for ``sim://`` monitors and demo environments.… (+43 more)

### Community 42 - "Deployment Architecture — NexusOps (target state)"
Cohesion: 0.14
Nodes (14): 10. Events and WS during runs, 11. Post-deploy hooks, 12. Rollback semantics (existing behavior kept), 13. The simulated runner stays — labeled, 14. Open questions, 1. Current state — what is real and what is simulated, 3. Target pipeline, 4. Runner registry — the DI fix (+6 more)

### Community 43 - "toast.tsx"
Cohesion: 0.03
Nodes (70): CheckOut, DockerHostOut, IncidentOut, MonitorOut, App(), SimulatedChip(), mocks, Toast (+62 more)

### Community 44 - "docker_real.py"
Cohesion: 0.14
Nodes (21): ContainerStats, Point-in-time resource usage snapshot., _as_float(), _compute_stats(), _cpu_percent(), _network_bytes(), parse_log_line(), parse_rfc3339() (+13 more)

### Community 45 - "test_permissions.py"
Cohesion: 0.17
Nodes (9): _auth_context(), Unit tests for the permission registry, scope matching and RBAC gate., A fake context in the given organization. ``membership_status=None`` models a…, test_api_key_scope_intersects_role_permissions(), test_membership_is_required_for_authority(), test_plain_user_without_permissions_is_denied(), test_superadmin_bypasses_everything(), test_superadmin_owned_api_key_is_limited_to_its_scope() (+1 more)

### Community 46 - "events.py"
Cohesion: 0.19
Nodes (16): _decode_cursor(), _encode_cursor(), list_event_types(), list_events(), datetime, DbSession, Depends, get (+8 more)

### Community 47 - "test_phase3_nodes.py"
Cohesion: 0.15
Nodes (33): _create_token(), _dispatch(), _enroll(), _enrolled_node(), _load_agent_module(), _mutate_in_system_scope(), Phase 3 — Nodes & Agent v2 end-to-end behaviour. Grouped by the question each…, Import the shipped agent source (sync, so async tests never touch Path). (+25 more)

### Community 48 - "test_ssrf.py"
Cohesion: 0.05
Nodes (80): UnprocessableEntity, assert_safe_tcp_endpoint(), assert_safe_url(), _is_forbidden_address(), is_simulation_url(), ValueError, _raise_block(), Validate *url* for outbound requests; return the parsed URL or raise 422.… (+72 more)

### Community 49 - "NotFound"
Cohesion: 0.13
Nodes (38): NotFound, An encrypted configuration value, scoped to org, project or environment.…, Secret, _actor_type(), _collect_refs(), create_secret(), delete_secret(), _detail() (+30 more)

### Community 50 - "update_role"
Cohesion: 0.12
Nodes (23): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, delete, get (+15 more)

### Community 51 - "update_server"
Cohesion: 0.15
Nodes (19): create_enrollment_token(), create_server(), patch, post, Request, UUID, Create a tag or update its colour (idempotent on name)., Mint one single-use enrollment token in the caller's organization. The org… (+11 more)

### Community 52 - "apikey.py"
Cohesion: 0.14
Nodes (19): create_api_key(), list_api_keys(), CurrentUser, DbSessionDep, delete, get, post, Request (+11 more)

### Community 53 - "test_migration_phase2.py"
Cohesion: 0.09
Nodes (43): alembic_config, alembic_script, Phase 2.1 corrective migration: legacy ``environment_type`` classification.…, Every case is classified as documented, ids and ownership intact., An explicit non-DEV classification survives the corrective migration. The…, The correction is part of ``head`` and adds no extra Alembic head., Insert one legacy environment per case, in two organizations., _seed_typed_environments() (+35 more)

### Community 54 - "v1/auth.py"
Cohesion: 0.09
Nodes (48): change_password(), _clear_refresh_cookie(), _cookies_secure(), login(), logout(), me(), _optional_actor(), AsyncSession (+40 more)

### Community 55 - "test_auth_journey.py"
Cohesion: 0.09
Nodes (28): cookie_attributes(), Response, The raw Set-Cookie header carrying the refresh token., Extract just the opaque token from a Set-Cookie header., Parse Set-Cookie attributes (lowercased keys, empty string for flags)., refresh_cookie_header(), refresh_cookie_value(), _cookie_name() (+20 more)

### Community 56 - "sweep_session"
Cohesion: 0.09
Nodes (37): _run(), _run(), _run(), _run(), _collect_logs(), _run(), _run(), _run() (+29 more)

### Community 57 - "collections_abc"
Cohesion: 0.05
Nodes (29): alembic, downgrade(), rename ``server.*`` permission codenames to ``node.*`` The Node/Server…, _rename_permissions(), upgrade(), _quoted_list(), Add the operations framework table (node-agent-architecture.md §5). One tenant-…, upgrade() (+21 more)

### Community 58 - "dispatch_event_frame"
Cohesion: 0.10
Nodes (40): DeliveryStatus, _as_uuid(), _attempt_delivery(), _audit(), create_channel(), decode_delivery_cursor(), decrypt_channel_config(), delete_channel() (+32 more)

### Community 59 - "test_tenant_isolation.py"
Cohesion: 0.08
Nodes (45): bearer(), error_of(), login_account(), login_headers(), Any, AsyncClient, Pure helpers for journey tests: payloads, auth shortcuts, cookie parsing., Login and unpack tokens, the raw cookie header and the user object. (+37 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "_list_deployments"
Cohesion: 0.09
Nodes (39): _attribute_step_idx(), cancel_deployment(), _emails_for(), get_deployment(), list_application_deployments(), list_deployment_logs(), _list_deployments(), _parse_sort() (+31 more)

### Community 62 - "test_error_logging.py"
Cohesion: 0.22
Nodes (4): Regression: the catch-all 500 handler must not log raw exception text.…, _SpyLogger, test_unhandled_exception_handler_logs_class_not_message(), fastapi_testclient

### Community 63 - "update_organization"
Cohesion: 0.16
Nodes (14): create_organization(), list_my_organizations(), CurrentUser, DbSessionDep, get, IdentityUser, patch, post (+6 more)

### Community 64 - "test_phase2_environments.py"
Cohesion: 0.18
Nodes (22): _environment(), _project(), parametrize, Phase 2: project-scoped environments, config layering, and their isolation. The…, Uniqueness is ``(project_id, slug)`` — not instance-wide., The update path is validated too (the pre-Phase-2 gap)., Knowing an environment UUID is not access: the project link must hold., Another tenant cannot reach the project, its environments, or its detail. (+14 more)

### Community 65 - "OutModel"
Cohesion: 0.09
Nodes (26): ChannelType, AlertOut, BaseModel, Schemas for operator-facing alerts., UnreadCountOut, AuditOut, One audit trail entry (no write routes ever exist for this resource).…, OutModel (+18 more)

### Community 66 - "test_schema_redaction.py"
Cohesion: 0.18
Nodes (17): is_sensitive_header(), mask_sensitive_headers(), True when *name* looks like it carries a credential (Authorization etc.)., Return a copy of *headers* with sensitive values replaced by a mask., mask_target(), Human-readable masked target safe to expose over the API. For webhook families…, _monitor_out(), Outbound-schema redaction: monitor probe credentials and webhook targets.… (+9 more)

### Community 67 - "containers.py"
Cohesion: 0.08
Nodes (53): list_alerts(), mark_all_read(), mark_read(), CurrentUser, DbDep, Depends, get, post (+45 more)

### Community 68 - "digest_of"
Cohesion: 0.09
Nodes (23): digest_of(), Short server-verifiable digest used for change detection display. HMAC-SHA256…, test_digest_is_keyed_not_plain_sha256(), test_digest_length_and_determinism(), 10. Status/expiry tracking and monitor tie-in, 11. Failure handling, 12. Audit and events, 13. Non-goals (+15 more)

### Community 69 - "package.json"
Cohesion: 0.13
Nodes (15): name, private, type, version, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom (+7 more)

### Community 70 - "test_event_registry.py"
Cohesion: 0.21
Nodes (8): event_type_catalogue(), is_known_event_type(), Canonical registry of system-event types. Single source of truth shared by…, Return True when *event_type* is part of the canonical registry., Serialise the registry for the ``/events/types`` endpoint., Registry coherence: schema-advertised event types must equal the canonical…, test_catalogue_serialises_every_entry(), test_known_event_lookup()

### Community 71 - "test_secrets.py"
Cohesion: 0.10
Nodes (28): Exception, A ``${secret:KEY}`` reference could not be resolved. Fail-closed. Carries…, One successfully resolved reference: metadata for audit, no value., Outcome of resolving an environment's config references., Resolve every ``${secret:KEY}`` reference an environment's config names.…, resolve_secrets_for_environment(), ResolvedSecrets, SecretReference (+20 more)

### Community 72 - "enums.py"
Cohesion: 0.05
Nodes (73): _load_organization(), membership_for_org(), permission_dep(), Any, Organization, UUID, FastAPI dependencies: database session, authenticated tenant context, RBAC…, The user's active membership in *org_id*, if any. This single indexed read is… (+65 more)

### Community 73 - "seed.py"
Cohesion: 0.11
Nodes (33): encrypt_str(), generate_agent_token(), hash_token(), A per-node credential (``nxa_``): long-lived, node-scoped, never shared., Project, EnvironmentType, Kind of a project-scoped deployment environment (Phase 2). Descriptive only —…, ApiKey (+25 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "core/tenancy.py"
Cohesion: 0.08
Nodes (38): The active organization, or raise if this request has none., _apply_scope_guc(), current_org(), _desired_guc(), _guard(), _has_org_predicate(), install_tenancy_guards(), _mappers_of() (+30 more)

### Community 76 - "AsyncSession"
Cohesion: 0.10
Nodes (32): _detail(), AsyncSession, container_counts(), create_server(), get_server(), list_tags_with_usage(), _order_clause(), pending_rotation() (+24 more)

### Community 77 - "DockerProviderError"
Cohesion: 0.15
Nodes (10): DockerProviderError, Exception, A provider operation failed. ``str()`` is safe to show/log., Build a compact, secret-free description of a provider failure. Only the…, sanitize_error(), T, Execute an SDK call with one short retry, normalizing failures., Talks to a real docker daemon over ``unix://`` or ``tcp://``. (+2 more)

### Community 78 - "incident_service.py"
Cohesion: 0.10
Nodes (56): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+48 more)

### Community 79 - "test_phase2_secrets.py"
Cohesion: 0.19
Nodes (21): _env(), _project(), Phase 2 secrets: layered scope, immutable versions, rollback, isolation. Two…, Two racing rotations must both be kept and never share a version number., Another tenant cannot read, rotate, roll back or even enumerate the secret., The documented example: same key at three scopes; most specific wins., A ref declared in the project base config resolves for its environments., _resolved() (+13 more)

### Community 80 - "AuthContext.tsx"
Cohesion: 0.09
Nodes (24): setAccessToken(), setActiveOrgId(), Membership, User, AuthContext, AuthProvider(), AuthState, isOrgSelectionError() (+16 more)

### Community 81 - "AuthContext"
Cohesion: 0.07
Nodes (40): AuthContext, Resolved identity plus the organization this request acts in.…, create_api_key(), list_api_keys(), AsyncSession, Request, UUID, Live (non-revoked) keys owned by *owner_id*, newest first. (+32 more)

### Community 82 - ".from_user"
Cohesion: 0.11
Nodes (26): create_user(), deactivate_user(), get_user(), list_users(), CurrentUser, DbSessionDep, delete, get (+18 more)

### Community 83 - "tests/conftest.py"
Cohesion: 0.22
Nodes (7): configure_test_env(), Test bootstrap: pin every cached setting BEFORE the first ``app`` import. The…, KEY=VALUE pairs from the repo .env (first definition wins); never logged., Export the exact settings the app caches; host values cannot leak through., _read_dot_env(), os, pathlib

### Community 84 - "test_agent_contract.py"
Cohesion: 0.18
Nodes (16): agent_fixture(), _load_agent(), _patch_stats(), Any, fixture, MonkeyPatch, Contract tests: the shipped agent's payloads must satisfy the ingest schemas.…, One-shot docker stats reduce to cpu/mem/limit fields the schema accepts, with… (+8 more)

### Community 85 - "user_service.py"
Cohesion: 0.12
Nodes (40): MembershipStatus, _apply_deactivation(), _assert_not_last_active_member(), _assert_not_last_active_superadmin(), create_user(), deactivate_user(), get_by_email(), get_member() (+32 more)

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "operation_service.py"
Cohesion: 0.18
Nodes (25): OperationStatus, Lifecycle of one node operation (node-agent-architecture.md §5.1).…, Operation, One whitelisted action for one node, with a CAS lifecycle. ``attempts`` is…, _active_org(), cancel_operation(), claim_operation(), expire_one() (+17 more)

### Community 88 - "LogLine"
Cohesion: 0.10
Nodes (24): _decode_frame(), _max_log_id(), _poll_new_lines(), Parse a Redis pub/sub frame ``{ts, stream, message}`` into a LogLine., Highest persisted log id for a container (poll fallback watermark)., Fetch log rows persisted after ``last_seen['id']`` (poll fallback)., Live-tail a container's logs. Primary source is the Redis pub/sub channel…, stream_container_logs() (+16 more)

### Community 89 - "Settings"
Cohesion: 0.14
Nodes (6): field_validator, model_validator, Username from :attr:`database_url`, or ``None`` if it is unparseable., Validated application settings (loaded from environment / .env)., Settings, BaseSettings

### Community 90 - "container.py"
Cohesion: 0.21
Nodes (12): ContainerRemoveOut, host_ref(), HostRef, LogEntryOut, UUID, Container schemas: list/detail read models, log entries, action results., Summary of the docker host a container runs on., Summary of the server associated with a container. (+4 more)

### Community 91 - "validate_config"
Cohesion: 0.08
Nodes (31): field_validator, collect_secret_refs(), walk(), ConfigValidationError, effective_config(), merge_config(), Any, ValueError (+23 more)

### Community 92 - "ApiKeysPage.tsx"
Cohesion: 0.09
Nodes (20): ApiKeyOut, ApiKeysPage, ApiKeyCreatedOut, ApiKeysPage(), handleCopyKey(), copyText(), describeError(), EMPTY_FORM (+12 more)

### Community 93 - "apply_scope_to_session"
Cohesion: 0.09
Nodes (48): apply_scope_to_session(), current_scope(), org_scope(), ``'org'``, ``'system'`` or ``'unset'``., Run the enclosed block as a single organization. Nesting the *same* org is a…, Push the current scope onto *db*'s connection immediately. Needed only when a…, _entity_exists(), Whether *id_* exists **for this organization**. Runs inside the socket's… (+40 more)

### Community 94 - "test_phase21_secret_version_integrity.py"
Cohesion: 0.18
Nodes (18): _app_role_dsn(), _owner_dsn(), _probe(), Phase 2.1 — ``secret_versions`` is append-only in the **database**, not just in…, Immutability is a database guarantee, not merely a missing code path. The owner…, The legitimate append paths keep working under the guard., The documented deletion policy: purging a Secret cascades its history., RLS is preserved: another tenant cannot see a version row, even by id. (+10 more)

### Community 95 - "alert_service.py"
Cohesion: 0.33
Nodes (9): get_alert(), mark_all_read(), mark_read(), AsyncSession, UUID, Alert inbox: insert-only creation plus read/unread bookkeeping., Mark one alert read; raises :class:`NotFound` for unknown ids., Mark every unread alert read. Returns how many rows changed. (+1 more)

### Community 96 - "NexusOps (self-hosted infrastructure management and monitoring platform)"
Cohesion: 0.20
Nodes (10): mailpit service (dev SMTP sink + web UI :8025), NexusOps compose stack (8 services on one network), HIGH finding: redirect-following SSRF in uptime monitors (fixed: follow_redirects=False + per-hop guard), SSRF guard (assert_safe_url, per-redirect-hop validation, assert_safe_tcp_endpoint), Mailpit SMTP port internal-only (host-side injection needs extra mapping), Host port knobs (NEXUSOPS_HTTP_PORT/POSTGRES/REDIS/MAILPIT/VITE), SPA entry point (loads /src/main.tsx, dark color-scheme), Uptime monitors -> incidents -> notifications flow (+2 more)

### Community 97 - "REST API surface (/api/v1)"
Cohesion: 0.29
Nodes (7): Cursor (keyset) and offset pagination envelopes, Permission model (data-driven registry, require_permission, wildcard scopes), REST API surface (/api/v1), RBAC registry (PERMISSIONS + ROLE_MATRIX + scope_matches), Adding a new resource: 7-step checklist (model -> migration -> schemas -> service -> router -> tests -> frontend), Alembic migration workflow (autogenerate, models __init__ export, entrypoint apply), Command palette (Ctrl/Cmd+K)

### Community 98 - "journey.spec.ts"
Cohesion: 0.15
Nodes (15): EDGE, MAILPIT, ADMIN, Bootstrap, bootstrapVia(), test, ADMIN, formLogin() (+7 more)

### Community 99 - "run_async"
Cohesion: 0.13
Nodes (21): flush_pending_publishes(), Wait for frames scheduled by ``after_commit`` hooks to reach Redis. The commit…, T, Run *coroutine* on a dedicated event loop (Celery workers are sync). The loop…, run_async(), _drained(), _is_same_origin(), Browsers always send Origin on WS handshakes, even same-origin ones. When it… (+13 more)

### Community 100 - "big_serial_pk"
Cohesion: 0.33
Nodes (5): big_serial_pk(), UUID, Identity PK for very high-volume tables (metrics, logs)., declared_attr, Mapped

### Community 101 - "README.md - NexusOps overview"
Cohesion: 0.09
Nodes (41): docker-compose.dev.yml - dev overlay, docker-compose.docker-sock.yml - docker socket override, docker-compose.yml - full stack definition, docs/agent.md - agent guide, docs/api.md - API guide, Append-only audit log (Postgres BEFORE UPDATE OR DELETE trigger), docs/architecture.md - system architecture, docs/deployment.md - deployment and operations guide (+33 more)

### Community 102 - "env.py"
Cohesion: 0.24
Nodes (10): _database_url(), Alembic environment: metadata comes from app.models, URL from app settings., Migrations run as the table **owner**, never as the application role. The owner…, Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online(), Owner-role DSN for Alembic and the container entrypoint. Migrations… (+2 more)

### Community 103 - "system_scope"
Cohesion: 0.07
Nodes (31): Run the enclosed block with tenant filtering off (maintenance only). ``reason``…, system_scope(), task, Claim up to CLAIM_BATCH due monitors and execute each check.…, run_due_monitors(), make(), Loader criteria do not apply to DML — so the guard refuses instead. A silent…, One broadcast channel, two tenants: the frame's org decides who is told. (+23 more)

### Community 104 - "apiPost"
Cohesion: 0.13
Nodes (18): apiPost(), SecretRow, SecretsPage, errorMessage(), formatTimestamp(), RotateSecretValueForm(), SecretHistoryModal(), SecretScopeBadge() (+10 more)

### Community 105 - "redis service (Redis 7, no persistence, loopback :6390)"
Cohesion: 0.22
Nodes (11): redis service (Redis 7, no persistence, loopback :6390), WebSocket API (/api/v1/ws handshake, frames, limits), WebSocket channels (global, server-metrics, container-logs, deployment-logs, incidents), Deployment engine (queue_deployment / execute_deployment / sweeper backstop), Real-time spine: PostgreSQL system_events + Redis pub/sub, Rollback as a new deployment (rollback_of_id), WebSocket hub (framework-thin, Redis fan-in, per-socket queues), Test suites (pytest unit+integration, vitest, Playwright e2e) (+3 more)

### Community 106 - "NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)"
Cohesion: 0.18
Nodes (12): Agent security model (one-way telemetry, no command channel), Agent enrollment token (X-Agent-Token, nxa_..., SHA-256 at rest), Agent heartbeat exponential backoff (cap 5 min, exit 1 on revoked token), agent/install.sh (enrollment installer), Agent metrics collection (/proc statvfs Docker socket), NexusOps agent (stdlib-only Python, agent/nexusops_agent.py), Agent systemd hardening (ProtectSystem=strict, NoNewPrivileges), Agent ingest API (POST /agent/hello, POST /agent/heartbeat) (+4 more)

### Community 107 - "DashboardPage.tsx"
Cohesion: 0.11
Nodes (15): DashboardSummary, DashboardPage, LoadingBlock(), asFeedItem(), badgeLevel(), DashboardPage(), FeedItem, formatTimestamp() (+7 more)

### Community 108 - "RolesPage.tsx"
Cohesion: 0.11
Nodes (15): Role, RolesPage, describeError(), GROUP_STYLE, LEGEND_STYLE, OPTION_STYLE, PermissionSpec, roleAllows() (+7 more)

### Community 109 - "Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)"
Cohesion: 0.25
Nodes (9): API keys (X-API-Key, nxo_..., scope intersection), First boot sequence (api entrypoint migrates, compose never seeds), Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test), Makefile workflows (up/test/lint/typecheck/migrate/seed), HIGH finding: API-key scope bypass for superadmin-owned keys (fixed: scope intersection first), Security audit 2026-09 (26 raw findings -> 20 confirmed, all fixed), HIGH finding: known seed superadmin + API key backdoor (fixed: NEXUSOPS_ALLOW_SEED opt-in, one-time password), Threat model (edge attacker, malicious agent, curious operator, leaked token, SSRF) (+1 more)

### Community 111 - "create_organization"
Cohesion: 0.16
Nodes (23): add_member(), create_organization(), get_organization(), membership_for_user(), AsyncSession, Membership, Organization, Request (+15 more)

### Community 112 - "pytest"
Cohesion: 0.23
Nodes (12): created_at server defaults must evaluate per insert, not at table creation., Regression: system_events and audit_logs shipped with DEFAULT 'now()' (quoted…, test_audit_and_event_created_at_defaults_are_dynamic(), _app_for_environment(), MonkeyPatch, ENVIRONMENT gating contract: docs exposure and HSTS (see .env.example).…, create_app() with get_settings() patched to the given environment., test_non_production_does_not_emit_hsts() (+4 more)

### Community 113 - "schemas/health.py"
Cohesion: 0.18
Nodes (12): liveness(), get, Response, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness(), HealthOut, Health / readiness schemas. (+4 more)

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "server_service.py"
Cohesion: 0.05
Nodes (68): asyncio, Health probes: liveness (always cheap) and readiness (checks dependencies).…, container_log_channel(), Canonical Redis pub/sub channel names shared by API, workers and WS hub., server_metrics_channel(), _is_trusted(), Client-IP resolution behind chained reverse proxies. The API never takes TCP…, fail_on_bad_config() (+60 more)

### Community 116 - "test_tenancy_allowlist.py"
Cohesion: 0.20
Nodes (14): AST, _actual_callers(), _calls_system_scope(), _module_path(), Path, The system-scope allowlist is the only fence around the tenancy carve-out.…, Every module that could open a system scope: ``app/`` plus the scripts., No module may lift tenant isolation without being named in the list. (+6 more)

### Community 117 - "Multi-Tenancy Architecture"
Cohesion: 0.14
Nodes (12): Whether the runtime connection is the RLS-enforced application role. False…, 10. Migration (Phase 1), 1. Tenancy invariants, 2.1 Org creation — v1 decision, 2. Org resolution on every request, 3. The session guard (the mechanical layer), 4. Background jobs, 6. Agents (+4 more)

### Community 118 - "dependencies"
Cohesion: 0.33
Nodes (6): dependencies, lucide-react, react, react-dom, react-router-dom, @tanstack/react-query

### Community 119 - "DeploymentDetailPage.test.tsx"
Cohesion: 0.13
Nodes (9): ACTIVE_MEMBERSHIP, ApiError, deploymentDetail(), EMPTY_LOGS, FakeWebSocket, get, ME, post (+1 more)

### Community 120 - "generate_secrets.sh"
Cohesion: 0.47
Nodes (3): existing_real_keys(), replace_or_append(), generate_secrets.sh script

### Community 121 - "server.py"
Cohesion: 0.11
Nodes (17): _clean_tag_names(), DockerHostSummary, EnrollTokenOut, computed_field, Server API schemas: create/update payloads, list/detail outputs, enrollment., Whether the node has reported capabilities at all (v2 hello)., Compact system event projection for server timelines., Full server view with recent timeline events and container counts. (+9 more)

### Community 122 - "server_payload"
Cohesion: 0.10
Nodes (26): A valid POST /servers body with per-test overrides., server_payload(), test_token_cannot_claim_a_foreign_tenants_node(), test_v1_heartbeat_keeps_the_204_contract(), _create_server(), Server CRUD, cascade delete, audit trail rows and audit immutability., The HTTP listing path — schema serialization is exercised end-to-end. A…, ``/servers`` is a temporary alias for pre-rename clients. It must keep working… (+18 more)

### Community 123 - "test_migration_phase22.py"
Cohesion: 0.38
Nodes (6): UUID, Phase 2.2 — the environment-type correction follows the documented precedence.…, Create one legacy (application-scoped) environment per case., Every branch of the slug-first rule, end to end through ``head``., _seed_legacy(), test_recognised_slug_alias_wins_over_a_conflicting_name()

### Community 124 - "main.py"
Cohesion: 0.10
Nodes (26): ASGIApp, dispose_engine(), AccessLogMiddleware, Request, Response, HTTP middleware: request ids, security headers, structured access logs., Baseline hardening headers on every API response., RequestIDMiddleware (+18 more)

### Community 125 - "_run_docker_action"
Cohesion: 0.18
Nodes (15): _demux_docker_stream(), _docker_error(), execute_operation(), OperationError, Exception, A stable, sanitized failure contract for the control plane., Re-validate the operation's parameters locally, against a closed shape., Make control characters safe and bound the result. Never touches container… (+7 more)

### Community 126 - "list_operations"
Cohesion: 0.16
Nodes (20): cancel_operation(), create_operation(), get_operation(), list_operations(), DbDep, Depends, get, post (+12 more)

### Community 127 - "list_audit_logs"
Cohesion: 0.29
Nodes (7): list_audit_logs(), datetime, DbSession, Depends, get, PageParamsDep, Newest-first audit trail with optional filters. No write routes exist for this…

### Community 137 - "list_sessions"
Cohesion: 0.19
Nodes (12): list_sessions(), CurrentUser, DbSessionDep, delete, get, Request, UUID, Active sessions of this organization's members. Defaults to the caller's own;… (+4 more)

### Community 146 - "test_auth_multi_org.py"
Cohesion: 0.24
Nodes (17): _latest_audit(), _latest_event(), _list_ids(), Any, UUID, Phase 3.1 — pre-organization auth events are instance-level and tenant-…, No account => no actor => a system instance-level row, as before., A NULL-org auth fact is not reachable through either organization. (+9 more)

### Community 147 - "20260922_1000-a3f1c8d24b6e_add_tenancy_foundation.py"
Cohesion: 0.20
Nodes (12): _app_role_credentials(), _assert_fully_backfilled(), _backfill_org_ids(), _drop_constraint(), add tenancy foundation Phase 1 of the platform roadmap: organizations,…, Carry a value into a PL/pgSQL block. ``CREATE ROLE``/``ALTER ROLE`` are utility…, Application role name/password from settings (never hard-coded)., Point every pre-existing row at the bootstrap organization. ``audit_logs`` is… (+4 more)

### Community 148 - "postgres service (PostgreSQL 17, loopback :5433)"
Cohesion: 0.29
Nodes (7): postgres service (PostgreSQL 17, loopback :5433), Fernet encryption at rest (ENCRYPTION_KEY, write-once), Backups (pgdata volume, nightly pg_dump, ephemeral Redis), Required secrets (POSTGRES_PASSWORD, JWT_SECRET >= 32 chars, ENCRYPTION_KEY Fernet), Production hardening checklist (secrets, ENVIRONMENT, no seed, TLS, rotation), Compose vs host network namespaces (postgres:5432 vs 127.0.0.1:5433), Simulation mode (SIMULATION_MODE)

### Community 149 - "phase3.spec.ts"
Cohesion: 0.17
Nodes (10): frontend_e2e_fixtures_expect, AGENT, NodeDetail, OperationRow, REPO_ROOT, ref_node_child_process, ref_node_fs, ref_node_os (+2 more)

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
Cohesion: 0.17
Nodes (15): NotificationError, Any, BaseException, Exception, Low-level notification transports: SMTP email and outgoing webhooks. These…, POST *payload* as JSON to *url*; 2xx is success, anything else raises. Response…, Raised when a delivery attempt fails. Message is safe to persist., Bounded, single-line, content-free error reason. (+7 more)

### Community 156 - "nexusops-challenge.mjs"
Cohesion: 0.33
Nodes (5): CHALLENGE_COMMON, meta, RESEARCH_COMMON, SCHEMA, TASKS

### Community 157 - "test_agent_ingestion.py"
Cohesion: 0.30
Nodes (10): _enrolled(), _heartbeat(), Agent ingest pipeline: hello, heartbeat, staleness transitions, events., A container absent from a later heartbeat is gone from the daemon., A payload at the agent's cap may be truncated — absence proves nothing., test_heartbeat_at_container_cap_skips_reconciliation(), test_heartbeat_removes_vanished_containers(), test_heartbeat_updates_status_metrics_and_containers() (+2 more)

### Community 158 - "test_schemas_agent.py"
Cohesion: 0.15
Nodes (24): AgentHeartbeatIn, AgentHelloIn, Periodic metrics + observed containers from an enrolled agent. Network counters…, First contact from an agent after enrollment; fills static host facts., _heartbeat(), Unit tests for agent-facing schemas (heartbeat + container payloads)., An absent protocol version is the oldest contract, never v2., A capability report forbids unknown keys, so its shape is closed. (+16 more)

### Community 159 - "test_run_async_publishes_frames_scheduled_by_the_commit_hook"
Cohesion: 0.29
Nodes (5): _FakeDb, Stands in for an ``AsyncSession`` whose only job here is ``sync_session``. A…, The shape of a worker task whose last statement is a commit., test_run_async_publishes_frames_scheduled_by_the_commit_hook(), commit_then_return()

### Community 160 - "main"
Cohesion: 0.14
Nodes (15): _build_hello_payload(), _enroll(), _interruptible_sleep(), main(), memory_total_mb(), os_info(), persist_token(), _process_pending_operations() (+7 more)

### Community 161 - "register_exception_handlers"
Cohesion: 0.36
Nodes (8): _error_payload(), FastAPI, Request, register_exception_handlers(), handle_app_error(), handle_http_exception(), handle_unexpected(), handle_validation_error()

### Community 162 - "NotificationChannel"
Cohesion: 0.14
Nodes (21): NotificationChannel, NotificationDelivery, A delivery target (email address / webhook endpoint). ``config_ciphertext``…, SystemEvent, _create_monitor(), Monitor checks driving the full down -> incident -> recovery lifecycle., Regression: probe headers and URL query credentials never leave the API. Probe…, A monitor's checks, incidents and timeline all live in its organization, so the… (+13 more)

### Community 163 - "redact_mapping"
Cohesion: 0.22
Nodes (13): _is_sensitive_key(), Substring match on a normalised key so header-style names are caught too.…, Return a copy of *data* with sensitive values replaced. Used by audit metadata…, redact_mapping(), parametrize, Unit tests for app.core.logging redaction (pure functions only)., test_case_insensitive_substring_match(), test_flat_sensitive_keys_redacted() (+5 more)

### Community 164 - "AgentClient"
Cohesion: 0.25
Nodes (5): AgentClient, A verifying TLS context. Verification is never disabled. A private/self-hosted…, Refuse to send credentials over plain HTTP to a non-loopback server. The…, _tls_context(), SSLContext

### Community 165 - "deployment.py"
Cohesion: 0.15
Nodes (12): DeploymentApplicationRef, DeploymentCreate, DeploymentEnvironmentRef, DeploymentStepOut, LogOut, Deployment API schemas: requests, outputs, step and log items., Persisted deployment log line., Request body for triggering a deployment of an application. (+4 more)

### Community 166 - "_enforce"
Cohesion: 0.33
Nodes (7): _enforce(), node_rate_limit(), _dependency(), Request, _dependency(), Return a dependency keyed on the **authenticated node**, not the IP. A fleet…, Shared fixed-window accounting for every limiter in this module.

### Community 167 - "resolve_auth"
Cohesion: 0.14
Nodes (23): _attach_organization(), get_current_user(), get_identity(), get_optional_user(), _load_permissions(), _org_id_from_header(), AsyncSession, DbSessionDep (+15 more)

### Community 170 - "list_enrollment_tokens"
Cohesion: 0.21
Nodes (11): _enrollment_out(), list_enrollment_tokens(), Enrollment tokens in the active organization, newest first. The response type…, Revoke an unused enrollment token immediately., revoke_enrollment_token(), EnrollmentTokenState, Derived lifecycle state of an enrollment token, computed server-side. Stored as…, EnrollmentTokenOut (+3 more)

### Community 171 - "get_meta"
Cohesion: 0.40
Nodes (5): get_meta(), DbSessionDep, get, Public metadata; identity fields appear only for valid credentials., OptionalUser

### Community 172 - "Domain Model — NexusOps as a Multi-Tenant Platform"
Cohesion: 0.29
Nodes (7): org_id_column(), A plain ``org_id`` column for the few tables that carry one without taking part…, 0.1 Shipped tenant layer (Phase 1), 0. Design stance, 1. The hierarchy, 3. Cross-cutting decisions, Domain Model — NexusOps as a Multi-Tenant Platform

### Community 173 - "scope_matches"
Cohesion: 0.20
Nodes (9): Check an API-key scope list against a required permission. Supports exact match…, scope_matches(), parametrize, test_scope_matches_truth_table(), 1. Principles (already true in the codebase, kept), 5. API keys, 2.1 Identity & tenancy (new), 4.1 Audit event at resolution time (+1 more)

### Community 174 - "Authorization Architecture"
Cohesion: 0.25
Nodes (8): 0. What shipped (Phase 1), 2. Registry changes (Phase 1 + new subsystems), 3. The five system roles (target), 4. Grants (resource-level access; design now, later phase), 6. Enforcement mechanics (unchanged patterns, one addition), 7. Custom roles (later phase), 8. Permission-change audit, Authorization Architecture

### Community 175 - "2. Entities"
Cohesion: 0.25
Nodes (8): 2.1.1 ApiKey org binding detail, 2.2.1 Environment promotion detail — **shipped in Phase 2**, 2.2 Delivery (existing models, extended), 2.4 Routing & TLS (new subsystem), 2.5 Secrets (re-scoped — **shipped in Phase 2**), 2.6 Observability (existing, org-scoped via parents), 2.7 Backups, connections, billing (new subsystems, design-only in early phases), 2. Entities

### Community 176 - "permissions.py"
Cohesion: 0.29
Nodes (5): permission_exists(), PermissionSpec, Permission registry and role matrix. Permissions are *data*: the registry below…, test_permission_exists_helper(), fnmatch

### Community 177 - "record_result"
Cohesion: 0.21
Nodes (11): _bounded(), ensure_dispatchable(), ensure_node_can_run(), Any, ``CLAIMED|RUNNING → SUCCEEDED|FAILED``, guarded by ownership and expiry.…, Keep one agent report from becoming an unbounded row. The agent is…, The registry entry for *op_type* (KeyError is a programming error)., Refuse a type whose capability is outside the known vocabulary. This is the… (+3 more)

### Community 178 - "network_rates"
Cohesion: 0.33
Nodes (6): build_facts(), network_rates(), network_total_bytes(), Sum rx/tx bytes over non-loopback interfaces from /proc/net/dev., Return (rx_kb_s, tx_kb_s) or ``(None, None)`` when not measurable., Open-ended host facts, stored in the node's flexible JSONB blob. Deliberately…

### Community 179 - "20261009_1100-d4e5f6a7b8c9_correct_legacy_environment_types.py"
Cohesion: 0.33
Nodes (3): downgrade(), Phase 2.1 — correct legacy ``environment_type`` classification. The Phase 2…, No-op: the correction is a best-effort classification, not reversible.…

### Community 180 - "router.py"
Cohesion: 0.40
Nodes (4): websocket, WebSocket endpoint. Mounted by the app factory under ``/api/v1``., Hand the socket to the hub (auth handshake handled there)., websocket_endpoint()

### Community 181 - "docker_sim.py"
Cohesion: 0.20
Nodes (7): Any, datetime, Simulated docker provider for demo and test environments. The provider is…, Replay registered LogEntry rows ordered by ts (tail N). ``follow`` is ignored…, _seed_int(), test_seed_int_is_deterministic_and_spread(), math

### Community 182 - "_FakeCtx"
Cohesion: 0.40
Nodes (3): _FakeCtx, Duck-typed stand-in for AuthContext., test_require_permission_returns_ctx_when_allowed()

### Community 183 - "8. Upstream binding and re-render triggers"
Cohesion: 0.33
Nodes (6): 8.1 Binding rules, 8.2 Certificate selection rule (this doc owns it), 8.3 Re-render triggers, 8.4 Drift, 8.5 How deployments hook routing (post-deploy route sync), 8. Upstream binding and re-render triggers

### Community 184 - "EnrollmentTokenCreated"
Cohesion: 0.25
Nodes (8): _enrollment_created(), EnrollmentTokenCreated, The one response that carries the raw token., install_hint(), The one-liner an operator pastes, without the raw token in argv. The token…, 8.1 Today (real), 8.2 One-liner and token delivery (implemented bar the curl step), 8. Install UX

### Community 185 - "AgentContainerIn"
Cohesion: 0.33
Nodes (11): AgentContainerIn, Observed container state reported by an agent., _container(), parametrize, test_allowed_container_statuses(), test_bogus_status_string_rejected(), test_container_id_pattern_accepts(), test_container_id_pattern_rejects() (+3 more)

### Community 186 - "maintenance.py"
Cohesion: 0.11
Nodes (18): collect_recent_logs(), Pull recent logs from running containers of a real host. Simulated hosts are…, ingest_provider_lines(), Persist provider lines for a container AND fan them out to Redis. Used by the…, aggregate_metrics(), expire_sessions(), _run(), task (+10 more)

### Community 187 - "EventLevel"
Cohesion: 0.15
Nodes (27): Conflict, ActorType, EventLevel, create_role(), delete_role(), effective_permissions(), get_role(), list_roles() (+19 more)

### Community 188 - "instant_pacing"
Cohesion: 0.40
Nodes (4): instant_pacing(), fixture, MonkeyPatch, Remove the per-line sleeps; pacing bounds are asserted separately.

### Community 189 - "list_servers"
Cohesion: 0.29
Nodes (10): get_server(), list_servers(), list_tags(), DbDep, Depends, get, ReadCtx, All tags with their server usage counts. (+2 more)

### Community 190 - "EnvironmentUpdate"
Cohesion: 0.27
Nodes (6): EnvironmentBase, EnvironmentUpdate, _normalise_environment_type(), field_validator, Shared environment fields., Partial environment update; omitted fields are left untouched. Config is…

### Community 191 - "test_rbac.py"
Cohesion: 0.29
Nodes (9): _invite_user(), _org_headers(), Role-based access control: least-privileged users are properly boxed in., Admin invites a user with *role_name*; returns their credentials dict., Headers for an invited user, scoped to the organization they joined. An account…, Regression: a superadmin-owned key is still limited to its scope list. The…, test_operator_reads_but_cannot_manage_secrets(), test_scoped_api_key_cannot_exceed_its_grant() (+1 more)

### Community 192 - "ContainerInfo"
Cohesion: 0.28
Nodes (4): ContainerInfo, List containers visible to the provider., Inspect a single container by id (short ids allowed)., Normalized view of a container as reported by any provider.

### Community 193 - "test_migration_drift.py"
Cohesion: 0.25
Nodes (7): alembic_autogenerate, alembic_migration, Model / migration drift: the schema in the database must match the models.…, ``Base.metadata`` and the migrated database must describe the same schema., The DB whitelist and ``OperationType`` are the same closed set. The migration…, test_models_and_migrations_do_not_drift(), test_operations_type_check_matches_the_enum()

### Community 194 - "_memory_count_and_ttl"
Cohesion: 0.25
Nodes (7): _memory_count_and_ttl(), Fixed-window counter backed by process memory. Returns (count, ttl)., _clean_memory_windows(), fixture, MonkeyPatch, redis_down(), test_memory_counter_resets_per_window()

### Community 195 - "4. Operations framework (added in this pass)"
Cohesion: 0.29
Nodes (7): OperationSpec, Everything the control plane needs to know about one operation type.…, 5.1 Operation whitelist additions (deployments), 5. ProxyProvider interface, 2.3 Capabilities (implemented, Phase 3), 4. Operations framework (added in this pass), docker()

### Community 196 - "docker_capability"
Cohesion: 0.33
Nodes (6): build_capabilities(), docker_capability(), _docker_socket(), Report Docker availability by *talking to the daemon*, not by path lookup. A…, systemd is present when it is actually running as the init system., systemd_capability()

### Community 197 - "create_operation"
Cohesion: 0.40
Nodes (5): OperationCreate, Request one whitelisted action on one node., create_operation(), Request, Queue one whitelisted action for one node in the caller's organization.…

### Community 198 - "sweep_deployments"
Cohesion: 0.40
Nodes (5): task, Execute one queued deployment. The engine owns all state transitions., Re-enqueue deployments the broker lost; fail ones whose worker died.…, run_deployment(), sweep_deployments()

### Community 199 - "6. Agent security"
Cohesion: 0.40
Nodes (5): 6.1 Token scope, 6.2 docker.sock is root-equivalent, 6.3 Transport: HTTPS-only, 6.4 No arbitrary exec, 6. Agent security

### Community 200 - "_transport_is_https"
Cohesion: 0.50
Nodes (4): Whether this request's cookie will travel over https. The edge always…, _transport_is_https(), The Secure-cookie decision follows the wire, not the environment label.…, test_transport_is_https_decision()

### Community 201 - "delete_server"
Cohesion: 0.50
Nodes (4): delete_server(), delete, Hard-delete a server and all of its children (cascades)., DeleteCtx

### Community 205 - "6. Config rendering — strict allowlists"
Cohesion: 0.67
Nodes (3): 6.1 What is rendered, 6.2 The allowlist (the injection defense), 6. Config rendering — strict allowlists

## Knowledge Gaps
- **425 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+420 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1950 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **25 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `6. Tooling: reproducible e2e` connect `apply_scope_to_session` to `run_async`, `core/tenancy.py`, `client.ts`, `record_result`, `sweep_session`, `auth_service.py`?**
  _High betweenness centrality (0.192) - this node is a cross-community bridge._
- **Why does `useEventStream()` connect `client.ts` to `apiGet`, `@tanstack/react-query`, `App.tsx`, `useToast`, `DashboardPage.tsx`, `types.ts`, `apply_scope_to_session`?**
  _High betweenness centrality (0.191) - this node is a cross-community bridge._
- **Why does `TenancyScopeError` connect `core/tenancy.py` to `system_scope`, `enums.py`, `test_operations.py`, `AuthContext`, `server_service.py`, `LogLine`, `sweep_session`, `test_tenant_isolation.py`, `apply_scope_to_session`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Are the 82 inferred relationships involving `AuthContext` (e.g. with `TenancyScopeError` and `MembershipStatus`) actually correct?**
  _`AuthContext` has 82 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `APIModel` (e.g. with `OperationSpec` and `test_specs_reject_unknown_params()`) actually correct?**
  _`APIModel` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `apiGet()` (e.g. with `ContainerDetailPage.test.tsx` and `mockApi()`) actually correct?**
  _`apiGet()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `meta`, `SCHEMA`, `RESEARCH_COMMON` to the rest of the system?**
  _425 weakly-connected nodes found - possible documentation gaps or missing edges._