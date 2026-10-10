"""Authoritative DNS observation for domain-ownership verification.

Two halves, deliberately separated:

* :func:`observe` — the only I/O. It discovers the name's **authoritative**
  nameservers and asks *them* for the proof TXT record, with bounded timeouts.
  A recursive caching resolver is used only to bootstrap the delegation (which
  nameservers are authoritative, and their addresses); it never answers the
  ownership question, because a cached positive answer would defeat the point of
  re-proving control.
* :func:`decide` — pure. Given an observation, the expected token and the stored
  NS snapshot it returns what the control plane should do. All the interesting
  anti-takeover logic lives here so it is testable without a network.

Errors are classified, never raised at the API boundary: missing TXT,
NXDOMAIN, timeout, SERVFAIL, missing nameservers and malformed responses are all
*observations* that the lifecycle turns into states.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Protocol

from app.core.dnsname import apex_of, verification_record_name
from app.core.logging import get_logger

log = get_logger("nexusops.dns")

#: Per-server query timeout, and the whole-observation budget. Both are small on
#: purpose: verification runs in a worker, and an unresponsive authoritative
#: server must not hold a task open for minutes.
DNS_QUERY_TIMEOUT = 3.0
DNS_TOTAL_BUDGET = 12.0
#: How many authoritative servers one observation may try.
MAX_NAMESERVERS = 8
#: Cap on how many TXT values one response may contribute (a zone can legally
#: hold many; we only ever look for one, and must not buffer unbounded data).
MAX_TXT_VALUES = 40

#: Observation statuses. ``OK`` means "authoritative servers answered"; it says
#: nothing about whether the token matched.
STATUS_OK = "OK"
STATUS_NO_NAMESERVERS = "NO_NAMESERVERS"
STATUS_NXDOMAIN = "NXDOMAIN"
STATUS_NO_TXT = "NO_TXT"
STATUS_TIMEOUT = "TIMEOUT"
STATUS_SERVFAIL = "SERVFAIL"
STATUS_MALFORMED = "MALFORMED"
STATUS_ERROR = "ERROR"

#: Decision reasons, mapped onto Domain status transitions by the lifecycle.
REASON_VERIFIED = "TXT_MATCH"
REASON_TXT_MISSING = "TXT_MISSING"
REASON_TXT_MISMATCH = "TXT_MISMATCH"
REASON_NS_CHANGED = "NS_CHANGED"
REASON_DNS_UNAVAILABLE = "DNS_UNAVAILABLE"
REASON_NO_NAMESERVERS = "NO_AUTHORITATIVE_NS"


@dataclass(frozen=True, slots=True)
class TxtObservation:
    """One bounded look at a name's authoritative TXT record."""

    status: str
    values: tuple[str, ...] = ()
    #: Sorted, lowercased, trailing-dot-stripped apex NS set as observed.
    nameservers: tuple[str, ...] = ()
    detail: str = ""

    @property
    def authoritative(self) -> bool:
        return self.status in (STATUS_OK, STATUS_NXDOMAIN, STATUS_NO_TXT)


@dataclass(frozen=True, slots=True)
class VerificationDecision:
    """What the lifecycle should do with an observation."""

    ok: bool
    reason: str
    detail: str
    #: The NS set to store when the verification succeeds.
    ns_snapshot: tuple[str, ...]
    #: True when a previously-stored snapshot disagrees with what is observed.
    ns_changed: bool


class Observer(Protocol):
    """The seam tests replace with a mock authoritative DNS."""

    def __call__(self, name: str) -> TxtObservation: ...


def _normalise_ns(names: list[str] | tuple[str, ...]) -> tuple[str, ...]:
    cleaned = {str(n).strip().rstrip(".").lower() for n in names if str(n).strip()}
    return tuple(sorted(cleaned))


def matches_token(values: tuple[str, ...], expected: str) -> bool:
    """Constant-time comparison of the observed TXT values against the token.

    TXT records may carry several strings; nginx-style multiple values are
    compared individually. ``compare_digest`` avoids turning the comparison into
    a timing oracle for a token an attacker can guess at.
    """
    import secrets

    for value in values:
        if not isinstance(value, str):
            continue
        if expected and secrets.compare_digest(value.strip(), expected):
            return True
    return False


