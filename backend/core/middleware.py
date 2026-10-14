"""Request correlation and response hardening middleware (`NFR-5`, `NFR-3`)."""

from collections.abc import Callable
from uuid import uuid4

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from core.logging import set_request_id

REQUEST_ID_HEADER = "X-Request-ID"

# Where Django's own console lives (`API.md` section 9). It is the only path here that renders HTML a
# person signs into, and so the only one whose policy has to make room for Django's templates.
ADMIN_PATH_PREFIX = "/admin/"


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


class ContentSecurityPolicyMiddleware:
    """Answer with a `Content-Security-Policy` (`SEC-FIND-1.4`, `SECURITY-BASELINE.md` section 6).

    The baseline calls the CSP a "Django 6 built-in". It is not — Django ships no CSP support, and
    `SECURITY-BASELINE.md` is corrected alongside this middleware — so the choice was between a
    dependency (`django-csp`) and a header. One header from one middleware is the smaller thing to
    own, and it keeps the policy in settings where the rest of the project's policy lives.

    Two policies, because the console cannot live under the strict one: Django's admin templates bring
    their own inline `<script>` and `style` attributes, and `'unsafe-inline'` in those two directives
    is what stands between the console and rendering as unstyled, dead markup. What the console keeps
    is every origin restriction — nothing loads from another host and nothing frames it — so the
    concession is narrower than it looks.

    The API's own responses are JSON, where a policy is inert either way. It gets the strict one,
    which costs nothing and is what any accidental HTML response from this service would inherit.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        response["Content-Security-Policy"] = (
            settings.CONTENT_SECURITY_POLICY_ADMIN
            if request.path.startswith(ADMIN_PATH_PREFIX)
            else settings.CONTENT_SECURITY_POLICY
        )
        return response
