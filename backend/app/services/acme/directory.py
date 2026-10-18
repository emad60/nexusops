"""Which ACME directory issuance uses — one policy, decided in one place.

The design's rule (phase5-design.md §5.4) is short and easy to state and easy to
get wrong: *local development, tests, CI and non-production deployments default to
staging or the explicitly configured local test directory; production issuance
requires explicit production configuration; tests never contact the production CA;
and there is no silent fallback in either direction.*

Implementing that rule needs exactly one decision point, because a rule spread over
"the task reads a setting", "the client picks a URL" and "the API labels the result"
is three chances to disagree. So:

* :func:`select_directory` is the **pure** matrix — settings value + environment in,
  one directory or a named error out. No I/O, no defaults beyond the one the design
  states, fully testable.
* :func:`directory_for_settings` is the only thing that reads
  :class:`~app.core.config.Settings`, and it re-runs the matrix rather than trusting
  that the startup validator already did. Two independent calls of the same total
  function cannot disagree; a stored flag could.
* :func:`assert_issuance_allowed` is the last gate before a client is built. It is
  deliberately redundant with :func:`select_directory` *and* with the settings
  validator: the thing it prevents — a production CA reached from a test, burning
  real rate limits with a name the operator never asked for — is not recoverable, so
  it is checked where the socket is opened.
* :func:`describe` is what the API exposes: the directory's **name**, its label and
  whether its certificates are publicly trusted. Never anything a caller could turn
  into a different CA.

The vocabulary itself (:class:`~app.models.enums.AcmeDirectory`) is closed and
carries its URLs, including Pebble's fixed local address, so there is no
configuration value that can point a directory name at an arbitrary host.
"""

from __future__ import annotations

from typing import Any

from app.models.enums import AcmeDirectory

#: The directory every non-production environment issues from unless it names one.
#: Staging, not production: the failure mode of this default has to be an unusable
#: certificate, never a rate-limited real one.
NON_PRODUCTION_DEFAULT = AcmeDirectory.STAGING


class AcmeDirectoryError(ValueError):
    """A directory selection that is refused rather than guessed.

    ``code`` is stable so the caller can map it (a 422 at an API boundary, a
    sanitized ``last_error`` in a worker) without parsing the message. The message
    names variables, directories and the accepted set — never a credential.
    """

    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


def coerce_directory(value: AcmeDirectory | str | None) -> AcmeDirectory | None:
    """The member *value* names, or ``None`` when it names none of them.

    Lower-cases and strips first, so ``" STAGING "`` from an environment variable
    and ``AcmeDirectory.STAGING`` are the same answer; a name outside the closed set
    is ``None`` and the caller refuses it, rather than being coerced into the
    closest match.
    """
    if isinstance(value, AcmeDirectory):
        return value
    if not isinstance(value, str):
        return None
    candidate = value.strip().lower()
    if not candidate:
        return None
    try:
        return AcmeDirectory(candidate)
    except ValueError:
        return None


