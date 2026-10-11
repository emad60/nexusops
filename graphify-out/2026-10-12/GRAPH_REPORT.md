# Graph Report - nexusops  (2026-10-12)

## Corpus Check
- 364 files · ~411,440 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: (none) 10, .example 1, .service 1)

## Summary
- 6207 nodes · 18252 edges · 225 communities (202 shown, 23 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1490 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e2e8c721`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- apiGet
- test_certificates.py
- ApiKeysPage.tsx
- test_phase4_routing.py
- container_service.py
- toast.tsx
- config.py
- OperationType
- App.tsx
- test_agent_v2.py
- assert_error_code
- ServerDetailPage.tsx
- events.py
- ContainerDetailPage.tsx
- projects.py
- certificate_service.py
- deployment_engine.py
- Container
- enrollment_service.py
- v1/secrets.py
- test_deployments_simulated.py
- containers.py
- metrics_service.py
- test_security.py
- .bundle_id
- monitor_service.py
- Node & Agent Architecture
- test_agent_backoff.py
- SimulatedDeploymentRunner
- nexusops_agent.py
- integration/conftest.py
- auth_service.py
- docker_host_service.py
- test_rate_limit.py
- docker_hosts.py
- hub.py
- NginxBundle
- v1/search.py
- enums.py
- list_deliveries
- DockerProvider
- test_monitor_transport.py
- StepFailure
- client.ts
- project_service.py
- test_permissions.py
- routes.py
- apply_scope_to_session
- BadRequest
- NotFound
- roles.py
- servers.py
- proxy_service.py
- test_migration_phase21.py
- APIModel
- test_agent_nginx_contract.py
- users.py
- collections_abc
- notification_service.py
- test_tenant_isolation.py
- compilerOptions
- v1/deployments.py
- errors.py
- dns_verifier.py
- test_phase2_environments.py
- route_service.py
- test_schema_redaction.py
- event_bus.py
- Certificate Management — NexusOps
- seed.py
- core/tenancy.py
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
- log_service.py
- user_service.py
- devDependencies
- Conflict
- test_certificate_lifecycle.py
- Settings
- DomainStatus
- Server
- alerts.py
- org_scope
- test_phase21_secret_version_integrity.py
- server_service.py
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- fixtures.ts
- @tanstack/react-query
- redact_mapping
- certificates.py
- organization.py
- Path
- _rows
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- test_migration_phase5.py
- docker_real.py
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- test_maintenance_sweep.py
- organization_service.py
- Phase 5 — HTTPS, Certificates and Private-Key Delivery — Design
- dnsmock.py
- scripts
- typing
- test_tenancy_allowlist.py
- _alembic_config
- dependencies
- DeploymentDetailPage.test.tsx
- generate_secrets.sh
- ControlHandler
- server_payload
- test_migration_phase2.py
- logging.py
- OperationError
- v1/operations.py
- EventLevel
- install.sh
- docker-entrypoint.sh
- integration/__init__.py
- ProjectDetailPage.tsx
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
- notification_sender.py
- nexusops-challenge.mjs
- Secrets Architecture
- test_schemas_agent.py
- .state
- build_capabilities
- alert_service.py
- decide
- RouteHeader
- AgentClient
- certificate_lifecycle.py
- nginx.py
- deps.py
- simulation.py
- _exec
- test_agent_contract.py
- StepLine
- Domain Routing — NexusOps
- container.py
- apikeys.py
- main
- Platform Security Model — NexusOps
- enqueue.py
- journey.spec.ts
- _node_session
- _enforce
- _nginx_apply
- _nginx_bootstrap
- v1/channels.py
- AuthContext
- 20261012_1200-c8d9e0f1a2b3_phase5_certificate_metadata.py
- maintenance.py
- pytest
- instant_pacing
- phase3.spec.ts
- sweep_deployments
- bundle_summary
- get_settings
- 10.1 Slices (each independently reviewable, in order)
- test_ws_hub.py
- .route_file_path
- ._check_status
- AgentContainerPortIn
- README.md - NexusOps overview
- CertificateStatus
- 6. Config rendering — strict allowlists
- test_monitors_incidents.py
- run_async
- ProxyProvider
- test_domain_creation_rejects_invalid_names
- test_existing_url_monitors_are_untouched_by_routing
- test_agent_ingestion.py
- _validate_bundle
- current_org
- test_notifications.py
- _FakeAsyncClient
- redact_log_event
- encrypt_str
- test_app_gating.py
- .apply_params
- InvalidTransition
- DeploymentRunner
- test_event_publish_drain.py
- _memory_count_and_ttl
- 4. DNS ownership verification
- services/__init__.py
- _pace
- v1/agent.py
- 9. Phase 6 — Real deployments — **proposal, not implemented**
- decrypt_str

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

## Communities (225 total, 23 thin omitted)

### Community 0 - "apiGet"
Cohesion: 0.06
Nodes (80): apiDelete(), apiGet(), apiPost(), DomainDetailPage, MonitorDetailPage, useAuth(), SelectField(), useToast() (+72 more)

### Community 1 - "test_certificates.py"
Cohesion: 0.08
Nodes (55): _app_role_dsn(), _audits(), _certificate_rows(), _create_domain(), _created_certificate(), _dns_stub(), _events(), _fake_observe() (+47 more)

### Community 2 - "ApiKeysPage.tsx"
Cohesion: 0.09
Nodes (19): ApiKeyOut, ApiKeysPage, ApiKeyCreatedOut, handleCopyKey(), copyText(), describeError(), EMPTY_FORM, GROUP_STYLE (+11 more)

### Community 3 - "test_phase4_routing.py"
Cohesion: 0.05
Nodes (128): One bounded look at a name's authoritative TXT record., TxtObservation, task, Re-prove control of every domain whose next check is due. Covers three cases…, Keep every routed node's live configuration matching the desired bundle. One…, sweep_domains(), sweep_routes(), _agent_result_body() (+120 more)

### Community 4 - "container_service.py"
Cohesion: 0.10
Nodes (31): clip(), Provider abstraction for docker hosts (real daemon or simulated). Providers are…, Truncate *text* to *limit* characters, stripping control chars., is_simulated(), Provider selection based on a docker host's endpoint URL. Mapping: *…, True when *provider* is the simulated implementation., _as_health(), _as_status() (+23 more)

### Community 5 - "toast.tsx"
Cohesion: 0.02
Nodes (80): name, private, type, version, CheckOut, IncidentOut, MonitorOut, SessionInfo (+72 more)

### Community 6 - "config.py"
Cohesion: 0.12
Nodes (28): _is_trusted(), _parse_networks(), Request, Client-IP resolution behind chained reverse proxies. The API never takes TCP…, Parse a comma-separated CIDR list; malformed entries are skipped., Real client address for *request* per the trust model above., resolve_client_ip(), fail_on_bad_config() (+20 more)

### Community 7 - "OperationType"
Cohesion: 0.12
Nodes (20): OperationType, The whitelist. Nothing outside this enum ships as an exec surface. Each type…, Any, Validate *params* against the type's model and return the stored form.…, validate_params(), MonkeyPatch, The operation dispatch whitelist is a contract, not a convention.…, A type whose capability cannot be confirmed must not be dispatchable. (+12 more)

### Community 8 - "App.tsx"
Cohesion: 0.04
Nodes (89): AuditEntry, DeploymentOut, DeploymentStepOut, EnvironmentDetailOut, EnvironmentOut, IncidentEventOut, Page, ProjectOut (+81 more)

### Community 9 - "test_agent_v2.py"
Cohesion: 0.08
Nodes (36): agent_fixture(), _load_agent(), Any, fixture, parametrize, Agent protocol v2: honest metrics, capability detection, and the executor. The…, Phase 4 shipped three nginx ops — no file primitive, no command primitive., Trusting a private CA must not weaken verification. (+28 more)

### Community 10 - "assert_error_code"
Cohesion: 0.07
Nodes (62): OperationStatus, Lifecycle of one node operation (node-agent-architecture.md §5.1).…, expire_operations(), Expire node operations past their deadline — pending and claimed alike. A…, assert_error_code(), Assert envelope shape + code; returns the inner error object., Regression: lockout must not leak which emails exist. After login_max_attempts…, test_locked_account_response_is_indistinguishable() (+54 more)

### Community 11 - "ServerDetailPage.tsx"
Cohesion: 0.05
Nodes (47): EnrollmentTokenCreated, EnrollmentTokenItem, MetricPoint, OperationItem, OperationType, OrganizationRequiredPage, ServerDetailPage, ServerListPage (+39 more)

### Community 12 - "events.py"
Cohesion: 0.09
Nodes (27): _decode_cursor(), _encode_cursor(), list_event_types(), list_events(), datetime, DbSession, Depends, get (+19 more)

### Community 13 - "ContainerDetailPage.tsx"
Cohesion: 0.05
Nodes (41): getAccessToken(), onActiveOrgChange(), refreshToken(), CursorPage, EventItem, ContainerDetailPage, EventsPage, Subscription (+33 more)

### Community 14 - "projects.py"
Cohesion: 0.04
Nodes (96): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+88 more)

### Community 15 - "certificate_service.py"
Cohesion: 0.11
Nodes (37): Certificate, CertificateGeneration, One ACME order + one key pair. Renewal inserts a new row, never mutates one.…, One requested certificate: an identity, its lifecycle view, no material., CertificateChallengeType, How ownership of an identifier is proved to the CA. DNS-01 only in v1: it is…, _actor(), all_generations() (+29 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.08
Nodes (71): deployment_log_channel(), Deployment, DeploymentStep, DeploymentStatus, StepStatus, _after_commit_enqueue(), _after_rollback_drop(), _audit_resolution_failed() (+63 more)

### Community 17 - "Container"
Cohesion: 0.07
Nodes (40): ContainerHealth, ContainerStatus, Container, Observed container state mirrored from an agent or docker provider., ContainerInfo, DockerProviderError, A provider operation failed. ``str()`` is safe to show/log., Normalized view of a container as reported by any provider. (+32 more)

### Community 18 - "enrollment_service.py"
Cohesion: 0.10
Nodes (33): generate_enrollment_token(), An enrollment credential (``nxk_``): single-use, short-lived, org-scoped.…, Return the active org id or raise; used by services that need it explicitly., require_org(), EnrollmentToken, One single-use credential that enrolls (or claims) exactly one node., Whether the row could still be redeemed (not a race-safe check)., EnrollmentTokenState (+25 more)

### Community 19 - "v1/secrets.py"
Cohesion: 0.12
Nodes (33): create_secret(), delete_secret(), get_secret(), list_secret_versions(), list_secrets(), DbSession, delete, get (+25 more)

### Community 20 - "test_deployments_simulated.py"
Cohesion: 0.14
Nodes (29): execute_deployment(), Run one deployment to a terminal state. Never raises; safe to re-run., get_environment(), _as_worker(), _delivery_chain(), _owner_ctx(), _queue(), _queued_with_recorder() (+21 more)

### Community 21 - "containers.py"
Cohesion: 0.07
Nodes (53): _action_route(), _endpoint(), _container_out(), _decode_frame(), _ev(), get_container(), _like_pattern(), list_container_logs() (+45 more)

### Community 22 - "metrics_service.py"
Cohesion: 0.11
Nodes (31): MetricGranularity, MetricSnapshot, aggregate_rollups(), dashboard_summary(), ensure_server(), _extra_object(), granularity_for_range(), latest_for_servers() (+23 more)

### Community 23 - "test_security.py"
Cohesion: 0.07
Nodes (58): argon2, argon2_exceptions, User, Resolve the caller's identity only (no organization)., _resolve_identity(), _user_from_api_key(), Unauthorized, create_access_token() (+50 more)

### Community 24 - ".bundle_id"
Cohesion: 0.18
Nodes (10): 3.1 Domain, 3.2 Route, 3. Entities (per domain-model.md §2.4), 5. ProxyProvider interface, 8.1 Binding rules, 8.2 Certificate selection rule (this doc owns it) — **Phase 5 target design**, 8.3 Re-render triggers, 8.5 How deployments hook routing (post-deploy route sync) (+2 more)

### Community 25 - "monitor_service.py"
Cohesion: 0.10
Nodes (49): MonitorStatus, Monitor, MonitorCheck, One probe. Targets are polymorphic since Phase 4 (domain-model.md §2.6).…, Drop the query string so signed tokens never appear in error text., Public alias: redact any query string from a URL before display/persist., strip_query(), MonitorBase (+41 more)

### Community 26 - "Node & Agent Architecture"
Cohesion: 0.09
Nodes (22): install_hint(), The one-liner an operator pastes, without the raw token in argv. The token…, 1. Scope and stance, 3.2 Enrollment v2, 3.3 Token storage & rotation with dual-token grace, 3.4 Revocation semantics — fixing the 401 hot-loop, 3.5 Reconnect / offline states, 3. Agent lifecycle (+14 more)

### Community 27 - "test_agent_backoff.py"
Cohesion: 0.16
Nodes (20): agent_fixture(), _install_sleep(), fake_sleep(), _load_agent(), _patch_host(), Any, fixture, MonkeyPatch (+12 more)

### Community 28 - "SimulatedDeploymentRunner"
Cohesion: 0.25
Nodes (23): Staged docker-style simulation used by v1 deployments., Canonical step identifiers stored on :class:`DeploymentStep` rows., SimulatedDeploymentRunner, StepName, _collect(), _ctx(), Unit tests for SimulatedDeploymentRunner (async generators, no broker)., RESOLVE_CONFIG is planned by the engine, not produced by a runner. (+15 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.09
Nodes (29): build_heartbeat(), collect_container_stats(), collect_containers(), _container_ports(), _container_status(), cpu_percent_since(), disk_stats(), docker_capability() (+21 more)

### Community 30 - "integration/conftest.py"
Cohesion: 0.09
Nodes (24): _admin_dsn(), client(), _ensure_database(), _migrated_database(), org_db(), owner(), AsyncClient, fixture (+16 more)

### Community 31 - "auth_service.py"
Cohesion: 0.10
Nodes (48): System scope bound to *db*, for rows that have no organization. Used by exactly…, system_write_scope(), Opaque refresh token; only its SHA-256 hash is stored. Rotation chain: on…, RefreshToken, _audit(), _auth_event_scope(), _bootstrap_organization(), change_own_password() (+40 more)

### Community 32 - "docker_host_service.py"
Cohesion: 0.12
Nodes (38): DockerHostStatus, DockerHost, describe_provider_error(), provider_for(), Exception, Return the provider matching *host*'s endpoint configuration., Sanitized, length-capped text safe for host ``last_error`` columns., Destructive removal requiring exact-name confirmation. Deletes via the provider… (+30 more)

### Community 33 - "test_rate_limit.py"
Cohesion: 0.36
Nodes (9): RateLimited, rate_limit(), Return a dependency enforcing *limit* requests per window per IP. With…, _FakeRequest, Unit tests for the Redis-backed rate limiter's failure modes. Regression…, test_auth_limiter_is_fail_closed(), test_fail_closed_fallback_is_per_ip(), test_fail_closed_limiter_still_limits_when_redis_down() (+1 more)

### Community 34 - "docker_hosts.py"
Cohesion: 0.07
Nodes (55): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+47 more)

### Community 35 - "hub.py"
Cohesion: 0.13
Nodes (22): _authenticate_api_key(), _authenticate_jwt(), _bind_organization(), _frame_org(), _load_permissions(), _org_id_from_frame(), AsyncSession, UUID (+14 more)

### Community 36 - "NginxBundle"
Cohesion: 0.13
Nodes (16): Render the complete desired state for *node*. A full tree every time — never a…, BundleFile, fingerprint_files(), is_allowed_bundle_path(), NginxBundle, model_validator, One rendered file. The path is allowlisted, the content is bounded., Deterministic fingerprint over the complete rendered tree. Path order is… (+8 more)

### Community 37 - "v1/search.py"
Cohesion: 0.13
Nodes (31): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+23 more)

### Community 38 - "enums.py"
Cohesion: 0.08
Nodes (63): _org_scoped_classes(), Mapped classes marked :class:`~app.models.base.OrgScoped`. Reads the mapper…, Base, big_serial_pk(), json_column(), org_id_column(), OrgScoped, datetime (+55 more)

### Community 39 - "list_deliveries"
Cohesion: 0.17
Nodes (22): create_channel(), delete_channel(), get_channel(), list_channels(), list_deliveries(), DbDep, delete, Depends (+14 more)

### Community 40 - "DockerProvider"
Cohesion: 0.09
Nodes (12): DockerProvider, Any, datetime, Protocol, List containers visible to the provider., Inspect a single container by id (short ids allowed)., List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``., List volumes: keys ``name``, ``driver``, ``mountpoint``. (+4 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.07
Nodes (53): CheckResult, CheckOutcome, coerce_headers(), _decode(), get_transport(), HTTPMonitorTransport, MonitorTransport, Any (+45 more)

### Community 42 - "StepFailure"
Cohesion: 0.11
Nodes (19): Exception, Raised by a runner when a step fails irrecoverably., StepFailure, 10. Events and WS during runs, 12. Rollback semantics (existing behavior kept), 13. The simulated runner stays — labeled, 14. Open questions, 1. Current state — what is real and what is simulated (+11 more)

### Community 43 - "client.ts"
Cohesion: 0.04
Nodes (54): API_BASE, ApiError, apiRequest(), buildUrl(), extractError(), getActiveOrgId(), ORGANIZATION_HEADER, OrgListener (+46 more)

### Community 44 - "project_service.py"
Cohesion: 0.12
Nodes (48): paginate(), AsyncSession, Execute *stmt* with limit/offset and return ``(rows, total)``., Application, DeploymentEnvironment, A **project-scoped** deployment environment (Phase 2 promotion). The…, ApplicationUpdate, Partial application update; omitted fields are left untouched. (+40 more)

### Community 45 - "test_permissions.py"
Cohesion: 0.05
Nodes (41): permission_exists(), PermissionSpec, Permission registry and role matrix. Permissions are *data*: the registry below…, Check an API-key scope list against a required permission. Supports exact match…, scope_matches(), _auth_context(), _FakeCtx, parametrize (+33 more)

### Community 46 - "routes.py"
Cohesion: 0.18
Nodes (27): create_route(), delete_route(), disable_route(), _domain_status(), enable_route(), get_route(), list_routes(), AsyncSession (+19 more)

### Community 47 - "apply_scope_to_session"
Cohesion: 0.07
Nodes (58): get_sessionmaker(), async_sessionmaker, AsyncSession, apply_scope_to_session(), Run the enclosed block with tenant filtering off (maintenance only). ``reason``…, Push the current scope onto *db*'s connection immediately. Needed only when a…, system_scope(), racing_flush() (+50 more)

### Community 48 - "BadRequest"
Cohesion: 0.08
Nodes (61): BadRequest, UnprocessableEntity, assert_safe_tcp_endpoint(), assert_safe_url(), assert_safe_url_async(), _is_forbidden_address(), is_simulation_url(), ValueError (+53 more)

### Community 49 - "NotFound"
Cohesion: 0.08
Nodes (52): NotFound, An encrypted configuration value, scoped to org, project or environment.…, One immutable value of a :class:`Secret` — append-only history. A row is…, Secret, SecretVersion, _actor_type(), _collect_refs(), create_secret() (+44 more)

### Community 50 - "roles.py"
Cohesion: 0.11
Nodes (29): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, delete, get (+21 more)

### Community 51 - "servers.py"
Cohesion: 0.07
Nodes (62): apply_node_proxy_config(), create_enrollment_token(), create_server(), delete_server(), _detail(), _enrollment_created(), _enrollment_out(), get_server() (+54 more)

### Community 52 - "proxy_service.py"
Cohesion: 0.05
Nodes (82): ProxyApplyOutcome, Terminal outcome of one ``nginx.apply`` operation on a node., NodeProxyCapabilityOut, NodeProxyStatusOut, Route schemas, the upstream picker, and the node proxy-status read model. Every…, The node's reported nginx capability, bounded to the useful facts., ``GET /nodes/{id}/proxy/status``. Reports what the node said and what the…, One genuinely usable published port reported by the node's agent. (+74 more)

### Community 53 - "test_migration_phase21.py"
Cohesion: 0.22
Nodes (9): Phase 2.1 corrective migration: legacy ``environment_type`` classification.…, Every case is classified as documented, ids and ownership intact., An explicit non-DEV classification survives the corrective migration. The…, The correction is part of ``head`` and adds no extra Alembic head., Insert one legacy environment per case, in two organizations., _seed_typed_environments(), test_corrective_migration_is_reachable_from_head(), test_corrects_legacy_environment_types() (+1 more)

### Community 54 - "APIModel"
Cohesion: 0.06
Nodes (68): change_password(), _clear_refresh_cookie(), _cookies_secure(), login(), logout(), me(), _optional_actor(), AsyncSession (+60 more)

### Community 55 - "test_agent_nginx_contract.py"
Cohesion: 0.08
Nodes (54): _agent_bundle(), agent_fixture(), _bootstrap_fixture(), _load_agent(), Any, fixture, parametrize, Path (+46 more)

### Community 56 - "users.py"
Cohesion: 0.13
Nodes (25): create_user(), deactivate_user(), get_user(), list_users(), CurrentUser, DbSessionDep, delete, get (+17 more)

### Community 57 - "collections_abc"
Cohesion: 0.05
Nodes (24): alembic, downgrade(), rename ``server.*`` permission codenames to ``node.*`` The Node/Server…, _rename_permissions(), upgrade(), Fix pre-existing model/migration drift (surfaced by the new drift check). Two…, _clear_app_role_guc(), downgrade() (+16 more)

### Community 58 - "notification_service.py"
Cohesion: 0.17
Nodes (23): _as_uuid(), _attempt_delivery(), decode_delivery_cursor(), dispatch_event_frame(), _send(), dispatcher_loop(), encode_delivery_cursor(), list_deliveries() (+15 more)

### Community 59 - "test_tenant_isolation.py"
Cohesion: 0.05
Nodes (80): bearer(), cookie_attributes(), error_of(), login_account(), login_headers(), Any, AsyncClient, Response (+72 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "v1/deployments.py"
Cohesion: 0.08
Nodes (49): _attribute_step_idx(), cancel_deployment(), _emails_for(), get_deployment(), list_application_deployments(), list_deployment_logs(), _list_deployments(), _parse_sort() (+41 more)

### Community 62 - "errors.py"
Cohesion: 0.09
Nodes (20): AppError, _error_payload(), Any, Exception, FastAPI, Request, Error taxonomy and the single place where API error envelopes are shaped. Every…, Base class for expected, client-facing errors. (+12 more)

### Community 63 - "dns_verifier.py"
Cohesion: 0.15
Nodes (14): _discover_nameservers(), _normalise_ns(), observe(), Observer, public_addresses(), Protocol, _query_txt(), Authoritative DNS observation for domain-ownership verification. Two halves,… (+6 more)

### Community 64 - "test_phase2_environments.py"
Cohesion: 0.18
Nodes (22): _environment(), _project(), parametrize, Phase 2: project-scoped environments, config layering, and their isolation. The…, Uniqueness is ``(project_id, slug)`` — not instance-wide., The update path is validated too (the pre-Phase-2 gap)., Knowing an environment UUID is not access: the project link must hold., Another tenant cannot reach the project, its environments, or its detail. (+14 more)

### Community 65 - "route_service.py"
Cohesion: 0.09
Nodes (52): Last nginx apply outcome for a route, as reported by its node's agent.…, RouteConfigState, One hostname+path served from one container on one node. Relationship rules the…, Route, Payload for ``POST /routes``. A route is created **disabled** unless…, RouteCreate, mark_removal_requested(), Record that *route* must leave its node's configuration. True when new. Called… (+44 more)

### Community 66 - "test_schema_redaction.py"
Cohesion: 0.18
Nodes (17): is_sensitive_header(), mask_sensitive_headers(), True when *name* looks like it carries a credential (Authorization etc.)., Return a copy of *headers* with sensitive values replaced by a mask., mask_target(), Human-readable masked target safe to expose over the API. For webhook families…, _monitor_out(), Outbound-schema redaction: monitor probe credentials and webhook targets.… (+9 more)

### Community 67 - "event_bus.py"
Cohesion: 0.13
Nodes (24): get_redis(), ping(), Shared async Redis client., SystemEvent, _after_commit_publish(), _after_rollback_drop(), event_frame_from_row(), _publish_after_commit() (+16 more)

### Community 68 - "Certificate Management — NexusOps"
Cohesion: 0.13
Nodes (15): 10. Status/expiry tracking and monitor tie-in, 12. Audit and events, 13. Non-goals, 3. API surface and permissions, 4.1 DNS-01 first (the default and the wedge), 4.2 DNSProvider interface, 4.3 ACME account and directory, 4.4 HTTP-01 via node nginx (later fallback) (+7 more)

### Community 69 - "seed.py"
Cohesion: 0.13
Nodes (26): OrganizationStatus, A login session binding refresh tokens to a device/context., A named permission set. ``org_id`` is NULL for every row in v1 — the five…, Role, Session, Membership, Organization, A tenant. Every organization-owned row points here via ``org_id``. (+18 more)

### Community 70 - "core/tenancy.py"
Cohesion: 0.09
Nodes (32): The active organization, or raise if this request has none., _apply_scope_guc(), _desired_guc(), _guard(), _has_org_predicate(), install_tenancy_guards(), _mappers_of(), org_scoped_table_names() (+24 more)

### Community 71 - "test_secrets.py"
Cohesion: 0.22
Nodes (13): _create(), _environment_config(), Secrets: metadata-only reads, rotation versioning, deploy-time resolution., Project → application → environment carrying *config*; returns its id., A reference naming no secret must abort, not resolve to an empty value.…, A row this ENCRYPTION_KEY cannot decrypt must abort, not yield ``""``., test_create_and_list_return_metadata_only(), test_delete_removes_metadata_row() (+5 more)

### Community 72 - "test_nginx_renderer.py"
Cohesion: 0.14
Nodes (35): NginxProvider, ValueError, The only production provider in Phase 4., Rendering refused the input. Always a bug or a corrupt row, never a leak., RenderError, provider(), fixture, parametrize (+27 more)

### Community 73 - "domain_service.py"
Cohesion: 0.10
Nodes (40): Domain, One DNS name an organization is proving it controls. ``name`` is canonical (see…, What the lifecycle should do with an observation., VerificationDecision, _actor(), apply_decision(), _bad_name(), claim_verified_name() (+32 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "monitors.py"
Cohesion: 0.13
Nodes (38): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+30 more)

### Community 76 - "PageParams"
Cohesion: 0.08
Nodes (42): list_sessions(), CurrentUser, DbSessionDep, delete, get, Request, UUID, Session routes: list active sessions, revoke own or (with user.manage) any. (+34 more)

### Community 77 - "domains.py"
Cohesion: 0.13
Nodes (34): create_domain(), delete_domain(), _enqueue_verification(), get_domain(), list_domain_routes(), list_domains(), _project_names(), alias (+26 more)

### Community 78 - "incidents.py"
Cohesion: 0.15
Nodes (30): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+22 more)

### Community 79 - "test_phase2_secrets.py"
Cohesion: 0.19
Nodes (21): _env(), _project(), Phase 2 secrets: layered scope, immutable versions, rollback, isolation. Two…, Two racing rotations must both be kept and never share a version number., Another tenant cannot read, rotate, roll back or even enumerate the secret., The documented example: same key at three scopes; most specific wins., A ref declared in the project base config resolves for its environments., _resolved() (+13 more)

### Community 80 - "RolesPage.tsx"
Cohesion: 0.18
Nodes (9): RolesPage, describeError(), GROUP_STYLE, LEGEND_STYLE, OPTION_STYLE, PermissionSpec, roleAllows(), RoleForm (+1 more)

### Community 81 - "test_schemas_server.py"
Cohesion: 0.21
Nodes (22): Payload for registering a server., Partial update. ``tags`` replaces the full set when provided., ServerCreate, ServerUpdate, _base(), parametrize, Unit tests for app.schemas.server (validation only, no I/O)., test_empty_ip_is_allowed_but_whitespace_collapses() (+14 more)

### Community 82 - "canonicalize_name"
Cohesion: 0.09
Nodes (41): apex_of(), canonicalize_name(), canonicalize_path(), _check_labels(), _check_not_ip(), hostname_is_covered(), _idna(), InvalidName (+33 more)

### Community 83 - "tests/conftest.py"
Cohesion: 0.22
Nodes (7): configure_test_env(), Test bootstrap: pin every cached setting BEFORE the first ``app`` import. The…, KEY=VALUE pairs from the repo .env (first definition wins); never logged., Export the exact settings the app caches; host values cannot leak through., _read_dot_env(), os, sys

### Community 84 - "log_service.py"
Cohesion: 0.15
Nodes (21): LogLine, One parsed log record from a container log stream., append_lines(), count_container_logs(), detect_level(), _entry_values(), ingest_provider_lines(), publish_log_line() (+13 more)

### Community 85 - "user_service.py"
Cohesion: 0.12
Nodes (41): MembershipStatus, UserStatus, _apply_deactivation(), _assert_not_last_active_member(), _assert_not_last_active_superadmin(), create_user(), deactivate_user(), get_by_email() (+33 more)

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "Conflict"
Cohesion: 0.08
Nodes (52): Conflict, Operation, Whether the agent reported this operation as successful. A terminal check, not…, One whitelisted action for one node, with a CAS lifecycle. ``attempts`` is…, _active_org(), _bounded(), cancel_operation(), claim_operation() (+44 more)

### Community 88 - "test_certificate_lifecycle.py"
Cohesion: 0.10
Nodes (32): one_live_generation_predicate(), The SQL predicate of ``uq_cert_generations_one_live``. Built from…, CertificateGenerationState, Pre-issuance lifecycle of one ACME order + key pair. **The vocabulary is…, The states in which a generation is still being worked on. At most one of these…, CertificateGenerationOut, One generation's lifecycle metadata. No material, no internal cursors.…, can_transition() (+24 more)

### Community 89 - "Settings"
Cohesion: 0.14
Nodes (6): field_validator, model_validator, Username from :attr:`database_url`, or ``None`` if it is unparseable., Validated application settings (loaded from environment / .env)., Settings, BaseSettings

### Community 90 - "DomainStatus"
Cohesion: 0.13
Nodes (26): DomainStatus, Ownership-verification lifecycle of a Domain (domain-routing.md §4). ``STALE``…, The state a domain flip forces on its routes, or ``None`` to leave them., route_config_state_for(), The honest state of a route that left the desired tree but is not gone. One…, removal_requested_detail(), _affected_node_ids(), _announce() (+18 more)

### Community 91 - "Server"
Cohesion: 0.15
Nodes (20): ListenerOwnership, Who holds one required listener port, per the node's pre-flight. The…, Alias for :attr:`extra`, so the API can expose open-ended agent facts. The…, Server, capability_of(), capability_out(), eligibility_error(), _listener_conflict_message() (+12 more)

### Community 92 - "alerts.py"
Cohesion: 0.21
Nodes (16): list_alerts(), mark_all_read(), mark_read(), CurrentUser, DbDep, Depends, get, post (+8 more)

### Community 93 - "org_scope"
Cohesion: 0.10
Nodes (41): current_scope(), org_scope(), ``'org'``, ``'system'`` or ``'unset'``., Run the enclosed block as a single organization. Nesting the *same* org is a…, _entity_exists(), Whether *id_* exists **for this organization**. Runs inside the socket's…, _create_server(), _guc() (+33 more)

### Community 94 - "test_phase21_secret_version_integrity.py"
Cohesion: 0.18
Nodes (18): _app_role_dsn(), _owner_dsn(), _probe(), Phase 2.1 — ``secret_versions`` is append-only in the **database**, not just in…, Immutability is a database guarantee, not merely a missing code path. The owner…, The legitimate append paths keep working under the guard., The documented deletion policy: purging a Secret cascades its history., RLS is preserved: another tenant cannot see a version row, even by id. (+10 more)

### Community 95 - "server_service.py"
Cohesion: 0.07
Nodes (61): agent_heartbeat(), Response, Ingest one metrics sample and hand the agent its next work. A protocol-1 agent…, server_metrics_channel(), ServerStatus, AgentTokenRotation, A pending credential rotation, delivered on the agent's next beat. Served…, acknowledge_rotation() (+53 more)

### Community 96 - "NexusOps (self-hosted infrastructure management and monitoring platform)"
Cohesion: 0.20
Nodes (10): mailpit service (dev SMTP sink + web UI :8025), NexusOps compose stack (8 services on one network), HIGH finding: redirect-following SSRF in uptime monitors (fixed: follow_redirects=False + per-hop guard), SSRF guard (assert_safe_url, per-redirect-hop validation, assert_safe_tcp_endpoint), Mailpit SMTP port internal-only (host-side injection needs extra mapping), Host port knobs (NEXUSOPS_HTTP_PORT/POSTGRES/REDIS/MAILPIT/VITE), SPA entry point (loads /src/main.tsx, dark color-scheme), Uptime monitors -> incidents -> notifications flow (+2 more)

### Community 97 - "REST API surface (/api/v1)"
Cohesion: 0.29
Nodes (7): Cursor (keyset) and offset pagination envelopes, Permission model (data-driven registry, require_permission, wildcard scopes), REST API surface (/api/v1), RBAC registry (PERMISSIONS + ROLE_MATRIX + scope_matches), Adding a new resource: 7-step checklist (model -> migration -> schemas -> service -> router -> tests -> frontend), Alembic migration workflow (autogenerate, models __init__ export, entrypoint apply), Command palette (Ctrl/Cmd+K)

### Community 98 - "fixtures.ts"
Cohesion: 0.23
Nodes (11): EDGE, MAILPIT, ADMIN, Bootstrap, bootstrapVia(), test, ADMIN, openProject() (+3 more)

### Community 99 - "@tanstack/react-query"
Cohesion: 0.05
Nodes (36): DashboardSummary, SearchResult, DashboardPage, Command, CommandPalette(), CommandPaletteProps, STATIC_COMMANDS, BubblePosition (+28 more)

### Community 100 - "redact_mapping"
Cohesion: 0.09
Nodes (35): _is_sensitive_key(), Return a copy of *data* with sensitive values replaced, at any depth. Two…, Substring match on a normalised key so header-style names are caught too.…, redact_mapping(), parametrize, Unit tests for app.core.logging redaction (pure functions only)., No sensitive key name involved: the PEM armor is the only signal., Lists of dicts holding further lists — the shape an agent report takes. (+27 more)

### Community 101 - "certificates.py"
Cohesion: 0.11
Nodes (32): create_certificate(), delete_certificate(), get_certificate(), list_certificates(), alias, AsyncSession, DbDep, delete (+24 more)

### Community 102 - "organization.py"
Cohesion: 0.11
Nodes (25): create_organization(), list_my_organizations(), CurrentUser, DbSessionDep, get, IdentityUser, patch, post (+17 more)

### Community 103 - "Path"
Cohesion: 0.12
Nodes (15): Path, An unloadable CA file must error, never silently fall back to no verify., A throwaway key + self-signed cert for ``localhost`` (real handshakes)., A one-shot HTTPS server; records a failed handshake instead of crashing., A real handshake against a self-signed server must fail verification., Trusting that same cert as a CA lets the identical handshake through., A link-local URL over plain HTTP must fail before any request or write., _self_signed_cert() (+7 more)

### Community 104 - "_rows"
Cohesion: 0.16
Nodes (22): _rows(), _columns(), _integrity_error(), _migrate_from_phase3(), Statement, Phase 4 migration (`f4a5b6c7d8e9`) against a real Phase 3 database. Phase 4 is…, The polymorphic shape is enforced in both directions., The anti-takeover rule is a partial unique index, not a convention. (+14 more)

### Community 105 - "redis service (Redis 7, no persistence, loopback :6390)"
Cohesion: 0.22
Nodes (11): redis service (Redis 7, no persistence, loopback :6390), WebSocket API (/api/v1/ws handshake, frames, limits), WebSocket channels (global, server-metrics, container-logs, deployment-logs, incidents), Deployment engine (queue_deployment / execute_deployment / sweeper backstop), Real-time spine: PostgreSQL system_events + Redis pub/sub, Rollback as a new deployment (rollback_of_id), WebSocket hub (framework-thin, Redis fan-in, per-socket queues), Test suites (pytest unit+integration, vitest, Playwright e2e) (+3 more)

### Community 106 - "NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)"
Cohesion: 0.18
Nodes (12): Agent security model (one-way telemetry, no command channel), Agent enrollment token (X-Agent-Token, nxa_..., SHA-256 at rest), Agent heartbeat exponential backoff (cap 5 min, exit 1 on revoked token), agent/install.sh (enrollment installer), Agent metrics collection (/proc statvfs Docker socket), NexusOps agent (stdlib-only Python, agent/nexusops_agent.py), Agent systemd hardening (ProtectSystem=strict, NoNewPrivileges), Agent ingest API (POST /agent/hello, POST /agent/heartbeat) (+4 more)

### Community 107 - "test_migration_phase5.py"
Cohesion: 0.11
Nodes (36): ``Base.metadata`` and the migrated database must describe the same schema., test_models_and_migrations_do_not_drift(), _columns(), _foreign_keys(), _indexes(), _insert_certificate(), _insert_generation(), _integrity_error() (+28 more)

### Community 108 - "docker_real.py"
Cohesion: 0.08
Nodes (29): ContainerStats, Exception, Build a compact, secret-free description of a provider failure. Only the…, Point-in-time resource usage snapshot., sanitize_error(), _as_float(), _compute_stats(), _cpu_percent() (+21 more)

### Community 109 - "Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)"
Cohesion: 0.25
Nodes (9): API keys (X-API-Key, nxo_..., scope intersection), First boot sequence (api entrypoint migrates, compose never seeds), Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test), Makefile workflows (up/test/lint/typecheck/migrate/seed), HIGH finding: API-key scope bypass for superadmin-owned keys (fixed: scope intersection first), Security audit 2026-09 (26 raw findings -> 20 confirmed, all fixed), HIGH finding: known seed superadmin + API key backdoor (fixed: NEXUSOPS_ALLOW_SEED opt-in, one-time password), Threat model (edge attacker, malicious agent, curious operator, leaked token, SSRF) (+1 more)

### Community 110 - "test_maintenance_sweep.py"
Cohesion: 0.15
Nodes (13): asyncio, ensure_docker_host(), Return the agent-backed Docker host for a server, creating it if needed. The…, The docker-host maintenance sweep must actually reach real hosts., Regression: sync_host_state listed the provider BEFORE registering the host's…, Re-collection stores only lines newer than the newest stored row. The sweep re-…, The sweep and a heartbeat can both see a brand-new container in the same…, Regression: the sweep called asyncio.run() inside its own running loop, so… (+5 more)

### Community 111 - "organization_service.py"
Cohesion: 0.16
Nodes (26): _check(), Forbidden, add_member(), create_organization(), get_organization(), membership_for_user(), AsyncSession, Membership (+18 more)

### Community 112 - "Phase 5 — HTTPS, Certificates and Private-Key Delivery — Design"
Cohesion: 0.10
Nodes (21): 2.1 The six stages, kept distinct, 2.2 Certificate generation state machine, 2.3 Delivery/activation state machine (per certificate × node), 2.4 End-to-end sequence (control plane is the ACME client), 2.5 Failure at any stage, 2. Certificate lifecycle and state transitions, 4.1 CodenamesPhase 5 adds the two codenames already listed in authorization.md §2 — they are **not**, 4.2 Per-type permission and capability gating (+13 more)

### Community 113 - "dnsmock.py"
Cohesion: 0.11
Nodes (25): resolver(), answer(), encode_name(), encode_txt(), forward(), main(), parse_question(), TXT rdata: one or more length-prefixed strings, each ≤ 255 bytes. (+17 more)

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "typing"
Cohesion: 0.05
Nodes (54): CapabilityReport, Agent-facing schemas. Payloads are data only — never executed. Wire protocol v2…, One node-reported capability. ``present`` defaults to false, and a capability…, Schemas for operator-facing alerts., API key schemas. Raw keys appear exactly once, at creation., Schemas for the read-only audit log API. The audit table is append-only; these…, OutModel, Shared Pydantic v2 base schemas. (+46 more)

### Community 116 - "test_tenancy_allowlist.py"
Cohesion: 0.18
Nodes (15): AST, _actual_callers(), _calls_system_scope(), _module_path(), Path, The system-scope allowlist is the only fence around the tenancy carve-out.…, Every module that could open a system scope: ``app/`` plus the scripts., No module may lift tenant isolation without being named in the list. (+7 more)

### Community 117 - "_alembic_config"
Cohesion: 0.12
Nodes (18): _alembic_config(), _at_revision(), _migration_dsn(), _owner_dsn(), Run one Alembic direction against ``database`` through the app's settings path.…, Move ``database`` *back* to ``revision``. The same code path a deployment uses…, Phase 2 adds one migration; heads must not fork., _run_downgrade() (+10 more)

### Community 118 - "dependencies"
Cohesion: 0.33
Nodes (6): dependencies, lucide-react, react, react-dom, react-router-dom, @tanstack/react-query

### Community 119 - "DeploymentDetailPage.test.tsx"
Cohesion: 0.13
Nodes (9): ACTIVE_MEMBERSHIP, ApiError, deploymentDetail(), EMPTY_LOGS, FakeWebSocket, get, ME, post (+1 more)

### Community 120 - "generate_secrets.sh"
Cohesion: 0.47
Nodes (3): existing_real_keys(), replace_or_append(), generate_secrets.sh script

### Community 121 - "ControlHandler"
Cohesion: 0.22
Nodes (7): BaseHTTPRequestHandler, clear_record(), ControlHandler, in_zone(), The journey's only way to publish a record — no shell, no shared volume., set_record(), snapshot()

### Community 122 - "server_payload"
Cohesion: 0.07
Nodes (36): A valid POST /servers body with per-test overrides., server_payload(), test_token_cannot_claim_a_foreign_tenants_node(), test_v1_heartbeat_keeps_the_204_contract(), Regression: a superadmin-owned key is still limited to its scope list. The…, test_scoped_api_key_cannot_exceed_its_grant(), _create_server(), Server CRUD, cascade delete, audit trail rows and audit immutability. (+28 more)

### Community 123 - "test_migration_phase2.py"
Cohesion: 0.15
Nodes (20): alembic_config, alembic_script, Phase 2 migration (`b2c3d4e5f6a7`) against realistic legacy data. The promotion…, Upgrade ``database`` to ``revision``., The pre-Phase-2 shapes: application-scoped environments, per-app dupes., A fresh database reaches the same shape the models describe., _run_migration(), _seed_legacy_data() (+12 more)

### Community 124 - "logging.py"
Cohesion: 0.06
Nodes (44): ASGIApp, liveness(), get, Response, Health probes: liveness (always cheap) and readiness (checks dependencies).…, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness() (+36 more)

### Community 125 - "OperationError"
Cohesion: 0.16
Nodes (17): _demux_docker_stream(), _docker_error(), execute_operation(), OperationError, Exception, A stable, sanitized failure contract for the control plane., Re-validate the operation's parameters locally, against a closed shape., Make control characters safe and bound the result. Never touches container… (+9 more)

### Community 126 - "v1/operations.py"
Cohesion: 0.16
Nodes (22): cancel_operation(), create_operation(), get_operation(), list_operations(), DbDep, Depends, get, post (+14 more)

### Community 127 - "EventLevel"
Cohesion: 0.16
Nodes (31): EventLevel, IncidentEventKind, IncidentSeverity, IncidentStatus, MonitorTargetType, String enum; member names equal values so name/value storage never disagrees., How far a route's *removal* has got, which ``config_state`` cannot say. A route…, What a monitor observes (domain-model.md §2.6, polymorphic targets). ``URL`` is… (+23 more)

### Community 137 - "ProjectDetailPage.tsx"
Cohesion: 0.08
Nodes (30): apiPatch(), ApplicationOut, DockerHostOut, ENVIRONMENT_TYPE_LABELS, EnvironmentType, ProjectDetailPage, configToText(), parseConfigText() (+22 more)

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
Cohesion: 0.11
Nodes (20): _listener_ownership(), _listening_ports(), _live_bundle_id(), _live_files(), _nginx_binary(), nginx_capability(), _nginx_owned_ports(), _nginx_status() (+12 more)

### Community 153 - "types.ts"
Cohesion: 0.04
Nodes (55): AlertOut, CapabilityReport, ChannelOut, ContainerOut, DeliveryOut, DeploymentLogLine, DeploymentStatus, DomainDetailOut (+47 more)

### Community 154 - "nexusops-draft.mjs"
Cohesion: 0.40
Nodes (4): DOCS, meta, SPINE, VERIFY_RULES

### Community 155 - "notification_sender.py"
Cohesion: 0.15
Nodes (18): NotificationError, Any, BaseException, Exception, Low-level notification transports: SMTP email and outgoing webhooks. These…, POST *payload* as JSON to *url*; 2xx is success, anything else raises. Response…, Raised when a delivery attempt fails. Message is safe to persist., Bounded, single-line, content-free error reason. (+10 more)

### Community 156 - "nexusops-challenge.mjs"
Cohesion: 0.33
Nodes (5): CHALLENGE_COMMON, meta, RESEARCH_COMMON, SCHEMA, TASKS

### Community 157 - "Secrets Architecture"
Cohesion: 0.13
Nodes (15): 10. Resolution flow at deploy time, 2.1 Resolution runs inside org scope, 2.2 Migration mapping (applied by `b2c3d4e5f6a7`), 2. Scope model (org / project / environment layering) — **shipped**, 3.1 What this fixed, 3. SecretVersion — append-only history (**shipped in Phase 2**), 4.1 Audit event at resolution time, 4. Resolution authorization (+7 more)

### Community 158 - "test_schemas_agent.py"
Cohesion: 0.11
Nodes (37): AgentContainerIn, AgentHeartbeatIn, AgentHelloIn, Observed container state reported by an agent., Periodic metrics + observed containers from an enrolled agent. Network counters…, First contact from an agent after enrollment; fills static host facts., Whatever the pre-flight returns must satisfy the hello schema., test_capability_report_shape_is_accepted() (+29 more)

### Community 159 - ".state"
Cohesion: 0.13
Nodes (17): computed_field, Derived lifecycle state: revoked wins over used wins over expired., 3.2 `certificate_generations` — one ACME order + one key pair, 3.3 `certificate_deliveries` — per certificate × node, material-free, 3.4 `dns_providers` — customer DNS credentials (metadata-only reads), 3.5 Reused / changed existing entities, 3.6 Monitors, 3.7 Chosen migration sequence and dependency order (decided) (+9 more)

### Community 160 - "build_capabilities"
Cohesion: 0.13
Nodes (15): build_capabilities(), build_facts(), _build_hello_payload(), _enroll(), memory_total_mb(), network_rates(), network_total_bytes(), os_info() (+7 more)

### Community 161 - "alert_service.py"
Cohesion: 0.20
Nodes (15): AlertSeverity, create_alert(), get_alert(), mark_all_read(), mark_read(), AsyncSession, UUID, Alert inbox: insert-only creation plus read/unread bookkeeping. (+7 more)

### Community 162 - "decide"
Cohesion: 0.23
Nodes (18): decide(), matches_token(), Constant-time comparison of the observed TXT values against the token. TXT…, Turn one observation into the verification outcome — pure, no I/O.…, observation(), parametrize, The verification decision: every outcome, without a network. ``decide`` is…, test_a_sweep_invalidates_a_changed_delegation_even_with_the_token() (+10 more)

### Community 163 - "RouteHeader"
Cohesion: 0.18
Nodes (7): field_validator, One header a route adds. ``target`` says where it lands., A fixed host redirect. Phase 4 cannot express a scheme change here. There is…, RouteHeader, RouteRedirect, field_validator, test_redirect_codes_are_restricted()

### Community 164 - "AgentClient"
Cohesion: 0.15
Nodes (8): AgentClient, _docker_raw(), A verifying TLS context. Verification is never disabled. A private/self-hosted…, Refuse to send credentials over plain HTTP to a non-loopback server. The…, One raw Docker API call; returns ``(status, body_bytes)``., _tls_context(), _UnixHTTPConnection, SSLContext

### Community 165 - "certificate_lifecycle.py"
Cohesion: 0.15
Nodes (20): attempt_delay_seconds(), is_retryable(), is_terminal(), next_attempt_at(), datetime, The pre-issuance certificate lifecycle — pure decisions, no I/O, no side…, Whether a generation has spent every attempt it was allowed., Whether a failed generation may be moved back to ``ORDERING``. A failure is… (+12 more)

### Community 166 - "nginx.py"
Cohesion: 0.13
Nodes (23): _header_lines(), _quote(), _rate_zone(), NginxProvider — a pure, deterministic renderer plus the two op wrappers.…, Validate the route's headers and split them by destination., Wrap an already-validated value in quotes for a template slot. Values reaching…, The ``limit_req_zone`` declaration for a rate-limited route., A fixed host redirect, or ``None`` for a normal proxying route. (+15 more)

### Community 167 - "deps.py"
Cohesion: 0.12
Nodes (30): active_memberships(), _attach_organization(), get_current_user(), get_identity(), get_optional_user(), _load_organization(), _load_permissions(), membership_for_org() (+22 more)

### Community 168 - "simulation.py"
Cohesion: 0.19
Nodes (11): Celery application: periodic cadences live here, dynamic work is claimed…, _containers_for(), task, Simulation mode: drive the seeded fleet so dashboards stay alive on a laptop.…, Deterministic smooth value in [base-amplitude, base+amplitude]., Stable per-server container set; one container cycles EXITED occasionally., simulation_tick(), _run() (+3 more)

### Community 169 - "_exec"
Cohesion: 0.23
Nodes (11): UUID, Phase 2.2 — the environment-type correction follows the documented precedence.…, Only the previous migration's ``PROD`` output is corrected. A row already…, Create one legacy (application-scoped) environment per case., Every branch of the slug-first rule, end to end through ``head``., _seed_legacy(), test_correction_preserves_operator_set_values(), test_recognised_slug_alias_wins_over_a_conflicting_name() (+3 more)

### Community 170 - "test_agent_contract.py"
Cohesion: 0.18
Nodes (16): agent_fixture(), _load_agent(), _patch_stats(), Any, fixture, MonkeyPatch, Contract tests: the shipped agent's payloads must satisfy the ingest schemas.…, One-shot docker stats reduce to cpu/mem/limit fields the schema accepts, with… (+8 more)

### Community 171 - "StepLine"
Cohesion: 0.26
Nodes (8): LogLevel, _commit_short(), Deployment runner port plus a faithful simulated implementation.…, Everything a runner needs to execute one deployment., One streamed output line for a step., RunContext, _slug(), StepLine

### Community 172 - "Domain Routing — NexusOps"
Cohesion: 0.18
Nodes (11): 10. Wildcards and catch-all, 11. User journey, 12. API surface, permissions, audit, 13. Monitoring tie-in, 1. Scope and current state, 2. Where nginx runs, 7.1 Flow: config apply with rollback, 7. Apply pipeline via agent operation (+3 more)

### Community 173 - "container.py"
Cohesion: 0.20
Nodes (11): ContainerRemoveOut, HostRef, LogEntryOut, UUID, Container schemas: list/detail read models, log entries, action results., Summary of the docker host a container runs on., Summary of the server associated with a container., One persisted log record (keyset-paginated). (+3 more)

### Community 174 - "apikeys.py"
Cohesion: 0.16
Nodes (19): create_api_key(), list_api_keys(), CurrentUser, DbSessionDep, delete, get, post, Request (+11 more)

### Community 175 - "main"
Cohesion: 0.20
Nodes (10): _interruptible_sleep(), main(), persist_token(), _process_pending_operations(), Atomically store *token* at 0600. Temp file in the same directory + fsync +…, Sleep in short slices so SIGTERM/SIGINT stop the agent promptly., Print the revoked-state notice once per entry; return True thereafter., Claim, execute and report operations — strictly one at a time. (+2 more)

### Community 176 - "Platform Security Model — NexusOps"
Cohesion: 0.14
Nodes (14): make(), 1.1 Real vs simulated today (do not mistake one for the other), 1. Scope, stance, and simulation honesty, 2. Assets, 3. Trust boundaries, 4. Tenant isolation model (summary), 5.1 Threat model table, 5.2 Design notes on selected rows (+6 more)

### Community 177 - "enqueue.py"
Cohesion: 0.39
Nodes (8): after_commit(), _on_commit(), _on_rollback(), Any, AsyncSession, Deferred Celery handoff: enqueue only after the creating transaction commits. A…, Run ``factory`` once the current transaction commits. ``label`` names the work…, _run()

### Community 178 - "journey.spec.ts"
Cohesion: 0.29
Nodes (4): ADMIN, formLogin(), uiGoto(), UNIQUE

### Community 179 - "_node_session"
Cohesion: 0.14
Nodes (17): _dns_stub(), _fake_observe(), _hello_elsewhere(), _mark_reconcile_required_elsewhere(), _node_session(), _pause_render(), fixture, MonkeyPatch (+9 more)

### Community 180 - "_enforce"
Cohesion: 0.33
Nodes (7): _enforce(), node_rate_limit(), _dependency(), Request, _dependency(), Return a dependency keyed on the **authenticated node**, not the IP. A fleet…, Shared fixed-window accounting for every limiter in this module.

### Community 181 - "_nginx_apply"
Cohesion: 0.10
Nodes (29): _fsync_dir(), _nginx_apply(), Materialize the bundle under ``staged/<id>/`` and return that directory.…, Build a self-contained config for ``nginx -t`` over the staged tree. The…, Move the staged tree over the live one, keeping the previous as backup., Put the previous known-good tree back. Returns whether it was possible., Stage → validate → swap → reload, with a rollback on a failed reload., Persist the last apply outcome atomically (temp + rename). (+21 more)

### Community 182 - "_nginx_bootstrap"
Cohesion: 0.14
Nodes (16): _insert_http_includes(), _nginx_bootstrap(), _nginx_config_test(), _nginx_failure_summary(), _nginx_running(), _pid_alive(), Reload nginx via ``-s reload``, falling back to a SIGHUP of the master., Idempotent, minimal, reversible hook-up of the managed include. The only change… (+8 more)

### Community 183 - "v1/channels.py"
Cohesion: 0.15
Nodes (19): Notification channel endpoints. Config is write-only; never echoed back., # NOTE: /deliveries is declared before /{channel_id} so the literal wins., ChannelType, DeliveryStatus, ChannelBase, ChannelCreate, ChannelOut, ChannelUpdate (+11 more)

### Community 184 - "AuthContext"
Cohesion: 0.07
Nodes (55): AuthContext, Resolved identity plus the organization this request acts in.…, ActorType, create_api_key(), list_api_keys(), AsyncSession, Request, UUID (+47 more)

### Community 185 - "20261012_1200-c8d9e0f1a2b3_phase5_certificate_metadata.py"
Cohesion: 0.23
Nodes (13): downgrade(), _drop_certificate_permissions(), _drop_tenant_policies(), _grant(), _in_list(), Phase 5.1 — certificate metadata and the pre-issuance lifecycle. Adds, in one…, Grant the app role on *table*; the migration role GUC carries the name. The…, The two-policy shape every tenant table uses: tenant + system scope. (+5 more)

### Community 186 - "maintenance.py"
Cohesion: 0.09
Nodes (43): Deployment execution task + stuck-deployment sweeper., _run(), _candidates(), _run(), _run(), aggregate_metrics(), _run(), _collect_logs() (+35 more)

### Community 187 - "pytest"
Cohesion: 0.14
Nodes (13): alembic_autogenerate, alembic_migration, CertificateKeyAlgorithm, The key type generated for a generation. Fixed in v1; never client-chosen., created_at server defaults must evaluate per insert, not at table creation., Regression: system_events and audit_logs shipped with DEFAULT 'now()' (quoted…, test_audit_and_event_created_at_defaults_are_dynamic(), Model / migration drift: the schema in the database must match the models.… (+5 more)

### Community 188 - "instant_pacing"
Cohesion: 0.40
Nodes (4): instant_pacing(), fixture, MonkeyPatch, Remove the per-line sleeps; pacing bounds are asserted separately.

### Community 189 - "phase3.spec.ts"
Cohesion: 0.15
Nodes (10): frontend_e2e_fixtures_expect, AGENT, NodeDetail, OperationRow, REPO_ROOT, ref_node_child_process, ref_node_fs, ref_node_os (+2 more)

### Community 190 - "sweep_deployments"
Cohesion: 0.33
Nodes (6): task, Execute one queued deployment. The engine owns all state transitions., Re-enqueue deployments the broker lost; fail ones whose worker died.…, run_deployment(), _run(), sweep_deployments()

### Community 191 - "bundle_summary"
Cohesion: 0.40
Nodes (5): bundle_summary(), Any, Bounded, human-readable bundle metadata for audit rows and UI. Never includes…, Canonical JSON for fingerprint-adjacent comparisons in tests., stable_json()

### Community 192 - "get_settings"
Cohesion: 0.07
Nodes (35): _database_url(), Alembic environment: metadata comes from app.models, URL from app settings., Migrations run as the table **owner**, never as the application role. The owner…, Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online(), _quoted_list() (+27 more)

### Community 193 - "10.1 Slices (each independently reviewable, in order)"
Cohesion: 0.25
Nodes (8): 10.1 Slices (each independently reviewable, in order), 10.2 Test requirements (what "done" means per slice), 10.3.1 Approved decisions (previously open), 10.3.2 Known limitations (accepted, not blockers), 10.3.3 Open items and what they block now, 10.3 Decisions and known limitations, 10.4 Reserved-operation-type lists — one source of truth (required consolidation), 10. Implementation slices, acceptance criteria, tests, limitations

### Community 194 - "test_ws_hub.py"
Cohesion: 0.07
Nodes (46): _close_socket(), Connection, Hub, _is_same_origin(), _params_key(), _parse_payload(), Any, WebSocket (+38 more)

### Community 195 - ".route_file_path"
Cohesion: 0.50
Nodes (3): Where a route's fragment lands, so the service can name it in events., A deterministic, filesystem-safe fragment name for one route., _route_key()

### Community 198 - "README.md - NexusOps overview"
Cohesion: 0.09
Nodes (43): What one reported result did to its operation row. The caller's side effects —…, ResultTransition, docker-compose.dev.yml - dev overlay, docker-compose.docker-sock.yml - docker socket override, docker-compose.yml - full stack definition, docs/agent.md - agent guide, docs/api.md - API guide, Append-only audit log (Postgres BEFORE UPDATE OR DELETE trigger) (+35 more)

### Community 199 - "CertificateStatus"
Cohesion: 0.21
Nodes (12): CertificateStatus, Certificate-level view of the *current* generation, derived, never stored raw.…, assert_pre_issuance(), certificate_status_for(), Return *value* as a pre-issuance state, or refuse it loudly. This is the guard…, The certificate-level status implied by a generation's state. Derived, never…, derive_status(), The certificate's status and its explanation, derived from *generation*.… (+4 more)

### Community 200 - "6. Config rendering — strict allowlists"
Cohesion: 0.67
Nodes (3): 6.1 What is rendered, 6.2 The allowlist (the injection defense), 6. Config rendering — strict allowlists

### Community 201 - "test_monitors_incidents.py"
Cohesion: 0.36
Nodes (7): _create_monitor(), Monitor checks driving the full down -> incident -> recovery lifecycle., Regression: probe headers and URL query credentials never leave the API. Probe…, A monitor's checks, incidents and timeline all live in its organization, so the…, test_check_now_endpoint_runs_immediately(), test_down_then_recover_lifecycle(), test_monitor_responses_mask_probe_credentials()

### Community 202 - "run_async"
Cohesion: 0.10
Nodes (27): flush_pending_publishes(), Wait for frames scheduled by ``after_commit`` hooks to reach Redis. The commit…, task, Flag silent servers OFFLINE, recover returning ones. Safe to overlap., sweep_servers(), task, Claim up to CLAIM_BATCH due monitors and execute each check.…, run_due_monitors() (+19 more)

### Community 203 - "ProxyProvider"
Cohesion: 0.33
Nodes (5): ProxyProvider, Any, Protocol, What ``app.services.proxy_service`` is allowed to assume about a provider. The…, 11. Post-deploy hooks

### Community 206 - "test_agent_ingestion.py"
Cohesion: 0.30
Nodes (10): _enrolled(), _heartbeat(), Agent ingest pipeline: hello, heartbeat, staleness transitions, events., A container absent from a later heartbeat is gone from the daemon., A payload at the agent's cap may be truncated — absence proves nothing., test_heartbeat_at_container_cap_skips_reconciliation(), test_heartbeat_removes_vanished_containers(), test_heartbeat_updates_status_metrics_and_containers() (+2 more)

### Community 208 - "_validate_bundle"
Cohesion: 0.40
Nodes (5): _allowed_bundle_path(), The bundle fingerprint — byte-identical to the control plane's algorithm.…, Independently validate a bundle. Anything unexpected is refused., _tree_fingerprint(), _validate_bundle()

### Community 209 - "current_org"
Cohesion: 0.11
Nodes (17): Whether the runtime connection is the RLS-enforced application role. False…, current_org(), UUID, The organization this unit of work is acting for, if any., A session that spans two organizations is how identity-map hits leak., test_scope_cannot_be_switched_on_a_live_session(), 10. Migration (Phase 1), 1. Tenancy invariants (+9 more)

### Community 212 - "test_notifications.py"
Cohesion: 0.36
Nodes (9): NotificationDelivery, _channel(), _delivery(), UUID, Notification channel + delivery-log endpoints. Regression coverage for GET…, The same event frame consumed twice queues ONE delivery per channel. Every API…, test_dispatch_frame_is_idempotent_across_workers(), test_list_deliveries_filters_by_channel() (+1 more)

### Community 213 - "_FakeAsyncClient"
Cohesion: 0.22
Nodes (3): _FakeAsyncClient, _FakeRequestObj, Scripted httpx.AsyncClient: responses keyed by absolute request URL.

### Community 218 - "redact_log_event"
Cohesion: 0.20
Nodes (14): Any, structlog processor: scrub one record before anything renders it. The pipeline…, Replace every embedded PEM private-key block in *value* with the marker. Only…, Scrub PEM private-key blocks out of one free-text value. The scalar counterpart…, Recursively redact one value of any shape — the depth-agnostic walk. Dicts,…, redact_log_event(), _redact_private_key_blocks(), redact_text() (+6 more)

### Community 219 - "encrypt_str"
Cohesion: 0.23
Nodes (17): encrypt_str(), NotificationChannel, A delivery target (email address / webhook endpoint). ``config_ciphertext``…, _audit(), create_channel(), decrypt_channel_config(), delete_channel(), encrypt_config() (+9 more)

### Community 220 - "test_app_gating.py"
Cohesion: 0.44
Nodes (8): _app_for_environment(), MonkeyPatch, ENVIRONMENT gating contract: docs exposure and HSTS (see .env.example).…, create_app() with get_settings() patched to the given environment., test_non_production_does_not_emit_hsts(), test_non_production_keeps_docs_and_schema(), test_production_emits_hsts(), test_production_hides_docs_and_schema()

### Community 224 - "InvalidTransition"
Cohesion: 0.33
Nodes (5): InvalidTransition, ValueError, Two pre-issuance states with no legal move between them., A generation state this phase's schema cannot express. Raised for the post-…, UnrepresentableState

### Community 226 - "DeploymentRunner"
Cohesion: 0.25
Nodes (6): DeploymentRunner, Protocol, Stream output lines for *step_name*; raise StepFailure to fail it., Adapter interface implemented by real (future) and simulated runners., Return the ordered step names for this run., 2. What survives unchanged

### Community 228 - "test_event_publish_drain.py"
Cohesion: 0.25
Nodes (6): _FakeDb, Frames committed inside a task must reach Redis before that task's loop closes.…, Stands in for an ``AsyncSession`` whose only job here is ``sync_session``. A…, The shape of a worker task whose last statement is a commit., test_run_async_publishes_frames_scheduled_by_the_commit_hook(), commit_then_return()

### Community 230 - "_memory_count_and_ttl"
Cohesion: 0.25
Nodes (7): _memory_count_and_ttl(), Fixed-window counter backed by process memory. Returns (count, ttl)., _clean_memory_windows(), fixture, MonkeyPatch, redis_down(), test_memory_counter_resets_per_window()

### Community 232 - "4. DNS ownership verification"
Cohesion: 0.40
Nodes (5): 4.1 The token, 4.2 The check (control-plane side), 4.3 Anti-takeover rules, 4.4 Sequence: add-domain → verified, 4. DNS ownership verification

### Community 234 - "services/__init__.py"
Cohesion: 0.06
Nodes (41): Dependency factory enforcing a permission; returns 403 when denied., require_permission(), list_audit_logs(), datetime, DbSession, Depends, get, PageParamsDep (+33 more)

### Community 235 - "_pace"
Cohesion: 0.67
Nodes (3): _pace(), Deterministic per-line delay between 0.05s and 0.35s., test_pace_bounds()

### Community 236 - "v1/agent.py"
Cohesion: 0.09
Nodes (37): agent_enroll(), agent_hello(), claim_operation(), _presented_token(), DbDep, post, Request, UUID (+29 more)

### Community 241 - "decrypt_str"
Cohesion: 0.11
Nodes (20): decrypt_str(), _fernet(), parametrize, test_decrypt_with_wrong_ciphertext_raises_value_error(), test_encrypt_decrypt_roundtrip(), 11. Failure handling, 6.1 Threat model — what each envelope actually protects against, 6.2 Recommended v1 design (+12 more)

## Knowledge Gaps
- **496 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+491 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2460 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `6. Tooling: reproducible e2e` connect `maintenance.py` to `test_ws_hub.py`, `core/tenancy.py`, `run_async`, `ContainerDetailPage.tsx`, `Conflict`, `org_scope`, `auth_service.py`?**
  _High betweenness centrality (0.236) - this node is a cross-community bridge._
- **Why does `useEventStream()` connect `ContainerDetailPage.tsx` to `apiGet`, `@tanstack/react-query`, `App.tsx`, `client.ts`, `ServerDetailPage.tsx`, `maintenance.py`?**
  _High betweenness centrality (0.230) - this node is a cross-community bridge._
- **Why does `TenancyScopeError` connect `core/tenancy.py` to `test_certificates.py`, `event_bus.py`, `deps.py`, `assert_error_code`, `apply_scope_to_session`, `current_org`, `enrollment_service.py`, `log_service.py`, `AuthContext`, `maintenance.py`, `test_tenant_isolation.py`, `org_scope`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._
- **Are the 98 inferred relationships involving `AuthContext` (e.g. with `TenancyScopeError` and `MembershipStatus`) actually correct?**
  _`AuthContext` has 98 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `APIModel` (e.g. with `OperationSpec` and `test_specs_reject_unknown_params()`) actually correct?**
  _`APIModel` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `Server` (e.g. with `ServerStatus` and `2.3 Infrastructure — Nodes`) actually correct?**
  _`Server` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 8 inferred relationships involving `record()` (e.g. with `AuthContext` and `client_ip()`) actually correct?**
  _`record()` has 8 INFERRED edges - model-reasoned connections that need verification._