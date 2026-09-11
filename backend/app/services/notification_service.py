"""Notification channels and the outbound delivery pipeline.

Configuration is stored Fernet-encrypted and never returned by any API. The
dispatcher subscribes to ``nx:events``, fans frames out to matching channels,
and retries failures with capped exponential backoff. Nothing in this module
raises out of a delivery attempt — failures land on the delivery row.
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, NoReturn
from urllib.parse import urlparse

import orjson
from fastapi import Request
from sqlalchemy import and_, func, or_, select, tuple_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.api.deps import AuthContext
from app.core.channels import CHANNEL_EVENTS
from app.core.config import get_settings
from app.core.db import get_sessionmaker
from app.core.errors import BadRequest, NotFound
from app.core.logging import get_logger
from app.core.pagination import CursorParams
from app.core.redis_client import get_redis
from app.core.security import decrypt_str, encrypt_str
from app.core.ssrf import assert_safe_url_async
from app.models import NotificationChannel, NotificationDelivery
from app.models.enums import AlertSeverity, ChannelType, DeliveryStatus, EventLevel
from app.providers.notification_sender import NotificationError, send_email, send_webhook
from app.schemas.channel import ChannelCreate, ChannelUpdate, EmailConfig, WebhookConfig
from app.services import alert_service, audit_service, event_bus

log = get_logger("nexusops.notifications")

MAX_ATTEMPTS = 5
BASE_RETRY_SECONDS = 30
MAX_RETRY_SECONDS = 3600
SEND_CONCURRENCY = 5
RETRY_SWEEP_SECONDS = 30.0
ERROR_BACKOFF_AFTER = 3

#: Subject templates keyed by event type (bodies share one plain-text layout).
_SUBJECTS: dict[str, str] = {
    "MONITOR_DOWN": "[CRITICAL] Monitor DOWN: {resource}",
    "MONITOR_RECOVERED": "[INFO] Monitor recovered: {resource}",
    "INCIDENT_OPENED": "[MAJOR] Incident opened: {resource}",
    "INCIDENT_RESOLVED": "[INFO] Incident resolved: {resource}",
    "SERVER_OFFLINE": "[CRITICAL] Server offline: {resource}",
    "DEPLOYMENT_FAILED": "[CRITICAL] Deployment failed: {resource}",
}
_DEFAULT_SUBJECT = "[NexusOps] {type}"
_BODY_TEMPLATE = (
    "NexusOps event\n\nType: {type}\nResource: {resource}\nDetail: {message}\nTime: {created_at}\n"
)


def _now() -> datetime:
    return datetime.now(UTC)


async def _audit(
    db: AsyncSession,
    ctx: AuthContext | None,
    action: str,
    channel_id: uuid.UUID | str,
    *,
    request: Request | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    await audit_service.record(
        db,
        ctx,
        action=action,
        resource_type="notification_channel",
        resource_id=channel_id,
        request=request,
        metadata=metadata,
    )


# --- Config encryption & masking -----------------------------------------------


def encrypt_config(config: dict[str, Any]) -> str:
    """Encrypt the whole provider config blob for storage."""
    return encrypt_str(orjson.dumps(config).decode())


def decrypt_channel_config(channel: NotificationChannel) -> dict[str, Any]:
    """Decrypt a channel's config. Raises ValueError when the key has rotated."""
    return orjson.loads(decrypt_str(channel.config_ciphertext))


def mask_target(channel_type: ChannelType, config: dict[str, Any]) -> str:
    """Human-readable masked target safe to expose over the API.

    For webhook families the credential IS the path — Slack
    ``/services/T/B/XXXX``, Discord ``/api/webhooks/{id}/{token}``, Telegram
    ``/bot<TOKEN>/sendMessage`` — so the display reference never includes the
    path (or the query). The full URL stays inside the encrypted config blob.
    """
    if channel_type == ChannelType.EMAIL:
        recipients = [str(r) for r in config.get("recipients", [])]
        if not recipients:
            return ""
        extra = len(recipients) - 1
        return recipients[0] if extra < 1 else f"{recipients[0]} (+{extra} more)"
    parsed = urlparse(str(config.get("url", "")))
    if not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}/..."


