"""Enrollment tokens: mint, list, revoke, and the transactional consume.

This module is one of the few places allowed to open a **system scope** (see the
allowlist in :mod:`app.core.tenancy`), and it is deliberate: an agent presents an
``nxk_`` token with no organization header and no member identity, so resolving
*which* organization the token belongs to is the first thing that must happen.
The lookup is a by-**hash** read of a 256-bit secret, and the organization it
returns is then authoritative — the token's organization determines node
ownership, never anything the agent sends. That is the same carve-out
``api_keys`` and ``agent_credentials`` rely on, expressed here as a scoped read
instead of an RLS-exempt table.

The consume is the security-critical part, and it is a single compare-and-set:

* ``UPDATE enrollment_tokens SET used_at = now() WHERE id = ... AND used_at IS
  NULL AND revoked_at IS NULL AND expires_at > now() RETURNING org_id`` — one
  statement, so two concurrent redemptions cannot both win. A loser sees zero
  rows and is refused before any node is created.
* The node is then created (or claimed) inside the token's organization scope,
  and a fresh unique node credential is issued, all in the same transaction. If
  the transaction rolls back, so does the token consumption.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext
from app.core.errors import BadRequest, Conflict, NotFound, Unauthorized
from app.core.logging import get_logger
from app.core.security import generate_agent_token, hash_token
from app.core.tenancy import apply_scope_to_session, org_scope, require_org, system_scope
from app.models import AgentCredential, EnrollmentToken, Server
from app.models.enums import EnrollmentTokenState
from app.schemas.agent import AGENT_PROTOCOL_VERSION, AgentEnrollIn
from app.schemas.enrollment import EnrollmentTokenCreate

log = get_logger("nexusops.enrollment")


def _utcnow() -> datetime:
    return datetime.now(UTC)


def token_state(token: EnrollmentToken) -> EnrollmentTokenState:
    """Derived lifecycle state — revoked wins over used wins over expired."""
    if token.revoked_at is not None:
        return EnrollmentTokenState.REVOKED
    if token.used_at is not None:
        return EnrollmentTokenState.USED
    if token.expires_at <= _utcnow():
        return EnrollmentTokenState.EXPIRED
    return EnrollmentTokenState.ACTIVE


def install_hint(raw_token: str) -> str:
    """The one-liner an operator pastes, without the raw token in argv.

    The token travels in the environment (read by install.sh) rather than as a
    command-line argument, so it never lands in shell history or the target's
    process list. ``<platform-url>`` is a placeholder because the API does not
    know its own public origin.
    """
    return (
        "sudo NEXUSOPS_ENROLL_TOKEN=<token> NEXUSOPS_SERVER=<platform-url> "
        "bash agent/install.sh   # set NEXUSOPS_SERVER to this control plane's URL"
    )


# --- operator-facing ---------------------------------------------------------


async def create_token(
    db: AsyncSession, ctx: AuthContext, payload: EnrollmentTokenCreate
) -> tuple[str, EnrollmentToken]:
    """Mint one single-use token in the caller's active organization."""
    from app.core.security import generate_enrollment_token

    org_id = require_org()

    if payload.node_id is not None:
        # Loading under the active scope makes a foreign node a 404, exactly like
        # a random id — the token cannot be bound to another tenant's node.
        placeholder = await db.get(Server, payload.node_id)
        if placeholder is None:
            raise NotFound("Node not found", code="NODE_NOT_FOUND")

    raw, _prefix, token_hash = generate_enrollment_token()
    token = EnrollmentToken(
        org_id=org_id,
        name=payload.name,
        note=payload.note,
        token_hash=token_hash,
        single_use=True,
        expires_at=_utcnow() + timedelta(seconds=payload.expires_in_seconds),
        node_id=payload.node_id,
        created_by_id=ctx.user_id,
    )
    db.add(token)
    await db.flush()
    log.info(
        "enrollment_token_created",
        token=str(token.id),
        org=str(org_id),
        expires_at=token.expires_at.isoformat(),
    )
    return raw, token


async def list_tokens(
    db: AsyncSession, *, limit: int, offset: int
) -> tuple[list[EnrollmentToken], int]:
    from sqlalchemy import func

    total = int((await db.execute(select(func.count()).select_from(EnrollmentToken))).scalar() or 0)
    rows = (
        (
            await db.execute(
                select(EnrollmentToken)
                .order_by(EnrollmentToken.created_at.desc(), EnrollmentToken.id.desc())
                .limit(limit)
                .offset(offset)
            )
        )
        .scalars()
        .all()
    )
    return list(rows), total


async def get_token(db: AsyncSession, token_id: uuid.UUID) -> EnrollmentToken:
    token = await db.get(EnrollmentToken, token_id)
    if token is None:
        raise NotFound("Enrollment token not found", code="ENROLLMENT_TOKEN_NOT_FOUND")
    return token


async def revoke_token(
    db: AsyncSession, token_id: uuid.UUID, *, ctx: AuthContext
) -> EnrollmentToken:
    """Immediate kill switch. A used token cannot be revoked (nothing to kill)."""
    now = _utcnow()
    org_id = require_org()
    result = await db.execute(
        update(EnrollmentToken)
        .where(
            EnrollmentToken.id == token_id,
            EnrollmentToken.org_id == org_id,
            EnrollmentToken.revoked_at.is_(None),
            EnrollmentToken.used_at.is_(None),
        )
        .values(revoked_at=now, revoked_by_id=ctx.user_id, updated_at=now)
        .returning(EnrollmentToken.id)
    )
    if result.first() is None:
        token = await db.get(EnrollmentToken, token_id)
        if token is None:
            raise NotFound("Enrollment token not found", code="ENROLLMENT_TOKEN_NOT_FOUND")
        if token.used_at is not None:
            raise Conflict(
                "Enrollment token was already used and cannot be revoked",
                code="ENROLLMENT_TOKEN_ALREADY_USED",
            )
        # Already revoked: idempotent success, so a retried click is not an error.
        return token
    await db.flush()
    return await get_token(db, token_id)


