/**
 * AuditLogPage — immutable audit trail (route: /audit-logs).
 *
 * Data: GET /audit-logs (offset-paginated Page<AuditOut>). The backend exposes
 * no write routes for this resource — the audit table is append-only (UPDATE
 * and DELETE are blocked by a DB trigger) — so this page intentionally renders
 * no mutation controls of any kind.
 */

import { useState, type FormEvent } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../api/client";
import type { AuditEntry, Page } from "../api/types";
import { EmptyState, ErrorBlock, StatusBadge } from "../components/ui";
import { TableSkeleton } from "../components/Skeleton";
import { Pagination } from "../components/Pagination";

const LIMIT = 25;
const RESULTS = ["SUCCESS", "DENIED", "ERROR"] as const;

/** The API also returns `user_agent` (AuditOut); not part of the shared type. */
type AuditRow = AuditEntry & { user_agent?: string };

function formatTimestamp(iso: string | null | undefined): string {
  if (!iso) return "—";
  const ts = new Date(iso);
  if (Number.isNaN(ts.getTime())) return iso;
  return ts.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function shortId(id: string): string {
  return id.length > 8 ? `${id.slice(0, 8)}…` : id;
}

export default function AuditLogPage() {
  const [offset, setOffset] = useState(0);
  // Text filters are drafts until submitted, so keystrokes do not refetch.
  const [actorDraft, setActorDraft] = useState("");
  const [actionDraft, setActionDraft] = useState("");
  const [actor, setActor] = useState("");
  const [action, setAction] = useState("");
  const [result, setResult] = useState<string>("ALL");
  const [since, setSince] = useState(""); // yyyy-mm-dd
  const [until, setUntil] = useState(""); // yyyy-mm-dd

  const query = useQuery({
    queryKey: ["audit-logs", offset, actor, action, result, since, until],
    queryFn: ({ signal }) => {
      // Date-only inputs become full-day UTC bounds at fetch time.
      const sinceAt = since ? `${since}T00:00:00` : undefined;
      const untilAt = until ? `${until}T23:59:59` : undefined;
      return apiGet<Page<AuditRow>>(
        "/audit-logs",
        {
          limit: LIMIT,
          offset,
          actor_email: actor || undefined,
          action: action || undefined,
          result: result === "ALL" ? undefined : result,
          since: sinceAt,
          until: untilAt,
        },
        signal,
      );
    },
  });

  function applyTextFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setActor(actorDraft.trim());
    setAction(actionDraft.trim());
    setOffset(0);
  }

  function clearFilters() {
    setActorDraft("");
    setActionDraft("");
    setActor("");
    setAction("");
    setResult("ALL");
    setSince("");
    setUntil("");
    setOffset(0);
  }

  const rows = query.data?.items ?? [];

  return (
    <div>
      <header className="page-head">
        <div className="page-title">
          <h1>Audit Log</h1>
          <p className="page-sub">Immutable record of privileged actions across NexusOps.</p>
        </div>
      </header>

      <div className="card mb-16" role="note" aria-label="Append-only notice">
        <p className="small muted">
          The audit trail is <strong>append-only</strong>. Every privileged action writes one
          immutable entry that can never be edited or deleted — by users or through the API. This
          page is intentionally read-only and provides no mutation controls.
        </p>
      </div>

      <form className="table-toolbar" role="search" onSubmit={applyTextFilters}>
        <div className="filters">
          <label className="small faint" htmlFor="audit-actor">
            Actor email
          </label>
          <input
            id="audit-actor"
            className="input"
            style={{ width: 200 }}
            placeholder="contains…"
            value={actorDraft}
            onChange={(event) => setActorDraft(event.target.value)}
          />
          <label className="small faint" htmlFor="audit-action">
            Action
          </label>
          <input
            id="audit-action"
            className="input"
            style={{ width: 160 }}
            placeholder="e.g. secret.rotate"
            value={actionDraft}
            onChange={(event) => setActionDraft(event.target.value)}
          />
          <label className="small faint" htmlFor="audit-result">
            Result
          </label>
          <select
            id="audit-result"
            className="input"
            value={result}
            onChange={(event) => {
              setResult(event.target.value);
              setOffset(0);
            }}
          >
            <option value="ALL">All results</option>
            {RESULTS.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
          <label className="small faint" htmlFor="audit-since">
            Since
          </label>
          <input
            id="audit-since"
            className="input"
            type="date"
            value={since}
            onChange={(event) => {
              setSince(event.target.value);
              setOffset(0);
            }}
          />
          <label className="small faint" htmlFor="audit-until">
            Until
          </label>
          <input
            id="audit-until"
            className="input"
            type="date"
            value={until}
            onChange={(event) => {
              setUntil(event.target.value);
              setOffset(0);
            }}
          />
          <button type="submit" className="btn sm">
            Apply
          </button>
          <button type="button" className="btn ghost sm" onClick={clearFilters}>
            Clear
          </button>
        </div>
      </form>

      {query.isPending ? (
        <TableSkeleton label="Loading audit entries" rows={10} cols={5} />
      ) : query.isError ? (
        <ErrorBlock error={query.error} />
      ) : rows.length === 0 ? (
        <EmptyState
          title="No audit entries match the current filters"
          hint="Audit entries are written automatically on every privileged action."
        />
      ) : (
        <div className="table-wrap sticky-first">
          <table className="data">
            <thead>
              <tr>
                <th>Time</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Resource</th>
                <th>Request ID</th>
                <th>IP</th>
                <th>Result</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id}>
                  <td className="num" title={row.created_at}>
                    {formatTimestamp(row.created_at)}
                  </td>
                  <td>{row.actor_email}</td>
                  <td className="mono">{row.action}</td>
                  <td
                    className="small muted mono"
                    title={row.resource_id ?? undefined}
                  >
                    {row.resource_type
                      ? `${row.resource_type} · ${shortId(row.resource_id ?? "")}`
                      : "—"}
                  </td>
                  <td className="mono small" title={row.id}>
                    {shortId(row.id)}
                  </td>
                  <td className="mono small" title={row.user_agent || undefined}>
                    {row.ip_address || "—"}
                  </td>
                  <td>
                    <StatusBadge value={row.result} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!query.isPending && !query.isError ? (
        <Pagination page={query.data as Page<unknown>} onPage={(next) => setOffset(next)} />
      ) : null}
    </div>
  );
}
