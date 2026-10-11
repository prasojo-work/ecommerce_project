"""Contract tests for the address book (`API.md` section 8, `SCOPE.md` `US-2.5`).

The ownership cases are the reason this file exists. `QA-C31` is broken object-level authorization,
and these are what stop it: another account's address has to be unreachable through every endpoint
that takes an id, and has to still be there afterwards.

`US-2.5` also implies a default, and the endpoints hold a stronger rule than the database does —
*exactly one* default for as long as the account has any address, rather than merely *at most one*.
Create, update and delete are each tested against it, including deleting the default itself.

Tokens come from `issue_tokens` rather than a real sign-in: the address book does not care how the
token was obtained, and this keeps the file off the rate-limited `/auth` endpoints, which have their
own tests.
"""

import json
from collections.abc import Iterator
from typing import Any

import pytest
from django.core.cache import cache
from django.test import Client

from accounts.models import Address, User
from accounts.tokens import issue_tokens

pytestmark = pytest.mark.django_db

PASSWORD = "correct-horse-9!"

ADDRESS: dict[str, str] = {
    "label": "Home",
    "recipient": "Ada Lovelace",
    "line1": "12 Analytical Way",
    "city": "London",
    "postal_code": "N1 9AB",
    "country": "GB",
}


@pytest.fixture(autouse=True)
def clear_throttle_windows() -> Iterator[None]:
    """The address endpoints are authenticated and therefore rate-limited, and the window lives in
    the process cache, which pytest does not reset between tests — the same fixture as
    `test_accounts_api.py`, for the same reason."""
    cache.clear()
    yield
    cache.clear()


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def signed_in(email: str) -> tuple[Client, User, str]:
    """A fresh client, the account it acts as, and that account's access token."""
    user = User.objects.create_user(
        email=email, password=PASSWORD, display_name=email.split("@")[0]
    )
    return Client(), user, issue_tokens(user).access_token


def list_addresses(client: Client, token: str) -> Any:
    return client.get("/api/v1/addresses", headers=headers(token))


def create_address(client: Client, token: str, **overrides: Any) -> Any:
    return client.post(
        "/api/v1/addresses",
        data=json.dumps({**ADDRESS, **overrides}),
        content_type="application/json",
        headers=headers(token),
    )


def update_address(client: Client, token: str, address_id: int, **changes: Any) -> Any:
    return client.patch(
        f"/api/v1/addresses/{address_id}",
        data=json.dumps(changes),
        content_type="application/json",
        headers=headers(token),
    )


def delete_address(client: Client, token: str, address_id: int) -> Any:
    return client.delete(f"/api/v1/addresses/{address_id}", headers=headers(token))


def defaults_of(user: User) -> int:
    return Address.objects.filter(user=user, is_default=True).count()


# --- authentication -------------------------------------------------------------------------


def test_the_address_book_needs_a_token() -> None:
    client = Client()

    assert client.get("/api/v1/addresses").status_code == 401
    assert (
        client.post(
            "/api/v1/addresses", data=json.dumps(ADDRESS), content_type="application/json"
        ).status_code
        == 401
    )
    assert (
        client.patch(
            "/api/v1/addresses/1", data=json.dumps({}), content_type="application/json"
        ).status_code
        == 401
    )
    assert client.delete("/api/v1/addresses/1").status_code == 401


# --- creating (`US-2.5`) --------------------------------------------------------------------


def test_create_returns_the_stored_address() -> None:
    client, _, token = signed_in("ada@example.com")

    response = create_address(client, token)

    assert response.status_code == 201
    body = response.json()
    assert body["label"] == "Home"
    assert body["recipient"] == "Ada Lovelace"
    assert body["line1"] == "12 Analytical Way"
    assert body["city"] == "London"
    assert body["postal_code"] == "N1 9AB"
    assert body["country"] == "GB"
    # Optional in the model, so absent from the request and defaulted rather than null.
    assert body["line2"] == ""
    assert body["region"] == ""
    assert body["phone"] == ""


