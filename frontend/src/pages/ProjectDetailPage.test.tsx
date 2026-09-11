/** Tests for ProjectDetailPage: applications + environments render (config refs as-is),
 * create-environment flow and edit-application flow. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi, type Mock } from "vitest";

import { ApiError, apiGet, apiPatch, apiPost } from "../api/client";
import { AuthProvider } from "../auth/AuthContext";
import { ToastProvider } from "../components/toast";
import ProjectDetailPage from "./ProjectDetailPage";

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
const patch = apiPatch as unknown as Mock;

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

function application(id: string, name: string, overrides: Record<string, unknown> = {}) {
  return {
    id,
    project_id: "p1",
    name,
    slug: name,
    description: `${name} service`,
    repository_url: `https://github.com/org/${name}`,
    build_config: { dockerfile: "Dockerfile" },
    current_version: "1.4.2",
    latest_deployment: {
      number: 12,
      status: "SUCCESS",
      version: "1.4.2",
      finished_at: "2026-09-09T10:00:00Z",
    },
    created_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

const PROJECT = {
  id: "p1",
  name: "Delivery Co",
  description: "Logistics platform",
  repository_url: "https://github.com/org/delivery",
  default_branch: "main",
  created_at: "2026-01-01T00:00:00Z",
  applications: [
    application("app-1", "platform-api"),
    application("app-2", "worker", { latest_deployment: null, current_version: null }),
  ],
};

function envPage(items: Record<string, unknown>[]) {
  return { items, total: items.length, limit: 100, offset: 0 };
}

const PROD_ENV = {
  id: "env-1",
  application_id: "app-1",
  name: "production",
  slug: "production",
  server_id: null,
  healthcheck_path: "/healthz",
  auto_deploy: true,
  config: { DATABASE_URL: "${secret:DATABASE_URL}", LOG_LEVEL: "info" },
  created_at: "2026-01-01T00:00:00Z",
};

const EMPTY_SERVERS = { items: [], total: 0, limit: 100, offset: 0 };

function renderPage(): ReturnType<typeof render> {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <AuthProvider>
          <MemoryRouter initialEntries={["/projects/p1"]}>
            <Routes>
              <Route path="/projects" element={<div>projects list probe</div>} />
              <Route path="/projects/:projectId" element={<ProjectDetailPage />} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      </ToastProvider>
    </QueryClientProvider>,
  );
}

describe("ProjectDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    get.mockImplementation(async (path: string) => {
      if (path === "/auth/me") return ME;
      if (path === "/projects/p1") return PROJECT;
      if (path === "/projects/applications/app-1/environments") return envPage([PROD_ENV]);
      if (path === "/projects/applications/app-2/environments") return envPage([]);
      if (path === "/servers") return EMPTY_SERVERS;
      throw new ApiError(404, "NOT_FOUND", `unexpected GET ${path}`);
    });
    post.mockResolvedValue({
      ...PROD_ENV,
      id: "env-9",
      name: "staging",
      auto_deploy: false,
    });
    patch.mockResolvedValue({
      ...PROJECT.applications[0],
      name: "platform-api-v2",
    });
  });

  it("renders applications with environments and shows config refs as-is", async () => {
    renderPage();
    expect(await screen.findByText("platform-api")).toBeInTheDocument();
    expect(screen.getByText("worker")).toBeInTheDocument();
    // Environments load per application.
    expect(await screen.findByText("production")).toBeInTheDocument();
    expect(await screen.findByText("engine-local")).toBeInTheDocument();
    // The worker application has never deployed.
    expect(screen.getByText("never deployed")).toBeInTheDocument();
    // Secret references are displayed exactly as stored — never resolved.
    expect(
      screen.getByText(/DATABASE_URL=\$\{secret:DATABASE_URL\}/),
    ).toBeInTheDocument();
    expect(screen.getByText("LOG_LEVEL=info")).toBeInTheDocument();
  });

  it("creates an environment through the dialog with config parsed from KEY=VALUE lines", async () => {
    renderPage();
    await screen.findByText("platform-api");
    const addButtons = screen.getAllByRole("button", { name: "+ Add environment" });
    fireEvent.click(addButtons[0]);

    expect(await screen.findByRole("heading", { name: "New environment" })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "staging" } });
    fireEvent.change(screen.getByLabelText(/Config \(one KEY=VALUE per line\)/), {
      target: { value: "LOG_LEVEL=debug\nAPI_TOKEN=${secret:API_TOKEN}" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Create environment" }));

    await waitFor(() =>
      expect(post).toHaveBeenCalledWith(
        "/projects/applications/app-1/environments",
        expect.objectContaining({
          name: "staging",
          server_id: null,
          config: { LOG_LEVEL: "debug", API_TOKEN: "${secret:API_TOKEN}" },
        }),
      ),
    );
  });

  it("edits an application through the dialog", async () => {
    renderPage();
    await screen.findByText("platform-api");
    fireEvent.click(screen.getByRole("button", { name: "Edit application platform-api" }));
    expect(
      await screen.findByRole("heading", { name: "Edit application platform-api" }),
    ).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "platform-api-v2" } });
    fireEvent.click(screen.getByRole("button", { name: "Save changes" }));

    await waitFor(() =>
      expect(patch).toHaveBeenCalledWith(
        "/projects/p1/applications/app-1",
        expect.objectContaining({ name: "platform-api-v2" }),
      ),
    );
  });

  it("shows the not-found state for a missing project", async () => {
    get.mockImplementation(async (path: string) => {
      if (path === "/auth/me") return ME;
      throw new ApiError(404, "NOT_FOUND", "no such project");
    });
    renderPage();
    expect(await screen.findByText("Project not found")).toBeInTheDocument();
  });
});
