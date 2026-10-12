"""Phase 5.2.1 — the organization DEK envelope.

Two additive columns on ``organizations`` and one constraint, and that is the whole
schema change:

* ``dek_ciphertext`` — the organization's Fernet DEK, wrapped by the configured KEK
  provider. Stored as the self-describing envelope
  (``v1:<provider>:<key_id>:<key_version>:<base64 ciphertext>``), so a row records
  which provider can unwrap it and a KEK rotation can tell what it is looking at
  without guessing. NULL until the organization's first Phase-5 write.
* ``dek_generation`` — which DEK generation is wrapped: ``0`` is the schema's word
  for "no DEK yet", the first real DEK is ``1``, and a rotation increments it. It
  participates in the encryption-context binding, so a DEK cannot be replayed as
  another generation's.
* ``ck_organizations_dek_pair_valid`` — ``(dek_ciphertext IS NULL) =
  (dek_generation = 0)``. The pair moves in lockstep in both directions, which is
  what makes "generation 0" trustworthy as a marker: no writer can leave a
  ciphertext behind a zero generation or a bare generation with no material.

**Nothing else lands here.** No ``dns_providers``, no ``acme_accounts``, no
``deke_id``, no certificate material column, and no forward reference to any of
them: those arrive in 5.2.2 together with the tables they belong to. There is
therefore nowhere in this schema for a placeholder key to be written, which is the
point — an issued generation still cannot exist.

The downgrade **refuses** when any organization has a wrapped DEK. Dropping these
columns would destroy the only copy of key material that Vault can still unwrap for
that organization, and a schema reversal performed to roll back an application
version is not a reason to strand every organization's envelope. An operator who
really means it clears the column first (which is itself an auditable,
deliberate act).

Revision ID: f5a6b7c8d9e0
Revises: c8d9e0f1a2b3
Created: 2026-10-12
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f5a6b7c8d9e0"
down_revision: str | None = "c8d9e0f1a2b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

#: Mirrors the model's constraint name (``ck_%(table_name)s_%(constraint_name)s``).
#: Wrapped in ``op.f()`` wherever it is passed to Alembic, so the convention is
#: not applied a second time — without it the name lands as
#: ``ck_organizations_ck_organizations_dek_pair_valid``, which is both ugly and
#: invisible to ``compare_metadata`` (the drift check).
DEK_PAIR_CONSTRAINT = "ck_organizations_dek_pair_valid"
DEK_PAIR_PREDICATE = "(dek_ciphertext IS NULL) = (dek_generation = 0)"


def upgrade() -> None:
    op.add_column("organizations", sa.Column("dek_ciphertext", sa.Text(), nullable=True))
    op.add_column(
        "organizations",
        sa.Column(
            "dek_generation",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.create_check_constraint(op.f(DEK_PAIR_CONSTRAINT), "organizations", DEK_PAIR_PREDICATE)


def downgrade() -> None:
    """Drop the envelope columns — unless doing so would destroy key material."""
    bind = op.get_bind()
    populated = bind.execute(
        sa.text("SELECT count(*) FROM organizations WHERE dek_ciphertext IS NOT NULL")
    ).scalar_one()
    if populated:
        raise RuntimeError(
            f"refusing to drop the organization DEK envelope: {populated} organization(s) "
            "have a wrapped DEK. Dropping these columns would destroy the only copy of that "
            "key material and leave every one of those organizations unable to decrypt its "
            "Phase-5 data. Re-wrap or remove it deliberately first (see "
            "docs/phase5-design.md §6.3), then re-run the downgrade."
        )
    op.drop_constraint(op.f(DEK_PAIR_CONSTRAINT), "organizations", type_="check")
    op.drop_column("organizations", "dek_generation")
    op.drop_column("organizations", "dek_ciphertext")
