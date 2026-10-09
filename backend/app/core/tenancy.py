"""Tenancy core: organization scope, the session guard and the RLS GUC.

Everything that decides *which organization a unit of work may see* lives here.
There are three independent nets, and they are deliberately not interchangeable:

===============  ==========================================================================
Net              Catches
===============  ==========================================================================
Session guard    every ORM SELECT (``with_loader_criteria``); rejected DML that forgot
(``do_orm_execute``)  ``org_id``; rejected Core statements and unscoped access
Org stamping     new rows missing an owner; rows moved to another tenant
(``before_flush``)
Explicit predicates   write paths that name ``org_id`` in their WHERE clause
PostgreSQL RLS   the backstop: bulk DML, identity-map hits, raw SQL, ORM bugs
===============  ==========================================================================

The guard filters SELECTs only — SQLAlchemy does not apply loader criteria to
ORM-enabled UPDATE/DELETE, and Core statements bypass it entirely. That is why
RLS exists and why :class:`TenancyScopeError` is raised rather than a filter
being silently skipped: a missing filter is a cross-tenant read, and the failure
mode of "no filter" is strictly worse than a loud error. INSERTs are covered by
stamping (:func:`_stamp_org_on_flush`) plus the RLS ``WITH CHECK``.

Scopes
------
* ``org_scope(org_id)`` — tenant scope. Selects are filtered to that org; DML
  must carry ``org_id``; Core statements are refused.
* ``system_scope(reason)`` — maintenance scope. No guard, no RLS filter. Only
  permitted in the modules listed in :data:`SYSTEM_SCOPE_ALLOWED_MODULES`
  (asserted by ``tests/unit/test_tenancy_allowlist.py``), and every use is
  logged with its reason.
* neither — *unset*. Fail-loud: touching an organization-owned table raises.
  Nothing in the request path should ever run here, and RLS denies everything
  anyway because the GUC is left empty.

The GUC
-------
``app.current_org`` is set with ``set_config(..., is_local => true)`` at the
start of **every** transaction (``after_begin``). Transaction-local is the
property that makes a pooled connection safe: PostgreSQL discards the setting
when the transaction ends, so a connection handed back to the pool carries no
organization at all. A *session-level* setting (``is_local => false``) instead
survives SQLAlchemy's checkin reset — which is a plain ``rollback`` and does not
undo ``set_config`` — and lingered until the next transaction happened to
re-issue it. Scoping it to the transaction closes that window rather than
relying on the re-issuance to cover it.

``after_begin`` is the right setter for the same reason it always was: it fires
exactly when the transaction begins, which is precisely when ``SET LOCAL`` is
guaranteed to apply (the old worry — a ``SET LOCAL`` compiled outside any
transaction being a no-op — does not apply to a hook that runs *inside* the
begin).

The value is always a UUID *string*: ``SYSTEM_ORG_SENTINEL`` for system scope,
the organization id for tenant scope, and the empty string when unset. Policies
compare through :func:`app_current_org` (see the tenancy migration), which
returns NULL for anything that is not a well-formed UUID — so a None, an empty
string or the ``system`` literal can never raise a cast error mid-query, and RLS
fails closed instead of failing loudly in the wrong place.

A session must not span two scopes: enter the scope before its first statement,
or call :func:`apply_scope_to_session` after switching (the helper exists for
exactly that, and for tests that reuse one session deliberately).
"""

from __future__ import annotations

import contextlib
import functools
import uuid
from collections.abc import AsyncIterator, Iterator
from contextvars import ContextVar, Token
from typing import Any

from sqlalchemy import event as sa_event
from sqlalchemy.engine import Connection
from sqlalchemy.orm import ORMExecuteState, Session, with_loader_criteria
from sqlalchemy.sql import ColumnElement, visitors
from sqlalchemy.sql.schema import TableClause

from app.core.logging import get_logger
from app.models.tenancy import SYSTEM_ORG_SENTINEL

log = get_logger("nexusops.tenancy")

# --- Scopes ------------------------------------------------------------------

SCOPE_UNSET = "unset"
SCOPE_ORG = "org"
SCOPE_SYSTEM = "system"

