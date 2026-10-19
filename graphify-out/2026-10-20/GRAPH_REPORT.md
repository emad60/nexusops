# Graph Report - nexusops  (2026-10-20)

## Corpus Check
- 417 files · ~548,778 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: (none) 10, .example 1, .service 1)

## Summary
- 8146 nodes · 24244 edges · 254 communities (231 shown, 23 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1972 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6e43de78`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- apiGet
- assert_error_code
- ApiKeysPage.tsx
- test_phase4_routing.py
- container_service.py
- package.json
- resolve_client_ip
- dek_envelope.py
- App.tsx
- test_agent_v2.py
- test_operations.py
- ServerDetailPage.tsx
- APIModel
- client.ts
- validate_config
- test_certificate_manual_issuance.py
- deployment_engine.py
- Container
- enrollment_service.py
- secret_service.py
- test_deployments_simulated.py
- TxtObservation
- metrics_service.py
- test_security.py
- Domain Routing — NexusOps
- schemas/proxy.py
- Product Roadmap — NexusOps Multi-Tenant Platform
- test_agent_backoff.py
- auth_service.py
- nexusops_agent.py
- test_certificate_pebble.py
- hub.py
- AcmeDirectory
- rate_limit.py
- docker_hosts.py
- integration/test_certificate_issuance.py
- OperationType
- v1/search.py
- models/__init__.py
- logging.py
- DockerProvider
- test_monitor_transport.py
- test_migration_phase5212.py
- AuthContext.tsx
- record
- AuthContext
- test_kek_health_api.py
- test_phase3_nodes.py
- UnprocessableEntity
- test_ws_hub.py
- dns_provider_service.py
- AuthorizationState
- proxy_service.py
- DeterministicKEKProvider
- incident_service.py
- test_agent_nginx_contract.py
- users.py
- alembic
- v1/channels.py
- integration/conftest.py
- compilerOptions
- v1/deployments.py
- v1/operations.py
- dns_verifier.py
- test_phase2_environments.py
- route_service.py
- test_schema_redaction.py
- publish
- AuditLog
- CertificateGenerationState
- UnrepresentableState
- SecretResolutionError
- test_nginx_renderer.py
- domains.py
- api service (FastAPI / uvicorn :8000)
- monitors.py
- PageParams
- test_acme_accounts.py
- monitor_service.py
- test_phase2_secrets.py
- RolesPage.tsx
- test_schemas_server.py
- InvalidName
- tests/conftest.py
- server_service.py
- user_service.py
- devDependencies
- NotFound
- Certificate
- test_payload_crypto.py
- DomainStatus
- dns/__init__.py
- containers.py
- certificate_service.py
- test_phase21_secret_version_integrity.py
- test_dns_propagation.py
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- journey.spec.ts
- test_org_dek_envelope.py
- redact_mapping
- decide
- docker_real.py
- list_dns_providers
- _exec
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- test_migration_phase5.py
- test_migration_phase532.py
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- organization_service.py
- CheckResult
- middleware.py
- dnsmock.py
- scripts
- ScopedSession
- test_tenancy_allowlist.py
- _alembic_config
- ownership
- @tanstack/react-query
- generate_secrets.sh
- _invoke_sender
- apply_scope_to_session
- _run_migration
- test_dns_providers.py
- OperationError
- log_service.py
- 20261018_1200-d0e1f2a3b4c5_phase532_manual_dns01.py
- install.sh
- docker-entrypoint.sh
- integration/__init__.py
- DockerHostsPage.test.tsx
- CLAUDE.md - project graphify rules
- Graphify query workflow (query / path / explain / update)
- frontend/index.html - SPA shell
- NexusOps Favicon — stylized letter 'N' lettermark in sky blue (#38bdf8) on a dark navy rounded square (#0b1120, 7px corner radius)
- nexusops-backend
- _Attempt
- 20261009_1000-c3d4e5f6a7b8_enforce_secret_version_integrity.py
- postgres service (PostgreSQL 17, loopback :5433)
- phase4.spec.ts
- nexusops-understand.mjs
- Invisible account lockout (5 fails -> 15 min, enumeration resistance)
- nginx_capability
- types.ts
- nexusops-draft.mjs
- v1/secrets.py
- nexusops-challenge.mjs
- Secrets Architecture
- test_schemas_agent.py
- .state
- test_kek_vault_transit_live.py
- alert_service.py
- _View
- routes.py
- AgentClient
- get_settings
- _rows
- _FakeCloudflare
- redact_log_event
- pytest
- test_agent_contract.py
- test_kek_vault_transit.py
- monitor_transport.py
- env.py
- get_latest_server_metrics
- certificate_issuance.py
- Platform Security Model — NexusOps
- Node & Agent Architecture
- v1/auth.py
- test_phase541_route_binding.py
- list_sessions
- _nginx_apply
- _run_downgrade
- events.py
- SystemEvent
- 20261012_1200-c8d9e0f1a2b3_phase5_certificate_metadata.py
- _guard
- Phase 5 — HTTPS, Certificates and Private-Key Delivery — Design
- Deployment Architecture — NexusOps (target state)
- phase3.spec.ts
- Settings
- ChannelCreate
- enqueue.py
- 10. Implementation slices, acceptance criteria, tests, limitations
- ApplicationBase
- route_certificate_service.py
- v1/certificates.py
- entries
- 20261014_1200-a7b8c9d0e1f2_isolate_org_dek_envelopes.py
- 20261010_1200-f4a5b6c7d8e9_phase4_domains_and_routes.py
- certificate_order.py
- v1/health.py
- SimulatedDeploymentRunner
- Domain Model — NexusOps as a Multi-Tenant Platform
- _LibrarySession
- _credential_seam
- test_agent_ingestion.py
- VaultTransitKEKProvider
- 20261019_1000-e1f2a3b4c5d6_phase541_route_certificate_binding.py
- 20261008_1200-b2c3d4e5f6a7_add_projects_and_environments.py
- NotificationChannel
- 20261014_1600-b8c9d0e1f2a3_phase522_providers_acme_material.py
- 6. Private-key encryption and key management
- _FakeAsyncClient
- 20261009_1100-d4e5f6a7b8c9_correct_legacy_environment_types.py
- 20261004_1200-e7c4a2b9d1f3_add_operations_framework.py
- README.md - NexusOps overview
- api_key_service.py
- _TaskRecorder
- update_organization
- Platform Vision — NexusOps
- stable_json
- 20260923_1000-c4e2a1f7b9d3_rename_server_codenames_to_node.py
- sweep_deployments
- notification_service.py
- ControlHandler
- 20261012_1600-f5a6b7c8d9e0_phase5_org_dek_envelope.py
- _bootstrap_resolver
- role_service.py
- _validate_ip
- errors.py
- .__init__
- enums.py
- servers.py
- Append-only audit log (Postgres BEFORE UPDATE OR DELETE trigger)
- v1/agent.py
- projects.py
- AuditLogPage.test.tsx
- client_ip
- instant_pacing
- .__tablename__
- test_app_gating.py
- .__init__
- 20260922_1000-a3f1c8d24b6e_add_tenancy_foundation.py
- get_meta
- ContainerListPage.test.tsx
- 20261009_1300-a1b2c3d4e5f6_add_phase3_nodes_and_agent_v2.py
- .dispatch
- dependencies
- LoginPage.tsx
- _live_bundle_id
- 20261009_1200-e5f6a7b8c9d0_fix_environment_type_precedence.py
- 20261016_1000-c9d0e1f2a3b4_phase53_generation_directory.py
- router.py

## God Nodes (most connected - your core abstractions)
1. `AuthContext` - 180 edges
2. `APIModel` - 160 edges
3. `get_settings()` - 114 edges
4. `record()` - 103 edges
5. `Server` - 96 edges
6. `NotFound` - 94 edges
7. `apiGet()` - 91 edges
8. `Conflict` - 88 edges
9. `publish()` - 86 edges
10. `assert_error_code()` - 82 edges

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

## Communities (254 total, 23 thin omitted)

### Community 0 - "apiGet"
Cohesion: 0.06
Nodes (90): apiDelete(), apiGet(), apiPatch(), apiPost(), ApplicationOut, ENVIRONMENT_TYPE_LABELS, EnvironmentType, IncidentEventOut (+82 more)

### Community 1 - "assert_error_code"
Cohesion: 0.07
Nodes (63): assert_error_code(), error_of(), Unwrap an API error envelope., Assert envelope shape + code; returns the inner error object., Regression: lockout must not leak which emails exist. After login_max_attempts…, test_locked_account_response_is_indistinguishable(), _app_role_dsn(), _audits() (+55 more)

### Community 2 - "ApiKeysPage.tsx"
Cohesion: 0.09
Nodes (19): ApiKeyOut, ApiKeysPage, ApiKeyCreatedOut, handleCopyKey(), copyText(), describeError(), EMPTY_FORM, GROUP_STYLE (+11 more)

### Community 3 - "test_phase4_routing.py"
Cohesion: 0.04
Nodes (149): MonitorTargetType, What a monitor observes (domain-model.md §2.6, polymorphic targets). ``URL`` is…, task, Re-prove control of every domain whose next check is due. Covers three cases…, Keep every routed node's live configuration matching the desired bundle. One…, sweep_domains(), sweep_routes(), _candidates() (+141 more)

### Community 4 - "container_service.py"
Cohesion: 0.07
Nodes (63): DockerHostStatus, DockerHost, clip(), Truncate *text* to *limit* characters, stripping control chars., describe_provider_error(), is_simulated(), provider_for(), Exception (+55 more)

### Community 5 - "package.json"
Cohesion: 0.13
Nodes (15): name, private, type, version, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom (+7 more)

### Community 6 - "resolve_client_ip"
Cohesion: 0.18
Nodes (21): _is_trusted(), _parse_networks(), Request, Client-IP resolution behind chained reverse proxies. The API never takes TCP…, Parse a comma-separated CIDR list; malformed entries are skipped., Real client address for *request* per the trust model above., resolve_client_ip(), make_request() (+13 more)

### Community 7 - "dek_envelope.py"
Cohesion: 0.11
Nodes (38): RuntimeError, Raised when a unit of work touches tenant data with no valid org scope. This is…, TenancyScopeError, OrganizationDekEnvelope, The organization's Fernet DEK, **wrapped** by the configured KEK provider. The…, _claim_first_dek(), _context(), _load() (+30 more)

### Community 8 - "App.tsx"
Cohesion: 0.04
Nodes (103): DeploymentOut, Page, ProjectOut, AlertsPage, App(), AuditLogPage, ContainerListPage, DeploymentListPage (+95 more)

### Community 9 - "test_agent_v2.py"
Cohesion: 0.06
Nodes (51): agent_fixture(), _load_agent(), Any, fixture, parametrize, Path, Agent protocol v2: honest metrics, capability detection, and the executor. The…, Phase 4 shipped three nginx ops — no file primitive, no command primitive. (+43 more)

### Community 10 - "test_operations.py"
Cohesion: 0.07
Nodes (56): OperationStatus, Lifecycle of one node operation (node-agent-architecture.md §5.1).…, expire_operations(), Expire node operations past their deadline — pending and claimed alike. A…, _dispatch(), _dispatch_body(), _enrolled_node(), _mutate_in_system_scope() (+48 more)

### Community 11 - "ServerDetailPage.tsx"
Cohesion: 0.06
Nodes (42): ContainerOut, MetricPoint, ServerDetail, ServerSummary, ChartSeries, LineChart(), LineChartProps, PAD (+34 more)

### Community 12 - "APIModel"
Cohesion: 0.03
Nodes (128): AlertOut, Schemas for operator-facing alerts., ApiKeyCreateRequest, API key schemas. Raw keys appear exactly once, at creation., ApplicationSummary, Application API schemas., Application as embedded in project outputs (no deployment summary)., AuditOut (+120 more)

### Community 13 - "client.ts"
Cohesion: 0.05
Nodes (54): API_BASE, ApiError, apiRequest(), buildUrl(), extractError(), getAccessToken(), getActiveOrgId(), onActiveOrgChange() (+46 more)

### Community 14 - "validate_config"
Cohesion: 0.06
Nodes (42): EnvironmentType, Kind of a project-scoped deployment environment (Phase 2). Descriptive only —…, EnvironmentBase, EnvironmentUpdate, _normalise_environment_type(), field_validator, Shared environment fields., Partial environment update; omitted fields are left untouched. Config is… (+34 more)

### Community 15 - "test_certificate_manual_issuance.py"
Cohesion: 0.09
Nodes (50): _challenge_value(), _create_domain(), _credential_seam(), _dns(), _document(), _events(), _FakeCloudflare, _issue() (+42 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.10
Nodes (59): deployment_log_channel(), Canonical Redis pub/sub channel names shared by API, workers and WS hub., Deployment, DeploymentStep, AlertSeverity, DeploymentStatus, EventLevel, StepStatus (+51 more)

### Community 17 - "Container"
Cohesion: 0.07
Nodes (42): ContainerHealth, ContainerStatus, Container, Observed container state mirrored from an agent or docker provider., ContainerStats, DockerProviderError, Provider abstraction for docker hosts (real daemon or simulated). Providers are…, A provider operation failed. ``str()`` is safe to show/log. (+34 more)

### Community 18 - "enrollment_service.py"
Cohesion: 0.11
Nodes (31): generate_enrollment_token(), An enrollment credential (``nxk_``): single-use, short-lived, org-scoped.…, Return the active org id or raise; used by services that need it explicitly., require_org(), EnrollmentToken, One single-use credential that enrolls (or claims) exactly one node., Whether the row could still be redeemed (not a race-safe check)., EnrollmentTokenState (+23 more)

### Community 19 - "secret_service.py"
Cohesion: 0.07
Nodes (66): digest_of(), encrypt_str(), Short server-verifiable digest used for change detection display. HMAC-SHA256…, An encrypted configuration value, scoped to org, project or environment.…, One immutable value of a :class:`Secret` — append-only history. A row is…, Secret, SecretVersion, _actor_type() (+58 more)

### Community 20 - "test_deployments_simulated.py"
Cohesion: 0.15
Nodes (27): execute_deployment(), Run one deployment to a terminal state. Never raises; safe to re-run., _as_worker(), _delivery_chain(), _owner_ctx(), _queue(), _queued_with_recorder(), Deployment engine over the simulated runner: success, failure, rollback. (+19 more)

### Community 21 - "TxtObservation"
Cohesion: 0.09
Nodes (28): check_once(), nameserver_summary(), observe(), _observer_name(), observer_window(), PropagationResult, Has the challenge record actually reached the authoritative nameservers?…, One TXT record name and **every** value that must be present there. A set… (+20 more)

### Community 22 - "metrics_service.py"
Cohesion: 0.12
Nodes (30): MetricGranularity, aggregate_rollups(), dashboard_summary(), ensure_server(), _extra_object(), granularity_for_range(), latest_for_servers(), _prune() (+22 more)

### Community 23 - "test_security.py"
Cohesion: 0.07
Nodes (52): argon2, argon2_exceptions, Unauthorized, create_access_token(), decode_access_token(), generate_agent_token(), generate_api_key(), generate_refresh_token() (+44 more)

### Community 24 - "Domain Routing — NexusOps"
Cohesion: 0.08
Nodes (27): 10. Wildcards and catch-all, 11. User journey, 12. API surface, permissions, audit, 1. Scope and current state, 2. Where nginx runs, 3.1 Domain, 3.2 Route, 3. Entities (per domain-model.md §2.4) (+19 more)

### Community 25 - "schemas/proxy.py"
Cohesion: 0.09
Nodes (23): NginxApplyParams, NginxBootstrapParams, NginxStatusParams, model_validator, RateLimit, Proxy bundle and operation-parameter schemas — the agent-facing config…, One header a route adds. ``target`` says where it lands., One route's request-rate ceiling (rendered as a ``limit_req_zone``). (+15 more)

### Community 26 - "Product Roadmap — NexusOps Multi-Tenant Platform"
Cohesion: 0.12
Nodes (17): What one reported result did to its operation row. The caller's side effects —…, ResultTransition, 0. Stance, 10. Phase 7 — Teams, grants & custom roles — **proposal, not implemented**, 11. Phase 8 — Backups — **proposal, not implemented**, 12. Phase 9 — Billing & metering — **proposal, not implemented**, 13.1 Scope-creep gates — what must be true before each expansion, 13. First commercially meaningful version (+9 more)

### Community 27 - "test_agent_backoff.py"
Cohesion: 0.16
Nodes (20): agent_fixture(), _install_sleep(), fake_sleep(), _load_agent(), _patch_host(), Any, fixture, MonkeyPatch (+12 more)

### Community 28 - "auth_service.py"
Cohesion: 0.10
Nodes (50): active_memberships(), Membership, The user's memberships in non-suspended organizations, oldest first. Reads only…, System scope bound to *db*, for rows that have no organization. Used by exactly…, system_write_scope(), ActorType, AuditResult, _audit() (+42 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.06
Nodes (51): build_capabilities(), build_facts(), build_heartbeat(), _build_hello_payload(), collect_container_stats(), collect_containers(), _container_ports(), _container_status() (+43 more)

### Community 30 - "test_certificate_pebble.py"
Cohesion: 0.09
Nodes (57): _assert_no_material(), _challenge_url(), _create_domain(), _create_provider(), _decrypted(), _events(), _forbidden_provider(), _issue() (+49 more)

### Community 31 - "hub.py"
Cohesion: 0.12
Nodes (25): Central configuration. All runtime configuration flows through this module so…, AppError, Exception, Base class for expected, client-facing errors., _authenticate_api_key(), _authenticate_jwt(), _bind_organization(), _load_permissions() (+17 more)

### Community 32 - "AcmeDirectory"
Cohesion: 0.03
Nodes (108): AbstractAsyncContextManager, Which known directory this account is at; ``None`` when the URL is neither.…, AcmeDirectory, Which certificate authority a per-organization ACME account belongs to. A…, Whether this directory issues publicly trusted certificates. The single…, Whether a certificate from this directory is trusted by a browser. False for…, Short operator-facing name, stored in metadata and shown in the API., The directory a stored URL names, or ``None`` when it names none. ``None``… (+100 more)

### Community 33 - "rate_limit.py"
Cohesion: 0.17
Nodes (17): RateLimited, _memory_count_and_ttl(), rate_limit(), Redis-backed fixed-window rate limiting as a FastAPI dependency factory. Auth-…, Fixed-window counter backed by process memory. Returns (count, ttl)., Return a dependency enforcing *limit* requests per window per IP. With…, _clean_memory_windows(), _FakeRequest (+9 more)

### Community 34 - "docker_hosts.py"
Cohesion: 0.07
Nodes (54): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+46 more)

### Community 35 - "integration/test_certificate_issuance.py"
Cohesion: 0.11
Nodes (40): load(), pending_cleanup(), The generation's order document, or an empty one. **Never raises.** A malformed…, Challenges whose record this platform created and has not confirmed gone.…, _AmbiguousZone, _create_domain(), _create_provider(), _document_with_running_attempt() (+32 more)

### Community 36 - "OperationType"
Cohesion: 0.12
Nodes (20): OperationType, The whitelist. Nothing outside this enum ships as an exec surface. Each type…, Any, Validate *params* against the type's model and return the stored form.…, validate_params(), MonkeyPatch, The operation dispatch whitelist is a contract, not a convention.…, A type whose capability cannot be confirmed must not be dispatchable. (+12 more)

### Community 37 - "v1/search.py"
Cohesion: 0.08
Nodes (43): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+35 more)

### Community 38 - "models/__init__.py"
Cohesion: 0.06
Nodes (88): _org_scoped_classes(), Mapped classes marked :class:`~app.models.base.OrgScoped`. Reads the mapper…, ``before_flush`` handler: own new rows, and refuse rows that change hands.…, _stamp_org_on_flush(), AcmeAccount, The per-organization ACME account and its protected account key. One account…, One ACME account: its directory, its CA-side URL, and its wrapped key., Base (+80 more)

### Community 39 - "logging.py"
Cohesion: 0.03
Nodes (153): asyncio, get_logger(), Structured logging via structlog. Every log record carries timestamp, level,…, current_org(), current_scope(), org_scope(), UUID, Tenancy core: organization scope, the session guard and the RLS GUC. Everything… (+145 more)

### Community 40 - "DockerProvider"
Cohesion: 0.08
Nodes (12): DockerProvider, Any, datetime, Protocol, List containers visible to the provider., Inspect a single container by id (short ids allowed)., List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``., List volumes: keys ``name``, ``driver``, ``mountpoint``. (+4 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.16
Nodes (26): get_transport(), Deterministic fake checker for ``sim://`` monitors and demo environments.…, Pick the transport matching the monitor URL scheme., SimulatedTransport, _strip_query(), _check(), clock(), FakeClock (+18 more)

### Community 42 - "test_migration_phase5212.py"
Cohesion: 0.13
Nodes (25): _columns(), Phase 5.2.1.2 migration (`a7b8c9d0e1f2`): the envelope leaves…, ``column -> (data_type, is_nullable)`` for *table*., ``(org_id, ciphertext, generation)`` for every populated envelope, ordered., The move creates rows only where there was key material. A row with a NULL…, Two envelopes for one tenant are refused by the database, not by a service., F3: a negative generation, and either half of an inconsistent pair, fail. The…, RLS plus the grant: the policies are only load-bearing for a non-owner role.… (+17 more)

### Community 43 - "AuthContext.tsx"
Cohesion: 0.02
Nodes (83): Membership, SearchResult, User, AuthContext, AuthProvider(), AuthState, isOrgSelectionError(), MeResponse (+75 more)

### Community 44 - "record"
Cohesion: 0.12
Nodes (51): Application, DeploymentEnvironment, Project, A **project-scoped** deployment environment (Phase 2 promotion). The…, Any, AsyncSession, Request, UUID (+43 more)

### Community 45 - "AuthContext"
Cohesion: 0.04
Nodes (71): _attach_organization(), AuthContext, get_current_user(), get_identity(), get_optional_user(), _load_organization(), _load_permissions(), membership_for_org() (+63 more)

### Community 46 - "test_kek_health_api.py"
Cohesion: 0.11
Nodes (21): Drop every cached verdict (tests, and any future configuration reload)., reset_health_cache(), _clear_health_cache(), fixture, MonkeyPatch, parametrize, Provider health on the readiness surface, seen through the API. The approved…, A probe is unauthenticated in most deployments; it must leak nothing. (+13 more)

### Community 47 - "test_phase3_nodes.py"
Cohesion: 0.14
Nodes (35): Run the enclosed block with tenant filtering off (maintenance only). ``reason``…, system_scope(), _create_token(), _dispatch(), _enroll(), _enrolled_node(), _load_agent_module(), _mutate_in_system_scope() (+27 more)

### Community 48 - "UnprocessableEntity"
Cohesion: 0.09
Nodes (54): BadRequest, UnprocessableEntity, assert_safe_tcp_endpoint(), assert_safe_url(), _is_forbidden_address(), ValueError, _raise_block(), SSRF guard applied to every operator-supplied outbound URL. Monitors and… (+46 more)

### Community 49 - "test_ws_hub.py"
Cohesion: 0.07
Nodes (46): _close_socket(), Connection, _frame_org(), Hub, _params_key(), _parse_payload(), Any, WebSocket (+38 more)

### Community 50 - "dns_provider_service.py"
Cohesion: 0.09
Nodes (48): DnsProvider, One stored DNS credential plus the scope it is allowed to touch., DnsProviderKind, Which DNS API a stored credential speaks to. One member in v1 (Cloudflare) —…, provider_for(), The credential-verification implementation for *kind*. Separate from…, DnsProviderCreate, DnsProviderUpdate (+40 more)

### Community 51 - "AuthorizationState"
Cohesion: 0.07
Nodes (9): AuthorizationState, One authorization's status after a poll., Poll one authorization until it is not ``pending``, or the deadline passes., Poll until the authorization leaves ``pending``, or the deadline passes. The…, _FakeAcme, The CA side of the seam, honest about the outcomes that matter here., _FakeAcme, The CA side of the seam, sharing an order store across two sessions. A manual… (+1 more)

### Community 52 - "proxy_service.py"
Cohesion: 0.05
Nodes (107): ListenerOwnership, ProxyApplyOutcome, Terminal outcome of one ``nginx.apply`` operation on a node., Who holds one required listener port, per the node's pre-flight. The…, Alias for :attr:`extra`, so the API can expose open-ended agent facts. The…, Server, Operation, Whether the agent reported this operation as successful. A terminal check, not… (+99 more)

### Community 53 - "DeterministicKEKProvider"
Cohesion: 0.05
Nodes (61): _derive(), DeterministicKEKProvider, The deterministic in-process provider — tests and explicitly configured dev.…, A per-(binding, key version) key: HKDF-style derivation. Two properties, both…, Deterministic wrap/unwrap/rewrap over an in-process AEAD., Bump the modelled KEK version, so a test can prove rewrap moves it., EncryptionContext, KEKContextMismatchError (+53 more)

### Community 54 - "incident_service.py"
Cohesion: 0.12
Nodes (45): ActionCtx, acknowledge_incident(), add_incident_note(), get_incident(), list_incidents(), DbDep, Depends, get (+37 more)

### Community 55 - "test_agent_nginx_contract.py"
Cohesion: 0.07
Nodes (57): CapabilityReport, One node-reported capability. ``present`` defaults to false, and a capability…, _agent_bundle(), agent_fixture(), _bootstrap_fixture(), _load_agent(), Any, fixture (+49 more)

### Community 56 - "users.py"
Cohesion: 0.15
Nodes (25): create_user(), deactivate_user(), get_user(), list_users(), CurrentUser, DbSessionDep, get, patch (+17 more)

### Community 57 - "alembic"
Cohesion: 0.07
Nodes (3): alembic, Fix pre-existing model/migration drift (surfaced by the new drift check). Two…, sqlalchemy_dialects

### Community 58 - "v1/channels.py"
Cohesion: 0.15
Nodes (27): create_channel(), delete_channel(), get_channel(), list_channels(), list_deliveries(), DbDep, Depends, get (+19 more)

### Community 59 - "integration/conftest.py"
Cohesion: 0.04
Nodes (83): dispose_engine(), close_redis(), lifespan(), Start the WS hub + notification dispatcher; tear them down cleanly., _admin_dsn(), _clean_slate(), client(), _ensure_database() (+75 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "v1/deployments.py"
Cohesion: 0.10
Nodes (44): _attribute_step_idx(), cancel_deployment(), _emails_for(), get_deployment(), list_application_deployments(), list_deployment_logs(), _list_deployments(), _parse_sort() (+36 more)

### Community 62 - "v1/operations.py"
Cohesion: 0.18
Nodes (20): cancel_operation(), create_operation(), get_operation(), list_operations(), DbDep, Depends, get, post (+12 more)

### Community 63 - "dns_verifier.py"
Cohesion: 0.10
Nodes (26): _aggregate_answers(), _ask_one(), discover_authoritative_nameservers(), _discover_nameservers(), _normalise_ns(), observe(), observe_txt_record(), public_addresses() (+18 more)

### Community 64 - "test_phase2_environments.py"
Cohesion: 0.18
Nodes (22): _environment(), _project(), parametrize, Phase 2: project-scoped environments, config layering, and their isolation. The…, Uniqueness is ``(project_id, slug)`` — not instance-wide., The update path is validated too (the pre-Phase-2 gap)., Knowing an environment UUID is not access: the project link must hold., Another tenant cannot reach the project, its environments, or its detail. (+14 more)

### Community 65 - "route_service.py"
Cohesion: 0.10
Nodes (48): Last nginx apply outcome for a route, as reported by its node's agent.…, RouteConfigState, One hostname+path served from one container on one node. Relationship rules the…, Route, _actor(), _apply_or_defer(), _conflicting_route(), create_route() (+40 more)

### Community 66 - "test_schema_redaction.py"
Cohesion: 0.18
Nodes (17): is_sensitive_header(), mask_sensitive_headers(), True when *name* looks like it carries a credential (Authorization etc.)., Return a copy of *headers* with sensitive values replaced by a mask., mask_target(), Human-readable masked target safe to expose over the API. For webhook families…, _monitor_out(), Outbound-schema redaction: monitor probe credentials and webhook targets.… (+9 more)

### Community 67 - "publish"
Cohesion: 0.14
Nodes (25): get_redis(), ping(), Shared async Redis client., _after_commit_publish(), _after_rollback_drop(), event_frame_from_row(), publish(), _publish_after_commit() (+17 more)

### Community 68 - "AuditLog"
Cohesion: 0.22
Nodes (18): AuditLog, _latest_audit(), _latest_event(), _list_ids(), Any, UUID, Phase 3.1 — pre-organization auth events are instance-level and tenant-…, No account => no actor => a system instance-level row, as before. (+10 more)

### Community 69 - "CertificateGenerationState"
Cohesion: 0.05
Nodes (85): directory_required_predicate(), material_guard_predicate(), one_live_generation_predicate(), pre_issuance_predicate(), The SQL predicate of ``uq_cert_generations_one_live``. Built from…, The states in which a generation carries no material *by construction*.…, The SQL of ``ck_certificate_generations_material_guard``. Derived from the enum…, A generation that outlives the order must name the CA that issued it. The… (+77 more)

### Community 70 - "UnrepresentableState"
Cohesion: 0.33
Nodes (5): InvalidTransition, ValueError, Two states with no legal move between them., A state the caller's context cannot accept. Two callers narrow differently and…, UnrepresentableState

### Community 71 - "SecretResolutionError"
Cohesion: 0.20
Nodes (9): Exception, A ``${secret:KEY}`` reference could not be resolved. Fail-closed. Carries…, SecretResolutionError, 1.1 The honest defect list, 1. Current state — what is real and what is simulated, 6.1 Core items, 6.2 Further findings-sourced items (tracked in this doc only — not in the roadmap's hardening table), 6. Current-code hardening listEvery item below was a defect in the code as of this document's date, evidenced (+1 more)

### Community 72 - "test_nginx_renderer.py"
Cohesion: 0.04
Nodes (85): _header_lines(), NginxProvider, Any, ValueError, _quote(), _rate_zone(), NginxProvider — a pure, deterministic renderer plus the two op wrappers.…, Validate the route's headers and split them by destination. (+77 more)

### Community 73 - "domains.py"
Cohesion: 0.15
Nodes (31): create_domain(), delete_domain(), _enqueue_verification(), get_domain(), list_domain_routes(), list_domains(), _project_names(), alias (+23 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "monitors.py"
Cohesion: 0.17
Nodes (31): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+23 more)

### Community 76 - "PageParams"
Cohesion: 0.06
Nodes (60): list_alerts(), Depends, Alert inbox endpoints. Authenticated users see the shared operator feed., Unread alerts first, then newest first., API key routes — self-service management of the caller's own machine…, list_audit_logs(), datetime, DbSession (+52 more)

### Community 77 - "test_acme_accounts.py"
Cohesion: 0.06
Nodes (73): account_for(), account_key(), account_key_fingerprint(), AcmeAccountKeyUnavailable, _actor(), find_account(), generate_account_key(), mark_used() (+65 more)

### Community 78 - "monitor_service.py"
Cohesion: 0.12
Nodes (43): is_simulation_url(), True when *url* targets the built-in simulated checker (``sim://``)., MonitorStatus, Monitor, One probe. Targets are polymorphic since Phase 4 (domain-model.md §2.6).…, Drop the query string so signed tokens never appear in error text., Public alias: redact any query string from a URL before display/persist., strip_query() (+35 more)

### Community 79 - "test_phase2_secrets.py"
Cohesion: 0.13
Nodes (27): decrypt_str(), _fernet(), _env(), _project(), Phase 2 secrets: layered scope, immutable versions, rollback, isolation. Two…, Two racing rotations must both be kept and never share a version number., Another tenant cannot read, rotate, roll back or even enumerate the secret., The documented example: same key at three scopes; most specific wins. (+19 more)

### Community 80 - "RolesPage.tsx"
Cohesion: 0.11
Nodes (15): Role, RolesPage, describeError(), GROUP_STYLE, LEGEND_STYLE, OPTION_STYLE, PermissionSpec, roleAllows() (+7 more)

### Community 81 - "test_schemas_server.py"
Cohesion: 0.21
Nodes (22): Payload for registering a server., Partial update. ``tags`` replaces the full set when provided., ServerCreate, ServerUpdate, _base(), parametrize, Unit tests for app.schemas.server (validation only, no I/O)., test_empty_ip_is_allowed_but_whitespace_collapses() (+14 more)

### Community 82 - "InvalidName"
Cohesion: 0.09
Nodes (43): _canonicalize(), canonicalize_name(), canonicalize_path(), canonicalize_record_name(), _check_labels(), _check_not_ip(), hostname_is_covered(), _idna() (+35 more)

### Community 83 - "tests/conftest.py"
Cohesion: 0.22
Nodes (7): configure_test_env(), Test bootstrap: pin every cached setting BEFORE the first ``app`` import. The…, KEY=VALUE pairs from the repo .env (first definition wins); never logged., Export the exact settings the app caches; host values cannot leak through., _read_dot_env(), os, pathlib

### Community 84 - "server_service.py"
Cohesion: 0.05
Nodes (78): agent_heartbeat(), Response, Ingest one metrics sample and hand the agent its next work. A protocol-1 agent…, server_metrics_channel(), ServerStatus, AgentTokenRotation, A pending credential rotation, delivered on the agent's next beat. Served…, acknowledge_rotation() (+70 more)

### Community 85 - "user_service.py"
Cohesion: 0.12
Nodes (40): MembershipStatus, _apply_deactivation(), _assert_not_last_active_member(), _assert_not_last_active_superadmin(), create_user(), deactivate_user(), get_by_email(), get_member() (+32 more)

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "NotFound"
Cohesion: 0.10
Nodes (44): Conflict, NotFound, _active_org(), _bounded(), cancel_operation(), claim_operation(), create_operation(), ensure_dispatchable() (+36 more)

### Community 88 - "Certificate"
Cohesion: 0.08
Nodes (47): Certificate, CertificateGeneration, One requested certificate: an identity, its lifecycle view, no material., One ACME order + one key pair. Renewal inserts a new row, never mutates one.…, Map a system event type to the alert severity it deserves., severity_for_event(), confirm_manual_publication(), _dns_mode() (+39 more)

### Community 89 - "test_payload_crypto.py"
Cohesion: 0.08
Nodes (59): decrypt(), decrypt_str(), encrypt(), fingerprint(), _parse_header(), PayloadContext, PayloadContextMismatch, PayloadDecryptionError (+51 more)

### Community 90 - "DomainStatus"
Cohesion: 0.06
Nodes (70): The exact TXT owner name a user must publish at their provider., verification_record_name(), DomainStatus, Ownership-verification lifecycle of a Domain (domain-routing.md §4). ``STALE``…, Domain, One DNS name an organization is proving it controls. ``name`` is canonical (see…, DomainCreate, Payload for ``POST /domains``. ``name`` is passed through the canonicaliser; it… (+62 more)

### Community 91 - "dns/__init__.py"
Cohesion: 0.04
Nodes (54): _Ambiguous, CloudflareDnsProvider, BaseException, Exception, Response, Cloudflare: credential verification, and the DNS-01 record operations. The…, A bounded, credential-free description of a failed call., Verify the token and list the zones it can reach. Never raises for a provider-… (+46 more)

### Community 92 - "containers.py"
Cohesion: 0.07
Nodes (61): _action_route(), _endpoint(), _container_out(), _decode_frame(), _ev(), get_container(), _like_pattern(), list_container_logs() (+53 more)

### Community 93 - "certificate_service.py"
Cohesion: 0.08
Nodes (45): apex_of(), The name a wildcard Domain is anchored at (``*.example.com`` →…, CertificateCreate, Payload for ``POST /certificates`` — a *request*, never an issuance.…, enqueue_generation(), Hand one generation to the worker, but only once *db* commits. Inline is a…, _actor(), all_generations() (+37 more)

### Community 94 - "test_phase21_secret_version_integrity.py"
Cohesion: 0.18
Nodes (18): _app_role_dsn(), _owner_dsn(), _probe(), Phase 2.1 — ``secret_versions`` is append-only in the **database**, not just in…, Immutability is a database guarantee, not merely a missing code path. The owner…, The legitimate append paths keep working under the guard., The documented deletion policy: purging a Secret cascades its history., RLS is preserved: another tenant cannot see a version row, even by id. (+10 more)

### Community 95 - "test_dns_propagation.py"
Cohesion: 0.12
Nodes (36): evaluate(), Fold one round of observations into ``(ok, status, detail)``. **Pure.** ``ok``…, Poll the authoritative servers until every value is visible, or the deadline.…, wait_for_txt_records(), _Clock, _ok(), MonkeyPatch, parametrize (+28 more)

### Community 96 - "NexusOps (self-hosted infrastructure management and monitoring platform)"
Cohesion: 0.20
Nodes (10): mailpit service (dev SMTP sink + web UI :8025), NexusOps compose stack (8 services on one network), HIGH finding: redirect-following SSRF in uptime monitors (fixed: follow_redirects=False + per-hop guard), SSRF guard (assert_safe_url, per-redirect-hop validation, assert_safe_tcp_endpoint), Mailpit SMTP port internal-only (host-side injection needs extra mapping), Host port knobs (NEXUSOPS_HTTP_PORT/POSTGRES/REDIS/MAILPIT/VITE), SPA entry point (loads /src/main.tsx, dark color-scheme), Uptime monitors -> incidents -> notifications flow (+2 more)

### Community 97 - "REST API surface (/api/v1)"
Cohesion: 0.29
Nodes (7): Cursor (keyset) and offset pagination envelopes, Permission model (data-driven registry, require_permission, wildcard scopes), REST API surface (/api/v1), RBAC registry (PERMISSIONS + ROLE_MATRIX + scope_matches), Adding a new resource: 7-step checklist (model -> migration -> schemas -> service -> router -> tests -> frontend), Alembic migration workflow (autogenerate, models __init__ export, entrypoint apply), Command palette (Ctrl/Cmd+K)

### Community 98 - "journey.spec.ts"
Cohesion: 0.15
Nodes (15): EDGE, MAILPIT, ADMIN, Bootstrap, bootstrapVia(), test, ADMIN, formLogin() (+7 more)

### Community 99 - "test_org_dek_envelope.py"
Cohesion: 0.08
Nodes (73): install_tenancy_guards(), Attach the guard and the GUC writer to the ORM session class. Idempotent, and…, org_dek(), Fernet, Yield the organization's DEK for **one operation**, then drop it. The key-only…, _run(), db(), A session with **no** tenant scope. Deliberately unscoped: it is how a test… (+65 more)

### Community 100 - "redact_mapping"
Cohesion: 0.09
Nodes (33): _is_sensitive_key(), Return a copy of *data* with sensitive values replaced, at any depth. Two…, Substring match on a normalised key so header-style names are caught too.…, redact_mapping(), parametrize, Unit tests for app.core.logging redaction (pure functions only)., No sensitive key name involved: the PEM armor is the only signal., Lists of dicts holding further lists — the shape an agent report takes. (+25 more)

### Community 101 - "decide"
Cohesion: 0.23
Nodes (18): decide(), matches_token(), Constant-time comparison of the observed TXT values against the token. TXT…, Turn one observation into the verification outcome — pure, no I/O.…, observation(), parametrize, The verification decision: every outcome, without a network. ``decide`` is…, test_a_sweep_invalidates_a_changed_delegation_even_with_the_token() (+10 more)

### Community 102 - "docker_real.py"
Cohesion: 0.08
Nodes (29): ContainerInfo, Exception, Build a compact, secret-free description of a provider failure. Only the…, Normalized view of a container as reported by any provider., sanitize_error(), _as_float(), _compute_stats(), _cpu_percent() (+21 more)

### Community 103 - "list_dns_providers"
Cohesion: 0.13
Nodes (23): create_dns_provider(), delete_dns_provider(), get_dns_provider(), list_dns_providers(), DbDep, Depends, get, ManageCtx (+15 more)

### Community 104 - "_exec"
Cohesion: 0.14
Nodes (24): _exec(), Statement, Run statements in one transaction as the owner (committed on success)., _columns(), _integrity_error(), _migrate_from_phase3(), Statement, Phase 4 migration (`f4a5b6c7d8e9`) against a real Phase 3 database. Phase 4 is… (+16 more)

### Community 105 - "redis service (Redis 7, no persistence, loopback :6390)"
Cohesion: 0.22
Nodes (11): redis service (Redis 7, no persistence, loopback :6390), WebSocket API (/api/v1/ws handshake, frames, limits), WebSocket channels (global, server-metrics, container-logs, deployment-logs, incidents), Deployment engine (queue_deployment / execute_deployment / sweeper backstop), Real-time spine: PostgreSQL system_events + Redis pub/sub, Rollback as a new deployment (rollback_of_id), WebSocket hub (framework-thin, Redis fan-in, per-socket queues), Test suites (pytest unit+integration, vitest, Playwright e2e) (+3 more)

### Community 106 - "NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)"
Cohesion: 0.18
Nodes (12): Agent security model (one-way telemetry, no command channel), Agent enrollment token (X-Agent-Token, nxa_..., SHA-256 at rest), Agent heartbeat exponential backoff (cap 5 min, exit 1 on revoked token), agent/install.sh (enrollment installer), Agent metrics collection (/proc statvfs Docker socket), NexusOps agent (stdlib-only Python, agent/nexusops_agent.py), Agent systemd hardening (ProtectSystem=strict, NoNewPrivileges), Agent ingest API (POST /agent/hello, POST /agent/heartbeat) (+4 more)

### Community 107 - "test_migration_phase5.py"
Cohesion: 0.11
Nodes (34): _columns(), _foreign_keys(), _indexes(), _insert_certificate(), _insert_generation(), _integrity_error(), _migrate_from_phase4(), _migrate_to_phase5() (+26 more)

### Community 108 - "test_migration_phase532.py"
Cohesion: 0.16
Nodes (26): _columns(), _insert_certificate(), _insert_generation(), _insert_provider(), _migrate_to_phase53(), _migrate_to_phase532(), Phase 5.3.2 migration (`d0e1f2a3b4c5`): one column, one state, one refusal. The…, The only workflow that existed is the only value the backfill can mean. (+18 more)

### Community 109 - "Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)"
Cohesion: 0.25
Nodes (9): API keys (X-API-Key, nxo_..., scope intersection), First boot sequence (api entrypoint migrates, compose never seeds), Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test), Makefile workflows (up/test/lint/typecheck/migrate/seed), HIGH finding: API-key scope bypass for superadmin-owned keys (fixed: scope intersection first), Security audit 2026-09 (26 raw findings -> 20 confirmed, all fixed), HIGH finding: known seed superadmin + API key backdoor (fixed: NEXUSOPS_ALLOW_SEED opt-in, one-time password), Threat model (edge attacker, malicious agent, curious operator, leaked token, SSRF) (+1 more)

### Community 110 - "organization_service.py"
Cohesion: 0.17
Nodes (24): add_member(), create_organization(), get_organization(), membership_for_user(), AsyncSession, Membership, Organization, Request (+16 more)

### Community 111 - "CheckResult"
Cohesion: 0.22
Nodes (13): CheckResult, HTTPMonitorTransport, Real HTTP(S) probe using httpx with per-monitor settings. Redirects are…, _FakeResponse, MonkeyPatch, A 302 from a public URL into link-local/metadata space must be refused., Defense in depth: even the httpx client must never auto-follow., _script_client() (+5 more)

### Community 112 - "middleware.py"
Cohesion: 0.14
Nodes (15): ASGIApp, AccessLogMiddleware, HTTP middleware: request ids, security headers, structured access logs., Baseline hardening headers on every API response., RequestIDMiddleware, SecurityHeadersMiddleware, create_app(), _include_routers() (+7 more)

### Community 113 - "dnsmock.py"
Cohesion: 0.10
Nodes (32): resolver(), answer(), encode_name(), encode_txt(), forward(), main(), _nameservers(), parse_question() (+24 more)

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 116 - "test_tenancy_allowlist.py"
Cohesion: 0.20
Nodes (14): AST, _actual_callers(), _calls_system_scope(), _module_path(), Path, The system-scope allowlist is the only fence around the tenancy carve-out.…, Every module that could open a system scope: ``app/`` plus the scripts., No module may lift tenant isolation without being named in the list. (+6 more)

### Community 117 - "_alembic_config"
Cohesion: 0.07
Nodes (29): Phase 2.1 corrective migration: legacy ``environment_type`` classification.…, Every case is classified as documented, ids and ownership intact., An explicit non-DEV classification survives the corrective migration. The…, The correction is part of ``head`` and adds no extra Alembic head., Insert one legacy environment per case, in two organizations., _seed_typed_environments(), test_corrective_migration_is_reachable_from_head(), test_corrects_legacy_environment_types() (+21 more)

### Community 118 - "ownership"
Cohesion: 0.12
Nodes (16): _CloudflareCredentials, _compose(), _get_json(), manual_dns(), ownership(), observe(), pebble_stack(), CompletedProcess (+8 more)

### Community 119 - "@tanstack/react-query"
Cohesion: 0.08
Nodes (21): DeploymentStepOut, DeploymentDetailPage, MetaInfo, SimulatedChip(), mocks, ACTIVE_STATUSES, DeploymentDetailRow, DeploymentLogRow (+13 more)

### Community 120 - "generate_secrets.sh"
Cohesion: 0.47
Nodes (3): existing_real_keys(), replace_or_append(), generate_secrets.sh script

### Community 121 - "_invoke_sender"
Cohesion: 0.20
Nodes (14): NotificationError, Any, BaseException, Exception, POST *payload* as JSON to *url*; 2xx is success, anything else raises. Response…, Raised when a delivery attempt fails. Message is safe to persist., Bounded, single-line, content-free error reason., Send a plain-text email via SMTP. Raises :class:`NotificationError`. The… (+6 more)

### Community 122 - "apply_scope_to_session"
Cohesion: 0.03
Nodes (90): get_sessionmaker(), async_sessionmaker, AsyncSession, apply_scope_to_session(), Push the current scope onto *db*'s connection immediately. Needed only when a…, The operator-facing one-liner stored in ``last_error``. Bounded., dispatch_event_frame(), dispatcher_loop() (+82 more)

### Community 123 - "_run_migration"
Cohesion: 0.15
Nodes (20): alembic_config, alembic_script, Phase 2 migration (`b2c3d4e5f6a7`) against realistic legacy data. The promotion…, Upgrade ``database`` to ``revision``., The pre-Phase-2 shapes: application-scoped environments, per-app dupes., A fresh database reaches the same shape the models describe., _run_migration(), _seed_legacy_data() (+12 more)

### Community 124 - "test_dns_providers.py"
Cohesion: 0.10
Nodes (41): _audits(), _create(), _create_domain(), _created(), _events(), _member_with_role(), _org_id(), Any (+33 more)

### Community 125 - "OperationError"
Cohesion: 0.09
Nodes (32): _demux_docker_stream(), _docker_error(), execute_operation(), _insert_http_includes(), _nginx_binary(), _nginx_bootstrap(), _nginx_config_test(), _nginx_status() (+24 more)

### Community 126 - "log_service.py"
Cohesion: 0.15
Nodes (23): container_log_channel(), LogSource, LogLine, One parsed log record from a container log stream., append_lines(), count_container_logs(), detect_level(), _entry_values() (+15 more)

### Community 127 - "20261018_1200-d0e1f2a3b4c5_phase532_manual_dns01.py"
Cohesion: 0.22
Nodes (14): _assert_no_manual_work(), downgrade(), _drop_constraint(), _guard_predicate(), _in_list(), Phase 5.3.2 — manual DNS-01: ``certificates.dns_mode`` and ``AWAITING_MANUAL``.…, Raw ``ALTER TABLE ... DROP CONSTRAINT IF EXISTS`` (see the 5.2.2 migration)., Replace the state CHECK, the guard and the one-live index in one transaction.… (+6 more)

### Community 137 - "DockerHostsPage.test.tsx"
Cohesion: 0.18
Nodes (8): DockerHostOut, ApiError, failingHost, host, hostsPage, mockCountApi(), server, serversPage

### Community 146 - "_Attempt"
Cohesion: 0.06
Nodes (43): AcmeOrder, AcmeSession, A fresh order and its authorizations, as public data., One attempt's conversation with a CA, for one account. Method calls are…, Register (or discover) this account and return its CA-side URL (``kid``)., Create an order for *identifiers* and return its authorizations., Re-open an order this session did not create, by its recorded URL. The manual…, Tell the CA a challenge is ready to be validated. (+35 more)

### Community 147 - "20261009_1000-c3d4e5f6a7b8_enforce_secret_version_integrity.py"
Cohesion: 0.48
Nodes (6): _clear_app_role_guc(), downgrade(), Phase 2.1 — enforce append-only ``secret_versions`` in the database. Phase 2…, Publish the app-role name to the migration GUC the revoke block reads., _set_app_role_in_guc(), upgrade()

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
Cohesion: 0.14
Nodes (14): _listener_ownership(), _listening_ports(), nginx_capability(), _nginx_owned_ports(), _nginx_running(), _nginx_version(), _pid_alive(), ``nginx -v`` prints its version to stderr; bounded and non-shell. (+6 more)

### Community 153 - "types.ts"
Cohesion: 0.02
Nodes (87): AlertOut, CapabilityReport, ChannelOut, CheckOut, DeliveryOut, DeploymentLogLine, DeploymentStatus, DomainDetailOut (+79 more)

### Community 154 - "nexusops-draft.mjs"
Cohesion: 0.40
Nodes (4): DOCS, meta, SPINE, VERIFY_RULES

### Community 155 - "v1/secrets.py"
Cohesion: 0.11
Nodes (34): create_secret(), delete_secret(), get_secret(), list_secret_versions(), list_secrets(), DbSession, get, PageParamsDep (+26 more)

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
Cohesion: 0.09
Nodes (23): computed_field, Derived lifecycle state: revoked wins over used wins over expired., 2.1.1 ApiKey org binding detail, 2.2.1 Environment promotion detail — **shipped in Phase 2**, 2.2 Delivery (existing models, extended), 2.4 Routing & TLS (new subsystem), 2.5 Secrets (re-scoped — **shipped in Phase 2**), 2.6 Observability (existing, org-scoped via parents) (+15 more)

### Community 160 - "test_kek_vault_transit_live.py"
Cohesion: 0.07
Nodes (43): _ca_context(), _configure(), _ctx(), _docker(), _free_port(), LiveVault, CompletedProcess, fixture (+35 more)

### Community 161 - "alert_service.py"
Cohesion: 0.14
Nodes (21): mark_all_read(), mark_read(), CurrentUser, DbDep, get, post, UUID, Mark every unread alert read; returns how many rows changed. (+13 more)

### Community 162 - "_View"
Cohesion: 0.17
Nodes (5): One authoritative server's record store, through its control API., Drop every TXT record this view holds (setup, never an assertion)., The DNS-record seam, backed by the two **real** authoritative servers. It…, _ReplicatedZone, _View

### Community 163 - "routes.py"
Cohesion: 0.19
Nodes (29): bind_route_certificate(), create_route(), delete_route(), disable_route(), _domain_status(), enable_route(), get_route(), list_routes() (+21 more)

### Community 164 - "AgentClient"
Cohesion: 0.15
Nodes (8): AgentClient, _docker_raw(), SSLContext, A verifying TLS context. Verification is never disabled. A private/self-hosted…, Refuse to send credentials over plain HTTP to a non-loopback server. The…, One raw Docker API call; returns ``(status, body_bytes)``., _tls_context(), _UnixHTTPConnection

### Community 165 - "get_settings"
Cohesion: 0.05
Nodes (65): fail_on_bad_config(), get_settings(), Return the cached settings singleton., Exit immediately with a readable message if configuration is invalid. Also…, get_engine(), AsyncEngine, Runtime DSN (application role, RLS enforced) for Celery/script sync paths., sync_database_url() (+57 more)

### Community 166 - "_rows"
Cohesion: 0.31
Nodes (14): _migration_dsn(), _owner_dsn(), _rows(), _clear_bindings(), _column(), _fk(), Phase 5.4.1 migration — the association column, its tenant key, its refusal.…, The composite key's columns and its delete action, straight from the catalog. (+6 more)

### Community 167 - "_FakeCloudflare"
Cohesion: 0.18
Nodes (11): cloudflare(), _dns_stub(), _fake_observe(), _FakeCloudflare, _never_reach_the_network(), fixture, MonkeyPatch, Replace the provider seam for one test, and make it reachable to tune. (+3 more)

### Community 168 - "redact_log_event"
Cohesion: 0.12
Nodes (20): configure_logging(), _orjson_dumps(), Any, structlog processor: scrub one record before anything renders it. The pipeline…, Configure structlog + stdlib logging once at process start. Everything…, Replace every embedded PEM private-key block in *value* with the marker. Only…, Scrub PEM private-key blocks out of one free-text value. The scalar counterpart…, Recursively redact one value of any shape — the depth-agnostic walk. Dicts,… (+12 more)

### Community 169 - "pytest"
Cohesion: 0.16
Nodes (12): created_at server defaults must evaluate per insert, not at table creation., Regression: system_events and audit_logs shipped with DEFAULT 'now()' (quoted…, test_audit_and_event_created_at_defaults_are_dynamic(), UUID, Phase 2.2 — the environment-type correction follows the documented precedence.…, Only the previous migration's ``PROD`` output is corrected. A row already…, Create one legacy (application-scoped) environment per case., Every branch of the slug-first rule, end to end through ``head``. (+4 more)

### Community 170 - "test_agent_contract.py"
Cohesion: 0.18
Nodes (16): agent_fixture(), _load_agent(), _patch_stats(), Any, fixture, MonkeyPatch, Contract tests: the shipped agent's payloads must satisfy the ingest schemas.…, One-shot docker stats reduce to cpu/mem/limit fields the schema accepts, with… (+8 more)

### Community 171 - "test_kek_vault_transit.py"
Cohesion: 0.10
Nodes (48): logs(), _ctx(), _login_ok(), _provider(), parametrize, Request, Response, The Vault Transit adapter's HTTP contract, without a Vault. This module pins… (+40 more)

### Community 172 - "monitor_transport.py"
Cohesion: 0.11
Nodes (18): assert_safe_url_async(), Async wrapper around :func:`assert_safe_url`; DNS runs off the loop., CheckOutcome, coerce_headers(), _decode(), MonitorTransport, Any, BaseException (+10 more)

### Community 173 - "env.py"
Cohesion: 0.24
Nodes (10): _database_url(), Alembic environment: metadata comes from app.models, URL from app settings., Migrations run as the table **owner**, never as the application role. The owner…, Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online(), Owner-role DSN for Alembic and the container entrypoint. Migrations… (+2 more)

### Community 174 - "get_latest_server_metrics"
Cohesion: 0.25
Nodes (11): get_dashboard_summary(), get_latest_server_metrics(), get_server_metrics(), CurrentUser, DbDep, Depends, get, UUID (+3 more)

### Community 175 - "certificate_issuance.py"
Cohesion: 0.06
Nodes (55): _actor(), _aware(), _enqueue_issuance(), _expectations(), _failure_from(), _identifiers(), _leaf_of(), BaseException (+47 more)

### Community 176 - "Platform Security Model — NexusOps"
Cohesion: 0.12
Nodes (16): make(), 10.1 Node revocation playbook (compromised node / leaked agent token), 10.2 Key compromise playbook, 10. Incident response, 1. Scope, stance, and simulation honesty, 2. Assets, 3. Trust boundaries, 4. Tenant isolation model (summary) (+8 more)

### Community 177 - "Node & Agent Architecture"
Cohesion: 0.08
Nodes (26): install_hint(), The one-liner an operator pastes, without the raw token in argv. The token…, 1. Scope and stance, 3.2 Enrollment v2, 3.3 Token storage & rotation with dual-token grace, 3.4 Revocation semantics — fixing the 401 hot-loop, 3.5 Reconnect / offline states, 3. Agent lifecycle (+18 more)

### Community 178 - "v1/auth.py"
Cohesion: 0.08
Nodes (48): change_password(), _clear_refresh_cookie(), _cookies_secure(), login(), logout(), me(), _optional_actor(), AsyncSession (+40 more)

### Community 179 - "test_phase541_route_binding.py"
Cohesion: 0.12
Nodes (44): _dns_stub(), _fake_observe(), fixture, MonkeyPatch, Stand in for authoritative DNS in every test in this module., _bind(), _certificate(), _dns_stub() (+36 more)

### Community 180 - "list_sessions"
Cohesion: 0.28
Nodes (9): list_sessions(), CurrentUser, DbSessionDep, get, Request, UUID, Active sessions of this organization's members. Defaults to the caller's own;…, Revoke a session and its refresh tokens. Own session always; others need… (+1 more)

### Community 181 - "_nginx_apply"
Cohesion: 0.10
Nodes (27): _fsync_dir(), _nginx_apply(), _nginx_failure_summary(), Materialize the bundle under ``staged/<id>/`` and return that directory.…, Build a self-contained config for ``nginx -t`` over the staged tree. The…, Move the staged tree over the live one, keeping the previous as backup., Put the previous known-good tree back. Returns whether it was possible., Reload nginx via ``-s reload``, falling back to a SIGHUP of the master. (+19 more)

### Community 182 - "_run_downgrade"
Cohesion: 0.18
Nodes (17): Move ``database`` *back* to ``revision``. The same code path a deployment uses…, _run_downgrade(), _columns(), Phase 5.2.1 migration (`f5a6b7c8d9e0`): two columns, one invariant, one…, The naming convention must not be applied twice. A fresh database is the only…, A ciphertext behind generation 0, and a generation with no material, both fail., The refusal is the point: a rollback must not delete key material., A populated instance in the schema Phase 5.2.1 is written on top of. (+9 more)

### Community 183 - "events.py"
Cohesion: 0.10
Nodes (26): _decode_cursor(), _encode_cursor(), list_event_types(), list_events(), datetime, DbSession, Depends, get (+18 more)

### Community 184 - "SystemEvent"
Cohesion: 0.16
Nodes (18): NotificationDelivery, SystemEvent, _create_monitor(), Monitor checks driving the full down -> incident -> recovery lifecycle., Regression: probe headers and URL query credentials never leave the API. Probe…, A monitor's checks, incidents and timeline all live in its organization, so the…, test_check_now_endpoint_runs_immediately(), test_down_then_recover_lifecycle() (+10 more)

### Community 185 - "20261012_1200-c8d9e0f1a2b3_phase5_certificate_metadata.py"
Cohesion: 0.23
Nodes (13): downgrade(), _drop_certificate_permissions(), _drop_tenant_policies(), _grant(), _in_list(), Phase 5.1 — certificate metadata and the pre-issuance lifecycle. Adds, in one…, Grant the app role on *table*; the migration role GUC carries the name. The…, The two-policy shape every tenant table uses: tenant + system scope. (+5 more)

### Community 186 - "_guard"
Cohesion: 0.13
Nodes (19): _apply_scope_guc(), _desired_guc(), _guard(), _has_org_predicate(), _mappers_of(), org_scoped_table_names(), Any, The ``app.current_org`` value implied by the current scopes. (+11 more)

### Community 187 - "Phase 5 — HTTPS, Certificates and Private-Key Delivery — Design"
Cohesion: 0.08
Nodes (26): 1.2 Phase 5 in one sentence, 1.3 Trust boundaries Phase 5 adds, 1.4 Non-goals for Phase 5, 1.5 Trust concentration: centralized key custody, accepted **conditionally** (decided), 1. Architecture and trust boundaries, 5.1 Decision: maintained ACME client library (josepy/`acme`), not a hand-rolled RFC 8555 client, 5.2 Challenge: DNS-01 only in v1, 5.3 DNS provider abstraction and the DNS-01 flow (+18 more)

### Community 188 - "Deployment Architecture — NexusOps (target state)"
Cohesion: 0.10
Nodes (20): DeploymentRunner, Protocol, Adapter interface implemented by real (future) and simulated runners., Return the ordered step names for this run., 10. Events and WS during runs, 12. Rollback semantics (existing behavior kept), 13. The simulated runner stays — labeled, 14. Open questions (+12 more)

### Community 189 - "phase3.spec.ts"
Cohesion: 0.15
Nodes (10): frontend_e2e_fixtures_expect, AGENT, NodeDetail, OperationRow, REPO_ROOT, ref_node_child_process, ref_node_fs, ref_node_os (+2 more)

### Community 190 - "Settings"
Cohesion: 0.11
Nodes (9): field_validator, model_validator, Username from :attr:`database_url`, or ``None`` if it is unparseable., Validated application settings (loaded from environment / .env)., Refuse a Vault address that carries userinfo (Phase 5.2.1.2, F4).…, Refuse to start with an ACME directory selection that is unsafe or ambiguous.…, Refuse to start with an unusable or unsafe key source. Two failures are worth…, Settings (+1 more)

### Community 191 - "ChannelCreate"
Cohesion: 0.40
Nodes (3): ChannelCreate, ChannelUpdate, model_validator

### Community 192 - "enqueue.py"
Cohesion: 0.39
Nodes (8): after_commit(), _on_commit(), _on_rollback(), Any, AsyncSession, Deferred Celery handoff: enqueue only after the creating transaction commits. A…, Run ``factory`` once the current transaction commits. ``label`` names the work…, _run()

### Community 193 - "10. Implementation slices, acceptance criteria, tests, limitations"
Cohesion: 0.13
Nodes (14): 10.10 Phase 5.4.1 — certificate-to-route binding foundation (shipped 2026-10-19), 10.2 Test requirements (what "done" means per slice), 10.3.1 Approved decisions (previously open), 10.3.2 Known limitations (accepted, not blockers), 10.3.3 Open items and what they block now, 10.3 Decisions and known limitations, 10.4 Reserved-operation-type lists — one source of truth (required consolidation), 10.5.1 Migration (one, additive, `down_revision = c8d9e0f1a2b3`) (+6 more)

### Community 194 - "ApplicationBase"
Cohesion: 0.40
Nodes (4): ApplicationBase, Any, field_validator, Shared application fields; ``build_config`` is a free-form dict.

### Community 195 - "route_certificate_service.py"
Cohesion: 0.10
Nodes (36): _actor(), bind_certificate(), BindingEvaluation, BindingState, bound_route_count(), certificate_covers_hostname(), certificate_identifiers(), evaluate() (+28 more)

### Community 196 - "v1/certificates.py"
Cohesion: 0.08
Nodes (56): _at(), confirm_manual_challenge(), create_certificate(), delete_certificate(), _detail(), get_certificate(), get_manual_challenge(), list_certificates() (+48 more)

### Community 197 - "entries"
Cohesion: 0.12
Nodes (43): AcmeChallenge, One ``dns-01`` challenge, resolved to what has to be published. Every field is…, challenge_ref(), cleanup_incomplete(), entries(), Every challenge entry in *document*, in order, shape-checked. A challenge URL…, Record the order this attempt is working on. Called before any challenge. Once…, Append one entry per challenge, preserving any already recorded. Keyed by… (+35 more)

### Community 198 - "20261014_1200-a7b8c9d0e1f2_isolate_org_dek_envelopes.py"
Cohesion: 0.23
Nodes (11): downgrade(), _drop_constraint(), _drop_tenant_policies(), _grant(), Phase 5.2.1.2 — the organization DEK envelope gets a tenant table of its own.…, Grant the app role the four DML verbs on *table*. Not ownership, and not…, Restore the envelope onto ``organizations`` — without losing any of it., Raw ``ALTER TABLE ... DROP CONSTRAINT``, as the tenancy migration does.… (+3 more)

### Community 199 - "20261010_1200-f4a5b6c7d8e9_phase4_domains_and_routes.py"
Cohesion: 0.31
Nodes (9): downgrade(), _drop_tenant_policies(), _grant(), _in_list(), Phase 4 — domains, routes and the routing schema. Adds, in one migration with a…, Grant the app role on *table*; the migration role GUC carries the name. The…, The two-policy shape every tenant table uses: tenant + system scope., _tenant_policies() (+1 more)

### Community 200 - "certificate_order.py"
Cohesion: 0.07
Nodes (66): attempt_in_flight(), attempt_unfinished(), begin_attempt(), challenge(), cleanup_instructions(), confirm_published(), current_entries(), finish_attempt() (+58 more)

### Community 201 - "v1/health.py"
Cohesion: 0.20
Nodes (13): liveness(), get, Response, Health probes: liveness (always cheap) and readiness (checks dependencies).…, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness(), HealthOut (+5 more)

### Community 202 - "SimulatedDeploymentRunner"
Cohesion: 0.11
Nodes (41): LogLevel, _commit_short(), _pace(), Exception, Deployment runner port plus a faithful simulated implementation.…, Stream output lines for *step_name*; raise StepFailure to fail it., Staged docker-style simulation used by v1 deployments., Deterministic per-line delay between 0.05s and 0.35s. (+33 more)

### Community 203 - "Domain Model — NexusOps as a Multi-Tenant Platform"
Cohesion: 0.25
Nodes (8): org_id_column(), A plain ``org_id`` column for the few tables that carry one without taking part…, 0.1 Shipped tenant layer (Phase 1), 0. Design stance, 1.1 ER diagram, 1. The hierarchy, 3. Cross-cutting decisions, Domain Model — NexusOps as a Multi-Tenant Platform

### Community 204 - "_LibrarySession"
Cohesion: 0.05
Nodes (48): AuthorizationResource, The directory URL stored on the account row and recorded per issuance., AcmeProtocolError, The response was not a well-formed ACME answer. A missing ``Location`` on an…, _execute(), _finalize_deadline(), _first_error(), _LibrarySession (+40 more)

### Community 205 - "_credential_seam"
Cohesion: 0.29
Nodes (7): _credential_seam(), _dns_stub(), _fake_observe(), _FakeCloudflare, fixture, MonkeyPatch, The credential side of the DNS seam, for creating a provider through the API.

### Community 206 - "test_agent_ingestion.py"
Cohesion: 0.30
Nodes (10): _enrolled(), _heartbeat(), Agent ingest pipeline: hello, heartbeat, staleness transitions, events., A container absent from a later heartbeat is gone from the daemon., A payload at the agent's cap may be truncated — absence proves nothing., test_heartbeat_at_container_cap_skips_reconciliation(), test_heartbeat_removes_vanished_containers(), test_heartbeat_updates_status_metrics_and_containers() (+2 more)

### Community 207 - "VaultTransitKEKProvider"
Cohesion: 0.05
Nodes (40): AsyncBaseTransport, _construct(), Provider construction — the only place a ``KEKProvider`` is ever created. One…, Provider health, cached, for the readiness surface. Health is the one place a…, KEKConfigurationError, KEKError, KEKUnauthorizedError, KEKUnavailableError (+32 more)

### Community 208 - "20261019_1000-e1f2a3b4c5d6_phase541_route_certificate_binding.py"
Cohesion: 0.33
Nodes (5): _assert_no_bindings(), downgrade(), Phase 5.4.1 — certificate-to-route binding foundation. One nullable column, one…, Refuse a downgrade that would drop live associations., Remove the association — refusing while any route still holds one.

### Community 209 - "20261008_1200-b2c3d4e5f6a7_add_projects_and_environments.py"
Cohesion: 0.53
Nodes (5): downgrade(), _drop_constraint(), _quoted_list(), Phase 2 — projects & environments: env promotion, config, secret versions. This…, upgrade()

### Community 210 - "NotificationChannel"
Cohesion: 0.21
Nodes (20): ChannelType, NotificationChannel, A delivery target (email address / webhook endpoint). ``config_ciphertext``…, _audit(), create_channel(), decrypt_channel_config(), delete_channel(), encrypt_config() (+12 more)

### Community 211 - "20261014_1600-b8c9d0e1f2a3_phase522_providers_acme_material.py"
Cohesion: 0.21
Nodes (14): _assert_no_material(), downgrade(), _drop_constraint(), _drop_tenant_policies(), _grant(), _in_list(), Phase 5.2.2 — DNS credentials, ACME accounts, and the certificate material…, Raw ``ALTER TABLE ... DROP CONSTRAINT IF EXISTS``. ``op.drop_constraint`` is… (+6 more)

### Community 212 - "6. Private-key encryption and key management"
Cohesion: 0.29
Nodes (7): 6.1 Threat model — what each envelope actually protects against, 6.2 Recommended v1 design, 6.3 Rotation, 6.5 Backups, recovery, and consequences of key loss, 6.6 Production-readiness requirements for centralized custody (conditions of §1.5), 6.8 Decisions closed here, and what remains an operator choice, 6. Private-key encryption and key management

### Community 213 - "_FakeAsyncClient"
Cohesion: 0.22
Nodes (3): _FakeAsyncClient, _FakeRequestObj, Scripted httpx.AsyncClient: responses keyed by absolute request URL.

### Community 214 - "20261009_1100-d4e5f6a7b8c9_correct_legacy_environment_types.py"
Cohesion: 0.33
Nodes (3): downgrade(), Phase 2.1 — correct legacy ``environment_type`` classification. The Phase 2…, No-op: the correction is a best-effort classification, not reversible.…

### Community 215 - "20261004_1200-e7c4a2b9d1f3_add_operations_framework.py"
Cohesion: 0.50
Nodes (3): _quoted_list(), Add the operations framework table (node-agent-architecture.md §5). One tenant-…, upgrade()

### Community 216 - "README.md - NexusOps overview"
Cohesion: 0.37
Nodes (12): docker-compose.dev.yml - dev overlay, docker-compose.docker-sock.yml - docker socket override, docker-compose.yml - full stack definition, docs/agent.md - agent guide, docs/api.md - API guide, docs/architecture.md - system architecture, docs/deployment.md - deployment and operations guide, docs/development.md - developer guide (+4 more)

### Community 217 - "api_key_service.py"
Cohesion: 0.09
Nodes (33): create_api_key(), list_api_keys(), CurrentUser, DbSessionDep, get, post, Request, UUID (+25 more)

### Community 219 - "update_organization"
Cohesion: 0.16
Nodes (14): create_organization(), list_my_organizations(), CurrentUser, DbSessionDep, get, IdentityUser, patch, post (+6 more)

### Community 220 - "Platform Vision — NexusOps"
Cohesion: 0.20
Nodes (10): 1. Where NexusOps is today, 2.1 What we are NOT building, 2.2 The wedge (differentiation), 2. The direction, 3. Guiding principles, 4. Customer journey (target), 5.1 Architecture overview (target), 5. Control plane / data plane boundary (+2 more)

### Community 221 - "stable_json"
Cohesion: 0.67
Nodes (3): Any, Canonical JSON for fingerprint-adjacent comparisons in tests., stable_json()

### Community 222 - "20260923_1000-c4e2a1f7b9d3_rename_server_codenames_to_node.py"
Cohesion: 0.60
Nodes (4): downgrade(), rename ``server.*`` permission codenames to ``node.*`` The Node/Server…, _rename_permissions(), upgrade()

### Community 223 - "sweep_deployments"
Cohesion: 0.67
Nodes (3): task, Re-enqueue deployments the broker lost; fail ones whose worker died.…, sweep_deployments()

### Community 224 - "notification_service.py"
Cohesion: 0.22
Nodes (18): DeliveryStatus, _as_uuid(), _attempt_delivery(), decode_delivery_cursor(), _send(), encode_delivery_cursor(), list_deliveries(), _now() (+10 more)

### Community 225 - "ControlHandler"
Cohesion: 0.20
Nodes (8): BaseHTTPRequestHandler, clear_record(), ControlHandler, in_zone(), Remove the whole name, one record type, or **one value** of a type. The value-…, The journey's only way to publish a record — no shell, no shared volume., set_record(), snapshot()

### Community 226 - "20261012_1600-f5a6b7c8d9e0_phase5_org_dek_envelope.py"
Cohesion: 0.40
Nodes (3): downgrade(), Phase 5.2.1 — the organization DEK envelope. Two additive columns on…, Drop the envelope columns — unless doing so would destroy key material.

### Community 227 - "_bootstrap_resolver"
Cohesion: 0.67
Nodes (3): _bootstrap_resolver(), The deployment's resolver view: this zone's delegation, not the host's. In a…, Resolver

### Community 228 - "role_service.py"
Cohesion: 0.07
Nodes (52): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, get, patch (+44 more)

### Community 230 - "errors.py"
Cohesion: 0.11
Nodes (16): _error_payload(), FastAPI, Request, Error taxonomy and the single place where API error envelopes are shaped. Every…, register_exception_handlers(), handle_app_error(), handle_http_exception(), handle_unexpected() (+8 more)

### Community 232 - "enums.py"
Cohesion: 0.10
Nodes (30): alembic_autogenerate, alembic_migration, directory_known_predicate(), known_directory_urls(), Certificates and their generations — the Phase 5 metadata foundation. Two…, Every ACME directory URL a generation may record, from the vocabulary. Read…, ``directory_url`` is NULL or names a directory in the vocabulary. The ``NULL``…, CertificateChallengeType (+22 more)

### Community 233 - "servers.py"
Cohesion: 0.07
Nodes (63): apply_node_proxy_config(), create_enrollment_token(), create_server(), delete_server(), _detail(), _enrollment_created(), _enrollment_out(), get_server() (+55 more)

### Community 236 - "v1/agent.py"
Cohesion: 0.06
Nodes (49): agent_enroll(), agent_hello(), claim_operation(), _presented_token(), DbDep, post, Request, UUID (+41 more)

### Community 237 - "projects.py"
Cohesion: 0.12
Nodes (46): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+38 more)

### Community 238 - "AuditLogPage.test.tsx"
Cohesion: 0.20
Nodes (5): AuditEntry, AuditLogPage(), formatTimestamp(), shortId(), mockedGet

### Community 239 - "client_ip"
Cohesion: 0.31
Nodes (9): client_ip(), _enforce(), node_rate_limit(), _dependency(), Request, _dependency(), Return a dependency keyed on the **authenticated node**, not the IP. A fleet…, Best-effort client IP; honours X-Forwarded-For from trusted proxies. Delegates… (+1 more)

### Community 241 - "instant_pacing"
Cohesion: 0.40
Nodes (4): instant_pacing(), fixture, MonkeyPatch, Remove the per-line sleeps; pacing bounds are asserted separately.

### Community 244 - "test_app_gating.py"
Cohesion: 0.44
Nodes (8): _app_for_environment(), MonkeyPatch, ENVIRONMENT gating contract: docs exposure and HSTS (see .env.example).…, create_app() with get_settings() patched to the given environment., test_non_production_does_not_emit_hsts(), test_non_production_keeps_docs_and_schema(), test_production_emits_hsts(), test_production_hides_docs_and_schema()

### Community 247 - ".__init__"
Cohesion: 0.12
Nodes (8): _BarrierRewrapProvider, _FailingRewrapProvider, _OverlappingProvider, Fails *only* ``rewrap_dek`` — a rotation that cannot reach its provider. The…, The deterministic provider with a real await point inside ``wrap_dek``. Without…, Two rewrap attempts overlap, deterministically. ``rewrap_dek`` is called…, Holds one rewrap result open until the test releases it. The result is computed…, _StaleSnapshotProvider

### Community 250 - "20260922_1000-a3f1c8d24b6e_add_tenancy_foundation.py"
Cohesion: 0.20
Nodes (12): _app_role_credentials(), _assert_fully_backfilled(), _backfill_org_ids(), _drop_constraint(), add tenancy foundation Phase 1 of the platform roadmap: organizations,…, Carry a value into a PL/pgSQL block. ``CREATE ROLE``/``ALTER ROLE`` are utility…, Application role name/password from settings (never hard-coded)., Point every pre-existing row at the bootstrap organization. ``audit_logs`` is… (+4 more)

### Community 252 - "get_meta"
Cohesion: 0.40
Nodes (5): get_meta(), DbSessionDep, get, Public metadata; identity fields appear only for valid credentials., OptionalUser

### Community 254 - "ContainerListPage.test.tsx"
Cohesion: 0.29
Nodes (3): ApiError, server, serversPage

### Community 255 - "20261009_1300-a1b2c3d4e5f6_add_phase3_nodes_and_agent_v2.py"
Cohesion: 0.40
Nodes (4): _grant(), Phase 3 — Nodes & Agent v2 schema. Adds, in one migration with a single head: *…, Grant the app role on *table*; the migration role GUC carries the name. The…, upgrade()

### Community 256 - ".dispatch"
Cohesion: 0.60
Nodes (3): Request, Response, RequestResponseEndpoint

### Community 258 - "dependencies"
Cohesion: 0.33
Nodes (6): dependencies, lucide-react, react, react-dom, react-router-dom, @tanstack/react-query

### Community 259 - "LoginPage.tsx"
Cohesion: 0.33
Nodes (4): LoginPage, FieldErrors, MetaInfo, redirectTarget()

### Community 260 - "_live_bundle_id"
Cohesion: 0.20
Nodes (10): _allowed_bundle_path(), _live_bundle_id(), _live_files(), The bundle fingerprint — byte-identical to the control plane's algorithm.…, Read the live managed tree, or ``None`` when it does not exist yet., Fingerprint of the configuration tree currently on disk., Independently validate a bundle. Anything unexpected is refused., _template_version_of() (+2 more)

### Community 261 - "20261009_1200-e5f6a7b8c9d0_fix_environment_type_precedence.py"
Cohesion: 0.40
Nodes (3): downgrade(), Phase 2.2 — make legacy environment typing match the documented precedence. The…, No-op: the correction is a classification, not a reversible structure.…

### Community 264 - "20261016_1000-c9d0e1f2a3b4_phase53_generation_directory.py"
Cohesion: 0.28
Nodes (7): _assert_no_directory_recorded(), downgrade(), _drop_constraint(), Phase 5.3 — the issuance provenance pair on ``certificate_generations``. Adds,…, Remove the provenance pair — refusing while any generation records a directory., Raw ``ALTER TABLE ... DROP CONSTRAINT IF EXISTS`` (see the 5.2.2 migration)., Refuse a downgrade that would discard which CA a generation was ordered at.

### Community 269 - "router.py"
Cohesion: 0.40
Nodes (4): websocket, WebSocket endpoint. Mounted by the app factory under ``/api/v1``., Hand the socket to the hub (auth handshake handled there)., websocket_endpoint()

## Knowledge Gaps
- **486 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+481 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 3201 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `6. Tooling: reproducible e2e` connect `logging.py` to `auth_service.py`, `client.ts`, `NotFound`, `dek_envelope.py`?**
  _High betweenness centrality (0.190) - this node is a cross-community bridge._
- **Why does `useEventStream()` connect `client.ts` to `apiGet`, `logging.py`, `App.tsx`, `AuthContext.tsx`, `ServerDetailPage.tsx`, `@tanstack/react-query`?**
  _High betweenness centrality (0.190) - this node is a cross-community bridge._
- **Why does `TenancyScopeError` connect `dek_envelope.py` to `assert_error_code`, `publish`, `test_org_dek_envelope.py`, `models/__init__.py`, `logging.py`, `apply_scope_to_session`, `test_operations.py`, `AuthContext`, `test_acme_accounts.py`, `enrollment_service.py`, `_guard`, `log_service.py`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Are the 111 inferred relationships involving `AuthContext` (e.g. with `TenancyScopeError` and `MembershipStatus`) actually correct?**
  _`AuthContext` has 111 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `APIModel` (e.g. with `OperationSpec` and `test_specs_reject_unknown_params()`) actually correct?**
  _`APIModel` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `meta`, `SCHEMA`, `RESEARCH_COMMON` to the rest of the system?**
  _486 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `apiGet` be split into smaller, more focused modules?**
  _Cohesion score 0.057002457002457 - nodes in this community are weakly interconnected._