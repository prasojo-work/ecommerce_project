"""Request and response schemas for checkout (`API.md` section 6).

Money is the `{amount_cents, currency}` object from `API.md` section 1. The quote answers with
*each* option's total rather than its price alone, because `US-4.2` asks for the order total to
update as the method changes, and a client adding the numbers itself would be a second place the
subtotal could be computed a different way.
"""

from __future__ import annotations

from ninja import Schema
from pydantic import Field

from catalog.schemas import MoneySchema


class QuoteAddressSchema(Schema):
    """A delivery address supplied inline — `US-4.1`'s "enter a new one".

    The constraints mirror `accounts.schemas.AddressCreateSchema`, the address book this could be
    saved into, with the address-book-only fields (`label`, `is_default`) left out: a checkout does
    not name an address or make one the default.
    """

    recipient: str = Field(min_length=1, max_length=120)
    line1: str = Field(min_length=1, max_length=120)
    line2: str = Field(default="", max_length=120)
    city: str = Field(min_length=1, max_length=120)
    region: str = Field(default="", max_length=120)
    postal_code: str = Field(min_length=1, max_length=32)
    country: str = Field(min_length=2, max_length=2)
    phone: str = Field(default="", max_length=32)


class QuoteRequestSchema(Schema):
    """`POST /checkout/quote`.

    Exactly one of `address_id` (a saved address) or `address` (a new one) — `US-4.1`'s two ways to
    give an address. The "exactly one" rule is checked in the endpoint rather than here so the
    refusal is a plain `400` with a readable message, not a model-level pydantic error whose field
    location is the whole body.
    """

    address_id: int | None = None
    address: QuoteAddressSchema | None = None


class ShippingOptionSchema(Schema):
    """One shipping method and what choosing it does to the total."""

    code: str
    name: str
    description: str
    price: MoneySchema
    total: MoneySchema


class QuoteSchema(Schema):
    """The quote: the cart's subtotal, and every shipping option with the total it produces.

    The address is not echoed back. It is a precondition the request had to satisfy, not a result,
    and what a checkout needs to render from this is money.
    """

    subtotal: MoneySchema
    item_count: int
    shipping_options: list[ShippingOptionSchema]
