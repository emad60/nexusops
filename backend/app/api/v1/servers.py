"""Node endpoints: CRUD, tags, agent enrollment tokens.

The domain entity is the existing ``servers`` table (kept; domain-model.md
§2.2), renamed at the surface to **Node**. Routes are served under ``/nodes``
with a temporary ``/servers`` alias.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext, require_permission
from app.core.db import get_session
from app.core.pagination import Page, PageParams, page_params
from app.models.enums import ServerStatus
from app.schemas.enrollment import (
    EnrollmentTokenCreate,
    EnrollmentTokenCreated,
    EnrollmentTokenOut,
)
from app.schemas.server import (
    EnrollTokenOut,
    ServerCreate,
    ServerDetail,
    ServerOut,
    ServerUpdate,
    SystemEventOut,
)
from app.schemas.tag import TagOut, TagUpsertIn
from app.services import audit_service, enrollment_service, server_service

#: Prefix-less inner router: the paths below are declared once and mounted under
#: both the canonical ``/nodes`` surface and the temporary ``/servers`` alias.
_router = APIRouter()

ReadCtx = Annotated[AuthContext, Depends(require_permission("node.read"))]
CreateCtx = Annotated[AuthContext, Depends(require_permission("node.create"))]
UpdateCtx = Annotated[AuthContext, Depends(require_permission("node.update"))]
DeleteCtx = Annotated[AuthContext, Depends(require_permission("node.delete"))]
#: Credential lifecycle actions (rotate/revoke/enrollment-token revoke) reuse the
#: existing ``node.credential.write`` codename — no new grant is invented.
CredentialCtx = Annotated[AuthContext, Depends(require_permission("node.credential.write"))]

DbDep = Annotated[AsyncSession, Depends(get_session)]


async def _detail(db: AsyncSession, server_id: uuid.UUID) -> ServerDetail:
    server = await server_service.get_server(db, server_id)
    counts = await server_service.container_counts(db, server_id=server.id)
    events = await server_service.recent_events(db, server_id=server.id, limit=25)
    detail = ServerDetail.model_validate(server)
    detail.counts.containers_running = counts["containers_running"]
    detail.counts.containers_total = counts["containers_total"]
    detail.recent_events = [SystemEventOut.model_validate(e) for e in events]
    return detail


@_router.get("", response_model=Page[ServerOut])
async def list_servers(
    db: DbDep,
    ctx: ReadCtx,
    params: Annotated[PageParams, Depends(page_params)],
    status_filter: list[ServerStatus] | None = Query(None, alias="status"),
    environment: str | None = Query(None, max_length=32),
    tag: str | None = Query(None, max_length=64),
    q: str | None = Query(None, max_length=200),
    simulated: bool | None = Query(None),
    sort: str = Query("-created_at"),
) -> Page[ServerOut]:
    """List servers with filters, search and pagination."""
    rows, total = await server_service.list_servers(
        db,
        statuses=status_filter,
        environment=environment,
        tag=tag,
        q=q,
        simulated=simulated,
        sort=sort,
        params=params,
    )
    return Page(
        items=[ServerOut.model_validate(s) for s in rows],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@_router.post("", response_model=ServerOut, status_code=status.HTTP_201_CREATED)
async def create_server(
    data: ServerCreate, request: Request, db: DbDep, ctx: CreateCtx
) -> ServerOut:
    """Register a node. Returns the row without an enrollment token —
    generate one via ``POST /nodes/{id}/agent-token``."""
    server = await server_service.create_server(db, payload=data, ctx=ctx)
    await audit_service.record(
        db,
        ctx,
        action="node.create",
        resource_type="node",
        resource_id=server.id,
        metadata={"name": server.name, "environment": server.environment},
        request=request,
    )
    return ServerOut.model_validate(server)


@_router.get("/tags", response_model=list[TagOut])
async def list_tags(db: DbDep, ctx: ReadCtx) -> list[TagOut]:
    """All tags with their server usage counts."""
    pairs = await server_service.list_tags_with_usage(db)
    return [
        TagOut(
            id=tag.id,
            created_at=tag.created_at,
            name=tag.name,
            color=tag.color or "#64748b",
            usage_count=count,
        )
        for tag, count in pairs
    ]


@_router.post("/tags", response_model=TagOut, status_code=status.HTTP_201_CREATED)
async def upsert_tag(db: DbDep, ctx: UpdateCtx, data: TagUpsertIn) -> TagOut:
    """Create a tag or update its colour (idempotent on name)."""
    tag = await server_service.upsert_tag(db, name=data.name, color=data.color)
    count = await server_service.tag_usage_count(db, tag_id=tag.id)
    return TagOut(
        id=tag.id,
        created_at=tag.created_at,
        name=tag.name,
        color=tag.color or "#64748b",
        usage_count=count,
    )


# --- Enrollment tokens (organization-scoped) --------------------------------
# Declared before ``/{server_id}`` so the literal path is not consumed as a node
# id — the same ordering ``/tags`` relies on.


@_router.post(
    "/enrollment-tokens",
    response_model=EnrollmentTokenCreated,
    status_code=status.HTTP_201_CREATED,
)
async def create_enrollment_token(
    data: EnrollmentTokenCreate, request: Request, db: DbDep, ctx: CreateCtx
) -> EnrollmentTokenCreated:
    """Mint one single-use enrollment token in the caller's organization.

    The org comes from the caller's active membership (unknown to the request
    body), so a token can never be minted into another tenant. The raw token is
    returned exactly once and stored only as a hash.
    """
    raw, token = await enrollment_service.create_token(db, ctx, data)
    await audit_service.record(
        db,
        ctx,
        action="enrollment_token.create",
        resource_type="enrollment_token",
        resource_id=token.id,
        metadata={"name": token.name, "expires_at": token.expires_at.isoformat()},
        request=request,
    )
    return _enrollment_created(raw, token)


@_router.get("/enrollment-tokens", response_model=Page[EnrollmentTokenOut])
async def list_enrollment_tokens(
    db: DbDep,
    ctx: ReadCtx,
    params: Annotated[PageParams, Depends(page_params)],
) -> Page[EnrollmentTokenOut]:
    """Enrollment tokens in the active organization, newest first.

    The response type has no token field, so a raw value can never be re-read.
    """
    tokens, total = await enrollment_service.list_tokens(
        db, limit=params.limit, offset=params.offset
    )
    return Page(
        items=[_enrollment_out(token) for token in tokens],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@_router.post("/enrollment-tokens/{token_id}/revoke", response_model=EnrollmentTokenOut)
async def revoke_enrollment_token(
    token_id: uuid.UUID, request: Request, db: DbDep, ctx: CredentialCtx
) -> EnrollmentTokenOut:
    """Revoke an unused enrollment token immediately."""
    token = await enrollment_service.revoke_token(db, token_id, ctx=ctx)
    await audit_service.record(
        db,
        ctx,
        action="enrollment_token.revoke",
        resource_type="enrollment_token",
        resource_id=token.id,
        metadata={"name": token.name},
        request=request,
    )
    return _enrollment_out(token)


@_router.get("/{server_id}", response_model=ServerDetail)
async def get_server(db: DbDep, ctx: ReadCtx, server_id: uuid.UUID) -> ServerDetail:
    """Full server view with recent timeline events and container counts."""
    return await _detail(db, server_id)


@_router.patch("/{server_id}", response_model=ServerDetail)
async def update_server(
    server_id: uuid.UUID,
    data: ServerUpdate,
    request: Request,
    db: DbDep,
    ctx: UpdateCtx,
) -> ServerDetail:
    """Apply a partial update; ``tags`` replaces the whole set when present."""
    await server_service.update_server(db, server_id=server_id, payload=data, ctx=ctx)
    await audit_service.record(
        db,
        ctx,
        action="node.update",
        resource_type="node",
        resource_id=server_id,
        metadata={"fields": sorted(data.model_dump(exclude_unset=True))},
        request=request,
    )
    return await _detail(db, server_id)


@_router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(server_id: uuid.UUID, request: Request, db: DbDep, ctx: DeleteCtx) -> None:
    """Hard-delete a server and all of its children (cascades)."""
    snapshot = await server_service.delete_server(db, server_id=server_id, ctx=ctx)
    await audit_service.record(
        db,
        ctx,
        action="node.delete",
        resource_type="node",
        resource_id=server_id,
        metadata=snapshot,
        request=request,
    )


@_router.post("/{server_id}/agent-token", response_model=EnrollTokenOut)
async def rotate_agent_token(
    server_id: uuid.UUID, request: Request, db: DbDep, ctx: UpdateCtx
) -> EnrollTokenOut:
    """Rotate a node's credential with a bounded dual-token grace window.

    The previous token keeps authenticating for the configured grace period so a
    running agent can pick up the replacement on its next heartbeat; the raw new
    token is shown exactly once here. This is *rotation*, not revocation — see
    ``POST /nodes/{id}/agent-token/revoke`` for the immediate kill switch.
    """
    raw, _server = await server_service.rotate_agent_token(db, server_id=server_id, ctx=ctx)
    await audit_service.record(
        db,
        ctx,
        action="node.rotate_token",
        resource_type="node",
        resource_id=server_id,
        # Metadata is names and ids only: never the raw token or its hash.
        metadata={"name": _server.name},
        request=request,
    )
    # The hint names the variables the agent and installer actually read, and
    # delivers the token through the environment so it never lands in shell
    # history or the target's process list (argument vectors are observable).
    install_hint = (
        "sudo NEXUSOPS_TOKEN=<token> NEXUSOPS_SERVER=<platform-url> bash agent/install.sh"
    )
    return EnrollTokenOut(agent_token=raw, install_hint=install_hint)


@_router.post("/{server_id}/agent-token/revoke", response_model=ServerOut)
async def revoke_agent_token(
    server_id: uuid.UUID, request: Request, db: DbDep, ctx: CredentialCtx
) -> ServerOut:
    """Immediately stop accepting this node's credential. No grace, no delivery.

    This is the compromise path: a stolen token cannot fetch a replacement, and
    the node stops being addressed at once. Recovery is a re-enrollment with a
    fresh organization-scoped token, not a reinstall.
    """
    node = await server_service.revoke_agent_token(db, server_id=server_id, ctx=ctx)
    await audit_service.record(
        db,
        ctx,
        action="node.revoke_token",
        resource_type="node",
        resource_id=server_id,
        metadata={"name": node.name},
        request=request,
    )
    return ServerOut.model_validate(node)


def _enrollment_out(token: object) -> EnrollmentTokenOut:
    return EnrollmentTokenOut.model_validate(token)


def _enrollment_created(raw: str, token: object) -> EnrollmentTokenCreated:
    # ``state`` is a computed field on the schema, so validating the row is
    # enough; drop the derived value (extra="forbid") and add the one-time raw
    # token and its hint.
    data = EnrollmentTokenOut.model_validate(token).model_dump()
    data.pop("state", None)
    data.update(token=raw, install_hint=enrollment_service.install_hint(raw))
    return EnrollmentTokenCreated(**data)


# Canonical surface. New clients discover only ``/nodes`` (see the package docs).
router = APIRouter()
router.include_router(_router, prefix="/nodes", tags=["nodes"])

# Temporary compatibility alias for pre-rename clients. Hidden from the OpenAPI
# schema so it is not advertised; remove in the Phase 2 cleanup.
servers_router = APIRouter()
servers_router.include_router(_router, prefix="/servers", tags=["servers"], include_in_schema=False)
