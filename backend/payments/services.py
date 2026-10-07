"""Mock gateway (`ADR-0004`).

This context owns payment records. It never touches the `orders` tables directly:
reads and status changes go through the functions `orders.services` publishes.
"""

from __future__ import annotations

from uuid import uuid4

from orders.models import Order
from orders.services import mark_order_paid
from payments.models import Payment


class OrderNotPayableError(Exception):
    """Raised when an order is not in a state that accepts payment."""

    def __init__(self, number: str, status: str) -> None:
        self.number = number
        self.status = status
        super().__init__(f"Order {number} cannot be paid while it is {status}.")


def charge_mock(
    order: Order,
    *,
    simulate_failure: bool = False,
) -> tuple[Payment, bool]:
    """Settle `order` with the mock provider.

    Returns ``(payment, charged)``. Replaying a settled order is idempotent and
    returns the existing payment with ``charged=False``. A simulated failure
    records a `failed` payment and leaves the order `pending_payment`, so the
    shopper can retry (ARCHITECTURE.md §8).
    """
    payment = Payment.objects.filter(order=order).first()
    if payment is not None and payment.status == Payment.Status.SUCCEEDED:
        return payment, False
    if order.status != Order.Status.PENDING_PAYMENT:
        raise OrderNotPayableError(order.number, order.status)

    if payment is None:
        payment = Payment(order=order, provider=Payment.Provider.MOCK, amount=order.total)
    payment.amount = order.total
    payment.provider_reference = f"MOCK-{uuid4().hex[:16].upper()}"
    payment.status = (
        Payment.Status.FAILED if simulate_failure else Payment.Status.SUCCEEDED
    )
    payment.save()

    if payment.status == Payment.Status.SUCCEEDED:
        mark_order_paid(order)
    return payment, True
