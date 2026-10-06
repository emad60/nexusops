"""WebSocket hub tenancy: one socket, one organization, no cross-tenant fan-out.

``nx:events`` is a single Redis channel carrying every tenant's events, so the
organization stamped on each frame is the *only* thing keeping a live stream
inside its own tenant. These tests drive :meth:`Hub._route` directly (it is a
pure function of the connection registry and one Redis message) so the delivery
decision is asserted without a broker, a socket or a database.

They also pin the subscribe-time check for per-entity channels
(``nx:deploy:<id>`` and friends): that path delivers by subscription key alone,
so the existence check performed under the socket's organization scope is what
stops a foreign id from ever becoming a subscription in the first place.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

import orjson
import pytest
from app.core.channels import (
    CHANNEL_EVENTS,
    WS_CHANNEL_DEPLOYMENT_LOGS,
    WS_CHANNEL_GLOBAL,
    WS_CHANNEL_INCIDENTS,
)
from app.ws import hub as hub_module
from app.ws.hub import Connection, Hub, _is_same_origin

ORG_A = uuid.UUID("11111111-1111-4111-8111-111111111111")
ORG_B = uuid.UUID("22222222-2222-4222-8222-222222222222")


@dataclass
class _User:
    is_superadmin: bool = True


@dataclass
class _Org:
    id: uuid.UUID


@dataclass
class _Stub:
    user: _User = field(default_factory=_User)
    org: _Org | None = None

    @property
    def org_id(self) -> uuid.UUID | None:
        return self.org.id if self.org is not None else None

    def has_permission(self, codename: str) -> bool:
        return True

    def require_org_id(self) -> uuid.UUID:
        org_id = self.org_id
        if org_id is None:  # pragma: no cover - the socket always has one
            raise AssertionError("stub socket has no organization")
        return org_id


def _connection(org_id: uuid.UUID, *subscriptions: tuple[str, str]) -> Connection:
    conn = Connection(  # type: ignore[arg-type] - a stub auth is enough for routing
        ws=object(),  # never touched by _route
        id=uuid.uuid4(),
        auth=_Stub(org=_Org(id=org_id)),  # type: ignore[arg-type]
    )
    for channel in subscriptions:
        conn.subscriptions[channel] = {}
    return conn


def _drain(conn: Connection) -> list[dict[str, Any]]:
    frames = []
    while not conn.queue.empty():
        frames.append(conn.queue.get_nowait())
    return frames


def _event_frame(org_id: uuid.UUID | None, event_type: str = "SERVER_STATUS") -> dict[str, Any]:
    payload: dict[str, Any] = {"type": event_type, "message": "hello"}
    if org_id is not None:
        payload["org_id"] = str(org_id)
    return {"channel": CHANNEL_EVENTS, "data": orjson.dumps(payload)}


@pytest.fixture
def hub() -> Hub:
    return Hub()


def test_same_origin_compares_the_full_authority_including_port() -> None:
    """The proxy must forward the Host the browser actually used.

    A browser sends ``Origin`` with its port; the same-origin fallback compares
    it against the ``Host`` the socket was reached on. nginx's default ``$host``
    drops the port, so the edge sent ``Host: 127.0.0.1`` for an origin of
    ``http://127.0.0.1:8090`` and every handshake was refused with a
    pre-upgrade 403 (the intermittent live-event failure). The fix is in
    ``nginx/default.conf.template`` (``$http_host``); this test pins the
    comparison that required it.
    """
    assert _is_same_origin("http://127.0.0.1:8090", "127.0.0.1:8090") is True
    assert _is_same_origin("https://nexusops.example.com", "nexusops.example.com") is True
    # A port-stripped Host is a different authority — exactly the broken case.
    assert _is_same_origin("http://127.0.0.1:8090", "127.0.0.1") is False
    # A foreign origin is never same-origin, port or not.
    assert _is_same_origin("http://evil.example", "127.0.0.1:8090") is False
    assert _is_same_origin("http://127.0.0.1:8090", None) is False


def test_an_event_reaches_only_its_own_tenants_sockets(hub: Hub) -> None:
    a = _connection(ORG_A, (WS_CHANNEL_GLOBAL, ""), (WS_CHANNEL_INCIDENTS, ""))
    b = _connection(ORG_B, (WS_CHANNEL_GLOBAL, ""), (WS_CHANNEL_INCIDENTS, ""))
    hub._connections.update({a, b})

    hub._route(_event_frame(ORG_A, "INCIDENT_OPENED"))

    a_frames = _drain(a)
    assert [f["channel"] for f in a_frames] == [WS_CHANNEL_GLOBAL, WS_CHANNEL_INCIDENTS]
    # Organization B generates nothing and receives nothing.
    assert _drain(b) == []

    hub._route(_event_frame(ORG_B, "INCIDENT_OPENED"))

    assert [f["channel"] for f in _drain(b)] == [WS_CHANNEL_GLOBAL, WS_CHANNEL_INCIDENTS]
    assert _drain(a) == []


def test_an_orgless_event_is_delivered_to_nobody(hub: Hub) -> None:
    a = _connection(ORG_A, (WS_CHANNEL_GLOBAL, ""))
    hub._connections.add(a)

    hub._route(_event_frame(None))
    hub._route({"channel": CHANNEL_EVENTS, "data": "not json at all"})

    # A frame with no organization belongs to no tenant, so there is no socket
    # it could safely be shown to.
    assert _drain(a) == []


def test_a_malformed_org_on_the_frame_is_not_trusted(hub: Hub) -> None:
    a = _connection(ORG_A, (WS_CHANNEL_GLOBAL, ""))
    hub._connections.add(a)

    hub._route({"channel": CHANNEL_EVENTS, "data": '{"type": "X", "org_id": "not-a-uuid"}'})

    assert _drain(a) == []


def test_incidents_channel_only_carries_incident_frames(hub: Hub) -> None:
    a = _connection(ORG_A, (WS_CHANNEL_GLOBAL, ""), (WS_CHANNEL_INCIDENTS, ""))
    hub._connections.add(a)

    hub._route(_event_frame(ORG_A, "SERVER_STATUS"))

    # Global subscribers see everything; the incident feed is narrower on purpose.
    assert [f["channel"] for f in _drain(a)] == [WS_CHANNEL_GLOBAL]


def test_per_entity_channels_deliver_by_subscription_key(hub: Hub) -> None:
    deployment_id = uuid.uuid4()
    subscriber = _connection(ORG_A, (WS_CHANNEL_DEPLOYMENT_LOGS, f"deployment_id={deployment_id}"))
    other = _connection(ORG_A, (WS_CHANNEL_DEPLOYMENT_LOGS, f"deployment_id={uuid.uuid4()}"))
    hub._connections.update({subscriber, other})

    hub._route({"channel": f"nx:deploy:{deployment_id}", "data": '{"line": "npm ci"}'})

    assert len(_drain(subscriber)) == 1
    assert _drain(other) == []


class _FakeSession:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, *exc: Any) -> None:
        return None


def _fake_sessionmaker() -> Any:
    return _FakeSession


async def test_subscribing_checks_the_entity_inside_the_sockets_organization(
    hub: Hub, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The per-entity existence check must run scoped to the socket's org.

    Delivery for these channels is by subscription key alone, so this check is
    the boundary: if it were unscoped, an id from another tenant would resolve
    and become a subscription that streams that tenant's logs.
    """
    calls: list[dict[str, Any]] = []

    async def fake_exists(db: Any, model: Any, id_: Any, *, org_id: uuid.UUID) -> bool:
        calls.append({"model": model.__name__, "id": id_, "org_id": org_id})
        return False  # a foreign id is indistinguishable from a missing one

    monkeypatch.setattr(hub_module, "_entity_exists", fake_exists)
    monkeypatch.setattr(hub_module, "get_sessionmaker", _fake_sessionmaker)

    deployment_id = uuid.uuid4()
    conn = _connection(ORG_A)  # no subscription yet
    hub._connections.add(conn)

    await hub._handle_message(
        conn,
        {
            "action": "subscribe",
            "channel": WS_CHANNEL_DEPLOYMENT_LOGS,
            "params": {"deployment_id": str(deployment_id)},
        },
    )

    assert calls == [{"model": "Deployment", "id": deployment_id, "org_id": ORG_A}]
    assert _drain(conn) == [{"type": "error", "code": "NOT_FOUND"}]
    assert conn.subscriptions == {}  # nothing was subscribed


async def test_subscribe_is_refused_without_the_channels_permission(
    hub: Hub, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Permission checks run on every subscribe frame, not only at auth time."""

    async def fake_exists(*args: Any, **kwargs: Any) -> bool:  # pragma: no cover
        raise AssertionError("the permission check must run before the entity check")

    monkeypatch.setattr(hub_module, "_entity_exists", fake_exists)

    conn = _connection(ORG_A)
    conn.auth.has_permission = lambda codename: False  # type: ignore[method-assign]
    hub._connections.add(conn)

    await hub._handle_message(
        conn,
        {
            "action": "subscribe",
            "channel": WS_CHANNEL_DEPLOYMENT_LOGS,
            "params": {"deployment_id": str(uuid.uuid4())},
        },
    )

    assert _drain(conn) == [{"type": "error", "code": "FORBIDDEN"}]


async def test_unknown_channel_is_refused(hub: Hub) -> None:
    conn = _connection(ORG_A)
    hub._connections.add(conn)

    await hub._handle_message(conn, {"action": "subscribe", "channel": "not-a-channel"})

    assert _drain(conn) == [{"type": "error", "code": "UNKNOWN_CHANNEL"}]
