import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { ApiError, apiDelete, apiGet, apiPatch, apiPost } from "../api/client";
import type {
  ContainerOut,
  EnrollmentTokenCreated,
  EnrollmentTokenItem,
  MetricPoint,
  OperationItem,
  OperationType,
  Page,
  ServerDetail,
} from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { EmptyState, ErrorBlock, LoadingBlock, Modal, StatusBadge, TagChip } from "../components/ui";
import { Pagination } from "../components/Pagination";
import { LineChart, type ChartSeries } from "../components/LineChart";
import { InfoHint } from "../components/InfoHint";
import {
  buildServerPayload,
  ServerFormFields,
  validateServerForm,
  type ServerFormErrors,
  type ServerFormValues,
  type ServerPayload,
} from "../components/ServerForm";
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

/** Response of POST /nodes/{id}/agent-token — the raw token is shown exactly once. */
interface EnrollTokenOut {
  agent_token: string;
  install_hint: string;
}

/** Response of GET /nodes/{id}/metrics/latest. */
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

/** Response of GET /nodes/{id}/metrics (bucketed timeseries). */
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
  const [errors, setErrors] = useState<ServerFormErrors>({});

  const updateMutation = useMutation({
    mutationFn: (payload: ServerPayload) =>
      apiPatch<ServerDetail>(`/nodes/${server.id}`, payload),
    onSuccess: (updated) => {
      notify(`Node ${updated.name} updated`, "success");
      void queryClient.invalidateQueries({ queryKey: ["server", server.id] });
      void queryClient.invalidateQueries({ queryKey: ["servers"] });
      onClose();
    },
    onError: (error) => notify(errorMessage(error), "error"),
  });

  const submit = () => {
    const nextErrors = validateServerForm(values);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;
    updateMutation.mutate(buildServerPayload(values));
  };

  return (
    <Modal open title={`Edit ${server.name}`} onClose={onClose} wide>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <ServerFormFields
          values={values}
          onChange={setValues}
          errors={errors}
          idPrefix="server-edit"
        />
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
  const [issuedEnrollment, setIssuedEnrollment] = useState<EnrollmentTokenCreated | null>(null);
  const [removeTarget, setRemoveTarget] = useState<ContainerOut | null>(null);
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
    queryFn: ({ signal }) => apiGet<ServerDetail>(`/nodes/${serverId}`, undefined, signal),
    enabled: Boolean(serverId),
    // Heartbeats arrive out-of-band (agent → backend), so liveness changes are
    // not tied to any page action: poll gently so the status badge stays true.
    refetchInterval: 10_000,
  });

  const historyQuery = useQuery({
    queryKey: ["server-metrics", serverId, range],
    queryFn: ({ signal }) =>
      apiGet<ServerTimeseries>(
        `/nodes/${serverId}/metrics`,
        { range, metrics: "cpu_percent,mem_percent,disk_percent" },
        signal,
      ),
    enabled: Boolean(serverId),
  });

  const latestQuery = useQuery({
    queryKey: ["server-metrics-latest", serverId],
    queryFn: async () => {
      try {
        return await apiGet<MetricSnapshot>(`/nodes/${serverId}/metrics/latest`);
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

  const operationsQuery = useQuery({
    queryKey: ["operations", { node_id: serverId }],
    queryFn: ({ signal }) =>
      apiGet<Page<OperationItem>>("/operations", { node_id: serverId, limit: 10 }, signal),
    enabled: Boolean(serverId),
    // Operations move out-of-band (agent claim/result), so poll so a QUEUED row
    // does not look final.
    refetchInterval: 5_000,
  });

  const canManageTokens = hasPermission("node.create");
  const enrollmentTokensQuery = useQuery({
    queryKey: ["enrollment-tokens"],
    queryFn: ({ signal }) =>
      apiGet<Page<EnrollmentTokenItem>>("/nodes/enrollment-tokens", { limit: 20 }, signal),
    enabled: canManageTokens,
  });

  const dispatchMutation = useMutation({
    mutationFn: ({ type, containerId }: { type: OperationType; containerId: string }) => {
      if (!serverId) return Promise.reject(new Error("Missing server id"));
      return apiPost<OperationItem>("/operations", {
        node_id: serverId,
        type,
        params: { container_id: containerId, force: type === "container.remove" },
      });
    },
    onSuccess: () => {
      // "Queued" is deliberately not "done": the row only becomes SUCCEEDED
      // once the agent claims, executes and reports back.
      notify("Operation queued — it runs when the agent next checks in", "success");
      void queryClient.invalidateQueries({ queryKey: ["operations", { node_id: serverId }] });
    },
    onError: (error) => notify(errorMessage(error), "error"),
  });

  const createEnrollmentMutation = useMutation({
    mutationFn: () =>
      apiPost<EnrollmentTokenCreated>("/nodes/enrollment-tokens", { expires_in_seconds: 3600 }),
    onSuccess: (data) => {
      setIssuedEnrollment(data);
      void queryClient.invalidateQueries({ queryKey: ["enrollment-tokens"] });
    },
    onError: (error) => notify(errorMessage(error), "error"),
  });

  const revokeEnrollmentMutation = useMutation({
    mutationFn: (tokenId: string) =>
      apiPost<EnrollmentTokenItem>(`/nodes/enrollment-tokens/${tokenId}/revoke`),
    onSuccess: () => {
      notify("Enrollment token revoked", "success");
      void queryClient.invalidateQueries({ queryKey: ["enrollment-tokens"] });
    },
    onError: (error) => notify(errorMessage(error), "error"),
  });

  const revokeCredentialMutation = useMutation({
    mutationFn: () => {
      if (!serverId) return Promise.reject(new Error("Missing server id"));
      return apiPost<ServerDetail>(`/nodes/${serverId}/agent-token/revoke`);
    },
    onSuccess: () => {
      notify("Node credential revoked — the agent will stop reporting", "success");
      void queryClient.invalidateQueries({ queryKey: ["server", serverId] });
    },
    onError: (error) => notify(errorMessage(error), "error"),
  });

  const tokenMutation = useMutation({
    mutationFn: () => {
      if (!serverId) return Promise.reject(new Error("Missing server id"));
      return apiPost<EnrollTokenOut>(`/nodes/${serverId}/agent-token`);
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
      return apiDelete<void>(`/nodes/${serverId}`);
    },
    onSuccess: () => {
      notify(`Node ${serverQuery.data?.name ?? ""} deleted`, "success");
      void queryClient.invalidateQueries({ queryKey: ["servers"] });
      navigate("/nodes");
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
        title="Node not found"
        hint="The address does not include a node id."
      />
    );
  }

  if (serverQuery.isPending) {
    return <LoadingBlock label="Loading node…" />;
  }

  if (serverQuery.isError || !serverQuery.data) {
    return <ErrorBlock error={serverQuery.error} />;
  }

  const server = serverQuery.data;
  const canUpdate = hasPermission("node.update");
  const canDelete = hasPermission("node.delete");
  const canLifecycle = hasPermission("container.lifecycle");
  const canRemove = hasPermission("container.remove");
  // Capability-aware: a docker operation is only offered when the node actually
  // reported docker as present. Unreported is *not* present.
  const dockerPresent = Boolean(server.capabilities?.docker?.present);

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
    <section aria-labelledby="node-heading">
      <div className="page-head">
        <div className="page-title">
          <h1 id="node-heading">
            {server.name} <StatusBadge value={server.status} />
            {server.simulated ? (
              <span className="badge WARNING no-dot">
                SIMULATED
                <InfoHint label="About simulated nodes">
                  This node generates demo data — no real host is contacted and none of its
                  metrics, containers or deployments are real.
                </InfoHint>
              </span>
            ) : null}
          </h1>
          <p className="page-sub">
            {server.hostname} · {server.environment}
            {server.description ? ` — ${server.description}` : ""}
          </p>
          {server.agent_revoked ? (
            <p className="form-error" role="status">
              This node's credential is <strong>revoked</strong> — it is no longer accepted and
              the agent has stopped reporting. To restore it, re-enroll the machine with a fresh
              enrollment token: create one below, then run the installer again on the host. The
              agent will pick up a new credential automatically.
            </p>
          ) : null}
          {server.enrolled && !server.capabilities_reported ? (
            <p className="small faint">
              This node has not reported capabilities (legacy agent or pre-v2 hello). Operations
              cannot be dispatched to it until its agent is upgraded and re-hellos.
            </p>
          ) : null}
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
              {tokenMutation.isPending ? "Rotating…" : "Rotate credential"}
            </button>
          ) : null}
          {canUpdate && server.enrolled ? (
            <button
              type="button"
              className="btn danger sm"
              onClick={() => revokeCredentialMutation.mutate()}
              disabled={revokeCredentialMutation.isPending}
            >
              {revokeCredentialMutation.isPending ? "Revoking…" : "Revoke credential"}
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
            <dt>Protocol</dt>
            <dd>
              {server.enrolled
                ? server.protocol_version
                  ? `v${server.protocol_version}`
                  : "v1 (legacy agent)"
                : "not enrolled"}
            </dd>
            <dt>Credential</dt>
            <dd>
              {server.agent_revoked
                ? "revoked"
                : server.enrolled
                  ? "active"
                  : "not issued"}
            </dd>
            <dt>Capabilities</dt>
            <dd>
              {!server.capabilities_reported ? (
                <span className="faint">not reported</span>
              ) : (
                Object.entries(server.capabilities ?? {}).map(([name, report]) => (
                  <span
                    key={name}
                    className={`badge ${report?.present ? "INFO" : "WARNING"} no-dot`}
                    title={report?.api_version ? `API ${report.api_version}` : undefined}
                  >
                    {name}: {report?.present ? "available" : "unavailable"}
                  </span>
                ))
              )}
            </dd>
          </dl>
          {canUpdate ? (
            <p className="small faint mt-8">
              &ldquo;Rotate credential&rdquo; issues a new node credential with a short grace
              window so a running agent can pick it up on its next heartbeat. Use &ldquo;Revoke
              credential&rdquo; (below) for the immediate kill switch when a token is known to be
              compromised.
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
                    <th scope="col">Actions</th>
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
                      <td className="container-actions">
                        {canLifecycle ? (
                          <>
                            <button
                              type="button"
                              className="btn ghost sm"
                              disabled={
                                !dockerPresent ||
                                dispatchMutation.isPending ||
                                container.status === "RUNNING"
                              }
                              onClick={() =>
                                dispatchMutation.mutate({
                                  type: "container.start",
                                  containerId: container.container_id,
                                })
                              }
                            >
                              Start
                            </button>
                            <button
                              type="button"
                              className="btn ghost sm"
                              disabled={
                                !dockerPresent ||
                                dispatchMutation.isPending ||
                                container.status !== "RUNNING"
                              }
                              onClick={() =>
                                dispatchMutation.mutate({
                                  type: "container.stop",
                                  containerId: container.container_id,
                                })
                              }
                            >
                              Stop
                            </button>
                            <button
                              type="button"
                              className="btn ghost sm"
                              disabled={!dockerPresent || dispatchMutation.isPending}
                              onClick={() =>
                                dispatchMutation.mutate({
                                  type: "container.restart",
                                  containerId: container.container_id,
                                })
                              }
                            >
                              Restart
                            </button>
                          </>
                        ) : null}
                        {canRemove ? (
                          <button
                            type="button"
                            className="btn danger sm"
                            disabled={!dockerPresent || dispatchMutation.isPending}
                            onClick={() => setRemoveTarget(container)}
                          >
                            Remove
                          </button>
                        ) : null}
                      </td>
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
          <h2>Operations</h2>
          <span className="small faint">
            queued actions run when the agent next checks in
          </span>
        </div>
        {operationsQuery.isError ? <ErrorBlock error={operationsQuery.error} /> : null}
        {operationsQuery.data && operationsQuery.data.items.length === 0 ? (
          <EmptyState
            icon="↯"
            title="No operations yet"
            hint="Use the container actions above to queue a start, stop, restart or removal."
          />
        ) : null}
        {operationsQuery.data && operationsQuery.data.items.length > 0 ? (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th scope="col">Type</th>
                  <th scope="col">Status</th>
                  <th scope="col">Requested</th>
                  <th scope="col">Deadline</th>
                  <th scope="col">Detail</th>
                </tr>
              </thead>
              <tbody>
                {operationsQuery.data.items.map((operation) => (
                  <tr key={operation.id}>
                    <td className="mono small">{operation.type}</td>
                    <td>
                      <StatusBadge value={operation.status} />
                      {operation.status === "PENDING" ? (
                        <span className="small faint"> queued</span>
                      ) : null}
                    </td>
                    <td>{formatRelative(operation.created_at)}</td>
                    <td>{formatRelative(operation.expires_at)}</td>
                    <td className="small">
                      {operation.error_code ? (
                        <span className="mono">
                          {operation.error_code}
                          {operation.error_message ? ` — ${operation.error_message}` : ""}
                        </span>
                      ) : operation.result ? (
                        <span className="mono faint">{JSON.stringify(operation.result)}</span>
                      ) : (
                        "—"
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>

      {canManageTokens ? (
        <div className="card mt-16">
          <div className="card-title">
            <h2>Enrollment tokens</h2>
            <button
              type="button"
              className="btn sm"
              onClick={() => createEnrollmentMutation.mutate()}
              disabled={createEnrollmentMutation.isPending}
            >
              {createEnrollmentMutation.isPending ? "Creating…" : "Create enrollment token"}
            </button>
          </div>
          <p className="small faint">
            An enrollment token enrolls one machine into this organization. It is single-use,
            expires, can be revoked, and its value is shown only once.
          </p>
          {enrollmentTokensQuery.isError ? <ErrorBlock error={enrollmentTokensQuery.error} /> : null}
          {enrollmentTokensQuery.data && enrollmentTokensQuery.data.items.length === 0 ? (
            <EmptyState
              icon="✚"
              title="No enrollment tokens"
              hint="Create one, then run the installer on the machine with the token."
            />
          ) : null}
          {enrollmentTokensQuery.data && enrollmentTokensQuery.data.items.length > 0 ? (
            <div className="table-wrap">
              <table className="data">
                <thead>
                  <tr>
                    <th scope="col">Name</th>
                    <th scope="col">State</th>
                    <th scope="col">Expires</th>
                    <th scope="col">Created</th>
                    <th scope="col" />
                  </tr>
                </thead>
                <tbody>
                  {enrollmentTokensQuery.data.items.map((token) => (
                    <tr key={token.id}>
                      <td>{token.name || "—"}</td>
                      <td>
                        <StatusBadge value={token.state} />
                      </td>
                      <td>{formatRelative(token.expires_at)}</td>
                      <td>{formatRelative(token.created_at)}</td>
                      <td>
                        {token.state === "ACTIVE" ? (
                          <button
                            type="button"
                            className="btn danger sm"
                            onClick={() => revokeEnrollmentMutation.mutate(token.id)}
                            disabled={revokeEnrollmentMutation.isPending}
                          >
                            Revoke
                          </button>
                        ) : null}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </div>
      ) : null}

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

      <Modal open={deleteOpen} title="Delete node" onClose={() => setDeleteOpen(false)}>
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
            {deleteMutation.isPending ? "Deleting…" : "Delete node"}
          </button>
        </div>
      </Modal>

      <Modal
        open={removeTarget !== null}
        title="Remove container"
        onClose={() => setRemoveTarget(null)}
      >
        {removeTarget ? (
          <>
            <p>
              Remove <strong>{removeTarget.name}</strong>? This permanently deletes the container
              on the node. Removal is destructive and cannot be undone.
            </p>
            <div className="modal-actions">
              <button type="button" className="btn" onClick={() => setRemoveTarget(null)}>
                Cancel
              </button>
              <button
                type="button"
                className="btn danger"
                onClick={() => {
                  dispatchMutation.mutate({
                    type: "container.remove",
                    containerId: removeTarget.container_id,
                  });
                  setRemoveTarget(null);
                }}
              >
                Remove container
              </button>
            </div>
          </>
        ) : null}
      </Modal>

      <Modal
        open={issuedEnrollment !== null}
        title="Enrollment token"
        onClose={() => setIssuedEnrollment(null)}
      >
        {issuedEnrollment ? (
          <>
            <p className="form-error" role="alert">
              This token is shown only once. It is single-use, expires {
                formatRelative(issuedEnrollment.expires_at)
              }, and is stored only as a hash — it can never be retrieved again.
            </p>
            <div className="field mt-8">
              <label htmlFor="enrollment-token-value">Token</label>
              <input
                id="enrollment-token-value"
                className="input mono"
                readOnly
                value={issuedEnrollment.token}
                onFocus={(e) => e.currentTarget.select()}
              />
            </div>
            <div className="modal-actions" style={{ justifyContent: "space-between" }}>
              <button
                type="button"
                className="btn"
                onClick={() => {
                  void navigator.clipboard
                    .writeText(issuedEnrollment.token)
                    .then(() => notify("Token copied to clipboard", "success"))
                    .catch(() =>
                      notify("Clipboard unavailable — select the token and copy it manually", "error"),
                    );
                }}
              >
                Copy token
              </button>
              <button
                type="button"
                className="btn primary"
                onClick={() => setIssuedEnrollment(null)}
              >
                Done — I saved it
              </button>
            </div>
            <p className="small faint mono mt-8" style={{ whiteSpace: "pre-wrap" }}>
              {issuedEnrollment.install_hint}
            </p>
          </>
        ) : null}
      </Modal>

      <Modal
        open={issuedToken !== null}
        title="Credential rotation"
        onClose={() => setIssuedToken(null)}
      >
        {issuedToken ? (
          <>
            <p className="form-error" role="alert">
              This new credential is shown only once. The node's current token keeps working for
              a short grace window (so the running agent can collect this one on its next
              heartbeat) and then stops. Copy the hint now — the raw value can never be
              retrieved again.
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
