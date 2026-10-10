import { execFileSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

import type { APIRequestContext } from "@playwright/test";

import { EDGE } from "./env";
import { expect, test } from "./fixtures";

/**
 * Phase 4 journey — one real `container:port` served over a real URL, end to end.
 *
 * Unlike every other spec, nothing here is simulated. The journey:
 *
 *   builds a node image that really runs nginx
 *   → enrolls the real `agent/nexusops_agent.py` **inside that node**
 *   → adds a domain and publishes the minted TXT record in a real authoritative
 *     mock DNS server (the control plane resolves the name's NS and asks *them*)
 *   → verifies the name, mirrors a real app container, and enables a route
 *   → the control plane renders a bundle, the agent stages it, runs `nginx -t`,
 *     swaps it atomically and reloads
 *   → and an HTTP request to the node's port 80 with the route's Host header
 *     reaches the app container through that nginx.
 *
 * Why containers rather than the host: the routing pre-flight requires a
 * *running* master that owns port 80, `nginx -t` to pass, and files written under
 * `/etc/nexusops/nginx` — all of which this journey must do against real nginx
 * without touching the machine it runs on.
 *
 * The node container runs with `--network host` so its nginx shares the host's
 * loopback: that is what makes `upstream_host = 127.0.0.1` (the documented
 * loopback-publish rule) reach the app container started here. It is also given
 * the docker socket so the agent mirrors containers the way a real node does.
 * That is a **root-equivalent mount into a test container** — acceptable for a
 * throwaway stack whose only dispatched operations are the whitelisted
 * `container.*` and `nginx.*` types, and not acceptable anywhere else.
 *
 * The spec skips itself when Docker is not reachable and when the mock DNS
 * server is not answering (it comes from `docker-compose.e2e.yml`, so `make e2e`
 * has it while a bare `npx playwright test` against a dev stack does not).
 */

const REPO_ROOT = path.resolve(fileURLToPath(new URL(".", import.meta.url)), "../..");
const AGENT = path.join(REPO_ROOT, "agent", "nexusops_agent.py");
const NODE_CONTEXT = path.join(REPO_ROOT, "e2e", "nginxnode");
const NODE_IMAGE = "nexusops-e2e-nginx-node:latest";

/** Authoritative mock DNS from the e2e overlay; see e2e/dnsmock/dnsmock.py. */
const DNS_CONTROL = (process.env.E2E_DNS_CONTROL_URL ?? "http://127.0.0.1:8054").replace(/\/$/, "");
const DNS_ZONE = process.env.E2E_DNS_ZONE ?? "e2e.test";

const MARKER = "NEXUSOPS_E2E_UPSTREAM_OK";

function dockerAvailable(): boolean {
  try {
    execFileSync("docker", ["info"], { stdio: "ignore" });
    return true;
  } catch {
    return false;
  }
}

function docker(args: string[]): string {
  // stderr is captured rather than inherited: a container that is already gone
  // makes `rm -f` (or a `kill` of a process that exited) fail, and that noise
  // belongs to the caller, not to the test report.
  return execFileSync("docker", args, {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  }).trim();
}

/** Docker's own port mapping, e.g. `127.0.0.1:45999` for `-p 127.0.0.1::8080`. */
function publishedPort(container: string, containerPort: number): number {
  const mapping = docker(["port", container, `${containerPort}/tcp`]);
  const match = /:(\d+)\s*$/.exec(mapping.split("\n")[0]);
  if (!match) throw new Error(`no published host port for ${container}:${containerPort}`);
  return Number(match[1]);
}

interface HttpResult {
  ok: boolean;
  status: number;
  body: string;
  error: string;
}

/** A request through the node's nginx, with the Host header the route answers on. */
function httpGet(url: string, host?: string): HttpResult {
  const args = ["-sS", "-o", "-", "-w", "\n%{http_code}", "--max-time", "10", url];
  if (host) args.unshift("-H", `Host: ${host}`);
  try {
    const out = execFileSync("curl", args, { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
    const split = out.lastIndexOf("\n");
    return {
      ok: true,
      status: Number(out.slice(split + 1)),
      body: out.slice(0, split),
      error: "",
    };
  } catch (error) {
    const failure = error as { stdout?: string; stderr?: string; message?: string };
    // `return 444` closes the connection with no response at all, so curl reports
    // an empty reply rather than a status code — that is the expected shape here.
    return {
      ok: false,
      status: 0,
      body: failure.stdout ?? "",
      error: `${failure.stderr ?? ""}${failure.message ?? ""}`.trim(),
    };
  }
}

/** The mock's control API: health, publish a record, clear a record. */
async function dnsPublish(payload: { name: string; type: string; value: string }): Promise<void> {
  const response = await fetch(`${DNS_CONTROL}/record`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`mock DNS refused the record: ${await response.text()}`);
}

async function dnsClear(name: string): Promise<void> {
  await fetch(`${DNS_CONTROL}/record?name=${encodeURIComponent(name)}`, { method: "DELETE" });
}

async function dnsZone(): Promise<string | null> {
  try {
    const response = await fetch(`${DNS_CONTROL}/health`, { signal: AbortSignal.timeout(3_000) });
    if (!response.ok) return null;
    return ((await response.json()) as { zone: string }).zone;
  } catch {
    return null;
  }
}

/**
 * Start (or restart) the management agent *inside* an already-running node
 * container, as a process that can be stopped without touching nginx.
 *
 * `exec` keeps the pidfile pointing at the agent itself, so `stopAgent` can end it
 * precisely; output goes to a file in the container rather than nowhere, so a
 * failure is diagnosable (`docker exec <node> tail /var/log/nexusops-agent.log`).
 * The container's own environment (server URL, token, nginx root) is inherited by
 * `docker exec`, so a restart re-runs exactly what the entrypoint used to run.
 */
function startAgent(container: string): void {
  docker([
    "exec",
    "-d",
    container,
    "sh",
    "-c",
    "echo $$ > /run/nexusops-agent.pid; exec python3 /opt/nexusops/nexusops_agent.py " +
      ">> /var/log/nexusops-agent.log 2>&1",
  ]);
}

/**
 * Stop the agent process and prove it is gone. nginx keeps running: the node is
 * still serving whatever configuration it last applied, it has simply stopped
 * reporting.
 */
function stopAgent(container: string): void {
  docker(["exec", container, "sh", "-c", "kill $(cat /run/nexusops-agent.pid) 2>/dev/null || true"]);
  // `[n]exusops_agent` is the classic self-match guard: the checking shell's own
  // command line contains the bracketed form, which the pattern does not match,
  // so this can only ever report a real agent process.
  const stillThere = () => {
    try {
      return docker(["exec", container, "pgrep", "-f", "[n]exusops_agent.py"]) !== "";
    } catch {
      return false; // pgrep exits non-zero when nothing matches
    }
  };
  const deadline = Date.now() + 15_000;
  while (stillThere()) {
    if (Date.now() > deadline) throw new Error(`agent ${container} did not stop`);
    execFileSync("sleep", ["0.5"]);
  }
}

/**
 * Start one real nginx node for *tenant*: a marker-serving app container on a
 * loopback-published port, a node row, a one-time enrollment token, and the real
 * agent running inside a container that mounts the host's nginx and Docker socket.
 *
 * Nodes are started one at a time by the transfer journey: the node's nginx owns
 * host port 80 (that is the whole point of the pre-flight), and two of them cannot
 * hold it at once. Each caller removes its own container before the next starts.
 */
async function startNode(
  api: APIRequestContext,
  spec: {
    tenant: Tenant;
    name: string;
    container: string;
    app: string;
    marker: string;
    /** Mark the node OFFLINE this many seconds after its last heartbeat. */
    offlineAfterSeconds?: number;
  },
): Promise<NodeHarness> {
  docker(["build", "-q", "-t", NODE_IMAGE, NODE_CONTEXT]);

  execFileSync(
    "docker",
    [
      "run",
      "-d",
      "--name",
      spec.app,
      "-p",
      "127.0.0.1::80",
      "nginx:1.27-alpine",
      "sh",
      "-c",
      `echo ${spec.marker} > /usr/share/nginx/html/index.html && exec nginx -g 'daemon off;'`,
    ],
    { stdio: ["ignore", "pipe", "pipe"] },
  );
  const upstreamPort = publishedPort(spec.app, 80);

  const created = await api.post("/api/v1/nodes", {
    headers: spec.tenant.headers,
    data: {
      name: spec.name,
      hostname: `${spec.name}.internal`,
      environment: "production",
      ...(spec.offlineAfterSeconds ? { offline_after_seconds: spec.offlineAfterSeconds } : {}),
    },
  });
  expect(created.status(), await created.text()).toBe(201);
  const nodeId = ((await created.json()) as { id: string }).id;

  const minted = await api.post("/api/v1/nodes/enrollment-tokens", {
    headers: spec.tenant.headers,
    data: { name: `${spec.name}-token`, node_id: nodeId, expires_in_seconds: 600 },
  });
  expect(minted.status(), await minted.text()).toBe(201);
  const token = ((await minted.json()) as { token: string }).token;

  execFileSync(
    "docker",
    [
      "run",
      "-d",
      "--name",
      spec.container,
      "--network",
      "host",
      "-v",
      "/var/run/docker.sock:/var/run/docker.sock",
      "-v",
      `${AGENT}:/opt/nexusops/nexusops_agent.py:ro`,
      "-e",
      `NEXUSOPS_SERVER=${EDGE}`,
      "-e",
      `NEXUSOPS_TOKEN=${token}`,
      "-e",
      "NEXUSOPS_TOKEN_FILE=/tmp/nexusops-agent-token",
      "-e",
      "NEXUSOPS_INTERVAL=3",
      "-e",
      "NEXUSOPS_NGINX_ROOT=/etc/nexusops/nginx",
      NODE_IMAGE,
      "sh",
      "-c",
      // nginx is the container's main process and the agent runs as a separate
      // process inside it (see `startAgent`). That separation is what lets the
      // transfer journey take the *management* agent away while the data plane
      // keeps serving — which is the only way to prove that a route the control
      // plane has asked to remove can still be answering, and that the platform
      // does not claim otherwise.
      "exec nginx -g 'daemon off;'",
    ],
    { stdio: ["ignore", "pipe", "pipe"] },
  );
  startAgent(spec.container);

  await expect
    .poll(
      async () => {
        const res = await api.get(`/api/v1/nodes/${nodeId}`, { headers: spec.tenant.headers });
        if (!res.ok()) return `http-${res.status()}`;
        const body = (await res.json()) as NodeDetail;
        const nginx = body.capabilities?.nginx ?? {};
        return `${body.status}:${nginx.present === true}:${nginx.routing_eligible === true}`;
      },
      { timeout: 120_000, intervals: [1_000, 2_000] },
    )
    .toBe("ONLINE:true:true");

  // The customer's own nginx.conf now carries the managed include, so an apply has
  // somewhere to land. (This is the bootstrap the first defect was found in.)
  await expect
    .poll(
      () => {
        try {
          docker(["exec", spec.container, "test", "-f", "/etc/nexusops/nginx/nexusops.conf"]);
          return "present";
        } catch {
          return "missing";
        }
      },
      { timeout: 90_000, intervals: [1_000, 2_000] },
    )
    .toBe("present");

  // The upstream picker offers this node's app on the port we just published.
  let target: RouteTargetBody | undefined;
  await expect
    .poll(
      async () => {
        const res = await api.get(`/api/v1/nodes/${nodeId}/route-targets`, {
          headers: spec.tenant.headers,
        });
        if (!res.ok()) return `http-${res.status()}`;
        const targets = (await res.json()) as RouteTargetBody[];
        target = targets.find((item) =>
          item.upstream_ports.some((port) => port.host_port === upstreamPort),
        );
        return target ? "found" : `not-found(${targets.length})`;
      },
      { timeout: 90_000, intervals: [2_000, 3_000] },
    )
    .toBe("found");

  return {
    id: nodeId,
    container: spec.container,
    app: spec.app,
    upstreamPort,
    targetId: (target as RouteTargetBody).id,
  };
}

/** Publish a name's TXT proof in the mock and verify it through the API. */
async function proveName(
  api: APIRequestContext,
  tenant: Tenant,
  domainName: string,
): Promise<{ domainId: string; recordName: string }> {
  const created = await api.post("/api/v1/domains", {
    headers: tenant.headers,
    data: { name: domainName },
  });
  expect(created.status(), await created.text()).toBe(201);
  const body = (await created.json()) as DomainBody;
  const instructions = body.verification;
  expect(instructions, "a fresh domain must hand out its TXT instructions").toBeTruthy();
  const recordName = (instructions as NonNullable<DomainBody["verification"]>).record_name;
  await dnsPublish({
    name: recordName,
    type: "TXT",
    value: (instructions as NonNullable<DomainBody["verification"]>).record_value,
  });
  const verify = await api.post(`/api/v1/domains/${body.id}/verify`, { headers: tenant.headers });
  expect(verify.status(), await verify.text()).toBe(200);
  await expect
    .poll(
      async () => {
        const res = await api.get(`/api/v1/domains/${body.id}`, { headers: tenant.headers });
        if (!res.ok()) return `http-${res.status()}`;
        return ((await res.json()) as DomainBody).status;
      },
      { timeout: 120_000, intervals: [2_000, 3_000] },
    )
    .toBe("VERIFIED");
  return { domainId: body.id, recordName };
}

/** How many routes one apply's bundle was the desired state for. */
function manifestLength(op: OperationBody): number {
  return op.params?.bundle?.manifest?.length ?? -1;
}

/**
 * `nginx.apply` operations on *nodeId* that **finished successfully with an empty
 * manifest** — the applies whose whole job was to stop serving routes.
 *
 * Counting them is how this journey proves a removal was processed exactly once,
 * instead of inferring it from a status row that a node's absence could explain.
 */
async function finishedRemovalApplies(
  api: APIRequestContext,
  tenant: Tenant,
  nodeId: string,
): Promise<OperationBody[]> {
  const listed = (await (
    await api.get("/api/v1/operations", {
      headers: tenant.headers,
      params: { node_id: nodeId, limit: "100" },
    })
  ).json()) as { items: OperationBody[] };
  return listed.items.filter(
    (op) =>
      op.type === "nginx.apply" && op.status === "SUCCEEDED" && manifestLength(op) === 0,
  );
}

/** Operations on *nodeId* of type `nginx.apply` that have not finished yet. */
async function liveApplies(
  api: APIRequestContext,
  tenant: Tenant,
  nodeId: string,
): Promise<OperationBody[]> {
  const listed = (await (
    await api.get("/api/v1/operations", {
      headers: tenant.headers,
      params: { node_id: nodeId },
    })
  ).json()) as { items: OperationBody[] };
  return listed.items.filter(
    (op) =>
      op.type === "nginx.apply" && ["PENDING", "CLAIMED", "RUNNING"].includes(op.status),
  );
}

interface NodeDetail {
  status: string;
  capabilities: Record<
    string,
    { present?: boolean; routing_eligible?: boolean; reason?: string }
  >;
  capabilities_reported: boolean;
}

interface DomainBody {
  id: string;
  name: string;
  status: string;
  verified: boolean;
  verification: { record_name: string; record_type: string; record_value: string } | null;
}

interface RouteBody {
  id: string;
  hostname: string;
  path: string;
  scheme: string;
  enabled: boolean;
  config_state: string;
  last_bundle_id: string | null;
  last_apply_error: string;
  /** `REQUESTED` (out of the desired configuration, unconfirmed) or `CONFIRMED`. */
  removal_state: "REQUESTED" | "CONFIRMED" | null;
  removal_requested_at: string | null;
  removal_confirmed_at: string | null;
  status_detail: string;
}

interface RouteTargetBody {
  id: string;
  container_id: string;
  name: string;
  upstream_ports: { host_port: number; container_port: number; upstream_host: string }[];
}

interface ProxyStatusBody {
  eligible: boolean;
  provider: string;
  drift: boolean | null;
  expected_bundle_id: string | null;
  live_bundle_id: string | null;
  route_total: number;
  route_enabled: number;
  route_in_sync: number;
  route_stale: number;
  /** Enabled routes whose removal no node has confirmed yet. */
  route_removal_pending: number;
  capability: { routing_eligible: boolean; listener_80: string };
}

interface OperationBody {
  id: string;
  type: string;
  status: string;
  params?: { bundle?: { manifest?: string[] } };
}

interface EventBody {
  type: string;
  resource_id: string | null;
  data: Record<string, unknown>;
}

interface MembershipBody {
  organization: { id: string; name: string };
}

/** One organization as the journey uses it: an id, and headers scoped to it. */
interface Tenant {
  id: string;
  headers: Record<string, string>;
}

/** A real nginx node, its agent, and the container its routes point at. */
interface NodeHarness {
  id: string;
  container: string;
  app: string;
  upstreamPort: number;
  targetId: string;
}

test.describe("domains and routes — a real nginx node, a real URL", () => {
  test.skip(!dockerAvailable(), "docker is not reachable on the host");

  test("takes an unverified name to a live route served by a real node", async ({ api, page }) => {
    const stamp = Date.now();
    const nodeName = `e2e-routing-node-${stamp}`;
    const appName = `nexusops-e2e-upstream-${stamp}`;
    const nodeContainer = `nexusops-e2e-node-${stamp}`;
    // A customer adds the name they control — the zone apex — and serves a
    // hostname under it. Coverage is one label deep, so this is a legal pairing.
    const domainName = DNS_ZONE;
    const hostname = `journey-${stamp}.${DNS_ZONE}`;

    // The mock DNS server is what makes verification real; without it this spec
    // cannot prove ownership, so say so here instead of failing obscurely later.
    const zone = await dnsZone();
    test.skip(zone === null, `mock DNS control API is not reachable at ${DNS_CONTROL}`);
    test.skip(zone !== null && zone !== DNS_ZONE, `mock DNS serves ${zone}, expected ${DNS_ZONE}`);

    let nodeId: string | null = null;
    let domainId: string | null = null;
    let routeId: string | null = null;
    let nodeUp = false;
    let appUp = false;
    let recordName = "";

    try {
      // 1. The node image really runs nginx; the agent is mounted, not copied, so
      //    the file under test is the shipped one. Cached after the first run.
      docker(["build", "-q", "-t", NODE_IMAGE, NODE_CONTEXT]);

      // 2. A placeholder node the enrollment token will claim.
      const created = await api.post("/api/v1/nodes", {
        data: { name: nodeName, hostname: `${nodeName}.internal`, environment: "production" },
      });
      expect(created.status(), await created.text()).toBe(201);
      nodeId = ((await created.json()) as { id: string }).id;

      const minted = await api.post("/api/v1/nodes/enrollment-tokens", {
        data: { name: `e2e-${stamp}`, node_id: nodeId, expires_in_seconds: 600 },
      });
      expect(minted.status(), await minted.text()).toBe(201);
      const token = ((await minted.json()) as { token: string }).token;

      // 3. The application the route will point at: a real container serving a
      //    marker on a loopback-published port. `-p 127.0.0.1::80` asks Docker for
      //    a free host port, which is exactly the loopback-publish rule the
      //    control plane turns into `proxy_pass http://127.0.0.1:<port>`.
      execFileSync(
        "docker",
        [
          "run",
          "-d",
          "--name",
          appName,
          "-p",
          "127.0.0.1::80",
          // The nginx image is already local (the repo's own edge builds on it),
          // so the journey needs neither a registry pull nor an `apk add`.
          "nginx:1.27-alpine",
          "sh",
          "-c",
          `echo ${MARKER} > /usr/share/nginx/html/index.html && exec nginx -g 'daemon off;'`,
        ],
        { stdio: ["ignore", "pipe", "pipe"] },
      );
      appUp = true;
      const upstreamPort = publishedPort(appName, 80);

      // 4. The node: nginx first (the pre-flight needs a running master that owns
      //    port 80), then the real agent — on the host's network, so the loopback
      //    address the route proxies to is the host's.
      execFileSync(
        "docker",
        [
          "run",
          "-d",
          "--name",
          nodeContainer,
          "--network",
          "host",
          "-v",
          "/var/run/docker.sock:/var/run/docker.sock",
          "-v",
          `${AGENT}:/opt/nexusops/nexusops_agent.py:ro`,
          "-e",
          `NEXUSOPS_SERVER=${EDGE}`,
          "-e",
          `NEXUSOPS_TOKEN=${token}`,
          "-e",
          "NEXUSOPS_TOKEN_FILE=/tmp/nexusops-agent-token",
          "-e",
          "NEXUSOPS_INTERVAL=3",
          "-e",
          "NEXUSOPS_NGINX_ROOT=/etc/nexusops/nginx",
          NODE_IMAGE,
          "sh",
          "-c",
          "nginx && exec python3 /opt/nexusops/nexusops_agent.py",
        ],
        { stdio: ["ignore", "pipe", "pipe"] },
      );
      nodeUp = true;

      // 5. The node comes ONLINE with a genuine nginx verdict: the binary is
      //    present, the pre-flight passes, and 80 is really the managed instance.
      await expect
        .poll(
          async () => {
            const res = await api.get(`/api/v1/nodes/${nodeId}`);
            if (!res.ok()) return `http-${res.status()}`;
            const body = (await res.json()) as NodeDetail;
            const nginx = body.capabilities?.nginx ?? {};
            return `${body.status}:${nginx.present === true}:${nginx.routing_eligible === true}`;
          },
          { timeout: 120_000, intervals: [1_000, 2_000] },
        )
        .toBe("ONLINE:true:true");

      const detail = (await (await api.get(`/api/v1/nodes/${nodeId}`)).json()) as NodeDetail;
      expect(detail.capabilities.nginx.routing_eligible).toBe(true);
      expect(detail.capabilities.nginx.reason).toBe("");
      expect(detail.capabilities_reported).toBe(true);

      // 6. Bootstrap ran for real: the customer's own nginx.conf was extended with
      //    the two include lines, and the managed tree exists on the node.
      await expect
        .poll(
          () => {
            try {
              docker(["exec", nodeContainer, "test", "-f", "/etc/nexusops/nginx/nexusops.conf"]);
              return "present";
            } catch {
              return "missing";
            }
          },
          { timeout: 90_000, intervals: [1_000, 2_000] },
        )
        .toBe("present");
      expect(docker(["exec", nodeContainer, "cat", "/etc/nginx/nginx.conf"])).toContain(
        "include /etc/nexusops/nginx/nexusops.conf;",
      );

      // 7. A domain that has never been verified on this fresh stack.
      const domain = await api.post("/api/v1/domains", { data: { name: domainName } });
      expect(domain.status(), await domain.text()).toBe(201);
      const domainBody = (await domain.json()) as DomainBody;
      domainId = domainBody.id;
      expect(domainBody.status).toBe("PENDING");
      expect(domainBody.verified).toBe(false);
      expect(
        domainBody.verification,
        "a fresh domain must hand out its TXT instructions",
      ).toBeTruthy();
      const instructions = domainBody.verification as NonNullable<DomainBody["verification"]>;
      recordName = instructions.record_name;
      expect(recordName).toBe(`_nexusops.${domainName}`);

      // Publish the minted token in the authoritative mock, then verify: the
      // control plane resolves the zone's NS, asks *those* nameservers, and
      // matches the value. No A record is published for the name — reachability
      // is a warning, not a gate, and this proves it.
      await dnsPublish({
        name: recordName,
        type: instructions.record_type,
        value: instructions.record_value,
      });
      const verify = await api.post(`/api/v1/domains/${domainId}/verify`);
      expect(verify.status(), await verify.text()).toBe(200);

      await expect
        .poll(
          async () => {
            const res = await api.get(`/api/v1/domains/${domainId}`);
            if (!res.ok()) return `http-${res.status()}`;
            const body = (await res.json()) as DomainBody;
            return `${body.status}:${body.verified}`;
          },
          { timeout: 120_000, intervals: [2_000, 3_000] },
        )
        .toBe("VERIFIED:true");

      // The verified name's token is no longer retrievable — the one-time rule.
      const after = (await (await api.get(`/api/v1/domains/${domainId}`)).json()) as DomainBody;
      expect(after.verification).toBeNull();

      // 8. The node mirrors real containers, so the upstream picker offers ours.
      let target: RouteTargetBody | undefined;
      await expect
        .poll(
          async () => {
            const res = await api.get(`/api/v1/nodes/${nodeId}/route-targets`);
            if (!res.ok()) return `http-${res.status()}`;
            const targets = (await res.json()) as RouteTargetBody[];
            target = targets.find((item) =>
              item.upstream_ports.some((port) => port.host_port === upstreamPort),
            );
            return target ? "found" : `not-found(${targets.length})`;
          },
          { timeout: 90_000, intervals: [2_000, 3_000] },
        )
        .toBe("found");

      const chosen = target as RouteTargetBody;
      const upstream = chosen.upstream_ports.find((port) => port.host_port === upstreamPort);
      expect(upstream?.upstream_host).toBe("127.0.0.1");

      // 9. The route: created disabled, then gated live. Enabling is what queues
      //    the render + apply, so a saved route can never be serving by accident.
      const route = await api.post("/api/v1/routes", {
        data: {
          domain_id: domainId,
          hostname,
          path: "/",
          node_id: nodeId,
          container_id: chosen.id,
          port: upstreamPort,
        },
      });
      expect(route.status(), await route.text()).toBe(201);
      const routeBody = (await route.json()) as RouteBody;
      routeId = routeBody.id;
      expect(routeBody.enabled).toBe(false);
      expect(routeBody.scheme).toBe("http");

      const enabled = await api.post(`/api/v1/routes/${routeId}/enable`);
      expect(enabled.status(), await enabled.text()).toBe(200);

      await expect
        .poll(
          async () => {
            const res = await api.get(`/api/v1/routes/${routeId}`);
            if (!res.ok()) return `http-${res.status()}`;
            const body = (await res.json()) as RouteBody;
            return `${body.enabled}:${body.config_state}`;
          },
          { timeout: 120_000, intervals: [2_000, 3_000] },
        )
        .toBe("true:IN_SYNC");

      const applied = (await (await api.get(`/api/v1/routes/${routeId}`)).json()) as RouteBody;
      expect(applied.last_apply_error).toBe("");
      expect(applied.last_bundle_id).toBeTruthy();

      // 10. The apply was real: the fragment is on the node, it names this
      //     hostname, and it proxies to the *published* port — never to a
      //     container-internal one.
      const fragmentDir = docker(["exec", nodeContainer, "ls", "/etc/nexusops/nginx/routes.d"]);
      const fragment = fragmentDir
        .split("\n")
        .map((line) => line.trim())
        .find((line) => /^r-[0-9a-f]{32}\.conf$/.test(line));
      expect(fragment, `no route fragment on the node: ${fragmentDir || "(empty)"}`).toBeTruthy();
      const rendered = docker([
        "exec",
        nodeContainer,
        "cat",
        `/etc/nexusops/nginx/routes.d/${fragment}`,
      ]);
      expect(rendered).toContain(`server_name ${hostname};`);
      expect(rendered).toContain(`proxy_pass http://127.0.0.1:${upstreamPort};`);
      // Phase 4 boundary: no TLS material can reach a node's configuration.
      expect(rendered).not.toContain("ssl_certificate");
      expect(rendered).not.toContain("https://");

      // 11. The point of the whole feature: the URL serves the container. The node
      //     owns host port 80, so this is the path a customer request takes.
      await expect
        .poll(() => httpGet("http://127.0.0.1/", hostname).body, {
          timeout: 30_000,
          intervals: [1_000, 2_000],
        })
        .toContain(MARKER);

      // ...and the managed catch-all still refuses to proxy anything else: an
      // unmapped Host gets no response at all (444), never another tenant's app.
      const unmapped = httpGet("http://127.0.0.1/", `not-managed-${stamp}.${DNS_ZONE}`);
      expect(unmapped.ok).toBe(false);
      expect(unmapped.body).not.toContain(MARKER);

      // 12. The node and the control plane agree about what is live: no drift, one
      //     enabled route in sync, and the same bundle the agent fingerprinted.
      const status = (await (
        await api.get(`/api/v1/nodes/${nodeId}/proxy/status`)
      ).json()) as ProxyStatusBody;
      expect(status.provider).toBe("nginx");
      expect(status.eligible).toBe(true);
      expect(status.capability.listener_80).toBe("MANAGED");
      expect(status.drift).toBe(false);
      expect(status.live_bundle_id).toBe(applied.last_bundle_id);
      expect(status.expected_bundle_id).toBe(applied.last_bundle_id);
      expect(status.route_total).toBe(1);
      expect(status.route_enabled).toBe(1);
      expect(status.route_in_sync).toBe(1);

      // 13. The dashboard shows the same truth the API just reported.
      await page.goto(`/domains/${domainId}`);
      await expect(page.getByRole("heading", { name: domainName, level: 1 })).toBeVisible();
      await expect(page.getByText("VERIFIED", { exact: true })).toBeVisible();
      // The route the journey enabled is listed on the domain it serves.
      await expect(page.getByRole("cell", { name: hostname, exact: false })).toBeVisible();

      // ``IN_SYNC`` is the only state that means the node's live configuration
      // matches the desired bundle (the badge renders it space-separated).
      await page.goto("/routes");
      const row = page.getByRole("row", { name: new RegExp(hostname) });
      await expect(row).toBeVisible();
      await expect(row.getByText("IN SYNC")).toBeVisible();
    } finally {
      if (routeId) {
        await api.delete(`/api/v1/routes/${routeId}`).catch(() => undefined);
      }
      if (domainId) {
        await api.delete(`/api/v1/domains/${domainId}`).catch(() => undefined);
      }
      if (recordName) {
        await dnsClear(recordName).catch(() => undefined);
      }
      if (nodeUp) {
        try {
          docker(["rm", "-f", nodeContainer]);
        } catch {
          /* the node may already be gone */
        }
      }
      if (appUp) {
        try {
          docker(["rm", "-f", appName]);
        } catch {
          /* the container may already be gone */
        }
      }
      if (nodeId) {
        await api.delete(`/api/v1/nodes/${nodeId}`).catch(() => undefined);
      }
    }
  });

  /**
   * Ownership transfer — the same name, a second organization, a second node.
   *
   * The name is proven by organization A and served from A's node; A's node is then
   * made genuinely unreachable while organization B proves control of the same name
   * through the same authoritative mock.
   *
   * **Only the management agent is taken away, never nginx.** Stopping the whole
   * container would have made "the route is still being served" impossible to
   * observe — and that is exactly the fact this journey exists to pin: a revoked
   * name whose node cannot be reached keeps answering, so the platform must keep
   * saying "removal requested, not confirmed" until an agent reports otherwise.
   *
   * What it has to show — on the wire, not in status rows — is:
   *
   *   A's route serves A's upstream (real HTTP);
   *   the agent stops reporting and the node goes OFFLINE while nginx keeps serving;
   *   A's domain goes UNVERIFIED and A is told why, without learning who took it;
   *   the route is excluded from the desired configuration, marked **removal
   *   pending**, and still answers with A's marker — the platform claims nothing;
   *   no apply is queued and nothing is announced as repaired while the agent is away;
   *   the agent returns, exactly one apply is processed, the fragment is gone from
   *   disk and the old Host gets the managed 444 instead of the old upstream;
   *   the removal is then — and only then — reported as confirmed;
   *   the new owner serves the name from its own node;
   *   and neither organization can read or modify the other's resources.
   */
  test("a name that changes hands stops being served by the old node", async ({
    api,
    apiToken,
  }) => {
    // Two real nodes in sequence, an offline window and a recovery: minutes, not
    // seconds. Nothing here is loosened to fit — the offline wait is bounded by the
    // node's own 30 s offline threshold.
    test.setTimeout(600_000);

    const stamp = Date.now();
    const domainName = DNS_ZONE; // the mock is authoritative for the zone apex
    const nodeAName = `e2e-xfer-a-${stamp}`;
    const nodeBName = `e2e-xfer-b-${stamp}`;
    const nodeAContainer = `nexusops-e2e-xfer-a-${stamp}`;
    const nodeBContainer = `nexusops-e2e-xfer-b-${stamp}`;
    const appA = `nexusops-e2e-xfer-app-a-${stamp}`;
    const appB = `nexusops-e2e-xfer-app-b-${stamp}`;
    const markerA = `NEXUSOPS_E2E_TRANSFER_A_${stamp}`;
    const markerB = `NEXUSOPS_E2E_TRANSFER_B_${stamp}`;

    const zone = await dnsZone();
    test.skip(zone === null, `mock DNS control API is not reachable at ${DNS_CONTROL}`);
    test.skip(zone !== null && zone !== DNS_ZONE, `mock DNS serves ${zone}, expected ${DNS_ZONE}`);

    // Organization A is the bootstrap organization the API context already acts in.
    // A is the bootstrap tenant, but the header is sent from the first request on:
    // once the account below belongs to a second organization the platform refuses
    // to guess which one a request is for, and an unqualified call starts failing
    // with ORGANIZATION_HEADER_REQUIRED in the middle of the journey.
    const orgA: Tenant = { id: apiToken.orgId, headers: { "X-Org-Id": apiToken.orgId } };
    let orgB: Tenant | null = null;
    let nodeA: NodeHarness | null = null;
    let nodeB: NodeHarness | null = null;
    let routeA: string | null = null;
    let routeB: string | null = null;
    let domainA: string | null = null;
    let domainB: string | null = null;
    let recordName = `_nexusops.${domainName}`;

    try {
      // 1. Organization A: a real node, a verified name, and a live HTTP route.
      nodeA = await startNode(api, {
        tenant: orgA,
        name: nodeAName,
        container: nodeAContainer,
        app: appA,
        marker: markerA,
        // A 30 s offline threshold, so stopping the agent flips the node OFFLINE
        // within the journey's patience instead of the 90 s platform default.
        offlineAfterSeconds: 30,
      });
      const provenA = await proveName(api, orgA, domainName);
      domainA = provenA.domainId;
      recordName = provenA.recordName;

      const routeARes = await api.post("/api/v1/routes", {
        headers: orgA.headers,
        data: {
          domain_id: domainA,
          hostname: domainName,
          path: "/",
          node_id: nodeA.id,
          container_id: nodeA.targetId,
          port: nodeA.upstreamPort,
          enabled: true,
        },
      });
      expect(routeARes.status(), await routeARes.text()).toBe(201);
      routeA = ((await routeARes.json()) as RouteBody).id;
      await expect
        .poll(
          async () => {
            const res = await api.get(`/api/v1/routes/${routeA}`, { headers: orgA.headers });
            if (!res.ok()) return `http-${res.status()}`;
            return ((await res.json()) as RouteBody).config_state;
          },
          { timeout: 120_000, intervals: [2_000, 3_000] },
        )
        .toBe("IN_SYNC");
      // The name really is served by A's node before anything changes hands.
      await expect
        .poll(() => httpGet("http://127.0.0.1/", domainName).body, {
          timeout: 30_000,
          intervals: [1_000, 2_000],
        })
        .toContain(markerA);

      // 2. Organization B — a second tenant the same operator may act in.
      const created = await api.post("/api/v1/organizations", {
        data: { name: `Transfer target ${stamp}`, description: "ownership transfer e2e" },
      });
      expect(created.status(), await created.text()).toBe(201);
      const membership = (await created.json()) as MembershipBody;
      orgB = { id: membership.organization.id, headers: { "X-Org-Id": membership.organization.id } };
      expect(orgB.id).not.toBe(orgA.id);

      // 3. Only the *management agent* goes away before the name changes hands —
      //    nginx keeps running, which is the whole point: a node whose control
      //    plane has lost contact is still perfectly capable of answering for a
      //    name it no longer owns. Nothing refreshes the heartbeat, so the control
      //    plane marks it OFFLINE (30 s threshold, checked every 15 s).
      stopAgent(nodeAContainer);
      await expect
        .poll(
          async () => {
            const res = await api.get(`/api/v1/nodes/${nodeA?.id}`, { headers: orgA.headers });
            if (!res.ok()) return `http-${res.status()}`;
            return ((await res.json()) as NodeDetail).status;
          },
          { timeout: 150_000, intervals: [3_000, 5_000] },
        )
        .toBe("OFFLINE");
      // ...and the data plane is demonstrably still up: with the agent gone, the
      // route this journey is about to revoke still answers on its own host.
      expect(
        httpGet("http://127.0.0.1/", domainName).body,
        "nginx must keep serving while only the agent is stopped",
      ).toContain(markerA);

      // 4. B proves control of the same name through the authoritative fixture.
      const provenB = await proveName(api, orgB, domainName);
      domainB = provenB.domainId;

      // 5. A lost the name — and is told, with a reason and nothing about B.
      await expect
        .poll(
          async () => {
            const res = await api.get(`/api/v1/domains/${domainA}`, { headers: orgA.headers });
            if (!res.ok()) return `http-${res.status()}`;
            return ((await res.json()) as DomainBody).status;
          },
          { timeout: 60_000, intervals: [2_000, 3_000] },
        )
        .toBe("UNVERIFIED");
      const eventsResponse = await api.get("/api/v1/events", {
        headers: orgA.headers,
        params: { types: "DOMAIN_UNVERIFIED" },
      });
      // Read the status before the shape: a refused or empty feed would otherwise
      // surface as "undefined is not an object" and hide which one it was.
      expect(eventsResponse.status(), await eventsResponse.text()).toBe(200);
      const events = (await eventsResponse.json()) as { items: EventBody[] };
      const loss = events.items.find(
        (event) => (event.data as { reason?: string }).reason === "claimed_by_another_organization",
      );
      expect(loss, "the previous owner must be told why it lost the name").toBeTruthy();
      expect(JSON.stringify(events.items)).not.toContain(domainB);

      // 6. The route is unresolved, and **not** reported as served: the node is
      //    offline, so no apply was even queued for it — the old configuration is
      //    still on the node and the control plane says so.
      const stateWhileOffline = (await (
        await api.get(`/api/v1/routes/${routeA}`, { headers: orgA.headers })
      ).json()) as RouteBody;
      expect(stateWhileOffline.enabled).toBe(true);
      expect(stateWhileOffline.config_state).toBe("STALE");
      expect(stateWhileOffline.last_apply_error.length).toBeGreaterThan(0);
      const statusWhileOffline = (await (
        await api.get(`/api/v1/nodes/${nodeA.id}/proxy/status`, { headers: orgA.headers })
      ).json()) as ProxyStatusBody;
      expect(statusWhileOffline.eligible).toBe(false);
      expect(statusWhileOffline.drift).toBe(true);
      expect(statusWhileOffline.expected_bundle_id).not.toBe(statusWhileOffline.live_bundle_id);
      expect(statusWhileOffline.route_in_sync).toBe(0);
      expect(statusWhileOffline.route_stale).toBe(1);
      // The removal is *requested* and visibly pending — not confirmed, and not
      // "recovered". The label is what stops an operator reading a revoked name as
      // already gone while the node is still answering for it.
      expect(stateWhileOffline.removal_state).toBe("REQUESTED");
      expect(stateWhileOffline.removal_confirmed_at).toBeNull();
      expect(stateWhileOffline.status_detail).toContain("Removal requested");
      expect(stateWhileOffline.status_detail).toContain("may still be serving");
      expect(statusWhileOffline.route_removal_pending).toBe(1);
      expect(await liveApplies(api, orgA, nodeA.id)).toHaveLength(0);
      // Not one apply has *finished* for this node since the name changed hands:
      // the only successful apply so far is the one that originally enabled the
      // route, and it carried a manifest.
      expect(await finishedRemovalApplies(api, orgA, nodeA.id)).toHaveLength(0);
      // The truth behind the label: the revoked name still reaches A's upstream,
      // because deleting a route from the desired state does not delete it from a
      // node that cannot be reached.
      expect(
        httpGet("http://127.0.0.1/", domainName).body,
        "the old route must still be answering while its removal is unconfirmed",
      ).toContain(markerA);

      // 7. The reconciler does not lie or pile up: several sweep ticks (15 s each on
      //    this stack) queue nothing, and the difference is never announced as
      //    repaired. Wait past two ticks before asking.
      await new Promise((resolve) => setTimeout(resolve, 35_000));
      expect(await liveApplies(api, orgA, nodeA.id)).toHaveLength(0);
      const recoveredResponse = await api.get("/api/v1/events", {
        headers: orgA.headers,
        params: { types: "NGINX_DRIFT_RECOVERED" },
      });
      expect(recoveredResponse.status(), await recoveredResponse.text()).toBe(200);
      const recoveredWhileOffline = (await recoveredResponse.json()) as { items: EventBody[] };
      expect(recoveredWhileOffline.items).toHaveLength(0);
      expect(
        (await (
          await api.get(`/api/v1/routes/${routeA}`, { headers: orgA.headers })
        ).json()) as RouteBody,
      ).toMatchObject({ config_state: "STALE" });

      // 8. The agent comes back. The next sweep tick queues exactly one apply, the
      //    agent applies it, and only then is the name gone — verified against the
      //    fragment on disk and against a real HTTP request.
      startAgent(nodeAContainer);
      await expect
        .poll(
          async () => {
            const res = await api.get(`/api/v1/nodes/${nodeA?.id}`, { headers: orgA.headers });
            if (!res.ok()) return `http-${res.status()}`;
            return ((await res.json()) as NodeDetail).status;
          },
          { timeout: 120_000, intervals: [2_000, 3_000] },
        )
        .toBe("ONLINE");
      await expect
        .poll(
          async () => {
            const res = await api.get(`/api/v1/nodes/${nodeA?.id}/proxy/status`, {
              headers: orgA.headers,
            });
            if (!res.ok()) return `http-${res.status()}`;
            const body = (await res.json()) as ProxyStatusBody;
            return body.expected_bundle_id === body.live_bundle_id ? "converged" : "drifted";
          },
          { timeout: 180_000, intervals: [2_000, 3_000] },
        )
        .toBe("converged");
      const recoveredResponseAfter = await api.get("/api/v1/events", {
        headers: orgA.headers,
        params: { types: "NGINX_DRIFT_RECOVERED" },
      });
      expect(recoveredResponseAfter.status(), await recoveredResponseAfter.text()).toBe(200);
      const recoveredEvents = (await recoveredResponseAfter.json()) as { items: EventBody[] };
      expect(recoveredEvents.items.length).toBeGreaterThan(0);

      // Exactly one removal was processed by the returning agent — not one per
      // sweep tick, and not zero: the reconciler queues a single apply and the
      // node's own report is what turns the request into a confirmation.
      const removalApplies = await finishedRemovalApplies(api, orgA, nodeA.id);
      expect(removalApplies).toHaveLength(1);
      const confirmed = (await (
        await api.get(`/api/v1/routes/${routeA}`, { headers: orgA.headers })
      ).json()) as RouteBody;
      expect(confirmed.removal_state).toBe("CONFIRMED");
      expect(confirmed.removal_confirmed_at).not.toBeNull();
      expect(confirmed.status_detail).toContain("Removal confirmed");
      const confirmedEvents = (await (
        await api.get("/api/v1/events", {
          headers: orgA.headers,
          params: { types: "ROUTE_REMOVAL_CONFIRMED" },
        })
      ).json()) as { items: EventBody[] };
      expect(confirmedEvents.items).toHaveLength(1);
      expect(
        (await (
          await api.get(`/api/v1/nodes/${nodeA.id}/proxy/status`, { headers: orgA.headers })
        ).json()) as ProxyStatusBody,
      ).toMatchObject({ route_removal_pending: 0 });

      // Nothing that answered for the name is left on the node...
      const routesDir = docker(["exec", nodeAContainer, "ls", "/etc/nexusops/nginx/routes.d"]);
      expect(
        routesDir.split("\n").filter((line) => /^r-[0-9a-f]{32}\.conf$/.test(line.trim())),
      ).toHaveLength(0);
      // ...and the request that used to reach A's app now gets the managed 444.
      const oldHost = httpGet("http://127.0.0.1/", domainName);
      expect(oldHost.body).not.toContain(markerA);
      expect(oldHost.status === 0 || oldHost.status === 444).toBe(true);

      // 9. The new owner serves the name from its own node — a different upstream,
      //    so the marker proves whose nginx answered. Port 80 is free again because
      //    A's node is removed first.
      docker(["rm", "-f", nodeAContainer]);
      nodeB = await startNode(api, {
        tenant: orgB,
        name: nodeBName,
        container: nodeBContainer,
        app: appB,
        marker: markerB,
      });
      const routeBRes = await api.post("/api/v1/routes", {
        headers: orgB.headers,
        data: {
          domain_id: domainB,
          hostname: domainName,
          path: "/",
          node_id: nodeB.id,
          container_id: nodeB.targetId,
          port: nodeB.upstreamPort,
          enabled: true,
        },
      });
      expect(routeBRes.status(), await routeBRes.text()).toBe(201);
      routeB = ((await routeBRes.json()) as RouteBody).id;
      await expect
        .poll(
          async () => {
            const res = await api.get(`/api/v1/routes/${routeB}`, {
              headers: orgB.headers,
            });
            if (!res.ok()) return `http-${res.status()}`;
            return ((await res.json()) as RouteBody).config_state;
          },
          { timeout: 120_000, intervals: [2_000, 3_000] },
        )
        .toBe("IN_SYNC");
      await expect
        .poll(() => httpGet("http://127.0.0.1/", domainName).body, {
          timeout: 30_000,
          intervals: [1_000, 2_000],
        })
        .toContain(markerB);

      // 10. Neither organization can reach the other's resources.
      expect(
        (await api.get(`/api/v1/routes/${routeA}`, { headers: orgB.headers })).status(),
      ).toBe(404);
      expect(
        (await api.post(`/api/v1/routes/${routeA}/disable`, { headers: orgB.headers })).status(),
      ).toBe(404);
      expect((await api.get(`/api/v1/nodes/${nodeA.id}`, { headers: orgB.headers })).status()).toBe(
        404,
      );
      expect(
        (await api.get(`/api/v1/domains/${domainA}`, { headers: orgB.headers })).status(),
      ).toBe(404);
      expect((await api.get(`/api/v1/routes/${routeB}`, { headers: orgA.headers })).status()).toBe(
        404,
      );
      expect((await api.get(`/api/v1/nodes/${nodeB.id}`, { headers: orgA.headers })).status()).toBe(
        404,
      );
      const orgARoutes = (
        (await (await api.get("/api/v1/routes", { headers: orgA.headers })).json()) as {
          items: { id: string }[];
        }
      ).items.map((row) => row.id);
      const orgBRoutes = (
        (await (await api.get("/api/v1/routes", { headers: orgB.headers })).json()) as {
          items: { id: string }[];
        }
      ).items.map((row) => row.id);
      expect(orgARoutes).toContain(routeA);
      expect(orgARoutes).not.toContain(routeB);
      expect(orgBRoutes).toContain(routeB);
      expect(orgBRoutes).not.toContain(routeA);
    } finally {
      const teardown: Array<[Tenant | null, string]> = [
        [orgB, routeB],
        [orgA, routeA],
      ];
      for (const [tenant, route] of teardown) {
        if (tenant && route) {
          await api.delete(`/api/v1/routes/${route}`, { headers: tenant.headers }).catch(() => undefined);
        }
      }
      const domains: Array<[Tenant | null, string | null]> = [
        [orgB, domainB],
        [orgA, domainA],
      ];
      for (const [tenant, domain] of domains) {
        if (tenant && domain) {
          await api
            .delete(`/api/v1/domains/${domain}`, { headers: tenant.headers })
            .catch(() => undefined);
        }
      }
      await dnsClear(recordName).catch(() => undefined);
      for (const container of [nodeAContainer, nodeBContainer]) {
        try {
          // The node container is the unit of teardown: whatever the agent was
          // doing (stopped, restarting) goes with it.
          docker(["rm", "-f", container]);
        } catch {
          /* already gone */
        }
      }
      for (const app of [appA, appB]) {
        try {
          docker(["rm", "-f", app]);
        } catch {
          /* already gone */
        }
      }
      for (const [tenant, node] of [
        [orgB, nodeB],
        [orgA, nodeA],
      ] as Array<[Tenant | null, NodeHarness | null]>) {
        if (tenant && node) {
          await api.delete(`/api/v1/nodes/${node.id}`, { headers: tenant.headers }).catch(() => undefined);
        }
      }
    }
  });
});


