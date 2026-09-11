"""Test bootstrap: pin every cached setting BEFORE the first ``app`` import.

The repository ``.env`` points services at docker-internal hostnames
(``postgres``, ``redis``); this suite talks to loopback instances with a
dedicated database and Redis index. ``get_settings`` is ``lru_cache``-d, so the
environment below must be final before anything imports :mod:`app` — pytest
loads this file before collecting test modules, which guarantees that order.

Credentials are read from the repo ``.env`` at runtime and are never printed.
"""

from __future__ import annotations

import base64
import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_DIR = BACKEND_DIR.parent
DOT_ENV_PATH = REPO_DIR / ".env"

TEST_DB_NAME = "nexusops_test"
TEST_PG_HOST = "127.0.0.1"
#: Dedicated Redis index so flushdb can never touch shared data.
TEST_REDIS_DB = 1

if str(BACKEND_DIR) not in sys.path:  # allow `pytest` from any cwd
    sys.path.insert(0, str(BACKEND_DIR))


def _read_dot_env() -> dict[str, str]:
    """KEY=VALUE pairs from the repo .env (first definition wins); never logged."""
    values: dict[str, str] = {}
    try:
        lines = DOT_ENV_PATH.read_text(encoding="utf-8").splitlines()
    except OSError:
        return values
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        cleaned = value.split(" #", 1)[0].strip().strip("'\"")
        if key:
            values.setdefault(key, cleaned)
    return values


_DOT_ENV = _read_dot_env()
_PG_PORT = _DOT_ENV.get("NEXUSOPS_POSTGRES_PORT", "5433")
_REDIS_PORT = _DOT_ENV.get("NEXUSOPS_REDIS_PORT", "6390")
_PG_USER = _DOT_ENV.get("POSTGRES_USER", "nexusops")
_PG_PASSWORD = _DOT_ENV.get("POSTGRES_PASSWORD", "")
_ADMIN_DB = _DOT_ENV.get("POSTGRES_DB", "postgres")

TEST_DATABASE_URL = (
    f"postgresql+psycopg://{quote_plus(_PG_USER)}:{quote_plus(_PG_PASSWORD)}"
    f"@{TEST_PG_HOST}:{_PG_PORT}/{TEST_DB_NAME}"
)
TEST_REDIS_URL = f"redis://127.0.0.1:{_REDIS_PORT}/{TEST_REDIS_DB}"

# Test-only fallbacks; the repo .env values win when present.
_FALLBACK_JWT_SECRET = "nexusops-integration-tests-signing-key-0123456789abcdef"
_FALLBACK_ENCRYPTION_KEY = base64.urlsafe_b64encode(b"nexusops-integration-test-key-x32").decode()


def configure_test_env() -> None:
    """Export the exact settings the app caches; host values cannot leak through."""
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["REDIS_URL"] = TEST_REDIS_URL
    os.environ["SIMULATION_MODE"] = "true"
    os.environ["ENVIRONMENT"] = "test"
    # Security tests must exercise the strict SSRF guard regardless of what a
    # developer's .env permits for local dev convenience.
    os.environ["ALLOW_PRIVATE_TARGETS"] = "false"
    # Access-log noise off; structlog config is read at first app import.
    os.environ["LOG_LEVEL"] = "WARNING"
    os.environ.setdefault("JWT_SECRET", _DOT_ENV.get("JWT_SECRET") or _FALLBACK_JWT_SECRET)
    os.environ.setdefault(
        "ENCRYPTION_KEY", _DOT_ENV.get("ENCRYPTION_KEY") or _FALLBACK_ENCRYPTION_KEY
    )


configure_test_env()
