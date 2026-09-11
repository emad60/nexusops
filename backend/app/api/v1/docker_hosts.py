"""Docker host API: CRUD, ping and provider-backed inventory reads.

Permission mapping (documented per the platform RBAC registry):
  * list / get / ping / images / volumes / networks -> ``container.read``
  * create  -> ``server.create``  (hosts attach to servers)
  * update  -> ``server.update``
  * delete  -> ``server.delete``
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from app.api.deps import AuthContext, DbSessionDep, require_permission
from app.core.pagination import Page, PageParams, page_params
from app.schemas.docker_host import (
    DockerHostCreate,
    DockerHostOut,
    DockerHostPingOut,
    DockerHostUpdate,
    DockerImageOut,
    DockerNetworkOut,
    DockerVolumeOut,
    image_out,
    network_out,
    volume_out,
)
from app.services import docker_host_service

hosts_router = APIRouter(prefix="/docker-hosts", tags=["docker"])

_ReadPerm = Annotated[AuthContext, Depends(require_permission("container.read"))]
_CreatePerm = Annotated[AuthContext, Depends(require_permission("server.create"))]
_UpdatePerm = Annotated[AuthContext, Depends(require_permission("server.update"))]
_DeletePerm = Annotated[AuthContext, Depends(require_permission("server.delete"))]


@hosts_router.get("", response_model=Page[DockerHostOut], summary="List docker hosts")
async def list_docker_hosts(
    db: DbSessionDep,
    _: _ReadPerm,
    params: Annotated[PageParams, Depends(page_params)],
    status_filter: Annotated[str | None, Query(alias="status", max_length=16)] = None,
    q: Annotated[str | None, Query(max_length=120)] = None,
) -> Page[DockerHostOut]:
    """Offset-paginated docker host listing; exposes status and last_error."""
    rows, total = await docker_host_service.list_hosts(
        db, params=params, status_filter=status_filter, q=q
    )
    return Page[DockerHostOut](
        items=[DockerHostOut.model_validate(row) for row in rows],
        total=total,
        limit=params.limit,
        offset=params.offset,
    )


@hosts_router.get("/{host_id}", response_model=DockerHostOut, summary="Get a docker host")
async def get_docker_host(db: DbSessionDep, _: _ReadPerm, host_id: UUID) -> DockerHostOut:
    host = await docker_host_service.get_host(db, host_id)
    return DockerHostOut.model_validate(host)


@hosts_router.post(
    "",
    response_model=DockerHostOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a docker host",
)
async def create_docker_host(
    db: DbSessionDep,
    ctx: _CreatePerm,
    payload: DockerHostCreate,
    request: Request,
) -> DockerHostOut:
    """Register a host. Endpoint allowlist: unix://, tcp://, sim:// or ''."""
    host = await docker_host_service.create_host(db, payload=payload, ctx=ctx, request=request)
    return DockerHostOut.model_validate(host)


@hosts_router.patch("/{host_id}", response_model=DockerHostOut, summary="Update a docker host")
async def update_docker_host(
    db: DbSessionDep,
    ctx: _UpdatePerm,
    host_id: UUID,
    payload: DockerHostUpdate,
    request: Request,
) -> DockerHostOut:
    """Partially update name / endpoint_url / tls_verify / server_id."""
    host = await docker_host_service.get_host(db, host_id)
    host = await docker_host_service.update_host(
        db, host=host, payload=payload, ctx=ctx, request=request
    )
    return DockerHostOut.model_validate(host)


@hosts_router.delete(
    "/{host_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a docker host"
)
async def delete_docker_host(
    db: DbSessionDep,
    ctx: _DeletePerm,
    host_id: UUID,
    request: Request,
) -> None:
    """Delete the host and cascade-delete its containers and images."""
    host = await docker_host_service.get_host(db, host_id)
    await docker_host_service.delete_host(db, host=host, ctx=ctx, request=request)


@hosts_router.post(
    "/{host_id}/ping", response_model=DockerHostPingOut, summary="Probe a docker host"
)
async def ping_docker_host(
    db: DbSessionDep,
    ctx: _ReadPerm,
    host_id: UUID,
    request: Request,
) -> DockerHostPingOut:
    """Test provider reachability; updates status/last_checked_at/last_error.

    Returns 200 even when unreachable — inspect ``status`` and ``error``.
    """
    host = await docker_host_service.get_host(db, host_id)
    return await docker_host_service.ping_host(db, host=host, ctx=ctx, request=request)


@hosts_router.get(
    "/{host_id}/images", response_model=list[DockerImageOut], summary="List images on a host"
)
async def list_host_images(db: DbSessionDep, _: _ReadPerm, host_id: UUID) -> list[DockerImageOut]:
    host = await docker_host_service.get_host(db, host_id)
    items = await docker_host_service.list_images(db, host)
    return [image_out(item) for item in items]


@hosts_router.get(
    "/{host_id}/volumes", response_model=list[DockerVolumeOut], summary="List volumes on a host"
)
async def list_host_volumes(db: DbSessionDep, _: _ReadPerm, host_id: UUID) -> list[DockerVolumeOut]:
    host = await docker_host_service.get_host(db, host_id)
    items = await docker_host_service.list_volumes(db, host)
    return [volume_out(item) for item in items]


@hosts_router.get(
    "/{host_id}/networks", response_model=list[DockerNetworkOut], summary="List networks on a host"
)
async def list_host_networks(
    db: DbSessionDep, _: _ReadPerm, host_id: UUID
) -> list[DockerNetworkOut]:
    host = await docker_host_service.get_host(db, host_id)
    items = await docker_host_service.list_networks(db, host)
    return [network_out(item) for item in items]
