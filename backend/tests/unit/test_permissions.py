"""Unit tests for the permission registry, scope matching and RBAC gate."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from app.api.deps import AuthContext, require_permission
from app.core.errors import Forbidden
from app.core.permissions import (
    ALL_CODENAMES,
    PERMISSIONS,
    ROLE_MATRIX,
    SYSTEM_ROLES,
    WILDCARD,
    permission_exists,
    scope_matches,
)
from app.models import User

# --- scope_matches truth table ---------------------------------------------------


@pytest.mark.parametrize(
    ("scopes", "required", "expected"),
    [
        # exact
        (["server.read"], "server.read", True),
        (["user.read"], "user.read", True),
        (["server.read"], "server.update", False),
        (["server.reading"], "server.read", False),
        (["SERVER.READ"], "server.read", False),  # case-sensitive
        # global wildcard
        (["*"], "server.read", True),
        (["*"], "secret.write", True),
        (["monitor.*", "*"], "anything.at.all", True),
        # trailing namespace wildcard
        (["server.*"], "server.read", True),
        (["server.*"], "server.delete", True),
        (["server.*"], "servers.read", False),  # different namespace
        (["server.*"], "user.read", False),
        # multiple scopes: any match wins
        (["user.read", "metric.read"], "metric.read", True),
        (["user.read", "metric.read"], "secret.write", False),
        # misses
        ([], "server.read", False),
        ([""], "server.read", False),
        ([], "", False),
    ],
)
def test_scope_matches_truth_table(scopes: list[str], required: str, expected: bool) -> None:
    assert scope_matches(scopes, required) is expected


def test_wildcard_constant_is_star() -> None:
    assert WILDCARD == "*"


# --- registry / role matrix coherence ---------------------------------------------


def test_every_referenced_codename_exists() -> None:
    referenced = {c for perms in ROLE_MATRIX.values() for c in perms}
    # The Owner wildcard is intentionally not a concrete codename.
    unknown = referenced - set(ALL_CODENAMES) - {WILDCARD}
    assert unknown == set(), f"ROLE_MATRIX references unregistered codenames: {sorted(unknown)}"


def test_permission_codenames_are_unique_and_wellformed() -> None:
    codenames = [p.codename for p in PERMISSIONS]
    assert len(codenames) == len(set(codenames))
    for p in PERMISSIONS:
        assert p.group and p.description
        assert p.codename == p.codename.strip().lower()
        assert "." in p.codename


def test_owner_holds_only_the_wildcard() -> None:
    assert ROLE_MATRIX["Owner"] == [WILDCARD]


def test_system_roles_mirror_matrix_order() -> None:
    assert SYSTEM_ROLES == tuple(ROLE_MATRIX)
    assert set(SYSTEM_ROLES) == {"Owner", "Admin", "Operator", "Developer", "Viewer"}


def test_role_capability_lattice_is_narrowing() -> None:
    admin = set(ROLE_MATRIX["Admin"])
    operator = set(ROLE_MATRIX["Operator"])
    developer = set(ROLE_MATRIX["Developer"])
    viewer = set(ROLE_MATRIX["Viewer"])
    assert viewer <= developer <= operator <= admin
    assert "role.manage" not in operator  # only Admin/Owner manage roles
    assert not viewer & {"deployment.create", "incident.action"}


def test_permission_exists_helper() -> None:
    sample = next(iter(PERMISSIONS)).codename
    assert permission_exists(sample) is True
    assert permission_exists("no.such.permission") is False


# --- require_permission dependency (direct call with fake ctx) ---------------------


class _FakeCtx:
    """Duck-typed stand-in for AuthContext."""

    def __init__(self, allowed: bool) -> None:
        self.allowed = allowed
        self.asked_for: list[str] = []

    def has_permission(self, codename: str) -> bool:
        self.asked_for.append(codename)
        return self.allowed


async def test_require_permission_returns_ctx_when_allowed() -> None:
    dep = require_permission("server.read")
    ctx = _FakeCtx(allowed=True)
    assert await dep(ctx) is ctx  # type: ignore[arg-type]
    assert ctx.asked_for == ["server.read"]


async def test_require_permission_raises_forbidden_when_denied() -> None:
    dep = require_permission("secret.write")
    ctx = _FakeCtx(allowed=False)
    with pytest.raises(Forbidden) as excinfo:
        await dep(ctx)  # type: ignore[arg-type]
    assert excinfo.value.code == "PERMISSION_DENIED"
    assert "secret.write" in str(excinfo.value)


# --- AuthContext.has_permission integration (in-memory models only) ---------------


def _auth_context(*, superadmin: bool = False, api_key_scopes: list[str] | None = None):
    user = User(email="owner@example.com", password_hash="x", is_superadmin=superadmin)
    api_key = SimpleNamespace(scopes=api_key_scopes) if api_key_scopes is not None else None
    return AuthContext(user=user, actor_type="API_KEY" if api_key else "USER", api_key=api_key)  # type: ignore[arg-type]


def test_superadmin_bypasses_everything() -> None:
    ctx = _auth_context(superadmin=True)
    assert ctx.has_permission("user.manage") is True
    assert ctx.has_permission("anything.at.all") is True


def test_plain_user_without_permissions_is_denied() -> None:
    ctx = _auth_context()
    ctx._permission_set = set()
    assert ctx.has_permission("server.read") is False


def test_user_with_wildcard_or_exact_or_namespace_perm() -> None:
    ctx = _auth_context()
    ctx._permission_set = {"*"}
    assert ctx.has_permission("container.remove") is True

    ctx2 = _auth_context()
    ctx2._permission_set = {"server.*"}
    assert ctx2.has_permission("server.delete") is True
    assert ctx2.has_permission("server") is False  # prefix must include the dot boundary


def test_api_key_scope_intersects_role_permissions() -> None:
    ctx = _auth_context(api_key_scopes=["server.*"])
    ctx._permission_set = {"server.read", "secret.write"}
    assert ctx.has_permission("server.read") is True  # both key scope and role allow
    assert ctx.has_permission("secret.write") is False  # role allows but key scope does not

    scoped_out = _auth_context(api_key_scopes=["*"])
    scoped_out._permission_set = {"log.read"}
    assert scoped_out.has_permission("log.read") is True


def test_superadmin_owned_api_key_is_limited_to_its_scope() -> None:
    # Regression: the superadmin shortcut must come AFTER the API-key scope
    # intersection. A least-privilege machine key minted by the superadmin
    # (e.g. scopes=["metric.read"] for a CI job) must never be able to act
    # outside its grant just because its owner is a superadmin — otherwise a
    # leaked "read-only" key yields full platform control.
    ctx = _auth_context(superadmin=True, api_key_scopes=["metric.read"])
    assert ctx.has_permission("metric.read") is True
    assert ctx.has_permission("server.read") is False
    assert ctx.has_permission("server.delete") is False
    assert ctx.has_permission("secret.write") is False
    assert ctx.has_permission("user.manage") is False

    # A superadmin-owned key with an explicit wildcard still acts globally.
    wildcard_ctx = _auth_context(superadmin=True, api_key_scopes=["*"])
    assert wildcard_ctx.has_permission("server.delete") is True
