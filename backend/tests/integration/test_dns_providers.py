"""Phase 5.2.2 — DNS credentials through the real HTTP surface and the real database.

A DNS credential is the first *customer secret* this platform holds that is never
delivered anywhere: the control plane uses it to publish challenge records and the
value itself must never leave the platform again. The claims below are the ones
that make that a property of the code rather than a promise in a docstring:

* **Write-only, by construction.** ``POST`` accepts a token and every read —
  single, list, verify — answers with the approved metadata field set and nothing
  else. The credential is asserted absent from each response body, from the audit
  row and from the event payload, while a service-level read-back proves it really
  was stored (the positive control: a platform that dropped the value would also
  never leak it).
* **The allowlist is enforced before any provider call.** An empty allowlist
  authorizes nothing, a wildcard entry names the zone it is under, and an
  allowlisted zone the token cannot see is a recorded warning rather than a
  failure — because the operator may be about to grant it.
* **Verification is a recorded result, not a gate.** A token that fails
  verification is still stored, with its bounded reason on the row, and re-running
  verification is what changes the verdict.
* **A reference is a reference.** The certificate override is stored as an id, a
  credential a certificate still names cannot be deleted, and a foreign or random
  id is the same 404 on every route.

The Cloudflare API is replaced by a fake at the provider seam — the one thing
outside this process a credential touches in this slice — so no test can reach the
network. Nothing here writes to a customer's DNS: the record methods are 5.3's.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from typing import Any

import pytest
from app.core.tenancy import apply_scope_to_session, org_scope
from app.models import AuditLog, DnsProvider, SystemEvent
from app.models.enums import DomainStatus
from app.providers.dns import CredentialCheck
from app.services import dns_provider_service, dns_verifier
from app.services.dns_verifier import STATUS_OK, TxtObservation
from sqlalchemy import select, text

from .helpers import API, assert_error_code, bearer, login_account, unique_email

pytestmark = pytest.mark.integration

NS_SET = ("ns1.example.net", "ns2.example.net")

#: The token the mocked authoritative DNS serves for domain verification.
DNS: dict[str, object] = {"token": "", "nameservers": NS_SET}

#: The secrets every test pastes. Distinctive on purpose: the assertions below look
#: for them anywhere in a body, an audit row or an event payload.
TOKEN = "cf-token-that-must-never-be-echoed"
ROTATED_TOKEN = "cf-token-after-rotation"

#: The complete ``DnsProviderOut`` field set — the allowlist the read model must be.
PROVIDER_FIELDS = {
    "id",
    "created_at",
    "updated_at",
    "name",
    "kind",
    "scopes",
    "zone_allowlist",
    "credential_fingerprint",
    "deke_id",
    "verified_at",
    "verify_error",
    "auto_cleanup",
    "last_used_at",
}


def _fake_observe(name: str) -> TxtObservation:
    return TxtObservation(
        STATUS_OK,
        values=(str(DNS["token"]),),
        nameservers=tuple(DNS["nameservers"]),  # type: ignore[arg-type]
    )


@pytest.fixture(autouse=True)
def _dns_stub(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Stand in for authoritative DNS in every test in this module."""
    DNS["token"] = ""
    DNS["nameservers"] = NS_SET
    monkeypatch.setattr(dns_verifier, "observe", _fake_observe)
    yield


class _FakeCloudflare:
    """The one thing the credential seam needs: a verdict and the zones it can see."""

    name = "cloudflare"
    #: Annotated variadically so the fake satisfies the protocol the same way the
    #: real provider does.
    required_fields: tuple[str, ...] = ("api_token",)

    def __init__(
        self,
        *,
        ok: bool = True,
        zones: tuple[str, ...] = ("example.com",),
        error: str = "",
    ) -> None:
        self.ok = ok
        self.zones = list(zones)
        self.error = error
        #: What the platform was actually handed, so a test can prove the stored
        #: plaintext round-trips without the API ever exposing it.
        self.calls: list[dict[str, str]] = []

    async def verify_creds(self, credentials: dict[str, str]) -> CredentialCheck:
        self.calls.append(dict(credentials))
        if not self.ok:
            return CredentialCheck(ok=False, error=self.error)
        return CredentialCheck(
            ok=True,
            scopes={"zone_names": list(self.zones), "token_status": "active"},
        )


