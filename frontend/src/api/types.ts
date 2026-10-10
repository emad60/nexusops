/** Shared API payload types (snake_case, mirroring the backend schemas). */

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface CursorPage<T> {
  items: T[];
  next_cursor: string | null;
  has_more: boolean;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  description: string;
  status: "ACTIVE" | "SUSPENDED";
  /** Auto-provisioned by the tenancy migration for data that pre-dates orgs. */
  is_provisional: boolean;
  renamed_at: string | null;
  created_at: string;
}

/** The caller's own membership: an organization plus their role in it. */
export interface Membership {
  organization: Organization;
  role_name: string | null;
  role_id: string | null;
  status: "ACTIVE" | "SUSPENDED";
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  /** Account state — instance-wide, not the tenant's view of the member. */
  is_active: boolean;
  status: "ACTIVE" | "LOCKED" | "DISABLED";
  /** Role held **in the active organization** (null until the membership loads). */
  role_id: string | null;
  role_name: string | null;
  /** The member's state in the active organization, independent of the account. */
  membership_status: "ACTIVE" | "SUSPENDED" | null;
  last_login_at: string | null;
  created_at: string;
}

export interface Role {
  id: string;
  name: string;
  description: string;
  is_system: boolean;
  permissions: string[];
  user_count?: number;
  created_at: string;
}

export interface SessionInfo {
  id: string;
  ip_address: string;
  device_label: string;
  user_agent: string;
  created_at: string;
  last_seen_at: string | null;
  expires_at: string;
  current: boolean;
}

export interface ApiKeyOut {
  id: string;
  name: string;
  key_prefix: string;
  scopes: string[];
  last_used_at: string | null;
  expires_at: string | null;
  revoked_at: string | null;
  created_at: string;
}

export interface Tag {
  id: string;
  name: string;
  color: string;
}

export interface ServerSummary {
  id: string;
  name: string;
  hostname: string;
  ip_address: string;
  os_name: string;
  os_version: string;
  arch: string;
  environment: string;
  location: string;
  description: string;
  status: "ONLINE" | "OFFLINE" | "DEGRADED" | "UNKNOWN";
  cpu_cores: number;
  memory_total_mb: number;
  disk_total_gb: number;
  agent_version: string;
  enrolled: boolean;
  simulated: boolean;
  heartbeat_interval_seconds: number;
  offline_after_seconds: number | null;
  uptime_seconds: number;
  tags: Tag[];
  docker_host: { id: string; name: string; status: string } | null;
  last_heartbeat_at: string | null;
  created_at: string;
  /**
   * Negotiated wire protocol. `null` means a pre-v2 (legacy) agent — treat it
   * as protocol 1, never as "supports v2".
   */
  protocol_version?: number | null;
  /**
   * Self-reported capabilities (hello v2). An **empty** object means the node
   * has not reported any: it is *unverified*, never "has everything". The
   * dispatch gate and the UI must both read it that way.
   */
  capabilities?: Record<string, CapabilityReport>;
  /** Whether the node has reported capabilities at all. */
  capabilities_reported?: boolean;
  /** Open-ended host facts reported at hello v2. */
  facts?: Record<string, unknown>;
  /** Set when an operator revoked this node's credential (kill switch). */
  credential_revoked_at?: string | null;
  /** Whether the credential is currently revoked. */
  agent_revoked?: boolean;
}

/** One node-reported capability from hello v2. */
export interface CapabilityReport {
  present: boolean;
  version?: string | null;
  api_version?: string | null;
}

/** Operation type whitelist (mirrors the backend `OperationType` enum). */
export type OperationType =
  | "container.start"
  | "container.stop"
  | "container.restart"
  | "container.remove"
  | "logs.tail"
  | "nginx.bootstrap"
  | "nginx.apply"
  | "nginx.status";

export type OperationStatus =
  | "PENDING"
  | "CLAIMED"
  | "RUNNING"
  | "SUCCEEDED"
  | "FAILED"
  | "EXPIRED"
  | "CANCELLED";

/**
 * One queued/executed node operation. `PENDING` is *queued*, not done: the UI
 * must never present it as success.
 */
export interface OperationItem {
  id: string;
  node_id: string;
  type: OperationType;
  status: OperationStatus;
  params: Record<string, unknown>;
  result: Record<string, unknown> | null;
  error_code: string | null;
  error_message: string | null;
  requested_by_id: string | null;
  attempts: number;
  claimed_at: string | null;
  available_until: string;
  execution_deadline: string | null;
  expires_at: string;
  created_at: string;
  updated_at: string;
}

/** Derived lifecycle state of an enrollment token. */
export type EnrollmentTokenState = "ACTIVE" | "USED" | "REVOKED" | "EXPIRED";

