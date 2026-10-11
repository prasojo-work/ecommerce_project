"""Contract tests for the auth endpoints (`API.md` section 2, `ADR-0009`).

`SCOPE.md` `US-2.1`-`US-2.3` are what is under test: registration with validation and a
duplicate-email error, sign-in that fails clearly without revealing which addresses exist, silent
refresh, and a logout that ends the session server-side rather than only in the browser.

Rate limiting and the cross-site origin guard (`M2.3`) are covered at the end of the file: `US-2.2`
asks for a rate-limited sign-in, and `ADR-0009` asks for an origin check on refresh. The throttle
tests read the configured rate rather than hard-coding one, and the origin tests pin
`CORS_ALLOWED_ORIGINS` explicitly instead of inheriting whatever `.env` happens to hold.
"""

import json
from collections.abc import Iterator
from typing import Any

import pytest
from django.conf import settings
from django.core.cache import cache
from django.test import Client, override_settings

from accounts.models import RefreshToken, User
from accounts.tokens import (
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
    TokenError,
    decode,
    issue_tokens,
)

pytestmark = pytest.mark.django_db

PASSWORD = "correct-horse-9!"


@pytest.fixture
def client() -> Client:
    """A client per test, because this one keeps its cookies — and cookies are the subject."""
    return Client()


@pytest.fixture
def user() -> User:
    return User.objects.create_user(email="ada@example.com", password=PASSWORD)


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register(
    client: Client,
    email: str = "ada@example.com",
    password: str = PASSWORD,
    display_name: str = "Ada",
) -> Any:
    return client.post(
        "/api/v1/auth/register",
        data=json.dumps({"email": email, "password": password, "display_name": display_name}),
        content_type="application/json",
    )


def login(client: Client, email: str = "ada@example.com", password: str = PASSWORD) -> Any:
    return client.post(
        "/api/v1/auth/login",
        data=json.dumps({"email": email, "password": password}),
        content_type="application/json",
    )


def refresh(client: Client, headers: dict[str, str] | None = None) -> Any:
    return client.post(
        "/api/v1/auth/refresh", content_type="application/json", headers=headers or {}
    )


def live_tokens(user: User) -> int:
    return RefreshToken.objects.filter(user=user, revoked_at__isnull=True).count()


# --- registration (`US-2.1`) ---------------------------------------------------------------


def test_register_creates_the_account_and_signs_it_in(client: Client) -> None:
    response = register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "Bearer"
    assert body["expires_in"] == settings.ACCESS_TOKEN_TTL_SECONDS
    assert body["user"]["email"] == "ada@example.com"
    assert body["user"]["display_name"] == "Ada"
    assert body["user"]["is_staff"] is False
    assert "password" not in body["user"]
    assert User.objects.filter(email="ada@example.com").exists()
    assert live_tokens(User.objects.get(email="ada@example.com")) == 1


def test_register_lower_cases_the_email(client: Client) -> None:
    assert (
        register(client, email="  Ada@Example.COM  ").json()["user"]["email"] == "ada@example.com"
    )


def test_a_duplicate_email_is_a_validation_error(client: Client, user: User) -> None:
    response = register(client)

    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["details"] == [
        {"field": "body.email", "issue": "That email is already registered."}
    ]
    assert error["request_id"]


def test_a_duplicate_differing_only_in_case_is_also_refused(client: Client, user: User) -> None:
    assert register(client, email="ADA@example.com").status_code == 400


def test_a_weak_password_is_refused_with_every_reason(client: Client) -> None:
    response = register(client, password="12345")

    assert response.status_code == 400
    details = response.json()["error"]["details"]
    assert {detail["field"] for detail in details} == {"body.password"}
    assert len(details) >= 3  # too short, too common, entirely numeric


def test_a_password_matching_the_email_is_refused(client: Client) -> None:
    """The similarity validator has to see the address, which is why the candidate user is built."""
    response = register(client, email="ada@example.com", password="ada@example.com")

    assert response.status_code == 400
    assert response.json()["error"]["details"][0]["field"] == "body.password"


def test_an_invalid_email_is_refused(client: Client) -> None:
    response = register(client, email="not-an-email")

    assert response.status_code == 400
    assert response.json()["error"]["details"][0]["field"] == "body.email"


# --- the cookie (`ADR-0009`) --------------------------------------------------------------


