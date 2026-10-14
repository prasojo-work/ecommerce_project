"""The operator console (`M5.1`, `ADR-0007`, `US-5.1`-`US-5.5`).

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

The orders half (`M5.1b`) is the opposite kind of page. The catalog is a form an operator fills in; an
order is a receipt nobody edits, so `US-5.4`'s details and `US-5.5`'s audit are read-only and the way
an order moves is an action — one per reachable status — that calls the same `transition_order` the
API does. What is tested there is that the console cannot be used to assign a status at all: no
editable field on the form, and a hand-written POST carrying one changes nothing.
"""

import json
from collections.abc import Iterator

import pytest
from django.conf import settings
from django.contrib import admin
from django.core.cache import cache
from django.core.management import call_command
from django.db.models import QuerySet
from django.http import HttpResponse
from django.test import Client, RequestFactory

from accounts.models import User
from catalog.admin import LOW_STOCK_THRESHOLD, ProductVariantAdmin
from catalog.models import Category, Product, ProductVariant
from orders.admin import OrderAdmin
from orders.models import Order, OrderEvent, OrderItem, OrderStatus
from orders.services import transition_order
from orders.shipping import DEFAULT_METHOD_CODE, SHIPPING_METHODS

pytestmark = pytest.mark.django_db

PASSWORD = "correct-horse-9!"
UNIT_PRICE = 12900
STANDARD_SHIPPING_CENTS = next(
    method.price_cents for method in SHIPPING_METHODS if method.code == DEFAULT_METHOD_CODE
)


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


def make_order(variant: ProductVariant, *, quantity: int = 2) -> Order:
    """An order the way checkout leaves one: priced lines, and its own first event.

    Built here rather than through `POST /orders` because what is under test is the console, not the
    checkout path — and an order that did not start where a new one starts would make every
    transition assertion say the wrong thing.
    """
    subtotal_cents = variant.price_cents * quantity
    order = Order.objects.create(
        email="ada@example.com",
        subtotal_cents=subtotal_cents,
        shipping_cents=STANDARD_SHIPPING_CENTS,
        total_cents=subtotal_cents + STANDARD_SHIPPING_CENTS,
        shipping_recipient="Ada Lovelace",
        shipping_line1="12 Analytical Way",
        shipping_city="London",
        shipping_postal_code="EC1A 1BB",
        shipping_country="GB",
    )
    OrderItem.objects.create(
        order=order,
        variant=variant,
        product_name=variant.product.name,
        variant_name=variant.name,
        unit_price_cents=variant.price_cents,
        quantity=quantity,
        line_total_cents=subtotal_cents,
    )
    # The one event with no previous state, and no actor: checkout did this, not a person.
    OrderEvent.objects.create(order=order, to_status=OrderStatus.PENDING, note="Order placed.")
    return order


def timeline(order: Order) -> QuerySet[OrderEvent]:
    """The order's events, read from this side because `django-stubs` does not know the reverse
    accessor (`Order.events`) that the model does have."""
    return OrderEvent.objects.filter(order=order)


def readonly_inline_data(*prefixes: str) -> dict[str, str]:
    """The management form each read-only inline still needs, with no rows filled in.

    Django validates a formset before it will accept a change form, so a POST that omits these is
    redisplayed with an error and proves nothing about what the console would have saved. Zero rows
    is what "the console shows these and does not edit them" submits.
    """
    data: dict[str, str] = {}
    for prefix in prefixes:
        data[f"{prefix}-TOTAL_FORMS"] = "0"
        data[f"{prefix}-INITIAL_FORMS"] = "0"
        data[f"{prefix}-MIN_NUM_FORMS"] = "0"
        data[f"{prefix}-MAX_NUM_FORMS"] = "1000"
    return data


def run_action(client: Client, action: str, *orders: Order) -> HttpResponse:
    """Post an action against a selection, the way the changelist's dropdown does.

    Followed through: the changelist answers a POST with a redirect, so the report an operator reads
    — "Moved: …" and the orders left alone — is rendered by the page it lands on, and this is the
    response that carries it.
    """
    response = client.post(
        "/admin/orders/order/",
        {"action": action, "_selected_action": [str(order.pk) for order in orders]},
        follow=True,
    )
    assert isinstance(response, HttpResponse)
    return response


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
        "/admin/orders/order/",
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


