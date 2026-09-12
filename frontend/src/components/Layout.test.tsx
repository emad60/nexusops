import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "../auth/AuthContext";
import { Layout } from "./Layout";

const mocks = vi.hoisted(() => ({
  apiGet: vi.fn(),
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

// The real hook opens a WebSocket; the badge logic under test needs none.
vi.mock("../hooks/useEventStream", () => ({
  useEventStream: vi.fn(),
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

function mockApi(meta: unknown) {
  mocks.apiGet.mockImplementation((path: string) => {
    if (path === "/auth/me") return Promise.resolve(ME);
    if (path === "/meta") return Promise.resolve(meta);
    if (path === "/alerts/unread-count") return Promise.resolve({ count: 0 });
    return Promise.reject(new Error(`unexpected GET ${path}`));
  });
}

async function renderLayout() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  const utils = render(
    <MemoryRouter initialEntries={["/"]}>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Routes>
            <Route element={<Layout />}>
              <Route index element={<div>Page marker</div>} />
            </Route>
          </Routes>
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
});

describe("Layout", () => {
  it("hides the simulation badge on a production instance", async () => {
    mockApi({ environment: "production", simulation_mode: false });
    await renderLayout();

    expect(screen.getByText("Page marker")).toBeInTheDocument();
    // The badge is gated on the runtime /meta flag — it must never render
    // from a stale default (regression: it used to be unconditional).
    expect(screen.queryByText("SIMULATION MODE")).not.toBeInTheDocument();
  });

  it("keeps the badge hidden while /meta has not answered", async () => {
    let resolveMeta!: (value: unknown) => void;
    mocks.apiGet.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(ME);
      if (path === "/meta") return new Promise((resolve) => (resolveMeta = resolve));
      if (path === "/alerts/unread-count") return Promise.resolve({ count: 0 });
      return Promise.reject(new Error(`unexpected GET ${path}`));
    });
    await renderLayout();

    expect(screen.queryByText("SIMULATION MODE")).not.toBeInTheDocument();

    act(() => resolveMeta({ environment: "production", simulation_mode: false }));

    await act(async () => {});
    expect(screen.queryByText("SIMULATION MODE")).not.toBeInTheDocument();
  });

  it("shows the simulation badge when the instance runs simulated", async () => {
    mockApi({ environment: "development", simulation_mode: true });
    await renderLayout();

    expect(await screen.findByText("SIMULATION MODE")).toBeInTheDocument();
  });
});
