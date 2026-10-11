"""Bearer-token authentication (`API.md` section 2, `ADR-0009`).

Kept out of `accounts/api.py` so both the auth endpoints and the address book authenticate the
same way without either router owning the other's module.
"""

from __future__ import annotations

from django.http import HttpRequest
from ninja.security import HttpBearer

from accounts.models import User
from accounts.tokens import resolve_access_token


class AccessTokenAuth(HttpBearer):
    """`Authorization: Bearer <access_token>` (`API.md` section 2)."""

    def authenticate(self, request: HttpRequest, token: str) -> User | None:
        return resolve_access_token(token)


class AuthenticatedRequest(HttpRequest):
    """A request that Ninja has attached the authenticated user to.

    Ninja assigns whatever `authenticate()` returned to `request.auth`, which `django-stubs` does
    not know about. Declaring it here keeps the endpoints typed instead of reaching for `Any`.
    """

    auth: User


auth = AccessTokenAuth()
