"""Phase 5.3.2 — manual DNS-01 end to end, with a fake CA and a fake resolver.

The Pebble suite proves a manual certificate is issued by a *real* CA through the
real client. This module proves the parts a fake CA is better at isolating, because
they are about the platform's own bookkeeping rather than any CA's behaviour:

* **Manual mode needs no DNS credential.** The certificate names no provider, the
  flow never calls a provider at all — not to publish and not to clean up — and the
  result is a generation waiting for a human rather than a failure.
* **A confirmation is a request to re-observe, not a verdict.** Confirming while the
  record is absent records the confirmation, observes, and leaves ``ready`` false;
  the generation does not move and no attempt is spent. The CA is never told.
* **Repeating it is idempotent.** The first confirmation's timestamp survives, the
  observation is simply run again, and no second order is placed.
* **The value has exactly one exit.** It appears in the organization-scoped
  challenge endpoint and nowhere else — not in a listing, not in a detail, not in an
  event payload, not in an audit entry — and another organization's id is a 404.
* **Cleanup is instructions, never a delete.** Nothing is removed from the zone by
  this platform, and after issuance the operator is told exactly which values are
  obsolete and to keep everything else at the name.
* **An interrupted wait is recovered, not re-ordered.** A worker that died mid-resume
  is recorded as lost work; a generation that is merely *waiting* is not.

What these tests deliberately do not use is a real zone: ``_NeverCalled`` fails the
test if the manual flow touches a DNS provider, which is the property manual mode
exists to guarantee.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import uuid
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from app.core.config import get_settings
from app.core.tenancy import apply_scope_to_session, org_scope
from app.models import Certificate, CertificateGeneration, SystemEvent
from app.models.enums import AcmeDirectory, DomainStatus
from app.models.observability import AuditLog
from app.providers.dns import CredentialCheck
from app.services import (
    certificate_order,
    dns_propagation,
    dns_provider_service,
    dns_verifier,
)
from app.services.acme import (
    AcmeChallenge,
    AcmeError,
    AcmeOrder,
    AuthorizationState,
    IssuedChain,
)
from app.services.certificate_issuance import (
    CODE_AWAITING_MANUAL,
    CODE_MANUAL_CHALLENGE_INVALID,
    issue_generation,
)
from app.services.dns_verifier import (
    STATUS_NO_TXT,
    STATUS_OK,
    ServerAnswer,
    TxtObservation,
)
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID
from sqlalchemy import select

from .helpers import API, assert_error_code

pytestmark = pytest.mark.integration

#: The delegated NS set and the addresses the resolver stub answers from. Two of
#: each, because the propagation policy is per *server*: one agreeing server is not
#: a delegation, and every test below is exercising the same judging code the real
#: wire path uses.
NS_SET = ("ns1.example.net", "ns2.example.net")
NS_ADDRESSES = ("192.0.2.1", "192.0.2.2")

#: What the authoritative servers currently answer, keyed by record name. The
#: observer reads this and the tests write to it — publication, in one dict.
ZONE: dict[str, set[str]] = {}


def _observe(name: str, **_kwargs: Any) -> TxtObservation:
    """What the "authoritative servers" say about *name*, with per-server answers.

    Both servers always answer. Absence is ``NO_TXT`` rather than silence, so the
    round is judged as "the zone does not hold this value" — a verdict — instead of
    as "nothing was reachable", which would be a different (and much weaker) test.
    """
    values = tuple(sorted(ZONE.get(name, ())))
    status = STATUS_OK if values else STATUS_NO_TXT
    answers = tuple(
        ServerAnswer(server=address, status=status, values=values) for address in NS_ADDRESSES
    )
    return TxtObservation(status, values=values, nameservers=NS_SET, server_answers=answers)


@pytest.fixture(autouse=True)
def _dns(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """One resolver stub for both the ownership check and the propagation check.

    ``dns_propagation.observe_txt_record`` is patched because that is exactly where
    ``check_once`` reads its default observer — the confirmation endpoint therefore
    runs the *real* judging code against this zone rather than a parallel opinion of
    its own. ``dns_verifier.observe`` is the separate seam domain ownership uses.
    """
    ZONE.clear()
    monkeypatch.setattr(dns_verifier, "observe", _observe)
    monkeypatch.setattr(dns_propagation, "observe_txt_record", _observe)
    yield
    ZONE.clear()


class _FakeCloudflare:
    """Credential verification only; present so an automated row can be created."""

    name = "cloudflare"
    required_fields: tuple[str, ...] = ("api_token",)

    async def verify_creds(self, credentials: dict[str, str]) -> CredentialCheck:
        return CredentialCheck(ok=True, scopes={"zone_names": ["example.com"]})


@pytest.fixture(autouse=True)
def _credential_seam(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(dns_provider_service, "provider_for", lambda kind: _FakeCloudflare())


class _NeverCalled:
    """A DNS provider that fails the test the moment manual mode touches it.

    Not a recorder: the claim is that a manual certificate has no automated
    publisher at all, so any call — publish, find, delete — is a defect rather than
    something to assert about afterwards.
    """

    name = "must-never-be-used"

    def _fail(self, *args: Any, **kwargs: Any) -> Any:
        raise AssertionError("the manual DNS-01 flow must never call a DNS provider")

    resolve_zone = create_txt = find_txt = delete_txt = _fail


def _challenge_value(order_number: int, index: int) -> str:
    """A 43-character base64url TXT digest, distinct per order and identifier.

    The shape matters: the order document validates a stored value against exactly
    this pattern before showing it to an operator.
    """
    digest = hashlib.sha256(f"order-{order_number}-challenge-{index}".encode()).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


class _FakeAcme:
    """The CA side of the seam, sharing an order store across two sessions.

    A manual issuance opens two sessions separated by an operator: one places the
    order, one resumes it and finalizes. The order must therefore outlive the first
    session — and its challenge URLs and values must be identical when it comes
    back, because the operator published *those* values.
    """

    directory = AcmeDirectory.STAGING

    def __init__(self, ca: _ManualCa) -> None:
        self.ca = ca
        self.answered: list[str] = []
        self.closed = False
        self.resumed: list[str] = []

    async def register_account(self, *, contact_email: str | None = None) -> str:
        return "https://ca.test/kid/1"

    async def create_order(self, *, csr_pem: bytes, identifiers: tuple[str, ...]) -> AcmeOrder:
        order_number = self.ca.orders_placed + 1
        challenges = []
        for index, identifier in enumerate(identifiers):
            wildcard = identifier.startswith("*.")
            base = identifier[2:] if wildcard else identifier
            token = f"token-{order_number}-{index}"
            challenges.append(
                AcmeChallenge(
                    identifier=base,
                    wildcard=wildcard,
                    authorization_url=f"https://ca.test/{order_number}/authz/{index}",
                    challenge_url=f"https://ca.test/{order_number}/chall/{index}",
                    token=token,
                    record_name=f"_acme-challenge.{base}",
                    record_value=_challenge_value(order_number, index),
                    key_authorization=f"{token}.thumbprint",
                    status="pending",
                )
            )
        order = AcmeOrder(
            order_url=f"https://ca.test/order/{order_number}",
            status="pending",
            challenges=tuple(challenges),
            expires_at=datetime.now(UTC) + timedelta(days=7),
            identifiers=identifiers,
        )
        self.ca.orders_placed = order_number
        self.ca.order = order
        return order

    async def resume_order(self, *, order_url: str) -> AcmeOrder:
        self.resumed.append(order_url)
        if self.ca.unusable or self.ca.order is None or self.ca.order.order_url != order_url:
            raise AcmeError(
                "the recorded order is no longer usable at the certificate authority",
                code="ACME_ORDER_UNUSABLE",
            )
        return self.ca.order

    async def accept_challenge(self, *, challenge_url: str) -> None:
        self.answered.append(challenge_url)

    async def poll_authorization(
        self, *, authorization_url: str, timeout_seconds: float
    ) -> AuthorizationState:
        if self.ca.reject:
            return AuthorizationState(
                status="invalid",
                error_code="unauthorized",
                error_detail="no TXT record found at _acme-challenge",
            )
        return AuthorizationState(status="valid")

    async def finalize_order(self, *, csr_pem: bytes, timeout_seconds: float) -> IssuedChain:
        csr = x509.load_pem_x509_csr(csr_pem)
        ca_key = ec.generate_private_key(ec.SECP256R1())
        sans = csr.extensions.get_extension_for_class(
            x509.SubjectAlternativeName
        ).value.get_values_for_type(x509.DNSName)
        leaf = (
            x509.CertificateBuilder()
            .subject_name(csr.subject)
            .issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Fake CA")]))
            .public_key(csr.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(UTC) - timedelta(minutes=5))
            .not_valid_after(datetime.now(UTC) + timedelta(days=90))
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName(name) for name in sans]),
                critical=False,
            )
            .sign(ca_key, hashes.SHA256())
        )
        assert self.ca.order is not None
        return IssuedChain(
            fullchain_pem=leaf.public_bytes(serialization.Encoding.PEM).decode("ascii"),
            order_url=self.ca.order.order_url,
        )

    async def close(self) -> None:
        self.closed = True


class _ManualCa:
    """A session factory whose order survives across the operator's pause."""

    def __init__(self, *, unusable: bool = False, reject: bool = False) -> None:
        self.unusable = unusable
        self.reject = reject
        self.order: AcmeOrder | None = None
        self.orders_placed = 0
        self.sessions: list[_FakeAcme] = []

    @asynccontextmanager
    async def open(
        self, *, directory: AcmeDirectory, account_key_pem: str, account_url: str | None
    ) -> AsyncIterator[_FakeAcme]:
        assert directory is AcmeDirectory.STAGING
        assert account_key_pem.startswith("-----BEGIN PRIVATE KEY-----")
        session = _FakeAcme(self)
        self.sessions.append(session)
        try:
            yield session
        finally:
            await session.close()


