"""Registry coherence: schema-advertised event types must equal the canonical registry."""

from __future__ import annotations

from app.schemas.meta import EVENT_TYPES as SCHEMA_EVENT_TYPES
from app.services.event_registry import (
    EVENT_TYPES as REGISTRY,
)
from app.services.event_registry import (
    INCIDENT_CHANNEL_PREFIXES,
    event_type_catalogue,
    is_known_event_type,
)


def test_schema_and_registry_declare_the_same_event_types() -> None:
    assert sorted(SCHEMA_EVENT_TYPES) == sorted(REGISTRY)
    # And no duplicates sneak in on either side.
    assert len(SCHEMA_EVENT_TYPES) == len(set(SCHEMA_EVENT_TYPES))
    assert len(REGISTRY) == len(set(REGISTRY))


def test_registry_is_substantive() -> None:
    assert len(REGISTRY) >= 25
    for event_type, description in REGISTRY.items():
        assert description.strip(), f"empty description for {event_type}"
        assert event_type == event_type.upper()
        assert " " not in event_type


def test_known_event_lookup() -> None:
    sample = next(iter(REGISTRY))
    assert is_known_event_type(sample) is True
    assert is_known_event_type("TOTALLY_MADE_UP") is False
    assert is_known_event_type("") is False


def test_catalogue_serialises_every_entry() -> None:
    catalogue = event_type_catalogue()
    assert {row["type"] for row in catalogue} == set(REGISTRY)
    for row in catalogue:
        assert row["description"] == REGISTRY[row["type"]]


def test_incident_channel_prefixes_reference_real_families() -> None:
    for prefix in INCIDENT_CHANNEL_PREFIXES:
        matches = [t for t in REGISTRY if t.startswith(prefix)]
        assert matches, f"prefix {prefix} matches nothing in the registry"
