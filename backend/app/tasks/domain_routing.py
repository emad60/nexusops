"""Domain verification and routing sweeps.

Two properties shape this module:

* **A worker holds one scope at a time.** The claim that discovers work runs
  under ``sweep_session`` (system scope, allowlisted and logged), and every row is
  then touched inside ``org_session(row.org_id)``. A single session never spans
  two organizations.
* **Releasing a competing claim is its own transaction.** When an organization
  verifies a name another organization currently holds ``VERIFIED``, the previous
  holder is flipped to ``UNVERIFIED`` *first*, in a system-scoped step that is
  audited and announced to that organization; the new owner is written after.
  The window between the two steps can only ever leave the name served by
  *nobody* — never by two owners — because the partial unique index would refuse
  the second claim otherwise.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update

from app.core.errors import Conflict
from app.core.logging import get_logger
from app.models import Domain, Route, Server
from app.models.enums import DomainStatus
from app.tasks._util import org_for, org_session, run_async, sweep_session
from app.tasks.celery_app import app

logger = get_logger(__name__)

#: Domains one sweep tick may process. The sweep is a background correctness net,
#: not a high-throughput pipeline; a large backlog simply takes a few ticks.
SWEEP_BATCH = 100
#: Nodes one route sweep may process per tick.
ROUTE_SWEEP_BATCH = 100


def _utcnow() -> datetime:
    return datetime.now(UTC)


@app.task(name="nx.verify_domain", soft_time_limit=120, time_limit=150)
def verify_domain_task(domain_id: str) -> dict[str, str]:
    """Verify one domain by name (user-triggered)."""
    try:
        parsed = uuid.UUID(str(domain_id))
    except (ValueError, TypeError):
        return {"status": "invalid"}
    return run_async(_verify(parsed, trigger="user"))


async def _verify(domain_id: uuid.UUID, *, trigger: str) -> dict[str, str]:
    """Observe DNS, decide, and apply the outcome for one domain."""
    from app.services.dns_verifier import decide, observe

    org_id = await org_for(Domain, domain_id)
    if org_id is None:
        return {"status": "missing"}

    # Read the inputs under the owning organization, then release the session
    # before the network call: a DNS timeout must not hold a transaction open.
    async with org_session(org_id) as db:
        domain = await db.get(Domain, domain_id)
        if domain is None:
            return {"status": "missing"}
        name = domain.name
        token = domain.verification_token
        snapshot = tuple(domain.ns_snapshot or ())
        was_verified = DomainStatus(domain.status) in (
            DomainStatus.VERIFIED,
            DomainStatus.STALE,
        )

    observation = observe(name)
    decision = decide(
        observation,
        expected_token=token,
        ns_snapshot=snapshot,
        # A sweep re-checks an existing proof, so a changed delegation invalidates
        # it. A user-requested verification is a deliberate re-proof and accepts
        # the new delegation.
        require_snapshot_match=(trigger == "sweep"),
    )

    flipped: list[uuid.UUID] = []
    if decision.ok:
        flipped = await _release_competing_claim(name=name, owner_id=domain_id)

    async with org_session(org_id) as db:
        domain = await db.get(Domain, domain_id)
        if domain is None:
            return {"status": "missing"}
        from app.services import audit_service, domain_service

        status = await domain_service.apply_decision(
            db, domain, decision, observation=observation, trigger=trigger
        )
        await _announce(
            db, domain=domain, status=status, decision=decision, was_verified=was_verified
        )
        await audit_service.record(
            db,
            None,
            action=_audit_action(status, decision, was_verified),
            resource_type="domain",
            resource_id=domain.id,
            org_id=org_id,
            actor_email="system:verify_domain",
            metadata={
                "trigger": trigger,
                "reason": decision.reason,
                "status": status.value,
                "nameservers": len(observation.nameservers),
            },
        )
        if status is DomainStatus.VERIFIED:
            await _record_reachability(db, domain=domain, org_id=org_id)
        affected_nodes = await _affected_node_ids(db, domain_id=domain.id)

    for node_id in affected_nodes:
        await _apply_for_node(node_id, reason=f"domain_{status.value.lower()}")

    return {
        "status": str(status.value),
        "reason": decision.reason,
        "flipped": str(len(flipped)),
    }


def _audit_action(status: DomainStatus, decision, was_verified: bool) -> str:
    if status is DomainStatus.VERIFIED:
        return "domain.reverified" if was_verified else "domain.verified"
    if status is DomainStatus.STALE:
        return "domain.stale"
    if status is DomainStatus.UNVERIFIED:
        return "domain.ns_changed" if decision.ns_changed else "domain.unverified"
    if status is DomainStatus.FAILED:
        return "domain.verification_failed"
    return "domain.verification_attempted"


async def _announce(
    db, *, domain: Domain, status: DomainStatus, decision, was_verified: bool
) -> None:
    """Publish the sanitized, org-scoped event for a state change.

    Payloads carry ids, the name and the state — never the verification token, the
    observed TXT values or any DNS frame.
    """
    from app.services import event_bus

    if status is DomainStatus.VERIFIED:
        event_type, level, message = (
            "DOMAIN_VERIFIED",
            "INFO",
            f"Domain {domain.name} verified",
        )
    elif status is DomainStatus.STALE:
        event_type, level, message = (
            "DOMAIN_STALE",
            "WARNING",
            f"Domain {domain.name} lost its proof record; routes are pulled",
        )
    elif status is DomainStatus.UNVERIFIED:
        event_type, level, message = (
            "DOMAIN_UNVERIFIED",
            "WARNING",
            f"Domain {domain.name} is no longer verified; routes are pulled",
        )
    elif status is DomainStatus.FAILED:
        event_type, level, message = (
            "DOMAIN_UNVERIFIED",
            "WARNING",
            f"Verification for {domain.name} failed permanently",
        )
    else:
        return
    from app.models.enums import EventLevel

    await event_bus.publish(
        db,
        type=event_type,
        level=EventLevel(level),
        message=message,
        org_id=domain.org_id,
        resource_type="domain",
        resource_id=str(domain.id),
        data={"name": domain.name, "status": status.value, "reason": decision.reason},
    )


async def _release_competing_claim(*, name: str, owner_id: uuid.UUID) -> list[uuid.UUID]:
    """Move another organization's ``VERIFIED`` claim on *name* to ``UNVERIFIED``.

    Its own transaction, before the new claim is written, so the platform-wide
    unique index is never asked to allow two verified owners. Both the previous
    owner's audit trail and its event stream learn what happened and why — a
    silent loss of a name would be indistinguishable from a bug.
    """
    from app.models.enums import EventLevel
    from app.services import audit_service, event_bus

    async with sweep_session("task.verify_domain.release_competing_claim") as db:
        rows = (
            await db.execute(
                select(Domain.id, Domain.org_id).where(
                    Domain.id != owner_id,
                    Domain.status == DomainStatus.VERIFIED,
                    Domain.name == name,
                )
            )
        ).all()
        released: list[uuid.UUID] = []
        for domain_id, org_id in rows:
            await db.execute(
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
            await audit_service.record(
                db,
                None,
                action="domain.claim_released",
                resource_type="domain",
                resource_id=domain_id,
                org_id=org_id,
                actor_email="system:verify_domain",
                metadata={"name": name, "reason": "verified by another organization"},
            )
            await event_bus.publish(
                db,
                type="DOMAIN_UNVERIFIED",
                level=EventLevel.WARNING,
                message=(
                    f"Domain {name} is now verified by another organization; its routes "
                    "were pulled from this organization"
                ),
                org_id=org_id,
                resource_type="domain",
                resource_id=str(domain_id),
                data={"name": name, "reason": "claimed_by_another_organization"},
            )
            released.append(uuid.UUID(str(org_id)))
        return released


async def _record_reachability(db, *, domain: Domain, org_id: uuid.UUID) -> None:
    """Best-effort DNS-target warning for the domain's serving nodes."""
    from app.services import domain_service

    node_ids = await _affected_node_ids(db, domain_id=domain.id)
    if not node_ids:
        return
    addresses: list[str] = []
    rows = (
        (await db.execute(select(Server.ip_address).where(Server.id.in_(node_ids)))).scalars().all()
    )
    addresses = [value for value in rows if value]
    payload = await domain_service.record_reachability(db, domain, node_addresses=addresses)
    if payload.get("warning"):
        logger.info("domain_reachability_warning", domain=str(domain.id), name=domain.name)


