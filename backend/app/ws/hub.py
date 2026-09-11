"""WebSocket hub: authenticated live streams fanned in from Redis pub/sub.

Channels: ``global`` (all events, ``event.read``), ``incidents``
(``INCIDENT_*``/``MONITOR_*`` only, ``monitor.read``), ``server-metrics``
(``nx:metrics:<server_id>``, ``metric.read``+``server.read``),
``container-logs`` (``nx:logs:<container_id>``, ``container.logs``) and
``deployment-logs`` (``nx:deploy:<deployment_id>``, ``deployment.read``).

Permissions are re-checked on every subscribe frame; entity existence is
validated against the database. This module depends only on models, core and
the :class:`~app.api.deps.AuthContext` dataclass — no FastAPI request stack.
"""

from __future__ import annotations

import asyncio
import contextlib
import time
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, cast
from urllib.parse import urlparse

import orjson
from redis.exceptions import TimeoutError as RedisTimeoutError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocket, WebSocketDisconnect

from app.api.deps import AuthContext
from app.core.channels import (
    CHANNEL_EVENTS,
    WS_CHANNEL_CONTAINER_LOGS,
    WS_CHANNEL_DEPLOYMENT_LOGS,
    WS_CHANNEL_GLOBAL,
    WS_CHANNEL_INCIDENTS,
    WS_CHANNEL_SERVER_METRICS,
)
from app.core.config import get_settings
from app.core.db import get_sessionmaker
from app.core.errors import AppError
from app.core.logging import get_logger
from app.core.permissions import WILDCARD
from app.core.redis_client import get_redis
from app.core.security import decode_access_token, hash_token
from app.models import ApiKey, Container, Deployment, Server, User
from app.models import Session as DbSession
from app.services.event_registry import INCIDENT_CHANNEL_PREFIXES

log = get_logger("nexusops.ws")

AUTH_TIMEOUT_SECONDS = 10
IDLE_TIMEOUT_SECONDS = 120
WATCHDOG_INTERVAL_SECONDS = 15
MAX_SUBSCRIPTIONS = 50
QUEUE_MAXSIZE = 1000
LISTENER_RETRY_SECONDS = 5

CLOSE_UNAUTHORIZED = 4401
CLOSE_FORBIDDEN_ORIGIN = 4403
CLOSE_TOO_MANY_SUBSCRIPTIONS = 4408
CLOSE_IDLE_TIMEOUT = 1001
CLOSE_SERVICE_RESTART = 1012

#: Redis pattern subscriptions consumed by the fan-in listener.
REDIS_PATTERNS: tuple[str, ...] = ("nx:logs:*", "nx:deploy:*", "nx:metrics:*")


@dataclass(slots=True, eq=False)
class Connection:
    """One authenticated socket and its outbound queue.

    ``eq=False`` is load-bearing: the default dataclass ``__eq__`` sets
    ``__hash__ = None``, which makes instances unhashable and blew up the
    moment a live socket was added to the ``Hub._connections`` set (every
    browser connection died with ``TypeError: unhashable type`` — masked for
    months by the origin check rejecting connections before this line).
    """

    ws: WebSocket
    id: uuid.UUID
    auth: AuthContext
    subscriptions: dict[tuple[str, str], dict[str, str]] = field(default_factory=dict)
    queue: asyncio.Queue[dict[str, Any]] = field(
        default_factory=lambda: asyncio.Queue(maxsize=QUEUE_MAXSIZE)
    )
    alive: bool = True
    last_activity: float = field(default_factory=time.monotonic)


def _params_key(params: dict[str, str]) -> str:
    return ",".join(f"{k}={v}" for k, v in sorted(params.items()))


async def _close_socket(socket: WebSocket, code: int, reason: str) -> None:
    with contextlib.suppress(Exception):
        await socket.close(code=code, reason=reason)


