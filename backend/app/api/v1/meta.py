"""Instance metadata: version, mode, and the caller's effective capabilities.

The SPA calls this once after login to learn which UI surfaces to render.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import DbSessionDep, OptionalUser
from app.core.config import get_settings
from app.schemas.meta import EVENT_TYPES, MetaOut
from app.services import auth_service

meta_router = APIRouter(prefix="/meta", tags=["meta"])


@meta_router.get("", response_model=MetaOut)
async def get_meta(db: DbSessionDep, ctx: OptionalUser) -> MetaOut:
    """Public metadata; identity fields appear only for valid credentials."""
    settings = get_settings()
    out = MetaOut(
        environment=settings.environment,
        simulation_mode=settings.simulation_mode,
        event_types=list(EVENT_TYPES),
        bootstrap_available=await auth_service.count_users(db) == 0,
    )

    if ctx is None:
        return out

    if ctx.user.is_superadmin:
        out.permissions = ["*"]
    else:
        # User.role and Role.permissions are both lazy="selectin", so after any
        # query-loaded user these attributes are already in memory — no IO
        # needed (mirrors deps._load_permissions; no AsyncAttrs on User's Base).
        role = ctx.user.role
        out.permissions = sorted(p.codename for p in role.permissions) if role else []
        out.role = role.name if role else None
    out.is_superadmin = ctx.user.is_superadmin
    return out
