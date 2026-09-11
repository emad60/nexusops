"""API key lifecycle: creation with scope validation, listing, revocation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID

from fastapi import Request
from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext
from app.core.errors import NotFound, UnprocessableEntity
from app.core.pagination import PageParams, paginate
from app.core.permissions import ALL_CODENAMES, WILDCARD
from app.core.security import generate_api_key
from app.models import ApiKey
from app.models.enums import ActorType, EventLevel
from app.services import audit_service, event_bus


def validate_scopes(scopes: list[str]) -> list[str]:
    """Validate + normalise scopes; returns the deduplicated list.

    Accepts exact registered codenames, prefix wildcards (``server.*``) and the
    global ``*``. Unknown literal codenames are rejected.
    """
    invalid: list[str] = []
    for scope in scopes:
        if scope == WILDCARD:
            continue
        if scope.endswith("*"):
            prefix = scope[:-1]
            if any(codename.startswith(prefix) for codename in ALL_CODENAMES):
                continue
        elif scope in ALL_CODENAMES:
            continue
        invalid.append(scope)
    if invalid:
        raise UnprocessableEntity(
            f"Unknown scopes: {', '.join(sorted(set(invalid)))}",
            code="UNKNOWN_SCOPE",
            details={"unknown": sorted(set(invalid))},
        )
    return list(dict.fromkeys(scopes))


async def create_api_key(
    db: AsyncSession,
    *,
    actor: AuthContext,
    user_id: UUID,
    name: str,
    scopes: list[str],
    expires_in_days: int | None = None,
    request: Request | None = None,
) -> tuple[ApiKey, str]:
    """Create a key for *user_id*. Returns ``(row, raw_key)`` — raw shown once."""
    clean_scopes = validate_scopes(scopes)
    raw_key, key_prefix, key_hash = generate_api_key()
    now = datetime.now(UTC)
    key = ApiKey(
        user_id=user_id,
        name=name.strip()[:120],
        key_prefix=key_prefix,
        key_hash=key_hash,
        scopes=clean_scopes,
        expires_at=(now + timedelta(days=expires_in_days) if expires_in_days is not None else None),
        created_at=now,
        updated_at=now,
    )
    db.add(key)
    await db.flush()

    await audit_service.record(
        db,
        actor,
        action="apikey.create",
        resource_type="api_key",
        resource_id=key.id,
        metadata={"name": key.name, "key_prefix": key_prefix, "scopes": clean_scopes},
        request=request,
    )
    await event_bus.publish(
        db,
        type="API_KEY_CREATED",
        message=f"API key '{key.name}' created",
        actor_id=actor.user_id,
        actor_type=ActorType.USER if actor.api_key is None else ActorType.API_KEY,
        resource_type="api_key",
        resource_id=str(key.id),
        data={"owner_id": str(user_id), "key_prefix": key_prefix},
    )
    return key, raw_key


async def list_api_keys(
    db: AsyncSession, *, owner_id: UUID, params: PageParams
) -> tuple[list[ApiKey], int]:
    """Live (non-revoked) keys owned by *owner_id*, newest first."""
    stmt = (
        select(ApiKey)
        .where(ApiKey.user_id == owner_id, ApiKey.revoked_at.is_(None))
        .order_by(ApiKey.created_at.desc())
    )
    return await paginate(db, stmt, params)


async def revoke_api_key(
    db: AsyncSession,
    *,
    actor: AuthContext,
    key_id: UUID,
    owner_id: UUID,
    request: Request | None = None,
) -> ApiKey:
    """Revoke a key owned by *owner_id*. Foreign keys look like NotFound (no leak)."""
    key = (
        await db.execute(select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == owner_id))
    ).scalar_one_or_none()
    if key is None:
        raise NotFound("API key not found", code="API_KEY_NOT_FOUND")
    if key.revoked_at is None:
        now = datetime.now(UTC)
        key.revoked_at = now
        await db.flush()
        await audit_service.record(
            db,
            actor,
            action="apikey.revoke",
            resource_type="api_key",
            resource_id=key.id,
            metadata={"name": key.name, "key_prefix": key.key_prefix},
            request=request,
        )
        await event_bus.publish(
            db,
            type="API_KEY_REVOKED",
            message=f"API key '{key.name}' revoked",
            level=EventLevel.WARNING,
            actor_id=actor.user_id,
            actor_type=ActorType.USER if actor.api_key is None else ActorType.API_KEY,
            resource_type="api_key",
            resource_id=str(key.id),
        )
    return key


async def revoke_all_for_user(db: AsyncSession, *, user_id: UUID) -> int:
    """Revoke every live key of a user (used on deactivation). Returns count."""
    result = await db.execute(
        update(ApiKey)
        .where(ApiKey.user_id == user_id, ApiKey.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )
    return int(cast(CursorResult[Any], result).rowcount or 0)