async def validated_config(
    channel_type: ChannelType, config: EmailConfig | WebhookConfig
) -> dict[str, Any]:
    """Validate a schema config into its encrypted-at-rest dict form."""
    if channel_type == ChannelType.EMAIL:
        if not isinstance(config, EmailConfig):
            raise BadRequest("EMAIL channels require an email config")
        return {"recipients": [str(r) for r in config.recipients]}
    if not isinstance(config, WebhookConfig):
        raise BadRequest("WEBHOOK channels require a webhook config")
    await assert_safe_url_async(str(config.url))  # SSRF guard: webhooks are server-side fetches
    return {
        "url": str(config.url),
        "headers": {str(k): str(v) for k, v in (config.headers or {}).items()},
        "secret_header": (
            {"name": config.secret_header.name, "value": config.secret_header.value}
            if config.secret_header
            else None
        ),
    }


# --- Channel CRUD ---------------------------------------------------------------


async def require_channel(db: AsyncSession, channel_id: uuid.UUID) -> NotificationChannel:
    channel = (
        await db.execute(select(NotificationChannel).where(NotificationChannel.id == channel_id))
    ).scalar_one_or_none()
    if channel is None:
        raise NotFound("Notification channel not found")
    return channel


def _normalize_events(events: list[str] | None) -> list[str]:
    return [e.strip().upper()[:64] for e in (events or []) if e.strip()][:32]


async def create_channel(
    db: AsyncSession,
    ctx: AuthContext | None,
    data: ChannelCreate,
    *,
    request: Request | None = None,
) -> NotificationChannel:
    config = await validated_config(data.type, data.config)
    channel = NotificationChannel(
        name=data.name.strip(),
        type=data.type,
        config_ciphertext=encrypt_config(config),
        display_target=mask_target(data.type, config),
        events=_normalize_events(data.events),
        enabled=data.enabled,
        created_by_id=ctx.user_id if ctx else None,
    )
    db.add(channel)
    await db.flush()
    await _audit(
        db,
        ctx,
        "channel.create",
        channel.id,
        request=request,
        metadata={"type": channel.type.value, "target": channel.display_target},
    )
    return channel


async def update_channel(
    db: AsyncSession,
    ctx: AuthContext | None,
    channel: NotificationChannel,
    data: ChannelUpdate,
    *,
    request: Request | None = None,
) -> NotificationChannel:
    if data.name is not None:
        channel.name = data.name.strip()
    if data.events is not None:
        channel.events = _normalize_events(data.events)
    if data.enabled is not None:
        channel.enabled = data.enabled
    if data.config is not None:
        channel_type = data.type or (
            ChannelType.EMAIL if isinstance(data.config, EmailConfig) else ChannelType.WEBHOOK
        )
        channel.type = channel_type
        config = await validated_config(channel_type, data.config)
        channel.config_ciphertext = encrypt_config(config)
        channel.display_target = mask_target(channel_type, config)
    elif data.type is not None and data.type != channel.type:
        raise BadRequest("Changing channel type requires sending a new config")
    await db.flush()
    await _audit(
        db,
        ctx,
        "channel.update",
        channel.id,
        request=request,
        metadata={"type": channel.type.value},
    )
    return channel


async def delete_channel(
    db: AsyncSession,
    ctx: AuthContext | None,
    channel: NotificationChannel,
    *,
    request: Request | None = None,
) -> None:
    channel_id, name = str(channel.id), channel.name
    await db.delete(channel)
    await db.flush()
    await _audit(db, ctx, "channel.delete", channel_id, request=request, metadata={"name": name})


# --- Rendering -------------------------------------------------------------------


def render_frame(frame: dict[str, Any]) -> tuple[str, str]:
    """Render an event frame into an ASCII-safe ``(subject, body)`` pair."""
    data = frame.get("data") or {}
    context = {
        "type": str(frame.get("type", "EVENT")).upper(),
        "level": str(frame.get("level", "INFO")),
        "message": str(frame.get("message", ""))[:500],
        "resource": str(
            data.get("monitor_name")
            or frame.get("resource_id")
            or frame.get("resource_type")
            or "-"
        ),
        "created_at": str(frame.get("created_at") or _now().isoformat()),
    }
    subject_tpl = _SUBJECTS.get(context["type"], _DEFAULT_SUBJECT)
    subject = subject_tpl.format(**context).encode("ascii", "replace").decode()[:300]
    body = _BODY_TEMPLATE.format(**context).encode("ascii", "replace").decode()[:8000]
    return subject, body


