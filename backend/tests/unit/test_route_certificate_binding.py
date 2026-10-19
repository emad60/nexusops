"""Wildcard and label-boundary rules for certificate ↔ route coverage.

Pure-function coverage for the matcher Phase 5.4.1 binds with. The integration
suite exercises the same rule through the API; these cases pin the boundaries
that are easy to get wrong and expensive to get wrong — a wildcard that also
matches the apex, or a suffix test that matches a neighbouring name.
"""

from __future__ import annotations

import pytest
from app.services.route_certificate_service import identifier_covers_hostname


@pytest.mark.parametrize(
    ("identifier", "hostname", "expected"),
    [
        # Exact matches, including the wildcard route hostname case.
        ("example.com", "example.com", True),
        ("api.example.com", "api.example.com", True),
        ("*.example.com", "*.example.com", True),
        ("example.com", "api.example.com", False),
        # A wildcard SAN covers exactly one label below the apex.
        ("*.example.com", "api.example.com", True),
        ("*.example.com", "example.com", False),
        ("*.example.com", "a.b.example.com", False),
        # A wildcard route needs the identical wildcard identifier: a narrower
        # SAN would leave part of the name space it answers unserved.
        ("api.example.com", "*.example.com", False),
        # Label-wise, never suffix-wise.
        ("*.example.com", "notexample.com", False),
        ("*.example.com", "example.com.evil.test", False),
        ("*.example.com", "xexample.com", False),
        # Deeper SANs are not wildcards and cover only themselves.
        ("a.b.example.com", "a.b.example.com", True),
        ("a.b.example.com", "c.a.b.example.com", False),
        # Empty / malformed inputs never match.
        ("", "example.com", False),
        ("example.com", "", False),
        ("*", "example.com", False),
    ],
)
def test_identifier_coverage_boundaries(identifier: str, hostname: str, expected: bool) -> None:
    assert identifier_covers_hostname(identifier, hostname) is expected
