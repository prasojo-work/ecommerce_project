from __future__ import annotations

import json
import re

import pytest

from accounts.models import Address
from cart.models import Cart
from orders.models import Order
from orders.shipping import FREE_SHIPPING_THRESHOLD

ORDER_NUMBER_PATTERN = r"NDV-\d{4}-\d{6}"


@pytest.mark.django_db
def test_shipping_options_are_priced_against_the_live_cart(client, login, cart_add, variant):
    headers = login()

    empty = client.get("/api/v1/shipping/options", headers=headers).json()
    assert empty["subtotal"] == 0
    assert empty["currency"] == "IDR"
    assert empty["free_shipping_threshold"] == FREE_SHIPPING_THRESHOLD
    assert [option["cost"] for option in empty["options"]] == [25_000, 60_000]
    assert [option["eta"] for option in empty["options"]] == ["3–5 days", "1–2 days"]

    cart_add(headers, variant, 1)
    priced = client.get("/api/v1/shipping/options", headers=headers).json()
    assert priced["subtotal"] == 1_000_000
    assert [option["cost"] for option in priced["options"]] == [0, 60_000]


@pytest.mark.django_db
def test_checkout_creates_a_pending_order_with_snapshots(
    client, login, cart_add, place_order, address, variant
):
    headers = login()
    cart_add(headers, variant, 2)

    response = place_order(headers, address, key="key-1")

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending_payment"
    assert re.fullmatch(ORDER_NUMBER_PATTERN, body["number"])
    assert body["subtotal"] == 2_000_000
    assert body["shipping_cost"] == 0
    assert body["total"] == 2_000_000
    assert body["currency"] == "IDR"
    assert body["shipping_method"] == "standard"
    assert body["shipping_method_name"] == "Standard delivery"
    assert body["shipping_address"]["recipient"] == address.recipient
    assert body["shipping_address"]["city"] == "Bandung"

    item = body["items"][0]
    assert item["product_title"] == "Nordvik Sofa"
    assert item["variant_name"] == "Fog grey"
    assert item["unit_price"] == 1_000_000
    assert item["quantity"] == 2
    assert item["line_total"] == 2_000_000


@pytest.mark.django_db
def test_standard_shipping_is_charged_below_the_free_threshold(
    client, login, cart_add, place_order, address, variant
):
    variant.product.base_price = 100_000
    variant.product.save(update_fields=["base_price"])
    headers = login()
    cart_add(headers, variant, 1)

    body = place_order(headers, address).json()

    assert body["subtotal"] == 100_000
    assert body["shipping_cost"] == 25_000
    assert body["total"] == 125_000


@pytest.mark.django_db
def test_express_shipping_is_never_free(client, login, cart_add, place_order, address, variant):
    headers = login()
    cart_add(headers, variant, 1)

    body = place_order(headers, address, shipping="express").json()

    assert body["shipping_method"] == "express"
    assert body["shipping_cost"] == 60_000
    assert body["total"] == 1_060_000


@pytest.mark.django_db
def test_order_prices_come_from_the_cart_snapshot(
    client, login, cart_add, place_order, address, variant
):
    headers = login()
    cart_add(headers, variant, 1)

    variant.price = 9_000_000
    variant.save(update_fields=["price"])

    body = place_order(headers, address).json()

    assert body["items"][0]["unit_price"] == 1_000_000
    assert body["total"] == 1_000_000


@pytest.mark.django_db
def test_checkout_reserves_stock_and_clears_the_cart(
    client, login, cart_add, place_order, address, variant
):
    headers = login()
    cart_add(headers, variant, 2)

    place_order(headers, address)

    variant.refresh_from_db()
    assert variant.stock_qty == 3
    assert client.get("/api/v1/cart", headers=headers).json()["items"] == []


@pytest.mark.django_db
def test_duplicate_submit_returns_the_same_order(client, login, cart_add, place_order, address, variant):
    headers = login()
    cart_add(headers, variant, 1)

    first = place_order(headers, address, key="key-dup")
    second = place_order(headers, address, key="key-dup")

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["number"] == second.json()["number"]
    assert Order.objects.count() == 1


