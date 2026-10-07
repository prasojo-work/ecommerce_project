import hashlib
from typing import Any

from django.db.models import QuerySet
from ninja import Query, Router
from ninja.errors import HttpError

from catalog.cache import cached
from catalog.models import Category, Product
from catalog.schemas import (
    CategoryOut,
    PaginatedProducts,
    ProductDetail,
    ProductFilters,
    ProductImageOut,
    ProductListItem,
    ProductVariantOut,
)

router = Router(tags=["catalog"])

_SORT_MAP = {
    "newest": "-created_at",
    "price": "base_price",
    "-price": "-base_price",
    "title": "title",
}


def _active_products() -> QuerySet:
    return (
        Product.objects.filter(status=Product.Status.ACTIVE)
        .select_related("category")
        .prefetch_related("variants", "images")
    )


def _category_out(category: Any) -> CategoryOut:
    return CategoryOut(id=category.id, name=category.name, slug=category.slug)


def _price_from(product: Any) -> int:
    prices = [v.effective_price for v in product.variants.all() if v.is_active]
    return min(prices) if prices else product.base_price


def _primary_image(product: Any) -> str | None:
    image = next(iter(product.images.all()), None)
    return image.url if image else None


def _to_list_item(product: Any) -> ProductListItem:
    return ProductListItem(
        id=product.id,
        title=product.title,
        slug=product.slug,
        category=_category_out(product.category),
        brand=product.brand,
        price_from=_price_from(product),
        currency=product.currency,
        image=_primary_image(product),
    )


def _to_detail(product: Any) -> ProductDetail:
    return ProductDetail(
        id=product.id,
        title=product.title,
        slug=product.slug,
        description=product.description,
        brand=product.brand,
        category=_category_out(product.category),
        base_price=product.base_price,
        currency=product.currency,
        images=[ProductImageOut(url=i.url, alt=i.alt) for i in product.images.all()],
        variants=[
            ProductVariantOut(
                id=v.id,
                sku=v.sku,
                name=v.name,
                attributes=v.attributes,
                price=v.effective_price,
                stock_qty=v.stock_qty,
                is_active=v.is_active,
            )
            for v in product.variants.all()
        ],
    )


def _build_categories() -> list[CategoryOut]:
    categories = Category.objects.filter(is_active=True).order_by("position", "name")
    return [_category_out(c) for c in categories]


def _products_cache_key(filters: ProductFilters) -> str:
    """One key per distinct listing query.

    Hashed rather than concatenated: `q` is caller-supplied and unbounded, and
    some cache backends reject long or whitespace-bearing keys.
    """
    raw = "|".join(
        [
            filters.category or "",
            filters.q or "",
            filters.sort,
            str(filters.page),
            str(filters.page_size),
        ]
    )
    return f"products:{hashlib.sha256(raw.encode()).hexdigest()[:32]}"


def _build_products(filters: ProductFilters) -> PaginatedProducts:
    queryset = _active_products()
    if filters.category:
        queryset = queryset.filter(category__slug=filters.category)
    if filters.q:
        queryset = queryset.filter(title__icontains=filters.q)
    queryset = queryset.order_by(_SORT_MAP[filters.sort])

    total = queryset.count()
    page = max(filters.page, 1)
    page_size = min(max(filters.page_size, 1), 100)
    offset = (page - 1) * page_size
    page_items = queryset[offset : offset + page_size]

    return PaginatedProducts(
        count=total,
        page=page,
        page_size=page_size,
        results=[_to_list_item(p) for p in page_items],
    )


def _build_detail(slug: str) -> ProductDetail | None:
    product = _active_products().filter(slug=slug).first()
    return None if product is None else _to_detail(product)


@router.get("/categories", response=list[CategoryOut])
def list_categories(request: Any) -> list[CategoryOut]:
    return cached("categories", _build_categories)


@router.get("/products", response=PaginatedProducts)
def list_products(request: Any, filters: Query[ProductFilters]) -> PaginatedProducts:
    return cached(_products_cache_key(filters), lambda: _build_products(filters))


@router.get("/products/{slug}", response=ProductDetail)
def product_detail(request: Any, slug: str) -> ProductDetail:
    product = cached(f"product:{slug}", lambda: _build_detail(slug))
    if product is None:
        raise HttpError(404, "Product not found")
    return product
