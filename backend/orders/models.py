"""Order models.

Physical design follows `docs/03-architecture/DATA-MODEL.md` section 2, and the shape is the point.
`ARCHITECTURE.md` section 4 calls an order *the immutable record of a purchase*, so everything that
can change underneath it is **copied onto the row** rather than referenced: a product gets renamed, a
variant gets re-priced, a customer edits the address they shipped to, and last year's order still
says what was bought, for how much, and where it went.

That is why `OrderItem.variant` is a nullable `SET_NULL` where the cart's is a `PROTECT`. A cart is
live intent and may not be silently rearranged, so withdrawing a variant from the catalog is refused
while carts hold it. An order is a receipt: it must survive the SKU being withdrawn, and the snapshot
columns are what it survives *on*. `PROTECT` would make catalog maintenance impossible and `CASCADE`
would delete the receipt.

Money is integer cents in USD (`DATA-MODEL.md` section 5). Where an arithmetic rule can be stated as
a constraint it is, because a total that disagrees with its own parts is a receipt nobody can trust.
"""

from __future__ import annotations

import secrets
from typing import Any

from django.conf import settings
from django.db import models

from core.models import TimeStampedModel


def generate_order_number() -> str:
    """A human-facing order number, e.g. `LSH-9F3A17C4`.

    Random rather than sequential, for two reasons. It is what a customer reads out to support, so it
    should not tell them how many orders the shop has taken — and `GET /orders/{number}` is scoped to
    the caller, but an unguessable identifier means a mistake in that scoping is not by itself enough
    to reach somebody else's order. Eight hex characters is 4.3 billion values; the unique column is
    the arbiter on the vanishing chance of a collision.
    """
    return f"LSH-{secrets.token_hex(4).upper()}"


class OrderStatus(models.TextChoices):
    """`DATA-MODEL.md` section 3."""

    PENDING = "pending", "Pending"
    PAID = "paid", "Paid"
    SHIPPED = "shipped", "Shipped"
    DELIVERED = "delivered", "Delivered"
    CANCELLED = "cancelled", "Cancelled"


# The transitions `DATA-MODEL.md` section 3 allows: forward one step at a time, and `cancelled`
# reachable from anywhere. The last part is the spec's literal wording ("any → cancelled"), and it is
# deliberate rather than an oversight: an order that has shipped or been delivered still has to be
# able to record a cancellation — that is what a return is — and only `cancelled` is unreachable
# *from*, which is what keeps this table acyclic. A terminal state nothing can leave is what makes
# "any → cancelled" safe.
ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    OrderStatus.PENDING: frozenset({OrderStatus.PAID, OrderStatus.CANCELLED}),
    OrderStatus.PAID: frozenset({OrderStatus.SHIPPED, OrderStatus.CANCELLED}),
    OrderStatus.SHIPPED: frozenset({OrderStatus.DELIVERED, OrderStatus.CANCELLED}),
    OrderStatus.DELIVERED: frozenset({OrderStatus.CANCELLED}),
    OrderStatus.CANCELLED: frozenset(),
}


class Order(TimeStampedModel):
    """One purchase, and the state it is in.

    `status` starts at `pending` and only ever moves through `ALLOWED_TRANSITIONS`, which
    `orders/services.py` enforces inside a transaction that also writes the `OrderEvent`. Nothing else
    writes this column.
    """

    number = models.CharField(max_length=20, unique=True, default=generate_order_number)

    # Nullable because `API.md` section 6 gives order creation *optional* authentication, and `email`
    # below is how a guest order is contacted. `SET_NULL` rather than `CASCADE` for the same reason
    # the line's variant is: closing an account must not delete the record of what was bought.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    email = models.EmailField()

    status = models.CharField(
        max_length=16, choices=OrderStatus.choices, default=OrderStatus.PENDING, db_index=True
    )

    subtotal_cents = models.PositiveIntegerField()
    shipping_cents = models.PositiveIntegerField()
    total_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="USD")

    # `DATA-MODEL.md` section 2 calls this a shipping-address *snapshot*, and the `shipping_` prefix is
    # what keeps it from reading like the order's own address. It is where this order went, which is
    # not where the customer lives now. Field names otherwise follow `accounts.Address`.
    shipping_recipient = models.CharField(max_length=120)
    shipping_line1 = models.CharField(max_length=255)
    shipping_line2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=120)
    shipping_region = models.CharField(max_length=120, blank=True)
    shipping_postal_code = models.CharField(max_length=32)
    shipping_country = models.CharField(max_length=2)

    # `NFR-4` asks for idempotent order creation and this is the column that makes it so: the endpoint
    # stores the caller's key with the order it produced, so a replay finds that order instead of
    # making a second one. Nullable because a caller who sends no key is simply not idempotent, and
    # unique because a stored key has to identify exactly one order. Postgres allows any number of
    # NULLs in a unique index, so "no key" costs nothing.
    idempotency_key = models.CharField(max_length=255, null=True, blank=True, unique=True)

    class Meta(TimeStampedModel.Meta):
        # Newest first: this is the order history's reading order (`US-4.5`), and `-id` breaks a tie
        # between two orders created in the same instant so the query stays deterministic.
        ordering = ("-created_at", "-id")
        constraints = (
            # The one arithmetic rule in this table. Tax and discounts are not in v1 (`SCOPE.md`
            # section 5), so an order's total is its subtotal plus its shipping, always — and the day
            # that stops being true, this constraint is what will say so.
            models.CheckConstraint(
                condition=models.Q(
                    total_cents=models.F("subtotal_cents") + models.F("shipping_cents")
                ),
                name="order_total_is_subtotal_plus_shipping",
            ),
            # `DATA-MODEL.md` section 4 asks for money columns `>= 0`. `PositiveIntegerField` is the
            # portability layer for that (Postgres enforces it, SQLite does not), so the rule is stated
            # once more where every backend has to obey it.
            models.CheckConstraint(
                condition=models.Q(subtotal_cents__gte=0)
                & models.Q(shipping_cents__gte=0)
                & models.Q(total_cents__gte=0),
                name="order_money_is_not_negative",
            ),
        )

    def __str__(self) -> str:
        return f"{self.number} ({self.status})"

    def can_transition_to(self, status: str) -> bool:
        """Whether `status` is reachable from where this order is (`DATA-MODEL.md` section 3).

        A question, not an act: what happens on `True` is `orders/services.py`'s business.
        """
        return status in ALLOWED_TRANSITIONS[self.status]


