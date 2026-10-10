import { execFileSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

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
  return execFileSync("docker", args, { encoding: "utf8" }).trim();
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
  capability: { routing_eligible: boolean; listener_80: string };
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
});
