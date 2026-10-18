"""DNS credentials: accept, verify, list, and enforce the zone allowlist.

A DNS credential is a **write-only secret**: the API accepts it, the platform
encrypts it under the organization DEK and records a fingerprint of it, and no
read path ever returns it (phase5-design.md §3.4). Two mechanisms make that more
than a promise:

* every serializer here is an allowlist of metadata fields — ``_detail`` names
  each field it emits and ``credentials_ciphertext`` is not among them, so a new
  column cannot leak by default;
* the plaintext is only reconstructible through :func:`credentials_for_use`, whose
  callers are the issuance path (5.3) and the verifier — never an API route.

**The zone allowlist is enforced before any provider call** (§5.3). A challenge
for a name outside the allowed zones is refused with a named error, so a
compromised or simply wrong credential cannot be used to write records in a zone
the customer did not authorize. An empty allowlist authorizes **nothing**: the
fail-closed reading, chosen deliberately over a convenient "no allowlist means no
restriction".

Verification is a *recorded result*, not a gate: ``verify_creds()`` runs on save
and on demand, and its outcome (``verified_at``/``verify_error``/``scopes``) is
stored so a broken credential is visible on the row rather than surfacing as a
failed issuance later. A provider outage never rolls back a stored credential.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from typing import Any

from fastapi import Request
from sqlalchemy import ColumnElement, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext
from app.core.dnsname import InvalidName, canonicalize_name, canonicalize_record_name
from app.core.errors import Conflict, NotFound, UnprocessableEntity
from app.core.logging import get_logger
from app.core.pagination import PageParams, paginate
from app.models import Certificate, DnsProvider
from app.models.dns_provider import MAX_ALLOWLISTED_ZONES
from app.models.enums import ActorType, DnsProviderKind, EventLevel
from app.providers.dns import CredentialCheck, DnsCredentialError, provider_for
from app.schemas.dns_provider import DnsProviderCreate, DnsProviderUpdate
from app.services import audit_service, event_bus
from app.services.dek_envelope import org_dek_context
from app.services.payload_crypto import (
    PURPOSE_DNS_CREDENTIALS,
    PayloadContext,
    decrypt_str,
    encrypt,
    fingerprint,
)

log = get_logger("nexusops.dns_providers")

#: Every call below takes the DEK from :func:`org_dek_context` **without a purpose
#: argument**, and that is deliberate rather than an omission.
#:
#: ``purpose`` there is the KEK binding of the *organization DEK envelope*, and
#: there is exactly one such envelope per organization (phase5-design.md §6.7).
#: Passing ``dns.credentials`` — the purpose of the payload this module stores —
#: would bind that one envelope to a purpose, so whichever subsystem wrote first
#: (a DNS credential, an ACME account key, certificate material) would own the
#: binding and every other one would fail to unwrap the very same DEK. The KEK
#: rotation sweep re-wraps under ``org-dek`` for the same reason
#: (:func:`app.services.dek_envelope.rewrap_org_deks`).
#:
#: Purpose separation is real, but it lives one layer down, in
#: :class:`~app.services.payload_crypto.PayloadContext`: the ciphertext — not the
#: key — is bound to ``(organization, purpose, record, DEK generation)``, so a
#: credential encrypted here cannot be presented as an ACME account key even
#: though both are protected by the same per-organization DEK.

#: Upper bounds on the credential blob. A bound, not a schema: it keeps a caller
#: from using the credential field as a storage amplifier, and every value this
#: bounds is a token, never a document.
MAX_CREDENTIAL_FIELDS = 8
MAX_CREDENTIAL_VALUE_LENGTH = 4096

#: Length of the fingerprint we store (lower-case hex SHA-256).
_FINGERPRINT_KIND = "dns.credentials"


class DnsCredentialUnavailable(RuntimeError):
    """The stored credential cannot be read right now.

    One cause matters and is named rather than reported as a generic decryption
    failure: the row's ``deke_id`` is behind the organization's current DEK
    generation, which means a DEK rotation has not re-encrypted it yet (§6.3). The
    fix is to finish that rotation, not to try another key.
    """

    def __init__(self, message: str, *, code: str = "DNS_CREDENTIAL_UNAVAILABLE") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


def _actor(ctx: AuthContext | None) -> tuple[uuid.UUID | None, ActorType]:
    if ctx is None:
        return None, ActorType.SYSTEM
    try:
        return ctx.user_id, ActorType(ctx.actor_type)
    except ValueError:
        return ctx.user_id, ActorType.USER


# --- The credential blob -------------------------------------------------------


def resolve_kind(kind: DnsProviderKind | str) -> DnsProviderKind:
    """The named provider kind, or a 422 that lists the closed set.

    Deliberately **not** a fallback: ``cloudflare`` is the value the schema applies
    to a field the caller omitted, not something substituted for a kind the caller
    chose and the control plane cannot call. An unknown kind is refused here, as a
    named client error, rather than reaching the database and surfacing as a CHECK
    violation — or worse, as an unhandled ``ValueError``.
    """
    if isinstance(kind, DnsProviderKind):
        return kind
    try:
        return DnsProviderKind(kind)
    except ValueError as exc:
        raise UnprocessableEntity(
            f"'{kind}' is not a supported DNS provider kind. Supported: "
            f"{', '.join(sorted(member.value for member in DnsProviderKind))}.",
            code="DNS_PROVIDER_KIND_UNSUPPORTED",
        ) from exc


def normalize_credentials(kind: DnsProviderKind, raw: Mapping[str, str]) -> dict[str, str]:
    """Validate and trim a submitted credential blob for *kind*.

    Rejects rather than repairs: an empty required field, a non-string value or a
    payload larger than the bounds is the caller's mistake and becomes a 422, so a
    half-specified credential is never stored (and never "verified" against an
    empty token).
    """
    provider = provider_for(kind)
    if not raw:
        raise DnsCredentialError("a DNS provider needs its credentials")
    if len(raw) > MAX_CREDENTIAL_FIELDS:
        raise DnsCredentialError(f"at most {MAX_CREDENTIAL_FIELDS} credential fields are accepted")
    cleaned: dict[str, str] = {}
    for key, value in raw.items():
        if not isinstance(value, str):  # pragma: no cover - pydantic enforces dict[str, str]
            raise DnsCredentialError(f"credential field {key!r} must be a string")
        trimmed = value.strip()
        if len(trimmed) > MAX_CREDENTIAL_VALUE_LENGTH:
            raise DnsCredentialError(f"credential field {key!r} is too long")
        if trimmed:
            cleaned[key] = trimmed
    for required in provider.required_fields:
        if not cleaned.get(required):
            raise DnsCredentialError(
                f"a {provider.name} credential needs a non-empty {required!r}",
                code="DNS_CREDENTIAL_INCOMPLETE",
            )
    return cleaned


def canonical_blob(credentials: Mapping[str, str]) -> bytes:
    """A stable serialization of the credential blob.

    Stable because it is what the stored fingerprint is computed over: re-pasting
    the same token must produce the same fingerprint (so "did it change?" is
    answerable), and a JSON object's key order must not make it look changed. It is
    never logged, never returned and never compared against caller input as a
    secret check.
    """
    return json.dumps(
        {key: credentials[key] for key in sorted(credentials)}, separators=(",", ":")
    ).encode()


def _canonical_zone(entry: str) -> str:
    """Canonicalize one allowlist entry, tolerating a wildcard prefix.

    ``*.example.com`` is accepted as a synonym for ``example.com`` — the allowlist
    bounds *zones*, and an operator copying a wildcard identifier out of a
    certificate request should not have the entry rejected as malformed. It is not
    treated as "subdomains only", which would be a different rule than the one the
    design states.
    """
    candidate = entry.strip()
    if candidate.startswith("*."):
        candidate = candidate[2:]
    return canonicalize_name(candidate)


def normalize_zone_allowlist(entries: Sequence[str]) -> list[str]:
    """Canonical, de-duplicated, order-preserving allowlist of zones."""
    if len(entries) > MAX_ALLOWLISTED_ZONES:
        raise UnprocessableEntity(
            f"A DNS provider may be allowlisted for at most {MAX_ALLOWLISTED_ZONES} zones.",
            code="DNS_ZONE_ALLOWLIST_TOO_LONG",
        )
    zones: list[str] = []
    for entry in entries:
        try:
            zone = _canonical_zone(entry)
        except InvalidName as exc:
            raise UnprocessableEntity(
                f"'{entry}' is not a usable zone name: {exc.message}",
                code="DNS_ZONE_INVALID",
            ) from exc
        if zone not in zones:
            zones.append(zone)
    return zones


def zone_allows(allowlist: Sequence[str], name: str) -> bool:
    """Whether *name* is inside one of the allowlisted zones. **Pure.**

    The rule is a zone boundary, not a record match: ``name`` is allowed when it
    equals an allowlisted zone or sits beneath it. Both the challenge record
    (``_acme-challenge.www.example.com``) and the identifier it is issued for
    (``www.example.com``) are inside ``example.com``, so the same predicate serves
    the pre-flight check and the cleanup path — which is why the candidate is
    canonicalised as a **record name**: the challenge owner is the one name in this
    subsystem that carries a service label (``_acme-challenge``), and refusing it
    here would refuse the publish the allowlist exists to permit.

    An empty allowlist allows nothing. That is the fail-closed reading and it is
    the whole point of the field: a credential with no authorized zone can only be
    used to write somewhere the customer did not name.
    """
    try:
        candidate = canonicalize_record_name(name, allow_wildcard=True)
    except InvalidName:
        return False
    apex_candidate = candidate[2:] if candidate.startswith("*.") else candidate
    for entry in allowlist:
        try:
            zone = _canonical_zone(entry)
        except InvalidName:  # pragma: no cover - entries are normalized before storage
            continue
        if apex_candidate == zone or apex_candidate.endswith(f".{zone}"):
            return True
    return False


def require_zone_allowed(provider: DnsProvider, name: str) -> None:
    """Refuse *name* unless the provider's allowlist covers it (§5.3).

    Raised **before** any provider call, so a refusal costs nothing and cannot be
    turned into a write. The code is stable so callers (the issuance task and the
    API) can map it without parsing the message.
    """
    if zone_allows(provider.zone_allowlist or [], name):
        return
    raise UnprocessableEntity(
        f"'{name}' is not inside any zone this DNS credential is allowlisted for. "
        "Add the zone to the provider's allowlist before issuing for this name.",
        code="DNS_ZONE_NOT_ALLOWED",
    )


# --- Reads ---------------------------------------------------------------------


def detail(provider: DnsProvider) -> dict[str, Any]:
    """Serialise provider **metadata**. No credential-bearing field may appear.

    Public (not ``_detail``) because the API layer builds its response model from
    exactly this mapping rather than from the ORM object: the response can only
    contain what is enumerated here, so adding a column to the model does not add
    it to every response — which is what stops a ciphertext field from leaking by
    default. There is one serializer, used by both the detail route and the list
    route, so a page cannot expose a field a single read does not.
    """
    return {
        "id": provider.id,
        "name": provider.name,
        "kind": provider.kind,
        "scopes": provider.scopes,
        "zone_allowlist": provider.zone_allowlist,
        "credential_fingerprint": provider.credential_fingerprint,
        "deke_id": provider.deke_id,
        "verified_at": provider.verified_at,
        "verify_error": provider.verify_error,
        "auto_cleanup": provider.auto_cleanup,
        "last_used_at": provider.last_used_at,
        "created_at": provider.created_at,
        "updated_at": provider.updated_at,
    }


async def require_provider(db: AsyncSession, provider_id: uuid.UUID) -> DnsProvider:
    """The provider row, or the same 404 a random uuid gets (no existence oracle)."""
    provider = await db.get(DnsProvider, provider_id)
    if provider is None:
        raise NotFound("DNS provider not found", code="DNS_PROVIDER_NOT_FOUND")
    return provider


async def list_dns_providers(
    db: AsyncSession,
    params: PageParams,
    *,
    q: str | None = None,
    kind: DnsProviderKind | None = None,
) -> tuple[list[DnsProvider], int]:
    filters: list[ColumnElement[bool]] = []
    if q:
        filters.append(DnsProvider.name.ilike(f"%{q}%"))
    if kind is not None:
        filters.append(DnsProvider.kind == kind)
    stmt = select(DnsProvider).where(*filters).order_by(DnsProvider.name.asc())
    return await paginate(db, stmt, params)


async def provider_detail(db: AsyncSession, provider_id: uuid.UUID) -> dict[str, Any]:
    return detail(await require_provider(db, provider_id))


async def credentials_for_use(db: AsyncSession, provider: DnsProvider) -> dict[str, str]:
    """Decrypt a stored credential **for one call**, then drop it.

    INTERNAL USE ONLY —    the issuance path and the verifier. It is not reachable
    from any route, and it must not become reachable: everything a customer-facing
    read returns comes from :func:`detail`.

    The payload context includes the row's ``deke_id``, so the value can only be
    read back under the DEK generation that wrote it. If the organization's
    envelope has moved on and this row has not yet been re-encrypted, that is a
    named failure — never a silent attempt with a key that cannot have produced
    the ciphertext.
    """
    context = PayloadContext(
        org_id=provider.org_id,
        purpose=PURPOSE_DNS_CREDENTIALS,
        record_id=provider.id,
        deke_id=provider.deke_id,
    )
    async with org_dek_context(db, provider.org_id) as dek:
        if dek.generation != provider.deke_id:
            raise DnsCredentialUnavailable(
                "this credential was encrypted under an older organization DEK "
                f"generation ({provider.deke_id}) and the current one is "
                f"{dek.generation}; finish the DEK rotation before using it",
                code="DNS_CREDENTIAL_ROTATION_PENDING",
            )
        return json.loads(decrypt_str(dek.fernet, context, provider.credentials_ciphertext))


# --- Mutations -----------------------------------------------------------------


async def _verify(
    kind: DnsProviderKind, credentials: Mapping[str, str], allowlist: Sequence[str]
) -> CredentialCheck:
    """Run the provider's verification and fold in the allowlist observation.

    A provider-side failure is a result, not an exception; only a *malformed*
    credential raises, and that is rejected before anything is stored.
    """
    check = await provider_for(kind).verify_creds(credentials)
    if not check.ok:
        return check
    visible = {str(zone).lower() for zone in check.scopes.get("zone_names", [])}
    missing = [zone for zone in allowlist if zone not in visible]
    scopes = dict(check.scopes)
    if missing:
        scopes["warnings"] = [
            f"allowlisted zone {zone!r} is not visible to this credential" for zone in missing
        ]
    return CredentialCheck(ok=True, scopes=scopes, warnings=check.warnings)


async def create_dns_provider(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    payload: DnsProviderCreate,
    request: Request | None = None,
) -> DnsProvider:
    """Store a credential, verifying it first (on save, per §5.3).

    Ordering matters and is deliberate: the provider call happens **before** the
    row is written, so no transaction is held across network I/O and a credential
    that fails verification is still stored — with its failure recorded — rather
    than rejected, because the operator's next step is to read ``verify_error`` and
    fix the token, not to re-submit the form.
    """
    name = payload.name.strip()
    if not name:
        raise UnprocessableEntity("A DNS provider needs a name.", code="DNS_PROVIDER_NAME_REQUIRED")
    kind = resolve_kind(payload.kind)
    try:
        credentials = normalize_credentials(kind, payload.credentials)
    except DnsCredentialError as exc:
        raise UnprocessableEntity(exc.message, code=exc.code) from exc
    zone_allowlist = normalize_zone_allowlist(payload.zone_allowlist)
    check = await _verify(kind, credentials, zone_allowlist)

    if ctx is None:  # pragma: no cover - every API path supplies an organization
        raise UnprocessableEntity(
            "A DNS provider belongs to an organization.", code="DNS_PROVIDER_ORGANIZATION_REQUIRED"
        )
    org_id = ctx.require_org_id()

    # The record id is generated here rather than at flush time because it is part
    # of the payload context: the ciphertext is bound to the row it will live in.
    provider_id = uuid.uuid4()
    blob = canonical_blob(credentials)
    async with org_dek_context(db, org_id) as dek:
        context = PayloadContext(
            org_id=org_id,
            purpose=PURPOSE_DNS_CREDENTIALS,
            record_id=provider_id,
            deke_id=dek.generation,
        )
        ciphertext = encrypt(dek.fernet, context, blob)
        deke_id = dek.generation

    provider = DnsProvider(
        id=provider_id,
        name=name,
        kind=kind,
        credentials_ciphertext=ciphertext,
        credential_fingerprint=fingerprint(blob, kind=_FINGERPRINT_KIND),
        deke_id=deke_id,
        scopes=check.scopes,
        zone_allowlist=zone_allowlist,
        verified_at=datetime.now(UTC) if check.ok else None,
        verify_error="" if check.ok else check.error,
        auto_cleanup=payload.auto_cleanup,
    )
    db.add(provider)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise Conflict(
            "A DNS provider with this name already exists in this organization.",
            code="DNS_PROVIDER_NAME_TAKEN",
        ) from exc

    await audit_service.record(
        db,
        ctx,
        action="dns_provider.created",
        resource_type="dns_provider",
        resource_id=provider.id,
        metadata={
            "name": name,
            "kind": kind.value,
            "zones": zone_allowlist,
            "verified": check.ok,
            # The fingerprint, never the credential: an audit entry records that a
            # value was accepted and which one, not what it was.
            "credential_fingerprint": provider.credential_fingerprint,
        },
        request=request,
    )
    actor_id, actor_type = _actor(ctx)
    await event_bus.publish(
        db,
        type="DNS_PROVIDER_CREATED",
        message=f"DNS credential '{name}' stored for {kind.value}",
        actor_id=actor_id,
        actor_type=actor_type,
        resource_type="dns_provider",
        resource_id=str(provider.id),
        data={"name": name, "kind": kind.value, "verified": check.ok},
        org_id=org_id,
    )
    log.info(
        "dns_provider_created",
        provider=str(provider.id),
        kind=kind.value,
        zones=len(zone_allowlist),
        verified=check.ok,
    )
    return provider


async def update_dns_provider(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    provider_id: uuid.UUID,
    payload: DnsProviderUpdate,
    request: Request | None = None,
) -> DnsProvider:
    """Update metadata, and rotate the credential when a new one is supplied.

    Rotating replaces the ciphertext in place — the credential is one secret per
    provider, not a versioned history: the old token keeps working at the CA until
    the customer revokes it, and keeping the previous value would keep a live
    credential stored after the operator believed they had replaced it.
    """
    provider = await require_provider(db, provider_id)
    data = payload.model_dump(exclude_unset=True)
    changed: list[str] = []

    if "name" in data and data["name"] is not None:
        new_name = str(data["name"]).strip()
        if not new_name:
            raise UnprocessableEntity(
                "A DNS provider needs a name.", code="DNS_PROVIDER_NAME_REQUIRED"
            )
        if new_name != provider.name:
            provider.name = new_name
            changed.append("name")
    if "zone_allowlist" in data and data["zone_allowlist"] is not None:
        provider.zone_allowlist = normalize_zone_allowlist(data["zone_allowlist"])
        changed.append("zone_allowlist")
    if "auto_cleanup" in data and data["auto_cleanup"] is not None:
        provider.auto_cleanup = bool(data["auto_cleanup"])
        changed.append("auto_cleanup")

    if data.get("credentials") is not None:
        try:
            credentials = normalize_credentials(resolve_kind(provider.kind), data["credentials"])
        except DnsCredentialError as exc:
            raise UnprocessableEntity(exc.message, code=exc.code) from exc
        blob = canonical_blob(credentials)
        async with org_dek_context(db, provider.org_id) as dek:
            context = PayloadContext(
                org_id=provider.org_id,
                purpose=PURPOSE_DNS_CREDENTIALS,
                record_id=provider.id,
                deke_id=dek.generation,
            )
            provider.credentials_ciphertext = encrypt(dek.fernet, context, blob)
            provider.deke_id = dek.generation
        provider.credential_fingerprint = fingerprint(blob, kind=_FINGERPRINT_KIND)
        # A rotated credential has not been verified yet: keeping the previous
        # result would claim a check that was never run against this value.
        provider.verified_at = None
        provider.verify_error = ""
        provider.scopes = {}
        changed.append("credentials")

    await db.flush()
    await audit_service.record(
        db,
        ctx,
        action="dns_provider.updated",
        resource_type="dns_provider",
        resource_id=provider.id,
        metadata={"fields": sorted(changed), "name": provider.name},
        request=request,
    )
    return provider


async def verify_dns_provider(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    provider_id: uuid.UUID,
    request: Request | None = None,
) -> DnsProvider:
    """Re-run ``verify_creds()`` and store the outcome."""
    provider = await require_provider(db, provider_id)
    credentials = await credentials_for_use(db, provider)
    check = await _verify(resolve_kind(provider.kind), credentials, provider.zone_allowlist or [])
    provider.verified_at = datetime.now(UTC) if check.ok else None
    provider.verify_error = "" if check.ok else check.error
    if check.ok and check.scopes:
        provider.scopes = check.scopes
    await db.flush()

    await audit_service.record(
        db,
        ctx,
        action="dns_provider.verified" if check.ok else "dns_provider.verification_failed",
        resource_type="dns_provider",
        resource_id=provider.id,
        metadata={"name": provider.name, "kind": str(provider.kind), "verified": check.ok},
        request=request,
    )
    actor_id, actor_type = _actor(ctx)
    await event_bus.publish(
        db,
        type="DNS_PROVIDER_VERIFIED" if check.ok else "DNS_PROVIDER_VERIFICATION_FAILED",
        message=(
            f"DNS credential '{provider.name}' verified"
            if check.ok
            else f"DNS credential '{provider.name}' could not be verified"
        ),
        level=EventLevel.INFO if check.ok else EventLevel.WARNING,
        actor_id=actor_id,
        actor_type=actor_type,
        resource_type="dns_provider",
        resource_id=str(provider.id),
        data={"name": provider.name, "kind": str(provider.kind), "verified": check.ok},
        org_id=provider.org_id,
    )
    return provider


async def delete_dns_provider(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    provider_id: uuid.UUID,
    request: Request | None = None,
) -> None:
    """Remove a credential, refusing while a certificate still names it.

    The FK is ``ON DELETE RESTRICT``, so the database would refuse anyway; this
    turns that into a named 409 explaining which certificate to rebind first. A
    silent fallback to another credential would change which token the platform
    signs with on the next attempt, so deletion stays blocked until the operator
    rebinds explicitly.
    """
    provider = await require_provider(db, provider_id)
    in_use = await db.scalar(
        select(Certificate.primary_cn)
        .where(Certificate.dns_provider_id == provider.id)
        .order_by(Certificate.primary_cn.asc())
        .limit(1)
    )
    if in_use is not None:
        raise Conflict(
            f"Certificate '{in_use}' still uses this DNS credential. Point it at another "
            "provider before deleting this one.",
            code="DNS_PROVIDER_IN_USE",
        )
    name = provider.name
    await db.delete(provider)
    await db.flush()
    actor_id, actor_type = _actor(ctx)
    await event_bus.publish(
        db,
        type="DNS_PROVIDER_DELETED",
        message=f"DNS credential '{name}' deleted",
        actor_id=actor_id,
        actor_type=actor_type,
        resource_type="dns_provider",
        resource_id=str(provider.id),
        data={"name": name},
        org_id=provider.org_id,
    )
    await audit_service.record(
        db,
        ctx,
        action="dns_provider.deleted",
        resource_type="dns_provider",
        resource_id=provider.id,
        metadata={"name": name},
        request=request,
    )


__all__ = [
    "MAX_CREDENTIAL_FIELDS",
    "MAX_CREDENTIAL_VALUE_LENGTH",
    "DnsCredentialUnavailable",
    "canonical_blob",
    "create_dns_provider",
    "credentials_for_use",
    "delete_dns_provider",
    "detail",
    "list_dns_providers",
    "normalize_credentials",
    "normalize_zone_allowlist",
    "provider_detail",
    "require_provider",
    "require_zone_allowed",
    "resolve_kind",
    "update_dns_provider",
    "verify_dns_provider",
    "zone_allows",
]
