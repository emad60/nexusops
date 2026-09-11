"""Log pipeline: detection, bulk ingestion, trimming and live fan-out.

Flow: provider/agent lines -> :func:`append_lines` (chunked bulk insert) ->
:func:`publish_log_line` (Redis pub/sub for the WS hub). Retention is handled
by the worker beat via :func:`trim_container_logs` / :func:`trim_deployment_logs`.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, cast

import orjson
from sqlalchemy import delete, func, insert, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.channels import container_log_channel
from app.core.logging import get_logger
from app.core.redis_client import get_redis
from app.models import Container, LogEntry
from app.models.enums import LogLevel, LogSource
from app.providers.base import LogLine

log = get_logger("nexusops.logs")

_MAX_MESSAGE_CHARS = 8000
_CHUNK_SIZE = 500

# Ordered most-to-least severe; first match wins.
_LEVEL_PATTERNS: tuple[tuple[LogLevel, re.Pattern[str]], ...] = tuple(
    (level, re.compile(pattern, re.IGNORECASE))
    for level, pattern in (
        (LogLevel.FATAL, r"\b(?:fatal|crit(?:ical)?)\b"),
        (LogLevel.ERROR, r"\berror\b|\berr(?:or)?\s*[#:]|traceback|exception\b"),
        (LogLevel.WARN, r"\bwarn(?:ing)?\b|\bwrn\b"),
        (LogLevel.INFO, r"\binf(?:o)?\b|\bnotice\b"),
        (LogLevel.DEBUG, r"\bdebug\b|\bdbug\b"),
        (LogLevel.TRACE, r"\btrc\b|\btrace\b|\bverbose\b"),
    )
)

# [LEVEL] / LEVEL: prefixes at the start of a line are strong signals.
_PREFIX_RE = re.compile(
    r"^\W*(fatal|critical|crit|error|err|warning|warn|info|debug|trace)\W+", re.IGNORECASE
)


def detect_level(message: str) -> LogLevel:
    """Heuristically classify *message* into a :class:`LogLevel`."""
    if not message:
        return LogLevel.UNKNOWN
    prefix = _PREFIX_RE.match(message)
    if prefix is not None:
        word = prefix.group(1).lower()
        if word.startswith(("fatal", "crit")):
            return LogLevel.FATAL
        if word in {"error", "err"}:
            return LogLevel.ERROR
        if word.startswith(("warn",)):
            return LogLevel.WARN
        if word == "info":
            return LogLevel.INFO
        if word == "debug":
            return LogLevel.DEBUG
        return LogLevel.TRACE
    for level, pattern in _LEVEL_PATTERNS:
        if pattern.search(message):
            return level
    return LogLevel.UNKNOWN


def _entry_values(
    line: LogLine,
    *,
    source: LogSource,
    container_id: Any = None,
    deployment_id: Any = None,
    server_id: Any = None,
) -> dict[str, Any]:
    ts = (
        line.ts
        if (line.ts and line.ts.tzinfo)
        else (line.ts.replace(tzinfo=UTC) if line.ts else datetime.now(UTC))
    )
    return {
        "source": source.value,
        "container_id": container_id,
        "deployment_id": deployment_id,
        "server_id": server_id,
        "stream": (line.stream or "stdout")[:8],
        "level": detect_level(line.message).value,
        "message": (line.message or "")[:_MAX_MESSAGE_CHARS],
        "ts": ts,
    }


async def append_lines(
    db: AsyncSession,
    *,
    source: LogSource,
    container_id=None,
    deployment_id=None,
    server_id=None,
    lines: Sequence[LogLine],
) -> int:
    """Bulk-insert log lines in chunks of at most 500 rows. Returns count."""
    values = [
        _entry_values(
            line,
            source=source,
            container_id=container_id,
            deployment_id=deployment_id,
            server_id=server_id,
        )
        for line in lines
        if line is not None
    ]
    written = 0
    for offset in range(0, len(values), _CHUNK_SIZE):
        chunk = values[offset : offset + _CHUNK_SIZE]
        await db.execute(insert(LogEntry), chunk)
        written += len(chunk)
    return written


async def trim_container_logs(db: AsyncSession, container_id, keep: int = 5000) -> int:
    """Delete the oldest log rows beyond *keep* for one container."""
    keep = max(int(keep), 1)
    newest = (
        select(LogEntry.id)
        .where(LogEntry.container_id == container_id)
        .order_by(LogEntry.ts.desc(), LogEntry.id.desc())
        .limit(keep)
        .scalar_subquery()
    )
    result = await db.execute(
        delete(LogEntry).where(LogEntry.container_id == container_id, LogEntry.id.not_in(newest))
    )
    return int(cast(CursorResult[Any], result).rowcount or 0)


async def trim_deployment_logs(db: AsyncSession, deployment_id, keep: int = 20000) -> int:
    """Delete the oldest log rows beyond *keep* for one deployment."""
    keep = max(int(keep), 1)
    newest = (
        select(LogEntry.id)
        .where(LogEntry.deployment_id == deployment_id)
        .order_by(LogEntry.ts.desc(), LogEntry.id.desc())
        .limit(keep)
        .scalar_subquery()
    )
    result = await db.execute(
        delete(LogEntry).where(LogEntry.deployment_id == deployment_id, LogEntry.id.not_in(newest))
    )
    return int(cast(CursorResult[Any], result).rowcount or 0)


async def publish_log_line(channel_id_str: str, line: LogLine) -> bool:
    """Best-effort publish of one frame to the container's Redis channel."""
    try:
        frame = {
            "ts": line.ts.isoformat() if line.ts else datetime.now(UTC).isoformat(),
            "stream": line.stream or "stdout",
            "message": (line.message or "")[:_MAX_MESSAGE_CHARS],
        }
        await get_redis().publish(container_log_channel(channel_id_str), orjson.dumps(frame))
        return True
    except Exception as exc:  # Redis down must never break ingestion
        log.warning("log_publish_failed", channel=channel_id_str, error=str(exc))
        return False


async def ingest_provider_lines(
    db: AsyncSession,
    *,
    container_row: Container,
    lines: Sequence[LogLine],
) -> int:
    """Persist provider lines for a container AND fan them out to Redis.

    Used by the simulated generator and by host sync so the WS hub sees
    real-host log lines too.
    """
    if not lines:
        return 0
    written = await append_lines(
        db,
        source=LogSource.CONTAINER,
        container_id=container_row.id,
        server_id=container_row.server_id,
        lines=lines,
    )
    cid = str(container_row.id)
    for line in lines:
        if line is not None:
            await publish_log_line(cid, line)
    return written


async def count_container_logs(db: AsyncSession, container_id) -> int:
    """Total persisted log rows for a container (cheap UI counter)."""
    total = await db.scalar(
        select(func.count()).select_from(LogEntry).where(LogEntry.container_id == container_id)
    )
    return int(total or 0)
