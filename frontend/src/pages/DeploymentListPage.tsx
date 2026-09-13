/**
 * /deployments — paginated deployment history with status filter and a
 * trigger-deployment dialog (POST /deployments/applications/{id}/deployments).
 */

import { useMemo, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ApiError, apiGet, apiPost } from "../api/client";
import type { DeploymentOut, EnvironmentOut, Page, ProjectOut } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { Pagination } from "../components/Pagination";
import { EmptyState, ErrorBlock, Modal, StatusBadge } from "../components/ui";
import { TableSkeleton } from "../components/Skeleton";
import { useToast } from "../components/toast";
import { formatDurationMs, formatRelative, truncate } from "../lib/format";

type DeploymentRow = DeploymentOut & {
  application?: { id: string; name: string; slug?: string } | null;
  environment?: { id: string; name: string; slug?: string } | null;
  steps_total?: number;
  steps_success?: number;
  steps_failed?: number;
  steps_running?: number;
};

const DEPLOYMENT_STATUSES = [
  "QUEUED",
  "RUNNING",
  "SUCCESS",
  "FAILED",
  "CANCELLED",
  "ROLLBACK",
] as const;

const PAGE_SIZE = 20;
const VERSION_PATTERN = "^[A-Za-z0-9._/-]+$";

function errorMessage(err: unknown): string {
  if (err instanceof ApiError) return `${err.code}: ${err.message}`;
  if (err instanceof Error) return err.message;
  return "Request failed";
}

interface AppOption {
  id: string;
  name: string;
  projectName: string;
}

