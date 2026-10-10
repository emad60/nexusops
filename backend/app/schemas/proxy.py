"""Proxy bundle and operation-parameter schemas — the agent-facing config contract.

Everything the agent will write arrives through these models, and all of them set
``extra="forbid"`` (the :class:`~app.schemas.base.APIModel` default), so an unknown
key is a 422 at the API and a refusal at the node. The limits live here rather
than inside the renderer: a malicious or malformed database row must not be able
to produce unbounded configuration output, and the agent has to apply the same
bounds independently of the control plane.

The bundle is a *closed tree*: a fingerprint, a template version, a manifest of
route ids and an explicit set of files whose paths must match the managed
allowlist. There is no field for a certificate, a key or an arbitrary directive —
Phase 4 serves HTTP only.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from pydantic import Field, field_validator, model_validator

from app.schemas.base import APIModel

#: The only provider implemented in Phase 4.
PROVIDER_NAME = "nginx"
#: Bumped whenever a template changes shape, so a fingerprint difference is
#: explainable from the bundle alone.
TEMPLATE_VERSION = 1

#: Fixed, non-interpolated managed paths. The agent validates every incoming path
#: against these; nothing else may be written.
MANAGED_ROOT = "/etc/nexusops/nginx"
MANAGED_CONF_PATH = f"{MANAGED_ROOT}/nexusops.conf"
ROUTES_DIR = f"{MANAGED_ROOT}/routes.d"
STAGED_DIR = f"{MANAGED_ROOT}/staged"
STATE_DIR = f"{MANAGED_ROOT}/state"

#: Bundle limits. Chosen to be generous for a real node (40 routes, a few KB each)
#: and small enough that a bad row cannot become a megabyte of config.
MAX_BUNDLE_FILES = 64
MAX_FILE_BYTES = 64 * 1024
MAX_BUNDLE_BYTES = 512 * 1024
MAX_ROUTES_PER_NODE = 40
MAX_HEADERS_PER_ROUTE = 16
MAX_HEADER_VALUE = 512
MAX_RATE_REQUESTS = 10_000
MAX_RATE_BURST = 10_000
MAX_REDIRECT_CODE = 308

#: File names inside ``routes.d`` — hex only, so a route id can never need
#: escaping and a hand-crafted name cannot traverse anywhere.
ROUTE_FILE_RE = re.compile(r"^r-[0-9a-f]{32}\.conf$")
_FINGERPRINT_RE = re.compile(r"^[0-9a-f]{64}$")

#: Header names we render ourselves and refuse to let a route override: allowing
#: them would let one route rewrite the Host it forwards or smuggle a body
#: encoding past the proxy's framing.
RESERVED_PROXY_HEADERS: frozenset[str] = frozenset(
    {
        "host",
        "connection",
        "content-length",
        "transfer-encoding",
        "upgrade",
        "expect",
        "x-forwarded-for",
        "x-forwarded-proto",
        "x-forwarded-host",
        "keep-alive",
        "te",
        "trailer",
    }
)

_HEADER_NAME_RE = re.compile(r"^[A-Za-z0-9-]{1,64}$")
#: Printable ASCII, minus ``$`` (nginx variable expansion — a user value must
#: never become a variable reference) and minus quote/backslash, which would break
#: out of the quoted template slot. The gaps are explicit byte ranges: ``\x22`` is
#: ``"``, ``\x24`` is ``$``, ``\x5c`` is ``\``.
_HEADER_VALUE_RE = re.compile(r"^[\x20\x21\x23\x25-\x5b\x5d-\x7e]{0,512}$")

#: Rate-limit windows nginx can express: it has ``r/s`` and ``r/m`` and nothing
#: between, so the design's "10s" is not representable and is not offered.
RATE_WINDOWS: frozenset[str] = frozenset({"1s", "1m"})
#: Redirect codes nginx can emit. ``301/302/307/308`` only; no scheme redirects.
REDIRECT_CODES: frozenset[int] = frozenset({301, 302, 307, 308})


def is_allowed_bundle_path(path: str) -> bool:
    """Whether *path* is one of the managed files a bundle may write."""
    if path == MANAGED_CONF_PATH:
        return True
    if not path.startswith(ROUTES_DIR + "/"):
        return False
    name = path[len(ROUTES_DIR) + 1 :]
    return ROUTE_FILE_RE.match(name) is not None


class RouteHeader(APIModel):
    """One header a route adds. ``target`` says where it lands."""

    name: str = Field(min_length=1, max_length=64)
    value: str = Field(default="", max_length=MAX_HEADER_VALUE)
    #: ``response`` → ``add_header``; ``proxy`` → ``proxy_set_header`` upstream.
    target: str = Field(default="response")

    @field_validator("name")
    @classmethod
    def _check_name(cls, value: str) -> str:
        if not _HEADER_NAME_RE.match(value):
            raise ValueError("a header name may only use letters, digits and hyphens")
        return value

    @field_validator("value")
    @classmethod
    def _check_value(cls, value: str) -> str:
        if not _HEADER_VALUE_RE.match(value):
            raise ValueError("a header value must be printable ASCII without $ or quotes")
        return value

    @field_validator("target")
    @classmethod
    def _check_target(cls, value: str) -> str:
        if value not in ("response", "proxy"):
            raise ValueError("target must be 'response' or 'proxy'")
        return value

    @model_validator(mode="after")
    def _check_reserved(self) -> RouteHeader:
        if self.target == "proxy" and self.name.lower() in RESERVED_PROXY_HEADERS:
            raise ValueError(f"'{self.name}' is set by NexusOps and cannot be overridden")
        return self


class RateLimit(APIModel):
    """One route's request-rate ceiling (rendered as a ``limit_req_zone``)."""

    requests: int = Field(ge=1, le=MAX_RATE_REQUESTS)
    window: str = Field(default="1s")
    burst: int = Field(default=0, ge=0, le=MAX_RATE_BURST)

    @field_validator("window")
    @classmethod
    def _check_window(cls, value: str) -> str:
        if value not in RATE_WINDOWS:
            raise ValueError("window must be '1s' or '1m'")
        return value

    @model_validator(mode="after")
    def _check_burst(self) -> RateLimit:
        if self.burst > self.requests:
            raise ValueError("burst may not exceed the request rate")
        return self


