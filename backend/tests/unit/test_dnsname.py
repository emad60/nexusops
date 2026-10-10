"""Canonicalisation and coverage: the rules routing and verification both share.

These are the tests that keep "what the API stored" and "what the renderer
compares" the same string. Every rejection case is here because the alternative
was a subtle acceptance: substring coverage, an IP literal treated as a name, an
all-numeric TLD, or a wildcard in the middle of a name.
"""

from __future__ import annotations

import pytest
from app.core.dnsname import (
    InvalidName,
    canonicalize_name,
    canonicalize_path,
    hostname_is_covered,
    is_valid_path,
    verification_record_name,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Example.COM", "example.com"),
        ("example.com.", "example.com"),
        ("  Example.com  ", "example.com"),
        ("a.b.c.example.com", "a.b.c.example.com"),
        ("my-host.example.com", "my-host.example.com"),
        ("xn--80ak6aa92e.com", "xn--80ak6aa92e.com"),
    ],
)
def test_canonicalization_lowercases_and_strips(raw: str, expected: str) -> None:
    assert canonicalize_name(raw) == expected


def test_idna_names_become_punycode() -> None:
    # The canonical stored form is always ASCII, so uniqueness and coverage
    # compare one representation for a name that has two spellings.
    assert canonicalize_name("Пример.Испытание") == "xn--e1afmkfd.xn--80akhbyknj4f"
    assert canonicalize_name("bücher.example") == "xn--bcher-kva.example"


@pytest.mark.parametrize(
    "raw",
    [
        "localhost",
        "example",
        "*.example.com",  # wildcards are opt-in, not the default
        "-leading.example.com",
        "trailing-.example.com",
        "under_score.example.com",
        "double..dot.example.com",
        "",
        " ",
        "example..com",
        "exa mple.com",
        "example.com/path",
        "http://example.com",
        "*.*.example.com",
        "a.*.example.com",
    ],
)
def test_invalid_names_are_rejected(raw: str) -> None:
    with pytest.raises(InvalidName):
        canonicalize_name(raw)


@pytest.mark.parametrize("raw", ["192.168.1.1", "10.0.0.1", "::1", "[2001:db8::1]", "2001:db8::1"])
def test_ip_literals_are_rejected(raw: str) -> None:
    with pytest.raises(InvalidName) as excinfo:
        canonicalize_name(raw)
    assert excinfo.value.code == "DOMAIN_IS_IP"


def test_all_numeric_tld_is_rejected() -> None:
    with pytest.raises(InvalidName):
        canonicalize_name("example.123")


def test_labels_longer_than_63_octets_are_rejected() -> None:
    with pytest.raises(InvalidName):
        canonicalize_name(f"{'a' * 64}.example.com")


def test_name_longer_than_253_octets_is_rejected() -> None:
    label = "a" * 60
    with pytest.raises(InvalidName):
        canonicalize_name(".".join([label] * 5))


def test_wildcard_is_allowed_only_as_the_first_label() -> None:
    assert canonicalize_name("*.example.com", allow_wildcard=True) == "*.example.com"
    with pytest.raises(InvalidName):
        canonicalize_name("api.*.example.com", allow_wildcard=True)
    with pytest.raises(InvalidName):
        canonicalize_name("*example.com", allow_wildcard=True)


def test_verification_record_name_uses_the_apex() -> None:
    assert verification_record_name("example.com") == "_nexusops.example.com"
    assert verification_record_name("*.example.com") == "_nexusops.example.com"
    assert verification_record_name("api.example.com") == "_nexusops.api.example.com"


@pytest.mark.parametrize(
    ("hostname", "domain"),
    [
        ("example.com", "example.com"),
        ("api.example.com", "example.com"),
        ("a.example.com", "example.com"),
        ("*.example.com", "*.example.com"),
        ("api.example.com", "*.example.com"),
        ("deep.api.example.com", "deep.api.example.com"),
    ],
)
def test_covered_hostnames(hostname: str, domain: str) -> None:
    assert hostname_is_covered(hostname, domain)


@pytest.mark.parametrize(
    ("hostname", "domain"),
    [
        # One label deeper than the domain: explicitly out of scope, so hostname
        # coverage cannot diverge from the wildcard-certificate depth rule.
        ("a.b.example.com", "example.com"),
        # The apex of a wildcard domain is not covered by the wildcard itself.
        ("example.com", "*.example.com"),
        # A name that merely *ends with* the string is not covered.
        ("notexample.com", "example.com"),
        ("example.com.evil.test", "example.com"),
        ("xexample.com", "example.com"),
        # A wildcard route needs a wildcard domain.
        ("*.example.com", "example.com"),
        ("api.other.com", "example.com"),
    ],
)
def test_uncovered_hostnames(hostname: str, domain: str) -> None:
    assert not hostname_is_covered(hostname, domain)


def test_coverage_is_not_a_substring_test() -> None:
    # The regression this guards: ``"example.com" in hostname``-style checks
    # accept attacker-controlled suffixes.
    assert not hostname_is_covered("evil-example.com", "example.com")
    assert not hostname_is_covered("example.com.attacker.test", "example.com")


@pytest.mark.parametrize("path", ["/", "/api", "/a/b/c", "/v1.2/x_y-z", "/a/b/"])
def test_valid_paths(path: str) -> None:
    assert is_valid_path(path)
    assert canonicalize_path(path) == path


@pytest.mark.parametrize(
    "path",
    [
        "api",  # must be absolute
        "/a b",
        "/a;b",
        "/a{b}",
        "/a$b",
        "/a'b",
        '/a"b',
        "/../etc/passwd",
        "//double",
        "/~regex",
        "/=404",
    ],
)
def test_invalid_paths(path: str) -> None:
    assert not is_valid_path(path)
    with pytest.raises(InvalidName):
        canonicalize_path(path)
