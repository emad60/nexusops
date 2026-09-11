"""Unit tests for app.schemas.server (validation only, no I/O)."""

from __future__ import annotations

import pytest
from app.core.errors import UnprocessableEntity
from app.schemas.server import ServerCreate, ServerUpdate
from pydantic import ValidationError


def _base(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {"name": "edge-01", "hostname": "edge01.example.com"}
    payload.update(overrides)
    return payload


# --- valid creation ------------------------------------------------------------------


def test_minimal_create_uses_documented_defaults() -> None:
    server = ServerCreate(**_base())
    assert server.ip_address == ""
    assert server.environment == "production"
    assert server.heartbeat_interval_seconds == 30
    assert server.offline_after_seconds is None
    assert server.tags == []
    assert server.simulated is False


def test_valid_ipv4_and_ipv6_accepted_and_stripped() -> None:
    for ip in ["10.0.0.5", "192.168.1.4", "2606:4700::1111", "::1"]:
        assert ServerCreate(**_base(ip_address=ip)).ip_address == ip
    assert ServerCreate(**_base(ip_address=" 10.0.0.5 ")).ip_address == "10.0.0.5"


def test_empty_ip_is_allowed_but_whitespace_collapses() -> None:
    assert ServerCreate(**_base(ip_address="")).ip_address == ""
    assert ServerCreate(**_base(ip_address="   ")).ip_address == ""


# --- invalid IP rejection --------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_ip", ["999.999.1.1", "not-an-ip", "10.0.0", "10.0.0.256", "example.com"]
)
def test_invalid_ip_rejected_with_stable_code(bad_ip: str) -> None:
    # AppError does not subclass ValueError, so it escapes pydantic untouched
    # and the API error handler renders its stable machine code directly.
    with pytest.raises(UnprocessableEntity) as excinfo:
        ServerCreate(**_base(ip_address=bad_ip))
    assert excinfo.value.code == "INVALID_IP"
    assert bad_ip in str(excinfo.value)


# --- tag cleaning ------------------------------------------------------------------------


def test_tags_dedup_case_insensitive_preserving_first_casing() -> None:
    server = ServerCreate(**_base(tags=["Web", "web ", "", "   ", "API", "api"]))
    assert server.tags == ["Web", "API"]


def test_tags_strip_surrounding_whitespace() -> None:
    assert ServerCreate(**_base(tags=["  prod  "])).tags == ["prod"]


def test_more_than_50_unique_tags_rejected() -> None:
    tags = [f"tag-{i:03d}" for i in range(51)]
    with pytest.raises(ValidationError):
        ServerCreate(**_base(tags=tags))
    assert len(ServerCreate(**_base(tags=tags[:50])).tags) == 50


# --- heartbeat interval bounds ---------------------------------------------------------------


@pytest.mark.parametrize("interval", [5, 30, 3600])
def test_heartbeat_interval_bounds_inclusive(interval: int) -> None:
    assert ServerCreate(**_base(heartbeat_interval_seconds=interval))


@pytest.mark.parametrize("interval", [4, 0, -30, 3601, 100_000])
def test_heartbeat_interval_out_of_bounds_rejected(interval: int) -> None:
    with pytest.raises(ValidationError):
        ServerCreate(**_base(heartbeat_interval_seconds=interval))


@pytest.mark.parametrize("seconds", [None, 1, 604_800])
def test_offline_after_bounds_inclusive(seconds: int | None) -> None:
    assert ServerCreate(**_base(offline_after_seconds=seconds)) is not None


@pytest.mark.parametrize("seconds", [0, -1, 604_801])
def test_offline_after_out_of_bounds_rejected(seconds: int) -> None:
    with pytest.raises(ValidationError):
        ServerCreate(**_base(offline_after_seconds=seconds))


# --- misc field rules --------------------------------------------------------------------------


def test_empty_name_or_hostname_rejected() -> None:
    with pytest.raises(ValidationError):
        ServerCreate(name="", hostname="h")
    with pytest.raises(ValidationError):
        ServerCreate(name="n", hostname="")


def test_unknown_fields_are_forbidden() -> None:
    with pytest.raises(ValidationError):
        ServerCreate(**_base(role="admin"))


def test_update_allows_none_and_explicit_empty_ip() -> None:
    patch = ServerUpdate(ip_address=None)
    assert patch.ip_address is None
    cleared = ServerUpdate(ip_address="")
    assert cleared.ip_address == ""


def test_update_rejects_invalid_ip_too() -> None:
    with pytest.raises(UnprocessableEntity) as excinfo:
        ServerUpdate(ip_address="300.300.300.300")
    assert excinfo.value.code == "INVALID_IP"