class RouteRedirect(APIModel):
    """A fixed host redirect. Phase 4 cannot express a scheme change here.

    There is deliberately **no** ``to_scheme`` field: the only redirect Phase 4
    can render is to another organization-owned name over HTTP, so no route can
    be configured into an HTTPS redirect before certificates exist.
    """

    to_host: str = Field(min_length=4, max_length=253)
    code: int = Field(default=301)

    @field_validator("code")
    @classmethod
    def _check_code(cls, value: int) -> int:
        if value not in REDIRECT_CODES:
            raise ValueError("code must be one of 301, 302, 307, 308")
        return value


class BundleFile(APIModel):
    """One rendered file. The path is allowlisted, the content is bounded."""

    path: str = Field(min_length=1, max_length=512)
    content: str = Field(max_length=MAX_FILE_BYTES)

    @field_validator("path")
    @classmethod
    def _check_path(cls, value: str) -> str:
        if not is_allowed_bundle_path(value):
            raise ValueError("path is outside the NexusOps-managed configuration tree")
        return value

    @field_validator("content")
    @classmethod
    def _check_content(cls, value: str) -> str:
        if "\x00" in value:
            raise ValueError("content may not contain NUL bytes")
        if len(value.encode("utf-8")) > MAX_FILE_BYTES:
            raise ValueError(f"content exceeds {MAX_FILE_BYTES} bytes")
        return value


