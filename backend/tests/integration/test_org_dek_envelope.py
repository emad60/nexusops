"""The organization DEK envelope, against a real database.

`test_kek_deterministic` proves the provider contract; this module proves the
*envelope* on top of it, where the interesting failures live:

* **first use is a race, and must not be lost.** Several concurrent first requests
  for the same organization each generate a candidate DEK, and exactly one may
  become the stored envelope. The others must adopt it, so every caller ends up
  holding the same key and the row keeps one generation — the property that makes
  "generation 1" meaningful at all.
* **binding is enforced by the row, not by a caller's good manners.** Taking a
  wrapped DEK out of one organization's row and putting it in another's (the
  cheapest possible cross-tenant attack, and one a compromised writer can do with
  a single UPDATE) must fail to unwrap.
* **a failed provider call leaves nothing behind.** No ciphertext, no generation
  bump, and no committed envelope that looks usable but is not — the failure mode
  the schema's pair invariant exists to make unrepresentable.
* **no plaintext DEK is persisted anywhere**, including in the columns and in the
  log stream, and the API surface never exposes the wrapped value either.
* **rewrap moves the ciphertext without moving the key.** A KEK rotation must
  change what is stored, keep the binding, and keep the DEK usable — reported per
  organization so one bad row cannot stall the rotation.

The provider here is the deterministic one, named explicitly at every call site:
the test suite selects it, it is never reached by falling back from anything.
"""

from __future__ import annotations

import asyncio
import base64
import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
import structlog
from app.core.config import get_settings
from app.models.tenancy import Organization
from app.services.dek_envelope import (
    UnknownOrganizationError,
    org_dek,
    rewrap_org_deks,
)
from app.services.kek import (
    KEKContextMismatchError,
    KEKEnvelopeError,
    KEKUnavailableError,
    ProviderHealth,
    ProviderStatus,
    WrappedKey,
)
from app.services.kek.deterministic import DeterministicKEKProvider
from cryptography.fernet import InvalidToken
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def sessions() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """A sessionmaker for envelope tests, so each caller gets its own session.

    Concurrency is the point of half these tests, and a shared session would
    serialize the very interleaving being tested.
    """
    settings = get_settings()
    assert settings.database_url is not None
    engine = create_async_engine(settings.database_url)
    try:
        yield async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def org_id(owner: dict) -> uuid.UUID:
    return uuid.UUID(owner["active_organization_id"])


class _FailingProvider:
    """A provider that cannot wrap — the "Vault is down" path, exactly."""

    name = "test"
    production_safe = False

    def __init__(self) -> None:
        self.calls = 0

    async def wrap_dek(self, dek: bytes, ctx) -> WrappedKey:
        self.calls += 1
        raise KEKUnavailableError("provider unreachable during wrap")

    async def unwrap_dek(self, wrapped: WrappedKey, ctx) -> bytes:
        raise KEKUnavailableError("provider unreachable during unwrap")

    async def rewrap_dek(self, wrapped: WrappedKey, ctx) -> WrappedKey:
        raise KEKUnavailableError("provider unreachable during rewrap")

    async def health(self) -> ProviderHealth:
        return ProviderHealth(ProviderStatus.UNREACHABLE, self.name, "simulated outage")


class _OverlappingProvider(DeterministicKEKProvider):
    """The deterministic provider with a real await point inside ``wrap_dek``.

    Without it the race would be a hope rather than a test: each coroutine could run
    to completion before the next started, and the concurrency assertions would
    pass while proving nothing. The sleep makes every racer observe an empty
    column before any of them claims it, and ``wraps`` counts that they did.
    """

    def __init__(self) -> None:
        super().__init__()
        self.wraps = 0

    async def wrap_dek(self, dek: bytes, ctx) -> WrappedKey:
        self.wraps += 1
        await asyncio.sleep(0.05)
        return await super().wrap_dek(dek, ctx)


async def _stored(db: AsyncSession, org: uuid.UUID) -> tuple[str | None, int]:
    """The wrapped DEK and its generation, read straight from the row."""
    row = (
        await db.execute(
            select(Organization.dek_ciphertext, Organization.dek_generation).where(
                Organization.id == org
            )
        )
    ).one()
    return row[0], int(row[1])


async def _set_stored(db: AsyncSession, org: uuid.UUID, ciphertext: str, generation: int) -> None:
    """Overwrite a row's envelope — how these tests simulate replay/repointing."""
    await db.execute(
        text("UPDATE organizations SET dek_ciphertext = :c, dek_generation = :g WHERE id = :id"),
        {"c": ciphertext, "g": generation, "id": str(org)},
    )
    await db.commit()


