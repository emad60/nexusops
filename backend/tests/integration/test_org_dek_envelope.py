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
* **rewrap moves the ciphertext without moving the key**, and (Phase 5.2.1.2,
  audit finding F2) **a losing rewrap cannot overwrite a newer envelope.** A KEK
  rotation changes what is stored, keeps the binding, keeps the DEK usable, and
  its write is a compare-and-set on the exact envelope it read — so the stored
  value cannot regress to an older key version, a stale snapshot cannot be forced
  onto the row, and a writer that keeps losing stops after a bounded number of
  attempts and reports it instead of spinning. Every one of those is asserted
  against a real PostgreSQL row here, because that is where the guarantee lives.

**Where the envelope is** moved in this slice (audit finding F1): it is no longer
two columns on the RLS-exempt ``organizations`` table but a row of its own in
``organization_dek_envelopes``, an ordinary organization-scoped tenant table.
Every access below therefore states its tenancy scope, exactly as production code
must:

* ``org_scope(org_id)`` for one organization's own key (the request path);
* ``system_scope(...)`` for the rotation sweep, which is cross-tenant by nature;
* and neither, for the test that proves an unscoped or mismatched scope is
  refused *before* the database is touched rather than answered with an empty set.

The provider here is the deterministic one, named explicitly at every call site:
the test suite selects it, it is never reached by falling back from anything.
"""

from __future__ import annotations

import asyncio
import base64
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
import structlog
from app.core.config import get_settings
from app.core.tenancy import (
    TenancyScopeError,
    apply_scope_to_session,
    install_tenancy_guards,
    org_scope,
    system_scope,
)
from app.models.tenancy import OrganizationDekEnvelope
from app.services.dek_envelope import (
    _REWRAP_ATTEMPTS,
    RewrapReport,
    UnknownOrganizationError,
    org_dek,
    rewrap_org_deks,
)
from app.services.kek import (
    PURPOSE_ORG_DEK,
    EncryptionContext,
    KEKContextMismatchError,
    KEKEnvelopeError,
    KEKUnavailableError,
    ProviderHealth,
    ProviderStatus,
    WrappedKey,
)
from app.services.kek.deterministic import DeterministicKEKProvider
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

pytestmark = pytest.mark.integration

#: The reason string a sweep enters the system scope with. Not asserted on; it
#: exists so the log line this suite generates says what the sweep was doing.
SWEEP_REASON = "KEK rotation sweep (test)"


@pytest_asyncio.fixture
async def sessions() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """A sessionmaker for envelope tests, so each caller gets its own session.

    Concurrency is the point of half these tests, and a shared session would
    serialize the very interleaving being tested.
    """
    # These tests open their own engine, so they must not depend on which fixture
    # happened to import the app first: the guard this module is about (the
    # scope check on organization-scoped tables) is installed here explicitly.
    # ``install_tenancy_guards`` is idempotent.
    install_tenancy_guards()
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


@asynccontextmanager
async def _scoped(
    sessions: async_sessionmaker[AsyncSession],
    *,
    org: uuid.UUID | None = None,
    system: str | None = None,
) -> AsyncIterator[AsyncSession]:
    """One session inside an explicit tenancy scope.

    The envelope is key material, so the service refuses to touch it outside a
    scope that authorizes the organization it was asked about, and the session
    guard refuses an unscoped read of a tenant table. Every call site in this
    module therefore says which of the two legitimate scopes it is running in.
    """
    context = system_scope(system) if system is not None else org_scope(org)
    async with sessions() as db:
        with context:
            # The scope is entered before the session's first statement, so the
            # ``after_begin`` GUC writer would set it anyway; pushing it here makes
            # the session's scope state explicit rather than implied by ordering.
            await apply_scope_to_session(db)
            yield db


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


class _FailingRewrapProvider(DeterministicKEKProvider):
    """Fails *only* ``rewrap_dek`` — a rotation that cannot reach its provider.

    The distinction matters: this provider is at the current key version and can
    wrap and unwrap, so the failure lands strictly between "the provider was
    asked" and "the database was written", which is the window the stored
    envelope must survive untouched.
    """

    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    async def rewrap_dek(self, wrapped: WrappedKey, ctx) -> WrappedKey:
        self.calls += 1
        raise KEKUnavailableError("provider unreachable during rewrap")


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


class _BarrierRewrapProvider(DeterministicKEKProvider):
    """Two rewrap attempts overlap, deterministically.

    ``rewrap_dek`` is called *after* a pass has read its snapshot and *before* it
    writes, so a barrier here means both competing passes hold the same, older
    snapshot when either of them tries to write. That is the interleaving the
    compare-and-set exists for; a sleep would only make it likely.
    """

    def __init__(self, parties: int) -> None:
        super().__init__()
        self.parties = parties
        self.entered = 0
        self.rewraps = 0
        self.both_entered = asyncio.Event()

    async def rewrap_dek(self, wrapped: WrappedKey, ctx) -> WrappedKey:
        self.entered += 1
        self.rewraps += 1
        if self.entered >= self.parties:
            self.both_entered.set()
        # Retries (and any later pass) find the event already set and pass straight
        # through, so only the first round of attempts is coupled.
        await self.both_entered.wait()
        return await super().rewrap_dek(wrapped, ctx)


class _StaleSnapshotProvider(DeterministicKEKProvider):
    """Holds one rewrap result open until the test releases it.

    The result is computed *before* the gate, so it is a genuine snapshot value:
    whatever the row looks like by the time the blocked pass writes, the envelope
    it is holding was derived from an older key version.
    """

    def __init__(self) -> None:
        super().__init__()
        self.calls = 0
        self.stale_result: WrappedKey | None = None
        self.first_call_started = asyncio.Event()
        self.release_first = asyncio.Event()

    async def rewrap_dek(self, wrapped: WrappedKey, ctx) -> WrappedKey:
        self.calls += 1
        result = await super().rewrap_dek(wrapped, ctx)
        if self.calls == 1:
            self.stale_result = result
            self.first_call_started.set()
            await self.release_first.wait()
        return result


class _PingPongProvider(DeterministicKEKProvider):
    """Hands control back to the test before every one of the first ``rounds``
    rewrap results is used.

    Each round the test gets to move the row on (as a competing writer would), so
    the pass's compare-and-set loses every time. This is how the *bound* on
    retries is proved rather than assumed: an unbounded retry loop could never
    finish this test.
    """

    def __init__(self, rounds: int) -> None:
        super().__init__()
        self.rounds = rounds
        self.calls = 0
        self.ready_to_write = asyncio.Event()
        self.competitor_moved = asyncio.Event()

    async def rewrap_dek(self, wrapped: WrappedKey, ctx) -> WrappedKey:
        self.calls += 1
        result = await super().rewrap_dek(wrapped, ctx)
        if self.calls <= self.rounds:
            self.ready_to_write.set()
            await self.competitor_moved.wait()
            self.competitor_moved.clear()
            self.ready_to_write.clear()
        return result


async def _stored(db: AsyncSession, org: uuid.UUID) -> tuple[str | None, int]:
    """The wrapped DEK and its generation, read straight from the envelope row.

    ``(None, 0)`` means "this organization has no envelope at all", which is the
    normal state before its first key-management write.
    """
    row = (
        await db.execute(
            select(
                OrganizationDekEnvelope.dek_ciphertext,
                OrganizationDekEnvelope.dek_generation,
            ).where(OrganizationDekEnvelope.org_id == org)
        )
    ).one_or_none()
    if row is None:
        return None, 0
    return row[0], int(row[1])


async def _row_count(db: AsyncSession, org: uuid.UUID) -> int:
    """How many envelope rows exist for *org* (the unique constraint allows one)."""
    rows = (
        (
            await db.execute(
                select(OrganizationDekEnvelope.id).where(OrganizationDekEnvelope.org_id == org)
            )
        )
        .scalars()
        .all()
    )
    return len(rows)


async def _set_stored(db: AsyncSession, org: uuid.UUID, ciphertext: str, generation: int) -> None:
    """Overwrite a row's envelope — how these tests simulate replay/repointing.

    Raw SQL on purpose: the envelope service has no "put this value" path, and it
    should not grow one. The caller supplies a session in the **system** scope,
    which is the only scope that may write another organization's row.
    """
    await db.execute(
        text(
            "INSERT INTO organization_dek_envelopes "
            "(id, org_id, dek_ciphertext, dek_generation, created_at, updated_at) "
            "VALUES (gen_random_uuid(), :id, :c, :g, now(), now()) "
            "ON CONFLICT (org_id) DO UPDATE "
            "SET dek_ciphertext = EXCLUDED.dek_ciphertext, "
            "    dek_generation = EXCLUDED.dek_generation, "
            "    updated_at = now()"
        ),
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


async def _rewrap_in_system(
    sessions: async_sessionmaker[AsyncSession], provider: object
) -> RewrapReport:
    """Run one rotation pass the way an operator's sweep does: in the system scope."""
    async with _scoped(sessions, system=SWEEP_REASON) as db:
        report = await rewrap_org_deks(db, provider=provider)
        await db.commit()
        return report


