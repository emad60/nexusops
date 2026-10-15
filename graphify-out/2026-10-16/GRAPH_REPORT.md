# Graph Report - nexusops  (2026-10-14)

## Corpus Check
- 394 files · ~472,845 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: (none) 10, .example 1, .service 1)

## Summary
- 7110 nodes · 20871 edges · 249 communities (227 shown, 22 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1673 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6dfa0b92`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- apiGet
- test_certificates.py
- ApiKeysPage.tsx
- _verified_domain
- container_service.py
- package.json
- resolve_client_ip
- OperationType
- App.tsx
- test_agent_v2.py
- assert_error_code
- ServerDetailPage.tsx
- uuid
- client.ts
- validate_config
- certificate_service.py
- deployment_engine.py
- SimulatedDockerProvider
- enrollment_service.py
- secret_service.py
- test_deployments_simulated.py
- list_containers
- metrics_service.py
- get_settings
- Domain Routing — NexusOps
- monitor_service.py
- Product Roadmap — NexusOps Multi-Tenant Platform
- test_agent_backoff.py
- SimulatedDeploymentRunner
- nexusops_agent.py
- integration/conftest.py
- auth_service.py
- docker_host_service.py
- test_rate_limit.py
- docker_hosts.py
- AppError
- schemas/proxy.py
- v1/search.py
- models/__init__.py
- list_deliveries
- DockerProvider
- test_monitor_transport.py
- test_migration_phase5212.py
- AuthContext.tsx
- record
- test_permissions.py
- kek/health.py
- test_phase3_nodes.py
- UnprocessableEntity
- Hub
- role.py
- servers.py
- proxy_service.py
- WrappedKey
- organization.py
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
- route_service.py
- monitor.py
- server_service.py
- Certificate Management — NexusOps
- seed.py
- core/tenancy.py
- test_secrets.py
- test_nginx_renderer.py
- domain_service.py
- api service (FastAPI / uvicorn :8000)
- MonitorOut
- enums.py
- test_acme_accounts.py
- incident_service.py
- test_phase2_secrets.py
- RolesPage.tsx
- test_schemas_server.py
- InvalidName
- tests/conftest.py
- log_service.py
- NotFound
- devDependencies
- Conflict
- test_certificate_lifecycle.py
- test_payload_crypto.py
- DomainStatus
- dns_provider_service.py
- mark_all_read
- apply_scope_to_session
- test_phase21_secret_version_integrity.py
- Server
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- journey.spec.ts
- test_org_dek_envelope.py
- redact_mapping
- DeterministicKEKProvider
- test_phase4_routing.py
- Path
- test_migration_phase4.py
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- test_migration_phase5.py
- docker_real.py
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- routes.py
- organization_service.py
- 1. Architecture and trust boundaries
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
- dns_providers.py
- install.sh
- docker-entrypoint.sh
- integration/__init__.py
- DockerHostsPage.test.tsx
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
- rollback_secret
- nexusops-challenge.mjs
- Secrets Architecture
- test_schemas_agent.py
- .state
- test_kek_vault_transit_live.py
- alert_service.py
- decide
- RouteHeader
- AgentClient
- test_kek_selection.py
- nginx.py
- AuthContext
- TxtObservation
- pytest
- test_agent_contract.py
- test_kek_vault_transit.py
- monitor_transport.py
- Container
- APIModel
- readiness
- Platform Security Model — NexusOps
- Node & Agent Architecture
- main
- _node_session
- server.py
- _nginx_apply
- _rows
- events.py
- 1. Scope and current state
- 20261012_1200-c8d9e0f1a2b3_phase5_certificate_metadata.py
- run_async
- get_latest_server_metrics
- Deployment Architecture — NexusOps (target state)
- phase3.spec.ts
- Settings
- is_retryable
- env.py
- 10. Implementation slices, acceptance criteria, tests, limitations
- test_ws_hub.py
- dek_envelope.py
- container.py
- CheckResult
- 20261014_1200-a7b8c9d0e1f2_isolate_org_dek_envelopes.py
- 20261010_1200-f4a5b6c7d8e9_phase4_domains_and_routes.py
- CertificateGenerationState
- NotificationChannel
- scope_matches
- ProxyProvider
- _removal_audits
- Multi-Tenancy Architecture
- test_agent_ingestion.py
- AuditLogPage.test.tsx
- resolve_secrets_for_environment
- notification_sender.py
- UpstreamContainerOut
- 20261014_1600-b8c9d0e1f2a3_phase522_providers_acme_material.py
- SystemEvent
- _FakeAsyncClient
- channel.py
- test_migration_drift.py
- README.md - NexusOps overview
- paginate
- ContainerListPage.test.tsx
- docs/engineering-report.md - build and verification report
- Platform Vision — NexusOps
- 20261009_1100-d4e5f6a7b8c9_correct_legacy_environment_types.py
- CloudflareDnsProvider
- assert_state
- certificate_lifecycle.py
- UnrepresentableState
- LoginPage.tsx
- cloudflare
- get_meta
- _live_bundle_id
- 2. Entities
- register_exception_handlers
- 6. Private-key encryption and key management
- apply_node_proxy_config
- 20261009_1300-a1b2c3d4e5f6_add_phase3_nodes_and_agent_v2.py
- websocket_endpoint
- v1/agent.py
- MonitorTargetType
- 4. Authorization and tenant isolation
- network_rates
- material_guard_predicate
- instant_pacing
- .__tablename__
- ApplicationBase
- .apply_params
- DnsCredentialUnavailable
- mark_stale_servers
- .__init__
- _FakeSession

## God Nodes (most connected - your core abstractions)
1. `AuthContext` - 172 edges
2. `APIModel` - 151 edges
3. `get_settings()` - 101 edges
4. `record()` - 98 edges
5. `Server` - 93 edges
6. `apiGet()` - 91 edges
7. `NotFound` - 90 edges
8. `Conflict` - 80 edges
9. `publish()` - 78 edges
10. `assert_error_code()` - 77 edges

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

## Communities (249 total, 22 thin omitted)

### Community 0 - "apiGet"
Cohesion: 0.06
Nodes (90): apiDelete(), apiGet(), apiPatch(), apiPost(), ApplicationOut, ENVIRONMENT_TYPE_LABELS, EnvironmentType, IncidentEventOut (+82 more)

### Community 1 - "test_certificates.py"
Cohesion: 0.07
Nodes (58): error_of(), Unwrap an API error envelope., _app_role_dsn(), _audits(), _certificate_rows(), _create_domain(), _created_certificate(), _dns_stub() (+50 more)

### Community 2 - "ApiKeysPage.tsx"
Cohesion: 0.09
Nodes (19): ApiKeyOut, ApiKeysPage, ApiKeyCreatedOut, handleCopyKey(), copyText(), describeError(), EMPTY_FORM, GROUP_STYLE (+11 more)

### Community 3 - "_verified_domain"
Cohesion: 0.09
Nodes (58): ServerStatus, Keep every routed node's live configuration matching the desired bundle. One…, sweep_routes(), _candidates(), _run(), _converged_node_with_a_route(), _create_route(), _drain() (+50 more)

### Community 4 - "container_service.py"
Cohesion: 0.10
Nodes (37): clip(), Truncate *text* to *limit* characters, stripping control chars., describe_provider_error(), is_simulated(), provider_for(), Exception, Provider selection based on a docker host's endpoint URL. Mapping: *…, Return the provider matching *host*'s endpoint configuration. (+29 more)

### Community 5 - "package.json"
Cohesion: 0.13
Nodes (15): name, private, type, version, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom (+7 more)

### Community 6 - "resolve_client_ip"
Cohesion: 0.06
Nodes (50): ASGIApp, _is_trusted(), _parse_networks(), Request, Client-IP resolution behind chained reverse proxies. The API never takes TCP…, Parse a comma-separated CIDR list; malformed entries are skipped., Real client address for *request* per the trust model above., resolve_client_ip() (+42 more)

### Community 7 - "OperationType"
Cohesion: 0.13
Nodes (18): OperationType, The whitelist. Nothing outside this enum ships as an exec surface. Each type…, MonkeyPatch, The operation dispatch whitelist is a contract, not a convention.…, A type whose capability cannot be confirmed must not be dispatchable., The framework reuses existing codenames; a generic exec grant must not exist., Phase 4 ships exactly the three nginx ops, each gated on the capability. This…, Every params model must forbid extras, so nothing reaches the agent unseen. (+10 more)

### Community 8 - "App.tsx"
Cohesion: 0.04
Nodes (103): DeploymentOut, Page, ProjectOut, AlertsPage, App(), AuditLogPage, ContainerListPage, DeploymentListPage (+95 more)

### Community 9 - "test_agent_v2.py"
Cohesion: 0.08
Nodes (37): agent_fixture(), _load_agent(), Any, fixture, parametrize, Agent protocol v2: honest metrics, capability detection, and the executor. The…, Phase 4 shipped three nginx ops — no file primitive, no command primitive., Trusting a private CA must not weaken verification. (+29 more)

### Community 10 - "assert_error_code"
Cohesion: 0.06
Nodes (63): dispose_engine(), OperationSpec, Everything the control plane needs to know about one operation type.…, assert_error_code(), Assert envelope shape + code; returns the inner error object., Regression: lockout must not leak which emails exist. After login_max_attempts…, test_locked_account_response_is_indistinguishable(), Regression: mark_stale_servers ran under the system scope and added Alert rows… (+55 more)

### Community 11 - "ServerDetailPage.tsx"
Cohesion: 0.06
Nodes (42): ContainerOut, MetricPoint, ServerDetail, ServerSummary, ChartSeries, LineChart(), LineChartProps, PAD (+34 more)

### Community 12 - "uuid"
Cohesion: 0.07
Nodes (44): Agent-facing schemas. Payloads are data only — never executed. Wire protocol v2…, AlertOut, Schemas for operator-facing alerts., API key schemas. Raw keys appear exactly once, at creation., ApplicationSummary, Application API schemas., Application as embedded in project outputs (no deployment summary)., AuditOut (+36 more)

### Community 13 - "client.ts"
Cohesion: 0.05
Nodes (54): API_BASE, ApiError, apiRequest(), buildUrl(), extractError(), getAccessToken(), getActiveOrgId(), onActiveOrgChange() (+46 more)

### Community 14 - "validate_config"
Cohesion: 0.06
Nodes (34): EnvironmentBase, _normalise_environment_type(), field_validator, Shared environment fields., ProjectBase, field_validator, collect_secret_refs(), walk() (+26 more)

### Community 15 - "certificate_service.py"
Cohesion: 0.05
Nodes (78): create_certificate(), delete_certificate(), get_certificate(), list_certificates(), alias, AsyncSession, DbDep, delete (+70 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.11
Nodes (57): deployment_log_channel(), Deployment, DeploymentStep, AlertSeverity, DeploymentStatus, DeploymentTrigger, EventLevel, String enum; member names equal values so name/value storage never disagrees. (+49 more)

### Community 17 - "SimulatedDockerProvider"
Cohesion: 0.08
Nodes (35): ContainerStatus, LogEntry, DockerProviderError, A provider operation failed. ``str()`` is safe to show/log., Any, datetime, Simulated docker provider for demo and test environments. The provider is…, Plausible numbers derived from the row plus time-based sine noise. (+27 more)

### Community 18 - "enrollment_service.py"
Cohesion: 0.10
Nodes (33): generate_enrollment_token(), An enrollment credential (``nxk_``): single-use, short-lived, org-scoped.…, Return the active org id or raise; used by services that need it explicitly., require_org(), EnrollmentToken, One single-use credential that enrolls (or claims) exactly one node., Whether the row could still be redeemed (not a race-safe check)., EnrollmentTokenState (+25 more)

### Community 19 - "secret_service.py"
Cohesion: 0.10
Nodes (43): An encrypted configuration value, scoped to org, project or environment.…, One immutable value of a :class:`Secret` — append-only history. A row is…, Secret, SecretVersion, _actor_type(), _collect_refs(), create_secret(), delete_secret() (+35 more)

### Community 20 - "test_deployments_simulated.py"
Cohesion: 0.15
Nodes (28): execute_deployment(), Run one deployment to a terminal state. Never raises; safe to re-run., get_environment(), _as_worker(), _delivery_chain(), _owner_ctx(), _queue(), _queued_with_recorder() (+20 more)

### Community 21 - "list_containers"
Cohesion: 0.08
Nodes (43): _action_route(), _endpoint(), _decode_frame(), _ev(), get_container(), _like_pattern(), list_container_logs(), list_containers() (+35 more)

### Community 22 - "metrics_service.py"
Cohesion: 0.11
Nodes (31): MetricGranularity, MetricSnapshot, aggregate_rollups(), dashboard_summary(), ensure_server(), _extra_object(), granularity_for_range(), latest_for_servers() (+23 more)

### Community 23 - "get_settings"
Cohesion: 0.06
Nodes (62): argon2, argon2_exceptions, fail_on_bad_config(), get_settings(), Central configuration. All runtime configuration flows through this module so…, Return the cached settings singleton., Exit immediately with a readable message if configuration is invalid. Also…, get_engine() (+54 more)

### Community 24 - "Domain Routing — NexusOps"
Cohesion: 0.07
Nodes (28): The directory URL stored on the account row and recorded per issuance., 10. Wildcards and catch-all, 11. User journey, 12. API surface, permissions, audit, 13. Monitoring tie-in, 1. Scope and current state, 2. Where nginx runs, 3.1 Domain (+20 more)

### Community 25 - "monitor_service.py"
Cohesion: 0.16
Nodes (36): MonitorStatus, Monitor, One probe. Targets are polymorphic since Phase 4 (domain-model.md §2.6).…, _active_incident(), _audit(), claim_due_monitors(), create_monitor(), delete_monitor() (+28 more)

### Community 26 - "Product Roadmap — NexusOps Multi-Tenant Platform"
Cohesion: 0.10
Nodes (21): What one reported result did to its operation row. The caller's side effects —…, ResultTransition, 0. Stance, 10. Phase 7 — Teams, grants & custom roles — **proposal, not implemented**, 11. Phase 8 — Backups — **proposal, not implemented**, 12. Phase 9 — Billing & metering — **proposal, not implemented**, 13.1 Scope-creep gates — what must be true before each expansion, 13. First commercially meaningful version (+13 more)

### Community 27 - "test_agent_backoff.py"
Cohesion: 0.14
Nodes (22): agent_fixture(), _install_sleep(), fake_sleep(), _load_agent(), _patch_host(), Any, fixture, MonkeyPatch (+14 more)

### Community 28 - "SimulatedDeploymentRunner"
Cohesion: 0.12
Nodes (39): LogLevel, _commit_short(), _pace(), Exception, Deployment runner port plus a faithful simulated implementation.…, Stream output lines for *step_name*; raise StepFailure to fail it., Staged docker-style simulation used by v1 deployments., Deterministic per-line delay between 0.05s and 0.35s. (+31 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.08
Nodes (33): build_capabilities(), build_heartbeat(), collect_container_stats(), collect_containers(), _container_ports(), _container_status(), cpu_percent_since(), disk_stats() (+25 more)

### Community 30 - "integration/conftest.py"
Cohesion: 0.07
Nodes (30): alembic_config, close_redis(), _admin_dsn(), _clean_slate(), client(), _ensure_database(), _migrated_database(), org_db() (+22 more)

### Community 31 - "auth_service.py"
Cohesion: 0.09
Nodes (52): active_memberships(), The user's memberships in non-suspended organizations, oldest first. Reads only…, System scope bound to *db*, for rows that have no organization. Used by exactly…, system_write_scope(), AuditResult, UserStatus, Opaque refresh token; only its SHA-256 hash is stored. Rotation chain: on…, RefreshToken (+44 more)

### Community 32 - "docker_host_service.py"
Cohesion: 0.14
Nodes (33): DockerHostStatus, DockerHost, DockerHostPingOut, Result of probing a host's provider endpoint., _assert_endpoint_allowed(), _assert_name_free(), create_host(), delete_host() (+25 more)

### Community 33 - "test_rate_limit.py"
Cohesion: 0.13
Nodes (23): RateLimited, _enforce(), _memory_count_and_ttl(), node_rate_limit(), _dependency(), Request, rate_limit(), _dependency() (+15 more)

### Community 34 - "docker_hosts.py"
Cohesion: 0.07
Nodes (53): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+45 more)

### Community 35 - "AppError"
Cohesion: 0.20
Nodes (16): AppError, Exception, Base class for expected, client-facing errors., _authenticate_api_key(), _authenticate_jwt(), _bind_organization(), _load_permissions(), _org_id_from_frame() (+8 more)

### Community 36 - "schemas/proxy.py"
Cohesion: 0.10
Nodes (28): bundle_summary(), BundleFile, fingerprint_files(), is_allowed_bundle_path(), NginxBootstrapParams, NginxBundle, NginxStatusParams, Any (+20 more)

### Community 37 - "v1/search.py"
Cohesion: 0.12
Nodes (32): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+24 more)

### Community 38 - "models/__init__.py"
Cohesion: 0.08
Nodes (62): _org_scoped_classes(), Mapped classes marked :class:`~app.models.base.OrgScoped`. Reads the mapper…, The per-organization ACME account and its protected account key. One account…, Base, big_serial_pk(), json_column(), org_id_column(), OrgScoped (+54 more)

### Community 39 - "list_deliveries"
Cohesion: 0.15
Nodes (23): create_channel(), delete_channel(), get_channel(), list_deliveries(), DbDep, delete, Depends, get (+15 more)

### Community 40 - "DockerProvider"
Cohesion: 0.10
Nodes (10): DockerProvider, Any, Protocol, List containers visible to the provider., Inspect a single container by id (short ids allowed)., List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``., List volumes: keys ``name``, ``driver``, ``mountpoint``., List networks: keys ``name``, ``driver``, ``scope``. (+2 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.17
Nodes (24): coerce_headers(), Any, Deterministic fake checker for ``sim://`` monitors and demo environments.…, Normalise arbitrary JSON-ish header input into a plain str->str dict., SimulatedTransport, _check(), clock(), FakeClock (+16 more)

### Community 42 - "test_migration_phase5212.py"
Cohesion: 0.13
Nodes (25): _columns(), Phase 5.2.1.2 migration (`a7b8c9d0e1f2`): the envelope leaves…, ``column -> (data_type, is_nullable)`` for *table*., ``(org_id, ciphertext, generation)`` for every populated envelope, ordered., The move creates rows only where there was key material. A row with a NULL…, Two envelopes for one tenant are refused by the database, not by a service., F3: a negative generation, and either half of an inconsistent pair, fail. The…, RLS plus the grant: the policies are only load-bearing for a non-owner role.… (+17 more)

### Community 43 - "AuthContext.tsx"
Cohesion: 0.02
Nodes (83): Membership, SearchResult, User, AuthContext, AuthProvider(), AuthState, isOrgSelectionError(), MeResponse (+75 more)

### Community 44 - "record"
Cohesion: 0.06
Nodes (99): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+91 more)

### Community 45 - "test_permissions.py"
Cohesion: 0.10
Nodes (17): permission_exists(), PermissionSpec, Permission registry and role matrix. Permissions are *data*: the registry below…, _auth_context(), _FakeCtx, Unit tests for the permission registry, scope matching and RBAC gate., Duck-typed stand-in for AuthContext., A fake context in the given organization. ``membership_status=None`` models a… (+9 more)

### Community 46 - "kek/health.py"
Cohesion: 0.08
Nodes (26): Provider health, cached, for the readiness surface. Health is the one place a…, Drop every cached verdict (tests, and any future configuration reload)., reset_health_cache(), ProviderHealth, A provider's self-report. ``detail`` is sanitized: no tokens, no DSNs., Report operability without touching key material., _clear_health_cache(), fixture (+18 more)

### Community 47 - "test_phase3_nodes.py"
Cohesion: 0.14
Nodes (35): Run the enclosed block with tenant filtering off (maintenance only). ``reason``…, system_scope(), _create_token(), _dispatch(), _enroll(), _enrolled_node(), _load_agent_module(), _mutate_in_system_scope() (+27 more)

### Community 48 - "UnprocessableEntity"
Cohesion: 0.07
Nodes (63): BadRequest, UnprocessableEntity, assert_safe_tcp_endpoint(), assert_safe_url(), assert_safe_url_async(), _is_forbidden_address(), is_simulation_url(), ValueError (+55 more)

### Community 49 - "Hub"
Cohesion: 0.13
Nodes (18): _close_socket(), Connection, _frame_org(), Hub, _params_key(), _parse_payload(), Any, WebSocket (+10 more)

### Community 50 - "role.py"
Cohesion: 0.10
Nodes (28): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, delete, get (+20 more)

### Community 51 - "servers.py"
Cohesion: 0.08
Nodes (53): create_enrollment_token(), create_server(), delete_server(), _detail(), _enrollment_created(), _enrollment_out(), get_server(), list_enrollment_tokens() (+45 more)

### Community 52 - "proxy_service.py"
Cohesion: 0.06
Nodes (83): ListenerOwnership, ProxyApplyOutcome, Terminal outcome of one ``nginx.apply`` operation on a node., Who holds one required listener port, per the node's pre-flight. The…, NodeProxyCapabilityOut, NodeProxyStatusOut, The node's reported nginx capability, bounded to the useful facts., ``GET /nodes/{id}/proxy/status``. Reports what the node said and what the… (+75 more)

### Community 53 - "WrappedKey"
Cohesion: 0.06
Nodes (43): AsyncBaseTransport, _derive(), The deterministic in-process provider — tests and explicitly configured dev.…, A per-(binding, key version) key: HKDF-style derivation. Two properties, both…, KEKContextMismatchError, KEKEnvelopeError, KEKError, KEKUnauthorizedError (+35 more)

### Community 54 - "organization.py"
Cohesion: 0.11
Nodes (27): create_organization(), list_my_organizations(), CurrentUser, DbSessionDep, get, IdentityUser, patch, post (+19 more)

### Community 55 - "test_agent_nginx_contract.py"
Cohesion: 0.08
Nodes (51): _agent_bundle(), agent_fixture(), _bootstrap_fixture(), _load_agent(), Any, fixture, parametrize, Path (+43 more)

### Community 56 - "create_user"
Cohesion: 0.18
Nodes (15): create_user(), deactivate_user(), get_user(), CurrentUser, DbSessionDep, delete, get, patch (+7 more)

### Community 57 - "alembic"
Cohesion: 0.04
Nodes (27): alembic, downgrade(), rename ``server.*`` permission codenames to ``node.*`` The Node/Server…, _rename_permissions(), upgrade(), _quoted_list(), Add the operations framework table (node-agent-architecture.md §5). One tenant-…, upgrade() (+19 more)

### Community 58 - "notification_service.py"
Cohesion: 0.15
Nodes (27): DeliveryStatus, _as_uuid(), _attempt_delivery(), decode_delivery_cursor(), dispatch_event_frame(), _send(), dispatcher_loop(), encode_delivery_cursor() (+19 more)

### Community 59 - "helpers.py"
Cohesion: 0.07
Nodes (58): owner(), Bootstrap owner credentials for this test (fresh DB => first user). ``headers``…, bearer(), cookie_attributes(), login_account(), login_headers(), Any, AsyncClient (+50 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "_list_deployments"
Cohesion: 0.10
Nodes (36): _attribute_step_idx(), cancel_deployment(), _emails_for(), get_deployment(), list_application_deployments(), list_deployment_logs(), _list_deployments(), _parse_sort() (+28 more)

### Community 62 - "test_error_logging.py"
Cohesion: 0.22
Nodes (4): Regression: the catch-all 500 handler must not log raw exception text.…, _SpyLogger, test_unhandled_exception_handler_logs_class_not_message(), fastapi_testclient

### Community 63 - "dns_verifier.py"
Cohesion: 0.12
Nodes (19): apex_of(), The name a wildcard Domain is anchored at (``*.example.com`` →…, The exact TXT owner name a user must publish at their provider., verification_record_name(), _discover_nameservers(), _normalise_ns(), observe(), Observer (+11 more)

### Community 64 - "test_phase2_environments.py"
Cohesion: 0.18
Nodes (22): _environment(), _project(), parametrize, Phase 2: project-scoped environments, config layering, and their isolation. The…, Uniqueness is ``(project_id, slug)`` — not instance-wide., The update path is validated too (the pre-Phase-2 gap)., Knowing an environment UUID is not access: the project link must hold., Another tenant cannot reach the project, its environments, or its detail. (+14 more)

### Community 65 - "route_service.py"
Cohesion: 0.08
Nodes (58): AsyncSession, routes_for_domain(), Last nginx apply outcome for a route, as reported by its node's agent.…, How far a route's *removal* has got, which ``config_state`` cannot say. A route…, RouteConfigState, RouteRemovalState, One hostname+path served from one container on one node. Relationship rules the…, Route (+50 more)

### Community 66 - "monitor.py"
Cohesion: 0.11
Nodes (26): is_sensitive_header(), mask_sensitive_headers(), MonitorBase, MonitorCreate, MonitorSortField, MonitorUpdate, Schemas for uptime monitors and their check history., Whitelist of sortable columns exposed as query parameters. (+18 more)

### Community 67 - "server_service.py"
Cohesion: 0.06
Nodes (60): Canonical Redis pub/sub channel names shared by API, workers and WS hub., server_metrics_channel(), get_redis(), ping(), Shared async Redis client., ActorType, _after_commit_publish(), _after_rollback_drop() (+52 more)

### Community 68 - "Certificate Management — NexusOps"
Cohesion: 0.12
Nodes (16): 10. Status/expiry tracking and monitor tie-in, 11. Failure handling, 12. Audit and events, 13. Non-goals, 3. API surface and permissions, 4.1 DNS-01 first (the default and the wedge), 4.2 DNSProvider interface, 4.3 ACME account and directory (+8 more)

### Community 69 - "seed.py"
Cohesion: 0.15
Nodes (23): EnvironmentType, Kind of a project-scoped deployment environment (Phase 2). Descriptive only —…, Tag, Membership, Organization, Binds a user to an organization with a role *inside that organization*.…, A tenant. Every organization-owned row points here via ``org_id``., _lock() (+15 more)

### Community 70 - "core/tenancy.py"
Cohesion: 0.11
Nodes (30): _apply_scope_guc(), _desired_guc(), _guard(), _has_org_predicate(), install_tenancy_guards(), _mappers_of(), org_scoped_table_names(), Any (+22 more)

### Community 71 - "test_secrets.py"
Cohesion: 0.09
Nodes (30): decrypt_str(), encrypt_str(), _create_monitor(), Monitor checks driving the full down -> incident -> recovery lifecycle., Regression: probe headers and URL query credentials never leave the API. Probe…, A monitor's checks, incidents and timeline all live in its organization, so the…, test_check_now_endpoint_runs_immediately(), test_down_then_recover_lifecycle() (+22 more)

### Community 72 - "test_nginx_renderer.py"
Cohesion: 0.12
Nodes (38): NginxProvider, ValueError, The only production provider in Phase 4., Where a route's fragment lands, so the service can name it in events., Rendering refused the input. Always a bug or a corrupt row, never a leak., RenderError, NginxApplyParams, One validated bundle to apply atomically. (+30 more)

### Community 73 - "domain_service.py"
Cohesion: 0.06
Nodes (66): create_domain(), delete_domain(), _enqueue_verification(), get_domain(), list_domain_routes(), list_domains(), _project_names(), alias (+58 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "MonitorOut"
Cohesion: 0.16
Nodes (32): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+24 more)

### Community 76 - "enums.py"
Cohesion: 0.06
Nodes (87): permission_dep(), Any, FastAPI dependencies: database session, authenticated tenant context, RBAC…, Dependency factory enforcing a permission; returns 403 when denied., require_permission(), list_alerts(), Depends, Alert inbox endpoints. Authenticated users see the shared operator feed. (+79 more)

### Community 77 - "test_acme_accounts.py"
Cohesion: 0.06
Nodes (72): AcmeAccount, Which known directory this account is at; ``None`` when the URL is neither.…, One ACME account: its directory, its CA-side URL, and its wrapped key., AcmeDirectory, Which certificate authority a per-organization ACME account belongs to. A…, The directory a stored URL names, or ``None`` when it names neither. ``None``…, account_for(), account_key() (+64 more)

### Community 78 - "incident_service.py"
Cohesion: 0.11
Nodes (49): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+41 more)

### Community 79 - "test_phase2_secrets.py"
Cohesion: 0.19
Nodes (21): _env(), _project(), Phase 2 secrets: layered scope, immutable versions, rollback, isolation. Two…, Two racing rotations must both be kept and never share a version number., Another tenant cannot read, rotate, roll back or even enumerate the secret., The documented example: same key at three scopes; most specific wins., A ref declared in the project base config resolves for its environments., _resolved() (+13 more)

### Community 80 - "RolesPage.tsx"
Cohesion: 0.11
Nodes (15): Role, RolesPage, describeError(), GROUP_STYLE, LEGEND_STYLE, OPTION_STYLE, PermissionSpec, roleAllows() (+7 more)

### Community 81 - "test_schemas_server.py"
Cohesion: 0.21
Nodes (22): Payload for registering a server., Partial update. ``tags`` replaces the full set when provided., ServerCreate, ServerUpdate, _base(), parametrize, Unit tests for app.schemas.server (validation only, no I/O)., test_empty_ip_is_allowed_but_whitespace_collapses() (+14 more)

### Community 82 - "InvalidName"
Cohesion: 0.10
Nodes (42): _canonicalize(), canonicalize_name(), canonicalize_path(), canonicalize_record_name(), _check_labels(), _check_not_ip(), hostname_is_covered(), _idna() (+34 more)

### Community 83 - "tests/conftest.py"
Cohesion: 0.22
Nodes (7): configure_test_env(), Test bootstrap: pin every cached setting BEFORE the first ``app`` import. The…, KEY=VALUE pairs from the repo .env (first definition wins); never logged., Export the exact settings the app caches; host values cannot leak through., _read_dot_env(), os, sys

### Community 84 - "log_service.py"
Cohesion: 0.12
Nodes (26): container_log_channel(), LogSource, LogLine, datetime, Provider abstraction for docker hosts (real daemon or simulated). Providers are…, Yield parsed log lines. With ``follow=True`` the stream never ends., One parsed log record from a container log stream., append_lines() (+18 more)

### Community 85 - "NotFound"
Cohesion: 0.09
Nodes (51): list_sessions(), CurrentUser, DbSessionDep, delete, get, Request, UUID, Active sessions of this organization's members. Defaults to the caller's own;… (+43 more)

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "Conflict"
Cohesion: 0.07
Nodes (57): Conflict, OperationStatus, Lifecycle of one node operation (node-agent-architecture.md §5.1).…, Operation, Whether the agent reported this operation as successful. A terminal check, not…, One whitelisted action for one node, with a CAS lifecycle. ``attempts`` is…, OperationCreate, Any (+49 more)

### Community 88 - "test_certificate_lifecycle.py"
Cohesion: 0.09
Nodes (26): CertificateGeneration, one_live_generation_predicate(), One ACME order + one key pair. Renewal inserts a new row, never mutates one.…, The SQL predicate of ``uq_cert_generations_one_live``. Built from…, CertificateGenerationOut, One generation's lifecycle metadata. No material, no internal cursors.…, _documented_matrix(), _generation_checks() (+18 more)

### Community 89 - "test_payload_crypto.py"
Cohesion: 0.07
Nodes (62): decrypt(), decrypt_str(), encrypt(), fingerprint(), _parse_header(), PayloadContext, PayloadContextMismatch, PayloadDecryptionError (+54 more)

### Community 90 - "DomainStatus"
Cohesion: 0.07
Nodes (45): DomainStatus, Ownership-verification lifecycle of a Domain (domain-routing.md §4). ``STALE``…, Domain, One DNS name an organization is proving it controls. ``name`` is canonical (see…, What the lifecycle should do with an observation., VerificationDecision, apply_decision(), _detail_for() (+37 more)

### Community 91 - "dns_provider_service.py"
Cohesion: 0.07
Nodes (55): DnsProvider, One stored DNS credential plus the scope it is allowed to touch., DnsProviderKind, Which DNS API a stored credential speaks to. One member in v1 (Cloudflare) —…, CredentialCheck, DnsCredentialError, DnsCredentialProvider, provider_for() (+47 more)

### Community 92 - "mark_all_read"
Cohesion: 0.25
Nodes (11): mark_all_read(), mark_read(), CurrentUser, DbDep, get, post, UUID, Mark every unread alert read; returns how many rows changed. (+3 more)

### Community 93 - "apply_scope_to_session"
Cohesion: 0.06
Nodes (67): get_sessionmaker(), async_sessionmaker, AsyncSession, apply_scope_to_session(), current_org(), current_scope(), org_scope(), UUID (+59 more)

### Community 94 - "test_phase21_secret_version_integrity.py"
Cohesion: 0.18
Nodes (18): _app_role_dsn(), _owner_dsn(), _probe(), Phase 2.1 — ``secret_versions`` is append-only in the **database**, not just in…, Immutability is a database guarantee, not merely a missing code path. The owner…, The legitimate append paths keep working under the guard., The documented deletion policy: purging a Secret cascades its history., RLS is preserved: another tenant cannot see a version row, even by id. (+10 more)

### Community 95 - "Server"
Cohesion: 0.09
Nodes (38): Alias for :attr:`extra`, so the API can expose open-ended agent facts. The…, Server, acknowledge_rotation(), container_counts(), create_server(), get_server(), list_tags_with_usage(), _order_clause() (+30 more)

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
Nodes (69): org_dek(), Fernet, Yield the organization's DEK for **one operation**, then drop it. The key-only…, Parse a stored envelope, strictly. Every rejection is a named…, db(), A session with **no** tenant scope. Deliberately unscoped: it is how a test…, org_id(), _plaintext_key() (+61 more)

### Community 100 - "redact_mapping"
Cohesion: 0.09
Nodes (33): _is_sensitive_key(), Return a copy of *data* with sensitive values replaced, at any depth. Two…, Substring match on a normalised key so header-style names are caught too.…, redact_mapping(), parametrize, Unit tests for app.core.logging redaction (pure functions only)., No sensitive key name involved: the PEM armor is the only signal., Lists of dicts holding further lists — the shape an agent report takes. (+25 more)

### Community 101 - "DeterministicKEKProvider"
Cohesion: 0.05
Nodes (48): DeterministicKEKProvider, Deterministic wrap/unwrap/rewrap over an in-process AEAD., Bump the modelled KEK version, so a test can prove rewrap moves it., EncryptionContext, What a wrapped DEK is bound to. Frozen: a context is not edited in place., The canonical, unambiguous binding string. Field order and separator are fixed…, The binding as a provider expects it: base64, never line-wrapped. Wrap-free…, Wrap *dek* under the provider's root key, bound to *ctx*. (+40 more)

### Community 102 - "test_phase4_routing.py"
Cohesion: 0.07
Nodes (52): _agent_result_body(), _audits(), _claim(), _container_id(), _create_domain(), _create_node(), _event_types(), _heartbeat() (+44 more)

### Community 103 - "Path"
Cohesion: 0.12
Nodes (15): Path, An unloadable CA file must error, never silently fall back to no verify., A throwaway key + self-signed cert for ``localhost`` (real handshakes)., A one-shot HTTPS server; records a failed handshake instead of crashing., A real handshake against a self-signed server must fail verification., Trusting that same cert as a CA lets the identical handshake through., A link-local URL over plain HTTP must fail before any request or write., _self_signed_cert() (+7 more)

### Community 104 - "test_migration_phase4.py"
Cohesion: 0.15
Nodes (21): _columns(), _integrity_error(), _migrate_from_phase3(), Statement, Phase 4 migration (`f4a5b6c7d8e9`) against a real Phase 3 database. Phase 4 is…, The polymorphic shape is enforced in both directions., The anti-takeover rule is a partial unique index, not a convention., The column names of one table, read from the catalogue. (+13 more)

### Community 105 - "redis service (Redis 7, no persistence, loopback :6390)"
Cohesion: 0.22
Nodes (11): redis service (Redis 7, no persistence, loopback :6390), WebSocket API (/api/v1/ws handshake, frames, limits), WebSocket channels (global, server-metrics, container-logs, deployment-logs, incidents), Deployment engine (queue_deployment / execute_deployment / sweeper backstop), Real-time spine: PostgreSQL system_events + Redis pub/sub, Rollback as a new deployment (rollback_of_id), WebSocket hub (framework-thin, Redis fan-in, per-socket queues), Test suites (pytest unit+integration, vitest, Playwright e2e) (+3 more)

### Community 106 - "NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)"
Cohesion: 0.18
Nodes (12): Agent security model (one-way telemetry, no command channel), Agent enrollment token (X-Agent-Token, nxa_..., SHA-256 at rest), Agent heartbeat exponential backoff (cap 5 min, exit 1 on revoked token), agent/install.sh (enrollment installer), Agent metrics collection (/proc statvfs Docker socket), NexusOps agent (stdlib-only Python, agent/nexusops_agent.py), Agent systemd hardening (ProtectSystem=strict, NoNewPrivileges), Agent ingest API (POST /agent/hello, POST /agent/heartbeat) (+4 more)

### Community 107 - "test_migration_phase5.py"
Cohesion: 0.11
Nodes (37): _columns(), _foreign_keys(), _indexes(), _insert_certificate(), _insert_generation(), _integrity_error(), _migrate_from_phase4(), _migrate_to_phase5() (+29 more)

### Community 108 - "docker_real.py"
Cohesion: 0.08
Nodes (31): ContainerInfo, ContainerStats, Exception, Build a compact, secret-free description of a provider failure. Only the…, Normalized view of a container as reported by any provider., Point-in-time resource usage snapshot., sanitize_error(), _as_float() (+23 more)

### Community 109 - "Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)"
Cohesion: 0.25
Nodes (9): API keys (X-API-Key, nxo_..., scope intersection), First boot sequence (api entrypoint migrates, compose never seeds), Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test), Makefile workflows (up/test/lint/typecheck/migrate/seed), HIGH finding: API-key scope bypass for superadmin-owned keys (fixed: scope intersection first), Security audit 2026-09 (26 raw findings -> 20 confirmed, all fixed), HIGH finding: known seed superadmin + API key backdoor (fixed: NEXUSOPS_ALLOW_SEED opt-in, one-time password), Threat model (edge attacker, malicious agent, curious operator, leaked token, SSRF) (+1 more)

### Community 110 - "routes.py"
Cohesion: 0.20
Nodes (25): create_route(), delete_route(), disable_route(), _domain_status(), enable_route(), get_route(), list_routes(), AsyncSession (+17 more)

### Community 111 - "organization_service.py"
Cohesion: 0.14
Nodes (28): _check(), Forbidden, add_member(), create_organization(), get_organization(), membership_for_user(), AsyncSession, Membership (+20 more)

### Community 112 - "1. Architecture and trust boundaries"
Cohesion: 0.40
Nodes (5): 1.2 Phase 5 in one sentence, 1.3 Trust boundaries Phase 5 adds, 1.4 Non-goals for Phase 5, 1.5 Trust concentration: centralized key custody, accepted **conditionally** (decided), 1. Architecture and trust boundaries

### Community 113 - "dnsmock.py"
Cohesion: 0.12
Nodes (24): resolver(), answer(), encode_name(), encode_txt(), forward(), in_zone(), main(), parse_question() (+16 more)

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "v1/auth.py"
Cohesion: 0.08
Nodes (49): change_password(), _clear_refresh_cookie(), _cookies_secure(), login(), logout(), me(), _optional_actor(), AsyncSession (+41 more)

### Community 116 - "test_tenancy_allowlist.py"
Cohesion: 0.20
Nodes (14): AST, _actual_callers(), _calls_system_scope(), _module_path(), Path, The system-scope allowlist is the only fence around the tenancy carve-out.…, Every module that could open a system scope: ``app/`` plus the scripts., No module may lift tenant isolation without being named in the list. (+6 more)

### Community 117 - "_alembic_config"
Cohesion: 0.10
Nodes (22): The correction is part of ``head`` and adds no extra Alembic head., test_corrective_migration_is_reachable_from_head(), _alembic_config(), _at_revision(), _migration_dsn(), _owner_dsn(), Run one Alembic direction against ``database`` through the app's settings path.…, Phase 2 adds one migration; heads must not fork. (+14 more)

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
Cohesion: 0.24
Nodes (6): BaseHTTPRequestHandler, clear_record(), ControlHandler, The journey's only way to publish a record — no shell, no shared volume., set_record(), snapshot()

### Community 122 - "test_tenant_isolation.py"
Cohesion: 0.04
Nodes (61): A valid POST /servers body with per-test overrides., server_payload(), test_token_cannot_claim_a_foreign_tenants_node(), test_v1_heartbeat_keeps_the_204_contract(), Regression: a superadmin-owned key is still limited to its scope list. The…, test_scoped_api_key_cannot_exceed_its_grant(), _create_server(), Server CRUD, cascade delete, audit trail rows and audit immutability. (+53 more)

### Community 123 - "_run_migration"
Cohesion: 0.16
Nodes (19): alembic_script, Phase 2 migration (`b2c3d4e5f6a7`) against realistic legacy data. The promotion…, Upgrade ``database`` to ``revision``., The pre-Phase-2 shapes: application-scoped environments, per-app dupes., A fresh database reaches the same shape the models describe., _run_migration(), _seed_legacy_data(), test_environment_type_check_rejects_unknown_kinds() (+11 more)

### Community 124 - "test_dns_providers.py"
Cohesion: 0.07
Nodes (52): _audits(), cloudflare(), _create(), _create_domain(), _created(), _dns_stub(), _events(), _fake_observe() (+44 more)

### Community 125 - "OperationError"
Cohesion: 0.12
Nodes (23): _demux_docker_stream(), _docker_error(), execute_operation(), _insert_http_includes(), _nginx_bootstrap(), OperationError, Exception, Idempotent, minimal, reversible hook-up of the managed include. The only change… (+15 more)

### Community 126 - "list_operations"
Cohesion: 0.16
Nodes (20): cancel_operation(), create_operation(), get_operation(), list_operations(), DbDep, Depends, get, post (+12 more)

### Community 127 - "dns_providers.py"
Cohesion: 0.12
Nodes (30): create_dns_provider(), delete_dns_provider(), get_dns_provider(), list_dns_providers(), DbDep, delete, Depends, get (+22 more)

### Community 137 - "DockerHostsPage.test.tsx"
Cohesion: 0.18
Nodes (8): DockerHostOut, ApiError, failingHost, host, hostsPage, mockCountApi(), server, serversPage

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
Cohesion: 0.09
Nodes (25): _listener_ownership(), _listening_ports(), _nginx_binary(), nginx_capability(), _nginx_config_test(), _nginx_failure_summary(), _nginx_owned_ports(), _nginx_running() (+17 more)

### Community 153 - "types.ts"
Cohesion: 0.02
Nodes (87): AlertOut, CapabilityReport, ChannelOut, CheckOut, DeliveryOut, DeploymentLogLine, DeploymentStatus, DomainDetailOut (+79 more)

### Community 154 - "nexusops-draft.mjs"
Cohesion: 0.40
Nodes (4): DOCS, meta, SPINE, VERIFY_RULES

### Community 155 - "rollback_secret"
Cohesion: 0.11
Nodes (31): create_secret(), delete_secret(), get_secret(), list_secret_versions(), list_secrets(), DbSession, delete, get (+23 more)

### Community 156 - "nexusops-challenge.mjs"
Cohesion: 0.33
Nodes (5): CHALLENGE_COMMON, meta, RESEARCH_COMMON, SCHEMA, TASKS

### Community 157 - "Secrets Architecture"
Cohesion: 0.14
Nodes (14): 10. Resolution flow at deploy time, 2.1 Resolution runs inside org scope, 2.2 Migration mapping (applied by `b2c3d4e5f6a7`), 2. Scope model (org / project / environment layering) — **shipped**, 3.1 What this fixed, 3. SecretVersion — append-only history (**shipped in Phase 2**), 4.1 Audit event at resolution time, 4. Resolution authorization (+6 more)

### Community 158 - "test_schemas_agent.py"
Cohesion: 0.10
Nodes (38): AgentContainerIn, AgentHeartbeatIn, AgentHelloIn, Any, field_validator, Observed container state reported by an agent., Periodic metrics + observed containers from an enrolled agent. Network counters…, First contact from an agent after enrollment; fills static host facts. (+30 more)

### Community 159 - ".state"
Cohesion: 0.07
Nodes (34): computed_field, Derived lifecycle state: revoked wins over used wins over expired., 2.1 The six stages, kept distinct, 2.2 Certificate generation state machine, 2.3 Delivery/activation state machine (per certificate × node), 2.4 End-to-end sequence (control plane is the ACME client), 2.5 Failure at any stage, 2. Certificate lifecycle and state transitions (+26 more)

### Community 160 - "test_kek_vault_transit_live.py"
Cohesion: 0.07
Nodes (42): _ca_context(), _configure(), _ctx(), _docker(), _free_port(), LiveVault, fixture, Path (+34 more)

### Community 161 - "alert_service.py"
Cohesion: 0.20
Nodes (14): create_alert(), get_alert(), mark_all_read(), mark_read(), AsyncSession, UUID, Alert inbox: insert-only creation plus read/unread bookkeeping., Map a system event type to the alert severity it deserves. (+6 more)

### Community 162 - "decide"
Cohesion: 0.23
Nodes (18): decide(), matches_token(), Constant-time comparison of the observed TXT values against the token. TXT…, Turn one observation into the verification outcome — pure, no I/O.…, observation(), parametrize, The verification decision: every outcome, without a network. ``decide`` is…, test_a_sweep_invalidates_a_changed_delegation_even_with_the_token() (+10 more)

### Community 163 - "RouteHeader"
Cohesion: 0.10
Nodes (11): field_validator, model_validator, RateLimit, One header a route adds. ``target`` says where it lands., One route's request-rate ceiling (rendered as a ``limit_req_zone``)., A fixed host redirect. Phase 4 cannot express a scheme change here. There is…, RouteHeader, RouteRedirect (+3 more)

### Community 164 - "AgentClient"
Cohesion: 0.15
Nodes (8): AgentClient, _docker_raw(), SSLContext, A verifying TLS context. Verification is never disabled. A private/self-hosted…, Refuse to send credentials over plain HTTP to a non-loopback server. The…, One raw Docker API call; returns ``(status, body_bytes)``., _tls_context(), _UnixHTTPConnection

### Community 165 - "test_kek_selection.py"
Cohesion: 0.05
Nodes (60): build_kek_provider(), _construct(), Provider construction — the only place a ``KEKProvider`` is ever created. One…, Drop the cached provider (tests, and any future configuration reload)., Return the configured provider, or raise naming exactly what is wrong., reset_kek_provider(), provider_health(), The configured provider's health, at most one probe per cache window. (+52 more)

### Community 166 - "nginx.py"
Cohesion: 0.13
Nodes (23): _header_lines(), _quote(), _rate_zone(), NginxProvider — a pure, deterministic renderer plus the two op wrappers.…, Validate the route's headers and split them by destination., Wrap an already-validated value in quotes for a template slot. Values reaching…, The ``limit_req_zone`` declaration for a rate-limited route., A fixed host redirect, or ``None`` for a normal proxying route. (+15 more)

### Community 167 - "AuthContext"
Cohesion: 0.05
Nodes (65): _attach_organization(), AuthContext, get_current_user(), get_identity(), get_optional_user(), _load_organization(), _load_permissions(), membership_for_org() (+57 more)

### Community 168 - "TxtObservation"
Cohesion: 0.19
Nodes (13): One bounded look at a name's authoritative TXT record., TxtObservation, _flip_name_to(), Have *second_org* prove control of *name*, returning the verify outcome., Retry/backoff exhaustion lands in FAILED rather than retrying forever., _run_verify(), test_a_sweep_invalidates_a_changed_delegation_and_re_verification_restores_it(), test_a_verified_domain_goes_stale_then_unverified_when_proof_disappears() (+5 more)

### Community 169 - "pytest"
Cohesion: 0.11
Nodes (22): created_at server defaults must evaluate per insert, not at table creation., Regression: system_events and audit_logs shipped with DEFAULT 'now()' (quoted…, test_audit_and_event_created_at_defaults_are_dynamic(), Phase 2.1 corrective migration: legacy ``environment_type`` classification.…, Every case is classified as documented, ids and ownership intact., An explicit non-DEV classification survives the corrective migration. The…, Insert one legacy environment per case, in two organizations., _seed_typed_environments() (+14 more)

### Community 170 - "test_agent_contract.py"
Cohesion: 0.20
Nodes (15): agent_fixture(), _load_agent(), _patch_stats(), Any, fixture, MonkeyPatch, Contract tests: the shipped agent's payloads must satisfy the ingest schemas.…, One-shot docker stats reduce to cpu/mem/limit fields the schema accepts, with… (+7 more)

### Community 171 - "test_kek_vault_transit.py"
Cohesion: 0.10
Nodes (49): _ctx(), _login_ok(), _provider(), parametrize, Request, Response, The Vault Transit adapter's HTTP contract, without a Vault. This module pins…, encrypt, decrypt *and* rewrap: the binding must survive a rotation. (+41 more)

### Community 172 - "monitor_transport.py"
Cohesion: 0.09
Nodes (21): CheckOutcome, _decode(), get_transport(), MonitorTransport, BaseException, Protocol, Pluggable monitor check transports (real HTTP + deterministic simulator). A…, Pick the transport matching the monitor URL scheme. (+13 more)

### Community 173 - "Container"
Cohesion: 0.12
Nodes (22): ContainerHealth, Container, Observed container state mirrored from an agent or docker provider., Make a container row visible to this provider instance., _apply_agent_entry(), ensure_docker_host(), Return the agent-backed Docker host for a server, creating it if needed. The…, Write one heartbeat entry onto a container row. Kept complete at every call… (+14 more)

### Community 174 - "APIModel"
Cohesion: 0.03
Nodes (64): AgentContainerPortIn, AgentTokenRotation, CapabilityReport, One published-port binding of a container, as docker reports it. Four distinct…, A pending credential rotation, delivered on the agent's next beat. Served…, One node-reported capability. ``present`` defaults to false, and a capability…, ApiKeyCreateRequest, ApplicationUpdate (+56 more)

### Community 175 - "readiness"
Cohesion: 0.18
Nodes (12): liveness(), get, Response, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness(), HealthOut, Health / readiness schemas. (+4 more)

### Community 176 - "Platform Security Model — NexusOps"
Cohesion: 0.12
Nodes (17): 10.1 Node revocation playbook (compromised node / leaked agent token), 10.2 Key compromise playbook, 10. Incident response, 1.1 Real vs simulated today (do not mistake one for the other), 1. Scope, stance, and simulation honesty, 2. Assets, 3. Trust boundaries, 4. Tenant isolation model (summary) (+9 more)

### Community 177 - "Node & Agent Architecture"
Cohesion: 0.09
Nodes (22): install_hint(), The one-liner an operator pastes, without the raw token in argv. The token…, 1. Scope and stance, 3.2 Enrollment v2, 3.3 Token storage & rotation with dual-token grace, 3.4 Revocation semantics — fixing the 401 hot-loop, 3.5 Reconnect / offline states, 3. Agent lifecycle (+14 more)

### Community 178 - "main"
Cohesion: 0.14
Nodes (15): _build_hello_payload(), _enroll(), _interruptible_sleep(), main(), memory_total_mb(), os_info(), persist_token(), _process_pending_operations() (+7 more)

### Community 179 - "_node_session"
Cohesion: 0.13
Nodes (21): _dns_stub(), _fake_observe(), _hello_elsewhere(), _mark_reconcile_required_elsewhere(), _node_session(), _pause_render(), fixture, MonkeyPatch (+13 more)

### Community 180 - "server.py"
Cohesion: 0.11
Nodes (17): _clean_tag_names(), DockerHostSummary, EnrollTokenOut, computed_field, Server API schemas: create/update payloads, list/detail outputs, enrollment., Whether the node has reported capabilities at all (v2 hello)., Compact system event projection for server timelines., One-time agent enrollment token. The raw value is never stored. (+9 more)

### Community 181 - "_nginx_apply"
Cohesion: 0.11
Nodes (24): _fsync_dir(), _nginx_apply(), Materialize the bundle under ``staged/<id>/`` and return that directory.…, Build a self-contained config for ``nginx -t`` over the staged tree. The…, Move the staged tree over the live one, keeping the previous as backup., Put the previous known-good tree back. Returns whether it was possible., Stage → validate → swap → reload, with a rollback on a failed reload., Persist the last apply outcome atomically (temp + rename). (+16 more)

### Community 182 - "_rows"
Cohesion: 0.22
Nodes (17): Move ``database`` *back* to ``revision``. The same code path a deployment uses…, _rows(), _run_downgrade(), _columns(), Phase 5.2.1 migration (`f5a6b7c8d9e0`): two columns, one invariant, one…, The naming convention must not be applied twice. A fresh database is the only…, A ciphertext behind generation 0, and a generation with no material, both fail., The refusal is the point: a rollback must not delete key material. (+9 more)

### Community 183 - "events.py"
Cohesion: 0.09
Nodes (28): _decode_cursor(), _encode_cursor(), list_event_types(), list_events(), datetime, DbSession, Depends, get (+20 more)

### Community 184 - "1. Scope and current state"
Cohesion: 0.13
Nodes (20): configure_logging(), _orjson_dumps(), Any, structlog processor: scrub one record before anything renders it. The pipeline…, Configure structlog + stdlib logging once at process start. Everything…, Replace every embedded PEM private-key block in *value* with the marker. Only…, Scrub PEM private-key blocks out of one free-text value. The scalar counterpart…, Recursively redact one value of any shape — the depth-agnostic walk. Dicts,… (+12 more)

### Community 185 - "20261012_1200-c8d9e0f1a2b3_phase5_certificate_metadata.py"
Cohesion: 0.23
Nodes (13): downgrade(), _drop_certificate_permissions(), _drop_tenant_policies(), _grant(), _in_list(), Phase 5.1 — certificate metadata and the pre-issuance lifecycle. Adds, in one…, Grant the app role on *table*; the migration role GUC carries the name. The…, The two-policy shape every tenant table uses: tenant + system scope. (+5 more)

### Community 186 - "run_async"
Cohesion: 0.04
Nodes (97): asyncio, flush_pending_publishes(), Wait for frames scheduled by ``after_commit`` hooks to reach Redis. The commit…, process_heartbeat(), Apply a heartbeat: refresh facts, store a RAW metric, mirror containers.…, Celery application: periodic cadences live here, dynamic work is claimed…, task, Deployment execution task + stuck-deployment sweeper. (+89 more)

### Community 187 - "get_latest_server_metrics"
Cohesion: 0.25
Nodes (11): get_dashboard_summary(), get_latest_server_metrics(), get_server_metrics(), CurrentUser, DbDep, Depends, get, UUID (+3 more)

### Community 188 - "Deployment Architecture — NexusOps (target state)"
Cohesion: 0.11
Nodes (19): DeploymentRunner, Protocol, Adapter interface implemented by real (future) and simulated runners., Return the ordered step names for this run., 10. Events and WS during runs, 12. Rollback semantics (existing behavior kept), 13. The simulated runner stays — labeled, 14. Open questions (+11 more)

### Community 189 - "phase3.spec.ts"
Cohesion: 0.15
Nodes (10): frontend_e2e_fixtures_expect, AGENT, NodeDetail, OperationRow, REPO_ROOT, ref_node_child_process, ref_node_fs, ref_node_os (+2 more)

### Community 190 - "Settings"
Cohesion: 0.11
Nodes (9): field_validator, model_validator, Whether the runtime connection is the RLS-enforced application role. False…, Username from :attr:`database_url`, or ``None`` if it is unparseable., Validated application settings (loaded from environment / .env)., Refuse a Vault address that carries userinfo (Phase 5.2.1.2, F4).…, Refuse to start with an unusable or unsafe key source. Two failures are worth…, Settings (+1 more)

### Community 191 - "is_retryable"
Cohesion: 0.21
Nodes (12): is_retryable(), is_terminal(), Whether a generation has spent every attempt it was allowed., Whether a failed generation may be moved back to ``ORDERING``. A failure is…, Whether this generation will never move again. ``REVOKED`` and…, A short, sanitized sentence for ``status``. Never key material., retry_budget_exhausted(), status_detail_for() (+4 more)

### Community 192 - "env.py"
Cohesion: 0.24
Nodes (10): _database_url(), Alembic environment: metadata comes from app.models, URL from app settings., Migrations run as the table **owner**, never as the application role. The owner…, Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online(), Owner-role DSN for Alembic and the container entrypoint. Migrations… (+2 more)

### Community 193 - "10. Implementation slices, acceptance criteria, tests, limitations"
Cohesion: 0.18
Nodes (11): 10.2 Test requirements (what "done" means per slice), 10.3.1 Approved decisions (previously open), 10.3.2 Known limitations (accepted, not blockers), 10.3.3 Open items and what they block now, 10.3 Decisions and known limitations, 10.4 Reserved-operation-type lists — one source of truth (required consolidation), 10.5.1 Migration (one, additive, `down_revision = c8d9e0f1a2b3`), 10.5.4 What each later step adds (and where it stays out of scope) (+3 more)

### Community 194 - "test_ws_hub.py"
Cohesion: 0.14
Nodes (26): _connection(), _drain(), _event_frame(), _fake_sessionmaker(), hub(), _Org, Any, fixture (+18 more)

### Community 195 - "dek_envelope.py"
Cohesion: 0.12
Nodes (37): OrganizationDekEnvelope, The organization's Fernet DEK, **wrapped** by the configured KEK provider. The…, _claim_first_dek(), _context(), _load(), _load_envelope(), org_dek_context(), _organization_exists() (+29 more)

### Community 196 - "container.py"
Cohesion: 0.15
Nodes (18): _container_out(), Serialize one row; env values never leave the database (keys only)., ContainerDetailOut, ContainerOut, ContainerRemoveOut, host_ref(), HostRef, LogEntryOut (+10 more)

### Community 197 - "CheckResult"
Cohesion: 0.22
Nodes (13): CheckResult, HTTPMonitorTransport, Real HTTP(S) probe using httpx with per-monitor settings. Redirects are…, _FakeResponse, MonkeyPatch, A 302 from a public URL into link-local/metadata space must be refused., Defense in depth: even the httpx client must never auto-follow., _script_client() (+5 more)

### Community 198 - "20261014_1200-a7b8c9d0e1f2_isolate_org_dek_envelopes.py"
Cohesion: 0.23
Nodes (11): downgrade(), _drop_constraint(), _drop_tenant_policies(), _grant(), Phase 5.2.1.2 — the organization DEK envelope gets a tenant table of its own.…, Grant the app role the four DML verbs on *table*. Not ownership, and not…, Restore the envelope onto ``organizations`` — without losing any of it., Raw ``ALTER TABLE ... DROP CONSTRAINT``, as the tenancy migration does.… (+3 more)

### Community 199 - "20261010_1200-f4a5b6c7d8e9_phase4_domains_and_routes.py"
Cohesion: 0.31
Nodes (9): downgrade(), _drop_tenant_policies(), _grant(), _in_list(), Phase 4 — domains, routes and the routing schema. Adds, in one migration with a…, Grant the app role on *table*; the migration role GUC carries the name. The…, The two-policy shape every tenant table uses: tenant + system scope., _tenant_policies() (+1 more)

### Community 200 - "CertificateGenerationState"
Cohesion: 0.25
Nodes (14): CertificateGenerationState, Lifecycle of one ACME order + key pair, pre- and post-issuance. **Phase 5.1…, can_transition(), coerce_state(), The enum member for *value*, or ``None`` when it names no state at all., Whether *current* may move to *target*., The target state, or :class:`InvalidTransition` when the move is illegal., require_transition() (+6 more)

### Community 201 - "NotificationChannel"
Cohesion: 0.23
Nodes (18): NotificationChannel, A delivery target (email address / webhook endpoint). ``config_ciphertext``…, _audit(), create_channel(), decrypt_channel_config(), delete_channel(), encrypt_config(), _normalize_events() (+10 more)

### Community 202 - "scope_matches"
Cohesion: 0.13
Nodes (15): Check an API-key scope list against a required permission. Supports exact match…, scope_matches(), parametrize, test_scope_matches_truth_table(), 0. What shipped (Phase 1), 1. Principles (already true in the codebase, kept), 2. Registry changes (Phase 1 + new subsystems), 3. The five system roles (target) (+7 more)

### Community 203 - "ProxyProvider"
Cohesion: 0.33
Nodes (5): ProxyProvider, Any, Protocol, What ``app.services.proxy_service`` is allowed to assume about a provider. The…, 11. Post-deploy hooks

### Community 205 - "Multi-Tenancy Architecture"
Cohesion: 0.18
Nodes (10): 10. Migration (Phase 1), 1. Tenancy invariants, 2.1 Org creation — v1 decision, 2. Org resolution on every request, 3. The session guard (the mechanical layer), 4. Background jobs, 6. Agents, 7. The IDOR suite (+2 more)

### Community 206 - "test_agent_ingestion.py"
Cohesion: 0.30
Nodes (10): _enrolled(), _heartbeat(), Agent ingest pipeline: hello, heartbeat, staleness transitions, events., A container absent from a later heartbeat is gone from the daemon., A payload at the agent's cap may be truncated — absence proves nothing., test_heartbeat_at_container_cap_skips_reconciliation(), test_heartbeat_removes_vanished_containers(), test_heartbeat_updates_status_metrics_and_containers() (+2 more)

### Community 207 - "AuditLogPage.test.tsx"
Cohesion: 0.20
Nodes (5): AuditEntry, AuditLogPage(), formatTimestamp(), shortId(), mockedGet

### Community 208 - "resolve_secrets_for_environment"
Cohesion: 0.17
Nodes (14): Exception, A ``${secret:KEY}`` reference could not be resolved. Fail-closed. Carries…, One successfully resolved reference: metadata for audit, no value., Outcome of resolving an environment's config references., Resolve every ``${secret:KEY}`` reference an environment's config names.…, resolve_secrets_for_environment(), ResolvedSecrets, SecretReference (+6 more)

### Community 209 - "notification_sender.py"
Cohesion: 0.17
Nodes (15): NotificationError, Any, BaseException, Exception, Low-level notification transports: SMTP email and outgoing webhooks. These…, POST *payload* as JSON to *url*; 2xx is success, anything else raises. Response…, Raised when a delivery attempt fails. Message is safe to persist., Bounded, single-line, content-free error reason. (+7 more)

### Community 210 - "UpstreamContainerOut"
Cohesion: 0.20
Nodes (11): One genuinely usable published port reported by the node's agent., A container that can actually back a route on this node., UpstreamContainerOut, UpstreamPortOut, container_out(), The address nginx should proxy to for one published binding. A wildcard bind…, The published ports of *container* that a route may actually point at. Honest…, Containers on *node_id* that can back a route, for the route editor. (+3 more)

### Community 211 - "20261014_1600-b8c9d0e1f2a3_phase522_providers_acme_material.py"
Cohesion: 0.21
Nodes (14): _assert_no_material(), downgrade(), _drop_constraint(), _drop_tenant_policies(), _grant(), _in_list(), Phase 5.2.2 — DNS credentials, ACME accounts, and the certificate material…, Raw ``ALTER TABLE ... DROP CONSTRAINT IF EXISTS``. ``op.drop_constraint`` is… (+6 more)

### Community 212 - "SystemEvent"
Cohesion: 0.33
Nodes (10): NotificationDelivery, SystemEvent, _channel(), _delivery(), UUID, Notification channel + delivery-log endpoints. Regression coverage for GET…, The same event frame consumed twice queues ONE delivery per channel. Every API…, test_dispatch_frame_is_idempotent_across_workers() (+2 more)

### Community 213 - "_FakeAsyncClient"
Cohesion: 0.22
Nodes (3): _FakeAsyncClient, _FakeRequestObj, Scripted httpx.AsyncClient: responses keyed by absolute request URL.

### Community 214 - "channel.py"
Cohesion: 0.19
Nodes (12): ChannelType, ChannelBase, ChannelCreate, ChannelOut, ChannelUpdate, DeliveryOut, EmailConfig, model_validator (+4 more)

### Community 215 - "test_migration_drift.py"
Cohesion: 0.14
Nodes (13): alembic_autogenerate, alembic_migration, CertificateRevocationState, The states in which a generation is still being worked on. At most one of these…, The states whose rows must carry key material and a DEK generation. The…, The CA conversation about a generation, deliberately a second axis. ``state``…, Model / migration drift: the schema in the database must match the models.…, ``Base.metadata`` and the migrated database must describe the same schema. (+5 more)

### Community 217 - "paginate"
Cohesion: 0.15
Nodes (13): list_audit_logs(), datetime, DbSession, Depends, get, PageParamsDep, Newest-first audit trail with optional filters. No write routes exist for this…, paginate() (+5 more)

### Community 218 - "ContainerListPage.test.tsx"
Cohesion: 0.29
Nodes (3): ApiError, server, serversPage

### Community 219 - "docs/engineering-report.md - build and verification report"
Cohesion: 0.27
Nodes (12): docker-compose.dev.yml - dev overlay, docker-compose.docker-sock.yml - docker socket override, docker-compose.yml - full stack definition, docs/agent.md - agent guide, docs/api.md - API guide, Append-only audit log (Postgres BEFORE UPDATE OR DELETE trigger), docs/deployment.md - deployment and operations guide, docs/development.md - developer guide (+4 more)

### Community 220 - "Platform Vision — NexusOps"
Cohesion: 0.20
Nodes (10): 1. Where NexusOps is today, 2.1 What we are NOT building, 2.2 The wedge (differentiation), 2. The direction, 3. Guiding principles, 4. Customer journey (target), 5.1 Architecture overview (target), 5. Control plane / data plane boundary (+2 more)

### Community 221 - "20261009_1100-d4e5f6a7b8c9_correct_legacy_environment_types.py"
Cohesion: 0.33
Nodes (3): downgrade(), Phase 2.1 — correct legacy ``environment_type`` classification. The Phase 2…, No-op: the correction is a best-effort classification, not reversible.…

### Community 222 - "CloudflareDnsProvider"
Cohesion: 0.28
Nodes (5): CloudflareDnsProvider, Response, Cloudflare credential verification over the public API., A bounded, credential-free description of a failed call., Verify the token and list the zones it can reach. Never raises for a provider-…

### Community 223 - "assert_state"
Cohesion: 0.14
Nodes (18): assert_material_bearing(), assert_pre_issuance(), assert_state(), certificate_status_for(), material_required(), Return *value* as a state, or refuse a value that names none., Return *value* as a pre-issuance state, or refuse it loudly. The narrowing the…, Return *value* as a state that **must** carry material, or refuse it. The… (+10 more)

### Community 224 - "certificate_lifecycle.py"
Cohesion: 0.36
Nodes (8): attempt_delay_seconds(), next_attempt_at(), datetime, The certificate lifecycle — pure decisions, no I/O, no side effects. The whole…, Exponential backoff after *attempt_count* spent attempts, capped at 24h., When the next attempt on a generation becomes due., _utcnow(), test_backoff_grows_and_is_capped()

### Community 225 - "UnrepresentableState"
Cohesion: 0.33
Nodes (5): InvalidTransition, ValueError, Two states with no legal move between them., A state the caller's context cannot accept. Two callers narrow differently and…, UnrepresentableState

### Community 226 - "LoginPage.tsx"
Cohesion: 0.33
Nodes (4): LoginPage, FieldErrors, MetaInfo, redirectTarget()

### Community 227 - "cloudflare"
Cohesion: 0.25
Nodes (6): cloudflare(), _FakeCloudflare, fixture, MonkeyPatch, Every test in this module gets the fake, and no test can reach the network., The credential seam: a verdict plus the zones the token can see.

### Community 228 - "get_meta"
Cohesion: 0.40
Nodes (5): get_meta(), DbSessionDep, get, Public metadata; identity fields appear only for valid credentials., OptionalUser

### Community 229 - "_live_bundle_id"
Cohesion: 0.20
Nodes (10): _allowed_bundle_path(), _live_bundle_id(), _live_files(), The bundle fingerprint — byte-identical to the control plane's algorithm.…, Read the live managed tree, or ``None`` when it does not exist yet., Fingerprint of the configuration tree currently on disk., Independently validate a bundle. Anything unexpected is refused., _template_version_of() (+2 more)

### Community 230 - "2. Entities"
Cohesion: 0.25
Nodes (8): 2.1.1 ApiKey org binding detail, 2.2.1 Environment promotion detail — **shipped in Phase 2**, 2.2 Delivery (existing models, extended), 2.4 Routing & TLS (new subsystem), 2.5 Secrets (re-scoped — **shipped in Phase 2**), 2.6 Observability (existing, org-scoped via parents), 2.7 Backups, connections, billing (new subsystems, design-only in early phases), 2. Entities

### Community 231 - "register_exception_handlers"
Cohesion: 0.24
Nodes (9): _error_payload(), Any, FastAPI, Request, register_exception_handlers(), handle_app_error(), handle_http_exception(), handle_unexpected() (+1 more)

### Community 232 - "6. Private-key encryption and key management"
Cohesion: 0.25
Nodes (8): 6.1 Threat model — what each envelope actually protects against, 6.2 Recommended v1 design, 6.3 Rotation, 6.4 No secret-store migration (explicit scope boundary), 6.5 Backups, recovery, and consequences of key loss, 6.6 Production-readiness requirements for centralized custody (conditions of §1.5), 6.8 Decisions closed here, and what remains an operator choice, 6. Private-key encryption and key management

### Community 233 - "apply_node_proxy_config"
Cohesion: 0.29
Nodes (7): apply_node_proxy_config(), Ask the node to report its live proxy state (queues ``nginx.status``)., Force a re-render and apply of this node's desired configuration. The routine…, refresh_node_proxy_status(), Raise a named conflict when routing may not be managed on this node., require_eligible(), ProxyManageCtx

### Community 234 - "20261009_1300-a1b2c3d4e5f6_add_phase3_nodes_and_agent_v2.py"
Cohesion: 0.40
Nodes (4): _grant(), Phase 3 — Nodes & Agent v2 schema. Adds, in one migration with a single head: *…, Grant the app role on *table*; the migration role GUC carries the name. The…, upgrade()

### Community 235 - "websocket_endpoint"
Cohesion: 0.67
Nodes (3): websocket, Hand the socket to the hub (auth handshake handled there)., websocket_endpoint()

### Community 236 - "v1/agent.py"
Cohesion: 0.09
Nodes (38): agent_enroll(), agent_heartbeat(), agent_hello(), claim_operation(), _presented_token(), DbDep, post, Request (+30 more)

### Community 237 - "MonitorTargetType"
Cohesion: 0.33
Nodes (7): MonitorTargetType, What a monitor observes (domain-model.md §2.6, polymorphic targets). ``URL`` is…, _count_rows_in_system_scope(), The second organization wins; the first stops being the owner., test_enabling_a_route_attaches_an_http_uptime_monitor(), test_monitor_optout_is_respected(), test_verified_names_are_platform_unique_with_a_cross_org_flip()

### Community 238 - "4. Authorization and tenant isolation"
Cohesion: 0.40
Nodes (5): 4.1 CodenamesPhase 5 adds the two codenames already listed in authorization.md §2 — they are **not**, 4.2 Per-type permission and capability gating, 4.3 Tenant isolation, 4.4 Route → certificate binding at write time, 4. Authorization and tenant isolation

### Community 239 - "network_rates"
Cohesion: 0.33
Nodes (6): build_facts(), network_rates(), network_total_bytes(), Sum rx/tx bytes over non-loopback interfaces from /proc/net/dev., Return (rx_kb_s, tx_kb_s) or ``(None, None)`` when not measurable., Open-ended host facts, stored in the node's flexible JSONB blob. Deliberately…

### Community 240 - "material_guard_predicate"
Cohesion: 0.33
Nodes (6): material_guard_predicate(), pre_issuance_predicate(), The states in which a generation carries no material *by construction*.…, The SQL of ``ck_certificate_generations_material_guard``. Derived from the enum…, The guard is derived, not restated: it is the pre-issuance branch *or* the six…, test_the_material_guard_check_is_the_enums_predicate()

### Community 241 - "instant_pacing"
Cohesion: 0.40
Nodes (4): instant_pacing(), fixture, MonkeyPatch, Remove the per-line sleeps; pacing bounds are asserted separately.

### Community 243 - "ApplicationBase"
Cohesion: 0.40
Nodes (4): ApplicationBase, Any, field_validator, Shared application fields; ``build_config`` is a free-form dict.

### Community 245 - "DnsCredentialUnavailable"
Cohesion: 0.50
Nodes (3): DnsCredentialUnavailable, RuntimeError, The stored credential cannot be read right now. One cause matters and is named…

### Community 246 - "mark_stale_servers"
Cohesion: 0.67
Nodes (3): mark_stale_servers(), Flip ONLINE servers past their offline threshold to OFFLINE and back. Uses…, _utc_today()

### Community 247 - ".__init__"
Cohesion: 0.12
Nodes (10): _BarrierRewrapProvider, _FailingRewrapProvider, _OverlappingProvider, _PingPongProvider, Fails *only* ``rewrap_dek`` — a rotation that cannot reach its provider. The…, The deterministic provider with a real await point inside ``wrap_dek``. Without…, Two rewrap attempts overlap, deterministically. ``rewrap_dek`` is called…, Holds one rewrap result open until the test releases it. The result is computed… (+2 more)

## Knowledge Gaps
- **497 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+492 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 2829 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `6. Tooling: reproducible e2e` connect `run_async` to `core/tenancy.py`, `client.ts`, `Conflict`, `apply_scope_to_session`, `auth_service.py`?**
  _High betweenness centrality (0.202) - this node is a cross-community bridge._
- **Why does `useEventStream()` connect `client.ts` to `apiGet`, `App.tsx`, `AuthContext.tsx`, `ServerDetailPage.tsx`, `@tanstack/react-query`, `run_async`?**
  _High betweenness centrality (0.201) - this node is a cross-community bridge._
- **Why does `TenancyScopeError` connect `core/tenancy.py` to `test_certificates.py`, `dek_envelope.py`, `server_service.py`, `test_org_dek_envelope.py`, `AuthContext`, `run_async`, `assert_error_code`, `enums.py`, `test_acme_accounts.py`, `enrollment_service.py`, `log_service.py`, `test_tenant_isolation.py`, `apply_scope_to_session`?**
  _High betweenness centrality (0.102) - this node is a cross-community bridge._
- **Are the 105 inferred relationships involving `AuthContext` (e.g. with `TenancyScopeError` and `MembershipStatus`) actually correct?**
  _`AuthContext` has 105 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `APIModel` (e.g. with `OperationSpec` and `test_specs_reject_unknown_params()`) actually correct?**
  _`APIModel` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `meta`, `SCHEMA`, `RESEARCH_COMMON` to the rest of the system?**
  _497 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `apiGet` be split into smaller, more focused modules?**
  _Cohesion score 0.057002457002457 - nodes in this community are weakly interconnected._