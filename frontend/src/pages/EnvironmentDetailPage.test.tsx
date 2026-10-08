/** Tests for EnvironmentDetailPage: config layering (project base vs environment
 * overrides vs effective), the override editor, secret metadata panel and the
 * environment's deployments. */

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi, type Mock } from "vitest";

import { ApiError, apiGet, apiPatch, apiPost } from "../api/client";
import { AuthProvider } from "../auth/AuthContext";
import { ToastProvider } from "../components/toast";
import EnvironmentDetailPage from "./EnvironmentDetailPage";

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
    getActiveOrgId: () => null,
    setActiveOrgId: vi.fn(),
    ORGANIZATION_HEADER: "X-Org-Id",
    getAccessToken: vi.fn(() => null),
    refreshToken: vi.fn(async () => false),
  };
});

const get = apiGet as unknown as Mock;
const patch = apiPatch as unknown as Mock;
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
  organizations: [
    {
      organization: {
        id: "org-1",
        name: "Acme",
        slug: "acme",
        description: "",
        status: "ACTIVE" as const,
        is_provisional: false,
        renamed_at: null,
        created_at: "2026-01-01T00:00:00Z",
      },
      role_name: "Owner",
      role_id: "r-1",
      status: "ACTIVE" as const,
    },
  ],
  active_organization_id: "org-1",
};

const DETAIL = {
  id: "env-1",
  project_id: "p1",
  name: "production",
  slug: "production",
  environment_type: "PROD" as const,
  server_id: null,
  healthcheck_path: "/healthz",
  auto_deploy: true,
  // Overrides only list the keys this environment changes.
  config: { LOG_LEVEL: "debug", DATABASE_URL: "${secret:DATABASE_URL}" },
  project_config: { LOG_LEVEL: "info", REGION: "eu" },
  effective_config: {
    LOG_LEVEL: "debug",
    REGION: "eu",
    DATABASE_URL: "${secret:DATABASE_URL}",
  },
  secret_references: ["DATABASE_URL"],
  application_count: 2,
  deployment_count: 3,
  secret_count: 1,
  created_at: "2026-01-01T00:00:00Z",
};

const ENV_SECRET = {
  id: "sec-1",
  key: "DATABASE_URL",
  version: 2,
  digest: "abcdef012345",
  description: "",
  project_id: "p1",
  environment_id: "env-1",
  rotated_at: null,
  rotated_by_email: null,
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-02-01T00:00:00Z",
};

const PROJECT_SECRET = {
  ...ENV_SECRET,
  id: "sec-2",
  key: "STRIPE_KEY",
  digest: "ffffffffffff",
  environment_id: null,
};

const DEPLOYMENT = {
  id: "d-1",
  number: 7,
  application_id: "app-1",
  environment_id: "env-1",
  version: "1.4.2",
  git_commit: "abc123",
  notes: "",
  status: "SUCCESS",
  trigger: "MANUAL",
  is_rollback: false,
  queued_at: "2026-02-01T00:00:00Z",
  started_at: "2026-02-01T00:00:05Z",
  finished_at: "2026-02-01T00:01:00Z",
  duration_ms: 55000,
  failure_reason: "",
  cancel_requested: false,
  application: { id: "app-1", name: "platform-api", slug: "platform-api" },
  environment: { id: "env-1", name: "production" },
  created_at: "2026-02-01T00:00:00Z",
};

function page(items: unknown[]) {
  return { items, total: items.length, limit: 100, offset: 0 };
}

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <AuthProvider>
          <MemoryRouter initialEntries={["/projects/p1/environments/env-1"]}>
            <Routes>
              <Route path="/projects/:projectId" element={<div>project page probe</div>} />
              <Route
                path="/projects/:projectId/environments/:environmentId"
                element={<EnvironmentDetailPage />}
              />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      </ToastProvider>
    </QueryClientProvider>,
  );
}

