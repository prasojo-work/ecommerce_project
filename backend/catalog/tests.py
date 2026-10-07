# Create your tests here.
import pytest
from ninja.testing import TestClient

from catalog.models import Category, Product, ProductImage, ProductVariant
from core.api import api

client = TestClient(api)


@pytest.fixture
def catalog(db):
    living = Category.objects.create(name="Living room", slug="living-room")
    bedroom = Category.objects.create(name="Bedroom", slug="bedroom")

    sofa = Product.objects.create(
        category=living,
        title="Nordvik Sofa",
        slug="nordvik-sofa",
        status=Product.Status.ACTIVE,
        brand="Nordvik",
        base_price=5_000_000,
        description="A compact sofa.",
    )
    ProductVariant.objects.create(
        product=sofa, sku="SOFA-A", name="Fog grey", stock_qty=3
    )
    ProductVariant.objects.create(
        product=sofa, sku="SOFA-B", name="Deep green", price=4_200_000, stock_qty=2
    )
    ProductImage.objects.create(
        product=sofa, url="https://example.com/sofa.jpg", alt="Sofa", position=0
    )

    Product.objects.create(
        category=bedroom,
        title="Lund Bed",
        slug="lund-bed",
        status=Product.Status.ACTIVE,
        base_price=3_200_000,
    )
    Product.objects.create(
        category=bedroom,
        title="Draft Table",
        slug="draft-table",
        status=Product.Status.DRAFT,
        base_price=100,
    )
    return {"sofa": sofa}


def test_list_categories(catalog):
    response = client.get("/categories")
    assert response.status_code == 200
    slugs = {c["slug"] for c in response.json()}
    assert {"living-room", "bedroom"} <= slugs


def test_list_products_excludes_drafts(catalog):
    body = client.get("/products").json()
    assert body["count"] == 2
    assert {r["slug"] for r in body["results"]} == {"nordvik-sofa", "lund-bed"}


def test_pagination(catalog):
    first = client.get("/products?page_size=1").json()
    assert first["count"] == 2
    assert len(first["results"]) == 1

    second = client.get("/products?page_size=1&page=2").json()
    assert len(second["results"]) == 1
    assert second["results"][0]["slug"] != first["results"][0]["slug"]


def test_search(catalog):
    body = client.get("/products?q=sofa").json()
    assert body["count"] == 1
    assert body["results"][0]["slug"] == "nordvik-sofa"


def test_filter_by_category(catalog):
    body = client.get("/products?category=bedroom").json()
    assert body["count"] == 1
    assert body["results"][0]["slug"] == "lund-bed"


def test_sort_by_price(catalog):
    body = client.get("/products?sort=price").json()
    prices = [r["price_from"] for r in body["results"]]
    assert prices == [3_200_000, 4_200_000]


def test_price_from_uses_cheapest_variant(catalog):
    body = client.get("/products?q=sofa").json()
    assert body["results"][0]["price_from"] == 4_200_000


def test_product_detail(catalog):
    response = client.get("/products/nordvik-sofa")
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Nordvik Sofa"
    assert len(body["variants"]) == 2
    assert len(body["images"]) == 1
    assert body["variants"][0]["price"] == 5_000_000


def test_product_detail_not_found(catalog):
    assert client.get("/products/missing").status_code == 404
