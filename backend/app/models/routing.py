"""Domains and Routes — the reverse-proxy management subsystem (Phase 4).

Two tenant-owned tables, one relationship spine:
**Organization → Domain → Route → (Node, Container, port)**. Both inherit
:class:`~app.models.base.OrgScoped`, so the session guard and PostgreSQL RLS treat
them exactly like every other tenant table: a query without an active
organization raises rather than reading across tenants.

Phase-4 boundary decisions recorded in the schema rather than only in prose:

* ``domains.name`` is stored **canonical** (lowercase, trailing dot stripped,
  IDNA/punycode) so uniqueness and route coverage compare one form. Verified
  names are unique platform-wide through a partial unique index on
  ``lower(name) WHERE status = 'VERIFIED'`` — that index is what makes
  anti-takeover a database fact instead of an application convention.
* Routes are HTTP-only in Phase 4 and remain so: ``scheme`` is a closed check of
  ``'http'``. Phase 5.4.1 adds ``certificate_id`` **without** touching that
  check — the column records which certificate a route is *allowed* to serve,
  and nothing in this tree renders a TLS server block or flips ``scheme``.
  HTTPS activation arrives as a later migration that widens ``scheme``, not by
  softening a constraint now.
* ``certificate_id`` is a **tenant-consistent** reference: the foreign key is the
  pair ``(certificate_id, org_id)`` against ``certificates (id, org_id)``, so a
  route pointing at another organization's certificate is unrepresentable in the
  database rather than merely refused by the service. ``ORG_ID`` being part of
  the key is why a bare ``certificates.id`` FK would not have been enough.
* ``ON DELETE RESTRICT`` on that pair: deleting a certificate a route depends on
  must be an explicit act (unbind, then delete), never a deletion's side effect
  that silently strips a live association.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, OrgScoped, TimestampMixin, json_column, status_check, uuid_pk
from app.models.enums import DomainStatus, RouteConfigState


class Domain(OrgScoped, TimestampMixin, Base):
    """One DNS name an organization is proving it controls.

    ``name`` is canonical (see :mod:`app.core.dnsname`); callers never write a
    raw user string into it. ``verification_token`` is *not* a secret in the
    credential sense — it is published in the owner's DNS zone — but it is only
    returned by the API to ``domain.manage`` holders, and never after the name is
    verified, because a stale token in a log or event payload is a replay
    primitive.
    """

    __tablename__ = "domains"
    __table_args__ = (
        status_check("status", DomainStatus),
        UniqueConstraint("org_id", "name", name="uq_domains_org_id_name"),
        CheckConstraint("char_length(name) BETWEEN 4 AND 253", name="name_length"),
        CheckConstraint("attempt_count >= 0", name="attempt_count_non_negative"),
        Index("ix_domains_org_status", "org_id", "status"),
        Index("ix_domains_verification_sweep", "status", "next_check_at"),
        # Platform-wide one-verified-owner rule. Partial so any number of
        # organizations may *track* a name; only one may hold it verified.
        Index(
            "uq_domains_verified_name",
            text("lower(name)"),
            unique=True,
            postgresql_where=text("status = 'VERIFIED'"),
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    #: Optional grouping only — never an authorization dimension. The API
    #: rejects a project that belongs to another organization.
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(253), nullable=False)
    status: Mapped[DomainStatus] = mapped_column(
        String(16), default=DomainStatus.PENDING, nullable=False, index=True
    )
    #: ``nxs-verify=<32 urlsafe chars>``. Rotated on every re-verification so a
    #: token that leaked while pending is worthless afterwards.
    verification_token: Mapped[str] = mapped_column(String(96), nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    #: Apex NS set (sorted hostnames) observed when the name was verified.
    #: A different set later means the delegation changed hands.
    ns_snapshot: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    #: Boundary of the grace window: when a previously-verified name stopped
    #: proving control. ``STALE`` until ``stale_expires_at``, then UNVERIFIED.
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    proof_lost_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    #: Not indexed on purpose: the sweep selects on ``status`` +
    #: ``next_check_at`` (``ix_domains_verification_sweep``) and only ever reads
    #: this column off a row it already has.
    stale_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    #: Sanitized, bounded explanation of the last failed attempt. Never contains
    #: the expected token, another organization's data, or raw DNS frames.
    last_error: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    #: Last observed A/AAAA answer for the warning (§6 of domain-routing.md).
    #: Nothing gates on this: ownership and reachability are separate facts.
    dns_reachability: Mapped[dict[str, Any]] = json_column()

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Domain {self.name} {self.status}>"


class Route(OrgScoped, TimestampMixin, Base):
    """One hostname+path served from one container on one node.

    Relationship rules the database can carry are constraints here; the ones that
    need other rows (is the domain verified *now*, is the container on this node,
    is the port actually published) are enforced in
    :mod:`app.services.route_service` and again at render time.
    """

    __tablename__ = "routes"
    __table_args__ = (
        status_check("config_state", RouteConfigState),
        CheckConstraint("scheme = 'http'", name="scheme_http_only"),
        CheckConstraint("port BETWEEN 1 AND 65535", name="port_range"),
        CheckConstraint("path LIKE '/%'", name="path_absolute"),
        CheckConstraint("char_length(path) <= 255", name="path_length"),
        CheckConstraint("char_length(hostname) BETWEEN 4 AND 253", name="hostname_length"),
        # One nginx answer per name+prefix per node, among enabled routes only:
        # a disabled route may coexist with (or be replaced by) an enabled one.
        Index(
            "uq_routes_node_host_path",
            "node_id",
            "hostname",
            "path",
            unique=True,
            postgresql_where=text("enabled"),
        ),
        Index("ix_routes_domain", "domain_id"),
        Index("ix_routes_org_state", "org_id", "config_state"),
        Index("ix_routes_certificate_id", "certificate_id"),
        # Tenant-consistent reference (Phase 5.4.1). The pair is the key, so a
        # route in organization A cannot name a certificate in organization B
        # even if both ids are valid — a plain single-column FK would accept
        # that and leave the isolation guarantee to the service layer.
        # ``MATCH SIMPLE`` (the default) means a NULL ``certificate_id`` skips
        # the check entirely, which is what an unbound route needs.
        # RESTRICT: the certificate cannot disappear out from under a binding.
        ForeignKeyConstraint(
            ["certificate_id", "org_id"],
            ["certificates.id", "certificates.org_id"],
            name="fk_routes_certificate_org",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    domain_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("domains.id", ondelete="CASCADE"), nullable=False
    )
    #: The Domain's name, a one-label subdomain of it, or ``*.<name>`` for a
    #: wildcard Domain. Stored canonical and validated for coverage on write.
    hostname: Mapped[str] = mapped_column(String(253), nullable=False)
    path: Mapped[str] = mapped_column(String(255), default="/", nullable=False)
    node_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    #: The upstream container. ``SET NULL`` on delete: losing the container makes
    #: the route stale, not silently re-pointed at something else.
    container_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("containers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    #: The **host-published** port on the node (never the container-internal one).
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    #: HTTP only in Phase 4. Phase 5 adds https through its own migration.
    scheme: Mapped[str] = mapped_column(String(8), default="http", nullable=False)
    #: The certificate this route is allowed to serve once HTTPS is activated
    #: (Phase 5.4.1). ``NULL`` = unbound. Association only: this column does not
    #: make the route serve TLS, does not widen ``scheme`` and is not read by the
    #: HTTP renderer. Delivery re-evaluates eligibility from authoritative state
    #: on every read, so a binding whose domain lost verification, whose route is
    #: disabled, or whose certificate was superseded reports ineligible rather
    #: than silently serving something else.
    certificate_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    headers: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb")
    )
    rate_limit: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    #: Host redirect only (``{to_host, code}``). There is no ``to_scheme`` field
    #: in Phase 4, so no route can be made to emit an HTTPS redirect.
    redirect: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    config_state: Mapped[RouteConfigState] = mapped_column(
        String(16), default=RouteConfigState.PENDING, nullable=False
    )
    #: Auto-attached HTTP uptime monitor (opt out per route).
    monitor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("monitors.id", ondelete="SET NULL"), nullable=True
    )
    monitor_optout: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    #: Fingerprint of the bundle the node last confirmed as live for this route.
    last_bundle_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_apply_error: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    #: The two halves of a removal, kept apart on purpose. **Requested** means the
    #: route is out of the node's *desired* configuration (its domain stopped
    #: serving, an operator disabled it, the upstream vanished); the node may still
    #: be running the previous configuration, so nothing may claim it stopped
    #: serving. **Confirmed** means a node reported an *applied* bundle that does
    #: not contain this route. Between the two the honest report is "removal
    #: requested, not confirmed" — which is exactly the state a node that is offline
    #: or failing sits in, and the reason `STALE` alone cannot express it.
    removal_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    removal_confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Route {self.hostname}{self.path} -> {self.port} {self.config_state}>"
