"""Fix frozen created_at defaults on system_events and audit_logs

Both columns were created with the quoted string default 'now()', which
PostgreSQL folds to a constant at CREATE TABLE time — so every row written
since carried the table-creation instant (observed in production as all
audit/event rows sharing one timestamp, making both tabs look static). The
models now use func.now(); this repairs the existing defaults to evaluate
per insert.

Historical rows keep the frozen creation-time timestamp — the true insert
times are not recoverable.

Revision ID: b3d7f9e2c6a4
Revises: f2a9b4c6e8d1
Create Date: 2026-09-13 19:45:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b3d7f9e2c6a4"
down_revision: str | None = "f2a9b4c6e8d1"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

_TZ = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.alter_column("system_events", "created_at", existing_type=_TZ, server_default=sa.func.now())
    op.alter_column("audit_logs", "created_at", existing_type=_TZ, server_default=sa.func.now())


def downgrade() -> None:
    # Restores the historical (buggy) string form: DEFAULT 'now()' folds to a
    # constant at DDL time, freezing timestamps at this migration's run time.
    op.alter_column(
        "system_events", "created_at", existing_type=_TZ, server_default=sa.text("'now()'")
    )
    op.alter_column(
        "audit_logs", "created_at", existing_type=_TZ, server_default=sa.text("'now()'")
    )
