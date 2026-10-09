# Graph Report - nexusops  (2026-10-10)

## Corpus Check
- 323 files · ~303,506 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: (none) 8, .example 1, .service 1)

## Summary
- 4804 nodes · 14015 edges · 189 communities (168 shown, 21 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1121 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b0018f51`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- apiGet
- project_service.py
- @tanstack/react-query
- App.tsx
- operation.py
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
- enrollment_service.py
- redact_mapping
- test_deployments_simulated.py
- list_containers
- MetricGranularity
- get_settings
- Domain Routing — NexusOps
- monitor_service.py
- Node & Agent Architecture
- test_agent_backoff.py
- SimulatedDeploymentRunner
- nexusops_agent.py
- integration/conftest.py
- enums.py
- container_service.py
- test_rate_limit.py
- docker_hosts.py
- test_ws_hub.py
- monitors.py
- v1/search.py
- server_service.py
- v1/channels.py
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
- roles.py
- servers.py
- create_api_key
- test_migration_phase2.py
- v1/auth.py
- assert_error_code
- maintenance.py
- alembic
- update_channel
- helpers.py
- compilerOptions
- trigger_deployment
- test_error_logging.py
- organizations.py
- test_phase2_environments.py
- uuid
- test_schema_redaction.py
- PageParams
- Certificate Management — NexusOps
- package.json
- test_event_registry.py
- test_secrets.py
- README.md - NexusOps overview
- seed.py
- api service (FastAPI / uvicorn :8000)
- _guard
- monitor_transport.py
- test_monitors_incidents.py
- publish
- test_phase2_secrets.py
- AuthContext.tsx
- AuthContext
- create_user
- tests/conftest.py
- test_agent_contract.py
- user_service.py
- devDependencies
- operation_service.py
- LogSource
- Settings
- container.py
- validate_config
- ApiKeysPage.tsx
- test_tenant_isolation.py
- test_phase21_secret_version_integrity.py
- alerts.py
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- journey.spec.ts
- docker_host_service.py
- models/base.py
- Product Roadmap — NexusOps Multi-Tenant Platform
- env.py
- Platform Security Model — NexusOps
- apiPost
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- DashboardPage.tsx
- RolesPage.tsx
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- ScopedSession
- organization_service.py
- test_app_gating.py
- readiness
- scripts
- deps.py
- test_tenancy_allowlist.py
- Multi-Tenancy Architecture
- dependencies
- DeploymentDetailPage.test.tsx
- generate_secrets.sh
- User
- server_payload
- pytest
- middleware.py
- _run_docker_action
- resolve_secrets_for_environment
- require_permission
- install.sh
- docker-entrypoint.sh
- integration/__init__.py
- list_sessions
- CLAUDE.md - project graphify rules
- Graphify query workflow (query / path / explain / update)
- frontend/index.html - SPA shell
- NexusOps Favicon — stylized letter 'N' lettermark in sky blue (#38bdf8) on a dark navy rounded square (#0b1120, 7px corner radius)
- nexusops-backend
- docs/engineering-report.md - build and verification report
- 20260922_1000-a3f1c8d24b6e_add_tenancy_foundation.py
- postgres service (PostgreSQL 17, loopback :5433)
- phase3.spec.ts
- nexusops-understand.mjs
- Invisible account lockout (5 fails -> 15 min, enumeration resistance)
- _raw_probe
- _docker_request
- nexusops-draft.mjs
- build_heartbeat
- nexusops-challenge.mjs
- test_agent_ingestion.py
- test_schemas_agent.py
- Session
- main
- register_exception_handlers
- test_notifications.py
- Platform Vision — NexusOps
- AgentClient
- _FakeAsyncClient
- client_ip
- resolve_auth
- AgentHelloIn
- .__tablename__
- 3. Agent lifecycle
- get_meta
- SecretVersion
- scope_matches
- Authorization Architecture
- 2. Entities
- permissions.py
- DockerHostUpdate
- network_rates
- 20261009_1100-d4e5f6a7b8c9_correct_legacy_environment_types.py
- websocket_endpoint
- .dispatch
- _FakeCtx
- 8. Upstream binding and re-render triggers
- install_hint
- NexusOps — Phase 1 (Multi-Tenancy) Report
- test_collect_recent_logs_is_incremental
- Conflict
- instant_pacing

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

## Communities (189 total, 21 thin omitted)

### Community 0 - "apiGet"
Cohesion: 0.05
Nodes (30): apiGet(), ProjectOut, ProjectListPage, Command, CommandPalette(), CommandPaletteProps, STATIC_COMMANDS, Layout() (+22 more)

### Community 1 - "project_service.py"
Cohesion: 0.11
Nodes (52): paginate(), AsyncSession, Execute *stmt* with limit/offset and return ``(rows, total)``., Any, AsyncSession, Request, Append an audit row using the caller's transaction (no commit here). The…, record() (+44 more)

### Community 2 - "@tanstack/react-query"
Cohesion: 0.05
Nodes (61): AuditEntry, DeploymentOut, Page, SessionInfo, ContainerListPage, DeploymentListPage, EventsPage, IncidentListPage (+53 more)

### Community 3 - "App.tsx"
Cohesion: 0.07
Nodes (39): DeploymentStepOut, IncidentEventOut, AuditLogPage, DeploymentDetailPage, EnvironmentDetailPage, IncidentDetailPage, LoginPage, LoginRoute() (+31 more)

### Community 4 - "operation.py"
Cohesion: 0.07
Nodes (37): OperationType, The whitelist. Nothing outside this enum ships as an exec surface. Each type…, AgentOperationClaimOut, AgentOperationResultIn, AgentOperationResultOut, ContainerActionParams, LogsTailParams, OperationCreate (+29 more)

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
Cohesion: 0.08
Nodes (35): agent_fixture(), _load_agent(), Any, fixture, parametrize, Path, Agent protocol v2: honest metrics, capability detection, and the executor. The…, No CLI switch may disable TLS verification. (+27 more)

### Community 10 - "test_operations.py"
Cohesion: 0.08
Nodes (50): OperationStatus, Lifecycle of one node operation (node-agent-architecture.md §5.1).…, _dispatch(), _dispatch_body(), _enrolled_node(), _mutate_in_system_scope(), MonkeyPatch, Node operations: the compare-and-set state machine and its tenant boundary.… (+42 more)

### Community 11 - "types.ts"
Cohesion: 0.05
Nodes (59): CapabilityReport, ContainerOut, DeploymentLogLine, DeploymentStatus, EnrollmentTokenCreated, EnrollmentTokenItem, EnrollmentTokenState, MetricPoint (+51 more)

### Community 12 - "APIModel"
Cohesion: 0.03
Nodes (66): CapabilityReport, One node-reported capability. ``present`` defaults to false, and a capability…, ApiKeyCreateRequest, APIModel, BaseModel, Base for request/response models: ORM mode + strict-ish population., DeploymentApplicationRef, DeploymentCreate (+58 more)

### Community 13 - "client.ts"
Cohesion: 0.06
Nodes (42): API_BASE, ApiError, apiRequest(), buildUrl(), extractError(), getAccessToken(), getActiveOrgId(), onActiveOrgChange() (+34 more)

### Community 14 - "projects.py"
Cohesion: 0.09
Nodes (51): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+43 more)

### Community 15 - "models/__init__.py"
Cohesion: 0.13
Nodes (34): _org_scoped_classes(), Mapped classes marked :class:`~app.models.base.OrgScoped`. Reads the mapper…, Base, OrgScoped, Base for all ORM models with stable constraint naming for Alembic., Mixin marking a table as **organization-owned** (Phase 1 tenancy). Set the…, TimestampMixin, EnrollmentToken (+26 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.10
Nodes (58): deployment_log_channel(), Deployment, DeploymentStep, AlertSeverity, DeploymentStatus, StepStatus, create_alert(), Insert an alert row (flush only — the caller owns the transaction). (+50 more)

### Community 17 - "SimulatedDockerProvider"
Cohesion: 0.07
Nodes (37): ContainerHealth, ContainerStatus, Container, Observed container state mirrored from an agent or docker provider., Any, datetime, Simulated docker provider for demo and test environments. The provider is…, Plausible numbers derived from the row plus time-based sine noise. (+29 more)

### Community 18 - "enrollment_service.py"
Cohesion: 0.09
Nodes (34): agent_enroll(), Redeem an enrollment token for a unique node credential. Transactional and…, generate_enrollment_token(), An enrollment credential (``nxk_``): single-use, short-lived, org-scoped.…, Return the active org id or raise; used by services that need it explicitly., require_org(), EnrollmentTokenState, Derived lifecycle state of an enrollment token, computed server-side. Stored as… (+26 more)

### Community 19 - "redact_mapping"
Cohesion: 0.05
Nodes (59): create_secret(), delete_secret(), get_secret(), list_secret_versions(), list_secrets(), DbSession, delete, get (+51 more)

### Community 20 - "test_deployments_simulated.py"
Cohesion: 0.15
Nodes (29): execute_deployment(), Run one deployment to a terminal state. Never raises; safe to re-run., get_application(), get_environment(), _as_worker(), _delivery_chain(), _owner_ctx(), _queue() (+21 more)

### Community 21 - "list_containers"
Cohesion: 0.10
Nodes (35): _action_route(), _endpoint(), _ev(), get_container(), _like_pattern(), list_container_logs(), list_containers(), _load_container() (+27 more)

### Community 22 - "MetricGranularity"
Cohesion: 0.08
Nodes (37): get_dashboard_summary(), get_latest_server_metrics(), get_server_metrics(), CurrentUser, DbDep, Depends, get, UUID (+29 more)

### Community 23 - "get_settings"
Cohesion: 0.04
Nodes (85): argon2, argon2_exceptions, _quoted_list(), Add the operations framework table (node-agent-architecture.md §5). One tenant-…, upgrade(), downgrade(), _drop_constraint(), _quoted_list() (+77 more)

### Community 24 - "Domain Routing — NexusOps"
Cohesion: 0.08
Nodes (25): 10. Wildcards and catch-all, 11. User journey, 12. API surface, permissions, audit, 13. Monitoring tie-in, 1. Scope and current state, 2. Where nginx runs, 3.1 Domain, 3.2 Route (+17 more)

### Community 25 - "monitor_service.py"
Cohesion: 0.16
Nodes (35): MonitorStatus, Monitor, get_transport(), Pick the transport matching the monitor URL scheme., _active_incident(), _audit(), claim_due_monitors(), create_monitor() (+27 more)

### Community 26 - "Node & Agent Architecture"
Cohesion: 0.13
Nodes (15): 1. Scope and stance, 4.1 Wire contract today (real, pinned by tests), 4.2 v2 additions (implemented, Phase 3), 4. Heartbeat contract v2, 6.1 Token scope, 6.2 docker.sock is root-equivalent, 6.3 Transport: HTTPS-only, 6.4 No arbitrary exec (+7 more)

### Community 27 - "test_agent_backoff.py"
Cohesion: 0.16
Nodes (20): agent_fixture(), _install_sleep(), fake_sleep(), _load_agent(), _patch_host(), Any, fixture, MonkeyPatch (+12 more)

### Community 28 - "SimulatedDeploymentRunner"
Cohesion: 0.11
Nodes (42): LogLevel, _commit_short(), _pace(), Exception, Deployment runner port plus a faithful simulated implementation.…, Stream output lines for *step_name*; raise StepFailure to fail it., Staged docker-style simulation used by v1 deployments., Deterministic per-line delay between 0.05s and 0.35s. (+34 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.13
Nodes (19): build_capabilities(), _build_hello_payload(), docker_capability(), _docker_socket(), _enroll(), memory_total_mb(), os_info(), NexusOps host agent — protocol v2. Reports host metrics and Docker container… (+11 more)

### Community 30 - "integration/conftest.py"
Cohesion: 0.10
Nodes (27): close_redis(), lifespan(), Start the WS hub + notification dispatcher; tear them down cleanly., dispatcher_loop(), Consume ``nx:events`` and sweep due retries forever. Runs as a lifespan task., _admin_dsn(), _clean_slate(), client() (+19 more)

### Community 31 - "enums.py"
Cohesion: 0.09
Nodes (58): active_memberships(), The user's memberships in non-suspended organizations, oldest first. Reads only…, hash_password(), verify_password(), System scope bound to *db*, for rows that have no organization. Used by exactly…, system_write_scope(), ActorType, AuditResult (+50 more)

### Community 32 - "container_service.py"
Cohesion: 0.09
Nodes (43): clip(), DockerProviderError, Exception, Provider abstraction for docker hosts (real daemon or simulated). Providers are…, A provider operation failed. ``str()`` is safe to show/log., Build a compact, secret-free description of a provider failure. Only the…, Truncate *text* to *limit* characters, stripping control chars., sanitize_error() (+35 more)

### Community 33 - "test_rate_limit.py"
Cohesion: 0.18
Nodes (16): RateLimited, _memory_count_and_ttl(), rate_limit(), Fixed-window counter backed by process memory. Returns (count, ttl)., Return a dependency enforcing *limit* requests per window per IP. With…, _clean_memory_windows(), _FakeRequest, fixture (+8 more)

### Community 34 - "docker_hosts.py"
Cohesion: 0.10
Nodes (40): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+32 more)

### Community 35 - "test_ws_hub.py"
Cohesion: 0.05
Nodes (64): AppError, Exception, Base class for expected, client-facing errors., _authenticate_api_key(), _authenticate_jwt(), _bind_organization(), _close_socket(), Connection (+56 more)

### Community 36 - "monitors.py"
Cohesion: 0.16
Nodes (32): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+24 more)

### Community 37 - "v1/search.py"
Cohesion: 0.13
Nodes (31): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+23 more)

### Community 38 - "server_service.py"
Cohesion: 0.05
Nodes (92): agent_heartbeat(), agent_hello(), claim_operation(), _presented_token(), DbDep, post, Request, Response (+84 more)

### Community 39 - "v1/channels.py"
Cohesion: 0.10
Nodes (38): create_channel(), delete_channel(), get_channel(), list_channels(), list_deliveries(), DbDep, delete, Depends (+30 more)

### Community 40 - "DockerProvider"
Cohesion: 0.09
Nodes (12): DockerProvider, Any, datetime, Protocol, List containers visible to the provider., Inspect a single container by id (short ids allowed)., List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``., List volumes: keys ``name``, ``driver``, ``mountpoint``. (+4 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.13
Nodes (34): CheckResult, HTTPMonitorTransport, Deterministic fake checker for ``sim://`` monitors and demo environments.…, Real HTTP(S) probe using httpx with per-monitor settings. Redirects are…, SimulatedTransport, _check(), clock(), FakeClock (+26 more)

### Community 42 - "Deployment Architecture — NexusOps (target state)"
Cohesion: 0.10
Nodes (21): DeploymentRunner, Protocol, Adapter interface implemented by real (future) and simulated runners., Return the ordered step names for this run., 10. Events and WS during runs, 11. Post-deploy hooks, 12. Rollback semantics (existing behavior kept), 13. The simulated runner stays — labeled (+13 more)

### Community 43 - "toast.tsx"
Cohesion: 0.03
Nodes (70): CheckOut, DockerHostOut, IncidentOut, MonitorOut, App(), SimulatedChip(), mocks, Toast (+62 more)

### Community 44 - "docker_real.py"
Cohesion: 0.09
Nodes (28): ContainerInfo, ContainerStats, Normalized view of a container as reported by any provider., Point-in-time resource usage snapshot., _as_float(), _compute_stats(), _cpu_percent(), _network_bytes() (+20 more)

### Community 45 - "test_permissions.py"
Cohesion: 0.17
Nodes (9): _auth_context(), Unit tests for the permission registry, scope matching and RBAC gate., A fake context in the given organization. ``membership_status=None`` models a…, test_api_key_scope_intersects_role_permissions(), test_membership_is_required_for_authority(), test_plain_user_without_permissions_is_denied(), test_superadmin_bypasses_everything(), test_superadmin_owned_api_key_is_limited_to_its_scope() (+1 more)

### Community 46 - "events.py"
Cohesion: 0.11
Nodes (24): _decode_cursor(), _encode_cursor(), list_events(), datetime, DbSession, UUID, System events API: cursor-paginated feed + canonical type catalogue., Opaque keyset cursor for (created_at DESC, id DESC) streams. (+16 more)

### Community 47 - "test_phase3_nodes.py"
Cohesion: 0.15
Nodes (33): _create_token(), _dispatch(), _enroll(), _enrolled_node(), _load_agent_module(), _mutate_in_system_scope(), Phase 3 — Nodes & Agent v2 end-to-end behaviour. Grouped by the question each…, Import the shipped agent source (sync, so async tests never touch Path). (+25 more)

### Community 48 - "test_ssrf.py"
Cohesion: 0.07
Nodes (59): UnprocessableEntity, assert_safe_tcp_endpoint(), assert_safe_url(), _is_forbidden_address(), is_simulation_url(), ValueError, _raise_block(), SSRF guard applied to every operator-supplied outbound URL. Monitors and… (+51 more)

### Community 49 - "NotFound"
Cohesion: 0.13
Nodes (36): NotFound, _actor_type(), _collect_refs(), create_secret(), delete_secret(), _detail(), get_secret(), get_secret_detail() (+28 more)

### Community 50 - "roles.py"
Cohesion: 0.11
Nodes (29): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, delete, get (+21 more)

### Community 51 - "servers.py"
Cohesion: 0.05
Nodes (78): create_enrollment_token(), create_server(), delete_server(), _detail(), _enrollment_created(), _enrollment_out(), get_server(), list_enrollment_tokens() (+70 more)

### Community 52 - "create_api_key"
Cohesion: 0.16
Nodes (17): create_api_key(), list_api_keys(), CurrentUser, DbSessionDep, delete, get, post, Request (+9 more)

### Community 53 - "test_migration_phase2.py"
Cohesion: 0.09
Nodes (43): alembic_config, alembic_script, Phase 2.1 corrective migration: legacy ``environment_type`` classification.…, Every case is classified as documented, ids and ownership intact., An explicit non-DEV classification survives the corrective migration. The…, The correction is part of ``head`` and adds no extra Alembic head., Insert one legacy environment per case, in two organizations., _seed_typed_environments() (+35 more)

### Community 54 - "v1/auth.py"
Cohesion: 0.07
Nodes (56): change_password(), _clear_refresh_cookie(), _cookies_secure(), login(), logout(), me(), _optional_actor(), AsyncSession (+48 more)

### Community 55 - "assert_error_code"
Cohesion: 0.09
Nodes (32): assert_error_code(), cookie_attributes(), Response, Assert envelope shape + code; returns the inner error object., The raw Set-Cookie header carrying the refresh token., Extract just the opaque token from a Set-Cookie header., Parse Set-Cookie attributes (lowercased keys, empty string for flags)., refresh_cookie_header() (+24 more)

### Community 56 - "maintenance.py"
Cohesion: 0.05
Nodes (82): flush_pending_publishes(), Wait for frames scheduled by ``after_commit`` hooks to reach Redis. The commit…, Send every due PENDING / retryable-FAILED delivery. Returns count attempted. A…, retry_due_deliveries(), Celery application: periodic cadences live here, dynamic work is claimed…, task, Execute one queued deployment. The engine owns all state transitions., Re-enqueue deployments the broker lost; fail ones whose worker died.… (+74 more)

### Community 57 - "alembic"
Cohesion: 0.05
Nodes (14): alembic, downgrade(), rename ``server.*`` permission codenames to ``node.*`` The Node/Server…, _rename_permissions(), upgrade(), Fix pre-existing model/migration drift (surfaced by the new drift check). Two…, downgrade(), Phase 2.2 — make legacy environment typing match the documented precedence. The… (+6 more)

### Community 58 - "update_channel"
Cohesion: 0.09
Nodes (39): NotificationError, Any, BaseException, Exception, POST *payload* as JSON to *url*; 2xx is success, anything else raises. Response…, Raised when a delivery attempt fails. Message is safe to persist., Bounded, single-line, content-free error reason., Send a plain-text email via SMTP. Raises :class:`NotificationError`. The… (+31 more)

### Community 59 - "helpers.py"
Cohesion: 0.08
Nodes (44): owner(), Bootstrap owner credentials for this test (fresh DB => first user). ``headers``…, bearer(), error_of(), login_account(), login_headers(), Any, AsyncClient (+36 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "trigger_deployment"
Cohesion: 0.16
Nodes (18): cancel_deployment(), post, Request, Queue a new deployment for an application/environment pair., Cancel a QUEUED deployment immediately or flag a RUNNING one., Queue a rollback to the last good version of this app/environment., rollback_deployment(), trigger_deployment() (+10 more)

### Community 62 - "test_error_logging.py"
Cohesion: 0.22
Nodes (4): Regression: the catch-all 500 handler must not log raw exception text.…, _SpyLogger, test_unhandled_exception_handler_logs_class_not_message(), fastapi_testclient

### Community 63 - "organizations.py"
Cohesion: 0.15
Nodes (18): create_organization(), list_my_organizations(), CurrentUser, DbSessionDep, get, IdentityUser, patch, post (+10 more)

### Community 64 - "test_phase2_environments.py"
Cohesion: 0.18
Nodes (22): _environment(), _project(), parametrize, Phase 2: project-scoped environments, config layering, and their isolation. The…, Uniqueness is ``(project_id, slug)`` — not instance-wide., The update path is validated too (the pre-Phase-2 gap)., Knowing an environment UUID is not access: the project link must hold., Another tenant cannot reach the project, its environments, or its detail. (+14 more)

### Community 65 - "uuid"
Cohesion: 0.07
Nodes (39): API key schemas. Raw keys appear exactly once, at creation., AuditOut, Schemas for the read-only audit log API. The audit table is append-only; these…, One audit trail entry (no write routes ever exist for this resource).…, OutModel, Shared Pydantic v2 base schemas., Response model base — timestamps serialized as ISO-8601 UTC., DeploymentStepOut (+31 more)

### Community 66 - "test_schema_redaction.py"
Cohesion: 0.18
Nodes (17): is_sensitive_header(), mask_sensitive_headers(), True when *name* looks like it carries a credential (Authorization etc.)., Return a copy of *headers* with sensitive values replaced by a mask., mask_target(), Human-readable masked target safe to expose over the API. For webhook families…, _monitor_out(), Outbound-schema redaction: monitor probe credentials and webhook targets.… (+9 more)

### Community 67 - "PageParams"
Cohesion: 0.07
Nodes (62): API key routes — self-service management of the caller's own machine…, _attribute_step_idx(), _emails_for(), get_deployment(), list_application_deployments(), list_deployment_logs(), _list_deployments(), _parse_sort() (+54 more)

### Community 68 - "Certificate Management — NexusOps"
Cohesion: 0.12
Nodes (16): 10. Status/expiry tracking and monitor tie-in, 11. Failure handling, 12. Audit and events, 13. Non-goals, 3. API surface and permissions, 4.1 DNS-01 first (the default and the wedge), 4.2 DNSProvider interface, 4.3 ACME account and directory (+8 more)

### Community 69 - "package.json"
Cohesion: 0.13
Nodes (15): name, private, type, version, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom (+7 more)

### Community 70 - "test_event_registry.py"
Cohesion: 0.15
Nodes (11): list_event_types(), Depends, get, Canonical event types with descriptions (for UI filter dropdowns)., event_type_catalogue(), is_known_event_type(), Return True when *event_type* is part of the canonical registry., Serialise the registry for the ``/events/types`` endpoint. (+3 more)

### Community 71 - "test_secrets.py"
Cohesion: 0.18
Nodes (15): _create(), _environment_config(), Secrets: metadata-only reads, rotation versioning, deploy-time resolution., Project → application → environment carrying *config*; returns its id., A reference naming no secret must abort, not resolve to an empty value.…, A row this ENCRYPTION_KEY cannot decrypt must abort, not yield ``""``., ${secret:KEY} placeholders resolve through decrypt at deploy time., test_create_and_list_return_metadata_only() (+7 more)

### Community 73 - "seed.py"
Cohesion: 0.12
Nodes (31): Application, DeploymentEnvironment, Project, Delivery pipeline: projects → environments → applications → deployments. Phase…, A **project-scoped** deployment environment (Phase 2 promotion). The…, EnvironmentType, Kind of a project-scoped deployment environment (Phase 2). Descriptive only —…, ApiKey (+23 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "_guard"
Cohesion: 0.11
Nodes (23): _apply_scope_guc(), _desired_guc(), _guard(), _has_org_predicate(), install_tenancy_guards(), _mappers_of(), org_scoped_table_names(), Any (+15 more)

### Community 76 - "monitor_transport.py"
Cohesion: 0.09
Nodes (24): assert_safe_url_async(), Async wrapper around :func:`assert_safe_url`; DNS runs off the loop., CheckOutcome, coerce_headers(), _decode(), MonitorTransport, Any, BaseException (+16 more)

### Community 77 - "test_monitors_incidents.py"
Cohesion: 0.31
Nodes (8): _create_monitor(), Monitor checks driving the full down -> incident -> recovery lifecycle., Regression: probe headers and URL query credentials never leave the API. Probe…, A monitor's checks, incidents and timeline all live in its organization, so the…, test_check_now_endpoint_runs_immediately(), test_down_then_recover_lifecycle(), test_metadata_endpoint_and_private_target_blocked(), test_monitor_responses_mask_probe_credentials()

### Community 78 - "publish"
Cohesion: 0.09
Nodes (59): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+51 more)

### Community 79 - "test_phase2_secrets.py"
Cohesion: 0.19
Nodes (21): _env(), _project(), Phase 2 secrets: layered scope, immutable versions, rollback, isolation. Two…, Two racing rotations must both be kept and never share a version number., Another tenant cannot read, rotate, roll back or even enumerate the secret., The documented example: same key at three scopes; most specific wins., A ref declared in the project base config resolves for its environments., _resolved() (+13 more)

### Community 80 - "AuthContext.tsx"
Cohesion: 0.09
Nodes (24): setAccessToken(), setActiveOrgId(), Membership, User, AuthContext, AuthProvider(), AuthState, isOrgSelectionError() (+16 more)

### Community 81 - "AuthContext"
Cohesion: 0.10
Nodes (22): AuthContext, _load_organization(), Organization, UUID, Resolved identity plus the organization this request acts in.…, The active organization, or raise if this request has none., create_api_key(), list_api_keys() (+14 more)

### Community 82 - "create_user"
Cohesion: 0.18
Nodes (18): create_user(), deactivate_user(), get_user(), list_users(), CurrentUser, DbSessionDep, delete, get (+10 more)

### Community 83 - "tests/conftest.py"
Cohesion: 0.12
Nodes (14): alembic_autogenerate, alembic_migration, configure_test_env(), Test bootstrap: pin every cached setting BEFORE the first ``app`` import. The…, KEY=VALUE pairs from the repo .env (first definition wins); never logged., Export the exact settings the app caches; host values cannot leak through., _read_dot_env(), Model / migration drift: the schema in the database must match the models.… (+6 more)

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
Cohesion: 0.08
Nodes (53): cancel_operation(), create_operation(), get_operation(), list_operations(), DbDep, Depends, get, post (+45 more)

### Community 88 - "LogSource"
Cohesion: 0.15
Nodes (17): LogSource, append_lines(), count_container_logs(), detect_level(), _entry_values(), ingest_provider_lines(), Any, AsyncSession (+9 more)

### Community 89 - "Settings"
Cohesion: 0.12
Nodes (7): field_validator, model_validator, Whether the runtime connection is the RLS-enforced application role. False…, Username from :attr:`database_url`, or ``None`` if it is unparseable., Validated application settings (loaded from environment / .env)., Settings, BaseSettings

### Community 90 - "container.py"
Cohesion: 0.15
Nodes (18): _container_out(), Serialize one row; env values never leave the database (keys only)., ContainerDetailOut, ContainerOut, ContainerRemoveOut, host_ref(), HostRef, LogEntryOut (+10 more)

### Community 91 - "validate_config"
Cohesion: 0.06
Nodes (36): EnvironmentBase, EnvironmentCreate, EnvironmentUpdate, _normalise_environment_type(), field_validator, Shared environment fields., Payload to create an environment under a project., Partial environment update; omitted fields are left untouched. Config is… (+28 more)

### Community 92 - "ApiKeysPage.tsx"
Cohesion: 0.09
Nodes (20): ApiKeyOut, ApiKeysPage, ApiKeyCreatedOut, ApiKeysPage(), handleCopyKey(), copyText(), describeError(), EMPTY_FORM (+12 more)

### Community 93 - "test_tenant_isolation.py"
Cohesion: 0.04
Nodes (96): dispose_engine(), get_sessionmaker(), async_sessionmaker, AsyncSession, apply_scope_to_session(), current_org(), current_scope(), org_scope() (+88 more)

### Community 94 - "test_phase21_secret_version_integrity.py"
Cohesion: 0.18
Nodes (18): _app_role_dsn(), _owner_dsn(), _probe(), Phase 2.1 — ``secret_versions`` is append-only in the **database**, not just in…, Immutability is a database guarantee, not merely a missing code path. The owner…, The legitimate append paths keep working under the guard., The documented deletion policy: purging a Secret cascades its history., RLS is preserved: another tenant cannot see a version row, even by id. (+10 more)

### Community 95 - "alerts.py"
Cohesion: 0.13
Nodes (25): list_alerts(), mark_all_read(), mark_read(), CurrentUser, DbDep, Depends, get, post (+17 more)

### Community 96 - "NexusOps (self-hosted infrastructure management and monitoring platform)"
Cohesion: 0.20
Nodes (10): mailpit service (dev SMTP sink + web UI :8025), NexusOps compose stack (8 services on one network), HIGH finding: redirect-following SSRF in uptime monitors (fixed: follow_redirects=False + per-hop guard), SSRF guard (assert_safe_url, per-redirect-hop validation, assert_safe_tcp_endpoint), Mailpit SMTP port internal-only (host-side injection needs extra mapping), Host port knobs (NEXUSOPS_HTTP_PORT/POSTGRES/REDIS/MAILPIT/VITE), SPA entry point (loads /src/main.tsx, dark color-scheme), Uptime monitors -> incidents -> notifications flow (+2 more)

### Community 97 - "REST API surface (/api/v1)"
Cohesion: 0.29
Nodes (7): Cursor (keyset) and offset pagination envelopes, Permission model (data-driven registry, require_permission, wildcard scopes), REST API surface (/api/v1), RBAC registry (PERMISSIONS + ROLE_MATRIX + scope_matches), Adding a new resource: 7-step checklist (model -> migration -> schemas -> service -> router -> tests -> frontend), Alembic migration workflow (autogenerate, models __init__ export, entrypoint apply), Command palette (Ctrl/Cmd+K)

### Community 98 - "journey.spec.ts"
Cohesion: 0.15
Nodes (15): EDGE, MAILPIT, ADMIN, Bootstrap, bootstrapVia(), test, ADMIN, formLogin() (+7 more)

### Community 99 - "docker_host_service.py"
Cohesion: 0.13
Nodes (35): DockerHostStatus, DockerHost, DockerHostCreate, DockerHostPingOut, Result of probing a host's provider endpoint., Payload for registering a docker host., _assert_endpoint_allowed(), _assert_name_free() (+27 more)

### Community 100 - "models/base.py"
Cohesion: 0.14
Nodes (19): big_serial_pk(), json_column(), datetime, UUID, Declarative base, shared mixins and column helpers., Identity PK for very high-volume tables (metrics, logs)., status_check(), _utcnow() (+11 more)

### Community 101 - "Product Roadmap — NexusOps Multi-Tenant Platform"
Cohesion: 0.12
Nodes (17): 0. Stance, 10. Phase 7 — Teams, grants & custom roles, 11. Phase 8 — Backups, 12. Phase 9 — Billing & metering, 13.1 Scope-creep gates — what must be true before each expansion, 13. First commercially meaningful version, 14. Biggest risks (short form), 15. Reading order (+9 more)

### Community 102 - "env.py"
Cohesion: 0.24
Nodes (10): _database_url(), Alembic environment: metadata comes from app.models, URL from app settings., Migrations run as the table **owner**, never as the application role. The owner…, Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online(), Owner-role DSN for Alembic and the container entrypoint. Migrations… (+2 more)

### Community 103 - "Platform Security Model — NexusOps"
Cohesion: 0.11
Nodes (19): 10.1 Node revocation playbook (compromised node / leaked agent token), 10.2 Key compromise playbook, 10. Incident response, 1.1 Real vs simulated today (do not mistake one for the other), 1. Scope, stance, and simulation honesty, 2. Assets, 3. Trust boundaries, 4. Tenant isolation model (summary) (+11 more)

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

### Community 111 - "organization_service.py"
Cohesion: 0.15
Nodes (27): Forbidden, add_member(), create_organization(), get_organization(), membership_for_user(), AsyncSession, Membership, Organization (+19 more)

### Community 112 - "test_app_gating.py"
Cohesion: 0.44
Nodes (8): _app_for_environment(), MonkeyPatch, ENVIRONMENT gating contract: docs exposure and HSTS (see .env.example).…, create_app() with get_settings() patched to the given environment., test_non_production_does_not_emit_hsts(), test_non_production_keeps_docs_and_schema(), test_production_emits_hsts(), test_production_hides_docs_and_schema()

### Community 113 - "readiness"
Cohesion: 0.33
Nodes (6): liveness(), get, Response, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness()

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "deps.py"
Cohesion: 0.05
Nodes (85): asyncio, FastAPI dependencies: database session, authenticated tenant context, RBAC…, Agent ingest endpoints: enrollment, hello, heartbeat, and operation traffic.…, Audit log API. Strictly read-only: the table is append-only by design., _decode_frame(), _max_log_id(), _poll_new_lines(), Container API: listing/detail, lifecycle actions, removal, logs, streaming.… (+77 more)

### Community 116 - "test_tenancy_allowlist.py"
Cohesion: 0.20
Nodes (14): AST, _actual_callers(), _calls_system_scope(), _module_path(), Path, The system-scope allowlist is the only fence around the tenancy carve-out.…, Every module that could open a system scope: ``app/`` plus the scripts., No module may lift tenant isolation without being named in the list. (+6 more)

### Community 117 - "Multi-Tenancy Architecture"
Cohesion: 0.22
Nodes (9): 10. Migration (Phase 1), 1. Tenancy invariants, 2.1 Org creation — v1 decision, 4. Background jobs, 5. WebSockets, 6. Agents, 7. The IDOR suite, 8. What stays global (+1 more)

### Community 118 - "dependencies"
Cohesion: 0.33
Nodes (6): dependencies, lucide-react, react, react-dom, react-router-dom, @tanstack/react-query

### Community 119 - "DeploymentDetailPage.test.tsx"
Cohesion: 0.13
Nodes (9): ACTIVE_MEMBERSHIP, ApiError, deploymentDetail(), EMPTY_LOGS, FakeWebSocket, get, ME, post (+1 more)

### Community 120 - "generate_secrets.sh"
Cohesion: 0.47
Nodes (3): existing_real_keys(), replace_or_append(), generate_secrets.sh script

### Community 121 - "User"
Cohesion: 0.16
Nodes (13): Permission, Identity & access models: users, roles, permissions, sessions, tokens., A named permission set. ``org_id`` is NULL for every row in v1 — the five…, Role, User, Membership, Organization, Tenancy models: organizations and memberships. These two tables are the root of… (+5 more)

### Community 122 - "server_payload"
Cohesion: 0.08
Nodes (31): A valid POST /servers body with per-test overrides., server_payload(), test_token_cannot_claim_a_foreign_tenants_node(), test_v1_heartbeat_keeps_the_204_contract(), Regression: a superadmin-owned key is still limited to its scope list. The…, test_scoped_api_key_cannot_exceed_its_grant(), _create_server(), Server CRUD, cascade delete, audit trail rows and audit immutability. (+23 more)

### Community 123 - "pytest"
Cohesion: 0.20
Nodes (10): created_at server defaults must evaluate per insert, not at table creation., Regression: system_events and audit_logs shipped with DEFAULT 'now()' (quoted…, test_audit_and_event_created_at_defaults_are_dynamic(), UUID, Phase 2.2 — the environment-type correction follows the documented precedence.…, Create one legacy (application-scoped) environment per case., Every branch of the slug-first rule, end to end through ``head``., _seed_legacy() (+2 more)

### Community 124 - "middleware.py"
Cohesion: 0.14
Nodes (15): ASGIApp, AccessLogMiddleware, HTTP middleware: request ids, security headers, structured access logs., Baseline hardening headers on every API response., RequestIDMiddleware, SecurityHeadersMiddleware, create_app(), _include_routers() (+7 more)

### Community 125 - "_run_docker_action"
Cohesion: 0.18
Nodes (15): _demux_docker_stream(), _docker_error(), execute_operation(), OperationError, Exception, A stable, sanitized failure contract for the control plane., Re-validate the operation's parameters locally, against a closed shape., Make control characters safe and bound the result. Never touches container… (+7 more)

### Community 126 - "resolve_secrets_for_environment"
Cohesion: 0.19
Nodes (13): Exception, A ``${secret:KEY}`` reference could not be resolved. Fail-closed. Carries…, One successfully resolved reference: metadata for audit, no value., Outcome of resolving an environment's config references., Resolve every ``${secret:KEY}`` reference an environment's config names.…, resolve_secrets_for_environment(), ResolvedSecrets, SecretReference (+5 more)

### Community 127 - "require_permission"
Cohesion: 0.15
Nodes (13): permission_dep(), Any, Dependency factory enforcing a permission; returns 403 when denied., require_permission(), _check(), list_audit_logs(), datetime, DbSession (+5 more)

### Community 137 - "list_sessions"
Cohesion: 0.20
Nodes (11): list_sessions(), CurrentUser, DbSessionDep, delete, get, Request, UUID, Active sessions of this organization's members. Defaults to the caller's own;… (+3 more)

### Community 146 - "docs/engineering-report.md - build and verification report"
Cohesion: 0.27
Nodes (12): docker-compose.dev.yml - dev overlay, docker-compose.docker-sock.yml - docker socket override, docker-compose.yml - full stack definition, docs/agent.md - agent guide, docs/api.md - API guide, Append-only audit log (Postgres BEFORE UPDATE OR DELETE trigger), docs/deployment.md - deployment and operations guide, docs/development.md - developer guide (+4 more)

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

### Community 155 - "build_heartbeat"
Cohesion: 0.20
Nodes (10): build_heartbeat(), cpu_percent_since(), disk_stats(), load1(), memory_stats(), Return (used_gb, used_percent)., Return (busy, total) jiffies from /proc/stat., Return (used_mb, used_percent) from /proc/meminfo. (+2 more)

### Community 156 - "nexusops-challenge.mjs"
Cohesion: 0.33
Nodes (5): CHALLENGE_COMMON, meta, RESEARCH_COMMON, SCHEMA, TASKS

### Community 157 - "test_agent_ingestion.py"
Cohesion: 0.30
Nodes (10): _enrolled(), _heartbeat(), Agent ingest pipeline: hello, heartbeat, staleness transitions, events., A container absent from a later heartbeat is gone from the daemon., A payload at the agent's cap may be truncated — absence proves nothing., test_heartbeat_at_container_cap_skips_reconciliation(), test_heartbeat_removes_vanished_containers(), test_heartbeat_updates_status_metrics_and_containers() (+2 more)

### Community 158 - "test_schemas_agent.py"
Cohesion: 0.22
Nodes (19): AgentHeartbeatIn, Periodic metrics + observed containers from an enrolled agent. Network counters…, _container(), _heartbeat(), parametrize, Unit tests for agent-facing schemas (heartbeat + container payloads)., test_allowed_container_statuses(), test_bogus_status_string_rejected() (+11 more)

### Community 159 - "Session"
Cohesion: 0.22
Nodes (7): A login session binding refresh tokens to a device/context., Session, _FakeDb, Stands in for an ``AsyncSession`` whose only job here is ``sync_session``. A…, The shape of a worker task whose last statement is a commit., test_run_async_publishes_frames_scheduled_by_the_commit_hook(), commit_then_return()

### Community 160 - "main"
Cohesion: 0.20
Nodes (10): _interruptible_sleep(), main(), persist_token(), _process_pending_operations(), Atomically store *token* at 0600. Temp file in the same directory + fsync +…, Sleep in short slices so SIGTERM/SIGINT stop the agent promptly., Print the revoked-state notice once per entry; return True thereafter., Claim, execute and report operations — strictly one at a time. (+2 more)

### Community 161 - "register_exception_handlers"
Cohesion: 0.24
Nodes (9): _error_payload(), Any, FastAPI, Request, register_exception_handlers(), handle_app_error(), handle_http_exception(), handle_unexpected() (+1 more)

### Community 162 - "test_notifications.py"
Cohesion: 0.36
Nodes (9): NotificationDelivery, _channel(), _delivery(), UUID, Notification channel + delivery-log endpoints. Regression coverage for GET…, The same event frame consumed twice queues ONE delivery per channel. Every API…, test_dispatch_frame_is_idempotent_across_workers(), test_list_deliveries_filters_by_channel() (+1 more)

### Community 163 - "Platform Vision — NexusOps"
Cohesion: 0.20
Nodes (10): 1. Where NexusOps is today, 2.1 What we are NOT building, 2.2 The wedge (differentiation), 2. The direction, 3. Guiding principles, 4. Customer journey (target), 5.1 Architecture overview (target), 5. Control plane / data plane boundary (+2 more)

### Community 164 - "AgentClient"
Cohesion: 0.25
Nodes (5): AgentClient, A verifying TLS context. Verification is never disabled. A private/self-hosted…, Refuse to send credentials over plain HTTP to a non-local server. The…, _tls_context(), SSLContext

### Community 165 - "_FakeAsyncClient"
Cohesion: 0.22
Nodes (3): _FakeAsyncClient, _FakeRequestObj, Scripted httpx.AsyncClient: responses keyed by absolute request URL.

### Community 166 - "client_ip"
Cohesion: 0.31
Nodes (9): client_ip(), _enforce(), node_rate_limit(), _dependency(), Request, _dependency(), Return a dependency keyed on the **authenticated node**, not the IP. A fleet…, Best-effort client IP; honours X-Forwarded-For from trusted proxies. Delegates… (+1 more)

### Community 167 - "resolve_auth"
Cohesion: 0.12
Nodes (25): _attach_organization(), get_current_user(), get_identity(), get_optional_user(), _load_permissions(), membership_for_org(), _org_id_from_header(), AsyncSession (+17 more)

### Community 168 - "AgentHelloIn"
Cohesion: 0.13
Nodes (13): AgentHelloIn, Any, field_validator, First contact from an agent after enrollment; fills static host facts., An absent protocol version is the oldest contract, never v2., A capability report forbids unknown keys, so its shape is closed., test_agent_hello_bounds(), test_agent_hello_minimal() (+5 more)

### Community 170 - "3. Agent lifecycle"
Cohesion: 0.40
Nodes (5): 3.2 Enrollment v2, 3.3 Token storage & rotation with dual-token grace, 3.4 Revocation semantics — fixing the 401 hot-loop, 3.5 Reconnect / offline states, 3. Agent lifecycle

### Community 171 - "get_meta"
Cohesion: 0.29
Nodes (7): get_meta(), DbSessionDep, get, Public metadata; identity fields appear only for valid credentials., MetaOut, Instance metadata. Identity fields are populated only when the caller presents…, OptionalUser

### Community 172 - "SecretVersion"
Cohesion: 0.22
Nodes (9): org_id_column(), A plain ``org_id`` column for the few tables that carry one without taking part…, One immutable value of a :class:`Secret` — append-only history. A row is…, SecretVersion, 0.1 Shipped tenant layer (Phase 1), 0. Design stance, 1.1 ER diagram, 1. The hierarchy (+1 more)

### Community 173 - "scope_matches"
Cohesion: 0.25
Nodes (7): Check an API-key scope list against a required permission. Supports exact match…, scope_matches(), parametrize, test_scope_matches_truth_table(), 1. Principles (already true in the codebase, kept), 5. API keys, 2.1 Identity & tenancy (new)

### Community 174 - "Authorization Architecture"
Cohesion: 0.25
Nodes (8): 0. What shipped (Phase 1), 2. Registry changes (Phase 1 + new subsystems), 3. The five system roles (target), 4. Grants (resource-level access; design now, later phase), 6. Enforcement mechanics (unchanged patterns, one addition), 7. Custom roles (later phase), 8. Permission-change audit, Authorization Architecture

### Community 175 - "2. Entities"
Cohesion: 0.25
Nodes (8): 2.1.1 ApiKey org binding detail, 2.2.1 Environment promotion detail — **shipped in Phase 2**, 2.2 Delivery (existing models, extended), 2.4 Routing & TLS (new subsystem), 2.5 Secrets (re-scoped — **shipped in Phase 2**), 2.6 Observability (existing, org-scoped via parents), 2.7 Backups, connections, billing (new subsystems, design-only in early phases), 2. Entities

### Community 176 - "permissions.py"
Cohesion: 0.29
Nodes (5): permission_exists(), PermissionSpec, Permission registry and role matrix. Permissions are *data*: the registry below…, test_permission_exists_helper(), fnmatch

### Community 177 - "DockerHostUpdate"
Cohesion: 0.33
Nodes (5): DockerHostUpdate, model_validator, Validate/normalize an endpoint URL against the scheme allowlist., Partial update payload; only supplied fields change., validate_endpoint_url()

### Community 178 - "network_rates"
Cohesion: 0.33
Nodes (6): build_facts(), network_rates(), network_total_bytes(), Sum rx/tx bytes over non-loopback interfaces from /proc/net/dev., Return (rx_kb_s, tx_kb_s) or ``(None, None)`` when not measurable., Open-ended host facts, stored in the node's flexible JSONB blob. Deliberately…

### Community 179 - "20261009_1100-d4e5f6a7b8c9_correct_legacy_environment_types.py"
Cohesion: 0.33
Nodes (3): downgrade(), Phase 2.1 — correct legacy ``environment_type`` classification. The Phase 2…, No-op: the correction is a best-effort classification, not reversible.…

### Community 180 - "websocket_endpoint"
Cohesion: 0.67
Nodes (3): websocket, Hand the socket to the hub (auth handshake handled there)., websocket_endpoint()

### Community 181 - ".dispatch"
Cohesion: 0.60
Nodes (3): Request, Response, RequestResponseEndpoint

### Community 182 - "_FakeCtx"
Cohesion: 0.33
Nodes (4): _FakeCtx, Duck-typed stand-in for AuthContext., test_require_permission_raises_forbidden_when_denied(), test_require_permission_returns_ctx_when_allowed()

### Community 183 - "8. Upstream binding and re-render triggers"
Cohesion: 0.33
Nodes (6): 8.1 Binding rules, 8.2 Certificate selection rule (this doc owns it), 8.3 Re-render triggers, 8.4 Drift, 8.5 How deployments hook routing (post-deploy route sync), 8. Upstream binding and re-render triggers

### Community 184 - "install_hint"
Cohesion: 0.40
Nodes (5): install_hint(), The one-liner an operator pastes, without the raw token in argv. The token…, 8.1 Today (real), 8.2 One-liner and token delivery (implemented bar the curl step), 8. Install UX

### Community 185 - "NexusOps — Phase 1 (Multi-Tenancy) Report"
Cohesion: 0.40
Nodes (4): 1. What Phase 1 delivered, 5. Tests, 8. Position, NexusOps — Phase 1 (Multi-Tenancy) Report

### Community 187 - "Conflict"
Cohesion: 0.15
Nodes (25): Conflict, create_role(), delete_role(), effective_permissions(), get_role(), list_roles(), permissions_for_role(), AsyncSession (+17 more)

### Community 188 - "instant_pacing"
Cohesion: 0.40
Nodes (4): instant_pacing(), fixture, MonkeyPatch, Remove the per-line sleeps; pacing bounds are asserted separately.

## Knowledge Gaps
- **425 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+420 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1941 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `6. Tooling: reproducible e2e` connect `maintenance.py` to `test_ws_hub.py`, `client.ts`, `operation_service.py`, `NexusOps — Phase 1 (Multi-Tenancy) Report`, `test_tenant_isolation.py`, `enums.py`?**
  _High betweenness centrality (0.201) - this node is a cross-community bridge._
- **Why does `useEventStream()` connect `client.ts` to `apiGet`, `@tanstack/react-query`, `App.tsx`, `useToast`, `DashboardPage.tsx`, `types.ts`, `maintenance.py`?**
  _High betweenness centrality (0.200) - this node is a cross-community bridge._
- **Why does `TenancyScopeError` connect `test_tenant_isolation.py` to `test_operations.py`, `_guard`, `publish`, `AuthContext`, `enrollment_service.py`, `deps.py`, `LogSource`, `maintenance.py`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Are the 82 inferred relationships involving `AuthContext` (e.g. with `TenancyScopeError` and `MembershipStatus`) actually correct?**
  _`AuthContext` has 82 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `APIModel` (e.g. with `OperationSpec` and `test_specs_reject_unknown_params()`) actually correct?**
  _`APIModel` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `apiGet()` (e.g. with `ContainerDetailPage.test.tsx` and `mockApi()`) actually correct?**
  _`apiGet()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `meta`, `SCHEMA`, `RESEARCH_COMMON` to the rest of the system?**
  _425 weakly-connected nodes found - possible documentation gaps or missing edges._