/** Dialog that queues a new deployment for an application/environment pair. */
function TriggerDeploymentModal({
  open,
  onClose,
  onQueued,
}: {
  open: boolean;
  onClose: () => void;
  onQueued: (deploymentId: string) => void;
}) {
  const notify = useToast();
  const [applicationId, setApplicationId] = useState("");
  const [environmentId, setEnvironmentId] = useState("");
  const [version, setVersion] = useState("");
  const [gitCommit, setGitCommit] = useState("");
  const [notes, setNotes] = useState("");

  const projectsQ = useQuery({
    queryKey: ["projects", { scope: "trigger-options", limit: 100, offset: 0 }],
    queryFn: ({ signal }) => apiGet<Page<ProjectOut>>("/projects", { limit: 100, offset: 0 }, signal),
    enabled: open,
  });

  const applications = useMemo<AppOption[]>(
    () =>
      (projectsQ.data?.items ?? []).flatMap((project) =>
        (project.applications ?? []).map((app) => ({
          id: app.id,
          name: app.name,
          projectName: project.name,
        })),
      ),
    [projectsQ.data],
  );

  const environmentsQ = useQuery({
    queryKey: ["environments", applicationId],
    queryFn: ({ signal }) =>
      apiGet<Page<EnvironmentOut>>(
        `/projects/applications/${applicationId}/environments`,
        { limit: 100 },
        signal,
      ),
    enabled: open && applicationId !== "",
  });

  const triggerMutation = useMutation({
    mutationFn: () =>
      apiPost<DeploymentRow>(`/deployments/applications/${applicationId}/deployments`, {
        environment_id: environmentId,
        version,
        git_commit: gitCommit,
        notes,
      }),
    onSuccess: (created) => {
      notify(`Deployment #${created.number} queued`, "success");
      onClose();
      onQueued(created.id);
    },
    onError: (err) => notify(errorMessage(err), "error"),
  });

  const canSubmit =
    applicationId !== "" && environmentId !== "" && version.trim() !== "" && !triggerMutation.isPending;

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!canSubmit) return;
    triggerMutation.mutate();
  }

  return (
    <Modal open={open} title="Trigger deployment" onClose={onClose}>
      <form onSubmit={handleSubmit} noValidate>
        <div className="field">
          <label htmlFor="trigger-application">Application</label>
          <select
            id="trigger-application"
            className="input"
            value={applicationId}
            onChange={(event) => {
              setApplicationId(event.target.value);
              setEnvironmentId("");
            }}
            required
          >
            <option value="">Select an application…</option>
            {applications.map((app) => (
              <option key={app.id} value={app.id}>
                {app.name} — {app.projectName}
              </option>
            ))}
          </select>
          {projectsQ.isPending ? <span className="faint small">Loading applications…</span> : null}
        </div>

        <div className="field">
          <label htmlFor="trigger-environment">Environment</label>
          <select
            id="trigger-environment"
            className="input"
            value={environmentId}
            onChange={(event) => setEnvironmentId(event.target.value)}
            required
            disabled={applicationId === ""}
          >
            <option value="">Select an environment…</option>
            {(environmentsQ.data?.items ?? []).map((env) => (
              <option key={env.id} value={env.id}>
                {env.name}
              </option>
            ))}
          </select>
        </div>

        <div className="field-row">
          <div className="field">
            <label htmlFor="trigger-version">Version</label>
            <input
              id="trigger-version"
              className="input"
              value={version}
              onChange={(event) => setVersion(event.target.value)}
              placeholder="1.4.2"
              pattern={VERSION_PATTERN}
              title="Letters, digits, dot, underscore, slash and dash only"
              required
            />
          </div>
          <div className="field">
            <label htmlFor="trigger-commit">Git commit (optional)</label>
            <input
              id="trigger-commit"
              className="input"
              value={gitCommit}
              onChange={(event) => setGitCommit(event.target.value)}
              placeholder="a1b2c3d"
            />
          </div>
        </div>

        <div className="field">
          <label htmlFor="trigger-notes">Notes (optional)</label>
          <textarea
            id="trigger-notes"
            className="input"
            rows={3}
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
          />
        </div>

        {triggerMutation.isError ? (
          <p className="form-error" role="alert">
            {errorMessage(triggerMutation.error)}
          </p>
        ) : null}

        <div className="modal-actions">
          <button type="button" className="btn ghost" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn primary" disabled={!canSubmit}>
            {triggerMutation.isPending ? "Queueing…" : "Queue deployment"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export default function DeploymentListPage() {
  const { hasPermission } = useAuth();
  const navigate = useNavigate();
  const [offset, setOffset] = useState(0);
  const [statusFilter, setStatusFilter] = useState("");
  const [qInput, setQInput] = useState("");
  const [q, setQ] = useState("");
  const [triggerOpen, setTriggerOpen] = useState(false);

  const deploymentsQ = useQuery({
    queryKey: ["deployments", { offset, status: statusFilter, q }],
    queryFn: ({ signal }) =>
      apiGet<Page<DeploymentRow>>(
        "/deployments",
        {
          limit: PAGE_SIZE,
          offset,
          status: statusFilter || undefined,
          q: q || undefined,
        },
        signal,
      ),
  });

  const items = deploymentsQ.data?.items ?? [];

  function applyFilters(nextStatus: string, nextQ: string) {
    setOffset(0);
    setStatusFilter(nextStatus);
    setQ(nextQ);
  }

  return (
    <main className="content" aria-label="Deployments">
      <div className="page-head">
        <div className="page-title">
          <h1>Deployments</h1>
          <p className="page-sub">
            Release history across every application and environment
            {deploymentsQ.data ? ` · ${deploymentsQ.data.total} total` : ""}
          </p>
        </div>
        <div className="page-actions">
          {hasPermission("deployment.create") ? (
            <button type="button" className="btn primary" onClick={() => setTriggerOpen(true)}>
              Trigger deployment
            </button>
          ) : null}
        </div>
      </div>

      <div className="table-toolbar">
        <div className="filters">
          <label className="faint small" htmlFor="deployment-status-filter">
            Status
          </label>
          <select
            id="deployment-status-filter"
            className="input"
            aria-label="Filter by status"
            value={statusFilter}
            onChange={(event) => applyFilters(event.target.value, q)}
          >
            <option value="">All statuses</option>
            {DEPLOYMENT_STATUSES.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
        </div>
        <form
          role="search"
          onSubmit={(event) => {
            event.preventDefault();
            applyFilters(statusFilter, qInput.trim());
          }}
        >
          <input
            className="input search-input"
            type="search"
            aria-label="Search deployments by version or notes"
            placeholder="Search version or notes…"
            value={qInput}
            onChange={(event) => setQInput(event.target.value)}
          />
        </form>
      </div>

      {deploymentsQ.isPending ? (
        <TableSkeleton label="Loading deployments" rows={8} cols={7} />
      ) : deploymentsQ.isError ? (
        <ErrorBlock error={deploymentsQ.error} />
      ) : items.length === 0 ? (
        <EmptyState
          icon="⇪"
          title="No deployments found"
          hint={
            q || statusFilter
              ? "No releases match the current filters."
              : "Trigger a deployment to see its history here."
          }
        />
      ) : (
        <div className="card">
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Application</th>
                  <th>Environment</th>
                  <th>Version</th>
                  <th>Status</th>
                  <th>Steps</th>
                  <th>Triggered by</th>
                  <th>Timing</th>
                </tr>
              </thead>
              <tbody>
                {items.map((deployment) => (
                  <tr
                    key={deployment.id}
                    className="clickable"
                    onClick={() => navigate(`/deployments/${deployment.id}`)}
                  >
                    <td className="num">
                      <Link to={`/deployments/${deployment.id}`} onClick={(e) => e.stopPropagation()}>
                        {deployment.number}
                      </Link>
                    </td>
                    <td>
                      {deployment.is_rollback ? <span title="Rollback">↩ </span> : null}
                      {deployment.application?.name ?? "—"}
                    </td>
                    <td>{deployment.environment?.name ?? "—"}</td>
                    <td className="mono">
                      {truncate(deployment.version, 28)}
                      {deployment.git_commit ? (
                        <span className="faint"> · {deployment.git_commit.slice(0, 7)}</span>
                      ) : null}
                    </td>
                    <td>
                      <StatusBadge value={deployment.status} />
                    </td>
                    <td className="small faint">
                      {deployment.steps_total
                        ? `${deployment.steps_success ?? 0}/${deployment.steps_total} ok`
                        : "—"}
                    </td>
                    <td className="small">
                      {deployment.triggered_by_email ?? deployment.trigger}
                      {deployment.trigger !== "MANUAL" ? (
                        <span className="faint"> · {deployment.trigger}</span>
                      ) : null}
                    </td>
                    <td className="small">
                      {formatRelative(deployment.created_at)}
                      {deployment.duration_ms != null ? (
                        <span className="faint"> · {formatDurationMs(deployment.duration_ms)}</span>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {deploymentsQ.data ? <Pagination page={deploymentsQ.data} onPage={setOffset} /> : null}
        </div>
      )}

      {hasPermission("deployment.create") ? (
        <TriggerDeploymentModal
          open={triggerOpen}
          onClose={() => setTriggerOpen(false)}
          onQueued={(deploymentId) => {
            void navigate(`/deployments/${deploymentId}`);
          }}
        />
      ) : null}
    </main>
  );
}
