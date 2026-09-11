"""Error taxonomy and the single place where API error envelopes are shaped.

Every client-visible failure is an :class:`AppError` with a stable machine
code. Handlers guarantee the response body:

    {"error": {"code": "...", "message": "...", "request_id": "...", ...}}

Internal stack traces never reach the client; they are logged with the
request id instead.
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

log = get_logger("nexusops.errors")


class AppError(Exception):
    """Base class for expected, client-facing errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: Any = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details
        self.headers = headers
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code


class BadRequest(AppError):
    status_code = status.HTTP_400_BAD_REQUEST
    code = "BAD_REQUEST"


class Unauthorized(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "UNAUTHORIZED"

    def __init__(self, message: str = "Authentication required", **kwargs: Any) -> None:
        super().__init__(message, headers={"WWW-Authenticate": "Bearer"}, **kwargs)


class Forbidden(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "FORBIDDEN"


class NotFound(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "NOT_FOUND"


class Conflict(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "CONFLICT"


class UnprocessableEntity(AppError):
    status_code = 422
    code = "VALIDATION_ERROR"


class RateLimited(AppError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = "RATE_LIMITED"

    def __init__(
        self, message: str = "Too many requests", retry_after: int | None = None, **kwargs: Any
    ) -> None:
        headers = {"Retry-After": str(retry_after)} if retry_after else None
        super().__init__(message, headers=headers, **kwargs)


def _error_payload(
    request: Request, code: str, message: str, details: Any = None
) -> dict[str, Any]:
    request_id = getattr(request.state, "request_id", None)
    err: dict[str, Any] = {"code": code, "message": message, "request_id": request_id}
    if details is not None:
        err["details"] = details
    return {"error": err}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> ORJSONResponse:
        return ORJSONResponse(
            status_code=exc.status_code,
            content=_error_payload(request, exc.code, exc.message, exc.details),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> ORJSONResponse:
        details = [
            {
                "loc": [str(loc) for loc in err["loc"]],
                "msg": err["msg"],
                "type": err["type"],
            }
            for err in exc.errors()
        ]
        return ORJSONResponse(
            status_code=422,
            content=_error_payload(
                request, "VALIDATION_ERROR", "Request validation failed", details
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> ORJSONResponse:
        codes = {
            401: "UNAUTHORIZED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            429: "RATE_LIMITED",
        }
        code = codes.get(exc.status_code, f"HTTP_{exc.status_code}")
        return ORJSONResponse(
            status_code=exc.status_code,
            content=_error_payload(request, code, str(exc.detail)),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> ORJSONResponse:
        request_id = getattr(request.state, "request_id", None)
        # Log the exception CLASS, never str(exc): SQLAlchemy statement errors
        # (and others) embed bound parameters — password hashes, secret
        # ciphertext, token hashes — in their message. The engine is created
        # with hide_parameters=True as the second half of this guard, so the
        # traceback itself is also parameter-free.
        log.error(
            "unhandled_exception",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            error=exc.__class__.__name__,
            exc_info=True,
        )
        return ORJSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_payload(
                request,
                "INTERNAL_ERROR",
                "An unexpected error occurred. Reference this request id in support.",
            ),
        )
