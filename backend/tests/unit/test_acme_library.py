"""Contracts of the production ACME adapter that a fake session cannot check.

Each was only observable against a real CA, and each broke issuance completely
while every fake-session test passed:

* the finalization deadline handed to ``acme`` must be **naive** local time,
  because the library compares it with ``datetime.datetime.now()``;
* an ``acme.messages.Status`` is not a string — ``str(Status("valid"))`` is
  ``"Status(valid)"`` — so every status the adapter stores or compares has to be
  normalised to the plain member name;
* finalization must carry **this attempt's** CSR. An order re-read from the CA (the
  manual DNS-01 resume path) has no CSR, and the library parses the one on the
  order resource — so passing it through unchanged finalized with an empty CSR.

They live here, next to the adapter, so the next change to any seam fails in a
one-second unit test rather than in an integration run against Pebble.
"""

from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from typing import Any

import pytest
from acme import messages
from app.models.enums import AcmeDirectory
from app.services.acme.library import (
    _finalize_deadline,
    _LibrarySession,
    _status_text,
)

CSR_PEM = (
    b"-----BEGIN CERTIFICATE REQUEST-----\nnot-a-real-csr\n-----END CERTIFICATE REQUEST-----\n"
)


def test_finalize_deadline_is_naive() -> None:
    """``acme`` compares the deadline with ``datetime.now()``; aware raises TypeError."""
    deadline = _finalize_deadline(30)
    assert deadline.tzinfo is None
    assert isinstance(deadline, datetime)


def test_finalize_deadline_never_collapses_to_now() -> None:
    """A zero or negative timeout still allows the CA one second to answer."""
    assert (_finalize_deadline(0) - datetime.now()).total_seconds() >= 0.9


class _FinalizingClient:
    """The one client method finalization uses, recording the resource it was given."""

    def __init__(self) -> None:
        self.received: Any = None

    def finalize_order(self, orderr: Any, deadline: datetime) -> Any:
        self.received = orderr
        return SimpleNamespace(fullchain_pem="-----BEGIN CERTIFICATE-----\nleaf\n-----")


def test_finalize_order_sends_this_attempts_csr() -> None:
    """A resumed order has no CSR; finalization still signs the CSR just generated.

    ``acme`` finalizes ``orderr.csr_pem``, and the resource ``resume_order`` reads
    back from the CA carries none — it was created by a previous attempt whose key
    was discarded. Finalizing that resource unchanged raises ``ValueError`` before
    the CA is asked, which made every manual DNS-01 resume fail while the fake CA
    (which accepts any CSR) reported success.
    """
    client = _FinalizingClient()
    session = _LibrarySession(
        AcmeDirectory.PEBBLE, account_key_pem="unused", account_url="https://ca/acct/1"
    )
    session._client = client  # type: ignore[assignment]
    session._key = object()  # type: ignore[assignment]
    session._orderr = messages.OrderResource(
        body=messages.Order(status=messages.STATUS_PENDING, identifiers=[]),
        uri="https://ca/order/9",
        csr_pem=b"",
        authorizations=(),
    )

    chain = session._finalize_order(CSR_PEM, 10)

    assert client.received.csr_pem == CSR_PEM
    assert chain.order_url == "https://ca/order/9"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (messages.Status("valid"), "valid"),
        (messages.Status("pending"), "pending"),
        (messages.STATUS_PENDING, "pending"),
        ("invalid", "invalid"),
        (" Status(invalid) ", "invalid"),
    ],
)
def test_status_text_normalises_acme_status(value: object, expected: str) -> None:
    assert _status_text(value) == expected


def test_status_text_matches_the_wire_vocabulary() -> None:
    """The normalised value is what callers compare against, so it must be plain."""
    assert _status_text(messages.STATUS_PENDING) == "pending"
    assert _status_text(messages.STATUS_PENDING) != messages.STATUS_PENDING
