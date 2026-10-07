import json

import pytest
from django.test import Client as DjangoClient

from accounts.models import Address, User

PASSWORD = "secret-pass-123"


@pytest.fixture
def client():
    return DjangoClient()


def login_headers(client, email):
    response = client.post(
        "/api/v1/auth/login",
        data=json.dumps({"email": email, "password": PASSWORD}),
        content_type="application/json",
    )
    return {"authorization": f"Bearer {response.json()['access_token']}"}


def create_address(client, headers, **overrides):
    payload = {
        "recipient": "Shopper",
        "phone": "0812000000",
        "line1": "Jl. Merdeka 1",
        "city": "Jakarta",
        "province": "DKI",
        "postal_code": "10110",
        **overrides,
    }
    return client.post(
        "/api/v1/addresses",
        data=json.dumps(payload),
        content_type="application/json",
        headers=headers,
    )


@pytest.mark.django_db
def test_address_crud(client):
    User.objects.create_user(email="shopper@example.com", password=PASSWORD)
    headers = login_headers(client, "shopper@example.com")

    created = create_address(client, headers)
    assert created.status_code == 201
    address_id = created.json()["id"]

    listed = client.get("/api/v1/addresses", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    patched = client.patch(
        f"/api/v1/addresses/{address_id}",
        data=json.dumps({"city": "Bandung"}),
        content_type="application/json",
        headers=headers,
    )
    assert patched.status_code == 200
    assert patched.json()["city"] == "Bandung"

    deleted = client.delete(f"/api/v1/addresses/{address_id}", headers=headers)
    assert deleted.status_code == 204
    assert Address.objects.count() == 0


@pytest.mark.django_db
def test_addresses_require_authentication(client):
    assert client.get("/api/v1/addresses").status_code == 401


@pytest.mark.django_db
def test_cannot_read_another_users_address(client):
    owner = User.objects.create_user(email="owner@example.com", password=PASSWORD)
    User.objects.create_user(email="other@example.com", password=PASSWORD)
    address = Address.objects.create(
        user=owner,
        recipient="Owner",
        phone="1",
        line1="x",
        city="Jakarta",
        province="DKI",
        postal_code="10110",
    )
    headers = login_headers(client, "other@example.com")

    assert client.get(f"/api/v1/addresses/{address.id}", headers=headers).status_code == 404


@pytest.mark.django_db
def test_only_one_default_address_is_kept(client):
    User.objects.create_user(email="shopper@example.com", password=PASSWORD)
    headers = login_headers(client, "shopper@example.com")

    first = create_address(client, headers, is_default=True).json()
    create_address(client, headers, recipient="Second", is_default=True)

    refreshed = client.get(f"/api/v1/addresses/{first['id']}", headers=headers).json()
    assert refreshed["is_default"] is False
