"""Phase 2: project-scoped environments, config layering, and their isolation.

The central phase claim is that an Environment belongs to a **Project**, not to
an application. These tests exercise that from the outside: the routes, the
uniqueness rule, the layered config, and the IDOR boundary (a known environment
UUID buys nothing across projects or tenants).
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import select

from .helpers import API

pytestmark = pytest.mark.integration


async def _project(client, owner, name: str = "Ymart") -> dict:
    response = await client.post(f"{API}/projects", headers=owner["headers"], json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()


async def _environment(client, owner, project_id: str, **payload) -> dict:
    body = {"name": "production", **payload}
    response = await client.post(
        f"{API}/projects/{project_id}/environments", headers=owner["headers"], json=body
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_environment_belongs_to_the_project_not_an_application(client, owner):
    project = await _project(client, owner)
    environment = await _environment(client, owner, project["id"], name="Production")

    assert environment["project_id"] == project["id"]
    # There is no application_id on an environment any more — that was the
    # application-scoped model Phase 2 removed.
    assert "application_id" not in environment
    assert environment["slug"] == "production"
    assert environment["environment_type"] == "DEV"  # documented default


async def test_project_detail_lists_its_environments(client, owner):
    project = await _project(client, owner)
    await _environment(client, owner, project["id"], name="Development", environment_type="dev")
    await _environment(client, owner, project["id"], name="Production", environment_type="prod")

    detail = await client.get(f"{API}/projects/{project['id']}", headers=owner["headers"])
    assert detail.status_code == 200, detail.text
    names = [env["name"] for env in detail.json()["environments"]]
    assert names == ["Development", "Production"]
    types = {env["name"]: env["environment_type"] for env in detail.json()["environments"]}
    assert types == {"Development": "DEV", "Production": "PROD"}


@pytest.mark.parametrize(
    ("sent", "stored"),
    [
        ("dev", "DEV"),
        ("development", "DEV"),
        ("DEV", "DEV"),
        ("staging", "STAGING"),
        ("Staging", "STAGING"),
        ("prod", "PROD"),
        ("production", "PROD"),
        ("PRODUCTION", "PROD"),
    ],
)
async def test_environment_type_accepts_case_insensitive_forms(client, owner, sent, stored):
    project = await _project(client, owner, name=f"Types {sent}")
    environment = await _environment(
        client,
        owner,
        project["id"],
        name=f"Env {sent} {uuid.uuid4().hex[:6]}",
        environment_type=sent,
    )
    assert environment["environment_type"] == stored


async def test_environment_type_rejects_unknown_values(client, owner):
    project = await _project(client, owner, name="Bad Type")
    response = await client.post(
        f"{API}/projects/{project['id']}/environments",
        headers=owner["headers"],
        json={"name": "qa", "environment_type": "preprod"},
    )
    assert response.status_code == 422, response.text


async def test_environment_crud_roundtrip(client, owner):
    project = await _project(client, owner)
    created = await _environment(
        client,
        owner,
        project["id"],
        name="Staging",
        environment_type="staging",
        config={"LOG_LEVEL": "info"},
    )

    listed = await client.get(
        f"{API}/projects/{project['id']}/environments", headers=owner["headers"]
    )
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["items"]] == [created["id"]]

    fetched = await client.get(
        f"{API}/projects/{project['id']}/environments/{created['id']}",
        headers=owner["headers"],
    )
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Staging"

    updated = await client.patch(
        f"{API}/projects/{project['id']}/environments/{created['id']}",
        headers=owner["headers"],
        json={"name": "Staging EU", "environment_type": "prod"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "Staging EU"
    assert updated.json()["slug"] == "staging-eu"  # slug follows the name
    assert updated.json()["environment_type"] == "PROD"

    deleted = await client.delete(
        f"{API}/projects/{project['id']}/environments/{created['id']}",
        headers=owner["headers"],
    )
    assert deleted.status_code in (200, 204)
    gone = await client.get(
        f"{API}/projects/{project['id']}/environments/{created['id']}",
        headers=owner["headers"],
    )
    assert gone.status_code == 404


async def test_environment_name_is_unique_within_the_project(client, owner):
    project = await _project(client, owner)
    await _environment(client, owner, project["id"], name="Production")

    duplicate = await client.post(
        f"{API}/projects/{project['id']}/environments",
        headers=owner["headers"],
        json={"name": "Production"},
    )
    assert duplicate.status_code == 409, duplicate.text


async def test_same_environment_slug_is_allowed_in_two_projects(client, owner):
    """Uniqueness is ``(project_id, slug)`` — not instance-wide."""
    first = await _project(client, owner, name="Alpha")
    second = await _project(client, owner, name="Beta")
    a = await _environment(client, owner, first["id"], name="Production")
    b = await _environment(client, owner, second["id"], name="Production")
    assert a["slug"] == b["slug"] == "production"
    assert a["project_id"] != b["project_id"]


async def test_environment_detail_separates_the_config_layers(client, owner):
    project_resp = await client.post(
        f"{API}/projects",
        headers=owner["headers"],
        json={
            "name": "Layered",
            "config": {"LOG_LEVEL": "info", "REGION": "eu", "FEATURE_X": "false"},
        },
    )
    project = project_resp.json()
    assert project["config"] == {"LOG_LEVEL": "info", "REGION": "eu", "FEATURE_X": "false"}

    environment = await _environment(
        client,
        owner,
        project["id"],
        name="Production",
        config={"LOG_LEVEL": "debug", "FEATURE_X": "true", "DATABASE_URL": "${secret:DB_URL}"},
    )

    detail = await client.get(
        f"{API}/projects/{project['id']}/environments/{environment['id']}",
        headers=owner["headers"],
    )
    assert detail.status_code == 200, detail.text
    body = detail.json()

    # Project base and environment overrides are distinct views.
    assert body["project_config"]["LOG_LEVEL"] == "info"
    assert body["config"]["LOG_LEVEL"] == "debug"
    # Effective config is the shallow merge: overrides win, the rest inherits.
    assert body["effective_config"] == {
        "LOG_LEVEL": "debug",
        "REGION": "eu",
        "FEATURE_X": "true",
        "DATABASE_URL": "${secret:DB_URL}",
    }
    # Only key *names* are exposed; never a value.
    assert body["secret_references"] == ["DB_URL"]
    assert "${secret:DB_URL}" in str(body)


async def test_project_config_change_is_inherited_by_environments(client, owner):
    project = await _project(client, owner, name="Inherit Co")
    environment = await _environment(client, owner, project["id"], name="Staging", config={})

    path = f"{API}/projects/{project['id']}/environments/{environment['id']}"
    before = (await client.get(path, headers=owner["headers"])).json()
    assert before["effective_config"] == {}

    await client.patch(
        f"{API}/projects/{project['id']}",
        headers=owner["headers"],
        json={"config": {"REGION": "us"}},
    )
    after = (await client.get(path, headers=owner["headers"])).json()
    assert after["effective_config"] == {"REGION": "us"}


async def test_environment_patch_validates_config(client, owner):
    """The update path is validated too (the pre-Phase-2 gap)."""
    project = await _project(client, owner, name="Patch Validate")
    environment = await _environment(client, owner, project["id"], name="Production")

    bad = await client.patch(
        f"{API}/projects/{project['id']}/environments/{environment['id']}",
        headers=owner["headers"],
        json={"config": {"URL": "prefix-${secret:TOKEN}-suffix"}},
    )
    assert bad.status_code == 422, bad.text

    good = await client.patch(
        f"{API}/projects/{project['id']}/environments/{environment['id']}",
        headers=owner["headers"],
        json={"config": {"URL": "${secret:TOKEN}"}},
    )
    assert good.status_code == 200, good.text
    assert good.json()["config"] == {"URL": "${secret:TOKEN}"}


async def test_environment_idor_through_the_wrong_project(client, owner):
    """Knowing an environment UUID is not access: the project link must hold."""
    project_a = await _project(client, owner, name="IDOR A")
    project_b = await _project(client, owner, name="IDOR B")
    environment = await _environment(client, owner, project_a["id"], name="Production")

    for method in ("get", "delete"):
        response = await getattr(client, method)(
            f"{API}/projects/{project_b['id']}/environments/{environment['id']}",
            headers=owner["headers"],
        )
        assert response.status_code == 404, (method, response.text)

    patched = await client.patch(
        f"{API}/projects/{project_b['id']}/environments/{environment['id']}",
        headers=owner["headers"],
        json={"name": "Hijacked"},
    )
    assert patched.status_code == 404


async def test_environment_idor_across_organizations(client, owner, second_org):
    """Another tenant cannot reach the project, its environments, or its detail."""
    project = await _project(client, owner, name="Tenant A Only")
    environment = await _environment(client, owner, project["id"], name="Production")

    # Same user, different active organization.
    forbidden_list = await client.get(
        f"{API}/projects/{project['id']}/environments", headers=second_org["headers"]
    )
    assert forbidden_list.status_code == 404

    forbidden_detail = await client.get(
        f"{API}/projects/{project['id']}/environments/{environment['id']}",
        headers=second_org["headers"],
    )
    assert forbidden_detail.status_code == 404

    forbidden_create = await client.post(
        f"{API}/projects/{project['id']}/environments",
        headers=second_org["headers"],
        json={"name": "sneaky"},
    )
    assert forbidden_create.status_code == 404


async def test_environment_mutations_are_audited(client, owner, org_db):
    """Create, update and delete each write an audit row (Phase 2 exit criterion)."""
    from app.models import AuditLog

    project = await _project(client, owner, name="Audit Co")
    environment = await _environment(client, owner, project["id"], name="Production")
    await client.patch(
        f"{API}/projects/{project['id']}/environments/{environment['id']}",
        headers=owner["headers"],
        json={"auto_deploy": True},
    )
    await client.delete(
        f"{API}/projects/{project['id']}/environments/{environment['id']}",
        headers=owner["headers"],
    )

    # ``audit_logs.resource_id`` is stored as text, so compare as text.
    rows = (
        (
            await org_db.execute(
                select(AuditLog.action).where(AuditLog.resource_id == str(environment["id"]))
            )
        )
        .scalars()
        .all()
    )
    assert set(rows) == {"environment.create", "environment.update", "environment.delete"}