/** Enrollment-token metadata. Never carries the raw token. */
export interface EnrollmentTokenItem {
  id: string;
  org_id: string;
  name: string;
  note: string;
  single_use: boolean;
  expires_at: string;
  revoked_at: string | null;
  used_at: string | null;
  used_by_node_id: string | null;
  node_id: string | null;
  created_by_id: string | null;
  state: EnrollmentTokenState;
  created_at: string;
}

/** The one response that carries the raw enrollment token. */
export interface EnrollmentTokenCreated extends EnrollmentTokenItem {
  token: string;
  install_hint: string;
}

export interface ServerDetail extends ServerSummary {
  recent_events: EventItem[];
  counts: { containers_running: number; containers_total: number };
}

export interface ContainerOut {
  id: string;
  container_id: string;
  name: string;
  image_ref: string;
  command: string;
  status:
    | "RUNNING"
    | "EXITED"
    | "PAUSED"
    | "CREATED"
    | "RESTARTING"
    | "DEAD"
    | "REMOVED";
  health: "NONE" | "STARTING" | "HEALTHY" | "UNHEALTHY";
  ports: Array<{ private?: number; public?: number; type?: string }>;
  env_keys: string[];
  labels: Record<string, string>;
  mounts: Array<Record<string, unknown>>;
  restart_count: number;
  cpu_percent: number | null;
  mem_used_mb: number | null;
  mem_limit_mb: number | null;
  net_rx_kb_s: number | null;
  net_tx_kb_s: number | null;
  started_at: string | null;
  observed_at: string;
  simulated: boolean;
  docker_host: { id: string; name: string; status: string } | null;
  server: { id: string; name: string } | null;
  created_at: string;
}

export interface DockerHostOut {
  id: string;
  server_id: string | null;
  name: string;
  endpoint_url: string;
  tls_verify: boolean;
  status: "AVAILABLE" | "UNAVAILABLE" | "UNKNOWN";
  last_checked_at: string | null;
  last_error: string;
  created_at: string;
}

export interface MonitorOut {
  id: string;
  name: string;
  url: string;
  method: string;
  interval_seconds: number;
  timeout_seconds: number;
  expected_status: number;
  enabled: boolean;
  status: "PENDING" | "UP" | "DOWN" | "PAUSED";
  consecutive_failures: number;
  consecutive_successes: number;
  failure_threshold: number;
  success_threshold: number;
  next_check_at: string;
  last_check_at: string | null;
  last_success_at: string | null;
  last_failure_at: string | null;
  project_name: string | null;
  current_open_incident_id: string | null;
  uptime_pct_24h: number | null;
  created_at: string;
}

export interface CheckOut {
  id: number;
  monitor_id: string;
  checked_at: string;
  result: "SUCCESS" | "FAILURE" | "TIMEOUT" | "ERROR";
  response_time_ms: number | null;
  status_code: number | null;
  error: string;
}

export interface IncidentEventOut {
  id: string;
  kind: string;
  message: string;
  occurred_at: string;
}

export interface IncidentOut {
  id: string;
  monitor_id: string;
  monitor_name?: string | null;
  title: string;
  severity: "CRITICAL" | "MAJOR" | "MINOR" | "WARNING";
  status: "OPEN" | "ACKNOWLEDGED" | "RESOLVED";
  failure_count: number;
  opened_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
  resolution: string;
  timeline?: IncidentEventOut[];
  created_at: string;
}

export interface AlertOut {
  id: string;
  severity: "INFO" | "WARNING" | "CRITICAL";
  title: string;
  body: string;
  event_type: string;
  source: string;
  resource_type: string | null;
  resource_id: string | null;
  read_at: string | null;
  created_at: string;
}

export interface ChannelOut {
  id: string;
  name: string;
  type: "EMAIL" | "WEBHOOK";
  display_target: string;
  events: string[];
  enabled: boolean;
  created_at: string;
}

export interface DeliveryOut {
  id: string;
  channel_id: string;
  event_type: string;
  subject: string;
  status: "PENDING" | "SENT" | "FAILED" | "SKIPPED";
  attempts: number;
  last_error: string;
  sent_at: string | null;
  created_at: string;
}

export interface ProjectOut {
  id: string;
  name: string;
  description: string;
  repository_url: string;
  default_branch: string;
  /** Project base config (flat string→string); environment overrides win per key. */
  config?: Record<string, string>;
  applications?: ApplicationOut[];
  /** Phase 2: environments are project-scoped and listed on project detail. */
  environments?: EnvironmentOut[];
  created_at: string;
}

