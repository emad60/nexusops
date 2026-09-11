import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiGet, apiPost } from "../api/client";
import type { Page, ServerSummary } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { EmptyState, ErrorBlock, LoadingBlock, Modal, StatusBadge, TagChip } from "../components/ui";
import { Pagination } from "../components/Pagination";
import { useToast } from "../components/toast";
import { formatBytesMb, formatGb, formatRelative } from "../lib/format";

const PAGE_SIZE = 20;
const SERVER_STATUSES = ["ONLINE", "OFFLINE", "DEGRADED", "UNKNOWN"] as const;

/** Payload for POST /servers (mirrors the backend ServerCreate schema). */
interface ServerCreatePayload {
  name: string;
  hostname: string;
  ip_address: string;
  os_name: string;
  os_version: string;
  arch: string;
  environment: string;
  location: string;
  description: string;
  heartbeat_interval_seconds: number;
  offline_after_seconds: number | null;
  tags: string[];
  simulated: boolean;
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

const EMPTY_FORM: ServerFormValues = {
  name: "",
  hostname: "",
  ip_address: "",
  os_name: "",
  os_version: "",
  arch: "",
  environment: "production",
  location: "",
  description: "",
  heartbeat_interval_seconds: "30",
  offline_after_seconds: "",
  tags: "",
  simulated: false,
};

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return `${error.code}: ${error.message}`;
  if (error instanceof Error) return error.message;
  return "Request failed";
}

function setParam(params: URLSearchParams, key: string, value: string): void {
  if (value) params.set(key, value);
  else params.delete(key);
}

function buildPayload(values: ServerFormValues): ServerCreatePayload | string {
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

function ServerFormFields({
  values,
  onChange,
}: {
  values: ServerFormValues;
  onChange: (next: ServerFormValues) => void;
}) {
  const set = <K extends keyof ServerFormValues>(key: K, value: ServerFormValues[K]) =>
    onChange({ ...values, [key]: value });

  return (
    <>
      <div className="field-row">
        <div className="field">
          <label htmlFor="server-name">Name *</label>
          <input
            id="server-name"
            className="input"
            value={values.name}
            onChange={(e) => set("name", e.target.value)}
            placeholder="edge-01"
            autoFocus
          />
        </div>
        <div className="field">
          <label htmlFor="server-hostname">Hostname *</label>
          <input
            id="server-hostname"
            className="input"
            value={values.hostname}
            onChange={(e) => set("hostname", e.target.value)}
            placeholder="edge01.example.net"
          />
        </div>
      </div>
      <div className="field-row">
        <div className="field">
          <label htmlFor="server-ip">IP address</label>
          <input
            id="server-ip"
            className="input"
            value={values.ip_address}
            onChange={(e) => set("ip_address", e.target.value)}
            placeholder="10.0.0.14"
          />
        </div>
        <div className="field">
          <label htmlFor="server-environment">Environment</label>
          <input
            id="server-environment"
            className="input"
            value={values.environment}
            onChange={(e) => set("environment", e.target.value)}
            placeholder="production"
          />
        </div>
        <div className="field">
          <label htmlFor="server-arch">Architecture</label>
          <input
            id="server-arch"
            className="input"
            value={values.arch}
            onChange={(e) => set("arch", e.target.value)}
            placeholder="x86_64"
          />
        </div>
      </div>
      <div className="field-row">
        <div className="field">
          <label htmlFor="server-os-name">OS</label>
          <input
            id="server-os-name"
            className="input"
            value={values.os_name}
            onChange={(e) => set("os_name", e.target.value)}
            placeholder="Ubuntu"
          />
        </div>
        <div className="field">
          <label htmlFor="server-os-version">OS version</label>
          <input
            id="server-os-version"
            className="input"
            value={values.os_version}
            onChange={(e) => set("os_version", e.target.value)}
            placeholder="24.04"
          />
        </div>
        <div className="field">
          <label htmlFor="server-location">Location</label>
          <input
            id="server-location"
            className="input"
            value={values.location}
            onChange={(e) => set("location", e.target.value)}
            placeholder="dc-west-rack4"
          />
        </div>
      </div>
      <div className="field-row">
        <div className="field">
          <label htmlFor="server-heartbeat">Heartbeat interval (seconds)</label>
          <input
            id="server-heartbeat"
            className="input"
            type="number"
            min={5}
            max={3600}
            value={values.heartbeat_interval_seconds}
            onChange={(e) => set("heartbeat_interval_seconds", e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="server-offline-after">Offline after (seconds, optional)</label>
          <input
            id="server-offline-after"
            className="input"
            type="number"
            min={1}
            value={values.offline_after_seconds}
            onChange={(e) => set("offline_after_seconds", e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="server-tags">Tags (comma separated)</label>
          <input
            id="server-tags"
            className="input"
            value={values.tags}
            onChange={(e) => set("tags", e.target.value)}
            placeholder="edge, gpu"
          />
        </div>
      </div>
      <div className="field">
        <label htmlFor="server-description">Description</label>
        <textarea
          id="server-description"
          className="input"
          rows={2}
          value={values.description}
          onChange={(e) => set("description", e.target.value)}
        />
      </div>
      <div className="field">
        <label htmlFor="server-simulated">
          <input
            id="server-simulated"
            type="checkbox"
            checked={values.simulated}
            onChange={(e) => set("simulated", e.target.checked)}
          />{" "}
          Simulated server (demo data)
        </label>
      </div>
    </>
  );
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
  const [values, setValues] = useState<ServerFormValues>(EMPTY_FORM);
  const [formError, setFormError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: (payload: ServerCreatePayload) => apiPost<ServerSummary>("/servers", payload),
    onSuccess: (created) => {
      notify(`Server ${created.name} registered`, "success");
      void queryClient.invalidateQueries({ queryKey: ["servers"] });
      onCreated(created);
      onClose();
    },
    onError: (error) => notify(errorMessage(error), "error"),
  });

  const submit = () => {
    const payload = buildPayload(values);
    if (typeof payload === "string") {
      setFormError(payload);
      return;
    }
    setFormError(null);
    createMutation.mutate(payload);
  };

  return (
    <Modal open={open} title="Register server" onClose={onClose} wide>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <ServerFormFields values={values} onChange={setValues} />
        {formError ? (
          <p className="form-error" role="alert">
            {formError}
          </p>
        ) : null}
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
          <input
            type="search"
            className="input search-input"
            placeholder="Search by name or hostname…"
            aria-label="Search servers"
            value={qDraft}
            onChange={(e) => setQDraft(e.target.value)}
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
      {serversQuery.isPending ? <LoadingBlock label="Loading servers…" /> : null}

      {serversQuery.data && servers.length === 0 ? (
        <EmptyState
          icon="◎"
          title="No servers found"
          hint={
            hasFilters
              ? "No machine matches the current filters — try clearing them."
              : "Register your first server to start monitoring."
          }
        />
      ) : null}

      {serversQuery.data && servers.length > 0 ? (
        <div className="card">
          <div className="table-wrap">
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
                  <tr key={server.id}>
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
