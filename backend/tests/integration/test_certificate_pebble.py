"""Phase 5.3.1 — issuance through the **real** ACME protocol, against Pebble.

The other issuance integration test proves the flow against its seams: a fake
session, a fake zone, a fake resolver. That is the right test for the state
machine, but it cannot show that the production adapter speaks RFC 8555 or that
the platform's own DNS observation is what lets a real CA validate. This module
is that second claim: one CA, one zone, the real client, the real propagation
code and the real persistence path.

Infrastructure (started by :func:`pebble_stack` when it is not already running)
lives in ``docker-compose.pebble.yml`` as project ``nexusops-pebble``, on Linux
host networking:

* ``ca`` — ``ghcr.io/letsencrypt/pebble``, validating DNS-01 against
  ``127.0.0.2:53``. Its TLS certificate is self-signed and regenerated on every
  start, so it is never added to a trust store: the ``pebble`` directory is the
  one place the client disables verification, and that directory is refused in
  production by :mod:`app.services.acme.directory`.
* ``ns-a`` / ``ns-b`` — this repository's own authoritative server
  (``e2e/dnsmock``) on ``127.0.0.2:53`` and ``127.0.0.3:53``. Both advertise the
  *same* delegation (``ns1``/``ns2.pebble.test``) while holding their own record
  stores, which is what makes a mid-propagation zone representable: one server
  with the challenge value, one still without it.

The test does **not** skip when the infrastructure is unavailable. A silent skip
here is how "the fake CA covers it" becomes a claim nobody re-checks, so a
missing Docker daemon, a failed ``up`` or an unreachable Pebble is a failure
whose message names the command to run by hand (``make pebble-up``).

Run it with ``make test-pebble``; it needs the same PostgreSQL and Redis the
other integration tests need.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import time
import uuid
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import dns.resolver
import httpx
import pytest
from app.core.config import get_settings
from app.core.tenancy import apply_scope_to_session, org_scope
from app.models import Certificate, CertificateGeneration, SystemEvent
from app.models.enums import AcmeDirectory, DomainStatus
from app.providers.dns import CredentialCheck, TxtRecord, ZoneRef, ZoneResolution
from app.services import certificate_order, dns_provider_service, dns_verifier
from app.services.acme import open_acme_session
from app.services.certificate_issuance import issue_generation
from app.services.dek_envelope import org_dek_context
from app.services.dns_verifier import (
    STATUS_NO_TXT,
    STATUS_OK,
    TxtObservation,
    observe_txt_record,
)
from app.services.payload_crypto import (
    PURPOSE_CERTIFICATE_CHAIN,
    PURPOSE_CERTIFICATE_KEY,
    PayloadContext,
    decrypt,
)
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .helpers import API

pytestmark = [pytest.mark.integration, pytest.mark.pebble]

REPO_ROOT = Path(__file__).resolve().parents[3]
COMPOSE_FILE = REPO_ROOT / "docker-compose.pebble.yml"
PROJECT = "nexusops-pebble"

ZONE = "pebble.test"
#: Loopback address and control-API port of each authoritative view.
VIEWS: dict[str, tuple[str, int]] = {"ns-a": ("127.0.0.2", 18053), "ns-b": ("127.0.0.3", 18054)}
#: Where the deployment's resolver would find this zone's delegation.
BOOTSTRAP = "127.0.0.2"

TOKEN = "cf-token-that-must-never-be-echoed"
TYPE_TXT = "16"
#: The compose binary, resolved once. Absolute so the process is not started from
#: an inherited PATH entry that could name something else.
DOCKER = shutil.which("docker")


# --- infrastructure ------------------------------------------------------------


def _get_json(url: str, *, insecure: bool = False, timeout: float = 5.0) -> dict[str, Any]:
    response = httpx.get(url, timeout=timeout, verify=not insecure)
    response.raise_for_status()
    return response.json() if response.content else {}


def _post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = httpx.post(url, json=payload, timeout=5.0)
    response.raise_for_status()
    return response.json() if response.content else {}


def _delete(url: str, *, params: dict[str, str]) -> None:
    httpx.delete(url, params=params, timeout=5.0).raise_for_status()


def _stack_reachable() -> bool:
    """Both authoritative views serve this zone, and Pebble answers its directory."""
    try:
        for address, control in VIEWS.values():
            if _get_json(f"http://{address}:{control}/health")["zone"] != ZONE:
                return False
        _get_json(AcmeDirectory.PEBBLE.url(), insecure=True)
    except Exception:
        return False
    return True


def _compose(*args: str) -> subprocess.CompletedProcess[str]:
    assert DOCKER is not None
    return subprocess.run(
        [DOCKER, "compose", "-p", PROJECT, "-f", str(COMPOSE_FILE), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


@pytest.fixture(scope="module")
def pebble_stack() -> Iterator[dict[str, Any]]:
    """The isolated CA and authoritative zone, started if they are not up.

    A stack this fixture started is torn down again; one that was already running
    (``make pebble-up``) is left alone, because tearing down a developer's stack at
    the end of a test run is not this fixture's decision to make.
    """
    if DOCKER is None:
        pytest.fail(
            "the Pebble integration test needs a Docker daemon: install Docker, "
            "then run `make test-pebble`"
        )
    started = False
    if not _stack_reachable():
        up = _compose("up", "-d", "--build")
        if up.returncode != 0:
            pytest.fail(
                "could not start the isolated Pebble stack: "
                f"{(up.stderr or up.stdout).strip()[-2000:]}"
            )
        started = True

    deadline = time.monotonic() + 120
    while time.monotonic() < deadline and not _stack_reachable():
        time.sleep(1.0)
    if not _stack_reachable():
        logs = _compose("logs", "--no-color", "--tail", "40").stdout
        if started:
            _compose("down", "--remove-orphans")
        pytest.fail(
            "the Pebble stack did not become reachable within 120s "
            f"(service logs below)\n{logs[-4000:]}"
        )
    try:
        yield {
            "directory": AcmeDirectory.PEBBLE.url(),
            "views": VIEWS,
            "compose": str(COMPOSE_FILE),
            "project": PROJECT,
        }
    finally:
        if started:
            _compose("down", "--remove-orphans")


# --- the two authoritative views ------------------------------------------------


class _View:
    """One authoritative server's record store, through its control API."""

    def __init__(self, name: str, address: str, control: int) -> None:
        self.name = name
        self.address = address
        self.control = control

    def records(self) -> dict[str, dict[str, list[str]]]:
        return _get_json(f"http://{self.address}:{self.control}/records")["records"]

    def txt(self, name: str) -> tuple[str, ...]:
        return tuple(self.records().get(name, {}).get(TYPE_TXT, ()))

    def publish(self, name: str, value: str) -> None:
        _post_json(
            f"http://{self.address}:{self.control}/record",
            {"name": name, "type": "TXT", "value": value},
        )

    def remove(self, name: str, value: str) -> None:
        _delete(
            f"http://{self.address}:{self.control}/record",
            params={"name": name, "type": "TXT", "value": value},
        )

    def reset(self) -> None:
        """Drop every TXT record this view holds (setup, never an assertion)."""
        for name, types in self.records().items():
            for value in types.get(TYPE_TXT, ()):
                self.remove(name, value)


