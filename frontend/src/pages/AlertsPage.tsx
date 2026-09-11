import { useState } from "react";
import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { ApiError, apiDelete, apiGet, apiPatch, apiPost } from "../api/client";
import type { AlertOut, ChannelOut, CursorPage, DeliveryOut, Page } from "../api/types";
import { Pagination } from "../components/Pagination";
import {
  EmptyState,
  ErrorBlock,
  LoadingBlock,
  Modal,
  StatusBadge,
} from "../components/ui";
import { useToast } from "../components/toast";
import { useAuth } from "../auth/AuthContext";
import { formatDateTime, formatRelative, truncate } from "../lib/format";

/** GET /alerts/unread-count — tiny payload, not in the shared types. */
interface UnreadCount {
  count: number;
}

/** POST /notification-channels/{id}/test response. */
interface TestNotificationResult {
  status: DeliveryOut["status"];
  error: string | null;
}

const CHANNEL_PAGE_SIZE = 50;
const DELIVERY_PAGE_SIZE = 15;

/** Human-readable rendering of an API failure, SSRF rejections in particular. */
function describeError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.code === "SSRF_BLOCKED") {
      return `Webhook URL blocked by the SSRF guard: ${err.message} Pick a host that is reachable from the NexusOps server network.`;
    }
    return `${err.code}: ${err.message}`;
  }
  return "Request failed";
}

function parseEventList(raw: string): string[] {
  return raw
    .split(",")
    .map((token) => token.trim().toUpperCase())
    .filter(Boolean);
}

function parseRecipients(raw: string): string[] {
  return raw
    .split(/[\n,]/)
    .map((token) => token.trim())
    .filter(Boolean);
}

/** Comma-separated events → chips; empty list means "subscribed to all events". */
function EventChips({ events }: { events: string[] }) {
  if (events.length === 0) return <span className="faint small">All events</span>;
  return (
    <span className="wrap flex gap-8">
      {events.map((event) => (
        <span key={event} className="tag-chip">
          {event}
        </span>
      ))}
    </span>
  );
}

