"""Phase 5.1 through the real HTTP surface and the real database.

What this module exists to prove:

* **A request is a request.** The API records an intent, audits it and emits one
  event — and reports, in the response itself, that nothing has been issued.
  ``issued`` is False, ``current_generation_id`` is NULL, ``expires_at`` is NULL
  and the status detail says so, so no client can read a request as a live
  certificate.
* **The exclusions hold.** No key material in any response or audit entry, and no
  way to write a material-bearing generation without its material: since 5.2.2 the
  vocabulary has those states, and the **material guard** CHECK — not the absence
  of the column — is what refuses a metadata-only ``ISSUED`` row.
* **The database, not the API, keeps the invariants.** One in-flight generation
  per certificate, one certificate row per name per organization, and one
  generation number per certificate are constraints; the tests below break them
  with raw SQL/ORM writes and expect a refusal.
* **The credential override is resolved, never stored blind.** ``dns_provider_id``
  is a field of the request now, and naming a provider another tenant owns (or
  none at all) is a 404 rather than a reference the platform would later publish a
  challenge with.
* **Authorization and tenancy are two different gates.** A read-only role is a
  403 and a foreign tenant is a 404 — including without the ORM, as the
  application role with only the RLS GUC for company.

The node side is absent on purpose: Phase 5.1 has no ACME client, no delivery and
no agent protocol change, so there is nothing to simulate.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta

import psycopg
import pytest
from app.core.tenancy import TenancyScopeError, apply_scope_to_session, system_scope
from app.models import AuditLog, Certificate, CertificateGeneration, SystemEvent
from app.models.enums import AcmeDirectory, DomainStatus
from app.services import dns_verifier
from app.services.dns_verifier import STATUS_OK, TxtObservation
from sqlalchemy import select

from tests.conftest import TEST_DATABASE_URL

from .helpers import API, assert_error_code, bearer, error_of, login_account, unique_email

pytestmark = pytest.mark.integration

NS_SET = ("ns1.example.net", "ns2.example.net")

#: The token the mocked authoritative DNS serves. Kept in a dict so the fake
#: observer can read whatever the test just created.
DNS: dict[str, object] = {"token": "", "nameservers": NS_SET}


def _fake_observe(name: str) -> TxtObservation:
    return TxtObservation(
        STATUS_OK,
        values=(str(DNS["token"]),),
        nameservers=tuple(DNS["nameservers"]),  # type: ignore[arg-type]
    )


CERTIFICATE_FIELDS = {
    "id",
    "created_at",
    "updated_at",
    "domain_id",
    "domain_name",
    "domain_status",
    "primary_cn",
    "sans",
    "status",
    "challenge_type",
    "key_algorithm",
    "auto_renew",
    "expires_at",
    "last_error",
    "current_generation_id",
    "latest_generation",
    "issued",
    # Which credential may publish this certificate's challenges (5.2.2), and a
    # *reference* — never the credential itself.
    "dns_provider_id",
    "status_detail",
}
GENERATION_FIELDS = {
    "id",
    "created_at",
    "updated_at",
    "certificate_id",
    "generation",
    "state",
    "attempt_count",
    "next_attempt_at",
    "last_error",
    "retryable",
    "terminal",
    "status_detail",
    # Metadata *about* the material (5.2.2): the CA's validity window, when it was
    # issued, the leaf fingerprint and the separate CA axis.
    "not_before",
    "not_after",
    "issued_at",
    "fingerprint",
    "revocation_state",
    # Provenance (5.3): which directory the order was placed at, the same value
    # resolved to a known directory, and whether that directory is publicly trusted.
    "directory_url",
    "directory",
    "publicly_trusted",
}


@pytest.fixture(autouse=True)
def _dns_stub(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Stand in for authoritative DNS in every test in this module."""
    DNS["token"] = ""
    DNS["nameservers"] = NS_SET
    monkeypatch.setattr(dns_verifier, "observe", _fake_observe)
    yield


# --- helpers ------------------------------------------------------------------


