"""Request and response schemas for the cart (`API.md` section 5).

Money is the `{amount_cents, currency}` object from `API.md` section 1, as it is everywhere else in
this API, rather than a bare number that would leave a client to guess the currency.

Every mutation answers with the whole cart. `US-3.1` asks for the header cart count to update on an
add, and returning the lines, the count and the total from the one request is what makes that
possible without a second round trip.
"""

from __future__ import annotations

from ninja import Schema
from pydantic import Field

from catalog.schemas import MoneySchema


class AddItemSchema(Schema):
    """`POST /cart/items`. One is the default because that is what a product page sends."""

    variant_id: int
    quantity: int = Field(default=1, ge=1)


class SetQuantitySchema(Schema):
    """`PATCH /cart/items/{line_id}`.

    Zero is deliberately not a value: removing a line is `US-3.3`'s endpoint, and a stored zero
    would be a line every total has to remember to skip.
    """

    quantity: int = Field(ge=1)


class CartLineSchema(Schema):
    """One line, priced from the variant as it stands now (`DATA-MODEL.md` section 2).

    `available_stock` is here so the quantity stepper can cap itself at the same number the API
    enforces, instead of discovering the limit by being refused.
    """

    id: int
    variant_id: int
    product_name: str
    product_slug: str
    variant_name: str
    sku: str
    unit_price: MoneySchema
    line_total: MoneySchema
    quantity: int
    available_stock: int
    image_path: str | None = None


class CartSchema(Schema):
    """The whole cart.

    `id` is null when the account has no cart yet, which is a normal state rather than an error:
    reading a cart never creates one, so an empty payload is what a shopper who has added nothing
    gets.
    """

    id: int | None
    items: list[CartLineSchema] = Field(default_factory=list)
    item_count: int
    subtotal: MoneySchema
