/**
 * The full NexusOps journey, exactly as specified:
 *
 *   register → login → add server → agent heartbeat → create uptime monitor
 *   → monitor fails → incident opens + notification sent → recovery
 *   → deployment succeeds → deployment fails → audit trail shows everything
 *
 * Runs against the composed stack (`make up`): nginx edge on :8080, mailpit on
 * :8025, SIMULATION_MODE=true. Both are overridable via E2E_BASE_URL /
 * E2E_MAILPIT_URL so `make e2e` can use its own ports. The seeded database
 * provides fleet + channels; this spec creates its own user, server, monitors
 * and deployments.
 */

import { expect } from "@playwright/test";
import { test } from "./fixtures";
import { EDGE } from "./env";

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
/**
 * Count `subscribed` acks received by the app's *global-channel* socket.
 *
 * Registering before navigation makes the WebSocket handshake explicit: a
 * `subscribed` frame only arrives after the upgrade, the auth frame and the
 * subscribe were all accepted. A rejected handshake (the pre-upgrade 403 this
 * harness hit) then fails fast and specifically, instead of surfacing minutes
 * later as a generic "element not found" timeout on a live-event assertion.
 */
function trackGlobalSubscribeAcks(page: import("@playwright/test").Page) {
  let acks = 0;
  page.on("websocket", (ws) => {
    if (!ws.url().includes("/api/v1/ws")) return;
    ws.on("framereceived", (frame) => {
      try {
        const parsed = JSON.parse(frame.payload) as { type?: string; channel?: string };
        if (parsed.type === "subscribed" && parsed.channel === "global") acks += 1;
      } catch {
        // Binary/log frames are not control frames.
      }
    });
  });
  return { count: () => acks };
}

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
    const context = await browser.newContext({ baseURL: EDGE });
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
        // Reuse the retrying helper: on a cold stack the login form can be
        // re-rendered while the first paint settles, and a single fill+click
        // then submits nothing. `formLogin` re-fills and honors the
        // fail-closed login limiter instead of racing it.
        await formLogin(page);

        await page.goto("/settings/users");
        await page.getByRole("button", { name: /add user|new user|invite/i }).click();
        await page.getByLabel("Full name").fill(`E2E User ${UNIQUE}`);
        await page.getByLabel("Email").fill(`e2e-user-${UNIQUE}@nexusops.example.com`);
        // The invite dialog labels its field "Initial password" and requires a
        // role before "Send invite" enables; an explicit password skips the
        // one-time secret display, so the login below can reuse it.
        await page.getByLabel("Initial password").fill("e2e-password-123");
        // By id, not by label text: the field is `required`, so its label text
        // reads "Role *" (see form.tsx), and the users table behind the modal
        // has aria-labelled "Role for <email>" selects that a loose label match
        // would hit as well.
        await page.locator("#invite-role").selectOption({ label: "Operator" });
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
    await uiGoto(page, "/nodes");
    await page.getByRole("button", { name: /add node|new node/i }).click();
    // The register dialog renders required labels as "Name *" / "Hostname *"
    // and its submit is "Register node".
    await page.getByLabel(/^name\b/i).fill(name);
    await page.getByLabel(/^hostname\b/i).fill(`${name}.test`);
    await page.getByRole("button", { name: /register node/i }).click();
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
    // The containers table refetches on a 10s poll (rows arrive out-of-band
    // via the heartbeat), so allow more than one full poll interval here.
    await expect(page.getByText("demo-web")).toBeVisible({ timeout: 20_000 });
  });

  test("uptime monitor fails → incident opens → email lands in mailpit", async ({ page }) => {
    // Default per-test timeout (120s) is too tight for threshold-crossing
    // waits (DOWN on first failing check, incident after the 3rd).
    test.setTimeout(240_000);
    const monitorName = `e2e-monitor-${UNIQUE}`;
    await uiGoto(page, "/monitors");
    await page.getByRole("button", { name: /new monitor|add monitor/i }).click();
    // Required fields render their label as "Name *" (form.tsx), so this is
    // anchored on the word rather than the whole string.
    await page.getByLabel(/^name\b/i).fill(monitorName);
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
    //
    // Polled, not sampled once: the delivery row is written when the incident
    // opens, which trails the previous step's `.badge.OPEN` assertion by up to
    // a dispatcher cycle. A single read here is a race that only passes when the
    // previous step happened to run slow. (The mailpit check below polls for the
    // same reason — this assertion was the one that didn't.)
    await expect
      .poll(
        async () => {
          const response = await api.get("/api/v1/notification-channels/deliveries?limit=20");
          if (!response.ok()) return -1;
          const body = (await response.json()) as {
            items: Array<{ event_type: string }>;
          };
          return body.items.filter((d) =>
            ["MONITOR_DOWN", "INCIDENT_OPENED"].includes(d.event_type),
          ).length;
        },
        { timeout: 60_000, interval: 5_000 },
      )
      .toBeGreaterThan(0);

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
    for (const action of ["node.create", "monitor.create", "user.create"]) {
      await actionInput.fill(action);
      await actionInput.press("Enter");
      await expect(page.getByText(action).first()).toBeVisible();
    }
  });

  test("live event stream updates without reload", async ({ page, api }) => {
    const acks = trackGlobalSubscribeAcks(page);
    await uiGoto(page, "/events");
    await expect(page.locator("table.data tbody tr").first()).toBeVisible();
    // Deterministic liveness gate BEFORE triggering the event: the socket must
    // have upgraded, authenticated and subscribed, or the event can never
    // arrive regardless of how long the assertion below waits.
    await expect
      .poll(acks.count, {
        timeout: 15_000,
        message: "the global WebSocket never subscribed (handshake or auth rejected)",
      })
      .toBeGreaterThanOrEqual(1);

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

  test("live event stream reconnects after the socket drops", async ({ page, api }) => {
    test.setTimeout(120_000);
    // Expose the page's WebSocket instances so the test can drop the live
    // connection exactly as a network blip / server restart would (an
    // `onclose`) - without a reload. `context.setOffline` deliberately does
    // NOT close established sockets, so it cannot exercise reconnect.
    await page.addInitScript(() => {
      const Native = window.WebSocket;
      (window as unknown as { __sockets: WebSocket[] }).__sockets = [];
      window.WebSocket = class extends Native {
        constructor(url: string | URL, protocols?: string | string[]) {
          super(url, protocols);
          (window as unknown as { __sockets: WebSocket[] }).__sockets.push(this);
        }
      } as typeof WebSocket;
    });

    const acks = trackGlobalSubscribeAcks(page);
    await uiGoto(page, "/events");
    await expect(page.locator("table.data tbody tr").first()).toBeVisible();
    await expect.poll(acks.count, { timeout: 15_000 }).toBeGreaterThanOrEqual(1);

    // Drop every live socket the app holds; nothing else signals the page. The
    // SPA must notice and reconnect on its own or a live view goes dark.
    const dropped = await page.evaluate(() => {
      const sockets = (window as unknown as { __sockets?: WebSocket[] }).__sockets ?? [];
      for (const socket of sockets) socket.close();
      return sockets.length;
    });
    expect(dropped, "no WebSocket was exposed to drop").toBeGreaterThan(0);

    // A fresh socket upgraded, re-authenticated and re-subscribed.
    await expect
      .poll(acks.count, { timeout: 30_000, message: "the socket never reconnected after the drop" })
      .toBeGreaterThanOrEqual(2);

    // And it is live again: an event published after the reconnect still
    // reaches the page through the socket.
    const list = (await (await api.fetch("/api/v1/monitors?limit=100")).json()) as {
      items: Array<{ id: string; name: string }>;
    };
    const monitor = list.items.find((m) => m.name === `e2e-monitor-${UNIQUE}`) ?? list.items[0];
    const reconnectedName = `${monitor.name}-reconnect`;
    const patched = await api.fetch(`/api/v1/monitors/${monitor.id}`, {
      method: "PATCH",
      data: { name: reconnectedName },
    });
    expect(
      patched.status(),
      `monitor PATCH failed: ${patched.status()} ${await patched.text()}`,
    ).toBeLessThan(300);
    await expect(page.getByText(reconnectedName).first()).toBeVisible({ timeout: 45_000 });
  });
});