@pytest.fixture
def cloudflare(monkeypatch: pytest.MonkeyPatch) -> _FakeCloudflare:
    """Replace the provider seam for one test, and make it reachable to tune."""
    fake = _FakeCloudflare()
    monkeypatch.setattr(dns_provider_service, "provider_for", lambda kind: fake)
    return fake


@pytest.fixture(autouse=True)
def _never_reach_the_network(cloudflare: _FakeCloudflare) -> _FakeCloudflare:
    """Every test in this module gets the fake, whether or not it inspects it."""
    return cloudflare


@asynccontextmanager
async def _scoped(session, org_id: uuid.UUID) -> AsyncIterator[Any]:
    """One session inside the organization's scope, as a request runs.

    Service calls that reach key material (the credential read-back, the envelope)
    run inside a scope exactly like the request path does; this is that scope, made
    explicit.
    """
    with org_scope(org_id):
        await apply_scope_to_session(session)
        yield session


def _org_id(owner: dict) -> uuid.UUID:
    return uuid.UUID(owner["active_organization_id"])


# --- helpers ------------------------------------------------------------------


async def _create(client, owner, name: str, *, zones=("example.com",), token=TOKEN, **extra):
    return await client.post(
        f"{API}/dns-providers",
        headers=owner["headers"],
        json={
            "name": name,
            "credentials": {"api_token": token},
            "zone_allowlist": list(zones),
            **extra,
        },
    )


async def _created(client, owner, name: str, **kwargs) -> dict:
    response = await _create(client, owner, name, **kwargs)
    assert response.status_code == 201, response.text
    return response.json()


async def _create_domain(client, owner, name: str, *, verified: bool = True, **extra) -> dict:
    """A domain in the caller's organization, verified through the real task."""
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


async def _audits(db, action: str) -> list[AuditLog]:
    return list((await db.execute(select(AuditLog).where(AuditLog.action == action))).scalars())


async def _events(db, event_type: str) -> list[SystemEvent]:
    return list(
        (await db.execute(select(SystemEvent).where(SystemEvent.type == event_type))).scalars()
    )


async def _row(db, provider_id: str) -> DnsProvider:
    """The row as it is stored, not as this session last saw it.

    The API writes through its own session, and the test session's identity map
    would happily hand back the object it loaded a moment ago; ``populate_existing``
    forces the read, so an assertion about what a PATCH persisted is about the
    database rather than about this process's memory.
    """
    row = await db.get(DnsProvider, uuid.UUID(provider_id), populate_existing=True)
    assert row is not None
    return row


# --- 1. write-only, by construction -------------------------------------------


