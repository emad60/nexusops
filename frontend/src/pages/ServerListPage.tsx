import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiGet, apiPost } from "../api/client";
import type { Page, ServerSummary } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { EmptyState, ErrorBlock, Modal, StatusBadge, TagChip } from "../components/ui";
import { TableSkeleton } from "../components/Skeleton";
import { Pagination } from "../components/Pagination";
import {
  buildServerPayload,
  EMPTY_SERVER_FORM,
  ServerFormFields,
  validateServerForm,
  type ServerFormErrors,
  type ServerFormValues,
  type ServerPayload,
} from "../components/ServerForm";
import { SearchInput } from "../components/form";
import { useToast } from "../components/toast";
import { formatBytesMb, formatGb, formatRelative } from "../lib/format";

const PAGE_SIZE = 20;
const SERVER_STATUSES = ["ONLINE", "OFFLINE", "DEGRADED", "UNKNOWN"] as const;

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return `${error.code}: ${error.message}`;
  if (error instanceof Error) return error.message;
  return "Request failed";
}

function setParam(params: URLSearchParams, key: string, value: string): void {
  if (value) params.set(key, value);
  else params.delete(key);
}

function AddServerModal({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: (server: ServerSummary) => void;
}) {
  const notify = useToast();
  const queryClient = useQueryClient();
  const [values, setValues] = useState<ServerFormValues>(EMPTY_SERVER_FORM);
  const [errors, setErrors] = useState<ServerFormErrors>({});

  const createMutation = useMutation({
    mutationFn: (payload: ServerPayload) => apiPost<ServerSummary>("/servers", payload),
    onSuccess: (created) => {
      notify(`Server ${created.name} registered`, "success");
      void queryClient.invalidateQueries({ queryKey: ["servers"] });
      onCreated(created);
      onClose();
    },
    onError: (error) => notify(errorMessage(error), "error"),
  });

  const submit = () => {
    const nextErrors = validateServerForm(values);
    setErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;
    createMutation.mutate(buildServerPayload(values));
  };

  return (
    <Modal open={open} title="Register server" onClose={onClose} wide>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <ServerFormFields values={values} onChange={setValues} errors={errors} focusName />
        <div className="modal-actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn primary" disabled={createMutation.isPending}>
            {createMutation.isPending ? "Registering…" : "Register server"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export default function ServerListPage() {
  const { hasPermission } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [addOpen, setAddOpen] = useState(false);

  const q = searchParams.get("q") ?? "";
  const status = searchParams.get("status") ?? "";
  const environment = searchParams.get("environment") ?? "";
  const offset = Math.max(0, Number(searchParams.get("offset") ?? "0") || 0);

  // Drafts keep the text inputs responsive; they are committed to the URL
  // (which drives the query) after a short debounce.
  const [qDraft, setQDraft] = useState(q);
  const [envDraft, setEnvDraft] = useState(environment);

  useEffect(() => setQDraft(q), [q]);
  useEffect(() => setEnvDraft(environment), [environment]);

  useEffect(() => {
    const timer = setTimeout(() => {
      if (qDraft.trim() === q && envDraft.trim() === environment) return;
      const next = new URLSearchParams(searchParams);
      setParam(next, "q", qDraft.trim());
      setParam(next, "environment", envDraft.trim());
      next.delete("offset");
      setSearchParams(next, { replace: true });
    }, 300);
    return () => clearTimeout(timer);
  }, [qDraft, envDraft, q, environment, searchParams, setSearchParams]);

  const setFilter = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams);
    setParam(next, key, value);
    next.delete("offset");
    setSearchParams(next);
  };

  const serversQuery = useQuery({
    queryKey: ["servers", { q, status, environment, offset }],
    queryFn: ({ signal }) =>
      apiGet<Page<ServerSummary>>(
        "/servers",
        {
          limit: PAGE_SIZE,
          offset,
          q: q || undefined,
          status: status || undefined,
          environment: environment || undefined,
        },
        signal,
      ),
    placeholderData: keepPreviousData,
  });

  const servers = serversQuery.data?.items ?? [];
  const hasFilters = Boolean(q || status || environment);

  return (
    <section aria-labelledby="servers-heading">
      <div className="page-head">
        <div className="page-title">
          <h1 id="servers-heading">Servers</h1>
          <p className="page-sub">Registered machines, their agent state and last heartbeat.</p>
        </div>
        <div className="page-actions">
          {hasPermission("server.create") ? (
            <button type="button" className="btn primary" onClick={() => setAddOpen(true)}>
              + Add server
            </button>
          ) : null}
        </div>
      </div>

      <div className="table-toolbar">
        <div className="filters">
          <SearchInput
            placeholder="Search by name or hostname…"
            aria-label="Search servers"
            value={qDraft}
            onChange={(e) => setQDraft(e.target.value)}
            onClear={() => setQDraft("")}
          />
          <select
            className="input"
            aria-label="Filter by status"
            value={status}
            onChange={(e) => setFilter("status", e.target.value)}
          >
            <option value="">All statuses</option>
            {SERVER_STATUSES.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
          <input
            type="text"
            className="input"
            placeholder="Environment…"
            aria-label="Filter by environment"
            value={envDraft}
            onChange={(e) => setEnvDraft(e.target.value)}
            style={{ width: 150 }}
          />
        </div>
      </div>

      {serversQuery.isError ? <ErrorBlock error={serversQuery.error} /> : null}
      {serversQuery.isPending ? <TableSkeleton label="Loading servers" rows={8} cols={8} /> : null}

      {serversQuery.data && servers.length === 0 ? (
        <EmptyState
          icon="◎"
          title="No servers found"
          hint={
            hasFilters
              ? "No machine matches the current filters — try clearing them."
              : "Register your first server to start monitoring."
          }
          action={
            !hasFilters && hasPermission("server.create") ? (
              <button type="button" className="btn primary" onClick={() => setAddOpen(true)}>
                Register server
              </button>
            ) : null
          }
        />
      ) : null}

      {serversQuery.data && servers.length > 0 ? (
        <div className="card">
          <div className="table-wrap sticky-first">
            <table className="data">
              <thead>
                <tr>
                  <th scope="col">Server</th>
                  <th scope="col">Status</th>
                  <th scope="col">Environment</th>
                  <th scope="col">IP address</th>
                  <th scope="col">Capacity</th>
                  <th scope="col">Agent</th>
                  <th scope="col">Last heartbeat</th>
                  <th scope="col">Tags</th>
                </tr>
              </thead>
              <tbody>
                {servers.map((server) => (
                  <tr key={server.id} className="clickable" onClick={() => navigate(`/servers/${server.id}`)}>
                    <td>
                      <Link to={`/servers/${server.id}`}>{server.name}</Link>
                      <div className="small faint mono">{server.hostname}</div>
                    </td>
                    <td>
                      <StatusBadge value={server.status} />
                    </td>
                    <td>{server.environment}</td>
                    <td className="mono">{server.ip_address || "—"}</td>
                    <td className="small">
                      {server.cpu_cores} vCPU · {formatBytesMb(server.memory_total_mb)} ·{" "}
                      {formatGb(server.disk_total_gb)}
                    </td>
                    <td className="mono small">
                      {server.enrolled ? server.agent_version || "enrolled" : "—"}
                    </td>
                    <td title={server.last_heartbeat_at ?? undefined}>
                      {formatRelative(server.last_heartbeat_at)}
                    </td>
                    <td>
                      {server.tags.map((tag) => (
                        <TagChip key={tag.id} name={tag.name} color={tag.color} />
                      ))}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination
            page={{
              items: servers,
              total: serversQuery.data.total,
              limit: serversQuery.data.limit,
              offset: serversQuery.data.offset,
            }}
            onPage={(nextOffset) => {
              const next = new URLSearchParams(searchParams);
              setParam(next, "offset", nextOffset > 0 ? String(nextOffset) : "");
              setSearchParams(next);
            }}
          />
        </div>
      ) : null}

      <AddServerModal
        open={addOpen}
        onClose={() => setAddOpen(false)}
        onCreated={(created) => navigate(`/servers/${created.id}`)}
      />
    </section>
  );
}