export interface ApplicationOut {
  id: string;
  project_id: string;
  name: string;
  slug: string;
  description: string;
  build_config: Record<string, unknown>;
  current_version: string | null;
  latest_deployment?: {
    number: number;
    status: DeploymentStatus;
    version: string;
    finished_at: string | null;
  } | null;
  created_at: string;
}

export type DeploymentStatus =
  | "QUEUED"
  | "RUNNING"
  | "SUCCESS"
  | "FAILED"
  | "CANCELLED"
  | "ROLLBACK";

/** Environment kinds. Descriptive only — never an authorization dimension. */
export type EnvironmentType = "DEV" | "STAGING" | "PROD";

/** UI labels for the stored environment type. */
export const ENVIRONMENT_TYPE_LABELS: Record<EnvironmentType, string> = {
  DEV: "Development",
  STAGING: "Staging",
  PROD: "Production",
};

/**
 * A project-scoped deployment environment (Phase 2). It belongs to a
 * **project**, not an application; `config` holds this environment's overrides
 * over the project base config.
 */
export interface EnvironmentOut {
  id: string;
  project_id: string;
  name: string;
  slug: string;
  environment_type: EnvironmentType;
  server_id: string | null;
  healthcheck_path: string;
  auto_deploy: boolean;
  config: Record<string, string>;
  created_at: string;
}

/**
 * Environment detail. The three configuration layers are returned separately so
 * the UI can show where a value comes from. `secret_references` are key names
 * only — secret values are never returned by any endpoint.
 */
export interface EnvironmentDetailOut extends EnvironmentOut {
  project_config: Record<string, string>;
  effective_config: Record<string, string>;
  secret_references: string[];
  application_count: number;
  deployment_count: number;
  secret_count: number;
}

export interface DeploymentStepOut {
  id: string;
  idx: number;
  name: string;
  status: "PENDING" | "RUNNING" | "SUCCESS" | "FAILED" | "SKIPPED" | "CANCELLED";
  output: string;
  error: string;
  retry_count: number;
  started_at: string | null;
  finished_at: string | null;
}

export interface DeploymentOut {
  id: string;
  number: number;
  application_id: string;
  environment_id: string;
  version: string;
  git_commit: string;
  notes: string;
  status: DeploymentStatus;
  trigger: "MANUAL" | "API" | "ROLLBACK" | "AUTO";
  is_rollback: boolean;
  triggered_by_email?: string | null;
  queued_at: string | null;
  started_at: string | null;
  finished_at: string | null;
  duration_ms: number | null;
  failure_reason: string;
  cancel_requested: boolean;
  application?: { id: string; name: string; slug: string };
  environment?: { id: string; name: string };
  steps?: DeploymentStepOut[];
  step_summary?: { total: number; done: number; failed: number };
  created_at: string;
}

export interface DeploymentLogLine {
  id: number;
  stream: string;
  level: string;
  message: string;
  ts: string;
}

export interface EventItem {
  id: string;
  type: string;
  level: "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL";
  message: string;
  actor_type: string;
  resource_type: string | null;
  resource_id: string | null;
  data: Record<string, unknown>;
  created_at: string;
}

