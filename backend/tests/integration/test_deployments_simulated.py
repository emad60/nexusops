"""Deployment engine over the simulated runner: success, failure, rollback."""

from __future__ import annotations

import asyncio
import contextlib
import uuid

import pytest
from app.api.deps import AuthContext
from app.models import AuditLog, Deployment, DeploymentStep, LogEntry, User
from app.services.deployment_engine import (
    execute_deployment,
    queue_deployment,
    rollback_deployment,
)
from sqlalchemy import select

from .helpers import API

pytestmark = pytest.mark.integration


@contextlib.contextmanager
def _as_worker(owner):
    """Enter the organization scope the worker would be running in.

    The engine opens its own sessions, and a Celery task resolves the
    deployment's organization first (``tasks/_util.org_for``), then runs the
    whole deployment inside it. Tests that drive the engine directly have to do
    the same, or the guard refuses the writes the engine makes.
    """
    import uuid as _uuid

    from app.core.tenancy import org_scope

    with org_scope(_uuid.UUID(owner["active_organization_id"])):
        yield


async def _owner_ctx(org_db, owner) -> AuthContext:
    """Same AuthContext the HTTP route would resolve for this owner."""
    user = (
        await org_db.execute(select(User).where(User.email == owner["credentials"]["email"]))
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
            f"{API}/nodes",
            headers=owner["headers"],
            json={
                "name": "deploy-target",
                "hostname": "deploy-target.integration.test",
            },
        )
    ).json()
    # Phase 2: the environment is created on the project, not the application.
    environment = (
        await client.post(
            f"{API}/projects/{project['id']}/environments",
            headers=owner["headers"],
            json={
                "name": "production",
                "environment_type": "prod",
                "server_id": server["id"],
            },
        )
    ).json()
    return {"project": project, "application": application}, environment


async def _queue(org_db, owner_ctx, application: dict, environment: dict, version: str):
    from app.services.project_service import get_application, get_environment

    app_row = await get_application(org_db, uuid.UUID(application["id"]))
    env_row = await get_environment(org_db, uuid.UUID(environment["id"]))
    return await queue_deployment(
        org_db,
        ctx=owner_ctx,
        application=app_row,
        environment=env_row,
        version=version,
        notes="integration run",
    )


async def test_trigger_via_http_returns_fully_serialized_deployment(client, owner, org_db):
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
    # 7 runner steps plus the engine-owned RESOLVE_CONFIG step planned first.
    assert body["steps_total"] == 8
    assert [step["idx"] for step in body["steps"]] == list(range(8))
    assert body["steps"][0]["name"] == "RESOLVE_CONFIG"


async def test_successful_deployment_writes_steps_and_logs(client, owner, org_db):
    delivery, environment = await _delivery_chain(client, owner)

    with _as_worker(owner):
        queued = await _queue(
            org_db,
            await _owner_ctx(org_db, owner),
            delivery["application"],
            environment,
            "2.7.0",
        )
    queued_id = queued.id  # capture before expire_all: expired-attribute access
    await org_db.commit()  # from sync code would attempt a lazy refresh
    assert queued.status == "QUEUED"

    with _as_worker(owner):
        await execute_deployment(queued_id)
    org_db.expire_all()

    final = await org_db.get(Deployment, queued_id)
    assert final.status == "SUCCESS"
    assert final.finished_at is not None
    assert final.duration_ms is not None

    steps = (
        (
            await org_db.execute(
                select(DeploymentStep)
                .where(DeploymentStep.deployment_id == queued_id)
                .order_by(DeploymentStep.idx)
            )
        )
        .scalars()
        .all()
    )
    assert [s.name for s in steps] == [
        "RESOLVE_CONFIG",
        "PULL_REPO",
        "CHECKOUT",
        "BUILD_IMAGE",
        "STOP_OLD_CONTAINER",
        "START_NEW_CONTAINER",
        "HEALTH_CHECK",
        "FINALIZE",
    ]
    assert all(s.status == "SUCCESS" for s in steps)
    # The engine-owned step is visible like any other: it says what it resolved.
    assert "no ${secret:KEY} references" in (steps[0].output or "")

    logs = (
        (await org_db.execute(select(LogEntry).where(LogEntry.deployment_id == queued_id)))
        .scalars()
        .all()
    )
    assert len(logs) >= 5


