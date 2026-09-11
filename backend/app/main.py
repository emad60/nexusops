"""NexusOps API entrypoint.

Wires middleware, error handling, REST routers and the WebSocket hub into a
single FastAPI application. Configuration problems abort startup here, before
any request is served.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Settings, fail_on_bad_config, get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import (
    AccessLogMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
)

fail_on_bad_config()
configure_logging()

logger = get_logger(__name__)

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Start the WS hub + notification dispatcher; tear them down cleanly."""
    settings = get_settings()
    background_tasks: list[asyncio.Task] = []

    try:
        from app.services.notification_service import dispatcher_loop

        background_tasks.append(asyncio.create_task(dispatcher_loop()))
        logger.info("notification_dispatcher_started")
    except Exception:
        logger.exception("notification_dispatcher_failed_to_start")

    if settings.simulation_mode:
        logger.warning("simulation_mode_enabled", hint="synthetic fleet is being driven by beat")

    try:
        from app.ws.hub import hub

        hub.start()
    except Exception:
        logger.exception("ws_hub_failed_to_start")

    logger.info(
        "api_started", environment=settings.environment, simulation=settings.simulation_mode
    )
    try:
        yield
    finally:
        for task in background_tasks:
            task.cancel()
        await asyncio.gather(*background_tasks, return_exceptions=True)
        try:
            from app.ws.hub import hub

            await hub.stop()
        except Exception:
            logger.exception("ws_hub_stop_failed")
        from app.core.db import dispose_engine
        from app.core.redis_client import close_redis

        await dispose_engine()
        await close_redis()
        logger.info("api_stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    # The documented ENVIRONMENT contract: docs exposure follows the same gate
    # as cookie Secure and error detail. Anonymous schema enumeration is recon
    # aid on an internet-facing deployment, so production gets neither the
    # OpenAPI schema nor the Swagger UI.
    docs_enabled = not settings.is_production
    application = FastAPI(
        title="NexusOps",
        version="1.0.0",
        description="Self-hosted infrastructure management & monitoring platform.",
        lifespan=lifespan,
        openapi_url=f"{API_PREFIX}/openapi.json" if docs_enabled else None,
        docs_url="/api/docs" if docs_enabled else None,
        redoc_url=None,
    )

    # Middleware order = registration order reversed on the way in; keep
    # RequestID outermost so every log line carries an id even on early errors.
    application.add_middleware(RequestIDMiddleware)
    application.add_middleware(SecurityHeadersMiddleware, is_production=settings.is_production)
    application.add_middleware(AccessLogMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=[
            "Authorization",
            "Content-Type",
            "X-API-Key",
            "X-Agent-Token",
            "X-Request-ID",
        ],
        expose_headers=["X-Request-ID", "Retry-After"],
        max_age=600,
    )
    register_exception_handlers(application)

    _include_routers(application, settings)

    @application.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        payload = {"name": "NexusOps", "version": "1.0.0", "api": API_PREFIX}
        if docs_enabled:
            payload["docs"] = "/api/docs"
        return payload

    return application


def _include_routers(application: FastAPI, settings: Settings) -> None:
    """Mount every domain router. Router variables follow the module contract."""
    from app.api.v1 import (
        agent,
        alerts,
        apikeys,
        audit,
        auth,
        channels,
        containers,
        deployments,
        docker_hosts,
        events,
        health,
        incidents,
        meta,
        metrics,
        monitors,
        projects,
        roles,
        search,
        secrets,
        servers,
        sessions,
        users,
    )

    # Health probes live at the root for orchestrators hitting the container
    # directly; they are ALSO mounted below under /api/v1 via the loop.

    application.include_router(health.health_router)

    for module in (
        health,  # /api/v1/health /api/v1/ready /api/v1/liveness aliases
        meta,
        auth,
        users,
        roles,
        sessions,
        apikeys,
        servers,
        agent,
        search,
        metrics,
        events,
        audit,
        secrets,
        docker_hosts,
        containers,
        monitors,
        alerts,
        channels,
        incidents,
        projects,
        deployments,
    ):
        for name in (
            "router",
            "health_router",
            "agent_router",
            "search_router",
            "meta_router",
            "testkit_router",
            "hosts_router",
            "events_router",
            "audit_router",
            "secrets_router",
        ):
            candidate = getattr(module, name, None)
            if candidate is not None:
                application.include_router(candidate, prefix=API_PREFIX)

    # WebSocket hub lives beside the REST surface.
    from app.ws.router import router as ws_router

    application.include_router(ws_router, prefix=API_PREFIX)

    # Dev-only fault-injection endpoints for E2E tests; never in production.
    import sys as _sys

    for module_name, module_obj in list(_sys.modules.items()):
        if module_name.startswith("app.api.v1."):
            testkit_router = getattr(module_obj, "testkit_router", None)
            if testkit_router is not None:
                application.include_router(testkit_router)


app = create_app()