_current_org: ContextVar[uuid.UUID | None] = ContextVar("nexusops_current_org", default=None)
_current_scope: ContextVar[str] = ContextVar("nexusops_current_scope", default=SCOPE_UNSET)
_scope_reason: ContextVar[str] = ContextVar("nexusops_scope_reason", default="")

#: GUC name read by every RLS policy.
ORG_GUC = "app.current_org"

#: Modules permitted to open a system scope, i.e. to run with tenant isolation
#: switched off. This is the only fence around the carve-out, so it is asserted
#: mechanically rather than trusted: see ``tests/unit/test_tenancy_allowlist.py``,
#: which AST-scans ``app/`` and ``scripts/`` and fails if a module outside this
#: set opens a scope (or if a listed module stops doing so, so the list cannot
#: rot into a vague list of files nobody dares edit).
#:
#: Two shapes legitimately need it, and nothing else does:
#:
#: * **Pre-org writes** — a security event about a caller whose organization is
#:   not yet known (a failed login for an address with no account, a refresh
#:   token replay). Written through ``system_write_scope`` and readable only by
#:   a system scope, never by a tenant.
#: * **Cross-tenant sweeps** — a worker or dispatcher that has to *find* work
#:   before it knows whose work it is, then re-enters ``org_scope`` per row
#:   before touching anything. The claim itself is the only system-scoped step.
SYSTEM_SCOPE_ALLOWED_MODULES: frozenset[str] = frozenset(
    {
        "app/core/tenancy.py",  # defines the scopes
        "app/services/auth_service.py",  # pre-org security events (login/refresh/logout)
        "app/services/enrollment_service.py",  # pre-org enrollment-token hash lookup
        "app/services/event_bus.py",  # raw-frame consumers are cross-org by design
        "app/services/notification_service.py",  # claims undelivered rows, dispatches frames
        "app/tasks/_util.py",  # sweep_session(), the worker-side claim helper
        "app/tasks/deployments.py",  # deployment sweeper
        "app/tasks/heartbeat.py",  # offline sweep
        "app/tasks/maintenance.py",  # retention/aggregation sweeps
        "app/tasks/monitoring.py",  # monitor due-check claim
        "app/tasks/simulation.py",  # simulation tick
    }
)

#: Organization-owned tables deliberately outside RLS, with the reason. Keep
#: this list tiny and justified: every entry is a hole, and the catalog test
#: (``tests/integration/test_rls_policies.py``) compares it against the actual
#: set of tables carrying an ``org_id`` column so nothing can join silently.
RLS_EXEMPT_ORG_TABLES: dict[str, str] = {
    "organizations": "the tenant itself — cannot be scoped by its own id",
    "memberships": "read before an org is known: validating X-Org-Id is a cross-org read",
    "api_keys": "hash lookup precedes org knowledge; the key's org_id is its boundary",
    "roles": "instance-wide templates in v1 (org_id is NULL for every row)",
    "agent_credentials": "node token hash → (node, org) routing; pre-org by definition",
}


class TenancyScopeError(RuntimeError):
    """Raised when a unit of work touches tenant data with no valid org scope.

    This is a programming error, never a user-facing condition: it means a code
    path reached organization-owned data without saying which organization it
    was acting for. It surfaces as a 500 so it cannot be mistaken for an
    authorization decision.
    """


# --- Scope accessors ---------------------------------------------------------


def current_org() -> uuid.UUID | None:
    """The organization this unit of work is acting for, if any."""
    return _current_org.get()


def current_scope() -> str:
    """``'org'``, ``'system'`` or ``'unset'``."""
    return _current_scope.get()


def require_org() -> uuid.UUID:
    """Return the active org id or raise; used by services that need it explicitly."""
    org = _current_org.get()
    if org is None:
        raise TenancyScopeError(
            "no active organization: this code path must run inside org_scope(...)"
        )
    return org


def _desired_guc() -> str:
    """The ``app.current_org`` value implied by the current scopes."""
    scope = _current_scope.get()
    if scope == SCOPE_ORG:
        org = _current_org.get()
        return str(org) if org is not None else ""
    if scope == SCOPE_SYSTEM:
        return SYSTEM_ORG_SENTINEL
    return ""