def test_the_refresh_token_is_never_in_the_body(client: Client) -> None:
    response = register(client)
    cookie_value = response.cookies[settings.REFRESH_COOKIE_NAME].value

    assert "refresh_token" not in response.json()
    assert cookie_value not in response.content.decode()


def test_the_refresh_cookie_is_http_only_and_scoped_to_the_auth_routes(client: Client) -> None:
    cookie = register(client).cookies[settings.REFRESH_COOKIE_NAME]

    assert cookie["httponly"]
    assert cookie["path"] == "/api/v1/auth"


@override_settings(REFRESH_COOKIE_SECURE=True)
def test_the_refresh_cookie_is_secure_when_production_asks_for_it(client: Client) -> None:
    cookie = register(client).cookies[settings.REFRESH_COOKIE_NAME]

    assert cookie["secure"]


# --- sign in (`US-2.2`) -------------------------------------------------------------------


def test_login_returns_a_token_pair(client: Client, user: User) -> None:
    response = login(client)

    assert response.status_code == 200
    assert response.json()["access_token"]
    assert response.json()["user"]["email"] == "ada@example.com"
    assert settings.REFRESH_COOKIE_NAME in response.cookies
    assert live_tokens(user) == 1


def test_login_is_case_insensitive(client: Client, user: User) -> None:
    assert login(client, email="ADA@EXAMPLE.COM").status_code == 200


def test_a_wrong_password_is_unauthenticated(client: Client, user: User) -> None:
    response = login(client, password="wrong-password")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_an_unknown_email_is_indistinguishable_from_a_wrong_password(
    client: Client, user: User
) -> None:
    """`US-2.2` wants a clear error. It must not also report which addresses are registered."""
    unknown = login(client, email="nobody@example.com").json()["error"]
    wrong = login(client, password="wrong-password").json()["error"]

    assert (unknown["code"], unknown["message"]) == (wrong["code"], wrong["message"])


def test_an_inactive_account_cannot_sign_in(client: Client, user: User) -> None:
    user.is_active = False
    user.save(update_fields=["is_active"])

    assert login(client).status_code == 401


# --- the access token on protected routes -------------------------------------------------


def test_me_returns_the_token_holder(client: Client, user: User) -> None:
    token = login(client).json()["access_token"]

    response = client.get("/api/v1/auth/me", headers=auth_header(token))

    assert response.status_code == 200
    assert response.json() == {
        "id": user.pk,
        "email": "ada@example.com",
        "display_name": "",
        "is_staff": False,
    }


def test_me_without_a_token_is_unauthenticated(client: Client) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


def test_me_refuses_an_unsigned_token(client: Client, user: User) -> None:
    assert client.get("/api/v1/auth/me", headers=auth_header("not.a.token")).status_code == 401


@override_settings(ACCESS_TOKEN_TTL_SECONDS=-1)
def test_me_refuses_an_expired_access_token(client: Client, user: User) -> None:
    token = login(client).json()["access_token"]

    assert client.get("/api/v1/auth/me", headers=auth_header(token)).status_code == 401


def test_an_access_token_cannot_be_traded_for_a_new_pair(client: Client, user: User) -> None:
    """The token types are not interchangeable, so a stolen access token cannot extend itself."""
    client.cookies[settings.REFRESH_COOKIE_NAME] = login(client).json()["access_token"]

    assert refresh(client).status_code == 401


# --- silent refresh (`US-2.3`) ------------------------------------------------------------


def test_refresh_rotates_the_token(client: Client, user: User) -> None:
    login(client)
    original = RefreshToken.objects.get(user=user)

    response = refresh(client)

    assert response.status_code == 200
    assert response.json()["access_token"]
    original.refresh_from_db()
    assert original.revoked_at is not None
    assert RefreshToken.objects.filter(user=user).count() == 2
    assert live_tokens(user) == 1


def test_refresh_without_a_cookie_is_unauthenticated(client: Client) -> None:
    assert refresh(client).status_code == 401


def test_refresh_with_an_unreadable_cookie_is_refused_and_cleared(client: Client) -> None:
    client.cookies[settings.REFRESH_COOKIE_NAME] = "not-a-token"

    response = refresh(client)

    assert response.status_code == 401
    assert response.cookies[settings.REFRESH_COOKIE_NAME].value == ""


