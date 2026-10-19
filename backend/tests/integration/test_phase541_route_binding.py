"""Phase 5.4.1 — certificate ↔ route binding foundation.

The association delivery (5.4) derives its target set from is only worth having if
it is (a) tenant-consistent in the database, (b) impossible to create for a
certificate that must not be served, and (c) re-evaluated on every read rather
than trusted. These cases pin all three, plus the boundary this slice must not
cross: binding changes no ``scheme``, renders no TLS and queues no operation.

The certificate rows are built directly in the tenant session: issuance is Phase
5.3's path and already covered by its own suite, and the point here is what a
*bound* certificate's metadata implies, not how it was obtained.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from app.core.db import get_sessionmaker
from app.models import Certificate, CertificateGeneration, Domain, Route
from app.models.enums import (
    AcmeDirectory,
    CertificateGenerationState,
    CertificateStatus,
    DomainStatus,
)
from app.services import dns_verifier
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from tests.integration.conftest import ScopedSession
from tests.integration.helpers import API, bearer, unique_email
from tests.integration.test_phase4_routing import (
    DNS,
    NS_SET,
    _create_domain,
    _create_route,
    _fake_observe,
    _proxy_ready_node,
    _verified_domain,
)

pytestmark = pytest.mark.integration

DIRECTORY = AcmeDirectory.STAGING.url()


@pytest.fixture(autouse=True)
def _dns_stub(monkeypatch: pytest.MonkeyPatch):
    """The verification helpers in the Phase-4 module read this module's stub."""
    DNS["token"] = ""
    DNS["nameservers"] = NS_SET
    monkeypatch.setattr(dns_verifier, "observe", _fake_observe)
    yield


# --- helpers -------------------------------------------------------------------


async def _certificate(
    scoped_db,
    owner: dict,
    *,
    domain: dict,
    identifiers: list[str] | None = None,
    status: CertificateStatus = CertificateStatus.ISSUED,
    suspended: bool = False,
    expires_in: timedelta = timedelta(days=30),
    with_generation: bool = True,
) -> dict:
    """Insert a certificate whose stored metadata matches *status*.

    ``status`` is written as given rather than derived: the read model derives it
    from the generation, while the binding check reads the row plus the current
    generation, so both are set to describe the same fact.
    """
    org_id = uuid.UUID(owner["active_organization_id"])
    identifiers = identifiers or [domain["name"]]
    now = datetime.now(UTC)
    certificate = Certificate(
        org_id=org_id,
        domain_id=uuid.UUID(domain["id"]),
        primary_cn=identifiers[0],
        sans=identifiers[1:],
        status=status,
        dns_mode="automated",
    )
    if suspended:
        certificate.suspended_at = now
        certificate.suspension_reason = "ownership_lost"
    scoped_db.add(certificate)
    await scoped_db.flush()

    if with_generation:
        not_after = now + expires_in
        generation = CertificateGeneration(
            org_id=org_id,
            certificate_id=certificate.id,
            generation=1,
            state=CertificateGenerationState.ISSUED,
            directory_url=DIRECTORY,
            key_ciphertext="test-key-ciphertext",
            chain_ciphertext="test-chain-ciphertext",
            fingerprint="a" * 64,
            not_before=now - timedelta(days=10),
            not_after=not_after,
            deke_id=1,
            issued_at=now,
        )
        scoped_db.add(generation)
        await scoped_db.flush()
        certificate.current_generation_id = generation.id
        certificate.expires_at = not_after
        await scoped_db.flush()

    await scoped_db.commit()
    return {
        "id": str(certificate.id),
        "primary_cn": certificate.primary_cn,
        "identifiers": identifiers,
    }


async def _foreign_certificate(client, second_org: dict, *, name: str) -> dict:
    """A certificate owned by the *second* organization, inserted in its scope."""
    domain = await _verified_domain(client, {"headers": second_org["headers"]}, name)
    async with get_sessionmaker()() as session:
        foreign = ScopedSession(session, org_id=uuid.UUID(second_org["id"]))
        return await _certificate(
            foreign, {"active_organization_id": second_org["id"]}, domain=domain
        )


