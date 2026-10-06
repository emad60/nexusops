"""Agent ingest endpoints: enrollment handshake and periodic heartbeats.

Authentication uses the per-node enrollment token (``X-Agent-Token``), stored
only as a SHA-256 hash in ``agent_credentials``. Payloads are data-only by
design — the platform never executes anything an agent sends.

The token resolves **before** any organization is known (the control plane has
to identify the node first), so the lookup runs against the RLS-exempt routing
table and everything afterwards runs inside that node's organization scope.
That is the whole tenancy contract of this module: a node can only ever speak
for the organization that owns it.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.errors import Unauthorized
from app.core.logging import get_logger
from app.core.rate_limit import rate_limit
from app.core.security import hash_token
from app.core.tenancy import apply_scope_to_session, org_scope
from app.models import AgentCredential, Server
from app.schemas.agent import AgentHeartbeatIn, AgentHelloIn, AgentHelloOut
from app.schemas.operation import (
    AgentOperationClaimOut,
    AgentOperationResultIn,
    AgentOperationResultOut,
)
from app.services import audit_service, operation_service, server_service

agent_router = APIRouter(prefix="/agent", tags=["agent"])

log = get_logger("nexusops.agent")

DbDep = Annotated[AsyncSession, Depends(get_session)]

_hello_limiter = rate_limit("agent_hello", limit=30, window_seconds=60)
_heartbeat_limiter = rate_limit("agent_heartbeat", limit=600, window_seconds=60)
#: Claim/result ride the same poll cadence as the heartbeat, so they get the same
#: generous ceiling; the CAS in the service is what makes concurrency safe, not
#: this limiter.
_claim_limiter = rate_limit("agent_ops_claim", limit=600, window_seconds=60)
_result_limiter = rate_limit("agent_ops_result", limit=600, window_seconds=60)


def _presented_token(request: Request) -> str:
    raw = request.headers.get("x-agent-token", "").strip()
    if not raw:
        raise Unauthorized("Missing X-Agent-Token header", code="AGENT_TOKEN_MISSING")
    if not raw.startswith("nxa_"):
        raise Unauthorized("Malformed agent token", code="AGENT_TOKEN_MALFORMED")
    return raw


async def require_server(request: Request, db: DbDep) -> AsyncIterator[Server]:
    """Resolve ``X-Agent-Token`` to the node it identifies, inside its own org.

    The credential row names exactly one ``(node, organization)`` pair. The node
    is then loaded **under that organization's scope**, so both nets agree: the
    policy filters the row to that tenant and the explicit comparison below
    refuses a credential whose organization and node disagree (which would mean
    the routing row was tampered with or left behind by a bad enrollment).

    Yielding (rather than returning) is what keeps the scope open for the
    endpoint body: without it, the write path would run unscoped and the guard
    would refuse it — correctly, since an unscoped write to an organization-owned
    table is exactly the bug this module must not have.
    """
    raw = _presented_token(request)
    credential = (
        await db.execute(
            select(AgentCredential).where(AgentCredential.token_hash == hash_token(raw))
        )
    ).scalar_one_or_none()
    if credential is None or credential.revoked_at is not None:
        raise Unauthorized("Unknown or rotated agent token", code="AGENT_TOKEN_INVALID")

    with org_scope(credential.org_id):
        # The credential lookup ran before the scope existed, so the connection's
        # GUC still says "no tenant"; push it now instead of waiting for the next
        # transaction boundary, or every read below would be denied by RLS.
        await apply_scope_to_session(db)
        node = (
            await db.execute(select(Server).where(Server.id == credential.server_id))
        ).scalar_one_or_none()
        if node is None or node.org_id != credential.org_id:
            # Either the node is gone, or the routing row points somewhere the
            # node does not belong. Both are indistinguishable to the caller.
            raise Unauthorized("Unknown or rotated agent token", code="AGENT_TOKEN_INVALID")
        request.state.agent_server_id = str(node.id)
        request.state.agent_org_id = str(credential.org_id)
        try:
            yield node
        finally:
            # The session commits after this generator closes, so anything the
            # handler left pending is flushed here — inside the node's
            # organization, not in an unscoped commit that RLS would reject.
            await db.flush()


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


@agent_router.post("/operations/{operation_id}/claim", response_model=AgentOperationClaimOut)
async def claim_operation(
    operation_id: uuid.UUID,
    request: Request,
    db: DbDep,
    _server: Server = Depends(require_server),
    _rl: None = Depends(_claim_limiter),
) -> AgentOperationClaimOut:
    """Compare-and-set claim of one operation for **this** node.

    The node identity comes from the token, and the service's CAS additionally
    requires ``node_id == this node`` and ``org_id == this node's org``, so a
    token cannot claim another node's work even within its own tenant. A foreign
    id is a 404, identical to a random one.
    """
    operation = await operation_service.claim_operation(
        db, server=_server, operation_id=operation_id
    )
    await audit_service.record(
        db,
        None,
        action="operation.claim",
        resource_type="operation",
        resource_id=operation.id,
        org_id=_server.org_id,
        actor_email=f"agent:{_server.name}",
        metadata={"node_id": str(_server.id), "type": str(operation.type)},
    )
    return AgentOperationClaimOut(
        id=operation.id,
        type=operation.type,
        params=operation.params,
        expires_at=operation.expires_at,
    )


@agent_router.post("/operations/{operation_id}/result", response_model=AgentOperationResultOut)
async def report_operation_result(
    operation_id: uuid.UUID,
    data: AgentOperationResultIn,
    request: Request,
    db: DbDep,
    _server: Server = Depends(require_server),
    _rl: None = Depends(_result_limiter),
) -> AgentOperationResultOut:
    """Record the agent's outcome for an operation it claimed.

    The report is *asserted*, never verified: the platform's guarantee is
    attribution and bounded blast radius, not proof of execution. A duplicate
    report against an already-terminal row is a no-op rather than an error.
    """
    operation = await operation_service.record_result(
        db,
        server=_server,
        operation_id=operation_id,
        ok=data.ok,
        output=data.output,
        error_code=data.error_code,
        error_message=data.error_message,
    )
    await audit_service.record(
        db,
        None,
        action="operation.result",
        resource_type="operation",
        resource_id=operation.id,
        org_id=_server.org_id,
        actor_email=f"agent:{_server.name}",
        metadata={
            "node_id": str(_server.id),
            "type": str(operation.type),
            "status": str(operation.status),
        },
    )
    return AgentOperationResultOut(
        id=operation.id,
        type=operation.type,
        status=operation.status,
        error_code=operation.error_code,
    )
