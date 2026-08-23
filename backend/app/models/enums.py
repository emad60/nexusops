"""Closed registries of domain enumerations.

Member names equal their values (uppercase) so that SQLAlchemy's default
name-based Enum storage and JSON serialisation never disagree.
"""

from __future__ import annotations

import enum


class StrEnum(enum.StrEnum):
    """String enum; member names equal values so name/value storage never disagrees."""

    pass


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"
    DISABLED = "DISABLED"


class ServerStatus(StrEnum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    DEGRADED = "DEGRADED"
    UNKNOWN = "UNKNOWN"


class DockerHostStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class ContainerStatus(StrEnum):
    RUNNING = "RUNNING"
    EXITED = "EXITED"
    PAUSED = "PAUSED"
    CREATED = "CREATED"
    RESTARTING = "RESTARTING"
    DEAD = "DEAD"
    REMOVED = "REMOVED"


class ContainerHealth(StrEnum):
    NONE = "NONE"
    STARTING = "STARTING"
    HEALTHY = "HEALTHY"
    UNHEALTHY = "UNHEALTHY"


class CredentialKind(StrEnum):
    PASSWORD = "PASSWORD"  # noqa: S105 - enum member name, not a credential
    SSH_KEY = "SSH_KEY"


class DeploymentStatus(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    ROLLBACK = "ROLLBACK"


class StepStatus(StrEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"


class DeploymentTrigger(StrEnum):
    MANUAL = "MANUAL"
    API = "API"
    ROLLBACK = "ROLLBACK"
    AUTO = "AUTO"


class MonitorStatus(StrEnum):
    PENDING = "PENDING"
    UP = "UP"
    DOWN = "DOWN"
    PAUSED = "PAUSED"


class CheckResult(StrEnum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    TIMEOUT = "TIMEOUT"
    ERROR = "ERROR"


class IncidentStatus(StrEnum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


class IncidentSeverity(StrEnum):
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    WARNING = "WARNING"


class IncidentEventKind(StrEnum):
    OPENED = "OPENED"
    DETECTED = "DETECTED"
    NOTIFIED = "NOTIFIED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RECOVERY_DETECTED = "RECOVERY_DETECTED"
    RESOLVED = "RESOLVED"
    NOTE = "NOTE"
    ACTION = "ACTION"


class ChannelType(StrEnum):
    EMAIL = "EMAIL"
    WEBHOOK = "WEBHOOK"


class DeliveryStatus(StrEnum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class AlertSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class MetricGranularity(StrEnum):
    RAW = "RAW"
    HOURLY = "HOURLY"
    DAILY = "DAILY"


class LogLevel(StrEnum):
    TRACE = "TRACE"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    FATAL = "FATAL"
    UNKNOWN = "UNKNOWN"


class LogSource(StrEnum):
    CONTAINER = "CONTAINER"
    DEPLOYMENT = "DEPLOYMENT"
    SERVER = "SERVER"


class EventLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ActorType(StrEnum):
    USER = "USER"
    SYSTEM = "SYSTEM"
    AGENT = "AGENT"
    API_KEY = "API_KEY"


class AuditResult(StrEnum):
    SUCCESS = "SUCCESS"
    DENIED = "DENIED"
    ERROR = "ERROR"
