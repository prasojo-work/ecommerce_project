"""The orders context's public interface (`ARCHITECTURE.md` section 4).

The models hold the shape and the rules; this module holds the acts. Creating an order, moving its
status, and cancelling it all belong here for the same reason: each has to validate, write more than
one row, and leave nothing half-done if it fails. The endpoints go through here rather than assigning
`order.status`, which is what makes `ALLOWED_TRANSITIONS` a rule instead of a suggestion.

**Order creation is the one place stock is decremented** (`ADR-0017`). The cart's cap is an
affordance; the binding, race-safe deed is here, inside the transaction that writes the order, so
either the stock moves and the order exists or neither does. Cancelling returns it, or the
reservation would leak.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from cart.models import Cart, CartItem, CartStatus
from catalog.models import ProductVariant
from orders.models import ALLOWED_TRANSITIONS, Order, OrderEvent, OrderItem, OrderStatus
from orders.shipping import ShippingMethod
from payments.services import start_payment

if TYPE_CHECKING:
    from accounts.models import Address, User


class InvalidTransition(RuntimeError):
    """An order was asked to reach a status it cannot reach from where it is."""


class EmptyCart(RuntimeError):
    """Checkout was asked to sell a cart with nothing in it."""


class NotForSale(RuntimeError):
    """A line names a variant — or a product — that is no longer on sale."""


class InsufficientStock(RuntimeError):
    """A line asks for more of a variant than is in stock."""


@dataclass(frozen=True)
class ShippingAddress:
    """The shipping-address snapshot `orders.models.Order` stores, never an `Address` reference.

    A receipt says where that order went, which is not where the customer lives now. The endpoint
    resolves an address — saved or inline — into this, and the order keeps the seven strings.
    """

    recipient: str
    line1: str
    city: str
    postal_code: str
    country: str
    line2: str = ""
    region: str = ""

    @classmethod
    def from_address(cls, address: Address) -> ShippingAddress:
        return cls(
            recipient=address.recipient,
            line1=address.line1,
            line2=address.line2,
            city=address.city,
            region=address.region,
            postal_code=address.postal_code,
            country=address.country,
        )


@transaction.atomic
def transition_order(
    order: Order, to_status: str, *, actor: User | None = None, note: str = ""
) -> Order:
    """Move `order` to `to_status` and record who did it (`US-5.5`, `DATA-MODEL.md` section 3).

    The guard and the record are one transaction on purpose. An audit trail written in a second step
    is an audit trail with a gap in it whenever the second step fails, and a gap is worse than no
    trail because it still looks complete.

    The row is locked for the duration. Two operators reading `paid` at the same moment would both
    find `shipped` reachable and both write an event claiming to have moved the order from the same
    place — one transition, two records of it.

    Raises `InvalidTransition` rather than returning a flag: every caller so far is answering a
    request that should become a `409`, and an exception is what carries that decision outward
    without every layer in between having to pass it along.
    """
    locked = Order.objects.select_for_update().get(pk=order.pk)

    from_status = locked.status
    if to_status not in ALLOWED_TRANSITIONS[from_status]:
        raise InvalidTransition(f"An order that is {from_status} cannot become {to_status}.")

    locked.status = to_status
    # `updated_at` is `auto_now`, so it only moves if it is named here.
    locked.save(update_fields=["status", "updated_at"])

    OrderEvent.objects.create(
        order=locked, from_status=from_status, to_status=to_status, actor=actor, note=note
    )

    return locked


def _locked_cart(user: User) -> Cart:
    """The caller's active cart, locked — or `EmptyCart` when there is none."""
    cart = Cart.objects.select_for_update().filter(user=user, status=CartStatus.ACTIVE).first()
    if cart is None:
        raise EmptyCart("Your cart is empty.")
    return cart


def _locked_variants(variant_ids: list[int]) -> dict[int, ProductVariant]:
    """Every named variant, locked, in a deterministic order.

    `order_by("pk")` is not cosmetic: two concurrent checkouts that locked their variants in the
    order their carts happen to list them could take the same two rows in opposite orders and
    deadlock. Ordering the lock acquisition is what `ADR-0017` means by "so two concurrent orders
    cannot deadlock".

    Read through `.values()`-style dicts elsewhere and instances here; the lock needs the row objects.
    """
    rows = (
        ProductVariant.objects.select_related("product")
        .select_for_update(of=("self",))
        .filter(pk__in=sorted(set(variant_ids)))
        .order_by("pk")
    )
    return {row.pk: row for row in rows}