# --- creation and recovery ----------------------------------------------------


async def test_first_use_creates_one_wrapped_generation(sessions, org_id) -> None:
    provider = DeterministicKEKProvider()
    async with _scoped(sessions, org=org_id) as db:
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
    async with _scoped(sessions, org=org_id) as db:
        async with org_dek(db, org_id, provider=provider) as fernet:
            token = fernet.encrypt(b"phase 5.2.1")
            await db.commit()
    before = token

    async with _scoped(sessions, org=org_id) as db:
        async with org_dek(db, org_id, provider=provider) as fernet:
            assert fernet.decrypt(before) == b"phase 5.2.1"
        _, generation = await _stored(db, org_id)

    assert generation == 1, "recovery must not generate a second DEK"


async def test_unknown_organization_is_named(sessions) -> None:
    provider = DeterministicKEKProvider()
    unknown = uuid.uuid4()
    async with _scoped(sessions, org=unknown) as db:
        with pytest.raises(UnknownOrganizationError):
            async with org_dek(db, unknown, provider=provider):
                pass  # pragma: no cover - the context manager raises first


async def test_no_plaintext_dek_is_stored_or_logged(sessions, org_id) -> None:
    """Neither the column, nor an event, nor an error carries the key."""
    provider = DeterministicKEKProvider()
    with structlog.testing.capture_logs() as logs:
        async with _scoped(sessions, org=org_id) as db:
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
        async with _scoped(sessions, org=org_id) as db:
            async with org_dek(db, org_id, provider=provider) as fernet:
                tokens[index] = fernet.encrypt(b"concurrent first use")
                # Committing inside the block is what a request handler does at the
                # end of its unit of work; it is also what releases the claim for
                # the requests queued behind the winner.
                await db.commit()

    await asyncio.gather(*(first_use(i) for i in range(6)))

    assert len(tokens) == 6
    # Every racer generated and wrapped a candidate before any claim landed: this
    # is the interleaving the test is about, not six sequential calls.
    assert provider.wraps == 6, "the racers did not actually overlap"
    async with _scoped(sessions, org=org_id) as db:
        ciphertext, generation = await _stored(db, org_id)
        # One authoritative row, not six attempts' worth of rows: "exactly one
        # envelope per organization" is a constraint, and the race must respect it.
        assert await _row_count(db, org_id) == 1

    # One generation, and every caller's ciphertext decrypts under every other
    # caller's DEK: the losers adopted the winner's envelope instead of keeping
    # their own candidate.
    assert generation == 1
    assert ciphertext is not None
    for index, token in tokens.items():
        for other in tokens:
            if other == index:
                continue
            async with _scoped(sessions, org=org_id) as db:
                async with org_dek(db, org_id, provider=provider) as fernet:
                    assert fernet.decrypt(token) == b"concurrent first use"


