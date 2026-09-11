"""Cross-entity global search powering the Ctrl+K command palette.

Every section is permission-filtered: callers only ever see entity types their
role grants read access to. Queries are bounded ILIKE matches — deliberately
simple and fast; no ranking service behind this.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import String, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DbSessionDep
from app.models import Container, Deployment, Incident, Monitor, Project, Server, User
from app.schemas.search import SearchHit, SearchResultOut

search_router = APIRouter(prefix="/search", tags=["search"])

# One per-entity search coroutine: (db, query, per-type limit) -> hits.
SearchFunc = Callable[[AsyncSession, str, int], Awaitable[list[SearchHit]]]


def _hit(type_: str, row_id: object, title: str, subtitle: str, url_path: str) -> SearchHit:
    return SearchHit(
        type=type_,
        id=row_id if isinstance(row_id, uuid.UUID) else uuid.UUID(str(row_id)),
        title=title[:160],
        subtitle=subtitle[:200],
        url_path=url_path,
    )


async def _search_servers(db: AsyncSession, q: str, limit: int) -> list[SearchHit]:
    pattern = f"%{q}%"
    rows = (
        await db.execute(
            select(Server)
            .where(
                or_(
                    Server.name.ilike(pattern),
                    Server.hostname.ilike(pattern),
                    Server.ip_address.ilike(pattern),
                )
            )
            .order_by(Server.name)
            .limit(limit)
        )
    ).scalars()
    return [
        _hit("servers", s.id, s.name, f"{s.hostname} · {s.environment}", f"/servers/{s.id}")
        for s in rows
    ]


async def _search_containers(db: AsyncSession, q: str, limit: int) -> list[SearchHit]:
    pattern = f"%{q}%"
    rows = (
        await db.execute(
            select(Container)
            .where(
                or_(
                    Container.name.ilike(pattern),
                    Container.image_ref.ilike(pattern),
                )
            )
            .order_by(Container.name)
            .limit(limit)
        )
    ).scalars()
    return [_hit("containers", c.id, c.name, c.image_ref, f"/containers/{c.id}") for c in rows]


async def _search_deployments(db: AsyncSession, q: str, limit: int) -> list[SearchHit]:
    pattern = f"%{q}%"
    rows = (
        await db.execute(
            select(Deployment)
            .where(
                or_(
                    Deployment.version.ilike(pattern),
                    Deployment.git_commit.ilike(pattern),
                    Deployment.notes.ilike(pattern),
                    func.cast(Deployment.number, String).ilike(pattern),
                )
            )
            .order_by(Deployment.number.desc())
            .limit(limit)
        )
    ).scalars()
    return [
        _hit("deployments", d.id, f"#{d.number} {d.version}", d.git_commit, f"/deployments/{d.id}")
        for d in rows
    ]


async def _search_projects(db: AsyncSession, q: str, limit: int) -> list[SearchHit]:
    pattern = f"%{q}%"
    rows = (
        await db.execute(
            select(Project)
            .where(
                or_(
                    Project.name.ilike(pattern),
                    Project.repository_url.ilike(pattern),
                )
            )
            .order_by(Project.name)
            .limit(limit)
        )
    ).scalars()
    return [_hit("projects", p.id, p.name, p.repository_url, f"/projects/{p.id}") for p in rows]


async def _search_monitors(db: AsyncSession, q: str, limit: int) -> list[SearchHit]:
    pattern = f"%{q}%"
    rows = (
        await db.execute(
            select(Monitor)
            .where(
                or_(
                    Monitor.name.ilike(pattern),
                    Monitor.url.ilike(pattern),
                )
            )
            .order_by(Monitor.name)
            .limit(limit)
        )
    ).scalars()
    return [_hit("monitors", m.id, m.name, m.url, f"/monitors/{m.id}") for m in rows]


async def _search_incidents(db: AsyncSession, q: str, limit: int) -> list[SearchHit]:
    pattern = f"%{q}%"
    rows = (
        await db.execute(
            select(Incident)
            .where(Incident.title.ilike(pattern))
            .order_by(Incident.opened_at.desc())
            .limit(limit)
        )
    ).scalars()
    return [_hit("incidents", i.id, i.title, i.status.value, f"/incidents/{i.id}") for i in rows]


async def _search_users(db: AsyncSession, q: str, limit: int) -> list[SearchHit]:
    pattern = f"%{q}%"
    rows = (
        await db.execute(
            select(User)
            .where(
                or_(
                    User.email.ilike(pattern),
                    User.full_name.ilike(pattern),
                ),
                User.is_active.is_(True),
            )
            .order_by(User.email)
            .limit(limit)
        )
    ).scalars()
    # There is no per-user route; deep-link the management page.
    return [_hit("users", u.id, u.full_name or u.email, u.email, "/settings/users") for u in rows]


@search_router.get("", response_model=SearchResultOut)
async def search(
    db: DbSessionDep,
    ctx: CurrentUser,
    q: Annotated[str, Query(min_length=2, max_length=120)],
    limit_per_type: Annotated[int, Query(ge=1, le=25)] = 5,
) -> SearchResultOut:
    """Permission-filtered multi-entity search for the command palette."""
    sections: tuple[tuple[str, str, SearchFunc], ...] = (
        ("servers", "server.read", _search_servers),
        ("containers", "container.read", _search_containers),
        ("deployments", "deployment.read", _search_deployments),
        ("projects", "project.read", _search_projects),
        ("monitors", "monitor.read", _search_monitors),
        ("incidents", "monitor.read", _search_incidents),
        ("users", "user.read", _search_users),
    )
    found = {
        attr: await finder(db, q, limit_per_type)
        for attr, permission, finder in sections
        if ctx.has_permission(permission)
    }
    return SearchResultOut(**found)