@transaction.atomic
def create_order(
    *,
    user: User,
    shipping_address: ShippingAddress,
    shipping_method: ShippingMethod,
    email: str,
    idempotency_key: str | None = None,
) -> tuple[Order, bool]:
    """Turn the caller's cart into an order, and return `(order, created)`.

    `Idempotency-Key` (`NFR-4`): a key already known answers with the order it produced and touches
    nothing, so `created` is `False`. The check is a read, so a simultaneous double submit could both
    pass it; the unique index on `idempotency_key` is the arbiter, and the endpoint catches the
    `IntegrityError` and re-reads. A caller who sends no key is simply not idempotent.

    The stock decrement is load-bearing (`ADR-0017`): each named variant is locked and checked, and
    only once every line fits is any of them written. Either all lines are taken and the order exists,
    or a lock, a check or a write fails and the transaction leaves the catalog as it was — there is no
    window where the stock is short and the order is not.

    Lines are read as dicts rather than instances so nothing here touches an implicit `*_id` attname,
    which is invisible to `basedpyright` (`ADR-0014`).
    """
    if idempotency_key is not None:
        replay = Order.objects.filter(idempotency_key=idempotency_key).first()
        if replay is not None:
            return replay, False

    cart = _locked_cart(user)
    lines = list(CartItem.objects.filter(cart=cart).order_by("id").values("variant_id", "quantity"))
    if not lines:
        raise EmptyCart("Your cart is empty.")

    variants = _locked_variants([line["variant_id"] for line in lines])
    for line in lines:
        variant = variants.get(line["variant_id"])
        if variant is None or not variant.is_active or not variant.product.is_active:
            raise NotForSale("An item in your cart is no longer available.")
        if variant.stock_qty < line["quantity"]:
            raise InsufficientStock(
                f"Only {variant.stock_qty} of {variant.product.name} ({variant.name}) in stock; "
                f"{line['quantity']} requested."
            )

    subtotal_cents = 0
    currency = "USD"
    for line in lines:
        variant = variants[line["variant_id"]]
        variant.stock_qty -= line["quantity"]
        variant.save(update_fields=["stock_qty", "updated_at"])
        subtotal_cents += variant.price_cents * line["quantity"]
        currency = variant.product.currency

    order = Order.objects.create(
        user=user,
        email=email,
        subtotal_cents=subtotal_cents,
        shipping_cents=shipping_method.price_cents,
        total_cents=subtotal_cents + shipping_method.price_cents,
        currency=currency,
        shipping_recipient=shipping_address.recipient,
        shipping_line1=shipping_address.line1,
        shipping_line2=shipping_address.line2,
        shipping_city=shipping_address.city,
        shipping_region=shipping_address.region,
        shipping_postal_code=shipping_address.postal_code,
        shipping_country=shipping_address.country,
        idempotency_key=idempotency_key,
    )

    OrderItem.objects.bulk_create(
        [
            OrderItem(
                order=order,
                variant=variants[line["variant_id"]],
                product_name=variants[line["variant_id"]].product.name,
                variant_name=variants[line["variant_id"]].name,
                unit_price_cents=variants[line["variant_id"]].price_cents,
                quantity=line["quantity"],
                line_total_cents=variants[line["variant_id"]].price_cents * line["quantity"],
            )
            for line in lines
        ]
    )

    # The order's own first event: from nothing to `pending`. No actor — checkout did this, not a
    # person — which is what the empty `from_status` and the note record.
    OrderEvent.objects.create(order=order, to_status=OrderStatus.PENDING, note="Order placed.")

    start_payment(order)

    cart.status = CartStatus.CONVERTED
    cart.save(update_fields=["status", "updated_at"])

    return order, True


@transaction.atomic
def cancel_order(order: Order, *, actor: User | None = None, note: str = "") -> Order:
    """Cancel an order and return its lines to stock.

    Creation reserved the stock (`ADR-0017`), so cancelling has to release it or a decline would
    quietly shrink the shop's sellable quantity forever. `M5.5`'s operator console cancels through
    here rather than assigning the status itself, which is what keeps this the one place that knows a
    cancellation is also a stock event.
    """
    locked = Order.objects.select_for_update().get(pk=order.pk)
    cancelled = transition_order(locked, OrderStatus.CANCELLED, actor=actor, note=note)
    for item in OrderItem.objects.filter(order=cancelled).select_related("variant").order_by("id"):
        variant = item.variant
        if variant is not None:
            ProductVariant.objects.filter(pk=variant.pk).update(
                stock_qty=F("stock_qty") + item.quantity, updated_at=timezone.now()
            )
    return cancelled
