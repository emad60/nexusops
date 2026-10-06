"""The system-scope allowlist is the only fence around the tenancy carve-out.

``system_scope`` turns off both the ORM tenant guard and PostgreSQL RLS, so a
module that calls it is a place where the database will not enforce the tenant
boundary. ``app.core.tenancy.SYSTEM_SCOPE_ALLOWED_MODULES`` names the modules
allowed to do that and the docstring promises it is "asserted mechanically
rather than trusted".

This module is that assertion, and it checks the list in **both** directions:

* a module that calls ``system_scope``/``system_write_scope`` but is not listed
  is a new hole, and fails;
* a module that is listed but no longer calls it is stale documentation, and
  also fails — otherwise the list rots into "some files somewhere" and nobody
  can tell how many holes exist.

The scan is AST-based rather than a grep so a comment or docstring that merely
mentions ``system_scope`` (this module and ``docs/`` are full of them) cannot
satisfy or trip it.
"""

from __future__ import annotations

import ast
from pathlib import Path

from app.core.tenancy import SYSTEM_SCOPE_ALLOWED_MODULES

BACKEND_DIR = Path(__file__).resolve().parents[2]
APP_DIR = BACKEND_DIR / "app"

#: Functions that suspend tenant isolation. Any *call* to one of these counts,
#: including the ``sweep_session`` helper in ``app/tasks/_util.py`` — it opens a
#: system scope on the caller's behalf, so a module using it has the same
#: privileges as one calling ``system_scope`` directly.
SYSTEM_SCOPE_FUNCTIONS = frozenset({"system_scope", "system_write_scope", "sweep_session"})


def _module_path(path: Path) -> str:
    return path.relative_to(BACKEND_DIR).as_posix()


def _calls_system_scope(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if name in SYSTEM_SCOPE_FUNCTIONS:
            return True
    return False


def _scanned_files() -> list[Path]:
    """Every module that could open a system scope: ``app/`` plus the scripts."""
    files = [p for p in APP_DIR.rglob("*.py") if "__pycache__" not in p.parts]
    files.extend(p for p in (BACKEND_DIR / "scripts").rglob("*.py"))
    return sorted(files)


def _actual_callers() -> set[str]:
    callers: set[str] = set()
    for path in _scanned_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:  # pragma: no cover - a broken file fails elsewhere
            raise AssertionError(f"cannot parse {_module_path(path)}: {exc}") from exc
        if _calls_system_scope(tree):
            callers.add(_module_path(path))
    return callers


def test_every_system_scope_caller_is_allowlisted() -> None:
    """No module may lift tenant isolation without being named in the list."""
    unlisted = sorted(_actual_callers() - set(SYSTEM_SCOPE_ALLOWED_MODULES))
    assert not unlisted, (
        "These modules call system_scope() but are not in "
        "SYSTEM_SCOPE_ALLOWED_MODULES: "
        + ", ".join(unlisted)
        + ". Either rewrite them to act inside org_scope(...) or add them to the "
        "allowlist with a comment explaining why the tenant boundary cannot apply."
    )


def test_allowlist_has_no_stale_entries() -> None:
    """Every listed module must still be a real caller, so the list stays short."""
    stale = sorted(set(SYSTEM_SCOPE_ALLOWED_MODULES) - _actual_callers())
    assert not stale, (
        "These modules are allowlisted for system_scope() but no longer call it; "
        "remove them from SYSTEM_SCOPE_ALLOWED_MODULES: " + ", ".join(stale)
    )


def test_allowlisted_modules_exist() -> None:
    """A typo in the allowlist would otherwise disable both checks above."""
    missing = sorted(
        module for module in SYSTEM_SCOPE_ALLOWED_MODULES if not (BACKEND_DIR / module).exists()
    )
    assert not missing, "Allowlisted modules that do not exist: " + ", ".join(missing)
