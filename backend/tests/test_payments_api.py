"""Contract tests for the mock payment endpoints (`API.md` section 7, `ADR-0010`).

Two claims run through these. The first is that the mock drives *both* outcomes — `ADR-0010` chose a
provider behind a port precisely so the decline path would be testable rather than hoped for, and a
failed payment has to leave the shop as if it never happened, which means the stock order creation
reserved comes back. The second is that the routes are the mock's alone: switched to a real provider
they answer `404`, as if they had never been part of the contract.
"""

import json
from typing import Any

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import Client

from accounts.models import User
from accounts.tokens import issue_tokens
from cart.models import Cart, CartItem, CartStatus
from catalog.models import Category, Product, ProductVariant
from orders.models import Order, OrderEvent, OrderStatus
from orders.services import ShippingAddress, create_order
from orders.shipping import DEFAULT_METHOD_CODE, SHIPPING_METHODS, ShippingMethod
from payments.models import Payment, PaymentStatus
from payments.providers import get_gateway

pytestmark = pytest.mark.django_db

client = Client()

CONFIRM = "/api/v1/payments/mock/confirm"
FAIL = "/api/v1/payments/mock/fail"

PASSWORD = "correct-horse-battery-staple"
STOCK = 3
UNIT_PRICE = 12900

STANDARD: ShippingMethod = next(
    method for method in SHIPPING_METHODS if method.code == DEFAULT_METHOD_CODE
)

ADDRESS = ShippingAddress(
    recipient="Ada Lovelace",
    line1="12 Analytical Way",
    city="London",
    postal_code="EC1A 1BB",
    country="GB",
)


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


@pytest.fixture
def order(shopper: User, variant: ProductVariant) -> Order:
    """A placed order with an `initiated` payment, built through the service the endpoint uses."""
    cart = Cart.objects.create(user=shopper, status=CartStatus.ACTIVE)
    CartItem.objects.create(cart=cart, variant=variant, quantity=2)
    placed, _ = create_order(
        user=shopper,
        shipping_address=ADDRESS,
        shipping_method=STANDARD,
        email=shopper.email,
    )
    return placed


def auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {issue_tokens(user).access_token}"}


def post(user: User, path: str, number: str) -> Any:
    return client.post(
        path,
        data=json.dumps({"order_number": number}),
        content_type="application/json",
        headers=auth(user),
    )


def error_code(response: Any) -> str:
    return response.json()["error"]["code"]


# --- who may settle a payment ---------------------------------------------------------------


@pytest.mark.parametrize("path", [CONFIRM, FAIL])
def test_the_mock_endpoints_require_a_token(path: str) -> None:
    response = client.post(
        path, data=json.dumps({"order_number": "LSH-00000000"}), content_type="application/json"
    )

    assert response.status_code == 401
    assert error_code(response) == "UNAUTHENTICATED"


# --- the two paths `ADR-0010` exists to make testable ---------------------------------------


def test_confirming_captures_the_payment_and_pays_the_order(order: Order, shopper: User) -> None:
    response = post(shopper, CONFIRM, order.number)

    assert response.status_code == 200
    result = response.json()
    assert result["order_status"] == OrderStatus.PAID
    assert result["payment"]["status"] == PaymentStatus.SUCCEEDED
    assert result["payment"]["provider"] == "mock"
    assert result["payment"]["provider_ref"]

    order.refresh_from_db()
    assert order.status == OrderStatus.PAID
    assert Payment.objects.get(order=order).status == PaymentStatus.SUCCEEDED


