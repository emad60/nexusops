import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ContainerListPage from "./ContainerListPage";
import type { ContainerRow } from "./ContainerListPage";
import type { Page, ServerSummary } from "../api/types";
import type { ReactElement } from "react";

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

import { apiGet, ApiError } from "../api/client";

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

function makeContainer(overrides: Partial<ContainerRow>): ContainerRow {
  return {
    id: "c-1",
    container_id: "abc123def456",
    name: "web-proxy",
    image_ref: "nginx:1.25",
    status: "RUNNING",
    health: "HEALTHY",
    env_keys: [],
    labels: {},
    ports: [],
    restart_count: 0,
    cpu_percent: 3.5,
    mem_used_mb: 128,
    mem_limit_mb: 512,
    net_rx_kb_s: 1.2,
    net_tx_kb_s: 0.8,
    started_at: "2026-09-01T00:00:00Z",
    finished_at: null,
    observed_at: "2026-09-10T12:00:00Z",
    simulated: false,
    host: { id: "h-1", name: "docker on build-01", status: "AVAILABLE" },
    server: { id: "srv-1", name: "build-01", status: "ONLINE" },
    ...overrides,
  };
}

function renderPage(ui: ReactElement = <ContainerListPage />) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/containers"]}>
        <Routes>
          <Route path="/containers" element={ui} />
          <Route path="/containers/:containerId" element={ui} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.mocked(apiGet).mockReset();
});

describe("ContainerListPage", () => {
  it("renders container rows with status, host and usage", async () => {
    vi.mocked(apiGet).mockImplementation(async (path: string) => {
      if (path === "/servers") return serversPage;
      if (path === "/containers") {
        return {
          items: [
            makeContainer({}),
            makeContainer({
              id: "c-2",
              name: "db-primary",
              image_ref: "postgres:16",
              status: "EXITED",
              health: "NONE",
              mem_used_mb: 512,
              mem_limit_mb: 1024,
              host: null,
              server: null,
            }),
          ],
          total: 2,
          limit: 25,
          offset: 0,
        };
      }
      throw new Error(`unexpected path: ${path}`);
    });

    renderPage();

    const table = await screen.findByRole("table");
    expect(within(table).getByText("web-proxy")).toBeInTheDocument();
    expect(within(table).getByText("db-primary")).toBeInTheDocument();
    expect(within(table).getByText("nginx:1.25")).toBeInTheDocument();
    // Status badges are scoped to the table — the filter <option>s share the text.
    expect(within(table).getByText("RUNNING")).toBeInTheDocument();
    expect(within(table).getByText("EXITED")).toBeInTheDocument();
    expect(within(table).getByText("docker on build-01")).toBeInTheDocument();
    expect(within(table).getByText("128 / 512 MB")).toBeInTheDocument();
    expect(within(table).getByText("512 / 1024 MB")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "db-primary" })).toHaveAttribute(
      "href",
      "/containers/c-2",
    );
  });

  it("shows the empty state when no containers exist", async () => {
    vi.mocked(apiGet).mockImplementation(async (path: string) => {
      if (path === "/servers") return serversPage;
      if (path === "/containers") return { items: [], total: 0, limit: 25, offset: 0 };
      throw new Error(`unexpected path: ${path}`);
    });

    renderPage();

    expect(await screen.findByText("No containers match")).toBeInTheDocument();
    expect(screen.queryByText("web-proxy")).not.toBeInTheDocument();
  });

  it("renders the API error message when the request fails", async () => {
    vi.mocked(apiGet).mockImplementation(async (path: string) => {
      if (path === "/servers") return serversPage;
      throw new ApiError(500, "DB_DOWN", "Database unavailable");
    });

    renderPage();

    expect(await screen.findByText(/DB_DOWN/)).toBeInTheDocument();
    expect(screen.getByText(/Database unavailable/)).toBeInTheDocument();
  });

  it("sends the status filter and resets the offset when filtering", async () => {
    vi.mocked(apiGet).mockImplementation(async (path: string) => {
      if (path === "/servers") return serversPage;
      if (path === "/containers") {
        return { items: [makeContainer({})], total: 1, limit: 25, offset: 0 };
      }
      throw new Error(`unexpected path: ${path}`);
    });

    renderPage();
    await screen.findByText("web-proxy");

    fireEvent.change(screen.getByLabelText("Filter by status"), {
      target: { value: "RUNNING" },
    });
    fireEvent.change(screen.getByLabelText("Search containers"), {
      target: { value: "proxy" },
    });

    await waitFor(() => {
      const calls = vi
        .mocked(apiGet)
        .mock.calls.filter(([requestedPath]) => requestedPath === "/containers");
      const last = calls[calls.length - 1];
      expect(last?.[1]).toMatchObject({ status: "RUNNING", q: "proxy", offset: 0 });
    });
  });
});