async def test_a_lost_race_discards_its_candidate(sessions, org_id) -> None:
    """The loser adopts the winner; its own wrapped candidate is never stored."""
    provider = DeterministicKEKProvider()
    async with _scoped(sessions, org=org_id) as db:
        async with org_dek(db, org_id, provider=provider) as winner:
            winner_token = winner.encrypt(b"winner")
            await db.commit()

    # A second, sequential call is the "late" case of the same race.
    async with _scoped(sessions, org=org_id) as db:
        async with org_dek(db, org_id, provider=provider) as late:
            assert late.decrypt(winner_token) == b"winner"
            await db.commit()
        ciphertext, generation = await _stored(db, org_id)

    assert generation == 1
    assert ciphertext is not None


# --- tenant and context isolation ---------------------------------------------


async def test_envelope_access_requires_the_matching_scope(owner, second_org, sessions) -> None:
    """The database is not touched when the scope does not authorize the row.

    This is the F1 access model in one test. The check has to be an explicit
    refusal rather than a policy-filtered empty result, because "no rows" is
    indistinguishable from "this organization has no DEK yet" — and the service
    responds to *that* by minting one. So: an unscoped session, and a session
    scoped to a *different* organization, must both fail loudly, and neither may
    leave an envelope behind.
    """
    provider = DeterministicKEKProvider()
    mine = uuid.UUID(owner["active_organization_id"])
    other = uuid.UUID(second_org["id"])

    # (a) no scope at all.
    async with sessions() as db:
        with pytest.raises(TenancyScopeError):
            async with org_dek(db, mine, provider=provider):
                pass  # pragma: no cover - refused before any read
        with pytest.raises(TenancyScopeError):
            await db.execute(select(OrganizationDekEnvelope))
        await db.rollback()

    # (b) an organization scope for somebody else.
    async with _scoped(sessions, org=other) as db:
        with pytest.raises(TenancyScopeError):
            async with org_dek(db, mine, provider=provider):
                pass  # pragma: no cover - refused before any read
        await db.rollback()

    # Nothing was created for either organization by the refused calls, and the
    # unscoped read of a tenant table did not quietly return every row.
    async with _scoped(sessions, system=SWEEP_REASON) as db:
        assert await _row_count(db, mine) == 0
        assert await _row_count(db, other) == 0


