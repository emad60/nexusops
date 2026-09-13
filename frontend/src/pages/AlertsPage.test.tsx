import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi, type Mock } from "vitest";
import { ApiError, apiGet, apiPatch, apiPost } from "../api/client";
import type { AlertOut, ChannelOut, CursorPage, DeliveryOut, Page } from "../api/types";
import { ToastProvider } from "../components/toast";
import AlertsPage from "./AlertsPage";

vi.mock("../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/client")>();
  return { ...actual, apiGet: vi.fn(), apiPost: vi.fn(), apiPatch: vi.fn(), apiDelete: vi.fn() };
});

const mockHasPermission = vi.fn((_codename: string) => true);

vi.mock("../auth/AuthContext", () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: () => ({
    user: null,
    permissions: [],
    superadmin: false,
    initializing: false,
    login: vi.fn(),
    logout: vi.fn(),
    refreshProfile: vi.fn(),
    hasPermission: (codename: string) => mockHasPermission(codename),
  }),
}));

const mockedGet = apiGet as unknown as Mock;
const mockedPost = apiPost as unknown as Mock;
const mockedPatch = apiPatch as unknown as Mock;

const unreadAlert: AlertOut = {
  id: "a1",
  severity: "CRITICAL",
  title: "Marketing site is DOWN",
  body: "4 consecutive failing checks",
  event_type: "INCIDENT_OPENED",
  source: "monitor_runner",
  resource_type: "incident",
  resource_id: "inc-1",
  read_at: null,
  created_at: "2026-09-10T11:55:00Z",
};

const readAlert: AlertOut = {
  ...unreadAlert,
  id: "a2",
  severity: "INFO",
  title: "Deploy finished",
  event_type: "DEPLOYMENT_FINISHED",
  read_at: "2026-09-10T12:00:00Z",
};

const webhookChannel: ChannelOut = {
  id: "ch-1",
  name: "Ops webhook",
  type: "WEBHOOK",
  display_target: "https://hooks.example.com/…8f2",
  events: ["INCIDENT_OPENED", "MONITOR_DOWN"],
  enabled: true,
  created_at: "2026-09-01T00:00:00Z",
};

const delivery: DeliveryOut = {
  id: "d1",
  channel_id: "ch-1",
  event_type: "INCIDENT_OPENED",
  subject: "[CRITICAL] Marketing site is DOWN",
  status: "SENT",
  attempts: 1,
  last_error: "",
  sent_at: "2026-09-10T11:55:25Z",
  created_at: "2026-09-10T11:55:25Z",
};

function setupApi() {
  mockedGet.mockImplementation((path: string) => {
    if (path === "/alerts") {
      return Promise.resolve({
        items: [unreadAlert, readAlert],
        total: 2,
        limit: 15,
        offset: 0,
      } satisfies Page<AlertOut>);
    }
    if (path === "/alerts/unread-count") return Promise.resolve({ count: 1 });
    if (path === "/notification-channels") {
      return Promise.resolve({
        items: [webhookChannel],
        total: 1,
        limit: 50,
        offset: 0,
      } satisfies Page<ChannelOut>);
    }
    if (path === "/notification-channels/deliveries") {
      return Promise.resolve({
        items: [delivery],
        next_cursor: null,
        has_more: false,
      } satisfies CursorPage<DeliveryOut>);
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
      <MemoryRouter>
        <ToastProvider>
          <AlertsPage />
        </ToastProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  mockHasPermission.mockReturnValue(true);
  setupApi();
});

describe("AlertsPage", () => {
  it("renders the alert inbox, notification channels and deliveries", async () => {
    renderPage();

    expect(await screen.findByText("Marketing site is DOWN")).toBeInTheDocument();
    expect(screen.getByText("1 unread")).toBeInTheDocument();
    expect(screen.getByText("Notification channels")).toBeInTheDocument();
    expect(screen.getByText("Ops webhook")).toBeInTheDocument();
    expect(screen.getByText("https://hooks.example.com/…8f2")).toBeInTheDocument();
    expect(screen.getByText("Recent deliveries")).toBeInTheDocument();
    expect(screen.getByText("[CRITICAL] Marketing site is DOWN")).toBeInTheDocument();
  });

  it("marks a single alert as read", async () => {
    mockedPost.mockResolvedValue({ ...unreadAlert, read_at: "2026-09-10T12:30:00Z" });

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Mark read" }));

    await waitFor(() => {
      expect(mockedPost).toHaveBeenCalledWith("/alerts/a1/read");
    });
  });

  it("marks all alerts as read in one action", async () => {
    mockedPost.mockResolvedValue({ count: 1 });

    renderPage();
    // Wait for the unread count so the button is enabled before clicking.
    expect(await screen.findByText("1 unread")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Mark all read" }));

    await waitFor(() => {
      expect(mockedPost).toHaveBeenCalledWith("/alerts/read-all");
    });
  });

  it("creates a webhook channel through the dialog", async () => {
    mockedPost.mockResolvedValue(webhookChannel);

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "+ New channel" }));

    const dialog = screen.getByRole("dialog", { name: "New notification channel" });
    fireEvent.change(within(dialog).getByLabelText("Name *"), { target: { value: "Pagerduty" } });
    fireEvent.change(within(dialog).getByLabelText("Webhook URL *"), {
      target: { value: "https://hooks.example.com/pd" },
    });
    fireEvent.click(within(dialog).getByRole("button", { name: "Create channel" }));

    await waitFor(() => {
      expect(mockedPost).toHaveBeenCalledWith("/notification-channels", {
        name: "Pagerduty",
        type: "WEBHOOK",
        events: [],
        enabled: true,
        config: { url: "https://hooks.example.com/pd" },
      });
    });
  });

  it("keeps the stored target when editing a channel with an empty config", async () => {
    mockedPatch.mockResolvedValue(webhookChannel);

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Edit" }));

    const dialog = screen.getByRole("dialog", { name: "Edit channel Ops webhook" });
    // Name is prefilled, the stored target is never echoed — leave the config
    // field empty and save: the PATCH must omit `config` so nothing changes.
    fireEvent.click(within(dialog).getByRole("button", { name: "Save changes" }));

    await waitFor(() => {
      expect(mockedPatch).toHaveBeenCalledWith("/notification-channels/ch-1", {
        name: "Ops webhook",
        enabled: true,
        events: ["INCIDENT_OPENED", "MONITOR_DOWN"],
      });
    });
  });

  it("hides channels and deliveries without channel.read permission", async () => {
    mockHasPermission.mockReturnValue(false);

    renderPage();

    expect(
      await screen.findByText("Your role does not include permission to view notification channels."),
    ).toBeInTheDocument();
    const fetchedPaths = mockedGet.mock.calls.map((call) => call[0] as string);
    expect(fetchedPaths).not.toContain("/notification-channels");
    expect(fetchedPaths).not.toContain("/notification-channels/deliveries");
  });

  it("shows a readable error when the inbox cannot be loaded", async () => {
    mockedGet.mockImplementation((path: string) => {
      if (path === "/alerts") {
        return Promise.reject(new ApiError(503, "DATABASE_DOWN", "cannot reach storage"));
      }
      return Promise.reject(new ApiError(404, "NOT_FOUND", `unhandled path ${path}`));
    });

    renderPage();
    expect(await screen.findByText(/Error \(DATABASE_DOWN\): cannot reach storage/)).toBeInTheDocument();
  });
});