def _is_same_origin(origin: str, host: str | None) -> bool:
    """Browsers always send Origin on WS handshakes, even same-origin ones.

    When it matches the Host the page was served from, the request is
    same-origin and inherently trustworthy — the configured allowlist governs
    cross-origin clients only. Comparing netlocs (not raw strings) keeps the
    check honest about default ports.
    """
    if not host:
        return False
    return urlparse(origin).netloc.rstrip("/") == host.rstrip("/")


async def _load_permissions(db: AsyncSession, user: User) -> set[str]:
    """Resolve a user's permission codenames exactly like the HTTP path."""
    if user.is_superadmin:
        return {WILDCARD}
    # User.role and Role.permissions are both lazy="selectin", so after any
    # query-loaded user these attributes are already in memory — no IO needed
    # (mirrors deps._load_permissions; User's Base has no AsyncAttrs mixin).
    role = user.role
    if role is None:
        return set()
    return {p.codename for p in role.permissions}


async def _authenticate_jwt(db: AsyncSession, token: str) -> AuthContext:
    """Bearer-JWT auth mirroring ``deps.resolve_auth`` without Request."""
    payload = decode_access_token(token)  # raises Unauthorized on any problem
    try:
        user_id = uuid.UUID(str(payload["sub"]))
        session_id = uuid.UUID(str(payload["sid"]))
    except (KeyError, ValueError) as exc:
        raise AppError("Malformed token claims", code="UNAUTHORIZED") from exc

    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user is None or not user.is_active:
        raise AppError("Account is inactive", code="UNAUTHORIZED")

    sess = (
        await db.execute(select(DbSession).where(DbSession.id == session_id))
    ).scalar_one_or_none()
    if sess is None or sess.revoked_at is not None:
        raise AppError("Session revoked", code="UNAUTHORIZED")
    now = datetime.now(UTC)
    if sess.expires_at < now:
        raise AppError("Session expired", code="UNAUTHORIZED")
    sess.last_seen_at = now

    ctx = AuthContext(user=user, actor_type="USER", session_id=session_id)
    ctx._permission_set = await _load_permissions(db, user)
    await db.commit()
    return ctx


async def _authenticate_api_key(db: AsyncSession, raw_key: str) -> AuthContext:
    """X-API-Key auth mirroring ``deps.resolve_auth``."""
    row = (
        await db.execute(select(ApiKey).where(ApiKey.key_hash == hash_token(raw_key)))
    ).scalar_one_or_none()
    if row is None or row.revoked_at is not None:
        raise AppError("Invalid API key", code="UNAUTHORIZED")
    now = datetime.now(UTC)
    if row.expires_at is not None and row.expires_at < now:
        raise AppError("API key expired", code="UNAUTHORIZED")
    user = (await db.execute(select(User).where(User.id == row.user_id))).scalar_one_or_none()
    if user is None or not user.is_active:
        raise AppError("API key owner is inactive", code="UNAUTHORIZED")
    ctx = AuthContext(user=user, actor_type="API_KEY", api_key=row)
    ctx._permission_set = await _load_permissions(db, user)
    if row.last_used_at is None or (now - row.last_used_at).total_seconds() > 60:
        row.last_used_at = now
        await db.commit()
    return ctx


async def _entity_exists(db: AsyncSession, model: type[Any], id_: Any) -> bool:
    return (
        await db.execute(select(model.id).where(model.id == id_))
    ).scalar_one_or_none() is not None


