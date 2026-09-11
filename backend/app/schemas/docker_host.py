"""Docker host schemas: CRUD payloads, read models, provider inventory."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import Field, field_serializer, model_validator

from app.schemas.base import APIModel, OutModel

#: Schemes a host endpoint may use. Empty string means "inherited from agent".
ALLOWED_ENDPOINT_SCHEMES = ("unix", "tcp", "sim")

_ENDPOINT_MAX_LENGTH = 512


def validate_endpoint_url(value: str | None) -> str:
    """Validate/normalize an endpoint URL against the scheme allowlist."""
    url = (value or "").strip()
    if not url:
        return ""
    if any(ch.isspace() or ord(ch) < 32 for ch in url):
        raise ValueError("endpoint_url must not contain whitespace or control characters")
    if len(url) > _ENDPOINT_MAX_LENGTH:
        raise ValueError(f"endpoint_url must be at most {_ENDPOINT_MAX_LENGTH} characters")
    parts = urlsplit(url)
    if parts.scheme.lower() not in ALLOWED_ENDPOINT_SCHEMES:
        allowed = ", ".join(f"{s}://" for s in ALLOWED_ENDPOINT_SCHEMES)
        raise ValueError(
            f"endpoint_url scheme not allowed; use one of {allowed} or empty for agent-inherited"
        )
    return url


def redact_endpoint_url(url: str) -> str:
    """Mask any userinfo credentials before the URL leaves the API."""
    if not url:
        return ""
    try:
        parts = urlsplit(url)
    except ValueError:
        return "[invalid]"
    if "@" in (parts.netloc or ""):
        host_part = parts.netloc.rsplit("@", 1)[1]
        return f"{parts.scheme}://[redacted]@{host_part}"
    return url


class DockerHostCreate(APIModel):
    """Payload for registering a docker host."""

    name: str = Field(min_length=1, max_length=120)
    endpoint_url: str = Field(default="", max_length=_ENDPOINT_MAX_LENGTH)
    tls_verify: bool = True
    server_id: UUID | None = None

    @model_validator(mode="after")
    def _check_endpoint(self) -> DockerHostCreate:
        self.endpoint_url = validate_endpoint_url(self.endpoint_url)
        return self


class DockerHostUpdate(APIModel):
    """Partial update payload; only supplied fields change."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    endpoint_url: str | None = Field(default=None, max_length=_ENDPOINT_MAX_LENGTH)
    tls_verify: bool | None = None
    server_id: UUID | None = None

    @model_validator(mode="after")
    def _check_endpoint(self) -> DockerHostUpdate:
        if self.endpoint_url is not None:
            self.endpoint_url = validate_endpoint_url(self.endpoint_url)
        return self


class DockerHostOut(OutModel):
    """Read model. Endpoint URLs are returned with credentials masked."""

    updated_at: datetime
    name: str
    endpoint_url: str
    tls_verify: bool
    status: str
    last_checked_at: datetime | None = None
    last_error: str = ""
    server_id: UUID | None = None

    @field_serializer("endpoint_url")
    def _redact(self, value: str) -> str:
        return redact_endpoint_url(value)


class DockerImageOut(APIModel):
    id: str
    repo_tags: list[str] = Field(default_factory=list)
    size_bytes: int = 0
    architecture: str = ""


class DockerVolumeOut(APIModel):
    name: str
    driver: str
    mountpoint: str


class DockerNetworkOut(APIModel):
    name: str
    driver: str
    scope: str


class DockerHostPingOut(APIModel):
    """Result of probing a host's provider endpoint."""

    status: str
    checked_at: datetime
    latency_ms: float | None = None
    error: str = ""


def image_out(row: dict[str, Any]) -> DockerImageOut:
    """Build an :class:`DockerImageOut` from a provider inventory dict."""
    return DockerImageOut(
        id=str(row.get("id", "")),
        repo_tags=[str(t) for t in row.get("repo_tags") or []],
        size_bytes=int(row.get("size_bytes") or 0),
        architecture=str(row.get("architecture") or ""),
    )


def volume_out(row: dict[str, Any]) -> DockerVolumeOut:
    return DockerVolumeOut(
        name=str(row.get("name", "")),
        driver=str(row.get("driver", "")),
        mountpoint=str(row.get("mountpoint", "")),
    )


def network_out(row: dict[str, Any]) -> DockerNetworkOut:
    return DockerNetworkOut(
        name=str(row.get("name", "")),
        driver=str(row.get("driver", "")),
        scope=str(row.get("scope", "")),
    )
