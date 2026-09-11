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


async def test_rotate_bumps_version_changes_digest_and_ciphertext(client, owner, db):
    created = await _create(client, owner)

    rotated = await client.post(
        f"{API}/secrets/{created['id']}/rotate",
        headers=owner["headers"],
        json={"value": "second-passphrase"},
    )
    assert rotated.status_code == 200, rotated.text
    assert rotated.json()["version"] == 2
    assert rotated.json()["digest"] != created["digest"]

    row = (await db.execute(select(Secret).where(Secret.key == "TEST_KEY"))).scalar_one()
    assert decrypt_str(row.ciphertext) == "second-passphrase"


async def test_delete_removes_metadata_row(client, owner, db):
    created = await _create(client, owner, key="DOOMED_KEY")
    response = await client.delete(f"{API}/secrets/{created['id']}", headers=owner["headers"])
    assert response.status_code in (200, 204)
    remaining = (
        await db.execute(select(Secret).where(Secret.key == "DOOMED_KEY"))
    ).scalar_one_or_none()
    assert remaining is None


async def test_environment_resolution_substitutes_secret_refs(client, owner, db):
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
    environment = (
        await client.post(
            f"{API}/projects/applications/{application['id']}/environments",
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

    # A global (project_id IS NULL) secret satisfies the reference.
    row = Secret(
        key="RESOLVE_DB_URL",
        ciphertext=encrypt_str("postgresql://resolved:user@db/x"),
        version=1,
        digest="digest-1",
        description="resolution test",
    )
    db.add(row)
    await db.commit()

    env_row = await db.get(DeploymentEnvironment, uuid.UUID(environment["id"]))
    resolved = await secret_service.resolve_secrets_for_environment(db, env_row)
    # Contract: the resolver returns {referenced_secret_key: plaintext} — the
    # deployment engine substitutes these into the environment's config.
    assert resolved == {"RESOLVE_DB_URL": "postgresql://resolved:user@db/x"}
