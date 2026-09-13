import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi, type Mock } from "vitest";
import { ApiError, apiGet, apiPost } from "../api/client";
import type { MonitorOut, Page } from "../api/types";
import { ToastProvider } from "../components/toast";
import MonitorListPage from "./MonitorListPage";

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

function makeMonitor(overrides: Partial<MonitorOut> = {}): MonitorOut {
  return {
    id: "m1",
    name: "Marketing site",
    url: "https://example.com/health",
    method: "GET",
    interval_seconds: 60,
    timeout_seconds: 10,
    expected_status: 200,
    enabled: true,
    status: "UP",
    consecutive_failures: 0,
    consecutive_successes: 12,
    failure_threshold: 3,
    success_threshold: 2,
    next_check_at: "2026-09-10T12:00:00Z",
    last_check_at: "2026-09-10T11:59:30Z",
    last_success_at: "2026-09-10T11:59:30Z",
    last_failure_at: null,
    project_name: null,
    current_open_incident_id: null,
    uptime_pct_24h: 99.95,
    created_at: "2026-09-01T00:00:00Z",
    ...overrides,
  };
}

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ToastProvider>
          <MonitorListPage />
        </ToastProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  mockedGet.mockResolvedValue({
    items: [],
    total: 0,
    limit: 25,
    offset: 0,
  } satisfies Page<MonitorOut>);
});

describe("MonitorListPage", () => {
  it("renders monitors from the API with status and pagination", async () => {
    mockedGet.mockResolvedValue({
      items: [
        makeMonitor(),
        makeMonitor({
          id: "m2",
          name: "Billing API",
          url: "https://billing.internal/health",
          status: "DOWN",
          current_open_incident_id: "inc-9",
        }),
      ],
      total: 2,
      limit: 25,
      offset: 0,
    } satisfies Page<MonitorOut>);

    renderPage();

    expect(await screen.findByText("Marketing site")).toBeInTheDocument();
    expect(screen.getByText("Billing API")).toBeInTheDocument();
    // "UP"/"DOWN" appear both as status-filter options and as row badges.
    expect(screen.getAllByText("UP").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("DOWN").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("incident open")).toBeInTheDocument();
    expect(screen.getByText(/Showing 1–2 of 2/)).toBeInTheDocument();
    expect(mockedGet).toHaveBeenCalledWith(
      "/monitors",
      expect.objectContaining({ limit: 25, offset: 0 }),
      expect.anything(),
    );
  });

  it("shows the empty state when no monitors exist", async () => {
    renderPage();
    expect(await screen.findByText("No monitors yet")).toBeInTheDocument();
  });

  it("shows a readable error when the API call fails", async () => {
    mockedGet.mockRejectedValue(new ApiError(500, "SERVER_ERROR", "database exploded"));
    renderPage();
    expect(await screen.findByText(/Error \(SERVER_ERROR\): database exploded/)).toBeInTheDocument();
  });

  it("creates a monitor through the dialog", async () => {
    mockedPost.mockResolvedValue(makeMonitor());

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "+ New monitor" }));

    fireEvent.change(await screen.findByLabelText("Name *"), {
      target: { value: "Checkout API" },
    });
    fireEvent.change(screen.getByLabelText("Target URL *"), {
      target: { value: "https://checkout.internal/health" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create monitor" }));

    await waitFor(() => {
      expect(mockedPost).toHaveBeenCalledWith("/monitors", {
        name: "Checkout API",
        url: "https://checkout.internal/health",
        method: "GET",
        interval_seconds: 60,
      });
    });
  });

  it("surfaces SSRF_BLOCKED errors readably in the create dialog", async () => {
    mockedPost.mockRejectedValue(
      new ApiError(422, "SSRF_BLOCKED", "Target address is not allowed"),
    );

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "+ New monitor" }));
    fireEvent.change(await screen.findByLabelText("Name *"), { target: { value: "Evil" } });
    fireEvent.change(screen.getByLabelText("Target URL *"), {
      target: { value: "http://169.254.169.254/latest" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create monitor" }));

    // The message surfaces in both the dialog error block and the toast.
    expect((await screen.findAllByText(/SSRF guard/)).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Target address is not allowed/).length).toBeGreaterThan(0);
  });

  it("pauses a monitor with the pause action", async () => {
    mockedGet.mockResolvedValue({
      items: [makeMonitor({ enabled: true })],
      total: 1,
      limit: 25,
      offset: 0,
    } satisfies Page<MonitorOut>);
    mockedPost.mockResolvedValue(makeMonitor({ enabled: false, status: "PAUSED" }));

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Pause" }));

    await waitFor(() => {
      expect(mockedPost).toHaveBeenCalledWith("/monitors/m1/pause");
    });
  });
});
