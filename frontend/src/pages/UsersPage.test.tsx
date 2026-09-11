import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../api/client";
import type { Page, Role, User } from "../api/types";
import { AuthProvider } from "../auth/AuthContext";
import { ToastProvider } from "../components/toast";
import UsersPage from "./UsersPage";

const mocks = vi.hoisted(() => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
  apiPatch: vi.fn(),
  apiDelete: vi.fn(),
}));

// Keep the real ApiError so `instanceof` checks inside the page still work.
vi.mock("../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/client")>();
  return { ...actual, ...mocks };
});

const ME = {
  user: {
    id: "u-self",
    email: "admin@example.com",
    full_name: "Ada Admin",
    is_active: true,
    status: "ACTIVE",
    role_id: "r-1",
    role_name: "Owner",
    last_login_at: null,
    created_at: "2026-01-01T00:00:00Z",
  },
  role: "Owner",
  permissions: ["user.read", "user.manage", "role.read"],
  superadmin: false,
};

function makeUser(over: Partial<User> & { id: string; email: string }): User {
  return {
    full_name: "",
    is_active: true,
    status: "ACTIVE",
    role_id: null,
    role_name: null,
    last_login_at: null,
    created_at: "2026-02-02T00:00:00Z",
    ...over,
  };
}

const ALICE = makeUser({
  id: "u-self",
  email: "admin@example.com",
  full_name: "Ada Admin",
  role_id: "r-1",
  role_name: "Owner",
});

const BOB = makeUser({
  id: "u-2",
  email: "bob@example.com",
  full_name: "Bob Ops",
  status: "LOCKED",
  role_id: "r-2",
  role_name: "Developer",
});

const USERS_PAGE: Page<User> = { items: [ALICE, BOB], total: 2, limit: 25, offset: 0 };

const ROLES_PAGE: Page<Role> = {
  items: [
    { id: "r-1", name: "Owner", description: "", is_system: true, permissions: ["*"], created_at: "2026-01-01T00:00:00Z" },
    { id: "r-2", name: "Developer", description: "", is_system: true, permissions: ["server.read"], created_at: "2026-01-01T00:00:00Z" },
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
            <UsersPage />
          </AuthProvider>
        </ToastProvider>
      </QueryClientProvider>
    </MemoryRouter>,
  );
}

function defaultGet(path: string): Promise<unknown> {
  if (path === "/auth/me") return Promise.resolve(ME);
  if (path === "/users") return Promise.resolve(USERS_PAGE);
  if (path === "/roles") return Promise.resolve(ROLES_PAGE);
  return Promise.reject(new ApiError(404, "NOT_FOUND", `unexpected GET ${path}`));
}

beforeEach(() => {
  vi.clearAllMocks();
  mocks.apiGet.mockImplementation(defaultGet);
  mocks.apiPost.mockResolvedValue({});
  mocks.apiPatch.mockResolvedValue({});
  mocks.apiDelete.mockResolvedValue({});
});

describe("UsersPage", () => {
  it("renders the user directory with role selects and the lockout indicator", async () => {
    renderPage();

    expect(await screen.findByText("admin@example.com")).toBeInTheDocument();
    expect(screen.getByText("bob@example.com")).toBeInTheDocument();
    // LOCKED status renders the badge plus the explicit lockout hint.
    expect(screen.getByText("sign-in locked")).toBeInTheDocument();
    expect(screen.getByLabelText("Role for bob@example.com")).toBeInTheDocument();
    expect(screen.getByLabelText("Search users")).toBeInTheDocument();
  });

  it("blocks deactivating yourself and deactivates other users", async () => {
    renderPage();
    await screen.findByText("admin@example.com");

    const buttons = screen.getAllByRole("button", { name: "Deactivate" });
    expect(buttons).toHaveLength(2);
    expect(buttons[0]).toBeDisabled(); // own account

    fireEvent.click(buttons[1]);
    await waitFor(() => expect(mocks.apiDelete).toHaveBeenCalledWith("/users/u-2"));
    expect(await screen.findByText("Deactivated bob@example.com")).toBeInTheDocument();
  });

  it("invites a user and shows the generated password exactly once", async () => {
    mocks.apiPost.mockResolvedValue({
      user: makeUser({ id: "u-3", email: "carol@example.com" }),
      initial_password: "temp-pass-9f3",
    });
    renderPage();
    await screen.findByText("admin@example.com");

    fireEvent.click(screen.getByRole("button", { name: "Invite user" }));
    fireEvent.change(screen.getByLabelText("Email"), { target: { value: "carol@example.com" } });
    fireEvent.change(screen.getByLabelText("Full name"), { target: { value: "Carol Dev" } });
    fireEvent.change(screen.getByLabelText("Initial password"), {
      target: { value: "s3cret!" },
    });
    fireEvent.change(screen.getByLabelText("Role"), { target: { value: "r-2" } });
    fireEvent.click(screen.getByRole("button", { name: "Send invite" }));

    await waitFor(() =>
      expect(mocks.apiPost).toHaveBeenCalledWith("/users", {
        email: "carol@example.com",
        password: "s3cret!",
        full_name: "Carol Dev",
        role_id: "r-2",
      }),
    );
    // One-time password is displayed with the once-only warning.
    expect(await screen.findByText("temp-pass-9f3")).toBeInTheDocument();
    expect(screen.getByText(/only once/i)).toBeInTheDocument();
  });

  it("shows the error block when the users request fails", async () => {
    mocks.apiGet.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(ME);
      if (path === "/roles") return Promise.resolve(ROLES_PAGE);
      if (path === "/users") {
        return Promise.reject(new ApiError(500, "DB_DOWN", "database unavailable"));
      }
      return Promise.reject(new ApiError(404, "NOT_FOUND", `unexpected GET ${path}`));
    });
    renderPage();

    expect(await screen.findByText(/DB_DOWN/)).toBeInTheDocument();
    expect(screen.getByText(/database unavailable/)).toBeInTheDocument();
  });

  it("shows the empty state when no users exist", async () => {
    mocks.apiGet.mockImplementation((path: string) => {
      if (path === "/auth/me") return Promise.resolve(ME);
      if (path === "/roles") return Promise.resolve(ROLES_PAGE);
      if (path === "/users") {
        return Promise.resolve({ items: [], total: 0, limit: 25, offset: 0 } satisfies Page<User>);
      }
      return Promise.reject(new ApiError(404, "NOT_FOUND", `unexpected GET ${path}`));
    });
    renderPage();

    expect(await screen.findByText("No users found")).toBeInTheDocument();
  });
});
