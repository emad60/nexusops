"""Unit tests for monitor check transports (simulated + URL hygiene helpers)."""

from __future__ import annotations

from typing import Any, ClassVar

import httpx
import pytest
from app.models import Monitor
from app.models.enums import CheckResult
from app.providers.monitor_transport import (
    BODY_SNIPPET_LEN,
    MAX_BODY_BYTES,
    HTTPMonitorTransport,
    SimulatedTransport,
    _sanitize_error,
    _strip_query,
    coerce_headers,
    get_transport,
)

#: Fixed UUID keeps the sha256 rolls reproducible across runs.
MONITOR_ID = "00000000-0000-0000-0000-00000000abcd"
INTERVAL = 60


def _monitor(url: str, **overrides: Any) -> Monitor:
    # follow_redirects/expected_status match the schema defaults a flushed row
    # would carry; unflushed ORM instances do not apply column defaults.
    fields: dict[str, Any] = {
        "url": url,
        "interval_seconds": INTERVAL,
        "follow_redirects": True,
        "expected_status": 200,
    }
    fields.update(overrides)
    return Monitor(id=MONITOR_ID, **fields)


class FakeClock:
    """Stands in for time.time() so sim buckets are fully deterministic."""

    def __init__(self) -> None:
        self.now = 0.0

    def advance_to_bucket(self, bucket: int, interval: int = INTERVAL) -> None:
        self.now = float(bucket * interval)


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> FakeClock:
    import app.providers.monitor_transport as mt

    fake = FakeClock()
    monkeypatch.setattr(mt.time, "time", lambda: fake.now)
    return fake


async def _check(transport: SimulatedTransport, monitor: Monitor) -> tuple[str, int | None]:
    outcome = await transport.check(monitor)
    return outcome.result.value, outcome.status_code


# --- always-down ---------------------------------------------------------------------


@pytest.mark.parametrize("bucket", [0, 1, 7, 123])
async def test_always_down_fails_regardless_of_bucket(clock: FakeClock, bucket: int) -> None:
    clock.advance_to_bucket(bucket)
    transport = SimulatedTransport()
    result, status = await _check(transport, _monitor("sim://demo/always-down"))
    assert result == "FAILURE" and status == 500


async def test_always_down_carries_error_text(clock: FakeClock) -> None:
    clock.advance_to_bucket(3)
    outcome = await SimulatedTransport().check(_monitor("sim://demo/always-down"))
    assert outcome.error
    assert outcome.response_time_ms is not None and outcome.response_time_ms >= 60


# --- flaky ~30% -------------------------------------------------------------------------


async def test_flaky_stays_between_20_and_40_percent_over_200_buckets(
    clock: FakeClock,
) -> None:
    transport = SimulatedTransport()
    monitor = _monitor("sim://demo/flaky")
    failures = 0
    for bucket in range(200):
        clock.advance_to_bucket(bucket)
        result, _status = await _check(transport, monitor)
        failures += result == "FAILURE"
    rate = failures / 200
    assert 0.20 <= rate <= 0.40, f"flaky failure rate {rate:.2%} outside [20%, 40%]"


async def test_flaky_is_deterministic_per_bucket(clock: FakeClock) -> None:
    transport = SimulatedTransport()
    monitor = _monitor("sim://demo/flaky")
    for bucket in (0, 5, 42):
        clock.advance_to_bucket(bucket)
        first = await transport.check(monitor)
        second = await transport.check(monitor)
        assert first == second


# --- slow / normal --------------------------------------------------------------------------


async def test_slow_target_reports_high_latency(clock: FakeClock) -> None:
    clock.advance_to_bucket(9)
    outcome = await SimulatedTransport().check(_monitor("sim://demo/slow"))
    assert outcome.result == CheckResult.SUCCESS
    assert outcome.status_code == 200
    assert outcome.response_time_ms is not None
    assert outcome.response_time_ms >= 1500


