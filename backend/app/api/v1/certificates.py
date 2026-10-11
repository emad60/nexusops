"""Certificate endpoints: request, list, inspect, update the renewal preference.

``certificate.read`` covers reads and ``certificate.manage`` covers every mutation
— the same split the registry defines for every other resource, resolved from the
caller's **membership** in the active organization. Both are org-scoped, so a
certificate id from another tenant is the same 404 a random uuid gets.

The phase's boundary is visible in what is *absent*: there is no issue, renew,
revoke or bind endpoint, because none of those can be honored before the key
envelope (5.2), the ACME client (5.3) and the delivery path (5.4) exist. A
request is recorded, and the read model says plainly that nothing has been
issued yet.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext, require_permission
from app.core.db import get_session
from app.core.pagination import Page, PageParams, page_params
from app.models.enums import CertificateStatus
from app.schemas.certificate import (
    CertificateCreate,
    CertificateDetailOut,
    CertificateOut,
    CertificateUpdate,
)
from app.services import certificate_service

router = APIRouter(prefix="/certificates", tags=["certificates"])

DbDep = Annotated[AsyncSession, Depends(get_session)]
ReadCtx = Annotated[AuthContext, Depends(require_permission("certificate.read"))]
ManageCtx = Annotated[AuthContext, Depends(require_permission("certificate.manage"))]


async def _serialize_many(db: AsyncSession, rows: list) -> list[CertificateOut]:
    metadata = await certificate_service.relevant_metadata(db, rows)
    return [
        certificate_service.serialize_certificate(
            certificate,
            domain=metadata["domains"].get(certificate.domain_id),
            generation=metadata["latest"].get(certificate.id),
        )
        for certificate in rows
    ]


@router.get("", response_model=Page[CertificateOut])
async def list_certificates(
    db: DbDep,
    _ctx: ReadCtx,
    params: Annotated[PageParams, Depends(page_params)],
    status_filter: Annotated[CertificateStatus | None, Query(alias="status")] = None,
    domain_id: Annotated[uuid.UUID | None, Query()] = None,
) -> Page[CertificateOut]:
    rows, total = await certificate_service.list_certificates(
        db, params, status=status_filter, domain_id=domain_id
    )
    return Page[CertificateOut](
        items=await _serialize_many(db, rows),
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@router.post("", response_model=CertificateOut, status_code=status.HTTP_201_CREATED)
async def create_certificate(
    payload: CertificateCreate,
    request: Request,
    db: DbDep,
    ctx: ManageCtx,
) -> CertificateOut:
    """Record a certificate request. **Nothing is issued by this call.**"""
    certificate = await certificate_service.create_certificate(
        db, ctx, payload=payload, request=request
    )
    return (await _serialize_many(db, [certificate]))[0]


@router.get("/{certificate_id}", response_model=CertificateDetailOut)
async def get_certificate(
    certificate_id: uuid.UUID,
    db: DbDep,
    _ctx: ReadCtx,
) -> CertificateDetailOut:
    certificate = await certificate_service.get_certificate(db, certificate_id)
    base = (await _serialize_many(db, [certificate]))[0]
    generations = await certificate_service.all_generations(db, certificate.id)
    return CertificateDetailOut(
        **base.model_dump(),
        generations=[
            certificate_service.serialize_generation(generation) for generation in generations
        ],
    )


@router.delete("/{certificate_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_certificate(
    certificate_id: uuid.UUID,
    request: Request,
    db: DbDep,
    ctx: ManageCtx,
) -> None:
    """Delete a certificate request. Refused once a generation has been issued."""
    await certificate_service.delete_certificate(
        db, ctx, certificate_id=certificate_id, request=request
    )


@router.patch("/{certificate_id}", response_model=CertificateOut)
async def update_certificate(
    certificate_id: uuid.UUID,
    payload: CertificateUpdate,
    request: Request,
    db: DbDep,
    ctx: ManageCtx,
) -> CertificateOut:
    """Update ``auto_renew`` — the only field a request may change in place."""
    certificate = await certificate_service.update_certificate(
        db, ctx, certificate_id=certificate_id, payload=payload, request=request
    )
    return (await _serialize_many(db, [certificate]))[0]
