"""Contract tests for the order history and detail routes (`API.md` section 6, `US-4.5`, `US-4.6`).

Two promises are tested here, and neither is about money. **Scoping**, because `GET /orders/{number}`
takes an identifier a customer can read off a receipt and type — an order that is not the caller's has
to be unreachable rather than merely unlinked, and the refusal has to say nothing about whether it
exists. **Shape**, because the history answers with rows and the detail with a receipt: the difference
is what keeps one page from shipping every order's full contents, and it is exactly the kind of
difference that quietly collapses when one schema is reused for both.

`US-4.6` also asks for the status *timeline*, which is `M4.1`'s `OrderEvent` read back in the order it
was written — so the tests read it forwards, not reversed.
"""

import json
from typing import Any

import pytest
from django.test import Client

from accounts.models import User
from accounts.tokens import issue_tokens
from cart.models import Cart, CartItem, CartStatus
from catalog.models import Category, Product, ProductVariant
from orders.shipping import DEFAULT_METHOD_CODE, SHIPPING_METHODS

pytestmark = pytest.mark.django_db

client = Client()

ORDERS = "/api/v1/orders"
PAYMENTS = "/api/v1/payments/mock/confirm"

PASSWORD = "correct-horse-battery-staple"
UNIT_PRICE = 12900

STANDARD_PRICE = next(
    method.price_cents for method in SHIPPING_METHODS if method.code == DEFAULT_METHOD_CODE
)

INLINE_ADDRESS = {
    "recipient": "Ada Lovelace",
    "line1": "12 Analytical Way",
    "city": "London",
    "postal_code": "EC1A 1BB",
    "country": "GB",
}


@pytest.fixture
def shopper() -> User:
    return User.objects.create_user(email="ada@example.com", password=PASSWORD)


@pytest.fixture
def other_shopper() -> User:
    return User.objects.create_user(email="grace@example.com", password=PASSWORD)


@pytest.fixture
def variant() -> ProductVariant:
    category = Category.objects.create(name="Seating", slug="seating")
    product = Product.objects.create(
        category=category, name="Aalto Chair", slug="aalto-chair", base_price_cents=UNIT_PRICE
    )
    return ProductVariant.objects.create(
        product=product, sku="AAL-OAK", name="Oak", price_cents=UNIT_PRICE, stock_qty=10
    )


def auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {issue_tokens(user).access_token}"}


def place(user: User, variant: ProductVariant, quantity: int = 1, key: str | None = None) -> str:
    """Order a variant the way a customer does, and answer with the number it was given."""
    cart = Cart.objects.create(user=user, status=CartStatus.ACTIVE)
    CartItem.objects.create(cart=cart, variant=variant, quantity=quantity)

    headers = auth(user)
    if key is not None:
        headers["Idempotency-Key"] = key

    response = client.post(
        ORDERS,
        data=json.dumps({"address": INLINE_ADDRESS, "shipping_method": DEFAULT_METHOD_CODE}),
        content_type="application/json",
        headers=headers,
    )
    assert response.status_code == 201
    return str(response.json()["number"])


def history(user: User, **params: Any) -> Any:
    return client.get(ORDERS, params, headers=auth(user))


def test_the_history_needs_a_token(shopper: User) -> None:
    response = client.get(ORDERS)

    assert response.status_code == 401


def test_the_history_lists_only_the_callers_orders(
    shopper: User, other_shopper: User, variant: ProductVariant
) -> None:
    mine = place(shopper, variant)
    theirs = place(other_shopper, variant)

    numbers = [row["number"] for row in history(shopper).json()["items"]]

    assert numbers == [mine]
    assert theirs not in numbers


def test_the_history_is_newest_first(shopper: User, variant: ProductVariant) -> None:
    older = place(shopper, variant)
    newer = place(shopper, variant)

    numbers = [row["number"] for row in history(shopper).json()["items"]]

    assert numbers == [newer, older]


