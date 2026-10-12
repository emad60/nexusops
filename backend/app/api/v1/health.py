"""Health probes: liveness (always cheap) and readiness (checks dependencies).

Mounted at the root so orchestrators can probe ``/health``, ``/ready`` and
``/liveness`` without the API prefix.

Readiness gates on the database and Redis only. The key-management provider is
reported in ``components.key_management`` and deliberately **never** moves the
status code: the approved posture (phase5-design.md §6.9) is that the API keeps
serving while key-dependent operations fail closed with a named error, so a Vault
outage must not pull a healthy instance out of rotation.
"""

from __future__ import annotations

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.core.db import get_sessionmaker
from app.core.logging import get_logger
from app.core.redis_client import get_redis
from app.schemas.health import HealthOut, ReadyComponents, ReadyOut
from app.services.kek.health import provider_health

health_router = APIRouter(tags=["health"])

log = get_logger("nexusops.health")


@health_router.get("/health", response_model=HealthOut, include_in_schema=False)
@health_router.get("/liveness", response_model=HealthOut)
async def liveness() -> HealthOut:
    """Process-level liveness: no dependency checks, always 200 if served."""
    return HealthOut()


@health_router.get("/ready", response_model=ReadyOut)
async def readiness(response: Response) -> ReadyOut:
    """Readiness: database and Redis must answer; 503 with details otherwise."""
    components = ReadyComponents()

    try:
        maker = get_sessionmaker()
        async with maker() as db:
            await db.execute(text("SELECT 1"))
        components.database = "ok"
    except Exception as exc:
        components.database = f"error: {type(exc).__name__}"
        log.warning("readiness_db_failed", error=str(exc))

    try:
        await get_redis().ping()
        components.redis = "ok"
    except Exception as exc:
        components.redis = f"error: {type(exc).__name__}"
        log.warning("readiness_redis_failed", error=str(exc))

    # Key management is reported, not enforced: a provider that is down or
    # misconfigured leaves this instance serving everything that does not need a
    # DEK, so failing the whole probe would take a working API out of rotation for
    # a subsystem the platform is explicitly designed to keep serving without.
    try:
        health = await provider_health()
        components.key_management = str(health.status)
    except Exception as exc:
        components.key_management = f"error: {type(exc).__name__}"
        log.warning("readiness_kek_failed", error=type(exc).__name__)

    ready = components.database == "ok" and components.redis == "ok"
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadyOut(status="ready" if ready else "unavailable", components=components)
