"""Unit tests for pagination primitives: params, bounds and cursors."""

from __future__ import annotations

import inspect
from datetime import UTC, datetime

import pytest
from app.core.pagination import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    CursorPage,
    CursorParams,
    Page,
    PageParams,
    cursor_params,
    decode_cursor,
    encode_cursor,
    page_params,
)


def _query_default(param_name: str, func: object) -> object:
    signature = inspect.signature(func)  # type: ignore[arg-type]
    return signature.parameters[param_name].default


def _constraint(default: object, kind: type) -> object | None:
    """Pull a Ge/Le constraint out of a FastAPI Query's pydantic metadata."""
    for meta in getattr(default, "metadata", []):
        if isinstance(meta, kind):
            return meta
    return None


# --- offset pages ------------------------------------------------------------------


def test_page_params_defaults_and_constants() -> None:
    assert DEFAULT_LIMIT == 25
    assert MAX_LIMIT == 100
    assert PageParams() == PageParams(limit=DEFAULT_LIMIT, offset=0)


def test_page_params_holds_explicit_values() -> None:
    assert page_params(limit=10, offset=5) == PageParams(limit=10, offset=5)
    assert page_params(limit=1, offset=0) == PageParams(limit=1, offset=0)


def test_offset_query_declares_ge_zero_without_upper_bound() -> None:
    from annotated_types import Ge, Le

    default = _query_default("offset", page_params)
    assert default.default == 0
    ge = _constraint(default, Ge)
    assert ge is not None and ge.ge == 0
    assert _constraint(default, Le) is None


def test_limit_query_declares_one_to_max_limit() -> None:
    from annotated_types import Ge, Le

    default = _query_default("limit", page_params)
    assert default.default == DEFAULT_LIMIT
    assert _constraint(default, Ge).ge == 1  # type: ignore[union-attr]
    assert _constraint(default, Le).le == MAX_LIMIT  # type: ignore[union-attr]


# --- keyset cursors -----------------------------------------------------------------


def test_cursor_roundtrip() -> None:
    ts = datetime(2026, 8, 24, 12, 30, 15, tzinfo=UTC)
    token = encode_cursor(ts, 4242)
    assert isinstance(token, str)
    decoded = decode_cursor(token)
    assert decoded is not None
    assert decoded.ts == ts
    assert decoded.id == 4242


@pytest.mark.parametrize(
    "bad", [None, "", "not-base64!!", "YWJj", "no-pipe-here", "2026-08-24T00:00:00|notanint"]
)
def test_bad_cursors_decode_to_none(bad: str | None) -> None:
    assert decode_cursor(bad) is None


def test_pipe_inside_timestamp_survives() -> None:
    ts = datetime(2026, 8, 24, tzinfo=UTC)
    decoded = decode_cursor(encode_cursor(ts, 7))
    assert decoded is not None
    assert (decoded.ts, decoded.id) == (ts, 7)


def test_cursor_params_bounds() -> None:
    from annotated_types import Ge, Le

    limit = _query_default("limit", cursor_params)
    assert limit.default == DEFAULT_LIMIT
    assert _constraint(limit, Ge).ge == 1  # type: ignore[union-attr]
    assert _constraint(limit, Le).le == MAX_LIMIT  # type: ignore[union-attr]
    cursor = _query_default("cursor", cursor_params)
    assert cursor.default is None
    assert CursorParams() == CursorParams(limit=DEFAULT_LIMIT, cursor=None)


# --- page models ----------------------------------------------------------------------


def test_page_model_fields() -> None:
    page = Page[int](items=[1, 2], total=10, limit=2, offset=0)
    assert page.model_dump() == {"items": [1, 2], "total": 10, "limit": 2, "offset": 0}


def test_cursor_page_defaults() -> None:
    page = CursorPage[str](items=["a"])
    assert page.next_cursor is None
    assert page.has_more is False
