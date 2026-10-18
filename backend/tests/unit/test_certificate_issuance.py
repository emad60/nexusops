"""Unit tests for the issuance internals that do not need a database or a CA.

The flow around these helpers is covered by the integration suite; here the cheap,
decisive parts are pinned: failure classification and backoff, what counts as an
identifier, whether a returned chain answers our own CSR, and that the TXT
expectations group by record name and ignore a replaced order.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from app.core.errors import AppError
from app.models.enums import ActorType
from app.providers.dns import DnsProviderError
from app.services import certificate_order as order
from app.services.acme import AcmeRateLimited, AcmeRejected, AcmeTimeout
from app.services.acme.directory import AcmeDirectoryError
from app.services.acme_account_service import AcmeAccountKeyUnavailable
from app.services.certificate_issuance import (
    CODE_ATTEMPT_ERROR,
    CODE_CONTEXT_INCOMPLETE,
    CODE_MATERIAL_MISMATCH,
    _AttemptFailure,
    _aware,
    _expectations,
    _failure_from,
    _generate_key_and_csr,
    _identifiers,
    _leaf_of,
    _scheduled_retry,
    _verify_leaf,
)
from app.services.dns_provider_service import DnsCredentialUnavailable
from app.services.payload_crypto import PayloadError
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

NOW = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)


def _self_signed(key: ec.EllipticCurvePrivateKey, names: tuple[str, ...]) -> str:
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, names[0])])
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(NOW)
        .not_valid_after(NOW + timedelta(days=90))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName(name) for name in names]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )
    return certificate.public_bytes(serialization.Encoding.PEM).decode("ascii")


# --- key and CSR ---------------------------------------------------------------


def test_generated_key_and_csr_cover_every_identifier() -> None:
    identifiers = ("example.com", "www.example.com", "*.example.com")
    key, key_pem, csr_pem = _generate_key_and_csr(identifiers)

    assert isinstance(key, ec.EllipticCurvePrivateKey)
    assert key.curve.name == "secp256r1"
    assert "BEGIN PRIVATE KEY" in key_pem
    # PKCS#8 unencrypted *in this frame only*; storage encrypts it first.
    assert "ENCRYPTED" not in key_pem

    csr = x509.load_pem_x509_csr(csr_pem)
    assert csr.is_signature_valid
    san = csr.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    assert tuple(san.get_values_for_type(x509.DNSName)) == identifiers
    assert csr.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value == "example.com"


# --- identifiers ---------------------------------------------------------------


def test_identifiers_are_canonicalized_and_deduplicated() -> None:
    certificate = SimpleNamespace(
        primary_cn="Example.com",
        sans=["www.example.com", "EXAMPLE.com", "*.example.com"],
    )
    assert _identifiers(certificate) == ("example.com", "www.example.com", "*.example.com")


def test_identifiers_refuse_an_unusable_stored_name() -> None:
    certificate = SimpleNamespace(primary_cn="not a name", sans=[])
    with pytest.raises(_AttemptFailure) as failure:
        _identifiers(certificate)
    assert failure.value.code == CODE_CONTEXT_INCOMPLETE


def test_identifiers_refuse_an_empty_list() -> None:
    with pytest.raises(_AttemptFailure) as failure:
        _identifiers(SimpleNamespace(primary_cn="", sans=[]))
    assert failure.value.code == CODE_CONTEXT_INCOMPLETE


# --- leaf verification ---------------------------------------------------------


def test_leaf_of_parses_the_first_certificate() -> None:
    key = ec.generate_private_key(ec.SECP256R1())
    pem = _self_signed(key, ("example.com",))
    fullchain = pem + pem  # a chain: leaf first, then the issuer block
    assert _leaf_of(fullchain).subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value == (
        "example.com"
    )


@pytest.mark.parametrize(
    "material",
    ["", "not a certificate", "-----BEGIN CERTIFICATE-----\nxx\n-----END CERTIFICATE-----"],
)
def test_leaf_of_refuses_unreadable_material(material: str) -> None:
    with pytest.raises(_AttemptFailure) as failure:
        _leaf_of(material)
    assert failure.value.code == CODE_MATERIAL_MISMATCH


def test_verify_leaf_accepts_the_attempts_own_key_and_names() -> None:
    key = ec.generate_private_key(ec.SECP256R1())
    leaf = _leaf_of(_self_signed(key, ("example.com", "www.example.com")))
    _verify_leaf(leaf, key, ("example.com", "www.example.com"))


def test_verify_leaf_refuses_a_chain_for_another_key() -> None:
    key = ec.generate_private_key(ec.SECP256R1())
    other = ec.generate_private_key(ec.SECP256R1())
    leaf = _leaf_of(_self_signed(other, ("example.com",)))

    with pytest.raises(_AttemptFailure) as failure:
        _verify_leaf(leaf, key, ("example.com",))
    assert failure.value.code == CODE_MATERIAL_MISMATCH
    assert "does not match the key" in failure.value.message


def test_verify_leaf_refuses_a_chain_missing_an_identifier() -> None:
    key = ec.generate_private_key(ec.SECP256R1())
    leaf = _leaf_of(_self_signed(key, ("example.com",)))

    with pytest.raises(_AttemptFailure) as failure:
        _verify_leaf(leaf, key, ("example.com", "www.example.com"))
    assert failure.value.code == CODE_MATERIAL_MISMATCH
    assert "www.example.com" in failure.value.detail


# --- failure classification ----------------------------------------------------


def test_rejections_are_not_retryable() -> None:
    failure = _failure_from(AcmeRejected("refused", code="ACME_CAA", detail="caa record"))
    assert failure.code == "ACME_CAA"
    assert failure.detail == "caa record"
    assert failure.retryable is False


def test_rate_limits_carry_the_ca_retry_after() -> None:
    failure = _failure_from(AcmeRateLimited("slow down", detail="limit", retry_after_seconds=1200))
    assert failure.code == "ACME_RATE_LIMITED"
    assert failure.retryable is True
    assert failure.retry_after_seconds == 1200


def test_acme_and_dns_errors_keep_their_vocabulary() -> None:
    acme = _failure_from(AcmeTimeout("late", code="ACME_POLL_TIMEOUT"))
    assert (acme.code, acme.retryable) == ("ACME_POLL_TIMEOUT", True)

    dns_failure = _failure_from(DnsProviderError("nope", code="DNS_PROVIDER_ERROR"))
    assert (dns_failure.code, dns_failure.retryable) == ("DNS_PROVIDER_ERROR", False)


def test_directory_refusal_keeps_its_code() -> None:
    failure = _failure_from(AcmeDirectoryError("not here", code="ACME_DIRECTORY_UNKNOWN"))
    assert failure.code == "ACME_DIRECTORY_UNKNOWN"
    assert failure.retryable is False


@pytest.mark.parametrize(
    "exc",
    [DnsCredentialUnavailable("rotating"), AcmeAccountKeyUnavailable("rotating")],
)
def test_unfinished_rotation_is_retryable(exc: RuntimeError) -> None:
    failure = _failure_from(exc)
    assert failure.retryable is True


def test_payload_and_app_errors_are_named() -> None:
    payload = _failure_from(PayloadError("envelope rejected"))
    assert payload.code == "CERTIFICATE_PAYLOAD_ERROR"

    app = _failure_from(AppError("no", code="SOME_CODE"))
    assert app.code == "SOME_CODE"


def test_unclassified_exception_reports_only_its_class_name() -> None:
    failure = _failure_from(RuntimeError("secret material in the message"))
    assert failure.code == CODE_ATTEMPT_ERROR
    assert failure.detail == "RuntimeError"
    assert "secret material" not in failure.text()


def test_failure_text_is_bounded() -> None:
    failure = _AttemptFailure("m" * 400, code="X", detail="d" * 400)
    assert len(failure.text()) <= 500


def test_aware_attaches_utc_to_a_naive_timestamp() -> None:
    naive = datetime(2026, 10, 18, 12, 0)
    assert _aware(naive).tzinfo is UTC
    aware = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
    assert _aware(aware) is aware


# --- retry scheduling ----------------------------------------------------------


def test_backoff_doubles_and_honors_a_longer_retry_after() -> None:
    assert _scheduled_retry(_AttemptFailure("f", code="X"), 1, now=NOW) == NOW + timedelta(
        minutes=5
    )
    assert _scheduled_retry(_AttemptFailure("f", code="X"), 2, now=NOW) == NOW + timedelta(
        minutes=10
    )

    short = _AttemptFailure("f", code="X", retry_after_seconds=60)
    assert _scheduled_retry(short, 1, now=NOW) == NOW + timedelta(minutes=5)

    long = _AttemptFailure("f", code="X", retry_after_seconds=3600)
    assert _scheduled_retry(long, 1, now=NOW) == NOW + timedelta(hours=1)


def test_no_retry_once_the_budget_is_spent() -> None:
    assert _scheduled_retry(_AttemptFailure("f", code="X"), 5, now=NOW) is None


# --- TXT expectations ----------------------------------------------------------


def _document_with(*entries: tuple[str, str, str]) -> dict[str, object]:
    """An order document with ``(order_url, record_name, record_value)`` entries."""
    document = order.set_order({}, directory_url="d", order_url="current", mode="automated")
    challenges = [
        SimpleNamespace(
            challenge_url=f"https://ca.test/chall/{index}",
            identifier="example.com",
            wildcard=index % 2 == 1,
            authorization_url="a",
            token="t",
            record_name=name,
            record_value=value,
            key_authorization="k",
        )
        for index, (_, name, value) in enumerate(entries)
    ]
    # Record each challenge against the order_url it belongs to.
    for challenge, (order_url, _, _) in zip(challenges, entries, strict=True):
        order.record_challenges(document, (challenge,), mode="automated", order_url=order_url)
    return document


def test_expectations_group_shared_names_and_keep_both_values() -> None:
    document = _document_with(
        ("current", "_acme-challenge.example.com", "apex-value"),
        ("current", "_acme-challenge.example.com", "wildcard-value"),
    )
    expectations = _expectations(document)
    assert len(expectations) == 1
    assert expectations[0].name == "_acme-challenge.example.com"
    assert set(expectations[0].values) == {"apex-value", "wildcard-value"}


def test_expectations_ignore_a_replaced_order_and_blank_entries() -> None:
    document = _document_with(
        ("old", "_acme-challenge.example.com", "stale-value"),
        ("current", "_acme-challenge.other.test", "live-value"),
    )
    # A blank value can only come from a malformed document; it is skipped.
    document["challenges"].append(
        {
            "challenge_url": "https://ca.test/chall/blank",
            "order_url": "current",
            "record_name": "",
            "record_value": "",
        }
    )

    expectations = _expectations(document)
    assert [expectation.name for expectation in expectations] == ["_acme-challenge.other.test"]
    assert expectations[0].values == ("live-value",)


def test_actor_records_the_system_when_no_caller_asked() -> None:
    from app.services.certificate_issuance import _actor

    assert _actor(None) == (None, ActorType.SYSTEM)


def test_actor_keeps_the_caller_type() -> None:
    from app.services.certificate_issuance import _actor

    ctx = SimpleNamespace(user_id=None, actor_type="USER")
    assert _actor(ctx) == (None, ActorType.USER)

    # An unrecognized actor type is not guessed at as SYSTEM; the call still has a
    # user, so it is recorded as one.
    unknown = SimpleNamespace(user_id=None, actor_type="not-a-type")
    assert _actor(unknown) == (None, ActorType.USER)