def test_failing_declines_the_payment_and_returns_the_stock(
    order: Order, shopper: User, variant: ProductVariant
) -> None:
    """A decline ends the *purchase*, not just the attempt: the order is cancelled and the stock it
    reserved comes back, or a failed payment would shrink the shop's sellable quantity forever."""
    variant.refresh_from_db()
    assert variant.stock_qty == STOCK - 2  # reserved by order creation

    response = post(shopper, FAIL, order.number)

    assert response.status_code == 200
    result = response.json()
    assert result["order_status"] == OrderStatus.CANCELLED
    assert result["payment"]["status"] == PaymentStatus.FAILED

    order.refresh_from_db()
    assert order.status == OrderStatus.CANCELLED
    variant.refresh_from_db()
    assert variant.stock_qty == STOCK


def test_an_order_carries_the_event_of_its_own_transitions(order: Order, shopper: User) -> None:
    post(shopper, CONFIRM, order.number)

    moves = list(
        OrderEvent.objects.filter(order=order)
        .order_by("id")
        .values_list("from_status", "to_status")
    )
    assert moves == [("", OrderStatus.PENDING), (OrderStatus.PENDING, OrderStatus.PAID)]


# --- settling twice, and settling what cannot be settled ------------------------------------


def test_confirming_twice_is_a_conflict(order: Order, shopper: User) -> None:
    assert post(shopper, CONFIRM, order.number).status_code == 200

    second = post(shopper, CONFIRM, order.number)

    assert second.status_code == 409
    assert error_code(second) == "CONFLICT"
    assert Payment.objects.filter(order=order).count() == 1


def test_failing_twice_is_a_conflict(order: Order, shopper: User, variant: ProductVariant) -> None:
    assert post(shopper, FAIL, order.number).status_code == 200

    second = post(shopper, FAIL, order.number)

    assert second.status_code == 409
    # The stock was returned exactly once, so a double decline cannot stock a shelf that never left.
    variant.refresh_from_db()
    assert variant.stock_qty == STOCK


def test_confirming_a_cancelled_order_is_a_conflict(
    order: Order, shopper: User, variant: ProductVariant
) -> None:
    post(shopper, FAIL, order.number)

    response = post(shopper, CONFIRM, order.number)

    assert response.status_code == 409
    variant.refresh_from_db()
    assert variant.stock_qty == STOCK


# --- the caller's own orders ----------------------------------------------------------------


def test_another_accounts_order_is_not_found(order: Order, other_shopper: User) -> None:
    response = post(other_shopper, CONFIRM, order.number)

    assert response.status_code == 404
    assert error_code(response) == "NOT_FOUND"
    order.refresh_from_db()
    assert order.status == OrderStatus.PENDING


def test_an_unknown_order_number_is_a_404(shopper: User) -> None:
    response = post(shopper, CONFIRM, "LSH-00000000")

    assert response.status_code == 404


# --- the mock is the only thing these routes belong to -------------------------------------


@pytest.mark.parametrize("path", [CONFIRM, FAIL])
def test_the_mock_endpoints_are_absent_for_a_real_provider(
    path: str, order: Order, shopper: User, settings: Any
) -> None:
    settings.PAYMENT_PROVIDER = "stripe"

    response = post(shopper, path, order.number)

    assert response.status_code == 404
    order.refresh_from_db()
    assert order.status == OrderStatus.PENDING


def test_a_provider_naming_no_adapter_is_refused_rather_than_defaulted_to_the_mock(
    settings: Any,
) -> None:
    """`ADR-0010`: exactly one adapter exists in v1, and which one is configuration rather than
    code. An unrecognised value is a deployment mistake, and quietly serving the mock would take a
    real payment nowhere while still reporting success — so the lookup raises instead."""
    settings.PAYMENT_PROVIDER = "stripe"

    with pytest.raises(ImproperlyConfigured, match="stripe"):
        get_gateway()


def test_a_payment_renders_its_provider_its_state_and_its_order(order: Order) -> None:
    """Read in a log line and in the console, so the order is named in it: the row on its own does
    not say which purchase it belongs to."""
    payment = Payment.objects.get(order=order)

    assert str(payment) == (
        f"mock {PaymentStatus.INITIATED} {payment.amount_cents} for order {order.pk}"
    )