# --- setup ---------------------------------------------------------------------


@asynccontextmanager
async def _scoped(db: Any, org_id: uuid.UUID) -> AsyncIterator[Any]:
    with org_scope(org_id):
        await apply_scope_to_session(db)
        yield db


async def _create_domain(client: Any, owner: dict, name: str) -> dict:
    created = await client.post(f"{API}/domains", headers=owner["headers"], json={"name": name})
    assert created.status_code == 201, created.text
    body = created.json()
    # The ownership observer is asked for the *domain* name and resolves the
    # ``_nexusops.`` record itself, so the stub answers at both names.
    token = body["verification"]["record_value"]
    ZONE[name] = {token}
    ZONE[body["verification"]["record_name"]] = {token}

    from app.tasks.domain_routing import _verify

    outcome = await _verify(uuid.UUID(body["id"]), trigger="user")
    assert outcome["status"] == DomainStatus.VERIFIED.value, outcome
    detail = await client.get(f"{API}/domains/{body['id']}", headers=owner["headers"])
    assert detail.status_code == 200, detail.text
    return detail.json()


def _state(value: Any) -> str:
    return str(getattr(value, "value", value))


@asynccontextmanager
async def _request(
    client: Any,
    owner: dict,
    org_db: Any,
    *,
    name: str,
    identifiers: list[str] | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """A verified domain and a **manual** certificate request with no credential."""
    domain = await _create_domain(client, owner, name)
    created = await client.post(
        f"{API}/certificates",
        headers=owner["headers"],
        json={
            "domain_id": domain["id"],
            "identifiers": identifiers or [name],
            "dns_mode": "manual",
        },
    )
    assert created.status_code == 201, created.text
    certificate = created.json()
    org_id = uuid.UUID(owner["active_organization_id"])
    async with _scoped(org_db, org_id):
        generation = await org_db.get(
            CertificateGeneration, uuid.UUID(certificate["latest_generation"]["id"])
        )
        certificate_row = await org_db.get(Certificate, uuid.UUID(certificate["id"]))
        assert generation is not None and certificate_row is not None
    # Yield *outside* the scope: the test runs in this context, and a scope left
    # open here would make a request for another organization refuse to switch.
    yield {
        "org_id": org_id,
        "domain": domain,
        "certificate": certificate,
        "certificate_row": certificate_row,
        "generation": generation,
        "generation_id": certificate["latest_generation"]["id"],
    }


async def _reload(db: Any, setup: dict[str, Any]) -> CertificateGeneration:
    """The generation as it is in the database *now*.

    The API writes the challenge document from its own session, so the instance this
    test holds would otherwise keep the document it was loaded with — which is not
    what a worker dispatch sees when it loads the row.
    """
    async with _scoped(db, setup["org_id"]):
        generation = await db.get(CertificateGeneration, uuid.UUID(setup["generation_id"]))
        assert generation is not None
        await db.refresh(generation)
        return generation


def _document(db_generation: CertificateGeneration) -> dict[str, Any]:
    return certificate_order.load(db_generation)


async def _issue(
    db: Any,
    setup: dict[str, Any],
    ca: _ManualCa,
    *,
    now: datetime | None = None,
) -> Any:
    """One attempt through the real flow, with the manual seams injected."""
    generation = await _reload(db, setup)
    with org_scope(setup["org_id"]):
        await apply_scope_to_session(db)
        result = await issue_generation(
            db,
            generation,
            certificate=setup["certificate_row"],
            settings=get_settings(),
            now=now or datetime.now(UTC) + timedelta(seconds=1),
            session_factory=ca.open,
            provider_factory=lambda kind: _NeverCalled(),
            observer=_observe,
            checkpoint=db.commit,
        )
        await db.commit()
    return result


async def _events(db: Any, org_id: uuid.UUID, event_type: str) -> list[SystemEvent]:
    async with _scoped(db, org_id):
        rows = await db.execute(
            select(SystemEvent)
            .where(SystemEvent.type == event_type)
            .order_by(SystemEvent.created_at)
        )
        return list(rows.scalars())


def _publish(document: dict[str, Any]) -> None:
    """Do what the operator does: put every instructed value in the zone."""
    for entry in certificate_order.manual_instructions(document):
        ZONE.setdefault(entry["record_name"], set()).add(entry["record_value"])


# --- 1. the workflow itself -----------------------------------------------------


async def test_a_manual_certificate_is_issued_without_any_dns_credential(
    client: Any, owner: dict, org_db: Any
) -> None:
    """The whole manual path: wait, publish, confirm, issue — with no provider.

    Every provider call would have failed the test (``_NeverCalled``), so the
    issuance below is also the proof that manual mode does not quietly fall back to
    an automated publisher when one is absent.
    """
    ca = _ManualCa()
    async with _request(client, owner, org_db, name="manual-one.example.com") as setup:
        # No credential is attached, and the read model says the customer publishes.
        assert setup["certificate_row"].dns_provider_id is None
        assert _state(setup["certificate_row"].dns_mode) == "manual"
        assert setup["certificate"]["dns_mode"] == "manual"

        first = await _issue(org_db, setup, ca)
        assert first.ok is False
        assert first.waiting is True
        assert first.code == CODE_AWAITING_MANUAL
        assert _state(first.state) == "AWAITING_MANUAL"
        assert ca.orders_placed == 1

        generation = await _reload(org_db, setup)
        assert _state(generation.state) == "AWAITING_MANUAL"
        # Waiting is not failing: nothing is scheduled, nothing is recorded as an
        # error, and no key exists yet because nothing has been issued.
        assert generation.next_attempt_at is None
        assert generation.last_error == ""
        assert generation.key_ciphertext is None
        document = _document(generation)

        # The instructions exist, and they are exactly the CA's challenge values.
        instructions = certificate_order.manual_instructions(document)
        assert len(instructions) == 1
        assert instructions[0]["identifier"] == "manual-one.example.com"
        assert instructions[0]["record_name"] == "_acme-challenge.manual-one.example.com"
        assert instructions[0]["record_value"] == _challenge_value(1, 0)
        assert instructions[0]["problem"] == ""

        # The operator publishes, then confirms through the API.
        _publish(document)
        confirmed = await client.post(
            f"{API}/certificates/{setup['certificate']['id']}/challenge/confirm",
            headers=owner["headers"],
            json={},
        )
        assert confirmed.status_code == 202, confirmed.text
        body = confirmed.json()
        assert body["ready"] is True
        assert body["resume_requested"] is True
        assert body["records"][0]["observed"] is True
        assert body["records"][0]["validated"] is False, "only the CA may validate"
        assert body["state"] == "AWAITING_MANUAL"

        # The resume attempt finishes the order the operator already answered.
        second = await _issue(org_db, setup, ca)
        assert second.ok is True, (second.code, second.message)
        assert _state(second.state) == "ISSUED"
        assert ca.orders_placed == 1, "a resume must not place a second order"
        resumed = ca.sessions[-1]
        assert resumed.resumed == [ca.order.order_url] if ca.order else True
        assert resumed.answered, "the resumed attempt must answer the CA"

        generation = await _reload(org_db, setup)
        async with _scoped(org_db, setup["org_id"]):
            certificate = await org_db.get(Certificate, uuid.UUID(setup["certificate"]["id"]))
            assert certificate is not None
            assert certificate.current_generation_id == generation.id
        assert _state(generation.state) == "ISSUED"
        assert generation.key_ciphertext and generation.chain_ciphertext
        document = _document(generation)
        assert all(
            entry["mode"] == certificate_order.MODE_MANUAL
            for entry in certificate_order.entries(document)
        )
        # Nothing was created by this platform, so nothing may be deleted by it.
        assert certificate_order.pending_cleanup(document) == []
        assert all(
            entry["cleanup"] == certificate_order.CLEANUP_NOT_REQUIRED
            for entry in certificate_order.entries(document)
        )

    # Cleanup is an instruction, and it names the value that is now obsolete.
    final = await client.get(
        f"{API}/certificates/{setup['certificate']['id']}/challenge", headers=owner["headers"]
    )
    assert final.status_code == 200, final.text
    cleanup = final.json()["cleanup"]
    assert cleanup["required"] is True
    assert cleanup["records"][0]["record_name"] == "_acme-challenge.manual-one.example.com"
    assert cleanup["records"][0]["remove_values"] == [_challenge_value(1, 0)]
    assert "did not create" in cleanup["note"]


async def test_a_manual_request_cannot_name_a_provider(client: Any, owner: dict) -> None:
    """``automated`` and ``manual`` are different publishers; one row cannot be both.

    The refusal is by name rather than by silently picking a winner, because either
    choice would be a lie about who is expected to publish the record.
    """
    domain = await _create_domain(client, owner, "manual-conflict.example.com")
    provider = await client.post(
        f"{API}/dns-providers",
        headers=owner["headers"],
        json={
            "name": "Conflict zone",
            "credentials": {"api_token": "not-a-real-token"},
            "zone_allowlist": ["manual-conflict.example.com"],
        },
    )
    assert provider.status_code == 201, provider.text
    refused = await client.post(
        f"{API}/certificates",
        headers=owner["headers"],
        json={
            "domain_id": domain["id"],
            "identifiers": ["manual-conflict.example.com"],
            "dns_mode": "manual",
            "dns_provider_id": provider.json()["id"],
        },
    )
    assert refused.status_code == 422, refused.text
    assert_error_code(refused.json(), "CERTIFICATE_MANUAL_WITH_PROVIDER")


# --- 2. confirming before publishing is not progress ----------------------------


async def test_confirming_while_the_record_is_absent_does_not_advance(
    client: Any, owner: dict, org_db: Any
) -> None:
    """The confirmation is a request to look. Looking found nothing, so nothing moved."""
    ca = _ManualCa()
    async with _request(client, owner, org_db, name="manual-absent.example.com") as setup:
        first = await _issue(org_db, setup, ca)
        assert first.waiting is True

        response = await client.post(
            f"{API}/certificates/{setup['certificate']['id']}/challenge/confirm",
            headers=owner["headers"],
            json={},
        )
        assert response.status_code == 202, response.text
        body = response.json()
        assert body["ready"] is False
        assert body["resume_requested"] is False
        assert body["records"][0]["confirmed"] is True, "the operator did say they published"
        assert body["records"][0]["observed"] is False, "and this platform did not see it"
        assert body["observation"]["status"] == "PENDING"
        assert all(
            answer["serves_expected"] is False for answer in body["observation"]["nameservers"]
        )

        generation = await _reload(org_db, setup)
        assert _state(generation.state) == "AWAITING_MANUAL"
        assert generation.attempt_count == 1, "a failed observation is not an attempt"
        document = _document(generation)

        # A dispatch that arrives anyway is refused without spending an attempt or
        # creating a second order — the record the operator is about to publish is
        # still the record the CA expects.
        again = await _issue(org_db, setup, ca)
        assert again.ok is False
        assert again.code == CODE_AWAITING_MANUAL
        assert ca.orders_placed == 1

        # And the instructions are unchanged: the operator keeps publishing the same
        # value, not a value from an order that was replaced underneath them.
        current = certificate_order.manual_instructions(document)
        assert [entry["record_value"] for entry in current] == [_challenge_value(1, 0)]


# --- 3. idempotence -------------------------------------------------------------


async def test_repeated_confirmations_are_idempotent(client: Any, owner: dict, org_db: Any) -> None:
    """Two confirmations of one record: one timestamp, one order, one re-observation."""
    ca = _ManualCa()
    async with _request(client, owner, org_db, name="manual-repeat.example.com") as setup:
        await _issue(org_db, setup, ca)
        _publish(_document(await _reload(org_db, setup)))

        url = f"{API}/certificates/{setup['certificate']['id']}/challenge/confirm"
        first = await client.post(url, headers=owner["headers"], json={})
        assert first.status_code == 202, first.text
        stamped = first.json()["records"][0]["confirmed_at"]
        assert stamped is not None

        # The record is still there, so this is "check again" rather than an error.
        second = await client.post(url, headers=owner["headers"], json={})
        assert second.status_code == 202, second.text
        body = second.json()
        assert body["records"][0]["confirmed_at"] == stamped
        assert body["ready"] is True
        assert ca.orders_placed == 1

        generation = await _reload(org_db, setup)
        assert generation.attempt_count == 1
        assert _state(generation.state) == "AWAITING_MANUAL"

        # Confirming a certificate that is not waiting for one is a named refusal,
        # not a silent success that would look like progress.
        async with _scoped(org_db, setup["org_id"]):
            generation.state = "PENDING"
            await org_db.commit()
        late = await client.post(url, headers=owner["headers"], json={})
        assert late.status_code == 409, late.text
        assert_error_code(late.json(), "CERTIFICATE_MANUAL_CHALLENGE_NOT_PENDING")


# --- 4. a tampered document is refused ------------------------------------------


async def test_a_persisted_challenge_that_lost_its_shape_is_refused(
    client: Any, owner: dict, org_db: Any
) -> None:
    """The document is validated before it is shown or acted on.

    A truncated value or a reference that names nothing would send an operator to
    publish the wrong record, and a confirmation against it would ask the CA to
    validate a challenge nobody can answer. Both are refused by name instead.
    """
    ca = _ManualCa()
    async with _request(client, owner, org_db, name="manual-tamper.example.com") as setup:
        await _issue(org_db, setup, ca)

        async with _scoped(org_db, setup["org_id"]):
            generation = await org_db.get(CertificateGeneration, uuid.UUID(setup["generation_id"]))
            assert generation is not None
            document = certificate_order.load(generation)
            document["challenges"][0]["record_value"] = "not-a-digest"
            certificate_order.store(generation, document)
            await org_db.commit()

        url = f"{API}/certificates/{setup['certificate']['id']}/challenge"
        shown = await client.get(url, headers=owner["headers"])
        assert shown.status_code == 200, shown.text
        assert shown.json()["records"][0]["problem"] != ""
        assert shown.json()["ready"] is False

        refused = await client.post(f"{url}/confirm", headers=owner["headers"], json={})
        assert refused.status_code == 409, refused.text
        assert_error_code(refused.json(), CODE_MANUAL_CHALLENGE_INVALID)


# --- 5. the value has exactly one exit ------------------------------------------


async def test_the_challenge_value_is_organization_scoped_and_never_in_a_listing(
    client: Any, owner: dict, org_db: Any, second_org: dict
) -> None:
    """One endpoint, one organization, and no copy anywhere else.

    The event payload and the audit entry are checked by *value*, because "we did
    not intend to put it there" is not the property — the property is that the
    string does not occur.
    """
    ca = _ManualCa()
    async with _request(client, owner, org_db, name="manual-scope.example.com") as setup:
        await _issue(org_db, setup, ca)
        value = _challenge_value(1, 0)

        url = f"{API}/certificates/{setup['certificate']['id']}/challenge"
        own = await client.get(url, headers=owner["headers"])
        assert own.status_code == 200, own.text
        assert own.json()["records"][0]["record_value"] == value

        # Another organization: the certificate id is not theirs, so it is the same
        # 404 a random uuid gets — not a 403 that would confirm it exists.
        foreign = await client.get(url, headers=second_org["headers"])
        assert foreign.status_code == 404, foreign.text
        assert_error_code(foreign.json(), "CERTIFICATE_NOT_FOUND")
        foreign_confirm = await client.post(
            f"{url}/confirm", headers=second_org["headers"], json={}
        )
        assert foreign_confirm.status_code == 404, foreign_confirm.text

        # Nothing in the ordinary read model, in either representation.
        detail = await client.get(
            f"{API}/certificates/{setup['certificate']['id']}", headers=owner["headers"]
        )
        listed = await client.get(f"{API}/certificates", headers=owner["headers"])
        assert detail.status_code == 200 and listed.status_code == 200
        for response in (detail, listed):
            assert value not in response.text

        # Nor in the events or the audit trail.
        awaiting = await _events(org_db, setup["org_id"], "CERTIFICATE_AWAITING_MANUAL")
        assert len(awaiting) == 1
        assert awaiting[0].data["record_names"] == ["_acme-challenge.manual-scope.example.com"]
        assert value not in repr(awaiting[0].data)

        async with _scoped(org_db, setup["org_id"]):
            rows = (
                await org_db.execute(
                    select(AuditLog).where(AuditLog.action == "certificate.created")
                )
            ).scalars()
            for row in rows:
                assert value not in repr(dict(row.metadata_ or {}))

        # The endpoint is not a probe for certificates it does not describe: an
        # automated certificate has no manual challenge, and says so by name.
        automated_domain = await _create_domain(client, owner, "manual-automated.example.com")
        automated = await client.post(
            f"{API}/certificates",
            headers=owner["headers"],
            json={
                "domain_id": automated_domain["id"],
                "identifiers": ["manual-automated.example.com"],
                "dns_provider_id": None,
            },
        )
        assert automated.status_code == 201, automated.text
        not_manual = await client.get(
            f"{API}/certificates/{automated.json()['id']}/challenge",
            headers=owner["headers"],
        )
        assert not_manual.status_code == 409, not_manual.text
        assert_error_code(not_manual.json(), "CERTIFICATE_MANUAL_CHALLENGE_NOT_PENDING")


# --- 6. recovery ----------------------------------------------------------------


async def test_an_interrupted_manual_wait_is_recovered_rather_than_reordered(
    client: Any, owner: dict, org_db: Any
) -> None:
    """A worker that died mid-resume is lost work; a clean wait is not.

    The two look identical in the row — ``AWAITING_MANUAL`` with no attempt running
    — and only the attempt stamp tells them apart. Getting that wrong in either
    direction is a defect: recovering a clean wait would spend an attempt nobody
    spent, and ignoring a dead worker would leave an order that never resumes.
    """
    ca = _ManualCa()
    async with _request(client, owner, org_db, name="manual-recover.example.com") as setup:
        await _issue(org_db, setup, ca)

        # (a) A clean wait is refused without touching the row: the next move is the
        # operator's, and a confirmation that has not been *observed* is not one.
        async with _scoped(org_db, setup["org_id"]):
            generation = await org_db.get(CertificateGeneration, uuid.UUID(setup["generation_id"]))
            assert generation is not None
            document = certificate_order.load(generation)
            assert certificate_order.attempt_unfinished(document) is False
            assert certificate_order.manual_ready(document) is False
            _publish(document)
            ref = certificate_order.manual_current(document)[0]["ref"]
            certificate_order.confirm_published(document, ref)
            # Confirmed but not yet observed: still not ready.
            assert certificate_order.manual_ready(document) is False
            certificate_order.store(generation, document)
            await org_db.commit()

        waiting = await _issue(org_db, setup, ca)
        assert waiting.waiting is True
        assert waiting.code == CODE_AWAITING_MANUAL
        assert ca.orders_placed == 1
        generation = await _reload(org_db, setup)
        assert generation.attempt_count == 1, "a clean wait must not spend an attempt"

        # (b) A stamp left behind by a dead worker *is* recovered: the lost attempt is
        # accounted and the order it answered is resumed, never silently dropped.
        async with _scoped(org_db, setup["org_id"]):
            generation = await org_db.get(CertificateGeneration, uuid.UUID(setup["generation_id"]))
            assert generation is not None
            document = certificate_order.load(generation)
            document["attempt_started_at"] = (datetime.now(UTC) - timedelta(days=2)).isoformat()
            document["attempt_finished_at"] = ""
            certificate_order.store(generation, document)
            await org_db.commit()

        recovered = await _issue(org_db, setup, ca, now=datetime.now(UTC))
        assert recovered.waiting is True, (recovered.code, recovered.message)
        generation = await _reload(org_db, setup)
        assert generation.attempt_count == 2, "the lost attempt is counted, then retried"
        document = _document(generation)
        assert certificate_order.attempt_unfinished(document) is False
        assert ca.orders_placed == 1, "recovery resumes the order, it does not re-order"
        assert ca.sessions[-1].resumed == [ca.order.order_url] if ca.order else True

        # The operator's persisted confirmation survived the interruption, and is
        # still not a validation: only a fresh observation and the CA may decide.
        current = certificate_order.manual_current(document)
        assert current and current[0]["record_value"] == _challenge_value(1, 0)
        assert current[0]["confirmed_at"]
        assert current[0]["validated_at"] == ""
        assert _state(generation.state) == "AWAITING_MANUAL"


async def test_an_unusable_order_is_replaced_and_reissues_instructions(
    client: Any, owner: dict, org_db: Any
) -> None:
    """The CA's own refusal is the one thing that may invalidate a published value.

    An order the CA no longer accepts cannot be answered, so the flow places a new
    one and hands the operator a fresh instruction — rather than asking them to keep
    a record for an order that is already dead.
    """
    ca = _ManualCa()
    async with _request(client, owner, org_db, name="manual-reorder.example.com") as setup:
        await _issue(org_db, setup, ca)
        document = _document(await _reload(org_db, setup))
        old_order = document["order_url"]
        old_value = certificate_order.manual_current(document)[0]["record_value"]
        assert old_value == _challenge_value(1, 0)

        # The operator publishes and confirms; the CA has meanwhile aged the order
        # out, so the confirmation can no longer be answered.
        ca.unusable = True
        _publish(document)
        confirmed = await client.post(
            f"{API}/certificates/{setup['certificate']['id']}/challenge/confirm",
            headers=owner["headers"],
            json={},
        )
        assert confirmed.status_code == 202, confirmed.text
        assert confirmed.json()["ready"] is True

        restarted = await _issue(org_db, setup, ca)
        assert restarted.waiting is True
        assert ca.orders_placed == 2, "an unusable order is replaced, not retried forever"

        document = _document(await _reload(org_db, setup))
        assert document["order_url"] != old_order
        fresh = certificate_order.manual_current(document)
        assert fresh and fresh[0]["record_value"] == _challenge_value(2, 0)
        assert fresh[0]["record_value"] != old_value, "the new order has a new challenge"
        # Fresh instructions are unconfirmed: the old confirmation belonged to a
        # record that no longer answers anything.
        assert all(entry["confirmed_at"] == "" for entry in fresh)
        assert certificate_order.manual_ready(document) is False

    # And the API shows the new instruction rather than the dead one.
    shown = await client.get(
        f"{API}/certificates/{setup['certificate']['id']}/challenge", headers=owner["headers"]
    )
    assert shown.status_code == 200, shown.text
    assert shown.json()["records"][0]["record_value"] == _challenge_value(2, 0)
    assert shown.json()["records"][0]["confirmed"] is False
    assert shown.json()["ready"] is False


async def test_the_sweep_does_not_dispatch_a_waiting_manual_generation(
    client: Any, owner: dict, org_db: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A waiting generation is not due work — and the sweep must not pretend it is.

    Dispatching it would buy a refusal per tick, forever, and would make a waiting
    generation indistinguishable from a lost worker in the dispatch log.
    """
    from app.tasks import certificates as certificate_tasks

    ca = _ManualCa()
    async with _request(client, owner, org_db, name="manual-sweep.example.com") as setup:
        await _issue(org_db, setup, ca)

    class _Queue:
        def __init__(self) -> None:
            self.ids: list[str] = []

        def delay(self, value: str) -> None:
            self.ids.append(value)

    queue = _Queue()
    monkeypatch.setattr(certificate_tasks, "issue_certificate", queue)

    counts = await asyncio.to_thread(certificate_tasks.sweep_certificates)

    assert queue.ids == []
    assert counts["awaiting_manual"] >= 1
