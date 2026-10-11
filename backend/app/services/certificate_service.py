"""Certificate metadata: request, list, inspect, update. **No issuance.**

Phase 5.1 is the identity and lifecycle half of the certificate subsystem, so
everything in this module is about *what was asked for* and *how far the request
has got* — never about a key. Creating a certificate here records an intent: the
row, its first generation in ``PENDING``, an audit entry and an event. It does not
contact a CA, does not queue a worker, and cannot produce material, because a
material-bearing generation state does not exist yet in this phase's schema.

Rules enforced here rather than in the API layer, so a worker-initiated call
obeys them identically:

* the domain belongs to the active organization (a foreign id is a 404 — never a
  403 that confirms the name exists elsewhere);
* a certificate is only requested for a **verified** name. The platform can only
  complete DNS-01 for a name this organization has proved control of, and
  ``docs/phase5-design.md`` §3.1 calls ``domain_id`` "the verified name this
  certificate is for" — so the check is the same ``is_serving`` predicate the
  renderer uses, not a new one;
* every identifier on the order is allowed under that domain
  (:func:`identifier_allowed_for_domain`), so an organization cannot ask the
  platform to mint a certificate for a name it merely tracks;
* the challenge type is one this phase can actually serve (``dns-01`` only), and
  the key algorithm is fixed rather than client-chosen;
* one certificate row per name per organization — a renewal adds a *generation*.

Nothing here sets ``current_generation_id``: it is the generation a new bind
should reference, and it stays NULL until a generation carries material. A
request is therefore never reported as issued — see
:mod:`app.services.certificate_lifecycle`.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TypedDict

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext
from app.core.dnsname import InvalidName, apex_of, canonicalize_name, hostname_is_covered
from app.core.errors import Conflict, NotFound, UnprocessableEntity
from app.core.logging import get_logger
from app.core.pagination import PageParams, paginate
from app.models import Certificate, CertificateGeneration, Domain
from app.models.enums import (
    ActorType,
    CertificateChallengeType,
    CertificateKeyAlgorithm,
    CertificateStatus,
    DomainStatus,
)
from app.schemas.certificate import (
    CertificateCreate,
    CertificateGenerationOut,
    CertificateOut,
    CertificateUpdate,
)
from app.services import audit_service, certificate_lifecycle, event_bus

log = get_logger("nexusops.certificates")

#: Challenge types this phase can serve. DNS-01 only: it is the sole challenge
#: that works for NAT-ed nodes and for wildcards (phase5-design.md §5.2).
SUPPORTED_CHALLENGE_TYPES: tuple[str, ...] = (CertificateChallengeType.DNS_01.value,)

#: Only ``auto_renew`` is updatable, so this is the whole list of mutable fields.
_MUTABLE_FIELDS = ("auto_renew",)


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _actor(ctx: AuthContext | None) -> tuple[uuid.UUID | None, ActorType]:
    if ctx is None:
        return None, ActorType.SYSTEM
    try:
        return ctx.user_id, ActorType(ctx.actor_type)
    except ValueError:
        return ctx.user_id, ActorType.USER


def identifier_allowed_for_domain(identifier: str, domain_name: str) -> bool:
    """Whether *identifier* may ride a certificate requested for *domain_name*.

    The rule is the platform's route-coverage rule — the domain's own name, a
    single-label subdomain of it, or (for a wildcard domain) exactly one label
    below it — **plus one deliberate extension**: a non-wildcard domain also
    authorizes its own wildcard form (``example.com`` → ``*.example.com``).

    That extension is not a loosening of route coverage, it is the shape of
    DNS-01 wildcard issuance: proving control of ``example.com``'s TXT record is
    how ``*.example.com`` is issued, and ``core.dnsname`` refuses the pair
    (``hostname_is_covered("*.example.com", "example.com")`` is False) because a
    *route* must never claim a wildcard name space its Domain row did not prove.
    The two rules stay separate on purpose, so a wildcard route cannot follow the
    certificate rule's precedent.
    """
    if identifier == domain_name:
        return True
    if hostname_is_covered(identifier, domain_name):
        return True
    return identifier == f"*.{apex_of(domain_name)}"


async def _resolve_domain(db: AsyncSession, domain_id: uuid.UUID) -> Domain:
    """The domain, or the same 404 a random uuid gets (no existence oracle)."""
    domain = await db.get(Domain, domain_id)
    if domain is None:
        raise NotFound("Domain not found", code="DOMAIN_NOT_FOUND")
    return domain


def _canonical_identifiers(payload: CertificateCreate) -> tuple[str, list[str]]:
    """``(primary_cn, sans)`` from the request's identifier list, canonicalised."""
    try:
        identifiers = [
            canonicalize_name(value, allow_wildcard=True) for value in payload.identifiers
        ]
    except InvalidName as exc:
        raise UnprocessableEntity(exc.message, code=exc.code) from exc

    primary_cn, *rest = identifiers
    sans: list[str] = []
    for candidate in rest:
        if candidate == primary_cn:
            raise UnprocessableEntity(
                "The primary name appears more than once; list each identifier once",
                code="CERTIFICATE_DUPLICATE_IDENTIFIER",
            )
        if candidate not in sans:
            sans.append(candidate)
    return primary_cn, sans


