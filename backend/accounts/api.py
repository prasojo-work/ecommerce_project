"""Account endpoints (`API.md` section 2, `ADR-0009`).

Register, sign in, refresh, sign out, and read the current user. The refresh token exists only as
an httpOnly cookie; the access token only in a response body or an `Authorization` header.

Both controls `US-2.2` and `ADR-0009` ask for are here (`M2.3`): every endpoint carries a rate limit
(`accounts/throttling.py`), and `/auth/refresh` checks the request's origin before it reads the
cookie. The second is load-bearing rather than extra — a refresh token is a credential the browser
attaches by itself, and once the frontend and the API are different sites the cookie is
`SameSite=None`, at which point that attribute stops protecting anything.
"""

from __future__ import annotations

import json
from urllib.parse import urlparse

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.http import HttpRequest, HttpResponse
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError, ValidationError
from ninja.security import HttpBearer

from accounts.models import User
from accounts.schemas import LoginSchema, RegisterSchema, TokenSchema, UserSchema
from accounts.throttling import (
    AuthenticatedRateThrottle,
    LoginRateThrottle,
    RefreshRateThrottle,
    RegisterRateThrottle,
)
from accounts.tokens import (
    SESSION_UNKNOWN_MESSAGE,
    TokenError,
    TokenPair,
    issue_tokens,
    resolve_access_token,
    revoke,
    rotate,
)
from core.errors import error_body

router = Router(tags=["accounts"])


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


def _field_errors(field: str, issues: list[str]) -> ValidationError:
    """A `400` in the `API.md` section 3 envelope, naming the offending fields.

    Ninja's handler prefixes each location with its source, so the client sees `body.email` — which
    is how it tells a bad body from a bad query string.
    """
    return ValidationError(
        [{"loc": ["body", field], "msg": issue, "type": "value_error"} for issue in issues]
    )


def _user_schema(user: User) -> UserSchema:
    return UserSchema(
        id=user.pk,
        email=user.email,
        display_name=user.display_name,
        is_staff=user.is_staff,
    )


def _set_refresh_cookie(response: HttpResponse, tokens: TokenPair) -> None:
    """Deliver the refresh token the only way `ADR-0009` allows.

    httpOnly so no script can read it, scoped to the auth routes so it is not attached to every
    catalog request, and `Secure`/`SameSite` raised in production where the two halves of the app
    are different sites.
    """
    response.set_cookie(
        settings.REFRESH_COOKIE_NAME,
        tokens.refresh_token,
        max_age=int((tokens.refresh_expires_at - timezone.now()).total_seconds()),
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path=settings.REFRESH_COOKIE_PATH,
    )


def _clear_refresh_cookie(response: HttpResponse) -> None:
    response.delete_cookie(
        settings.REFRESH_COOKIE_NAME,
        path=settings.REFRESH_COOKIE_PATH,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
    )


def _token_schema(user: User, tokens: TokenPair) -> TokenSchema:
    return TokenSchema(
        access_token=tokens.access_token,
        expires_in=tokens.access_expires_in,
        user=_user_schema(user),
    )


def _sign_in(response: HttpResponse, user: User) -> TokenSchema:
    tokens = issue_tokens(user)
    _set_refresh_cookie(response, tokens)
    return _token_schema(user, tokens)


def _fail(
    response: HttpResponse,
    message: str,
    *,
    status: int = 401,
    code: str = "UNAUTHENTICATED",
) -> HttpResponse:
    """A refusal that keeps whatever the endpoint did to the injected response's cookies.

    Raising `HttpError` instead would hand the response to the exception handler, which builds a
    *fresh* one — so a cookie cleared here would never reach the browser, and the browser would
    present a dead refresh token on every page load forever. Returning the response directly keeps
    the cookie change, and the body is the same `API.md` section 3 envelope the handler would have
    produced, because `error_body` is what produces it in both places.

    The status and code are parameters because the origin guard below has to answer `403` and say
    `FORBIDDEN`, which is not a credential failure.
    """
    response.status_code = status
    response.content = json.dumps(error_body(code, message))
    return response


ORIGIN_REFUSED_MESSAGE = "That request did not come from this storefront."


def _request_origin(request: HttpRequest) -> str | None:
    """The origin the client claims it came from, or `None` when it claims nothing.

    `Origin` is the header to read: browsers send it on every `POST`, cross-site or not. `Referer`
    is the fallback for an agent that sends only that, so the check stays useful instead of
    silently passing.
    """
    origin = request.headers.get("Origin")
    if origin:
        return origin.rstrip("/").lower()

    referer = request.headers.get("Referer")
    if referer:
        parsed = urlparse(referer)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}".lower()
    return None