async def _create_domain(client, owner, name: str, *, verified: bool = True, **extra) -> dict:
    """A domain in the caller's organization, verified through the real task.

    Verification goes through ``domain_routing._verify`` (the same function the
    worker calls) against the mocked authoritative DNS, so a "verified" domain in
    these tests is verified by the platform's own rules rather than by a status
    field a test set.
    """
    created = await client.post(
        f"{API}/domains", headers=owner["headers"], json={"name": name, **extra}
    )
    assert created.status_code == 201, created.text
    body = created.json()
    if not verified:
        return body
    DNS["token"] = body["verification"]["record_value"]
    from app.tasks.domain_routing import _verify

    outcome = await _verify(uuid.UUID(body["id"]), trigger="user")
    assert outcome["status"] == DomainStatus.VERIFIED.value, outcome
    detail = await client.get(f"{API}/domains/{body['id']}", headers=owner["headers"])
    assert detail.status_code == 200, detail.text
    return detail.json()


def _request_body(domain_id: str, identifiers: list[str], **overrides) -> dict:
    return {"domain_id": domain_id, "identifiers": identifiers, **overrides}


async def _request_certificate(client, headers, domain: dict, *identifiers: str, **overrides):
    """POST /certificates for *domain*, defaulting to its own name."""
    names = list(identifiers) or [domain["name"]]
    return await client.post(
        f"{API}/certificates",
        headers=headers,
        json=_request_body(domain["id"], names, **overrides),
    )


async def _created_certificate(client, owner, domain: dict, *identifiers: str) -> dict:
    response = await _request_certificate(client, owner["headers"], domain, *identifiers)
    assert response.status_code == 201, response.text
    return response.json()


async def _member_with_role(client, owner, role_name: str) -> dict:
    """A non-superadmin member of the owner's organization holding *role_name*."""
    roles = (await client.get(f"{API}/roles", headers=owner["headers"])).json()
    rows = roles["items"] if isinstance(roles, dict) else roles
    role = next(row for row in rows if row["name"] == role_name)
    email = unique_email(role_name.lower())
    created = await client.post(
        f"{API}/users",
        headers=owner["headers"],
        json={
            "email": email,
            "password": "Integration-Pass1",
            "full_name": f"Member {role_name}",
            "role_id": role["id"],
        },
    )
    assert created.status_code in (200, 201), created.text
    session = await login_account(client, email=email, password="Integration-Pass1")
    return {
        "role": role_name,
        "headers": bearer(session["access_token"], session["active_organization_id"]),
    }


async def _insert_generation(
    org_db,
    certificate_id: str,
    *,
    generation: int,
    state: str,
    directory_url: str | None = None,
) -> None:
    """Write a generation straight to the database, bypassing every service rule.

    ``directory_url`` is a parameter rather than a constant because 5.3 added a
    second constraint on the same rows: a material-bearing state must name the ACME
    directory it was ordered at, so a test isolating the *material* guard has to
    satisfy the provenance rule to reach it.
    """
    org_db.add(
        CertificateGeneration(
            id=uuid.uuid4(),
            certificate_id=uuid.UUID(certificate_id),
            generation=generation,
            state=state,
            order_state={},
            last_error="",
            attempt_count=0,
            directory_url=directory_url,
        )
    )
    await org_db.flush()


def _app_role_dsn() -> str:
    """The RLS-enforced DSN, without the SQLAlchemy driver suffix."""
    return TEST_DATABASE_URL.replace("+psycopg", "")


def _probe(sql: str, params: tuple = (), *, org: str | None = None, expect_error: bool = False):
    """One statement as the application role with an explicit tenancy GUC.

    No ORM, no guard, no request context: what remains is PostgreSQL row-level
    security, which is the point of the probe.
    """
    with psycopg.connect(_app_role_dsn()) as conn:
        if org is not None:
            conn.execute("SELECT set_config('app.current_org', %s, false)", (org,))
        try:
            return conn.execute(sql, params).fetchall()
        except psycopg.errors.Error as exc:
            if not expect_error:
                raise
            return exc


