"""Configuration layering: project base ⊕ environment overrides (Phase 2).

An environment's effective configuration is its **project's** ``config`` with the
environment's own ``config`` applied on top. The merge is **shallow**: a key the
environment defines replaces the project's value for that key, and every key the
environment does not mention is inherited unchanged. Nested objects are replaced,
not merged recursively — deliberately, because shallow is the one rule a reader
can apply without knowing the merge implementation.

Accepted shape (documented, not open-ended): a **flat map of string keys to
string values**. Values may be plaintext non-secret settings or a ``${secret:KEY}``
reference. Nothing here interpolates, evaluates or executes a value — config is
data the deployment engine reads, never a mechanism.

Secret material must live in a Secret row, never in config: a reference names a
key; only the reference syntax is sanctioned. A value that contains ``${secret:``
but is not exactly one full-value reference is rejected, and the config size is
bounded so config cannot become a bulk data channel.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.schemas.secret import SECRET_REF_PATTERN

#: Bounds keep config a settings map, not a payload. 100 keys of 4 KiB each is
#: two orders of magnitude above any real environment's settings.
MAX_CONFIG_KEYS = 100
MAX_CONFIG_VALUE_LENGTH = 4096

#: Maximum nesting depth the reference collector will walk. Guards against a
#: runaway structure; config is flat today, so this only ever matters if a
#: future shape nests.
MAX_CONFIG_DEPTH = 8


class ConfigValidationError(ValueError):
    """A configuration map is not shaped like a flat string→string settings map."""


def validate_config(config: Mapping[str, Any] | None, *, label: str = "config") -> dict[str, str]:
    """Return a normalised ``dict[str, str]`` or raise :class:`ConfigValidationError`.

    Enforced on **both** create and update paths (the pre-Phase-2 update path
    skipped validation entirely — secrets-architecture.md §1.4).
    """
    if config is None:
        return {}
    if not isinstance(config, Mapping):
        raise ConfigValidationError(f"{label} must be a JSON object")
    if len(config) > MAX_CONFIG_KEYS:
        raise ConfigValidationError(f"{label} supports at most {MAX_CONFIG_KEYS} keys")
    normalised: dict[str, str] = {}
    for key, value in config.items():
        if not isinstance(key, str) or not key.strip():
            raise ConfigValidationError(f"{label} keys must be non-empty strings")
        if not isinstance(value, str):
            raise ConfigValidationError(
                f"{label} value for '{key}' must be a string (config is a flat string→string map)"
            )
        if len(value) > MAX_CONFIG_VALUE_LENGTH:
            raise ConfigValidationError(
                f"{label} value for '{key}' exceeds {MAX_CONFIG_VALUE_LENGTH} chars"
            )
        if "${secret:" in value and not SECRET_REF_PATTERN.fullmatch(value):
            raise ConfigValidationError(
                f"{label} value for '{key}' must look like ${{secret:KEY_NAME}}"
            )
        normalised[key] = value
    return normalised


def merge_config(
    base: Mapping[str, str] | None,
    override: Mapping[str, str] | None,
) -> dict[str, str]:
    """Shallow merge; ``override`` wins on a key clash, everything else inherits."""
    merged: dict[str, str] = dict(base or {})
    merged.update(override or {})
    return merged


def effective_config(
    project_config: Mapping[str, str] | None,
    environment_config: Mapping[str, str] | None,
) -> dict[str, str]:
    """The resolved settings an environment deploys with (references unresolved)."""
    return merge_config(project_config, environment_config)


def collect_secret_refs(node: Any, *, _depth: int = 0) -> list[str]:
    """Recursively collect ``${secret:KEY}`` references, sorted and de-duplicated.

    Used both to resolve a deployment's references and to report which keys an
    environment *names* (names are not secrets). Never returns values.
    """
    if _depth > MAX_CONFIG_DEPTH:
        return []
    found: set[str] = set()

    def walk(value: Any, depth: int) -> None:
        if depth > MAX_CONFIG_DEPTH:
            return
        if isinstance(value, Mapping):
            for item in value.values():
                walk(item, depth + 1)
        elif isinstance(value, (list, tuple)):
            for item in value:
                walk(item, depth + 1)
        elif isinstance(value, str):
            found.update(SECRET_REF_PATTERN.findall(value))

    walk(node, _depth)
    return sorted(found)
