"""Explicit certificate ↔ route binding — association only (Phase 5.4.1).

This module owns the one thing Phase 5.4's delivery targeting needs and Phase 5.5
does not exist yet to provide: a persisted, tenant-consistent answer to *which
certificate is this route allowed to serve*. It deliberately does none of the
things activation does:

* it never writes ``routes.scheme`` (still a closed ``'http'`` CHECK),
* it never renders a TLS server block or touches a node,
* it never reads key material — eligibility is decided from certificate metadata
  (identifiers, current generation's state, validity window, suspension).

Two rules shape the whole module:

**The binding is a claim, not a proof.** Every consumer must re-evaluate it from
authoritative rows. A binding can become ineligible without its own row changing:
the domain can lose verification, the certificate can be suspended, the route can
be disabled, the hostname can be moved off the certificate. None of those silently
rewrite or drop the association — they make :func:`evaluate` say so, and delivery
(the later slice) refuses on that answer. That is the only way "the association is
still there" never gets mistaken for "the certificate may still be served".

**Nothing is bound implicitly.** ``certificate_id`` is not accepted on route
create/update payloads and not accepted on delivery requests; the two operations
here are the only writers, and both run under the route's row lock so two
conflicting binds serialize instead of racing.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext
from app.core.errors import Conflict, NotFound
from app.core.logging import get_logger
from app.models import Certificate, CertificateGeneration, Domain, Route
from app.models.enums import (
    ActorType,
    CertificateGenerationState,
    CertificateStatus,
    DomainStatus,
)
from app.services import audit_service, event_bus

log = get_logger("nexusops.route_certificates")

#: States in which a certificate may be *newly* bound. Everything else (pending,
#: failed, expired, revoked, revocation pending) describes material that either
#: does not exist or must not be served.
BINDABLE_STATUSES = (CertificateStatus.ISSUED,)


class BindingState:
    """The three answers a route's association can give.

    Plain constants rather than an enum because this is a *derived* read model:
    the stored fact is ``routes.certificate_id`` plus authoritative rows, and a
    fourth member would invite callers to persist it.
    """

    UNBOUND = "UNBOUND"
    BOUND = "BOUND"
    INELIGIBLE = "INELIGIBLE"


@dataclass(frozen=True)
class BindingEvaluation:
    """What the stored association means *right now*.

    ``eligible`` is the only field delivery may gate on; ``code`` and ``detail``
    explain a refusal without exposing anything beyond the route's own metadata.
    """

    state: str
    eligible: bool
    code: str
    detail: str
    certificate_id: uuid.UUID | None = None
    generation: int | None = None
    fingerprint: str | None = None


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _actor(ctx: AuthContext | None) -> tuple[uuid.UUID | None, ActorType]:
    if ctx is None:
        return None, ActorType.SYSTEM
    try:
        return ctx.user_id, ActorType(ctx.actor_type)
    except ValueError:
        return ctx.user_id, ActorType.USER


def certificate_identifiers(certificate: Certificate) -> list[str]:
    """Every name the certificate covers: the primary CN plus its SANs."""
    identifiers = [certificate.primary_cn]
    for name in certificate.sans or []:
        if name not in identifiers:
            identifiers.append(name)
    return identifiers


def identifier_covers_hostname(identifier: str, hostname: str) -> bool:
    """Whether one certificate identifier covers a route hostname.

    Exact match, plus the single-label rule DNS itself uses for a wildcard SAN:

    * ``*.example.com`` covers ``api.example.com`` — exactly one label, never the
      apex (``example.com``) and never ``a.b.example.com``;
    * a non-wildcard identifier covers only itself;
    * a **wildcard route hostname** (``*.example.com``) is covered only by the
      identical wildcard identifier, because the route answers the whole
      one-label name space and a narrower SAN would leave part of it unserved.

    Comparisons are label-wise; ``endswith`` on the raw strings would let
    ``notexample.com`` match ``example.com``.
    """
    if not identifier or not hostname:
        return False
    if identifier == hostname:
        return True
    if not identifier.startswith("*."):
        return False
    if hostname.startswith("*."):
        return False
    base = identifier[2:]
    if not base or not hostname.endswith("." + base):
        return False
    prefix = hostname[: -(len(base) + 1)]
    return bool(prefix) and "." not in prefix


def certificate_covers_hostname(certificate: Certificate, hostname: str) -> bool:
    """Whether any identifier on *certificate* covers *hostname*."""
    return any(
        identifier_covers_hostname(identifier, hostname)
        for identifier in certificate_identifiers(certificate)
    )


async def _load_route_for_update(db: AsyncSession, route_id: uuid.UUID) -> Route:
    """The route row, locked for the duration of a bind/unbind.

    ``FOR UPDATE`` is what turns two conflicting binds into "one wins, the other
    reads the winner and gets a named conflict" instead of last-writer-wins. It
    is taken on the route only: the certificate is read, never written here, and
    taking a second lock would add a lock-order rule for no benefit.
    """
    route = (
        await db.execute(select(Route).where(Route.id == route_id).with_for_update())
    ).scalar_one_or_none()
    if route is None:
        raise NotFound("Route not found", code="ROUTE_NOT_FOUND")
    return route


async def _resolve_domain(db: AsyncSession, domain_id: uuid.UUID) -> Domain:
    domain = await db.get(Domain, domain_id)
    if domain is None:
        raise NotFound("Domain not found", code="DOMAIN_NOT_FOUND")
    return domain


def _expired(certificate: Certificate, generation: CertificateGeneration | None) -> bool:
    deadline = certificate.expires_at or (generation.not_after if generation else None)
    return deadline is not None and deadline <= _utcnow()


async def _rejection(
    db: AsyncSession, *, route: Route, certificate: Certificate
) -> tuple[str, str] | None:
    """Why *certificate* cannot be bound to *route* right now, or ``None``.

    Ordered from the outside in: domain ownership, then the certificate's own
    lifecycle, then name coverage. The returned pair is ``(code, message)`` and is
    used both by the write path (raised) and the read path (reported), so a bind
    refusal and a later ineligibility can never disagree about the rule.
    """
    domain = await _resolve_domain(db, route.domain_id)
    if DomainStatus(domain.status) is not DomainStatus.VERIFIED:
        return (
            "DOMAIN_NOT_VERIFIED",
            f"Domain '{domain.name}' is {DomainStatus(domain.status).value.lower()}, so its "
            "routes cannot bind a certificate. Verify ownership first.",
        )

    generation: CertificateGeneration | None = None
    if certificate.current_generation_id is not None:
        generation = await db.get(CertificateGeneration, certificate.current_generation_id)

    if certificate.suspended_at is not None:
        return (
            "CERTIFICATE_SUSPENDED",
            f"Certificate for '{certificate.primary_cn}' is suspended "
            f"({certificate.suspension_reason or 'no reason recorded'}) and cannot be bound.",
        )
    if certificate.status not in BINDABLE_STATUSES:
        return (
            "CERTIFICATE_NOT_ISSUED",
            f"Certificate for '{certificate.primary_cn}' is "
            f"{CertificateStatus(certificate.status).value.lower()}; only an issued "
            "certificate can be bound to a route.",
        )
    if generation is None or CertificateGenerationState(generation.state) not in (
        CertificateGenerationState.ISSUED,
    ):
        return (
            "CERTIFICATE_NOT_ISSUED",
            "The certificate has no current issued generation, so it has no material to "
            "serve. Only an issued certificate can be bound to a route.",
        )
    if _expired(certificate, generation):
        return (
            "CERTIFICATE_EXPIRED",
            f"Certificate for '{certificate.primary_cn}' is past its validity window and "
            "cannot be bound until it is renewed.",
        )
    if not certificate_covers_hostname(certificate, route.hostname):
        return (
            "CERTIFICATE_HOSTNAME_NOT_COVERED",
            f"Certificate for '{certificate.primary_cn}' does not cover "
            f"'{route.hostname}'. Its identifiers are: "
            f"{', '.join(certificate_identifiers(certificate))}.",
        )
    return None


async def bind_certificate(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    route_id: uuid.UUID,
    certificate_id: uuid.UUID,
    request: Request | None = None,
) -> Route:
    """Associate *certificate* with *route* after validating current state.

    Refusals are deliberately explicit rather than idempotent in the dangerous
    direction: re-binding the same certificate succeeds (nothing changed), but
    replacing a *different* binding requires an unbind first, so a stale UI or a
    racing request can never silently retarget a route at a certificate nobody
    reviewed.
    """
    route = await _load_route_for_update(db, route_id)

    # Tenant boundary: a foreign certificate is the same 404 a random uuid gets,
    # so this endpoint is not an existence oracle. The composite FK is the second
    # line of defence, not the first.
    certificate = await db.get(Certificate, certificate_id)
    if certificate is None:
        raise NotFound("Certificate not found", code="CERTIFICATE_NOT_FOUND")

    if route.certificate_id == certificate.id:
        return route
    if route.certificate_id is not None:
        raise Conflict(
            "This route is already bound to a different certificate. Unbind it first.",
            code="ROUTE_CERTIFICATE_CONFLICT",
        )

    rejection = await _rejection(db, route=route, certificate=certificate)
    if rejection is not None:
        code, message = rejection
        raise Conflict(message, code=code)

    route.certificate_id = certificate.id
    await db.flush()

    actor_id, actor_type = _actor(ctx)
    await event_bus.publish(
        db,
        type="ROUTE_CERTIFICATE_BOUND",
        message=(
            f"Certificate for {certificate.primary_cn} bound to "
            f"{route.hostname}{route.path} (association only)"
        ),
        actor_id=actor_id,
        actor_type=actor_type,
        resource_type="route",
        resource_id=str(route.id),
        data={
            "hostname": route.hostname,
            "path": route.path,
            "certificate_id": str(certificate.id),
            "primary_cn": certificate.primary_cn,
        },
    )
    await audit_service.record(
        db,
        ctx,
        action="route.certificate_bound",
        resource_type="route",
        resource_id=route.id,
        metadata={
            "hostname": route.hostname,
            "path": route.path,
            "certificate_id": str(certificate.id),
            "primary_cn": certificate.primary_cn,
        },
        request=request,
    )
    log.info(
        "route_certificate_bound",
        route=str(route.id),
        certificate=str(certificate.id),
        hostname=route.hostname,
    )
    return route


async def unbind_certificate(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    route_id: uuid.UUID,
    request: Request | None = None,
) -> Route:
    """Remove the association. Idempotent: unbinding an unbound route is a no-op.

    The route keeps serving HTTP either way — this column has never been read by
    the renderer — and no certificate is deleted or suspended by an unbind.
    """
    route = await _load_route_for_update(db, route_id)
    previous = route.certificate_id
    if previous is None:
        return route

    route.certificate_id = None
    await db.flush()

    actor_id, actor_type = _actor(ctx)
    await event_bus.publish(
        db,
        type="ROUTE_CERTIFICATE_UNBOUND",
        message=(
            f"Certificate binding removed from {route.hostname}{route.path} "
            "(the certificate itself is unchanged)"
        ),
        actor_id=actor_id,
        actor_type=actor_type,
        resource_type="route",
        resource_id=str(route.id),
        data={
            "hostname": route.hostname,
            "path": route.path,
            "certificate_id": str(previous),
        },
    )
    await audit_service.record(
        db,
        ctx,
        action="route.certificate_unbound",
        resource_type="route",
        resource_id=route.id,
        metadata={
            "hostname": route.hostname,
            "path": route.path,
            "certificate_id": str(previous),
        },
        request=request,
    )
    log.info(
        "route_certificate_unbound",
        route=str(route.id),
        certificate=str(previous),
        hostname=route.hostname,
    )
    return route


async def evaluate(db: AsyncSession, route: Route) -> BindingEvaluation:
    """Re-derive what the stored binding means from authoritative state.

    This is the function delivery (Phase 5.4) must call; it never trusts the
    association alone. It also applies the one rule that has no row of its own —
    ``routes.enabled`` — because §7.4's target set requires it, and nothing may
    receive certificate material for a route that is not being served.

    A route that has never been bound reports ``UNBOUND``; a bound route whose
    certificate disappeared (which the RESTRICT FK makes impossible) reports
    ``INELIGIBLE`` rather than pretending it is unbound, so a broken invariant is
    visible instead of silent.
    """
    if route.certificate_id is None:
        return BindingEvaluation(
            state=BindingState.UNBOUND,
            eligible=False,
            code="ROUTE_CERTIFICATE_UNBOUND",
            detail="No certificate is associated with this route.",
        )

    certificate = await db.get(Certificate, route.certificate_id)
    if certificate is None:
        return BindingEvaluation(
            state=BindingState.INELIGIBLE,
            eligible=False,
            code="CERTIFICATE_NOT_FOUND",
            detail="The associated certificate no longer exists.",
        )

    generation: CertificateGeneration | None = None
    if certificate.current_generation_id is not None:
        generation = await db.get(CertificateGeneration, certificate.current_generation_id)
    generation_number = generation.generation if generation is not None else None
    fingerprint = generation.fingerprint if generation is not None else None

    if not route.enabled:
        return BindingEvaluation(
            state=BindingState.INELIGIBLE,
            eligible=False,
            code="ROUTE_DISABLED",
            detail=(
                "The route is disabled; its node is not part of the certificate's "
                "delivery target set."
            ),
            certificate_id=certificate.id,
            generation=generation_number,
            fingerprint=fingerprint,
        )

    rejection = await _rejection(db, route=route, certificate=certificate)
    if rejection is not None:
        code, message = rejection
        return BindingEvaluation(
            state=BindingState.INELIGIBLE,
            eligible=False,
            code=code,
            detail=message,
            certificate_id=certificate.id,
            generation=generation_number,
            fingerprint=fingerprint,
        )

    return BindingEvaluation(
        state=BindingState.BOUND,
        eligible=True,
        code="ROUTE_CERTIFICATE_ELIGIBLE",
        detail=(
            "The route is enabled, its domain is verified, and the certificate covers its hostname."
        ),
        certificate_id=certificate.id,
        generation=generation_number,
        fingerprint=fingerprint,
    )


async def bound_route_count(db: AsyncSession, certificate_id: uuid.UUID) -> int:
    """How many routes still reference *certificate* (the deletion guard)."""
    count = await db.scalar(
        select(func.count()).select_from(Route).where(Route.certificate_id == certificate_id)
    )
    return int(count or 0)