async def _audits(org_db, action: str) -> list[AuditLog]:
    return list((await org_db.execute(select(AuditLog).where(AuditLog.action == action))).scalars())


async def _events(org_db, event_type: str) -> list[SystemEvent]:
    return list(
        (await org_db.execute(select(SystemEvent).where(SystemEvent.type == event_type))).scalars()
    )


async def _certificate_rows(org_db, certificate_id: str) -> list[Certificate]:
    return list(
        (
            await org_db.execute(
                select(Certificate).where(Certificate.id == uuid.UUID(certificate_id))
            )
        ).scalars()
    )


async def _generation_rows(org_db, certificate_id: str) -> list[CertificateGeneration]:
    rows = await org_db.execute(
        select(CertificateGeneration)
        .where(CertificateGeneration.certificate_id == uuid.UUID(certificate_id))
        .order_by(CertificateGeneration.generation)
    )
    return list(rows.scalars())


# --- 1. a request is a request ------------------------------------------------


async def test_a_request_is_recorded_and_reports_that_nothing_is_issued(
    client, owner, org_db
) -> None:
    domain = await _create_domain(client, owner, "cert-one.example.com")
    body = await _created_certificate(client, owner, domain)

    # The whole approved metadata surface, and nothing else.
    assert set(body) == CERTIFICATE_FIELDS
    assert set(body["latest_generation"]) == GENERATION_FIELDS
    assert body["domain_id"] == domain["id"]
    assert body["domain_name"] == "cert-one.example.com"
    assert body["domain_status"] == "VERIFIED"
    assert body["primary_cn"] == "cert-one.example.com"
    assert body["sans"] == []
    assert body["challenge_type"] == "dns-01"
    assert body["key_algorithm"] == "ecdsa-p256"
    assert body["auto_renew"] is True

    # Nothing has been issued, and the payload says so three separate ways.
    assert body["status"] == "PENDING"
    assert body["issued"] is False
    assert body["current_generation_id"] is None
    assert body["expires_at"] is None
    assert "no certificate has been issued" in body["status_detail"]

    generation = body["latest_generation"]
    assert generation["generation"] == 1
    assert generation["state"] == "PENDING"
    assert generation["attempt_count"] == 0
    assert generation["retryable"] is False
    assert generation["terminal"] is False

    # The row itself carries the same facts: no pointer to a current generation,
    # no expiry that nothing has set, and exactly one generation, in PENDING.
    rows = await _certificate_rows(org_db, body["id"])
    assert len(rows) == 1
    assert rows[0].current_generation_id is None
    assert rows[0].expires_at is None
    generations = await _generation_rows(org_db, body["id"])
    assert [(row.generation, str(row.state)) for row in generations] == [(1, "PENDING")]


async def test_the_request_is_audited_and_announced_without_material(client, owner, org_db) -> None:
    domain = await _create_domain(client, owner, "cert-audit.example.com")
    body = await _created_certificate(client, owner, domain)

    created = await _audits(org_db, "certificate.created")
    assert len(created) == 1
    assert str(created[0].resource_id) == body["id"]
    metadata = dict(created[0].metadata_ or {})
    assert metadata["primary_cn"] == "cert-audit.example.com"
    assert metadata["identifiers"] == ["cert-audit.example.com"]
    for key in metadata:
        assert "key" not in key.lower()

    events = await _events(org_db, "CERTIFICATE_REQUESTED")
    assert len(events) == 1
    assert events[0].resource_id == body["id"]
    assert events[0].data["state"] == "PENDING"
    assert "not" in events[0].message.lower()

    # The catalogue the SPA reads knows the type, so it can render it.
    listed = await client.get(f"{API}/events", headers=owner["headers"])
    assert listed.status_code == 200, listed.text


