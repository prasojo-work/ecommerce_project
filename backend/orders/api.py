"""Checkout (`API.md` section 6, `SCOPE.md` `US-4.1`-`US-4.2`).

`M4.2` lands the quote: given the caller's cart and an address, it answers the subtotal and every
shipping option with the total it produces. Order creation, and the stock decrement that binds, is
`M4.3`, which spends these same figures.

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

from ninja import Router
from ninja.errors import HttpError

from accounts.auth import AuthenticatedRequest, auth
from accounts.models import Address, User
from accounts.throttling import AuthenticatedRateThrottle
from cart.models import Cart, CartItem, CartStatus
from catalog.schemas import MoneySchema
from orders.schemas import QuoteRequestSchema, QuoteSchema, ShippingOptionSchema
from orders.shipping import SHIPPING_METHODS

router = Router(tags=["orders"])

# v1 is single-currency (`DATA-MODEL.md` section 5), so a currency has to come from somewhere even
# when the caller's lines disagree — which, being single-currency, they cannot.
DEFAULT_CURRENCY = "USD"

NEED_AN_ADDRESS = "Provide a delivery address: either `address_id` or `address`."
ONE_ADDRESS = "Provide either `address_id` or `address`, not both."
NO_SUCH_ADDRESS = "No such address."
EMPTY_CART = "Your cart is empty, so there is nothing to quote."


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


def _validate_address(user: User, payload: QuoteRequestSchema) -> None:
    """Refuse a request that did not bring exactly one usable address (`US-4.1`).

    A saved address is resolved through the caller's own scope, so somebody else's is a `404` and
    not a `403` that would confirm the id exists — the shape `accounts/addresses_api.py` explains.
    An inline address needs no lookup: the schema has already checked its fields.

    The address is validated and then dropped. It is a precondition for a quote, not part of the
    answer, and returning it would invite a client to treat a quote response as an address record.
    """
    address_id = payload.address_id
    inline = payload.address

    if address_id is None and inline is None:
        raise HttpError(400, NEED_AN_ADDRESS)
    if address_id is not None and inline is not None:
        raise HttpError(400, ONE_ADDRESS)
    if address_id is not None and not Address.objects.filter(user=user, pk=address_id).exists():
        raise HttpError(404, NO_SUCH_ADDRESS)


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
    _validate_address(user, payload)
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
