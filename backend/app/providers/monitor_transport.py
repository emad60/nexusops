"""Pluggable monitor check transports (real HTTP + deterministic simulator).

A transport turns a :class:`~app.models.observability.Monitor` row into a
:class:`CheckOutcome`. Transports never raise for *outcome-level* problems
(timeouts, bad status codes, connection errors) — those are classified into the
result. Unexpected programming errors propagate to the caller.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable
from urllib.parse import urlparse, urlunparse

import httpx

from app.core.errors import UnprocessableEntity
from app.core.ssrf import assert_safe_url_async
from app.models import Monitor
from app.models.enums import CheckResult

#: Response bodies are read up to this cap so a huge page cannot exhaust memory.
MAX_BODY_BYTES = 256 * 1024

#: Stored alongside failures only; enough to spot "wrong page served".
BODY_SNIPPET_LEN = 512

_ERROR_SNIPPET_LEN = 300

#: Redirect hops followed per check; every hop re-runs the SSRF guard.
MAX_REDIRECTS = 5

_ALLOWED_METHODS = frozenset({"GET", "HEAD", "POST", "PUT", "OPTIONS"})


@dataclass(slots=True)
class CheckOutcome:
    """Result of a single monitor check."""

    result: CheckResult
    status_code: int | None = None
    response_time_ms: float | None = None
    error: str = ""
    body_snippet: str = ""


@runtime_checkable
class MonitorTransport(Protocol):
    """Anything that can execute a check for a monitor."""

    async def check(self, monitor: Monitor) -> CheckOutcome:  # pragma: no cover
        ...


def _sanitize_error(exc: BaseException) -> str:
    """Flatten an exception into a bounded single-line string.

    The request URL is already stripped of its query string before it is sent,
    so credentials or signed tokens embedded in a URL cannot leak into stored
    error text; here we only collapse whitespace and bound the length.
    """
    text = " ".join(str(exc).split())
    return text[:_ERROR_SNIPPET_LEN]


def _strip_query(url: str) -> str:
    """Drop the query string so signed tokens never appear in error text."""
    parts = urlparse(url)
    if not parts.query:
        return url
    return urlunparse(parts._replace(query=""))


def strip_query(url: str) -> str:
    """Public alias: redact any query string from a URL before display/persist."""
    return _strip_query(url)


class HTTPMonitorTransport:
    """Real HTTP(S) probe using httpx with per-monitor settings.

    Redirects are followed MANUALLY (never via ``follow_redirects``): httpx
    would happily connect to any 3xx target, letting a public-facing monitor
    URL redirect straight into RFC1918/loopback/metadata addresses and bypass
    the SSRF guard entirely. Each hop is re-validated with
    :func:`assert_safe_url_async` before a connection is attempted.
    """

    async def check(self, monitor: Monitor) -> CheckOutcome:
        headers = {str(k): str(v) for k, v in (monitor.headers or {}).items()}
        url = _strip_query(monitor.url)
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(
                timeout=monitor.timeout_seconds,
                follow_redirects=False,
                verify=not monitor.skip_tls_verify,
            ) as client:
                request = client.build_request(
                    method=monitor.method if monitor.method in _ALLOWED_METHODS else "GET",
                    url=url,
                    headers=headers,
                )
                response = await client.send(request, stream=True)
                redirects = 0
                while monitor.follow_redirects and response.is_redirect:
                    location = response.headers.get("location", "")
                    if not location or redirects >= MAX_REDIRECTS:
                        break
                    next_url = str(httpx.URL(str(response.url)).join(location))
                    try:
                        # SSRF guard applies to EVERY hop, not just the first.
                        await assert_safe_url_async(next_url)
                    except UnprocessableEntity:
                        return CheckOutcome(
                            result=CheckResult.ERROR,
                            response_time_ms=round((time.perf_counter() - started) * 1000, 2),
                            error="redirect target rejected by SSRF guard",
                        )
                    finally:
                        await response.aclose()
                    redirects += 1
                    # 303 always re-issues as GET; other redirects keep method.
                    method = "GET" if response.status_code == 303 else request.method
                    request = client.build_request(
                        method=method if method in _ALLOWED_METHODS else "GET",
                        url=next_url,
                        headers=headers,
                    )
                    response = await client.send(request, stream=True)
        except httpx.TimeoutException:
            elapsed_ms = (time.perf_counter() - started) * 1000
            return CheckOutcome(
                result=CheckResult.TIMEOUT,
                status_code=None,
                response_time_ms=round(elapsed_ms, 2),
                error=f"timeout after {monitor.timeout_seconds:g}s",
            )
        except httpx.HTTPError as exc:
            elapsed_ms = (time.perf_counter() - started) * 1000
            return CheckOutcome(
                result=CheckResult.ERROR,
                status_code=None,
                response_time_ms=round(elapsed_ms, 2),
                error=_sanitize_error(exc),
            )

        body = b""
        try:
            chunks: list[bytes] = []
            total = 0
            async for chunk in response.aiter_bytes():
                chunks.append(chunk)
                total += len(chunk)
                if total >= MAX_BODY_BYTES:
                    break
            body = b"".join(chunks)[:MAX_BODY_BYTES]
            status_code = response.status_code
        except httpx.HTTPError as exc:
            return CheckOutcome(
                result=CheckResult.ERROR,
                status_code=None,
                response_time_ms=round((time.perf_counter() - started) * 1000, 2),
                error=_sanitize_error(exc),
            )
        finally:
            await response.aclose()

        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)

        if monitor.expected_status is not None and status_code != monitor.expected_status:
            return CheckOutcome(
                result=CheckResult.FAILURE,
                status_code=status_code,
                response_time_ms=elapsed_ms,
                error=f"expected {monitor.expected_status}, got {status_code}",
                body_snippet=_decode(body)[:BODY_SNIPPET_LEN],
            )

        expected_body = (monitor.expected_body or "").strip()
        if expected_body and expected_body not in _decode(body):
            return CheckOutcome(
                result=CheckResult.FAILURE,
                status_code=status_code,
                response_time_ms=elapsed_ms,
                error="response body mismatch",
                body_snippet=_decode(body)[:BODY_SNIPPET_LEN],
            )

        # Successes must never persist response content.
        return CheckOutcome(
            result=CheckResult.SUCCESS,
            status_code=status_code,
            response_time_ms=elapsed_ms,
        )


def _decode(body: bytes) -> str:
    return body.decode("utf-8", errors="replace")


class SimulatedTransport:
    """Deterministic fake checker for ``sim://`` monitors and demo environments.

    Outcomes derive from ``sha256(str(monitor.id) + epoch_bucket)`` where the
    bucket rolls every ``interval_seconds``, so a given interval always yields
    the same result — charts and incidents look stable across restarts. No wall
    time is actually slept; latencies are reported values only.
    """

    async def check(self, monitor: Monitor) -> CheckOutcome:
        # Single-segment sim:// URLs land in the host component, multi-segment
        # ones in the path; inspect both so sim://demo/flaky and
        # sim:///demo/flaky behave identically.
        parts = urlparse(monitor.url)
        target = f"{parts.netloc}{parts.path}".lower()
        bucket = int(time.time() // max(int(monitor.interval_seconds), 1))
        digest = hashlib.sha256(f"{monitor.id}{bucket}".encode()).hexdigest()
        roll = int(digest, 16)

        failure = target.endswith("always-down")
        if not failure and "flaky" in target:
            failure = roll % 10 < 3
        if failure:
            return CheckOutcome(
                result=CheckResult.FAILURE,
                status_code=500,
                response_time_ms=float(roll % 400 + 60),
                error="simulated upstream returned 500",
            )

        if "slow" in target:
            latency_ms = float(1500 + roll % 1000)
        else:
            latency_ms = float(20 + roll % 160)
        return CheckOutcome(
            result=CheckResult.SUCCESS,
            status_code=200,
            response_time_ms=latency_ms,
        )


_HTTP_TRANSPORT = HTTPMonitorTransport()
_SIMULATED_TRANSPORT = SimulatedTransport()


def get_transport(monitor: Monitor) -> MonitorTransport:
    """Pick the transport matching the monitor URL scheme."""
    if urlparse(monitor.url).scheme.lower() == "sim":
        return _SIMULATED_TRANSPORT
    return _HTTP_TRANSPORT


def coerce_headers(raw: Any) -> dict[str, str]:
    """Normalise arbitrary JSON-ish header input into a plain str->str dict."""
    if not isinstance(raw, dict):
        return {}
    return {str(k): str(v) for k, v in raw.items()}


__all__ = [
    "BODY_SNIPPET_LEN",
    "MAX_BODY_BYTES",
    "MAX_REDIRECTS",
    "CheckOutcome",
    "HTTPMonitorTransport",
    "MonitorTransport",
    "SimulatedTransport",
    "coerce_headers",
    "get_transport",
    "strip_query",
]
