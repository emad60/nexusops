"""Unit tests for the ACME seam: directory policy, failure vocabulary, payloads.

The seam in :mod:`app.services.acme` is what issuance programs against, so these
tests pin the three properties the flow relies on and would miss in an integration
run: the directory matrix refuses rather than guesses, every failure has a stable
code and a bounded message, and the public payloads carry no private material.
"""

from __future__ import annotations

import dataclasses
from types import SimpleNamespace

import pytest
from app.models.enums import AcmeDirectory
from app.services.acme import (
    MAX_ERROR_DETAIL,
    REJECTION_CODES,
    TRANSIENT_CODES,
    AcmeChallenge,
    AcmeConfigError,
    AcmeOrder,
    AcmeRateLimited,
    AcmeRejected,
    AcmeTimeout,
    AcmeUnavailable,
    AuthorizationState,
    IssuedChain,
    classify_error,
    open_acme_session,
    provider_for,
    sanitize_detail,
)
from app.services.acme.directory import (
    NON_PRODUCTION_DEFAULT,
    AcmeDirectoryError,
    assert_issuance_allowed,
    coerce_directory,
    describe,
    directory_for_settings,
    directory_for_url,
    select_directory,
)
from app.services.acme.library import LibraryAcmeProvider

# --- directory selection -------------------------------------------------------


def test_non_production_default_is_staging() -> None:
    assert NON_PRODUCTION_DEFAULT is AcmeDirectory.STAGING
    assert select_directory(None, environment="test") is AcmeDirectory.STAGING
    assert select_directory("", environment="development") is AcmeDirectory.STAGING


def test_production_requires_explicit_configuration() -> None:
    with pytest.raises(AcmeDirectoryError) as refused:
        select_directory(None, environment="production")
    assert refused.value.code == "ACME_DIRECTORY_REQUIRED_IN_PRODUCTION"


@pytest.mark.parametrize("value", ["letsencrypt", "STAGING!", "", 42])
def test_unknown_directory_name_is_refused(value: object) -> None:
    # An empty string is the "unset" case and resolves to the non-production
    # default; every other unknown value is refused rather than coerced.
    if value == "":
        assert select_directory(value, environment="test") is NON_PRODUCTION_DEFAULT
        return
    with pytest.raises(AcmeDirectoryError) as refused:
        select_directory(value, environment="test")
    assert refused.value.code == "ACME_DIRECTORY_UNKNOWN"


@pytest.mark.parametrize("environment", ["test", "development", "staging", "ci", ""])
def test_production_directory_is_refused_outside_production(environment: str) -> None:
    with pytest.raises(AcmeDirectoryError) as refused:
        select_directory("production", environment=environment)
    assert refused.value.code == "ACME_DIRECTORY_PRODUCTION_OUTSIDE_PRODUCTION"


def test_pebble_is_refused_in_production() -> None:
    with pytest.raises(AcmeDirectoryError) as refused:
        select_directory(AcmeDirectory.PEBBLE, environment="production")
    assert refused.value.code == "ACME_DIRECTORY_TEST_CA_IN_PRODUCTION"


@pytest.mark.parametrize(
    ("configured", "environment", "expected"),
    [
        ("production", "production", AcmeDirectory.PRODUCTION),
        (" PRODUCTION ", "production", AcmeDirectory.PRODUCTION),
        ("staging", "production", AcmeDirectory.STAGING),
        ("pebble", "test", AcmeDirectory.PEBBLE),
        (AcmeDirectory.STAGING, "ci", AcmeDirectory.STAGING),
    ],
)
def test_allowed_combinations_pass_through(
    configured: object, environment: str, expected: AcmeDirectory
) -> None:
    assert select_directory(configured, environment=environment) is expected


def test_coerce_directory_needs_an_exact_member_name() -> None:
    assert coerce_directory(" STAGING ") is AcmeDirectory.STAGING
    assert coerce_directory(AcmeDirectory.PEBBLE) is AcmeDirectory.PEBBLE
    assert coerce_directory("staging2") is None
    assert coerce_directory(None) is None


def test_directory_for_settings_reads_the_same_matrix() -> None:
    settings = SimpleNamespace(acme_directory="staging", environment="production")
    assert directory_for_settings(settings) is AcmeDirectory.STAGING

    with pytest.raises(AcmeDirectoryError):
        directory_for_settings(SimpleNamespace(acme_directory="pebble", environment="production"))


def test_directory_for_url_is_an_exact_match_only() -> None:
    assert directory_for_url(AcmeDirectory.PRODUCTION.url()) is AcmeDirectory.PRODUCTION
    assert directory_for_url(AcmeDirectory.PEBBLE.url()) is AcmeDirectory.PEBBLE
    # A near-miss is not inferred into a member: provenance is not guessed.
    assert directory_for_url(AcmeDirectory.STAGING.url() + "/") is None
    assert directory_for_url(AcmeDirectory.STAGING.url().upper()) is None
    assert directory_for_url("") is None
    assert directory_for_url(None) is None


