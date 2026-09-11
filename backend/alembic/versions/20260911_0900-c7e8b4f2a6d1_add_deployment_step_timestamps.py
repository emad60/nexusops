"""Add deployment_steps.created_at / updated_at

DeploymentStepOut (the API response model) inherits `created_at` from OutModel
like every other read schema, but the step table never had the timestamp
columns — serializing any deployment detail (GET /api/v1/deployments/{id}) or
the trigger response crashed with a pydantic "Field required" ValidationError.
Backfill existing rows with the row insert time via server_default.

Revision ID: c7e8b4f2a6d1
Revises: a1f4c2d9e7b3
Create Date: 2026-09-11 09:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c7e8b4f2a6d1"
down_revision: str | None = "a1f4c2d9e7b3"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "deployment_steps",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.add_column(
        "deployment_steps",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("deployment_steps", "updated_at")
    op.drop_column("deployment_steps", "created_at")
