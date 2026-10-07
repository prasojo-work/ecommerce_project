from typing import Any, Literal

from ninja import Schema


class CategoryOut(Schema):
    id: int
    name: str
    slug: str


class ProductImageOut(Schema):
    url: str
    alt: str


class ProductVariantOut(Schema):
    id: int
    sku: str
    name: str
    attributes: dict[str, Any]
    price: int
    stock_qty: int
    is_active: bool


class ProductListItem(Schema):
    id: int
    title: str
    slug: str
    category: CategoryOut
    brand: str
    price_from: int
    currency: str
    image: str | None


class ProductDetail(Schema):
    id: int
    title: str
    slug: str
    description: str
    brand: str
    category: CategoryOut
    base_price: int
    currency: str
    images: list[ProductImageOut]
    variants: list[ProductVariantOut]


class PaginatedProducts(Schema):
    count: int
    page: int
    page_size: int
    results: list[ProductListItem]


class ProductFilters(Schema):
    q: str | None = None
    category: str | None = None
    sort: Literal["newest", "price", "-price", "title"] = "newest"
    page: int = 1
    page_size: int = 12
