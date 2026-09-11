/**
 * Operational overview — the landing page for the whole fleet.
 *
 * Data comes from GET /dashboard/summary (counters + recent events) and the
 * public GET /meta endpoint (environment + simulation flag), kept live by the
 * `global` WebSocket channel: every event frame is prepended to the feed and
 * the summary query is refreshed.
 *
 * Note: the metrics API only exposes per-server timeseries
 * (/servers/{id}/metrics) — there is no fleet-wide history endpoint, so this
 * page charts nothing and leans on counters + the live feed instead.
 */

import { useState, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiGet } from "../api/client";
import type { DashboardSummary } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { useEventStream, type WsFrame } from "../hooks/useEventStream";
import { EmptyState, ErrorBlock, LoadingBlock, StatusBadge } from "../components/ui";

/** Public instance metadata (subset of the backend MetaOut schema). */
interface MetaInfo {
  name?: string;
  version?: string;
  environment?: string;
  simulation_mode?: boolean;
}

interface FeedItem {
  id: string;
  type: string;
  level: string;
  message: string;
  resource_type: string | null;
  created_at: string;
  live?: boolean;
}

const FEED_LIMIT = 12;
const LIVE_FEED_LIMIT = 20;

/** DEBUG has no badge color; render it neutral. */
function badgeLevel(level: string): string {
  return level === "DEBUG" ? "NEUTRAL" : level;
}

