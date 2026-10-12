"""The organization DEK envelope: one wrapped data key per organization.

Every organization owns one Fernet DEK, stored **wrapped** on its row
(``organizations.dek_ciphertext`` + ``dek_generation``). The plaintext DEK exists
only for the duration of one operation — it is created, unwrapped, or rewrapped
inside this module and dropped when the caller's ``async with`` block ends. This
is the approved posture (phase5-design.md §6.7 point 5): **operation-scoped
unwrap, no long-lived plaintext-DEK cache**, deliberately unlike the module-global
``_fernet`` cache the secret store uses for its own single-key path.

Two behaviours here are load-bearing:

* **First use is claimed, not assumed.** Concurrent first requests for the same
  organization each generate a candidate DEK, but only one can win the conditional
  ``UPDATE ... WHERE dek_ciphertext IS NULL``. The losers discard their candidate
  and unwrap the winner's envelope, so an organization ends up with exactly one
  authoritative generation instead of two rows' worth of competing key material.
  Crucially the claim is a compare-and-set on a column, **not** a row lock held
  across a provider round-trip: no transaction is open while Vault is being called,
  so a slow or unavailable provider cannot pin a row lock or a connection.
* **A failure never leaves a usable-looking envelope.** The row is written only
  after the provider has returned a ciphertext for it; if wrapping fails, the
  transaction rolls back and the organization keeps ``dek_generation = 0`` — the
  schema's own way of saying "no DEK yet" (the pair CHECK makes any other
  combination unrepresentable).

Scope note: this slice creates and unwraps DEKs. It does **not** store a
certificate key, a DNS credential or an ACME account key — those columns arrive, with
their own tables, in Phase 5.2.2. Nothing here holds key material in the database
beyond the wrapped DEK itself.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, cast

from cryptography.fernet import Fernet
from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.tenancy import Organization
from app.services.kek import (
    PURPOSE_ORG_DEK,
    EncryptionContext,
    KEKEnvelopeError,
    KEKProvider,
    WrappedKey,
)
from app.services.kek.factory import get_kek_provider

log = get_logger("nexusops.dek")


class UnknownOrganizationError(LookupError):
    """No such organization is visible to this session."""


@dataclass
class RewrapReport:
    """What a KEK-rotation pass did. Counts and sanitized reasons only."""

    scanned: int = 0
    rewrapped: int = 0
    unchanged: int = 0
    failed: int = 0
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


async def _load(db: AsyncSession, org_id: uuid.UUID) -> tuple[str | None, int]:
    row = (
        await db.execute(
            select(Organization.dek_ciphertext, Organization.dek_generation).where(
                Organization.id == org_id
            )
        )
    ).one_or_none()
    if row is None:
        raise UnknownOrganizationError(f"organization {org_id} does not exist")
    ciphertext, generation = row
    return ciphertext, int(generation)


async def _claim_first_dek(
    db: AsyncSession, org_id: uuid.UUID, purpose: str, provider: KEKProvider
) -> bytes:
    """Generate a DEK, wrap it, and claim the row — or adopt the winner's.

    The provider call happens **before** the conditional ``UPDATE`` and outside any
    lock, so no transaction is held across network I/O. Losing the race is normal
    and cheap: the candidate is discarded and the winner's envelope is unwrapped.
    """
    candidate = Fernet.generate_key()  # CSPRNG, one per organization, never derived
    context = _context(org_id, purpose, 1)
    wrapped = await provider.wrap_dek(candidate, context)
    claimed = await db.execute(
        update(Organization)
        .where(Organization.id == org_id, Organization.dek_ciphertext.is_(None))
        .values(dek_ciphertext=wrapped.encode(), dek_generation=1)
    )
    # ``rowcount`` is what makes this a compare-and-set rather than an assumption:
    # zero means another writer claimed the row between our read and our write.
    if int(cast(CursorResult[Any], claimed).rowcount or 0) == 1:
        log.info("org_dek_created", org_id=str(org_id), generation=1)
        return candidate
    # Another request claimed the row first. Its envelope is the authoritative one;
    # ours is dropped without ever having been stored.
    ciphertext, generation = await _load(db, org_id)
    if ciphertext is None:  # pragma: no cover - only reachable if the row was cleared concurrently
        raise KEKEnvelopeError("another writer removed the DEK while it was being created")
    return await _unwrap(db, org_id, purpose, generation, ciphertext, provider)


async def _unwrap(
    db: AsyncSession,
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
    provider = provider or get_kek_provider()
    ciphertext, generation = await _load(db, org_id)
    if ciphertext is None:
        key = await _claim_first_dek(db, org_id, purpose, provider)
    else:
        key = await _unwrap(db, org_id, purpose, generation, ciphertext, provider)
    fernet = Fernet(key)
    try:
        yield fernet
    finally:
        # Overwrite the references we control. (Python cannot scrub the bytes
        # object itself; the point is that nothing keeps it alive or reachable.)
        key = b""
        fernet = None  # type: ignore[assignment]


async def rewrap_org_deks(
    db: AsyncSession, *, batch_size: int = 100, provider: KEKProvider | None = None
) -> RewrapReport:
    """Re-wrap every stored DEK under the provider's current key version.

    This is the KEK-rotation path (§6.3): the provider does the rewrap, so **no
    plaintext DEK is returned to this process at any point**. It is resumable and
    per-row idempotent — a row already on the current version comes back unchanged
    and is not rewritten — and it reports failures per organization instead of
    aborting, because a single unreadable envelope must not block the rotation of
    everyone else's.

    Operator-invoked (a management script), not a background task: a KEK rotation is
    a deliberate, observable operation, not a periodic job.
    """
    provider = provider or get_kek_provider()
    report = RewrapReport()
    last_id: uuid.UUID | None = None
    while True:
        stmt = (
            select(Organization.id, Organization.dek_ciphertext, Organization.dek_generation)
            .where(Organization.dek_ciphertext.is_not(None))
            .order_by(Organization.id)
            .limit(batch_size)
        )
        if last_id is not None:
            # Keyset pagination: stable while rows are being rewritten underneath
            # us, unlike OFFSET which would skip a row after every update.
            stmt = stmt.where(Organization.id > last_id)
        rows = list((await db.execute(stmt)).all())
        if not rows:
            break
        for org_id, ciphertext, generation in rows:
            last_id = org_id
            report.scanned += 1
            assert ciphertext is not None  # the query filters them out
            try:
                wrapped = WrappedKey.decode(ciphertext)
                _require_matching_provider(wrapped, provider)
                rewrapped = await provider.rewrap_dek(
                    wrapped, _context(org_id, PURPOSE_ORG_DEK, int(generation))
                )
            except Exception as exc:
                report.failed += 1
                report.failures.append((org_id, str(exc)))
                log.warning("org_dek_rewrap_failed", org_id=str(org_id), error=str(exc))
                continue
            if rewrapped == wrapped:
                report.unchanged += 1
                continue
            await db.execute(
                update(Organization)
                .where(Organization.id == org_id)
                .values(dek_ciphertext=rewrapped.encode())
            )
            report.rewrapped += 1
            log.info(
                "org_dek_rewrapped",
                org_id=str(org_id),
                from_version=wrapped.key_version,
                to_version=rewrapped.key_version,
            )
    return report


__all__ = ["RewrapReport", "UnknownOrganizationError", "org_dek", "rewrap_org_deks"]
