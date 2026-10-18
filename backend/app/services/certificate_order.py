"""The durable progress of one ACME order, as a document the platform can resume.

``certificate_generations.order_state`` is the only place an attempt's working
material lives between worker invocations, and this module owns its shape. Two
things about it are deliberate and worth stating before the code:

**It holds public ACME data and nothing else.** Order and challenge URLs, the
authorization and challenge URLs, an ACME token, the key authorization, the TXT
record name and value, the provider's record reference, cleanup status and
timestamps. Every one of those is either public by construction (the TXT value is
*published in DNS*, the token is handed to the CA in the clear) or an opaque
provider handle. None of them can carry the ACME account key, a DNS credential or a
certificate private key — none of those is a field a writer here can set, and
:func:`public_view` is the allowlist that decides what an operator sees, so a field
added by a future writer does not become visible by default.

**It is the crash-recovery contract.** A worker that dies mid-attempt leaves a
generation in ``ORDERING``/``CHALLENGE_PUBLISHED``/``VALIDATING``; the sweep
(:mod:`app.tasks.certificates`) reads this document to decide what has to be
undone (a TXT record this platform created and must delete) and what may simply be
resumed (an order that is still open, a challenge already answered). That is why
the record *reference* is kept rather than the record name: cleanup deletes the one
record this platform made, never "the TXT record at that name"
(phase5-design.md §5.3, §5.5).

The document is versioned and read defensively. A missing, empty or malformed
document is not an error — it is the state of a generation that has not been
ordered yet — but a *partially* readable one is never guessed at: fields that fail
their shape check are dropped rather than coerced, because a wrong field here could
mean deleting the wrong DNS record.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from app.services.acme import AcmeChallenge

#: Bumped when the document's shape changes incompatibly. Read through
#: :func:`load`, which reports an unknown version rather than misreading it.
DOCUMENT_VERSION = 1

#: Who publishes the challenge. Persisted per challenge rather than per
#: generation, because the two are genuinely different facts: an automated
#: challenge has a provider record reference and an automated cleanup path, a
#: manual one has neither, and a retry must not "clean up" a record the operator
#: published by hand (phase5-design.md §5.3). This slice records ``automated``
#: challenges only — the operator-facing manual publication flow is a later slice,
#: and the mode exists here so that adding it cannot retroactively change how an
#: existing challenge's record must be cleaned up.
MODE_AUTOMATED = "automated"
MODE_MANUAL = "manual"

#: Cleanup lifecycle of one published record.
CLEANUP_NOT_REQUIRED = "not_required"
CLEANUP_PENDING = "pending"
CLEANUP_DONE = "done"
#: The provider could not confirm the record is gone. Reported truthfully, never
#: as success: "we could not tell" is not "it is not there".
CLEANUP_UNRESOLVED = "unresolved"

#: Bound on how many challenges one document records. Matches the identifier
#: bound on ``certificates.sans``; a bound rather than a policy, so a hand-written
#: or future document cannot turn a JSONB column into a storage amplifier.
MAX_RECORDED_CHALLENGES = 100

#: Bound on stored free text (the sanitized per-challenge error).
MAX_TEXT = 300

#: Length of a challenge's opaque public reference.
REF_LENGTH = 16

_KNOWN_CLEANUP_STATES = frozenset(
    {CLEANUP_NOT_REQUIRED, CLEANUP_PENDING, CLEANUP_DONE, CLEANUP_UNRESOLVED}
)


def _utcnow() -> datetime:
    return datetime.now(UTC)


def challenge_ref(challenge_url: str) -> str:
    """A stable, opaque public reference for one challenge.

    Derived from the challenge URL rather than stored, so it is the same value on
    every read and an operator's confirmation cannot land on a different challenge
    than the one they were shown. Opaque rather than the URL itself: the URL is a
    public ACME resource but it is long, and a path parameter is a poor place for
    it. Not a secret in any direction — it names a challenge anybody who could read
    the order could already see.
    """
    return hashlib.sha256(challenge_url.encode("utf-8")).hexdigest()[:REF_LENGTH]


def _text(value: Any, *, limit: int = MAX_TEXT) -> str:
    """A bounded string from a stored value, or ``""`` when it is not one."""
    if value is None:
        return ""
    if not isinstance(value, str):
        return ""
    return value[:limit]


def _timestamp(value: Any) -> str:
    """An ISO-8601 string from a stored value, or ``""`` when it is not one."""
    return _text(value)


def _instant(value: Any) -> datetime | None:
    """Parse a stored timestamp, tolerating anything that is not one."""
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)


def now_iso() -> str:
    """The write stamp every field in this document uses."""
    return _utcnow().isoformat()


# --- reading -------------------------------------------------------------------


def load(generation: Any) -> dict[str, Any]:
    """The generation's order document, or an empty one. **Never raises.**

    A malformed value is treated as "nothing has been ordered yet" rather than as
    corrupt progress, because the two are not distinguishable from the outside and
    the caller acts on the fields it needs, each of which is shape-checked again
    where it is used. The version is reported, not enforced here; the flow refuses
    an unknown version where it matters.
    """
    raw = getattr(generation, "order_state", None)
    if not isinstance(raw, dict):
        return {"version": DOCUMENT_VERSION}
    document = dict(raw)
    challenges = document.get("challenges")
    if not isinstance(challenges, list):
        document["challenges"] = []
    else:
        document["challenges"] = [entry for entry in challenges if isinstance(entry, dict)]
    return document


def store(generation: Any, document: dict[str, Any]) -> dict[str, Any]:
    """Write *document* back onto the generation and return what was written.

    A JSON-safe shallow copy with the bounded challenge list applied: the caller
    keeps mutating its own view, and what lands in the column is exactly what
    :func:`entries` will return on the next read.
    """
    sanitized = dict(document)
    sanitized["version"] = DOCUMENT_VERSION
    sanitized["challenges"] = entries(document)[:MAX_RECORDED_CHALLENGES]
    generation.order_state = sanitized
    return sanitized


def entries(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Every challenge entry in *document*, in order, shape-checked.

    A challenge URL has to be a non-empty string: every reader derives a reference,
    a comparison key or a cleanup target from it, so a hand-edited number or list
    in that position is dropped rather than coerced into one.
    """
    raw = document.get("challenges")
    if not isinstance(raw, list):
        return []
    return [
        entry
        for entry in raw
        if isinstance(entry, dict)
        and isinstance(entry.get("challenge_url"), str)
        and entry["challenge_url"]
    ]


