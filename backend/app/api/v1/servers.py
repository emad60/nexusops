"""Server endpoints: CRUD, tags, agent enrollment tokens."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext, require_permission
from app.core.db import get_session
from app.core.pagination import Page, PageParams, page_params
from app.models.enums import ServerStatus
from app.schemas.server import (
    EnrollTokenOut,
    ServerCreate,
    ServerDetail,
    ServerOut,
    ServerUpdate,
    SystemEventOut,
)
from app.schemas.tag import TagOut, TagUpsertIn
from app.services import audit_service, server_service

router = APIRouter(prefix="/servers", tags=["servers"])

ReadCtx = Annotated[AuthContext, Depends(require_permission("server.read"))]
CreateCtx = Annotated[AuthContext, Depends(require_permission("server.create"))]
UpdateCtx = Annotated[AuthContext, Depends(require_permission("server.update"))]
DeleteCtx = Annotated[AuthContext, Depends(require_permission("server.delete"))]

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


@router.get("", response_model=Page[ServerOut])
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


@router.post("", response_model=ServerOut, status_code=status.HTTP_201_CREATED)
async def create_server(
    data: ServerCreate, request: Request, db: DbDep, ctx: CreateCtx
) -> ServerOut:
    """Register a server. Returns the row without an enrollment token —
    generate one via ``POST /servers/{id}/agent-token``."""
    server = await server_service.create_server(db, payload=data, ctx=ctx)
    await audit_service.record(
        db,
        ctx,
        action="server.create",
        resource_type="server",
        resource_id=server.id,
        metadata={"name": server.name, "environment": server.environment},
        request=request,
    )
    return ServerOut.model_validate(server)


@router.get("/tags", response_model=list[TagOut])
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


@router.post("/tags", response_model=TagOut, status_code=status.HTTP_201_CREATED)
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


@router.get("/{server_id}", response_model=ServerDetail)
async def get_server(db: DbDep, ctx: ReadCtx, server_id: uuid.UUID) -> ServerDetail:
    """Full server view with recent timeline events and container counts."""
    return await _detail(db, server_id)


@router.patch("/{server_id}", response_model=ServerDetail)
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
        action="server.update",
        resource_type="server",
        resource_id=server_id,
        metadata={"fields": sorted(data.model_dump(exclude_unset=True))},
        request=request,
    )
    return await _detail(db, server_id)


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_server(server_id: uuid.UUID, request: Request, db: DbDep, ctx: DeleteCtx) -> None:
    """Hard-delete a server and all of its children (cascades)."""
    snapshot = await server_service.delete_server(db, server_id=server_id, ctx=ctx)
    await audit_service.record(
        db,
        ctx,
        action="server.delete",
        resource_type="server",
        resource_id=server_id,
        metadata=snapshot,
        request=request,
    )


@router.post("/{server_id}/agent-token", response_model=EnrollTokenOut)
async def rotate_agent_token(
    server_id: uuid.UUID, request: Request, db: DbDep, ctx: UpdateCtx
) -> EnrollTokenOut:
    """Issue a fresh agent enrollment token. Any previous token stops working.

    The raw token is shown exactly once and only ever stored hashed.
    """
    raw, _server = await server_service.rotate_agent_token(db, server_id=server_id)
    await audit_service.record(
        db,
        ctx,
        action="server.rotate_token",
        resource_type="server",
        resource_id=server_id,
        metadata={"name": _server.name},
        request=request,
    )
    install_hint = (
        "bash agent/install.sh   # from the NexusOps repository, with env: "
        f"NEXUSOPS_URL=<platform-url> NEXUSOPS_TOKEN={raw}"
    )
    return EnrollTokenOut(agent_token=raw, install_hint=install_hint)
