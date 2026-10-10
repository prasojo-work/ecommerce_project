import csv
from pathlib import Path

import pytest
from django.conf import settings

from catalog import seed_data
from catalog.models import Category, ImageCredit, Product, ProductImage, ProductVariant
from catalog.seeders import clear, seed

pytestmark = pytest.mark.django_db

CURATED_KEYWORDS = [kw for keywords in seed_data.CATALOG.values() for kw in keywords]

# `ADR-0012` allows BY-ND images only if they are never altered. `catalog/seeders.py` carries the
# no-crop constraint; this pins the exact set so a change to curation is a deliberate one.
BY_ND_IMAGES = {"/images/bed-frame.webp", "/images/bookshelf.webp", "/images/dining-table.webp"}

ALLOWED_LICENCES = {"BY-2.0", "BY-SA-2.0", "BY-SA-3.0", "BY-ND-2.0", "PDM-1.0", "CC0-1.0"}


def _manifest_rows() -> dict[str, dict[str, str]]:
    path = Path(settings.BASE_DIR) / seed_data.MANIFEST_PATH
    with path.open(encoding="utf-8") as handle:
        return {row["source_page"]: row for row in csv.DictReader(handle)}


def _counts() -> tuple[int, int, int, int, int]:
    return (
        Category.objects.count(),
        Product.objects.count(),
        ProductVariant.objects.count(),
        ProductImage.objects.count(),
        ImageCredit.objects.count(),
    )


def test_seed_creates_one_product_per_curated_keyword() -> None:
    seed()

    assert Category.objects.count() == len(seed_data.CATALOG)
    assert Product.objects.count() == len(CURATED_KEYWORDS) == 49


def test_every_product_has_exactly_one_credited_image() -> None:
    seed()

    assert ProductImage.objects.count() == Product.objects.count()
    assert not ProductImage.objects.filter(credit__isnull=True).exists()


def test_every_product_has_at_least_one_variant() -> None:
    seed()

    for product in Product.objects.all():
        assert ProductVariant.objects.filter(product=product).exists()


def test_images_reference_files_that_exist_in_the_repository() -> None:
    """The seed is useless if it points at images nobody vendored."""
    seed()
    public_root = Path(settings.BASE_DIR).parent / "frontend" / "public"

    missing = [
        image.path
        for image in ProductImage.objects.all()
        if not (public_root / image.path.lstrip("/")).is_file()
    ]

    assert missing == []


def test_credits_carry_the_manifest_values() -> None:
    seed()
    rows = _manifest_rows()

    for credit in ImageCredit.objects.all():
        row = rows[credit.source_page_url]
        assert credit.title == row["source_title"]
        assert credit.creator == row["creator"]
        assert credit.license == row["license"]
        assert credit.source == row["source"]


def test_shipped_licences_stay_within_the_allowed_set() -> None:
    seed()

    assert set(ImageCredit.objects.values_list("license", flat=True)) <= ALLOWED_LICENCES
    assert ImageCredit.objects.filter(license="BY-ND-2.0").count() == 3


def test_the_by_nd_images_that_ship_are_exactly_the_expected_three() -> None:
    seed()

    shipped = set(
        ProductImage.objects.filter(credit__license="BY-ND-2.0").values_list("path", flat=True)
    )

    assert shipped == BY_ND_IMAGES


def test_seed_is_idempotent() -> None:
    seed()
    before = _counts()

    seed()

    assert _counts() == before


def test_seed_is_deterministic_across_a_reset() -> None:
    seed()
    before = list(
        ProductVariant.objects.order_by("sku").values_list("sku", "price_cents", "stock_qty")
    )

    clear()
    seed()

    after = list(
        ProductVariant.objects.order_by("sku").values_list("sku", "price_cents", "stock_qty")
    )
    assert after == before


def test_a_second_run_without_reset_does_not_duplicate_variants() -> None:
    seed()
    skus = list(ProductVariant.objects.values_list("sku", flat=True))

    seed()

    assert len(skus) == len(set(skus)) == ProductVariant.objects.count()


def test_base_price_is_the_cheapest_variant_price() -> None:
    seed()

    for product in Product.objects.all():
        prices = list(
            ProductVariant.objects.filter(product=product).values_list("price_cents", flat=True)
        )
        assert product.base_price_cents == min(prices)


def test_prices_stay_inside_the_configured_band() -> None:
    seed()

    for product in Product.objects.prefetch_related("category"):
        low, high = seed_data.PRICE_BANDS_CENTS[product.category.name]
        assert low <= product.base_price_cents <= round(high * 1.20)


def test_out_of_stock_products_follow_the_documented_rule() -> None:
    """One product in every ten is out of stock, so the state is reachable by design."""
    seed()

    out_of_stock = Product.objects.filter(variants__stock_qty=0).distinct().count()

    assert out_of_stock == 5  # positions 0, 10, 20, 30, 40 of 49
    assert ProductVariant.objects.filter(stock_qty__gt=0).exists()


def test_products_carry_their_source_keyword_and_a_series() -> None:
    seed()

    keywords = sorted(product.attributes["keyword"] for product in Product.objects.all())

    assert keywords == sorted(CURATED_KEYWORDS)
    assert set(Product.objects.values_list("attributes__series", flat=True)) <= set(
        seed_data.SERIES
    )


def test_deep_dimension_is_null_for_flats_and_set_for_case_goods() -> None:
    seed()

    assert Product.objects.filter(category__slug="decor", depth_cm__isnull=True).exists()
    assert Product.objects.filter(category__slug="living-room", depth_cm__isnull=False).exists()


def test_clear_removes_the_whole_catalog() -> None:
    seed()

    clear()

    assert _counts() == (0, 0, 0, 0, 0)


def test_every_seeded_row_passes_model_validation() -> None:
    """SQLite does not enforce `max_length`, so only `full_clean()` catches overflowing values.

    This is how a too-long `alt` text got as far as PostgreSQL during `M1.2`.
    """
    seed()

    for model in (Category, Product, ProductVariant, ProductImage, ImageCredit):
        for row in model.objects.all():
            row.full_clean()


def test_an_unknown_curated_keyword_fails_loudly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(seed_data.CATALOG, "Living Room", ("armchair", "no such keyword"))

    with pytest.raises(ValueError, match="no such keyword"):
        seed()
