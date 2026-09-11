import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ApiError, apiGet, apiPost } from "../api/client";
import type { IncidentEventOut, IncidentOut } from "../api/types";
import {
  EmptyState,
  ErrorBlock,
  LoadingBlock,
  Modal,
  StatusBadge,
} from "../components/ui";
import { useToast } from "../components/toast";
import { useAuth } from "../auth/AuthContext";
import { useEventStream } from "../hooks/useEventStream";
import { formatDateTime, formatRelative } from "../lib/format";

/** The detail representation also carries actor + payload on timeline events. */
interface TimelineEvent extends IncidentEventOut {
  actor_id?: string | null;
  data?: Record<string, unknown>;
}

type IncidentDetailData = IncidentOut & {
  timeline?: TimelineEvent[];
  /** Returned by the API but absent from the shared list type. */
  detected_at?: string | null;
};

/** Badge color class for a timeline event kind (styles.css status words). */
function kindBadgeClass(kind: string): string {
  switch (kind) {
    case "OPENED":
      return "OPEN";
    case "DETECTED":
      return "WARNING";
    case "NOTIFIED":
      return "PENDING";
    case "ACKNOWLEDGED":
      return "ACKNOWLEDGED";
    case "RECOVERY_DETECTED":
      return "UP";
    case "RESOLVED":
      return "RESOLVED";
    default:
      return "NEUTRAL";
  }
}

function describeError(err: unknown): string {
  if (err instanceof ApiError) return `${err.code}: ${err.message}`;
  return "Request failed";
}

