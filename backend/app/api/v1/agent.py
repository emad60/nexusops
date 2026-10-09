"""Agent ingest endpoints: enrollment, hello, heartbeat, and operation traffic.

Authentication uses the per-node token (``X-Agent-Token``), stored only as a
SHA-256 hash in ``agent_credentials``. Payloads are data-only by design — the
platform never executes anything an agent sends.

Three tenancy properties hold here, and each is enforced before anything is
written:

* The token resolves **before** any organization is known (the control plane has
  to identify the node first), so the lookup runs against the RLS-exempt routing
  table and everything afterwards runs inside that node's organization scope.
* Enrollment (``/agent/enroll``) derives the organization from the *enrollment
  token row*, never from the payload; there is no org field to lie about.
* A rotation's *previous* hash is accepted for a bounded grace window, so a
  running agent survives a rotate without a reinstall. Revocation is immediate
  and has no grace.

Delivery is pull-based and rides the heartbeat: a protocol-2 agent receives its
pending operation ids and any pending credential rotation in the heartbeat
response. A protocol-1 agent keeps the original 204 contract unchanged.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.errors import Unauthorized
from app.core.logging import get_logger
from app.core.rate_limit import node_rate_limit, rate_limit
from app.core.security import AGENT_TOKEN_PREFIX, hash_token
from app.core.tenancy import apply_scope_to_session, org_scope
from app.models import AgentCredential, Server
from app.schemas.agent import (
    AGENT_PROTOCOL_VERSION,
    AgentEnrollIn,
    AgentEnrollOut,
    AgentHeartbeatIn,
    AgentHeartbeatOut,
    AgentHelloIn,
    AgentHelloOut,
)
from app.schemas.operation import (
    AgentOperationClaimOut,
    AgentOperationResultIn,
    AgentOperationResultOut,
)
from app.services import audit_service, enrollment_service, operation_service, server_service

agent_router = APIRouter(prefix="/agent", tags=["agent"])

log = get_logger("nexusops.agent")

DbDep = Annotated[AsyncSession, Depends(get_session)]

#: Enrollment has no node identity yet, so it is throttled per IP and fails
#: closed on a Redis outage (it mints node credentials; it must not be free).
_enroll_limiter = rate_limit("agent_enroll", limit=30, window_seconds=60, fail_closed=True)
_hello_limiter = rate_limit("agent_hello", limit=30, window_seconds=60)
#: IP ceiling covering *unauthenticated* attempts (a rejected-token flood never
#: reaches the per-node limiter because authentication fails first).
_heartbeat_ip_limiter = rate_limit("agent_heartbeat_ip", limit=1200, window_seconds=60)
#: Per-node ceilings: NAT'd fleets no longer share one bucket. Claim/result ride
#: the same poll cadence as the heartbeat, so they get the same generous limit;
#: the CAS in the service is what makes concurrency safe, not this limiter.
_heartbeat_limiter = node_rate_limit("agent_heartbeat", limit=600, window_seconds=60)
_claim_limiter = node_rate_limit("agent_ops_claim", limit=600, window_seconds=60)
_result_limiter = node_rate_limit("agent_ops_result", limit=600, window_seconds=60)


def _presented_token(request: Request) -> str:
    raw = request.headers.get("x-agent-token", "").strip()
    if not raw:
        raise Unauthorized("Missing X-Agent-Token header", code="AGENT_TOKEN_MISSING")
    if not raw.startswith(AGENT_TOKEN_PREFIX):
        # An enrollment token presented where a node token is expected is a
        # distinct, actionable error rather than a generic malformed one.
        raise Unauthorized("Malformed agent token", code="AGENT_TOKEN_MALFORMED")
    return raw


async def require_server(request: Request, db: DbDep) -> AsyncIterator[Server]:
    """Resolve ``X-Agent-Token`` to the node it identifies, inside its own org.

    The credential row names exactly one ``(node, organization)`` pair. The node
    is then loaded **under that organization's scope**, so both nets agree: the
    policy filters the row to that tenant and the explicit comparison below
    refuses a credential whose organization and node disagree.

    Rotation grace: a hash matching ``previous_token_hash`` authenticates the
    request for as long as the grace window is open. ``request.state`` records
    which hash was used so the heartbeat can deliver the replacement only to the
    old-token caller. Revocation is checked before the grace path, so a revoked
    node is rejected even if a stale ``previous_token_hash`` remains.
    """
    raw = _presented_token(request)
    presented_hash = hash_token(raw)
    now = datetime.now(UTC)
    credential = (
        await db.execute(
            select(AgentCredential).where(
                or_(
                    AgentCredential.token_hash == presented_hash,
                    AgentCredential.previous_token_hash == presented_hash,
                )
            )
        )
    ).scalar_one_or_none()
    if credential is None:
        raise Unauthorized("Unknown agent token", code="AGENT_TOKEN_UNKNOWN")
    if credential.revoked_at is not None:
        # Explicit, distinguishable from an unknown token so the agent's log is
        # actionable and an operator knows a re-enroll is required.
        raise Unauthorized("Agent credential was revoked", code="AGENT_TOKEN_REVOKED")

    authenticated_with_previous = credential.token_hash != presented_hash
    if authenticated_with_previous and (
        credential.previous_expires_at is None or credential.previous_expires_at <= now
    ):
        raise Unauthorized("Agent token rotation grace has expired", code="AGENT_TOKEN_UNKNOWN")

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
            raise Unauthorized("Unknown agent token", code="AGENT_TOKEN_UNKNOWN")
        request.state.agent_server_id = str(node.id)
        request.state.agent_org_id = str(credential.org_id)
        request.state.agent_token_is_previous = authenticated_with_previous
        try:
            yield node
        finally:
            # The session commits after this generator closes, so anything the
            # handler left pending is flushed here — inside the node's
            # organization, not in an unscoped commit that RLS would reject.
            await db.flush()


@agent_router.post("/enroll", response_model=AgentEnrollOut, status_code=status.HTTP_201_CREATED)
async def agent_enroll(
    data: AgentEnrollIn,
    request: Request,
    db: DbDep,
    _rl: None = Depends(_enroll_limiter),
) -> AgentEnrollOut:
    """Redeem an enrollment token for a unique node credential.

    Transactional and single-use: the token is consumed by a compare-and-set
    *before* the node is created, so two concurrent redemptions cannot both
    succeed. The organization is the token row's, never the payload's.
    """
    node, raw_agent_token = await enrollment_service.enroll(db, payload=data)
    await audit_service.record(
        db,
        None,
        action="node.enrolled",
        resource_type="node",
        resource_id=node.id,
        org_id=node.org_id,
        actor_email=f"agent:{node.hostname}",
        request=request,
        metadata={"name": node.name, "hostname": node.hostname},
    )
    log.info("agent_enrolled", node=str(node.id), name=node.name)
    return AgentEnrollOut(
        node_id=node.id,
        name=node.name,
        agent_token=raw_agent_token,
        heartbeat_interval_seconds=node.heartbeat_interval_seconds,
        offline_after_seconds=node.offline_after_seconds,
        protocol_version=AGENT_PROTOCOL_VERSION,
    )


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
        protocol_version=out.protocol_version,
        os=f"{data.os_name} {data.os_version}".strip(),
    )
    return out


@agent_router.post("/heartbeat")
async def agent_heartbeat(
    data: AgentHeartbeatIn,
    request: Request,
    db: DbDep,
    _server: Server = Depends(require_server),
    _ip_rl: None = Depends(_heartbeat_ip_limiter),
    _rl: None = Depends(_heartbeat_limiter),
) -> Response:
    """Ingest one metrics sample and hand the agent its next work.

    A protocol-1 agent gets ``204 No Content`` exactly as before. A protocol-2
    agent gets ``200`` with the pending operation ids and any rotation due — the
    delivery channel is the heartbeat because hello happens only at process
    start, so a running agent never sees a push.
    """
    await server_service.process_heartbeat(db, server=_server, payload=data)

    if data.rotation_applied:
        await server_service.acknowledge_rotation(db, server=_server)

    protocol = _server.protocol_version or 1
    if protocol < AGENT_PROTOCOL_VERSION:
        # Preserve the v1 wire contract bit-for-bit.
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    pending = await operation_service.pending_ids_for_node(db, _server)
    rotation = await server_service.pending_rotation(
        db,
        server=_server,
        authenticated_with_previous=bool(getattr(request.state, "agent_token_is_previous", False)),
    )
    body = AgentHeartbeatOut(
        heartbeat_interval_seconds=_server.heartbeat_interval_seconds,
        pending_operations=[uuid.UUID(op_id) for op_id in pending],
        token_rotation=rotation,
    )
    return Response(
        content=body.model_dump_json(),
        media_type="application/json",
        status_code=status.HTTP_200_OK,
    )


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

    The claim also returns the operation's execution deadline, so the agent
    enforces the same bound the control plane will expire against.
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
        claimed_at=operation.claimed_at,
        expires_at=operation.expires_at,
        execution_deadline=operation.execution_deadline,
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