@pytest.mark.django_db
def test_checkout_rejects_an_empty_cart(client, login, place_order, address):
    response = place_order(login(), address)

    assert response.status_code == 400
    assert Order.objects.count() == 0


@pytest.mark.django_db
def test_checkout_rejects_insufficient_stock(client, login, cart_add, place_order, address, variant):
    headers = login()
    cart_add(headers, variant, 6)

    response = place_order(headers, address)

    assert response.status_code == 409
    assert "Only 5 left" in response.json()["detail"]
    assert Order.objects.count() == 0
    variant.refresh_from_db()
    assert variant.stock_qty == 5


@pytest.mark.django_db
def test_checkout_rejects_an_unknown_shipping_method(client, login, cart_add, place_order, address, variant):
    headers = login()
    cart_add(headers, variant, 1)

    assert place_order(headers, address, shipping="teleport").status_code == 400
    assert Order.objects.count() == 0


@pytest.mark.django_db
def test_checkout_rejects_another_users_address(
    client, login, cart_add, place_order, variant, rival
):
    headers = login()
    cart_add(headers, variant, 1)
    rivals_address = Address.objects.create(
        user=rival,
        recipient="Someone else",
        phone="0899",
        line1="Elsewhere 9",
        city="Jakarta",
        province="DKI Jakarta",
        postal_code="10110",
    )

    response = place_order(headers, rivals_address)

    assert response.status_code == 404
    assert Order.objects.count() == 0


@pytest.mark.django_db
def test_checkout_requires_authentication(client, address):
    response = client.post(
        "/api/v1/orders",
        data=json.dumps({"address_id": address.id, "shipping_method": "standard"}),
        content_type="application/json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_order_history_lists_own_orders_newest_first(
    client, login, cart_add, place_order, address, variant
):
    headers = login()
    cart_add(headers, variant, 1)
    first_number = place_order(headers, address, key="k1").json()["number"]
    cart_add(headers, variant, 1)
    second_number = place_order(headers, address, key="k2").json()["number"]

    body = client.get("/api/v1/orders", headers=headers).json()

    assert body["count"] == 2
    assert [row["number"] for row in body["results"]] == [second_number, first_number]
    assert body["results"][0]["item_count"] == 1


@pytest.mark.django_db
def test_order_history_hides_other_peoples_orders(
    client, login, cart_add, place_order, address, variant, rival
):
    headers = login()
    cart_add(headers, variant, 1)
    place_order(headers, address, key="k-mine")

    rival_body = client.get("/api/v1/orders", headers=login("rival@example.com")).json()

    assert rival_body["count"] == 0


@pytest.mark.django_db
def test_order_detail_is_scoped_to_the_owner(
    client, login, cart_add, place_order, address, variant, rival
):
    headers = login()
    cart_add(headers, variant, 1)
    number = place_order(headers, address, key="k-detail").json()["number"]

    assert client.get(f"/api/v1/orders/{number}", headers=headers).status_code == 200
    rival_headers = login("rival@example.com")
    assert client.get(f"/api/v1/orders/{number}", headers=rival_headers).status_code == 404
    assert client.get("/api/v1/orders/NDV-2026-999999", headers=headers).status_code == 404


@pytest.mark.django_db
def test_order_snapshot_survives_later_catalog_edits(
    client, login, cart_add, place_order, address, variant
):
    headers = login()
    cart_add(headers, variant, 1)
    number = place_order(headers, address, key="k-snapshot").json()["number"]

    variant.product.title = "Renamed Sofa"
    variant.product.save(update_fields=["title"])
    variant.name = "Renamed variant"
    variant.save(update_fields=["name"])

    body = client.get(f"/api/v1/orders/{number}", headers=headers).json()

    assert body["items"][0]["product_title"] == "Nordvik Sofa"
    assert body["items"][0]["variant_name"] == "Fog grey"


@pytest.mark.django_db
def test_order_numbers_are_unique(client, login, cart_add, place_order, address, variant):
    headers = login()
    numbers = set()
    for index in range(3):
        cart_add(headers, variant, 1)
        numbers.add(place_order(headers, address, key=f"k-{index}").json()["number"])

    assert len(numbers) == 3
    assert Order.objects.count() == 3
    assert Cart.objects.get(user__email="shopper@example.com").items.count() == 0