def test_the_first_address_becomes_the_default() -> None:
    """Without this an account could have addresses and no default, which checkout would have to
    special-case for no benefit."""
    client, user, token = signed_in("ada@example.com")

    response = create_address(client, token)

    assert response.json()["is_default"] is True
    assert defaults_of(user) == 1


def test_a_requested_default_unsets_the_previous_one() -> None:
    client, user, token = signed_in("ada@example.com")
    first = create_address(client, token).json()["id"]

    second = create_address(client, token, label="Work", is_default=True).json()

    assert second["is_default"] is True
    assert Address.objects.get(pk=first).is_default is False
    assert defaults_of(user) == 1


def test_a_second_address_is_not_the_default_unless_asked() -> None:
    client, user, token = signed_in("ada@example.com")
    first = create_address(client, token).json()["id"]

    second = create_address(client, token, label="Work").json()

    assert second["is_default"] is False
    assert Address.objects.get(pk=first).is_default is True
    assert defaults_of(user) == 1


def test_the_default_rule_is_per_account() -> None:
    """`DATA-MODEL.md`'s partial unique index is per user, so two accounts can each have one."""
    ada_client, ada, ada_token = signed_in("ada@example.com")
    grace_client, grace, grace_token = signed_in("grace@example.com")

    create_address(ada_client, ada_token)
    create_address(grace_client, grace_token)

    assert defaults_of(ada) == 1
    assert defaults_of(grace) == 1


# --- listing --------------------------------------------------------------------------------


def test_the_list_returns_the_default_first() -> None:
    client, _, token = signed_in("ada@example.com")
    first = create_address(client, token).json()["id"]
    second = create_address(client, token, label="Work").json()["id"]

    assert [row["id"] for row in list_addresses(client, token).json()] == [first, second]

    update_address(client, token, second, is_default=True)

    assert [row["id"] for row in list_addresses(client, token).json()] == [second, first]


def test_an_empty_book_lists_nothing() -> None:
    client, _, token = signed_in("ada@example.com")

    assert list_addresses(client, token).json() == []


# --- updating -------------------------------------------------------------------------------


def test_update_changes_only_the_named_fields() -> None:
    client, _, token = signed_in("ada@example.com")
    address_id = create_address(client, token).json()["id"]

    response = update_address(client, token, address_id, city="Edinburgh", phone="+44 131 496 0000")

    assert response.status_code == 200
    body = response.json()
    assert body["city"] == "Edinburgh"
    assert body["phone"] == "+44 131 496 0000"
    assert body["recipient"] == "Ada Lovelace"
    assert body["label"] == "Home"


def test_promoting_an_address_moves_the_default() -> None:
    client, user, token = signed_in("ada@example.com")
    first = create_address(client, token).json()["id"]
    second = create_address(client, token, label="Work").json()["id"]

    response = update_address(client, token, second, is_default=True)

    assert response.json()["is_default"] is True
    assert Address.objects.get(pk=first).is_default is False
    assert Address.objects.get(pk=second).is_default is True
    assert defaults_of(user) == 1


def test_clearing_the_default_is_refused() -> None:
    """It would leave the account with addresses and no default, so it is a `409` — the body is
    fine and the state of the resource is what refuses it."""
    client, user, token = signed_in("ada@example.com")
    address_id = create_address(client, token).json()["id"]

    response = update_address(client, token, address_id, is_default=False)

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"
    assert Address.objects.get(pk=address_id).is_default is True
    assert defaults_of(user) == 1


# --- deleting -------------------------------------------------------------------------------


def test_delete_removes_the_address() -> None:
    client, _, token = signed_in("ada@example.com")
    address_id = create_address(client, token).json()["id"]

    response = delete_address(client, token, address_id)

    assert response.status_code == 204
    assert Address.objects.filter(pk=address_id).exists() is False
    assert list_addresses(client, token).json() == []


def test_deleting_the_default_promotes_the_oldest_survivor() -> None:
    client, user, token = signed_in("ada@example.com")
    first = create_address(client, token).json()["id"]
    second = create_address(client, token, label="Work").json()["id"]
    third = create_address(client, token, label="Studio").json()["id"]

    delete_address(client, token, first)

    assert Address.objects.get(pk=second).is_default is True
    assert Address.objects.get(pk=third).is_default is False
    assert defaults_of(user) == 1


