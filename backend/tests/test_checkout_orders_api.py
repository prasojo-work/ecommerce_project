"""Contract tests for order creation (`API.md` section 6, `SCOPE.md` `US-4.4`, `NFR-4`).

Three promises are tested before the money is. A token is required (`ADR-0017`); the stock decrement
is *binding* rather than the cart's affordance (`ADR-0017` again); and an `Idempotency-Key` makes a
retried submit safe (`NFR-4`). Each is a claim the code makes in prose, so each gets a test that would
fail if the prose stopped being true.

The snapshots get one too. `ARCHITECTURE.md` calls an order the *immutable record of a purchase*, and
that is only half true if renaming a product or re-pricing a variant afterwards edits the receipt.
"""

import json
import threading
from typing import Any

import pytest
from django.db import connection, connections
from django.test import Client

from accounts.models import Address, User
from accounts.tokens import issue_tokens
from cart.models import Cart, CartItem, CartStatus
from catalog.models import Category, Product, ProductVariant
from orders.models import Order, OrderItem
from orders.shipping import DEFAULT_METHOD_CODE, SHIPPING_METHODS, ShippingMethod
from payments.models import Payment, PaymentStatus

pytestmark = pytest.mark.django_db

client = Client()

ORDERS = "/api/v1/orders"

PASSWORD = "correct-horse-battery-staple"
STOCK = 3
UNIT_PRICE = 12900

STANDARD: ShippingMethod = next(
    method for method in SHIPPING_METHODS if method.code == DEFAULT_METHOD_CODE
)

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
    cart = Cart.objects.create(user=user, status=CartStatus.ACTIVE)
    for product_variant, quantity in products:
        CartItem.objects.create(cart=cart, variant=product_variant, quantity=quantity)
    return cart


