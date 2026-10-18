"""Certificate endpoints: request, list, inspect, retry, update, manual challenge.

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

The two ``/challenge`` endpoints are the **only** exit for a manual DNS-01 TXT
value. ``GET`` reports the exact record to publish and the last authoritative
observation; ``POST .../confirm`` records "I published it" and rechecks DNS once.
Both require ``certificate.manage`` with the caller's own organization — a
``certificate.read`` grant is enough to see that a certificate exists, and this is
deliberately more than that, because publishing the wrong value is a live
issuance step rather than a metadata read. Confirming is a request to look, never a
claim that the challenge passed: the CA's authorization stays the only verdict.

The phase's boundary is visible in what is still *absent*: there is no renew,
revoke or bind endpoint, because none of those can be honored before the delivery
path (5.4) and the renewal slice (5.6) exist. A request is recorded, issuance is
attempted in the background, and the read model says which of the two happened.
"""

from __future__ import annotations

import uuid
from datetime import datetime
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
    ManualChallengeConfirmIn,
    ManualChallengeOut,
    ManualChallengeRecordOut,
    ManualCleanupOut,
    ManualCleanupRecordOut,
    ManualNameserverAnswerOut,
    ManualObservationOut,
)
from app.services import certificate_issuance, certificate_order, certificate_service

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


def _at(value: object) -> datetime | None:
    """A stored challenge timestamp as a datetime, or ``None`` when there is none.

    The order document keeps its stamps as strings and writes ``""`` for "not yet",
    which is not a datetime. The response models accept only the latter, so the
    empty placeholder has to be translated here rather than leak into validation.
    """
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _manual_out(
    status_in: certificate_issuance.ManualChallengeStatus,
) -> ManualChallengeOut:
    """The operator-facing view of one manual challenge set.

    Everything here comes from the persisted order document and the certificate
    row — no DNS is contacted and nothing is written, so this answers the same way
    whether it is called once or fifty times.
    """
    instructions = certificate_order.manual_instructions(status_in.document)
    cleanup = certificate_order.cleanup_instructions(
        status_in.document, complete=status_in.finished
    )
    raw = status_in.observation
    return ManualChallengeOut(
        certificate_id=status_in.certificate_id,
        generation=status_in.generation,
        state=status_in.state,
        identifiers=list(status_in.identifiers),
        records=[
            ManualChallengeRecordOut(
                reference=str(entry.get("ref") or ""),
                identifier=str(entry.get("identifier") or ""),
                wildcard=bool(entry.get("wildcard")),
                record_name=str(entry.get("record_name") or ""),
                record_value=str(entry.get("record_value") or ""),
                recommended_ttl=entry.get("recommended_ttl"),
                confirmed=bool(entry.get("confirmed")),
                confirmed_at=_at(entry.get("confirmed_at")),
                observed=bool(entry.get("observed")),
                observed_at=_at(entry.get("observed_at")),
                validated=bool(entry.get("validated")),
                validated_at=_at(entry.get("validated_at")),
                problem=str(entry.get("problem") or ""),
            )
            for entry in instructions
        ],
        ready=certificate_order.manual_ready(status_in.document),
        observation=(
            ManualObservationOut(
                status=str(raw.get("status") or ""),
                detail=str(raw.get("detail") or ""),
                checked_at=_at(raw.get("checked_at")),
                attempts=int(raw.get("attempts") or 0),
                nameservers=[
                    ManualNameserverAnswerOut(
                        server=answer["server"],
                        status=answer["status"],
                        serves_expected=answer["serves_expected"],
                    )
                    for answer in raw.get("nameservers") or []
                ],
            )
            if raw is not None
            else None
        ),
        cleanup=ManualCleanupOut(
            required=bool(cleanup["required"]),
            records=[ManualCleanupRecordOut(**record) for record in cleanup["records"]],
            note=str(cleanup["note"] or ""),
        ),
        resume_requested=status_in.resume_requested,
        order_expires_at=certificate_order.order_expires(status_in.document),
    )


@router.get("/{certificate_id}/challenge", response_model=ManualChallengeOut)
async def get_manual_challenge(
    certificate_id: uuid.UUID,
    db: DbDep,
    _ctx: ManageCtx,
) -> ManualChallengeOut:
    """The manual dns-01 record to publish, and how the last check went.

    The only response in the API that carries a challenge TXT value, and it is
    reachable only for a certificate whose ``dns_mode`` is ``manual``, in the
    caller's own organization. Read-only: no DNS is contacted.
    """
    certificate = await certificate_service.get_certificate(db, certificate_id)
    return _manual_out(await certificate_issuance.manual_challenge(db, certificate))


@router.post(
    "/{certificate_id}/challenge/confirm",
    response_model=ManualChallengeOut,
    status_code=status.HTTP_202_ACCEPTED,
)
async def confirm_manual_challenge(
    certificate_id: uuid.UUID,
    payload: ManualChallengeConfirmIn,
    request: Request,
    db: DbDep,
    ctx: ManageCtx,
) -> ManualChallengeOut:
    """Record that the record is published and recheck authoritative DNS **once**.

    ``202`` because a passing check hands a resume attempt to the worker rather than
    finishing issuance here. What comes back is the fresh observation, not a
    verdict: the challenge is validated when the CA says so, and a confirmation made
    while the record is absent simply reports that nothing was seen. Repeating it is
    idempotent — the first confirmation's timestamp is kept and the observation is
    run again.
    """
    certificate = await certificate_service.get_certificate(db, certificate_id)
    result = await certificate_issuance.confirm_manual_publication(
        db,
        certificate,
        ctx,
        refs=payload.references or None,
        request=request,
    )
    return _manual_out(result)


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
