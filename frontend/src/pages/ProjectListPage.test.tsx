/** Tests for ProjectListPage: card grid with counts, empty state, create flow. */

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi, type Mock } from "vitest";

import { ApiError, apiGet, apiPost } from "../api/client";
import { AuthProvider } from "../auth/AuthContext";
import { ToastProvider } from "../components/toast";
import ProjectListPage from "./ProjectListPage";

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

function application(id: string, name: string) {
  return {
    id,
    project_id: "p1",
    name,
    slug: name,
    description: "",
    repository_url: "",
    build_config: {},
    current_version: null,
    created_at: "2026-01-01T00:00:00Z",
  };
}

function project(id: string, name: string, apps: ReturnType<typeof application>[]) {
  return {
    id,
    name,
    description: `${name} description`,
    repository_url: `https://github.com/org/${name}`,
    default_branch: "main",
    created_at: "2026-01-01T00:00:00Z",
    applications: apps,
  };
}

const PROJECTS_PAGE = {
  items: [
    project("p1", "Alpha", [application("app-1", "web"), application("app-2", "api")]),
    project("p2", "Beta", [application("app-3", "worker")]),
  ],
  total: 2,
  limit: 24,
  offset: 0,
};

const EMPTY_PAGE = { items: [], total: 0, limit: 24, offset: 0 };

function envPage(total: number) {
  return {
    items: [],
    total,
    limit: 1,
    offset: 0,
  };
}

function renderPage(): ReturnType<typeof render> {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <AuthProvider>
          <MemoryRouter initialEntries={["/projects"]}>
            <Routes>
              <Route path="/projects" element={<ProjectListPage />} />
              <Route path="/projects/:projectId" element={<div>project detail probe</div>} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      </ToastProvider>
    </QueryClientProvider>,
  );
}

describe("ProjectListPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    get.mockImplementation(async (path: string) => {
      if (path === "/auth/me") return ME;
      if (path === "/projects") return PROJECTS_PAGE;
      if (path === "/projects/applications/app-1/environments") return envPage(2);
      if (path === "/projects/applications/app-2/environments") return envPage(3);
      if (path === "/projects/applications/app-3/environments") return envPage(0);
      throw new ApiError(404, "NOT_FOUND", `unexpected GET ${path}`);
    });
    post.mockResolvedValue({
      id: "p9",
      name: "Gallery",
      description: "",
      repository_url: "",
      default_branch: "main",
      created_at: "2026-09-10T00:00:00Z",
      applications: [],
    });
  });

  it("renders project cards with application and environment counts", async () => {
    renderPage();
    const alpha = await screen.findByRole("region", { name: "Project Alpha" });
    expect(within(alpha).getByText("2")).toBeInTheDocument();
    // Environment counts arrive from per-application count queries.
    await within(alpha).findByText("5");
    const beta = screen.getByRole("region", { name: "Project Beta" });
    expect(within(beta).getByText("1")).toBeInTheDocument();
    await within(beta).findByText("0");
  });

  it("shows the empty state when there are no projects", async () => {
    get.mockImplementation(async (path: string) => {
      if (path === "/auth/me") return ME;
      if (path === "/projects") return EMPTY_PAGE;
      throw new ApiError(404, "NOT_FOUND", `unexpected GET ${path}`);
    });
    renderPage();
    expect(await screen.findByText("No projects yet")).toBeInTheDocument();
  });

  it("shows the error state when the API fails", async () => {
    get.mockImplementation(async (path: string) => {
      if (path === "/auth/me") return ME;
      throw new ApiError(503, "UNAVAILABLE", "redis down");
    });
    renderPage();
    expect(await screen.findByText(/redis down/)).toBeInTheDocument();
  });

  it("creates a project through the dialog and opens its detail page", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "New project" }));
    expect(await screen.findByRole("heading", { name: "New project" })).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "Gallery" } });
    fireEvent.click(screen.getByRole("button", { name: "Create project" }));

    await waitFor(() =>
      expect(post).toHaveBeenCalledWith(
        "/projects",
        expect.objectContaining({ name: "Gallery", default_branch: "main" }),
      ),
    );
    expect(await screen.findByText("project detail probe")).toBeInTheDocument();
  });
});