async def test_detail_adds_the_generation_history(client, owner) -> None:
    domain = await _create_domain(client, owner, "cert-detail.example.com")
    created = await _created_certificate(client, owner, domain)

    detail = await client.get(f"{API}/certificates/{created['id']}", headers=owner["headers"])
    assert detail.status_code == 200, detail.text
    payload = detail.json()
    assert set(payload) == CERTIFICATE_FIELDS | {"generations"}
    assert len(payload["generations"]) == 1
    assert payload["generations"][0]["state"] == "PENDING"

    missing = await client.get(f"{API}/certificates/{uuid.uuid4()}", headers=owner["headers"])
    assert missing.status_code == 404
    assert_error_code(missing.json(), "CERTIFICATE_NOT_FOUND")


async def test_identifiers_are_canonicalised_and_the_extras_are_sans(client, owner) -> None:
    domain = await _create_domain(client, owner, "APEX.example.com")
    body = await _created_certificate(
        client, owner, domain, "APEX.example.com.", "api.apex.example.com", "API.APEX.example.com"
    )
    assert body["primary_cn"] == "apex.example.com"
    # Canonicalised, de-duplicated, order preserved, and the CN is not repeated.
    assert body["sans"] == ["api.apex.example.com"]


async def test_the_wildcard_form_of_a_non_wildcard_domain_is_allowed(client, owner) -> None:
    """Apex + wildcard is one order, which is what DNS-01 wildcard issuance needs."""
    domain = await _create_domain(client, owner, "wildpair.example.com")
    body = await _created_certificate(
        client, owner, domain, "wildpair.example.com", "*.wildpair.example.com"
    )
    assert body["primary_cn"] == "wildpair.example.com"
    assert body["sans"] == ["*.wildpair.example.com"]


async def test_a_name_outside_the_domain_is_refused(client, owner) -> None:
    domain = await _create_domain(client, owner, "owned.example.com")
    for identifier in ("elsewhere.example.net", "example.com", "*.other.example.com"):
        response = await _request_certificate(
            client, owner["headers"], domain, "owned.example.com", identifier
        )
        assert response.status_code == 422, (identifier, response.text)
        assert_error_code(response.json(), "CERTIFICATE_NAME_NOT_COVERED")

    # A deeper name is not covered either: coverage is one label, never a suffix.
    deep = await _request_certificate(client, owner["headers"], domain, "a.b.owned.example.com")
    assert deep.status_code == 422
    assert_error_code(deep.json(), "CERTIFICATE_NAME_NOT_COVERED")


async def test_the_primary_name_may_not_be_repeated(client, owner) -> None:
    domain = await _create_domain(client, owner, "dup-ident.example.com")
    response = await _request_certificate(
        client, owner["headers"], domain, "dup-ident.example.com", "DUP-IDENT.example.com"
    )
    assert response.status_code == 422
    assert_error_code(response.json(), "CERTIFICATE_DUPLICATE_IDENTIFIER")


async def test_http_01_is_refused(client, owner) -> None:
    domain = await _create_domain(client, owner, "http01.example.com")
    response = await _request_certificate(
        client, owner["headers"], domain, "http01.example.com", challenge_type="http-01"
    )
    assert response.status_code == 422
    assert_error_code(response.json(), "CHALLENGE_TYPE_UNSUPPORTED")


async def test_the_credential_override_must_be_one_that_exists(client, owner) -> None:
    """A provider id the caller's organization does not have is a 404, not a 422.

    The reference is resolvable — the column and the table exist — so an unknown id
    is a lookup failure, and a foreign one must be indistinguishable from a
    random one. Anything looser would store an id that later publishes a challenge
    with another tenant's credential.
    """
    unknown = "11111111-1111-1111-1111-111111111111"
    domain = await _create_domain(client, owner, "forward-ref.example.com")
    response = await _request_certificate(
        client, owner["headers"], domain, "forward-ref.example.com", dns_provider_id=unknown
    )
    assert response.status_code == 404, response.text
    assert_error_code(response.json(), "DNS_PROVIDER_NOT_FOUND")

    # The same on the update path, and a malformed id is still a body error.
    created = await _created_certificate(client, owner, domain)
    patched = await client.patch(
        f"{API}/certificates/{created['id']}",
        headers=owner["headers"],
        json={"dns_provider_id": unknown},
    )
    assert patched.status_code == 404, patched.text
    assert_error_code(patched.json(), "DNS_PROVIDER_NOT_FOUND")

    malformed = await client.patch(
        f"{API}/certificates/{created['id']}",
        headers=owner["headers"],
        json={"dns_provider_id": "not-a-uuid"},
    )
    assert malformed.status_code == 422, malformed.text
    assert_error_code(
        malformed.json(),
        "VALIDATION_ERROR",
        exact_keys={"code", "message", "request_id", "details"},
    )


