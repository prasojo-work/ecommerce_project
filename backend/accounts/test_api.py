import json

import pytest
from django.test import Client as DjangoClient

from accounts.models import User


@pytest.fixture
def client():
    return DjangoClient()


def post_json(client, path, payload):
    return client.post(path, data=json.dumps(payload), content_type="application/json")


@pytest.mark.django_db
def test_register_returns_access_token_and_sets_cookie(client):
    response = post_json(
        client,
        "/api/v1/auth/register",
        {"email": "new@example.com", "password": "secret-pass-123", "full_name": "New Shopper"},
    )

    assert response.status_code == 201
    assert "access_token" in response.json()
    assert "nordvik_refresh" in response.cookies


@pytest.mark.django_db
def test_register_rejects_duplicate_email(client):
    payload = {"email": "dup@example.com", "password": "secret-pass-123"}
    post_json(client, "/api/v1/auth/register", payload)

    response = post_json(client, "/api/v1/auth/register", payload)

    assert response.status_code == 400


@pytest.mark.django_db
def test_login_rejects_a_bad_password(client):
    User.objects.create_user(email="shopper@example.com", password="secret-pass-123")

    response = post_json(
        client, "/api/v1/auth/login", {"email": "shopper@example.com", "password": "wrong"}
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_me_returns_the_current_user(client):
    User.objects.create_user(email="shopper@example.com", password="secret-pass-123")
    login = post_json(
        client,
        "/api/v1/auth/login",
        {"email": "shopper@example.com", "password": "secret-pass-123"},
    )
    token = login.json()["access_token"]

    me = client.get("/api/v1/auth/me", headers={"authorization": f"Bearer {token}"})

    assert me.status_code == 200
    assert me.json()["email"] == "shopper@example.com"


@pytest.mark.django_db
def test_me_requires_authentication(client):
    assert client.get("/api/v1/auth/me").status_code == 401


@pytest.mark.django_db
def test_refresh_rotates_and_logout_revokes(client):
    User.objects.create_user(email="shopper@example.com", password="secret-pass-123")
    post_json(
        client,
        "/api/v1/auth/login",
        {"email": "shopper@example.com", "password": "secret-pass-123"},
    )

    refreshed = client.post("/api/v1/auth/refresh")
    assert refreshed.status_code == 200
    assert "access_token" in refreshed.json()

    logged_out = client.post("/api/v1/auth/logout")
    assert logged_out.status_code == 204

    after_logout = client.post("/api/v1/auth/refresh")
    assert after_logout.status_code == 401
