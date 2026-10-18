"""Phase 5.3 — issuance end to end, with a fake CA, a fake zone and a fake resolver.

What these tests pin is the flow itself, not any CA's behaviour: the real
``issue_generation`` code runs against its documented seams (``session_factory``,
``provider_factory``, ``observer``), a real PostgreSQL schema and the real tenancy
scope, so the claims below are about this platform's code path rather than a mock's.

* **A successful attempt is an issuance.** The generation reaches ``ISSUED`` with a
  material set whose fingerprint matches the leaf, the certificate becomes current,
  the order document records the directory, and every TXT record this platform
  created is deleted again.
* **A failed attempt is recorded, scheduled and cleaned up.** The failure carries
  the CA's vocabulary, the backoff is scheduled, and the challenge record does not
  survive the failure.
* **Dispatches are not attempts.** A running attempt is refused without touching
  the row — including when the *task* is dispatched twice, which is what a
  redelivered message looks like; an abandoned one is recorded as lost work and
  retried immediately; a manual retry pulls the schedule forward and hands the
  work to the worker path.
* **Nothing leaks.** No response, event or column holds the private key or the
  account key in the clear, and the failure text names a code rather than echoing
  CA free text.
"""

from __future__ import annotations

import asyncio
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
from app.providers.dns import (
    CredentialCheck,
    DnsWriteAmbiguous,
    TxtRecord,
    ZoneRef,
    ZoneResolution,
)
from app.services import certificate_order, dns_provider_service, dns_verifier
from app.services.acme import (
    AcmeChallenge,
    AcmeOrder,
    AcmeUnavailable,
    AuthorizationState,
    IssuedChain,
)
from app.services.certificate_issuance import (
    CODE_ATTEMPT_IN_FLIGHT,
    CODE_ATTEMPTS_EXHAUSTED,
    CODE_WORKER_LOST,
    issue_generation,
    request_retry,
)
from app.services.dns_verifier import STATUS_OK, TxtObservation
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID
from sqlalchemy import select

from .helpers import API

pytestmark = pytest.mark.integration

NS_SET = ("ns1.example.net", "ns2.example.net")

#: The token the mocked authoritative DNS serves for domain verification.
DNS: dict[str, object] = {"token": "", "nameservers": NS_SET}

TOKEN = "cf-token-that-must-never-be-echoed"


def _fake_observe(name: str) -> TxtObservation:
    return TxtObservation(
        STATUS_OK,
        values=(str(DNS["token"]),),
        nameservers=tuple(DNS["nameservers"]),  # type: ignore[arg-type]
    )


