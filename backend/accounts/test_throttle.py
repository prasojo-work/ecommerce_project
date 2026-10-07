"""Priority auth controls: brute-force and registration-abuse limits.

`SEC-FIND-3.1`. The limits key on the client address, so this also documents that
a single address cannot be used to grind a login.
"""

from __future__ import annotations

import json

import pytest
from django.test import Client

from accounts.models import User
from conftest import PASSWORD

LOGIN = "/api/v1/auth/login"
REGISTER = "/api/v1/auth/register"

# The throttle instances are built at import time from these rates.
LOGIN_LIMIT = 10
REGISTER_LIMIT = 30


def _login(client, email: str, password: str = "wrong-password"):
    return client.post(
        LOGIN,
        data=json.dumps({"email": email, "password": password}),
        content_type="application/json",
    )


@pytest.mark.django_db
def test_failed_logins_are_counted_and_then_refused(client, shopper):
    """Guessing must not be free: every attempt counts, success or not."""
    for _ in range(LOGIN_LIMIT):
        assert _login(client, shopper.email).status_code == 401

    blocked = _login(client, shopper.email)

    assert blocked.status_code == 429
    assert blocked.json()["code"] == "rate_limited"


@pytest.mark.django_db
def test_a_valid_password_is_also_refused_once_the_limit_is_reached(client, shopper):
    """The limiter must fail closed, not let a lucky guess through."""
    for _ in range(LOGIN_LIMIT):
        _login(client, shopper.email)

    blocked = _login(client, shopper.email, PASSWORD)

    assert blocked.status_code == 429


@pytest.mark.django_db
def test_the_limit_is_per_client_address(client, shopper):
    for _ in range(LOGIN_LIMIT + 1):
        _login(client, shopper.email)
    assert _login(client, shopper.email).status_code == 429

    elsewhere = Client(REMOTE_ADDR="203.0.113.9")

    assert _login(elsewhere, shopper.email).status_code == 401


@pytest.mark.django_db
def test_one_attacker_cannot_lock_another_address_out(client, shopper, rival):
    """Throttling by address keeps a victim's own login working."""
    for _ in range(LOGIN_LIMIT + 1):
        _login(client, shopper.email)

    elsewhere = Client(REMOTE_ADDR="203.0.113.10")

    assert _login(elsewhere, rival.email).status_code == 401


@pytest.mark.django_db
def test_registration_is_throttled(client):
    for index in range(REGISTER_LIMIT):
        response = client.post(
            REGISTER,
            data=json.dumps(
                {"email": f"shopper{index}@example.com", "password": "secret-pass-123"}
            ),
            content_type="application/json",
        )
        assert response.status_code == 201

    blocked = client.post(
        REGISTER,
        data=json.dumps({"email": "one-too-many@example.com", "password": "secret-pass-123"}),
        content_type="application/json",
    )

    assert blocked.status_code == 429
    assert User.objects.filter(email="one-too-many@example.com").exists() is False
