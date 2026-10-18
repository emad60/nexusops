"""Two contracts of the production ACME adapter that a fake session cannot check.

Both were only observable against a real CA, and both broke issuance completely
while every fake-session test passed:

* the finalization deadline handed to ``acme`` must be **naive** local time,
  because the library compares it with ``datetime.datetime.now()``;
* an ``acme.messages.Status`` is not a string — ``str(Status("valid"))`` is
  ``"Status(valid)"`` — so every status the adapter stores or compares has to be
  normalised to the plain member name.

They live here, next to the adapter, so the next change to either seam fails in a
one-second unit test rather than in an integration run against Pebble.
"""

from __future__ import annotations

from datetime import datetime

import pytest
from acme import messages
from app.services.acme.library import _finalize_deadline, _status_text


def test_finalize_deadline_is_naive() -> None:
    """``acme`` compares the deadline with ``datetime.now()``; aware raises TypeError."""
    deadline = _finalize_deadline(30)
    assert deadline.tzinfo is None
    assert isinstance(deadline, datetime)


def test_finalize_deadline_never_collapses_to_now() -> None:
    """A zero or negative timeout still allows the CA one second to answer."""
    assert (_finalize_deadline(0) - datetime.now()).total_seconds() >= 0.9


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
