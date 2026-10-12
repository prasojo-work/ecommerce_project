"""The cart's database rules (`DATA-MODEL.md` section 2 and section 4).

Every rule here is a constraint rather than a convention, so each is asserted by trying to break it.
A partial unique index is only worth having if a second active cart really cannot exist when
application code asks for one, and a `PROTECT` is only worth choosing if withdrawing a variant from
the catalog really is refused while carts hold it.
"""

import pytest
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from accounts.models import User
from cart.models import Cart, CartItem, CartStatus
from catalog.models import Category, Product, ProductVariant

pytestmark = pytest.mark.django_db


@pytest.fixture
def user() -> User:
    return User.objects.create_user(
        email="ada@example.com", password="correct-horse-battery-staple"
    )


@pytest.fixture
def variant() -> ProductVariant:
    category = Category.objects.create(name="Seating", slug="seating")
    product = Product.objects.create(
        category=category, name="Aalto Chair", slug="aalto-chair", base_price_cents=12900
    )
    return ProductVariant.objects.create(
        product=product, sku="AAL-OAK", name="Oak", price_cents=12900, stock_qty=3
    )


def test_a_shopper_cannot_have_two_active_carts(user: User) -> None:
    Cart.objects.create(user=user)

    with pytest.raises(IntegrityError), transaction.atomic():
        Cart.objects.create(user=user)


def test_a_converted_cart_does_not_block_a_new_active_one(user: User) -> None:
    """The index is partial for this reason: checkout leaves a `converted` cart behind, and the
    shopper must still be able to fill a new one."""
    converted = Cart.objects.create(user=user, status=CartStatus.CONVERTED)

    fresh = Cart.objects.create(user=user)

    assert fresh.pk != converted.pk
    assert Cart.objects.filter(user=user, status=CartStatus.ACTIVE).count() == 1


def test_two_active_carts_for_different_shoppers_are_fine(
    user: User, variant: ProductVariant
) -> None:
    other = User.objects.create_user(email="grace@example.com", password="correct-horse-battery")

    assert Cart.objects.create(user=user).pk != Cart.objects.create(user=other).pk


def test_a_variant_appears_once_per_cart(user: User, variant: ProductVariant) -> None:
    cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=cart, variant=variant, quantity=1)

    with pytest.raises(IntegrityError), transaction.atomic():
        CartItem.objects.create(cart=cart, variant=variant, quantity=1)


def test_a_quantity_below_one_is_refused(user: User, variant: ProductVariant) -> None:
    """`DATA-MODEL.md` section 4's `quantity >= 1`, which is why removal has an endpoint rather than
    a quantity of zero."""
    cart = Cart.objects.create(user=user)

    with pytest.raises(IntegrityError), transaction.atomic():
        CartItem.objects.create(cart=cart, variant=variant, quantity=0)


def test_deleting_a_cart_takes_its_lines_with_it(user: User, variant: ProductVariant) -> None:
    cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=cart, variant=variant, quantity=1)

    cart.delete()

    assert CartItem.objects.count() == 0


def test_a_variant_in_a_cart_cannot_be_deleted(user: User, variant: ProductVariant) -> None:
    """`PROTECT` rather than `CASCADE`: withdrawing a variant must not silently empty the carts
    holding it, so it has to be a decision."""
    cart = Cart.objects.create(user=user)
    CartItem.objects.create(cart=cart, variant=variant, quantity=1)

    with pytest.raises(ProtectedError):
        variant.delete()

    assert CartItem.objects.count() == 1


def test_the_models_read_sensibly(user: User, variant: ProductVariant) -> None:
    cart = Cart.objects.create(user=user)
    line = CartItem.objects.create(cart=cart, variant=variant, quantity=2)

    assert str(cart) == f"Cart {cart.pk} (active)"
    assert str(line) == f"2 on cart {cart.pk}"