def test_reusing_a_rotated_token_ends_every_session(client: Client, user: User) -> None:
    """A revoked token presented again means a copy is in circulation, so nothing survives."""
    login(client)
    copied = client.cookies[settings.REFRESH_COOKIE_NAME].value

    refresh(client)  # the legitimate client moves on and gets a replacement
    assert live_tokens(user) == 1

    client.cookies[settings.REFRESH_COOKIE_NAME] = copied
    response = refresh(client)

    assert response.status_code == 401
    assert live_tokens(user) == 0


# --- logout (`US-2.3`) --------------------------------------------------------------------


def test_logout_revokes_the_session_and_clears_the_cookie(client: Client, user: User) -> None:
    token = login(client).json()["access_token"]

    response = client.post("/api/v1/auth/logout", headers=auth_header(token))

    assert response.status_code == 204
    assert live_tokens(user) == 0
    assert response.cookies[settings.REFRESH_COOKIE_NAME].value == ""


def test_a_refresh_token_is_dead_after_logout(client: Client, user: User) -> None:
    """The heart of `US-2.3`: logout ends the session on the server, not only in the browser."""
    signed_in = login(client)
    token = signed_in.json()["access_token"]
    presented = signed_in.cookies[settings.REFRESH_COOKIE_NAME].value

    client.post("/api/v1/auth/logout", headers=auth_header(token))

    client.cookies[settings.REFRESH_COOKIE_NAME] = presented
    assert refresh(client).status_code == 401


def test_logout_without_an_access_token_is_unauthenticated(client: Client) -> None:
    assert client.post("/api/v1/auth/logout").status_code == 401


def test_logout_succeeds_when_the_cookie_is_unreadable(client: Client, user: User) -> None:
    token = login(client).json()["access_token"]
    client.cookies[settings.REFRESH_COOKIE_NAME] = "not-a-token"

    assert client.post("/api/v1/auth/logout", headers=auth_header(token)).status_code == 204


# --- the tokens themselves -----------------------------------------------------------------


def test_a_token_carries_its_type_and_subject(user: User) -> None:
    pair = issue_tokens(user)

    assert decode(pair.access_token, ACCESS_TOKEN_TYPE)["sub"] == str(user.pk)
    with pytest.raises(TokenError):
        decode(pair.access_token, REFRESH_TOKEN_TYPE)


def test_deleting_a_user_removes_their_tokens(user: User) -> None:
    issue_tokens(user)

    user.delete()

    assert RefreshToken.objects.count() == 0


# --- rate limiting (`M2.3`, `US-2.2`) -------------------------------------------------------

TRUSTED_ORIGIN = "https://storefront.example"


@pytest.fixture(autouse=True)
def clear_throttle_windows() -> Iterator[None]:
    """The window lives in the cache, which outlives a test and is shared by every client in the
    process. Clearing it per test stops the limits leaking between cases, so each one can assert
    the rate it is about rather than a rate reduced by whatever ran before it."""
    cache.clear()
    yield
    cache.clear()


def requests_allowed_per(scope: str) -> int:
    """The configured limit for a scope, so the tests cannot drift away from the settings."""
    return int(str(settings.NINJA_DEFAULT_THROTTLE_RATES[scope]).split("/")[0])


@pytest.mark.parametrize("scope", ["login", "register", "refresh", "auth"])
def test_every_scope_has_a_configured_rate(scope: str) -> None:
    """A throttle whose scope has no rate raises `ImproperlyConfigured` at request time, not at
    startup, so an endpoint could ship and only fail under the request that used it."""
    assert settings.NINJA_DEFAULT_THROTTLE_RATES.get(scope)


def test_login_is_rate_limited(client: Client, user: User) -> None:
    """`US-2.2`: the endpoint is rate-limited. The refusal must also say when to come back."""
    allowed = requests_allowed_per("login")
    for _ in range(allowed):
        assert login(client, password="wrong").status_code == 401

    response = login(client, password="wrong")

    assert response.status_code == 429
    assert response.json()["error"]["code"] == "RATE_LIMITED"
    assert int(response["Retry-After"]) >= 1


