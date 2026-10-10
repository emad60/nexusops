"""Domain lifecycle: create, prove control, lose control, re-prove, delete.

The state machine (domain-routing.md §4) is implemented here, and every write
path is explicit about its precondition so a concurrent request cannot leave the
row in a state that contradicts the rules:

``PENDING → VERIFYING → VERIFIED``; a sweep that stops seeing the proof TXT
moves ``VERIFIED → STALE`` for a 72-hour grace window, then ``UNVERIFIED``; a
changed apex NS set collapses straight to ``UNVERIFIED``; a failed attempt
increments ``attempt_count`` with a bounded backoff and lands in ``FAILED`` once
the budget is spent. ``UNVERIFIED``/``STALE``/``FAILED`` can all be re-verified.

Two invariants the rest of the system relies on:

* Only ``VERIFIED`` renders. :func:`is_serving` is the single predicate the
  renderer and the enable gate share, so "no proof ⇒ no live route" cannot drift
  between the two.
* A verification token is only ever returned while it is actionable. The read
  model builds ``verification`` from :func:`verification_instructions`, which
  returns ``None`` for a verified name.
"""

from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import Request
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext
from app.core.dnsname import (
    InvalidName,
    canonicalize_name,
    verification_record_name,
)
from app.core.errors import Conflict, NotFound, UnprocessableEntity
from app.core.logging import get_logger
from app.core.pagination import PageParams, paginate
from app.models import Domain, Project, Route
from app.models.enums import ActorType, DomainStatus, RouteConfigState
from app.schemas.domain import DomainCreate
from app.services import audit_service, dns_verifier, event_bus
from app.services.dns_verifier import TxtObservation, VerificationDecision

log = get_logger("nexusops.domains")

#: Prefix of the TXT value a user publishes. Documented, user-visible string.
TXT_VALUE_PREFIX = "nxs-verify="
#: Attempts allowed before a domain is parked in ``FAILED``.
MAX_VERIFY_ATTEMPTS = 8
#: Grace window after proof disappears before the name becomes UNVERIFIED.
STALE_GRACE = timedelta(hours=72)
#: Backoff between attempts, indexed by attempt number (seconds).
_BACKOFF_SECONDS = (30, 60, 120, 300, 600, 1800, 3600, 7200)
#: How long after a successful verification the next sweep re-checks the name.
REVERIFY_INTERVAL = timedelta(hours=1)
#: Statuses from which a route may be served. Shared by the renderer and the
#: enable gate so the two can never disagree.
SERVING_STATUSES = (DomainStatus.VERIFIED,)
#: Statuses for which the verification token is still actionable.
TOKEN_ACTIVE_STATUSES = (
    DomainStatus.PENDING,
    DomainStatus.VERIFYING,
    DomainStatus.STALE,
    DomainStatus.UNVERIFIED,
    DomainStatus.FAILED,
)


def _utcnow() -> datetime:
    return datetime.now(UTC)


def is_serving(domain: Domain) -> bool:
    """Whether a domain's routes may be rendered/enabled right now."""
    status = domain.status
    return (status.value if isinstance(status, DomainStatus) else str(status)) in {
        s.value for s in SERVING_STATUSES
    }


def mint_token() -> str:
    """A fresh, cryptographically random per-domain proof value."""
    return f"{TXT_VALUE_PREFIX}{secrets.token_urlsafe(24)}"


def verification_instructions(domain: Domain, *, include_token: bool) -> dict[str, Any] | None:
    """The exact record a domain manager must publish, or ``None``.

    ``None`` means "there is nothing left to publish": either the caller may not
    see the token or the name is verified and the token is no longer retrievable.
    """
    if not include_token:
        return None
    status = DomainStatus(domain.status)
    if status not in TOKEN_ACTIVE_STATUSES:
        return None
    return {
        "record_name": verification_record_name(domain.name),
        "record_type": "TXT",
        "record_value": domain.verification_token,
        "active": True,
    }


def _bad_name(exc: InvalidName) -> UnprocessableEntity:
    return UnprocessableEntity(exc.message, code=exc.code)


