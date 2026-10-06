/**
 * The tenancy half of the HTTP client.
 *
 * The API never guesses which organization a request is for, so the browser has
 * to state one on every authenticated call — and must *not* state one on the
 * pre-auth calls (login, refresh), which have no tenant yet.
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  ORGANIZATION_HEADER,
  apiGet,
  getActiveOrgId,
  setAccessToken,
  setActiveOrgId,
} from "./client";

function headersOf(call: number): Record<string, string> {
  const fetchMock = globalThis.fetch as unknown as ReturnType<typeof vi.fn>;
  return (fetchMock.mock.calls[call][1] as RequestInit).headers as Record<string, string>;
}

beforeEach(() => {
  setAccessToken(null);
  setActiveOrgId(null);
  globalThis.fetch = vi.fn(async () =>
    new Response(JSON.stringify({ ok: true }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }),
  ) as unknown as typeof fetch;
});

afterEach(() => {
  vi.restoreAllMocks();
  localStorage.clear();
});

describe("organization header", () => {
  it("is sent on authenticated requests", async () => {
    setAccessToken("tok-1");
    setActiveOrgId("org-a");

    await apiGet("/nodes");

    expect(headersOf(0)[ORGANIZATION_HEADER]).toBe("org-a");
    expect(headersOf(0).Authorization).toBe("Bearer tok-1");
  });

  it("is omitted while signed out, so pre-auth calls carry no tenant", async () => {
    setActiveOrgId("org-a");

    await apiGet("/meta");

    expect(headersOf(0)[ORGANIZATION_HEADER]).toBeUndefined();
  });

  it("is omitted when no organization has been chosen yet", async () => {
    setAccessToken("tok-1");

    await apiGet("/auth/me");

    expect(headersOf(0)[ORGANIZATION_HEADER]).toBeUndefined();
  });

  it("remembers the choice across reloads, and forgets it on sign-out", () => {
    setActiveOrgId("org-a");
    expect(localStorage.getItem("nexusops.activeOrgId")).toBe("org-a");
    expect(getActiveOrgId()).toBe("org-a");

    setActiveOrgId(null);
    expect(localStorage.getItem("nexusops.activeOrgId")).toBeNull();
    expect(getActiveOrgId()).toBeNull();
  });
});