async def test_normal_target_reports_modest_latency(clock: FakeClock) -> None:
    clock.advance_to_bucket(11)
    outcome = await SimulatedTransport().check(_monitor("sim://demo/web"))
    assert outcome.result == CheckResult.SUCCESS
    assert outcome.response_time_ms is not None
    assert 20.0 <= outcome.response_time_ms < 180.0


@pytest.mark.parametrize("url", ["sim:///demo/always-down", "sim://demo/always-down"])
async def test_multi_segment_paths_behave_like_host_form(clock: FakeClock, url: str) -> None:
    clock.advance_to_bucket(4)
    result, _status = await _check(SimulatedTransport(), _monitor(url))
    assert result == "FAILURE"


async def test_zero_interval_does_not_divide_by_zero(clock: FakeClock) -> None:
    clock.now = 1234.5
    result, _status = await _check(
        SimulatedTransport(), _monitor("sim://demo/always-down", interval_seconds=0)
    )
    assert result == "FAILURE"


# --- transport selection & helpers --------------------------------------------------------------


def test_get_transport_selects_by_scheme() -> None:
    assert isinstance(get_transport(_monitor("sim://demo/x")), SimulatedTransport)
    assert isinstance(get_transport(_monitor("https://example.com/")), HTTPMonitorTransport)
    assert isinstance(get_transport(_monitor("http://example.com/")), HTTPMonitorTransport)


def test_constants_are_sane() -> None:
    assert MAX_BODY_BYTES == 256 * 1024
    assert 0 < BODY_SNIPPET_LEN < MAX_BODY_BYTES


def test_strip_query_removes_signed_tokens() -> None:
    url = "https://example.com/path?token=supersecret&x=1"
    stripped = _strip_query(url)
    assert "token" not in stripped and "supersecret" not in stripped
    assert stripped.startswith("https://example.com/path")


def test_strip_query_leans_on_clean_urls() -> None:
    assert _strip_query("https://example.com/plain") == "https://example.com/plain"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (None, {}),
        ([1, 2], {}),
        ("nope", {}),
        ({"A": 1}, {"A": "1"}),
        ({1: True}, {"1": "True"}),
    ],
)
def test_coerce_headers(raw: Any, expected: dict[str, str]) -> None:
    assert coerce_headers(raw) == expected


def test_sanitize_error_flattens_and_bounds() -> None:
    text = _sanitize_error(RuntimeError("line1\n  line2\t tab"))
    assert text == "line1 line2 tab"
    huge = _sanitize_error(RuntimeError("x" * 5000))
    assert len(huge) <= 300


# --- redirect handling: every hop re-runs the SSRF guard (regression) -------------
#
# httpx's built-in follow_redirects would connect to any 3xx target — letting a
# public monitor URL redirect straight into RFC1918/loopback/metadata space and
# bypass the guard. The transport must therefore follow redirects manually and
# re-validate each Location before connecting.


class _FakeResponse:
    def __init__(
        self, status_code: int, url: str, headers: dict | None = None, content: bytes = b"ok"
    ):
        self.status_code = status_code
        self.url = httpx.URL(url)
        self.headers = httpx.Headers(headers or {})
        self._content = content
        self.closed = False

    @property
    def is_redirect(self) -> bool:
        return 300 <= self.status_code < 400 and "location" in self.headers

    async def aiter_bytes(self):
        yield self._content

    async def aclose(self) -> None:
        self.closed = True


class _FakeRequestObj:
    def __init__(self, method: str, url: str) -> None:
        self.method = method
        self.url = url


class _FakeAsyncClient:
    """Scripted httpx.AsyncClient: responses keyed by absolute request URL."""

    script: ClassVar[dict[str, _FakeResponse]] = {}
    sent_urls: ClassVar[list[str]] = []
    init_kwargs: ClassVar[dict] = {}

    def __init__(self, **kwargs):
        type(self).init_kwargs = kwargs

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    def build_request(self, method, url, headers=None):
        return _FakeRequestObj(method, str(url))

    async def send(self, request, stream=False):
        url = request.url
        type(self).sent_urls.append(url)
        try:
            return type(self).script[url]
        except KeyError:
            raise AssertionError(f"unexpected connection attempt to {url}") from None


