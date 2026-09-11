import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { ApiError, apiDelete, apiGet, apiPatch, apiPost } from "../api/client";
import type { ContainerOut, MetricPoint, Page, ServerDetail } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { EmptyState, ErrorBlock, LoadingBlock, Modal, StatusBadge, TagChip } from "../components/ui";
import { Pagination } from "../components/Pagination";
import { LineChart, type ChartSeries } from "../components/LineChart";
import { useToast } from "../components/toast";
import { useEventStream } from "../hooks/useEventStream";
import {
  formatBytesMb,
  formatDateTime,
  formatGb,
  formatPercent,
  formatRelative,
  formatUptime,
} from "../lib/format";

const CONTAINER_PAGE_SIZE = 8;
const METRIC_RANGES = ["1h", "6h", "24h", "7d", "30d"] as const;

/** Response of POST /servers/{id}/agent-token — the raw token is shown exactly once. */
interface EnrollTokenOut {
  agent_token: string;
  install_hint: string;
}

/** Response of GET /servers/{id}/metrics/latest. */
interface MetricSnapshot {
  server_id: string;
  recorded_at: string;
  cpu_percent: number;
  mem_used_mb: number;
  mem_percent: number;
  disk_used_gb: number;
  disk_percent: number;
  net_rx_kb_s: number;
  net_tx_kb_s: number;
  load1: number;
  uptime_seconds: number;
}

/** Response of GET /servers/{id}/metrics (bucketed timeseries). */
interface ServerTimeseries {
  range: string;
  granularity: string;
  points: MetricPoint[];
}

interface LiveSample {
  ts: number;
  cpu_percent: number | null;
  mem_percent: number | null;
  mem_used_mb: number | null;
  disk_percent: number | null;
}

interface CurrentMetrics {
  cpu_percent: number | null;
  mem_percent: number | null;
  mem_used_mb: number | null;
  disk_percent: number | null;
}

interface ServerFormValues {
  name: string;
  hostname: string;
  ip_address: string;
  os_name: string;
  os_version: string;
  arch: string;
  environment: string;
  location: string;
  description: string;
  heartbeat_interval_seconds: string;
  offline_after_seconds: string;
  tags: string;
  simulated: boolean;
}

/** Partial payload for PATCH /servers/{id} (mirrors the backend ServerUpdate schema). */
interface ServerUpdatePayload {
  name?: string;
  hostname?: string;
  ip_address?: string | null;
  os_name?: string;
  os_version?: string;
  arch?: string;
  environment?: string;
  location?: string;
  description?: string;
  heartbeat_interval_seconds?: number;
  offline_after_seconds?: number | null;
  tags?: string[];
  simulated?: boolean;
}

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return `${error.code}: ${error.message}`;
  if (error instanceof Error) return error.message;
  return "Request failed";
}