async def _affected_node_ids(db, *, domain_id: uuid.UUID) -> list[uuid.UUID]:
    rows = (
        (await db.execute(select(Route.node_id).where(Route.domain_id == domain_id).distinct()))
        .scalars()
        .all()
    )
    return [uuid.UUID(str(row)) for row in rows]


async def _apply_for_node(node_id: uuid.UUID, *, reason: str) -> None:
    """Push a fresh bundle to one node, tolerating anything that blocks it.

    A domain flip must never fail because a node went offline mid-sweep: the
    route sweep will retry, and the route's state already records why it is not
    being served.
    """
    from app.services import proxy_service

    org_id = await org_for(Server, node_id)
    if org_id is None:
        return
    try:
        async with org_session(org_id) as db:
            node = await db.get(Server, node_id)
            if node is None:
                return
            await proxy_service.enqueue_apply(db, node=node, reason=reason)
    except Conflict as exc:
        logger.info("route_apply_deferred", node=str(node_id), code=exc.code)
    except Exception as exc:
        logger.warning("route_apply_failed", node=str(node_id), error=exc.__class__.__name__)


@app.task(name="nx.sweep_domains", soft_time_limit=300, time_limit=330)
def sweep_domains() -> dict[str, int]:
    """Re-prove control of every domain whose next check is due.

    Covers three cases with one mechanism: the hourly re-check of a verified name,
    the short backoff retries of a pending name, and the grace expiry of a stale
    one (a stale row's ``next_check_at`` keeps being set, so it keeps being
    re-checked until the grace window closes and it flips to ``UNVERIFIED``).
    """

    async def _claim() -> list[uuid.UUID]:
        now = _utcnow()
        async with sweep_session("task.sweep_domains.claim") as db:
            rows = (
                (
                    await db.execute(
                        select(Domain.id)
                        .where(
                            Domain.status.in_(
                                (
                                    DomainStatus.VERIFIED,
                                    DomainStatus.STALE,
                                    DomainStatus.PENDING,
                                )
                            ),
                            Domain.next_check_at.is_not(None),
                            Domain.next_check_at <= now,
                        )
                        .order_by(Domain.next_check_at.asc())
                        .limit(SWEEP_BATCH)
                    )
                )
                .scalars()
                .all()
            )
        return [uuid.UUID(str(row)) for row in rows]

    async def _run() -> dict[str, int]:
        ids = await _claim()
        counts = {"checked": 0, "verified": 0, "unverified": 0, "stale": 0}
        for domain_id in ids:
            try:
                outcome = await _verify(domain_id, trigger="sweep")
            except Exception as exc:
                logger.warning(
                    "domain_sweep_row_failed", domain=str(domain_id), error=exc.__class__.__name__
                )
                continue
            status = outcome.get("status", "")
            if status == "missing":
                continue
            counts["checked"] += 1
            if status == DomainStatus.VERIFIED.value:
                counts["verified"] += 1
            elif status == DomainStatus.UNVERIFIED.value:
                counts["unverified"] += 1
            elif status == DomainStatus.STALE.value:
                counts["stale"] += 1
        return counts

    counts = run_async(_run())
    if counts["checked"]:
        logger.info("domain_sweep_done", **counts)
    return counts


