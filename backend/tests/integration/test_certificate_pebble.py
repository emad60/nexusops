"""Phase 5.3.1 and 5.3.2 — issuance through the **real** ACME protocol, against Pebble.

The other issuance integration tests prove the flows against their seams: a fake
session, a fake zone, a fake resolver. That is the right test for the state
machine, but it cannot show that the production adapter speaks RFC 8555 or that
the platform's own DNS observation is what lets a real CA validate. This module
is that second claim: one CA, one zone, the real client, the real propagation
code and the real persistence path. Since 5.3.2 it also carries the **manual
DNS-01** workflow through that same real CA: the operator publishes the record by
hand at the isolated authoritative servers, so no provider is constructed and no
credential exists anywhere in the flow.

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

import asyncio
import json
import logging
import re
import shutil
import subprocess
import time
import uuid
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import dns.resolver
import httpx
import pytest
from app.core.config import get_settings
from app.core.tenancy import apply_scope_to_session, org_scope
from app.models import Certificate, CertificateGeneration, SystemEvent
from app.models.enums import AcmeDirectory, DomainStatus
from app.models.observability import AuditLog
from app.providers.dns import CredentialCheck, TxtRecord, ZoneRef, ZoneResolution
from app.services import certificate_order, dns_propagation, dns_provider_service, dns_verifier
from app.services.acme import open_acme_session
from app.services.certificate_issuance import CODE_AWAITING_MANUAL, issue_generation
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


# === Phase 5.3.2 — the manual workflow against the same real CA =================


class _Setups:
    """The manual request's rows, reloaded when a test needs the current document.

    The confirmation endpoint writes the challenge document from its own session,
    so the instance a test loaded at setup time would keep the document it was
    loaded with — and the resume attempt would then act on a stale view. This is
    the same trap the fake-CA suite documents; here it matters even more, because
    the thing being reloaded decides whether a real CA is allowed to validate.
    """

    def __init__(self, db: Any, setup: dict[str, Any]) -> None:
        self.db = db
        self.setup = setup

    async def rows(self) -> tuple[Any, Any]:
        async with _scoped(self.db, self.setup["org_id"]):
            generation = await self.db.get(
                CertificateGeneration, uuid.UUID(self.setup["generation_id"])
            )
            certificate = await self.db.get(Certificate, uuid.UUID(self.setup["certificate"]["id"]))
            assert generation is not None and certificate is not None
            await self.db.refresh(generation)
            await self.db.refresh(certificate)
            return generation, certificate

    async def generation(self) -> Any:
        return (await self.rows())[0]


def _forbidden_provider(kind: Any) -> Any:
    """A manual certificate has no automated publisher; constructing one is a defect."""
    raise AssertionError(f"the manual DNS-01 flow must not construct a DNS provider ({kind})")


@pytest.fixture
def manual_dns(monkeypatch: pytest.MonkeyPatch) -> list[TxtObservation]:
    """The confirmation endpoint observes through the **real** authoritative servers.

    ``check_once`` reads ``dns_propagation.observe_txt_record`` as its default
    observer. Replacing that default with the bootstrap-resolver wrapper keeps the
    wire path real — the delegation comes from ``127.0.0.2`` and the answers come
    from the two authoritative servers — and only supplies the one fact a test
    host cannot know: that ``pebble.test`` is delegated to those views.
    """
    observer, seen = _recording_observer()
    monkeypatch.setattr(dns_propagation, "observe_txt_record", observer)
    return seen


class _TaskRecorder:
    """Records the worker handoff instead of performing it, like the deployments suite."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def delay(self, generation_id: str) -> None:
        self.calls.append(generation_id)


