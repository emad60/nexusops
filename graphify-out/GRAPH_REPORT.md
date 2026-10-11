# Graph Report - nexusops  (2026-10-11)

## Corpus Check
- 354 files · ~377,210 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: (none) 10, .example 1, .service 1)

## Summary
- 5864 nodes · 17274 edges · 242 communities (222 shown, 20 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1356 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c354e45b`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- apiGet
- project_service.py
- ApiKeysPage.tsx
- _proxy_ready_node
- container_service.py
- types.ts
- resolve_client_ip
- operation.py
- App.tsx
- test_agent_v2.py
- assert_error_code
- ServerDetailPage.tsx
- list_events
- client.ts
- projects.py
- models/__init__.py
- deployment_engine.py
- SimulatedDockerProvider
- enrollment_service.py
- rollback_secret
- get_application
- list_containers
- get_latest_server_metrics
- get_settings
- Domain Routing — NexusOps
- monitor_service.py
- Node & Agent Architecture
- test_agent_backoff.py
- SimulatedDeploymentRunner
- nexusops_agent.py
- integration/conftest.py
- login
- create_host
- test_rate_limit.py
- docker_hosts.py
- test_ws_hub.py
- BundleFile
- search
- publish
- list_deliveries
- DockerProvider
- test_monitor_transport.py
- StepFailure
- AuthContext.tsx
- schemas/health.py
- test_permissions.py
- routes.py
- test_phase3_nodes.py
- BadRequest
- NotFound
- roles.py
- DbDep
- proxy_service.py
- _exec
- v1/auth.py
- test_agent_nginx_contract.py
- users.py
- alembic
- dispatch_event_frame
- helpers.py
- compilerOptions
- v1/deployments.py
- test_error_logging.py
- dns_verifier.py
- test_phase2_environments.py
- route_service.py
- test_schema_redaction.py
- AuthContext
- digest_of
- package.json
- test_event_registry.py
- test_secrets.py
- test_nginx_renderer.py
- domain_service.py
- api service (FastAPI / uvicorn :8000)
- monitors.py
- PageParams
- domains.py
- incidents.py
- test_phase2_secrets.py
- RolesPage.tsx
- test_schemas_server.py
- canonicalize_name
- tests/conftest.py
- UUID
- create_user
- devDependencies
- Conflict
- log_service.py
- Settings
- domain_routing.py
- validate_config
- create_alert
- hub.py
- test_phase21_secret_version_integrity.py
- StepLine
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- journey.spec.ts
- after_commit
- redact_mapping
- README.md - NexusOps overview
- _database_url
- _mutate_in_system_scope
- test_migration_phase4.py
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
- APIModel
- test_tenancy_allowlist.py
- _alembic_config
- dependencies
- @tanstack/react-query
- generate_secrets.sh
- ControlHandler
- test_tenant_isolation.py
- test_migration_phase2.py
- middleware.py
- OperationError
- record
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
- Hub
- main
- monitor_transport.py
- decide
- incident_service.py
- AgentClient
- client_ip
- nginx.py
- resolve_auth
- 2. The Node concept
- test_a_late_result_for_an_expired_operation_cannot_fail_a_live_route
- test_agent_contract.py
- 20261009_1000-c3d4e5f6a7b8_enforce_secret_version_integrity.py
- AppError
- 2. Entities
- apikeys.py
- scope_matches
- Platform Security Model — NexusOps
- ContainerListPage.test.tsx
- network_rates
- _node_proxy_state
- websocket_endpoint
- _nginx_apply
- _nginx_bootstrap
- 8. Upstream binding and re-render triggers
- create_api_key
- update_channel
- maintenance.py
- permissions_for_role
- instant_pacing
- phase3.spec.ts
- _heartbeat
- Path
- 20261010_1200-f4a5b6c7d8e9_phase4_domains_and_routes.py
- container.py
- sweep_session
- v1/channels.py
- RouteHeader
- test_schemas_search.py
- Product Roadmap — NexusOps Multi-Tenant Platform
- Platform Vision — NexusOps
- ServerOut
- _create_monitor
- run_async
- NginxBundle
- ._shallow_validate
- Path
- pytest
- register_exception_handlers
- _live_bundle_id
- Multi-Tenancy Architecture
- .__tablename__
- monitoring.py
- test_notifications.py
- _FakeAsyncClient
- test_migration_phase22.py
- SecretOut
- client_ip.py
- _verified_domain
- redact_log_event
- bundle_summary
- permissions.py
- create_app
- 4. DNS ownership verification
- AgentHelloIn
- test_a_transfer_pulls_the_previous_owners_route_from_its_node
- _unique_slug
- list_enrollment_tokens
- _run
- test_run_async_publishes_frames_scheduled_by_the_commit_hook
- 20261009_1100-d4e5f6a7b8c9_correct_legacy_environment_types.py
- 20261009_1300-a1b2c3d4e5f6_add_phase3_nodes_and_agent_v2.py
- sweep_deployments
- _FakeCtx
- 20261004_1200-e7c4a2b9d1f3_add_operations_framework.py
- get_meta
- _is_same_origin
- agent_enroll
- delete_server
- DesiredTree
- 5. The Operations framework
- enrollment_contract
- test_configure_logging_installs_redaction_on_every_logging_path

## God Nodes (most connected - your core abstractions)
1. `AuthContext` - 156 edges
2. `APIModel` - 145 edges
3. `Server` - 93 edges
4. `apiGet()` - 91 edges
5. `record()` - 87 edges
6. `NotFound` - 84 edges
7. `get_settings()` - 82 edges
8. `publish()` - 71 edges
9. `Conflict` - 70 edges
10. `apiPost()` - 70 edges

## Surprising Connections (you probably didn't know these)
- `2. Org resolution on every request` --references--> `resolve_auth()`  [INFERRED]
  docs/multi-tenancy.md → backend/app/api/deps.py
- `3. Cross-cutting decisions` --references--> `require_permission()`  [INFERRED]
  docs/domain-model.md → backend/app/api/deps.py
- `10. Phase 7 — Teams, grants & custom roles — **proposal, not implemented**` --references--> `require_permission()`  [INFERRED]
  docs/product-roadmap.md → backend/app/api/deps.py
- `6.2 Further findings-sourced items (tracked in this doc only — not in the roadmap's hardening table)` --references--> `redact_log_event()`  [INFERRED]
  docs/platform-security-model.md → backend/app/core/logging.py
- `3.2 Route` --references--> `rate_limit()`  [INFERRED]
  docs/domain-routing.md → backend/app/core/rate_limit.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three authentication credential families with centralized permission checks** — docs_api_md_auth, docs_api_md_refresh_rotation, docs_api_md_api_keys, docs_agent_md_enrollment_token, docs_api_md_permission_model [EXTRACTED 1.00]
- **NexusOps compose stack services** — docker_compose_yml_nexusops_stack, docker_compose_yml_postgres_service, docker_compose_yml_redis_service, docker_compose_yml_mailpit_service, docker_compose_yml_api_service, docker_compose_yml_worker_service, docker_compose_yml_scheduler_service, docker_compose_yml_frontend_service, docker_compose_yml_nginx_service [EXTRACTED 1.00]
- **WebSocket real-time fan-out spine** — docs_architecture_md_websocket_hub, docs_api_md_websocket_channels, docker_compose_yml_redis_service, docs_architecture_md_event_bus, readme_react_spa [INFERRED 0.85]

## Communities (242 total, 20 thin omitted)

### Community 0 - "apiGet"
Cohesion: 0.06
Nodes (90): apiDelete(), apiGet(), apiPatch(), apiPost(), ApplicationOut, ENVIRONMENT_TYPE_LABELS, EnvironmentType, IncidentEventOut (+82 more)

### Community 1 - "project_service.py"
Cohesion: 0.17
Nodes (34): actor_of(), _apply_update(), _check_server(), create_application(), create_environment(), create_project(), delete_application(), delete_environment() (+26 more)

### Community 2 - "ApiKeysPage.tsx"
Cohesion: 0.09
Nodes (19): ApiKeyOut, ApiKeysPage, ApiKeyCreatedOut, handleCopyKey(), copyText(), describeError(), EMPTY_FORM, GROUP_STYLE (+11 more)

### Community 3 - "_proxy_ready_node"
Cohesion: 0.14
Nodes (28): _create_route(), _drain(), _proxy_ready_node(), A node that stays offline accumulates one op, not one per attempt., The auto-attached monitor stays on the check → incident → notification path., The reconciler does not turn a healthy node into a status-poll loop., Claim and answer every pending operation, exactly like the agent would.…, The safety check runs again at enable time, not only at creation. (+20 more)

### Community 4 - "container_service.py"
Cohesion: 0.10
Nodes (45): DockerHostStatus, DockerHost, clip(), DockerProviderError, A provider operation failed. ``str()`` is safe to show/log., Truncate *text* to *limit* characters, stripping control chars., describe_provider_error(), is_simulated() (+37 more)

### Community 5 - "types.ts"
Cohesion: 0.02
Nodes (87): AlertOut, CapabilityReport, ChannelOut, CheckOut, DeliveryOut, DeploymentLogLine, DeploymentStatus, DomainDetailOut (+79 more)

### Community 6 - "resolve_client_ip"
Cohesion: 0.28
Nodes (15): Request, Real client address for *request* per the trust model above., resolve_client_ip(), make_request(), Request, Unit tests for the chained-proxy client-IP resolver (app/core/client_ip.py)., test_all_trusted_entries_fall_back_to_peer(), test_empty_header_value_falls_back_to_peer() (+7 more)

### Community 7 - "operation.py"
Cohesion: 0.06
Nodes (42): OperationType, The whitelist. Nothing outside this enum ships as an exec surface. Each type…, AgentOperationClaimOut, AgentOperationResultIn, AgentOperationResultOut, ContainerActionParams, LogsTailParams, OperationOut (+34 more)

### Community 8 - "App.tsx"
Cohesion: 0.04
Nodes (103): DeploymentOut, Page, ProjectOut, AlertsPage, App(), AuditLogPage, ContainerListPage, DeploymentListPage (+95 more)

### Community 9 - "test_agent_v2.py"
Cohesion: 0.08
Nodes (36): agent_fixture(), _load_agent(), Any, fixture, parametrize, Agent protocol v2: honest metrics, capability detection, and the executor. The…, Phase 4 shipped three nginx ops — no file primitive, no command primitive., Trusting a private CA must not weaken verification. (+28 more)

### Community 10 - "assert_error_code"
Cohesion: 0.07
Nodes (57): OperationStatus, Lifecycle of one node operation (node-agent-architecture.md §5.1).…, assert_error_code(), Assert envelope shape + code; returns the inner error object., test_metadata_endpoint_and_private_target_blocked(), _dispatch(), _dispatch_body(), _enrolled_node() (+49 more)

### Community 11 - "ServerDetailPage.tsx"
Cohesion: 0.06
Nodes (42): ContainerOut, MetricPoint, ServerDetail, ServerSummary, ChartSeries, LineChart(), LineChartProps, PAD (+34 more)

### Community 12 - "list_events"
Cohesion: 0.18
Nodes (15): _decode_cursor(), _encode_cursor(), list_event_types(), list_events(), datetime, DbSession, Depends, get (+7 more)

### Community 13 - "client.ts"
Cohesion: 0.05
Nodes (54): API_BASE, ApiError, apiRequest(), buildUrl(), extractError(), getAccessToken(), getActiveOrgId(), onActiveOrgChange() (+46 more)

### Community 14 - "projects.py"
Cohesion: 0.07
Nodes (59): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+51 more)

### Community 15 - "models/__init__.py"
Cohesion: 0.05
Nodes (99): Alembic environment: metadata comes from app.models, URL from app settings., Owner-role DSN for Alembic and the container entrypoint. Migrations…, sync_migration_url(), encrypt_str(), _org_scoped_classes(), Mapped classes marked :class:`~app.models.base.OrgScoped`. Reads the mapper…, Base, big_serial_pk() (+91 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.09
Nodes (64): deployment_log_channel(), Deployment, DeploymentStep, AlertSeverity, DeploymentStatus, DeploymentTrigger, EventLevel, String enum; member names equal values so name/value storage never disagrees. (+56 more)

### Community 17 - "SimulatedDockerProvider"
Cohesion: 0.08
Nodes (31): Any, datetime, Plausible numbers derived from the row plus time-based sine noise., Replay registered LogEntry rows ordered by ts (tail N). ``follow`` is ignored…, Implements :class:`DockerProvider` semantics against DB rows., Make a container row visible to this provider instance., Attach already-fetched log rows so ``logs()`` can replay them., _seed_int() (+23 more)

### Community 18 - "enrollment_service.py"
Cohesion: 0.13
Nodes (26): generate_enrollment_token(), An enrollment credential (``nxk_``): single-use, short-lived, org-scoped.…, EnrollmentToken, One single-use credential that enrolls (or claims) exactly one node., Whether the row could still be redeemed (not a race-safe check)., EnrollmentTokenCreate, Mint one enrollment token in the caller's active organization., _claim_and_consume() (+18 more)

### Community 19 - "rollback_secret"
Cohesion: 0.15
Nodes (23): create_secret(), delete_secret(), get_secret(), list_secret_versions(), list_secrets(), DbSession, delete, get (+15 more)

### Community 20 - "get_application"
Cohesion: 0.13
Nodes (25): get_application(), get_environment(), _as_worker(), _delivery_chain(), _owner_ctx(), _queue(), _queued_with_recorder(), Regression: the trigger route must re-read the queued row eagerly.… (+17 more)

### Community 21 - "list_containers"
Cohesion: 0.08
Nodes (43): _action_route(), _endpoint(), _decode_frame(), _ev(), get_container(), _like_pattern(), list_container_logs(), list_containers() (+35 more)

### Community 22 - "get_latest_server_metrics"
Cohesion: 0.09
Nodes (32): get_dashboard_summary(), get_latest_server_metrics(), get_server_metrics(), CurrentUser, DbDep, Depends, get, UUID (+24 more)

### Community 23 - "get_settings"
Cohesion: 0.07
Nodes (61): argon2, argon2_exceptions, get_settings(), Return the cached settings singleton., Runtime DSN (application role, RLS enforced) for Celery/script sync paths., sync_database_url(), Unauthorized, create_access_token() (+53 more)

### Community 24 - "Domain Routing — NexusOps"
Cohesion: 0.12
Nodes (17): 10. Wildcards and catch-all, 11. User journey, 12. API surface, permissions, audit, 13. Monitoring tie-in, 1. Scope and current state, 2. Where nginx runs, 3.1 Domain, 3.2 Route (+9 more)

### Community 25 - "monitor_service.py"
Cohesion: 0.14
Nodes (39): MonitorStatus, Monitor, MonitorCheck, One probe. Targets are polymorphic since Phase 4 (domain-model.md §2.6).…, MonitorCreate, Payload for POST /monitors., _active_incident(), _audit() (+31 more)

### Community 26 - "Node & Agent Architecture"
Cohesion: 0.10
Nodes (20): 1. Scope and stance, 3.2 Enrollment v2, 3.3 Token storage & rotation with dual-token grace, 3.4 Revocation semantics — fixing the 401 hot-loop, 3.5 Reconnect / offline states, 3. Agent lifecycle, 6.1 Token scope, 6.2 docker.sock is root-equivalent (+12 more)

### Community 27 - "test_agent_backoff.py"
Cohesion: 0.14
Nodes (22): agent_fixture(), _install_sleep(), fake_sleep(), _load_agent(), _patch_host(), Any, fixture, MonkeyPatch (+14 more)

### Community 28 - "SimulatedDeploymentRunner"
Cohesion: 0.21
Nodes (26): _pace(), Staged docker-style simulation used by v1 deployments., Deterministic per-line delay between 0.05s and 0.35s., Canonical step identifiers stored on :class:`DeploymentStep` rows., SimulatedDeploymentRunner, StepName, _collect(), _ctx() (+18 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.09
Nodes (29): build_heartbeat(), collect_container_stats(), collect_containers(), _container_ports(), _container_status(), cpu_percent_since(), disk_stats(), docker_capability() (+21 more)

### Community 30 - "integration/conftest.py"
Cohesion: 0.11
Nodes (27): dispose_engine(), close_redis(), _admin_dsn(), _clean_slate(), client(), _ensure_database(), _migrated_database(), org_db() (+19 more)

### Community 31 - "login"
Cohesion: 0.10
Nodes (43): active_memberships(), The user's memberships in non-suspended organizations, oldest first. Reads only…, System scope bound to *db*, for rows that have no organization. Used by exactly…, system_write_scope(), _audit(), _auth_event_scope(), change_own_password(), count_users() (+35 more)

### Community 32 - "create_host"
Cohesion: 0.14
Nodes (22): _assert_endpoint_allowed(), _assert_name_free(), create_host(), delete_host(), endpoint_scheme(), list_images(), list_networks(), list_volumes() (+14 more)

### Community 33 - "test_rate_limit.py"
Cohesion: 0.18
Nodes (16): RateLimited, _memory_count_and_ttl(), rate_limit(), Fixed-window counter backed by process memory. Returns (count, ttl)., Return a dependency enforcing *limit* requests per window per IP. With…, _clean_memory_windows(), _FakeRequest, fixture (+8 more)

### Community 34 - "docker_hosts.py"
Cohesion: 0.07
Nodes (55): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+47 more)

### Community 35 - "test_ws_hub.py"
Cohesion: 0.14
Nodes (25): _connection(), _drain(), _event_frame(), _fake_sessionmaker(), _FakeSession, hub(), _Org, Any (+17 more)

### Community 36 - "BundleFile"
Cohesion: 0.18
Nodes (16): BundleFile, fingerprint_files(), is_allowed_bundle_path(), One rendered file. The path is allowlisted, the content is bounded., Deterministic fingerprint over the complete rendered tree. Path order is…, Whether *path* is one of the managed files a bundle may write., The two implementations must produce byte-identical fingerprints., A removal-only bundle's id must mean the same thing on both sides. Convergence… (+8 more)

### Community 37 - "search"
Cohesion: 0.16
Nodes (23): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+15 more)

### Community 38 - "publish"
Cohesion: 0.08
Nodes (47): get_redis(), ping(), Shared async Redis client., ActorType, SystemEvent, Revoke a key owned by *owner_id*. Foreign keys look like NotFound (no leak)., revoke_api_key(), _after_commit_publish() (+39 more)

### Community 39 - "list_deliveries"
Cohesion: 0.17
Nodes (22): create_channel(), delete_channel(), get_channel(), list_channels(), list_deliveries(), DbDep, delete, Depends (+14 more)

### Community 40 - "DockerProvider"
Cohesion: 0.08
Nodes (14): ContainerInfo, DockerProvider, Any, datetime, Protocol, List containers visible to the provider., Inspect a single container by id (short ids allowed)., List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``. (+6 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.12
Nodes (36): CheckResult, get_transport(), HTTPMonitorTransport, Deterministic fake checker for ``sim://`` monitors and demo environments.…, Pick the transport matching the monitor URL scheme., Real HTTP(S) probe using httpx with per-monitor settings. Redirects are…, SimulatedTransport, _check() (+28 more)

### Community 42 - "StepFailure"
Cohesion: 0.09
Nodes (24): DeploymentRunner, Exception, Protocol, Raised by a runner when a step fails irrecoverably., Adapter interface implemented by real (future) and simulated runners., Return the ordered step names for this run., StepFailure, 10. Events and WS during runs (+16 more)

### Community 43 - "AuthContext.tsx"
Cohesion: 0.02
Nodes (83): Membership, SearchResult, User, AuthContext, AuthProvider(), AuthState, isOrgSelectionError(), MeResponse (+75 more)

### Community 44 - "schemas/health.py"
Cohesion: 0.18
Nodes (12): liveness(), get, Response, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness(), HealthOut, Health / readiness schemas. (+4 more)

### Community 45 - "test_permissions.py"
Cohesion: 0.17
Nodes (9): _auth_context(), Unit tests for the permission registry, scope matching and RBAC gate., A fake context in the given organization. ``membership_status=None`` models a…, test_api_key_scope_intersects_role_permissions(), test_membership_is_required_for_authority(), test_plain_user_without_permissions_is_denied(), test_superadmin_bypasses_everything(), test_superadmin_owned_api_key_is_limited_to_its_scope() (+1 more)

### Community 46 - "routes.py"
Cohesion: 0.14
Nodes (33): create_route(), delete_route(), disable_route(), _domain_status(), enable_route(), get_route(), list_routes(), AsyncSession (+25 more)

### Community 47 - "test_phase3_nodes.py"
Cohesion: 0.14
Nodes (35): Run the enclosed block with tenant filtering off (maintenance only). ``reason``…, system_scope(), _create_token(), _dispatch(), _enroll(), _enrolled_node(), _load_agent_module(), _mutate_in_system_scope() (+27 more)

### Community 48 - "BadRequest"
Cohesion: 0.08
Nodes (60): BadRequest, UnprocessableEntity, assert_safe_tcp_endpoint(), assert_safe_url(), _is_forbidden_address(), is_simulation_url(), ValueError, _raise_block() (+52 more)

### Community 49 - "NotFound"
Cohesion: 0.11
Nodes (43): NotFound, An encrypted configuration value, scoped to org, project or environment.…, One immutable value of a :class:`Secret` — append-only history. A row is…, Secret, SecretVersion, _actor_type(), create_secret(), delete_secret() (+35 more)

### Community 50 - "roles.py"
Cohesion: 0.11
Nodes (29): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, delete, get (+21 more)

### Community 51 - "DbDep"
Cohesion: 0.17
Nodes (19): create_enrollment_token(), create_server(), DbDep, patch, post, Request, Register a node. Returns the row without an enrollment token — generate one via…, Create a tag or update its colour (idempotent on name). (+11 more)

### Community 52 - "proxy_service.py"
Cohesion: 0.03
Nodes (170): agent_hello(), First contact after enrollment: persist static host facts, negotiate cadence.…, apply_node_proxy_config(), node_route_targets(), Containers on this node that a route can point at, with usable ports. Only…, Ask the node to report its live proxy state (queues ``nginx.status``)., Force a re-render and apply of this node's desired configuration. The routine…, refresh_node_proxy_status() (+162 more)

### Community 53 - "_exec"
Cohesion: 0.21
Nodes (11): Phase 2.1 corrective migration: legacy ``environment_type`` classification.…, Every case is classified as documented, ids and ownership intact., An explicit non-DEV classification survives the corrective migration. The…, Insert one legacy environment per case, in two organizations., _seed_typed_environments(), test_corrects_legacy_environment_types(), test_only_dev_defaulted_rows_are_corrected(), _exec() (+3 more)

### Community 54 - "v1/auth.py"
Cohesion: 0.05
Nodes (73): change_password(), _clear_refresh_cookie(), _cookies_secure(), login(), logout(), me(), _optional_actor(), AsyncSession (+65 more)

### Community 55 - "test_agent_nginx_contract.py"
Cohesion: 0.11
Nodes (32): _agent_bundle(), agent_fixture(), _load_agent(), Any, fixture, parametrize, Phase 4 agent contract: nginx capability, port reporting, and bundle…, An unreadable ``/proc`` must never be read as "the port is free". (+24 more)

### Community 56 - "users.py"
Cohesion: 0.13
Nodes (25): create_user(), deactivate_user(), get_user(), list_users(), CurrentUser, DbSessionDep, delete, get (+17 more)

### Community 57 - "alembic"
Cohesion: 0.05
Nodes (15): alembic, downgrade(), rename ``server.*`` permission codenames to ``node.*`` The Node/Server…, _rename_permissions(), upgrade(), Fix pre-existing model/migration drift (surfaced by the new drift check). Two…, downgrade(), _drop_constraint() (+7 more)

### Community 58 - "dispatch_event_frame"
Cohesion: 0.17
Nodes (18): _as_uuid(), _attempt_delivery(), decode_delivery_cursor(), dispatch_event_frame(), _send(), encode_delivery_cursor(), list_deliveries(), _now() (+10 more)

### Community 59 - "helpers.py"
Cohesion: 0.06
Nodes (60): bearer(), cookie_attributes(), login_account(), login_headers(), Any, AsyncClient, Response, Pure helpers for journey tests: payloads, auth shortcuts, cookie parsing. (+52 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "v1/deployments.py"
Cohesion: 0.09
Nodes (45): _attribute_step_idx(), cancel_deployment(), _emails_for(), get_deployment(), list_application_deployments(), list_deployment_logs(), _list_deployments(), _parse_sort() (+37 more)

### Community 62 - "test_error_logging.py"
Cohesion: 0.22
Nodes (4): Regression: the catch-all 500 handler must not log raw exception text.…, _SpyLogger, test_unhandled_exception_handler_logs_class_not_message(), fastapi_testclient

### Community 63 - "dns_verifier.py"
Cohesion: 0.16
Nodes (16): apex_of(), The name a wildcard Domain is anchored at (``*.example.com`` →…, The exact TXT owner name a user must publish at their provider., verification_record_name(), _discover_nameservers(), _normalise_ns(), observe(), public_addresses() (+8 more)

### Community 64 - "test_phase2_environments.py"
Cohesion: 0.18
Nodes (22): _environment(), _project(), parametrize, Phase 2: project-scoped environments, config layering, and their isolation. The…, Uniqueness is ``(project_id, slug)`` — not instance-wide., The update path is validated too (the pre-Phase-2 gap)., Knowing an environment UUID is not access: the project link must hold., Another tenant cannot reach the project, its environments, or its detail. (+14 more)

### Community 65 - "route_service.py"
Cohesion: 0.09
Nodes (53): MonitorTargetType, Last nginx apply outcome for a route, as reported by its node's agent.…, What a monitor observes (domain-model.md §2.6, polymorphic targets). ``URL`` is…, RouteConfigState, One hostname+path served from one container on one node. Relationship rules the…, Route, mark_removal_requested(), _mark_route_stale() (+45 more)

### Community 66 - "test_schema_redaction.py"
Cohesion: 0.18
Nodes (17): is_sensitive_header(), mask_sensitive_headers(), True when *name* looks like it carries a credential (Authorization etc.)., Return a copy of *headers* with sensitive values replaced by a mask., mask_target(), Human-readable masked target safe to expose over the API. For webhook families…, _monitor_out(), Outbound-schema redaction: monitor probe credentials and webhook targets.… (+9 more)

### Community 67 - "AuthContext"
Cohesion: 0.05
Nodes (89): AuthContext, get_current_user(), _load_organization(), _load_permissions(), permission_dep(), Any, Organization, FastAPI dependencies: database session, authenticated tenant context, RBAC… (+81 more)

### Community 68 - "digest_of"
Cohesion: 0.10
Nodes (21): digest_of(), Short server-verifiable digest used for change detection display. HMAC-SHA256…, test_digest_length_and_determinism(), 10. Status/expiry tracking and monitor tie-in, 12. Audit and events, 13. Non-goals, 1. Scope and current state, 2. Certificate entity (+13 more)

### Community 69 - "package.json"
Cohesion: 0.13
Nodes (15): name, private, type, version, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom (+7 more)

### Community 70 - "test_event_registry.py"
Cohesion: 0.21
Nodes (8): event_type_catalogue(), is_known_event_type(), Canonical registry of system-event types. Single source of truth shared by…, Return True when *event_type* is part of the canonical registry., Serialise the registry for the ``/events/types`` endpoint., Registry coherence: schema-advertised event types must equal the canonical…, test_catalogue_serialises_every_entry(), test_known_event_lookup()

### Community 71 - "test_secrets.py"
Cohesion: 0.11
Nodes (26): Exception, A ``${secret:KEY}`` reference could not be resolved. Fail-closed. Carries…, One successfully resolved reference: metadata for audit, no value., Resolve every ``${secret:KEY}`` reference an environment's config names.…, resolve_secrets_for_environment(), SecretReference, SecretResolutionError, _create() (+18 more)

### Community 72 - "test_nginx_renderer.py"
Cohesion: 0.15
Nodes (32): NginxProvider, The only production provider in Phase 4., Where a route's fragment lands, so the service can name it in events., provider(), fixture, parametrize, The renderer: determinism, the injection boundary, and the Phase 4 HTTP-only…, route() (+24 more)

### Community 73 - "domain_service.py"
Cohesion: 0.09
Nodes (46): DomainStatus, Ownership-verification lifecycle of a Domain (domain-routing.md §4). ``STALE``…, Domain, One DNS name an organization is proving it controls. ``name`` is canonical (see…, DomainCreate, Payload for ``POST /domains``. ``name`` is passed through the canonicaliser; it…, What the lifecycle should do with an observation., VerificationDecision (+38 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "monitors.py"
Cohesion: 0.14
Nodes (36): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+28 more)

### Community 76 - "PageParams"
Cohesion: 0.11
Nodes (36): list_alerts(), Depends, Unread alerts first, then newest first., list_applications(), list_environments(), list_projects(), Depends, get (+28 more)

### Community 77 - "domains.py"
Cohesion: 0.15
Nodes (32): create_domain(), delete_domain(), _enqueue_verification(), get_domain(), list_domain_routes(), list_domains(), _project_names(), alias (+24 more)

### Community 78 - "incidents.py"
Cohesion: 0.20
Nodes (24): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+16 more)

### Community 79 - "test_phase2_secrets.py"
Cohesion: 0.20
Nodes (20): _env(), _project(), Phase 2 secrets: layered scope, immutable versions, rollback, isolation. Two…, Two racing rotations must both be kept and never share a version number., Another tenant cannot read, rotate, roll back or even enumerate the secret., The documented example: same key at three scopes; most specific wins., A ref declared in the project base config resolves for its environments., _resolved() (+12 more)

### Community 80 - "RolesPage.tsx"
Cohesion: 0.11
Nodes (15): Role, RolesPage, describeError(), GROUP_STYLE, LEGEND_STYLE, OPTION_STYLE, PermissionSpec, roleAllows() (+7 more)

### Community 81 - "test_schemas_server.py"
Cohesion: 0.21
Nodes (22): Payload for registering a server., Partial update. ``tags`` replaces the full set when provided., ServerCreate, ServerUpdate, _base(), parametrize, Unit tests for app.schemas.server (validation only, no I/O)., test_empty_ip_is_allowed_but_whitespace_collapses() (+14 more)

### Community 82 - "canonicalize_name"
Cohesion: 0.12
Nodes (32): canonicalize_name(), canonicalize_path(), _check_labels(), _check_not_ip(), hostname_is_covered(), _idna(), InvalidName, is_valid_path() (+24 more)

### Community 83 - "tests/conftest.py"
Cohesion: 0.12
Nodes (13): alembic_autogenerate, alembic_migration, configure_test_env(), Test bootstrap: pin every cached setting BEFORE the first ``app`` import. The…, KEY=VALUE pairs from the repo .env (first definition wins); never logged., Export the exact settings the app caches; host values cannot leak through., _read_dot_env(), Model / migration drift: the schema in the database must match the models.… (+5 more)

### Community 84 - "UUID"
Cohesion: 0.19
Nodes (14): _detail(), get_server(), list_tags(), node_proxy_status(), AsyncSession, get, ReadCtx, UUID (+6 more)

### Community 85 - "create_user"
Cohesion: 0.07
Nodes (50): list_sessions(), CurrentUser, DbSessionDep, delete, get, Request, UUID, Active sessions of this organization's members. Defaults to the caller's own;… (+42 more)

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "Conflict"
Cohesion: 0.06
Nodes (64): agent_heartbeat(), claim_operation(), _presented_token(), DbDep, post, Request, Response, UUID (+56 more)

### Community 88 - "log_service.py"
Cohesion: 0.12
Nodes (29): container_log_channel(), Canonical Redis pub/sub channel names shared by API, workers and WS hub., LogLevel, LogSource, LogEntry, LogLine, One parsed log record from a container log stream., _persist_log_lines() (+21 more)

### Community 89 - "Settings"
Cohesion: 0.14
Nodes (6): field_validator, model_validator, Username from :attr:`database_url`, or ``None`` if it is unparseable., Validated application settings (loaded from environment / .env)., Settings, BaseSettings

### Community 90 - "domain_routing.py"
Cohesion: 0.14
Nodes (25): The honest state of a route that left the desired tree but is not gone. One…, removal_requested_detail(), _affected_node_ids(), _announce(), _apply_for_node(), _audit_action(), datetime, task (+17 more)

### Community 91 - "validate_config"
Cohesion: 0.08
Nodes (31): field_validator, collect_secret_refs(), walk(), ConfigValidationError, effective_config(), merge_config(), Any, ValueError (+23 more)

### Community 92 - "create_alert"
Cohesion: 0.13
Nodes (21): mark_all_read(), mark_read(), CurrentUser, DbDep, get, post, UUID, Mark every unread alert read; returns how many rows changed. (+13 more)

### Community 93 - "hub.py"
Cohesion: 0.03
Nodes (113): asyncio, The active organization, or raise if this request has none., Health probes: liveness (always cheap) and readiness (checks dependencies).…, get_engine(), get_sessionmaker(), async_sessionmaker, AsyncEngine, AsyncSession (+105 more)

### Community 94 - "test_phase21_secret_version_integrity.py"
Cohesion: 0.18
Nodes (18): _app_role_dsn(), _owner_dsn(), _probe(), Phase 2.1 — ``secret_versions`` is append-only in the **database**, not just in…, Immutability is a database guarantee, not merely a missing code path. The owner…, The legitimate append paths keep working under the guard., The documented deletion policy: purging a Secret cascades its history., RLS is preserved: another tenant cannot see a version row, even by id. (+10 more)

### Community 95 - "StepLine"
Cohesion: 0.24
Nodes (7): _commit_short(), Stream output lines for *step_name*; raise StepFailure to fail it., Everything a runner needs to execute one deployment., One streamed output line for a step., RunContext, _slug(), StepLine

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
Cohesion: 0.09
Nodes (33): _is_sensitive_key(), Return a copy of *data* with sensitive values replaced, at any depth. Two…, Substring match on a normalised key so header-style names are caught too.…, redact_mapping(), parametrize, Unit tests for app.core.logging redaction (pure functions only)., No sensitive key name involved: the PEM armor is the only signal., Lists of dicts holding further lists — the shape an agent report takes. (+25 more)

### Community 101 - "README.md - NexusOps overview"
Cohesion: 0.30
Nodes (14): docker-compose.dev.yml - dev overlay, docker-compose.docker-sock.yml - docker socket override, docker-compose.yml - full stack definition, docs/agent.md - agent guide, docs/api.md - API guide, Append-only audit log (Postgres BEFORE UPDATE OR DELETE trigger), docs/architecture.md - system architecture, docs/deployment.md - deployment and operations guide (+6 more)

### Community 102 - "_database_url"
Cohesion: 0.33
Nodes (6): _database_url(), Migrations run as the table **owner**, never as the application role. The owner…, Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online()

### Community 103 - "_mutate_in_system_scope"
Cohesion: 0.15
Nodes (19): Keep every routed node's live configuration matching the desired bundle. One…, sweep_routes(), _live_operations(), _mutate_in_system_scope(), Offline during a transfer: unresolved, bounded, and never a false success., A detected difference is repaired unattended — and bounded while it isn't., Disable the last route on an offline node, then let the reconciler converge., Delete the last route on an offline node: the node's own state remembers it. (+11 more)

### Community 104 - "test_migration_phase4.py"
Cohesion: 0.16
Nodes (22): _rows(), _columns(), _integrity_error(), _migrate_from_phase3(), Statement, Phase 4 migration (`f4a5b6c7d8e9`) against a real Phase 3 database. Phase 4 is…, The polymorphic shape is enforced in both directions., The anti-takeover rule is a partial unique index, not a convention. (+14 more)

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
Nodes (29): ContainerStats, Exception, Build a compact, secret-free description of a provider failure. Only the…, Point-in-time resource usage snapshot., sanitize_error(), _as_float(), _compute_stats(), _cpu_percent() (+21 more)

### Community 109 - "Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)"
Cohesion: 0.25
Nodes (9): API keys (X-API-Key, nxo_..., scope intersection), First boot sequence (api entrypoint migrates, compose never seeds), Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test), Makefile workflows (up/test/lint/typecheck/migrate/seed), HIGH finding: API-key scope bypass for superadmin-owned keys (fixed: scope intersection first), Security audit 2026-09 (26 raw findings -> 20 confirmed, all fixed), HIGH finding: known seed superadmin + API key backdoor (fixed: NEXUSOPS_ALLOW_SEED opt-in, one-time password), Threat model (edge attacker, malicious agent, curious operator, leaked token, SSRF) (+1 more)

### Community 110 - "ScopedSession"
Cohesion: 0.19
Nodes (3): A session that enters its tenancy scope around each operation. A fixture cannot…, ScopedSession, 3. The session guard (the mechanical layer)

### Community 111 - "organization_service.py"
Cohesion: 0.13
Nodes (33): MembershipStatus, OrganizationStatus, Membership, Organization, A tenant. Every organization-owned row points here via ``org_id``., Binds a user to an organization with a role *inside that organization*.…, _bootstrap_organization(), Organization (+25 more)

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
Cohesion: 0.03
Nodes (109): AgentContainerPortIn, AgentEnrollOut, AgentHeartbeatOut, AgentHelloOut, AgentTokenRotation, CapabilityReport, Agent-facing schemas. Payloads are data only — never executed. Wire protocol v2…, Tells the agent how often to report and what protocol it negotiated. (+101 more)

### Community 116 - "test_tenancy_allowlist.py"
Cohesion: 0.20
Nodes (14): AST, _actual_callers(), _calls_system_scope(), _module_path(), Path, The system-scope allowlist is the only fence around the tenancy carve-out.…, Every module that could open a system scope: ``app/`` plus the scripts., No module may lift tenant isolation without being named in the list. (+6 more)

### Community 117 - "_alembic_config"
Cohesion: 0.15
Nodes (15): The correction is part of ``head`` and adds no extra Alembic head., test_corrective_migration_is_reachable_from_head(), _alembic_config(), _at_revision(), _migration_dsn(), Run one Alembic direction against ``database`` through the app's settings path.…, Move ``database`` *back* to ``revision``. The same code path a deployment uses…, Phase 2 adds one migration; heads must not fork. (+7 more)

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

### Community 122 - "test_tenant_isolation.py"
Cohesion: 0.05
Nodes (61): error_of(), Unwrap an API error envelope., A valid POST /servers body with per-test overrides., server_payload(), test_token_cannot_claim_a_foreign_tenants_node(), test_v1_heartbeat_keeps_the_204_contract(), Regression: a superadmin-owned key is still limited to its scope list. The…, test_scoped_api_key_cannot_exceed_its_grant() (+53 more)

### Community 123 - "test_migration_phase2.py"
Cohesion: 0.13
Nodes (22): alembic_config, alembic_script, Phase 2 migration (`b2c3d4e5f6a7`) against realistic legacy data. The promotion…, Upgrade ``database`` to ``revision``., The pre-Phase-2 shapes: application-scoped environments, per-app dupes., A fresh database reaches the same shape the models describe., _run_migration(), _seed_legacy_data() (+14 more)

### Community 124 - "middleware.py"
Cohesion: 0.15
Nodes (14): ASGIApp, AccessLogMiddleware, Request, Response, HTTP middleware: request ids, security headers, structured access logs., Baseline hardening headers on every API response., RequestIDMiddleware, SecurityHeadersMiddleware (+6 more)

### Community 125 - "OperationError"
Cohesion: 0.18
Nodes (15): _demux_docker_stream(), _docker_error(), execute_operation(), OperationError, Exception, A stable, sanitized failure contract for the control plane., Re-validate the operation's parameters locally, against a closed shape., Decode docker's 8-byte-header frame stream, or ``None`` if not framed. (+7 more)

### Community 126 - "record"
Cohesion: 0.14
Nodes (21): cancel_operation(), create_operation(), get_operation(), list_operations(), DbDep, Depends, get, post (+13 more)

### Community 127 - "test_phase4_routing.py"
Cohesion: 0.10
Nodes (26): _create_domain(), _dns_stub(), _fake_observe(), fixture, MonkeyPatch, parametrize, Phase 4 through the real HTTP surface, workers and agent contract. The journey…, Stand in for authoritative DNS in every test in this module. (+18 more)

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

### Community 157 - "Secrets Architecture"
Cohesion: 0.13
Nodes (15): 10. Resolution flow at deploy time, 2.1 Resolution runs inside org scope, 2.2 Migration mapping (applied by `b2c3d4e5f6a7`), 2. Scope model (org / project / environment layering) — **shipped**, 3.1 What this fixed, 3. SecretVersion — append-only history (**shipped in Phase 2**), 4.1 Audit event at resolution time, 4. Resolution authorization (+7 more)

### Community 158 - "test_schemas_agent.py"
Cohesion: 0.22
Nodes (21): AgentContainerIn, AgentHeartbeatIn, Observed container state reported by an agent., Periodic metrics + observed containers from an enrolled agent. Network counters…, _container(), _heartbeat(), parametrize, Unit tests for agent-facing schemas (heartbeat + container payloads). (+13 more)

### Community 159 - "Hub"
Cohesion: 0.13
Nodes (18): _close_socket(), Connection, _frame_org(), Hub, _params_key(), _parse_payload(), Any, WebSocket (+10 more)

### Community 160 - "main"
Cohesion: 0.11
Nodes (19): build_capabilities(), _build_hello_payload(), _enroll(), _interruptible_sleep(), main(), memory_total_mb(), os_info(), persist_token() (+11 more)

### Community 161 - "monitor_transport.py"
Cohesion: 0.09
Nodes (24): assert_safe_url_async(), Async wrapper around :func:`assert_safe_url`; DNS runs off the loop., CheckOutcome, coerce_headers(), _decode(), MonitorTransport, Any, BaseException (+16 more)

### Community 162 - "decide"
Cohesion: 0.23
Nodes (18): decide(), matches_token(), Constant-time comparison of the observed TXT values against the token. TXT…, Turn one observation into the verification outcome — pure, no I/O.…, observation(), parametrize, The verification decision: every outcome, without a network. ``decide`` is…, test_a_sweep_invalidates_a_changed_delegation_even_with_the_token() (+10 more)

### Community 163 - "incident_service.py"
Cohesion: 0.20
Nodes (26): IncidentEventKind, IncidentSeverity, IncidentStatus, Incident, IncidentEvent, acknowledge(), _add_event(), add_note() (+18 more)

### Community 164 - "AgentClient"
Cohesion: 0.15
Nodes (8): AgentClient, _docker_raw(), A verifying TLS context. Verification is never disabled. A private/self-hosted…, Refuse to send credentials over plain HTTP to a non-loopback server. The…, One raw Docker API call; returns ``(status, body_bytes)``., _tls_context(), _UnixHTTPConnection, SSLContext

### Community 165 - "client_ip"
Cohesion: 0.31
Nodes (9): client_ip(), _enforce(), node_rate_limit(), _dependency(), Request, _dependency(), Return a dependency keyed on the **authenticated node**, not the IP. A fleet…, Best-effort client IP; honours X-Forwarded-For from trusted proxies. Delegates… (+1 more)

### Community 166 - "nginx.py"
Cohesion: 0.12
Nodes (26): _header_lines(), ValueError, _quote(), _rate_zone(), NginxProvider — a pure, deterministic renderer plus the two op wrappers.…, Validate the route's headers and split them by destination., Wrap an already-validated value in quotes for a template slot. Values reaching…, The ``limit_req_zone`` declaration for a rate-limited route. (+18 more)

### Community 167 - "resolve_auth"
Cohesion: 0.08
Nodes (31): _attach_organization(), get_identity(), get_optional_user(), membership_for_org(), _org_id_from_header(), AsyncSession, DbSessionDep, Membership (+23 more)

### Community 168 - "2. The Node concept"
Cohesion: 0.25
Nodes (7): Alias for :attr:`extra`, so the API can expose open-ended agent facts. The…, 2.3 Infrastructure — Nodes, 2.1 Current shape (real), 2.2 Changes for the target model, 2.3 Capabilities (implemented, Phase 3), 2.4 DockerEndpoint — the 0..1 relation, 2. The Node concept

### Community 169 - "test_a_late_result_for_an_expired_operation_cannot_fail_a_live_route"
Cohesion: 0.13
Nodes (23): _agent_result_body(), _audits(), _claim(), _event_types(), The same delivery twice: one apply, one set of events, one audit row., A report that contradicts what already happened is ignored, not applied., A report that arrives after its operation expired changes nothing at all., The result body the agent sends for one operation it claimed. Shared by the… (+15 more)

### Community 170 - "test_agent_contract.py"
Cohesion: 0.20
Nodes (15): agent_fixture(), _load_agent(), _patch_stats(), Any, fixture, MonkeyPatch, Contract tests: the shipped agent's payloads must satisfy the ingest schemas.…, One-shot docker stats reduce to cpu/mem/limit fields the schema accepts, with… (+7 more)

### Community 171 - "20261009_1000-c3d4e5f6a7b8_enforce_secret_version_integrity.py"
Cohesion: 0.48
Nodes (6): _clear_app_role_guc(), downgrade(), Phase 2.1 — enforce append-only ``secret_versions`` in the database. Phase 2…, Publish the app-role name to the migration GUC the revoke block reads., _set_app_role_in_guc(), upgrade()

### Community 172 - "AppError"
Cohesion: 0.14
Nodes (22): AppError, Exception, Base class for expected, client-facing errors., _authenticate_api_key(), _authenticate_jwt(), _bind_organization(), _entity_exists(), _load_permissions() (+14 more)

### Community 173 - "2. Entities"
Cohesion: 0.25
Nodes (8): 2.1.1 ApiKey org binding detail, 2.2.1 Environment promotion detail — **shipped in Phase 2**, 2.2 Delivery (existing models, extended), 2.4 Routing & TLS (new subsystem), 2.5 Secrets (re-scoped — **shipped in Phase 2**), 2.6 Observability (existing, org-scoped via parents), 2.7 Backups, connections, billing (new subsystems, design-only in early phases), 2. Entities

### Community 174 - "apikeys.py"
Cohesion: 0.16
Nodes (18): create_api_key(), list_api_keys(), CurrentUser, DbSessionDep, delete, get, post, Request (+10 more)

### Community 175 - "scope_matches"
Cohesion: 0.25
Nodes (7): Check an API-key scope list against a required permission. Supports exact match…, scope_matches(), parametrize, test_scope_matches_truth_table(), 1. Principles (already true in the codebase, kept), 5. API keys, 2.1 Identity & tenancy (new)

### Community 176 - "Platform Security Model — NexusOps"
Cohesion: 0.10
Nodes (20): make(), 10.1 Node revocation playbook (compromised node / leaked agent token), 10.2 Key compromise playbook, 10. Incident response, 1.1 Real vs simulated today (do not mistake one for the other), 1. Scope, stance, and simulation honesty, 2. Assets, 3. Trust boundaries (+12 more)

### Community 177 - "ContainerListPage.test.tsx"
Cohesion: 0.29
Nodes (3): ApiError, server, serversPage

### Community 178 - "network_rates"
Cohesion: 0.33
Nodes (6): build_facts(), network_rates(), network_total_bytes(), Sum rx/tx bytes over non-loopback interfaces from /proc/net/dev., Return (rx_kb_s, tx_kb_s) or ``(None, None)`` when not measurable., Open-ended host facts, stored in the node's flexible JSONB blob. Deliberately…

### Community 179 - "_node_proxy_state"
Cohesion: 0.16
Nodes (21): _converged_node_with_a_route(), _hello_elsewhere(), _mark_reconcile_required_elsewhere(), _node_proxy_state(), _node_session(), _pause_render(), gated(), One worker unit of work: a fresh session, its org scope, and its node. (+13 more)

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
Cohesion: 0.40
Nodes (5): 8.1 Binding rules, 8.2 Certificate selection rule (this doc owns it) — **Phase 5 target design**, 8.3 Re-render triggers, 8.5 How deployments hook routing (post-deploy route sync), 8. Upstream binding and re-render triggers

### Community 184 - "create_api_key"
Cohesion: 0.22
Nodes (11): create_api_key(), list_api_keys(), AsyncSession, Request, UUID, Live (non-revoked) keys owned by *owner_id*, newest first., Revoke every live key of a user (used on deactivation). Returns count., Validate + normalise scopes; returns the deduplicated list. Accepts exact… (+3 more)

### Community 185 - "update_channel"
Cohesion: 0.23
Nodes (17): EmailConfig, _audit(), create_channel(), decrypt_channel_config(), delete_channel(), encrypt_config(), _normalize_events(), Any (+9 more)

### Community 186 - "maintenance.py"
Cohesion: 0.10
Nodes (30): dispatcher_loop(), Send every due PENDING / retryable-FAILED delivery. Returns count attempted. A…, Consume ``nx:events`` and sweep due retries forever. Runs as a lifespan task., retry_due_deliveries(), aggregate_metrics(), _run(), _collect_logs(), expire_operations() (+22 more)

### Community 187 - "permissions_for_role"
Cohesion: 0.40
Nodes (5): effective_permissions(), permissions_for_role(), User, Sorted permission codenames a role grants; ``*`` expands to the registry.…, Instance-level permissions for a user (legacy default-role view). Deliberately…

### Community 188 - "instant_pacing"
Cohesion: 0.40
Nodes (4): instant_pacing(), fixture, MonkeyPatch, Remove the per-line sleeps; pacing bounds are asserted separately.

### Community 189 - "phase3.spec.ts"
Cohesion: 0.15
Nodes (10): frontend_e2e_fixtures_expect, AGENT, NodeDetail, OperationRow, REPO_ROOT, ref_node_child_process, ref_node_fs, ref_node_os (+2 more)

### Community 190 - "_heartbeat"
Cohesion: 0.25
Nodes (11): _container_id(), _create_node(), _heartbeat(), heartbeat_payload(), test_a_container_on_another_node_is_refused(), test_a_container_without_published_ports_offers_nothing(), test_a_stopped_container_cannot_be_enabled(), test_an_unchanged_desired_state_does_not_re_queue_an_apply() (+3 more)

### Community 191 - "Path"
Cohesion: 0.12
Nodes (15): Path, An unloadable CA file must error, never silently fall back to no verify., A throwaway key + self-signed cert for ``localhost`` (real handshakes)., A one-shot HTTPS server; records a failed handshake instead of crashing., A real handshake against a self-signed server must fail verification., Trusting that same cert as a CA lets the identical handshake through., A link-local URL over plain HTTP must fail before any request or write., _self_signed_cert() (+7 more)

### Community 192 - "20261010_1200-f4a5b6c7d8e9_phase4_domains_and_routes.py"
Cohesion: 0.31
Nodes (9): downgrade(), _drop_tenant_policies(), _grant(), _in_list(), Phase 4 — domains, routes and the routing schema. Adds, in one migration with a…, Grant the app role on *table*; the migration role GUC carries the name. The…, The two-policy shape every tenant table uses: tenant + system scope., _tenant_policies() (+1 more)

### Community 193 - "container.py"
Cohesion: 0.15
Nodes (18): _container_out(), Serialize one row; env values never leave the database (keys only)., ContainerDetailOut, ContainerOut, ContainerRemoveOut, host_ref(), HostRef, LogEntryOut (+10 more)

### Community 194 - "sweep_session"
Cohesion: 0.15
Nodes (19): _candidates(), _run(), org_session(), Any, UUID, Yield a short-lived session; commit on success, rollback on error., A task session inside the **system** scope — for work that spans tenants. The…, A task session bound to exactly one organization — for per-tenant work. (+11 more)

### Community 195 - "v1/channels.py"
Cohesion: 0.17
Nodes (16): Notification channel endpoints. Config is write-only; never echoed back., # NOTE: /deliveries is declared before /{channel_id} so the literal wins., ChannelType, DeliveryStatus, ChannelBase, ChannelCreate, ChannelOut, ChannelUpdate (+8 more)

### Community 196 - "RouteHeader"
Cohesion: 0.10
Nodes (12): field_validator, model_validator, RateLimit, One header a route adds. ``target`` says where it lands., One route's request-rate ceiling (rendered as a ``limit_req_zone``)., A fixed host redirect. Phase 4 cannot express a scheme change here. There is…, RouteHeader, RouteRedirect (+4 more)

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
Cohesion: 0.38
Nodes (4): computed_field, Whether the node has reported capabilities at all (v2 hello)., Server as listed in collections. Never exposes the agent token hash., ServerOut

### Community 201 - "_create_monitor"
Cohesion: 0.33
Nodes (6): _create_monitor(), Regression: probe headers and URL query credentials never leave the API. Probe…, A monitor's checks, incidents and timeline all live in its organization, so the…, test_check_now_endpoint_runs_immediately(), test_down_then_recover_lifecycle(), test_monitor_responses_mask_probe_credentials()

### Community 202 - "run_async"
Cohesion: 0.15
Nodes (18): task, Flag silent servers OFFLINE, recover returning ones. Safe to overlap., sweep_servers(), _run(), T, Run *coroutine* on a dedicated event loop (Celery workers are sync). The loop…, run_async(), _drained() (+10 more)

### Community 203 - "NginxBundle"
Cohesion: 0.14
Nodes (9): Any, Params for the whitelisted ``nginx.apply`` operation., ProxyProvider, Any, Protocol, What ``app.services.proxy_service`` is allowed to assume about a provider. The…, NginxBundle, The desired configuration for one node, as data. (+1 more)

### Community 205 - "Path"
Cohesion: 0.15
Nodes (18): _bootstrap_fixture(), Path, Stage bootstrap's real layout: the system config lives *outside* the tree. This…, The one write outside the tree: the includes land, and it still validates., Point the agent's managed tree at a throwaway directory., What the control plane renders when a node must stop serving its routes., The whole point: the fragment is gone from disk *and* the node agrees., Defence in depth: the reader does not depend on the writer's mkdir. (+10 more)

### Community 206 - "pytest"
Cohesion: 0.18
Nodes (14): _enrolled(), _heartbeat(), Agent ingest pipeline: hello, heartbeat, staleness transitions, events., A container absent from a later heartbeat is gone from the daemon., A payload at the agent's cap may be truncated — absence proves nothing., test_heartbeat_at_container_cap_skips_reconciliation(), test_heartbeat_removes_vanished_containers(), test_heartbeat_updates_status_metrics_and_containers() (+6 more)

### Community 207 - "register_exception_handlers"
Cohesion: 0.24
Nodes (9): _error_payload(), Any, FastAPI, Request, register_exception_handlers(), handle_app_error(), handle_http_exception(), handle_unexpected() (+1 more)

### Community 208 - "_live_bundle_id"
Cohesion: 0.20
Nodes (10): _allowed_bundle_path(), _live_bundle_id(), _live_files(), The bundle fingerprint — byte-identical to the control plane's algorithm.…, Read the live managed tree, or ``None`` when it does not exist yet., Fingerprint of the configuration tree currently on disk., Independently validate a bundle. Anything unexpected is refused., _template_version_of() (+2 more)

### Community 209 - "Multi-Tenancy Architecture"
Cohesion: 0.18
Nodes (10): Whether the runtime connection is the RLS-enforced application role. False…, 10. Migration (Phase 1), 1. Tenancy invariants, 2.1 Org creation — v1 decision, 2. Org resolution on every request, 4. Background jobs, 6. Agents, 8. What stays global (+2 more)

### Community 211 - "monitoring.py"
Cohesion: 0.22
Nodes (7): Celery application: periodic cadences live here, dynamic work is claimed…, task, Monitor dispatch: claim due monitors atomically, run their checks., Claim up to CLAIM_BATCH due monitors and execute each check.…, run_due_monitors(), celery, celery_schedules

### Community 212 - "test_notifications.py"
Cohesion: 0.39
Nodes (8): _channel(), _delivery(), UUID, Notification channel + delivery-log endpoints. Regression coverage for GET…, The same event frame consumed twice queues ONE delivery per channel. Every API…, test_dispatch_frame_is_idempotent_across_workers(), test_list_deliveries_filters_by_channel(), test_list_deliveries_serializes_rows()

### Community 213 - "_FakeAsyncClient"
Cohesion: 0.22
Nodes (3): _FakeAsyncClient, _FakeRequestObj, Scripted httpx.AsyncClient: responses keyed by absolute request URL.

### Community 214 - "test_migration_phase22.py"
Cohesion: 0.28
Nodes (8): UUID, Phase 2.2 — the environment-type correction follows the documented precedence.…, Only the previous migration's ``PROD`` output is corrected. A row already…, Create one legacy (application-scoped) environment per case., Every branch of the slug-first rule, end to end through ``head``., _seed_legacy(), test_correction_preserves_operator_set_values(), test_recognised_slug_alias_wins_over_a_conflicting_name()

### Community 215 - "SecretOut"
Cohesion: 0.25
Nodes (8): Secret metadata — deliberately excludes any value-bearing field., SecretOut, 1.1 Storage and crypto, 1.2 Data model, 1.3 API surface (metadata-only reads), 1.6 Gap list (Phase 2 status), 1. Current state, 9. Leak-path table

### Community 216 - "client_ip.py"
Cohesion: 0.33
Nodes (6): _is_trusted(), _parse_networks(), Client-IP resolution behind chained reverse proxies. The API never takes TCP…, Parse a comma-separated CIDR list; malformed entries are skipped., test_parse_networks_skips_malformed_entries(), _Network

### Community 217 - "_verified_domain"
Cohesion: 0.13
Nodes (22): Observer, Protocol, One bounded look at a name's authoritative TXT record., The seam tests replace with a mock authoritative DNS., TxtObservation, _count_rows_in_system_scope(), The second organization wins; the first stops being the owner., _run_verify() (+14 more)

### Community 218 - "redact_log_event"
Cohesion: 0.29
Nodes (7): Any, structlog processor: scrub one record before anything renders it. The pipeline…, Recursively redact one value of any shape — the depth-agnostic walk. Dicts,…, redact_log_event(), redact_value(), test_the_log_processor_does_not_mutate_the_record_it_was_given(), test_the_log_processor_scrubs_a_private_key_at_any_depth()

### Community 219 - "bundle_summary"
Cohesion: 0.40
Nodes (5): bundle_summary(), Any, Bounded, human-readable bundle metadata for audit rows and UI. Never includes…, Canonical JSON for fingerprint-adjacent comparisons in tests., stable_json()

### Community 220 - "permissions.py"
Cohesion: 0.29
Nodes (5): permission_exists(), PermissionSpec, Permission registry and role matrix. Permissions are *data*: the registry below…, test_permission_exists_helper(), fnmatch

### Community 221 - "create_app"
Cohesion: 0.38
Nodes (6): create_app(), _include_routers(), lifespan(), FastAPI, Mount every domain router. Router variables follow the module contract., Start the WS hub + notification dispatcher; tear them down cleanly.

### Community 222 - "4. DNS ownership verification"
Cohesion: 0.40
Nodes (5): 4.1 The token, 4.2 The check (control-plane side), 4.3 Anti-takeover rules, 4.4 Sequence: add-domain → verified, 4. DNS ownership verification

### Community 223 - "AgentHelloIn"
Cohesion: 0.10
Nodes (18): AgentHelloIn, Any, field_validator, First contact from an agent after enrollment; fills static host facts., Whatever the pre-flight returns must satisfy the hello schema., test_capability_report_shape_is_accepted(), An absent protocol version is the oldest contract, never v2., A capability report forbids unknown keys, so its shape is closed. (+10 more)

### Community 224 - "test_a_transfer_pulls_the_previous_owners_route_from_its_node"
Cohesion: 0.33
Nodes (6): _flip_name_to(), Have *second_org* prove control of *name*, returning the verify outcome., Audit rows for one removal action in the organization being inspected., The old owner's node is told to drop the name, and says when it has., _removal_audits(), test_a_transfer_pulls_the_previous_owners_route_from_its_node()

### Community 225 - "_unique_slug"
Cohesion: 0.33
Nodes (7): _ensure_unique(), Any, ColumnElement, Return ``base`` or the first ``base-N`` variant unique under the parent., Conflict when an ORM row matching *condition* exists. Selects a mapped…, _unique_slug(), InstrumentedAttribute

### Community 226 - "list_enrollment_tokens"
Cohesion: 0.14
Nodes (17): _enrollment_created(), _enrollment_out(), list_enrollment_tokens(), Depends, Enrollment tokens in the active organization, newest first. The response type…, Revoke an unused enrollment token immediately., revoke_enrollment_token(), EnrollmentTokenState (+9 more)

### Community 227 - "_run"
Cohesion: 0.33
Nodes (7): _containers_for(), task, Deterministic smooth value in [base-amplitude, base+amplitude]., Stable per-server container set; one container cycles EXITED occasionally., simulation_tick(), _run(), _wave()

### Community 228 - "test_run_async_publishes_frames_scheduled_by_the_commit_hook"
Cohesion: 0.29
Nodes (5): _FakeDb, Stands in for an ``AsyncSession`` whose only job here is ``sync_session``. A…, The shape of a worker task whose last statement is a commit., test_run_async_publishes_frames_scheduled_by_the_commit_hook(), commit_then_return()

### Community 229 - "20261009_1100-d4e5f6a7b8c9_correct_legacy_environment_types.py"
Cohesion: 0.33
Nodes (3): downgrade(), Phase 2.1 — correct legacy ``environment_type`` classification. The Phase 2…, No-op: the correction is a best-effort classification, not reversible.…

### Community 230 - "20261009_1300-a1b2c3d4e5f6_add_phase3_nodes_and_agent_v2.py"
Cohesion: 0.40
Nodes (4): _grant(), Phase 3 — Nodes & Agent v2 schema. Adds, in one migration with a single head: *…, Grant the app role on *table*; the migration role GUC carries the name. The…, upgrade()

### Community 231 - "sweep_deployments"
Cohesion: 0.33
Nodes (6): task, Execute one queued deployment. The engine owns all state transitions., Re-enqueue deployments the broker lost; fail ones whose worker died.…, run_deployment(), sweep_deployments(), _run()

### Community 232 - "_FakeCtx"
Cohesion: 0.33
Nodes (4): _FakeCtx, Duck-typed stand-in for AuthContext., test_require_permission_raises_forbidden_when_denied(), test_require_permission_returns_ctx_when_allowed()

### Community 233 - "20261004_1200-e7c4a2b9d1f3_add_operations_framework.py"
Cohesion: 0.50
Nodes (3): _quoted_list(), Add the operations framework table (node-agent-architecture.md §5). One tenant-…, upgrade()

### Community 234 - "get_meta"
Cohesion: 0.40
Nodes (5): get_meta(), DbSessionDep, get, Public metadata; identity fields appear only for valid credentials., OptionalUser

### Community 235 - "_is_same_origin"
Cohesion: 0.40
Nodes (5): _is_same_origin(), Browsers always send Origin on WS handshakes, even same-origin ones. When it…, The proxy must forward the Host the browser actually used. A browser sends…, test_same_origin_compares_the_full_authority_including_port(), 7. Known limitations and unresolved issues

### Community 236 - "agent_enroll"
Cohesion: 0.50
Nodes (4): agent_enroll(), Redeem an enrollment token for a unique node credential. Transactional and…, AgentEnrollIn, The first request a brand-new machine makes. ``enrollment_token`` is an…

### Community 237 - "delete_server"
Cohesion: 0.50
Nodes (4): delete_server(), delete, Hard-delete a server and all of its children (cascades)., DeleteCtx

### Community 238 - "DesiredTree"
Cohesion: 0.50
Nodes (3): DesiredTree, What a node *should* be running: the bundle, its routes and its exclusions., 5. ProxyProvider interface

### Community 239 - "5. The Operations framework"
Cohesion: 0.50
Nodes (4): 5.1 Model and lifecycle, 5.2 Whitelisted operation types, 5.3 Result reporting and audit, 5. The Operations framework

### Community 240 - "enrollment_contract"
Cohesion: 0.67
Nodes (3): enrollment_contract(), Any, The minimum response an enrolling agent needs (facts about its new node).

## Knowledge Gaps
- **457 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+452 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2319 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `6. Tooling: reproducible e2e` connect `sweep_session` to `_is_same_origin`, `AppError`, `client.ts`, `Conflict`, `maintenance.py`, `hub.py`, `login`?**
  _High betweenness centrality (0.248) - this node is a cross-community bridge._
- **Why does `useEventStream()` connect `client.ts` to `apiGet`, `sweep_session`, `App.tsx`, `AuthContext.tsx`, `ServerDetailPage.tsx`, `@tanstack/react-query`?**
  _High betweenness centrality (0.247) - this node is a cross-community bridge._
- **Why does `TenancyScopeError` connect `hub.py` to `sweep_session`, `AuthContext`, `publish`, `assert_error_code`, `log_service.py`, `test_tenant_isolation.py`?**
  _High betweenness centrality (0.110) - this node is a cross-community bridge._
- **Are the 94 inferred relationships involving `AuthContext` (e.g. with `TenancyScopeError` and `MembershipStatus`) actually correct?**
  _`AuthContext` has 94 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `APIModel` (e.g. with `OperationSpec` and `test_specs_reject_unknown_params()`) actually correct?**
  _`APIModel` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `Server` (e.g. with `ServerStatus` and `2.3 Infrastructure — Nodes`) actually correct?**
  _`Server` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `apiGet()` (e.g. with `ContainerDetailPage.test.tsx` and `mockApi()`) actually correct?**
  _`apiGet()` has 5 INFERRED edges - model-reasoned connections that need verification._