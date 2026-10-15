"""Cloudflare: credential verification only (Phase 5.2.2).

Two read-only calls establish whether a stored token is usable and what it can
reach:

1. ``GET /user/tokens/verify`` — is the token live? Cloudflare answers
   ``result.status == "active"`` for a valid token and 401/403 otherwise.
2. ``GET /zones`` — which zones can this token see? A token scoped to one zone
   (which is what the design requires: ``Zone:DNS:Edit`` on a specific zone, never
   a global key — §5.3) lists exactly that zone, so the response is also a check
   against ``zone_allowlist``: an allowlisted zone the token cannot see is
   reported as a warning, not a failure, because the operator may intend to grant
   it later.

Nothing here writes to the customer's DNS. ``create_txt``/``delete_txt`` and the
propagation check are the issuance slice's, and they are intentionally absent —
this module cannot modify a zone even if it wanted to, which is the point of
splitting them.

The token is never logged, never echoed into a result and never included in an
error string. Failures carry the HTTP status and Cloudflare's own error codes,
which describe the request rather than the credential.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from app.core.logging import get_logger
from app.providers.dns import CredentialCheck, DnsCredentialError

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
                zones = await client.get("/zones", params={"per_page": MAX_ZONES_LISTED})
                if zones.status_code != httpx.codes.OK:
                    return CredentialCheck(ok=False, error=self._error_summary(zones))
                listing = zones.json() if zones.content else {}
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
        zone_ids = [str(entry["id"]) for entry in entries if entry.get("id")]
        zone_names = sorted(str(entry["name"]).lower() for entry in entries if entry.get("name"))
        log.info("dns_credential_verified", kind=self.name, zones=len(zone_names))
        return CredentialCheck(
            ok=True,
            scopes={
                "zone_ids": zone_ids,
                "zone_names": zone_names,
                "token_status": status,
            },
        )


__all__ = [
    "API_BASE",
    "MAX_ERROR_LENGTH",
    "MAX_ZONES_LISTED",
    "REQUEST_TIMEOUT_SECONDS",
    "CloudflareDnsProvider",
]
