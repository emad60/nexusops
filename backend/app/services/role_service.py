"""Role management and the permission registry API."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext
from app.core.errors import Conflict, NotFound, UnprocessableEntity
from app.core.permissions import ALL_CODENAMES, PERMISSIONS, SYSTEM_ROLES, WILDCARD
from app.models import Permission, Role, User
from app.models.enums import ActorType, EventLevel
from app.services import audit_service, event_bus


def permission_registry() -> list[dict[str, str]]:
    """The static registry as [{group, codename, description}], registry order."""
    return [
        {"group": spec.group, "codename": spec.codename, "description": spec.description}
        for spec in PERMISSIONS
    ]


def effective_permissions(user: User) -> list[str]:
    """Sorted explicit permission codenames for a user; ``*`` expands to the registry."""
    if user.is_superadmin:
        return sorted(ALL_CODENAMES)
    codes = {p.codename for p in (user.role.permissions if user.role else [])}
    if WILDCARD in codes:
        codes = set(ALL_CODENAMES)
    return sorted(codes)


async def list_roles(db: AsyncSession) -> list[Role]:
    """All roles ordered by name (permissions eager-loaded)."""
    return list((await db.execute(select(Role).order_by(Role.name))).scalars().all())


async def get_role(db: AsyncSession, role_id: UUID) -> Role:
    """Fetch a role or raise NotFound."""
    role = await db.get(Role, role_id)
    if role is None:
        raise NotFound("Role not found", code="ROLE_NOT_FOUND")
    return role


def validate_codenames(codenames: list[str]) -> None:
    """Ensure every codename exists in the registry; 422 listing the unknown ones."""
    unknown = sorted(set(codenames) - set(ALL_CODENAMES))
    if unknown:
        raise UnprocessableEntity(
            f"Unknown permissions: {', '.join(unknown)}",
            code="UNKNOWN_PERMISSIONS",
            details={"unknown": unknown},
        )


async def _resolve_permission_rows(db: AsyncSession, codenames: list[str]) -> list[Permission]:
    """Load Permission rows for *codenames*, failing loudly on unseeded entries."""
    if not codenames:
        return []
    rows = (
        (
            await db.execute(
                select(Permission).where(Permission.codename.in_(sorted(set(codenames))))
            )
        )
        .scalars()
        .all()
    )
    missing = sorted(set(codenames) - {r.codename for r in rows})
    if missing:
        raise Conflict(
            f"Permissions not present in database: {', '.join(missing)}",
            code="PERMISSIONS_NOT_SEEDED",
            details={"missing": missing},
        )
    return list(rows)


async def create_role(
    db: AsyncSession,
    *,
    actor: AuthContext,
    name: str,
    description: str = "",
    permissions: list[str] | None = None,
    request: Request | None = None,
) -> Role:
    """Create a custom role. System role names are reserved."""
    name_clean = name.strip()
    existing = (
        await db.execute(select(Role.id).where(Role.name == name_clean))
    ).scalar_one_or_none()
    if existing is not None:
        raise Conflict(f"Role '{name_clean}' already exists", code="ROLE_NAME_TAKEN")
    if name_clean in SYSTEM_ROLES:
        raise Conflict("System roles are immutable", code="SYSTEM_ROLE_IMMUTABLE")

    requested = sorted(set(permissions or []))
    validate_codenames(requested)
    perm_rows = await _resolve_permission_rows(db, requested)

    now = datetime.now(UTC)
    role = Role(
        name=name_clean,
        description=description.strip(),
        is_system=False,
        created_at=now,
        updated_at=now,
    )
    role.permissions = perm_rows
    db.add(role)
    await db.flush()

    await audit_service.record(
        db,
        actor,
        action="role.create",
        resource_type="role",
        resource_id=role.id,
        metadata={"name": name_clean, "permissions": requested},
        request=request,
    )
    await event_bus.publish(
        db,
        type="PERMISSION_CHANGED",
        message=f"Role {name_clean} created with {len(perm_rows)} permission(s)",
        actor_id=actor.user_id,
        actor_type=ActorType.USER,
        resource_type="role",
        resource_id=str(role.id),
    )
    return role


async def update_role(
    db: AsyncSession,
    *,
    actor: AuthContext,
    role_id: UUID,
    name: str | None = None,
    description: str | None = None,
    permissions: list[str] | None = None,
    request: Request | None = None,
) -> Role:
    """Update a custom role. System roles are immutable."""
    role = await get_role(db, role_id)
    if role.is_system:
        raise Conflict("System roles are immutable", code="SYSTEM_ROLE_IMMUTABLE")

    name_clean = name.strip() if name else None
    if name_clean and name_clean != role.name:
        clash = (
            await db.execute(select(Role.id).where(Role.name == name_clean))
        ).scalar_one_or_none()
        if clash is not None:
            raise Conflict(f"Role '{name_clean}' already exists", code="ROLE_NAME_TAKEN")

    old_codenames = {p.codename for p in role.permissions}
    new_codenames: set[str] | None = None
    perm_rows: list[Permission] | None = None
    if permissions is not None:
        new_codenames = set(permissions)
        validate_codenames(sorted(new_codenames - old_codenames))
        perm_rows = await _resolve_permission_rows(db, sorted(new_codenames))

    changed_permissions = new_codenames is not None and new_codenames != old_codenames

    if name_clean:
        role.name = name_clean
    if description is not None:
        role.description = description.strip()
    if perm_rows is not None:
        role.permissions = perm_rows
    await db.flush()

    metadata: dict[str, object] = {"name": role.name}
    if changed_permissions:
        assert new_codenames is not None
        metadata["permissions"] = {
            "added": sorted(new_codenames - old_codenames),
            "removed": sorted(old_codenames - new_codenames),
        }
    await audit_service.record(
        db,
        actor,
        action="role.update",
        resource_type="role",
        resource_id=role.id,
        metadata=metadata,
        request=request,
    )
    if changed_permissions:
        await event_bus.publish(
            db,
            type="PERMISSION_CHANGED",
            message=f"Permissions changed on role {role.name}",
            level=EventLevel.WARNING,
            actor_id=actor.user_id,
            actor_type=ActorType.USER,
            resource_type="role",
            resource_id=str(role.id),
            data={"added": sorted((new_codenames or set()) - old_codenames)},
        )
    return role


async def delete_role(
    db: AsyncSession, *, actor: AuthContext, role_id: UUID, request: Request | None = None
) -> None:
    """Delete a custom role that has no assigned users."""
    role = await get_role(db, role_id)
    if role.is_system:
        raise Conflict("System roles are immutable", code="SYSTEM_ROLE_IMMUTABLE")
    assigned = int(
        (
            await db.execute(select(func.count()).select_from(User).where(User.role_id == role_id))
        ).scalar_one()
    )
    if assigned > 0:
        raise Conflict(f"Role still assigned to {assigned} user(s)", code="ROLE_IN_USE")

    name = role.name
    await db.delete(role)
    await db.flush()
    await audit_service.record(
        db,
        actor,
        action="role.delete",
        resource_type="role",
        resource_id=role_id,
        metadata={"name": name},
        request=request,
    )
    await event_bus.publish(
        db,
        type="PERMISSION_CHANGED",
        message=f"Role {name} deleted",
        level=EventLevel.WARNING,
        actor_id=actor.user_id,
        actor_type=ActorType.USER,
        resource_type="role",
        resource_id=str(role_id),
    )
