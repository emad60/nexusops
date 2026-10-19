# Graph Report - nexusops  (2026-10-19)

## Corpus Check
- 412 files · ~540,069 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: (none) 10, .example 1, .service 1)

## Summary
- 8040 nodes · 23842 edges · 271 communities (248 shown, 23 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 1952 edges (avg confidence: 0.94)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5c1044a2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- apiGet
- test_certificates.py
- ApiKeysPage.tsx
- _verified_domain
- docker_host_service.py
- package.json
- resolve_client_ip
- _raw_probe
- App.tsx
- test_agent_v2.py
- assert_error_code
- ServerDetailPage.tsx
- APIModel
- client.ts
- validate_config
- test_certificate_manual_issuance.py
- deployment_engine.py
- SimulatedDockerProvider
- enrollment_service.py
- NotFound
- test_deployments_simulated.py
- container.py
- metrics_service.py
- get_settings
- Domain Routing — NexusOps
- test_phase4_routing.py
- Product Roadmap — NexusOps Multi-Tenant Platform
- test_agent_backoff.py
- certificate_issuance.py
- nexusops_agent.py
- test_certificate_pebble.py
- AuthContext
- AcmeDirectory
- test_rate_limit.py
- docker_hosts.py
- integration/test_certificate_issuance.py
- library.py
- v1/search.py
- enums.py
- typing
- DockerProvider
- test_monitor_transport.py
- _rows
- AuthContext.tsx
- project_service.py
- test_permissions.py
- ProviderHealth
- test_phase3_nodes.py
- test_ssrf.py
- test_ws_hub.py
- create_dns_provider
- AuthorizationState
- proxy_service.py
- DeterministicKEKProvider
- incident_service.py
- test_agent_nginx_contract.py
- .from_user
- alembic
- list_deliveries
- test_tenant_isolation.py
- compilerOptions
- _list_deployments
- fixture
- dns_verifier.py
- test_phase2_environments.py
- route_service.py
- test_schema_redaction.py
- publish
- test_auth_multi_org.py
- CertificateGenerationState
- certificate_lifecycle.py
- test_secrets.py
- test_nginx_renderer.py
- domain_service.py
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
- AsyncSession
- user_service.py
- devDependencies
- Conflict
- Certificate
- test_payload_crypto.py
- DomainStatus
- CloudflareDnsProvider
- list_containers
- create_certificate
- test_phase21_secret_version_integrity.py
- TxtObservation
- NexusOps (self-hosted infrastructure management and monitoring platform)
- REST API surface (/api/v1)
- journey.spec.ts
- test_org_dek_envelope.py
- redact_mapping
- sync_host_state
- docker_real.py
- list_dns_providers
- _exec
- redis service (Redis 7, no persistence, loopback :6390)
- NexusOps agent (stdlib-only Python, agent/nexusops_agent.py)
- test_migration_phase5.py
- test_migration_phase532.py
- Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)
- organization_service.py
- sweep_session
- middleware.py
- dnsmock.py
- scripts
- test_certificate_lifecycle.py
- test_tenancy_allowlist.py
- _alembic_config
- AcmeOrder
- @tanstack/react-query
- generate_secrets.sh
- _invoke_sender
- server_payload
- _run_migration
- test_dns_providers.py
- OperationError
- LogLine
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
- rollback_secret
- nexusops-challenge.mjs
- Secrets Architecture
- test_schemas_agent.py
- .state
- test_kek_vault_transit_live.py
- Alert
- Path
- routes.py
- AgentClient
- test_kek_selection.py
- Path
- main
- redact_log_event
- test_migration_phase22.py
- test_agent_contract.py
- test_kek_vault_transit.py
- MonitorTransport
- v1/auth.py
- get_latest_server_metrics
- _failure_from
- Platform Security Model — NexusOps
- Node & Agent Architecture
- login
- _converged_node_with_a_route
- ssrf.py
- _nginx_apply
- test_migration_phase521.py
- list_events
- test_notifications.py
- 20261012_1200-c8d9e0f1a2b3_phase5_certificate_metadata.py
- apply_scope_to_session
- Phase 5 — HTTPS, Certificates and Private-Key Delivery — Design
- Deployment Architecture — NexusOps (target state)
- phase3.spec.ts
- Settings
- channel.py
- _nginx_bootstrap
- 10. Implementation slices, acceptance criteria, tests, limitations
- ._shallow_validate
- Certificate Management — NexusOps
- v1/certificates.py
- entries
- 20261014_1200-a7b8c9d0e1f2_isolate_org_dek_envelopes.py
- 20261010_1200-f4a5b6c7d8e9_phase4_domains_and_routes.py
- certificate_order.py
- readiness
- SimulatedDeploymentRunner
- PayloadContext
- _LibrarySession
- incidents.py
- pytest
- VaultTransitKEKProvider
- ._check_status
- 20261008_1200-b2c3d4e5f6a7_add_projects_and_environments.py
- NotificationChannel
- 20261014_1600-b8c9d0e1f2a3_phase522_providers_acme_material.py
- test_monitors_incidents.py
- _FakeAsyncClient
- 20261009_1100-d4e5f6a7b8c9_correct_legacy_environment_types.py
- api_key_service.py
- README.md - NexusOps overview
- create_api_key
- AcmeProvider
- update_organization
- Platform Vision — NexusOps
- AgentContainerIn
- 20260923_1000-c4e2a1f7b9d3_rename_server_codenames_to_node.py
- is_terminal
- _attempt_delivery
- ControlHandler
- 20261012_1600-f5a6b7c8d9e0_phase5_org_dek_envelope.py
- me
- update_role
- system_scope
- test_error_logging.py
- register_exception_handlers
- CertificateStatus
- record
- _mutate_in_system_scope
- Append-only audit log (Postgres BEFORE UPDATE OR DELETE trigger)
- process_heartbeat
- projects.py
- AuditLogPage.test.tsx
- client_ip
- parametrize
- instant_pacing
- .__tablename__
- ZoneResolution
- test_app_gating.py
- test_tasks_util.py
- change_password
- .__init__
- _validate_resolution
- dispatch_event_frame
- 20260922_1000-a3f1c8d24b6e_add_tenancy_foundation.py
- cloudflare
- get_meta
- 2. The Node concept
- ContainerListPage.test.tsx
- 20261009_1300-a1b2c3d4e5f6_add_phase3_nodes_and_agent_v2.py
- .dispatch
- _FinalizingClient
- dependencies
- LoginPage.tsx
- _validate_bundle
- 20261009_1200-e5f6a7b8c9d0_fix_environment_type_precedence.py
- enqueue_generation
- 20261006_1200-f1a2b3c4d5e6_fix_schema_drift.py
- 20261016_1000-c9d0e1f2a3b4_phase53_generation_directory.py
- known_directory_urls
- test_capability_report_shape_is_accepted
- AcmeAccountKeyUnavailable
- enrollment_contract
- websocket_endpoint
- test_run_async_publishes_frames_scheduled_by_the_commit_hook

## God Nodes (most connected - your core abstractions)
1. `AuthContext` - 176 edges
2. `APIModel` - 158 edges
3. `get_settings()` - 114 edges
4. `record()` - 101 edges
5. `Server` - 93 edges
6. `apiGet()` - 91 edges
7. `NotFound` - 90 edges
8. `Conflict` - 86 edges
9. `publish()` - 84 edges
10. `assert_error_code()` - 82 edges

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

## Communities (271 total, 23 thin omitted)

### Community 0 - "apiGet"
Cohesion: 0.06
Nodes (90): apiDelete(), apiGet(), apiPatch(), apiPost(), ApplicationOut, ENVIRONMENT_TYPE_LABELS, EnvironmentType, IncidentEventOut (+82 more)

### Community 1 - "test_certificates.py"
Cohesion: 0.08
Nodes (58): _app_role_dsn(), _audits(), _certificate_rows(), _create_domain(), _created_certificate(), _dns_stub(), _events(), _fake_observe() (+50 more)

### Community 2 - "ApiKeysPage.tsx"
Cohesion: 0.09
Nodes (19): ApiKeyOut, ApiKeysPage, ApiKeyCreatedOut, handleCopyKey(), copyText(), describeError(), EMPTY_FORM, GROUP_STYLE (+11 more)

### Community 3 - "_verified_domain"
Cohesion: 0.09
Nodes (68): _agent_result_body(), _audits(), _claim(), _create_route(), _drain(), _event_types(), _heartbeat(), _live_operations() (+60 more)

### Community 4 - "docker_host_service.py"
Cohesion: 0.10
Nodes (44): DockerHostStatus, DockerHost, describe_provider_error(), provider_for(), Exception, Return the provider matching *host*'s endpoint configuration., Sanitized, length-capped text safe for host ``last_error`` columns., DockerHostPingOut (+36 more)

### Community 5 - "package.json"
Cohesion: 0.13
Nodes (15): name, private, type, version, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom (+7 more)

### Community 6 - "resolve_client_ip"
Cohesion: 0.20
Nodes (19): _parse_networks(), Request, Parse a comma-separated CIDR list; malformed entries are skipped., Real client address for *request* per the trust model above., resolve_client_ip(), make_request(), Request, Unit tests for the chained-proxy client-IP resolver (app/core/client_ip.py). (+11 more)

### Community 7 - "_raw_probe"
Cohesion: 0.17
Nodes (13): _app_role_dsn(), A libpq DSN for the RLS-enforced application role (no ORM, no guard)., Run one statement as ``nexusops_app`` with an explicit GUC. Parameterized like…, Raw SQL as the application role: the policies alone return nothing. Written…, Adding ``org_id`` to ``audit_logs`` must not have opened a way to edit it. The…, ``WITH CHECK`` is not decoration: an unlucky INSERT cannot cross tenants., Key material is out of reach of a read *and* a write, in raw SQL. This is audit…, _raw_probe() (+5 more)

### Community 8 - "App.tsx"
Cohesion: 0.04
Nodes (103): DeploymentOut, Page, ProjectOut, AlertsPage, App(), AuditLogPage, ContainerListPage, DeploymentListPage (+95 more)

### Community 9 - "test_agent_v2.py"
Cohesion: 0.08
Nodes (36): agent_fixture(), _load_agent(), Any, fixture, parametrize, Agent protocol v2: honest metrics, capability detection, and the executor. The…, Phase 4 shipped three nginx ops — no file primitive, no command primitive., Trusting a private CA must not weaken verification. (+28 more)

