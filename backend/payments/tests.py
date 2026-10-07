from __future__ import annotations

import json
from typing import Any

import pytest

from orders.models import Order
from payments.models import Payment


def _pay(client, headers, order_number: str, *, simulate_failure: bool = False):
    return client.post(
        "/api/v1/payments/mock",
        data=json.dumps(
            {"order_number": order_number, "simulate_failure": simulate_failure}
        ),
        content_type="application/json",
        headers=headers,
    )


@pytest.fixture
def pending_order(client, login, cart_add, place_order, address, variant) -> Any:
    """Return ``(headers, order_number, total)`` for a fresh `pending_payment` order."""
    headers = login()
    cart_add(headers, variant, 1)
    body = place_order(headers, address, key="pay-key-1").json()
    return headers, body["number"], body["total"]


@pytest.mark.django_db
def test_mock_payment_settles_the_order(client, pending_order):
    headers, number, total = pending_order

    response = _pay(client, headers, number)

    assert response.status_code == 201
    body = response.json()
    assert body["order_number"] == number
    assert body["provider"] == "mock"
    assert body["status"] == "succeeded"
    assert body["amount"] == total
    assert body["provider_reference"].startswith("MOCK-")
    assert Order.objects.get(number=number).status == Order.Status.PAID


@pytest.mark.django_db
def test_failed_payment_leaves_the_order_pending(client, pending_order):
    headers, number, _ = pending_order

    response = _pay(client, headers, number, simulate_failure=True)

    assert response.status_code == 201
    assert response.json()["status"] == "failed"
    assert Order.objects.get(number=number).status == Order.Status.PENDING_PAYMENT


@pytest.mark.django_db
def test_shopper_can_retry_a_failed_payment(client, pending_order):
    headers, number, _ = pending_order
    failed_id = _pay(client, headers, number, simulate_failure=True).json()["id"]

    retry = _pay(client, headers, number)

    assert retry.status_code == 201
    assert retry.json()["id"] == failed_id
    assert retry.json()["status"] == "succeeded"
    assert Order.objects.get(number=number).status == Order.Status.PAID
    assert Payment.objects.count() == 1


@pytest.mark.django_db
def test_replaying_a_settled_payment_is_idempotent(client, pending_order):
    headers, number, _ = pending_order

    first = _pay(client, headers, number)
    second = _pay(client, headers, number)

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["id"] == first.json()["id"]
    assert Payment.objects.count() == 1


@pytest.mark.django_db
def test_settled_order_is_not_payable_after_a_status_change(client, pending_order):
    headers, number, _ = pending_order
    order = Order.objects.get(number=number)
    order.status = Order.Status.SHIPPED
    order.save(update_fields=["status"])

    response = _pay(client, headers, number)

    assert response.status_code == 409
    assert Payment.objects.count() == 0


@pytest.mark.django_db
def test_cannot_pay_another_users_order(client, pending_order, login):
    _, number, _ = pending_order

    response = _pay(client, login("rival@example.com"), number)

    assert response.status_code == 404
    assert Payment.objects.count() == 0


@pytest.mark.django_db
def test_unknown_order_number_is_rejected(client, login):
    response = _pay(client, login(), "NDV-2026-999999")

    assert response.status_code == 404


@pytest.mark.django_db
def test_payment_requires_authentication(client):
    response = client.post(
        "/api/v1/payments/mock",
        data=json.dumps({"order_number": "NDV-2026-000001"}),
        content_type="application/json",
    )

    assert response.status_code == 401
