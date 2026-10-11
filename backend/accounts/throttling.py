"""Rate limiting for the auth surface (`US-2.2`, `NFR-3`).

Django Ninja supplies the mechanism: `SimpleRateThrottle` keeps a rolling window of request
timestamps in the cache, `allow_request` runs before the view body, and a rejection is answered as
`429` with `Retry-After` in whole seconds. These classes choose a scope, a key, and when the rate
is read.

Three decisions are worth knowing, because each has a failure mode that is not obvious:

* **The rate is re-read on every request.** `SimpleRateThrottle.__init__` resolves the rate string
  once and stores the parsed numbers on the instance, and Ninja attaches throttle *instances* — the
  ones below are built when this module is imported. Left at that, the limit would be whatever the
  settings held at import time: changing it would appear to do nothing until a restart, and no test
  could lower a limit to watch it trip. `LiveRateThrottle` re-resolves instead, so the mapping in
  settings is live.
* **The key is the client, never the account.** A limiter keyed on the submitted email address would
  let anyone lock a known account out of its own sign-in screen, which turns a rate limit into a
  denial-of-service tool. The anonymous endpoints key on the client IP and decline to count a request
  that is already authenticated. The cost is that a distributed attack is not meaningfully slowed by
  this alone — a deliberate trade at this stage, recorded in the runbook.
* **Whose IP that is depends on the proxy count.** `BaseThrottle.get_ident` uses `X-Forwarded-For`
  verbatim when `NUM_PROXIES` is unset, which any client can forge, so `NINJA_NUM_PROXIES` is set
  explicitly in settings rather than left to Ninja's default.

Limits live in `NINJA_DEFAULT_THROTTLE_RATES` — settings, so they are policy rather than code, which
is what `ADR-0011` asks — and they are read here through Django rather than through Ninja's own
frozen copy of that mapping.
"""

from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpRequest
from ninja.throttling import AnonRateThrottle, AuthRateThrottle


def rate_for(scope: str | None) -> str:
    """The configured rate for a scope, read from settings when it is asked for."""
    rate = settings.NINJA_DEFAULT_THROTTLE_RATES.get(scope or "")
    if rate is None:
        raise ImproperlyConfigured(
            f"No throttle rate is configured for the '{scope}' scope. Add it to "
            "NINJA_DEFAULT_THROTTLE_RATES in config/settings/base.py."
        )
    return str(rate)


class LiveRateThrottle(AnonRateThrottle):
    """A throttle that keeps up with its configured rate. Base for the anonymous endpoints."""

    def get_rate(self) -> str | None:
        return rate_for(self.scope)

    def allow_request(self, request: HttpRequest) -> bool:
        self.num_requests, self.duration = self.parse_rate(self.get_rate())
        return super().allow_request(request)


class LoginRateThrottle(LiveRateThrottle):
    """`/auth/login` — the endpoint that is actually worth brute-forcing (`US-2.2`)."""

    scope = "login"


class RegisterRateThrottle(LiveRateThrottle):
    """`/auth/register` — tighter, because a person registers once and a script registers many."""

    scope = "register"


class RefreshRateThrottle(LiveRateThrottle):
    """`/auth/refresh` — generous, because the client is meant to call it silently and rarely."""

    scope = "refresh"


class AuthenticatedRateThrottle(AuthRateThrottle):
    """The same, for endpoints that already carry a token, keyed per account rather than per IP.

    `AuthRateThrottle` and not `UserRateThrottle`: the latter reads `request.user`, which only exists
    when `AuthenticationMiddleware` is installed, and this API authenticates with a bearer header.
    Using it would raise `AttributeError` on the first request instead of limiting anything.
    """

    scope = "auth"

    def get_rate(self) -> str | None:
        return rate_for(self.scope)

    def allow_request(self, request: HttpRequest) -> bool:
        self.num_requests, self.duration = self.parse_rate(self.get_rate())
        return super().allow_request(request)


__all__ = [
    "AuthenticatedRateThrottle",
    "LoginRateThrottle",
    "RefreshRateThrottle",
    "RegisterRateThrottle",
]
