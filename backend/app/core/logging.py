"""Structured logging via structlog.

Every log record carries timestamp, level, service, logger name and any
contextual bindings (request_id, user_id, ...) set through structlog's
contextvars. Secrets must never be passed to loggers; use
:func:`redact_mapping` when logging dicts that may contain sensitive keys.
"""

from __future__ import annotations

import logging
import sys

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


def redact_mapping(data: dict) -> dict:
    """Return a copy of *data* with sensitive values replaced.

    Used by audit metadata rendering, error payloads and access logs so that
    secrets never reach persistent sinks.
    """
    redacted: dict = {}
    for key, value in data.items():
        key_l = str(key).lower()
        if any(part in key_l for part in _SENSITIVE_KEY_PARTS):
            redacted[key] = _REDACTED
        elif isinstance(value, dict):
            redacted[key] = redact_mapping(value)
        else:
            redacted[key] = value
    return redacted


def _orjson_dumps(obj: object, default=None, **_kwargs) -> str:  # type: ignore[no-untyped-def]
    return orjson.dumps(obj, default=default).decode()


def configure_logging(level: str = "INFO", *, json_output: bool | None = None) -> None:
    """Configure structlog + stdlib logging once at process start."""
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
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level_int),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Route stdlib logging (uvicorn, celery, docker SDK…) through the same shape.
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level_int)
    for noisy in ("uvicorn.access", "celery.app.trace", "docker.utils.config"):
        logging.getLogger(noisy).setLevel(max(level_int, logging.WARNING))


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)  # type: ignore[return-value]
