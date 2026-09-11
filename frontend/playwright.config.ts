import { defineConfig } from "@playwright/test";

/**
 * E2E runs against a fully composed stack (make up):
 *   web    http://127.0.0.1:8080   (nginx edge)
 *   api    /api/v1 behind the edge
 *   mailpit http://127.0.0.1:8025  (SMTP sink)
 * Requires SIMULATION_MODE=true and a freshly migrated+seeded database
 * (`make clean && make up` gives a deterministic state).
 */
export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 2 : 0,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: "http://127.0.0.1:8080",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
});