@pytest.fixture(autouse=True)
def _dns_stub(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    DNS["token"] = ""
    DNS["nameservers"] = NS_SET
    monkeypatch.setattr(dns_verifier, "observe", _fake_observe)
    yield


class _FakeCloudflare:
    """The credential side of the DNS seam, for creating a provider through the API."""

    name = "cloudflare"
    required_fields: tuple[str, ...] = ("api_token",)

    async def verify_creds(self, credentials: dict[str, str]) -> CredentialCheck:
        return CredentialCheck(ok=True, scopes={"zone_names": ["example.com"]})


@pytest.fixture(autouse=True)
def _credential_seam(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(dns_provider_service, "provider_for", lambda kind: _FakeCloudflare())


class _FakeZone:
    """A DNS API that keeps the records it was asked to create.

    Deliberately dumb: it answers for any name, returns a fresh reference per
    create, and deletes exactly the reference it was handed — which is what makes
    "cleanup deletes the record this platform made" observable.
    """

    name = "fake-dns"

    def __init__(self) -> None:
        self.records: dict[str, TxtRecord] = {}
        self.creates: list[TxtRecord] = []
        self.deleted: list[str] = []
        self._next = 0
        self.delete_ok = True

    async def resolve_zone(self, credentials: dict[str, str], name: str) -> ZoneResolution:
        return ZoneResolution(zone=ZoneRef(id="zone-1", name="example.com"))

    async def create_txt(
        self, credentials: dict[str, str], *, zone_id: str, name: str, value: str, ttl: int
    ) -> TxtRecord:
        self._next += 1
        record = TxtRecord(id=f"rec-{self._next}", zone_id=zone_id, name=name, value=value)
        self.records[record.id] = record
        self.creates.append(record)
        return record

    async def find_txt(
        self, credentials: dict[str, str], *, zone_id: str, name: str, value: str
    ) -> tuple[TxtRecord, ...]:
        return tuple(
            record
            for record in self.records.values()
            if record.zone_id == zone_id and record.name == name and record.value == value
        )

    async def delete_txt(
        self, credentials: dict[str, str], *, zone_id: str, record_id: str
    ) -> bool:
        self.deleted.append(record_id)
        self.records.pop(record_id, None)
        return self.delete_ok


class _AmbiguousZone(_FakeZone):
    """A DNS API whose create committed remotely but whose response was lost.

    The record *is* in the zone — ``find_txt`` will find it — which is the state
    that must be adopted rather than retried blindly: a second create would leave
    an extra TXT record this platform has no reference to, and no cleanup path can
    delete a record it never recorded.
    """

    def __init__(self) -> None:
        super().__init__()
        self.ambiguous = 0

    async def create_txt(
        self, credentials: dict[str, str], *, zone_id: str, name: str, value: str, ttl: int
    ) -> TxtRecord:
        await super().create_txt(credentials, zone_id=zone_id, name=name, value=value, ttl=ttl)
        self.ambiguous += 1
        raise DnsWriteAmbiguous(
            "the DNS provider did not answer before the request timed out",
            detail="the create may have succeeded; the zone was not observed",
            name=name,
            value=value,
        )


class _FakeAcme:
    """The CA side of the seam, honest about the outcomes that matter here."""

    directory = AcmeDirectory.STAGING

    def __init__(self, *, outcome: str = "issue") -> None:
        self.outcome = outcome
        self.csr: x509.CertificateSigningRequest | None = None
        self.order: AcmeOrder | None = None
        self.answered: list[str] = []
        self.closed = False
        self.order_identifiers: tuple[str, ...] = ()

    async def register_account(self, *, contact_email: str | None = None) -> str:
        return "https://ca.test/kid/1"

    async def create_order(self, *, csr_pem: bytes, identifiers: tuple[str, ...]) -> AcmeOrder:
        self.csr = x509.load_pem_x509_csr(csr_pem)
        self.order_identifiers = identifiers
        challenges = []
        for index, identifier in enumerate(identifiers):
            wildcard = identifier.startswith("*.")
            base = identifier[2:] if wildcard else identifier
            challenges.append(
                AcmeChallenge(
                    identifier=base,
                    wildcard=wildcard,
                    authorization_url=f"https://ca.test/authz/{index}",
                    challenge_url=f"https://ca.test/chall/{index}",
                    token=f"token-{index}",
                    record_name=f"_acme-challenge.{base}",
                    record_value=f"value-{index}",
                    key_authorization=f"token-{index}.thumbprint",
                    status="pending",
                )
            )
        self.order = AcmeOrder(
            order_url="https://ca.test/order/1",
            status="pending",
            challenges=tuple(challenges),
            identifiers=identifiers,
        )
        return self.order

    async def accept_challenge(self, *, challenge_url: str) -> None:
        self.answered.append(challenge_url)

    async def poll_authorization(
        self, *, authorization_url: str, timeout_seconds: float
    ) -> AuthorizationState:
        if self.outcome == "reject":
            return AuthorizationState(
                status="invalid",
                error_code="caa",
                error_detail="CAA record inhibits issuance",
            )
        return AuthorizationState(status="valid")

    async def finalize_order(self, *, csr_pem: bytes, timeout_seconds: float) -> IssuedChain:
        assert self.csr is not None
        if self.outcome == "finalize_fail":
            raise AcmeUnavailable(
                "the certificate authority could not be reached to finalize the order",
                code="ACME_REQUEST_FAILED",
                detail="connection reset while fetching the certificate",
            )
        ca_key = ec.generate_private_key(ec.SECP256R1())
        sans = self.csr.extensions.get_extension_for_class(
            x509.SubjectAlternativeName
        ).value.get_values_for_type(x509.DNSName)
        leaf = (
            x509.CertificateBuilder()
            .subject_name(self.csr.subject)
            .issuer_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Fake CA")]))
            .public_key(self.csr.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.now(UTC) - timedelta(minutes=5))
            .not_valid_after(datetime.now(UTC) + timedelta(days=90))
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName(name) for name in sans]),
                critical=False,
            )
            .sign(ca_key, hashes.SHA256())
        )
        pem = leaf.public_bytes(serialization.Encoding.PEM).decode("ascii")
        # A real client returns leaf-first PEM; a self-signed fake needs one block.
        return IssuedChain(fullchain_pem=pem, order_url="https://ca.test/order/1")

    async def close(self) -> None:
        self.closed = True