async def _renewed_certificate(scoped_db, owner: dict, *, domain: dict) -> dict:
    """A certificate whose newest generation is current and whose old one is gone.

    Renewal does not create a second certificate row, so a binding to the
    certificate follows the new generation without a rebind — the case this test
    exists for.
    """
    certificate = await _certificate(scoped_db, owner, domain=domain)
    org_id = uuid.UUID(owner["active_organization_id"])
    row = await scoped_db.get(Certificate, uuid.UUID(certificate["id"]))
    assert row is not None and row.current_generation_id is not None
    current = await scoped_db.get(CertificateGeneration, row.current_generation_id)
    assert current is not None
    current.state = CertificateGenerationState.SUPERSEDED

    now = datetime.now(UTC)
    renewal = CertificateGeneration(
        org_id=org_id,
        certificate_id=row.id,
        generation=2,
        state=CertificateGenerationState.ISSUED,
        directory_url=DIRECTORY,
        key_ciphertext="renewed-key",
        chain_ciphertext="renewed-chain",
        fingerprint="b" * 64,
        not_before=now - timedelta(hours=1),
        not_after=now + timedelta(days=60),
        deke_id=1,
        issued_at=now,
    )
    scoped_db.add(renewal)
    await scoped_db.flush()
    row.current_generation_id = renewal.id
    row.expires_at = renewal.not_after
    await scoped_db.commit()
    return {**certificate, "generation": 2}


async def _bind(client, owner: dict, route: dict, certificate: dict, *, headers=None):
    return await client.post(
        f"{API}/routes/{route['id']}/certificate",
        headers=headers or owner["headers"],
        json={"certificate_id": certificate["id"]},
    )


async def _unbind(client, owner: dict, route: dict, *, headers=None):
    return await client.delete(
        f"{API}/routes/{route['id']}/certificate", headers=headers or owner["headers"]
    )


async def _route_detail(client, owner: dict, route: dict) -> dict:
    response = await client.get(f"{API}/routes/{route['id']}", headers=owner["headers"])
    assert response.status_code == 200, response.text
    return response.json()


async def _setup(
    client,
    owner: dict,
    *,
    name: str = "bind.example.com",
    hostname: str | None = None,
) -> tuple[dict, dict, dict]:
    node, _agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, name)
    created = await _create_route(
        client,
        owner,
        domain=domain,
        node_id=node["id"],
        container_id=container_id,
        **({"hostname": hostname} if hostname else {}),
    )
    assert created.status_code == 201, created.text
    return created.json(), node, domain


# --- 1. the happy path ---------------------------------------------------------


async def test_a_covered_certificate_binds_and_reports_eligible(client, owner, org_db):
    route, _node, domain = await _setup(client, owner)
    certificate = await _certificate(org_db, owner, domain=domain)

    response = await _bind(client, owner, route, certificate)
    assert response.status_code == 200, response.text
    assert response.json()["certificate_id"] == certificate["id"]

    detail = await _route_detail(client, owner, route)
    assert detail["certificate_id"] == certificate["id"]
    # Disabled route: the association is stored, but delivery has no target yet.
    assert detail["certificate_binding"]["state"] == "INELIGIBLE"
    assert detail["certificate_binding"]["code"] == "ROUTE_DISABLED"
    assert detail["certificate_binding"]["certificate_id"] == certificate["id"]

    enabled = await client.post(f"{API}/routes/{route['id']}/enable", headers=owner["headers"])
    assert enabled.status_code == 200, enabled.text
    detail = await _route_detail(client, owner, route)
    binding = detail["certificate_binding"]
    assert binding["state"] == "BOUND"
    assert binding["eligible"] is True
    assert binding["code"] == "ROUTE_CERTIFICATE_ELIGIBLE"
    assert binding["generation"] == 1