def _challenge_type(payload: CertificateCreate) -> CertificateChallengeType:
    requested = (payload.challenge_type or "").strip().lower()
    if requested not in SUPPORTED_CHALLENGE_TYPES:
        raise UnprocessableEntity(
            f"Unsupported challenge type '{payload.challenge_type}'. This phase issues with "
            f"{', '.join(SUPPORTED_CHALLENGE_TYPES)} only — HTTP-01 is not offered yet.",
            code="CHALLENGE_TYPE_UNSUPPORTED",
        )
    return CertificateChallengeType(requested)


async def create_certificate(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    payload: CertificateCreate,
    request: Request | None = None,
) -> Certificate:
    """Record a certificate request and its first generation, atomically.

    The certificate row and its ``PENDING`` generation are written in one
    transaction: a certificate with no generation would be a request nobody can
    act on, and a generation with no certificate cannot exist (its FK says so).
    """
    primary_cn, sans = _canonical_identifiers(payload)
    challenge_type = _challenge_type(payload)
    domain = await _resolve_domain(db, payload.domain_id)
    if DomainStatus(domain.status) is not DomainStatus.VERIFIED:
        raise Conflict(
            f"Domain '{domain.name}' is {DomainStatus(domain.status).value.lower()}. A "
            "certificate can only be requested for a name this organization has verified.",
            code="DOMAIN_NOT_VERIFIED",
        )
    for identifier in (primary_cn, *sans):
        if not identifier_allowed_for_domain(identifier, domain.name):
            raise UnprocessableEntity(
                f"'{identifier}' is not covered by the domain '{domain.name}'. A certificate "
                "may use the domain name itself, a single-label subdomain of it, or the "
                "domain's wildcard form.",
                code="CERTIFICATE_NAME_NOT_COVERED",
            )

    existing = await db.scalar(select(Certificate.id).where(Certificate.primary_cn == primary_cn))
    if existing is not None:
        raise Conflict(
            "A certificate for this name already exists in this organization. Renew it, or "
            "delete the existing request first.",
            code="CERTIFICATE_EXISTS",
        )

    now = _utcnow()
    certificate = Certificate(
        domain_id=domain.id,
        primary_cn=primary_cn,
        sans=sans,
        status=CertificateStatus.PENDING,
        current_generation_id=None,
        challenge_type=challenge_type,
        auto_renew=payload.auto_renew,
        # Fixed by the platform, never by the caller: the delivery path in 5.4
        # implements exactly this key type.
        key_algorithm=CertificateKeyAlgorithm.ECDSA_P256,
        expires_at=None,
        last_error="",
    )
    db.add(certificate)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise Conflict(
            "A certificate for this name already exists in this organization. Renew it, or "
            "delete the existing request first.",
            code="CERTIFICATE_EXISTS",
        ) from exc

    generation = CertificateGeneration(
        certificate_id=certificate.id,
        generation=1,
        # The one state a fresh request may hold: nothing has been ordered yet.
        state=certificate_lifecycle.assert_pre_issuance(certificate_lifecycle.INITIAL_STATE),
        order_state={},
        last_error="",
        # Due immediately: the issuance slice picks the request up rather than
        # waiting out a backoff it has not earned.
        next_attempt_at=now,
        attempt_count=0,
    )
    db.add(generation)
    await db.flush()

    await audit_service.record(
        db,
        ctx,
        action="certificate.created",
        resource_type="certificate",
        resource_id=certificate.id,
        metadata={
            "domain": domain.name,
            "primary_cn": primary_cn,
            "identifiers": [primary_cn, *sans],
            "challenge_type": challenge_type.value,
            "generation": generation.generation,
        },
        request=request,
    )
    actor_id, actor_type = _actor(ctx)
    await event_bus.publish(
        db,
        type="CERTIFICATE_REQUESTED",
        message=f"Certificate requested for {primary_cn} — nothing has been issued yet",
        actor_id=actor_id,
        actor_type=actor_type,
        resource_type="certificate",
        resource_id=str(certificate.id),
        data={
            "primary_cn": primary_cn,
            "sans": sans,
            "challenge_type": challenge_type.value,
            "state": str(generation.state),
        },
    )
    log.info(
        "certificate_requested",
        certificate=str(certificate.id),
        primary_cn=primary_cn,
        identifiers=len(sans) + 1,
    )
    return certificate


