"""Phase 2.2 — make legacy environment typing match the documented precedence.

The documented rule (domain-model.md §2.2.1) is **slug first**: if the
normalised slug is a recognised alias its type wins; otherwise use a recognised
name alias; otherwise default to ``DEV``. Migration ``d4e5f6a7b8c9`` did not
implement that — it classified with a flat ``slug OR name`` test in which PROD
was checked before STAGING, so a row whose slug says ``staging``/``stage`` but
whose name says ``production``/``prod`` was set to ``PROD`` when the rule
requires ``STAGING``.

That single disagreement is the only case where the two rules differ:

===============  ==============  ===============  ==============
slug             name            slug-first rule  ``d4e5…`` result
===============  ==============  ===============  ==============
prod alias       staging alias   PROD             PROD
staging alias    prod alias      **STAGING**      PROD  ← wrong
prod alias       (none)          PROD             PROD
staging alias    (none)          STAGING          STAGING
(none)           prod alias      PROD             PROD
(none)           staging alias   STAGING          STAGING
===============  ==============  ===============  ==============

This migration corrects exactly that fingerprint: rows whose slug is a staging
alias and whose name is a prod alias **and whose current type is the ``PROD``
that the previous migration wrote**. The last condition is deliberate — a row
whose operator has since set it to ``DEV`` or left it ``STAGING`` is a
legitimate manual decision and is left untouched. What remains ambiguous is a
row an operator *wants* kept as ``PROD`` despite a staging slug; there is no
signal to distinguish that from the previous migration's output, and the
documented precedence wins.

Only ``environment_type`` (and ``updated_at``) changes: ids, deployments,
uniqueness, organization ownership and RLS are untouched.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Created: 2026-10-09
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: str | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


#: Slug-first rule: a staging slug beats a conflicting prod name. Narrowed to
#: rows still carrying the previous migration's ``PROD`` output so a deliberate
#: operator change to another value is preserved.
FIX_ENVIRONMENT_TYPE_PRECEDENCE = """
UPDATE deployment_environments
   SET environment_type = 'STAGING',
       updated_at = now()
 WHERE environment_type = 'PROD'
   AND lower(btrim(slug)) IN ('staging', 'stage')
   AND lower(btrim(name)) IN ('production', 'prod');
"""


def upgrade() -> None:
    op.execute(FIX_ENVIRONMENT_TYPE_PRECEDENCE)


def downgrade() -> None:
    """No-op: the correction is a classification, not a reversible structure.

    Reverting would re-apply the wrong precedence (``PROD`` for a staging slug),
    which is exactly the bug this migration exists to fix. The schema shape is
    unchanged either way.
    """