async def test_binding_does_not_touch_http_serving_or_queue_work(client, owner, org_db):
    """The one thing this slice must not do: activate HTTPS."""
    route, _node, domain = await _setup(client, owner)
    certificate = await _certificate(org_db, owner, domain=domain)

    async def operation_count() -> int:
        return int(await org_db.scalar(text("SELECT count(*) FROM operations")) or 0)

    before = await operation_count()
    response = await _bind(client, owner, route, certificate)
    assert response.status_code == 200, response.text
    assert response.json()["scheme"] == "http"
    assert response.json()["url"] == f"http://{route['hostname']}{route['path']}"
    assert await operation_count() == before

    detail = await _route_detail(client, owner, route)
    assert detail["scheme"] == "http"
    assert detail["url"].startswith("http://")


# --- 2. SAN coverage, including wildcard boundaries ----------------------------


@pytest.mark.parametrize(
    ("identifiers", "hostname_overrides", "expected_code"),
    [
        (["*.example.com"], {"hostname": "api.example.com"}, None),
        (["example.com"], {"hostname": "api.example.com"}, "CERTIFICATE_HOSTNAME_NOT_COVERED"),
        (["*.example.com"], {"hostname": "example.com"}, "CERTIFICATE_HOSTNAME_NOT_COVERED"),
        (["other.example.com"], {"hostname": "example.com"}, "CERTIFICATE_HOSTNAME_NOT_COVERED"),
    ],
)
async def test_binding_enforces_the_san_boundary(
    client, owner, org_db, identifiers, hostname_overrides, expected_code
):
    node, _agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _verified_domain(client, owner, "example.com")
    created = await _create_route(
        client,
        owner,
        domain=domain,
        node_id=node["id"],
        container_id=container_id,
        **hostname_overrides,
    )
    assert created.status_code == 201, created.text
    route = created.json()
    certificate = await _certificate(org_db, owner, domain=domain, identifiers=identifiers)

    response = await _bind(client, owner, route, certificate)
    if expected_code is None:
        assert response.status_code == 200, response.text
        assert response.json()["certificate_id"] == certificate["id"]
    else:
        assert response.status_code == 409, response.text
        assert response.json()["error"]["code"] == expected_code
        assert (await _route_detail(client, owner, route))["certificate_id"] is None


# --- 3. tenancy ----------------------------------------------------------------


async def test_a_cross_organization_certificate_is_a_404_not_a_bind(client, owner, second_org):
    route, _node, _domain = await _setup(client, owner)
    foreign = await _foreign_certificate(client, second_org, name="other.example.com")

    response = await _bind(client, owner, route, foreign)
    assert response.status_code == 404, response.text
    assert response.json()["error"]["code"] == "CERTIFICATE_NOT_FOUND"
    assert (await _route_detail(client, owner, route))["certificate_id"] is None


async def test_the_database_refuses_a_cross_tenant_pair_even_without_the_service(
    client, owner, org_db, second_org
):
    """The composite FK is the proof; the service check is the first line."""
    route, _node, _domain = await _setup(client, owner)
    foreign = await _foreign_certificate(client, second_org, name="other.example.com")

    with pytest.raises(IntegrityError):
        await org_db.execute(
            text("UPDATE routes SET certificate_id = :cid WHERE id = :rid"),
            {"cid": foreign["id"], "rid": route["id"]},
        )
    await org_db.rollback()
    assert (await _route_detail(client, owner, route))["certificate_id"] is None


async def test_rls_hides_the_bound_route_from_the_other_tenant(client, owner, org_db, second_org):
    route, _node, domain = await _setup(client, owner)
    certificate = await _certificate(org_db, owner, domain=domain)
    assert (await _bind(client, owner, route, certificate)).status_code == 200

    async with get_sessionmaker()() as session:
        foreign = ScopedSession(session, org_id=uuid.UUID(second_org["id"]))
        assert await foreign.get(Route, uuid.UUID(route["id"])) is None
        assert await foreign.get(Certificate, uuid.UUID(certificate["id"])) is None


