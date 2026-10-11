"""Structured logging via structlog.

Every log record carries timestamp, level, service, logger name and any
contextual bindings (request_id, user_id, ...) set through structlog's
contextvars. Secrets must never be passed to loggers; use
:func:`redact_mapping` when logging dicts that may contain sensitive keys.

That last rule is a discipline, and disciplines fail, so the pipeline enforces
it too: :func:`redact_log_event` is the final processor on **every** record —
structlog's own chain and the ``foreign_pre_chain`` that catches stdlib loggers
(uvicorn, celery, the docker SDK) — and it runs the same recursive walk over the
whole event dict, formatted tracebacks included. A value that reaches a log call
by accident therefore cannot reach a sink verbatim.
"""

from __future__ import annotations

import logging
import re
import sys
from collections.abc import Callable, MutableMapping
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

#: PEM armor of a *private* key, in any of its spellings (``PRIVATE KEY``,
#: ``RSA PRIVATE KEY``, ``EC PRIVATE KEY``, ``OPENSSH PRIVATE KEY``,
#: ``ENCRYPTED PRIVATE KEY``). Certificates and public keys are deliberately not
#: matched: they are not secrets, and redacting them would destroy the diagnostic
#: value of a chain-inspection result for no security gain.
_PRIVATE_KEY_BLOCK = re.compile(
    r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----",
    re.DOTALL,
)


def _is_sensitive_key(key: object) -> bool:
    """Substring match on a normalised key so header-style names are caught too.

    ``X-API-Key`` / ``Private-Key`` style keys normalise their separators to
    underscores before matching; the app's own API-key header is spelled
    ``X-API-Key``, which must never survive into a persistent log sink.
    """
    normalized = str(key).lower().replace("-", "_").replace(".", "_").replace(" ", "_")
    return any(part in normalized for part in _SENSITIVE_KEY_PARTS)


def _redact_private_key_blocks(value: str) -> str:
    """Replace every embedded PEM private-key block in *value* with the marker.

    Only the block is replaced, so whatever diagnostic text surrounded it — an
    nginx error line, a tool's stderr — survives. Prose *about* a private key is
    untouched: the match is the PEM armor itself, not the phrase.
    """
    if "PRIVATE KEY" not in value:
        # Cheap miss, so the common case never runs a regex over a long string.
        return value
    return _PRIVATE_KEY_BLOCK.sub(_REDACTED, value)


def redact_text(value: str) -> str:
    """Scrub PEM private-key blocks out of one free-text value.

    The scalar counterpart to :func:`redact_mapping`, for a column or log field
    that carries agent- or tool-supplied text directly (an operation's
    ``error_message``): there is no key name to match on, so the content is the
    only signal available.
    """
    return _redact_private_key_blocks(value)


def redact_value(value: Any) -> Any:
    """Recursively redact one value of any shape — the depth-agnostic walk.

    Dicts, lists and tuples are all walked, at any depth, because a sensitive
    value does not have to sit directly under a sensitive key: an agent's
    operation result, or an audit payload built from one, can nest a private key
    inside ``{"output": {"lines": [{"text": ...}]}}``. The key name is not the
    only tell either — a PEM private key is recognisable by its own armor
    whatever field it was put in — so a string is scrubbed by content as well.

    A container's *type* is preserved (``list`` stays a ``list``, ``tuple`` a
    ``tuple``) so a redacted payload keeps the shape its consumer expects.
    """
    if isinstance(value, dict):
        return redact_mapping(value)
    if isinstance(value, list):
        return [redact_value(item) for item in value]
    if isinstance(value, tuple):
        return tuple(redact_value(item) for item in value)
    if isinstance(value, str):
        return _redact_private_key_blocks(value)
    return value


def redact_mapping(data: dict) -> dict:
    """Return a copy of *data* with sensitive values replaced, at any depth.

    Two independent rules, because either alone leaves a hole:

    * **key name** — a normalised substring match. A match replaces the whole
      subtree with the marker, so a container named ``credentials`` cannot leak a
      nested value the walker never had to reach into.
    * **value content** — a string carrying a PEM private-key block is scrubbed in
      place, whatever key it arrived under, including inside nested lists.

    Used by audit metadata rendering, error payloads and access logs so that
    secrets never reach persistent sinks. The input is never mutated.
    """
    redacted: dict = {}
    for key, value in data.items():
        if _is_sensitive_key(key):
            redacted[key] = _REDACTED
        else:
            redacted[key] = redact_value(value)
    return redacted


def redact_log_event(
    _logger: Any, _method_name: str, event_dict: MutableMapping[str, Any]
) -> dict[str, Any]:
    """structlog processor: scrub one record before anything renders it.

    The pipeline stage that makes the module docstring's rule structural rather
    than aspirational. It is deliberately the **last** processor, so it sees what
    a sink would have seen: the bound values, whatever the caller interpolated
    into the message, and the formatted traceback (whose text can echo the input
    that failed validation).

    A structlog processor must return an event dict, and this one does — the
    shape is preserved, only sensitive values are replaced.
    """
    return redact_mapping(dict(event_dict))


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
        # Last, so nothing renders a record before it has been through redaction:
        # the message, the bound values and the formatted traceback alike.
        redact_log_event,
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
