import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ToastProvider } from "../components/toast";
import DockerHostsPage from "./DockerHostsPage";
import type { DockerHostOut, Page, ServerSummary } from "../api/types";

vi.mock("../api/client", () => {
  class ApiError extends Error {
    status: number;
    code: string;
    constructor(status: number, code: string, message: string) {
      super(message);
      this.status = status;
      this.code = code;
    }
  }
  return { apiGet: vi.fn(), apiPost: vi.fn(), apiPatch: vi.fn(), apiDelete: vi.fn(), ApiError };
});

import { apiGet, apiPost, ApiError } from "../api/client";

const host: DockerHostOut = {
  id: "h-1",
  server_id: "srv-1",
  name: "docker on build-01",
  endpoint_url: "unix:///var/run/docker.sock",
  tls_verify: true,
  status: "AVAILABLE",
  last_checked_at: "2026-09-10T11:00:00Z",
  last_error: "",
  created_at: "2026-01-01T00:00:00Z",
};

const failingHost: DockerHostOut = {
  ...host,
  id: "h-2",
  server_id: null,
  name: "docker on edge-02",
  endpoint_url: "",
  tls_verify: false,
  status: "UNAVAILABLE",
  last_checked_at: null,
  last_error: "connection refused",
};

const server: ServerSummary = {
  id: "srv-1",
  name: "build-01",
  hostname: "build-01.internal",
  ip_address: "10.0.0.5",
  os_name: "Linux",
  os_version: "6.8",
  arch: "x86_64",
  environment: "prod",
  location: "dc1",
  description: "",
  status: "ONLINE",
  cpu_cores: 8,
  memory_total_mb: 16384,
  disk_total_gb: 500,
  agent_version: "1.0.0",
  enrolled: true,
  simulated: false,
  heartbeat_interval_seconds: 15,
  offline_after_seconds: 60,
  uptime_seconds: 3600,
  tags: [],
  docker_host: null,
  last_heartbeat_at: null,
  created_at: "2026-01-01T00:00:00Z",
};

const serversPage: Page<ServerSummary> = {
  items: [server],
  total: 1,
  limit: 100,
  offset: 0,
};

const hostsPage: Page<DockerHostOut> = {
  items: [host, failingHost],
  total: 2,
  limit: 20,
  offset: 0,
};

function renderHosts() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <MemoryRouter initialEntries={["/docker-hosts"]}>
          <Routes>
            <Route path="/docker-hosts" element={<DockerHostsPage />} />
            <Route path="/servers/:serverId" element={<div>server detail</div>} />
          </Routes>
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  );
}

function mockCountApi() {
  const totalsByHost: Record<string, { total: number; running: number }> = {
    "h-1": { total: 7, running: 4 },
    "h-2": { total: 2, running: 1 },
  };
  vi.mocked(apiGet).mockImplementation(async (path: string, query?: Record<string, unknown>) => {
    if (path === "/docker-hosts") return hostsPage;
    if (path === "/servers") return serversPage;
    if (path === "/containers") {
      const counts = totalsByHost[String(query?.host_id)] ?? { total: 0, running: 0 };
      const running = query?.status === "RUNNING";
      return { items: [], total: running ? counts.running : counts.total, limit: 1, offset: 0 };
    }
    throw new Error(`unexpected path: ${path}`);
  });
}

beforeEach(() => {
  vi.mocked(apiGet).mockReset();
  vi.mocked(apiPost).mockReset();
});

describe("DockerHostsPage", () => {
  it("renders hosts with container counts, server links and errors", async () => {
    mockCountApi();
    renderHosts();

    const table = await screen.findByRole("table");
    expect(within(table).getByText("docker on build-01")).toBeInTheDocument();
    expect(within(table).getByText("docker on edge-02")).toBeInTheDocument();
    expect(within(table).getByText("AVAILABLE")).toBeInTheDocument();
    expect(within(table).getByText("UNAVAILABLE")).toBeInTheDocument();
    expect(await screen.findByText("4 / 7")).toBeInTheDocument();
    expect(screen.getByText("1 / 2")).toBeInTheDocument();
    expect(screen.getByTitle("connection refused")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "build-01" })).toHaveAttribute(
      "href",
      "/servers/srv-1",
    );
  });

  it("shows the empty state when no hosts are registered", async () => {
    vi.mocked(apiGet).mockImplementation(async (path: string) => {
      if (path === "/docker-hosts") return { items: [], total: 0, limit: 20, offset: 0 };
      if (path === "/servers") return serversPage;
      throw new Error(`unexpected path: ${path}`);
    });

    renderHosts();

    expect(await screen.findByText("No docker hosts registered")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Ping host/ })).not.toBeInTheDocument();
  });

  it("renders the API error message when the host list fails", async () => {
    vi.mocked(apiGet).mockImplementation(async (path: string) => {
      if (path === "/servers") return serversPage;
      throw new ApiError(403, "PERMISSION_DENIED", "container.read is required");
    });

    renderHosts();

    expect(await screen.findByText(/PERMISSION_DENIED/)).toBeInTheDocument();
    expect(screen.getByText(/container.read is required/)).toBeInTheDocument();
  });

  it("pings a host and reports the latency via toast", async () => {
    mockCountApi();
    vi.mocked(apiPost).mockResolvedValue({
      status: "AVAILABLE",
      checked_at: "2026-09-10T12:00:00Z",
      latency_ms: 42.4,
      error: "",
    });
    renderHosts();
    await screen.findByText("docker on build-01");

    fireEvent.click(screen.getByRole("button", { name: "Ping host docker on build-01" }));

    await screen.findByText(/Host reachable in 42 ms/);
    expect(apiPost).toHaveBeenCalledWith("/docker-hosts/h-1/ping");
  });

  it("reports an unreachable host via the error toast and refreshes hosts", async () => {
    mockCountApi();
    vi.mocked(apiPost).mockResolvedValue({
      status: "UNAVAILABLE",
      checked_at: "2026-09-10T12:00:00Z",
      latency_ms: null,
      error: "dial tcp: connectex: no connection could be made",
    });
    renderHosts();
    await screen.findByText("docker on edge-02");

    fireEvent.click(screen.getByRole("button", { name: "Ping host docker on edge-02" }));

    await screen.findByText(/Host unreachable: dial tcp/);
    await waitFor(() => {
      expect(vi.mocked(apiGet).mock.calls.some(([path]) => path === "/docker-hosts")).toBe(true);
    });
  });
});
