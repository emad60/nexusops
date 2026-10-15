"""DNS credential endpoints: store, list, inspect, verify, rotate, delete.

Both codenames are the certificate ones: the design deliberately gives
``dns_providers`` no codename of its own in v1 (phase5-design.md §10.3.2 L4) —
managing a credential *is* managing the inputs to a certificate request — so reads
ride ``certificate.read`` and every mutation rides ``certificate.manage``, resolved
from the caller's membership in the active organization.

The phase's boundary is visible in what these routes return: metadata only. There
is no endpoint that reads a credential back, none that returns the ciphertext, and
none that reveals the plaintext under any circumstance — verification is a
*recorded result* on the row (``verified_at``/``verify_error``/``scopes``), never a
response that echoes what was sent.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext, require_permission
from app.core.db import get_session
from app.core.pagination import Page, PageParams, page_params
from app.models.enums import DnsProviderKind
from app.schemas.dns_provider import DnsProviderCreate, DnsProviderOut, DnsProviderUpdate
from app.services import dns_provider_service

router = APIRouter(prefix="/dns-providers", tags=["dns-providers"])

DbDep = Annotated[AsyncSession, Depends(get_session)]
ReadCtx = Annotated[AuthContext, Depends(require_permission("certificate.read"))]
ManageCtx = Annotated[AuthContext, Depends(require_permission("certificate.manage"))]


@router.get("", response_model=Page[DnsProviderOut])
async def list_dns_providers(
    db: DbDep,
    _ctx: ReadCtx,
    params: Annotated[PageParams, Depends(page_params)],
    q: Annotated[str | None, Query(max_length=120)] = None,
    kind: Annotated[DnsProviderKind | None, Query()] = None,
) -> Page[DnsProviderOut]:
    """List stored credentials. **No credential value is in any row of the page.**"""
    rows, total = await dns_provider_service.list_dns_providers(db, params, q=q, kind=kind)
    return Page[DnsProviderOut](
        items=[DnsProviderOut.model_validate(dns_provider_service.detail(row)) for row in rows],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@router.post("", response_model=DnsProviderOut, status_code=status.HTTP_201_CREATED)
async def create_dns_provider(
    payload: DnsProviderCreate,
    request: Request,
    db: DbDep,
    ctx: ManageCtx,
) -> DnsProviderOut:
    """Store a DNS credential and its zone allowlist, verifying it first.

    A credential that fails verification is still stored, with the failure recorded
    on the row: the operator's next step is to read ``verify_error`` and fix the
    token, not to submit the form again (which would discard the attempt's context).
    """
    provider = await dns_provider_service.create_dns_provider(
        db, ctx, payload=payload, request=request
    )
    return DnsProviderOut.model_validate(dns_provider_service.detail(provider))


@router.get("/{provider_id}", response_model=DnsProviderOut)
async def get_dns_provider(
    provider_id: uuid.UUID,
    db: DbDep,
    _ctx: ReadCtx,
) -> DnsProviderOut:
    """One credential's metadata. A foreign id is the same 404 a random one gets."""
    return DnsProviderOut.model_validate(
        await dns_provider_service.provider_detail(db, provider_id)
    )


@router.patch("/{provider_id}", response_model=DnsProviderOut)
async def update_dns_provider(
    provider_id: uuid.UUID,
    payload: DnsProviderUpdate,
    request: Request,
    db: DbDep,
    ctx: ManageCtx,
) -> DnsProviderOut:
    """Update metadata, or **rotate** the credential by sending a new one."""
    provider = await dns_provider_service.update_dns_provider(
        db, ctx, provider_id=provider_id, payload=payload, request=request
    )
    return DnsProviderOut.model_validate(dns_provider_service.detail(provider))


@router.post("/{provider_id}/verify", response_model=DnsProviderOut)
async def verify_dns_provider(
    provider_id: uuid.UUID,
    request: Request,
    db: DbDep,
    ctx: ManageCtx,
) -> DnsProviderOut:
    """Re-run the provider's ``verify_creds()`` and record the outcome.

    The one endpoint that proves the stored credential can still be *used*, and it
    answers with metadata: a live/expired verdict, the zones the token can see, and
    a bounded error if it cannot authenticate.
    """
    provider = await dns_provider_service.verify_dns_provider(
        db, ctx, provider_id=provider_id, request=request
    )
    return DnsProviderOut.model_validate(dns_provider_service.detail(provider))


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dns_provider(
    provider_id: uuid.UUID,
    request: Request,
    db: DbDep,
    ctx: ManageCtx,
) -> None:
    """Delete a credential. Refused while a certificate still names it."""
    await dns_provider_service.delete_dns_provider(
        db, ctx, provider_id=provider_id, request=request
    )