async def test_a_credential_is_stored_verified_and_never_read_back(client, owner, db) -> None:
    """The whole read surface is metadata, and the value is really there underneath.

    Both halves matter. Without the allowlist assertion a serializer that dumped the
    row would pass; without the read-back a platform that silently discarded the
    token would pass too, and only fail at issuance.
    """
    body = await _created(client, owner, "cloudflare production")
    assert set(body) == PROVIDER_FIELDS
    assert TOKEN not in json.dumps(body)
    assert body["kind"] == "cloudflare"
    assert body["credential_fingerprint"] and len(body["credential_fingerprint"]) == 64
    assert body["deke_id"] >= 1
    assert body["verified_at"] is not None
    assert body["verify_error"] == ""
    assert body["auto_cleanup"] is True
    assert body["scopes"]["token_status"] == "active"

    # List and detail are the same serializer, so neither exposes more than the
    # other: a page cannot be the read path that leaks.
    listing = await client.get(f"{API}/dns-providers", headers=owner["headers"])
    assert listing.status_code == 200, listing.text
    page = listing.json()
    assert page["total"] >= 1
    assert all(set(row) == PROVIDER_FIELDS for row in page["items"])
    assert TOKEN not in json.dumps(page)

    detail = await client.get(f"{API}/dns-providers/{body['id']}", headers=owner["headers"])
    assert detail.status_code == 200, detail.text
    assert set(detail.json()) == PROVIDER_FIELDS
    assert TOKEN not in json.dumps(detail.json())

    # The row carries ciphertext, not the token — and the positive control: the
    # platform can still use what it stored, under the row's own DEK generation,
    # and what comes back is the token it was given. Only the issuance path may
    # call this.
    async with _scoped(db, _org_id(owner)) as scoped:
        row = await _row(scoped, body["id"])
        assert TOKEN not in row.credentials_ciphertext
        assert row.credentials_ciphertext != TOKEN
        assert await dns_provider_service.credentials_for_use(scoped, row) == {"api_token": TOKEN}

    # Re-pasting the same token is recognisable as "unchanged"; a new one is not.
    same = await _created(client, owner, "cloudflare production copy")
    assert same["credential_fingerprint"] == body["credential_fingerprint"]
    other = await _created(client, owner, "cloudflare staging", token=ROTATED_TOKEN)
    assert other["credential_fingerprint"] != body["credential_fingerprint"]

    # Audited and announced — and neither carries the credential.
    async with _scoped(db, _org_id(owner)) as scoped:
        entries = await _audits(scoped, "dns_provider.created")
        assert len(entries) == 3
        by_name = {entry.metadata_["name"]: entry for entry in entries}
        assert set(by_name) == {
            "cloudflare production",
            "cloudflare production copy",
            "cloudflare staging",
        }
        for entry in entries:
            assert entry.resource_type == "dns_provider"
            assert TOKEN not in json.dumps(entry.metadata_)
            assert ROTATED_TOKEN not in json.dumps(entry.metadata_)
        # The field is present and its value is redacted: "credential" matches the
        # platform's global sensitive-key policy (core/logging.redact_mapping), so
        # the audit row states that a credential was accepted and says nothing about
        # which one — while the fingerprint itself stays available on the read model.
        assert {entry.metadata_["credential_fingerprint"] for entry in entries} == {"[REDACTED]"}
        assert body["credential_fingerprint"] != other["credential_fingerprint"]
        assert by_name["cloudflare production"].metadata_["zones"] == ["example.com"]
        assert by_name["cloudflare production"].metadata_["verified"] is True

        created_events = await _events(scoped, "DNS_PROVIDER_CREATED")
        assert len(created_events) == 3
        assert TOKEN not in json.dumps([event.data for event in created_events])
        assert {event.data["name"] for event in created_events} == set(by_name)


async def test_the_zone_allowlist_is_canonical_and_a_wildcard_names_its_zone(client, owner) -> None:
    """The allowlist bounds *zones*, so a wildcard entry means the zone it is under.

    An operator copying ``*.example.com`` out of a certificate request should not
    have the entry rejected as malformed, and re-pasting ``Example.COM.`` must not
    become a second entry that reads as a different zone.
    """
    body = await _created(
        client,
        owner,
        "canonical",
        zones=["Example.COM.", "*.sub.example.com", "example.com", "sub.example.com"],
    )
    assert body["zone_allowlist"] == ["example.com", "sub.example.com"]


async def test_a_zone_the_token_cannot_see_is_a_warning_not_a_failure(client, owner) -> None:
    """A recorded observation, because the operator may be about to grant the zone."""
    body = await _created(client, owner, "warning", zones=["example.com", "not-mine.example.net"])
    assert body["verified_at"] is not None
    assert body["verify_error"] == ""
    assert any("not-mine.example.net" in warning for warning in body["scopes"]["warnings"])