### Community 10 - "assert_error_code"
Cohesion: 0.07
Nodes (58): assert_error_code(), Assert envelope shape + code; returns the inner error object., Regression: lockout must not leak which emails exist. After login_max_attempts…, test_locked_account_response_is_indistinguishable(), test_metadata_endpoint_and_private_target_blocked(), _dispatch(), _dispatch_body(), _enrolled_node() (+50 more)

### Community 11 - "ServerDetailPage.tsx"
Cohesion: 0.06
Nodes (42): ContainerOut, MetricPoint, ServerDetail, ServerSummary, ChartSeries, LineChart(), LineChartProps, PAD (+34 more)

### Community 12 - "APIModel"
Cohesion: 0.03
Nodes (123): _manual_out(), The operator-facing view of one manual challenge set. Everything here comes…, Role management and permission-registry routes (role.read / role.manage)., CertificateRevocationState, The CA conversation about a generation, deliberately a second axis. ``state``…, AgentContainerPortIn, AgentEnrollIn, AgentEnrollOut (+115 more)

### Community 13 - "client.ts"
Cohesion: 0.05
Nodes (54): API_BASE, ApiError, apiRequest(), buildUrl(), extractError(), getAccessToken(), getActiveOrgId(), onActiveOrgChange() (+46 more)

### Community 14 - "validate_config"
Cohesion: 0.08
Nodes (28): field_validator, collect_secret_refs(), walk(), ConfigValidationError, merge_config(), Any, ValueError, A configuration map is not shaped like a flat string→string settings map. (+20 more)

### Community 15 - "test_certificate_manual_issuance.py"
Cohesion: 0.09
Nodes (50): _challenge_value(), _create_domain(), _credential_seam(), _dns(), _document(), _events(), _FakeCloudflare, _issue() (+42 more)

### Community 16 - "deployment_engine.py"
Cohesion: 0.10
Nodes (59): deployment_log_channel(), Deployment, DeploymentStep, AlertSeverity, DeploymentStatus, DeploymentTrigger, EventLevel, String enum; member names equal values so name/value storage never disagrees. (+51 more)

### Community 17 - "SimulatedDockerProvider"
Cohesion: 0.08
Nodes (34): ContainerStatus, DockerProviderError, A provider operation failed. ``str()`` is safe to show/log., Any, datetime, Plausible numbers derived from the row plus time-based sine noise., Replay registered LogEntry rows ordered by ts (tail N). ``follow`` is ignored…, Implements :class:`DockerProvider` semantics against DB rows. (+26 more)

### Community 18 - "enrollment_service.py"
Cohesion: 0.13
Nodes (28): generate_enrollment_token(), An enrollment credential (``nxk_``): single-use, short-lived, org-scoped.…, Return the active org id or raise; used by services that need it explicitly., require_org(), EnrollmentToken, One single-use credential that enrolls (or claims) exactly one node., Whether the row could still be redeemed (not a race-safe check)., EnrollmentTokenState (+20 more)

### Community 19 - "NotFound"
Cohesion: 0.10
Nodes (46): NotFound, An encrypted configuration value, scoped to org, project or environment.…, One immutable value of a :class:`Secret` — append-only history. A row is…, Secret, SecretVersion, The credential a challenge may be published with, or a 404. Same shape as the…, _resolve_dns_provider(), _actor_type() (+38 more)

### Community 20 - "test_deployments_simulated.py"
Cohesion: 0.11
Nodes (35): execute_deployment(), Run one deployment to a terminal state. Never raises; safe to re-run., get_environment(), task, Execute one queued deployment. The engine owns all state transitions., Re-enqueue deployments the broker lost; fail ones whose worker died.…, run_deployment(), _run() (+27 more)

### Community 21 - "container.py"
Cohesion: 0.21
Nodes (12): ContainerRemoveOut, host_ref(), HostRef, LogEntryOut, UUID, Container schemas: list/detail read models, log entries, action results., Summary of the docker host a container runs on., Summary of the server associated with a container. (+4 more)

### Community 22 - "metrics_service.py"
Cohesion: 0.06
Nodes (46): _database_url(), Alembic environment: metadata comes from app.models, URL from app settings., Migrations run as the table **owner**, never as the application role. The owner…, Emit SQL to stdout without a live DB connection., Run migrations against the configured database., run_migrations_offline(), run_migrations_online(), _is_trusted() (+38 more)

### Community 23 - "get_settings"
Cohesion: 0.03
Nodes (142): argon2, argon2_exceptions, _presented_token(), Resolve ``X-Agent-Token`` to the node it identifies, inside its own org. The…, require_server(), Whether this request's cookie will travel over https. The edge always…, _transport_is_https(), get_settings() (+134 more)

### Community 24 - "Domain Routing — NexusOps"
Cohesion: 0.07
Nodes (31): 10. Wildcards and catch-all, 11. User journey, 12. API surface, permissions, audit, 1. Scope and current state, 2. Where nginx runs, 3.1 Domain, 3.2 Route, 3. Entities (per domain-model.md §2.4) (+23 more)

### Community 25 - "test_phase4_routing.py"
Cohesion: 0.06
Nodes (47): MonitorTargetType, What a monitor observes (domain-model.md §2.6, polymorphic targets). ``URL`` is…, _count_rows_in_system_scope(), _create_domain(), _flip_name_to(), heartbeat_payload(), parametrize, Phase 4 through the real HTTP surface, workers and agent contract. The journey… (+39 more)

### Community 26 - "Product Roadmap — NexusOps Multi-Tenant Platform"
Cohesion: 0.11
Nodes (19): What one reported result did to its operation row. The caller's side effects —…, ResultTransition, 0. Stance, 10. Phase 7 — Teams, grants & custom roles — **proposal, not implemented**, 11. Phase 8 — Backups — **proposal, not implemented**, 12. Phase 9 — Billing & metering — **proposal, not implemented**, 13.1 Scope-creep gates — what must be true before each expansion, 13. First commercially meaningful version (+11 more)

### Community 27 - "test_agent_backoff.py"
Cohesion: 0.15
Nodes (21): agent_fixture(), _install_sleep(), fake_sleep(), _load_agent(), _patch_host(), Any, fixture, MonkeyPatch (+13 more)

### Community 28 - "certificate_issuance.py"
Cohesion: 0.06
Nodes (54): ActorType, DnsProviderKind, Which DNS API a stored credential speaks to. One member in v1 (Cloudflare) —…, CredentialCheck, DnsCredentialError, DnsCredentialProvider, DnsProviderUnavailable, DnsWriteAmbiguous (+46 more)

### Community 29 - "nexusops_agent.py"
Cohesion: 0.09
Nodes (30): build_capabilities(), build_heartbeat(), collect_container_stats(), collect_containers(), _container_ports(), _container_status(), cpu_percent_since(), disk_stats() (+22 more)

### Community 30 - "test_certificate_pebble.py"
Cohesion: 0.05
Nodes (83): load(), The generation's order document, or an empty one. **Never raises.** A malformed…, _assert_no_material(), _bootstrap_resolver(), _challenge_url(), _CloudflareCredentials, _compose(), _create_domain() (+75 more)

### Community 31 - "AuthContext"
Cohesion: 0.06
Nodes (54): active_memberships(), _attach_organization(), AuthContext, get_current_user(), get_identity(), get_optional_user(), _load_organization(), _load_permissions() (+46 more)

### Community 32 - "AcmeDirectory"
Cohesion: 0.09
Nodes (45): AcmeDirectory, Which certificate authority a per-organization ACME account belongs to. A…, Whether this directory issues publicly trusted certificates. The single…, Whether a certificate from this directory is trusted by a browser. False for…, Short operator-facing name, stored in metadata and shown in the API., AcmeDirectoryError, assert_issuance_allowed(), coerce_directory() (+37 more)

### Community 33 - "test_rate_limit.py"
Cohesion: 0.18
Nodes (16): RateLimited, _memory_count_and_ttl(), rate_limit(), Fixed-window counter backed by process memory. Returns (count, ttl)., Return a dependency enforcing *limit* requests per window per IP. With…, _clean_memory_windows(), _FakeRequest, fixture (+8 more)

### Community 34 - "docker_hosts.py"
Cohesion: 0.08
Nodes (52): create_docker_host(), delete_docker_host(), get_docker_host(), list_docker_hosts(), list_host_images(), list_host_networks(), list_host_volumes(), ping_docker_host() (+44 more)

### Community 35 - "integration/test_certificate_issuance.py"
Cohesion: 0.08
Nodes (49): A reference to **one** TXT record this platform created. The reference, not the…, Create one TXT record and return its reference. Raises…, Every TXT record at *name* whose value equals *value*. The reconciliation…, TxtRecord, cleanup_incomplete(), Records this platform published and still cannot confirm are gone., _AmbiguousZone, _create_domain() (+41 more)

### Community 36 - "library.py"
Cohesion: 0.06
Nodes (46): AuthorizationResource, AcmeConfigError, AcmeError, AcmeRateLimited, AcmeRejected, AcmeTimeout, AcmeUnavailable, classify_error() (+38 more)

### Community 37 - "v1/search.py"
Cohesion: 0.06
Nodes (45): _hit(), AsyncSession, CurrentUser, DbSessionDep, get, max_length, min_length, Query (+37 more)

### Community 38 - "enums.py"
Cohesion: 0.05
Nodes (87): _quoted_list(), Add the operations framework table (node-agent-architecture.md §5). One tenant-…, upgrade(), _org_scoped_classes(), Mapped classes marked :class:`~app.models.base.OrgScoped`. Reads the mapper…, The per-organization ACME account and its protected account key. One account…, Base, big_serial_pk() (+79 more)

### Community 39 - "typing"
Cohesion: 0.03
Nodes (154): asyncio, Agent ingest endpoints: enrollment, hello, heartbeat, and operation traffic.…, _decode_frame(), _max_log_id(), _poll_new_lines(), Container API: listing/detail, lifecycle actions, removal, logs, streaming.…, Parse a Redis pub/sub frame ``{ts, stream, message}`` into a LogLine., Highest persisted log id for a container (poll fallback watermark). (+146 more)

### Community 40 - "DockerProvider"
Cohesion: 0.08
Nodes (14): ContainerInfo, DockerProvider, Any, datetime, Protocol, List containers visible to the provider., Inspect a single container by id (short ids allowed)., List images: keys ``id``, ``repo_tags``, ``size_bytes``, ``architecture``. (+6 more)

### Community 41 - "test_monitor_transport.py"
Cohesion: 0.08
Nodes (46): coerce_headers(), _decode(), get_transport(), HTTPMonitorTransport, Any, BaseException, Deterministic fake checker for ``sim://`` monitors and demo environments.…, Pick the transport matching the monitor URL scheme. (+38 more)

