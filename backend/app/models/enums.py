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


class OrganizationStatus(StrEnum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


class MembershipStatus(StrEnum):
    # No INVITED state in v1: onboarding is operator-issued (an administrator
    # creates the account and its membership together), so a membership is
    # active from the moment it exists. A real invite flow is its own phase.
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


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


class EnvironmentType(StrEnum):
    """Kind of a project-scoped deployment environment (Phase 2).

    Descriptive only — **never** an authorization dimension. Access to an
    environment is decided by permissions and organization membership (and, in
    a later phase, grants), not by whether it is production. Stored uppercase
    like every other closed registry in this module; the SPA renders the labels
    Development / Staging / Production.
    """

    DEV = "DEV"
    STAGING = "STAGING"
    PROD = "PROD"


class EnrollmentTokenState(StrEnum):
    """Derived lifecycle state of an enrollment token, computed server-side.

    Stored as nothing: a token's state is a pure function of ``used_at``,
    ``revoked_at`` and ``expires_at``, so it cannot drift from the row. Revoked
    takes precedence over used, which takes precedence over expired, so a token
    that was revoked after use still reads REVOKED.
    """

    ACTIVE = "ACTIVE"
    USED = "USED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class OperationStatus(StrEnum):
    """Lifecycle of one node operation (node-agent-architecture.md §5.1).

    ``SUCCEEDED``/``FAILED``/``EXPIRED``/``CANCELLED`` are terminal: once a row
    reaches one of them it never transitions again. That immutability is what
    makes a replayed claim or a late duplicate result a no-op instead of a
    second execution.
    """

    PENDING = "PENDING"
    CLAIMED = "CLAIMED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"

    @classmethod
    def terminal(cls) -> frozenset[OperationStatus]:
        return frozenset({cls.SUCCEEDED, cls.FAILED, cls.EXPIRED, cls.CANCELLED})


class OperationType(StrEnum):
    """The whitelist. Nothing outside this enum ships as an exec surface.

    Each type maps to an existing permission codename plus a node capability
    (see ``app.schemas.operation.OPERATION_SPECS``) — the architecture
    deliberately does **not** add a generic ``node.execute`` codename, so a
    container action reuses ``container.lifecycle`` rather than inventing a new
    grant. Reserved types from the companion docs (``secret.env.apply``,
    ``certificate.*``, the ``nginx.*`` family) are deliberately absent until the
    subsystems they belong to ship, so no params pass-through can exist for them.
    """

    CONTAINER_START = "container.start"
    CONTAINER_STOP = "container.stop"
    CONTAINER_RESTART = "container.restart"
    CONTAINER_REMOVE = "container.remove"
    LOGS_TAIL = "logs.tail"


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
