"""Add refresh_tokens.grace_used

One-shot flag bounding the refresh-rotation grace rescue (see
auth_service.refresh): a replayed immediately-superseded token is rescued
once — the rescue re-rotates from that token and flips the flag — and any
further replay of the same token is theft again and revokes the session
family. Without the flag a stolen token could be replayed every < grace
window forever, each rescue resetting the window.

Revision ID: d9e4f7a1c3b5
Revises: c7e8b4f2a6d1
Create Date: 2026-09-11 09:30:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d9e4f7a1c3b5"
down_revision: str | None = "c7e8b4f2a6d1"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "refresh_tokens",
        sa.Column(
            "grace_used",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("refresh_tokens", "grace_used")
