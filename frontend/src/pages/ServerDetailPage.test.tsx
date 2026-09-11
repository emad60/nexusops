import { act, render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ServerDetailPage from "./ServerDetailPage";
import { ToastProvider } from "../components/toast";
import type { ContainerOut, Page, ServerDetail, ServerSummary } from "../api/types";

const mocks = vi.hoisted(() => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
  useEventStream: vi.fn(),
  frameHandler: null as null | ((frame: unknown) => void),
}));

vi.mock("../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/client")>();
  return { ...actual, apiGet: mocks.apiGet, apiPost: mocks.apiPost, apiPatch: mocks.apiPatch, apiDelete: mocks.apiDelete };
});

vi.mock("../hooks/useEventStream", () => ({
  useEventStream: mocks.useEventStream,
}));

vi.mock("../auth/AuthContext", () => ({
  AuthProvider: ({ children }: { children: ReactNode }) => children,
  useAuth: () => ({
    user: null,
    permissions: ["*"],
    superadmin: true,
    initializing: false,
    login: vi.fn(),
    logout: vi.fn(),
    refreshProfile: vi.fn(),
    hasPermission: () => true,
  }),
}));

const SERVER_ID = "srv-1";

function makeDetail(): ServerDetail {
  const summary: ServerSummary = {
    id: SERVER_ID,
    name: "edge-01",
    hostname: "edge01.example.net",
    ip_address: "10.0.0.14",
    os_name: "Ubuntu",
    os_version: "24.04",
    arch: "x86_64",
    environment: "production",
    location: "dc-west",
    description: "Edge compute node",
    status: "ONLINE",
    cpu_cores: 8,
    memory_total_mb: 16384,
    disk_total_gb: 512,
    agent_version: "1.4.2",
    enrolled: true,
    simulated: false,
    heartbeat_interval_seconds: 30,
    offline_after_seconds: null,
    uptime_seconds: 86400,
    tags: [{ id: "t1", name: "edge", color: "#38bdf8" }],
    docker_host: null,
    last_heartbeat_at: new Date(Date.now() - 30_000).toISOString(),
    created_at: "2026-01-01T00:00:00Z",
  };
  return {
    ...summary,
    counts: { containers_running: 1, containers_total: 1 },
    recent_events: [
      {
        id: "e1",
        type: "SERVER_ONLINE",
        level: "INFO",
        message: "Agent connected",
        actor_type: "AGENT",
        resource_type: "server",
        resource_id: SERVER_ID,
        data: {},
        created_at: "2026-09-10T08:00:00Z",
      },
    ],
  };
}

const timeseries = {
  range: "24h",
  granularity: "RAW",
  points: [
    { ts: "2026-09-10T07:00:00Z", cpu_percent_avg: 41, mem_percent_avg: 62, disk_percent_avg: 55 },
    { ts: "2026-09-10T08:00:00Z", cpu_percent_avg: 44, mem_percent_avg: 61, disk_percent_avg: 55 },
  ],
};

const snapshot = {
  server_id: SERVER_ID,
  recorded_at: "2026-09-10T08:00:00Z",
  cpu_percent: 41,
  mem_used_mb: 8192,
  mem_percent: 62,
  disk_used_gb: 280,
  disk_percent: 55,
  net_rx_kb_s: 12.5,
  net_tx_kb_s: 8.1,
  load1: 0.4,
  uptime_seconds: 86400,
};

const container: ContainerOut = {
  id: "cnt-1",
  container_id: "abc123def456",
  name: "redis",
  image_ref: "redis:7",
  command: "",
  status: "RUNNING",
  health: "HEALTHY",
  ports: [],
  env_keys: [],
  labels: {},
  mounts: [],
  restart_count: 0,
  cpu_percent: 12.5,
  mem_used_mb: 256,
  mem_limit_mb: 1024,
  net_rx_kb_s: null,
  net_tx_kb_s: null,
  started_at: "2026-09-01T00:00:00Z",
  observed_at: new Date(Date.now() - 60_000).toISOString(),
  simulated: false,
  docker_host: null,
  server: { id: SERVER_ID, name: "edge-01" },
  created_at: "2026-09-01T00:00:00Z",
};

