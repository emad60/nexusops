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

- The agent authenticates with an enrollment token (`X-Agent-Token: nxa_…`);
  the server stores only its SHA-256 hash. Regenerating the token in the UI
  invalidates the old one immediately.
- Communication is one-way telemetry over HTTPS (or HTTP in dev). **The server
  cannot execute commands on the host through the agent** — there is no command
  channel by design. Container actions (start/stop/restart) operate through
  configured Docker endpoints, not the agent.
- TLS verification is on by default; `--insecure` exists only for lab testing.
- The systemd unit runs with `ProtectSystem=strict`, `NoNewPrivileges`, and a
  read-only `/proc`; it joins the `docker` group only for socket reads.

## Install

1. In the NexusOps web UI open **Servers → your server → Enroll token**
   and copy the token (shown once).
2. On the target host:

   ```bash
   sudo ./install.sh --server https://nexusops.example.com --token nxa_...
   ```

   > The enrollment token is a long-lived bearer credential — the agent sends
   > it on every hello/heartbeat. Point the agent at an `https://` URL (TLS
   > terminated at your edge) whenever the host is not on the same trusted
   > loopback; the agent warns when it is about to send the token over plain
   > HTTP to a non-loopback address (`--allow-insecure-transport` silences the
   > warning for deliberate dev setups).

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

Flags: `--interval N` (≥5 s), `--insecure`, `--allow-insecure-transport`, `--once`.
Environment overrides: `NEXUSOPS_SERVER`, `NEXUSOPS_TOKEN`, `NEXUSOPS_INTERVAL`.

Failure handling: failed beats back off exponentially (up to 5 min) and recover
automatically; an expired/revoked token exits with status 1 so the supervisor
does not hot-loop against a rejected credential.
