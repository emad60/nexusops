import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ToastProvider } from "../components/toast";
import ContainerDetailPage from "./ContainerDetailPage";
import type { ContainerDetailData } from "./ContainerDetailPage";
import type { WsFrame } from "../hooks/useEventStream";

vi.mock("../api/client", () => {
  class ApiError extends Error {
    status: number;
    code: string;
    constructor(status: number, code: string, message: string) {
      super(message);
      this.status = status;
      this.code = code;
    }
  }
  return { apiGet: vi.fn(), apiPost: vi.fn(), apiPatch: vi.fn(), apiDelete: vi.fn(), apiRequest: vi.fn(), ApiError };
});

vi.mock("../hooks/useEventStream", () => ({ useEventStream: vi.fn() }));

vi.mock("../auth/AuthContext", () => ({
  useAuth: () => ({
    user: {
      id: "u-1",
      email: "ops@nexusops.local",
      full_name: "Ops Operator",
      is_active: true,
      status: "ACTIVE",
      role_id: null,
      role_name: "admin",
      last_login_at: null,
      created_at: "2026-01-01T00:00:00Z",
    },
    permissions: ["*"],
    superadmin: true,
    initializing: false,
    login: async () => {},
    logout: async () => {},
    refreshProfile: async () => {},
    hasPermission: () => true,
  }),
}));

import { apiGet, apiPost, apiRequest, ApiError } from "../api/client";
import { useEventStream } from "../hooks/useEventStream";

const CID = "c-1";

const detail: ContainerDetailData = {
  id: CID,
  container_id: "abc123def456",
  name: "web-proxy",
  image_ref: "nginx:1.25",
  status: "RUNNING",
  health: "HEALTHY",
  env_keys: ["TZ", "NGINX_PORT"],
  labels: { "app.k8s/name": "web" },
  ports: [{ private: 80, public: 8080, type: "tcp" }],
  mounts: [{ Type: "bind", Source: "/srv/site", Destination: "/usr/share/nginx/html" }],
  restart_count: 2,
  cpu_percent: 4.2,
  mem_used_mb: 220,
  mem_limit_mb: 512,
  net_rx_kb_s: 12.4,
  net_tx_kb_s: 8.1,
  started_at: "2026-09-01T00:00:00Z",
  finished_at: null,
  observed_at: "2026-09-10T12:00:00Z",
  simulated: false,
  host: { id: "h-1", name: "docker on build-01", status: "AVAILABLE" },
  server: { id: "srv-1", name: "build-01", status: "ONLINE" },
  command: "nginx -g 'daemon off;'",
};

// Backend returns logs newest-first.
const logsPage = {
  items: [
    { id: 2, ts: "2026-09-10T11:58:00Z", stream: "stdout", level: "INFO", message: "shutting down" },
    { id: 1, ts: "2026-09-10T10:00:00Z", stream: "stdout", level: "INFO", message: "listening on 8080" },
  ],
  next_cursor: null,
  has_more: false,
};

function renderDetail() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <MemoryRouter initialEntries={[`/containers/${CID}`]}>
          <Routes>
            <Route path="/containers" element={<div>containers list</div>} />
            <Route path="/containers/:containerId" element={<ContainerDetailPage />} />
            <Route path="/servers/:serverId" element={<div>server detail</div>} />
          </Routes>
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  );
}

function mockApi() {
  vi.mocked(apiGet).mockImplementation(async (path: string) => {
    if (path === `/containers/${CID}`) return detail;
    if (path === `/containers/${CID}/logs`) return logsPage;
    throw new Error(`unexpected path: ${path}`);
  });
}

beforeEach(() => {
  vi.mocked(apiGet).mockReset();
  vi.mocked(apiPost).mockReset();
  vi.mocked(apiRequest).mockReset();
  vi.mocked(useEventStream).mockClear();
  mockApi();
});

describe("ContainerDetailPage", () => {
  it("renders container facts, configuration and the server link", async () => {
    renderDetail();

    expect(await screen.findByText("web-proxy")).toBeInTheDocument();
    expect(screen.getByText("nginx:1.25")).toBeInTheDocument();
    // Header and the facts card both carry the health pill.
    expect((await screen.findAllByText("HEALTHY")).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("nginx -g 'daemon off;'")).toBeInTheDocument();
    expect(screen.getByText("8080 → 80/tcp")).toBeInTheDocument();
    expect(screen.getByText("NGINX_PORT")).toBeInTheDocument();
    expect(screen.getByText("/srv/site")).toBeInTheDocument();
    const serverLink = screen.getByRole("link", { name: "build-01" });
    expect(serverLink).toHaveAttribute("href", "/servers/srv-1");
  });

  it("shows the log history oldest-first", async () => {
    renderDetail();

    const viewer = await screen.findByRole("log");
    const first = within(viewer).getByText("listening on 8080");
    const second = within(viewer).getByText("shutting down");
    expect(first.compareDocumentPosition(second) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });

  it("appends live log frames from the container-logs stream", async () => {
    renderDetail();
    await screen.findByRole("log");

    expect(useEventStream).toHaveBeenCalledWith(
      [{ channel: "container-logs", params: { container_id: CID } }],
      expect.any(Function),
    );
    const onFrame = vi.mocked(useEventStream).mock.calls.at(-1)?.[1] as (frame: WsFrame) => void;

    act(() => {
      onFrame({
        type: "event",
        channel: "container-logs",
        params: { container_id: CID },
        data: { ts: "2026-09-10T12:01:00Z", stream: "stderr", message: "boom: crash detected" },
      });
    });

    expect(await screen.findByText("boom: crash detected")).toBeInTheDocument();
  });

  it("runs a lifecycle action, toasts and refreshes state", async () => {
    vi.mocked(apiPost).mockResolvedValue({ ...detail, status: "RESTARTING" });
    renderDetail();
    await screen.findByText("web-proxy");

    fireEvent.click(screen.getByRole("button", { name: "Restart" }));

    await screen.findByText(/restart accepted/i);
    expect(apiPost).toHaveBeenCalledWith(`/containers/${CID}/restart`);
  });

  it("shows an error toast when a lifecycle action fails", async () => {
    vi.mocked(apiPost).mockRejectedValue(
      new ApiError(409, "DOCKER_UNREACHABLE", "Docker host did not respond"),
    );
    renderDetail();
    await screen.findByText("web-proxy");

    fireEvent.click(screen.getByRole("button", { name: "Stop" }));

    expect(await screen.findByText(/DOCKER_UNREACHABLE/)).toBeInTheDocument();
    expect(screen.getByText(/Docker host did not respond/)).toBeInTheDocument();
  });

  it("gates removal behind typing the exact container name", async () => {
    vi.mocked(apiRequest).mockResolvedValue({ id: CID, removed: true });
    renderDetail();
    await screen.findByText("web-proxy");

    fireEvent.click(screen.getByRole("button", { name: "Remove" }));
    const input = await screen.findByLabelText("Container name");
    const confirmButton = screen.getByRole("button", { name: "Remove container" });

    expect(confirmButton).toBeDisabled();
    fireEvent.change(input, { target: { value: "wrong-name" } });
    expect(confirmButton).toBeDisabled();

    fireEvent.change(input, { target: { value: "web-proxy" } });
    expect(confirmButton).toBeEnabled();
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(apiRequest).toHaveBeenCalledWith(`/containers/${CID}`, {
        method: "DELETE",
        query: { confirm: "web-proxy" },
      });
    });
  });
});
