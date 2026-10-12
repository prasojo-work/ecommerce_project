"""Checkout (`API.md` section 6, `SCOPE.md` `US-4.1`-`US-4.2`).

`M4.2` lands the quote and `M4.3` the order: the quote prices the caller's cart, and placing an order
spends those same figures inside one transaction that decrements stock and starts a payment.

**The caller's cart, like every cart read.** The cart is authenticated (`ADR-0017`), and a quote
needs a cart, so this route carries the same bearer requirement. `API.md` section 6 marked the quote
"optional" before `ADR-0017`; the contract now says `access`, because a route that always reads a
cart can never be served without one.

**The quote validates the address, not the stock.** `US-4.1` asks for server-side address validation,
which is what a missing or malformed field is refused for here. Stock is deliberately *not* checked:
`ADR-0017` puts the binding, race-safe check in the order-creation transaction (`M4.3`), and a second
check here would be a weaker one in a different place, answering `409` for a cart that order creation
might well accept.
"""

from __future__ import annotations

from django.db import IntegrityError
from ninja import HeaderEx, P, Router, Status
from ninja.errors import HttpError

from accounts.auth import AuthenticatedRequest, auth
from accounts.models import Address, User
from accounts.throttling import AuthenticatedRateThrottle
from cart.models import Cart, CartItem, CartStatus
from catalog.schemas import MoneySchema
from orders.models import Order, OrderItem
from orders.schemas import (
    OrderCreateSchema,
    OrderItemSchema,
    OrderSchema,
    OrderShippingAddressSchema,
    QuoteRequestSchema,
    QuoteSchema,
    ShippingOptionSchema,
)
from orders.services import (
    EmptyCart,
    InsufficientStock,
    NotForSale,
    ShippingAddress,
    create_order,
)
from orders.shipping import SHIPPING_METHODS, get_method

router = Router(tags=["orders"])

# v1 is single-currency (`DATA-MODEL.md` section 5), so a currency has to come from somewhere even
# when the caller's lines disagree — which, being single-currency, they cannot.
DEFAULT_CURRENCY = "USD"

NEED_AN_ADDRESS = "Provide a delivery address: either `address_id` or `address`."
ONE_ADDRESS = "Provide either `address_id` or `address`, not both."
NO_SUCH_ADDRESS = "No such address."
EMPTY_CART = "Your cart is empty, so there is nothing to quote."
NOTHING_TO_ORDER = "Your cart is empty."


def money(amount_cents: int, currency: str) -> MoneySchema:
    return MoneySchema(amount_cents=amount_cents, currency=currency)


def _cart_totals(user: User) -> tuple[int, int, str]:
    """The caller's active cart as `(subtotal_cents, item_count, currency)`, or a `409` if empty.

    Prices are read live from the variant, as a cart stores none of its own (`DATA-MODEL.md`
    section 2) — the same numbers the cart page shows, which is the point of quoting rather than
    re-deriving them somewhere else. A cart that does not exist and a cart with no lines are the
    same answer: there is nothing to quote.
    """
    cart = Cart.objects.filter(user=user, status=CartStatus.ACTIVE).first()
    if cart is None:
        raise HttpError(409, EMPTY_CART)

    rows = list(
        CartItem.objects.filter(cart=cart).values_list(
            "quantity", "variant__price_cents", "variant__product__currency"
        )
    )
    if not rows:
        raise HttpError(409, EMPTY_CART)

    return (
        sum(price_cents * quantity for quantity, price_cents, _ in rows),
        sum(quantity for quantity, _, _ in rows),
        rows[0][2],
    )


def _shipping_address(
    user: User, payload: QuoteRequestSchema | OrderCreateSchema
) -> ShippingAddress:
    """The delivery address the request names, as the snapshot an order stores (`US-4.1`).

    Exactly one of a saved `address_id` or an inline `address`. A saved one is resolved through the
    caller's own scope, so somebody else's is a `404` and not a `403` that would confirm the id
    exists — the shape `accounts/addresses_api.py` explains; an inline one needs no lookup, since the
    schema has already checked its fields against the address book's constraints.

    The quote calls this and drops the answer — it returns money, and echoing an address back would
    invite a client to read it from here instead of from where the shopper set it. Order creation
    keeps it, because an order *is* where it went.
    """
    address_id = payload.address_id
    inline = payload.address

    if address_id is not None and inline is not None:
        raise HttpError(400, ONE_ADDRESS)
    if inline is not None:
        return ShippingAddress(
            recipient=inline.recipient,
            line1=inline.line1,
            line2=inline.line2,
            city=inline.city,
            region=inline.region,
            postal_code=inline.postal_code,
            country=inline.country,
        )
    if address_id is None:
        raise HttpError(400, NEED_AN_ADDRESS)
    saved = Address.objects.filter(user=user, pk=address_id).first()
    if saved is None:
        raise HttpError(404, NO_SUCH_ADDRESS)
    return ShippingAddress.from_address(saved)


