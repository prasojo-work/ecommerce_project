"""One error shape for the whole API.

`ARCHITECTURE.md` §5 specifies `{"detail", "code", "errors"}`. Django Ninja's
defaults diverge — `HttpError` returns only `detail`, and a validation failure
puts a *list* in `detail`, which the frontend renders as `[object Object]`.
These handlers make every failure conform and add the request id for support.
"""

from __future__ import annotations

from typing import Any

from ninja.errors import HttpError, ValidationError

# Machine-readable codes for the statuses this API can return.
_STATUS_CODES = {
    400: "invalid_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    422: "validation_error",
    429: "rate_limited",
    500: "server_error",
}

# Ninja prefixes each error location with the part of the request it came from —
# and sometimes twice, e.g. `["body", "payload", "email"]`. A caller cares about
# the field name, so every leading container marker is dropped.
_CONTAINERS = {"body", "payload", "query", "path", "header", "cookie"}


def _field_name(location: Any) -> str:
    parts = [str(part) for part in location]
    while parts and parts[0].lower() in _CONTAINERS:
        parts.pop(0)
    return ".".join(parts) or "body"


def _envelope(
    request: Any, *, detail: str, code: str, errors: dict[str, str] | None = None
) -> dict[str, Any]:
    payload: dict[str, Any] = {"detail": detail, "code": code, "errors": errors or {}}
    request_id = getattr(request, "request_id", None)
    if request_id:
        payload["request_id"] = request_id
    return payload


def register_error_handlers(api: Any) -> None:
    @api.exception_handler(HttpError)
    def on_http_error(request: Any, exc: HttpError) -> Any:
        """Also covers `Throttled`, which subclasses `HttpError`."""
        return api.create_response(
            request,
            _envelope(
                request,
                detail=exc.message,
                code=_STATUS_CODES.get(exc.status_code, "http_error"),
            ),
            status=exc.status_code,
        )

    @api.exception_handler(ValidationError)
    def on_validation_error(request: Any, exc: ValidationError) -> Any:
        errors: dict[str, str] = {}
        for item in exc.errors:
            errors[_field_name(item.get("loc", ()))] = str(item.get("msg", "Invalid value"))
        return api.create_response(
            request,
            _envelope(
                request,
                detail="Validation failed.",
                code="validation_error",
                errors=errors,
            ),
            status=422,
        )
