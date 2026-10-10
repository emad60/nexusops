"""The ProxyProvider seam: what the control plane needs from a config renderer.

Three methods, one implementation in Phase 4 (:mod:`app.providers.nginx`):

* :meth:`ProxyProvider.render` — pure. Same node + same enabled routes ⇒ same
  bundle and same fingerprint, byte for byte. It reads no clock, no session and
  no random source, which is what makes drift detection meaningful.
* :meth:`ProxyProvider.apply` — turns a bundle into the *params* of a whitelisted
  ``nginx.apply`` operation. It does not touch the network or the database.
* :meth:`ProxyProvider.status` — names the read-only operation that reports live
  state.

The dataclasses here are deliberately plain: the renderer must stay testable
without a database, so the service layer flattens ORM rows into
:class:`ResolvedRoute` / :class:`ResolvedNode` before calling it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from app.schemas.proxy import NginxBundle


@dataclass(frozen=True, slots=True)
class ResolvedNode:
    """The node facts a renderer is allowed to know."""

    id: str
    name: str


@dataclass(frozen=True, slots=True)
class ResolvedRoute:
    """One *enabled* route, flattened and already validated.

    The service resolves everything the template needs — canonical hostname,
    covered domain, upstream host — so the renderer never re-reads the database
    or re-derives authorization.
    """

    id: str
    hostname: str
    path: str
    upstream_host: str
    upstream_port: int
    headers: tuple[dict[str, Any], ...] = ()
    rate_limit: dict[str, Any] | None = None
    redirect: dict[str, Any] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ProxyProvider(Protocol):
    """What ``app.services.proxy_service`` is allowed to assume about a provider.

    The protocol exists so the service is not written against nginx specifically:
    Phase 5 or a future provider can implement the same three methods without a
    route-level code change. It is a *protocol*, not a plugin registry — there is
    exactly one implementation and no discovery mechanism.
    """

    name: str
    capability: str

    def render(self, node: ResolvedNode, routes: list[ResolvedRoute]) -> NginxBundle: ...

    def apply_params(self, bundle: NginxBundle) -> dict[str, Any]: ...

    def status_params(self) -> dict[str, Any]: ...