def body(**overrides: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {"address": INLINE_ADDRESS, "shipping_method": DEFAULT_METHOD_CODE}
    fields.update(overrides)
    return fields


def place(user: User, payload: dict[str, Any] | None = None, key: str | None = None) -> Any:
    headers = auth(user)
    if key is not None:
        headers["Idempotency-Key"] = key
    return client.post(
        ORDERS,
        data=json.dumps(body() if payload is None else payload),
        content_type="application/json",
        headers=headers,
    )


def error_code(response: Any) -> str:
    return response.json()["error"]["code"]


# --- who may place an order (`ADR-0017`) ----------------------------------------------------


def test_placing_an_order_requires_a_token() -> None:
    response = client.post(ORDERS, data=json.dumps(body()), content_type="application/json")

    assert response.status_code == 401
    assert error_code(response) == "UNAUTHENTICATED"


# --- the receipt ----------------------------------------------------------------------------


def test_placing_an_order_answers_the_receipt(shopper: User, variant: ProductVariant) -> None:
    cart_with(shopper, [(variant, 2)])

    response = place(shopper)

    assert response.status_code == 201
    order = response.json()
    assert order["number"].startswith("LSH-")
    assert order["status"] == "pending"
    assert order["email"] == shopper.email
    assert order["subtotal"] == {"amount_cents": 2 * UNIT_PRICE, "currency": "USD"}
    assert order["shipping"]["amount_cents"] == STANDARD.price_cents
    assert order["total"] == {
        "amount_cents": 2 * UNIT_PRICE + STANDARD.price_cents,
        "currency": "USD",
    }
    assert order["shipping_address"]["recipient"] == INLINE_ADDRESS["recipient"]
    assert len(order["items"]) == 1
    assert order["items"][0]["product_name"] == variant.product.name
    assert order["items"][0]["unit_price"] == {"amount_cents": UNIT_PRICE, "currency": "USD"}
    assert order["items"][0]["line_total"] == {
        "amount_cents": 2 * UNIT_PRICE,
        "currency": "USD",
    }


def test_the_accounts_email_is_used_unless_the_payload_overrides_it(
    shopper: User, variant: ProductVariant
) -> None:
    cart_with(shopper, [(variant, 1)])

    assert place(shopper).json()["email"] == shopper.email

    cart_with(shopper, [(variant, 1)])
    overridden = place(shopper, body(email="gift@example.com"))

    assert overridden.json()["email"] == "gift@example.com"


def test_a_saved_address_may_be_named_instead(shopper: User, variant: ProductVariant) -> None:
    address = save_address(shopper)
    cart_with(shopper, [(variant, 1)])

    response = place(shopper, body(address=INLINE_ADDRESS, address_id=address.pk))

    assert response.status_code == 400  # both at once is ambiguous, not a preference

    response = place(shopper, {"address_id": address.pk, "shipping_method": DEFAULT_METHOD_CODE})

    assert response.status_code == 201
    assert response.json()["shipping_address"]["recipient"] == SAVED_ADDRESS["recipient"]


def test_the_receipt_keeps_what_was_bought_at_the_price_it_was(
    shopper: User, variant: ProductVariant
) -> None:
    """The snapshot, not the live row: catalog edits after the sale do not rewrite the order."""
    cart_with(shopper, [(variant, 2)])
    number = place(shopper).json()["number"]

    variant.product.name = "Aalto Chair (renamed)"
    variant.product.save(update_fields=["name"])
    variant.price_cents = UNIT_PRICE * 10
    variant.save(update_fields=["price_cents"])

    item = OrderItem.objects.get(order__number=number)
    assert item.product_name == "Aalto Chair"
    assert item.unit_price_cents == UNIT_PRICE


# --- the cart it consumes -------------------------------------------------------------------


def test_the_stock_is_decremented(shopper: User, variant: ProductVariant) -> None:
    cart_with(shopper, [(variant, 2)])

    place(shopper)

    variant.refresh_from_db()
    assert variant.stock_qty == STOCK - 2


def test_the_cart_is_converted_rather_than_deleted(shopper: User, variant: ProductVariant) -> None:
    cart = cart_with(shopper, [(variant, 1)])

    place(shopper)

    cart.refresh_from_db()
    assert cart.status == CartStatus.CONVERTED
    assert CartItem.objects.filter(cart=cart).count() == 1


def test_a_payment_is_started_with_the_order(shopper: User, variant: ProductVariant) -> None:
    cart_with(shopper, [(variant, 1)])

    number = place(shopper).json()["number"]

    payment = Payment.objects.get(order__number=number)
    assert payment.status == PaymentStatus.INITIATED
    assert payment.provider == "mock"
    assert payment.amount_cents == UNIT_PRICE + STANDARD.price_cents
    assert payment.provider_ref


def test_an_empty_cart_is_a_conflict(shopper: User) -> None:
    response = place(shopper)

    assert response.status_code == 409
    assert error_code(response) == "CONFLICT"
    assert Order.objects.count() == 0


def test_more_than_the_stock_is_a_conflict_that_writes_nothing(
    shopper: User, variant: ProductVariant
) -> None:
    cart_with(shopper, [(variant, STOCK + 1)])

    response = place(shopper)

    assert response.status_code == 409
    assert str(STOCK) in response.json()["error"]["message"]
    assert Order.objects.count() == 0
    variant.refresh_from_db()
    assert variant.stock_qty == STOCK


def test_a_withdrawn_variant_is_a_conflict(shopper: User, variant: ProductVariant) -> None:
    cart_with(shopper, [(variant, 1)])
    variant.is_active = False
    variant.save(update_fields=["is_active"])

    response = place(shopper)

    assert response.status_code == 409
    assert "no longer available" in response.json()["error"]["message"]


# --- the address and the method -------------------------------------------------------------


def test_an_address_is_required(shopper: User, variant: ProductVariant) -> None:
    cart_with(shopper, [(variant, 1)])

    response = place(shopper, {"shipping_method": DEFAULT_METHOD_CODE})

    assert response.status_code == 400


def test_another_shoppers_address_is_not_found(
    shopper: User, other_shopper: User, variant: ProductVariant
) -> None:
    someone_elses = save_address(other_shopper)
    cart_with(shopper, [(variant, 1)])

    response = place(
        shopper, {"address_id": someone_elses.pk, "shipping_method": DEFAULT_METHOD_CODE}
    )

    assert response.status_code == 404
    assert error_code(response) == "NOT_FOUND"


def test_an_unknown_shipping_method_is_a_validation_error(
    shopper: User, variant: ProductVariant
) -> None:
    cart_with(shopper, [(variant, 1)])

    response = place(shopper, body(shipping_method="teleport"))

    assert response.status_code == 400
    assert error_code(response) == "VALIDATION_ERROR"


# --- idempotency (`NFR-4`) ------------------------------------------------------------------


def test_an_idempotency_key_makes_a_retry_a_no_op(shopper: User, variant: ProductVariant) -> None:
    """The second submit answers `200` with the *first* order, and neither the catalog nor the cart
    moves again."""
    cart_with(shopper, [(variant, 2)])

    first = place(shopper, key="submit-1")
    second = place(shopper, key="submit-1")

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["number"] == first.json()["number"]
    assert Order.objects.count() == 1
    variant.refresh_from_db()
    assert variant.stock_qty == STOCK - 2


def test_a_different_key_is_a_different_order(shopper: User, variant: ProductVariant) -> None:
    cart_with(shopper, [(variant, 1)])
    assert place(shopper, key="a").status_code == 201

    cart_with(shopper, [(variant, 1)])
    assert place(shopper, key="b").status_code == 201

    assert Order.objects.count() == 2


# --- concurrency ----------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(
    connection.vendor != "postgresql",
    reason="SQLite ignores `SELECT … FOR UPDATE`, so it cannot show what the lock is for.",
)
def test_two_concurrent_orders_cannot_oversell_the_last_unit(
    shopper: User, variant: ProductVariant
) -> None:
    """What the row lock and the conditional decrement in `orders/services.py` are for.

    With one unit left and two carts asking for it, exactly one order may exist: without the lock both
    requests would read `stock_qty == 1`, both would take it, and the shop would have sold a variant
    it does not have. The transaction is committed (`transaction=True`) so the two threads can see each
    other — the same reason the cart's concurrency test does it.
    """
    variant.stock_qty = 1
    variant.save(update_fields=["stock_qty"])
    header = auth(shopper)
    outcome: list[int] = []

    def place_once(key: str) -> None:
        try:
            response = Client().post(
                ORDERS,
                data=json.dumps(body()),
                content_type="application/json",
                headers={**header, "Idempotency-Key": key},
            )
            outcome.append(response.status_code)
        finally:
            # Each thread owns a connection; leaving one open keeps the test database busy and
            # pytest cannot drop it at teardown.
            connections.close_all()

    cart_with(shopper, [(variant, 1)])

    threads = [threading.Thread(target=place_once, args=(key,)) for key in ("k1", "k2")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    assert sorted(outcome) == [201, 409]
    assert Order.objects.count() == 1
    variant.refresh_from_db()
    assert variant.stock_qty == 0
