"""Deployment engine over the simulated runner: success, failure, rollback."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from app.api.deps import AuthContext
from app.models import Deployment, DeploymentStep, LogEntry, User
from app.services.deployment_engine import (
    execute_deployment,
    queue_deployment,
    rollback_deployment,
)
from sqlalchemy import select

from .helpers import API

pytestmark = pytest.mark.integration


async def _owner_ctx(db, owner) -> AuthContext:
    """Same AuthContext the HTTP route would resolve for this owner."""
    user = (
        await db.execute(select(User).where(User.email == owner["credentials"]["email"]))
    ).scalar_one()
    return AuthContext(user=user)


async def _delivery_chain(client, owner) -> tuple[dict, dict]:
    """Project -> application -> environment bound to a fresh server."""
    project = (
        await client.post(f"{API}/projects", headers=owner["headers"], json={"name": "Delivery Co"})
    ).json()
    application = (
        await client.post(
            f"{API}/projects/{project['id']}/applications",
            headers=owner["headers"],
            json={"name": "platform-api"},
        )
    ).json()
    server = (
        await client.post(
            f"{API}/servers",
            headers=owner["headers"],
            json={
                "name": "deploy-target",
                "hostname": "deploy-target.integration.test",
            },
        )
    ).json()
    environment = (
        await client.post(
            f"{API}/projects/applications/{application['id']}/environments",
            headers=owner["headers"],
            json={"name": "production", "server_id": server["id"]},
        )
    ).json()
    return {"project": project, "application": application}, environment


async def _queue(db, owner_ctx, application: dict, environment: dict, version: str):
    from app.services.project_service import get_application, get_environment

    app_row = await get_application(db, uuid.UUID(application["id"]))
    env_row = await get_environment(db, uuid.UUID(environment["id"]))
    return await queue_deployment(
        db,
        ctx=owner_ctx,
        application=app_row,
        environment=env_row,
        version=version,
        notes="integration run",
    )


async def test_trigger_via_http_returns_fully_serialized_deployment(client, owner, db):
    """Regression: the trigger route must re-read the queued row eagerly.

    ``queue_deployment`` leaves ``steps``/``application``/``environment``
    unloaded on the freshly flushed object (they were set by id); serializing
    it directly lazy-loads on the AsyncSession and 500s with MissingGreenlet.
    """
    delivery, environment = await _delivery_chain(client, owner)

    resp = await client.post(
        # The trigger alias nests under the deployments router, matching the
        # frontend's call path: /api/v1/deployments/applications/{id}/deployments.
        f"{API}/deployments/applications/{delivery['application']['id']}/deployments",
        headers=owner["headers"],
        json={"environment_id": environment["id"], "version": "9.9.9-regression"},
    )
    assert resp.status_code == 202, resp.text
    body = resp.json()
    assert body["version"] == "9.9.9-regression"
    assert body["status"] == "QUEUED"
    assert body["application"]["name"] == "platform-api"
    assert body["environment"]["name"] == "production"
    assert body["steps_total"] == 7
    assert [step["idx"] for step in body["steps"]] == list(range(7))


async def test_successful_deployment_writes_steps_and_logs(client, owner, db):
    delivery, environment = await _delivery_chain(client, owner)

    queued = await _queue(
        db, await _owner_ctx(db, owner), delivery["application"], environment, "2.7.0"
    )
    queued_id = queued.id  # capture before expire_all: expired-attribute access
    await db.commit()  # from sync code would attempt a lazy refresh
    assert queued.status == "QUEUED"

    await execute_deployment(queued_id)
    db.expire_all()

    final = await db.get(Deployment, queued_id)
    assert final.status == "SUCCESS"
    assert final.finished_at is not None
    assert final.duration_ms is not None

    steps = (
        (
            await db.execute(
                select(DeploymentStep)
                .where(DeploymentStep.deployment_id == queued_id)
                .order_by(DeploymentStep.idx)
            )
        )
        .scalars()
        .all()
    )
    assert [s.name for s in steps] == [
        "PULL_REPO",
        "CHECKOUT",
        "BUILD_IMAGE",
        "STOP_OLD_CONTAINER",
        "START_NEW_CONTAINER",
        "HEALTH_CHECK",
        "FINALIZE",
    ]
    assert all(s.status == "SUCCESS" for s in steps)

    logs = (
        (await db.execute(select(LogEntry).where(LogEntry.deployment_id == queued_id)))
        .scalars()
        .all()
    )
    assert len(logs) >= 5


async def test_broken_version_fails_at_health_check(client, owner, db):
    delivery, environment = await _delivery_chain(client, owner)

    queued = await _queue(
        db, await _owner_ctx(db, owner), delivery["application"], environment, "2.8.0-broken"
    )
    queued_id = queued.id  # capture before expire_all
    await db.commit()

    await execute_deployment(queued_id)
    db.expire_all()

    final = await db.get(Deployment, queued_id)
    assert final.status == "FAILED"
    assert "HEALTH_CHECK" in (final.failure_reason or "")

    steps = (
        (
            await db.execute(
                select(DeploymentStep)
                .where(DeploymentStep.deployment_id == queued_id)
                .order_by(DeploymentStep.idx)
            )
        )
        .scalars()
        .all()
    )
    by_name = {s.name: s for s in steps}
    assert by_name["HEALTH_CHECK"].status == "FAILED"
    assert by_name["FINALIZE"].status == "SKIPPED"


async def test_rollback_redeploys_last_good_version(client, owner, db):
    delivery, environment = await _delivery_chain(client, owner)

    good = await _queue(
        db, await _owner_ctx(db, owner), delivery["application"], environment, "3.0.0"
    )
    good_id = good.id  # capture before expire_all
    await db.commit()
    await execute_deployment(good_id)

    broken = await _queue(
        db, await _owner_ctx(db, owner), delivery["application"], environment, "3.1.0-broken"
    )
    broken_id = broken.id  # capture before expire_all
    await db.commit()
    await execute_deployment(broken_id)
    db.expire_all()

    assert (await db.get(Deployment, good_id)).status == "SUCCESS"
    assert (await db.get(Deployment, broken_id)).status == "FAILED"

    rolled = await rollback_deployment(db, await _owner_ctx(db, owner), broken_id)
    rolled_id = rolled.id  # capture before expire_all
    await db.commit()
    assert rolled.is_rollback is True
    assert rolled.version == "3.0.0"

    await execute_deployment(rolled_id)
    db.expire_all()
    assert (await db.get(Deployment, rolled_id)).status == "SUCCESS"


async def _queued_with_recorder(db, monkeypatch, owner, application: dict, environment: dict):
    """queue_deployment with the Celery handoff recorded instead of dispatched."""
    from app.services import deployment_engine
    from app.services.project_service import get_application, get_environment

    calls: list[uuid.UUID] = []

    async def record(deployment_id: uuid.UUID) -> None:
        calls.append(deployment_id)

    monkeypatch.setattr(deployment_engine, "_enqueue_task", record)
    app_row = await get_application(db, uuid.UUID(application["id"]))
    env_row = await get_environment(db, uuid.UUID(environment["id"]))
    queued = await queue_deployment(
        db,
        ctx=await _owner_ctx(db, owner),
        application=app_row,
        environment=env_row,
        version="0.0.0-defer",
    )
    return queued, calls


async def test_enqueue_happens_only_after_commit(client, owner, db, monkeypatch):
    """Regression: the Celery handoff must not race the API's commit.

    The worker's claim query filters on ``status == QUEUED``; when the task
    was enqueued inline (pre-commit) the worker sometimes read before the
    route's transaction committed, no-op'd, and left the deployment QUEUED
    until the 5-minute sweep. The handoff is now deferred to after-commit.
    """
    delivery, environment = await _delivery_chain(client, owner)
    queued, calls = await _queued_with_recorder(
        db, monkeypatch, owner, delivery["application"], environment
    )

    assert calls == [], "enqueue must not fire before the session commits"

    await db.commit()
    await asyncio.sleep(0.05)  # let the after-commit task run
    assert calls == [queued.id], "exactly one enqueue after commit"


async def test_enqueue_dropped_on_rollback(client, owner, db, monkeypatch):
    """A rolled-back queue_deployment must never hand a phantom id to Celery."""
    delivery, environment = await _delivery_chain(client, owner)
    _, calls = await _queued_with_recorder(
        db, monkeypatch, owner, delivery["application"], environment
    )

    await db.rollback()
    await asyncio.sleep(0.05)
    assert calls == [], "no enqueue for a rolled-back deployment"

    # A later unrelated commit on the same session must not resurrect it.
    await db.commit()
    await asyncio.sleep(0.05)
    assert calls == []
