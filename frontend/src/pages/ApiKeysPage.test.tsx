import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../api/client";
import type { ApiKeyOut, Page } from "../api/types";
import { ToastProvider } from "../components/toast";
import ApiKeysPage from "./ApiKeysPage";

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

function makeKey(over: Partial<ApiKeyOut> & { id: string; name: string }): ApiKeyOut {
  return {
    key_prefix: "nxk_1a2b3c",
    scopes: ["server.read", "monitor.read"],
    last_used_at: null,
    expires_at: null,
    revoked_at: null,
    created_at: "2026-03-01T00:00:00Z",
    ...over,
  };
}

const CI_KEY = makeKey({ id: "k-1", name: "CI key" });

const KEYS_PAGE: Page<ApiKeyOut> = { items: [CI_KEY], total: 1, limit: 25, offset: 0 };

// No AuthProvider needed: key management is fully self-service.
function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <ApiKeysPage />
        </ToastProvider>
      </QueryClientProvider>
    </MemoryRouter>,
  );
}

function defaultGet(path: string): Promise<unknown> {
  if (path === "/api-keys") return Promise.resolve(KEYS_PAGE);
  return Promise.reject(new ApiError(404, "NOT_FOUND", `unexpected GET ${path}`));
}

beforeEach(() => {
  vi.clearAllMocks();
  mocks.apiGet.mockImplementation(defaultGet);
  mocks.apiPost.mockResolvedValue({});
  mocks.apiDelete.mockResolvedValue({});
});

describe("ApiKeysPage", () => {
  it("renders the key list with prefix, scopes and usage metadata", async () => {
    renderPage();

    expect(await screen.findByText("CI key")).toBeInTheDocument();
    expect(screen.getByText("nxk_1a2b3c…")).toBeInTheDocument();
    expect(screen.getByText("server.read")).toBeInTheDocument();
    // Both "last used" and "expires" render "Never" for this fixture.
    expect(screen.getAllByText("Never")).toHaveLength(2);
    expect(screen.getByRole("button", { name: "Revoke CI key" })).toBeInTheDocument();
  });

  it("creates a scoped key and shows the raw secret exactly once", async () => {
    mocks.apiPost.mockResolvedValue({
      ...makeKey({ id: "k-2", name: "Deploy key", scopes: ["server.read"] }),
      key: "nxk_raw_secret_value",
    });
    renderPage();
    await screen.findByText("CI key");

    fireEvent.click(screen.getByRole("button", { name: "Create key" }));
    fireEvent.change(screen.getByLabelText("Key name"), { target: { value: "Deploy key" } });
    fireEvent.click(screen.getByLabelText(/server\.read/));
    fireEvent.click(screen.getByRole("button", { name: "Generate key" }));

    await waitFor(() =>
      expect(mocks.apiPost).toHaveBeenCalledWith("/api-keys", {
        name: "Deploy key",
        scopes: ["server.read"],
        expires_in_days: null,
      }),
    );
    expect(await screen.findByText("nxk_raw_secret_value")).toBeInTheDocument();
    expect(screen.getByText(/only this once/i)).toBeInTheDocument();
  });

  it("makes explicit scopes exclusive with the full-access wildcard", async () => {
    renderPage();
    await screen.findByText("CI key");

    fireEvent.click(screen.getByRole("button", { name: "Create key" }));
    fireEvent.click(screen.getByLabelText(/Full access/));
    expect(screen.getByLabelText(/server\.read/)).toBeDisabled();

    fireEvent.click(screen.getByLabelText(/Full access/));
    expect(screen.getByLabelText(/server\.read/)).toBeEnabled();
    fireEvent.click(screen.getByLabelText(/server\.read/));
    expect(screen.getByLabelText(/container\.read/)).toBeEnabled();
  });

  it("revokes a key after confirmation", async () => {
    renderPage();
    await screen.findByText("CI key");

    fireEvent.click(screen.getByRole("button", { name: "Revoke CI key" }));
    fireEvent.click(screen.getByRole("button", { name: "Revoke key" }));

    await waitFor(() => expect(mocks.apiDelete).toHaveBeenCalledWith("/api-keys/k-1"));
    expect(await screen.findByText("Revoked API key CI key")).toBeInTheDocument();
  });

  it("shows the empty state when no keys exist", async () => {
    mocks.apiGet.mockImplementation((path: string) => {
      if (path === "/api-keys") {
        return Promise.resolve({ items: [], total: 0, limit: 25, offset: 0 } satisfies Page<ApiKeyOut>);
      }
      return Promise.reject(new ApiError(404, "NOT_FOUND", `unexpected GET ${path}`));
    });
    renderPage();

    expect(await screen.findByText("No API keys yet")).toBeInTheDocument();
  });
});
