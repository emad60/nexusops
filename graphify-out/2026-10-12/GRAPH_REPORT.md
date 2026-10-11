# Graph Report - nexusops  (2026-10-12)

## Corpus Check
- 364 files · ~407,491 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: (none) 10, .example 1, .service 1)

## Summary
- 6203 nodes · 18225 edges · 239 communities (219 shown, 20 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1481 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `37b7211e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- apiGet
- test_certificates.py
- ApiKeysPage.tsx
- _proxy_ready_node
- DockerProviderError
- toast.tsx
- resolve_client_ip
- OperationType
- App.tsx
- test_agent_v2.py
- assert_error_code
- ServerDetailPage.tsx
- test_event_registry.py
- client.ts
- project_service.py
- certificate_service.py
- deployment_engine.py
- SimulatedDockerProvider
- enrollment_service.py
- rollback_secret
- test_deployments_simulated.py
- list_containers
- metrics.py
- test_security.py
- Domain Routing — NexusOps
- monitor_service.py
- Node & Agent Architecture
- test_agent_backoff.py
- SimulatedDeploymentRunner
- nexusops_agent.py
- integration/conftest.py
- seed.py
- create_host
- rate_limit.py
- docker_hosts.py
- hub.py
- schemas/proxy.py
- v1/search.py
- models/__init__.py
- v1/channels.py
- DockerProvider
- test_monitor_transport.py
- StepFailure
- AuthContext.tsx
- v1/health.py
- test_permissions.py
- routes.py
- test_phase3_nodes.py
- test_ssrf.py
- NotFound
- roles.py
- record
- proxy_service.py
- pytest
- v1/auth.py
- test_agent_nginx_contract.py
- create_user
- alembic
- notification_service.py
- helpers.py
- compilerOptions
- v1/deployments.py
- test_error_logging.py
- dns_verifier.py
- test_phase2_environments.py
- route_service.py
- test_schema_redaction.py
- enums.py
- decrypt_str
- package.json
- TenancyScopeError
- test_secrets.py
- test_nginx_renderer.py
- domain_service.py
- api service (FastAPI / uvicorn :8000)
- monitors.py
- deps.py
- domains.py
- incident_service.py
- test_phase2_secrets.py
- RolesPage.tsx
- test_schemas_server.py
- canonicalize_name
- tests/conftest.py
- _resolve_tags
- create_user
- devDependencies
- Conflict
- test_certificate_lifecycle.py
- Settings
- _release_competing_claim
- validate_config
- alerts.py
- get_sessionmaker
- test_phase21_secret_version_integrity.py
- Server
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- journey.spec.ts
- Layout.tsx
- redact_mapping
- certificates.py
- organization.py
- _mutate_in_system_scope
- test_migration_phase4.py
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- _rows
- RealDockerProvider
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- ScopedSession
- update_organization
- Phase 5 — HTTPS, Certificates and Private-Key Delivery — Design
- dnsmock.py
- scripts
- APIModel
- test_tenancy_allowlist.py
- _alembic_config
- dependencies
- DeploymentDetailPage.tsx
- generate_secrets.sh
- ControlHandler
- test_tenant_isolation.py
- _exec
- middleware.py
- OperationError
- list_operations
- test_phase4_routing.py
- install.sh
- docker-entrypoint.sh
- integration/__init__.py
- EnvironmentDetailPage.tsx
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
- types.ts
- nexusops-draft.mjs
- NotificationError
- nexusops-challenge.mjs
- Secrets Architecture
- test_schemas_agent.py
- .state
- build_capabilities
- alert_service.py
- decide
- AlertsPage.tsx
- AgentClient
- certificate_lifecycle.py
- nginx.py
- AuthContext
- DashboardPage.tsx
- test_a_late_result_for_an_expired_operation_cannot_fail_a_live_route
- test_agent_contract.py
- StepLine
- docker_real.py
- container.py
- create_api_key
- config.py
- Platform Security Model — NexusOps
- docker_sim.py
- list_sessions
- _node_proxy_state
- router.py
- _nginx_apply
- _nginx_bootstrap
- channel.py
- create_api_key
- 20261012_1200-c8d9e0f1a2b3_phase5_certificate_metadata.py
- run_async
- test_migration_drift.py
- instant_pacing
- phase3.spec.ts
- server.py
- test_migration_phase3.py
- get_settings
- 10. Implementation slices, acceptance criteria, tests, limitations
- test_ws_hub.py
- get_host
- list_docker_hosts
- main.py
- README.md - NexusOps overview
- CertificateStatus
- _validate_resolution
- NotificationChannel
- test_tasks_util.py
- ProxyProvider
- create_docker_host
- ContainerInfo
- test_agent_ingestion.py
- .__init__
- _live_bundle_id
- Multi-Tenancy Architecture
- DockerHostCreate
- test_schemas_search.py
- test_notifications.py
- _FakeAsyncClient
- _provider_inventory
- 9. Renewal, expiration, ownership loss, removal, revocation
- ssrf.py
- _verified_domain
- 1. Scope and current state
- update_channel
- test_app_gating.py
- register_exception_handlers
- .apply_params
- 5. ACME issuance and DNS-01 handling
- InvalidTransition
- 20261009_1100-d4e5f6a7b8c9_correct_legacy_environment_types.py
- DeploymentRunner
- 20260923_1000-c4e2a1f7b9d3_rename_server_codenames_to_node.py
- test_run_async_publishes_frames_scheduled_by_the_commit_hook
- _dns_stub
- redis_down
- lax
- 4. DNS ownership verification
- update_docker_host
- v1/meta.py
- _pace
- 7. Secure delivery of certificate material to authorized nodes
- 9. Phase 6 — Real deployments — **proposal, not implemented**
- redact_log_event

## God Nodes (most connected - your core abstractions)
1. `AuthContext` - 162 edges
2. `APIModel` - 148 edges
3. `Server` - 93 edges
4. `record()` - 93 edges
5. `apiGet()` - 91 edges
6. `NotFound` - 87 edges
7. `get_settings()` - 84 edges
8. `Conflict` - 73 edges
9. `publish()` - 73 edges
10. `assert_error_code()` - 70 edges

## Surprising Connections (you probably didn't know these)
- `2. Org resolution on every request` --references--> `resolve_auth()`  [INFERRED]
  docs/multi-tenancy.md → backend/app/api/deps.py
- `3. Cross-cutting decisions` --references--> `require_permission()`  [INFERRED]
  docs/domain-model.md → backend/app/api/deps.py
- `10. Phase 7 — Teams, grants & custom roles — **proposal, not implemented**` --references--> `require_permission()`  [INFERRED]
  docs/product-roadmap.md → backend/app/api/deps.py
- `7.2 The mechanism: reference-only op + material in the claim response` --references--> `require_server()`  [INFERRED]
  docs/phase5-design.md → backend/app/api/v1/agent.py
- `7.3 Authorization binding` --references--> `require_server()`  [INFERRED]
  docs/phase5-design.md → backend/app/api/v1/agent.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three authentication credential families with centralized permission checks** — docs_api_md_auth, docs_api_md_refresh_rotation, docs_api_md_api_keys, docs_agent_md_enrollment_token, docs_api_md_permission_model [EXTRACTED 1.00]
- **NexusOps compose stack services** — docker_compose_yml_nexusops_stack, docker_compose_yml_postgres_service, docker_compose_yml_redis_service, docker_compose_yml_mailpit_service, docker_compose_yml_api_service, docker_compose_yml_worker_service, docker_compose_yml_scheduler_service, docker_compose_yml_frontend_service, docker_compose_yml_nginx_service [EXTRACTED 1.00]
- **WebSocket real-time fan-out spine** — docs_architecture_md_websocket_hub, docs_api_md_websocket_channels, docker_compose_yml_redis_service, docs_architecture_md_event_bus, readme_react_spa [INFERRED 0.85]

## Communities (239 total, 20 thin omitted)

### Community 0 - "apiGet"
Cohesion: 0.06
Nodes (73): apiDelete(), apiGet(), apiPost(), IncidentEventOut, IncidentDetailPage, useAuth(), errorMessage(), RotateSecretValueForm() (+65 more)

### Community 1 - "test_certificates.py"
Cohesion: 0.08
Nodes (55): _app_role_dsn(), _audits(), _certificate_rows(), _create_domain(), _created_certificate(), _dns_stub(), _events(), _fake_observe() (+47 more)

### Community 2 - "ApiKeysPage.tsx"
Cohesion: 0.09
Nodes (19): ApiKeyOut, ApiKeysPage, ApiKeyCreatedOut, handleCopyKey(), copyText(), describeError(), EMPTY_FORM, GROUP_STYLE (+11 more)

### Community 3 - "_proxy_ready_node"
Cohesion: 0.12
Nodes (33): _create_route(), _drain(), _proxy_ready_node(), A node that stays offline accumulates one op, not one per attempt., The auto-attached monitor stays on the check → incident → notification path., The old owner's node is told to drop the name, and says when it has., The reconciler does not turn a healthy node into a status-poll loop., Claim and answer every pending operation, exactly like the agent would.… (+25 more)

### Community 4 - "DockerProviderError"
Cohesion: 0.13
Nodes (12): clip(), DockerProviderError, Exception, Provider abstraction for docker hosts (real daemon or simulated). Providers are…, A provider operation failed. ``str()`` is safe to show/log., Build a compact, secret-free description of a provider failure. Only the…, Truncate *text* to *limit* characters, stripping control chars., sanitize_error() (+4 more)

### Community 5 - "toast.tsx"
Cohesion: 0.03
Nodes (58): CheckOut, IncidentOut, MonitorOut, SessionInfo, SimulatedChip(), mocks, Toast, TOAST_ARIA_LABEL (+50 more)

### Community 6 - "resolve_client_ip"
Cohesion: 0.17
Nodes (22): _is_trusted(), _parse_networks(), Request, Client-IP resolution behind chained reverse proxies. The API never takes TCP…, Parse a comma-separated CIDR list; malformed entries are skipped., Real client address for *request* per the trust model above., resolve_client_ip(), make_request() (+14 more)

### Community 7 - "OperationType"
Cohesion: 0.11
Nodes (22): OperationType, The whitelist. Nothing outside this enum ships as an exec surface. Each type…, Any, Validate *params* against the type's model and return the stored form.…, validate_params(), Raise a named conflict when routing may not be managed on this node., require_eligible(), MonkeyPatch (+14 more)

### Community 8 - "App.tsx"
Cohesion: 0.04
Nodes (100): EnvironmentOut, Page, ProjectOut, SecretRow, App(), AuditLogPage, ContainerListPage, DeploymentListPage (+92 more)

### Community 9 - "test_agent_v2.py"
Cohesion: 0.06
Nodes (51): agent_fixture(), _load_agent(), Any, fixture, parametrize, Path, Agent protocol v2: honest metrics, capability detection, and the executor. The…, Phase 4 shipped three nginx ops — no file primitive, no command primitive. (+43 more)

### Community 10 - "assert_error_code"
Cohesion: 0.07
Nodes (59): OperationStatus, Lifecycle of one node operation (node-agent-architecture.md §5.1).…, expire_operations(), Expire node operations past their deadline — pending and claimed alike. A…, assert_error_code(), Assert envelope shape + code; returns the inner error object., _dispatch(), _dispatch_body() (+51 more)

### Community 11 - "ServerDetailPage.tsx"
Cohesion: 0.08
Nodes (33): EnrollmentTokenCreated, EnrollmentTokenItem, MetricPoint, OperationItem, OperationType, ServerDetailPage, ServerListPage, ChartSeries (+25 more)

### Community 12 - "test_event_registry.py"
Cohesion: 0.21
Nodes (8): event_type_catalogue(), is_known_event_type(), Canonical registry of system-event types. Single source of truth shared by…, Return True when *event_type* is part of the canonical registry., Serialise the registry for the ``/events/types`` endpoint., Registry coherence: schema-advertised event types must equal the canonical…, test_catalogue_serialises_every_entry(), test_known_event_lookup()

### Community 13 - "client.ts"
Cohesion: 0.05
Nodes (52): API_BASE, ApiError, apiRequest(), buildUrl(), extractError(), getAccessToken(), getActiveOrgId(), onActiveOrgChange() (+44 more)

### Community 14 - "project_service.py"
Cohesion: 0.05
Nodes (110): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+102 more)

### Community 15 - "certificate_service.py"
Cohesion: 0.10
Nodes (37): Certificate, One requested certificate: an identity, its lifecycle view, no material., CertificateKeyAlgorithm, The key type generated for a generation. Fixed in v1; never client-chosen., _actor(), all_generations(), _canonical_identifiers(), CertificateMetadata (+29 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.10
Nodes (58): deployment_log_channel(), Deployment, DeploymentStep, DeploymentStatus, StepStatus, _after_commit_enqueue(), _after_rollback_drop(), _audit_resolution_failed() (+50 more)

### Community 17 - "SimulatedDockerProvider"
Cohesion: 0.13
Nodes (26): ContainerStatus, Implements :class:`DockerProvider` semantics against DB rows., Make a container row visible to this provider instance., Attach already-fetched log rows so ``logs()`` can replay them., SimulatedDockerProvider, _log_entry(), datetime, Unit tests for the simulated docker provider (in-memory rows, no docker). (+18 more)

### Community 18 - "enrollment_service.py"
Cohesion: 0.10
Nodes (33): generate_enrollment_token(), An enrollment credential (``nxk_``): single-use, short-lived, org-scoped.…, Return the active org id or raise; used by services that need it explicitly., require_org(), EnrollmentToken, One single-use credential that enrolls (or claims) exactly one node., Whether the row could still be redeemed (not a race-safe check)., EnrollmentTokenState (+25 more)

### Community 19 - "rollback_secret"
Cohesion: 0.14
Nodes (26): create_secret(), delete_secret(), get_secret(), list_secret_versions(), list_secrets(), DbSession, delete, get (+18 more)

### Community 20 - "test_deployments_simulated.py"
Cohesion: 0.15
Nodes (28): execute_deployment(), Run one deployment to a terminal state. Never raises; safe to re-run., get_environment(), _as_worker(), _delivery_chain(), _owner_ctx(), _queue(), _queued_with_recorder() (+20 more)

### Community 21 - "list_containers"
Cohesion: 0.10
Nodes (35): _action_route(), _endpoint(), _ev(), get_container(), _like_pattern(), list_container_logs(), list_containers(), _load_container() (+27 more)

### Community 22 - "metrics.py"
Cohesion: 0.08
Nodes (37): get_dashboard_summary(), get_latest_server_metrics(), get_server_metrics(), CurrentUser, DbDep, Depends, get, UUID (+29 more)

### Community 23 - "test_security.py"
Cohesion: 0.08
Nodes (43): argon2, argon2_exceptions, Unauthorized, create_access_token(), decode_access_token(), generate_agent_token(), generate_api_key(), password_needs_rehash() (+35 more)

### Community 24 - "Domain Routing — NexusOps"
Cohesion: 0.10
Nodes (21): 10. Wildcards and catch-all, 11. User journey, 12. API surface, permissions, audit, 13. Monitoring tie-in, 2. Where nginx runs, 3.1 Domain, 3.2 Route, 3. Entities (per domain-model.md §2.4) (+13 more)

### Community 25 - "monitor_service.py"
Cohesion: 0.13
Nodes (38): BadRequest, MonitorCheck, Drop the query string so signed tokens never appear in error text., Public alias: redact any query string from a URL before display/persist., strip_query(), _active_incident(), _audit(), claim_due_monitors() (+30 more)

### Community 26 - "Node & Agent Architecture"
Cohesion: 0.08
Nodes (26): install_hint(), The one-liner an operator pastes, without the raw token in argv. The token…, 1. Scope and stance, 3.2 Enrollment v2, 3.3 Token storage & rotation with dual-token grace, 3.4 Revocation semantics — fixing the 401 hot-loop, 3.5 Reconnect / offline states, 3. Agent lifecycle (+18 more)

### Community 27 - "test_agent_backoff.py"
Cohesion: 0.15
Nodes (21): agent_fixture(), _install_sleep(), fake_sleep(), _load_agent(), _patch_host(), Any, fixture, MonkeyPatch (+13 more)

### Community 28 - "SimulatedDeploymentRunner"
Cohesion: 0.25
Nodes (23): Staged docker-style simulation used by v1 deployments., Canonical step identifiers stored on :class:`DeploymentStep` rows., SimulatedDeploymentRunner, StepName, _collect(), _ctx(), Unit tests for SimulatedDeploymentRunner (async generators, no broker)., RESOLVE_CONFIG is planned by the engine, not produced by a runner. (+15 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.08
Nodes (37): build_facts(), build_heartbeat(), _build_hello_payload(), cpu_percent_since(), disk_stats(), _enroll(), _interruptible_sleep(), load1() (+29 more)

### Community 30 - "integration/conftest.py"
Cohesion: 0.12
Nodes (25): _admin_dsn(), _clean_slate(), client(), _ensure_database(), _migrated_database(), org_db(), owner(), AsyncClient (+17 more)

### Community 31 - "seed.py"
Cohesion: 0.05
Nodes (91): active_memberships(), The user's memberships in non-suspended organizations, oldest first. Reads only…, encrypt_str(), generate_refresh_token(), hash_password(), hash_token(), Return ``(raw_token, sha256_hex_hash)``., apply_scope_to_session() (+83 more)

### Community 32 - "create_host"
Cohesion: 0.22
Nodes (15): _assert_endpoint_allowed(), _assert_name_free(), create_host(), endpoint_scheme(), ping_host(), AsyncSession, Request, UUID (+7 more)

### Community 33 - "rate_limit.py"
Cohesion: 0.17
Nodes (20): RateLimited, _enforce(), _memory_count_and_ttl(), node_rate_limit(), _dependency(), Request, rate_limit(), _dependency() (+12 more)

### Community 34 - "docker_hosts.py"
Cohesion: 0.27
Nodes (12): Docker host API: CRUD, ping and provider-backed inventory reads. Permission…, DockerHostPingOut, DockerImageOut, DockerNetworkOut, DockerVolumeOut, image_out(), network_out(), Any (+4 more)

### Community 35 - "hub.py"
Cohesion: 0.08
Nodes (40): membership_for_org(), Membership, The user's active membership in *org_id*, if any. This single indexed read is…, AppError, Exception, Base class for expected, client-facing errors., _authenticate_api_key(), _authenticate_jwt() (+32 more)

### Community 36 - "schemas/proxy.py"
Cohesion: 0.07
Nodes (31): bundle_summary(), BundleFile, fingerprint_files(), is_allowed_bundle_path(), NginxApplyParams, NginxBundle, Any, field_validator (+23 more)

### Community 37 - "v1/search.py"
Cohesion: 0.18
Nodes (23): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+15 more)

### Community 38 - "models/__init__.py"
Cohesion: 0.07
Nodes (71): _org_scoped_classes(), org_scoped_table_names(), Mapped classes marked :class:`~app.models.base.OrgScoped`. Reads the mapper…, Names of the tables the guard and RLS are expected to cover., Base, big_serial_pk(), json_column(), org_id_column() (+63 more)

### Community 39 - "v1/channels.py"
Cohesion: 0.15
Nodes (28): create_channel(), delete_channel(), get_channel(), list_channels(), list_deliveries(), DbDep, delete, Depends (+20 more)

### Community 40 - "DockerProvider"
Cohesion: 0.10
Nodes (10): DockerProvider, Any, datetime, Protocol, List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``., List volumes: keys ``name``, ``driver``, ``mountpoint``., List networks: keys ``name``, ``driver``, ``scope``., Yield parsed log lines. With ``follow=True`` the stream never ends. (+2 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.07
Nodes (57): assert_safe_url_async(), Async wrapper around :func:`assert_safe_url`; DNS runs off the loop., CheckResult, Monitor, One probe. Targets are polymorphic since Phase 4 (domain-model.md §2.6).…, CheckOutcome, coerce_headers(), _decode() (+49 more)

### Community 42 - "StepFailure"
Cohesion: 0.11
Nodes (19): Exception, Raised by a runner when a step fails irrecoverably., StepFailure, 10. Events and WS during runs, 12. Rollback semantics (existing behavior kept), 13. The simulated runner stays — labeled, 14. Open questions, 1. Current state — what is real and what is simulated (+11 more)

### Community 43 - "AuthContext.tsx"
Cohesion: 0.05
Nodes (32): Membership, User, AuthContext, AuthProvider(), AuthState, isOrgSelectionError(), MeResponse, ORG_SELECTION_FAILURES (+24 more)

### Community 44 - "v1/health.py"
Cohesion: 0.20
Nodes (13): liveness(), get, Response, Health probes: liveness (always cheap) and readiness (checks dependencies).…, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness(), HealthOut (+5 more)

### Community 45 - "test_permissions.py"
Cohesion: 0.05
Nodes (38): permission_exists(), PermissionSpec, Permission registry and role matrix. Permissions are *data*: the registry below…, Check an API-key scope list against a required permission. Supports exact match…, scope_matches(), _auth_context(), _FakeCtx, parametrize (+30 more)

### Community 46 - "routes.py"
Cohesion: 0.14
Nodes (32): create_route(), delete_route(), disable_route(), _domain_status(), enable_route(), get_route(), list_routes(), AsyncSession (+24 more)

### Community 47 - "test_phase3_nodes.py"
Cohesion: 0.14
Nodes (35): Run the enclosed block with tenant filtering off (maintenance only). ``reason``…, system_scope(), _create_token(), _dispatch(), _enroll(), _enrolled_node(), _load_agent_module(), _mutate_in_system_scope() (+27 more)

### Community 48 - "test_ssrf.py"
Cohesion: 0.17
Nodes (25): assert_safe_tcp_endpoint(), assert_safe_url(), Validate *url* for outbound requests; return the parsed URL or raise 422.…, Validate a ``tcp://`` docker host endpoint for outbound connection. Docker…, install_dns(), Exception, MonkeyPatch, Unit tests for the SSRF guard — fully offline via injected DNS answers. (+17 more)

### Community 49 - "NotFound"
Cohesion: 0.09
Nodes (51): NotFound, An encrypted configuration value, scoped to org, project or environment.…, Secret, _actor_type(), _collect_refs(), create_secret(), delete_secret(), _detail() (+43 more)

### Community 50 - "roles.py"
Cohesion: 0.06
Nodes (52): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, delete, get (+44 more)

### Community 51 - "record"
Cohesion: 0.06
Nodes (64): apply_node_proxy_config(), create_enrollment_token(), create_server(), delete_server(), _enrollment_created(), _enrollment_out(), get_server(), list_enrollment_tokens() (+56 more)

### Community 52 - "proxy_service.py"
Cohesion: 0.05
Nodes (96): ListenerOwnership, ProxyApplyOutcome, Last nginx apply outcome for a route, as reported by its node's agent.…, Terminal outcome of one ``nginx.apply`` operation on a node., Who holds one required listener port, per the node's pre-flight. The…, RouteConfigState, NodeProxyCapabilityOut, The node's reported nginx capability, bounded to the useful facts. (+88 more)

### Community 53 - "pytest"
Cohesion: 0.14
Nodes (13): created_at server defaults must evaluate per insert, not at table creation., Regression: system_events and audit_logs shipped with DEFAULT 'now()' (quoted…, test_audit_and_event_created_at_defaults_are_dynamic(), Phase 2.1 corrective migration: legacy ``environment_type`` classification.…, Every case is classified as documented, ids and ownership intact., An explicit non-DEV classification survives the corrective migration. The…, The correction is part of ``head`` and adds no extra Alembic head., Insert one legacy environment per case, in two organizations. (+5 more)

### Community 54 - "v1/auth.py"
Cohesion: 0.09
Nodes (49): change_password(), _clear_refresh_cookie(), _cookies_secure(), login(), logout(), me(), _optional_actor(), AsyncSession (+41 more)

### Community 55 - "test_agent_nginx_contract.py"
Cohesion: 0.07
Nodes (56): _agent_bundle(), agent_fixture(), _bootstrap_fixture(), _load_agent(), Any, fixture, parametrize, Path (+48 more)

### Community 56 - "create_user"
Cohesion: 0.13
Nodes (22): create_user(), deactivate_user(), get_user(), list_users(), CurrentUser, DbSessionDep, delete, get (+14 more)

### Community 57 - "alembic"
Cohesion: 0.06
Nodes (12): alembic, Fix pre-existing model/migration drift (surfaced by the new drift check). Two…, _clear_app_role_guc(), downgrade(), Phase 2.1 — enforce append-only ``secret_versions`` in the database. Phase 2…, Publish the app-role name to the migration GUC the revoke block reads., _set_app_role_in_guc(), upgrade() (+4 more)

### Community 58 - "notification_service.py"
Cohesion: 0.13
Nodes (33): DeliveryStatus, NotificationDelivery, _as_uuid(), _attempt_delivery(), decode_delivery_cursor(), decrypt_channel_config(), dispatch_event_frame(), _send() (+25 more)

### Community 59 - "helpers.py"
Cohesion: 0.06
Nodes (60): bearer(), cookie_attributes(), login_account(), login_headers(), Any, AsyncClient, Response, Pure helpers for journey tests: payloads, auth shortcuts, cookie parsing. (+52 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "v1/deployments.py"
Cohesion: 0.08
Nodes (50): _attribute_step_idx(), cancel_deployment(), _emails_for(), get_deployment(), list_application_deployments(), list_deployment_logs(), _list_deployments(), _parse_sort() (+42 more)

### Community 62 - "test_error_logging.py"
Cohesion: 0.22
Nodes (4): Regression: the catch-all 500 handler must not log raw exception text.…, _SpyLogger, test_unhandled_exception_handler_logs_class_not_message(), fastapi_testclient

### Community 63 - "dns_verifier.py"
Cohesion: 0.11
Nodes (21): apex_of(), The name a wildcard Domain is anchored at (``*.example.com`` →…, The exact TXT owner name a user must publish at their provider., verification_record_name(), _discover_nameservers(), _normalise_ns(), observe(), Observer (+13 more)

### Community 64 - "test_phase2_environments.py"
Cohesion: 0.18
Nodes (22): _environment(), _project(), parametrize, Phase 2: project-scoped environments, config layering, and their isolation. The…, Uniqueness is ``(project_id, slug)`` — not instance-wide., The update path is validated too (the pre-Phase-2 gap)., Knowing an environment UUID is not access: the project link must hold., Another tenant cannot reach the project, its environments, or its detail. (+14 more)

### Community 65 - "route_service.py"
Cohesion: 0.11
Nodes (47): UnprocessableEntity, One hostname+path served from one container on one node. Relationship rules the…, Route, _actor(), _apply_or_defer(), _conflicting_route(), create_route(), delete_route() (+39 more)

### Community 66 - "test_schema_redaction.py"
Cohesion: 0.18
Nodes (17): is_sensitive_header(), mask_sensitive_headers(), True when *name* looks like it carries a credential (Authorization etc.)., Return a copy of *headers* with sensitive values replaced by a mask., mask_target(), Human-readable masked target safe to expose over the API. For webhook families…, _monitor_out(), Outbound-schema redaction: monitor probe credentials and webhook targets.… (+9 more)

### Community 67 - "enums.py"
Cohesion: 0.03
Nodes (165): asyncio, _decode_frame(), _max_log_id(), _poll_new_lines(), Container API: listing/detail, lifecycle actions, removal, logs, streaming.…, Parse a Redis pub/sub frame ``{ts, stream, message}`` into a LogLine., Highest persisted log id for a container (poll fallback watermark)., Fetch log rows persisted after ``last_seen['id']`` (poll fallback). (+157 more)

### Community 68 - "decrypt_str"
Cohesion: 0.07
Nodes (29): decrypt_str(), _fernet(), parametrize, test_decrypt_with_wrong_ciphertext_raises_value_error(), test_encrypt_decrypt_roundtrip(), 10. Status/expiry tracking and monitor tie-in, 11. Failure handling, 12. Audit and events (+21 more)

### Community 69 - "package.json"
Cohesion: 0.13
Nodes (15): name, private, type, version, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom (+7 more)

### Community 70 - "TenancyScopeError"
Cohesion: 0.10
Nodes (26): _apply_scope_guc(), _desired_guc(), _guard(), _has_org_predicate(), install_tenancy_guards(), _mappers_of(), Any, Raised when a unit of work touches tenant data with no valid org scope. This is… (+18 more)

### Community 71 - "test_secrets.py"
Cohesion: 0.22
Nodes (13): _create(), _environment_config(), Secrets: metadata-only reads, rotation versioning, deploy-time resolution., Project → application → environment carrying *config*; returns its id., A reference naming no secret must abort, not resolve to an empty value.…, A row this ENCRYPTION_KEY cannot decrypt must abort, not yield ``""``., test_create_and_list_return_metadata_only(), test_delete_removes_metadata_row() (+5 more)

### Community 72 - "test_nginx_renderer.py"
Cohesion: 0.13
Nodes (36): NginxProvider, ValueError, The only production provider in Phase 4., Where a route's fragment lands, so the service can name it in events., Rendering refused the input. Always a bug or a corrupt row, never a leak., RenderError, provider(), fixture (+28 more)

### Community 73 - "domain_service.py"
Cohesion: 0.07
Nodes (50): paginate(), AsyncSession, Execute *stmt* with limit/offset and return ``(rows, total)``., Domain, One DNS name an organization is proving it controls. ``name`` is canonical (see…, list_hosts(), Offset-paginated host listing with optional status/name filters., _actor() (+42 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "monitors.py"
Cohesion: 0.10
Nodes (48): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+40 more)

### Community 76 - "deps.py"
Cohesion: 0.05
Nodes (71): permission_dep(), Any, FastAPI dependencies: database session, authenticated tenant context, RBAC…, Dependency factory enforcing a permission; returns 403 when denied., require_permission(), _check(), API key routes — self-service management of the caller's own machine…, list_audit_logs() (+63 more)

### Community 77 - "domains.py"
Cohesion: 0.11
Nodes (39): create_domain(), delete_domain(), _enqueue_verification(), get_domain(), list_domain_routes(), list_domains(), _project_names(), alias (+31 more)

### Community 78 - "incident_service.py"
Cohesion: 0.10
Nodes (56): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+48 more)

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
Cohesion: 0.12
Nodes (32): canonicalize_name(), canonicalize_path(), _check_labels(), _check_not_ip(), hostname_is_covered(), _idna(), InvalidName, is_valid_path() (+24 more)

### Community 83 - "tests/conftest.py"
Cohesion: 0.20
Nodes (8): configure_test_env(), Test bootstrap: pin every cached setting BEFORE the first ``app`` import. The…, KEY=VALUE pairs from the repo .env (first definition wins); never logged., Export the exact settings the app caches; host values cannot leak through., _read_dot_env(), os, pathlib, sys

### Community 84 - "_resolve_tags"
Cohesion: 0.29
Nodes (7): list_tags_with_usage(), Fetch existing tags by name and case-preservingly create missing ones., All tags ordered by name with their server usage counts., Create a tag or update its colour; names are matched exactly., _resolve_tags(), upsert_tag(), Tag

### Community 85 - "create_user"
Cohesion: 0.10
Nodes (38): _apply_deactivation(), _assert_not_last_active_member(), _assert_not_last_active_superadmin(), create_user(), deactivate_user(), get_by_email(), get_member(), get_user() (+30 more)

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "Conflict"
Cohesion: 0.08
Nodes (51): Conflict, Operation, Whether the agent reported this operation as successful. A terminal check, not…, One whitelisted action for one node, with a CAS lifecycle. ``attempts`` is…, OperationCreate, Request one whitelisted action on one node., _active_org(), _bounded() (+43 more)

### Community 88 - "test_certificate_lifecycle.py"
Cohesion: 0.10
Nodes (35): CertificateGeneration, one_live_generation_predicate(), One ACME order + one key pair. Renewal inserts a new row, never mutates one.…, The SQL predicate of ``uq_cert_generations_one_live``. Built from…, CertificateGenerationState, Pre-issuance lifecycle of one ACME order + key pair. **The vocabulary is…, The states in which a generation is still being worked on. At most one of these…, CertificateGenerationOut (+27 more)

### Community 89 - "Settings"
Cohesion: 0.14
Nodes (6): field_validator, model_validator, Username from :attr:`database_url`, or ``None`` if it is unparseable., Validated application settings (loaded from environment / .env)., Settings, BaseSettings

### Community 90 - "_release_competing_claim"
Cohesion: 0.50
Nodes (4): The honest state of a route that left the desired tree but is not gone. One…, removal_requested_detail(), Move another organization's ``VERIFIED`` claim on *name* to ``UNVERIFIED``. Its…, _release_competing_claim()

### Community 91 - "validate_config"
Cohesion: 0.07
Nodes (30): _normalise_environment_type(), field_validator, field_validator, collect_secret_refs(), walk(), ConfigValidationError, merge_config(), Any (+22 more)

### Community 92 - "alerts.py"
Cohesion: 0.19
Nodes (17): list_alerts(), mark_all_read(), mark_read(), CurrentUser, DbDep, Depends, get, post (+9 more)

### Community 93 - "get_sessionmaker"
Cohesion: 0.06
Nodes (58): get_sessionmaker(), async_sessionmaker, AsyncSession, current_scope(), org_scope(), ``'org'``, ``'system'`` or ``'unset'``., Run the enclosed block as a single organization. Nesting the *same* org is a…, _entity_exists() (+50 more)

### Community 94 - "test_phase21_secret_version_integrity.py"
Cohesion: 0.18
Nodes (18): _app_role_dsn(), _owner_dsn(), _probe(), Phase 2.1 — ``secret_versions`` is append-only in the **database**, not just in…, Immutability is a database guarantee, not merely a missing code path. The owner…, The legitimate append paths keep working under the guard., The documented deletion policy: purging a Secret cascades its history., RLS is preserved: another tenant cannot see a version row, even by id. (+10 more)

### Community 95 - "Server"
Cohesion: 0.06
Nodes (58): agent_enroll(), agent_heartbeat(), agent_hello(), claim_operation(), _presented_token(), DbDep, post, Request (+50 more)

### Community 96 - "NexusOps (self-hosted infrastructure management and monitoring platform)"
Cohesion: 0.20
Nodes (10): mailpit service (dev SMTP sink + web UI :8025), NexusOps compose stack (8 services on one network), HIGH finding: redirect-following SSRF in uptime monitors (fixed: follow_redirects=False + per-hop guard), SSRF guard (assert_safe_url, per-redirect-hop validation, assert_safe_tcp_endpoint), Mailpit SMTP port internal-only (host-side injection needs extra mapping), Host port knobs (NEXUSOPS_HTTP_PORT/POSTGRES/REDIS/MAILPIT/VITE), SPA entry point (loads /src/main.tsx, dark color-scheme), Uptime monitors -> incidents -> notifications flow (+2 more)

### Community 97 - "REST API surface (/api/v1)"
Cohesion: 0.29
Nodes (7): Cursor (keyset) and offset pagination envelopes, Permission model (data-driven registry, require_permission, wildcard scopes), REST API surface (/api/v1), RBAC registry (PERMISSIONS + ROLE_MATRIX + scope_matches), Adding a new resource: 7-step checklist (model -> migration -> schemas -> service -> router -> tests -> frontend), Alembic migration workflow (autogenerate, models __init__ export, entrypoint apply), Command palette (Ctrl/Cmd+K)

### Community 98 - "journey.spec.ts"
Cohesion: 0.14
Nodes (16): EDGE, MAILPIT, ADMIN, Bootstrap, bootstrapVia(), test, ADMIN, formLogin() (+8 more)

### Community 99 - "Layout.tsx"
Cohesion: 0.07
Nodes (22): SearchResult, mocks, Probe(), USER, Command, CommandPalette(), CommandPaletteProps, STATIC_COMMANDS (+14 more)

### Community 100 - "redact_mapping"
Cohesion: 0.09
Nodes (33): _is_sensitive_key(), Return a copy of *data* with sensitive values replaced, at any depth. Two…, Substring match on a normalised key so header-style names are caught too.…, redact_mapping(), parametrize, Unit tests for app.core.logging redaction (pure functions only)., No sensitive key name involved: the PEM armor is the only signal., Lists of dicts holding further lists — the shape an agent report takes. (+25 more)

### Community 101 - "certificates.py"
Cohesion: 0.10
Nodes (34): create_certificate(), delete_certificate(), get_certificate(), list_certificates(), alias, AsyncSession, DbDep, delete (+26 more)

### Community 102 - "organization.py"
Cohesion: 0.11
Nodes (24): create_organization(), list_my_organizations(), CurrentUser, DbSessionDep, get, IdentityUser, patch, post (+16 more)

### Community 103 - "_mutate_in_system_scope"
Cohesion: 0.11
Nodes (30): Keep every routed node's live configuration matching the desired bundle. One…, sweep_routes(), _container_id(), _create_node(), _heartbeat(), heartbeat_payload(), _live_operations(), _mutate_in_system_scope() (+22 more)

### Community 104 - "test_migration_phase4.py"
Cohesion: 0.13
Nodes (23): Move ``database`` *back* to ``revision``. The same code path a deployment uses…, _run_downgrade(), _columns(), _integrity_error(), _migrate_from_phase3(), Statement, Phase 4 migration (`f4a5b6c7d8e9`) against a real Phase 3 database. Phase 4 is…, The polymorphic shape is enforced in both directions. (+15 more)

### Community 105 - "redis service (Redis 7, no persistence, loopback :6390)"
Cohesion: 0.22
Nodes (11): redis service (Redis 7, no persistence, loopback :6390), WebSocket API (/api/v1/ws handshake, frames, limits), WebSocket channels (global, server-metrics, container-logs, deployment-logs, incidents), Deployment engine (queue_deployment / execute_deployment / sweeper backstop), Real-time spine: PostgreSQL system_events + Redis pub/sub, Rollback as a new deployment (rollback_of_id), WebSocket hub (framework-thin, Redis fan-in, per-socket queues), Test suites (pytest unit+integration, vitest, Playwright e2e) (+3 more)

### Community 106 - "NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)"
Cohesion: 0.18
Nodes (12): Agent security model (one-way telemetry, no command channel), Agent enrollment token (X-Agent-Token, nxa_..., SHA-256 at rest), Agent heartbeat exponential backoff (cap 5 min, exit 1 on revoked token), agent/install.sh (enrollment installer), Agent metrics collection (/proc statvfs Docker socket), NexusOps agent (stdlib-only Python, agent/nexusops_agent.py), Agent systemd hardening (ProtectSystem=strict, NoNewPrivileges), Agent ingest API (POST /agent/hello, POST /agent/heartbeat) (+4 more)

### Community 107 - "_rows"
Cohesion: 0.13
Nodes (34): _rows(), _columns(), _foreign_keys(), _indexes(), _insert_certificate(), _insert_generation(), _integrity_error(), _migrate_from_phase4() (+26 more)

### Community 108 - "RealDockerProvider"
Cohesion: 0.17
Nodes (5): T, Execute an SDK call with one short retry, normalizing failures., Two short samples give real cpu/net deltas without streaming., Talks to a real docker daemon over ``unix://`` or ``tcp://``., RealDockerProvider

### Community 109 - "Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)"
Cohesion: 0.25
Nodes (9): API keys (X-API-Key, nxo_..., scope intersection), First boot sequence (api entrypoint migrates, compose never seeds), Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test), Makefile workflows (up/test/lint/typecheck/migrate/seed), HIGH finding: API-key scope bypass for superadmin-owned keys (fixed: scope intersection first), Security audit 2026-09 (26 raw findings -> 20 confirmed, all fixed), HIGH finding: known seed superadmin + API key backdoor (fixed: NEXUSOPS_ALLOW_SEED opt-in, one-time password), Threat model (edge attacker, malicious agent, curious operator, leaked token, SSRF) (+1 more)

### Community 110 - "ScopedSession"
Cohesion: 0.19
Nodes (3): A session that enters its tenancy scope around each operation. A fixture cannot…, ScopedSession, 3. The session guard (the mechanical layer)

### Community 111 - "update_organization"
Cohesion: 0.20
Nodes (17): add_member(), get_organization(), membership_for_user(), AsyncSession, Membership, Organization, Request, User (+9 more)

### Community 112 - "Phase 5 — HTTPS, Certificates and Private-Key Delivery — Design"
Cohesion: 0.11
Nodes (19): 1.2 Phase 5 in one sentence, 1.3 Trust boundaries Phase 5 adds, 1.4 Non-goals for Phase 5, 1.5 Trust concentration: centralized key custody, accepted **conditionally** (decided), 1. Architecture and trust boundaries, 2.1 The six stages, kept distinct, 2.2 Certificate generation state machine, 2.3 Delivery/activation state machine (per certificate × node) (+11 more)

### Community 113 - "dnsmock.py"
Cohesion: 0.12
Nodes (24): resolver(), answer(), encode_name(), encode_txt(), forward(), main(), parse_question(), TXT rdata: one or more length-prefixed strings, each ≤ 255 bytes. (+16 more)

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "APIModel"
Cohesion: 0.03
Nodes (100): Agent ingest endpoints: enrollment, hello, heartbeat, and operation traffic.…, AgentContainerPortIn, AgentEnrollIn, AgentEnrollOut, AgentHeartbeatOut, AgentHelloOut, AgentTokenRotation, CapabilityReport (+92 more)

### Community 116 - "test_tenancy_allowlist.py"
Cohesion: 0.20
Nodes (14): AST, _actual_callers(), _calls_system_scope(), _module_path(), Path, The system-scope allowlist is the only fence around the tenancy carve-out.…, Every module that could open a system scope: ``app/`` plus the scripts., No module may lift tenant isolation without being named in the list. (+6 more)

### Community 117 - "_alembic_config"
Cohesion: 0.18
Nodes (13): _alembic_config(), _at_revision(), _migration_dsn(), Run one Alembic direction against ``database`` through the app's settings path.…, Phase 2 adds one migration; heads must not fork., test_exactly_one_alembic_head(), Phase 4 adds one migration; the chain still has exactly one head., Phase 4.2 sits directly on the Phase 4 head, in a chain with one head. This… (+5 more)

### Community 118 - "dependencies"
Cohesion: 0.33
Nodes (6): dependencies, lucide-react, react, react-dom, react-router-dom, @tanstack/react-query

### Community 119 - "DeploymentDetailPage.tsx"
Cohesion: 0.09
Nodes (17): DeploymentStepOut, DeploymentDetailPage, ACTIVE_STATUSES, DeploymentDetailRow, DeploymentLogRow, formatLogTime(), LogLines(), StepCard() (+9 more)

### Community 120 - "generate_secrets.sh"
Cohesion: 0.47
Nodes (3): existing_real_keys(), replace_or_append(), generate_secrets.sh script

### Community 121 - "ControlHandler"
Cohesion: 0.22
Nodes (7): BaseHTTPRequestHandler, clear_record(), ControlHandler, in_zone(), The journey's only way to publish a record — no shell, no shared volume., set_record(), snapshot()

### Community 122 - "test_tenant_isolation.py"
Cohesion: 0.04
Nodes (63): dispose_engine(), error_of(), Unwrap an API error envelope., A valid POST /servers body with per-test overrides., server_payload(), test_token_cannot_claim_a_foreign_tenants_node(), test_v1_heartbeat_keeps_the_204_contract(), Regression: a superadmin-owned key is still limited to its scope list. The… (+55 more)

### Community 123 - "_exec"
Cohesion: 0.14
Nodes (23): alembic_config, UUID, Phase 2.2 — the environment-type correction follows the documented precedence.…, Only the previous migration's ``PROD`` output is corrected. A row already…, Create one legacy (application-scoped) environment per case., Every branch of the slug-first rule, end to end through ``head``., _seed_legacy(), test_correction_preserves_operator_set_values() (+15 more)

### Community 124 - "middleware.py"
Cohesion: 0.14
Nodes (15): ASGIApp, AccessLogMiddleware, Request, Response, HTTP middleware: request ids, security headers, structured access logs., Baseline hardening headers on every API response., RequestIDMiddleware, SecurityHeadersMiddleware (+7 more)

### Community 125 - "OperationError"
Cohesion: 0.15
Nodes (17): _demux_docker_stream(), _docker_error(), execute_operation(), OperationError, _process_pending_operations(), Exception, A stable, sanitized failure contract for the control plane., Re-validate the operation's parameters locally, against a closed shape. (+9 more)

### Community 126 - "list_operations"
Cohesion: 0.21
Nodes (15): cancel_operation(), create_operation(), get_operation(), list_operations(), DbDep, Depends, get, post (+7 more)

### Community 127 - "test_phase4_routing.py"
Cohesion: 0.11
Nodes (27): MonitorTargetType, What a monitor observes (domain-model.md §2.6, polymorphic targets). ``URL`` is…, task, Re-prove control of every domain whose next check is due. Covers three cases…, sweep_domains(), _count_rows_in_system_scope(), _create_domain(), parametrize (+19 more)

### Community 137 - "EnvironmentDetailPage.tsx"
Cohesion: 0.13
Nodes (22): apiPatch(), ApplicationOut, DeploymentOut, ENVIRONMENT_TYPE_LABELS, EnvironmentDetailOut, EnvironmentType, EnvironmentDetailPage, ProjectDetailPage (+14 more)

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
Cohesion: 0.20
Nodes (10): _listener_ownership(), _listening_ports(), nginx_capability(), _nginx_owned_ports(), _nginx_version(), ``nginx -v`` prints its version to stderr; bounded and non-shell., TCP ports in LISTEN state, read from ``/proc`` (no shell, no tooling). ``None``…, Ports declared by ``listen`` directives in the *loaded* configuration. ``nginx… (+2 more)

### Community 153 - "types.ts"
Cohesion: 0.03
Nodes (55): AuditEntry, CapabilityReport, ContainerOut, DeploymentLogLine, DeploymentStatus, DockerHostOut, DomainDetailOut, DomainOut (+47 more)

### Community 154 - "nexusops-draft.mjs"
Cohesion: 0.40
Nodes (4): DOCS, meta, SPINE, VERIFY_RULES

### Community 155 - "NotificationError"
Cohesion: 0.21
Nodes (12): NotificationError, Any, BaseException, Exception, POST *payload* as JSON to *url*; 2xx is success, anything else raises. Response…, Raised when a delivery attempt fails. Message is safe to persist., Bounded, single-line, content-free error reason., Send a plain-text email via SMTP. Raises :class:`NotificationError`. The… (+4 more)

### Community 156 - "nexusops-challenge.mjs"
Cohesion: 0.33
Nodes (5): CHALLENGE_COMMON, meta, RESEARCH_COMMON, SCHEMA, TASKS

### Community 157 - "Secrets Architecture"
Cohesion: 0.11
Nodes (19): 10. Resolution flow at deploy time, 1.1 Storage and crypto, 1.2 Data model, 1.3 API surface (metadata-only reads), 1.6 Gap list (Phase 2 status), 1. Current state, 2.1 Resolution runs inside org scope, 2.2 Migration mapping (applied by `b2c3d4e5f6a7`) (+11 more)

### Community 158 - "test_schemas_agent.py"
Cohesion: 0.10
Nodes (37): AgentContainerIn, AgentHeartbeatIn, AgentHelloIn, Any, field_validator, Observed container state reported by an agent., Periodic metrics + observed containers from an enrolled agent. Network counters…, First contact from an agent after enrollment; fills static host facts. (+29 more)

### Community 159 - ".state"
Cohesion: 0.24
Nodes (10): computed_field, Derived lifecycle state: revoked wins over used wins over expired., 2. Certificate entity, 3.2 `certificate_generations` — one ACME order + one key pair, 3.3 `certificate_deliveries` — per certificate × node, material-free, 3.4 `dns_providers` — customer DNS credentials (metadata-only reads), 3.5 Reused / changed existing entities, 3.6 Monitors (+2 more)

### Community 160 - "build_capabilities"
Cohesion: 0.13
Nodes (15): build_capabilities(), collect_container_stats(), collect_containers(), _container_ports(), _container_status(), docker_capability(), _docker_request(), _docker_socket() (+7 more)

### Community 161 - "alert_service.py"
Cohesion: 0.20
Nodes (17): AlertSeverity, Alert, create_alert(), get_alert(), mark_all_read(), mark_read(), AsyncSession, UUID (+9 more)

### Community 162 - "decide"
Cohesion: 0.23
Nodes (18): decide(), matches_token(), Constant-time comparison of the observed TXT values against the token. TXT…, Turn one observation into the verification outcome — pure, no I/O.…, observation(), parametrize, The verification decision: every outcome, without a network. ``decide`` is…, test_a_sweep_invalidates_a_changed_delegation_even_with_the_token() (+10 more)

### Community 163 - "AlertsPage.tsx"
Cohesion: 0.11
Nodes (20): AlertOut, ChannelOut, DeliveryOut, AlertsPage, ChannelDialog(), DeleteChannelDialog(), describeError(), parseEventList() (+12 more)

### Community 164 - "AgentClient"
Cohesion: 0.15
Nodes (8): AgentClient, _docker_raw(), A verifying TLS context. Verification is never disabled. A private/self-hosted…, Refuse to send credentials over plain HTTP to a non-loopback server. The…, One raw Docker API call; returns ``(status, body_bytes)``., _tls_context(), _UnixHTTPConnection, SSLContext

### Community 165 - "certificate_lifecycle.py"
Cohesion: 0.15
Nodes (20): attempt_delay_seconds(), is_retryable(), is_terminal(), next_attempt_at(), datetime, The pre-issuance certificate lifecycle — pure decisions, no I/O, no side…, Whether a generation has spent every attempt it was allowed., Whether a failed generation may be moved back to ``ORDERING``. A failure is… (+12 more)

### Community 166 - "nginx.py"
Cohesion: 0.11
Nodes (26): _header_lines(), _quote(), _rate_zone(), NginxProvider — a pure, deterministic renderer plus the two op wrappers.…, Validate the route's headers and split them by destination., Wrap an already-validated value in quotes for a template slot. Values reaching…, The ``limit_req_zone`` declaration for a rate-limited route., A fixed host redirect, or ``None`` for a normal proxying route. (+18 more)

### Community 167 - "AuthContext"
Cohesion: 0.09
Nodes (31): _attach_organization(), AuthContext, get_current_user(), get_identity(), get_optional_user(), _load_organization(), _load_permissions(), _org_id_from_header() (+23 more)

### Community 168 - "DashboardPage.tsx"
Cohesion: 0.11
Nodes (15): DashboardSummary, DashboardPage, LoadingBlock(), asFeedItem(), badgeLevel(), DashboardPage(), FeedItem, formatTimestamp() (+7 more)

### Community 169 - "test_a_late_result_for_an_expired_operation_cannot_fail_a_live_route"
Cohesion: 0.15
Nodes (21): _agent_result_body(), _audits(), _claim(), _event_types(), The same delivery twice: one apply, one set of events, one audit row., A report that contradicts what already happened is ignored, not applied., A report that arrives after its operation expired changes nothing at all., The result body the agent sends for one operation it claimed. Shared by the… (+13 more)

### Community 170 - "test_agent_contract.py"
Cohesion: 0.20
Nodes (15): agent_fixture(), _load_agent(), _patch_stats(), Any, fixture, MonkeyPatch, Contract tests: the shipped agent's payloads must satisfy the ingest schemas.…, One-shot docker stats reduce to cpu/mem/limit fields the schema accepts, with… (+7 more)

### Community 171 - "StepLine"
Cohesion: 0.22
Nodes (8): _commit_short(), Deployment runner port plus a faithful simulated implementation.…, Stream output lines for *step_name*; raise StepFailure to fail it., Everything a runner needs to execute one deployment., One streamed output line for a step., RunContext, _slug(), StepLine

### Community 172 - "docker_real.py"
Cohesion: 0.17
Nodes (19): _as_float(), _compute_stats(), _cpu_percent(), _network_bytes(), parse_log_line(), parse_rfc3339(), Any, datetime (+11 more)

### Community 173 - "container.py"
Cohesion: 0.15
Nodes (18): _container_out(), Serialize one row; env values never leave the database (keys only)., ContainerDetailOut, ContainerOut, ContainerRemoveOut, host_ref(), HostRef, LogEntryOut (+10 more)

### Community 174 - "create_api_key"
Cohesion: 0.16
Nodes (17): create_api_key(), list_api_keys(), CurrentUser, DbSessionDep, delete, get, post, Request (+9 more)

### Community 175 - "config.py"
Cohesion: 0.14
Nodes (15): _database_url(), Alembic environment: metadata comes from app.models, URL from app settings., Migrations run as the table **owner**, never as the application role. The owner…, Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online(), fail_on_bad_config() (+7 more)

### Community 176 - "Platform Security Model — NexusOps"
Cohesion: 0.12
Nodes (17): make(), 10.1 Node revocation playbook (compromised node / leaked agent token), 10.2 Key compromise playbook, 10. Incident response, 1.1 Real vs simulated today (do not mistake one for the other), 1. Scope, stance, and simulation honesty, 2. Assets, 3. Trust boundaries (+9 more)

### Community 177 - "docker_sim.py"
Cohesion: 0.14
Nodes (10): ContainerStats, Point-in-time resource usage snapshot., Any, datetime, Simulated docker provider for demo and test environments. The provider is…, Plausible numbers derived from the row plus time-based sine noise., Replay registered LogEntry rows ordered by ts (tail N). ``follow`` is ignored…, _seed_int() (+2 more)

### Community 178 - "list_sessions"
Cohesion: 0.18
Nodes (12): list_sessions(), CurrentUser, DbSessionDep, delete, get, Request, UUID, Active sessions of this organization's members. Defaults to the caller's own;… (+4 more)

### Community 179 - "_node_proxy_state"
Cohesion: 0.16
Nodes (21): _converged_node_with_a_route(), _hello_elsewhere(), _mark_reconcile_required_elsewhere(), _node_proxy_state(), _node_session(), _pause_render(), gated(), One worker unit of work: a fresh session, its org scope, and its node. (+13 more)

### Community 180 - "router.py"
Cohesion: 0.40
Nodes (4): websocket, WebSocket endpoint. Mounted by the app factory under ``/api/v1``., Hand the socket to the hub (auth handshake handled there)., websocket_endpoint()

### Community 181 - "_nginx_apply"
Cohesion: 0.12
Nodes (24): _fsync_dir(), _nginx_apply(), Materialize the bundle under ``staged/<id>/`` and return that directory.…, Build a self-contained config for ``nginx -t`` over the staged tree. The…, Move the staged tree over the live one, keeping the previous as backup., Put the previous known-good tree back. Returns whether it was possible., Stage → validate → swap → reload, with a rollback on a failed reload., Persist the last apply outcome atomically (temp + rename). (+16 more)

### Community 182 - "_nginx_bootstrap"
Cohesion: 0.11
Nodes (23): _insert_http_includes(), _nginx_binary(), _nginx_bootstrap(), _nginx_config_test(), _nginx_failure_summary(), _nginx_running(), _nginx_status(), _pid_alive() (+15 more)

### Community 183 - "channel.py"
Cohesion: 0.20
Nodes (12): ChannelType, ChannelBase, ChannelCreate, ChannelUpdate, DeliveryOut, EmailConfig, model_validator, Schemas for notification channels and delivery records. Channel configuration… (+4 more)

### Community 184 - "create_api_key"
Cohesion: 0.22
Nodes (11): create_api_key(), list_api_keys(), AsyncSession, Request, UUID, Live (non-revoked) keys owned by *owner_id*, newest first., Revoke every live key of a user (used on deactivation). Returns count., Validate + normalise scopes; returns the deduplicated list. Accepts exact… (+3 more)

### Community 185 - "20261012_1200-c8d9e0f1a2b3_phase5_certificate_metadata.py"
Cohesion: 0.23
Nodes (13): downgrade(), _drop_certificate_permissions(), _drop_tenant_policies(), _grant(), _in_list(), Phase 5.1 — certificate metadata and the pre-issuance lifecycle. Adds, in one…, Grant the app role on *table*; the migration role GUC carries the name. The…, The two-policy shape every tenant table uses: tenant + system scope. (+5 more)

### Community 186 - "run_async"
Cohesion: 0.04
Nodes (89): collect_recent_logs(), Pull recent logs from running containers of a real host. Simulated hosts are…, flush_pending_publishes(), Wait for frames scheduled by ``after_commit`` hooks to reach Redis. The commit…, Celery application: periodic cadences live here, dynamic work is claimed…, task, Execute one queued deployment. The engine owns all state transitions., Re-enqueue deployments the broker lost; fail ones whose worker died.… (+81 more)

### Community 187 - "test_migration_drift.py"
Cohesion: 0.18
Nodes (11): alembic_autogenerate, alembic_migration, CertificateChallengeType, How ownership of an identifier is proved to the CA. DNS-01 only in v1: it is…, Model / migration drift: the schema in the database must match the models.…, ``Base.metadata`` and the migrated database must describe the same schema., The DB whitelist and ``OperationType`` are the same closed set. The migration…, The Phase 5.1 closed vocabularies are the sets the code declares.… (+3 more)

### Community 188 - "instant_pacing"
Cohesion: 0.40
Nodes (4): instant_pacing(), fixture, MonkeyPatch, Remove the per-line sleeps; pacing bounds are asserted separately.

### Community 189 - "phase3.spec.ts"
Cohesion: 0.15
Nodes (10): frontend_e2e_fixtures_expect, AGENT, NodeDetail, OperationRow, REPO_ROOT, ref_node_child_process, ref_node_fs, ref_node_os (+2 more)

### Community 190 - "server.py"
Cohesion: 0.14
Nodes (13): _clean_tag_names(), DockerHostSummary, EnrollTokenOut, Server API schemas: create/update payloads, list/detail outputs, enrollment., Compact system event projection for server timelines., One-time agent enrollment token. The raw value is never stored., Reject non-empty values that are not valid IPv4/IPv6 addresses., Strip, drop empties and de-duplicate tag names case-insensitively. (+5 more)

### Community 191 - "test_migration_phase3.py"
Cohesion: 0.20
Nodes (11): alembic_script, Phase 3 migration (``a1b2c3d4e5f6``) against realistic legacy data. Phase 3 is…, A fresh database reaches the same shape the models describe., Phase 3 adds one migration; heads must not fork., The pre-Phase-3 shapes: a node with telemetry, and operation history., _seed_legacy(), test_exactly_one_alembic_head(), test_migration_from_zero_adds_the_phase3_shape() (+3 more)

### Community 192 - "get_settings"
Cohesion: 0.08
Nodes (31): _quoted_list(), Add the operations framework table (node-agent-architecture.md §5). One tenant-…, upgrade(), downgrade(), _drop_constraint(), _quoted_list(), Phase 2 — projects & environments: env promotion, config, secret versions. This…, upgrade() (+23 more)

### Community 193 - "10. Implementation slices, acceptance criteria, tests, limitations"
Cohesion: 0.25
Nodes (8): 10.1 Slices (each independently reviewable, in order), 10.2 Test requirements (what "done" means per slice), 10.3.1 Approved decisions (previously open), 10.3.2 Known limitations (accepted, not blockers), 10.3.3 Open items and whether they block Phase 5.1, 10.3 Decisions and known limitations, 10.4 Reserved-operation-type lists — one source of truth (required consolidation), 10. Implementation slices, acceptance criteria, tests, limitations

### Community 194 - "test_ws_hub.py"
Cohesion: 0.10
Nodes (34): _is_same_origin(), Browsers always send Origin on WS handshakes, even same-origin ones. When it…, _connection(), _drain(), _event_frame(), _fake_sessionmaker(), _FakeSession, hub() (+26 more)

### Community 195 - "get_host"
Cohesion: 0.39
Nodes (12): get_docker_host(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host(), DbSessionDep, get, _ReadPerm (+4 more)

### Community 196 - "list_docker_hosts"
Cohesion: 0.17
Nodes (11): list_docker_hosts(), alias, Depends, max_length, Query, Offset-paginated docker host listing; exposes status and last_error., DockerHostOut, field_serializer (+3 more)

### Community 197 - "main.py"
Cohesion: 0.26
Nodes (10): close_redis(), create_app(), _include_routers(), lifespan(), FastAPI, NexusOps API entrypoint. Wires middleware, error handling, REST routers and the…, Mount every domain router. Router variables follow the module contract., Start the WS hub + notification dispatcher; tear them down cleanly. (+2 more)

### Community 198 - "README.md - NexusOps overview"
Cohesion: 0.09
Nodes (43): What one reported result did to its operation row. The caller's side effects —…, ResultTransition, docker-compose.dev.yml - dev overlay, docker-compose.docker-sock.yml - docker socket override, docker-compose.yml - full stack definition, docs/agent.md - agent guide, docs/api.md - API guide, Append-only audit log (Postgres BEFORE UPDATE OR DELETE trigger) (+35 more)

### Community 199 - "CertificateStatus"
Cohesion: 0.24
Nodes (11): CertificateStatus, Certificate-level view of the *current* generation, derived, never stored raw.…, assert_pre_issuance(), certificate_status_for(), Return *value* as a pre-issuance state, or refuse it loudly. This is the guard…, The certificate-level status implied by a generation's state. Derived, never…, derive_status(), The certificate's status and its explanation, derived from *generation*.… (+3 more)

### Community 200 - "_validate_resolution"
Cohesion: 0.24
Nodes (9): _is_forbidden_address(), True when *addr* points into a network the server must never contact.…, Resolve *hostname* (AF_UNSPEC) and refuse any non-public answer., _validate_resolution(), test_private_and_special_addresses_are_forbidden(), test_public_addresses_are_allowed(), test_validate_resolution_passes_hostname_through(), IPv4Address (+1 more)

### Community 201 - "NotificationChannel"
Cohesion: 0.23
Nodes (11): NotificationChannel, A delivery target (email address / webhook endpoint). ``config_ciphertext``…, _create_monitor(), Monitor checks driving the full down -> incident -> recovery lifecycle., Regression: probe headers and URL query credentials never leave the API. Probe…, A monitor's checks, incidents and timeline all live in its organization, so the…, test_check_now_endpoint_runs_immediately(), test_down_then_recover_lifecycle() (+3 more)

### Community 202 - "test_tasks_util.py"
Cohesion: 0.36
Nodes (8): _answer(), _boom(), _nested(), Unit tests for the Celery-task async bridge (pure asyncio, no broker)., test_run_async_awaits_nested_coroutines(), test_run_async_is_repeatable_per_invocation(), test_run_async_propagates_exceptions(), test_run_async_returns_coroutine_result()

### Community 203 - "ProxyProvider"
Cohesion: 0.33
Nodes (5): ProxyProvider, Any, Protocol, What ``app.services.proxy_service`` is allowed to assume about a provider. The…, 11. Post-deploy hooks

### Community 204 - "create_docker_host"
Cohesion: 0.22
Nodes (9): create_docker_host(), delete_docker_host(), delete, post, Request, Delete the host and cascade-delete its containers and images., Register a host. Endpoint allowlist: unix://, tcp://, sim:// or ''., _CreatePerm (+1 more)

### Community 205 - "ContainerInfo"
Cohesion: 0.28
Nodes (4): ContainerInfo, List containers visible to the provider., Inspect a single container by id (short ids allowed)., Normalized view of a container as reported by any provider.

### Community 206 - "test_agent_ingestion.py"
Cohesion: 0.30
Nodes (10): _enrolled(), _heartbeat(), Agent ingest pipeline: hello, heartbeat, staleness transitions, events., A container absent from a later heartbeat is gone from the daemon., A payload at the agent's cap may be truncated — absence proves nothing., test_heartbeat_at_container_cap_skips_reconciliation(), test_heartbeat_removes_vanished_containers(), test_heartbeat_updates_status_metrics_and_containers() (+2 more)

### Community 208 - "_live_bundle_id"
Cohesion: 0.20
Nodes (10): _allowed_bundle_path(), _live_bundle_id(), _live_files(), The bundle fingerprint — byte-identical to the control plane's algorithm.…, Read the live managed tree, or ``None`` when it does not exist yet., Fingerprint of the configuration tree currently on disk., Independently validate a bundle. Anything unexpected is refused., _template_version_of() (+2 more)

### Community 209 - "Multi-Tenancy Architecture"
Cohesion: 0.15
Nodes (12): Whether the runtime connection is the RLS-enforced application role. False…, 10. Migration (Phase 1), 1. Tenancy invariants, 2.1 Org creation — v1 decision, 2. Org resolution on every request, 4. Background jobs, 5. WebSockets, 6. Agents (+4 more)

### Community 210 - "DockerHostCreate"
Cohesion: 0.25
Nodes (7): DockerHostCreate, DockerHostUpdate, model_validator, Validate/normalize an endpoint URL against the scheme allowlist., Payload for registering a docker host., Partial update payload; only supplied fields change., validate_endpoint_url()

### Community 211 - "test_schemas_search.py"
Cohesion: 0.33
Nodes (8): Results grouped per entity type, permission-filtered per caller. Every section…, SearchResultOut, Unit tests for global-search schemas., test_extra_fields_are_forbidden(), test_search_hit_requires_core_fields(), test_search_result_defaults_to_empty_sections(), test_search_result_exposes_exactly_the_documented_sections(), test_sections_hold_hits()

### Community 212 - "test_notifications.py"
Cohesion: 0.39
Nodes (8): _channel(), _delivery(), UUID, Notification channel + delivery-log endpoints. Regression coverage for GET…, The same event frame consumed twice queues ONE delivery per channel. Every API…, test_dispatch_frame_is_idempotent_across_workers(), test_list_deliveries_filters_by_channel(), test_list_deliveries_serializes_rows()

### Community 213 - "_FakeAsyncClient"
Cohesion: 0.22
Nodes (3): _FakeAsyncClient, _FakeRequestObj, Scripted httpx.AsyncClient: responses keyed by absolute request URL.

### Community 214 - "_provider_inventory"
Cohesion: 0.31
Nodes (9): list_images(), list_networks(), list_volumes(), _provider_inventory(), Any, Run an inventory call; degrade gracefully on provider failure. Unreachable…, Images on a host; empty list when the host is unreachable., Volumes on a host; empty list when the host is unreachable. (+1 more)

### Community 215 - "9. Renewal, expiration, ownership loss, removal, revocation"
Cohesion: 0.33
Nodes (6): 9.1 Renewal, 9.2 Expiration monitoring, 9.3 Ownership loss (a verified Domain changes owners), 9.4 Removal, 9.5 Revocation, 9. Renewal, expiration, ownership loss, removal, revocation

### Community 216 - "ssrf.py"
Cohesion: 0.13
Nodes (18): is_simulation_url(), ValueError, _raise_block(), SSRF guard applied to every operator-supplied outbound URL. Monitors and…, True when *url* targets the built-in simulated checker (``sim://``)., Internal signal: a specific SSRF rule matched (never shown to clients)., UrlRejected, _validate_syntax() (+10 more)

### Community 217 - "_verified_domain"
Cohesion: 0.15
Nodes (22): DomainStatus, Ownership-verification lifecycle of a Domain (domain-routing.md §4). ``STALE``…, One bounded look at a name's authoritative TXT record., TxtObservation, The state a domain flip forces on its routes, or ``None`` to leave them., route_config_state_for(), _flip_name_to(), Have *second_org* prove control of *name*, returning the verify outcome. (+14 more)

### Community 218 - "1. Scope and current state"
Cohesion: 0.24
Nodes (10): Replace every embedded PEM private-key block in *value* with the marker. Only…, Scrub PEM private-key blocks out of one free-text value. The scalar counterpart…, Recursively redact one value of any shape — the depth-agnostic walk. Dicts,…, _redact_private_key_blocks(), redact_text(), redact_value(), 1. Scope and current state, 7.1 Flow: config apply with rollback (+2 more)

### Community 219 - "update_channel"
Cohesion: 0.44
Nodes (9): _audit(), create_channel(), delete_channel(), encrypt_config(), _normalize_events(), AsyncSession, Request, Encrypt the whole provider config blob for storage. (+1 more)

### Community 220 - "test_app_gating.py"
Cohesion: 0.44
Nodes (8): _app_for_environment(), MonkeyPatch, ENVIRONMENT gating contract: docs exposure and HSTS (see .env.example).…, create_app() with get_settings() patched to the given environment., test_non_production_does_not_emit_hsts(), test_non_production_keeps_docs_and_schema(), test_production_emits_hsts(), test_production_hides_docs_and_schema()

### Community 221 - "register_exception_handlers"
Cohesion: 0.36
Nodes (8): _error_payload(), FastAPI, Request, register_exception_handlers(), handle_app_error(), handle_http_exception(), handle_unexpected(), handle_validation_error()

### Community 223 - "5. ACME issuance and DNS-01 handling"
Cohesion: 0.25
Nodes (8): 5.1 Decision: maintained ACME client library (josepy/`acme`), not a hand-rolled RFC 8555 client, 5.2 Challenge: DNS-01 only in v1, 5.3 DNS provider abstraction and the DNS-01 flow, 5.4 ACME account, 5.5 Issuance task and idempotency, 5.6 HTTPS activation (the "HTTP keeps serving" rule), 5.7 HTTP-01 (later fallback, design only), 5. ACME issuance and DNS-01 handling

### Community 224 - "InvalidTransition"
Cohesion: 0.33
Nodes (5): InvalidTransition, ValueError, Two pre-issuance states with no legal move between them., A generation state this phase's schema cannot express. Raised for the post-…, UnrepresentableState

### Community 225 - "20261009_1100-d4e5f6a7b8c9_correct_legacy_environment_types.py"
Cohesion: 0.33
Nodes (3): downgrade(), Phase 2.1 — correct legacy ``environment_type`` classification. The Phase 2…, No-op: the correction is a best-effort classification, not reversible.…

### Community 226 - "DeploymentRunner"
Cohesion: 0.33
Nodes (5): DeploymentRunner, Protocol, Adapter interface implemented by real (future) and simulated runners., Return the ordered step names for this run., 2. What survives unchanged

### Community 227 - "20260923_1000-c4e2a1f7b9d3_rename_server_codenames_to_node.py"
Cohesion: 0.60
Nodes (4): downgrade(), rename ``server.*`` permission codenames to ``node.*`` The Node/Server…, _rename_permissions(), upgrade()

### Community 228 - "test_run_async_publishes_frames_scheduled_by_the_commit_hook"
Cohesion: 0.29
Nodes (5): _FakeDb, Stands in for an ``AsyncSession`` whose only job here is ``sync_session``. A…, The shape of a worker task whose last statement is a commit., test_run_async_publishes_frames_scheduled_by_the_commit_hook(), commit_then_return()

### Community 229 - "_dns_stub"
Cohesion: 0.40
Nodes (5): _dns_stub(), _fake_observe(), fixture, MonkeyPatch, Stand in for authoritative DNS in every test in this module.

### Community 230 - "redis_down"
Cohesion: 0.40
Nodes (4): _clean_memory_windows(), fixture, MonkeyPatch, redis_down()

### Community 231 - "lax"
Cohesion: 0.40
Nodes (5): lax(), fixture, Production posture: private targets are NOT allowed (resolution runs)., Simulation posture: resolution skipped, syntax still enforced., strict()

### Community 232 - "4. DNS ownership verification"
Cohesion: 0.40
Nodes (5): 4.1 The token, 4.2 The check (control-plane side), 4.3 Anti-takeover rules, 4.4 Sequence: add-domain → verified, 4. DNS ownership verification

### Community 233 - "update_docker_host"
Cohesion: 0.50
Nodes (4): patch, Partially update name / endpoint_url / tls_verify / server_id., update_docker_host(), _UpdatePerm

### Community 234 - "v1/meta.py"
Cohesion: 0.22
Nodes (9): get_meta(), DbSessionDep, get, Instance metadata: version, mode, and the caller's effective capabilities. The…, Public metadata; identity fields appear only for valid credentials., MetaOut, Public metadata schema + the canonical system-event type registry., Instance metadata. Identity fields are populated only when the caller presents… (+1 more)

### Community 235 - "_pace"
Cohesion: 0.67
Nodes (3): _pace(), Deterministic per-line delay between 0.05s and 0.35s., test_pace_bounds()

### Community 236 - "7. Secure delivery of certificate material to authorized nodes"
Cohesion: 0.33
Nodes (6): 7.2 The mechanism: reference-only op + material in the claim response, 7.3 Authorization binding, 7.4 Derived (never configured) target set, 7.5 Recovery for an interrupted delivery, 7.6 Material never persists in ordinary data, 7. Secure delivery of certificate material to authorized nodes

### Community 241 - "redact_log_event"
Cohesion: 0.18
Nodes (12): configure_logging(), _orjson_dumps(), Any, structlog processor: scrub one record before anything renders it. The pipeline…, Configure structlog + stdlib logging once at process start. Everything…, redact_log_event(), Both chains carry the processor: structlog's, and the foreign one.…, test_configure_logging_installs_redaction_on_every_logging_path() (+4 more)

## Knowledge Gaps
- **495 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+490 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2459 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `6. Tooling: reproducible e2e` connect `run_async` to `test_ws_hub.py`, `TenancyScopeError`, `client.ts`, `Conflict`, `get_sessionmaker`, `seed.py`?**
  _High betweenness centrality (0.237) - this node is a cross-community bridge._
- **Why does `useEventStream()` connect `client.ts` to `apiGet`, `Layout.tsx`, `DashboardPage.tsx`, `App.tsx`, `ServerDetailPage.tsx`, `DeploymentDetailPage.tsx`, `run_async`?**
  _High betweenness centrality (0.230) - this node is a cross-community bridge._
- **Why does `TenancyScopeError` connect `TenancyScopeError` to `test_certificates.py`, `enums.py`, `AuthContext`, `run_async`, `assert_error_code`, `deps.py`, `enrollment_service.py`, `test_tenant_isolation.py`, `get_sessionmaker`?**
  _High betweenness centrality (0.109) - this node is a cross-community bridge._
- **Are the 98 inferred relationships involving `AuthContext` (e.g. with `TenancyScopeError` and `MembershipStatus`) actually correct?**
  _`AuthContext` has 98 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `APIModel` (e.g. with `OperationSpec` and `test_specs_reject_unknown_params()`) actually correct?**
  _`APIModel` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `Server` (e.g. with `ServerStatus` and `2.3 Infrastructure — Nodes`) actually correct?**
  _`Server` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `record()` (e.g. with `AuthContext` and `client_ip()`) actually correct?**
  _`record()` has 8 INFERRED edges - model-reasoned connections that need verification._