@contextlib.contextmanager
def org_scope(org_id: uuid.UUID) -> Iterator[None]:
    """Run the enclosed block as a single organization.

    Nesting the *same* org is a no-op (worker loops often re-enter); switching
    to a different org while one is active is refused, because a session that
    spans two scopes is exactly how an identity-map hit turns into a cross-tenant
    read.
    """
    active = _current_org.get()
    if _current_scope.get() == SCOPE_ORG and active is not None:
        if active == org_id:
            yield
            return
        raise TenancyScopeError(
            f"already inside org_scope({active}); refusing to switch to {org_id} "
            "on the same session — open a fresh session instead"
        )
    org_token: Token[uuid.UUID | None] = _current_org.set(org_id)
    scope_token = _current_scope.set(SCOPE_ORG)
    reason_token = _scope_reason.set("")
    try:
        yield
    finally:
        _scope_reason.reset(reason_token)
        _current_scope.reset(scope_token)
        _current_org.reset(org_token)


@contextlib.contextmanager
def system_scope(reason: str) -> Iterator[None]:
    """Run the enclosed block with tenant filtering off (maintenance only).

    ``reason`` is required and logged: every one of these blocks is a place where
    the database will not enforce the tenant boundary for us, so the audit trail
    of *why* matters.
    """
    if _current_scope.get() == SCOPE_SYSTEM:
        yield
        return
    org_token: Token[uuid.UUID | None] = _current_org.set(None)
    scope_token = _current_scope.set(SCOPE_SYSTEM)
    reason_token = _scope_reason.set(reason)
    log.info("system_scope_enter", reason=reason)
    try:
        yield
    finally:
        _scope_reason.reset(reason_token)
        _current_scope.reset(scope_token)
        _current_org.reset(org_token)


# --- Session guard -----------------------------------------------------------


def _org_scoped_classes() -> tuple[type, ...]:
    """Mapped classes marked :class:`~app.models.base.OrgScoped`.

    Reads the mapper registry rather than ``OrgScoped.__subclasses__()`` so a
    model that inherits from another organization-owned model (indirect
    inheritance) is still covered — a table the guard cannot enumerate would
    silently fall back to RLS alone.
    """
    from app.models.base import Base, OrgScoped

    return tuple(
        mapper.class_
        for mapper in Base.registry.mappers
        if isinstance(mapper.class_, type) and issubclass(mapper.class_, OrgScoped)
    )


@functools.cache
def org_scoped_table_names() -> frozenset[str]:
    """Names of the tables the guard and RLS are expected to cover."""
    from sqlalchemy import inspect as sa_inspect

    names: set[str] = set()
    for cls in _org_scoped_classes():
        table: Any = sa_inspect(cls).local_table
        if table is not None:
            names.add(table.name)
    return frozenset(names)


def _statement_tables(statement: Any) -> set[str]:
    """Every table name referenced anywhere in *statement*.

    Raw ``text()`` fragments are opaque here — that is the documented limit of
    the guard, and precisely why RLS exists (a ``text()`` statement is filtered
    by the policies whether or not the guard can see it).
    """
    names: set[str] = set()
    for element in visitors.iterate(statement, {}):
        if isinstance(element, TableClause):
            name = getattr(element, "name", None)
            if name:
                names.add(name)
    return names


def _has_org_predicate(statement: Any) -> bool:
    """Whether a DML statement explicitly constrains ``org_id``."""
    where = getattr(statement, "whereclause", None)
    if where is None:
        return False
    for element in visitors.iterate(where, {}):
        if isinstance(element, ColumnElement) and getattr(element, "name", None) == "org_id":
            return True
    return False


def _mappers_of(state: ORMExecuteState) -> list[Any]:
    """Mappers the statement involves (``bind_mapper`` covers DML, ``all_mappers`` reads)."""
    mappers: list[Any] = []
    if state.bind_mapper is not None:
        mappers.append(state.bind_mapper)
    mappers.extend(state.all_mappers)
    return mappers


