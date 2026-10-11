# Graph Report - nexusops  (2026-10-11)

## Corpus Check
- 354 files · ~372,677 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: (none) 10, .example 1, .service 1)

## Summary
- 5805 nodes · 17098 edges · 230 communities (205 shown, 25 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1346 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a49b3d83`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- apiGet
- record
- ApiKeysPage.tsx
- _verified_domain
- DockerProviderError
- types.ts
- resolve_client_ip
- OperationType
- App.tsx
- test_agent_v2.py
- assert_error_code
- ServerDetailPage.tsx
- uuid
- client.ts
- projects.py
- models/__init__.py
- deployment_engine.py
- SimulatedDockerProvider
- enrollment_service.py
- rollback_secret
- test_deployments_simulated.py
- containers.py
- metrics_service.py
- test_security.py
- Domain Routing — NexusOps
- monitor_service.py
- Node & Agent Architecture
- test_agent_backoff.py
- SimulatedDeploymentRunner
- nexusops_agent.py
- test_tenant_isolation.py
- auth_service.py
- docker_host_service.py
- test_rate_limit.py
- docker_hosts.py
- test_ws_hub.py
- NginxBundle
- v1/search.py
- enums.py
- v1/channels.py
- DockerProvider
- test_monitor_transport.py
- Deployment Architecture — NexusOps (target state)
- AuthContext.tsx
- v1/health.py
- test_permissions.py
- routes.py
- test_phase3_nodes.py
- test_ssrf.py
- secret_service.py
- update_role
- servers.py
- proxy_service.py
- test_migration_phase21.py
- v1/auth.py
- test_agent_nginx_contract.py
- create_user
- alembic
- _attempt_delivery
- helpers.py
- compilerOptions
- _list_deployments
- test_error_logging.py
- dns_verifier.py
- test_phase2_environments.py
- route_service.py
- test_schema_redaction.py
- typing
- encrypt_str
- package.json
- test_event_registry.py
- test_secrets.py
- test_nginx_renderer.py
- domain_service.py
- api service (FastAPI / uvicorn :8000)
- TenancyScopeError
- AsyncSession
- domains.py
- incidents.py
- test_phase2_secrets.py
- RolesPage.tsx
- test_schemas_server.py
- canonicalize_name
- tests/conftest.py
- DbDep
- NotFound
- devDependencies
- operation_service.py
- LogLine
- Settings
- domain_routing.py
- validate_config
- alert_service.py
- apply_scope_to_session
- test_phase21_secret_version_integrity.py
- StepLine
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- journey.spec.ts
- after_commit
- redact_mapping
- README.md - NexusOps overview
- env.py
- sweep_routes
- test_migration_phase4.py
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- LoginPage.tsx
- docker_real.py
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- ScopedSession
- create_organization
- test_app_gating.py
- dnsmock.py
- scripts
- APIModel
- test_tenancy_allowlist.py
- _alembic_config
- dependencies
- @tanstack/react-query
- generate_secrets.sh
- ControlHandler
- server_payload
- test_migration_phase2.py
- middleware.py
- OperationError
- list_operations
- test_phase4_routing.py
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
- Secrets Architecture
- test_schemas_agent.py
- organizations.py
- main
- ssrf.py
- decide
- seed.py
- AgentClient
- _enforce
- nginx.py
- AuthContext
- Server
- test_a_late_result_for_an_expired_operation_cannot_fail_a_live_route
- test_agent_contract.py
- get_settings
- _handle_apply_result
- 2. Entities
- create_api_key
- scope_matches
- Platform Security Model — NexusOps
- ContainerListPage.test.tsx
- network_rates
- .dispatch
- websocket_endpoint
- _nginx_apply
- _nginx_bootstrap
- 8. Upstream binding and re-render triggers
- api_key_service.py
- update_channel
- run_async
- Conflict
- instant_pacing
- phase3.spec.ts
- _mutate_in_system_scope
- docs/engineering-report.md - build and verification report
- 20261010_1200-f4a5b6c7d8e9_phase4_domains_and_routes.py
- test_migration_drift.py
- EnvironmentUpdate
- channel.py
- RouteHeader
- test_schemas_search.py
- Product Roadmap — NexusOps Multi-Tenant Platform
- Platform Vision — NexusOps
- ServerOut
- NotificationChannel
- test_tasks_util.py
- ProxyProvider
- ApplicationCreate
- .__init__
- update_server
- register_exception_handlers
- _live_bundle_id
- _memory_count_and_ttl
- .__tablename__
- _validate_resolution
- .apply_params
- parametrize
- pytest
- DeploymentRunner
- StepFailure
- MonitorTargetType
- assert_safe_tcp_endpoint
- bundle_summary
- list_servers
- lax
- 4. DNS ownership verification
- ._check_status
- test_an_offline_node_keeps_the_revoked_route_unresolved_until_it_returns
- _pace
- .state
- _publish_live_frame
- removal_requested_detail
- 9. Phase 6 — Real deployments — **proposal, not implemented**

## God Nodes (most connected - your core abstractions)
1. `AuthContext` - 156 edges
2. `APIModel` - 145 edges
3. `Server` - 92 edges
4. `apiGet()` - 91 edges
5. `record()` - 86 edges
6. `NotFound` - 83 edges
7. `get_settings()` - 82 edges
8. `publish()` - 71 edges
9. `apiPost()` - 70 edges
10. `Conflict` - 67 edges

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

## Communities (230 total, 25 thin omitted)

### Community 0 - "apiGet"
Cohesion: 0.06
Nodes (90): apiDelete(), apiGet(), apiPatch(), apiPost(), ApplicationOut, ENVIRONMENT_TYPE_LABELS, EnvironmentType, IncidentEventOut (+82 more)

### Community 1 - "record"
Cohesion: 0.11
Nodes (51): paginate(), AsyncSession, Execute *stmt* with limit/offset and return ``(rows, total)``., Any, AsyncSession, Request, UUID, Append an audit row using the caller's transaction (no commit here). The… (+43 more)

### Community 2 - "ApiKeysPage.tsx"
Cohesion: 0.09
Nodes (19): ApiKeyOut, ApiKeysPage, ApiKeyCreatedOut, handleCopyKey(), copyText(), describeError(), EMPTY_FORM, GROUP_STYLE (+11 more)

### Community 3 - "_verified_domain"
Cohesion: 0.15
Nodes (32): _create_route(), _drain(), _proxy_ready_node(), A node that stays offline accumulates one op, not one per attempt., The auto-attached monitor stays on the check → incident → notification path., The old owner's node is told to drop the name, and says when it has., Claim and answer every pending operation, exactly like the agent would.…, The safety check runs again at enable time, not only at creation. (+24 more)

### Community 4 - "DockerProviderError"
Cohesion: 0.09
Nodes (35): clip(), DockerProviderError, Exception, Provider abstraction for docker hosts (real daemon or simulated). Providers are…, A provider operation failed. ``str()`` is safe to show/log., Build a compact, secret-free description of a provider failure. Only the…, Truncate *text* to *limit* characters, stripping control chars., sanitize_error() (+27 more)

### Community 5 - "types.ts"
Cohesion: 0.02
Nodes (87): AlertOut, CapabilityReport, ChannelOut, CheckOut, DeliveryOut, DeploymentLogLine, DeploymentStatus, DomainDetailOut (+79 more)

### Community 6 - "resolve_client_ip"
Cohesion: 0.19
Nodes (20): _is_trusted(), _parse_networks(), Request, Parse a comma-separated CIDR list; malformed entries are skipped., Real client address for *request* per the trust model above., resolve_client_ip(), make_request(), Request (+12 more)

### Community 7 - "OperationType"
Cohesion: 0.10
Nodes (24): OperationType, The whitelist. Nothing outside this enum ships as an exec surface. Each type…, Any, Validate *params* against the type's model and return the stored form.…, validate_params(), ensure_dispatchable(), Refuse a type whose capability is outside the known vocabulary. This is the…, Raise a named conflict when routing may not be managed on this node. (+16 more)

### Community 8 - "App.tsx"
Cohesion: 0.04
Nodes (103): DeploymentOut, Page, ProjectOut, AlertsPage, App(), AuditLogPage, ContainerListPage, DeploymentListPage (+95 more)

### Community 9 - "test_agent_v2.py"
Cohesion: 0.06
Nodes (51): agent_fixture(), _load_agent(), Any, fixture, parametrize, Path, Agent protocol v2: honest metrics, capability detection, and the executor. The…, Phase 4 shipped three nginx ops — no file primitive, no command primitive. (+43 more)

### Community 10 - "assert_error_code"
Cohesion: 0.07
Nodes (57): assert_error_code(), Assert envelope shape + code; returns the inner error object., Regression: lockout must not leak which emails exist. After login_max_attempts…, test_locked_account_response_is_indistinguishable(), _dispatch(), _dispatch_body(), _enrolled_node(), _mutate_in_system_scope() (+49 more)

### Community 11 - "ServerDetailPage.tsx"
Cohesion: 0.06
Nodes (42): ContainerOut, MetricPoint, ServerDetail, ServerSummary, ChartSeries, LineChart(), LineChartProps, PAD (+34 more)

### Community 12 - "uuid"
Cohesion: 0.06
Nodes (51): Agent-facing schemas. Payloads are data only — never executed. Wire protocol v2…, AlertOut, Schemas for operator-facing alerts., API key schemas. Raw keys appear exactly once, at creation., Application API schemas., AuditOut, Schemas for the read-only audit log API. The audit table is append-only; these…, One audit trail entry (no write routes ever exist for this resource).… (+43 more)

### Community 13 - "client.ts"
Cohesion: 0.05
Nodes (54): API_BASE, ApiError, apiRequest(), buildUrl(), extractError(), getAccessToken(), getActiveOrgId(), onActiveOrgChange() (+46 more)

### Community 14 - "projects.py"
Cohesion: 0.10
Nodes (54): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+46 more)

### Community 15 - "models/__init__.py"
Cohesion: 0.06
Nodes (77): _org_scoped_classes(), Mapped classes marked :class:`~app.models.base.OrgScoped`. Reads the mapper…, Base, big_serial_pk(), json_column(), org_id_column(), OrgScoped, datetime (+69 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.12
Nodes (53): deployment_log_channel(), Application, Deployment, DeploymentStep, DeploymentStatus, StepStatus, _after_commit_enqueue(), _after_rollback_drop() (+45 more)

### Community 17 - "SimulatedDockerProvider"
Cohesion: 0.09
Nodes (30): ContainerStatus, Any, Plausible numbers derived from the row plus time-based sine noise., Implements :class:`DockerProvider` semantics against DB rows., Make a container row visible to this provider instance., Attach already-fetched log rows so ``logs()`` can replay them., _seed_int(), SimulatedDockerProvider (+22 more)

### Community 18 - "enrollment_service.py"
Cohesion: 0.13
Nodes (26): agent_enroll(), Redeem an enrollment token for a unique node credential. Transactional and…, generate_enrollment_token(), hash_token(), An enrollment credential (``nxk_``): single-use, short-lived, org-scoped.…, AgentEnrollIn, The first request a brand-new machine makes. ``enrollment_token`` is an…, _claim_and_consume() (+18 more)

### Community 19 - "rollback_secret"
Cohesion: 0.14
Nodes (26): create_secret(), delete_secret(), get_secret(), list_secret_versions(), list_secrets(), DbSession, delete, get (+18 more)

### Community 20 - "test_deployments_simulated.py"
Cohesion: 0.14
Nodes (30): execute_deployment(), Run one deployment to a terminal state. Never raises; safe to re-run., get_application(), get_environment(), _as_worker(), _delivery_chain(), _owner_ctx(), _queue() (+22 more)

### Community 21 - "containers.py"
Cohesion: 0.06
Nodes (63): _action_route(), _endpoint(), _container_out(), _decode_frame(), _ev(), get_container(), _like_pattern(), list_container_logs() (+55 more)

### Community 22 - "metrics_service.py"
Cohesion: 0.09
Nodes (41): get_dashboard_summary(), get_latest_server_metrics(), get_server_metrics(), CurrentUser, DbDep, Depends, get, UUID (+33 more)

### Community 23 - "test_security.py"
Cohesion: 0.08
Nodes (40): argon2, argon2_exceptions, create_access_token(), generate_agent_token(), generate_api_key(), generate_refresh_token(), hash_password(), password_needs_rehash() (+32 more)

### Community 24 - "Domain Routing — NexusOps"
Cohesion: 0.11
Nodes (18): 10. Wildcards and catch-all, 11. User journey, 12. API surface, permissions, audit, 13. Monitoring tie-in, 1. Scope and current state, 2. Where nginx runs, 3.1 Domain, 3.2 Route (+10 more)

### Community 25 - "monitor_service.py"
Cohesion: 0.07
Nodes (76): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+68 more)

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
Cohesion: 0.09
Nodes (29): build_heartbeat(), collect_container_stats(), collect_containers(), _container_ports(), _container_status(), cpu_percent_since(), disk_stats(), docker_capability() (+21 more)

### Community 30 - "test_tenant_isolation.py"
Cohesion: 0.04
Nodes (61): dispose_engine(), close_redis(), Run the enclosed block with tenant filtering off (maintenance only). ``reason``…, system_scope(), dispatch_event_frame(), Queue an event frame to every subscribed enabled channel; send immediately.…, _admin_dsn(), _clean_slate() (+53 more)

### Community 31 - "auth_service.py"
Cohesion: 0.10
Nodes (50): active_memberships(), The user's memberships in non-suspended organizations, oldest first. Reads only…, Unauthorized, System scope bound to *db*, for rows that have no organization. Used by exactly…, system_write_scope(), ActorType, AuditResult, _audit() (+42 more)

### Community 32 - "docker_host_service.py"
Cohesion: 0.13
Nodes (36): DockerHostStatus, DockerHost, provider_for(), Return the provider matching *host*'s endpoint configuration., _assert_endpoint_allowed(), _assert_name_free(), create_host(), delete_host() (+28 more)

### Community 33 - "test_rate_limit.py"
Cohesion: 0.36
Nodes (9): RateLimited, rate_limit(), Return a dependency enforcing *limit* requests per window per IP. With…, _FakeRequest, Unit tests for the Redis-backed rate limiter's failure modes. Regression…, test_auth_limiter_is_fail_closed(), test_fail_closed_fallback_is_per_ip(), test_fail_closed_limiter_still_limits_when_redis_down() (+1 more)

### Community 34 - "docker_hosts.py"
Cohesion: 0.07
Nodes (55): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+47 more)

### Community 35 - "test_ws_hub.py"
Cohesion: 0.05
Nodes (59): _authenticate_api_key(), _authenticate_jwt(), _bind_organization(), _close_socket(), Connection, _frame_org(), Hub, _load_permissions() (+51 more)

### Community 36 - "NginxBundle"
Cohesion: 0.10
Nodes (18): BundleFile, fingerprint_files(), is_allowed_bundle_path(), NginxBundle, field_validator, model_validator, One rendered file. The path is allowlisted, the content is bounded., Deterministic fingerprint over the complete rendered tree. Path order is… (+10 more)

### Community 37 - "v1/search.py"
Cohesion: 0.18
Nodes (23): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+15 more)

### Community 38 - "enums.py"
Cohesion: 0.04
Nodes (107): Agent ingest endpoints: enrollment, hello, heartbeat, and operation traffic.…, Canonical Redis pub/sub channel names shared by API, workers and WS hub., server_metrics_channel(), Client-IP resolution behind chained reverse proxies. The API never takes TCP…, fail_on_bad_config(), Central configuration. All runtime configuration flows through this module so…, Exit immediately with a readable message if configuration is invalid. Also…, Error taxonomy and the single place where API error envelopes are shaped. Every… (+99 more)

### Community 39 - "v1/channels.py"
Cohesion: 0.15
Nodes (27): create_channel(), delete_channel(), get_channel(), list_channels(), list_deliveries(), DbDep, delete, Depends (+19 more)

### Community 40 - "DockerProvider"
Cohesion: 0.09
Nodes (12): DockerProvider, Any, datetime, Protocol, List containers visible to the provider., Inspect a single container by id (short ids allowed)., List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``., List volumes: keys ``name``, ``driver``, ``mountpoint``. (+4 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.06
Nodes (60): CheckResult, CheckOutcome, coerce_headers(), _decode(), get_transport(), HTTPMonitorTransport, MonitorTransport, Any (+52 more)

### Community 42 - "Deployment Architecture — NexusOps (target state)"
Cohesion: 0.15
Nodes (13): 10. Events and WS during runs, 12. Rollback semantics (existing behavior kept), 13. The simulated runner stays — labeled, 14. Open questions, 1.1 The honest defect list, 1. Current state — what is real and what is simulated, 3. Target pipeline, 6. Phased scope (+5 more)

### Community 43 - "AuthContext.tsx"
Cohesion: 0.02
Nodes (83): Membership, SearchResult, User, AuthContext, AuthProvider(), AuthState, isOrgSelectionError(), MeResponse (+75 more)

### Community 44 - "v1/health.py"
Cohesion: 0.20
Nodes (13): liveness(), get, Response, Health probes: liveness (always cheap) and readiness (checks dependencies).…, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness(), HealthOut (+5 more)

### Community 45 - "test_permissions.py"
Cohesion: 0.09
Nodes (19): permission_exists(), PermissionSpec, Permission registry and role matrix. Permissions are *data*: the registry below…, _auth_context(), _FakeCtx, Unit tests for the permission registry, scope matching and RBAC gate., Duck-typed stand-in for AuthContext., A fake context in the given organization. ``membership_status=None`` models a… (+11 more)

### Community 46 - "routes.py"
Cohesion: 0.20
Nodes (25): create_route(), delete_route(), disable_route(), _domain_status(), enable_route(), get_route(), list_routes(), AsyncSession (+17 more)

### Community 47 - "test_phase3_nodes.py"
Cohesion: 0.15
Nodes (33): _create_token(), _dispatch(), _enroll(), _enrolled_node(), _load_agent_module(), _mutate_in_system_scope(), Phase 3 — Nodes & Agent v2 end-to-end behaviour. Grouped by the question each…, Import the shipped agent source (sync, so async tests never touch Path). (+25 more)

### Community 48 - "test_ssrf.py"
Cohesion: 0.19
Nodes (24): UnprocessableEntity, assert_safe_url(), _raise_block(), Validate *url* for outbound requests; return the parsed URL or raise 422.…, Reject non-empty values that are not valid IPv4/IPv6 addresses., _validate_ip(), install_dns(), Exception (+16 more)

### Community 49 - "secret_service.py"
Cohesion: 0.12
Nodes (37): An encrypted configuration value, scoped to org, project or environment.…, Secret, _actor_type(), _collect_refs(), create_secret(), delete_secret(), _detail(), get_secret() (+29 more)

### Community 50 - "update_role"
Cohesion: 0.12
Nodes (23): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, delete, get (+15 more)

### Community 51 - "servers.py"
Cohesion: 0.11
Nodes (32): apply_node_proxy_config(), create_enrollment_token(), create_server(), _enrollment_created(), _enrollment_out(), post, Request, Node endpoints: CRUD, tags, agent enrollment tokens. The domain entity is the… (+24 more)

### Community 52 - "proxy_service.py"
Cohesion: 0.06
Nodes (71): ListenerOwnership, Last nginx apply outcome for a route, as reported by its node's agent.…, Who holds one required listener port, per the node's pre-flight. The…, RouteConfigState, has_live_operation(), Whether a live (pending/claimed/running) operation of this type exists. Used to…, after_hello(), capability_of() (+63 more)

### Community 53 - "test_migration_phase21.py"
Cohesion: 0.22
Nodes (9): Phase 2.1 corrective migration: legacy ``environment_type`` classification.…, Every case is classified as documented, ids and ownership intact., An explicit non-DEV classification survives the corrective migration. The…, The correction is part of ``head`` and adds no extra Alembic head., Insert one legacy environment per case, in two organizations., _seed_typed_environments(), test_corrective_migration_is_reachable_from_head(), test_corrects_legacy_environment_types() (+1 more)

### Community 54 - "v1/auth.py"
Cohesion: 0.08
Nodes (52): change_password(), _clear_refresh_cookie(), _cookies_secure(), login(), logout(), me(), _optional_actor(), AsyncSession (+44 more)

### Community 55 - "test_agent_nginx_contract.py"
Cohesion: 0.08
Nodes (53): _agent_bundle(), agent_fixture(), _bootstrap_fixture(), _load_agent(), Any, fixture, parametrize, Path (+45 more)

### Community 56 - "create_user"
Cohesion: 0.13
Nodes (19): create_user(), deactivate_user(), get_user(), CurrentUser, DbSessionDep, delete, get, patch (+11 more)

### Community 57 - "alembic"
Cohesion: 0.05
Nodes (13): alembic, downgrade(), rename ``server.*`` permission codenames to ``node.*`` The Node/Server…, _rename_permissions(), upgrade(), Fix pre-existing model/migration drift (surfaced by the new drift check). Two…, downgrade(), Phase 2.1 — correct legacy ``environment_type`` classification. The Phase 2… (+5 more)

### Community 58 - "_attempt_delivery"
Cohesion: 0.36
Nodes (9): _as_uuid(), _attempt_delivery(), decode_delivery_cursor(), encode_delivery_cursor(), list_deliveries(), _now(), datetime, UUID (+1 more)

### Community 59 - "helpers.py"
Cohesion: 0.06
Nodes (62): owner(), Bootstrap owner credentials for this test (fresh DB => first user). ``headers``…, bearer(), cookie_attributes(), error_of(), login_account(), login_headers(), Any (+54 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "_list_deployments"
Cohesion: 0.09
Nodes (41): _attribute_step_idx(), cancel_deployment(), _emails_for(), get_deployment(), list_application_deployments(), list_deployment_logs(), _list_deployments(), _parse_sort() (+33 more)

### Community 62 - "test_error_logging.py"
Cohesion: 0.22
Nodes (4): Regression: the catch-all 500 handler must not log raw exception text.…, _SpyLogger, test_unhandled_exception_handler_logs_class_not_message(), fastapi_testclient

### Community 63 - "dns_verifier.py"
Cohesion: 0.12
Nodes (19): apex_of(), Canonical domain/hostname handling — one pure function per question. Every…, The name a wildcard Domain is anchored at (``*.example.com`` →…, The exact TXT owner name a user must publish at their provider., verification_record_name(), _discover_nameservers(), _normalise_ns(), observe() (+11 more)

### Community 64 - "test_phase2_environments.py"
Cohesion: 0.18
Nodes (22): _environment(), _project(), parametrize, Phase 2: project-scoped environments, config layering, and their isolation. The…, Uniqueness is ``(project_id, slug)`` — not instance-wide., The update path is validated too (the pre-Phase-2 gap)., Knowing an environment UUID is not access: the project link must hold., Another tenant cannot reach the project, its environments, or its detail. (+14 more)

### Community 65 - "route_service.py"
Cohesion: 0.10
Nodes (48): One hostname+path served from one container on one node. Relationship rules the…, Route, mark_reconcile_required(), Record that *node*'s desired configuration changed and is not applied yet.…, _actor(), _apply_or_defer(), _conflicting_route(), create_route() (+40 more)

### Community 66 - "test_schema_redaction.py"
Cohesion: 0.14
Nodes (18): is_sensitive_header(), mask_sensitive_headers(), field_serializer, True when *name* looks like it carries a credential (Authorization etc.)., Return a copy of *headers* with sensitive values replaced by a mask., mask_target(), Human-readable masked target safe to expose over the API. For webhook families…, _monitor_out() (+10 more)

### Community 67 - "typing"
Cohesion: 0.05
Nodes (89): Dependency factory enforcing a permission; returns 403 when denied., require_permission(), list_alerts(), mark_all_read(), mark_read(), CurrentUser, DbDep, Depends (+81 more)

### Community 68 - "encrypt_str"
Cohesion: 0.08
Nodes (30): decrypt_str(), digest_of(), encrypt_str(), _fernet(), Short server-verifiable digest used for change detection display. HMAC-SHA256…, parametrize, test_decrypt_with_wrong_ciphertext_raises_value_error(), test_digest_is_keyed_not_plain_sha256() (+22 more)

### Community 69 - "package.json"
Cohesion: 0.13
Nodes (15): name, private, type, version, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom (+7 more)

### Community 70 - "test_event_registry.py"
Cohesion: 0.22
Nodes (7): event_type_catalogue(), is_known_event_type(), Return True when *event_type* is part of the canonical registry., Serialise the registry for the ``/events/types`` endpoint., Registry coherence: schema-advertised event types must equal the canonical…, test_catalogue_serialises_every_entry(), test_known_event_lookup()

### Community 71 - "test_secrets.py"
Cohesion: 0.09
Nodes (29): Exception, A ``${secret:KEY}`` reference could not be resolved. Fail-closed. Carries…, One successfully resolved reference: metadata for audit, no value., Outcome of resolving an environment's config references., Resolve every ``${secret:KEY}`` reference an environment's config names.…, resolve_secrets_for_environment(), ResolvedSecrets, SecretReference (+21 more)

### Community 72 - "test_nginx_renderer.py"
Cohesion: 0.13
Nodes (37): NginxProvider, ValueError, The only production provider in Phase 4., Where a route's fragment lands, so the service can name it in events., Rendering refused the input. Always a bug or a corrupt row, never a leak., RenderError, provider(), fixture (+29 more)

### Community 73 - "domain_service.py"
Cohesion: 0.09
Nodes (44): DomainStatus, Ownership-verification lifecycle of a Domain (domain-routing.md §4). ``STALE``…, Domain, One DNS name an organization is proving it controls. ``name`` is canonical (see…, What the lifecycle should do with an observation., VerificationDecision, _actor(), apply_decision() (+36 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "TenancyScopeError"
Cohesion: 0.10
Nodes (26): _apply_scope_guc(), _desired_guc(), _guard(), _has_org_predicate(), install_tenancy_guards(), _mappers_of(), org_scoped_table_names(), Any (+18 more)

### Community 76 - "AsyncSession"
Cohesion: 0.13
Nodes (25): _detail(), AsyncSession, Compact system event projection for server timelines., SystemEventOut, container_counts(), get_server(), list_tags_with_usage(), AsyncSession (+17 more)

### Community 77 - "domains.py"
Cohesion: 0.11
Nodes (39): create_domain(), delete_domain(), _enqueue_verification(), get_domain(), list_domain_routes(), list_domains(), _project_names(), alias (+31 more)

### Community 78 - "incidents.py"
Cohesion: 0.13
Nodes (33): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+25 more)

### Community 79 - "test_phase2_secrets.py"
Cohesion: 0.19
Nodes (21): _env(), _project(), Phase 2 secrets: layered scope, immutable versions, rollback, isolation. Two…, Two racing rotations must both be kept and never share a version number., Another tenant cannot read, rotate, roll back or even enumerate the secret., The documented example: same key at three scopes; most specific wins., A ref declared in the project base config resolves for its environments., _resolved() (+13 more)

### Community 80 - "RolesPage.tsx"
Cohesion: 0.11
Nodes (15): Role, RolesPage, describeError(), GROUP_STYLE, LEGEND_STYLE, OPTION_STYLE, PermissionSpec, roleAllows() (+7 more)

### Community 81 - "test_schemas_server.py"
Cohesion: 0.21
Nodes (22): Payload for registering a server., Partial update. ``tags`` replaces the full set when provided., ServerCreate, ServerUpdate, _base(), parametrize, Unit tests for app.schemas.server (validation only, no I/O)., test_empty_ip_is_allowed_but_whitespace_collapses() (+14 more)

### Community 82 - "canonicalize_name"
Cohesion: 0.11
Nodes (32): canonicalize_name(), canonicalize_path(), _check_labels(), _check_not_ip(), hostname_is_covered(), _idna(), InvalidName, is_valid_path() (+24 more)

### Community 83 - "tests/conftest.py"
Cohesion: 0.25
Nodes (6): configure_test_env(), Test bootstrap: pin every cached setting BEFORE the first ``app`` import. The…, KEY=VALUE pairs from the repo .env (first definition wins); never logged., Export the exact settings the app caches; host values cannot leak through., _read_dot_env(), os

### Community 84 - "DbDep"
Cohesion: 0.15
Nodes (22): delete_server(), get_server(), list_enrollment_tokens(), list_servers(), list_tags(), node_proxy_status(), node_route_targets(), DbDep (+14 more)

### Community 85 - "NotFound"
Cohesion: 0.08
Nodes (55): list_sessions(), CurrentUser, DbSessionDep, delete, get, Request, UUID, Active sessions of this organization's members. Defaults to the caller's own;… (+47 more)

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "operation_service.py"
Cohesion: 0.09
Nodes (44): OperationStatus, Lifecycle of one node operation (node-agent-architecture.md §5.1).…, Operation, Whether the agent reported this operation as successful. A terminal check, not…, One whitelisted action for one node, with a CAS lifecycle. ``attempts`` is…, _active_org(), _bounded(), cancel_operation() (+36 more)

### Community 88 - "LogLine"
Cohesion: 0.09
Nodes (27): LogSource, LogLine, One parsed log record from a container log stream., datetime, Replay registered LogEntry rows ordered by ts (tail N). ``follow`` is ignored…, collect_recent_logs(), Pull recent logs from running containers of a real host. Simulated hosts are…, append_lines() (+19 more)

### Community 89 - "Settings"
Cohesion: 0.14
Nodes (6): field_validator, model_validator, Username from :attr:`database_url`, or ``None`` if it is unparseable., Validated application settings (loaded from environment / .env)., Settings, BaseSettings

### Community 90 - "domain_routing.py"
Cohesion: 0.15
Nodes (23): _affected_node_ids(), _announce(), _apply_for_node(), _audit_action(), datetime, task, UUID, Domain verification and routing sweeps. Two properties shape this module: * **A… (+15 more)

### Community 91 - "validate_config"
Cohesion: 0.09
Nodes (29): field_validator, collect_secret_refs(), walk(), ConfigValidationError, effective_config(), merge_config(), Any, ValueError (+21 more)

### Community 92 - "alert_service.py"
Cohesion: 0.20
Nodes (17): AlertSeverity, Alert, create_alert(), get_alert(), mark_all_read(), mark_read(), AsyncSession, UUID (+9 more)

### Community 93 - "apply_scope_to_session"
Cohesion: 0.06
Nodes (67): asyncio, get_engine(), get_sessionmaker(), async_sessionmaker, AsyncEngine, AsyncSession, apply_scope_to_session(), current_scope() (+59 more)

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
Cohesion: 0.15
Nodes (15): EDGE, MAILPIT, ADMIN, Bootstrap, bootstrapVia(), test, ADMIN, formLogin() (+7 more)

### Community 99 - "after_commit"
Cohesion: 0.43
Nodes (7): after_commit(), _on_commit(), _on_rollback(), Any, AsyncSession, Run ``factory`` once the current transaction commits. ``label`` names the work…, _run()

### Community 100 - "redact_mapping"
Cohesion: 0.22
Nodes (13): _is_sensitive_key(), Substring match on a normalised key so header-style names are caught too.…, Return a copy of *data* with sensitive values replaced. Used by audit metadata…, redact_mapping(), parametrize, Unit tests for app.core.logging redaction (pure functions only)., test_case_insensitive_substring_match(), test_flat_sensitive_keys_redacted() (+5 more)

### Community 102 - "env.py"
Cohesion: 0.24
Nodes (10): _database_url(), Alembic environment: metadata comes from app.models, URL from app settings., Migrations run as the table **owner**, never as the application role. The owner…, Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online(), Owner-role DSN for Alembic and the container entrypoint. Migrations… (+2 more)

### Community 103 - "sweep_routes"
Cohesion: 0.13
Nodes (22): Keep every routed node's live configuration matching the desired bundle. One…, sweep_routes(), _live_operations(), _node_proxy_state(), A detected difference is repaired unattended — and bounded while it isn't., Disable the last route on an offline node, then let the reconciler converge., Delete the last route on an offline node: the node's own state remembers it., Credentials for a Viewer, who holds the routing read permissions only. (+14 more)

### Community 104 - "test_migration_phase4.py"
Cohesion: 0.15
Nodes (26): _exec(), _owner_dsn(), Statement, Run statements in one transaction as the owner (committed on success)., _rows(), _columns(), _integrity_error(), _migrate_from_phase3() (+18 more)

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
Nodes (27): ContainerInfo, ContainerStats, Normalized view of a container as reported by any provider., Point-in-time resource usage snapshot., _as_float(), _compute_stats(), _cpu_percent(), _network_bytes() (+19 more)

### Community 109 - "Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)"
Cohesion: 0.25
Nodes (9): API keys (X-API-Key, nxo_..., scope intersection), First boot sequence (api entrypoint migrates, compose never seeds), Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test), Makefile workflows (up/test/lint/typecheck/migrate/seed), HIGH finding: API-key scope bypass for superadmin-owned keys (fixed: scope intersection first), Security audit 2026-09 (26 raw findings -> 20 confirmed, all fixed), HIGH finding: known seed superadmin + API key backdoor (fixed: NEXUSOPS_ALLOW_SEED opt-in, one-time password), Threat model (edge attacker, malicious agent, curious operator, leaked token, SSRF) (+1 more)

### Community 110 - "ScopedSession"
Cohesion: 0.09
Nodes (14): Whether the runtime connection is the RLS-enforced application role. False…, A session that enters its tenancy scope around each operation. A fixture cannot…, ScopedSession, 10. Migration (Phase 1), 1. Tenancy invariants, 2.1 Org creation — v1 decision, 2. Org resolution on every request, 3. The session guard (the mechanical layer) (+6 more)

### Community 111 - "create_organization"
Cohesion: 0.16
Nodes (23): add_member(), create_organization(), get_organization(), membership_for_user(), AsyncSession, Membership, Organization, Request (+15 more)

### Community 112 - "test_app_gating.py"
Cohesion: 0.44
Nodes (8): _app_for_environment(), MonkeyPatch, ENVIRONMENT gating contract: docs exposure and HSTS (see .env.example).…, create_app() with get_settings() patched to the given environment., test_non_production_does_not_emit_hsts(), test_non_production_keeps_docs_and_schema(), test_production_emits_hsts(), test_production_hides_docs_and_schema()

### Community 113 - "dnsmock.py"
Cohesion: 0.12
Nodes (24): resolver(), answer(), encode_name(), encode_txt(), forward(), main(), parse_question(), TXT rdata: one or more length-prefixed strings, each ≤ 255 bytes. (+16 more)

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "APIModel"
Cohesion: 0.02
Nodes (81): AgentContainerPortIn, AgentEnrollOut, AgentHeartbeatOut, AgentHelloOut, AgentTokenRotation, CapabilityReport, Tells the agent how often to report and what protocol it negotiated., One published-port binding of a container, as docker reports it. Four distinct… (+73 more)

### Community 116 - "test_tenancy_allowlist.py"
Cohesion: 0.20
Nodes (14): AST, _actual_callers(), _calls_system_scope(), _module_path(), Path, The system-scope allowlist is the only fence around the tenancy carve-out.…, Every module that could open a system scope: ``app/`` plus the scripts., No module may lift tenant isolation without being named in the list. (+6 more)

### Community 117 - "_alembic_config"
Cohesion: 0.18
Nodes (13): _alembic_config(), _at_revision(), _migration_dsn(), Run one Alembic direction against ``database`` through the app's settings path.…, Move ``database`` *back* to ``revision``. The same code path a deployment uses…, Phase 2 adds one migration; heads must not fork., _run_downgrade(), test_exactly_one_alembic_head() (+5 more)

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
Cohesion: 0.07
Nodes (41): A valid POST /servers body with per-test overrides., server_payload(), _enrolled(), _heartbeat(), Agent ingest pipeline: hello, heartbeat, staleness transitions, events., A container absent from a later heartbeat is gone from the daemon., A payload at the agent's cap may be truncated — absence proves nothing., test_heartbeat_at_container_cap_skips_reconciliation() (+33 more)

### Community 123 - "test_migration_phase2.py"
Cohesion: 0.13
Nodes (22): alembic_config, alembic_script, Phase 2 migration (`b2c3d4e5f6a7`) against realistic legacy data. The promotion…, Upgrade ``database`` to ``revision``., The pre-Phase-2 shapes: application-scoped environments, per-app dupes., A fresh database reaches the same shape the models describe., _run_migration(), _seed_legacy_data() (+14 more)

### Community 124 - "middleware.py"
Cohesion: 0.13
Nodes (17): ASGIApp, AccessLogMiddleware, HTTP middleware: request ids, security headers, structured access logs., Baseline hardening headers on every API response., RequestIDMiddleware, SecurityHeadersMiddleware, create_app(), _include_routers() (+9 more)

### Community 125 - "OperationError"
Cohesion: 0.18
Nodes (15): _demux_docker_stream(), _docker_error(), execute_operation(), OperationError, Exception, A stable, sanitized failure contract for the control plane., Re-validate the operation's parameters locally, against a closed shape., Decode docker's 8-byte-header frame stream, or ``None`` if not framed. (+7 more)

### Community 126 - "list_operations"
Cohesion: 0.18
Nodes (17): cancel_operation(), create_operation(), get_operation(), list_operations(), DbDep, Depends, get, post (+9 more)

### Community 127 - "test_phase4_routing.py"
Cohesion: 0.10
Nodes (33): One bounded look at a name's authoritative TXT record., TxtObservation, _create_domain(), _dns_stub(), _fake_observe(), fixture, MonkeyPatch, parametrize (+25 more)

### Community 137 - "AuditLogPage.test.tsx"
Cohesion: 0.20
Nodes (5): AuditEntry, AuditLogPage(), formatTimestamp(), shortId(), mockedGet

### Community 146 - "test_auth_multi_org.py"
Cohesion: 0.13
Nodes (28): SystemEvent, event_frame_from_row(), Serialize a persisted event for WS delivery (used on replay/backfill)., _latest_audit(), _latest_event(), _list_ids(), Any, UUID (+20 more)

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

### Community 157 - "Secrets Architecture"
Cohesion: 0.10
Nodes (20): 10. Resolution flow at deploy time, 1.1 Storage and crypto, 1.2 Data model, 1.3 API surface (metadata-only reads), 1.6 Gap list (Phase 2 status), 1. Current state, 2.1 Resolution runs inside org scope, 2.2 Migration mapping (applied by `b2c3d4e5f6a7`) (+12 more)

### Community 158 - "test_schemas_agent.py"
Cohesion: 0.11
Nodes (36): AgentContainerIn, AgentHeartbeatIn, AgentHelloIn, Observed container state reported by an agent., Periodic metrics + observed containers from an enrolled agent. Network counters…, First contact from an agent after enrollment; fills static host facts., test_container_ports_report_the_four_facts(), _container() (+28 more)

### Community 159 - "organizations.py"
Cohesion: 0.15
Nodes (18): create_organization(), list_my_organizations(), CurrentUser, DbSessionDep, get, IdentityUser, patch, post (+10 more)

### Community 160 - "main"
Cohesion: 0.11
Nodes (19): build_capabilities(), _build_hello_payload(), _enroll(), _interruptible_sleep(), main(), memory_total_mb(), os_info(), persist_token() (+11 more)

### Community 161 - "ssrf.py"
Cohesion: 0.19
Nodes (12): assert_safe_url_async(), ValueError, SSRF guard applied to every operator-supplied outbound URL. Monitors and…, Async wrapper around :func:`assert_safe_url`; DNS runs off the loop., Internal signal: a specific SSRF rule matched (never shown to clients)., UrlRejected, _validate_syntax(), test_syntax_rejects_bad_urls() (+4 more)

### Community 162 - "decide"
Cohesion: 0.23
Nodes (18): decide(), matches_token(), Constant-time comparison of the observed TXT values against the token. TXT…, Turn one observation into the verification outcome — pure, no I/O.…, observation(), parametrize, The verification decision: every outcome, without a network. ``decide`` is…, test_a_sweep_invalidates_a_changed_delegation_even_with_the_token() (+10 more)

### Community 163 - "seed.py"
Cohesion: 0.09
Nodes (39): ``before_flush`` handler: own new rows, and refuse rows that change hands.…, _stamp_org_on_flush(), DeploymentEnvironment, Project, A **project-scoped** deployment environment (Phase 2 promotion). The…, EnvironmentType, MonitorStatus, Kind of a project-scoped deployment environment (Phase 2). Descriptive only —… (+31 more)

### Community 164 - "AgentClient"
Cohesion: 0.15
Nodes (8): AgentClient, _docker_raw(), A verifying TLS context. Verification is never disabled. A private/self-hosted…, Refuse to send credentials over plain HTTP to a non-loopback server. The…, One raw Docker API call; returns ``(status, body_bytes)``., _tls_context(), _UnixHTTPConnection, SSLContext

### Community 165 - "_enforce"
Cohesion: 0.33
Nodes (7): _enforce(), node_rate_limit(), _dependency(), Request, _dependency(), Return a dependency keyed on the **authenticated node**, not the IP. A fleet…, Shared fixed-window accounting for every limiter in this module.

### Community 166 - "nginx.py"
Cohesion: 0.11
Nodes (26): _header_lines(), _quote(), _rate_zone(), NginxProvider — a pure, deterministic renderer plus the two op wrappers.…, Validate the route's headers and split them by destination., Wrap an already-validated value in quotes for a template slot. Values reaching…, The ``limit_req_zone`` declaration for a rate-limited route., A fixed host redirect, or ``None`` for a normal proxying route. (+18 more)

### Community 167 - "AuthContext"
Cohesion: 0.07
Nodes (46): _attach_organization(), AuthContext, get_current_user(), get_identity(), get_optional_user(), _load_organization(), _load_permissions(), membership_for_org() (+38 more)

### Community 168 - "Server"
Cohesion: 0.09
Nodes (32): agent_heartbeat(), agent_hello(), claim_operation(), _presented_token(), DbDep, post, Request, Response (+24 more)

### Community 169 - "test_a_late_result_for_an_expired_operation_cannot_fail_a_live_route"
Cohesion: 0.18
Nodes (17): _agent_result_body(), _audits(), _claim(), _event_types(), The same delivery twice: one apply, one set of events, one audit row., A report that contradicts what already happened is ignored, not applied., A report that arrives after its operation expired changes nothing at all., The result body the agent sends for one operation it claimed. Shared by the… (+9 more)

### Community 170 - "test_agent_contract.py"
Cohesion: 0.20
Nodes (15): agent_fixture(), _load_agent(), _patch_stats(), Any, fixture, MonkeyPatch, Contract tests: the shipped agent's payloads must satisfy the ingest schemas.…, One-shot docker stats reduce to cpu/mem/limit fields the schema accepts, with… (+7 more)

### Community 171 - "get_settings"
Cohesion: 0.07
Nodes (34): _quoted_list(), Add the operations framework table (node-agent-architecture.md §5). One tenant-…, upgrade(), downgrade(), _drop_constraint(), _quoted_list(), Phase 2 — projects & environments: env promotion, config, secret versions. This…, upgrade() (+26 more)

### Community 172 - "_handle_apply_result"
Cohesion: 0.14
Nodes (16): ProxyApplyOutcome, Terminal outcome of one ``nginx.apply`` operation on a node., _apply_outcome(), _clear_reconcile_required(), _handle_apply_result(), _handle_bootstrap_result(), handle_operation_result(), timedelta (+8 more)

### Community 173 - "2. Entities"
Cohesion: 0.22
Nodes (9): 2.1.1 ApiKey org binding detail, 2.1 Identity & tenancy (new), 2.2.1 Environment promotion detail — **shipped in Phase 2**, 2.2 Delivery (existing models, extended), 2.4 Routing & TLS (new subsystem), 2.5 Secrets (re-scoped — **shipped in Phase 2**), 2.6 Observability (existing, org-scoped via parents), 2.7 Backups, connections, billing (new subsystems, design-only in early phases) (+1 more)

### Community 174 - "create_api_key"
Cohesion: 0.16
Nodes (17): create_api_key(), list_api_keys(), CurrentUser, DbSessionDep, delete, get, post, Request (+9 more)

### Community 175 - "scope_matches"
Cohesion: 0.14
Nodes (14): Check an API-key scope list against a required permission. Supports exact match…, scope_matches(), parametrize, test_scope_matches_truth_table(), 0. What shipped (Phase 1), 1. Principles (already true in the codebase, kept), 2. Registry changes (Phase 1 + new subsystems), 3. The five system roles (target) (+6 more)

### Community 176 - "Platform Security Model — NexusOps"
Cohesion: 0.11
Nodes (18): make(), 10.1 Node revocation playbook (compromised node / leaked agent token), 10.2 Key compromise playbook, 10. Incident response, 1.1 Real vs simulated today (do not mistake one for the other), 1. Scope, stance, and simulation honesty, 2. Assets, 3. Trust boundaries (+10 more)

### Community 177 - "ContainerListPage.test.tsx"
Cohesion: 0.29
Nodes (3): ApiError, server, serversPage

### Community 178 - "network_rates"
Cohesion: 0.33
Nodes (6): build_facts(), network_rates(), network_total_bytes(), Sum rx/tx bytes over non-loopback interfaces from /proc/net/dev., Return (rx_kb_s, tx_kb_s) or ``(None, None)`` when not measurable., Open-ended host facts, stored in the node's flexible JSONB blob. Deliberately…

### Community 179 - ".dispatch"
Cohesion: 0.60
Nodes (3): Request, Response, RequestResponseEndpoint

### Community 180 - "websocket_endpoint"
Cohesion: 0.67
Nodes (3): websocket, Hand the socket to the hub (auth handshake handled there)., websocket_endpoint()

### Community 181 - "_nginx_apply"
Cohesion: 0.13
Nodes (17): _fsync_dir(), _nginx_apply(), Materialize the bundle under ``staged/<id>/`` and return that directory.…, Build a self-contained config for ``nginx -t`` over the staged tree. The…, Move the staged tree over the live one, keeping the previous as backup., Put the previous known-good tree back. Returns whether it was possible., Stage → validate → swap → reload, with a rollback on a failed reload., Persist the last apply outcome atomically (temp + rename). (+9 more)

### Community 182 - "_nginx_bootstrap"
Cohesion: 0.18
Nodes (14): _insert_http_includes(), _nginx_bootstrap(), _nginx_config_test(), _nginx_failure_summary(), Reload nginx via ``-s reload``, falling back to a SIGHUP of the master., Idempotent, minimal, reversible hook-up of the managed include. The only change…, Insert the include lines at the end of the single top-level ``http`` block. A…, Make control characters safe and bound the result. Never touches container… (+6 more)

### Community 183 - "8. Upstream binding and re-render triggers"
Cohesion: 0.29
Nodes (7): 8.1 Binding rules, 8.2 Certificate selection rule (this doc owns it) — **Phase 5 target design**, 8.3 Re-render triggers, 8.4 Drift and reconciliation, 8.5 How deployments hook routing (post-deploy route sync), 8. Upstream binding and re-render triggers, Requested is not confirmed

### Community 184 - "api_key_service.py"
Cohesion: 0.22
Nodes (14): create_api_key(), list_api_keys(), AsyncSession, Request, UUID, API key lifecycle: creation with scope validation, listing, revocation., Live (non-revoked) keys owned by *owner_id*, newest first., Revoke a key owned by *owner_id*. Foreign keys look like NotFound (no leak). (+6 more)

### Community 185 - "update_channel"
Cohesion: 0.20
Nodes (19): EmailConfig, _audit(), create_channel(), decrypt_channel_config(), delete_channel(), encrypt_config(), _normalize_events(), Any (+11 more)

### Community 186 - "run_async"
Cohesion: 0.04
Nodes (93): flush_pending_publishes(), Wait for frames scheduled by ``after_commit`` hooks to reach Redis. The commit…, dispatcher_loop(), Send every due PENDING / retryable-FAILED delivery. Returns count attempted. A…, Consume ``nx:events`` and sweep due retries forever. Runs as a lifespan task., retry_due_deliveries(), Celery application: periodic cadences live here, dynamic work is claimed…, task (+85 more)

### Community 187 - "Conflict"
Cohesion: 0.15
Nodes (25): Conflict, create_role(), delete_role(), effective_permissions(), get_role(), list_roles(), permissions_for_role(), AsyncSession (+17 more)

### Community 188 - "instant_pacing"
Cohesion: 0.40
Nodes (4): instant_pacing(), fixture, MonkeyPatch, Remove the per-line sleeps; pacing bounds are asserted separately.

### Community 189 - "phase3.spec.ts"
Cohesion: 0.15
Nodes (10): frontend_e2e_fixtures_expect, AGENT, NodeDetail, OperationRow, REPO_ROOT, ref_node_child_process, ref_node_fs, ref_node_os (+2 more)

### Community 190 - "_mutate_in_system_scope"
Cohesion: 0.22
Nodes (14): _container_id(), _create_node(), _heartbeat(), heartbeat_payload(), _mutate_in_system_scope(), test_a_container_on_another_node_is_refused(), test_a_container_without_published_ports_offers_nothing(), test_a_listener_conflict_is_named_precisely() (+6 more)

### Community 191 - "docs/engineering-report.md - build and verification report"
Cohesion: 0.24
Nodes (12): docker-compose.dev.yml - dev overlay, docker-compose.docker-sock.yml - docker socket override, docker-compose.yml - full stack definition, docs/agent.md - agent guide, docs/api.md - API guide, Append-only audit log (Postgres BEFORE UPDATE OR DELETE trigger), docs/deployment.md - deployment and operations guide, docs/development.md - developer guide (+4 more)

### Community 192 - "20261010_1200-f4a5b6c7d8e9_phase4_domains_and_routes.py"
Cohesion: 0.31
Nodes (9): downgrade(), _drop_tenant_policies(), _grant(), _in_list(), Phase 4 — domains, routes and the routing schema. Adds, in one migration with a…, Grant the app role on *table*; the migration role GUC carries the name. The…, The two-policy shape every tenant table uses: tenant + system scope., _tenant_policies() (+1 more)

### Community 193 - "test_migration_drift.py"
Cohesion: 0.25
Nodes (7): alembic_autogenerate, alembic_migration, Model / migration drift: the schema in the database must match the models.…, ``Base.metadata`` and the migrated database must describe the same schema., The DB whitelist and ``OperationType`` are the same closed set. The migration…, test_models_and_migrations_do_not_drift(), test_operations_type_check_matches_the_enum()

### Community 194 - "EnvironmentUpdate"
Cohesion: 0.27
Nodes (6): EnvironmentBase, EnvironmentUpdate, _normalise_environment_type(), field_validator, Shared environment fields., Partial environment update; omitted fields are left untouched. Config is…

### Community 195 - "channel.py"
Cohesion: 0.20
Nodes (11): ChannelType, DeliveryStatus, ChannelBase, ChannelCreate, DeliveryOut, BaseModel, model_validator, Schemas for notification channels and delivery records. Channel configuration… (+3 more)

### Community 196 - "RouteHeader"
Cohesion: 0.24
Nodes (9): One header a route adds. ``target`` says where it lands., A fixed host redirect. Phase 4 cannot express a scheme change here. There is…, RouteHeader, RouteRedirect, field_validator, Payload for ``POST /routes``. A route is created **disabled** unless…, Partial update. Changing the node re-validates the upstream from scratch., RouteCreate (+1 more)

### Community 197 - "test_schemas_search.py"
Cohesion: 0.33
Nodes (8): Results grouped per entity type, permission-filtered per caller. Every section…, SearchResultOut, Unit tests for global-search schemas., test_extra_fields_are_forbidden(), test_search_hit_requires_core_fields(), test_search_result_defaults_to_empty_sections(), test_search_result_exposes_exactly_the_documented_sections(), test_sections_hold_hits()

### Community 198 - "Product Roadmap — NexusOps Multi-Tenant Platform"
Cohesion: 0.11
Nodes (19): What one reported result did to its operation row. The caller's side effects —…, ResultTransition, 0. Stance, 10. Phase 7 — Teams, grants & custom roles — **proposal, not implemented**, 11. Phase 8 — Backups — **proposal, not implemented**, 12. Phase 9 — Billing & metering — **proposal, not implemented**, 13.1 Scope-creep gates — what must be true before each expansion, 13. First commercially meaningful version (+11 more)

### Community 199 - "Platform Vision — NexusOps"
Cohesion: 0.20
Nodes (10): 1. Where NexusOps is today, 2.1 What we are NOT building, 2.2 The wedge (differentiation), 2. The direction, 3. Guiding principles, 4. Customer journey (target), 5.1 Architecture overview (target), 5. Control plane / data plane boundary (+2 more)

### Community 200 - "ServerOut"
Cohesion: 0.28
Nodes (6): computed_field, Whether the node has reported capabilities at all (v2 hello)., Full server view with recent timeline events and container counts., Server as listed in collections. Never exposes the agent token hash., ServerDetail, ServerOut

### Community 201 - "NotificationChannel"
Cohesion: 0.23
Nodes (11): NotificationChannel, A delivery target (email address / webhook endpoint). ``config_ciphertext``…, _create_monitor(), Monitor checks driving the full down -> incident -> recovery lifecycle., Regression: probe headers and URL query credentials never leave the API. Probe…, A monitor's checks, incidents and timeline all live in its organization, so the…, test_check_now_endpoint_runs_immediately(), test_down_then_recover_lifecycle() (+3 more)

### Community 202 - "test_tasks_util.py"
Cohesion: 0.36
Nodes (8): _answer(), _boom(), _nested(), Unit tests for the Celery-task async bridge (pure asyncio, no broker)., test_run_async_awaits_nested_coroutines(), test_run_async_is_repeatable_per_invocation(), test_run_async_propagates_exceptions(), test_run_async_returns_coroutine_result()

### Community 203 - "ProxyProvider"
Cohesion: 0.33
Nodes (5): ProxyProvider, Any, Protocol, What ``app.services.proxy_service`` is allowed to assume about a provider. The…, 11. Post-deploy hooks

### Community 204 - "ApplicationCreate"
Cohesion: 0.29
Nodes (6): ApplicationBase, ApplicationCreate, Any, field_validator, Shared application fields; ``build_config`` is a free-form dict., Payload to register an application under a project.

### Community 206 - "update_server"
Cohesion: 0.25
Nodes (8): patch, Apply a partial update; ``tags`` replaces the whole set when present., Rotate a node's credential with a bounded dual-token grace window. The previous…, rotate_agent_token(), update_server(), EnrollTokenOut, One-time agent enrollment token. The raw value is never stored., UpdateCtx

### Community 207 - "register_exception_handlers"
Cohesion: 0.36
Nodes (8): _error_payload(), FastAPI, Request, register_exception_handlers(), handle_app_error(), handle_http_exception(), handle_unexpected(), handle_validation_error()

### Community 208 - "_live_bundle_id"
Cohesion: 0.20
Nodes (10): _allowed_bundle_path(), _live_bundle_id(), _live_files(), The bundle fingerprint — byte-identical to the control plane's algorithm.…, Read the live managed tree, or ``None`` when it does not exist yet., Fingerprint of the configuration tree currently on disk., Independently validate a bundle. Anything unexpected is refused., _template_version_of() (+2 more)

### Community 209 - "_memory_count_and_ttl"
Cohesion: 0.25
Nodes (7): _memory_count_and_ttl(), Fixed-window counter backed by process memory. Returns (count, ttl)., _clean_memory_windows(), fixture, MonkeyPatch, redis_down(), test_memory_counter_resets_per_window()

### Community 211 - "_validate_resolution"
Cohesion: 0.32
Nodes (7): _is_forbidden_address(), True when *addr* points into a network the server must never contact.…, Resolve *hostname* (AF_UNSPEC) and refuse any non-public answer., _validate_resolution(), test_validate_resolution_passes_hostname_through(), IPv4Address, IPv6Address

### Community 213 - "parametrize"
Cohesion: 0.29
Nodes (8): is_simulation_url(), True when *url* targets the built-in simulated checker (``sim://``)., parametrize, test_non_simulation_urls(), test_private_and_special_addresses_are_forbidden(), test_public_addresses_are_allowed(), test_simulation_url_detection(), test_syntax_accepts_wellformed_http_urls()

### Community 214 - "pytest"
Cohesion: 0.16
Nodes (12): created_at server defaults must evaluate per insert, not at table creation., Regression: system_events and audit_logs shipped with DEFAULT 'now()' (quoted…, test_audit_and_event_created_at_defaults_are_dynamic(), UUID, Phase 2.2 — the environment-type correction follows the documented precedence.…, Only the previous migration's ``PROD`` output is corrected. A row already…, Create one legacy (application-scoped) environment per case., Every branch of the slug-first rule, end to end through ``head``. (+4 more)

### Community 215 - "DeploymentRunner"
Cohesion: 0.25
Nodes (6): DeploymentRunner, Protocol, Stream output lines for *step_name*; raise StepFailure to fail it., Adapter interface implemented by real (future) and simulated runners., Return the ordered step names for this run., 2. What survives unchanged

### Community 216 - "StepFailure"
Cohesion: 0.25
Nodes (7): Exception, Raised by a runner when a step fails irrecoverably., StepFailure, 5.1 Operation whitelist additions (deployments), 5.2 `RunContext` extension, 5. `AgentDeploymentRunner` — real execution over agent operations, 9. Cancellation and per-step timeouts

### Community 217 - "MonitorTargetType"
Cohesion: 0.33
Nodes (7): MonitorTargetType, What a monitor observes (domain-model.md §2.6, polymorphic targets). ``URL`` is…, _count_rows_in_system_scope(), The second organization wins; the first stops being the owner., test_enabling_a_route_attaches_an_http_uptime_monitor(), test_monitor_optout_is_respected(), test_verified_names_are_platform_unique_with_a_cross_org_flip()

### Community 218 - "assert_safe_tcp_endpoint"
Cohesion: 0.33
Nodes (6): assert_safe_tcp_endpoint(), Validate a ``tcp://`` docker host endpoint for outbound connection. Docker…, test_tcp_endpoint_lax_mode_skips_resolution(), test_tcp_endpoint_rejects_embedded_credentials(), test_tcp_endpoint_rejects_non_tcp_schemes(), test_tcp_endpoint_requires_explicit_port()

### Community 219 - "bundle_summary"
Cohesion: 0.40
Nodes (5): bundle_summary(), Any, Bounded, human-readable bundle metadata for audit rows and UI. Never includes…, Canonical JSON for fingerprint-adjacent comparisons in tests., stable_json()

### Community 220 - "list_servers"
Cohesion: 0.40
Nodes (5): list_servers(), _order_clause(), ColumnElement, Filter + paginate servers. Returns ``(rows, total)``., Translate ``name`` / ``-created_at`` style sort keys to ORDER BY.

### Community 221 - "lax"
Cohesion: 0.40
Nodes (5): lax(), fixture, Production posture: private targets are NOT allowed (resolution runs)., Simulation posture: resolution skipped, syntax still enforced., strict()

### Community 222 - "4. DNS ownership verification"
Cohesion: 0.40
Nodes (5): 4.1 The token, 4.2 The check (control-plane side), 4.3 Anti-takeover rules, 4.4 Sequence: add-domain → verified, 4. DNS ownership verification

### Community 224 - "test_an_offline_node_keeps_the_revoked_route_unresolved_until_it_returns"
Cohesion: 0.50
Nodes (4): _flip_name_to(), Have *second_org* prove control of *name*, returning the verify outcome., Offline during a transfer: unresolved, bounded, and never a false success., test_an_offline_node_keeps_the_revoked_route_unresolved_until_it_returns()

### Community 225 - "_pace"
Cohesion: 0.67
Nodes (3): _pace(), Deterministic per-line delay between 0.05s and 0.35s., test_pace_bounds()

### Community 227 - "_publish_live_frame"
Cohesion: 0.67
Nodes (3): _publish_live_frame(), datetime, Best-effort push of a lightweight metric frame for live dashboards.

## Knowledge Gaps
- **458 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+453 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2298 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **25 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `6. Tooling: reproducible e2e` connect `run_async` to `OperationType`, `TenancyScopeError`, `client.ts`, `apply_scope_to_session`, `auth_service.py`?**
  _High betweenness centrality (0.271) - this node is a cross-community bridge._
- **Why does `useEventStream()` connect `client.ts` to `apiGet`, `App.tsx`, `AuthContext.tsx`, `ServerDetailPage.tsx`, `@tanstack/react-query`, `run_async`?**
  _High betweenness centrality (0.271) - this node is a cross-community bridge._
- **Why does `TenancyScopeError` connect `TenancyScopeError` to `seed.py`, `enums.py`, `AuthContext`, `assert_error_code`, `LogLine`, `run_async`, `apply_scope_to_session`, `test_tenant_isolation.py`?**
  _High betweenness centrality (0.113) - this node is a cross-community bridge._
- **Are the 94 inferred relationships involving `AuthContext` (e.g. with `TenancyScopeError` and `MembershipStatus`) actually correct?**
  _`AuthContext` has 94 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `APIModel` (e.g. with `OperationSpec` and `test_specs_reject_unknown_params()`) actually correct?**
  _`APIModel` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `Server` (e.g. with `ServerStatus` and `2.3 Infrastructure — Nodes`) actually correct?**
  _`Server` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `apiGet()` (e.g. with `ContainerDetailPage.test.tsx` and `mockApi()`) actually correct?**
  _`apiGet()` has 5 INFERRED edges - model-reasoned connections that need verification._