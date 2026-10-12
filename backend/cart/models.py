"""Cart models.

Physical design follows `docs/03-architecture/DATA-MODEL.md` section 2: a cart belongs to a user
and to nothing else. `ADR-0017` reversed the guest cart that `ADR-0008` had chosen, so there is no
`session_key` column and no cookie — and because the owner cannot be absent, "one cart per shopper"
is a database fact rather than a rule the endpoints have to remember.

A line stores a quantity and no price: prices are resolved live from the variant until checkout
(`DATA-MODEL.md` section 2), and `M4` snapshots them onto the order, which is where a price that must
not move actually belongs.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


class CartStatus(models.TextChoices):
    """`DATA-MODEL.md` section 3."""

    ACTIVE = "active", "Active"
    CONVERTED = "converted", "Converted"
    ABANDONED = "abandoned", "Abandoned"


class Cart(TimeStampedModel):
    """A shopper's cart, and the states checkout leaves behind.

    `converted` and `abandoned` exist so that the rows an order produced stay distinguishable from
    the one currently in use — the active cart is the only one the endpoints ever reach.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="carts"
    )
    status = models.CharField(max_length=16, choices=CartStatus.choices, default=CartStatus.ACTIVE)

    class Meta(TimeStampedModel.Meta):
        ordering = ("id",)
        constraints = (
            # At most one *active* cart per user. Without it, two concurrent first-adds would each
            # create one and the shopper's lines would be split across two carts — and the endpoints
            # resolve-or-create, which is only safe because this index exists to arbitrate.
            models.UniqueConstraint(
                fields=("user",),
                condition=models.Q(status=CartStatus.ACTIVE),
                name="one_active_cart_per_user",
            ),
        )

    def __str__(self) -> str:
        return f"Cart {self.pk} ({self.status})"


class CartItem(TimeStampedModel):
    """One variant, and how many of it, on one cart."""

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    # `PROTECT`, not `CASCADE`: withdrawing a variant from the catalog must not silently empty the
    # carts holding it. Deleting one that is in a cart is a decision, and this makes it one.
    variant = models.ForeignKey(
        "catalog.ProductVariant", on_delete=models.PROTECT, related_name="cart_items"
    )
    quantity = models.PositiveIntegerField()

    class Meta(TimeStampedModel.Meta):
        ordering = ("id",)
        constraints = (
            # One line per variant: adding a variant that is already on the cart adds to its
            # quantity instead of starting a second line, which is what `US-3.1` describes.
            models.UniqueConstraint(fields=("cart", "variant"), name="unique_variant_per_cart"),
            # A zero-quantity line would be a row no total should count, and removal has its own
            # endpoint (`US-3.3`), so the floor is the database's rather than the API's.
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1), name="cart_item_quantity_at_least_one"
            ),
        )

    def __str__(self) -> str:
        return f"{self.quantity} on cart {self.cart.pk}"
