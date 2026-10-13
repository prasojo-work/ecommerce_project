"""The mock payment endpoints (`API.md` section 7, `ADR-0010`).

The mock is not a special case bolted onto a real flow; it is the only adapter v1 has, behind the
same `PaymentGateway` port a real one would implement. What *is* special is these two routes: they
let a caller state the outcome of a capture, which no real provider's contract contains. So they
answer `404` — as if they did not exist — unless `PAYMENT_PROVIDER=mock`, and the docstrings say
plainly that they are removed when a real provider is integrated.

Both endpoints are scoped to the caller: an order is reached through `user`, so another account's
order is a `404` and not a `403` that would confirm the order number exists, the rule the cart and
the address book share.
"""

from __future__ import annotations

from django.conf import settings
from ninja import Router
from ninja.errors import HttpError

from accounts.auth import AuthenticatedRequest, auth
from accounts.throttling import AuthenticatedRateThrottle
from catalog.schemas import MoneySchema
from orders.models import Order, OrderStatus
from orders.services import InvalidTransition, cancel_order, transition_order
from orders.tasks import send_order_confirmation
from payments.models import Payment, PaymentStatus
from payments.providers import MOCK
from payments.schemas import MockPaymentRequestSchema, MockPaymentResultSchema, PaymentSchema
from payments.services import NoOpenPayment, capture, decline

router = Router(tags=["payments"])

MOCK_ONLY = "The mock payment endpoints exist only while PAYMENT_PROVIDER=mock."
NO_SUCH_ORDER = "No such order."
NOTHING_TO_SETTLE = "This order has no payment awaiting a decision."


def _order_to_settle(user: object, number: str) -> Order:
    """The caller's order with this number, or `404` — including when the routes are switched off."""
    if settings.PAYMENT_PROVIDER != MOCK:
        # A real provider owns its own confirmation; these routes are not part of its contract.
        raise HttpError(404, MOCK_ONLY)
    order = Order.objects.filter(user=user, number=number).first()
    if order is None:
        raise HttpError(404, NO_SUCH_ORDER)
    return order


def _result(order: Order, payment: Payment) -> MockPaymentResultSchema:
    return MockPaymentResultSchema(
        order_number=order.number,
        order_status=order.status,
        payment=PaymentSchema(
            id=payment.pk,
            provider=payment.provider,
            status=payment.status,
            amount=MoneySchema(amount_cents=payment.amount_cents, currency=payment.currency),
            provider_ref=payment.provider_ref,
        ),
    )


@router.post(
    "/payments/mock/confirm",
    response=MockPaymentResultSchema,
    auth=auth,
    throttle=[AuthenticatedRateThrottle()],
    summary="Confirm a mock payment",
)
def confirm_mock_payment(
    request: AuthenticatedRequest, payload: MockPaymentRequestSchema
) -> MockPaymentResultSchema:
    """`US-4.3`: capture the order's payment and move the order to match.

    The capture decides the order's fate, not the caller: `capture` answers with the attempt's status
    and that status picks the transition. A real adapter that *declined* — answering `False` rather
    than raising — would therefore cancel the order exactly as the mock's fail endpoint does, with no
    branch here to remember to update.
    """
    order = _order_to_settle(request.auth, payload.order_number)
    try:
        payment = capture(order)
        if payment.status == PaymentStatus.SUCCEEDED:
            order = transition_order(order, OrderStatus.PAID, note="Mock payment captured.")
        else:
            order = cancel_order(order, note="Mock payment declined.")
    except (NoOpenPayment, InvalidTransition) as exc:
        raise HttpError(409, NOTHING_TO_SETTLE) from exc

    if order.status == OrderStatus.PAID:
        # `ADR-0006`: the receipt is off the request path — the customer has paid, and the mail is not
        # the reason they are waiting. A decline never reaches here, because `order` is what the
        # transition returned, so the email follows the *outcome* and not the attempt.
        send_order_confirmation.enqueue(order_id=order.pk)

    return _result(order, payment)


@router.post(
    "/payments/mock/fail",
    response=MockPaymentResultSchema,
    auth=auth,
    throttle=[AuthenticatedRateThrottle()],
    summary="Decline a mock payment",
)
def fail_mock_payment(
    request: AuthenticatedRequest, payload: MockPaymentRequestSchema
) -> MockPaymentResultSchema:
    """The failure path, on request (`ADR-0010`) — QA drives a decline instead of hoping for one.

    The order is cancelled, which returns its reserved stock (`orders/services.py`): a reservation
    made at order creation is released when the order is, or the shop would sell stock it had already
    set aside for a purchase that never happened.
    """
    order = _order_to_settle(request.auth, payload.order_number)
    try:
        payment = decline(order)
        order = cancel_order(order, note="Mock payment declined.")
    except (NoOpenPayment, InvalidTransition) as exc:
        raise HttpError(409, NOTHING_TO_SETTLE) from exc

    return _result(order, payment)