function finite(value: unknown): number | null {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function initialValues(server: ServerDetail): ServerFormValues {
  return {
    name: server.name,
    hostname: server.hostname,
    ip_address: server.ip_address,
    os_name: server.os_name,
    os_version: server.os_version,
    arch: server.arch,
    environment: server.environment,
    location: server.location,
    description: server.description,
    heartbeat_interval_seconds: String(server.heartbeat_interval_seconds),
    offline_after_seconds:
      server.offline_after_seconds == null ? "" : String(server.offline_after_seconds),
    tags: server.tags.map((tag) => tag.name).join(", "),
    simulated: server.simulated,
  };
}

function buildUpdatePayload(values: ServerFormValues): ServerUpdatePayload | string {
  const name = values.name.trim();
  const hostname = values.hostname.trim();
  if (!name) return "Name is required.";
  if (!hostname) return "Hostname is required.";

  const intervalRaw = values.heartbeat_interval_seconds.trim();
  let interval = 30;
  if (intervalRaw) {
    interval = Number(intervalRaw);
    if (!Number.isFinite(interval) || interval < 5 || interval > 3600) {
      return "Heartbeat interval must be between 5 and 3600 seconds.";
    }
  }

  const offlineRaw = values.offline_after_seconds.trim();
  let offlineAfter: number | null = null;
  if (offlineRaw) {
    offlineAfter = Number(offlineRaw);
    if (!Number.isFinite(offlineAfter) || offlineAfter <= 0) {
      return "Offline threshold must be a positive number of seconds.";
    }
  }

  return {
    name,
    hostname,
    ip_address: values.ip_address.trim(),
    os_name: values.os_name.trim(),
    os_version: values.os_version.trim(),
    arch: values.arch.trim(),
    environment: values.environment.trim() || "production",
    location: values.location.trim(),
    description: values.description.trim(),
    heartbeat_interval_seconds: interval,
    offline_after_seconds: offlineAfter,
    tags: values.tags
      .split(",")
      .map((tag) => tag.trim())
      .filter(Boolean),
    simulated: values.simulated,
  };
}

function MetricStat({
  label,
  value,
  pct,
  foot,
}: {
  label: string;
  value: string;
  pct?: number | null;
  foot?: string;
}) {
  const level = pct == null ? "" : pct >= 90 ? "err" : pct >= 75 ? "warn" : "ok";
  return (
    <div className="card stat-card">
      <div className="stat-label">{label}</div>
      <div className={`stat-value ${level}`}>{value}</div>
      {typeof pct === "number" ? (
        <div className="progress-track">
          <div className={`progress-fill ${level}`} style={{ width: `${Math.min(100, Math.max(0, pct))}%` }} />
        </div>
      ) : null}
      {foot ? <div className="stat-foot">{foot}</div> : null}
    </div>
  );
}

function EditServerModal({ server, onClose }: { server: ServerDetail; onClose: () => void }) {
  const notify = useToast();
  const queryClient = useQueryClient();
  const [values, setValues] = useState<ServerFormValues>(() => initialValues(server));
  const [formError, setFormError] = useState<string | null>(null);

  const updateMutation = useMutation({
    mutationFn: (payload: ServerUpdatePayload) =>
      apiPatch<ServerDetail>(`/servers/${server.id}`, payload),
    onSuccess: (updated) => {
      notify(`Server ${updated.name} updated`, "success");
      void queryClient.invalidateQueries({ queryKey: ["server", server.id] });
      void queryClient.invalidateQueries({ queryKey: ["servers"] });
      onClose();
    },
    onError: (error) => notify(errorMessage(error), "error"),
  });

  const set = <K extends keyof ServerFormValues>(key: K, value: ServerFormValues[K]) =>
    setValues((current) => ({ ...current, [key]: value }));

  const submit = () => {
    const payload = buildUpdatePayload(values);
    if (typeof payload === "string") {
      setFormError(payload);
      return;
    }
    setFormError(null);
    updateMutation.mutate(payload);
  };

  return (
    <Modal open title={`Edit ${server.name}`} onClose={onClose} wide>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <div className="field-row">
          <div className="field">
            <label htmlFor="server-edit-name">Name *</label>
            <input
              id="server-edit-name"
              className="input"
              value={values.name}
              onChange={(e) => set("name", e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="server-edit-hostname">Hostname *</label>
            <input
              id="server-edit-hostname"
              className="input"
              value={values.hostname}
              onChange={(e) => set("hostname", e.target.value)}
            />
          </div>
        </div>
        <div className="field-row">
          <div className="field">
            <label htmlFor="server-edit-ip">IP address</label>
            <input
              id="server-edit-ip"
              className="input"
              value={values.ip_address}
              onChange={(e) => set("ip_address", e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="server-edit-environment">Environment</label>
            <input
              id="server-edit-environment"
              className="input"
              value={values.environment}
              onChange={(e) => set("environment", e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="server-edit-arch">Architecture</label>
            <input
              id="server-edit-arch"
              className="input"
              value={values.arch}
              onChange={(e) => set("arch", e.target.value)}
            />
          </div>
        </div>
        <div className="field-row">
          <div className="field">
            <label htmlFor="server-edit-os-name">OS</label>
            <input
              id="server-edit-os-name"
              className="input"
              value={values.os_name}
              onChange={(e) => set("os_name", e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="server-edit-os-version">OS version</label>
            <input
              id="server-edit-os-version"
              className="input"
              value={values.os_version}
              onChange={(e) => set("os_version", e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="server-edit-location">Location</label>
            <input
              id="server-edit-location"
              className="input"
              value={values.location}
              onChange={(e) => set("location", e.target.value)}
            />
          </div>
        </div>
        <div className="field-row">
          <div className="field">
            <label htmlFor="server-edit-heartbeat">Heartbeat interval (seconds)</label>
            <input
              id="server-edit-heartbeat"
              className="input"
              type="number"
              min={5}
              max={3600}
              value={values.heartbeat_interval_seconds}
              onChange={(e) => set("heartbeat_interval_seconds", e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="server-edit-offline-after">Offline after (seconds, optional)</label>
            <input
              id="server-edit-offline-after"
              className="input"
              type="number"
              min={1}
              value={values.offline_after_seconds}
              onChange={(e) => set("offline_after_seconds", e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="server-edit-tags">Tags (comma separated)</label>
            <input
              id="server-edit-tags"
              className="input"
              value={values.tags}
              onChange={(e) => set("tags", e.target.value)}
            />
          </div>
        </div>
        <div className="field">
          <label htmlFor="server-edit-description">Description</label>
          <textarea
            id="server-edit-description"
            className="input"
            rows={2}
            value={values.description}
            onChange={(e) => set("description", e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="server-edit-simulated">
            <input
              id="server-edit-simulated"
              type="checkbox"
              checked={values.simulated}
              onChange={(e) => set("simulated", e.target.checked)}
            />{" "}
            Simulated server (demo data)
          </label>
        </div>
        {formError ? (
          <p className="form-error" role="alert">
            {formError}
          </p>
        ) : null}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn primary" disabled={updateMutation.isPending}>
            {updateMutation.isPending ? "Saving…" : "Save changes"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export default function ServerDetailPage() {
  const params = useParams();
  const serverId = params.serverId;
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const notify = useToast();
  const queryClient = useQueryClient();

  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [issuedToken, setIssuedToken] = useState<EnrollTokenOut | null>(null);
  const [range, setRange] = useState<(typeof METRIC_RANGES)[number]>("24h");
  const [containersOffset, setContainersOffset] = useState(0);
  const [live, setLive] = useState<{ latest: LiveSample | null; samples: LiveSample[] }>({
    latest: null,
    samples: [],
  });

  // Live per-server metrics frames: {server_id, ts, cpu_percent, mem_percent,
  // mem_used_mb, disk_percent} published on the server-metrics channel.
  useEventStream(
    serverId ? [{ channel: "server-metrics", params: { server_id: serverId } }] : [],
    (frame) => {
      const data = frame.data ?? {};
      const parsedTs = Date.parse(String(data.ts ?? ""));
      const sample: LiveSample = {
        ts: Number.isNaN(parsedTs) ? Date.now() : parsedTs,
        cpu_percent: finite(data.cpu_percent),
        mem_percent: finite(data.mem_percent),
        mem_used_mb: finite(data.mem_used_mb),
        disk_percent: finite(data.disk_percent),
      };
      if (
        sample.cpu_percent == null &&
        sample.mem_percent == null &&
        sample.disk_percent == null
      ) {
        return;
      }
      setLive((prev) => ({
        latest: sample,
        samples: [...prev.samples, sample].slice(-240),
      }));
    },
  );

  useEffect(() => {
    // Switching servers (same route instance) must drop live state and paging.
    setLive({ latest: null, samples: [] });
    setContainersOffset(0);
  }, [serverId]);

  const serverQuery = useQuery({
    queryKey: ["server", serverId],
    queryFn: ({ signal }) => apiGet<ServerDetail>(`/servers/${serverId}`, undefined, signal),
    enabled: Boolean(serverId),
    // Heartbeats arrive out-of-band (agent → backend), so liveness changes are
    // not tied to any page action: poll gently so the status badge stays true.
    refetchInterval: 10_000,
  });

  const historyQuery = useQuery({
    queryKey: ["server-metrics", serverId, range],
    queryFn: ({ signal }) =>
      apiGet<ServerTimeseries>(
        `/servers/${serverId}/metrics`,
        { range, metrics: "cpu_percent,mem_percent,disk_percent" },
        signal,
      ),
    enabled: Boolean(serverId),
  });

  const latestQuery = useQuery({
    queryKey: ["server-metrics-latest", serverId],
    queryFn: async () => {
      try {
        return await apiGet<MetricSnapshot>(`/servers/${serverId}/metrics/latest`);
      } catch (error) {
        // 404 simply means the agent has not reported metrics yet.
        if (error instanceof ApiError && error.status === 404) return null;
        throw error;
      }
    },
    enabled: Boolean(serverId),
  });

  const containersQuery = useQuery({
    queryKey: ["containers", { server_id: serverId, offset: containersOffset }],
    queryFn: ({ signal }) =>
      apiGet<Page<ContainerOut>>(
        "/containers",
        {
          server_id: serverId,
          limit: CONTAINER_PAGE_SIZE,
          offset: containersOffset,
          sort: "observed_at",
          order: "desc",
        },
        signal,
      ),
    enabled: Boolean(serverId),
    placeholderData: keepPreviousData,
    // Inventory rows arrive out-of-band (agent heartbeat → backend), not from
    // any action on this page, so poll gently to keep the list truthful.
    refetchInterval: 10_000,
  });

  const tokenMutation = useMutation({
    mutationFn: () => {
      if (!serverId) return Promise.reject(new Error("Missing server id"));
      return apiPost<EnrollTokenOut>(`/servers/${serverId}/agent-token`);
    },
    onSuccess: (data) => {
      setIssuedToken(data);
      notify("Agent token issued — copy it now, it will not be shown again", "success");
    },
    onError: (error) => notify(errorMessage(error), "error"),
  });

  const deleteMutation = useMutation({
    mutationFn: () => {
      if (!serverId) return Promise.reject(new Error("Missing server id"));
      return apiDelete<void>(`/servers/${serverId}`);
    },
    onSuccess: () => {
      notify(`Server ${serverQuery.data?.name ?? ""} deleted`, "success");
      void queryClient.invalidateQueries({ queryKey: ["servers"] });
      navigate("/servers");
    },
    onError: (error) => notify(errorMessage(error), "error"),
  });

  const historyPoints = historyQuery.data?.points;
  const chartSeries: ChartSeries[] = useMemo(() => {
    const points = historyPoints ?? [];
    const build = (
      avgKey: string,
      pick: (sample: LiveSample) => number | null,
      name: string,
      color: string,
    ): ChartSeries => {
      const history = points
        .map((point) => ({ ts: Date.parse(point.ts), value: finite(point[avgKey]) }))
        .filter((point) => !Number.isNaN(point.ts));
      const lastTs = history.length > 0 ? history[history.length - 1].ts : 0;
      const tail = live.samples
        .filter((sample) => sample.ts > lastTs)
        .map((sample) => ({ ts: sample.ts, value: pick(sample) }));
      return { name, color, points: [...history, ...tail] };
    };
    return [
      build("cpu_percent_avg", (s) => s.cpu_percent, "CPU", "#38bdf8"),
      build("mem_percent_avg", (s) => s.mem_percent, "Memory", "#34d399"),
      build("disk_percent_avg", (s) => s.disk_percent, "Disk", "#fbbf24"),
    ];
  }, [historyPoints, live.samples]);

  if (!serverId) {
    return (
      <EmptyState
        title="Server not found"
        hint="The address does not include a server id."
      />
    );
  }

  if (serverQuery.isPending) {
    return <LoadingBlock label="Loading server…" />;
  }

  if (serverQuery.isError || !serverQuery.data) {
    return <ErrorBlock error={serverQuery.error} />;
  }

  const server = serverQuery.data;
  const canUpdate = hasPermission("server.update");
  const canDelete = hasPermission("server.delete");

  const snapshot = latestQuery.data;
  const current: CurrentMetrics | null =
    live.latest ??
    (snapshot
      ? {
          cpu_percent: snapshot.cpu_percent,
          mem_percent: snapshot.mem_percent,
          mem_used_mb: snapshot.mem_used_mb,
          disk_percent: snapshot.disk_percent,
        }
      : null);

  const copyToken = async () => {
    if (!issuedToken) return;
    try {
      await navigator.clipboard.writeText(issuedToken.agent_token);
      notify("Token copied to clipboard", "success");
    } catch {
      notify("Clipboard unavailable — select the token and copy it manually", "error");
    }
  };

  return (
    <section aria-labelledby="server-heading">
      <div className="page-head">
        <div className="page-title">
          <h1 id="server-heading">
            {server.name} <StatusBadge value={server.status} />
            {server.simulated ? <span className="badge WARNING no-dot">SIMULATED</span> : null}
          </h1>
          <p className="page-sub">
            {server.hostname} · {server.environment}
            {server.description ? ` — ${server.description}` : ""}
          </p>
        </div>
        <div className="page-actions">
          <Link className="btn ghost sm" to="/audit-logs">
            Audit log
          </Link>
          {canUpdate ? (
            <button
              type="button"
              className="btn sm"
              onClick={() => tokenMutation.mutate()}
              disabled={tokenMutation.isPending}
            >
              {tokenMutation.isPending ? "Issuing…" : "Issue agent token"}
            </button>
          ) : null}
          {canUpdate ? (
            <button type="button" className="btn sm" onClick={() => setEditOpen(true)}>
              Edit
            </button>
          ) : null}
          {canDelete ? (
            <button type="button" className="btn danger sm" onClick={() => setDeleteOpen(true)}>
              Delete
            </button>
          ) : null}
        </div>
      </div>

      <div className="grid cols-4 mb-16">
        <MetricStat
          label="CPU"
          value={formatPercent(current?.cpu_percent ?? null)}
          pct={current?.cpu_percent ?? null}
          foot={`${server.cpu_cores} vCPU`}
        />
        <MetricStat
          label="Memory"
          value={formatPercent(current?.mem_percent ?? null)}
          pct={current?.mem_percent ?? null}
          foot={`${formatBytesMb(current?.mem_used_mb ?? null)} of ${formatBytesMb(server.memory_total_mb)}`}
        />
        <MetricStat
          label="Disk"
          value={formatPercent(current?.disk_percent ?? null)}
          pct={current?.disk_percent ?? null}
          foot={`${formatGb(server.disk_total_gb)} total`}
        />
        <MetricStat
          label="Containers"
          value={`${server.counts.containers_running}/${server.counts.containers_total}`}
          foot="running / total"
        />
      </div>

      <div className="card">
        <div className="card-title">
          <h2>Resource history</h2>
          <select
            className="input"
            aria-label="Metrics range"
            value={range}
            onChange={(e) => setRange(e.target.value as (typeof METRIC_RANGES)[number])}
          >
            {METRIC_RANGES.map((value) => (
              <option key={value} value={value}>
                Last {value}
              </option>
            ))}
          </select>
        </div>
        {historyQuery.isError ? <ErrorBlock error={historyQuery.error} /> : null}
        <LineChart series={chartSeries} fixedMax={100} unit="%" />
        <p className="small faint mt-8">
          {live.latest
            ? "Live stream connected — points after the last aggregate arrive in real time."
            : "Live stream idle — waiting for agent frames."}
        </p>
      </div>

      <div className="grid cols-2 mt-16">
        <div className="card">
          <div className="card-title">
            <h2>Facts</h2>
          </div>
          <dl className="kv">
            <dt>Hostname</dt>
            <dd className="mono">{server.hostname}</dd>
            <dt>IP address</dt>
            <dd className="mono">{server.ip_address || "—"}</dd>
            <dt>Operating system</dt>
            <dd>
              {server.os_name || "—"}
              {server.os_version ? ` ${server.os_version}` : ""}
            </dd>
            <dt>Architecture</dt>
            <dd>{server.arch || "—"}</dd>
            <dt>Environment</dt>
            <dd>{server.environment}</dd>
            <dt>Location</dt>
            <dd>{server.location || "—"}</dd>
            <dt>Docker host</dt>
            <dd>{server.docker_host ? server.docker_host.name : "—"}</dd>
            <dt>Capacity</dt>
            <dd>
              {server.cpu_cores} vCPU · {formatBytesMb(server.memory_total_mb)} ·{" "}
              {formatGb(server.disk_total_gb)}
            </dd>
            <dt>Uptime</dt>
            <dd>{formatUptime(server.uptime_seconds)}</dd>
            {server.tags.length > 0 ? (
              <>
                <dt>Tags</dt>
                <dd>
                  {server.tags.map((tag) => (
                    <TagChip key={tag.id} name={tag.name} color={tag.color} />
                  ))}
                </dd>
              </>
            ) : null}
            <dt>Created</dt>
            <dd>{formatDateTime(server.created_at)}</dd>
          </dl>
        </div>

        <div className="card">
          <div className="card-title">
            <h2>Agent</h2>
          </div>
          <dl className="kv">
            <dt>Enrolled</dt>
            <dd>{server.enrolled ? "yes" : "no"}</dd>
            <dt>Agent version</dt>
            <dd className="mono">{server.agent_version || "—"}</dd>
            <dt>Last heartbeat</dt>
            <dd>
              {formatRelative(server.last_heartbeat_at)}
              {server.last_heartbeat_at ? (
                <span className="faint"> · {formatDateTime(server.last_heartbeat_at)}</span>
              ) : null}
            </dd>
            <dt>Heartbeat interval</dt>
            <dd>{server.heartbeat_interval_seconds}s</dd>
            <dt>Offline after</dt>
            <dd>{server.offline_after_seconds != null ? `${server.offline_after_seconds}s` : "platform default"}</dd>
          </dl>
          {canUpdate ? (
            <p className="small faint mt-8">
              "Issue agent token" generates a fresh enrollment token; the previous one stops
              working immediately.
            </p>
          ) : null}
        </div>
      </div>

      <div className="card mt-16">
        <div className="card-title">
          <h2>Containers</h2>
          <span className="small faint">
            {server.counts.containers_running} running / {server.counts.containers_total} total
          </span>
        </div>
        {containersQuery.isError ? <ErrorBlock error={containersQuery.error} /> : null}
        {containersQuery.isPending ? <LoadingBlock label="Loading containers…" /> : null}
        {containersQuery.data && containersQuery.data.items.length === 0 ? (
          <EmptyState
            icon="▢"
            title="No containers reported"
            hint="Containers appear once the agent submits its first inventory."
          />
        ) : null}
        {containersQuery.data && containersQuery.data.items.length > 0 ? (
          <>
            <div className="table-wrap">
              <table className="data">
                <thead>
                  <tr>
                    <th scope="col">Name</th>
                    <th scope="col">Image</th>
                    <th scope="col">Status</th>
                    <th scope="col">Health</th>
                    <th scope="col" className="num">
                      CPU
                    </th>
                    <th scope="col" className="num">
                      Memory
                    </th>
                    <th scope="col">Seen</th>
                  </tr>
                </thead>
                <tbody>
                  {containersQuery.data.items.map((container) => (
                    <tr key={container.id}>
                      <td>
                        <Link to={`/containers/${container.id}`}>{container.name}</Link>
                      </td>
                      <td className="mono small">{container.image_ref}</td>
                      <td>
                        <StatusBadge value={container.status} />
                      </td>
                      <td>
                        <StatusBadge value={container.health} />
                      </td>
                      <td className="num">{formatPercent(container.cpu_percent, 1)}</td>
                      <td className="num">
                        {formatBytesMb(container.mem_used_mb)}
                        {container.mem_limit_mb ? ` / ${formatBytesMb(container.mem_limit_mb)}` : ""}
                      </td>
                      <td>{formatRelative(container.observed_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination
              page={{
                items: containersQuery.data.items,
                total: containersQuery.data.total,
                limit: containersQuery.data.limit,
                offset: containersQuery.data.offset,
              }}
              onPage={setContainersOffset}
            />
          </>
        ) : null}
      </div>

      <div className="card mt-16">
        <div className="card-title">
          <h2>Recent events</h2>
          <Link className="small" to="/events">
            View all events
          </Link>
        </div>
        {server.recent_events.length === 0 ? (
          <EmptyState icon="◇" title="No recent events" />
        ) : (
          <ul className="timeline">
            {server.recent_events.map((event) => (
              <li key={event.id}>
                <div className="tl-time">
                  {formatRelative(event.created_at)} · {formatDateTime(event.created_at)}
                </div>
                <div>
                  <StatusBadge value={event.level} />{" "}
                  <span className="mono small faint">{event.type}</span>
                </div>
                <div>{event.message || event.type}</div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {editOpen ? <EditServerModal server={server} onClose={() => setEditOpen(false)} /> : null}

      <Modal open={deleteOpen} title="Delete server" onClose={() => setDeleteOpen(false)}>
        <p>
          Delete <strong>{server.name}</strong>? Its containers, metrics and events are removed as
          well. This cannot be undone.
        </p>
        {deleteMutation.isError ? (
          <div className="mt-8">
            <ErrorBlock error={deleteMutation.error} />
          </div>
        ) : null}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={() => setDeleteOpen(false)}>
            Cancel
          </button>
          <button
            type="button"
            className="btn danger"
            onClick={() => deleteMutation.mutate()}
            disabled={deleteMutation.isPending}
          >
            {deleteMutation.isPending ? "Deleting…" : "Delete server"}
          </button>
        </div>
      </Modal>

      <Modal
        open={issuedToken !== null}
        title="Agent enrollment token"
        onClose={() => setIssuedToken(null)}
      >
        {issuedToken ? (
          <>
            <p className="form-error" role="alert">
              This token is shown only once. Copy it now — it is stored only as a hash and can
              never be retrieved again. Issuing a new token invalidates this one.
            </p>
            <div className="field mt-8">
              <label htmlFor="agent-token-value">Token</label>
              <input
                id="agent-token-value"
                className="input mono"
                readOnly
                value={issuedToken.agent_token}
                onFocus={(e) => e.currentTarget.select()}
              />
            </div>
            <div className="modal-actions" style={{ justifyContent: "space-between" }}>
              <button type="button" className="btn" onClick={() => void copyToken()}>
                Copy token
              </button>
              <button type="button" className="btn primary" onClick={() => setIssuedToken(null)}>
                Done — I saved it
              </button>
            </div>
            <p className="small faint mono mt-8" style={{ whiteSpace: "pre-wrap" }}>
              {issuedToken.install_hint}
            </p>
          </>
        ) : null}
      </Modal>
    </section>
  );
}
