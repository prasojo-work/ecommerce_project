"""Catalog read endpoints (`API.md` section 4). Public: no authentication.

Rows are read with `values()` rather than through model instances, and relations through managers
rather than reverse accessors (`ADR-0014`). The reason is shared: django-stubs generates an implicit
primary key (`id`) and foreign-key attnames (`parent_id`) through its **mypy plugin**, so
`basedpyright` cannot see them — the same limitation `ADR-0014` records for reverse relations. Field
names passed as strings work in every reader, and keep a page to a fixed number of queries.

Only `is_active` products and variants are served.
"""

from typing import Any

from django.db.models import Q, QuerySet
from django.http import HttpRequest
from ninja import Query, Router
from ninja.errors import HttpError

from catalog.models import Category, Product, ProductImage, ProductVariant
from catalog.schemas import (
    AvailabilitySchema,
    CategoryDetailSchema,
    CategoryRefSchema,
    CategorySchema,
    CategoryTreeSchema,
    ImageSchema,
    MoneySchema,
    PageFilters,
    ProductCardSchema,
    ProductDetailSchema,
    ProductFilters,
    ProductPageSchema,
    SortOption,
    VariantSchema,
)

router = Router(tags=["catalog"])

CARD_FIELDS = (
    "id",
    "slug",
    "name",
    "base_price_cents",
    "currency",
    "material",
    "color",
    "category__slug",
    "category__name",
)

DETAIL_FIELDS = (*CARD_FIELDS, "description", "width_cm", "height_cm", "depth_cm")

# Ordering always ends with a tiebreaker, so a page boundary cannot shift between two requests.
SORT_FIELDS: dict[SortOption, tuple[str, ...]] = {
    SortOption.NAME: ("name",),
    SortOption.PRICE: ("base_price_cents", "name"),
    SortOption.PRICE_DESC: ("-base_price_cents", "name"),
    SortOption.NEWEST: ("-created_at", "name"),
}


def money(amount_cents: int, currency: str) -> MoneySchema:
    return MoneySchema(amount_cents=amount_cents, currency=currency)


def _category_scope(slug: str) -> list[str]:
    """The slug plus every descendant, so filtering by a parent includes its children.

    Walks down with `parent__slug` lookups, which follow the forward foreign key, rather than
    through the reverse accessor (`ADR-0014`).
    """
    scope = [slug]
    frontier = [slug]
    while frontier:
        children = [
            child
            for child in Category.objects.filter(parent__slug__in=frontier).values_list(
                "slug", flat=True
            )
            if child not in scope
        ]
        if not children:
            break
        scope.extend(children)
        frontier = children
    return scope


def _product_queryset(filters: ProductFilters) -> QuerySet[Product]:
    queryset = Product.objects.filter(is_active=True)

    if filters.category:
        queryset = queryset.filter(category__slug__in=_category_scope(filters.category))
    if filters.q:
        # `US-1.3`: search names and keywords. The seed keeps the curated keyword in `attributes`,
        # so the lookup reaches it as a JSON key rather than a column.
        queryset = queryset.filter(
            Q(name__icontains=filters.q) | Q(attributes__keyword__icontains=filters.q)
        )
    if filters.min_price is not None:
        queryset = queryset.filter(base_price_cents__gte=filters.min_price)
    if filters.max_price is not None:
        queryset = queryset.filter(base_price_cents__lte=filters.max_price)

    return queryset.order_by(*SORT_FIELDS[filters.sort])


def _cards(rows: list[dict[str, Any]]) -> list[ProductCardSchema]:
    """Build listing rows with two extra queries in total, whatever the page size."""
    product_ids = [row["id"] for row in rows]
    if not product_ids:
        return []

    primary_image: dict[Any, ImageSchema] = {}
    images = ProductImage.objects.filter(product_id__in=product_ids).order_by("position", "id")
    for product_id, path, alt, position in images.values_list(
        "product_id", "path", "alt", "position"
    ):
        primary_image.setdefault(product_id, ImageSchema(path=path, alt=alt, position=position))

    in_stock: dict[Any, bool] = {}
    variants = ProductVariant.objects.filter(product_id__in=product_ids)
    for product_id, stock_qty in variants.values_list("product_id", "stock_qty"):
        in_stock[product_id] = in_stock.get(product_id, False) or stock_qty > 0

    return [
        ProductCardSchema(
            id=row["id"],
            slug=row["slug"],
            name=row["name"],
            category=CategoryRefSchema(slug=row["category__slug"], name=row["category__name"]),
            price=money(row["base_price_cents"], row["currency"]),
            image=primary_image.get(row["id"]),
            in_stock=in_stock.get(row["id"], False),
            material=row["material"],
            color=row["color"],
        )
        for row in rows
    ]