async def test_an_organization_scope_cannot_read_another_tenants_envelope(
    owner, second_org, sessions
) -> None:
    """An ordinary organization read cannot reach a different tenant's envelope.

    Two independent nets are asserted: the ORM guard (the loader criteria add
    ``org_id``, and a query that asks for another organization's row returns
    nothing) and the service's own scope check. The raw-SQL half — which is what
    proves PostgreSQL would refuse even without the ORM — lives in
    ``test_tenant_isolation.py`` next to the other RLS probes.
    """
    provider = DeterministicKEKProvider()
    mine = uuid.UUID(owner["active_organization_id"])
    theirs = uuid.UUID(second_org["id"])

    async with _scoped(sessions, org=theirs) as db:
        async with org_dek(db, theirs, provider=provider):
            await db.commit()
        their_ciphertext, _ = await _stored(db, theirs)
    assert their_ciphertext is not None

    async with _scoped(sessions, org=mine) as db:
        # Asking for the other tenant's row by its key: no rows, not their rows.
        found = (
            (
                await db.execute(
                    select(OrganizationDekEnvelope.dek_ciphertext).where(
                        OrganizationDekEnvelope.org_id == theirs
                    )
                )
            )
            .scalars()
            .all()
        )
        assert found == []
        assert await _stored(db, theirs) == (None, 0)
        # And the service refuses the organization itself rather than minting it one.
        with pytest.raises(TenancyScopeError):
            async with org_dek(db, theirs, provider=provider):
                pass  # pragma: no cover


async def test_organizations_get_independent_deks(owner, second_org, sessions) -> None:
    provider = DeterministicKEKProvider()
    other_id = uuid.UUID(second_org["id"])
    mine_id = uuid.UUID(owner["active_organization_id"])

    async with _scoped(sessions, org=mine_id) as db:
        async with org_dek(db, mine_id, provider=provider) as mine:
            mine_token = mine.encrypt(b"tenant A")
            mine_key = _plaintext_key(mine)
            await db.commit()

    async with _scoped(sessions, org=other_id) as db:
        async with org_dek(db, other_id, provider=provider) as theirs:
            theirs_key = _plaintext_key(theirs)
            await db.commit()

    # Different key material, and not merely a different label: the other tenant's
    # ciphertext is unreadable under this DEK.
    assert mine_key != theirs_key
    with pytest.raises(InvalidToken):
        theirs.decrypt(mine_token)


