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
from typing import Any, Protocol

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
class ServerAnswer:
    """What **one** authoritative server said, kept separately from the rest.

    ``values`` is the whole TXT set that server returned, not only the value the
    caller was looking for: a stale server that still holds an older value is a
    different fact from one that holds nothing, and a caller deciding whether a
    record has propagated needs to distinguish them without re-querying.
    """

    #: The address that was queried (DNS has no port to report: always 53).
    server: str
    status: str
    values: tuple[str, ...] = ()

    @property
    def answered(self) -> bool:
        """Whether this server gave an authoritative answer about the name."""
        return self.status in (STATUS_OK, STATUS_NXDOMAIN, STATUS_NO_TXT)


@dataclass(frozen=True, slots=True)
class TxtObservation:
    """One bounded look at a name's authoritative TXT record.

    ``values`` is the **union** of what the servers returned, which is what an
    existence check needs. A caller that must not act on a partial view — the ACME
    propagation check — reads :attr:`server_answers` instead, so one positive answer
    cannot hide another server still serving nothing.
    """

    status: str
    values: tuple[str, ...] = ()
    #: Sorted, lowercased, trailing-dot-stripped apex NS set as observed.
    nameservers: tuple[str, ...] = ()
    detail: str = ""
    #: One entry per authoritative address that was asked, in query order. Empty
    #: when the observation was built from an aggregate answer (a test seam, the
    #: ownership verifier's single-answer path) rather than from the wire.
    server_answers: tuple[ServerAnswer, ...] = ()

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


def observe_txt_record(
    name: str, *, budget: float = DNS_TOTAL_BUDGET, resolver: Any | None = None
) -> TxtObservation:
    """Query *name*'s authoritative servers for its TXT records (the DNS-01 half).

    :func:`observe` answers "does this apex still prove ownership of a domain";
    this answers "is the value the CA is about to look for actually being
    served", for an arbitrary owner name — ``_acme-challenge.www.example.com``.
    Three differences from :func:`observe`, all deliberate:

    * the owner name is used **as given**: no ``_nexusops`` prefix and no
      :func:`~app.core.dnsname.apex_of`, because the name comes from the CA's
      challenge rather than from this platform's own convention;
    * the authoritative nameservers are discovered by walking the name's labels
      from the right (:func:`discover_authoritative_nameservers`) instead of
      resolving the apex, because the zone a challenge record lives in is a
      property of the customer's delegation and not something to guess;
    * the result is what the **authoritative** servers say, never a recursive
      cache — a caching resolver returning a stale negative answer is exactly the
      answer that must not be trusted before telling a CA "ready" (nor before
      telling an operator their record is missing).

    Errors are observations here too: missing records, NXDOMAIN, timeouts and
    SERVFAIL are statuses, so the caller decides whether to keep polling.

    *resolver* is the **bootstrap** resolver — the one that answers "who is
    authoritative for this name" and "what address is that nameserver". It plays
    the role ``/etc/resolv.conf`` plays in a deployment, and it never answers the
    question that matters: the TXT values always come from a direct query to the
    authoritative server. None means the system resolver. A caller may supply one
    when its deployment's delegation view is not the host's (split-horizon DNS),
    and the isolated Pebble test does exactly that rather than editing the host's
    resolver configuration.
    """
    import dns.exception
    import dns.resolver

    started = time.monotonic()

    def _remaining() -> float:
        return budget - (time.monotonic() - started)

    try:
        nameservers = discover_authoritative_nameservers(
            name, timeout=min(DNS_QUERY_TIMEOUT, max(_remaining(), 0.5)), resolver=resolver
        )
    except dns.exception.Timeout:
        return TxtObservation(STATUS_TIMEOUT, detail="timed out discovering nameservers")
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers):
        return TxtObservation(
            STATUS_NO_NAMESERVERS,
            detail="no authoritative nameserver was found for this record name",
        )
    except Exception as exc:  # resolver misconfiguration, no nameservers configured
        log.warning("dns_ns_lookup_failed", name=name, error=exc.__class__.__name__)
        return TxtObservation(STATUS_ERROR, detail="the nameserver lookup failed")

    if not nameservers:
        return TxtObservation(
            STATUS_NO_NAMESERVERS,
            detail="no authoritative nameserver was found for this record name",
        )

    addresses = _resolve_addresses(
        nameservers[:MAX_NAMESERVERS], budget=budget, started=started, resolver=resolver
    )
    if not addresses:
        return TxtObservation(
            STATUS_NO_NAMESERVERS,
            nameservers=_normalise_ns(nameservers),
            detail="the authoritative nameservers have no resolvable addresses",
        )

    # Every server, not the first positive one: a zone whose servers disagree is
    # the state in which telling a CA "ready" is wrong, and only a complete view
    # can see it (see app.services.dns_propagation).
    status, values, detail, answers = _query_txt_all(name, addresses, budget=max(_remaining(), 0.5))
    return TxtObservation(
        status,
        values=tuple(values[:MAX_TXT_VALUES]),
        nameservers=_normalise_ns(nameservers),
        detail=detail,
        server_answers=tuple(answers),
    )