async def test_raw_sql_as_the_app_role_cannot_see_the_bound_route(
    client, owner, org_db, second_org
):
    """No ORM, no session guard — the RLS policy alone hides the association."""
    from tests.integration.test_tenant_isolation import _raw_probe

    route, _node, domain = await _setup(client, owner)
    certificate = await _certificate(org_db, owner, domain=domain)
    bound = await _bind(client, owner, route, certificate)
    assert bound.status_code == 200, bound.text

    mine = _raw_probe(
        "SELECT certificate_id FROM routes WHERE id = %s",
        (route["id"],),
        org=owner["active_organization_id"],
    )
    assert [str(row[0]) for row in mine] == [certificate["id"]]

    # The other organization sees neither the route nor a row naming the certificate.
    assert (
        _raw_probe("SELECT 1 FROM routes WHERE id = %s", (route["id"],), org=second_org["id"]) == []
    )
    assert (
        _raw_probe(
            "SELECT org_id FROM routes WHERE certificate_id = %s",
            (certificate["id"],),
            org=second_org["id"],
        )
        == []
    )


# --- 4. authorization ----------------------------------------------------------


async def _user_with(client, owner: dict, permissions: list[str], label: str) -> dict[str, str]:
    role = await client.post(
        f"{API}/roles",
        headers=owner["headers"],
        json={"name": f"{label} {uuid.uuid4().hex[:6]}", "permissions": permissions},
    )
    assert role.status_code == 201, role.text
    created = await client.post(
        f"{API}/users",
        headers=owner["headers"],
        json={
            "email": unique_email(label),
            "password": "Scoped-Pass1!",
            "full_name": label,
            "role_id": role.json()["id"],
        },
    )
    assert created.status_code == 201, created.text
    login = await client.post(
        f"{API}/auth/login",
        json={"email": created.json()["user"]["email"], "password": "Scoped-Pass1!"},
    )
    assert login.status_code == 200, login.text
    return bearer(login.json()["access_token"], owner["active_organization_id"])


async def test_bind_and_unbind_require_domain_and_certificate_manage(client, owner, org_db):
    route, _node, domain = await _setup(client, owner)
    certificate = await _certificate(org_db, owner, domain=domain)

    # domain.manage but not certificate.manage
    route_only = await _user_with(client, owner, ["domain.read", "domain.manage"], "route-manager")
    denied = await _bind(client, owner, route, certificate, headers=route_only)
    assert denied.status_code == 403, denied.text
    assert denied.json()["error"]["code"] == "PERMISSION_DENIED"

    # A read-only viewer fails on the first requirement.
    viewer = await _user_with(client, owner, ["domain.read", "certificate.read"], "binding-viewer")
    denied = await _bind(client, owner, route, certificate, headers=viewer)
    assert denied.status_code == 403, denied.text
    assert (await _route_detail(client, owner, route))["certificate_id"] is None

    # The same two permissions gate unbinding.
    assert (await _bind(client, owner, route, certificate)).status_code == 200
    denied = await _unbind(client, owner, route, headers=route_only)
    assert denied.status_code == 403, denied.text
    assert (await _route_detail(client, owner, route))["certificate_id"] == certificate["id"]


# --- 5. certificate and domain eligibility ------------------------------------


async def test_an_unverified_domain_cannot_bind(client, owner, org_db):
    node, _agent_token, container_id = await _proxy_ready_node(client, owner)
    domain = await _create_domain(client, owner, "pending.example.com")
    created = await _create_route(
        client, owner, domain=domain, node_id=node["id"], container_id=container_id
    )
    assert created.status_code == 201, created.text
    certificate = await _certificate(org_db, owner, domain=domain)

    response = await _bind(client, owner, created.json(), certificate)
    assert response.status_code == 409, response.text
    assert response.json()["error"]["code"] == "DOMAIN_NOT_VERIFIED"


