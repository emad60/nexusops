import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet } from "../api/client";
import type { IncidentOut, Page } from "../api/types";
import { Pagination } from "../components/Pagination";
import { InfoHint } from "../components/InfoHint";
import { EmptyState, ErrorBlock, StatusBadge } from "../components/ui";
import { TableSkeleton } from "../components/Skeleton";
import { useEventStream } from "../hooks/useEventStream";
import { formatDateTime, formatRelative } from "../lib/format";

const PAGE_SIZE = 25;
const STATUS_FILTERS = ["OPEN", "ACKNOWLEDGED", "RESOLVED"] as const;
const SEVERITIES = ["CRITICAL", "MAJOR", "MINOR", "WARNING"] as const;

export default function IncidentListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [offset, setOffset] = useState(0);
  const [statusFilter, setStatusFilter] = useState("");
  const [severityFilter, setSeverityFilter] = useState("");

  // Live incident feed: any OPENED / ACKNOWLEDGED / RESOLVED / NOTE event on the
  // incidents channel refreshes the visible page without a manual reload.
  useEventStream([{ channel: "incidents" }], () => {
    void queryClient.invalidateQueries({ queryKey: ["incidents"] });
  });

  const incidentsQuery = useQuery({
    queryKey: ["incidents", { limit: PAGE_SIZE, offset, status: statusFilter, severity: severityFilter }],
    queryFn: ({ signal }) =>
      apiGet<Page<IncidentOut>>("/incidents", {
        limit: PAGE_SIZE,
        offset,
        status: statusFilter || undefined,
        severity: severityFilter || undefined,
      }, signal),
    // Belt and braces for the WS feed above: incidents open in the worker,
    // out of band, so poll gently in case a live frame is missed.
    refetchInterval: 10_000,
  });

  const incidents = incidentsQuery.data?.items ?? [];

  return (
    <main>
      <div className="page-head">
        <div className="page-title">
          <h1>Incidents</h1>
          <p className="page-sub">
            Uptime failures that crossed their threshold. Acknowledge to claim triage,
            resolve with a short post-mortem note.
          </p>
        </div>
      </div>

      <div className="table-toolbar">
        <div className="filters">
          <label className="flex gap-8" htmlFor="incident-status-filter">
            <span className="small muted">Status</span>
            <select
              id="incident-status-filter"
              className="input"
              value={statusFilter}
              onChange={(event) => {
                setStatusFilter(event.target.value);
                setOffset(0);
              }}
            >
              <option value="">All statuses</option>
              {STATUS_FILTERS.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </label>
          <label className="flex gap-8" htmlFor="incident-severity-filter">
            <span className="small muted">Severity</span>
            <select
              id="incident-severity-filter"
              className="input"
              value={severityFilter}
              onChange={(event) => {
                setSeverityFilter(event.target.value);
                setOffset(0);
              }}
            >
              <option value="">All severities</option>
              {SEVERITIES.map((severity) => (
                <option key={severity} value={severity}>
                  {severity}
                </option>
              ))}
            </select>
          </label>
        </div>
        <span className="small faint" aria-hidden>
          ● live
        </span>
      </div>

      {incidentsQuery.isLoading ? (
        <TableSkeleton label="Loading incidents" rows={8} cols={7} />
      ) : incidentsQuery.isError ? (
        <ErrorBlock error={incidentsQuery.error} />
      ) : incidents.length === 0 ? (
        <EmptyState
          icon="✓"
          title={
            statusFilter || severityFilter
              ? "No incidents match the current filters"
              : "No incidents — all monitors healthy"
          }
        />
      ) : (
        <div className="card">
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th scope="col">
                    Severity{" "}
                    <InfoHint label="About severity">
                      How bad the outage is: CRITICAL, MAJOR, MINOR or WARNING. Incidents opened
                      by monitor failures start at MAJOR after repeated failing checks.
                    </InfoHint>
                  </th>
                  <th scope="col">Title</th>
                  <th scope="col">Monitor</th>
                  <th scope="col">
                    Status{" "}
                    <InfoHint label="About status">
                      OPEN needs attention. ACKNOWLEDGED means someone has claimed it and
                      notifications are silenced. RESOLVED means recovery was detected or it was
                      closed manually.
                    </InfoHint>
                  </th>
                  <th scope="col" className="num">
                    Failures{" "}
                    <InfoHint label="About failures">
                      Consecutive failed checks recorded when the incident opened. The count is
                      kept for the audit trail even after the monitor recovers.
                    </InfoHint>
                  </th>
                  <th scope="col">Opened</th>
                  <th scope="col">Last update</th>
                </tr>
              </thead>
              <tbody>
                {incidents.map((incident) => (
                  <tr key={incident.id} className="clickable" onClick={() => navigate(`/incidents/${incident.id}`)}>
                    <td>
                      <StatusBadge value={incident.severity} />
                    </td>
                    <td>
                      <Link to={`/incidents/${incident.id}`}>{incident.title}</Link>
                    </td>
                    <td onClick={(event) => event.stopPropagation()}>
                      <Link to={`/monitors/${incident.monitor_id}`}>
                        {incident.monitor_name ?? incident.monitor_id.slice(0, 8)}
                      </Link>
                    </td>
                    <td>
                      <StatusBadge value={incident.status} />
                    </td>
                    <td className="num">{incident.failure_count}</td>
                    <td title={formatDateTime(incident.opened_at)}>
                      {formatRelative(incident.opened_at)}
                    </td>
                    <td title={formatDateTime(incident.resolved_at ?? incident.acknowledged_at)}>
                      {incident.status === "RESOLVED"
                        ? `resolved ${formatRelative(incident.resolved_at)}`
                        : incident.status === "ACKNOWLEDGED"
                          ? `ack ${formatRelative(incident.acknowledged_at)}`
                          : formatRelative(incident.opened_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {incidentsQuery.data ? (
            <Pagination page={incidentsQuery.data} onPage={setOffset} />
          ) : null}
        </div>
      )}
    </main>
  );
}
