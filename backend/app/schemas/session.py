"""Session schemas."""

from __future__ import annotations

from datetime import datetime

from app.models import Session as DbSession
from app.schemas.base import OutModel


class SessionOut(OutModel):
    ip_address: str
    device_label: str
    user_agent: str
    last_seen_at: datetime | None = None
    expires_at: datetime
    revoked_at: datetime | None = None
    current: bool = False

    @classmethod
    def from_session(cls, session: DbSession, *, current: bool = False) -> SessionOut:
        return cls(
            id=session.id,
            created_at=session.created_at,
            ip_address=session.ip_address,
            device_label=session.device_label,
            user_agent=session.user_agent,
            last_seen_at=session.last_seen_at,
            expires_at=session.expires_at,
            revoked_at=session.revoked_at,
            current=current,
        )
