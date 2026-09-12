"""Unit tests for the chained-proxy client-IP resolver (app/core/client_ip.py)."""

from __future__ import annotations

from types import SimpleNamespace

from app.core.client_ip import _parse_networks, resolve_client_ip
from starlette.requests import Request


def make_request(forwarded: str | None, peer: str = "172.23.0.5") -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if forwarded is not None:
        headers.append((b"x-forwarded-for", forwarded.encode()))
    scope: dict = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "query_string": b"",
        "headers": headers,
        "client": (peer, 51784),
    }
    return Request(scope)


def test_no_header_falls_back_to_tcp_peer():
    assert resolve_client_ip(make_request(None)) == "172.23.0.5"


def test_all_trusted_entries_fall_back_to_peer():
    # Dev topology: the edge is the only proxy; its sole entry is our own.
    assert resolve_client_ip(make_request("172.23.0.1")) == "172.23.0.5"


def test_trusted_hop_skipped_to_real_client():
    # Production chain after the host proxy stamps X-Forwarded-For: client, edge-peer.
    request = make_request("203.0.113.7, 172.23.0.1")
    assert resolve_client_ip(request) == "203.0.113.7"


def test_spoofed_leftmost_entries_are_ignored():
    # A client injecting XFF through the chain lands leftmost; the walk from
    # the right must stop at the outer proxy's stamp, never reach the fake.
    request = make_request("6.6.6.6, 203.0.113.7, 172.23.0.1")
    assert resolve_client_ip(request) == "203.0.113.7"


def test_public_rightmost_is_taken_verbatim():
    request = make_request("203.0.113.7")
    assert resolve_client_ip(request) == "203.0.113.7"


def test_malformed_and_empty_entries_do_not_crash_or_mislead():
    request = make_request("not-an-ip,, , 203.0.113.7, 172.23.0.1")
    assert resolve_client_ip(request) == "203.0.113.7"


def test_empty_header_value_falls_back_to_peer():
    assert resolve_client_ip(make_request("")) == "172.23.0.5"


def test_trusted_cidr_list_is_configurable(monkeypatch):
    monkeypatch.setattr(
        "app.core.client_ip.get_settings",
        lambda: SimpleNamespace(trusted_proxy_cidrs="10.0.0.0/8,127.0.0.0/8"),
    )
    # 172.23.0.1 is no longer trusted → it is taken as the client address.
    assert resolve_client_ip(make_request("203.0.113.7, 172.23.0.1")) == "172.23.0.1"
    # 10.0.0.9 stays trusted → walk continues past it.
    assert resolve_client_ip(make_request("203.0.113.7, 10.0.0.9")) == "203.0.113.7"


def test_parse_networks_skips_malformed_entries():
    networks = _parse_networks("10.0.0.0/8, nonsense, 192.168.0.0/16,")
    assert len(networks) == 2


def test_oversized_header_is_bounded():
    header = ",".join(f"203.0.113.{i % 250 + 1}" for i in range(500))
    request = make_request(header)
    # Every entry is public/untrusted; the walk must still terminate and take
    # the rightmost (bounded) entry rather than hang or error.
    assert resolve_client_ip(request).startswith("203.0.113.")
