"""Canonical domain/hostname handling — one pure function per question.

Every write path (API, worker, renderer) funnels through :func:`canonicalize_name`
so validation, uniqueness, verification and route coverage all compare the *same*
string. A second normalisation would be a second source of truth, and the
divergence would show up as a domain that verifies but cannot be routed.

The rules (domain-routing.md §6.2):

* lowercase; one trailing dot removed; IDNA/punycode applied to non-ASCII labels;
* labels 1-63 octets, total name ≤ 253 octets, labels alphanumeric with internal
  hyphens, never leading/trailing hyphens;
* the rightmost label (TLD) must not be all digits — an all-numeric name is an
  IPv4 literal, and ``1.2.3.4`` is never a domain;
* A/AAAA/other IP literals are rejected outright, IPv6 included;
* a wildcard is allowed only as the *leading* label (``*.example.com``) and only
  for Domains — it is never a valid route hostname;
* no substring/``endswith`` ownership tests: coverage is computed label-wise by
  :func:`hostname_is_covered`, which is the same function the API validates with.
"""

from __future__ import annotations

import ipaddress
import re

#: Longest name we accept. DNS's own limit for a fully qualified name.
MAX_NAME_LENGTH = 253
#: Longest single DNS label, in octets.
MAX_LABEL_LENGTH = 63
#: Longest a single rendered path may be.
MAX_PATH_LENGTH = 255

_LABEL_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")
#: Path allowlist for route prefixes. Deliberately conservative: no ``~``/``=``
#: (nginx match-type markers), no whitespace, quotes, ``;``, ``{``, ``}``, ``$``.
_PATH_RE = re.compile(r"^[A-Za-z0-9._\-/]*$")


class InvalidName(ValueError):
    """A domain or hostname that cannot be canonicalised.

    The message is user-facing and stable: it names the rule that failed and
    never echoes the whole input back, so it is safe in a 422 body.
    """

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _idna(fqdn: str) -> str:
    """Punycode-encode non-ASCII labels (IDNA2003 through the stdlib codec).

    Only the *labels* are converted, so the wildcard prefix survives. The codec
    raises ``UnicodeError`` for input it cannot encode; that is reported as a
    normal validation failure rather than escaping as a 500.
    """
    labels = fqdn.split(".")
    converted: list[str] = []
    for label in labels:
        if label.isascii():
            converted.append(label)
            continue
        try:
            converted.append(label.encode("idna").decode("ascii"))
        except UnicodeError:
            raise InvalidName(
                "DOMAIN_INVALID", "a label contains characters that cannot be encoded"
            ) from None
    return ".".join(converted)


def _check_labels(name: str, *, allow_wildcard: bool) -> tuple[str, list[str]]:
    """Validate the shape of an already-lowercased, punycode name."""
    wildcard = name.startswith("*.")
    if wildcard and not allow_wildcard:
        raise InvalidName("DOMAIN_INVALID", "a wildcard is not valid here")
    body = name[2:] if wildcard else name
    labels = body.split(".")
    if len(labels) < 2:
        raise InvalidName("DOMAIN_INVALID", "a domain needs at least two labels")
    if any(label == "*" for label in labels):
        raise InvalidName("DOMAIN_INVALID", "a wildcard is only allowed as the first label")
    for label in labels:
        if not label:
            raise InvalidName("DOMAIN_INVALID", "the name contains an empty label")
        if len(label.encode("ascii")) > MAX_LABEL_LENGTH:
            raise InvalidName("DOMAIN_INVALID", "a label is longer than 63 characters")
        if "*" in label:
            raise InvalidName("DOMAIN_INVALID", "a wildcard must be a label of its own")
        if not _LABEL_RE.match(label):
            raise InvalidName("DOMAIN_INVALID", "a label may only use letters, digits and hyphens")
    if labels[-1].isdigit():
        raise InvalidName("DOMAIN_INVALID", "the last label must not be all digits")
    return (body if not wildcard else name), labels


