"""Identity & access models: users, roles, permissions, sessions, tokens."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, org_id_column, uuid_pk
from app.models.enums import UserStatus


class Role(TimestampMixin, Base):
    """A named permission set.

    ``org_id`` is NULL for every row in v1 — the five built-in roles are
    instance-wide templates and a membership's ``role_id`` points at one of them.
    Custom per-organization roles are Phase 7 work; when they arrive this column
    starts carrying values and ``name`` uniqueness splits into a partial unique
    index over ``org_id IS NULL`` (system templates) plus ``(org_id, name)`` for
    organization-owned roles. A plain composite ``UNIQUE (org_id, name)`` would
    be wrong here, because PostgreSQL treats NULLs as distinct and the system
    role names would stop being unique.
    """

    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = uuid_pk()
    org_id: Mapped[uuid.UUID | None] = org_id_column(nullable=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    permissions: Mapped[list[Permission]] = relationship(
        secondary="role_permissions", lazy="selectin"
    )
    users: Mapped[list[User]] = relationship(back_populates="role")


class Permission(TimestampMixin, Base):
    __tablename__ = "permissions"

    id: Mapped[uuid.UUID] = uuid_pk()
    codename: Mapped[str] = mapped_column(String(96), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    group: Mapped[str] = mapped_column(String(48), default="", nullable=False)


class RolePermission(Base):
    __tablename__ = "role_permissions"
    role_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )
    permission_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    full_name: Mapped[str] = mapped_column(String(160), default="", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Bootstrap escape hatch: implies every permission. Never granted via API.
    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    status: Mapped[UserStatus] = mapped_column(
        String(16), default=UserStatus.ACTIVE, nullable=False
    )
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    role_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("roles.id", ondelete="RESTRICT"), nullable=True
    )
    role: Mapped[Role | None] = relationship(lazy="selectin")

    api_keys: Mapped[list[ApiKey]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def display_name(self) -> str:
        return self.full_name or self.email.split("@")[0]


class Session(TimestampMixin, Base):
    """A login session binding refresh tokens to a device/context."""

    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ip_address: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    user_agent: Mapped[str] = mapped_column(Text, default="", nullable=False)
    device_label: Mapped[str] = mapped_column(String(120), default="", nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_reason: Mapped[str] = mapped_column(String(120), default="", nullable=False)


class RefreshToken(TimestampMixin, Base):
    """Opaque refresh token; only its SHA-256 hash is stored.

    Rotation chain: on refresh the old row gets ``superseded_by_id`` and a
    fresh row is issued. Presenting a superseded token indicates theft and
    revokes the whole session — except for the one-shot grace rescue in
    ``auth_service.refresh`` (a navigation can abort an in-flight rotation
    after the server committed it, losing the response cookie); ``grace_used``
    bounds that rescue to a single use per token.
    """

    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = uuid_pk()
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    superseded_by_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    grace_used: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )


class ApiKey(TimestampMixin, Base):
    """Machine credential. Raw key shown once at creation; hash stored.

    A key is bound to **one organization** at creation (the creator must hold an
    active membership in it): machine callers present no ``X-Org-Id`` header, so
    the key's own ``org_id`` is the tenancy boundary. The header is ignored for
    key auth, and a key can never be widened to another org afterwards.
    """

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    org_id: Mapped[uuid.UUID] = org_id_column()
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(24), nullable=False)
    key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    scopes: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="api_keys")
