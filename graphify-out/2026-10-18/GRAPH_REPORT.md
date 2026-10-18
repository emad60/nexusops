# Graph Report - nexusops  (2026-10-18)

## Corpus Check
- 407 files · ~509,064 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: (none) 10, .example 1, .service 1)

## Summary
- 7685 nodes · 22605 edges · 286 communities (260 shown, 26 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1862 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b37ef716`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- apiGet
- test_certificates.py
- ApiKeysPage.tsx
- test_phase4_routing.py
- docker_host_service.py
- package.json
- resolve_client_ip
- OperationType
- App.tsx
- test_agent_v2.py
- assert_error_code
- ServerDetailPage.tsx
- APIModel
- client.ts
- validate_config
- v1/certificates.py
- deployment_engine.py
- SimulatedDockerProvider
- enrollment_service.py
- secret_service.py
- test_deployments_simulated.py
- PageParams
- metrics_service.py
- test_security.py
- Domain Routing — NexusOps
- monitor_service.py
- Product Roadmap — NexusOps Multi-Tenant Platform
- test_agent_backoff.py
- SimulatedDeploymentRunner
- nexusops_agent.py
- integration/conftest.py
- auth_service.py
- AcmeDirectory
- test_rate_limit.py
- docker_hosts.py
- integration/test_certificate_issuance.py
- NginxBundle
- v1/search.py
- models/__init__.py
- test_channel
- DockerProvider
- test_monitor_transport.py
- test_migration_phase5212.py
- AuthContext.tsx
- project_service.py
- test_permissions.py
- test_kek_health_api.py
- test_phase3_nodes.py
- UnprocessableEntity
- test_ws_hub.py
- roles.py
- DbDep
- proxy_service.py
- WrappedKey
- update_organization
- test_agent_nginx_contract.py
- create_user
- alembic
- notification_service.py
- helpers.py
- compilerOptions
- _list_deployments
- test_error_logging.py
- dns_verifier.py
- test_phase2_environments.py
- AuthContext
- test_schema_redaction.py
- publish
- Certificate Management — NexusOps
- seed.py
- core/tenancy.py
- test_secrets.py
- test_nginx_renderer.py
- domain_service.py
- api service (FastAPI / uvicorn :8000)
- monitors.py
- enums.py
- test_acme_accounts.py
- StrEnum
- test_phase2_secrets.py
- RolesPage.tsx
- test_schemas_server.py
- InvalidName
- tests/conftest.py
- server_service.py
- user_service.py
- devDependencies
- NotFound
- test_certificate_lifecycle.py
- test_payload_crypto.py
- domain_routing.py
- dns_provider_service.py
- alerts.py
- ScopedSession
- test_phase21_secret_version_integrity.py
- AsyncSession
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- journey.spec.ts
- test_org_dek_envelope.py
- redact_mapping
- DeterministicKEKProvider
- library.py
- Path
- _exec
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- test_migration_phase5.py
- docker_real.py
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- routes.py
- run_async
- middleware.py
- dnsmock.py
- scripts
- v1/auth.py
- test_tenancy_allowlist.py
- _alembic_config
- dependencies
- @tanstack/react-query
- generate_secrets.sh
- ControlHandler
- test_tenant_isolation.py
- _run_migration
- test_dns_providers.py
- OperationError
- list_operations
- list_dns_providers
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
- get_settings
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
- decide
- RateLimit
- AgentClient
- test_kek_selection.py
- nginx.py
- resolve_auth
- unit/test_certificate_issuance.py
- pytest
- test_agent_contract.py
- test_kek_vault_transit.py
- CheckOutcome
- .register_container
- ._check_status
- v1/health.py
- Platform Security Model — NexusOps
- Node & Agent Architecture
- main
- _dns_stub
- ServerOut
- _nginx_apply
- _rows
- list_events
- encrypt_str
- 20261012_1200-c8d9e0f1a2b3_phase5_certificate_metadata.py
- apply_scope_to_session
- test_schemas_search.py
- Deployment Architecture — NexusOps (target state)
- phase3.spec.ts
- Settings
- dns/__init__.py
- env.py
- 10. Implementation slices, acceptance criteria, tests, limitations
- config.py
- dek_envelope.py
- certificate_service.py
- test_certificate_order.py
- 20261014_1200-a7b8c9d0e1f2_isolate_org_dek_envelopes.py
- 20261010_1200-f4a5b6c7d8e9_phase4_domains_and_routes.py
- certificate_order.py
- NotificationChannel
- StepLine
- ProxyProvider
- _LibrarySession
- incidents.py
- test_agent_ingestion.py
- .dispatch
- Hub
- notification_sender.py
- certificate_issuance.py
- 20261014_1600-b8c9d0e1f2a3_phase522_providers_acme_material.py
- SystemEvent
- _FakeAsyncClient
- ChannelType
- test_migration_drift.py
- README.md - NexusOps overview
- create_api_key
- test_dns_propagation.py
- Append-only audit log (Postgres BEFORE UPDATE OR DELETE trigger)
- Platform Vision — NexusOps
- list_domains
- CloudflareDnsProvider
- CertificateGenerationState
- next_attempt_at
- acme_account_service.py
- NexusOps — Phase 1 (Multi-Tenancy) Report
- cloudflare
- record
- _validate_bundle
- 2. Entities
- register_exception_handlers
- .__init__
- servers.py
- hub.py
- AcmeSession
- agent_heartbeat
- projects.py
- RealDockerProvider
- AcmeOrder
- CredentialCheck
- instant_pacing
- .__tablename__
- ._shallow_validate
- .apply_params
- DnsCredentialUnavailable
- _nginx_bootstrap
- .__init__
- TxtObservation
- EnvironmentUpdate
- 20260922_1000-a3f1c8d24b6e_add_tenancy_foundation.py
- require_server
- test_event_registry.py
- update_server
- list_sessions
- ContainerStats
- dispatch_event_frame
- search
- AuthorizationState
- PayloadContext
- tasks/certificates.py
- test_migration_phase21.py
- test_monitors_incidents.py
- AuditLogPage.test.tsx
- 20261016_1000-c9d0e1f2a3b4_phase53_generation_directory.py
- ContainerInfo
- scope_matches
- Domain Model — NexusOps as a Multi-Tenant Platform
- Authorization Architecture
- 6. Private-key encryption and key management
- list_audit_logs
- permissions.py
- TxtExpectation
- test_run_async_publishes_frames_scheduled_by_the_commit_hook
- ContainerListPage.test.tsx
- strip_query
- LoginPage.tsx
- _is_same_origin
- router.py
- _FakeCtx
- .route_file_path
- PropagationResult
- test_remove_honours_force_and_never_shells
- stable_json
- .register_log_rows
- ApplicationCreate

## God Nodes (most connected - your core abstractions)
1. `AuthContext` - 175 edges
2. `APIModel` - 151 edges
3. `get_settings()` - 110 edges
4. `record()` - 100 edges
5. `Server` - 93 edges
6. `apiGet()` - 91 edges
7. `NotFound` - 90 edges
8. `Conflict` - 84 edges
9. `publish()` - 82 edges
10. `assert_error_code()` - 77 edges

## Surprising Connections (you probably didn't know these)
- `0. What shipped (Phase 1)` --references--> `resolve_auth()`  [INFERRED]
  docs/authorization.md → backend/app/api/deps.py
- `6. Enforcement mechanics (unchanged patterns, one addition)` --references--> `resolve_auth()`  [INFERRED]
  docs/authorization.md → backend/app/api/deps.py
- `3. Cross-cutting decisions` --references--> `require_permission()`  [INFERRED]
  docs/domain-model.md → backend/app/api/deps.py
- `10. Phase 7 — Teams, grants & custom roles — **proposal, not implemented**` --references--> `require_permission()`  [INFERRED]
  docs/product-roadmap.md → backend/app/api/deps.py
- `7. The IDOR suite` --references--> `_search_users()`  [INFERRED]
  docs/multi-tenancy.md → backend/app/api/v1/search.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three authentication credential families with centralized permission checks** — docs_api_md_auth, docs_api_md_refresh_rotation, docs_api_md_api_keys, docs_agent_md_enrollment_token, docs_api_md_permission_model [EXTRACTED 1.00]
- **NexusOps compose stack services** — docker_compose_yml_nexusops_stack, docker_compose_yml_postgres_service, docker_compose_yml_redis_service, docker_compose_yml_mailpit_service, docker_compose_yml_api_service, docker_compose_yml_worker_service, docker_compose_yml_scheduler_service, docker_compose_yml_frontend_service, docker_compose_yml_nginx_service [EXTRACTED 1.00]
- **WebSocket real-time fan-out spine** — docs_architecture_md_websocket_hub, docs_api_md_websocket_channels, docker_compose_yml_redis_service, docs_architecture_md_event_bus, readme_react_spa [INFERRED 0.85]

## Communities (286 total, 26 thin omitted)

### Community 0 - "apiGet"
Cohesion: 0.06
Nodes (90): apiDelete(), apiGet(), apiPatch(), apiPost(), ApplicationOut, ENVIRONMENT_TYPE_LABELS, EnvironmentType, IncidentEventOut (+82 more)

### Community 1 - "test_certificates.py"
Cohesion: 0.07
Nodes (59): error_of(), Unwrap an API error envelope., _app_role_dsn(), _audits(), _certificate_rows(), _create_domain(), _created_certificate(), _dns_stub() (+51 more)

### Community 2 - "ApiKeysPage.tsx"
Cohesion: 0.09
Nodes (19): ApiKeyOut, ApiKeysPage, ApiKeyCreatedOut, handleCopyKey(), copyText(), describeError(), EMPTY_FORM, GROUP_STYLE (+11 more)

### Community 3 - "test_phase4_routing.py"
Cohesion: 0.04
Nodes (147): DomainStatus, MonitorTargetType, Ownership-verification lifecycle of a Domain (domain-routing.md §4). ``STALE``…, What a monitor observes (domain-model.md §2.6, polymorphic targets). ``URL`` is…, Keep every routed node's live configuration matching the desired bundle. One…, sweep_routes(), _agent_result_body(), _audits() (+139 more)

### Community 4 - "docker_host_service.py"
Cohesion: 0.07
Nodes (77): BadRequest, AuditResult, ContainerHealth, ContainerStatus, DockerHostStatus, Container, DockerHost, Observed container state mirrored from an agent or docker provider. (+69 more)

### Community 5 - "package.json"
Cohesion: 0.13
Nodes (15): name, private, type, version, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom (+7 more)

### Community 6 - "resolve_client_ip"
Cohesion: 0.17
Nodes (22): _is_trusted(), _parse_networks(), Request, Client-IP resolution behind chained reverse proxies. The API never takes TCP…, Parse a comma-separated CIDR list; malformed entries are skipped., Real client address for *request* per the trust model above., resolve_client_ip(), make_request() (+14 more)

### Community 7 - "OperationType"
Cohesion: 0.12
Nodes (20): OperationType, The whitelist. Nothing outside this enum ships as an exec surface. Each type…, Any, Validate *params* against the type's model and return the stored form.…, validate_params(), MonkeyPatch, The operation dispatch whitelist is a contract, not a convention.…, A type whose capability cannot be confirmed must not be dispatchable. (+12 more)

### Community 8 - "App.tsx"
Cohesion: 0.04
Nodes (103): DeploymentOut, Page, ProjectOut, AlertsPage, App(), AuditLogPage, ContainerListPage, DeploymentListPage (+95 more)

### Community 9 - "test_agent_v2.py"
Cohesion: 0.09
Nodes (33): agent_fixture(), _load_agent(), Any, fixture, parametrize, Agent protocol v2: honest metrics, capability detection, and the executor. The…, Phase 4 shipped three nginx ops — no file primitive, no command primitive., Trusting a private CA must not weaken verification. (+25 more)

### Community 10 - "assert_error_code"
Cohesion: 0.07
Nodes (57): expire_operations(), Expire node operations past their deadline — pending and claimed alike. A…, assert_error_code(), Assert envelope shape + code; returns the inner error object., _dispatch(), _dispatch_body(), _enrolled_node(), _mutate_in_system_scope() (+49 more)

### Community 11 - "ServerDetailPage.tsx"
Cohesion: 0.06
Nodes (42): ContainerOut, MetricPoint, ServerDetail, ServerSummary, ChartSeries, LineChart(), LineChartProps, PAD (+34 more)

### Community 12 - "APIModel"
Cohesion: 0.02
Nodes (144): AgentContainerPortIn, AgentEnrollIn, AgentEnrollOut, AgentHeartbeatOut, AgentHelloOut, AgentTokenRotation, Agent-facing schemas. Payloads are data only — never executed. Wire protocol v2…, Tells the agent how often to report and what protocol it negotiated. (+136 more)

### Community 13 - "client.ts"
Cohesion: 0.05
Nodes (54): API_BASE, ApiError, apiRequest(), buildUrl(), extractError(), getAccessToken(), getActiveOrgId(), onActiveOrgChange() (+46 more)

### Community 14 - "validate_config"
Cohesion: 0.08
Nodes (30): field_validator, collect_secret_refs(), walk(), ConfigValidationError, effective_config(), merge_config(), Any, ValueError (+22 more)

### Community 15 - "v1/certificates.py"
Cohesion: 0.09
Nodes (42): create_certificate(), delete_certificate(), _detail(), get_certificate(), list_certificates(), alias, AsyncSession, DbDep (+34 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.11
Nodes (57): deployment_log_channel(), Deployment, DeploymentStep, AlertSeverity, DeploymentStatus, StepStatus, _after_commit_enqueue(), _after_rollback_drop() (+49 more)

### Community 17 - "SimulatedDockerProvider"
Cohesion: 0.13
Nodes (23): Implements :class:`DockerProvider` semantics against DB rows., SimulatedDockerProvider, _log_entry(), datetime, Unit tests for the simulated docker provider (in-memory rows, no docker)., _row(), test_different_seeds_produce_different_fleets(), test_image_listing_shape_and_bounds() (+15 more)

### Community 18 - "enrollment_service.py"
Cohesion: 0.12
Nodes (29): generate_enrollment_token(), An enrollment credential (``nxk_``): single-use, short-lived, org-scoped.…, Return the active org id or raise; used by services that need it explicitly., require_org(), EnrollmentToken, One single-use credential that enrolls (or claims) exactly one node., Whether the row could still be redeemed (not a race-safe check)., _claim_and_consume() (+21 more)

### Community 19 - "secret_service.py"
Cohesion: 0.11
Nodes (40): digest_of(), Short server-verifiable digest used for change detection display. HMAC-SHA256…, An encrypted configuration value, scoped to org, project or environment.…, Secret, _actor_type(), _collect_refs(), create_secret(), delete_secret() (+32 more)

### Community 20 - "test_deployments_simulated.py"
Cohesion: 0.15
Nodes (28): execute_deployment(), Run one deployment to a terminal state. Never raises; safe to re-run., get_environment(), _as_worker(), _delivery_chain(), _owner_ctx(), _queue(), _queued_with_recorder() (+20 more)

### Community 21 - "PageParams"
Cohesion: 0.04
Nodes (121): get_channel(), list_channels(), list_deliveries(), DbDep, Depends, get, ReadCtx, UUID (+113 more)

### Community 22 - "metrics_service.py"
Cohesion: 0.09
Nodes (41): get_dashboard_summary(), get_latest_server_metrics(), get_server_metrics(), CurrentUser, DbDep, Depends, get, UUID (+33 more)

### Community 23 - "test_security.py"
Cohesion: 0.09
Nodes (46): argon2, argon2_exceptions, Unauthorized, create_access_token(), decode_access_token(), _fernet(), generate_agent_token(), generate_api_key() (+38 more)

### Community 24 - "Domain Routing — NexusOps"
Cohesion: 0.07
Nodes (30): The directory URL stored on the account row and recorded per issuance., 10. Wildcards and catch-all, 11. User journey, 12. API surface, permissions, audit, 13. Monitoring tie-in, 2. Where nginx runs, 3.1 Domain, 3.2 Route (+22 more)

### Community 25 - "monitor_service.py"
Cohesion: 0.16
Nodes (36): MonitorStatus, Monitor, One probe. Targets are polymorphic since Phase 4 (domain-model.md §2.6).…, _active_incident(), _audit(), claim_due_monitors(), create_monitor(), delete_monitor() (+28 more)

### Community 26 - "Product Roadmap — NexusOps Multi-Tenant Platform"
Cohesion: 0.12
Nodes (17): What one reported result did to its operation row. The caller's side effects —…, ResultTransition, 0. Stance, 10. Phase 7 — Teams, grants & custom roles — **proposal, not implemented**, 11. Phase 8 — Backups — **proposal, not implemented**, 12. Phase 9 — Billing & metering — **proposal, not implemented**, 13.1 Scope-creep gates — what must be true before each expansion, 13. First commercially meaningful version (+9 more)

### Community 27 - "test_agent_backoff.py"
Cohesion: 0.15
Nodes (21): agent_fixture(), _install_sleep(), fake_sleep(), _load_agent(), _patch_host(), Any, fixture, MonkeyPatch (+13 more)

### Community 28 - "SimulatedDeploymentRunner"
Cohesion: 0.21
Nodes (27): Exception, Staged docker-style simulation used by v1 deployments., Canonical step identifiers stored on :class:`DeploymentStep` rows., Raised by a runner when a step fails irrecoverably., SimulatedDeploymentRunner, StepFailure, StepName, _collect() (+19 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.09
Nodes (30): build_capabilities(), build_heartbeat(), collect_container_stats(), collect_containers(), _container_ports(), _container_status(), cpu_percent_since(), disk_stats() (+22 more)

### Community 30 - "integration/conftest.py"
Cohesion: 0.07
Nodes (41): alembic_config, dispose_engine(), close_redis(), lifespan(), Start the WS hub + notification dispatcher; tear them down cleanly., ServerStatus, task, Flag silent servers OFFLINE, recover returning ones. Safe to overlap. (+33 more)

### Community 31 - "auth_service.py"
Cohesion: 0.10
Nodes (48): active_memberships(), The user's memberships in non-suspended organizations, oldest first. Reads only…, System scope bound to *db*, for rows that have no organization. Used by exactly…, system_write_scope(), _audit(), _auth_event_scope(), _bootstrap_organization(), change_own_password() (+40 more)

### Community 32 - "AcmeDirectory"
Cohesion: 0.09
Nodes (45): AcmeDirectory, Which certificate authority a per-organization ACME account belongs to. A…, Whether this directory issues publicly trusted certificates. The single…, Whether a certificate from this directory is trusted by a browser. False for…, Short operator-facing name, stored in metadata and shown in the API., AcmeDirectoryError, assert_issuance_allowed(), coerce_directory() (+37 more)

### Community 33 - "test_rate_limit.py"
Cohesion: 0.12
Nodes (25): RateLimited, client_ip(), _enforce(), _memory_count_and_ttl(), node_rate_limit(), _dependency(), Request, rate_limit() (+17 more)

### Community 34 - "docker_hosts.py"
Cohesion: 0.07
Nodes (55): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+47 more)

### Community 35 - "integration/test_certificate_issuance.py"
Cohesion: 0.10
Nodes (40): cleanup_incomplete(), load(), The generation's order document, or an empty one. **Never raises.** A malformed…, Records this platform published and still cannot confirm are gone., _create_domain(), _create_provider(), _credential_seam(), _dns_stub() (+32 more)

### Community 36 - "NginxBundle"
Cohesion: 0.12
Nodes (16): Render the complete desired state for *node*. A full tree every time — never a…, BundleFile, fingerprint_files(), is_allowed_bundle_path(), NginxBundle, field_validator, One rendered file. The path is allowlisted, the content is bounded., Deterministic fingerprint over the complete rendered tree. Path order is… (+8 more)

### Community 37 - "v1/search.py"
Cohesion: 0.37
Nodes (13): _hit(), AsyncSession, Cross-entity global search powering the Ctrl+K command palette. Every section…, Search this organization's members — never the instance's accounts. ``users``…, _search_containers(), _search_deployments(), _search_incidents(), _search_monitors() (+5 more)

### Community 38 - "models/__init__.py"
Cohesion: 0.08
Nodes (66): The per-organization ACME account and its protected account key. One account…, Base, big_serial_pk(), json_column(), OrgScoped, datetime, UUID, Declarative base, shared mixins and column helpers. (+58 more)

### Community 39 - "test_channel"
Cohesion: 0.23
Nodes (12): create_channel(), delete_channel(), delete, ManageCtx, patch, post, Request, Response (+4 more)

### Community 40 - "DockerProvider"
Cohesion: 0.12
Nodes (8): DockerProvider, Any, Protocol, List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``., List volumes: keys ``name``, ``driver``, ``mountpoint``., List networks: keys ``name``, ``driver``, ``scope``., Structural interface implemented by real and simulated providers., Return True when the remote daemon answers.

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.08
Nodes (49): CheckResult, coerce_headers(), _decode(), get_transport(), HTTPMonitorTransport, Any, BaseException, Pluggable monitor check transports (real HTTP + deterministic simulator). A… (+41 more)

### Community 42 - "test_migration_phase5212.py"
Cohesion: 0.13
Nodes (25): _columns(), Phase 5.2.1.2 migration (`a7b8c9d0e1f2`): the envelope leaves…, ``column -> (data_type, is_nullable)`` for *table*., ``(org_id, ciphertext, generation)`` for every populated envelope, ordered., The move creates rows only where there was key material. A row with a NULL…, Two envelopes for one tenant are refused by the database, not by a service., F3: a negative generation, and either half of an inconsistent pair, fail. The…, RLS plus the grant: the policies are only load-bearing for a non-owner role.… (+17 more)

### Community 43 - "AuthContext.tsx"
Cohesion: 0.02
Nodes (83): Membership, SearchResult, User, AuthContext, AuthProvider(), AuthState, isOrgSelectionError(), MeResponse (+75 more)

### Community 44 - "project_service.py"
Cohesion: 0.13
Nodes (47): Application, DeploymentEnvironment, Project, A **project-scoped** deployment environment (Phase 2 promotion). The…, actor_of(), _apply_update(), _check_server(), create_application() (+39 more)

### Community 45 - "test_permissions.py"
Cohesion: 0.17
Nodes (9): _auth_context(), Unit tests for the permission registry, scope matching and RBAC gate., A fake context in the given organization. ``membership_status=None`` models a…, test_api_key_scope_intersects_role_permissions(), test_membership_is_required_for_authority(), test_plain_user_without_permissions_is_denied(), test_superadmin_bypasses_everything(), test_superadmin_owned_api_key_is_limited_to_its_scope() (+1 more)

### Community 46 - "test_kek_health_api.py"
Cohesion: 0.15
Nodes (16): MonkeyPatch, parametrize, Provider health on the readiness surface, seen through the API. The approved…, A probe is unauthenticated in most deployments; it must leak nothing., Liveness must not acquire a provider dependency by accident., A provider that answers truthfully and is never asked to do more., The suite selects the deterministic provider explicitly, so it is healthy., The whole point of reporting instead of gating: the API keeps serving. (+8 more)

### Community 47 - "test_phase3_nodes.py"
Cohesion: 0.14
Nodes (35): Run the enclosed block with tenant filtering off (maintenance only). ``reason``…, system_scope(), _create_token(), _dispatch(), _enroll(), _enrolled_node(), _load_agent_module(), _mutate_in_system_scope() (+27 more)

### Community 48 - "UnprocessableEntity"
Cohesion: 0.07
Nodes (64): UnprocessableEntity, assert_safe_tcp_endpoint(), assert_safe_url(), assert_safe_url_async(), _is_forbidden_address(), is_simulation_url(), ValueError, _raise_block() (+56 more)

### Community 49 - "test_ws_hub.py"
Cohesion: 0.14
Nodes (25): _connection(), _drain(), _event_frame(), _fake_sessionmaker(), _FakeSession, hub(), _Org, Any (+17 more)

### Community 50 - "roles.py"
Cohesion: 0.12
Nodes (27): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, delete, get (+19 more)

### Community 51 - "DbDep"
Cohesion: 0.15
Nodes (22): delete_server(), get_server(), list_enrollment_tokens(), list_servers(), list_tags(), node_proxy_status(), node_route_targets(), DbDep (+14 more)

### Community 52 - "proxy_service.py"
Cohesion: 0.05
Nodes (107): ListenerOwnership, ProxyApplyOutcome, Terminal outcome of one ``nginx.apply`` operation on a node., Who holds one required listener port, per the node's pre-flight. The…, Alias for :attr:`extra`, so the API can expose open-ended agent facts. The…, Server, Operation, Whether the agent reported this operation as successful. A terminal check, not… (+99 more)

### Community 53 - "WrappedKey"
Cohesion: 0.05
Nodes (50): AsyncBaseTransport, _derive(), The deterministic in-process provider — tests and explicitly configured dev.…, A per-(binding, key version) key: HKDF-style derivation. Two properties, both…, _construct(), Provider construction — the only place a ``KEKProvider`` is ever created. One…, Provider health, cached, for the readiness surface. Health is the one place a…, KEKConfigurationError (+42 more)

### Community 54 - "update_organization"
Cohesion: 0.16
Nodes (14): create_organization(), list_my_organizations(), CurrentUser, DbSessionDep, get, IdentityUser, patch, post (+6 more)

### Community 55 - "test_agent_nginx_contract.py"
Cohesion: 0.07
Nodes (58): CapabilityReport, One node-reported capability. ``present`` defaults to false, and a capability…, _agent_bundle(), agent_fixture(), _bootstrap_fixture(), _load_agent(), Any, fixture (+50 more)

### Community 56 - "create_user"
Cohesion: 0.18
Nodes (18): create_user(), deactivate_user(), get_user(), list_users(), CurrentUser, DbSessionDep, delete, get (+10 more)

### Community 57 - "alembic"
Cohesion: 0.04
Nodes (16): alembic, downgrade(), rename ``server.*`` permission codenames to ``node.*`` The Node/Server…, _rename_permissions(), upgrade(), Fix pre-existing model/migration drift (surfaced by the new drift check). Two…, downgrade(), Phase 2.1 — correct legacy ``environment_type`` classification. The Phase 2… (+8 more)

### Community 58 - "notification_service.py"
Cohesion: 0.23
Nodes (18): DeliveryStatus, _attempt_delivery(), decode_delivery_cursor(), _send(), encode_delivery_cursor(), _invoke_sender(), list_deliveries(), _now() (+10 more)

### Community 59 - "helpers.py"
Cohesion: 0.06
Nodes (73): bearer(), cookie_attributes(), login_account(), login_headers(), Any, AsyncClient, Response, Pure helpers for journey tests: payloads, auth shortcuts, cookie parsing. (+65 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "_list_deployments"
Cohesion: 0.11
Nodes (31): cancel_deployment(), _emails_for(), get_deployment(), list_application_deployments(), _list_deployments(), _parse_sort(), _parse_statuses(), alias (+23 more)

### Community 62 - "test_error_logging.py"
Cohesion: 0.22
Nodes (4): Regression: the catch-all 500 handler must not log raw exception text.…, _SpyLogger, test_unhandled_exception_handler_logs_class_not_message(), fastapi_testclient

### Community 63 - "dns_verifier.py"
Cohesion: 0.13
Nodes (20): apex_of(), The name a wildcard Domain is anchored at (``*.example.com`` →…, The exact TXT owner name a user must publish at their provider., verification_record_name(), discover_authoritative_nameservers(), _discover_nameservers(), _normalise_ns(), observe() (+12 more)

### Community 64 - "test_phase2_environments.py"
Cohesion: 0.18
Nodes (22): _environment(), _project(), parametrize, Phase 2: project-scoped environments, config layering, and their isolation. The…, Uniqueness is ``(project_id, slug)`` — not instance-wide., The update path is validated too (the pre-Phase-2 gap)., Knowing an environment UUID is not access: the project link must hold., Another tenant cannot reach the project, its environments, or its detail. (+14 more)

### Community 65 - "AuthContext"
Cohesion: 0.08
Nodes (54): AuthContext, UUID, Resolved identity plus the organization this request acts in.…, The active organization, or raise if this request has none., Last nginx apply outcome for a route, as reported by its node's agent.…, How far a route's *removal* has got, which ``config_state`` cannot say. A route…, RouteConfigState, RouteRemovalState (+46 more)

### Community 66 - "test_schema_redaction.py"
Cohesion: 0.18
Nodes (17): is_sensitive_header(), mask_sensitive_headers(), True when *name* looks like it carries a credential (Authorization etc.)., Return a copy of *headers* with sensitive values replaced by a mask., mask_target(), Human-readable masked target safe to expose over the API. For webhook families…, _monitor_out(), Outbound-schema redaction: monitor probe credentials and webhook targets.… (+9 more)

### Community 67 - "publish"
Cohesion: 0.07
Nodes (49): ActorType, create_api_key(), AsyncSession, Request, UUID, Revoke a key owned by *owner_id*. Foreign keys look like NotFound (no leak)., Revoke every live key of a user (used on deactivation). Returns count., Create a key for *user_id*. Returns ``(row, raw_key)`` — raw shown once. The… (+41 more)

### Community 68 - "Certificate Management — NexusOps"
Cohesion: 0.14
Nodes (13): Which known directory this account is at; ``None`` when the URL is neither.…, The directory a stored URL names, or ``None`` when it names none. ``None``…, 10. Status/expiry tracking and monitor tie-in, 12. Audit and events, 13. Non-goals, 2. Certificate entity, 3. API surface and permissions, 5.1 Shipped (5.3): the flow as it actually runs (+5 more)

### Community 69 - "seed.py"
Cohesion: 0.14
Nodes (24): EnvironmentType, Kind of a project-scoped deployment environment (Phase 2). Descriptive only —…, UserStatus, ApiKey, A login session binding refresh tokens to a device/context., Machine credential. Raw key shown once at creation; hash stored. A key is bound…, Session, User (+16 more)

### Community 70 - "core/tenancy.py"
Cohesion: 0.10
Nodes (30): _apply_scope_guc(), _desired_guc(), _guard(), _has_org_predicate(), install_tenancy_guards(), _mappers_of(), _org_scoped_classes(), org_scoped_table_names() (+22 more)

### Community 71 - "test_secrets.py"
Cohesion: 0.11
Nodes (26): Exception, A ``${secret:KEY}`` reference could not be resolved. Fail-closed. Carries…, One successfully resolved reference: metadata for audit, no value., Resolve every ``${secret:KEY}`` reference an environment's config names.…, resolve_secrets_for_environment(), SecretReference, SecretResolutionError, _create() (+18 more)

### Community 72 - "test_nginx_renderer.py"
Cohesion: 0.15
Nodes (33): NginxProvider, The only production provider in Phase 4., provider(), fixture, parametrize, The renderer: determinism, the injection boundary, and the Phase 4 HTTP-only…, route(), test_apply_params_are_a_closed_shape() (+25 more)

### Community 73 - "domain_service.py"
Cohesion: 0.09
Nodes (43): Domain, One DNS name an organization is proving it controls. ``name`` is canonical (see…, What the lifecycle should do with an observation., VerificationDecision, _actor(), apply_decision(), _bad_name(), claim_verified_name() (+35 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "monitors.py"
Cohesion: 0.15
Nodes (37): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+29 more)

### Community 76 - "enums.py"
Cohesion: 0.06
Nodes (65): asyncio, _load_organization(), permission_dep(), Any, Organization, FastAPI dependencies: database session, authenticated tenant context, RBAC…, Dependency factory enforcing a permission; returns 403 when denied., require_permission() (+57 more)

### Community 77 - "test_acme_accounts.py"
Cohesion: 0.11
Nodes (41): account_for(), account_key_fingerprint(), find_account(), Request, Fingerprint the **public** half of a PEM account key. Over the public key…, The organization's account at *directory*, if it has one. Read-only., The organization's account at *directory*, created on first use. Creating the…, The named directory, or a 422 naming the closed set. Deliberately *not* a… (+33 more)

### Community 78 - "StrEnum"
Cohesion: 0.16
Nodes (32): EnrollmentTokenState, IncidentEventKind, IncidentSeverity, IncidentStatus, Derived lifecycle state of an enrollment token, computed server-side. Stored as…, String enum; member names equal values so name/value storage never disagrees., StrEnum, Incident (+24 more)

### Community 79 - "test_phase2_secrets.py"
Cohesion: 0.17
Nodes (23): decrypt_str(), _env(), _project(), Phase 2 secrets: layered scope, immutable versions, rollback, isolation. Two…, Two racing rotations must both be kept and never share a version number., Another tenant cannot read, rotate, roll back or even enumerate the secret., The documented example: same key at three scopes; most specific wins., A ref declared in the project base config resolves for its environments. (+15 more)

### Community 80 - "RolesPage.tsx"
Cohesion: 0.11
Nodes (15): Role, RolesPage, describeError(), GROUP_STYLE, LEGEND_STYLE, OPTION_STYLE, PermissionSpec, roleAllows() (+7 more)

### Community 81 - "test_schemas_server.py"
Cohesion: 0.21
Nodes (22): Payload for registering a server., Partial update. ``tags`` replaces the full set when provided., ServerCreate, ServerUpdate, _base(), parametrize, Unit tests for app.schemas.server (validation only, no I/O)., test_empty_ip_is_allowed_but_whitespace_collapses() (+14 more)

### Community 82 - "InvalidName"
Cohesion: 0.10
Nodes (40): _canonicalize(), canonicalize_name(), canonicalize_path(), canonicalize_record_name(), _check_labels(), _check_not_ip(), hostname_is_covered(), _idna() (+32 more)

### Community 83 - "tests/conftest.py"
Cohesion: 0.20
Nodes (8): configure_test_env(), Test bootstrap: pin every cached setting BEFORE the first ``app`` import. The…, KEY=VALUE pairs from the repo .env (first definition wins); never logged., Export the exact settings the app caches; host values cannot leak through., _read_dot_env(), os, pathlib, sys

### Community 84 - "server_service.py"
Cohesion: 0.04
Nodes (69): container_log_channel(), Canonical Redis pub/sub channel names shared by API, workers and WS hub., server_metrics_channel(), get_redis(), ping(), Shared async Redis client., LogSource, LogLine (+61 more)

### Community 85 - "user_service.py"
Cohesion: 0.12
Nodes (40): MembershipStatus, _apply_deactivation(), _assert_not_last_active_member(), _assert_not_last_active_superadmin(), create_user(), deactivate_user(), get_by_email(), get_member() (+32 more)

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "NotFound"
Cohesion: 0.10
Nodes (47): Conflict, NotFound, OperationStatus, Lifecycle of one node operation (node-agent-architecture.md §5.1).…, _active_org(), _bounded(), cancel_operation(), claim_operation() (+39 more)

### Community 88 - "test_certificate_lifecycle.py"
Cohesion: 0.06
Nodes (41): CertificateGeneration, directory_known_predicate(), directory_required_predicate(), known_directory_urls(), material_guard_predicate(), one_live_generation_predicate(), pre_issuance_predicate(), Certificates and their generations — the Phase 5 metadata foundation. Two… (+33 more)

### Community 89 - "test_payload_crypto.py"
Cohesion: 0.08
Nodes (54): decrypt(), encrypt(), fingerprint(), _parse_header(), PayloadContextMismatch, PayloadDecryptionError, PayloadEnvelopeError, PayloadError (+46 more)

### Community 90 - "domain_routing.py"
Cohesion: 0.14
Nodes (25): The honest state of a route that left the desired tree but is not gone. One…, removal_requested_detail(), _affected_node_ids(), _announce(), _apply_for_node(), _audit_action(), datetime, task (+17 more)

### Community 91 - "dns_provider_service.py"
Cohesion: 0.10
Nodes (43): DnsProvider, One stored DNS credential plus the scope it is allowed to touch., DnsProviderKind, Which DNS API a stored credential speaks to. One member in v1 (Cloudflare) —…, provider_for(), The credential-verification implementation for *kind*. Separate from…, DnsProviderCreate, Payload for ``POST /dns-providers``. ``credentials`` is a provider-shaped blob… (+35 more)

### Community 92 - "alerts.py"
Cohesion: 0.21
Nodes (16): list_alerts(), mark_all_read(), mark_read(), CurrentUser, DbDep, Depends, get, post (+8 more)

### Community 93 - "ScopedSession"
Cohesion: 0.11
Nodes (11): A session that enters its tenancy scope around each operation. A fixture cannot…, ScopedSession, 10. Migration (Phase 1), 1. Tenancy invariants, 2.1 Org creation — v1 decision, 3. The session guard (the mechanical layer), 4. Background jobs, 6. Agents (+3 more)

### Community 94 - "test_phase21_secret_version_integrity.py"
Cohesion: 0.18
Nodes (18): _app_role_dsn(), _owner_dsn(), _probe(), Phase 2.1 — ``secret_versions`` is append-only in the **database**, not just in…, Immutability is a database guarantee, not merely a missing code path. The owner…, The legitimate append paths keep working under the guard., The documented deletion policy: purging a Secret cascades its history., RLS is preserved: another tenant cannot see a version row, even by id. (+10 more)

### Community 95 - "AsyncSession"
Cohesion: 0.12
Nodes (30): _detail(), AsyncSession, _actor_kwargs(), container_counts(), create_server(), delete_server(), get_server(), list_tags_with_usage() (+22 more)

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
Nodes (70): org_dek(), Fernet, Yield the organization's DEK for **one operation**, then drop it. The key-only…, db(), A session with **no** tenant scope. Deliberately unscoped: it is how a test…, _BarrierRewrapProvider, org_id(), _plaintext_key() (+62 more)

### Community 100 - "redact_mapping"
Cohesion: 0.09
Nodes (35): _is_sensitive_key(), Return a copy of *data* with sensitive values replaced, at any depth. Two…, Substring match on a normalised key so header-style names are caught too.…, redact_mapping(), parametrize, Unit tests for app.core.logging redaction (pure functions only)., No sensitive key name involved: the PEM armor is the only signal., Lists of dicts holding further lists — the shape an agent report takes. (+27 more)

### Community 101 - "DeterministicKEKProvider"
Cohesion: 0.05
Nodes (49): DeterministicKEKProvider, Deterministic wrap/unwrap/rewrap over an in-process AEAD., Bump the modelled KEK version, so a test can prove rewrap moves it., EncryptionContext, What a wrapped DEK is bound to. Frozen: a context is not edited in place., The canonical, unambiguous binding string. Field order and separator are fixed…, The binding as a provider expects it: base64, never line-wrapped. Wrap-free…, Parse a stored envelope, strictly. Every rejection is a named… (+41 more)

### Community 102 - "library.py"
Cohesion: 0.07
Nodes (40): AuthorizationResource, AcmeConfigError, AcmeError, AcmeRateLimited, AcmeRejected, AcmeTimeout, AcmeUnavailable, classify_error() (+32 more)

### Community 103 - "Path"
Cohesion: 0.12
Nodes (15): Path, An unloadable CA file must error, never silently fall back to no verify., A throwaway key + self-signed cert for ``localhost`` (real handshakes)., A one-shot HTTPS server; records a failed handshake instead of crashing., A real handshake against a self-signed server must fail verification., Trusting that same cert as a CA lets the identical handshake through., A link-local URL over plain HTTP must fail before any request or write., _self_signed_cert() (+7 more)

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
Nodes (36): _columns(), _foreign_keys(), _indexes(), _insert_certificate(), _insert_generation(), _integrity_error(), _migrate_from_phase4(), _migrate_to_phase5() (+28 more)

### Community 108 - "docker_real.py"
Cohesion: 0.13
Nodes (22): Exception, Build a compact, secret-free description of a provider failure. Only the…, sanitize_error(), _as_float(), _compute_stats(), _cpu_percent(), _network_bytes(), parse_log_line() (+14 more)

### Community 109 - "Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)"
Cohesion: 0.25
Nodes (9): API keys (X-API-Key, nxo_..., scope intersection), First boot sequence (api entrypoint migrates, compose never seeds), Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test), Makefile workflows (up/test/lint/typecheck/migrate/seed), HIGH finding: API-key scope bypass for superadmin-owned keys (fixed: scope intersection first), Security audit 2026-09 (26 raw findings -> 20 confirmed, all fixed), HIGH finding: known seed superadmin + API key backdoor (fixed: NEXUSOPS_ALLOW_SEED opt-in, one-time password), Threat model (edge attacker, malicious agent, curious operator, leaked token, SSRF) (+1 more)

### Community 110 - "routes.py"
Cohesion: 0.13
Nodes (35): create_route(), delete_route(), disable_route(), _domain_status(), enable_route(), get_route(), list_routes(), AsyncSession (+27 more)

### Community 111 - "run_async"
Cohesion: 0.09
Nodes (31): flush_pending_publishes(), Wait for frames scheduled by ``after_commit`` hooks to reach Redis. The commit…, task, Execute one queued deployment. The engine owns all state transitions., Re-enqueue deployments the broker lost; fail ones whose worker died.…, run_deployment(), sweep_deployments(), _run() (+23 more)

### Community 112 - "middleware.py"
Cohesion: 0.14
Nodes (15): ASGIApp, AccessLogMiddleware, HTTP middleware: request ids, security headers, structured access logs., Baseline hardening headers on every API response., RequestIDMiddleware, SecurityHeadersMiddleware, create_app(), _include_routers() (+7 more)

### Community 113 - "dnsmock.py"
Cohesion: 0.12
Nodes (24): resolver(), answer(), encode_name(), encode_txt(), forward(), main(), parse_question(), TXT rdata: one or more length-prefixed strings, each ≤ 255 bytes. (+16 more)

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "v1/auth.py"
Cohesion: 0.08
Nodes (46): change_password(), _clear_refresh_cookie(), _cookies_secure(), login(), logout(), me(), _optional_actor(), AsyncSession (+38 more)

### Community 116 - "test_tenancy_allowlist.py"
Cohesion: 0.20
Nodes (14): AST, _actual_callers(), _calls_system_scope(), _module_path(), Path, The system-scope allowlist is the only fence around the tenancy carve-out.…, Every module that could open a system scope: ``app/`` plus the scripts., No module may lift tenant isolation without being named in the list. (+6 more)

### Community 117 - "_alembic_config"
Cohesion: 0.11
Nodes (20): _alembic_config(), _at_revision(), _migration_dsn(), _owner_dsn(), Run one Alembic direction against ``database`` through the app's settings path.…, Phase 2 adds one migration; heads must not fork., test_exactly_one_alembic_head(), Phase 3 adds one migration; heads must not fork. (+12 more)

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
Nodes (57): A valid POST /servers body with per-test overrides., server_payload(), test_token_cannot_claim_a_foreign_tenants_node(), test_v1_heartbeat_keeps_the_204_contract(), Regression: a superadmin-owned key is still limited to its scope list. The…, test_scoped_api_key_cannot_exceed_its_grant(), _create_server(), Server CRUD, cascade delete, audit trail rows and audit immutability. (+49 more)

### Community 123 - "_run_migration"
Cohesion: 0.16
Nodes (19): alembic_script, Phase 2 migration (`b2c3d4e5f6a7`) against realistic legacy data. The promotion…, Upgrade ``database`` to ``revision``., The pre-Phase-2 shapes: application-scoped environments, per-app dupes., A fresh database reaches the same shape the models describe., _run_migration(), _seed_legacy_data(), test_environment_type_check_rejects_unknown_kinds() (+11 more)

### Community 124 - "test_dns_providers.py"
Cohesion: 0.10
Nodes (41): _audits(), _create(), _create_domain(), _created(), _events(), _member_with_role(), _org_id(), Any (+33 more)

### Community 125 - "OperationError"
Cohesion: 0.13
Nodes (19): _demux_docker_stream(), _docker_error(), execute_operation(), OperationError, _process_pending_operations(), Exception, A stable, sanitized failure contract for the control plane., Re-validate the operation's parameters locally, against a closed shape. (+11 more)

### Community 126 - "list_operations"
Cohesion: 0.14
Nodes (22): cancel_operation(), create_operation(), get_operation(), list_operations(), DbDep, Depends, get, post (+14 more)

### Community 127 - "list_dns_providers"
Cohesion: 0.12
Nodes (27): create_dns_provider(), delete_dns_provider(), get_dns_provider(), list_dns_providers(), DbDep, delete, Depends, get (+19 more)

### Community 137 - "DockerHostsPage.test.tsx"
Cohesion: 0.18
Nodes (8): DockerHostOut, ApiError, failingHost, host, hostsPage, mockCountApi(), server, serversPage

### Community 146 - "_Attempt"
Cohesion: 0.09
Nodes (30): _Attempt, _AttemptFailure, _Material, Any, Exception, Record the failure and schedule the retry; report whether it is terminal. Both…, Delete every TXT record this generation created and cannot confirm gone.…, Delete one record by its reference, recording the outcome truthfully. (+22 more)

### Community 147 - "get_settings"
Cohesion: 0.07
Nodes (32): _quoted_list(), Add the operations framework table (node-agent-architecture.md §5). One tenant-…, upgrade(), downgrade(), _drop_constraint(), _quoted_list(), Phase 2 — projects & environments: env promotion, config, secret versions. This…, upgrade() (+24 more)

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
Cohesion: 0.02
Nodes (87): AlertOut, CapabilityReport, ChannelOut, CheckOut, DeliveryOut, DeploymentLogLine, DeploymentStatus, DomainDetailOut (+79 more)

### Community 154 - "nexusops-draft.mjs"
Cohesion: 0.40
Nodes (4): DOCS, meta, SPINE, VERIFY_RULES

### Community 155 - "v1/secrets.py"
Cohesion: 0.11
Nodes (37): create_secret(), delete_secret(), get_secret(), list_secret_versions(), list_secrets(), DbSession, delete, get (+29 more)

### Community 156 - "nexusops-challenge.mjs"
Cohesion: 0.33
Nodes (5): CHALLENGE_COMMON, meta, RESEARCH_COMMON, SCHEMA, TASKS

### Community 157 - "Secrets Architecture"
Cohesion: 0.11
Nodes (18): 10. Resolution flow at deploy time, 1.1 Storage and crypto, 1.2 Data model, 1.3 API surface (metadata-only reads), 1.6 Gap list (Phase 2 status), 1. Current state, 2.1 Resolution runs inside org scope, 2.2 Migration mapping (applied by `b2c3d4e5f6a7`) (+10 more)

### Community 158 - "test_schemas_agent.py"
Cohesion: 0.12
Nodes (35): AgentContainerIn, AgentHeartbeatIn, AgentHelloIn, Observed container state reported by an agent., Periodic metrics + observed containers from an enrolled agent. Network counters…, First contact from an agent after enrollment; fills static host facts., _container(), _heartbeat() (+27 more)

### Community 159 - ".state"
Cohesion: 0.07
Nodes (35): computed_field, Derived lifecycle state: revoked wins over used wins over expired., 1.2 Phase 5 in one sentence, 1.3 Trust boundaries Phase 5 adds, 1.4 Non-goals for Phase 5, 1.5 Trust concentration: centralized key custody, accepted **conditionally** (decided), 1. Architecture and trust boundaries, 2.1 The six stages, kept distinct (+27 more)

### Community 160 - "test_kek_vault_transit_live.py"
Cohesion: 0.07
Nodes (45): _ca_context(), _configure(), _ctx(), _docker(), _free_port(), LiveVault, fixture, Path (+37 more)

### Community 161 - "alert_service.py"
Cohesion: 0.28
Nodes (12): Alert, create_alert(), get_alert(), mark_all_read(), mark_read(), AsyncSession, UUID, Alert inbox: insert-only creation plus read/unread bookkeeping. (+4 more)

### Community 162 - "decide"
Cohesion: 0.23
Nodes (18): decide(), matches_token(), Constant-time comparison of the observed TXT values against the token. TXT…, Turn one observation into the verification outcome — pure, no I/O.…, observation(), parametrize, The verification decision: every outcome, without a network. ``decide`` is…, test_a_sweep_invalidates_a_changed_delegation_even_with_the_token() (+10 more)

### Community 163 - "RateLimit"
Cohesion: 0.29
Nodes (4): model_validator, RateLimit, One route's request-rate ceiling (rendered as a ``limit_req_zone``)., test_rate_limit_constraints()

### Community 164 - "AgentClient"
Cohesion: 0.15
Nodes (8): AgentClient, _docker_raw(), SSLContext, A verifying TLS context. Verification is never disabled. A private/self-hosted…, Refuse to send credentials over plain HTTP to a non-loopback server. The…, One raw Docker API call; returns ``(status, body_bytes)``., _tls_context(), _UnixHTTPConnection

### Community 165 - "test_kek_selection.py"
Cohesion: 0.05
Nodes (61): build_kek_provider(), Drop the cached provider (tests, and any future configuration reload)., Return the configured provider, or raise naming exactly what is wrong., reset_kek_provider(), provider_health(), Drop every cached verdict (tests, and any future configuration reload)., The configured provider's health, at most one probe per cache window., reset_health_cache() (+53 more)

### Community 166 - "nginx.py"
Cohesion: 0.14
Nodes (23): _header_lines(), ValueError, _quote(), _rate_zone(), NginxProvider — a pure, deterministic renderer plus the two op wrappers.…, Validate the route's headers and split them by destination., Wrap an already-validated value in quotes for a template slot. Values reaching…, The ``limit_req_zone`` declaration for a rate-limited route. (+15 more)

### Community 167 - "resolve_auth"
Cohesion: 0.14
Nodes (22): _attach_organization(), get_current_user(), get_identity(), get_optional_user(), _load_permissions(), _org_id_from_header(), AsyncSession, DbSessionDep (+14 more)

### Community 168 - "unit/test_certificate_issuance.py"
Cohesion: 0.07
Nodes (44): _aware(), _expectations(), _failure_from(), _generate_key_and_csr(), _identifiers(), _leaf_of(), BaseException, EllipticCurvePrivateKey (+36 more)

### Community 169 - "pytest"
Cohesion: 0.16
Nodes (12): created_at server defaults must evaluate per insert, not at table creation., Regression: system_events and audit_logs shipped with DEFAULT 'now()' (quoted…, test_audit_and_event_created_at_defaults_are_dynamic(), UUID, Phase 2.2 — the environment-type correction follows the documented precedence.…, Only the previous migration's ``PROD`` output is corrected. A row already…, Create one legacy (application-scoped) environment per case., Every branch of the slug-first rule, end to end through ``head``. (+4 more)

### Community 170 - "test_agent_contract.py"
Cohesion: 0.20
Nodes (15): agent_fixture(), _load_agent(), _patch_stats(), Any, fixture, MonkeyPatch, Contract tests: the shipped agent's payloads must satisfy the ingest schemas.…, One-shot docker stats reduce to cpu/mem/limit fields the schema accepts, with… (+7 more)

### Community 171 - "test_kek_vault_transit.py"
Cohesion: 0.10
Nodes (49): _ctx(), _login_ok(), _provider(), parametrize, Request, Response, The Vault Transit adapter's HTTP contract, without a Vault. This module pins…, encrypt, decrypt *and* rewrap: the binding must survive a rotation. (+41 more)

### Community 172 - "CheckOutcome"
Cohesion: 0.29
Nodes (5): CheckOutcome, MonitorTransport, Protocol, Result of a single monitor check., Anything that can execute a check for a monitor.

### Community 175 - "v1/health.py"
Cohesion: 0.20
Nodes (13): liveness(), get, Response, Health probes: liveness (always cheap) and readiness (checks dependencies).…, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness(), HealthOut (+5 more)

### Community 176 - "Platform Security Model — NexusOps"
Cohesion: 0.11
Nodes (18): make(), 10.1 Node revocation playbook (compromised node / leaked agent token), 10.2 Key compromise playbook, 10. Incident response, 1. Scope, stance, and simulation honesty, 2. Assets, 3. Trust boundaries, 4. Tenant isolation model (summary) (+10 more)

### Community 177 - "Node & Agent Architecture"
Cohesion: 0.08
Nodes (26): install_hint(), The one-liner an operator pastes, without the raw token in argv. The token…, 1. Scope and stance, 3.2 Enrollment v2, 3.3 Token storage & rotation with dual-token grace, 3.4 Revocation semantics — fixing the 401 hot-loop, 3.5 Reconnect / offline states, 3. Agent lifecycle (+18 more)

### Community 178 - "main"
Cohesion: 0.11
Nodes (19): build_facts(), _build_hello_payload(), _enroll(), _interruptible_sleep(), main(), memory_total_mb(), network_rates(), network_total_bytes() (+11 more)

### Community 179 - "_dns_stub"
Cohesion: 0.40
Nodes (5): _dns_stub(), _fake_observe(), fixture, MonkeyPatch, Stand in for authoritative DNS in every test in this module.

### Community 180 - "ServerOut"
Cohesion: 0.28
Nodes (6): computed_field, Whether the node has reported capabilities at all (v2 hello)., Full server view with recent timeline events and container counts., Server as listed in collections. Never exposes the agent token hash., ServerDetail, ServerOut

### Community 181 - "_nginx_apply"
Cohesion: 0.12
Nodes (25): _fsync_dir(), _nginx_apply(), Materialize the bundle under ``staged/<id>/`` and return that directory.…, Build a self-contained config for ``nginx -t`` over the staged tree. The…, Move the staged tree over the live one, keeping the previous as backup., Put the previous known-good tree back. Returns whether it was possible., Stage → validate → swap → reload, with a rollback on a failed reload., Persist the last apply outcome atomically (temp + rename). (+17 more)

### Community 182 - "_rows"
Cohesion: 0.22
Nodes (17): Move ``database`` *back* to ``revision``. The same code path a deployment uses…, _rows(), _run_downgrade(), _columns(), Phase 5.2.1 migration (`f5a6b7c8d9e0`): two columns, one invariant, one…, The naming convention must not be applied twice. A fresh database is the only…, A ciphertext behind generation 0, and a generation with no material, both fail., The refusal is the point: a rollback must not delete key material. (+9 more)

### Community 183 - "list_events"
Cohesion: 0.22
Nodes (13): _decode_cursor(), _encode_cursor(), list_event_types(), list_events(), datetime, DbSession, Depends, get (+5 more)

### Community 184 - "encrypt_str"
Cohesion: 0.14
Nodes (18): Any, structlog processor: scrub one record before anything renders it. The pipeline…, Replace every embedded PEM private-key block in *value* with the marker. Only…, Scrub PEM private-key blocks out of one free-text value. The scalar counterpart…, Recursively redact one value of any shape — the depth-agnostic walk. Dicts,…, redact_log_event(), _redact_private_key_blocks(), redact_text() (+10 more)

### Community 185 - "20261012_1200-c8d9e0f1a2b3_phase5_certificate_metadata.py"
Cohesion: 0.23
Nodes (13): downgrade(), _drop_certificate_permissions(), _drop_tenant_policies(), _grant(), _in_list(), Phase 5.1 — certificate metadata and the pre-issuance lifecycle. Adds, in one…, Grant the app role on *table*; the migration role GUC carries the name. The…, The two-policy shape every tenant table uses: tenant + system scope. (+5 more)

### Community 186 - "apply_scope_to_session"
Cohesion: 0.04
Nodes (110): get_sessionmaker(), async_sessionmaker, AsyncSession, apply_scope_to_session(), current_org(), org_scope(), RuntimeError, UUID (+102 more)

### Community 187 - "test_schemas_search.py"
Cohesion: 0.33
Nodes (8): Results grouped per entity type, permission-filtered per caller. Every section…, SearchResultOut, Unit tests for global-search schemas., test_extra_fields_are_forbidden(), test_search_hit_requires_core_fields(), test_search_result_defaults_to_empty_sections(), test_search_result_exposes_exactly_the_documented_sections(), test_sections_hold_hits()

### Community 188 - "Deployment Architecture — NexusOps (target state)"
Cohesion: 0.17
Nodes (12): 10. Events and WS during runs, 12. Rollback semantics (existing behavior kept), 13. The simulated runner stays — labeled, 14. Open questions, 1. Current state — what is real and what is simulated, 3. Target pipeline, 4. Runner registry — the DI fix, 6. Phased scope (+4 more)

### Community 189 - "phase3.spec.ts"
Cohesion: 0.15
Nodes (10): frontend_e2e_fixtures_expect, AGENT, NodeDetail, OperationRow, REPO_ROOT, ref_node_child_process, ref_node_fs, ref_node_os (+2 more)

### Community 190 - "Settings"
Cohesion: 0.10
Nodes (10): field_validator, model_validator, Whether the runtime connection is the RLS-enforced application role. False…, Username from :attr:`database_url`, or ``None`` if it is unparseable., Validated application settings (loaded from environment / .env)., Refuse a Vault address that carries userinfo (Phase 5.2.1.2, F4).…, Refuse to start with an ACME directory selection that is unsafe or ambiguous.…, Refuse to start with an unusable or unsafe key source. Two failures are worth… (+2 more)

### Community 191 - "dns/__init__.py"
Cohesion: 0.07
Nodes (31): Cloudflare: credential verification, and the DNS-01 record operations. The…, DnsCredentialError, DnsProviderError, DnsProviderRejected, DnsProviderUnavailable, DnsRecordProvider, DnsWriteAmbiguous, _provider_class() (+23 more)

### Community 192 - "env.py"
Cohesion: 0.24
Nodes (10): _database_url(), Alembic environment: metadata comes from app.models, URL from app settings., Migrations run as the table **owner**, never as the application role. The owner…, Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online(), Owner-role DSN for Alembic and the container entrypoint. Migrations… (+2 more)

### Community 193 - "10. Implementation slices, acceptance criteria, tests, limitations"
Cohesion: 0.18
Nodes (11): 10.2 Test requirements (what "done" means per slice), 10.3.1 Approved decisions (previously open), 10.3.2 Known limitations (accepted, not blockers), 10.3.3 Open items and what they block now, 10.3 Decisions and known limitations, 10.4 Reserved-operation-type lists — one source of truth (required consolidation), 10.5.1 Migration (one, additive, `down_revision = c8d9e0f1a2b3`), 10.5.4 What each later step adds (and where it stays out of scope) (+3 more)

### Community 194 - "config.py"
Cohesion: 0.23
Nodes (12): fail_on_bad_config(), Central configuration. All runtime configuration flows through this module so…, Exit immediately with a readable message if configuration is invalid. Also…, _app_for_environment(), MonkeyPatch, ENVIRONMENT gating contract: docs exposure and HSTS (see .env.example).…, create_app() with get_settings() patched to the given environment., test_non_production_does_not_emit_hsts() (+4 more)

### Community 195 - "dek_envelope.py"
Cohesion: 0.11
Nodes (38): current_scope(), ``'org'``, ``'system'`` or ``'unset'``., _claim_first_dek(), _context(), _load(), _load_envelope(), org_dek_context(), _organization_exists() (+30 more)

### Community 196 - "certificate_service.py"
Cohesion: 0.10
Nodes (41): Certificate, One requested certificate: an identity, its lifecycle view, no material., CertificateChallengeType, CertificateKeyAlgorithm, How ownership of an identifier is proved to the CA. DNS-01 only in v1: it is…, The key type generated for a generation. Fixed in v1; never client-chosen., _actor(), all_generations() (+33 more)

### Community 197 - "test_certificate_order.py"
Cohesion: 0.12
Nodes (42): AcmeChallenge, One ``dns-01`` challenge, resolved to what has to be published. Every field is…, challenge_ref(), entries(), pending_cleanup(), Write *document* back onto the generation and return what was written. A JSON-…, Every challenge entry in *document*, in order, shape-checked. A challenge URL…, Record the order this attempt is working on. Called before any challenge. Once… (+34 more)

### Community 198 - "20261014_1200-a7b8c9d0e1f2_isolate_org_dek_envelopes.py"
Cohesion: 0.23
Nodes (11): downgrade(), _drop_constraint(), _drop_tenant_policies(), _grant(), Phase 5.2.1.2 — the organization DEK envelope gets a tenant table of its own.…, Grant the app role the four DML verbs on *table*. Not ownership, and not…, Restore the envelope onto ``organizations`` — without losing any of it., Raw ``ALTER TABLE ... DROP CONSTRAINT``, as the tenancy migration does.… (+3 more)

### Community 199 - "20261010_1200-f4a5b6c7d8e9_phase4_domains_and_routes.py"
Cohesion: 0.31
Nodes (9): downgrade(), _drop_tenant_policies(), _grant(), _in_list(), Phase 4 — domains, routes and the routing schema. Adds, in one migration with a…, Grant the app role on *table*; the migration role GUC carries the name. The…, The two-policy shape every tenant table uses: tenant + system scope., _tenant_policies() (+1 more)

### Community 200 - "certificate_order.py"
Cohesion: 0.09
Nodes (40): attempt_in_flight(), begin_attempt(), challenge(), current_entries(), finish_attempt(), _instant(), manual_instructions(), manual_pending() (+32 more)

### Community 201 - "NotificationChannel"
Cohesion: 0.20
Nodes (19): NotificationChannel, A delivery target (email address / webhook endpoint). ``config_ciphertext``…, EmailConfig, WebhookConfig, _audit(), create_channel(), decrypt_channel_config(), delete_channel() (+11 more)

### Community 202 - "StepLine"
Cohesion: 0.10
Nodes (23): LogLevel, _commit_short(), DeploymentRunner, _pace(), Protocol, Deployment runner port plus a faithful simulated implementation.…, Stream output lines for *step_name*; raise StepFailure to fail it., Deterministic per-line delay between 0.05s and 0.35s. (+15 more)

### Community 203 - "ProxyProvider"
Cohesion: 0.33
Nodes (5): ProxyProvider, Any, Protocol, What ``app.services.proxy_service`` is allowed to assume about a provider. The…, 11. Post-deploy hooks

### Community 204 - "_LibrarySession"
Cohesion: 0.10
Nodes (21): AcmeProtocolError, The response was not a well-formed ACME answer. A missing ``Location`` on an…, _execute(), _LibrarySession, _call(), _call(), _call(), _call() (+13 more)

### Community 205 - "incidents.py"
Cohesion: 0.14
Nodes (31): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+23 more)

### Community 206 - "test_agent_ingestion.py"
Cohesion: 0.30
Nodes (10): _enrolled(), _heartbeat(), Agent ingest pipeline: hello, heartbeat, staleness transitions, events., A container absent from a later heartbeat is gone from the daemon., A payload at the agent's cap may be truncated — absence proves nothing., test_heartbeat_at_container_cap_skips_reconciliation(), test_heartbeat_removes_vanished_containers(), test_heartbeat_updates_status_metrics_and_containers() (+2 more)

### Community 207 - ".dispatch"
Cohesion: 0.60
Nodes (3): Request, Response, RequestResponseEndpoint

### Community 208 - "Hub"
Cohesion: 0.13
Nodes (18): _close_socket(), Connection, _frame_org(), Hub, _params_key(), _parse_payload(), Any, WebSocket (+10 more)

### Community 209 - "notification_sender.py"
Cohesion: 0.17
Nodes (15): NotificationError, Any, BaseException, Exception, Low-level notification transports: SMTP email and outgoing webhooks. These…, POST *payload* as JSON to *url*; 2xx is success, anything else raises. Response…, Raised when a delivery attempt fails. Message is safe to persist., Bounded, single-line, content-free error reason. (+7 more)

### Community 210 - "certificate_issuance.py"
Cohesion: 0.12
Nodes (28): Map a system event type to the alert severity it deserves., severity_for_event(), _actor(), enqueue_generation(), _enqueue_issuance(), _flush_and_checkpoint(), issue_generation(), _publish_failure() (+20 more)

### Community 211 - "20261014_1600-b8c9d0e1f2a3_phase522_providers_acme_material.py"
Cohesion: 0.21
Nodes (14): _assert_no_material(), downgrade(), _drop_constraint(), _drop_tenant_policies(), _grant(), _in_list(), Phase 5.2.2 — DNS credentials, ACME accounts, and the certificate material…, Raw ``ALTER TABLE ... DROP CONSTRAINT IF EXISTS``. ``op.drop_constraint`` is… (+6 more)

### Community 212 - "SystemEvent"
Cohesion: 0.33
Nodes (10): NotificationDelivery, SystemEvent, _channel(), _delivery(), UUID, Notification channel + delivery-log endpoints. Regression coverage for GET…, The same event frame consumed twice queues ONE delivery per channel. Every API…, test_dispatch_frame_is_idempotent_across_workers() (+2 more)

### Community 213 - "_FakeAsyncClient"
Cohesion: 0.22
Nodes (3): _FakeAsyncClient, _FakeRequestObj, Scripted httpx.AsyncClient: responses keyed by absolute request URL.

### Community 214 - "ChannelType"
Cohesion: 0.38
Nodes (5): ChannelType, ChannelBase, ChannelCreate, ChannelUpdate, model_validator

### Community 215 - "test_migration_drift.py"
Cohesion: 0.15
Nodes (11): alembic_autogenerate, alembic_migration, The operator-facing one-liner stored in ``last_error``. Bounded., test_both_new_tables_carry_a_tenant_and_a_system_policy(), Model / migration drift: the schema in the database must match the models.…, ``Base.metadata`` and the migrated database must describe the same schema., The DB whitelist and ``OperationType`` are the same closed set. The migration…, test_models_and_migrations_do_not_drift() (+3 more)

### Community 216 - "README.md - NexusOps overview"
Cohesion: 0.37
Nodes (12): docker-compose.dev.yml - dev overlay, docker-compose.docker-sock.yml - docker socket override, docker-compose.yml - full stack definition, docs/agent.md - agent guide, docs/api.md - API guide, docs/architecture.md - system architecture, docs/deployment.md - deployment and operations guide, docs/development.md - developer guide (+4 more)

### Community 217 - "create_api_key"
Cohesion: 0.16
Nodes (17): create_api_key(), list_api_keys(), CurrentUser, DbSessionDep, delete, get, post, Request (+9 more)

### Community 218 - "test_dns_propagation.py"
Cohesion: 0.13
Nodes (26): evaluate(), Fold one round of observations into ``(ok, status, detail)``. **Pure.** ``ok``…, Poll the authoritative servers until every value is visible, or the deadline.…, wait_for_txt_records(), _Clock, _ok(), MonkeyPatch, parametrize (+18 more)

### Community 220 - "Platform Vision — NexusOps"
Cohesion: 0.20
Nodes (10): 1. Where NexusOps is today, 2.1 What we are NOT building, 2.2 The wedge (differentiation), 2. The direction, 3. Guiding principles, 4. Customer journey (target), 5.1 Architecture overview (target), 5. Control plane / data plane boundary (+2 more)

### Community 221 - "list_domains"
Cohesion: 0.15
Nodes (29): create_domain(), delete_domain(), _enqueue_verification(), get_domain(), list_domain_routes(), list_domains(), _project_names(), alias (+21 more)

### Community 222 - "CloudflareDnsProvider"
Cohesion: 0.11
Nodes (18): _Ambiguous, CloudflareDnsProvider, BaseException, Exception, Response, A bounded, credential-free description of a failed call., Verify the token and list the zones it can reach. Never raises for a provider-…, Find the zone that actually holds *name*. Walking suffixes deepest-first and… (+10 more)

### Community 223 - "CertificateGenerationState"
Cohesion: 0.06
Nodes (60): CertificateGenerationState, Lifecycle of one ACME order + key pair, pre- and post-issuance. **Phase 5.1…, The states in which a generation is still being worked on. At most one of these…, The states whose rows must carry key material and a DEK generation. The…, IssuanceAttempt, Why this call will not attempt, or ``None`` when it should. Checked before the…, What one call to :func:`issue_generation` did. Never carries material. ``code``…, _refusal() (+52 more)

### Community 224 - "next_attempt_at"
Cohesion: 0.38
Nodes (7): attempt_delay_seconds(), next_attempt_at(), datetime, Exponential backoff after *attempt_count* spent attempts, capped at 24h., When the next attempt on a generation becomes due., _utcnow(), test_backoff_grows_and_is_capped()

### Community 225 - "acme_account_service.py"
Cohesion: 0.10
Nodes (26): AcmeAccount, One ACME account: its directory, its CA-side URL, and its wrapped key., account_key(), AcmeAccountKeyUnavailable, _actor(), generate_account_key(), mark_used(), Any (+18 more)

### Community 226 - "NexusOps — Phase 1 (Multi-Tenancy) Report"
Cohesion: 0.29
Nodes (7): OperationSpec, Everything the control plane needs to know about one operation type.…, 1. What Phase 1 delivered, 4. Operations framework (added in this pass), 5. Tests, 8. Position, NexusOps — Phase 1 (Multi-Tenancy) Report

### Community 227 - "cloudflare"
Cohesion: 0.25
Nodes (6): cloudflare(), _FakeCloudflare, fixture, MonkeyPatch, Every test in this module gets the fake, and no test can reach the network., The credential seam: a verdict plus the zones the token can see.

### Community 228 - "record"
Cohesion: 0.12
Nodes (29): Any, AsyncSession, Request, UUID, Append an audit row using the caller's transaction (no commit here). The…, record(), add_member(), create_organization() (+21 more)

### Community 229 - "_validate_bundle"
Cohesion: 0.40
Nodes (5): _allowed_bundle_path(), The bundle fingerprint — byte-identical to the control plane's algorithm.…, Independently validate a bundle. Anything unexpected is refused., _tree_fingerprint(), _validate_bundle()

### Community 230 - "2. Entities"
Cohesion: 0.25
Nodes (8): 2.1.1 ApiKey org binding detail, 2.2.1 Environment promotion detail — **shipped in Phase 2**, 2.2 Delivery (existing models, extended), 2.4 Routing & TLS (new subsystem), 2.5 Secrets (re-scoped — **shipped in Phase 2**), 2.6 Observability (existing, org-scoped via parents), 2.7 Backups, connections, billing (new subsystems, design-only in early phases), 2. Entities

### Community 231 - "register_exception_handlers"
Cohesion: 0.36
Nodes (8): _error_payload(), FastAPI, Request, register_exception_handlers(), handle_app_error(), handle_http_exception(), handle_unexpected(), handle_validation_error()

### Community 233 - "servers.py"
Cohesion: 0.13
Nodes (28): apply_node_proxy_config(), create_enrollment_token(), create_server(), _enrollment_created(), _enrollment_out(), post, Request, Node endpoints: CRUD, tags, agent enrollment tokens. The domain entity is the… (+20 more)

### Community 234 - "hub.py"
Cohesion: 0.13
Nodes (25): membership_for_org(), Membership, The user's active membership in *org_id*, if any. This single indexed read is…, AppError, Exception, Base class for expected, client-facing errors., _authenticate_api_key(), _authenticate_jwt() (+17 more)

### Community 235 - "AcmeSession"
Cohesion: 0.09
Nodes (18): AbstractAsyncContextManager, AcmeProvider, AcmeSession, Protocol, One attempt's conversation with a CA, for one account. Method calls are…, Register (or discover) this account and return its CA-side URL (``kid``)., Tell the CA a challenge is ready to be validated., Drop the account key and any transport state this session held. (+10 more)

### Community 236 - "agent_heartbeat"
Cohesion: 0.15
Nodes (20): agent_enroll(), agent_heartbeat(), agent_hello(), claim_operation(), _presented_token(), DbDep, post, Request (+12 more)

### Community 237 - "projects.py"
Cohesion: 0.13
Nodes (43): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+35 more)

### Community 238 - "RealDockerProvider"
Cohesion: 0.17
Nodes (5): T, Execute an SDK call with one short retry, normalizing failures., Two short samples give real cpu/net deltas without streaming., Talks to a real docker daemon over ``unix://`` or ``tcp://``., RealDockerProvider

### Community 239 - "AcmeOrder"
Cohesion: 0.11
Nodes (9): AcmeOrder, IssuedChain, A fresh order and its authorizations, as public data., What finalization returned: PEM chain text plus nothing else. The chain is…, Create an order for *identifiers* and return its authorizations., Finalize the current order and download the issued chain., _FakeAcme, The CA side of the seam, honest about the two outcomes that matter here. (+1 more)

### Community 240 - "CredentialCheck"
Cohesion: 0.12
Nodes (16): CredentialCheck, DnsCredentialProvider, Protocol, What a verification attempt learned. Never carries the credential. ``ok`` is…, One DNS API, seen from the control plane's credential side., cloudflare(), _dns_stub(), _fake_observe() (+8 more)

### Community 241 - "instant_pacing"
Cohesion: 0.40
Nodes (4): instant_pacing(), fixture, MonkeyPatch, Remove the per-line sleeps; pacing bounds are asserted separately.

### Community 245 - "DnsCredentialUnavailable"
Cohesion: 0.50
Nodes (3): DnsCredentialUnavailable, RuntimeError, The stored credential cannot be read right now. One cause matters and is named…

### Community 246 - "_nginx_bootstrap"
Cohesion: 0.16
Nodes (16): _insert_http_includes(), _nginx_bootstrap(), _nginx_config_test(), _nginx_failure_summary(), _nginx_running(), _pid_alive(), Reload nginx via ``-s reload``, falling back to a SIGHUP of the master., Idempotent, minimal, reversible hook-up of the managed include. The only change… (+8 more)

### Community 247 - ".__init__"
Cohesion: 0.12
Nodes (8): _FailingRewrapProvider, _OverlappingProvider, _PingPongProvider, Fails *only* ``rewrap_dek`` — a rotation that cannot reach its provider. The…, The deterministic provider with a real await point inside ``wrap_dek``. Without…, Holds one rewrap result open until the test releases it. The result is computed…, Hands control back to the test before every one of the first ``rounds`` rewrap…, _StaleSnapshotProvider

### Community 248 - "TxtObservation"
Cohesion: 0.18
Nodes (13): observe(), _observer_name(), observer_window(), Has the challenge record actually reached the authoritative nameservers?…, Whether any unsatisfied observation is inconclusive rather than absent., One round: observe every expected name. Returns the round and its elapsed time., Call *observer* for *name*, converting an unexpected exception into an…, _still_changing() (+5 more)

### Community 249 - "EnvironmentUpdate"
Cohesion: 0.15
Nodes (11): EnvironmentCreate, EnvironmentUpdate, _normalise_environment_type(), field_validator, Payload to create an environment under a project., Partial environment update; omitted fields are left untouched. Config is…, ProjectCreate, ProjectUpdate (+3 more)

### Community 250 - "20260922_1000-a3f1c8d24b6e_add_tenancy_foundation.py"
Cohesion: 0.20
Nodes (12): _app_role_credentials(), _assert_fully_backfilled(), _backfill_org_ids(), _drop_constraint(), add tenancy foundation Phase 1 of the platform roadmap: organizations,…, Carry a value into a PL/pgSQL block. ``CREATE ROLE``/``ALTER ROLE`` are utility…, Application role name/password from settings (never hard-coded)., Point every pre-existing row at the bootstrap organization. ``audit_logs`` is… (+4 more)

### Community 251 - "require_server"
Cohesion: 0.15
Nodes (14): Resolve ``X-Agent-Token`` to the node it identifies, inside its own org. The…, require_server(), 1. Scope and current state, 4.1 CodenamesPhase 5 adds the two codenames already listed in authorization.md §2 — they are **not**, 4.2 Per-type permission and capability gating, 4.3 Tenant isolation, 4.4 Route → certificate binding at write time, 4. Authorization and tenant isolation (+6 more)

### Community 252 - "test_event_registry.py"
Cohesion: 0.21
Nodes (8): event_type_catalogue(), is_known_event_type(), Canonical registry of system-event types. Single source of truth shared by…, Return True when *event_type* is part of the canonical registry., Serialise the registry for the ``/events/types`` endpoint., Registry coherence: schema-advertised event types must equal the canonical…, test_catalogue_serialises_every_entry(), test_known_event_lookup()

### Community 253 - "update_server"
Cohesion: 0.17
Nodes (12): patch, Create a tag or update its colour (idempotent on name)., Apply a partial update; ``tags`` replaces the whole set when present., Rotate a node's credential with a bounded dual-token grace window. The previous…, rotate_agent_token(), update_server(), upsert_tag(), EnrollTokenOut (+4 more)

### Community 254 - "list_sessions"
Cohesion: 0.20
Nodes (11): list_sessions(), CurrentUser, DbSessionDep, delete, get, Request, UUID, Active sessions of this organization's members. Defaults to the caller's own;… (+3 more)

### Community 255 - "ContainerStats"
Cohesion: 0.22
Nodes (6): ContainerStats, Point-in-time resource usage snapshot., Any, Plausible numbers derived from the row plus time-based sine noise., _seed_int(), test_seed_int_is_deterministic_and_spread()

### Community 256 - "dispatch_event_frame"
Cohesion: 0.22
Nodes (11): _as_uuid(), dispatch_event_frame(), dispatcher_loop(), Any, Render an event frame into an ASCII-safe ``(subject, body)`` pair., Queue an event frame to every subscribed enabled channel; send immediately.…, Consume ``nx:events`` and sweep due retries forever. Runs as a lifespan task., render_frame() (+3 more)

### Community 257 - "search"
Cohesion: 0.20
Nodes (10): CurrentUser, DbSessionDep, get, max_length, min_length, Query, Permission-filtered multi-entity search for the command palette., search() (+2 more)

### Community 258 - "AuthorizationState"
Cohesion: 0.20
Nodes (5): AuthorizationState, One authorization's status after a poll., Poll one authorization until it is not ``pending``, or the deadline passes., Poll until the authorization leaves ``pending``, or the deadline passes. The…, test_authorization_state_status_predicates()

### Community 259 - "PayloadContext"
Cohesion: 0.27
Nodes (8): decrypt_str(), PayloadContext, What a ciphertext belongs to: organization, purpose, record and DEK generation.…, The canonical header string, used both outside and inside the token., :func:`decrypt` for the UTF-8 payloads (credentials, keys, chains)., Purpose, record and generation are all part of what the ciphertext belongs to.…, test_a_key_presented_under_another_context_is_refused(), read()

### Community 260 - "tasks/certificates.py"
Cohesion: 0.24
Nodes (9): issue_certificate(), _order_ttl_seconds(), task, Certificate issuance tasks: one worker per generation, plus the due sweep. The…, Dispatch every generation that is due an attempt — including abandoned ones.…, The order TTL from settings — the same one the service ages attempts with., Run at most one issuance attempt for one generation. The id is the only thing…, sweep_certificates() (+1 more)

### Community 261 - "test_migration_phase21.py"
Cohesion: 0.22
Nodes (9): Phase 2.1 corrective migration: legacy ``environment_type`` classification.…, Every case is classified as documented, ids and ownership intact., An explicit non-DEV classification survives the corrective migration. The…, The correction is part of ``head`` and adds no extra Alembic head., Insert one legacy environment per case, in two organizations., _seed_typed_environments(), test_corrective_migration_is_reachable_from_head(), test_corrects_legacy_environment_types() (+1 more)

### Community 262 - "test_monitors_incidents.py"
Cohesion: 0.27
Nodes (9): _create_monitor(), Monitor checks driving the full down -> incident -> recovery lifecycle., Regression: probe headers and URL query credentials never leave the API. Probe…, A monitor's checks, incidents and timeline all live in its organization, so the…, test_check_now_endpoint_runs_immediately(), test_down_then_recover_lifecycle(), test_metadata_endpoint_and_private_target_blocked(), test_monitor_responses_mask_probe_credentials() (+1 more)

### Community 263 - "AuditLogPage.test.tsx"
Cohesion: 0.20
Nodes (5): AuditEntry, AuditLogPage(), formatTimestamp(), shortId(), mockedGet

### Community 264 - "20261016_1000-c9d0e1f2a3b4_phase53_generation_directory.py"
Cohesion: 0.28
Nodes (7): _assert_no_directory_recorded(), downgrade(), _drop_constraint(), Phase 5.3 — the issuance provenance pair on ``certificate_generations``. Adds,…, Remove the provenance pair — refusing while any generation records a directory., Raw ``ALTER TABLE ... DROP CONSTRAINT IF EXISTS`` (see the 5.2.2 migration)., Refuse a downgrade that would discard which CA a generation was ordered at.

### Community 265 - "ContainerInfo"
Cohesion: 0.28
Nodes (4): ContainerInfo, List containers visible to the provider., Inspect a single container by id (short ids allowed)., Normalized view of a container as reported by any provider.

### Community 266 - "scope_matches"
Cohesion: 0.25
Nodes (7): Check an API-key scope list against a required permission. Supports exact match…, scope_matches(), parametrize, test_scope_matches_truth_table(), 1. Principles (already true in the codebase, kept), 5. API keys, 2.1 Identity & tenancy (new)

### Community 267 - "Domain Model — NexusOps as a Multi-Tenant Platform"
Cohesion: 0.25
Nodes (8): org_id_column(), A plain ``org_id`` column for the few tables that carry one without taking part…, 0.1 Shipped tenant layer (Phase 1), 0. Design stance, 1.1 ER diagram, 1. The hierarchy, 3. Cross-cutting decisions, Domain Model — NexusOps as a Multi-Tenant Platform

### Community 268 - "Authorization Architecture"
Cohesion: 0.25
Nodes (8): 0. What shipped (Phase 1), 2. Registry changes (Phase 1 + new subsystems), 3. The five system roles (target), 4. Grants (resource-level access; design now, later phase), 6. Enforcement mechanics (unchanged patterns, one addition), 7. Custom roles (later phase), 8. Permission-change audit, Authorization Architecture

### Community 269 - "6. Private-key encryption and key management"
Cohesion: 0.25
Nodes (8): 6.1 Threat model — what each envelope actually protects against, 6.2 Recommended v1 design, 6.3 Rotation, 6.4 No secret-store migration (explicit scope boundary), 6.5 Backups, recovery, and consequences of key loss, 6.6 Production-readiness requirements for centralized custody (conditions of §1.5), 6.8 Decisions closed here, and what remains an operator choice, 6. Private-key encryption and key management

### Community 270 - "list_audit_logs"
Cohesion: 0.29
Nodes (7): list_audit_logs(), datetime, DbSession, Depends, get, PageParamsDep, Newest-first audit trail with optional filters. No write routes exist for this…

### Community 271 - "permissions.py"
Cohesion: 0.29
Nodes (5): permission_exists(), PermissionSpec, Permission registry and role matrix. Permissions are *data*: the registry below…, test_permission_exists_helper(), fnmatch

### Community 272 - "TxtExpectation"
Cohesion: 0.29
Nodes (5): The expected values absent from *observed*, in expectation order., One TXT record name and **every** value that must be present there. A set…, TxtExpectation, test_expectation_requires_a_name_and_a_value(), test_missing_from_strips_observed_values_and_keeps_expectation_order()

### Community 273 - "test_run_async_publishes_frames_scheduled_by_the_commit_hook"
Cohesion: 0.29
Nodes (5): _FakeDb, Stands in for an ``AsyncSession`` whose only job here is ``sync_session``. A…, The shape of a worker task whose last statement is a commit., test_run_async_publishes_frames_scheduled_by_the_commit_hook(), commit_then_return()

### Community 274 - "ContainerListPage.test.tsx"
Cohesion: 0.29
Nodes (3): ApiError, server, serversPage

### Community 275 - "strip_query"
Cohesion: 0.33
Nodes (4): Drop the query string so signed tokens never appear in error text., Public alias: redact any query string from a URL before display/persist., strip_query(), field_serializer

### Community 276 - "LoginPage.tsx"
Cohesion: 0.33
Nodes (4): LoginPage, FieldErrors, MetaInfo, redirectTarget()

### Community 277 - "_is_same_origin"
Cohesion: 0.40
Nodes (5): _is_same_origin(), Browsers always send Origin on WS handshakes, even same-origin ones. When it…, The proxy must forward the Host the browser actually used. A browser sends…, test_same_origin_compares_the_full_authority_including_port(), 7. Known limitations and unresolved issues

### Community 278 - "router.py"
Cohesion: 0.40
Nodes (4): websocket, WebSocket endpoint. Mounted by the app factory under ``/api/v1``., Hand the socket to the hub (auth handshake handled there)., websocket_endpoint()

### Community 279 - "_FakeCtx"
Cohesion: 0.40
Nodes (3): _FakeCtx, Duck-typed stand-in for AuthContext., test_require_permission_returns_ctx_when_allowed()

### Community 280 - ".route_file_path"
Cohesion: 0.50
Nodes (3): Where a route's fragment lands, so the service can name it in events., A deterministic, filesystem-safe fragment name for one route., _route_key()

### Community 281 - "PropagationResult"
Cohesion: 0.50
Nodes (3): PropagationResult, What the authoritative servers said about a set of expectations. ``observed``…, The record names whose expectation is not satisfied yet.

### Community 282 - "test_remove_honours_force_and_never_shells"
Cohesion: 0.50
Nodes (3): test_container_start_maps_to_a_fixed_api_call(), fake_raw(), test_remove_honours_force_and_never_shells()

### Community 283 - "stable_json"
Cohesion: 0.67
Nodes (3): Any, Canonical JSON for fingerprint-adjacent comparisons in tests., stable_json()

## Knowledge Gaps
- **486 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+481 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 3031 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `6. Tooling: reproducible e2e` connect `apply_scope_to_session` to `NexusOps — Phase 1 (Multi-Tenancy) Report`, `hub.py`, `client.ts`, `_is_same_origin`, `NotFound`, `auth_service.py`?**
  _High betweenness centrality (0.195) - this node is a cross-community bridge._
- **Why does `useEventStream()` connect `client.ts` to `apiGet`, `App.tsx`, `AuthContext.tsx`, `ServerDetailPage.tsx`, `@tanstack/react-query`, `apply_scope_to_session`?**
  _High betweenness centrality (0.193) - this node is a cross-community bridge._
- **Why does `TenancyScopeError` connect `apply_scope_to_session` to `AuthContext`, `test_certificates.py`, `dek_envelope.py`, `publish`, `test_org_dek_envelope.py`, `core/tenancy.py`, `assert_error_code`, `enums.py`, `test_acme_accounts.py`, `enrollment_service.py`, `server_service.py`, `test_tenant_isolation.py`?**
  _High betweenness centrality (0.100) - this node is a cross-community bridge._
- **Are the 107 inferred relationships involving `AuthContext` (e.g. with `TenancyScopeError` and `MembershipStatus`) actually correct?**
  _`AuthContext` has 107 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `APIModel` (e.g. with `OperationSpec` and `test_specs_reject_unknown_params()`) actually correct?**
  _`APIModel` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `meta`, `SCHEMA`, `RESEARCH_COMMON` to the rest of the system?**
  _486 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `apiGet` be split into smaller, more focused modules?**
  _Cohesion score 0.057002457002457 - nodes in this community are weakly interconnected._