# --- agent-facing ------------------------------------------------------------


async def _claim_and_consume(db: AsyncSession, raw_token: str) -> EnrollmentToken:
    """Atomically consume *raw_token*; return the row it identified.

    Runs in a system scope because the token hash lookup precedes any knowledge
    of the organization. The CAS is what makes single-use real under concurrency.
    """
    now = _utcnow()
    token_hash = hash_token(raw_token)
    with system_scope("agent enrollment: token lookup"):
        await apply_scope_to_session(db)
        row = (
            await db.execute(
                select(EnrollmentToken).where(EnrollmentToken.token_hash == token_hash)
            )
        ).scalar_one_or_none()
        if row is None:
            # A bogus token is answered exactly like a revoked or used one: the
            # response must not tell an attacker which guess was closest.
            raise Unauthorized(
                "Enrollment token is invalid, expired, revoked or already used",
                code="ENROLLMENT_TOKEN_INVALID",
            )
        result = await db.execute(
            update(EnrollmentToken)
            .where(
                EnrollmentToken.id == row.id,
                EnrollmentToken.used_at.is_(None),
                EnrollmentToken.revoked_at.is_(None),
                EnrollmentToken.expires_at > now,
            )
            .values(used_at=now, updated_at=now)
            .returning(EnrollmentToken.id)
        )
        if result.first() is None:
            raise Unauthorized(
                "Enrollment token is invalid, expired, revoked or already used",
                code="ENROLLMENT_TOKEN_INVALID",
            )
        await db.flush()
        await db.refresh(row)
        return row


def _unique_name(base: str, taken: set[str]) -> str:
    """A per-organization display name derived from the hostname."""
    candidate = base[:120] or "node"
    if candidate not in taken:
        return candidate
    for suffix in range(2, 1000):
        tail = f"-{suffix}"
        trimmed = candidate[: 120 - len(tail)] + tail
        if trimmed not in taken:
            return trimmed
    return f"{candidate[:112]}-{uuid.uuid4().hex[:6]}"


async def enroll(db: AsyncSession, *, payload: AgentEnrollIn) -> tuple[Server, str]:
    """Redeem an enrollment token and return ``(node, raw_agent_token)``.

    The organization comes from the token row. The agent's payload is facts
    only — there is no path by which it can name a tenant, and the request is
    refused before any row is written if the token is not valid.
    """
    token = await _claim_and_consume(db, payload.enrollment_token)

    with org_scope(token.org_id):
        await apply_scope_to_session(db)

        now = _utcnow()
        if token.node_id is not None:
            node = await db.get(Server, token.node_id)
            if node is None:
                # The placeholder was deleted between minting and enrollment.
                raise BadRequest(
                    "The node this token was issued for no longer exists",
                    code="ENROLLMENT_TARGET_MISSING",
                )
        else:
            taken = set((await db.execute(select(Server.name))).scalars().all())
            node = Server(
                name=_unique_name(payload.hostname.strip(), taken),
                hostname=payload.hostname.strip(),
                os_name=payload.os_name,
                os_version=payload.os_version,
                arch=payload.arch,
                cpu_cores=payload.cpu_cores,
                memory_total_mb=payload.memory_total_mb,
                disk_total_gb=payload.disk_total_gb,
                # The node is not ONLINE until a heartbeat is accepted; but the
                # real-agent flag must be false from the moment it is a real node.
                simulated=False,
            )
            db.add(node)
            await db.flush()

        # Real telemetry, not simulation: an enrolled node is never a sim source.
        node.simulated = False
        if payload.agent_version:
            node.agent_version = payload.agent_version
        node.credential_revoked_at = None

        raw_agent_token, _prefix, agent_hash = generate_agent_token()
        credential = await db.get(AgentCredential, node.id)
        if credential is None:
            db.add(
                AgentCredential(
                    server_id=node.id,
                    org_id=node.org_id,
                    token_hash=agent_hash,
                    created_by_id=token.created_by_id,
                )
            )
        else:
            # Re-enrollment through a fresh token replaces the credential
            # outright: the old one is dead immediately, and no grace applies to
            # an enrollment (grace exists only for a *rotation* of a live node).
            credential.token_hash = agent_hash
            credential.revoked_at = None
            credential.rotated_at = now
            credential.previous_token_hash = None
            credential.previous_expires_at = None
            credential.pending_token_ciphertext = None
            credential.rotation_applied_at = None

        token.used_by_node_id = node.id
        await db.flush()

        log.info(
            "node_enrolled",
            node=str(node.id),
            org=str(token.org_id),
            token=str(token.id),
            claimed=token.node_id is not None,
        )
        return node, raw_agent_token


def enrollment_contract(node: Server) -> dict[str, Any]:
    """The minimum response an enrolling agent needs (facts about its new node)."""
    return {
        "node_id": node.id,
        "name": node.name,
        "heartbeat_interval_seconds": node.heartbeat_interval_seconds,
        "offline_after_seconds": node.offline_after_seconds,
        "protocol_version": AGENT_PROTOCOL_VERSION,
    }
