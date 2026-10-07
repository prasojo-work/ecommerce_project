"""Request correlation ids (`ARCHITECTURE.md` §4 gives `core` this job).

Every request gets an id, every log line carries it, and it is echoed back in
the `X-Request-ID` response header so a user can quote it when reporting a
problem. Callers may supply their own id for cross-tier tracing.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from core.logging import set_request_id

REQUEST_ID_HEADER = "X-Request-ID"
_META_KEY = "HTTP_X_REQUEST_ID"


def _accept(raw: str) -> str | None:
    """Trust a caller-supplied id only when it is a uuid.

    Anything else could carry newlines or arbitrary text straight into the logs,
    so a malformed value is discarded and replaced rather than echoed.
    """
    try:
        return str(uuid.UUID(str(raw).strip()))
    except ValueError:
        return None


class RequestIDMiddleware:
    def __init__(self, get_response: Callable[[Any], Any]) -> None:
        self.get_response = get_response

    def __call__(self, request: Any) -> Any:
        request_id = _accept(request.META.get(_META_KEY, "")) or str(uuid.uuid4())
        request.request_id = request_id
        set_request_id(request_id)
        response = self.get_response(request)
        response[REQUEST_ID_HEADER] = request_id
        return response
