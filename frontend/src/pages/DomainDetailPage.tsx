import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiDelete, apiGet, apiPost } from "../api/client";
import type { DomainDetailOut, RouteOut } from "../api/types";
import { LoadingBlock, ErrorBlock, Modal, StatusBadge } from "../components/ui";
import { useToast } from "../components/toast";
import { useAuth } from "../auth/AuthContext";
import { formatDateTime, formatRelative } from "../lib/format";

function describeError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.code === "DOMAIN_HAS_ENABLED_ROUTES") {
      return "This domain still backs enabled routes — disable them before deleting it.";
    }
    return `${err.code}: ${err.message}`;
  }
  return err instanceof Error ? err.message : "Request failed";
}

/** Clipboard write with a graceful fallback for blocked/insecure contexts. */
async function copyText(text: string): Promise<boolean> {
  try {
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      await navigator.clipboard.writeText(text);
      return true;
    }
  } catch {
    // Clipboard unavailable; the value stays selectable by hand.
  }
  return false;
}

function VerificationCard({ domain }: { domain: DomainDetailOut }) {
  const notify = useToast();
  const verification = domain.verification;
  if (!verification) {
    return (
      <section className="card">
        <h2>Ownership</h2>
        <p className="small muted">
          This name is verified. Its verification record is no longer shown — a token that
          outlived its usefulness would only be a replay primitive.
        </p>
        {domain.ns_snapshot.length ? (
          <p className="small muted">
            Authoritative servers at verification time: {domain.ns_snapshot.join(", ")}
          </p>
        ) : null}
      </section>
    );
  }
  return (
    <section className="card">
      <h2>Prove ownership</h2>
      <p className="small muted">
        Publish this TXT record in the name&apos;s DNS zone, then re-verify. The token rotates on
        every attempt, so a leaked one becomes worthless.
      </p>
      <dl className="kv">
        <dt>Record name</dt>
        <dd className="mono">{verification.record_name}</dd>
        <dt>Type</dt>
        <dd className="mono">{verification.record_type}</dd>
        <dt>Value</dt>
        <dd className="mono" style={{ wordBreak: "break-all" }}>
          {verification.record_value}
        </dd>
      </dl>
      <button
        type="button"
        className="btn sm"
        onClick={() => {
          void copyText(`${verification.record_name} ${verification.record_type} ${verification.record_value}`).then(
            (ok) => notify(ok ? "Record copied" : "Copy blocked — select the value manually", ok ? "success" : "error"),
          );
        }}
      >
        Copy record
      </button>
    </section>
  );
}

