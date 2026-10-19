"""Certificate metadata: request, list, inspect, update. **No issuance.**

Phase 5.1 shipped the identity and lifecycle half of the certificate subsystem, so
everything in this module is about *what was asked for* and *how far the request
has got* — never about a key. Creating a certificate here records an intent: the
row, its first generation in ``PENDING``, an audit entry and an event. It does not
contact a CA and **cannot produce material**: 5.2.2 owned the material columns,
the guard CHECK that requires them in every post-issuance state, and the credential
a challenge will be published with — but nothing in this module writes any of
them, and no serializer here emits one.

What it does do since 5.3 is *hand the fresh generation to the worker*
(:func:`app.services.certificate_issuance.enqueue_generation`), deferred to after
its transaction commits. Recording a request and attempting it are deliberately
one call apart and one process apart: the ACME round trip and the DNS propagation
wait are exactly what a request thread must never hold a transaction through, and
the worker re-validates everything this module checked before it touches a CA.

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
from app.models import Certificate, CertificateGeneration, DnsProvider, Domain
from app.models.enums import (
    ActorType,
    CertificateChallengeType,
    CertificateDnsMode,
    CertificateGenerationState,
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
from app.services import audit_service, certificate_lifecycle, event_bus, route_certificate_service
from app.services.acme.directory import directory_for_url

log = get_logger("nexusops.certificates")

#: Challenge types this phase can serve. DNS-01 only: it is the sole challenge
#: that works for NAT-ed nodes and for wildcards (phase5-design.md §5.2).
SUPPORTED_CHALLENGE_TYPES: tuple[str, ...] = (CertificateChallengeType.DNS_01.value,)

#: Who may publish the challenge record. Both are supported; the caller must say
#: which, and the platform never infers it (phase5-design.md §5.3).
SUPPORTED_DNS_MODES: tuple[str, ...] = (
    CertificateDnsMode.AUTOMATED.value,
    CertificateDnsMode.MANUAL.value,
)


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


async def _resolve_dns_provider(db: AsyncSession, provider_id: uuid.UUID) -> DnsProvider:
    """The credential a challenge may be published with, or a 404.

    Same shape as the domain lookup, and for the same reason: a provider id from
    another tenant must be indistinguishable from a random one, because storing a
    foreign reference here would later publish this certificate's challenge with
    another organization's token — in a zone that organization allowlisted, which
    is precisely the write the allowlist exists to prevent. ``ON DELETE RESTRICT``
    on the column keeps the reference valid afterwards.

    A stored credential is *not* required to be currently verified: verification
    is a recorded result an operator re-runs, and refusing to bind an unverified
    credential would make "the token expired last week" block every rebind. The
    issuance path is where a credential that cannot authenticate stops an order.
    """
    provider = await db.get(DnsProvider, provider_id)
    if provider is None:
        raise NotFound("DNS provider not found", code="DNS_PROVIDER_NOT_FOUND")
    return provider


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


def _dns_mode(payload: CertificateCreate) -> CertificateDnsMode:
    """The requested publisher, refused unless it is one this phase implements.

    Explicit and required rather than derived from whether a credential was named:
    "no credential attached" is also the state of an automated request whose token
    has not been stored yet, and reading that as ``manual`` would move a customer's
    certificate into a workflow nobody chose — one where the platform stops and
    waits for a human who was never told.
    """
    requested = (payload.dns_mode or "").strip().lower()
    if requested not in SUPPORTED_DNS_MODES:
        raise UnprocessableEntity(
            f"Unsupported DNS mode '{payload.dns_mode}'. This phase publishes dns-01 "
            f"challenges as {' or '.join(SUPPORTED_DNS_MODES)} only.",
            code="CERTIFICATE_DNS_MODE_UNSUPPORTED",
        )
    mode = CertificateDnsMode(requested)
    if mode is CertificateDnsMode.MANUAL and payload.dns_provider_id is not None:
        # Two publishers on one certificate is a contradiction the database refuses
        # too; refusing it here is what turns it into a message instead of a 500.
        raise UnprocessableEntity(
            "A manual certificate has its challenge record published by the customer, so "
            "it cannot name a DNS credential. Leave dns_provider_id unset, or request an "
            "automated certificate instead.",
            code="CERTIFICATE_MANUAL_WITH_PROVIDER",
        )
    return mode


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
    dns_mode = _dns_mode(payload)
    domain = await _resolve_domain(db, payload.domain_id)
    dns_provider = (
        await _resolve_dns_provider(db, payload.dns_provider_id)
        if payload.dns_provider_id is not None
        else None
    )
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
        # NULL is a value here, not a missing one: it means "no credential chosen
        # yet". The request is still recorded, and issuance refuses it with a named
        # code until PATCH attaches one — which is honest, and keeps the create
        # path usable before the operator has stored their DNS token.
        dns_provider_id=dns_provider.id if dns_provider is not None else None,
        # Who publishes the challenge record. ``manual`` means the customer does,
        # and consequently that no credential is involved at all.
        dns_mode=dns_mode,
        suspended_at=None,
        suspension_reason="",
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
            "dns_mode": dns_mode.value,
            "generation": generation.generation,
            # The provider's name and id, never its credential: an audit entry may
            # say which credential was chosen and must never say what it holds.
            "dns_provider": dns_provider.name if dns_provider is not None else None,
            "dns_provider_source": ("certificate" if dns_provider is not None else None),
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
            "dns_mode": dns_mode.value,
            "state": str(generation.state),
        },
    )
    log.info(
        "certificate_requested",
        certificate=str(certificate.id),
        primary_cn=primary_cn,
        identifiers=len(sans) + 1,
    )
    # Imported here rather than at module scope: the issuance flow imports this
    # module (it reads the certificate a generation belongs to), so a top-level
    # import in either direction would be a cycle.
    from app.services.certificate_issuance import enqueue_generation

    enqueue_generation(db, generation.id)
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
    """Update ``auto_renew`` and the DNS credential override.

    Nothing here touches identifiers, status, expiry or generations — changing
    what a certificate *is* is a new generation, and issuing one is not something
    this phase does.

    The two fields read an explicit ``null`` differently on purpose. For
    ``auto_renew``, null is the absence of a value and is ignored; for
    ``dns_provider_id``, null *is* the value — it detaches the credential, which
    leaves the certificate unissuable until another is attached.
    """
    certificate = await get_certificate(db, certificate_id)
    data = payload.model_dump(exclude_unset=True)
    changed: list[str] = []

    if data.get("auto_renew") is not None:
        certificate.auto_renew = bool(data["auto_renew"])
        changed.append("auto_renew")

    # ``"dns_provider_id" in data`` rather than a truthiness test: clearing the
    # override sends null, and a null that is dropped would leave the old
    # credential bound while the caller believes it cleared it.
    if "dns_provider_id" in data:
        requested = data["dns_provider_id"]
        if requested is None:
            certificate.dns_provider_id = None
        else:
            if certificate.dns_mode == CertificateDnsMode.MANUAL:
                # The database's CHECK says the same thing; this is the version an
                # operator can act on. A manual certificate has no publisher to
                # point a credential at, and silently accepting one would leave the
                # row describing two workflows.
                raise UnprocessableEntity(
                    "This certificate publishes its challenge record by hand, so it cannot "
                    "name a DNS credential.",
                    code="CERTIFICATE_MANUAL_WITH_PROVIDER",
                )
            provider = await _resolve_dns_provider(db, requested)
            certificate.dns_provider_id = provider.id
        changed.append("dns_provider_id")

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
    half is checked twice, because two different things mean "issued" and either
    one alone would leave a hole now that material exists:

    * ``current_generation_id`` — the generation a new bind would reference; and
    * **any** generation in a material-bearing state, which is the stronger fact:
      a certificate whose current generation is NULL but which still holds a
      ``SUPERSEDED`` or ``REVOKED`` generation would cascade that row away, and
      deleting a private key the CA still considers valid is destruction of
      evidence rather than cleanup. Phase 5.1 could not tell the difference
      because every generation was pre-issuance by construction.

    The first half of the rule is checked here since the binding column arrived
    (Phase 5.4.1): a certificate a route still references is refused with
    ``CERTIFICATE_IN_USE``, and the composite FK's ``ON DELETE RESTRICT`` is the
    database backstop if this check is ever bypassed. Unbinding is an explicit
    act; deleting the certificate must not double as one.

    A pre-issuance generation carries no material, so removing a certificate that
    merely *asked* for one strands nothing — which is what keeps this endpoint
    useful.
    """
    certificate = await get_certificate(db, certificate_id)
    bound_routes = await route_certificate_service.bound_route_count(db, certificate.id)
    if bound_routes:
        raise Conflict(
            f"{bound_routes} route(s) are still bound to this certificate. Unbind them first.",
            code="CERTIFICATE_IN_USE",
        )
    if certificate.current_generation_id is not None:
        raise Conflict(
            "This certificate has an issued generation and cannot be deleted; revoke it first",
            code="CERTIFICATE_HAS_ISSUED_GENERATION",
        )
    issued_generation = await db.scalar(
        select(CertificateGeneration.generation)
        .where(
            CertificateGeneration.certificate_id == certificate.id,
            CertificateGeneration.state.in_(CertificateGenerationState.material_bearing()),
        )
        .order_by(CertificateGeneration.generation.asc())
        .limit(1)
    )
    if issued_generation is not None:
        raise Conflict(
            "This certificate has a generation that carries key material and cannot be "
            "deleted; revoke it first",
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
    # Which authority answered for this generation, and whether a browser would
    # trust a certificate from it. Derived from the URL stored on the row rather
    # than from the current configuration: a generation issued at staging stays
    # labelled staging after the platform is pointed at production, and an
    # unrecognised URL reads as not publicly trusted rather than as trusted
    # because it is unreadable.
    directory = directory_for_url(generation.directory_url)
    payload.directory = directory
    payload.publicly_trusted = bool(directory and directory.is_publicly_trusted)
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
