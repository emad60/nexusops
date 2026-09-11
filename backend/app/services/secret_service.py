"""Secrets manager: encrypted values with metadata-only reads.

Plaintext exists only transiently in memory: it is accepted on create/rotate,
Fernet-encrypted at rest and never returned by any read path. Deployment
resolution happens server-side via :func:`resolve_secrets_for_environment`,
which is INTERNAL USE ONLY and must never be exposed through an API route.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AuthContext
from app.core.errors import Conflict, NotFound
from app.core.logging import get_logger
from app.core.pagination import PageParams
from app.core.security import decrypt_str, digest_of, encrypt_str
from app.models import Application, Project, Secret, User
from app.models.enums import ActorType
from app.schemas.secret import SECRET_REF_PATTERN
from app.services import audit_service, event_bus

if TYPE_CHECKING:
    from fastapi import Request

    from app.models import DeploymentEnvironment

log = get_logger("nexusops.secrets")


def _actor_type(ctx: AuthContext) -> ActorType:
    return ActorType.API_KEY if ctx.api_key is not None else ActorType.USER


async def _project_exists(db: AsyncSession, project_id: uuid.UUID) -> None:
    exists = (
        await db.execute(select(Project.id).where(Project.id == project_id))
    ).scalar_one_or_none()
    if exists is None:
        raise NotFound("Project not found", code="PROJECT_NOT_FOUND")


def _detail(secret: Secret, rotated_by_email: str | None) -> dict[str, Any]:
    """Serialise secret metadata. No value-bearing field may appear here."""
    return {
        "id": secret.id,
        "key": secret.key,
        "version": secret.version,
        "digest": secret.digest,
        "description": secret.description,
        "project_id": secret.project_id,
        "rotated_at": secret.rotated_at,
        "rotated_by_email": rotated_by_email,
        "created_at": secret.created_at,
        "updated_at": secret.updated_at,
    }


# --- Reads ---------------------------------------------------------------------


async def get_secret(db: AsyncSession, secret_id: uuid.UUID) -> Secret:
    """Load a secret row or raise NotFound."""
    secret = (await db.execute(select(Secret).where(Secret.id == secret_id))).scalar_one_or_none()
    if secret is None:
        raise NotFound("Secret not found", code="SECRET_NOT_FOUND")
    return secret


async def get_secret_detail(db: AsyncSession, secret_id: uuid.UUID) -> dict[str, Any]:
    """Metadata for one secret including the rotator's email when known."""
    row = (
        await db.execute(
            select(Secret, User.email)
            .outerjoin(User, User.id == Secret.rotated_by_id)
            .where(Secret.id == secret_id)
        )
    ).first()
    if row is None:
        raise NotFound("Secret not found", code="SECRET_NOT_FOUND")
    return _detail(row[0], row[1])


async def list_secrets(
    db: AsyncSession,
    *,
    q: str | None = None,
    project_id: uuid.UUID | None = None,
    params: PageParams,
) -> tuple[list[dict[str, Any]], int]:
    """Paginated metadata list, optionally filtered by key substring / scope."""
    filters: list[ColumnElement[bool]] = []
    if q:
        filters.append(Secret.key.ilike(f"%{q}%"))
    if project_id is not None:
        filters.append(Secret.project_id == project_id)

    count_stmt = select(func.count()).select_from(Secret).where(*filters)
    total = int((await db.execute(count_stmt)).scalar_one())

    rows = (
        await db.execute(
            select(Secret, User.email)
            .outerjoin(User, User.id == Secret.rotated_by_id)
            .where(*filters)
            .order_by(Secret.key.asc(), Secret.id.asc())
            .limit(params.limit)
            .offset(params.offset)
        )
    ).all()
    return [_detail(secret, email) for secret, email in rows], total


# --- Mutations ------------------------------------------------------------------


async def create_secret(
    db: AsyncSession,
    ctx: AuthContext,
    *,
    key: str,
    value: str,
    project_id: uuid.UUID | None = None,
    description: str = "",
    request: Request | None = None,
) -> Secret:
    """Encrypt and persist a new secret; audit + emit SECRET_UPDATED(create).

    Raises ``Conflict(SECRET_EXISTS)`` on duplicate (project, key) or global key.
    """
    if project_id is not None:
        await _project_exists(db, project_id)

    secret = Secret(
        project_id=project_id,
        key=key,
        ciphertext=encrypt_str(value),
        version=1,
        digest=digest_of(value),
        description=description,
        created_by_id=ctx.user_id,
        rotated_by_id=ctx.user_id,
        rotated_at=datetime.now(UTC),
    )
    try:
        async with db.begin_nested():
            db.add(secret)
            await db.flush()
    except IntegrityError as exc:
        raise Conflict("A secret with this key already exists", code="SECRET_EXISTS") from exc

    await audit_service.record(
        db,
        ctx,
        action="secret.create",
        resource_type="secret",
        resource_id=secret.id,
        metadata={"key": key, "project_id": str(project_id) if project_id else None},
        request=request,
    )
    await event_bus.publish(
        db,
        type="SECRET_UPDATED",
        message=f"Secret {key} created",
        actor_id=ctx.user_id,
        actor_type=_actor_type(ctx),
        resource_type="secret",
        resource_id=str(secret.id),
        data={"action": "create", "key": key},
    )
    log.info("secret_created", key=key, project_id=str(project_id) if project_id else None)
    return secret


