"""Operator console for orders (M5).

Drives the real Django admin over HTTP so the tests cover what the operator
actually gets: access control, the guarded actions, and the fields the console
refuses to let anyone edit.
"""

from __future__ import annotations

from typing import Any

import pytest
from django.test import Client
from django.urls import reverse

from accounts.models import Address, User
from catalog.models import ProductVariant
from orders.models import Order, OrderItem
from orders.services import transition_order


@pytest.fixture
def order(db: Any, shopper: User, address: Address, variant: ProductVariant) -> Order:
    order = Order.objects.create(
        user=shopper,
        subtotal=2_000_000,
        shipping_cost=0,
        total=2_000_000,
        shipping_method="standard",
        shipping_method_name="Standard delivery",
        shipping_address_snapshot={"recipient": "Ada Lovelace"},
        idempotency_key="admin-key-1",
    )
    OrderItem.objects.create(
        order=order,
        variant=variant,
        product_title_snapshot="Nordvik Sofa",
        variant_name_snapshot="Fog grey",
        unit_price=1_000_000,
        quantity=2,
        line_total=2_000_000,
    )
    variant.stock_qty = 3
    variant.save(update_fields=["stock_qty"])
    return order


def status_of(order_pk: int) -> str:
    return Order.objects.get(pk=order_pk).status


def run_action(client: Client, action: str, *order_ids: int) -> Any:
    return client.post(
        reverse("admin:orders_order_changelist"),
        {"action": action, "_selected_action": [str(pk) for pk in order_ids]},
        follow=True,
    )


@pytest.mark.django_db
def test_the_changelist_is_reachable_for_staff(staff_client):
    response = staff_client.get(reverse("admin:orders_order_changelist"))

    assert response.status_code == 200


@pytest.mark.django_db
def test_an_anonymous_visitor_is_sent_to_the_admin_login(client):
    response = client.get(reverse("admin:orders_order_changelist"))

    assert response.status_code == 302
    assert reverse("admin:login") in response["Location"]


@pytest.mark.django_db
def test_a_signed_in_customer_is_still_refused(client, shopper):
    client.force_login(shopper)

    response = client.get(reverse("admin:orders_order_changelist"))

    assert response.status_code == 302


@pytest.mark.django_db
def test_operator_walks_an_order_through_fulfilment(staff_client, order):
    transition_order(order, "paid")

    run_action(staff_client, "mark_processing", order.pk)
    assert status_of(order.pk) == "processing"

    run_action(staff_client, "mark_shipped", order.pk)
    assert status_of(order.pk) == "shipped"

    run_action(staff_client, "mark_completed", order.pk)
    assert status_of(order.pk) == "completed"


@pytest.mark.django_db
def test_operator_cannot_jump_straight_to_shipped(staff_client, order):
    response = run_action(staff_client, "mark_shipped", order.pk)

    assert response.status_code == 200
    assert status_of(order.pk) == "pending_payment"
    assert "could not move" in response.content.decode()


@pytest.mark.django_db
def test_operator_cancels_an_order_and_the_stock_comes_back(staff_client, order, variant):
    run_action(staff_client, "cancel_orders", order.pk)

    variant.refresh_from_db()
    assert variant.stock_qty == 5
    assert status_of(order.pk) == "cancelled"


@pytest.mark.django_db
def test_actions_tolerate_a_mixed_selection(staff_client, order):
    second = Order.objects.create(
        user=order.user,
        subtotal=1_000_000,
        shipping_cost=0,
        total=1_000_000,
        shipping_method="standard",
        shipping_method_name="Standard delivery",
        shipping_address_snapshot={"recipient": "Ada Lovelace"},
        idempotency_key="admin-key-2",
    )
    transition_order(second, "paid")
    transition_order(second, "processing")

    response = run_action(staff_client, "mark_shipped", order.pk, second.pk)

    html = response.content.decode()
    assert status_of(order.pk) == "pending_payment"
    assert status_of(second.pk) == "shipped"
    assert "could not move" in html
    assert "1 order(s) moved to shipped" in html


@pytest.mark.django_db
def test_order_records_are_shown_but_not_editable(staff_client, order):
    response = staff_client.get(reverse("admin:orders_order_change", args=[order.pk]))

    assert response.status_code == 200
    form = response.context["adminform"].form
    for locked in ("status", "total", "subtotal", "shipping_cost", "idempotency_key"):
        assert locked not in form.fields, f"{locked} must not be hand-editable"


@pytest.mark.django_db
def test_orders_cannot_be_created_or_deleted_from_the_console(staff_client, order):
    added = staff_client.get(reverse("admin:orders_order_add"))
    deleted = staff_client.get(reverse("admin:orders_order_delete", args=[order.pk]))

    assert added.status_code == 403
    assert deleted.status_code == 403


@pytest.mark.django_db
def test_the_item_snapshot_is_shown_but_not_editable(staff_client, order):
    response = staff_client.get(reverse("admin:orders_order_change", args=[order.pk]))

    assert response.status_code == 200
    inline = response.context["inline_admin_formsets"][0]
    assert inline.formset.can_delete is False
    form = inline.formset.forms[0]
    for locked in (
        "product_title_snapshot",
        "variant_name_snapshot",
        "unit_price",
        "line_total",
    ):
        assert locked not in form.fields, f"{locked} must not be hand-editable"
    assert "Nordvik Sofa" in response.content.decode()
