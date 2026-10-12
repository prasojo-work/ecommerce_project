"""The orders' database rules (`DATA-MODEL.md` section 2 and section 4).

Every rule here is a constraint rather than a convention, so each is asserted by trying to break it.
A receipt whose total disagrees with its own parts is only worth refusing if the database refuses it,
and a snapshot is only worth taking if it survives the catalogue and the account moving underneath it
— which is what the two `SET_NULL` tests are about, and what separates an order from a cart.
"""

from __future__ import annotations

import re
from typing import Any

import pytest
from django.db import IntegrityError, transaction

from accounts.models import User
from catalog.models import Category, Product, ProductVariant
from orders.models import (
    ImmutableOrderEvent,
    Order,
    OrderEvent,
    OrderItem,
    OrderStatus,
    generate_order_number,
)

pytestmark = pytest.mark.django_db

UNIT_PRICE = 12900
QUANTITY = 2
SHIPPING = 1500


def an_order(**overrides: Any) -> Order:
    """An order that satisfies every constraint, so that a test can break exactly one of them."""
    fields: dict[str, Any] = {
        "email": "ada@example.com",
        "subtotal_cents": UNIT_PRICE * QUANTITY,
        "shipping_cents": SHIPPING,
        "total_cents": UNIT_PRICE * QUANTITY + SHIPPING,
        "shipping_recipient": "Ada Lovelace",
        "shipping_line1": "12 Analytical Way",
        "shipping_city": "London",
        "shipping_postal_code": "EC1A 1BB",
        "shipping_country": "GB",
    }
    fields.update(overrides)
    return Order.objects.create(**fields)


@pytest.fixture
def shopper() -> User:
    return User.objects.create_user(
        email="ada@example.com", password="correct-horse-battery-staple"
    )


@pytest.fixture
def variant() -> ProductVariant:
    category = Category.objects.create(name="Seating", slug="seating")
    product = Product.objects.create(
        category=category, name="Aalto Chair", slug="aalto-chair", base_price_cents=UNIT_PRICE
    )
    return ProductVariant.objects.create(
        product=product, sku="AAL-OAK", name="Oak", price_cents=UNIT_PRICE, stock_qty=5
    )


@pytest.fixture
def order(shopper: User) -> Order:
    return an_order(user=shopper)


@pytest.fixture
def line(order: Order, variant: ProductVariant) -> OrderItem:
    return OrderItem.objects.create(
        order=order,
        variant=variant,
        product_name=variant.product.name,
        variant_name=variant.name,
        unit_price_cents=UNIT_PRICE,
        quantity=QUANTITY,
        line_total_cents=UNIT_PRICE * QUANTITY,
    )


def test_an_order_number_is_readable_and_carries_no_sequence() -> None:
    numbers = [generate_order_number() for _ in range(50)]

    assert all(re.fullmatch(r"LSH-[0-9A-F]{8}", number) for number in numbers)
    # A customer reads this out to support, so it must not say how many orders the shop has taken —
    # and a serial would. Two orders placed in the same instant must also not be guessable from each
    # other, which is why these have to differ rather than merely be well formatted.
    assert len(set(numbers)) == len(numbers)


def test_an_order_number_is_unique(order: Order) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        an_order(number=order.number)


def test_a_total_that_is_not_the_sum_of_its_parts_is_refused(order: Order) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        an_order(total_cents=order.total_cents + 1)


def test_money_cannot_be_negative() -> None:
    # The total has to break one rule at a time: `total = subtotal + shipping` is satisfied here so
    # that the `>= 0` constraint is the one being tested rather than the arithmetic one.
    with pytest.raises(IntegrityError), transaction.atomic():
        an_order(subtotal_cents=-1, total_cents=SHIPPING - 1)


def test_a_line_of_zero_quantity_is_refused(order: Order) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        OrderItem.objects.create(
            order=order,
            product_name="Aalto Chair",
            variant_name="Oak",
            unit_price_cents=UNIT_PRICE,
            quantity=0,
            line_total_cents=0,
        )


