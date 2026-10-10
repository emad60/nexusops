# Graph Report - nexusops  (2026-10-11)

## Corpus Check
- 354 files · ~366,454 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: (none) 10, .example 1, .service 1)

## Summary
- 5750 nodes · 16922 edges · 216 communities (192 shown, 24 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1333 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d840e770`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- apiGet
- project_service.py
- ApiKeysPage.tsx
- test_phase4_routing.py
- incident_service.py
- types.ts
- resolve_client_ip
- Path
- App.tsx
- test_agent_v2.py
- test_operations.py
- ServerDetailPage.tsx
- APIModel
- client.ts
- projects.py
- models/__init__.py
- deployment_engine.py
- Container
- enrollment_service.py
- rollback_secret
- test_deployments_simulated.py
- list_containers
- enums.py
- get_settings
- Domain Routing — NexusOps
- monitors.py
- Node & Agent Architecture
- test_agent_backoff.py
- SimulatedDeploymentRunner
- nexusops_agent.py
- integration/conftest.py
- auth_service.py
- containers.py
- test_rate_limit.py
- docker_hosts.py
- test_ws_hub.py
- NginxBundle
- v1/search.py
- publish
- v1/channels.py
- DockerProvider
- test_monitor_transport.py
- Deployment Architecture — NexusOps (target state)
- AuthContext.tsx
- v1/health.py
- require_permission
- list_routes
- test_phase3_nodes.py
- test_ssrf.py
- NotFound
- list_alerts
- record
- proxy_service.py
- test_migration_phase21.py
- v1/auth.py
- test_agent_nginx_contract.py
- create_user
- alembic
- notification_service.py
- test_tenant_isolation.py
- compilerOptions
- v1/deployments.py
- errors.py
- dns_verifier.py
- test_phase2_environments.py
- route_service.py
- test_schema_redaction.py
- deps.py
- encrypt_str
- package.json
- test_event_registry.py
- test_secrets.py
- test_nginx_renderer.py
- domain_service.py
- api service (FastAPI / uvicorn :8000)
- hub.py
- server_service.py
- list_domains
- incidents.py
- test_phase2_secrets.py
- RolesPage.tsx
- monitor_service.py
- canonicalize_name
- tests/conftest.py
- resolve_secrets_for_environment
- AuthContext
- devDependencies
- Conflict
- log_service.py
- Settings
- DomainStatus
- validate_config
- alert_service.py
- apply_scope_to_session
- test_phase21_secret_version_integrity.py
- StepLine
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- journey.spec.ts
- enqueue.py
- redact_mapping
- README.md - NexusOps overview
- env.py
- hash_token
- _rows
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- LoginPage.tsx
- docker_real.py
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- ScopedSession
- organization_service.py
- test_app_gating.py
- dnsmock.py
- scripts
- v1/agent.py
- test_tenancy_allowlist.py
- test_migration_phase2.py
- dependencies
- @tanstack/react-query
- generate_secrets.sh
- ControlHandler
- server_payload
- _exec
- middleware.py
- OperationError
- list_operations
- _dns_stub
- install.sh
- docker-entrypoint.sh
- integration/__init__.py
- AuditLogPage.test.tsx
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
- DockerHostsPage.test.tsx
- nexusops-draft.mjs
- notification_sender.py
- nexusops-challenge.mjs
- test_agent_ingestion.py
- test_schemas_agent.py
- test_run_async_publishes_frames_scheduled_by_the_commit_hook
- main
- monitor_transport.py
- list_sessions
- seed.py
- AgentClient
- client_ip
- nginx.py
- resolve_auth
- report_operation_result
- RateLimit
- test_agent_contract.py
- 20261009_1000-c3d4e5f6a7b8_enforce_secret_version_integrity.py
- _FakeAsyncClient
- permissions.py
- paginate
- sweep_deployments
- Platform Security Model — NexusOps
- ContainerListPage.test.tsx
- network_rates
- .dispatch
- router.py
- _nginx_apply
- _nginx_bootstrap
- 8. Upstream binding and re-render triggers
- Multi-Tenancy Architecture
- update_channel
- run_async
- role_service.py
- instant_pacing
- phase3.spec.ts
- 20261004_1200-e7c4a2b9d1f3_add_operations_framework.py
- docs/engineering-report.md - build and verification report
- get_latest_server_metrics
- test_migration_drift.py
- test_rbac.py
- channel.py
- get_meta
- _raw_probe
- Product Roadmap — NexusOps Multi-Tenant Platform
- Platform Vision — NexusOps
- install_hint
- NotificationChannel
- pytest
- ProxyProvider
- ApplicationBase
- .__init__
- 20261008_1200-b2c3d4e5f6a7_add_projects_and_environments.py
- MonitorCreate
- _live_bundle_id
- test_remove_honours_force_and_never_shells
- .__tablename__
- .apply_params
- .route_file_path
- test_migration_phase22.py
- test_domain_creation_rejects_invalid_names
- test_existing_url_monitors_are_untouched_by_routing

## God Nodes (most connected - your core abstractions)
1. `AuthContext` - 155 edges
2. `APIModel` - 145 edges
3. `apiGet()` - 91 edges
4. `Server` - 89 edges
5. `record()` - 86 edges
6. `NotFound` - 83 edges
7. `get_settings()` - 82 edges
8. `publish()` - 71 edges
9. `apiPost()` - 70 edges
10. `useToast()` - 67 edges

## Surprising Connections (you probably didn't know these)
- `2. Org resolution on every request` --references--> `resolve_auth()`  [INFERRED]
  docs/multi-tenancy.md → backend/app/api/deps.py
- `3. Cross-cutting decisions` --references--> `require_permission()`  [INFERRED]
  docs/domain-model.md → backend/app/api/deps.py
- `10. Phase 7 — Teams, grants & custom roles — **proposal, not implemented**` --references--> `require_permission()`  [INFERRED]
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

## Communities (216 total, 24 thin omitted)

### Community 0 - "apiGet"
Cohesion: 0.06
Nodes (90): apiDelete(), apiGet(), apiPatch(), apiPost(), ApplicationOut, ENVIRONMENT_TYPE_LABELS, EnvironmentType, IncidentEventOut (+82 more)

### Community 1 - "project_service.py"
Cohesion: 0.11
Nodes (52): DeploymentEnvironment, A **project-scoped** deployment environment (Phase 2 promotion). The…, EnvironmentCreate, EnvironmentUpdate, Payload to create an environment under a project., Partial environment update; omitted fields are left untouched. Config is…, ProjectCreate, ProjectUpdate (+44 more)

### Community 2 - "ApiKeysPage.tsx"
Cohesion: 0.09
Nodes (19): ApiKeyOut, ApiKeysPage, ApiKeyCreatedOut, handleCopyKey(), copyText(), describeError(), EMPTY_FORM, GROUP_STYLE (+11 more)

### Community 3 - "test_phase4_routing.py"
Cohesion: 0.08
Nodes (78): MonitorTargetType, What a monitor observes (domain-model.md §2.6, polymorphic targets). ``URL`` is…, Keep every routed node's live configuration matching the desired bundle. One…, sweep_routes(), assert_error_code(), Assert envelope shape + code; returns the inner error object., _claim(), _container_id() (+70 more)

### Community 4 - "incident_service.py"
Cohesion: 0.23
Nodes (22): IncidentEventKind, IncidentStatus, Incident, acknowledge(), _add_event(), add_note(), get_incident(), list_incidents() (+14 more)

### Community 5 - "types.ts"
Cohesion: 0.02
Nodes (87): AlertOut, CapabilityReport, ChannelOut, CheckOut, DeliveryOut, DeploymentLogLine, DeploymentStatus, DomainDetailOut (+79 more)

### Community 6 - "resolve_client_ip"
Cohesion: 0.17
Nodes (22): _is_trusted(), _parse_networks(), Request, Client-IP resolution behind chained reverse proxies. The API never takes TCP…, Parse a comma-separated CIDR list; malformed entries are skipped., Real client address for *request* per the trust model above., resolve_client_ip(), make_request() (+14 more)

### Community 7 - "Path"
Cohesion: 0.12
Nodes (15): Path, An unloadable CA file must error, never silently fall back to no verify., A throwaway key + self-signed cert for ``localhost`` (real handshakes)., A one-shot HTTPS server; records a failed handshake instead of crashing., A real handshake against a self-signed server must fail verification., Trusting that same cert as a CA lets the identical handshake through., A link-local URL over plain HTTP must fail before any request or write., _self_signed_cert() (+7 more)

### Community 8 - "App.tsx"
Cohesion: 0.04
Nodes (103): DeploymentOut, Page, ProjectOut, AlertsPage, App(), AuditLogPage, ContainerListPage, DeploymentListPage (+95 more)

### Community 9 - "test_agent_v2.py"
Cohesion: 0.09
Nodes (33): agent_fixture(), _load_agent(), Any, fixture, parametrize, Agent protocol v2: honest metrics, capability detection, and the executor. The…, Phase 4 shipped three nginx ops — no file primitive, no command primitive., Trusting a private CA must not weaken verification. (+25 more)

### Community 10 - "test_operations.py"
Cohesion: 0.07
Nodes (54): expire_operations(), Expire node operations past their deadline — pending and claimed alike. A…, _dispatch(), _dispatch_body(), _enrolled_node(), _mutate_in_system_scope(), MonkeyPatch, Node operations: the compare-and-set state machine and its tenant boundary.… (+46 more)

### Community 11 - "ServerDetailPage.tsx"
Cohesion: 0.06
Nodes (42): ContainerOut, MetricPoint, ServerDetail, ServerSummary, ChartSeries, LineChart(), LineChartProps, PAD (+34 more)

### Community 12 - "APIModel"
Cohesion: 0.03
Nodes (121): AgentContainerPortIn, AgentTokenRotation, CapabilityReport, Agent-facing schemas. Payloads are data only — never executed. Wire protocol v2…, One published-port binding of a container, as docker reports it. Four distinct…, A pending credential rotation, delivered on the agent's next beat. Served…, One node-reported capability. ``present`` defaults to false, and a capability…, AlertOut (+113 more)

### Community 13 - "client.ts"
Cohesion: 0.05
Nodes (54): API_BASE, ApiError, apiRequest(), buildUrl(), extractError(), getAccessToken(), getActiveOrgId(), onActiveOrgChange() (+46 more)

### Community 14 - "projects.py"
Cohesion: 0.13
Nodes (45): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+37 more)

### Community 15 - "models/__init__.py"
Cohesion: 0.08
Nodes (60): _org_scoped_classes(), Mapped classes marked :class:`~app.models.base.OrgScoped`. Reads the mapper…, Base, big_serial_pk(), json_column(), org_id_column(), OrgScoped, datetime (+52 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.11
Nodes (58): deployment_log_channel(), Deployment, DeploymentStep, AlertSeverity, DeploymentStatus, DeploymentTrigger, EventLevel, StepStatus (+50 more)

### Community 17 - "Container"
Cohesion: 0.07
Nodes (40): ContainerStatus, LogLevel, Container, Observed container state mirrored from an agent or docker provider., LogEntry, ContainerInfo, Normalized view of a container as reported by any provider., Any (+32 more)

### Community 18 - "enrollment_service.py"
Cohesion: 0.09
Nodes (35): generate_enrollment_token(), An enrollment credential (``nxk_``): single-use, short-lived, org-scoped.…, Return the active org id or raise; used by services that need it explicitly., require_org(), EnrollmentToken, One single-use credential that enrolls (or claims) exactly one node., Whether the row could still be redeemed (not a race-safe check)., EnrollmentTokenState (+27 more)

### Community 19 - "rollback_secret"
Cohesion: 0.13
Nodes (27): create_secret(), delete_secret(), get_secret(), list_secret_versions(), list_secrets(), DbSession, delete, get (+19 more)

### Community 20 - "test_deployments_simulated.py"
Cohesion: 0.15
Nodes (29): execute_deployment(), Run one deployment to a terminal state. Never raises; safe to re-run., get_application(), get_environment(), _as_worker(), _delivery_chain(), _owner_ctx(), _queue() (+21 more)

### Community 21 - "list_containers"
Cohesion: 0.07
Nodes (49): _action_route(), _endpoint(), _container_out(), _decode_frame(), _ev(), get_container(), _like_pattern(), list_container_logs() (+41 more)

### Community 22 - "enums.py"
Cohesion: 0.09
Nodes (37): ContainerHealth, CredentialKind, MetricGranularity, Closed registries of domain enumerations. Member names equal their values…, String enum; member names equal values so name/value storage never disagrees., How far a route's *removal* has got, which ``config_state`` cannot say. A route…, RouteRemovalState, StrEnum (+29 more)

### Community 23 - "get_settings"
Cohesion: 0.07
Nodes (54): argon2, argon2_exceptions, fail_on_bad_config(), get_settings(), Return the cached settings singleton., Exit immediately with a readable message if configuration is invalid. Also…, get_engine(), AsyncEngine (+46 more)

### Community 24 - "Domain Routing — NexusOps"
Cohesion: 0.09
Nodes (23): 10. Wildcards and catch-all, 11. User journey, 12. API surface, permissions, audit, 13. Monitoring tie-in, 1. Scope and current state, 2. Where nginx runs, 3.1 Domain, 3.2 Route (+15 more)

### Community 25 - "monitors.py"
Cohesion: 0.16
Nodes (32): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+24 more)

### Community 26 - "Node & Agent Architecture"
Cohesion: 0.10
Nodes (21): 1. Scope and stance, 3.2 Enrollment v2, 3.3 Token storage & rotation with dual-token grace, 3.4 Revocation semantics — fixing the 401 hot-loop, 3.5 Reconnect / offline states, 3. Agent lifecycle, 5.1 Model and lifecycle, 5.2 Whitelisted operation types (+13 more)

### Community 27 - "test_agent_backoff.py"
Cohesion: 0.15
Nodes (21): agent_fixture(), _install_sleep(), fake_sleep(), _load_agent(), _patch_host(), Any, fixture, MonkeyPatch (+13 more)

### Community 28 - "SimulatedDeploymentRunner"
Cohesion: 0.22
Nodes (25): Staged docker-style simulation used by v1 deployments., Canonical step identifiers stored on :class:`DeploymentStep` rows., SimulatedDeploymentRunner, StepName, _collect(), _ctx(), Unit tests for SimulatedDeploymentRunner (async generators, no broker)., RESOLVE_CONFIG is planned by the engine, not produced by a runner. (+17 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.09
Nodes (29): build_heartbeat(), collect_container_stats(), collect_containers(), _container_ports(), _container_status(), cpu_percent_since(), disk_stats(), docker_capability() (+21 more)

### Community 30 - "integration/conftest.py"
Cohesion: 0.11
Nodes (26): alembic_config, close_redis(), _admin_dsn(), _clean_slate(), client(), _ensure_database(), _migrated_database(), org_db() (+18 more)

### Community 31 - "auth_service.py"
Cohesion: 0.10
Nodes (47): active_memberships(), The user's memberships in non-suspended organizations, oldest first. Reads only…, System scope bound to *db*, for rows that have no organization. Used by exactly…, system_write_scope(), _audit(), _auth_event_scope(), _bootstrap_organization(), change_own_password() (+39 more)

### Community 32 - "containers.py"
Cohesion: 0.06
Nodes (83): asyncio, Container API: listing/detail, lifecycle actions, removal, logs, streaming.…, BadRequest, configure_logging(), get_logger(), _orjson_dumps(), Any, Structured logging via structlog. Every log record carries timestamp, level,… (+75 more)

### Community 33 - "test_rate_limit.py"
Cohesion: 0.18
Nodes (16): RateLimited, _memory_count_and_ttl(), rate_limit(), Fixed-window counter backed by process memory. Returns (count, ttl)., Return a dependency enforcing *limit* requests per window per IP. With…, _clean_memory_windows(), _FakeRequest, fixture (+8 more)

### Community 34 - "docker_hosts.py"
Cohesion: 0.07
Nodes (55): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+47 more)

### Community 35 - "test_ws_hub.py"
Cohesion: 0.05
Nodes (62): AppError, Exception, Base class for expected, client-facing errors., _authenticate_api_key(), _authenticate_jwt(), _bind_organization(), _close_socket(), Connection (+54 more)

### Community 36 - "NginxBundle"
Cohesion: 0.11
Nodes (18): Render the complete desired state for *node*. A full tree every time — never a…, BundleFile, fingerprint_files(), is_allowed_bundle_path(), NginxBundle, field_validator, One rendered file. The path is allowlisted, the content is bounded., Deterministic fingerprint over the complete rendered tree. Path order is… (+10 more)

### Community 37 - "v1/search.py"
Cohesion: 0.13
Nodes (31): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+23 more)

### Community 38 - "publish"
Cohesion: 0.13
Nodes (29): get_redis(), ping(), Shared async Redis client., ActorType, SystemEvent, create_api_key(), Create a key for *user_id*. Returns ``(row, raw_key)`` — raw shown once. The…, _after_commit_publish() (+21 more)

### Community 39 - "v1/channels.py"
Cohesion: 0.16
Nodes (26): create_channel(), delete_channel(), get_channel(), list_channels(), list_deliveries(), DbDep, delete, Depends (+18 more)

### Community 40 - "DockerProvider"
Cohesion: 0.09
Nodes (10): DockerProvider, Any, Protocol, List containers visible to the provider., Inspect a single container by id (short ids allowed)., List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``., List volumes: keys ``name``, ``driver``, ``mountpoint``., List networks: keys ``name``, ``driver``, ``scope``. (+2 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.13
Nodes (34): CheckResult, HTTPMonitorTransport, Deterministic fake checker for ``sim://`` monitors and demo environments.…, Real HTTP(S) probe using httpx with per-monitor settings. Redirects are…, SimulatedTransport, _check(), clock(), FakeClock (+26 more)

### Community 42 - "Deployment Architecture — NexusOps (target state)"
Cohesion: 0.15
Nodes (13): 10. Events and WS during runs, 12. Rollback semantics (existing behavior kept), 13. The simulated runner stays — labeled, 14. Open questions, 1. Current state — what is real and what is simulated, 3. Target pipeline, 4. Runner registry — the DI fix, 6. Phased scope (+5 more)

### Community 43 - "AuthContext.tsx"
Cohesion: 0.02
Nodes (83): Membership, SearchResult, User, AuthContext, AuthProvider(), AuthState, isOrgSelectionError(), MeResponse (+75 more)

### Community 44 - "v1/health.py"
Cohesion: 0.20
Nodes (13): liveness(), get, Response, Health probes: liveness (always cheap) and readiness (checks dependencies).…, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness(), HealthOut (+5 more)

### Community 45 - "require_permission"
Cohesion: 0.11
Nodes (26): permission_dep(), Any, Dependency factory enforcing a permission; returns 403 when denied., require_permission(), _check(), _decode_cursor(), _encode_cursor(), list_event_types() (+18 more)

### Community 46 - "list_routes"
Cohesion: 0.19
Nodes (22): create_route(), delete_route(), disable_route(), _domain_status(), enable_route(), get_route(), list_routes(), AsyncSession (+14 more)

### Community 47 - "test_phase3_nodes.py"
Cohesion: 0.14
Nodes (35): Run the enclosed block with tenant filtering off (maintenance only). ``reason``…, system_scope(), _create_token(), _dispatch(), _enroll(), _enrolled_node(), _load_agent_module(), _mutate_in_system_scope() (+27 more)

### Community 48 - "test_ssrf.py"
Cohesion: 0.06
Nodes (79): UnprocessableEntity, assert_safe_tcp_endpoint(), assert_safe_url(), _is_forbidden_address(), is_simulation_url(), ValueError, _raise_block(), Validate *url* for outbound requests; return the parsed URL or raise 422.… (+71 more)

### Community 49 - "NotFound"
Cohesion: 0.11
Nodes (44): NotFound, An encrypted configuration value, scoped to org, project or environment.…, One immutable value of a :class:`Secret` — append-only history. A row is…, Secret, SecretVersion, _actor_type(), _collect_refs(), create_secret() (+36 more)

### Community 50 - "list_alerts"
Cohesion: 0.21
Nodes (14): list_alerts(), mark_all_read(), mark_read(), CurrentUser, DbDep, Depends, get, post (+6 more)

### Community 51 - "record"
Cohesion: 0.05
Nodes (78): apply_node_proxy_config(), create_enrollment_token(), create_server(), delete_server(), _detail(), _enrollment_created(), _enrollment_out(), get_server() (+70 more)

### Community 52 - "proxy_service.py"
Cohesion: 0.06
Nodes (73): ListenerOwnership, ProxyApplyOutcome, Terminal outcome of one ``nginx.apply`` operation on a node., Who holds one required listener port, per the node's pre-flight. The…, NodeProxyCapabilityOut, The node's reported nginx capability, bounded to the useful facts., One genuinely usable published port reported by the node's agent., A container that can actually back a route on this node. (+65 more)

### Community 53 - "test_migration_phase21.py"
Cohesion: 0.12
Nodes (17): Phase 2.1 corrective migration: legacy ``environment_type`` classification.…, Every case is classified as documented, ids and ownership intact., An explicit non-DEV classification survives the corrective migration. The…, The correction is part of ``head`` and adds no extra Alembic head., Insert one legacy environment per case, in two organizations., _seed_typed_environments(), test_corrective_migration_is_reachable_from_head(), test_corrects_legacy_environment_types() (+9 more)

### Community 54 - "v1/auth.py"
Cohesion: 0.06
Nodes (70): change_password(), _clear_refresh_cookie(), _cookies_secure(), login(), logout(), me(), _optional_actor(), AsyncSession (+62 more)

### Community 55 - "test_agent_nginx_contract.py"
Cohesion: 0.08
Nodes (52): _agent_bundle(), agent_fixture(), _bootstrap_fixture(), _load_agent(), Any, fixture, parametrize, Path (+44 more)

### Community 56 - "create_user"
Cohesion: 0.18
Nodes (18): create_user(), deactivate_user(), get_user(), list_users(), CurrentUser, DbSessionDep, delete, get (+10 more)

### Community 57 - "alembic"
Cohesion: 0.04
Nodes (26): alembic, downgrade(), rename ``server.*`` permission codenames to ``node.*`` The Node/Server…, _rename_permissions(), upgrade(), Fix pre-existing model/migration drift (surfaced by the new drift check). Two…, downgrade(), Phase 2.1 — correct legacy ``environment_type`` classification. The Phase 2… (+18 more)

### Community 58 - "notification_service.py"
Cohesion: 0.14
Nodes (27): _as_uuid(), _attempt_delivery(), decode_delivery_cursor(), decrypt_channel_config(), dispatch_event_frame(), _send(), dispatcher_loop(), encode_delivery_cursor() (+19 more)

### Community 59 - "test_tenant_isolation.py"
Cohesion: 0.05
Nodes (70): bearer(), cookie_attributes(), error_of(), login_account(), login_headers(), Any, AsyncClient, Response (+62 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "v1/deployments.py"
Cohesion: 0.06
Nodes (66): _attribute_step_idx(), cancel_deployment(), _emails_for(), get_deployment(), list_application_deployments(), list_deployment_logs(), _list_deployments(), _parse_sort() (+58 more)

### Community 62 - "errors.py"
Cohesion: 0.10
Nodes (17): _error_payload(), FastAPI, Request, Error taxonomy and the single place where API error envelopes are shaped. Every…, register_exception_handlers(), handle_app_error(), handle_http_exception(), handle_unexpected() (+9 more)

### Community 63 - "dns_verifier.py"
Cohesion: 0.09
Nodes (36): apex_of(), The name a wildcard Domain is anchored at (``*.example.com`` →…, decide(), _discover_nameservers(), matches_token(), _normalise_ns(), observe(), Observer (+28 more)

### Community 64 - "test_phase2_environments.py"
Cohesion: 0.18
Nodes (22): _environment(), _project(), parametrize, Phase 2: project-scoped environments, config layering, and their isolation. The…, Uniqueness is ``(project_id, slug)`` — not instance-wide., The update path is validated too (the pre-Phase-2 gap)., Knowing an environment UUID is not access: the project link must hold., Another tenant cannot reach the project, its environments, or its detail. (+14 more)

### Community 65 - "route_service.py"
Cohesion: 0.10
Nodes (51): Last nginx apply outcome for a route, as reported by its node's agent.…, RouteConfigState, One hostname+path served from one container on one node. Relationship rules the…, Route, bundle_summary(), Bounded, human-readable bundle metadata for audit rows and UI. Never includes…, enqueue_apply(), Raise a named conflict when routing may not be managed on this node. (+43 more)

### Community 66 - "test_schema_redaction.py"
Cohesion: 0.18
Nodes (17): is_sensitive_header(), mask_sensitive_headers(), True when *name* looks like it carries a credential (Authorization etc.)., Return a copy of *headers* with sensitive values replaced by a mask., mask_target(), Human-readable masked target safe to expose over the API. For webhook families…, _monitor_out(), Outbound-schema redaction: monitor probe credentials and webhook targets.… (+9 more)

### Community 67 - "deps.py"
Cohesion: 0.13
Nodes (34): FastAPI dependencies: database session, authenticated tenant context, RBAC…, Alert inbox endpoints. Authenticated users see the shared operator feed., API key routes — self-service management of the caller's own machine…, Audit log API. Strictly read-only: the table is append-only by design., Domain endpoints: add, list, inspect, verify, re-verify, delete. Authorization…, routes_for_domain(), Instance metadata: version, mode, and the caller's effective capabilities. The…, Metrics query API: node timeseries, latest snapshot, dashboard summary. (+26 more)

### Community 68 - "encrypt_str"
Cohesion: 0.05
Nodes (41): digest_of(), encrypt_str(), Short server-verifiable digest used for change detection display. HMAC-SHA256…, test_digest_length_and_determinism(), 10. Status/expiry tracking and monitor tie-in, 12. Audit and events, 13. Non-goals, 1. Scope and current state (+33 more)

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
Cohesion: 0.14
Nodes (36): NginxProvider, ValueError, The only production provider in Phase 4., Rendering refused the input. Always a bug or a corrupt row, never a leak., RenderError, provider(), fixture, parametrize (+28 more)

### Community 73 - "domain_service.py"
Cohesion: 0.09
Nodes (44): The exact TXT owner name a user must publish at their provider., verification_record_name(), Domain, One DNS name an organization is proving it controls. ``name`` is canonical (see…, What the lifecycle should do with an observation., VerificationDecision, _actor(), apply_decision() (+36 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "hub.py"
Cohesion: 0.07
Nodes (37): Central configuration. All runtime configuration flows through this module so…, _apply_scope_guc(), _desired_guc(), _guard(), _has_org_predicate(), install_tenancy_guards(), _mappers_of(), org_scoped_table_names() (+29 more)

### Community 76 - "server_service.py"
Cohesion: 0.06
Nodes (74): agent_heartbeat(), Response, Ingest one metrics sample and hand the agent its next work. A protocol-1 agent…, Canonical Redis pub/sub channel names shared by API, workers and WS hub., server_metrics_channel(), ServerStatus, Alias for :attr:`extra`, so the API can expose open-ended agent facts. The…, Server (+66 more)

### Community 77 - "list_domains"
Cohesion: 0.13
Nodes (30): create_domain(), delete_domain(), _enqueue_verification(), get_domain(), list_domain_routes(), list_domains(), _project_names(), alias (+22 more)

### Community 78 - "incidents.py"
Cohesion: 0.13
Nodes (34): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+26 more)

### Community 79 - "test_phase2_secrets.py"
Cohesion: 0.19
Nodes (21): _env(), _project(), Phase 2 secrets: layered scope, immutable versions, rollback, isolation. Two…, Two racing rotations must both be kept and never share a version number., Another tenant cannot read, rotate, roll back or even enumerate the secret., The documented example: same key at three scopes; most specific wins., A ref declared in the project base config resolves for its environments., _resolved() (+13 more)

### Community 80 - "RolesPage.tsx"
Cohesion: 0.11
Nodes (15): Role, RolesPage, describeError(), GROUP_STYLE, LEGEND_STYLE, OPTION_STYLE, PermissionSpec, roleAllows() (+7 more)

### Community 81 - "monitor_service.py"
Cohesion: 0.16
Nodes (36): MonitorStatus, Monitor, One probe. Targets are polymorphic since Phase 4 (domain-model.md §2.6).…, get_transport(), Pick the transport matching the monitor URL scheme., _active_incident(), _audit(), claim_due_monitors() (+28 more)

### Community 82 - "canonicalize_name"
Cohesion: 0.12
Nodes (33): canonicalize_name(), canonicalize_path(), _check_labels(), _check_not_ip(), hostname_is_covered(), _idna(), InvalidName, is_valid_path() (+25 more)

### Community 83 - "tests/conftest.py"
Cohesion: 0.22
Nodes (7): configure_test_env(), Test bootstrap: pin every cached setting BEFORE the first ``app`` import. The…, KEY=VALUE pairs from the repo .env (first definition wins); never logged., Export the exact settings the app caches; host values cannot leak through., _read_dot_env(), os, pathlib

### Community 84 - "resolve_secrets_for_environment"
Cohesion: 0.19
Nodes (13): Exception, A ``${secret:KEY}`` reference could not be resolved. Fail-closed. Carries…, One successfully resolved reference: metadata for audit, no value., Outcome of resolving an environment's config references., Resolve every ``${secret:KEY}`` reference an environment's config names.…, resolve_secrets_for_environment(), ResolvedSecrets, SecretReference (+5 more)

### Community 85 - "AuthContext"
Cohesion: 0.07
Nodes (53): AuthContext, Resolved identity plus the organization this request acts in.…, permission_exists(), MembershipStatus, _apply_deactivation(), _assert_not_last_active_member(), _assert_not_last_active_superadmin(), create_user() (+45 more)

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "Conflict"
Cohesion: 0.06
Nodes (70): Conflict, OperationStatus, OperationType, Lifecycle of one node operation (node-agent-architecture.md §5.1).…, The whitelist. Nothing outside this enum ships as an exec surface. Each type…, Operation, Whether the agent reported this operation as successful. A terminal check, not…, One whitelisted action for one node, with a CAS lifecycle. ``attempts`` is… (+62 more)

### Community 88 - "log_service.py"
Cohesion: 0.11
Nodes (27): container_log_channel(), LogSource, LogLine, datetime, Yield parsed log lines. With ``follow=True`` the stream never ends., One parsed log record from a container log stream., append_lines(), count_container_logs() (+19 more)

### Community 89 - "Settings"
Cohesion: 0.14
Nodes (6): field_validator, model_validator, Username from :attr:`database_url`, or ``None`` if it is unparseable., Validated application settings (loaded from environment / .env)., Settings, BaseSettings

### Community 90 - "DomainStatus"
Cohesion: 0.07
Nodes (46): DomainStatus, Ownership-verification lifecycle of a Domain (domain-routing.md §4). ``STALE``…, The honest state of a route that left the desired tree but is not gone. One…, removal_requested_detail(), _affected_node_ids(), _announce(), _apply_for_node(), _audit_action() (+38 more)

### Community 91 - "validate_config"
Cohesion: 0.07
Nodes (34): EnvironmentType, Kind of a project-scoped deployment environment (Phase 2). Descriptive only —…, EnvironmentBase, _normalise_environment_type(), field_validator, Shared environment fields., ProjectBase, field_validator (+26 more)

### Community 92 - "alert_service.py"
Cohesion: 0.23
Nodes (14): Alert, create_alert(), get_alert(), mark_all_read(), mark_read(), AsyncSession, UUID, Alert inbox: insert-only creation plus read/unread bookkeeping. (+6 more)

### Community 93 - "apply_scope_to_session"
Cohesion: 0.06
Nodes (73): dispose_engine(), get_sessionmaker(), async_sessionmaker, apply_scope_to_session(), current_org(), current_scope(), org_scope(), UUID (+65 more)

### Community 94 - "test_phase21_secret_version_integrity.py"
Cohesion: 0.18
Nodes (18): _app_role_dsn(), _owner_dsn(), _probe(), Phase 2.1 — ``secret_versions`` is append-only in the **database**, not just in…, Immutability is a database guarantee, not merely a missing code path. The owner…, The legitimate append paths keep working under the guard., The documented deletion policy: purging a Secret cascades its history., RLS is preserved: another tenant cannot see a version row, even by id. (+10 more)

### Community 95 - "StepLine"
Cohesion: 0.10
Nodes (23): _commit_short(), DeploymentRunner, _pace(), Exception, Protocol, Deployment runner port plus a faithful simulated implementation.…, Stream output lines for *step_name*; raise StepFailure to fail it., Deterministic per-line delay between 0.05s and 0.35s. (+15 more)

### Community 96 - "NexusOps (self-hosted infrastructure management and monitoring platform)"
Cohesion: 0.20
Nodes (10): mailpit service (dev SMTP sink + web UI :8025), NexusOps compose stack (8 services on one network), HIGH finding: redirect-following SSRF in uptime monitors (fixed: follow_redirects=False + per-hop guard), SSRF guard (assert_safe_url, per-redirect-hop validation, assert_safe_tcp_endpoint), Mailpit SMTP port internal-only (host-side injection needs extra mapping), Host port knobs (NEXUSOPS_HTTP_PORT/POSTGRES/REDIS/MAILPIT/VITE), SPA entry point (loads /src/main.tsx, dark color-scheme), Uptime monitors -> incidents -> notifications flow (+2 more)

### Community 97 - "REST API surface (/api/v1)"
Cohesion: 0.29
Nodes (7): Cursor (keyset) and offset pagination envelopes, Permission model (data-driven registry, require_permission, wildcard scopes), REST API surface (/api/v1), RBAC registry (PERMISSIONS + ROLE_MATRIX + scope_matches), Adding a new resource: 7-step checklist (model -> migration -> schemas -> service -> router -> tests -> frontend), Alembic migration workflow (autogenerate, models __init__ export, entrypoint apply), Command palette (Ctrl/Cmd+K)

### Community 98 - "journey.spec.ts"
Cohesion: 0.15
Nodes (15): EDGE, MAILPIT, ADMIN, Bootstrap, bootstrapVia(), test, ADMIN, formLogin() (+7 more)

### Community 99 - "enqueue.py"
Cohesion: 0.12
Nodes (20): after_commit(), _on_commit(), _on_rollback(), Any, AsyncSession, Deferred Celery handoff: enqueue only after the creating transaction commits. A…, Run ``factory`` once the current transaction commits. ``label`` names the work…, _run() (+12 more)

### Community 100 - "redact_mapping"
Cohesion: 0.22
Nodes (13): _is_sensitive_key(), Substring match on a normalised key so header-style names are caught too.…, Return a copy of *data* with sensitive values replaced. Used by audit metadata…, redact_mapping(), parametrize, Unit tests for app.core.logging redaction (pure functions only)., test_case_insensitive_substring_match(), test_flat_sensitive_keys_redacted() (+5 more)

### Community 102 - "env.py"
Cohesion: 0.24
Nodes (10): _database_url(), Alembic environment: metadata comes from app.models, URL from app settings., Migrations run as the table **owner**, never as the application role. The owner…, Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online(), Owner-role DSN for Alembic and the container entrypoint. Migrations… (+2 more)

### Community 103 - "hash_token"
Cohesion: 0.23
Nodes (13): generate_agent_token(), generate_api_key(), generate_refresh_token(), hash_token(), A per-node credential (``nxa_``): long-lived, node-scoped, never shared., Return ``(raw_token, sha256_hex_hash)``., Return ``(raw_key, prefix, hash)``. Keys look like ``nxo_live_<random>``., test_agent_token_prefix_convention() (+5 more)

### Community 104 - "_rows"
Cohesion: 0.22
Nodes (16): _rows(), _integrity_error(), _migrate_from_phase3(), Statement, Phase 4 migration (`f4a5b6c7d8e9`) against a real Phase 3 database. Phase 4 is…, The polymorphic shape is enforced in both directions., The anti-takeover rule is a partial unique index, not a convention., A populated pre-Phase-4 instance: a node, a URL monitor, a live operation. (+8 more)

### Community 105 - "redis service (Redis 7, no persistence, loopback :6390)"
Cohesion: 0.22
Nodes (11): redis service (Redis 7, no persistence, loopback :6390), WebSocket API (/api/v1/ws handshake, frames, limits), WebSocket channels (global, server-metrics, container-logs, deployment-logs, incidents), Deployment engine (queue_deployment / execute_deployment / sweeper backstop), Real-time spine: PostgreSQL system_events + Redis pub/sub, Rollback as a new deployment (rollback_of_id), WebSocket hub (framework-thin, Redis fan-in, per-socket queues), Test suites (pytest unit+integration, vitest, Playwright e2e) (+3 more)

### Community 106 - "NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)"
Cohesion: 0.18
Nodes (12): Agent security model (one-way telemetry, no command channel), Agent enrollment token (X-Agent-Token, nxa_..., SHA-256 at rest), Agent heartbeat exponential backoff (cap 5 min, exit 1 on revoked token), agent/install.sh (enrollment installer), Agent metrics collection (/proc statvfs Docker socket), NexusOps agent (stdlib-only Python, agent/nexusops_agent.py), Agent systemd hardening (ProtectSystem=strict, NoNewPrivileges), Agent ingest API (POST /agent/hello, POST /agent/heartbeat) (+4 more)

### Community 107 - "LoginPage.tsx"
Cohesion: 0.33
Nodes (4): LoginPage, FieldErrors, MetaInfo, redirectTarget()

### Community 108 - "docker_real.py"
Cohesion: 0.08
Nodes (30): ContainerStats, Exception, Build a compact, secret-free description of a provider failure. Only the…, Point-in-time resource usage snapshot., sanitize_error(), _as_float(), _compute_stats(), _cpu_percent() (+22 more)

### Community 109 - "Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)"
Cohesion: 0.25
Nodes (9): API keys (X-API-Key, nxo_..., scope intersection), First boot sequence (api entrypoint migrates, compose never seeds), Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test), Makefile workflows (up/test/lint/typecheck/migrate/seed), HIGH finding: API-key scope bypass for superadmin-owned keys (fixed: scope intersection first), Security audit 2026-09 (26 raw findings -> 20 confirmed, all fixed), HIGH finding: known seed superadmin + API key backdoor (fixed: NEXUSOPS_ALLOW_SEED opt-in, one-time password), Threat model (edge attacker, malicious agent, curious operator, leaked token, SSRF) (+1 more)

### Community 111 - "organization_service.py"
Cohesion: 0.12
Nodes (31): A named permission set. ``org_id`` is NULL for every row in v1 — the five…, Role, Membership, Binds a user to an organization with a role *inside that organization*.…, add_member(), create_organization(), get_organization(), membership_for_user() (+23 more)

### Community 112 - "test_app_gating.py"
Cohesion: 0.44
Nodes (8): _app_for_environment(), MonkeyPatch, ENVIRONMENT gating contract: docs exposure and HSTS (see .env.example).…, create_app() with get_settings() patched to the given environment., test_non_production_does_not_emit_hsts(), test_non_production_keeps_docs_and_schema(), test_production_emits_hsts(), test_production_hides_docs_and_schema()

### Community 113 - "dnsmock.py"
Cohesion: 0.11
Nodes (25): resolver(), answer(), encode_name(), encode_txt(), forward(), main(), parse_question(), TXT rdata: one or more length-prefixed strings, each ≤ 255 bytes. (+17 more)

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "v1/agent.py"
Cohesion: 0.05
Nodes (42): Agent ingest endpoints: enrollment, hello, heartbeat, and operation traffic.…, AgentEnrollOut, AgentHeartbeatOut, AgentHelloOut, Tells the agent how often to report and what protocol it negotiated., v2 heartbeat response: cadence, work to pull, and any pending rotation. A v1…, The minimum a freshly enrolled agent needs, and nothing more., AgentOperationClaimOut (+34 more)

### Community 116 - "test_tenancy_allowlist.py"
Cohesion: 0.20
Nodes (14): AST, _actual_callers(), _calls_system_scope(), _module_path(), Path, The system-scope allowlist is the only fence around the tenancy carve-out.…, Every module that could open a system scope: ``app/`` plus the scripts., No module may lift tenant isolation without being named in the list. (+6 more)

### Community 117 - "test_migration_phase2.py"
Cohesion: 0.26
Nodes (12): _migration_dsn(), _owner_dsn(), Phase 2 migration (`b2c3d4e5f6a7`) against realistic legacy data. The promotion…, Upgrade ``database`` to ``revision`` through the app's own settings path.…, The pre-Phase-2 shapes: application-scoped environments, per-app dupes., A fresh database reaches the same shape the models describe., _run_migration(), _seed_legacy_data() (+4 more)

### Community 118 - "dependencies"
Cohesion: 0.33
Nodes (6): dependencies, lucide-react, react, react-dom, react-router-dom, @tanstack/react-query

### Community 119 - "@tanstack/react-query"
Cohesion: 0.08
Nodes (21): DeploymentStepOut, DeploymentDetailPage, MetaInfo, SimulatedChip(), mocks, ACTIVE_STATUSES, DeploymentDetailRow, DeploymentLogRow (+13 more)

### Community 120 - "generate_secrets.sh"
Cohesion: 0.47
Nodes (3): existing_real_keys(), replace_or_append(), generate_secrets.sh script

### Community 121 - "ControlHandler"
Cohesion: 0.22
Nodes (7): BaseHTTPRequestHandler, clear_record(), ControlHandler, in_zone(), The journey's only way to publish a record — no shell, no shared volume., set_record(), snapshot()

### Community 122 - "server_payload"
Cohesion: 0.10
Nodes (27): A valid POST /servers body with per-test overrides., server_payload(), test_token_cannot_claim_a_foreign_tenants_node(), test_v1_heartbeat_keeps_the_204_contract(), _create_server(), Server CRUD, cascade delete, audit trail rows and audit immutability., The HTTP listing path — schema serialization is exercised end-to-end. A…, ``/servers`` is a temporary alias for pre-rename clients. It must keep working… (+19 more)

### Community 123 - "_exec"
Cohesion: 0.21
Nodes (12): alembic_script, _exec(), Statement, Run statements in one transaction as the owner (committed on success)., Phase 3 migration (``a1b2c3d4e5f6``) against realistic legacy data. Phase 3 is…, A fresh database reaches the same shape the models describe., The pre-Phase-3 shapes: a node with telemetry, and operation history., _seed_legacy() (+4 more)

### Community 124 - "middleware.py"
Cohesion: 0.13
Nodes (17): ASGIApp, AccessLogMiddleware, HTTP middleware: request ids, security headers, structured access logs., Baseline hardening headers on every API response., RequestIDMiddleware, SecurityHeadersMiddleware, create_app(), _include_routers() (+9 more)

### Community 125 - "OperationError"
Cohesion: 0.18
Nodes (15): _demux_docker_stream(), _docker_error(), execute_operation(), OperationError, Exception, A stable, sanitized failure contract for the control plane., Re-validate the operation's parameters locally, against a closed shape., Decode docker's 8-byte-header frame stream, or ``None`` if not framed. (+7 more)

### Community 126 - "list_operations"
Cohesion: 0.18
Nodes (19): cancel_operation(), create_operation(), get_operation(), list_operations(), DbDep, Depends, get, post (+11 more)

### Community 127 - "_dns_stub"
Cohesion: 0.40
Nodes (5): _dns_stub(), _fake_observe(), fixture, MonkeyPatch, Stand in for authoritative DNS in every test in this module.

### Community 137 - "AuditLogPage.test.tsx"
Cohesion: 0.20
Nodes (5): AuditEntry, AuditLogPage(), formatTimestamp(), shortId(), mockedGet

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
Cohesion: 0.09
Nodes (24): AGENT, DNS_CONTROL, dnsPublish(), docker(), DomainBody, EventBody, finishedRemovalApplies(), HttpResult (+16 more)

### Community 150 - "nexusops-understand.mjs"
Cohesion: 0.33
Nodes (5): COMMON, meta, out, READERS, SCHEMA

### Community 151 - "Invisible account lockout (5 fails -> 15 min, enumeration resistance)"
Cohesion: 0.33
Nodes (6): Invisible account lockout (5 fails -> 15 min, enumeration resistance), Unified error envelope (code, message, request_id), Per-IP rate limiting (Redis fixed window), Request lifecycle (edge -> middleware -> rate limit -> deps -> router), Client IP resolution (resolve_client_ip, TRUSTED_PROXY_CIDRS, XFF overwrite), EmailStr rejects reserved domains (login 422 on .test/.local/.arpa)

### Community 152 - "nginx_capability"
Cohesion: 0.12
Nodes (19): _listener_ownership(), _listening_ports(), _nginx_binary(), nginx_capability(), _nginx_owned_ports(), _nginx_running(), _nginx_status(), _nginx_version() (+11 more)

### Community 153 - "DockerHostsPage.test.tsx"
Cohesion: 0.18
Nodes (8): DockerHostOut, ApiError, failingHost, host, hostsPage, mockCountApi(), server, serversPage

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
Cohesion: 0.09
Nodes (39): AgentContainerIn, AgentHeartbeatIn, AgentHelloIn, Any, field_validator, Observed container state reported by an agent., Periodic metrics + observed containers from an enrolled agent. Network counters…, First contact from an agent after enrollment; fills static host facts. (+31 more)

### Community 159 - "test_run_async_publishes_frames_scheduled_by_the_commit_hook"
Cohesion: 0.29
Nodes (5): _FakeDb, Stands in for an ``AsyncSession`` whose only job here is ``sync_session``. A…, The shape of a worker task whose last statement is a commit., test_run_async_publishes_frames_scheduled_by_the_commit_hook(), commit_then_return()

### Community 160 - "main"
Cohesion: 0.11
Nodes (19): build_capabilities(), _build_hello_payload(), _enroll(), _interruptible_sleep(), main(), memory_total_mb(), os_info(), persist_token() (+11 more)

### Community 161 - "monitor_transport.py"
Cohesion: 0.09
Nodes (24): assert_safe_url_async(), Async wrapper around :func:`assert_safe_url`; DNS runs off the loop., CheckOutcome, coerce_headers(), _decode(), MonitorTransport, Any, BaseException (+16 more)

### Community 162 - "list_sessions"
Cohesion: 0.24
Nodes (10): list_sessions(), CurrentUser, DbSessionDep, delete, get, Request, UUID, Active sessions of this organization's members. Defaults to the caller's own;… (+2 more)

### Community 163 - "seed.py"
Cohesion: 0.15
Nodes (24): Project, OrganizationStatus, UserStatus, User, Organization, A tenant. Every organization-owned row points here via ``org_id``., _lock(), _organization_name() (+16 more)

### Community 164 - "AgentClient"
Cohesion: 0.15
Nodes (8): AgentClient, _docker_raw(), A verifying TLS context. Verification is never disabled. A private/self-hosted…, Refuse to send credentials over plain HTTP to a non-loopback server. The…, One raw Docker API call; returns ``(status, body_bytes)``., _tls_context(), _UnixHTTPConnection, SSLContext

### Community 165 - "client_ip"
Cohesion: 0.31
Nodes (9): client_ip(), _enforce(), node_rate_limit(), _dependency(), Request, _dependency(), Return a dependency keyed on the **authenticated node**, not the IP. A fleet…, Best-effort client IP; honours X-Forwarded-For from trusted proxies. Delegates… (+1 more)

### Community 166 - "nginx.py"
Cohesion: 0.15
Nodes (20): _header_lines(), _quote(), _rate_zone(), NginxProvider — a pure, deterministic renderer plus the two op wrappers.…, Validate the route's headers and split them by destination., Wrap an already-validated value in quotes for a template slot. Values reaching…, The ``limit_req_zone`` declaration for a rate-limited route., A fixed host redirect, or ``None`` for a normal proxying route. (+12 more)

### Community 167 - "resolve_auth"
Cohesion: 0.07
Nodes (36): _attach_organization(), get_current_user(), get_identity(), get_optional_user(), _load_organization(), _load_permissions(), membership_for_org(), _org_id_from_header() (+28 more)

### Community 168 - "report_operation_result"
Cohesion: 0.22
Nodes (15): agent_enroll(), agent_hello(), claim_operation(), _presented_token(), DbDep, post, Request, UUID (+7 more)

### Community 169 - "RateLimit"
Cohesion: 0.29
Nodes (4): model_validator, RateLimit, One route's request-rate ceiling (rendered as a ``limit_req_zone``)., test_rate_limit_constraints()

### Community 170 - "test_agent_contract.py"
Cohesion: 0.20
Nodes (15): agent_fixture(), _load_agent(), _patch_stats(), Any, fixture, MonkeyPatch, Contract tests: the shipped agent's payloads must satisfy the ingest schemas.…, One-shot docker stats reduce to cpu/mem/limit fields the schema accepts, with… (+7 more)

### Community 171 - "20261009_1000-c3d4e5f6a7b8_enforce_secret_version_integrity.py"
Cohesion: 0.48
Nodes (6): _clear_app_role_guc(), downgrade(), Phase 2.1 — enforce append-only ``secret_versions`` in the database. Phase 2…, Publish the app-role name to the migration GUC the revoke block reads., _set_app_role_in_guc(), upgrade()

### Community 172 - "_FakeAsyncClient"
Cohesion: 0.22
Nodes (3): _FakeAsyncClient, _FakeRequestObj, Scripted httpx.AsyncClient: responses keyed by absolute request URL.

### Community 173 - "permissions.py"
Cohesion: 0.10
Nodes (18): PermissionSpec, Permission registry and role matrix. Permissions are *data*: the registry below…, Check an API-key scope list against a required permission. Supports exact match…, scope_matches(), parametrize, test_scope_matches_truth_table(), 1. Principles (already true in the codebase, kept), 5. API keys (+10 more)

### Community 174 - "paginate"
Cohesion: 0.07
Nodes (37): create_api_key(), list_api_keys(), CurrentUser, DbSessionDep, delete, get, post, Request (+29 more)

### Community 175 - "sweep_deployments"
Cohesion: 0.22
Nodes (9): _enqueue_task(), Hand the deployment to Celery; broker downtime is tolerated (beat sweeps)., task, Execute one queued deployment. The engine owns all state transitions., Re-enqueue deployments the broker lost; fail ones whose worker died.…, run_deployment(), _run(), sweep_deployments() (+1 more)

### Community 176 - "Platform Security Model — NexusOps"
Cohesion: 0.10
Nodes (20): make(), 10.1 Node revocation playbook (compromised node / leaked agent token), 10.2 Key compromise playbook, 10. Incident response, 1.1 Real vs simulated today (do not mistake one for the other), 1. Scope, stance, and simulation honesty, 2. Assets, 3. Trust boundaries (+12 more)

### Community 177 - "ContainerListPage.test.tsx"
Cohesion: 0.29
Nodes (3): ApiError, server, serversPage

### Community 178 - "network_rates"
Cohesion: 0.33
Nodes (6): build_facts(), network_rates(), network_total_bytes(), Sum rx/tx bytes over non-loopback interfaces from /proc/net/dev., Return (rx_kb_s, tx_kb_s) or ``(None, None)`` when not measurable., Open-ended host facts, stored in the node's flexible JSONB blob. Deliberately…

### Community 179 - ".dispatch"
Cohesion: 0.60
Nodes (3): Request, Response, RequestResponseEndpoint

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
Cohesion: 0.29
Nodes (7): 8.1 Binding rules, 8.2 Certificate selection rule (this doc owns it) — **Phase 5 target design**, 8.3 Re-render triggers, 8.4 Drift and reconciliation, 8.5 How deployments hook routing (post-deploy route sync), 8. Upstream binding and re-render triggers, Requested is not confirmed

### Community 184 - "Multi-Tenancy Architecture"
Cohesion: 0.14
Nodes (12): Whether the runtime connection is the RLS-enforced application role. False…, 10. Migration (Phase 1), 1. Tenancy invariants, 2.1 Org creation — v1 decision, 2. Org resolution on every request, 3. The session guard (the mechanical layer), 4. Background jobs, 6. Agents (+4 more)

### Community 185 - "update_channel"
Cohesion: 0.36
Nodes (11): _audit(), create_channel(), delete_channel(), encrypt_config(), _normalize_events(), AsyncSession, Request, Fire a TEST delivery straight through the sender; audit and report result. (+3 more)

### Community 186 - "run_async"
Cohesion: 0.05
Nodes (70): Celery application: periodic cadences live here, dynamic work is claimed…, _candidates(), _run(), task, Heartbeat sweeps: offline detection and recovery for servers., Flag silent servers OFFLINE, recover returning ones. Safe to overlap., sweep_servers(), _run() (+62 more)

### Community 187 - "role_service.py"
Cohesion: 0.07
Nodes (47): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, delete, get (+39 more)

### Community 188 - "instant_pacing"
Cohesion: 0.40
Nodes (4): instant_pacing(), fixture, MonkeyPatch, Remove the per-line sleeps; pacing bounds are asserted separately.

### Community 189 - "phase3.spec.ts"
Cohesion: 0.15
Nodes (10): frontend_e2e_fixtures_expect, AGENT, NodeDetail, OperationRow, REPO_ROOT, ref_node_child_process, ref_node_fs, ref_node_os (+2 more)

### Community 190 - "20261004_1200-e7c4a2b9d1f3_add_operations_framework.py"
Cohesion: 0.50
Nodes (3): _quoted_list(), Add the operations framework table (node-agent-architecture.md §5). One tenant-…, upgrade()

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

### Community 195 - "channel.py"
Cohesion: 0.17
Nodes (15): ChannelType, DeliveryStatus, ChannelBase, ChannelCreate, ChannelUpdate, DeliveryOut, EmailConfig, BaseModel (+7 more)

### Community 196 - "get_meta"
Cohesion: 0.40
Nodes (5): get_meta(), DbSessionDep, get, Public metadata; identity fields appear only for valid credentials., OptionalUser

### Community 197 - "_raw_probe"
Cohesion: 0.20
Nodes (10): _app_role_dsn(), A libpq DSN for the RLS-enforced application role (no ORM, no guard)., Run one statement as ``nexusops_app`` with an explicit GUC. Parameterized like…, Raw SQL as the application role: the policies alone return nothing. Written…, Adding ``org_id`` to ``audit_logs`` must not have opened a way to edit it. The…, ``WITH CHECK`` is not decoration: an unlucky INSERT cannot cross tenants., _raw_probe(), test_audit_trail_is_still_append_only_after_tenancy() (+2 more)

### Community 198 - "Product Roadmap — NexusOps Multi-Tenant Platform"
Cohesion: 0.12
Nodes (17): 0. Stance, 10. Phase 7 — Teams, grants & custom roles — **proposal, not implemented**, 11. Phase 8 — Backups — **proposal, not implemented**, 12. Phase 9 — Billing & metering — **proposal, not implemented**, 13.1 Scope-creep gates — what must be true before each expansion, 13. First commercially meaningful version, 14. Biggest risks (short form), 15. Reading order (+9 more)

### Community 199 - "Platform Vision — NexusOps"
Cohesion: 0.20
Nodes (10): 1. Where NexusOps is today, 2.1 What we are NOT building, 2.2 The wedge (differentiation), 2. The direction, 3. Guiding principles, 4. Customer journey (target), 5.1 Architecture overview (target), 5. Control plane / data plane boundary (+2 more)

### Community 200 - "install_hint"
Cohesion: 0.40
Nodes (5): install_hint(), The one-liner an operator pastes, without the raw token in argv. The token…, 8.1 Today (real), 8.2 One-liner and token delivery (implemented bar the curl step), 8. Install UX

### Community 201 - "NotificationChannel"
Cohesion: 0.13
Nodes (20): NotificationChannel, A delivery target (email address / webhook endpoint). ``config_ciphertext``…, _create_monitor(), Monitor checks driving the full down -> incident -> recovery lifecycle., Regression: probe headers and URL query credentials never leave the API. Probe…, A monitor's checks, incidents and timeline all live in its organization, so the…, test_check_now_endpoint_runs_immediately(), test_down_then_recover_lifecycle() (+12 more)

### Community 202 - "pytest"
Cohesion: 0.40
Nodes (4): created_at server defaults must evaluate per insert, not at table creation., Regression: system_events and audit_logs shipped with DEFAULT 'now()' (quoted…, test_audit_and_event_created_at_defaults_are_dynamic(), pytest

### Community 203 - "ProxyProvider"
Cohesion: 0.33
Nodes (5): ProxyProvider, Any, Protocol, What ``app.services.proxy_service`` is allowed to assume about a provider. The…, 11. Post-deploy hooks

### Community 204 - "ApplicationBase"
Cohesion: 0.40
Nodes (4): ApplicationBase, Any, field_validator, Shared application fields; ``build_config`` is a free-form dict.

### Community 206 - "20261008_1200-b2c3d4e5f6a7_add_projects_and_environments.py"
Cohesion: 0.53
Nodes (5): downgrade(), _drop_constraint(), _quoted_list(), Phase 2 — projects & environments: env promotion, config, secret versions. This…, upgrade()

### Community 207 - "MonitorCreate"
Cohesion: 0.50
Nodes (4): MonitorBase, MonitorCreate, Shared validation bounds for monitor configuration., Payload for POST /monitors.

### Community 208 - "_live_bundle_id"
Cohesion: 0.20
Nodes (10): _allowed_bundle_path(), _live_bundle_id(), _live_files(), The bundle fingerprint — byte-identical to the control plane's algorithm.…, Read the live managed tree, or ``None`` when it does not exist yet., Fingerprint of the configuration tree currently on disk., Independently validate a bundle. Anything unexpected is refused., _template_version_of() (+2 more)

### Community 209 - "test_remove_honours_force_and_never_shells"
Cohesion: 0.50
Nodes (3): test_container_start_maps_to_a_fixed_api_call(), fake_raw(), test_remove_honours_force_and_never_shells()

### Community 213 - ".route_file_path"
Cohesion: 0.50
Nodes (3): Where a route's fragment lands, so the service can name it in events., A deterministic, filesystem-safe fragment name for one route., _route_key()

### Community 214 - "test_migration_phase22.py"
Cohesion: 0.28
Nodes (8): UUID, Phase 2.2 — the environment-type correction follows the documented precedence.…, Only the previous migration's ``PROD`` output is corrected. A row already…, Create one legacy (application-scoped) environment per case., Every branch of the slug-first rule, end to end through ``head``., _seed_legacy(), test_correction_preserves_operator_set_values(), test_recognised_slug_alias_wins_over_a_conflicting_name()

## Knowledge Gaps
- **460 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+455 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2274 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **24 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `6. Tooling: reproducible e2e` connect `run_async` to `enqueue.py`, `client.ts`, `Conflict`, `apply_scope_to_session`, `auth_service.py`?**
  _High betweenness centrality (0.264) - this node is a cross-community bridge._
- **Why does `useEventStream()` connect `client.ts` to `apiGet`, `App.tsx`, `AuthContext.tsx`, `ServerDetailPage.tsx`, `@tanstack/react-query`, `run_async`?**
  _High betweenness centrality (0.263) - this node is a cross-community bridge._
- **Why does `TenancyScopeError` connect `apply_scope_to_session` to `deps.py`, `publish`, `resolve_auth`, `test_operations.py`, `hub.py`, `enrollment_service.py`, `AuthContext`, `log_service.py`, `run_async`, `test_tenant_isolation.py`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Are the 93 inferred relationships involving `AuthContext` (e.g. with `TenancyScopeError` and `MembershipStatus`) actually correct?**
  _`AuthContext` has 93 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `APIModel` (e.g. with `OperationSpec` and `test_specs_reject_unknown_params()`) actually correct?**
  _`APIModel` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `apiGet()` (e.g. with `ContainerDetailPage.test.tsx` and `mockApi()`) actually correct?**
  _`apiGet()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `Server` (e.g. with `ServerStatus` and `2.3 Infrastructure — Nodes`) actually correct?**
  _`Server` has 5 INFERRED edges - model-reasoned connections that need verification._