### Community 42 - "_rows"
Cohesion: 0.15
Nodes (26): _rows(), _columns(), Phase 5.2.1.2 migration (`a7b8c9d0e1f2`): the envelope leaves…, ``column -> (data_type, is_nullable)`` for *table*., ``(org_id, ciphertext, generation)`` for every populated envelope, ordered., The move creates rows only where there was key material. A row with a NULL…, Two envelopes for one tenant are refused by the database, not by a service., F3: a negative generation, and either half of an inconsistent pair, fail. The… (+18 more)

### Community 43 - "AuthContext.tsx"
Cohesion: 0.02
Nodes (83): Membership, SearchResult, User, AuthContext, AuthProvider(), AuthState, isOrgSelectionError(), MeResponse (+75 more)

### Community 44 - "project_service.py"
Cohesion: 0.14
Nodes (43): Application, DeploymentEnvironment, A **project-scoped** deployment environment (Phase 2 promotion). The…, _apply_update(), _check_server(), create_application(), create_environment(), create_project() (+35 more)

### Community 45 - "test_permissions.py"
Cohesion: 0.05
Nodes (36): permission_exists(), Check an API-key scope list against a required permission. Supports exact match…, scope_matches(), _auth_context(), _FakeCtx, parametrize, Unit tests for the permission registry, scope matching and RBAC gate., Duck-typed stand-in for AuthContext. (+28 more)

### Community 46 - "ProviderHealth"
Cohesion: 0.08
Nodes (24): Drop every cached verdict (tests, and any future configuration reload)., reset_health_cache(), ProviderHealth, A provider's self-report. ``detail`` is sanitized: no tokens, no DSNs., Report operability without touching key material., _clear_health_cache(), fixture, MonkeyPatch (+16 more)

### Community 47 - "test_phase3_nodes.py"
Cohesion: 0.15
Nodes (33): _create_token(), _dispatch(), _enroll(), _enrolled_node(), _load_agent_module(), _mutate_in_system_scope(), Phase 3 — Nodes & Agent v2 end-to-end behaviour. Grouped by the question each…, Import the shipped agent source (sync, so async tests never touch Path). (+25 more)

### Community 48 - "test_ssrf.py"
Cohesion: 0.15
Nodes (24): assert_safe_tcp_endpoint(), Validate a ``tcp://`` docker host endpoint for outbound connection. Docker…, install_dns(), lax(), Exception, fixture, MonkeyPatch, Unit tests for the SSRF guard — fully offline via injected DNS answers. (+16 more)

### Community 49 - "test_ws_hub.py"
Cohesion: 0.07
Nodes (46): _close_socket(), Connection, Hub, _is_same_origin(), _params_key(), _parse_payload(), Any, WebSocket (+38 more)

### Community 50 - "create_dns_provider"
Cohesion: 0.18
Nodes (20): _actor(), canonical_blob(), create_dns_provider(), delete_dns_provider(), normalize_zone_allowlist(), AsyncSession, Request, UUID (+12 more)

### Community 51 - "AuthorizationState"
Cohesion: 0.11
Nodes (7): AuthorizationState, One authorization's status after a poll., Poll one authorization until it is not ``pending``, or the deadline passes., Poll until the authorization leaves ``pending``, or the deadline passes. The…, _FakeAcme, The CA side of the seam, honest about the outcomes that matter here., test_authorization_state_status_predicates()

### Community 52 - "proxy_service.py"
Cohesion: 0.04
Nodes (123): ListenerOwnership, OperationType, ProxyApplyOutcome, The whitelist. Nothing outside this enum ships as an exec surface. Each type…, Terminal outcome of one ``nginx.apply`` operation on a node., Who holds one required listener port, per the node's pre-flight. The…, Server, Operation (+115 more)

### Community 53 - "DeterministicKEKProvider"
Cohesion: 0.04
Nodes (74): _derive(), DeterministicKEKProvider, The deterministic in-process provider — tests and explicitly configured dev.…, A per-(binding, key version) key: HKDF-style derivation. Two properties, both…, Deterministic wrap/unwrap/rewrap over an in-process AEAD., Bump the modelled KEK version, so a test can prove rewrap moves it., EncryptionContext, KEKContextMismatchError (+66 more)

### Community 54 - "incident_service.py"
Cohesion: 0.19
Nodes (27): IncidentEventKind, IncidentSeverity, IncidentStatus, Incident, IncidentEvent, acknowledge(), _add_event(), add_note() (+19 more)

### Community 55 - "test_agent_nginx_contract.py"
Cohesion: 0.12
Nodes (31): _agent_bundle(), agent_fixture(), _load_agent(), Any, fixture, parametrize, Phase 4 agent contract: nginx capability, port reporting, and bundle…, An unreadable ``/proc`` must never be read as "the port is free". (+23 more)

### Community 56 - ".from_user"
Cohesion: 0.16
Nodes (20): create_user(), deactivate_user(), get_user(), list_users(), CurrentUser, DbSessionDep, get, patch (+12 more)

### Community 58 - "list_deliveries"
Cohesion: 0.17
Nodes (23): create_channel(), delete_channel(), get_channel(), list_channels(), list_deliveries(), DbDep, Depends, get (+15 more)

### Community 59 - "test_tenant_isolation.py"
Cohesion: 0.05
Nodes (75): bearer(), cookie_attributes(), error_of(), login_account(), login_headers(), Any, AsyncClient, Response (+67 more)

### Community 60 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+11 more)

### Community 61 - "_list_deployments"
Cohesion: 0.11
Nodes (34): _attribute_step_idx(), cancel_deployment(), _emails_for(), get_deployment(), list_application_deployments(), list_deployment_logs(), _list_deployments(), alias (+26 more)

### Community 62 - "fixture"
Cohesion: 0.22
Nodes (11): _admin_dsn(), client(), owner(), AsyncClient, fixture, A second organization the owner also belongs to. Both tenants are owned by the…, Bootstrap owner credentials for this test (fresh DB => first user). ``headers``…, A libpq DSN to the maintenance database (create/drop scratch DBs). (+3 more)

### Community 63 - "dns_verifier.py"
Cohesion: 0.08
Nodes (41): _aggregate_answers(), _ask_one(), decide(), discover_authoritative_nameservers(), _discover_nameservers(), matches_token(), _normalise_ns(), observe() (+33 more)

### Community 64 - "test_phase2_environments.py"
Cohesion: 0.18
Nodes (22): _environment(), _project(), parametrize, Phase 2: project-scoped environments, config layering, and their isolation. The…, Uniqueness is ``(project_id, slug)`` — not instance-wide., The update path is validated too (the pre-Phase-2 gap)., Knowing an environment UUID is not access: the project link must hold., Another tenant cannot reach the project, its environments, or its detail. (+14 more)

### Community 65 - "route_service.py"
Cohesion: 0.11
Nodes (46): AsyncSession, routes_for_domain(), One hostname+path served from one container on one node. Relationship rules the…, Route, _actor(), _apply_or_defer(), _conflicting_route(), create_route() (+38 more)

### Community 66 - "test_schema_redaction.py"
Cohesion: 0.12
Nodes (21): Drop the query string so signed tokens never appear in error text., Public alias: redact any query string from a URL before display/persist., strip_query(), is_sensitive_header(), mask_sensitive_headers(), field_serializer, True when *name* looks like it carries a credential (Authorization etc.)., Return a copy of *headers* with sensitive values replaced by a mask. (+13 more)

### Community 67 - "publish"
Cohesion: 0.18
Nodes (17): _after_commit_publish(), _after_rollback_drop(), publish(), _publish_after_commit(), _publish_redis(), Any, AsyncSession, UUID (+9 more)

### Community 68 - "test_auth_multi_org.py"
Cohesion: 0.24
Nodes (17): _latest_audit(), _latest_event(), _list_ids(), Any, UUID, Phase 3.1 — pre-organization auth events are instance-level and tenant-…, No account => no actor => a system instance-level row, as before., A NULL-org auth fact is not reachable through either organization. (+9 more)

### Community 69 - "CertificateGenerationState"
Cohesion: 0.10
Nodes (29): directory_required_predicate(), one_live_generation_predicate(), pre_issuance_predicate(), The SQL predicate of ``uq_cert_generations_one_live``. Built from…, The states in which a generation carries no material *by construction*.…, A generation that outlives the order must name the CA that issued it. The…, CertificateGenerationState, Lifecycle of one ACME order + key pair, pre- and post-issuance. **Phase 5.1… (+21 more)

### Community 70 - "certificate_lifecycle.py"
Cohesion: 0.11
Nodes (26): attempt_delay_seconds(), can_transition(), coerce_state(), InvalidTransition, next_attempt_at(), datetime, ValueError, The certificate lifecycle — pure decisions, no I/O, no side effects. The whole… (+18 more)

### Community 71 - "test_secrets.py"
Cohesion: 0.09
Nodes (29): Exception, A ``${secret:KEY}`` reference could not be resolved. Fail-closed. Carries…, One successfully resolved reference: metadata for audit, no value., Outcome of resolving an environment's config references., Resolve every ``${secret:KEY}`` reference an environment's config names.…, resolve_secrets_for_environment(), ResolvedSecrets, SecretReference (+21 more)

### Community 72 - "test_nginx_renderer.py"
Cohesion: 0.04
Nodes (95): _header_lines(), NginxProvider, Any, ValueError, _quote(), _rate_zone(), NginxProvider — a pure, deterministic renderer plus the two op wrappers.…, Validate the route's headers and split them by destination. (+87 more)

### Community 73 - "domain_service.py"
Cohesion: 0.06
Nodes (75): create_domain(), delete_domain(), _enqueue_verification(), get_domain(), list_domain_routes(), list_domains(), _project_names(), alias (+67 more)

### Community 74 - "api service (FastAPI / uvicorn :8000)"
Cohesion: 0.22
Nodes (15): Dev overlay (hot reload, Vite on :5173), Docker socket override (DOCKER_GID group_add), api service (FastAPI / uvicorn :8000), frontend service (built SPA served by nginx), nginx service (edge :8080, only host-exposed port), scheduler service (celery beat), worker service (celery worker, concurrency 4), Modular monolith topology (one API image, Celery worker/beat) (+7 more)

### Community 75 - "monitors.py"
Cohesion: 0.18
Nodes (32): check_now(), create_monitor(), delete_monitor(), get_monitor(), list_checks(), list_monitor_incidents(), list_monitors(), pause_monitor() (+24 more)

