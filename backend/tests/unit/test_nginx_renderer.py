"""The renderer: determinism, the injection boundary, and the Phase 4 HTTP-only rule.

Golden assertions are used deliberately. A snapshot is the only way to notice
that a template change silently started emitting something new — and the thing it
might start emitting is exactly what these tests forbid (an ``ssl_`` directive, a
redirect to https, an unquoted user value, a second ``default_server``).
"""

from __future__ import annotations

import pytest
from app.core.dnsname import InvalidName, canonicalize_name
from app.providers.nginx import NginxProvider, RenderError
from app.providers.proxy import ResolvedNode, ResolvedRoute
from app.schemas.proxy import (
    MANAGED_CONF_PATH,
    MAX_BUNDLE_FILES,
    MAX_FILE_BYTES,
    MAX_REDIRECT_CODE,
    MAX_ROUTES_PER_NODE,
    ROUTES_DIR,
    BundleFile,
    NginxApplyParams,
    NginxBundle,
    RateLimit,
    RouteHeader,
    RouteRedirect,
    fingerprint_files,
    is_allowed_bundle_path,
)
from pydantic import ValidationError

NODE = ResolvedNode(id="11111111-1111-1111-1111-111111111111", name="node-a")


def route(route_id: str = "a" * 32, **overrides) -> ResolvedRoute:
    base = {
        "id": route_id,
        "hostname": "app.example.com",
        "path": "/",
        "upstream_host": "127.0.0.1",
        "upstream_port": 8081,
    }
    base.update(overrides)
    return ResolvedRoute(**base)


@pytest.fixture
def provider() -> NginxProvider:
    return NginxProvider()


def test_render_is_deterministic_and_order_independent(provider: NginxProvider) -> None:
    routes = [
        route("1" * 32, hostname="b.example.com"),
        route("2" * 32, hostname="a.example.com", path="/api"),
    ]
    first = provider.render(NODE, routes)
    second = provider.render(NODE, list(reversed(routes)))
    third = provider.render(NODE, routes)
    assert first.bundle_id == second.bundle_id == third.bundle_id
    assert [f.path for f in first.files] == [f.path for f in second.files]
    assert [f.content for f in first.files] == [f.content for f in second.files]


def test_bundle_shape_is_the_documented_tree(provider: NginxProvider) -> None:
    bundle = provider.render(NODE, [route()])
    paths = [f.path for f in bundle.files]
    assert paths[0] == MANAGED_CONF_PATH
    assert len(paths) == 2
    assert paths[1].startswith(ROUTES_DIR + "/")
    assert paths[1].endswith(".conf")
    assert bundle.manifest == ["a" * 32]
    assert bundle.provider == "nginx"


def test_default_server_answers_444_and_never_proxies(provider: NginxProvider) -> None:
    bundle = provider.render(NODE, [])
    conf = next(f.content for f in bundle.files if f.path == MANAGED_CONF_PATH)
    assert "listen 80 default_server;" in conf
    assert "return 444;" in conf
    # No route may be reachable through the catch-all block.
    default_block = conf.split("server {", 1)[1]
    assert "proxy_pass" not in default_block


def test_golden_route_fragment(provider: NginxProvider) -> None:
    bundle = provider.render(
        NODE,
        [
            route(
                "ab" * 16,
                headers=(
                    {"name": "X-Frame-Options", "value": "DENY", "target": "response"},
                    {"name": "X-App-Version", "value": "42", "target": "proxy"},
                ),
            )
        ],
    )
    fragment = bundle.files[1].content
    assert "listen 80;" in fragment
    assert "server_name app.example.com;" in fragment
    assert "proxy_pass http://127.0.0.1:8081;" in fragment
    assert 'add_header X-Frame-Options "DENY" always;' in fragment
    assert 'proxy_set_header X-App-Version "42";' in fragment
    # The standard forwarding headers are always present and never optional.
    assert "proxy_set_header Host $host;" in fragment
    assert "proxy_set_header X-Forwarded-Proto $scheme;" in fragment
    assert "proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;" in fragment


def test_no_tls_or_certificate_material_anywhere(provider: NginxProvider) -> None:
    bundle = provider.render(
        NODE,
        [route(), route("c" * 32, hostname="api.example.com", path="/v1")],
    )
    blob = "\n".join(f.content for f in bundle.files).lower()
    for forbidden in (
        "ssl_certificate",
        "ssl_",
        "listen 443",
        "https://",
        "letsencrypt",
        "acme",
        "certificate_id",
        "private_key",
        "proxy_pass https",
    ):
        assert forbidden not in blob, f"Phase 4 must not render {forbidden!r}"


def test_fragment_names_are_derived_from_the_route_id(provider: NginxProvider) -> None:
    first = provider.render(NODE, [route("a" * 32)])
    second = provider.render(NODE, [route("b" * 32)])
    assert first.files[1].path != second.files[1].path
    assert NginxProvider.route_file_path("a" * 32) == first.files[1].path


def test_trailing_slash_and_path_prefix_render_verbatim(provider: NginxProvider) -> None:
    bundle = provider.render(NODE, [route(path="/api/v2")])
    assert "location /api/v2 {" in bundle.files[1].content


