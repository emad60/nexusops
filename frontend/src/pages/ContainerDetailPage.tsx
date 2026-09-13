import { Fragment, useCallback, useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import { apiGet, apiPost, apiRequest, ApiError } from "../api/client";
import type { CursorPage } from "../api/types";
import { useEventStream } from "../hooks/useEventStream";
import type { WsFrame } from "../hooks/useEventStream";
import { useAuth } from "../auth/AuthContext";
import { useToast } from "../components/toast";
import { EmptyState, ErrorBlock, LoadingBlock, Modal, StatusBadge, TagChip } from "../components/ui";
import type { ContainerRow } from "./ContainerListPage";

/** Container as returned by GET /containers/{id} — adds command and mounts. */
export interface ContainerDetailData extends ContainerRow {
  command: string;
  mounts: Array<Record<string, unknown>>;
}

/** One persisted log row from GET /containers/{id}/logs. */
export interface LogEntryRow {
  id: number;
  ts: string;
  stream: string;
  level: string;
  message: string;
}

type LifecycleAction = "start" | "stop" | "restart" | "pause" | "unpause";

interface DisplayLine {
  key: string;
  ts: string;
  stream: string;
  level: string;
  message: string;
}

const LOG_HISTORY_LIMIT = 100;
const MAX_LIVE_LINES = 1000;
const REMOVABLE_STATUSES = ["EXITED", "CREATED", "DEAD", "REMOVED"];

function formatUtc(iso: string | null | undefined): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return `${date.toISOString().replace("T", " ").slice(0, 19)} UTC`;
}

function formatLogTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toISOString().slice(11, 19);
}

function formatPercent(value: number | null): string {
  return value === null || value === undefined ? "—" : `${value.toFixed(1)}%`;
}

function formatKbPerSecond(value: number | null): string {
  return value === null || value === undefined ? "—" : `${value.toFixed(1)} KB/s`;
}

function formatPort(port: Record<string, unknown>): string {
  const privatePort = typeof port.private === "number" ? port.private : undefined;
  const publicPort = typeof port.public === "number" ? port.public : undefined;
  const type = typeof port.type === "string" ? port.type : "tcp";
  if (privatePort === undefined && publicPort === undefined) return "?";
  if (privatePort !== undefined && publicPort !== undefined && privatePort !== publicPort) {
    return `${publicPort} → ${privatePort}/${type}`;
  }
  return `${privatePort ?? publicPort}/${type}`;
}

function unknownToString(value: unknown): string {
  return typeof value === "string" && value.length > 0 ? value : "—";
}