def discover_authoritative_nameservers(
    name: str, *, timeout: float, resolver: Any | None = None
) -> list[str]:
    """The nameservers authoritative for *name*, found by walking its labels.

    A public-suffix list is deliberately not used. The question is not "which
    zone does this name belong to" but "who answers for it", and the delegation
    chain answers exactly that: querying ``NS`` at a name that is not a zone cut
    returns NODATA (RFC 1034 §4.2.1), so the first suffix that *does* answer is
    the zone cut whose servers hold this name's records. That is also the case a
    suffix-list guess gets wrong — a subdomain delegated to a different provider
    answers first here, which is the correct delegation for the challenge record.

    Only labels below the TLD are tried (``a.b.example.com`` → ``a.b.example.com``,
    ``b.example.com``, ``example.com``): the TLD's own servers do not hold the
    record, and answering with them would make a missing record look like a
    nameserver for the wrong zone.
    """
    import dns.exception
    import dns.resolver

    candidate = (name or "").strip().rstrip(".").lower()
    labels = [label for label in candidate.split(".") if label]
    if len(labels) < 2:
        return []

    resolver = resolver or dns.resolver.Resolver(configure=True)
    labels = labels[1:]  # never query the TLD itself
    for start in range(len(labels)):
        suffix = ".".join(labels[start:])
        try:
            answer = resolver.resolve(suffix, "NS", lifetime=max(timeout, 0.5))
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
            continue
        except dns.exception.Timeout:
            continue
        advertised = [str(record.target).rstrip(".") for record in answer]
        if advertised:
            return advertised
    return []


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


def _resolve_addresses(
    nameservers: list[str], *, budget: float, started: float, resolver: Any | None = None
) -> list[str]:
    """Resolve NS hostnames to addresses, glue or not.

    A nameserver name that resolves to nothing is skipped rather than failing the
    whole observation: one dead NS out of four must not block verification.
    """
    import dns.resolver

    resolver = resolver or dns.resolver.Resolver(configure=True)
    addresses: list[str] = []
    for ns_name in nameservers:
        remaining = budget - (time.monotonic() - started)
        if remaining <= 0.5:
            break
        for record_type in ("A", "AAAA"):
            try:
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


def _ask_one(qname: str, address: str, *, budget: float) -> tuple[str, list[str], str]:
    """One authoritative server's answer for *qname*'s TXT records.

    Never raises for a DNS condition: a timeout, a SERVFAIL, a non-zero rcode and a
    malformed TXT all come back as statuses, because each one is a fact the caller
    may have to report.
    """
    import dns.message
    import dns.query
    import dns.rcode
    import dns.rdatatype
    import dns.resolver

    query = dns.message.make_query(qname, dns.rdatatype.TXT, want_dnssec=False)
    timeout = min(budget, DNS_QUERY_TIMEOUT)
    answer = None
    last_status = STATUS_TIMEOUT
    last_detail = "no authoritative server answered in time"
    for attempt in ("udp", "tcp"):
        try:
            if attempt == "udp":
                answer = dns.query.udp(query, address, timeout=timeout)
            else:
                answer = dns.query.tcp(query, address, timeout=timeout)
            break
        except dns.exception.Timeout:
            last_status, last_detail = STATUS_TIMEOUT, "an authoritative server timed out"
            continue
        except (OSError, dns.exception.DNSException) as exc:
            last_status = STATUS_ERROR
            last_detail = f"the authoritative query failed ({exc.__class__.__name__})"
            continue
    if answer is None:
        return last_status, [], last_detail

    rcode = answer.rcode()
    if rcode == dns.rcode.NXDOMAIN:
        return STATUS_NXDOMAIN, [], "the record name does not exist"
    if rcode == dns.rcode.SERVFAIL:
        return STATUS_SERVFAIL, [], "an authoritative server returned SERVFAIL"
    if rcode != dns.rcode.NOERROR:
        return (
            STATUS_ERROR,
            [],
            f"an authoritative server returned rcode {dns.rcode.to_text(rcode)}",
        )
    values: list[str] = []
    for rrset in answer.answer:
        if rrset.rdtype != dns.rdatatype.TXT:
            continue
        for rdata in rrset:
            try:
                values.append(b"".join(rdata.strings).decode("utf-8", "replace"))
            except (AttributeError, TypeError):
                return STATUS_MALFORMED, [], "an authoritative server sent a malformed TXT record"
    if not values:
        return STATUS_NO_TXT, [], "no TXT record at the verification name"
    return STATUS_OK, values, ""