def test_a_line_total_that_is_not_the_unit_price_times_the_quantity_is_refused(
    order: Order, variant: ProductVariant
) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        OrderItem.objects.create(
            order=order,
            variant=variant,
            product_name="Aalto Chair",
            variant_name="Oak",
            unit_price_cents=UNIT_PRICE,
            quantity=QUANTITY,
            line_total_cents=UNIT_PRICE * QUANTITY + 1,
        )


def test_a_line_outlives_its_variant_being_withdrawn(
    line: OrderItem, variant: ProductVariant
) -> None:
    """`SET_NULL`, where the cart uses `PROTECT`: the catalogue moves on, the receipt does not.

    This is the whole reason the line carries snapshots. With `PROTECT` a shop could never withdraw a
    SKU that had ever been sold; with `CASCADE` it would delete the evidence that it had been.
    """
    variant.delete()

    line.refresh_from_db()
    assert line.variant is None
    assert line.product_name == "Aalto Chair"
    assert line.variant_name == "Oak"
    assert line.unit_price_cents == UNIT_PRICE


def test_an_order_outlives_its_account_being_deleted(order: Order, shopper: User) -> None:
    shopper.delete()

    order.refresh_from_db()
    assert order.user is None
    # The email is a snapshot for the same reason the address is: the record of where the receipt
    # went has to survive the account it was sent to.
    assert order.email == "ada@example.com"


def test_the_creation_event_has_no_previous_status(order: Order) -> None:
    event = OrderEvent.objects.create(order=order, to_status=OrderStatus.PENDING)

    # Empty rather than `NULL`: `DJ001` keeps string fields to a single kind of emptiness.
    assert event.from_status == ""


def test_a_stored_event_cannot_be_edited(order: Order) -> None:
    event = OrderEvent.objects.create(order=order, to_status=OrderStatus.PENDING)

    event.to_status = OrderStatus.PAID
    with pytest.raises(ImmutableOrderEvent):
        event.save()

    stored = OrderEvent.objects.get(pk=event.pk)
    assert stored.to_status == OrderStatus.PENDING


def test_a_stored_event_cannot_be_deleted(order: Order) -> None:
    event = OrderEvent.objects.create(order=order, to_status=OrderStatus.PENDING)

    with pytest.raises(ImmutableOrderEvent):
        event.delete()

    assert OrderEvent.objects.filter(pk=event.pk).exists()


@pytest.mark.parametrize(
    ("from_status", "to_status", "allowed"),
    [
        (OrderStatus.PENDING, OrderStatus.PAID, True),
        (OrderStatus.PENDING, OrderStatus.SHIPPED, False),
        (OrderStatus.PAID, OrderStatus.SHIPPED, True),
        (OrderStatus.PAID, OrderStatus.PENDING, False),
        (OrderStatus.SHIPPED, OrderStatus.DELIVERED, True),
        (OrderStatus.DELIVERED, OrderStatus.SHIPPED, False),
    ],
)
def test_the_status_machine_moves_forward_one_step_at_a_time(
    order: Order, from_status: str, to_status: str, allowed: bool
) -> None:
    order.status = from_status

    assert order.can_transition_to(to_status) is allowed


@pytest.mark.parametrize(
    "from_status",
    [status for status in OrderStatus if status is not OrderStatus.CANCELLED],
)
def test_cancelling_is_reachable_from_every_status_that_is_not_cancelled(
    order: Order, from_status: str
) -> None:
    """`DATA-MODEL.md` section 3 says "any → cancelled", and it means it, including `delivered`:
    that is what a return records. Only `cancelled` itself is exempt — there is nothing to cancel."""
    order.status = from_status

    assert order.can_transition_to(OrderStatus.CANCELLED) is True


def test_cancelled_is_terminal(order: Order) -> None:
    order.status = OrderStatus.CANCELLED

    assert [status for status in OrderStatus if order.can_transition_to(status)] == []
