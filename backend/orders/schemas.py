from __future__ import annotations

from datetime import datetime

from ninja import Schema


class ShippingOptionOut(Schema):
    code: str
    name: str
    cost: int
    eta: str


class ShippingOptionsOut(Schema):
    subtotal: int
    currency: str
    free_shipping_threshold: int
    options: list[ShippingOptionOut]


class OrderItemOut(Schema):
    id: int
    variant_id: int | None
    product_title: str
    variant_name: str
    unit_price: int
    quantity: int
    line_total: int


class OrderOut(Schema):
    id: int
    number: str
    status: str
    subtotal: int
    shipping_cost: int
    total: int
    currency: str
    shipping_method: str
    shipping_method_name: str
    shipping_address: dict[str, str]
    items: list[OrderItemOut]
    created_at: datetime


class OrderSummaryOut(Schema):
    id: int
    number: str
    status: str
    total: int
    currency: str
    item_count: int
    created_at: datetime


class PaginatedOrders(Schema):
    count: int
    page: int
    page_size: int
    results: list[OrderSummaryOut]


class OrderFilters(Schema):
    page: int = 1
    page_size: int = 12


class OrderCreateIn(Schema):
    address_id: int
    shipping_method: str
    idempotency_key: str | None = None
