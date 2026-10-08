"""Secrets manager: encrypted values with metadata-only reads.

Plaintext exists only transiently in memory: it is accepted on create/rotate,
Fernet-encrypted at rest and never returned by any read path. Deployment
resolution happens server-side via :func:`resolve_secrets_for_environment`,
which is INTERNAL USE ONLY and must never be exposed through an API route.

Phase 2 adds layered scope — **environment > project > organization**, most
specific wins — and append-only history. ``Secret`` is the logical secret;
:class:`~app.models.secrets.SecretVersion` rows are immutable values. Rotation
appends a version and moves the parent pointer; it never overwrites history.
Rollback appends a *new* version carrying a prior value, so no version is ever
rewritten or deleted.

Resolution is **fail-closed**: a ``${secret:KEY}`` reference that names no row at
any scope level, or whose ciphertext cannot be decrypted, raises
:class:`SecretResolutionError` rather than resolving to ``""``. A deployment must
never proceed without the credentials its configuration names.

Authorization: reading metadata needs ``secret.read``; *consuming* a secret is a
deploy-time concern gated by the deploy permission chain (``deployment.create``),
never by ``secret.read``. No path returns a value.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass
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
from app.models import DeploymentEnvironment, Project, Secret, SecretVersion, User
from app.models.enums import ActorType
from app.services import audit_service, event_bus
from app.services.config_service import collect_secret_refs

if TYPE_CHECKING:
    from fastapi import Request

log = get_logger("nexusops.secrets")


def _actor_type(ctx: AuthContext) -> ActorType:
    return ActorType.API_KEY if ctx.api_key is not None else ActorType.USER


async def _project_exists(db: AsyncSession, project_id: uuid.UUID) -> None:
    exists = (
        await db.execute(select(Project.id).where(Project.id == project_id))
    ).scalar_one_or_none()
    if exists is None:
        raise NotFound("Project not found", code="PROJECT_NOT_FOUND")


async def resolve_secret_scope(
    db: AsyncSession,
    *,
    project_id: uuid.UUID | None,
    environment_id: uuid.UUID | None,
) -> tuple[uuid.UUID | None, uuid.UUID | None]:
    """Validate and normalise a requested secret scope.

    Returns ``(project_id, environment_id)``. An environment scope requires a
    real environment and implies its project; a mismatched ``project_id`` is a
    404 (never a silent re-scope). The environment is read through the ORM, so
    both the tenancy guard and RLS keep another organization's environment
    invisible — a known UUID buys nothing.
    """
    if environment_id is not None:
        environment = await db.get(DeploymentEnvironment, environment_id)
        if environment is None:
            raise NotFound("Environment not found", code="ENVIRONMENT_NOT_FOUND")
        if project_id is not None and project_id != environment.project_id:
            raise NotFound("Environment not found in this project", code="ENVIRONMENT_NOT_FOUND")
        return environment.project_id, environment.id
    if project_id is not None:
        await _project_exists(db, project_id)
        return project_id, None
    return None, None


def _detail(secret: Secret, rotated_by_email: str | None) -> dict[str, Any]:
    """Serialise secret metadata. No value-bearing field may appear here."""
    return {
        "id": secret.id,
        "key": secret.key,
        "version": secret.version,
        "digest": secret.digest,
        "description": secret.description,
        "project_id": secret.project_id,
        "environment_id": secret.environment_id,
        "rotated_at": secret.rotated_at,
        "rotated_by_email": rotated_by_email,
        "created_at": secret.created_at,
        "updated_at": secret.updated_at,
    }


def _version_detail(version: SecretVersion, created_by_email: str | None) -> dict[str, Any]:
    """Serialise one version's metadata. ``ciphertext`` is never included."""
    return {
        "id": version.id,
        "secret_id": version.secret_id,
        "version": version.version,
        "digest": version.digest,
        "created_by_email": created_by_email,
        "created_at": version.created_at,
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
    environment_id: uuid.UUID | None = None,
    params: PageParams,
) -> tuple[list[dict[str, Any]], int]:
    """Paginated metadata list, optionally filtered by key substring / scope."""
    filters: list[ColumnElement[bool]] = []
    if q:
        filters.append(Secret.key.ilike(f"%{q}%"))
    if environment_id is not None:
        filters.append(Secret.environment_id == environment_id)
    elif project_id is not None:
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