def version(document: dict[str, Any]) -> int:
    """The document's version, defaulting to the current one when unreadable."""
    raw = document.get("version")
    return raw if isinstance(raw, int) else DOCUMENT_VERSION


# --- writing -------------------------------------------------------------------


def set_order(
    document: dict[str, Any],
    *,
    directory_url: str,
    order_url: str,
    mode: str,
    expires_at: datetime | None = None,
    txt_ttl: int = 0,
) -> dict[str, Any]:
    """Record the order this attempt is working on. Called before any challenge.

    Once per *order*, which is once per attempt: an attempt that cannot resume the
    order it lost the CSR for re-orders (:mod:`app.services.certificate_issuance`),
    and the fields describing the order — its URL, its expiry and ``started_at`` —
    are then the new order's. ``started_at`` is refreshed rather than preserved for
    that reason: it answers "when was the order recorded here created", and a stale
    answer would age an order that was just placed.
    """
    document["version"] = DOCUMENT_VERSION
    document["directory_url"] = directory_url
    document["order_url"] = order_url
    document["mode"] = MODE_MANUAL if mode == MODE_MANUAL else MODE_AUTOMATED
    document["txt_ttl"] = int(txt_ttl)
    document["started_at"] = now_iso()
    if expires_at is not None:
        document["order_expires_at"] = expires_at.isoformat()
    return document


