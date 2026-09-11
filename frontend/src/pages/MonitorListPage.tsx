import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiGet, apiPost } from "../api/client";
import type { CheckOut, MonitorOut, Page } from "../api/types";
import { Pagination } from "../components/Pagination";
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

const PAGE_SIZE = 25;

const STATUS_FILTERS = ["UP", "DOWN", "PENDING", "PAUSED"] as const;
const METHODS = ["GET", "HEAD", "POST", "PUT", "OPTIONS"] as const;

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

function CreateMonitorDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const notify = useToast();
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [method, setMethod] = useState<(typeof METHODS)[number]>("GET");
  const [intervalSeconds, setIntervalSeconds] = useState(60);
  const [formError, setFormError] = useState("");

  const createMutation = useMutation({
    mutationFn: (body: { name: string; url: string; method: string; interval_seconds: number }) =>
      apiPost<MonitorOut>("/monitors", body),
    onSuccess: (created) => {
      void queryClient.invalidateQueries({ queryKey: ["monitors"] });
      notify(`Monitor "${created.name}" created`, "success");
      setName("");
      setUrl("");
      setFormError("");
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
    createMutation.mutate({
      name: name.trim(),
      url: url.trim(),
      method,
      interval_seconds: intervalSeconds,
    });
  };

  return (
    <Modal open={open} title="New uptime monitor" onClose={onClose}>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          submit();
        }}
      >
        <div className="field">
          <label htmlFor="monitor-name">Name</label>
          <input
            id="monitor-name"
            className="input"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Marketing site"
            autoFocus
          />
        </div>
        <div className="field">
          <label htmlFor="monitor-url">Target URL</label>
          <input
            id="monitor-url"
            className="input"
            value={url}
            onChange={(event) => setUrl(event.target.value)}
            placeholder="https://example.com/health"
          />
          <span className="small faint">
            Validated by the server-side SSRF guard before storage.
          </span>
        </div>
        <div className="field-row">
          <div className="field">
            <label htmlFor="monitor-method">Method</label>
            <select
              id="monitor-method"
              className="input"
              value={method}
              onChange={(event) => setMethod(event.target.value as (typeof METHODS)[number])}
            >
              {METHODS.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="monitor-interval">Interval (seconds)</label>
            <input
              id="monitor-interval"
              className="input"
              type="number"
              min={10}
              max={86400}
              value={intervalSeconds}
              onChange={(event) => setIntervalSeconds(Number(event.target.value))}
            />
          </div>
        </div>
        {formError ? <div className="form-error">{formError}</div> : null}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn primary" disabled={createMutation.isPending}>
            {createMutation.isPending ? "Creating…" : "Create monitor"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export default function MonitorListPage() {
  const { hasPermission } = useAuth();
  const canManage = hasPermission("monitor.manage");
  const notify = useToast();
  const queryClient = useQueryClient();

  const [offset, setOffset] = useState(0);
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [createOpen, setCreateOpen] = useState(false);

  const monitorsQuery = useQuery({
    queryKey: ["monitors", { limit: PAGE_SIZE, offset, status: statusFilter, q: search }],
    queryFn: ({ signal }) =>
      apiGet<Page<MonitorOut>>("/monitors", {
        limit: PAGE_SIZE,
        offset,
        status: statusFilter || undefined,
        q: search || undefined,
      }, signal),
  });

  const toggleMutation = useMutation({
    mutationFn: (monitor: MonitorOut) =>
      apiPost<MonitorOut>(
        `/monitors/${monitor.id}/${monitor.enabled ? "pause" : "resume"}`,
      ),
    onSuccess: (updated) => {
      void queryClient.invalidateQueries({ queryKey: ["monitors"] });
      notify(`Monitor "${updated.name}" ${updated.enabled ? "resumed" : "paused"}`, "success");
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  const checkNowMutation = useMutation({
    mutationFn: (monitor: MonitorOut) => apiPost<CheckOut>(`/monitors/${monitor.id}/check-now`),
    onSuccess: (check) => {
      void queryClient.invalidateQueries({ queryKey: ["monitors"] });
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

  const monitors = monitorsQuery.data?.items ?? [];

  return (
    <main>
      <div className="page-head">
        <div className="page-title">
          <h1>Uptime monitors</h1>
          <p className="page-sub">
            HTTP availability checks with incident tracking and notification fan-out.
          </p>
        </div>
        <div className="page-actions">
          {canManage ? (
            <button
              type="button"
              className="btn primary"
              onClick={() => setCreateOpen(true)}
            >
              + New monitor
            </button>
          ) : null}
        </div>
      </div>

      <div className="table-toolbar">
        <div className="filters">
          <label className="flex gap-8" htmlFor="monitor-search">
            <span className="small muted">Search</span>
            <input
              id="monitor-search"
              className="input search-input"
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setOffset(0);
              }}
              placeholder="Filter by name or URL"
            />
          </label>
          <label className="flex gap-8" htmlFor="monitor-status-filter">
            <span className="small muted">Status</span>
            <select
              id="monitor-status-filter"
              className="input"
              value={statusFilter}
              onChange={(event) => {
                setStatusFilter(event.target.value);
                setOffset(0);
              }}
            >
              <option value="">All states</option>
              {STATUS_FILTERS.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      {monitorsQuery.isLoading ? (
        <LoadingBlock label="Loading monitors…" />
      ) : monitorsQuery.isError ? (
        <ErrorBlock error={monitorsQuery.error} />
      ) : monitors.length === 0 ? (
        <EmptyState
          icon="⏱"
          title={search || statusFilter ? "No monitors match the current filters" : "No monitors yet"}
          hint={
            canManage && !search && !statusFilter
              ? "Create your first uptime monitor to start tracking availability."
              : undefined
          }
        />
      ) : (
        <div className="card">
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th scope="col">Name</th>
                  <th scope="col">Target</th>
                  <th scope="col">Interval</th>
                  <th scope="col">Last check</th>
                  <th scope="col" className="num">
                    Uptime 24h
                  </th>
                  <th scope="col">State</th>
                  {canManage ? <th scope="col">Actions</th> : null}
                </tr>
              </thead>
              <tbody>
                {monitors.map((monitor) => (
                  <tr key={monitor.id}>
                    <td>
                      <Link to={`/monitors/${monitor.id}`}>{monitor.name}</Link>
                      {monitor.current_open_incident_id ? (
                        <span className="badge OPEN no-dot small mt-8">incident open</span>
                      ) : null}
                    </td>
                    <td className="mono" title={monitor.url}>
                      {truncate(monitor.url, 48)}
                    </td>
                    <td>{monitor.interval_seconds}s</td>
                    <td>
                      {monitor.last_check_at ? (
                        <span title={formatDateTime(monitor.last_check_at)}>
                          {formatRelative(monitor.last_check_at)}
                        </span>
                      ) : (
                        <span className="faint">never</span>
                      )}
                    </td>
                    <td className="num">
                      {monitor.uptime_pct_24h != null
                        ? `${monitor.uptime_pct_24h.toFixed(1)}%`
                        : "—"}
                    </td>
                    <td>
                      <StatusBadge value={monitor.status} />
                    </td>
                    {canManage ? (
                      <td>
                        <div className="flex gap-8">
                          <button
                            type="button"
                            className="btn sm"
                            disabled={toggleMutation.isPending}
                            onClick={() => toggleMutation.mutate(monitor)}
                          >
                            {monitor.enabled ? "Pause" : "Enable"}
                          </button>
                          <button
                            type="button"
                            className="btn sm ghost"
                            disabled={checkNowMutation.isPending}
                            onClick={() => checkNowMutation.mutate(monitor)}
                          >
                            Check now
                          </button>
                        </div>
                      </td>
                    ) : null}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {monitorsQuery.data ? (
            <Pagination page={monitorsQuery.data} onPage={setOffset} />
          ) : null}
        </div>
      )}

      <CreateMonitorDialog open={createOpen} onClose={() => setCreateOpen(false)} />
    </main>
  );
}
