"""Configuration layering: shallow merge, validation, reference collection.

These are pure functions (no database), so the contract they define — the exact
merge semantics the API and the resolver both depend on — is pinned cheaply.
"""

from __future__ import annotations

import pytest
from app.services import config_service as cfg


def test_environment_overrides_win_per_key_and_nothing_else_is_lost():
    """The documented example: project base ⊕ production overrides."""
    project = {"LOG_LEVEL": "info", "REGION": "eu", "FEATURE_X": "false"}
    production = {"LOG_LEVEL": "debug", "FEATURE_X": "true"}

    assert cfg.effective_config(project, production) == {
        "LOG_LEVEL": "debug",  # overridden
        "REGION": "eu",  # inherited
        "FEATURE_X": "true",  # overridden
    }


def test_merge_is_shallow_not_recursive():
    """A nested-looking key is replaced wholesale, never merged key-by-key."""
    project = {"A": "project-a", "B": "project-b"}
    environment = {"A": "env-a"}

    merged = cfg.merge_config(project, environment)
    assert merged["A"] == "env-a"
    assert merged["B"] == "project-b"
    # The base mapping is not mutated.
    assert project == {"A": "project-a", "B": "project-b"}


def test_merge_with_empty_layers_is_identity():
    assert cfg.merge_config({}, {}) == {}
    assert cfg.merge_config({"K": "v"}, {}) == {"K": "v"}
    assert cfg.merge_config({}, {"K": "v"}) == {"K": "v"}


def test_validate_rejects_non_flat_values():
    with pytest.raises(cfg.ConfigValidationError):
        cfg.validate_config({"NESTED": {"a": "b"}})  # type: ignore[dict-item]
    with pytest.raises(cfg.ConfigValidationError):
        cfg.validate_config({"LIST": ["a"]})  # type: ignore[dict-item]
    with pytest.raises(cfg.ConfigValidationError):
        cfg.validate_config({"NUM": 3})  # type: ignore[dict-item]


def test_validate_rejects_partial_secret_reference():
    """A value containing ${secret:...} must be exactly one full-value reference."""
    with pytest.raises(cfg.ConfigValidationError):
        cfg.validate_config({"URL": "prefix-${secret:TOKEN}-suffix"})
    # A full-value reference (the sanctioned form) is accepted.
    assert cfg.validate_config({"URL": "${secret:TOKEN}"}) == {"URL": "${secret:TOKEN}"}


def test_validate_rejects_lowercase_secret_reference():
    """One grammar: the save-time and resolver regexes agree (uppercase keys)."""
    with pytest.raises(cfg.ConfigValidationError):
        cfg.validate_config({"URL": "${secret:lower_case}"})


def test_validate_bounds():
    with pytest.raises(cfg.ConfigValidationError):
        cfg.validate_config({f"K{i}": "v" for i in range(cfg.MAX_CONFIG_KEYS + 1)})
    with pytest.raises(cfg.ConfigValidationError):
        cfg.validate_config({"K": "x" * (cfg.MAX_CONFIG_VALUE_LENGTH + 1)})
    with pytest.raises(cfg.ConfigValidationError):
        cfg.validate_config({"": "v"})


def test_collect_secret_refs_is_sorted_unique_and_value_free():
    config = {
        "A": "${secret:B_KEY}",
        "B": "${secret:A_KEY}",
        "C": "${secret:B_KEY}",  # duplicate
        "D": "plain",
    }
    assert cfg.collect_secret_refs(config) == ["A_KEY", "B_KEY"]


def test_collect_secret_refs_walks_nested_structures():
    nested = {"outer": {"inner": ["${secret:DEEP_KEY}", "plain"]}}
    assert cfg.collect_secret_refs(nested) == ["DEEP_KEY"]
    # Defensive: no plaintext is ever returned, only key names.
    assert cfg.collect_secret_refs({"X": "top-secret-value"}) == []
