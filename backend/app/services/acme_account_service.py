"""One ACME account per organization per directory, and its wrapped account key.

The account is the tenant's identity at the certificate authority. Phase 5.2.2
ships the row and its custody rules; **registration is 5.3**, so nothing here
contacts a CA — ``account_for()`` creates the account *locally*, with its key pair
generated control-plane-side and stored Fernet(**org DEK**) in
``acme_accounts.key_ciphertext``, and ``account_url`` stays NULL until the
registration slice writes the ``kid`` the CA returned.

Why an account per organization rather than one platform account
(phase5-design.md §5.4): rate-limit blast radius and revocation ownership. A shared
account would let one tenant's issuance exhaust another tenant's budget, and would
make every revocation the platform's problem to attribute. The cost is stated
plainly in the design's limitations (L5), not hidden here.

Two custody rules the code enforces rather than documents:

* the key is reconstructed **only** by :func:`account_key`, whose callers are the
  ACME client (5.3) and rotation — never an API route, never a read model;
* the payload is bound to ``(organization, purpose, record, DEK generation)`` by
  :mod:`app.services.payload_crypto`, so an account key moved to another row,
  another organization or another DEK generation is refused before it is decrypted
  and the account cannot be signed for with a key that was not issued for it.

Creation is idempotent under a race: two concurrent issuance attempts for the same
organization and directory converge on one row (the unique constraint decides the
winner, the loser adopts it) rather than registering two accounts.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext
from app.core.errors import Conflict, UnprocessableEntity
from app.core.logging import get_logger
from app.models import AcmeAccount
from app.models.enums import AcmeDirectory, ActorType, CertificateKeyAlgorithm
from app.services import audit_service, event_bus
from app.services.dek_envelope import org_dek_context
from app.services.payload_crypto import (
    PURPOSE_ACME_ACCOUNT_KEY,
    PayloadContext,
    decrypt_str,
    encrypt,
    fingerprint,
)

log = get_logger("nexusops.acme_accounts")

#: The DEK is taken from :func:`org_dek_context` **without a purpose argument**.
#: That keyword binds the *organization DEK envelope* to a KEK derivation context,
#: and there is one envelope per organization (phase5-design.md §6.7) — passing
#: ``acme.account_key`` here would bind that single envelope to this subsystem, and
#: an organization that stored a DNS credential first would then be unable to
#: unwrap its own DEK for ACME. Purpose separation is enforced one layer down by
#: :class:`~app.services.payload_crypto.PayloadContext`, on the ciphertext.

#: Domain separation for the account-key fingerprint. A fingerprint here is
#: display and change detection ("is this the same account key as before?"), never
#: a decryption oracle and never compared against caller-supplied secret material.
_FINGERPRINT_KIND = "acme.account_key"

#: Fixed in v1 (§5.4): the account key is P-256, like every certificate key. Not
#: client-chosen, so a caller cannot ask for a key the JWS signing path does not
#: implement.
_ACCOUNT_KEY_ALGORITHM = CertificateKeyAlgorithm.ECDSA_P256


class AcmeAccountKeyUnavailable(RuntimeError):
    """The stored account key cannot be read right now.

    One cause is named rather than reported as a generic decryption failure: the
    row's ``deke_id`` is behind the organization's current DEK generation, which
    means a DEK rotation has not re-encrypted it yet (§6.3). The fix is to finish
    that rotation — never to try another key, which could not have produced this
    ciphertext.
    """

    def __init__(self, message: str, *, code: str = "ACME_ACCOUNT_KEY_UNAVAILABLE") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


def resolve_directory(directory: AcmeDirectory | str) -> AcmeDirectory:
    """The named directory, or a 422 naming the closed set.

    Deliberately *not* a default: there is no "if unset, use staging" branch and no
    fallback to production, because both directions are silent downgrades or
    upgrades the design forbids (§5.4). A caller with no configured directory has a
    configuration bug, which fails here.
    """
    if isinstance(directory, AcmeDirectory):
        return directory
    try:
        return AcmeDirectory(directory)
    except ValueError as exc:
        raise UnprocessableEntity(
            f"'{directory}' is not a known ACME directory. Configure one of: "
            f"{', '.join(sorted(member.value for member in AcmeDirectory))}.",
            code="ACME_DIRECTORY_UNKNOWN",
        ) from exc


def generate_account_key() -> str:
    """A fresh P-256 account key, PEM-encoded (PKCS#8).

    PEM because that is the interchange form the ACME client signs with; PKCS#8
    because it is the one form that carries the curve without a separate parameter
    block. Generated here, in the control plane, and handed straight to the
    encryptor — the plaintext never leaves this call's frame except as the wrapped
    payload stored on the row.
    """
    key = ec.generate_private_key(ec.SECP256R1())
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()


def account_key_fingerprint(pem: str) -> str:
    """Fingerprint the **public** half of a PEM account key.

    Over the public key rather than the private one on purpose: the fingerprint is
    shown to operators and written to an audit entry (``acme_account.created``), and
    a handle derived from the private half would be a (weak) oracle for it. The
    public half identifies the account just as well — it is what the CA knows.
    """
    try:
        public = serialization.load_pem_private_key(pem.encode(), password=None).public_key()
        der = public.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    except (ValueError, TypeError) as exc:  # pragma: no cover - only a broken key reaches this
        raise UnprocessableEntity(
            "The generated ACME account key could not be read back as a PEM private key.",
            code="ACME_ACCOUNT_KEY_UNREADABLE",
        ) from exc
    return fingerprint(der, kind=_FINGERPRINT_KIND)


def _actor(ctx: AuthContext | None) -> tuple[uuid.UUID | None, ActorType]:
    if ctx is None:
        return None, ActorType.SYSTEM
    try:
        return ctx.user_id, ActorType(ctx.actor_type)
    except ValueError:
        return ctx.user_id, ActorType.USER


def summary(account: AcmeAccount) -> dict[str, Any]:
    """Metadata for a log line, an audit entry or an event payload.

    An explicit allowlist, for the same reason the DNS provider serializer is one:
    ``key_ciphertext`` is not named here, so a column added later cannot start
    leaking because it happened to be on the object.

    ``directory`` is the stored **value** (``staging``), not the enum member's name
    (``STAGING``): the audit entry and the event published for the same account both
    spell it that way, and two spellings of one field would be a difference an
    operator has to decode rather than read.
    """
    return {
        "id": str(account.id),
        "directory_url": account.directory_url,
        "directory": (account.directory.value if account.directory is not None else "unknown"),
        "key_fingerprint": account.key_fingerprint,
        "key_algorithm": str(account.key_algorithm),
        "deke_id": account.deke_id,
        "registered": account.account_url is not None,
        "last_used_at": account.last_used_at.isoformat() if account.last_used_at else None,
    }


async def find_account(
    db: AsyncSession, *, org_id: uuid.UUID, directory: AcmeDirectory | str
) -> AcmeAccount | None:
    """The organization's account at *directory*, if it has one. Read-only."""
    resolved = resolve_directory(directory)
    return await db.scalar(
        select(AcmeAccount).where(
            AcmeAccount.org_id == org_id, AcmeAccount.directory_url == resolved.url()
        )
    )


async def account_for(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    org_id: uuid.UUID,
    directory: AcmeDirectory | str,
    request: Request | None = None,
) -> AcmeAccount:
    """The organization's account at *directory*, created on first use.

    Creating the account here — generating its key and wrapping it under the
    organization DEK — means the issuance path (5.3) never has to decide whether an
    account exists: it asks for one and gets a row that can sign. Registration with
    the CA (and therefore ``account_url``) is a separate, later step
    (:func:`record_registration`), so this function is safe to call from a retry.
    """
    resolved = resolve_directory(directory)
    directory_url = resolved.url()
    existing = await find_account(db, org_id=org_id, directory=resolved)
    if existing is not None:
        return existing

    account_id = uuid.uuid4()
    pem = generate_account_key()
    # Fingerprinted from the plaintext while it is still here: the fingerprint is
    # over the *public* half, so deriving it needs the private key once and needs it
    # never again. Computing it after the wrap would mean decrypting a row to
    # label it.
    key_fingerprint = account_key_fingerprint(pem)
    async with org_dek_context(db, org_id) as dek:
        context = PayloadContext(
            org_id=org_id,
            purpose=PURPOSE_ACME_ACCOUNT_KEY,
            record_id=account_id,
            deke_id=dek.generation,
        )
        key_ciphertext = encrypt(dek.fernet, context, pem.encode())
        deke_id = dek.generation
    del pem  # the plaintext is not held past the wrap

    account = AcmeAccount(
        id=account_id,
        directory_url=directory_url,
        account_url=None,
        key_ciphertext=key_ciphertext,
        key_fingerprint=key_fingerprint,
        deke_id=deke_id,
        key_algorithm=_ACCOUNT_KEY_ALGORITHM,
    )
    try:
        # Inside a savepoint: two concurrent issuance attempts can both miss the
        # row above, and the loser must adopt the winner's account rather than
        # fail the whole attempt (or, worse, register a second account).
        async with db.begin_nested():
            db.add(account)
            await db.flush()
    except IntegrityError:
        if account in db:
            # The failed INSERT expunges the object; drop it explicitly so no
            # later flush retries it against the same unique constraint.
            db.expunge(account)
        winner = await find_account(db, org_id=org_id, directory=resolved)
        if winner is None:  # pragma: no cover - the constraint fired, so a row exists
            raise
        log.info("acme_account_adopted", account=str(winner.id), directory=resolved.value)
        return winner

    await audit_service.record(
        db,
        ctx,
        action="acme_account.created",
        resource_type="acme_account",
        resource_id=account.id,
        # The fingerprint, never the key: an audit entry records that an account
        # key exists and which one it is, not what it is.
        metadata={
            "directory": resolved.value,
            "directory_url": directory_url,
            "key_fingerprint": account.key_fingerprint,
        },
        request=request,
    )
    actor_id, actor_type = _actor(ctx)
    await event_bus.publish(
        db,
        type="ACME_ACCOUNT_CREATED",
        message=f"ACME account created for the {resolved.value} directory",
        actor_id=actor_id,
        actor_type=actor_type,
        resource_type="acme_account",
        resource_id=str(account.id),
        data={"directory": resolved.value, "directory_url": directory_url},
        org_id=org_id,
    )
    log.info("acme_account_created", account=str(account.id), directory=resolved.value)
    return account


async def account_key(db: AsyncSession, account: AcmeAccount) -> str:
    """Decrypt the account key **for one operation**, then drop it.

    INTERNAL USE ONLY — the ACME client (5.3) and rotation. Not reachable from any
    route, and it must not become reachable: every read model in this subsystem is
    metadata, and the account key is the credential that signs for a tenant.

    The payload context includes the row's ``deke_id``, so the key can only be read
    back under the DEK generation that wrote it. If the organization's envelope has
    moved on and the row has not been re-encrypted yet, that is a named failure.
    """
    context = PayloadContext(
        org_id=account.org_id,
        purpose=PURPOSE_ACME_ACCOUNT_KEY,
        record_id=account.id,
        deke_id=account.deke_id,
    )
    async with org_dek_context(db, account.org_id) as dek:
        if dek.generation != account.deke_id:
            raise AcmeAccountKeyUnavailable(
                "this ACME account key was encrypted under an older organization DEK "
                f"generation ({account.deke_id}) and the current one is {dek.generation}; "
                "finish the DEK rotation before issuing with this account",
                code="ACME_ACCOUNT_KEY_ROTATION_PENDING",
            )
        return decrypt_str(dek.fernet, context, account.key_ciphertext)


async def record_registration(
    db: AsyncSession, account: AcmeAccount, *, account_url: str
) -> AcmeAccount:
    """Record the CA's account URL, which becomes the JWS ``kid`` (5.3).

    Idempotent and monotonic in the direction that matters: the same URL is a
    no-op, and a *different* URL for an account that was already registered is
    refused rather than silently repointed — a repointed ``kid`` would sign the
    tenant's requests as a different account at the CA.
    """
    if account.account_url is None:
        account.account_url = account_url
        account.last_used_at = datetime.now(UTC)
        await db.flush()
        await event_bus.publish(
            db,
            type="ACME_ACCOUNT_REGISTERED",
            message="ACME account registered with the certificate authority",
            resource_type="acme_account",
            resource_id=str(account.id),
            data={"directory_url": account.directory_url},
            org_id=account.org_id,
        )
        return account
    if account.account_url != account_url:
        raise Conflict(
            "This ACME account is already registered at a different account URL. "
            "Registering it again would change which account signs for this organization.",
            code="ACME_ACCOUNT_ALREADY_REGISTERED",
        )
    return account


async def mark_used(db: AsyncSession, account: AcmeAccount) -> None:
    """Record that the issuance path used this account, so stale ones are visible."""
    account.last_used_at = datetime.now(UTC)
    await db.flush()


__all__ = [
    "AcmeAccountKeyUnavailable",
    "account_for",
    "account_key",
    "account_key_fingerprint",
    "find_account",
    "generate_account_key",
    "mark_used",
    "record_registration",
    "resolve_directory",
    "summary",
]
