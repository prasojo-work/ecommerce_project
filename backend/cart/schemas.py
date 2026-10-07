from __future__ import annotations

from ninja import Schema


class CartItemIn(Schema):
    variant_id: int
    quantity: int = 1


class CartItemPatch(Schema):
    quantity: int


class CartItemOut(Schema):
    id: int
    variant_id: int
    product_title: str
    product_slug: str
    variant_name: str
    image: str | None
    unit_price: int
    quantity: int
    line_total: int


class CartOut(Schema):
    items: list[CartItemOut]
    subtotal: int
    currency: str