def test_the_order_page_shows_the_lines_and_the_timeline(operator_client: Client) -> None:
    # `US-5.4` asks to "see orders and their details" and `US-5.5` to have the change audited; both
    # are read-only inlines here, and this is the page saying the operator can see what was bought
    # and how the order has moved.
    order = make_order(make_variant("AAL-OAK", 5))

    response = operator_client.get(f"/admin/orders/order/{order.pk}/change/")

    assert response.status_code == 200
    content = response.content.decode()
    assert "Aalto Chair" in content
    assert "Order placed." in content


def test_the_order_form_offers_no_way_to_assign_the_status(operator: User) -> None:
    # `US-5.5`'s "valid transitions only" holds exactly as long as `status` cannot be typed in. The
    # day someone adds it to a fieldset without `readonly_fields`, `ALLOWED_TRANSITIONS` has an
    # end-run around it — so the assertion is that no field on this form is editable at all.
    model_admin = OrderAdmin(Order, admin.site)
    request = RequestFactory().get("/admin/orders/order/")
    request.user = operator
    order = make_order(make_variant("AAL-OAK", 5))

    assert "status" in model_admin.get_readonly_fields(request, order)
    assert model_admin.get_form(request, order).base_fields == {}


def test_a_hand_written_post_cannot_move_the_status(operator_client: Client) -> None:
    # The end-run, attempted over HTTP: the console renders no `status` input, so a POST ships one
    # anyway. It is not a form field, so nothing reads it, and the order is where it was.
    order = make_order(make_variant("AAL-OAK", 5))

    response = operator_client.post(
        f"/admin/orders/order/{order.pk}/change/",
        {"status": OrderStatus.DELIVERED, **readonly_inline_data("items", "events")},
    )

    order.refresh_from_db()
    assert response.status_code == 302
    assert order.status == OrderStatus.PENDING
    assert timeline(order).count() == 1


def test_the_change_page_offers_no_save_button(operator_client: Client) -> None:
    # Every field is read-only, so Django's Save would be a control that appears to write and
    # cannot. The submit row reads as Close instead — the page saying movements are the actions.
    order = make_order(make_variant("AAL-OAK", 5))

    content = operator_client.get(f"/admin/orders/order/{order.pk}/change/").content.decode()

    assert 'name="_save"' not in content
    assert 'name="_continue"' not in content


def test_the_console_neither_adds_nor_removes_orders(operator_client: Client) -> None:
    # An order is what checkout writes, and a receipt is not a thing to remove — cancelling is how an
    # order is undone, and that is recorded. Both doors are shut rather than merely missing from a
    # template, so neither the operator nor a hand-written URL gets through.
    order = make_order(make_variant("AAL-OAK", 5))

    assert operator_client.get("/admin/orders/order/add/").status_code == 403
    assert operator_client.get(f"/admin/orders/order/{order.pk}/delete/").status_code == 403


def test_marking_an_order_paid_moves_it_and_records_the_operator(
    operator_client: Client, operator: User
) -> None:
    # `US-5.5`: the move is written down, with who made it. An action that assigned `status` itself
    # would leave the trail one line short and the assignment invisible.
    order = make_order(make_variant("AAL-OAK", 5))

    response = run_action(operator_client, "mark_paid", order)

    assert response.status_code == 200
    order.refresh_from_db()
    assert order.status == OrderStatus.PAID
    event = timeline(order).order_by("-id").first()
    assert event is not None
    assert (event.from_status, event.to_status) == (OrderStatus.PENDING, OrderStatus.PAID)
    assert event.actor == operator


def test_an_illegal_move_is_refused_and_records_nothing(operator_client: Client) -> None:
    # `US-5.5`'s "valid transitions only": `pending` cannot become `shipped` (`DATA-MODEL.md` §3),
    # and the console is not a way around that — the order is left where it was and no event claims
    # otherwise. Writing the event anyway would be worse than refusing.
    order = make_order(make_variant("AAL-OAK", 5))

    response = run_action(operator_client, "mark_shipped", order)

    order.refresh_from_db()
    assert order.status == OrderStatus.PENDING
    assert timeline(order).count() == 1
    assert "cannot become" in response.content.decode()


