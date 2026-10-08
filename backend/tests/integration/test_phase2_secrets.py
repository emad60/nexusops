"""Phase 2 secrets: layered scope, immutable versions, rollback, isolation.

Two things are under test that did not exist before this phase:

* **Scope precedence** — organization < project < environment, most specific
  wins, resolved inside the active tenant only.
* **Append-only versions** — rotation and rollback add rows; nothing overwrites
  or deletes a version, and no endpoint ever returns a value.
"""

from __future__ import annotations

import asyncio
import uuid

import pytest
from app.models import DeploymentEnvironment, Secret, SecretVersion
from app.services import secret_service
from sqlalchemy import select

from .helpers import API

pytestmark = pytest.mark.integration

VALUE_ORG = "org-level-secret-abc"
VALUE_PROJECT = "project-level-secret-def"
VALUE_ENV = "environment-level-secret-ghi"


async def _project(client, owner, name: str, config: dict | None = None) -> dict:
    body: dict = {"name": name}
    if config is not None:
        body["config"] = config
    response = await client.post(f"{API}/projects", headers=owner["headers"], json=body)
    assert response.status_code == 201, response.text
    return response.json()


async def _env(client, owner, project_id: str, name: str, config: dict | None = None) -> dict:
    response = await client.post(
        f"{API}/projects/{project_id}/environments",
        headers=owner["headers"],
        json={"name": name, "config": config or {}},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _secret(client, owner, key: str, value: str, **scope) -> dict:
    response = await client.post(
        f"{API}/secrets",
        headers=owner["headers"],
        json={"key": key, "value": value, **scope},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def _resolved(org_db, environment_id: str) -> dict[str, str]:
    env_row = await org_db.get(DeploymentEnvironment, uuid.UUID(environment_id))
    return (await secret_service.resolve_secrets_for_environment(org_db, env_row)).values


async def test_scope_precedence_environment_over_project_over_org(client, owner, org_db):
    """The documented example: same key at three scopes; most specific wins."""
    # Organization-wide fallback (no project, no environment).
    await _secret(client, owner, "API_URL", VALUE_ORG)

    project_p = await _project(client, owner, "Precedence P")
    project_q = await _project(client, owner, "Precedence Q")
    # Project scope.
    await _secret(client, owner, "API_URL", VALUE_PROJECT, project_id=project_p["id"])

    env_prod = await _env(
        client, owner, project_p["id"], "Production", {"API_URL": "${secret:API_URL}"}
    )
    env_staging = await _env(
        client, owner, project_p["id"], "Staging", {"API_URL": "${secret:API_URL}"}
    )
    env_other = await _env(
        client, owner, project_q["id"], "Production", {"API_URL": "${secret:API_URL}"}
    )
    # Environment scope on Production only.
    await _secret(
        client,
        owner,
        "API_URL",
        VALUE_ENV,
        project_id=project_p["id"],
        environment_id=env_prod["id"],
    )

    assert await _resolved(org_db, env_prod["id"]) == {"API_URL": VALUE_ENV}
    assert await _resolved(org_db, env_staging["id"]) == {"API_URL": VALUE_PROJECT}
    assert await _resolved(org_db, env_other["id"]) == {"API_URL": VALUE_ORG}


async def test_reference_named_only_in_project_config_is_resolved(client, owner, org_db):
    """A ref declared in the project base config resolves for its environments."""
    await _secret(client, owner, "SHARED_TOKEN", "shared-value-1")
    project = await _project(
        client, owner, "Project Ref", {"SHARED_TOKEN": "${secret:SHARED_TOKEN}"}
    )
    environment = await _env(client, owner, project["id"], "Production", {"APP_ENV": "prod"})

    assert await _resolved(org_db, environment["id"]) == {"SHARED_TOKEN": "shared-value-1"}


async def test_environment_secret_scope_requires_matching_project(client, owner):
    project_a = await _project(client, owner, "Scope A")
    project_b = await _project(client, owner, "Scope B")
    environment = await _env(client, owner, project_a["id"], "Production")

    mismatch = await client.post(
        f"{API}/secrets",
        headers=owner["headers"],
        json={
            "key": "MISMATCHED",
            "value": "x",
            "project_id": project_b["id"],
            "environment_id": environment["id"],
        },
    )
    assert mismatch.status_code == 404, mismatch.text


async def test_create_writes_version_one(client, owner, org_db):
    created = await _secret(client, owner, "V1_KEY", "v1-value")
    assert created["version"] == 1

    versions = await client.get(f"{API}/secrets/{created['id']}/versions", headers=owner["headers"])
    assert versions.status_code == 200
    body = versions.json()
    assert [item["version"] for item in body] == [1]
    assert "ciphertext" not in body[0]
    assert "value" not in str(body)

    row = (
        await org_db.execute(
            select(SecretVersion).where(SecretVersion.secret_id == uuid.UUID(created["id"]))
        )
    ).scalar_one()
    assert row.version == 1


async def test_rotation_appends_and_preserves_history(client, owner, org_db):
    created = await _secret(client, owner, "ROTATE_KEY", "original")
    rotated = await client.post(
        f"{API}/secrets/{created['id']}/rotate",
        headers=owner["headers"],
        json={"value": "replacement"},
    )
    assert rotated.status_code == 200, rotated.text
    assert rotated.json()["version"] == 2

    # History keeps the original ciphertext untouched.
    rows = (
        (
            await org_db.execute(
                select(SecretVersion)
                .where(SecretVersion.secret_id == uuid.UUID(created["id"]))
                .order_by(SecretVersion.version)
            )
        )
        .scalars()
        .all()
    )
    assert [row.version for row in rows] == [1, 2]
    from app.core.security import decrypt_str

    assert decrypt_str(rows[0].ciphertext) == "original"
    assert decrypt_str(rows[1].ciphertext) == "replacement"


async def test_rollback_is_non_destructive(client, owner):
    created = await _secret(client, owner, "ROLLBACK_KEY", "v1-value")
    secret_id = created["id"]
    await client.post(
        f"{API}/secrets/{secret_id}/rotate", headers=owner["headers"], json={"value": "v2-value"}
    )

    rolled = await client.post(
        f"{API}/secrets/{secret_id}/rollback",
        headers=owner["headers"],
        json={"version": 1},
    )
    assert rolled.status_code == 200, rolled.text
    # Rollback appends a NEW version (3) carrying v1's value; version 2 stays.
    assert rolled.json()["version"] == 3

    versions = (
        await client.get(f"{API}/secrets/{secret_id}/versions", headers=owner["headers"])
    ).json()
    assert sorted(item["version"] for item in versions) == [1, 2, 3]


async def test_rollback_to_current_version_is_refused(client, owner):
    created = await _secret(client, owner, "CURRENT_KEY", "only")
    response = await client.post(
        f"{API}/secrets/{created['id']}/rollback",
        headers=owner["headers"],
        json={"version": 1},
    )
    assert response.status_code == 409, response.text


async def test_rollback_of_unknown_version_is_not_found(client, owner):
    created = await _secret(client, owner, "NOVERSION_KEY", "only")
    response = await client.post(
        f"{API}/secrets/{created['id']}/rollback",
        headers=owner["headers"],
        json={"version": 99},
    )
    assert response.status_code == 404, response.text


async def test_concurrent_rotations_are_serialized(client, owner, org_db):
    """Two racing rotations must both be kept and never share a version number."""
    created = await _secret(client, owner, "RACE_KEY", "start")
    secret_id = created["id"]

    first, second = await asyncio.gather(
        client.post(
            f"{API}/secrets/{secret_id}/rotate", headers=owner["headers"], json={"value": "race-a"}
        ),
        client.post(
            f"{API}/secrets/{secret_id}/rotate", headers=owner["headers"], json={"value": "race-b"}
        ),
    )
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text
    assert {first.json()["version"], second.json()["version"]} == {2, 3}

    rows = (
        (
            await org_db.execute(
                select(SecretVersion).where(SecretVersion.secret_id == uuid.UUID(secret_id))
            )
        )
        .scalars()
        .all()
    )
    versions = sorted(row.version for row in rows)
    assert versions == [1, 2, 3]  # both values preserved, no duplicate version

    parent = (
        await org_db.execute(select(Secret).where(Secret.id == uuid.UUID(secret_id)))
    ).scalar_one()
    assert parent.version == 3
    # Exactly one current version.
    assert sum(1 for row in rows if row.version == parent.version) == 1


async def test_secret_plaintext_never_appears_in_any_response(client, owner):
    marker = "S3cr3t-Never-Leak-" + uuid.uuid4().hex
    created = await _secret(client, owner, "LEAK_KEY", marker)
    project = await _project(client, owner, "Leak Co", {"URL": "${secret:LEAK_KEY}"})
    environment = await _env(
        client, owner, project["id"], "Production", {"K": "${secret:LEAK_KEY}"}
    )

    responses = [
        await client.get(f"{API}/secrets", headers=owner["headers"]),
        await client.get(f"{API}/secrets/{created['id']}", headers=owner["headers"]),
        await client.get(f"{API}/secrets/{created['id']}/versions", headers=owner["headers"]),
        await client.get(f"{API}/projects/{project['id']}", headers=owner["headers"]),
        await client.get(
            f"{API}/projects/{project['id']}/environments/{environment['id']}",
            headers=owner["headers"],
        ),
    ]
    for response in responses:
        assert response.status_code == 200, response.text
        assert marker not in response.text, f"plaintext leaked through {response.request.url}"


async def test_secret_isolation_across_organizations(client, owner, second_org):
    """Another tenant cannot read, rotate, roll back or even enumerate the secret."""
    project = await _project(client, owner, "Isolation Co")
    environment = await _env(client, owner, project["id"], "Production")
    secret = await _secret(
        client,
        owner,
        "ISOLATED",
        "tenant-a-only",
        project_id=project["id"],
        environment_id=environment["id"],
    )
    sid = secret["id"]

    assert (
        await client.get(f"{API}/secrets/{sid}", headers=second_org["headers"])
    ).status_code == 404
    assert (
        await client.get(f"{API}/secrets/{sid}/versions", headers=second_org["headers"])
    ).status_code == 404
    assert (
        await client.post(
            f"{API}/secrets/{sid}/rotate", headers=second_org["headers"], json={"value": "x"}
        )
    ).status_code == 404
    assert (
        await client.post(
            f"{API}/secrets/{sid}/rollback", headers=second_org["headers"], json={"version": 1}
        )
    ).status_code == 404
    assert (
        await client.delete(f"{API}/secrets/{sid}", headers=second_org["headers"])
    ).status_code == 404

    listed = await client.get(f"{API}/secrets", headers=second_org["headers"])
    assert listed.status_code == 200
    assert sid not in {item["id"] for item in listed.json()["items"]}


async def test_secret_lifecycle_is_audited(client, owner, org_db):
    from app.models import AuditLog

    created = await _secret(client, owner, "AUDIT_KEY", "one")
    sid = created["id"]
    await client.post(
        f"{API}/secrets/{sid}/rotate", headers=owner["headers"], json={"value": "two"}
    )
    await client.post(
        f"{API}/secrets/{sid}/rollback", headers=owner["headers"], json={"version": 1}
    )

    # ``audit_logs.resource_id`` is stored as text.
    rows = (
        (await org_db.execute(select(AuditLog.action).where(AuditLog.resource_id == sid)))
        .scalars()
        .all()
    )
    assert {"secret.create", "secret.rotate", "secret.rollback"} <= set(rows)
