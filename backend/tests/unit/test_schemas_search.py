"""Unit tests for global-search schemas."""

from __future__ import annotations

from uuid import uuid4

import pytest
from app.schemas.search import SearchHit, SearchResultOut
from pydantic import ValidationError

_SECTIONS = (
    "servers",
    "containers",
    "deployments",
    "projects",
    "monitors",
    "incidents",
    "users",
)


def test_search_result_defaults_to_empty_sections() -> None:
    out = SearchResultOut()
    for section in _SECTIONS:
        assert getattr(out, section) == []


def test_search_result_exposes_exactly_the_documented_sections() -> None:
    assert tuple(SearchResultOut.model_fields) == _SECTIONS


def test_sections_hold_hits() -> None:
    hit = SearchHit(type="server", id=uuid4(), title="edge-01", url_path="/servers/1")
    assert hit.subtitle == ""
    out = SearchResultOut(servers=[hit])
    assert out.servers == [hit]
    assert out.containers == []


def test_search_hit_requires_core_fields() -> None:
    with pytest.raises(ValidationError):
        SearchHit(type="server", title="no id", url_path="/x")
    with pytest.raises(ValidationError):
        SearchHit(id=uuid4(), title="no type", url_path="/x")


def test_extra_fields_are_forbidden() -> None:
    with pytest.raises(ValidationError):
        SearchResultOut(servers=[], mystery=1)