def decide(
    observation: TxtObservation,
    *,
    expected_token: str,
    ns_snapshot: tuple[str, ...] | list[str],
    require_snapshot_match: bool,
) -> VerificationDecision:
    """Turn one observation into the verification outcome — pure, no I/O.

    ``require_snapshot_match`` is what distinguishes the two callers:

    * a **sweep** re-checking an already-verified name sets it: a changed
      delegation means the name may have changed hands, so the proof is stale
      even if the TXT record is still there;
    * a **user-requested verification** clears it: the user is deliberately
      re-proving control, and a legitimate re-delegation must be able to
      re-verify without being permanently pinned to a dead NS set.
    """
    snapshot = _normalise_ns(list(ns_snapshot))
    # Both sides are normalised here, not only the stored one: ``observe`` already
    # returns a canonical set, but this function is the safety-critical decision
    # and must not depend on its caller having normalised anything.
    observed = _normalise_ns(list(observation.nameservers))
    ns_changed = bool(snapshot) and observed != snapshot

    if observation.status == STATUS_NO_NAMESERVERS:
        return VerificationDecision(
            False,
            REASON_NO_NAMESERVERS,
            observation.detail or "no NS records found",
            observed,
            ns_changed,
        )
    if observation.status in (STATUS_TIMEOUT, STATUS_SERVFAIL, STATUS_ERROR):
        return VerificationDecision(
            False,
            REASON_DNS_UNAVAILABLE,
            observation.detail or "the authoritative servers did not answer",
            observed,
            ns_changed,
        )
    if observation.status == STATUS_NXDOMAIN or not observation.values:
        return VerificationDecision(
            False,
            REASON_TXT_MISSING,
            observation.detail or "no TXT record found",
            observed,
            ns_changed,
        )

    if require_snapshot_match and ns_changed:
        return VerificationDecision(
            False,
            REASON_NS_CHANGED,
            "the domain's authoritative nameservers changed; re-verify to confirm control",
            observed,
            True,
        )
    if not matches_token(observation.values, expected_token):
        return VerificationDecision(
            False,
            REASON_TXT_MISMATCH,
            "the TXT record does not match the expected value",
            observed,
            ns_changed,
        )
    return VerificationDecision(True, REASON_VERIFIED, "", observed, ns_changed)


# --- observation (the only I/O) ---------------------------------------------


def observe(name: str, *, budget: float = DNS_TOTAL_BUDGET) -> TxtObservation:
    """Query the name's authoritative servers for ``_nexusops.<apex>`` TXT.

    Never raises for DNS conditions; a broken response is
    :data:`STATUS_MALFORMED` and an unreachable set of servers is
    :data:`STATUS_TIMEOUT`. Only a programming error can escape.
    """
    import dns.exception
    import dns.resolver

    apex = apex_of(name)
    started = time.monotonic()

    def _remaining() -> float:
        return budget - (time.monotonic() - started)

    try:
        nameservers = _discover_nameservers(
            apex, timeout=min(DNS_QUERY_TIMEOUT, max(_remaining(), 0.5))
        )
    except dns.exception.Timeout:
        return TxtObservation(STATUS_TIMEOUT, detail="timed out discovering nameservers")
    except dns.resolver.NXDOMAIN:
        return TxtObservation(STATUS_NO_NAMESERVERS, detail="the domain does not exist in DNS")
    except dns.resolver.NoAnswer:
        return TxtObservation(STATUS_NO_NAMESERVERS, detail="the domain has no NS records")
    except Exception as exc:  # resolver misconfiguration, no nameservers configured
        log.warning("dns_ns_lookup_failed", apex=apex, error=exc.__class__.__name__)
        return TxtObservation(STATUS_ERROR, detail="the nameserver lookup failed")

    if not nameservers:
        return TxtObservation(STATUS_NO_NAMESERVERS, detail="the domain has no NS records")

    addresses = _resolve_addresses(nameservers[:MAX_NAMESERVERS], budget=budget, started=started)
    if not addresses:
        return TxtObservation(
            STATUS_NO_NAMESERVERS,
            nameservers=_normalise_ns(nameservers),
            detail="the authoritative nameservers have no resolvable addresses",
        )

    qname = verification_record_name(name)
    status, values, detail = _query_txt(qname, addresses, budget=max(_remaining(), 0.5))
    return TxtObservation(
        status,
        values=tuple(values[:MAX_TXT_VALUES]),
        nameservers=_normalise_ns(nameservers),
        detail=detail,
    )


def public_addresses(hostname: str, *, budget: float = DNS_QUERY_TIMEOUT) -> list[str]:
    """Best-effort A/AAAA lookup used **only** for the reachability warning.

    This deliberately uses an ordinary recursive resolver: it describes where the
    world currently sends traffic, not who owns the name. Nothing gates on it.
    """
    import dns.resolver

    addresses: list[str] = []
    for record_type in ("A", "AAAA"):
        try:
            resolver = dns.resolver.Resolver(configure=True)
            resolver.lifetime = budget
            resolver.timeout = budget
            answer = resolver.resolve(hostname, record_type, lifetime=budget)
        except Exception as exc:
            # A missing record type is the normal case, not a failure: only one of
            # A/AAAA usually exists, so this stays at debug level.
            log.debug(
                "dns_address_query_failed",
                hostname=hostname,
                record_type=record_type,
                error=str(exc),
            )
            continue
        for record in answer:
            try:
                addresses.append(record.address)
            except AttributeError:  # pragma: no cover - defensive
                continue
    return list(dict.fromkeys(addresses))


