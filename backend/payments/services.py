"""The payment lifecycle (`ARCHITECTURE.md` section 4, `ADR-0010`).

A `Payment` is one *attempt* to move money, and an order can carry several: a decline ends the
attempt, not the purchase. This module holds the acts — start an attempt, capture it, or record a
decline — and reaches a provider only through `payments/providers.py`, so nothing here knows which
adapter answered.

The gateway is **synchronous** and that is deliberate; `payments/gateway.py` records why. The mock
waits on nothing, so an `async def` around it would be ceremony, and the start has to sit inside the
order-creation transaction anyway.
"""

from __future__ import annotations

from django.db import transaction

from orders.models import Order
from payments.models import Payment, PaymentStatus
from payments.providers import get_gateway


class NoOpenPayment(RuntimeError):
    """An order was asked to move a payment that is not awaiting a decision."""


def _open_attempt(order: Order) -> Payment:
    """The order's most recent attempt still awaiting an answer.

    "Most recent" rather than "the": `M4` starts one attempt per order, but the model allows more,
    and a retry design would add them. Reaching for the newest keeps this correct when it does.
    """
    attempt = (
        Payment.objects.filter(order=order, status=PaymentStatus.INITIATED).order_by("-id").first()
    )
    if attempt is None:
        raise NoOpenPayment("This order has no payment awaiting a decision.")
    return attempt


@transaction.atomic
def start_payment(order: Order) -> Payment:
    """Ask the gateway to stand ready for `order`'s total, and record the attempt.

    Called inside order creation (`orders/services.py`), so the order and its first payment commit
    together: an order with no payment row would be one no confirm endpoint could ever reach. The
    intent is made *before* anything is asked of the customer, which is what the `initiated` state
    means.
    """
    gateway = get_gateway()
    provider_ref = gateway.create_intent(
        order_number=order.number, amount_cents=order.total_cents, currency=order.currency
    )
    return Payment.objects.create(
        order=order,
        provider=gateway.name,
        status=PaymentStatus.INITIATED,
        amount_cents=order.total_cents,
        currency=order.currency,
        provider_ref=provider_ref,
    )


@transaction.atomic
def capture(order: Order) -> Payment:
    """Ask the gateway to take the money, and record what it answered."""
    attempt = _open_attempt(order)
    succeeded = get_gateway().capture(attempt.provider_ref)
    attempt.status = PaymentStatus.SUCCEEDED if succeeded else PaymentStatus.FAILED
    attempt.save(update_fields=["status", "updated_at"])
    return attempt


@transaction.atomic
def decline(order: Order) -> Payment:
    """Record a decline the caller asked for, without asking the gateway.

    The mock's `capture` always succeeds (`payments/mock.py`), so a *decline* has to be something the
    caller states rather than something the adapter guesses. Keeping the decision at the edge is what
    makes the failure path deterministic — the point of `ADR-0010`'s confirm/fail pair.
    """
    attempt = _open_attempt(order)
    attempt.status = PaymentStatus.FAILED
    attempt.save(update_fields=["status", "updated_at"])
    return attempt