@pytest.mark.parametrize(
    ("certificate_kwargs", "expected_code"),
    [
        ({"status": CertificateStatus.PENDING, "with_generation": False}, "CERTIFICATE_NOT_ISSUED"),
        ({"status": CertificateStatus.FAILED, "with_generation": False}, "CERTIFICATE_NOT_ISSUED"),
        ({"suspended": True}, "CERTIFICATE_SUSPENDED"),
        ({"expires_in": timedelta(days=-1)}, "CERTIFICATE_EXPIRED"),
    ],
)
async def test_an_ineligible_certificate_cannot_be_bound(
    client, owner, org_db, certificate_kwargs, expected_code
):
    route, _node, domain = await _setup(client, owner)
    certificate = await _certificate(org_db, owner, domain=domain, **certificate_kwargs)

    response = await _bind(client, owner, route, certificate)
    assert response.status_code == 409, response.text
    assert response.json()["error"]["code"] == expected_code
    assert (await _route_detail(client, owner, route))["certificate_id"] is None


async def test_a_renewed_generation_is_picked_up_without_a_rebind(client, owner, org_db):
    route, _node, domain = await _setup(client, owner)
    await client.post(f"{API}/routes/{route['id']}/enable", headers=owner["headers"])
    certificate = await _renewed_certificate(org_db, owner, domain=domain)

    response = await _bind(client, owner, route, certificate)
    assert response.status_code == 200, response.text
    detail = await _route_detail(client, owner, route)
    assert detail["certificate_binding"]["eligible"] is True
    assert detail["certificate_binding"]["generation"] == 2


# --- 6. lifecycle changes do not silently erase or retarget --------------------


async def test_disablement_makes_the_binding_ineligible_without_erasing_it(client, owner, org_db):
    route, _node, domain = await _setup(client, owner)
    certificate = await _certificate(org_db, owner, domain=domain)
    assert (await _bind(client, owner, route, certificate)).status_code == 200
    await client.post(f"{API}/routes/{route['id']}/enable", headers=owner["headers"])

    disabled = await client.post(f"{API}/routes/{route['id']}/disable", headers=owner["headers"])
    assert disabled.status_code == 200, disabled.text
    detail = await _route_detail(client, owner, route)
    assert detail["certificate_id"] == certificate["id"]
    assert detail["certificate_binding"]["state"] == "INELIGIBLE"
    assert detail["certificate_binding"]["code"] == "ROUTE_DISABLED"

    await client.post(f"{API}/routes/{route['id']}/enable", headers=owner["headers"])
    assert (await _route_detail(client, owner, route))["certificate_binding"]["state"] == "BOUND"


async def test_domain_ownership_loss_makes_the_binding_ineligible(client, owner, org_db):
    route, _node, domain = await _setup(client, owner)
    certificate = await _certificate(org_db, owner, domain=domain)
    assert (await _bind(client, owner, route, certificate)).status_code == 200
    await client.post(f"{API}/routes/{route['id']}/enable", headers=owner["headers"])

    row = await org_db.get(Domain, uuid.UUID(domain["id"]))
    assert row is not None
    row.status = DomainStatus.STALE
    await org_db.commit()

    detail = await _route_detail(client, owner, route)
    assert detail["certificate_id"] == certificate["id"]
    assert detail["certificate_binding"]["state"] == "INELIGIBLE"
    assert detail["certificate_binding"]["code"] == "DOMAIN_NOT_VERIFIED"


async def test_hostname_change_off_the_certificate_makes_the_binding_ineligible(
    client, owner, org_db
):
    route, _node, domain = await _setup(client, owner)
    certificate = await _certificate(org_db, owner, domain=domain)
    assert (await _bind(client, owner, route, certificate)).status_code == 200
    await client.post(f"{API}/routes/{route['id']}/enable", headers=owner["headers"])

    moved = await client.patch(
        f"{API}/routes/{route['id']}",
        headers=owner["headers"],
        json={"hostname": f"api.{domain['name']}"},
    )
    assert moved.status_code == 200, moved.text
    detail = await _route_detail(client, owner, route)
    assert detail["certificate_id"] == certificate["id"]
    assert detail["certificate_binding"]["code"] == "CERTIFICATE_HOSTNAME_NOT_COVERED"