async def rotate_secret(
    db: AsyncSession,
    ctx: AuthContext,
    secret_id: uuid.UUID,
    value: str,
    *,
    request: Request | None = None,
) -> Secret:
    """Re-encrypt a secret with a new value, bumping its version."""
    secret = await get_secret(db, secret_id)
    secret.ciphertext = encrypt_str(value)
    secret.version += 1
    secret.digest = digest_of(value)
    secret.rotated_at = datetime.now(UTC)
    secret.rotated_by_id = ctx.user_id
    await db.flush()

    await audit_service.record(
        db,
        ctx,
        action="secret.rotate",
        resource_type="secret",
        resource_id=secret.id,
        metadata={
            "key": secret.key,
            "version": secret.version,
            "project_id": str(secret.project_id),
        }
        if secret.project_id
        else {"key": secret.key, "version": secret.version},
        request=request,
    )
    await event_bus.publish(
        db,
        type="SECRET_UPDATED",
        message=f"Secret {secret.key} rotated to version {secret.version}",
        actor_id=ctx.user_id,
        actor_type=_actor_type(ctx),
        resource_type="secret",
        resource_id=str(secret.id),
        data={"action": "rotate", "key": secret.key, "version": secret.version},
    )
    log.info("secret_rotated", key=secret.key, version=secret.version)
    return secret


async def delete_secret(
    db: AsyncSession,
    ctx: AuthContext,
    secret_id: uuid.UUID,
    *,
    request: Request | None = None,
) -> None:
    """Remove a secret permanently."""
    secret = await get_secret(db, secret_id)
    key, project_id = secret.key, secret.project_id
    await db.delete(secret)
    await db.flush()

    await audit_service.record(
        db,
        ctx,
        action="secret.delete",
        resource_type="secret",
        resource_id=secret_id,
        metadata={"key": key, "project_id": str(project_id) if project_id else None},
        request=request,
    )
    await event_bus.publish(
        db,
        type="SECRET_UPDATED",
        message=f"Secret {key} deleted",
        actor_id=ctx.user_id,
        actor_type=_actor_type(ctx),
        resource_type="secret",
        resource_id=str(secret_id),
        data={"action": "delete", "key": key},
    )
    log.info("secret_deleted", key=key)


# --- Deployment-time resolution (INTERNAL ONLY) ---------------------------------


def _collect_refs(node: Any, refs: set[str]) -> None:
    """Recursively collect ``${secret:KEY}`` references from config values."""
    if isinstance(node, dict):
        for item in node.values():
            _collect_refs(item, refs)
    elif isinstance(node, (list, tuple)):
        for item in node:
            _collect_refs(item, refs)
    elif isinstance(node, str):
        refs.update(SECRET_REF_PATTERN.findall(node))


async def resolve_secrets_for_environment(
    db: AsyncSession, environment: DeploymentEnvironment
) -> dict[str, str]:
    """Resolve every ``${secret:KEY}`` reference in an environment's config.

    INTERNAL USE ONLY — invoked by the deployment engine while executing steps.
    NEVER expose resolved values through any API endpoint, WS frame or log line.
    Project-scoped keys win over global ones; unresolved or undecryptable
    references resolve to "" with a warning so deploys degrade instead of crash.
    """
    refs: set[str] = set()
    _collect_refs(environment.config or {}, refs)
    if not refs:
        return {}

    project_id = await db.scalar(
        select(Application.project_id).where(Application.id == environment.application_id)
    )
    rows = (
        await db.execute(
            select(Secret).where(
                Secret.key.in_(refs),
                or_(Secret.project_id == project_id, Secret.project_id.is_(None)),
            )
        )
    ).scalars()

    best: dict[str, Secret] = {}
    for secret in rows:
        current = best.get(secret.key)
        # Prefer the project-scoped row over the global fallback.
        if current is None or (
            secret.project_id == project_id and current.project_id != project_id
        ):
            best[secret.key] = secret

    resolved: dict[str, str] = {}
    for key in sorted(refs):
        found = best.get(key)
        if found is None:
            log.warning("secret_reference_missing", key=key, environment=environment.slug)
            resolved[key] = ""
            continue
        try:
            resolved[key] = decrypt_str(found.ciphertext)
        except ValueError:
            log.error("secret_decrypt_failed", key=key, version=found.version)
            resolved[key] = ""
    return resolved
