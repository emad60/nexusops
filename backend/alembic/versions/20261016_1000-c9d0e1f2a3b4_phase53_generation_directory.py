"""Phase 5.3 — the issuance provenance pair on ``certificate_generations``.

Adds, from ``b8c9d0e1f2a3`` with a single head, one column and the two constraints
that make it meaningful:

* ``directory_url`` — which ACME directory this generation's order was created at,
  written when an attempt starts. The account table already records the URL of the
  account's directory (5.2.2); this is the *generation's* copy, and it is a copy on
  purpose: an account can be re-registered, and a certificate that was issued from
  staging must say so from its own row for as long as the row exists
  (phase5-design.md §5.4's "the generation records which directory issued it, the
  API exposes it").
* ``ck_certificate_generations_directory_known`` — ``directory_url`` is NULL or one
  of the vocabulary's URLs. The vocabulary is duplicated here as literals, exactly
  like the state and revocation vocabularies were: a CHECK cannot call Python, a new
  directory is a new migration, and ``test_migration_drift.py`` asserts the literals
  still equal :class:`~app.models.enums.AcmeDirectory`. A URL outside the set stays
  unrepresentable, so no hand-edited row can claim a CA this platform cannot reason
  about — in particular so nothing can label a staging certificate as production.
* ``ck_certificate_generations_directory_required`` — every state that outlives the
  order (the complement of ``PENDING``/``ORDERING``/``CHALLENGE_PUBLISHED``/
  ``VALIDATING``/``FAILED``) has one. That is the material guard's counterpart on the
  provenance axis, and it is a second constraint rather than an extension of the
  guard because the two failures mean different things: missing material is a partial
  write, a missing directory is a certificate nobody can classify as trustworthy.

Why this is *not* folded into the 5.2.2 guard: the guard is a shipped constraint whose
predicate the model derives from the state enum, and widening it would change the
meaning of a constraint an operator may already have reasoned about. Two additive
CHECKs say the same thing about the new column without rewriting the old one.

Nothing here is destructive. The downgrade drops the two constraints and the column;
it refuses outright while any generation names a directory, because dropping the
column is the only change that could lose the answer to "was this publicly trusted",
and a stopped migration with the data intact is the honest outcome — the same rule
5.2.2's downgrade applies to material.

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Created: 2026-10-16
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c9d0e1f2a3b4"
down_revision: str | None = "b8c9d0e1f2a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: ``AcmeDirectory``'s URLs, as literals (a CHECK cannot call Python). Drift-tested
#: against the enum, so a new member cannot appear without a migration here.
DIRECTORY_URLS = (
    "https://acme-staging-v02.api.letsencrypt.org/directory",
    "https://acme-v02.api.letsencrypt.org/directory",
    "https://localhost:14000/dir",
)

#: The states in which a generation carries no material *by construction*. Mirrors
#: ``app.models.certificate.pre_issuance_predicate()``; duplicated because a CHECK is
#: SQL and the migration has to stay reproducible if the predicate moves.
PRE_ISSUANCE_STATES = ("PENDING", "ORDERING", "CHALLENGE_PUBLISHED", "VALIDATING", "FAILED")

CK_GENERATIONS_DIRECTORY_KNOWN = "ck_certificate_generations_directory_known"
CK_GENERATIONS_DIRECTORY_REQUIRED = "ck_certificate_generations_directory_required"

#: Full names, because ``op.f`` marks an already-conventional name as final: the
#: ``ck_%(table_name)s_%(constraint_name)s`` convention would otherwise expand an
#: explicitly passed name a second time.
_KNOWN_PREDICATE = (
    "directory_url IS NULL OR directory_url IN "
    f"({', '.join(repr(url) for url in DIRECTORY_URLS)})"
)
_REQUIRED_PREDICATE = (
    f"state IN ({', '.join(repr(state) for state in PRE_ISSUANCE_STATES)}) "
    "OR directory_url IS NOT NULL"
)


def _drop_constraint(table: str, name: str) -> None:
    """Raw ``ALTER TABLE ... DROP CONSTRAINT IF EXISTS`` (see the 5.2.2 migration)."""
    op.execute(sa.text(f'ALTER TABLE "{table}" DROP CONSTRAINT IF EXISTS "{name}"'))


def _assert_no_directory_recorded() -> None:
    """Refuse a downgrade that would discard which CA a generation was ordered at."""
    op.execute(
        sa.text(
            """
            DO $$
            DECLARE
                recorded integer;
            BEGIN
                SELECT count(*) INTO recorded
                  FROM certificate_generations
                 WHERE directory_url IS NOT NULL;
                IF recorded > 0 THEN
                    RAISE EXCEPTION
                        'refusing to downgrade past 5.3: % certificate generation(s) record the '
                        'directory they were ordered at, and dropping that column would make '
                        'a staging certificate indistinguishable from a publicly trusted one. '
                        'Finish or remove those generations first.', recorded;
                END IF;
            END $$;
            """
        )
    )


def upgrade() -> None:
    op.add_column(
        "certificate_generations", sa.Column("directory_url", sa.String(length=255), nullable=True)
    )
    op.create_check_constraint(
        op.f(CK_GENERATIONS_DIRECTORY_KNOWN), "certificate_generations", _KNOWN_PREDICATE
    )
    op.create_check_constraint(
        op.f(CK_GENERATIONS_DIRECTORY_REQUIRED), "certificate_generations", _REQUIRED_PREDICATE
    )


def downgrade() -> None:
    """Remove the provenance pair — refusing while any generation records a directory."""
    _assert_no_directory_recorded()
    _drop_constraint("certificate_generations", CK_GENERATIONS_DIRECTORY_REQUIRED)
    _drop_constraint("certificate_generations", CK_GENERATIONS_DIRECTORY_KNOWN)
    op.drop_column("certificate_generations", "directory_url")
