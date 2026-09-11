/**
 * /deployments/:deploymentId — deployment banner, live pipeline steps and log
 * stream. Live log lines arrive over the `deployment-logs` WebSocket channel;
 * step statuses poll while the run is active.
 */

import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiGet, apiPost } from "../api/client";
import type { CursorPage, DeploymentStepOut } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { EmptyState, ErrorBlock, LoadingBlock, Modal, StatusBadge } from "../components/ui";
import { useToast } from "../components/toast";
import { useEventStream } from "../hooks/useEventStream";
import { formatDateTime, formatDurationMs, formatRelative } from "../lib/format";

interface DeploymentDetailRow {
  id: string;
  number: number;
  version: string;
  git_commit: string;
  notes: string;
  status: string;
  trigger: string;
  is_rollback: boolean;
  rollback_of_id?: string | null;
  triggered_by_email?: string | null;
  failure_reason: string;
  cancel_requested: boolean;
  queued_at: string | null;
  started_at: string | null;
  finished_at: string | null;
  duration_ms: number | null;
  application?: { id: string; name: string; slug?: string } | null;
  environment?: { id: string; name: string; slug?: string } | null;
  steps?: DeploymentStepOut[];
  steps_total?: number;
  steps_success?: number;
  steps_failed?: number;
}

interface DeploymentLogRow {
  id: number;
  level: string;
  message: string;
  ts: string;
  step_idx?: number | null;
}

const ACTIVE_STATUSES = new Set(["QUEUED", "RUNNING"]);

function formatLogTime(ts: string): string {
  const date = new Date(ts);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleTimeString(undefined, { hour12: false });
}

function LogLines({ lines }: { lines: DeploymentLogRow[] }) {
  return (
    <>
      {lines.map((line) => (
        <div key={line.id} className={`log-line level-${line.level}`}>
          <span className="ts">{formatLogTime(line.ts)}</span>
          <span className="msg">{line.message}</span>
        </div>
      ))}
    </>
  );
}

/** One pipeline step: status, timing and its accumulated + live output. */
function StepCard({ step, liveLines }: { step: DeploymentStepOut; liveLines: DeploymentLogRow[] }) {
  const persistedLines = step.output ? step.output.split("\n") : [];
  const expandByDefault = step.status !== "PENDING";
  return (
    <section className="card" aria-label={`Step ${step.idx + 1}: ${step.name}`}>
      <div className="flex flex-between gap-8 wrap">
        <span>
          <span className="mono faint">#{step.idx + 1}</span> <strong>{step.name}</strong>
          {step.retry_count > 0 ? (
            <span className="faint small"> · {step.retry_count} retries</span>
          ) : null}
        </span>
        <StatusBadge value={step.status} />
      </div>
      <div className="small faint mt-8">
        {step.started_at ? `started ${formatRelative(step.started_at)}` : "not started"}
        {step.finished_at ? ` · finished ${formatRelative(step.finished_at)}` : ""}
      </div>
      {step.error ? (
        <p className="form-error" role="alert">
          {step.error}
        </p>
      ) : null}
      {(persistedLines.length > 0 || liveLines.length > 0) && expandByDefault ? (
        <div className="log-viewer mt-8" data-testid={`step-output-${step.idx}`}>
          {persistedLines.map((line, index) => (
            <div key={`p${index}`} className="log-line">
              <span className="msg">{line}</span>
            </div>
          ))}
          <LogLines lines={liveLines} />
        </div>
      ) : null}
    </section>
  );
}