function renderDetail() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <ToastProvider>
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[`/servers/${SERVER_ID}`]}>
          <Routes>
            <Route path="/servers/:serverId" element={<ServerDetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    </ToastProvider>,
  );
}

function primeApiGet() {
  mocks.apiGet.mockImplementation((path: string) => {
    if (path === `/servers/${SERVER_ID}`) return Promise.resolve(makeDetail());
    if (path === `/servers/${SERVER_ID}/metrics/latest`) return Promise.resolve(snapshot);
    if (path.startsWith(`/servers/${SERVER_ID}/metrics`)) return Promise.resolve(timeseries);
    if (path === "/containers") {
      return Promise.resolve({
        items: [container],
        total: 1,
        limit: 8,
        offset: 0,
      } satisfies Page<ContainerOut>);
    }
    return Promise.reject(new Error(`unexpected path: ${path}`));
  });
}

describe("ServerDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.frameHandler = null;
    mocks.useEventStream.mockImplementation((_subs: unknown, handler: (frame: unknown) => void) => {
      mocks.frameHandler = handler;
    });
    primeApiGet();
  });

  it("renders server facts, live stat cards, containers and events", async () => {
    renderDetail();

    expect(await screen.findByRole("heading", { name: /edge-01/ })).toBeInTheDocument();
    expect(screen.getByText("1.4.2")).toBeInTheDocument(); // agent version
    expect(screen.getByText("41%")).toBeInTheDocument(); // CPU from latest snapshot
    expect(screen.getByText("edge")).toBeInTheDocument(); // tag chip
    expect(screen.getByRole("link", { name: "redis" })).toBeInTheDocument(); // containers table
    expect(screen.getByText("Agent connected")).toBeInTheDocument(); // recent event
    expect(screen.getByRole("link", { name: "Audit log" })).toHaveAttribute(
      "href",
      "/audit-logs",
    );
  });

  it("applies live metric frames pushed over the event stream", async () => {
    renderDetail();
    expect(await screen.findByText("41%")).toBeInTheDocument();

    const frame = {
      type: "event",
      channel: "server-metrics",
      params: { server_id: SERVER_ID },
      data: {
        server_id: SERVER_ID,
        ts: new Date().toISOString(),
        cpu_percent: 82,
        mem_percent: 55,
        mem_used_mb: 2048,
        disk_percent: 63,
      },
    };
    await act(async () => {
      mocks.frameHandler?.(frame);
    });

    expect(await screen.findByText("82%")).toBeInTheDocument();
    expect(screen.getByText("55%")).toBeInTheDocument();
    expect(screen.getByText("63%")).toBeInTheDocument();
    expect(mocks.useEventStream).toHaveBeenCalledWith(
      [{ channel: "server-metrics", params: { server_id: SERVER_ID } }],
      expect.any(Function),
    );
  });

  it("issues an agent token, shows it once, and hides it after dismissal", async () => {
    mocks.apiPost.mockImplementation((path: string) => {
      if (path === `/servers/${SERVER_ID}/agent-token`) {
        return Promise.resolve({
          agent_token: "nxs_live_secret_abc123",
          install_hint: "NEXUSOPS_TOKEN=nxs_live_secret_abc123 bash agent/install.sh",
        });
      }
      return Promise.reject(new Error(`unexpected POST ${path}`));
    });

    renderDetail();
    fireEvent.click(await screen.findByRole("button", { name: "Issue agent token" }));

    expect(await screen.findByText(/shown only once/)).toBeInTheDocument();
    expect(screen.getByDisplayValue("nxs_live_secret_abc123")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Done — I saved it" }));
    await waitFor(() => {
      expect(screen.queryByDisplayValue("nxs_live_secret_abc123")).not.toBeInTheDocument();
    });
  });

  it("shows an error block when the server cannot be loaded", async () => {
    const { ApiError } = await import("../api/client");
    mocks.apiGet.mockImplementation(() =>
      Promise.reject(new ApiError(404, "NOT_FOUND", "No such server")),
    );

    renderDetail();

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/No such server/);
  });
});
