import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiDelete, apiGet, apiPost } from "../api/client";
import type { DomainOut, Page } from "../api/types";
import { Pagination } from "../components/Pagination";
import { TableSkeleton } from "../components/Skeleton";
import { EmptyState, ErrorBlock, Modal, StatusBadge } from "../components/ui";
import { TextField } from "../components/form";
import { useToast } from "../components/toast";
import { useAuth } from "../auth/AuthContext";
import { formatRelative } from "../lib/format";

const PAGE_SIZE = 25;
const STATUS_FILTERS = ["PENDING", "VERIFYING", "VERIFIED", "STALE", "UNVERIFIED", "FAILED"] as const;

/** Human-readable rendering of an API failure, ownership conflicts in particular. */
function describeError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.code === "DOMAIN_EXISTS") return "That name is already tracked in this organization.";
    if (err.code === "DOMAIN_HAS_ENABLED_ROUTES") {
      return "Disable or delete this domain's routes before deleting the domain.";
    }
    return `${err.code}: ${err.message}`;
  }
  return "Request failed";
}

function CreateDomainDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const notify = useToast();
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [nameError, setNameError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const createMutation = useMutation({
    mutationFn: (body: { name: string }) => apiPost<DomainOut>("/domains", body),
    onSuccess: (created) => {
      void queryClient.invalidateQueries({ queryKey: ["domains"] });
      notify(`Domain "${created.name}" added — publish its TXT record to verify`, "success");
      setName("");
      setNameError(null);
      setFormError(null);
      onClose();
    },
    onError: (err) => {
      setFormError(describeError(err));
      notify(describeError(err), "error");
    },
  });

  const submit = () => {
    const trimmed = name.trim();
    const nextNameError = trimmed ? null : "Name is required.";
    setNameError(nextNameError);
    if (nextNameError) return;
    setFormError(null);
    createMutation.mutate({ name: trimmed });
  };

  return (
    <Modal open={open} title="Add a domain" onClose={onClose}>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          submit();
        }}
      >
        <TextField
          id="domain-name"
          label="Domain name"
          required
          error={nameError}
          hint="The apex name you control, e.g. example.com. Ownership is proven with a TXT record before any route can be enabled."
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="example.com"
          autoFocus
        />
        {formError ? <div className="form-error">{formError}</div> : null}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn primary" disabled={createMutation.isPending}>
            {createMutation.isPending ? "Adding…" : "Add domain"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export default function DomainListPage() {
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const canManage = hasPermission("domain.manage");
  const notify = useToast();
  const queryClient = useQueryClient();

  const [offset, setOffset] = useState(0);
  const [statusFilter, setStatusFilter] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<DomainOut | null>(null);

  const domainsQuery = useQuery({
    queryKey: ["domains", { limit: PAGE_SIZE, offset, status: statusFilter }],
    queryFn: ({ signal }) =>
      apiGet<Page<DomainOut>>(
        "/domains",
        { limit: PAGE_SIZE, offset, status: statusFilter || undefined },
        signal,
      ),
  });

  const verifyMutation = useMutation({
    mutationFn: (domain: DomainOut) => apiPost<DomainOut>(`/domains/${domain.id}/verify`),
    onSuccess: (updated) => {
      void queryClient.invalidateQueries({ queryKey: ["domains"] });
      notify(`Re-verification requested for ${updated.name}`, "success");
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  const deleteMutation = useMutation({
    mutationFn: (domain: DomainOut) => apiDelete<void>(`/domains/${domain.id}`),
    onSuccess: (_result, domain) => {
      void queryClient.invalidateQueries({ queryKey: ["domains"] });
      notify(`Domain "${domain.name}" deleted`, "success");
      setPendingDelete(null);
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  const domains = domainsQuery.data?.items ?? [];

  return (
    <main>
      <div className="page-head">
        <div className="page-title">
          <h1>Domains</h1>
          <p className="page-sub">
            DNS names this organization owns. Ownership is proven with a TXT record, and only a
            verified name can back an enabled route.
          </p>
        </div>
        <div className="page-actions">
          {canManage ? (
            <button type="button" className="btn primary" onClick={() => setCreateOpen(true)}>
              + Add domain
            </button>
          ) : null}
        </div>
      </div>

      <div className="table-toolbar">
        <div className="filters">
          <label className="flex gap-8" htmlFor="domain-status-filter">
            <span className="small muted">Status</span>
            <select
              id="domain-status-filter"
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

      {domainsQuery.isLoading ? (
        <TableSkeleton label="Loading domains" rows={6} cols={5} />
      ) : domainsQuery.isError ? (
        <ErrorBlock error={domainsQuery.error} />
      ) : domains.length === 0 ? (
        <EmptyState
          icon="🌐"
          title={statusFilter ? "No domains match the current filter" : "No domains yet"}
          hint={
            canManage && !statusFilter
              ? "Add a domain, publish its TXT record, then create routes that point at your containers."
              : undefined
          }
          action={
            canManage && !statusFilter ? (
              <button type="button" className="btn primary" onClick={() => setCreateOpen(true)}>
                + Add domain
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
                  <th scope="col">Name</th>
                  <th scope="col">Status</th>
                  <th scope="col" className="num">
                    Routes
                  </th>
                  <th scope="col">Last checked</th>
                  {canManage ? <th scope="col">Actions</th> : null}
                </tr>
              </thead>
              <tbody>
                {domains.map((domain) => (
                  <tr
                    key={domain.id}
                    className="clickable"
                    onClick={() => navigate(`/domains/${domain.id}`)}
                  >
                    <td>
                      <Link to={`/domains/${domain.id}`}>{domain.name}</Link>
                      {domain.project_name ? (
                        <span className="small muted"> · {domain.project_name}</span>
                      ) : null}
                    </td>
                    <td>
                      <StatusBadge value={domain.status} />
                      {!domain.verified && domain.last_error ? (
                        <span className="small muted" title={domain.last_error}>
                          {domain.last_error}
                        </span>
                      ) : null}
                    </td>
                    <td className="num">
                      {domain.enabled_route_count} / {domain.route_count}
                    </td>
                    <td>
                      {domain.last_checked_at ? (
                        <span title={domain.last_checked_at}>
                          {formatRelative(domain.last_checked_at)}
                        </span>
                      ) : (
                        <span className="faint">never</span>
                      )}
                    </td>
                    {canManage ? (
                      <td onClick={(event) => event.stopPropagation()}>
                        <div className="flex gap-8">
                          <button
                            type="button"
                            className="btn sm"
                            disabled={verifyMutation.isPending}
                            onClick={() => verifyMutation.mutate(domain)}
                          >
                            Verify
                          </button>
                          <button
                            type="button"
                            className="btn sm danger"
                            onClick={() => setPendingDelete(domain)}
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
          {domainsQuery.data ? (
            <Pagination page={domainsQuery.data} onPage={setOffset} />
          ) : null}
        </div>
      )}

      <CreateDomainDialog open={createOpen} onClose={() => setCreateOpen(false)} />

      <Modal
        open={pendingDelete !== null}
        title="Delete domain"
        onClose={() => setPendingDelete(null)}
      >
        <p>
          Delete <strong>{pendingDelete?.name}</strong>? A domain with enabled routes cannot be
          deleted — disable those routes first.
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
            Delete domain
          </button>
        </div>
      </Modal>
    </main>
  );
}
