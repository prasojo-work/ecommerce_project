"""The single error envelope from `API.md` section 3, required by `NFR-4`.

Every error the API returns has one shape:

    {"error": {"code": ..., "message": ..., "details": [...], "request_id": ...}}

`request_id` comes from the middleware that also sets the `X-Request-ID` response header, so an
error body can be matched to a log line.

Ninja's built-in handlers do not satisfy the contract on two counts, which is why they are
replaced rather than extended: request validation answers `422` with `{"detail": ...}` where
`API.md` section 3 documents `400` with the envelope, and an unhandled exception is re-raised to
Django in production, which produces a non-JSON error body.
"""

import logging
from collections.abc import Callable
from typing import Any, cast

from django.http import HttpRequest, HttpResponse
from ninja import NinjaAPI
from ninja.errors import HttpError, ValidationError
from ninja.main import ExcHandler

from core.logging import get_request_id

logger = logging.getLogger(__name__)

# `API.md` section 3 lists the status codes; each maps to the machine-readable code a client can
# switch on. Anything unmapped falls back to "ERROR" rather than inventing a code.
STATUS_CODES: dict[int, str] = {
    400: "VALIDATION_ERROR",
    401: "UNAUTHENTICATED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "SEMANTIC_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
}


def error_body(
    code: str, message: str, details: list[dict[str, str]] | None = None
) -> dict[str, object]:
    """The envelope itself, so non-Ninja views can return the same shape."""
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
            "request_id": get_request_id(),
        }
    }


def _validation_details(exc: ValidationError) -> list[dict[str, str]]:
    """Pydantic's error list as the `{field, issue}` pairs `API.md` section 3 documents.

    Ninja prefixes each location with the parameter source (`query`, `body`, ...), which is
    exactly the context a client needs to tell a bad query string from a bad body.
    """
    details: list[dict[str, str]] = []
    for error in getattr(exc, "errors", []):
        location = error.get("loc", ())
        details.append(
            {
                "field": ".".join(str(part) for part in location),
                "issue": str(error.get("msg", "invalid")),
            }
        )
    return details


def _register(
    api: NinjaAPI, exc_class: type[Exception], handler: Callable[[HttpRequest, Any], HttpResponse]
) -> None:
    """Register one handler.

    Ninja declares a handler's second parameter as `Exc[T]` — which is `T | type[T]` — although it
    always passes an instance. A handler typed for the instance therefore does not satisfy the
    declared signature, so the mismatch is asserted in this one place instead of at every call.
    """
    api.add_exception_handler(exc_class, cast("ExcHandler[Any]", handler))


def install_error_handlers(api: NinjaAPI) -> None:
    """Replace Ninja's defaults so every error goes through the envelope.

    Ninja resolves a handler by walking the exception's MRO, so registering `Exception` covers
    every failure that is not already handled more specifically.
    """

    def handle_validation_error(request: HttpRequest, exc: ValidationError) -> HttpResponse:
        return api.create_response(
            request,
            error_body("VALIDATION_ERROR", "Request validation failed.", _validation_details(exc)),
            status=400,
        )

    def handle_http_error(request: HttpRequest, exc: HttpError) -> HttpResponse:
        code = STATUS_CODES.get(exc.status_code, "ERROR")
        return api.create_response(request, error_body(code, str(exc)), status=exc.status_code)

    def handle_unexpected_error(request: HttpRequest, exc: Exception) -> HttpResponse:
        # Log the traceback: without this the envelope would hide the cause entirely (NFR-5).
        logger.exception("Unhandled error while serving %s", request.path)
        return api.create_response(
            request,
            error_body("INTERNAL_ERROR", "An unexpected error occurred."),
            status=500,
        )

    _register(api, ValidationError, handle_validation_error)
    _register(api, HttpError, handle_http_error)
    _register(api, Exception, handle_unexpected_error)
