"""The mock payment adapter (`ADR-0010`, `SCOPE.md` `US-4.3`).

It reaches nothing and charges nobody. `create_intent` mints a reference and `capture` always
succeeds, because the failure path is exercised through the `/payments/mock/fail` endpoint instead —
a *decline* is a thing the caller asks for, not a coin the adapter flips. Keeping the decision at the
edge is what lets the QA of the failure path be deterministic.
"""

from __future__ import annotations

import secrets


class MockGateway:
    """A provider that only pretends. Selected by `PAYMENT_PROVIDER=mock`."""

    name = "mock"

    def create_intent(self, *, order_number: str, amount_cents: int, currency: str) -> str:
        """A reference nobody can look up, prefixed so a stored value is recognisable as fake."""
        # 6 random bytes is 12 hex characters; with the order number and prefix this stays inside the
        # 64-character column `payments.models.Payment.provider_ref` declares.
        return f"mock_{order_number}_{secrets.token_hex(6)}"

    def capture(self, provider_ref: str) -> bool:
        """Always succeeds. The mock makes no charge, so it has no reason to decline one."""
        return True
