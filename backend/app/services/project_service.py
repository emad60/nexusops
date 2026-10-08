"""Delivery domain services: projects, applications and their environments.

All object-level authorization happens here: IDs are never trusted alone —
nested resources are resolved through their parents and 404 when the parent
link does not hold.
"""

from __future__ import annotations

import re
import uuid
from typing import Any

from fastapi import Request
from sqlalchemy import ColumnElement, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.api.deps import AuthContext
from app.core.errors import Conflict, NotFound
from app.core.logging import get_logger
from app.core.pagination import PageParams, paginate
from app.models import (
    Application,
    Deployment,
    DeploymentEnvironment,
    Project,
    Secret,
    Server,
)
from app.models.enums import ActorType
from app.schemas.application import ApplicationCreate, ApplicationUpdate
from app.schemas.environment import EnvironmentCreate, EnvironmentUpdate
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services import audit_service, event_bus
from app.services.config_service import collect_secret_refs, effective_config

log = get_logger("nexusops.delivery")

_SLUG_RE = re.compile(r"[^a-z0-9]+")
_NAME_MAX = {"application": 140, "environment": 84}


def slugify(raw: str, fallback: str, max_len: int) -> str:
    """Lowercase kebab-case slug safe for URL segments."""
    cleaned = _SLUG_RE.sub("-", raw.lower()).strip("-")
    return (cleaned or fallback)[:max_len]


def actor_of(ctx: AuthContext | None) -> tuple[uuid.UUID | None, ActorType]:
    """Map a request auth context onto (actor_id, actor_type)."""
    if ctx is None:
        return None, ActorType.SYSTEM
    try:
        return ctx.user_id, ActorType(ctx.actor_type)
    except ValueError:
        return ctx.user_id, ActorType.USER


async def _unique_slug(
    db: AsyncSession,
    *,
    column: Any,
    parent_column: ColumnElement[uuid.UUID] | InstrumentedAttribute[uuid.UUID],
    parent_id: uuid.UUID,
    base: str,
    kind: str,
) -> str:
    """Return ``base`` or the first ``base-N`` variant unique under the parent."""
    candidate, suffix = base, 1
    while True:
        taken = await db.scalar(
            select(column).where(parent_column == parent_id, column == candidate)
        )
        if taken is None:
            return candidate
        stem = base[: max(1, _NAME_MAX[kind] - len(str(suffix)) - 1)]
        suffix += 1
        candidate = f"{stem}-{suffix}"


async def _ensure_unique(
    db: AsyncSession,
    column: Any,
    condition: ColumnElement[bool],
    code: str,
    message: str,
) -> None:
    """Conflict when an ORM row matching *condition* exists.

    Selects a mapped **column** on purpose: the tenancy guard applies tenant
    filtering to ORM selects and refuses a bare Core ``select(1)`` on a
    tenant-owned table, so an existence probe has to name a mapped attribute to
    stay inside the org scope.
    """
    if await db.scalar(select(column).where(condition)) is not None:
        raise Conflict(message, code=code)


def _integrity_conflict(exc: IntegrityError, code: str, message: str) -> Conflict:
    log.warning("delivery_integrity_violation", code=code, error=str(exc.orig))
    return Conflict(message, code=code)


async def _apply_update(db: AsyncSession, obj: Any, data: dict[str, Any]) -> None:
    for key, value in data.items():
        setattr(obj, key, value)
    await db.flush()


# --- Projects -----------------------------------------------------------------


async def get_project(db: AsyncSession, project_id: uuid.UUID) -> Project:
    project = await db.get(Project, project_id)
    if project is None:
        raise NotFound("Project not found")
    return project


async def list_projects(db: AsyncSession, params: PageParams) -> tuple[list[Project], int]:
    stmt = select(Project).order_by(Project.name.asc())
    return await paginate(db, stmt, params)


async def create_project(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    payload: ProjectCreate,
    request: Request | None = None,
) -> Project:
    owner_id = payload.owner_id or (ctx.user_id if ctx else None)
    project = Project(
        name=payload.name.strip(),
        description=payload.description,
        repository_url=payload.repository_url,
        default_branch=payload.default_branch or "main",
        owner_id=owner_id,
        config=dict(payload.config),
    )
    # Initialize the collection while the object is still pending: assigning an
    # unloaded relationship AFTER flush would trigger a lazy load, which is
    # illegal from sync serialization. Pending objects initialize collections
    # without IO, and the (provably empty) set stays loaded for serialization.
    project.applications = []
    project.environments = []
    db.add(project)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise _integrity_conflict(exc, "DUPLICATE_NAME", "A project with this name exists") from exc
    actor_id, actor_type = actor_of(ctx)
    await event_bus.publish(
        db,
        type="PROJECT_CREATED",
        message=f"Project {project.name} created",
        actor_id=actor_id,
        actor_type=actor_type,
        resource_type="project",
        resource_id=str(project.id),
    )
    await audit_service.record(
        db,
        ctx,
        action="project.create",
        resource_type="project",
        resource_id=project.id,
        metadata={"name": project.name},
        request=request,
    )
    return project