@asynccontextmanager
async def _manual_request(
    client: Any,
    owner: dict,
    org_db: Any,
    state: dict[str, Any],
    *,
    name: str,
) -> AsyncIterator[dict[str, Any]]:
    """A verified domain and a **manual** certificate request with no credential."""
    domain = await _create_domain(client, owner, state, name)
    created = await client.post(
        f"{API}/certificates",
        headers=owner["headers"],
        json={"domain_id": domain["id"], "identifiers": [name], "dns_mode": "manual"},
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
    yield {
        "org_id": org_id,
        "domain": domain,
        "certificate": certificate,
        "certificate_row": certificate_row,
        "generation": generation,
        "generation_id": certificate["latest_generation"]["id"],
    }


async def _issue_manual(
    db: Any,
    setup: dict[str, Any],
    *,
    observer: Any,
    now: datetime | None = None,
) -> Any:
    """One attempt through the real manual flow, with the provider seam forbidden."""
    generation, certificate = await _Setups(db, setup).rows()
    with org_scope(setup["org_id"]):
        await apply_scope_to_session(db)
        result = await issue_generation(
            db,
            generation,
            certificate=certificate,
            settings=_pebble_settings(),
            now=now or datetime.now(UTC),
            provider_factory=_forbidden_provider,
            observer=observer,
            checkpoint=db.commit,
        )
        await db.commit()
    return result


def _publish_views(views: dict[str, _View], name: str, value: str) -> None:
    """The operator's own act: a TXT record, written outside this platform."""
    for view in views.values():
        view.publish(name, value)


def _challenge_url(setup: dict[str, Any]) -> str:
    return f"{API}/certificates/{setup['certificate']['id']}/challenge"


def _assert_no_material(text: str, value: str) -> None:
    """No private key, certificate PEM, challenge value or DNS credential in *text*."""
    assert "PRIVATE KEY" not in text
    assert "BEGIN CERTIFICATE" not in text
    assert value not in text
    assert TOKEN not in text


async def _settled() -> None:
    """Let a post-commit handoff run: ``after_commit`` schedules it, never awaits it.

    The handoff is a task created on the running loop when the request's transaction
    commits, so it lands one iteration after the request returns. Yielding twice is
    enough for the loop to run it — and if it were never scheduled, the assertions
    after this call would see an empty list rather than a stale one.
    """
    await asyncio.sleep(0)
    await asyncio.sleep(0)


# --- 5. the manual workflow, one real CA, no credential ------------------------


async def test_pebble_issues_a_manual_certificate_without_any_dns_credential(
    client: Any,
    owner: dict,
    org_db: Any,
    pebble_stack: dict[str, Any],
    ownership: dict,
    manual_dns: list[TxtObservation],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The whole manual path through Pebble: wait, publish, confirm, resume, issue.

    One test again, because the ten claims are one fact: the operator-published
    record is what a real CA validated, and the artifacts left behind are the ones
    the design says the workflow produces. ``provider_factory`` raises on *any*
    call, so the successful issuance below is also the proof that manual mode does
    not construct, let alone call, an automated DNS provider.
    """
    caplog.set_level(logging.INFO)
    views = _view_map()
    _reset_zone(views)
    observer, _seen = _recording_observer()
    name = f"manual.{ZONE}"
    record_name = f"_acme-challenge.{name}"

    from app.tasks import certificates as certificate_tasks

    tasks = _TaskRecorder()
    monkeypatch.setattr(certificate_tasks, "issue_certificate", tasks)

    async with _manual_request(client, owner, org_db, ownership, name=name) as setup:
        # Creating a request hands its first attempt to the worker. That handoff is
        # not what this test counts, so it is drained and forgotten first.
        await _settled()
        tasks.calls.clear()

        # (1) No credential is attached, and the row says the customer publishes.
        assert setup["certificate_row"].dns_provider_id is None
        assert _state(setup["certificate_row"].dns_mode) == "manual"
        assert setup["certificate"]["dns_mode"] == "manual"

        # (2) The first attempt places the order at Pebble and stops.
        first = await _issue_manual(org_db, setup, observer=observer)
        assert first.ok is False
        assert first.waiting is True
        assert first.code == CODE_AWAITING_MANUAL
        assert _state(first.state) == "AWAITING_MANUAL"

        setups = _Setups(org_db, setup)
        generation = await setups.generation()
        assert generation.attempt_count == 1
        assert generation.next_attempt_at is None
        assert generation.last_error == ""
        assert generation.key_ciphertext is None and generation.chain_ciphertext is None
        assert generation.directory_url == pebble_stack["directory"]
        document = certificate_order.load(generation)
        order_url = document["order_url"]
        assert order_url.startswith("https://localhost:14000/")

        instructions = certificate_order.manual_instructions(document)
        assert len(instructions) == 1
        value = instructions[0]["record_value"]
        assert re.fullmatch(r"[A-Za-z0-9_-]{43}", value), value
        assert instructions[0]["record_name"] == record_name
        assert instructions[0]["problem"] == ""

        # (3) The authenticated, organization-scoped endpoint returns the record and
        # nothing else that is secret.
        shown = await client.get(_challenge_url(setup), headers=owner["headers"])
        assert shown.status_code == 200, shown.text
        body = shown.json()
        assert body["records"][0]["record_name"] == record_name
        assert body["records"][0]["record_value"] == value
        assert body["records"][0]["confirmed"] is False
        assert body["ready"] is False
        assert body["cleanup"]["required"] is False, "nothing is obsolete while waiting"
        # The value appears exactly where an operator needs it — as the record to
        # publish, and in the (not yet required) cleanup instruction naming what to
        # remove afterwards — and nowhere else in the document.
        remainder = shown.json()
        remainder["records"][0]["record_value"] = ""
        for record in remainder["cleanup"]["records"]:
            record["remove_values"] = []
        assert value not in json.dumps(remainder)
        assert "PRIVATE KEY" not in shown.text
        assert "BEGIN CERTIFICATE" not in shown.text
        assert TOKEN not in shown.text

        # (4) Confirming while the record is absent cannot advance anything: no
        # attempt, no CA answer, no second order.
        absent = await client.post(
            f"{_challenge_url(setup)}/confirm", headers=owner["headers"], json={}
        )
        assert absent.status_code == 202, absent.text
        absent_body = absent.json()
        assert absent_body["ready"] is False
        assert absent_body["resume_requested"] is False
        assert absent_body["records"][0]["observed"] is False
        assert absent_body["records"][0]["confirmed"] is True
        assert tasks.calls == [], "an unobserved confirmation must not queue an attempt"
        assert all(view.txt(record_name) == () for view in views.values())
        generation = await setups.generation()
        assert _state(generation.state) == "AWAITING_MANUAL"
        assert generation.attempt_count == 1
        assert certificate_order.load(generation)["order_url"] == order_url

        # (5) The operator publishes, outside this platform, at both authorities.
        _publish_views(views, record_name, value)
        assert all(view.txt(record_name) == (value,) for view in views.values())

        # (6) Confirmation re-observes for real, and a repeat is idempotent.
        confirmed = await client.post(
            f"{_challenge_url(setup)}/confirm", headers=owner["headers"], json={}
        )
        assert confirmed.status_code == 202, confirmed.text
        confirmed_body = confirmed.json()
        assert confirmed_body["ready"] is True
        assert confirmed_body["resume_requested"] is True
        assert confirmed_body["records"][0]["observed"] is True
        assert confirmed_body["records"][0]["validated"] is False, "only the CA validates"
        stamp = confirmed_body["records"][0]["confirmed_at"]
        assert stamp
        await _settled()
        assert tasks.calls == [setup["generation_id"]]

        repeated = await client.post(
            f"{_challenge_url(setup)}/confirm", headers=owner["headers"], json={}
        )
        assert repeated.status_code == 202, repeated.text
        assert repeated.json()["records"][0]["confirmed_at"] == stamp
        assert repeated.json()["ready"] is True
        # Every handoff carries the generation id and nothing else — no value, no key.
        assert all(call == setup["generation_id"] for call in tasks.calls)

        # The confirmation observed the record at both real servers, over DNS.
        agreeing = [
            observation
            for observation in manual_dns
            if observation.status == STATUS_OK
            and len(observation.server_answers) == 2
            and all(answer.status == STATUS_OK for answer in observation.server_answers)
        ]
        assert agreeing, [observation.server_answers for observation in manual_dns]

        # (7) The resume finishes the **same** order through Pebble's validation and
        # finalization. The order URL is recorded across the pause, so this is also
        # the proof that no second order was placed.
        second = await _issue_manual(org_db, setup, observer=observer)
        assert second.ok is True, (second.code, second.message)
        assert _state(second.state) == "ISSUED"
        assert "pebble" in second.message.lower()

        generation = await setups.generation()
        certificate = (await setups.rows())[1]
        assert certificate_order.load(generation)["order_url"] == order_url
        assert generation.attempt_count == 2, "the resume is the second attempt"

        # (8, 9) Encrypted persistence with the DEK generation, provenance and
        # validity metadata — and a chain that answers the key that was generated.
        assert _state(generation.state) == "ISSUED"
        assert generation.fingerprint and len(generation.fingerprint) == 64
        assert generation.issued_at is not None
        assert generation.not_before is not None and generation.not_after > generation.not_before
        assert generation.last_error == ""
        assert generation.deke_id is not None and generation.deke_id >= 1
        assert generation.directory_url == pebble_stack["directory"]
        assert generation.key_ciphertext and generation.chain_ciphertext
        for stored in (generation.key_ciphertext, generation.chain_ciphertext):
            assert "PRIVATE KEY" not in stored
            assert "BEGIN CERTIFICATE" not in stored

        async with _scoped(org_db, setup["org_id"]):
            async with org_dek_context(org_db, setup["org_id"]) as dek:
                key_pem = _decrypted(
                    dek,
                    setup["org_id"],
                    generation,
                    PURPOSE_CERTIFICATE_KEY,
                    generation.key_ciphertext,
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
        assert tuple(sans.get_values_for_type(x509.DNSName)) == (name,)

        # (10) The generation is `ISSUED` only after the chain was verified and
        # stored: the row above is the post-persistence view, and the certificate
        # points at it.
        assert certificate.current_generation_id == generation.id
        assert certificate.expires_at == generation.not_after
        assert _state(certificate.status) == "ISSUED"

        document = certificate_order.load(generation)
        entries = certificate_order.entries(document)
        assert entries and all(entry["mode"] == certificate_order.MODE_MANUAL for entry in entries)
        assert all(entry["validated_at"] for entry in entries)
        assert all(entry["cleanup"] == certificate_order.CLEANUP_NOT_REQUIRED for entry in entries)
        assert certificate_order.pending_cleanup(document) == []
        assert certificate_order.cleanup_incomplete(document) == []

    # Cleanup never deletes: the record is the customer's, and it is still there.
    assert all(view.txt(record_name) == (value,) for view in views.values())

    after = await client.get(_challenge_url(setup), headers=owner["headers"])
    assert after.status_code == 200, after.text
    cleanup = after.json()["cleanup"]
    assert cleanup["required"] is True
    assert cleanup["records"][0]["record_name"] == record_name
    assert cleanup["records"][0]["remove_values"] == [value]
    assert "did not create" in cleanup["note"]

    # The read models: issued, Pebble-labelled, not publicly trusted, no value.
    detail = await client.get(
        f"{API}/certificates/{setup['certificate']['id']}", headers=owner["headers"]
    )
    assert detail.status_code == 200, detail.text
    detail_body = detail.json()
    assert detail_body["issued"] is True
    assert detail_body["status"] == "ISSUED"
    assert detail_body["latest_generation"]["directory"] == "pebble"
    assert detail_body["latest_generation"]["publicly_trusted"] is False
    listed = await client.get(f"{API}/certificates", headers=owner["headers"])
    assert listed.status_code == 200, listed.text
    for response in (detail, listed):
        _assert_no_material(response.text, value)

    # The audit trail names the action, not the record's value or any material.
    async with _scoped(org_db, setup["org_id"]):
        audit_rows = list(
            (
                await org_db.execute(
                    select(AuditLog).where(AuditLog.action == "certificate.challenge_confirmed")
                )
            ).scalars()
        )
    assert audit_rows
    for row in audit_rows:
        _assert_no_material(repr(dict(row.metadata_ or {})), value)

    # The waiting event names the record, and neither it nor the confirmation or
    # issuance events carries the value, a key or a credential.
    awaiting = await _events(org_db, setup["org_id"], "CERTIFICATE_AWAITING_MANUAL")
    confirmed_events = await _events(org_db, setup["org_id"], "CERTIFICATE_CHALLENGE_CONFIRMED")
    issued_events = await _events(org_db, setup["org_id"], "CERTIFICATE_ISSUED")
    assert len(awaiting) == 1
    assert awaiting[0].data["record_names"] == [record_name]
    assert confirmed_events and len(issued_events) == 1
    for event in (*awaiting, *confirmed_events, *issued_events):
        _assert_no_material(repr(dict(event.data)), value)

    # And the logs: structured events carry identifiers and statuses only.
    _assert_no_material(caplog.text, value)


# --- 6. a wrong or absent record never authorizes issuance ---------------------


async def test_a_wrong_manual_value_never_authorizes_the_order(
    client: Any,
    owner: dict,
    org_db: Any,
    pebble_stack: dict[str, Any],
    ownership: dict,
    manual_dns: list[TxtObservation],
) -> None:
    """A wrong TXT value is observed as absent, not trusted as "published".

    The confirmation is a request to look; what the platform looks at is the
    challenge digest the CA produced. A record with the right name and the wrong
    value changes nothing: not ready, no attempt spent, no CA answer, one order.
    Once the right value is published, the same order resumes and issues.
    """
    views = _view_map()
    _reset_zone(views)
    observer, _seen = _recording_observer()
    name = f"wrong.{ZONE}"
    record_name = f"_acme-challenge.{name}"
    wrong = "A" * 43

    async with _manual_request(client, owner, org_db, ownership, name=name) as setup:
        first = await _issue_manual(org_db, setup, observer=observer)
        assert first.waiting is True

        setups = _Setups(org_db, setup)
        document = certificate_order.load(await setups.generation())
        value = certificate_order.manual_instructions(document)[0]["record_value"]
        order_url = document["order_url"]

        _publish_views(views, record_name, wrong)
        observed_wrong = await client.post(
            f"{_challenge_url(setup)}/confirm", headers=owner["headers"], json={}
        )
        assert observed_wrong.status_code == 202, observed_wrong.text
        body = observed_wrong.json()
        assert body["ready"] is False
        assert body["resume_requested"] is False
        assert body["records"][0]["confirmed"] is True
        assert body["records"][0]["observed"] is False
        assert all(
            answer["serves_expected"] is False for answer in body["observation"]["nameservers"]
        )

        # A dispatch that arrives anyway is refused without spending an attempt
        # and without touching the open order.
        again = await _issue_manual(org_db, setup, observer=observer)
        assert again.ok is False
        assert again.code == CODE_AWAITING_MANUAL
        generation = await setups.generation()
        assert generation.attempt_count == 1
        assert _state(generation.state) == "AWAITING_MANUAL"
        assert certificate_order.load(generation)["order_url"] == order_url

        # The correct value, and only it, makes the order resumable.
        for view in views.values():
            view.remove(record_name, wrong)
        _publish_views(views, record_name, value)
        ready = await client.post(
            f"{_challenge_url(setup)}/confirm", headers=owner["headers"], json={}
        )
        assert ready.status_code == 202, ready.text
        assert ready.json()["ready"] is True
        assert ready.json()["resume_requested"] is True

        second = await _issue_manual(org_db, setup, observer=observer)
        assert second.ok is True, (second.code, second.message)
        assert _state(second.state) == "ISSUED"
        assert certificate_order.load(await setups.generation())["order_url"] == order_url

    # Manual cleanup is an instruction: the value the operator published is still
    # in the zone until they remove it.
    assert all(view.txt(record_name) == (value,) for view in views.values())


# --- 7. one stale authority is enough to delay the CA -------------------------


async def test_one_stale_authority_delays_the_manual_validation(
    client: Any,
    owner: dict,
    org_db: Any,
    pebble_stack: dict[str, Any],
    ownership: dict,
    manual_dns: list[TxtObservation],
) -> None:
    """The manual path inherits the automated policy: every server that answers.

    A zone mid-propagation is exactly the state a manual operator creates: their
    provider accepted the write, one authority has it, one does not. Confirming
    then must not tell Pebble the challenge is ready; it must say what it saw. The
    same attempt resumes once both servers agree.
    """
    views = _view_map()
    _reset_zone(views)
    observer, _seen = _recording_observer()
    name = f"stale-manual.{ZONE}"
    record_name = f"_acme-challenge.{name}"
    addresses = {address for address, _control in VIEWS.values()}

    async with _manual_request(client, owner, org_db, ownership, name=name) as setup:
        first = await _issue_manual(org_db, setup, observer=observer)
        assert first.waiting is True

        setups = _Setups(org_db, setup)
        document = certificate_order.load(await setups.generation())
        value = certificate_order.manual_instructions(document)[0]["record_value"]
        order_url = document["order_url"]

        # Only one authority has it: publish there, leave the other empty.
        views["ns-a"].publish(record_name, value)
        assert views["ns-a"].txt(record_name) == (value,)
        assert views["ns-b"].txt(record_name) == ()

        partial = await client.post(
            f"{_challenge_url(setup)}/confirm", headers=owner["headers"], json={}
        )
        assert partial.status_code == 202, partial.text
        body = partial.json()
        assert body["ready"] is False
        assert body["resume_requested"] is False
        summary = {answer["server"]: answer for answer in body["observation"]["nameservers"]}
        assert set(summary) == addresses
        serving = {address for address, answer in summary.items() if answer["serves_expected"]}
        assert serving == {"127.0.0.2"}

        # The disagreement was observed over DNS, not inferred from the response.
        assert any(
            {answer.server: answer.status for answer in observation.server_answers}
            == {"127.0.0.2": STATUS_OK, "127.0.0.3": STATUS_NO_TXT}
            for observation in manual_dns
        ), [observation.server_answers for observation in manual_dns]

        # And the CA was not told: still waiting, still the first attempt, same order.
        generation = await setups.generation()
        assert _state(generation.state) == "AWAITING_MANUAL"
        assert generation.attempt_count == 1
        assert certificate_order.load(generation)["order_url"] == order_url

        # Publication reaches the second authority; the same order now resumes.
        views["ns-b"].publish(record_name, value)
        agreed = await client.post(
            f"{_challenge_url(setup)}/confirm", headers=owner["headers"], json={}
        )
        assert agreed.status_code == 202, agreed.text
        assert agreed.json()["ready"] is True
        assert all(
            answer["serves_expected"] for answer in agreed.json()["observation"]["nameservers"]
        )

        second = await _issue_manual(org_db, setup, observer=observer)
        assert second.ok is True, (second.code, second.message)
        assert _state(second.state) == "ISSUED"
        assert certificate_order.load(await setups.generation())["order_url"] == order_url


# --- 8. an interrupted resume recovers the persisted order ---------------------


async def test_an_interrupted_manual_resume_recovers_without_a_second_order(
    client: Any,
    owner: dict,
    org_db: Any,
    pebble_stack: dict[str, Any],
    ownership: dict,
    manual_dns: list[TxtObservation],
) -> None:
    """A worker that died mid-attempt is lost work; the order it held is resumable.

    The stamp is the only thing that distinguishes "a worker is on it" from "a
    worker died on it". Recovery must count the lost attempt and resume the order
    the operator was already answering — placing a second order would change the
    challenge value underneath them and invalidate the record they published.
    """
    views = _view_map()
    _reset_zone(views)
    observer, _seen = _recording_observer()
    name = f"recover.{ZONE}"
    record_name = f"_acme-challenge.{name}"

    async with _manual_request(client, owner, org_db, ownership, name=name) as setup:
        first = await _issue_manual(org_db, setup, observer=observer)
        assert first.waiting is True

        setups = _Setups(org_db, setup)
        generation = await setups.generation()
        document = certificate_order.load(generation)
        value = certificate_order.manual_instructions(document)[0]["record_value"]
        order_url = document["order_url"]

        # A stamp a worker left behind when it died, with no finish time.
        document["attempt_started_at"] = (datetime.now(UTC) - timedelta(days=2)).isoformat()
        document["attempt_finished_at"] = ""
        async with _scoped(org_db, setup["org_id"]):
            row = await org_db.get(CertificateGeneration, uuid.UUID(setup["generation_id"]))
            assert row is not None
            certificate_order.store(row, document)
            await org_db.commit()

        recovered = await _issue_manual(org_db, setup, observer=observer)
        assert recovered.ok is False
        assert recovered.waiting is True
        assert recovered.code == CODE_AWAITING_MANUAL

        generation = await setups.generation()
        document = certificate_order.load(generation)
        assert _state(generation.state) == "AWAITING_MANUAL"
        assert generation.attempt_count == 2, "the lost attempt is counted, then retried"
        assert certificate_order.attempt_unfinished(document) is False
        assert document["order_url"] == order_url, "recovery resumed, it did not re-order"
        assert certificate_order.manual_instructions(document)[0]["record_value"] == value

        # The operator's record is still the one the open order expects.
        _publish_views(views, record_name, value)
        ready = await client.post(
            f"{_challenge_url(setup)}/confirm", headers=owner["headers"], json={}
        )
        assert ready.status_code == 202, ready.text
        assert ready.json()["ready"] is True

        finished = await _issue_manual(org_db, setup, observer=observer)
        assert finished.ok is True, (finished.code, finished.message)
        assert _state(finished.state) == "ISSUED"
        assert certificate_order.load(await setups.generation())["order_url"] == order_url

    assert all(view.txt(record_name) == (value,) for view in views.values())
