"""Agent ingest endpoints: enrollment handshake and periodic heartbeats.

Authentication uses the per-server enrollment token (``X-Agent-Token``),
which is stored only as a SHA-256 hash. Payloads are data-only by design —
the platform never executes anything an agent sends.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.errors import Unauthorized
from app.core.logging import get_logger
from app.core.rate_limit import rate_limit
from app.core.security import hash_token
from app.models import Server
from app.schemas.agent import AgentHeartbeatIn, AgentHelloIn, AgentHelloOut
from app.services import server_service

agent_router = APIRouter(prefix="/agent", tags=["agent"])

log = get_logger("nexusops.agent")

DbDep = Annotated[AsyncSession, Depends(get_session)]

_hello_limiter = rate_limit("agent_hello", limit=30, window_seconds=60)
_heartbeat_limiter = rate_limit("agent_heartbeat", limit=600, window_seconds=60)


async def require_server(request: Request, db: DbDep) -> Server:
    """Resolve ``X-Agent-Token`` to an enrolled server or raise 401."""
    raw = request.headers.get("x-agent-token", "").strip()
    if not raw:
        raise Unauthorized("Missing X-Agent-Token header", code="AGENT_TOKEN_MISSING")
    if not raw.startswith("nxa_"):
        raise Unauthorized("Malformed agent token", code="AGENT_TOKEN_MALFORMED")

    server = (
        await db.execute(select(Server).where(Server.agent_token_hash == hash_token(raw)))
    ).scalar_one_or_none()
    if server is None:
        raise Unauthorized("Unknown or rotated agent token", code="AGENT_TOKEN_INVALID")
    request.state.agent_server_id = str(server.id)
    return server


@agent_router.post("/hello", response_model=AgentHelloOut)
async def agent_hello(
    data: AgentHelloIn,
    request: Request,
    db: DbDep,
    _server: Server = Depends(require_server),
    _rl: None = Depends(_hello_limiter),
) -> AgentHelloOut:
    """First contact after enrollment: persist static host facts, negotiate cadence."""
    out = await server_service.register_agent_hello(db, server=_server, payload=data)
    log.info(
        "agent_hello",
        server=_server.name,
        agent_version=data.agent_version,
        os=f"{data.os_name} {data.os_version}".strip(),
    )
    return out


@agent_router.post("/heartbeat", status_code=status.HTTP_204_NO_CONTENT)
async def agent_heartbeat(
    data: AgentHeartbeatIn,
    request: Request,
    db: DbDep,
    _server: Server = Depends(require_server),
    _rl: None = Depends(_heartbeat_limiter),
) -> Response:
    """Ingest one metrics sample + observed containers. Returns 204 when applied."""
    await server_service.process_heartbeat(db, server=_server, payload=data)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
