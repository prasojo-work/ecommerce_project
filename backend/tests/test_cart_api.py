"""Contract tests for the cart API (`API.md` section 5, `SCOPE.md` `US-3.1`-`US-3.5`).

The first thing tested is not cart behaviour but who can reach it at all: the catalog is open to
anyone and the cart is open to nobody without a token (`ADR-0017`), so all four operations are
checked for that before any of them is checked for anything else.

Stock is deliberately small — three — because the cases worth pinning are the boundary, the step
over it, and the attempt to reach the boundary twice.
"""

import json
import threading
from typing import Any

import pytest
from django.db import connection, connections
from django.test import Client

from accounts.models import User
from accounts.tokens import issue_tokens
from cart.models import Cart, CartItem, CartStatus
from catalog.models import Category, Product, ProductImage, ProductVariant

pytestmark = pytest.mark.django_db

client = Client()

PASSWORD = "correct-horse-battery-staple"
STOCK = 3
UNIT_PRICE = 12900


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
        product=product, sku="AAL-OAK", name="Oak", price_cents=UNIT_PRICE, stock_qty=STOCK
    )


def auth(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {issue_tokens(user).access_token}"}


def add(user: User, variant: ProductVariant, quantity: int = 1) -> Any:
    return client.post(
        "/api/v1/cart/items",
        data=json.dumps({"variant_id": variant.pk, "quantity": quantity}),
        content_type="application/json",
        headers=auth(user),
    )


def set_quantity(user: User, line_id: int, quantity: int) -> Any:
    return client.patch(
        f"/api/v1/cart/items/{line_id}",
        data=json.dumps({"quantity": quantity}),
        content_type="application/json",
        headers=auth(user),
    )


def remove(user: User, line_id: int) -> Any:
    return client.delete(f"/api/v1/cart/items/{line_id}", headers=auth(user))


def line_id(response: Any) -> int:
    """The id of the only line in a cart response."""
    items = response.json()["items"]
    assert len(items) == 1
    return int(items[0]["id"])


# --- who may touch a cart (`ADR-0017`) ------------------------------------------------------


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("get", "/api/v1/cart", None),
        ("post", "/api/v1/cart/items", {"variant_id": 1, "quantity": 1}),
        ("patch", "/api/v1/cart/items/1", {"quantity": 1}),
        ("delete", "/api/v1/cart/items/1", None),
    ],
)
def test_every_cart_operation_requires_a_token(
    method: str, path: str, body: dict[str, int] | None
) -> None:
    """`ADR-0017`: browsing is public, holding a cart is not. The body is valid in every case, so
    the only thing that can be refusing these is the missing token."""
    response = getattr(client, method)(
        path,
        data=None if body is None else json.dumps(body),
        content_type="application/json",
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"
    assert Cart.objects.count() == 0


def test_a_malformed_token_is_refused(shopper: User) -> None:
    response = client.get("/api/v1/cart", headers={"Authorization": "Bearer not-a-token"})

    assert response.status_code == 401


def test_reading_a_cart_never_creates_one(shopper: User) -> None:
    """Only adding something makes a cart. A reader is not yet a shopper."""
    response = client.get("/api/v1/cart", headers=auth(shopper))

    assert response.status_code == 200
    assert response.json() == {
        "id": None,
        "items": [],
        "item_count": 0,
        "subtotal": {"amount_cents": 0, "currency": "USD"},
    }
    assert Cart.objects.count() == 0


# --- adding (`US-3.1`, `US-3.2`) ------------------------------------------------------------


def test_adding_an_item_creates_the_cart_and_returns_it(
    shopper: User, variant: ProductVariant
) -> None:
    response = add(shopper, variant)

    assert response.status_code == 200
    body = response.json()
    assert body["id"] is not None
    assert body["item_count"] == 1
    assert body["subtotal"] == {"amount_cents": UNIT_PRICE, "currency": "USD"}
    assert body["items"] == [
        {
            "id": line_id(response),
            "variant_id": variant.pk,
            "product_name": "Aalto Chair",
            "product_slug": "aalto-chair",
            "variant_name": "Oak",
            "sku": "AAL-OAK",
            "unit_price": {"amount_cents": UNIT_PRICE, "currency": "USD"},
            "line_total": {"amount_cents": UNIT_PRICE, "currency": "USD"},
            "quantity": 1,
            "available_stock": STOCK,
            "image_path": None,
        }
    ]
    assert Cart.objects.filter(user=shopper, status=CartStatus.ACTIVE).count() == 1
    assert CartItem.objects.get().quantity == 1


def test_the_line_carries_the_products_primary_image(
    shopper: User, variant: ProductVariant
) -> None:
    """One query for the whole cart's images, and the first by position is the one a card shows."""
    ProductImage.objects.create(
        product=variant.product, path="/images/aalto-second.jpg", position=2
    )
    ProductImage.objects.create(product=variant.product, path="/images/aalto-first.jpg", position=0)

    response = add(shopper, variant)

    assert response.json()["items"][0]["image_path"] == "/images/aalto-first.jpg"


def test_adding_the_same_variant_twice_keeps_one_line(
    shopper: User, variant: ProductVariant
) -> None:
    """`DATA-MODEL.md` section 2 makes (`cart`, `variant`) unique, so this adds up rather than out."""
    add(shopper, variant, quantity=1)
    response = add(shopper, variant, quantity=1)

    assert response.status_code == 200
    assert response.json()["item_count"] == 2
    assert len(response.json()["items"]) == 1
    assert CartItem.objects.get().quantity == 2


def test_adding_exactly_the_available_stock_is_allowed(
    shopper: User, variant: ProductVariant
) -> None:
    response = add(shopper, variant, quantity=STOCK)

    assert response.status_code == 200
    assert response.json()["item_count"] == STOCK
    assert CartItem.objects.get().quantity == STOCK


def test_adding_more_than_the_stock_is_refused(shopper: User, variant: ProductVariant) -> None:
    response = add(shopper, variant, quantity=STOCK + 1)

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "CONFLICT"
    # `US-3.2` asks for a clear message, so it names both numbers.
    assert str(STOCK) in error["message"] and str(STOCK + 1) in error["message"]
    assert CartItem.objects.count() == 0


def test_the_cap_applies_to_the_total_not_to_the_step(
    shopper: User, variant: ProductVariant
) -> None:
    """A quantity that fits is accepted, and the one after it that would not is refused — the
    stored quantity stays where it was rather than being truncated silently."""
    add(shopper, variant, quantity=2)
    response = add(shopper, variant, quantity=2)

    assert response.status_code == 409
    assert CartItem.objects.get().quantity == 2


def test_a_variant_with_no_stock_cannot_be_added(shopper: User, variant: ProductVariant) -> None:
    variant.stock_qty = 0
    variant.save(update_fields=["stock_qty"])

    response = add(shopper, variant)

    assert response.status_code == 409


def test_adding_an_unknown_variant_is_a_404(shopper: User) -> None:
    response = client.post(
        "/api/v1/cart/items",
        data=json.dumps({"variant_id": 987654, "quantity": 1}),
        content_type="application/json",
        headers=auth(shopper),
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_adding_a_withdrawn_variant_is_a_conflict_not_a_404(
    shopper: User, variant: ProductVariant
) -> None:
    """A variant that exists but cannot be sold is a stale page, not a typo, and the two deserve
    different answers."""
    variant.is_active = False
    variant.save(update_fields=["is_active"])

    response = add(shopper, variant)

    assert response.status_code == 409
    assert "no longer available" in response.json()["error"]["message"]


def test_a_variant_whose_product_is_withdrawn_is_also_refused(
    shopper: User, variant: ProductVariant
) -> None:
    variant.product.is_active = False
    variant.product.save(update_fields=["is_active"])

    assert add(shopper, variant).status_code == 409


# --- updating (`US-3.2`) --------------------------------------------------------------------


def test_setting_a_quantity_updates_the_totals(shopper: User, variant: ProductVariant) -> None:
    created = add(shopper, variant)

    response = set_quantity(shopper, line_id(created), 3)

    assert response.status_code == 200
    assert response.json()["item_count"] == 3
    assert response.json()["subtotal"] == {"amount_cents": 3 * UNIT_PRICE, "currency": "USD"}
    assert response.json()["items"][0]["line_total"] == {
        "amount_cents": 3 * UNIT_PRICE,
        "currency": "USD",
    }
    assert CartItem.objects.get().quantity == 3


def test_setting_a_quantity_above_stock_is_refused_and_changes_nothing(
    shopper: User, variant: ProductVariant
) -> None:
    created = add(shopper, variant)

    response = set_quantity(shopper, line_id(created), STOCK + 1)

    assert response.status_code == 409
    assert CartItem.objects.get().quantity == 1


def test_setting_a_quantity_to_zero_is_a_validation_error(
    shopper: User, variant: ProductVariant
) -> None:
    """Zero is not a quantity: removal has its own endpoint (`US-3.3`)."""
    created = add(shopper, variant)

    response = set_quantity(shopper, line_id(created), 0)

    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert error["details"][0]["field"] == "body.quantity"
    assert CartItem.objects.get().quantity == 1


def test_setting_the_quantity_of_an_unknown_line_is_a_404(shopper: User) -> None:
    assert set_quantity(shopper, 987654, 1).status_code == 404


# --- removing (`US-3.3`) --------------------------------------------------------------------


def test_removing_a_line_returns_the_cart_without_it(
    shopper: User, variant: ProductVariant
) -> None:
    created = add(shopper, variant)

    response = remove(shopper, line_id(created))

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["item_count"] == 0
    assert response.json()["subtotal"] == {"amount_cents": 0, "currency": "USD"}
    assert CartItem.objects.count() == 0
    # The cart itself survives, and so does the shopper's access to it.
    assert Cart.objects.filter(user=shopper, status=CartStatus.ACTIVE).exists()


def test_removing_a_line_from_a_cart_that_does_not_exist_is_a_404(shopper: User) -> None:
    assert remove(shopper, 1).status_code == 404


# --- ownership ------------------------------------------------------------------------------


def test_another_accounts_line_is_not_found(
    shopper: User, other_shopper: User, variant: ProductVariant
) -> None:
    """The owner is part of the query, so a line that is not yours is a `404` — not a `403`, which
    would confirm the id exists (`QA-C31`)."""
    theirs = line_id(add(other_shopper, variant))

    assert set_quantity(shopper, theirs, 2).status_code == 404
    assert remove(shopper, theirs).status_code == 404
    assert CartItem.objects.get().quantity == 1


def test_each_account_has_its_own_cart(
    shopper: User, other_shopper: User, variant: ProductVariant
) -> None:
    mine = add(shopper, variant, quantity=1).json()
    theirs = add(other_shopper, variant, quantity=STOCK).json()

    assert mine["id"] != theirs["id"]
    assert mine["item_count"] == 1
    assert theirs["item_count"] == STOCK
    assert client.get("/api/v1/cart", headers=auth(shopper)).json()["item_count"] == 1
    assert client.get("/api/v1/cart", headers=auth(other_shopper)).json()["item_count"] == STOCK


# --- concurrency ----------------------------------------------------------------------------


@pytest.mark.django_db(transaction=True)
@pytest.mark.skipif(
    connection.vendor != "postgresql",
    reason="SQLite ignores `SELECT … FOR UPDATE`, so it cannot show what the lock is for.",
)
def test_two_concurrent_adds_do_not_lose_an_increment(
    shopper: User, variant: ProductVariant
) -> None:
    """What the row lock in `_started_cart` is for.

    Without it, both requests read the same quantity and one increment is written over the other, so
    the cart holds one instead of two. Two real connections are required, which is why this test
    commits (`transaction=True`) instead of running inside the usual wrapping transaction: a wrapped
    test hides exactly what is being asserted, because the second connection could not see the first
    one's rows at all.

    A run in which the threads happen not to overlap passes as well. The assertion is that the
    locked path cannot lose an increment, not that a race was observed.
    """
    header = auth(shopper)
    outcome: list[int] = []

    def add_once() -> None:
        try:
            response = Client().post(
                "/api/v1/cart/items",
                data=json.dumps({"variant_id": variant.pk, "quantity": 1}),
                content_type="application/json",
                headers=header,
            )
            outcome.append(response.status_code)
        finally:
            # Each thread gets its own connection, and a thread that leaves one open keeps the test
            # database busy — pytest then cannot drop it at teardown and reports an `OperationalError`
            # instead of a clean run.
            connections.close_all()

    threads = [threading.Thread(target=add_once) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    assert sorted(outcome) == [200, 200]
    assert CartItem.objects.get().quantity == 2