async def get_certificate(db: AsyncSession, certificate_id: uuid.UUID) -> Certificate:
    certificate = await db.get(Certificate, certificate_id)
    if certificate is None:
        raise NotFound("Certificate not found", code="CERTIFICATE_NOT_FOUND")
    return certificate


async def list_certificates(
    db: AsyncSession,
    params: PageParams,
    *,
    status: CertificateStatus | None = None,
    domain_id: uuid.UUID | None = None,
) -> tuple[list[Certificate], int]:
    stmt = select(Certificate)
    if status is not None:
        stmt = stmt.where(Certificate.status == status)
    if domain_id is not None:
        stmt = stmt.where(Certificate.domain_id == domain_id)
    stmt = stmt.order_by(Certificate.primary_cn.asc())
    return await paginate(db, stmt, params)


async def update_certificate(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    certificate_id: uuid.UUID,
    payload: CertificateUpdate,
    request: Request | None = None,
) -> Certificate:
    """Update the one mutable preference: whether renewal should run.

    Nothing here touches identifiers, status, expiry or generations — changing
    what a certificate *is* is a new generation, and issuing one is not something
    this phase does.
    """
    certificate = await get_certificate(db, certificate_id)
    data = payload.model_dump(exclude_unset=True)
    # An explicit ``null`` is not a value for a boolean preference: it is the
    # absence of one, and must not be recorded as a change.
    changed = sorted(field for field in _MUTABLE_FIELDS if data.get(field) is not None)
    if "auto_renew" in changed:
        certificate.auto_renew = bool(data["auto_renew"])
    await db.flush()
    await audit_service.record(
        db,
        ctx,
        action="certificate.updated",
        resource_type="certificate",
        resource_id=certificate.id,
        metadata={"fields": changed, "primary_cn": certificate.primary_cn},
        request=request,
    )
    return certificate


async def delete_certificate(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    certificate_id: uuid.UUID,
    request: Request | None = None,
) -> None:
    """Delete a certificate request and its generations.

    The design's deletion rule (phase5-design.md §3.1) is that a certificate row
    is removed only when it is orphaned *and* no generation is issued. The second
    half is what is checked here, through ``current_generation_id``: that pointer
    only ever names an issued generation — it is what a new bind would reference —
    so a non-NULL value means material exists and the certificate is not merely a
    request.

    The first half (no ``routes.certificate_id`` references it) has nothing to
    check yet: that column arrives with the binding slice (5.5), and the FK there
    is ``ON DELETE RESTRICT``, so the database will refuse a delete that a bound
    route makes invalid rather than this function guessing.

    Generations are removed with their certificate (``ON DELETE CASCADE``); a
    pre-issuance generation carries no material, so nothing is stranded by this.
    """
    certificate = await get_certificate(db, certificate_id)
    if certificate.current_generation_id is not None:
        raise Conflict(
            "This certificate has an issued generation and cannot be deleted; revoke it first",
            code="CERTIFICATE_HAS_ISSUED_GENERATION",
        )
    primary_cn = certificate.primary_cn
    await db.delete(certificate)
    await db.flush()
    actor_id, actor_type = _actor(ctx)
    await event_bus.publish(
        db,
        type="CERTIFICATE_DELETED",
        message=f"Certificate request for {primary_cn} deleted",
        actor_id=actor_id,
        actor_type=actor_type,
        resource_type="certificate",
        resource_id=str(certificate.id),
        data={"primary_cn": primary_cn},
    )
    await audit_service.record(
        db,
        ctx,
        action="certificate.deleted",
        resource_type="certificate",
        resource_id=certificate.id,
        metadata={"primary_cn": primary_cn},
        request=request,
    )


