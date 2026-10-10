# Graph Report - nexusops  (2026-10-11)

## Corpus Check
- 353 files · ~361,953 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: (none) 10, .example 1, .service 1)

## Summary
- 5726 nodes · 16869 edges · 220 communities (195 shown, 25 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1331 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `11f045a1`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- apiGet
- AuthContext
- ApiKeysPage.tsx
- test_phase4_routing.py
- OperationType
- types.ts
- resolve_client_ip
- ProjectDetailPage.tsx
- DockerHostsPage.tsx
- test_agent_v2.py
- assert_error_code
- ServerDetailPage.tsx
- typing
- client.ts
- projects.py
- models/__init__.py
- deployment_engine.py
- Container
- enrollment_service.py
- v1/secrets.py
- test_deployments_simulated.py
- containers.py
- enums.py
- get_settings
- Domain Routing — NexusOps
- monitors.py
- Node & Agent Architecture
- test_agent_backoff.py
- SimulatedDeploymentRunner
- nexusops_agent.py
- get_sessionmaker
- auth_service.py
- container_service.py
- get_redis
- docker_hosts.py
- test_ws_hub.py
- schemas/proxy.py
- search
- api_key_service.py
- v1/channels.py
- DockerProvider
- test_monitor_transport.py
- StepFailure
- @tanstack/react-query
- Hub
- require_permission
- routes.py
- test_phase3_nodes.py
- test_ssrf.py
- secret_service.py
- roles.py
- servers.py
- Server
- test_migration_phase21.py
- v1/auth.py
- test_agent_nginx_contract.py
- users.py
- collections_abc
- notification_service.py
- helpers.py
- compilerOptions
- v1/deployments.py
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
- core/tenancy.py
- AsyncSession
- domains.py
- incident_service.py
- test_phase2_secrets.py
- AuthContext.tsx
- monitor_service.py
- canonicalize_name
- tests/conftest.py
- test_schemas_server.py
- user_service.py
- devDependencies
- NotFound
- log_service.py
- Settings
- domain_routing.py
- validate_config
- alert_service.py
- test_tenant_isolation.py
- test_phase21_secret_version_integrity.py
- StepLine
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- journey.spec.ts
- logging.py
- redact_mapping
- README.md - NexusOps overview
- env.py
- docker_host_service.py
- _rows
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- App.tsx
- docker_real.py
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- ScopedSession
- organization_service.py
- test_app_gating.py
- dnsmock.py
- scripts
- APIModel
- test_tenancy_allowlist.py
- hub.py
- dependencies
- DeploymentDetailPage.test.tsx
- generate_secrets.sh
- UnprocessableEntity
- server_payload
- test_migration_phase2.py
- main.py
- OperationError
- v1/operations.py
- TxtObservation
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
- test_event_publish_drain.py
- main
- monitor_transport.py
- test_notifications.py
- seed.py
- AgentClient
- SecretsPage.tsx
- nginx.py
- deps.py
- agent_heartbeat
- RouteHeader
- test_agent_contract.py
- 20261009_1000-c3d4e5f6a7b8_enforce_secret_version_integrity.py
- _FakeAsyncClient
- scope_matches
- apikeys.py
- 2. Entities
- Platform Security Model — NexusOps
- decide
- network_rates
- container.py
- router.py
- _nginx_apply
- _nginx_bootstrap
- 8. Upstream binding and re-render triggers
- Multi-Tenancy Architecture
- NotificationChannel
- maintenance.py
- role_service.py
- instant_pacing
- phase3.spec.ts
- server.py
- docs/engineering-report.md - build and verification report
- get_latest_server_metrics
- test_migration_drift.py
- test_rbac.py
- ChannelType
- 20261010_1200-f4a5b6c7d8e9_phase4_domains_and_routes.py
- _raw_probe
- Product Roadmap — NexusOps Multi-Tenant Platform
- Platform Vision — NexusOps
- enqueue.py
- test_monitors_incidents.py
- 2. The Node concept
- ProxyProvider
- ApplicationBase
- DeploymentRunner
- 20261008_1200-b2c3d4e5f6a7_add_projects_and_environments.py
- 20261009_1300-a1b2c3d4e5f6_add_phase3_nodes_and_agent_v2.py
- _live_bundle_id
- _invite
- lax
- ._check_status
- .apply_params
- .route_file_path
- pytest
- _pace
- MonitorSortField
- 9. Phase 6 — Real deployments — **proposal, not implemented**
- test_domain_creation_rejects_invalid_names
- test_existing_url_monitors_are_untouched_by_routing

## God Nodes (most connected - your core abstractions)
1. `AuthContext` - 155 edges
2. `APIModel` - 145 edges
3. `apiGet()` - 91 edges
4. `Server` - 88 edges
5. `record()` - 86 edges
6. `NotFound` - 83 edges
7. `get_settings()` - 82 edges
8. `publish()` - 71 edges
9. `apiPost()` - 70 edges
10. `useToast()` - 67 edges

## Surprising Connections (you probably didn't know these)
- `0. What shipped (Phase 1)` --references--> `resolve_auth()`  [INFERRED]
  docs/authorization.md → backend/app/api/deps.py
- `6. Enforcement mechanics (unchanged patterns, one addition)` --references--> `resolve_auth()`  [INFERRED]
  docs/authorization.md → backend/app/api/deps.py
- `2. Org resolution on every request` --references--> `resolve_auth()`  [INFERRED]
  docs/multi-tenancy.md → backend/app/api/deps.py
- `3. Cross-cutting decisions` --references--> `require_permission()`  [INFERRED]
  docs/domain-model.md → backend/app/api/deps.py
- `10. Phase 7 — Teams, grants & custom roles — **proposal, not implemented**` --references--> `require_permission()`  [INFERRED]
  docs/product-roadmap.md → backend/app/api/deps.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three authentication credential families with centralized permission checks** — docs_api_md_auth, docs_api_md_refresh_rotation, docs_api_md_api_keys, docs_agent_md_enrollment_token, docs_api_md_permission_model [EXTRACTED 1.00]
- **NexusOps compose stack services** — docker_compose_yml_nexusops_stack, docker_compose_yml_postgres_service, docker_compose_yml_redis_service, docker_compose_yml_mailpit_service, docker_compose_yml_api_service, docker_compose_yml_worker_service, docker_compose_yml_scheduler_service, docker_compose_yml_frontend_service, docker_compose_yml_nginx_service [EXTRACTED 1.00]
- **WebSocket real-time fan-out spine** — docs_architecture_md_websocket_hub, docs_api_md_websocket_channels, docker_compose_yml_redis_service, docs_architecture_md_event_bus, readme_react_spa [INFERRED 0.85]

## Communities (220 total, 25 thin omitted)

### Community 0 - "apiGet"
Cohesion: 0.06
Nodes (95): apiGet(), apiPost(), CursorPage, DeploymentOut, ProjectOut, RouteConfigState, DeploymentListPage, DomainDetailPage (+87 more)

### Community 1 - "AuthContext"
Cohesion: 0.10
Nodes (55): AuthContext, Resolved identity plus the organization this request acts in.…, The active organization, or raise if this request has none., Application, DeploymentEnvironment, A **project-scoped** deployment environment (Phase 2 promotion). The…, Any, AsyncSession (+47 more)

### Community 2 - "ApiKeysPage.tsx"
Cohesion: 0.09
Nodes (20): ApiKeyOut, ApiKeysPage, ApiKeyCreatedOut, ApiKeysPage(), handleCopyKey(), copyText(), describeError(), EMPTY_FORM (+12 more)

### Community 3 - "test_phase4_routing.py"
Cohesion: 0.08
Nodes (75): Keep every routed node's live configuration matching the desired bundle. One…, sweep_routes(), _claim(), _container_id(), _count_rows_in_system_scope(), _create_node(), _create_route(), _drain() (+67 more)

### Community 4 - "OperationType"
Cohesion: 0.12
Nodes (20): OperationType, The whitelist. Nothing outside this enum ships as an exec surface. Each type…, Any, Validate *params* against the type's model and return the stored form.…, validate_params(), MonkeyPatch, The operation dispatch whitelist is a contract, not a convention.…, A type whose capability cannot be confirmed must not be dispatchable. (+12 more)

### Community 5 - "types.ts"
Cohesion: 0.04
Nodes (57): AlertOut, CapabilityReport, ChannelOut, ContainerOut, DeliveryOut, DeploymentLogLine, DeploymentStatus, DeploymentStepOut (+49 more)

### Community 6 - "resolve_client_ip"
Cohesion: 0.17
Nodes (22): _is_trusted(), _parse_networks(), Request, Client-IP resolution behind chained reverse proxies. The API never takes TCP…, Parse a comma-separated CIDR list; malformed entries are skipped., Real client address for *request* per the trust model above., resolve_client_ip(), make_request() (+14 more)

### Community 7 - "ProjectDetailPage.tsx"
Cohesion: 0.08
Nodes (30): apiDelete(), apiPatch(), ApplicationOut, ENVIRONMENT_TYPE_LABELS, EnvironmentType, ProjectDetailPage, configToText(), parseConfigText() (+22 more)

### Community 8 - "DockerHostsPage.tsx"
Cohesion: 0.06
Nodes (30): DockerHostOut, DockerHostsPage, CheckboxField(), CheckboxFieldProps, FieldAria, FieldBaseProps, PasswordField(), PasswordFieldProps (+22 more)

### Community 9 - "test_agent_v2.py"
Cohesion: 0.06
Nodes (51): agent_fixture(), _load_agent(), Any, fixture, parametrize, Path, Agent protocol v2: honest metrics, capability detection, and the executor. The…, Phase 4 shipped three nginx ops — no file primitive, no command primitive. (+43 more)

### Community 10 - "assert_error_code"
Cohesion: 0.08
Nodes (55): OperationStatus, Lifecycle of one node operation (node-agent-architecture.md §5.1).…, assert_error_code(), Assert envelope shape + code; returns the inner error object., _dispatch(), _dispatch_body(), _enrolled_node(), _mutate_in_system_scope() (+47 more)

### Community 11 - "ServerDetailPage.tsx"
Cohesion: 0.08
Nodes (39): EnrollmentTokenCreated, EnrollmentTokenItem, MetricPoint, OperationItem, OperationType, ServerDetailPage, ServerListPage, ChartSeries (+31 more)

### Community 12 - "typing"
Cohesion: 0.05
Nodes (63): Agent ingest endpoints: enrollment, hello, heartbeat, and operation traffic.…, AgentEnrollOut, AgentHeartbeatOut, AgentHelloOut, Agent-facing schemas. Payloads are data only — never executed. Wire protocol v2…, Tells the agent how often to report and what protocol it negotiated., v2 heartbeat response: cadence, work to pull, and any pending rotation. A v1…, The minimum a freshly enrolled agent needs, and nothing more. (+55 more)

### Community 13 - "client.ts"
Cohesion: 0.05
Nodes (59): API_BASE, ApiError, apiRequest(), buildUrl(), extractError(), getAccessToken(), getActiveOrgId(), onActiveOrgChange() (+51 more)

### Community 14 - "projects.py"
Cohesion: 0.13
Nodes (42): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+34 more)