def record_challenges(
    document: dict[str, Any],
    challenges: tuple[AcmeChallenge, ...] | list[AcmeChallenge],
    *,
    mode: str,
    order_url: str,
) -> dict[str, Any]:
    """Append one entry per challenge, preserving any already recorded.

    Keyed by challenge URL: re-reading the same order (an attempt that resumed after
    a crash, or a retry that found its order still open) must not reset the record
    reference or the cleanup state of a challenge it already published, because that
    is exactly the information cleanup needs.

    ``order_url`` is stored per entry because an attempt may place a second order
    while the first order's records are still awaiting cleanup. Without it, "the
    challenges of the order this attempt is working on" is not answerable — and a
    propagation check that included a *replaced* order's value would wait for a value
    nothing will ever publish (see :func:`current_entries`).
    """
    entry_mode = MODE_MANUAL if mode == MODE_MANUAL else MODE_AUTOMATED
    entry_order_url = _text(order_url, limit=512)
    existing = {entry.get("challenge_url"): entry for entry in entries(document)}
    for challenge in challenges:
        if challenge.challenge_url in existing:
            continue
        existing[challenge.challenge_url] = {
            "ref": challenge_ref(challenge.challenge_url),
            "order_url": entry_order_url,
            "identifier": _text(challenge.identifier, limit=253),
            "wildcard": bool(challenge.wildcard),
            "authorization_url": _text(challenge.authorization_url, limit=512),
            "challenge_url": _text(challenge.challenge_url, limit=512),
            "token": _text(challenge.token),
            "record_name": _text(challenge.record_name, limit=253),
            "record_value": _text(challenge.record_value, limit=512),
            "key_authorization": _text(challenge.key_authorization, limit=512),
            "mode": entry_mode,
            # The provider-side reference to the one record this platform created.
            # Present from the start (empty) rather than added on first publish,
            # because :func:`update_challenge` only writes fields an entry already
            # has — that is what stops a caller from turning this column into a
            # second, untyped record, and it means the reference has to be declared
            # here or it could never be written at all.
            "record_id": "",
            "zone_id": "",
            # Which credential published it, so cleanup uses the same one even if
            # the certificate was rebound to another credential in between.
            "provider_id": "",
            # Cleanup is only ever owed for a record *this platform* created.
            "cleanup": CLEANUP_NOT_REQUIRED if entry_mode == MODE_MANUAL else CLEANUP_PENDING,
            "cleanup_attempts": 0,
            "cleanup_error": "",
            "published_at": "",
            "confirmed_at": "",
            "validated_at": "",
            "error": "",
        }
    document["version"] = DOCUMENT_VERSION
    document["challenges"] = list(existing.values())[:MAX_RECORDED_CHALLENGES]
    return document


def reset_challenges(document: dict[str, Any]) -> dict[str, Any]:
    """Forget the previous order's challenges, for a *new* order on the generation.

    What is dropped is what can be dropped safely: an entry that never referenced a
    provider record (nothing was created, so nothing is owed) and an entry whose
    cleanup is settled. What is **kept** is an entry that still names a record this
    platform created and has not confirmed gone — pending or unresolved — because
    that entry is the only remaining pointer to a TXT record in a customer's zone,
    and losing it is how an orphaned challenge record stays there forever. Those
    survivors are carried into the next attempt, which cleans them up as its first
    act (:meth:`app.services.certificate_issuance._cleanup_records`).

    The reason a fresh order replaces rather than appends is bounded accumulation:
    an attempt cannot resume an order it lost the CSR for (see
    :mod:`app.services.certificate_issuance`), so it re-orders — and appending each
    order's challenges would let one generation accumulate ``attempt budget`` times
    ``identifiers`` entries at the same handful of record names. Survivors are placed
    first so that the bound in :func:`store` truncates *new* entries before it can
    truncate a record reference.
    """
    survivors = [
        entry
        for entry in entries(document)
        if entry.get("record_id") and entry.get("cleanup") in (CLEANUP_PENDING, CLEANUP_UNRESOLVED)
    ]
    document["challenges"] = survivors
    return document


