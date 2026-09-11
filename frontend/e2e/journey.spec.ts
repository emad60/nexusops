/**
 * The full NexusOps journey, exactly as specified:
 *
 *   register → login → add server → agent heartbeat → create uptime monitor
 *   → monitor fails → incident opens + notification sent → recovery
 *   → deployment succeeds → deployment fails → audit trail shows everything
 *
 * Runs against the composed stack (`make up`): nginx edge on :8080, mailpit on
 * :8025, SIMULATION_MODE=true. The seeded database provides fleet + channels;
 * this spec creates its own user, server, monitors and deployments.
 */

import { expect } from "@playwright/test";
import { test } from "./fixtures";

const UNIQUE = Date.now(); // keeps the journey idempotent against a used DB

const ADMIN = {
  email: "admin@nexusops.example.com",
  password: "nexusops-admin",
  full_name: "E2E Admin",
};

/**
 * Sign in through the login form. If the POST hits the fail-closed login
 * limiter (10/min) the form shows a RATE_LIMITED alert; honor it with a
 * backoff and retry rather than failing the journey.
 */
async function formLogin(page: import("@playwright/test").Page): Promise<void> {
  await page.getByLabel("Email").fill(ADMIN.email);
  await page.getByLabel("Password", { exact: true }).fill(ADMIN.password);
  for (let attempt = 0; ; attempt++) {
    await page.getByRole("button", { name: /sign in/i }).click();
    try {
      await expect(page).toHaveURL("/", { timeout: 10_000 });
      return;
    } catch {
      const limited = await page
        .getByRole("alert")
        .filter({ hasText: /RATE_LIMITED|rate limit/i })
        .first()
        .isVisible()
        .catch(() => false);
      if (!limited || attempt >= 2) {
        throw new Error(`UI login failed after ${attempt + 1} attempt(s); still on ${page.url()}`);
      }
      await page.waitForTimeout(8_000);
    }
  }
}

/**
 * Navigate to `path` in the shared journey page, recovering if the SPA boot
 * bounces to /login. A bounce right after a navigation is possible even with
 * the server-side grace window (fixtures.ts) — the guard must therefore run
 * AFTER the navigation, not before it: sign in through the form and retry.
 */
async function uiGoto(page: import("@playwright/test").Page, path: string): Promise<void> {
  for (let attempt = 0; attempt < 2; attempt++) {
    await page.goto(path);
    if (!page.url().includes("login")) return;
    await formLogin(page);
  }
  if (page.url().includes("login")) {
    throw new Error(`still bounced to login after form sign-in: ${page.url()}`);
  }
}