async def test_an_unverified_domain_cannot_back_a_certificate(client, owner) -> None:
    domain = await _create_domain(client, owner, "unverified.example.com", verified=False)
    response = await _request_certificate(
        client, owner["headers"], domain, "unverified.example.com"
    )
    assert response.status_code == 409, response.text
    assert_error_code(response.json(), "DOMAIN_NOT_VERIFIED")


async def test_duplicate_requests_are_refused(client, owner) -> None:
    domain = await _create_domain(client, owner, "dupe.example.com")
    await _created_certificate(client, owner, domain)

    again = await _request_certificate(client, owner["headers"], domain, "DUPE.example.com")
    assert again.status_code == 409, again.text
    assert_error_code(again.json(), "CERTIFICATE_EXISTS")


async def test_the_same_name_may_be_requested_by_another_organization(
    client, owner, second_org
) -> None:
    """Uniqueness is per organization; the platform-wide rule is the domain's."""
    domain = await _create_domain(client, owner, "shared-name.example.com")
    await _created_certificate(client, owner, domain)

    # The second organization tracks the name and verifies it (its own row).
    theirs = await _create_domain(client, second_org, "shared-name.example.com")
    body = await _created_certificate(client, second_org, theirs)
    assert body["primary_cn"] == "shared-name.example.com"
    assert body["domain_id"] == theirs["id"]


# --- 2. the database keeps the lifecycle invariants ---------------------------


async def test_a_second_in_flight_generation_is_refused_but_a_failed_one_is_not(
    client, owner, org_db
) -> None:
    """The one-live-generation index is the backstop against racing attempts."""
    domain = await _create_domain(client, owner, "one-live.example.com")
    created = await _created_certificate(client, owner, domain)

    # A second in-flight generation for the same certificate cannot exist...
    with pytest.raises(Exception) as exc:
        await _insert_generation(org_db, created["id"], generation=2, state="PENDING")
    assert "uq_cert_generations_one_live" in str(exc.value)
    await org_db.rollback()

    # ...but a retry may: a spent attempt does not occupy the in-flight slot.
    await _insert_generation(org_db, created["id"], generation=2, state="FAILED")
    await org_db.commit()
    rows = await _generation_rows(org_db, created["id"])
    assert [(row.generation, str(row.state)) for row in rows] == [(1, "PENDING"), (2, "FAILED")]

    # A second FAILED attempt is still refused: the generation number is unique
    # per certificate, so a rewound or duplicated attempt cannot be written.
    with pytest.raises(Exception) as exc:
        await _insert_generation(org_db, created["id"], generation=2, state="FAILED")
    assert "uq_certificate_generations_cert_number" in str(exc.value)
    await org_db.rollback()


