"""Fulfilment state machine and stock-release rules (M5 domain logic).

These are pure domain tests: they drive the service functions directly, so a
failure names the rule rather than an HTTP status. Statuses are plain strings
here for the same reason the state machine speaks them (see `orders/services.py`).
"""

from __future__ import annotations

from typing import Any

import pytest

from accounts.models import Address, User
from catalog.models import ProductVariant
from orders.models import Order, OrderItem
from orders.services import (
    ALLOWED_TRANSITIONS,
    InvalidTransitionError,
    can_transition,
    cancel_order,
    transition_order,
)

RESERVED = 2


@pytest.fixture
def order(db: Any, shopper: User, address: Address, variant: ProductVariant) -> Order:
    """A `pending_payment` order for 2 units — stock already decremented."""
    order = Order.objects.create(
        user=shopper,
        subtotal=2_000_000,
        shipping_cost=0,
        total=2_000_000,
        shipping_method="standard",
        shipping_method_name="Standard delivery",
        shipping_address_snapshot={
            "recipient": "Ada Lovelace",
            "phone": "0812345678",
            "line1": "Jl. Merdeka 1",
            "line2": "",
            "city": "Bandung",
            "province": "West Java",
            "postal_code": "40111",
            "country": "ID",
        },
        idempotency_key="svc-key-1",
    )
    OrderItem.objects.create(
        order=order,
        variant=variant,
        product_title_snapshot="Nordvik Sofa",
        variant_name_snapshot="Fog grey",
        unit_price=1_000_000,
        quantity=RESERVED,
        line_total=2_000_000,
    )
    variant.stock_qty = 3
    variant.save(update_fields=["stock_qty"])
    return order


def status_of(order_pk: int) -> str:
    return Order.objects.get(pk=order_pk).status


def test_the_transition_map_covers_every_status():
    """A new `Order.Status` value must come with a transition rule."""
    declared = {str(value) for value in Order.Status.values}

    assert declared == set(ALLOWED_TRANSITIONS)


def test_can_transition_matrix():
    assert can_transition("pending_payment", "paid")
    assert can_transition("pending_payment", "cancelled")
    assert can_transition("paid", "processing")
    assert can_transition("processing", "shipped")
    assert can_transition("shipped", "completed")
    assert not can_transition("pending_payment", "shipped")
    assert not can_transition("shipped", "cancelled")
    assert not can_transition("completed", "cancelled")
    assert not can_transition("cancelled", "paid")


@pytest.mark.django_db
def test_an_order_walks_the_full_fulfilment_path(order):
    for target in ("paid", "processing", "shipped", "completed"):
        transition_order(order, target)

    assert status_of(order.pk) == "completed"


@pytest.mark.django_db
def test_a_step_cannot_be_skipped(order):
    with pytest.raises(InvalidTransitionError):
        transition_order(order, "shipped")

    assert status_of(order.pk) == "pending_payment"


@pytest.mark.django_db
def test_a_shipped_order_cannot_be_cancelled(order):
    for target in ("paid", "processing", "shipped"):
        transition_order(order, target)

    with pytest.raises(InvalidTransitionError):
        cancel_order(order)

    assert status_of(order.pk) == "shipped"


@pytest.mark.django_db
def test_cancelling_returns_the_reserved_stock(order, variant):
    cancel_order(order)

    variant.refresh_from_db()
    assert variant.stock_qty == 3 + RESERVED
    assert status_of(order.pk) == "cancelled"


@pytest.mark.django_db
def test_cancelling_twice_cannot_restock_the_same_units(order, variant):
    cancel_order(order)

    with pytest.raises(InvalidTransitionError):
        cancel_order(order)

    variant.refresh_from_db()
    assert variant.stock_qty == 5


@pytest.mark.django_db
def test_fulfilment_transitions_leave_stock_alone(order, variant):
    for target in ("paid", "processing"):
        transition_order(order, target)

    variant.refresh_from_db()
    assert variant.stock_qty == 3


@pytest.mark.django_db
def test_status_changes_never_touch_the_order_snapshots(order):
    transition_order(order, "paid")

    item = OrderItem.objects.get(order=order)
    assert item.product_title_snapshot == "Nordvik Sofa"
    assert item.unit_price == 1_000_000
    assert Order.objects.get(pk=order.pk).total == 2_000_000
