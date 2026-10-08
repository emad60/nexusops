/**
 * Phase 2 journey — projects, environments, configuration layering and secrets.
 *
 *   login → select organization → open a project → create a Production
 *   environment → configure the project base config → configure environment
 *   overrides → create an environment secret → verify metadata → rotate →
 *   verify version history → roll back → verify history survives → verify a
 *   second organization cannot reach the project, the environment or the secret.
 *
 * Deliberately performs **no deployment**: Phase 2 ends at configuration and
 * secrets; real delivery is a later phase. Runs against the composed stack
 * (`make e2e`), which starts from a fresh migrated + seeded volume.
 *
 * The cross-tenant checks run last on purpose — they are the only step that adds
 * a second organization to the admin's membership list, which changes the
 * top-bar organization control from a label into a select for any page loaded
 * afterwards.
 */

import type { Page } from "@playwright/test";
import { expect } from "@playwright/test";

import { test } from "./fixtures";
import { EDGE } from "./env";

const UNIQUE = Date.now();
const ADMIN = {
  email: "admin@nexusops.example.com",
  password: "nexusops-admin",
};

const PROJECT_NAME = "Demo Platform";
const ENV_NAME = `staging-${UNIQUE}`;
const FLAG_KEY = `E2E_FLAG_${UNIQUE}`;
const SECRET_KEY = `E2E_SECRET_${UNIQUE}`;

/** The shared journey page, recovered if the SPA boot bounces to /login. */
async function uiGoto(page: Page, path: string): Promise<void> {
  for (let attempt = 0; attempt < 2; attempt++) {
    await page.goto(path);
    if (!page.url().includes("login")) return;
    await page.getByLabel("Email").fill(ADMIN.email);
    await page.getByLabel("Password", { exact: true }).fill(ADMIN.password);
    await page.getByRole("button", { name: /sign in/i }).click();
    await expect(page).toHaveURL("/", { timeout: 10_000 });
  }
  if (page.url().includes("login")) {
    throw new Error(`still bounced to login after sign-in: ${page.url()}`);
  }
}

/** Open the project and return to its detail page. */
async function openProject(page: Page): Promise<void> {
  await uiGoto(page, "/projects");
  // The project card links to its detail page.
  await page.getByRole("link", { name: new RegExp(PROJECT_NAME) }).first().click();
  await expect(page.getByRole("heading", { name: PROJECT_NAME })).toBeVisible();
}