def test_deleting_a_non_default_leaves_the_default_alone() -> None:
    client, user, token = signed_in("ada@example.com")
    first = create_address(client, token).json()["id"]
    second = create_address(client, token, label="Work").json()["id"]

    delete_address(client, token, second)

    assert Address.objects.get(pk=first).is_default is True
    assert defaults_of(user) == 1


def test_deleting_a_missing_address_is_a_404() -> None:
    client, _, token = signed_in("ada@example.com")

    response = delete_address(client, token, 4321)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


# --- ownership (`QA-C31`) -------------------------------------------------------------------


def test_another_accounts_address_is_not_listed() -> None:
    ada_client, _, ada_token = signed_in("ada@example.com")
    grace_client, _, grace_token = signed_in("grace@example.com")
    create_address(ada_client, ada_token, recipient="Ada Lovelace")

    body = list_addresses(grace_client, grace_token).json()

    assert body == []


def test_updating_another_accounts_address_is_a_404() -> None:
    ada_client, _, ada_token = signed_in("ada@example.com")
    grace_client, _, grace_token = signed_in("grace@example.com")
    address_id = create_address(ada_client, ada_token).json()["id"]

    response = update_address(grace_client, grace_token, address_id, recipient="Grace Hopper")

    assert response.status_code == 404
    # `404` and not `403` on purpose: `403` would confirm that the id exists.
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_deleting_another_accounts_address_is_a_404() -> None:
    ada_client, _, ada_token = signed_in("ada@example.com")
    grace_client, _, grace_token = signed_in("grace@example.com")
    address_id = create_address(ada_client, ada_token).json()["id"]

    response = delete_address(grace_client, grace_token, address_id)

    assert response.status_code == 404
    assert Address.objects.filter(pk=address_id).exists() is True


def test_an_attempt_on_another_accounts_address_changes_nothing() -> None:
    """A refused request must leave the row exactly as it was, not partly applied."""
    ada_client, _, ada_token = signed_in("ada@example.com")
    grace_client, _, grace_token = signed_in("grace@example.com")
    address_id = create_address(ada_client, ada_token).json()["id"]

    update_address(grace_client, grace_token, address_id, recipient="Grace Hopper", city="Paris")

    stored = Address.objects.get(pk=address_id)
    assert stored.recipient == "Ada Lovelace"
    assert stored.city == "London"


# --- validation -----------------------------------------------------------------------------


def test_a_missing_required_field_names_that_field() -> None:
    client, _, token = signed_in("ada@example.com")
    payload = {key: value for key, value in ADDRESS.items() if key != "recipient"}

    response = client.post(
        "/api/v1/addresses",
        data=json.dumps(payload),
        content_type="application/json",
        headers=headers(token),
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["details"][0]["field"] == "body.recipient"


def test_a_blank_required_field_is_refused() -> None:
    """The model declares these non-blank; nothing in the database refuses the empty string."""
    client, _, token = signed_in("ada@example.com")

    response = create_address(client, token, city="")

    assert response.status_code == 400
    assert response.json()["error"]["details"][0]["field"] == "body.city"


def test_an_over_long_field_is_refused_before_the_database() -> None:
    """`M1.2` found that SQLite does not enforce `max_length`, so the schema has to."""
    client, _, token = signed_in("ada@example.com")

    response = create_address(client, token, recipient="x" * 121)

    assert response.status_code == 400
    assert response.json()["error"]["details"][0]["field"] == "body.recipient"


def test_a_country_that_is_not_two_letters_is_refused() -> None:
    client, _, token = signed_in("ada@example.com")

    response = create_address(client, token, country="GBR")

    assert response.status_code == 400
    assert response.json()["error"]["details"][0]["field"] == "body.country"


def test_an_update_cannot_blank_a_required_field() -> None:
    client, _, token = signed_in("ada@example.com")
    address_id = create_address(client, token).json()["id"]

    response = update_address(client, token, address_id, line1="")

    assert response.status_code == 400
    assert Address.objects.get(pk=address_id).line1 == "12 Analytical Way"
