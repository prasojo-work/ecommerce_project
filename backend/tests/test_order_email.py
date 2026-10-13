"""The confirmation email (`ADR-0006`, `ARCHITECTURE.md` section 6, `SCOPE.md` `US-4.4`).

Two properties. The email exists and says what a receipt has to say — the number, the lines, the
total, and where it went. And it is a consequence of *being paid*: nothing goes out when a cart is
merely turned into an order, and nothing goes out when the payment is declined. A confirmation for an
order that was never paid would be worse than no confirmation at all.

`django.core.mail.outbox` is the surface under test, which is what the `locmem` backend is for: the
transport is mocked, so these assert composition and recipient and never touch a mail server.
"""

import json
from typing import Any

import pytest
from django.conf import settings
from django.core import mail
from django.tasks import TaskResultStatus
from django.test import Client

from accounts.models import User
from accounts.tokens import issue_tokens
from cart.models import Cart, CartItem, CartStatus
from catalog.models import Category, Product, ProductVariant
from orders.models import Order
from orders.services import ShippingAddress, create_order
from orders.shipping import DEFAULT_METHOD_CODE, SHIPPING_METHODS, ShippingMethod
from orders.tasks import send_order_confirmation

pytestmark = pytest.mark.django_db

client = Client()

CONFIRM = "/api/v1/payments/mock/confirm"
FAIL = "/api/v1/payments/mock/fail"

PASSWORD = "correct-horse-battery-staple"
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
def variant() -> ProductVariant:
    category = Category.objects.create(name="Seating", slug="seating")
    product = Product.objects.create(
        category=category, name="Aalto Chair", slug="aalto-chair", base_price_cents=UNIT_PRICE
    )
    return ProductVariant.objects.create(
        product=product, sku="AAL-OAK", name="Oak", price_cents=UNIT_PRICE, stock_qty=3
    )


def auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {issue_tokens(user).access_token}"}


def money(amount_cents: int) -> str:
    return f"USD {amount_cents // 100}.{amount_cents % 100:02d}"


@pytest.fixture
def order(shopper: User, variant: ProductVariant) -> Order:
    cart = Cart.objects.create(user=shopper, status=CartStatus.ACTIVE)
    CartItem.objects.create(cart=cart, variant=variant, quantity=2)
    placed, _ = create_order(
        user=shopper,
        shipping_address=ADDRESS,
        shipping_method=STANDARD,
        email=shopper.email,
    )
    return placed


def settle(user: User, path: str, number: str) -> Any:
    return client.post(
        path,
        data=json.dumps({"order_number": number}),
        content_type="application/json",
        headers=auth(user),
    )


# --- it follows the payment, not the order ---------------------------------------------------


def test_placing_an_order_sends_nothing(order: Order) -> None:
    assert mail.outbox == []


def test_a_declined_payment_sends_nothing(order: Order, shopper: User) -> None:
    assert settle(shopper, FAIL, order.number).status_code == 200

    assert mail.outbox == []


def test_confirming_sends_one_confirmation(order: Order, shopper: User) -> None:
    assert settle(shopper, CONFIRM, order.number).status_code == 200

    assert len(mail.outbox) == 1
    sent = mail.outbox[0]
    assert sent.to == [order.email]
    assert sent.from_email == settings.DEFAULT_FROM_EMAIL
    assert order.number in sent.subject


def test_the_body_carries_the_lines_the_total_and_the_address(
    order: Order, shopper: User, variant: ProductVariant
) -> None:
    settle(shopper, CONFIRM, order.number)

    body = mail.outbox[0].body
    assert order.number in body
    assert variant.name in body
    assert variant.product.name in body
    assert "2 x" in body
    assert money(2 * UNIT_PRICE) in body
    assert money(STANDARD.price_cents) in body
    assert money(2 * UNIT_PRICE + STANDARD.price_cents) in body
    assert ADDRESS.recipient in body
    assert ADDRESS.city in body


def test_the_confirmation_goes_to_the_address_on_the_order(
    shopper: User, variant: ProductVariant
) -> None:
    """Not to the account's email: the order's own address is what was asked to be contacted."""
    cart = Cart.objects.create(user=shopper, status=CartStatus.ACTIVE)
    CartItem.objects.create(cart=cart, variant=variant, quantity=1)
    placed, _ = create_order(
        user=shopper,
        shipping_address=ADDRESS,
        shipping_method=STANDARD,
        email="gift@example.com",
    )

    settle(shopper, CONFIRM, placed.number)

    assert mail.outbox[0].to == ["gift@example.com"]


# --- the task on its own ---------------------------------------------------------------------


def test_the_task_can_be_enqueued_and_reports_success(order: Order) -> None:
    """The `Task` object, not just the function: enqueuing runs through the backend and answers a
    result, which is what a real queue would return too."""
    result = send_order_confirmation.enqueue(order_id=order.pk)

    assert result.status == TaskResultStatus.SUCCESSFUL
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [order.email]