def begin_attempt(document: dict[str, Any]) -> dict[str, Any]:
    """Mark an attempt as *running*, so a duplicate dispatch can be recognized.

    A live state (``ORDERING`` … ``VALIDATING``) says a generation has an open
    order; it does not say a worker is currently working on it. Those are different
    facts and the flow needs both: a generation left in ``CHALLENGE_PUBLISHED`` by a
    worker that died still has an open order, and a duplicate dispatch of it must be
    told apart from one arriving while the attempt is genuinely running. This pair
    is what makes "an attempt is in flight" answerable, and the sweep turns it into
    "an attempt whose worker died" by ageing it against the order TTL.
    """
    document["attempt_started_at"] = now_iso()
    document["attempt_finished_at"] = ""
    return document


def finish_attempt(document: dict[str, Any]) -> dict[str, Any]:
    """Mark the attempt as no longer running, whatever its outcome."""
    document["attempt_finished_at"] = now_iso()
    return document


def attempt_in_flight(
    document: dict[str, Any], *, now: datetime | None = None, ttl_seconds: float = 0.0
) -> bool:
    """Whether an attempt is running *and* recent enough to still be running.

    ``ttl_seconds`` turns this into the sweep's abandoned-attempt predicate: an
    attempt that started longer ago than the order TTL is one whose worker died,
    and reporting it as in flight would make the recovery path unreachable.
    """
    started = _instant(document.get("attempt_started_at"))
    if started is None or _text(document.get("attempt_finished_at")):
        return False
    if ttl_seconds <= 0:
        return True
    return ((now or _utcnow()) - started).total_seconds() < ttl_seconds


def update_challenge(document: dict[str, Any], ref: str, **fields: Any) -> dict[str, Any] | None:
    """Set fields on the challenge named by *ref*, and return the updated entry.

    Only the fields this module writes are accepted: an unknown key is dropped
    rather than stored, so a caller cannot turn the column into a second, untyped
    record. ``cleanup`` is validated against the closed set for the same reason.
    """
    for entry in entries(document):
        if entry.get("ref") != ref:
            continue
        for key, value in fields.items():
            if key not in entry:
                continue
            if key == "cleanup":
                entry[key] = value if value in _KNOWN_CLEANUP_STATES else CLEANUP_PENDING
            elif key in {"cleanup_attempts"}:
                entry[key] = int(value or 0)
            elif key == "cleanup_error":
                entry[key] = _text(value)
            else:
                entry[key] = _text(value)
        return entry
    return None


def challenge(document: dict[str, Any], ref: str) -> dict[str, Any] | None:
    """The entry named by *ref*, or ``None`` when no challenge has it."""
    for entry in entries(document):
        if entry.get("ref") == ref:
            return entry
    return None


def current_entries(document: dict[str, Any]) -> list[dict[str, Any]]:
    """The challenges belonging to the order this document currently records.

    Entries from a replaced order may still be present (they are kept until their
    records are confirmed deleted, see :func:`reset_challenges`), and they must not
    be confused with the live order's: their values are no longer published and
    waiting for them would wait out the whole propagation deadline for nothing.
    """
    order_url = _text(document.get("order_url"), limit=512)
    if not order_url:
        return []
    return [entry for entry in entries(document) if entry.get("order_url") == order_url]


