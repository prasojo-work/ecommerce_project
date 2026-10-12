"""The guarded transition (`DATA-MODEL.md` section 3, `SCOPE.md` `US-5.5`).

The guard has two halves and both are asserted. A test that only checked the new status would pass on
an implementation that moved the order and silently dropped the event — and the event is the half
`US-5.5` actually asks for, because a status that changed with nobody's name against it is not an
audit trail.

The refusal tests assert the *absence* of a record as well as the unchanged status: a guard that
raised after writing half its work would look identical from the status alone.
"""

from __future__ import annotations

import pytest

from accounts.models import User
from orders.models import Order, OrderEvent, OrderStatus
from orders.services import InvalidTransition, transition_order

pytestmark = pytest.mark.django_db

UNIT_PRICE = 12900
SHIPPING = 1500


@pytest.fixture
def shopper() -> User:
    return User.objects.create_user(
        email="ada@example.com", password="correct-horse-battery-staple"
    )


@pytest.fixture
def order() -> Order:
    return Order.objects.create(
        email="ada@example.com",
        subtotal_cents=UNIT_PRICE,
        shipping_cents=SHIPPING,
        total_cents=UNIT_PRICE + SHIPPING,
        shipping_recipient="Ada Lovelace",
        shipping_line1="12 Analytical Way",
        shipping_city="London",
        shipping_postal_code="EC1A 1BB",
        shipping_country="GB",
    )


def events_for(order: Order) -> list[OrderEvent]:
    """`OrderEvent.objects`, not `order.events` — reverse accessors are untyped here (`ADR-0014`)."""
    return list(OrderEvent.objects.filter(order=order))


def test_a_valid_transition_moves_the_order_and_records_it(order: Order) -> None:
    moved = transition_order(order, OrderStatus.PAID)

    assert moved.pk == order.pk
    assert moved.status == OrderStatus.PAID

    [event] = events_for(order)
    assert event.from_status == OrderStatus.PENDING
    assert event.to_status == OrderStatus.PAID


def test_the_record_names_who_moved_it_and_why(order: Order, shopper: User) -> None:
    transition_order(order, OrderStatus.PAID, actor=shopper, note="Payment captured.")

    [event] = events_for(order)
    assert event.actor == shopper
    assert event.note == "Payment captured."


def test_a_transition_by_the_system_has_no_actor(order: Order) -> None:
    """Checkout moves an order with nobody at the keyboard, and that has to be distinguishable from
    an operator having done it (`DATA-MODEL.md` section 2's `actor`)."""
    transition_order(order, OrderStatus.PAID)

    [event] = events_for(order)
    assert event.actor is None


@pytest.mark.parametrize(
    "to_status",
    [OrderStatus.SHIPPED, OrderStatus.DELIVERED, OrderStatus.PENDING],
)
def test_an_unreachable_status_is_refused_and_changes_nothing(order: Order, to_status: str) -> None:
    with pytest.raises(InvalidTransition):
        transition_order(order, to_status)

    order.refresh_from_db()
    assert order.status == OrderStatus.PENDING
    assert events_for(order) == []


def test_the_refusal_says_where_the_order_was(order: Order) -> None:
    with pytest.raises(InvalidTransition) as raised:
        transition_order(order, OrderStatus.DELIVERED)

    assert OrderStatus.PENDING in str(raised.value)
    assert OrderStatus.DELIVERED in str(raised.value)


def test_a_cancelled_order_cannot_move_again(order: Order) -> None:
    transition_order(order, OrderStatus.CANCELLED)

    with pytest.raises(InvalidTransition):
        transition_order(order, OrderStatus.PAID)


def test_a_delivered_order_can_still_be_cancelled(order: Order) -> None:
    """The `any → cancelled` reading, end to end: a return gets recorded rather than refused."""
    transition_order(order, OrderStatus.PAID)
    transition_order(order, OrderStatus.SHIPPED)
    transition_order(order, OrderStatus.DELIVERED)

    returned = transition_order(order, OrderStatus.CANCELLED, note="Returned by the customer.")

    assert returned.status == OrderStatus.CANCELLED
    assert [event.to_status for event in events_for(order)] == [
        OrderStatus.PAID,
        OrderStatus.SHIPPED,
        OrderStatus.DELIVERED,
        OrderStatus.CANCELLED,
    ]


def test_the_timeline_reads_in_the_order_things_happened(order: Order) -> None:
    transition_order(order, OrderStatus.PAID)
    transition_order(order, OrderStatus.SHIPPED)

    timeline = events_for(order)
    assert [event.to_status for event in timeline] == [OrderStatus.PAID, OrderStatus.SHIPPED]
    assert [event.from_status for event in timeline] == [OrderStatus.PENDING, OrderStatus.PAID]


def test_the_guard_reads_the_locked_row_rather_than_the_callers_copy(order: Order) -> None:
    """A caller holding a stale object must not be able to write a move the database has moved past.

    The copy in memory still says `pending` after the first move, so `pending -> paid` is exactly what
    a guard that trusted the caller would allow. The database says `paid`, and `paid -> paid` is not a
    transition — so the repeat is refused instead of being recorded twice.
    """
    transition_order(order, OrderStatus.PAID)
    assert order.status == OrderStatus.PENDING  # the caller's view, deliberately stale

    with pytest.raises(InvalidTransition):
        transition_order(order, OrderStatus.PAID)

    assert len(events_for(order)) == 1


def test_every_status_the_model_can_hold_is_in_the_table(order: Order) -> None:
    """`can_transition_to` indexes the table with the order's own status, so a status missing from it
    would surface as a `KeyError` at runtime rather than as a refusal."""
    for status in OrderStatus:
        order.status = status

        for target in OrderStatus:
            assert isinstance(order.can_transition_to(target), bool)
