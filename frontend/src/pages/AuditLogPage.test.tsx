import { describe, expect, it, vi, beforeEach, type Mock } from "vitest";
import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ApiError, apiGet } from "../api/client";
import type { AuditEntry, Page } from "../api/types";
import AuditLogPage from "./AuditLogPage";

vi.mock("../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/client")>();
  return { ...actual, apiGet: vi.fn() };
});

const mockedGet = apiGet as unknown as Mock;

function makeEntry(overrides: Partial<AuditEntry> = {}): AuditEntry {
  return {
    id: "9f1c2a34-56b7-4c8d-9e0f-1a2b3c4d5e6f",
    actor_email: "admin@nexusops.local",
    action: "secret.rotate",
    resource_type: "secret",
    resource_id: "s-1",
    ip_address: "10.0.0.8",
    result: "SUCCESS",
    metadata: {},
    created_at: "2026-09-10T09:30:00Z",
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
        <AuditLogPage />
      </QueryClientProvider>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  mockedGet.mockReset();
  mockedGet.mockResolvedValue({
    items: [makeEntry()],
    total: 1,
    limit: 25,
    offset: 0,
  } satisfies Page<AuditEntry>);
});

describe("AuditLogPage", () => {
  it("renders entries with actor, action and result, plus the append-only note", async () => {
    renderPage();

    const table = await screen.findByRole("table");
    expect(within(table).getByText("admin@nexusops.local")).toBeInTheDocument();
    expect(within(table).getByText("secret.rotate")).toBeInTheDocument();
    expect(within(table).getByText("SUCCESS")).toBeInTheDocument();
    expect(within(table).getByText("10.0.0.8")).toBeInTheDocument();
    expect(screen.getByRole("note")).toHaveTextContent(/append-only/i);
    // Immutable by design: the table itself carries no mutation controls.
    expect(within(table).queryByRole("button")).not.toBeInTheDocument();
  });

  it("shows the empty state when no entries match", async () => {
    mockedGet.mockResolvedValue({ items: [], total: 0, limit: 25, offset: 0 });
    renderPage();

    expect(
      await screen.findByText("No audit entries match the current filters"),
    ).toBeInTheDocument();
  });

  it("shows an error state when the API fails", async () => {
    mockedGet.mockRejectedValue(new ApiError(403, "FORBIDDEN", "missing audit.read"));
    renderPage();

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("missing audit.read");
  });

  it("applies the action filter on submit", async () => {
    renderPage();
    await screen.findByRole("table");

    fireEvent.change(screen.getByLabelText("Action"), { target: { value: "user.login" } });
    fireEvent.click(screen.getByRole("button", { name: "Apply" }));

    await waitFor(() =>
      expect(mockedGet).toHaveBeenCalledWith(
        "/audit-logs",
        expect.objectContaining({ action: "user.login", offset: 0 }),
        expect.anything(),
      ),
    );
  });

  it("sends the selected result filter immediately", async () => {
    renderPage();
    await screen.findByRole("table");

    fireEvent.change(screen.getByLabelText("Result"), { target: { value: "DENIED" } });

    await waitFor(() =>
      expect(mockedGet).toHaveBeenCalledWith(
        "/audit-logs",
        expect.objectContaining({ result: "DENIED" }),
        expect.anything(),
      ),
    );
  });
});
