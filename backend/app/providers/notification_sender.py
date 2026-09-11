"""Low-level notification transports: SMTP email and outgoing webhooks.

These functions are deliberately dumb: they take fully-resolved settings and a
rendered message, and either succeed or raise :class:`NotificationError` with a
sanitized message. Server responses are never echoed back into errors so that
bounce texts or remote stack traces cannot leak into the database or API.
"""

from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage
from typing import Any

import httpx

from app.core.logging import get_logger

log = get_logger("nexusops.notify_sender")

_WEBHOOK_TIMEOUT_SECONDS = 10.0


class NotificationError(Exception):
    """Raised when a delivery attempt fails. Message is safe to persist."""


def _safe_reason(exc: BaseException) -> str:
    """Bounded, single-line, content-free error reason."""
    return f"{exc.__class__.__name__}"[:120]


# --- Email --------------------------------------------------------------------


async def send_email(
    *,
    host: str,
    port: int,
    user: str = "",
    password: str = "",
    from_addr: str,
    tls: bool = False,
    subject: str,
    body: str,
    recipients: list[str],
    timeout: float = 15.0,  # noqa: ASYNC109 - public API mirrors httpx
) -> None:
    """Send a plain-text email via SMTP. Raises :class:`NotificationError`.

    The blocking ``smtplib`` conversation runs in a worker thread; credentials
    never appear in raised messages.
    """

    def _send() -> None:
        message = EmailMessage()
        message["From"] = from_addr
        message["To"] = ", ".join(recipients)
        message["Subject"] = subject
        message.set_content(body)

        try:
            with smtplib.SMTP(host, port, timeout=timeout) as smtp:
                smtp.ehlo()
                if tls:
                    if not smtp.has_extn("starttls"):
                        raise NotificationError("smtp: server does not support STARTTLS")
                    smtp.starttls()
                    smtp.ehlo()
                if user:
                    smtp.login(user, password)
                smtp.send_message(message)
        except NotificationError:
            raise
        except (smtplib.SMTPException, OSError) as exc:
            log.warning("email_send_failed", reason=_safe_reason(exc))
            raise NotificationError(f"smtp delivery failed ({_safe_reason(exc)})") from exc

    try:
        await asyncio.to_thread(_send)
    except NotificationError:
        raise
    except Exception as exc:  # unexpected — still must not leak internals
        log.warning("email_send_unexpected", reason=_safe_reason(exc))
        raise NotificationError(f"smtp delivery failed ({_safe_reason(exc)})") from exc


# --- Webhook ------------------------------------------------------------------


async def send_webhook(
    *,
    url: str,
    headers: dict[str, str] | None = None,
    payload: dict[str, Any],
    secret_header: tuple[str, str] | None = None,
    timeout: float = _WEBHOOK_TIMEOUT_SECONDS,  # noqa: ASYNC109 - public API mirrors httpx
) -> None:
    """POST *payload* as JSON to *url*; 2xx is success, anything else raises.

    Response bodies are intentionally discarded — only the status code reaches
    the error message.
    """
    merged = {str(k): str(v) for k, v in (headers or {}).items()}
    if secret_header is not None:
        name, value = secret_header
        merged[str(name)] = str(value)
    merged.setdefault("content-type", "application/json")

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
            response = await client.post(url, json=payload, headers=merged)
    except httpx.HTTPError as exc:
        log.warning("webhook_send_failed", reason=_safe_reason(exc))
        raise NotificationError(f"webhook request failed ({_safe_reason(exc)})") from exc

    if not 200 <= response.status_code < 300:
        raise NotificationError(f"webhook returned {response.status_code}")


__all__ = ["NotificationError", "send_email", "send_webhook"]
