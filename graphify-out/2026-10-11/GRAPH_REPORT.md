# Graph Report - nexusops  (2026-10-10)

## Corpus Check
- 353 files · ~352,494 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: (none) 10, .example 1, .service 1)

## Summary
- 5684 nodes · 16744 edges · 223 communities (200 shown, 23 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1322 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c8cc2f13`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- apiGet
- project_service.py
- ApiKeysPage.tsx
- test_phase4_routing.py
- operation.py
- types.ts
- config.py
- ProjectDetailPage.tsx
- DockerHostsPage.tsx
- test_agent_v2.py
- assert_error_code
- ServerDetailPage.tsx
- APIModel
- client.ts
- projects.py
- models/__init__.py
- deployment_engine.py
- SimulatedDockerProvider
- EnrollmentToken
- v1/secrets.py
- test_deployments_simulated.py
- containers.py
- metrics_service.py
- get_settings
- Domain Routing — NexusOps
- monitors.py
- Node & Agent Architecture
- test_agent_backoff.py
- SimulatedDeploymentRunner
- nexusops_agent.py
- integration/conftest.py
- auth_service.py
- record
- test_rate_limit.py
- docker_hosts.py
- test_ws_hub.py
- nginx.py
- search
- enums.py
- v1/channels.py
- DockerProvider
- test_monitor_transport.py
- StepFailure
- @tanstack/react-query
- docker_real.py
- test_permissions.py
- routes.py
- test_phase3_nodes.py
- test_ssrf.py
- secret_service.py
- roles.py
- DbDep
- proxy_service.py
- pytest
- v1/auth.py
- test_agent_nginx_contract.py
- sweep_session
- alembic
- notification_service.py
- test_tenant_isolation.py
- compilerOptions
- _list_deployments
- register_exception_handlers
- dns_verifier.py
- test_phase2_environments.py
- route_service.py
- test_schema_redaction.py
- PageParams
- encrypt_str
- package.json
- test_event_registry.py
- test_secrets.py
- test_nginx_renderer.py
- domain_service.py
- api service (FastAPI / uvicorn :8000)
- typing
- server_service.py
- domains.py
- incidents.py
- test_phase2_secrets.py
- AuthContext.tsx
- monitor_service.py
- canonicalize_name
- tests/conftest.py
- test_schemas_server.py
- sessions.py
- devDependencies
- operation_service.py
- LogLine
- Settings
- DomainStatus
- validate_config
- Path
- org_scope
- test_phase21_secret_version_integrity.py
- StepLine
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- phase3.spec.ts
- run_async
- Secrets Architecture
- README.md - NexusOps overview
- env.py
- apply_scope_to_session
- _exec
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- App.tsx
- RealDockerProvider
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- ScopedSession
- organization_service.py
- test_app_gating.py
- dnsmock.py
- scripts
- v1/health.py
- test_tenancy_allowlist.py
- resolve_auth
- dependencies
- DeploymentDetailPage.test.tsx
- generate_secrets.sh
- ServerOut
- server_payload
- _run_migration
- middleware.py
- OperationError
- list_operations
- list_audit_logs
- install.sh
- docker-entrypoint.sh
- integration/__init__.py
- Page
- CLAUDE.md - project graphify rules
- Graphify query workflow (query / path / explain / update)
- frontend/index.html - SPA shell
- NexusOps Favicon — stylized letter 'N' lettermark in sky blue (#38bdf8) on a dark navy rounded square (#0b1120, 7px corner radius)
- nexusops-backend
- test_auth_multi_org.py
- 20260922_1000-a3f1c8d24b6e_add_tenancy_foundation.py
- postgres service (PostgreSQL 17, loopback :5433)
- phase4.spec.ts
- nexusops-understand.mjs
- Invisible account lockout (5 fails -> 15 min, enumeration resistance)
- nginx_capability
- DashboardPage.tsx
- nexusops-draft.mjs
- notification_sender.py
- nexusops-challenge.mjs
- test_agent_ingestion.py
- test_schemas_agent.py
- test_run_async_publishes_frames_scheduled_by_the_commit_hook
- main
- monitor_transport.py
- test_notifications.py
- redact_mapping
- AgentClient
- SecretsPage.tsx
- monitoring.py
- AuthContext
- _run
- .__tablename__
- test_agent_contract.py
- 20261009_1000-c3d4e5f6a7b8_enforce_secret_version_integrity.py
- _FakeAsyncClient
- scope_matches
- configure_logging
- 2. Entities
- Platform Security Model — NexusOps
- create_operation
- network_rates
- test_corrects_legacy_environment_types
- websocket_endpoint
- _nginx_apply
- _nginx_bootstrap
- 8. Upstream binding and re-render triggers
- Multi-Tenancy Architecture
- NotificationChannel
- maintenance.py
- Conflict
- instant_pacing
- servers.py
- resolve_secrets_for_environment
- UUID
- ControlHandler
- test_migration_drift.py
- node_proxy_status
- channel.py
- 20261010_1200-f4a5b6c7d8e9_phase4_domains_and_routes.py
- test_error_logging.py
- Product Roadmap — NexusOps Multi-Tenant Platform
- Platform Vision — NexusOps
- enqueue.py
- test_monitors_incidents.py
- journey.spec.ts
- build_capabilities
- ApplicationBase
- sweep_deployments
- 20261008_1200-b2c3d4e5f6a7_add_projects_and_environments.py
- 20261009_1300-a1b2c3d4e5f6_add_phase3_nodes_and_agent_v2.py
- _validate_bundle
- 20261004_1200-e7c4a2b9d1f3_add_operations_framework.py
- get_meta
- ._check_status
- sweep_routes
- sweep_servers
- test_created_at_defaults.py
- test_remove_honours_force_and_never_shells
- Domain Model — NexusOps as a Multi-Tenant Platform
- 4. Operations framework (added in this pass)
- _seed_legacy_data
- _seed_legacy
- .ok
- test_domain_creation_rejects_invalid_names
- test_existing_url_monitors_are_untouched_by_routing

## God Nodes (most connected - your core abstractions)
1. `AuthContext` - 155 edges
2. `APIModel` - 145 edges
3. `apiGet()` - 91 edges
4. `Server` - 86 edges
5. `record()` - 86 edges
6. `NotFound` - 83 edges
7. `get_settings()` - 82 edges
8. `publish()` - 71 edges
9. `apiPost()` - 70 edges
10. `useToast()` - 67 edges

## Surprising Connections (you probably didn't know these)
- `3. Cross-cutting decisions` --references--> `require_permission()`  [INFERRED]
  docs/domain-model.md → backend/app/api/deps.py
- `10. Phase 7 — Teams, grants & custom roles` --references--> `require_permission()`  [INFERRED]
  docs/product-roadmap.md → backend/app/api/deps.py
- `3.2 Route` --references--> `rate_limit()`  [INFERRED]
  docs/domain-routing.md → backend/app/core/rate_limit.py
- `6.2 The allowlist (the injection defense)` --references--> `rate_limit()`  [INFERRED]
  docs/domain-routing.md → backend/app/core/rate_limit.py
- `1.1 Storage and crypto` --references--> `encrypt_str()`  [INFERRED]
  docs/secrets-architecture.md → backend/app/core/security.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three authentication credential families with centralized permission checks** — docs_api_md_auth, docs_api_md_refresh_rotation, docs_api_md_api_keys, docs_agent_md_enrollment_token, docs_api_md_permission_model [EXTRACTED 1.00]
- **NexusOps compose stack services** — docker_compose_yml_nexusops_stack, docker_compose_yml_postgres_service, docker_compose_yml_redis_service, docker_compose_yml_mailpit_service, docker_compose_yml_api_service, docker_compose_yml_worker_service, docker_compose_yml_scheduler_service, docker_compose_yml_frontend_service, docker_compose_yml_nginx_service [EXTRACTED 1.00]
- **WebSocket real-time fan-out spine** — docs_architecture_md_websocket_hub, docs_api_md_websocket_channels, docker_compose_yml_redis_service, docs_architecture_md_event_bus, readme_react_spa [INFERRED 0.85]

## Communities (223 total, 23 thin omitted)

### Community 0 - "apiGet"
Cohesion: 0.06
Nodes (95): apiGet(), apiPost(), CursorPage, DeploymentOut, ProjectOut, RouteConfigState, DeploymentListPage, DomainDetailPage (+87 more)

### Community 1 - "project_service.py"
Cohesion: 0.10
Nodes (53): paginate(), AsyncSession, Execute *stmt* with limit/offset and return ``(rows, total)``., EnvironmentCreate, Payload to create an environment under a project., ProjectCreate, ProjectUpdate, Payload to create a project; owner defaults to the caller. (+45 more)

### Community 2 - "ApiKeysPage.tsx"
Cohesion: 0.09
Nodes (20): ApiKeyOut, ApiKeysPage, ApiKeyCreatedOut, ApiKeysPage(), handleCopyKey(), copyText(), describeError(), EMPTY_FORM (+12 more)

### Community 3 - "test_phase4_routing.py"
Cohesion: 0.09
Nodes (66): MonitorTargetType, What a monitor observes (domain-model.md §2.6, polymorphic targets). ``URL`` is…, _claim(), _container_id(), _count_rows_in_system_scope(), _create_domain(), _create_node(), _create_route() (+58 more)

### Community 4 - "operation.py"
Cohesion: 0.06
Nodes (40): OperationType, The whitelist. Nothing outside this enum ships as an exec surface. Each type…, AgentOperationClaimOut, AgentOperationResultIn, AgentOperationResultOut, ContainerActionParams, LogsTailParams, OperationCreate (+32 more)

### Community 5 - "types.ts"
Cohesion: 0.04
Nodes (57): AlertOut, CapabilityReport, ChannelOut, ContainerOut, DeliveryOut, DeploymentLogLine, DeploymentStatus, DeploymentStepOut (+49 more)

### Community 6 - "config.py"
Cohesion: 0.12
Nodes (27): _is_trusted(), _parse_networks(), Request, Client-IP resolution behind chained reverse proxies. The API never takes TCP…, Parse a comma-separated CIDR list; malformed entries are skipped., Real client address for *request* per the trust model above., resolve_client_ip(), fail_on_bad_config() (+19 more)

### Community 7 - "ProjectDetailPage.tsx"
Cohesion: 0.08
Nodes (30): apiDelete(), apiPatch(), ApplicationOut, ENVIRONMENT_TYPE_LABELS, EnvironmentType, ProjectDetailPage, configToText(), parseConfigText() (+22 more)

### Community 8 - "DockerHostsPage.tsx"
Cohesion: 0.06
Nodes (30): DockerHostOut, DockerHostsPage, CheckboxField(), CheckboxFieldProps, FieldAria, FieldBaseProps, PasswordField(), PasswordFieldProps (+22 more)

### Community 9 - "test_agent_v2.py"
Cohesion: 0.09
Nodes (33): agent_fixture(), _load_agent(), Any, fixture, parametrize, Agent protocol v2: honest metrics, capability detection, and the executor. The…, Phase 4 shipped three nginx ops — no file primitive, no command primitive., Trusting a private CA must not weaken verification. (+25 more)

### Community 10 - "assert_error_code"
Cohesion: 0.07
Nodes (58): assert_error_code(), Assert envelope shape + code; returns the inner error object., Regression: lockout must not leak which emails exist. After login_max_attempts…, test_locked_account_response_is_indistinguishable(), test_metadata_endpoint_and_private_target_blocked(), _dispatch(), _dispatch_body(), _enrolled_node() (+50 more)

### Community 11 - "ServerDetailPage.tsx"
Cohesion: 0.08
Nodes (39): EnrollmentTokenCreated, EnrollmentTokenItem, MetricPoint, OperationItem, OperationType, ServerDetailPage, ServerListPage, ChartSeries (+31 more)

### Community 12 - "APIModel"
Cohesion: 0.03
Nodes (107): AgentContainerPortIn, AgentEnrollIn, AgentEnrollOut, AgentHeartbeatOut, Agent-facing schemas. Payloads are data only — never executed. Wire protocol v2…, One published-port binding of a container, as docker reports it. Four distinct…, v2 heartbeat response: cadence, work to pull, and any pending rotation. A v1…, The first request a brand-new machine makes. ``enrollment_token`` is an… (+99 more)

### Community 13 - "client.ts"
Cohesion: 0.05
Nodes (59): API_BASE, ApiError, apiRequest(), buildUrl(), extractError(), getAccessToken(), getActiveOrgId(), onActiveOrgChange() (+51 more)

### Community 14 - "projects.py"
Cohesion: 0.13
Nodes (45): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+37 more)

### Community 15 - "models/__init__.py"
Cohesion: 0.06
Nodes (88): generate_agent_token(), hash_token(), A per-node credential (``nxa_``): long-lived, node-scoped, never shared., _org_scoped_classes(), Mapped classes marked :class:`~app.models.base.OrgScoped`. Reads the mapper…, Base, big_serial_pk(), json_column() (+80 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.09
Nodes (66): _attribute_step_idx(), _parse_statuses(), datetime, Deployment endpoints: list, detail, trigger, cancel, rollback, logs. Two…, Queue a new deployment for an application/environment pair., trigger_deployment(), deployment_log_channel(), NotFound (+58 more)

### Community 17 - "SimulatedDockerProvider"
Cohesion: 0.09
Nodes (31): DockerProviderError, A provider operation failed. ``str()`` is safe to show/log., Any, Plausible numbers derived from the row plus time-based sine noise., Implements :class:`DockerProvider` semantics against DB rows., Make a container row visible to this provider instance., Attach already-fetched log rows so ``logs()`` can replay them., _seed_int() (+23 more)

### Community 18 - "EnrollmentToken"
Cohesion: 0.12
Nodes (23): generate_enrollment_token(), An enrollment credential (``nxk_``): single-use, short-lived, org-scoped.…, EnrollmentToken, One single-use credential that enrolls (or claims) exactly one node., Whether the row could still be redeemed (not a race-safe check)., _claim_and_consume(), create_token(), enroll() (+15 more)

### Community 19 - "v1/secrets.py"
Cohesion: 0.13
Nodes (30): create_secret(), delete_secret(), get_secret(), list_secret_versions(), list_secrets(), DbSession, delete, get (+22 more)

### Community 20 - "test_deployments_simulated.py"
Cohesion: 0.14
Nodes (30): execute_deployment(), Run one deployment to a terminal state. Never raises; safe to re-run., get_application(), get_environment(), _as_worker(), _delivery_chain(), _owner_ctx(), _queue() (+22 more)

### Community 21 - "containers.py"
Cohesion: 0.09
Nodes (45): _action_route(), _endpoint(), _container_out(), _ev(), get_container(), _like_pattern(), list_container_logs(), list_containers() (+37 more)

### Community 22 - "metrics_service.py"
Cohesion: 0.11
Nodes (29): aggregate_rollups(), dashboard_summary(), ensure_server(), _extra_object(), granularity_for_range(), latest_for_servers(), _prune(), Any (+21 more)

### Community 23 - "get_settings"
Cohesion: 0.07
Nodes (49): argon2, argon2_exceptions, get_settings(), Return the cached settings singleton., get_engine(), AsyncEngine, Runtime DSN (application role, RLS enforced) for Celery/script sync paths., sync_database_url() (+41 more)

### Community 24 - "Domain Routing — NexusOps"
Cohesion: 0.09
Nodes (23): 10. Wildcards and catch-all, 11. User journey, 12. API surface, permissions, audit, 13. Monitoring tie-in, 1. Scope and current state, 2. Where nginx runs, 3.1 Domain, 3.2 Route (+15 more)

### Community 25 - "monitors.py"
Cohesion: 0.11
Nodes (44): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+36 more)

### Community 26 - "Node & Agent Architecture"
Cohesion: 0.08
Nodes (26): install_hint(), The one-liner an operator pastes, without the raw token in argv. The token…, 1. Scope and stance, 3.2 Enrollment v2, 3.3 Token storage & rotation with dual-token grace, 3.4 Revocation semantics — fixing the 401 hot-loop, 3.5 Reconnect / offline states, 3. Agent lifecycle (+18 more)

### Community 27 - "test_agent_backoff.py"
Cohesion: 0.14
Nodes (22): agent_fixture(), _install_sleep(), fake_sleep(), _load_agent(), _patch_host(), Any, fixture, MonkeyPatch (+14 more)

### Community 28 - "SimulatedDeploymentRunner"
Cohesion: 0.25
Nodes (23): Staged docker-style simulation used by v1 deployments., Canonical step identifiers stored on :class:`DeploymentStep` rows., SimulatedDeploymentRunner, StepName, _collect(), _ctx(), Unit tests for SimulatedDeploymentRunner (async generators, no broker)., RESOLVE_CONFIG is planned by the engine, not produced by a runner. (+15 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.10
Nodes (26): build_heartbeat(), collect_container_stats(), collect_containers(), _container_ports(), _container_status(), cpu_percent_since(), disk_stats(), _docker_request() (+18 more)

### Community 30 - "integration/conftest.py"
Cohesion: 0.11
Nodes (28): close_redis(), _admin_dsn(), _clean_slate(), client(), _ensure_database(), _migrated_database(), org_db(), owner() (+20 more)

### Community 31 - "auth_service.py"
Cohesion: 0.06
Nodes (87): hash_password(), System scope bound to *db*, for rows that have no organization. Used by exactly…, system_write_scope(), MembershipStatus, UserStatus, Opaque refresh token; only its SHA-256 hash is stored. Rotation chain: on…, RefreshToken, User (+79 more)

### Community 32 - "record"
Cohesion: 0.09
Nodes (50): BadRequest, AuditResult, ContainerHealth, ContainerStatus, DockerHostStatus, Container, DockerHost, Observed container state mirrored from an agent or docker provider. (+42 more)

### Community 33 - "test_rate_limit.py"
Cohesion: 0.18
Nodes (16): RateLimited, _memory_count_and_ttl(), rate_limit(), Fixed-window counter backed by process memory. Returns (count, ttl)., Return a dependency enforcing *limit* requests per window per IP. With…, _clean_memory_windows(), _FakeRequest, fixture (+8 more)

### Community 34 - "docker_hosts.py"
Cohesion: 0.05
Nodes (77): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+69 more)

### Community 35 - "test_ws_hub.py"
Cohesion: 0.05
Nodes (64): AppError, Exception, Base class for expected, client-facing errors., _authenticate_api_key(), _authenticate_jwt(), _bind_organization(), _close_socket(), Connection (+56 more)

### Community 36 - "nginx.py"
Cohesion: 0.06
Nodes (49): _header_lines(), _quote(), _rate_zone(), NginxProvider — a pure, deterministic renderer plus the two op wrappers.…, Validate the route's headers and split them by destination., Wrap an already-validated value in quotes for a template slot. Values reaching…, The ``limit_req_zone`` declaration for a rate-limited route., A fixed host redirect, or ``None`` for a normal proxying route. (+41 more)

### Community 37 - "search"
Cohesion: 0.11
Nodes (32): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+24 more)

### Community 38 - "enums.py"
Cohesion: 0.06
Nodes (71): ActorType, AlertSeverity, CredentialKind, EnvironmentType, EventLevel, IncidentEventKind, IncidentSeverity, IncidentStatus (+63 more)

### Community 39 - "v1/channels.py"
Cohesion: 0.14
Nodes (30): create_channel(), delete_channel(), get_channel(), list_channels(), list_deliveries(), DbDep, delete, Depends (+22 more)

### Community 40 - "DockerProvider"
Cohesion: 0.09
Nodes (12): DockerProvider, Any, datetime, Protocol, List containers visible to the provider., Inspect a single container by id (short ids allowed)., List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``., List volumes: keys ``name``, ``driver``, ``mountpoint``. (+4 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.13
Nodes (34): CheckResult, HTTPMonitorTransport, Deterministic fake checker for ``sim://`` monitors and demo environments.…, Real HTTP(S) probe using httpx with per-monitor settings. Redirects are…, SimulatedTransport, _check(), clock(), FakeClock (+26 more)

### Community 42 - "StepFailure"
Cohesion: 0.09
Nodes (23): DeploymentRunner, Exception, Protocol, Raised by a runner when a step fails irrecoverably., Adapter interface implemented by real (future) and simulated runners., Return the ordered step names for this run., StepFailure, 10. Events and WS during runs (+15 more)

### Community 43 - "@tanstack/react-query"
Cohesion: 0.03
Nodes (55): CheckOut, IncidentOut, MonitorOut, SessionInfo, ACTIVE_MEMBERSHIP, ME, mocks, mocks (+47 more)

### Community 44 - "docker_real.py"
Cohesion: 0.12
Nodes (24): ContainerStats, Exception, Build a compact, secret-free description of a provider failure. Only the…, Point-in-time resource usage snapshot., sanitize_error(), _as_float(), _compute_stats(), _cpu_percent() (+16 more)

### Community 45 - "test_permissions.py"
Cohesion: 0.09
Nodes (18): permission_exists(), PermissionSpec, Permission registry and role matrix. Permissions are *data*: the registry below…, _auth_context(), _FakeCtx, Unit tests for the permission registry, scope matching and RBAC gate., Duck-typed stand-in for AuthContext., A fake context in the given organization. ``membership_status=None`` models a… (+10 more)

### Community 46 - "routes.py"
Cohesion: 0.08
Nodes (41): create_route(), delete_route(), disable_route(), _domain_status(), enable_route(), get_route(), list_routes(), AsyncSession (+33 more)

### Community 47 - "test_phase3_nodes.py"
Cohesion: 0.14
Nodes (35): Run the enclosed block with tenant filtering off (maintenance only). ``reason``…, system_scope(), _create_token(), _dispatch(), _enroll(), _enrolled_node(), _load_agent_module(), _mutate_in_system_scope() (+27 more)

### Community 48 - "test_ssrf.py"
Cohesion: 0.07
Nodes (60): UnprocessableEntity, assert_safe_tcp_endpoint(), assert_safe_url(), _is_forbidden_address(), is_simulation_url(), ValueError, _raise_block(), SSRF guard applied to every operator-supplied outbound URL. Monitors and… (+52 more)

### Community 49 - "secret_service.py"
Cohesion: 0.13
Nodes (37): An encrypted configuration value, scoped to org, project or environment.…, One immutable value of a :class:`Secret` — append-only history. A row is…, Secret, SecretVersion, _actor_type(), create_secret(), delete_secret(), _detail() (+29 more)

### Community 50 - "roles.py"
Cohesion: 0.11
Nodes (29): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, delete, get (+21 more)

### Community 51 - "DbDep"
Cohesion: 0.14
Nodes (23): apply_node_proxy_config(), create_server(), DbDep, post, Request, Register a node. Returns the row without an enrollment token — generate one via…, Create a tag or update its colour (idempotent on name)., Rotate a node's credential with a bounded dual-token grace window. The previous… (+15 more)

### Community 52 - "proxy_service.py"
Cohesion: 0.08
Nodes (49): ListenerOwnership, Who holds one required listener port, per the node's pre-flight. The…, NodeProxyCapabilityOut, The node's reported nginx capability, bounded to the useful facts., One genuinely usable published port reported by the node's agent., UpstreamPortOut, capability_of(), capability_out() (+41 more)

### Community 53 - "pytest"
Cohesion: 0.14
Nodes (18): alembic_config, alembic_script, Phase 2.1 corrective migration: legacy ``environment_type`` classification.…, The correction is part of ``head`` and adds no extra Alembic head., test_corrective_migration_is_reachable_from_head(), _alembic_config(), _migration_dsn(), Phase 2 migration (`b2c3d4e5f6a7`) against realistic legacy data. The promotion… (+10 more)

### Community 54 - "v1/auth.py"
Cohesion: 0.06
Nodes (66): change_password(), _clear_refresh_cookie(), _cookies_secure(), login(), logout(), me(), _optional_actor(), AsyncSession (+58 more)

### Community 55 - "test_agent_nginx_contract.py"
Cohesion: 0.08
Nodes (47): CapabilityReport, One node-reported capability. ``present`` defaults to false, and a capability…, _agent_bundle(), agent_fixture(), _bootstrap_fixture(), _load_agent(), Any, fixture (+39 more)

### Community 56 - "sweep_session"
Cohesion: 0.16
Nodes (21): _apply_for_node(), Push a fresh bundle to one node, tolerating anything that blocks it. A domain…, org_for(), org_session(), Any, UUID, Yield a short-lived session; commit on success, rollback on error., A task session inside the **system** scope — for work that spans tenants. The… (+13 more)

### Community 57 - "alembic"
Cohesion: 0.05
Nodes (13): alembic, downgrade(), rename ``server.*`` permission codenames to ``node.*`` The Node/Server…, _rename_permissions(), upgrade(), Fix pre-existing model/migration drift (surfaced by the new drift check). Two…, downgrade(), Phase 2.1 — correct legacy ``environment_type`` classification. The Phase 2… (+5 more)

### Community 58 - "notification_service.py"
Cohesion: 0.14
Nodes (28): _as_uuid(), _attempt_delivery(), decode_delivery_cursor(), decrypt_channel_config(), dispatch_event_frame(), _send(), dispatcher_loop(), encode_delivery_cursor() (+20 more)

### Community 59 - "test_tenant_isolation.py"
Cohesion: 0.05
Nodes (77): bearer(), cookie_attributes(), error_of(), login_account(), login_headers(), Any, AsyncClient, Response (+69 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "_list_deployments"
Cohesion: 0.11
Nodes (32): cancel_deployment(), _emails_for(), get_deployment(), list_application_deployments(), list_deployment_logs(), _list_deployments(), _parse_sort(), alias (+24 more)

### Community 62 - "register_exception_handlers"
Cohesion: 0.24
Nodes (9): _error_payload(), Any, FastAPI, Request, register_exception_handlers(), handle_app_error(), handle_http_exception(), handle_unexpected() (+1 more)

### Community 63 - "dns_verifier.py"
Cohesion: 0.07
Nodes (44): apex_of(), The name a wildcard Domain is anchored at (``*.example.com`` →…, The exact TXT owner name a user must publish at their provider., verification_record_name(), decide(), _discover_nameservers(), matches_token(), _normalise_ns() (+36 more)

### Community 64 - "test_phase2_environments.py"
Cohesion: 0.18
Nodes (22): _environment(), _project(), parametrize, Phase 2: project-scoped environments, config layering, and their isolation. The…, Uniqueness is ``(project_id, slug)`` — not instance-wide., The update path is validated too (the pre-Phase-2 gap)., Knowing an environment UUID is not access: the project link must hold., Another tenant cannot reach the project, its environments, or its detail. (+14 more)

### Community 65 - "route_service.py"
Cohesion: 0.12
Nodes (44): Last nginx apply outcome for a route, as reported by its node's agent.…, RouteConfigState, One hostname+path served from one container on one node. Relationship rules the…, Route, _actor(), _conflicting_route(), create_route(), delete_route() (+36 more)

### Community 66 - "test_schema_redaction.py"
Cohesion: 0.18
Nodes (17): is_sensitive_header(), mask_sensitive_headers(), True when *name* looks like it carries a credential (Authorization etc.)., Return a copy of *headers* with sensitive values replaced by a mask., mask_target(), Human-readable masked target safe to expose over the API. For webhook families…, _monitor_out(), Outbound-schema redaction: monitor probe credentials and webhook targets.… (+9 more)

### Community 67 - "PageParams"
Cohesion: 0.04
Nodes (84): list_alerts(), mark_all_read(), mark_read(), CurrentUser, DbDep, Depends, get, post (+76 more)

### Community 68 - "encrypt_str"
Cohesion: 0.09
Nodes (29): decrypt_str(), digest_of(), encrypt_str(), _fernet(), Short server-verifiable digest used for change detection display. HMAC-SHA256…, parametrize, test_decrypt_with_wrong_ciphertext_raises_value_error(), test_digest_length_and_determinism() (+21 more)

### Community 69 - "package.json"
Cohesion: 0.13
Nodes (15): name, private, type, version, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom (+7 more)

### Community 70 - "test_event_registry.py"
Cohesion: 0.21
Nodes (8): event_type_catalogue(), is_known_event_type(), Canonical registry of system-event types. Single source of truth shared by…, Return True when *event_type* is part of the canonical registry., Serialise the registry for the ``/events/types`` endpoint., Registry coherence: schema-advertised event types must equal the canonical…, test_catalogue_serialises_every_entry(), test_known_event_lookup()

### Community 71 - "test_secrets.py"
Cohesion: 0.18
Nodes (15): _create(), _environment_config(), Secrets: metadata-only reads, rotation versioning, deploy-time resolution., Project → application → environment carrying *config*; returns its id., A reference naming no secret must abort, not resolve to an empty value.…, A row this ENCRYPTION_KEY cannot decrypt must abort, not yield ``""``., ${secret:KEY} placeholders resolve through decrypt at deploy time., test_create_and_list_return_metadata_only() (+7 more)

### Community 72 - "test_nginx_renderer.py"
Cohesion: 0.11
Nodes (40): NginxProvider, Any, ValueError, The only production provider in Phase 4., Params for the whitelisted ``nginx.apply`` operation., Where a route's fragment lands, so the service can name it in events., Rendering refused the input. Always a bug or a corrupt row, never a leak., RenderError (+32 more)

### Community 73 - "domain_service.py"
Cohesion: 0.10
Nodes (40): Domain, One DNS name an organization is proving it controls. ``name`` is canonical (see…, What the lifecycle should do with an observation., VerificationDecision, _actor(), apply_decision(), _bad_name(), claim_verified_name() (+32 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "typing"
Cohesion: 0.04
Nodes (99): asyncio, Cross-entity global search powering the Ctrl+K command palette. Every section…, Canonical Redis pub/sub channel names shared by API, workers and WS hub., Error taxonomy and the single place where API error envelopes are shaped. Every…, get_logger(), Structured logging via structlog. Every log record carries timestamp, level,…, Redis-backed fixed-window rate limiting as a FastAPI dependency factory. Auth-…, get_redis() (+91 more)

### Community 76 - "server_service.py"
Cohesion: 0.05
Nodes (85): agent_enroll(), agent_heartbeat(), agent_hello(), claim_operation(), _presented_token(), DbDep, post, Request (+77 more)

### Community 77 - "domains.py"
Cohesion: 0.11
Nodes (39): create_domain(), delete_domain(), _enqueue_verification(), get_domain(), list_domain_routes(), list_domains(), _project_names(), alias (+31 more)

### Community 78 - "incidents.py"
Cohesion: 0.13
Nodes (33): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+25 more)

### Community 79 - "test_phase2_secrets.py"
Cohesion: 0.19
Nodes (21): _env(), _project(), Phase 2 secrets: layered scope, immutable versions, rollback, isolation. Two…, Two racing rotations must both be kept and never share a version number., Another tenant cannot read, rotate, roll back or even enumerate the secret., The documented example: same key at three scopes; most specific wins., A ref declared in the project base config resolves for its environments., _resolved() (+13 more)

### Community 80 - "AuthContext.tsx"
Cohesion: 0.04
Nodes (50): Membership, Role, User, RolesPage, UsersPage, AuthContext, AuthProvider(), AuthState (+42 more)

### Community 81 - "monitor_service.py"
Cohesion: 0.14
Nodes (39): assert_safe_url_async(), Async wrapper around :func:`assert_safe_url`; DNS runs off the loop., MonitorStatus, Monitor, MonitorCheck, One probe. Targets are polymorphic since Phase 4 (domain-model.md §2.6).…, _active_incident(), _audit() (+31 more)

### Community 82 - "canonicalize_name"
Cohesion: 0.12
Nodes (32): canonicalize_name(), canonicalize_path(), _check_labels(), _check_not_ip(), hostname_is_covered(), _idna(), InvalidName, is_valid_path() (+24 more)

### Community 83 - "tests/conftest.py"
Cohesion: 0.20
Nodes (8): configure_test_env(), Test bootstrap: pin every cached setting BEFORE the first ``app`` import. The…, KEY=VALUE pairs from the repo .env (first definition wins); never logged., Export the exact settings the app caches; host values cannot leak through., _read_dot_env(), base64, os, sys

### Community 84 - "test_schemas_server.py"
Cohesion: 0.21
Nodes (22): Payload for registering a server., Partial update. ``tags`` replaces the full set when provided., ServerCreate, ServerUpdate, _base(), parametrize, Unit tests for app.schemas.server (validation only, no I/O)., test_empty_ip_is_allowed_but_whitespace_collapses() (+14 more)

### Community 85 - "sessions.py"
Cohesion: 0.15
Nodes (16): list_sessions(), CurrentUser, DbSessionDep, delete, get, Request, UUID, Session routes: list active sessions, revoke own or (with user.manage) any. (+8 more)

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "operation_service.py"
Cohesion: 0.11
Nodes (42): OperationStatus, Lifecycle of one node operation (node-agent-architecture.md §5.1).…, Operation, One whitelisted action for one node, with a CAS lifecycle. ``attempts`` is…, _active_org(), cancel_operation(), claim_operation(), ensure_dispatchable() (+34 more)

### Community 88 - "LogLine"
Cohesion: 0.08
Nodes (31): _decode_frame(), _max_log_id(), _poll_new_lines(), Parse a Redis pub/sub frame ``{ts, stream, message}`` into a LogLine., Highest persisted log id for a container (poll fallback watermark)., Fetch log rows persisted after ``last_seen['id']`` (poll fallback)., Live-tail a container's logs. Primary source is the Redis pub/sub channel…, stream_container_logs() (+23 more)

### Community 89 - "Settings"
Cohesion: 0.14
Nodes (6): field_validator, model_validator, Username from :attr:`database_url`, or ``None`` if it is unparseable., Validated application settings (loaded from environment / .env)., Settings, BaseSettings

### Community 90 - "DomainStatus"
Cohesion: 0.11
Nodes (28): DomainStatus, Ownership-verification lifecycle of a Domain (domain-routing.md §4). ``STALE``…, The state a domain flip forces on its routes, or ``None`` to leave them., route_config_state_for(), _affected_node_ids(), _audit_action(), task, UUID (+20 more)

### Community 91 - "validate_config"
Cohesion: 0.06
Nodes (34): EnvironmentBase, EnvironmentUpdate, _normalise_environment_type(), field_validator, Shared environment fields., Partial environment update; omitted fields are left untouched. Config is…, field_validator, collect_secret_refs() (+26 more)

### Community 92 - "Path"
Cohesion: 0.12
Nodes (15): Path, An unloadable CA file must error, never silently fall back to no verify., A throwaway key + self-signed cert for ``localhost`` (real handshakes)., A one-shot HTTPS server; records a failed handshake instead of crashing., A real handshake against a self-signed server must fail verification., Trusting that same cert as a CA lets the identical handshake through., A link-local URL over plain HTTP must fail before any request or write., _self_signed_cert() (+7 more)

### Community 93 - "org_scope"
Cohesion: 0.09
Nodes (43): current_scope(), org_scope(), ``'org'``, ``'system'`` or ``'unset'``., Run the enclosed block as a single organization. Nesting the *same* org is a…, _entity_exists(), Whether *id_* exists **for this organization**. Runs inside the socket's…, _create_server(), _guc() (+35 more)

### Community 94 - "test_phase21_secret_version_integrity.py"
Cohesion: 0.18
Nodes (18): _app_role_dsn(), _owner_dsn(), _probe(), Phase 2.1 — ``secret_versions`` is append-only in the **database**, not just in…, Immutability is a database guarantee, not merely a missing code path. The owner…, The legitimate append paths keep working under the guard., The documented deletion policy: purging a Secret cascades its history., RLS is preserved: another tenant cannot see a version row, even by id. (+10 more)

### Community 95 - "StepLine"
Cohesion: 0.18
Nodes (12): LogLevel, _commit_short(), _pace(), Deployment runner port plus a faithful simulated implementation.…, Stream output lines for *step_name*; raise StepFailure to fail it., Deterministic per-line delay between 0.05s and 0.35s., Everything a runner needs to execute one deployment., One streamed output line for a step. (+4 more)

### Community 96 - "NexusOps (self-hosted infrastructure management and monitoring platform)"
Cohesion: 0.20
Nodes (10): mailpit service (dev SMTP sink + web UI :8025), NexusOps compose stack (8 services on one network), HIGH finding: redirect-following SSRF in uptime monitors (fixed: follow_redirects=False + per-hop guard), SSRF guard (assert_safe_url, per-redirect-hop validation, assert_safe_tcp_endpoint), Mailpit SMTP port internal-only (host-side injection needs extra mapping), Host port knobs (NEXUSOPS_HTTP_PORT/POSTGRES/REDIS/MAILPIT/VITE), SPA entry point (loads /src/main.tsx, dark color-scheme), Uptime monitors -> incidents -> notifications flow (+2 more)

### Community 97 - "REST API surface (/api/v1)"
Cohesion: 0.29
Nodes (7): Cursor (keyset) and offset pagination envelopes, Permission model (data-driven registry, require_permission, wildcard scopes), REST API surface (/api/v1), RBAC registry (PERMISSIONS + ROLE_MATRIX + scope_matches), Adding a new resource: 7-step checklist (model -> migration -> schemas -> service -> router -> tests -> frontend), Alembic migration workflow (autogenerate, models __init__ export, entrypoint apply), Command palette (Ctrl/Cmd+K)

### Community 98 - "phase3.spec.ts"
Cohesion: 0.12
Nodes (18): EDGE, MAILPIT, ADMIN, Bootstrap, bootstrapVia(), test, ADMIN, openProject() (+10 more)

### Community 99 - "run_async"
Cohesion: 0.20
Nodes (14): T, Run *coroutine* on a dedicated event loop (Celery workers are sync). The loop…, run_async(), _drained(), The drain must not become a delay on the hot path for quiet tasks., test_flush_is_a_noop_when_nothing_is_pending(), _answer(), _boom() (+6 more)

### Community 100 - "Secrets Architecture"
Cohesion: 0.14
Nodes (14): 10. Resolution flow at deploy time, 2.1 Resolution runs inside org scope, 2.2 Migration mapping (applied by `b2c3d4e5f6a7`), 2. Scope model (org / project / environment layering) — **shipped**, 3.1 What this fixed, 3. SecretVersion — append-only history (**shipped in Phase 2**), 4.1 Audit event at resolution time, 4. Resolution authorization (+6 more)

### Community 101 - "README.md - NexusOps overview"
Cohesion: 0.30
Nodes (14): docker-compose.dev.yml - dev overlay, docker-compose.docker-sock.yml - docker socket override, docker-compose.yml - full stack definition, docs/agent.md - agent guide, docs/api.md - API guide, Append-only audit log (Postgres BEFORE UPDATE OR DELETE trigger), docs/architecture.md - system architecture, docs/deployment.md - deployment and operations guide (+6 more)

### Community 102 - "env.py"
Cohesion: 0.24
Nodes (10): _database_url(), Alembic environment: metadata comes from app.models, URL from app settings., Migrations run as the table **owner**, never as the application role. The owner…, Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online(), Owner-role DSN for Alembic and the container entrypoint. Migrations… (+2 more)

### Community 103 - "apply_scope_to_session"
Cohesion: 0.08
Nodes (34): dispose_engine(), get_sessionmaker(), async_sessionmaker, AsyncSession, apply_scope_to_session(), Push the current scope onto *db*'s connection immediately. Needed only when a…, collect_recent_logs(), Pull recent logs from running containers of a real host. Simulated hosts are… (+26 more)

### Community 104 - "_exec"
Cohesion: 0.14
Nodes (26): An explicit non-DEV classification survives the corrective migration. The…, test_only_dev_defaulted_rows_are_corrected(), Only the previous migration's ``PROD`` output is corrected. A row already…, test_correction_preserves_operator_set_values(), _exec(), _owner_dsn(), Statement, Run statements in one transaction as the owner (committed on success). (+18 more)

### Community 105 - "redis service (Redis 7, no persistence, loopback :6390)"
Cohesion: 0.22
Nodes (11): redis service (Redis 7, no persistence, loopback :6390), WebSocket API (/api/v1/ws handshake, frames, limits), WebSocket channels (global, server-metrics, container-logs, deployment-logs, incidents), Deployment engine (queue_deployment / execute_deployment / sweeper backstop), Real-time spine: PostgreSQL system_events + Redis pub/sub, Rollback as a new deployment (rollback_of_id), WebSocket hub (framework-thin, Redis fan-in, per-socket queues), Test suites (pytest unit+integration, vitest, Playwright e2e) (+3 more)

### Community 106 - "NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)"
Cohesion: 0.18
Nodes (12): Agent security model (one-way telemetry, no command channel), Agent enrollment token (X-Agent-Token, nxa_..., SHA-256 at rest), Agent heartbeat exponential backoff (cap 5 min, exit 1 on revoked token), agent/install.sh (enrollment installer), Agent metrics collection (/proc statvfs Docker socket), NexusOps agent (stdlib-only Python, agent/nexusops_agent.py), Agent systemd hardening (ProtectSystem=strict, NoNewPrivileges), Agent ingest API (POST /agent/hello, POST /agent/heartbeat) (+4 more)

### Community 107 - "App.tsx"
Cohesion: 0.05
Nodes (40): SearchResult, AlertsPage, App(), DeploymentDetailPage, DomainListPage, EnvironmentDetailPage, IncidentDetailPage, LoginPage (+32 more)

### Community 108 - "RealDockerProvider"
Cohesion: 0.14
Nodes (7): ContainerInfo, Normalized view of a container as reported by any provider., T, Execute an SDK call with one short retry, normalizing failures., Two short samples give real cpu/net deltas without streaming., Talks to a real docker daemon over ``unix://`` or ``tcp://``., RealDockerProvider

### Community 109 - "Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)"
Cohesion: 0.25
Nodes (9): API keys (X-API-Key, nxo_..., scope intersection), First boot sequence (api entrypoint migrates, compose never seeds), Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test), Makefile workflows (up/test/lint/typecheck/migrate/seed), HIGH finding: API-key scope bypass for superadmin-owned keys (fixed: scope intersection first), Security audit 2026-09 (26 raw findings -> 20 confirmed, all fixed), HIGH finding: known seed superadmin + API key backdoor (fixed: NEXUSOPS_ALLOW_SEED opt-in, one-time password), Threat model (edge attacker, malicious agent, curious operator, leaked token, SSRF) (+1 more)

### Community 111 - "organization_service.py"
Cohesion: 0.16
Nodes (25): add_member(), create_organization(), get_organization(), membership_for_user(), AsyncSession, Membership, Organization, Request (+17 more)

### Community 112 - "test_app_gating.py"
Cohesion: 0.44
Nodes (8): _app_for_environment(), MonkeyPatch, ENVIRONMENT gating contract: docs exposure and HSTS (see .env.example).…, create_app() with get_settings() patched to the given environment., test_non_production_does_not_emit_hsts(), test_non_production_keeps_docs_and_schema(), test_production_emits_hsts(), test_production_hides_docs_and_schema()

### Community 113 - "dnsmock.py"
Cohesion: 0.12
Nodes (24): resolver(), answer(), encode_name(), encode_txt(), forward(), main(), parse_question(), TXT rdata: one or more length-prefixed strings, each ≤ 255 bytes. (+16 more)

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "v1/health.py"
Cohesion: 0.20
Nodes (13): liveness(), get, Response, Health probes: liveness (always cheap) and readiness (checks dependencies).…, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness(), HealthOut (+5 more)

### Community 116 - "test_tenancy_allowlist.py"
Cohesion: 0.20
Nodes (14): AST, _actual_callers(), _calls_system_scope(), _module_path(), Path, The system-scope allowlist is the only fence around the tenancy carve-out.…, Every module that could open a system scope: ``app/`` plus the scripts., No module may lift tenant isolation without being named in the list. (+6 more)

### Community 117 - "resolve_auth"
Cohesion: 0.13
Nodes (22): get_current_user(), get_identity(), get_optional_user(), DbSessionDep, Request, Resolve credentials **and** the active organization. ``require_org=False`` is…, Org-scoped authentication: identity + validated active organization. Also…, Identity-only authentication for the pre-org exemptions (no scope). (+14 more)

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
Cohesion: 0.18
Nodes (10): list_servers(), list_tags(), Depends, ReadCtx, All tags with their server usage counts., List servers with filters, search and pagination., computed_field, Whether the node has reported capabilities at all (v2 hello). (+2 more)

### Community 122 - "server_payload"
Cohesion: 0.06
Nodes (39): A valid POST /servers body with per-test overrides., server_payload(), test_token_cannot_claim_a_foreign_tenants_node(), test_v1_heartbeat_keeps_the_204_contract(), Regression: a superadmin-owned key is still limited to its scope list. The…, test_scoped_api_key_cannot_exceed_its_grant(), _create_server(), Server CRUD, cascade delete, audit trail rows and audit immutability. (+31 more)

### Community 123 - "_run_migration"
Cohesion: 0.18
Nodes (13): UUID, Phase 2.2 — the environment-type correction follows the documented precedence.…, Create one legacy (application-scoped) environment per case., Every branch of the slug-first rule, end to end through ``head``., _seed_legacy(), test_recognised_slug_alias_wins_over_a_conflicting_name(), Upgrade ``database`` to ``revision`` through the app's own settings path.…, A fresh database reaches the same shape the models describe. (+5 more)

### Community 124 - "middleware.py"
Cohesion: 0.11
Nodes (20): ASGIApp, AccessLogMiddleware, Request, Response, HTTP middleware: request ids, security headers, structured access logs., Baseline hardening headers on every API response., RequestIDMiddleware, SecurityHeadersMiddleware (+12 more)

### Community 125 - "OperationError"
Cohesion: 0.13
Nodes (19): _demux_docker_stream(), _docker_error(), execute_operation(), OperationError, _process_pending_operations(), Exception, A stable, sanitized failure contract for the control plane., Re-validate the operation's parameters locally, against a closed shape. (+11 more)

### Community 126 - "list_operations"
Cohesion: 0.21
Nodes (15): cancel_operation(), create_operation(), get_operation(), list_operations(), DbDep, Depends, get, post (+7 more)

### Community 127 - "list_audit_logs"
Cohesion: 0.29
Nodes (7): list_audit_logs(), datetime, DbSession, Depends, get, PageParamsDep, Newest-first audit trail with optional filters. No write routes exist for this…

### Community 137 - "Page"
Cohesion: 0.09
Nodes (21): AuditEntry, Page, AuditLogPage, ContainerListPage, PaginationProps, AuditLogPage(), AuditRow, formatTimestamp() (+13 more)

### Community 146 - "test_auth_multi_org.py"
Cohesion: 0.24
Nodes (17): _latest_audit(), _latest_event(), _list_ids(), Any, UUID, Phase 3.1 — pre-organization auth events are instance-level and tenant-…, No account => no actor => a system instance-level row, as before., A NULL-org auth fact is not reachable through either organization. (+9 more)

### Community 147 - "20260922_1000-a3f1c8d24b6e_add_tenancy_foundation.py"
Cohesion: 0.20
Nodes (12): _app_role_credentials(), _assert_fully_backfilled(), _backfill_org_ids(), _drop_constraint(), add tenancy foundation Phase 1 of the platform roadmap: organizations,…, Carry a value into a PL/pgSQL block. ``CREATE ROLE``/``ALTER ROLE`` are utility…, Application role name/password from settings (never hard-coded)., Point every pre-existing row at the bootstrap organization. ``audit_logs`` is… (+4 more)

### Community 148 - "postgres service (PostgreSQL 17, loopback :5433)"
Cohesion: 0.29
Nodes (7): postgres service (PostgreSQL 17, loopback :5433), Fernet encryption at rest (ENCRYPTION_KEY, write-once), Backups (pgdata volume, nightly pg_dump, ephemeral Redis), Required secrets (POSTGRES_PASSWORD, JWT_SECRET >= 32 chars, ENCRYPTION_KEY Fernet), Production hardening checklist (secrets, ENVIRONMENT, no seed, TLS, rotation), Compose vs host network namespaces (postgres:5432 vs 127.0.0.1:5433), Simulation mode (SIMULATION_MODE)

### Community 149 - "phase4.spec.ts"
Cohesion: 0.10
Nodes (15): frontend_e2e_fixtures_expect, AGENT, DNS_CONTROL, docker(), DomainBody, HttpResult, NODE_CONTEXT, NodeDetail (+7 more)

### Community 150 - "nexusops-understand.mjs"
Cohesion: 0.33
Nodes (5): COMMON, meta, out, READERS, SCHEMA

### Community 151 - "Invisible account lockout (5 fails -> 15 min, enumeration resistance)"
Cohesion: 0.33
Nodes (6): Invisible account lockout (5 fails -> 15 min, enumeration resistance), Unified error envelope (code, message, request_id), Per-IP rate limiting (Redis fixed window), Request lifecycle (edge -> middleware -> rate limit -> deps -> router), Client IP resolution (resolve_client_ip, TRUSTED_PROXY_CIDRS, XFF overwrite), EmailStr rejects reserved domains (login 422 on .test/.local/.arpa)

### Community 152 - "nginx_capability"
Cohesion: 0.11
Nodes (20): _listener_ownership(), _listening_ports(), _live_bundle_id(), _live_files(), _nginx_binary(), nginx_capability(), _nginx_owned_ports(), _nginx_status() (+12 more)

### Community 153 - "DashboardPage.tsx"
Cohesion: 0.12
Nodes (14): DashboardSummary, DashboardPage, asFeedItem(), badgeLevel(), DashboardPage(), FeedItem, formatTimestamp(), MetaInfo (+6 more)

### Community 154 - "nexusops-draft.mjs"
Cohesion: 0.40
Nodes (4): DOCS, meta, SPINE, VERIFY_RULES

### Community 155 - "notification_sender.py"
Cohesion: 0.15
Nodes (18): NotificationError, Any, BaseException, Exception, Low-level notification transports: SMTP email and outgoing webhooks. These…, POST *payload* as JSON to *url*; 2xx is success, anything else raises. Response…, Raised when a delivery attempt fails. Message is safe to persist., Bounded, single-line, content-free error reason. (+10 more)

### Community 156 - "nexusops-challenge.mjs"
Cohesion: 0.33
Nodes (5): CHALLENGE_COMMON, meta, RESEARCH_COMMON, SCHEMA, TASKS

### Community 157 - "test_agent_ingestion.py"
Cohesion: 0.30
Nodes (10): _enrolled(), _heartbeat(), Agent ingest pipeline: hello, heartbeat, staleness transitions, events., A container absent from a later heartbeat is gone from the daemon., A payload at the agent's cap may be truncated — absence proves nothing., test_heartbeat_at_container_cap_skips_reconciliation(), test_heartbeat_removes_vanished_containers(), test_heartbeat_updates_status_metrics_and_containers() (+2 more)

### Community 158 - "test_schemas_agent.py"
Cohesion: 0.12
Nodes (35): AgentContainerIn, AgentHeartbeatIn, AgentHelloIn, Observed container state reported by an agent., Periodic metrics + observed containers from an enrolled agent. Network counters…, First contact from an agent after enrollment; fills static host facts., _container(), _heartbeat() (+27 more)

### Community 159 - "test_run_async_publishes_frames_scheduled_by_the_commit_hook"
Cohesion: 0.29
Nodes (5): _FakeDb, Stands in for an ``AsyncSession`` whose only job here is ``sync_session``. A…, The shape of a worker task whose last statement is a commit., test_run_async_publishes_frames_scheduled_by_the_commit_hook(), commit_then_return()

### Community 160 - "main"
Cohesion: 0.17
Nodes (13): _build_hello_payload(), _enroll(), _interruptible_sleep(), main(), memory_total_mb(), os_info(), persist_token(), Atomically store *token* at 0600. Temp file in the same directory + fsync +… (+5 more)

### Community 161 - "monitor_transport.py"
Cohesion: 0.08
Nodes (23): CheckOutcome, coerce_headers(), _decode(), get_transport(), MonitorTransport, Any, BaseException, Protocol (+15 more)

### Community 162 - "test_notifications.py"
Cohesion: 0.36
Nodes (9): NotificationDelivery, _channel(), _delivery(), UUID, Notification channel + delivery-log endpoints. Regression coverage for GET…, The same event frame consumed twice queues ONE delivery per channel. Every API…, test_dispatch_frame_is_idempotent_across_workers(), test_list_deliveries_filters_by_channel() (+1 more)

### Community 163 - "redact_mapping"
Cohesion: 0.18
Nodes (15): _is_sensitive_key(), Substring match on a normalised key so header-style names are caught too.…, Return a copy of *data* with sensitive values replaced. Used by audit metadata…, redact_mapping(), _bounded(), Keep one agent report from becoming an unbounded row. The agent is…, parametrize, Unit tests for app.core.logging redaction (pure functions only). (+7 more)

### Community 164 - "AgentClient"
Cohesion: 0.15
Nodes (8): AgentClient, _docker_raw(), A verifying TLS context. Verification is never disabled. A private/self-hosted…, Refuse to send credentials over plain HTTP to a non-loopback server. The…, One raw Docker API call; returns ``(status, body_bytes)``., _tls_context(), _UnixHTTPConnection, SSLContext

### Community 165 - "SecretsPage.tsx"
Cohesion: 0.13
Nodes (13): SecretRow, SecretsPage, SecretScopeBadge(), CreateSecretModal(), CreateSecretPayload, DeleteSecretModal(), errorMessage(), formatTimestamp() (+5 more)

### Community 166 - "monitoring.py"
Cohesion: 0.20
Nodes (8): Celery application: periodic cadences live here, dynamic work is claimed…, task, Monitor dispatch: claim due monitors atomically, run their checks., Claim up to CLAIM_BATCH due monitors and execute each check.…, run_due_monitors(), _run(), celery, celery_schedules

### Community 167 - "AuthContext"
Cohesion: 0.05
Nodes (67): active_memberships(), _attach_organization(), AuthContext, _load_organization(), _load_permissions(), membership_for_org(), _org_id_from_header(), permission_dep() (+59 more)

### Community 168 - "_run"
Cohesion: 0.33
Nodes (7): _containers_for(), task, Deterministic smooth value in [base-amplitude, base+amplitude]., Stable per-server container set; one container cycles EXITED occasionally., simulation_tick(), _run(), _wave()

### Community 170 - "test_agent_contract.py"
Cohesion: 0.20
Nodes (15): agent_fixture(), _load_agent(), _patch_stats(), Any, fixture, MonkeyPatch, Contract tests: the shipped agent's payloads must satisfy the ingest schemas.…, One-shot docker stats reduce to cpu/mem/limit fields the schema accepts, with… (+7 more)

### Community 171 - "20261009_1000-c3d4e5f6a7b8_enforce_secret_version_integrity.py"
Cohesion: 0.48
Nodes (6): _clear_app_role_guc(), downgrade(), Phase 2.1 — enforce append-only ``secret_versions`` in the database. Phase 2…, Publish the app-role name to the migration GUC the revoke block reads., _set_app_role_in_guc(), upgrade()

### Community 172 - "_FakeAsyncClient"
Cohesion: 0.22
Nodes (3): _FakeAsyncClient, _FakeRequestObj, Scripted httpx.AsyncClient: responses keyed by absolute request URL.

### Community 173 - "scope_matches"
Cohesion: 0.15
Nodes (13): Check an API-key scope list against a required permission. Supports exact match…, scope_matches(), parametrize, test_scope_matches_truth_table(), 1. Principles (already true in the codebase, kept), 2. Registry changes (Phase 1 + new subsystems), 3. The five system roles (target), 4. Grants (resource-level access; design now, later phase) (+5 more)

### Community 174 - "configure_logging"
Cohesion: 0.50
Nodes (4): configure_logging(), _orjson_dumps(), Any, Configure structlog + stdlib logging once at process start. Everything…

### Community 175 - "2. Entities"
Cohesion: 0.12
Nodes (15): Alias for :attr:`extra`, so the API can expose open-ended agent facts. The…, 2.1.1 ApiKey org binding detail, 2.2.1 Environment promotion detail — **shipped in Phase 2**, 2.2 Delivery (existing models, extended), 2.3 Infrastructure — Nodes, 2.4 Routing & TLS (new subsystem), 2.5 Secrets (re-scoped — **shipped in Phase 2**), 2.6 Observability (existing, org-scoped via parents) (+7 more)

### Community 176 - "Platform Security Model — NexusOps"
Cohesion: 0.11
Nodes (18): 10.1 Node revocation playbook (compromised node / leaked agent token), 10.2 Key compromise playbook, 10. Incident response, 1.1 Real vs simulated today (do not mistake one for the other), 1. Scope, stance, and simulation honesty, 2. Assets, 3. Trust boundaries, 4. Tenant isolation model (summary) (+10 more)

### Community 177 - "create_operation"
Cohesion: 0.50
Nodes (4): create_operation(), Request, Queue one whitelisted action for one node in the caller's organization.…, 5.4 The boundary, as built (creation / claim+result / delivery)

### Community 178 - "network_rates"
Cohesion: 0.33
Nodes (6): build_facts(), network_rates(), network_total_bytes(), Sum rx/tx bytes over non-loopback interfaces from /proc/net/dev., Return (rx_kb_s, tx_kb_s) or ``(None, None)`` when not measurable., Open-ended host facts, stored in the node's flexible JSONB blob. Deliberately…

### Community 179 - "test_corrects_legacy_environment_types"
Cohesion: 0.50
Nodes (4): Every case is classified as documented, ids and ownership intact., Insert one legacy environment per case, in two organizations., _seed_typed_environments(), test_corrects_legacy_environment_types()

### Community 180 - "websocket_endpoint"
Cohesion: 0.67
Nodes (3): websocket, Hand the socket to the hub (auth handshake handled there)., websocket_endpoint()

### Community 181 - "_nginx_apply"
Cohesion: 0.13
Nodes (17): _fsync_dir(), _nginx_apply(), Materialize the bundle under ``staged/<id>/`` and return that directory., Build a self-contained config for ``nginx -t`` over the staged tree. The…, Move the staged tree over the live one, keeping the previous as backup., Put the previous known-good tree back. Returns whether it was possible., Stage → validate → swap → reload, with a rollback on a failed reload., Persist the last apply outcome atomically (temp + rename). (+9 more)

### Community 182 - "_nginx_bootstrap"
Cohesion: 0.16
Nodes (16): _insert_http_includes(), _nginx_bootstrap(), _nginx_config_test(), _nginx_failure_summary(), _nginx_running(), _pid_alive(), Reload nginx via ``-s reload``, falling back to a SIGHUP of the master., Idempotent, minimal, reversible hook-up of the managed include. The only change… (+8 more)

### Community 183 - "8. Upstream binding and re-render triggers"
Cohesion: 0.33
Nodes (6): 8.1 Binding rules, 8.2 Certificate selection rule (this doc owns it), 8.3 Re-render triggers, 8.4 Drift, 8.5 How deployments hook routing (post-deploy route sync), 8. Upstream binding and re-render triggers

### Community 184 - "Multi-Tenancy Architecture"
Cohesion: 0.15
Nodes (11): Whether the runtime connection is the RLS-enforced application role. False…, 10. Migration (Phase 1), 1. Tenancy invariants, 2.1 Org creation — v1 decision, 3. The session guard (the mechanical layer), 4. Background jobs, 5. WebSockets, 6. Agents (+3 more)

### Community 185 - "NotificationChannel"
Cohesion: 0.25
Nodes (16): NotificationChannel, A delivery target (email address / webhook endpoint). ``config_ciphertext``…, EmailConfig, _audit(), create_channel(), delete_channel(), encrypt_config(), _normalize_events() (+8 more)

### Community 186 - "maintenance.py"
Cohesion: 0.13
Nodes (22): aggregate_metrics(), _run(), _collect_logs(), expire_operations(), _run(), expire_sessions(), _run(), task (+14 more)

### Community 187 - "Conflict"
Cohesion: 0.15
Nodes (25): Conflict, create_role(), delete_role(), effective_permissions(), get_role(), list_roles(), permissions_for_role(), AsyncSession (+17 more)

### Community 188 - "instant_pacing"
Cohesion: 0.40
Nodes (4): instant_pacing(), fixture, MonkeyPatch, Remove the per-line sleeps; pacing bounds are asserted separately.

### Community 189 - "servers.py"
Cohesion: 0.17
Nodes (17): create_enrollment_token(), _enrollment_created(), _enrollment_out(), list_enrollment_tokens(), Node endpoints: CRUD, tags, agent enrollment tokens. The domain entity is the…, Mint one single-use enrollment token in the caller's organization. The org…, Enrollment tokens in the active organization, newest first. The response type…, Revoke an unused enrollment token immediately. (+9 more)

### Community 190 - "resolve_secrets_for_environment"
Cohesion: 0.12
Nodes (20): _collect_refs(), Exception, A ``${secret:KEY}`` reference could not be resolved. Fail-closed. Carries…, One successfully resolved reference: metadata for audit, no value., Outcome of resolving an environment's config references., Backwards-compatible wrapper around :func:`config_service.collect_secret_refs`., Resolve every ``${secret:KEY}`` reference an environment's config names.…, resolve_secrets_for_environment() (+12 more)

### Community 191 - "UUID"
Cohesion: 0.19
Nodes (14): delete_server(), _detail(), get_server(), AsyncSession, delete, patch, UUID, Full server view with recent timeline events and container counts. (+6 more)

### Community 192 - "ControlHandler"
Cohesion: 0.22
Nodes (7): BaseHTTPRequestHandler, clear_record(), ControlHandler, in_zone(), The journey's only way to publish a record — no shell, no shared volume., set_record(), snapshot()

### Community 193 - "test_migration_drift.py"
Cohesion: 0.25
Nodes (7): alembic_autogenerate, alembic_migration, Model / migration drift: the schema in the database must match the models.…, ``Base.metadata`` and the migrated database must describe the same schema., The DB whitelist and ``OperationType`` are the same closed set. The migration…, test_models_and_migrations_do_not_drift(), test_operations_type_check_matches_the_enum()

### Community 194 - "node_proxy_status"
Cohesion: 0.24
Nodes (11): node_proxy_status(), node_route_targets(), get, Provider capability, last apply and drift state for one node. Bounded by…, Containers on this node that a route can point at, with usable ports. Only…, A container that can actually back a route on this node., UpstreamContainerOut, container_out() (+3 more)

### Community 195 - "channel.py"
Cohesion: 0.27
Nodes (8): ChannelType, ChannelBase, ChannelCreate, ChannelUpdate, model_validator, Schemas for notification channels and delivery records. Channel configuration…, SecretHeader, WebhookConfig

### Community 196 - "20261010_1200-f4a5b6c7d8e9_phase4_domains_and_routes.py"
Cohesion: 0.31
Nodes (9): downgrade(), _drop_tenant_policies(), _grant(), _in_list(), Phase 4 — domains, routes and the routing schema. Adds, in one migration with a…, Grant the app role on *table*; the migration role GUC carries the name. The…, The two-policy shape every tenant table uses: tenant + system scope., _tenant_policies() (+1 more)

### Community 197 - "test_error_logging.py"
Cohesion: 0.22
Nodes (4): Regression: the catch-all 500 handler must not log raw exception text.…, _SpyLogger, test_unhandled_exception_handler_logs_class_not_message(), fastapi_testclient

### Community 198 - "Product Roadmap — NexusOps Multi-Tenant Platform"
Cohesion: 0.11
Nodes (19): 0. Stance, 10. Phase 7 — Teams, grants & custom roles, 11. Phase 8 — Backups, 12. Phase 9 — Billing & metering, 13.1 Scope-creep gates — what must be true before each expansion, 13. First commercially meaningful version, 14. Biggest risks (short form), 15. Reading order (+11 more)

### Community 199 - "Platform Vision — NexusOps"
Cohesion: 0.20
Nodes (10): 1. Where NexusOps is today, 2.1 What we are NOT building, 2.2 The wedge (differentiation), 2. The direction, 3. Guiding principles, 4. Customer journey (target), 5.1 Architecture overview (target), 5. Control plane / data plane boundary (+2 more)

### Community 200 - "enqueue.py"
Cohesion: 0.39
Nodes (8): after_commit(), _on_commit(), _on_rollback(), Any, AsyncSession, Deferred Celery handoff: enqueue only after the creating transaction commits. A…, Run ``factory`` once the current transaction commits. ``label`` names the work…, _run()

### Community 201 - "test_monitors_incidents.py"
Cohesion: 0.31
Nodes (8): _create_monitor(), Monitor checks driving the full down -> incident -> recovery lifecycle., Regression: probe headers and URL query credentials never leave the API. Probe…, A monitor's checks, incidents and timeline all live in its organization, so the…, test_check_now_endpoint_runs_immediately(), test_down_then_recover_lifecycle(), test_monitor_responses_mask_probe_credentials(), test_notification_pipeline_queues_delivery_for_down_event()

### Community 202 - "journey.spec.ts"
Cohesion: 0.29
Nodes (4): ADMIN, formLogin(), uiGoto(), UNIQUE

### Community 203 - "build_capabilities"
Cohesion: 0.29
Nodes (7): build_capabilities(), docker_capability(), _docker_socket(), Report Docker availability by *talking to the daemon*, not by path lookup. A…, systemd is present when it is actually running as the init system., Everything the control plane uses to decide what it may ask this node.…, systemd_capability()

### Community 204 - "ApplicationBase"
Cohesion: 0.40
Nodes (4): ApplicationBase, Any, field_validator, Shared application fields; ``build_config`` is a free-form dict.

### Community 205 - "sweep_deployments"
Cohesion: 0.29
Nodes (7): task, Execute one queued deployment. The engine owns all state transitions., Re-enqueue deployments the broker lost; fail ones whose worker died.…, run_deployment(), _run(), sweep_deployments(), _run()

### Community 206 - "20261008_1200-b2c3d4e5f6a7_add_projects_and_environments.py"
Cohesion: 0.53
Nodes (5): downgrade(), _drop_constraint(), _quoted_list(), Phase 2 — projects & environments: env promotion, config, secret versions. This…, upgrade()

### Community 207 - "20261009_1300-a1b2c3d4e5f6_add_phase3_nodes_and_agent_v2.py"
Cohesion: 0.40
Nodes (4): _grant(), Phase 3 — Nodes & Agent v2 schema. Adds, in one migration with a single head: *…, Grant the app role on *table*; the migration role GUC carries the name. The…, upgrade()

### Community 208 - "_validate_bundle"
Cohesion: 0.40
Nodes (5): _allowed_bundle_path(), The bundle fingerprint — byte-identical to the control plane's algorithm.…, Independently validate a bundle. Anything unexpected is refused., _tree_fingerprint(), _validate_bundle()

### Community 209 - "20261004_1200-e7c4a2b9d1f3_add_operations_framework.py"
Cohesion: 0.50
Nodes (3): _quoted_list(), Add the operations framework table (node-agent-architecture.md §5). One tenant-…, upgrade()

### Community 210 - "get_meta"
Cohesion: 0.40
Nodes (5): get_meta(), DbSessionDep, get, Public metadata; identity fields appear only for valid credentials., OptionalUser

### Community 212 - "sweep_routes"
Cohesion: 0.67
Nodes (4): Keep every routed node's live configuration matching the desired bundle. Two…, sweep_routes(), _candidates(), _run()

### Community 213 - "sweep_servers"
Cohesion: 0.50
Nodes (4): task, Flag silent servers OFFLINE, recover returning ones. Safe to overlap., sweep_servers(), _run()

### Community 214 - "test_created_at_defaults.py"
Cohesion: 0.50
Nodes (3): created_at server defaults must evaluate per insert, not at table creation., Regression: system_events and audit_logs shipped with DEFAULT 'now()' (quoted…, test_audit_and_event_created_at_defaults_are_dynamic()

### Community 215 - "test_remove_honours_force_and_never_shells"
Cohesion: 0.50
Nodes (3): test_container_start_maps_to_a_fixed_api_call(), fake_raw(), test_remove_honours_force_and_never_shells()

### Community 216 - "Domain Model — NexusOps as a Multi-Tenant Platform"
Cohesion: 0.50
Nodes (4): 0. Design stance, 1. The hierarchy, 3. Cross-cutting decisions, Domain Model — NexusOps as a Multi-Tenant Platform

### Community 217 - "4. Operations framework (added in this pass)"
Cohesion: 0.67
Nodes (3): OperationSpec, Everything the control plane needs to know about one operation type.…, 4. Operations framework (added in this pass)

### Community 218 - "_seed_legacy_data"
Cohesion: 0.67
Nodes (3): The pre-Phase-2 shapes: application-scoped environments, per-app dupes., _seed_legacy_data(), test_promotes_environments_and_keeps_every_deployment_resolvable()

### Community 219 - "_seed_legacy"
Cohesion: 0.67
Nodes (3): The pre-Phase-3 shapes: a node with telemetry, and operation history., _seed_legacy(), test_upgrade_preserves_existing_nodes_containers_metrics_and_operations()

## Knowledge Gaps
- **455 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+450 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2244 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `6. Tooling: reproducible e2e` connect `sweep_session` to `test_ws_hub.py`, `typing`, `client.ts`, `operation_service.py`, `org_scope`, `auth_service.py`?**
  _High betweenness centrality (0.251) - this node is a cross-community bridge._
- **Why does `useEventStream()` connect `client.ts` to `apiGet`, `App.tsx`, `ServerDetailPage.tsx`, `sweep_session`, `DashboardPage.tsx`?**
  _High betweenness centrality (0.251) - this node is a cross-community bridge._
- **Why does `TenancyScopeError` connect `typing` to `AuthContext`, `apply_scope_to_session`, `assert_error_code`, `LogLine`, `sweep_session`, `test_tenant_isolation.py`, `org_scope`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Are the 93 inferred relationships involving `AuthContext` (e.g. with `TenancyScopeError` and `MembershipStatus`) actually correct?**
  _`AuthContext` has 93 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `APIModel` (e.g. with `OperationSpec` and `test_specs_reject_unknown_params()`) actually correct?**
  _`APIModel` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `apiGet()` (e.g. with `ContainerDetailPage.test.tsx` and `mockApi()`) actually correct?**
  _`apiGet()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `Server` (e.g. with `ServerStatus` and `2.3 Infrastructure — Nodes`) actually correct?**
  _`Server` has 5 INFERRED edges - model-reasoned connections that need verification._