function formatTimestamp(iso: string): string {
  const ts = new Date(iso);
  if (Number.isNaN(ts.getTime())) return iso;
  return ts.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Narrow an untyped WebSocket frame payload into a feed item. */
function asFeedItem(data: Record<string, unknown> | undefined): FeedItem | null {
  if (!data || typeof data.id !== "string") return null;
  return {
    id: data.id,
    type: typeof data.type === "string" ? data.type : "EVENT",
    level: typeof data.level === "string" ? data.level : "INFO",
    message: typeof data.message === "string" ? data.message : "",
    resource_type: typeof data.resource_type === "string" ? data.resource_type : null,
    created_at:
      typeof data.created_at === "string" ? data.created_at : new Date().toISOString(),
    live: true,
  };
}

/** Status pill with a trailing count; hidden entirely at zero. */
function CountBadge({ value, count }: { value: string; count: number }) {
  if (count <= 0) return null;
  return <span className={`badge ${value}`}>{`${value} ${count}`}</span>;
}

interface StatSpec {
  key: string;
  label: string;
  value: number;
  tone: "" | "ok" | "warn" | "err";
  foot: ReactNode;
  to: string;
  link: string;
  hidden: boolean;
}

export default function DashboardPage() {
  const { hasPermission } = useAuth();
  const queryClient = useQueryClient();
  const [liveEvents, setLiveEvents] = useState<FeedItem[]>([]);

  // Public metadata — simulation flag, environment, version.
  const { data: meta } = useQuery({
    queryKey: ["meta"],
    queryFn: ({ signal }) => apiGet<MetaInfo>("/meta", undefined, signal),
    staleTime: 5 * 60_000,
  });

  const summaryQuery = useQuery({
    queryKey: ["dashboard", "summary"],
    queryFn: ({ signal }) => apiGet<DashboardSummary>("/dashboard/summary", undefined, signal),
    staleTime: 30_000,
    refetchInterval: 60_000,
  });
  const summary = summaryQuery.data;

  useEventStream([{ channel: "global" }], (frame: WsFrame) => {
    if (frame.type !== "event") return;
    const item = asFeedItem(frame.data);
    if (!item) return;
    setLiveEvents((current) =>
      [item, ...current.filter((existing) => existing.id !== item.id)].slice(0, LIVE_FEED_LIMIT),
    );
    void queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] });
  });

  const avgCpu = summary?.avg_cpu_percent ?? null;
  const avgMem = summary?.avg_mem_percent ?? null;

  const stats: StatSpec[] = summary
    ? [
        {
          key: "servers",
          label: "Servers online",
          value: summary.servers_online,
          tone: summary.servers_offline > 0 ? "err" : "ok",
          foot: (
            <div>
              <div className="flex gap-8 wrap">
                <CountBadge value="ONLINE" count={summary.servers_online} />
                <CountBadge value="DEGRADED" count={summary.servers_degraded} />
                <CountBadge value="OFFLINE" count={summary.servers_offline} />
                <CountBadge value="UNKNOWN" count={Math.max(0, summary.servers_total - summary.servers_online - summary.servers_offline - summary.servers_degraded)} />
              </div>
              {avgCpu != null || avgMem != null ? (
                <div className="small faint mt-8">
                  {avgCpu != null ? `Avg CPU ${Math.round(avgCpu)}%` : null}
                  {avgCpu != null && avgMem != null ? " · " : null}
                  {avgMem != null ? `Avg memory ${Math.round(avgMem)}%` : null}
                </div>
              ) : null}
            </div>
          ),
          to: "/servers",
          link: "View servers",
          hidden: !hasPermission("server.read"),
        },
        {
          key: "incidents",
          label: "Open incidents",
          value: summary.incidents_open,
          tone: summary.incidents_open > 0 ? "err" : "ok",
          foot: (
            <span>
              {summary.monitors_up} monitors up · {summary.monitors_down} down
            </span>
          ),
          to: "/incidents",
          link: "View incidents",
          hidden: !hasPermission("monitor.read"),
        },
        {
          key: "containers",
          label: "Running containers",
          value: summary.containers_running,
          tone: "ok",
          foot: <span>Across all docker hosts</span>,
          to: "/containers",
          link: "View containers",
          hidden: !hasPermission("container.read"),
        },
        {
          key: "deployments",
          label: "Deployments today",
          value: summary.deployments_today,
          tone: summary.deployments_failed_today > 0 ? "warn" : "ok",
          foot: <span>{summary.deployments_failed_today} failed today</span>,
          to: "/deployments",
          link: "View deployments",
          hidden: !hasPermission("deployment.read"),
        },
        {
          key: "monitors",
          label: "Monitors up",
          value: summary.monitors_up,
          tone: summary.monitors_down > 0 ? "warn" : "ok",
          foot: (
            <span>
              {summary.monitors_down} down · {summary.monitors_paused} paused
            </span>
          ),
          to: "/monitors",
          link: "View monitors",
          hidden: !hasPermission("monitor.read"),
        },
      ]
    : [];

  // Live frames first, then the summary snapshot; deduped by event id.
  const seen = new Set<string>();
  const feed: FeedItem[] = [];
  for (const item of [...liveEvents, ...(summary?.recent_events ?? [])]) {
    if (seen.has(item.id)) continue;
    seen.add(item.id);
    feed.push(item);
    if (feed.length >= FEED_LIMIT) break;
  }

  return (
    <>
      <div className="page-head">
        <div className="page-title">
          <h1>
            Overview
            {meta?.simulation_mode ? (
              <span
                className="badge no-dot"
                style={{ background: "var(--warn-soft)", color: "var(--warn)" }}
                title="Simulated infrastructure — no real hosts are contacted"
              >
                SIMULATION MODE
              </span>
            ) : null}
          </h1>
          <p className="page-sub">
            {meta
              ? `${meta.name ?? "NexusOps"} v${meta.version ?? "?"}${
                  meta.environment ? ` · ${meta.environment} environment` : ""
                }`
              : "Fleet health at a glance"}
          </p>
        </div>
      </div>

      {summaryQuery.isLoading ? <LoadingBlock label="Loading fleet overview…" /> : null}
      {summaryQuery.isError ? <ErrorBlock error={summaryQuery.error} /> : null}

      {summary ? (
        <>
          {summary.servers_total === 0 ? (
            <div className="card mb-16">
              <EmptyState
                icon="▣"
                title="No servers enrolled yet"
                hint="Enroll a server with the NexusOps agent to see live metrics, containers and deployments here."
              />
            </div>
          ) : null}

          <div className="grid cols-4 mb-16">
            {stats.map((stat) => (
              <div key={stat.key} className="card stat-card">
                <div className="stat-label">{stat.label}</div>
                <div className={`stat-value ${stat.tone}`}>{stat.value.toLocaleString()}</div>
                <div className="stat-foot">{stat.foot}</div>
                {!stat.hidden ? (
                  <Link className="small" to={stat.to} style={{ display: "inline-block", marginTop: 8 }}>
                    {stat.link} →
                  </Link>
                ) : null}
              </div>
            ))}
          </div>

          <div className="card">
            <div className="card-title">
              <h2>Recent events</h2>
              {hasPermission("event.read") ? (
                <Link className="small" to="/events">
                  View all events →
                </Link>
              ) : null}
            </div>
            {feed.length === 0 ? (
              <EmptyState
                icon="⇄"
                title="No events yet"
                hint="System activity will stream in here as it happens."
              />
            ) : (
              <ul className="timeline">
                {feed.map((item) => (
                  <li key={item.id}>
                    <div className="flex gap-8 wrap" style={{ alignItems: "center" }}>
                      {item.live ? (
                        <span
                          aria-label="Delivered live"
                          title="Delivered live"
                          style={{ color: "var(--accent)" }}
                        >
                          ●
                        </span>
                      ) : null}
                      <StatusBadge value={badgeLevel(item.level)} />
                      <span className="mono faint small">{item.type}</span>
                    </div>
                    <div className="mt-8">{item.message || item.type}</div>
                    <div className="tl-time">
                      {formatTimestamp(item.created_at)}
                      {item.resource_type ? ` · ${item.resource_type}` : ""}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </>
      ) : null}
    </>
  );
}