# --- Sending ---------------------------------------------------------------------


async def _invoke_sender(
    channel_type: ChannelType,
    config: dict[str, Any],
    *,
    subject: str,
    body: str,
    event_type: str = "",
) -> tuple[DeliveryStatus, str]:
    """Call the transport for *channel_type*. Never raises."""
    settings = get_settings()
    try:
        if channel_type == ChannelType.WEBHOOK:
            secret = config.get("secret_header")
            await send_webhook(
                url=str(config["url"]),
                headers={str(k): str(v) for k, v in (config.get("headers") or {}).items()},
                payload={"event_type": event_type, "subject": subject, "body": body},
                secret_header=(
                    (str(secret["name"]), str(secret["value"]))
                    if isinstance(secret, dict)
                    else None
                ),
            )
        elif channel_type == ChannelType.EMAIL:
            await send_email(
                host=settings.smtp_host,
                port=settings.smtp_port,
                user=settings.smtp_user,
                password=settings.smtp_password,
                from_addr=settings.smtp_from,
                tls=settings.smtp_tls,
                subject=subject,
                body=body,
                recipients=[str(r) for r in config.get("recipients", [])],
            )
        else:
            raise NotificationError(f"unsupported channel type {channel_type}")
        return DeliveryStatus.SENT, ""
    except NotificationError as exc:
        return DeliveryStatus.FAILED, str(exc)
    except Exception as exc:
        log.warning("delivery_unexpected_error", reason=exc.__class__.__name__)
        return DeliveryStatus.FAILED, f"unexpected {exc.__class__.__name__}"


async def send_delivery(db: AsyncSession, delivery_id: uuid.UUID) -> None:
    """Attempt one delivery and record the outcome. Commits; never raises."""
    try:
        delivery = (
            await db.execute(
                select(NotificationDelivery).where(NotificationDelivery.id == delivery_id)
            )
        ).scalar_one_or_none()
        if delivery is None:
            return
        channel = (
            await db.execute(
                select(NotificationChannel).where(NotificationChannel.id == delivery.channel_id)
            )
        ).scalar_one_or_none()
        if channel is None:
            return

        delivery.attempts += 1
        error = ""
        try:
            config = decrypt_channel_config(channel)
        except ValueError as exc:
            log.warning("delivery_decrypt_failed", reason=str(exc)[:120])
            error = "decryption failed"
        else:
            _, error = await _invoke_sender(
                channel.type,
                config,
                subject=delivery.subject,
                body=delivery.body,
                event_type=delivery.event_type,
            )

        now = _now()
        if not error:
            delivery.status = DeliveryStatus.SENT
            delivery.sent_at = now
            delivery.last_error = ""
        else:
            delivery.status = DeliveryStatus.FAILED
            delivery.last_error = error[:2000]
            if delivery.attempts < MAX_ATTEMPTS:
                delay = min(2**delivery.attempts * BASE_RETRY_SECONDS, MAX_RETRY_SECONDS)
                delivery.next_retry_at = now + timedelta(seconds=delay)
            else:  # terminal failure — page an operator once
                delivery.next_retry_at = None
                await event_bus.publish(
                    db,
                    type="NOTIFICATION_FAILED",
                    message=f"Delivery to {channel.name} failed permanently",
                    level=EventLevel.WARNING,
                    resource_type="notification_channel",
                    resource_id=str(channel.id),
                    data={"delivery_id": str(delivery.id), "error": error[:300]},
                    dedup_key=f"notify-failed:{delivery.id}",
                )
                await alert_service.create_alert(
                    db,
                    event_type="NOTIFICATION_FAILED",
                    severity=AlertSeverity.WARNING,
                    title=f"Notifications to {channel.name} are failing",
                    body=error[:500],
                    source="notifications",
                    resource_type="notification_channel",
                    resource_id=str(channel.id),
                )
        await db.commit()
    except Exception as exc:
        await db.rollback()
        log.warning("delivery_send_error", reason=exc.__class__.__name__)


