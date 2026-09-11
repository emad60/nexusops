import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi, type Mock } from "vitest";
import { ApiError, apiGet } from "../api/client";
import type { IncidentOut, Page } from "../api/types";
import { ToastProvider } from "../components/toast";
import IncidentListPage from "./IncidentListPage";

vi.mock("../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/client")>();
  return { ...actual, apiGet: vi.fn(), apiPost: vi.fn(), apiPatch: vi.fn(), apiDelete: vi.fn() };
});

vi.mock("../auth/AuthContext", () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: () => ({
    user: null,
    permissions: ["monitor.read"],
    superadmin: false,
    initializing: false,
    login: vi.fn(),
    logout: vi.fn(),
    refreshProfile: vi.fn(),
    hasPermission: () => true,
  }),
}));

// The live feed is exercised elsewhere; tests stay deterministic (no sockets).
vi.mock("../hooks/useEventStream", () => ({ useEventStream: vi.fn() }));

const mockedGet = apiGet as unknown as Mock;

function makeIncident(overrides: Partial<IncidentOut> = {}): IncidentOut {
  return {
    id: "inc-1",
    monitor_id: "mon-1",
    monitor_name: "Marketing site",
    title: "Marketing site is DOWN",
    severity: "CRITICAL",
    status: "OPEN",
    failure_count: 4,
    opened_at: "2026-09-10T11:55:00Z",
    acknowledged_at: null,
    resolved_at: null,
    resolution: "",
    created_at: "2026-09-10T11:55:00Z",
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
          <IncidentListPage />
        </ToastProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  mockedGet.mockResolvedValue({ items: [], total: 0, limit: 25, offset: 0 } satisfies Page<IncidentOut>);
});

describe("IncidentListPage", () => {
  it("renders incidents with severity, status and monitor links", async () => {
    mockedGet.mockResolvedValue({
      items: [
        makeIncident(),
        makeIncident({
          id: "inc-2",
          monitor_id: "mon-2",
          monitor_name: "Billing API",
          title: "Billing API latency spike",
          severity: "MINOR",
          status: "RESOLVED",
          resolved_at: "2026-09-10T12:10:00Z",
          resolution: "Recovered after rollback",
        }),
      ],
      total: 2,
      limit: 25,
      offset: 0,
    } satisfies Page<IncidentOut>);

    renderPage();

    expect(await screen.findByText("Marketing site is DOWN")).toBeInTheDocument();
    expect(screen.getByText("Billing API latency spike")).toBeInTheDocument();
    expect(screen.getAllByText("CRITICAL").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("MINOR").length).toBeGreaterThanOrEqual(1);
    // RESOLVED appears both as a filter option and as a row badge.
    expect(screen.getAllByText("RESOLVED").length).toBeGreaterThanOrEqual(2);
    expect(screen.getByText(/Showing 1–2 of 2/)).toBeInTheDocument();
    expect(mockedGet).toHaveBeenCalledWith(
      "/incidents",
      expect.objectContaining({ limit: 25, offset: 0 }),
      expect.anything(),
    );
  });

  it("filters by status through the status select", async () => {
    renderPage();

    fireEvent.change(await screen.findByLabelText("Status"), { target: { value: "OPEN" } });

    await waitFor(() => {
      expect(mockedGet).toHaveBeenCalledWith(
        "/incidents",
        expect.objectContaining({ status: "OPEN" }),
        expect.anything(),
      );
    });
  });

  it("shows the healthy empty state", async () => {
    renderPage();
    expect(await screen.findByText("No incidents — all monitors healthy")).toBeInTheDocument();
  });

  it("shows a readable error when the API call fails", async () => {
    mockedGet.mockRejectedValue(new ApiError(503, "DATABASE_DOWN", "cannot reach storage"));
    renderPage();
    expect(await screen.findByText(/Error \(DATABASE_DOWN\): cannot reach storage/)).toBeInTheDocument();
  });
});