async def latest_generation(
    db: AsyncSession, certificate_id: uuid.UUID
) -> CertificateGeneration | None:
    """The newest generation of *certificate_id*, whatever state it is in."""
    stmt = (
        select(CertificateGeneration)
        .where(CertificateGeneration.certificate_id == certificate_id)
        .order_by(CertificateGeneration.generation.desc())
        .limit(1)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def latest_generations(
    db: AsyncSession, certificate_ids: list[uuid.UUID]
) -> dict[uuid.UUID, CertificateGeneration]:
    """``{certificate_id: newest generation}`` for a page, in one query."""
    if not certificate_ids:
        return {}
    stmt = (
        select(CertificateGeneration)
        .where(CertificateGeneration.certificate_id.in_(certificate_ids))
        .distinct(CertificateGeneration.certificate_id)
        .order_by(
            CertificateGeneration.certificate_id,
            CertificateGeneration.generation.desc(),
        )
    )
    rows = (await db.execute(stmt)).scalars().all()
    return {row.certificate_id: row for row in rows}


async def all_generations(
    db: AsyncSession, certificate_id: uuid.UUID
) -> list[CertificateGeneration]:
    """Every generation of one certificate, newest first (detail view)."""
    stmt = (
        select(CertificateGeneration)
        .where(CertificateGeneration.certificate_id == certificate_id)
        .order_by(CertificateGeneration.generation.desc())
    )
    return list((await db.execute(stmt)).scalars().all())


class CertificateMetadata(TypedDict):
    """The owning domains of a page of certificates, keyed by the ids they carry."""

    domains: dict[uuid.UUID, Domain]
    latest: dict[uuid.UUID, CertificateGeneration]


async def relevant_metadata(
    db: AsyncSession, certificates: list[Certificate]
) -> CertificateMetadata:
    """Domains and newest generations for a certificate list, in two queries."""
    if not certificates:
        return {"domains": {}, "latest": {}}
    domain_ids = {certificate.domain_id for certificate in certificates}
    domains = {
        row.id: row
        for row in (await db.execute(select(Domain).where(Domain.id.in_(domain_ids))))
        .scalars()
        .all()
    }
    latest = await latest_generations(db, [certificate.id for certificate in certificates])
    return {"domains": domains, "latest": latest}


def derive_status(
    certificate: Certificate, generation: CertificateGeneration | None
) -> tuple[CertificateStatus, str]:
    """The certificate's status and its explanation, derived from *generation*.

    Derivation rather than storage is what keeps the two honest: a request that
    has not been issued cannot report ``ISSUED``, because no pre-issuance state
    maps to it (``certificate_lifecycle.certificate_status_for``).
    """
    if generation is None:
        # Structurally unreachable: creation writes the certificate and its first
        # generation in one transaction. Reported as a request-with-no-attempt
        # rather than guessed at.
        return CertificateStatus(certificate.status), "No issuance has been attempted yet"
    return (
        certificate_lifecycle.certificate_status_for(generation.state),
        certificate_lifecycle.status_detail_for(generation.state, generation.attempt_count),
    )


def serialize_generation(generation: CertificateGeneration) -> CertificateGenerationOut:
    """One generation's read model, with the derived lifecycle flags filled in."""
    payload = CertificateGenerationOut.model_validate(generation)
    payload.retryable = certificate_lifecycle.is_retryable(
        generation.state, generation.attempt_count
    )
    payload.terminal = certificate_lifecycle.is_terminal(generation.state, generation.attempt_count)
    payload.status_detail = certificate_lifecycle.status_detail_for(
        generation.state, generation.attempt_count
    )
    return payload


def serialize_certificate(
    certificate: Certificate,
    *,
    domain: Domain | None,
    generation: CertificateGeneration | None,
) -> CertificateOut:
    """The certificate read model: approved metadata only, derived status.

    ``latest_generation`` is the newest attempt — what ``status`` is derived
    from. ``current_generation_id`` is a different thing (the generation a bind
    should use) and is NULL until an issuance exists, which is why ``issued``
    stays False for every Phase 5.1 certificate.
    """
    status, detail = derive_status(certificate, generation)
    payload = CertificateOut.model_validate(certificate)
    payload.domain_name = domain.name if domain is not None else None
    payload.domain_status = (
        str(getattr(domain.status, "value", domain.status)) if domain is not None else None
    )
    payload.status = status
    payload.status_detail = detail
    payload.latest_generation = serialize_generation(generation) if generation is not None else None
    payload.issued = certificate.current_generation_id is not None
    return payload