def _touched_table_names(state: ORMExecuteState) -> set[str]:
    """Which organization-owned tables this statement reads or writes."""
    scoped = org_scoped_table_names()
    if not state.is_orm_statement:
        return _statement_tables(state.statement) & scoped
    names: set[str] = set()
    for mapper in _mappers_of(state):
        table = mapper.local_table
        if table is not None and table.name in scoped:
            names.add(table.name)
    return names


def _guard(state: ORMExecuteState) -> None:
    """``do_orm_execute`` handler: filter reads, refuse unscoped writes."""
    scope = _current_scope.get()
    org = _current_org.get()

    if scope == SCOPE_SYSTEM:
        return
    if scope == SCOPE_ORG and org is None:
        raise TenancyScopeError("org_scope() entered without an organization id")

    touched = _touched_table_names(state)

    if scope == SCOPE_UNSET:
        # Fail loud. The alternative — filtering on ``org_id == None`` — matches
        # only orphan rows, turning a missing scope into a silent empty result
        # instead of a bug report. Statements whose mappers the guard cannot
        # resolve (column/relationship loads report no mappers of their own) are
        # left to RLS, which denies them because the GUC is empty.
        if touched:
            _refuse(
                scope,
                f"organization-owned table(s) {sorted(touched)} reached with no tenant "
                f"scope (statement: {type(state.statement).__name__})",
            )
        return

    if not touched:
        return

    if not state.is_orm_statement:
        # Core statements cannot be filtered or rewritten by the guard, so they
        # are refused outright under org scope rather than silently unfiltered.
        _refuse(
            scope,
            f"Core statement touches organization-owned table(s) {sorted(touched)}; "
            f"use the ORM, or run the operation inside system_scope()",
        )

    if state.is_select:
        # with_loader_criteria applies to every mapped class inheriting
        # OrgScoped, including relationship and column (refresh) loads. NULL
        # org_id rows (pre-org audit/event records) do not match
        # ``org_id == <uuid>``, so they are invisible under org scope by
        # construction rather than by an extra predicate.
        #
        # The criteria must be a *callable* of the target class: ``OrgScoped`` is
        # a plain mixin, so it has no mapper of its own and ``OrgScoped.org_id``
        # is an unnamed, unattached column — building the expression up front
        # makes the statement uncompilable ("Cannot compile Column object until
        # its 'name' is assigned"). The lambda is evaluated per entity, which is
        # also what makes ``include_aliases`` work.
        from app.models.base import OrgScoped

        state.statement = state.statement.options(
            with_loader_criteria(OrgScoped, lambda cls: cls.org_id == org, include_aliases=True)
        )
        return

    if (state.is_update or state.is_delete) and not _has_org_predicate(state.statement):
        _refuse(
            scope,
            f"bulk {'UPDATE' if state.is_update else 'DELETE'} on {sorted(touched)} "
            f"carries no org_id predicate; loader criteria do not apply to DML — add "
            f"``.where(Model.org_id == org_id)``, or run it inside system_scope()",
        )


def _stamp_org_on_flush(session: Session, flush_context: Any, instances: Any) -> None:
    """``before_flush`` handler: own new rows, and refuse rows that change hands.

    Loader criteria do not apply to INSERT, so without this every service that
    creates a row would have to remember ``org_id=...``: a forgotten column was
    a silent NULL (which RLS rejects as a ``WITH CHECK`` violation — loud, but
    with a database error and no model name). Stamping it here makes ownership a
    property of the scope rather than of each call site.

    The dangerous case is not a missing ``org_id`` but a **mismatched** one: a
    row created during organization A's request pointing at organization B. RLS
    would reject it; this raises first, at the ORM layer, naming the model — so
    the bug is reported where it was written. The same check covers an UPDATE
    that tries to move an existing row into another organization.
    """
    if _current_scope.get() != SCOPE_ORG:
        return
    from app.models.base import OrgScoped

    org = require_org()
    for obj in session.new:
        if not isinstance(obj, OrgScoped):
            continue
        owner = getattr(obj, "org_id", None)
        if owner is None:
            obj.org_id = org
        elif owner != org:
            raise TenancyScopeError(
                f"{type(obj).__name__} is being created in organization {org} but "
                f"points at {owner}; a row cannot be born in another tenant"
            )

    from sqlalchemy import inspect as sa_inspect

    for obj in session.dirty:
        if not isinstance(obj, OrgScoped):
            continue
        state = sa_inspect(obj)
        if state is None:  # pragma: no cover - a mapped instance always has state
            continue
        history = state.attrs.org_id.history
        if not history.has_changes():
            continue
        for new_value in history.added:
            if new_value != org:
                raise TenancyScopeError(
                    f"{type(obj).__name__} is being moved from organization "
                    f"{history.deleted[0] if history.deleted else None} to {new_value} "
                    f"while the active scope is {org}; ownership is not transferable"
                )