def select_directory(configured: AcmeDirectory | str | None, *, environment: str) -> AcmeDirectory:
    """The directory issuance must use, or a named refusal. **Pure.**

    The whole matrix, in the order the design states it:

    ============================  ==================  ==============================
    ``ACME_DIRECTORY``            ``ENVIRONMENT``     result
    ============================  ==================  ==============================
    unset                         production          refuse (``REQUIRED_IN_PRODUCTION``)
    unset                         anything else       ``STAGING`` (the default)
    unknown name                  anywhere            refuse (``UNKNOWN``)
    ``pebble``                    production          refuse (``TEST_CA_IN_PRODUCTION``)
    ``production``                not production      refuse (``PRODUCTION_OUTSIDE``)
    ``staging`` / ``pebble``      not production      that directory
    ``production``                production          ``PRODUCTION``
    ``staging``                   production          ``STAGING`` (explicit, allowed)
    ============================  ==================  ==============================

    The last row is the only interesting "allowed" one: an operator running a
    production deployment that deliberately issues from the staging CA — to
    rehearse a rollout — is making an explicit choice, and refusing it would push
    them to a deployment that lies about which CA it uses.
    """
    production_environment = (environment or "").strip().lower() == "production"
    if configured is None or (isinstance(configured, str) and not configured.strip()):
        if production_environment:
            raise AcmeDirectoryError(
                "ACME_DIRECTORY is required in production (set 'production'). Issuance "
                "would otherwise have to guess which certificate authority to use, and "
                "neither guess is safe.",
                code="ACME_DIRECTORY_REQUIRED_IN_PRODUCTION",
            )
        return NON_PRODUCTION_DEFAULT

    resolved = coerce_directory(configured)
    if resolved is None:
        raise AcmeDirectoryError(
            f"'{configured}' is not a known ACME directory. Configure one of: "
            f"{', '.join(sorted(member.value for member in AcmeDirectory))}.",
            code="ACME_DIRECTORY_UNKNOWN",
        )
    if resolved is AcmeDirectory.PEBBLE and production_environment:
        raise AcmeDirectoryError(
            "the Pebble test certificate authority cannot be used in production: its "
            "certificates are signed by a CA no client trusts. Set ACME_DIRECTORY="
            "production (or 'staging' to rehearse).",
            code="ACME_DIRECTORY_TEST_CA_IN_PRODUCTION",
        )
    if resolved is AcmeDirectory.PRODUCTION and not production_environment:
        raise AcmeDirectoryError(
            f"the production certificate authority cannot be used from ENVIRONMENT="
            f"'{environment}': issuance from anywhere but production must never reach "
            "the real CA. Set ACME_DIRECTORY=staging or 'pebble'.",
            code="ACME_DIRECTORY_PRODUCTION_OUTSIDE_PRODUCTION",
        )
    return resolved


def directory_for_url(url: str | None) -> AcmeDirectory | None:
    """The directory a stored URL names, or ``None`` when it names none of them.

    An exact match against the vocabulary's own URLs, not a prefix or a host guess.
    Every stored ``directory_url`` is written from :meth:`AcmeDirectory.url`, so a
    value that matches nothing is one this platform did not write — and inferring a
    member from it would let a hand-edited row claim a CA it never used, which is
    precisely what the recorded provenance is for. ``None`` is a refusal, not a
    default: callers report it rather than substituting the configured directory.
    """
    if not isinstance(url, str):
        return None
    candidate = url.strip()
    if not candidate:
        return None
    for member in AcmeDirectory:
        if member.url() == candidate:
            return member
    return None


def directory_for_settings(settings: Any) -> AcmeDirectory:
    """The directory this deployment issues from, from :class:`Settings`."""
    return select_directory(
        getattr(settings, "acme_directory", None),
        environment=getattr(settings, "environment", ""),
    )


def assert_issuance_allowed(directory: AcmeDirectory, *, settings: Any) -> None:
    """Refuse a directory the current environment may not issue from.

    Redundant with :func:`directory_for_settings` on purpose, and called immediately
    before a client is constructed. The check it repeats is the one whose failure is
    unrecoverable — a staging or CI process signing up for a rate-limited order at
    the real CA — and a guard that depends on every caller having used the *right*
    resolution function is not a guard.
    """
    if directory.is_production and not getattr(settings, "is_production", False):
        raise AcmeDirectoryError(
            "refusing to build an ACME client for the production directory outside a "
            "production environment",
            code="ACME_DIRECTORY_PRODUCTION_OUTSIDE_PRODUCTION",
        )


def describe(directory: AcmeDirectory) -> dict[str, Any]:
    """Safe metadata about a directory, for an API read model or an event payload.

    An explicit allowlist with no URL-free surprises: the name, the label and
    whether the certificates it issues are publicly trusted. The URL is included
    because it is already public (it is the CA's published endpoint) and because an
    operator diagnosing a certificate needs to know which CA answered; nothing else
    about a CA conversation belongs here.
    """
    return {
        "name": directory.value,
        "label": directory.label,
        "url": directory.url(),
        "is_production": directory.is_production,
        "is_publicly_trusted": directory.is_publicly_trusted,
    }


__all__ = [
    "NON_PRODUCTION_DEFAULT",
    "AcmeDirectoryError",
    "assert_issuance_allowed",
    "coerce_directory",
    "describe",
    "directory_for_settings",
    "directory_for_url",
    "select_directory",
]
