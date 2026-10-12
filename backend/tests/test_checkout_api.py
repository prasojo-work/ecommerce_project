"""Contract tests for the checkout quote (`API.md` section 6, `SCOPE.md` `US-4.1`-`US-4.2`).

Two things are pinned before the money is. The first is who can reach the route at all: the cart is
authenticated (`ADR-0017`) and a quote reads the cart, so an anonymous request is a `401` before
anything else is checked. The second is the address rule `US-4.1` asks to be enforced server-side —
exactly one of a saved address or an inline one — because a quote that silently picked one of two
addresses would be a checkout shipping somewhere the customer did not choose.

The money cases then check the arithmetic the order's own constraint will later hold:
`total_cents = subtotal_cents + shipping_cents`, per option, never a number the client has to add.
"""

import json
from typing import Any

import pytest
from django.test import Client

from accounts.models import Address, User
from accounts.tokens import issue_tokens
from cart.models import Cart, CartItem, CartStatus
from catalog.models import Category, Product, ProductVariant
from orders.shipping import DEFAULT_METHOD_CODE, SHIPPING_METHODS

pytestmark = pytest.mark.django_db

client = Client()

QUOTE = "/api/v1/checkout/quote"

PASSWORD = "correct-horse-battery-staple"
STOCK = 5
UNIT_PRICE = 12900

STANDARD = next(method for method in SHIPPING_METHODS if method.code == DEFAULT_METHOD_CODE)
EXPRESS = next(method for method in SHIPPING_METHODS if method.code != DEFAULT_METHOD_CODE)

SAVED_ADDRESS = {
    "recipient": "Ada Lovelace",
    "line1": "12 Analytical Way",
    "city": "London",
    "postal_code": "EC1A 1BB",
    "country": "GB",
}

INLINE_ADDRESS = {
    "recipient": "Grace Hopper",
    "line1": "1 Compiler Court",
    "city": "Arlington",
    "postal_code": "22201",
    "country": "US",
}


@pytest.fixture
def shopper() -> User:
    return User.objects.create_user(email="ada@example.com", password=PASSWORD)


@pytest.fixture
def other_shopper() -> User:
    return User.objects.create_user(email="grace@example.com", password=PASSWORD)


@pytest.fixture
def variant() -> ProductVariant:
    category = Category.objects.create(name="Seating", slug="seating")
    product = Product.objects.create(
        category=category, name="Aalto Chair", slug="aalto-chair", base_price_cents=UNIT_PRICE
    )
    return ProductVariant.objects.create(
        product=product, sku="AAL-OAK", name="Oak", price_cents=UNIT_PRICE, stock_qty=STOCK
    )


def auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {issue_tokens(user).access_token}"}


def save_address(user: User) -> Address:
    return Address.objects.create(user=user, **SAVED_ADDRESS)


def cart_with(user: User, products: list[tuple[ProductVariant, int]]) -> Cart:
    """An active cart holding the given `(variant, quantity)` lines."""
    cart = Cart.objects.create(user=user, status=CartStatus.ACTIVE)
    for product_variant, quantity in products:
        CartItem.objects.create(cart=cart, variant=product_variant, quantity=quantity)
    return cart


def quote(user: User, payload: dict[str, Any]) -> Any:
    return client.post(
        QUOTE,
        data=json.dumps(payload),
        content_type="application/json",
        headers=auth(user),
    )


def error_code(response: Any) -> str:
    return response.json()["error"]["code"]


def test_quoting_requires_a_token() -> None:
    response = client.post(
        QUOTE,
        data=json.dumps({"address": INLINE_ADDRESS}),
        content_type="application/json",
    )

    assert response.status_code == 401
    assert error_code(response) == "UNAUTHENTICATED"


