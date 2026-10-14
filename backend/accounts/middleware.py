"""Rate limiting for Django's own views, where Ninja's throttles cannot reach (`SEC-FIND-1.7`)."""

from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

from accounts.throttling import AdminLoginRateThrottle

# Django's own sign-in for the operator console (`API.md` section 9).
ADMIN_LOGIN_PATH = "/admin/login/"


class AdminLoginThrottleMiddleware:
    """Limit sign-in attempts against the operator console (`SEC-FIND-1.7`).

    Django Ninja attaches throttles to Ninja operations, and the console is not one: `/admin/login/` is
    a plain Django view, so the screen `SECURITY-BASELINE.md` names as the highest-value target was the
    one place in the system with no limit on it. A working operator password buys the whole catalog and
    every order, and nothing else in this project stands between an attacker and that except the
    password itself.

    The window is not reimplemented here. `AdminLoginRateThrottle` is the same `LiveRateThrottle` the
    auth endpoints use, keyed on the client by the same rules and reading the same rates mapping, so
    this class is an attachment rather than a second limiter that could drift from the first.

    Only `POST` is counted. A `GET` is somebody looking at a form, and counting it would spend an
    operator's budget on a browser refresh.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.method == "POST" and request.path == ADMIN_LOGIN_PATH:
            throttle = AdminLoginRateThrottle()

            if not throttle.allow_request(request):
                response = HttpResponse(
                    "Too many sign-in attempts. Try again shortly.",
                    status=429,
                )
                # `int` because the header is whole seconds, `max(1, ...)` because a `Retry-After: 0`
                # tells the client to retry immediately, which is the one thing it must not do. The
                # `or 0.0` is for the type: `wait()` answers `None` when a request is allowed, and this
                # branch is only reached when it was not, so it never fires.
                seconds = max(1, int(throttle.wait() or 0.0))
                response["Retry-After"] = str(seconds)

                return response

        return self.get_response(request)
