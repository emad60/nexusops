"""created_at server defaults must evaluate per insert, not at table creation."""

from __future__ import annotations

import pytest
from sqlalchemy import text

pytestmark = pytest.mark.integration


async def test_audit_and_event_created_at_defaults_are_dynamic(db):
    """Regression: system_events and audit_logs shipped with DEFAULT 'now()'
    (quoted string), which PostgreSQL folds to a constant at CREATE TABLE
    time. Every row then carried the table-creation instant — in production
    all audit/event rows shared one timestamp and both tabs looked frozen.
    The default must be the bare now() call, evaluated per row."""
    for table in ("audit_logs", "system_events"):
        default = await db.scalar(
            text(
                "select column_default from information_schema.columns "
                "where table_schema = 'public' and table_name = :t "
                "and column_name = 'created_at'"
            ).bindparams(t=table)
        )
        assert default is not None, f"{table}.created_at has no default"
        assert default == "now()", (
            f"{table}.created_at default is {default!r}; a quoted literal is "
            "folded to a constant at DDL time and freezes all future rows"
        )
