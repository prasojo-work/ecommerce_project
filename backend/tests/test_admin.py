"""The operator console (`M5.1`, `ADR-0007`, `US-5.1`-`US-5.3`).

Django admin is the v1 console, and almost everything it needs is *configuration* — which is exactly
what breaks silently. Three promises are tested here. **It loads**: a model registered against fields
it does not have is a hard `admin.E108` system-check error, and the swappable user model is the one
that would produce it, so a `check` runs inside a test. **It is gated**: `is_staff` is the operator
flag (`ADR-0007`), and an anonymous visitor and a signed-in *customer* are both turned away. **It is
usable** — the part `ADR-0007` actually asks for: every table opens, a category and an operator are
created through its forms, and `US-5.3`'s low-stock indicator selects and names the right rows.

The final test guards the **API**, not the admin. Installing the console put `CsrfViewMiddleware` in
front of every request; `django-ninja` exempts each operation at the view, and this is what says the
API did not notice.
"""

import json

import pytest
from django.contrib import admin
from django.core.management import call_command
from django.test import Client

from accounts.models import User
from catalog.admin import LOW_STOCK_THRESHOLD, ProductVariantAdmin
from catalog.models import Category, Product, ProductVariant

pytestmark = pytest.mark.django_db

PASSWORD = "correct-horse-9!"
UNIT_PRICE = 12900


@pytest.fixture
def operator() -> User:
    """An operator, made the way `M5.2`'s runbook entry makes one.

    `is_staff` is what `ADR-0007` names as the gate, and it is what opens the console — but Django
    separates *reaching* the admin from *changing* what is in it, and the model permissions live on
    `is_superuser` or on explicit grants. `createsuperuser` sets both, so that is the operator these
    tests use; the `customer` below is the contrast that proves authentication is not the gate.
    """
    return User.objects.create_superuser(email="ops@example.com", password=PASSWORD)


@pytest.fixture
def customer() -> User:
    return User.objects.create_user(email="ada@example.com", password=PASSWORD)


@pytest.fixture
def operator_client(operator: User) -> Client:
    client = Client()
    client.force_login(operator)
    return client


def make_variant(sku: str, stock_qty: int) -> ProductVariant:
    """A variant on a shared product, so a test can lay out several stock levels in one line each."""
    category, _ = Category.objects.get_or_create(slug="seating", defaults={"name": "Seating"})
    product, _ = Product.objects.get_or_create(
        slug="aalto-chair",
        defaults={"category": category, "name": "Aalto Chair", "base_price_cents": UNIT_PRICE},
    )
    return ProductVariant.objects.create(
        product=product, sku=sku, name="Oak", price_cents=UNIT_PRICE, stock_qty=stock_qty
    )


def test_the_admin_passes_djangos_system_checks() -> None:
    # `admin.E108` — a list column naming a field the model does not have — is what a mis-registered
    # model produces, and the custom user model, with no `username`, is the one here that would.
    # `call_command` raises `SystemCheckError` on any error, so reaching the next line is the
    # assertion.
    call_command("check", verbosity=0)


def test_the_admin_turns_an_anonymous_visitor_away(client: Client) -> None:
    response = client.get("/admin/")

    assert response.status_code == 302
    assert "/admin/login/" in response["Location"]


def test_the_admin_turns_a_signed_in_customer_away(customer: User) -> None:
    # Authentication is not authorisation: a shopper with a valid session is still not an operator.
    client = Client()
    client.force_login(customer)

    assert client.get("/admin/").status_code == 302


def test_an_operator_reaches_the_console(operator_client: Client) -> None:
    assert operator_client.get("/admin/").status_code == 200


@pytest.mark.parametrize(
    "path",
    [
        "/admin/accounts/user/",
        "/admin/catalog/category/",
        "/admin/catalog/product/",
        "/admin/catalog/productvariant/",
        "/admin/catalog/imagecredit/",
    ],
)
def test_every_registered_table_opens(operator_client: Client, path: str) -> None:
    assert operator_client.get(path).status_code == 200


def test_a_category_can_be_created_in_the_admin(operator_client: Client) -> None:
    response = operator_client.post(
        "/admin/catalog/category/add/",
        {"name": "Seating", "slug": "seating", "description": "", "position": "0", "parent": ""},
    )

    assert response.status_code == 302
    assert Category.objects.filter(slug="seating").exists()


def test_the_admin_refuses_a_duplicate_category_slug(operator_client: Client) -> None:
    # `US-5.1`: "slug is unique". The rule is the model's, and the console is where an operator meets
    # it — as a form redisplayed with an error rather than a second row.
    Category.objects.create(name="Seating", slug="seating")

    response = operator_client.post(
        "/admin/catalog/category/add/",
        {
            "name": "Seating again",
            "slug": "seating",
            "description": "",
            "position": "0",
            "parent": "",
        },
    )

    assert response.status_code == 200
    assert Category.objects.filter(slug="seating").count() == 1


def test_an_operator_added_in_the_admin_gets_a_hashed_password(operator_client: Client) -> None:
    response = operator_client.post(
        "/admin/accounts/user/add/",
        {
            "email": "new-ops@example.com",
            "display_name": "New Ops",
            "password1": PASSWORD,
            "password2": PASSWORD,
        },
    )

    assert response.status_code == 302
    created = User.objects.get(email="new-ops@example.com")
    assert created.password != PASSWORD
    assert created.check_password(PASSWORD)


def test_the_stock_column_names_the_state_in_words() -> None:
    # `NFR-2`: state is never carried by colour alone, so the column says the word the filter means.
    model_admin = ProductVariantAdmin(ProductVariant, admin.site)

    assert model_admin.stock_state(make_variant("OUT", 0)) == "Out of stock"
    assert model_admin.stock_state(make_variant("LOW", LOW_STOCK_THRESHOLD)) == "Low"
    assert model_admin.stock_state(make_variant("FINE", LOW_STOCK_THRESHOLD + 1)) == "In stock"


def test_the_low_stock_filter_finds_variants_at_or_below_the_threshold(
    operator_client: Client,
) -> None:
    make_variant("OUT", 0)
    make_variant("LOW", LOW_STOCK_THRESHOLD)
    make_variant("FINE", LOW_STOCK_THRESHOLD + 1)

    response = operator_client.get("/admin/catalog/productvariant/", {"stock": "low"})

    assert response.status_code == 200
    assert {variant.sku for variant in response.context["cl"].result_list} == {"OUT", "LOW"}


def test_the_stock_filter_can_single_out_the_empty_ones(operator_client: Client) -> None:
    make_variant("OUT", 0)
    make_variant("LOW", LOW_STOCK_THRESHOLD)
    make_variant("FINE", LOW_STOCK_THRESHOLD + 1)

    response = operator_client.get("/admin/catalog/productvariant/", {"stock": "out"})

    assert {variant.sku for variant in response.context["cl"].result_list} == {"OUT"}


def test_installing_the_admin_did_not_put_csrf_in_front_of_the_api() -> None:
    # The client is the one that *enforces* CSRF, so a `201` with no token is the proof that
    # `CsrfViewMiddleware` left the API alone — which it must, because `django-ninja` exempts every
    # operation at the view and the console is the only thing that wanted the middleware.
    strict_client = Client(enforce_csrf_checks=True)

    response = strict_client.post(
        "/api/v1/auth/register",
        data=json.dumps(
            {"email": "csrf@example.com", "password": PASSWORD, "display_name": "Strict"}
        ),
        content_type="application/json",
    )

    assert response.status_code == 201