async def test_an_empty_allowlist_authorizes_nothing(client, owner, db) -> None:
    """The fail-closed reading of an empty list, at the check the issuance path uses."""
    body = await _created(client, owner, "no-zones", zones=[])
    assert body["zone_allowlist"] == []

    async with _scoped(db, _org_id(owner)) as scoped:
        row = await _row(scoped, body["id"])
        assert dns_provider_service.zone_allows([], "example.com") is False
        with pytest.raises(Exception) as raised:
            dns_provider_service.require_zone_allowed(row, "example.com")
        assert getattr(raised.value, "code", None) == "DNS_ZONE_NOT_ALLOWED"

    # Once the zone is allowlisted the same predicate admits both the challenge
    # record and the identifier it serves — a zone boundary, not a record match —
    # and still refuses a lookalike domain that merely ends in the same text.
    patched = await client.patch(
        f"{API}/dns-providers/{body['id']}",
        headers=owner["headers"],
        json={"zone_allowlist": ["example.com"]},
    )
    assert patched.status_code == 200, patched.text
    async with _scoped(db, _org_id(owner)) as scoped:
        row = await _row(scoped, body["id"])
        assert dns_provider_service.zone_allows(row.zone_allowlist, "example.com") is True
        assert (
            dns_provider_service.zone_allows(row.zone_allowlist, "_acme-challenge.www.example.com")
            is True
        )
        assert dns_provider_service.zone_allows(row.zone_allowlist, "notexample.com") is False
        assert (
            dns_provider_service.zone_allows(row.zone_allowlist, "example.com.evil.example.net")
            is False
        )
        # The challenge owner name carries a service label, and it is the name the
        # publish and the cleanup actually use — refusing it here would refuse the
        # write the allowlist exists to authorize. A lookalike outside the zone, and
        # an underscore that is not a leading service label, stay refused.
        assert (
            dns_provider_service.zone_allows(row.zone_allowlist, "_ACME-Challenge.Example.COM")
            is True
        )
        assert (
            dns_provider_service.zone_allows(row.zone_allowlist, "_acme-challenge.other.test")
            is False
        )
        assert (
            dns_provider_service.zone_allows(row.zone_allowlist, "under_score.example.com") is False
        )


async def test_a_malformed_or_unsupported_credential_never_reaches_the_database(
    client, owner, db
) -> None:
    """Malformed input is the caller's mistake, and it stops before anything is stored."""
    blank = await _create(client, owner, "blank", token="   ")
    assert blank.status_code == 422, blank.text
    assert_error_code(blank.json(), "DNS_CREDENTIAL_INCOMPLETE")

    empty = await client.post(
        f"{API}/dns-providers",
        headers=owner["headers"],
        json={"name": "empty", "credentials": {}, "zone_allowlist": ["example.com"]},
    )
    assert empty.status_code == 422, empty.text
    assert_error_code(
        empty.json(),
        "VALIDATION_ERROR",
        exact_keys={"code", "message", "request_id", "details"},
    )

    # A kind the control plane cannot call is a named client error, never a row
    # naming a provider the issuance path would then fail to reach.
    unsupported = await client.post(
        f"{API}/dns-providers",
        headers=owner["headers"],
        json={
            "name": "route53",
            "kind": "route53",
            "credentials": {"api_token": TOKEN},
            "zone_allowlist": ["example.com"],
        },
    )
    assert unsupported.status_code == 422, unsupported.text
    assert_error_code(unsupported.json(), "DNS_PROVIDER_KIND_UNSUPPORTED")

    bad_zone = await _create(client, owner, "bad-zone", zones=["not a zone"])
    assert bad_zone.status_code == 422, bad_zone.text
    assert_error_code(bad_zone.json(), "DNS_ZONE_INVALID")

    async with _scoped(db, _org_id(owner)) as scoped:
        rows = list(
            (
                await scoped.execute(
                    select(DnsProvider).where(
                        DnsProvider.name.in_(["blank", "empty", "route53", "bad-zone"])
                    )
                )
            ).scalars()
        )
        assert rows == []


