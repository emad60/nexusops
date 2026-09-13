import { useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { apiGet } from "../api/client";
import type { Page, ServerSummary } from "../api/types";
import { Pagination } from "../components/Pagination";
import { EmptyState, ErrorBlock, StatusBadge } from "../components/ui";
import { TableSkeleton } from "../components/Skeleton";
import { SearchInput } from "../components/form";

/** Host/server summary embedded in container payloads. */
export interface ContainerRef {
  id: string;
  name: string;
  status: string;
}

/**
 * Container row exactly as returned by GET /containers (list projection —
 * `command` and `mounts` only appear on the detail endpoint).
 */
export interface ContainerRow {
  id: string;
  container_id: string;
  name: string;
  image_ref: string;
  status: string;
  health: string;
  env_keys: string[];
  labels: Record<string, string>;
  ports: Array<Record<string, unknown>>;
  restart_count: number;
  cpu_percent: number | null;
  mem_used_mb: number | null;
  mem_limit_mb: number | null;
  net_rx_kb_s: number | null;
  net_tx_kb_s: number | null;
  started_at: string | null;
  finished_at: string | null;
  observed_at: string | null;
  simulated: boolean;
  host: ContainerRef | null;
  server: ContainerRef | null;
}

const PAGE_SIZE = 25;

const STATUS_OPTIONS = [
  "RUNNING",
  "EXITED",
  "PAUSED",
  "CREATED",
  "RESTARTING",
  "DEAD",
  "REMOVED",
];

const SORT_OPTIONS: Array<{ value: string; label: string }> = [
  { value: "observed_at", label: "Observed" },
  { value: "name", label: "Name" },
  { value: "status", label: "Status" },
  { value: "cpu_percent", label: "CPU" },
  { value: "mem_used_mb", label: "Memory" },
];

/** Absolute UTC stamp — deterministic regardless of the viewer's timezone. */
function formatUtc(iso: string | null | undefined): string {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return `${date.toISOString().replace("T", " ").slice(0, 19)} UTC`;
}

function formatCpu(value: number | null): string {
  return value === null || value === undefined ? "—" : `${value.toFixed(1)}%`;
}

function formatMemory(row: ContainerRow): string {
  if (row.mem_used_mb === null || row.mem_used_mb === undefined) return "—";
  const used = Math.round(row.mem_used_mb);
  if (row.mem_limit_mb === null || row.mem_limit_mb === undefined) return `${used} MB`;
  return `${used} / ${Math.round(row.mem_limit_mb)} MB`;
}

export default function ContainerListPage() {
  const navigate = useNavigate();
  const [offset, setOffset] = useState(0);
  const [status, setStatus] = useState("");
  const [serverId, setServerId] = useState("");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("observed_at");
  const [order, setOrder] = useState<"asc" | "desc">("desc");

  // Lightweight option source for the server filter (server names only).
  const serversQuery = useQuery({
    queryKey: ["servers", "container-filter-options"],
    queryFn: ({ signal }) => apiGet<Page<ServerSummary>>("/servers", { limit: 100 }, signal),
    staleTime: 60_000,
  });

  const containersQuery = useQuery({
    queryKey: ["containers", { offset, status, serverId, search, sort, order }],
    queryFn: ({ signal }) =>
      apiGet<Page<ContainerRow>>(
        "/containers",
        {
          limit: PAGE_SIZE,
          offset,
          status: status || undefined,
          server_id: serverId || undefined,
          q: search || undefined,
          sort,
          order,
        },
        signal,
      ),
    placeholderData: keepPreviousData,
  });

  const items = containersQuery.data?.items ?? [];
  const showEmpty =
    !containersQuery.isPending && !containersQuery.isError && items.length === 0;

  return (
    <div>
      <div className="page-head">
        <div className="page-title">
          <h1>Containers</h1>
          <p className="page-sub">
            Workloads across every docker host
            {containersQuery.data ? ` · ${containersQuery.data.total} total` : ""}
          </p>
        </div>
      </div>

      <div className="card">
        <div className="table-toolbar">
          <div className="filters">
            <SearchInput
              placeholder="Search name or image…"
              aria-label="Search containers"
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setOffset(0);
              }}
              onClear={() => {
                setSearch("");
                setOffset(0);
              }}
            />
            <select
              className="input"
              aria-label="Filter by status"
              value={status}
              onChange={(event) => {
                setStatus(event.target.value);
                setOffset(0);
              }}
            >
              <option value="">All statuses</option>
              {STATUS_OPTIONS.map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
            <select
              className="input"
              aria-label="Filter by server"
              value={serverId}
              onChange={(event) => {
                setServerId(event.target.value);
                setOffset(0);
              }}
            >
              <option value="">All servers</option>
              {(serversQuery.data?.items ?? []).map((server) => (
                <option key={server.id} value={server.id}>
                  {server.name}
                </option>
              ))}
            </select>
            <select
              className="input"
              aria-label="Sort containers by"
              value={sort}
              onChange={(event) => {
                setSort(event.target.value);
                setOffset(0);
              }}
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  Sort: {option.label}
                </option>
              ))}
            </select>
            <button
              type="button"
              className="btn sm"
              aria-label={order === "desc" ? "Sorted descending, switch to ascending" : "Sorted ascending, switch to descending"}
              onClick={() => setOrder(order === "desc" ? "asc" : "desc")}
            >
              {order === "desc" ? "↓ Desc" : "↑ Asc"}
            </button>
          </div>
        </div>

        {containersQuery.isPending ? (
          <TableSkeleton label="Loading containers" rows={10} cols={10} />
        ) : containersQuery.isError ? (
          <ErrorBlock error={containersQuery.error} />
        ) : showEmpty ? (
          <EmptyState
            icon="▣"
            title="No containers match"
            hint="Try clearing the search or filters, or check back once a docker host has reported inventory."
          />
        ) : (
          <>
            <div
              className="table-wrap sticky-first"
              style={{ opacity: containersQuery.isFetching ? 0.65 : 1 }}
            >
              <table className="data">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Image</th>
                    <th>Status</th>
                    <th>Health</th>
                    <th>Host</th>
                    <th>Server</th>
                    <th className="num">CPU</th>
                    <th className="num">Memory</th>
                    <th className="num">Restarts</th>
                    <th>Observed</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((row) => (
                    <tr
                      key={row.id}
                      className="clickable"
                      onClick={() => navigate(`/containers/${row.id}`)}
                    >
                      <td>
                        <Link to={`/containers/${row.id}`} className="mono">
                          {row.name}
                        </Link>
                        {row.simulated ? (
                          <span className="badge NEUTRAL no-dot" style={{ marginLeft: 6 }}>
                            SIM
                          </span>
                        ) : null}
                      </td>
                      <td className="mono small">{row.image_ref}</td>
                      <td>
                        <StatusBadge value={row.status} />
                      </td>
                      <td>
                        {row.health === "NONE" ? (
                          <span className="faint">—</span>
                        ) : (
                          <StatusBadge value={row.health} />
                        )}
                      </td>
                      <td>{row.host ? row.host.name : <span className="faint">—</span>}</td>
                      <td>{row.server ? row.server.name : <span className="faint">—</span>}</td>
                      <td className="num">{formatCpu(row.cpu_percent)}</td>
                      <td className="num">{formatMemory(row)}</td>
                      <td className="num">{row.restart_count}</td>
                      <td className="small muted">{formatUtc(row.observed_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {containersQuery.data ? (
              <Pagination
                page={containersQuery.data}
                onPage={(nextOffset) => setOffset(nextOffset)}
              />
            ) : null}
          </>
        )}
      </div>
    </div>
  );
}
