import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../api/client";
import type { Page, Role } from "../api/types";
import { AuthProvider } from "../auth/AuthContext";
import { ToastProvider } from "../components/toast";
import RolesPage from "./RolesPage";

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

// Superadmin so role.manage is granted regardless of the permission list.
const ME = {
  user: {
    id: "u-self",
    email: "admin@example.com",
    full_name: "Ada Admin",
    is_active: true,
    status: "ACTIVE",
    role_id: "r-owner",
    role_name: "Owner",
    last_login_at: null,
    created_at: "2026-01-01T00:00:00Z",
  },
  role: "Owner",
  permissions: ["role.read", "role.manage"],
  superadmin: true,
};

const REGISTRY = [
  { group: "Access Control", codename: "user.read", description: "List and view users" },
  { group: "Access Control", codename: "user.manage", description: "Manage users" },
  { group: "Servers", codename: "server.read", description: "List and view servers" },
  { group: "Servers", codename: "server.update", description: "Edit servers" },
];

const ROLES_PAGE: Page<Role> = {
  items: [
    {
      id: "r-owner",
      name: "Owner",
      description: "Full access",
      is_system: true,
      permissions: ["*"],
      created_at: "2026-01-01T00:00:00Z",
    },
    {
      id: "r-oncall",
      name: "OnCall",
      description: "Night shift",
      is_system: false,
      permissions: ["server.read", "user.read"],
      created_at: "2026-05-01T00:00:00Z",
    },
  ],
  total: 2,
  limit: 100,
  offset: 0,
};

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>
        <ToastProvider>
          <AuthProvider>
            <RolesPage />
          </AuthProvider>
        </ToastProvider>
      </QueryClientProvider>
    </MemoryRouter>,
  );
}

function defaultGet(path: string): Promise<unknown> {
  if (path === "/auth/me") return Promise.resolve(ME);
  if (path === "/roles") return Promise.resolve(ROLES_PAGE);
  if (path === "/roles/permissions") return Promise.resolve(REGISTRY);
  return Promise.reject(new ApiError(404, "NOT_FOUND", `unexpected GET ${path}`));
}

beforeEach(() => {
  vi.clearAllMocks();
  mocks.apiGet.mockImplementation(defaultGet);
  mocks.apiPost.mockResolvedValue({});
  mocks.apiPatch.mockResolvedValue({});
  mocks.apiDelete.mockResolvedValue({});
});

describe("RolesPage", () => {
  it("renders the permission matrix, expanding the wildcard role", async () => {
    renderPage();

    expect(await screen.findByText("server.update")).toBeInTheDocument();

    // Owner holds ["*"] so it ticks every permission — OnCall only has
    // server.read and user.read, so server.update shows exactly one tick.
    const updateRow = screen.getByText("server.update").closest("tr");
    expect(updateRow).not.toBeNull();
    expect(within(updateRow as HTMLTableRowElement).getAllByText("✓")).toHaveLength(1);
    expect(within(updateRow as HTMLTableRowElement).getAllByText("—")).toHaveLength(1);

    // server.read is granted to both roles.
    const readRow = screen.getByText("server.read").closest("tr");
    expect(within(readRow as HTMLTableRowElement).getAllByText("✓")).toHaveLength(2);

    // user.manage: granted to Owner only via the wildcard.
    const manageRow = screen.getByText("user.manage").closest("tr");
    expect(within(manageRow as HTMLTableRowElement).getAllByText("✓")).toHaveLength(1);
    expect(within(manageRow as HTMLTableRowElement).getAllByText("—")).toHaveLength(1);

    // Permissions render grouped under their group headers.
    expect(screen.getByText("Access Control")).toBeInTheDocument();
    expect(screen.getByText("Servers")).toBeInTheDocument();
  });

  it("marks system roles non-editable while custom roles get Edit/Delete", async () => {
    renderPage();
    await screen.findByText("OnCall");

    expect(screen.getByText(/system · all/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Edit Owner" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Delete Owner" })).toBeNull();
    expect(screen.getByRole("button", { name: "Edit OnCall" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Delete OnCall" })).toBeInTheDocument();
  });

  it("creates a custom role from the grouped checkbox grid", async () => {
    renderPage();
    await screen.findByText("OnCall");

    fireEvent.click(screen.getByRole("button", { name: "New role" }));
    fireEvent.change(screen.getByLabelText("Name"), { target: { value: "SRE" } });
    fireEvent.click(screen.getByLabelText(/server\.update/));
    fireEvent.click(screen.getByRole("button", { name: "Create role" }));

    await waitFor(() =>
      expect(mocks.apiPost).toHaveBeenCalledWith("/roles", {
        name: "SRE",
        description: "",
        permissions: ["server.update"],
      }),
    );
    expect(await screen.findByText("Created role SRE")).toBeInTheDocument();
  });

  it("deletes a custom role after confirmation", async () => {
    renderPage();
    await screen.findByText("OnCall");

    fireEvent.click(screen.getByRole("button", { name: "Delete OnCall" }));
    fireEvent.click(screen.getByRole("button", { name: "Delete role" }));

    await waitFor(() => expect(mocks.apiDelete).toHaveBeenCalledWith("/roles/r-oncall"));
    expect(await screen.findByText("Deleted role OnCall")).toBeInTheDocument();
  });

  it("shows the empty state when no roles exist", async () => {
    mocks.apiGet.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(ME);
      if (path === "/roles/permissions") return Promise.resolve(REGISTRY);
      if (path === "/roles") {
        return Promise.resolve({ items: [], total: 0, limit: 100, offset: 0 } satisfies Page<Role>);
      }
      return Promise.reject(new ApiError(404, "NOT_FOUND", `unexpected GET ${path}`));
    });
    renderPage();

    expect(await screen.findByText("No roles defined")).toBeInTheDocument();
  });
});
