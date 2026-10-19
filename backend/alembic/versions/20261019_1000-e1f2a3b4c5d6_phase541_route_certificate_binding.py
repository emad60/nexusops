"""Phase 5.4.1 — certificate-to-route binding foundation.

One nullable column, one composite foreign key, and the reason they are one
change: Phase 5.4's delivery target set is derived from
``routes.certificate_id`` (§7.4), so delivery cannot be built before some route
can name a certificate. This migration adds **association only**:

* ``routes.certificate_id`` — the certificate the route is *allowed* to serve.
  Nothing renders TLS, nothing widens ``routes.scheme`` (still a closed
  ``'http'`` CHECK), and no node operation is introduced. Phase 5.5 keeps the
  activation half.
* ``fk_routes_certificate_org`` — ``(certificate_id, org_id)`` →
  ``certificates (id, org_id)``, ``ON DELETE RESTRICT``. A plain
  ``certificate_id → certificates.id`` key would accept a route in one
  organization naming another organization's certificate; the pair makes that
  unrepresentable in the database, which is the only place the proof survives a
  service-layer bug. ``MATCH SIMPLE`` (the default) means an unbound route
  (``certificate_id IS NULL``) skips the check, so binding stays optional.
* ``uq_certificates_id_org`` — the referenced key PostgreSQL requires for that
  pair. It is redundant with the primary key on its own, and exists only so the
  composite FK is expressible.
* ``ix_routes_certificate_id`` — the delivery target query and the deletion guard
  both look routes up by certificate.

The downgrade refuses while any route is bound. Dropping the column would erase
every association silently, and "the route no longer names a certificate" is not
something a schema rollback should decide on an operator's behalf; unbinding is an
explicit endpoint. This matches the refusal shape of the 5.2.2/5.3/5.3.2
downgrades.

Revision ID: e1f2a3b4c5d6
Revises: d0e1f2a3b4c5
Created: 2026-10-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e1f2a3b4c5d6"
down_revision: str | None = "d0e1f2a3b4c5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FK_ROUTE_CERTIFICATE = "fk_routes_certificate_org"
UQ_CERTIFICATE_ID_ORG = "uq_certificates_id_org"
IX_ROUTES_CERTIFICATE = "ix_routes_certificate_id"


def _assert_no_bindings() -> None:
    """Refuse a downgrade that would drop live associations."""
    op.execute(
        sa.text(
            """
            DO $$
            DECLARE
                bound integer;
            BEGIN
                SELECT count(*) INTO bound FROM routes WHERE certificate_id IS NOT NULL;
                IF bound > 0 THEN
                    RAISE EXCEPTION
                        'refusing to downgrade past 5.4.1: % route(s) still reference a '
                        'certificate. Unbind them first; dropping the column would erase '
                        'those associations without an operator act.',
                        bound;
                END IF;
            END $$;
            """
        )
    )


def upgrade() -> None:
    op.create_unique_constraint(
        UQ_CERTIFICATE_ID_ORG, "certificates", ["id", "org_id"]
    )
    op.add_column("routes", sa.Column("certificate_id", sa.Uuid(), nullable=True))
    op.create_index(IX_ROUTES_CERTIFICATE, "routes", ["certificate_id"])
    op.create_foreign_key(
        FK_ROUTE_CERTIFICATE,
        "routes",
        "certificates",
        ["certificate_id", "org_id"],
        ["id", "org_id"],
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    """Remove the association — refusing while any route still holds one."""
    _assert_no_bindings()
    op.drop_constraint(FK_ROUTE_CERTIFICATE, "routes", type_="foreignkey")
    op.drop_index(IX_ROUTES_CERTIFICATE, table_name="routes")
    op.drop_column("routes", "certificate_id")
    op.drop_constraint(UQ_CERTIFICATE_ID_ORG, "certificates", type_="unique")
