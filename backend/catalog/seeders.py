"""Catalog seeding step.

Every row is derived from the curated mapping in `catalog/seed_data.py`, the vendored
`backend/seed_data/manifest.csv`, or a generator seeded with `SEED`, so two runs produce identical
data and `manage.py seed` is safe to re-run without `--reset`.

Licensing (`ADR-0012`): no `BY-ND` image ships. That licence forbids derivatives, and a product
grid cannot promise never to crop or resize what it displays, so the three `BY-ND` keywords in the
source set are excluded with everything else that does not fit. Every vendored image is `BY`,
`BY-SA`, `PDM`, or `CC0` — the licences `ADR-0012` prefers — so all of them are safe to crop and
resize.

`clear()` removes the **whole** catalog rather than only seeded rows, because nothing yet
distinguishes a seeded row from an operator-created one. That becomes a real question at `M5`,
when the operator console can add products, and `--reset` would otherwise delete their work.
"""

import csv
import random
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.utils.text import slugify

from catalog import seed_data
from catalog.models import Category, ImageCredit, Product, ProductImage, ProductVariant
from core.seeding import SeedStep

# Changing this changes the whole catalog. It is the project start date, so it is easy to recall.
SEED = 20261010


def _manifest_rows() -> dict[str, dict[str, str]]:
    """The vendored manifest, keyed by `keyword`."""
    path = Path(settings.BASE_DIR) / seed_data.MANIFEST_PATH
    with path.open(encoding="utf-8") as handle:
        rows = {row["keyword"]: row for row in csv.DictReader(handle)}

    missing = sorted(
        keyword
        for keywords in seed_data.CATALOG.values()
        for keyword in keywords
        if keyword not in rows
    )
    if missing:
        raise ValueError(f"curated keywords missing from {path}: {missing}")
    return rows


def _dimensions(category: str, rng: random.Random) -> tuple[Decimal, Decimal, Decimal | None]:
    width_band, height_band, depth_band = seed_data.DIMENSION_BANDS_CM[category]
    width = Decimal(rng.randint(*width_band))
    height = Decimal(rng.randint(*height_band))
    depth = None if depth_band is None else Decimal(rng.randint(*depth_band))
    return width, height, depth


# Every tenth product in curated order is seeded out of stock, so the storefront always has a real
# out-of-stock case to render rather than one that only appears by chance.
OUT_OF_STOCK_EVERY = 10


def _variant_plan(
    category: str, rng: random.Random, *, out_of_stock: bool
) -> list[tuple[str, int, int]]:
    """(finish, price_cents, stock_qty) per variant. The first variant is the cheapest."""
    low, high = seed_data.PRICE_BANDS_CENTS[category]
    cheapest = round(rng.randint(low, high), -2)

    plan = []
    for index, finish in enumerate(rng.sample(seed_data.FINISHES, rng.randint(1, 3))):
        price = cheapest if index == 0 else round(cheapest * rng.uniform(1.05, 1.20), -2)
        plan.append((finish, price, 0 if out_of_stock else rng.randint(1, 40)))
    return plan


def _seed_image(product: Product, row: dict[str, str]) -> None:
    credit, _ = ImageCredit.objects.update_or_create(
        source_page_url=row["source_page"],
        defaults={
            "title": row["source_title"],
            "creator": row["creator"],
            "license": row["license"],
            "source": row["source"],
        },
    )
    ProductImage.objects.update_or_create(
        product=product,
        path=f"{seed_data.IMAGE_URL_PREFIX}/{row['filename']}",
        defaults={
            # The image depicts the product, so the product name is the meaningful alt text. The
            # source title is provenance and is deliberately not concatenated in: it is unbounded
            # and overflowed this column on PostgreSQL while SQLite accepted it silently.
            "alt": product.name,
            "position": 0,
            "credit": credit,
        },
    )


def _seed_product(
    category: Category,
    keyword: str,
    row: dict[str, str],
    rng: random.Random,
    *,
    out_of_stock: bool,
) -> None:
    series = rng.choice(seed_data.SERIES)
    material = rng.choice(seed_data.MATERIALS[category.name])
    name = f"{series} {material} {keyword.title()}"
    width, height, depth = _dimensions(category.name, rng)
    plan = _variant_plan(category.name, rng, out_of_stock=out_of_stock)

    product, _ = Product.objects.update_or_create(
        slug=slugify(name),
        defaults={
            "category": category,
            "name": name,
            "description": rng.choice(seed_data.DESCRIPTION_TEMPLATES).format(
                material=material, keyword=keyword
            ),
            "material": material,
            "color": rng.choice(seed_data.FINISHES),
            "width_cm": width,
            "height_cm": height,
            "depth_cm": depth,
            # `base_price_cents` is the display price and the variant price is authoritative, so
            # it is the cheapest variant rather than an independently generated number.
            "base_price_cents": min(price for _, price, _ in plan),
            "currency": "USD",
            "is_active": True,
            "attributes": {"keyword": keyword, "series": series},
        },
    )

    for finish, price, stock in plan:
        ProductVariant.objects.update_or_create(
            sku=f"LYS-{product.slug.upper()}-{finish.upper()}",
            defaults={
                "product": product,
                "name": finish,
                "price_cents": price,
                "stock_qty": stock,
                "is_active": True,
            },
        )

    _seed_image(product, row)


def seed() -> None:
    """Create the curated catalogue. Re-running updates rows in place."""
    # S311: an unguessable PRNG is the wrong tool here. Determinism is the requirement, which is
    # what makes `manage.py seed` reproducible and safe to re-run.
    rng = random.Random(SEED)  # noqa: S311
    rows = _manifest_rows()

    position = 0
    for category_position, (category_name, keywords) in enumerate(seed_data.CATALOG.items()):
        category, _ = Category.objects.update_or_create(
            slug=slugify(category_name),
            defaults={
                "name": category_name,
                "description": seed_data.CATEGORY_DESCRIPTIONS[category_name],
                "position": category_position,
                "parent": None,
            },
        )
        for keyword in keywords:
            _seed_product(
                category,
                keyword,
                rows[keyword],
                rng,
                out_of_stock=position % OUT_OF_STOCK_EVERY == 0,
            )
            position += 1


def clear() -> None:
    """Remove every catalog row. Products go first: `Product.category` is `PROTECT`."""
    Product.objects.all().delete()
    ImageCredit.objects.all().delete()
    Category.objects.all().delete()


STEPS = (SeedStep(name="catalog", run=seed, clear=clear),)
