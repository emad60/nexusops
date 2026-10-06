import { act, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { setAccessToken, setActiveOrgId } from "../api/client";
import { useEventStream } from "./useEventStream";

const ORG_A = "11111111-1111-4111-8111-111111111111";

/**
 * The socket handshake is a tenancy boundary, not a formality.
 *
 * The hub binds every socket to one organization and closes it (4401) when the
 * auth frame carries no valid `org_id`. A client that omits it therefore fails
 * *silently* — the connection is accepted, refused, and retried — which is
 * exactly how this regressed into a 2s reconnect loop that only the end-to-end
 * journey caught. These tests pin the frame contents.
 */

class FakeSocket {
  static instances: FakeSocket[] = [];
  static OPEN = 1;

  readyState = 0;
  sent: Record<string, unknown>[] = [];
  onopen: (() => void) | null = null;
  onmessage: ((message: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  closed = false;

  constructor(public url: string) {
    FakeSocket.instances.push(this);
  }

  send(payload: string) {
    this.sent.push(JSON.parse(payload) as Record<string, unknown>);
  }

  /** Simulate the server accepting the upgrade. */
  open() {
    this.readyState = FakeSocket.OPEN;
    this.onopen?.();
  }

  close() {
    this.closed = true;
  }

  /** Simulate the server dropping an established socket (idle watchdog, deploy, blip). */
  serverClose() {
    this.readyState = 3; // CLOSED
    this.onclose?.();
  }
}

function Stream({ channel = "global" as const }) {
  useEventStream([{ channel }], () => {});
  return null;
}

describe("useEventStream", () => {
  beforeEach(() => {
    FakeSocket.instances = [];
    vi.stubGlobal("WebSocket", FakeSocket);
    vi.stubGlobal("location", { protocol: "http:", host: "localhost:8080" });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    setAccessToken(null);
    setActiveOrgId(null);
  });

  it("authenticates with the organization the page is acting in", () => {
    setAccessToken("token-abc");
    setActiveOrgId("11111111-1111-4111-8111-111111111111");

    render(<Stream />);
    const socket = FakeSocket.instances[0];
    socket.open();

    expect(socket.sent[0]).toEqual({
      action: "auth",
      token: "token-abc",
      org_id: "11111111-1111-4111-8111-111111111111",
    });
    // Subscription follows in the same batch: the hub has no auth_ok frame.
    expect(socket.sent[1]).toEqual({ action: "subscribe", channel: "global", params: {} });
  });

  it("reconnects and re-authenticates after the server drops the socket", () => {
    vi.useFakeTimers({ toFake: ["setTimeout", "setInterval", "clearTimeout", "clearInterval"] });
    setAccessToken("token-abc");
    setActiveOrgId(ORG_A);

    render(<Stream />);
    const first = FakeSocket.instances[0];
    first.open();
    expect(first.sent[0]).toMatchObject({ action: "auth", org_id: ORG_A });

    // The server hangs up (idle watchdog, a deploy, a network blip). The hook
    // must not leave the page permanently dark: it reconnects with backoff and
    // replays the handshake on the new socket.
    act(() => first.serverClose());
    expect(FakeSocket.instances).toHaveLength(1); // backoff, not a hot loop

    act(() => {
      vi.advanceTimersByTime(2_000);
    });
    expect(FakeSocket.instances).toHaveLength(2);

    const second = FakeSocket.instances[1];
    act(() => second.open());
    expect(second.sent[0]).toMatchObject({ action: "auth", org_id: ORG_A });
    expect(second.sent[1]).toEqual({ action: "subscribe", channel: "global", params: {} });
  });

  it("keeps a quiet stream alive with periodic pings", () => {
    // The hub reaps a socket quiet for 120s; a live view with no traffic would
    // be dropped and silently lose every event published during the gap.
    vi.useFakeTimers({ toFake: ["setTimeout", "setInterval", "clearTimeout", "clearInterval"] });
    setAccessToken("token-abc");
    setActiveOrgId(ORG_A);

    render(<Stream />);
    const socket = FakeSocket.instances[0];
    socket.open();
    expect(socket.sent).toHaveLength(2); // auth + subscribe, no ping yet

    act(() => {
      vi.advanceTimersByTime(30_000);
    });
    expect(socket.sent[2]).toEqual({ action: "ping" });

    act(() => {
      vi.advanceTimersByTime(30_000);
    });
    expect(socket.sent[3]).toEqual({ action: "ping" });
  });

  it("waits for the organization instead of reconnecting into a refusal", () => {
    setAccessToken("token-abc");
    setActiveOrgId(null); // the AuthProvider has not resolved one yet

    render(<Stream />);
    const socket = FakeSocket.instances[0];
    socket.open();

    // No org => nothing is sent: an auth frame without `org_id` would be
    // refused by the hub and look like a server that keeps hanging up.
    expect(socket.sent).toEqual([]);
    expect(socket.closed).toBe(false); // and the socket is kept, not churned

    // Once the organization lands, the SAME socket authenticates and
    // subscribes — no reconnect, no dropped frames.
    setActiveOrgId("22222222-2222-4222-8222-222222222222");
    expect(socket.sent).toEqual([
      { action: "auth", token: "token-abc", org_id: "22222222-2222-4222-8222-222222222222" },
      { action: "subscribe", channel: "global", params: {} },
    ]);
  });
});
