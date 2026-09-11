"""Schemas for uptime monitors and their check history."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field, field_serializer

from app.models.enums import CheckResult, MonitorStatus
from app.providers.monitor_transport import strip_query
from app.schemas.base import APIModel, OutModel

ALLOWED_METHODS = ("GET", "HEAD", "POST", "PUT", "OPTIONS")
MAX_HEADERS = 20

#: Header-name fragments that mark a probe header as credential-bearing.
#: Values of matching headers are masked in every response; the full value
#: is used server-side by the probe transport only.
_SENSITIVE_HEADER_FRAGMENTS = (
    "auth",
    "cookie",
    "credential",
    "key",
    "secret",
    "session",
    "token",
)

_MASKED_HEADER_VALUE = "******"


def is_sensitive_header(name: str) -> bool:
    """True when *name* looks like it carries a credential (Authorization etc.)."""
    lowered = name.lower()
    return any(fragment in lowered for fragment in _SENSITIVE_HEADER_FRAGMENTS)


def mask_sensitive_headers(headers: dict[str, str] | None) -> dict[str, str]:
    """Return a copy of *headers* with sensitive values replaced by a mask."""
    return {
        str(k): (_MASKED_HEADER_VALUE if is_sensitive_header(str(k)) else str(v))
        for k, v in (headers or {}).items()
    }


class MonitorBase(APIModel):
    """Shared validation bounds for monitor configuration."""

    name: str = Field(min_length=1, max_length=160)
    project_id: UUID | None = None
    url: str = Field(min_length=1, max_length=1000)
    method: Literal["GET", "HEAD", "POST", "PUT", "OPTIONS"] = "GET"
    interval_seconds: int = Field(default=60, ge=10, le=86400)
    timeout_seconds: float = Field(default=10.0, ge=0.5, le=60)
    expected_status: int = Field(default=200, ge=100, le=599)
    expected_body: str | None = Field(default=None, max_length=4096)
    headers: dict[str, str] = Field(default_factory=dict, max_length=MAX_HEADERS)
    skip_tls_verify: bool = False
    follow_redirects: bool = True
    enabled: bool = True
    failure_threshold: int = Field(default=3, ge=1, le=50)
    success_threshold: int = Field(default=2, ge=1, le=50)


class MonitorCreate(MonitorBase):
    """Payload for POST /monitors."""


class MonitorUpdate(APIModel):
    """Partial update; ``url`` changes are re-validated against the SSRF guard."""

    name: str | None = Field(default=None, min_length=1, max_length=160)
    project_id: UUID | None = None
    url: str | None = Field(default=None, min_length=1, max_length=1000)
    method: Literal["GET", "HEAD", "POST", "PUT", "OPTIONS"] | None = None
    interval_seconds: int | None = Field(default=None, ge=10, le=86400)
    timeout_seconds: float | None = Field(default=None, ge=0.5, le=60)
    expected_status: int | None = Field(default=None, ge=100, le=599)
    expected_body: str | None = Field(default=None, max_length=4096)
    headers: dict[str, str] | None = Field(default=None, max_length=MAX_HEADERS)
    skip_tls_verify: bool | None = None
    follow_redirects: bool | None = None
    enabled: bool | None = None
    failure_threshold: int | None = Field(default=None, ge=1, le=50)
    success_threshold: int | None = Field(default=None, ge=1, le=50)


class MonitorOut(OutModel):
    """Monitor representation.

    Credential material is masked on the way out: probe headers are the
    canonical place users put ``Authorization: Bearer …`` / ``X-API-Key``
    values, and monitor URLs commonly carry ``?token=…`` query credentials.
    Sensitive header values are replaced by a mask and the URL query string is
    stripped; the full values live server-side and are used only by the probe.
    """

    updated_at: datetime
    name: str
    project_id: UUID | None = None
    project_name: str | None = None
    url: str
    method: str
    interval_seconds: int
    timeout_seconds: float
    expected_status: int
    expected_body: str | None = None
    headers: dict[str, str] = Field(default_factory=dict)
    skip_tls_verify: bool
    follow_redirects: bool
    enabled: bool
    status: MonitorStatus
    consecutive_failures: int
    consecutive_successes: int
    failure_threshold: int
    success_threshold: int
    next_check_at: datetime
    last_check_at: datetime | None = None
    last_success_at: datetime | None = None
    last_failure_at: datetime | None = None
    current_open_incident_id: UUID | None = None
    uptime_pct_24h: float | None = None

    @field_serializer("url")
    def _redact_url_query(self, url: str) -> str:
        # Strip the query string (signed tokens / API keys embedded in URLs)
        # from the client-visible reference; the probe uses the full URL.
        return strip_query(url)

    @field_serializer("headers")
    def _mask_header_values(self, headers: dict[str, str]) -> dict[str, str]:
        return mask_sensitive_headers(headers)


class MonitorCheckOut(APIModel):
    """A single historical check result."""

    id: int
    monitor_id: UUID
    checked_at: datetime
    result: CheckResult
    response_time_ms: float | None = None
    status_code: int | None = None
    error: str = ""


class UptimeSummary(APIModel):
    """Aggregated availability over a lookback window."""

    uptime_pct: float
    total_checks: int
    failed_checks: int
    avg_response_ms: float | None = None
    p95_response_ms: float | None = None


class MonitorSortField:
    """Whitelist of sortable columns exposed as query parameters."""

    CREATED_AT = "created_at"
    NAME = "name"
    STATUS = "status"
    NEXT_CHECK_AT = "next_check_at"

    ALL = frozenset({CREATED_AT, NAME, STATUS, NEXT_CHECK_AT})


__all__ = [
    "ALLOWED_METHODS",
    "MAX_HEADERS",
    "MonitorBase",
    "MonitorCheckOut",
    "MonitorCreate",
    "MonitorOut",
    "MonitorSortField",
    "MonitorUpdate",
    "UptimeSummary",
    "is_sensitive_header",
    "mask_sensitive_headers",
]
