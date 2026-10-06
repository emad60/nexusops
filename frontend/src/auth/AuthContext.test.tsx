/**
 * Organization bootstrap in AuthProvider.
 *
 * Three behaviours matter for tenant isolation and none of them is cosmetic:
 *
 * 1. After sign-in the client must settle on an organization *before* the shell
 *    renders, because every tenant request without `X-Org-Id` is refused.
 * 2. A remembered organization that stopped being valid (membership revoked,
 *    organization suspended) is answered with 403 on every route — including
 *    `/auth/me`. It must be dropped rather than leaving the app wedged.
 * 3. A user with no membership gets an explicit "choose an organization" state
 *    instead of a shell full of failed requests.
 */

import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { AuthProvider, useAuth } from "./AuthContext";
import { OrganizationSwitcher } from "../components/OrganizationSwitcher";
import { ApiError, setActiveOrgId } from "../api/client";

const mocks = vi.hoisted(() => ({ apiGet: vi.fn(), apiPost: vi.fn() }));

vi.mock("../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/client")>();
  return { ...actual, apiGet: mocks.apiGet, apiPost: mocks.apiPost };
});

const USER = {
  id: "u-1",
  email: "op@nexusops.io",
  full_name: "Ops One",
  is_active: true,
  status: "ACTIVE" as const,
  role_id: "r-1",
  role_name: "Owner",
  last_login_at: null,
  created_at: "2026-01-01T00:00:00Z",
};

function membership(id: string, name: string, isProvisional = false) {
  return {
    organization: {
      id,
      name,
      slug: name.toLowerCase().replace(/\s+/g, "-"),
      description: "",
      status: "ACTIVE" as const,
      is_provisional: isProvisional,
      renamed_at: null,
      created_at: "2026-01-01T00:00:00Z",
    },
    role_name: "Owner",
    role_id: "r-1",
    status: "ACTIVE" as const,
  };
}

function me(organizations: unknown[], activeOrgId: string | null) {
  return {
    user: USER,
    role: activeOrgId ? "Owner" : null,
    permissions: activeOrgId ? ["*"] : [],
    superadmin: true,
    organizations,
    active_organization_id: activeOrgId,
  };
}

function Probe() {
  const { user, activeMembership, initializing } = useAuth();
  if (initializing) return <span>loading</span>;
  return (
    <div>
      <span data-testid="email">{user?.email ?? "anonymous"}</span>
      <span data-testid="org">{activeMembership?.organization.name ?? "none"}</span>
      <OrganizationSwitcher />
    </div>
  );
}

async function renderProvider() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const utils = render(
    <MemoryRouter>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <Probe />
        </AuthProvider>
      </QueryClientProvider>
    </MemoryRouter>,
  );
  await act(async () => {});
  return utils;
}

beforeEach(() => {
  vi.clearAllMocks();
  localStorage.clear();
  setActiveOrgId(null);
});

describe("AuthProvider organization bootstrap", () => {
  it("selects the caller's organization and names it in the header control", async () => {
    mocks.apiGet.mockResolvedValue(me([membership("org-a", "Acme Fleet", true)], null));

    await renderProvider();

    expect(screen.getByTestId("org")).toHaveTextContent("Acme Fleet");
    // The provisional flag has to stay visible: a migration-created tenant must
    // never look like a deliberately named one.
    expect(screen.getByText("provisional")).toBeInTheDocument();
  });

  it("drops a remembered organization that is no longer valid, then recovers", async () => {
    setActiveOrgId("org-gone");
    mocks.apiGet
      .mockRejectedValueOnce(new ApiError(403, "ORGANIZATION_FORBIDDEN", "not a member"))
      .mockResolvedValueOnce(me([membership("org-a", "Acme Fleet")], null));

    await renderProvider();

    expect(screen.getByTestId("org")).toHaveTextContent("Acme Fleet");
    // 1) the remembered org is refused, 2) retried without it, 3) re-read with
    // the organization that was chosen so permissions match the tenant in use.
    expect(mocks.apiGet).toHaveBeenCalledTimes(3);
  });

  it("shows every organization in the switcher when there is more than one", async () => {
    mocks.apiGet.mockResolvedValue(
      me([membership("org-a", "Acme Fleet"), membership("org-b", "Globex Ops")], "org-a"),
    );

    await renderProvider();

    expect(screen.getByRole("combobox", { name: "Active organization" })).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /Globex Ops/ })).toBeInTheDocument();
  });

  it("leaves the caller without an active organization when they have no membership", async () => {
    mocks.apiGet.mockResolvedValue(me([], null));

    await renderProvider();

    expect(screen.getByTestId("email")).toHaveTextContent("op@nexusops.io");
    expect(screen.getByTestId("org")).toHaveTextContent("none");
    // Nothing to switch between, so the control stays out of the way.
    expect(screen.queryByRole("combobox")).not.toBeInTheDocument();
  });
});