class _FakeCa:
    """A session factory that records what the flow asked the CA to do."""

    def __init__(self, *, outcome: str = "issue") -> None:
        self.outcome = outcome
        self.sessions: list[_FakeAcme] = []
        self.opened = 0

    @asynccontextmanager
    async def open(
        self, *, directory: AcmeDirectory, account_key_pem: str, account_url: str | None
    ) -> AsyncIterator[_FakeAcme]:
        self.opened += 1
        assert directory is AcmeDirectory.STAGING
        assert account_key_pem.startswith("-----BEGIN PRIVATE KEY-----")
        session = _FakeAcme(outcome=self.outcome)
        self.sessions.append(session)
        try:
            yield session
        finally:
            await session.close()


# --- setup ---------------------------------------------------------------------


@asynccontextmanager
async def _scoped(db, org_id: uuid.UUID) -> AsyncIterator[Any]:
    with org_scope(org_id):
        await apply_scope_to_session(db)
        yield db


async def _create_domain(client, owner, name: str) -> dict:
    created = await client.post(f"{API}/domains", headers=owner["headers"], json={"name": name})
    assert created.status_code == 201, created.text
    body = created.json()
    DNS["token"] = body["verification"]["record_value"]
    from app.tasks.domain_routing import _verify

    outcome = await _verify(uuid.UUID(body["id"]), trigger="user")
    assert outcome["status"] == DomainStatus.VERIFIED.value, outcome
    detail = await client.get(f"{API}/domains/{body['id']}", headers=owner["headers"])
    assert detail.status_code == 200, detail.text
    return detail.json()


