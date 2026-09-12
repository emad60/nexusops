"""Client-IP resolution behind chained reverse proxies.

The API never takes TCP connections from browsers directly: requests arrive
through the compose edge and, in production, through a host nginx (itself
behind Cloudflare). ``request.client.host`` is therefore the last proxy hop
— a docker-network address — and ``X-Forwarded-For`` is the only place the
real client address can come from.

Trust model: XFF is a chain of claims. Every proxy appends the address it
saw, and any client can inject fake *leftmost* entries. The readable truth is
found by walking the chain right-to-left and skipping entries contributed by
proxies we control (``trusted_proxy_cidrs``): the first entry we do NOT trust
is the client address as recorded by the outermost proxy we own. That outer
proxy must also OVERWRITE XFF at the trust boundary (the host vhost stamps
``X-Forwarded-For $remote_addr`` with real_ip against Cloudflare ranges), so
client-injected entries never survive to us. If every entry is trusted — or
the header is absent — we fall back to the TCP peer.
"""

from __future__ import annotations

import ipaddress
from functools import lru_cache

from fastapi import Request

from app.core.config import get_settings

# Bound the walk so a hostile multi-thousand-entry header cannot burn CPU.
_MAX_FORWARDED_ENTRIES = 10

_Network = ipaddress.IPv4Network | ipaddress.IPv6Network


@lru_cache(maxsize=8)
def _parse_networks(raw: str) -> tuple[_Network, ...]:
    """Parse a comma-separated CIDR list; malformed entries are skipped."""
    networks: list[_Network] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            network = ipaddress.ip_network(part, strict=False)
        except ValueError:
            continue
        networks.append(network)
    return tuple(networks)


def _is_trusted(address: str) -> bool:
    try:
        ip = ipaddress.ip_address(address)
    except ValueError:
        return False
    return any(ip in network for network in _parse_networks(get_settings().trusted_proxy_cidrs))


def resolve_client_ip(request: Request) -> str:
    """Real client address for *request* per the trust model above."""
    peer = request.client.host if request.client else "unknown"
    entries = request.headers.get("x-forwarded-for", "").split(",")
    for entry in reversed([e.strip() for e in entries][-_MAX_FORWARDED_ENTRIES:]):
        if not entry or _is_trusted(entry):
            continue
        return entry
    return peer
