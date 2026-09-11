"""Health probes: liveness (always cheap) and readiness (checks dependencies).

Mounted at the root so orchestrators can probe ``/health``, ``/ready`` and
``/liveness`` without the API prefix.
"""

from __future__ import annotations

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.core.db import get_sessionmaker
from app.core.logging import get_logger
from app.core.redis_client import get_redis
from app.schemas.health import HealthOut, ReadyComponents, ReadyOut

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

    ready = components.database == "ok" and components.redis == "ok"
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadyOut(status="ready" if ready else "unavailable", components=components)
