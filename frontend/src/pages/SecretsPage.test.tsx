import { describe, expect, it, vi, beforeEach, type Mock } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ApiError, apiDelete, apiGet, apiPost } from "../api/client";
import type { Page, SecretRow } from "../api/types";
import { ToastProvider } from "../components/toast";
import SecretsPage from "./SecretsPage";

vi.mock("../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/client")>();
  return { ...actual, apiGet: vi.fn(), apiPost: vi.fn(), apiDelete: vi.fn() };
});
vi.mock("../auth/AuthContext", () => ({
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

function makeSecret(overrides: Partial<SecretRow> = {}): SecretRow {
  return {
    id: "s-1",
    key: "DB_PASSWORD",
    version: 2,
    digest: "a1b2c3d4e5f6",
    description: "Primary database password",
    project_id: null,
    rotated_at: "2026-09-01T12:00:00Z",
    rotated_by_email: "admin@nexusops.local",
    created_at: "2026-08-01T00:00:00Z",
    updated_at: "2026-09-01T12:00:00Z",
    ...overrides,
  };
}

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <MemoryRouter>
      <QueryClientProvider client={client}>
        <ToastProvider>
          <SecretsPage />
        </ToastProvider>
      </QueryClientProvider>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  mockedGet.mockReset();
  mockedPost.mockReset();
  mockedDelete.mockReset();
  mockedGet.mockResolvedValue({
    items: [makeSecret()],
    total: 1,
    limit: 25,
    offset: 0,
  } satisfies Page<SecretRow>);
});

describe("SecretsPage", () => {
  it("renders secret metadata without any value column", async () => {
    renderPage();

    expect(await screen.findByText("DB_PASSWORD")).toBeInTheDocument();
    expect(screen.getByText("v2")).toBeInTheDocument();
    expect(screen.getByText("a1b2c3d4e5f6")).toBeInTheDocument();
    // Values are write-only: no "Value" column may ever exist.
    expect(screen.queryByRole("columnheader", { name: "Value" })).not.toBeInTheDocument();
  });

  it("shows the unrecoverable-value warning in the create dialog and submits the payload", async () => {
    mockedPost.mockResolvedValue(makeSecret({ key: "STRIPE_API_KEY", version: 1 }));
    renderPage();
    await screen.findByText("DB_PASSWORD");

    fireEvent.click(screen.getByRole("button", { name: "New secret" }));
    expect(await screen.findByRole("dialog")).toHaveTextContent(/never be viewed/i);

    fireEvent.change(screen.getByLabelText("Key"), { target: { value: "STRIPE_API_KEY" } });
    fireEvent.change(screen.getByLabelText("Value"), { target: { value: "hunter2" } });
    fireEvent.click(screen.getByRole("button", { name: "Create secret" }));

    await waitFor(() =>
      expect(mockedPost).toHaveBeenCalledWith("/secrets", {
        key: "STRIPE_API_KEY",
        value: "hunter2",
        description: "",
      }),
    );
  });

  it("rejects an invalid key client-side without calling the API", async () => {
    renderPage();
    await screen.findByText("DB_PASSWORD");

    fireEvent.click(screen.getByRole("button", { name: "New secret" }));
    fireEvent.change(await screen.findByLabelText("Key"), { target: { value: "lowercase_key" } });
    fireEvent.change(screen.getByLabelText("Value"), { target: { value: "hunter2" } });
    fireEvent.click(screen.getByRole("button", { name: "Create secret" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/UPPERCASE/i);
    expect(mockedPost).not.toHaveBeenCalled();
  });

  it("shows a toast with the API error message when creation fails", async () => {
    mockedPost.mockRejectedValue(new ApiError(422, "VALIDATION_ERROR", "Key already exists"));
    renderPage();
    await screen.findByText("DB_PASSWORD");

    fireEvent.click(screen.getByRole("button", { name: "New secret" }));
    fireEvent.change(await screen.findByLabelText("Key"), { target: { value: "DB_PASSWORD" } });
    fireEvent.change(screen.getByLabelText("Value"), { target: { value: "hunter2" } });
    fireEvent.click(screen.getByRole("button", { name: "Create secret" }));

    expect(
      await within(screen.getByRole("status")).findByText(/VALIDATION_ERROR: Key already exists/),
    ).toBeInTheDocument();
  });

  it("confirms before deleting a secret", async () => {
    mockedDelete.mockResolvedValue(undefined);
    renderPage();
    await screen.findByText("DB_PASSWORD");

    fireEvent.click(screen.getByRole("button", { name: "Delete DB_PASSWORD" }));
    const dialog = await screen.findByRole("dialog");
    expect(dialog).toHaveTextContent(/Permanently delete/);

    fireEvent.click(within(dialog).getByRole("button", { name: "Delete secret" }));
    await waitFor(() => expect(mockedDelete).toHaveBeenCalledWith("/secrets/s-1"));
  });
});
