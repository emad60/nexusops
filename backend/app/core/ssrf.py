"""SSRF guard applied to every operator-supplied outbound URL.

Monitors and webhook channels make the server itself issue requests. Without
this guard an authenticated user could point them at cloud metadata endpoints,
localhost admin ports or internal RFC1918 services. Validation therefore:

  * restricts the scheme to ``http``/``https``,
  * rejects userinfo embedded in the authority (``user:pass@host``),
  * requires a resolvable hostname whose **every** resolved address is public,
  * rejects unresolvable hosts (fail closed).

Known limitation — DNS rebinding TOCTOU: resolution happens once here and the
actual request is issued later by a different resolver round-trip, so an
attacker controlling DNS could return a public address during validation and a
private one at request time. Full mitigation requires pinning the validated IP
at connect time (custom transport), which is tracked separately. The window is
narrow and exploitation requires attacker-controlled authoritative DNS.
"""

from __future__ import annotations

import asyncio
import ipaddress
import socket
import urllib.parse

from app.core.config import get_settings
from app.core.errors import BadRequest, UnprocessableEntity
from app.core.logging import get_logger

ALLOWED_SCHEMES: frozenset[str] = frozenset({"http", "https"})

#: Generic client-facing reason. Details go to logs, never to the response,
#: so attackers cannot probe which exact rule tripped.
_BLOCK_MESSAGE = "URL is not allowed"

_SIMULATION_SCHEME = "sim"

log = get_logger("nexusops.ssrf")


class UrlRejected(ValueError):
    """Internal signal: a specific SSRF rule matched (never shown to clients)."""


def _raise_block() -> None:
    raise UnprocessableEntity(_BLOCK_MESSAGE, code="SSRF_BLOCKED")


def _is_forbidden_address(addr: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """True when *addr* points into a network the server must never contact.

    Everything that is not globally routable is refused: RFC1918, loopback,
    link-local (including the 169.254.169.254 cloud-metadata endpoint), ULA,
    benchmark/documentation ranges and CGNAT 100.64.0.0/10 all carry
    ``is_global == False``. Multicast ranges are flagged "global" by
    :mod:`ipaddress` yet are never legitimate probe targets, so multicast
    remains an explicit check.
    """
    return not addr.is_global or addr.is_multicast


def _validate_syntax(parsed: urllib.parse.ParseResult) -> None:
    if parsed.scheme.lower() not in ALLOWED_SCHEMES:
        raise UrlRejected(f"scheme not permitted: {parsed.scheme!r}")
    if "@" in parsed.netloc:
        raise UrlRejected("userinfo embedded in authority")
    hostname = parsed.hostname
    if not hostname:
        raise UrlRejected("empty hostname")
    try:
        port = parsed.port
    except ValueError as exc:
        raise UrlRejected("invalid port") from exc
    if port is not None and not 1 <= port <= 65535:
        raise UrlRejected(f"port out of range: {port}")
    if parsed.username is not None or parsed.password is not None:
        raise UrlRejected("credentials embedded in URL")


def _validate_resolution(hostname: str) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    """Resolve *hostname* (AF_UNSPEC) and refuse any non-public answer."""
    try:
        infos = socket.getaddrinfo(
            hostname,
            None,
            family=socket.AF_UNSPEC,
            type=socket.SOCK_STREAM,
        )
    except OSError as exc:
        raise UrlRejected(f"dns resolution failed: {exc.__class__.__name__}") from exc

    addresses: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = []
    seen: set[str] = set()
    for info in infos:
        raw = info[4][0]
        try:
            addr = ipaddress.ip_address(raw)
        except ValueError:
            continue
        if str(addr) in seen:
            continue
        seen.add(str(addr))
        addresses.append(addr)

    if not addresses:
        raise UrlRejected("no addresses resolved")
    bad = [str(a) for a in addresses if _is_forbidden_address(a)]
    if bad:
        raise UrlRejected(f"non-public address: {bad[0]}")
    return addresses


def assert_safe_url(url: str) -> urllib.parse.ParseResult:
    """Validate *url* for outbound requests; return the parsed URL or raise 422.

    Raises :class:`UnprocessableEntity` with code ``SSRF_BLOCKED`` and a generic
    message when any rule fails. When ``settings.allow_private_targets`` is
    enabled (development/simulation mode) the private-address and resolution
    checks are skipped — syntax checks still apply.
    """
    try:
        parsed = urllib.parse.urlparse(url)
        _validate_syntax(parsed)
        if not get_settings().allow_private_targets and parsed.hostname:
            _validate_resolution(parsed.hostname)
    except UrlRejected as exc:
        log.warning("url_blocked", reason=str(exc))
        _raise_block()
    except Exception as exc:  # malformed URL, NUL bytes, … — fail closed
        log.warning("url_blocked", reason=exc.__class__.__name__)
        _raise_block()
    return parsed


async def assert_safe_url_async(url: str) -> urllib.parse.ParseResult:
    """Async wrapper around :func:`assert_safe_url`; DNS runs off the loop."""
    return await asyncio.to_thread(assert_safe_url, url)


def assert_safe_tcp_endpoint(url: str) -> None:
    """Validate a ``tcp://`` docker host endpoint for outbound connection.

    Docker ``tcp://`` endpoints never went through :func:`assert_safe_url`
    (whose scheme allow-list covers http/https only), yet they make the server
    open raw connections to an arbitrary host:port — usable as an internal
    probing oracle in strict mode. This applies the same private-address
    rules to the authority component. ``unix://`` endpoints are local sockets
    and exempt; callers must not invoke this for them.
    """
    blocked_reason: str
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme.lower() != "tcp":
            raise UrlRejected(f"scheme not permitted: {parsed.scheme!r}")
        hostname = parsed.hostname
        if not hostname:
            raise UrlRejected("empty hostname")
        try:
            port = parsed.port
        except ValueError as exc:
            raise UrlRejected("invalid port") from exc
        if port is None:
            raise UrlRejected("missing port")
        if not 1 <= port <= 65535:
            raise UrlRejected(f"port out of range: {port}")
        if "@" in parsed.netloc or parsed.username is not None or parsed.password is not None:
            raise UrlRejected("credentials embedded in URL")
        if not get_settings().allow_private_targets:
            _validate_resolution(hostname)
        return
    except UrlRejected as exc:
        blocked_reason = str(exc)
    except Exception as exc:  # malformed URL, NUL bytes, … — fail closed
        blocked_reason = exc.__class__.__name__
    log.warning("tcp_endpoint_blocked", reason=blocked_reason)
    raise BadRequest(_BLOCK_MESSAGE, code="ENDPOINT_BLOCKED") from None


def is_simulation_url(url: str) -> bool:
    """True when *url* targets the built-in simulated checker (``sim://``)."""
    return urllib.parse.urlparse(url).scheme.lower() == _SIMULATION_SCHEME


__all__ = [
    "ALLOWED_SCHEMES",
    "UrlRejected",
    "assert_safe_tcp_endpoint",
    "assert_safe_url",
    "assert_safe_url_async",
    "is_simulation_url",
]
