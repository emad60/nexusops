# Graph Report - nexusops  (2026-10-18)

## Corpus Check
- 409 files · ~518,298 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: (none) 10, .example 1, .service 1)

## Summary
- 7795 nodes · 22983 edges · 260 communities (238 shown, 22 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1880 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `63728ee9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- apiGet
- test_certificates.py
- ApiKeysPage.tsx
- _verified_domain
- container_service.py
- toast.tsx
- resolve_client_ip
- OperationType
- App.tsx
- test_agent_v2.py
- assert_error_code
- ServerDetailPage.tsx
- APIModel
- ContainerDetailPage.tsx
- validate_config
- v1/certificates.py
- deployment_engine.py
- SimulatedDockerProvider
- enrollment_service.py
- secret_service.py
- test_deployments_simulated.py
- containers.py
- metrics_service.py
- get_settings
- Domain Routing — NexusOps
- test_phase4_routing.py
- Product Roadmap — NexusOps Multi-Tenant Platform
- test_agent_backoff.py
- @tanstack/react-query
- nexusops_agent.py
- test_certificate_pebble.py
- AuthContext
- AcmeDirectory
- sqlalchemy
- docker_hosts.py
- integration/test_certificate_issuance.py
- schemas/proxy.py
- v1/search.py
- models/__init__.py
- log_service.py
- DockerProvider
- test_monitor_transport.py
- test_migration_phase5212.py
- client.ts
- project_service.py
- test_permissions.py
- test_kek_health_api.py
- test_phase3_nodes.py
- UnprocessableEntity
- test_ws_hub.py
- update_role
- docker_host_service.py
- proxy_service.py
- VaultTransitKEKProvider
- update_organization
- test_agent_nginx_contract.py
- UserOut
- alembic
- notification_service.py
- helpers.py
- compilerOptions
- _list_deployments
- test_error_logging.py
- dns_verifier.py
- test_phase2_environments.py
- route_service.py
- test_schema_redaction.py
- publish
- login_account
- seed.py
- core/tenancy.py
- test_secrets.py
- test_nginx_renderer.py
- domains.py
- api service (FastAPI / uvicorn :8000)
- monitor_service.py
- typing
- test_acme_accounts.py
- ssrf.py
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
- DomainStatus
- dns_provider_service.py
- mark_all_read
- ScopedSession
- test_phase21_secret_version_integrity.py
- test_dns_propagation.py
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- fixtures.ts
- test_org_dek_envelope.py
- redact_mapping
- DeterministicKEKProvider
- payload_crypto.py
- Path
- _exec
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- test_migration_phase5.py
- v1/auth.py
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- UpstreamContainerOut
- run_async
- middleware.py
- dnsmock.py
- scripts
- login
- test_tenancy_allowlist.py
- test_migration_phase2.py
- dependencies
- DeploymentDetailPage.test.tsx
- generate_secrets.sh
- ControlHandler
- test_tenant_isolation.py
- _run_migration
- test_dns_providers.py
- OperationError
- list_operations
- test_tasks_util.py
- install.sh
- docker-entrypoint.sh
- integration/__init__.py
- ProjectDetailPage.tsx
- CLAUDE.md - project graphify rules
- Graphify query workflow (query / path / explain / update)
- frontend/index.html - SPA shell
- NexusOps Favicon — stylized letter 'N' lettermark in sky blue (#38bdf8) on a dark navy rounded square (#0b1120, 7px corner radius)
- nexusops-backend
- certificate_issuance.py
- 20261009_1000-c3d4e5f6a7b8_enforce_secret_version_integrity.py
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
- Multi-Tenancy Architecture
- _expectations
- pytest
- test_agent_contract.py
- test_kek_vault_transit.py
- monitor_transport.py
- me
- _credential_seam
- journey.spec.ts
- Platform Security Model — NexusOps
- Node & Agent Architecture
- main
- _node_session
- Domain
- _nginx_apply
- _rows
- list_events
- UnrepresentableState
- 20261012_1200-c8d9e0f1a2b3_phase5_certificate_metadata.py
- apply_scope_to_session
- test_schemas_search.py
- Deployment Architecture — NexusOps (target state)
- phase3.spec.ts
- Settings
- TxtRecord
- env.py
- 10. Implementation slices, acceptance criteria, tests, limitations
- test_app_gating.py
- dek_envelope.py
- certificate_service.py
- entries
- 20261014_1200-a7b8c9d0e1f2_isolate_org_dek_envelopes.py
- 20261010_1200-f4a5b6c7d8e9_phase4_domains_and_routes.py
- certificate_order.py
- _run
- SimulatedDeploymentRunner
- ProxyProvider
- _LibrarySession
- enums.py
- test_agent_ingestion.py
- .dispatch
- Hub
- 20261008_1200-b2c3d4e5f6a7_add_projects_and_environments.py
- Certificate
- 20261014_1600-b8c9d0e1f2a3_phase522_providers_acme_material.py
- SystemEvent
- _FakeAsyncClient
- 20261009_1100-d4e5f6a7b8c9_correct_legacy_environment_types.py
- test_migration_drift.py
- README.md - NexusOps overview
- create_api_key
- wait_for_txt_records
- register
- Platform Vision — NexusOps
- 9. Renewal, expiration, ownership loss, removal, revocation
- 20260923_1000-c4e2a1f7b9d3_rename_server_codenames_to_node.py
- CertificateGenerationState
- certificate_lifecycle.py
- account_key
- 20261012_1600-f5a6b7c8d9e0_phase5_org_dek_envelope.py
- cloudflare
- record
- _validate_bundle
- scope_matches
- register_exception_handlers
- .text
- servers.py
- ._route
- Appendix A — Decisions resolved here (that certificate-management.md left open)
- report_operation_result
- projects.py
- docker_real.py
- enqueue_generation
- _transport_is_https
- instant_pacing
- .__tablename__
- known_directory_urls
- .apply_params
- .facts
- _nginx_bootstrap
- KEKUnavailableError
- TxtObservation
- resolve_secrets_for_environment
- 20260922_1000-a3f1c8d24b6e_add_tenancy_foundation.py
- 7. Secure delivery of certificate material to authorized nodes
- test_event_registry.py
- generate_account_key
- PayloadContext
- 20261016_1000-c9d0e1f2a3b4_phase53_generation_directory.py
- TxtExpectation
- test_run_async_publishes_frames_scheduled_by_the_commit_hook
- test_same_origin_compares_the_full_authority_including_port
- PropagationResult

## God Nodes (most connected - your core abstractions)
1. `AuthContext` - 175 edges
2. `APIModel` - 151 edges
3. `get_settings()` - 112 edges
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

## Communities (260 total, 22 thin omitted)

### Community 0 - "apiGet"
Cohesion: 0.06
Nodes (80): apiDelete(), apiGet(), apiPost(), DomainDetailPage, MonitorDetailPage, useAuth(), SelectField(), useToast() (+72 more)

### Community 1 - "test_certificates.py"
Cohesion: 0.08
Nodes (56): _app_role_dsn(), _audits(), _certificate_rows(), _create_domain(), _created_certificate(), _dns_stub(), _events(), _fake_observe() (+48 more)

### Community 2 - "ApiKeysPage.tsx"
Cohesion: 0.09
Nodes (19): ApiKeyOut, ApiKeysPage, ApiKeyCreatedOut, handleCopyKey(), copyText(), describeError(), EMPTY_FORM, GROUP_STYLE (+11 more)

### Community 3 - "_verified_domain"
Cohesion: 0.07
Nodes (75): Keep every routed node's live configuration matching the desired bundle. One…, sweep_routes(), _candidates(), _run(), _agent_result_body(), _audits(), _claim(), _converged_node_with_a_route() (+67 more)

### Community 4 - "container_service.py"
Cohesion: 0.09
Nodes (44): ContainerStatus, clip(), DockerProviderError, Exception, A provider operation failed. ``str()`` is safe to show/log., Build a compact, secret-free description of a provider failure. Only the…, Truncate *text* to *limit* characters, stripping control chars., sanitize_error() (+36 more)

### Community 5 - "toast.tsx"
Cohesion: 0.02
Nodes (80): name, private, type, version, CheckOut, IncidentOut, MonitorOut, SessionInfo (+72 more)

### Community 6 - "resolve_client_ip"
Cohesion: 0.19
Nodes (20): _is_trusted(), _parse_networks(), Request, Parse a comma-separated CIDR list; malformed entries are skipped., Real client address for *request* per the trust model above., resolve_client_ip(), make_request(), Request (+12 more)

### Community 7 - "OperationType"
Cohesion: 0.14
Nodes (17): OperationType, The whitelist. Nothing outside this enum ships as an exec surface. Each type…, Any, Validate *params* against the type's model and return the stored form.…, validate_params(), The operation dispatch whitelist is a contract, not a convention.…, The framework reuses existing codenames; a generic exec grant must not exist., Phase 4 ships exactly the three nginx ops, each gated on the capability. This… (+9 more)

### Community 8 - "App.tsx"
Cohesion: 0.04
Nodes (89): AuditEntry, DeploymentOut, DeploymentStepOut, EnvironmentDetailOut, EnvironmentOut, IncidentEventOut, Page, ProjectOut (+81 more)

### Community 9 - "test_agent_v2.py"
Cohesion: 0.08
Nodes (36): agent_fixture(), _load_agent(), Any, fixture, parametrize, Agent protocol v2: honest metrics, capability detection, and the executor. The…, Phase 4 shipped three nginx ops — no file primitive, no command primitive., Trusting a private CA must not weaken verification. (+28 more)

### Community 10 - "assert_error_code"
Cohesion: 0.07
Nodes (55): assert_error_code(), Assert envelope shape + code; returns the inner error object., _dispatch(), _dispatch_body(), _enrolled_node(), _mutate_in_system_scope(), MonkeyPatch, Node operations: the compare-and-set state machine and its tenant boundary.… (+47 more)

### Community 11 - "ServerDetailPage.tsx"
Cohesion: 0.05
Nodes (47): EnrollmentTokenCreated, EnrollmentTokenItem, MetricPoint, OperationItem, OperationType, OrganizationRequiredPage, ServerDetailPage, ServerListPage (+39 more)

### Community 12 - "APIModel"
Cohesion: 0.02
Nodes (159): _enrollment_created(), AgentContainerPortIn, AgentEnrollOut, AgentHeartbeatOut, AgentHelloOut, Agent-facing schemas. Payloads are data only — never executed. Wire protocol v2…, Tells the agent how often to report and what protocol it negotiated., One published-port binding of a container, as docker reports it. Four distinct… (+151 more)

### Community 13 - "ContainerDetailPage.tsx"
Cohesion: 0.05
Nodes (41): getAccessToken(), onActiveOrgChange(), refreshToken(), CursorPage, EventItem, ContainerDetailPage, EventsPage, Subscription (+33 more)

### Community 14 - "validate_config"
Cohesion: 0.07
Nodes (32): ProjectUpdate, field_validator, Partial project update; omitted fields are left untouched., collect_secret_refs(), walk(), ConfigValidationError, effective_config(), merge_config() (+24 more)

### Community 15 - "v1/certificates.py"
Cohesion: 0.12
Nodes (34): create_certificate(), delete_certificate(), _detail(), get_certificate(), list_certificates(), alias, AsyncSession, DbDep (+26 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.11
Nodes (54): deployment_log_channel(), Deployment, DeploymentStep, DeploymentStatus, StepStatus, _after_commit_enqueue(), _after_rollback_drop(), _audit_resolution_failed() (+46 more)

### Community 17 - "SimulatedDockerProvider"
Cohesion: 0.08
Nodes (29): Any, Plausible numbers derived from the row plus time-based sine noise., Implements :class:`DockerProvider` semantics against DB rows., Make a container row visible to this provider instance., Attach already-fetched log rows so ``logs()`` can replay them., _seed_int(), SimulatedDockerProvider, _log_entry() (+21 more)

### Community 18 - "enrollment_service.py"
Cohesion: 0.10
Nodes (33): generate_enrollment_token(), An enrollment credential (``nxk_``): single-use, short-lived, org-scoped.…, Return the active org id or raise; used by services that need it explicitly., require_org(), EnrollmentToken, One single-use credential that enrolls (or claims) exactly one node., Whether the row could still be redeemed (not a race-safe check)., AgentEnrollIn (+25 more)

### Community 19 - "secret_service.py"
Cohesion: 0.08
Nodes (52): digest_of(), encrypt_str(), Short server-verifiable digest used for change detection display. HMAC-SHA256…, An encrypted configuration value, scoped to org, project or environment.…, One immutable value of a :class:`Secret` — append-only history. A row is…, Secret, SecretVersion, _actor_type() (+44 more)

### Community 20 - "test_deployments_simulated.py"
Cohesion: 0.15
Nodes (29): execute_deployment(), Run one deployment to a terminal state. Never raises; safe to re-run., get_application(), get_environment(), _as_worker(), _delivery_chain(), _owner_ctx(), _queue() (+21 more)

### Community 21 - "containers.py"
Cohesion: 0.06
Nodes (68): _action_route(), _endpoint(), _container_out(), _decode_frame(), _ev(), get_container(), _like_pattern(), list_container_logs() (+60 more)

### Community 22 - "metrics_service.py"
Cohesion: 0.09
Nodes (41): get_dashboard_summary(), get_latest_server_metrics(), get_server_metrics(), CurrentUser, DbDep, Depends, get, UUID (+33 more)

### Community 23 - "get_settings"
Cohesion: 0.04
Nodes (77): argon2, argon2_exceptions, _quoted_list(), Add the operations framework table (node-agent-architecture.md §5). One tenant-…, upgrade(), _grant(), Phase 3 — Nodes & Agent v2 schema. Adds, in one migration with a single head: *…, Grant the app role on *table*; the migration role GUC carries the name. The… (+69 more)

### Community 24 - "Domain Routing — NexusOps"
Cohesion: 0.07
Nodes (31): The directory URL stored on the account row and recorded per issuance., 10. Wildcards and catch-all, 11. User journey, 12. API surface, permissions, audit, 13. Monitoring tie-in, 1. Scope and current state, 2. Where nginx runs, 3.1 Domain (+23 more)

### Community 25 - "test_phase4_routing.py"
Cohesion: 0.06
Nodes (60): Run the enclosed block with tenant filtering off (maintenance only). ``reason``…, system_scope(), MonitorTargetType, What a monitor observes (domain-model.md §2.6, polymorphic targets). ``URL`` is…, _container_id(), _count_rows_in_system_scope(), _create_domain(), _create_node() (+52 more)

### Community 26 - "Product Roadmap — NexusOps Multi-Tenant Platform"
Cohesion: 0.11
Nodes (18): What one reported result did to its operation row. The caller's side effects —…, ResultTransition, 0. Stance, 10. Phase 7 — Teams, grants & custom roles — **proposal, not implemented**, 11. Phase 8 — Backups — **proposal, not implemented**, 12. Phase 9 — Billing & metering — **proposal, not implemented**, 13.1 Scope-creep gates — what must be true before each expansion, 13. First commercially meaningful version (+10 more)

### Community 27 - "test_agent_backoff.py"
Cohesion: 0.14
Nodes (22): agent_fixture(), _install_sleep(), fake_sleep(), _load_agent(), _patch_host(), Any, fixture, MonkeyPatch (+14 more)

### Community 28 - "@tanstack/react-query"
Cohesion: 0.05
Nodes (36): DashboardSummary, SearchResult, DashboardPage, Command, CommandPalette(), CommandPaletteProps, STATIC_COMMANDS, BubblePosition (+28 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.09
Nodes (30): build_capabilities(), build_heartbeat(), collect_container_stats(), collect_containers(), _container_ports(), _container_status(), cpu_percent_since(), disk_stats() (+22 more)

### Community 30 - "test_certificate_pebble.py"
Cohesion: 0.08
Nodes (49): _bootstrap_resolver(), _CloudflareCredentials, _compose(), _create_domain(), _create_provider(), _decrypted(), _events(), _get_json() (+41 more)

### Community 31 - "AuthContext"
Cohesion: 0.06
Nodes (78): active_memberships(), _attach_organization(), AuthContext, get_current_user(), get_identity(), get_optional_user(), _load_permissions(), _org_id_from_header() (+70 more)

### Community 32 - "AcmeDirectory"
Cohesion: 0.04
Nodes (105): AbstractAsyncContextManager, AuthorizationResource, Which known directory this account is at; ``None`` when the URL is neither.…, AcmeDirectory, Which certificate authority a per-organization ACME account belongs to. A…, Whether this directory issues publicly trusted certificates. The single…, Whether a certificate from this directory is trusted by a browser. False for…, Short operator-facing name, stored in metadata and shown in the API. (+97 more)

### Community 33 - "sqlalchemy"
Cohesion: 0.03
Nodes (84): asyncio, liveness(), get, Response, Health probes: liveness (always cheap) and readiness (checks dependencies).…, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness() (+76 more)

### Community 34 - "docker_hosts.py"
Cohesion: 0.08
Nodes (52): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+44 more)

### Community 35 - "integration/test_certificate_issuance.py"
Cohesion: 0.11
Nodes (42): Request, Make the certificate's newest generation attemptable *now*, or refuse it. A…, request_retry(), load(), The generation's order document, or an empty one. **Never raises.** A malformed…, _AmbiguousZone, _create_domain(), _create_provider() (+34 more)

### Community 36 - "schemas/proxy.py"
Cohesion: 0.14
Nodes (19): BundleFile, fingerprint_files(), is_allowed_bundle_path(), NginxBundle, Any, Proxy bundle and operation-parameter schemas — the agent-facing config…, One rendered file. The path is allowlisted, the content is bounded., Deterministic fingerprint over the complete rendered tree. Path order is… (+11 more)

### Community 37 - "v1/search.py"
Cohesion: 0.18
Nodes (23): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+15 more)

### Community 38 - "models/__init__.py"
Cohesion: 0.07
Nodes (71): _org_scoped_classes(), Mapped classes marked :class:`~app.models.base.OrgScoped`. Reads the mapper…, AcmeAccount, The per-organization ACME account and its protected account key. One account…, One ACME account: its directory, its CA-side URL, and its wrapped key., Base, big_serial_pk(), json_column() (+63 more)

### Community 39 - "log_service.py"
Cohesion: 0.09
Nodes (31): container_log_channel(), LogSource, LogLine, datetime, Provider abstraction for docker hosts (real daemon or simulated). Providers are…, Yield parsed log lines. With ``follow=True`` the stream never ends., One parsed log record from a container log stream., datetime (+23 more)

### Community 40 - "DockerProvider"
Cohesion: 0.09
Nodes (10): DockerProvider, Any, Protocol, List containers visible to the provider., Inspect a single container by id (short ids allowed)., List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``., List volumes: keys ``name``, ``driver``, ``mountpoint``., List networks: keys ``name``, ``driver``, ``scope``. (+2 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.13
Nodes (34): CheckResult, HTTPMonitorTransport, Deterministic fake checker for ``sim://`` monitors and demo environments.…, Real HTTP(S) probe using httpx with per-monitor settings. Redirects are…, SimulatedTransport, _check(), clock(), FakeClock (+26 more)

### Community 42 - "test_migration_phase5212.py"
Cohesion: 0.16
Nodes (22): _columns(), Phase 5.2.1.2 migration (`a7b8c9d0e1f2`): the envelope leaves…, ``column -> (data_type, is_nullable)`` for *table*., ``(org_id, ciphertext, generation)`` for every populated envelope, ordered., The move creates rows only where there was key material. A row with a NULL…, Two envelopes for one tenant are refused by the database, not by a service., F3: a negative generation, and either half of an inconsistent pair, fail. The…, The reversal is a data move in the other direction, and it is reversible.… (+14 more)

### Community 43 - "client.ts"
Cohesion: 0.04
Nodes (54): API_BASE, ApiError, apiRequest(), buildUrl(), extractError(), getActiveOrgId(), ORGANIZATION_HEADER, OrgListener (+46 more)

### Community 44 - "project_service.py"
Cohesion: 0.13
Nodes (45): DeploymentEnvironment, A **project-scoped** deployment environment (Phase 2 promotion). The…, ProjectCreate, Payload to create a project; owner defaults to the caller., actor_of(), _apply_update(), _check_server(), create_application() (+37 more)

### Community 45 - "test_permissions.py"
Cohesion: 0.09
Nodes (19): permission_exists(), PermissionSpec, Permission registry and role matrix. Permissions are *data*: the registry below…, User, _auth_context(), _FakeCtx, Unit tests for the permission registry, scope matching and RBAC gate., Duck-typed stand-in for AuthContext. (+11 more)

### Community 46 - "test_kek_health_api.py"
Cohesion: 0.11
Nodes (21): Drop every cached verdict (tests, and any future configuration reload)., reset_health_cache(), _clear_health_cache(), fixture, MonkeyPatch, parametrize, Provider health on the readiness surface, seen through the API. The approved…, A probe is unauthenticated in most deployments; it must leak nothing. (+13 more)

### Community 47 - "test_phase3_nodes.py"
Cohesion: 0.15
Nodes (33): _create_token(), _dispatch(), _enroll(), _enrolled_node(), _load_agent_module(), _mutate_in_system_scope(), Phase 3 — Nodes & Agent v2 end-to-end behaviour. Grouped by the question each…, Import the shipped agent source (sync, so async tests never touch Path). (+25 more)

### Community 48 - "UnprocessableEntity"
Cohesion: 0.11
Nodes (38): UnprocessableEntity, assert_safe_tcp_endpoint(), assert_safe_url(), _raise_block(), Validate *url* for outbound requests; return the parsed URL or raise 422.…, Validate a ``tcp://`` docker host endpoint for outbound connection. Docker…, Reject non-empty values that are not valid IPv4/IPv6 addresses., _validate_ip() (+30 more)

### Community 49 - "test_ws_hub.py"
Cohesion: 0.14
Nodes (25): _connection(), _drain(), _event_frame(), _fake_sessionmaker(), _FakeSession, hub(), _Org, Any (+17 more)

### Community 50 - "update_role"
Cohesion: 0.19
Nodes (15): create_role(), delete_role(), CurrentUser, DbSessionDep, patch, post, Request, UUID (+7 more)

### Community 51 - "docker_host_service.py"
Cohesion: 0.14
Nodes (33): DockerHostStatus, DockerHost, DockerHostPingOut, Result of probing a host's provider endpoint., _assert_endpoint_allowed(), _assert_name_free(), create_host(), delete_host() (+25 more)

### Community 52 - "proxy_service.py"
Cohesion: 0.06
Nodes (86): ListenerOwnership, ProxyApplyOutcome, Terminal outcome of one ``nginx.apply`` operation on a node., Who holds one required listener port, per the node's pre-flight. The…, Server, bundle_summary(), Bounded, human-readable bundle metadata for audit rows and UI. Never includes…, NodeProxyCapabilityOut (+78 more)

### Community 53 - "VaultTransitKEKProvider"
Cohesion: 0.05
Nodes (49): AsyncBaseTransport, The deterministic in-process provider — tests and explicitly configured dev.…, _construct(), Provider construction — the only place a ``KEKProvider`` is ever created. One…, Provider health, cached, for the readiness surface. Health is the one place a…, KEKConfigurationError, KEKContextMismatchError, KEKEnvelopeError (+41 more)

### Community 54 - "update_organization"
Cohesion: 0.13
Nodes (18): create_organization(), list_my_organizations(), CurrentUser, DbSessionDep, get, IdentityUser, patch, post (+10 more)

### Community 55 - "test_agent_nginx_contract.py"
Cohesion: 0.07
Nodes (57): CapabilityReport, One node-reported capability. ``present`` defaults to false, and a capability…, _agent_bundle(), agent_fixture(), _bootstrap_fixture(), _load_agent(), Any, fixture (+49 more)

### Community 56 - "UserOut"
Cohesion: 0.16
Nodes (22): create_user(), deactivate_user(), get_user(), list_users(), CurrentUser, DbSessionDep, get, patch (+14 more)

### Community 57 - "alembic"
Cohesion: 0.12
Nodes (6): alembic, Fix pre-existing model/migration drift (surfaced by the new drift check). Two…, downgrade(), Phase 2.2 — make legacy environment typing match the documented precedence. The…, No-op: the correction is a classification, not a reversible structure.…, sqlalchemy_dialects

### Community 58 - "notification_service.py"
Cohesion: 0.05
Nodes (93): create_channel(), delete_channel(), get_channel(), list_channels(), list_deliveries(), DbDep, Depends, get (+85 more)

### Community 59 - "helpers.py"
Cohesion: 0.07
Nodes (47): owner(), AsyncClient, A second organization the owner also belongs to. Both tenants are owned by the…, Bootstrap owner credentials for this test (fresh DB => first user). ``headers``…, second_org(), bearer(), cookie_attributes(), error_of() (+39 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "_list_deployments"
Cohesion: 0.10
Nodes (35): cancel_deployment(), _emails_for(), get_deployment(), list_application_deployments(), _list_deployments(), _parse_sort(), _parse_statuses(), alias (+27 more)

### Community 62 - "test_error_logging.py"
Cohesion: 0.22
Nodes (4): Regression: the catch-all 500 handler must not log raw exception text.…, _SpyLogger, test_unhandled_exception_handler_logs_class_not_message(), fastapi_testclient

### Community 63 - "dns_verifier.py"
Cohesion: 0.10
Nodes (26): _aggregate_answers(), _ask_one(), discover_authoritative_nameservers(), _discover_nameservers(), _normalise_ns(), observe(), observe_txt_record(), public_addresses() (+18 more)

### Community 64 - "test_phase2_environments.py"
Cohesion: 0.18
Nodes (22): _environment(), _project(), parametrize, Phase 2: project-scoped environments, config layering, and their isolation. The…, Uniqueness is ``(project_id, slug)`` — not instance-wide., The update path is validated too (the pre-Phase-2 gap)., Knowing an environment UUID is not access: the project link must hold., Another tenant cannot reach the project, its environments, or its detail. (+14 more)

### Community 65 - "route_service.py"
Cohesion: 0.07
Nodes (78): create_route(), delete_route(), disable_route(), _domain_status(), enable_route(), get_route(), list_routes(), AsyncSession (+70 more)

### Community 66 - "test_schema_redaction.py"
Cohesion: 0.18
Nodes (17): is_sensitive_header(), mask_sensitive_headers(), True when *name* looks like it carries a credential (Authorization etc.)., Return a copy of *headers* with sensitive values replaced by a mask., mask_target(), Human-readable masked target safe to expose over the API. For webhook families…, _monitor_out(), Outbound-schema redaction: monitor probe credentials and webhook targets.… (+9 more)

### Community 67 - "publish"
Cohesion: 0.15
Nodes (20): create_api_key(), AsyncSession, Request, UUID, Revoke a key owned by *owner_id*. Foreign keys look like NotFound (no leak)., Revoke every live key of a user (used on deactivation). Returns count., Create a key for *user_id*. Returns ``(row, raw_key)`` — raw shown once. The…, revoke_all_for_user() (+12 more)

### Community 68 - "login_account"
Cohesion: 0.12
Nodes (31): login_account(), Login and unpack tokens, the raw cookie header and the user object., A fresh, deliverable-shaped address unique to a single test. ``example.com`` is…, unique_email(), _latest_audit(), _latest_event(), _list_ids(), Any (+23 more)

### Community 69 - "seed.py"
Cohesion: 0.18
Nodes (20): generate_agent_token(), A per-node credential (``nxa_``): long-lived, node-scoped, never shared., _lock(), _organization_name(), _organization_slug(), datetime, User, Idempotent demo seed: roles, admin user, simulated fleet, monitors, history.… (+12 more)

### Community 70 - "core/tenancy.py"
Cohesion: 0.11
Nodes (25): _apply_scope_guc(), _desired_guc(), _guard(), _has_org_predicate(), _mappers_of(), org_scoped_table_names(), Any, Tenancy core: organization scope, the session guard and the RLS GUC. Everything… (+17 more)

### Community 71 - "test_secrets.py"
Cohesion: 0.10
Nodes (26): decrypt_str(), _fernet(), _create(), _environment_config(), Secrets: metadata-only reads, rotation versioning, deploy-time resolution., Project → application → environment carrying *config*; returns its id., A reference naming no secret must abort, not resolve to an empty value.…, A row this ENCRYPTION_KEY cannot decrypt must abort, not yield ``""``. (+18 more)

### Community 72 - "test_nginx_renderer.py"
Cohesion: 0.12
Nodes (38): NginxProvider, ValueError, The only production provider in Phase 4., Where a route's fragment lands, so the service can name it in events., Rendering refused the input. Always a bug or a corrupt row, never a leak., RenderError, NginxApplyParams, One validated bundle to apply atomically. (+30 more)

### Community 73 - "domains.py"
Cohesion: 0.05
Nodes (74): create_domain(), delete_domain(), _enqueue_verification(), get_domain(), list_domain_routes(), list_domains(), _project_names(), alias (+66 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "monitor_service.py"
Cohesion: 0.08
Nodes (74): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+66 more)

### Community 76 - "typing"
Cohesion: 0.05
Nodes (95): permission_dep(), Any, FastAPI dependencies: database session, authenticated tenant context, RBAC…, Dependency factory enforcing a permission; returns 403 when denied., require_permission(), Agent ingest endpoints: enrollment, hello, heartbeat, and operation traffic.…, list_alerts(), Depends (+87 more)

### Community 77 - "test_acme_accounts.py"
Cohesion: 0.11
Nodes (42): account_for(), account_key_fingerprint(), find_account(), Request, UUID, Fingerprint the **public** half of a PEM account key. Over the public key…, The organization's account at *directory*, if it has one. Read-only., The organization's account at *directory*, created on first use. Creating the… (+34 more)

### Community 78 - "ssrf.py"
Cohesion: 0.11
Nodes (25): assert_safe_url_async(), _is_forbidden_address(), is_simulation_url(), ValueError, SSRF guard applied to every operator-supplied outbound URL. Monitors and…, Async wrapper around :func:`assert_safe_url`; DNS runs off the loop., True when *url* targets the built-in simulated checker (``sim://``)., Internal signal: a specific SSRF rule matched (never shown to clients). (+17 more)

### Community 79 - "test_phase2_secrets.py"
Cohesion: 0.19
Nodes (21): _env(), _project(), Phase 2 secrets: layered scope, immutable versions, rollback, isolation. Two…, Two racing rotations must both be kept and never share a version number., Another tenant cannot read, rotate, roll back or even enumerate the secret., The documented example: same key at three scopes; most specific wins., A ref declared in the project base config resolves for its environments., _resolved() (+13 more)

### Community 80 - "RolesPage.tsx"
Cohesion: 0.18
Nodes (9): RolesPage, describeError(), GROUP_STYLE, LEGEND_STYLE, OPTION_STYLE, PermissionSpec, roleAllows(), RoleForm (+1 more)

### Community 81 - "test_schemas_server.py"
Cohesion: 0.21
Nodes (22): Payload for registering a server., Partial update. ``tags`` replaces the full set when provided., ServerCreate, ServerUpdate, _base(), parametrize, Unit tests for app.schemas.server (validation only, no I/O)., test_empty_ip_is_allowed_but_whitespace_collapses() (+14 more)

### Community 82 - "InvalidName"
Cohesion: 0.08
Nodes (47): _canonicalize(), canonicalize_name(), canonicalize_path(), canonicalize_record_name(), _check_labels(), _check_not_ip(), hostname_is_covered(), _idna() (+39 more)

### Community 83 - "tests/conftest.py"
Cohesion: 0.25
Nodes (6): configure_test_env(), Test bootstrap: pin every cached setting BEFORE the first ``app`` import. The…, KEY=VALUE pairs from the repo .env (first definition wins); never logged., Export the exact settings the app caches; host values cannot leak through., _read_dot_env(), os

### Community 84 - "server_service.py"
Cohesion: 0.05
Nodes (79): agent_heartbeat(), Response, Ingest one metrics sample and hand the agent its next work. A protocol-1 agent…, server_metrics_channel(), ContainerHealth, ServerStatus, AgentCredential, Container (+71 more)

### Community 85 - "user_service.py"
Cohesion: 0.06
Nodes (80): _check(), list_sessions(), CurrentUser, DbSessionDep, get, Request, UUID, Active sessions of this organization's members. Defaults to the caller's own;… (+72 more)

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "NotFound"
Cohesion: 0.08
Nodes (55): Conflict, NotFound, OperationStatus, Lifecycle of one node operation (node-agent-architecture.md §5.1).…, Operation, Whether the agent reported this operation as successful. A terminal check, not…, One whitelisted action for one node, with a CAS lifecycle. ``attempts`` is…, _active_org() (+47 more)

### Community 88 - "test_certificate_lifecycle.py"
Cohesion: 0.08
Nodes (32): material_guard_predicate(), The SQL of ``ck_certificate_generations_material_guard``. Derived from the enum…, can_transition(), coerce_state(), The enum member for *value*, or ``None`` when it names no state at all., Whether *current* may move to *target*., The target state, or :class:`InvalidTransition` when the move is illegal., require_transition() (+24 more)

### Community 89 - "test_payload_crypto.py"
Cohesion: 0.12
Nodes (36): decrypt(), decrypt_str(), encrypt(), PayloadDecryptionError, Fernet, Fernet refused the token: the key is wrong or the bytes were altered. Distinct…, Encrypt *payload* for *context* and return the storable value. The plaintext is…, Return the payload *stored* holds for *context*, or raise. Fails closed in… (+28 more)

### Community 90 - "DomainStatus"
Cohesion: 0.12
Nodes (30): DomainStatus, Ownership-verification lifecycle of a Domain (domain-routing.md §4). ``STALE``…, The state a domain flip forces on its routes, or ``None`` to leave them., route_config_state_for(), The honest state of a route that left the desired tree but is not gone. One…, removal_requested_detail(), _affected_node_ids(), _announce() (+22 more)

### Community 91 - "dns_provider_service.py"
Cohesion: 0.03
Nodes (119): create_dns_provider(), delete_dns_provider(), get_dns_provider(), list_dns_providers(), DbDep, Depends, get, ManageCtx (+111 more)

### Community 92 - "mark_all_read"
Cohesion: 0.23
Nodes (12): mark_all_read(), mark_read(), CurrentUser, DbDep, get, post, UUID, Mark every unread alert read; returns how many rows changed. (+4 more)

### Community 94 - "test_phase21_secret_version_integrity.py"
Cohesion: 0.18
Nodes (18): _app_role_dsn(), _owner_dsn(), _probe(), Phase 2.1 — ``secret_versions`` is append-only in the **database**, not just in…, Immutability is a database guarantee, not merely a missing code path. The owner…, The legitimate append paths keep working under the guard., The documented deletion policy: purging a Secret cascades its history., RLS is preserved: another tenant cannot see a version row, even by id. (+10 more)

### Community 95 - "test_dns_propagation.py"
Cohesion: 0.17
Nodes (22): evaluate(), Fold one round of observations into ``(ok, status, detail)``. **Pure.** ``ok``…, _ok(), parametrize, Unit tests for the DNS propagation wait. Publishing a record is not the same…, The defect this policy closes: one server's positive answer is not a verdict.…, A per-server observation, exactly what ``observe_txt_record`` returns., _servers() (+14 more)

### Community 96 - "NexusOps (self-hosted infrastructure management and monitoring platform)"
Cohesion: 0.20
Nodes (10): mailpit service (dev SMTP sink + web UI :8025), NexusOps compose stack (8 services on one network), HIGH finding: redirect-following SSRF in uptime monitors (fixed: follow_redirects=False + per-hop guard), SSRF guard (assert_safe_url, per-redirect-hop validation, assert_safe_tcp_endpoint), Mailpit SMTP port internal-only (host-side injection needs extra mapping), Host port knobs (NEXUSOPS_HTTP_PORT/POSTGRES/REDIS/MAILPIT/VITE), SPA entry point (loads /src/main.tsx, dark color-scheme), Uptime monitors -> incidents -> notifications flow (+2 more)

### Community 97 - "REST API surface (/api/v1)"
Cohesion: 0.29
Nodes (7): Cursor (keyset) and offset pagination envelopes, Permission model (data-driven registry, require_permission, wildcard scopes), REST API surface (/api/v1), RBAC registry (PERMISSIONS + ROLE_MATRIX + scope_matches), Adding a new resource: 7-step checklist (model -> migration -> schemas -> service -> router -> tests -> frontend), Alembic migration workflow (autogenerate, models __init__ export, entrypoint apply), Command palette (Ctrl/Cmd+K)

### Community 98 - "fixtures.ts"
Cohesion: 0.23
Nodes (11): EDGE, MAILPIT, ADMIN, Bootstrap, bootstrapVia(), test, ADMIN, openProject() (+3 more)

### Community 99 - "test_org_dek_envelope.py"
Cohesion: 0.08
Nodes (70): install_tenancy_guards(), Attach the guard and the GUC writer to the ORM session class. Idempotent, and…, org_dek(), Fernet, Yield the organization's DEK for **one operation**, then drop it. The key-only…, db(), A session with **no** tenant scope. Deliberately unscoped: it is how a test…, org_id() (+62 more)

### Community 100 - "redact_mapping"
Cohesion: 0.06
Nodes (51): configure_logging(), _is_sensitive_key(), _orjson_dumps(), Any, Return a copy of *data* with sensitive values replaced, at any depth. Two…, structlog processor: scrub one record before anything renders it. The pipeline…, Configure structlog + stdlib logging once at process start. Everything…, Substring match on a normalised key so header-style names are caught too.… (+43 more)

### Community 101 - "DeterministicKEKProvider"
Cohesion: 0.04
Nodes (63): _derive(), DeterministicKEKProvider, A per-(binding, key version) key: HKDF-style derivation. Two properties, both…, Deterministic wrap/unwrap/rewrap over an in-process AEAD., Bump the modelled KEK version, so a test can prove rewrap moves it., EncryptionContext, What a wrapped DEK is bound to. Frozen: a context is not edited in place., The canonical, unambiguous binding string. Field order and separator are fixed… (+55 more)

### Community 102 - "payload_crypto.py"
Cohesion: 0.14
Nodes (19): fingerprint(), _parse_header(), PayloadContextMismatch, PayloadEnvelopeError, PayloadError, RuntimeError, UUID, Payload encryption under the organization DEK (Phase 5.2.2). Three Phase-5… (+11 more)

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
Cohesion: 0.10
Nodes (40): ``Base.metadata`` and the migrated database must describe the same schema., test_models_and_migrations_do_not_drift(), _columns(), _foreign_keys(), _indexes(), _insert_certificate(), _insert_generation(), _integrity_error() (+32 more)

### Community 108 - "v1/auth.py"
Cohesion: 0.21
Nodes (13): Authentication routes: register, login, refresh rotation, logout, me, password., LoginRequest, MeOut, PasswordChangeRequest, Authentication request/response schemas., Optional body for non-browser clients; the cookie takes precedence., Token response, plus everything a client needs to pick an organization. The JWT…, Caller identity, their organizations, and their authority in the active one.… (+5 more)

### Community 109 - "Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)"
Cohesion: 0.25
Nodes (9): API keys (X-API-Key, nxo_..., scope intersection), First boot sequence (api entrypoint migrates, compose never seeds), Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test), Makefile workflows (up/test/lint/typecheck/migrate/seed), HIGH finding: API-key scope bypass for superadmin-owned keys (fixed: scope intersection first), Security audit 2026-09 (26 raw findings -> 20 confirmed, all fixed), HIGH finding: known seed superadmin + API key backdoor (fixed: NEXUSOPS_ALLOW_SEED opt-in, one-time password), Threat model (edge attacker, malicious agent, curious operator, leaked token, SSRF) (+1 more)

### Community 110 - "UpstreamContainerOut"
Cohesion: 0.20
Nodes (11): One genuinely usable published port reported by the node's agent., A container that can actually back a route on this node., UpstreamContainerOut, UpstreamPortOut, container_out(), The address nginx should proxy to for one published binding. A wildcard bind…, The published ports of *container* that a route may actually point at. Honest…, Containers on *node_id* that can back a route, for the route editor. (+3 more)

### Community 111 - "run_async"
Cohesion: 0.04
Nodes (79): flush_pending_publishes(), Wait for frames scheduled by ``after_commit`` hooks to reach Redis. The commit…, Celery application: periodic cadences live here, dynamic work is claimed…, issue_certificate(), _run(), _order_ttl_seconds(), task, Certificate issuance tasks: one worker per generation, plus the due sweep. The… (+71 more)

### Community 112 - "middleware.py"
Cohesion: 0.13
Nodes (17): ASGIApp, AccessLogMiddleware, HTTP middleware: request ids, security headers, structured access logs., Baseline hardening headers on every API response., RequestIDMiddleware, SecurityHeadersMiddleware, create_app(), _include_routers() (+9 more)

### Community 113 - "dnsmock.py"
Cohesion: 0.09
Nodes (33): resolver(), answer(), encode_name(), encode_txt(), forward(), in_zone(), main(), _nameservers() (+25 more)

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "login"
Cohesion: 0.21
Nodes (19): change_password(), _clear_refresh_cookie(), _cookies_secure(), login(), logout(), DbSessionDep, IdentityUser, post (+11 more)

### Community 116 - "test_tenancy_allowlist.py"
Cohesion: 0.20
Nodes (14): AST, _actual_callers(), _calls_system_scope(), _module_path(), Path, The system-scope allowlist is the only fence around the tenancy carve-out.…, Every module that could open a system scope: ``app/`` plus the scripts., No module may lift tenant isolation without being named in the list. (+6 more)

### Community 117 - "test_migration_phase2.py"
Cohesion: 0.07
Nodes (35): alembic_config, alembic_script, Phase 2.1 corrective migration: legacy ``environment_type`` classification.…, Every case is classified as documented, ids and ownership intact., An explicit non-DEV classification survives the corrective migration. The…, The correction is part of ``head`` and adds no extra Alembic head., Insert one legacy environment per case, in two organizations., _seed_typed_environments() (+27 more)

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
Nodes (7): BaseHTTPRequestHandler, clear_record(), ControlHandler, Remove the whole name, one record type, or **one value** of a type. The value-…, The journey's only way to publish a record — no shell, no shared volume., set_record(), snapshot()

### Community 122 - "test_tenant_isolation.py"
Cohesion: 0.04
Nodes (63): A valid POST /servers body with per-test overrides., server_payload(), test_token_cannot_claim_a_foreign_tenants_node(), test_v1_heartbeat_keeps_the_204_contract(), Regression: a superadmin-owned key is still limited to its scope list. The…, test_scoped_api_key_cannot_exceed_its_grant(), _create_server(), Server CRUD, cascade delete, audit trail rows and audit immutability. (+55 more)

### Community 123 - "_run_migration"
Cohesion: 0.14
Nodes (17): Upgrade ``database`` to ``revision``., A fresh database reaches the same shape the models describe., _run_migration(), test_migration_from_zero_matches_the_models(), Phase 3 migration (``a1b2c3d4e5f6``) against realistic legacy data. Phase 3 is…, A fresh database reaches the same shape the models describe., Phase 3 adds one migration; heads must not fork., The pre-Phase-3 shapes: a node with telemetry, and operation history. (+9 more)

### Community 124 - "test_dns_providers.py"
Cohesion: 0.07
Nodes (52): _audits(), cloudflare(), _create(), _create_domain(), _created(), _dns_stub(), _events(), _fake_observe() (+44 more)

### Community 125 - "OperationError"
Cohesion: 0.13
Nodes (19): _demux_docker_stream(), _docker_error(), execute_operation(), OperationError, _process_pending_operations(), Exception, A stable, sanitized failure contract for the control plane., Re-validate the operation's parameters locally, against a closed shape. (+11 more)

### Community 126 - "list_operations"
Cohesion: 0.14
Nodes (22): cancel_operation(), create_operation(), get_operation(), list_operations(), DbDep, Depends, get, post (+14 more)

### Community 127 - "test_tasks_util.py"
Cohesion: 0.36
Nodes (8): _answer(), _boom(), _nested(), Unit tests for the Celery-task async bridge (pure asyncio, no broker)., test_run_async_awaits_nested_coroutines(), test_run_async_is_repeatable_per_invocation(), test_run_async_propagates_exceptions(), test_run_async_returns_coroutine_result()

### Community 137 - "ProjectDetailPage.tsx"
Cohesion: 0.08
Nodes (30): apiPatch(), ApplicationOut, DockerHostOut, ENVIRONMENT_TYPE_LABELS, EnvironmentType, ProjectDetailPage, configToText(), parseConfigText() (+22 more)

### Community 146 - "certificate_issuance.py"
Cohesion: 0.04
Nodes (81): AcmeSession, One attempt's conversation with a CA, for one account. Method calls are…, Register (or discover) this account and return its CA-side URL (``kid``)., Tell the CA a challenge is ready to be validated., Drop the account key and any transport state this session held., _actor(), _Attempt, _AttemptFailure (+73 more)

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
Cohesion: 0.11
Nodes (20): _listener_ownership(), _listening_ports(), _live_bundle_id(), _live_files(), _nginx_binary(), nginx_capability(), _nginx_owned_ports(), _nginx_status() (+12 more)

### Community 153 - "types.ts"
Cohesion: 0.04
Nodes (55): AlertOut, CapabilityReport, ChannelOut, ContainerOut, DeliveryOut, DeploymentLogLine, DeploymentStatus, DomainDetailOut (+47 more)

### Community 154 - "nexusops-draft.mjs"
Cohesion: 0.40
Nodes (4): DOCS, meta, SPINE, VERIFY_RULES

### Community 155 - "rollback_secret"
Cohesion: 0.16
Nodes (22): create_secret(), delete_secret(), get_secret(), list_secret_versions(), list_secrets(), DbSession, get, PageParamsDep (+14 more)

### Community 156 - "nexusops-challenge.mjs"
Cohesion: 0.33
Nodes (5): CHALLENGE_COMMON, meta, RESEARCH_COMMON, SCHEMA, TASKS

### Community 157 - "Secrets Architecture"
Cohesion: 0.14
Nodes (14): 10. Resolution flow at deploy time, 2.1 Resolution runs inside org scope, 2.2 Migration mapping (applied by `b2c3d4e5f6a7`), 2. Scope model (org / project / environment layering) — **shipped**, 3.1 What this fixed, 3. SecretVersion — append-only history (**shipped in Phase 2**), 4.1 Audit event at resolution time, 4. Resolution authorization (+6 more)

### Community 158 - "test_schemas_agent.py"
Cohesion: 0.11
Nodes (35): AgentContainerIn, AgentHeartbeatIn, AgentHelloIn, Any, field_validator, Observed container state reported by an agent., Periodic metrics + observed containers from an enrolled agent. Network counters…, First contact from an agent after enrollment; fills static host facts. (+27 more)

### Community 159 - ".state"
Cohesion: 0.07
Nodes (34): computed_field, Derived lifecycle state: revoked wins over used wins over expired., 1.2 Phase 5 in one sentence, 1.3 Trust boundaries Phase 5 adds, 1.4 Non-goals for Phase 5, 1.5 Trust concentration: centralized key custody, accepted **conditionally** (decided), 1. Architecture and trust boundaries, 2.1 The six stages, kept distinct (+26 more)

### Community 160 - "test_kek_vault_transit_live.py"
Cohesion: 0.07
Nodes (44): _ca_context(), _configure(), _ctx(), _docker(), _free_port(), LiveVault, CompletedProcess, fixture (+36 more)

### Community 161 - "alert_service.py"
Cohesion: 0.20
Nodes (14): create_alert(), get_alert(), mark_all_read(), mark_read(), AsyncSession, UUID, Alert inbox: insert-only creation plus read/unread bookkeeping., Map a system event type to the alert severity it deserves. (+6 more)

### Community 162 - "decide"
Cohesion: 0.20
Nodes (20): decide(), matches_token(), What the lifecycle should do with an observation., Constant-time comparison of the observed TXT values against the token. TXT…, Turn one observation into the verification outcome — pure, no I/O.…, VerificationDecision, observation(), parametrize (+12 more)

### Community 163 - "RouteHeader"
Cohesion: 0.10
Nodes (11): field_validator, model_validator, RateLimit, One header a route adds. ``target`` says where it lands., One route's request-rate ceiling (rendered as a ``limit_req_zone``)., A fixed host redirect. Phase 4 cannot express a scheme change here. There is…, RouteHeader, RouteRedirect (+3 more)

### Community 164 - "AgentClient"
Cohesion: 0.15
Nodes (8): AgentClient, _docker_raw(), SSLContext, A verifying TLS context. Verification is never disabled. A private/self-hosted…, Refuse to send credentials over plain HTTP to a non-loopback server. The…, One raw Docker API call; returns ``(status, body_bytes)``., _tls_context(), _UnixHTTPConnection

### Community 165 - "test_kek_selection.py"
Cohesion: 0.06
Nodes (53): build_kek_provider(), Drop the cached provider (tests, and any future configuration reload)., Return the configured provider, or raise naming exactly what is wrong., reset_kek_provider(), provider_health(), The configured provider's health, at most one probe per cache window., _clean_provider_cache(), fixture (+45 more)

### Community 166 - "nginx.py"
Cohesion: 0.13
Nodes (23): _header_lines(), _quote(), _rate_zone(), NginxProvider — a pure, deterministic renderer plus the two op wrappers.…, Validate the route's headers and split them by destination., Wrap an already-validated value in quotes for a template slot. Values reaching…, The ``limit_req_zone`` declaration for a rate-limited route., A fixed host redirect, or ``None`` for a normal proxying route. (+15 more)

### Community 167 - "Multi-Tenancy Architecture"
Cohesion: 0.14
Nodes (12): Whether the runtime connection is the RLS-enforced application role. False…, 10. Migration (Phase 1), 1. Tenancy invariants, 2.1 Org creation — v1 decision, 2. Org resolution on every request, 3. The session guard (the mechanical layer), 4. Background jobs, 6. Agents (+4 more)

### Community 168 - "_expectations"
Cohesion: 0.40
Nodes (6): _expectations(), One TXT expectation per record name the *current* order has to publish. Values…, _document_with(), An order document with ``(order_url, record_name, record_value)`` entries., test_expectations_group_shared_names_and_keep_both_values(), test_expectations_ignore_a_replaced_order_and_blank_entries()

### Community 169 - "pytest"
Cohesion: 0.16
Nodes (12): created_at server defaults must evaluate per insert, not at table creation., Regression: system_events and audit_logs shipped with DEFAULT 'now()' (quoted…, test_audit_and_event_created_at_defaults_are_dynamic(), UUID, Phase 2.2 — the environment-type correction follows the documented precedence.…, Only the previous migration's ``PROD`` output is corrected. A row already…, Create one legacy (application-scoped) environment per case., Every branch of the slug-first rule, end to end through ``head``. (+4 more)

### Community 170 - "test_agent_contract.py"
Cohesion: 0.20
Nodes (15): agent_fixture(), _load_agent(), _patch_stats(), Any, fixture, MonkeyPatch, Contract tests: the shipped agent's payloads must satisfy the ingest schemas.…, One-shot docker stats reduce to cpu/mem/limit fields the schema accepts, with… (+7 more)

### Community 171 - "test_kek_vault_transit.py"
Cohesion: 0.11
Nodes (47): _ctx(), _login_ok(), _provider(), parametrize, Request, Response, The Vault Transit adapter's HTTP contract, without a Vault. This module pins…, encrypt, decrypt *and* rewrap: the binding must survive a rotation. (+39 more)

### Community 172 - "monitor_transport.py"
Cohesion: 0.10
Nodes (20): CheckOutcome, coerce_headers(), _decode(), get_transport(), MonitorTransport, Any, BaseException, Protocol (+12 more)

### Community 173 - "me"
Cohesion: 0.25
Nodes (8): me(), get, The caller's identity, organizations, and authority in the active one.…, effective_permissions(), permissions_for_role(), User, Sorted permission codenames a role grants; ``*`` expands to the registry.…, Instance-level permissions for a user (legacy default-role view). Deliberately…

### Community 174 - "_credential_seam"
Cohesion: 0.29
Nodes (7): _credential_seam(), _dns_stub(), _fake_observe(), _FakeCloudflare, fixture, MonkeyPatch, The credential side of the DNS seam, for creating a provider through the API.

### Community 175 - "journey.spec.ts"
Cohesion: 0.29
Nodes (4): ADMIN, formLogin(), uiGoto(), UNIQUE

### Community 176 - "Platform Security Model — NexusOps"
Cohesion: 0.12
Nodes (16): 10.1 Node revocation playbook (compromised node / leaked agent token), 10.2 Key compromise playbook, 10. Incident response, 1. Scope, stance, and simulation honesty, 2. Assets, 3. Trust boundaries, 4. Tenant isolation model (summary), 5.1 Threat model table (+8 more)

### Community 177 - "Node & Agent Architecture"
Cohesion: 0.08
Nodes (25): install_hint(), The one-liner an operator pastes, without the raw token in argv. The token…, 1. Scope and stance, 3.2 Enrollment v2, 3.3 Token storage & rotation with dual-token grace, 3.4 Revocation semantics — fixing the 401 hot-loop, 3.5 Reconnect / offline states, 3. Agent lifecycle (+17 more)

### Community 178 - "main"
Cohesion: 0.11
Nodes (19): build_facts(), _build_hello_payload(), _enroll(), _interruptible_sleep(), main(), memory_total_mb(), network_rates(), network_total_bytes() (+11 more)

### Community 179 - "_node_session"
Cohesion: 0.12
Nodes (22): _dns_stub(), _fake_observe(), _hello_elsewhere(), _mark_reconcile_required_elsewhere(), _node_session(), _pause_render(), gated(), fixture (+14 more)

### Community 180 - "Domain"
Cohesion: 0.29
Nodes (6): Domain, One DNS name an organization is proving it controls. ``name`` is canonical (see…, is_serving(), Whether a domain's routes may be rendered/enabled right now., The exact record a domain manager must publish, or ``None``. ``None`` means…, verification_instructions()

### Community 181 - "_nginx_apply"
Cohesion: 0.12
Nodes (25): _fsync_dir(), _nginx_apply(), Materialize the bundle under ``staged/<id>/`` and return that directory.…, Build a self-contained config for ``nginx -t`` over the staged tree. The…, Move the staged tree over the live one, keeping the previous as backup., Put the previous known-good tree back. Returns whether it was possible., Stage → validate → swap → reload, with a rollback on a failed reload., Persist the last apply outcome atomically (temp + rename). (+17 more)

### Community 182 - "_rows"
Cohesion: 0.22
Nodes (17): Move ``database`` *back* to ``revision``. The same code path a deployment uses…, _rows(), _run_downgrade(), _columns(), Phase 5.2.1 migration (`f5a6b7c8d9e0`): two columns, one invariant, one…, The naming convention must not be applied twice. A fresh database is the only…, A ciphertext behind generation 0, and a generation with no material, both fail., The refusal is the point: a rollback must not delete key material. (+9 more)

### Community 183 - "list_events"
Cohesion: 0.22
Nodes (13): _decode_cursor(), _encode_cursor(), list_event_types(), list_events(), datetime, DbSession, Depends, get (+5 more)

### Community 184 - "UnrepresentableState"
Cohesion: 0.33
Nodes (5): InvalidTransition, ValueError, Two states with no legal move between them., A state the caller's context cannot accept. Two callers narrow differently and…, UnrepresentableState

### Community 185 - "20261012_1200-c8d9e0f1a2b3_phase5_certificate_metadata.py"
Cohesion: 0.23
Nodes (13): downgrade(), _drop_certificate_permissions(), _drop_tenant_policies(), _grant(), _in_list(), Phase 5.1 — certificate metadata and the pre-issuance lifecycle. Adds, in one…, Grant the app role on *table*; the migration role GUC carries the name. The…, The two-policy shape every tenant table uses: tenant + system scope. (+5 more)

### Community 186 - "apply_scope_to_session"
Cohesion: 0.04
Nodes (83): _load_organization(), membership_for_org(), Membership, Organization, The user's active membership in *org_id*, if any. This single indexed read is…, AppError, Exception, Base class for expected, client-facing errors. (+75 more)

### Community 187 - "test_schemas_search.py"
Cohesion: 0.33
Nodes (8): Results grouped per entity type, permission-filtered per caller. Every section…, SearchResultOut, Unit tests for global-search schemas., test_extra_fields_are_forbidden(), test_search_hit_requires_core_fields(), test_search_result_defaults_to_empty_sections(), test_search_result_exposes_exactly_the_documented_sections(), test_sections_hold_hits()

### Community 188 - "Deployment Architecture — NexusOps (target state)"
Cohesion: 0.18
Nodes (11): 10. Events and WS during runs, 12. Rollback semantics (existing behavior kept), 13. The simulated runner stays — labeled, 14. Open questions, 3. Target pipeline, 4. Runner registry — the DI fix, 6. Phased scope, 6a — Image-based deploys (Phase 3 ops framework is live; needs the deploy step stream) (+3 more)

### Community 189 - "phase3.spec.ts"
Cohesion: 0.15
Nodes (10): frontend_e2e_fixtures_expect, AGENT, NodeDetail, OperationRow, REPO_ROOT, ref_node_child_process, ref_node_fs, ref_node_os (+2 more)

### Community 190 - "Settings"
Cohesion: 0.11
Nodes (9): field_validator, model_validator, Username from :attr:`database_url`, or ``None`` if it is unparseable., Validated application settings (loaded from environment / .env)., Refuse a Vault address that carries userinfo (Phase 5.2.1.2, F4).…, Refuse to start with an ACME directory selection that is unsafe or ambiguous.…, Refuse to start with an unusable or unsafe key source. Two failures are worth…, Settings (+1 more)

### Community 191 - "TxtRecord"
Cohesion: 0.09
Nodes (11): One zone a credential can write in, as the provider names it., A reference to **one** TXT record this platform created. The reference, not the…, Create one TXT record and return its reference. Raises…, Every TXT record at *name* whose value equals *value*. The reconciliation…, TxtRecord, ZoneRef, One authoritative server's record store, through its control API., Drop every TXT record this view holds (setup, never an assertion). (+3 more)

### Community 192 - "env.py"
Cohesion: 0.28
Nodes (8): _database_url(), Alembic environment: metadata comes from app.models, URL from app settings., Migrations run as the table **owner**, never as the application role. The owner…, Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online(), logging_config

### Community 193 - "10. Implementation slices, acceptance criteria, tests, limitations"
Cohesion: 0.18
Nodes (11): 10.2 Test requirements (what "done" means per slice), 10.3.1 Approved decisions (previously open), 10.3.2 Known limitations (accepted, not blockers), 10.3.3 Open items and what they block now, 10.3 Decisions and known limitations, 10.4 Reserved-operation-type lists — one source of truth (required consolidation), 10.5.1 Migration (one, additive, `down_revision = c8d9e0f1a2b3`), 10.5.4 What each later step adds (and where it stays out of scope) (+3 more)

### Community 194 - "test_app_gating.py"
Cohesion: 0.44
Nodes (8): _app_for_environment(), MonkeyPatch, ENVIRONMENT gating contract: docs exposure and HSTS (see .env.example).…, create_app() with get_settings() patched to the given environment., test_non_production_does_not_emit_hsts(), test_non_production_keeps_docs_and_schema(), test_production_emits_hsts(), test_production_hides_docs_and_schema()

### Community 195 - "dek_envelope.py"
Cohesion: 0.10
Nodes (44): current_scope(), RuntimeError, Raised when a unit of work touches tenant data with no valid org scope. This is…, ``'org'``, ``'system'`` or ``'unset'``., ``before_flush`` handler: own new rows, and refuse rows that change hands.…, _stamp_org_on_flush(), TenancyScopeError, OrganizationDekEnvelope (+36 more)

### Community 196 - "certificate_service.py"
Cohesion: 0.09
Nodes (43): apex_of(), The name a wildcard Domain is anchored at (``*.example.com`` →…, CertificateChallengeType, CertificateKeyAlgorithm, How ownership of an identifier is proved to the CA. DNS-01 only in v1: it is…, The key type generated for a generation. Fixed in v1; never client-chosen., CertificateCreate, Payload for ``POST /certificates`` — a *request*, never an issuance.… (+35 more)

### Community 197 - "entries"
Cohesion: 0.10
Nodes (52): AcmeChallenge, One ``dns-01`` challenge, resolved to what has to be published. Every field is…, challenge(), cleanup_incomplete(), current_entries(), entries(), manual_instructions(), manual_pending() (+44 more)

### Community 198 - "20261014_1200-a7b8c9d0e1f2_isolate_org_dek_envelopes.py"
Cohesion: 0.23
Nodes (11): downgrade(), _drop_constraint(), _drop_tenant_policies(), _grant(), Phase 5.2.1.2 — the organization DEK envelope gets a tenant table of its own.…, Grant the app role the four DML verbs on *table*. Not ownership, and not…, Restore the envelope onto ``organizations`` — without losing any of it., Raw ``ALTER TABLE ... DROP CONSTRAINT``, as the tenancy migration does.… (+3 more)

### Community 199 - "20261010_1200-f4a5b6c7d8e9_phase4_domains_and_routes.py"
Cohesion: 0.31
Nodes (9): downgrade(), _drop_tenant_policies(), _grant(), _in_list(), Phase 4 — domains, routes and the routing schema. Adds, in one migration with a…, Grant the app role on *table*; the migration role GUC carries the name. The…, The two-policy shape every tenant table uses: tenant + system scope., _tenant_policies() (+1 more)

### Community 200 - "certificate_order.py"
Cohesion: 0.09
Nodes (32): attempt_in_flight(), begin_attempt(), challenge_ref(), finish_attempt(), _instant(), now_iso(), public_view(), datetime (+24 more)

### Community 201 - "_run"
Cohesion: 0.33
Nodes (7): _containers_for(), task, Deterministic smooth value in [base-amplitude, base+amplitude]., Stable per-server container set; one container cycles EXITED occasionally., simulation_tick(), _run(), _wave()

### Community 202 - "SimulatedDeploymentRunner"
Cohesion: 0.09
Nodes (49): LogLevel, _commit_short(), DeploymentRunner, _pace(), Exception, Protocol, Deployment runner port plus a faithful simulated implementation.…, Stream output lines for *step_name*; raise StepFailure to fail it. (+41 more)

### Community 203 - "ProxyProvider"
Cohesion: 0.33
Nodes (5): ProxyProvider, Any, Protocol, What ``app.services.proxy_service`` is allowed to assume about a provider. The…, 11. Post-deploy hooks

### Community 204 - "_LibrarySession"
Cohesion: 0.04
Nodes (48): AcmeOrder, AcmeProtocolError, AuthorizationState, IssuedChain, The response was not a well-formed ACME answer. A missing ``Location`` on an…, A fresh order and its authorizations, as public data., One authorization's status after a poll., What finalization returned: PEM chain text plus nothing else. The chain is… (+40 more)

### Community 205 - "enums.py"
Cohesion: 0.08
Nodes (68): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+60 more)

### Community 206 - "test_agent_ingestion.py"
Cohesion: 0.30
Nodes (10): _enrolled(), _heartbeat(), Agent ingest pipeline: hello, heartbeat, staleness transitions, events., A container absent from a later heartbeat is gone from the daemon., A payload at the agent's cap may be truncated — absence proves nothing., test_heartbeat_at_container_cap_skips_reconciliation(), test_heartbeat_removes_vanished_containers(), test_heartbeat_updates_status_metrics_and_containers() (+2 more)

### Community 207 - ".dispatch"
Cohesion: 0.60
Nodes (3): Request, Response, RequestResponseEndpoint

### Community 208 - "Hub"
Cohesion: 0.16
Nodes (15): _close_socket(), Connection, Hub, _org_id_from_frame(), _params_key(), Any, WebSocket, The organization the client asked this socket to act in, if well formed. (+7 more)

### Community 209 - "20261008_1200-b2c3d4e5f6a7_add_projects_and_environments.py"
Cohesion: 0.53
Nodes (5): downgrade(), _drop_constraint(), _quoted_list(), Phase 2 — projects & environments: env promotion, config, secret versions. This…, upgrade()

### Community 210 - "Certificate"
Cohesion: 0.12
Nodes (25): Certificate, CertificateGeneration, One requested certificate: an identity, its lifecycle view, no material., One ACME order + one key pair. Renewal inserts a new row, never mutates one.…, _flush_and_checkpoint(), IssuanceAttempt, issue_generation(), _publish_success() (+17 more)

### Community 211 - "20261014_1600-b8c9d0e1f2a3_phase522_providers_acme_material.py"
Cohesion: 0.21
Nodes (14): _assert_no_material(), downgrade(), _drop_constraint(), _drop_tenant_policies(), _grant(), _in_list(), Phase 5.2.2 — DNS credentials, ACME accounts, and the certificate material…, Raw ``ALTER TABLE ... DROP CONSTRAINT IF EXISTS``. ``op.drop_constraint`` is… (+6 more)

### Community 212 - "SystemEvent"
Cohesion: 0.15
Nodes (19): NotificationDelivery, SystemEvent, _create_monitor(), Monitor checks driving the full down -> incident -> recovery lifecycle., Regression: probe headers and URL query credentials never leave the API. Probe…, A monitor's checks, incidents and timeline all live in its organization, so the…, test_check_now_endpoint_runs_immediately(), test_down_then_recover_lifecycle() (+11 more)

### Community 213 - "_FakeAsyncClient"
Cohesion: 0.22
Nodes (3): _FakeAsyncClient, _FakeRequestObj, Scripted httpx.AsyncClient: responses keyed by absolute request URL.

### Community 214 - "20261009_1100-d4e5f6a7b8c9_correct_legacy_environment_types.py"
Cohesion: 0.33
Nodes (3): downgrade(), Phase 2.1 — correct legacy ``environment_type`` classification. The Phase 2…, No-op: the correction is a best-effort classification, not reversible.…

### Community 215 - "test_migration_drift.py"
Cohesion: 0.33
Nodes (5): alembic_autogenerate, alembic_migration, Model / migration drift: the schema in the database must match the models.…, The DB whitelist and ``OperationType`` are the same closed set. The migration…, test_operations_type_check_matches_the_enum()

### Community 216 - "README.md - NexusOps overview"
Cohesion: 0.32
Nodes (14): docker-compose.dev.yml - dev overlay, docker-compose.docker-sock.yml - docker socket override, docker-compose.yml - full stack definition, docs/agent.md - agent guide, docs/api.md - API guide, Append-only audit log (Postgres BEFORE UPDATE OR DELETE trigger), docs/architecture.md - system architecture, docs/deployment.md - deployment and operations guide (+6 more)

### Community 217 - "create_api_key"
Cohesion: 0.17
Nodes (16): create_api_key(), list_api_keys(), CurrentUser, DbSessionDep, get, post, Request, UUID (+8 more)

### Community 218 - "wait_for_txt_records"
Cohesion: 0.18
Nodes (14): Poll the authoritative servers until every value is visible, or the deadline.…, wait_for_txt_records(), _Clock, MonkeyPatch, A monotonic clock that only moves when something sleeps., test_observer_failure_becomes_a_dns_status_not_a_crash(), broken(), test_observer_window_converts_an_exception() (+6 more)

### Community 219 - "register"
Cohesion: 0.33
Nodes (6): _optional_actor(), AsyncSession, Bootstrap the first owner account or accept an authenticated invitation., Resolve credentials if presented; None for truly anonymous calls., register(), UserEnvelope

### Community 220 - "Platform Vision — NexusOps"
Cohesion: 0.20
Nodes (10): 1. Where NexusOps is today, 2.1 What we are NOT building, 2.2 The wedge (differentiation), 2. The direction, 3. Guiding principles, 4. Customer journey (target), 5.1 Architecture overview (target), 5. Control plane / data plane boundary (+2 more)

### Community 221 - "9. Renewal, expiration, ownership loss, removal, revocation"
Cohesion: 0.33
Nodes (6): 9.1 Renewal, 9.2 Expiration monitoring, 9.3 Ownership loss (a verified Domain changes owners), 9.4 Removal, 9.5 Revocation, 9. Renewal, expiration, ownership loss, removal, revocation

### Community 222 - "20260923_1000-c4e2a1f7b9d3_rename_server_codenames_to_node.py"
Cohesion: 0.60
Nodes (4): downgrade(), rename ``server.*`` permission codenames to ``node.*`` The Node/Server…, _rename_permissions(), upgrade()

### Community 223 - "CertificateGenerationState"
Cohesion: 0.10
Nodes (31): directory_required_predicate(), one_live_generation_predicate(), pre_issuance_predicate(), The SQL predicate of ``uq_cert_generations_one_live``. Built from…, The states in which a generation carries no material *by construction*.…, A generation that outlives the order must name the CA that issued it. The…, CertificateGenerationState, Lifecycle of one ACME order + key pair, pre- and post-issuance. **Phase 5.1… (+23 more)

### Community 224 - "certificate_lifecycle.py"
Cohesion: 0.14
Nodes (22): attempt_delay_seconds(), is_retryable(), is_terminal(), next_attempt_at(), datetime, The certificate lifecycle — pure decisions, no I/O, no side effects. The whole…, Whether a generation has spent every attempt it was allowed., Whether a failed generation may be moved back to ``ORDERING``. A failure is… (+14 more)

### Community 225 - "account_key"
Cohesion: 0.12
Nodes (18): account_key(), AcmeAccountKeyUnavailable, mark_used(), Any, AsyncSession, RuntimeError, Metadata for a log line, an audit entry or an event payload. An explicit…, Decrypt the account key **for one operation**, then drop it. INTERNAL USE ONLY… (+10 more)

### Community 226 - "20261012_1600-f5a6b7c8d9e0_phase5_org_dek_envelope.py"
Cohesion: 0.40
Nodes (3): downgrade(), Phase 5.2.1 — the organization DEK envelope. Two additive columns on…, Drop the envelope columns — unless doing so would destroy key material.

### Community 227 - "cloudflare"
Cohesion: 0.25
Nodes (6): cloudflare(), _FakeCloudflare, fixture, MonkeyPatch, Every test in this module gets the fake, and no test can reach the network., The credential seam: a verdict plus the zones the token can see.

### Community 228 - "record"
Cohesion: 0.13
Nodes (24): Any, AsyncSession, Request, UUID, Append an audit row using the caller's transaction (no commit here). The…, record(), create_role(), delete_role() (+16 more)

### Community 229 - "_validate_bundle"
Cohesion: 0.40
Nodes (5): _allowed_bundle_path(), The bundle fingerprint — byte-identical to the control plane's algorithm.…, Independently validate a bundle. Anything unexpected is refused., _tree_fingerprint(), _validate_bundle()

### Community 230 - "scope_matches"
Cohesion: 0.09
Nodes (23): Check an API-key scope list against a required permission. Supports exact match…, scope_matches(), parametrize, test_scope_matches_truth_table(), 0. What shipped (Phase 1), 1. Principles (already true in the codebase, kept), 2. Registry changes (Phase 1 + new subsystems), 3. The five system roles (target) (+15 more)

### Community 231 - "register_exception_handlers"
Cohesion: 0.24
Nodes (9): _error_payload(), Any, FastAPI, Request, register_exception_handlers(), handle_app_error(), handle_http_exception(), handle_unexpected() (+1 more)

### Community 232 - ".text"
Cohesion: 0.40
Nodes (4): The operator-facing one-liner stored in ``last_error``. Bounded., test_both_new_tables_carry_a_tenant_and_a_system_policy(), Catalog completeness: a new tenant table cannot ship unprotected. Compares the…, test_every_table_with_an_org_id_has_a_policy()

### Community 233 - "servers.py"
Cohesion: 0.07
Nodes (60): apply_node_proxy_config(), create_enrollment_token(), create_server(), delete_server(), _detail(), _enrollment_out(), get_server(), list_enrollment_tokens() (+52 more)

### Community 234 - "._route"
Cohesion: 0.20
Nodes (7): _frame_org(), _parse_payload(), Spawn the Redis fan-in listener (idempotent)., Deliver one Redis message to every matching subscription., The organization an event frame belongs to, or ``None`` when it has none., Decode a Redis-published body into a JSON-safe object., 5. WebSockets

### Community 235 - "Appendix A — Decisions resolved here (that certificate-management.md left open)"
Cohesion: 0.33
Nodes (6): Appendix A — Decisions resolved here (that certificate-management.md left open), Approved and recorded in the Phase 5.1 closeout (2026-10-12), Approved in the Phase 5.0 finalization (2026-10-12), Approved in the Phase 5.2 key-management decision gate (2026-10-12), Recorded in the Phase 5.3.1 verification (2026-10-18), Recorded in the Phase 5.3 closeout (2026-10-16)

### Community 236 - "report_operation_result"
Cohesion: 0.25
Nodes (11): agent_enroll(), agent_hello(), claim_operation(), DbDep, post, UUID, Redeem an enrollment token for a unique node credential. Transactional and…, First contact after enrollment: persist static host facts, negotiate cadence.… (+3 more)

### Community 237 - "projects.py"
Cohesion: 0.12
Nodes (47): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+39 more)

### Community 238 - "docker_real.py"
Cohesion: 0.09
Nodes (27): ContainerInfo, ContainerStats, Normalized view of a container as reported by any provider., Point-in-time resource usage snapshot., _as_float(), _compute_stats(), _cpu_percent(), _network_bytes() (+19 more)

### Community 239 - "enqueue_generation"
Cohesion: 0.50
Nodes (5): enqueue_generation(), _enqueue_issuance(), UUID, Hand one generation to the worker, but only once *db* commits. Inline is a…, Dispatch the worker task. Deliberately the only place that names it. Indirected…

### Community 240 - "_transport_is_https"
Cohesion: 0.50
Nodes (4): Whether this request's cookie will travel over https. The edge always…, _transport_is_https(), The Secure-cookie decision follows the wire, not the environment label.…, test_transport_is_https_decision()

### Community 241 - "instant_pacing"
Cohesion: 0.40
Nodes (4): instant_pacing(), fixture, MonkeyPatch, Remove the per-line sleeps; pacing bounds are asserted separately.

### Community 243 - "known_directory_urls"
Cohesion: 0.50
Nodes (4): directory_known_predicate(), known_directory_urls(), Every ACME directory URL a generation may record, from the vocabulary. Read…, ``directory_url`` is NULL or names a directory in the vocabulary. The ``NULL``…

### Community 245 - ".facts"
Cohesion: 0.50
Nodes (3): Alias for :attr:`extra`, so the API can expose open-ended agent facts. The…, 2.3 Infrastructure — Nodes, 2.1 Current shape (real)

### Community 246 - "_nginx_bootstrap"
Cohesion: 0.16
Nodes (16): _insert_http_includes(), _nginx_bootstrap(), _nginx_config_test(), _nginx_failure_summary(), _nginx_running(), _pid_alive(), Reload nginx via ``-s reload``, falling back to a SIGHUP of the master., Idempotent, minimal, reversible hook-up of the managed include. The only change… (+8 more)

### Community 247 - "KEKUnavailableError"
Cohesion: 0.20
Nodes (6): KEKUnavailableError, The provider could not be reached, or answered nothing usable in time., _FailingProvider, _FailingRewrapProvider, A provider that cannot wrap — the "Vault is down" path, exactly., Fails *only* ``rewrap_dek`` — a rotation that cannot reach its provider. The…

### Community 248 - "TxtObservation"
Cohesion: 0.17
Nodes (14): observe(), _observer_name(), observer_window(), Has the challenge record actually reached the authoritative nameservers?…, ``(satisfied, inconclusive, detail)`` for one name across every server seen.…, One round: observe every expected name. Returns the round and its elapsed time., Call *observer* for *name*, converting an unexpected exception into an…, _verdict() (+6 more)

### Community 249 - "resolve_secrets_for_environment"
Cohesion: 0.13
Nodes (19): Exception, A ``${secret:KEY}`` reference could not be resolved. Fail-closed. Carries…, One successfully resolved reference: metadata for audit, no value., Outcome of resolving an environment's config references., Resolve every ``${secret:KEY}`` reference an environment's config names.…, resolve_secrets_for_environment(), ResolvedSecrets, SecretReference (+11 more)

### Community 250 - "20260922_1000-a3f1c8d24b6e_add_tenancy_foundation.py"
Cohesion: 0.20
Nodes (12): _app_role_credentials(), _assert_fully_backfilled(), _backfill_org_ids(), _drop_constraint(), add tenancy foundation Phase 1 of the platform roadmap: organizations,…, Carry a value into a PL/pgSQL block. ``CREATE ROLE``/``ALTER ROLE`` are utility…, Application role name/password from settings (never hard-coded)., Point every pre-existing row at the bootstrap organization. ``audit_logs`` is… (+4 more)

### Community 251 - "7. Secure delivery of certificate material to authorized nodes"
Cohesion: 0.33
Nodes (6): 7.2 The mechanism: reference-only op + material in the claim response, 7.3 Authorization binding, 7.4 Derived (never configured) target set, 7.5 Recovery for an interrupted delivery, 7.6 Material never persists in ordinary data, 7. Secure delivery of certificate material to authorized nodes

### Community 252 - "test_event_registry.py"
Cohesion: 0.21
Nodes (8): event_type_catalogue(), is_known_event_type(), Canonical registry of system-event types. Single source of truth shared by…, Return True when *event_type* is part of the canonical registry., Serialise the registry for the ``/events/types`` endpoint., Registry coherence: schema-advertised event types must equal the canonical…, test_catalogue_serialises_every_entry(), test_known_event_lookup()

### Community 259 - "PayloadContext"
Cohesion: 0.33
Nodes (6): PayloadContext, What a ciphertext belongs to: organization, purpose, record and DEK generation.…, The canonical header string, used both outside and inside the token., Purpose, record and generation are all part of what the ciphertext belongs to.…, test_a_key_presented_under_another_context_is_refused(), read()

### Community 264 - "20261016_1000-c9d0e1f2a3b4_phase53_generation_directory.py"
Cohesion: 0.28
Nodes (7): _assert_no_directory_recorded(), downgrade(), _drop_constraint(), Phase 5.3 — the issuance provenance pair on ``certificate_generations``. Adds,…, Remove the provenance pair — refusing while any generation records a directory., Raw ``ALTER TABLE ... DROP CONSTRAINT IF EXISTS`` (see the 5.2.2 migration)., Refuse a downgrade that would discard which CA a generation was ordered at.

### Community 272 - "TxtExpectation"
Cohesion: 0.29
Nodes (5): One TXT record name and **every** value that must be present there. A set…, The expected values absent from *observed*, in expectation order., TxtExpectation, test_expectation_requires_a_name_and_a_value(), test_missing_from_strips_observed_values_and_keeps_expectation_order()

### Community 273 - "test_run_async_publishes_frames_scheduled_by_the_commit_hook"
Cohesion: 0.29
Nodes (5): _FakeDb, Stands in for an ``AsyncSession`` whose only job here is ``sync_session``. A…, The shape of a worker task whose last statement is a commit., test_run_async_publishes_frames_scheduled_by_the_commit_hook(), commit_then_return()

### Community 281 - "PropagationResult"
Cohesion: 0.50
Nodes (3): PropagationResult, What the authoritative servers said about a set of expectations. ``observed``…, The record names whose expectation is not satisfied yet. Judged exactly the way…

## Knowledge Gaps
- **486 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+481 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 3062 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **22 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `6. Tooling: reproducible e2e` connect `run_async` to `dek_envelope.py`, `ContainerDetailPage.tsx`, `NotFound`, `apply_scope_to_session`, `AuthContext`?**
  _High betweenness centrality (0.183) - this node is a cross-community bridge._
- **Why does `useEventStream()` connect `ContainerDetailPage.tsx` to `apiGet`, `App.tsx`, `client.ts`, `ServerDetailPage.tsx`, `run_async`, `@tanstack/react-query`?**
  _High betweenness centrality (0.183) - this node is a cross-community bridge._
- **Why does `TenancyScopeError` connect `dek_envelope.py` to `sqlalchemy`, `test_certificates.py`, `publish`, `test_org_dek_envelope.py`, `core/tenancy.py`, `log_service.py`, `test_tenant_isolation.py`, `assert_error_code`, `typing`, `test_acme_accounts.py`, `run_async`, `enrollment_service.py`, `test_phase4_routing.py`, `apply_scope_to_session`, `AuthContext`?**
  _High betweenness centrality (0.091) - this node is a cross-community bridge._
- **Are the 107 inferred relationships involving `AuthContext` (e.g. with `TenancyScopeError` and `MembershipStatus`) actually correct?**
  _`AuthContext` has 107 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `APIModel` (e.g. with `OperationSpec` and `test_specs_reject_unknown_params()`) actually correct?**
  _`APIModel` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `meta`, `SCHEMA`, `RESEARCH_COMMON` to the rest of the system?**
  _486 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `apiGet` be split into smaller, more focused modules?**
  _Cohesion score 0.05742574257425743 - nodes in this community are weakly interconnected._