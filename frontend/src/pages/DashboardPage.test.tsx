import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "../auth/AuthContext";
import DashboardPage from "./DashboardPage";

const mocks = vi.hoisted(() => ({
  apiGet: vi.fn(),
  stream: {
    subs: null as unknown,
    handler: null as ((frame: unknown) => void) | null,
  },
}));

vi.mock("../api/client", () => ({
  ApiError: class ApiError extends Error {
    readonly status: number;
    readonly code: string;
    constructor(status: number, code: string, message: string) {
      super(message);
      this.name = "ApiError";
      this.status = status;
      this.code = code;
    }
  },
  apiGet: mocks.apiGet,
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
  apiRequest: vi.fn(),
  setAccessToken: vi.fn(),
  getAccessToken: () => null,
  refreshToken: vi.fn(async () => false),
  API_BASE: "/api/v1",
}));

// The real hook opens a WebSocket; capture the handler instead so tests stay
// deterministic and network-free.
vi.mock("../hooks/useEventStream", () => ({
  useEventStream: (subs: unknown, onFrame: (frame: unknown) => void) => {
    mocks.stream.subs = subs;
    mocks.stream.handler = onFrame;
  },
}));

const ME = {
  user: {
    id: "u-1",
    email: "op@nexusops.io",
    full_name: "Ops One",
    is_active: true,
    status: "ACTIVE" as const,
    role_id: "r-1",
    role_name: "admin",
    last_login_at: null,
    created_at: "2026-01-01T00:00:00Z",
  },
  role: "admin",
  permissions: ["*"],
  superadmin: true,
};

const META = {
  name: "NexusOps",
  version: "1.0.0",
  environment: "production",
  simulation_mode: true,
  event_types: [],
};

const SUMMARY = {
  servers_total: 3,
  servers_online: 2,
  servers_offline: 1,
  servers_degraded: 0,
  containers_running: 7,
  monitors_up: 4,
  monitors_down: 1,
  monitors_paused: 1,
  incidents_open: 2,
  deployments_today: 5,
  deployments_failed_today: 1,
  avg_cpu_percent: 34.5,
  avg_mem_percent: 61.2,
  unread_alerts: 0,
  recent_events: [
    {
      id: "ev-1",
      type: "INCIDENT_OPENED",
      level: "CRITICAL",
      message: "api-gateway is down",
      actor_type: "SYSTEM",
      resource_type: "incident",
      resource_id: "i-1",
      data: {},
      created_at: "2026-09-10T09:15:00Z",
    },
  ],
};

function mockApi(overrides: { summary?: unknown } = {}) {
  mocks.apiGet.mockImplementation((path: string) => {
    if (path === "/auth/me") return Promise.resolve(ME);
    if (path === "/meta") return Promise.resolve(META);
    if (path === "/dashboard/summary") {
      return overrides.summary !== undefined
        ? overrides.summary
        : Promise.resolve(SUMMARY);
    }
    return Promise.reject(new Error(`unexpected GET ${path}`));
  });
}

async function renderDashboard() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const utils = render(
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <DashboardPage />
        </AuthProvider>
      </QueryClientProvider>
    </MemoryRouter>,
  );
  // Settle AuthProvider's async /auth/me probe inside act.
  await act(async () => {});
  return utils;
}

beforeEach(() => {
  vi.clearAllMocks();
  mocks.stream.subs = null;
  mocks.stream.handler = null;
});

describe("DashboardPage", () => {
  it("renders loading, then fleet summary, simulation badge and recent events", async () => {
    // Hold the summary back so the loading state is observable after mount.
    let resolveSummary!: (value: unknown) => void;
    mockApi({
      summary: new Promise((resolve) => {
        resolveSummary = resolve;
      }),
    });
    await renderDashboard();

    expect(screen.getByText("Loading fleet overview…")).toBeInTheDocument();

    act(() => resolveSummary(SUMMARY));

    expect(await screen.findByText("Open incidents")).toBeInTheDocument();
    expect(screen.getByText("SIMULATION MODE")).toBeInTheDocument();
    expect(screen.getByText("api-gateway is down")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /view servers/i })).toHaveAttribute(
      "href",
      "/servers",
    );
    // Subscribed to the live global channel.
    expect(mocks.stream.subs).toEqual([{ channel: "global" }]);
  });

  it("shows the error block when the summary request fails", async () => {
    const { ApiError } = await import("../api/client");
    mockApi({
      summary: Promise.reject(new ApiError(503, "SERVICE_UNAVAILABLE", "Summary unavailable")),
    });
    await renderDashboard();

    expect(await screen.findByRole("alert")).toHaveTextContent("SERVICE_UNAVAILABLE");
    // Counters are not rendered from a failed summary.
    expect(screen.queryByText("Open incidents")).not.toBeInTheDocument();
  });

  it("prepends live event frames from the global stream to the feed", async () => {
    mockApi();
    await renderDashboard();
    await screen.findByText("SIMULATION MODE");

    act(() => {
      mocks.stream.handler?.({
        type: "event",
        channel: "global",
        params: {},
        data: {
          id: "live-1",
          type: "SERVER_ONLINE",
          level: "INFO",
          message: "edge-01 came back online",
          resource_type: "server",
          created_at: "2026-09-10T10:00:00Z",
        },
      });
    });

    expect(await screen.findByText("edge-01 came back online")).toBeInTheDocument();
    expect(screen.getByLabelText("Delivered live")).toBeInTheDocument();
    // The live item ranks above the snapshot's recent event.
    const feed = screen.getByRole("list");
    expect(feed.textContent).toContain("edge-01 came back online");
    expect(feed.textContent).toContain("api-gateway is down");
  });

  it("renders the empty state when no servers are enrolled", async () => {
    mockApi({
      summary: Promise.resolve({
        ...SUMMARY,
        servers_total: 0,
        servers_online: 0,
        servers_offline: 0,
        servers_degraded: 0,
        recent_events: [],
      }),
    });
    await renderDashboard();

    expect(await screen.findByText("No servers enrolled yet")).toBeInTheDocument();
    expect(screen.getByText("No events yet")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByRole("link", { name: /view servers/i })).toHaveAttribute(
        "href",
        "/servers",
      );
    });
  });
});
