"""Schemas for notification channels and delivery records.

Channel configuration is accepted once at create/update time, validated, then
encrypted whole and never returned by any endpoint — responses carry only the
pre-masked ``display_target``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, StringConstraints, model_validator

from app.models.enums import ChannelType, DeliveryStatus
from app.schemas.base import APIModel, OutModel

MAX_CHANNEL_EVENTS = 32
MAX_WEBHOOK_HEADERS = 10

SecretName = Annotated[str, StringConstraints(min_length=1, max_length=64, pattern=r"^[\w-]+$")]


class EmailConfig(APIModel):
    recipients: list[EmailStr] = Field(min_length=1, max_length=25)


class SecretHeader(APIModel):
    name: SecretName
    value: str = Field(min_length=8, max_length=256)


class WebhookConfig(APIModel):
    url: str = Field(min_length=1, max_length=1000)
    headers: dict[str, str] = Field(default_factory=dict, max_length=MAX_WEBHOOK_HEADERS)
    secret_header: SecretHeader | None = None


class ChannelBase(APIModel):
    name: str = Field(min_length=1, max_length=120)
    type: ChannelType
    events: list[str] = Field(
        default_factory=list,
        max_length=MAX_CHANNEL_EVENTS,
        description="Event types to subscribe to; empty subscribes to all.",
    )
    enabled: bool = True


class ChannelCreate(ChannelBase):
    config: EmailConfig | WebhookConfig

    @model_validator(mode="after")
    def _config_matches_type(self) -> ChannelCreate:
        expected = EmailConfig if self.type == ChannelType.EMAIL else WebhookConfig
        if not isinstance(self.config, expected):
            raise ValueError(f"config does not match channel type {self.type.value}")
        return self


class ChannelUpdate(APIModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    events: list[str] | None = Field(default=None, max_length=MAX_CHANNEL_EVENTS)
    enabled: bool | None = None
    type: ChannelType | None = None
    config: EmailConfig | WebhookConfig | None = None

    @model_validator(mode="after")
    def _config_matches_type(self) -> ChannelUpdate:
        if self.config is not None and self.type is not None:
            expected = EmailConfig if self.type == ChannelType.EMAIL else WebhookConfig
            if not isinstance(self.config, expected):
                raise ValueError(f"config does not match channel type {self.type.value}")
        return self


class ChannelOut(OutModel):
    """Channel metadata. Configuration is deliberately absent by design."""

    updated_at: datetime
    name: str
    type: ChannelType
    display_target: str = ""
    events: list[str] = Field(default_factory=list)
    enabled: bool
    created_by_id: UUID | None = None


class DeliveryOut(OutModel):
    channel_id: UUID
    event_id: UUID | None = None
    incident_id: UUID | None = None
    event_type: str
    subject: str = ""
    body: str = ""
    status: DeliveryStatus
    attempts: int
    last_error: str = ""
    sent_at: datetime | None = None
    next_retry_at: datetime | None = None


class TestNotificationOut(BaseModel):
    status: DeliveryStatus
    error: str | None = None


__all__ = [
    "MAX_CHANNEL_EVENTS",
    "MAX_WEBHOOK_HEADERS",
    "ChannelCreate",
    "ChannelOut",
    "ChannelUpdate",
    "DeliveryOut",
    "EmailConfig",
    "SecretHeader",
    "TestNotificationOut",
    "WebhookConfig",
]
