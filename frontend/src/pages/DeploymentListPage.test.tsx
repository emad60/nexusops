/** Tests for DeploymentListPage: table render, filters, empty/error states, trigger flow. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi, type Mock } from "vitest";

import { ApiError, apiGet, apiPost } from "../api/client";
import { AuthProvider } from "../auth/AuthContext";
import { ToastProvider } from "../components/toast";
import DeploymentListPage from "./DeploymentListPage";

vi.mock("../api/client", () => {
  class ApiError extends Error {
    status: number;
    code: string;
    details?: unknown;
    constructor(status: number, code: string, message: string, details?: unknown) {
      super(message);
      this.name = "ApiError";
      this.status = status;
      this.code = code;
      this.details = details;
    }
  }
  return {
    API_BASE: "/api/v1",
    ApiError,
    apiGet: vi.fn(),
    apiPost: vi.fn(),
    apiPatch: vi.fn(),
    apiDelete: vi.fn(),
    apiRequest: vi.fn(),
    setAccessToken: vi.fn(),
    getAccessToken: vi.fn(() => null),
    refreshToken: vi.fn(async () => false),
  };
});

const get = apiGet as unknown as Mock;
const post = apiPost as unknown as Mock;

const ME = {
  user: {
    id: "u1",
    email: "owner@nexusops.test",
    full_name: "Owner",
    is_active: true,
    status: "ACTIVE",
    role_id: "r1",
    role_name: "Owner",
    last_login_at: null,
    created_at: "2026-01-01T00:00:00Z",
  },
  role: "Owner",
  permissions: ["*"],
  superadmin: true,
};

function deploymentRow(overrides: Record<string, unknown> = {}) {
  return {
    id: "dep-1",
    number: 12,
    application_id: "app-1",
    environment_id: "env-1",
    version: "1.4.2",
    git_commit: "a1b2c3d4e5",
    notes: "",
    status: "RUNNING",
    trigger: "MANUAL",
    is_rollback: false,
    triggered_by_email: "owner@nexusops.test",
    queued_at: "2026-09-10T08:00:00Z",
    started_at: "2026-09-10T08:00:05Z",
    finished_at: null,
    duration_ms: null,
    failure_reason: "",
    cancel_requested: false,
    application: { id: "app-1", name: "platform-api", slug: "platform-api" },
    environment: { id: "env-1", name: "production", slug: "production" },
    steps_total: 3,
    steps_success: 1,
    steps_failed: 0,
    steps_running: 1,
    steps_skipped: 0,
    steps_cancelled: 0,
    steps_pending: 1,
    created_at: "2026-09-10T08:00:00Z",
    updated_at: "2026-09-10T08:00:05Z",
    ...overrides,
  };
}

const PAGE_ONE = {
  items: [deploymentRow()],
  total: 1,
  limit: 20,
  offset: 0,
};

const EMPTY_PAGE = { items: [], total: 0, limit: 20, offset: 0 };

const PROJECTS_PAGE = {
  items: [
    {
      id: "p1",
      name: "Delivery Co",
      description: "",
      repository_url: "",
      default_branch: "main",
      created_at: "2026-01-01T00:00:00Z",
      applications: [
        {
          id: "app-1",
          project_id: "p1",
          name: "platform-api",
          slug: "platform-api",
          description: "",
          repository_url: "",
          build_config: {},
          current_version: null,
          created_at: "2026-01-01T00:00:00Z",
        },
      ],
    },
  ],
  total: 1,
  limit: 100,
  offset: 0,
};

const ENVS_PAGE = {
  items: [
    {
      id: "env-1",
      application_id: "app-1",
      name: "production",
      slug: "production",
      server_id: null,
      healthcheck_path: "",
      auto_deploy: false,
      config: {},
      created_at: "2026-01-01T00:00:00Z",
    },
  ],
  total: 1,
  limit: 100,
  offset: 0,
};

function renderPage(): ReturnType<typeof render> {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <AuthProvider>
          <MemoryRouter initialEntries={["/deployments"]}>
            <Routes>
              <Route path="/deployments" element={<DeploymentListPage />} />
              <Route path="/deployments/:deploymentId" element={<div>deployment detail probe</div>} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      </ToastProvider>
    </QueryClientProvider>,
  );
}

describe("DeploymentListPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    get.mockImplementation(async (path: string) => {
      if (path === "/auth/me") return ME;
      if (path === "/deployments") return PAGE_ONE;
      if (path === "/projects") return PROJECTS_PAGE;
      if (path.startsWith("/projects/applications/")) return ENVS_PAGE;
      throw new ApiError(404, "NOT_FOUND", `unexpected GET ${path}`);
    });
    post.mockResolvedValue(deploymentRow({ id: "dep-9", number: 13, status: "QUEUED" }));
  });

  it("renders the deployment table with application, environment, status and version", async () => {
    renderPage();
    expect(await screen.findByText("platform-api")).toBeInTheDocument();
    expect(screen.getByText("production")).toBeInTheDocument();
    expect(screen.getByText("1.4.2")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
  });

  it("shows the empty state when there are no deployments", async () => {
    get.mockImplementation(async (path: string) => {
      if (path === "/auth/me") return ME;
      if (path === "/deployments") return EMPTY_PAGE;
      throw new ApiError(404, "NOT_FOUND", `unexpected GET ${path}`);
    });
    renderPage();
    expect(await screen.findByText("No deployments found")).toBeInTheDocument();
  });

  it("shows the error state when the API fails", async () => {
    get.mockImplementation(async (path: string) => {
      if (path === "/auth/me") return ME;
      throw new ApiError(503, "UNAVAILABLE", "database down");
    });
    renderPage();
    expect(await screen.findByText(/UNAVAILABLE/)).toBeInTheDocument();
    expect(screen.getByText(/database down/)).toBeInTheDocument();
  });

  it("re-queries with the selected status filter", async () => {
    renderPage();
    await screen.findByText("platform-api");
    fireEvent.change(screen.getByLabelText("Filter by status"), { target: { value: "FAILED" } });
    await waitFor(() =>
      expect(get).toHaveBeenCalledWith(
        "/deployments",
        expect.objectContaining({ status: "FAILED" }),
        expect.anything(),
      ),
    );
  });

  it("queues a deployment through the trigger dialog and opens its detail page", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Trigger deployment" }));
    expect(
      await screen.findByRole("heading", { name: "Trigger deployment" }),
    ).toBeInTheDocument();

    // Wait for the application option before selecting it.
    await screen.findByRole("option", { name: "platform-api — Delivery Co" });
    fireEvent.change(screen.getByLabelText("Application"), { target: { value: "app-1" } });
    // Environment options load for the selected application.
    await waitFor(() =>
      expect(get).toHaveBeenCalledWith(
        "/projects/applications/app-1/environments",
        expect.objectContaining({ limit: 100 }),
        expect.anything(),
      ),
    );
    await screen.findByRole("option", { name: "production" });
    fireEvent.change(screen.getByLabelText("Environment"), { target: { value: "env-1" } });
    fireEvent.change(screen.getByLabelText("Version"), { target: { value: "2.0.0" } });
    fireEvent.click(screen.getByRole("button", { name: "Queue deployment" }));

    await waitFor(() =>
      expect(post).toHaveBeenCalledWith(
        "/deployments/applications/app-1/deployments",
        expect.objectContaining({ environment_id: "env-1", version: "2.0.0" }),
      ),
    );
    expect(await screen.findByText("deployment detail probe")).toBeInTheDocument();
  });
});
