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

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  status: "ACTIVE" | "LOCKED" | "DISABLED";
  role_id: string | null;
  role_name: string | null;
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
  applications?: ApplicationOut[];
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

export interface EnvironmentOut {
  id: string;
  application_id: string;
  name: string;
  slug: string;
  server_id: string | null;
  healthcheck_path: string;
  auto_deploy: boolean;
  config: Record<string, unknown>;
  created_at: string;
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
  rotated_at: string | null;
  rotated_by_email?: string | null;
  created_at: string;
  updated_at: string;
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
  servers: SearchHit[];
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