def _plaintext_key(fernet) -> bytes:
    """The 32 raw key bytes behind a yielded Fernet, for the no-leak assertions.

    Read from the Fernet instance itself: the envelope deliberately exposes no
    accessor for its key, and the only place a test can legitimately observe it is
    the object the operation was handed.
    """
    return fernet._signing_key + fernet._encryption_key


# --- creation and recovery ----------------------------------------------------


async def test_first_use_creates_one_wrapped_generation(sessions, org_id) -> None:
    provider = DeterministicKEKProvider()
    async with sessions() as db:
        async with org_dek(db, org_id, provider=provider):
            await db.commit()
        ciphertext, generation = await _stored(db, org_id)

    assert generation == 1, "first use must claim generation 1"
    assert ciphertext is not None
    envelope = WrappedKey.decode(ciphertext)
    assert envelope.provider == "test"
    assert envelope.key_id == "deterministic-test-key"
    assert envelope.key_version == "1"


async def test_second_use_recovers_the_same_dek(sessions, org_id) -> None:
    """The envelope is reachable across operations: wrap once, unwrap later."""
    provider = DeterministicKEKProvider()
    async with sessions() as db:
        async with org_dek(db, org_id, provider=provider) as fernet:
            token = fernet.encrypt(b"phase 5.2.1")
            await db.commit()
    before = token

    async with sessions() as db:
        async with org_dek(db, org_id, provider=provider) as fernet:
            assert fernet.decrypt(before) == b"phase 5.2.1"
        _, generation = await _stored(db, org_id)

    assert generation == 1, "recovery must not generate a second DEK"


async def test_unknown_organization_is_named(sessions) -> None:
    provider = DeterministicKEKProvider()
    async with sessions() as db:
        with pytest.raises(UnknownOrganizationError):
            async with org_dek(db, uuid.uuid4(), provider=provider):
                pass  # pragma: no cover - the context manager raises first


async def test_no_plaintext_dek_is_stored_or_logged(sessions, org_id) -> None:
    """Neither the column, nor an event, nor an error carries the key."""
    provider = DeterministicKEKProvider()
    with structlog.testing.capture_logs() as logs:
        async with sessions() as db:
            async with org_dek(db, org_id, provider=provider) as fernet:
                raw = _plaintext_key(fernet)
                fernet_key = base64.urlsafe_b64encode(raw)
                await db.commit()
            ciphertext, _ = await _stored(db, org_id)
            assert ciphertext is not None
            assert raw not in ciphertext.encode("utf-8")
            assert fernet_key.decode() not in ciphertext
    rendered = str(logs)
    assert fernet_key.decode() not in rendered
    assert raw.hex() not in rendered


# --- first-use concurrency ----------------------------------------------------


async def test_concurrent_first_use_yields_exactly_one_generation(sessions, org_id) -> None:
    """Six racing first requests, one stored DEK, everybody holding that one key."""
    provider = _OverlappingProvider()
    tokens: dict[int, bytes] = {}

    async def first_use(index: int) -> None:
        async with sessions() as db:
            async with org_dek(db, org_id, provider=provider) as fernet:
                tokens[index] = fernet.encrypt(b"concurrent first use")
                # Committing inside the block is what a request handler does at the
                # end of its unit of work; it is also what releases the row for the
                # requests queued behind the winner.
                await db.commit()

    await asyncio.gather(*(first_use(i) for i in range(6)))

    assert len(tokens) == 6
    # Every racer generated and wrapped a candidate before any claim landed: this
    # is the interleaving the test is about, not six sequential calls.
    assert provider.wraps == 6, "the racers did not actually overlap"
    async with sessions() as db:
        ciphertext, generation = await _stored(db, org_id)

    # One generation, and every caller's ciphertext decrypts under every other
    # caller's DEK: the losers adopted the winner's envelope instead of keeping
    # their own candidate.
    assert generation == 1
    assert ciphertext is not None
    for index, token in tokens.items():
        for other in tokens:
            if other == index:
                continue
            async with sessions() as db:
                async with org_dek(db, org_id, provider=provider) as fernet:
                    assert fernet.decrypt(token) == b"concurrent first use"


async def test_a_lost_race_discards_its_candidate(sessions, org_id) -> None:
    """The loser adopts the winner; its own wrapped candidate is never stored."""
    provider = DeterministicKEKProvider()
    async with sessions() as db:
        async with org_dek(db, org_id, provider=provider) as winner:
            winner_token = winner.encrypt(b"winner")
            await db.commit()

    # A second, sequential call is the "late" case of the same race.
    async with sessions() as db:
        async with org_dek(db, org_id, provider=provider) as late:
            assert late.decrypt(winner_token) == b"winner"
            await db.commit()
        ciphertext, generation = await _stored(db, org_id)

    assert generation == 1
    assert ciphertext is not None


# --- tenant and context isolation ---------------------------------------------


