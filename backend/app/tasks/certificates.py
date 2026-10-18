"""Certificate issuance tasks: one worker per generation, plus the due sweep.

The split is the one Phase 4's deployments use, for the same reasons: an issuance
is a long conversation (a Certificate Authority round trip, a DNS write in someone
else's zone, a propagation wait) and no request thread may hold a transaction
through it, so the API enqueues a task keyed by the generation row and a worker is
the only thing that runs the flow.

Neither task here decides anything. Every guard, transition and write belongs to
:mod:`app.services.certificate_issuance`, so a dispatch that arrives late, twice,
or for a row another worker already finished is a refusal the service records —
not a second code path that could disagree with the first. What the sweep adds is
*timeliness*: it is what turns "this generation is due an attempt" and "this
generation's worker died holding a live state" into a queued task.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import and_, or_, select

from app.core.logging import get_logger
from app.tasks._util import org_for, org_session, run_async, sweep_session
from app.tasks.celery_app import app

logger = get_logger(__name__)

#: How many generations one sweep tick dispatches. Bounded because the work each
#: dispatch starts is expensive and rate-limited at the CA: a backlog has to be
#: worked through at a controlled rate, not as a burst of ACME orders.
DISPATCH_BATCH = 50


@app.task(name="nx.issue_certificate", soft_time_limit=540, time_limit=590)
def issue_certificate(generation_id: str) -> dict[str, str]:
    """Run at most one issuance attempt for one generation.

    The id is the only thing in the payload — no names, no provider credentials,
    no key material — and the row is the unit of idempotency: see
    :func:`app.services.certificate_issuance.issue_generation`, which refuses a
    duplicate dispatch, recovers one whose worker died, and honors the backoff.

    The session's ``commit`` is handed to the service as its checkpoint, so what
    an attempt has learned survives a worker killed mid-flow: which state it
    reached, which challenge records it created for the customer's zone, and
    whether it was attempted at all.
    """

    async def _run() -> dict[str, str]:
        from app.models import CertificateGeneration
        from app.services import certificate_issuance

        try:
            # Celery serializes the argument as a string; a hand-enqueued task
            # can carry anything, and an unparseable id must not become a
            # database error inside the tenancy lookup.
            generation_uuid = uuid.UUID(generation_id)
        except (AttributeError, TypeError, ValueError):
            logger.warning("certificate_generation_bad_id", generation_id=str(generation_id))
            return {"generation_id": str(generation_id), "status": "rejected", "code": "BAD_ID"}

        # Which tenant owns the row is what defines the scope, so it is resolved
        # before any scope exists — and it is resolved (not assumed) because a
        # worker's process serves every tenant in sequence.
        org_id = await org_for(CertificateGeneration, generation_uuid)
        if org_id is None:
            # Deleted between the enqueue and the run, or the enqueue raced a
            # rollback. Nothing to attempt and nobody to tell.
            logger.warning(
                "certificate_generation_org_unresolved", generation_id=str(generation_uuid)
            )
            return {
                "generation_id": str(generation_uuid),
                "status": "skipped",
                "code": "GENERATION_MISSING",
            }

        async with org_session(org_id) as db:
            generation = await db.get(CertificateGeneration, generation_uuid)
            if generation is None:
                return {
                    "generation_id": str(generation_uuid),
                    "status": "skipped",
                    "code": "GENERATION_MISSING",
                }
            attempt = await certificate_issuance.issue_generation(
                db, generation, checkpoint=db.commit
            )
            return {
                "generation_id": str(generation_uuid),
                "status": "issued" if attempt.ok else "not_issued",
                "state": attempt.state.value,
                "attempt": str(attempt.attempt),
                "code": attempt.code,
            }

    result = run_async(_run())
    logger.info("certificate_issue_task_finished", **result)
    return result


@app.task(name="nx.sweep_certificates", soft_time_limit=120, time_limit=150)
def sweep_certificates() -> dict[str, int]:
    """Dispatch every generation that is due an attempt — including abandoned ones.

    Two shapes are dispatched, and neither of them is a decision this task makes
    about whether an attempt is *allowed* (the service still refuses whatever it
    must):

    * **Due** — a ``FAILED`` generation whose backoff has elapsed, or one that has
      never been attempted (``PENDING``). A generation that has spent its attempt
      budget is excluded here as well as refused there, so a dead end is not
      redispatched once a minute forever.
    * **Abandoned** — a live state (``ORDERING`` … ``VALIDATING``) whose recorded
      attempt started longer ago than the order TTL: the worker that began it
      died. This is the recovery the design's stuck-state sweep asks for, and it
      is deliberately the *same* predicate the service uses (``attempt_in_flight``
      with the same TTL), read from the same document, so the sweep cannot
      consider a generation abandoned while the service considers it running.

    Everything the sweep writes is nothing: it reads rows, dispatches tasks and
    lets the worker record what happened. That is what keeps one writer in charge
    of a generation's state.
    """

    async def _run() -> dict[str, int]:
        from app.models import CertificateGeneration
        from app.models.enums import CertificateGenerationState
        from app.services import certificate_lifecycle, certificate_order

        now = datetime.now(UTC)
        ttl = float(_order_ttl_seconds())
        counts = {"candidates": 0, "dispatched": 0, "in_flight": 0, "awaiting_manual": 0}

        due = or_(
            CertificateGeneration.next_attempt_at.is_(None),
            CertificateGeneration.next_attempt_at <= now,
        )
        # Attemptable *and* due. The failed branch carries the budget bound so an
        # exhausted generation is not redispatched on every tick; the constant is
        # the lifecycle module's, not a second copy of the number.
        attemptable = or_(
            and_(
                CertificateGeneration.state.in_(CertificateGenerationState.live_pre_issuance()),
                due,
            ),
            and_(
                CertificateGeneration.state == CertificateGenerationState.FAILED,
                CertificateGeneration.attempt_count < certificate_lifecycle.MAX_ISSUE_ATTEMPTS,
                due,
            ),
        )

        # Generations exist in every tenant, so the sweep itself is cross-tenant;
        # each dispatch is attributed to its own generation's organization by the
        # task, which resolves the scope before it touches the row.
        async with sweep_session("task.sweep_certificates") as db:
            candidates = (
                (
                    await db.execute(
                        select(CertificateGeneration)
                        .where(attemptable)
                        # A live state carries no deadline, so ordering by it puts
                        # the abandoned ones first: recovering a lost worker is
                        # worth more than the next scheduled retry.
                        .order_by(
                            CertificateGeneration.next_attempt_at.asc().nullsfirst(),
                            CertificateGeneration.updated_at.asc(),
                        )
                        .limit(DISPATCH_BATCH)
                    )
                )
                .scalars()
                .all()
            )
            counts["candidates"] = len(candidates)

            for generation in candidates:
                document = certificate_order.load(generation)
                if certificate_order.attempt_in_flight(document, now=now, ttl_seconds=ttl):
                    # A worker is genuinely working on it. Dispatching anyway would
                    # only buy a refusal, once per tick, per running attempt.
                    counts["in_flight"] += 1
                    continue
                if (
                    certificate_lifecycle.coerce_state(generation.state)
                    is CertificateGenerationState.AWAITING_MANUAL
                    and not certificate_order.manual_ready(document)
                ):
                    # The next step is the customer's, not the platform's. A
                    # dispatch here would be a no-op the service refuses with
                    # ``CERTIFICATE_AWAITING_MANUAL`` — once per tick, forever —
                    # and the fresh attempt it idled would be indistinguishable
                    # from a lost worker that genuinely needs recovering. The
                    # confirmation endpoint is what makes a waiting generation
                    # dispatchable, so that is the only path that can unstick it.
                    counts["awaiting_manual"] += 1
                    continue
                try:
                    issue_certificate.delay(str(generation.id))
                except Exception:
                    logger.error(
                        "certificate_dispatch_failed",
                        generation_id=str(generation.id),
                        certificate_id=str(generation.certificate_id),
                    )
                    # The broker is unreachable; the next tick tries the whole
                    # batch again, and nothing has been written.
                    break
                counts["dispatched"] += 1
                logger.info(
                    "certificate_dispatched",
                    generation_id=str(generation.id),
                    certificate_id=str(generation.certificate_id),
                    state=str(generation.state),
                    attempt_count=generation.attempt_count,
                )

        return counts

    return run_async(_run())


def _order_ttl_seconds() -> int:
    """The order TTL from settings — the same one the service ages attempts with."""
    from app.core.config import get_settings

    return get_settings().certificate_order_ttl_seconds
