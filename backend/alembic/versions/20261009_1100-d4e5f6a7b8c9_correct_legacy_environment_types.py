"""Phase 2.1 — correct legacy ``environment_type`` classification.

The Phase 2 migration promoted ``deployment_environments`` to project scope and
added ``environment_type`` with ``server_default='DEV'``, then dropped the
default. Every **pre-existing** row therefore became ``DEV`` — including rows
whose slug/name plainly say ``production`` or ``staging``. The kind was never
recorded before Phase 2, so the default was safe but wrong for the obvious
cases. This migration corrects those rows with a small, explicit, case-normalised
mapping — no fuzzy matching, no guessing beyond an unambiguous exact name:

===============  ==========
slug / name      type
===============  ==========
production, prod PROD
staging, stage   STAGING
dev, development DEV
anything else    DEV (unchanged)
===============  ==========

Rules, deliberately narrow:

* Only rows still carrying the Phase 2 default ``DEV`` are candidates, so an
  operator's explicit post-Phase-2 classification is never overwritten.
* ``slug`` is checked first, then ``name``; both are compared case-insensitively
  after trimming. A row whose slug and name disagree takes the PROD/STAGING
  precedence in the order listed above.
* ``dev``/``development`` and anything unknown already satisfy the DEV fallback,
  so the migration touches only rows that actually change (their ``updated_at``
  is bumped; untouched rows keep theirs).

Nothing else changes: no id, deployment, unique constraint, organization
ownership or RLS policy is touched — the statement updates one descriptive
column in place. Documented in domain-model.md §2.2.1 and
secrets-architecture.md (environment types).

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Created: 2026-10-09
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


#: The exact aliases that promote a defaulted row to a non-DEV kind. Kept as one
#: literal list so the mapping is reviewable in a single place.
PROD_ALIASES = ("production", "prod")
STAGING_ALIASES = ("staging", "stage")
#: ``dev``/``development`` and unknown values already fall back to DEV, so only
#: the two promotable families appear in the WHERE clause.
CLASSIFIED_ALIASES = PROD_ALIASES + STAGING_ALIASES


def _quoted(aliases: Sequence[str]) -> str:
    return ", ".join(f"'{alias}'" for alias in aliases)


CORRECT_LEGACY_ENVIRONMENT_TYPES = """
UPDATE deployment_environments
   SET environment_type = CASE
           WHEN lower(btrim(slug)) IN ({prod})
             OR lower(btrim(name)) IN ({prod}) THEN 'PROD'
           WHEN lower(btrim(slug)) IN ({staging})
             OR lower(btrim(name)) IN ({staging}) THEN 'STAGING'
           ELSE 'DEV'
       END,
       updated_at = now()
 WHERE environment_type = 'DEV'
   AND (
       lower(btrim(slug)) IN ({classified})
       OR lower(btrim(name)) IN ({classified})
   );
""".format(
    prod=_quoted(PROD_ALIASES),
    staging=_quoted(STAGING_ALIASES),
    classified=_quoted(CLASSIFIED_ALIASES),
)


def upgrade() -> None:
    op.execute(CORRECT_LEGACY_ENVIRONMENT_TYPES)


def downgrade() -> None:
    """No-op: the correction is a best-effort classification, not reversible.

    Reverting would set PROD/STAGING rows back to ``DEV`` and *lose* the
    corrected classification for rows that legitimately belong there. The
    Phase 2 shape (a column that exists and holds a valid kind) is unchanged, so
    nothing structural depends on a reverse.
    """