export interface AuditEntry {
  id: string;
  actor_email: string;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  ip_address: string;
  result: "SUCCESS" | "DENIED" | "ERROR";
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface SecretRow {
  id: string;
  key: string;
  version: number;
  digest: string;
  description: string;
  project_id: string | null;
  environment_id: string | null;
  rotated_at: string | null;
  rotated_by_email?: string | null;
  created_at: string;
  updated_at: string;
}

/** One immutable secret version's metadata. Never carries a value or ciphertext. */
export interface SecretVersionRow {
  id: string;
  secret_id: string;
  version: number;
  digest: string;
  created_by_email?: string | null;
  created_at: string;
}

export interface MetricPoint {
  ts: string;
  [series: string]: number | string;
}

export interface MetricsResponse {
  range: string;
  granularity: "RAW" | "HOURLY" | "DAILY";
  points: MetricPoint[];
}

export interface DashboardSummary {
  servers_total: number;
  servers_online: number;
  servers_offline: number;
  servers_degraded: number;
  containers_running: number;
  monitors_up: number;
  monitors_down: number;
  monitors_paused: number;
  incidents_open: number;
  deployments_today: number;
  deployments_failed_today: number;
  unread_alerts: number;
  avg_cpu_percent?: number | null;
  avg_mem_percent?: number | null;
  recent_events: EventItem[];
}

export interface SearchResult {
  nodes: SearchHit[];
  containers: SearchHit[];
  deployments: SearchHit[];
  projects: SearchHit[];
  monitors: SearchHit[];
  incidents: SearchHit[];
  users: SearchHit[];
}

export interface SearchHit {
  type: string;
  id: string;
  title: string;
  subtitle: string;
  url_path: string;
}

/* --- Phase 4: domains and routes ------------------------------------------ */

/** Domain ownership lifecycle. Only `VERIFIED` may back an enabled route. */
export type DomainStatus =
  | "PENDING"
  | "VERIFYING"
  | "VERIFIED"
  | "STALE"
  | "UNVERIFIED"
  | "FAILED";

/**
 * How a route's desired configuration relates to what the node actually serves.
 * `PENDING` means an apply is queued but not confirmed — never "applied".
 */
export type RouteConfigState = "PENDING" | "IN_SYNC" | "STALE" | "FAILED";

/** The exact DNS record a domain owner has to publish, while it is actionable. */
export interface DomainVerificationOut {
  record_name: string;
  record_type: string;
  record_value: string;
  active: boolean;
}

/** Best-effort A/AAAA observation — a warning only, never a gate. */
export interface DomainReachabilityOut {
  hostname: string | null;
  addresses: string[];
  expected_addresses: string[];
  resolves_to_node: boolean | null;
  checked_at: string | null;
  warning: string | null;
}

/** Domain read model. `verified` is derived from `status` server-side. */
export interface DomainOut {
  id: string;
  project_id: string | null;
  project_name: string | null;
  name: string;
  status: DomainStatus;
  verified: boolean;
  verified_at: string | null;
  last_checked_at: string | null;
  proof_lost_at: string | null;
  stale_expires_at: string | null;
  attempt_count: number;
  last_error: string;
  ns_snapshot: string[];
  verification: DomainVerificationOut | null;
  reachability: DomainReachabilityOut | null;
  route_count: number;
  enabled_route_count: number;
  created_at: string;
  updated_at: string;
}

export interface DomainDetailOut extends DomainOut {
  routes: RouteOut[];
}

/** One header a route adds: to the response, or to the upstream request. */
export interface RouteHeader {
  name: string;
  value: string;
  target: "response" | "proxy";
}

export interface RateLimit {
  requests: number;
  window: "1s" | "1m";
  burst: number;
}

/** A fixed host redirect. Phase 4 has no field for a scheme change. */
export interface RouteRedirect {
  to_host: string;
  code: number;
}

/** Route read model. HTTP only until Phase 5 ships certificates. */
export interface RouteOut {
  id: string;
  domain_id: string;
  domain_name: string | null;
  hostname: string;
  path: string;
  url: string;
  node_id: string;
  node_name: string | null;
  container_id: string | null;
  container_name: string | null;
  container_ref: string | null;
  port: number;
  scheme: string;
  enabled: boolean;
  config_state: RouteConfigState;
  headers: RouteHeader[];
  rate_limit: RateLimit | null;
  redirect: RouteRedirect | null;
  monitor_id: string | null;
  monitor_optout: boolean;
  last_applied_at: string | null;
  last_bundle_id: string | null;
  last_apply_error: string;
  /** Human-readable explanation of `config_state` — never raw configuration. */
  status_detail: string;
  created_at: string;
  updated_at: string;
}

export interface RouteDetailOut extends RouteOut {
  domain_status: string;
}

/** The node's reported nginx pre-flight, bounded to the useful facts. */
export interface NodeProxyCapabilityOut {
  present: boolean;
  version: string | null;
  running: boolean | null;
  config_test_ok: boolean | null;
  routing_eligible: boolean;
  reason: string;
  listener_80: "MANAGED" | "FREE" | "OTHER" | "UNKNOWN";
  listener_443: "MANAGED" | "FREE" | "OTHER" | "UNKNOWN";
}

export interface NodeProxyStatusOut {
  id: string;
  node_id: string;
  node_name: string;
  provider: string;
  capability: NodeProxyCapabilityOut;
  eligible: boolean;
  ineligible_reason: string;
  expected_bundle_id: string | null;
  live_bundle_id: string | null;
  drift: boolean | null;
  last_status_at: string | null;
  last_status_error: string;
  route_total: number;
  route_enabled: number;
  route_in_sync: number;
  route_stale: number;
  route_failed: number;
  last_applied_at: string | null;
  last_apply_error: string;
  created_at: string;
  updated_at: string;
}

/** One genuinely usable published port reported by the node's agent. */
export interface UpstreamPortOut {
  host_port: number;
  container_port: number;
  protocol: string;
  bind_address: string;
  upstream_host: string;
}

/** A container that can actually back a route on a node. */
export interface UpstreamContainerOut {
  id: string;
  container_id: string;
  name: string;
  image_ref: string;
  status: string;
  upstream_ports: UpstreamPortOut[];
  unavailable_reason: string | null;
}