def test_a_saved_address_quotes_the_cart(shopper: User, variant: ProductVariant) -> None:
    address = save_address(shopper)
    cart_with(shopper, [(variant, 2)])

    response = quote(shopper, {"address_id": address.pk})

    assert response.status_code == 200
    body = response.json()
    assert body["subtotal"] == {"amount_cents": 2 * UNIT_PRICE, "currency": "USD"}
    assert body["item_count"] == 2


def test_an_inline_address_quotes_the_cart(shopper: User, variant: ProductVariant) -> None:
    cart_with(shopper, [(variant, 1)])

    response = quote(shopper, {"address": INLINE_ADDRESS})

    assert response.status_code == 200
    assert response.json()["subtotal"]["amount_cents"] == UNIT_PRICE


def test_every_option_carries_its_own_total(shopper: User, variant: ProductVariant) -> None:
    """`US-4.2`: the total updates with the method, and each option states the total it produces."""
    cart_with(shopper, [(variant, 2)])

    body = quote(shopper, {"address": INLINE_ADDRESS}).json()
    subtotal = 2 * UNIT_PRICE

    options = {option["code"]: option for option in body["shipping_options"]}
    assert set(options) == {STANDARD.code, EXPRESS.code}
    for method in (STANDARD, EXPRESS):
        option = options[method.code]
        assert option["name"] == method.name
        assert option["price"]["amount_cents"] == method.price_cents
        assert option["total"]["amount_cents"] == subtotal + method.price_cents
        assert option["total"]["currency"] == "USD"


def test_the_subtotal_sums_every_line(shopper: User, variant: ProductVariant) -> None:
    other = ProductVariant.objects.create(
        product=variant.product, sku="AAL-WAL", name="Walnut", price_cents=500, stock_qty=STOCK
    )
    cart_with(shopper, [(variant, 2), (other, 3)])

    body = quote(shopper, {"address": INLINE_ADDRESS}).json()

    assert body["subtotal"]["amount_cents"] == 2 * UNIT_PRICE + 3 * 500
    assert body["item_count"] == 5


def test_a_cart_that_does_not_exist_is_a_conflict(shopper: User) -> None:
    response = quote(shopper, {"address": INLINE_ADDRESS})

    assert response.status_code == 409
    assert error_code(response) == "CONFLICT"


def test_an_empty_cart_is_a_conflict(shopper: User) -> None:
    Cart.objects.create(user=shopper, status=CartStatus.ACTIVE)

    response = quote(shopper, {"address": INLINE_ADDRESS})

    assert response.status_code == 409


def test_an_address_is_required(shopper: User, variant: ProductVariant) -> None:
    cart_with(shopper, [(variant, 1)])

    response = quote(shopper, {})

    assert response.status_code == 400
    assert error_code(response) == "VALIDATION_ERROR"


def test_two_addresses_are_refused(shopper: User, variant: ProductVariant) -> None:
    """A quote that picked one of two addresses would ship somewhere the customer did not choose."""
    address = save_address(shopper)
    cart_with(shopper, [(variant, 1)])

    response = quote(shopper, {"address_id": address.pk, "address": INLINE_ADDRESS})

    assert response.status_code == 400


def test_another_shoppers_address_is_not_found(
    shopper: User, other_shopper: User, variant: ProductVariant
) -> None:
    """`404`, never `403`: `403` would confirm the id exists (the address book's rule)."""
    someone_elses = save_address(other_shopper)
    cart_with(shopper, [(variant, 1)])

    response = quote(shopper, {"address_id": someone_elses.pk})

    assert response.status_code == 404
    assert error_code(response) == "NOT_FOUND"


def test_a_malformed_inline_address_names_the_field(shopper: User, variant: ProductVariant) -> None:
    """`US-4.1`'s server-side validation, reported on the field a form can point at."""
    cart_with(shopper, [(variant, 1)])

    response = quote(shopper, {"address": {**INLINE_ADDRESS, "postal_code": ""}})

    assert response.status_code == 400
    details = response.json()["error"]["details"]
    assert any(detail["field"].endswith("postal_code") for detail in details)
