"""Phase 5.2.2 — the per-organization ACME account and the DEK that protects it.

The account is the tenant's identity at the certificate authority: it holds the key
that will sign their issuance requests (5.3), so the claims here are about custody
rather than about ACME. Three of them are load-bearing:

* **The key is write-only.** ``summary()`` is an explicit allowlist and the row's
  ciphertext is what is stored; the positive control is that the key can still be
  read back by the one internal function that is allowed to, and that what comes
  back is the key the row was created with.
* **The payload is bound to its row.** A ciphertext presented under another
  purpose, another record, another DEK generation or another organization is
  refused, and a generation the row has moved past is a *named* rotation-pending
  failure rather than a guess at the current key.
* **One envelope per organization, but a purpose per payload.** This is the claim
  the module exists to pin: the organization DEK is unwrapped once per operation
  and every subsystem encrypts under that same DEK, so storing a DNS credential
  must not cost the organization its ability to unwrap its own DEK for ACME — and
  must not cost it the *separation* either (a credential's ciphertext is still
  unreadable as an account key). Getting one of those without the other is exactly
  how a single-envelope design goes wrong, so both orders are exercised below.

Registration itself is 5.3; ``record_registration`` is the seam it will call, and
nothing here contacts a certificate authority.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from typing import Any

import pytest
from app.core.errors import Conflict, UnprocessableEntity
from app.core.tenancy import TenancyScopeError, apply_scope_to_session, org_scope
from app.models import AcmeAccount, AuditLog, DnsProvider, OrganizationDekEnvelope, SystemEvent
from app.models.enums import AcmeDirectory, CertificateKeyAlgorithm
from app.providers.dns import CredentialCheck
from app.services import dns_provider_service
from app.services.acme_account_service import (
    AcmeAccountKeyUnavailable,
    account_for,
    account_key,
    account_key_fingerprint,
    find_account,
    record_registration,
    resolve_directory,
    summary,
)
from app.services.dek_envelope import FIRST_GENERATION, org_dek_context
from app.services.payload_crypto import (
    PURPOSE_ACME_ACCOUNT_KEY,
    PURPOSE_DNS_CREDENTIALS,
    PayloadContext,
    PayloadContextMismatch,
    decrypt_str,
)
from cryptography.hazmat.primitives import serialization
from sqlalchemy import func, select, text

from .helpers import API

pytestmark = pytest.mark.integration

STAGING = AcmeDirectory.STAGING
PRODUCTION = AcmeDirectory.PRODUCTION

#: The credential the DNS-provider leg pastes. Distinctive on purpose: the
#: assertions below look for it anywhere a response, an audit row or an event
#: payload could carry it.
DNS_TOKEN = "cf-token-that-must-never-be-echoed"

#: The complete ``summary()`` field set — the allowlist every log line, audit entry
#: and event payload is built from. ``key_ciphertext`` is not in it, and neither is
#: anything that decrypts to the key.
SUMMARY_FIELDS = {
    "id",
    "directory_url",
    "directory",
    "key_fingerprint",
    "key_algorithm",
    "deke_id",
    "registered",
    "last_used_at",
}

#: The PEM header of the account key. If this string appears anywhere outside the
#: decrypted key, something has stored or echoed the key in the clear.
PEM_MARKER = "BEGIN PRIVATE KEY"


class _FakeCloudflare:
    """The credential seam: a verdict plus the zones the token can see."""

    name = "cloudflare"
    required_fields: tuple[str, ...] = ("api_token",)

    def __init__(self, *, zones: tuple[str, ...] = ("example.com",)) -> None:
        self.zones = list(zones)
        #: What the platform was handed, so the read-back can be compared against
        #: the value the operator actually pasted.
        self.calls: list[dict[str, str]] = []

    async def verify_creds(self, credentials: dict[str, str]) -> CredentialCheck:
        self.calls.append(dict(credentials))
        return CredentialCheck(ok=True, scopes={"zone_names": list(self.zones)})


@pytest.fixture(autouse=True)
def cloudflare(monkeypatch: pytest.MonkeyPatch) -> Iterator[_FakeCloudflare]:
    """Every test in this module gets the fake, and no test can reach the network."""
    fake = _FakeCloudflare()
    monkeypatch.setattr(dns_provider_service, "provider_for", lambda kind: fake)
    yield fake


@asynccontextmanager
async def _scoped(session, org_id: uuid.UUID) -> AsyncIterator[Any]:
    """One session inside an organization's scope, the way a request runs.

    Anything that reaches key material — the envelope, the payload decrypt — only
    runs inside a scope, so this is that scope made explicit.
    """
    with org_scope(org_id):
        await apply_scope_to_session(session)
        yield session


def _org_id(owner: dict) -> uuid.UUID:
    return uuid.UUID(owner["active_organization_id"])


async def _audits(db, action: str) -> list[AuditLog]:
    return list((await db.execute(select(AuditLog).where(AuditLog.action == action))).scalars())


async def _events(db, event_type: str) -> list[SystemEvent]:
    return list(
        (await db.execute(select(SystemEvent).where(SystemEvent.type == event_type))).scalars()
    )


async def _account_count(db) -> int:
    return int(await db.scalar(select(func.count()).select_from(AcmeAccount)) or 0)


async def _stored(db, account_id: uuid.UUID) -> AcmeAccount:
    """The row as it is stored, not as this session last saw it."""
    row = await db.get(AcmeAccount, account_id, populate_existing=True)
    assert row is not None
    return row


async def _store_credential(client, owner, name: str = "cloudflare production") -> dict:
    """One DNS credential through the real API — the other purpose under this DEK."""
    response = await client.post(
        f"{API}/dns-providers",
        headers=owner["headers"],
        json={
            "name": name,
            "credentials": {"api_token": DNS_TOKEN},
            "zone_allowlist": ["example.com"],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


# --- 1. the key is stored, and write-only -------------------------------------


async def test_the_key_is_generated_stored_and_never_reaches_a_read_model(owner, db) -> None:
    """Metadata out, key in — and the key really is there underneath.

    Both halves matter: without the allowlist assertion a ``summary()`` that dumped
    the row would pass, and without the read-back a control plane that silently
    stored garbage would pass too, and only fail when it first had to sign.
    """
    org_id = _org_id(owner)
    async with _scoped(db, org_id) as scoped:
        account = await account_for(scoped, None, org_id=org_id, directory=STAGING)

        assert account.directory_url == STAGING.url()
        assert account.directory is STAGING
        assert account.account_url is None
        assert account.key_algorithm == CertificateKeyAlgorithm.ECDSA_P256.value
        assert account.deke_id == FIRST_GENERATION
        assert len(account.key_fingerprint) == 64

        row = await _stored(scoped, account.id)
        # The column holds a ciphertext: no PEM, and not the key's own fingerprint
        # material either. (The stored value is a payload envelope; the header names
        # the context, which is the point of the binding.)
        assert PEM_MARKER not in row.key_ciphertext
        assert row.key_ciphertext.startswith("nxp1:")

        # The positive control: the one internal reader gets the key back, it is a
        # usable P-256 private key, and it is the same key the row is labelled with.
        pem = await account_key(scoped, row)
        assert pem.startswith(f"-----{PEM_MARKER}-----")
        private = serialization.load_pem_private_key(pem.encode(), password=None)
        assert private.curve.name == "secp256r1"
        assert account_key_fingerprint(pem) == row.key_fingerprint

        # A log line, an audit entry or an event payload is built from this, and it
        # is an explicit field set rather than the object.
        line = summary(row)
        assert set(line) == SUMMARY_FIELDS
        assert line["registered"] is False
        assert line["directory"] == "staging"
        assert json.dumps(line).count(PEM_MARKER) == 0
        assert DNS_TOKEN not in json.dumps(line)

    # The fingerprint is a handle over the *public* half, so two accounts generated
    # independently never share one.
    async with _scoped(db, org_id) as scoped:
        other = await account_for(scoped, None, org_id=org_id, directory=PRODUCTION)
        assert other.key_fingerprint != account.key_fingerprint
        assert other.directory is PRODUCTION


async def test_asking_twice_converges_on_one_account(client, owner, db) -> None:
    """Staging and production are two accounts; a repeat is not a second one.

    Issuance retries, so ``account_for`` has to be safe to call again — and the
    (organization, directory) identity has to mean a second call cannot register a
    second account at the CA.
    """
    org_id = _org_id(owner)
    async with _scoped(db, org_id) as scoped:
        first = await account_for(scoped, None, org_id=org_id, directory=STAGING)
        first_id = first.id
        again = await account_for(scoped, None, org_id=org_id, directory=STAGING)
        assert again.id == first_id
        assert await _account_count(scoped) == 1

        assert await find_account(scoped, org_id=org_id, directory=PRODUCTION) is None
        production = await account_for(scoped, None, org_id=org_id, directory=PRODUCTION)
        assert production.id != first_id
        assert await _account_count(scoped) == 2

        # The directory round-trips through the row, so a staging-issued certificate
        # can be recognized as staging from its own record rather than from config.
        assert (await _stored(scoped, first_id)).directory is STAGING
        assert (await _stored(scoped, production.id)).directory is PRODUCTION


async def test_the_account_is_audited_and_announced_without_its_key(owner, db) -> None:
    org_id = _org_id(owner)
    async with _scoped(db, org_id) as scoped:
        account = await account_for(scoped, None, org_id=org_id, directory=STAGING)

        entries = await _audits(scoped, "acme_account.created")
        assert len(entries) == 1
        assert entries[0].resource_type == "acme_account"
        # The fingerprint, never the key: an audit entry records that a key exists
        # and which one it is, not what it is.
        assert entries[0].metadata_["key_fingerprint"] == account.key_fingerprint
        assert entries[0].metadata_["directory"] == "staging"
        assert PEM_MARKER not in json.dumps(entries[0].metadata_)

        events = await _events(scoped, "ACME_ACCOUNT_CREATED")
        assert len(events) == 1
        assert events[0].data == {
            "directory": "staging",
            "directory_url": STAGING.url(),
        }
        assert PEM_MARKER not in json.dumps(events[0].data)


# --- 2. the payload is bound to its row ---------------------------------------


async def test_a_key_presented_under_another_context_is_refused(owner, db) -> None:
    """Purpose, record and generation are all part of what the ciphertext belongs to.

    This is the half of the design that keeps *one* organization DEK from making
    every Phase-5 secret interchangeable: the envelope is shared, the payload is not.
    """
    org_id = _org_id(owner)
    async with _scoped(db, org_id) as scoped:
        account = await account_for(scoped, None, org_id=org_id, directory=STAGING)
        row = await _stored(scoped, account.id)

        async with org_dek_context(scoped, org_id) as dek:
            assert dek.generation == row.deke_id

            def read(**overrides: Any) -> str:
                context = PayloadContext(
                    org_id=org_id,
                    purpose=PURPOSE_ACME_ACCOUNT_KEY,
                    record_id=row.id,
                    deke_id=row.deke_id,
                )
                return decrypt_str(dek.fernet, context, row.key_ciphertext)

            # Under its own context the key comes back; every other placement fails.
            assert read().startswith(f"-----{PEM_MARKER}-----")
            for wrong in (
                # The other purpose under this same envelope and row.
                PayloadContext(
                    org_id=org_id,
                    purpose=PURPOSE_DNS_CREDENTIALS,
                    record_id=row.id,
                    deke_id=row.deke_id,
                ),
                # Another record.
                PayloadContext(
                    org_id=org_id,
                    purpose=PURPOSE_ACME_ACCOUNT_KEY,
                    record_id=uuid.uuid4(),
                    deke_id=row.deke_id,
                ),
                # Another DEK generation.
                PayloadContext(
                    org_id=org_id,
                    purpose=PURPOSE_ACME_ACCOUNT_KEY,
                    record_id=row.id,
                    deke_id=row.deke_id + 1,
                ),
            ):
                with pytest.raises(PayloadContextMismatch):
                    decrypt_str(dek.fernet, wrong, row.key_ciphertext)


async def test_a_key_from_another_organization_cannot_be_read_back(owner, second_org, db) -> None:
    """The tenant boundary is the account boundary, at the payload level too."""
    here = _org_id(owner)
    there = uuid.UUID(second_org["id"])
    async with _scoped(db, here) as scoped:
        account = await account_for(scoped, None, org_id=here, directory=STAGING)
        row = await _stored(scoped, account.id)

    # The other organization has no account at this directory, and its own scoped
    # read cannot see this one at all.
    async with _scoped(db, there) as scoped:
        assert await find_account(scoped, org_id=there, directory=STAGING) is None
        assert await _account_count(scoped) == 0

        theirs = await account_for(scoped, None, org_id=there, directory=STAGING)
        assert theirs.id != row.id
        assert theirs.key_fingerprint != row.key_fingerprint

        # And the first organization's ciphertext is not readable as theirs: the
        # organization is part of the binding, so the wrong tenant is refused before
        # decryption even when the record id is known.
        async with org_dek_context(scoped, there) as dek:
            context = PayloadContext(
                org_id=there,
                purpose=PURPOSE_ACME_ACCOUNT_KEY,
                record_id=row.id,
                deke_id=row.deke_id,
            )
            with pytest.raises(PayloadContextMismatch):
                decrypt_str(dek.fernet, context, row.key_ciphertext)


async def test_a_generation_the_row_has_not_been_rewrapped_for_is_a_named_failure(
    owner, db
) -> None:
    """A DEK rotation that has not reached this row says so — it never guesses.

    The fix is to finish the rotation, not to try the current key: the current key
    could not have produced this ciphertext, so a silent fallback would only turn a
    lagging rotation into an unreadable account key at issuance time.
    """
    org_id = _org_id(owner)
    async with _scoped(db, org_id) as scoped:
        account = await account_for(scoped, None, org_id=org_id, directory=STAGING)
        await scoped.execute(
            text("UPDATE acme_accounts SET deke_id = :stale WHERE id = :id"),
            {"stale": FIRST_GENERATION + 1, "id": str(account.id)},
        )
        await scoped.commit()

        row = await _stored(scoped, account.id)
        with pytest.raises(AcmeAccountKeyUnavailable) as raised:
            await account_key(scoped, row)
        assert raised.value.code == "ACME_ACCOUNT_KEY_ROTATION_PENDING"
        assert "DEK rotation" in raised.value.message


async def test_an_unknown_directory_is_refused_rather_than_defaulted(owner, db) -> None:
    """No staging default, no production fallback (§5.4): an unset directory fails.

    Both directions of a silent fallback are wrong — one mints a certificate a
    browser distrusts, the other burns production rate limit for a staging test —
    so a caller with no configured directory has a configuration bug, not an
    account.
    """
    with pytest.raises(UnprocessableEntity) as raised:
        resolve_directory("acme-1")
    assert raised.value.code == "ACME_DIRECTORY_UNKNOWN"
    assert "staging" in raised.value.message and "production" in raised.value.message

    org_id = _org_id(owner)
    async with _scoped(db, org_id) as scoped:
        with pytest.raises(UnprocessableEntity) as raised:
            await account_for(scoped, None, org_id=org_id, directory="acme-1")
        assert raised.value.code == "ACME_DIRECTORY_UNKNOWN"
        # Nothing was created on the way to the refusal.
        assert await _account_count(scoped) == 0


# --- 3. registration records the kid, once ------------------------------------


async def test_registration_records_the_kid_once_and_refuses_to_repoint_it(owner, db) -> None:
    """The account URL becomes the JWS ``kid``, so it is write-once in effect.

    A repointed ``kid`` would sign this organization's requests as a different
    account at the CA, so the second, different URL is a conflict rather than an
    update — while the *same* URL stays a no-op, because registration is retried.
    """
    org_id = _org_id(owner)
    account_url = "https://acme-staging-v02.api.letsencrypt.org/acme/acct/123456"
    async with _scoped(db, org_id) as scoped:
        account = await account_for(scoped, None, org_id=org_id, directory=STAGING)

        registered = await record_registration(scoped, account, account_url=account_url)
        assert registered.account_url == account_url
        assert registered.last_used_at is not None
        assert summary(registered)["registered"] is True
        assert len(await _events(scoped, "ACME_ACCOUNT_REGISTERED")) == 1

        # Idempotent: the retry publishes nothing new.
        await record_registration(scoped, account, account_url=account_url)
        assert len(await _events(scoped, "ACME_ACCOUNT_REGISTERED")) == 1

        with pytest.raises(Conflict) as raised:
            await record_registration(scoped, account, account_url=account_url + "9")
        assert raised.value.code == "ACME_ACCOUNT_ALREADY_REGISTERED"
        # The stored value is unchanged by the refusal.
        assert (await _stored(scoped, account.id)).account_url == account_url
        assert len(await _events(scoped, "ACME_ACCOUNT_REGISTERED")) == 1

        # Registering does not re-key anything: the same key is still readable.
        pem = await account_key(scoped, await _stored(scoped, account.id))
        assert account_key_fingerprint(pem) == account.key_fingerprint


# --- 4. one envelope per organization, one purpose per payload -----------------


async def test_a_stored_credential_does_not_cost_the_organization_its_acme_account(
    client, owner, db
) -> None:
    """The claim this module exists for, in the order that was reported broken.

    An operator stores a DNS credential — a *different* purpose that encrypts under
    the same organization DEK — and the organization must still be able to unwrap
    its own DEK for ACME. There is one envelope per organization (§6.7), so the
    envelope's purpose is ``org-dek`` for both; binding that single envelope to the
    first subsystem to use it would make the second one unable to unwrap the very
    same key. Purpose separation lives one layer down, on the ciphertext, and this
    test asserts both halves: the envelope is shared, and the payloads are not
    interchangeable.
    """
    org_id = _org_id(owner)
    credential = await _store_credential(client, owner)

    async with _scoped(db, org_id) as scoped:
        account = await account_for(scoped, None, org_id=org_id, directory=STAGING)

        # One envelope, claimed once, and both ciphertexts are under that same
        # generation — which is the whole point: there is no per-subsystem DEK.
        envelopes = list(
            (
                await scoped.execute(
                    select(OrganizationDekEnvelope).where(OrganizationDekEnvelope.org_id == org_id)
                )
            ).scalars()
        )
        assert len(envelopes) == 1

        provider_row = await scoped.get(DnsProvider, uuid.UUID(credential["id"]))
        assert provider_row is not None
        account_row = await _stored(scoped, account.id)
        assert provider_row.deke_id == account_row.deke_id == FIRST_GENERATION

        # Both purposes still read back correctly under the one DEK — the credential
        # to the issuer of challenge records, the account key to the signer.
        assert await dns_provider_service.credentials_for_use(scoped, provider_row) == {
            "api_token": DNS_TOKEN
        }
        assert (await account_key(scoped, account_row)).startswith(f"-----{PEM_MARKER}-----")

        # ...and they are not interchangeable. The shared envelope does not make the
        # credential readable as an account key: the purpose is in the binding.
        async with org_dek_context(scoped, org_id) as dek:
            with pytest.raises(PayloadContextMismatch):
                decrypt_str(
                    dek.fernet,
                    PayloadContext(
                        org_id=org_id,
                        purpose=PURPOSE_ACME_ACCOUNT_KEY,
                        record_id=provider_row.id,
                        deke_id=provider_row.deke_id,
                    ),
                    provider_row.credentials_ciphertext,
                )

    # Nothing about the account leaked into the credential's API surface either.
    assert DNS_TOKEN not in json.dumps(credential)
    assert credential["deke_id"] == FIRST_GENERATION


async def test_the_same_holds_when_the_account_comes_first(client, owner, db) -> None:
    """The mirror order, because the envelope claim is not order-dependent.

    Whichever subsystem runs first claims the organization's DEK; if the envelope's
    binding depended on which one that was, exactly one order would work and the
    other would fail in production with an unwrap error nobody could explain.
    """
    org_id = _org_id(owner)
    async with _scoped(db, org_id) as scoped:
        account = await account_for(scoped, None, org_id=org_id, directory=STAGING)
        account_id = account.id
        # Committed before the HTTP call below: the API writes through its own
        # session, and an account left uncommitted here would hold the
        # organization's envelope row while that request tried to claim it.
        await scoped.commit()

    credential = await _store_credential(client, owner, name="after the account")

    async with _scoped(db, org_id) as scoped:
        provider_row = await scoped.get(DnsProvider, uuid.UUID(credential["id"]))
        assert provider_row is not None
        account_row = await _stored(scoped, account_id)
        assert provider_row.deke_id == account_row.deke_id == FIRST_GENERATION
        assert (await account_key(scoped, account_row)).startswith(f"-----{PEM_MARKER}-----")
        assert await dns_provider_service.credentials_for_use(scoped, provider_row) == {
            "api_token": DNS_TOKEN
        }


async def test_reaching_an_account_outside_a_scope_fails_loudly(owner, db) -> None:
    """The service is not a route, so the boundary it enforces is tenancy itself.

    ``account_for`` is called by the issuance worker, which acts for an organization
    without a user, so there is no permission check to borrow: what must hold is
    that an unscoped read of an account row refuses rather than returning every
    tenant's accounts — and that the refusal is the *scope* error, not an empty
    result that reads like "no account yet".
    """
    org_id = _org_id(owner)
    async with _scoped(db, org_id) as scoped:
        account = await account_for(scoped, None, org_id=org_id, directory=STAGING)

    with pytest.raises(TenancyScopeError):
        await db.get(AcmeAccount, account.id, populate_existing=True)

    # And the mirror case: a scope for a *different* organization is refused too,
    # rather than reaching this organization's envelope and minting one for itself.
    async with _scoped(db, uuid.uuid4()) as other:
        with pytest.raises(TenancyScopeError):
            await account_for(other, None, org_id=org_id, directory=STAGING)
