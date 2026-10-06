"""Infrastructure models: servers, credentials, docker hosts, containers."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import (
    Base,
    OrgScoped,
    TimestampMixin,
    json_column,
    org_id_column,
    status_check,
    uuid_pk,
)
from app.models.enums import (
    ContainerHealth,
    ContainerStatus,
    CredentialKind,
    DockerHostStatus,
    ServerStatus,
)


class Tag(OrgScoped, TimestampMixin, Base):
    __tablename__ = "tags"
    # Tag names are unique per organization, not per instance: two customers
    # independently tagging a server "prod" must not collide (and the old
    # instance-wide index made org B's tag name visible as a uniqueness error).
    __table_args__ = (UniqueConstraint("org_id", "name", name="uq_tags_org_name"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    color: Mapped[str] = mapped_column(String(16), default="#64748b", nullable=False)


class Server(OrgScoped, TimestampMixin, Base):
    __tablename__ = "servers"
    __table_args__ = (
        UniqueConstraint("org_id", "name", name="uq_servers_org_name"),
        status_check("status", ServerStatus),
        CheckConstraint("heartbeat_interval_seconds >= 5", name="heartbeat_interval_min"),
        Index("ix_servers_status_heartbeat", "status", "last_heartbeat_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    os_name: Mapped[str] = mapped_column(String(96), default="", nullable=False)
    os_version: Mapped[str] = mapped_column(String(96), default="", nullable=False)
    arch: Mapped[str] = mapped_column(String(32), default="", nullable=False)
    environment: Mapped[str] = mapped_column(String(32), default="production", nullable=False)
    location: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    status: Mapped[ServerStatus] = mapped_column(
        String(16), default=ServerStatus.UNKNOWN, nullable=False, index=True
    )

    cpu_cores: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    memory_total_mb: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    disk_total_gb: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    agent_version: Mapped[str] = mapped_column(String(48), default="", nullable=False)
    # The agent's token hash lives in ``agent_credentials`` (one row per node),
    # not here: the hash has to be resolvable BEFORE an organization is known
    # (auth must identify the node first), and this table is RLS-enforced. The
    # routing table carries no tenant payload beyond (node, org) ids, so it can
    # stay outside RLS without weakening the boundary.
    agent_enrolled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    heartbeat_interval_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    offline_after_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    uptime_seconds: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    simulated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    extra: Mapped[dict] = json_column()

    docker_host: Mapped[DockerHost | None] = relationship(back_populates="server", uselist=False)
    tags: Mapped[list[Tag]] = relationship(
        secondary="server_tags", lazy="selectin", order_by="Tag.name"
    )


class ServerTag(OrgScoped, Base):
    """Join table between servers and tags.

    Inheriting :class:`OrgScoped` supplies the ``org_id`` column, but the ORM
    never writes it: the ``Server.tags`` secondary relationship emits only the two
    key columns. A BEFORE INSERT/UPDATE trigger fills it from the referenced
    server row — authoritatively, via a ``SECURITY DEFINER`` function owned by the
    migration role, so the value cannot be spoofed by the caller's scope. A
    cross-organization pair therefore fails the RLS ``WITH CHECK`` instead of
    being created. (The table is also RLS-policied like any other tenant table,
    so reads are filtered here too rather than inherited from the parents.)
    """

    __tablename__ = "server_tags"

    server_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("servers.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )


class AgentCredential(TimestampMixin, Base):
    """Token hash → (node, organization) routing row — the pre-org lookup.

    Deliberately outside :class:`OrgScoped` and outside RLS: an agent presents
    its token with no ``X-Org-Id`` header and no member identity, so resolving
    *which* organization and node the request belongs to is the very first thing
    that has to happen. The row holds only what that lookup needs, and carries no
    tenant payload — everything downstream (heartbeat, inventory, operations)
    runs under ``org_scope(row.org_id)`` and is enforced by the guard and RLS.

    One row per node: enrollment, rotation and revocation are updates to this
    row, so a revoked node's token stops being accepted immediately while the
    organization's other nodes are untouched.
    """

    __tablename__ = "agent_credentials"

    server_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("servers.id", ondelete="CASCADE"), primary_key=True
    )
    org_id: Mapped[uuid.UUID] = org_id_column()
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ServerCredential(OrgScoped, TimestampMixin, Base):
    """SSH credential for a server. The secret part is Fernet-encrypted."""

    __tablename__ = "server_credentials"

    id: Mapped[uuid.UUID] = uuid_pk()
    server_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("servers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[CredentialKind] = mapped_column(
        String(16), default=CredentialKind.SSH_KEY, nullable=False
    )
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    port: Mapped[int] = mapped_column(Integer, default=22, nullable=False)
    secret_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class DockerHost(OrgScoped, TimestampMixin, Base):
    __tablename__ = "docker_hosts"

    id: Mapped[uuid.UUID] = uuid_pk()
    server_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("servers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    endpoint_url: Mapped[str] = mapped_column(String(512), default="", nullable=False)
    tls_verify: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[DockerHostStatus] = mapped_column(
        String(16), default=DockerHostStatus.UNKNOWN, nullable=False, index=True
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str] = mapped_column(Text, default="", nullable=False)

    server: Mapped[Server | None] = relationship(back_populates="docker_host")


class Container(OrgScoped, Base):
    """Observed container state mirrored from an agent or docker provider."""

    __tablename__ = "containers"
    __table_args__ = (
        UniqueConstraint("docker_host_id", "container_id", name="uq_containers_host_cid"),
        status_check("status", ContainerStatus),
        status_check("health", ContainerHealth),
        Index("ix_containers_status_name", "status", "name"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    docker_host_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("docker_hosts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    server_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("servers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    container_id: Mapped[str] = mapped_column(String(72), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    image_ref: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    command: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    status: Mapped[ContainerStatus] = mapped_column(String(16), nullable=False, index=True)
    health: Mapped[ContainerHealth] = mapped_column(
        String(12), default=ContainerHealth.NONE, nullable=False
    )
    ports: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)
    env_keys: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    labels: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    mounts: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, default=list)

    restart_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cpu_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    mem_used_mb: Mapped[float | None] = mapped_column(Float, nullable=True)
    mem_limit_mb: Mapped[float | None] = mapped_column(Float, nullable=True)
    net_rx_kb_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    net_tx_kb_s: Mapped[float | None] = mapped_column(Float, nullable=True)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    simulated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ContainerImage(OrgScoped, TimestampMixin, Base):
    __tablename__ = "container_images"
    __table_args__ = (UniqueConstraint("docker_host_id", "image_id", name="uq_images_host_iid"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    docker_host_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("docker_hosts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    image_id: Mapped[str] = mapped_column(String(80), nullable=False)
    repo_tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    architecture: Mapped[str] = mapped_column(String(32), default="", nullable=False)