def _query_txt(qname: str, addresses: list[str], *, budget: float) -> tuple[str, list[str], str]:
    """Ask each authoritative address in turn, stopping at the first positive one.

    This is the **ownership** question ("does an authoritative server still serve
    this apex's proof token"), for which one truthful positive answer is enough. It
    is deliberately not the ACME readiness question: see :func:`_query_txt_all`.
    """
    started = time.monotonic()
    last_status = STATUS_TIMEOUT
    last_detail = "no authoritative server answered in time"
    saw_authoritative_nxdomain = False
    saw_authoritative_no_txt = False

    for address in addresses:
        remaining = budget - (time.monotonic() - started)
        if remaining <= 0.5:
            break
        status, values, detail = _ask_one(qname, address, budget=remaining)
        if status == STATUS_OK:
            return STATUS_OK, values, ""
        if status == STATUS_NXDOMAIN:
            saw_authoritative_nxdomain = True
        elif status == STATUS_NO_TXT:
            saw_authoritative_no_txt = True
        last_status, last_detail = status, detail

    if saw_authoritative_nxdomain and not saw_authoritative_no_txt:
        return STATUS_NXDOMAIN, [], "the record name does not exist"
    return last_status, [], last_detail


def _query_txt_all(
    qname: str, addresses: list[str], *, budget: float
) -> tuple[str, list[str], str, list[ServerAnswer]]:
    """Ask **every** authoritative address, even after a positive answer.

    The difference from :func:`_query_txt` is the whole point of this function: an
    authoritative set that disagrees with itself is exactly the state in which a
    CA must not yet be told the challenge is ready, and it is invisible to a loop
    that stops at the first positive response. Each server's answer is kept, so
    the callers can require agreement instead of inferring it from a union.
    """
    started = time.monotonic()
    answers: list[ServerAnswer] = []
    for address in addresses:
        remaining = budget - (time.monotonic() - started)
        if remaining <= 0.5:
            # Out of budget: the server was not observed, which is recorded as a
            # timeout rather than silently dropped or counted as agreement.
            answers.append(ServerAnswer(address, STATUS_TIMEOUT, ()))
            continue
        status, values, _detail = _ask_one(qname, address, budget=remaining)
        answers.append(ServerAnswer(address, status, tuple(values)))
    status, values, detail = _aggregate_answers(answers)
    return status, values, detail, answers


def _aggregate_answers(answers: list[ServerAnswer]) -> tuple[str, list[str], str]:
    """Fold per-server answers into one status and the union of their values.

    The union is what an existence check wants; it is *not* evidence of agreement,
    which is why :class:`TxtObservation` keeps the per-server list as well.
    """
    if not answers:
        return STATUS_TIMEOUT, [], "no authoritative server was asked"

    values: list[str] = []
    for answer in answers:
        if answer.status != STATUS_OK:
            continue
        for value in answer.values:
            if value not in values:
                values.append(value)
    if any(answer.status == STATUS_OK and answer.values for answer in answers):
        silent = sum(1 for answer in answers if not answer.answered)
        detail = (
            f"{silent} of {len(answers)} authoritative servers did not answer" if silent else ""
        )
        return STATUS_OK, values, detail
    if any(answer.status == STATUS_NXDOMAIN for answer in answers) and not any(
        answer.status == STATUS_NO_TXT for answer in answers
    ):
        return STATUS_NXDOMAIN, [], "the record name does not exist"
    if any(answer.status == STATUS_NO_TXT for answer in answers):
        return STATUS_NO_TXT, [], "no TXT record at the verification name"
    for status, detail in (
        (STATUS_TIMEOUT, "no authoritative server answered in time"),
        (STATUS_SERVFAIL, "an authoritative server returned SERVFAIL"),
        (STATUS_MALFORMED, "an authoritative server sent a malformed TXT record"),
    ):
        if any(answer.status == status for answer in answers):
            return status, [], detail
    return STATUS_ERROR, [], "the authoritative query failed"
