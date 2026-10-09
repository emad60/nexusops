import { execFileSync, spawn, type ChildProcess } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { EDGE } from "./env";
import { expect, test } from "./fixtures";

/**
 * Phase 3 journey — an **isolated real agent** against the throwaway stack.
 *
 * Unlike the simulated providers the other specs use, this one enrolls an actual
 * `agent/nexusops_agent.py` process running on the Playwright host:
 *
 *   enrollment token → `/agent/enroll` → node credential → hello (capabilities)
 *   → heartbeat → control plane queues `container.stop` → the agent claims it,
 *   calls the Docker API, reports the result → the operation reaches SUCCEEDED
 *   and the host container is really stopped.
 *
 * The control plane is on `127.0.0.1`, which the agent's HTTPS-only rule exempts
 * (the credential cannot leave the loopback host), so no TLS is involved. The
 * spec skips itself when Docker is not reachable on the host rather than failing
 * an environment that cannot run a real container.
 */

const REPO_ROOT = path.resolve(fileURLToPath(new URL(".", import.meta.url)), "../..");
const AGENT = path.join(REPO_ROOT, "agent", "nexusops_agent.py");

function dockerAvailable(): boolean {
  try {
    execFileSync("docker", ["info"], { stdio: "ignore" });
    return true;
  } catch {
    return false;
  }
}

function docker(args: string[]): string {
  return execFileSync("docker", args, { encoding: "utf8" }).trim();
}

interface NodeDetail {
  status: string;
  agent_version: string;
  protocol_version: number | null;
  capabilities: Record<string, { present?: boolean }>;
  capabilities_reported: boolean;
}

interface OperationRow {
  id: string;
  status: string;
  result: Record<string, unknown> | null;
  error_code: string | null;
}

test.describe("agent v2 — enrollment and an operation end to end", () => {
  test.skip(!dockerAvailable(), "docker is not reachable on the host");

  test("enrolls a real agent, then delivers and completes a container operation", async ({
    api,
    page,
  }) => {
    const stamp = Date.now();
    const nodeName = `e2e-agent-${stamp}`;
    const containerName = `nexusops-e2e-${stamp}`;
    const tokenFile = path.join(os.tmpdir(), `nexusops-e2e-token-${stamp}`);

    // 1. A placeholder node the enrollment token will claim.
    const created = await api.post("/api/v1/nodes", {
      data: { name: nodeName, hostname: `${nodeName}.internal`, environment: "production" },
    });
    expect(created.status(), await created.text()).toBe(201);
    const nodeId = ((await created.json()) as { id: string }).id;

    // 2. Mint a single-use enrollment token bound to that node.
    const minted = await api.post("/api/v1/nodes/enrollment-tokens", {
      data: { name: `e2e-${stamp}`, node_id: nodeId, expires_in_seconds: 600 },
    });
    expect(minted.status(), await minted.text()).toBe(201);
    const tokenBody = (await minted.json()) as { id: string; token: string; state: string };
    expect(tokenBody.token.startsWith("nxk_")).toBeTruthy();
    expect(tokenBody.state).toBe("ACTIVE");

    // The raw token is shown exactly once: the listing exposes no token value.
    const listing = await api.get("/api/v1/nodes/enrollment-tokens?limit=20");
    const listText = await listing.text();
    expect(listText).toContain(tokenBody.id);
    expect(listText).not.toContain(tokenBody.token);

    // 3. A real container for the agent to act on (its Docker API target).
    // No ``--rm``: the stopped container must remain inspectable after the
    // operation, which is how the test proves it really stopped.
    const containerId = docker([
      "run",
      "-d",
      "--name",
      containerName,
      "alpine",
      "sleep",
      "600",
    ]);

    let agent: ChildProcess | null = null;
    try {
      // 4. Start the real agent against the edge. Loopback HTTP is permitted.
      agent = spawn(
        "python3",
        [
          AGENT,
          "--server",
          EDGE,
          "--token",
          tokenBody.token,
          "--token-file",
          tokenFile,
          "--interval",
          "5",
        ],
        { stdio: ["ignore", "pipe", "pipe"] },
      );
      const agentLog: string[] = [];
      agent.stdout?.on("data", (chunk) => agentLog.push(String(chunk)));
      agent.stderr?.on("data", (chunk) => agentLog.push(String(chunk)));

      // 5. The node comes ONLINE with a real, Docker-proven capability.
      await expect
        .poll(
          async () => {
            const res = await api.get(`/api/v1/nodes/${nodeId}`);
            if (!res.ok()) return `http-${res.status()}`;
            const body = (await res.json()) as NodeDetail;
            return `${body.status}:${body.capabilities?.docker?.present === true}`;
          },
          { timeout: 60_000, intervals: [1_000, 2_000] },
        )
        .toBe("ONLINE:true");

      const detail = (await (await api.get(`/api/v1/nodes/${nodeId}`)).json()) as NodeDetail;
      expect(detail.agent_version).toMatch(/^\d+\.\d+\.\d+/);
      expect(detail.protocol_version).toBe(2);
      expect(detail.capabilities_reported).toBe(true);
      expect(detail.capabilities.docker?.present).toBe(true);

      // 6. Dispatch a whitelisted operation and let the agent execute it.
      const dispatch = await api.post("/api/v1/operations", {
        data: { node_id: nodeId, type: "container.stop", params: { container_id: containerId } },
      });
      expect(dispatch.status(), await dispatch.text()).toBe(201);
      const operationId = ((await dispatch.json()) as OperationRow).id;

      await expect
        .poll(
          async () => {
            const res = await api.get(`/api/v1/operations/${operationId}`);
            return ((await res.json()) as OperationRow).status;
          },
          { timeout: 60_000, intervals: [1_000, 2_000] },
        )
        .toBe("SUCCEEDED");

      const final = (await (
        await api.get(`/api/v1/operations/${operationId}`)
      ).json()) as OperationRow;
      expect(final.error_code).toBeNull();
      expect(final.result).toBeTruthy();

      // The operation was not merely queued: the host container really stopped.
      expect(docker(["inspect", "-f", "{{.State.Running}}", containerId])).toBe("false");

      // 7. The dashboard shows the same truth — agent version, capability and a
      //    succeeded operation (never "queued" rendered as success).
      await page.goto(`/nodes/${nodeId}`);
      await expect(page.getByText(detail.agent_version, { exact: false })).toBeVisible();
      await expect(page.getByText("Capabilities")).toBeVisible();
      await expect(page.getByText("container.stop")).toBeVisible();
      await expect(page.getByText("SUCCEEDED")).toBeVisible();
    } finally {
      agent?.kill("SIGTERM");
      try {
        docker(["rm", "-f", containerId]);
      } catch {
        /* the container may already be gone */
      }
      fs.rmSync(tokenFile, { force: true });
      await api.delete(`/api/v1/nodes/${nodeId}`).catch(() => undefined);
    }
  });
});
