"""NginxProvider — a pure, deterministic renderer plus the two op wrappers.

Rendering is a function of ``(node, enabled routes)`` and nothing else: no clock,
no database, no randomness, no file reads. The same inputs always produce the
same bytes and therefore the same fingerprint, which is what makes drift
detection and "did anything change?" cheap and unambiguous.

**Phase 4 renders HTTP only.** There is no ``ssl_*`` directive, no certificate
path, no redirect to ``https://`` and no reference to any key material anywhere
in the template text — HTTPS arrives with its own subsystem in Phase 5.

Why this is an injection defence and not merely a template: every user-influenced
value has already been canonicalised and allowlisted
(:mod:`app.core.dnsname`, :mod:`app.schemas.proxy`), and the renderer
re-validates the structured fields it receives rather than trusting the caller.
``nginx -t`` at the node is a syntax net, never the boundary.
"""

from __future__ import annotations

import hashlib
from typing import Any

from app.core.dnsname import canonicalize_name, canonicalize_path, hostname_is_covered
from app.providers.proxy import ResolvedNode, ResolvedRoute
from app.schemas.proxy import (
    MANAGED_CONF_PATH,
    MAX_HEADERS_PER_ROUTE,
    MAX_ROUTES_PER_NODE,
    ROUTES_DIR,
    TEMPLATE_VERSION,
    BundleFile,
    NginxBundle,
)

# --- template text -----------------------------------------------------------
#
# Fixed strings only. Nothing below is assembled from user input; user values are
# inserted at exactly one place each, after re-validation, and the slots are
# quoted so a value can never escape into directive syntax.

_BANNER = (
    "# NexusOps managed configuration — generated from route records.\n"
    "# Do not edit: the next apply overwrites this file.\n"
    f"# templates v{TEMPLATE_VERSION}\n"
)

_DEFAULT_SERVER = """\
server {
    listen 80 default_server;
    server_name _;
    # Unmatched or unowned Host headers are dropped rather than proxied: no
    # organization may answer for a name it does not own.
    return 444;
}
"""

_STANDARD_PROXY_HEADERS = """\
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
"""


class RenderError(ValueError):
    """Rendering refused the input. Always a bug or a corrupt row, never a leak."""


def _route_key(route_id: str) -> str:
    """A deterministic, filesystem-safe fragment name for one route."""
    digest = hashlib.sha256(route_id.encode("utf-8")).hexdigest()[:32]
    return f"r-{digest}.conf"


def _zone_name(route: ResolvedRoute) -> str:
    digest = hashlib.sha256(route.id.encode("utf-8")).hexdigest()[:16]
    return f"nx_{digest}"


def _validate_upstream_host(value: str) -> str:
    """Accept only a literal IPv4/IPv6 address — never a name, never an expression.

    The upstream host is derived by the service from the container's *published
    binding*, so it is always an address. Re-checking here means a corrupt row
    cannot introduce a hostname that nginx would resolve at request time.
    """
    import ipaddress

    if not isinstance(value, str) or not value:
        raise RenderError("upstream host is missing")
    candidate = value
    try:
        ipaddress.ip_address(candidate)
    except ValueError:
        raise RenderError("upstream host must be a literal IP address") from None
    return candidate