async def retry_due_deliveries(db: AsyncSession, limit: int = 50) -> int:
    """Send every due PENDING / retryable-FAILED delivery. Returns count attempted."""
    due_ids = (
        (
            await db.execute(
                select(NotificationDelivery.id)
                .where(
                    or_(
                        NotificationDelivery.status == DeliveryStatus.PENDING,
                        and_(
                            NotificationDelivery.status == DeliveryStatus.FAILED,
                            NotificationDelivery.attempts < MAX_ATTEMPTS,
                        ),
                    ),
                    NotificationDelivery.next_retry_at.is_not(None),
                    NotificationDelivery.next_retry_at <= _now(),
                )
                .order_by(NotificationDelivery.next_retry_at)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )

    attempted = 0
    for delivery_id in due_ids:
        await send_delivery(db, delivery_id)
        attempted += 1
    return attempted


def _as_uuid(value: Any) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(value)) if value else None
    except (TypeError, ValueError):
        return None


async def dispatch_event_frame(frame: dict[str, Any]) -> int:
    """Queue an event frame to every subscribed enabled channel; send immediately.

    Returns how many deliveries were queued.
    """
    event_type = str(frame.get("type", "")).upper()[:64]
    if not event_type:
        return 0
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as db:
        channels = (
            (
                await db.execute(
                    select(NotificationChannel).where(
                        NotificationChannel.enabled.is_(True),
                        or_(
                            func.jsonb_array_length(NotificationChannel.events) == 0,
                            NotificationChannel.events.contains([event_type]),
                        ),
                    )
                )
            )
            .scalars()
            .all()
        )
        if not channels:
            return 0
        subject, body = render_frame(frame)
        # Idempotent insert: every API worker runs this dispatcher and pubsub
        # broadcasts each frame to all of them — without ON CONFLICT each
        # worker queued (and emailed) its own delivery for the same
        # (channel, event). The unique constraint is the arbiter; only the
        # first inserter proceeds to send, and the frame's own workers see an
        # empty RETURNING. Manual/test sends carry NULL event_id and are
        # exempt (Postgres treats NULLs as distinct).
        event_id = _as_uuid(frame.get("id"))
        incident_id = _as_uuid((frame.get("data") or {}).get("incident_id"))
        stmt = (
            pg_insert(NotificationDelivery)
            .values(
                [
                    {
                        "channel_id": channel.id,
                        "event_id": event_id,
                        "incident_id": incident_id,
                        "event_type": event_type,
                        "subject": subject,
                        "body": body,
                        "status": DeliveryStatus.PENDING.value,
                        "attempts": 0,
                        "next_retry_at": _now(),
                    }
                    for channel in channels
                ]
            )
            .on_conflict_do_nothing(constraint="uq_deliveries_channel_event")
            .returning(NotificationDelivery.id)
        )
        delivery_ids = list((await db.execute(stmt)).scalars().all())
        await db.commit()
        if not delivery_ids:
            return 0

    semaphore = asyncio.Semaphore(SEND_CONCURRENCY)

    async def _send(delivery_id: uuid.UUID) -> None:
        async with semaphore:
            try:
                async with sessionmaker() as db:
                    await send_delivery(db, delivery_id)
            except Exception as exc:  # isolation: one bad channel never blocks others
                log.warning("dispatch_send_failed", reason=exc.__class__.__name__)

    await asyncio.gather(*(_send(i) for i in delivery_ids))
    return len(delivery_ids)


# --- Test notifications ------------------------------------------------------------


async def send_test_notification(
    db: AsyncSession,
    ctx: AuthContext | None,
    channel: NotificationChannel,
    *,
    request: Request | None = None,
) -> tuple[DeliveryStatus, str]:
    """Fire a TEST delivery straight through the sender; audit and report result."""
    subject, body = render_frame(
        {
            "type": "CHANNEL_TEST",
            "level": "INFO",
            "message": f"This is a test notification from NexusOps for channel {channel.name}.",
            "resource_type": "notification_channel",
            "resource_id": str(channel.id),
            "created_at": _now().isoformat(),
        }
    )
    try:
        config = decrypt_channel_config(channel)
        result_status, error = await _invoke_sender(
            channel.type, config, subject=subject, body=body, event_type="CHANNEL_TEST"
        )
    except ValueError as exc:
        result_status, error = DeliveryStatus.FAILED, "decryption failed"
        log.warning("test_notification_decrypt_failed", reason=str(exc)[:120])

    db.add(
        NotificationDelivery(
            channel_id=channel.id,
            event_type="CHANNEL_TEST",
            subject=subject,
            body=body,
            status=result_status,
            attempts=1,
            last_error=error[:2000],
            sent_at=_now() if result_status == DeliveryStatus.SENT else None,
            next_retry_at=None,
        )
    )
    await _audit(
        db,
        ctx,
        "channel.test",
        channel.id,
        request=request,
        metadata={"status": result_status.value},
    )
    return result_status, error


# --- Deliveries listing (keyset on next_retry_at/id) -------------------------------


def encode_delivery_cursor(ts: datetime, delivery_id: uuid.UUID) -> str:
    raw = orjson.dumps({"t": ts.isoformat(), "i": str(delivery_id)}).decode()
    return base64.urlsafe_b64encode(raw.encode()).decode()


def decode_delivery_cursor(cursor: str | None) -> tuple[datetime, uuid.UUID] | None:
    if not cursor:
        return None
    try:
        data = orjson.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
        ts = datetime.fromisoformat(str(data["t"]))
        return ts, uuid.UUID(str(data["i"]))
    except (KeyError, ValueError, TypeError, binascii.Error, UnicodeDecodeError):
        return None


async def list_deliveries(
    db: AsyncSession,
    *,
    channel_id: uuid.UUID | None = None,
    status: DeliveryStatus | None = None,
    params: CursorParams,
) -> tuple[list[NotificationDelivery], str | None, bool]:
    stmt = select(NotificationDelivery)
    if channel_id is not None:
        stmt = stmt.where(NotificationDelivery.channel_id == channel_id)
    if status is not None:
        stmt = stmt.where(NotificationDelivery.status == status)
    cursor = decode_delivery_cursor(params.cursor)
    if cursor is not None:
        ts, delivery_id = cursor
        stmt = stmt.where(
            tuple_(NotificationDelivery.next_retry_at, NotificationDelivery.id) < (ts, delivery_id)
        )
    stmt = stmt.order_by(NotificationDelivery.next_retry_at.desc(), NotificationDelivery.id.desc())
    rows = (await db.execute(stmt.limit(params.limit + 1))).scalars().all()
    has_more = len(rows) > params.limit
    rows = rows[: params.limit]
    next_cursor = (
        encode_delivery_cursor(rows[-1].next_retry_at or _now(), rows[-1].id)
        if has_more and rows
        else None
    )
    return list(rows), next_cursor, has_more


# --- Background dispatcher -----------------------------------------------------------


async def dispatcher_loop(poll_seconds: float = 1.0) -> NoReturn:
    """Consume ``nx:events`` and sweep due retries forever. Runs as a lifespan task."""
    sessionmaker: async_sessionmaker[AsyncSession] = get_sessionmaker()
    pubsub = get_redis().pubsub(ignore_subscribe_messages=True)
    await pubsub.subscribe(CHANNEL_EVENTS)
    last_sweep = 0.0
    consecutive_errors = 0
    log.info("notification_dispatcher_started")
    try:
        while True:
            try:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=poll_seconds
                )
                if message and isinstance(message.get("data"), (str, bytes, bytearray)):
                    try:
                        frame = orjson.loads(message["data"])
                    except orjson.JSONDecodeError:
                        frame = None
                    if isinstance(frame, dict):
                        await dispatch_event_frame(frame)
                if time.monotonic() - last_sweep >= RETRY_SWEEP_SECONDS:
                    last_sweep = time.monotonic()
                    retried = 0
                    async with sessionmaker() as db:
                        retried = await retry_due_deliveries(db)
                    if retried:
                        log.info("deliveries_retried", count=retried)
                consecutive_errors = 0
            except asyncio.CancelledError:
                raise
            except Exception:
                consecutive_errors += 1
                log.error("dispatcher_loop_error", consecutive=consecutive_errors, exc_info=True)
                if consecutive_errors >= ERROR_BACKOFF_AFTER:
                    await asyncio.sleep(5.0)  # back off when the loop misbehaves repeatedly
    finally:
        try:
            await pubsub.aclose()
        except Exception as exc:  # pragma: no cover - shutdown best effort
            log.warning("dispatcher_pubsub_close_failed", reason=exc.__class__.__name__)
