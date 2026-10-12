"""Request and response schemas for the mock payment endpoints (`API.md` section 7)."""

from __future__ import annotations

from ninja import Schema

from catalog.schemas import MoneySchema


class MockPaymentRequestSchema(Schema):
    """Both mock endpoints act on an order's open payment.

    The order is named by its human-facing `number`, the same value the confirmation shows, rather
    than by a payment id: the caller is holding an order, and asking it to keep a payment id as well
    would be asking it to remember something the API can look up.
    """

    order_number: str


class PaymentSchema(Schema):
    """One attempt, as a client sees it. Never anything card-shaped, because none is stored."""

    id: int
    provider: str
    status: str
    amount: MoneySchema
    provider_ref: str


class MockPaymentResultSchema(Schema):
    """What the mock answers: the attempt, and where the order ended up.

    The order's status is repeated because it is the outcome the client acts on — `paid` moves the
    shopper to the confirmation, `cancelled` back to the cart — and reading it from the payment alone
    would make the client infer the order's state from a payment's.
    """

    order_number: str
    order_status: str
    payment: PaymentSchema