@override_settings(NINJA_DEFAULT_THROTTLE_RATES={"login": "2/min"})
def test_the_limit_follows_the_client_and_not_the_address(client: Client, user: User) -> None:
    """Keying on the submitted address would let anyone lock a known account out of its own
    sign-in screen, which turns a rate limit into a denial-of-service tool.

    The limit is lowered here because this case is about *whose* requests are counted, not about
    the number the project ships — and every counted refusal costs a password hash.
    """
    for _ in range(requests_allowed_per("login")):
        login(client, password="wrong")

    # A different address from the same client is still refused, so the counter is not per account.
    assert login(client, email="grace@example.com", password="wrong").status_code == 429

    # And another client has its own window, so one visitor cannot lock out the next.
    assert login(Client(REMOTE_ADDR="203.0.113.7"), password="wrong").status_code == 401


@override_settings(NINJA_DEFAULT_THROTTLE_RATES={"register": "2/hour"})
def test_register_is_rate_limited(client: Client) -> None:
    """`NFR-3` names auth rate limiting generally, and registration is the other anonymous door.

    Lowered for the same reason as the login case above: the shipped `10/hour` is policy, and each
    registration here costs a password hash.
    """
    allowed = requests_allowed_per("register")
    for index in range(allowed):
        created = register(client, email=f"ada{index}@example.com")
        assert created.status_code == 201

    assert register(client, email="ada-extra@example.com").status_code == 429


def test_refresh_is_rate_limited(client: Client, user: User) -> None:
    """`API.md` section 2 promises a rate limit on every auth endpoint, including this one."""
    allowed = requests_allowed_per("refresh")
    login(client)
    for _ in range(allowed):
        assert refresh(client).status_code == 200

    assert refresh(client).status_code == 429


@override_settings(NINJA_DEFAULT_THROTTLE_RATES={"login": "10/min", "auth": "2/min"})
def test_the_authenticated_endpoints_are_throttled_too(client: Client, user: User) -> None:
    """`/auth/me` is keyed per account rather than per IP, so it needs its own wiring check.

    The rate is overridden through settings and takes effect because `AuthenticatedRateThrottle`
    re-reads it on every request — Ninja's own throttles resolve theirs once, when the instance is
    built at import, which would leave this limit unfixably at its configured value.
    """
    token = login(client).json()["access_token"]

    assert client.get("/api/v1/auth/me", headers=auth_header(token)).status_code == 200
    assert client.get("/api/v1/auth/me", headers=auth_header(token)).status_code == 200

    assert client.get("/api/v1/auth/me", headers=auth_header(token)).status_code == 429


# --- the refresh origin guard (`M2.3`, `ADR-0009`) ------------------------------------------


@override_settings(CORS_ALLOWED_ORIGINS=[TRUSTED_ORIGIN])
def test_refresh_from_a_foreign_origin_is_refused(client: Client, user: User) -> None:
    """In production the refresh cookie is `SameSite=None`, so this check is what stands between a
    page the customer happens to be visiting and their session."""
    login(client)

    response = refresh(client, headers={"Origin": "https://evil.example"})

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


@override_settings(CORS_ALLOWED_ORIGINS=[TRUSTED_ORIGIN])
def test_a_refused_origin_leaves_the_session_alone(client: Client, user: User) -> None:
    """The guard runs before rotation, so a forged request cannot sign the real customer out by
    replaying a stale cookie — which would otherwise trip reuse detection and revoke everything."""
    login(client)

    assert refresh(client, headers={"Origin": "https://evil.example"}).status_code == 403
    assert live_tokens(user) == 1

    assert refresh(client, headers={"Origin": TRUSTED_ORIGIN}).status_code == 200


@override_settings(CORS_ALLOWED_ORIGINS=[TRUSTED_ORIGIN])
def test_a_foreign_referer_is_refused_when_there_is_no_origin(client: Client, user: User) -> None:
    """`Origin` is the header to read, but an agent that sends only `Referer` must not slip past."""
    login(client)

    response = refresh(client, headers={"Referer": "https://evil.example/account"})

    assert response.status_code == 403


@override_settings(CORS_ALLOWED_ORIGINS=[TRUSTED_ORIGIN])
def test_a_trusted_referer_is_accepted(client: Client, user: User) -> None:
    login(client)

    response = refresh(client, headers={"Referer": f"{TRUSTED_ORIGIN}/account"})

    assert response.status_code == 200


@override_settings(CORS_ALLOWED_ORIGINS=[])
def test_refresh_without_any_origin_is_allowed(client: Client, user: User) -> None:
    """Non-browser clients send no `Origin`, and no page can prevent a browser from sending one,
    so a missing header is not evidence of an attack — it is evidence of curl."""
    login(client)

    assert refresh(client).status_code == 200