function RoutesCard({ routes }: { routes: RouteOut[] }) {
  if (routes.length === 0) {
    return (
      <section className="card">
        <h2>Routes</h2>
        <p className="small muted">No routes use this domain yet.</p>
        <Link className="btn sm" to="/routes">
          Go to routes
        </Link>
      </section>
    );
  }
  return (
    <section className="card">
      <div className="flex-between">
        <h2>Routes</h2>
        <Link className="btn sm" to="/routes">
          Manage routes
        </Link>
      </div>
      <div className="table-wrap">
        <table className="data">
          <thead>
            <tr>
              <th scope="col">Host</th>
              <th scope="col">Path</th>
              <th scope="col">Upstream</th>
              <th scope="col">State</th>
              <th scope="col">Enabled</th>
            </tr>
          </thead>
          <tbody>
            {routes.map((route) => (
              <tr key={route.id}>
                <td className="mono">{route.hostname}</td>
                <td className="mono">{route.path}</td>
                <td>
                  {route.node_name ?? "—"} · {route.port}
                </td>
                <td>
                  <StatusBadge value={route.config_state} />
                  {route.status_detail ? (
                    <span className="small muted">{route.status_detail}</span>
                  ) : null}
                </td>
                <td>{route.enabled ? "yes" : "no"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default function DomainDetailPage() {
  const { domainId } = useParams<{ domainId: string }>();
  const navigate = useNavigate();
  const { hasPermission } = useAuth();
  const canManage = hasPermission("domain.manage");
  const notify = useToast();
  const queryClient = useQueryClient();
  const [deleteOpen, setDeleteOpen] = useState(false);

  const domainQuery = useQuery({
    queryKey: ["domain", domainId],
    queryFn: ({ signal }) => apiGet<DomainDetailOut>(`/domains/${domainId}`, undefined, signal),
    enabled: Boolean(domainId),
  });

  const verifyMutation = useMutation({
    mutationFn: () => apiPost<DomainDetailOut>(`/domains/${domainId}/verify`),
    onSuccess: (updated) => {
      void queryClient.invalidateQueries({ queryKey: ["domain", domainId] });
      void queryClient.invalidateQueries({ queryKey: ["domains"] });
      notify(
        updated.verified
          ? `${updated.name} is verified`
          : `Verification for ${updated.name} is in progress`,
        "success",
      );
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  const deleteMutation = useMutation({
    mutationFn: () => apiDelete<void>(`/domains/${domainId}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["domains"] });
      notify("Domain deleted", "success");
      navigate("/domains");
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  if (domainQuery.isLoading) return <LoadingBlock label="Loading domain…" />;
  if (domainQuery.isError) return <ErrorBlock error={domainQuery.error} />;
  const domain = domainQuery.data;
  if (!domain) return null;

  return (
    <main>
      <div className="page-head">
        <div className="page-title">
          <h1 className="mono">{domain.name}</h1>
          <p className="page-sub">
            <StatusBadge value={domain.status} />{" "}
            {domain.verified_at ? `Verified ${formatRelative(domain.verified_at)}.` : ""}{" "}
            {domain.project_name ? `Project: ${domain.project_name}.` : ""}
          </p>
        </div>
        <div className="page-actions">
          {canManage ? (
            <>
              <button
                type="button"
                className="btn"
                disabled={verifyMutation.isPending}
                onClick={() => verifyMutation.mutate()}
              >
                {verifyMutation.isPending ? "Checking…" : "Re-verify"}
              </button>
              <button type="button" className="btn danger" onClick={() => setDeleteOpen(true)}>
                Delete
              </button>
            </>
          ) : null}
        </div>
      </div>

      {domain.last_error ? (
        <div className="card">
          <h2>Last verification result</h2>
          <p className="small">{domain.last_error}</p>
          <p className="small muted">
            {domain.attempt_count} attempt{domain.attempt_count === 1 ? "" : "s"}
            {domain.last_checked_at ? ` · last checked ${formatDateTime(domain.last_checked_at)}` : ""}
          </p>
        </div>
      ) : null}

      <div className="grid-2">
        <VerificationCard domain={domain} />

        <section className="card">
          <h2>Reachability</h2>
          {domain.reachability ? (
            <>
              <p className="small">
                Observed addresses:{" "}
                {domain.reachability.addresses.length
                  ? domain.reachability.addresses.join(", ")
                  : "none"}
              </p>
              <p className="small muted">
                Expected node addresses:{" "}
                {domain.reachability.expected_addresses.length
                  ? domain.reachability.expected_addresses.join(", ")
                  : "unknown"}
              </p>
              {domain.reachability.warning ? (
                <p className="small">{domain.reachability.warning}</p>
              ) : (
                <p className="small muted">
                  Reachability is a warning only: ownership and DNS pointing at the node are
                  separate facts.
                </p>
              )}
            </>
          ) : (
            <p className="small muted">
              No DNS observation yet. Reachability never gates a route — it only warns when a name
              does not yet point at its node.
            </p>
          )}
        </section>
      </div>

      <RoutesCard routes={domain.routes} />

      <Modal open={deleteOpen} title="Delete domain" onClose={() => setDeleteOpen(false)}>
        <p>
          Delete <strong>{domain.name}</strong>? Enabled routes must be disabled or deleted first;
          otherwise the API refuses with 409.
        </p>
        <div className="modal-actions">
          <button type="button" className="btn" onClick={() => setDeleteOpen(false)}>
            Cancel
          </button>
          <button
            type="button"
            className="btn danger"
            disabled={deleteMutation.isPending}
            onClick={() => deleteMutation.mutate()}
          >
            Delete domain
          </button>
        </div>
      </Modal>
    </main>
  );
}