async def update_project(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    request: Request | None = None,
) -> Project:
    project = await get_project(db, project_id)
    data = payload.model_dump(exclude_unset=True, exclude_none=True)
    if data.get("name") and data["name"] != project.name:
        await _ensure_unique(
            db,
            Project.id,
            (Project.name == data["name"]) & (Project.id != project.id),
            "DUPLICATE_NAME",
            "A project with this name exists",
        )
        data["name"] = data["name"].strip()
    try:
        await _apply_update(db, project, data)
    except IntegrityError as exc:
        raise _integrity_conflict(exc, "DUPLICATE_NAME", "A project with this name exists") from exc
    await audit_service.record(
        db,
        ctx,
        action="project.update",
        resource_type="project",
        resource_id=project.id,
        metadata={"fields": sorted(data)},
        request=request,
    )
    return project


async def delete_project(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    project_id: uuid.UUID,
    request: Request | None = None,
) -> None:
    project = await get_project(db, project_id)
    name = project.name
    await db.delete(project)
    await db.flush()
    await event_bus.publish(
        db,
        type="PROJECT_DELETED",
        message=f"Project {name} deleted",
        resource_type="project",
        resource_id=str(project.id),
    )
    await audit_service.record(
        db,
        ctx,
        action="project.delete",
        resource_type="project",
        resource_id=project.id,
        metadata={"name": name},
        request=request,
    )


async def latest_deployments_by_application(
    db: AsyncSession, application_ids: list[uuid.UUID]
) -> dict[uuid.UUID, Deployment]:
    """Latest (max number) deployment per application via a grouped subquery."""
    if not application_ids:
        return {}
    top = (
        select(
            Deployment.application_id.label("app_id"),
            func.max(Deployment.number).label("top_number"),
        )
        .where(Deployment.application_id.in_(application_ids))
        .group_by(Deployment.application_id)
        .subquery()
    )
    stmt = select(Deployment).join(
        top,
        (Deployment.application_id == top.c.app_id) & (Deployment.number == top.c.top_number),
    )
    rows = (await db.execute(stmt)).scalars().all()
    return {row.application_id: row for row in rows}


# --- Applications ---------------------------------------------------------------


async def get_application(db: AsyncSession, application_id: uuid.UUID) -> Application:
    application = await db.get(Application, application_id)
    if application is None:
        raise NotFound("Application not found")
    return application


async def get_scoped_application(
    db: AsyncSession, project_id: uuid.UUID, application_id: uuid.UUID
) -> Application:
    application = await db.get(Application, application_id)
    if application is None or application.project_id != project_id:
        raise NotFound("Application not found in this project")
    return application


async def list_applications(
    db: AsyncSession, project_id: uuid.UUID, params: PageParams
) -> tuple[list[Application], int]:
    stmt = (
        select(Application).where(Application.project_id == project_id).order_by(Application.name)
    )
    return await paginate(db, stmt, params)


async def create_application(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    project_id: uuid.UUID,
    payload: ApplicationCreate,
    request: Request | None = None,
) -> Application:
    project = await get_project(db, project_id)
    base_slug = slugify(payload.name, "app", _NAME_MAX["application"])
    slug = await _unique_slug(
        db,
        column=Application.slug,
        parent_column=Application.project_id,
        parent_id=project.id,
        base=base_slug,
        kind="application",
    )
    application = Application(
        project_id=project.id,
        name=payload.name.strip(),
        slug=slug,
        description=payload.description,
        repository_url=payload.repository_url or project.repository_url,
        build_config=payload.build_config,
    )
    db.add(application)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise _integrity_conflict(
            exc, "DUPLICATE_NAME", "An application with this name exists in the project"
        ) from exc
    await event_bus.publish(
        db,
        type="APPLICATION_CREATED",
        message=f"Application {application.name} created in project {project.name}",
        resource_type="application",
        resource_id=str(application.id),
        data={"project_id": str(project.id), "slug": slug},
    )
    await audit_service.record(
        db,
        ctx,
        action="application.create",
        resource_type="application",
        resource_id=application.id,
        metadata={"name": application.name, "project": project.name},
        request=request,
    )
    return application