async def create_domain(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    payload: DomainCreate,
    request: Request | None = None,
) -> Domain:
    """Create a ``PENDING`` domain with a fresh token; return it with instructions."""
    try:
        name = canonicalize_name(payload.name, allow_wildcard=True)
    except InvalidName as exc:
        raise _bad_name(exc) from exc

    if payload.project_id is not None:
        project = await db.get(Project, payload.project_id)
        if project is None:
            # A project in another organization is invisible here (guard + RLS),
            # so this single check covers "does not exist" and "not yours"
            # without an existence oracle.
            raise NotFound("Project not found", code="PROJECT_NOT_FOUND")

    existing = await db.scalar(select(Domain.id).where(Domain.name == name))
    if existing is not None:
        raise Conflict(
            "This domain is already tracked in this organization",
            code="DOMAIN_EXISTS",
        )

    domain = Domain(
        project_id=payload.project_id,
        name=name,
        status=DomainStatus.PENDING,
        verification_token=mint_token(),
        ns_snapshot=[],
        attempt_count=0,
        next_check_at=_utcnow(),
    )
    db.add(domain)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise Conflict(
            "This domain is already tracked in this organization", code="DOMAIN_EXISTS"
        ) from exc

    actor_id, actor_type = _actor(ctx)
    await event_bus.publish(
        db,
        type="DOMAIN_CREATED",
        message=f"Domain {name} added, awaiting DNS verification",
        actor_id=actor_id,
        actor_type=actor_type,
        resource_type="domain",
        resource_id=str(domain.id),
        # No token, no record value: the event is org-scoped but readable by any
        # member with event.read, which is a wider audience than domain.manage.
        data={"name": name, "record_name": verification_record_name(name)},
    )
    await audit_service.record(
        db,
        ctx,
        action="domain.created",
        resource_type="domain",
        resource_id=domain.id,
        metadata={
            "name": name,
            "project_id": str(domain.project_id) if domain.project_id else None,
        },
        request=request,
    )
    return domain


def _actor(ctx: AuthContext | None) -> tuple[uuid.UUID | None, ActorType]:
    if ctx is None:
        return None, ActorType.SYSTEM
    try:
        return ctx.user_id, ActorType(ctx.actor_type)
    except ValueError:
        return ctx.user_id, ActorType.USER


async def get_domain(db: AsyncSession, domain_id: uuid.UUID) -> Domain:
    """One domain in the active organization, or a 404 identical to a random id."""
    domain = await db.get(Domain, domain_id)
    if domain is None:
        raise NotFound("Domain not found", code="DOMAIN_NOT_FOUND")
    return domain


async def list_domains(
    db: AsyncSession,
    params: PageParams,
    *,
    status: DomainStatus | None = None,
    project_id: uuid.UUID | None = None,
) -> tuple[list[Domain], int]:
    stmt = select(Domain)
    if status is not None:
        stmt = stmt.where(Domain.status == status)
    if project_id is not None:
        stmt = stmt.where(Domain.project_id == project_id)
    stmt = stmt.order_by(Domain.name.asc())
    return await paginate(db, stmt, params)


async def domain_route_counts(
    db: AsyncSession, domain_ids: list[uuid.UUID]
) -> dict[uuid.UUID, tuple[int, int]]:
    """``{domain_id: (total, enabled)}`` for a page of domains, in one query."""
    if not domain_ids:
        return {}
    rows = (
        await db.execute(
            select(
                Route.domain_id,
                func.count().label("total"),
                func.count().filter(Route.enabled.is_(True)).label("enabled"),
            )
            .where(Route.domain_id.in_(domain_ids))
            .group_by(Route.domain_id)
        )
    ).all()
    return {row[0]: (int(row[1]), int(row[2])) for row in rows}


