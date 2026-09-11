import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import ServerListPage from "./ServerListPage";
import { ToastProvider } from "../components/toast";
import type { Page, ServerSummary } from "../api/types";

const mocks = vi.hoisted(() => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
}));

vi.mock("../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/client")>();
  return { ...actual, apiGet: mocks.apiGet, apiPost: mocks.apiPost, apiPatch: mocks.apiPatch, apiDelete: mocks.apiDelete };
});

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

function makeServer(overrides: Partial<ServerSummary> = {}): ServerSummary {
  return {
    id: "srv-1",
    name: "edge-01",
    hostname: "edge01.example.net",
    ip_address: "10.0.0.14",
    os_name: "Ubuntu",
    os_version: "24.04",
    arch: "x86_64",
    environment: "production",
    location: "dc-west",
    description: "",
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
    last_heartbeat_at: new Date(Date.now() - 5 * 60_000).toISOString(),
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function renderList() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <ToastProvider>
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={["/servers"]}>
          <Routes>
            <Route path="/servers" element={<ServerListPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    </ToastProvider>,
  );
}

describe("ServerListPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders server rows with status badges, tags and relative heartbeat", async () => {
    const page: Page<ServerSummary> = {
      items: [
        makeServer(),
        makeServer({
          id: "srv-2",
          name: "db-01",
          hostname: "db01.example.net",
          status: "OFFLINE",
          last_heartbeat_at: null,
          tags: [],
        }),
      ],
      total: 2,
      limit: 20,
      offset: 0,
    };
    mocks.apiGet.mockImplementation(() => Promise.resolve(page));

    renderList();

    expect(await screen.findByText("edge-01")).toBeInTheDocument();
    expect(screen.getByText("db-01")).toBeInTheDocument();
    expect(screen.getByText("ONLINE", { selector: ".badge" })).toBeInTheDocument();
    expect(screen.getByText("OFFLINE", { selector: ".badge" })).toBeInTheDocument();
    expect(screen.getByText("5m ago")).toBeInTheDocument();
    expect(screen.getByText("Showing 1–2 of 2")).toBeInTheDocument();
    expect(mocks.apiGet).toHaveBeenCalledWith(
      "/servers",
      expect.objectContaining({ limit: 20, offset: 0 }),
      expect.anything(),
    );
  });

  it("shows the empty state when no servers exist", async () => {
    mocks.apiGet.mockImplementation(() =>
      Promise.resolve({ items: [], total: 0, limit: 20, offset: 0 } satisfies Page<ServerSummary>),
    );

    renderList();

    expect(await screen.findByText("No servers found")).toBeInTheDocument();
  });

  it("shows an error block when the API call fails", async () => {
    const { ApiError } = await import("../api/client");
    mocks.apiGet.mockImplementation(() =>
      Promise.reject(new ApiError(500, "INTERNAL", "database exploded")),
    );

    renderList();

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/database exploded/);
  });

  it("registers a server from the Add server dialog", async () => {
    const page: Page<ServerSummary> = { items: [makeServer()], total: 1, limit: 20, offset: 0 };
    mocks.apiGet.mockImplementation(() => Promise.resolve(page));
    const created = makeServer({ id: "srv-new", name: "new-box", hostname: "newbox.example.net" });
    mocks.apiPost.mockImplementation(() => Promise.resolve(created));

    renderList();

    await screen.findByText("edge-01");
    fireEvent.click(screen.getByRole("button", { name: "+ Add server" }));

    fireEvent.change(screen.getByLabelText("Name *"), { target: { value: "new-box" } });
    fireEvent.change(screen.getByLabelText("Hostname *"), {
      target: { value: "newbox.example.net" },
    });
    fireEvent.change(screen.getByLabelText("Environment"), { target: { value: "staging" } });

    fireEvent.click(screen.getByRole("button", { name: "Register server" }));

    await waitFor(() => {
      expect(mocks.apiPost).toHaveBeenCalledWith(
        "/servers",
        expect.objectContaining({
          name: "new-box",
          hostname: "newbox.example.net",
          environment: "staging",
        }),
      );
    });
    expect(await screen.findByText(/new-box registered/)).toBeInTheDocument();
  });
});
