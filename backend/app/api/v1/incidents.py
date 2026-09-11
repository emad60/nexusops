"""Incident endpoints: list, detail with timeline, acknowledge, resolve, notes."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel

from app.api.deps import AuthContext, DbSessionDep, require_permission
from app.core.errors import NotFound
from app.core.pagination import Page, PageParams, page_params
from app.models.enums import IncidentSeverity, IncidentStatus
from app.schemas.incident import (
    IncidentAcknowledge,
    IncidentDetail,
    IncidentNote,
    IncidentOut,
    IncidentResolve,
)
from app.services import incident_service

router = APIRouter(prefix="/incidents", tags=["incidents"])

DbDep = DbSessionDep
ReadCtx = Annotated[AuthContext, Depends(require_permission("monitor.read"))]
ActionCtx = Annotated[AuthContext, Depends(require_permission("incident.action"))]


def _to_out(incident, names: dict) -> IncidentOut:
    out = IncidentOut.model_validate(incident)
    out.monitor_name = names.get(incident.monitor_id)
    return out


async def _require_incident(db: DbDep, incident_id: uuid.UUID):
    incident = await incident_service.get_incident(db, incident_id)
    if incident is None:
        raise NotFound("Incident not found")
    return incident


class AckResponse(BaseModel):
    status: IncidentStatus


@router.get("", response_model=Page[IncidentOut])
async def list_incidents(
    db: DbDep,
    ctx: ReadCtx,
    params: Annotated[PageParams, Depends(page_params)],
    status_filter: IncidentStatus | None = Query(None, alias="status"),
    severity: IncidentSeverity | None = Query(None),
    monitor_id: uuid.UUID | None = Query(None),
) -> Page[IncidentOut]:
    """List incidents (newest first) with optional filters."""
    rows, total = await incident_service.list_incidents(
        db,
        status_filter=status_filter,
        severity=severity,
        monitor_id=monitor_id,
        limit=params.limit,
        offset=params.offset,
    )
    names = await incident_service.monitor_names(db, rows)
    return Page(
        items=[_to_out(i, names) for i in rows],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@router.get("/{incident_id}", response_model=IncidentDetail)
async def get_incident(db: DbDep, ctx: ReadCtx, incident_id: uuid.UUID) -> IncidentDetail:
    incident = await _require_incident(db, incident_id)
    names = await incident_service.monitor_names(db, [incident])
    out = IncidentDetail.model_validate(incident)
    out.monitor_name = names.get(incident.monitor_id)
    return out


@router.post("/{incident_id}/acknowledge", response_model=IncidentOut)
async def acknowledge_incident(
    request: Request,
    db: DbDep,
    ctx: ActionCtx,
    incident_id: uuid.UUID,
    data: IncidentAcknowledge | None = None,
) -> IncidentOut:
    incident = await _require_incident(db, incident_id)
    note = data.note.strip() if data and data.note else ""
    updated = await incident_service.acknowledge(db, incident, ctx, note=note, request=request)
    names = await incident_service.monitor_names(db, [updated])
    return _to_out(updated, names)


@router.post("/{incident_id}/resolve", response_model=IncidentOut)
async def resolve_incident(
    request: Request,
    db: DbDep,
    ctx: ActionCtx,
    incident_id: uuid.UUID,
    data: IncidentResolve,
) -> IncidentOut:
    incident = await _require_incident(db, incident_id)
    updated = await incident_service.resolve(
        db, incident, data.resolution.strip(), ctx, request=request
    )
    names = await incident_service.monitor_names(db, [updated])
    return _to_out(updated, names)


@router.post("/{incident_id}/notes", response_model=IncidentDetail)
async def add_incident_note(
    request: Request, db: DbDep, ctx: ActionCtx, incident_id: uuid.UUID, data: IncidentNote
) -> IncidentDetail:
    incident = await _require_incident(db, incident_id)
    await incident_service.add_note(db, incident, ctx, data.message, request=request)
    refreshed = await incident_service.get_incident(db, incident_id)
    assert refreshed is not None  # just written in this transaction
    names = await incident_service.monitor_names(db, [refreshed])
    out = IncidentDetail.model_validate(refreshed)
    out.monitor_name = names.get(refreshed.monitor_id)
    return out