class _ReplicatedZone:
    """The DNS-record seam, backed by the two **real** authoritative servers.

    It stands in for a provider's HTTP API — no customer credential is used
    anywhere — and publishes the way a replicated zone behaves: a record the API
    accepted reaches every authoritative server serving the zone. The ``stale`` set
    models the other case on purpose: an API whose write has not reached one server
    yet, which is the state the propagation policy exists to catch.

    Deletion is by *value*, not by name, because one name legitimately holds two
    challenge values (apex and wildcard). Deleting "the record this platform
    created" must not be able to take the other one with it.
    """

    name = "pebble-zone"

    def __init__(self, views: dict[str, _View], *, stale: tuple[str, ...] = ()) -> None:
        self.views = views
        self.stale = set(stale)
        self.records: dict[str, TxtRecord] = {}
        self.created: list[TxtRecord] = []
        self.deleted: list[str] = []
        self._next = 0

    def _live(self) -> list[_View]:
        return [view for name, view in self.views.items() if name not in self.stale]

    async def resolve_zone(self, credentials: dict[str, str], name: str) -> ZoneResolution:
        assert ZONE in name
        return ZoneResolution(zone=ZoneRef(id="zone-pebble", name=ZONE))

    async def create_txt(
        self, credentials: dict[str, str], *, zone_id: str, name: str, value: str, ttl: int
    ) -> TxtRecord:
        for view in self._live():
            view.publish(name, value)
        self._next += 1
        record = TxtRecord(id=f"rec-{self._next}", zone_id=zone_id, name=name, value=value)
        self.records[record.id] = record
        self.created.append(record)
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
        record = self.records.get(record_id)
        if record is None:
            return True
        self.deleted.append(record_id)
        for view in self.views.values():
            view.remove(record.name, record.value)
        self.records.pop(record_id, None)
        return all(record.value not in view.txt(record.name) for view in self.views.values())