async def delete_domain(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    domain_id: uuid.UUID,
    request: Request | None = None,
) -> None:
    """Delete a domain — refused while any enabled route still answers for it.

    An enabled route with no domain would render a fragment nobody can explain,
    so the operator disables (and the node applies) first. That ordering is also
    what keeps "delete" from being a way to bypass the apply pipeline.
    """
    domain = await get_domain(db, domain_id)
    enabled = await db.scalar(
        select(func.count()).select_from(Route).where(Route.domain_id == domain.id, Route.enabled)
    )
    if enabled:
        raise Conflict(
            "Disable this domain's routes before deleting it",
            code="DOMAIN_HAS_ENABLED_ROUTES",
        )
    name = domain.name
    await db.delete(domain)
    await db.flush()
    await event_bus.publish(
        db,
        type="DOMAIN_DELETED",
        message=f"Domain {name} removed",
        resource_type="domain",
        resource_id=str(domain.id),
        data={"name": name},
    )
    await audit_service.record(
        db,
        ctx,
        action="domain.deleted",
        resource_type="domain",
        resource_id=domain.id,
        metadata={"name": name},
        request=request,
    )


# --- verification lifecycle ---------------------------------------------------


async def request_verification(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    domain_id: uuid.UUID,
    request: Request | None = None,
) -> Domain:
    """Mark a domain VERIFYING and reset its attempt budget for a fresh check.

    Idempotent in the sense that matters: a second request for the same domain
    while a check is in flight simply resets the budget again, and the worker's
    own status guard refuses a stale result. The work is enqueued after commit by
    the API layer (see ``api/v1/domains.py``).
    """
    domain = await get_domain(db, domain_id)
    now = _utcnow()
    domain.status = DomainStatus.VERIFYING
    domain.attempt_count = 0
    domain.last_error = ""
    domain.next_check_at = now
    await db.flush()
    await audit_service.record(
        db,
        ctx,
        action="domain.verification_requested",
        resource_type="domain",
        resource_id=domain.id,
        metadata={"name": domain.name},
        request=request,
    )
    return domain


def next_attempt_at(attempt: int, *, now: datetime | None = None) -> datetime:
    """Bounded backoff for attempt number *attempt* (1-based)."""
    index = min(max(attempt - 1, 0), len(_BACKOFF_SECONDS) - 1)
    return (now or _utcnow()) + timedelta(seconds=_BACKOFF_SECONDS[index])


def _detail_for(decision: VerificationDecision) -> str:
    """A short, safe explanation. The expected token never appears in it."""
    return (decision.detail or "")[:480]


async def apply_decision(
    db: AsyncSession,
    domain: Domain,
    decision: VerificationDecision,
    *,
    observation: TxtObservation | None = None,
    trigger: str,
) -> DomainStatus:
    """Apply one verification outcome to the row — the transactional core.

    Must be called inside a session that can write the row (the worker uses the
    system scope, which is also what lets a successful verification flip another
    organization's competing ``VERIFIED`` row; see
    :func:`claim_verified_name`).

    Returns the status the row ended in.
    """
    del observation
    now = _utcnow()
    domain.last_checked_at = now
    domain.attempt_count = (domain.attempt_count or 0) + 1

    if decision.ok:
        domain.status = DomainStatus.VERIFIED
        domain.verified_at = now
        domain.proof_lost_at = None
        domain.stale_expires_at = None
        domain.last_error = ""
        domain.ns_snapshot = list(decision.ns_snapshot)
        domain.next_check_at = now + REVERIFY_INTERVAL
        await db.flush()
        return DomainStatus.VERIFIED

    # Failure. The fresh-user-verification path and the sweep path differ in how
    # long a name keeps being served:
    #  * a name that was serving and whose proof just disappeared gets the grace
    #    window (still excluded from the next render, but recoverable without
    #    the operator re-publishing anything);
    #  * a name that was never verified simply accumulates attempts.
    was_verified = domain.verified_at is not None and domain.status in (
        DomainStatus.VERIFIED,
        DomainStatus.STALE,
    )
    domain.last_error = _detail_for(decision)
    if decision.ns_changed:
        # A changed delegation is not a propagation hiccup: stop serving at once.
        domain.status = DomainStatus.UNVERIFIED
        domain.proof_lost_at = now
        domain.stale_expires_at = None
        domain.next_check_at = None
    elif was_verified and domain.status == DomainStatus.VERIFIED:
        domain.status = DomainStatus.STALE
        domain.proof_lost_at = now
        domain.stale_expires_at = now + STALE_GRACE
        domain.next_check_at = now + REVERIFY_INTERVAL
    elif domain.status == DomainStatus.STALE:
        expires = domain.stale_expires_at
        if expires is not None and expires <= now:
            domain.status = DomainStatus.UNVERIFIED
            domain.stale_expires_at = None
            domain.next_check_at = None
        else:
            domain.next_check_at = now + REVERIFY_INTERVAL
    elif domain.attempt_count >= MAX_VERIFY_ATTEMPTS:
        domain.status = DomainStatus.FAILED
        domain.next_check_at = None
    else:
        domain.status = DomainStatus.PENDING
        domain.next_check_at = next_attempt_at(domain.attempt_count, now=now)
    await db.flush()
    log.info(
        "domain_verification_failed",
        domain=str(domain.id),
        name=domain.name,
        reason=decision.reason,
        trigger=trigger,
        status=str(domain.status),
    )
    return DomainStatus(domain.status)