async def update_application(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    project_id: uuid.UUID,
    application_id: uuid.UUID,
    payload: ApplicationUpdate,
    request: Request | None = None,
) -> Application:
    application = await get_scoped_application(db, project_id, application_id)
    data = payload.model_dump(exclude_unset=True, exclude_none=True)
    if data.get("name") and data["name"] != application.name:
        base_slug = slugify(data["name"], "app", _NAME_MAX["application"])
        data["name"] = data["name"].strip()
        data["slug"] = await _unique_slug(
            db,
            column=Application.slug,
            parent_column=Application.project_id,
            parent_id=application.project_id,
            base=base_slug,
            kind="application",
        )
    try:
        await _apply_update(db, application, data)
    except IntegrityError as exc:
        raise _integrity_conflict(
            exc, "DUPLICATE_NAME", "An application with this name exists in the project"
        ) from exc
    await audit_service.record(
        db,
        ctx,
        action="application.update",
        resource_type="application",
        resource_id=application.id,
        metadata={"fields": sorted(data)},
        request=request,
    )
    return application


async def delete_application(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    project_id: uuid.UUID,
    application_id: uuid.UUID,
    request: Request | None = None,
) -> None:
    application = await get_scoped_application(db, project_id, application_id)
    name = application.name
    await db.delete(application)
    await db.flush()
    await event_bus.publish(
        db,
        type="APPLICATION_DELETED",
        message=f"Application {name} deleted",
        resource_type="application",
        resource_id=str(application.id),
    )
    await audit_service.record(
        db,
        ctx,
        action="application.delete",
        resource_type="application",
        resource_id=application.id,
        metadata={"name": name},
        request=request,
    )


# --- Environments (project-scoped, Phase 2) -------------------------------------


async def get_environment(db: AsyncSession, environment_id: uuid.UUID) -> DeploymentEnvironment:
    environment = await db.get(DeploymentEnvironment, environment_id)
    if environment is None:
        raise NotFound("Environment not found", code="ENVIRONMENT_NOT_FOUND")
    return environment


async def get_scoped_environment(
    db: AsyncSession, project_id: uuid.UUID, environment_id: uuid.UUID
) -> DeploymentEnvironment:
    """Resolve an environment **through its project**.

    A known environment UUID is not enough: the link to the project in the path
    must hold, or this is a 404. That is what makes knowing an id worthless
    across projects and, with the guard + RLS beneath it, across tenants.
    """
    environment = await db.get(DeploymentEnvironment, environment_id)
    if environment is None or environment.project_id != project_id:
        raise NotFound("Environment not found in this project", code="ENVIRONMENT_NOT_FOUND")
    return environment


async def list_environments(
    db: AsyncSession, project_id: uuid.UUID, params: PageParams
) -> tuple[list[DeploymentEnvironment], int]:
    # Resolve the project first: an unknown or out-of-tenant project id is a 404,
    # never a 200 with an empty list (which would confirm nothing but would also
    # make the route's behaviour depend on whether the caller guessed right).
    await get_project(db, project_id)
    stmt = (
        select(DeploymentEnvironment)
        .where(DeploymentEnvironment.project_id == project_id)
        .order_by(DeploymentEnvironment.name)
    )
    return await paginate(db, stmt, params)


async def list_project_environments(
    db: AsyncSession, project_id: uuid.UUID
) -> list[DeploymentEnvironment]:
    """Every environment of a project (unpaginated) for the project detail view."""
    rows = (
        await db.execute(
            select(DeploymentEnvironment)
            .where(DeploymentEnvironment.project_id == project_id)
            .order_by(DeploymentEnvironment.name)
        )
    ).scalars()
    return list(rows)


async def environment_detail(db: AsyncSession, environment: DeploymentEnvironment) -> dict:
    """Environment detail payload: layered config + counts, never secret values.

    ``secret_references`` are key **names** the environment's effective config
    names — names are not secrets. Values never leave the resolver.
    """
    project = await get_project(db, environment.project_id)
    project_config = dict(project.config or {})
    environment_config = dict(environment.config or {})
    effective = effective_config(project_config, environment_config)

    application_count = int(
        await db.scalar(
            select(func.count())
            .select_from(Application)
            .where(Application.project_id == environment.project_id)
        )
        or 0
    )
    deployment_count = int(
        await db.scalar(
            select(func.count())
            .select_from(Deployment)
            .where(Deployment.environment_id == environment.id)
        )
        or 0
    )
    secret_count = int(
        await db.scalar(
            select(func.count()).select_from(Secret).where(Secret.environment_id == environment.id)
        )
        or 0
    )
    return {
        "project_config": project_config,
        "effective_config": effective,
        "secret_references": collect_secret_refs(effective),
        "application_count": application_count,
        "deployment_count": deployment_count,
        "secret_count": secret_count,
    }