def _refuse(scope: str, detail: str) -> None:
    if scope == SCOPE_ORG:
        raise TenancyScopeError(detail)
    raise TenancyScopeError(
        f"organization-owned data touched with no tenant scope: {detail}. "
        "Enter org_scope(...) for tenant work, or system_scope(reason) for maintenance."
    )


def _apply_scope_guc(session: Session, transaction: Any, connection: Connection) -> None:
    """``after_begin`` handler: (re)issue the RLS GUC for this transaction.

    Transaction-local (``is_local => true``): the value is gone the moment the
    transaction ends, so a connection returned to the pool cannot carry one
    request's organization into the next (see the module docstring).
    """
    value = _desired_guc()
    connection.exec_driver_sql(f"SELECT set_config('{ORG_GUC}', %s, true)", (value,))
    connection.info["nx_applied_org"] = value


@contextlib.asynccontextmanager
async def system_write_scope(db: Any, reason: str) -> AsyncIterator[None]:
    """System scope bound to *db*, for rows that have no organization.

    Used by exactly two kinds of write: pre-org security records (a failed login
    for an address that has no account, a refresh-token replay) and nothing
    else. The row is written under the system policy — visible only to system
    scope, never to a tenant — and the previous scope is re-applied afterwards,
    because the GUC is connection state and would otherwise stay on the system
    sentinel for the rest of the transaction.
    """
    with system_scope(reason):
        await apply_scope_to_session(db)
        try:
            yield
        finally:
            pass
    # ``system_scope`` has restored the ContextVars; push the previous scope
    # back onto the connection so the surrounding transaction continues to obey
    # it.
    await apply_scope_to_session(db)


async def apply_scope_to_session(db: Any) -> None:
    """Push the current scope onto *db*'s connection immediately.

    Needed only when a session is deliberately reused across scopes (the
    ``after_begin`` handler covers every other case, because it fires whenever a
    new transaction starts). Sweeps that iterate organizations on one worker use
    this between rows; request paths do not need it — they enter the scope before
    the session's first statement.
    """
    from sqlalchemy import text

    await db.execute(
        text(f"SELECT set_config('{ORG_GUC}', :value, true)"), {"value": _desired_guc()}
    )


_installed = False


def install_tenancy_guards() -> None:
    """Attach the guard and the GUC writer to the ORM session class.

    Idempotent, and deliberately *not* attached to a specific engine: test runs
    rebuild the engine between tests, and a listener that only exists on the
    first engine would silently stop protecting later ones.
    """
    global _installed
    if _installed:
        return
    sa_event.listen(Session, "do_orm_execute", _guard)
    sa_event.listen(Session, "before_flush", _stamp_org_on_flush)
    sa_event.listen(Session, "after_begin", _apply_scope_guc)
    _installed = True


__all__ = [
    "ORG_GUC",
    "RLS_EXEMPT_ORG_TABLES",
    "SCOPE_ORG",
    "SCOPE_SYSTEM",
    "SCOPE_UNSET",
    "SYSTEM_ORG_SENTINEL",
    "SYSTEM_SCOPE_ALLOWED_MODULES",
    "TenancyScopeError",
    "apply_scope_to_session",
    "current_org",
    "current_scope",
    "install_tenancy_guards",
    "org_scope",
    "org_scoped_table_names",
    "require_org",
    "system_scope",
    "system_write_scope",
]
