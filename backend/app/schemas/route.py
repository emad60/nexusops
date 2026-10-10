"""Route schemas, the upstream picker, and the node proxy-status read model.

Every structured field a route can carry is validated here with the same models
the renderer re-validates with (:mod:`app.schemas.proxy`), so an API write and a
render can never disagree about what is acceptable.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.models.enums import RouteConfigState, RouteRemovalState
from app.schemas.base import APIModel, OutModel
from app.schemas.proxy import RateLimit, RouteHeader, RouteRedirect

#: Host and port the proxy itself owns on a node; a container publishing on them
#: can never be a routable upstream, because nginx needs them.
RESERVED_HOST_PORTS = (80, 443)


class UpstreamPortOut(APIModel):
    """One genuinely usable published port reported by the node's agent."""

    host_port: int
    container_port: int
    protocol: str = "tcp"
    bind_address: str = ""
    #: The address the renderer will proxy to (loopback for wildcard/loopback
    #: bindings, otherwise the specific host address).
    upstream_host: str


class UpstreamContainerOut(APIModel):
    """A container that can actually back a route on this node."""

    id: UUID
    container_id: str
    name: str
    image_ref: str = ""
    status: str
    upstream_ports: list[UpstreamPortOut] = Field(default_factory=list)
    unavailable_reason: str | None = None


class RouteCreate(APIModel):
    """Payload for ``POST /routes``.

    A route is created **disabled** unless ``enabled`` is requested; enabling is
    the operation that requires a verified domain and a routable node, and the
    service refuses it if either is missing.
    """

    domain_id: UUID
    hostname: str = Field(min_length=4, max_length=253)
    path: str = Field(default="/", max_length=255)
    node_id: UUID
    container_id: UUID
    port: int = Field(ge=1, le=65535)
    headers: list[RouteHeader] = Field(default_factory=list, max_length=16)
    rate_limit: RateLimit | None = None
    redirect: RouteRedirect | None = None
    monitor_optout: bool = False
    enabled: bool = False

    @field_validator("headers")
    @classmethod
    def _distinct_headers(cls, value: list[RouteHeader]) -> list[RouteHeader]:
        seen: set[tuple[str, str]] = set()
        for header in value:
            key = (header.target, header.name.lower())
            if key in seen:
                raise ValueError(f"header {header.name} is set twice for the same target")
            seen.add(key)
        return value


class RouteUpdate(APIModel):
    """Partial update. Changing the node re-validates the upstream from scratch."""

    hostname: str | None = Field(default=None, min_length=4, max_length=253)
    path: str | None = Field(default=None, max_length=255)
    node_id: UUID | None = None
    container_id: UUID | None = None
    port: int | None = Field(default=None, ge=1, le=65535)
    headers: list[RouteHeader] | None = Field(default=None, max_length=16)
    rate_limit: RateLimit | None = None
    redirect: RouteRedirect | None = None
    monitor_optout: bool | None = None


class RouteOut(OutModel):
    """Route read model."""

    updated_at: datetime
    domain_id: UUID
    domain_name: str | None = None
    hostname: str
    path: str
    #: Derived (``http://hostname/path``) by the endpoint; no DB column.
    url: str = ""
    node_id: UUID
    node_name: str | None = None
    container_id: UUID | None = None
    container_name: str | None = None
    container_ref: str | None = None
    port: int
    scheme: str
    enabled: bool
    config_state: RouteConfigState
    headers: list[RouteHeader] = Field(default_factory=list)
    rate_limit: RateLimit | None = None
    redirect: RouteRedirect | None = None
    monitor_id: UUID | None = None
    monitor_optout: bool = False
    last_applied_at: datetime | None = None
    last_bundle_id: str | None = None
    last_apply_error: str = ""
    #: Which half of a removal this route is in, when it is in one: ``REQUESTED``
    #: (out of the desired configuration, no node has confirmed it is gone) or
    #: ``CONFIRMED`` (a node applied a bundle without it). ``None`` when no removal
    #: is in flight. Derived from the row's own timestamps.
    removal_state: RouteRemovalState | None = None
    removal_requested_at: datetime | None = None
    removal_confirmed_at: datetime | None = None
    #: Human-readable explanation of ``config_state`` — never raw configuration.
    status_detail: str = ""


class RouteDetailOut(RouteOut):
    """Detail is the list model plus the owning domain's verification state."""

    domain_status: str


class NodeProxyCapabilityOut(APIModel):
    """The node's reported nginx capability, bounded to the useful facts."""

    present: bool = False
    version: str | None = None
    running: bool | None = None
    config_test_ok: bool | None = None
    routing_eligible: bool = False
    reason: str = ""
    listener_80: str = "UNKNOWN"
    listener_443: str = "UNKNOWN"


class NodeProxyStatusOut(OutModel):
    """``GET /nodes/{id}/proxy/status``.

    Reports what the node said and what the control plane *expects* — never a
    configuration file, a system path listing or arbitrary host data.
    """

    updated_at: datetime
    node_id: UUID
    node_name: str
    provider: str = "nginx"
    capability: NodeProxyCapabilityOut
    #: Whether route creation/enabling is allowed on this node right now.
    eligible: bool = False
    ineligible_reason: str = ""
    expected_bundle_id: str | None = None
    live_bundle_id: str | None = None
    drift: bool | None = None
    last_status_at: datetime | None = None
    last_status_error: str = ""
    route_total: int = 0
    route_enabled: int = 0
    route_in_sync: int = 0
    route_stale: int = 0
    route_failed: int = 0
    #: Enabled routes that are out of the desired configuration but whose removal
    #: no node has confirmed. Non-zero means a node may still be running the
    #: configuration that serves them — never that they are gone.
    route_removal_pending: int = 0
    last_applied_at: datetime | None = None
    last_apply_error: str = ""
