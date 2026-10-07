"""Inventory console (M5, `US-7.2` avoid overselling)."""

from __future__ import annotations

import pytest
from django.urls import reverse

from catalog.models import Product, ProductVariant

VARIANTS = "admin:catalog_productvariant_changelist"
PRODUCTS = "admin:catalog_product_changelist"


def run_action(client, url: str, action: str, *pks: int):
    return client.post(
        reverse(url),
        {"action": action, "_selected_action": [str(pk) for pk in pks]},
        follow=True,
    )


@pytest.mark.django_db
def test_stock_level_filter_shows_what_needs_reordering(staff_client, variant):
    variant.sku = "SOFA-LOW"
    variant.stock_qty = 2
    variant.save(update_fields=["sku", "stock_qty"])
    ProductVariant.objects.create(
        product=variant.product, sku="SOFA-PLENTY", name="Oak", stock_qty=40
    )

    response = staff_client.get(f"{reverse(VARIANTS)}?stock=low")

    html = response.content.decode()
    assert response.status_code == 200
    assert "SOFA-LOW" in html
    assert "SOFA-PLENTY" not in html


@pytest.mark.django_db
def test_out_of_stock_filter(staff_client, variant):
    variant.sku = "SOFA-GONE"
    variant.stock_qty = 0
    variant.save(update_fields=["sku", "stock_qty"])
    ProductVariant.objects.create(
        product=variant.product, sku="SOFA-FINE", name="Oak", stock_qty=9
    )

    response = staff_client.get(f"{reverse(VARIANTS)}?stock=out")

    html = response.content.decode()
    assert "SOFA-GONE" in html
    assert "SOFA-FINE" not in html


@pytest.mark.django_db
def test_stock_is_editable_straight_from_the_list(staff_client, variant):
    response = staff_client.get(reverse(VARIANTS))

    assert response.status_code == 200
    assert 'name="form-0-stock_qty"' in response.content.decode()


@pytest.mark.django_db
def test_operator_deactivates_variants_in_bulk(staff_client, variant):
    run_action(staff_client, VARIANTS, "deactivate_variants", variant.pk)

    variant.refresh_from_db()
    assert variant.is_active is False


@pytest.mark.django_db
def test_operator_archives_a_product(staff_client, variant):
    run_action(staff_client, PRODUCTS, "archive_products", variant.product.pk)

    variant.product.refresh_from_db()
    assert variant.product.status == Product.Status.ARCHIVED


@pytest.mark.django_db
def test_operator_publishes_a_product(staff_client, variant):
    variant.product.status = Product.Status.DRAFT
    variant.product.save(update_fields=["status"])

    run_action(staff_client, PRODUCTS, "publish_products", variant.product.pk)

    variant.product.refresh_from_db()
    assert variant.product.status == Product.Status.ACTIVE


@pytest.mark.django_db
def test_an_anonymous_visitor_cannot_reach_the_inventory(client):
    response = client.get(reverse(VARIANTS))

    assert response.status_code == 302
    assert reverse("admin:login") in response["Location"]
