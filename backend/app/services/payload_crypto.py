"""Payload encryption under the organization DEK (Phase 5.2.2).

Three Phase-5 tables store a secret that the control plane must be able to read
back: ``certificate_generations.key_ciphertext``/``chain_ciphertext``,
``dns_providers.credentials_ciphertext`` and ``acme_accounts.key_ciphertext``. All
three encrypt through here, under the **organization DEK** the envelope service
unwraps for the duration of one operation (``app/services/dek_envelope.py``), so
the key that protects them never reaches a module global and is dropped when the
write ends.

Why a module of its own rather than calls to ``core.security.encrypt_str``: that
function is the *single-key* path the secret store still uses, and Phase 5
deliberately does not migrate it (§6.4). Keeping the two apart is what makes
"a DEK rotation re-encrypts Phase-5 rows and nothing else" true by construction —
the two envelopes share no code path, no key source and no column.

**The stored value is bound to its context.** A ciphertext belongs to exactly one
``(organization, purpose, record, DEK generation)`` tuple, and the stored value
says so in two places:

* an outer header, ``nxp1:<org_id>:<purpose>:<record_id>:<deke_id>``, so a value
  that was moved to another row, another purpose or another organization is
  rejected **before** any decryption happens — the cheap, non-cryptographic check
  a database mistake deserves;
* the same header again inside the Fernet plaintext, as an authenticated framing
  line, so the binding is covered by the Fernet HMAC. An attacker who can write to
  the database cannot re-label a ciphertext they cannot re-key, because the
  authenticated copy would disagree.

Honest limitation, stated rather than implied: Fernet has no associated-data input
(the design's chosen envelope, §6.2 — AES-GCM with AAD was the alternative and was
not adopted). The in-plaintext header therefore catches a forged binding only *after*
the token authenticates, not before, and this module is the only place that
decision is made. Nothing is weakened by it here — a mismatch raises, and no
plaintext escapes a rejection — but it is a property of Fernet, not a guarantee
this module adds.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from hmac import compare_digest
from typing import Final
from uuid import UUID

from cryptography.fernet import Fernet, InvalidToken

#: Format tag of the stored value, versioned so a future change is parseable
#: rather than guessed at. ``nxp1`` = "nexusops payload, version 1".
PAYLOAD_FORMAT: Final = "nxp1"

#: The purposes a payload may be encrypted for. A closed set on purpose: the
#: purpose is part of the binding, so an unlisted purpose is a programming error
#: (or an attacker probing for one), not a value to accept and store.
PURPOSE_CERTIFICATE_KEY: Final = "certificate.key"
PURPOSE_CERTIFICATE_CHAIN: Final = "certificate.chain"
PURPOSE_DNS_CREDENTIALS: Final = "dns.credentials"
PURPOSE_ACME_ACCOUNT_KEY: Final = "acme.account_key"

PAYLOAD_PURPOSES: Final[frozenset[str]] = frozenset(
    {
        PURPOSE_CERTIFICATE_KEY,
        PURPOSE_CERTIFICATE_CHAIN,
        PURPOSE_DNS_CREDENTIALS,
        PURPOSE_ACME_ACCOUNT_KEY,
    }
)

#: Separator between the header fields. None of them can contain it: two are
#: UUIDs, one is a member of the closed set above and one is a positive integer.
_SEPARATOR: Final = ":"

#: Separator between the authenticated framing line and the payload inside the
#: Fernet plaintext. A payload is arbitrary bytes, so the frame is a length-free
#: *first* line and everything after the first newline is the payload verbatim.
_FRAME: Final = b"\n"


class PayloadError(RuntimeError):
    """Base class for a payload that could not be encrypted or trusted."""


class PayloadEnvelopeError(PayloadError):
    """The stored value is not a well-formed payload envelope.

    Raised for an unknown format tag, a truncated value, a non-numeric generation
    or a UUID that does not parse — never by falling back to "treat it as the
    legacy shape".
    """


class PayloadContextMismatch(PayloadError):
    """The stored value belongs to a different context than the one presented.

    A moved ciphertext, a re-used row id, a purpose swap or a DEK-generation
    mismatch. This is the error a *cross-record* or *cross-tenant* read produces,
    and it is distinct from a decryption failure so an operator can tell "the
    wrong key was configured" from "the wrong row was read".
    """


class PayloadDecryptionError(PayloadError):
    """Fernet refused the token: the key is wrong or the bytes were altered.

    Distinct from :class:`PayloadContextMismatch` (§6.5): a generation whose
    material cannot be decrypted is marked failed and re-issued, and it must never
    be served with a broken payload.
    """


@dataclass(frozen=True, slots=True)
class PayloadContext:
    """What a ciphertext belongs to: organization, purpose, record and DEK generation.

    All four are authenticated, so the context is not a label placed *next to*
    key material — it is part of what the MAC covers.
    """

    org_id: UUID
    purpose: str
    record_id: UUID
    deke_id: int

    def __post_init__(self) -> None:
        if self.purpose not in PAYLOAD_PURPOSES:
            raise PayloadEnvelopeError(
                f"unknown payload purpose {self.purpose!r}; expected one of "
                f"{sorted(PAYLOAD_PURPOSES)}"
            )
        if self.deke_id < 1:
            # 0 means "this organization has no DEK yet" at the envelope level, so
            # it can never be the generation that encrypted anything.
            raise PayloadEnvelopeError(
                f"deke_id must be a real DEK generation (>= 1), got {self.deke_id}"
            )

    def header(self) -> str:
        """The canonical header string, used both outside and inside the token."""
        return _SEPARATOR.join(
            (
                PAYLOAD_FORMAT,
                str(self.org_id),
                self.purpose,
                str(self.record_id),
                str(self.deke_id),
            )
        )


def _parse_header(header: str) -> tuple[str, UUID, str, UUID, int]:
    parts = header.split(_SEPARATOR)
    if len(parts) != 5:
        raise PayloadEnvelopeError(f"malformed payload header {header!r}")
    tag, org_id, purpose, record_id, deke_id = parts
    if tag != PAYLOAD_FORMAT:
        raise PayloadEnvelopeError(
            f"unknown payload format tag {tag!r}; expected {PAYLOAD_FORMAT!r}"
        )
    try:
        return tag, UUID(org_id), purpose, UUID(record_id), int(deke_id)
    except ValueError as exc:
        raise PayloadEnvelopeError(f"malformed payload header {header!r}") from exc


def _split(stored: str) -> tuple[str, str]:
    """Split the stored value into its outer header and the Fernet token."""
    if not isinstance(stored, str) or not stored:
        raise PayloadEnvelopeError("empty payload value")
    # The token is urlsafe base64 and contains no ':', so the header is everything
    # before the fifth separator and the token is the remainder — which keeps a
    # future header field from silently truncating the ciphertext.
    header, found, token = stored.rpartition(_SEPARATOR)
    if not found or not token:
        raise PayloadEnvelopeError("stored payload has no ciphertext")
    _parse_header(header)
    return header, token


def _require_context(stored_header: str, context: PayloadContext) -> None:
    """Compare the presented context with the header, in constant time.

    Constant-time because the comparison is between an attacker-influenced stored
    value and a caller-supplied expectation; the cost is one small memcmp and the
    alternative is a comparison whose timing depends on how much of the binding
    matches.
    """
    if not compare_digest(stored_header, context.header()):
        raise PayloadContextMismatch(
            "the stored payload was encrypted for a different organization, purpose, "
            "record or DEK generation"
        )


def fingerprint(payload: bytes, *, kind: str) -> str:
    """A stable, non-reversible handle for a secret, for display and change detection.

    Domain-separated by *kind* so the same bytes stored as two different things do
    not share a fingerprint. This is **never** a verification oracle: it is not
    compared against attacker-supplied input to conclude that a secret is correct,
    and the value it is computed over never leaves the caller.
    """
    if not kind:
        raise PayloadError("a fingerprint needs a kind")
    return sha256(kind.encode() + b"\x00" + payload).hexdigest()


def encrypt(fernet: Fernet, context: PayloadContext, payload: bytes) -> str:
    """Encrypt *payload* for *context* and return the storable value.

    The plaintext is framed as ``<header>\\n<payload>``, so the context is covered
    by the Fernet MAC and a re-labelled ciphertext is refused rather than decrypted
    into the wrong row.
    """
    body = context.header().encode() + _FRAME + payload
    token = fernet.encrypt(body).decode()
    return f"{context.header()}{_SEPARATOR}{token}"


def decrypt(fernet: Fernet, context: PayloadContext, stored: str) -> bytes:
    """Return the payload *stored* holds for *context*, or raise.

    Fails closed in three distinct, named ways: a malformed envelope, a header that
    does not match the presented context (checked before any decryption), and a
    token Fernet refuses. There is no code path that returns partially trusted
    bytes.
    """
    stored_header, token = _split(stored)
    _require_context(stored_header, context)
    try:
        body = fernet.decrypt(token.encode())
    except InvalidToken as exc:
        raise PayloadDecryptionError(
            "the stored payload could not be decrypted: the organization DEK does not "
            "match the one that encrypted it, or the ciphertext was altered"
        ) from exc
    inner_header, newline, payload = body.partition(_FRAME)
    if not newline:  # pragma: no cover - only a non-conforming writer can produce this
        raise PayloadEnvelopeError("the decrypted payload is missing its authenticated header")
    # The authenticated copy is authoritative: if it disagrees with the outer
    # header, the value was re-labelled by something that could write the column
    # but could not re-key the ciphertext.
    if not compare_digest(inner_header.decode(errors="replace"), stored_header):
        raise PayloadContextMismatch(
            "the stored payload's authenticated binding disagrees with its header; "
            "the value was rewritten without being re-encrypted"
        )
    return payload


def decrypt_str(fernet: Fernet, context: PayloadContext, stored: str) -> str:
    """:func:`decrypt` for the UTF-8 payloads (credentials, keys, chains)."""
    try:
        return decrypt(fernet, context, stored).decode()
    except UnicodeDecodeError as exc:
        raise PayloadDecryptionError("the decrypted payload is not valid UTF-8") from exc


__all__ = [
    "PAYLOAD_FORMAT",
    "PAYLOAD_PURPOSES",
    "PURPOSE_ACME_ACCOUNT_KEY",
    "PURPOSE_CERTIFICATE_CHAIN",
    "PURPOSE_CERTIFICATE_KEY",
    "PURPOSE_DNS_CREDENTIALS",
    "PayloadContext",
    "PayloadContextMismatch",
    "PayloadDecryptionError",
    "PayloadEnvelopeError",
    "PayloadError",
    "decrypt",
    "decrypt_str",
    "encrypt",
    "fingerprint",
]
