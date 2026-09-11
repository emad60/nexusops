"""Notification channel + delivery-log endpoints.

Regression coverage for GET /notification-channels/deliveries: the response
model requires ``created_at``, which the delivery table originally lacked, so
every listing crashed with a pydantic ValidationError (HTTP 500).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from app.models import NotificationDelivery

from .helpers import API

pytestmark = pytest.mark.integration


async def _channel(client, owner) -> dict:
    response = await client.post(
        f"{API}/notification-channels",
        headers=owner["headers"],
        json={
            "type": "EMAIL",
            "name": "regression",
            "config": {"recipients": ["ops@nexusops.example.com"]},
            "events": ["MONITOR_DOWN"],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _delivery(db, channel_id: uuid.UUID) -> NotificationDelivery:
    row = NotificationDelivery(
        channel_id=channel_id,
        event_type="MONITOR_DOWN",
        subject="down",
        body="probe is down",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def test_list_deliveries_serializes_rows(client, owner, db):
    channel = await _channel(client, owner)
    await _delivery(db, uuid.UUID(channel["id"]))

    response = await client.get(
        f"{API}/notification-channels/deliveries?limit=20",
        headers=owner["headers"],
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["items"], "the freshly created delivery must appear"
    item = next(d for d in body["items"] if d["event_type"] == "MONITOR_DOWN")
    assert item["channel_id"] == channel["id"]
    # OutModel contract: every row serializes a server timestamp.
    assert datetime.fromisoformat(item["created_at"].replace("Z", "+00:00")) <= datetime.now(UTC)


async def test_list_deliveries_filters_by_channel(client, owner, db):
    channel = await _channel(client, owner)
    await _delivery(db, uuid.UUID(channel["id"]))

    other = await _channel(client, owner)
    response = await client.get(
        f"{API}/notification-channels/deliveries?channel_id={other['id']}",
        headers=owner["headers"],
    )
    assert response.status_code == 200, response.text
    assert all(d["channel_id"] == other["id"] for d in response.json()["items"])


async def test_dispatch_frame_is_idempotent_across_workers(client, owner, db):
    """The same event frame consumed twice queues ONE delivery per channel.

    Every API worker runs the dispatcher and Redis pubsub broadcasts each
    frame to all of them — before the uq_deliveries_channel_event constraint
    each worker queued (and emailed) its own delivery for the same event.
    """
    from app.models import NotificationChannel, SystemEvent
    from app.models.enums import EventLevel
    from app.services.notification_service import dispatch_event_frame
    from sqlalchemy import select

    channel = await _channel(client, owner)
    # A real event row: the delivery FK references system_events.
    event = SystemEvent(type="MONITOR_DOWN", level=EventLevel.INFO, message="probe down", data={})
    db.add(event)
    await db.commit()
    event_id = str(event.id)
    frame = {
        "id": event_id,
        "type": "MONITOR_DOWN",
        "message": "probe down",
        "data": {},
    }

    first = await dispatch_event_frame(frame)
    second = await dispatch_event_frame(frame)  # the second worker's copy
    assert first == 1
    assert second == 0

    rows = await db.execute(
        select(NotificationDelivery).where(
            NotificationDelivery.channel_id == uuid.UUID(channel["id"]),
            NotificationDelivery.event_id == uuid.UUID(event_id),
        )
    )
    assert len(rows.scalars().all()) == 1
    # And the channel table is untouched by the dedup path.
    channels = (await db.execute(select(NotificationChannel))).scalars().all()
    assert any(c.id == uuid.UUID(channel["id"]) for c in channels)
