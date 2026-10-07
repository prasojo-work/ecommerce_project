"""Checkout orchestration for the `orders` context.

Everything that turns a cart into an order lives here so the rules stay in one
place: cart conversion, price snapshots, stock reservation under row lock, and
the published functions other contexts (payments) are allowed to call.
"""

from __future__ import annotations

from django.db import transaction

from accounts.models import Address, User
from cart.models import Cart
from catalog.models import ProductVariant
from orders.models import Order, OrderItem
from orders.shipping import cost_for, get_option


class EmptyCartError(Exception):
    """Raised when there is nothing to check out."""


class UnknownShippingMethodError(Exception):
    """Raised when the requested shipping code is not offered."""


class InsufficientStockError(Exception):
    def __init__(self, variant: ProductVariant, requested: int) -> None:
        self.variant = variant
        self.requested = requested
        self.available = variant.stock_qty
        super().__init__(
            f"Only {self.available} left of {variant.product.title} ({variant.name})."
        )


def shipping_address_snapshot(address: Address) -> dict[str, str]:
    """Freeze the delivery address onto the order (DATA-MODEL: PII, immutable)."""
    return {
        "recipient": address.recipient,
        "phone": address.phone,
        "line1": address.line1,
        "line2": address.line2,
        "city": address.city,
        "province": address.province,
        "postal_code": address.postal_code,
        "country": address.country,
    }


@transaction.atomic
def create_order_from_cart(
    *,
    user: User,
    address: Address,
    shipping_code: str,
    idempotency_key: str,
) -> tuple[Order, bool]:
    """Convert the user's cart into a `pending_payment` order.

    Returns ``(order, created)``; ``created`` is False when this is a replay of a
    previous submit carrying the same idempotency key. Prices come from the cart's
    `unit_price_snapshot` — the amount the shopper was actually shown — so the
    charged total can never surprise them (US-5.2).
    """
    existing = Order.objects.filter(idempotency_key=idempotency_key, user=user).first()
    if existing is not None:
        return existing, False

    option = get_option(shipping_code)
    if option is None:
        raise UnknownShippingMethodError(shipping_code)

    cart = Cart.objects.filter(user=user).first()
    if cart is None:
        raise EmptyCartError
    rows = list(cart.items.select_related("variant__product"))
    if not rows:
        raise EmptyCartError

    # Reserve stock under a row lock so two concurrent checkouts cannot oversell.
    locked = {
        variant.pk: variant
        for variant in ProductVariant.objects.select_for_update().filter(
            pk__in=[row.variant_id for row in rows]
        )
    }
    for row in rows:
        variant = locked[row.variant_id]
        if variant.stock_qty < row.quantity:
            raise InsufficientStockError(variant, row.quantity)

    subtotal = sum(row.line_total for row in rows)
    shipping_cost = cost_for(option, subtotal)

    order = Order.objects.create(
        user=user,
        status=Order.Status.PENDING_PAYMENT,
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        total=subtotal + shipping_cost,
        currency="IDR",
        shipping_method=option.code,
        shipping_method_name=option.name,
        shipping_address_snapshot=shipping_address_snapshot(address),
        idempotency_key=idempotency_key,
    )
    OrderItem.objects.bulk_create(
        [
            OrderItem(
                order=order,
                variant=locked[row.variant_id],
                product_title_snapshot=locked[row.variant_id].product.title,
                variant_name_snapshot=locked[row.variant_id].name,
                unit_price=row.unit_price_snapshot,
                quantity=row.quantity,
                line_total=row.line_total,
            )
            for row in rows
        ]
    )
    for row in rows:
        variant = locked[row.variant_id]
        variant.stock_qty -= row.quantity
        variant.save(update_fields=["stock_qty"])

    cart.items.all().delete()
    return order, True


def get_order_for_payment(*, user: User, number: str) -> Order | None:
    """Published read used by the `payments` context."""
    return Order.objects.filter(number=number, user=user).first()


def mark_order_paid(order: Order) -> Order:
    """Published write used by the `payments` context."""
    if order.status == Order.Status.PENDING_PAYMENT:
        order.status = Order.Status.PAID
        order.save(update_fields=["status", "updated_at"])
    return order