async def _check_server(db: AsyncSession, server_id: uuid.UUID | None) -> uuid.UUID | None:
    if server_id is not None and await db.get(Server, server_id) is None:
        raise NotFound("Server not found", code="SERVER_NOT_FOUND")
    return server_id


async def create_environment(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    project_id: uuid.UUID,
    payload: EnvironmentCreate,
    request: Request | None = None,
) -> DeploymentEnvironment:
    project = await get_project(db, project_id)
    server_id = await _check_server(db, payload.server_id)
    # A duplicate *name* in the project is a conflict, not a silent
    # ``production-2``. Slug suffixes stay reserved for the genuine case of two
    # different names that slugify alike.
    await _ensure_unique(
        db,
        DeploymentEnvironment.id,
        (DeploymentEnvironment.project_id == project.id)
        & (DeploymentEnvironment.name == payload.name.strip()),
        "DUPLICATE_NAME",
        "An environment with this name exists in the project",
    )
    base_slug = slugify(payload.name, "env", _NAME_MAX["environment"])
    slug = await _unique_slug(
        db,
        column=DeploymentEnvironment.slug,
        parent_column=DeploymentEnvironment.project_id,
        parent_id=project.id,
        base=base_slug,
        kind="environment",
    )
    environment = DeploymentEnvironment(
        project_id=project.id,
        name=payload.name.strip(),
        slug=slug,
        environment_type=payload.environment_type,
        server_id=server_id,
        healthcheck_path=payload.healthcheck_path,
        auto_deploy=payload.auto_deploy,
        config=dict(payload.config),
    )
    db.add(environment)
    try:
        await db.flush()
    except IntegrityError as exc:
        raise _integrity_conflict(
            exc, "DUPLICATE_NAME", "An environment with this name exists in the project"
        ) from exc
    await event_bus.publish(
        db,
        type="ENVIRONMENT_CREATED",
        message=f"Environment {environment.name} created in project {project.name}",
        resource_type="deployment_environment",
        resource_id=str(environment.id),
        data={"project_id": str(project.id), "slug": slug},
    )
    await audit_service.record(
        db,
        ctx,
        action="environment.create",
        resource_type="deployment_environment",
        resource_id=environment.id,
        # Config holds references only; redact_mapping guards defence-in-depth.
        metadata={
            "name": environment.name,
            "project": project.name,
            "environment_type": str(environment.environment_type),
        },
        request=request,
    )
    return environment


async def update_environment(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    project_id: uuid.UUID,
    environment_id: uuid.UUID,
    payload: EnvironmentUpdate,
    request: Request | None = None,
) -> DeploymentEnvironment:
    environment = await get_scoped_environment(db, project_id, environment_id)
    data = payload.model_dump(exclude_unset=True, exclude_none=True)
    if "server_id" in payload.model_dump(exclude_unset=True):
        data["server_id"] = await _check_server(db, payload.server_id)
    else:
        data.pop("server_id", None)
    if data.get("name") and data["name"] != environment.name:
        data["name"] = data["name"].strip()
        data["slug"] = await _unique_slug(
            db,
            column=DeploymentEnvironment.slug,
            parent_column=DeploymentEnvironment.project_id,
            parent_id=environment.project_id,
            base=slugify(data["name"], "env", _NAME_MAX["environment"]),
            kind="environment",
        )
    if "config" in data:
        data["config"] = dict(data["config"])
    try:
        await _apply_update(db, environment, data)
    except IntegrityError as exc:
        raise _integrity_conflict(
            exc, "DUPLICATE_NAME", "An environment with this name exists in the project"
        ) from exc
    await audit_service.record(
        db,
        ctx,
        action="environment.update",
        resource_type="deployment_environment",
        resource_id=environment.id,
        metadata={"fields": sorted(data)},
        request=request,
    )
    return environment


async def delete_environment(
    db: AsyncSession,
    ctx: AuthContext | None,
    *,
    project_id: uuid.UUID,
    environment_id: uuid.UUID,
    request: Request | None = None,
) -> None:
    environment = await get_scoped_environment(db, project_id, environment_id)
    name = environment.name
    await db.delete(environment)
    await db.flush()
    await event_bus.publish(
        db,
        type="ENVIRONMENT_DELETED",
        message=f"Environment {name} deleted",
        resource_type="deployment_environment",
        resource_id=str(environment.id),
    )
    await audit_service.record(
        db,
        ctx,
        action="environment.delete",
        resource_type="deployment_environment",
        resource_id=environment.id,
        metadata={"name": name},
        request=request,
    )
