/**
 * /settings/sessions — the current user's active sign-in sessions.
 *
 * GET /sessions defaults to the caller's own sessions; revoking one uses
 * DELETE /sessions/{id}. There is no bulk endpoint, so "revoke all others"
 * fans out per-session deletes client-side and reports a summary. Refresh
 * tokens rotate, so revoked sessions drop out of the list after the next
 * token refresh — hence the invalidate after every revoke.
 */
import { useState } from "react";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiDelete, apiGet } from "../api/client";
import type { Page, SessionInfo } from "../api/types";
import { Pagination } from "../components/Pagination";
import { EmptyState, ErrorBlock, LoadingBlock } from "../components/ui";
import { useToast } from "../components/toast";
import { formatDateTime, formatRelative, truncate } from "../lib/format";

const PAGE_SIZE = 100;

/** Human message for any thrown error (ApiError and network aware). */
export function describeError(err: unknown): string {
  if (err instanceof ApiError) {
    return err.status === 0 ? "Cannot reach the NexusOps server." : `${err.code}: ${err.message}`;
  }
  return err instanceof Error ? err.message : "Request failed";
}

export default function SessionsPage() {
  const notify = useToast();
  const queryClient = useQueryClient();
  const [offset, setOffset] = useState(0);

  const sessionsQuery = useQuery({
    queryKey: ["sessions", offset],
    queryFn: ({ signal }) =>
      apiGet<Page<SessionInfo>>("/sessions", { limit: PAGE_SIZE, offset }, signal),
    placeholderData: keepPreviousData,
  });
  const sessionsPage = sessionsQuery.data;
  const sessions = sessionsPage?.items ?? [];
  const others = sessions.filter((session) => !session.current);

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["sessions"] });

  const revokeOne = useMutation({
    mutationFn: (session: SessionInfo) => apiDelete<void>(`/sessions/${session.id}`),
    onSuccess: (_res, session) => {
      notify(`Revoked the session on ${session.device_label}`, "success");
      void refresh();
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  const revokeOthers = useMutation({
    mutationFn: async (targets: SessionInfo[]) =>
      Promise.allSettled(targets.map((session) => apiDelete<void>(`/sessions/${session.id}`))),
    onSuccess: (results) => {
      const ok = results.filter((r) => r.status === "fulfilled").length;
      const failed = results.length - ok;
      const plural = ok === 1 ? "" : "s";
      notify(
        failed === 0
          ? `Revoked ${ok} other session${plural}`
          : `Revoked ${ok} other session${plural}; ${failed} failed`,
        failed === 0 ? "success" : "error",
      );
      void refresh();
    },
  });

  return (
    <div>
      <div className="page-head">
        <div className="page-title">
          <h1>Sessions</h1>
          <p className="page-sub">Devices currently signed in as you.</p>
        </div>
        <div className="page-actions">
          {others.length > 0 && (
            <button
              type="button"
              className="btn danger"
              disabled={revokeOthers.isPending}
              onClick={() => revokeOthers.mutate(others)}
            >
              Revoke other sessions
            </button>
          )}
        </div>
      </div>

      <div className="card">
        {sessionsQuery.isPending ? (
          <LoadingBlock label="Loading sessions…" />
        ) : sessionsQuery.isError ? (
          <ErrorBlock error={sessionsQuery.error} />
        ) : !sessionsPage || sessions.length === 0 ? (
          <EmptyState title="No active sessions" hint="Sign in again to create one." />
        ) : (
          <>
            <div className="table-wrap">
              <table className="data">
                <thead>
                  <tr>
                    <th scope="col">Device</th>
                    <th scope="col">IP address</th>
                    <th scope="col">Created</th>
                    <th scope="col">Last seen</th>
                    <th scope="col">Expires</th>
                    <th scope="col">Status</th>
                    <th scope="col">
                      <span className="faint">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.map((session) => (
                    <tr key={session.id}>
                      <td>
                        <div>{session.device_label}</div>
                        <div className="small faint mono">{truncate(session.user_agent, 60)}</div>
                      </td>
                      <td className="mono">{session.ip_address}</td>
                      <td className="muted">{formatDateTime(session.created_at)}</td>
                      <td className="muted">
                        {session.last_seen_at ? formatRelative(session.last_seen_at) : "—"}
                      </td>
                      <td className="muted">{formatDateTime(session.expires_at)}</td>
                      <td>
                        {session.current ? (
                          <span className="badge ACTIVE no-dot">This session</span>
                        ) : (
                          <span className="faint">—</span>
                        )}
                      </td>
                      <td>
                        <button
                          type="button"
                          className="btn danger sm"
                          aria-label={`Revoke session on ${session.device_label}`}
                          disabled={session.current || revokeOne.isPending}
                          title={
                            session.current
                              ? "This is your current session"
                              : `Sign out of ${session.device_label}`
                          }
                          onClick={() => revokeOne.mutate(session)}
                        >
                          Revoke
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Pagination page={sessionsPage} onPage={setOffset} />
            <p className="small faint mt-8">
              Revoked sessions disappear from this list after your next token refresh.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
