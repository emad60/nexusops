"""Global search schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import Field

from app.schemas.base import APIModel


class SearchHit(APIModel):
    """One result row; ``url_path`` is the SPA route for the entity."""

    type: str
    id: UUID
    title: str
    subtitle: str = ""
    url_path: str


class SearchResultOut(APIModel):
    """Results grouped per entity type, permission-filtered per caller.

    Every section is always present (possibly empty) so clients can iterate
    the object uniformly.
    """

    servers: list[SearchHit] = Field(default_factory=list)
    containers: list[SearchHit] = Field(default_factory=list)
    deployments: list[SearchHit] = Field(default_factory=list)
    projects: list[SearchHit] = Field(default_factory=list)
    monitors: list[SearchHit] = Field(default_factory=list)
    incidents: list[SearchHit] = Field(default_factory=list)
    users: list[SearchHit] = Field(default_factory=list)
