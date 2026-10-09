"""Request correlation middleware (supports NFR-5 observability)."""

from collections.abc import Callable
from uuid import uuid4

from django.http import HttpRequest, HttpResponse

from core.logging import set_request_id

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware:
    """Attach a correlation id to each request and echo it back in the response."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid4().hex
        set_request_id(request_id)
        response = self.get_response(request)
        response[REQUEST_ID_HEADER] = request_id
        return response
