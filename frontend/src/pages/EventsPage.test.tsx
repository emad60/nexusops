import { describe, expect, it, vi, beforeEach, type Mock } from "vitest";
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ApiError, apiGet } from "../api/client";
import type { CursorPage, EventItem } from "../api/types";
import { useEventStream } from "../hooks/useEventStream";
import EventsPage from "./EventsPage";

vi.mock("../api/client", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../api/client")>();
  return { ...actual, apiGet: vi.fn() };
});
vi.mock("../hooks/useEventStream", () => ({ useEventStream: vi.fn() }));

const mockedGet = apiGet as unknown as Mock;
const mockedStream = useEventStream as unknown as Mock;

function makeEvent(overrides: Partial<EventItem> = {}): EventItem {
  return {
    id: "evt-1",
    type: "SERVER_ONLINE",
    level: "INFO",
    message: "web-01 came back online",
    actor_type: "AGENT",
    resource_type: "server",
    resource_id: "srv-1",
    data: {},
    created_at: "2026-09-10T10:00:00Z",
    ...overrides,
  };
}

function mockApi(page: CursorPage<EventItem>): void {
  mockedGet.mockImplementation((path: string) => {
    if (path === "/events/types") {
      return Promise.resolve([
        { type: "SERVER_ONLINE", description: "Server agent came online" },
      ]);
    }
    if (path === "/events") return Promise.resolve(page);
    return Promise.reject(new ApiError(404, "NOT_FOUND", `unexpected path ${path}`));
  });
}

function renderPage() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <MemoryRouter>
      <QueryClientProvider client={client}>
        <EventsPage />
      </QueryClientProvider>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  mockedGet.mockReset();
  mockedStream.mockClear();
});

describe("EventsPage", () => {
  it("renders fetched events with severity badges and subscribes to the global channel", async () => {
    mockApi({
      items: [
        makeEvent(),
        makeEvent({ id: "evt-2", type: "MONITOR_DOWN", level: "CRITICAL", message: "api monitor exceeded failure threshold" }),
      ],
      next_cursor: null,
      has_more: false,
    });
    renderPage();

    const table = await screen.findByRole("table");
    expect(within(table).getByText("web-01 came back online")).toBeInTheDocument();
    expect(within(table).getByText("MONITOR_DOWN")).toBeInTheDocument();
    expect(within(table).getAllByText("CRITICAL").length).toBeGreaterThan(0);
    expect(mockedStream).toHaveBeenCalledWith([{ channel: "global" }], expect.any(Function));
  });

  it("shows the empty state when no events match", async () => {
    mockApi({ items: [], next_cursor: null, has_more: false });
    renderPage();

    expect(await screen.findByText("No events match the current filters")).toBeInTheDocument();
  });

  it("shows an error state when the API fails", async () => {
    mockedGet.mockImplementation(() =>
      Promise.reject(new ApiError(500, "INTERNAL", "boom")),
    );
    renderPage();

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("boom");
  });

  it("sends the selected level filter to the API", async () => {
    mockApi({ items: [makeEvent()], next_cursor: null, has_more: false });
    renderPage();
    await screen.findByRole("table");

    fireEvent.change(screen.getByLabelText("Level"), { target: { value: "ERROR" } });

    await waitFor(() =>
      expect(mockedGet).toHaveBeenCalledWith(
        "/events",
        expect.objectContaining({ level: "ERROR" }),
        expect.anything(),
      ),
    );
  });

  it("live-appends events arriving on the global channel", async () => {
    mockApi({ items: [makeEvent()], next_cursor: null, has_more: false });
    renderPage();
    await screen.findByRole("table");

    const handler = mockedStream.mock.calls.at(-1)![1] as (frame: unknown) => void;
    act(() => {
      handler({
        type: "event",
        channel: "global",
        data: {
          id: "evt-live",
          type: "DEPLOYMENT_FAILED",
          level: "ERROR",
          message: "deploy 42 failed",
          actor_type: "SYSTEM",
          created_at: "2026-09-10T11:00:00Z",
        },
      });
    });

    expect(await screen.findByText("deploy 42 failed")).toBeInTheDocument();
  });
});