async def list_secret_versions(db: AsyncSession, secret_id: uuid.UUID) -> list[dict[str, Any]]:
    """Every version of a secret, newest first. Metadata only — never a value."""
    await get_secret(db, secret_id)  # 404 when absent or out of tenant scope
    rows = (
        await db.execute(
            select(SecretVersion, User.email)
            .outerjoin(User, User.id == SecretVersion.created_by_id)
            .where(SecretVersion.secret_id == secret_id)
            .order_by(SecretVersion.version.desc())
        )
    ).all()
    return [_version_detail(version, email) for version, email in rows]


# --- Mutations ------------------------------------------------------------------


async def create_secret(
    db: AsyncSession,
    ctx: AuthContext,
    *,
    key: str,
    value: str,
    project_id: uuid.UUID | None = None,
    environment_id: uuid.UUID | None = None,
    description: str = "",
    request: Request | None = None,
) -> Secret:
    """Encrypt and persist a new secret (plus its version-1 row).

    Raises ``Conflict(SECRET_EXISTS)`` on a duplicate key at the same scope.
    """
    scope_project, scope_environment = await resolve_secret_scope(
        db, project_id=project_id, environment_id=environment_id
    )

    secret = Secret(
        project_id=scope_project,
        environment_id=scope_environment,
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
            # Version 1 is written with the secret, in the same transaction, so
            # history and pointer can never disagree.
            db.add(
                SecretVersion(
                    secret_id=secret.id,
                    version=1,
                    ciphertext=secret.ciphertext,
                    digest=secret.digest,
                    created_by_id=ctx.user_id,
                )
            )
            await db.flush()
    except IntegrityError as exc:
        raise Conflict("A secret with this key already exists", code="SECRET_EXISTS") from exc

    await audit_service.record(
        db,
        ctx,
        action="secret.create",
        resource_type="secret",
        resource_id=secret.id,
        metadata={
            "key": key,
            "project_id": str(scope_project) if scope_project else None,
            "environment_id": str(scope_environment) if scope_environment else None,
        },
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
    log.info(
        "secret_created",
        key=key,
        project_id=str(scope_project) if scope_project else None,
        environment_id=str(scope_environment) if scope_environment else None,
    )
    return secret


async def _locked_secret(db: AsyncSession, secret_id: uuid.UUID) -> Secret:
    """Load a secret with ``FOR UPDATE`` so rotations serialize on the row.

    Two concurrent rotations must not compute the same next version. The row
    lock is the ordering point: the second transaction blocks, then re-reads the
    committed ``version`` before choosing its own, so versions are unique. The
    ``(secret_id, version)`` unique constraint is the database-level backstop.
    """
    secret = (
        await db.execute(select(Secret).where(Secret.id == secret_id).with_for_update())
    ).scalar_one_or_none()
    if secret is None:
        raise NotFound("Secret not found", code="SECRET_NOT_FOUND")
    return secret


async def rotate_secret(
    db: AsyncSession,
    ctx: AuthContext,
    secret_id: uuid.UUID,
    value: str,
    *,
    request: Request | None = None,
) -> Secret:
    """Append a new version and make it current — never overwrite the old one."""
    secret = await _locked_secret(db, secret_id)
    new_version = secret.version + 1
    ciphertext = encrypt_str(value)
    digest = digest_of(value)

    db.add(
        SecretVersion(
            secret_id=secret.id,
            version=new_version,
            ciphertext=ciphertext,
            digest=digest,
            created_by_id=ctx.user_id,
        )
    )
    secret.ciphertext = ciphertext
    secret.version = new_version
    secret.digest = digest
    secret.rotated_at = datetime.now(UTC)
    secret.rotated_by_id = ctx.user_id
    await db.flush()

    await audit_service.record(
        db,
        ctx,
        action="secret.rotate",
        resource_type="secret",
        resource_id=secret.id,
        metadata={"key": secret.key, "version": new_version},
        request=request,
    )
    await event_bus.publish(
        db,
        type="SECRET_UPDATED",
        message=f"Secret {secret.key} rotated to version {new_version}",
        actor_id=ctx.user_id,
        actor_type=_actor_type(ctx),
        resource_type="secret",
        resource_id=str(secret.id),
        data={"action": "rotate", "key": secret.key, "version": new_version},
    )
    log.info("secret_rotated", key=secret.key, version=new_version)
    return secret


async def rollback_secret(
    db: AsyncSession,
    ctx: AuthContext,
    secret_id: uuid.UUID,
    target_version: int,
    *,
    request: Request | None = None,
) -> Secret:
    """Make a previous version's value current **by appending a new version**.

    Non-destructive by construction: the target row is read, its ciphertext is
    carried onto a *new* version row, and every earlier version — including the
    one being replaced as current — stays exactly where it was. Rolling back to
    the current version is refused (it would add a no-op version).
    """
    secret = await _locked_secret(db, secret_id)
    target = (
        await db.execute(
            select(SecretVersion).where(
                SecretVersion.secret_id == secret.id,
                SecretVersion.version == target_version,
            )
        )
    ).scalar_one_or_none()
    if target is None:
        raise NotFound("Secret version not found", code="SECRET_VERSION_NOT_FOUND")
    if target_version == secret.version:
        raise Conflict(
            "That version is already current",
            code="SECRET_VERSION_CURRENT",
        )

    new_version = secret.version + 1
    db.add(
        SecretVersion(
            secret_id=secret.id,
            version=new_version,
            ciphertext=target.ciphertext,
            digest=target.digest,
            created_by_id=ctx.user_id,
        )
    )
    secret.ciphertext = target.ciphertext
    secret.digest = target.digest
    secret.version = new_version
    secret.rotated_at = datetime.now(UTC)
    secret.rotated_by_id = ctx.user_id
    await db.flush()

    await audit_service.record(
        db,
        ctx,
        action="secret.rollback",
        resource_type="secret",
        resource_id=secret.id,
        # Names and version numbers only — never a value.
        metadata={
            "key": secret.key,
            "rolled_back_to": target_version,
            "version": new_version,
        },
        request=request,
    )
    await event_bus.publish(
        db,
        type="SECRET_UPDATED",
        message=f"Secret {secret.key} rolled back to version {target_version}",
        actor_id=ctx.user_id,
        actor_type=_actor_type(ctx),
        resource_type="secret",
        resource_id=str(secret.id),
        data={
            "action": "rollback",
            "key": secret.key,
            "rolled_back_to": target_version,
            "version": new_version,
        },
    )
    log.info("secret_rolled_back", key=secret.key, target=target_version, version=new_version)
    return secret


async def delete_secret(
    db: AsyncSession,
    ctx: AuthContext,
    secret_id: uuid.UUID,
    *,
    request: Request | None = None,
) -> None:
    """Remove a secret permanently, with its version history (FK CASCADE)."""
    secret = await get_secret(db, secret_id)
    key, project_id, environment_id = secret.key, secret.project_id, secret.environment_id
    await db.delete(secret)
    await db.flush()

    await audit_service.record(
        db,
        ctx,
        action="secret.delete",
        resource_type="secret",
        resource_id=secret_id,
        metadata={
            "key": key,
            "project_id": str(project_id) if project_id else None,
            "environment_id": str(environment_id) if environment_id else None,
        },
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


class SecretResolutionError(Exception):
    """A ``${secret:KEY}`` reference could not be resolved. Fail-closed.

    Carries secret **key names** and failure reasons only — never a value, a
    ciphertext or a digest. The deployment engine renders ``reason`` into the
    deployment's ``failure_reason`` and audits the key lists.
    """

    def __init__(self, *, missing: Sequence[str], undecryptable: Sequence[str]) -> None:
        self.missing: tuple[str, ...] = tuple(sorted(missing))
        self.undecryptable: tuple[str, ...] = tuple(sorted(undecryptable))
        parts: list[str] = []
        if self.missing:
            parts.append("missing: " + ", ".join(self.missing))
        if self.undecryptable:
            parts.append("undecryptable: " + ", ".join(self.undecryptable))
        self.reason = "; ".join(parts)
        super().__init__(f"unresolved secret reference(s) ({self.reason})")


@dataclass(frozen=True, slots=True)
class SecretReference:
    """One successfully resolved reference: metadata for audit, no value."""

    key: str
    secret_id: uuid.UUID
    version: int


@dataclass(frozen=True, slots=True)
class ResolvedSecrets:
    """Outcome of resolving an environment's config references."""

    values: dict[str, str]
    references: tuple[SecretReference, ...] = ()


def _collect_refs(node: Any, refs: set[str]) -> None:
    """Backwards-compatible wrapper around :func:`config_service.collect_secret_refs`."""
    refs.update(collect_secret_refs(node))


def _scope_rank(secret: Secret, *, project_id: uuid.UUID, environment_id: uuid.UUID) -> int:
    """Specificity of a candidate row: environment (2) > project (1) > org (0)."""
    if secret.environment_id == environment_id:
        return 2
    if secret.project_id == project_id:
        return 1
    return 0


async def resolve_secrets_for_environment(
    db: AsyncSession, environment: DeploymentEnvironment
) -> ResolvedSecrets:
    """Resolve every ``${secret:KEY}`` reference an environment's config names.

    INTERNAL USE ONLY — invoked by the deployment engine before it runs a step.
    NEVER expose resolved values through any API endpoint, WS frame or log line.

    References are collected from the **effective** config (project config ⊕ the
    environment's overrides), and each key resolves at the most specific scope
    that defines it: environment > project > organization.

    **Fail-closed.** Every reference must resolve: a key with no row at any
    scope, or a ciphertext this ``ENCRYPTION_KEY`` cannot decrypt, raises
    :class:`SecretResolutionError` and the caller aborts the deployment before
    any step executes.
    """
    project_id = environment.project_id
    project_config = await db.scalar(select(Project.config).where(Project.id == project_id))

    refs: set[str] = set()
    _collect_refs(project_config or {}, refs)
    _collect_refs(environment.config or {}, refs)
    if not refs:
        return ResolvedSecrets(values={})

    rows = (
        await db.execute(
            select(Secret).where(
                Secret.key.in_(refs),
                or_(
                    Secret.environment_id == environment.id,
                    (Secret.project_id == project_id) & Secret.environment_id.is_(None),
                    Secret.project_id.is_(None) & Secret.environment_id.is_(None),
                ),
            )
        )
    ).scalars()

    best: dict[str, Secret] = {}
    best_rank: dict[str, int] = {}
    for secret in rows:
        rank = _scope_rank(secret, project_id=project_id, environment_id=environment.id)
        if rank > best_rank.get(secret.key, -1):
            best[secret.key] = secret
            best_rank[secret.key] = rank

    values: dict[str, str] = {}
    references: list[SecretReference] = []
    missing: list[str] = []
    undecryptable: list[str] = []

    for key in sorted(refs):
        found = best.get(key)
        if found is None:
            missing.append(key)
            continue
        try:
            values[key] = decrypt_str(found.ciphertext)
        except ValueError:
            log.error("secret_decrypt_failed", key=key, version=found.version)
            undecryptable.append(key)
            continue
        references.append(SecretReference(key=key, secret_id=found.id, version=found.version))

    if missing or undecryptable:
        # Key names + reasons only; values and ciphertext never touch the log.
        log.error(
            "secret_resolution_failed",
            environment=environment.slug,
            missing=missing,
            undecryptable=undecryptable,
        )
        raise SecretResolutionError(missing=missing, undecryptable=undecryptable)

    return ResolvedSecrets(values=values, references=tuple(references))
