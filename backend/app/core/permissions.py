"""Permission registry and role matrix.

Permissions are *data*: the registry below is seeded into the database and all
authorization checks resolve against role→permission rows (with a wildcard
``*`` supported for the Owner role). No ``if user.role == "admin"`` checks are
allowed anywhere in the codebase — use :func:`user_has_permission` or the
``require_permission(...)`` dependency.
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass

WILDCARD = "*"


@dataclass(frozen=True, slots=True)
class PermissionSpec:
    codename: str
    group: str
    description: str


PERMISSIONS: tuple[PermissionSpec, ...] = (
    # users & roles
    PermissionSpec("user.read", "Access Control", "List and view users"),
    PermissionSpec(
        "user.manage", "Access Control", "Create, update, deactivate users; assign roles"
    ),
    PermissionSpec("role.read", "Access Control", "List roles and their permissions"),
    PermissionSpec("role.manage", "Access Control", "Create and modify roles"),
    PermissionSpec("audit.read", "Access Control", "View audit logs"),
    # servers
    PermissionSpec("server.read", "Servers", "List and view servers"),
    PermissionSpec("server.create", "Servers", "Register servers"),
    PermissionSpec("server.update", "Servers", "Edit servers"),
    PermissionSpec("server.delete", "Servers", "Remove servers"),
    PermissionSpec("credential.write", "Servers", "Store / rotate server credentials"),
    # docker
    PermissionSpec("container.read", "Containers", "List containers, images, volumes, networks"),
    PermissionSpec("container.logs", "Containers", "Stream container logs"),
    PermissionSpec(
        "container.lifecycle", "Containers", "Start / stop / restart / pause containers"
    ),
    PermissionSpec("container.remove", "Containers", "Remove containers (destructive)"),
    # delivery
    PermissionSpec("project.read", "Delivery", "View projects and applications"),
    PermissionSpec(
        "project.manage", "Delivery", "Create / edit projects, applications, environments"
    ),
    PermissionSpec("deployment.read", "Delivery", "View deployments and their logs"),
    PermissionSpec("deployment.create", "Delivery", "Trigger deployments"),
    PermissionSpec("deployment.cancel", "Delivery", "Cancel running deployments"),
    PermissionSpec("deployment.rollback", "Delivery", "Roll back to previous versions"),
    # monitoring
    PermissionSpec("monitor.read", "Monitoring", "View monitors, checks, incidents"),
    PermissionSpec("monitor.manage", "Monitoring", "Create / edit / delete monitors"),
    PermissionSpec("incident.action", "Monitoring", "Acknowledge / resolve incidents"),
    # notifications
    PermissionSpec("channel.read", "Notifications", "View notification channels"),
    PermissionSpec("channel.manage", "Notifications", "Create / edit / delete channels"),
    # observability reads
    PermissionSpec("metric.read", "Observability", "View metrics"),
    PermissionSpec("log.read", "Observability", "Read persisted logs"),
    PermissionSpec("event.read", "Observability", "View system events"),
    # secrets
    PermissionSpec("secret.read", "Secrets", "List secrets (metadata only)"),
    PermissionSpec("secret.write", "Secrets", "Create / rotate / delete secrets"),
)

ALL_CODENAMES: frozenset[str] = frozenset(p.codename for p in PERMISSIONS)


def _perms(*codenames: str) -> list[str]:
    return list(codenames)


#: Seed matrix for the five built-in roles. Owner holds the wildcard.
ROLE_MATRIX: dict[str, list[str]] = {
    "Owner": [WILDCARD],
    "Admin": _perms(
        "user.read",
        "user.manage",
        "role.read",
        "audit.read",
        "server.read",
        "server.create",
        "server.update",
        "server.delete",
        "credential.write",
        "container.read",
        "container.logs",
        "container.lifecycle",
        "container.remove",
        "project.read",
        "project.manage",
        "deployment.read",
        "deployment.create",
        "deployment.cancel",
        "deployment.rollback",
        "monitor.read",
        "monitor.manage",
        "incident.action",
        "channel.read",
        "channel.manage",
        "metric.read",
        "log.read",
        "event.read",
        "secret.read",
        "secret.write",
    ),
    "Operator": _perms(
        "user.read",
        "audit.read",
        "server.read",
        "server.create",
        "server.update",
        "server.delete",
        "credential.write",
        "container.read",
        "container.logs",
        "container.lifecycle",
        "container.remove",
        "project.read",
        "deployment.read",
        "deployment.create",
        "deployment.cancel",
        "deployment.rollback",
        "monitor.read",
        "monitor.manage",
        "incident.action",
        "channel.read",
        "channel.manage",
        "metric.read",
        "log.read",
        "event.read",
        "secret.read",
    ),
    "Developer": _perms(
        "server.read",
        "container.read",
        "container.logs",
        "project.read",
        "deployment.read",
        "deployment.create",
        "deployment.cancel",
        "monitor.read",
        "monitor.manage",
        "incident.action",
        "channel.read",
        "metric.read",
        "log.read",
        "event.read",
        "secret.read",
    ),
    "Viewer": _perms(
        "server.read",
        "container.read",
        "container.logs",
        "project.read",
        "deployment.read",
        "monitor.read",
        "channel.read",
        "metric.read",
        "log.read",
        "event.read",
    ),
}

SYSTEM_ROLES: tuple[str, ...] = tuple(ROLE_MATRIX)


def scope_matches(scopes: list[str], required: str) -> bool:
    """Check an API-key scope list against a required permission.

    Supports exact match plus wildcards: ``*``, ``server.*``.
    """
    for scope in scopes:
        if scope == WILDCARD or scope == required:
            return True
        if scope.endswith("*") and fnmatch.fnmatchcase(required, scope):
            return True
    return False


def permission_exists(codename: str) -> bool:
    return codename in ALL_CODENAMES
