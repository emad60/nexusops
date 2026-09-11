/**
 * EventsPage — system events feed (route: /events).
 *
 * Data: GET /events (cursor/keyset-paginated, newest first) and GET /events/types
 * for the filter dropdown. Live: the "global" WebSocket channel pushes each new
 * event as it is persisted; this page live-appends matching events to page one
 * and offers a "show newer" jump when the reader has paged away.
 */

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "../api/client";
import type { CursorPage, EventItem, Page } from "../api/types";
import { EmptyState, ErrorBlock, LoadingBlock, StatusBadge } from "../components/ui";
import { Pagination } from "../components/Pagination";
import { useEventStream, type WsFrame } from "../hooks/useEventStream";

const LIMIT = 25;

const LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] as const;
type EventLevelValue = (typeof LEVELS)[number];

/** Time-range option → milliseconds back from now ("any" sends no `since`). */
const RANGE_MS: Record<string, number> = {
  "1h": 3_600_000,
  "24h": 86_400_000,
  "7d": 604_800_000,
};

interface EventTypeRow {
  type: string;
  description: string;
}

function isEventLevel(value: string): value is EventLevelValue {
  return (LEVELS as readonly string[]).includes(value);
}

/** Defensively convert one "global" WS frame payload into an EventItem. */
function frameToEvent(data: Record<string, unknown>): EventItem | null {
  if (typeof data.type !== "string" || typeof data.id !== "string") return null;
  return {
    id: data.id,
    type: data.type,
    level: typeof data.level === "string" && isEventLevel(data.level) ? data.level : "INFO",
    message: typeof data.message === "string" ? data.message : "",
    actor_type: typeof data.actor_type === "string" ? data.actor_type : "SYSTEM",
    resource_type: typeof data.resource_type === "string" ? data.resource_type : null,
    resource_id: typeof data.resource_id === "string" ? data.resource_id : null,
    data: {},
    created_at: typeof data.created_at === "string" ? data.created_at : new Date().toISOString(),
  };
}