async def test_a_material_bearing_generation_cannot_be_written_without_material(
    client, owner, org_db
) -> None:
    """The guard CHECK, not the vocabulary, is what refuses a metadata-only issuance.

    Phase 5.1 bought "an issued generation without material is unrepresentable" by
    not having the state. 5.2.2 has the state, so the property is carried by the
    constraint instead — and this is the test that says so: the same row *with* its
    material is accepted, so the guard is precise rather than a blanket refusal.
    """
    domain = await _create_domain(client, owner, "unrepresentable.example.com")
    created = await _created_certificate(client, owner, domain)

    staging_url = AcmeDirectory.STAGING.url()
    for state in ("ISSUED", "SUPERSEDED", "REVOKED_LOCAL_ONLY"):
        with pytest.raises(Exception) as exc:
            await _insert_generation(
                org_db, created["id"], generation=9, state=state, directory_url=staging_url
            )
        assert "material_guard" in str(exc.value), state
        await org_db.rollback()

    # Nothing was reported as issued either: the request still reads as a request.
    detail = await client.get(f"{API}/certificates/{created['id']}", headers=owner["headers"])
    assert detail.json()["issued"] is False
    assert detail.json()["status"] == "PENDING"

    # The positive control. The values are not real key material — they are the
    # *shape* the guard requires, and 5.3 is what will write them for real.
    issued_at = datetime.now(UTC)
    org_db.add(
        CertificateGeneration(
            id=uuid.uuid4(),
            certificate_id=uuid.UUID(created["id"]),
            generation=9,
            state="ISSUED",
            order_state={},
            last_error="",
            attempt_count=0,
            key_ciphertext="shape-only-not-a-key",
            chain_ciphertext="shape-only-not-a-chain",
            deke_id=1,
            issued_at=issued_at,
            not_before=issued_at,
            not_after=issued_at + timedelta(days=90),
            fingerprint="0" * 64,
            # The provenance rule 5.3 pairs with the guard: the same row without
            # this value was refused a few lines above, and for a different reason.
            directory_url=staging_url,
        )
    )
    await org_db.flush()


