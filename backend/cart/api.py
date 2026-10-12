"""The cart (`API.md` section 5, `SCOPE.md` `US-3.1`-`US-3.5`).

The cart requires authentication (`ADR-0017`): every endpoint here carries the same bearer
requirement as the address book, and there is no guest cart, no cookie and no merge.

**A line is reached through the caller's own cart.** The owner is part of the query rather than a
check after it — the shape `accounts/addresses_api.py` explains at length — so another account's
line is a `404` and not a `403` that would confirm the id exists.

**Reading never writes.** `GET /cart` answers an account with no cart with an empty payload and
creates no row, so a cart exists only once something has been added to one.

**The stock check here is an affordance, not a guarantee.** It refuses a quantity the variant cannot
cover, which is what `US-3.2` asks for, but stock moves between the cart and checkout: the binding
check happens once, at order creation, in the transaction that decrements conditionally. `ADR-0017`
records that requirement for `M4`.

Rows are read with `values()` and joined field names rather than through instance attributes, for the
reason `ADR-0014` gives: implicit `id` and `*_id` attnames are visible to `basedpyright` only via
django-stubs' mypy plugin, which this project does not rely on.
"""

from __future__ import annotations

from typing import Any

from django.db import transaction
from ninja import Router
from ninja.errors import HttpError

from accounts.auth import AuthenticatedRequest, auth
from accounts.models import User
from accounts.throttling import AuthenticatedRateThrottle
from cart.models import Cart, CartItem, CartStatus
from cart.schemas import AddItemSchema, CartLineSchema, CartSchema, SetQuantitySchema
from catalog.models import ProductImage, ProductVariant
from catalog.schemas import MoneySchema

router = Router(tags=["cart"])

# v1 is single-currency (`DATA-MODEL.md` section 5), so a cart with no lines still has one to report.
DEFAULT_CURRENCY = "USD"

NO_SUCH_LINE = "No such cart line."
NO_SUCH_VARIANT = "No such variant."
NOT_FOR_SALE = "That variant is no longer available."

VARIANT_FIELDS = (
    "id",
    "sku",
    "name",
    "price_cents",
    "stock_qty",
    "product__name",
    "product__currency",
)

# Enough to render a line without a second query per line, plus the product's key so its primary
# image can be found in one more for the whole cart.
LINE_FIELDS = (
    "id",
    "quantity",
    "variant_id",
    "variant__sku",
    "variant__name",
    "variant__price_cents",
    "variant__stock_qty",
    "variant__product_id",
    "variant__product__name",
    "variant__product__slug",
    "variant__product__currency",
)


def money(amount_cents: int, currency: str) -> MoneySchema:
    return MoneySchema(amount_cents=amount_cents, currency=currency)


def _insufficient(variant: dict[str, Any], requested: int) -> HttpError:
    """`US-3.2` asks for a clear message, so this names both numbers rather than saying "invalid"."""
    return HttpError(
        409,
        f"Only {variant['stock_qty']} of {variant['product__name']} ({variant['name']}) in stock; "
        f"{requested} requested.",
    )


def _variant_row(variant_id: int) -> dict[str, Any]:
    """A variant that can be bought, as data.

    A variant that exists but is withdrawn — or whose product is — answers `409` rather than `404`:
    it is not a mistyped id, it is a product page that has gone stale, and a client should be able to
    tell those apart.
    """
    row = (
        ProductVariant.objects.filter(pk=variant_id, is_active=True, product__is_active=True)
        .values(*VARIANT_FIELDS)
        .first()
    )
    if row is not None:
        return dict(row)
    if ProductVariant.objects.filter(pk=variant_id).exists():
        raise HttpError(409, NOT_FOR_SALE)
    raise HttpError(404, NO_SUCH_VARIANT)


def _active_cart(user: User) -> Cart | None:
    return Cart.objects.filter(user=user, status=CartStatus.ACTIVE).first()


def _lock(cart: Cart) -> Cart:
    """The same row, re-read for update. SQLite ignores the lock, which is why the concurrency test
    is marked for PostgreSQL rather than pretending the two behave alike."""
    return Cart.objects.select_for_update().get(pk=cart.pk)


def _started_cart(user: User) -> Cart:
    """The caller's active cart, created if they have none, locked for this transaction.

    `get_or_create` rather than a read followed by a create: two concurrent first-adds would
    otherwise both find nothing and both insert, and the partial unique index would answer one of
    them with an `IntegrityError`. `get_or_create` is the one place Django already resolves that
    race. Locking afterwards is what serializes the *lines*, so two adds of the same variant cannot
    read the same quantity and write over each other.
    """
    cart, _ = Cart.objects.get_or_create(user=user, status=CartStatus.ACTIVE)
    return _lock(cart)


def _cart_to_change(user: User) -> Cart:
    """The caller's active cart, locked — or a `404`: an account with no cart has no line to change,
    and changing a line must not be what creates one."""
    cart = _active_cart(user)
    if cart is None:
        raise HttpError(404, NO_SUCH_LINE)
    return _lock(cart)


