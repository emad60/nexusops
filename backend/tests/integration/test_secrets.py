"""Secrets: metadata-only reads, rotation versioning, deploy-time resolution."""

from __future__ import annotations

import uuid

import pytest
from app.core.security import decrypt_str, encrypt_str
from app.models import DeploymentEnvironment, Secret
from app.services import secret_service
from sqlalchemy import select

from .helpers import API

pytestmark = pytest.mark.integration


async def _create(client, owner, key="TEST_KEY", value="first-passphrase") -> dict:
    response = await client.post(
        f"{API}/secrets",
        headers=owner["headers"],
        json={"key": key, "value": value, "description": "integration fixture"},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_create_and_list_return_metadata_only(client, owner):
    created = await _create(client, owner)

    assert created["key"] == "TEST_KEY"
    assert created["version"] == 1
    forbidden = {"value", "ciphertext", "plaintext", "encrypted_value"}
    assert not forbidden & set(created.keys())

    listed = await client.get(f"{API}/secrets", headers=owner["headers"])
    assert listed.status_code == 200
    page = listed.json()
    rows = page["items"] if isinstance(page, dict) else page
    assert len(rows) == 1
    assert not forbidden & set(rows[0].keys())


async def test_detail_endpoint_never_carries_the_value(client, owner):
    created = await _create(client, owner, key="DETAIL_KEY", value="swordfish-actual")
    detail = await client.get(f"{API}/secrets/{created['id']}", headers=owner["headers"])
    assert detail.status_code == 200
    body = detail.json()
    assert "swordfish-actual" not in str(body)


async def test_rotate_bumps_version_changes_digest_and_ciphertext(client, owner, org_db):
    created = await _create(client, owner)

    rotated = await client.post(
        f"{API}/secrets/{created['id']}/rotate",
        headers=owner["headers"],
        json={"value": "second-passphrase"},
    )
    assert rotated.status_code == 200, rotated.text
    assert rotated.json()["version"] == 2
    assert rotated.json()["digest"] != created["digest"]

    row = (await org_db.execute(select(Secret).where(Secret.key == "TEST_KEY"))).scalar_one()
    assert decrypt_str(row.ciphertext) == "second-passphrase"


async def test_delete_removes_metadata_row(client, owner, org_db):
    created = await _create(client, owner, key="DOOMED_KEY")
    response = await client.delete(f"{API}/secrets/{created['id']}", headers=owner["headers"])
    assert response.status_code in (200, 204)
    remaining = (
        await org_db.execute(select(Secret).where(Secret.key == "DOOMED_KEY"))
    ).scalar_one_or_none()
    assert remaining is None


async def test_environment_resolution_substitutes_secret_refs(client, owner, org_db):
    """${secret:KEY} placeholders resolve through decrypt at deploy time."""
    project = (
        await client.post(f"{API}/projects", headers=owner["headers"], json={"name": "Resolve Co"})
    ).json()
    application = (
        await client.post(
            f"{API}/projects/{project['id']}/applications",
            headers=owner["headers"],
            json={"name": "resolver-app"},
        )
    ).json()
    # Phase 2: environments live directly under the project.
    environment = (
        await client.post(
            f"{API}/projects/{project['id']}/environments",
            headers=owner["headers"],
            json={
                "name": "production",
                "config": {
                    "DATABASE_URL": "${secret:RESOLVE_DB_URL}",
                    "PLAIN": "untouched",
                },
            },
        )
    ).json()
    assert application["id"]  # application still exists; the env is project-scoped

    # A global (project_id IS NULL) secret satisfies the reference.
    row = Secret(
        key="RESOLVE_DB_URL",
        ciphertext=encrypt_str("postgresql://resolved:user@db/x"),
        version=1,
        digest="digest-1",
        description="resolution test",
    )
    org_db.add(row)
    await org_db.commit()

    env_row = await org_db.get(DeploymentEnvironment, uuid.UUID(environment["id"]))
    resolved = await secret_service.resolve_secrets_for_environment(org_db, env_row)
    # Contract: the resolver returns the referenced secrets' plaintext values —
    # the deployment engine substitutes these into the environment's config —
    # plus metadata (key name + version, never a value) for the resolution audit.
    assert resolved.values == {"RESOLVE_DB_URL": "postgresql://resolved:user@db/x"}
    assert [(ref.key, ref.version) for ref in resolved.references] == [("RESOLVE_DB_URL", 1)]


async def _environment_config(client, owner, config: dict) -> str:
    """Project → application → environment carrying *config*; returns its id."""
    project = (
        await client.post(f"{API}/projects", headers=owner["headers"], json={"name": "Fail Co"})
    ).json()
    application = (
        await client.post(
            f"{API}/projects/{project['id']}/applications",
            headers=owner["headers"],
            json={"name": "fail-closed-app"},
        )
    ).json()
    environment = (
        await client.post(
            f"{API}/projects/{project['id']}/environments",
            headers=owner["headers"],
            json={"name": "production", "config": config},
        )
    ).json()
    assert application["id"]
    return environment["id"]


async def test_missing_reference_fails_closed(client, owner, org_db):
    """A reference naming no secret must abort, not resolve to an empty value.

    Regression: resolution used to return ``""`` with a log warning, so a
    deployment shipped without the credentials its config declared.
    """
    env_id = await _environment_config(
        client, owner, {"DATABASE_URL": "${secret:ABSENT_KEY}", "PLAIN": "untouched"}
    )
    env_row = await org_db.get(DeploymentEnvironment, uuid.UUID(env_id))

    with pytest.raises(secret_service.SecretResolutionError) as excinfo:
        await secret_service.resolve_secrets_for_environment(org_db, env_row)

    error = excinfo.value
    assert error.missing == ("ABSENT_KEY",)
    assert error.undecryptable == ()
    # The message names the key so an operator can act, and carries no value.
    assert "ABSENT_KEY" in str(error)


async def test_undecryptable_reference_fails_closed(client, owner, org_db):
    """A row this ENCRYPTION_KEY cannot decrypt must abort, not yield ``""``."""
    env_id = await _environment_config(client, owner, {"TOKEN": "${secret:BROKEN_KEY}"})
    env_row = await org_db.get(DeploymentEnvironment, uuid.UUID(env_id))
    org_db.add(
        Secret(
            key="BROKEN_KEY",
            ciphertext="not-a-valid-fernet-token",
            version=3,
            digest="digest-broken",
            description="undecryptable by construction",
        )
    )
    await org_db.commit()

    with pytest.raises(secret_service.SecretResolutionError) as excinfo:
        await secret_service.resolve_secrets_for_environment(org_db, env_row)

    error = excinfo.value
    assert error.undecryptable == ("BROKEN_KEY",)
    assert error.missing == ()


async def test_no_references_returns_empty(client, owner, org_db):
    env_id = await _environment_config(client, owner, {"PLAIN": "untouched"})
    env_row = await org_db.get(DeploymentEnvironment, uuid.UUID(env_id))

    resolved = await secret_service.resolve_secrets_for_environment(org_db, env_row)

    assert resolved.values == {}
    assert resolved.references == ()
