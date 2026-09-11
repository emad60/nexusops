import { test as base, expect } from "@playwright/test";
import type { APIRequestContext, BrowserContext, Page } from "@playwright/test";

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

const EDGE = "http://127.0.0.1:8080";
const ADMIN = { email: "admin@nexusops.example.com", password: "nexusops-admin", full_name: "E2E Admin" };

export interface Bootstrap {
  token: string;
  freshDatabase: boolean;
}

async function bootstrapVia(request: APIRequestContext): Promise<Bootstrap> {
  const login = await request.post(`${EDGE}/api/v1/auth/login`, {
    data: { email: ADMIN.email, password: ADMIN.password },
  });
  if (login.ok()) {
    return { token: ((await login.json()) as { access_token: string }).access_token, freshDatabase: false };
  }

  // Fresh database: registering the very first user bootstraps the system
  // (Owner + superadmin). A used database answers INVITATION_REQUIRED.
  const reg = await request.post(`${EDGE}/api/v1/auth/register`, {
    data: { email: ADMIN.email, password: ADMIN.password, full_name: ADMIN.full_name },
  });
  expect(reg.ok(), `bootstrap register failed: ${reg.status()} ${await reg.text()}`).toBeTruthy();
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
  apiToken: string;
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
  apiToken: [
    async ({ playwright }, use) => {
      const ctx = await playwright.request.newContext({ baseURL: EDGE });
      try {
        const login = await ctx.post(`${EDGE}/api/v1/auth/login`, {
          data: { email: ADMIN.email, password: ADMIN.password },
        });
        expect(login.ok(), `api-token bootstrap login failed: ${login.status()}`).toBeTruthy();
        await use(((await login.json()) as { access_token: string }).access_token);
      } finally {
        await ctx.dispose();
      }
    },
    { scope: "worker" },
  ],

  api: async ({ playwright, apiToken }, use) => {
    const api = await playwright.request.newContext({
      baseURL: EDGE,
      extraHTTPHeaders: { Authorization: `Bearer ${apiToken}` },
    });
    await use(api);
    await api.dispose();
  },

  mailpit: async ({ playwright }, use) => {
    const mailpit = await playwright.request.newContext({ baseURL: "http://127.0.0.1:8025" });
    await use(mailpit);
    await mailpit.dispose();
  },
});

export { expect };