@app.task(name="nx.sweep_routes", soft_time_limit=240, time_limit=280)
def sweep_routes() -> dict[str, int]:
    """Keep every routed node's live configuration matching the desired bundle.

    Two mechanisms, both bounded: ask a node that has an applied bundle for its
    live fingerprint (``nginx.status``), and re-apply where the node has routes
    the control plane believes are applied but whose bundle is not the current
    desired one. ``nginx.apply`` is only queued when none is in flight, so a node
    that stays offline accumulates a single pending operation rather than a queue
    of duplicates.
    """
    from app.services import proxy_service

    async def _candidates() -> list[tuple[uuid.UUID, uuid.UUID]]:
        async with sweep_session("task.sweep_routes.claim") as db:
            rows = (
                await db.execute(
                    select(Server.id, Server.org_id)
                    .where(Server.id.in_(select(Route.node_id).where(Route.enabled.is_(True))))
                    .limit(ROUTE_SWEEP_BATCH)
                )
            ).all()
        return [(uuid.UUID(str(row[0])), uuid.UUID(str(row[1]))) for row in rows]

    async def _run() -> dict[str, int]:
        counts = {"nodes": 0, "status_requests": 0, "reapplies": 0}
        for node_id, org_id in await _candidates():
            counts["nodes"] += 1
            try:
                async with org_session(org_id) as db:
                    node = await db.get(Server, node_id)
                    if node is None:
                        continue
                    state = node.proxy_state or {}
                    if state.get("applied_bundle_id"):
                        if await proxy_service.request_status(db, node=node) is not None:
                            counts["status_requests"] += 1
                        continue
                    if await proxy_service.enqueue_apply(
                        db, node=node, reason="sweep_missing_apply"
                    ):
                        counts["reapplies"] += 1
            except Conflict as exc:
                logger.info("route_sweep_deferred", node=str(node_id), code=exc.code)
            except Exception as exc:
                logger.warning(
                    "route_sweep_failed", node=str(node_id), error=exc.__class__.__name__
                )
        return counts

    counts = run_async(_run())
    if counts["status_requests"] or counts["reapplies"]:
        logger.info("route_sweep_done", **counts)
    return counts


__all__ = ["sweep_domains", "sweep_routes", "verify_domain_task"]
