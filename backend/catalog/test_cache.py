"""Cached catalog reads must be both cheap and correct (`ADR-0013`).

The point of the cache is that a repeat read costs no database work; the risk it
introduces is staleness, so these tests pin both halves.
"""

import pytest

from catalog.models import Category, Product, ProductVariant

pytestmark = pytest.mark.django_db


def _make_product(*, slug: str = "cache-test-product") -> Product:
    category, _ = Category.objects.get_or_create(
        slug="cache-test", defaults={"name": "Cache test"}
    )
    product = Product.objects.create(
        category=category,
        title="Cache test product",
        slug=slug,
        status=Product.Status.ACTIVE,
        base_price=1_000,
    )
    ProductVariant.objects.create(
        product=product, sku=f"SKU-{slug}", name="Default", price=1_000
    )
    return product


def test_a_repeated_listing_read_does_no_database_work(client, django_assert_num_queries):
    _make_product()
    client.get("/api/v1/products")

    with django_assert_num_queries(0):
        response = client.get("/api/v1/products")

    assert response.status_code == 200


def test_a_repeated_detail_read_does_no_database_work(client, django_assert_num_queries):
    product = _make_product()
    client.get(f"/api/v1/products/{product.slug}")

    with django_assert_num_queries(0):
        response = client.get(f"/api/v1/products/{product.slug}")

    assert response.status_code == 200


def test_categories_are_cached(client, django_assert_num_queries):
    _make_product()
    client.get("/api/v1/categories")

    with django_assert_num_queries(0):
        response = client.get("/api/v1/categories")

    assert response.status_code == 200


def test_a_new_product_appears_on_the_next_read_not_after_the_ttl(client):
    _make_product()
    before = client.get("/api/v1/products").json()["count"]

    _make_product(slug="cache-test-second")

    assert client.get("/api/v1/products").json()["count"] == before + 1


def test_an_edit_appears_on_the_next_read(client):
    product = _make_product()
    client.get("/api/v1/products")

    product.title = "Renamed after the read"
    product.save(update_fields=["title"])

    titles = [item["title"] for item in client.get("/api/v1/products").json()["results"]]
    assert "Renamed after the read" in titles


def test_deactivating_a_variant_is_visible_on_the_next_detail_read(client):
    product = _make_product()
    variant = product.variants.get()
    client.get(f"/api/v1/products/{product.slug}")

    variant.is_active = False
    variant.save(update_fields=["is_active"])

    payload = client.get(f"/api/v1/products/{product.slug}").json()
    assert payload["variants"][0]["is_active"] is False


def test_a_missing_slug_stays_a_404_without_retouching_the_database(
    client, django_assert_num_queries
):
    _make_product()
    assert client.get("/api/v1/products/not-a-product").status_code == 404

    with django_assert_num_queries(0):
        assert client.get("/api/v1/products/not-a-product").status_code == 404
