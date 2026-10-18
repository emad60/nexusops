"""Certificate endpoints: request, list, inspect, retry, update the preference.

``certificate.read`` covers reads and ``certificate.manage`` covers every mutation
— the same split the registry defines for every other resource, resolved from the
caller's **membership** in the active organization. Both are org-scoped, so a
certificate id from another tenant is the same 404 a random uuid gets.

Two endpoints *start work* and neither of them does it: ``POST /certificates``
records a request, and ``POST /certificates/{id}/retry`` re-arms the schedule of an
attempt that already failed. Both hand the generation to the worker, and the worker
is the only thing that contacts a CA or writes material, so ``202 Accepted`` is
what a retry answers with. Every refusal — already issued, attempt budget spent, an
attempt genuinely running — is a named error, never a silent success.

The phase's boundary is visible in what is still *absent*: there is no renew,
revoke or bind endpoint, because none of those can be honored before the delivery
path (5.4) and the renewal slice (5.6) exist. A request is recorded, issuance is
attempted in the background, and the read model says which of the two happened.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext, require_permission
from app.core.db import get_session
from app.core.pagination import Page, PageParams, page_params
from app.models.certificate import Certificate
from app.models.enums import CertificateStatus
from app.schemas.certificate import (
    CertificateCreate,
    CertificateDetailOut,
    CertificateOut,
    CertificateUpdate,
)
from app.services import certificate_issuance, certificate_service

router = APIRouter(prefix="/certificates", tags=["certificates"])

DbDep = Annotated[AsyncSession, Depends(get_session)]
ReadCtx = Annotated[AuthContext, Depends(require_permission("certificate.read"))]
ManageCtx = Annotated[AuthContext, Depends(require_permission("certificate.manage"))]


async def _detail(db: AsyncSession, certificate: Certificate) -> CertificateDetailOut:
    """The single-certificate read model: metadata plus its generation history."""
    base = (await _serialize_many(db, [certificate]))[0]
    generations = await certificate_service.all_generations(db, certificate.id)
    return CertificateDetailOut(
        **base.model_dump(),
        generations=[
            certificate_service.serialize_generation(generation) for generation in generations
        ],
    )


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


@router.post(
    "/{certificate_id}/retry",
    response_model=CertificateDetailOut,
    status_code=status.HTTP_202_ACCEPTED,
)
async def retry_certificate(
    certificate_id: uuid.UUID,
    request: Request,
    db: DbDep,
    ctx: ManageCtx,
) -> CertificateDetailOut:
    """Pull the next issuance attempt forward and hand it to the worker.

    Accepted rather than performed: this call changes no state a CA has to answer
    for, it makes the generation due now and dispatches the same task the sweep and
    the creation path dispatch. The refusals are the point of the endpoint — a
    certificate that has already been issued, one whose attempt budget is spent,
    and one whose attempt is genuinely running each get their own message instead
    of a 200 that does nothing.
    """
    certificate = await certificate_service.get_certificate(db, certificate_id)
    await certificate_issuance.request_retry(db, certificate, ctx, request=request)
    return await _detail(db, certificate)


@router.get("/{certificate_id}", response_model=CertificateDetailOut)
async def get_certificate(
    certificate_id: uuid.UUID,
    db: DbDep,
    _ctx: ReadCtx,
) -> CertificateDetailOut:
    certificate = await certificate_service.get_certificate(db, certificate_id)
    return await _detail(db, certificate)


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
