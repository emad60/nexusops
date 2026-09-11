"""Unit tests for the SSRF guard — fully offline via injected DNS answers."""

from __future__ import annotations

import ipaddress
import socket
import urllib.parse
from types import SimpleNamespace

import app.core.ssrf as ssrf
import pytest
from app.core.errors import BadRequest, UnprocessableEntity
from app.core.ssrf import (
    ALLOWED_SCHEMES,
    UrlRejected,
    _is_forbidden_address,
    _validate_resolution,
    _validate_syntax,
    assert_safe_url,
    is_simulation_url,
)

# --- fixtures ---------------------------------------------------------------------


@pytest.fixture
def strict(monkeypatch: pytest.MonkeyPatch) -> None:
    """Production posture: private targets are NOT allowed (resolution runs)."""
    monkeypatch.setattr(ssrf, "get_settings", lambda: SimpleNamespace(allow_private_targets=False))


@pytest.fixture
def lax(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulation posture: resolution skipped, syntax still enforced."""
    monkeypatch.setattr(ssrf, "get_settings", lambda: SimpleNamespace(allow_private_targets=True))


def install_dns(monkeypatch: pytest.MonkeyPatch, answer: list[str] | Exception) -> None:
    """Replace socket.getaddrinfo with a stub returning canned addresses."""

    def resolver(host: object, port: object, *args: object, **kwargs: object) -> list[tuple]:
        if isinstance(answer, Exception):
            raise answer
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (str(addr), 0)) for addr in answer]

    monkeypatch.setattr(socket, "getaddrinfo", resolver)


# --- pure helper: forbidden-address classification ---------------------------------


@pytest.mark.parametrize(
    "address",
    [
        # RFC1918 private
        "10.0.0.1",
        "172.16.0.9",
        "192.168.1.10",
        # loopback
        "127.0.0.1",
        "::1",
        # link-local + cloud metadata
        "169.254.169.254",
        "fe80::1",
        # CGNAT shared address space
        "100.64.0.1",
        "100.127.255.254",
        # benchmark / documentation / reserved / unspecified
        "198.18.0.5",
        "192.0.2.1",
        "198.51.100.7",
        "203.0.113.9",
        "240.0.0.1",
        "0.0.0.0",  # noqa: S104 - string literal in an address-classification table
        # ULA / IPv6 documentation
        "fc00::1",
        "2001:db8::1",
        # multicast
        "224.0.0.1",
        "ff02::1",
    ],
)
def test_private_and_special_addresses_are_forbidden(address: str) -> None:
    assert _is_forbidden_address(ipaddress.ip_address(address)) is True


@pytest.mark.parametrize("address", ["8.8.8.8", "1.1.1.1", "2606:4700::1111", "203.97.33.1"])
def test_public_addresses_are_allowed(address: str) -> None:
    assert _is_forbidden_address(ipaddress.ip_address(address)) is False


# --- pure helper: syntax validation -------------------------------------------------


def test_allowed_schemes_registry() -> None:
    assert ALLOWED_SCHEMES == frozenset({"http", "https"})


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com/path?q=1",
        "https://example.com",
        "HTTP://EXAMPLE.COM",  # scheme comparison is case-insensitive
        "https://example.com:8443/",
        "http://203.0.113.10/",  # syntax only; the address is checked at resolution
    ],
)
def test_syntax_accepts_wellformed_http_urls(url: str) -> None:
    _validate_syntax(urllib.parse.urlparse(url))


@pytest.mark.parametrize(
    ("url", "reason_fragment"),
    [
        ("ftp://example.com/file", "scheme"),
        ("file:///etc/passwd", "scheme"),
        ("gopher://example.com", "scheme"),
        ("ws://example.com/socket", "scheme"),
        ("javascript:alert(1)", "scheme"),
        ("sim://demo/always-down", "scheme"),
        ("/relative/path", "scheme"),
        ("http://user@example.com/", "userinfo"),
        ("http://user:pass@example.com/", "userinfo"),
        ("http://victim.com@127.0.0.1/", "userinfo"),
        ("http://example.com:70000/", "port"),
        ("http://example.com:0/", "port"),
        ("http://example.com:notaport/", "port"),
    ],
)
def test_syntax_rejects_bad_urls(url: str, reason_fragment: str) -> None:
    with pytest.raises(UrlRejected, match=reason_fragment):
        _validate_syntax(urllib.parse.urlparse(url))


# --- full pipeline: allowed ----------------------------------------------------------


@pytest.mark.parametrize("url", ["https://example.com/", "http://status.example.net/health"])
def test_public_urls_pass_full_pipeline(
    strict: None, monkeypatch: pytest.MonkeyPatch, url: str
) -> None:
    install_dns(monkeypatch, ["93.184.216.34"])
    parsed = assert_safe_url(url)
    assert parsed.scheme in {"http", "https"}
    assert parsed.hostname


def test_every_resolved_address_must_be_public(
    strict: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_dns(monkeypatch, ["93.184.216.34", "10.0.0.99"])
    with pytest.raises(UnprocessableEntity):
        assert_safe_url("http://mixed.example.com/")


def test_lax_mode_skips_resolution_but_not_syntax(lax: None) -> None:
    # No DNS installed on purpose: resolution must be skipped entirely.
    parsed = assert_safe_url("http://127.0.0.1:8080/metrics")
    assert parsed.hostname == "127.0.0.1"
    with pytest.raises(UnprocessableEntity):
        assert_safe_url("ftp://127.0.0.1/")


# --- full pipeline: blocked ------------------------------------------------------------


@pytest.mark.parametrize(
    "address",
    ["10.0.0.5", "127.0.0.1", "169.254.169.254", "100.64.0.1", "::1", "fe80::1"],
)
def test_private_targets_blocked_via_resolution(
    strict: None, monkeypatch: pytest.MonkeyPatch, address: str
) -> None:
    install_dns(monkeypatch, [address])
    with pytest.raises(UnprocessableEntity):
        assert_safe_url("http://internal.example.com/")


def test_unresolvable_host_fails_closed(strict: None, monkeypatch: pytest.MonkeyPatch) -> None:
    install_dns(monkeypatch, socket.gaierror(-2, "Name or service not known"))
    with pytest.raises(UnprocessableEntity):
        assert_safe_url("https://does-not-exist.invalid/")


def test_empty_resolution_fails_closed(strict: None, monkeypatch: pytest.MonkeyPatch) -> None:
    install_dns(monkeypatch, [])
    with pytest.raises(UnprocessableEntity):
        assert_safe_url("https://empty.example.com/")


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com/",
        "file:///etc/passwd",
        "http://user:pass@example.com/",
        "http://example.com:70000/",
        "http://example.com:0/",
    ],
)
def test_syntax_blocks_apply_in_strict_mode(strict: None, url: str) -> None:
    with pytest.raises(UnprocessableEntity):
        assert_safe_url(url)


# --- error surface ----------------------------------------------------------------------


def test_block_error_is_generic_and_coded(strict: None, monkeypatch: pytest.MonkeyPatch) -> None:
    install_dns(monkeypatch, ["127.0.0.1"])
    with pytest.raises(UnprocessableEntity) as excinfo:
        assert_safe_url("http://secret-infra.example.com/")
    assert excinfo.value.code == "SSRF_BLOCKED"
    # The exact tripped rule must never leak to the client.
    assert str(excinfo.value) == "URL is not allowed"


# --- resolution helper details ------------------------------------------------------------


def test_validate_resolution_dedupes_and_returns_addresses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_dns(monkeypatch, ["93.184.216.34", "93.184.216.34", "2606:4700::1111"])
    addresses = _validate_resolution("dual-stack.example.com")
    assert {str(a) for a in addresses} == {"93.184.216.34", "2606:4700::1111"}


def test_validate_resolution_passes_hostname_through(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, object] = {}

    def spy(host: object, port: object, *args: object, **kwargs: object) -> list[tuple]:
        seen["host"] = host
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]

    monkeypatch.setattr(socket, "getaddrinfo", spy)
    assert _validate_resolution("spy.example.com")
    assert seen["host"] == "spy.example.com"


# --- simulation URLs -----------------------------------------------------------------------


@pytest.mark.parametrize("url", ["sim://demo/flaky", "SIM://demo/slow", "sim://x/y"])
def test_simulation_url_detection(url: str) -> None:
    assert is_simulation_url(url) is True


@pytest.mark.parametrize("url", ["https://example.com/", "simx://demo", "", "//host/path"])
def test_non_simulation_urls(url: str) -> None:
    assert is_simulation_url(url) is False


# --- tcp:// docker-host endpoints (finding: SSRF guard skipped for tcp://) ------------


def test_tcp_endpoint_to_metadata_ip_is_blocked(
    strict: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_dns(monkeypatch, ["169.254.169.254"])
    with pytest.raises(BadRequest) as excinfo:
        ssrf.assert_safe_tcp_endpoint("tcp://internal-metadata.example.com:2375")
    assert excinfo.value.code == "ENDPOINT_BLOCKED"


def test_tcp_endpoint_to_private_address_is_blocked(
    strict: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_dns(monkeypatch, ["10.0.0.9"])
    with pytest.raises(BadRequest):
        ssrf.assert_safe_tcp_endpoint("tcp://docker.internal.example.com:2375")


def test_tcp_endpoint_to_public_host_passes(strict: None, monkeypatch: pytest.MonkeyPatch) -> None:
    install_dns(monkeypatch, ["93.184.216.34"])
    assert ssrf.assert_safe_tcp_endpoint("tcp://docker.example.com:2375") is None


def test_tcp_endpoint_requires_explicit_port(strict: None) -> None:
    with pytest.raises(BadRequest):
        ssrf.assert_safe_tcp_endpoint("tcp://docker.example.com")


def test_tcp_endpoint_rejects_embedded_credentials(strict: None) -> None:
    with pytest.raises(BadRequest):
        ssrf.assert_safe_tcp_endpoint("tcp://user:pass@docker.example.com:2375")


def test_tcp_endpoint_rejects_non_tcp_schemes(strict: None) -> None:
    with pytest.raises(BadRequest):
        ssrf.assert_safe_tcp_endpoint("http://docker.example.com:2375")


def test_tcp_endpoint_lax_mode_skips_resolution(lax: None) -> None:
    # allow_private_targets=true: no DNS installed on purpose.
    assert ssrf.assert_safe_tcp_endpoint("tcp://10.0.0.9:2375") is None


async def test_docker_host_service_guards_tcp_but_exempt_local_endpoints(
    strict: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.services import docker_host_service

    install_dns(monkeypatch, ["10.0.0.9"])
    # unix:// sockets and agent-inherited (empty) endpoints never leave the box.
    await docker_host_service._assert_endpoint_allowed("unix:///var/run/docker.sock")
    await docker_host_service._assert_endpoint_allowed("")
    # tcp:// endpoints go through the strict resolution check.
    with pytest.raises(BadRequest):
        await docker_host_service._assert_endpoint_allowed("tcp://docker.internal.example.com:2375")