### Community 76 - "PageParams"
Cohesion: 0.04
Nodes (101): Dependency factory enforcing a permission; returns 403 when denied., require_permission(), Alert inbox endpoints. Authenticated users see the shared operator feed., API key routes — self-service management of the caller's own machine…, list_audit_logs(), datetime, DbSession, Depends (+93 more)

### Community 77 - "test_acme_accounts.py"
Cohesion: 0.07
Nodes (65): AcmeAccount, One ACME account: its directory, its CA-side URL, and its wrapped key., CertificateKeyAlgorithm, The key type generated for a generation. Fixed in v1; never client-chosen., account_for(), account_key(), account_key_fingerprint(), _actor() (+57 more)

### Community 78 - "monitor_service.py"
Cohesion: 0.10
Nodes (51): CheckResult, MonitorStatus, Monitor, MonitorCheck, One probe. Targets are polymorphic since Phase 4 (domain-model.md §2.6).…, CheckOutcome, Result of a single monitor check., MonitorBase (+43 more)

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
Cohesion: 0.07
Nodes (53): apex_of(), _canonicalize(), canonicalize_name(), canonicalize_path(), canonicalize_record_name(), _check_labels(), _check_not_ip(), hostname_is_covered() (+45 more)

### Community 83 - "tests/conftest.py"
Cohesion: 0.22
Nodes (7): configure_test_env(), Test bootstrap: pin every cached setting BEFORE the first ``app`` import. The…, KEY=VALUE pairs from the repo .env (first definition wins); never logged., Export the exact settings the app caches; host values cannot leak through., _read_dot_env(), os, pathlib

### Community 84 - "AsyncSession"
Cohesion: 0.10
Nodes (33): _actor_kwargs(), container_counts(), create_server(), delete_server(), get_server(), list_tags_with_usage(), _order_clause(), pending_rotation() (+25 more)

### Community 85 - "user_service.py"
Cohesion: 0.12
Nodes (40): MembershipStatus, _apply_deactivation(), _assert_not_last_active_member(), _assert_not_last_active_superadmin(), create_user(), deactivate_user(), get_by_email(), get_member() (+32 more)

### Community 86 - "devDependencies"
Cohesion: 0.13
Nodes (15): devDependencies, eslint, @eslint/js, eslint-plugin-react-hooks, jsdom, @playwright/test, @testing-library/jest-dom, @testing-library/react (+7 more)

### Community 87 - "Conflict"
Cohesion: 0.04
Nodes (81): _parse_sort(), _parse_statuses(), cancel_operation(), create_operation(), get_operation(), list_operations(), DbDep, Depends (+73 more)

### Community 88 - "Certificate"
Cohesion: 0.07
Nodes (48): Certificate, CertificateGeneration, One requested certificate: an identity, its lifecycle view, no material., One ACME order + one key pair. Renewal inserts a new row, never mutates one.…, CertificateDnsMode, Who publishes the DNS-01 challenge record. ``automated`` means the platform…, DnsRecordProvider, One DNS API, seen from the control plane's issuance side. Every method takes… (+40 more)

### Community 89 - "test_payload_crypto.py"
Cohesion: 0.09
Nodes (51): decrypt(), encrypt(), _parse_header(), PayloadContextMismatch, PayloadDecryptionError, PayloadEnvelopeError, PayloadError, Fernet (+43 more)

