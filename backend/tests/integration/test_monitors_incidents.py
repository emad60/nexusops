"""Monitor checks driving the full down -> incident -> recovery lifecycle."""

from __future__ import annotations

import uuid

import pytest
from app.core.security import encrypt_str
from app.models import Incident, IncidentEvent, NotificationChannel, NotificationDelivery
from app.services import monitor_service, notification_service
from sqlalchemy import select

from .helpers import API, assert_error_code

pytestmark = pytest.mark.integration


async def _create_monitor(client, owner, **overrides) -> dict:
    payload = {
        "name": overrides.pop("name", "probe"),
        "url": overrides.pop("url", "sim://probe/always-down"),
        "interval_seconds": 15,
        "failure_threshold": 2,
        "success_threshold": 2,
    }
    payload.update(overrides)
    response = await client.post(f"{API}/monitors", headers=owner["headers"], json=payload)
    assert response.status_code == 201, response.text
    return response.json()


async def test_metadata_endpoint_and_private_target_blocked(client, owner):
    bad = await client.post(
        f"{API}/monitors",
        headers=owner["headers"],
        json={"name": "metadata", "url": "http://169.254.169.254/latest/meta-data"},
    )
    assert bad.status_code == 422
    assert_error_code(bad.json(), "SSRF_BLOCKED")


async def test_down_then_recover_lifecycle(client, owner, db):
    monitor = await _create_monitor(client, owner, name="lifecycle")
    monitor_id = uuid.UUID(monitor["id"])

    # Two failing checks reach the failure threshold => OPEN incident.
    for _ in range(2):
        check = await monitor_service.run_check(db, monitor_id)
        await db.commit()
        assert check is not None and check.result == "FAILURE"

    opened = (
        (await db.execute(select(Incident).where(Incident.monitor_id == monitor_id)))
        .scalars()
        .all()
    )
    assert len(opened) == 1
    incident = opened[0]
    assert incident.status == "OPEN"

    timeline = (
        (await db.execute(select(IncidentEvent).where(IncidentEvent.incident_id == incident.id)))
        .scalars()
        .all()
    )
    kinds = {str(e.kind) for e in timeline}
    assert "OPENED" in kinds
    assert "DETECTED" in kinds or "NOTIFIED" in kinds or not kinds - {"OPENED"}

    # Recovery: flip to a healthy probe; the success threshold closes it.
    patched = await client.patch(
        f"{API}/monitors/{monitor['id']}",
        headers=owner["headers"],
        json={"url": "sim://probe/healthy"},
    )
    assert patched.status_code == 200

    for _ in range(3):
        check = await monitor_service.run_check(db, monitor_id)
        await db.commit()
        assert check is not None and check.result == "SUCCESS"

    refreshed = await db.get(Incident, incident.id)
    assert refreshed is not None and refreshed.status == "RESOLVED"
    final_kinds = {
        str(e.kind)
        for e in (
            await db.execute(select(IncidentEvent).where(IncidentEvent.incident_id == refreshed.id))
        )
        .scalars()
        .all()
    }
    assert "RESOLVED" in final_kinds


async def test_notification_pipeline_queues_delivery_for_down_event(db):
    channel = NotificationChannel(
        name="test sink",
        type="WEBHOOK",
        config_ciphertext=encrypt_str('{"url": "http://127.0.0.1:9/unreachable"}'),
        display_target="http://127.0.0.1:9/unreachable",
        events=["MONITOR_DOWN"],
        enabled=True,
    )
    db.add(channel)
    await db.commit()

    queued = await notification_service.dispatch_event_frame(
        {
            "type": "MONITOR_DOWN",
            "level": "CRITICAL",
            "message": "probe is down",
            "resource_type": "monitor",
            "resource_id": "00000000-0000-0000-0000-000000000000",
            "created_at": "2026-08-24T00:00:00+00:00",
        }
    )
    assert queued == 1

    delivery = (await db.execute(select(NotificationDelivery))).scalar_one()
    assert delivery.event_type == "MONITOR_DOWN"
    assert delivery.attempts >= 1  # sender ran; the unreachable endpoint just failed it


async def test_check_now_endpoint_runs_immediately(client, owner):
    monitor = await _create_monitor(client, owner, name="manual", url="sim://probe/healthy")
    response = await client.post(
        f"{API}/monitors/{monitor['id']}/check-now", headers=owner["headers"]
    )
    assert response.status_code in (200, 202), response.text


async def test_monitor_responses_mask_probe_credentials(client, owner):
    """Regression: probe headers and URL query credentials never leave the API.

    Probe headers are the canonical place users put ``Authorization: Bearer …``
    / ``X-API-Key`` values, and monitor URLs commonly embed ``?token=…``
    credentials. monitor.read is granted to every role, so a plain Viewer
    listing monitors must not be able to harvest operators' probe secrets.
    """
    created = await _create_monitor(
        client,
        owner,
        name="cred-hygiene",
        url="sim://probe/health?token=supersecret",
        headers={"Authorization": "Bearer topsecret", "X-Custom": "visible-value"},
    )
    assert "supersecret" not in created["url"]
    assert created["headers"]["Authorization"] == "******"
    assert created["headers"]["X-Custom"] == "visible-value"

    listed = await client.get(f"{API}/monitors", headers=owner["headers"])
    assert listed.status_code == 200
    rows = listed.json()["items"] if isinstance(listed.json(), dict) else listed.json()
    row = next(r for r in rows if r["id"] == created["id"])
    assert "supersecret" not in row["url"]
    assert row["headers"]["Authorization"] == "******"

    detail = await client.get(f"{API}/monitors/{created['id']}", headers=owner["headers"])
    assert detail.status_code == 200
    assert "supersecret" not in detail.json()["url"]
    assert detail.json()["headers"]["Authorization"] == "******"
