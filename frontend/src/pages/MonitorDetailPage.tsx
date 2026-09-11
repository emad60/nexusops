import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { ApiError, apiDelete, apiGet, apiPatch, apiPost } from "../api/client";
import type { CheckOut, CursorPage, IncidentOut, MonitorOut, Page } from "../api/types";
import {
  EmptyState,
  ErrorBlock,
  LoadingBlock,
  Modal,
  StatusBadge,
} from "../components/ui";
import { useToast } from "../components/toast";
import { useAuth } from "../auth/AuthContext";
import { formatDateTime, formatRelative, truncate } from "../lib/format";

/** Uptime aggregate (GET /monitors/{id}/uptime) — not part of the shared types. */
interface UptimeSummary {
  uptime_pct: number;
  total_checks: number;
  failed_checks: number;
  avg_response_ms: number | null;
  p95_response_ms: number | null;
}

const METHODS = ["GET", "HEAD", "POST", "PUT", "OPTIONS"] as const;
const CHECK_PAGE_SIZE = 25;

/** Human-readable rendering of an API failure, SSRF rejections in particular. */
function describeError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.code === "SSRF_BLOCKED") {
      return `Target URL blocked by the SSRF guard: ${err.message} Pick a host that is reachable from the NexusOps server network.`;
    }
    return `${err.code}: ${err.message}`;
  }
  return "Request failed";
}

function resultBadgeClass(result: CheckOut["result"]): string {
  if (result === "SUCCESS") return "SUCCESS";
  if (result === "TIMEOUT") return "TIMEOUT";
  if (result === "ERROR") return "ERROR";
  return "FAILED";
}