async def test_a_replayed_envelope_does_not_unwrap_for_another_organization(
    owner, second_org, sessions
) -> None:
    """Copying org A's wrapped DEK onto org B's row must fail to unwrap.

    This is the attack the binding exists for: a single UPDATE, no provider access,
    and with beside-ciphertext metadata it would simply work. The copy is written
    as the application role in the system scope, i.e. with every legitimate
    database permission to do it — and it still does not yield key material.
    """
    provider = DeterministicKEKProvider()
    victim = uuid.UUID(owner["active_organization_id"])
    attacker = uuid.UUID(second_org["id"])

    async with _scoped(sessions, org=victim) as db:
        async with org_dek(db, victim, provider=provider):
            await db.commit()
        ciphertext, generation = await _stored(db, victim)
    assert ciphertext is not None
    assert ciphertext.startswith("v1:test:")
    assert generation == 1

    async with _scoped(sessions, system=SWEEP_REASON) as db:
        await _set_stored(db, attacker, ciphertext, generation)

    async with _scoped(sessions, org=attacker) as db:
        with pytest.raises(KEKContextMismatchError):
            async with org_dek(db, attacker, provider=provider):
                pass  # pragma: no cover - the provider refuses the binding


async def test_a_dek_replayed_as_another_generation_fails(sessions, org_id) -> None:
    provider = DeterministicKEKProvider()
    async with _scoped(sessions, org=org_id) as db:
        async with org_dek(db, org_id, provider=provider):
            await db.commit()

    async with _scoped(sessions, org=org_id) as db:
        ciphertext, _ = await _stored(db, org_id)
        assert ciphertext is not None

    async with _scoped(sessions, system=SWEEP_REASON) as db:
        # Same organization, same ciphertext, different generation: still refused,
        # because the generation is part of what the ciphertext authenticates.
        await _set_stored(db, org_id, ciphertext, 3)

    async with _scoped(sessions, org=org_id) as db:
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
    async with _scoped(sessions, system=SWEEP_REASON) as db:
        await _set_stored(db, org_id, foreign.encode(), 1)

    async with _scoped(sessions, org=org_id) as db:
        with pytest.raises(KEKEnvelopeError, match="configured provider"):
            async with org_dek(db, org_id, provider=provider):
                pass  # pragma: no cover


async def test_a_corrupt_stored_envelope_is_refused_before_the_provider(sessions, org_id) -> None:
    provider = DeterministicKEKProvider()
    async with _scoped(sessions, system=SWEEP_REASON) as db:
        await _set_stored(db, org_id, "not-an-envelope", 1)

    async with _scoped(sessions, org=org_id) as db:
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
    """The wrapped DEK exists in exactly one place: the envelope table, wrapped.

    Asserted against the API rather than against the ORM, because the ORM is what
    already carries the column — what has to stay true is that no response model
    exposes it, which is the same response-allowlist check the certificate models use.
    The organization is given a real envelope first, so the assertion is about a
    populated row rather than an empty one. (The organization listing is the read
    model that used to carry the column directly, so it is the one worth pinning.)
    """
    provider = DeterministicKEKProvider()
    async with _scoped(sessions, org=org_id) as db:
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
    """Failure fails closed: no envelope row, nothing usable stored.

    "No envelope" is now the *absence* of a row rather than a NULL column, and
    that is asserted explicitly: a placeholder row with generation 0 would be a
    different (and worse) state to leave behind.
    """
    failing = _FailingProvider()
    async with _scoped(sessions, org=org_id) as db:
        with pytest.raises(KEKUnavailableError):
            async with org_dek(db, org_id, provider=failing):
                pass  # pragma: no cover
        await db.rollback()
        ciphertext, generation = await _stored(db, org_id)
        row_count = await _row_count(db, org_id)

    assert failing.calls == 1
    assert (ciphertext, generation) == (None, 0)
    assert row_count == 0, "a failed provider call must not claim a generation"