function ChannelDialog({
  open,
  channel,
  onClose,
}: {
  open: boolean;
  channel: ChannelOut | null; // null → create mode
  onClose: () => void;
}) {
  const notify = useToast();
  const queryClient = useQueryClient();
  const [name, setName] = useState(channel?.name ?? "");
  const [type, setType] = useState<ChannelOut["type"]>(channel?.type ?? "WEBHOOK");
  const [url, setUrl] = useState("");
  const [recipients, setRecipients] = useState("");
  const [events, setEvents] = useState(channel?.events.join(", ") ?? "");
  const [formError, setFormError] = useState("");

  const isEdit = channel != null;

  const saveMutation = useMutation({
    mutationFn: () => {
      const eventList = parseEventList(events);
      if (isEdit && channel) {
        const body: Record<string, unknown> = {
          name: name.trim(),
          enabled: channel.enabled,
          events: eventList,
        };
        if (type === "WEBHOOK" && url.trim()) {
          body.config = { url: url.trim() };
        }
        if (type === "EMAIL" && recipients.trim()) {
          body.config = { recipients: parseRecipients(recipients) };
        }
        return apiPatch<ChannelOut>(`/notification-channels/${channel.id}`, body);
      }
      const body: Record<string, unknown> = {
        name: name.trim(),
        type,
        events: eventList,
        enabled: true,
        config:
          type === "WEBHOOK" ? { url: url.trim() } : { recipients: parseRecipients(recipients) },
      };
      return apiPost<ChannelOut>("/notification-channels", body);
    },
    onSuccess: (saved) => {
      void queryClient.invalidateQueries({ queryKey: ["notification-channels"] });
      notify(`Channel "${saved.name}" ${isEdit ? "updated" : "created"}`, "success");
      onClose();
    },
    onError: (err) => {
      setFormError(describeError(err));
      notify(describeError(err), "error");
    },
  });

  const submit = () => {
    if (!name.trim()) {
      setFormError("Name is required.");
      return;
    }
    if (type === "WEBHOOK" && !url.trim()) {
      setFormError("A webhook URL is required.");
      return;
    }
    if (type === "EMAIL" && parseRecipients(recipients).length === 0) {
      setFormError("At least one recipient email is required.");
      return;
    }
    setFormError("");
    saveMutation.mutate();
  };

  return (
    <Modal
      open={open}
      title={isEdit ? `Edit channel ${channel?.name ?? ""}` : "New notification channel"}
      onClose={onClose}
    >
      <form
        onSubmit={(event) => {
          event.preventDefault();
          submit();
        }}
      >
        <div className="field">
          <label htmlFor="channel-name">Name</label>
          <input
            id="channel-name"
            className="input"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Ops webhook"
          />
        </div>
        {!isEdit ? (
          <div className="field">
            <label htmlFor="channel-type">Type</label>
            <select
              id="channel-type"
              className="input"
              value={type}
              onChange={(event) => setType(event.target.value as ChannelOut["type"])}
            >
              <option value="WEBHOOK">WEBHOOK</option>
              <option value="EMAIL">EMAIL</option>
            </select>
          </div>
        ) : null}
        {type === "WEBHOOK" ? (
          <div className="field">
            <label htmlFor="channel-url">Webhook URL</label>
            <input
              id="channel-url"
              className="input"
              value={url}
              onChange={(event) => setUrl(event.target.value)}
              placeholder={
                isEdit && channel
                  ? `Current target: ${channel.display_target || "hidden"} — leave empty to keep`
                  : "https://hooks.example.com/nexusops"
              }
            />
            <span className="small faint">
              Stored encrypted and never echoed back — only a masked target is shown.
            </span>
          </div>
        ) : (
          <div className="field">
            <label htmlFor="channel-recipients">Recipients</label>
            <textarea
              id="channel-recipients"
              className="input"
              rows={2}
              value={recipients}
              onChange={(event) => setRecipients(event.target.value)}
              placeholder="ops@example.com, oncall@example.com"
            />
          </div>
        )}
        <div className="field">
          <label htmlFor="channel-events">Event subscriptions</label>
          <input
            id="channel-events"
            className="input"
            value={events}
            onChange={(event) => setEvents(event.target.value)}
            placeholder="INCIDENT_OPENED, MONITOR_DOWN"
          />
          <span className="small faint">
            Comma-separated event types (e.g. INCIDENT_OPENED, MONITOR_DOWN). Leave empty to
            subscribe to all events.
          </span>
        </div>
        {formError ? <div className="form-error">{formError}</div> : null}
        <div className="modal-actions">
          <button type="button" className="btn" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="btn primary" disabled={saveMutation.isPending}>
            {saveMutation.isPending ? "Saving…" : isEdit ? "Save changes" : "Create channel"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function DeleteChannelDialog({
  open,
  channel,
  onClose,
}: {
  open: boolean;
  channel: ChannelOut;
  onClose: () => void;
}) {
  const notify = useToast();
  const queryClient = useQueryClient();
  const deleteMutation = useMutation({
    mutationFn: () => apiDelete<void>(`/notification-channels/${channel.id}`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["notification-channels"] });
      void queryClient.invalidateQueries({ queryKey: ["deliveries"] });
      notify(`Channel "${channel.name}" deleted`, "success");
      onClose();
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  return (
    <Modal open={open} title="Delete channel" onClose={onClose}>
      <p>
        Delete the <strong>{channel.type}</strong> channel <strong>{channel.name}</strong>?
        Pending deliveries to it will be dropped.
      </p>
      <div className="modal-actions">
        <button type="button" className="btn" onClick={onClose}>
          Cancel
        </button>
        <button
          type="button"
          className="btn danger"
          disabled={deleteMutation.isPending}
          onClick={() => deleteMutation.mutate()}
        >
          {deleteMutation.isPending ? "Deleting…" : "Delete channel"}
        </button>
      </div>
    </Modal>
  );
}

export default function AlertsPage() {
  const { hasPermission } = useAuth();
  const canReadChannels = hasPermission("channel.read");
  const canManageChannels = hasPermission("channel.manage");
  const notify = useToast();
  const queryClient = useQueryClient();

  const [alertOffset, setAlertOffset] = useState(0);
  const [channelDialogOpen, setChannelDialogOpen] = useState(false);
  const [editingChannel, setEditingChannel] = useState<ChannelOut | null>(null);
  const [deletingChannel, setDeletingChannel] = useState<ChannelOut | null>(null);

  // --- Alert inbox ---------------------------------------------------------
  const alertsQuery = useQuery({
    queryKey: ["alerts", { limit: 15, offset: alertOffset }],
    queryFn: ({ signal }) =>
      apiGet<Page<AlertOut>>("/alerts", { limit: 15, offset: alertOffset }, signal),
  });

  const unreadQuery = useQuery({
    queryKey: ["alerts", "unread-count"],
    queryFn: ({ signal }) => apiGet<UnreadCount>("/alerts/unread-count", undefined, signal),
  });

  const markReadMutation = useMutation({
    mutationFn: (alert: AlertOut) => apiPost<AlertOut>(`/alerts/${alert.id}/read`),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["alerts"] });
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  const markAllReadMutation = useMutation({
    mutationFn: () => apiPost<UnreadCount>("/alerts/read-all"),
    onSuccess: (result) => {
      void queryClient.invalidateQueries({ queryKey: ["alerts"] });
      notify(`${result.count} alert${result.count === 1 ? "" : "s"} marked read`, "success");
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  // --- Notification channels ----------------------------------------------
  const channelsQuery = useQuery({
    queryKey: ["notification-channels"],
    queryFn: ({ signal }) =>
      apiGet<Page<ChannelOut>>("/notification-channels", { limit: CHANNEL_PAGE_SIZE }, signal),
    enabled: canReadChannels,
  });

  const toggleChannelMutation = useMutation({
    mutationFn: (channel: ChannelOut) =>
      apiPatch<ChannelOut>(`/notification-channels/${channel.id}`, { enabled: !channel.enabled }),
    onSuccess: (updated) => {
      void queryClient.invalidateQueries({ queryKey: ["notification-channels"] });
      notify(`Channel "${updated.name}" ${updated.enabled ? "enabled" : "disabled"}`, "success");
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  const testChannelMutation = useMutation({
    mutationFn: (channel: ChannelOut) =>
      apiPost<TestNotificationResult>(`/notification-channels/${channel.id}/test`),
    onSuccess: (result) => {
      void queryClient.invalidateQueries({ queryKey: ["deliveries"] });
      if (result.status === "SENT") {
        notify("Test notification sent", "success");
      } else {
        notify(`Test notification ${result.status.toLowerCase()}${result.error ? `: ${result.error}` : ""}`, "error");
      }
    },
    onError: (err) => notify(describeError(err), "error"),
  });

  // --- Delivery log --------------------------------------------------------
  const deliveriesQuery = useInfiniteQuery({
    queryKey: ["deliveries"],
    queryFn: ({ pageParam, signal }) =>
      apiGet<CursorPage<DeliveryOut>>("/notification-channels/deliveries", {
        limit: DELIVERY_PAGE_SIZE,
        cursor: pageParam ?? undefined,
      }, signal),
    initialPageParam: null as string | null,
    getNextPageParam: (last) => (last.has_more ? last.next_cursor : null),
    enabled: canReadChannels,
  });

  const alerts = alertsQuery.data?.items ?? [];
  const channels = channelsQuery.data?.items ?? [];
  const deliveries = deliveriesQuery.data?.pages.flatMap((page) => page.items) ?? [];

  return (
    <main>
      <div className="page-head">
        <div className="page-title">
          <h1>Alerts</h1>
          <p className="page-sub">
            The operator alert inbox plus notification destinations and their delivery log.
          </p>
        </div>
        <div className="page-actions">
          {canManageChannels ? (
            <button
              type="button"
              className="btn primary"
              onClick={() => {
                setEditingChannel(null);
                setChannelDialogOpen(true);
              }}
            >
              + New channel
            </button>
          ) : null}
        </div>
      </div>

      <div className="card">
        <div className="card-title">
          <h2>Inbox</h2>
          <div className="flex gap-8">
            <span className="badge NEUTRAL no-dot">
              {unreadQuery.data ? `${unreadQuery.data.count} unread` : "…"}
            </span>
            <button
              type="button"
              className="btn sm"
              disabled={markAllReadMutation.isPending || (unreadQuery.data?.count ?? 0) === 0}
              onClick={() => markAllReadMutation.mutate()}
            >
              Mark all read
            </button>
          </div>
        </div>
        {alertsQuery.isLoading ? (
          <LoadingBlock label="Loading alerts…" />
        ) : alertsQuery.isError ? (
          <ErrorBlock error={alertsQuery.error} />
        ) : alerts.length === 0 ? (
          <EmptyState icon="✓" title="No alerts" hint="System notifications will appear here." />
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th scope="col">Severity</th>
                  <th scope="col">Alert</th>
                  <th scope="col">Event</th>
                  <th scope="col">Received</th>
                  <th scope="col">State</th>
                  <th scope="col">Actions</th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((alert) => (
                  <tr key={alert.id}>
                    <td>
                      <StatusBadge value={alert.severity} />
                    </td>
                    <td>
                      <div>{alert.title}</div>
                      {alert.body ? (
                        <div className="small faint">{truncate(alert.body, 120)}</div>
                      ) : null}
                    </td>
                    <td className="small mono">
                      {alert.event_type || "—"}
                      <div className="faint">{alert.source}</div>
                    </td>
                    <td title={formatDateTime(alert.created_at)}>
                      {formatRelative(alert.created_at)}
                    </td>
                    <td>
                      {alert.read_at ? (
                        <span className="faint small">read</span>
                      ) : (
                        <span className="badge NEUTRAL no-dot">UNREAD</span>
                      )}
                    </td>
                    <td>
                      {!alert.read_at ? (
                        <button
                          type="button"
                          className="btn sm ghost"
                          disabled={markReadMutation.isPending}
                          onClick={() => markReadMutation.mutate(alert)}
                        >
                          Mark read
                        </button>
                      ) : null}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {alertsQuery.data ? (
          <Pagination page={alertsQuery.data} onPage={setAlertOffset} />
        ) : null}
      </div>

      <div className="card">
        <div className="card-title">
          <h2>Notification channels</h2>
          <span className="small faint">destinations for incident &amp; monitor events</span>
        </div>
        {!canReadChannels ? (
          <p className="small muted">
            Your role does not include permission to view notification channels.
          </p>
        ) : channelsQuery.isLoading ? (
          <LoadingBlock label="Loading channels…" />
        ) : channelsQuery.isError ? (
          <ErrorBlock error={channelsQuery.error} />
        ) : channels.length === 0 ? (
          <EmptyState
            icon="✉"
            title="No notification channels configured"
            hint={
              canManageChannels
                ? "Create a webhook or email channel to receive incident notifications."
                : undefined
            }
          />
        ) : (
          <div className="table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th scope="col">Name</th>
                  <th scope="col">Type</th>
                  <th scope="col">Target</th>
                  <th scope="col">Subscribes to</th>
                  <th scope="col">State</th>
                  {canManageChannels ? <th scope="col">Actions</th> : null}
                </tr>
              </thead>
              <tbody>
                {channels.map((channel) => (
                  <tr key={channel.id}>
                    <td>{channel.name}</td>
                    <td>
                      <span className="badge no-dot NEUTRAL mono">{channel.type}</span>
                    </td>
                    <td className="mono small" title={channel.display_target}>
                      {channel.display_target || "—"}
                    </td>
                    <td>
                      <EventChips events={channel.events} />
                    </td>
                    <td>
                      <StatusBadge value={channel.enabled ? "ACTIVE" : "DISABLED"} />
                    </td>
                    {canManageChannels ? (
                      <td>
                        <div className="flex gap-8 wrap">
                          <button
                            type="button"
                            className="btn sm"
                            disabled={toggleChannelMutation.isPending}
                            onClick={() => toggleChannelMutation.mutate(channel)}
                          >
                            {channel.enabled ? "Disable" : "Enable"}
                          </button>
                          <button
                            type="button"
                            className="btn sm ghost"
                            disabled={testChannelMutation.isPending}
                            onClick={() => testChannelMutation.mutate(channel)}
                          >
                            Send test
                          </button>
                          <button
                            type="button"
                            className="btn sm ghost"
                            onClick={() => {
                              setEditingChannel(channel);
                              setChannelDialogOpen(true);
                            }}
                          >
                            Edit
                          </button>
                          <button
                            type="button"
                            className="btn sm danger"
                            onClick={() => setDeletingChannel(channel)}
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
        )}
      </div>

      {canReadChannels ? (
        <div className="card">
          <div className="card-title">
            <h2>Recent deliveries</h2>
            <span className="small faint">{deliveries.length} loaded</span>
          </div>
          {deliveriesQuery.isLoading ? (
            <LoadingBlock label="Loading deliveries…" />
          ) : deliveriesQuery.isError ? (
            <ErrorBlock error={deliveriesQuery.error} />
          ) : deliveries.length === 0 ? (
            <EmptyState
              icon="↗"
              title="No notification deliveries yet"
              hint="Every notification attempt through a channel is logged here."
            />
          ) : (
            <div className="table-wrap">
              <table className="data">
                <thead>
                  <tr>
                    <th scope="col">Status</th>
                    <th scope="col">Event</th>
                    <th scope="col">Subject</th>
                    <th scope="col" className="num">
                      Attempts
                    </th>
                    <th scope="col">Last error</th>
                    <th scope="col">Sent</th>
                  </tr>
                </thead>
                <tbody>
                  {deliveries.map((delivery) => (
                    <tr key={delivery.id}>
                      <td>
                        <StatusBadge value={delivery.status} />
                      </td>
                      <td className="mono small">{delivery.event_type}</td>
                      <td title={delivery.subject}>{truncate(delivery.subject, 60) || "—"}</td>
                      <td className="num">{delivery.attempts}</td>
                      <td className="small muted" title={delivery.last_error}>
                        {delivery.last_error ? truncate(delivery.last_error, 60) : "—"}
                      </td>
                      <td title={formatDateTime(delivery.sent_at)}>
                        {delivery.sent_at ? formatRelative(delivery.sent_at) : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {deliveriesQuery.hasNextPage ? (
            <div className="mt-8">
              <button
                type="button"
                className="btn sm"
                disabled={deliveriesQuery.isFetchingNextPage}
                onClick={() => void deliveriesQuery.fetchNextPage()}
              >
                {deliveriesQuery.isFetchingNextPage ? "Loading…" : "Load more"}
              </button>
            </div>
          ) : null}
        </div>
      ) : null}

      <ChannelDialog
        key={editingChannel?.id ?? "create"}
        open={channelDialogOpen}
        channel={editingChannel}
        onClose={() => setChannelDialogOpen(false)}
      />
      {deletingChannel ? (
        <DeleteChannelDialog
          open
          channel={deletingChannel}
          onClose={() => setDeletingChannel(null)}
        />
      ) : null}
    </main>
  );
}
