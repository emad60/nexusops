import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi, type Mock } from "vitest";
import { ApiError, apiGet, apiPost } from "../api/client";
import type { IncidentOut } from "../api/types";
import { ToastProvider } from "../components/toast";
import IncidentDetailPage from "./IncidentDetailPage";

vi.mock("../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/client")>();
  return { ...actual, apiGet: vi.fn(), apiPost: vi.fn(), apiPatch: vi.fn(), apiDelete: vi.fn() };
});

vi.mock("../auth/AuthContext", () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: () => ({
    user: null,
    permissions: ["monitor.read", "incident.action"],
    superadmin: false,
    initializing: false,
    login: vi.fn(),
    logout: vi.fn(),
    refreshProfile: vi.fn(),
    hasPermission: () => true,
  }),
}));

// Live feed: mocked so tests are deterministic and open no sockets.
vi.mock("../hooks/useEventStream", () => ({ useEventStream: vi.fn() }));

const mockedGet = apiGet as unknown as Mock;
const mockedPost = apiPost as unknown as Mock;

const INCIDENT_ID = "f47ac10b-58cc-4372-a567-0e02b2c3d479";

const incident: IncidentOut & {
  timeline?: Array<{ id: string; kind: string; message: string; occurred_at: string }>;
  detected_at?: string | null;
} = {
  id: INCIDENT_ID,
  monitor_id: "mon-1",
  monitor_name: "Marketing site",
  title: "Marketing site is DOWN",
  severity: "CRITICAL",
  status: "OPEN",
  failure_count: 4,
  opened_at: "2026-09-10T11:55:00Z",
  detected_at: "2026-09-10T11:55:20Z",
  acknowledged_at: null,
  resolved_at: null,
  resolution: "",
  created_at: "2026-09-10T11:55:00Z",
  timeline: [
    {
      id: "ev-1",
      kind: "OPENED",
      message: "Opened after 4 consecutive failing checks",
      occurred_at: "2026-09-10T11:55:00Z",
    },
    {
      id: "ev-2",
      kind: "DETECTED",
      message: "Detection error: connection refused",
      occurred_at: "2026-09-10T11:55:20Z",
    },
    {
      id: "ev-3",
      kind: "NOTIFIED",
      message: "WEBHOOK channel Ops webhook",
      occurred_at: "2026-09-10T11:55:25Z",
    },
    {
      id: "ev-4",
      kind: "NOTIFIED",
      message: "EMAIL channel oncall",
      occurred_at: "2026-09-10T11:55:26Z",
    },
  ],
};

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/incidents/${INCIDENT_ID}`]}>
        <ToastProvider>
          <Routes>
            <Route path="/incidents/:incidentId" element={<IncidentDetailPage />} />
          </Routes>
        </ToastProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  mockedGet.mockImplementation((path: string) => {
    if (path === `/incidents/${INCIDENT_ID}`) return Promise.resolve(incident);
    return Promise.reject(new ApiError(404, "NOT_FOUND", `unhandled path ${path}`));
  });
});

describe("IncidentDetailPage", () => {
  it("renders details, timeline events and the notification count", async () => {
    renderPage();

    expect(await screen.findByRole("heading", { name: /Marketing site is DOWN/ })).toBeInTheDocument();
    expect(screen.getByText("Timeline")).toBeInTheDocument();
    expect(screen.getByText("Opened after 4 consecutive failing checks")).toBeInTheDocument();
    expect(screen.getByText("Detection error: connection refused")).toBeInTheDocument();
    // Notifications card summarises NOTIFIED events (also shown on the timeline).
    expect(screen.getByText("Notifications sent")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getAllByText(/WEBHOOK channel Ops webhook/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByRole("link", { name: "Marketing site" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Acknowledge" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Resolve" })).toBeInTheDocument();
  });

  it("acknowledges the incident through the dialog", async () => {
    mockedPost.mockResolvedValue({ ...incident, status: "ACKNOWLEDGED" });

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Acknowledge" }));
    const dialog = screen.getByRole("dialog", { name: "Acknowledge incident" });
    fireEvent.change(within(dialog).getByLabelText("Note (optional)"), {
      target: { value: "Investigating now" },
    });
    fireEvent.click(within(dialog).getByRole("button", { name: "Acknowledge" }));

    await waitFor(() => {
      expect(mockedPost).toHaveBeenCalledWith(`/incidents/${INCIDENT_ID}/acknowledge`, {
        note: "Investigating now",
      });
    });
  });

  it("requires a resolution note to resolve the incident", async () => {
    mockedPost.mockResolvedValue({ ...incident, status: "RESOLVED", resolved_at: "2026-09-10T12:20:00Z" });

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Resolve" }));

    const dialog = screen.getByRole("dialog", { name: "Resolve incident" });
    fireEvent.change(within(dialog).getByLabelText("Resolution"), {
      target: { value: "Recovered after redeploy" },
    });
    fireEvent.click(within(dialog).getByRole("button", { name: "Resolve incident" }));

    await waitFor(() => {
      expect(mockedPost).toHaveBeenCalledWith(`/incidents/${INCIDENT_ID}/resolve`, {
        resolution: "Recovered after redeploy",
      });
    });
  });

  it("shows a readable error when the incident cannot be loaded", async () => {
    mockedGet.mockRejectedValue(new ApiError(404, "NOT_FOUND", "Incident not found"));
    renderPage();
    expect(await screen.findByText(/Error \(NOT_FOUND\): Incident not found/)).toBeInTheDocument();
  });
});