@router.post(
    "/checkout/quote",
    response=QuoteSchema,
    auth=auth,
    throttle=[AuthenticatedRateThrottle()],
    summary="Quote a checkout",
)
def quote_checkout(request: AuthenticatedRequest, payload: QuoteRequestSchema) -> QuoteSchema:
    """`US-4.1` and `US-4.2`: the subtotal, and every shipping option with its total.

    `total_cents = subtotal_cents + shipping_cents` is the same arithmetic the order's own check
    constraint holds, so a total shown here is a total `M4.3` can carry onto the receipt.
    """
    user = request.auth
    _shipping_address(user, payload)
    subtotal_cents, item_count, currency = _cart_totals(user)

    return QuoteSchema(
        subtotal=money(subtotal_cents, currency),
        item_count=item_count,
        shipping_options=[
            ShippingOptionSchema(
                code=method.code,
                name=method.name,
                description=method.description,
                price=money(method.price_cents, currency),
                total=money(subtotal_cents + method.price_cents, currency),
            )
            for method in SHIPPING_METHODS
        ],
    )


def _order_schema(order: Order) -> OrderSchema:
    """The order as the confirmation shows it: totals, where it went, and the lines it holds."""
    return OrderSchema(
        number=order.number,
        status=order.status,
        email=order.email,
        placed_at=order.created_at,
        subtotal=money(order.subtotal_cents, order.currency),
        shipping=money(order.shipping_cents, order.currency),
        total=money(order.total_cents, order.currency),
        shipping_address=OrderShippingAddressSchema(
            recipient=order.shipping_recipient,
            line1=order.shipping_line1,
            line2=order.shipping_line2,
            city=order.shipping_city,
            region=order.shipping_region,
            postal_code=order.shipping_postal_code,
            country=order.shipping_country,
        ),
        items=[
            OrderItemSchema(
                product_name=item.product_name,
                variant_name=item.variant_name,
                unit_price=money(item.unit_price_cents, order.currency),
                quantity=item.quantity,
                line_total=money(item.line_total_cents, order.currency),
            )
            for item in OrderItem.objects.filter(order=order).order_by("id")
        ],
    )


@router.post(
    "/orders",
    response={200: OrderSchema, 201: OrderSchema},
    auth=auth,
    throttle=[AuthenticatedRateThrottle()],
    summary="Place an order",
)
def place_order(
    request: AuthenticatedRequest,
    payload: OrderCreateSchema,
    idempotency_key: HeaderEx[str | None, P(alias="Idempotency-Key")] = None,
) -> Status[OrderSchema]:
    """`US-4.4`: turn the cart into an order, reserving its stock and starting a payment.

    `201` when this request made the order, `200` when an `Idempotency-Key` it had already seen
    answered from the row that key produced — the same body either way, so a client retrying a submit
    whose answer it never saw can take the first response as final.

    `409` for the states of the *cart* that checkout cannot sell: empty, holding something no longer
    for sale, or holding more of a variant than is left. Each reads as the cart's problem rather than
    the request's, which is why none is a `400`.
    """
    user = request.auth
    shipping_address = _shipping_address(user, payload)

    method = get_method(payload.shipping_method)
    if method is None:
        raise HttpError(400, f"`{payload.shipping_method}` is not a shipping method.")

    try:
        order, created = create_order(
            user=user,
            shipping_address=shipping_address,
            shipping_method=method,
            email=payload.email or user.email,
            idempotency_key=idempotency_key,
        )
    except EmptyCart as exc:
        raise HttpError(409, NOTHING_TO_ORDER) from exc
    except NotForSale as exc:
        raise HttpError(409, str(exc)) from exc
    except InsufficientStock as exc:
        raise HttpError(409, str(exc)) from exc
    except IntegrityError:
        if idempotency_key is None:
            raise
        # The unique index arbitrated a simultaneous double submit: the other request made the order,
        # so this one answers with it rather than a second.
        order = Order.objects.get(idempotency_key=idempotency_key)
        created = False

    return Status(201 if created else 200, _order_schema(order))
