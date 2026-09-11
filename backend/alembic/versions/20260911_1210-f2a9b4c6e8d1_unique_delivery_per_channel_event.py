"""One notification delivery per channel per event

The dispatcher runs in every API worker and consumes Redis pubsub, which
broadcasts each event frame to ALL subscribers — without a uniqueness
guarantee each worker queued (and emailed) its own delivery for the same
(channel, event). The constraint lands only after the duplicates produced by
that era are removed, keeping the earliest delivery per pair. Rows with a
NULL event_id (manual/test sends) are exempt: Postgres treats NULLs as
distinct.

Revision ID: f2a9b4c6e8d1
Revises: d9e4f7a1c3b5
Create Date: 2026-09-11 12:10:00

"""

from collections.abc import Sequence

from alembic import op

revision: str = "f2a9b4c6e8d1"
down_revision: str | None = "d9e4f7a1c3b5"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        DELETE FROM notification_deliveries a
        USING notification_deliveries b
        WHERE a.event_id IS NOT NULL
          AND b.event_id IS NOT NULL
          AND a.channel_id = b.channel_id
          AND a.event_id  = b.event_id
          AND a.id > b.id
        """
    )
    op.create_unique_constraint(
        "uq_deliveries_channel_event",
        "notification_deliveries",
        ["channel_id", "event_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_deliveries_channel_event",
        "notification_deliveries",
        type_="unique",
    )
