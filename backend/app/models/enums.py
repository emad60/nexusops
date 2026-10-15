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
    grant.

    Phase 4 adds the three ``nginx.*`` types the domain-routing design approves
    and nothing else. Their params are typed models (see
    :mod:`app.schemas.proxy`); there is no file-write or command primitive and
    no path is ever interpolated into a shell. ``certificate.*`` and
    ``secret.env.apply`` stay absent until the phases that own them ship.
    """

    CONTAINER_START = "container.start"
    CONTAINER_STOP = "container.stop"
    CONTAINER_RESTART = "container.restart"
    CONTAINER_REMOVE = "container.remove"
    LOGS_TAIL = "logs.tail"
    NGINX_BOOTSTRAP = "nginx.bootstrap"
    NGINX_APPLY = "nginx.apply"
    NGINX_STATUS = "nginx.status"


class DomainStatus(StrEnum):
    """Ownership-verification lifecycle of a Domain (domain-routing.md §4).

    ``STALE`` is the grace state: the periodic sweep no longer sees the proof
    TXT record but the name was previously verified. Routes stop being served in
    both ``STALE`` and ``UNVERIFIED`` — render filters on ``VERIFIED`` only — so
    losing the proof never leaves a live route behind.
    """

    PENDING = "PENDING"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    STALE = "STALE"
    UNVERIFIED = "UNVERIFIED"
    FAILED = "FAILED"


class RouteConfigState(StrEnum):
    """Last nginx apply outcome for a route, as reported by its node's agent.

    ``PENDING`` is "an apply is in flight"; ``IN_SYNC`` is the only state that
    means the node's live configuration matches the desired bundle.
    """

    PENDING = "PENDING"
    IN_SYNC = "IN_SYNC"
    STALE = "STALE"
    FAILED = "FAILED"


class RouteRemovalState(StrEnum):
    """How far a route's *removal* has got, which ``config_state`` cannot say.

    A route that must stop being served leaves its node's desired configuration
    at once, but the node may still be running the configuration that serves it:
    that is two different facts, and only one of them is a fact the control plane
    can know by itself.

    ``REQUESTED`` — the route is out of the desired tree (its domain stopped
    serving, so it is no longer allowed to answer). Nothing may claim it stopped
    serving; a node that is offline or failing sits here.
    ``CONFIRMED`` — a node reported an *applied* bundle that does not contain this
    route. Only the apply-result handler moves a route here.
    """

    REQUESTED = "REQUESTED"
    CONFIRMED = "CONFIRMED"


class ProxyApplyOutcome(StrEnum):
    """Terminal outcome of one ``nginx.apply`` operation on a node."""

    APPLIED = "applied"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    ROLLBACK_FAILED = "rollback_failed"


class ListenerOwnership(StrEnum):
    """Who holds one required listener port, per the node's pre-flight.

    The distinction exists because "nginx is installed" says nothing about
    whether NexusOps can manage it: ``MANAGED`` is the only state that means the
    intended nginx instance owns the port, ``OTHER`` names a conflicting process,
    ``FREE`` is an unused port, and ``UNKNOWN`` is an unreadable listener table
    (never treated as free).
    """

    MANAGED = "MANAGED"
    OTHER = "OTHER"
    FREE = "FREE"
    UNKNOWN = "UNKNOWN"


class MonitorTargetType(StrEnum):
    """What a monitor observes (domain-model.md §2.6, polymorphic targets).

    ``URL`` is the Phase 0 shape every existing monitor keeps; ``ROUTE`` is a
    NexusOps-managed route, whose HTTP uptime is checked from the control plane
    exactly like a URL target. There is deliberately no certificate target in
    Phase 4 — TLS is Phase 5.
    """

    URL = "URL"
    ROUTE = "ROUTE"


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


# --- certificates (Phase 5) --------------------------------------------------


class CertificateStatus(StrEnum):
    """Certificate-level view of the *current* generation, derived, never stored raw.

    The service computes this from the certificate's current generation (or, before
    the first issuance, from its newest generation), so the row can never claim a
    state its material does not support. **Phase 5.1 could only produce ``PENDING``
    and ``FAILED``** — every other member names a material-bearing state whose
    columns arrived in Phase 5.2.2 — and since then
    :func:`app.services.certificate_lifecycle.certificate_status_for` derives this
    from a generation's state directly, so a generation that holds material reports
    the member that describes it. Nothing in the tree writes one yet. ``REVOKED``
    and ``REVOKED_LOCAL_ONLY`` are deliberately distinct — the CA acknowledged the
    revocation in the first case and never answered in the second.
    """

    PENDING = "PENDING"
    ISSUED = "ISSUED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    SUSPENDED = "SUSPENDED"
    REVOCATION_PENDING = "REVOCATION_PENDING"
    REVOKED = "REVOKED"
    REVOKED_LOCAL_ONLY = "REVOKED_LOCAL_ONLY"


class CertificateChallengeType(StrEnum):
    """How ownership of an identifier is proved to the CA.

    DNS-01 only in v1: it is the only challenge that works for NAT-ed servers
    and for wildcards, and it needs no inbound connectivity to the node. An
    ``http-01`` value is therefore not a member — the API refuses the request
    with a named error instead of persisting a challenge nobody can serve.
    """

    DNS_01 = "dns-01"


class CertificateKeyAlgorithm(StrEnum):
    """The key type generated for a generation. Fixed in v1; never client-chosen."""

    ECDSA_P256 = "ecdsa-p256"


class CertificateGenerationState(StrEnum):
    """Lifecycle of one ACME order + key pair, pre- and post-issuance.

    **Phase 5.1 truncated this vocabulary on purpose.** Only the states a
    generation can occupy *before* any material exists were members, so a
    material-less ``ISSUED`` generation was unrepresentable — at the enum, at the
    database CHECK and at the API — rather than merely discouraged. Phase 5.2
    widens it to the full state machine (phase5-design.md §2.2) **in the same
    migration that adds the material columns and the organization DEK envelope
    those states require**, and pairs it with the material guard CHECK
    (:func:`material_bearing`): a generation in any of the states below cannot
    exist without ``key_ciphertext``, ``chain_ciphertext``, ``deke_id``,
    ``issued_at``, ``not_before`` and ``not_after``.

    Two classmethods carry the structural predicates, and both the model and the
    migration derive from them rather than restating a list:

    * :meth:`live_pre_issuance` — the mutable subset, and the predicate of the
      partial unique index that allows at most one in-flight generation per
      certificate, so a second concurrent issuance is a database error and not
      two racing orders. Widening the live set widens the index with it.
    * :meth:`material_bearing` — the post-issuance subset, which the guard CHECK
      requires material for. ``SUPERSEDED``, ``SUSPENDED``, ``EXPIRED`` and the
      revocation states are all material-bearing: a superseded or revoked
      generation still holds the material the node may still be serving until it
      is re-delivered or removed (§8.5, §9.3), so dropping the ciphertext for one
      would be data loss dressed up as cleanup.

    ``REVOKED_LOCAL_ONLY`` is deliberately distinct from ``REVOKED``: the CA
    acknowledged the revocation in the first case and never answered in the
    second (see :class:`CertificateRevocationState` for the CA axis).
    """

    # Pre-issuance (5.1): no material exists yet.
    PENDING = "PENDING"
    ORDERING = "ORDERING"
    CHALLENGE_PUBLISHED = "CHALLENGE_PUBLISHED"
    VALIDATING = "VALIDATING"
    FAILED = "FAILED"
    # Post-issuance (5.2): material is mandatory for every one of these.
    ISSUED = "ISSUED"
    SUPERSEDED = "SUPERSEDED"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"
    REVOCATION_PENDING = "REVOCATION_PENDING"
    REVOKED = "REVOKED"
    REVOCATION_FAILED = "REVOCATION_FAILED"
    REVOKED_LOCAL_ONLY = "REVOKED_LOCAL_ONLY"

    @classmethod
    def live_pre_issuance(cls) -> tuple[CertificateGenerationState, ...]:
        """The states in which a generation is still being worked on.

        At most one of these may exist per certificate at a time. ``FAILED`` is
        deliberately **not** one of them: a spent attempt may be retried, and a
        retry must not be blocked by the failed row it replaces.
        """
        return (cls.PENDING, cls.ORDERING, cls.CHALLENGE_PUBLISHED, cls.VALIDATING)

    @classmethod
    def material_bearing(cls) -> tuple[CertificateGenerationState, ...]:
        """The states whose rows must carry key material and a DEK generation.

        The complement of :meth:`live_pre_issuance` plus ``FAILED``: a state that
        has left the pre-issuance lifecycle is one the CA has answered for, and
        its material (or the record of what it was) outlives the order. The
        guard CHECK is the *or* branch over exactly this tuple.
        """
        pre_issuance = set(cls.live_pre_issuance()) | {cls.FAILED}
        return tuple(state for state in cls if state not in pre_issuance)


class CertificateRevocationState(StrEnum):
    """The CA conversation about a generation, deliberately a second axis.

    ``state`` answers "is this material usable?" and ``revocation_state`` answers
    "what did the CA say?". They are separate so that removing material from a
    node is never gated on the CA (phase5-design.md §2.2, §9.3 Stage 4): a
    ``REVOCATION_FAILED`` generation can still be ``SUPERSEDED`` and safely absent
    from every node, and the UI shows ``REVOKED_LOCAL_ONLY`` as a warning with a
    retry rather than as a success.

    ``FAILED`` and ``REVOKED_LOCAL_ONLY`` are distinct: the first means the CA
    was reached and refused (or the request was rejected), the second means the
    CA never answered at all.
    """

    NOT_REQUESTED = "NOT_REQUESTED"
    PENDING = "PENDING"
    REVOKED = "REVOKED"
    FAILED = "FAILED"
    REVOKED_LOCAL_ONLY = "REVOKED_LOCAL_ONLY"


class AcmeDirectory(StrEnum):
    """Which certificate authority a per-organization ACME account belongs to.

    A **closed set with its URLs attached**, because the account's identity is
    ``(organization, directory)`` and staging vs production are two different
    accounts, not two settings of one (phase5-design.md §5.4). The URL lives on
    the enum so the schema, the account row and the test fixtures all name the
    directory the same way; the row stores the URL, which is what a certificate's
    generation records so a staging certificate can be recognized as staging from
    its own data.

    Production is a **separate member, never inferred from the environment**: the
    design's rule is that selecting production requires explicit configuration, so
    there is no ``default()`` here and no function that reads ``ENVIRONMENT`` to
    pick one. A caller that has no configured directory has no directory — which
    fails closed, as the design requires, rather than quietly minting a staging
    certificate a browser would distrust.
    """

    STAGING = "staging"
    PRODUCTION = "production"

    def url(self) -> str:
        """The directory URL stored on the account row and recorded per issuance."""
        return _ACME_DIRECTORY_URLS[self]

    @classmethod
    def from_url(cls, url: str) -> AcmeDirectory | None:
        """The directory a stored URL names, or ``None`` when it names neither.

        ``None`` rather than a default: an unrecognized directory URL — a future
        CA, a typo, a hand-edited row — must be visible as unknown instead of being
        silently treated as one of the two known directories.
        """
        for directory, candidate in _ACME_DIRECTORY_URLS.items():
            if candidate == url:
                return directory
        return None


#: One URL per directory. Let's Encrypt's published endpoints; a CA swap is a new
#: member plus an entry here, and every existing row keeps the URL it was made at.
_ACME_DIRECTORY_URLS: dict[AcmeDirectory, str] = {
    AcmeDirectory.STAGING: "https://acme-staging-v02.api.letsencrypt.org/directory",
    AcmeDirectory.PRODUCTION: "https://acme-v02.api.letsencrypt.org/directory",
}


class DnsProviderKind(StrEnum):
    """Which DNS API a stored credential speaks to.

    One member in v1 (Cloudflare) — the enum, not the column, is the seam: adding
    Route53 or DigitalOcean later is a new member plus a provider implementation,
    not a schema change, because ``dns_providers.kind`` is a CHECK over this
    vocabulary. An unknown value is refused at the database, so a row can never
    name a provider the control plane cannot actually call.
    """

    CLOUDFLARE = "cloudflare"
