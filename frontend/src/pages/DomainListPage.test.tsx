import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi, type Mock } from "vitest";
import { ApiError, apiDelete, apiGet, apiPost } from "../api/client";
import type { DomainOut, Page } from "../api/types";
import { ToastProvider } from "../components/toast";
import DomainListPage from "./DomainListPage";

vi.mock("../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/client")>();
  return { ...actual, apiGet: vi.fn(), apiPost: vi.fn(), apiPatch: vi.fn(), apiDelete: vi.fn() };
});

vi.mock("../auth/AuthContext", () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: () => ({
    user: null,
    permissions: ["*"],
    superadmin: true,
    initializing: false,
    login: vi.fn(),
    logout: vi.fn(),
    refreshProfile: vi.fn(),
    hasPermission: () => true,
  }),
}));

const mockedGet = apiGet as unknown as Mock;
const mockedPost = apiPost as unknown as Mock;
const mockedDelete = apiDelete as unknown as Mock;

function makeDomain(overrides: Partial<DomainOut> = {}): DomainOut {
  return {
    id: "d1",
    name: "example.com",
    status: "VERIFIED",
    verified: true,
    verified_at: "2026-10-09T10:00:00Z",
    last_checked_at: "2026-10-10T09:00:00Z",
    proof_lost_at: null,
    stale_expires_at: null,
    attempt_count: 1,
    last_error: "",
    ns_snapshot: ["ns1.example.net"],
    project_id: null,
    project_name: null,
    verification: null,
    reachability: null,
    route_count: 2,
    enabled_route_count: 1,
    created_at: "2026-10-08T00:00:00Z",
    updated_at: "2026-10-10T09:00:00Z",
    ...overrides,
  };
}

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ToastProvider>
          <DomainListPage />
        </ToastProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  mockedGet.mockResolvedValue({ items: [], total: 0, limit: 25, offset: 0 } satisfies Page<DomainOut>);
});

describe("DomainListPage", () => {
  it("renders domains with status and route counts", async () => {
    mockedGet.mockResolvedValue({
      items: [
        makeDomain(),
        makeDomain({
          id: "d2",
          name: "pending.example.com",
          status: "PENDING",
          verified: false,
          verified_at: null,
          last_checked_at: null,
          route_count: 0,
          enabled_route_count: 0,
          last_error: "TXT_MISSING: no TXT record found",
        }),
      ],
      total: 2,
      limit: 25,
      offset: 0,
    } satisfies Page<DomainOut>);

    renderPage();

    expect(await screen.findByText("example.com")).toBeInTheDocument();
    expect(screen.getByText("pending.example.com")).toBeInTheDocument();
    expect(screen.getAllByText("VERIFIED").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("PENDING").length).toBeGreaterThanOrEqual(1);
    // enabled / total
    expect(screen.getByText("1 / 2")).toBeInTheDocument();
    expect(screen.getByText(/Showing 1–2 of 2/)).toBeInTheDocument();
  });

  it("shows the empty state when no domains exist", async () => {
    renderPage();
    expect(await screen.findByText("No domains yet")).toBeInTheDocument();
  });

  it("shows a readable error when the API call fails", async () => {
    mockedGet.mockRejectedValue(new ApiError(500, "SERVER_ERROR", "database exploded"));
    renderPage();
    expect(await screen.findByText(/Error \(SERVER_ERROR\): database exploded/)).toBeInTheDocument();
  });

  it("adds a domain through the dialog", async () => {
    mockedPost.mockResolvedValue(makeDomain());

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "+ Add domain" }));

    fireEvent.change(await screen.findByLabelText("Domain name *"), {
      target: { value: "checkout.example.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Add domain" }));

    await waitFor(() => {
      expect(mockedPost).toHaveBeenCalledWith("/domains", { name: "checkout.example.com" });
    });
  });

  it("records a domain conflict readably", async () => {
    mockedPost.mockRejectedValue(new ApiError(409, "DOMAIN_EXISTS", "already tracked"));
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "+ Add domain" }));
    fireEvent.change(await screen.findByLabelText("Domain name *"), {
      target: { value: "dup.example.com" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Add domain" }));

    expect(
      (await screen.findAllByText(/already tracked in this organization/)).length,
    ).toBeGreaterThan(0);
  });

  it("re-verifies a domain and deletes one after confirmation", async () => {
    mockedGet.mockResolvedValue({
      items: [makeDomain({ status: "PENDING", verified: false, verified_at: null })],
      total: 1,
      limit: 25,
      offset: 0,
    } satisfies Page<DomainOut>);
    mockedPost.mockResolvedValue(makeDomain());
    mockedDelete.mockResolvedValue(undefined);

    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Verify" }));
    await waitFor(() => expect(mockedPost).toHaveBeenCalledWith("/domains/d1/verify"));

    fireEvent.click(screen.getByRole("button", { name: "Delete" }));
    fireEvent.click(await screen.findByRole("button", { name: "Delete domain" }));
    await waitFor(() => expect(mockedDelete).toHaveBeenCalledWith("/domains/d1"));
  });
});
