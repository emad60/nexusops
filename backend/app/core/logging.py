"""Structured logging via structlog.

Every log record carries timestamp, level, service, logger name and any
contextual bindings (request_id, user_id, ...) set through structlog's
contextvars. Secrets must never be passed to loggers; use
:func:`redact_mapping` when logging dicts that may contain sensitive keys.
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Callable
from typing import Any

import orjson
import structlog

_SENSITIVE_KEY_PARTS = (
    "password",
    "secret",
    "token",
    "authorization",
    "api_key",
    "apikey",
    "private_key",
    "credential",
    "cookie",
    "session",
)

_REDACTED = "[REDACTED]"


def _is_sensitive_key(key: object) -> bool:
    """Substring match on a normalised key so header-style names are caught too.

    ``X-API-Key`` / ``Private-Key`` style keys normalise their separators to
    underscores before matching; the app's own API-key header is spelled
    ``X-API-Key``, which must never survive into a persistent log sink.
    """
    normalized = str(key).lower().replace("-", "_").replace(".", "_").replace(" ", "_")
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


def redact_mapping(data: dict) -> dict:
    """Return a copy of *data* with sensitive values replaced.

    Used by audit metadata rendering, error payloads and access logs so that
    secrets never reach persistent sinks.
    """
    redacted: dict = {}
    for key, value in data.items():
        if _is_sensitive_key(key):
            redacted[key] = _REDACTED
        elif isinstance(value, dict):
            redacted[key] = redact_mapping(value)
        else:
            redacted[key] = value
    return redacted


def _orjson_dumps(obj: object, default: Callable[[Any], Any] | None = None, **_kwargs: Any) -> str:
    return orjson.dumps(obj, default=default).decode()


def configure_logging(level: str = "INFO", *, json_output: bool | None = None) -> None:
    """Configure structlog + stdlib logging once at process start.

    Everything (structlog events, uvicorn, celery, docker SDK) flows through a
    single stdlib handler rendered by ``ProcessorFormatter`` so the shape is
    identical no matter who logged it. ``add_logger_name`` needs stdlib-backed
    loggers, hence ``LoggerFactory()`` rather than ``PrintLoggerFactory``.
    """
    if json_output is None:
        from app.core.config import get_settings

        json_output = get_settings().is_production or get_settings().is_testing

    level_int = getattr(logging, level.upper(), logging.INFO)

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)
    shared_processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    renderer: structlog.typing.Processor = (
        structlog.processors.JSONRenderer(serializer=_orjson_dumps)
        if json_output
        else structlog.dev.ConsoleRenderer(colors=sys.stdout.isatty())
    )

    structlog.configure(
        processors=[*shared_processors, structlog.stdlib.ProcessorFormatter.wrap_for_formatter],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level_int)

    for noisy in ("uvicorn.access", "celery.app.trace", "docker.utils.config"):
        logging.getLogger(noisy).setLevel(max(level_int, logging.WARNING))
    # Celery installs its own handlers on re-config; keep ours authoritative.
    for name in ("celery", "celery.worker", "celery.task"):
        logging.getLogger(name).handlers[:] = []


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