export default function DeploymentDetailPage() {
  const { deploymentId = "" } = useParams();
  const navigate = useNavigate();
  const notify = useToast();
  const qc = useQueryClient();
  const { hasPermission } = useAuth();

  const [confirmAction, setConfirmAction] = useState<"cancel" | "rollback" | null>(null);
  const [liveLines, setLiveLines] = useState<DeploymentLogRow[]>([]);
  const liveSeq = useRef(0);
  const logBoxRef = useRef<HTMLDivElement | null>(null);

  const deploymentQ = useQuery({
    queryKey: ["deployment", deploymentId],
    queryFn: ({ signal }) =>
      apiGet<DeploymentDetailRow>(`/deployments/${deploymentId}`, undefined, signal),
    enabled: deploymentId !== "",
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return ACTIVE_STATUSES.has(status ?? "") ? 2500 : false;
    },
  });

  const logsQ = useQuery({
    queryKey: ["deployment-logs", deploymentId],
    queryFn: ({ signal }) =>
      apiGet<CursorPage<DeploymentLogRow>>(
        `/deployments/${deploymentId}/logs`,
        { limit: 100 },
        signal,
      ),
    enabled: deploymentId !== "",
  });

  useEffect(() => {
    setLiveLines([]);
  }, [deploymentId]);

  // Live log frames: {deployment_id, step_idx, step, line, level, ts}.
  useEventStream(
    deploymentId ? [{ channel: "deployment-logs", params: { deployment_id: deploymentId } }] : [],
    (frame) => {
      const data = frame.data ?? {};
      const line = typeof data.line === "string" ? data.line : "";
      if (!line) return;
      liveSeq.current += 1;
      setLiveLines((current) => [
        ...current.slice(-400),
        {
          id: -liveSeq.current,
          level: typeof data.level === "string" ? data.level : "INFO",
          message: line,
          ts: typeof data.ts === "string" ? data.ts : new Date().toISOString(),
          step_idx: typeof data.step_idx === "number" ? data.step_idx : null,
        },
      ]);
    },
  );

  const deployment = deploymentQ.data;
  const steps = useMemo(() => deployment?.steps ?? [], [deployment]);
  const isActive = deployment !== undefined && ACTIVE_STATUSES.has(deployment.status);

  const persistedLogs = useMemo(() => logsQ.data?.items ?? [], [logsQ.data]);
  const allLogs = useMemo(() => [...persistedLogs, ...liveLines], [persistedLogs, liveLines]);
  const visibleLogs = useMemo(() => allLogs.slice(-400), [allLogs]);

  useEffect(() => {
    const box = logBoxRef.current;
    if (box) box.scrollTop = box.scrollHeight;
  }, [allLogs.length]);

  function invalidate() {
    void qc.invalidateQueries({ queryKey: ["deployment", deploymentId] });
    void qc.invalidateQueries({ queryKey: ["deployments"] });
  }

  const cancelMutation = useMutation({
    mutationFn: () => apiPost<DeploymentDetailRow>(`/deployments/${deploymentId}/cancel`),
    onSuccess: (updated) => {
      notify(
        updated.status === "CANCELLED"
          ? `Deployment #${updated.number} cancelled`
          : `Cancellation requested for deployment #${updated.number}`,
        "success",
      );
      setConfirmAction(null);
      invalidate();
    },
    onError: (err) => {
      notify(err instanceof ApiError ? `${err.code}: ${err.message}` : "Failed to cancel", "error");
    },
  });

  const rollbackMutation = useMutation({
    // Rollback queues a NEW deployment re-deploying the last good version.
    mutationFn: () => apiPost<DeploymentDetailRow>(`/deployments/${deploymentId}/rollback`),
    onSuccess: (created) => {
      notify(
        `Rollback queued as a new deployment (#${created.number}) — opening it…`,
        "success",
      );
      setConfirmAction(null);
      invalidate();
      navigate(`/deployments/${created.id}`);
    },
    onError: (err) => {
      notify(err instanceof ApiError ? `${err.code}: ${err.message}` : "Rollback failed", "error");
    },
  });

  if (deploymentId === "") {
    return (
      <main className="content">
        <EmptyState title="No deployment selected" />
      </main>
    );
  }

  if (deploymentQ.isPending) {
    return (
      <main className="content">
        <LoadingBlock label="Loading deployment…" />
      </main>
    );
  }

  if (deploymentQ.isError) {
    const notFound = deploymentQ.error instanceof ApiError && deploymentQ.error.status === 404;
    return (
      <main className="content">
        {notFound ? (
          <EmptyState
            icon="⇪"
            title="Deployment not found"
            hint="It may have been removed, or you do not have access to it."
          />
        ) : (
          <ErrorBlock error={deploymentQ.error} />
        )}
        <p className="mt-16">
          <Link to="/deployments" className="btn sm">
            ← Back to deployments
          </Link>
        </p>
      </main>
    );
  }

  if (!deployment) return null;

  const stepsTotal = deployment.steps_total ?? steps.length;
  const stepsDone = deployment.steps_success ?? 0;
  const progressPct = stepsTotal > 0 ? Math.round((stepsDone / stepsTotal) * 100) : 0;
  const progressClass =
    deployment.status === "FAILED" || deployment.status === "CANCELLED"
      ? "progress-fill err"
      : "progress-fill ok";

  return (
    <main className="content" aria-label={`Deployment ${deployment.number}`}>
      <div className="page-head">
        <div className="page-title">
          <h1>
            Deployment #{deployment.number} <StatusBadge value={deployment.status} />
          </h1>
          <p className="page-sub">
            <span className="mono">{deployment.version}</span>
            {deployment.git_commit ? (
              <span className="faint"> · commit {deployment.git_commit.slice(0, 7)}</span>
            ) : null}
            {deployment.is_rollback ? " · rollback" : ""}
            {deployment.application ? ` · ${deployment.application.name}` : ""}
            {deployment.environment ? ` → ${deployment.environment.name}` : ""}
          </p>
        </div>
        <div className="page-actions">
          {isActive && hasPermission("deployment.cancel") ? (
            <button
              type="button"
              className="btn danger"
              onClick={() => setConfirmAction("cancel")}
              aria-label={`Cancel deployment ${deployment.number}`}
            >
              Cancel
            </button>
          ) : null}
          {deployment.status === "SUCCESS" && hasPermission("deployment.rollback") ? (
            <button
              type="button"
              className="btn"
              onClick={() => setConfirmAction("rollback")}
              aria-label={`Roll back deployment ${deployment.number}`}
            >
              Roll back
            </button>
          ) : null}
          <Link to="/deployments" className="btn ghost sm">
            ← All deployments
          </Link>
        </div>
      </div>

      {/* Final / current status banner */}
      <section className="card" aria-label="Deployment summary">
        <div className="flex flex-between gap-12 wrap">
          <div>
            <div className="stat-label">Status</div>
            <div className="stat-value">
              <StatusBadge value={deployment.status} />
            </div>
            {deployment.failure_reason ? (
              <p className="form-error" role="alert">
                {deployment.failure_reason}
              </p>
            ) : null}
            {deployment.cancel_requested && isActive ? (
              <p className="small" style={{ color: "var(--warn)" }}>
                Cancellation requested — stopping soon.
              </p>
            ) : null}
            {deployment.notes ? <p className="small muted mt-8">{deployment.notes}</p> : null}
          </div>
          <div className="stat-card">
            <div className="stat-label">Duration</div>
            <div className="stat-value">{formatDurationMs(deployment.duration_ms)}</div>
            <div className="stat-foot">
              {deployment.started_at
                ? `started ${formatDateTime(deployment.started_at)}`
                : `queued ${formatDateTime(deployment.queued_at)}`}
              {deployment.finished_at ? ` · finished ${formatDateTime(deployment.finished_at)}` : ""}
            </div>
          </div>
        </div>
        <dl className="kv mt-16">
          <dt>Trigger</dt>
          <dd>
            {deployment.trigger}
            {deployment.triggered_by_email ? ` by ${deployment.triggered_by_email}` : ""}
            {deployment.is_rollback ? " (rollback)" : ""}
          </dd>
          <dt>Application</dt>
          <dd>{deployment.application?.name ?? "—"}</dd>
          <dt>Environment</dt>
          <dd>{deployment.environment?.name ?? "—"}</dd>
          <dt>Created</dt>
          <dd>{formatDateTime(deployment.queued_at ?? null)}</dd>
        </dl>
        {stepsTotal > 0 ? (
          <div className="mt-16">
            <div className="progress-track" role="progressbar" aria-label="Step progress" aria-valuenow={progressPct} aria-valuemin={0} aria-valuemax={100}>
              <div className={progressClass} style={{ width: `${progressPct}%` }} />
            </div>
            <div className="stat-foot mt-8">
              {stepsDone}/{stepsTotal} steps succeeded
            </div>
          </div>
        ) : null}
      </section>

      <h2 className="mt-16">Pipeline steps</h2>
      {steps.length === 0 ? (
        <EmptyState title="No steps recorded" hint="Steps appear here once the run starts." />
      ) : (
        <div className="mt-8">
          {steps.map((step) => (
            <StepCard
              key={step.idx}
              step={step}
              liveLines={liveLines.filter((line) => line.step_idx === step.idx)}
            />
          ))}
        </div>
      )}

      <section className="card mt-16" aria-label="Deployment logs">
        <div className="card-title">
          <h2>Logs</h2>
          {isActive ? <span className="badge RUNNING">LIVE</span> : null}
        </div>
        {logsQ.isError ? (
          <ErrorBlock error={logsQ.error} />
        ) : visibleLogs.length === 0 ? (
          <p className="faint small">No log output yet.</p>
        ) : (
          <div className="log-viewer" ref={logBoxRef} data-testid="deployment-log-console">
            <LogLines lines={visibleLogs} />
          </div>
        )}
      </section>

      <Modal
        open={confirmAction === "cancel"}
        title={`Cancel deployment #${deployment.number}?`}
        onClose={() => setConfirmAction(null)}
      >
        <p>
          {deployment.status === "QUEUED"
            ? "The queued deployment will be cancelled immediately."
            : "The running deployment will be flagged to stop at the next safe point."}
        </p>
        <div className="modal-actions">
          <button type="button" className="btn ghost" onClick={() => setConfirmAction(null)}>
            Keep running
          </button>
          <button
            type="button"
            className="btn danger"
            onClick={() => cancelMutation.mutate()}
            disabled={cancelMutation.isPending}
          >
            {cancelMutation.isPending ? "Cancelling…" : "Cancel deployment"}
          </button>
        </div>
      </Modal>

      <Modal
        open={confirmAction === "rollback"}
        title={`Roll back deployment #${deployment.number}?`}
        onClose={() => setConfirmAction(null)}
      >
        <p>
          Rolling back creates a <strong>new deployment</strong> that redeploys the last known-good
          version of {deployment.application?.name ?? "this application"} to{" "}
          {deployment.environment?.name ?? "its environment"}. This deployment stays untouched in
          the history.
        </p>
        <div className="modal-actions">
          <button type="button" className="btn ghost" onClick={() => setConfirmAction(null)}>
            Do nothing
          </button>
          <button
            type="button"
            className="btn primary"
            onClick={() => rollbackMutation.mutate()}
            disabled={rollbackMutation.isPending}
          >
            {rollbackMutation.isPending ? "Queueing rollback…" : "Queue rollback deployment"}
          </button>
        </div>
      </Modal>
    </main>
  );
}