async def test_a_failing_verification_is_recorded_and_the_verdict_can_change(
    client, owner, db, cloudflare
) -> None:
    """A broken token is stored with its reason — the fix is to read it, not to resubmit."""
    cloudflare.ok = False
    cloudflare.error = "Cloudflare returned HTTP 401 (errors: 1000, 6003)"
    body = await _created(client, owner, "expired", zones=["example.com"])
    assert body["verified_at"] is None
    assert body["verify_error"] == "Cloudflare returned HTTP 401 (errors: 1000, 6003)"

    # Verification on demand, still failing: the attempt is recorded as an event so
    # a credential that cannot be used is visible without re-pasting the token.
    failed = await client.post(f"{API}/dns-providers/{body['id']}/verify", headers=owner["headers"])
    assert failed.status_code == 200, failed.text
    assert failed.json()["verified_at"] is None
    assert failed.json()["verify_error"] == "Cloudflare returned HTTP 401 (errors: 1000, 6003)"

    async with _scoped(db, _org_id(owner)) as scoped:
        events = await _events(scoped, "DNS_PROVIDER_VERIFICATION_FAILED")
        assert len(events) == 1
        assert events[0].level == "WARNING"
        assert TOKEN not in json.dumps(events[0].data)
        assert len(await _audits(scoped, "dns_provider.verification_failed")) == 1

    # Fixing the token is a rotation, and a rotation has not been verified yet:
    # keeping the previous verdict would claim a check the new value never got.
    rotated = await client.patch(
        f"{API}/dns-providers/{body['id']}",
        headers=owner["headers"],
        json={"credentials": {"api_token": ROTATED_TOKEN}},
    )
    assert rotated.status_code == 200, rotated.text
    assert rotated.json()["verified_at"] is None
    assert rotated.json()["verify_error"] == ""
    assert rotated.json()["credential_fingerprint"] != body["credential_fingerprint"]

    cloudflare.ok = True
    verified = await client.post(
        f"{API}/dns-providers/{body['id']}/verify", headers=owner["headers"]
    )
    assert verified.status_code == 200, verified.text
    assert verified.json()["verified_at"] is not None
    assert verified.json()["verify_error"] == ""
    assert verified.json()["scopes"]["token_status"] == "active"
    assert cloudflare.calls[-1] == {"api_token": ROTATED_TOKEN}
    assert TOKEN not in json.dumps(verified.json())

    async with _scoped(db, _org_id(owner)) as scoped:
        # The failing attempt is still on the trail, next to the successful one.
        assert len(await _audits(scoped, "dns_provider.verification_failed")) == 1
        assert len(await _audits(scoped, "dns_provider.verified")) == 1
        assert len(await _events(scoped, "DNS_PROVIDER_VERIFIED")) == 1
        updated = (await _audits(scoped, "dns_provider.updated"))[0]
        # Which fields changed — never a field's value.
        assert updated.metadata_["fields"] == ["credentials"]
        assert ROTATED_TOKEN not in json.dumps(updated.metadata_)


async def test_a_partial_update_cannot_erase_a_field_because_null_is_not_a_value(
    client, owner, db
) -> None:
    body = await _created(client, owner, "partial", zones=["example.com"], auto_cleanup=False)
    patched = await client.patch(
        f"{API}/dns-providers/{body['id']}",
        headers=owner["headers"],
        json={"credentials": None, "auto_cleanup": None},
    )
    assert patched.status_code == 200, patched.text
    assert patched.json()["credential_fingerprint"] == body["credential_fingerprint"]
    assert patched.json()["auto_cleanup"] is False
    assert patched.json()["zone_allowlist"] == ["example.com"]
    assert patched.json()["verified_at"] is not None

    async with _scoped(db, _org_id(owner)) as scoped:
        updated = (await _audits(scoped, "dns_provider.updated"))[0]
        assert updated.metadata_["fields"] == []


# --- 2. names, references and deletion ----------------------------------------


async def test_a_name_is_unique_per_organization_and_free_in_another(client, owner, second_org):
    await _created(client, owner, "shared name")
    duplicate = await _create(client, owner, "shared name")
    assert duplicate.status_code == 409, duplicate.text
    assert_error_code(duplicate.json(), "DNS_PROVIDER_NAME_TAKEN")

    # The constraint is per tenant, not global: another organization may use the
    # same operator-facing label.
    elsewhere = await client.post(
        f"{API}/dns-providers",
        headers=second_org["headers"],
        json={
            "name": "shared name",
            "credentials": {"api_token": TOKEN},
            "zone_allowlist": ["example.com"],
        },
    )
    assert elsewhere.status_code == 201, elsewhere.text