def _check_not_ip(value: str) -> None:
    candidate = value.strip("[]")
    try:
        ipaddress.ip_address(candidate)
    except ValueError:
        return
    raise InvalidName("DOMAIN_IS_IP", "an IP address is not a domain name")


def canonicalize_name(value: str, *, allow_wildcard: bool = False) -> str:
    """Return the canonical form of a domain (or route hostname).

    Raises :class:`InvalidName` for anything that is not a valid name under the
    rules above. This is the only entry point; callers must not pre-trim or
    pre-lowercase, because the checks here also cover the IP-literal and TLD
    cases that a naive normalisation would let through.
    """
    if not isinstance(value, str):
        raise InvalidName("DOMAIN_INVALID", "a domain name is required")
    name = value.strip().rstrip(".").strip()
    if not name:
        raise InvalidName("DOMAIN_INVALID", "a domain name is required")
    _check_not_ip(name)
    lowered = name.lower()
    try:
        encoded = _idna(lowered)
    except InvalidName:
        raise
    _check_labels(encoded, allow_wildcard=allow_wildcard)
    if len(encoded.encode("ascii")) > MAX_NAME_LENGTH:
        raise InvalidName("DOMAIN_INVALID", "the name is longer than 253 characters")
    # The label/character checks above run on the *encoded* form, so an IDNA name
    # that punycodes into something invalid fails here rather than at render time.
    return encoded


def apex_of(name: str) -> str:
    """The name a wildcard Domain is anchored at (``*.example.com`` → ``example.com``).

    Verification always targets the apex: the TXT record lives at
    ``_nexusops.<apex>`` even for a wildcard Domain.
    """
    return name[2:] if name.startswith("*.") else name


def verification_record_name(name: str) -> str:
    """The exact TXT owner name a user must publish at their provider."""
    return f"_nexusops.{apex_of(name)}"


def hostname_is_covered(hostname: str, domain_name: str) -> bool:
    """Whether *hostname* is inside the name space of *domain_name*.

    Coverage is exactly one label deep, mirroring the wildcard-SAN rule the
    certificate subsystem will use, so hostname coverage and future cert
    coverage cannot diverge:

    * an exact Domain covers itself and any one-label subdomain;
    * a wildcard Domain ``*.example.com`` covers exactly one-label subdomains
      (``api.example.com``), never a deeper name and never the apex itself;
    * everything else is rejected — comparisons are label-wise, never
      ``endswith``.
    """
    if not hostname or not domain_name:
        return False
    # The Domain's own name always covers itself — including ``*.example.com``
    # as a route hostname on a ``*.example.com`` Domain.
    if hostname == domain_name:
        return True
    wildcard_domain = domain_name.startswith("*.")
    if hostname.startswith("*.") and not wildcard_domain:
        # A wildcard route exists only on a wildcard Domain: it answers a name
        # space the Domain row itself never proved control of.
        return False
    body = apex_of(domain_name)
    raw = hostname[2:] if hostname.startswith("*.") else hostname
    if raw == body:
        # The apex itself is covered only by the Domain that *is* the apex. A
        # ``*.example.com`` row does not cover ``example.com``.
        return not wildcard_domain
    if not raw.endswith("." + body):
        return False
    # Exactly one additional label — no dots in the prefix.
    prefix = raw[: -(len(body) + 1)]
    return bool(prefix) and "." not in prefix


def is_valid_path(path: str) -> bool:
    """Whether *path* is an acceptable nginx location prefix (see §6.2)."""
    if not isinstance(path, str) or not path.startswith("/"):
        return False
    if len(path) > MAX_PATH_LENGTH:
        return False
    if "//" in path or ".." in path:
        return False
    return _PATH_RE.match(path) is not None


def canonicalize_path(path: str) -> str:
    """Validate and return *path*; ``/`` is the default."""
    candidate = (path or "/").strip()
    if not is_valid_path(candidate):
        raise InvalidName(
            "ROUTE_PATH_INVALID", "the path must start with '/' and use a safe charset"
        )
    return candidate