async def claim_verified_name(
    db: AsyncSession, *, name: str, owner_id: uuid.UUID
) -> list[uuid.UUID]:
    """Enforce one verified owner platform-wide.

    Runs under the worker's system scope, because the row it must flip belongs to
    a *different* organization: the name is verified here, so the earlier
    organization loses it immediately and its routes stop being rendered. Returns
    the flipped organizations so the caller can emit an event for each — the
    previous owner must learn why its traffic stopped.
    """
    rows = (
        await db.execute(
            select(Domain.id, Domain.org_id).where(
                func.lower(Domain.name) == name.lower(),
                Domain.status == DomainStatus.VERIFIED,
                Domain.id != owner_id,
            )
        )
    ).all()
    flipped: list[uuid.UUID] = []
    for domain_id, org_id in rows:
        await db.execute(
            # Explicit org predicate: system scope turns the guard off, and a
            # wide UPDATE here would be exactly the kind of statement the guard
            # exists to prevent.
            update(Domain)
            .where(Domain.id == domain_id, Domain.org_id == org_id)
            .values(
                status=DomainStatus.UNVERIFIED,
                proof_lost_at=_utcnow(),
                stale_expires_at=None,
                next_check_at=None,
                last_error="another organization verified this name",
            )
        )
        flipped.append(uuid.UUID(str(org_id)))
    if flipped:
        await db.flush()
    return flipped


async def record_reachability(
    db: AsyncSession,
    domain: Domain,
    *,
    node_addresses: list[str],
    resolve: Any | None = None,
) -> dict[str, Any]:
    """Best-effort DNS target check for the routing warning (§6).

    Never changes ``status``: ownership and reachability are independent facts,
    and a name that resolves elsewhere is a configuration problem to explain, not
    a reason to drop ownership. ``resolve`` is injectable so tests never touch
    the network.
    """
    hostname = domain.name[2:] if domain.name.startswith("*.") else domain.name
    resolver = resolve or dns_verifier.public_addresses
    addresses = list(resolver(hostname))
    expected = [addr for addr in node_addresses if addr]
    match: bool | None = None
    warning: str | None = None
    if not addresses:
        match = False
        warning = (
            f"{hostname} does not resolve to any address yet. Publish an A/AAAA record "
            "pointing at your node, or wait for DNS propagation."
        )
    elif expected:
        match = any(addr in expected for addr in addresses)
        if not match:
            warning = (
                f"{hostname} resolves to {', '.join(addresses)}, which is not this node's "
                f"address ({', '.join(expected)}). Check the A/AAAA record, or whether the "
                "node is behind NAT."
            )
    payload = {
        "hostname": hostname,
        "addresses": addresses,
        "expected_addresses": expected,
        "resolves_to_node": match,
        "checked_at": _utcnow().isoformat(),
        "warning": warning,
    }
    domain.dns_reachability = payload
    await db.flush()
    return payload


def route_config_state_for(domain_status: DomainStatus) -> RouteConfigState | None:
    """The state a domain flip forces on its routes, or ``None`` to leave them."""
    if domain_status in SERVING_STATUSES:
        return RouteConfigState.PENDING
    return RouteConfigState.STALE