async def test_recovery_after_a_failed_wrap_still_works(sessions, org_id) -> None:
    """The organization is not poisoned by an outage that happened before it had a DEK."""
    failing = _FailingProvider()
    async with _scoped(sessions, org=org_id) as db:
        with pytest.raises(KEKUnavailableError):
            async with org_dek(db, org_id, provider=failing):
                pass  # pragma: no cover
        await db.rollback()

    provider = DeterministicKEKProvider()
    async with _scoped(sessions, org=org_id) as db:
        async with org_dek(db, org_id, provider=provider) as fernet:
            token = fernet.encrypt(b"after the outage")
            await db.commit()
        _, generation = await _stored(db, org_id)
    assert generation == 1

    async with _scoped(sessions, org=org_id) as db:
        async with org_dek(db, org_id, provider=provider) as fernet:
            assert fernet.decrypt(token) == b"after the outage"


# --- KEK rotation -------------------------------------------------------------


async def test_rewrap_moves_the_ciphertext_without_moving_the_key(sessions, org_id) -> None:
    """A KEK-only rotation: new version, same DEK, no plaintext in this process."""
    provider = DeterministicKEKProvider()
    async with _scoped(sessions, org=org_id) as db:
        async with org_dek(db, org_id, provider=provider) as fernet:
            token = fernet.encrypt(b"survives rotation")
            await db.commit()
        before, generation = await _stored(db, org_id)

    assert before is not None
    provider.rotate()  # the operator rotated the KEK in the provider

    report = await _rewrap_in_system(sessions, provider)
    async with _scoped(sessions, org=org_id) as db:
        after, generation_after = await _stored(db, org_id)

    assert report.scanned == 1
    assert report.rewrapped == 1
    assert report.failed == 0
    assert after is not None and after != before
    assert WrappedKey.decode(after).key_version == "2"
    assert generation_after == generation == 1, "a KEK rotation is not a DEK rotation"

    async with _scoped(sessions, org=org_id) as db:
        async with org_dek(db, org_id, provider=provider) as fernet:
            assert fernet.decrypt(token) == b"survives rotation"


async def test_rewrap_requires_the_system_scope(sessions, org_id) -> None:
    """A rotation that ran under one organization's scope would look successful
    while rotating only that tenant, so it is refused outright: the sweep has to
    visit every organization's envelope, and no organization scope may do that."""
    provider = DeterministicKEKProvider()
    async with _scoped(sessions, org=org_id) as db:
        async with org_dek(db, org_id, provider=provider):
            await db.commit()
        with pytest.raises(TenancyScopeError):
            await rewrap_org_deks(db, provider=provider)


async def test_rewrap_is_idempotent(sessions, org_id) -> None:
    provider = DeterministicKEKProvider()
    async with _scoped(sessions, org=org_id) as db:
        async with org_dek(db, org_id, provider=provider):
            await db.commit()

    await _rewrap_in_system(sessions, provider)
    async with _scoped(sessions, org=org_id) as db:
        first, _ = await _stored(db, org_id)

    second_report = await _rewrap_in_system(sessions, provider)
    async with _scoped(sessions, org=org_id) as db:
        second, _ = await _stored(db, org_id)

    assert first == second
    assert second_report.unchanged == 1
    assert second_report.rewrapped == 0


async def test_a_rewrap_provider_failure_leaves_the_envelope_byte_identical(
    sessions, org_id
) -> None:
    """The window between "the provider was asked" and "the row was written" is empty.

    A rotation that cannot reach its provider must leave the stored envelope exactly
    as it was — not partially rewritten, not regenerated — and the next pass must
    still be able to rotate it. That is the safe-retry property: the failure is
    reported per organization and costs nothing but a retry.
    """
    provider = DeterministicKEKProvider()
    async with _scoped(sessions, org=org_id) as db:
        async with org_dek(db, org_id, provider=provider) as fernet:
            token = fernet.encrypt(b"survives a failed rotation")
            await db.commit()
        before, generation = await _stored(db, org_id)
    assert before is not None

    failing = _FailingRewrapProvider()
    failing.rotate()  # the same key version the healthy provider was moved to
    report = await _rewrap_in_system(sessions, failing)

    async with _scoped(sessions, org=org_id) as db:
        after_failure, generation_after = await _stored(db, org_id)
        assert await _row_count(db, org_id) == 1

    assert failing.calls == 1
    assert report.scanned == 1
    assert report.failed == 1
    assert report.rewrapped == 0
    assert report.failures[0][0] == org_id
    assert (after_failure, generation_after) == (before, generation), (
        "a provider failure must not move the stored envelope or its generation"
    )

    # The retry is safe: the same rotation succeeds once the provider is reachable,
    # and the DEK is untouched throughout.
    healthy = DeterministicKEKProvider()
    healthy.rotate()
    retry = await _rewrap_in_system(sessions, healthy)

    async with _scoped(sessions, org=org_id) as db:
        recovered, recovered_generation = await _stored(db, org_id)
        async with org_dek(db, org_id, provider=healthy) as fernet:
            assert fernet.decrypt(token) == b"survives a failed rotation"

    assert retry.rewrapped == 1
    assert recovered is not None and recovered != before
    assert WrappedKey.decode(recovered).key_version == "2"
    assert recovered_generation == 1


