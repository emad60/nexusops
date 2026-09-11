"""Add notification_deliveries.created_at

DeliveryOut (the API response model) inherits `created_at` from OutModel like
every other read schema, but the delivery table never had the column — so any
listing of deliveries crashed with a pydantic "Field required" ValidationError
(500 on GET /api/v1/notification-channels/deliveries). Backfill existing rows
with the row insert time via server_default.

Revision ID: a1f4c2d9e7b3
Revises: b5866787bde4
Create Date: 2026-09-11 01:30:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a1f4c2d9e7b3"
down_revision: str | None = "b5866787bde4"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "notification_deliveries",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_notification_deliveries_created_at",
        "notification_deliveries",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_notification_deliveries_created_at", table_name="notification_deliveries")
    op.drop_column("notification_deliveries", "created_at")
