"""Unit tests for SimulatedDeploymentRunner (async generators, no broker)."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from app.models.enums import LogLevel
from app.providers.deployment_runner import (
    STEP_ORDER,
    RunContext,
    SimulatedDeploymentRunner,
    StepFailure,
    StepLine,
    StepName,
    _pace,
)


def _ctx(version: str = "1.2.3", **overrides: object) -> RunContext:
    fields: dict[str, object] = {
        "project_name": "Core Platform",
        "application_name": "billing-api",
        "environment_name": "production",
        "version": version,
        "git_commit": "a1b2c3d4e5f6a7b8",
        "server_name": "edge-01",
        "secrets": {"STRIPE_KEY": "sk_dummy_value_for_shape_only"},
    }
    fields.update(overrides)
    return RunContext(**fields)  # type: ignore[arg-type]


async def _collect(iterator: AsyncIterator[StepLine]) -> list[StepLine]:
    return [line async for line in iterator]


@pytest.fixture(autouse=True)
def instant_pacing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Remove the per-line sleeps; pacing bounds are asserted separately."""

    async def _no_sleep(_delay: float) -> None: ...

    monkeypatch.setattr("app.providers.deployment_runner.asyncio.sleep", _no_sleep)


# --- plan ---------------------------------------------------------------------------


def test_plan_steps_returns_full_ordered_plan() -> None:
    plan = SimulatedDeploymentRunner().plan_steps(_ctx())
    assert plan == list(STEP_ORDER)
    assert plan is not STEP_ORDER  # callers may mutate their copy
    assert StepName.HEALTH_CHECK in plan


def test_pace_bounds() -> None:
    delays = [_pace(i) for i in range(64)]
    assert min(delays) >= 0.05
    assert max(delays) <= 0.35
    assert _pace(0) == 0.05


def test_runner_satisfies_protocol() -> None:
    from app.providers.deployment_runner import DeploymentRunner

    runner = SimulatedDeploymentRunner()
    # DeploymentRunner is runtime_checkable: method presence is verified.
    assert isinstance(runner, DeploymentRunner)
    assert callable(runner.plan_steps)
    assert callable(runner.execute_step)


# --- happy path ------------------------------------------------------------------------


async def test_every_step_streams_lines_without_failure() -> None:
    runner = SimulatedDeploymentRunner()
    ctx = _ctx()
    for step in STEP_ORDER:
        lines = await _collect(runner.execute_step(step, ctx))
        assert lines, f"{step} produced no output"
        assert all(isinstance(line.level, LogLevel) for line in lines)


async def test_health_check_success_stream() -> None:
    runner = SimulatedDeploymentRunner()
    lines = await _collect(runner.execute_step(StepName.HEALTH_CHECK, _ctx("2.5.0")))
    text = [line.line for line in lines]
    assert any("HTTP/1.1 200 OK" in t for t in text)
    assert any("attempt 1/30" in t for t in text)
    assert not any("503" in t for t in text)


async def test_pull_repo_embeds_slug_and_commit() -> None:
    runner = SimulatedDeploymentRunner()
    lines = await _collect(runner.execute_step(StepName.PULL_REPO, _ctx()))
    text = "\n".join(line.line for line in lines)
    assert "https://git.internal/core-platform/billing-api.git" in text
    assert "HEAD is now at a1b2c3d4e5f6" in text  # commit truncated to 12 chars


async def test_finalize_mentions_application_and_environment() -> None:
    runner = SimulatedDeploymentRunner()
    lines = await _collect(runner.execute_step(StepName.FINALIZE, _ctx()))
    joined = " ".join(line.line for line in lines)
    assert "billing-api@1.2.3" in joined
    assert "production" in joined


async def test_secret_count_is_mentioned_but_never_the_values() -> None:
    runner = SimulatedDeploymentRunner()
    ctx = _ctx(secrets={"A": "value-a", "B": "value-b"})
    lines = await _collect(runner.execute_step(StepName.START_NEW_CONTAINER, ctx))
    joined = "\n".join(line.line for line in lines)
    assert "2 secret reference(s)" in joined
    for value in ("value-a", "value-b"):
        assert value not in joined


# --- failure path -----------------------------------------------------------------------


async def test_broken_version_fails_health_check() -> None:
    runner = SimulatedDeploymentRunner()
    iterator = runner.execute_step(StepName.HEALTH_CHECK, _ctx("9.9.9-broken"))

    seen: list[StepLine] = []
    with pytest.raises(StepFailure) as excinfo:
        async for line in iterator:
            seen.append(line)

    levels = {line.line for line in seen}
    assert any("503 Service Unavailable" in t for t in levels)
    assert not any("HTTP/1.1 200 OK" in t for t in levels)
    message = str(excinfo.value)
    assert "HEALTH_CHECK failed" in message
    assert "billing-api@9.9.9-broken" in message


async def test_broken_version_does_not_affect_other_steps() -> None:
    runner = SimulatedDeploymentRunner()
    ctx = _ctx("1.0.0-broken")
    for step in ("PULL_REPO", "CHECKOUT", "BUILD_IMAGE"):
        lines = await _collect(runner.execute_step(step, ctx))
        assert lines


async def test_unknown_step_raises_step_failure() -> None:
    runner = SimulatedDeploymentRunner()
    with pytest.raises(StepFailure, match="Unknown deployment step"):
        await _collect(runner.execute_step("NOT_A_STEP", _ctx()))


async def test_health_check_failure_message_includes_host() -> None:
    runner = SimulatedDeploymentRunner()
    ctx = _ctx("2.0.0-broken", server_name="db-07")
    with pytest.raises(StepFailure, match="db-07"):
        await _collect(runner.execute_step(StepName.HEALTH_CHECK, ctx))


async def test_default_target_derived_from_slugs() -> None:
    runner = SimulatedDeploymentRunner()
    ctx = _ctx(server_name=None)
    lines = await _collect(runner.execute_step(StepName.STOP_OLD_CONTAINER, ctx))
    assert any("billing-api-production" in line.line for line in lines)