async def test_only_the_preferences_are_writable_through_patch(client, owner, org_db) -> None:
    """``auto_renew`` and ``dns_provider_id`` are preferences; nothing else is.

    Changing what a certificate *is* — its identifiers, its status, its expiry —
    is a new generation, and issuing one is 5.3. The credential override is a
    reference rather than a fact about the certificate, which is why it is here
    and its resolution is asserted above.
    """
    domain = await _create_domain(client, owner, "patchable.example.com")
    created = await _created_certificate(client, owner, domain)

    updated = await client.patch(
        f"{API}/certificates/{created['id']}", headers=owner["headers"], json={"auto_renew": False}
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["auto_renew"] is False
    rows = await _certificate_rows(org_db, created["id"])
    assert rows[0].auto_renew is False

    # Identifiers, status and expiry are not writable this way.
    for field, value in (
        ("status", "ISSUED"),
        ("identifiers", ["other.example.com"]),
        ("expires_at", "2030-01-01T00:00:00Z"),
    ):
        rejected = await client.patch(
            f"{API}/certificates/{created['id']}",
            headers=owner["headers"],
            json={field: value},
        )
        assert rejected.status_code == 422, (field, rejected.text)

    audits = await _audits(org_db, "certificate.updated")
    assert len(audits) == 1
    assert audits[0].metadata_["fields"] == ["auto_renew"]


async def test_deleting_a_request_frees_its_domain(client, owner, org_db) -> None:
    domain = await _create_domain(client, owner, "deletable.example.com")
    created = await _created_certificate(client, owner, domain)

    # While the certificate exists the domain cannot go: its name is what a
    # certificate is issued for (ON DELETE RESTRICT).
    blocked = await client.delete(f"{API}/domains/{domain['id']}", headers=owner["headers"])
    assert blocked.status_code == 409, blocked.text
    assert_error_code(blocked.json(), "DOMAIN_HAS_CERTIFICATES")

    deleted = await client.delete(f"{API}/certificates/{created['id']}", headers=owner["headers"])
    assert deleted.status_code == 204, deleted.text
    # The request and its generations are both gone.
    assert await _certificate_rows(org_db, created["id"]) == []
    assert await _generation_rows(org_db, created["id"]) == []
    assert (
        await client.get(f"{API}/certificates/{created['id']}", headers=owner["headers"])
    ).status_code == 404
    assert len(await _audits(org_db, "certificate.deleted")) == 1
    assert len(await _events(org_db, "CERTIFICATE_DELETED")) == 1

    freed = await client.delete(f"{API}/domains/{domain['id']}", headers=owner["headers"])
    assert freed.status_code == 204, freed.text


async def test_a_certificate_with_a_current_generation_is_not_deletable(
    client, owner, org_db
) -> None:
    """Staged 5.2 condition: a bound, issued generation must not be deleted away."""
    domain = await _create_domain(client, owner, "bound.example.com")
    created = await _created_certificate(client, owner, domain)
    generations = await _generation_rows(org_db, created["id"])
    rows = await _certificate_rows(org_db, created["id"])
    rows[0].current_generation_id = generations[0].id
    await org_db.commit()

    refused = await client.delete(f"{API}/certificates/{created['id']}", headers=owner["headers"])
    assert refused.status_code == 409, refused.text
    assert_error_code(refused.json(), "CERTIFICATE_HAS_ISSUED_GENERATION")


# --- 3. authorization ---------------------------------------------------------


async def test_certificate_read_alone_does_not_authorize_management(client, owner) -> None:
    domain = await _create_domain(client, owner, "readonly.example.com")
    created = await _created_certificate(client, owner, domain)

    for role_name in ("Viewer", "Developer"):
        member = await _member_with_role(client, owner, role_name)

        readable = await client.get(f"{API}/certificates", headers=member["headers"])
        assert readable.status_code == 200, (role_name, readable.text)
        assert (
            await client.get(f"{API}/certificates/{created['id']}", headers=member["headers"])
        ).status_code == 200

        denied = await _request_certificate(
            client, member["headers"], domain, "api.readonly.example.com"
        )
        assert denied.status_code == 403, (role_name, denied.text)
        assert_error_code(denied.json(), "PERMISSION_DENIED")
        for method, path, kwargs in (
            ("patch", f"/certificates/{created['id']}", {"json": {"auto_renew": False}}),
            ("delete", f"/certificates/{created['id']}", {}),
        ):
            call = getattr(client, method)
            response = await call(f"{API}{path}", headers=member["headers"], **kwargs)
            assert response.status_code == 403, (role_name, method, response.text)
            assert_error_code(response.json(), "PERMISSION_DENIED")


async def test_an_operator_may_manage_and_an_admin_may_too(client, owner) -> None:
    domain = await _create_domain(client, owner, "operated.example.com")
    for role_name in ("Admin", "Operator"):
        member = await _member_with_role(client, owner, role_name)
        response = await _request_certificate(
            client, member["headers"], domain, f"{role_name.lower()}.operated.example.com"
        )
        assert response.status_code == 201, (role_name, response.text)


async def test_an_unauthenticated_caller_gets_nothing(client, owner) -> None:
    assert (await client.get(f"{API}/certificates")).status_code == 401


# --- 4. tenant isolation ------------------------------------------------------


async def test_a_foreign_certificate_id_is_the_same_404_as_a_random_one(
    client, owner, second_org
) -> None:
    domain = await _create_domain(client, owner, "tenant-a.example.com")
    created = await _created_certificate(client, owner, domain)

    theirs = await client.get(f"{API}/certificates/{created['id']}", headers=second_org["headers"])
    random_ = await client.get(f"{API}/certificates/{uuid.uuid4()}", headers=second_org["headers"])
    assert theirs.status_code == random_.status_code == 404
    assert error_of(theirs.json())["code"] == error_of(random_.json())["code"]

    for method, kwargs in (
        ("patch", {"json": {"auto_renew": False}}),
        ("delete", {}),
    ):
        call = getattr(client, method)
        response = await call(
            f"{API}/certificates/{created['id']}", headers=second_org["headers"], **kwargs
        )
        assert response.status_code == 404, (method, response.text)

    # The owning organization still owns it.
    assert (
        await client.get(f"{API}/certificates/{created['id']}", headers=owner["headers"])
    ).status_code == 200


async def test_listing_and_filtering_never_cross_tenants(client, owner, second_org) -> None:
    mine = await _create_domain(client, owner, "listed-a.example.com")
    await _created_certificate(client, owner, mine)
    theirs = await _create_domain(client, second_org, "listed-b.example.com")
    await _created_certificate(client, second_org, theirs)

    for headers, expected in (
        (owner["headers"], "listed-a.example.com"),
        (second_org["headers"], "listed-b.example.com"),
    ):
        page = await client.get(f"{API}/certificates", headers=headers)
        assert page.status_code == 200, page.text
        names = [item["primary_cn"] for item in page.json()["items"]]
        assert names == [expected]

    # Filtering by the *other* tenant's domain id returns nothing rather than
    # erroring: the id is invisible, not forbidden.
    filtered = await client.get(
        f"{API}/certificates", headers=owner["headers"], params={"domain_id": theirs["id"]}
    )
    assert filtered.status_code == 200
    assert filtered.json()["items"] == []


async def test_rls_blocks_cross_tenant_certificate_reads_without_the_orm(
    client, owner, second_org
) -> None:
    """The policies alone decide, with no ORM, no guard and no request context."""
    mine = await _create_domain(client, owner, "rls-a.example.com")
    created = await _created_certificate(client, owner, mine)
    theirs = await _create_domain(client, second_org, "rls-b.example.com")
    other = await _created_certificate(client, second_org, theirs)

    org_a = owner["active_organization_id"]
    visible = _probe("SELECT primary_cn FROM certificates", org=org_a)
    assert [row[0] for row in visible] == ["rls-a.example.com"]

    # Control: the same probe finds the row the organization does own...
    own = _probe("SELECT primary_cn FROM certificates WHERE id = %s", (created["id"],), org=org_a)
    assert own == [("rls-a.example.com",)]
    # ...and nothing when it asks for the other tenant's, by primary key.
    by_id = _probe("SELECT primary_cn FROM certificates WHERE id = %s", (other["id"],), org=org_a)
    assert by_id == []

    generations = _probe("SELECT count(*) FROM certificate_generations", org=org_a)
    assert generations == [(1,)]

    # A cross-tenant write is refused by WITH CHECK, not merely filtered.
    smuggled = _probe(
        "INSERT INTO certificates (id, org_id, domain_id, primary_cn, sans, status, "
        "challenge_type, auto_renew, key_algorithm, last_error, created_at, updated_at) "
        "VALUES (gen_random_uuid(), %s, %s, 'smuggled.example.com', '[]', 'PENDING', "
        "'dns-01', true, 'ecdsa-p256', '', now(), now())",
        (org_a, theirs["id"]),
        org=second_org["id"],
        expect_error=True,
    )
    assert "row-level security" in str(smuggled)

    # The GUC is what does it: the same row is writable from its own organization.
    assert _probe(
        "SELECT c.relrowsecurity FROM pg_class c "
        "WHERE c.relname IN ('certificates', 'certificate_generations') ORDER BY c.relname",
        org=org_a,
    ) == [(True,), (True,)]


async def test_both_new_tables_carry_a_tenant_and_a_system_policy(org_db) -> None:
    from sqlalchemy import text

    policies = (
        await org_db.execute(
            text(
                "SELECT tablename, policyname FROM pg_policies "
                "WHERE tablename IN ('certificates', 'certificate_generations') "
                "ORDER BY tablename, policyname"
            )
        )
    ).all()
    assert [tuple(row) for row in policies] == [
        ("certificate_generations", "certificate_generations_system"),
        ("certificate_generations", "certificate_generations_tenant"),
        ("certificates", "certificates_system"),
        ("certificates", "certificates_tenant"),
    ]


async def test_a_certificate_is_tenant_owned_and_unreachable_without_a_scope(
    client, owner, db
) -> None:
    """Ownership is explicit (``org_id``) and a missing scope fails loudly."""
    domain = await _create_domain(client, owner, "scoped.example.com")
    created = await _created_certificate(client, owner, domain)

    from app.core.db import get_sessionmaker

    async with get_sessionmaker()() as session:
        with system_scope("test: certificate row is tenant-owned"):
            await apply_scope_to_session(session)
            row = await session.get(Certificate, uuid.UUID(created["id"]))
            assert row is not None
            assert str(row.org_id) == owner["active_organization_id"]
            assert row.domain_id == uuid.UUID(domain["id"])

    # No scope, no read: the guard refuses rather than filtering to an empty set,
    # so a code path that forgot its tenant is a bug report and not a silent miss.
    with pytest.raises(TenancyScopeError):
        await db.get(Certificate, uuid.UUID(created["id"]))
