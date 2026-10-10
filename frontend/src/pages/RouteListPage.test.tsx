import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi, type Mock } from "vitest";
import { ApiError, apiDelete, apiGet, apiPost } from "../api/client";
import type {
  DomainOut,
  NodeProxyStatusOut,
  Page,
  RouteOut,
  ServerSummary,
  UpstreamContainerOut,
} from "../api/types";
import { ToastProvider } from "../components/toast";
import RouteListPage from "./RouteListPage";

vi.mock("../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/client")>();
  return { ...actual, apiGet: vi.fn(), apiPost: vi.fn(), apiPatch: vi.fn(), apiDelete: vi.fn() };
});

vi.mock("../auth/AuthContext", () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
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

const mockedGet = apiGet as unknown as Mock;
const mockedPost = apiPost as unknown as Mock;
const mockedDelete = apiDelete as unknown as Mock;

function makeRoute(overrides: Partial<RouteOut> = {}): RouteOut {
  return {
    id: "r1",
    domain_id: "d1",
    domain_name: "example.com",
    hostname: "app.example.com",
    path: "/",
    url: "http://app.example.com/",
    node_id: "n1",
    node_name: "node-1",
    container_id: "c1",
    container_name: "web",
    container_ref: "a".repeat(64),
    port: 8080,
    scheme: "http",
    enabled: true,
    config_state: "IN_SYNC",
    headers: [],
    rate_limit: null,
    redirect: null,
    monitor_id: "m1",
    monitor_optout: false,
    last_applied_at: "2026-10-10T12:00:00Z",
    last_bundle_id: "f".repeat(64),
    last_apply_error: "",
    removal_state: null,
    removal_requested_at: null,
    removal_confirmed_at: null,
    status_detail: "The node is serving this route.",
    created_at: "2026-10-09T00:00:00Z",
    updated_at: "2026-10-10T12:00:00Z",
    ...overrides,
  };
}

const DOMAIN: DomainOut = {
  id: "d1",
  name: "example.com",
  status: "VERIFIED",
  verified: true,
  verified_at: "2026-10-09T10:00:00Z",
  last_checked_at: null,
  proof_lost_at: null,
  stale_expires_at: null,
  attempt_count: 1,
  last_error: "",
  ns_snapshot: [],
  project_id: null,
  project_name: null,
  verification: null,
  reachability: null,
  route_count: 1,
  enabled_route_count: 1,
  created_at: "2026-10-08T00:00:00Z",
  updated_at: "2026-10-10T00:00:00Z",
};

const NODE: ServerSummary = {
  id: "n1",
  name: "node-1",
  hostname: "node-1.example.com",
  ip_address: "10.0.0.5",
  os_name: "Ubuntu",
  os_version: "24.04",
  arch: "x86_64",
  environment: "PROD",
  location: "",
  description: "",
  status: "ONLINE",
  cpu_cores: 4,
  memory_total_mb: 8192,
  disk_total_gb: 200,
  agent_version: "1.2.0",
  enrolled: true,
  simulated: false,
  heartbeat_interval_seconds: 30,
  offline_after_seconds: 90,
  uptime_seconds: 86400,
  tags: [],
  docker_host: null,
  last_heartbeat_at: "2026-10-10T12:00:00Z",
  created_at: "2026-10-01T00:00:00Z",
};

const TARGET: UpstreamContainerOut = {
  id: "c1",
  container_id: "a".repeat(64),
  name: "web",
  image_ref: "nginx:1.27",
  status: "RUNNING",
  upstream_ports: [
    {
      host_port: 8080,
      container_port: 80,
      protocol: "tcp",
      bind_address: "127.0.0.1",
      upstream_host: "127.0.0.1",
    },
  ],
  unavailable_reason: null,
};

const PROXY: NodeProxyStatusOut = {
  id: "p1",
  node_id: "n1",
  node_name: "node-1",
  provider: "nginx",
  capability: {
    present: true,
    version: "1.27.5",
    running: true,
    config_test_ok: true,
    routing_eligible: true,
    reason: "",
    listener_80: "MANAGED",
    listener_443: "FREE",
  },
  eligible: true,
  ineligible_reason: "",
  expected_bundle_id: null,
  live_bundle_id: null,
  drift: false,
  last_status_at: null,
  last_status_error: "",
  route_total: 1,
  route_enabled: 1,
  route_in_sync: 1,
  route_stale: 0,
  route_failed: 0,
  route_removal_pending: 0,
  last_applied_at: null,
  last_apply_error: "",
  created_at: "2026-10-01T00:00:00Z",
  updated_at: "2026-10-10T12:00:00Z",
};

function mockApi(routes: Page<RouteOut>) {
  mockedGet.mockImplementation((path: string) => {
    if (path === "/routes") return Promise.resolve(routes);
    if (path === "/domains") {
      return Promise.resolve({ items: [DOMAIN], total: 1, limit: 100, offset: 0 });
    }
    if (path === "/nodes") {
      return Promise.resolve({ items: [NODE], total: 1, limit: 100, offset: 0 });
    }
    if (path === "/nodes/n1/route-targets") return Promise.resolve([TARGET]);
    if (path === "/nodes/n1/proxy/status") return Promise.resolve(PROXY);
    return Promise.reject(new Error(`unexpected GET ${path}`));
  });
}

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ToastProvider>
          <RouteListPage />
        </ToastProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  mockApi({ items: [], total: 0, limit: 25, offset: 0 });
});