def test_a_row_carries_what_the_page_renders_and_not_the_whole_receipt(
    shopper: User, variant: ProductVariant
) -> None:
    number = place(shopper, variant, quantity=2)

    row = history(shopper).json()["items"][0]

    assert row["number"] == number
    assert row["status"] == "pending"
    assert row["item_count"] == 2
    assert row["total"] == {"amount_cents": UNIT_PRICE * 2 + STANDARD_PRICE, "currency": "USD"}
    assert row["placed_at"] != ""
    # The point of the row shape: pricing one page of orders must not pull every order's address and
    # every line into the response.
    assert "items" not in row
    assert "shipping_address" not in row


def test_the_history_pages_and_reports_the_total_before_paging(
    shopper: User, variant: ProductVariant
) -> None:
    for _ in range(3):
        place(shopper, variant)

    first = history(shopper, page_size=2).json()

    assert len(first["items"]) == 2
    assert first["total"] == 3
    assert first["page"] == 1
    assert first["page_size"] == 2

    second = history(shopper, page=2, page_size=2).json()

    assert len(second["items"]) == 1
    assert second["total"] == 3
    # Past the end is empty rather than an error, the rule the catalog's paging already states.
    assert history(shopper, page=9, page_size=2).json()["items"] == []


def test_the_detail_is_the_receipt_the_confirmation_showed(
    shopper: User, variant: ProductVariant
) -> None:
    number = place(shopper, variant, quantity=2)

    response = client.get(f"{ORDERS}/{number}", headers=auth(shopper))

    assert response.status_code == 200
    payload = response.json()
    assert payload["number"] == number
    assert payload["status"] == "pending"
    assert payload["items"] == [
        {
            "product_name": "Aalto Chair",
            "variant_name": "Oak",
            "unit_price": {"amount_cents": UNIT_PRICE, "currency": "USD"},
            "quantity": 2,
            "line_total": {"amount_cents": UNIT_PRICE * 2, "currency": "USD"},
        }
    ]
    assert payload["shipping_address"]["recipient"] == "Ada Lovelace"
    assert payload["shipping_address"]["postal_code"] == "EC1A 1BB"
    assert payload["total"]["amount_cents"] == (
        payload["subtotal"]["amount_cents"] + payload["shipping"]["amount_cents"]
    )


def test_the_timeline_starts_at_creation_and_reads_forwards(
    shopper: User, variant: ProductVariant
) -> None:
    number = place(shopper, variant)

    events = client.get(f"{ORDERS}/{number}", headers=auth(shopper)).json()["events"]

    assert [(event["from_status"], event["to_status"]) for event in events] == [("", "pending")]


def test_a_settled_order_shows_every_step_it_took(shopper: User, variant: ProductVariant) -> None:
    number = place(shopper, variant)
    settled = client.post(
        PAYMENTS,
        data=json.dumps({"order_number": number}),
        content_type="application/json",
        headers=auth(shopper),
    )
    assert settled.status_code == 200

    payload = client.get(f"{ORDERS}/{number}", headers=auth(shopper)).json()

    assert payload["status"] == "paid"
    assert [(event["from_status"], event["to_status"]) for event in payload["events"]] == [
        ("", "pending"),
        ("pending", "paid"),
    ]


def test_another_shoppers_order_is_a_404_that_says_nothing_about_it(
    shopper: User, other_shopper: User, variant: ProductVariant
) -> None:
    theirs = place(other_shopper, variant)

    response = client.get(f"{ORDERS}/{theirs}", headers=auth(shopper))

    assert response.status_code == 404
    # Not a `403`, and no hint that the number is real: a distinguishable refusal would confirm that
    # somebody else's order exists.
    assert response.json()["error"]["message"] == "No such order."


def test_an_unknown_number_answers_the_same_404_as_somebody_elses(
    shopper: User, variant: ProductVariant
) -> None:
    place(shopper, variant)

    response = client.get(f"{ORDERS}/LSH-00000000", headers=auth(shopper))

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "No such order."


def test_the_detail_needs_a_token_like_the_history_does(
    shopper: User, variant: ProductVariant
) -> None:
    number = place(shopper, variant)

    assert client.get(f"{ORDERS}/{number}").status_code == 401