class Hub:
    """Connection registry, Redis fan-in listener and per-socket pumps."""

    def __init__(self) -> None:
        self._connections: set[Connection] = set()
        self._listener_task: asyncio.Task[None] | None = None

    # --- lifecycle ----------------------------------------------------------

    def start(self) -> None:
        """Spawn the Redis fan-in listener (idempotent)."""
        if self._listener_task is None or self._listener_task.done():
            self._listener_task = asyncio.create_task(self._redis_listener())

    async def stop(self) -> None:
        """Cancel the listener and close every socket (service restart)."""
        if self._listener_task is not None:
            self._listener_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._listener_task
            self._listener_task = None
        for conn in list(self._connections):
            conn.alive = False
            await _close_socket(conn.ws, CLOSE_SERVICE_RESTART, "service restarting")
        self._connections.clear()

    # --- connection serving ---------------------------------------------------

    async def serve(self, websocket: WebSocket) -> None:
        """Origin check → accept → auth handshake → message loop."""
        origin = websocket.headers.get("origin")
        if (
            origin is not None
            and origin.rstrip("/") not in get_settings().cors_origin_list
            and not _is_same_origin(origin, websocket.headers.get("host"))
        ):
            await _close_socket(websocket, CLOSE_FORBIDDEN_ORIGIN, "origin not allowed")
            return

        await websocket.accept()

        try:
            async with asyncio.timeout(AUTH_TIMEOUT_SECONDS):
                first_frame = await websocket.receive_json()
        except WebSocketDisconnect:
            return  # client navigated away before authenticating — nothing to close
        except (TimeoutError, ValueError, KeyError, TypeError):
            await _close_socket(websocket, CLOSE_UNAUTHORIZED, "authentication timeout")
            return

        try:
            async with get_sessionmaker()() as db:
                auth = await self._authenticate(db, first_frame)
        except AppError as exc:
            log.info("ws_auth_rejected", code=exc.code)
            await _close_socket(websocket, CLOSE_UNAUTHORIZED, exc.code)
            return
        if auth is None:
            await _close_socket(websocket, CLOSE_UNAUTHORIZED, "bad auth frame")
            return

        conn = Connection(ws=websocket, id=uuid.uuid4(), auth=auth)
        self._connections.add(conn)
        log.info("ws_connected", connection=str(conn.id), actor_type=conn.auth.actor_type)

        sender = asyncio.create_task(self._sender_loop(conn), name=f"ws-sender-{conn.id}")
        watchdog = asyncio.create_task(self._watchdog_loop(conn), name=f"ws-watchdog-{conn.id}")
        try:
            while conn.alive:
                try:
                    message = await websocket.receive_json()
                except WebSocketDisconnect:
                    break
                except (RuntimeError, KeyError, TypeError, ValueError):
                    break  # transport closed mid-frame or non-JSON frame
                conn.last_activity = time.monotonic()
                if isinstance(message, dict):
                    await self._handle_message(conn, message)
                else:
                    self.enqueue(conn, {"type": "error", "code": "BAD_REQUEST"})
        finally:
            conn.alive = False
            sender.cancel()
            watchdog.cancel()
            for task in (sender, watchdog):
                with contextlib.suppress(asyncio.CancelledError):
                    await task
            self._connections.discard(conn)
            log.info("ws_disconnected", connection=str(conn.id))

    async def _authenticate(self, db: AsyncSession, frame: Any) -> AuthContext | None:
        """Validate the first frame; raises AppError on bad credentials."""
        if not isinstance(frame, dict):
            return None
        action = frame.get("action")
        if action == "auth" and isinstance(frame.get("token"), str):
            return await _authenticate_jwt(db, frame["token"])
        if action == "auth_apikey" and isinstance(frame.get("key"), str):
            return await _authenticate_api_key(db, frame["key"])
        return None

    # --- inbound frames -------------------------------------------------------

    async def _handle_message(self, conn: Connection, message: dict[str, Any]) -> None:
        action = message.get("action") or message.get("type")
        if action == "subscribe":
            await self._subscribe(conn, message)
        elif action == "unsubscribe":
            self._unsubscribe(conn, message)
        elif action == "ping":
            self.enqueue(conn, {"type": "pong"})
        else:
            self.enqueue(conn, {"type": "error", "code": "UNKNOWN_ACTION"})

    async def _subscribe(self, conn: Connection, message: dict[str, Any]) -> None:
        channel = str(message.get("channel") or "")
        raw_params = message.get("params") or {}
        if not isinstance(raw_params, dict):
            self.enqueue(conn, {"type": "error", "code": "BAD_REQUEST"})
            return
        params = {str(k): str(v) for k, v in raw_params.items()}

        requirement = self._requirement_for(channel)
        if requirement is None:
            self.enqueue(conn, {"type": "error", "code": "UNKNOWN_CHANNEL"})
            return

        codenames, param_name, model = requirement

        # Permission matrix enforced on EVERY subscribe frame.
        if not conn.auth.has_permission(codenames[0]) or not all(
            conn.auth.has_permission(c) for c in codenames
        ):
            self.enqueue(conn, {"type": "error", "code": "FORBIDDEN"})
            return

        if param_name is None:
            params = {}
        else:
            value = params.get(param_name, "")
            if not value:
                self.enqueue(conn, {"type": "error", "code": "BAD_REQUEST"})
                return
            try:
                entity_id = uuid.UUID(value)
            except ValueError:
                self.enqueue(conn, {"type": "error", "code": "NOT_FOUND"})
                return
            async with get_sessionmaker()() as db:
                # model is always set when param_name is (see _requirement_for)
                exists = await _entity_exists(db, cast(type[Any], model), entity_id)
            if not exists:
                self.enqueue(conn, {"type": "error", "code": "NOT_FOUND"})
                return

        key = (channel, _params_key(params))
        if key not in conn.subscriptions and len(conn.subscriptions) >= MAX_SUBSCRIPTIONS:
            await _close_socket(conn.ws, CLOSE_TOO_MANY_SUBSCRIPTIONS, "too many subscriptions")
            conn.alive = False
            return

        conn.subscriptions[key] = params
        self.enqueue(conn, {"type": "subscribed", "channel": channel, "params": params})

    def _requirement_for(
        self, channel: str
    ) -> tuple[tuple[str, ...], str | None, type | None] | None:
        """Return (required permissions, param name, model) for a channel."""
        if channel == WS_CHANNEL_GLOBAL:
            return (("event.read",), None, None)
        if channel == WS_CHANNEL_INCIDENTS:
            return (("monitor.read",), None, None)
        if channel == WS_CHANNEL_SERVER_METRICS:
            return (("metric.read", "server.read"), "server_id", Server)
        if channel == WS_CHANNEL_CONTAINER_LOGS:
            return (("container.logs",), "container_id", Container)
        if channel == WS_CHANNEL_DEPLOYMENT_LOGS:
            return (("deployment.read",), "deployment_id", Deployment)
        return None

    def _unsubscribe(self, conn: Connection, message: dict[str, Any]) -> None:
        channel = str(message.get("channel") or "")
        raw_params = message.get("params") or {}
        params = (
            {str(k): str(v) for k, v in raw_params.items()} if isinstance(raw_params, dict) else {}
        )
        removed = conn.subscriptions.pop((channel, _params_key(params)), None)
        if removed is None:
            self.enqueue(conn, {"type": "error", "code": "NOT_SUBSCRIBED"})
            return
        self.enqueue(conn, {"type": "unsubscribed", "channel": channel, "params": params})

    # --- outbound ---------------------------------------------------------------

    def enqueue(self, conn: Connection, frame: dict[str, Any]) -> None:
        """Queue a control/event frame; drop oldest on overflow."""
        try:
            conn.queue.put_nowait(frame)
        except asyncio.QueueFull:
            with contextlib.suppress(asyncio.QueueEmpty):
                conn.queue.get_nowait()
            with contextlib.suppress(asyncio.QueueFull):
                conn.queue.put_nowait(frame)
                conn.queue.put_nowait({"type": "notify", "code": "SLOW_CONSUMER_DROPPED"})

    def _push_event(
        self, conn: Connection, channel: str, params: dict[str, str], data: Any
    ) -> None:
        self.enqueue(
            conn,
            {
                "type": "event",
                "channel": channel,
                "params": params,
                "data": data if isinstance(data, dict) else {"message": str(data)},
            },
        )

    async def _sender_loop(self, conn: Connection) -> None:
        while conn.alive:
            try:
                frame = await conn.queue.get()
                await conn.ws.send_text(orjson.dumps(frame).decode())
            except asyncio.CancelledError:
                raise
            except Exception:
                conn.alive = False
                return

    async def _watchdog_loop(self, conn: Connection) -> None:
        while conn.alive:
            await asyncio.sleep(WATCHDOG_INTERVAL_SECONDS)
            if time.monotonic() - conn.last_activity > IDLE_TIMEOUT_SECONDS:
                log.info("ws_idle_timeout", connection=str(conn.id))
                conn.alive = False
                await _close_socket(conn.ws, CLOSE_IDLE_TIMEOUT, "idle timeout")
                return

    # --- Redis fan-in -------------------------------------------------------------

    async def _redis_listener(self) -> None:
        while True:
            pubsub = get_redis().pubsub()
            try:
                await pubsub.subscribe(CHANNEL_EVENTS)
                await pubsub.psubscribe(*REDIS_PATTERNS)
                # get_message loop, not listen(): the shared client sets
                # socket_timeout=5, so listen() raises TimeoutError every time
                # the channel goes idle. Treating that as a failure forced a
                # resubscribe every few seconds, and every event published
                # during a reconnect gap reached no WebSocket at all. Here the
                # idle timeout is swallowed and the ONE subscription persists;
                # parse_response runs check_health() before each read, so a
                # dead connection still surfaces as a real error below.
                while True:
                    try:
                        message = await pubsub.get_message(
                            ignore_subscribe_messages=True, timeout=5.0
                        )
                    except (TimeoutError, RedisTimeoutError):
                        continue  # idle window — subscription stays intact
                    if message is None or message.get("type") not in (
                        "message",
                        "pmessage",
                    ):
                        continue
                    try:
                        self._route(message)
                    except Exception as exc:
                        log.warning("ws_route_failed", error=str(exc))
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                log.warning("ws_redis_listener_retrying", error=str(exc))
                await asyncio.sleep(LISTENER_RETRY_SECONDS)
            finally:
                with contextlib.suppress(Exception):
                    await pubsub.aclose()

    def _route(self, message: dict[str, Any]) -> None:
        """Deliver one Redis message to every matching subscription."""
        channel = str(message.get("channel") or "")
        payload = _parse_payload(message.get("data"))

        if channel == CHANNEL_EVENTS:
            event_type = str(payload.get("type", "")) if isinstance(payload, dict) else ""
            incidentish = event_type.startswith(INCIDENT_CHANNEL_PREFIXES)
            for conn in list(self._connections):
                if (WS_CHANNEL_GLOBAL, "") in conn.subscriptions:
                    self._push_event(conn, WS_CHANNEL_GLOBAL, {}, payload)
                if (WS_CHANNEL_INCIDENTS, "") in conn.subscriptions and incidentish:
                    self._push_event(conn, WS_CHANNEL_INCIDENTS, {}, payload)
            return

        mapping = (
            ("nx:logs:", WS_CHANNEL_CONTAINER_LOGS, "container_id"),
            ("nx:deploy:", WS_CHANNEL_DEPLOYMENT_LOGS, "deployment_id"),
            ("nx:metrics:", WS_CHANNEL_SERVER_METRICS, "server_id"),
        )
        for prefix, ws_channel, param_name in mapping:
            if channel.startswith(prefix):
                entity_id = channel[len(prefix) :]
                wanted = (ws_channel, f"{param_name}={entity_id}")
                for conn in list(self._connections):
                    if wanted in conn.subscriptions:
                        self._push_event(conn, ws_channel, {param_name: entity_id}, payload)
                return


def _parse_payload(raw: Any) -> Any:
    """Decode a Redis-published body into a JSON-safe object."""
    if isinstance(raw, (bytes, bytearray, memoryview)):
        raw = bytes(raw).decode()
    if isinstance(raw, str):
        try:
            return orjson.loads(raw)
        except orjson.JSONDecodeError:
            return {"message": raw}
    return raw if raw is not None else {}


hub = Hub()
