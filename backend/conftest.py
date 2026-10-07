"""Shared fixtures for the API test suite.

Kept at the backend root so the `orders` and `payments` suites can exercise the
same end-to-end flow without duplicating setup. `cart/tests.py` predates this
file and keeps its own local fixtures (local definitions win in pytest).
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from django.http import HttpResponse
from django.test import Client

from accounts.models import Address, User
from catalog.models import Category, Product, ProductVariant

PASSWORD = "secret-pass-123"


@pytest.fixture(autouse=True)
def fast_password_hasher(settings: Any) -> None:
    """Hash at test speed; PBKDF2 otherwise dominates the suite runtime."""
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture
def client() -> Client:
    return Client()


@pytest.fixture
def shopper(db: Any) -> User:
    return User.objects.create_user(email="shopper@example.com", password=PASSWORD)


@pytest.fixture
def rival(db: Any) -> User:
    return User.objects.create_user(email="rival@example.com", password=PASSWORD)


@pytest.fixture
def address(db: Any, shopper: User) -> Address:
    return Address.objects.create(
        user=shopper,
        recipient="Ada Lovelace",
        phone="0812345678",
        line1="Jl. Merdeka 1",
        city="Bandung",
        province="West Java",
        postal_code="40111",
    )


@pytest.fixture
def variant(db: Any) -> ProductVariant:
    """A Rp 1.000.000 variant — above the free-delivery threshold."""
    category = Category.objects.create(name="Living room", slug="living-room")
    product = Product.objects.create(
        category=category,
        title="Nordvik Sofa",
        slug="nordvik-sofa",
        status=Product.Status.ACTIVE,
        base_price=1_000_000,
    )
    return ProductVariant.objects.create(
        product=product, sku="SOFA-A", name="Fog grey", stock_qty=5
    )


@pytest.fixture
def login(client: Client, shopper: User, rival: User) -> Any:
    """Return a callable producing `Authorization` headers for a user.

    Depends on both account fixtures so any test that logs in has the accounts
    it might reference already created.
    """

    def _login(email: str = "shopper@example.com") -> dict[str, str]:
        response = client.post(
            "/api/v1/auth/login",
            data=json.dumps({"email": email, "password": PASSWORD}),
            content_type="application/json",
        )
        return {"authorization": f"Bearer {response.json()['access_token']}"}

    return _login


@pytest.fixture
def cart_add(client: Client) -> Any:
    """Return a callable that adds a variant to the caller's cart."""

    def _add(headers: dict[str, str], variant: ProductVariant, quantity: int = 1) -> HttpResponse:
        return client.post(
            "/api/v1/cart/items",
            data=json.dumps({"variant_id": variant.id, "quantity": quantity}),
            content_type="application/json",
            headers=headers,
        )

    return _add


@pytest.fixture
def place_order(client: Client) -> Any:
    """Return a callable that submits checkout."""

    def _place(
        headers: dict[str, str],
        address: Address,
        shipping: str = "standard",
        key: str | None = None,
    ) -> HttpResponse:
        payload: dict[str, Any] = {
            "address_id": address.id,
            "shipping_method": shipping,
        }
        if key is not None:
            payload["idempotency_key"] = key
        return client.post(
            "/api/v1/orders",
            data=json.dumps(payload),
            content_type="application/json",
            headers=headers,
        )

    return _place