async def test_rewrap_reports_a_bad_row_without_stopping_the_pass(
    owner, second_org, sessions
) -> None:
    """One unreadable envelope must not block everyone else's rotation."""
    provider = DeterministicKEKProvider()
    good = uuid.UUID(owner["active_organization_id"])
    bad = uuid.UUID(second_org["id"])
    async with _scoped(sessions, org=good) as db:
        async with org_dek(db, good, provider=provider):
            await db.commit()

    async with _scoped(sessions, system=SWEEP_REASON) as db:
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
    report = await _rewrap_in_system(sessions, provider)

    assert report.scanned == 2
    assert report.rewrapped == 1
    assert report.failed == 1
    assert report.failures[0][0] == bad
    # The reason is sanitized by construction: it is a provider error message,
    # never key material.
    assert "not-a-key" not in report.failures[0][1]


# --- F2: the compare-and-set on the stored envelope ---------------------------


async def test_concurrent_rewraps_cannot_regress_the_stored_envelope(sessions, org_id) -> None:
    """Two passes with the same snapshot: one writes, the loser defers.

    Both passes read the same envelope and both compute a replacement, but only
    one may write. The loser's compare-and-set finds a row that is no longer the
    value it read, so it re-reads and stands down — which is why the stored
    envelope ends up on the current key version and never on the snapshot that was
    superseded. Without the compare-and-set this is the exact shape of a
    rotation that silently reverts a newer envelope.
    """
    provider = _BarrierRewrapProvider(parties=2)
    async with _scoped(sessions, org=org_id) as db:
        async with org_dek(db, org_id, provider=provider) as fernet:
            token = fernet.encrypt(b"one winner")
            await db.commit()
        before, generation = await _stored(db, org_id)
    assert before is not None

    provider.rotate()  # version 2: both passes now have work to do

    reports = await asyncio.gather(
        _rewrap_in_system(sessions, provider),
        _rewrap_in_system(sessions, provider),
    )

    async with _scoped(sessions, org=org_id) as db:
        after, generation_after = await _stored(db, org_id)
        async with org_dek(db, org_id, provider=provider) as fernet:
            assert fernet.decrypt(token) == b"one winner"

    # Both passes really did overlap: the barrier only releases once both have
    # entered the provider, and the loser's retry is the third call.
    assert provider.rewraps >= 3, "the passes did not overlap"
    assert sorted(report.rewrapped for report in reports) == [0, 1], (
        "exactly one pass may write the row"
    )
    assert sorted(report.unchanged for report in reports) == [0, 1], (
        "the losing pass must re-read and find its work already done"
    )
    assert all(report.failed == 0 and report.contended == 0 for report in reports)
    assert after is not None and after != before
    assert WrappedKey.decode(after).key_version == "2"
    assert generation_after == generation == 1, "a KEK rotation is not a DEK rotation"


