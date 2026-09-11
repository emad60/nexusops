"""Provider selection based on a docker host's endpoint URL.

Mapping:
  * ``unix://...`` / ``tcp://...``  -> :class:`RealDockerProvider`
  * ``sim://...`` or settings.simulation_mode -> :class:`SimulatedDockerProvider`
  * anything else (including empty = agent-inherited) -> BadRequest
"""

from __future__ import annotations

from app.core.config import get_settings
from app.core.errors import BadRequest
from app.models import DockerHost
from app.providers.base import DockerProviderError, clip, sanitize_error
from app.providers.docker_real import RealDockerProvider
from app.providers.docker_sim import SimulatedDockerProvider

__all__ = [
    "DockerProviderError",
    "RealDockerProvider",
    "SimulatedDockerProvider",
    "provider_for",
]


def provider_for(host: DockerHost) -> RealDockerProvider | SimulatedDockerProvider:
    """Return the provider matching *host*'s endpoint configuration."""
    url = (host.endpoint_url or "").strip()
    if url.startswith(("unix://", "tcp://")):
        return RealDockerProvider(url, tls_verify=bool(host.tls_verify))
    if url.startswith("sim://") or get_settings().simulation_mode:
        return SimulatedDockerProvider(str(host.id))
    raise BadRequest(
        "No direct provider available for this host endpoint (empty endpoints are agent-managed).",
        code="UNSUPPORTED_ENDPOINT",
    )


def is_simulated(provider: object) -> bool:
    """True when *provider* is the simulated implementation."""
    return getattr(provider, "kind", "") == "simulated"


def describe_provider_error(exc: Exception) -> str:
    """Sanitized, length-capped text safe for host ``last_error`` columns."""
    return clip(sanitize_error(exc), 480)