def test_wildcard_domain_renders_a_wildcard_server_name(provider: NginxProvider) -> None:
    bundle = provider.render(NODE, [route(hostname="*.example.com")])
    assert "server_name *.example.com;" in bundle.files[1].content


def test_rate_limit_zone_and_directive(provider: NginxProvider) -> None:
    bundle = provider.render(
        NODE, [route(rate_limit={"requests": 30, "window": "1s", "burst": 10})]
    )
    conf = bundle.files[0].content
    fragment = bundle.files[1].content
    assert "limit_req_zone $binary_remote_addr zone=nx_" in conf
    assert "rate=30r/s;" in conf
    assert "burst=10 nodelay;" in fragment


def test_rate_limit_zones_do_not_leak_between_renders(provider: NginxProvider) -> None:
    with_limit = provider.render(NODE, [route(rate_limit={"requests": 5, "window": "1s"})])
    without = provider.render(NODE, [route()])
    assert "limit_req_zone" in with_limit.files[0].content
    assert "limit_req_zone" not in without.files[0].content


def test_redirect_route_cannot_emit_https(provider: NginxProvider) -> None:
    bundle = provider.render(NODE, [route(redirect={"to_host": "www.other-name.com", "code": 302})])
    fragment = bundle.files[1].content
    assert "return 302 http://www.other-name.com$request_uri;" in fragment
    assert "proxy_pass" not in fragment
    assert "https" not in fragment.lower()
    # The model simply has no field for a scheme change.
    with pytest.raises(ValidationError):
        RouteRedirect(to_host="a.example.com", code=301, to_scheme="https")  # type: ignore[call-arg]


def test_missing_upstream_is_a_render_error(provider: NginxProvider) -> None:
    with pytest.raises(RenderError):
        provider.render(NODE, [route(upstream_host="")])


def test_upstream_host_must_be_an_ip_literal(provider: NginxProvider) -> None:
    with pytest.raises(RenderError):
        provider.render(NODE, [route(upstream_host="internal-service")])


def test_port_range_is_enforced(provider: NginxProvider) -> None:
    with pytest.raises(RenderError):
        provider.render(NODE, [route(upstream_port=0)])
    with pytest.raises(RenderError):
        provider.render(NODE, [route(upstream_port=70000)])


@pytest.mark.parametrize(
    "hostname",
    [
        "app.example.com; } #",
        "app.example.com\nserver { listen 80;",
        "app_example.com",
        "$host.example.com",
        "app.example.com `cmd`",
    ],
)
def test_hostname_injection_is_refused(provider: NginxProvider, hostname: str) -> None:
    with pytest.raises(InvalidName):
        provider.render(NODE, [route(hostname=hostname)])


@pytest.mark.parametrize(
    "path",
    [
        "/a;b",
        "/a b",
        "/a{b}",
        "/a$b",
        "/../etc",
        '"/a"',
        "/*",
    ],
)
def test_path_injection_is_refused(provider: NginxProvider, path: str) -> None:
    with pytest.raises(InvalidName):
        provider.render(NODE, [route(path=path)])


def test_duplicate_enabled_route_is_refused(provider: NginxProvider) -> None:
    with pytest.raises(RenderError):
        provider.render(NODE, [route("1" * 32), route("2" * 32)])


def test_route_count_is_bounded(provider: NginxProvider) -> None:
    routes = [
        route(f"{index:032x}", hostname=f"h{index}.example.com")
        for index in range(MAX_ROUTES_PER_NODE + 1)
    ]
    with pytest.raises(RenderError):
        provider.render(NODE, routes)


def test_header_allowlist(provider: NginxProvider) -> None:
    with pytest.raises(ValidationError):
        RouteHeader(name="X-Evil; rm -rf /", value="x")
    with pytest.raises(ValidationError):
        RouteHeader(name="X-Header", value='quote"break')
    with pytest.raises(ValidationError):
        RouteHeader(name="X-Header", value="$request_uri")
    with pytest.raises(ValidationError):
        RouteHeader(name="X-Header", value="line\nbreak")
    with pytest.raises(ValidationError):
        RouteHeader(name="X-Header", value="x" * 513)
    # Reserved proxy headers are refused: one route must not rewrite the Host it
    # forwards or smuggle a framing header upstream.
    for reserved in ("Host", "Connection", "Content-Length", "X-Forwarded-For"):
        with pytest.raises(ValidationError):
            RouteHeader(name=reserved, value="x", target="proxy")
    # ...but the same name as a *response* header is fine.
    assert RouteHeader(name="Host", value="example.com").target == "response"


def test_too_many_headers_is_refused(provider: NginxProvider) -> None:
    headers = tuple({"name": f"X-H{index}", "value": "v"} for index in range(17))
    with pytest.raises(RenderError):
        provider.render(NODE, [route(headers=headers)])


def test_render_validates_headers_again(provider: NginxProvider) -> None:
    # A corrupt database row (bypassing the API schema) is still refused.
    with pytest.raises(ValidationError):
        provider.render(NODE, [route(headers=({"name": "X", "value": "a", "extra": 1},))])