test.describe.serial("NexusOps end-to-end journey", () => {
  let agentToken = "";

  test("register a user then log in through the UI", async ({ browser, auth }) => {
    // The ONLY auth-flow test, so it gets its own clean, unauthenticated
    // context — its sign-outs must not revoke the shared admin session the
    // other tests rely on (fixtures.ts).
    const context = await browser.newContext({ baseURL: "http://127.0.0.1:8080" });
    const page = await context.newPage();
    try {
      await page.goto("/");
      await expect(page).toHaveURL(/\/(login)?$/);
      if (!page.url().includes("login")) {
        // Session cookie from a previous run: sign out first for a clean slate.
        await page.getByRole("button", { name: /sign out/i }).click();
        await expect(page).toHaveURL(/login/);
      }

      if (auth.freshDatabase) {
        // Truly fresh install: public signup bootstraps the system.
        await page.getByRole("tab", { name: /register/i }).click();
        await page.getByLabel("Full name").fill(ADMIN.full_name);
        await page.getByLabel("Email").fill(ADMIN.email);
        await page.getByLabel("Password", { exact: true }).fill(ADMIN.password);
        await page.getByRole("button", { name: /create account|register/i }).click();
      } else {
        // Seeded database: signup is invite-only by design. Exercise the invite
        // path instead — create a user as admin, take its one-time password,
        // sign out, then register-login as the new user.
        await page.getByLabel("Email").fill(ADMIN.email);
        await page.getByLabel("Password").fill(ADMIN.password);
        await page.getByRole("button", { name: /sign in/i }).click();
        await expect(page).toHaveURL("/");

        await page.goto("/settings/users");
        await page.getByRole("button", { name: /add user|new user|invite/i }).click();
        await page.getByLabel("Full name").fill(`E2E User ${UNIQUE}`);
        await page.getByLabel("Email").fill(`e2e-user-${UNIQUE}@nexusops.example.com`);
        // The invite dialog labels its field "Initial password" and requires a
        // role before "Send invite" enables; an explicit password skips the
        // one-time secret display, so the login below can reuse it.
        await page.getByLabel("Initial password").fill("e2e-password-123");
        await page.getByLabel("Role", { exact: true }).selectOption({ label: "Operator" });
        await page.getByRole("button", { name: /send invite/i }).click();

        await page.getByRole("button", { name: /sign out/i }).click();
        await expect(page).toHaveURL(/login/);

        await page.getByLabel("Email").fill(`e2e-user-${UNIQUE}@nexusops.example.com`);
        await page.getByLabel("Password", { exact: true }).fill("e2e-password-123");
        await page.getByRole("button", { name: /sign in/i }).click();
      }

      await expect(page).toHaveURL("/");
      // The badge renders twice (sidebar + dashboard header); scope to the
      // dashboard to keep the assertion strict-mode safe.
      await expect(page.getByRole("main").getByText(/simulation mode/i)).toBeVisible();
    } finally {
      await context.close();
    }
  });

  test("logout and login again as the seeded admin", async ({ page }) => {
    await uiGoto(page, "/");
    await expect(page.locator(".stat-card").first()).toBeVisible();

    await page.getByRole("button", { name: /sign out/i }).click();
    await expect(page).toHaveURL(/login/);

    await page.getByLabel("Email").fill(ADMIN.email);
    await page.getByLabel("Password", { exact: true }).fill(ADMIN.password);
    await page.getByRole("button", { name: /sign in/i }).click();
    await expect(page).toHaveURL("/");
    await expect(page.locator(".stat-card").first()).toBeVisible();
  });

  test("add a server, enroll an agent; heartbeat brings it ONLINE with containers", async ({
    page,
    request,
  }) => {
    const name = `e2e-node-${UNIQUE}`;
    await uiGoto(page, "/servers");
    await page.getByRole("button", { name: /add server|new server/i }).click();
    // The register dialog renders required labels as "Name *" / "Hostname *"
    // and its submit is "Register server".
    await page.getByLabel(/^name\b/i).fill(name);
    await page.getByLabel(/^hostname\b/i).fill(`${name}.test`);
    await page.getByRole("button", { name: /register server/i }).click();
    await expect(page.getByText(name).first()).toBeVisible();

    // Enrollment token is revealed exactly once on the detail view.
    await page.getByText(name).first().click();
    await page.getByRole("button", { name: /issue agent token/i }).click();
    agentToken = await page.getByLabel("Token", { exact: true }).inputValue();
    expect(agentToken).toMatch(/^nxa_/);

    // A real ingest round-trip with the same payload contract as the agent.
    const beat = await request.post("/api/v1/agent/heartbeat", {
      headers: { "X-Agent-Token": agentToken },
      data: {
        cpu_percent: 42.5,
        mem_used_mb: 2048,
        mem_percent: 51.2,
        disk_used_gb: 30,
        disk_percent: 48,
        net_rx_kb_s: 120,
        net_tx_kb_s: 90,
        load1: 0.8,
        uptime_seconds: 7200,
        containers: [
          {
            container_id: `e2e${String(UNIQUE).slice(-10)}aa`,
            name: "demo-web",
            status: "RUNNING",
            health: "HEALTHY",
            image_ref: "nginx:1.27-alpine",
            restart_count: 0,
          },
        ],
      },
    });
    expect(beat.status()).toBe(204);

    await expect(page.getByText("ONLINE").first()).toBeVisible({ timeout: 30_000 });
    await expect(page.getByText("demo-web")).toBeVisible();
  });

  test("uptime monitor fails → incident opens → email lands in mailpit", async ({ page }) => {
    // Default per-test timeout (120s) is too tight for threshold-crossing
    // waits (DOWN on first failing check, incident after the 3rd).
    test.setTimeout(240_000);
    const monitorName = `e2e-monitor-${UNIQUE}`;
    await uiGoto(page, "/monitors");
    await page.getByRole("button", { name: /new monitor|add monitor/i }).click();
    await page.getByLabel(/^name$/i).fill(monitorName);
    await page.getByLabel(/url/i).fill("sim://probe/always-down");
    // Short interval: the incident only opens after failure_threshold (3)
    // consecutive failing checks, and the default 60s cadence would stretch
    // that past the assertion windows below.
    await page.getByLabel(/interval/i).fill("10");
    // The dialog's submit reads "Create monitor" (and "Save changes" when editing).
    await page.getByRole("button", { name: /create monitor/i }).click();
    await expect(page.getByText(monitorName).first()).toBeVisible();

    await page.getByText(monitorName).first().click();
    await expect(page.locator(".badge.DOWN").first()).toBeVisible({ timeout: 60_000 });

    await page.goto("/incidents");
    const incidentCard = page.getByText(monitorName, { exact: false });
    await expect(incidentCard.first()).toBeVisible({ timeout: 90_000 });
    await expect(page.locator(".badge.OPEN").first()).toBeVisible();
  });

  test("notification delivery reached the mailpit sink", async ({ api, mailpit }) => {
    // The seeded EMAIL channel subscribes to MONITOR_DOWN; the previous step
    // opened an incident, so at least one delivery must have been rendered.
    const deliveries = await api.get("/api/v1/notification-channels/deliveries?limit=20");
    expect(deliveries.ok()).toBeTruthy();
    const body = (await deliveries.json()) as { items: Array<{ event_type: string }> };
    expect(
      body.items.some((d) => ["MONITOR_DOWN", "INCIDENT_OPENED"].includes(d.event_type)),
    ).toBeTruthy();

    // And the actual SMTP message exists in mailpit.
    await expect
      .poll(async () => ((await (await mailpit.fetch("/api/v1/messages?limit=30")).json()) as { total: number }).total, {
        timeout: 60_000,
        interval: 5_000,
      })
      .toBeGreaterThan(0);
  });

  test("monitor recovers after URL fix → incident resolves automatically", async ({ page, api }) => {
    const list = (await (await api.fetch("/api/v1/monitors?limit=100")).json()) as {
      items: Array<{ id: string; name: string }>;
    };
    // Target THIS run's monitor exactly: older runs leave their own
    // always-down monitors (60s cadence) behind, which would recover too
    // slowly and only after opening a fresh incident.
    const monitor = list.items.find((m) => m.name === `e2e-monitor-${UNIQUE}`);
    expect(monitor).toBeDefined();

    const updated = await api.fetch(`/api/v1/monitors/${monitor.id}`, {
      method: "PATCH",
      // Playwright's request context takes `data` (JSON-encoded automatically);
      // a raw `body` option is silently dropped, leaving the PATCH empty.
      data: { url: "sim://probe/healthy" },
    });
    expect(
      updated.status(),
      `monitor PATCH failed: ${updated.status()} ${await updated.text()}`,
    ).toBeLessThan(300);

    await uiGoto(page, "/incidents");
    await expect(page.locator(".badge.RESOLVED").first()).toBeVisible({ timeout: 120_000 });
  });

  test("deployment of a good version succeeds", async ({ page }) => {
    // Queue pickup by the worker + 7 simulated steps can take a while.
    test.setTimeout(180_000);
    const version = `2.${UNIQUE % 100}.0`;
    await uiGoto(page, "/deployments");
    // The trigger dialog lives on the deployments page and requires the
    // application + environment selects before "Queue deployment" enables.
    await page.getByRole("button", { name: /trigger deployment/i }).click();
    await page.getByLabel("Application").selectOption({ label: "platform-api — Demo Platform" });
    await page.getByLabel("Environment").selectOption({ label: "production" });
    await page.getByLabel("Version", { exact: true }).fill(version);
    await page.getByRole("button", { name: /queue deployment/i }).click();

    // Open THIS run's deployment (list is newest-first) — a bare global badge
    // assertion would also match seeded successes from earlier runs.
    await page.getByText(version).first().click();
    await expect(page.locator(".badge.SUCCESS").first()).toBeVisible({ timeout: 120_000 });
  });

  test("deployment of a -broken version fails with visible step error", async ({ page }) => {
    test.setTimeout(180_000);
    const version = `9.${UNIQUE % 100}.0-broken`;
    await uiGoto(page, "/deployments");
    await page.getByRole("button", { name: /trigger deployment/i }).click();
    await page.getByLabel("Application").selectOption({ label: "platform-api — Demo Platform" });
    await page.getByLabel("Environment").selectOption({ label: "production" });
    await page.getByLabel("Version", { exact: true }).fill(version);
    await page.getByRole("button", { name: /queue deployment/i }).click();

    // Simulated runner fails HEALTH_CHECK for versions ending in -broken.
    // Open THIS run's detail page, not any historical failure.
    await page.getByText(version).first().click();
    await expect(page.locator(".badge.FAILED").first()).toBeVisible({ timeout: 120_000 });
    await expect(page.getByText(/health.?check/i).first()).toBeVisible();
  });

  test("audit trail captured the journey's mutations", async ({ page }) => {
    await uiGoto(page, "/audit-logs");
    // The unfiltered trail is newest-first and the journey's own login/rotation
    // audits fill the first page — filter by exact action instead. The action
    // filter matches equality (`AuditLog.action == action`), and the toolbar
    // form submits on Enter.
    const actionInput = page.getByLabel("Action");
    for (const action of ["server.create", "monitor.create", "user.create"]) {
      await actionInput.fill(action);
      await actionInput.press("Enter");
      await expect(page.getByText(action).first()).toBeVisible();
    }
  });

  test("live event stream updates without reload", async ({ page, api }) => {
    await uiGoto(page, "/events");
    await expect(page.locator("table.data tbody tr").first()).toBeVisible();

    // Trigger an event that ALWAYS fires: renaming a monitor emits
    // MONITOR_UPDATED. (`check-now` on an UP monitor emits nothing — events
    // are transition-only.) Target THIS run's monitor; older runs leave
    // theirs behind.
    const list = (await (await api.fetch("/api/v1/monitors?limit=100")).json()) as {
      items: Array<{ id: string; name: string }>;
    };
    const monitor = list.items.find((m) => m.name === `e2e-monitor-${UNIQUE}`);
    expect(monitor).toBeDefined();

    // The events page caps its first page at LIMIT rows: a live prepend also
    // drops the oldest row, so the row COUNT cannot grow even when delivery
    // works. Assert on the new event's content appearing — which is what
    // "live" means anyway.
    const newName = `${monitor.name}-live`;
    const patched = await api.fetch(`/api/v1/monitors/${monitor.id}`, {
      method: "PATCH",
      // Playwright's request context takes `data` (JSON-encoded automatically);
      // a raw `body` option is silently dropped, leaving the PATCH empty.
      data: { name: newName },
    });
    expect(
      patched.status(),
      `monitor PATCH failed: ${patched.status()} ${await patched.text()}`,
    ).toBeLessThan(300);

    // Only the WS live-prepend can surface this row — no reload happens.
    await expect(page.getByText(newName).first()).toBeVisible({ timeout: 45_000 });
  });
});
