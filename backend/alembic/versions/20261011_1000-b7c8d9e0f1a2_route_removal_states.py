"""Route removal states — requested vs confirmed.

A revoked (or otherwise no longer valid) route leaves the node's *desired*
configuration the moment its domain stops serving. That is not the same fact as
"the node stopped serving it", which is only true once a node has reported an
applied bundle that does not contain the route. Before this migration the route
row could express neither half: it was marked ``STALE`` with a free-text reason,
and nothing distinguished "we have asked for this to be removed" from "the node
has confirmed it is gone".

Two nullable timestamps carry the distinction:

* ``removal_requested_at`` — when the route left the desired configuration. Set
  by the renderer (the single place that decides a route is not eligible) and by
  the cross-organization release path.
* ``removal_confirmed_at`` — when an agent's *applied* result carried a bundle
  that omits this route. Only the apply-result handler writes it, so no path can
  claim a removal the node has not confirmed.

Both are cleared when the route is included in an applied bundle again, so a
re-verified name that later changes hands starts a fresh removal.

Additive and nullable: existing rows read as "no removal in flight", which is
what they are — no backfill, no rewrite, no downtime.

Revision ID: b7c8d9e0f1a2
Revises: f4a5b6c7d8e9
Created: 2026-10-11
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b7c8d9e0f1a2"
down_revision: str | None = "f4a5b6c7d8e9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

def upgrade() -> None:
    op.add_column(
        "routes",
        sa.Column("removal_requested_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "routes",
        sa.Column("removal_confirmed_at", sa.DateTime(timezone=True), nullable=True),
    )
    # No grant is repeated here on purpose: the app role's DML grant is on the
    # ``routes`` table (phase 4), and PostgreSQL column privileges are inherited
    # from it, so a new column needs no new privilege. RLS is unaffected — the
    # policies are row-level and already in place.


def downgrade() -> None:
    op.drop_column("routes", "removal_confirmed_at")
    op.drop_column("routes", "removal_requested_at")
