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

from app.models.base import Base, TimestampMixin, json_column, status_check, uuid_pk
from app.models.enums import (
    ContainerHealth,
    ContainerStatus,
    CredentialKind,
    DockerHostStatus,
    ServerStatus,
)


class Tag(TimestampMixin, Base):
    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(16), default="#64748b", nullable=False)


class Server(TimestampMixin, Base):
    __tablename__ = "servers"
    __table_args__ = (
        status_check("status", ServerStatus),
        CheckConstraint("heartbeat_interval_seconds >= 5", name="heartbeat_interval_min"),
        Index("ix_servers_status_heartbeat", "status", "last_heartbeat_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
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
    agent_token_hash: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
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


class ServerTag(Base):
    __tablename__ = "server_tags"

    server_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("servers.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )


class ServerCredential(TimestampMixin, Base):
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


class DockerHost(TimestampMixin, Base):
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


class Container(Base):
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


class ContainerImage(TimestampMixin, Base):
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
