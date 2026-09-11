"""Role and permission-registry schemas."""

from __future__ import annotations

from pydantic import Field

from app.models import Role
from app.schemas.base import APIModel, OutModel


class PermissionOut(APIModel):
    group: str
    codename: str
    description: str


class RoleOut(OutModel):
    name: str
    description: str
    is_system: bool
    permissions: list[str]

    @classmethod
    def from_role(cls, role: Role) -> RoleOut:
        """Build from an ORM role whose ``permissions`` relationship is loaded."""
        return cls(
            id=role.id,
            created_at=role.created_at,
            name=role.name,
            description=role.description,
            is_system=role.is_system,
            permissions=sorted(p.codename for p in role.permissions),
        )


class RoleCreateRequest(APIModel):
    name: str = Field(min_length=1, max_length=64)
    description: str = Field(default="", max_length=2000)
    permissions: list[str] = Field(default_factory=list)


class RoleUpdateRequest(APIModel):
    """PATCH semantics: ``None`` means "leave unchanged"."""

    name: str | None = Field(default=None, min_length=1, max_length=64)
    description: str | None = Field(default=None, max_length=2000)
    permissions: list[str] | None = None
