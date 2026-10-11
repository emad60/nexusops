# Graph Report - nexusops  (2026-10-12)

## Corpus Check
- 355 files · ~391,238 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: (none) 10, .example 1, .service 1)

## Summary
- 5935 nodes · 17416 edges · 238 communities (213 shown, 25 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1417 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9554e2cd`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- apiGet
- AuthContext
- ApiKeysPage.tsx
- _proxy_ready_node
- container_service.py
- types.ts
- resolve_client_ip
- OperationType
- App.tsx
- test_agent_v2.py
- assert_error_code
- ServerDetailPage.tsx
- events.py
- client.ts
- projects.py
- models/__init__.py
- deployment_engine.py
- SimulatedDockerProvider
- enrollment_service.py
- v1/secrets.py
- test_deployments_simulated.py
- containers.py
- dashboard_summary
- test_security.py
- Domain Routing — NexusOps
- monitor_service.py
- Node & Agent Architecture
- test_agent_backoff.py
- SimulatedDeploymentRunner
- nexusops_agent.py
- apply_scope_to_session
- auth_service.py
- docker_host_service.py
- test_rate_limit.py
- docker_hosts.py
- test_ws_hub.py
- schemas/proxy.py
- v1/search.py
- sqlalchemy
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
- role_service.py
- DbDep
- proxy_service.py
- test_migration_phase21.py
- v1/auth.py
- test_agent_nginx_contract.py
- create_user
- alembic
- notification_service.py
- helpers.py
- compilerOptions
- v1/deployments.py
- register_exception_handlers
- dns_verifier.py
- test_phase2_environments.py
- route_service.py
- test_schema_redaction.py
- deps.py
- Certificate Management — NexusOps
- package.json
- core/tenancy.py
- decrypt_str
- test_nginx_renderer.py
- domain_service.py
- api service (FastAPI / uvicorn :8000)
- monitors.py
- pagination.py
- domains.py
- EventLevel
- test_phase2_secrets.py
- RolesPage.tsx
- test_schemas_server.py
- canonicalize_name
- tests/conftest.py
- list_servers
- create_user
- devDependencies
- NotFound
- enums.py
- Settings
- domain_routing.py
- validate_config
- PageParams
- org_scope
- test_phase21_secret_version_integrity.py
- AsyncSession
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- journey.spec.ts
- enqueue.py
- redact_mapping
- README.md - NexusOps overview
- organization.py
- _mutate_in_system_scope
- test_migration_phase4.py
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- LoginPage.tsx
- docker_real.py
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- ScopedSession
- publish
- Phase 5 — HTTPS, Certificates and Private-Key Delivery — Design
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
- pytest
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
- .state
- build_capabilities
- alert_service.py
- decide
- resolve_secrets_for_environment
- AgentClient
- client_ip
- nginx.py
- resolve_auth
- Container
- test_a_late_result_for_an_expired_operation_cannot_fail_a_live_route
- test_agent_contract.py
- 20261009_1000-c3d4e5f6a7b8_enforce_secret_version_integrity.py
- docs/engineering-report.md - build and verification report
- 2. Entities
- create_api_key
- scope_matches
- Platform Security Model — NexusOps
- ContainerListPage.test.tsx
- list_sessions
- _node_proxy_state
- websocket_endpoint
- _nginx_apply
- _nginx_bootstrap
- .bundle_id
- create_api_key
- UpstreamContainerOut
- maintenance.py
- test_migration_drift.py
- instant_pacing
- phase3.spec.ts
- _heartbeat
- Path
- 20261010_1200-f4a5b6c7d8e9_phase4_domains_and_routes.py
- 10. Implementation slices, acceptance criteria, tests, limitations
- NexusOps — Phase 1 (Multi-Tenancy) Report
- list_audit_logs
- RouteHeader
- 20261008_1200-b2c3d4e5f6a7_add_projects_and_environments.py
- Product Roadmap — NexusOps Multi-Tenant Platform
- Platform Vision — NexusOps
- ServerOut
- NotificationChannel
- run_async
- ProxyProvider
- ._shallow_validate
- .dispatch
- test_agent_ingestion.py
- .__init__
- _live_bundle_id
- Multi-Tenancy Architecture
- .__tablename__
- create_server
- test_notifications.py
- _FakeAsyncClient
- test_migration_phase22.py
- 9. Renewal, expiration, ownership loss, removal, revocation
- client_ip.py
- _verified_domain
- redact_log_event
- Domain Model — NexusOps as a Multi-Tenant Platform
- permissions.py
- .facts
- .apply_params
- test_capability_report_shape_is_accepted
- VerificationDecision
- register_agent_hello
- servers.py
- _run
- asyncio
- test_created_at_defaults.py
- 20261009_1300-a1b2c3d4e5f6_add_phase3_nodes_and_agent_v2.py
- test_remove_honours_force_and_never_shells
- require_permission
- _is_sensitive_key
- get_meta
- .ok
- v1/agent.py
- test_configure_logging_installs_redaction_on_every_logging_path

## God Nodes (most connected - your core abstractions)
1. `AuthContext` - 156 edges
2. `APIModel` - 145 edges
3. `Server` - 93 edges
4. `apiGet()` - 91 edges
5. `record()` - 90 edges
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
- `7. The IDOR suite` --references--> `_search_users()`  [INFERRED]
  docs/multi-tenancy.md → backend/app/api/v1/search.py
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

## Communities (238 total, 25 thin omitted)

### Community 0 - "apiGet"
Cohesion: 0.06
Nodes (90): apiDelete(), apiGet(), apiPatch(), apiPost(), ApplicationOut, ENVIRONMENT_TYPE_LABELS, EnvironmentType, IncidentEventOut (+82 more)

### Community 1 - "AuthContext"
Cohesion: 0.11
Nodes (53): AuthContext, Resolved identity plus the organization this request acts in.…, DeploymentEnvironment, A **project-scoped** deployment environment (Phase 2 promotion). The…, Any, AsyncSession, Request, UUID (+45 more)

### Community 2 - "ApiKeysPage.tsx"
Cohesion: 0.09
Nodes (19): ApiKeyOut, ApiKeysPage, ApiKeyCreatedOut, handleCopyKey(), copyText(), describeError(), EMPTY_FORM, GROUP_STYLE (+11 more)

### Community 3 - "_proxy_ready_node"
Cohesion: 0.13
Nodes (30): _create_route(), _drain(), _proxy_ready_node(), A node that stays offline accumulates one op, not one per attempt., The auto-attached monitor stays on the check → incident → notification path., The old owner's node is told to drop the name, and says when it has., The reconciler does not turn a healthy node into a status-poll loop., Claim and answer every pending operation, exactly like the agent would.… (+22 more)

### Community 4 - "container_service.py"
Cohesion: 0.09
Nodes (44): ContainerHealth, clip(), DockerProviderError, Exception, Provider abstraction for docker hosts (real daemon or simulated). Providers are…, A provider operation failed. ``str()`` is safe to show/log., Build a compact, secret-free description of a provider failure. Only the…, Truncate *text* to *limit* characters, stripping control chars. (+36 more)

### Community 5 - "types.ts"
Cohesion: 0.02
Nodes (87): AlertOut, CapabilityReport, ChannelOut, CheckOut, DeliveryOut, DeploymentLogLine, DeploymentStatus, DomainDetailOut (+79 more)

### Community 6 - "resolve_client_ip"
Cohesion: 0.28
Nodes (15): Request, Real client address for *request* per the trust model above., resolve_client_ip(), make_request(), Request, Unit tests for the chained-proxy client-IP resolver (app/core/client_ip.py)., test_all_trusted_entries_fall_back_to_peer(), test_empty_header_value_falls_back_to_peer() (+7 more)

### Community 7 - "OperationType"
Cohesion: 0.10
Nodes (23): OperationType, The whitelist. Nothing outside this enum ships as an exec surface. Each type…, Any, Validate *params* against the type's model and return the stored form.…, validate_params(), Raise a named conflict when routing may not be managed on this node., require_eligible(), MonkeyPatch (+15 more)

### Community 8 - "App.tsx"
Cohesion: 0.04
Nodes (103): DeploymentOut, Page, ProjectOut, AlertsPage, App(), AuditLogPage, ContainerListPage, DeploymentListPage (+95 more)

### Community 9 - "test_agent_v2.py"
Cohesion: 0.09
Nodes (33): agent_fixture(), _load_agent(), Any, fixture, parametrize, Agent protocol v2: honest metrics, capability detection, and the executor. The…, Phase 4 shipped three nginx ops — no file primitive, no command primitive., Trusting a private CA must not weaken verification. (+25 more)

### Community 10 - "assert_error_code"
Cohesion: 0.07
Nodes (59): Run the enclosed block with tenant filtering off (maintenance only). ``reason``…, system_scope(), assert_error_code(), Assert envelope shape + code; returns the inner error object., Regression: lockout must not leak which emails exist. After login_max_attempts…, test_locked_account_response_is_indistinguishable(), _dispatch(), _dispatch_body() (+51 more)

### Community 11 - "ServerDetailPage.tsx"
Cohesion: 0.06
Nodes (42): ContainerOut, MetricPoint, ServerDetail, ServerSummary, ChartSeries, LineChart(), LineChartProps, PAD (+34 more)

### Community 12 - "events.py"
Cohesion: 0.11
Nodes (22): _decode_cursor(), _encode_cursor(), list_event_types(), list_events(), datetime, DbSession, Depends, get (+14 more)

### Community 13 - "client.ts"
Cohesion: 0.05
Nodes (54): API_BASE, ApiError, apiRequest(), buildUrl(), extractError(), getAccessToken(), getActiveOrgId(), onActiveOrgChange() (+46 more)

### Community 14 - "projects.py"
Cohesion: 0.08
Nodes (59): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+51 more)

### Community 15 - "models/__init__.py"
Cohesion: 0.10
Nodes (52): Base, Base for all ORM models with stable constraint naming for Alembic., TimestampMixin, Application, Project, UserStatus, ApiKey, Permission (+44 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.10
Nodes (60): Queue a new deployment for an application/environment pair., trigger_deployment(), deployment_log_channel(), Deployment, DeploymentStep, DeploymentStatus, DeploymentTrigger, StepStatus (+52 more)

### Community 17 - "SimulatedDockerProvider"
Cohesion: 0.08
Nodes (33): ContainerStatus, Any, datetime, Simulated docker provider for demo and test environments. The provider is…, Plausible numbers derived from the row plus time-based sine noise., Replay registered LogEntry rows ordered by ts (tail N). ``follow`` is ignored…, Implements :class:`DockerProvider` semantics against DB rows., Attach already-fetched log rows so ``logs()`` can replay them. (+25 more)

### Community 18 - "enrollment_service.py"
Cohesion: 0.12
Nodes (29): generate_enrollment_token(), An enrollment credential (``nxk_``): single-use, short-lived, org-scoped.…, Return the active org id or raise; used by services that need it explicitly., require_org(), EnrollmentToken, One single-use credential that enrolls (or claims) exactly one node., Whether the row could still be redeemed (not a race-safe check)., _claim_and_consume() (+21 more)

### Community 19 - "v1/secrets.py"
Cohesion: 0.12
Nodes (32): create_secret(), delete_secret(), get_secret(), list_secret_versions(), list_secrets(), DbSession, delete, get (+24 more)

### Community 20 - "test_deployments_simulated.py"
Cohesion: 0.15
Nodes (29): execute_deployment(), Run one deployment to a terminal state. Never raises; safe to re-run., get_application(), get_environment(), _as_worker(), _delivery_chain(), _owner_ctx(), _queue() (+21 more)

### Community 21 - "containers.py"
Cohesion: 0.06
Nodes (63): _action_route(), _endpoint(), _container_out(), _decode_frame(), _ev(), get_container(), _like_pattern(), list_container_logs() (+55 more)

### Community 22 - "dashboard_summary"
Cohesion: 0.07
Nodes (38): get_dashboard_summary(), get_latest_server_metrics(), get_server_metrics(), CurrentUser, DbDep, Depends, get, UUID (+30 more)

### Community 23 - "test_security.py"
Cohesion: 0.07
Nodes (53): argon2, argon2_exceptions, Resolve the caller's identity only (no organization)., _resolve_identity(), Unauthorized, create_access_token(), decode_access_token(), generate_agent_token() (+45 more)

### Community 24 - "Domain Routing — NexusOps"
Cohesion: 0.11
Nodes (19): 10. Wildcards and catch-all, 11. User journey, 12. API surface, permissions, audit, 13. Monitoring tie-in, 1. Scope and current state, 2. Where nginx runs, 4.1 The token, 4.2 The check (control-plane side) (+11 more)

### Community 25 - "monitor_service.py"
Cohesion: 0.08
Nodes (57): AppError, BadRequest, Exception, Base class for expected, client-facing errors., assert_safe_url_async(), is_simulation_url(), SSRF guard applied to every operator-supplied outbound URL. Monitors and…, Async wrapper around :func:`assert_safe_url`; DNS runs off the loop. (+49 more)

### Community 26 - "Node & Agent Architecture"
Cohesion: 0.09
Nodes (22): install_hint(), The one-liner an operator pastes, without the raw token in argv. The token…, 1. Scope and stance, 3.2 Enrollment v2, 3.3 Token storage & rotation with dual-token grace, 3.4 Revocation semantics — fixing the 401 hot-loop, 3.5 Reconnect / offline states, 3. Agent lifecycle (+14 more)

### Community 27 - "test_agent_backoff.py"
Cohesion: 0.14
Nodes (22): agent_fixture(), _install_sleep(), fake_sleep(), _load_agent(), _patch_host(), Any, fixture, MonkeyPatch (+14 more)

### Community 28 - "SimulatedDeploymentRunner"
Cohesion: 0.11
Nodes (41): LogLevel, _commit_short(), _pace(), Exception, Deployment runner port plus a faithful simulated implementation.…, Stream output lines for *step_name*; raise StepFailure to fail it., Staged docker-style simulation used by v1 deployments., Deterministic per-line delay between 0.05s and 0.35s. (+33 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.08
Nodes (37): build_facts(), build_heartbeat(), _build_hello_payload(), cpu_percent_since(), disk_stats(), _enroll(), _interruptible_sleep(), load1() (+29 more)

### Community 30 - "apply_scope_to_session"
Cohesion: 0.07
Nodes (46): dispose_engine(), get_sessionmaker(), async_sessionmaker, AsyncSession, apply_scope_to_session(), Push the current scope onto *db*'s connection immediately. Needed only when a…, _admin_dsn(), _clean_slate() (+38 more)

### Community 31 - "auth_service.py"
Cohesion: 0.10
Nodes (48): active_memberships(), The user's memberships in non-suspended organizations, oldest first. Reads only…, System scope bound to *db*, for rows that have no organization. Used by exactly…, system_write_scope(), AuditResult, _audit(), _auth_event_scope(), _bootstrap_organization() (+40 more)

### Community 32 - "docker_host_service.py"
Cohesion: 0.13
Nodes (35): paginate(), AsyncSession, Execute *stmt* with limit/offset and return ``(rows, total)``., DockerHostStatus, DockerHost, _assert_endpoint_allowed(), _assert_name_free(), create_host() (+27 more)

### Community 33 - "test_rate_limit.py"
Cohesion: 0.18
Nodes (16): RateLimited, _memory_count_and_ttl(), rate_limit(), Fixed-window counter backed by process memory. Returns (count, ttl)., Return a dependency enforcing *limit* requests per window per IP. With…, _clean_memory_windows(), _FakeRequest, fixture (+8 more)

### Community 34 - "docker_hosts.py"
Cohesion: 0.07
Nodes (55): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+47 more)

### Community 35 - "test_ws_hub.py"
Cohesion: 0.06
Nodes (57): _authenticate_api_key(), _authenticate_jwt(), _bind_organization(), _close_socket(), Connection, _frame_org(), Hub, _load_permissions() (+49 more)

### Community 36 - "schemas/proxy.py"
Cohesion: 0.11
Nodes (25): bundle_summary(), BundleFile, fingerprint_files(), is_allowed_bundle_path(), NginxBootstrapParams, NginxBundle, NginxStatusParams, Any (+17 more)

### Community 37 - "v1/search.py"
Cohesion: 0.12
Nodes (32): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+24 more)

### Community 38 - "sqlalchemy"
Cohesion: 0.10
Nodes (34): big_serial_pk(), json_column(), org_id_column(), OrgScoped, datetime, UUID, Declarative base, shared mixins and column helpers., Identity PK for very high-volume tables (metrics, logs). (+26 more)

### Community 39 - "v1/channels.py"
Cohesion: 0.10
Nodes (40): create_channel(), delete_channel(), get_channel(), list_channels(), list_deliveries(), DbDep, delete, Depends (+32 more)

### Community 40 - "DockerProvider"
Cohesion: 0.09
Nodes (12): DockerProvider, Any, datetime, Protocol, List containers visible to the provider., Inspect a single container by id (short ids allowed)., List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``., List volumes: keys ``name``, ``driver``, ``mountpoint``. (+4 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.09
Nodes (47): CheckResult, coerce_headers(), _decode(), HTTPMonitorTransport, Any, BaseException, Pluggable monitor check transports (real HTTP + deterministic simulator). A…, Deterministic fake checker for ``sim://`` monitors and demo environments.… (+39 more)

### Community 42 - "Deployment Architecture — NexusOps (target state)"
Cohesion: 0.10
Nodes (21): DeploymentRunner, Protocol, Adapter interface implemented by real (future) and simulated runners., Return the ordered step names for this run., 10. Events and WS during runs, 12. Rollback semantics (existing behavior kept), 13. The simulated runner stays — labeled, 14. Open questions (+13 more)

### Community 43 - "AuthContext.tsx"
Cohesion: 0.02
Nodes (83): Membership, SearchResult, User, AuthContext, AuthProvider(), AuthState, isOrgSelectionError(), MeResponse (+75 more)

### Community 44 - "v1/health.py"
Cohesion: 0.20
Nodes (13): liveness(), get, Response, Health probes: liveness (always cheap) and readiness (checks dependencies).…, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness(), HealthOut (+5 more)

### Community 45 - "test_permissions.py"
Cohesion: 0.17
Nodes (9): _auth_context(), Unit tests for the permission registry, scope matching and RBAC gate., A fake context in the given organization. ``membership_status=None`` models a…, test_api_key_scope_intersects_role_permissions(), test_membership_is_required_for_authority(), test_plain_user_without_permissions_is_denied(), test_superadmin_bypasses_everything(), test_superadmin_owned_api_key_is_limited_to_its_scope() (+1 more)

### Community 46 - "routes.py"
Cohesion: 0.13
Nodes (33): create_route(), delete_route(), disable_route(), _domain_status(), enable_route(), get_route(), list_routes(), AsyncSession (+25 more)

### Community 47 - "test_phase3_nodes.py"
Cohesion: 0.15
Nodes (33): _create_token(), _dispatch(), _enroll(), _enrolled_node(), _load_agent_module(), _mutate_in_system_scope(), Phase 3 — Nodes & Agent v2 end-to-end behaviour. Grouped by the question each…, Import the shipped agent source (sync, so async tests never touch Path). (+25 more)

### Community 48 - "test_ssrf.py"
Cohesion: 0.08
Nodes (56): UnprocessableEntity, assert_safe_tcp_endpoint(), assert_safe_url(), _is_forbidden_address(), ValueError, _raise_block(), Validate *url* for outbound requests; return the parsed URL or raise 422.…, Validate a ``tcp://`` docker host endpoint for outbound connection. Docker… (+48 more)

### Community 49 - "secret_service.py"
Cohesion: 0.09
Nodes (51): digest_of(), encrypt_str(), Short server-verifiable digest used for change detection display. HMAC-SHA256…, An encrypted configuration value, scoped to org, project or environment.…, One immutable value of a :class:`Secret` — append-only history. A row is…, Secret, SecretVersion, _actor_type() (+43 more)

### Community 50 - "role_service.py"
Cohesion: 0.07
Nodes (53): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, delete, get (+45 more)

### Community 51 - "DbDep"
Cohesion: 0.10
Nodes (34): apply_node_proxy_config(), create_server(), delete_server(), node_proxy_status(), node_route_targets(), DbDep, delete, patch (+26 more)

### Community 52 - "proxy_service.py"
Cohesion: 0.06
Nodes (88): ListenerOwnership, ProxyApplyOutcome, Terminal outcome of one ``nginx.apply`` operation on a node., Who holds one required listener port, per the node's pre-flight. The…, Server, Operation, One whitelisted action for one node, with a CAS lifecycle. ``attempts`` is…, NodeProxyCapabilityOut (+80 more)

### Community 53 - "test_migration_phase21.py"
Cohesion: 0.22
Nodes (9): Phase 2.1 corrective migration: legacy ``environment_type`` classification.…, Every case is classified as documented, ids and ownership intact., An explicit non-DEV classification survives the corrective migration. The…, The correction is part of ``head`` and adds no extra Alembic head., Insert one legacy environment per case, in two organizations., _seed_typed_environments(), test_corrective_migration_is_reachable_from_head(), test_corrects_legacy_environment_types() (+1 more)

### Community 54 - "v1/auth.py"
Cohesion: 0.10
Nodes (40): change_password(), _clear_refresh_cookie(), _cookies_secure(), login(), logout(), me(), _optional_actor(), AsyncSession (+32 more)

### Community 55 - "test_agent_nginx_contract.py"
Cohesion: 0.08
Nodes (53): _agent_bundle(), agent_fixture(), _bootstrap_fixture(), _load_agent(), Any, fixture, parametrize, Path (+45 more)

### Community 56 - "create_user"
Cohesion: 0.18
Nodes (18): create_user(), deactivate_user(), get_user(), list_users(), CurrentUser, DbSessionDep, delete, get (+10 more)

### Community 57 - "alembic"
Cohesion: 0.04
Nodes (22): alembic, Alembic environment: metadata comes from app.models, URL from app settings., Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online(), downgrade(), rename ``server.*`` permission codenames to ``node.*`` The Node/Server… (+14 more)

### Community 58 - "notification_service.py"
Cohesion: 0.12
Nodes (42): DeliveryStatus, NotificationDelivery, _as_uuid(), _attempt_delivery(), _audit(), create_channel(), decode_delivery_cursor(), decrypt_channel_config() (+34 more)

### Community 59 - "helpers.py"
Cohesion: 0.07
Nodes (56): bearer(), cookie_attributes(), login_account(), login_headers(), Any, AsyncClient, Response, Pure helpers for journey tests: payloads, auth shortcuts, cookie parsing. (+48 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "v1/deployments.py"
Cohesion: 0.11
Nodes (36): _attribute_step_idx(), cancel_deployment(), _emails_for(), get_deployment(), list_application_deployments(), list_deployment_logs(), _list_deployments(), _parse_sort() (+28 more)

### Community 62 - "register_exception_handlers"
Cohesion: 0.14
Nodes (12): _error_payload(), FastAPI, Request, register_exception_handlers(), handle_app_error(), handle_http_exception(), handle_unexpected(), handle_validation_error() (+4 more)

### Community 63 - "dns_verifier.py"
Cohesion: 0.13
Nodes (18): apex_of(), The name a wildcard Domain is anchored at (``*.example.com`` →…, The exact TXT owner name a user must publish at their provider., verification_record_name(), _discover_nameservers(), _normalise_ns(), observe(), Observer (+10 more)

### Community 64 - "test_phase2_environments.py"
Cohesion: 0.18
Nodes (22): _environment(), _project(), parametrize, Phase 2: project-scoped environments, config layering, and their isolation. The…, Uniqueness is ``(project_id, slug)`` — not instance-wide., The update path is validated too (the pre-Phase-2 gap)., Knowing an environment UUID is not access: the project link must hold., Another tenant cannot reach the project, its environments, or its detail. (+14 more)

### Community 65 - "route_service.py"
Cohesion: 0.10
Nodes (50): Last nginx apply outcome for a route, as reported by its node's agent.…, RouteConfigState, One hostname+path served from one container on one node. Relationship rules the…, Route, mark_removal_requested(), Record that *route* must leave its node's configuration. True when new. Called…, _actor(), _apply_or_defer() (+42 more)

### Community 66 - "test_schema_redaction.py"
Cohesion: 0.18
Nodes (17): is_sensitive_header(), mask_sensitive_headers(), True when *name* looks like it carries a credential (Authorization etc.)., Return a copy of *headers* with sensitive values replaced by a mask., mask_target(), Human-readable masked target safe to expose over the API. For webhook families…, _monitor_out(), Outbound-schema redaction: monitor probe credentials and webhook targets.… (+9 more)

### Community 67 - "deps.py"
Cohesion: 0.04
Nodes (96): _database_url(), Migrations run as the table **owner**, never as the application role. The owner…, _load_organization(), Organization, FastAPI dependencies: database session, authenticated tenant context, RBAC…, API key routes — self-service management of the caller's own machine…, Audit log API. Strictly read-only: the table is append-only by design., Instance metadata: version, mode, and the caller's effective capabilities. The… (+88 more)

### Community 68 - "Certificate Management — NexusOps"
Cohesion: 0.13
Nodes (15): 10. Status/expiry tracking and monitor tie-in, 12. Audit and events, 13. Non-goals, 3. API surface and permissions, 4.1 DNS-01 first (the default and the wedge), 4.2 DNSProvider interface, 4.3 ACME account and directory, 4.4 HTTP-01 via node nginx (later fallback) (+7 more)

### Community 69 - "package.json"
Cohesion: 0.13
Nodes (15): name, private, type, version, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom (+7 more)

### Community 70 - "core/tenancy.py"
Cohesion: 0.11
Nodes (29): _apply_scope_guc(), _desired_guc(), _guard(), _has_org_predicate(), install_tenancy_guards(), _mappers_of(), _org_scoped_classes(), org_scoped_table_names() (+21 more)

### Community 71 - "decrypt_str"
Cohesion: 0.10
Nodes (26): decrypt_str(), _fernet(), _create(), _environment_config(), Secrets: metadata-only reads, rotation versioning, deploy-time resolution., Project → application → environment carrying *config*; returns its id., A reference naming no secret must abort, not resolve to an empty value.…, A row this ENCRYPTION_KEY cannot decrypt must abort, not yield ``""``. (+18 more)

### Community 72 - "test_nginx_renderer.py"
Cohesion: 0.12
Nodes (38): NginxProvider, ValueError, The only production provider in Phase 4., Where a route's fragment lands, so the service can name it in events., Rendering refused the input. Always a bug or a corrupt row, never a leak., RenderError, NginxApplyParams, One validated bundle to apply atomically. (+30 more)

### Community 73 - "domain_service.py"
Cohesion: 0.10
Nodes (42): DomainStatus, Ownership-verification lifecycle of a Domain (domain-routing.md §4). ``STALE``…, Domain, One DNS name an organization is proving it controls. ``name`` is canonical (see…, _actor(), apply_decision(), _bad_name(), claim_verified_name() (+34 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "monitors.py"
Cohesion: 0.09
Nodes (48): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+40 more)

### Community 76 - "pagination.py"
Cohesion: 0.14
Nodes (25): Cursor, cursor_params(), CursorPage, CursorParams, decode_cursor(), encode_cursor(), BaseModel, datetime (+17 more)

### Community 77 - "domains.py"
Cohesion: 0.12
Nodes (38): create_domain(), delete_domain(), _enqueue_verification(), get_domain(), list_domain_routes(), list_domains(), _project_names(), alias (+30 more)

### Community 78 - "EventLevel"
Cohesion: 0.09
Nodes (57): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+49 more)

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
Nodes (33): canonicalize_name(), canonicalize_path(), _check_labels(), _check_not_ip(), hostname_is_covered(), _idna(), InvalidName, is_valid_path() (+25 more)

### Community 83 - "tests/conftest.py"
Cohesion: 0.22
Nodes (7): configure_test_env(), Test bootstrap: pin every cached setting BEFORE the first ``app`` import. The…, KEY=VALUE pairs from the repo .env (first definition wins); never logged., Export the exact settings the app caches; host values cannot leak through., _read_dot_env(), base64, os

### Community 84 - "list_servers"
Cohesion: 0.14
Nodes (16): get_server(), list_servers(), list_tags(), Depends, get, ReadCtx, All tags with their server usage counts., Full server view with recent timeline events and container counts. (+8 more)

### Community 85 - "create_user"
Cohesion: 0.11
Nodes (36): _apply_deactivation(), _assert_not_last_active_member(), _assert_not_last_active_superadmin(), create_user(), deactivate_user(), get_by_email(), get_member(), get_user() (+28 more)

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "NotFound"
Cohesion: 0.09
Nodes (48): Conflict, NotFound, OperationStatus, Lifecycle of one node operation (node-agent-architecture.md §5.1).…, OperationCreate, Request one whitelisted action on one node., _active_org(), _bounded() (+40 more)

### Community 88 - "enums.py"
Cohesion: 0.09
Nodes (34): ActorType, AlertSeverity, LogSource, MetricGranularity, MonitorTargetType, OrganizationStatus, Closed registries of domain enumerations. Member names equal their values…, String enum; member names equal values so name/value storage never disagrees. (+26 more)

### Community 89 - "Settings"
Cohesion: 0.14
Nodes (6): field_validator, model_validator, Username from :attr:`database_url`, or ``None`` if it is unparseable., Validated application settings (loaded from environment / .env)., Settings, BaseSettings

### Community 90 - "domain_routing.py"
Cohesion: 0.17
Nodes (20): The honest state of a route that left the desired tree but is not gone. One…, removal_requested_detail(), _affected_node_ids(), _apply_for_node(), _audit_action(), datetime, UUID, Domain verification and routing sweeps. Two properties shape this module: * **A… (+12 more)

### Community 91 - "validate_config"
Cohesion: 0.07
Nodes (29): _normalise_environment_type(), field_validator, field_validator, collect_secret_refs(), walk(), ConfigValidationError, merge_config(), Any (+21 more)

### Community 92 - "PageParams"
Cohesion: 0.15
Nodes (27): list_alerts(), mark_all_read(), mark_read(), CurrentUser, DbDep, Depends, get, post (+19 more)

### Community 93 - "org_scope"
Cohesion: 0.08
Nodes (52): current_org(), current_scope(), org_scope(), UUID, Raised when a unit of work touches tenant data with no valid org scope. This is…, The organization this unit of work is acting for, if any., ``'org'``, ``'system'`` or ``'unset'``., Run the enclosed block as a single organization. Nesting the *same* org is a… (+44 more)

### Community 94 - "test_phase21_secret_version_integrity.py"
Cohesion: 0.18
Nodes (18): _app_role_dsn(), _owner_dsn(), _probe(), Phase 2.1 — ``secret_versions`` is append-only in the **database**, not just in…, Immutability is a database guarantee, not merely a missing code path. The owner…, The legitimate append paths keep working under the guard., The documented deletion policy: purging a Secret cascades its history., RLS is preserved: another tenant cannot see a version row, even by id. (+10 more)

### Community 95 - "AsyncSession"
Cohesion: 0.13
Nodes (26): _detail(), AsyncSession, _actor_kwargs(), container_counts(), delete_server(), get_server(), list_servers(), _order_clause() (+18 more)

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
Cohesion: 0.39
Nodes (8): after_commit(), _on_commit(), _on_rollback(), Any, AsyncSession, Deferred Celery handoff: enqueue only after the creating transaction commits. A…, Run ``factory`` once the current transaction commits. ``label`` names the work…, _run()

### Community 100 - "redact_mapping"
Cohesion: 0.10
Nodes (31): Return a copy of *data* with sensitive values replaced, at any depth. Two…, redact_mapping(), parametrize, Unit tests for app.core.logging redaction (pure functions only)., No sensitive key name involved: the PEM armor is the only signal., Lists of dicts holding further lists — the shape an agent report takes., The key-name rule still applies at depth, not just at the top level., Only the key is replaced: the reason an operator reads the row is kept. (+23 more)

### Community 102 - "organization.py"
Cohesion: 0.12
Nodes (23): create_organization(), list_my_organizations(), CurrentUser, DbSessionDep, get, IdentityUser, patch, post (+15 more)

### Community 103 - "_mutate_in_system_scope"
Cohesion: 0.11
Nodes (26): task, Re-prove control of every domain whose next check is due. Covers three cases…, Keep every routed node's live configuration matching the desired bundle. One…, sweep_domains(), sweep_routes(), _flip_name_to(), _live_operations(), _mutate_in_system_scope() (+18 more)

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
Nodes (30): ContainerInfo, ContainerStats, LogLine, Normalized view of a container as reported by any provider., Point-in-time resource usage snapshot., One parsed log record from a container log stream., _as_float(), _compute_stats() (+22 more)

### Community 109 - "Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)"
Cohesion: 0.25
Nodes (9): API keys (X-API-Key, nxo_..., scope intersection), First boot sequence (api entrypoint migrates, compose never seeds), Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test), Makefile workflows (up/test/lint/typecheck/migrate/seed), HIGH finding: API-key scope bypass for superadmin-owned keys (fixed: scope intersection first), Security audit 2026-09 (26 raw findings -> 20 confirmed, all fixed), HIGH finding: known seed superadmin + API key backdoor (fixed: NEXUSOPS_ALLOW_SEED opt-in, one-time password), Threat model (edge attacker, malicious agent, curious operator, leaked token, SSRF) (+1 more)

### Community 110 - "ScopedSession"
Cohesion: 0.19
Nodes (3): A session that enters its tenancy scope around each operation. A fixture cannot…, ScopedSession, 3. The session guard (the mechanical layer)

### Community 111 - "publish"
Cohesion: 0.11
Nodes (36): _after_commit_publish(), _after_rollback_drop(), publish(), _publish_after_commit(), _publish_redis(), Any, AsyncSession, UUID (+28 more)

### Community 112 - "Phase 5 — HTTPS, Certificates and Private-Key Delivery — Design"
Cohesion: 0.10
Nodes (20): 1.2 Phase 5 in one sentence, 1.3 Trust boundaries Phase 5 adds, 1.4 Non-goals for Phase 5, 1.5 Trust concentration: centralized key custody, accepted **conditionally** (decided), 1. Architecture and trust boundaries, 4.1 Codenames, 4.2 Per-type permission and capability gating, 4.3 Tenant isolation (+12 more)

### Community 113 - "dnsmock.py"
Cohesion: 0.11
Nodes (25): resolver(), answer(), encode_name(), encode_txt(), forward(), main(), parse_question(), TXT rdata: one or more length-prefixed strings, each ≤ 255 bytes. (+17 more)

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "APIModel"
Cohesion: 0.03
Nodes (96): User management routes (user.read / user.manage), scoped to the active tenant.…, AgentContainerPortIn, AgentEnrollIn, AgentEnrollOut, AgentHelloOut, AgentTokenRotation, Agent-facing schemas. Payloads are data only — never executed. Wire protocol v2…, Tells the agent how often to report and what protocol it negotiated. (+88 more)

### Community 116 - "test_tenancy_allowlist.py"
Cohesion: 0.20
Nodes (14): AST, _actual_callers(), _calls_system_scope(), _module_path(), Path, The system-scope allowlist is the only fence around the tenancy carve-out.…, Every module that could open a system scope: ``app/`` plus the scripts., No module may lift tenant isolation without being named in the list. (+6 more)

### Community 117 - "_alembic_config"
Cohesion: 0.15
Nodes (15): _alembic_config(), _at_revision(), _migration_dsn(), Run one Alembic direction against ``database`` through the app's settings path.…, Move ``database`` *back* to ``revision``. The same code path a deployment uses…, Phase 2 adds one migration; heads must not fork., _run_downgrade(), test_exactly_one_alembic_head() (+7 more)

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
Nodes (59): error_of(), Unwrap an API error envelope., A valid POST /servers body with per-test overrides., server_payload(), test_token_cannot_claim_a_foreign_tenants_node(), test_v1_heartbeat_keeps_the_204_contract(), Regression: a superadmin-owned key is still limited to its scope list. The…, test_scoped_api_key_cannot_exceed_its_grant() (+51 more)

### Community 123 - "pytest"
Cohesion: 0.15
Nodes (21): alembic_config, alembic_script, Phase 2 migration (`b2c3d4e5f6a7`) against realistic legacy data. The promotion…, Upgrade ``database`` to ``revision``., The pre-Phase-2 shapes: application-scoped environments, per-app dupes., A fresh database reaches the same shape the models describe., _run_migration(), _seed_legacy_data() (+13 more)

### Community 124 - "middleware.py"
Cohesion: 0.13
Nodes (20): ASGIApp, AccessLogMiddleware, HTTP middleware: request ids, security headers, structured access logs., Baseline hardening headers on every API response., RequestIDMiddleware, SecurityHeadersMiddleware, create_app(), _app_for_environment() (+12 more)

### Community 125 - "OperationError"
Cohesion: 0.15
Nodes (17): _demux_docker_stream(), _docker_error(), execute_operation(), OperationError, _process_pending_operations(), Exception, A stable, sanitized failure contract for the control plane., Re-validate the operation's parameters locally, against a closed shape. (+9 more)

### Community 126 - "list_operations"
Cohesion: 0.18
Nodes (18): cancel_operation(), create_operation(), get_operation(), list_operations(), DbDep, Depends, get, post (+10 more)

### Community 127 - "test_phase4_routing.py"
Cohesion: 0.11
Nodes (23): _create_domain(), _dns_stub(), _fake_observe(), fixture, parametrize, Phase 4 through the real HTTP surface, workers and agent contract. The journey…, Stand in for authoritative DNS in every test in this module., The polymorphic model must not disturb the original target shape. (+15 more)

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
Cohesion: 0.20
Nodes (10): _listener_ownership(), _listening_ports(), nginx_capability(), _nginx_owned_ports(), _nginx_version(), ``nginx -v`` prints its version to stderr; bounded and non-shell., TCP ports in LISTEN state, read from ``/proc`` (no shell, no tooling). ``None``…, Ports declared by ``listen`` directives in the *loaded* configuration. ``nginx… (+2 more)

### Community 153 - "DockerHostsPage.test.tsx"
Cohesion: 0.18
Nodes (8): DockerHostOut, ApiError, failingHost, host, hostsPage, mockCountApi(), server, serversPage

### Community 154 - "nexusops-draft.mjs"
Cohesion: 0.40
Nodes (4): DOCS, meta, SPINE, VERIFY_RULES

### Community 155 - "notification_sender.py"
Cohesion: 0.17
Nodes (15): NotificationError, Any, BaseException, Exception, Low-level notification transports: SMTP email and outgoing webhooks. These…, POST *payload* as JSON to *url*; 2xx is success, anything else raises. Response…, Raised when a delivery attempt fails. Message is safe to persist., Bounded, single-line, content-free error reason. (+7 more)

### Community 156 - "nexusops-challenge.mjs"
Cohesion: 0.33
Nodes (5): CHALLENGE_COMMON, meta, RESEARCH_COMMON, SCHEMA, TASKS

### Community 157 - "Secrets Architecture"
Cohesion: 0.13
Nodes (15): 10. Resolution flow at deploy time, 2.1 Resolution runs inside org scope, 2.2 Migration mapping (applied by `b2c3d4e5f6a7`), 2. Scope model (org / project / environment layering) — **shipped**, 3.1 What this fixed, 3. SecretVersion — append-only history (**shipped in Phase 2**), 4.1 Audit event at resolution time, 4. Resolution authorization (+7 more)

### Community 158 - "test_schemas_agent.py"
Cohesion: 0.10
Nodes (38): AgentContainerIn, AgentHeartbeatIn, AgentHelloIn, Any, field_validator, Observed container state reported by an agent., Periodic metrics + observed containers from an enrolled agent. Network counters…, First contact from an agent after enrollment; fills static host facts. (+30 more)

### Community 159 - ".state"
Cohesion: 0.12
Nodes (16): computed_field, Derived lifecycle state: revoked wins over used wins over expired., 2. Certificate entity, 2.1 The six stages, kept distinct, 2.2 Certificate generation state machine, 2.3 Delivery/activation state machine (per certificate × node), 2.4 End-to-end sequence (control plane is the ACME client), 2.5 Failure at any stage (+8 more)

### Community 160 - "build_capabilities"
Cohesion: 0.13
Nodes (15): build_capabilities(), collect_container_stats(), collect_containers(), _container_ports(), _container_status(), docker_capability(), _docker_request(), _docker_socket() (+7 more)

### Community 161 - "alert_service.py"
Cohesion: 0.22
Nodes (13): create_alert(), get_alert(), mark_all_read(), mark_read(), AsyncSession, UUID, Alert inbox: insert-only creation plus read/unread bookkeeping., Map a system event type to the alert severity it deserves. (+5 more)

### Community 162 - "decide"
Cohesion: 0.23
Nodes (18): decide(), matches_token(), Constant-time comparison of the observed TXT values against the token. TXT…, Turn one observation into the verification outcome — pure, no I/O.…, observation(), parametrize, The verification decision: every outcome, without a network. ``decide`` is…, test_a_sweep_invalidates_a_changed_delegation_even_with_the_token() (+10 more)

### Community 163 - "resolve_secrets_for_environment"
Cohesion: 0.19
Nodes (13): Exception, A ``${secret:KEY}`` reference could not be resolved. Fail-closed. Carries…, One successfully resolved reference: metadata for audit, no value., Outcome of resolving an environment's config references., Resolve every ``${secret:KEY}`` reference an environment's config names.…, resolve_secrets_for_environment(), ResolvedSecrets, SecretReference (+5 more)

### Community 164 - "AgentClient"
Cohesion: 0.15
Nodes (8): AgentClient, _docker_raw(), A verifying TLS context. Verification is never disabled. A private/self-hosted…, Refuse to send credentials over plain HTTP to a non-loopback server. The…, One raw Docker API call; returns ``(status, body_bytes)``., _tls_context(), _UnixHTTPConnection, SSLContext

### Community 165 - "client_ip"
Cohesion: 0.31
Nodes (9): client_ip(), _enforce(), node_rate_limit(), _dependency(), Request, _dependency(), Return a dependency keyed on the **authenticated node**, not the IP. A fleet…, Best-effort client IP; honours X-Forwarded-For from trusted proxies. Delegates… (+1 more)

### Community 166 - "nginx.py"
Cohesion: 0.13
Nodes (23): _header_lines(), _quote(), _rate_zone(), NginxProvider — a pure, deterministic renderer plus the two op wrappers.…, Validate the route's headers and split them by destination., Wrap an already-validated value in quotes for a template slot. Values reaching…, The ``limit_req_zone`` declaration for a rate-limited route., A fixed host redirect, or ``None`` for a normal proxying route. (+15 more)

### Community 167 - "resolve_auth"
Cohesion: 0.08
Nodes (32): _attach_organization(), get_current_user(), get_identity(), get_optional_user(), _load_permissions(), membership_for_org(), _org_id_from_header(), AsyncSession (+24 more)

### Community 168 - "Container"
Cohesion: 0.09
Nodes (26): Container, Observed container state mirrored from an agent or docker provider., Make a container row visible to this provider instance., ingest_provider_lines(), publish_log_line(), Best-effort publish of one frame to the container's Redis channel., Persist provider lines for a container AND fan them out to Redis. Used by the…, _apply_agent_entry() (+18 more)

### Community 169 - "test_a_late_result_for_an_expired_operation_cannot_fail_a_live_route"
Cohesion: 0.13
Nodes (23): _agent_result_body(), _audits(), _claim(), _event_types(), The same delivery twice: one apply, one set of events, one audit row., A report that contradicts what already happened is ignored, not applied., A report that arrives after its operation expired changes nothing at all., The result body the agent sends for one operation it claimed. Shared by the… (+15 more)

### Community 170 - "test_agent_contract.py"
Cohesion: 0.20
Nodes (15): agent_fixture(), _load_agent(), _patch_stats(), Any, fixture, MonkeyPatch, Contract tests: the shipped agent's payloads must satisfy the ingest schemas.…, One-shot docker stats reduce to cpu/mem/limit fields the schema accepts, with… (+7 more)

### Community 171 - "20261009_1000-c3d4e5f6a7b8_enforce_secret_version_integrity.py"
Cohesion: 0.48
Nodes (6): _clear_app_role_guc(), downgrade(), Phase 2.1 — enforce append-only ``secret_versions`` in the database. Phase 2…, Publish the app-role name to the migration GUC the revoke block reads., _set_app_role_in_guc(), upgrade()

### Community 172 - "docs/engineering-report.md - build and verification report"
Cohesion: 0.24
Nodes (12): docker-compose.dev.yml - dev overlay, docker-compose.docker-sock.yml - docker socket override, docker-compose.yml - full stack definition, docs/agent.md - agent guide, docs/api.md - API guide, Append-only audit log (Postgres BEFORE UPDATE OR DELETE trigger), docs/deployment.md - deployment and operations guide, docs/development.md - developer guide (+4 more)

### Community 173 - "2. Entities"
Cohesion: 0.25
Nodes (8): 2.1.1 ApiKey org binding detail, 2.2.1 Environment promotion detail — **shipped in Phase 2**, 2.2 Delivery (existing models, extended), 2.4 Routing & TLS (new subsystem), 2.5 Secrets (re-scoped — **shipped in Phase 2**), 2.6 Observability (existing, org-scoped via parents), 2.7 Backups, connections, billing (new subsystems, design-only in early phases), 2. Entities

### Community 174 - "create_api_key"
Cohesion: 0.16
Nodes (17): create_api_key(), list_api_keys(), CurrentUser, DbSessionDep, delete, get, post, Request (+9 more)

### Community 175 - "scope_matches"
Cohesion: 0.29
Nodes (6): Check an API-key scope list against a required permission. Supports exact match…, scope_matches(), parametrize, test_scope_matches_truth_table(), 5. API keys, 2.1 Identity & tenancy (new)

### Community 176 - "Platform Security Model — NexusOps"
Cohesion: 0.11
Nodes (19): make(), 10.1 Node revocation playbook (compromised node / leaked agent token), 10.2 Key compromise playbook, 10. Incident response, 1.1 Real vs simulated today (do not mistake one for the other), 1. Scope, stance, and simulation honesty, 2. Assets, 3. Trust boundaries (+11 more)

### Community 177 - "ContainerListPage.test.tsx"
Cohesion: 0.29
Nodes (3): ApiError, server, serversPage

### Community 178 - "list_sessions"
Cohesion: 0.20
Nodes (11): list_sessions(), CurrentUser, DbSessionDep, delete, get, Request, UUID, Active sessions of this organization's members. Defaults to the caller's own;… (+3 more)

### Community 179 - "_node_proxy_state"
Cohesion: 0.16
Nodes (21): _converged_node_with_a_route(), _hello_elsewhere(), _mark_reconcile_required_elsewhere(), _node_proxy_state(), _node_session(), _pause_render(), MonkeyPatch, One worker unit of work: a fresh session, its org scope, and its node. (+13 more)

### Community 180 - "websocket_endpoint"
Cohesion: 0.67
Nodes (3): websocket, Hand the socket to the hub (auth handshake handled there)., websocket_endpoint()

### Community 181 - "_nginx_apply"
Cohesion: 0.12
Nodes (24): _fsync_dir(), _nginx_apply(), Materialize the bundle under ``staged/<id>/`` and return that directory.…, Build a self-contained config for ``nginx -t`` over the staged tree. The…, Move the staged tree over the live one, keeping the previous as backup., Put the previous known-good tree back. Returns whether it was possible., Stage → validate → swap → reload, with a rollback on a failed reload., Persist the last apply outcome atomically (temp + rename). (+16 more)

### Community 182 - "_nginx_bootstrap"
Cohesion: 0.11
Nodes (23): _insert_http_includes(), _nginx_binary(), _nginx_bootstrap(), _nginx_config_test(), _nginx_failure_summary(), _nginx_running(), _nginx_status(), _pid_alive() (+15 more)

### Community 183 - ".bundle_id"
Cohesion: 0.18
Nodes (10): 3.1 Domain, 3.2 Route, 3. Entities (per domain-model.md §2.4), 5. ProxyProvider interface, 8.1 Binding rules, 8.2 Certificate selection rule (this doc owns it) — **Phase 5 target design**, 8.3 Re-render triggers, 8.5 How deployments hook routing (post-deploy route sync) (+2 more)

### Community 184 - "create_api_key"
Cohesion: 0.25
Nodes (11): create_api_key(), list_api_keys(), AsyncSession, Request, UUID, Live (non-revoked) keys owned by *owner_id*, newest first., Revoke a key owned by *owner_id*. Foreign keys look like NotFound (no leak)., Revoke every live key of a user (used on deactivation). Returns count. (+3 more)

### Community 185 - "UpstreamContainerOut"
Cohesion: 0.20
Nodes (11): One genuinely usable published port reported by the node's agent., A container that can actually back a route on this node., UpstreamContainerOut, UpstreamPortOut, container_out(), The address nginx should proxy to for one published binding. A wildcard bind…, The published ports of *container* that a route may actually point at. Honest…, Containers on *node_id* that can back a route, for the route editor. (+3 more)

### Community 186 - "maintenance.py"
Cohesion: 0.12
Nodes (33): _run(), _candidates(), _run(), _run(), _run(), _collect_logs(), _run(), Housekeeping: metric rollups, log trims, notification retries, session expiry. (+25 more)

### Community 187 - "test_migration_drift.py"
Cohesion: 0.25
Nodes (7): alembic_autogenerate, alembic_migration, Model / migration drift: the schema in the database must match the models.…, ``Base.metadata`` and the migrated database must describe the same schema., The DB whitelist and ``OperationType`` are the same closed set. The migration…, test_models_and_migrations_do_not_drift(), test_operations_type_check_matches_the_enum()

### Community 188 - "instant_pacing"
Cohesion: 0.40
Nodes (4): instant_pacing(), fixture, MonkeyPatch, Remove the per-line sleeps; pacing bounds are asserted separately.

### Community 189 - "phase3.spec.ts"
Cohesion: 0.15
Nodes (10): frontend_e2e_fixtures_expect, AGENT, NodeDetail, OperationRow, REPO_ROOT, ref_node_child_process, ref_node_fs, ref_node_os (+2 more)

### Community 190 - "_heartbeat"
Cohesion: 0.24
Nodes (12): _container_id(), _create_node(), _heartbeat(), heartbeat_payload(), test_a_container_on_another_node_is_refused(), test_a_container_without_published_ports_offers_nothing(), test_a_listener_conflict_is_named_precisely(), test_a_stopped_container_cannot_be_enabled() (+4 more)

### Community 191 - "Path"
Cohesion: 0.12
Nodes (15): Path, An unloadable CA file must error, never silently fall back to no verify., A throwaway key + self-signed cert for ``localhost`` (real handshakes)., A one-shot HTTPS server; records a failed handshake instead of crashing., A real handshake against a self-signed server must fail verification., Trusting that same cert as a CA lets the identical handshake through., A link-local URL over plain HTTP must fail before any request or write., _self_signed_cert() (+7 more)

### Community 192 - "20261010_1200-f4a5b6c7d8e9_phase4_domains_and_routes.py"
Cohesion: 0.31
Nodes (9): downgrade(), _drop_tenant_policies(), _grant(), _in_list(), Phase 4 — domains, routes and the routing schema. Adds, in one migration with a…, Grant the app role on *table*; the migration role GUC carries the name. The…, The two-policy shape every tenant table uses: tenant + system scope., _tenant_policies() (+1 more)

### Community 193 - "10. Implementation slices, acceptance criteria, tests, limitations"
Cohesion: 0.25
Nodes (8): 10.1 Slices (each independently reviewable, in order), 10.2 Test requirements (what "done" means per slice), 10.3.1 Approved decisions (previously open), 10.3.2 Known limitations (accepted, not blockers), 10.3.3 Open items and whether they block Phase 5.1, 10.3 Decisions and known limitations, 10.4 Reserved-operation-type lists — one source of truth (required consolidation), 10. Implementation slices, acceptance criteria, tests, limitations

### Community 194 - "NexusOps — Phase 1 (Multi-Tenancy) Report"
Cohesion: 0.29
Nodes (7): OperationSpec, Everything the control plane needs to know about one operation type.…, 1. What Phase 1 delivered, 4. Operations framework (added in this pass), 5. Tests, 8. Position, NexusOps — Phase 1 (Multi-Tenancy) Report

### Community 195 - "list_audit_logs"
Cohesion: 0.29
Nodes (7): list_audit_logs(), datetime, DbSession, Depends, get, PageParamsDep, Newest-first audit trail with optional filters. No write routes exist for this…

### Community 196 - "RouteHeader"
Cohesion: 0.12
Nodes (8): field_validator, model_validator, RateLimit, One header a route adds. ``target`` says where it lands., One route's request-rate ceiling (rendered as a ``limit_req_zone``)., RouteHeader, field_validator, test_rate_limit_constraints()

### Community 197 - "20261008_1200-b2c3d4e5f6a7_add_projects_and_environments.py"
Cohesion: 0.53
Nodes (5): downgrade(), _drop_constraint(), _quoted_list(), Phase 2 — projects & environments: env promotion, config, secret versions. This…, upgrade()

### Community 198 - "Product Roadmap — NexusOps Multi-Tenant Platform"
Cohesion: 0.11
Nodes (18): What one reported result did to its operation row. The caller's side effects —…, ResultTransition, 0. Stance, 11. Phase 8 — Backups — **proposal, not implemented**, 12. Phase 9 — Billing & metering — **proposal, not implemented**, 13.1 Scope-creep gates — what must be true before each expansion, 13. First commercially meaningful version, 14. Biggest risks (short form) (+10 more)

### Community 199 - "Platform Vision — NexusOps"
Cohesion: 0.20
Nodes (10): 1. Where NexusOps is today, 2.1 What we are NOT building, 2.2 The wedge (differentiation), 2. The direction, 3. Guiding principles, 4. Customer journey (target), 5.1 Architecture overview (target), 5. Control plane / data plane boundary (+2 more)

### Community 200 - "ServerOut"
Cohesion: 0.28
Nodes (6): computed_field, Whether the node has reported capabilities at all (v2 hello)., Full server view with recent timeline events and container counts., Server as listed in collections. Never exposes the agent token hash., ServerDetail, ServerOut

### Community 201 - "NotificationChannel"
Cohesion: 0.23
Nodes (11): NotificationChannel, A delivery target (email address / webhook endpoint). ``config_ciphertext``…, _create_monitor(), Monitor checks driving the full down -> incident -> recovery lifecycle., Regression: probe headers and URL query credentials never leave the API. Probe…, A monitor's checks, incidents and timeline all live in its organization, so the…, test_check_now_endpoint_runs_immediately(), test_down_then_recover_lifecycle() (+3 more)

### Community 202 - "run_async"
Cohesion: 0.08
Nodes (36): flush_pending_publishes(), Wait for frames scheduled by ``after_commit`` hooks to reach Redis. The commit…, task, Re-enqueue deployments the broker lost; fail ones whose worker died.…, sweep_deployments(), task, Flag silent servers OFFLINE, recover returning ones. Safe to overlap., sweep_servers() (+28 more)

### Community 203 - "ProxyProvider"
Cohesion: 0.33
Nodes (5): ProxyProvider, Any, Protocol, What ``app.services.proxy_service`` is allowed to assume about a provider. The…, 11. Post-deploy hooks

### Community 205 - ".dispatch"
Cohesion: 0.60
Nodes (3): Request, Response, RequestResponseEndpoint

### Community 206 - "test_agent_ingestion.py"
Cohesion: 0.30
Nodes (10): _enrolled(), _heartbeat(), Agent ingest pipeline: hello, heartbeat, staleness transitions, events., A container absent from a later heartbeat is gone from the daemon., A payload at the agent's cap may be truncated — absence proves nothing., test_heartbeat_at_container_cap_skips_reconciliation(), test_heartbeat_removes_vanished_containers(), test_heartbeat_updates_status_metrics_and_containers() (+2 more)

### Community 208 - "_live_bundle_id"
Cohesion: 0.20
Nodes (10): _allowed_bundle_path(), _live_bundle_id(), _live_files(), The bundle fingerprint — byte-identical to the control plane's algorithm.…, Read the live managed tree, or ``None`` when it does not exist yet., Fingerprint of the configuration tree currently on disk., Independently validate a bundle. Anything unexpected is refused., _template_version_of() (+2 more)

### Community 209 - "Multi-Tenancy Architecture"
Cohesion: 0.17
Nodes (11): Whether the runtime connection is the RLS-enforced application role. False…, 10. Migration (Phase 1), 1. Tenancy invariants, 2.1 Org creation — v1 decision, 2. Org resolution on every request, 4. Background jobs, 6. Agents, 7. The IDOR suite (+3 more)

### Community 211 - "create_server"
Cohesion: 0.33
Nodes (6): create_server(), Fetch existing tags by name and case-preservingly create missing ones., Register a server; enforces unique names and auto-creates tags., Apply a partial update; ``tags`` replaces the whole set when provided., _resolve_tags(), update_server()

### Community 212 - "test_notifications.py"
Cohesion: 0.39
Nodes (8): _channel(), _delivery(), UUID, Notification channel + delivery-log endpoints. Regression coverage for GET…, The same event frame consumed twice queues ONE delivery per channel. Every API…, test_dispatch_frame_is_idempotent_across_workers(), test_list_deliveries_filters_by_channel(), test_list_deliveries_serializes_rows()

### Community 213 - "_FakeAsyncClient"
Cohesion: 0.22
Nodes (3): _FakeAsyncClient, _FakeRequestObj, Scripted httpx.AsyncClient: responses keyed by absolute request URL.

### Community 214 - "test_migration_phase22.py"
Cohesion: 0.28
Nodes (8): UUID, Phase 2.2 — the environment-type correction follows the documented precedence.…, Only the previous migration's ``PROD`` output is corrected. A row already…, Create one legacy (application-scoped) environment per case., Every branch of the slug-first rule, end to end through ``head``., _seed_legacy(), test_correction_preserves_operator_set_values(), test_recognised_slug_alias_wins_over_a_conflicting_name()

### Community 215 - "9. Renewal, expiration, ownership loss, removal, revocation"
Cohesion: 0.33
Nodes (6): 9.1 Renewal, 9.2 Expiration monitoring, 9.3 Ownership loss (a verified Domain changes owners), 9.4 Removal, 9.5 Revocation, 9. Renewal, expiration, ownership loss, removal, revocation

### Community 216 - "client_ip.py"
Cohesion: 0.25
Nodes (8): _is_trusted(), _parse_networks(), Client-IP resolution behind chained reverse proxies. The API never takes TCP…, Parse a comma-separated CIDR list; malformed entries are skipped., test_parse_networks_skips_malformed_entries(), functools, ipaddress, _Network

### Community 217 - "_verified_domain"
Cohesion: 0.16
Nodes (19): One bounded look at a name's authoritative TXT record., TxtObservation, _count_rows_in_system_scope(), The second organization wins; the first stops being the owner., _run_verify(), test_a_domain_losing_verification_pulls_its_route(), test_a_sweep_invalidates_a_changed_delegation_and_re_verification_restores_it(), test_a_verified_domain_goes_stale_then_unverified_when_proof_disappears() (+11 more)

### Community 218 - "redact_log_event"
Cohesion: 0.19
Nodes (13): Any, structlog processor: scrub one record before anything renders it. The pipeline…, Replace every embedded PEM private-key block in *value* with the marker. Only…, Scrub PEM private-key blocks out of one free-text value. The scalar counterpart…, Recursively redact one value of any shape — the depth-agnostic walk. Dicts,…, redact_log_event(), _redact_private_key_blocks(), redact_text() (+5 more)

### Community 219 - "Domain Model — NexusOps as a Multi-Tenant Platform"
Cohesion: 0.40
Nodes (5): 0. Design stance, 1.1 ER diagram, 1. The hierarchy, 3. Cross-cutting decisions, Domain Model — NexusOps as a Multi-Tenant Platform

### Community 220 - "permissions.py"
Cohesion: 0.29
Nodes (5): permission_exists(), PermissionSpec, Permission registry and role matrix. Permissions are *data*: the registry below…, test_permission_exists_helper(), fnmatch

### Community 221 - ".facts"
Cohesion: 0.50
Nodes (3): Alias for :attr:`extra`, so the API can expose open-ended agent facts. The…, 2.3 Infrastructure — Nodes, 2.1 Current shape (real)

### Community 223 - "test_capability_report_shape_is_accepted"
Cohesion: 0.50
Nodes (4): CapabilityReport, One node-reported capability. ``present`` defaults to false, and a capability…, Whatever the pre-flight returns must satisfy the hello schema., test_capability_report_shape_is_accepted()

### Community 224 - "VerificationDecision"
Cohesion: 0.50
Nodes (4): What the lifecycle should do with an observation., VerificationDecision, _detail_for(), A short, safe explanation. The expected token never appears in it.

### Community 225 - "register_agent_hello"
Cohesion: 0.50
Nodes (4): _negotiate_protocol(), The wire version this node will use: the lower of the two sides., Mark the agent enrolled and persist its static host facts. Capabilities are…, register_agent_hello()

### Community 226 - "servers.py"
Cohesion: 0.18
Nodes (18): create_enrollment_token(), _enrollment_created(), _enrollment_out(), list_enrollment_tokens(), Node endpoints: CRUD, tags, agent enrollment tokens. The domain entity is the…, Mint one single-use enrollment token in the caller's organization. The org…, Enrollment tokens in the active organization, newest first. The response type…, Revoke an unused enrollment token immediately. (+10 more)

### Community 227 - "_run"
Cohesion: 0.33
Nodes (7): _containers_for(), task, Deterministic smooth value in [base-amplitude, base+amplitude]., Stable per-server container set; one container cycles EXITED occasionally., simulation_tick(), _run(), _wave()

### Community 228 - "asyncio"
Cohesion: 0.22
Nodes (7): asyncio, _FakeDb, Frames committed inside a task must reach Redis before that task's loop closes.…, Stands in for an ``AsyncSession`` whose only job here is ``sync_session``. A…, The shape of a worker task whose last statement is a commit., test_run_async_publishes_frames_scheduled_by_the_commit_hook(), commit_then_return()

### Community 229 - "test_created_at_defaults.py"
Cohesion: 0.50
Nodes (3): created_at server defaults must evaluate per insert, not at table creation., Regression: system_events and audit_logs shipped with DEFAULT 'now()' (quoted…, test_audit_and_event_created_at_defaults_are_dynamic()

### Community 230 - "20261009_1300-a1b2c3d4e5f6_add_phase3_nodes_and_agent_v2.py"
Cohesion: 0.40
Nodes (4): _grant(), Phase 3 — Nodes & Agent v2 schema. Adds, in one migration with a single head: *…, Grant the app role on *table*; the migration role GUC carries the name. The…, upgrade()

### Community 231 - "test_remove_honours_force_and_never_shells"
Cohesion: 0.50
Nodes (3): test_container_start_maps_to_a_fixed_api_call(), fake_raw(), test_remove_honours_force_and_never_shells()

### Community 232 - "require_permission"
Cohesion: 0.17
Nodes (11): permission_dep(), Any, Dependency factory enforcing a permission; returns 403 when denied., require_permission(), _check(), _FakeCtx, Duck-typed stand-in for AuthContext., test_require_permission_raises_forbidden_when_denied() (+3 more)

### Community 234 - "get_meta"
Cohesion: 0.40
Nodes (5): get_meta(), DbSessionDep, get, Public metadata; identity fields appear only for valid credentials., OptionalUser

### Community 236 - "v1/agent.py"
Cohesion: 0.09
Nodes (36): agent_enroll(), agent_heartbeat(), agent_hello(), claim_operation(), _presented_token(), DbDep, post, Request (+28 more)

## Knowledge Gaps
- **494 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+489 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2356 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **25 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `6. Tooling: reproducible e2e` connect `maintenance.py` to `NexusOps — Phase 1 (Multi-Tenancy) Report`, `run_async`, `client.ts`, `NotFound`, `org_scope`, `auth_service.py`?**
  _High betweenness centrality (0.246) - this node is a cross-community bridge._
- **Why does `useEventStream()` connect `client.ts` to `apiGet`, `App.tsx`, `AuthContext.tsx`, `ServerDetailPage.tsx`, `@tanstack/react-query`, `maintenance.py`?**
  _High betweenness centrality (0.246) - this node is a cross-community bridge._
- **Why does `TenancyScopeError` connect `org_scope` to `AuthContext`, `deps.py`, `core/tenancy.py`, `resolve_auth`, `maintenance.py`, `assert_error_code`, `publish`, `enrollment_service.py`, `enums.py`, `test_tenant_isolation.py`, `apply_scope_to_session`?**
  _High betweenness centrality (0.109) - this node is a cross-community bridge._
- **Are the 94 inferred relationships involving `AuthContext` (e.g. with `TenancyScopeError` and `MembershipStatus`) actually correct?**
  _`AuthContext` has 94 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `APIModel` (e.g. with `OperationSpec` and `test_specs_reject_unknown_params()`) actually correct?**
  _`APIModel` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `Server` (e.g. with `ServerStatus` and `2.3 Infrastructure — Nodes`) actually correct?**
  _`Server` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `apiGet()` (e.g. with `ContainerDetailPage.test.tsx` and `mockApi()`) actually correct?**
  _`apiGet()` has 5 INFERRED edges - model-reasoned connections that need verification._