describe("EnvironmentDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    get.mockImplementation(async (path: string, params?: Record<string, unknown>) => {
      if (path === "/auth/me") return ME;
      if (path === "/projects/p1/environments/env-1") return DETAIL;
      if (path === "/projects/p1") {
        return {
          id: "p1",
          name: "Ymart",
          description: "",
          repository_url: "",
          default_branch: "main",
          config: { LOG_LEVEL: "info", REGION: "eu" },
          applications: [],
          environments: [],
          created_at: "2026-01-01T00:00:00Z",
        };
      }
      if (path === "/secrets") {
        return page(params?.environment_id ? [ENV_SECRET] : [PROJECT_SECRET]);
      }
      if (path === "/deployments") return page([DEPLOYMENT]);
      if (path === "/nodes") return page([]);
      if (path === "/secrets/sec-1/versions") {
        return [
          {
            id: "ver-2",
            secret_id: "sec-1",
            version: 2,
            digest: "abcdef012345",
            created_by_email: "owner@nexusops.test",
            created_at: "2026-02-01T00:00:00Z",
          },
        ];
      }
      throw new ApiError(404, "NOT_FOUND", `unexpected GET ${path}`);
    });
    patch.mockResolvedValue({ ...DETAIL, config: { LOG_LEVEL: "trace" } });
    post.mockResolvedValue({ ...ENV_SECRET, id: "sec-9", key: "NEW_KEY", version: 1 });
  });

  it("shows project base config, environment overrides and the effective config separately", async () => {
    renderPage();

    expect(await screen.findByRole("heading", { name: /production/ })).toBeInTheDocument();
    // Environment type is shown as a label, not as an access rule.
    expect(screen.getAllByText("Production").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/never an access rule/i)).toBeInTheDocument();

    // Project base configuration.
    expect(screen.getByText("LOG_LEVEL=info")).toBeInTheDocument();
    // REGION is inherited unchanged, so it appears in both base and effective.
    expect(screen.getAllByText("REGION=eu").length).toBe(2);
    // Overrides, including the secret reference — never resolved client-side.
    expect(screen.getAllByText(/LOG_LEVEL=debug/).length).toBeGreaterThanOrEqual(1);
    expect(
      screen.getAllByText(/DATABASE_URL=\$\{secret:DATABASE_URL\}/).length,
    ).toBeGreaterThanOrEqual(1);
    // The effective config carries the override value, not the project base one.
    expect(screen.getAllByText(/LOG_LEVEL=debug/).length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText(/overridden/).length).toBeGreaterThanOrEqual(1);
  });

  it("saves environment overrides as KEY=VALUE lines", async () => {
    renderPage();
    await screen.findByRole("heading", { name: /production/ });

    fireEvent.change(screen.getByLabelText(/Environment overrides/), {
      target: { value: "LOG_LEVEL=trace" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save overrides" }));

    await waitFor(() =>
      expect(patch).toHaveBeenCalledWith("/projects/p1/environments/env-1", {
        config: { LOG_LEVEL: "trace" },
      }),
    );
  });

  it("rejects malformed override lines without calling the API", async () => {
    renderPage();
    await screen.findByRole("heading", { name: /production/ });

    fireEvent.change(screen.getByLabelText(/Environment overrides/), {
      target: { value: "not-a-pair" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save overrides" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/expected KEY=VALUE/i);
    expect(patch).not.toHaveBeenCalled();
  });

  it("lists secret metadata for the environment and the project secrets it inherits", async () => {
    renderPage();

    expect(await screen.findByText("DATABASE_URL")).toBeInTheDocument();
    // Environment-scoped secret resolves here; the project one is inherited.
    expect(screen.getByText("STRIPE_KEY (v2)")).toBeInTheDocument();
    // The environment table owns the env-scoped row only.
    expect(screen.getByRole("button", { name: "Version history of DATABASE_URL" })).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Version history of STRIPE_KEY" }),
    ).not.toBeInTheDocument();
    // Metadata only — no value is ever rendered.
    expect(screen.getByText("abcdef012345")).toBeInTheDocument();
    expect(screen.getByText("v2")).toBeInTheDocument();
  });

  it("lists the environment's deployments", async () => {
    renderPage();
    expect(await screen.findByRole("link", { name: "#7" })).toBeInTheDocument();
    expect(screen.getByText("platform-api")).toBeInTheDocument();
  });

  it("opens the secret version history dialog from the environment", async () => {
    renderPage();
    await screen.findByText("DATABASE_URL");
    fireEvent.click(screen.getByRole("button", { name: "Version history of DATABASE_URL" }));

    const dialog = await screen.findByRole("dialog");
    expect(await within(dialog).findByText("v2")).toBeInTheDocument();
    expect(dialog).toHaveTextContent(/nothing is deleted or overwritten/i);
  });
});