function EditMonitorDialog({
  open,
  monitor,
  onClose,
}: {
  open: boolean;
  monitor: MonitorOut;
  onClose: () => void;
}) {
  const notify = useToast();
  const queryClient = useQueryClient();
  const [name, setName] = useState(monitor.name);
  const [url, setUrl] = useState(monitor.url);
  const [method, setMethod] = useState<string>(monitor.method);
  const [intervalSeconds, setIntervalSeconds] = useState(monitor.interval_seconds);
  const [timeoutSeconds, setTimeoutSeconds] = useState(monitor.timeout_seconds);
  const [expectedStatus, setExpectedStatus] = useState(monitor.expected_status);
  const [enabled, setEnabled] = useState(monitor.enabled);
  const [formError, setFormError] = useState("");

  const editMutation = useMutation({
    mutationFn: (body: Partial<MonitorOut>) =>
      apiPatch<MonitorOut>(`/monitors/${monitor.id}`, body),
    onSuccess: (updated) => {
      void queryClient.invalidateQueries({ queryKey: ["monitor", monitor.id] });
      void queryClient.invalidateQueries({ queryKey: ["monitors"] });
      notify(`Monitor "${updated.name}" updated`, "success");
      onClose();
    },
    onError: (err) => {
      setFormError(describeError(err));
      notify(describeError(err), "error");
    },
  });

  const submit = () => {
    if (!name.trim() || !url.trim()) {
      setFormError("Name and URL are required.");
      return;
    }
    setFormError("");
    editMutation.mutate({
      name: name.trim(),
      url: url.trim(),
      method,
      interval_seconds: intervalSeconds,
      timeout_seconds: timeoutSeconds,
      expected_status: expectedStatus,
      enabled,
    });
  };

  return (
    <Modal open={open} title={`Edit ${monitor.name}`} onClose={onClose} wide>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          submit();
        }}
      >
        <div className="field">
          <label htmlFor="edit-monitor-name">Name</label>
          <input
            id="edit-monitor-name"
            className="input"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="edit-monitor-url">Target URL</label>
          <input
            id="edit-monitor-url"
            className="input"
            value={url}
            onChange={(event) => setUrl(event.target.value)}
          />
          <span className="small faint">URL changes are re-validated by the SSRF guard.</span>
        </div>
        <div className="field-row">
          <div className="field">
            <label htmlFor="edit-monitor-method">Method</label>
            <select
              id="edit-monitor-method"
              className="input"
              value={method}
              onChange={(event) => setMethod(event.target.value)}
            >
              {METHODS.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="edit-monitor-interval">Interval (seconds)</label>
            <input
              id="edit-monitor-interval"
              className="input"
              type="number"
              min={10}
              max={86400}
              value={intervalSeconds}
              onChange={(event) => setIntervalSeconds(Number(event.target.value))}
            />
          </div>
        </div>
        <div className="field-row">
          <div className="field">
            <label htmlFor="edit-monitor-timeout">Timeout (seconds)</label>
            <input
              id="edit-monitor-timeout"
              className="input"
              type="number"
              min={0.5}
              max={60}
              step={0.5}
              value={timeoutSeconds}
              onChange={(event) => setTimeoutSeconds(Number(event.target.value))}
            />
          </div>
          <div className="field">
            <label htmlFor="edit-monitor-expected">Expected status</label>
            <input
              id="edit-monitor-expected"
              className="input"
              type="number"
              min={100}
              max={599}
              value={expectedStatus}
              onChange={(event) => setExpectedStatus(Number(event.target.value))}
            />
          </div>
        </div>
        <div className="field">
          <label htmlFor="edit-monitor-enabled" className="flex gap-8">
            <input
              id="edit-monitor-enabled"
              type="checkbox"
              checked={enabled}
              onChange={(event) => setEnabled(event.target.checked)}
            />
            <span>Enabled (resume scheduling)</span>
          </label>
        </div>
        {formError ? <div className="form-error">{formError}</div> : null}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn primary" disabled={editMutation.isPending}>
            {editMutation.isPending ? "Saving…" : "Save changes"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function DeleteMonitorDialog({
  open,
  monitor,
  onClose,
}: {
  open: boolean;
  monitor: MonitorOut;
  onClose: () => void;
}) {
  const notify = useToast();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: () => apiDelete<void>(`/monitors/${monitor.id}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["monitors"] });
      void queryClient.removeQueries({ queryKey: ["monitor", monitor.id] });
      notify(`Monitor "${monitor.name}" deleted`, "success");
      navigate("/monitors");
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  return (
    <Modal open={open} title="Delete monitor" onClose={onClose}>
      <p>
        Delete <strong>{monitor.name}</strong>? Its check history and open incident stay
        for the audit trail, but the monitor stops running immediately.
      </p>
      <div className="modal-actions">
        <button type="button" className="btn" onClick={onClose}>
          Cancel
        </button>
        <button
          type="button"
          className="btn danger"
          disabled={deleteMutation.isPending}
          onClick={() => deleteMutation.mutate()}
        >
          {deleteMutation.isPending ? "Deleting…" : "Delete monitor"}
        </button>
      </div>
    </Modal>
  );
}

export default function MonitorDetailPage() {
  const { monitorId } = useParams<{ monitorId: string }>();
  const { hasPermission } = useAuth();
  const canManage = hasPermission("monitor.manage");
  const notify = useToast();
  const queryClient = useQueryClient();
  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  const monitorQuery = useQuery({
    queryKey: ["monitor", monitorId],
    queryFn: ({ signal }) => apiGet<MonitorOut>(`/monitors/${monitorId}`, undefined, signal),
    enabled: monitorId != null,
    // Freshness fallback: the WS hub pushes transitions, but a socket can be
    // down (reconnect backoff, blocked upgrade). Status and the check timeline
    // must still converge — 10s polling matches the other live detail pages.
    refetchInterval: 10_000,
  });

  const checksQuery = useInfiniteQuery({
    queryKey: ["monitor-checks", monitorId],
    queryFn: ({ pageParam, signal }) =>
      apiGet<CursorPage<CheckOut>>(`/monitors/${monitorId}/checks`, {
        limit: CHECK_PAGE_SIZE,
        cursor: pageParam ?? undefined,
      }, signal),
    initialPageParam: null as string | null,
    getNextPageParam: (last) => (last.has_more ? last.next_cursor : null),
    enabled: monitorId != null,
    refetchInterval: 10_000,
  });

  const uptimeQuery = useQuery({
    queryKey: ["monitor-uptime", monitorId],
    queryFn: ({ signal }) =>
      apiGet<UptimeSummary>(`/monitors/${monitorId}/uptime`, { hours: 24 }, signal),
    enabled: monitorId != null,
  });

  const incidentsQuery = useQuery({
    queryKey: ["monitor-incidents", monitorId],
    queryFn: ({ signal }) =>
      apiGet<Page<IncidentOut>>(`/monitors/${monitorId}/incidents`, { limit: 5 }, signal),
    enabled: monitorId != null,
  });

  const checkNowMutation = useMutation({
    mutationFn: () => apiPost<CheckOut>(`/monitors/${monitorId}/check-now`),
    onSuccess: (check) => {
      void queryClient.invalidateQueries({ queryKey: ["monitor-checks", monitorId] });
      void queryClient.invalidateQueries({ queryKey: ["monitor", monitorId] });
      void queryClient.invalidateQueries({ queryKey: ["monitor-uptime", monitorId] });
      if (check.result === "SUCCESS") {
        notify(
          `Check passed in ${check.response_time_ms != null ? `${Math.round(check.response_time_ms)} ms` : "an unknown time"}`,
          "success",
        );
      } else {
        notify(`Check finished with result ${check.result}`, "error");
      }
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  const toggleMutation = useMutation({
    mutationFn: (monitor: MonitorOut) =>
      apiPost<MonitorOut>(`/monitors/${monitor.id}/${monitor.enabled ? "pause" : "resume"}`),
    onSuccess: (updated) => {
      void queryClient.invalidateQueries({ queryKey: ["monitor", monitorId] });
      void queryClient.invalidateQueries({ queryKey: ["monitors"] });
      notify(`Monitor "${updated.name}" ${updated.enabled ? "resumed" : "paused"}`, "success");
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  if (!monitorId) {
    return <ErrorBlock error={{ code: "NOT_FOUND", message: "No monitor id in route" }} />;
  }

  const monitor = monitorQuery.data;
  const checks = checksQuery.data?.pages.flatMap((page) => page.items) ?? [];
  const incidents = incidentsQuery.data?.items ?? [];
  const timelineChecks = checks.slice(0, 12);

  if (monitorQuery.isLoading) {
    return <LoadingBlock label="Loading monitor…" />;
  }
  if (monitorQuery.isError) {
    return <ErrorBlock error={monitorQuery.error} />;
  }
  if (!monitor) {
    return <EmptyState title="Monitor not found" />;
  }

  return (
    <main>
      <p className="small mb-8">
        <Link to="/monitors">← Uptime monitors</Link>
      </p>
      <div className="page-head">
        <div className="page-title">
          <h1>
            {monitor.name} <StatusBadge value={monitor.status} />
          </h1>
          <p className="page-sub mono">{monitor.url}</p>
        </div>
        {canManage ? (
          <div className="page-actions">
            <button
              type="button"
              className="btn"
              disabled={checkNowMutation.isPending}
              onClick={() => checkNowMutation.mutate()}
            >
              Check now
            </button>
            <button
              type="button"
              className="btn"
              disabled={toggleMutation.isPending}
              onClick={() => toggleMutation.mutate(monitor)}
            >
              {monitor.enabled ? "Pause" : "Enable"}
            </button>
            <button
              type="button"
              className="btn"
              onClick={() => setEditOpen(true)}
            >
              Edit
            </button>
            <button
              type="button"
              className="btn danger"
              onClick={() => setDeleteOpen(true)}
            >
              Delete
            </button>
          </div>
        ) : null}
      </div>

      <div className="grid cols-4 mb-16">
        <div className="card stat-card">
          <div className="stat-label">Uptime 24h</div>
          <div className={`stat-value ${uptimeQuery.data && uptimeQuery.data.uptime_pct < 99 ? "warn" : "ok"}`}>
            {uptimeQuery.data ? `${uptimeQuery.data.uptime_pct.toFixed(2)}%` : "—"}
          </div>
          <div className="stat-foot">
            {uptimeQuery.data
              ? `${uptimeQuery.data.total_checks} checks · ${uptimeQuery.data.failed_checks} failed`
              : "no data yet"}
          </div>
        </div>
        <div className="card stat-card">
          <div className="stat-label">Avg response</div>
          <div className="stat-value">
            {uptimeQuery.data?.avg_response_ms != null
              ? `${Math.round(uptimeQuery.data.avg_response_ms)} ms`
              : "—"}
          </div>
          <div className="stat-foot">
            p95{" "}
            {uptimeQuery.data?.p95_response_ms != null
              ? `${Math.round(uptimeQuery.data.p95_response_ms)} ms`
              : "—"}
          </div>
        </div>
        <div className="card stat-card">
          <div className="stat-label">Consecutive</div>
          <div className="stat-value">
            {monitor.consecutive_failures > 0 ? monitor.consecutive_failures : monitor.consecutive_successes}
          </div>
          <div className="stat-foot">
            {monitor.consecutive_failures > 0
              ? `failures (threshold ${monitor.failure_threshold})`
              : `successes (threshold ${monitor.success_threshold})`}
          </div>
        </div>
        <div className="card stat-card">
          <div className="stat-label">Next check</div>
          <div className="stat-value" style={{ fontSize: 18 }}>
            {monitor.enabled ? formatRelative(monitor.next_check_at) : "paused"}
          </div>
          <div className="stat-foot">
            {monitor.enabled
              ? `every ${monitor.interval_seconds}s · ${monitor.method}`
              : "scheduling disabled"}
          </div>
        </div>
      </div>

      <div className="grid cols-2">
        <div className="card">
          <div className="card-title">
            <h2>Configuration</h2>
            {monitor.current_open_incident_id ? (
              <Link
                className="badge OPEN no-dot"
                to={`/incidents/${monitor.current_open_incident_id}`}
              >
                open incident
              </Link>
            ) : null}
          </div>
          <dl className="kv">
            <dt>Target</dt>
            <dd className="mono">{monitor.url}</dd>
            <dt>Method</dt>
            <dd>{monitor.method}</dd>
            <dt>Expected status</dt>
            <dd>{monitor.expected_status}</dd>
            <dt>Interval</dt>
            <dd>{monitor.interval_seconds}s</dd>
            <dt>Timeout</dt>
            <dd>{monitor.timeout_seconds}s</dd>
            <dt>Thresholds</dt>
            <dd>
              fail ≥ {monitor.failure_threshold} · recover ≥ {monitor.success_threshold}
            </dd>
            <dt>Project</dt>
            <dd>{monitor.project_name ?? <span className="faint">none</span>}</dd>
            <dt>Last check</dt>
            <dd>{formatDateTime(monitor.last_check_at)}</dd>
            <dt>Last success</dt>
            <dd>{formatDateTime(monitor.last_success_at)}</dd>
            <dt>Last failure</dt>
            <dd>{formatDateTime(monitor.last_failure_at)}</dd>
          </dl>
        </div>

        <div className="card">
          <div className="card-title">
            <h2>Status timeline</h2>
            <span className="small faint">most recent first</span>
          </div>
          {timelineChecks.length === 0 ? (
            <EmptyState icon="◔" title="No checks recorded yet" />
          ) : (
            <ul className="timeline">
              {timelineChecks.map((check) => (
                <li key={check.id}>
                  <div className="flex gap-8 flex-between">
                    <span className={`badge ${resultBadgeClass(check.result)}`}>{check.result}</span>
                    <span className="tl-time" title={formatDateTime(check.checked_at)}>
                      {formatRelative(check.checked_at)}
                    </span>
                  </div>
                  <div className="small muted mt-8">
                    {check.response_time_ms != null ? `${Math.round(check.response_time_ms)} ms` : "no timing"}
                    {check.status_code != null ? ` · HTTP ${check.status_code}` : ""}
                    {check.error ? ` · ${truncate(check.error, 90)}` : ""}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-title">
          <h2>Recent check results</h2>
          <span className="small faint">{checks.length} loaded</span>
        </div>
        {checksQuery.isLoading ? (
          <LoadingBlock label="Loading check history…" />
        ) : checksQuery.isError ? (
          <ErrorBlock error={checksQuery.error} />
        ) : checks.length === 0 ? (
          <EmptyState
            icon="◔"
            title="No check history yet"
            hint={canManage ? "Use “Check now” to run the first check." : undefined}
          />
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th scope="col">Result</th>
                  <th scope="col" className="num">
                    Latency
                  </th>
                  <th scope="col" className="num">
                    Status code
                  </th>
                  <th scope="col">Timestamp</th>
                  <th scope="col">Error</th>
                </tr>
              </thead>
              <tbody>
                {checks.map((check) => (
                  <tr key={check.id}>
                    <td>
                      <span className={`badge ${resultBadgeClass(check.result)}`}>
                        {check.result}
                      </span>
                    </td>
                    <td className="num">
                      {check.response_time_ms != null
                        ? `${Math.round(check.response_time_ms)} ms`
                        : "—"}
                    </td>
                    <td className="num">{check.status_code ?? "—"}</td>
                    <td>{formatDateTime(check.checked_at)}</td>
                    <td className="small muted">{check.error || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {checksQuery.hasNextPage ? (
          <div className="mt-8">
            <button
              type="button"
              className="btn sm"
              disabled={checksQuery.isFetchingNextPage}
              onClick={() => void checksQuery.fetchNextPage()}
            >
              {checksQuery.isFetchingNextPage ? "Loading…" : "Load more checks"}
            </button>
          </div>
        ) : null}
      </div>

      <div className="card">
        <div className="card-title">
          <h2>Recent incidents</h2>
          <Link className="small" to="/incidents">
            All incidents →
          </Link>
        </div>
        {incidentsQuery.isLoading ? (
          <LoadingBlock label="Loading incidents…" />
        ) : incidentsQuery.isError ? (
          <ErrorBlock error={incidentsQuery.error} />
        ) : incidents.length === 0 ? (
          <EmptyState icon="✓" title="No incidents for this monitor" />
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th scope="col">Title</th>
                  <th scope="col">Severity</th>
                  <th scope="col">Status</th>
                  <th scope="col">Opened</th>
                </tr>
              </thead>
              <tbody>
                {incidents.map((incident) => (
                  <tr key={incident.id}>
                    <td>
                      <Link to={`/incidents/${incident.id}`}>{incident.title}</Link>
                    </td>
                    <td>
                      <StatusBadge value={incident.severity} />
                    </td>
                    <td>
                      <StatusBadge value={incident.status} />
                    </td>
                    <td>{formatDateTime(incident.opened_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <EditMonitorDialog
        open={editOpen}
        monitor={monitor}
        onClose={() => setEditOpen(false)}
      />
      <DeleteMonitorDialog
        open={deleteOpen}
        monitor={monitor}
        onClose={() => setDeleteOpen(false)}
      />
    </main>
  );
}