### Community 15 - "models/__init__.py"
Cohesion: 0.08
Nodes (57): Base, big_serial_pk(), json_column(), org_id_column(), OrgScoped, datetime, UUID, Declarative base, shared mixins and column helpers. (+49 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.10
Nodes (59): deployment_log_channel(), Deployment, DeploymentStep, DeploymentStatus, StepStatus, _after_commit_enqueue(), _after_rollback_drop(), _audit_resolution_failed() (+51 more)

### Community 17 - "Container"
Cohesion: 0.07
Nodes (40): ContainerHealth, ContainerStatus, Container, Observed container state mirrored from an agent or docker provider., LogEntry, Any, datetime, Simulated docker provider for demo and test environments. The provider is… (+32 more)

### Community 18 - "enrollment_service.py"
Cohesion: 0.08
Nodes (40): generate_enrollment_token(), An enrollment credential (``nxk_``): single-use, short-lived, org-scoped.…, EnrollmentToken, One single-use credential that enrolls (or claims) exactly one node., Whether the row could still be redeemed (not a race-safe check)., EnrollmentTokenState, Derived lifecycle state of an enrollment token, computed server-side. Stored as…, AgentCredential (+32 more)

### Community 19 - "v1/secrets.py"
Cohesion: 0.14
Nodes (30): create_secret(), delete_secret(), get_secret(), list_secret_versions(), list_secrets(), DbSession, delete, get (+22 more)

### Community 20 - "test_deployments_simulated.py"
Cohesion: 0.14
Nodes (30): execute_deployment(), Run one deployment to a terminal state. Never raises; safe to re-run., get_application(), get_environment(), _as_worker(), _delivery_chain(), _owner_ctx(), _queue() (+22 more)

### Community 21 - "containers.py"
Cohesion: 0.07
Nodes (55): _action_route(), _endpoint(), _container_out(), _decode_frame(), _ev(), get_container(), _like_pattern(), list_container_logs() (+47 more)

### Community 22 - "enums.py"
Cohesion: 0.05
Nodes (80): Canonical Redis pub/sub channel names shared by API, workers and WS hub., server_metrics_channel(), ActorType, AlertSeverity, AuditResult, EventLevel, LogLevel, MetricGranularity (+72 more)

### Community 23 - "get_settings"
Cohesion: 0.07
Nodes (56): argon2, argon2_exceptions, _quoted_list(), Add the operations framework table (node-agent-architecture.md §5). One tenant-…, upgrade(), fail_on_bad_config(), get_settings(), Central configuration. All runtime configuration flows through this module so… (+48 more)

### Community 24 - "Domain Routing — NexusOps"
Cohesion: 0.09
Nodes (23): 10. Wildcards and catch-all, 11. User journey, 12. API surface, permissions, audit, 13. Monitoring tie-in, 1. Scope and current state, 2. Where nginx runs, 3.1 Domain, 3.2 Route (+15 more)

### Community 25 - "monitors.py"
Cohesion: 0.15
Nodes (37): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+29 more)

### Community 26 - "Node & Agent Architecture"
Cohesion: 0.12
Nodes (17): 1. Scope and stance, 3.2 Enrollment v2, 3.3 Token storage & rotation with dual-token grace, 3.4 Revocation semantics — fixing the 401 hot-loop, 3.5 Reconnect / offline states, 3. Agent lifecycle, 6.1 Token scope, 6.2 docker.sock is root-equivalent (+9 more)

### Community 27 - "test_agent_backoff.py"
Cohesion: 0.14
Nodes (22): agent_fixture(), _install_sleep(), fake_sleep(), _load_agent(), _patch_host(), Any, fixture, MonkeyPatch (+14 more)

### Community 28 - "SimulatedDeploymentRunner"
Cohesion: 0.25
Nodes (23): Staged docker-style simulation used by v1 deployments., Canonical step identifiers stored on :class:`DeploymentStep` rows., SimulatedDeploymentRunner, StepName, _collect(), _ctx(), Unit tests for SimulatedDeploymentRunner (async generators, no broker)., RESOLVE_CONFIG is planned by the engine, not produced by a runner. (+15 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.09
Nodes (29): build_heartbeat(), collect_container_stats(), collect_containers(), _container_ports(), _container_status(), cpu_percent_since(), disk_stats(), docker_capability() (+21 more)

### Community 30 - "get_sessionmaker"
Cohesion: 0.08
Nodes (36): get_engine(), get_session(), get_sessionmaker(), async_sessionmaker, AsyncEngine, AsyncSession, Async SQLAlchemy engine and session management., FastAPI dependency yielding an async session. (+28 more)

### Community 31 - "auth_service.py"
Cohesion: 0.11
Nodes (45): active_memberships(), The user's memberships in non-suspended organizations, oldest first. Reads only…, hash_password(), System scope bound to *db*, for rows that have no organization. Used by exactly…, system_write_scope(), _audit(), _auth_event_scope(), change_own_password() (+37 more)

### Community 32 - "container_service.py"
Cohesion: 0.08
Nodes (43): clip(), DockerProviderError, Exception, Provider abstraction for docker hosts (real daemon or simulated). Providers are…, A provider operation failed. ``str()`` is safe to show/log., Build a compact, secret-free description of a provider failure. Only the…, Truncate *text* to *limit* characters, stripping control chars., sanitize_error() (+35 more)

### Community 33 - "get_redis"
Cohesion: 0.08
Nodes (38): liveness(), get, Response, Health probes: liveness (always cheap) and readiness (checks dependencies).…, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness(), RateLimited (+30 more)

### Community 34 - "docker_hosts.py"
Cohesion: 0.07
Nodes (55): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+47 more)

### Community 35 - "test_ws_hub.py"
Cohesion: 0.12
Nodes (27): _connection(), _drain(), _event_frame(), _fake_sessionmaker(), _FakeSession, hub(), _Org, Any (+19 more)

