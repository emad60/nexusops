import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiDelete, apiGet, apiPost } from "../api/client";
import type {
  DomainOut,
  NodeProxyStatusOut,
  Page,
  RouteConfigState,
  RouteOut,
  ServerSummary,
  UpstreamContainerOut,
} from "../api/types";
import { Pagination } from "../components/Pagination";
import { TableSkeleton } from "../components/Skeleton";
import { EmptyState, ErrorBlock, Modal, StatusBadge } from "../components/ui";
import { CheckboxField, SelectField, TextField } from "../components/form";
import { useToast } from "../components/toast";
import { useAuth } from "../auth/AuthContext";
import { formatRelative, truncate } from "../lib/format";

const PAGE_SIZE = 25;
const CONFIG_STATES: RouteConfigState[] = ["PENDING", "IN_SYNC", "STALE", "FAILED"];

function describeError(err: unknown): string {
  if (err instanceof ApiError) {
    const friendly: Record<string, string> = {
      DOMAIN_NOT_VERIFIED: "Verify the domain before enabling a route for it.",
      NGINX_PREFLIGHT_FAILED:
        "This node did not pass its nginx pre-flight, so it cannot serve routes yet.",
      NGINX_LISTENER_CONFLICT: "This node's nginx does not own the listeners routing needs.",
      NODE_OFFLINE: "This node is offline; routing changes cannot be applied to it.",
      NODE_CAPABILITY_STALE: "This node has not reported in recently — wait for its next heartbeat.",
      UPSTREAM_NOT_RUNNING: "The container backing this route is not running.",
      PORT_NOT_PUBLISHED: "That port is not published by the selected container on this node.",
      PORT_RESERVED: "Port 80/443 belong to the node's proxy and cannot be route upstreams.",
      ROUTE_CONFLICT: "Another enabled route already answers for this host and path on this node.",
      HOSTNAME_NOT_COVERED: "The hostname is not covered by the selected domain.",
      CONTAINER_NOT_ON_NODE: "The container must run on the route's node.",
      DOMAIN_HAS_ENABLED_ROUTES: "Disable the domain's routes before deleting the domain.",
    };
    return friendly[err.code] ?? `${err.code}: ${err.message}`;
  }
  return "Request failed";
}

function CreateRouteDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const notify = useToast();
  const queryClient = useQueryClient();
  const [domainId, setDomainId] = useState("");
  const [nodeId, setNodeId] = useState("");
  const [containerId, setContainerId] = useState("");
  const [port, setPort] = useState<number | "">("");
  const [hostname, setHostname] = useState("");
  const [path, setPath] = useState("/");
  const [enableNow, setEnableNow] = useState(true);
  const [formError, setFormError] = useState<string | null>(null);

  const domainsQuery = useQuery({
    queryKey: ["domains", "verified-options"],
    queryFn: ({ signal }) => apiGet<Page<DomainOut>>("/domains", { limit: 100 }, signal),
    enabled: open,
  });
  const nodesQuery = useQuery({
    queryKey: ["servers", "routing-options"],
    queryFn: ({ signal }) => apiGet<Page<ServerSummary>>("/nodes", { limit: 100 }, signal),
    enabled: open,
  });
  const targetsQuery = useQuery({
    queryKey: ["route-targets", nodeId],
    queryFn: ({ signal }) =>
      apiGet<UpstreamContainerOut[]>(`/nodes/${nodeId}/route-targets`, undefined, signal),
    enabled: open && Boolean(nodeId),
  });
  const proxyQuery = useQuery({
    queryKey: ["proxy-status", nodeId],
    queryFn: ({ signal }) =>
      apiGet<NodeProxyStatusOut>(`/nodes/${nodeId}/proxy/status`, undefined, signal),
    enabled: open && Boolean(nodeId),
  });

  const domains = domainsQuery.data?.items ?? [];
  const nodes = nodesQuery.data?.items ?? [];
  const targets = targetsQuery.data ?? [];
  const selectedContainer = targets.find((item) => item.id === containerId) ?? null;
  const ports = selectedContainer?.upstream_ports ?? [];
  const selectedDomain = domains.find((item) => item.id === domainId) ?? null;

  const createMutation = useMutation({
    mutationFn: (body: Record<string, unknown>) => apiPost<RouteOut>("/routes", body),
    onSuccess: (created) => {
      void queryClient.invalidateQueries({ queryKey: ["routes"] });
      notify(
        created.enabled
          ? `Route ${created.hostname}${created.path} enabled — applying to the node`
          : `Route ${created.hostname}${created.path} created`,
        "success",
      );
      setFormError(null);
      onClose();
    },
    onError: (err) => {
      setFormError(describeError(err));
      notify(describeError(err), "error");
    },
  });

  const submit = () => {
    if (!domainId || !nodeId || !containerId || port === "") {
      setFormError("Domain, node, container and port are all required.");
      return;
    }
    setFormError(null);
    createMutation.mutate({
      domain_id: domainId,
      node_id: nodeId,
      container_id: containerId,
      port,
      hostname: hostname.trim() || selectedDomain?.name || "",
      path: path.trim() || "/",
      enabled: enableNow,
    });
  };

  return (
    <Modal open={open} title="New route" onClose={onClose} wide>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          submit();
        }}
      >
        <div className="field-row">
          <SelectField
            id="route-domain"
            label="Domain"
            required
            value={domainId}
            onChange={(event) => {
              setDomainId(event.target.value);
              const picked = domains.find((item) => item.id === event.target.value);
              if (picked) setHostname(picked.name);
            }}
          >
            <option value="">Select a domain…</option>
            {domains.map((domain) => (
              <option key={domain.id} value={domain.id}>
                {domain.name} ({domain.status})
              </option>
            ))}
          </SelectField>
          <SelectField
            id="route-node"
            label="Node"
            required
            value={nodeId}
            onChange={(event) => {
              setNodeId(event.target.value);
              setContainerId("");
              setPort("");
            }}
          >
            <option value="">Select a node…</option>
            {nodes.map((node) => (
              <option key={node.id} value={node.id}>
                {node.name}
              </option>
            ))}
          </SelectField>
        </div>

        {nodeId && proxyQuery.data && !proxyQuery.data.eligible ? (
          <div className="form-error">
            This node cannot serve routes right now: {proxyQuery.data.ineligible_reason || "its nginx pre-flight has not passed"}.
          </div>
        ) : null}

        <div className="field-row">
          <SelectField
            id="route-container"
            label="Container"
            required
            value={containerId}
            disabled={!nodeId}
            onChange={(event) => {
              setContainerId(event.target.value);
              setPort("");
            }}
          >
            <option value="">Select a container…</option>
            {targets.map((container) => (
              <option
                key={container.id}
                value={container.id}
                disabled={container.upstream_ports.length === 0}
              >
                {container.name}
                {container.upstream_ports.length === 0 ? " (no published ports)" : ""}
              </option>
            ))}
          </SelectField>
          <SelectField
            id="route-port"
            label="Published port"
            required
            value={port === "" ? "" : String(port)}
            disabled={!selectedContainer}
            onChange={(event) => setPort(event.target.value ? Number(event.target.value) : "")}
          >
            <option value="">Select a port…</option>
            {ports.map((item) => (
              <option key={item.host_port} value={item.host_port}>
                {item.host_port} → {item.upstream_host}:{item.container_port}
              </option>
            ))}
          </SelectField>
        </div>

        <div className="field-row">
          <TextField
            id="route-hostname"
            label="Hostname"
            required
            hint="The domain itself, one label below it, or its wildcard form."
            value={hostname}
            onChange={(event) => setHostname(event.target.value)}
            placeholder="app.example.com"
          />
          <TextField
            id="route-path"
            label="Path"
            hint="A prefix, always starting with /."
            value={path}
            onChange={(event) => setPath(event.target.value)}
            placeholder="/"
          />
        </div>

        <CheckboxField
          id="route-enable-now"
          label="Enable after creating"
          info="Enabling queues an nginx.apply on the node. It requires a verified domain, an eligible node and a running container."
          checked={enableNow}
          onChange={(event) => setEnableNow(event.target.checked)}
        />

        {formError ? <div className="form-error">{formError}</div> : null}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn primary" disabled={createMutation.isPending}>
            {createMutation.isPending ? "Saving…" : enableNow ? "Create & enable" : "Create route"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export default function RouteListPage() {
  const { hasPermission } = useAuth();
  const canManage = hasPermission("domain.manage");
  const notify = useToast();
  const queryClient = useQueryClient();

  const [offset, setOffset] = useState(0);
  const [stateFilter, setStateFilter] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<RouteOut | null>(null);

  const routesQuery = useQuery({
    queryKey: ["routes", { limit: PAGE_SIZE, offset, config_state: stateFilter }],
    queryFn: ({ signal }) =>
      apiGet<Page<RouteOut>>(
        "/routes",
        { limit: PAGE_SIZE, offset, config_state: stateFilter || undefined },
        signal,
      ),
  });

  const toggleMutation = useMutation({
    mutationFn: (route: RouteOut) =>
      apiPost<RouteOut>(`/routes/${route.id}/${route.enabled ? "disable" : "enable"}`),
    onSuccess: (updated) => {
      void queryClient.invalidateQueries({ queryKey: ["routes"] });
      notify(`Route ${updated.hostname}${updated.path} ${updated.enabled ? "enabled" : "disabled"}`, "success");
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  const deleteMutation = useMutation({
    mutationFn: (route: RouteOut) => apiDelete<void>(`/routes/${route.id}`),
    onSuccess: (_result, route) => {
      void queryClient.invalidateQueries({ queryKey: ["routes"] });
      notify(`Route ${route.hostname}${route.path} deleted`, "success");
      setPendingDelete(null);
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  const routes = useMemo(() => routesQuery.data?.items ?? [], [routesQuery.data]);

  return (
    <main>
      <div className="page-head">
        <div className="page-title">
          <h1>Routes</h1>
          <p className="page-sub">
            HTTP routes served by a node&apos;s nginx from a container on that node. Enabling a route
            queues an apply and reports the outcome back as the route&apos;s state.
          </p>
        </div>
        <div className="page-actions">
          {canManage ? (
            <button type="button" className="btn primary" onClick={() => setCreateOpen(true)}>
              + New route
            </button>
          ) : null}
        </div>
      </div>

      <div className="table-toolbar">
        <div className="filters">
          <label className="flex gap-8" htmlFor="route-state-filter">
            <span className="small muted">State</span>
            <select
              id="route-state-filter"
              className="input"
              value={stateFilter}
              onChange={(event) => {
                setStateFilter(event.target.value);
                setOffset(0);
              }}
            >
              <option value="">All states</option>
              {CONFIG_STATES.map((state) => (
                <option key={state} value={state}>
                  {state}
                </option>
              ))}
            </select>
          </label>
        </div>
      </div>

      {routesQuery.isLoading ? (
        <TableSkeleton label="Loading routes" rows={8} cols={7} />
      ) : routesQuery.isError ? (
        <ErrorBlock error={routesQuery.error} />
      ) : routes.length === 0 ? (
        <EmptyState
          icon="🛣"
          title={stateFilter ? "No routes match the current filter" : "No routes yet"}
          hint={
            canManage && !stateFilter
              ? "Add a verified domain and an eligible node, then point a route at a published container port."
              : undefined
          }
          action={
            canManage && !stateFilter ? (
              <button type="button" className="btn primary" onClick={() => setCreateOpen(true)}>
                + New route
              </button>
            ) : null
          }
        />
      ) : (
        <div className="card">
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th scope="col">Host</th>
                  <th scope="col">Domain</th>
                  <th scope="col">Node</th>
                  <th scope="col">Upstream</th>
                  <th scope="col">State</th>
                  <th scope="col">Applied</th>
                  {canManage ? <th scope="col">Actions</th> : null}
                </tr>
              </thead>
              <tbody>
                {routes.map((route) => (
                  <tr key={route.id}>
                    <td>
                      <span className="mono">
                        {route.hostname}
                        {route.path}
                      </span>
                      <span className="small muted"> {route.url}</span>
                    </td>
                    <td>{route.domain_name ?? "—"}</td>
                    <td>{route.node_name ?? "—"}</td>
                    <td className="mono">
                      {route.container_name ? truncate(route.container_name, 24) : "—"}:{route.port}
                    </td>
                    <td>
                      <StatusBadge value={route.config_state} />
                      {route.last_apply_error ? (
                        <span className="small muted" title={route.last_apply_error}>
                          {route.last_apply_error}
                        </span>
                      ) : null}
                    </td>
                    <td>
                      {route.last_applied_at ? (
                        <span title={route.last_applied_at}>{formatRelative(route.last_applied_at)}</span>
                      ) : (
                        <span className="faint">never</span>
                      )}
                    </td>
                    {canManage ? (
                      <td>
                        <div className="flex gap-8">
                          <button
                            type="button"
                            className="btn sm"
                            disabled={toggleMutation.isPending}
                            onClick={() => toggleMutation.mutate(route)}
                          >
                            {route.enabled ? "Disable" : "Enable"}
                          </button>
                          <button
                            type="button"
                            className="btn sm danger"
                            onClick={() => setPendingDelete(route)}
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    ) : null}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {routesQuery.data ? <Pagination page={routesQuery.data} onPage={setOffset} /> : null}
        </div>
      )}

      <CreateRouteDialog open={createOpen} onClose={() => setCreateOpen(false)} />

      <Modal
        open={pendingDelete !== null}
        title="Delete route"
        onClose={() => setPendingDelete(null)}
      >
        <p>
          Delete <strong>{pendingDelete?.hostname}{pendingDelete?.path}</strong>? The node still
          receives an apply so the route disappears from the served configuration.
        </p>
        <div className="modal-actions">
          <button type="button" className="btn" onClick={() => setPendingDelete(null)}>
            Cancel
          </button>
          <button
            type="button"
            className="btn danger"
            disabled={deleteMutation.isPending}
            onClick={() => pendingDelete && deleteMutation.mutate(pendingDelete)}
          >
            Delete route
          </button>
        </div>
      </Modal>
    </main>
  );
}