### Community 90 - "DomainStatus"
Cohesion: 0.09
Nodes (39): DomainStatus, Ownership-verification lifecycle of a Domain (domain-routing.md §4). ``STALE``…, Domain, One DNS name an organization is proving it controls. ``name`` is canonical (see…, is_serving(), Any, Best-effort DNS target check for the routing warning (§6). Never changes…, The state a domain flip forces on its routes, or ``None`` to leave them. (+31 more)

### Community 91 - "CloudflareDnsProvider"
Cohesion: 0.08
Nodes (24): _Ambiguous, CloudflareDnsProvider, BaseException, Exception, Response, A bounded, credential-free description of a failed call., Verify the token and list the zones it can reach. Never raises for a provider-…, Find the zone that actually holds *name*. Walking suffixes deepest-first and… (+16 more)

### Community 92 - "list_containers"
Cohesion: 0.09
Nodes (40): _action_route(), _endpoint(), _container_out(), _ev(), get_container(), _like_pattern(), list_container_logs(), list_containers() (+32 more)

### Community 93 - "create_certificate"
Cohesion: 0.11
Nodes (27): _actor(), all_generations(), CertificateMetadata, create_certificate(), delete_certificate(), _dns_mode(), get_certificate(), latest_generations() (+19 more)

### Community 94 - "test_phase21_secret_version_integrity.py"
Cohesion: 0.18
Nodes (18): _app_role_dsn(), _owner_dsn(), _probe(), Phase 2.1 — ``secret_versions`` is append-only in the **database**, not just in…, Immutability is a database guarantee, not merely a missing code path. The owner…, The legitimate append paths keep working under the guard., The documented deletion policy: purging a Secret cascades its history., RLS is preserved: another tenant cannot see a version row, even by id. (+10 more)

### Community 95 - "TxtObservation"
Cohesion: 0.06
Nodes (67): check_once(), evaluate(), nameserver_summary(), observe(), _observer_name(), observer_window(), PropagationResult, Has the challenge record actually reached the authoritative nameservers?… (+59 more)

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
Cohesion: 0.07
Nodes (74): OrganizationDekEnvelope, The organization's Fernet DEK, **wrapped** by the configured KEK provider. The…, org_dek(), Fernet, Yield the organization's DEK for **one operation**, then drop it. The key-only…, db(), A session with **no** tenant scope. Deliberately unscoped: it is how a test…, _BarrierRewrapProvider (+66 more)

### Community 100 - "redact_mapping"
Cohesion: 0.09
Nodes (35): _is_sensitive_key(), Return a copy of *data* with sensitive values replaced, at any depth. Two…, Substring match on a normalised key so header-style names are caught too.…, redact_mapping(), parametrize, Unit tests for app.core.logging redaction (pure functions only)., No sensitive key name involved: the PEM armor is the only signal., Lists of dicts holding further lists — the shape an agent report takes. (+27 more)

### Community 101 - "sync_host_state"
Cohesion: 0.15
Nodes (17): _as_health(), _as_status(), collect_recent_logs(), _daily_dedup(), _emit(), _mark_host_unavailable(), Any, AsyncSession (+9 more)

### Community 102 - "docker_real.py"
Cohesion: 0.08
Nodes (29): ContainerStats, Exception, Build a compact, secret-free description of a provider failure. Only the…, Point-in-time resource usage snapshot., sanitize_error(), _as_float(), _compute_stats(), _cpu_percent() (+21 more)

### Community 103 - "list_dns_providers"
Cohesion: 0.12
Nodes (27): create_dns_provider(), delete_dns_provider(), get_dns_provider(), list_dns_providers(), DbDep, Depends, get, ManageCtx (+19 more)

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

### Community 108 - "test_migration_phase532.py"
Cohesion: 0.16
Nodes (26): Move ``database`` *back* to ``revision``. The same code path a deployment uses…, _run_downgrade(), _columns(), _insert_certificate(), _insert_generation(), _insert_provider(), _migrate_to_phase53(), _migrate_to_phase532() (+18 more)

### Community 109 - "Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test)"
Cohesion: 0.25
Nodes (9): API keys (X-API-Key, nxo_..., scope intersection), First boot sequence (api entrypoint migrates, compose never seeds), Opt-in seeding and one-time admin password (NEXUSOPS_ALLOW_SEED, ENVIRONMENT=test), Makefile workflows (up/test/lint/typecheck/migrate/seed), HIGH finding: API-key scope bypass for superadmin-owned keys (fixed: scope intersection first), Security audit 2026-09 (26 raw findings -> 20 confirmed, all fixed), HIGH finding: known seed superadmin + API key backdoor (fixed: NEXUSOPS_ALLOW_SEED opt-in, one-time password), Threat model (edge attacker, malicious agent, curious operator, leaked token, SSRF) (+1 more)

### Community 110 - "organization_service.py"
Cohesion: 0.16
Nodes (26): _check(), Forbidden, add_member(), create_organization(), get_organization(), membership_for_user(), AsyncSession, Membership (+18 more)

### Community 111 - "sweep_session"
Cohesion: 0.07
Nodes (48): OperationSpec, Everything the control plane needs to know about one operation type.…, _run(), Keep every routed node's live configuration matching the desired bundle. One…, sweep_routes(), _candidates(), _run(), aggregate_metrics() (+40 more)

### Community 112 - "middleware.py"
Cohesion: 0.14
Nodes (15): ASGIApp, AccessLogMiddleware, HTTP middleware: request ids, security headers, structured access logs., Baseline hardening headers on every API response., RequestIDMiddleware, SecurityHeadersMiddleware, create_app(), _include_routers() (+7 more)

### Community 113 - "dnsmock.py"
Cohesion: 0.10
Nodes (32): resolver(), answer(), encode_name(), encode_txt(), forward(), main(), _nameservers(), parse_question() (+24 more)

### Community 114 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, test:watch

### Community 115 - "test_certificate_lifecycle.py"
Cohesion: 0.09
Nodes (23): material_guard_predicate(), The SQL of ``ck_certificate_generations_material_guard``. Derived from the enum…, _documented_matrix(), _generation_checks(), The generation lifecycle is a contract, and its material gating is its shape.…, The two predicates partition the vocabulary — the guard's whole premise., The 5.1 CHECK is widened to the whole machine in the same change as the guard —…, The guard is derived, not restated: it is the pre-issuance branch *or* the six… (+15 more)

### Community 116 - "test_tenancy_allowlist.py"
Cohesion: 0.20
Nodes (14): AST, _actual_callers(), _calls_system_scope(), _module_path(), Path, The system-scope allowlist is the only fence around the tenancy carve-out.…, Every module that could open a system scope: ``app/`` plus the scripts., No module may lift tenant isolation without being named in the list. (+6 more)

### Community 117 - "_alembic_config"
Cohesion: 0.09
Nodes (24): The correction is part of ``head`` and adds no extra Alembic head., test_corrective_migration_is_reachable_from_head(), _alembic_config(), _at_revision(), _migration_dsn(), _owner_dsn(), Run one Alembic direction against ``database`` through the app's settings path.…, Phase 2 adds one migration; heads must not fork. (+16 more)

### Community 118 - "AcmeOrder"
Cohesion: 0.09
Nodes (11): AcmeOrder, IssuedChain, A fresh order and its authorizations, as public data., What finalization returned: PEM chain text plus nothing else. The chain is…, Create an order for *identifiers* and return its authorizations., Re-open an order this session did not create, by its recorded URL. The manual…, Finalize the current order and download the issued chain., Re-open an order this process did not create, by its URL. Needed by the manual… (+3 more)

### Community 119 - "@tanstack/react-query"
Cohesion: 0.08
Nodes (21): DeploymentStepOut, DeploymentDetailPage, MetaInfo, SimulatedChip(), mocks, ACTIVE_STATUSES, DeploymentDetailRow, DeploymentLogRow (+13 more)

### Community 120 - "generate_secrets.sh"
Cohesion: 0.47
Nodes (3): existing_real_keys(), replace_or_append(), generate_secrets.sh script

### Community 121 - "_invoke_sender"
Cohesion: 0.20
Nodes (14): NotificationError, Any, BaseException, Exception, POST *payload* as JSON to *url*; 2xx is success, anything else raises. Response…, Raised when a delivery attempt fails. Message is safe to persist., Bounded, single-line, content-free error reason., Send a plain-text email via SMTP. Raises :class:`NotificationError`. The… (+6 more)

### Community 122 - "server_payload"
Cohesion: 0.08
Nodes (31): A valid POST /servers body with per-test overrides., server_payload(), test_token_cannot_claim_a_foreign_tenants_node(), test_v1_heartbeat_keeps_the_204_contract(), Regression: a superadmin-owned key is still limited to its scope list. The…, test_scoped_api_key_cannot_exceed_its_grant(), _create_server(), Server CRUD, cascade delete, audit trail rows and audit immutability. (+23 more)

### Community 123 - "_run_migration"
Cohesion: 0.11
Nodes (27): alembic_config, alembic_script, Phase 2.1 corrective migration: legacy ``environment_type`` classification.…, Every case is classified as documented, ids and ownership intact., An explicit non-DEV classification survives the corrective migration. The…, Insert one legacy environment per case, in two organizations., _seed_typed_environments(), test_corrects_legacy_environment_types() (+19 more)

### Community 124 - "test_dns_providers.py"
Cohesion: 0.07
Nodes (50): _audits(), cloudflare(), _create(), _create_domain(), _created(), _dns_stub(), _events(), _fake_observe() (+42 more)

### Community 125 - "OperationError"
Cohesion: 0.13
Nodes (19): _demux_docker_stream(), _docker_error(), execute_operation(), OperationError, _process_pending_operations(), Exception, A stable, sanitized failure contract for the control plane., Re-validate the operation's parameters locally, against a closed shape. (+11 more)

### Community 126 - "LogLine"
Cohesion: 0.12
Nodes (23): LogSource, LogLine, One parsed log record from a container log stream., _persist_log_lines(), Write LogEntry rows via log_service.append_lines, falling back to direct…, append_lines(), count_container_logs(), detect_level() (+15 more)

### Community 127 - "20261018_1200-d0e1f2a3b4c5_phase532_manual_dns01.py"
Cohesion: 0.22
Nodes (14): _assert_no_manual_work(), downgrade(), _drop_constraint(), _guard_predicate(), _in_list(), Phase 5.3.2 — manual DNS-01: ``certificates.dns_mode`` and ``AWAITING_MANUAL``.…, Raw ``ALTER TABLE ... DROP CONSTRAINT IF EXISTS`` (see the 5.2.2 migration)., Replace the state CHECK, the guard and the one-live index in one transaction.… (+6 more)

### Community 137 - "DockerHostsPage.test.tsx"
Cohesion: 0.18
Nodes (8): DockerHostOut, ApiError, failingHost, host, hostsPage, mockCountApi(), server, serversPage

### Community 146 - "_Attempt"
Cohesion: 0.06
Nodes (43): AcmeSession, One attempt's conversation with a CA, for one account. Method calls are…, Register (or discover) this account and return its CA-side URL (``kid``)., Tell the CA a challenge is ready to be validated., Drop the account key and any transport state this session held., _Attempt, _AttemptFailure, _generate_key_and_csr() (+35 more)

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
Cohesion: 0.02
Nodes (87): AlertOut, CapabilityReport, ChannelOut, CheckOut, DeliveryOut, DeploymentLogLine, DeploymentStatus, DomainDetailOut (+79 more)

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
Cohesion: 0.11
Nodes (18): 10. Resolution flow at deploy time, 1.1 Storage and crypto, 1.3 API surface (metadata-only reads), 1.6 Gap list (Phase 2 status), 1. Current state, 2.1 Resolution runs inside org scope, 2.2 Migration mapping (applied by `b2c3d4e5f6a7`), 2. Scope model (org / project / environment layering) — **shipped** (+10 more)

### Community 158 - "test_schemas_agent.py"
Cohesion: 0.15
Nodes (24): AgentHeartbeatIn, AgentHelloIn, Periodic metrics + observed containers from an enrolled agent. Network counters…, First contact from an agent after enrollment; fills static host facts., _heartbeat(), Unit tests for agent-facing schemas (heartbeat + container payloads)., An absent protocol version is the oldest contract, never v2., A capability report forbids unknown keys, so its shape is closed. (+16 more)

### Community 159 - ".state"
Cohesion: 0.10
Nodes (26): computed_field, Derived lifecycle state: revoked wins over used wins over expired., fingerprint(), A stable, non-reversible handle for a secret, for display and change detection.…, test_a_fingerprint_is_domain_separated_and_stable(), 1. Scope and current state, 2. Certificate entity, 2.4 Routing & TLS (new subsystem) (+18 more)

### Community 160 - "test_kek_vault_transit_live.py"
Cohesion: 0.07
Nodes (45): _ca_context(), _configure(), _ctx(), _docker(), _free_port(), LiveVault, CompletedProcess, fixture (+37 more)

### Community 161 - "Alert"
Cohesion: 0.12
Nodes (25): list_alerts(), mark_all_read(), mark_read(), CurrentUser, DbDep, Depends, get, post (+17 more)

### Community 162 - "Path"
Cohesion: 0.12
Nodes (21): _bootstrap_fixture(), Path, An unidentifiable nginx must not be reported as a successful bootstrap., Stage bootstrap's real layout: the system config lives *outside* the tree. This…, The one write outside the tree: the includes land, and it still validates., Point the agent's managed tree at a throwaway directory., What the control plane renders when a node must stop serving its routes., The whole point: the fragment is gone from disk *and* the node agrees. (+13 more)

### Community 163 - "routes.py"
Cohesion: 0.07
Nodes (43): create_route(), delete_route(), disable_route(), _domain_status(), enable_route(), get_route(), list_routes(), AsyncSession (+35 more)

### Community 164 - "AgentClient"
Cohesion: 0.15
Nodes (8): AgentClient, _docker_raw(), SSLContext, A verifying TLS context. Verification is never disabled. A private/self-hosted…, Refuse to send credentials over plain HTTP to a non-loopback server. The…, One raw Docker API call; returns ``(status, body_bytes)``., _tls_context(), _UnixHTTPConnection

### Community 165 - "test_kek_selection.py"
Cohesion: 0.04
Nodes (89): _claim_first_dek(), _context(), _load(), _load_envelope(), _organization_exists(), AsyncSession, UUID, No such organization is visible to this session. (+81 more)

### Community 166 - "Path"
Cohesion: 0.12
Nodes (15): Path, An unloadable CA file must error, never silently fall back to no verify., A throwaway key + self-signed cert for ``localhost`` (real handshakes)., A one-shot HTTPS server; records a failed handshake instead of crashing., A real handshake against a self-signed server must fail verification., Trusting that same cert as a CA lets the identical handshake through., A link-local URL over plain HTTP must fail before any request or write., _self_signed_cert() (+7 more)

### Community 167 - "main"
Cohesion: 0.11
Nodes (19): build_facts(), _build_hello_payload(), _enroll(), _interruptible_sleep(), main(), memory_total_mb(), network_rates(), network_total_bytes() (+11 more)

### Community 168 - "redact_log_event"
Cohesion: 0.16
Nodes (15): Any, structlog processor: scrub one record before anything renders it. The pipeline…, Replace every embedded PEM private-key block in *value* with the marker. Only…, Scrub PEM private-key blocks out of one free-text value. The scalar counterpart…, Recursively redact one value of any shape — the depth-agnostic walk. Dicts,…, redact_log_event(), _redact_private_key_blocks(), redact_text() (+7 more)

### Community 169 - "test_migration_phase22.py"
Cohesion: 0.28
Nodes (8): UUID, Phase 2.2 — the environment-type correction follows the documented precedence.…, Only the previous migration's ``PROD`` output is corrected. A row already…, Create one legacy (application-scoped) environment per case., Every branch of the slug-first rule, end to end through ``head``., _seed_legacy(), test_correction_preserves_operator_set_values(), test_recognised_slug_alias_wins_over_a_conflicting_name()

### Community 170 - "test_agent_contract.py"
Cohesion: 0.20
Nodes (15): agent_fixture(), _load_agent(), _patch_stats(), Any, fixture, MonkeyPatch, Contract tests: the shipped agent's payloads must satisfy the ingest schemas.…, One-shot docker stats reduce to cpu/mem/limit fields the schema accepts, with… (+7 more)

### Community 171 - "test_kek_vault_transit.py"
Cohesion: 0.10
Nodes (48): logs(), _ctx(), _login_ok(), _provider(), parametrize, Request, Response, The Vault Transit adapter's HTTP contract, without a Vault. This module pins… (+40 more)

### Community 172 - "MonitorTransport"
Cohesion: 0.50
Nodes (3): MonitorTransport, Protocol, Anything that can execute a check for a monitor.

### Community 173 - "v1/auth.py"
Cohesion: 0.18
Nodes (17): Authentication routes: register, login, refresh rotation, logout, me, password., LoginRequest, MeOut, PasswordChangeRequest, Authentication request/response schemas., Optional body for non-browser clients; the cookie takes precedence., Token response, plus everything a client needs to pick an organization. The JWT…, Caller identity, their organizations, and their authority in the active one.… (+9 more)

### Community 174 - "get_latest_server_metrics"
Cohesion: 0.13
Nodes (19): get_dashboard_summary(), get_latest_server_metrics(), get_server_metrics(), CurrentUser, DbDep, Depends, get, UUID (+11 more)

### Community 175 - "_failure_from"
Cohesion: 0.13
Nodes (19): _failure_from(), _leaf_of(), BaseException, One classified failure from whatever a step raised. The ACME and DNS seams both…, The leaf of *fullchain_pem*, or a named failure. ``fullchain`` is leaf-first by…, Refuse a chain that does not answer this attempt's own CSR. Two checks, both…, _verify_leaf(), EllipticCurvePrivateKey (+11 more)

### Community 176 - "Platform Security Model — NexusOps"
Cohesion: 0.12
Nodes (16): 10.1 Node revocation playbook (compromised node / leaked agent token), 10.2 Key compromise playbook, 10. Incident response, 1. Scope, stance, and simulation honesty, 2. Assets, 3. Trust boundaries, 4. Tenant isolation model (summary), 5.1 Threat model table (+8 more)

### Community 177 - "Node & Agent Architecture"
Cohesion: 0.09
Nodes (22): install_hint(), The one-liner an operator pastes, without the raw token in argv. The token…, 1. Scope and stance, 3.2 Enrollment v2, 3.3 Token storage & rotation with dual-token grace, 3.4 Revocation semantics — fixing the 401 hot-loop, 3.5 Reconnect / offline states, 3. Agent lifecycle (+14 more)

### Community 178 - "login"
Cohesion: 0.22
Nodes (17): _clear_refresh_cookie(), _cookies_secure(), login(), logout(), DbSessionDep, post, Request, Response (+9 more)

### Community 179 - "_converged_node_with_a_route"
Cohesion: 0.12
Nodes (24): _converged_node_with_a_route(), _dns_stub(), _fake_observe(), _hello_elsewhere(), _mark_reconcile_required_elsewhere(), _node_session(), _pause_render(), gated() (+16 more)

### Community 180 - "ssrf.py"
Cohesion: 0.16
Nodes (17): assert_safe_url(), assert_safe_url_async(), ValueError, _raise_block(), SSRF guard applied to every operator-supplied outbound URL. Monitors and…, Validate *url* for outbound requests; return the parsed URL or raise 422.…, Async wrapper around :func:`assert_safe_url`; DNS runs off the loop., Internal signal: a specific SSRF rule matched (never shown to clients). (+9 more)

### Community 181 - "_nginx_apply"
Cohesion: 0.12
Nodes (25): _fsync_dir(), _nginx_apply(), Materialize the bundle under ``staged/<id>/`` and return that directory.…, Build a self-contained config for ``nginx -t`` over the staged tree. The…, Move the staged tree over the live one, keeping the previous as backup., Put the previous known-good tree back. Returns whether it was possible., Stage → validate → swap → reload, with a rollback on a failed reload., Persist the last apply outcome atomically (temp + rename). (+17 more)

### Community 182 - "test_migration_phase521.py"
Cohesion: 0.21
Nodes (14): _columns(), Phase 5.2.1 migration (`f5a6b7c8d9e0`): two columns, one invariant, one…, The naming convention must not be applied twice. A fresh database is the only…, A ciphertext behind generation 0, and a generation with no material, both fail., The refusal is the point: a rollback must not delete key material., A populated instance in the schema Phase 5.2.1 is written on top of., ``column -> (data_type, is_nullable)`` for ``organizations``., _seed_phase51() (+6 more)

### Community 183 - "list_events"
Cohesion: 0.11
Nodes (20): _decode_cursor(), _encode_cursor(), list_event_types(), list_events(), datetime, DbSession, Depends, get (+12 more)

### Community 184 - "test_notifications.py"
Cohesion: 0.39
Nodes (8): _channel(), _delivery(), UUID, Notification channel + delivery-log endpoints. Regression coverage for GET…, The same event frame consumed twice queues ONE delivery per channel. Every API…, test_dispatch_frame_is_idempotent_across_workers(), test_list_deliveries_filters_by_channel(), test_list_deliveries_serializes_rows()

### Community 185 - "20261012_1200-c8d9e0f1a2b3_phase5_certificate_metadata.py"
Cohesion: 0.23
Nodes (13): downgrade(), _drop_certificate_permissions(), _drop_tenant_policies(), _grant(), _in_list(), Phase 5.1 — certificate metadata and the pre-issuance lifecycle. Adds, in one…, Grant the app role on *table*; the migration role GUC carries the name. The…, The two-policy shape every tenant table uses: tenant + system scope. (+5 more)

### Community 186 - "apply_scope_to_session"
Cohesion: 0.05
Nodes (69): dispose_engine(), apply_scope_to_session(), _desired_guc(), org_scope(), The ``app.current_org`` value implied by the current scopes., Run the enclosed block as a single organization. Nesting the *same* org is a…, Push the current scope onto *db*'s connection immediately. Needed only when a…, Mirror observed container state, diffing RUNNING transitions into events. (+61 more)

### Community 187 - "Phase 5 — HTTPS, Certificates and Private-Key Delivery — Design"
Cohesion: 0.05
Nodes (37): 1.2 Phase 5 in one sentence, 1.3 Trust boundaries Phase 5 adds, 1.4 Non-goals for Phase 5, 1.5 Trust concentration: centralized key custody, accepted **conditionally** (decided), 1. Architecture and trust boundaries, 2.1 The six stages, kept distinct, 2.2 Certificate generation state machine, 2.3 Delivery/activation state machine (per certificate × node) (+29 more)

### Community 188 - "Deployment Architecture — NexusOps (target state)"
Cohesion: 0.17
Nodes (12): 10. Events and WS during runs, 12. Rollback semantics (existing behavior kept), 13. The simulated runner stays — labeled, 14. Open questions, 3. Target pipeline, 4. Runner registry — the DI fix, 6. Phased scope, 6a — Image-based deploys (Phase 3 ops framework is live; needs the deploy step stream) (+4 more)

### Community 189 - "phase3.spec.ts"
Cohesion: 0.15
Nodes (10): frontend_e2e_fixtures_expect, AGENT, NodeDetail, OperationRow, REPO_ROOT, ref_node_child_process, ref_node_fs, ref_node_os (+2 more)

### Community 190 - "Settings"
Cohesion: 0.11
Nodes (9): field_validator, model_validator, Username from :attr:`database_url`, or ``None`` if it is unparseable., Validated application settings (loaded from environment / .env)., Refuse a Vault address that carries userinfo (Phase 5.2.1.2, F4).…, Refuse to start with an ACME directory selection that is unsafe or ambiguous.…, Refuse to start with an unusable or unsafe key source. Two failures are worth…, Settings (+1 more)

### Community 191 - "channel.py"
Cohesion: 0.17
Nodes (15): ChannelType, DeliveryStatus, ChannelBase, ChannelCreate, ChannelUpdate, DeliveryOut, EmailConfig, BaseModel (+7 more)

### Community 192 - "_nginx_bootstrap"
Cohesion: 0.16
Nodes (16): _insert_http_includes(), _nginx_bootstrap(), _nginx_config_test(), _nginx_failure_summary(), _nginx_running(), _pid_alive(), Reload nginx via ``-s reload``, falling back to a SIGHUP of the master., Idempotent, minimal, reversible hook-up of the managed include. The only change… (+8 more)

### Community 193 - "10. Implementation slices, acceptance criteria, tests, limitations"
Cohesion: 0.14
Nodes (13): 10.2 Test requirements (what "done" means per slice), 10.3.1 Approved decisions (previously open), 10.3.2 Known limitations (accepted, not blockers), 10.3.3 Open items and what they block now, 10.3 Decisions and known limitations, 10.4 Reserved-operation-type lists — one source of truth (required consolidation), 10.5.1 Migration (one, additive, `down_revision = c8d9e0f1a2b3`), 10.5.3 Tests (planned, in `backend/tests/`) (+5 more)

### Community 195 - "Certificate Management — NexusOps"
Cohesion: 0.13
Nodes (14): Which known directory this account is at; ``None`` when the URL is neither.…, The directory a stored URL names, or ``None`` when it names none. ``None``…, 10. Status/expiry tracking and monitor tie-in, 12. Audit and events, 13. Non-goals, 3. API surface and permissions, 5.1 Shipped (5.3): the flow as it actually runs, 5.2 Shipped (5.3.2): manual DNS-01 (+6 more)

### Community 196 - "v1/certificates.py"
Cohesion: 0.11
Nodes (39): _at(), confirm_manual_challenge(), create_certificate(), delete_certificate(), _detail(), get_certificate(), get_manual_challenge(), list_certificates() (+31 more)

### Community 197 - "entries"
Cohesion: 0.11
Nodes (46): AcmeChallenge, One ``dns-01`` challenge, resolved to what has to be published. Every field is…, _expectations(), One TXT expectation per record name the *current* order has to publish. Values…, challenge_ref(), entries(), pending_cleanup(), Every challenge entry in *document*, in order, shape-checked. A challenge URL… (+38 more)

### Community 198 - "20261014_1200-a7b8c9d0e1f2_isolate_org_dek_envelopes.py"
Cohesion: 0.23
Nodes (11): downgrade(), _drop_constraint(), _drop_tenant_policies(), _grant(), Phase 5.2.1.2 — the organization DEK envelope gets a tenant table of its own.…, Grant the app role the four DML verbs on *table*. Not ownership, and not…, Restore the envelope onto ``organizations`` — without losing any of it., Raw ``ALTER TABLE ... DROP CONSTRAINT``, as the tenancy migration does.… (+3 more)

### Community 199 - "20261010_1200-f4a5b6c7d8e9_phase4_domains_and_routes.py"
Cohesion: 0.31
Nodes (9): downgrade(), _drop_tenant_policies(), _grant(), _in_list(), Phase 4 — domains, routes and the routing schema. Adds, in one migration with a…, Grant the app role on *table*; the migration role GUC carries the name. The…, The two-policy shape every tenant table uses: tenant + system scope., _tenant_policies() (+1 more)

### Community 200 - "certificate_order.py"
Cohesion: 0.06
Nodes (71): confirm_manual_publication(), Request, Record an operator's confirmation and **recheck authoritative DNS once**. The…, attempt_in_flight(), attempt_unfinished(), begin_attempt(), challenge(), cleanup_instructions() (+63 more)

### Community 201 - "readiness"
Cohesion: 0.18
Nodes (12): liveness(), get, Response, Process-level liveness: no dependency checks, always 200 if served., Readiness: database and Redis must answer; 503 with details otherwise., readiness(), HealthOut, Health / readiness schemas. (+4 more)

### Community 202 - "SimulatedDeploymentRunner"
Cohesion: 0.09
Nodes (46): LogLevel, _commit_short(), DeploymentRunner, _pace(), Exception, Protocol, Deployment runner port plus a faithful simulated implementation.…, Stream output lines for *step_name*; raise StepFailure to fail it. (+38 more)

### Community 203 - "PayloadContext"
Cohesion: 0.16
Nodes (13): credentials_for_use(), DnsCredentialUnavailable, RuntimeError, Decrypt a stored credential **for one call**, then drop it. INTERNAL USE ONLY —…, The stored credential cannot be read right now. One cause matters and is named…, decrypt_str(), PayloadContext, What a ciphertext belongs to: organization, purpose, record and DEK generation.… (+5 more)

### Community 204 - "_LibrarySession"
Cohesion: 0.07
Nodes (29): The directory URL stored on the account row and recorded per issuance., AcmeProtocolError, The response was not a well-formed ACME answer. A missing ``Location`` on an…, _execute(), _LibrarySession, _call(), _call(), _call() (+21 more)

### Community 205 - "incidents.py"
Cohesion: 0.13
Nodes (33): ActionCtx, acknowledge_incident(), AckResponse, add_incident_note(), get_incident(), list_incidents(), BaseModel, DbDep (+25 more)

### Community 206 - "pytest"
Cohesion: 0.13
Nodes (18): The operator-facing one-liner stored in ``last_error``. Bounded., _enrolled(), _heartbeat(), Agent ingest pipeline: hello, heartbeat, staleness transitions, events., A container absent from a later heartbeat is gone from the daemon., A payload at the agent's cap may be truncated — absence proves nothing., test_heartbeat_at_container_cap_skips_reconciliation(), test_heartbeat_removes_vanished_containers() (+10 more)

### Community 207 - "VaultTransitKEKProvider"
Cohesion: 0.09
Nodes (16): AsyncBaseTransport, KEKUnavailableError, The provider could not be reached, or answered nothing usable in time., _classify(), _embeds_userinfo(), AsyncClient, Response, Exchange the AppRole credentials for a short-lived client token. The token is… (+8 more)

### Community 209 - "20261008_1200-b2c3d4e5f6a7_add_projects_and_environments.py"
Cohesion: 0.53
Nodes (5): downgrade(), _drop_constraint(), _quoted_list(), Phase 2 — projects & environments: env promotion, config, secret versions. This…, upgrade()

### Community 210 - "NotificationChannel"
Cohesion: 0.27
Nodes (15): NotificationChannel, A delivery target (email address / webhook endpoint). ``config_ciphertext``…, _audit(), create_channel(), decrypt_channel_config(), delete_channel(), encrypt_config(), _normalize_events() (+7 more)

### Community 211 - "20261014_1600-b8c9d0e1f2a3_phase522_providers_acme_material.py"
Cohesion: 0.21
Nodes (14): _assert_no_material(), downgrade(), _drop_constraint(), _drop_tenant_policies(), _grant(), _in_list(), Phase 5.2.2 — DNS credentials, ACME accounts, and the certificate material…, Raw ``ALTER TABLE ... DROP CONSTRAINT IF EXISTS``. ``op.drop_constraint`` is… (+6 more)

### Community 212 - "test_monitors_incidents.py"
Cohesion: 0.31
Nodes (8): _create_monitor(), Monitor checks driving the full down -> incident -> recovery lifecycle., Regression: probe headers and URL query credentials never leave the API. Probe…, A monitor's checks, incidents and timeline all live in its organization, so the…, test_check_now_endpoint_runs_immediately(), test_down_then_recover_lifecycle(), test_monitor_responses_mask_probe_credentials(), test_notification_pipeline_queues_delivery_for_down_event()

### Community 213 - "_FakeAsyncClient"
Cohesion: 0.22
Nodes (3): _FakeAsyncClient, _FakeRequestObj, Scripted httpx.AsyncClient: responses keyed by absolute request URL.

### Community 214 - "20261009_1100-d4e5f6a7b8c9_correct_legacy_environment_types.py"
Cohesion: 0.33
Nodes (3): downgrade(), Phase 2.1 — correct legacy ``environment_type`` classification. The Phase 2…, No-op: the correction is a best-effort classification, not reversible.…

### Community 215 - "api_key_service.py"
Cohesion: 0.22
Nodes (14): create_api_key(), list_api_keys(), AsyncSession, Request, UUID, API key lifecycle: creation with scope validation, listing, revocation., Live (non-revoked) keys owned by *owner_id*, newest first., Revoke a key owned by *owner_id*. Foreign keys look like NotFound (no leak). (+6 more)

### Community 216 - "README.md - NexusOps overview"
Cohesion: 0.37
Nodes (12): docker-compose.dev.yml - dev overlay, docker-compose.docker-sock.yml - docker socket override, docker-compose.yml - full stack definition, docs/agent.md - agent guide, docs/api.md - API guide, docs/architecture.md - system architecture, docs/deployment.md - deployment and operations guide, docs/development.md - developer guide (+4 more)

### Community 217 - "create_api_key"
Cohesion: 0.17
Nodes (16): create_api_key(), list_api_keys(), CurrentUser, DbSessionDep, get, post, Request, UUID (+8 more)

### Community 218 - "AcmeProvider"
Cohesion: 0.14
Nodes (13): AbstractAsyncContextManager, AcmeProvider, Protocol, The one thing the flow needs from a CA implementation: a session., Open questions — resolved (see phase5-design.md Appendix A), 10.8.3 The acceptance criterion that was met differently, and how 5.3.1 closed it, Appendix A — Decisions resolved here (that certificate-management.md left open), Approved and recorded in the Phase 5.1 closeout (2026-10-12) (+5 more)

### Community 219 - "update_organization"
Cohesion: 0.16
Nodes (14): create_organization(), list_my_organizations(), CurrentUser, DbSessionDep, get, IdentityUser, patch, post (+6 more)

### Community 220 - "Platform Vision — NexusOps"
Cohesion: 0.20
Nodes (10): 1. Where NexusOps is today, 2.1 What we are NOT building, 2.2 The wedge (differentiation), 2. The direction, 3. Guiding principles, 4. Customer journey (target), 5.1 Architecture overview (target), 5. Control plane / data plane boundary (+2 more)

### Community 221 - "AgentContainerIn"
Cohesion: 0.23
Nodes (13): AgentContainerIn, Observed container state reported by an agent., test_collected_container_entries_validate_with_ports(), test_container_ports_report_the_four_facts(), _container(), parametrize, test_allowed_container_statuses(), test_bogus_status_string_rejected() (+5 more)

### Community 222 - "20260923_1000-c4e2a1f7b9d3_rename_server_codenames_to_node.py"
Cohesion: 0.60
Nodes (4): downgrade(), rename ``server.*`` permission codenames to ``node.*`` The Node/Server…, _rename_permissions(), upgrade()

### Community 223 - "is_terminal"
Cohesion: 0.20
Nodes (14): is_retryable(), is_terminal(), Whether a generation has spent every attempt it was allowed., Whether a failed generation may be moved back to ``ORDERING``. A failure is…, Whether this generation will never move again. ``REVOKED`` and…, A short, sanitized sentence for ``status``. Never key material., retry_budget_exhausted(), status_detail_for() (+6 more)

### Community 224 - "_attempt_delivery"
Cohesion: 0.22
Nodes (14): _attempt_delivery(), decode_delivery_cursor(), _send(), encode_delivery_cursor(), list_deliveries(), _now(), datetime, UUID (+6 more)

### Community 225 - "ControlHandler"
Cohesion: 0.20
Nodes (8): BaseHTTPRequestHandler, clear_record(), ControlHandler, in_zone(), Remove the whole name, one record type, or **one value** of a type. The value-…, The journey's only way to publish a record — no shell, no shared volume., set_record(), snapshot()

### Community 226 - "20261012_1600-f5a6b7c8d9e0_phase5_org_dek_envelope.py"
Cohesion: 0.40
Nodes (3): downgrade(), Phase 5.2.1 — the organization DEK envelope. Two additive columns on…, Drop the envelope columns — unless doing so would destroy key material.

### Community 227 - "me"
Cohesion: 0.18
Nodes (10): me(), get, IdentityUser, The caller's identity, organizations, and authority in the active one.…, Organization, effective_permissions(), permissions_for_role(), User (+2 more)

### Community 228 - "update_role"
Cohesion: 0.08
Nodes (39): create_role(), delete_role(), list_permissions(), list_roles(), CurrentUser, DbSessionDep, get, patch (+31 more)

### Community 229 - "system_scope"
Cohesion: 0.18
Nodes (11): Run the enclosed block with tenant filtering off (maintenance only). ``reason``…, system_scope(), task, Claim up to CLAIM_BATCH due monitors and execute each check.…, run_due_monitors(), Loader criteria do not apply to DML — so the guard refuses instead. A silent…, One broadcast channel, two tenants: the frame's org decides who is told., A worker sweep claims across tenants and resolves each row's own owner. Both… (+3 more)

### Community 230 - "test_error_logging.py"
Cohesion: 0.22
Nodes (4): Regression: the catch-all 500 handler must not log raw exception text.…, _SpyLogger, test_unhandled_exception_handler_logs_class_not_message(), fastapi_testclient

### Community 231 - "register_exception_handlers"
Cohesion: 0.24
Nodes (9): _error_payload(), Any, FastAPI, Request, register_exception_handlers(), handle_app_error(), handle_http_exception(), handle_unexpected() (+1 more)

### Community 232 - "CertificateStatus"
Cohesion: 0.14
Nodes (15): alembic_autogenerate, alembic_migration, CertificateStatus, Certificate-level view of the *current* generation, derived, never stored raw.…, certificate_status_for(), The certificate-level status implied by a generation's state., derive_status(), The certificate's status and its explanation, derived from *generation*.… (+7 more)

### Community 233 - "record"
Cohesion: 0.06
Nodes (72): apply_node_proxy_config(), create_enrollment_token(), create_server(), delete_server(), _detail(), _enrollment_created(), _enrollment_out(), get_server() (+64 more)

### Community 234 - "_mutate_in_system_scope"
Cohesion: 0.27
Nodes (10): _container_id(), _create_node(), _mutate_in_system_scope(), The safety check runs again at enable time, not only at creation., test_a_container_without_published_ports_offers_nothing(), test_a_listener_conflict_is_named_precisely(), test_capability_that_goes_stale_between_creation_and_enable_blocks_the_route(), test_proxy_status_reports_the_preflight() (+2 more)

### Community 236 - "process_heartbeat"
Cohesion: 0.12
Nodes (24): agent_enroll(), agent_heartbeat(), agent_hello(), claim_operation(), DbDep, post, Request, Response (+16 more)

### Community 237 - "projects.py"
Cohesion: 0.07
Nodes (70): _app_out(), create_application(), create_environment(), create_project(), delete_application(), delete_environment(), delete_project(), get_application() (+62 more)

### Community 238 - "AuditLogPage.test.tsx"
Cohesion: 0.20
Nodes (5): AuditEntry, AuditLogPage(), formatTimestamp(), shortId(), mockedGet

### Community 239 - "client_ip"
Cohesion: 0.31
Nodes (9): client_ip(), _enforce(), node_rate_limit(), _dependency(), Request, _dependency(), Return a dependency keyed on the **authenticated node**, not the IP. A fleet…, Best-effort client IP; honours X-Forwarded-For from trusted proxies. Delegates… (+1 more)

### Community 240 - "parametrize"
Cohesion: 0.25
Nodes (9): is_simulation_url(), True when *url* targets the built-in simulated checker (``sim://``)., parametrize, test_non_simulation_urls(), test_private_and_special_addresses_are_forbidden(), test_private_targets_blocked_via_resolution(), test_public_addresses_are_allowed(), test_public_urls_pass_full_pipeline() (+1 more)

### Community 241 - "instant_pacing"
Cohesion: 0.40
Nodes (4): instant_pacing(), fixture, MonkeyPatch, Remove the per-line sleeps; pacing bounds are asserted separately.

### Community 243 - "ZoneResolution"
Cohesion: 0.25
Nodes (5): One zone a credential can write in, as the provider names it., Which zone holds a record name — or why that could not be established. ``zone…, The zone that holds *name*, or a reason it could not be determined., ZoneRef, ZoneResolution

### Community 244 - "test_app_gating.py"
Cohesion: 0.44
Nodes (8): _app_for_environment(), MonkeyPatch, ENVIRONMENT gating contract: docs exposure and HSTS (see .env.example).…, create_app() with get_settings() patched to the given environment., test_non_production_does_not_emit_hsts(), test_non_production_keeps_docs_and_schema(), test_production_emits_hsts(), test_production_hides_docs_and_schema()

### Community 245 - "test_tasks_util.py"
Cohesion: 0.36
Nodes (8): _answer(), _boom(), _nested(), Unit tests for the Celery-task async bridge (pure asyncio, no broker)., test_run_async_awaits_nested_coroutines(), test_run_async_is_repeatable_per_invocation(), test_run_async_propagates_exceptions(), test_run_async_returns_coroutine_result()

### Community 246 - "change_password"
Cohesion: 0.25
Nodes (8): change_password(), _optional_actor(), AsyncSession, Bootstrap the first owner account or accept an authenticated invitation., Change own password; other sessions are revoked, current one survives., Resolve credentials if presented; None for truly anonymous calls., register(), UserEnvelope

### Community 247 - ".__init__"
Cohesion: 0.12
Nodes (8): _FailingRewrapProvider, _OverlappingProvider, _PingPongProvider, Fails *only* ``rewrap_dek`` — a rotation that cannot reach its provider. The…, The deterministic provider with a real await point inside ``wrap_dek``. Without…, Holds one rewrap result open until the test releases it. The result is computed…, Hands control back to the test before every one of the first ``rounds`` rewrap…, _StaleSnapshotProvider

### Community 248 - "_validate_resolution"
Cohesion: 0.32
Nodes (7): _is_forbidden_address(), True when *addr* points into a network the server must never contact.…, Resolve *hostname* (AF_UNSPEC) and refuse any non-public answer., _validate_resolution(), test_validate_resolution_passes_hostname_through(), IPv4Address, IPv6Address

### Community 249 - "dispatch_event_frame"
Cohesion: 0.32
Nodes (8): _as_uuid(), dispatch_event_frame(), Any, Render an event frame into an ASCII-safe ``(subject, body)`` pair., Queue an event frame to every subscribed enabled channel; send immediately.…, render_frame(), A platform-level event has no tenant audience — it is not a broadcast., test_orgless_frame_notifies_nobody()

### Community 250 - "20260922_1000-a3f1c8d24b6e_add_tenancy_foundation.py"
Cohesion: 0.20
Nodes (12): _app_role_credentials(), _assert_fully_backfilled(), _backfill_org_ids(), _drop_constraint(), add tenancy foundation Phase 1 of the platform roadmap: organizations,…, Carry a value into a PL/pgSQL block. ``CREATE ROLE``/``ALTER ROLE`` are utility…, Application role name/password from settings (never hard-coded)., Point every pre-existing row at the bootstrap organization. ``audit_logs`` is… (+4 more)

### Community 251 - "cloudflare"
Cohesion: 0.25
Nodes (6): cloudflare(), _FakeCloudflare, fixture, MonkeyPatch, Every test in this module gets the fake, and no test can reach the network., The credential seam: a verdict plus the zones the token can see.

### Community 252 - "get_meta"
Cohesion: 0.29
Nodes (7): get_meta(), DbSessionDep, get, Public metadata; identity fields appear only for valid credentials., MetaOut, Instance metadata. Identity fields are populated only when the caller presents…, OptionalUser

### Community 253 - "2. The Node concept"
Cohesion: 0.29
Nodes (6): Alias for :attr:`extra`, so the API can expose open-ended agent facts. The…, 2.3 Infrastructure — Nodes, 2.1 Current shape (real), 2.2 Changes for the target model, 2.3 Capabilities (implemented, Phase 3), 2. The Node concept

### Community 254 - "ContainerListPage.test.tsx"
Cohesion: 0.29
Nodes (3): ApiError, server, serversPage

### Community 255 - "20261009_1300-a1b2c3d4e5f6_add_phase3_nodes_and_agent_v2.py"
Cohesion: 0.40
Nodes (4): _grant(), Phase 3 — Nodes & Agent v2 schema. Adds, in one migration with a single head: *…, Grant the app role on *table*; the migration role GUC carries the name. The…, upgrade()

### Community 256 - ".dispatch"
Cohesion: 0.60
Nodes (3): Request, Response, RequestResponseEndpoint

### Community 257 - "_FinalizingClient"
Cohesion: 0.33
Nodes (4): _FinalizingClient, Any, datetime, The one client method finalization uses, recording the resource it was given.

### Community 258 - "dependencies"
Cohesion: 0.33
Nodes (6): dependencies, lucide-react, react, react-dom, react-router-dom, @tanstack/react-query

### Community 259 - "LoginPage.tsx"
Cohesion: 0.33
Nodes (4): LoginPage, FieldErrors, MetaInfo, redirectTarget()

### Community 260 - "_validate_bundle"
Cohesion: 0.40
Nodes (5): _allowed_bundle_path(), The bundle fingerprint — byte-identical to the control plane's algorithm.…, Independently validate a bundle. Anything unexpected is refused., _tree_fingerprint(), _validate_bundle()

### Community 261 - "20261009_1200-e5f6a7b8c9d0_fix_environment_type_precedence.py"
Cohesion: 0.40
Nodes (3): downgrade(), Phase 2.2 — make legacy environment typing match the documented precedence. The…, No-op: the correction is a classification, not a reversible structure.…

### Community 262 - "enqueue_generation"
Cohesion: 0.50
Nodes (5): enqueue_generation(), _enqueue_issuance(), UUID, Hand one generation to the worker, but only once *db* commits. Inline is a…, Dispatch the worker task. Deliberately the only place that names it. Indirected…

### Community 264 - "20261016_1000-c9d0e1f2a3b4_phase53_generation_directory.py"
Cohesion: 0.28
Nodes (7): _assert_no_directory_recorded(), downgrade(), _drop_constraint(), Phase 5.3 — the issuance provenance pair on ``certificate_generations``. Adds,…, Remove the provenance pair — refusing while any generation records a directory., Raw ``ALTER TABLE ... DROP CONSTRAINT IF EXISTS`` (see the 5.2.2 migration)., Refuse a downgrade that would discard which CA a generation was ordered at.

### Community 265 - "known_directory_urls"
Cohesion: 0.50
Nodes (4): directory_known_predicate(), known_directory_urls(), Every ACME directory URL a generation may record, from the vocabulary. Read…, ``directory_url`` is NULL or names a directory in the vocabulary. The ``NULL``…

### Community 266 - "test_capability_report_shape_is_accepted"
Cohesion: 0.50
Nodes (4): CapabilityReport, One node-reported capability. ``present`` defaults to false, and a capability…, Whatever the pre-flight returns must satisfy the hello schema., test_capability_report_shape_is_accepted()

### Community 267 - "AcmeAccountKeyUnavailable"
Cohesion: 0.50
Nodes (3): AcmeAccountKeyUnavailable, RuntimeError, The stored account key cannot be read right now. One cause is named rather than…

### Community 268 - "enrollment_contract"
Cohesion: 0.67
Nodes (3): enrollment_contract(), Any, The minimum response an enrolling agent needs (facts about its new node).

### Community 269 - "websocket_endpoint"
Cohesion: 0.67
Nodes (3): websocket, Hand the socket to the hub (auth handshake handled there)., websocket_endpoint()

### Community 273 - "test_run_async_publishes_frames_scheduled_by_the_commit_hook"
Cohesion: 0.29
Nodes (5): _FakeDb, Stands in for an ``AsyncSession`` whose only job here is ``sync_session``. A…, The shape of a worker task whose last statement is a commit., test_run_async_publishes_frames_scheduled_by_the_commit_hook(), commit_then_return()

## Knowledge Gaps
- **488 isolated node(s):** `meta`, `SCHEMA`, `RESEARCH_COMMON`, `CHALLENGE_COMMON`, `TASKS` (+483 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 3167 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **23 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `6. Tooling: reproducible e2e` connect `sweep_session` to `typing`, `client.ts`, `test_ws_hub.py`, `proxy_service.py`, `get_settings`, `apply_scope_to_session`?**
  _High betweenness centrality (0.183) - this node is a cross-community bridge._
- **Why does `useEventStream()` connect `client.ts` to `apiGet`, `App.tsx`, `AuthContext.tsx`, `ServerDetailPage.tsx`, `sweep_session`, `@tanstack/react-query`?**
  _High betweenness centrality (0.183) - this node is a cross-community bridge._
- **Why does `TenancyScopeError` connect `typing` to `test_certificates.py`, `publish`, `test_org_dek_envelope.py`, `test_kek_selection.py`, `system_scope`, `assert_error_code`, `test_acme_accounts.py`, `sweep_session`, `enrollment_service.py`, `apply_scope_to_session`, `test_tenant_isolation.py`, `LogLine`, `AuthContext`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Are the 108 inferred relationships involving `AuthContext` (e.g. with `TenancyScopeError` and `MembershipStatus`) actually correct?**
  _`AuthContext` has 108 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `APIModel` (e.g. with `OperationSpec` and `test_specs_reject_unknown_params()`) actually correct?**
  _`APIModel` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `meta`, `SCHEMA`, `RESEARCH_COMMON` to the rest of the system?**
  _488 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `apiGet` be split into smaller, more focused modules?**
  _Cohesion score 0.057002457002457 - nodes in this community are weakly interconnected._