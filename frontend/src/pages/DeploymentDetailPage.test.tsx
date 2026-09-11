/** Tests for DeploymentDetailPage: render, live log frames, rollback flow, not-found state. */

import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi, type Mock } from "vitest";

import { ApiError, apiGet, apiPost } from "../api/client";
import { AuthProvider } from "../auth/AuthContext";
import { ToastProvider } from "../components/toast";
import DeploymentDetailPage from "./DeploymentDetailPage";

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

/** Deterministic WebSocket double; frames are injected by the tests. */
class FakeWebSocket {
  static instances: FakeWebSocket[] = [];
  url: string;
  readyState = 0;
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  sent: string[] = [];

  constructor(url: string) {
    this.url = url;
    FakeWebSocket.instances.push(this);
  }
  send(data: string): void {
    this.sent.push(data);
  }
  close(): void {
    this.readyState = 3;
  }
  open(): void {
    this.readyState = 1;
    this.onopen?.();
  }
  receive(frame: unknown): void {
    this.onmessage?.({ data: JSON.stringify(frame) });
  }
}

function step(idx: number, name: string, status: string, output = "") {
  return {
    id: `step-${idx}`,
    idx,
    name,
    status,
    output,
    error: "",
    retry_count: 0,
    started_at: status === "PENDING" ? null : "2026-09-10T08:00:05Z",
    finished_at: status === "SUCCESS" ? "2026-09-10T08:00:10Z" : null,
  };
}

function deploymentDetail(overrides: Record<string, unknown> = {}) {
  return {
    id: "dep-1",
    number: 12,
    application_id: "app-1",
    environment_id: "env-1",
    version: "1.4.2",
    git_commit: "a1b2c3d4e5",
    notes: "release notes",
    status: "RUNNING",
    trigger: "MANUAL",
    is_rollback: false,
    rollback_of_id: null,
    triggered_by_email: "owner@nexusops.test",
    failure_reason: "",
    cancel_requested: false,
    queued_at: "2026-09-10T08:00:00Z",
    started_at: "2026-09-10T08:00:05Z",
    finished_at: null,
    duration_ms: 65000,
    application: { id: "app-1", name: "platform-api", slug: "platform-api" },
    environment: { id: "env-1", name: "production", slug: "production" },
    steps: [
      step(0, "checkout", "SUCCESS", "cloned repo"),
      step(1, "build image", "RUNNING"),
      step(2, "deploy", "PENDING"),
    ],
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

const EMPTY_LOGS = { items: [], next_cursor: null, has_more: false };

function renderPage(): ReturnType<typeof render> {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={qc}>
      <ToastProvider>
        <AuthProvider>
          <MemoryRouter initialEntries={["/deployments/dep-1"]}>
            <Routes>
              <Route path="/deployments" element={<div>deployments list probe</div>} />
              <Route path="/deployments/:deploymentId" element={<DeploymentDetailPage />} />
            </Routes>
          </MemoryRouter>
        </AuthProvider>
      </ToastProvider>
    </QueryClientProvider>,
  );
}

describe("DeploymentDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    FakeWebSocket.instances = [];
    vi.stubGlobal("WebSocket", FakeWebSocket);
    get.mockImplementation(async (path: string) => {
      if (path === "/auth/me") return ME;
      if (path === "/deployments/dep-1") return deploymentDetail();
      if (path === "/deployments/dep-1/logs") return EMPTY_LOGS;
      if (path === "/deployments/dep-2")
        return deploymentDetail({ id: "dep-2", number: 13, status: "QUEUED", started_at: null });
      if (path === "/deployments/dep-2/logs") return EMPTY_LOGS;
      throw new ApiError(404, "NOT_FOUND", `unexpected GET ${path}`);
    });
    post.mockImplementation(async (path: string) => {
      if (path === "/deployments/dep-1/rollback")
        return deploymentDetail({ id: "dep-2", number: 13, status: "QUEUED" });
      throw new ApiError(400, "BAD_REQUEST", `unexpected POST ${path}`);
    });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders the status banner, duration and pipeline steps", async () => {
    renderPage();
    expect(await screen.findByText("build image")).toBeInTheDocument();
    expect(screen.getByText("checkout")).toBeInTheDocument();
    expect(screen.getByText("deploy")).toBeInTheDocument();
    expect(screen.getByText("1.4.2")).toBeInTheDocument();
    // duration_ms 65000 formats as 1m 5s
    expect(screen.getByText("1m 5s")).toBeInTheDocument();
    expect(screen.getByText("cloned repo")).toBeInTheDocument();
    expect(screen.getByText("1/3 steps succeeded")).toBeInTheDocument();
  });

  it("appends live log frames from the deployment-logs channel", async () => {
    renderPage();
    await screen.findByText("build image");
    const socket = FakeWebSocket.instances.at(-1);
    expect(socket).toBeDefined();

    await act(async () => {
      socket?.open();
    });
    await act(async () => {
      socket?.receive({
        type: "event",
        channel: "deployment-logs",
        params: { deployment_id: "dep-1" },
        data: {
          deployment_id: "dep-1",
          step_idx: 1,
          step: "build image",
          line: "pull ok",
          level: "INFO",
          ts: "2026-09-10T08:00:06Z",
        },
      });
    });
    // The live line appears both in the step output and the log console.
    const matches = await screen.findAllByText("pull ok");
    expect(matches.length).toBeGreaterThanOrEqual(1);
  });

  it("queues a rollback as a NEW deployment and navigates to it", async () => {
    get.mockImplementation(async (path: string) => {
      if (path === "/auth/me") return ME;
      if (path === "/deployments/dep-1")
        return deploymentDetail({ status: "SUCCESS", steps: [step(0, "deploy", "SUCCESS", "done")] });
      if (path === "/deployments/dep-1/logs") return EMPTY_LOGS;
      if (path === "/deployments/dep-2")
        return deploymentDetail({ id: "dep-2", number: 13, status: "QUEUED" });
      if (path === "/deployments/dep-2/logs") return EMPTY_LOGS;
      throw new ApiError(404, "NOT_FOUND", `unexpected GET ${path}`);
    });

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Roll back deployment 12" }));
    // The dialog labels the action as creating a NEW deployment.
    expect(await screen.findByText(/new deployment/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Queue rollback deployment" }));

    await waitFor(() =>
      expect(post).toHaveBeenCalledWith("/deployments/dep-1/rollback"),
    );
    await waitFor(() =>
      expect(get).toHaveBeenCalledWith("/deployments/dep-2", undefined, expect.anything()),
    );
  });

  it("shows the not-found state for a missing deployment", async () => {
    get.mockImplementation(async (path: string) => {
      if (path === "/auth/me") return ME;
      throw new ApiError(404, "NOT_FOUND", "no such deployment");
    });
    renderPage();
    expect(await screen.findByText("Deployment not found")).toBeInTheDocument();
  });
});