def test_a_selection_moves_what_it_can_and_leaves_the_rest(operator_client: Client) -> None:
    # A selection is not all or nothing. Two ticks where one order has already moved should land the
    # one that can move and say so about the other, not fail the pair.
    pending = make_order(make_variant("AAL-OAK", 5))
    already = make_order(make_variant("AAL-WALNUT", 5))
    transition_order(already, OrderStatus.PAID)

    response = run_action(operator_client, "mark_paid", pending, already)

    pending.refresh_from_db()
    already.refresh_from_db()
    assert pending.status == OrderStatus.PAID
    assert already.status == OrderStatus.PAID
    # Still two: the second order was not moved twice, and the audit says so.
    assert timeline(already).count() == 2
    assert "Left alone" in response.content.decode()


def test_cancelling_returns_the_stock_the_order_reserved(
    operator_client: Client, operator: User
) -> None:
    # `ADR-0017`: creation took the stock, so cancelling has to put it back or a cancellation quietly
    # shrinks the shop's sellable quantity forever. The console cancels through `cancel_order`, which
    # is the one place that knows a cancellation is also a stock event.
    variant = make_variant("AAL-OAK", 5)
    order = make_order(variant, quantity=2)
    # The reservation checkout made, applied here because the fixture builds the order directly.
    ProductVariant.objects.filter(pk=variant.pk).update(stock_qty=3)

    run_action(operator_client, "cancel_orders", order)

    variant.refresh_from_db()
    order.refresh_from_db()
    assert order.status == OrderStatus.CANCELLED
    assert variant.stock_qty == 5
    event = timeline(order).order_by("-id").first()
    assert event is not None
    assert event.to_status == OrderStatus.CANCELLED
    assert event.actor == operator


# --- the console's sign-in is rate-limited (`M6.3`, `SEC-FIND-1.7`) ------------------------

ADMIN_LOGIN = "/admin/login/"


@pytest.fixture(autouse=True)
def clear_throttle_windows() -> Iterator[None]:
    """The window lives in the process cache, which outlives a test and is shared by every client —
    the same fixture, and the same reason, as the one in `test_accounts_api.py`."""
    cache.clear()
    yield
    cache.clear()


def admin_login_attempts_per_window() -> int:
    """The configured limit, read from settings so the test cannot drift away from the policy."""
    return int(str(settings.NINJA_DEFAULT_THROTTLE_RATES["admin-login"]).split("/")[0])


def failed_sign_in(client: Client, username: str = "operator") -> int:
    """POST the console's sign-in form with the wrong password, and report the status."""
    return client.post(ADMIN_LOGIN, {"username": username, "password": "wrong"}).status_code


def test_the_console_sign_in_is_rate_limited(client: Client) -> None:
    """`SEC-FIND-1.7`: the console is the highest-value target here, and its sign-in had no limit.

    Ninja's throttles are attached to Ninja operations, and `/admin/login/` is a plain Django view —
    so the one screen where a guessed password buys the entire catalog and every order was the only
    one in the project outside every rate limit. The refusal also has to say when to come back: a bare
    `429` leaves a client guessing, and guessing wrong makes the block longer.
    """
    allowed = admin_login_attempts_per_window()

    for _ in range(allowed):
        assert failed_sign_in(client) == 200

    refused = client.post(ADMIN_LOGIN, {"username": "operator", "password": "wrong"})

    assert refused.status_code == 429
    assert int(refused["Retry-After"]) >= 1


def test_viewing_the_sign_in_form_is_not_counted(client: Client) -> None:
    """A `GET` is somebody looking at a form. Counting it would spend an operator's budget on a
    browser refresh and turn the back button into a lockout."""
    for _ in range(admin_login_attempts_per_window() * 2):
        assert client.get(ADMIN_LOGIN).status_code == 200

    assert failed_sign_in(client) == 200


def test_the_limit_counts_the_client_and_not_the_username(client: Client) -> None:
    """Changing the name in the form must not buy a fresh window.

    Keyed on the submitted username, this would be a way to lock a known operator out of the console
    rather than a way to slow an attacker down — the same argument `accounts/throttling.py` makes for
    the auth endpoints, and it has to hold here too or the limit is a liability.
    """
    allowed = admin_login_attempts_per_window()

    for attempt in range(allowed):
        assert failed_sign_in(client, username=f"nobody-{attempt}") == 200

    assert failed_sign_in(client, username="a-name-never-tried") == 429
