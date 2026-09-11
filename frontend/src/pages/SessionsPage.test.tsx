import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../api/client";
import type { Page, SessionInfo } from "../api/types";
import { ToastProvider } from "../components/toast";
import SessionsPage from "./SessionsPage";

const mocks = vi.hoisted(() => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
}));

vi.mock("../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/client")>();
  return { ...actual, ...mocks };
});

function makeSession(over: Partial<SessionInfo> & { id: string; device_label: string }): SessionInfo {
  return {
    ip_address: "10.0.0.5",
    user_agent: "Mozilla/5.0",
    created_at: "2026-06-01T09:00:00Z",
    last_seen_at: "2026-09-09T08:00:00Z",
    expires_at: "2026-12-01T09:00:00Z",
    current: false,
    ...over,
  };
}

const CURRENT = makeSession({ id: "s-1", device_label: "MacBook Pro", current: true });
const OTHER = makeSession({
  id: "s-2",
  device_label: "Pixel 8",
  ip_address: "203.0.113.9",
  user_agent: "Chrome Mobile",
});

const SESSIONS_PAGE: Page<SessionInfo> = {
  items: [CURRENT, OTHER],
  total: 2,
  limit: 100,
  offset: 0,
};

// No AuthProvider needed: sessions are self-service by definition.
function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <SessionsPage />
        </ToastProvider>
      </QueryClientProvider>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  mocks.apiGet.mockImplementation((path: string) => {
    if (path === "/sessions") return Promise.resolve(SESSIONS_PAGE);
    return Promise.reject(new ApiError(404, "NOT_FOUND", `unexpected GET ${path}`));
  });
  mocks.apiPost.mockResolvedValue({});
  mocks.apiDelete.mockResolvedValue({});
});

describe("SessionsPage", () => {
  it("renders sessions and marks the current one", async () => {
    renderPage();

    expect(await screen.findByText("MacBook Pro")).toBeInTheDocument();
    expect(screen.getByText("Pixel 8")).toBeInTheDocument();
    expect(screen.getByText("This session")).toBeInTheDocument();
    expect(screen.getByText("203.0.113.9")).toBeInTheDocument();
  });

  it("cannot revoke the current session", async () => {
    renderPage();
    await screen.findByText("MacBook Pro");

    expect(screen.getByRole("button", { name: "Revoke session on MacBook Pro" })).toBeDisabled();
    expect(mocks.apiDelete).not.toHaveBeenCalled();
  });

  it("revokes another session and invalidates the list", async () => {
    renderPage();
    await screen.findByText("Pixel 8");

    fireEvent.click(screen.getByRole("button", { name: "Revoke session on Pixel 8" }));

    await waitFor(() => expect(mocks.apiDelete).toHaveBeenCalledWith("/sessions/s-2"));
    expect(await screen.findByText("Revoked the session on Pixel 8")).toBeInTheDocument();
  });

  it("revokes all other sessions in one action", async () => {
    renderPage();
    await screen.findByText("Pixel 8");

    fireEvent.click(screen.getByRole("button", { name: "Revoke other sessions" }));

    await waitFor(() => expect(mocks.apiDelete).toHaveBeenCalledWith("/sessions/s-2"));
    expect(mocks.apiDelete).not.toHaveBeenCalledWith("/sessions/s-1");
    expect(await screen.findByText("Revoked 1 other session")).toBeInTheDocument();
  });

  it("shows the empty state when there are no sessions", async () => {
    mocks.apiGet.mockImplementation((path: string) => {
      if (path === "/sessions") {
        return Promise.resolve({
          items: [],
          total: 0,
          limit: 100,
          offset: 0,
        } satisfies Page<SessionInfo>);
      }
      return Promise.reject(new ApiError(404, "NOT_FOUND", `unexpected GET ${path}`));
    });
    renderPage();

    expect(await screen.findByText("No active sessions")).toBeInTheDocument();
  });
});