test.describe.serial("Phase 2 journey — projects, environments & secrets", () => {
  test("login, select the organization and open the project", async ({ page }) => {
    await uiGoto(page, "/");
    // Tenancy is never inferred: the shell always shows which organization it
    // acts in (a single membership renders as a label, not a select).
    await expect(page.getByTitle("Active organization")).toBeVisible();

    await openProject(page);
    // The seeded project already has a project-scoped Production environment.
    // Scoped to the project-level region: each application card also has an
    // "Environments" sub-heading (it deploys into the project's environments).
    const envsRegion = page.getByRole("region", { name: "Environments" });
    await expect(envsRegion.getByRole("heading", { name: "Environments" })).toBeVisible();
    await expect(envsRegion.getByText("production").first()).toBeVisible();
    await expect(envsRegion.getByText("Production").first()).toBeVisible();
  });

  test("create a Production environment from the project page", async ({ page }) => {
    await openProject(page);
    await page.getByRole("button", { name: "+ Add environment" }).click();

    const dialog = page.getByRole("dialog");
    await expect(dialog.getByRole("heading", { name: "New environment" })).toBeVisible();
    await dialog.getByLabel("Name").fill(ENV_NAME);
    await dialog.getByLabel("Type").selectOption("PROD");
    await dialog
      .getByLabel(/Config \(one KEY=VALUE per line\)/)
      .fill(`LOG_LEVEL=info\n${FLAG_KEY}=base`);
    await dialog.getByRole("button", { name: "Create environment" }).click();

    // The environment now belongs to the project and is listed with its type.
    const row = page.getByRole("row").filter({ hasText: ENV_NAME });
    await expect(row).toBeVisible();
    await expect(row.getByText("Production")).toBeVisible();
    await expect(row.getByText(`${FLAG_KEY}=base`)).toBeVisible();
  });

  test("configure the project base configuration", async ({ page }) => {
    await openProject(page);
    await page.getByRole("button", { name: "Edit project" }).click();

    const dialog = page.getByRole("dialog");
    await dialog
      .getByLabel(/Project config/)
      .fill(`LOG_LEVEL=info\nREGION=eu\n${FLAG_KEY}=base`);
    await dialog.getByRole("button", { name: "Save changes" }).click();
    await expect(dialog).toBeHidden();

    // Re-open: the value must have round-tripped through the API, not just the
    // local textarea. (The project page renders environment overrides, not the
    // base config — the layered view lives on the environment page.)
    await page.getByRole("button", { name: "Edit project" }).click();
    const reopened = page.getByRole("dialog");
    await expect(reopened.getByLabel(/Project config/)).toHaveValue(
      new RegExp(`${FLAG_KEY}=base`),
    );
    await reopened.getByRole("button", { name: "Cancel" }).click();
    await expect(reopened).toBeHidden();
  });

  test("configure the environment overrides and see them win in the effective config", async ({
    page,
  }) => {
    await openProject(page);
    await page
      .getByRole("link", { name: new RegExp(ENV_NAME) })
      .first()
      .click();
    await expect(page.getByRole("heading", { name: new RegExp(ENV_NAME) })).toBeVisible();

    // Project base config is shown separately from the environment overrides.
    await expect(
      page.getByRole("heading", { name: "Project configuration (base)" }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "Environment overrides" }),
    ).toBeVisible();

    await page
      .getByLabel(/Environment overrides/)
      .fill(`LOG_LEVEL=debug\n${FLAG_KEY}=override`);
    await page.getByRole("button", { name: "Save overrides" }).click();

    // Effective config: the override wins for the flagged key, the untouched
    // project key (REGION) is inherited.
    const effective = page.getByRole("region", { name: "Environment configuration" });
    await expect(effective.getByText(`${FLAG_KEY}=override`)).toBeVisible();
    await expect(effective.getByText("REGION=eu").first()).toBeVisible();
    await expect(effective.getByText(/overridden/).first()).toBeVisible();
  });

  test("create an environment-scoped secret and verify its metadata", async ({ page }) => {
    await uiGoto(page, "/projects");
    await page.getByRole("link", { name: new RegExp(PROJECT_NAME) }).first().click();
    await page
      .getByRole("link", { name: new RegExp(ENV_NAME) })
      .first()
      .click();

    await page.getByRole("button", { name: "+ New environment secret" }).click();
    const dialog = page.getByRole("dialog");
    await expect(dialog.getByRole("heading", { name: /New secret in/ })).toBeVisible();
    await dialog.getByLabel("Key").fill(SECRET_KEY);
    await dialog.getByLabel("Value").fill(`s3cret-${UNIQUE}`);
    await dialog.getByLabel("Description").fill("phase 2 journey secret");
    await dialog.getByRole("button", { name: "Create secret" }).click();

    // Metadata only: key, scope, version, digest — never a value.
    const row = page.getByRole("row").filter({ hasText: SECRET_KEY });
    await expect(row).toBeVisible();
    await expect(row.getByText("v1")).toBeVisible();
    await expect(page.getByText(`s3cret-${UNIQUE}`)).toHaveCount(0);
  });

  test("rotate the secret, verify version history, then roll back non-destructively", async ({
    page,
  }) => {
    await uiGoto(page, "/projects");
    await page.getByRole("link", { name: new RegExp(PROJECT_NAME) }).first().click();
    await page
      .getByRole("link", { name: new RegExp(ENV_NAME) })
      .first()
      .click();

    await page.getByRole("button", { name: `Version history of ${SECRET_KEY}` }).click();
    const dialog = page.getByRole("dialog");
    // v1 is current and its digest is shown — metadata, not a value.
    await expect(dialog.getByText("v1")).toBeVisible();

    await dialog.getByRole("button", { name: "Rotate to a new version" }).click();
    await dialog.getByLabel(/^New value/).fill(`rotated-${UNIQUE}`);
    await dialog.getByRole("button", { name: "Rotate secret" }).click();

    await expect(dialog.getByText("v2")).toBeVisible();
    await expect(dialog.getByText("previous", { exact: false }).first()).toBeVisible();

    // Roll back to v1: history is re-appended, never rewritten.
    await dialog.getByRole("button", { name: `Roll back ${SECRET_KEY} to v1` }).click();
    await expect(dialog.getByText("v3")).toBeVisible();

    // v1 and v2 are still there — nothing was deleted or overwritten. (The cell
    // text is "v1 previous", so these match on substring, not exact text.)
    await expect(dialog.getByText("v1", { exact: false })).toBeVisible();
    await expect(dialog.getByText("v2", { exact: false })).toBeVisible();
    await expect(dialog.getByText("previous", { exact: false }).first()).toBeVisible();
    await expect(dialog).toHaveText(/nothing is deleted or overwritten/i);
    // The header ✕ also carries the accessible name "Close"; scope to the
    // footer action so the choice is unambiguous.
    await dialog.locator(".modal-actions").getByRole("button", { name: "Close" }).click();
  });

  test("another organization cannot reach the project, its environment or its secret", async ({
    api,
    apiToken,
    playwright,
  }) => {
    // A second tenant owned by the same admin: it removes every *authentication*
    // difference, so what remains is purely the organization boundary.
    const created = await api.post("/api/v1/organizations", {
      data: { name: `Phase 2 Other ${UNIQUE}`, description: "cross-tenant probe" },
    });
    expect(created.status(), await created.text()).toBe(201);
    const otherOrgId = ((await created.json()) as { organization: { id: string } }).organization.id;

    // Resolve the ids of the resources created by this journey (as the owner).
    const projects = (await (await api.fetch("/api/v1/projects?limit=100")).json()) as {
      items: Array<{ id: string; name: string }>;
    };
    const project = projects.items.find((p) => p.name === PROJECT_NAME);
    expect(project, "seeded project not found").toBeDefined();

    const envs = (await (
      await api.fetch(`/api/v1/projects/${project?.id}/environments?limit=100`)
    ).json()) as { items: Array<{ id: string; name: string }> };
    const environment = envs.items.find((e) => e.name === ENV_NAME);
    expect(environment, "journey environment not found").toBeDefined();

    const secrets = (await (
      await api.fetch(`/api/v1/secrets?limit=100&q=${SECRET_KEY}`)
    ).json()) as { items: Array<{ id: string; key: string }> };
    const secret = secrets.items.find((s) => s.key === SECRET_KEY);
    expect(secret, "journey secret not found").toBeDefined();

    // Same token, same user, different X-Org-Id.
    const other = await playwright.request.newContext({
      baseURL: EDGE,
      extraHTTPHeaders: {
        Authorization: `Bearer ${apiToken.token}`,
        "X-Org-Id": otherOrgId,
      },
    });
    try {
      // The project is not visible in the other organization at all.
      const projectList = (await (await other.fetch("/api/v1/projects?limit=100")).json()) as {
        items: Array<{ id: string }>;
      };
      expect(projectList.items.map((p) => p.id)).not.toContain(project?.id);

      for (const path of [
        `/api/v1/projects/${project?.id}`,
        `/api/v1/projects/${project?.id}/environments`,
        `/api/v1/projects/${project?.id}/environments/${environment?.id}`,
        `/api/v1/secrets/${secret?.id}`,
        `/api/v1/secrets/${secret?.id}/versions`,
      ]) {
        const response = await other.get(path);
        expect(response.status(), `GET ${path} leaked across tenants`).toBe(404);
      }

      // Mutations are refused too, and the project cannot be used as a handle
      // to create anything in the other organization.
      for (const path of [
        `/api/v1/secrets/${secret?.id}/rotate`,
        `/api/v1/secrets/${secret?.id}/rollback`,
      ]) {
        const response = await other.post(path, { data: { value: "x", version: 1 } });
        expect(response.status(), `POST ${path} crossed the tenant boundary`).not.toBe(200);
        expect(response.status(), `POST ${path} crossed the tenant boundary`).not.toBe(204);
      }

      const patched = await other.patch(
        `/api/v1/projects/${project?.id}/environments/${environment?.id}`,
        { data: { name: "hijacked" } },
      );
      expect(patched.status(), "PATCH crossed the tenant boundary").toBe(404);

      // And the key does not become visible through the other tenant's listing.
      const otherSecrets = (await (await other.fetch("/api/v1/secrets?limit=100")).json()) as {
        items: Array<{ key: string }>;
      };
      expect(otherSecrets.items.map((s) => s.key)).not.toContain(SECRET_KEY);
    } finally {
      await other.dispose();
    }

    // The owner's own organization still sees everything — the boundary is
    // between tenants, not a blanket denial.
    const own = await api.get(`/api/v1/secrets/${secret?.id}`);
    expect(own.status()).toBe(200);
    const ownEnv = await api.get(
      `/api/v1/projects/${project?.id}/environments/${environment?.id}`,
    );
    expect(ownEnv.status()).toBe(200);
  });
});
