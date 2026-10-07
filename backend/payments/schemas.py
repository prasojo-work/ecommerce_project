from __future__ import annotations

from datetime import datetime

from ninja import Schema


class MockPaymentIn(Schema):
    order_number: str
    simulate_failure: bool = False


class PaymentOut(Schema):
    id: int
    order_number: str
    provider: str
    status: str
    amount: int
    provider_reference: str
    created_at: datetime
