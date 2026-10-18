"""Cloudflare: credential verification, and the DNS-01 record operations.

The **credential** half makes two read-only calls to establish whether a stored
token is usable and what it can reach:

1. ``GET /user/tokens/verify`` — is the token live? Cloudflare answers
   ``result.status == "active"`` for a valid token and 401/403 otherwise.
2. ``GET /zones`` — which zones can this token see? A token scoped to one zone
   (which is what the design requires: ``Zone:DNS:Edit`` on a specific zone, never
   a global key — §5.3) lists exactly that zone, so the response is also a check
   against ``zone_allowlist``: an allowlisted zone the token cannot see is
   reported as a warning, not a failure, because the operator may intend to grant
   it later.

The **record** half is the only code in this platform that modifies a customer's
DNS, and it is written to be recoverable rather than merely working:

* :meth:`CloudflareDnsProvider.resolve_zone` asks the customer's own delegation
  which zone holds a name (deepest suffix first), never a public-suffix guess — the
  zone a record belongs to is a fact about the account, not a property of the
  string, and writing into the parent zone of a delegated subdomain is silent
  data loss;
* :meth:`~CloudflareDnsProvider.create_txt` returns the provider's own record
  reference and treats a lost response or a 5xx as **ambiguous**, never as a plain
  retry, because retrying a write whose outcome is unknown is how a zone ends up
  with two challenge records and no way to tell which one this platform made;
* :meth:`~CloudflareDnsProvider.find_txt` is the reconciliation primitive — it
  matches by record name **and value**, so recovery can adopt the record it was
  trying to create, and can never touch a customer's unrelated TXT record at the
  same name;
* :meth:`~CloudflareDnsProvider.delete_txt` deletes by that reference, one record
  at a time, and reports "could not confirm" distinctly from "gone" — cleanup is
  not allowed to claim success it did not observe.

The token is never logged, never echoed into a result and never included in an
error string. Failures carry the HTTP status and Cloudflare's own error codes,
which describe the request rather than the credential.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import quote

import httpx

from app.core.logging import get_logger
from app.providers.dns import (
    CredentialCheck,
    DnsCredentialError,
    DnsProviderError,
    DnsProviderRejected,
    DnsProviderUnavailable,
    DnsWriteAmbiguous,
    TxtRecord,
    ZoneRef,
    ZoneResolution,
)

log = get_logger("nexusops.dns.cloudflare")

#: The public API base. Overridable for a local fake in tests, which is why it is
#: an instance attribute rather than a module constant read at call time.
API_BASE = "https://api.cloudflare.com/client/v4"

#: Per-request timeout. Verification happens on save (and before use), so it must
#: fail in bounded time rather than hold a request open on a hung provider.
REQUEST_TIMEOUT_SECONDS = 10.0

#: How many zones one verification lists. A bound, not a policy: it keeps the
#: stored scope summary (and the warning list derived from it) from growing with a
#: customer's account size.
MAX_ZONES_LISTED = 50

#: Bound on a stored/reported error string, matching the column.
MAX_ERROR_LENGTH = 500


class CloudflareDnsProvider:
    """Cloudflare credential verification over the public API."""

    name = "cloudflare"
    #: Annotated as variadic so the instance satisfies the protocol: a bare tuple
    #: literal infers ``tuple[str]``, which is a one-element tuple, not "any number".
    required_fields: tuple[str, ...] = ("api_token",)

    def __init__(self, *, base_url: str = API_BASE) -> None:
        self.base_url = base_url.rstrip("/")

    def _token(self, credentials: Mapping[str, str]) -> str:
        token = (credentials.get("api_token") or "").strip()
        if not token:
            raise DnsCredentialError(
                "a Cloudflare credential needs a non-empty api_token",
            )
        return token

    @staticmethod
    def _error_summary(response: httpx.Response) -> str:
        """A bounded, credential-free description of a failed call."""
        codes: list[str] = []
        try:
            payload = response.json()
        except ValueError:
            payload = None
        if isinstance(payload, dict):
            for entry in payload.get("errors") or []:
                if isinstance(entry, dict) and entry.get("code") is not None:
                    # Code only: messages are free text from a third party and
                    # nothing here needs them to be actionable.
                    codes.append(str(entry["code"]))
        detail = f" (errors: {', '.join(codes[:5])})" if codes else ""
        return f"Cloudflare returned HTTP {response.status_code}{detail}"[:MAX_ERROR_LENGTH]

    async def verify_creds(self, credentials: Mapping[str, str]) -> CredentialCheck:
        """Verify the token and list the zones it can reach. Never raises for a
        provider-side failure — that is a recorded result, not an exception."""
        token = self._token(credentials)
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=REQUEST_TIMEOUT_SECONDS,
                headers=headers,
                follow_redirects=False,
            ) as client:
                verify = await client.get("/user/tokens/verify")
                if verify.status_code != httpx.codes.OK:
                    return CredentialCheck(ok=False, error=self._error_summary(verify))
                body = verify.json() if verify.content else {}
                status = str((body.get("result") or {}).get("status") or "")
                if status != "active":
                    return CredentialCheck(
                        ok=False,
                        error=f"the Cloudflare token is not active (status {status or 'unknown'})"[
                            :MAX_ERROR_LENGTH
                        ],
                    )
                zones_response = await client.get("/zones", params={"per_page": MAX_ZONES_LISTED})
                if zones_response.status_code != httpx.codes.OK:
                    return CredentialCheck(ok=False, error=self._error_summary(zones_response))
                listing = zones_response.json() if zones_response.content else {}
        except httpx.HTTPError as exc:
            # A transport failure is a verification failure with a bounded,
            # credential-free reason; httpx messages carry the URL host, not the
            # Authorization header.
            return CredentialCheck(
                ok=False,
                error=f"could not reach Cloudflare: {type(exc).__name__}"[:MAX_ERROR_LENGTH],
            )

        entries: list[dict[str, Any]] = [
            entry for entry in (listing.get("result") or []) if isinstance(entry, dict)
        ]
        # ``zones`` is id/name **paired**, and that pairing is what the issuance path
        # resolves a challenge name against. ``zone_ids``/``zone_names`` are kept for
        # the summary and the allowlist warning, but they are two independent lists —
        # names sorted, ids in API order — so nothing may zip them. A record written
        # in the wrong zone is unrecoverable, so the pairs are the authority.
        zones = [
            {"id": str(entry["id"]), "name": str(entry["name"]).lower().rstrip(".")}
            for entry in entries
            if entry.get("id") and entry.get("name")
        ]
        zone_ids = [zone["id"] for zone in zones]
        zone_names = sorted(zone["name"] for zone in zones)
        log.info("dns_credential_verified", kind=self.name, zones=len(zone_names))
        return CredentialCheck(
            ok=True,
            scopes={
                "zones": zones,
                "zone_ids": zone_ids,
                "zone_names": zone_names,
                "token_status": status,
            },
        )

    # --- The record operations (Phase 5.3) ---------------------------------
    #
    # ``MAX_ZONE_CANDIDATES``, ``MAX_RECORDS_LISTED`` and ``_rejection()`` are module
    # globals declared *below* this class, together with ``_zone_candidates()``. That
    # is deliberate rather than untidy: they are shared by the credential path above
    # (``_error_summary`` is ``_rejection``'s formatter) and referenced only at call
    # time, so keeping the class body contiguous costs nothing and avoids a second
    # class with the same name or a mixin that has to be defined first.

    async def resolve_zone(self, credentials: Mapping[str, str], name: str) -> ZoneResolution:
        """Find the zone that actually holds *name*.

        Walking suffixes deepest-first and asking the API for an exact zone match is
        deliberate rather than clever: this platform cannot derive the zone from the
        record name (that needs a public-suffix list, which is a guess that changes
        over time), and the customer's own delegation is the authority. A delegated
        subdomain — ``shop.example.com`` as its own zone — is therefore found where a
        suffix-list guess would have picked the parent and written the record in the
        wrong zone.

        Because ``GET /zones?name=…`` returns only zones this token can access, the
        lookup also enforces the token's own scope: a name in a zone the credential
        cannot see resolves to nothing here rather than to a zone it may not write in.
        """
        token = self._token(credentials)
        candidate = self._canonical_name(name)
        candidates = _zone_candidates(candidate)
        if not candidates:
            return ZoneResolution(zone=None, reason="the record name has no delegable zone")
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=REQUEST_TIMEOUT_SECONDS,
                headers=headers,
                follow_redirects=False,
            ) as client:
                for suffix in candidates:
                    response = await client.get("/zones", params={"name": suffix})
                    if response.status_code != httpx.codes.OK:
                        raise _rejection(response)
                    payload = response.json() if response.content else {}
                    for entry in payload.get("result") or []:
                        if not isinstance(entry, dict):
                            continue
                        zone_name = str(entry.get("name") or "").lower().rstrip(".")
                        zone_id = str(entry.get("id") or "")
                        if zone_id and zone_name == suffix:
                            return ZoneResolution(zone=ZoneRef(id=zone_id, name=zone_name))
        except httpx.HTTPError as exc:
            raise DnsProviderUnavailable(
                f"could not reach Cloudflare: {type(exc).__name__}",
                code="DNS_PROVIDER_UNREACHABLE",
            ) from None
        return ZoneResolution(
            zone=None,
            reason=(
                f"no zone this credential can access holds '{candidate}' — check that "
                "the domain is on Cloudflare and that the token is scoped to its zone"
            ),
        )

    async def create_txt(
        self,
        credentials: Mapping[str, str],
        *,
        zone_id: str,
        name: str,
        value: str,
        ttl: int,
    ) -> TxtRecord:
        """Create one TXT record. Never creates a second one for an unknown outcome.

        The failure that matters: if the POST may have been applied but its response
        never arrived, this raises :class:`DnsWriteAmbiguous` *carrying the record's
        coordinates* so the caller can look for exactly this value before deciding to
        create anything again. A blind retry here is how a zone ends up with two
        challenge records and no way to tell which one this platform owns.
        """
        token = self._token(credentials)
        record_name = self._canonical_name(name)
        body = {"type": "TXT", "name": record_name, "content": value, "ttl": int(ttl)}
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=REQUEST_TIMEOUT_SECONDS,
                headers=headers,
                follow_redirects=False,
            ) as client:
                response = await client.post(
                    f"/zones/{quote(zone_id, safe='')}/dns_records", json=body
                )
        except httpx.HTTPError as exc:
            raise self._ambiguous(exc, record_name, value) from None
        if response.status_code >= 500:
            # A 5xx may have committed the write before failing. Treated as ambiguous
            # rather than retryable, because the alternative is a duplicate record.
            raise self._ambiguous(_Ambiguous(), record_name, value)
        if response.status_code not in (httpx.codes.OK, httpx.codes.CREATED):
            # 4xx and 429 are answers: the request was refused (or throttled) and the
            # zone is unchanged, so this is classifiable rather than ambiguous.
            raise _rejection(response)
        payload = response.json() if response.content else {}
        result = payload.get("result") if isinstance(payload, dict) else None
        record_id = str((result or {}).get("id") or "") if isinstance(result, dict) else ""
        if not record_id:
            # The write very probably happened and we have no handle on it: the exact
            # situation recovery exists for, and *not* a silent success.
            raise self._ambiguous(_Ambiguous(), record_name, value)
        stored = str((result or {}).get("name") or record_name)
        log.info("dns_txt_created", zone_id_present=True, name=record_name)
        return TxtRecord(id=record_id, zone_id=zone_id, name=stored, value=value)

    async def find_txt(
        self, credentials: Mapping[str, str], *, zone_id: str, name: str, value: str
    ) -> tuple[TxtRecord, ...]:
        """Records at *name* whose value **equals** *value*.

        The value filter is what makes this safe to act on: a customer's unrelated TXT
        record at the same owner name (a SPF fragment, a verification token of their
        own) can never be adopted or deleted through this method.
        """
        token = self._token(credentials)
        record_name = self._canonical_name(name)
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=REQUEST_TIMEOUT_SECONDS,
                headers=headers,
                follow_redirects=False,
            ) as client:
                response = await client.get(
                    f"/zones/{quote(zone_id, safe='')}/dns_records",
                    params={
                        "type": "TXT",
                        "name": record_name,
                        "per_page": MAX_RECORDS_LISTED,
                    },
                )
        except httpx.HTTPError as exc:
            raise DnsProviderUnavailable(
                f"could not reach Cloudflare: {type(exc).__name__}",
                code="DNS_PROVIDER_UNREACHABLE",
            ) from None
        if response.status_code != httpx.codes.OK:
            raise _rejection(response)
        payload = response.json() if response.content else {}
        found: list[TxtRecord] = []
        for entry in payload.get("result") or []:
            if not isinstance(entry, dict) or entry.get("type") != "TXT":
                continue
            content = str(entry.get("content") or "")
            record_id = str(entry.get("id") or "")
            if record_id and content == value:
                found.append(
                    TxtRecord(
                        id=record_id,
                        zone_id=zone_id,
                        name=str(entry.get("name") or record_name),
                        value=content,
                    )
                )
        return tuple(found)

    async def delete_txt(
        self, credentials: Mapping[str, str], *, zone_id: str, record_id: str
    ) -> bool:
        """Delete exactly one record, by the reference its creation returned.

        ``True`` covers both "deleted" and "already gone" (Cloudflare answers 404 for
        a record that is not there): both mean the record is not in the zone any more,
        and treating the second as failure would make cleanup retry a record that no
        longer exists. ``False`` is reserved for the case where the *provider* could
        not tell us — which the caller records as unresolved rather than as done.
        """
        token = self._token(credentials)
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                timeout=REQUEST_TIMEOUT_SECONDS,
                headers=headers,
                follow_redirects=False,
            ) as client:
                response = await client.delete(
                    f"/zones/{quote(zone_id, safe='')}/dns_records/{quote(record_id, safe='')}"
                )
        except httpx.HTTPError as exc:
            # Unresolved, not failed: the record may still be there and the caller must
            # not report cleanup as complete. Recording it as an exception would lose
            # the distinction between "could not confirm" and "confirmed still there".
            log.warning("dns_txt_delete_unconfirmed", error=type(exc).__name__)
            return False
        if response.status_code in (httpx.codes.OK, httpx.codes.NOT_FOUND):
            return True
        if response.status_code >= 500 or response.status_code == httpx.codes.TOO_MANY_REQUESTS:
            log.warning("dns_txt_delete_unconfirmed", status=response.status_code)
            return False
        raise _rejection(response)

    # --- helpers -----------------------------------------------------------

    @staticmethod
    def _canonical_name(name: str) -> str:
        """The owner name as the API expects it: lower-case, no trailing dot.

        Unlike a *domain identifier* this is not validated against the identifier
        rules: an ACME challenge owner legitimately starts with ``_acme-challenge``,
        which is not a hostname label the platform would accept for a certificate.
        """
        candidate = (name or "").strip().rstrip(".").lower()
        if not candidate or len(candidate) > 253 or ".." in candidate:
            raise DnsProviderRejected(
                "the DNS record name is not usable", code="DNS_RECORD_NAME_INVALID"
            )
        return candidate

    @staticmethod
    def _ambiguous(cause: BaseException, name: str, value: str) -> DnsWriteAmbiguous:
        return DnsWriteAmbiguous(
            "Cloudflare did not confirm the TXT record creation, so the record may or "
            "may not exist; the zone must be re-read before deciding to create it again",
            code="DNS_WRITE_AMBIGUOUS",
            detail=type(cause).__name__,
            name=name,
            value=value,
        )


# --- Module-level helpers shared by both halves --------------------------------

#: How many suffixes of a record name are tried when resolving its zone. The walk is
#: deepest-first and stops at the first zone the token can see, so this bounds a
#: pathological name (many labels) rather than a normal one.
MAX_ZONE_CANDIDATES = 6

#: How many TXT records one lookup considers. A bound, not a policy: a zone may hold
#: many TXT records at one name, and this keeps a lookup's response bounded.
MAX_RECORDS_LISTED = 100


def _rejection(response: httpx.Response) -> DnsProviderError:
    """Classify a failed Cloudflare response: rejected by us, or unavailable.

    4xx is the request's fault (a revoked token, a missing permission, a zone the
    token cannot see, a malformed record) and retrying cannot change it; 429 is the
    service asking us to slow down and 5xx is the service failing — both retryable.
    The message carries the status and Cloudflare's error codes only: never the
    token, never the free-text message, never the request body.
    """
    summary = CloudflareDnsProvider._error_summary(response)
    if response.status_code == httpx.codes.TOO_MANY_REQUESTS or response.status_code >= 500:
        return DnsProviderUnavailable(summary, code="DNS_PROVIDER_UNAVAILABLE")
    return DnsProviderRejected(
        summary,
        code=(
            "DNS_CREDENTIAL_REJECTED"
            if response.status_code in (httpx.codes.UNAUTHORIZED, httpx.codes.FORBIDDEN)
            else "DNS_PROVIDER_REJECTED"
        ),
    )


def _zone_candidates(name: str, *, limit: int = MAX_ZONE_CANDIDATES) -> list[str]:
    """Suffixes of *name* to try as zones, deepest first, never a bare TLD.

    ``_acme-challenge.www.example.com`` → ``_acme-challenge.www.example.com``,
    ``www.example.com``, ``example.com``: a challenge record's own owner name is tried
    first because a customer may legitimately delegate ``_acme-challenge`` to a
    validation service, in which case that *is* the zone that holds it.
    """
    labels = [label for label in name.split(".") if label]
    candidates: list[str] = []
    for start in range(max(len(labels) - 1, 0)):
        suffix = ".".join(labels[start:])
        if len(suffix.split(".")) >= 2:
            candidates.append(suffix)
        if len(candidates) >= limit:
            break
    return candidates


class _Ambiguous(Exception):
    """Placeholder cause for an ambiguous outcome that has no exception of its own.

    Exists so :meth:`CloudflareDnsProvider._ambiguous` has one signature for both the
    transport failure (a real exception) and the unreadable success (there is none).
    """


__all__ = [
    "API_BASE",
    "MAX_ERROR_LENGTH",
    "MAX_RECORDS_LISTED",
    "MAX_ZONES_LISTED",
    "MAX_ZONE_CANDIDATES",
    "REQUEST_TIMEOUT_SECONDS",
    "CloudflareDnsProvider",
]