def _validate_port(value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not (1 <= value <= 65535):
        raise RenderError("upstream port is out of range")
    return value


def _header_lines(route: ResolvedRoute) -> tuple[list[str], list[str]]:
    """Validate the route's headers and split them by destination."""
    from app.schemas.proxy import RouteHeader

    if len(route.headers) > MAX_HEADERS_PER_ROUTE:
        raise RenderError("too many headers on one route")
    response: list[str] = []
    proxy: list[str] = []
    for raw in route.headers:
        header = RouteHeader.model_validate(raw)  # raises on anything off-spec
        if header.target == "proxy":
            proxy.append(f"    proxy_set_header {header.name} {_quote(header.value)};")
        else:
            response.append(f"    add_header {header.name} {_quote(header.value)} always;")
    return response, proxy


def _quote(value: str) -> str:
    """Wrap an already-validated value in quotes for a template slot.

    Values reaching here have passed ``_HEADER_VALUE_RE`` (no ``"``, no ``\\``,
    no ``$``), so quoting is a formality — but it is kept so a future relaxation
    of the charset cannot silently become a directive break.
    """
    return f'"{value}"'


def _rate_zone(route: ResolvedRoute) -> str:
    """The ``limit_req_zone`` declaration for a rate-limited route."""
    from app.schemas.proxy import RateLimit

    if route.rate_limit is None:
        return ""
    limit = RateLimit.model_validate(route.rate_limit)
    unit = "r/s" if limit.window == "1s" else "r/m"
    return (
        f"limit_req_zone $binary_remote_addr zone={_zone_name(route)}:10m "
        f"rate={limit.requests}{unit};\n"
    )


def _redirect_line(route: ResolvedRoute) -> str | None:
    """A fixed host redirect, or ``None`` for a normal proxying route."""
    from app.schemas.proxy import RouteRedirect

    if route.redirect is None:
        return None
    redirect = RouteRedirect.model_validate(route.redirect)
    target = canonicalize_name(redirect.to_host)
    return f"    return {redirect.code} http://{target}$request_uri;"


def _server_block(route: ResolvedRoute, *, node: ResolvedNode) -> str:
    """One route's ``server`` block — the only place user values are emitted."""
    del node  # the block is per-route; node context is not part of the text
    hostname = canonicalize_name(route.hostname, allow_wildcard=True)
    path = canonicalize_path(route.path)
    port = _validate_port(route.upstream_port)
    lines: list[str] = [
        "server {",
        "    listen 80;",
        f"    server_name {hostname};",
        "",
    ]
    redirect = _redirect_line(route)
    if redirect is not None:
        lines.append(f"    location {path} {{")
        lines.append(redirect)
        lines.append("    }")
        lines.append("}")
        return "\n".join(lines) + "\n"

    upstream = _validate_upstream_host(route.upstream_host)
    response_headers, proxy_headers = _header_lines(route)
    lines.append(f"    location {path} {{")
    if route.rate_limit is not None:
        from app.schemas.proxy import RateLimit

        limit = RateLimit.model_validate(route.rate_limit)
        lines.append(f"    limit_req zone={_zone_name(route)} burst={limit.burst} nodelay;")
    lines.append(f"    proxy_pass http://{upstream}:{port};")
    lines.append(_STANDARD_PROXY_HEADERS.rstrip("\n"))
    lines.extend(proxy_headers)
    lines.extend(response_headers)
    lines.append("    }")
    lines.append("}")
    return "\n".join(lines) + "\n"


class NginxProvider:
    """The only production provider in Phase 4."""

    name = "nginx"
    capability = "nginx"

    # --- render ---------------------------------------------------------------

    def render(self, node: ResolvedNode, routes: list[ResolvedRoute]) -> NginxBundle:
        """Render the complete desired state for *node*.

        A full tree every time — never a delta — so the node's configuration is
        always reproducible from the database and a partially applied bundle
        cannot exist.
        """
        if len(routes) > MAX_ROUTES_PER_NODE:
            raise RenderError(f"a node may not serve more than {MAX_ROUTES_PER_NODE} routes")

        ordered = sorted(routes, key=lambda r: (r.hostname, r.path, r.id))
        seen: set[tuple[str, str]] = set()
        for route in ordered:
            canonical_host = canonicalize_name(route.hostname, allow_wildcard=True)
            key = (canonical_host, canonicalize_path(route.path))
            if key in seen:
                # The database enforces this for enabled routes; a duplicate here
                # means the desired state is contradictory and must not render.
                raise RenderError(f"duplicate enabled route for {canonical_host}{key[1]}")
            seen.add(key)

        files: list[BundleFile] = []
        http_level = [_BANNER, ""]
        zones = [_rate_zone(route) for route in ordered]
        for zone in zones:
            if zone:
                http_level.append(zone)
        http_level.append("\n")
        http_level.append(_DEFAULT_SERVER)
        files.append(BundleFile(path=MANAGED_CONF_PATH, content="".join(http_level)))

        for route in ordered:
            content = _BANNER + "\n" + _server_block(route, node=node)
            files.append(BundleFile(path=f"{ROUTES_DIR}/{_route_key(route.id)}", content=content))

        from app.schemas.proxy import fingerprint_files

        bundle_id = fingerprint_files(files, template_version=TEMPLATE_VERSION)
        return NginxBundle(
            bundle_id=bundle_id,
            template_version=TEMPLATE_VERSION,
            manifest=[route.id for route in ordered],
            files=files,
        )

    # --- apply / status ------------------------------------------------------

    def apply_params(self, bundle: NginxBundle) -> dict[str, Any]:
        """Params for the whitelisted ``nginx.apply`` operation."""
        return {"bundle": bundle.model_dump(), "reload": True}

    def status_params(self) -> dict[str, Any]:
        return {}

    # --- helpers used by the service layer -----------------------------------

    @staticmethod
    def route_file_path(route_id: str) -> str:
        """Where a route's fragment lands, so the service can name it in events."""
        return f"{ROUTES_DIR}/{_route_key(route_id)}"

    @staticmethod
    def covers(hostname: str, domain_name: str) -> bool:
        return hostname_is_covered(hostname, domain_name)


provider = NginxProvider()
