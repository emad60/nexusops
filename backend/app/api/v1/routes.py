"""Route endpoints: list, create, inspect, update, enable, disable, delete.

``domain.read`` covers reads (a route's whole point is where it points) and
``domain.manage`` covers every mutation, including enable/disable — those queue
``nginx.apply`` on a node, which the architecture gates on the same codename.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext, require_permission
from app.core.db import get_session
from app.core.pagination import Page, PageParams, page_params
from app.models.enums import RouteConfigState
from app.schemas.route import RouteCreate, RouteDetailOut, RouteOut, RouteUpdate
from app.services import route_service

router = APIRouter(prefix="/routes", tags=["routes"])

DbDep = Annotated[AsyncSession, Depends(get_session)]
ReadCtx = Annotated[AuthContext, Depends(require_permission("domain.read"))]
ManageCtx = Annotated[AuthContext, Depends(require_permission("domain.manage"))]


async def _serialize_many(db: AsyncSession, rows: list) -> list[RouteOut]:
    metadata = await route_service.relevant_metadata(db, rows)
    out: list[RouteOut] = []
    for route in rows:
        payload = RouteOut.model_validate(route)
        payload.domain_name = metadata["domain_names"].get(route.domain_id)
        payload.node_name = metadata["node_names"].get(route.node_id)
        container = metadata["containers"].get(route.container_id)
        if container is not None:
            payload.container_name = container.name
            payload.container_ref = container.container_id
        payload.url = f"http://{route.hostname}{route.path}"
        payload.removal_state = route_service.removal_state_of(route)
        payload.status_detail = await route_service.route_status_detail(route)
        out.append(payload)
    return out


@router.get("", response_model=Page[RouteOut])
async def list_routes(
    db: DbDep,
    _ctx: ReadCtx,
    params: Annotated[PageParams, Depends(page_params)],
    domain_id: Annotated[uuid.UUID | None, Query()] = None,
    node_id: Annotated[uuid.UUID | None, Query()] = None,
    enabled: Annotated[bool | None, Query()] = None,
    config_state: Annotated[RouteConfigState | None, Query()] = None,
) -> Page[RouteOut]:
    rows, total = await route_service.list_routes(
        db,
        params,
        domain_id=domain_id,
        node_id=node_id,
        enabled=enabled,
        config_state=config_state,
    )
    return Page[RouteOut](
        items=await _serialize_many(db, rows),
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@router.post("", response_model=RouteOut, status_code=status.HTTP_201_CREATED)
async def create_route(
    payload: RouteCreate,
    request: Request,
    db: DbDep,
    ctx: ManageCtx,
) -> RouteOut:
    route = await route_service.create_route(db, ctx, payload=payload, request=request)
    return (await _serialize_many(db, [route]))[0]


@router.get("/{route_id}", response_model=RouteDetailOut)
async def get_route(
    route_id: uuid.UUID,
    db: DbDep,
    _ctx: ReadCtx,
) -> RouteDetailOut:
    route = await route_service.get_route(db, route_id)
    payload = (await _serialize_many(db, [route]))[0]
    domain_status = await _domain_status(db, route.domain_id)
    return RouteDetailOut(**payload.model_dump(), domain_status=domain_status)


@router.patch("/{route_id}", response_model=RouteOut)
async def update_route(
    route_id: uuid.UUID,
    payload: RouteUpdate,
    request: Request,
    db: DbDep,
    ctx: ManageCtx,
) -> RouteOut:
    route = await route_service.update_route(
        db, ctx, route_id=route_id, payload=payload, request=request
    )
    return (await _serialize_many(db, [route]))[0]


@router.post("/{route_id}/enable", response_model=RouteOut)
async def enable_route(
    route_id: uuid.UUID,
    request: Request,
    db: DbDep,
    ctx: ManageCtx,
) -> RouteOut:
    route = await route_service.enable_route(db, ctx, route_id=route_id, request=request)
    return (await _serialize_many(db, [route]))[0]


@router.post("/{route_id}/disable", response_model=RouteOut)
async def disable_route(
    route_id: uuid.UUID,
    request: Request,
    db: DbDep,
    ctx: ManageCtx,
) -> RouteOut:
    route = await route_service.disable_route(db, ctx, route_id=route_id, request=request)
    return (await _serialize_many(db, [route]))[0]


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_route(
    route_id: uuid.UUID,
    request: Request,
    db: DbDep,
    ctx: ManageCtx,
) -> None:
    await route_service.delete_route(db, ctx, route_id=route_id, request=request)


async def _domain_status(db: AsyncSession, domain_id: uuid.UUID) -> str:
    from app.services import domain_service

    domain = await domain_service.get_domain(db, domain_id)
    return str(getattr(domain.status, "value", domain.status))