class OrderItem(TimeStampedModel):
    """One line of an order, as it stood when the order was placed."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    # Nullable, and only a way back to a live product: the four columns below are what the receipt
    # says, whether or not the SKU still exists.
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="order_items",
    )

    product_name = models.CharField(max_length=200)
    variant_name = models.CharField(max_length=120)
    unit_price_cents = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()
    line_total_cents = models.PositiveIntegerField()

    class Meta(TimeStampedModel.Meta):
        ordering = ("id",)
        constraints = (
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1), name="order_item_quantity_at_least_one"
            ),
            models.CheckConstraint(
                condition=models.Q(unit_price_cents__gte=0) & models.Q(line_total_cents__gte=0),
                name="order_item_money_is_not_negative",
            ),
            # The line's own arithmetic, for the same reason the order has its total: a line whose
            # total disagrees with its unit price times its quantity is a receipt with a hole in it.
            models.CheckConstraint(
                condition=models.Q(
                    line_total_cents=models.F("unit_price_cents") * models.F("quantity")
                ),
                name="order_item_line_total_is_unit_price_times_quantity",
            ),
        )

    def __str__(self) -> str:
        return f"{self.quantity} x {self.product_name} on {self.order_id}"


class ImmutableOrderEvent(RuntimeError):
    """Raised when something tries to change or remove a recorded event."""


class OrderEvent(models.Model):
    """One status change, written once and never rewritten — the audit trail `US-5.5` asks for.

    This table carries `created_at` and **not** `updated_at`, breaking the convention
    `DATA-MODEL.md` section 2 states for every other table. Deliberate: there is nothing a second
    timestamp on an immutable record could honestly mean, and a column that can only ever equal the
    first one invites someone to write to it.

    `save()` refuses to update a stored event and `delete()` refuses to remove one, so the trail can
    only be appended to. Both guards are one level up from the database, and that is worth saying
    plainly: a `QuerySet.update()` or `QuerySet.delete()` never calls them, and neither does the
    cascade from deleting an order. What they do cover is every ordinary use of the Python object,
    which is where a mistake would actually be made.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="events")
    # Empty on the one event with no previous state: the order's creation, which is the transition
    # from nothing to `pending`. Every later event has both ends. An empty string rather than `NULL`
    # because Django's convention is one kind of emptiness per string field, and `DJ001` holds this
    # codebase to it — so `""` is the sentinel that the choices deliberately do not include. Omitted
    # entirely on a creation event, which stores the field's own empty default.
    from_status = models.CharField(max_length=16, choices=OrderStatus.choices, blank=True)
    to_status = models.CharField(max_length=16, choices=OrderStatus.choices)
    note = models.CharField(max_length=255, blank=True)
    # Who did it. `SET_NULL` for the same reason the order's own FK is: the trail outlives the
    # account. `null` means the system did it — checkout, or a future expiry job — which is a
    # different thing from an operator having done it, and the `note` is where that shows.
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="order_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Chronological: this is a timeline, and the order history renders it in this order.
        ordering = ("created_at", "id")

    def __str__(self) -> str:
        return f"Order {self.order_id}: {self.from_status or 'new'} -> {self.to_status}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk is not None:
            raise ImmutableOrderEvent(
                "An order event records something that happened; it cannot be edited afterwards."
            )
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ImmutableOrderEvent(
            "An order event records something that happened; it cannot be deleted."
        )