export default function ContainerDetailPage() {
  const { containerId } = useParams<{ containerId: string }>();
  const navigate = useNavigate();
  const notify = useToast();
  const { hasPermission } = useAuth();
  const queryClient = useQueryClient();

  const [liveLines, setLiveLines] = useState<DisplayLine[]>([]);
  const [historyCleared, setHistoryCleared] = useState(false);
  const [tailPaused, setTailPaused] = useState(false);
  const [removeOpen, setRemoveOpen] = useState(false);
  const [confirmName, setConfirmName] = useState("");
  // Logs load on demand: the history fetch and the live stream stay idle
  // until "Show logs" — a container you merely inspect should not pull a
  // page of rows and open a websocket as a side effect.
  const [logsEnabled, setLogsEnabled] = useState(false);
  const [tailSize, setTailSize] = useState(LOG_HISTORY_LIMIT);
  const liveCounter = useRef(0);
  const logScrollRef = useRef<HTMLDivElement | null>(null);

  const containerQuery = useQuery({
    queryKey: ["container", containerId],
    queryFn: ({ signal }) =>
      apiGet<ContainerDetailData>(`/containers/${containerId}`, undefined, signal),
    enabled: containerId !== undefined,
  });

  const logsQuery = useQuery({
    queryKey: ["container-logs", containerId, tailSize],
    queryFn: ({ signal }) =>
      apiGet<CursorPage<LogEntryRow>>(
        `/containers/${containerId}/logs`,
        { limit: tailSize },
        signal,
      ),
    enabled: containerId !== undefined && logsEnabled,
  });

  const appendLiveLine = useCallback((frame: WsFrame) => {
    const data = frame.data ?? {};
    const message = typeof data.message === "string" ? data.message : "";
    if (!message) return;
    const ts = typeof data.ts === "string" ? data.ts : new Date().toISOString();
    const stream = typeof data.stream === "string" ? data.stream : "stdout";
    liveCounter.current += 1;
    const line: DisplayLine = {
      key: `live-${liveCounter.current}`,
      ts,
      stream,
      level: "",
      message,
    };
    setLiveLines((previous) => {
      const next = previous.length >= MAX_LIVE_LINES
        ? [...previous.slice(-(MAX_LIVE_LINES - 1)), line]
        : [...previous, line];
      return next;
    });
  }, []);

  useEventStream(
    containerId && logsEnabled
      ? [{ channel: "container-logs", params: { container_id: containerId } }]
      : [],
    appendLiveLine,
  );

  // Navigating between containers must not keep the previous tail.
  useEffect(() => {
    setLiveLines([]);
    setHistoryCleared(false);
  }, [containerId]);

  const container = containerQuery.data;

  const historyLines: DisplayLine[] =
    logsQuery.data && !historyCleared
      ? [...logsQuery.data.items]
          .reverse()
          .map((entry) => ({
            key: `h-${entry.id}`,
            ts: entry.ts,
            stream: entry.stream,
            level: entry.level,
            message: entry.message,
          }))
      : [];
  const displayLines = [...historyLines, ...liveLines];

  // Auto-scroll to the newest line unless the reader paused the tail.
  useEffect(() => {
    if (tailPaused) return;
    const element = logScrollRef.current;
    if (element) element.scrollTop = element.scrollHeight;
  }, [tailPaused, displayLines.length]);

  const actionMutation = useMutation({
    mutationFn: (action: LifecycleAction) =>
      apiPost<ContainerRow>(`/containers/${containerId}/${action}`),
    onSuccess: (updated, action) => {
      queryClient.setQueryData<ContainerDetailData>(["container", containerId], (previous) =>
        previous ? { ...previous, ...updated } : previous,
      );
      void queryClient.invalidateQueries({ queryKey: ["container", containerId] });
      void queryClient.invalidateQueries({ queryKey: ["containers"] });
      notify(`Container ${action} accepted — state refreshes as the host reports back`, "success");
    },
    onError: (error) => {
      notify(
        error instanceof ApiError
          ? `${error.code}: ${error.message}`
          : "Container action failed",
        "error",
      );
    },
  });

  const removeMutation = useMutation({
    mutationFn: () =>
      apiRequest<{ id: string; removed: boolean }>(`/containers/${containerId}`, {
        method: "DELETE",
        query: { confirm: confirmName },
      }),
    onSuccess: () => {
      notify("Container removed", "success");
      void queryClient.invalidateQueries({ queryKey: ["containers"] });
      navigate("/containers");
    },
    onError: (error) => {
      notify(
        error instanceof ApiError
          ? `${error.code}: ${error.message}`
          : "Removing the container failed",
        "error",
      );
    },
  });

  if (containerQuery.isPending) {
    return <LoadingBlock label="Loading container…" />;
  }

  if (containerQuery.isError || !container) {
    return (
      <div>
        <div className="page-head">
          <div className="page-title">
            <h1>Container</h1>
          </div>
        </div>
        <div className="card">
          <ErrorBlock error={containerQuery.error} />
        </div>
        <p className="mt-16">
          <Link to="/containers">← Back to containers</Link>
        </p>
      </div>
    );
  }

  const canLifecycle = hasPermission("container.lifecycle");
  const canRemove = hasPermission("container.remove");
  const busy = actionMutation.isPending;
  const status = container.status;
  const startable = REMOVABLE_STATUSES.includes(status);
  const lifecycleButtons: Array<{ action: LifecycleAction; label: string; when: boolean }> = [
    { action: "start", label: "Start", when: startable },
    { action: "stop", label: "Stop", when: status === "RUNNING" || status === "PAUSED" },
    { action: "restart", label: "Restart", when: status === "RUNNING" || status === "PAUSED" },
    { action: "pause", label: "Pause", when: status === "RUNNING" },
    { action: "unpause", label: "Unpause", when: status === "PAUSED" },
  ];

  const memoryLimit = container.mem_limit_mb;
  const memoryUsed = container.mem_used_mb;
  const memoryPct =
    memoryUsed !== null && memoryLimit !== null && memoryLimit > 0
      ? Math.min(100, Math.max(0, (memoryUsed / memoryLimit) * 100))
      : null;
  const memoryClass = memoryPct === null ? "ok" : memoryPct >= 90 ? "err" : memoryPct >= 70 ? "warn" : "ok";

  const labelEntries = Object.entries(container.labels);

  return (
    <div>
      <p className="small">
        <Link to="/containers">← Containers</Link>
      </p>
      <div className="page-head">
        <div className="page-title">
          <h1>
            <span className="mono">{container.name}</span>
            <StatusBadge value={container.status} />
            {container.health !== "NONE" ? <StatusBadge value={container.health} /> : null}
            {container.simulated ? <TagChip name="simulated" /> : null}
          </h1>
          <p className="page-sub mono">{container.image_ref}</p>
        </div>
        <div className="page-actions">
          {canLifecycle
            ? lifecycleButtons
                .filter((button) => button.when)
                .map((button) => (
                  <button
                    key={button.action}
                    type="button"
                    className="btn"
                    disabled={busy}
                    onClick={() => actionMutation.mutate(button.action)}
                  >
                    {button.label}
                  </button>
                ))
            : null}
          {canRemove ? (
            <button
              type="button"
              className="btn danger"
              onClick={() => {
                setConfirmName("");
                setRemoveOpen(true);
              }}
            >
              Remove
            </button>
          ) : null}
        </div>
      </div>

      <div className="grid cols-4">
        <div className="card stat-card">
          <div className="stat-label">CPU</div>
          <div className="stat-value">{formatPercent(container.cpu_percent)}</div>
          <div className="stat-foot">host share</div>
        </div>
        <div className="card stat-card">
          <div className="stat-label">Memory</div>
          <div className="stat-value">
            {memoryUsed === null ? "—" : `${Math.round(memoryUsed)} MB`}
          </div>
          <div className="stat-foot">
            {memoryLimit === null ? "no limit" : `limit ${Math.round(memoryLimit)} MB`}
          </div>
          {memoryPct !== null ? (
            <div className="progress-track mt-8" role="presentation">
              <div className={`progress-fill ${memoryClass}`} style={{ width: `${memoryPct}%` }} />
            </div>
          ) : null}
        </div>
        <div className="card stat-card">
          <div className="stat-label">Network in</div>
          <div className="stat-value">{formatKbPerSecond(container.net_rx_kb_s)}</div>
          <div className="stat-foot">RX</div>
        </div>
        <div className="card stat-card">
          <div className="stat-label">Network out</div>
          <div className="stat-value">{formatKbPerSecond(container.net_tx_kb_s)}</div>
          <div className="stat-foot">TX</div>
        </div>
      </div>

      <div className="grid cols-2 mt-16">
        <div className="card">
          <div className="card-title">
            <h2>Container facts</h2>
          </div>
          <dl className="kv">
            <dt>Container ID</dt>
            <dd className="mono">{container.container_id}</dd>
            <dt>Command</dt>
            <dd className="mono">{container.command || "—"}</dd>
            <dt>Status</dt>
            <dd>
              <StatusBadge value={container.status} />
            </dd>
            <dt>Health</dt>
            <dd>
              {container.health === "NONE" ? (
                <span className="faint">—</span>
              ) : (
                <StatusBadge value={container.health} />
              )}
            </dd>
            <dt>Restarts</dt>
            <dd>{container.restart_count}</dd>
            <dt>Started</dt>
            <dd>{formatUtc(container.started_at)}</dd>
            <dt>Finished</dt>
            <dd>{formatUtc(container.finished_at)}</dd>
            <dt>Observed</dt>
            <dd>{formatUtc(container.observed_at)}</dd>
            <dt>Docker host</dt>
            <dd>
              {container.host ? (
                <span className="flex gap-8">
                  {container.host.name} <StatusBadge value={container.host.status} />
                </span>
              ) : (
                "—"
              )}
            </dd>
            <dt>Server</dt>
            <dd>
              {container.server ? (
                <Link to={`/servers/${container.server.id}`}>{container.server.name}</Link>
              ) : (
                "—"
              )}
            </dd>
          </dl>
        </div>

        <div className="card">
          <div className="card-title">
            <h2>Configuration</h2>
          </div>
          <h3 className="small muted mb-8">Ports</h3>
          {container.ports.length > 0 ? (
            <p className="mono small">{container.ports.map(formatPort).join("  ·  ")}</p>
          ) : (
            <p className="faint small">No published ports.</p>
          )}
          <h3 className="small muted mb-8 mt-16">Environment keys</h3>
          {container.env_keys.length > 0 ? (
            <p>
              {container.env_keys.map((key) => (
                <span key={key} className="tag-chip mono">
                  {key}
                </span>
              ))}
            </p>
          ) : (
            <p className="faint small">No environment keys (values never leave the database).</p>
          )}
          <h3 className="small muted mb-8 mt-16">Labels</h3>
          {labelEntries.length > 0 ? (
            <dl className="kv">
              {labelEntries.map(([key, value]) => (
                <Fragment key={key}>
                  <dt className="mono">{key}</dt>
                  <dd>{value}</dd>
                </Fragment>
              ))}
            </dl>
          ) : (
            <p className="faint small">No labels.</p>
          )}
        </div>
      </div>

      {container.mounts.length > 0 ? (
        <div className="card mt-16">
          <div className="card-title">
            <h2>Mounts</h2>
          </div>
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Source</th>
                  <th>Destination</th>
                </tr>
              </thead>
              <tbody>
                {container.mounts.map((mount, index) => (
                  <tr key={index}>
                    <td>{unknownToString(mount.Type ?? mount.type)}</td>
                    <td className="mono small">{unknownToString(mount.Source ?? mount.source)}</td>
                    <td className="mono small">
                      {unknownToString(mount.Destination ?? mount.destination)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      <div className="card mt-16">
        <div className="card-title">
          <h2>Logs</h2>
          <div className="flex gap-8">
            {logsEnabled ? (
              <>
                <select
                  className="input"
                  aria-label="Number of log lines to show"
                  value={tailSize}
                  onChange={(event) => {
                    setTailSize(Number(event.target.value));
                    // A new tail size means fresh history.
                    setHistoryCleared(false);
                  }}
                >
                  <option value={20}>last 20</option>
                  <option value={50}>last 50</option>
                  <option value={100}>last 100</option>
                </select>
                <span className="small muted" aria-live="polite">
                  {tailPaused ? "paused — scrolling locked" : "following"}
                </span>
                <button
                  type="button"
                  className="btn ghost sm"
                  onClick={() => {
                    setLiveLines([]);
                    setHistoryCleared(true);
                  }}
                >
                  Clear
                </button>
              </>
            ) : (
              <button
                type="button"
                className="btn primary sm"
                onClick={() => setLogsEnabled(true)}
              >
                Show logs
              </button>
            )}
          </div>
        </div>
        {logsQuery.isError ? (
          <ErrorBlock error={logsQuery.error} />
        ) : !logsEnabled ? (
          <EmptyState
            icon="≡"
            title="Logs are not loaded"
            hint="Load recent output and follow live lines on demand."
          />
        ) : displayLines.length === 0 ? (
          logsQuery.isPending ? (
            <LoadingBlock label="Loading logs…" />
          ) : (
            <EmptyState
              icon="≡"
              title="No log lines yet"
              hint="Live output appears here as the container emits it."
            />
          )
        ) : (
          <div
            ref={logScrollRef}
            className="log-viewer"
            tabIndex={0}
            role="log"
            aria-label={`Logs for ${container.name}`}
            onMouseEnter={() => setTailPaused(true)}
            onMouseLeave={() => setTailPaused(false)}
            onFocus={() => setTailPaused(true)}
            onBlur={() => setTailPaused(false)}
          >
            {displayLines.map((line) => (
              <div
                key={line.key}
                className={`log-line${line.level ? ` level-${line.level}` : ""}`}
              >
                <span className="ts">{formatLogTime(line.ts)}</span>
                <span className={`stream ${line.stream}`}>{line.stream}</span>
                <span className="msg">{line.message}</span>
              </div>
            ))}
          </div>
        )}
        {tailPaused && displayLines.length > 0 ? (
          <p className="small faint mt-8">
            Auto-scroll paused while you read or hover.{" "}
            <button type="button" className="btn sm" onClick={() => setTailPaused(false)}>
              Jump to latest
            </button>
          </p>
        ) : null}
      </div>

      <Modal open={removeOpen} title="Remove container" onClose={() => setRemoveOpen(false)}>
        <p className="small muted">
          This removes <span className="mono">{container.name}</span> from its docker host and
          deletes the container record and its logs from NexusOps. This cannot be undone. Type the
          container name to confirm.
        </p>
        <div className="field mt-16">
          <label htmlFor="remove-confirm-input">Container name</label>
          <input
            id="remove-confirm-input"
            className="input"
            value={confirmName}
            onChange={(event) => setConfirmName(event.target.value)}
            placeholder={container.name}
            autoComplete="off"
          />
        </div>
        {removeMutation.isError ? <ErrorBlock error={removeMutation.error} /> : null}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={() => setRemoveOpen(false)}>
            Cancel
          </button>
          <button
            type="button"
            className="btn danger"
            disabled={confirmName !== container.name || removeMutation.isPending}
            onClick={() => removeMutation.mutate()}
          >
            Remove container
          </button>
        </div>
      </Modal>
    </div>
  );
}
