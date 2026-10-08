"""Projects, applications and (project-scoped) deployment-environments endpoints.

Routers stay thin: parse -> service call -> serialize. Environments live under
their **project** (Phase 2): ``/projects/{project_id}/environments``. They are no
longer reachable through an application — an environment is a property of the
project, not of any one application.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import AuthContext, DbSessionDep, require_permission
from app.core.pagination import Page, PageParams, page_params
from app.models import Application, Deployment
from app.schemas.application import ApplicationCreate, ApplicationOut, ApplicationUpdate
from app.schemas.deployment import LatestDeploymentSummary
from app.schemas.environment import (
    EnvironmentCreate,
    EnvironmentDetailOut,
    EnvironmentOut,
    EnvironmentUpdate,
)
from app.schemas.project import ProjectCreate, ProjectDetailOut, ProjectOut, ProjectUpdate
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["projects"])

ReadUser = Annotated[AuthContext, Depends(require_permission("project.read"))]
ManageUser = Annotated[AuthContext, Depends(require_permission("project.manage"))]


def _app_out(application: Application, latest: Deployment | None = None) -> ApplicationOut:
    out = ApplicationOut.model_validate(application)
    if latest is not None:
        out.latest_deployment = LatestDeploymentSummary(
            number=latest.number,
            status=latest.status,
            version=latest.version,
            finished_at=latest.finished_at,
        )
    return out


# --- Projects -----------------------------------------------------------------


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    db: DbSessionDep,
    ctx: ManageUser,
    request: Request,
) -> ProjectOut:
    """Register a new project. Names are unique within the organization."""
    project = await project_service.create_project(db, ctx, payload=payload, request=request)
    return ProjectOut.model_validate(project)


@router.get("", response_model=Page[ProjectOut])
async def list_projects(
    db: DbSessionDep,
    _: ReadUser,
    page: Annotated[PageParams, Depends(page_params)],
) -> Page[ProjectOut]:
    rows, total = await project_service.list_projects(db, page)
    return Page(
        items=[ProjectOut.model_validate(row) for row in rows],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )


@router.get("/{project_id}", response_model=ProjectDetailOut)
async def get_project(
    project_id: UUID,
    db: DbSessionDep,
    _: ReadUser,
) -> ProjectDetailOut:
    project = await project_service.get_project(db, project_id)
    latest = await project_service.latest_deployments_by_application(
        db, [application.id for application in project.applications]
    )
    applications = [
        _app_out(application, latest.get(application.id))
        for application in sorted(project.applications, key=lambda item: item.name)
    ]
    environments = [
        EnvironmentOut.model_validate(environment)
        for environment in await project_service.list_project_environments(db, project_id)
    ]
    out = ProjectDetailOut.model_validate(project)
    return out.model_copy(update={"applications": applications, "environments": environments})


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(
    project_id: UUID,
    payload: ProjectUpdate,
    db: DbSessionDep,
    ctx: ManageUser,
    request: Request,
) -> ProjectOut:
    project = await project_service.update_project(
        db, ctx, project_id=project_id, payload=payload, request=request
    )
    return ProjectOut.model_validate(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    db: DbSessionDep,
    ctx: ManageUser,
    request: Request,
) -> None:
    await project_service.delete_project(db, ctx, project_id=project_id, request=request)


# --- Nested applications --------------------------------------------------------


@router.post(
    "/{project_id}/applications",
    response_model=ApplicationOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_application(
    project_id: UUID,
    payload: ApplicationCreate,
    db: DbSessionDep,
    ctx: ManageUser,
    request: Request,
) -> ApplicationOut:
    application = await project_service.create_application(
        db, ctx, project_id=project_id, payload=payload, request=request
    )
    return ApplicationOut.model_validate(application)


@router.get("/{project_id}/applications", response_model=Page[ApplicationOut])
async def list_applications(
    project_id: UUID,
    db: DbSessionDep,
    _: ReadUser,
    page: Annotated[PageParams, Depends(page_params)],
) -> Page[ApplicationOut]:
    rows, total = await project_service.list_applications(db, project_id, page)
    return Page(
        items=[ApplicationOut.model_validate(row) for row in rows],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )


@router.get("/{project_id}/applications/{application_id}", response_model=ApplicationOut)
async def get_application(
    project_id: UUID,
    application_id: UUID,
    db: DbSessionDep,
    _: ReadUser,
) -> ApplicationOut:
    application = await project_service.get_scoped_application(db, project_id, application_id)
    latest = await project_service.latest_deployments_by_application(db, [application.id])
    return _app_out(application, latest.get(application.id))


@router.patch("/{project_id}/applications/{application_id}", response_model=ApplicationOut)
async def update_application(
    project_id: UUID,
    application_id: UUID,
    payload: ApplicationUpdate,
    db: DbSessionDep,
    ctx: ManageUser,
    request: Request,
) -> ApplicationOut:
    application = await project_service.update_application(
        db,
        ctx,
        project_id=project_id,
        application_id=application_id,
        payload=payload,
        request=request,
    )
    return ApplicationOut.model_validate(application)


@router.delete(
    "/{project_id}/applications/{application_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_application(
    project_id: UUID,
    application_id: UUID,
    db: DbSessionDep,
    ctx: ManageUser,
    request: Request,
) -> None:
    await project_service.delete_application(
        db, ctx, project_id=project_id, application_id=application_id, request=request
    )


# --- Nested environments (project-scoped) ---------------------------------------


@router.post(
    "/{project_id}/environments",
    response_model=EnvironmentOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_environment(
    project_id: UUID,
    payload: EnvironmentCreate,
    db: DbSessionDep,
    ctx: ManageUser,
    request: Request,
) -> EnvironmentOut:
    environment = await project_service.create_environment(
        db, ctx, project_id=project_id, payload=payload, request=request
    )
    return EnvironmentOut.model_validate(environment)


@router.get("/{project_id}/environments", response_model=Page[EnvironmentOut])
async def list_environments(
    project_id: UUID,
    db: DbSessionDep,
    _: ReadUser,
    page: Annotated[PageParams, Depends(page_params)],
) -> Page[EnvironmentOut]:
    rows, total = await project_service.list_environments(db, project_id, page)
    return Page(
        items=[EnvironmentOut.model_validate(row) for row in rows],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )


@router.get("/{project_id}/environments/{environment_id}", response_model=EnvironmentDetailOut)
async def get_environment(
    project_id: UUID,
    environment_id: UUID,
    db: DbSessionDep,
    _: ReadUser,
) -> EnvironmentDetailOut:
    """Environment detail: project config, overrides, effective config, counts.

    The three configuration layers are returned separately so the UI can show
    which value comes from where. Secret **references** are key names; values are
    never returned.
    """
    environment = await project_service.get_scoped_environment(db, project_id, environment_id)
    detail = await project_service.environment_detail(db, environment)
    base = EnvironmentDetailOut.model_validate(environment)
    return base.model_copy(update=detail)


@router.patch("/{project_id}/environments/{environment_id}", response_model=EnvironmentOut)
async def update_environment(
    project_id: UUID,
    environment_id: UUID,
    payload: EnvironmentUpdate,
    db: DbSessionDep,
    ctx: ManageUser,
    request: Request,
) -> EnvironmentOut:
    environment = await project_service.update_environment(
        db,
        ctx,
        project_id=project_id,
        environment_id=environment_id,
        payload=payload,
        request=request,
    )
    return EnvironmentOut.model_validate(environment)


@router.delete(
    "/{project_id}/environments/{environment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_environment(
    project_id: UUID,
    environment_id: UUID,
    db: DbSessionDep,
    ctx: ManageUser,
    request: Request,
) -> None:
    await project_service.delete_environment(
        db, ctx, project_id=project_id, environment_id=environment_id, request=request
    )