async def test_a_credential_a_certificate_still_names_cannot_be_deleted(client, owner, db) -> None:
    """The reference is an id on the certificate, and the delete is refused while it stands.

    A silent fallback to the Domain's credential would change which token signs for
    the certificate at its next renewal — the failure mode that keeps working.
    """
    provider = await _created(client, owner, "bound")
    domain = await _create_domain(client, owner, "bound.example.com")
    certificate = await client.post(
        f"{API}/certificates",
        headers=owner["headers"],
        json={
            "domain_id": domain["id"],
            "identifiers": [domain["name"]],
            "dns_provider_id": provider["id"],
        },
    )
    assert certificate.status_code == 201, certificate.text
    created = certificate.json()
    assert created["dns_provider_id"] == provider["id"]

    refused = await client.delete(f"{API}/dns-providers/{provider['id']}", headers=owner["headers"])
    assert refused.status_code == 409, refused.text
    error = assert_error_code(refused.json(), "DNS_PROVIDER_IN_USE")
    assert "bound.example.com" in error["message"]

    # The database would refuse too — the FK is RESTRICT — and the named 409 exists
    # so the operator is told which certificate to rebind rather than reading a
    # driver error.
    async with _scoped(db, _org_id(owner)) as scoped:
        provider_row = await _row(scoped, provider["id"])
        with pytest.raises(Exception) as raised:
            await scoped.delete(provider_row)
            await scoped.flush()
        assert "fk_certificates_dns_provider_id" in str(raised.value)
        await scoped.rollback()

    # Deleting the request frees the credential, because nothing names it any more.
    deleted = await client.delete(f"{API}/certificates/{created['id']}", headers=owner["headers"])
    assert deleted.status_code == 204, deleted.text
    freed = await client.delete(f"{API}/dns-providers/{provider['id']}", headers=owner["headers"])
    assert freed.status_code == 204, freed.text
    gone = await client.get(f"{API}/dns-providers/{provider['id']}", headers=owner["headers"])
    assert gone.status_code == 404
    assert_error_code(gone.json(), "DNS_PROVIDER_NOT_FOUND")

    async with _scoped(db, _org_id(owner)) as scoped:
        assert await _audits(scoped, "dns_provider.deleted")
        assert len(await _events(scoped, "DNS_PROVIDER_DELETED")) == 1


async def test_the_certificate_override_can_be_cleared_but_not_pointed_at_a_stranger(
    client, owner, second_org
) -> None:
    """``null`` clears the override; an id that does not resolve is a 404, not a store."""
    provider = await _created(client, owner, "overridable")
    domain = await _create_domain(client, owner, "override.example.com")
    created = (
        await client.post(
            f"{API}/certificates",
            headers=owner["headers"],
            json={
                "domain_id": domain["id"],
                "identifiers": [domain["name"]],
                "dns_provider_id": provider["id"],
            },
        )
    ).json()

    cleared = await client.patch(
        f"{API}/certificates/{created['id']}",
        headers=owner["headers"],
        json={"dns_provider_id": None},
    )
    assert cleared.status_code == 200, cleared.text
    assert cleared.json()["dns_provider_id"] is None

    # A credential in another organization is unreachable by id, and the response
    # is the one a random uuid gets: the route is not an existence oracle.
    foreign = await client.post(
        f"{API}/dns-providers",
        headers=second_org["headers"],
        json={
            "name": "foreign",
            "credentials": {"api_token": TOKEN},
            "zone_allowlist": ["example.com"],
        },
    )
    assert foreign.status_code == 201, foreign.text
    for candidate in (foreign.json()["id"], str(uuid.uuid4())):
        response = await client.patch(
            f"{API}/certificates/{created['id']}",
            headers=owner["headers"],
            json={"dns_provider_id": candidate},
        )
        assert response.status_code == 404, response.text
        assert_error_code(response.json(), "DNS_PROVIDER_NOT_FOUND")


# --- 3. tenancy and authorization ---------------------------------------------


async def test_every_route_is_tenant_scoped_and_a_foreign_id_is_a_random_id(
    client, owner, second_org
) -> None:
    provider = await _created(client, owner, "private")
    foreign_headers = second_org["headers"]

    for path, method, body in (
        (f"{API}/dns-providers/{provider['id']}", "get", None),
        (f"{API}/dns-providers/{provider['id']}", "patch", {"name": "stolen"}),
        (f"{API}/dns-providers/{provider['id']}/verify", "post", None),
        (f"{API}/dns-providers/{provider['id']}", "delete", None),
        (f"{API}/dns-providers/{uuid.uuid4()}", "get", None),
        (f"{API}/dns-providers/{uuid.uuid4()}", "patch", {"name": "stolen"}),
        (f"{API}/dns-providers/{uuid.uuid4()}", "delete", None),
    ):
        response = await getattr(client, method)(
            path, headers=foreign_headers, **({"json": body} if body is not None else {})
        )
        assert response.status_code == 404, (path, method, response.text)
        assert_error_code(response.json(), "DNS_PROVIDER_NOT_FOUND")

    listing = await client.get(f"{API}/dns-providers", headers=second_org["headers"])
    assert listing.status_code == 200, listing.text
    assert provider["id"] not in {row["id"] for row in listing.json()["items"]}


