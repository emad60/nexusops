"""rename ``server.*`` permission codenames to ``node.*``

The Node/Server vocabulary rename (authorization.md §2, product-roadmap.md) is
a surface change: the domain entity stays the ``servers`` table, but every
permission codename, API-key scope string and UI label moves to ``node``. This
migration carries the *stored* data across — the registry in
``app/core/permissions.py`` already emits the new names, so without this the
seeded rows and any minted API key would reference codenames that no longer
exist and silently grant nothing.

Scope:
  * ``permissions.codename`` rows (grants are id-based via ``role_permissions``,
    so no join table change is needed).
  * ``api_keys.scopes`` JSONB arrays, which hold raw scope strings.

Revision ID: c4e2a1f7b9d3
Revises: a3f1c8d24b6e
Create Date: 2026-09-23 10:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c4e2a1f7b9d3"
down_revision: str | None = "a3f1c8d24b6e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


#: ``old codename -> (new codename, group, description)``. Mirrors the registry
#: in ``app/core/permissions.py``; kept literal here so the migration stays
#: reproducible if the registry is ever reorganised.
_CODENAMES: tuple[tuple[str, str, str, str], ...] = (
    ("server.read", "node.read", "Nodes", "List and view nodes"),
    ("server.create", "node.create", "Nodes", "Register nodes"),
    ("server.update", "node.update", "Nodes", "Edit nodes"),
    ("server.delete", "node.delete", "Nodes", "Remove nodes"),
    (
        "credential.write",
        "node.credential.write",
        "Nodes",
        "Store / rotate node credentials",
    ),
)

#: The reverse direction for :func:`downgrade`, derived from ``_CODENAMES``.
_DOWNGRADE: tuple[tuple[str, str, str, str], ...] = tuple(
    (new, old, group, description) for old, new, group, description in _CODENAMES
)

#: Rewrites every ``server.*`` / ``credential.write`` entry in a scope array to
#: its ``node.*`` form, preserving order. Only touches arrays that need it.
_UPGRADE_SCOPES = """
UPDATE api_keys
SET scopes = (
    SELECT jsonb_agg(
        CASE
            WHEN elem = 'credential.write' THEN 'node.credential.write'
            WHEN elem LIKE 'server.%' THEN 'node.' || substr(elem, 8)
            ELSE elem
        END
        ORDER BY ordinality
    )
    FROM jsonb_array_elements_text(scopes) WITH ORDINALITY AS t(elem, ordinality)
)
WHERE jsonb_typeof(scopes) = 'array'
  AND EXISTS (
      SELECT 1
      FROM jsonb_array_elements_text(scopes) AS e(elem)
      WHERE e.elem LIKE 'server.%' OR e.elem = 'credential.write'
  )
"""

_DOWNGRADE_SCOPES = """
UPDATE api_keys
SET scopes = (
    SELECT jsonb_agg(
        CASE
            WHEN elem = 'node.credential.write' THEN 'credential.write'
            WHEN elem LIKE 'node.%' THEN 'server.' || substr(elem, 6)
            ELSE elem
        END
        ORDER BY ordinality
    )
    FROM jsonb_array_elements_text(scopes) WITH ORDINALITY AS t(elem, ordinality)
)
WHERE jsonb_typeof(scopes) = 'array'
  AND EXISTS (
      SELECT 1
      FROM jsonb_array_elements_text(scopes) AS e(elem)
      WHERE e.elem LIKE 'node.%' OR e.elem = 'node.credential.write'
  )
"""


def _rename_permissions(mapping: tuple[tuple[str, str, str, str], ...]) -> None:
    for old, new, group, description in mapping:
        op.execute(
            sa.text(
                "UPDATE permissions "
                'SET codename = :new, "group" = :group, description = :description '
                "WHERE codename = :old"
            ).bindparams(new=new, group=group, description=description, old=old)
        )


def upgrade() -> None:
    _rename_permissions(_CODENAMES)
    op.execute(_UPGRADE_SCOPES)


def downgrade() -> None:
    _rename_permissions(_DOWNGRADE)
    op.execute(_DOWNGRADE_SCOPES)