def test_assert_issuance_allowed_gates_the_production_directory() -> None:
    # The last gate before a client is built. Pebble is refused by
    # select_directory (and the settings validator), not here — this guard only
    # repeats the check whose failure would spend real rate limits.
    assert_issuance_allowed(AcmeDirectory.STAGING, settings=SimpleNamespace(is_production=False))
    assert_issuance_allowed(AcmeDirectory.PRODUCTION, settings=SimpleNamespace(is_production=True))

    with pytest.raises(AcmeDirectoryError) as refused:
        assert_issuance_allowed(
            AcmeDirectory.PRODUCTION, settings=SimpleNamespace(is_production=False)
        )
    assert refused.value.code == "ACME_DIRECTORY_PRODUCTION_OUTSIDE_PRODUCTION"


def test_describe_exposes_only_public_directory_facts() -> None:
    described = describe(AcmeDirectory.PEBBLE)
    assert set(described) == {"name", "label", "url", "is_production", "is_publicly_trusted"}
    assert described["name"] == "pebble"
    assert described["url"] == AcmeDirectory.PEBBLE.url()
    assert described["is_production"] is False
    assert described["is_publicly_trusted"] is False
    assert describe(AcmeDirectory.PRODUCTION)["is_publicly_trusted"] is True


# --- failure vocabulary --------------------------------------------------------


@pytest.mark.parametrize("code", sorted(REJECTION_CODES))
def test_rejection_codes_become_rejections(code: str) -> None:
    error = classify_error(code)
    assert isinstance(error, AcmeRejected)
    assert error.code == f"ACME_{code.upper()}"
    assert error.retryable is False


@pytest.mark.parametrize("code", sorted(TRANSIENT_CODES))
def test_transient_codes_are_retryable(code: str) -> None:
    error = classify_error(code)
    assert isinstance(error, AcmeUnavailable)
    assert error.retryable is True
    assert error.code == f"ACME_{code.upper()}"


def test_rate_limits_are_their_own_class() -> None:
    error = classify_error("rateLimited", "too many certificates")
    assert isinstance(error, AcmeRateLimited)
    assert error.code == "ACME_RATE_LIMITED"
    assert error.retryable is True


@pytest.mark.parametrize("code", ["", "controversialNewThing", "   "])
def test_unrecognized_codes_stay_retryable(code: str) -> None:
    # Not evidence the request was wrong: refusing to retry would strand a
    # generation that another attempt could have finished.
    error = classify_error(code)
    assert isinstance(error, AcmeUnavailable)
    assert error.code == "ACME_UNCLASSIFIED"
    assert error.retryable is True


def test_sanitize_detail_flattens_and_bounds_remote_text() -> None:
    assert sanitize_detail("a\nb\tc\r\nd") == "a b c d"
    assert sanitize_detail("  spaced   out  ") == "spaced out"
    assert sanitize_detail(None) == ""  # type: ignore[arg-type]
    assert len(sanitize_detail("x" * (MAX_ERROR_DETAIL * 3))) == MAX_ERROR_DETAIL


def test_acme_error_sanitizes_its_detail_argument() -> None:
    error = AcmeRejected("refused", code="ACME_CAA", detail="line one\nline two")
    assert "\n" not in error.detail
    assert error.detail == "line one line two"
    assert error.retryable is False


# --- provider seam -------------------------------------------------------------


def test_provider_for_returns_the_one_implementation() -> None:
    provider = provider_for(AcmeDirectory.STAGING)
    assert isinstance(provider, LibraryAcmeProvider)
    assert provider.directory is AcmeDirectory.STAGING


async def test_open_session_refuses_a_production_directory_before_connecting() -> None:
    # ENVIRONMENT=test (tests/conftest.py), so the guard refuses in `_connect`
    # before a key is loaded or a socket opened.
    with pytest.raises(AcmeConfigError) as refused:
        async with open_acme_session(
            directory=AcmeDirectory.PRODUCTION,
            account_key_pem="not-a-key",
            account_url=None,
        ):
            pytest.fail("a production session must never open outside production")
    assert refused.value.code == "ACME_DIRECTORY_PRODUCTION_OUTSIDE_PRODUCTION"


# --- public payloads -----------------------------------------------------------


def test_challenge_payload_has_no_private_fields() -> None:
    names = {field.name for field in dataclasses.fields(AcmeChallenge)}
    assert names == {
        "identifier",
        "wildcard",
        "authorization_url",
        "challenge_url",
        "token",
        "record_name",
        "record_value",
        "key_authorization",
        "status",
    }
    assert "account_key" not in names
    assert "private_key" not in names


def test_order_and_chain_payloads_are_frozen() -> None:
    order = AcmeOrder(order_url="u", status="pending", challenges=())
    with pytest.raises(dataclasses.FrozenInstanceError):
        order.status = "valid"  # type: ignore[misc]

    chain = IssuedChain(fullchain_pem="pem", order_url="u")
    assert {field.name for field in dataclasses.fields(chain)} == {
        "fullchain_pem",
        "order_url",
        "metadata",
    }


def test_authorization_state_status_predicates() -> None:
    assert AuthorizationState(status="pending").pending
    assert AuthorizationState(status="valid").valid
    assert AuthorizationState(status="invalid").invalid
    assert not AuthorizationState(status="valid").pending


def test_timeouts_are_their_own_retryable_class() -> None:
    assert isinstance(classify_error("serverInternal"), AcmeUnavailable)
    assert AcmeTimeout("late", code="ACME_POLL_TIMEOUT").retryable is True
