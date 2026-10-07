from __future__ import annotations

from typing import Any
from uuid import uuid4

from django.conf import settings
from django.db import models

ORDER_NUMBER_PREFIX = "NDV"


class Order(models.Model):
    """A purchase. Every display value is snapshotted so history never mutates.

    Field set follows `DATA-4.1`. Two additions beyond the documented columns:
    ``shipping_method`` / ``shipping_method_name``, because `ARCHITECTURE.md` §4
    gives this app ownership of "shipping" but `DATA-MODEL.md` enumerates no
    shipping entity, and an immutable snapshot has to record the chosen option.
    """

    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "Pending payment"
        PAID = "paid", "Paid"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    number = models.CharField(max_length=32, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING_PAYMENT,
    )
    subtotal = models.BigIntegerField(help_text="Smallest currency unit.")
    shipping_cost = models.BigIntegerField(default=0)
    total = models.BigIntegerField()
    currency = models.CharField(max_length=3, default="IDR")
    shipping_method = models.CharField(max_length=32)
    shipping_method_name = models.CharField(max_length=120)
    shipping_address_snapshot = models.JSONField()
    idempotency_key = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["user", "-created_at"])]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(subtotal__gte=0), name="order_subtotal_gte_0"
            ),
            models.CheckConstraint(
                condition=models.Q(shipping_cost__gte=0), name="order_shipping_cost_gte_0"
            ),
            models.CheckConstraint(condition=models.Q(total__gte=0), name="order_total_gte_0"),
        ]

    def __str__(self) -> str:
        return self.number

    def save(self, *args: Any, **kwargs: Any) -> None:
        # `number` is a human reference derived from the primary key, so it can
        # only be built after the row exists. The first write uses a throwaway
        # unique value; the second replaces it. Both happen in the caller's
        # transaction, so no partial order is ever visible.
        if self.number:
            super().save(*args, **kwargs)
            return
        self.number = f"TMP-{uuid4().hex[:16]}"
        super().save(*args, **kwargs)
        self.number = f"{ORDER_NUMBER_PREFIX}-{self.created_at:%Y}-{self.pk:06d}"
        super().save(update_fields=["number"])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="order_items",
    )
    product_title_snapshot = models.CharField(max_length=200)
    variant_name_snapshot = models.CharField(max_length=120)
    unit_price = models.BigIntegerField()
    quantity = models.PositiveIntegerField()
    line_total = models.BigIntegerField()

    class Meta:
        ordering = ["id"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1), name="order_item_quantity_gte_1"
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price__gte=0), name="order_item_unit_price_gte_0"
            ),
            models.CheckConstraint(
                condition=models.Q(line_total__gte=0), name="order_item_line_total_gte_0"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.quantity} x {self.product_title_snapshot}"