# --- the ownership seam (unchanged from the fake-CA test) -----------------------


class _CloudflareCredentials:
    """The credential side of the DNS seam, for creating a provider through the API."""

    name = "cloudflare"
    required_fields: tuple[str, ...] = ("api_token",)

    async def verify_creds(self, credentials: dict[str, str]) -> CredentialCheck:
        return CredentialCheck(ok=True, scopes={"zone_names": [ZONE]})


@pytest.fixture
def ownership(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Domain-ownership verification only; the ACME DNS observer stays real."""
    state: dict[str, Any] = {"token": "", "nameservers": ("ns1.pebble.test", "ns2.pebble.test")}

    def observe(name: str) -> TxtObservation:
        return TxtObservation(
            STATUS_OK,
            values=(str(state["token"]),),
            nameservers=tuple(state["nameservers"]),
        )

    monkeypatch.setattr(dns_verifier, "observe", observe)
    monkeypatch.setattr(dns_provider_service, "provider_for", lambda kind: _CloudflareCredentials())
    return state


# --- setup ----------------------------------------------------------------------


@asynccontextmanager
async def _scoped(db: Any, org_id: uuid.UUID) -> AsyncIterator[Any]:
    with org_scope(org_id):
        await apply_scope_to_session(db)
        yield db


def _view_map() -> dict[str, _View]:
    return {name: _View(name, address, control) for name, (address, control) in VIEWS.items()}


def _reset_zone(views: dict[str, _View]) -> None:
    for view in views.values():
        view.reset()


async def _create_domain(client: Any, owner: dict, state: dict[str, Any], name: str) -> dict:
    created = await client.post(f"{API}/domains", headers=owner["headers"], json={"name": name})
    assert created.status_code == 201, created.text
    body = created.json()
    state["token"] = body["verification"]["record_value"]

    from app.tasks.domain_routing import _verify

    outcome = await _verify(uuid.UUID(body["id"]), trigger="user")
    assert outcome["status"] == DomainStatus.VERIFIED.value, outcome
    detail = await client.get(f"{API}/domains/{body['id']}", headers=owner["headers"])
    assert detail.status_code == 200, detail.text
    return detail.json()


async def _create_provider(client: Any, owner: dict) -> dict:
    response = await client.post(
        f"{API}/dns-providers",
        headers=owner["headers"],
        json={
            "name": "Pebble zone",
            "credentials": {"api_token": TOKEN},
            "zone_allowlist": [ZONE],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


@asynccontextmanager
async def _request(
    client: Any,
    owner: dict,
    org_db: Any,
    state: dict[str, Any],
    *,
    name: str,
    identifiers: list[str] | None = None,
) -> AsyncIterator[dict[str, Any]]:
    """A verified domain, an attached credential, a request and its generation."""
    domain = await _create_domain(client, owner, state, name)
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
    """A state's string value, whether it is an enum member or was set as text."""
    return str(getattr(value, "value", value))


def _bootstrap_resolver() -> dns.resolver.Resolver:
    """The deployment's resolver view: this zone's delegation, not the host's.

    In a deployment this is ``/etc/resolv.conf``. Here it is the one place that
    knows ``pebble.test`` is served by ``ns1``/``ns2`` at loopback addresses — the
    TXT values themselves still come from the authoritative servers, never from
    here.
    """
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = [BOOTSTRAP]
    resolver.timeout = 3.0
    resolver.lifetime = 10.0
    return resolver


def _recording_observer() -> tuple[Any, list[TxtObservation]]:
    """The real observer, with its observations kept for assertions."""
    bootstrap = _bootstrap_resolver()
    seen: list[TxtObservation] = []

    def observe(name: str) -> TxtObservation:
        observation = observe_txt_record(name, resolver=bootstrap)
        seen.append(observation)
        return observation

    return observe, seen


def _pebble_settings(*, propagation_timeout: int = 60) -> Any:
    """The real settings, pointed at Pebble.

    ``model_copy`` rather than an environment variable: the directory is a
    deployment fact, and the test states the one it exercises. Every other setting
    (poll timeouts, TTL) stays production-shaped.
    """
    return get_settings().model_copy(
        update={
            "acme_directory": AcmeDirectory.PEBBLE.value,
            "certificate_propagation_timeout_seconds": max(propagation_timeout, 10),
            "certificate_validation_timeout_seconds": 60,
            "certificate_finalization_timeout_seconds": 30,
        }
    )


async def _issue(
    db: Any,
    setup: dict[str, Any],
    zone: _ReplicatedZone,
    *,
    propagation_timeout: int = 60,
) -> tuple[Any, list[TxtObservation]]:
    observer, seen = _recording_observer()
    with org_scope(setup["org_id"]):
        await apply_scope_to_session(db)
        result = await issue_generation(
            db,
            setup["generation"],
            certificate=setup["certificate_row"],
            settings=_pebble_settings(propagation_timeout=propagation_timeout),
            now=datetime.now(UTC),
            provider_factory=lambda kind: zone,
            observer=observer,
            # The worker's checkpoint, exactly as ``tasks.certificates`` passes it:
            # the attempt's stamp, its order document and its material are
            # committed at each boundary, so the API read below sees the issuance
            # a client would see rather than this session's uncommitted view.
            checkpoint=db.commit,
        )
        # ``org_session`` commits on exit, and the success event is written after
        # the last checkpoint — without this the event would only exist in this
        # session's uncommitted view.
        await db.commit()
    return result, seen


def _pem_blocks(pem: str) -> list[str]:
    return re.findall(r"-----BEGIN CERTIFICATE-----.*?-----END CERTIFICATE-----", pem, re.DOTALL)


async def _events(db: Any, org_id: uuid.UUID, event_type: str) -> list[SystemEvent]:
    async with _scoped(db, org_id):
        rows = await db.execute(
            select(SystemEvent)
            .where(SystemEvent.type == event_type)
            .order_by(SystemEvent.created_at)
        )
        return list(rows.scalars())


def _decrypted(dek: Any, org_id: uuid.UUID, generation: Any, purpose: str, stored: str) -> str:
    return decrypt(
        dek.fernet,
        PayloadContext(
            org_id=org_id,
            purpose=purpose,
            record_id=generation.id,
            deke_id=generation.deke_id,
        ),
        stored,
    ).decode("utf-8")


# --- 1. the issuance this phase exists for -------------------------------------


async def test_pebble_issues_a_certificate_and_the_platform_verifies_its_own_dns(
    client: Any, owner: dict, org_db: Any, pebble_stack: dict[str, Any], ownership: dict
) -> None:
    """Real ACME, real authoritative DNS, real encrypted persistence.

    One test, because the ten claims are one fact: the flow reached ``ISSUED``
    *through* Pebble, and every artifact it left behind is the artifact the design
    says it should be. Asserting them together is what keeps a fake half from
    creeping back in — an assertion that only looked at the row would pass with any
    CA at all.
    """
    views = _view_map()
    _reset_zone(views)
    zone = _ReplicatedZone(views)

    async with _request(client, owner, org_db, ownership, name=f"shop.{ZONE}") as setup:
        result, seen = await _issue(org_db, setup, zone)

    # (1-6) The CA accepted the account, the order, the DNS-01 answer and the
    # finalization: none of the material below exists unless all of them happened.
    assert result.ok is True, (result.code, result.message)
    assert _state(result.state) == "ISSUED"
    assert result.attempt == 1
    assert "pebble" in result.message.lower()

    # (4) The platform's own propagation check saw the value at *both* servers,
    # over DNS, before the challenge was answered. A fake observer cannot show this.
    agreeing = [
        observation
        for observation in seen
        if observation.status == STATUS_OK
        and len(observation.server_answers) == 2
        and all(answer.status == STATUS_OK for answer in observation.server_answers)
    ]
    assert agreeing, [observation.server_answers for observation in seen]
    assert {answer.server for answer in agreeing[0].server_answers} == {
        address for address, _control in VIEWS.values()
    }

    async with _scoped(org_db, setup["org_id"]):
        generation = await org_db.get(CertificateGeneration, uuid.UUID(setup["generation_id"]))
        certificate = await org_db.get(Certificate, uuid.UUID(setup["certificate"]["id"]))
        assert generation is not None and certificate is not None

        # (9) Lifecycle and required material fields.
        assert _state(generation.state) == "ISSUED"
        assert generation.attempt_count == 1
        assert generation.fingerprint and len(generation.fingerprint) == 64
        assert generation.not_before is not None and generation.not_after is not None
        assert generation.not_after > generation.not_before
        assert generation.issued_at is not None
        assert generation.last_error == ""
        assert generation.deke_id is not None and generation.deke_id >= 1

        # (8) Encrypted under the organization DEK — and *only* encrypted: a PEM in
        # either column is the failure this asserts against.
        assert generation.key_ciphertext and generation.chain_ciphertext
        for value in (generation.key_ciphertext, generation.chain_ciphertext):
            assert "PRIVATE KEY" not in value
            assert "BEGIN CERTIFICATE" not in value

        # The provenance the database CHECK requires alongside material.
        assert generation.directory_url == pebble_stack["directory"]

        # (6, 7) Decrypt as the platform would, then verify the chain against the
        # key this attempt generated. A fake can return any PEM; Pebble's leaf must
        # actually answer this key and these names.
        async with org_dek_context(org_db, setup["org_id"]) as dek:
            key_pem = _decrypted(
                dek, setup["org_id"], generation, PURPOSE_CERTIFICATE_KEY, generation.key_ciphertext
            )
            fullchain = _decrypted(
                dek,
                setup["org_id"],
                generation,
                PURPOSE_CERTIFICATE_CHAIN,
                generation.chain_ciphertext,
            )

        blocks = _pem_blocks(fullchain)
        assert len(blocks) >= 2, "a real CA returns the leaf and its issuer"
        leaf = x509.load_pem_x509_certificate(blocks[0].encode())
        issuer = x509.load_pem_x509_certificate(blocks[1].encode())
        assert leaf.issuer == issuer.subject
        issuer.public_key().verify(
            leaf.signature, leaf.tbs_certificate_bytes, ec.ECDSA(leaf.signature_hash_algorithm)
        )
        assert "Pebble" in issuer.subject.rfc4514_string()

        key = serialization.load_pem_private_key(key_pem.encode(), password=None)
        assert leaf.public_key().public_numbers() == key.public_key().public_numbers()
        sans = leaf.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
        assert tuple(sans.get_values_for_type(x509.DNSName)) == (setup["domain"]["name"],)

        # The certificate becomes current, and the row stops being a request.
        assert certificate.current_generation_id == generation.id
        assert certificate.expires_at == generation.not_after
        assert _state(certificate.status) == "ISSUED"

        document = certificate_order.load(generation)
        assert document["directory_url"] == pebble_stack["directory"]
        assert document["order_url"].startswith("https://localhost:14000/")
        assert certificate_order.attempt_in_flight(document) is False
        entries = certificate_order.entries(document)
        assert len(entries) == 1
        assert entries[0]["confirmed_at"] and entries[0]["validated_at"]
        assert entries[0]["cleanup"] == certificate_order.CLEANUP_DONE
        assert certificate_order.pending_cleanup(document) == []
        assert certificate_order.cleanup_incomplete(document) == []

    # (10) Cleanup removed exactly the records this workflow created, from the
    # servers that actually held them.
    assert zone.created, "the workflow must publish a challenge record"
    assert [record.id for record in zone.created] == zone.deleted
    for view in views.values():
        assert view.txt(f"_acme-challenge.shop.{ZONE}") == ()

    # The material guard is a database constraint, not a convention: a row that
    # keeps the state but loses its key must be refused.
    async with _scoped(org_db, setup["org_id"]):
        row = await org_db.get(CertificateGeneration, uuid.UUID(setup["generation_id"]))
        assert row is not None
        row.key_ciphertext = None
        with pytest.raises(IntegrityError) as refused:
            await org_db.flush()
        assert "material_guard" in str(refused.value)
        await org_db.rollback()

    # A Pebble certificate is never presented as publicly trusted, and the read
    # model derives that from the recorded directory rather than a stored flag.
    detail = await client.get(
        f"{API}/certificates/{setup['certificate']['id']}", headers=owner["headers"]
    )
    assert detail.status_code == 200, detail.text
    body = detail.json()
    assert body["issued"] is True
    assert body["status"] == "ISSUED"
    assert body["latest_generation"]["directory"] == "pebble"
    assert body["latest_generation"]["publicly_trusted"] is False

    events = await _events(org_db, setup["org_id"], "CERTIFICATE_ISSUED")
    assert len(events) == 1
    payload = events[0].data
    assert payload["directory"] == "pebble"
    assert payload["directory_url"] == pebble_stack["directory"]
    rendered = repr(payload)
    assert "PRIVATE KEY" not in rendered
    assert "BEGIN CERTIFICATE" not in rendered
    assert TOKEN not in rendered


# --- 2. a wildcard is supported, and supported *as* a wildcard ------------------


async def test_pebble_issues_a_wildcard_with_two_values_at_one_name(
    client: Any, owner: dict, org_db: Any, pebble_stack: dict[str, Any], ownership: dict
) -> None:
    """The case that silently degrades into a single-name certificate if mishandled.

    ``app.pebble.test`` and ``*.app.pebble.test`` are two authorizations that both
    publish at ``_acme-challenge.app.pebble.test``. The certificate must carry both
    names, both values must be observable at both servers *at once*, and cleanup
    must delete both without deleting a value it did not create.
    """
    views = _view_map()
    _reset_zone(views)
    zone = _ReplicatedZone(views)
    name = f"app.{ZONE}"
    identifiers = [name, f"*.{name}"]

    async with _request(
        client, owner, org_db, ownership, name=name, identifiers=identifiers
    ) as setup:
        result, seen = await _issue(org_db, setup, zone)

    assert result.ok is True, (result.code, result.message)
    shared = f"_acme-challenge.{name}"
    assert len(zone.created) == 2, "one TXT record per authorization"
    assert len({record.value for record in zone.created}) == 2

    observed_both = [
        observation
        for observation in seen
        if len(observation.values) == 2
        and len(observation.server_answers) == 2
        and all(answer.status == STATUS_OK for answer in observation.server_answers)
    ]
    assert observed_both, [observation.server_answers for observation in seen]

    async with _scoped(org_db, setup["org_id"]):
        generation = await org_db.get(CertificateGeneration, uuid.UUID(setup["generation_id"]))
        assert generation is not None
        async with org_dek_context(org_db, setup["org_id"]) as dek:
            fullchain = _decrypted(
                dek,
                setup["org_id"],
                generation,
                PURPOSE_CERTIFICATE_CHAIN,
                generation.chain_ciphertext,
            )
        leaf = x509.load_pem_x509_certificate(_pem_blocks(fullchain)[0].encode())
        sans = leaf.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
        assert set(sans.get_values_for_type(x509.DNSName)) == set(identifiers)

        document = certificate_order.load(generation)
        entries = certificate_order.entries(document)
        assert {entry["record_name"] for entry in entries} == {shared}
        assert {entry["wildcard"] for entry in entries} == {False, True}
        assert all(entry["cleanup"] == certificate_order.CLEANUP_DONE for entry in entries)

    for view in views.values():
        assert view.txt(shared) == ()


# --- 3. a mid-propagation zone never reaches the CA's validation ----------------


async def test_a_stale_authoritative_server_holds_the_challenge_back(
    client: Any, owner: dict, org_db: Any, pebble_stack: dict[str, Any], ownership: dict
) -> None:
    """One server has the value, the other does not — so the CA is not told.

    This is the defect the propagation policy exists to prevent: a single positive
    answer used to be enough, which spends a validation attempt on a zone that is
    visibly mid-propagation. The CA here is real, and its validation is never
    started: the attempt fails on *our* observation, retryably, and the record it
    published is cleaned up.
    """
    views = _view_map()
    _reset_zone(views)
    zone = _ReplicatedZone(views, stale=("ns-b",))
    name = f"stale.{ZONE}"

    async with _request(client, owner, org_db, ownership, name=name) as setup:
        result, seen = await _issue(org_db, setup, zone, propagation_timeout=10)

    assert result.ok is False
    assert result.code == "DNS_TIMEOUT", result
    assert result.retryable is True
    assert result.terminal is False
    assert result.next_attempt_at is not None
    assert "not visible at the authoritative nameservers" in result.message

    # The disagreement was observed directly, not inferred from the failure.
    assert any(
        {answer.server: answer.status for answer in observation.server_answers}
        == {"127.0.0.2": STATUS_OK, "127.0.0.3": STATUS_NO_TXT}
        for observation in seen
    ), [observation.server_answers for observation in seen]

    async with _scoped(org_db, setup["org_id"]):
        generation = await org_db.get(CertificateGeneration, uuid.UUID(setup["generation_id"]))
        assert generation is not None
        assert _state(generation.state) == "FAILED"
        assert generation.key_ciphertext is None and generation.chain_ciphertext is None
        assert "not visible at the authoritative nameservers" in generation.last_error
        document = certificate_order.load(generation)
        assert "finalized_at" not in document or not document["finalized_at"]
        entries = certificate_order.entries(document)
        assert entries and all(
            entry["cleanup"] == certificate_order.CLEANUP_DONE for entry in entries
        )
        # No challenge was answered, so no authorization can have been validated.
        assert all(entry["validated_at"] == "" for entry in entries)

    for view in views.values():
        assert view.txt(f"_acme-challenge.{name}") == ()


# --- 4. the CA itself refuses a challenge whose TXT record is absent ------------


async def test_pebble_rejects_a_challenge_whose_txt_record_is_absent(
    pebble_stack: dict[str, Any],
) -> None:
    """The CA-side half, with the platform's propagation guard out of the way.

    The propagation check is what stops this case in the real flow, so testing it
    through the flow would only prove the guard works. Driving the production
    client directly proves the other half: when such an order is answered anyway,
    Pebble genuinely resolves DNS and refuses, with the rejection the flow's
    ``_await_validation`` classifies.
    """
    views = _view_map()
    _reset_zone(views)
    identifier = f"absent.{ZONE}"
    record_name = f"_acme-challenge.{identifier}"

    account_key = ec.generate_private_key(ec.SECP256R1())
    account_pem = account_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode("ascii")
    certificate_key = ec.generate_private_key(ec.SECP256R1())
    csr = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, identifier)]))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName(identifier)]), critical=False)
        .sign(certificate_key, hashes.SHA256())
        .public_bytes(serialization.Encoding.PEM)
    )

    assert all(view.txt(record_name) == () for view in views.values())
    async with open_acme_session(
        directory=AcmeDirectory.PEBBLE, account_key_pem=account_pem, account_url=None
    ) as acme:
        kid = await acme.register_account()
        assert kid.startswith("https://localhost:14000/")
        order = await acme.create_order(csr_pem=csr, identifiers=(identifier,))
        challenge = order.challenges[0]
        assert challenge.record_name == record_name
        await acme.accept_challenge(challenge_url=challenge.challenge_url)
        state = await acme.poll_authorization(
            authorization_url=challenge.authorization_url, timeout_seconds=30
        )

    assert state.invalid is True
    assert state.error_code == "unauthorized"
    assert "TXT" in state.error_detail.upper()

    # Nothing was published, so nothing should need cleaning up — but the zone must
    # still be empty, which the next test's setup relies on.
    assert all(view.txt(record_name) == () for view in views.values())
