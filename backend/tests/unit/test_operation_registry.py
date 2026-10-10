"""The operation dispatch whitelist is a contract, not a convention.

``OPERATION_SPECS`` is the entire exec surface an agent can be asked to run, so
its completeness and its permissions are asserted here rather than trusted. The
point is that adding an operation type is a deliberate, reviewed act: it must
come with a spec, a real permission codename and a capability the deployment can
actually confirm — it cannot slip in as an enum member or a params pass-through.
"""

from __future__ import annotations

from dataclasses import replace

import pytest
from app.core.errors import Conflict, UnprocessableEntity
from app.core.permissions import ALL_CODENAMES
from app.models.enums import OperationType
from app.schemas.base import APIModel
from app.schemas.operation import (
    KNOWN_CAPABILITIES,
    OPERATION_SPECS,
    validate_params,
)
from app.services import operation_service

#: Types the companion architecture documents reserve for a later phase
#: (certificates, secret delivery). None may exist yet: each needs the subsystem
#: it belongs to, and shipping the name alone would create a pass-through.
#: Phase 4's nginx surface left this list deliberately — see the positive test
#: below, which is what replaced it.
RESERVED_LATER_PHASE_TYPES = (
    "certificate.issue",
    "certificate.renew",
    "certificate.install",
    "secret.env.apply",
)


def test_every_operation_type_has_exactly_one_spec() -> None:
    assert set(OPERATION_SPECS) == set(OperationType)


def test_every_spec_permission_is_a_registered_codename() -> None:
    for op_type, spec in OPERATION_SPECS.items():
        assert spec.permission in ALL_CODENAMES, f"{op_type} names unknown {spec.permission!r}"
        assert spec.timeout_seconds > 0


def test_no_generic_execute_grant_is_reachable() -> None:
    """The framework reuses existing codenames; a generic exec grant must not exist."""
    assert "node.execute" not in ALL_CODENAMES
    for spec in OPERATION_SPECS.values():
        assert not spec.permission.endswith(".execute")


def test_no_reserved_later_phase_type_is_registered() -> None:
    values = {str(member) for member in OperationType}
    for reserved in RESERVED_LATER_PHASE_TYPES:
        assert reserved not in values
        assert reserved not in {str(op_type) for op_type in OPERATION_SPECS}


def test_phase4_nginx_operations_are_registered_and_gated() -> None:
    """Phase 4 ships exactly the three nginx ops, each gated on the capability.

    This is the other half of the reservation above: the names may exist now, but
    only as reviewed specs on a capability a node can actually report — never as
    an enum member or a params pass-through.
    """
    nginx_ops = {
        OperationType.NGINX_BOOTSTRAP,
        OperationType.NGINX_APPLY,
        OperationType.NGINX_STATUS,
    }
    assert nginx_ops <= set(OPERATION_SPECS)
    for op_type in nginx_ops:
        spec = OPERATION_SPECS[op_type]
        assert spec.capability == "nginx"
        assert spec.params_model.model_config.get("extra") == "forbid", op_type


def test_specs_reject_unknown_params() -> None:
    """Every params model must forbid extras, so nothing reaches the agent unseen."""
    for op_type, spec in OPERATION_SPECS.items():
        assert issubclass(spec.params_model, APIModel)
        assert spec.params_model.model_config.get("extra") == "forbid", op_type
        with pytest.raises(UnprocessableEntity) as exc:
            validate_params(op_type, {"__unexpected__": "value"})
        assert exc.value.code == "OPERATION_PARAMS_INVALID"


def test_every_declared_capability_is_in_the_known_vocabulary() -> None:
    """Every spec's capability must be one the platform knows how to gate on.

    Since Phase 3 each node reports capabilities at hello and dispatch checks
    them per node; this asserts the *vocabulary* is closed so a spec cannot name
    a capability nobody can report.
    """
    assert {spec.capability for spec in OPERATION_SPECS.values()} <= KNOWN_CAPABILITIES


def test_an_unverified_capability_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    """A type whose capability cannot be confirmed must not be dispatchable."""
    spec = OPERATION_SPECS[OperationType.CONTAINER_START]
    monkeypatch.setitem(
        OPERATION_SPECS,
        OperationType.CONTAINER_START,
        replace(spec, capability="tls"),
    )

    with pytest.raises(Conflict) as exc:
        operation_service.ensure_dispatchable(OperationType.CONTAINER_START)
    assert exc.value.code == "NODE_CAPABILITY_UNVERIFIED"


def test_current_types_are_dispatchable() -> None:
    for op_type in OperationType:
        assert operation_service.ensure_dispatchable(op_type).permission in ALL_CODENAMES