async def test_deleting_the_route_drops_the_binding_and_keeps_the_certificate(
    client, owner, org_db
):
    route, _node, domain = await _setup(client, owner)
    certificate = await _certificate(org_db, owner, domain=domain)
    assert (await _bind(client, owner, route, certificate)).status_code == 200

    deleted = await client.delete(f"{API}/routes/{route['id']}", headers=owner["headers"])
    assert deleted.status_code == 204, deleted.text
    listed = await client.get(f"{API}/certificates/{certificate['id']}", headers=owner["headers"])
    assert listed.status_code == 200, listed.text


async def test_a_referenced_certificate_cannot_be_deleted(client, owner, org_db):
    route, _node, domain = await _setup(client, owner)
    certificate = await _certificate(org_db, owner, domain=domain)
    assert (await _bind(client, owner, route, certificate)).status_code == 200

    deleted = await client.delete(
        f"{API}/certificates/{certificate['id']}", headers=owner["headers"]
    )
    assert deleted.status_code == 409, deleted.text
    assert deleted.json()["error"]["code"] == "CERTIFICATE_IN_USE"

    # Unbinding is the explicit act that makes deletion possible again; the
    # certificate still refuses on its issued generation, which is 5.1's rule.
    assert (await _unbind(client, owner, route)).status_code == 204
    again = await client.delete(f"{API}/certificates/{certificate['id']}", headers=owner["headers"])
    assert again.status_code == 409, again.text
    assert again.json()["error"]["code"] == "CERTIFICATE_HAS_ISSUED_GENERATION"


# --- 7. conflicting updates --------------------------------------------------


async def test_a_conflicting_binding_requires_an_explicit_unbind(client, owner, org_db):
    # Two individually eligible certificates for the same route: one exact name,
    # one wildcard covering it. The conflict, not coverage, is what is under test.
    route, _node, domain = await _setup(client, owner, hostname="api.bind.example.com")
    await client.post(f"{API}/routes/{route['id']}/enable", headers=owner["headers"])
    first = await _certificate(org_db, owner, domain=domain, identifiers=["api.bind.example.com"])
    second = await _certificate(org_db, owner, domain=domain, identifiers=["*.bind.example.com"])

    assert (await _bind(client, owner, route, first)).status_code == 200
    conflict = await _bind(client, owner, route, second)
    assert conflict.status_code == 409, conflict.text
    assert conflict.json()["error"]["code"] == "ROUTE_CERTIFICATE_CONFLICT"
    assert (await _route_detail(client, owner, route))["certificate_id"] == first["id"]

    assert (await _bind(client, owner, route, first)).status_code == 200  # idempotent
    assert (await _unbind(client, owner, route)).status_code == 204
    assert (await _bind(client, owner, route, second)).status_code == 200


async def test_concurrent_conflicting_binds_serialize(client, owner, org_db):
    route, _node, domain = await _setup(client, owner, hostname="api.bind.example.com")
    await client.post(f"{API}/routes/{route['id']}/enable", headers=owner["headers"])
    first = await _certificate(org_db, owner, domain=domain, identifiers=["api.bind.example.com"])
    second = await _certificate(org_db, owner, domain=domain, identifiers=["*.bind.example.com"])

    responses = await asyncio.gather(
        _bind(client, owner, route, first),
        _bind(client, owner, route, second),
    )
    assert sorted(response.status_code for response in responses) == [200, 409]
    winner = next(response for response in responses if response.status_code == 200).json()
    detail = await _route_detail(client, owner, route)
    assert detail["certificate_id"] == winner["certificate_id"]
    assert detail["certificate_id"] in (first["id"], second["id"])