### Community 36 - "schemas/proxy.py"
Cohesion: 0.12
Nodes (22): Render the complete desired state for *node*. A full tree every time — never a…, BundleFile, fingerprint_files(), is_allowed_bundle_path(), NginxBundle, Any, Proxy bundle and operation-parameter schemas — the agent-facing config…, One rendered file. The path is allowlisted, the content is bounded. (+14 more)

### Community 37 - "search"
Cohesion: 0.12
Nodes (30): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+22 more)

### Community 38 - "api_key_service.py"
Cohesion: 0.20
Nodes (15): create_api_key(), list_api_keys(), AsyncSession, Request, UUID, API key lifecycle: creation with scope validation, listing, revocation., Live (non-revoked) keys owned by *owner_id*, newest first., Revoke a key owned by *owner_id*. Foreign keys look like NotFound (no leak). (+7 more)

### Community 39 - "v1/channels.py"
Cohesion: 0.15
Nodes (28): create_channel(), delete_channel(), get_channel(), list_channels(), list_deliveries(), DbDep, delete, Depends (+20 more)

### Community 40 - "DockerProvider"
Cohesion: 0.09
Nodes (12): DockerProvider, Any, datetime, Protocol, List containers visible to the provider., Inspect a single container by id (short ids allowed)., List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``., List volumes: keys ``name``, ``driver``, ``mountpoint``. (+4 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.13
Nodes (34): CheckResult, HTTPMonitorTransport, Deterministic fake checker for ``sim://`` monitors and demo environments.…, Real HTTP(S) probe using httpx with per-monitor settings. Redirects are…, SimulatedTransport, _check(), clock(), FakeClock (+26 more)

### Community 42 - "StepFailure"
Cohesion: 0.11
Nodes (19): Exception, Raised by a runner when a step fails irrecoverably., StepFailure, 10. Events and WS during runs, 12. Rollback semantics (existing behavior kept), 13. The simulated runner stays — labeled, 14. Open questions, 1.1 The honest defect list (+11 more)

### Community 43 - "@tanstack/react-query"
Cohesion: 0.03
Nodes (55): CheckOut, IncidentOut, MonitorOut, SessionInfo, ACTIVE_MEMBERSHIP, ME, mocks, mocks (+47 more)

### Community 44 - "Hub"
Cohesion: 0.13
Nodes (18): _close_socket(), Connection, _frame_org(), Hub, _params_key(), _parse_payload(), Any, WebSocket (+10 more)

### Community 45 - "require_permission"
Cohesion: 0.06
Nodes (38): permission_dep(), Any, Dependency factory enforcing a permission; returns 403 when denied., require_permission(), _check(), _decode_cursor(), _encode_cursor(), list_event_types() (+30 more)

### Community 46 - "routes.py"
Cohesion: 0.16
Nodes (30): create_route(), delete_route(), disable_route(), _domain_status(), enable_route(), get_route(), list_routes(), AsyncSession (+22 more)

### Community 47 - "test_phase3_nodes.py"
Cohesion: 0.15
Nodes (33): _create_token(), _dispatch(), _enroll(), _enrolled_node(), _load_agent_module(), _mutate_in_system_scope(), Phase 3 — Nodes & Agent v2 end-to-end behaviour. Grouped by the question each…, Import the shipped agent source (sync, so async tests never touch Path). (+25 more)

### Community 48 - "test_ssrf.py"
Cohesion: 0.11
Nodes (32): assert_safe_tcp_endpoint(), _is_forbidden_address(), is_simulation_url(), ValueError, SSRF guard applied to every operator-supplied outbound URL. Monitors and…, Validate a ``tcp://`` docker host endpoint for outbound connection. Docker…, True when *url* targets the built-in simulated checker (``sim://``)., Internal signal: a specific SSRF rule matched (never shown to clients). (+24 more)

### Community 49 - "secret_service.py"
Cohesion: 0.09
Nodes (49): An encrypted configuration value, scoped to org, project or environment.…, One immutable value of a :class:`Secret` — append-only history. A row is…, Secret, SecretVersion, _actor_type(), _collect_refs(), create_secret(), delete_secret() (+41 more)

### Community 50 - "roles.py"
Cohesion: 0.11
Nodes (29): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, delete, get (+21 more)

### Community 51 - "servers.py"
Cohesion: 0.06
Nodes (64): apply_node_proxy_config(), create_enrollment_token(), create_server(), delete_server(), _detail(), _enrollment_created(), _enrollment_out(), get_server() (+56 more)

### Community 52 - "Server"
Cohesion: 0.06
Nodes (79): ListenerOwnership, ProxyApplyOutcome, Terminal outcome of one ``nginx.apply`` operation on a node., Who holds one required listener port, per the node's pre-flight. The…, Server, Operation, Whether the agent reported this operation as successful. A terminal check, not…, One whitelisted action for one node, with a CAS lifecycle. ``attempts`` is… (+71 more)

### Community 53 - "test_migration_phase21.py"
Cohesion: 0.12
Nodes (17): Phase 2.1 corrective migration: legacy ``environment_type`` classification.…, Every case is classified as documented, ids and ownership intact., An explicit non-DEV classification survives the corrective migration. The…, The correction is part of ``head`` and adds no extra Alembic head., Insert one legacy environment per case, in two organizations., _seed_typed_environments(), test_corrective_migration_is_reachable_from_head(), test_corrects_legacy_environment_types() (+9 more)

### Community 54 - "v1/auth.py"
Cohesion: 0.05
Nodes (72): change_password(), _clear_refresh_cookie(), _cookies_secure(), login(), logout(), me(), _optional_actor(), AsyncSession (+64 more)

### Community 55 - "test_agent_nginx_contract.py"
Cohesion: 0.08
Nodes (53): _agent_bundle(), agent_fixture(), _bootstrap_fixture(), _load_agent(), Any, fixture, parametrize, Path (+45 more)

### Community 56 - "users.py"
Cohesion: 0.12
Nodes (27): create_user(), deactivate_user(), get_user(), list_users(), CurrentUser, DbSessionDep, delete, get (+19 more)

### Community 57 - "collections_abc"
Cohesion: 0.06
Nodes (14): alembic, downgrade(), rename ``server.*`` permission codenames to ``node.*`` The Node/Server…, _rename_permissions(), upgrade(), Fix pre-existing model/migration drift (surfaced by the new drift check). Two…, downgrade(), Phase 2.1 — correct legacy ``environment_type`` classification. The Phase 2… (+6 more)

### Community 58 - "notification_service.py"
Cohesion: 0.21
Nodes (19): DeliveryStatus, _as_uuid(), _attempt_delivery(), decode_delivery_cursor(), _send(), encode_delivery_cursor(), list_deliveries(), _now() (+11 more)

### Community 59 - "helpers.py"
Cohesion: 0.07
Nodes (52): bearer(), cookie_attributes(), error_of(), login_account(), login_headers(), Any, AsyncClient, Response (+44 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "v1/deployments.py"
Cohesion: 0.10
Nodes (42): _attribute_step_idx(), cancel_deployment(), _emails_for(), get_deployment(), list_application_deployments(), list_deployment_logs(), _list_deployments(), _parse_sort() (+34 more)

### Community 62 - "register_exception_handlers"
Cohesion: 0.12
Nodes (13): _error_payload(), Any, FastAPI, Request, register_exception_handlers(), handle_app_error(), handle_http_exception(), handle_unexpected() (+5 more)

### Community 63 - "dns_verifier.py"
Cohesion: 0.12
Nodes (19): apex_of(), The name a wildcard Domain is anchored at (``*.example.com`` →…, The exact TXT owner name a user must publish at their provider., verification_record_name(), _discover_nameservers(), _normalise_ns(), observe(), Observer (+11 more)

### Community 64 - "test_phase2_environments.py"
Cohesion: 0.18
Nodes (22): _environment(), _project(), parametrize, Phase 2: project-scoped environments, config layering, and their isolation. The…, Uniqueness is ``(project_id, slug)`` — not instance-wide., The update path is validated too (the pre-Phase-2 gap)., Knowing an environment UUID is not access: the project link must hold., Another tenant cannot reach the project, its environments, or its detail. (+14 more)

### Community 65 - "route_service.py"
Cohesion: 0.12
Nodes (44): MonitorTargetType, Last nginx apply outcome for a route, as reported by its node's agent.…, What a monitor observes (domain-model.md §2.6, polymorphic targets). ``URL`` is…, RouteConfigState, One hostname+path served from one container on one node. Relationship rules the…, Route, _actor(), _conflicting_route() (+36 more)

### Community 66 - "test_schema_redaction.py"
Cohesion: 0.18
Nodes (17): is_sensitive_header(), mask_sensitive_headers(), True when *name* looks like it carries a credential (Authorization etc.)., Return a copy of *headers* with sensitive values replaced by a mask., mask_target(), Human-readable masked target safe to expose over the API. For webhook families…, _monitor_out(), Outbound-schema redaction: monitor probe credentials and webhook targets.… (+9 more)

### Community 67 - "PageParams"
Cohesion: 0.08
Nodes (45): list_alerts(), Depends, Unread alerts first, then newest first., list_audit_logs(), datetime, DbSession, Depends, get (+37 more)

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
Cohesion: 0.22
Nodes (13): _create(), _environment_config(), Secrets: metadata-only reads, rotation versioning, deploy-time resolution., Project → application → environment carrying *config*; returns its id., A reference naming no secret must abort, not resolve to an empty value.…, A row this ENCRYPTION_KEY cannot decrypt must abort, not yield ``""``., test_create_and_list_return_metadata_only(), test_delete_removes_metadata_row() (+5 more)

### Community 72 - "test_nginx_renderer.py"
Cohesion: 0.13
Nodes (37): NginxProvider, ValueError, The only production provider in Phase 4., Rendering refused the input. Always a bug or a corrupt row, never a leak., RenderError, NginxApplyParams, One validated bundle to apply atomically., provider() (+29 more)

### Community 73 - "domain_service.py"
Cohesion: 0.09
Nodes (44): DomainStatus, Ownership-verification lifecycle of a Domain (domain-routing.md §4). ``STALE``…, Domain, One DNS name an organization is proving it controls. ``name`` is canonical (see…, What the lifecycle should do with an observation., VerificationDecision, _actor(), apply_decision() (+36 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "core/tenancy.py"
Cohesion: 0.10
Nodes (29): _apply_scope_guc(), _desired_guc(), _guard(), _has_org_predicate(), _mappers_of(), _org_scoped_classes(), org_scoped_table_names(), Any (+21 more)

### Community 76 - "AsyncSession"
Cohesion: 0.12
Nodes (30): _actor_kwargs(), container_counts(), create_server(), delete_server(), get_server(), list_tags_with_usage(), pending_rotation(), _publish_server_event() (+22 more)

### Community 77 - "domains.py"
Cohesion: 0.11
Nodes (39): create_domain(), delete_domain(), _enqueue_verification(), get_domain(), list_domain_routes(), list_domains(), _project_names(), alias (+31 more)

### Community 78 - "incident_service.py"
Cohesion: 0.10
Nodes (56): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+48 more)

### Community 79 - "test_phase2_secrets.py"
Cohesion: 0.19
Nodes (21): _env(), _project(), Phase 2 secrets: layered scope, immutable versions, rollback, isolation. Two…, Two racing rotations must both be kept and never share a version number., Another tenant cannot read, rotate, roll back or even enumerate the secret., The documented example: same key at three scopes; most specific wins., A ref declared in the project base config resolves for its environments., _resolved() (+13 more)

### Community 80 - "AuthContext.tsx"
Cohesion: 0.04
Nodes (50): Membership, Role, User, RolesPage, UsersPage, AuthContext, AuthProvider(), AuthState (+42 more)

### Community 81 - "monitor_service.py"
Cohesion: 0.15
Nodes (37): MonitorStatus, Monitor, MonitorCheck, One probe. Targets are polymorphic since Phase 4 (domain-model.md §2.6).…, _active_incident(), _audit(), claim_due_monitors(), create_monitor() (+29 more)

### Community 82 - "canonicalize_name"
Cohesion: 0.11
Nodes (34): canonicalize_name(), canonicalize_path(), _check_labels(), _check_not_ip(), hostname_is_covered(), _idna(), InvalidName, is_valid_path() (+26 more)

### Community 83 - "tests/conftest.py"
Cohesion: 0.20
Nodes (8): configure_test_env(), Test bootstrap: pin every cached setting BEFORE the first ``app`` import. The…, KEY=VALUE pairs from the repo .env (first definition wins); never logged., Export the exact settings the app caches; host values cannot leak through., _read_dot_env(), base64, os, sys

### Community 84 - "test_schemas_server.py"
Cohesion: 0.21
Nodes (22): Payload for registering a server., Partial update. ``tags`` replaces the full set when provided., ServerCreate, ServerUpdate, _base(), parametrize, Unit tests for app.schemas.server (validation only, no I/O)., test_empty_ip_is_allowed_but_whitespace_collapses() (+14 more)

### Community 85 - "user_service.py"
Cohesion: 0.08
Nodes (50): list_sessions(), CurrentUser, DbSessionDep, delete, get, Request, UUID, Active sessions of this organization's members. Defaults to the caller's own;… (+42 more)

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "NotFound"
Cohesion: 0.10
Nodes (44): Conflict, NotFound, _active_org(), _bounded(), cancel_operation(), claim_operation(), create_operation(), ensure_dispatchable() (+36 more)

### Community 88 - "log_service.py"
Cohesion: 0.18
Nodes (18): LogSource, append_lines(), count_container_logs(), detect_level(), _entry_values(), ingest_provider_lines(), Any, AsyncSession (+10 more)

### Community 89 - "Settings"
Cohesion: 0.14
Nodes (6): field_validator, model_validator, Username from :attr:`database_url`, or ``None`` if it is unparseable., Validated application settings (loaded from environment / .env)., Settings, BaseSettings

### Community 90 - "domain_routing.py"
Cohesion: 0.17
Nodes (21): _affected_node_ids(), _apply_for_node(), _audit_action(), datetime, task, UUID, Domain verification and routing sweeps. Two properties shape this module: * **A…, Move another organization's ``VERIFIED`` claim on *name* to ``UNVERIFIED``. Its… (+13 more)

### Community 91 - "validate_config"
Cohesion: 0.06
Nodes (33): EnvironmentBase, _normalise_environment_type(), field_validator, Shared environment fields., ProjectBase, field_validator, collect_secret_refs(), walk() (+25 more)

### Community 92 - "alert_service.py"
Cohesion: 0.13
Nodes (26): mark_all_read(), mark_read(), CurrentUser, DbDep, get, post, UUID, Alert inbox endpoints. Authenticated users see the shared operator feed. (+18 more)

### Community 93 - "test_tenant_isolation.py"
Cohesion: 0.05
Nodes (82): Whether the runtime connection is the RLS-enforced application role. False…, apply_scope_to_session(), current_org(), current_scope(), org_scope(), UUID, Raised when a unit of work touches tenant data with no valid org scope. This is…, The organization this unit of work is acting for, if any. (+74 more)

### Community 94 - "test_phase21_secret_version_integrity.py"
Cohesion: 0.18
Nodes (18): _app_role_dsn(), _owner_dsn(), _probe(), Phase 2.1 — ``secret_versions`` is append-only in the **database**, not just in…, Immutability is a database guarantee, not merely a missing code path. The owner…, The legitimate append paths keep working under the guard., The documented deletion policy: purging a Secret cascades its history., RLS is preserved: another tenant cannot see a version row, even by id. (+10 more)

### Community 95 - "StepLine"
Cohesion: 0.22
Nodes (8): _commit_short(), Deployment runner port plus a faithful simulated implementation.…, Stream output lines for *step_name*; raise StepFailure to fail it., Everything a runner needs to execute one deployment., One streamed output line for a step., RunContext, _slug(), StepLine

### Community 96 - "NexusOps (self-hosted infrastructure management and monitoring platform)"
Cohesion: 0.20
Nodes (10): mailpit service (dev SMTP sink + web UI :8025), NexusOps compose stack (8 services on one network), HIGH finding: redirect-following SSRF in uptime monitors (fixed: follow_redirects=False + per-hop guard), SSRF guard (assert_safe_url, per-redirect-hop validation, assert_safe_tcp_endpoint), Mailpit SMTP port internal-only (host-side injection needs extra mapping), Host port knobs (NEXUSOPS_HTTP_PORT/POSTGRES/REDIS/MAILPIT/VITE), SPA entry point (loads /src/main.tsx, dark color-scheme), Uptime monitors -> incidents -> notifications flow (+2 more)

### Community 97 - "REST API surface (/api/v1)"
Cohesion: 0.29
Nodes (7): Cursor (keyset) and offset pagination envelopes, Permission model (data-driven registry, require_permission, wildcard scopes), REST API surface (/api/v1), RBAC registry (PERMISSIONS + ROLE_MATRIX + scope_matches), Adding a new resource: 7-step checklist (model -> migration -> schemas -> service -> router -> tests -> frontend), Alembic migration workflow (autogenerate, models __init__ export, entrypoint apply), Command palette (Ctrl/Cmd+K)

### Community 98 - "journey.spec.ts"
Cohesion: 0.15
Nodes (15): EDGE, MAILPIT, ADMIN, Bootstrap, bootstrapVia(), test, ADMIN, formLogin() (+7 more)

### Community 99 - "logging.py"
Cohesion: 0.05
Nodes (54): configure_logging(), get_logger(), _orjson_dumps(), Any, Structured logging via structlog. Every log record carries timestamp, level,…, Configure structlog + stdlib logging once at process start. Everything…, flush_pending_publishes(), Wait for frames scheduled by ``after_commit`` hooks to reach Redis. The commit… (+46 more)

### Community 100 - "redact_mapping"
Cohesion: 0.07
Nodes (34): _is_sensitive_key(), Substring match on a normalised key so header-style names are caught too.…, Return a copy of *data* with sensitive values replaced. Used by audit metadata…, redact_mapping(), parametrize, Unit tests for app.core.logging redaction (pure functions only)., test_case_insensitive_substring_match(), test_flat_sensitive_keys_redacted() (+26 more)

### Community 102 - "env.py"
Cohesion: 0.24
Nodes (10): _database_url(), Alembic environment: metadata comes from app.models, URL from app settings., Migrations run as the table **owner**, never as the application role. The owner…, Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online(), Owner-role DSN for Alembic and the container entrypoint. Migrations… (+2 more)

### Community 103 - "docker_host_service.py"
Cohesion: 0.08
Nodes (50): asyncio, BadRequest, DockerHostStatus, DockerHost, provider_for(), Return the provider matching *host*'s endpoint configuration., _assert_endpoint_allowed(), _assert_name_free() (+42 more)

### Community 104 - "_rows"
Cohesion: 0.22
Nodes (16): _rows(), _integrity_error(), _migrate_from_phase3(), Statement, Phase 4 migration (`f4a5b6c7d8e9`) against a real Phase 3 database. Phase 4 is…, The polymorphic shape is enforced in both directions., The anti-takeover rule is a partial unique index, not a convention., A populated pre-Phase-4 instance: a node, a URL monitor, a live operation. (+8 more)

### Community 105 - "redis service (Redis 7, no persistence, loopback :6390)"
Cohesion: 0.22
Nodes (11): redis service (Redis 7, no persistence, loopback :6390), WebSocket API (/api/v1/ws handshake, frames, limits), WebSocket channels (global, server-metrics, container-logs, deployment-logs, incidents), Deployment engine (queue_deployment / execute_deployment / sweeper backstop), Real-time spine: PostgreSQL system_events + Redis pub/sub, Rollback as a new deployment (rollback_of_id), WebSocket hub (framework-thin, Redis fan-in, per-socket queues), Test suites (pytest unit+integration, vitest, Playwright e2e) (+3 more)

### Community 106 - "NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)"
Cohesion: 0.18
Nodes (12): Agent security model (one-way telemetry, no command channel), Agent enrollment token (X-Agent-Token, nxa_..., SHA-256 at rest), Agent heartbeat exponential backoff (cap 5 min, exit 1 on revoked token), agent/install.sh (enrollment installer), Agent metrics collection (/proc statvfs Docker socket), NexusOps agent (stdlib-only Python, agent/nexusops_agent.py), Agent systemd hardening (ProtectSystem=strict, NoNewPrivileges), Agent ingest API (POST /agent/hello, POST /agent/heartbeat) (+4 more)

### Community 107 - "App.tsx"
Cohesion: 0.05
Nodes (40): SearchResult, AlertsPage, App(), DeploymentDetailPage, DomainListPage, EnvironmentDetailPage, IncidentDetailPage, LoginPage (+32 more)

### Community 108 - "docker_real.py"
Cohesion: 0.09
Nodes (28): ContainerInfo, ContainerStats, Normalized view of a container as reported by any provider., Point-in-time resource usage snapshot., _as_float(), _compute_stats(), _cpu_percent(), _network_bytes() (+20 more)

### Community 109 - "Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)"
Cohesion: 0.25
Nodes (9): API keys (X-API-Key, nxo_..., scope intersection), First boot sequence (api entrypoint migrates, compose never seeds), Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test), Makefile workflows (up/test/lint/typecheck/migrate/seed), HIGH finding: API-key scope bypass for superadmin-owned keys (fixed: scope intersection first), Security audit 2026-09 (26 raw findings -> 20 confirmed, all fixed), HIGH finding: known seed superadmin + API key backdoor (fixed: NEXUSOPS_ALLOW_SEED opt-in, one-time password), Threat model (edge attacker, malicious agent, curious operator, leaked token, SSRF) (+1 more)

### Community 111 - "organization_service.py"
Cohesion: 0.11
Nodes (39): _load_organization(), Organization, Forbidden, MembershipStatus, OrganizationStatus, Membership, Organization, A tenant. Every organization-owned row points here via ``org_id``. (+31 more)

### Community 112 - "test_app_gating.py"
Cohesion: 0.44
Nodes (8): _app_for_environment(), MonkeyPatch, ENVIRONMENT gating contract: docs exposure and HSTS (see .env.example).…, create_app() with get_settings() patched to the given environment., test_non_production_does_not_emit_hsts(), test_non_production_keeps_docs_and_schema(), test_production_emits_hsts(), test_production_hides_docs_and_schema()

### Community 113 - "dnsmock.py"
Cohesion: 0.08
Nodes (31): resolver(), BaseHTTPRequestHandler, answer(), clear_record(), ControlHandler, encode_name(), encode_txt(), forward() (+23 more)

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "APIModel"
Cohesion: 0.03
Nodes (71): AgentContainerPortIn, AgentTokenRotation, CapabilityReport, One published-port binding of a container, as docker reports it. Four distinct…, A pending credential rotation, delivered on the agent's next beat. Served…, One node-reported capability. ``present`` defaults to false, and a capability…, ApiKeyCreateRequest, APIModel (+63 more)

### Community 116 - "test_tenancy_allowlist.py"
Cohesion: 0.20
Nodes (14): AST, _actual_callers(), _calls_system_scope(), _module_path(), Path, The system-scope allowlist is the only fence around the tenancy carve-out.…, Every module that could open a system scope: ``app/`` plus the scripts., No module may lift tenant isolation without being named in the list. (+6 more)

### Community 117 - "hub.py"
Cohesion: 0.14
Nodes (23): AppError, Exception, Base class for expected, client-facing errors., _authenticate_api_key(), _authenticate_jwt(), _bind_organization(), _entity_exists(), _load_permissions() (+15 more)

### Community 118 - "dependencies"
Cohesion: 0.33
Nodes (6): dependencies, lucide-react, react, react-dom, react-router-dom, @tanstack/react-query

### Community 119 - "DeploymentDetailPage.test.tsx"
Cohesion: 0.13
Nodes (9): ACTIVE_MEMBERSHIP, ApiError, deploymentDetail(), EMPTY_LOGS, FakeWebSocket, get, ME, post (+1 more)

### Community 120 - "generate_secrets.sh"
Cohesion: 0.47
Nodes (3): existing_real_keys(), replace_or_append(), generate_secrets.sh script

### Community 121 - "UnprocessableEntity"
Cohesion: 0.16
Nodes (25): UnprocessableEntity, assert_safe_url(), assert_safe_url_async(), _raise_block(), Validate *url* for outbound requests; return the parsed URL or raise 422.…, Async wrapper around :func:`assert_safe_url`; DNS runs off the loop., Reject non-empty values that are not valid IPv4/IPv6 addresses., _validate_ip() (+17 more)

### Community 122 - "server_payload"
Cohesion: 0.09
Nodes (29): A valid POST /servers body with per-test overrides., server_payload(), test_token_cannot_claim_a_foreign_tenants_node(), test_v1_heartbeat_keeps_the_204_contract(), _create_server(), Server CRUD, cascade delete, audit trail rows and audit immutability., The HTTP listing path — schema serialization is exercised end-to-end. A…, ``/servers`` is a temporary alias for pre-rename clients. It must keep working… (+21 more)

### Community 123 - "test_migration_phase2.py"
Cohesion: 0.14
Nodes (25): alembic_config, alembic_script, _exec(), _migration_dsn(), _owner_dsn(), Statement, Phase 2 migration (`b2c3d4e5f6a7`) against realistic legacy data. The promotion…, Upgrade ``database`` to ``revision`` through the app's own settings path.… (+17 more)

### Community 124 - "main.py"
Cohesion: 0.09
Nodes (28): ASGIApp, dispose_engine(), AccessLogMiddleware, Request, Response, HTTP middleware: request ids, security headers, structured access logs., Baseline hardening headers on every API response., RequestIDMiddleware (+20 more)

### Community 125 - "OperationError"
Cohesion: 0.18
Nodes (15): _demux_docker_stream(), _docker_error(), execute_operation(), OperationError, Exception, A stable, sanitized failure contract for the control plane., Re-validate the operation's parameters locally, against a closed shape., Decode docker's 8-byte-header frame stream, or ``None`` if not framed. (+7 more)

### Community 126 - "v1/operations.py"
Cohesion: 0.18
Nodes (20): cancel_operation(), create_operation(), get_operation(), list_operations(), DbDep, Depends, get, post (+12 more)

### Community 127 - "TxtObservation"
Cohesion: 0.09
Nodes (24): One bounded look at a name's authoritative TXT record., TxtObservation, _create_domain(), _dns_stub(), _fake_observe(), _flip_name_to(), fixture, MonkeyPatch (+16 more)

### Community 137 - "Page"
Cohesion: 0.09
Nodes (21): AuditEntry, Page, AuditLogPage, ContainerListPage, PaginationProps, AuditLogPage(), AuditRow, formatTimestamp() (+13 more)

### Community 146 - "test_auth_multi_org.py"
Cohesion: 0.20
Nodes (20): A fresh, deliverable-shaped address unique to a single test. ``example.com`` is…, unique_email(), test_second_register_without_invite_is_rejected(), _latest_audit(), _latest_event(), _list_ids(), Any, UUID (+12 more)

### Community 147 - "20260922_1000-a3f1c8d24b6e_add_tenancy_foundation.py"
Cohesion: 0.20
Nodes (12): _app_role_credentials(), _assert_fully_backfilled(), _backfill_org_ids(), _drop_constraint(), add tenancy foundation Phase 1 of the platform roadmap: organizations,…, Carry a value into a PL/pgSQL block. ``CREATE ROLE``/``ALTER ROLE`` are utility…, Application role name/password from settings (never hard-coded)., Point every pre-existing row at the bootstrap organization. ``audit_logs`` is… (+4 more)

### Community 148 - "postgres service (PostgreSQL 17, loopback :5433)"
Cohesion: 0.29
Nodes (7): postgres service (PostgreSQL 17, loopback :5433), Fernet encryption at rest (ENCRYPTION_KEY, write-once), Backups (pgdata volume, nightly pg_dump, ephemeral Redis), Required secrets (POSTGRES_PASSWORD, JWT_SECRET >= 32 chars, ENCRYPTION_KEY Fernet), Production hardening checklist (secrets, ENVIRONMENT, no seed, TLS, rotation), Compose vs host network namespaces (postgres:5432 vs 127.0.0.1:5433), Simulation mode (SIMULATION_MODE)

### Community 149 - "phase4.spec.ts"
Cohesion: 0.09
Nodes (20): AGENT, DNS_CONTROL, dnsPublish(), docker(), DomainBody, EventBody, HttpResult, MembershipBody (+12 more)

### Community 150 - "nexusops-understand.mjs"
Cohesion: 0.33
Nodes (5): COMMON, meta, out, READERS, SCHEMA

### Community 151 - "Invisible account lockout (5 fails -> 15 min, enumeration resistance)"
Cohesion: 0.33
Nodes (6): Invisible account lockout (5 fails -> 15 min, enumeration resistance), Unified error envelope (code, message, request_id), Per-IP rate limiting (Redis fixed window), Request lifecycle (edge -> middleware -> rate limit -> deps -> router), Client IP resolution (resolve_client_ip, TRUSTED_PROXY_CIDRS, XFF overwrite), EmailStr rejects reserved domains (login 422 on .test/.local/.arpa)

### Community 152 - "nginx_capability"
Cohesion: 0.12
Nodes (19): _listener_ownership(), _listening_ports(), _nginx_binary(), nginx_capability(), _nginx_owned_ports(), _nginx_running(), _nginx_status(), _nginx_version() (+11 more)

### Community 153 - "DashboardPage.tsx"
Cohesion: 0.12
Nodes (14): DashboardSummary, DashboardPage, asFeedItem(), badgeLevel(), DashboardPage(), FeedItem, formatTimestamp(), MetaInfo (+6 more)

### Community 154 - "nexusops-draft.mjs"
Cohesion: 0.40
Nodes (4): DOCS, meta, SPINE, VERIFY_RULES

### Community 155 - "notification_sender.py"
Cohesion: 0.16
Nodes (17): NotificationError, Any, BaseException, Exception, Low-level notification transports: SMTP email and outgoing webhooks. These…, POST *payload* as JSON to *url*; 2xx is success, anything else raises. Response…, Raised when a delivery attempt fails. Message is safe to persist., Bounded, single-line, content-free error reason. (+9 more)

### Community 156 - "nexusops-challenge.mjs"
Cohesion: 0.33
Nodes (5): CHALLENGE_COMMON, meta, RESEARCH_COMMON, SCHEMA, TASKS

### Community 157 - "test_agent_ingestion.py"
Cohesion: 0.30
Nodes (10): _enrolled(), _heartbeat(), Agent ingest pipeline: hello, heartbeat, staleness transitions, events., A container absent from a later heartbeat is gone from the daemon., A payload at the agent's cap may be truncated — absence proves nothing., test_heartbeat_at_container_cap_skips_reconciliation(), test_heartbeat_removes_vanished_containers(), test_heartbeat_updates_status_metrics_and_containers() (+2 more)

### Community 158 - "test_schemas_agent.py"
Cohesion: 0.11
Nodes (36): AgentContainerIn, AgentHeartbeatIn, AgentHelloIn, Observed container state reported by an agent., Periodic metrics + observed containers from an enrolled agent. Network counters…, First contact from an agent after enrollment; fills static host facts., test_container_ports_report_the_four_facts(), _container() (+28 more)

### Community 159 - "test_event_publish_drain.py"
Cohesion: 0.25
Nodes (6): _FakeDb, Frames committed inside a task must reach Redis before that task's loop closes.…, Stands in for an ``AsyncSession`` whose only job here is ``sync_session``. A…, The shape of a worker task whose last statement is a commit., test_run_async_publishes_frames_scheduled_by_the_commit_hook(), commit_then_return()

### Community 160 - "main"
Cohesion: 0.11
Nodes (19): build_capabilities(), _build_hello_payload(), _enroll(), _interruptible_sleep(), main(), memory_total_mb(), os_info(), persist_token() (+11 more)

### Community 161 - "monitor_transport.py"
Cohesion: 0.08
Nodes (24): CheckOutcome, coerce_headers(), _decode(), get_transport(), MonitorTransport, Any, BaseException, Protocol (+16 more)

### Community 162 - "test_notifications.py"
Cohesion: 0.46
Nodes (7): NotificationDelivery, _channel(), _delivery(), UUID, Notification channel + delivery-log endpoints. Regression coverage for GET…, test_list_deliveries_filters_by_channel(), test_list_deliveries_serializes_rows()

### Community 163 - "seed.py"
Cohesion: 0.16
Nodes (22): EnvironmentType, Kind of a project-scoped deployment environment (Phase 2). Descriptive only —…, _lock(), _organization_name(), _organization_slug(), datetime, User, Idempotent demo seed: roles, admin user, simulated fleet, monitors, history.… (+14 more)

### Community 164 - "AgentClient"
Cohesion: 0.15
Nodes (8): AgentClient, _docker_raw(), A verifying TLS context. Verification is never disabled. A private/self-hosted…, Refuse to send credentials over plain HTTP to a non-loopback server. The…, One raw Docker API call; returns ``(status, body_bytes)``., _tls_context(), _UnixHTTPConnection, SSLContext

### Community 165 - "SecretsPage.tsx"
Cohesion: 0.13
Nodes (13): SecretRow, SecretsPage, SecretScopeBadge(), CreateSecretModal(), CreateSecretPayload, DeleteSecretModal(), errorMessage(), formatTimestamp() (+5 more)

### Community 166 - "nginx.py"
Cohesion: 0.15
Nodes (20): _header_lines(), _quote(), _rate_zone(), NginxProvider — a pure, deterministic renderer plus the two op wrappers.…, Validate the route's headers and split them by destination., Wrap an already-validated value in quotes for a template slot. Values reaching…, The ``limit_req_zone`` declaration for a rate-limited route., A fixed host redirect, or ``None`` for a normal proxying route. (+12 more)

### Community 167 - "deps.py"
Cohesion: 0.07
Nodes (42): _attach_organization(), get_current_user(), get_identity(), get_optional_user(), _load_permissions(), membership_for_org(), _org_id_from_header(), AsyncSession (+34 more)

### Community 168 - "agent_heartbeat"
Cohesion: 0.14
Nodes (22): agent_enroll(), agent_heartbeat(), agent_hello(), claim_operation(), _presented_token(), DbDep, post, Request (+14 more)

### Community 169 - "RouteHeader"
Cohesion: 0.10
Nodes (11): field_validator, model_validator, RateLimit, One header a route adds. ``target`` says where it lands., One route's request-rate ceiling (rendered as a ``limit_req_zone``)., A fixed host redirect. Phase 4 cannot express a scheme change here. There is…, RouteHeader, RouteRedirect (+3 more)

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
Cohesion: 0.13
Nodes (15): Check an API-key scope list against a required permission. Supports exact match…, scope_matches(), parametrize, test_scope_matches_truth_table(), 0. What shipped (Phase 1), 1. Principles (already true in the codebase, kept), 2. Registry changes (Phase 1 + new subsystems), 3. The five system roles (target) (+7 more)

### Community 174 - "apikeys.py"
Cohesion: 0.16
Nodes (18): create_api_key(), list_api_keys(), CurrentUser, DbSessionDep, delete, get, post, Request (+10 more)

### Community 175 - "2. Entities"
Cohesion: 0.25
Nodes (8): 2.1.1 ApiKey org binding detail, 2.2.1 Environment promotion detail — **shipped in Phase 2**, 2.2 Delivery (existing models, extended), 2.4 Routing & TLS (new subsystem), 2.5 Secrets (re-scoped — **shipped in Phase 2**), 2.6 Observability (existing, org-scoped via parents), 2.7 Backups, connections, billing (new subsystems, design-only in early phases), 2. Entities

### Community 176 - "Platform Security Model — NexusOps"
Cohesion: 0.12
Nodes (16): 10.1 Node revocation playbook (compromised node / leaked agent token), 10.2 Key compromise playbook, 10. Incident response, 1.1 Real vs simulated today (do not mistake one for the other), 1. Scope, stance, and simulation honesty, 2. Assets, 3. Trust boundaries, 4. Tenant isolation model (summary) (+8 more)

### Community 177 - "decide"
Cohesion: 0.23
Nodes (18): decide(), matches_token(), Constant-time comparison of the observed TXT values against the token. TXT…, Turn one observation into the verification outcome — pure, no I/O.…, observation(), parametrize, The verification decision: every outcome, without a network. ``decide`` is…, test_a_sweep_invalidates_a_changed_delegation_even_with_the_token() (+10 more)

### Community 178 - "network_rates"
Cohesion: 0.33
Nodes (6): build_facts(), network_rates(), network_total_bytes(), Sum rx/tx bytes over non-loopback interfaces from /proc/net/dev., Return (rx_kb_s, tx_kb_s) or ``(None, None)`` when not measurable., Open-ended host facts, stored in the node's flexible JSONB blob. Deliberately…

### Community 179 - "container.py"
Cohesion: 0.21
Nodes (12): ContainerRemoveOut, host_ref(), HostRef, LogEntryOut, UUID, Container schemas: list/detail read models, log entries, action results., Summary of the docker host a container runs on., Summary of the server associated with a container. (+4 more)

### Community 180 - "router.py"
Cohesion: 0.40
Nodes (4): websocket, WebSocket endpoint. Mounted by the app factory under ``/api/v1``., Hand the socket to the hub (auth handshake handled there)., websocket_endpoint()

### Community 181 - "_nginx_apply"
Cohesion: 0.13
Nodes (17): _fsync_dir(), _nginx_apply(), Materialize the bundle under ``staged/<id>/`` and return that directory.…, Build a self-contained config for ``nginx -t`` over the staged tree. The…, Move the staged tree over the live one, keeping the previous as backup., Put the previous known-good tree back. Returns whether it was possible., Stage → validate → swap → reload, with a rollback on a failed reload., Persist the last apply outcome atomically (temp + rename). (+9 more)

### Community 182 - "_nginx_bootstrap"
Cohesion: 0.18
Nodes (14): _insert_http_includes(), _nginx_bootstrap(), _nginx_config_test(), _nginx_failure_summary(), Reload nginx via ``-s reload``, falling back to a SIGHUP of the master., Idempotent, minimal, reversible hook-up of the managed include. The only change…, Insert the include lines at the end of the single top-level ``http`` block. A…, Make control characters safe and bound the result. Never touches container… (+6 more)

### Community 183 - "8. Upstream binding and re-render triggers"
Cohesion: 0.33
Nodes (6): 8.1 Binding rules, 8.2 Certificate selection rule (this doc owns it) — **Phase 5 target design**, 8.3 Re-render triggers, 8.4 Drift and reconciliation, 8.5 How deployments hook routing (post-deploy route sync), 8. Upstream binding and re-render triggers

### Community 184 - "Multi-Tenancy Architecture"
Cohesion: 0.22
Nodes (9): 10. Migration (Phase 1), 1. Tenancy invariants, 2.1 Org creation — v1 decision, 2. Org resolution on every request, 4. Background jobs, 6. Agents, 7. The IDOR suite, 8. What stays global (+1 more)

### Community 185 - "NotificationChannel"
Cohesion: 0.22
Nodes (19): NotificationChannel, A delivery target (email address / webhook endpoint). ``config_ciphertext``…, EmailConfig, _audit(), create_channel(), decrypt_channel_config(), delete_channel(), encrypt_config() (+11 more)

### Community 186 - "maintenance.py"
Cohesion: 0.08
Nodes (47): _run(), _candidates(), _run(), _run(), aggregate_metrics(), _run(), _collect_logs(), expire_operations() (+39 more)

### Community 187 - "role_service.py"
Cohesion: 0.15
Nodes (24): create_role(), delete_role(), effective_permissions(), get_role(), list_roles(), permissions_for_role(), AsyncSession, Request (+16 more)

### Community 188 - "instant_pacing"
Cohesion: 0.40
Nodes (4): instant_pacing(), fixture, MonkeyPatch, Remove the per-line sleeps; pacing bounds are asserted separately.

### Community 189 - "phase3.spec.ts"
Cohesion: 0.15
Nodes (10): frontend_e2e_fixtures_expect, AGENT, NodeDetail, OperationRow, REPO_ROOT, ref_node_child_process, ref_node_fs, ref_node_os (+2 more)

### Community 190 - "server.py"
Cohesion: 0.17
Nodes (11): _clean_tag_names(), DockerHostSummary, EnrollTokenOut, Server API schemas: create/update payloads, list/detail outputs, enrollment., Compact system event projection for server timelines., One-time agent enrollment token. The raw value is never stored., Strip, drop empties and de-duplicate tag names case-insensitively., ServerCounts (+3 more)

### Community 191 - "docs/engineering-report.md - build and verification report"
Cohesion: 0.27
Nodes (12): docker-compose.dev.yml - dev overlay, docker-compose.docker-sock.yml - docker socket override, docker-compose.yml - full stack definition, docs/agent.md - agent guide, docs/api.md - API guide, Append-only audit log (Postgres BEFORE UPDATE OR DELETE trigger), docs/deployment.md - deployment and operations guide, docs/development.md - developer guide (+4 more)

### Community 192 - "get_latest_server_metrics"
Cohesion: 0.25
Nodes (11): get_dashboard_summary(), get_latest_server_metrics(), get_server_metrics(), CurrentUser, DbDep, Depends, get, UUID (+3 more)

### Community 193 - "test_migration_drift.py"
Cohesion: 0.25
Nodes (7): alembic_autogenerate, alembic_migration, Model / migration drift: the schema in the database must match the models.…, ``Base.metadata`` and the migrated database must describe the same schema., The DB whitelist and ``OperationType`` are the same closed set. The migration…, test_models_and_migrations_do_not_drift(), test_operations_type_check_matches_the_enum()

### Community 194 - "test_rbac.py"
Cohesion: 0.29
Nodes (9): _invite_user(), _org_headers(), Role-based access control: least-privileged users are properly boxed in., Admin invites a user with *role_name*; returns their credentials dict., Headers for an invited user, scoped to the organization they joined. An account…, Regression: a superadmin-owned key is still limited to its scope list. The…, test_operator_reads_but_cannot_manage_secrets(), test_scoped_api_key_cannot_exceed_its_grant() (+1 more)

### Community 195 - "ChannelType"
Cohesion: 0.40
Nodes (4): ChannelType, ChannelCreate, ChannelUpdate, model_validator

### Community 196 - "20261010_1200-f4a5b6c7d8e9_phase4_domains_and_routes.py"
Cohesion: 0.31
Nodes (9): downgrade(), _drop_tenant_policies(), _grant(), _in_list(), Phase 4 — domains, routes and the routing schema. Adds, in one migration with a…, Grant the app role on *table*; the migration role GUC carries the name. The…, The two-policy shape every tenant table uses: tenant + system scope., _tenant_policies() (+1 more)

### Community 197 - "_raw_probe"
Cohesion: 0.20
Nodes (10): _app_role_dsn(), A libpq DSN for the RLS-enforced application role (no ORM, no guard)., Run one statement as ``nexusops_app`` with an explicit GUC. Parameterized like…, Raw SQL as the application role: the policies alone return nothing. Written…, Adding ``org_id`` to ``audit_logs`` must not have opened a way to edit it. The…, ``WITH CHECK`` is not decoration: an unlucky INSERT cannot cross tenants., _raw_probe(), test_audit_trail_is_still_append_only_after_tenancy() (+2 more)

### Community 198 - "Product Roadmap — NexusOps Multi-Tenant Platform"
Cohesion: 0.12
Nodes (17): 0. Stance, 10. Phase 7 — Teams, grants & custom roles — **proposal, not implemented**, 11. Phase 8 — Backups — **proposal, not implemented**, 12. Phase 9 — Billing & metering — **proposal, not implemented**, 13.1 Scope-creep gates — what must be true before each expansion, 13. First commercially meaningful version, 14. Biggest risks (short form), 15. Reading order (+9 more)

### Community 199 - "Platform Vision — NexusOps"
Cohesion: 0.20
Nodes (10): 1. Where NexusOps is today, 2.1 What we are NOT building, 2.2 The wedge (differentiation), 2. The direction, 3. Guiding principles, 4. Customer journey (target), 5.1 Architecture overview (target), 5. Control plane / data plane boundary (+2 more)

### Community 200 - "enqueue.py"
Cohesion: 0.39
Nodes (8): after_commit(), _on_commit(), _on_rollback(), Any, AsyncSession, Deferred Celery handoff: enqueue only after the creating transaction commits. A…, Run ``factory`` once the current transaction commits. ``label`` names the work…, _run()

### Community 201 - "test_monitors_incidents.py"
Cohesion: 0.27
Nodes (9): _create_monitor(), Monitor checks driving the full down -> incident -> recovery lifecycle., Regression: probe headers and URL query credentials never leave the API. Probe…, A monitor's checks, incidents and timeline all live in its organization, so the…, test_check_now_endpoint_runs_immediately(), test_down_then_recover_lifecycle(), test_metadata_endpoint_and_private_target_blocked(), test_monitor_responses_mask_probe_credentials() (+1 more)

### Community 202 - "2. The Node concept"
Cohesion: 0.29
Nodes (6): Alias for :attr:`extra`, so the API can expose open-ended agent facts. The…, 2.3 Infrastructure — Nodes, 2.1 Current shape (real), 2.2 Changes for the target model, 2.3 Capabilities (implemented, Phase 3), 2. The Node concept

### Community 203 - "ProxyProvider"
Cohesion: 0.33
Nodes (5): ProxyProvider, Any, Protocol, What ``app.services.proxy_service`` is allowed to assume about a provider. The…, 11. Post-deploy hooks

### Community 204 - "ApplicationBase"
Cohesion: 0.40
Nodes (4): ApplicationBase, Any, field_validator, Shared application fields; ``build_config`` is a free-form dict.

### Community 205 - "DeploymentRunner"
Cohesion: 0.33
Nodes (5): DeploymentRunner, Protocol, Adapter interface implemented by real (future) and simulated runners., Return the ordered step names for this run., 2. What survives unchanged

### Community 206 - "20261008_1200-b2c3d4e5f6a7_add_projects_and_environments.py"
Cohesion: 0.53
Nodes (5): downgrade(), _drop_constraint(), _quoted_list(), Phase 2 — projects & environments: env promotion, config, secret versions. This…, upgrade()

### Community 207 - "20261009_1300-a1b2c3d4e5f6_add_phase3_nodes_and_agent_v2.py"
Cohesion: 0.40
Nodes (4): _grant(), Phase 3 — Nodes & Agent v2 schema. Adds, in one migration with a single head: *…, Grant the app role on *table*; the migration role GUC carries the name. The…, upgrade()

### Community 208 - "_live_bundle_id"
Cohesion: 0.20
Nodes (10): _allowed_bundle_path(), _live_bundle_id(), _live_files(), The bundle fingerprint — byte-identical to the control plane's algorithm.…, Read the live managed tree, or ``None`` when it does not exist yet., Fingerprint of the configuration tree currently on disk., Independently validate a bundle. Anything unexpected is refused., _template_version_of() (+2 more)

### Community 209 - "_invite"
Cohesion: 0.33
Nodes (6): _invite(), The user directory is "who is in this organization", not "who exists".…, ``sessions`` has no tenant column: the owning membership is the boundary.…, Invite a fresh account into the caller's organization and log it in., test_member_directory_only_ever_shows_the_active_tenant(), test_one_tenants_session_list_and_revocation_stop_at_its_members()

### Community 210 - "lax"
Cohesion: 0.40
Nodes (5): lax(), fixture, Production posture: private targets are NOT allowed (resolution runs)., Simulation posture: resolution skipped, syntax still enforced., strict()

### Community 213 - ".route_file_path"
Cohesion: 0.50
Nodes (3): Where a route's fragment lands, so the service can name it in events., A deterministic, filesystem-safe fragment name for one route., _route_key()

### Community 214 - "pytest"
Cohesion: 0.16
Nodes (12): created_at server defaults must evaluate per insert, not at table creation., Regression: system_events and audit_logs shipped with DEFAULT 'now()' (quoted…, test_audit_and_event_created_at_defaults_are_dynamic(), UUID, Phase 2.2 — the environment-type correction follows the documented precedence.…, Only the previous migration's ``PROD`` output is corrected. A row already…, Create one legacy (application-scoped) environment per case., Every branch of the slug-first rule, end to end through ``head``. (+4 more)

### Community 215 - "_pace"
Cohesion: 0.67
Nodes (3): _pace(), Deterministic per-line delay between 0.05s and 0.35s., test_pace_bounds()

## Knowledge Gaps
- **459 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+454 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2264 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **25 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `6. Tooling: reproducible e2e` connect `maintenance.py` to `logging.py`, `client.ts`, `hub.py`, `NotFound`, `test_tenant_isolation.py`, `auth_service.py`?**
  _High betweenness centrality (0.265) - this node is a cross-community bridge._
- **Why does `useEventStream()` connect `client.ts` to `apiGet`, `App.tsx`, `ServerDetailPage.tsx`, `DashboardPage.tsx`, `maintenance.py`?**
  _High betweenness centrality (0.264) - this node is a cross-community bridge._
- **Why does `TenancyScopeError` connect `test_tenant_isolation.py` to `AuthContext`, `deps.py`, `assert_error_code`, `core/tenancy.py`, `enums.py`, `log_service.py`, `maintenance.py`?**
  _High betweenness centrality (0.113) - this node is a cross-community bridge._
- **Are the 93 inferred relationships involving `AuthContext` (e.g. with `TenancyScopeError` and `MembershipStatus`) actually correct?**
  _`AuthContext` has 93 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `APIModel` (e.g. with `OperationSpec` and `test_specs_reject_unknown_params()`) actually correct?**
  _`APIModel` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `apiGet()` (e.g. with `ContainerDetailPage.test.tsx` and `mockApi()`) actually correct?**
  _`apiGet()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `Server` (e.g. with `ServerStatus` and `2.3 Infrastructure — Nodes`) actually correct?**
  _`Server` has 5 INFERRED edges - model-reasoned connections that need verification._