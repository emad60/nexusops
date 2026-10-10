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
* **A lost name must reach the nodes that were serving it.** Releasing a claim
  changes a *different* organization's routes, so the nodes that have to drop them
  are discovered inside that same system-scoped step — the last moment they are
  visible to the worker at all — and each one is then told to re-render and apply
  inside its **own** organization. Discovering the work and doing it are separate
  scopes on purpose: the discovery is cross-tenant lifecycle handling, the apply
  is ordinary per-tenant work.
* **Reconciliation repairs, it does not re-ask.** The route sweep calls
  :func:`app.services.proxy_service.reconcile_node`, which polls a converged node
  for its fingerprint and queues exactly one apply when the desired bundle and the
  node's live one differ. A difference is never reported as repaired until an
  agent says the apply succeeded.
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
    released_nodes: list[uuid.UUID] = []
    if decision.ok:
        flipped, released_nodes = await _release_competing_claim(name=name, owner_id=domain_id)

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
    # ...and every node the *previous* owner was serving the name from. Without
    # this pass a released organization keeps answering for a name it no longer
    # controls: its routes stop being rendered, but the configuration already on
    # the node keeps carrying them until something asks for a new one.
    for node_id in dict.fromkeys(released_nodes):
        await _apply_for_node(node_id, reason="domain_claim_released")

    return {
        "status": str(status.value),
        "reason": decision.reason,
        "flipped": str(len(flipped)),
        "released_nodes": str(len(set(released_nodes))),
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


async def _release_competing_claim(
    *, name: str, owner_id: uuid.UUID
) -> tuple[list[uuid.UUID], list[uuid.UUID]]:
    """Move another organization's ``VERIFIED`` claim on *name* to ``UNVERIFIED``.

    Its own transaction, before the new claim is written, so the platform-wide
    unique index is never asked to allow two verified owners. Both the previous
    owner's audit trail and its event stream learn what happened and why — a
    silent loss of a name would be indistinguishable from a bug.

    Returns ``(released_org_ids, affected_node_ids)``: the organizations that lost
    the name, and every node still serving one of their routes for it. The node
    ids are gathered **here**, under the system scope, because this is the only
    scope that can see another organization's routes at all — once the claim is
    released, an ordinary tenant scope has no way to find them. The routes are
    also marked unresolved immediately, so the previous owner's view is honest
    from the first moment instead of claiming a route is live until the next
    sweep touches it.

    Nothing in here applies configuration: each node is re-rendered and applied
    later, inside its own organization, by :func:`_apply_for_node`.
    """
    from app.models.enums import EventLevel
    from app.services import audit_service, event_bus, proxy_service

    # Why the route is being pulled, in the words the route row carries. The
    # wording is deliberately about the *request*: at this moment no node has been
    # told anything yet, and a node that never takes the apply must not read as
    # "removed" (``proxy_service.removal_confirmed_detail`` is the other half, and
    # only an agent's applied result can produce it).
    pulled_reason = "this name is now verified by another organization"

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
        affected_nodes: list[uuid.UUID] = []
        for domain_id, org_id in rows:
            # Discovery first, while the routes are still visible to this scope.
            routes = (
                (
                    await db.execute(
                        select(Route).where(
                            Route.domain_id == domain_id,
                            # Explicit tenant predicate: system scope turns the guard
                            # off, and a wide statement here is exactly what the guard
                            # exists to prevent.
                            Route.org_id == org_id,
                            Route.enabled.is_(True),
                        )
                    )
                )
                .scalars()
                .all()
            )
            for route in routes:
                await proxy_service.mark_removal_requested(db, route=route, reason=pulled_reason)
                affected_nodes.append(uuid.UUID(str(route.node_id)))
                await event_bus.publish(
                    db,
                    type="ROUTE_REMOVAL_REQUESTED",
                    level=EventLevel.WARNING,
                    org_id=org_id,
                    message=(
                        f"Route {route.hostname}{route.path}: "
                        f"{proxy_service.removal_requested_detail(pulled_reason)}"
                    ),
                    resource_type="route",
                    resource_id=str(route.id),
                    data={
                        "hostname": route.hostname,
                        "path": route.path,
                        "reason": "claimed_by_another_organization",
                    },
                )

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
                metadata={
                    # Names, counts and ids only: nothing about the organization
                    # that claimed the name is visible to the organization that
                    # lost it.
                    "name": name,
                    "reason": "verified by another organization",
                    "routes_pulled": len(routes),
                    "nodes_affected": len({uuid.UUID(str(route.node_id)) for route in routes}),
                    # The routes left this organization's desired configuration; each
                    # node still has to confirm it stopped serving them. Saying which
                    # half this is keeps the audit trail from reading like a removal
                    # that already happened.
                    "removal": "requested",
                },
            )
            await event_bus.publish(
                db,
                type="DOMAIN_UNVERIFIED",
                level=EventLevel.WARNING,
                message=(
                    f"Domain {name} is now verified by another organization; its routes "
                    "are out of this organization's desired configuration, and every "
                    "node that serves them still has to confirm the removal"
                ),
                org_id=org_id,
                resource_type="domain",
                resource_id=str(domain_id),
                data={
                    "name": name,
                    "reason": "claimed_by_another_organization",
                    "removal": "requested",
                },
            )
            released.append(uuid.UUID(str(org_id)))
        await db.flush()
        return released, affected_nodes


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

    A domain flip must never fail because a node went offline mid-sweep, so a
    refusal is logged rather than raised. That is safe precisely because the
    work is retried by the route sweep (``proxy_service.reconcile_node``), and
    because the affected routes already read as unresolved
    — the control plane never claims a node stopped serving a route it has not
    been told about.

    The node's own organization is resolved first and the apply runs inside it,
    so the cross-tenant discovery that produced *node_id* never leaks into the
    work itself.
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

    One bounded step per node, taken by
    :func:`app.services.proxy_service.reconcile_node`: a converged node is asked
    for a fresh fingerprint on an interval, and a node whose live bundle is not
    the desired one gets exactly one ``nginx.apply`` queued. That is the whole
    difference between a reconciler and a poll — ask a node for its status while
    its configuration is known to be wrong and it will keep answering the same
    way forever, because it is not misreporting: it is running the wrong tree.

    Every bound lives in the reconciler, and the per-outcome counters are
    returned so a tick that queues nothing is distinguishable from one that
    could not reach a node.
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
                    outcome = await proxy_service.reconcile_node(db, node=node)
            except Conflict as exc:
                # A named refusal (offline, listener conflict, render refused) is
                # a deferred tick, not a failure: the routes stay unresolved and
                # the next tick tries again.
                logger.info("route_sweep_deferred", node=str(node_id), code=exc.code)
                counts[proxy_service.RECONCILE_DEFERRED] = (
                    counts.get(proxy_service.RECONCILE_DEFERRED, 0) + 1
                )
                continue
            except Exception as exc:
                logger.warning(
                    "route_sweep_failed", node=str(node_id), error=exc.__class__.__name__
                )
                continue
            counts[outcome] = counts.get(outcome, 0) + 1
            if outcome == proxy_service.RECONCILE_STATUS_REQUESTED:
                counts["status_requests"] += 1
            elif outcome == proxy_service.RECONCILE_RECOVERY_QUEUED:
                counts["reapplies"] += 1
        return counts

    counts = run_async(_run())
    # Logged whenever anything happened other than a converged node: a tick that
    # repaired, deferred or blocked is the one worth reading in a worker log.
    if counts["status_requests"] or counts["reapplies"] or counts.get("deferred"):
        logger.info("route_sweep_done", **counts)
    return counts


__all__ = ["sweep_domains", "sweep_routes", "verify_domain_task"]
