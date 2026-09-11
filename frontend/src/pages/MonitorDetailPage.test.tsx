import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi, type Mock } from "vitest";
import { ApiError, apiGet, apiPatch, apiPost } from "../api/client";
import type { CheckOut, CursorPage, IncidentOut, MonitorOut, Page } from "../api/types";
import { ToastProvider } from "../components/toast";
import MonitorDetailPage from "./MonitorDetailPage";

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
const mockedPatch = apiPatch as unknown as Mock;

const MONITOR_ID = "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d";

const monitor: MonitorOut = {
  id: MONITOR_ID,
  name: "Marketing site",
  url: "https://example.com/health",
  method: "GET",
  interval_seconds: 60,
  timeout_seconds: 10,
  expected_status: 200,
  enabled: true,
  status: "UP",
  consecutive_failures: 0,
  consecutive_successes: 42,
  failure_threshold: 3,
  success_threshold: 2,
  next_check_at: "2026-09-10T12:01:00Z",
  last_check_at: "2026-09-10T12:00:00Z",
  last_success_at: "2026-09-10T12:00:00Z",
  last_failure_at: null,
  project_name: "Website",
  current_open_incident_id: null,
  uptime_pct_24h: 99.9,
  created_at: "2026-09-01T00:00:00Z",
};

const check: CheckOut = {
  id: 101,
  monitor_id: MONITOR_ID,
  checked_at: "2026-09-10T12:00:00Z",
  result: "SUCCESS",
  response_time_ms: 132.4,
  status_code: 200,
  error: "",
};

const emptyIncidents = { items: [], total: 0, limit: 5, offset: 0 } satisfies Page<IncidentOut>;

function setupApi(overrides: {
  monitor?: MonitorOut;
  checks?: CursorPage<CheckOut>;
} = {}) {
  mockedGet.mockImplementation((path: string) => {
    if (path === `/monitors/${MONITOR_ID}`) {
      return Promise.resolve(overrides.monitor ?? monitor);
    }
    if (path === `/monitors/${MONITOR_ID}/checks`) {
      return Promise.resolve(
        overrides.checks ?? { items: [check], next_cursor: null, has_more: false },
      );
    }
    if (path === `/monitors/${MONITOR_ID}/uptime`) {
      return Promise.resolve({
        uptime_pct: 99.92,
        total_checks: 1440,
        failed_checks: 1,
        avg_response_ms: 140.2,
        p95_response_ms: 310.5,
      });
    }
    if (path === `/monitors/${MONITOR_ID}/incidents`) {
      return Promise.resolve(emptyIncidents);
    }
    return Promise.reject(new ApiError(404, "NOT_FOUND", `unhandled path ${path}`));
  });
}

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/monitors/${MONITOR_ID}`]}>
        <ToastProvider>
          <Routes>
            <Route path="/monitors/:monitorId" element={<MonitorDetailPage />} />
          </Routes>
        </ToastProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  setupApi();
});

describe("MonitorDetailPage", () => {
  it("renders configuration, uptime stats and recent checks", async () => {
    renderPage();

    expect(await screen.findByRole("heading", { name: /Marketing site/ })).toBeInTheDocument();
    expect(screen.getByText("Configuration")).toBeInTheDocument();
    // The target URL shows in the subtitle and in the config card.
    expect(screen.getAllByText("https://example.com/health").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Website")).toBeInTheDocument();
    // Uptime aggregate from /uptime.
    expect(await screen.findByText("99.92%")).toBeInTheDocument();
    // Latency cell in the recent-checks table.
    expect(screen.getByText("132 ms")).toBeInTheDocument();
    expect(screen.getByText(/HTTP 200/)).toBeInTheDocument();
    expect(screen.getByText("Status timeline")).toBeInTheDocument();
  });

  it("shows the empty state when the monitor has no check history", async () => {
    setupApi({ checks: { items: [], next_cursor: null, has_more: false } });
    renderPage();

    expect(await screen.findByText("No checks recorded yet")).toBeInTheDocument();
    expect(screen.getByText("No check history yet")).toBeInTheDocument();
  });

  it("shows a readable error when the monitor cannot be loaded", async () => {
    mockedGet.mockRejectedValue(new ApiError(404, "NOT_FOUND", "Monitor not found"));
    renderPage();
    expect(await screen.findByText(/Error \(NOT_FOUND\): Monitor not found/)).toBeInTheDocument();
  });

  it("runs an on-demand check with the check-now action", async () => {
    mockedPost.mockResolvedValue({
      ...check,
      result: "TIMEOUT",
      response_time_ms: null,
      status_code: null,
      error: "connect timeout",
    });

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Check now" }));

    await waitFor(() => {
      expect(mockedPost).toHaveBeenCalledWith(`/monitors/${MONITOR_ID}/check-now`);
    });
    expect(await screen.findByText(/Check finished with result TIMEOUT/)).toBeInTheDocument();
  });

  it("saves edits through the edit dialog", async () => {
    mockedPatch.mockResolvedValue({ ...monitor, interval_seconds: 120 });

    renderPage();

    fireEvent.click(await screen.findByRole("button", { name: "Edit" }));
    fireEvent.change(await screen.findByLabelText("Interval (seconds)"), {
      target: { value: "120" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save changes" }));

    await waitFor(() => {
      expect(mockedPatch).toHaveBeenCalledWith(
        `/monitors/${MONITOR_ID}`,
        expect.objectContaining({ interval_seconds: 120 }),
      );
    });
  });
});