def fingerprint_files(files: list[BundleFile], *, template_version: int) -> str:
    """Deterministic fingerprint over the complete rendered tree.

    Path order is imposed here (sorted), lengths are included, and the template
    version is part of the preimage, so the same routes rendered by a newer
    template produce a different — and correctly *stale* — fingerprint.
    """
    digest = hashlib.sha256()
    digest.update(f"{PROVIDER_NAME}:{template_version}\n".encode())
    for file in sorted(files, key=lambda f: f.path):
        encoded = file.content.encode("utf-8")
        digest.update(f"{file.path}\0{len(encoded)}\0".encode())
        digest.update(encoded)
        digest.update(b"\n")
    return digest.hexdigest()


class NginxBundle(APIModel):
    """The desired configuration for one node, as data."""

    bundle_id: str = Field(min_length=64, max_length=64)
    provider: str = Field(default=PROVIDER_NAME, max_length=32)
    template_version: int = Field(default=TEMPLATE_VERSION, ge=1, le=1000)
    #: Route ids this bundle is the desired state for. The agent echoes it back
    #: so the control plane can attribute an outcome to specific routes without
    #: parsing config text.
    manifest: list[str] = Field(default_factory=list, max_length=MAX_ROUTES_PER_NODE)
    files: list[BundleFile] = Field(min_length=1, max_length=MAX_BUNDLE_FILES)

    @field_validator("bundle_id")
    @classmethod
    def _check_fingerprint(cls, value: str) -> str:
        if not _FINGERPRINT_RE.match(value):
            raise ValueError("bundle_id must be a sha256 hex digest")
        return value

    @field_validator("manifest")
    @classmethod
    def _check_manifest(cls, value: list[str]) -> list[str]:
        for item in value:
            if not re.fullmatch(r"[0-9a-fA-F-]{1,36}", item):
                raise ValueError("manifest entries must be identifiers")
        return value

    @model_validator(mode="after")
    def _check_tree(self) -> NginxBundle:
        paths = [f.path for f in self.files]
        if len(set(paths)) != len(paths):
            raise ValueError("bundle contains duplicate paths")
        if MANAGED_CONF_PATH not in paths:
            raise ValueError("bundle must contain the managed http-level configuration")
        total = sum(len(f.content.encode("utf-8")) for f in self.files)
        if total > MAX_BUNDLE_BYTES:
            raise ValueError(f"bundle exceeds {MAX_BUNDLE_BYTES} bytes")
        # The fingerprint must match the *content*, so a bundle cannot be edited
        # in transit (or by a buggy renderer) and still be attributed.
        expected = fingerprint_files(self.files, template_version=self.template_version)
        if expected != self.bundle_id:
            raise ValueError("bundle_id does not match the rendered file tree")
        return self

    @property
    def route_paths(self) -> list[str]:
        return [f.path for f in self.files if f.path != MANAGED_CONF_PATH]


class NginxBootstrapParams(APIModel):
    """No parameters. Bootstrap is fixed: it either can do the documented minimal
    change or it refuses — there is nothing to configure from the control plane."""


class NginxApplyParams(APIModel):
    """One validated bundle to apply atomically."""

    bundle: NginxBundle
    reload: bool = True


class NginxStatusParams(APIModel):
    """No parameters. Status is a read of fixed, known state."""


def bundle_summary(bundle: NginxBundle) -> dict[str, Any]:
    """Bounded, human-readable bundle metadata for audit rows and UI.

    Never includes rendered configuration text: the audit trail records *that* a
    bundle was applied and its fingerprint, not what the file said.
    """
    return {
        "bundle_id": bundle.bundle_id,
        "provider": bundle.provider,
        "template_version": bundle.template_version,
        "files": len(bundle.files),
        "routes": len(bundle.manifest),
    }


def stable_json(value: Any) -> str:
    """Canonical JSON for fingerprint-adjacent comparisons in tests."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"))