def test_rate_limit_constraints() -> None:
    with pytest.raises(ValidationError):
        RateLimit(requests=0)
    with pytest.raises(ValidationError):
        RateLimit(requests=10001)
    with pytest.raises(ValidationError):
        RateLimit(requests=10, burst=11)
    with pytest.raises(ValidationError):
        RateLimit(requests=10, window="10s")
    assert RateLimit(requests=10, window="1m").window == "1m"


def test_redirect_codes_are_restricted() -> None:
    for code in (301, 302, 307, 308):
        assert RouteRedirect(to_host="a.example.com", code=code).code == code
    for code in (200, 303, 404, MAX_REDIRECT_CODE + 1):
        with pytest.raises(ValidationError):
            RouteRedirect(to_host="a.example.com", code=code)


# --- bundle integrity and limits ----------------------------------------------


def _bundle_files() -> list[BundleFile]:
    return [
        BundleFile(path=MANAGED_CONF_PATH, content="# http\n"),
        BundleFile(path=f"{ROUTES_DIR}/r-{'0' * 32}.conf", content="# route\n"),
    ]


def test_bundle_fingerprint_covers_the_whole_tree() -> None:
    files = _bundle_files()
    fingerprint = fingerprint_files(files, template_version=1)
    bundle = NginxBundle(bundle_id=fingerprint, manifest=["1" * 32], files=files)
    assert bundle.bundle_id == fingerprint
    # Changing any byte of any file changes the fingerprint.
    tampered = [
        BundleFile(path=files[0].path, content="# http\n# changed\n"),
        files[1],
    ]
    with pytest.raises(ValidationError):
        NginxBundle(bundle_id=fingerprint, manifest=[], files=tampered)


def test_bundle_requires_the_managed_configuration() -> None:
    files = _bundle_files()[1:]
    fingerprint = fingerprint_files(files, template_version=1)
    with pytest.raises(ValidationError):
        NginxBundle(bundle_id=fingerprint, manifest=[], files=files)


def test_bundle_path_allowlist() -> None:
    assert is_allowed_bundle_path(MANAGED_CONF_PATH)
    assert is_allowed_bundle_path(f"{ROUTES_DIR}/r-{'a' * 32}.conf")
    for bad in (
        "/etc/nginx/nginx.conf",
        "/etc/nexusops/nginx/../nginx.conf",
        f"{ROUTES_DIR}/../nginx.conf",
        f"{ROUTES_DIR}/evil.conf",
        f"{ROUTES_DIR}/r-../../etc/passwd.conf",
        f"{ROUTES_DIR}/r-{'a' * 31}.conf",
        "/etc/passwd",
        "relative/path.conf",
    ):
        assert not is_allowed_bundle_path(bad), bad
        with pytest.raises(ValidationError):
            BundleFile(path=bad, content="x")


def test_bundle_file_size_and_count_limits() -> None:
    with pytest.raises(ValidationError):
        BundleFile(path=MANAGED_CONF_PATH, content="x" * (MAX_FILE_BYTES + 1))
    files = _bundle_files() + [
        BundleFile(path=f"{ROUTES_DIR}/r-{index:032x}.conf", content="x")
        for index in range(MAX_BUNDLE_FILES)
    ]
    fingerprint = fingerprint_files(files, template_version=1)
    with pytest.raises(ValidationError):
        NginxBundle(bundle_id=fingerprint, manifest=[], files=files)


def test_bundle_manifest_entries_are_bounded() -> None:
    files = _bundle_files()
    fingerprint = fingerprint_files(files, template_version=1)
    with pytest.raises(ValidationError):
        NginxBundle(bundle_id=fingerprint, manifest=["x" * 40], files=files)


def test_apply_params_are_a_closed_shape(provider: NginxProvider) -> None:
    bundle = provider.render(NODE, [route()])
    params = provider.apply_params(bundle)
    parsed = NginxApplyParams.model_validate(params)
    assert parsed.reload is True
    assert parsed.bundle.bundle_id == bundle.bundle_id
    # An extra key is refused rather than passed through to the node.
    with pytest.raises(ValidationError):
        NginxApplyParams.model_validate({**params, "shell": "rm -rf /"})


def test_bundle_serialization_round_trips(provider: NginxProvider) -> None:
    bundle = provider.render(NODE, [route()])
    dumped = bundle.model_dump()
    restored = NginxBundle.model_validate(dumped)
    assert restored.bundle_id == bundle.bundle_id
    assert restored.files == bundle.files


def test_status_params_are_empty(provider: NginxProvider) -> None:
    assert provider.status_params() == {}


def test_provider_only_accepts_canonical_hostnames(provider: NginxProvider) -> None:
    # The renderer re-validates, so a row that slipped past the API (uppercase,
    # trailing dot) still cannot produce an ambiguous server_name.
    bundle = provider.render(NODE, [route(hostname="App.Example.com")])
    assert "server_name app.example.com;" in bundle.files[1].content
    assert canonicalize_name("App.Example.com") == "app.example.com"
