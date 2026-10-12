"""Payment models (`DATA-MODEL.md` section 2, `ARCHITECTURE.md` section 4).

A `Payment` is one *attempt* to move money for an order, and the plural is deliberate: an order can
carry several, because a decline ends an attempt rather than the purchase. The row records what the
gateway was asked for (`provider_ref`), what it is worth (`amount_cents`) and how it ended
(`status`).

It holds **no card data of any kind**. `ADR-0010` keeps v1 out of PCI scope, and the way to stay out
is to never have the data in the first place — there is no column here for a number, a brand or a
last four, and the absence is the control.
"""

from __future__ import annotations

from django.db import models

from core.models import TimeStampedModel
from orders.models import Order


class PaymentStatus(models.TextChoices):
    """`DATA-MODEL.md` section 3."""

    INITIATED = "initiated", "Initiated"
    SUCCEEDED = "succeeded", "Succeeded"
    FAILED = "failed", "Failed"


class Payment(TimeStampedModel):
    """One attempt to capture an order's total."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")

    # Which adapter produced `provider_ref`. Stored per row rather than read from settings when the
    # payment is displayed: an order outlives the configuration that took it, and a receipt that
    # named today's provider for yesterday's charge would be a lie (`ADR-0010`).
    provider = models.CharField(max_length=32)

    status = models.CharField(
        max_length=16,
        choices=PaymentStatus.choices,
        default=PaymentStatus.INITIATED,
        db_index=True,
    )
    amount_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="USD")

    # The gateway's own handle for this attempt — what `capture` is called with. Empty only between
    # the row being built and the intent coming back; `payments/services.py` never leaves it empty.
    provider_ref = models.CharField(max_length=64, blank=True)

    class Meta(TimeStampedModel.Meta):
        ordering = ("id",)
        constraints = (
            # `DATA-MODEL.md` section 4 asks for money columns `>= 0`; stated again where every
            # backend has to obey it, since SQLite does not carry `PositiveIntegerField`'s range.
            models.CheckConstraint(
                condition=models.Q(amount_cents__gte=0), name="payment_amount_is_not_negative"
            ),
        )

    def __str__(self) -> str:
        return f"{self.provider} {self.status} {self.amount_cents} for order {self.order.pk}"
