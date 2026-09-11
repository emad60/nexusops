"""Deployment runner port plus a faithful simulated implementation.

``DeploymentRunner`` is the seam between the deployment engine and whatever
actually ships code. A real :class:`LocalDockerRunner` adapter (docker SDK /
SSH to a target server) is a **reserved interface that is deliberately NOT
implemented in v1** — shipping half of a real deploy path would be worse than
an honest simulation.

:class:`SimulatedDeploymentRunner` therefore covers every product flow end to
end: staged build output, per-line pacing, health-check gating and failure
propagation. Queues, live log frames, cancellation, rollback, alerting and the
audit trail are all exercised for real; only the shell commands are pretend.
"""

from __future__ import annotations

import asyncio
import secrets as secrets_module
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from app.models.enums import LogLevel

#: Per-line sleep bounds; every step finishes in well under 2.5 seconds.
_LINE_FLOOR_SECONDS = 0.05
_LINE_SPREAD_MS = 300


def _pace(position: int) -> float:
    """Deterministic per-line delay between 0.05s and 0.35s."""
    return _LINE_FLOOR_SECONDS + ((position * 37) % (_LINE_SPREAD_MS // 10 + 1)) / 100


class StepName:
    """Canonical step identifiers stored on :class:`DeploymentStep` rows."""

    PULL_REPO = "PULL_REPO"
    CHECKOUT = "CHECKOUT"
    BUILD_IMAGE = "BUILD_IMAGE"
    STOP_OLD_CONTAINER = "STOP_OLD_CONTAINER"
    START_NEW_CONTAINER = "START_NEW_CONTAINER"
    HEALTH_CHECK = "HEALTH_CHECK"
    FINALIZE = "FINALIZE"


#: Ordered execution plan produced by ``plan_steps``.
STEP_ORDER: tuple[str, ...] = (
    StepName.PULL_REPO,
    StepName.CHECKOUT,
    StepName.BUILD_IMAGE,
    StepName.STOP_OLD_CONTAINER,
    StepName.START_NEW_CONTAINER,
    StepName.HEALTH_CHECK,
    StepName.FINALIZE,
)


@dataclass(slots=True)
class RunContext:
    """Everything a runner needs to execute one deployment."""

    project_name: str
    application_name: str
    environment_name: str
    version: str
    git_commit: str = ""
    server_name: str | None = None
    #: Resolved secret values keyed by name. Never logged or persisted raw.
    secrets: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class StepLine:
    """One streamed output line for a step."""

    line: str
    level: LogLevel = LogLevel.INFO


class StepFailure(Exception):
    """Raised by a runner when a step fails irrecoverably."""


@runtime_checkable
class DeploymentRunner(Protocol):
    """Adapter interface implemented by real (future) and simulated runners."""

    def plan_steps(self, ctx: RunContext) -> list[str]:
        """Return the ordered step names for this run."""
        ...

    def execute_step(self, step_name: str, ctx: RunContext) -> AsyncIterator[StepLine]:
        """Stream output lines for *step_name*; raise StepFailure to fail it."""
        ...


def _slug(value: str) -> str:
    cleaned = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    return "-".join(part for part in cleaned.split("-") if part) or "app"


def _commit_short(ctx: RunContext) -> str:
    return ctx.git_commit[:12] if ctx.git_commit else ctx.version


class SimulatedDeploymentRunner:
    """Staged docker-style simulation used by v1 deployments."""

    def plan_steps(self, ctx: RunContext) -> list[str]:
        return list(STEP_ORDER)

    async def execute_step(self, step_name: str, ctx: RunContext) -> AsyncIterator[StepLine]:
        handlers = {
            StepName.PULL_REPO: self._pull_repo,
            StepName.CHECKOUT: self._checkout,
            StepName.BUILD_IMAGE: self._build_image,
            StepName.STOP_OLD_CONTAINER: self._stop_old_container,
            StepName.START_NEW_CONTAINER: self._start_new_container,
            StepName.HEALTH_CHECK: self._health_check,
            StepName.FINALIZE: self._finalize,
        }
        handler = handlers.get(step_name)
        if handler is None:
            raise StepFailure(f"Unknown deployment step: {step_name}")
        async for line in handler(ctx):
            yield line

    async def _stream(self, lines: list[tuple[str, LogLevel]]) -> AsyncIterator[StepLine]:
        for position, (text, level) in enumerate(lines):
            await asyncio.sleep(_pace(position))
            yield StepLine(line=text, level=level)

    def _pull_repo(self, ctx: RunContext) -> AsyncIterator[StepLine]:
        url = f"https://git.internal/{_slug(ctx.project_name)}/{_slug(ctx.application_name)}.git"
        return self._stream(
            [
                (f"Cloning {url} into workspace", LogLevel.INFO),
                ("remote: Enumerating objects: 148, done.", LogLevel.DEBUG),
                ("remote: Counting objects: 100% (148/148), done.", LogLevel.INFO),
                (
                    "Receiving objects: 100% (148/148), 1.21 MiB | 9.10 MiB/s, done.",
                    LogLevel.INFO,
                ),
                ("Resolving deltas: 100% (76/76), done.", LogLevel.INFO),
                (f"HEAD is now at {_commit_short(ctx)}", LogLevel.INFO),
                ("Repository cache warm; fetch completed in 0.8s", LogLevel.DEBUG),
            ]
        )

    def _checkout(self, ctx: RunContext) -> AsyncIterator[StepLine]:
        return self._stream(
            [
                (f"Checking out ref '{ctx.version}'", LogLevel.INFO),
                (f"HEAD detached at {_commit_short(ctx)}", LogLevel.INFO),
                ("Submodules: none configured", LogLevel.DEBUG),
                ("Working tree clean after checkout", LogLevel.INFO),
            ]
        )

    def _build_image(self, ctx: RunContext) -> AsyncIterator[StepLine]:
        digest = secrets_module.token_hex(6)
        tag = f"{_slug(ctx.application_name)}:{ctx.version}"
        return self._stream(
            [
                ("Sending build context to Docker daemon  4.096 kB", LogLevel.INFO),
                ("Step 1/4 : FROM python:3.13-slim", LogLevel.INFO),
                (" ---> 9a4b5c6d7e8f", LogLevel.DEBUG),
                ("Step 2/4 : COPY . /app", LogLevel.INFO),
                (
                    "Step 3/4 : RUN pip install --no-cache-dir -r requirements.txt",
                    LogLevel.INFO,
                ),
                (
                    f"Successfully installed agent-tools-{secrets_module.token_hex(4)}",
                    LogLevel.INFO,
                ),
                ('Step 4/4 : CMD ["python", "-m", "app"]', LogLevel.INFO),
                ("Removing intermediate container 7c1e9a2b4d5f", LogLevel.DEBUG),
                (f"Successfully built sha256:{digest}", LogLevel.INFO),
                (f"Tagging image {tag}", LogLevel.INFO),
            ]
        )

    def _stop_old_container(self, ctx: RunContext) -> AsyncIterator[StepLine]:
        target = ctx.server_name or f"{_slug(ctx.application_name)}-{_slug(ctx.environment_name)}"
        return self._stream(
            [
                (f"Stopping previous container on {target}", LogLevel.INFO),
                ("SIGTERM dispatched to PID 1", LogLevel.DEBUG),
                ("Connections drained: 0 active after 200ms", LogLevel.INFO),
                ("Previous container exited cleanly (code 0)", LogLevel.INFO),
                (f"Preserved as {target}-prev for rollback window", LogLevel.INFO),
            ]
        )

    def _start_new_container(self, ctx: RunContext) -> AsyncIterator[StepLine]:
        target = ctx.server_name or f"{_slug(ctx.application_name)}-{_slug(ctx.environment_name)}"
        return self._stream(
            [
                (
                    f"Creating container {target} from {_slug(ctx.application_name)}:{ctx.version}",
                    LogLevel.INFO,
                ),
                (f"Container created (id sha256:{secrets_module.token_hex(6)})", LogLevel.DEBUG),
                ("Starting container", LogLevel.INFO),
                ("docker inspect -> State.Status=RUNNING", LogLevel.INFO),
                ("Port mapping 0.0.0.0:8000->8000/tcp", LogLevel.INFO),
                (
                    f"Injected {len(ctx.secrets)} secret reference(s) as env vars",
                    LogLevel.DEBUG,
                ),
            ]
        )

    async def _health_check(self, ctx: RunContext) -> AsyncIterator[StepLine]:
        host = ctx.server_name or "127.0.0.1"
        probe = f"curl -fsS -o /dev/null -w '%{{http_code}}' http://{host}/"
        lines: list[tuple[str, LogLevel]] = [
            (f"Probing http://{host}/ (timeout 2s)", LogLevel.INFO),
            (probe, LogLevel.DEBUG),
        ]
        if ctx.version.endswith("-broken"):
            # Explicit E2E/demo hook: any version tagged '-broken' fails health.
            lines += [
                ("HTTP/1.1 503 Service Unavailable", LogLevel.WARN),
                ("Retrying in 500ms (attempt 2/30)", LogLevel.INFO),
                ("HTTP/1.1 503 Service Unavailable", LogLevel.WARN),
                (
                    "Health check failed after 3 attempts: upstream returned 503",
                    LogLevel.ERROR,
                ),
            ]
            async for line in self._stream(lines):
                yield line
            raise StepFailure(
                f"HEALTH_CHECK failed: application {ctx.application_name}@{ctx.version} "
                f"never became healthy on {host} (503 after 3 attempts)"
            )
        lines += [
            ("HTTP/1.1 200 OK", LogLevel.INFO),
            ("Health check passed on attempt 1/30", LogLevel.INFO),
        ]
        async for line in self._stream(lines):
            yield line

    def _finalize(self, ctx: RunContext) -> AsyncIterator[StepLine]:
        return self._stream(
            [
                (
                    f"Marking {ctx.application_name}@{ctx.version} active on "
                    f"{ctx.environment_name}",
                    LogLevel.INFO,
                ),
                ("Deployment metadata recorded", LogLevel.DEBUG),
                (
                    f"Deployment of {ctx.application_name} to {ctx.environment_name} complete",
                    LogLevel.INFO,
                ),
            ]
        )
