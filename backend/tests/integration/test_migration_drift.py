"""Model / migration drift: the schema in the database must match the models.

Before this test, a model change without a migration was only caught late — when
a *different* integration test happened to run ``alembic upgrade head`` against a
fresh database and then failed for an unrelated-looking reason. This makes the
comparison explicit and local: Alembic's own autogenerate diff between the
migrated database and ``Base.metadata`` must be empty.

The comparison runs as the **owner** role. That is deliberate: reflection needs
to see every table, and the point here is the shape of the schema, not tenant
isolation (the RLS-enforced role could not even describe another schema's tables).
"""

from __future__ import annotations

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from app.models import Base
from sqlalchemy import create_engine, text

from tests.conftest import TEST_OWNER_DATABASE_URL

pytestmark = pytest.mark.integration


def test_models_and_migrations_do_not_drift() -> None:
    """``Base.metadata`` and the migrated database must describe the same schema."""
    engine = create_engine(TEST_OWNER_DATABASE_URL)
    try:
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            diff = compare_metadata(context, Base.metadata)
    finally:
        engine.dispose()

    assert diff == [], (
        "models and migrations have drifted; run `make makemigrations m=...`:\n"
        + "\n".join(f"  - {entry}" for entry in diff)
    )


def test_operations_type_check_matches_the_enum() -> None:
    """The DB whitelist and ``OperationType`` are the same closed set.

    The migration spells the set as a literal on purpose (a new type is a new
    migration). This asserts the two never disagree: an enum member the CHECK
    rejects would be a runtime 500, and a value the CHECK accepts that the app
    does not know is an exec surface nobody reviewed.
    """
    from app.models.enums import OperationType

    engine = create_engine(TEST_OWNER_DATABASE_URL)
    try:
        with engine.connect() as conn:
            definition = conn.execute(
                text(
                    "SELECT pg_get_constraintdef(oid) FROM pg_constraint "
                    "WHERE conname = 'ck_operations_type_valid'"
                )
            ).scalar_one()
    finally:
        engine.dispose()

    for op_type in OperationType:
        assert f"'{op_type}'" in definition, f"{op_type} missing from the DB whitelist"

    # Reserved Phase 2 types must not be accepted by the database either.
    for reserved in ("nginx.reload", "certificate.install", "secret.env.apply"):
        assert reserved not in definition


def test_the_certificate_vocabularies_match_the_enums() -> None:
    """The certificate closed vocabularies are the sets the code declares.

    ``certificate_generations.state`` is the important one. Phase 5.1 spelled it
    as a literal *without* the post-issuance states, so the database refused a
    generation that would have to carry a private key; Phase 5.2.2 widens it to
    the full machine **and** adds the material guard, so the property that bought —
    no material-bearing row without material — is now a constraint instead of a
    missing column. Both halves are asserted here: an enum member the CHECK rejects
    would be a runtime 500, and a value the CHECK accepts that the enum does not
    know would be a state with no rules at all.
    """
    from app.models.enums import (
        CertificateChallengeType,
        CertificateGenerationState,
        CertificateKeyAlgorithm,
        CertificateRevocationState,
        CertificateStatus,
        DnsProviderKind,
    )

    names = {
        "status": "ck_certificates_status_valid",
        "challenge_type": "ck_certificates_challenge_type_valid",
        "key_algorithm": "ck_certificates_key_algorithm_valid",
        "state": "ck_certificate_generations_state_valid",
        "revocation_state": "ck_certificate_generations_revocation_state_valid",
        "material_guard": "ck_certificate_generations_material_guard",
        "dns_provider_kind": "ck_dns_providers_kind_valid",
    }
    engine = create_engine(TEST_OWNER_DATABASE_URL)
    try:
        with engine.connect() as conn:
            definitions = {
                key: conn.execute(
                    text(
                        "SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conname = :name"
                    ),
                    {"name": constraint},
                ).scalar_one()
                for key, constraint in names.items()
            }
    finally:
        engine.dispose()

    for member in CertificateStatus:
        assert f"'{member}'" in definitions["status"], member
    for member in CertificateGenerationState:
        assert f"'{member}'" in definitions["state"], member
    for member in CertificateChallengeType:
        assert f"'{member}'" in definitions["challenge_type"], member
    for member in CertificateKeyAlgorithm:
        assert f"'{member}'" in definitions["key_algorithm"], member
    for member in CertificateRevocationState:
        assert f"'{member}'" in definitions["revocation_state"], member
    for member in DnsProviderKind:
        assert f"'{member}'" in definitions["dns_provider_kind"], member

    # The material guard is the acceptance criterion of 5.2.2 in the schema: the
    # two branches are the pre-issuance states and the six fields every
    # material-bearing row must carry. A guard that lost one of them would admit
    # exactly the row the slice exists to make impossible.
    guard = definitions["material_guard"]
    pre_issuance = set(CertificateGenerationState.live_pre_issuance()) | {
        CertificateGenerationState.FAILED
    }
    material_bearing = set(CertificateGenerationState.material_bearing())
    assert pre_issuance | material_bearing == set(CertificateGenerationState)
    for state in sorted(pre_issuance, key=str):
        assert f"'{state}'" in guard, state
    for state in sorted(material_bearing, key=str):
        assert f"'{state}'" not in guard, (
            f"{state} is material-bearing and must not appear in the guard's no-material branch"
        )
    for column in (
        "key_ciphertext",
        "chain_ciphertext",
        "deke_id",
        "issued_at",
        "not_before",
        "not_after",
    ):
        assert column in guard, column