export default function IncidentDetailPage() {
  const { incidentId } = useParams<{ incidentId: string }>();
  const { hasPermission } = useAuth();
  const canAct = hasPermission("incident.action");
  const notify = useToast();
  const queryClient = useQueryClient();
  const [ackOpen, setAckOpen] = useState(false);
  const [resolveOpen, setResolveOpen] = useState(false);

  const incidentQuery = useQuery({
    queryKey: ["incident", incidentId],
    queryFn: ({ signal }) =>
      apiGet<IncidentDetailData>(`/incidents/${incidentId}`, undefined, signal),
    enabled: incidentId != null,
  });

  // Live: events for THIS incident refresh the timeline in place. Frames carry
  // the incident id as data.resource_id (see backend event_bus.publish).
  useEventStream([{ channel: "incidents" }], (frame) => {
    const resourceId = typeof frame.data?.resource_id === "string" ? frame.data.resource_id : null;
    if (resourceId && resourceId === incidentId) {
      void queryClient.invalidateQueries({ queryKey: ["incident", incidentId] });
      void queryClient.invalidateQueries({ queryKey: ["incidents"] });
    }
  });

  const ackMutation = useMutation({
    mutationFn: (note: string) =>
      apiPost<IncidentOut>(`/incidents/${incidentId}/acknowledge`, note.trim() ? { note: note.trim() } : undefined),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["incident", incidentId] });
      void queryClient.invalidateQueries({ queryKey: ["incidents"] });
      notify("Incident acknowledged", "success");
      setAckOpen(false);
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  const resolveMutation = useMutation({
    mutationFn: (resolution: string) =>
      apiPost<IncidentOut>(`/incidents/${incidentId}/resolve`, { resolution }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["incident", incidentId] });
      void queryClient.invalidateQueries({ queryKey: ["incidents"] });
      notify("Incident resolved", "success");
      setResolveOpen(false);
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  const noteMutation = useMutation({
    mutationFn: (message: string) =>
      apiPost<IncidentDetailData>(`/incidents/${incidentId}/notes`, { message }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["incident", incidentId] });
      notify("Note added", "success");
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  if (!incidentId) {
    return <ErrorBlock error={{ code: "NOT_FOUND", message: "No incident id in route" }} />;
  }

  const incident = incidentQuery.data;

  if (incidentQuery.isLoading) {
    return <LoadingBlock label="Loading incident…" />;
  }
  if (incidentQuery.isError) {
    return <ErrorBlock error={incidentQuery.error} />;
  }
  if (!incident) {
    return <EmptyState title="Incident not found" />;
  }

  const timeline = incident.timeline ?? [];
  const notifiedEvents = timeline.filter((event) => event.kind === "NOTIFIED");

  return (
    <main>
      <p className="small mb-8">
        <Link to="/incidents">← Incidents</Link>
      </p>
      <div className="page-head">
        <div className="page-title">
          <h1>
            {incident.title} <StatusBadge value={incident.status} />
          </h1>
          <p className="page-sub">
            Opened {formatDateTime(incident.opened_at)} · {incident.failure_count} consecutive
            failures
          </p>
        </div>
        {canAct ? (
          <div className="page-actions">
            {incident.status === "OPEN" ? (
              <button
                type="button"
                className="btn"
                onClick={() => setAckOpen(true)}
              >
                Acknowledge
              </button>
            ) : null}
            {incident.status !== "RESOLVED" ? (
              <button
                type="button"
                className="btn primary"
                onClick={() => setResolveOpen(true)}
              >
                Resolve
              </button>
            ) : null}
          </div>
        ) : null}
      </div>

      <div className="grid cols-2">
        <div className="card">
          <div className="card-title">
            <h2>Details</h2>
            <StatusBadge value={incident.severity} />
          </div>
          <dl className="kv">
            <dt>Monitor</dt>
            <dd>
              <Link to={`/monitors/${incident.monitor_id}`}>
                {incident.monitor_name ?? incident.monitor_id}
              </Link>
            </dd>
            <dt>Status</dt>
            <dd>
              <StatusBadge value={incident.status} />
            </dd>
            <dt>Severity</dt>
            <dd>
              <StatusBadge value={incident.severity} />
            </dd>
            <dt>Detected</dt>
            <dd>{formatDateTime(incident.detected_at ?? incident.opened_at)}</dd>
            <dt>Acknowledged</dt>
            <dd>{formatDateTime(incident.acknowledged_at)}</dd>
            <dt>Resolved</dt>
            <dd>{formatDateTime(incident.resolved_at)}</dd>
            <dt>Resolution</dt>
            <dd>
              {incident.resolution || <span className="faint">not resolved yet</span>}
            </dd>
          </dl>
        </div>

        <div className="card">
          <div className="card-title">
            <h2>Notifications sent</h2>
            <span className="badge NEUTRAL no-dot">{notifiedEvents.length}</span>
          </div>
          {notifiedEvents.length === 0 ? (
            <EmptyState
              icon="✉"
              title="No notifications recorded"
              hint="Channels subscribed to incident events are listed under Alerts."
            />
          ) : (
            <ul className="timeline">
              {notifiedEvents.map((event) => (
                <li key={event.id}>
                  <span className="badge NEUTRAL no-dot">NOTIFIED</span>
                  <p className="small mt-8">{event.message}</p>
                  <span className="tl-time">{formatDateTime(event.occurred_at)}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-title">
          <h2>Timeline</h2>
          <span className="small faint">● live</span>
        </div>
        {timeline.length === 0 ? (
          <EmptyState icon="≡" title="No events on this incident yet" />
        ) : (
          <ul className="timeline">
            {timeline.map((event) => (
              <li key={event.id}>
                <div className="flex gap-8 flex-between wrap">
                  <span className={`badge no-dot ${kindBadgeClass(event.kind)}`}>
                    {event.kind.replaceAll("_", " ")}
                  </span>
                  <span className="tl-time" title={formatDateTime(event.occurred_at)}>
                    {formatRelative(event.occurred_at)}
                  </span>
                </div>
                {event.message ? <p className="mt-8">{event.message}</p> : null}
              </li>
            ))}
          </ul>
        )}

        {canAct && incident.status !== "RESOLVED" ? (
          <form
            className="mt-16"
            onSubmit={(event) => {
              event.preventDefault();
              const form = event.currentTarget;
              const input = form.elements.namedItem("incident-note") as HTMLTextAreaElement | null;
              const message = input?.value.trim() ?? "";
              if (!message) return;
              noteMutation.mutate(message);
              form.reset();
            }}
          >
            <div className="field">
              <label htmlFor="incident-note">Add a note</label>
              <textarea
                id="incident-note"
                className="input"
                rows={2}
                maxLength={2000}
                placeholder="What you observed or tried…"
              />
            </div>
            <button type="submit" className="btn sm" disabled={noteMutation.isPending}>
              {noteMutation.isPending ? "Adding…" : "Add note"}
            </button>
          </form>
        ) : null}
      </div>

      <Modal open={ackOpen} title="Acknowledge incident" onClose={() => setAckOpen(false)}>
        <p className="mb-8">
          Claiming triage tells other operators this incident is being handled. Optionally
          add a note for the audit trail.
        </p>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            const input = event.currentTarget.elements.namedItem("ack-note") as HTMLTextAreaElement | null;
            ackMutation.mutate(input?.value ?? "");
          }}
        >
          <div className="field">
            <label htmlFor="ack-note">Note (optional)</label>
            <textarea
              id="ack-note"
              className="input"
              rows={3}
              maxLength={2000}
              placeholder="Investigating the failing checks…"
            />
          </div>
          <div className="modal-actions">
            <button type="button" className="btn" onClick={() => setAckOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn primary" disabled={ackMutation.isPending}>
              {ackMutation.isPending ? "Acknowledging…" : "Acknowledge"}
            </button>
          </div>
        </form>
      </Modal>

      <Modal open={resolveOpen} title="Resolve incident" onClose={() => setResolveOpen(false)}>
        <p className="mb-8">
          A resolution note is required — it stays on the incident timeline.
        </p>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            const input = event.currentTarget.elements.namedItem("resolve-text") as HTMLTextAreaElement | null;
            const resolution = input?.value.trim() ?? "";
            if (!resolution) return;
            resolveMutation.mutate(resolution);
          }}
        >
          <div className="field">
            <label htmlFor="resolve-text">Resolution</label>
            <textarea
              id="resolve-text"
              className="input"
              rows={3}
              maxLength={4000}
              placeholder="Recovery confirmed after redeploy; checks passing for 5 minutes."
              required
            />
          </div>
          <div className="modal-actions">
            <button type="button" className="btn" onClick={() => setResolveOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn primary" disabled={resolveMutation.isPending}>
              {resolveMutation.isPending ? "Resolving…" : "Resolve incident"}
            </button>
          </div>
        </form>
      </Modal>
    </main>
  );
}
