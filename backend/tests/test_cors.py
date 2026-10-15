"""Cross-origin access for the browser client (`ADR-0011`, `M2.4`).

Cookie attributes can be asserted through the test client, but *whether a browser would accept the
response at all* cannot: that depends on headers the middleware adds, on the preflight the browser
sends first, and on the allow-list. These tests pin all three, because the failure mode is silent —
a missing header does not raise, the browser simply refuses the response and the UI looks broken for
reasons that never reach the server log.

`CORS_ALLOWED_ORIGINS` is overridden rather than read, for the same reason the origin-guard tests in
`test_accounts_api.py` override it: it comes from `.env`, which exists on a developer machine and not
in CI, and a test that changes behaviour based on whether a file happens to be present proves
nothing.
"""

import pytest
from django.test import Client, override_settings

from core.middleware import REQUEST_ID_HEADER

TRUSTED_ORIGIN = "https://storefront.example"
FOREIGN_ORIGIN = "https://evil.example"


@pytest.fixture
def client() -> Client:
    return Client()


@override_settings(CORS_ALLOWED_ORIGINS=[TRUSTED_ORIGIN])
def test_an_allowed_origin_is_echoed_back_with_credentials(client: Client) -> None:
    """The frontend origin must be able to read the response, and to send its cookie with it."""
    response = client.get("/healthz", headers={"Origin": TRUSTED_ORIGIN})

    assert response.status_code == 200
    assert response["Access-Control-Allow-Origin"] == TRUSTED_ORIGIN
    assert response["Access-Control-Allow-Credentials"] == "true"


@override_settings(CORS_ALLOWED_ORIGINS=[TRUSTED_ORIGIN])
def test_a_foreign_origin_is_not_granted_access(client: Client) -> None:
    """No allow-origin header, rather than a refusal: the browser enforces the block, and it does so
    by finding no permission to read the response. The credentials header is still sent — the
    *absent* allow-origin is what decides — so the assertion is on the header that matters.
    """
    response = client.get("/healthz", headers={"Origin": FOREIGN_ORIGIN})

    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" not in response


@override_settings(CORS_ALLOWED_ORIGINS=[])
def test_no_configured_origin_grants_nothing(client: Client) -> None:
    """The default is an empty allow-list, so a deployment that forgets to configure it fails closed."""
    response = client.get("/healthz", headers={"Origin": TRUSTED_ORIGIN})

    assert "Access-Control-Allow-Origin" not in response


@override_settings(CORS_ALLOWED_ORIGINS=[TRUSTED_ORIGIN])
def test_the_refresh_preflight_succeeds(client: Client) -> None:
    """`POST /auth/refresh` is not a simple request — it carries `content-type: application/json` —
    so the browser sends `OPTIONS` first and only makes the real call if that answers. This is the
    request the middleware answers by itself, which is why it needs its own test: routing an OPTIONS
    to Ninja would answer `405` and the refresh would never happen.
    """
    response = client.options(
        "/api/v1/auth/refresh",
        headers={
            "Origin": TRUSTED_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response["Access-Control-Allow-Origin"] == TRUSTED_ORIGIN
    assert response["Access-Control-Allow-Credentials"] == "true"
    assert "POST" in response["Access-Control-Allow-Methods"]
    assert "content-type" in response["Access-Control-Allow-Headers"].lower()


@override_settings(CORS_ALLOWED_ORIGINS=[TRUSTED_ORIGIN])
def test_a_protected_route_can_be_called_with_a_bearer_header(client: Client) -> None:
    """The interceptor at `M2.4` sends `Authorization`, so the preflight has to allow it."""
    response = client.options(
        "/api/v1/auth/me",
        headers={
            "Origin": TRUSTED_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )

    assert response.status_code == 200
    assert "authorization" in response["Access-Control-Allow-Headers"].lower()


@override_settings(CORS_ALLOWED_ORIGINS=[TRUSTED_ORIGIN])
def test_the_checkout_preflight_allows_the_idempotency_key(client: Client) -> None:
    """`POST /orders` carries `Idempotency-Key` (`M4.3`), and a custom header is not sent until the
    preflight names it.

    This is the one that bit, and it bit silently. The browser asked, the answer did not list the
    header, and so the request was never made: nothing reached the server, nothing reached the log,
    and the checkout read as a click that did nothing. The assertion is therefore on the header the
    answer lists rather than on anything the request would have answered, because there is no
    response to assert on — that is the whole failure.
    """
    response = client.options(
        "/api/v1/orders",
        headers={
            "Origin": TRUSTED_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type,idempotency-key",
        },
    )

    assert response.status_code == 200
    assert "idempotency-key" in response["Access-Control-Allow-Headers"].lower()


@override_settings(CORS_ALLOWED_ORIGINS=[TRUSTED_ORIGIN])
def test_the_request_id_is_exposed_to_the_browser(client: Client) -> None:
    """`NFR-5` says correlation ids cross the API and the web app.

    Without this header the id arrives and JavaScript cannot see it: a response header is readable
    from the browser only when CORS names it, so the server would be emitting a correlation id for
    every request that the client could not use to explain an error to anyone. The value is no
    secret — the same id is in the error body (`API.md` section 3) — so exposing it grants nothing
    new; *not* exposing it is what leaves the correlation one-sided.
    """
    response = client.get("/healthz", headers={"Origin": TRUSTED_ORIGIN})

    assert REQUEST_ID_HEADER.lower() in response["Access-Control-Expose-Headers"].lower()
