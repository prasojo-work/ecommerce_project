"""Contract tests for the catalog read API (`API.md` section 4).

The catalog is seeded once for the module: every test here reads, so re-seeding per test would
only add time.
"""

from collections.abc import Iterator
from typing import Any

import pytest
from django.core.management import call_command
from django.test import Client
from django.utils.text import slugify

from catalog import seed_data
from catalog.models import Product
from catalog.seeders import clear

pytestmark = pytest.mark.django_db

client = Client()

CATEGORY_SLUGS = [slugify(name) for name in seed_data.CATALOG]
TOTAL_PRODUCTS = sum(len(keywords) for keywords in seed_data.CATALOG.values())


@pytest.fixture(scope="module", autouse=True)
def seeded_catalog(django_db_setup: Any, django_db_blocker: Any) -> Iterator[None]:
    """Seed once for the module, then clear it.

    A module-scoped fixture cannot use the per-test transaction, so this data is committed and
    outlives each test. Clear it on teardown, or the catalog leaks into the other test modules —
    the model tests assert against an empty database and fail on 46 unexpected products.
    """
    with django_db_blocker.unblock():
        call_command("seed")
        yield
        clear()


def _items(url: str) -> list[dict[str, Any]]:
    response = client.get(url)
    assert response.status_code == 200
    return response.json()["items"]


def test_category_tree_lists_every_category() -> None:
    response = client.get("/api/v1/categories")

    assert response.status_code == 200
    body = response.json()
    assert [item["slug"] for item in body["items"]] == CATEGORY_SLUGS


def test_category_tree_is_flat_and_unpaginated() -> None:
    """The seed has no nested categories, and a tree is not a paged listing."""
    body = client.get("/api/v1/categories").json()

    assert "total" not in body
    assert all(item["children"] == [] for item in body["items"])
    assert all(item["parent_slug"] is None for item in body["items"])


def test_category_detail_returns_the_category_and_its_products() -> None:
    response = client.get("/api/v1/categories/living-room")

    assert response.status_code == 200
    body = response.json()
    assert body["category"]["slug"] == "living-room"
    assert body["total"] == len(seed_data.CATALOG["Living Room"])
    assert len(body["items"]) == body["total"]


def test_category_detail_404s_for_an_unknown_slug() -> None:
    response = client.get("/api/v1/categories/nope")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_products_returns_the_first_page_with_paging_metadata() -> None:
    response = client.get("/api/v1/products")

    assert response.status_code == 200
    body = response.json()
    assert (body["page"], body["page_size"], body["total"]) == (1, 24, TOTAL_PRODUCTS)
    assert len(body["items"]) == 24


def test_the_second_page_continues_without_overlap() -> None:
    first = _items("/api/v1/products")
    second = _items("/api/v1/products?page=2")

    assert len(first) + len(second) == TOTAL_PRODUCTS
    assert {item["slug"] for item in first}.isdisjoint({item["slug"] for item in second})


def test_a_page_past_the_end_is_empty_rather_than_an_error() -> None:
    response = client.get("/api/v1/products?page=99")

    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == TOTAL_PRODUCTS


def test_page_size_is_honoured() -> None:
    assert len(_items("/api/v1/products?page_size=5")) == 5


def test_page_size_above_the_maximum_is_rejected_with_the_envelope() -> None:
    response = client.get("/api/v1/products?page_size=101")

    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["details"][0]["field"] == "query.page_size"


def test_a_zero_page_is_rejected() -> None:
    response = client.get("/api/v1/products?page=0")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_an_unknown_sort_value_is_rejected() -> None:
    response = client.get("/api/v1/products?sort=cheapest")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_a_card_does_not_nest_variants() -> None:
    """The listing is for the grid (`M1.5`); variants belong to the detail payload."""
    card = _items("/api/v1/products?page_size=1")[0]

    assert "variants" not in card
    assert "availability" not in card


def test_a_card_carries_what_the_grid_renders() -> None:
    """`US-1.1`: image, name, and price."""
    card = _items("/api/v1/products?page_size=1")[0]

    assert card["name"]
    assert card["price"]["amount_cents"] > 0
    assert card["price"]["currency"] == "USD"
    assert card["image"]["path"].startswith("/images/")
    assert card["category"]["slug"] in CATEGORY_SLUGS
    assert isinstance(card["in_stock"], bool)


def test_filtering_by_category_returns_only_that_category() -> None:
    items = _items("/api/v1/products?category=lighting&page_size=100")

    assert len(items) == len(seed_data.CATALOG["Lighting"])
    assert {item["category"]["slug"] for item in items} == {"lighting"}


