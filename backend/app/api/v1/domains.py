"""Domain endpoints: add, list, inspect, verify, re-verify, delete.

Authorization is the central registry, never a role-name check: ``domain.read``
for reads and ``domain.manage`` for anything that changes ownership state. The
verification token is only rendered for callers holding ``domain.manage`` **and**
only while it is still actionable — a token echoed to a reader, or long after
verification, is a replay primitive.

Verification work is enqueued *after commit*: a task that ran before the row was
visible would observe a domain that does not exist yet.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext, require_permission
from app.core.db import get_session
from app.core.pagination import Page, PageParams, page_params
from app.models import Project
from app.models.enums import DomainStatus
from app.schemas.domain import (
    DomainCreate,
    DomainDetailOut,
    DomainOut,
    DomainReachabilityOut,
    DomainVerificationOut,
)
from app.schemas.route import RouteOut
from app.services import domain_service, route_service
from app.services.enqueue import after_commit

router = APIRouter(prefix="/domains", tags=["domains"])

DbDep = Annotated[AsyncSession, Depends(get_session)]
ReadCtx = Annotated[AuthContext, Depends(require_permission("domain.read"))]
ManageCtx = Annotated[AuthContext, Depends(require_permission("domain.manage"))]

MANAGE_PERMISSION = "domain.manage"


def _serialize(
    domain,
    *,
    can_manage: bool,
    project_name: str | None = None,
    counts: tuple[int, int] = (0, 0),
) -> DomainOut:
    """Build the read model with the token policy applied in one place.

    ``include_token`` is the *caller's* permission; the service then decides
    whether a token is still actionable for this domain's state. Both must agree
    before a value leaves the control plane.
    """
    instructions = domain_service.verification_instructions(domain, include_token=can_manage)
    payload = DomainOut.model_validate(domain)
    payload.verification = DomainVerificationOut(**instructions) if instructions else None
    payload.project_name = project_name
    payload.reachability = (
        DomainReachabilityOut(**domain.dns_reachability) if domain.dns_reachability else None
    )
    payload.verified = DomainStatus(domain.status) is DomainStatus.VERIFIED
    payload.route_count, payload.enabled_route_count = counts
    return payload


async def _project_names(db: AsyncSession, domains: list) -> dict[uuid.UUID, str]:
    ids = {domain.project_id for domain in domains if domain.project_id}
    if not ids:
        return {}
    rows = (await db.execute(select(Project).where(Project.id.in_(ids)))).scalars().all()
    return {row.id: row.name for row in rows}


async def routes_for_domain(db: AsyncSession, domain_id: uuid.UUID) -> list[RouteOut]:
    rows, _ = await route_service.list_routes(
        db, PageParams(limit=100, offset=0), domain_id=domain_id
    )
    metadata = await route_service.relevant_metadata(db, rows)
    out: list[RouteOut] = []
    for route in rows:
        payload = RouteOut.model_validate(route)
        payload.domain_name = metadata["domain_names"].get(route.domain_id)
        payload.node_name = metadata["node_names"].get(route.node_id)
        container = metadata["containers"].get(route.container_id) if route.container_id else None
        if container is not None:
            payload.container_name = container.name
            payload.container_ref = container.container_id
        payload.url = f"http://{route.hostname}{route.path}"
        payload.removal_state = route_service.removal_state_of(route)
        payload.status_detail = await route_service.route_status_detail(route)
        out.append(payload)
    return out


@router.post("", response_model=DomainOut, status_code=status.HTTP_201_CREATED)
async def create_domain(
    payload: DomainCreate,
    request: Request,
    db: DbDep,
    ctx: ManageCtx,
) -> DomainOut:
    """Add a domain and return the exact TXT record that has to be published."""
    domain = await domain_service.create_domain(db, ctx, payload=payload, request=request)
    return _serialize(domain, can_manage=True)


@router.get("", response_model=Page[DomainOut])
async def list_domains(
    db: DbDep,
    ctx: ReadCtx,
    params: Annotated[PageParams, Depends(page_params)],
    status_filter: Annotated[DomainStatus | None, Query(alias="status")] = None,
    project_id: Annotated[uuid.UUID | None, Query()] = None,
) -> Page[DomainOut]:
    rows, total = await domain_service.list_domains(
        db, params, status=status_filter, project_id=project_id
    )
    counts = await domain_service.domain_route_counts(db, [row.id for row in rows])
    project_names = await _project_names(db, rows)
    can_manage = ctx.has_permission(MANAGE_PERMISSION)
    return Page[DomainOut](
        items=[
            _serialize(
                row,
                can_manage=can_manage,
                project_name=project_names.get(row.project_id) if row.project_id else None,
                counts=counts.get(row.id, (0, 0)),
            )
            for row in rows
        ],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@router.get("/{domain_id}", response_model=DomainDetailOut)
async def get_domain(
    domain_id: uuid.UUID,
    db: DbDep,
    ctx: ReadCtx,
) -> DomainDetailOut:
    domain = await domain_service.get_domain(db, domain_id)
    counts = await domain_service.domain_route_counts(db, [domain.id])
    project_names = await _project_names(db, [domain])
    base = _serialize(
        domain,
        can_manage=ctx.has_permission(MANAGE_PERMISSION),
        project_name=project_names.get(domain.project_id) if domain.project_id else None,
        counts=counts.get(domain.id, (0, 0)),
    )
    return DomainDetailOut(**base.model_dump(), routes=await routes_for_domain(db, domain.id))


@router.get("/{domain_id}/routes", response_model=list[RouteOut])
async def list_domain_routes(
    domain_id: uuid.UUID,
    db: DbDep,
    _ctx: ReadCtx,
) -> list[RouteOut]:
    domain = await domain_service.get_domain(db, domain_id)
    return await routes_for_domain(db, domain.id)


@router.post("/{domain_id}/verify", response_model=DomainOut)
async def verify_domain(
    domain_id: uuid.UUID,
    request: Request,
    db: DbDep,
    ctx: ManageCtx,
) -> DomainOut:
    """Start (or restart) a manual TXT verification against authoritative DNS."""
    domain = await domain_service.request_verification(
        db, ctx, domain_id=domain_id, request=request
    )
    domain_id_value = domain.id
    after_commit(db, "domain_verification", lambda: _enqueue_verification(domain_id_value))
    return _serialize(domain, can_manage=True)


@router.post("/{domain_id}/re-verify", response_model=DomainOut)
async def reverify_domain(
    domain_id: uuid.UUID,
    request: Request,
    db: DbDep,
    ctx: ManageCtx,
) -> DomainOut:
    """Re-prove control after the token, the delegation or the name changed."""
    return await verify_domain(domain_id, request, db, ctx)


@router.delete("/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_domain(
    domain_id: uuid.UUID,
    request: Request,
    db: DbDep,
    ctx: ManageCtx,
) -> None:
    await domain_service.delete_domain(db, ctx, domain_id=domain_id, request=request)


async def _enqueue_verification(domain_id: uuid.UUID) -> None:
    from app.tasks.domain_routing import verify_domain_task

    verify_domain_task.delay(str(domain_id))


__all__ = ["router", "routes_for_domain"]