def _page(
    queryset: QuerySet[Product], page: int, page_size: int
) -> tuple[list[ProductCardSchema], int]:
    """One page of cards and the total before paging. Past the last page is empty, not an error."""
    total = queryset.count()
    offset = (page - 1) * page_size
    rows = list(queryset.values(*CARD_FIELDS)[offset : offset + page_size])
    return _cards(rows), total


def _category_tree() -> tuple[list[CategorySchema], dict[str, CategorySchema]]:
    """Every root schema, plus an index of every category by slug so a nested slug resolves too."""
    rows = list(
        Category.objects.values("id", "parent_id", "slug", "name", "description").order_by(
            "position", "name"
        )
    )
    slug_by_id = {row["id"]: row["slug"] for row in rows}
    children_by_parent: dict[Any, list[dict[str, Any]]] = {}
    for row in rows:
        children_by_parent.setdefault(row["parent_id"], []).append(row)

    def build(row: dict[str, Any]) -> CategorySchema:
        parent_id = row["parent_id"]
        return CategorySchema(
            id=row["id"],
            slug=row["slug"],
            name=row["name"],
            description=row["description"],
            parent_slug=None if parent_id is None else slug_by_id.get(parent_id),
            children=[build(child) for child in children_by_parent.get(row["id"], [])],
        )

    index = {row["slug"]: build(row) for row in rows}
    roots = [index[row["slug"]] for row in rows if row["parent_id"] is None]
    return roots, index


@router.get("/categories", response=CategoryTreeSchema, summary="Category tree")
def list_categories(request: HttpRequest) -> CategoryTreeSchema:
    """Every category, nested under its parent. Not paginated: a tree is small and shaped."""
    roots, _ = _category_tree()
    return CategoryTreeSchema(items=roots)


@router.get("/categories/{slug}", response=CategoryDetailSchema, summary="One category")
def category_detail(
    request: HttpRequest, slug: str, filters: Query[PageFilters]
) -> CategoryDetailSchema:
    """One category plus its products, paginated. An unknown slug is a `404`."""
    _, index = _category_tree()
    category = index.get(slug)
    if category is None:
        raise HttpError(404, f"No category with slug '{slug}'.")

    queryset = _product_queryset(
        ProductFilters(category=slug, page=filters.page, page_size=filters.page_size)
    )
    items, total = _page(queryset, filters.page, filters.page_size)

    return CategoryDetailSchema(
        category=category,
        items=items,
        page=filters.page,
        page_size=filters.page_size,
        total=total,
    )


@router.get("/products", response=ProductPageSchema, summary="List products")
def list_products(request: HttpRequest, filters: Query[ProductFilters]) -> ProductPageSchema:
    """Filtered, sorted, paginated products.

    An unknown `category` filters to nothing rather than erroring, so the storefront can render its
    explicit no-results state (`US-1.3`).
    """
    items, total = _page(_product_queryset(filters), filters.page, filters.page_size)
    return ProductPageSchema(
        items=items,
        page=filters.page,
        page_size=filters.page_size,
        total=total,
    )


@router.get("/products/{slug}", response=ProductDetailSchema, summary="One product")
def product_detail(request: HttpRequest, slug: str) -> ProductDetailSchema:
    """One product with its gallery and variants nested, for the detail page (`US-1.2`)."""
    row = Product.objects.filter(slug=slug, is_active=True).values(*DETAIL_FIELDS).first()
    if row is None:
        raise HttpError(404, f"No product with slug '{slug}'.")

    # Related rows are reached through `product__slug` so the product's key is never needed.
    variant_rows = list(
        ProductVariant.objects.filter(product__slug=slug, is_active=True).values(
            "id", "sku", "name", "price_cents", "stock_qty"
        )
    )
    image_rows = list(
        ProductImage.objects.filter(product__slug=slug)
        .order_by("position", "id")
        .values("path", "alt", "position")
    )

    currency = row["currency"]
    in_stock_variants = sum(1 for variant in variant_rows if variant["stock_qty"] > 0)

    return ProductDetailSchema(
        id=row["id"],
        slug=row["slug"],
        name=row["name"],
        description=row["description"],
        category=CategoryRefSchema(slug=row["category__slug"], name=row["category__name"]),
        price=money(row["base_price_cents"], currency),
        material=row["material"],
        color=row["color"],
        width_cm=row["width_cm"],
        height_cm=row["height_cm"],
        depth_cm=row["depth_cm"],
        images=[
            ImageSchema(path=image["path"], alt=image["alt"], position=image["position"])
            for image in image_rows
        ],
        variants=[
            VariantSchema(
                id=variant["id"],
                sku=variant["sku"],
                name=variant["name"],
                # A variant carries no currency of its own; it is priced in the product's.
                price=money(variant["price_cents"], currency),
                stock_qty=variant["stock_qty"],
                in_stock=variant["stock_qty"] > 0,
            )
            for variant in variant_rows
        ],
        availability=AvailabilitySchema(
            in_stock=in_stock_variants > 0, in_stock_variants=in_stock_variants
        ),
    )