def test_an_unknown_category_filters_to_nothing() -> None:
    response = client.get("/api/v1/products?category=nope")

    assert response.status_code == 200
    assert response.json() == {"items": [], "page": 1, "page_size": 24, "total": 0}


def test_filtering_by_price_band() -> None:
    items = _items("/api/v1/products?min_price=50000&max_price=100000&page_size=100")

    assert items
    assert all(50_000 <= item["price"]["amount_cents"] <= 100_000 for item in items)


def test_search_matches_the_name_or_the_keyword() -> None:
    """`US-1.3`: the query searches names and keywords."""
    by_name = _items("/api/v1/products?q=armchair&page_size=100")
    by_keyword = _items("/api/v1/products?q=oak&page_size=100")

    assert any("Armchair" in item["name"] for item in by_name)
    assert by_keyword
    for item in by_keyword:
        assert (
            "oak" in item["name"].lower()
            or "oak" in str(Product.objects.get(slug=item["slug"]).attributes).lower()
        )


def test_a_search_with_no_matches_is_an_empty_page() -> None:
    response = client.get("/api/v1/products?q=zzzznomatch")

    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_default_sort_is_by_name_so_paging_is_stable() -> None:
    names = [item["name"] for item in _items("/api/v1/products?page_size=100")]

    assert names == sorted(names)


def test_sort_price_ascending() -> None:
    amounts = [
        item["price"]["amount_cents"]
        for item in _items("/api/v1/products?sort=price&page_size=100")
    ]

    assert amounts == sorted(amounts)


def test_sort_price_descending() -> None:
    amounts = [
        item["price"]["amount_cents"]
        for item in _items("/api/v1/products?sort=-price&page_size=100")
    ]

    assert amounts == sorted(amounts, reverse=True)


def test_sort_newest_matches_the_database_ordering() -> None:
    items = _items("/api/v1/products?sort=newest&page_size=100")
    expected = list(Product.objects.order_by("-created_at", "name").values_list("slug", flat=True))

    assert [item["slug"] for item in items] == expected


def test_the_default_page_size_is_twenty_four() -> None:
    assert client.get("/api/v1/products").json()["page_size"] == 24


def test_an_out_of_stock_product_is_flagged_in_the_listing() -> None:
    """The seed marks one product in ten out of stock, so the state is always reachable."""
    items = _items("/api/v1/products?page_size=100")

    assert any(item["in_stock"] is False for item in items)
    assert any(item["in_stock"] is True for item in items)


def test_product_detail_nests_variants_and_images() -> None:
    """`US-1.2`: the detail payload carries the gallery and the variants."""
    slug = _items("/api/v1/products?page_size=1")[0]["slug"]
    response = client.get(f"/api/v1/products/{slug}")

    assert response.status_code == 200
    body = response.json()
    assert body["variants"], "the detail payload must nest variants"
    assert body["images"], "the detail payload must carry the gallery"
    assert body["variants"][0]["price"]["currency"] == "USD"


def test_product_detail_availability_agrees_with_its_variants() -> None:
    slug = _items("/api/v1/products?page_size=1")[0]["slug"]
    body = client.get(f"/api/v1/products/{slug}").json()

    in_stock_variants = [variant for variant in body["variants"] if variant["in_stock"]]
    assert body["availability"]["in_stock_variants"] == len(in_stock_variants)
    assert body["availability"]["in_stock"] is bool(in_stock_variants)


def test_product_detail_404s_for_an_unknown_slug() -> None:
    response = client.get("/api/v1/products/nope")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_the_error_envelope_matches_the_request_id_header() -> None:
    """`NFR-4` and `NFR-5`: one error shape, correlatable with the logs."""
    response = client.get("/api/v1/products/nope")
    error = response.json()["error"]

    assert set(error) == {"code", "message", "details", "request_id"}
    assert error["request_id"] == response.headers["X-Request-ID"]
    assert error["details"] == []


def test_openapi_documents_every_catalog_path() -> None:
    """`M1.3` owns the contract the frontend types are generated from at `M1.4`."""
    schema = client.get("/api/v1/openapi.json").json()

    assert set(schema["paths"]) == {
        "/api/v1/categories",
        "/api/v1/categories/{slug}",
        "/api/v1/products",
        "/api/v1/products/{slug}",
    }


def test_openapi_documents_the_product_filters() -> None:
    schema = client.get("/api/v1/openapi.json").json()
    parameters = schema["paths"]["/api/v1/products"]["get"]["parameters"]
    names = {parameter["name"] for parameter in parameters}

    assert {"category", "q", "min_price", "max_price", "sort", "page", "page_size"} <= names
