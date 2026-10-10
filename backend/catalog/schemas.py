"""Schemas for the catalog read API.

Naming follows `API.md` section 1: `snake_case` fields and plural resource nouns. Money is the
`{amount_cents, currency}` object from the same section, never a bare number, so a client can
format it without a second lookup.

The list and detail payloads differ deliberately: a card carries one image and no variants, while
the detail payload carries the gallery and the variants. Nesting variants in a listing would
multiply the payload for data the grid never shows.
"""

from enum import StrEnum

from ninja import Schema
from pydantic import Field

DEFAULT_PAGE_SIZE = 24
MAX_PAGE_SIZE = 100


class SortOption(StrEnum):
    """`sort` values from `API.md` section 4. The `-` prefix means descending.

    Members are upper case because `Enum` already defines `name` and `value`; a member named
    `name` would shadow one of them.
    """

    NAME = "name"
    PRICE = "price"
    PRICE_DESC = "-price"
    NEWEST = "newest"


class MoneySchema(Schema):
    amount_cents: int
    currency: str


class CategoryRefSchema(Schema):
    """Just enough category to label a card or a breadcrumb."""

    slug: str
    name: str


class CategorySchema(Schema):
    id: int
    slug: str
    name: str
    description: str
    parent_slug: str | None = None
    children: list["CategorySchema"] = Field(default_factory=list)


class CategoryTreeSchema(Schema):
    items: list[CategorySchema]


class ImageSchema(Schema):
    path: str
    alt: str
    position: int


class ProductCardSchema(Schema):
    """A listing row. No variants: the grid does not render them."""

    id: int
    slug: str
    name: str
    category: CategoryRefSchema
    price: MoneySchema
    image: ImageSchema | None = None
    in_stock: bool
    material: str
    color: str


class ProductPageSchema(Schema):
    items: list[ProductCardSchema]
    page: int
    page_size: int
    total: int


class CategoryDetailSchema(Schema):
    category: CategorySchema
    items: list[ProductCardSchema]
    page: int
    page_size: int
    total: int


class VariantSchema(Schema):
    id: int
    sku: str
    name: str
    price: MoneySchema
    stock_qty: int
    in_stock: bool


class AvailabilitySchema(Schema):
    in_stock: bool
    in_stock_variants: int


class ProductDetailSchema(Schema):
    id: int
    slug: str
    name: str
    description: str
    category: CategoryRefSchema
    price: MoneySchema
    material: str
    color: str
    width_cm: float | None = None
    height_cm: float | None = None
    depth_cm: float | None = None
    images: list[ImageSchema] = Field(default_factory=list)
    variants: list[VariantSchema] = Field(default_factory=list)
    availability: AvailabilitySchema


class PageFilters(Schema):
    """Paging parameters, shared by the paginated routes."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)


class ProductFilters(PageFilters):
    """Query parameters for `GET /products` (`API.md` section 4).

    `min_price` and `max_price` are integer cents, matching the payload convention in `API.md`
    section 1, so a client never converts to a decimal in order to filter.
    """

    category: str | None = None
    q: str | None = None
    min_price: int | None = Field(default=None, ge=0, description="Minimum price, in cents.")
    max_price: int | None = Field(default=None, ge=0, description="Maximum price, in cents.")
    sort: SortOption = SortOption.NAME
