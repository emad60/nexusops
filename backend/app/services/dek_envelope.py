"""The organization DEK envelope: one wrapped data key per organization.

Every organization owns one Fernet DEK, stored **wrapped** in
``organization_dek_envelopes`` (``dek_ciphertext`` + ``dek_generation``). The
plaintext DEK exists only for the duration of one operation — it is created,
unwrapped, or rewrapped inside this module and dropped when the caller's
``async with`` block ends. This is the approved posture (phase5-design.md §6.7
point 5): **operation-scoped unwrap, no long-lived plaintext-DEK cache**,
deliberately unlike the module-global ``_fernet`` cache the secret store uses for
its own single-key path.

Where the envelope lives is a security property, not a storage choice. The
independent audit of Phase 5.2.1 (finding F1) put it plainly: on
``organizations`` — an RLS-exempt table, because it *is* the tenant — the
envelope was protected by the KEK provider alone, and PostgreSQL would not have
refused a cross-tenant read. It now lives in a table of its own, stamped with
``org_id`` like every other tenant-owned row, so the ORM guard, the loader
criteria and the RLS policies all apply to it. This module is the **only** code
path that reads or writes it, and it refuses to run outside a scope that
authorizes the organization it was asked about:

* request paths call it inside ``org_scope(org_id)`` (opened by the request
  dependencies), so the row it can reach is the acting organization's;
* the KEK-rotation sweep calls :func:`rewrap_org_deks` inside
  ``system_scope(...)``, because a rotation is cross-tenant by definition.

Anything else is a :class:`~app.core.tenancy.TenancyScopeError`, raised *before*
the database is touched. That matters more than it sounds: under a mismatched
organization scope the RLS policy would return an empty set rather than an error,
and an empty set here means "this organization has no DEK yet" — the code would
then try to mint one. An explicit refusal is the honest failure.

Three further behaviours are load-bearing:

* **First use is claimed, not assumed.** Concurrent first requests for the same
  organization each generate a candidate DEK, but only one can win the conditional
  ``INSERT ... ON CONFLICT (org_id) DO NOTHING`` — the unique constraint on
  ``org_id`` is the arbiter. The losers discard their candidate and unwrap the
  winner's envelope, so an organization ends up with exactly one authoritative
  generation instead of two rows' worth of competing key material. The claim is a
  compare-and-set on **row existence**, not a row lock held across a provider
  round-trip: no transaction is open while Vault is being called, so a slow or
  unavailable provider cannot pin a row lock or a connection.
* **A KEK rotation cannot write a stale envelope** (audit finding F2). The update
  in :func:`rewrap_org_deks` carries the exact envelope value *and* generation it
  read, so a writer that lost a race cannot overwrite the winner's envelope with
  one derived from a snapshot that is no longer current. The loser re-reads the
  authoritative state and retries against that, a bounded number of times.
* **A failure never leaves a usable-looking envelope.** The row is written only
  after the provider has returned a ciphertext for it; if wrapping fails, the
  transaction rolls back and the organization keeps ``dek_generation = 0`` — the
  schema's own way of saying "no DEK yet" (the pair CHECK makes any other
  combination unrepresentable).

Scope note: this slice creates and unwraps DEKs. It does **not** store a
certificate key, a DNS credential or an ACME account key — those columns arrive,
with their own tables, in Phase 5.2.2. Nothing here holds key material in the
database beyond the wrapped DEK itself.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, cast

from cryptography.fernet import Fernet
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.tenancy import (
    SCOPE_ORG,
    SCOPE_SYSTEM,
    TenancyScopeError,
    current_org,
    current_scope,
)
from app.models.tenancy import Organization, OrganizationDekEnvelope
from app.services.kek import (
    PURPOSE_ORG_DEK,
    EncryptionContext,
    KEKEnvelopeError,
    KEKProvider,
    WrappedKey,
)
from app.services.kek.factory import get_kek_provider

log = get_logger("nexusops.dek")

#: The generation a first-use claim stores. ``0`` stays reserved for "no DEK yet"
#: by the pair CHECK, so the first real DEK is ``1`` and nothing else may be the
#: result of a creation path.
FIRST_GENERATION = 1

#: How many times one row's rewrap may re-read and retry after losing the
#: compare-and-set. Bounded on purpose: a rotation that keeps losing is a sign of
#: contention to report, not a reason to spin, and every retry is a provider
#: round-trip. The next pass (or the next operator invocation) picks up whatever
#: this one could not claim.
_REWRAP_ATTEMPTS = 3


class UnknownOrganizationError(LookupError):
    """No such organization is visible to this session."""


@dataclass
class RewrapReport:
    """What a KEK-rotation pass did. Counts and sanitized reasons only."""

    scanned: int = 0
    rewrapped: int = 0
    unchanged: int = 0
    failed: int = 0
    #: Rows whose compare-and-set lost a race and could not be settled within the
    #: bounded retries. The stored envelope is whatever the winning writer put
    #: there — never this pass's snapshot — and the next pass picks it up.
    contended: int = 0
    #: ``(org_id, reason)`` — the reason is a provider error message, which by
    #: construction carries no key material.
    failures: list[tuple[uuid.UUID, str]] = field(default_factory=list)


def _context(org_id: uuid.UUID, purpose: str, generation: int) -> EncryptionContext:
    return EncryptionContext(org_id=org_id, purpose=purpose, dek_generation=generation)


def _require_matching_provider(wrapped: WrappedKey, provider: KEKProvider) -> None:
    """Refuse a stored envelope that this provider cannot legitimately unwrap.

    This is the no-fallback rule seen from the data's side: a DEK wrapped by the
    test provider must not be silently "unwrapped" by production custody (it cannot
    be — the keys differ), and a DEK wrapped by Vault must never be re-wrapped by a
    local test key. Failing with a named error beats a confusing auth failure.
    """
    if wrapped.provider != provider.name:
        raise KEKEnvelopeError(
            f"the stored DEK was wrapped by provider {wrapped.provider!r} but the "
            f"configured provider is {provider.name!r}; restore the matching provider "
            "configuration (there is no fallback)"
        )


def _require_envelope_scope(org_id: uuid.UUID) -> None:
    """Refuse to touch an envelope outside a scope that authorizes it.

    Two scopes are legitimate, and they are the two the tenancy model defines: the
    organization's own scope, and the system scope a cross-tenant sweep runs in.
    An *organization* scope for a **different** organization is the dangerous case,
    and the reason this check exists rather than relying on the policy alone: RLS
    would return no rows, which this module cannot distinguish from "no DEK yet",
    and it would respond by minting one.
    """
    scope = current_scope()
    if scope == SCOPE_SYSTEM:
        return
    if scope == SCOPE_ORG and current_org() == org_id:
        return
    raise TenancyScopeError(
        f"the DEK envelope of organization {org_id} was reached from scope "
        f"{scope!r} ({current_org()}); envelope access runs inside "
        f"org_scope({org_id}) for one organization's work, or inside "
        "system_scope(...) for the rotation sweep"
    )


async def _organization_exists(db: AsyncSession, org_id: uuid.UUID) -> bool:
    """Whether *org_id* names a real organization.

    ``organizations`` is the tenant itself and carries no RLS, so this is readable
    from any scope — which is exactly what makes it a usable precondition: it
    turns "no such organization" into a named error instead of an envelope row
    that the foreign key would reject with a driver-level message.
    """
    found = await db.scalar(select(Organization.id).where(Organization.id == org_id))
    return found is not None


async def _load_envelope(db: AsyncSession, org_id: uuid.UUID) -> tuple[str, int] | None:
    """The authoritative stored envelope, or ``None`` when there is none.

    The ``org_id`` predicate is explicit rather than left to the guard's loader
    criteria: under the system scope no criteria are added, so a query that relied
    on them would scan every tenant's envelope.
    """
    row = (
        await db.execute(
            select(
                OrganizationDekEnvelope.dek_ciphertext,
                OrganizationDekEnvelope.dek_generation,
            ).where(OrganizationDekEnvelope.org_id == org_id)
        )
    ).one_or_none()
    if row is None or row[0] is None:
        return None
    return str(row[0]), int(row[1])


async def _load(db: AsyncSession, org_id: uuid.UUID) -> tuple[str | None, int]:
    """``(ciphertext, generation)`` for *org_id*; ``(None, 0)`` means "no DEK yet"."""
    if not await _organization_exists(db, org_id):
        raise UnknownOrganizationError(f"organization {org_id} does not exist")
    envelope = await _load_envelope(db, org_id)
    return envelope if envelope is not None else (None, 0)


async def _claim_first_dek(
    db: AsyncSession, org_id: uuid.UUID, purpose: str, provider: KEKProvider
) -> bytes:
    """Generate a DEK, wrap it, and claim the row — or adopt the winner's.

    The provider call happens **before** the conditional insert and outside any
    lock, so no transaction is held across network I/O. Losing the race is normal
    and cheap: the candidate is discarded and the winner's envelope is unwrapped.
    ``ON CONFLICT (org_id) DO NOTHING`` against the table's unique constraint is
    what makes this a claim rather than an assumption — the loser's row is never
    written, so there is no second generation to reconcile.
    """
    candidate = Fernet.generate_key()  # CSPRNG, one per organization, never derived
    context = _context(org_id, purpose, FIRST_GENERATION)
    wrapped = await provider.wrap_dek(candidate, context)
    claimed = await db.execute(
        pg_insert(OrganizationDekEnvelope)
        .values(
            org_id=org_id,
            dek_ciphertext=wrapped.encode(),
            dek_generation=FIRST_GENERATION,
        )
        .on_conflict_do_nothing(index_elements=["org_id"])
    )
    # ``rowcount`` is what makes this a compare-and-set rather than an assumption:
    # zero means another writer claimed the row between our read and our write.
    if int(cast(CursorResult[Any], claimed).rowcount or 0) == 1:
        log.info("org_dek_created", org_id=str(org_id), generation=FIRST_GENERATION)
        return candidate
    # Another request claimed the row first. Its envelope is the authoritative one;
    # ours is dropped without ever having been stored.
    ciphertext, generation = await _load(db, org_id)
    if ciphertext is None:  # pragma: no cover - only reachable if the row was cleared concurrently
        raise KEKEnvelopeError("another writer removed the DEK while it was being created")
    return await _unwrap(org_id, purpose, generation, ciphertext, provider)


async def _unwrap(
    org_id: uuid.UUID,
    purpose: str,
    generation: int,
    ciphertext: str,
    provider: KEKProvider,
) -> bytes:
    wrapped = WrappedKey.decode(ciphertext)
    _require_matching_provider(wrapped, provider)
    context = _context(org_id, purpose, generation)
    return await provider.unwrap_dek(wrapped, context)


@asynccontextmanager
async def org_dek(
    db: AsyncSession,
    org_id: uuid.UUID,
    *,
    purpose: str = PURPOSE_ORG_DEK,
    provider: KEKProvider | None = None,
) -> AsyncIterator[Fernet]:
    """Yield the organization's DEK for **one operation**, then drop it.

    Usage is deliberately narrow: the caller gets a :class:`Fernet` and cannot
    reach the raw key bytes, the wrapped value or the provider. When the block
    exits — normally or by exception — the local references to the key material are
    cleared, so a traceback or a later inspection of the frame cannot surface a DEK.
    """
    _require_envelope_scope(org_id)
    provider = provider or get_kek_provider()
    ciphertext, generation = await _load(db, org_id)
    if ciphertext is None:
        key = await _claim_first_dek(db, org_id, purpose, provider)
    else:
        key = await _unwrap(org_id, purpose, generation, ciphertext, provider)
    fernet = Fernet(key)
    try:
        yield fernet
    finally:
        # Overwrite the references we control. (Python cannot scrub the bytes
        # object itself; the point is that nothing keeps it alive or reachable.)
        key = b""
        fernet = None  # type: ignore[assignment]


async def _rewrap_one(
    db: AsyncSession,
    *,
    org_id: uuid.UUID,
    ciphertext: str,
    generation: int,
    provider: KEKProvider,
    report: RewrapReport,
) -> None:
    """Rotate one organization's envelope under the provider's current key version.

    The write is a **compare-and-set**: it applies only while the stored envelope
    is still exactly the one this attempt read, at the same generation. A writer
    that lost a race therefore cannot overwrite the winner with an envelope derived
    from a snapshot that is no longer current (audit finding F2) — it re-reads the
    authoritative row and retries against *that* value, at most
    :data:`_REWRAP_ATTEMPTS` times. Nothing is written before the provider has
    returned a ciphertext, so a provider failure leaves the row exactly as it was.
    """
    previous, current_generation = ciphertext, generation
    for attempt in range(_REWRAP_ATTEMPTS):
        try:
            wrapped = WrappedKey.decode(previous)
            _require_matching_provider(wrapped, provider)
            rewrapped = await provider.rewrap_dek(
                wrapped, _context(org_id, PURPOSE_ORG_DEK, current_generation)
            )
        except Exception as exc:
            report.failed += 1
            report.failures.append((org_id, str(exc)))
            log.warning("org_dek_rewrap_failed", org_id=str(org_id), error=str(exc))
            return
        if rewrapped == wrapped:
            # Already on the current key version: the pass is per-row idempotent
            # and rewrites nothing.
            report.unchanged += 1
            return
        written = await db.execute(
            update(OrganizationDekEnvelope)
            .where(
                OrganizationDekEnvelope.org_id == org_id,
                OrganizationDekEnvelope.dek_ciphertext == previous,
                OrganizationDekEnvelope.dek_generation == current_generation,
            )
            .values(dek_ciphertext=rewrapped.encode())
        )
        if int(cast(CursorResult[Any], written).rowcount or 0) == 1:
            report.rewrapped += 1
            log.info(
                "org_dek_rewrapped",
                org_id=str(org_id),
                from_version=wrapped.key_version,
                to_version=rewrapped.key_version,
                attempts=attempt + 1,
            )
            return
        # Lost the compare-and-set. The row changed — or disappeared — under us, so
        # our snapshot is stale and must not be forced. Re-read the authoritative
        # state and decide against that instead.
        fresh = await _load_envelope(db, org_id)
        if fresh is None:
            # Nothing left to rotate (the DEK was cleared or removed concurrently).
            report.contended += 1
            log.warning("org_dek_rewrap_superseded", org_id=str(org_id), attempts=attempt + 1)
            return
        previous, current_generation = fresh
    report.contended += 1
    log.warning("org_dek_rewrap_contended", org_id=str(org_id), attempts=_REWRAP_ATTEMPTS)


async def rewrap_org_deks(
    db: AsyncSession, *, batch_size: int = 100, provider: KEKProvider | None = None
) -> RewrapReport:
    """Re-wrap every stored DEK under the provider's current key version.

    This is the KEK-rotation path (§6.3): the provider does the rewrap, so **no
    plaintext DEK is returned to this process at any point**, and a KEK rotation
    never increments ``dek_generation`` — the generation says which *DEK* is
    wrapped, and a rotation does not change the DEK, only which KEK version
    wraps it (that version lives inside the envelope). Rotating an organization's
    DEK generation is a different, deliberately unimplemented operation.

    It is resumable and per-row idempotent — a row already on the current version
    comes back unchanged and is not rewritten — and it reports failures per
    organization instead of aborting, because a single unreadable envelope must not
    block the rotation of everyone else's.

    It must run inside the **system scope**: every stored envelope has to be
    visited, which is cross-tenant by definition, and under an organization scope
    the policies would expose one tenant's rows and the rotation would look
    successful while doing nothing for anyone else. An operator-invoked script
    (a management command), not a background task: a KEK rotation is a deliberate,
    observable operation.
    """
    if current_scope() != SCOPE_SYSTEM:
        raise TenancyScopeError(
            "rewrap_org_deks() rotates every organization's envelope, so it must run "
            "inside system_scope(...) (a sweep opens it through sweep_session). An "
            "organization scope would silently rotate only the rows its policy exposes."
        )
    provider = provider or get_kek_provider()
    report = RewrapReport()
    last_org: uuid.UUID | None = None
    while True:
        stmt = (
            select(
                OrganizationDekEnvelope.org_id,
                OrganizationDekEnvelope.dek_ciphertext,
                OrganizationDekEnvelope.dek_generation,
            )
            .where(OrganizationDekEnvelope.dek_ciphertext.is_not(None))
            .order_by(OrganizationDekEnvelope.org_id)
            .limit(batch_size)
        )
        if last_org is not None:
            # Keyset pagination: stable while rows are being rewritten underneath
            # us, unlike OFFSET which would skip a row after every update.
            stmt = stmt.where(OrganizationDekEnvelope.org_id > last_org)
        rows = list((await db.execute(stmt)).all())
        if not rows:
            break
        for org_id, ciphertext, generation in rows:
            last_org = org_id
            report.scanned += 1
            assert ciphertext is not None  # the query filters them out
            await _rewrap_one(
                db,
                org_id=org_id,
                ciphertext=str(ciphertext),
                generation=int(generation),
                provider=provider,
                report=report,
            )
    return report


__all__ = [
    "FIRST_GENERATION",
    "RewrapReport",
    "UnknownOrganizationError",
    "org_dek",
    "rewrap_org_deks",
]