def _own_line(cart: Cart, line_id: int) -> CartItem:
    """The caller's line with this id, with its variant loaded, or a `404`.

    `404` rather than `403` deliberately: `403` would confirm the id exists, which is exactly what
    an attempt to enumerate other people's carts is trying to learn.
    """
    line = (
        CartItem.objects.select_related("variant", "variant__product")
        .filter(cart=cart, pk=line_id)
        .first()
    )
    if line is None:
        raise HttpError(404, NO_SUCH_LINE)
    return line


def _cart_payload(cart: Cart | None) -> CartSchema:
    """The whole cart in two queries regardless of how many lines it holds."""
    if cart is None:
        return CartSchema(id=None, items=[], item_count=0, subtotal=money(0, DEFAULT_CURRENCY))

    rows = list(CartItem.objects.filter(cart=cart).values(*LINE_FIELDS).order_by("id"))

    # One query for every line's primary image, keyed by product, rather than one per line. The
    # first image by position is the one a card shows, as in `catalog/api.py`.
    primary_image: dict[Any, str] = {}
    images = ProductImage.objects.filter(
        product_id__in=[row["variant__product_id"] for row in rows]
    ).order_by("position", "id")
    for product_id, path in images.values_list("product_id", "path"):
        primary_image.setdefault(product_id, path)

    items = [
        CartLineSchema(
            id=row["id"],
            variant_id=row["variant_id"],
            product_name=row["variant__product__name"],
            product_slug=row["variant__product__slug"],
            variant_name=row["variant__name"],
            sku=row["variant__sku"],
            unit_price=money(row["variant__price_cents"], row["variant__product__currency"]),
            line_total=money(
                row["variant__price_cents"] * row["quantity"],
                row["variant__product__currency"],
            ),
            quantity=row["quantity"],
            available_stock=row["variant__stock_qty"],
            image_path=primary_image.get(row["variant__product_id"]),
        )
        for row in rows
    ]

    return CartSchema(
        id=cart.pk,
        items=items,
        item_count=sum(item.quantity for item in items),
        subtotal=money(
            sum(item.line_total.amount_cents for item in items),
            items[0].unit_price.currency if items else DEFAULT_CURRENCY,
        ),
    )


@router.get(
    "/cart",
    response=CartSchema,
    auth=auth,
    throttle=[AuthenticatedRateThrottle()],
    summary="Current cart",
)
def get_cart(request: AuthenticatedRequest) -> CartSchema:
    """`US-3.4`. An account with no cart gets an empty payload, and asking creates nothing."""
    return _cart_payload(_active_cart(request.auth))


@router.post(
    "/cart/items",
    response=CartSchema,
    auth=auth,
    throttle=[AuthenticatedRateThrottle()],
    summary="Add an item",
)
def add_item(request: AuthenticatedRequest, payload: AddItemSchema) -> CartSchema:
    """`US-3.1`.

    Adding a variant that is already on the cart adds to its quantity rather than starting a second
    line, which is what the uniqueness in `DATA-MODEL.md` section 2 means and what the cap below
    then applies to the total.
    """
    user = request.auth
    variant = _variant_row(payload.variant_id)

    with transaction.atomic():
        cart = _started_cart(user)
        line = CartItem.objects.filter(cart=cart, variant_id=variant["id"]).first()
        wanted = payload.quantity + (line.quantity if line is not None else 0)
        if wanted > variant["stock_qty"]:
            raise _insufficient(variant, wanted)

        if line is None:
            CartItem.objects.create(cart=cart, variant_id=variant["id"], quantity=payload.quantity)
        else:
            line.quantity = wanted
            line.save(update_fields=["quantity", "updated_at"])

    return _cart_payload(cart)


@router.patch(
    "/cart/items/{line_id}",
    response=CartSchema,
    auth=auth,
    throttle=[AuthenticatedRateThrottle()],
    summary="Set a line's quantity",
)
def set_quantity(
    request: AuthenticatedRequest, line_id: int, payload: SetQuantitySchema
) -> CartSchema:
    """`US-3.2`. Above stock is refused rather than quietly capped: the client asked for a number and
    is told it cannot have it, which is the `409` in `API.md` section 5."""
    user = request.auth

    with transaction.atomic():
        cart = _cart_to_change(user)
        line = _own_line(cart, line_id)

        variant = _variant_row(line.variant.pk)
        if payload.quantity > variant["stock_qty"]:
            raise _insufficient(variant, payload.quantity)

        line.quantity = payload.quantity
        line.save(update_fields=["quantity", "updated_at"])

    return _cart_payload(cart)


@router.delete(
    "/cart/items/{line_id}",
    response=CartSchema,
    auth=auth,
    throttle=[AuthenticatedRateThrottle()],
    summary="Remove a line",
)
def remove_item(request: AuthenticatedRequest, line_id: int) -> CartSchema:
    """`US-3.3`. The cart survives with its remaining lines, and the response is the cart so the
    client can re-render the totals it just changed."""
    user = request.auth

    with transaction.atomic():
        cart = _cart_to_change(user)
        line = _own_line(cart, line_id)
        line.delete()

    return _cart_payload(cart)