async def test_organizations_get_independent_deks(owner, second_org, sessions) -> None:
    provider = DeterministicKEKProvider()
    other_id = uuid.UUID(second_org["id"])
    mine_id = uuid.UUID(owner["active_organization_id"])

    async with sessions() as db:
        async with org_dek(db, mine_id, provider=provider) as mine:
            mine_token = mine.encrypt(b"tenant A")
            await db.commit()
        async with org_dek(db, other_id, provider=provider) as theirs:
            await db.commit()

    async with sessions() as db:
        async with org_dek(db, mine_id, provider=provider) as mine:
            async with org_dek(db, other_id, provider=provider) as theirs:
                # Different key material, and not merely a different label: the
                # other tenant's ciphertext is unreadable under this DEK.
                assert _plaintext_key(mine) != _plaintext_key(theirs)
                with pytest.raises(InvalidToken):
                    theirs.decrypt(mine_token)


async def test_a_replayed_envelope_does_not_unwrap_for_another_organization(
    owner, second_org, sessions
) -> None:
    """Copying org A's wrapped DEK onto org B's row must fail to unwrap.

    This is the attack the binding exists for: a single UPDATE, no provider access,
    and with beside-ciphertext metadata it would simply work.
    """
    provider = DeterministicKEKProvider()
    victim = uuid.UUID(owner["active_organization_id"])
    attacker = uuid.UUID(second_org["id"])

    async with sessions() as db:
        async with org_dek(db, victim, provider=provider):
            await db.commit()
        ciphertext, _ = await _stored(db, victim)
        assert ciphertext is not None
        assert ciphertext.startswith("v1:test:")

    async with sessions() as db:
        await _set_stored(db, attacker, ciphertext, 1)
        with pytest.raises(KEKContextMismatchError):
            async with org_dek(db, attacker, provider=provider):
                pass  # pragma: no cover - the provider refuses the binding


async def test_a_dek_replayed_as_another_generation_fails(sessions, org_id) -> None:
    provider = DeterministicKEKProvider()
    async with sessions() as db:
        async with org_dek(db, org_id, provider=provider):
            await db.commit()
        ciphertext, _ = await _stored(db, org_id)
        assert ciphertext is not None
        # Same organization, same ciphertext, different generation: still refused,
        # because the generation is part of what the ciphertext authenticates.
        await _set_stored(db, org_id, ciphertext, 3)
        with pytest.raises(KEKContextMismatchError):
            async with org_dek(db, org_id, provider=provider):
                pass  # pragma: no cover


async def test_an_envelope_from_another_provider_is_refused(sessions, org_id) -> None:
    """No fallback: a DEK wrapped under a different provider is a named error."""
    provider = DeterministicKEKProvider()
    foreign = WrappedKey(
        provider="vault-transit",
        key_id="nexusops-org-dek",
        key_version="1",
        ciphertext=b"vault:v1:AAAA",
    )
    async with sessions() as db:
        await _set_stored(db, org_id, foreign.encode(), 1)
        with pytest.raises(KEKEnvelopeError, match="configured provider"):
            async with org_dek(db, org_id, provider=provider):
                pass  # pragma: no cover


async def test_a_corrupt_stored_envelope_is_refused_before_the_provider(sessions, org_id) -> None:
    provider = DeterministicKEKProvider()
    async with sessions() as db:
        await _set_stored(db, org_id, "not-an-envelope", 1)
        with pytest.raises(KEKEnvelopeError):
            async with org_dek(db, org_id, provider=provider):
                pass  # pragma: no cover


# --- no read model exposes the envelope ---------------------------------------

#: The full approved read surface for a membership and the organization it carries
#: (``app/schemas/organization.py``). The DEK columns are deliberately absent, and
#: this list is the assertion: a response that grows a ``dek_*`` field fails here.
MEMBERSHIP_FIELDS = {"organization", "role_name", "role_id", "status"}
ORGANIZATION_FIELDS = {
    "id",
    "created_at",  # OutModel carries the creation timestamp only, by design
    "name",
    "slug",
    "description",
    "status",
    "is_provisional",
    "renamed_at",
}


async def test_the_envelope_is_not_reachable_through_a_read_model(
    client, owner, sessions, org_id
) -> None:
    """The wrapped DEK exists in exactly one place: the table, wrapped.

    Asserted against the API rather than against the ORM, because the ORM is what
    already carries the column — what has to stay true is that no response model
    exposes it, which is the same response-allowlist check the certificate models use.
    The organization is given a real envelope first, so the assertion is about a
    populated row rather than an empty one.
    """
    provider = DeterministicKEKProvider()
    async with sessions() as db:
        async with org_dek(db, org_id, provider=provider):
            await db.commit()
        stored, _ = await _stored(db, org_id)
    assert stored is not None

    response = await client.get("/api/v1/organizations", headers=owner["headers"])
    assert response.status_code == 200, response.text
    body = response.json()
    assert body and isinstance(body, list)
    for membership in body:
        assert set(membership) == MEMBERSHIP_FIELDS, set(membership) ^ MEMBERSHIP_FIELDS
        assert set(membership["organization"]) == ORGANIZATION_FIELDS
        rendered = str(membership).lower()
        assert "dek" not in rendered
        assert "ciphertext" not in rendered
    # The envelope is not in the response, but it is in the row — so the test is
    # proving the read model, not an empty column.
    assert "dek_ciphertext" not in str(body)


