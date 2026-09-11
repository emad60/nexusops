"""Simulation mode: drive the seeded fleet so dashboards stay alive on a laptop.

Every SIMULATION_TICK_SECONDS beat tick synthesises plausible heartbeats for
servers flagged ``simulated``. Values are deterministic sine waves keyed by
server id, so restarts do not produce random spikes. One designated flaky node
skips its heartbeat for ~2 minutes each hour to exercise OFFLINE -> ONLINE
transitions end to end.
"""

from __future__ import annotations

import math
import time
from types import SimpleNamespace
from typing import Any

from sqlalchemy import select

from app.core.logging import get_logger
from app.tasks._util import run_async, task_session
from app.tasks.celery_app import app

logger = get_logger(__name__)

AGENT_VERSION = "sim-agent/1.0.0"
SIM_IMAGES = (
    "nginx:1.27-alpine",
    "redis:7-alpine",
    "ghcr.io/nexusops/demo-api:1.4.2",
    "postgres:17-alpine",
)
SIM_CONTAINER_NAMES = ("edge-proxy", "app-server", "job-runner", "cache")


def _wave(seed: str, period_seconds: float, amplitude: float, base: float) -> float:
    """Deterministic smooth value in [base-amplitude, base+amplitude]."""
    phase = sum(ord(c) * (i + 7) for i, c in enumerate(seed)) % 1000
    t = time.time()
    value = base + amplitude * math.sin((2 * math.pi * t) / period_seconds + phase)
    return round(max(value, 0.0), 2)


def _containers_for(server_id: str, server_name: str, now_bucket: int) -> list[dict]:
    """Stable per-server container set; one container cycles EXITED occasionally."""
    count = 2 + (sum(ord(c) for c in server_id) % 3)
    containers = []
    for i in range(count):
        # Every ~9 minutes one container is down for a single bucket (~20s),
        # producing CONTAINER_STOPPED / CONTAINER_STARTED diff events.
        down = (now_bucket + i) % 27 == 5
        name = f"{SIM_CONTAINER_NAMES[i % len(SIM_CONTAINER_NAMES)]}-{server_name.split('-')[-1]}"
        containers.append(
            {
                "container_id": f"sim{sum(ord(c) for c in server_id + str(i)):012x}"[:64],
                "name": name,
                "status": "EXITED" if down else "RUNNING",
                "health": "NONE" if down else "HEALTHY",
                "image_ref": SIM_IMAGES[i % len(SIM_IMAGES)],
                "restart_count": now_bucket // 500,
                "cpu_percent": 0.0 if down else _wave(server_id + name, 300, 15, 22),
                "mem_used_mb": 0.0 if down else _wave(server_id + name, 600, 80, 320),
            }
        )
    return containers


@app.task(name="nx.simulation_tick", soft_time_limit=90, time_limit=110)
def simulation_tick() -> dict[str, int]:
    from app.core.config import get_settings

    settings = get_settings()
    if not settings.simulation_mode:
        return {"skipped": 1}

    async def _run() -> int:
        from app.models import Server
        from app.services.server_service import process_heartbeat

        try:
            from app.schemas.agent import AgentHeartbeatIn as PayloadModel
        except Exception:  # pragma: no cover - schema always exists post wave-1
            PayloadModel = None  # type: ignore[misc, assignment]

        now = time.time()
        minute = time.gmtime(now).tm_min
        now_bucket = int(now // 20)

        async with task_session() as db:
            servers = (
                (await db.execute(select(Server).where(Server.simulated.is_(True)))).scalars().all()
            )
            beat_count = 0
            for server in servers:
                # The designated flaky node goes silent briefly each hour so
                # offline detection + recovery are demonstrable without tooling.
                silent_window = server.name.endswith("-flaky") and minute in (7, 8)
                if silent_window:
                    continue

                uptime = int(server.uptime_seconds or 3600) + 20
                payload_data = {
                    "cpu_percent": _wave(str(server.id), 420, 28, 34),
                    "mem_used_mb": _wave(str(server.id) + "m", 900, 900, 2400),
                    "mem_percent": _wave(str(server.id) + "mp", 900, 12, 55),
                    "disk_used_gb": _wave(str(server.id) + "d", 86400, 2, 38),
                    "disk_percent": _wave(str(server.id) + "dp", 86400, 3, 52),
                    "net_rx_kb_s": _wave(str(server.id) + "rx", 180, 400, 650),
                    "net_tx_kb_s": _wave(str(server.id) + "tx", 210, 350, 480),
                    "load1": _wave(str(server.id) + "l", 600, 0.8, 1.2),
                    "uptime_seconds": uptime,
                    "containers": _containers_for(str(server.id), server.name, now_bucket),
                }
                # Deliberately duck-typed: SimpleNamespace fallback for the
                # (unreachable) case where the agent schema fails to import.
                payload: Any = (
                    PayloadModel(**payload_data)
                    if PayloadModel is not None
                    else SimpleNamespace(**payload_data)
                )
                await process_heartbeat(
                    db, server=server, payload=payload, agent_version=AGENT_VERSION
                )
                beat_count += 1
            return beat_count

    beats = run_async(_run())
    if beats:
        logger.debug("simulation_tick_done", servers_beaten=beats)
    return {"beats": beats}
