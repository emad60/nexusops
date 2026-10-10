import { test as base, expect } from "@playwright/test";
import type { APIRequestContext, BrowserContext, Page } from "@playwright/test";

import { EDGE, MAILPIT } from "./env";

/**
 * Shared fixtures for the E2E journey.
 *
 * Auth model (respecting the backend's refresh-rotation + reuse detection):
 * - `adminSession`: ONE worker-scoped browser context, signed in once via
 *   `context.request` — the login's refresh cookie lands in that context's
 *   cookie jar, and every SPA boot afterwards rotates it *within* the same
 *   jar. The backend revokes a whole session family when an already-consumed
 *   refresh token is replayed (`auth.token_reuse_detected`), so the journey
 *   must never present the same cookie from two places: pages are strictly
 *   sequential and there is exactly one long-lived page per worker.
 * - `page`        : that single page, shared across tests (worker-scoped).
 *                   Every test starts with a full SPA navigation, which wipes
 *                   all in-memory state; only cookies persist by design. No
 *                   per-test page close — a close racing an in-flight cookie
 *                   rotation would drop the rotated cookie and trip the reuse
 *                   detector for every later test.
 * - `auth`        : the bootstrap result (token + fresh-database flag).
 * - `api` / `mailpit`: request contexts for the API and the SMTP sink.
 *
 * Login POSTs per journey: 2 worker-level (page bootstrap + `apiToken`) +
 * test 1's own clean-context flow + at most one form fallback — comfortably
 * inside the 10/min login rate limit that per-test logins exhausted by test 7.
 */

const ADMIN = { email: "admin@nexusops.example.com", password: "nexusops-admin", full_name: "E2E Admin" };

export interface Bootstrap {
  token: string;
  freshDatabase: boolean;
}

/** One full window of the login limiter (10 requests / 60s / IP). */
const RATE_LIMIT_WINDOW_MS = 65_000;

async function bootstrapVia(request: APIRequestContext): Promise<Bootstrap> {
  const attemptLogin = () =>
    request.post(`${EDGE}/api/v1/auth/login`, {
      data: { email: ADMIN.email, password: ADMIN.password },
    });

  let login = await attemptLogin();
  if (!login.ok() && login.status() === 429) {
    // The auth limiter is **fail-closed** and keyed per IP, so every request in
    // the run shares one bucket. A 429 means "too many logins", NOT "no such
    // account": reading it as the latter would send the harness down the
    // bootstrap-registration path, which a seeded instance always refuses
    // (INVITATION_REQUIRED). Wait out one window and retry instead.
    await new Promise((resolve) => setTimeout(resolve, RATE_LIMIT_WINDOW_MS));
    login = await attemptLogin();
  }
  if (login.ok()) {
    return { token: ((await login.json()) as { access_token: string }).access_token, freshDatabase: false };
  }

  // Fresh database: registering the very first user bootstraps the system
  // (Owner + superadmin). A used database answers INVITATION_REQUIRED.
  const reg = await request.post(`${EDGE}/api/v1/auth/register`, {
    data: { email: ADMIN.email, password: ADMIN.password, full_name: ADMIN.full_name },
  });
  expect(
    reg.ok(),
    `bootstrap register failed (login said ${login.status()}): ${reg.status()} ${await reg.text()}`,
  ).toBeTruthy();
  const retry = await request.post(`${EDGE}/api/v1/auth/login`, {
    data: { email: ADMIN.email, password: ADMIN.password },
  });
  expect(retry.ok()).toBeTruthy();
  return { token: ((await retry.json()) as { access_token: string }).access_token, freshDatabase: true };
}

export const test = base.extend<{
  auth: Bootstrap;
  adminSession: { context: BrowserContext; bootstrap: Bootstrap };
  journeyPage: Page;
  apiToken: { token: string; orgId: string };
  api: APIRequestContext;
  mailpit: APIRequestContext;
}>({
  adminSession: [
    async ({ browser }, use) => {
      const context = await browser.newContext({ baseURL: EDGE });
      const bootstrap = await bootstrapVia(context.request);
      await use({ context, bootstrap });
      await context.close();
    },
    { scope: "worker" },
  ],

  auth: [
    async ({ adminSession }, use) => {
      await use(adminSession.bootstrap);
    },
    { scope: "worker" },
  ],

  // One long-lived page for the whole journey (see module docstring for why
  // it must not be created or closed per test).
  journeyPage: [
    async ({ adminSession }, use) => {
      const page = await adminSession.context.newPage();
      await use(page);
    },
    { scope: "worker" },
  ],

  // Alias for the built-in page fixture. Deliberately does NOT close the page
  // at test end — the shared page must survive across tests.
  page: [
    async ({ journeyPage }, use) => {
      await use(journeyPage);
    },
    { scope: "test" },
  ],

  // Dedicated session for API-level tests, separate from the page session:
  // test 2 signs the PAGE out, and because the page boot refreshes with the
  // shared jar's cookie, that sign-out revokes whichever session the page
  // currently carries — which must never be the one the `api` fixture calls
  // with. This login's token is held here and used by nothing else.
  // The login response's active_organization_id also yields the tenant header:
  // since Phase 1 tenancy, every org-scoped endpoint rejects requests without
  // X-Org-Id (ORGANIZATION_HEADER_REQUIRED).
  apiToken: [
    async ({ playwright }, use) => {
      const ctx = await playwright.request.newContext({ baseURL: EDGE });
      try {
        const login = await ctx.post(`${EDGE}/api/v1/auth/login`, {
          data: { email: ADMIN.email, password: ADMIN.password },
        });
        expect(login.ok(), `api-token bootstrap login failed: ${login.status()}`).toBeTruthy();
        const body = (await login.json()) as {
          access_token: string;
          active_organization_id: string | null;
          organizations: Array<{ organization: { id: string } }>;
        };
        // ``active_organization_id`` is set only when the choice is unambiguous
        // (auth_service.IssuedTokens): an account that belongs to more than one
        // organization — which the cross-tenant journeys create and cannot
        // delete — must therefore *pick*, the way any client does. The list comes
        // oldest first, so index 0 is the organization the platform itself named
        // while the account still had exactly one, and a single-membership run
        // resolves to the identical value as before.
        const orgId = body.active_organization_id ?? body.organizations[0]?.organization.id ?? null;
        expect(orgId, "login returned no organization to scope API calls with").toBeTruthy();
        await use({ token: body.access_token, orgId: orgId as string });
      } finally {
        await ctx.dispose();
      }
    },
    { scope: "worker" },
  ],

  api: async ({ playwright, apiToken }, use) => {
    const api = await playwright.request.newContext({
      baseURL: EDGE,
      extraHTTPHeaders: {
        Authorization: `Bearer ${apiToken.token}`,
        "X-Org-Id": apiToken.orgId,
      },
    });
    await use(api);
    await api.dispose();
  },

  mailpit: async ({ playwright }, use) => {      const mailpit = await playwright.request.newContext({ baseURL: MAILPIT });
    await use(mailpit);
    await mailpit.dispose();
  },
});

export { expect };