async def test_read_alone_does_not_authorize_management(client, owner) -> None:
    """``certificate.read`` covers reads; every mutation rides ``certificate.manage``."""
    provider = await _created(client, owner, "role-gated")
    mutations = (
        ("post", f"{API}/dns-providers", {"name": "x", "credentials": {"api_token": TOKEN}}),
        ("patch", f"{API}/dns-providers/{provider['id']}", {"name": "renamed"}),
        ("post", f"{API}/dns-providers/{provider['id']}/verify", None),
        ("delete", f"{API}/dns-providers/{provider['id']}", None),
    )

    for role_name in ("Viewer", "Developer"):
        member = await _member_with_role(client, owner, role_name)
        assert (
            await client.get(f"{API}/dns-providers", headers=member["headers"])
        ).status_code == 200, role_name
        assert (
            await client.get(f"{API}/dns-providers/{provider['id']}", headers=member["headers"])
        ).status_code == 200, role_name
        for method, path, body in mutations:
            response = await getattr(client, method)(
                path,
                headers=member["headers"],
                **({"json": body} if body is not None else {}),
            )
            assert response.status_code == 403, (role_name, method, response.text)
            assert_error_code(response.json(), "PERMISSION_DENIED")

    operator = await _member_with_role(client, owner, "Operator")
    renamed = await client.patch(
        f"{API}/dns-providers/{provider['id']}",
        headers=operator["headers"],
        json={"name": "renamed by operator"},
    )
    assert renamed.status_code == 200, renamed.text
    assert renamed.json()["name"] == "renamed by operator"

    anonymous = await client.get(f"{API}/dns-providers/{provider['id']}")
    assert anonymous.status_code == 401
    assert_error_code(anonymous.json(), "UNAUTHORIZED")


async def test_a_credential_cannot_be_used_under_a_dek_it_was_not_written_with(
    client, owner, db
) -> None:
    """A DEK-generation mismatch is a named failure, never a guess at another key.

    The row records the generation that encrypted it, so a rotation that has not
    reached this row yet is visible as exactly that — the fix is to finish the
    rotation, not to try the current key and hope it decrypts.
    """
    provider = await _created(client, owner, "lagging")
    async with _scoped(db, _org_id(owner)) as scoped:
        await scoped.execute(
            text("UPDATE dns_providers SET deke_id = 2 WHERE id = :id"),
            {"id": provider["id"]},
        )
        await scoped.commit()

        row = await _row(scoped, provider["id"])
        with pytest.raises(dns_provider_service.DnsCredentialUnavailable) as raised:
            await dns_provider_service.credentials_for_use(scoped, row)
        assert raised.value.code == "DNS_CREDENTIAL_ROTATION_PENDING"
        assert "DEK rotation" in raised.value.message


# --- 4. the read model is an allowlist, not a dump ----------------------------


async def test_no_response_carries_the_ciphertext_column_or_its_contents(client, owner) -> None:
    """A response is built from an explicit field map, so a new column cannot leak.

    The assertion is structural rather than value-based: the column's name and the
    credential it holds must be absent from every response this subsystem produces.
    """
    body = await _created(client, owner, "structural")
    responses = [
        body,
        (await client.get(f"{API}/dns-providers", headers=owner["headers"])).json(),
        (await client.get(f"{API}/dns-providers/{body['id']}", headers=owner["headers"])).json(),
        (
            await client.post(f"{API}/dns-providers/{body['id']}/verify", headers=owner["headers"])
        ).json(),
    ]
    dumped = json.dumps(responses)
    assert "credentials_ciphertext" not in dumped
    assert "api_token" not in dumped
    assert TOKEN not in dumped
