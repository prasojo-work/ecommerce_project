from __future__ import annotations

from typing import Any

from ninja import Router, Status
from ninja.errors import HttpError

from accounts.auth import jwt_auth
from orders.services import get_order_for_payment
from payments.models import Payment
from payments.schemas import MockPaymentIn, PaymentOut
from payments.services import OrderNotPayableError, charge_mock

router = Router(tags=["payments"])


def _payment_out(payment: Payment, order_number: str) -> PaymentOut:
    return PaymentOut(
        id=payment.id,
        order_number=order_number,
        provider=payment.provider,
        status=payment.status,
        amount=payment.amount,
        provider_reference=payment.provider_reference,
        created_at=payment.created_at,
    )


@router.post("/payments/mock", auth=jwt_auth, response={200: PaymentOut, 201: PaymentOut})
def pay_with_mock(request: Any, payload: MockPaymentIn) -> Status[PaymentOut]:
    """Simulate a payment. Never charges anything real (`ADR-0004`)."""
    order = get_order_for_payment(user=request.auth, number=payload.order_number)
    if order is None:
        raise HttpError(404, "Order not found.")
    try:
        payment, charged = charge_mock(order, simulate_failure=payload.simulate_failure)
    except OrderNotPayableError as exc:
        raise HttpError(409, str(exc)) from None
    return Status(201 if charged else 200, _payment_out(payment, order.number))