async def test_broken_version_fails_at_health_check(client, owner, org_db):
    delivery, environment = await _delivery_chain(client, owner)

    with _as_worker(owner):
        queued = await _queue(
            org_db,
            await _owner_ctx(org_db, owner),
            delivery["application"],
            environment,
            "2.8.0-broken",
        )
    queued_id = queued.id  # capture before expire_all
    await org_db.commit()

    with _as_worker(owner):
        await execute_deployment(queued_id)
    org_db.expire_all()

    final = await org_db.get(Deployment, queued_id)
    assert final.status == "FAILED"
    assert "HEALTH_CHECK" in (final.failure_reason or "")

    steps = (
        (
            await org_db.execute(
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


async def test_rollback_redeploys_last_good_version(client, owner, org_db):
    delivery, environment = await _delivery_chain(client, owner)

    with _as_worker(owner):
        good = await _queue(
            org_db,
            await _owner_ctx(org_db, owner),
            delivery["application"],
            environment,
            "3.0.0",
        )
    good_id = good.id  # capture before expire_all
    await org_db.commit()
    with _as_worker(owner):
        await execute_deployment(good_id)

    with _as_worker(owner):
        broken = await _queue(
            org_db,
            await _owner_ctx(org_db, owner),
            delivery["application"],
            environment,
            "3.1.0-broken",
        )
    broken_id = broken.id  # capture before expire_all
    await org_db.commit()
    with _as_worker(owner):
        await execute_deployment(broken_id)
    org_db.expire_all()

    assert (await org_db.get(Deployment, good_id)).status == "SUCCESS"
    assert (await org_db.get(Deployment, broken_id)).status == "FAILED"

    with _as_worker(owner):
        rolled = await rollback_deployment(org_db, await _owner_ctx(org_db, owner), broken_id)
    rolled_id = rolled.id  # capture before expire_all
    await org_db.commit()
    assert rolled.is_rollback is True
    assert rolled.version == "3.0.0"

    with _as_worker(owner):
        await execute_deployment(rolled_id)
    org_db.expire_all()
    assert (await org_db.get(Deployment, rolled_id)).status == "SUCCESS"


async def _queued_with_recorder(org_db, monkeypatch, owner, application: dict, environment: dict):
    """queue_deployment with the Celery handoff recorded instead of dispatched."""
    from app.services import deployment_engine
    from app.services.project_service import get_application, get_environment

    calls: list[uuid.UUID] = []

    async def record(deployment_id: uuid.UUID) -> None:
        calls.append(deployment_id)

    monkeypatch.setattr(deployment_engine, "_enqueue_task", record)
    app_row = await get_application(org_db, uuid.UUID(application["id"]))
    env_row = await get_environment(org_db, uuid.UUID(environment["id"]))
    with _as_worker(owner):
        queued = await queue_deployment(
            org_db,
            ctx=await _owner_ctx(org_db, owner),
            application=app_row,
            environment=env_row,
            version="0.0.0-defer",
        )
    return queued, calls


async def _set_environment_config(org_db, environment: dict, config: dict) -> None:
    """Rewrite an environment's config the way the PATCH route would."""
    from app.services.project_service import get_environment

    env_row = await get_environment(org_db, uuid.UUID(environment["id"]))
    env_row.config = config
    await org_db.flush()
    await org_db.commit()


async def test_unresolvable_secret_fails_the_resolve_step(client, owner, org_db):
    """Fail-closed resolution, reported through the RESOLVE_CONFIG step.

    Regression: a ``${secret:KEY}`` reference with no Secret row resolved to
    ``""``, and an engine-level ``except Exception`` swallowed resolver errors
    into ``{}`` — so a deployment shipped without the credentials its config
    declared and reported SUCCESS.
    """
    delivery, environment = await _delivery_chain(client, owner)
    await _set_environment_config(org_db, environment, {"DATABASE_URL": "${secret:ABSENT_KEY}"})

    with _as_worker(owner):
        queued = await _queue(
            org_db,
            await _owner_ctx(org_db, owner),
            delivery["application"],
            environment,
            "4.0.0",
        )
    queued_id = queued.id  # capture before expire_all
    await org_db.commit()

    with _as_worker(owner):
        await execute_deployment(queued_id)
    org_db.expire_all()

    final = await org_db.get(Deployment, queued_id)
    assert final.status == "FAILED"
    assert "RESOLVE_CONFIG" in (final.failure_reason or "")
    assert "ABSENT_KEY" in (final.failure_reason or "")
    # The failure names the KEY (actionable) and never the reference syntax or a
    # value — nothing secret may reach a row the API serializes.
    assert "${secret:" not in (final.failure_reason or "")

    steps = (
        (
            await org_db.execute(
                select(DeploymentStep)
                .where(DeploymentStep.deployment_id == queued_id)
                .order_by(DeploymentStep.idx)
            )
        )
        .scalars()
        .all()
    )
    by_name = {s.name: s for s in steps}
    assert len(steps) == 8
    # The failure attributes to the resolve step; nothing downstream ran.
    assert by_name["RESOLVE_CONFIG"].status == "FAILED"
    assert "ABSENT_KEY" in (by_name["RESOLVE_CONFIG"].error or "")
    assert by_name["RESOLVE_CONFIG"].started_at is not None
    assert by_name["RESOLVE_CONFIG"].finished_at is not None
    assert by_name["PULL_REPO"].status == "SKIPPED"
    assert by_name["FINALIZE"].status == "SKIPPED"
    assert all(s.status == "SKIPPED" for name, s in by_name.items() if name != "RESOLVE_CONFIG"), (
        "no runner step may run or stay PENDING"
    )
    assert all(not s.output for name, s in by_name.items() if name != "RESOLVE_CONFIG")

    audit = (
        (await org_db.execute(select(AuditLog).where(AuditLog.action == "secret.resolve_failed")))
        .scalars()
        .all()
    )
    assert len(audit) == 1
    assert audit[0].result == "DENIED"
    assert audit[0].metadata_["missing"] == ["ABSENT_KEY"]
    assert audit[0].metadata_["deployment_id"] == str(queued_id)


async def test_resolved_secrets_are_audited_per_reference(client, owner, org_db):
    """A successful resolution is audited per secret: name + version, no value.

    Secret usage in a deploy used to be invisible to the audit trail.
    """
    created = await client.post(
        f"{API}/secrets",
        headers=owner["headers"],
        json={"key": "RESOLVE_ME", "value": "s3cr3t-value"},
    )
    assert created.status_code == 201, created.text

    delivery, environment = await _delivery_chain(client, owner)
    await _set_environment_config(org_db, environment, {"DATABASE_URL": "${secret:RESOLVE_ME}"})

    with _as_worker(owner):
        queued = await _queue(
            org_db,
            await _owner_ctx(org_db, owner),
            delivery["application"],
            environment,
            "5.0.0",
        )
    queued_id = queued.id  # capture before expire_all
    await org_db.commit()

    with _as_worker(owner):
        await execute_deployment(queued_id)
    org_db.expire_all()

    assert (await org_db.get(Deployment, queued_id)).status == "SUCCESS"

    rows = (
        (await org_db.execute(select(AuditLog).where(AuditLog.action == "secret.resolve")))
        .scalars()
        .all()
    )
    assert len(rows) == 1
    metadata = rows[0].metadata_
    assert metadata["key"] == "RESOLVE_ME"
    assert metadata["version"] == 1
    assert metadata["deployment_id"] == str(queued_id)
    assert "s3cr3t-value" not in str(metadata)


async def test_enqueue_happens_only_after_commit(client, owner, org_db, monkeypatch):
    """Regression: the Celery handoff must not race the API's commit.

    The worker's claim query filters on ``status == QUEUED``; when the task
    was enqueued inline (pre-commit) the worker sometimes read before the
    route's transaction committed, no-op'd, and left the deployment QUEUED
    until the 5-minute sweep. The handoff is now deferred to after-commit.
    """
    delivery, environment = await _delivery_chain(client, owner)
    queued, calls = await _queued_with_recorder(
        org_db, monkeypatch, owner, delivery["application"], environment
    )

    assert calls == [], "enqueue must not fire before the session commits"

    await org_db.commit()
    await asyncio.sleep(0.05)  # let the after-commit task run
    assert calls == [queued.id], "exactly one enqueue after commit"


async def test_enqueue_dropped_on_rollback(client, owner, org_db, monkeypatch):
    """A rolled-back queue_deployment must never hand a phantom id to Celery."""
    delivery, environment = await _delivery_chain(client, owner)
    _, calls = await _queued_with_recorder(
        org_db, monkeypatch, owner, delivery["application"], environment
    )

    await org_db.rollback()
    await asyncio.sleep(0.05)
    assert calls == [], "no enqueue for a rolled-back deployment"

    # A later unrelated commit on the same session must not resurrect it.
    await org_db.commit()
    await asyncio.sleep(0.05)
    assert calls == []