async def _create_provider(client, owner) -> dict:
    response = await client.post(
        f"{API}/dns-providers",
        headers=owner["headers"],
        json={
            "name": "Issuance zone",
            "credentials": {"api_token": TOKEN},
            "zone_allowlist": ["example.com"],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


@asynccontextmanager
async def _request(
    client,
    owner,
    org_db,
    *,
    name: str = "issuance-one.example.com",
    identifiers: list[str] | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """A verified domain, an attached credential, a request and its generation."""
    domain = await _create_domain(client, owner, name)
    provider = await _create_provider(client, owner)
    created = await client.post(
        f"{API}/certificates",
        headers=owner["headers"],
        json={
            "domain_id": domain["id"],
            "identifiers": identifiers or [name],
            "dns_provider_id": provider["id"],
        },
    )
    assert created.status_code == 201, created.text
    certificate = created.json()
    generation_id = certificate["latest_generation"]["id"]

    org_id = uuid.UUID(owner["active_organization_id"])
    async with _scoped(org_db, org_id):
        generation = await org_db.get(CertificateGeneration, uuid.UUID(generation_id))
        certificate_row = await org_db.get(Certificate, uuid.UUID(certificate["id"]))
        assert generation is not None and certificate_row is not None
        yield {
            "org_id": org_id,
            "domain": domain,
            "provider": provider,
            "certificate": certificate,
            "certificate_row": certificate_row,
            "generation": generation,
            "generation_id": generation_id,
        }


def _state(value: Any) -> str:
    """A generation state's string value, whether it is an enum or was set as text."""
    return str(getattr(value, "value", value))


def _observer_for(zone: _FakeZone):
    """Authoritative DNS that answers with exactly the records the fake zone holds."""

    def observe(name: str) -> TxtObservation:
        values = tuple(record.value for record in zone.records.values() if record.name == name)
        return TxtObservation(STATUS_OK, values=values, nameservers=NS_SET)

    return observe


async def _issue(db, setup: dict[str, Any], *, ca: _FakeCa, zone: _FakeZone, now=None):
    with org_scope(setup["org_id"]):
        await apply_scope_to_session(db)
        return await issue_generation(
            db,
            setup["generation"],
            certificate=setup["certificate_row"],
            settings=get_settings(),
            now=now or datetime.now(UTC) + timedelta(seconds=1),
            session_factory=ca.open,
            provider_factory=lambda kind: zone,
            observer=_observer_for(zone),
        )


async def _events(db, org_id: uuid.UUID, event_type: str) -> list[SystemEvent]:
    async with _scoped(db, org_id):
        rows = await db.execute(
            select(SystemEvent)
            .where(SystemEvent.type == event_type)
            .order_by(SystemEvent.created_at)
        )
        return list(rows.scalars())


# --- 1. a successful attempt ---------------------------------------------------


async def test_a_fake_ca_issues_the_generation_and_cleans_up(client, owner, org_db) -> None:
    async with _request(client, owner, org_db) as setup:
        ca, zone = _FakeCa(), _FakeZone()
        result = await _issue(org_db, setup, ca=ca, zone=zone)

        assert result.ok is True, result
        assert _state(result.state) == "ISSUED"
        assert result.attempt == 1

        # One order for one identifier, every challenge answered and verified.
        session = ca.sessions[0]
        assert session.order_identifiers == (setup["domain"]["name"],)
        assert len(session.answered) == 1
        assert session.closed is True

    async with _scoped(org_db, setup["org_id"]):
        generation = await org_db.get(CertificateGeneration, uuid.UUID(setup["generation_id"]))
        certificate = await org_db.get(Certificate, uuid.UUID(setup["certificate"]["id"]))
        assert generation is not None and certificate is not None

        assert _state(generation.state) == "ISSUED"
        assert generation.attempt_count == 1
        assert generation.fingerprint and len(generation.fingerprint) >= 32
        assert generation.not_before is not None and generation.not_after is not None
        assert generation.not_after > generation.not_before
        assert generation.issued_at is not None
        assert generation.key_ciphertext and generation.chain_ciphertext
        assert generation.last_error == ""

        assert certificate.current_generation_id == generation.id
        assert certificate.expires_at == generation.not_after
        assert _state(certificate.status) == "ISSUED"

        document = certificate_order.load(generation)
        assert document["directory_url"] == AcmeDirectory.STAGING.url()
        assert document["finalized_at"]
        assert certificate_order.attempt_in_flight(document) is False
        # Every record this platform created was deleted again, by reference.
        assert certificate_order.pending_cleanup(document) == []
        assert certificate_order.cleanup_incomplete(document) == []
        assert all(
            entry["cleanup"] == certificate_order.CLEANUP_DONE
            for entry in certificate_order.entries(document)
        )

    assert zone.creates, "the flow must create the challenge record"
    assert [record.id for record in zone.creates] == zone.deleted
    assert zone.records == {}

    events = await _events(org_db, setup["org_id"], "CERTIFICATE_ISSUED")
    assert len(events) == 1
    payload = events[0].data
    assert payload["directory"] == "staging"
    # Metadata about the material, never the material.
    assert set(payload) == {
        "primary_cn",
        "generation",
        "attempt",
        "fingerprint",
        "not_before",
        "not_after",
        "directory",
        "directory_url",
    }
    assert "PRIVATE KEY" not in str(payload)


async def test_issuance_stores_no_plaintext_material(client, owner, org_db) -> None:
    async with _request(client, owner, org_db) as setup:
        ca, zone = _FakeCa(), _FakeZone()
        result = await _issue(org_db, setup, ca=ca, zone=zone)
        assert result.ok is True

    async with _scoped(org_db, setup["org_id"]):
        generation = await org_db.get(CertificateGeneration, uuid.UUID(setup["generation_id"]))
        assert generation is not None
        for value in (generation.key_ciphertext, generation.chain_ciphertext):
            assert isinstance(value, str)
            assert "PRIVATE KEY" not in value
            assert "BEGIN CERTIFICATE" not in value
        # The order document is public ACME data: no key, no credential.
        document = repr(certificate_order.load(generation))
        assert "PRIVATE KEY" not in document
        assert TOKEN not in document
        assert "key_ciphertext" not in document


# --- 2. a failed attempt -------------------------------------------------------


async def test_a_ca_rejection_fails_the_attempt_and_schedules_a_retry(
    client, owner, org_db
) -> None:
    async with _request(client, owner, org_db) as setup:
        ca, zone = _FakeCa(outcome="reject"), _FakeZone()
        now = datetime.now(UTC) + timedelta(seconds=1)
        result = await _issue(org_db, setup, ca=ca, zone=zone, now=now)

        assert result.ok is False
        assert result.code == "ACME_CAA"
        assert result.retryable is True
        assert result.terminal is False
        assert result.next_attempt_at is not None
        assert result.next_attempt_at == now + timedelta(minutes=5)

    async with _scoped(org_db, setup["org_id"]):
        generation = await org_db.get(CertificateGeneration, uuid.UUID(setup["generation_id"]))
        certificate = await org_db.get(Certificate, uuid.UUID(setup["certificate"]["id"]))
        assert generation is not None and certificate is not None
        assert _state(generation.state) == "FAILED"
        assert generation.attempt_count == 1
        assert generation.next_attempt_at is not None
        assert "caa" in generation.last_error.lower()
        assert generation.fingerprint is None
        assert generation.key_ciphertext is None and generation.chain_ciphertext is None
        assert _state(certificate.status) == "FAILED"

    # The failure is durable and the record is gone: no orphaned challenge in the
    # customer's zone, and no unconfirmed cleanup reported as success.
    assert zone.records == {}
    assert zone.deleted == [record.id for record in zone.creates]

    events = await _events(org_db, setup["org_id"], "CERTIFICATE_ISSUANCE_FAILED")
    assert len(events) == 1
    assert events[0].data["code"] == "ACME_CAA"
    assert events[0].data["retryable"] is True
    assert events[0].data["next_attempt_at"]


async def test_an_unconfirmed_delete_is_reported_and_retried_later(client, owner, org_db) -> None:
    async with _request(client, owner, org_db) as setup:
        ca, zone = _FakeCa(outcome="reject"), _FakeZone()
        zone.delete_ok = False
        result = await _issue(org_db, setup, ca=ca, zone=zone)
        assert result.ok is False

    async with _scoped(org_db, setup["org_id"]):
        generation = await org_db.get(CertificateGeneration, uuid.UUID(setup["generation_id"]))
        assert generation is not None
        document = certificate_order.load(generation)
        unresolved = certificate_order.cleanup_incomplete(document)
        assert unresolved, "a delete that was not confirmed must not be reported as done"
        assert "did not confirm" in unresolved[0]["cleanup_error"]
        assert certificate_order.pending_cleanup(document) == unresolved


async def test_an_ambiguous_create_adopts_the_record_the_zone_holds(client, owner, org_db) -> None:
    """A lost create response must not become a duplicate — or an orphan.

    The provider accepted the write and the answer never arrived. Retrying the
    create would put a second TXT value at the name that this platform has no
    reference to; the reconciliation is to observe the zone, adopt the record that
    is actually there, and carry on with that reference so cleanup can delete it.
    """
    async with _request(client, owner, org_db) as setup:
        ca, zone = _FakeCa(), _AmbiguousZone()
        result = await _issue(org_db, setup, ca=ca, zone=zone)

        assert result.ok is True, (result.code, result.message)
        assert zone.ambiguous == 1, "the ambiguity is reconciled, not retried blind"
        assert len(zone.creates) == 1, "no second record may be created"

    async with _scoped(org_db, setup["org_id"]):
        generation = await org_db.get(CertificateGeneration, uuid.UUID(setup["generation_id"]))
        assert generation is not None
        entries = certificate_order.entries(certificate_order.load(generation))
        assert len(entries) == 1
        assert "adopted the record the zone already held" in entries[0]["error"]
        assert entries[0]["record_id"] == zone.creates[0].id
        assert entries[0]["cleanup"] == certificate_order.CLEANUP_DONE

    # The adopted record is the one that was deleted: nothing is left behind and
    # nothing else was ever there.
    assert zone.deleted == [zone.creates[0].id]
    assert zone.records == {}


async def test_a_failed_finalization_records_the_failure_and_cleans_up(
    client, owner, org_db
) -> None:
    """A CA that cannot be reached at finalization fails the attempt, not the order.

    The validation already succeeded, so the challenge records have done their job:
    they are deleted, the failure is retryable, and no material is written. The row
    must not look like a partial issuance.
    """
    async with _request(client, owner, org_db) as setup:
        ca, zone = _FakeCa(outcome="finalize_fail"), _FakeZone()
        result = await _issue(org_db, setup, ca=ca, zone=zone)

        assert result.ok is False
        assert result.code == "ACME_REQUEST_FAILED", result
        assert result.retryable is True
        assert result.terminal is False

    async with _scoped(org_db, setup["org_id"]):
        generation = await org_db.get(CertificateGeneration, uuid.UUID(setup["generation_id"]))
        certificate = await org_db.get(Certificate, uuid.UUID(setup["certificate"]["id"]))
        assert generation is not None and certificate is not None
        assert _state(generation.state) == "FAILED"
        assert generation.fingerprint is None
        assert generation.key_ciphertext is None and generation.chain_ciphertext is None
        assert generation.issued_at is None
        assert certificate.current_generation_id is None
        assert "could not be reached to finalize" in generation.last_error
        assert "connection reset" in generation.last_error
        document = certificate_order.load(generation)
        assert certificate_order.pending_cleanup(document) == []
        assert all(entry["validated_at"] for entry in certificate_order.entries(document)), (
            "the CA did validate; only the retrieval failed"
        )

    assert zone.records == {}
    assert zone.deleted == [record.id for record in zone.creates]


# --- 3. dispatches that are not attempts --------------------------------------


def _document_with_running_attempt(*, started: datetime, provider_id: str | None = None) -> dict:
    document = certificate_order.set_order(
        {},
        directory_url=AcmeDirectory.STAGING.url(),
        order_url="https://ca.test/order/0",
        mode="automated",
    )
    document["attempt_started_at"] = started.isoformat()
    document["attempt_finished_at"] = ""
    if provider_id is not None:
        document["challenges"] = [
            {
                "ref": "abc123",
                "order_url": "https://ca.test/order/0",
                "identifier": "issuance-one.example.com",
                "wildcard": False,
                "authorization_url": "https://ca.test/authz/0",
                "challenge_url": "https://ca.test/chall/0",
                "token": "token",
                "record_name": "_acme-challenge.issuance-one.example.com",
                "record_value": "old-value",
                "key_authorization": "k",
                "mode": "automated",
                "record_id": "rec-old",
                "zone_id": "zone-1",
                "provider_id": provider_id,
                "cleanup": "pending",
                "cleanup_attempts": 0,
                "cleanup_error": "",
                "published_at": "",
                "confirmed_at": "",
                "validated_at": "",
                "error": "",
            }
        ]
    return document


async def test_a_running_attempt_is_refused_without_touching_the_row(client, owner, org_db) -> None:
    async with _request(client, owner, org_db) as setup:
        now = datetime.now(UTC)
        async with _scoped(org_db, setup["org_id"]):
            generation = await org_db.get(CertificateGeneration, uuid.UUID(setup["generation_id"]))
            assert generation is not None
            generation.state = "VALIDATING"
            generation.attempt_count = 1
            generation.order_state = _document_with_running_attempt(started=now)
            await org_db.flush()

        ca, zone = _FakeCa(), _FakeZone()
        result = await _issue(org_db, setup, ca=ca, zone=zone, now=now)

        assert result.ok is False
        assert result.code == CODE_ATTEMPT_IN_FLIGHT
        assert ca.opened == 0, "a refused dispatch must not open a CA session"

    async with _scoped(org_db, setup["org_id"]):
        generation = await org_db.get(CertificateGeneration, uuid.UUID(setup["generation_id"]))
        assert generation is not None
        assert _state(generation.state) == "VALIDATING"
        assert generation.attempt_count == 1
        assert generation.last_error == ""


async def test_a_duplicate_task_dispatch_creates_no_second_order(client, owner, org_db) -> None:
    """Two dispatches of one in-flight generation: both refused, nothing written.

    The service's own guard is proven above; what is dispatched twice in production
    is the *task* — an API enqueue racing a sweep tick, or a message the broker
    redelivers. It resolves the tenant and builds its own loop and session, so the
    claim that a duplicate cannot become a second ACME order has to be made through
    it. Both deliveries run in one worker thread, one after the other, which is how
    a broker hands a redelivered message to the same worker.
    """
    from app.core.db import dispose_engine

    order_before = _document_with_running_attempt(
        started=datetime.now(UTC), provider_id="provider-under-test"
    )
    async with _request(client, owner, org_db) as setup:
        async with _scoped(org_db, setup["org_id"]):
            generation = await org_db.get(CertificateGeneration, uuid.UUID(setup["generation_id"]))
            assert generation is not None
            generation.state = "CHALLENGE_PUBLISHED"
            generation.attempt_count = 1
            generation.order_state = order_before
            await org_db.commit()

        # A worker thread runs its own loop and its own connections; drop this
        # loop's pooled ones first (the maintenance sweep's test does the same).
        await dispose_engine()
        try:
            from app.tasks.certificates import issue_certificate

            def _deliver_twice() -> tuple[dict[str, str], dict[str, str]]:
                generation_id = setup["generation_id"]
                return issue_certificate.run(generation_id), issue_certificate.run(generation_id)

            first, second = await asyncio.to_thread(_deliver_twice)
        finally:
            await dispose_engine()

    for outcome in (first, second):
        assert outcome["status"] == "not_issued", outcome
        assert outcome["code"] == CODE_ATTEMPT_IN_FLIGHT, outcome
        assert outcome["attempt"] == "1", outcome

    async with _scoped(org_db, setup["org_id"]):
        generation = await org_db.get(CertificateGeneration, uuid.UUID(setup["generation_id"]))
        assert generation is not None
        assert _state(generation.state) == "CHALLENGE_PUBLISHED"
        assert generation.attempt_count == 1
        # Nothing either dispatch touched: the recorded order — the one the first
        # worker is running — is byte-for-byte what it was, so there is no second
        # order and no second challenge set to answer.
        assert certificate_order.load(generation) == order_before
        assert len(certificate_order.entries(certificate_order.load(generation))) == 1
        # A refused dispatch is not a failure, so it must not record one.
        assert generation.last_error == ""

    for event_type in ("CERTIFICATE_ISSUED", "CERTIFICATE_ISSUANCE_FAILED"):
        assert await _events(org_db, setup["org_id"], event_type) == [], (
            "a duplicate dispatch must not report an issuance or a failure"
        )


async def test_an_abandoned_attempt_is_recorded_and_retried_immediately(
    client, owner, org_db
) -> None:
    async with _request(client, owner, org_db) as setup:
        stale = datetime.now(UTC) - timedelta(hours=2)
        async with _scoped(org_db, setup["org_id"]):
            generation = await org_db.get(CertificateGeneration, uuid.UUID(setup["generation_id"]))
            assert generation is not None
            generation.state = "CHALLENGE_PUBLISHED"
            generation.attempt_count = 1
            generation.order_state = _document_with_running_attempt(
                started=stale, provider_id=setup["provider"]["id"]
            )
            await org_db.flush()

        ca, zone = _FakeCa(), _FakeZone()
        result = await _issue(org_db, setup, ca=ca, zone=zone)

        assert result.ok is True
        assert result.attempt == 2, "the abandoned attempt is already counted"
        # The record the dead worker left was deleted before anything new was
        # published at that name.
        assert zone.deleted[0] == "rec-old"

    events = await _events(org_db, setup["org_id"], "CERTIFICATE_ISSUANCE_FAILED")
    lost = [event for event in events if event.data.get("code") == CODE_WORKER_LOST]
    assert len(lost) == 1
    assert lost[0].data["retryable"] is True

    async with _scoped(org_db, setup["org_id"]):
        generation = await org_db.get(CertificateGeneration, uuid.UUID(setup["generation_id"]))
        assert generation is not None
        assert _state(generation.state) == "ISSUED"
        assert generation.attempt_count == 2


async def test_a_manual_retry_pulls_the_schedule_forward(client, owner, org_db) -> None:
    async with _request(client, owner, org_db) as setup:
        now = datetime.now(UTC)
        async with _scoped(org_db, setup["org_id"]):
            generation = await org_db.get(CertificateGeneration, uuid.UUID(setup["generation_id"]))
            assert generation is not None
            generation.state = "FAILED"
            generation.attempt_count = 1
            generation.last_error = "the certificate authority refused the request (caa)"
            generation.next_attempt_at = now + timedelta(hours=1)
            certificate = setup["certificate_row"]
            await org_db.flush()

            retried = await request_retry(org_db, certificate, now=now)

            assert retried.id == generation.id
            assert retried.next_attempt_at == now
            assert _state(retried.state) == "FAILED", "a retry is not an attempt"

    events = await _events(org_db, setup["org_id"], "CERTIFICATE_ISSUANCE_RETRIED")
    assert len(events) == 1
    assert events[0].data["attempts"] == 1


async def test_a_manual_retry_refuses_an_exhausted_budget(client, owner, org_db) -> None:
    from app.core.errors import Conflict

    async with _request(client, owner, org_db) as setup:
        async with _scoped(org_db, setup["org_id"]):
            generation = await org_db.get(CertificateGeneration, uuid.UUID(setup["generation_id"]))
            assert generation is not None
            generation.state = "FAILED"
            generation.attempt_count = 5
            await org_db.flush()

            with pytest.raises(Conflict) as refused:
                await request_retry(org_db, setup["certificate_row"])
            assert refused.value.code == CODE_ATTEMPTS_EXHAUSTED