describe("RouteListPage", () => {
  it("renders routes with their applied state", async () => {
    mockApi({ items: [makeRoute()], total: 1, limit: 25, offset: 0 });
    renderPage();

    expect(await screen.findByText("app.example.com/")).toBeInTheDocument();
    expect(screen.getByText("example.com")).toBeInTheDocument();
    expect(screen.getByText("node-1")).toBeInTheDocument();
    expect(screen.getAllByText("IN_SYNC").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Showing 1–1 of 1/)).toBeInTheDocument();
  });

  it("shows the empty state when no routes exist", async () => {
    renderPage();
    expect(await screen.findByText("No routes yet")).toBeInTheDocument();
  });

  it("shows a readable error when the API call fails", async () => {
    mockedGet.mockRejectedValue(new ApiError(500, "SERVER_ERROR", "database exploded"));
    renderPage();
    expect(await screen.findByText(/Error \(SERVER_ERROR\): database exploded/)).toBeInTheDocument();
  });

  it("disables an enabled route", async () => {
    mockApi({ items: [makeRoute({ enabled: true })], total: 1, limit: 25, offset: 0 });
    mockedPost.mockResolvedValue(makeRoute({ enabled: false }));

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Disable" }));

    await waitFor(() => expect(mockedPost).toHaveBeenCalledWith("/routes/r1/disable"));
  });

  it("enables a disabled route", async () => {
    mockApi({
      items: [makeRoute({ enabled: false, config_state: "PENDING" })],
      total: 1,
      limit: 25,
      offset: 0,
    });
    mockedPost.mockResolvedValue(makeRoute({ enabled: true }));

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Enable" }));

    await waitFor(() => expect(mockedPost).toHaveBeenCalledWith("/routes/r1/enable"));
  });

  it("distinguishes a requested removal from a confirmed one", async () => {
    // Both rows are STALE. Only the removal half may say whether the name can
    // still be answering, so the two must not render the same label.
    mockApi({
      items: [
        makeRoute({
          id: "r-pending",
          config_state: "STALE",
          removal_state: "REQUESTED",
          removal_requested_at: "2026-10-11T09:00:00Z",
          last_apply_error: "the domain is unverified",
          status_detail: "Removal requested — the domain is unverified; the node has not confirmed the removal, so it may still be serving it",
        }),
        makeRoute({
          id: "r-confirmed",
          config_state: "STALE",
          removal_state: "CONFIRMED",
          removal_requested_at: "2026-10-11T09:00:00Z",
          removal_confirmed_at: "2026-10-11T09:05:00Z",
          last_apply_error: "the domain is unverified",
          status_detail: "Removal confirmed — the domain is unverified; the node applied a configuration without this route, so it is no longer served",
        }),
      ],
      total: 2,
      limit: 25,
      offset: 0,
    });

    renderPage();

    const pending = await screen.findByText("removal pending");
    expect(pending.getAttribute("title")).toContain("may still be serving it");
    const confirmed = await screen.findByText("removal confirmed");
    expect(confirmed.getAttribute("title")).toContain("no longer served");
    // Exactly one of each: neither label leaks onto the other row.
    expect(screen.getAllByText("removal pending")).toHaveLength(1);
    expect(screen.getAllByText("removal confirmed")).toHaveLength(1);
  });

  it("deletes a route after confirmation", async () => {
    mockApi({ items: [makeRoute()], total: 1, limit: 25, offset: 0 });
    mockedDelete.mockResolvedValue(undefined);

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Delete" }));
    fireEvent.click(await screen.findByRole("button", { name: "Delete route" }));

    await waitFor(() => expect(mockedDelete).toHaveBeenCalledWith("/routes/r1"));
  });

  it("surfaces the node pre-flight refusal in the create dialog", async () => {
    mockedPost.mockRejectedValue(
      new ApiError(409, "NGINX_PREFLIGHT_FAILED", "port 80 is held by another process"),
    );
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "+ New route" }));

    // Every select is populated by its own query, so each option has to exist
    // before a controlled change can take effect.
    await screen.findByRole("option", { name: /example.com/ });
    fireEvent.change(screen.getByLabelText("Domain *"), { target: { value: "d1" } });
    await screen.findByRole("option", { name: "node-1" });
    fireEvent.change(screen.getByLabelText("Node *"), { target: { value: "n1" } });

    // The container + port selects are populated from the node's route targets.
    await screen.findByRole("option", { name: "web" });
    fireEvent.change(screen.getByLabelText("Container *"), { target: { value: "c1" } });
    await screen.findByRole("option", { name: /8080/ });
    fireEvent.change(screen.getByLabelText("Published port *"), {
      target: { value: "8080" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create & enable" }));

    await waitFor(() =>
      expect(mockedPost).toHaveBeenCalledWith(
        "/routes",
        expect.objectContaining({ domain_id: "d1", node_id: "n1", container_id: "c1", port: 8080, enabled: true }),
      ),
    );
    expect(
      (await screen.findAllByText(/did not pass its nginx pre-flight/)).length,
    ).toBeGreaterThan(0);
  });
});