def _origin_is_trusted(request: HttpRequest) -> bool:
    """`ADR-0009`'s CSRF guard, and the reason this endpoint is the one that needs it.

    The refresh token travels in a cookie, so the browser attaches it to any request the cookie's
    scope and `SameSite` policy allow — convenient, and exactly what reintroduces CSRF once the
    frontend and the API are separate sites, where the attribute is `SameSite=None` and stops
    protecting anything. The origin check is therefore the control that actually holds.

    A request presenting **no** origin at all is allowed. Non-browser clients — curl, the test
    suite, a future mobile app — send none, and they cannot be reached by a page the user merely
    visits. Every browser sends one on a `POST`, so the case this guards against always has a
    header to inspect.
    """
    origin = _request_origin(request)
    if origin is None:
        return True
    trusted = {value.rstrip("/").lower() for value in settings.CORS_ALLOWED_ORIGINS}
    return origin in trusted


@router.post(
    "/register",
    response={201: TokenSchema},
    throttle=[RegisterRateThrottle()],
    summary="Create an account",
)
def register(request: HttpRequest, response: HttpResponse, payload: RegisterSchema) -> TokenSchema:
    """`US-2.1`: email and password with validation, and a duplicate-email error.

    Registering signs the account in, which is what `API.md` section 2 documents ("Create account;
    returns tokens").
    """
    email = payload.email.strip().lower()

    try:
        validate_email(email)
    except DjangoValidationError as exc:
        raise _field_errors("email", [str(message) for message in exc.messages]) from exc

    display_name = payload.display_name.strip()
    try:
        # Validated against a candidate carrying the address and name, because two of Django's four
        # defaults are similarity checks against the user's own attributes.
        validate_password(payload.password, user=User(email=email, display_name=display_name))
    except DjangoValidationError as exc:
        raise _field_errors("password", list(exc.messages)) from exc

    try:
        with transaction.atomic():
            user = User.objects.create_user(
                email=email, password=payload.password, display_name=display_name
            )
    except IntegrityError as exc:
        # The database is the arbiter rather than a prior `exists()` check, which two simultaneous
        # registrations would both pass.
        raise _field_errors("email", ["That email is already registered."]) from exc

    return _sign_in(response, user)


@router.post(
    "/login",
    response=TokenSchema,
    throttle=[LoginRateThrottle()],
    summary="Sign in",
)
def login(request: HttpRequest, response: HttpResponse, payload: LoginSchema) -> TokenSchema:
    """`US-2.2`.

    One message for every failure, so the endpoint cannot be used to find out which addresses have
    accounts. Django runs the password hasher even for an unknown address, so the timing does not
    give it away either.
    """
    user = authenticate(request, email=payload.email, password=payload.password)
    if not isinstance(user, User):
        raise HttpError(401, "Incorrect email or password.")
    return _sign_in(response, user)


@router.post(
    "/refresh",
    response=TokenSchema,
    throttle=[RefreshRateThrottle()],
    summary="Refresh the access token",
)
def refresh(request: HttpRequest, response: HttpResponse) -> TokenSchema | HttpResponse:
    """`US-2.3`: silent refresh. The token is read from the cookie, never from the body.

    The origin check runs before the cookie is read, so a cross-site request cannot spend a token —
    and cannot revoke one either, which is the sharper edge: replaying a stale cookie through a
    forged request would trip reuse detection and sign the real customer out.
    """
    if not _origin_is_trusted(request):
        return _fail(response, ORIGIN_REFUSED_MESSAGE, status=403, code="FORBIDDEN")

    presented = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
    if not presented:
        _clear_refresh_cookie(response)
        return _fail(response, SESSION_UNKNOWN_MESSAGE)

    try:
        user, tokens = rotate(presented)
    except TokenError as exc:
        # Clear the cookie even on failure: a browser that keeps presenting a dead token would
        # retry on every page load and never reach the sign-in screen.
        _clear_refresh_cookie(response)
        return _fail(response, str(exc))

    _set_refresh_cookie(response, tokens)
    return _token_schema(user, tokens)


@router.post(
    "/logout",
    response={204: None},
    auth=auth,
    throttle=[AuthenticatedRateThrottle()],
    summary="Sign out",
)
def logout(request: AuthenticatedRequest, response: HttpResponse) -> None:
    """`US-2.3`. Ends the session server-side; the access token is short-lived and expires anyway."""
    presented = request.COOKIES.get(settings.REFRESH_COOKIE_NAME)
    if presented:
        revoke(presented)
    _clear_refresh_cookie(response)


@router.get(
    "/me",
    response=UserSchema,
    auth=auth,
    throttle=[AuthenticatedRateThrottle()],
    summary="Current user",
)
def me(request: AuthenticatedRequest) -> UserSchema:
    """`US-2.4` reads the profile from here; updating it is `M2.6`."""
    return _user_schema(request.auth)
