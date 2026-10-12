"""The `PaymentGateway` port (`ADR-0010`).

This module is the seam. It states what the Ordering flow needs from *any* payment provider and
nothing about how one is reached: an intent is created and given a reference, and a reference is
captured. `payments/mock.py` is the only adapter in v1; a real provider is a second adapter plus a
value for `PAYMENT_PROVIDER`, with no change here or in `orders`.

**Synchronous, and that is a decision rather than an omission.** `ADR-0006` names the mock payment
call as an async candidate, and it is the right shape for a real one — but the mock adapter reaches
no network and awaits nothing, so an `async def` around it would be ceremony that buys no concurrency
and complicates the `transaction.atomic()` the capture has to sit in. The port is deliberately
narrow (two calls, no callbacks) so an adapter that *is* I/O-bound can grow an async sibling without
either caller changing its mind about what a gateway is for.
"""

from __future__ import annotations

from typing import Protocol


class PaymentGateway(Protocol):
    """What `payments/services.py` is allowed to assume about a provider."""

    #: The value this adapter answers to in `PAYMENT_PROVIDER`; stored on every `Payment` it makes.
    name: str

    def create_intent(self, *, order_number: str, amount_cents: int, currency: str) -> str:
        """Ask the provider to stand ready for this amount, and return its reference."""
        ...

    def capture(self, provider_ref: str) -> bool:
        """Take the money. `True` if the capture succeeded, `False` if the provider declined it."""
        ...