def pending_publication(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Current-order challenges whose TXT record is not published or confirmed yet."""
    return [entry for entry in current_entries(document) if not entry.get("published_at")]


def manual_pending(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Manual challenges an operator has not yet confirmed publishing."""
    return [
        entry
        for entry in entries(document)
        if entry.get("mode") == MODE_MANUAL and not entry.get("confirmed_at")
    ]


def pending_cleanup(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Challenges whose record this platform created and has not confirmed gone.

    ``unresolved`` is included on purpose: a record the provider could not confirm
    deleted is still a record to try to delete, and excluding it would make cleanup
    give up after one bad minute.
    """
    return [
        entry
        for entry in entries(document)
        if entry.get("cleanup") in (CLEANUP_PENDING, CLEANUP_UNRESOLVED) and entry.get("record_id")
    ]


def cleanup_incomplete(document: dict[str, Any]) -> list[dict[str, Any]]:
    """Records this platform published and still cannot confirm are gone."""
    return [
        entry
        for entry in entries(document)
        if entry.get("cleanup") == CLEANUP_UNRESOLVED and entry.get("record_id")
    ]


def manual_instructions(document: dict[str, Any]) -> list[dict[str, Any]]:
    """What the operator has to publish by hand. Public data only.

    The record name and the TXT value, because that is the instruction, plus the
    challenge reference they quote back. The wildcard flag is included because the
    two authorizations of an apex+wildcard order share a record name and differ
    only in that value — an operator publishing "the" record would otherwise
    overwrite one with the other.
    """
    return [
        {
            "ref": _text(entry.get("ref")),
            "identifier": _text(entry.get("identifier")),
            "wildcard": bool(entry.get("wildcard")),
            "record_name": _text(entry.get("record_name")),
            "record_value": _text(entry.get("record_value")),
            "confirmed": bool(entry.get("confirmed_at")),
            "validated": bool(entry.get("validated_at")),
        }
        for entry in entries(document)
        if entry.get("mode") == MODE_MANUAL
    ]


def public_view(document: dict[str, Any]) -> dict[str, Any]:
    """The operator-facing projection of the document. **An allowlist.**

    Built field by field rather than by deleting keys from a copy, so a writer that
    starts storing something new cannot make it visible here by accident. Nothing
    omitted from this function is needed to *act* on a challenge; what is omitted is
    the internal bookkeeping (key authorizations, retry counters, provider handles).
    """
    return {
        "version": version(document),
        "mode": MODE_MANUAL if document.get("mode") == MODE_MANUAL else MODE_AUTOMATED,
        "order_url": _text(document.get("order_url"), limit=512),
        "order_expires_at": _timestamp(document.get("order_expires_at")),
        "started_at": _timestamp(document.get("started_at")),
        "finalized_at": _timestamp(document.get("finalized_at")),
        "challenges": [
            {
                "ref": _text(entry.get("ref")),
                "identifier": _text(entry.get("identifier")),
                "wildcard": bool(entry.get("wildcard")),
                "record_name": _text(entry.get("record_name")),
                "record_value": _text(entry.get("record_value")),
                "mode": (MODE_MANUAL if entry.get("mode") == MODE_MANUAL else MODE_AUTOMATED),
                "published": bool(entry.get("published_at")),
                "confirmed_at": _timestamp(entry.get("confirmed_at")),
                "validated_at": _timestamp(entry.get("validated_at")),
                "cleanup": _text(entry.get("cleanup"), limit=16) or CLEANUP_PENDING,
                "error": _text(entry.get("error")),
            }
            for entry in entries(document)
        ],
    }


def started_at(document: dict[str, Any], *, fallback: datetime) -> datetime:
    """When this attempt's order was created, or *fallback* when it says nothing.

    Used by the stuck-state sweep: a generation in a live state whose order is
    older than the TTL is one whose worker died, and the age has to come from
    somewhere. The row's own ``updated_at`` is the fallback rather than "now",
    because "now" would make every recovered generation look fresh.
    """
    return _instant(document.get("started_at")) or fallback


__all__ = [
    "CLEANUP_DONE",
    "CLEANUP_NOT_REQUIRED",
    "CLEANUP_PENDING",
    "CLEANUP_UNRESOLVED",
    "DOCUMENT_VERSION",
    "MAX_RECORDED_CHALLENGES",
    "MODE_AUTOMATED",
    "MODE_MANUAL",
    "attempt_in_flight",
    "begin_attempt",
    "challenge",
    "challenge_ref",
    "cleanup_incomplete",
    "current_entries",
    "entries",
    "finish_attempt",
    "load",
    "manual_instructions",
    "manual_pending",
    "now_iso",
    "pending_cleanup",
    "pending_publication",
    "public_view",
    "record_challenges",
    "reset_challenges",
    "set_order",
    "started_at",
    "store",
    "update_challenge",
    "version",
]
