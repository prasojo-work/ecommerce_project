import json

import pytest
from django.test import Client as DjangoClient

from accounts.models import User
from catalog.models import Category, Product, ProductVariant

PASSWORD = "secret-pass-123"


@pytest.fixture
def client():
    return DjangoClient()


@pytest.fixture
def variant(db):
    category = Category.objects.create(name="Living room", slug="living-room")
    product = Product.objects.create(
        category=category,
        title="Nordvik Sofa",
        slug="nordvik-sofa",
        status=Product.Status.ACTIVE,
        base_price=5_000_000,
    )
    return ProductVariant.objects.create(
        product=product, sku="SOFA-A", name="Fog grey", stock_qty=5
    )


def auth_headers(client, email="shopper@example.com"):
    User.objects.create_user(email=email, password=PASSWORD)
    login = client.post(
        "/api/v1/auth/login",
        data=json.dumps({"email": email, "password": PASSWORD}),
        content_type="application/json",
    )
    return {"authorization": f"Bearer {login.json()['access_token']}"}


def add_item(client, headers, variant_id, quantity=1):
    return client.post(
        "/api/v1/cart/items",
        data=json.dumps({"variant_id": variant_id, "quantity": quantity}),
        content_type="application/json",
        headers=headers,
    )


@pytest.mark.django_db
def test_add_item_and_read_cart(client, variant):
    headers = auth_headers(client)

    added = add_item(client, headers, variant.id, 2)

    assert added.status_code == 201
    body = added.json()
    assert body["subtotal"] == 10_000_000
    assert body["items"][0]["quantity"] == 2
    assert body["items"][0]["product_title"] == "Nordvik Sofa"


@pytest.mark.django_db
def test_adding_the_same_variant_increments_quantity(client, variant):
    headers = auth_headers(client)
    add_item(client, headers, variant.id, 1)

    body = add_item(client, headers, variant.id, 2).json()

    assert len(body["items"]) == 1
    assert body["items"][0]["quantity"] == 3


@pytest.mark.django_db
def test_update_and_remove_item(client, variant):
    headers = auth_headers(client)
    item_id = add_item(client, headers, variant.id, 1).json()["items"][0]["id"]

    updated = client.patch(
        f"/api/v1/cart/items/{item_id}",
        data=json.dumps({"quantity": 4}),
        content_type="application/json",
        headers=headers,
    )
    assert updated.json()["items"][0]["quantity"] == 4

    removed = client.delete(f"/api/v1/cart/items/{item_id}", headers=headers)
    assert removed.json()["items"] == []


@pytest.mark.django_db
def test_cart_requires_authentication(client):
    assert client.get("/api/v1/cart").status_code == 401


@pytest.mark.django_db
def test_unknown_variant_is_rejected(client, variant):
    headers = auth_headers(client)

    assert add_item(client, headers, 999_999).status_code == 404