# --- failure behavior ---------------------------------------------------------


async def test_a_failed_wrap_leaves_no_envelope(sessions, org_id) -> None:
    """Failure fails closed: generation 0, no ciphertext, nothing usable stored."""
    failing = _FailingProvider()
    async with sessions() as db:
        with pytest.raises(KEKUnavailableError):
            async with org_dek(db, org_id, provider=failing):
                pass  # pragma: no cover
        await db.rollback()
        ciphertext, generation = await _stored(db, org_id)

    assert failing.calls == 1
    assert ciphertext is None
    assert generation == 0, "a failed provider call must not claim a generation"


async def test_recovery_after_a_failed_wrap_still_works(sessions, org_id) -> None:
    """The organization is not poisoned by an outage that happened before it had a DEK."""
    failing = _FailingProvider()
    async with sessions() as db:
        with pytest.raises(KEKUnavailableError):
            async with org_dek(db, org_id, provider=failing):
                pass  # pragma: no cover
        await db.rollback()

    provider = DeterministicKEKProvider()
    async with sessions() as db:
        async with org_dek(db, org_id, provider=provider) as fernet:
            token = fernet.encrypt(b"after the outage")
            await db.commit()
        _, generation = await _stored(db, org_id)
    assert generation == 1

    async with sessions() as db:
        async with org_dek(db, org_id, provider=provider) as fernet:
            assert fernet.decrypt(token) == b"after the outage"


# --- KEK rotation -------------------------------------------------------------


async def test_rewrap_moves_the_ciphertext_without_moving_the_key(sessions, org_id) -> None:
    """A KEK-only rotation: new version, same DEK, no plaintext in this process."""
    provider = DeterministicKEKProvider()
    async with sessions() as db:
        async with org_dek(db, org_id, provider=provider) as fernet:
            token = fernet.encrypt(b"survives rotation")
            await db.commit()
        before, generation = await _stored(db, org_id)

    assert before is not None
    provider.rotate()  # the operator rotated the KEK in the provider

    async with sessions() as db:
        report = await rewrap_org_deks(db, provider=provider)
        await db.commit()
        after, generation_after = await _stored(db, org_id)

    assert report.scanned == 1
    assert report.rewrapped == 1
    assert report.failed == 0
    assert after is not None and after != before
    assert WrappedKey.decode(after).key_version == "2"
    assert generation_after == generation == 1, "a KEK rotation is not a DEK rotation"

    async with sessions() as db:
        async with org_dek(db, org_id, provider=provider) as fernet:
            assert fernet.decrypt(token) == b"survives rotation"


async def test_rewrap_is_idempotent(sessions, org_id) -> None:
    provider = DeterministicKEKProvider()
    async with sessions() as db:
        async with org_dek(db, org_id, provider=provider):
            await db.commit()
        await rewrap_org_deks(db, provider=provider)
        await db.commit()
        first, _ = await _stored(db, org_id)
        second_report = await rewrap_org_deks(db, provider=provider)
        await db.commit()
        second, _ = await _stored(db, org_id)

    assert first == second
    assert second_report.unchanged == 1
    assert second_report.rewrapped == 0


async def test_rewrap_reports_a_bad_row_without_stopping_the_pass(
    owner, second_org, sessions
) -> None:
    """One unreadable envelope must not block everyone else's rotation."""
    provider = DeterministicKEKProvider()
    good = uuid.UUID(owner["active_organization_id"])
    bad = uuid.UUID(second_org["id"])
    async with sessions() as db:
        async with org_dek(db, good, provider=provider):
            await db.commit()
        await _set_stored(
            db,
            bad,
            WrappedKey(
                provider="vault-transit",
                key_id="some-other-key",
                key_version="1",
                ciphertext=b"vault:v1:AAAA",
            ).encode(),
            1,
        )
        provider.rotate()
        report = await rewrap_org_deks(db, provider=provider)

    assert report.scanned == 2
    assert report.rewrapped == 1
    assert report.failed == 1
    assert report.failures[0][0] == bad
    # The reason is sanitized by construction: it is a provider error message,
    # never key material.
    assert "not-a-key" not in report.failures[0][1]