def _discover_nameservers(apex: str, *, timeout: float) -> list[str]:
    import dns.resolver

    resolver = dns.resolver.Resolver(configure=True)
    resolver.lifetime = max(timeout, 0.5)
    resolver.timeout = max(timeout, 0.5)
    answer = resolver.resolve(apex, "NS", lifetime=max(timeout, 0.5))
    return [str(record.target).rstrip(".") for record in answer]


def _resolve_addresses(nameservers: list[str], *, budget: float, started: float) -> list[str]:
    """Resolve NS hostnames to addresses, glue or not.

    A nameserver name that resolves to nothing is skipped rather than failing the
    whole observation: one dead NS out of four must not block verification.
    """
    import dns.resolver

    addresses: list[str] = []
    for ns_name in nameservers:
        remaining = budget - (time.monotonic() - started)
        if remaining <= 0.5:
            break
        for record_type in ("A", "AAAA"):
            try:
                resolver = dns.resolver.Resolver(configure=True)
                resolver.lifetime = min(remaining, DNS_QUERY_TIMEOUT)
                resolver.timeout = min(remaining, DNS_QUERY_TIMEOUT)
                answer = resolver.resolve(
                    ns_name, record_type, lifetime=min(remaining, DNS_QUERY_TIMEOUT)
                )
            except Exception as exc:
                # One silent nameserver must not sink the whole observation.
                log.debug(
                    "dns_glue_query_failed",
                    nameserver=ns_name,
                    record_type=record_type,
                    error=str(exc),
                )
                continue
            for record in answer:
                try:
                    addresses.append(record.address)
                except AttributeError:  # pragma: no cover - defensive
                    continue
    # De-duplicate while keeping the deterministic order the resolver gave.
    return list(dict.fromkeys(addresses))


def _query_txt(qname: str, addresses: list[str], *, budget: float) -> tuple[str, list[str], str]:
    """Ask each authoritative address in turn for the TXT record."""
    import dns.message
    import dns.query
    import dns.rcode
    import dns.rdatatype
    import dns.resolver

    started = time.monotonic()
    last_status = STATUS_TIMEOUT
    last_detail = "no authoritative server answered in time"
    saw_authoritative_nxdomain = False
    saw_authoritative_no_txt = False

    for address in addresses:
        remaining = budget - (time.monotonic() - started)
        if remaining <= 0.5:
            break
        query = dns.message.make_query(qname, dns.rdatatype.TXT, want_dnssec=False)
        answer = None
        for attempt in ("udp", "tcp"):
            try:
                if attempt == "udp":
                    answer = dns.query.udp(
                        query, address, timeout=min(remaining, DNS_QUERY_TIMEOUT)
                    )
                else:
                    answer = dns.query.tcp(
                        query, address, timeout=min(remaining, DNS_QUERY_TIMEOUT)
                    )
                break
            except dns.exception.Timeout:
                last_status, last_detail = STATUS_TIMEOUT, "an authoritative server timed out"
                continue
            except (OSError, dns.exception.DNSException) as exc:
                last_status = STATUS_ERROR
                last_detail = f"the authoritative query failed ({exc.__class__.__name__})"
                continue
        if answer is None:
            continue
        rcode = answer.rcode()
        if rcode == dns.rcode.NXDOMAIN:
            saw_authoritative_nxdomain = True
            last_status, last_detail = STATUS_NXDOMAIN, "the record name does not exist"
            continue
        if rcode == dns.rcode.SERVFAIL:
            last_status, last_detail = STATUS_SERVFAIL, "an authoritative server returned SERVFAIL"
            continue
        if rcode != dns.rcode.NOERROR:
            last_status = STATUS_ERROR
            last_detail = f"an authoritative server returned rcode {dns.rcode.to_text(rcode)}"
            continue
        values: list[str] = []
        for rrset in answer.answer:
            if rrset.rdtype != dns.rdatatype.TXT:
                continue
            for rdata in rrset:
                try:
                    values.append(b"".join(rdata.strings).decode("utf-8", "replace"))
                except (AttributeError, TypeError):
                    return (
                        STATUS_MALFORMED,
                        [],
                        "an authoritative server sent a malformed TXT record",
                    )
        if not values:
            saw_authoritative_no_txt = True
            last_status, last_detail = STATUS_NO_TXT, "no TXT record at the verification name"
            continue
        return STATUS_OK, values, ""

    if saw_authoritative_nxdomain and not saw_authoritative_no_txt:
        return STATUS_NXDOMAIN, [], "the record name does not exist"
    return last_status, [], last_detail