async def test_a_stale_snapshot_cannot_overwrite_a_newer_envelope(sessions, org_id) -> None:
    """A pass holding an older snapshot must not force it onto the row.

    The blocked pass is holding a genuine v2 envelope derived from a v1 snapshot
    while a second pass moves the row to v3. When it is released its compare-and-set
    matches nothing, it re-reads, sees the row is already current, and stops. The
    stored envelope is byte-identical to the newer one — the stale write never
    landed — and the DEK is unchanged, so the earlier token still decrypts.
    """
    provider = _StaleSnapshotProvider()
    async with _scoped(sessions, org=org_id) as db:
        async with org_dek(db, org_id, provider=provider) as fernet:
            token = fernet.encrypt(b"survives a lost race")
            await db.commit()
        original, generation = await _stored(db, org_id)
    assert original is not None

    provider.rotate()  # version 2 — the snapshot the blocked pass will hold

    blocked = asyncio.create_task(_rewrap_in_system(sessions, provider))
    await asyncio.wait_for(provider.first_call_started.wait(), timeout=5)
    stale_envelope = provider.stale_result
    assert stale_envelope is not None
    assert stale_envelope.key_version == "2", "the blocked pass must hold a v2 envelope"

    # A second pass moves the row to version 3 while the first one is held.
    provider.rotate()  # version 3
    fresh_report = await _rewrap_in_system(sessions, provider)
    async with _scoped(sessions, org=org_id) as db:
        newer, _ = await _stored(db, org_id)
    assert newer is not None and newer != original

    provider.release_first.set()
    stale_report = await asyncio.wait_for(blocked, timeout=5)

    async with _scoped(sessions, org=org_id) as db:
        authoritative, generation_after = await _stored(db, org_id)
        async with org_dek(db, org_id, provider=provider) as fernet:
            assert fernet.decrypt(token) == b"survives a lost race"

    assert fresh_report.rewrapped == 1
    assert stale_report.rewrapped == 0, "the stale pass must not write"
    assert stale_report.unchanged == 1, "it re-read the row and found it current"
    assert stale_report.contended == 0 and stale_report.failed == 0
    assert authoritative == newer, "the newer envelope is byte-for-byte intact"
    assert authoritative != stale_envelope.encode(), (
        "the older envelope the blocked pass was holding must never be stored"
    )
    assert WrappedKey.decode(authoritative).key_version == "3"
    assert generation_after == generation == 1


async def test_a_repeatedly_losing_rewrap_stops_after_a_bounded_number_of_attempts(
    sessions, org_id
) -> None:
    """Retries are bounded, and a pass that keeps losing never writes at all.

    A competing writer moves the row on before every one of the pass's writes, so
    every compare-and-set loses. The pass must give up after its documented number
    of attempts, report the row as contended, and leave the last *winning* writer's
    envelope in place — a pass that retried forever would be a rotation that can
    never be observed to finish, and one that forced its own snapshot would be the
    regression this whole mechanism exists to prevent.
    """
    provider = _PingPongProvider(rounds=_REWRAP_ATTEMPTS)
    context = EncryptionContext(org_id=org_id, purpose=PURPOSE_ORG_DEK, dek_generation=1)
    # A competitor at a different key version: its envelopes are valid for this
    # binding, need rewriting by the pass's provider, and are never equal to what
    # the pass read (a fresh DEK each round), so the compare-and-set loses every time.
    competitor = DeterministicKEKProvider()
    competitor.rotate()

    async with _scoped(sessions, org=org_id) as db:
        async with org_dek(db, org_id, provider=provider):
            await db.commit()
    provider.rotate()  # version 2
    provider.rotate()  # version 3 — the pass has two versions of work to do

    async with _scoped(sessions, org=org_id) as db:
        initial, generation = await _stored(db, org_id)
    assert initial is not None

    losing = asyncio.create_task(_rewrap_in_system(sessions, provider))
    written: list[str] = []
    for _ in range(_REWRAP_ATTEMPTS):
        await asyncio.wait_for(provider.ready_to_write.wait(), timeout=5)
        envelope = await competitor.wrap_dek(Fernet.generate_key(), context)
        async with _scoped(sessions, system=SWEEP_REASON) as db:
            await _set_stored(db, org_id, envelope.encode(), generation)
        written.append(envelope.encode())
        provider.competitor_moved.set()

    report = await asyncio.wait_for(losing, timeout=5)

    async with _scoped(sessions, org=org_id) as db:
        final, generation_after = await _stored(db, org_id)

    assert provider.calls == _REWRAP_ATTEMPTS, "the retry bound must be the documented one"
    assert report.rewrapped == 0
    assert report.contended == 1
    assert report.failed == 0
    assert final == written[-1], "the last winning writer's envelope is the stored one"
    assert final not in written[:-1], "no earlier snapshot was restored"
    assert generation_after == generation == 1
