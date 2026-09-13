import { useState, type FormEvent } from "react";
import {
  keepPreviousData,
  useMutation,
  useQueries,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { apiGet, apiPatch, apiPost, ApiError } from "../api/client";
import type { DockerHostOut, Page, ServerSummary } from "../api/types";
import { Pagination } from "../components/Pagination";
import { EmptyState, ErrorBlock, Modal, StatusBadge } from "../components/ui";
import { TableSkeleton } from "../components/Skeleton";
import { InfoHint } from "../components/InfoHint";
import { CheckboxField, SearchInput, TextField } from "../components/form";
import { useToast } from "../components/toast";
import type { ContainerRow } from "./ContainerListPage";

/** Result of POST /docker-hosts/{id}/ping. */
export interface DockerHostPingOut {
  status: string;
  checked_at: string;
  latency_ms: number | null;
  error: string;
}

/** Exact per-host container totals, from two count-only container queries. */
export interface HostContainerCounts {
  total: number;
  running: number;
}

const PAGE_SIZE = 20;

const HOST_STATUS_OPTIONS = ["AVAILABLE", "UNAVAILABLE", "UNKNOWN"];

interface HostEditForm {
  name: string;
  endpointUrl: string;
  tlsVerify: boolean;
}

const EMPTY_EDIT: HostEditForm = { name: "", endpointUrl: "", tlsVerify: true };

/** Absolute UTC stamp — deterministic regardless of the viewer's timezone. */
function formatUtc(iso: string | null | undefined): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return `${date.toISOString().replace("T", " ").slice(0, 19)} UTC`;
}