function formatTimestamp(iso: string | null | undefined): string {
  if (!iso) return "—";
  const ts = new Date(iso);
  if (Number.isNaN(ts.getTime())) return iso;
  return ts.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

export default function EventsPage() {
  // Cursor pagination: cursorStack[i] is the keyset cursor that fetches page i.
  const [pageIndex, setPageIndex] = useState(0);
  const [cursorStack, setCursorStack] = useState<Array<string | null>>([null]);
  const [level, setLevel] = useState<string>("ALL");
  const [type, setType] = useState<string>("ALL");
  const [range, setRange] = useState<string>("any");
  // Live events pushed over WS while page one is open (newest first).
  const [liveItems, setLiveItems] = useState<EventItem[]>([]);
  const [liveBehind, setLiveBehind] = useState(0);

  const cursor = cursorStack[pageIndex] ?? null;
  const offset = pageIndex * LIMIT;

  const typesQuery = useQuery({
    queryKey: ["event-types"],
    queryFn: ({ signal }) => apiGet<EventTypeRow[]>("/events/types", undefined, signal),
    staleTime: 5 * 60_000,
  });

  const eventsQuery = useQuery({
    queryKey: ["events", cursor, level, type, range],
    queryFn: ({ signal }) => {
      // Computed at fetch time so the query key stays stable across renders.
      const since =
        range !== "any" && RANGE_MS[range] !== undefined
          ? new Date(Date.now() - RANGE_MS[range]).toISOString()
          : undefined;
      return apiGet<CursorPage<EventItem>>(
        "/events",
        {
          limit: LIMIT,
          cursor: cursor ?? undefined,
          level: level === "ALL" ? undefined : level,
          types: type === "ALL" ? undefined : type,
          since,
        },
        signal,
      );
    },
  });

  const items = eventsQuery.data?.items ?? [];

  const handleFrame = (frame: WsFrame) => {
    if (frame.type !== "event" || !frame.data) return;
    const evt = frameToEvent(frame.data);
    if (!evt) return;
    if (level !== "ALL" && evt.level !== level) return;
    if (type !== "ALL" && evt.type !== type) return;
    if (pageIndex !== 0) {
      setLiveBehind((n) => n + 1);
      return;
    }
    setLiveItems((prev) => [evt, ...prev.filter((e) => e.id !== evt.id)].slice(0, LIMIT));
  };
  useEventStream([{ channel: "global" }], handleFrame);

  function resetToFirstPage() {
    setPageIndex(0);
    setLiveItems([]);
    setLiveBehind(0);
  }

  function handlePage(newOffset: number) {
    const target = Math.floor(newOffset / LIMIT);
    if (target === pageIndex) return;
    if (target > pageIndex) {
      const next = eventsQuery.data?.next_cursor;
      if (!next) return;
      setCursorStack((stack) => {
        const copy = stack.slice(0, target);
        copy[target] = next;
        return copy;
      });
    }
    setPageIndex(target);
    setLiveItems([]);
    setLiveBehind(0);
  }

  // Merge live + fetched, dedupe by id, newest first, capped at one page.
  const seen = new Set<string>();
  const displayed: EventItem[] = [];
  const source = pageIndex === 0 ? [...liveItems, ...items] : items;
  for (const evt of source) {
    if (seen.has(evt.id)) continue;
    seen.add(evt.id);
    displayed.push(evt);
    if (displayed.length >= LIMIT) break;
  }

  // The backend streams a cursor page; synthesize the offset-style shape the
  // shared Pagination component expects (total is "n+1" while more pages exist).
  const synthPage: Page<EventItem> = {
    items: displayed,
    total: eventsQuery.data
      ? eventsQuery.data.has_more
        ? offset + LIMIT + 1
        : offset + eventsQuery.data.items.length
      : 0,
    limit: LIMIT,
    offset,
  };

  return (
    <div>
      <header className="page-head">
        <div className="page-title">
          <h1>Events</h1>
          <p className="page-sub">
            System-wide event stream, newest first — live-updates while this page is open.
          </p>
        </div>
      </header>

      <div className="table-toolbar">
        <div className="filters">
          <label className="small faint" htmlFor="events-level">
            Level
          </label>
          <select
            id="events-level"
            className="input"
            value={level}
            onChange={(event) => {
              setLevel(event.target.value);
              resetToFirstPage();
            }}
          >
            <option value="ALL">All levels</option>
            {LEVELS.map((lv) => (
              <option key={lv} value={lv}>
                {lv}
              </option>
            ))}
          </select>

          <label className="small faint" htmlFor="events-type">
            Type
          </label>
          <select
            id="events-type"
            className="input"
            value={type}
            onChange={(event) => {
              setType(event.target.value);
              resetToFirstPage();
            }}
          >
            <option value="ALL">All types</option>
            {(typesQuery.data ?? []).map((row) => (
              <option key={row.type} value={row.type}>
                {row.type}
              </option>
            ))}
          </select>

          <label className="small faint" htmlFor="events-range">
            Range
          </label>
          <select
            id="events-range"
            className="input"
            value={range}
            onChange={(event) => {
              setRange(event.target.value);
              resetToFirstPage();
            }}
          >
            <option value="any">Any time</option>
            <option value="1h">Last hour</option>
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
          </select>
        </div>

        {liveBehind > 0 ? (
          <button type="button" className="btn sm" onClick={resetToFirstPage}>
            Show {liveBehind} newer event{liveBehind === 1 ? "" : "s"}
          </button>
        ) : null}
      </div>

      {eventsQuery.isPending ? (
        <LoadingBlock label="Loading events…" />
      ) : eventsQuery.isError ? (
        <ErrorBlock error={eventsQuery.error} />
      ) : displayed.length === 0 ? (
        <EmptyState
          title="No events match the current filters"
          hint="Try widening the time range or clearing a filter."
        />
      ) : (
        <div className="table-wrap">
          <table className="data">
            <thead>
              <tr>
                <th>Time</th>
                <th>Level</th>
                <th>Type</th>
                <th>Message</th>
                <th>Actor</th>
                <th>Resource</th>
              </tr>
            </thead>
            <tbody>
              {displayed.map((evt) => (
                <tr key={evt.id}>
                  <td className="num" title={evt.created_at}>
                    {formatTimestamp(evt.created_at)}
                  </td>
                  <td>
                    <StatusBadge value={evt.level} />
                  </td>
                  <td className="mono">{evt.type}</td>
                  <td>{evt.message || <span className="faint">—</span>}</td>
                  <td className="small muted">{evt.actor_type}</td>
                  <td className="small muted mono" title={evt.resource_id ?? undefined}>
                    {evt.resource_type ?? "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!eventsQuery.isPending && !eventsQuery.isError ? (
        <Pagination page={synthPage} onPage={handlePage} />
      ) : null}
    </div>
  );
}