def _script_client(monkeypatch: pytest.MonkeyPatch, script: dict[str, _FakeResponse]):
    import app.providers.monitor_transport as mt

    _FakeAsyncClient.script = script
    _FakeAsyncClient.sent_urls = []
    _FakeAsyncClient.init_kwargs = {}
    monkeypatch.setattr(mt.httpx, "AsyncClient", _FakeAsyncClient)


async def test_redirect_to_private_target_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """A 302 from a public URL into link-local/metadata space must be refused."""
    _script_client(
        monkeypatch,
        {
            "http://public.example/start": _FakeResponse(
                302,
                "http://public.example/start",
                {"location": "http://169.254.169.254/latest/meta-data/"},
            ),
        },
    )
    monitor = _monitor("http://public.example/start", follow_redirects=True)
    outcome = await HTTPMonitorTransport().check(monitor)

    assert outcome.result is CheckResult.ERROR
    assert "redirect target rejected" in outcome.error
    # The private target must never have been connected to.
    assert all("169.254.169.254" not in url for url in _FakeAsyncClient.sent_urls)


async def test_redirect_to_loopback_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    _script_client(
        monkeypatch,
        {
            "http://public.example/x": _FakeResponse(
                302, "http://public.example/x", {"location": "http://127.0.0.1:8080/admin"}
            ),
        },
    )
    outcome = await HTTPMonitorTransport().check(_monitor("http://public.example/x"))
    assert outcome.result is CheckResult.ERROR
    assert "redirect target rejected" in outcome.error
    assert all("127.0.0.1" not in url for url in _FakeAsyncClient.sent_urls)


async def test_public_redirect_chain_is_followed(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.providers.monitor_transport as mt

    async def permissive_guard(url: str):  # DNS offline in unit tests
        return None

    monkeypatch.setattr(mt, "assert_safe_url_async", permissive_guard)
    _script_client(
        monkeypatch,
        {
            "http://public.example/start": _FakeResponse(
                302, "http://public.example/start", {"location": "/step-2"}
            ),
            "http://public.example/step-2": _FakeResponse(
                200, "http://public.example/step-2", content=b"healthy"
            ),
        },
    )
    monitor = _monitor("http://public.example/start", follow_redirects=True, expected_status=200)
    outcome = await HTTPMonitorTransport().check(monitor)

    assert outcome.result is CheckResult.SUCCESS
    assert outcome.status_code == 200
    assert _FakeAsyncClient.sent_urls[-1] == "http://public.example/step-2"


async def test_redirects_disabled_stops_at_first_response(monkeypatch: pytest.MonkeyPatch) -> None:
    _script_client(
        monkeypatch,
        {
            "http://public.example/start": _FakeResponse(
                302, "http://public.example/start", {"location": "/elsewhere"}
            ),
        },
    )
    monitor = _monitor("http://public.example/start", follow_redirects=False)
    outcome = await HTTPMonitorTransport().check(monitor)

    # No follow: the 302 itself is judged against expected_status and the
    # redirect target is never requested.
    assert outcome.result is CheckResult.FAILURE
    assert _FakeAsyncClient.sent_urls == ["http://public.example/start"]


async def test_httpx_client_is_created_without_auto_redirects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Defense in depth: even the httpx client must never auto-follow."""
    _script_client(monkeypatch, {})
    with pytest.raises(AssertionError):
        # Nothing is scripted, so the fake send raises; construction kwargs
        # are captured either way.
        await HTTPMonitorTransport().check(_monitor("http://public.example/x"))
    assert _FakeAsyncClient.init_kwargs.get("follow_redirects") is False