export default function DockerHostsPage() {
  const notify = useToast();
  const queryClient = useQueryClient();
  const [offset, setOffset] = useState(0);
  const [status, setStatus] = useState("");
  const [search, setSearch] = useState("");
  const [editTarget, setEditTarget] = useState<DockerHostOut | null>(null);
  const [editForm, setEditForm] = useState<HostEditForm>(EMPTY_EDIT);
  const [editErrors, setEditErrors] = useState<Partial<Record<"name" | "endpointUrl", string>>>({});
  const [editFormError, setEditFormError] = useState<string | null>(null);

  const hostsQuery = useQuery({
    queryKey: ["docker-hosts", { offset, status, search }],
    queryFn: ({ signal }) =>
      apiGet<Page<DockerHostOut>>(
        "/docker-hosts",
        {
          limit: PAGE_SIZE,
          offset,
          status: status || undefined,
          q: search || undefined,
        },
        signal,
      ),
    placeholderData: keepPreviousData,
  });

  // server_id → server name for the "attached server" column.
  const serversQuery = useQuery({
    queryKey: ["servers", "docker-hosts-page"],
    queryFn: ({ signal }) => apiGet<Page<ServerSummary>>("/servers", { limit: 100 }, signal),
    staleTime: 60_000,
  });

  const hostItems = hostsQuery.data?.items ?? [];
  const serverNames = new Map(
    (serversQuery.data?.items ?? []).map((server) => [server.id, server.name]),
  );

  // Aggregate container status per host: two tiny count-only queries.
  const countQueries = useQueries({
    queries: hostItems.map((host) => ({
      queryKey: ["container-counts", host.id],
      queryFn: async ({ signal }: { signal: AbortSignal }): Promise<HostContainerCounts> => {
        const [totalPage, runningPage] = await Promise.all([
          apiGet<Page<ContainerRow>>("/containers", { host_id: host.id, limit: 1 }, signal),
          apiGet<Page<ContainerRow>>(
            "/containers",
            { host_id: host.id, status: "RUNNING", limit: 1 },
            signal,
          ),
        ]);
        return { total: totalPage.total, running: runningPage.total };
      },
      staleTime: 15_000,
    })),
  });
  const countsById = new Map<string, HostContainerCounts | undefined>();
  hostItems.forEach((host, index) => {
    countsById.set(host.id, countQueries[index]?.data);
  });

  const pingMutation = useMutation({
    mutationFn: (hostId: string) => apiPost<DockerHostPingOut>(`/docker-hosts/${hostId}/ping`),
    onSuccess: (result) => {
      if (result.status === "AVAILABLE") {
        const latency =
          result.latency_ms !== null && result.latency_ms !== undefined
            ? Math.round(result.latency_ms)
            : "?";
        notify(`Host reachable in ${latency} ms`, "success");
      } else {
        notify(`Host unreachable: ${result.error || result.status}`, "error");
      }
      void queryClient.invalidateQueries({ queryKey: ["docker-hosts"] });
    },
    onError: (error) => {
      notify(
        error instanceof ApiError ? `${error.code}: ${error.message}` : "Ping request failed",
        "error",
      );
    },
  });

  const openEdit = (host: DockerHostOut) => {
    setEditTarget(host);
    setEditForm({ name: host.name, endpointUrl: host.endpoint_url, tlsVerify: host.tls_verify });
    setEditErrors({});
    setEditFormError(null);
  };

  const updateHost = useMutation({
    mutationFn: (input: { id: string; form: HostEditForm }) =>
      apiPatch<DockerHostOut>(`/docker-hosts/${input.id}`, {
        name: input.form.name.trim(),
        endpoint_url: input.form.endpointUrl.trim(),
        tls_verify: input.form.tlsVerify,
      }),
    onSuccess: (updated) => {
      notify(`Host ${updated.name} updated`, "success");
      void queryClient.invalidateQueries({ queryKey: ["docker-hosts"] });
      setEditTarget(null);
    },
    onError: (error) => {
      setEditFormError(
        error instanceof ApiError ? `${error.code}: ${error.message}` : "Update request failed",
      );
    },
  });

  const submitEdit = (event: FormEvent) => {
    event.preventDefault();
    if (!editTarget) return;
    const next: Partial<Record<"name" | "endpointUrl", string>> = {};
    if (!editForm.name.trim()) next.name = "Name is required.";
    const endpoint = editForm.endpointUrl.trim();
    if (endpoint && /\s/.test(endpoint)) {
      next.endpointUrl = "Endpoint must not contain whitespace.";
    } else if (endpoint && !/^[a-z][a-z0-9+.-]*:\/\//i.test(endpoint)) {
      next.endpointUrl = "Use a scheme like unix:// or tcp:// — or leave empty for agent-inherited.";
    }
    setEditErrors(next);
    setEditFormError(null);
    if (Object.keys(next).length > 0) return;
    updateHost.mutate({ id: editTarget.id, form: editForm });
  };

  return (
    <div>
      <div className="page-head">
        <div className="page-title">
          <h1>Docker Hosts</h1>
          <p className="page-sub">
            Docker endpoints across the fleet
            {hostsQuery.data ? ` · ${hostsQuery.data.total} total` : ""}
          </p>
        </div>
      </div>

      <div className="card">
        <div className="table-toolbar">
          <div className="filters">
            <SearchInput
              placeholder="Search hosts…"
              aria-label="Search docker hosts"
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setOffset(0);
              }}
              onClear={() => {
                setSearch("");
                setOffset(0);
              }}
            />
            <select
              className="input"
              aria-label="Filter by host status"
              value={status}
              onChange={(event) => {
                setStatus(event.target.value);
                setOffset(0);
              }}
            >
              <option value="">All statuses</option>
              {HOST_STATUS_OPTIONS.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          </div>
        </div>

        {hostsQuery.isPending ? (
          <TableSkeleton label="Loading docker hosts" rows={8} cols={9} />
        ) : hostsQuery.isError ? (
          <ErrorBlock error={hostsQuery.error} />
        ) : hostItems.length === 0 ? (
          <EmptyState
            icon="⬢"
            title="No docker hosts registered"
            hint="Hosts appear once a server enrolls with docker enabled, or a host is registered through the API."
          />
        ) : (
          <>
            <div className="table-wrap" style={{ opacity: hostsQuery.isFetching ? 0.65 : 1 }}>
              <table className="data">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Endpoint</th>
                    <th>Server</th>
                    <th>Status</th>
                    <th className="num">Containers</th>
                    <th>
                      TLS{" "}
                      <InfoHint label="About TLS verification">
                        Whether the agent verifies the docker daemon's TLS certificate.
                        "verified" is the safe default; "off" usually means a local unix socket
                        or an explicitly unsecured daemon.
                      </InfoHint>
                    </th>
                    <th>Last checked</th>
                    <th>Last error</th>
                    <th>
                      <span className="faint">Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {hostItems.map((host) => {
                    const counts = countsById.get(host.id);
                    return (
                      <tr key={host.id}>
                        <td className="mono">{host.name}</td>
                        <td className="mono small">{host.endpoint_url || "(agent-inherited)"}</td>
                        <td>
                          {host.server_id ? (
                            serverNames.has(host.server_id) ? (
                              <Link to={`/servers/${host.server_id}`}>
                                {serverNames.get(host.server_id)}
                              </Link>
                            ) : (
                              <span className="mono small" title={host.server_id}>
                                {host.server_id.slice(0, 8)}…
                              </span>
                            )
                          ) : (
                            <span className="faint">—</span>
                          )}
                        </td>
                        <td>
                          <StatusBadge value={host.status} />
                        </td>
                        <td className="num">
                          {counts ? (
                            <span title={`${counts.running} running of ${counts.total}`}>
                              {counts.running} / {counts.total}
                            </span>
                          ) : (
                            <span className="faint">…</span>
                          )}
                        </td>
                        <td>{host.tls_verify ? "✓ verified" : <span className="faint">off</span>}</td>
                        <td className="small muted">{formatUtc(host.last_checked_at)}</td>
                        <td className="small">
                          {host.last_error ? (
                            <span
                              className="muted"
                              title={host.last_error}
                              style={{
                                display: "inline-block",
                                maxWidth: 220,
                                whiteSpace: "nowrap",
                                overflow: "hidden",
                                textOverflow: "ellipsis",
                                verticalAlign: "bottom",
                              }}
                            >
                              {host.last_error}
                            </span>
                          ) : (
                            <span className="faint">—</span>
                          )}
                        </td>
                        <td>
                          <div className="flex gap-8">
                            <button
                              type="button"
                              className="btn sm"
                              aria-label={`Edit host ${host.name}`}
                              onClick={() => openEdit(host)}
                            >
                              Edit
                            </button>
                            <button
                              type="button"
                              className="btn sm"
                              aria-label={`Ping host ${host.name}`}
                              disabled={pingMutation.isPending && pingMutation.variables === host.id}
                              onClick={() => pingMutation.mutate(host.id)}
                            >
                              Ping
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {hostsQuery.data ? (
              <Pagination
                page={hostsQuery.data}
                onPage={(nextOffset) => setOffset(nextOffset)}
              />
            ) : null}
          </>
        )}
      </div>

      <Modal
        open={editTarget !== null}
        title={editTarget ? `Edit host ${editTarget.name}` : "Edit host"}
        onClose={() => setEditTarget(null)}
      >
        <form noValidate onSubmit={submitEdit}>
          <TextField
            id="host-edit-name"
            label="Name"
            required
            error={editErrors.name ?? null}
            value={editForm.name}
            onChange={(event) => setEditForm({ ...editForm, name: event.target.value })}
          />
          <TextField
            id="host-edit-endpoint"
            label="Endpoint"
            mono
            error={editErrors.endpointUrl ?? null}
            hint="unix:///var/run/docker.sock, tcp://host:2375 — leave empty for agent-inherited."
            placeholder="unix:///var/run/docker.sock"
            value={editForm.endpointUrl}
            onChange={(event) => setEditForm({ ...editForm, endpointUrl: event.target.value })}
          />
          <CheckboxField
            id="host-edit-tls"
            label="Verify the daemon's TLS certificate"
            checked={editForm.tlsVerify}
            onChange={(event) => setEditForm({ ...editForm, tlsVerify: event.target.checked })}
          />
          {editFormError ? <div className="form-error">{editFormError}</div> : null}
          <div className="modal-actions">
            <button type="button" className="btn" onClick={() => setEditTarget(null)}>
              Cancel
            </button>
            <button type="submit" className="btn primary" disabled={updateHost.isPending}>
              {updateHost.isPending ? "Saving…" : "Save changes"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
