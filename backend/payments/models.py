from __future__ import annotations

from django.db import models


class Payment(models.Model):
    """A payment attempt against an order (`DATA-5.1`). One row per order."""

    class Provider(models.TextChoices):
        MOCK = "mock", "Mock"
        STRIPE = "stripe", "Stripe"
        MIDTRANS = "midtrans", "Midtrans"

    class Status(models.TextChoices):
        INITIATED = "initiated", "Initiated"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        REFUNDED = "refunded", "Refunded"

    order = models.OneToOneField(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="payment",
    )
    provider = models.CharField(
        max_length=20, choices=Provider.choices, default=Provider.MOCK
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.INITIATED
    )
    amount = models.BigIntegerField(help_text="Smallest currency unit.")
    provider_reference = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gte=0), name="payment_amount_gte_0"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.provider}:{self.status} for order {self.order_id}"
