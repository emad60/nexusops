# NexusOps Agent

A single-file, **standard-library-only** Python agent (`agent/nexusops_agent.py`)
that reports host metrics and Docker container state to a NexusOps server.
No pip packages are required — any machine with Python 3.9+ can run it.

## What it collects

| Signal | Source |
| --- | --- |
| CPU % | `/proc/stat` delta between heartbeats |
| Memory used/total | `/proc/meminfo` |
| Disk used/% | `statvfs` on `/` |
| Load average | `os.getloadavg()` |
| Uptime | `/proc/uptime` |
| Containers | Docker Engine API over `/var/run/docker.sock` (list + capped inspect) |

If no docker socket exists the agent simply reports host metrics.

## Security model

- The agent authenticates with its own node credential (`X-Agent-Token: nxa_…`);
  the server stores only its SHA-256 hash. The credential is minted by redeeming an
  organization-scoped, single-use `nxk_` enrollment token. **Rotating** a credential
  keeps the old hash valid for a bounded grace window so a running agent survives;
  **revoking** it stops acceptance immediately.
- The agent is pull-only: it **cannot be reached** inbound, and the server never opens
  a connection to a node. It fetches work from the heartbeat response and executes a
  **closed whitelist** of operations (`container.start/stop/restart/remove`,
  `logs.tail`) via fixed Docker API calls over the unix socket. There is no
  `shell=True`, no `/containers/{id}/exec`, and no generic command endpoint, so a
  malformed or malicious control-plane message cannot become local code execution.
- Transport is **HTTPS-only**. A non-loopback plain `http://` URL is refused before
  any credential is sent; certificate verification is never disabled, and a private CA
  is trusted with `NEXUSOPS_CA_BUNDLE`.
- The systemd unit runs with `ProtectSystem=strict`, `NoNewPrivileges`, and a
  read-only `/proc`; it joins the `docker` group for socket access.

## Install

1. In the NexusOps web UI open **Nodes → Add node** and create an **enrollment
   token** (single-use, default 1 h TTL); copy it once — it is never shown again.
2. On the target host:

   ```bash
   sudo NEXUSOPS_ENROLL_TOKEN=nxk_... NEXUSOPS_SERVER=https://nexusops.example.com \
        bash install.sh
   ```

   > The enrollment token is delivered through the environment, never as a
   > command-line argument (argv is visible in `ps` and shell history). The
   > agent exchanges it for its own node credential, stored at
   > `/etc/nexusops-agent/token` (0600, written atomically). An already-enrolled
   > node can skip enrollment: `NEXUSOPS_TOKEN=nxa_... `. A non-loopback
   > `http://` URL is refused outright — terminate TLS at your edge.

3. Verify:

   ```bash
   systemctl status nexusops-agent
   journalctl -u nexusops-agent -f
   ```

The server marks the server ONLINE within one heartbeat and OFFLINE after
~90 s of silence (configurable per server via `offline_after_seconds`).

## Manual run / other supervisors

```bash
NEXUSOPS_SERVER=https://nexusops.example.com NEXUSOPS_TOKEN=nxa_... \
  python3 nexusops_agent.py --interval 30

# one-shot (useful for smoke tests)
python3 nexusops_agent.py --server https://nexusops.example.com --token nxa_... --once
```

Flags: `--interval N` (≥5 s), `--once`, `--token-file PATH`, `--ca-bundle PATH`.
The old `--insecure` / `--allow-insecure-transport` flags are **gone**: transport
is HTTPS-only, and a private CA is trusted with `NEXUSOPS_CA_BUNDLE` (never by
disabling verification). Environment overrides: `NEXUSOPS_SERVER`,
`NEXUSOPS_TOKEN`, `NEXUSOPS_INTERVAL`, `NEXUSOPS_TOKEN_FILE`, `NEXUSOPS_CA_BUNDLE`.
Passing an org-scoped `nxk_` enrollment token (via `NEXUSOPS_TOKEN` or
`--token`) makes the agent exchange it once for its own `nxa_` credential and
persist it to `NEXUSOPS_TOKEN_FILE` (default `/etc/nexusops-agent/token`, 0600,
atomic replace).

Failure handling: transient failures back off exponentially (up to 5 min) and
recover automatically. A **rejected token does not exit** — the unit runs with
`Restart=always`/`RestartSec=10`, so exiting turned every revocation into an
endless storm of rejected requests. Instead the agent parks in a 15-minute
re-attempt cadence (`REVOKED_POLL_SECONDS`), says so once on stderr, and stays
alive until an operator re-enrolls the node with a fresh token. Under `--once`
it still exits non-zero, because that mode is a smoke test. Revocation is a
distinct action from rotation (Phase 3): `POST /nodes/{id}/agent-token/revoke`
stops token acceptance immediately with no grace, while a rotation opens a bounded
dual-token window and delivers the replacement on the next heartbeat.
