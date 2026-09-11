"""Deployment endpoints: list, detail, trigger, cancel, rollback, logs.

Two routers are exported (the trigger/list aliases nest under a top-level
``/applications`` prefix):

* ``router`` — ``/deployments``
* ``applications_router`` — ``/applications/{id}/deployments[...]`` aliases
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import AuthContext, DbSessionDep, require_permission
from app.core.errors import NotFound, UnprocessableEntity
from app.core.pagination import (
    CursorPage,
    CursorParams,
    Page,
    PageParams,
    cursor_params,
    decode_cursor,
    encode_cursor,
    page_params,
    paginate,
)
from app.core.rate_limit import expensive_op_limiter
from app.models import Deployment, DeploymentEnvironment, DeploymentStep, LogEntry, User
from app.models.enums import DeploymentStatus, DeploymentTrigger
from app.schemas.deployment import DeploymentCreate, DeploymentDetail, DeploymentOut, LogOut
from app.services import deployment_engine, project_service

router = APIRouter(prefix="/deployments", tags=["deployments"])
applications_router = APIRouter(prefix="/applications", tags=["deployments"])

# main.py mounts each module's ``router`` only; nesting keeps the top-level
# ``/applications`` routes alive without a second include_router call there.
router.include_router(applications_router)

ReadUser = Annotated[AuthContext, Depends(require_permission("deployment.read"))]
CreateUser = Annotated[AuthContext, Depends(require_permission("deployment.create"))]
CancelUser = Annotated[AuthContext, Depends(require_permission("deployment.cancel"))]
RollbackUser = Annotated[AuthContext, Depends(require_permission("deployment.rollback"))]

_SORT_COLUMNS = {
    "created_at": Deployment.created_at,
    "started_at": Deployment.started_at,
    "number": Deployment.number,
}


def _parse_statuses(raw: str | None) -> list[DeploymentStatus]:
    if not raw:
        return []
    try:
        return [DeploymentStatus(item.strip().upper()) for item in raw.split(",") if item.strip()]
    except ValueError as exc:
        valid = ", ".join(status.value for status in DeploymentStatus)
        raise UnprocessableEntity(
            f"Unknown status filter. Valid values: {valid}", code="INVALID_STATUS"
        ) from exc


def _parse_sort(sort: str) -> list:
    descending = sort.startswith("-")
    column = _SORT_COLUMNS.get(sort.lstrip("-"))
    if column is None:
        raise UnprocessableEntity(
            f"sort must be one of: {', '.join(_SORT_COLUMNS)}", code="INVALID_SORT"
        )
    ordered = column.desc() if descending else column.asc()
    return [ordered, Deployment.id.desc()]


async def _emails_for(db: AsyncSession, deployments: list[Deployment]) -> dict[UUID, str]:
    user_ids = {dep.triggered_by_id for dep in deployments if dep.triggered_by_id}
    if not user_ids:
        return {}
    rows = await db.execute(select(User.id, User.email).where(User.id.in_(user_ids)))
    return {user_id: email for user_id, email in rows.all()}


# --- Listing --------------------------------------------------------------------


async def _list_deployments(
    db: DbSessionDep,
    page: PageParams,
    *,
    application_id: UUID | None,
    environment_id: UUID | None,
    statuses_raw: str | None,
    is_rollback: bool | None,
    q: str | None,
    sort: str,
) -> Page[DeploymentOut]:
    stmt: Select = select(Deployment)
    if application_id is not None:
        stmt = stmt.where(Deployment.application_id == application_id)
    if environment_id is not None:
        stmt = stmt.where(Deployment.environment_id == environment_id)
    statuses = _parse_statuses(statuses_raw)
    if statuses:
        stmt = stmt.where(Deployment.status.in_(statuses))
    if is_rollback is not None:
        stmt = stmt.where(Deployment.is_rollback.is_(is_rollback))
    if q:
        needle = f"%{q}%"
        stmt = stmt.where(or_(Deployment.version.ilike(needle), Deployment.notes.ilike(needle)))

    ordered = stmt.order_by(*_parse_sort(sort)).options(
        selectinload(Deployment.application),
        selectinload(Deployment.environment),
    )
    rows, total = await paginate(db, ordered, page)
    emails = await _emails_for(db, rows)
    return Page(
        items=[DeploymentOut.build(row, emails.get(row.triggered_by_id)) for row in rows],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )


@router.get("", response_model=Page[DeploymentOut])
async def list_deployments(
    db: DbSessionDep,
    _: ReadUser,
    page: Annotated[PageParams, Depends(page_params)],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    application_id: UUID | None = None,
    environment_id: UUID | None = None,
    is_rollback: bool | None = None,
    q: Annotated[str | None, Query(max_length=120)] = None,
    sort: str = "-created_at",
) -> Page[DeploymentOut]:
    """Filtered, sorted deployment list."""
    return await _list_deployments(
        db,
        page,
        application_id=application_id,
        environment_id=environment_id,
        statuses_raw=status_filter,
        is_rollback=is_rollback,
        q=q,
        sort=sort,
    )


@applications_router.get("/{application_id}/deployments", response_model=Page[DeploymentOut])
async def list_application_deployments(
    application_id: UUID,
    db: DbSessionDep,
    _: ReadUser,
    page: Annotated[PageParams, Depends(page_params)],
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    q: Annotated[str | None, Query(max_length=120)] = None,
    sort: str = "-created_at",
) -> Page[DeploymentOut]:
    """Alias of the deployment list scoped to one application."""
    await project_service.get_application(db, application_id)
    return await _list_deployments(
        db,
        page,
        application_id=application_id,
        environment_id=None,
        statuses_raw=status_filter,
        is_rollback=None,
        q=q,
        sort=sort,
    )


# --- Trigger / detail / cancel / rollback -----------------------------------------


@applications_router.post(
    "/{application_id}/deployments",
    response_model=DeploymentDetail,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(expensive_op_limiter())],
)
async def trigger_deployment(
    application_id: UUID,
    payload: DeploymentCreate,
    db: DbSessionDep,
    ctx: CreateUser,
    request: Request,
) -> DeploymentDetail:
    """Queue a new deployment for an application/environment pair."""
    application = await project_service.get_application(db, application_id)
    environment = await db.get(DeploymentEnvironment, payload.environment_id)
    if environment is None:
        raise NotFound("Environment not found")
    trigger = DeploymentTrigger.API if ctx.actor_type == "API_KEY" else DeploymentTrigger.MANUAL
    deployment = await deployment_engine.queue_deployment(
        db,
        ctx=ctx,
        application=application,
        environment=environment,
        version=payload.version,
        git_commit=payload.git_commit,
        notes=payload.notes,
        trigger=trigger,
        request=request,
    )
    # The freshly flushed row has no relationships loaded (steps/application/
    # environment were set by id, not object) — serializing it directly would
    # lazy-load on an AsyncSession and blow up with MissingGreenlet. Re-read it
    # eagerly, exactly like the cancel and rollback routes do.
    refreshed = await deployment_engine.get_deployment(db, deployment.id)
    return DeploymentDetail.build(refreshed)


@router.get("/{deployment_id}", response_model=DeploymentDetail)
async def get_deployment(
    deployment_id: UUID,
    db: DbSessionDep,
    _: ReadUser,
) -> DeploymentDetail:
    deployment = await deployment_engine.get_deployment(db, deployment_id)
    return DeploymentDetail.build(deployment)


@router.post("/{deployment_id}/cancel", response_model=DeploymentDetail)
async def cancel_deployment(
    deployment_id: UUID,
    db: DbSessionDep,
    ctx: CancelUser,
    request: Request,
) -> DeploymentDetail:
    """Cancel a QUEUED deployment immediately or flag a RUNNING one."""
    await deployment_engine.cancel_deployment(db, ctx, deployment_id, request=request)
    refreshed = await deployment_engine.get_deployment(db, deployment_id)
    return DeploymentDetail.build(refreshed)


@router.post(
    "/{deployment_id}/rollback",
    response_model=DeploymentDetail,
    status_code=status.HTTP_202_ACCEPTED,
)
async def rollback_deployment(
    deployment_id: UUID,
    db: DbSessionDep,
    ctx: RollbackUser,
    request: Request,
) -> DeploymentDetail:
    """Queue a rollback to the last good version of this app/environment."""
    created = await deployment_engine.rollback_deployment(db, ctx, deployment_id, request=request)
    refreshed = await deployment_engine.get_deployment(db, created.id)
    return DeploymentDetail.build(refreshed)


# --- Logs -----------------------------------------------------------------------


def _attribute_step_idx(steps: Sequence[DeploymentStep], ts: datetime) -> int | None:
    current = None
    for step in steps:
        if step.started_at is None or step.started_at > ts:
            break
        current = step.idx
    return current


@router.get("/{deployment_id}/logs", response_model=CursorPage[LogOut])
async def list_deployment_logs(
    deployment_id: UUID,
    db: DbSessionDep,
    _: ReadUser,
    params: Annotated[CursorParams, Depends(cursor_params)],
) -> CursorPage[LogOut]:
    """Keyset-paginated deployment log lines in ascending insertion order."""
    deployment = await deployment_engine.get_deployment(db, deployment_id)
    cursor = decode_cursor(params.cursor)
    stmt = (
        select(LogEntry)
        .where(LogEntry.deployment_id == deployment.id)
        .order_by(LogEntry.id.asc())
        .limit(params.limit + 1)
    )
    if cursor is not None:
        stmt = stmt.where(LogEntry.id > cursor.id)
    rows = list((await db.execute(stmt)).scalars().all())
    has_more = len(rows) > params.limit
    rows = rows[: params.limit]
    next_cursor = encode_cursor(rows[-1].ts, rows[-1].id) if has_more and rows else None
    items = []
    for row in rows:
        item = LogOut.model_validate(row)
        item.step_idx = _attribute_step_idx(deployment.steps, row.ts)
        items.append(item)
    return CursorPage(items=items, next_cursor=next_cursor, has_more=has_more)
