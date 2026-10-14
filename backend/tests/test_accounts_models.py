"""Model tests for the `accounts` app (`DATA-MODEL.md` section 2, `SCOPE.md` `US-2.1`-`US-2.5`).

The user model is the one thing in this project that cannot be swapped cheaply later, so the first
test here asserts the swap itself rather than a behaviour.
"""

from uuid import uuid4

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from accounts.models import Address, RefreshToken, User

pytestmark = pytest.mark.django_db


@pytest.fixture
def user() -> User:
    return User.objects.create_user(email="ada@example.com", password="correct-horse-9")


@pytest.fixture
def address(user: User) -> Address:
    return Address.objects.create(
        user=user,
        label="Home",
        recipient="Ada Lovelace",
        line1="12 Marylebone Road",
        city="London",
        postal_code="NW1 5LS",
        country="GB",
    )


def test_the_configured_user_model_is_the_accounts_one() -> None:
    assert settings.AUTH_USER_MODEL == "accounts.User"
    assert get_user_model() is User


def test_creating_a_user_hashes_the_password(user: User) -> None:
    assert user.password != "correct-horse-9"
    assert user.password.startswith("pbkdf2_")
    assert user.check_password("correct-horse-9") is True
    assert user.check_password("something-else") is False


def test_the_email_is_lower_cased_on_the_way_in() -> None:
    created = User.objects.create_user(email="  Ada@Example.COM  ", password="correct-horse-9")

    assert created.email == "ada@example.com"


def test_sign_in_is_case_insensitive(user: User) -> None:
    """`authenticate()` resolves users through `get_by_natural_key`."""
    assert User.objects.get_by_natural_key("ADA@Example.com") == user


def test_email_must_be_unique(user: User) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user(email="ada@example.com", password="correct-horse-9")


def test_two_addresses_of_one_email_differing_only_in_case_collide() -> None:
    User.objects.create_user(email="ada@example.com", password="correct-horse-9")

    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user(email="Ada@Example.com", password="correct-horse-9")


def test_creating_a_user_without_an_email_raises() -> None:
    with pytest.raises(ValueError, match="email address is required"):
        User.objects.create_user(email="", password="correct-horse-9")


def test_an_invalid_email_fails_validation() -> None:
    with pytest.raises(ValidationError):
        User(email="not-an-email").full_clean()


def test_create_superuser_sets_the_operator_flags() -> None:
    root = User.objects.create_superuser(email="root@example.com", password="correct-horse-9")

    assert root.is_staff is True
    assert root.is_superuser is True


def test_create_superuser_refuses_to_clear_its_own_flags() -> None:
    with pytest.raises(ValueError, match="is_staff=True"):
        User.objects.create_superuser(
            email="root@example.com", password="correct-horse-9", is_staff=False
        )


def test_create_superuser_also_refuses_to_clear_is_superuser() -> None:
    """Both flags, not only the one checked first. `is_staff` opens the console and `is_superuser`
    is what grants anything inside it, so a caller that got the second one wrong would produce an
    operator who can sign in and then find nothing they are allowed to touch."""
    with pytest.raises(ValueError, match="is_superuser=True"):
        User.objects.create_superuser(
            email="root@example.com", password="correct-horse-9", is_superuser=False
        )


def test_str_is_the_email(user: User) -> None:
    assert str(user) == "ada@example.com"


def test_an_address_renders_as_its_recipient_and_its_first_line(address: Address) -> None:
    """Printed by the console and by the order emails, so this is presentation rather than a debug
    aid: the recipient and the first line are what tell two saved addresses apart at a glance."""
    assert str(address) == "Ada Lovelace, 12 Marylebone Road"


def test_timestamps_are_set_on_both_tables(user: User, address: Address) -> None:
    assert user.created_at is not None
    assert user.updated_at is not None
    assert address.created_at is not None
    assert address.updated_at is not None


def test_display_name_is_optional(user: User) -> None:
    assert user.display_name == ""


def test_a_user_can_have_many_addresses(user: User, address: Address) -> None:
    second = Address.objects.create(
        user=user,
        recipient="Ada Lovelace",
        line1="1 Fitzroy Square",
        city="London",
        postal_code="W1T 5HH",
        country="GB",
    )

    assert list(Address.objects.filter(user=user)) == [address, second]


def test_only_one_address_per_user_can_be_default(user: User) -> None:
    Address.objects.create(
        user=user,
        recipient="Ada",
        line1="A",
        city="London",
        postal_code="1",
        country="GB",
        is_default=True,
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        Address.objects.create(
            user=user,
            recipient="Ada",
            line1="B",
            city="London",
            postal_code="2",
            country="GB",
            is_default=True,
        )


def test_the_default_constraint_is_per_user_not_global(user: User, address: Address) -> None:
    """The negative control for the partial index: another user's default must be fine."""
    other = User.objects.create_user(email="grace@example.com", password="correct-horse-9")

    Address.objects.create(
        user=user,
        recipient="Ada",
        line1="A",
        city="London",
        postal_code="1",
        country="GB",
        is_default=True,
    )
    Address.objects.create(
        user=other,
        recipient="Grace",
        line1="B",
        city="London",
        postal_code="2",
        country="GB",
        is_default=True,
    )

    assert Address.objects.filter(is_default=True).count() == 2


def test_the_default_address_sorts_first(user: User) -> None:
    plain = Address.objects.create(
        user=user, recipient="Ada", line1="A", city="London", postal_code="1", country="GB"
    )
    preferred = Address.objects.create(
        user=user,
        recipient="Ada",
        line1="B",
        city="London",
        postal_code="2",
        country="GB",
        is_default=True,
    )

    assert list(Address.objects.filter(user=user)) == [preferred, plain]


def test_deleting_a_user_cascades_to_their_addresses(user: User, address: Address) -> None:
    user.delete()

    assert Address.objects.count() == 0


def test_an_address_must_have_a_recipient(user: User) -> None:
    incomplete = Address(
        user=user,
        recipient="",
        line1="12 Marylebone Road",
        city="London",
        postal_code="NW1",
        country="GB",
    )

    with pytest.raises(ValidationError):
        incomplete.full_clean()


def test_country_is_capped_at_two_characters(user: User) -> None:
    """ISO-3166 alpha-2. Format validation itself belongs to the API schema (`M2.6`)."""
    wrong = Address(
        user=user,
        recipient="Ada",
        line1="12 Marylebone Road",
        city="London",
        postal_code="NW1",
        country="GBR",
    )

    with pytest.raises(ValidationError):
        wrong.full_clean()


def test_a_refresh_token_renders_its_account_and_whether_it_is_still_live(user: User) -> None:
    """The state word is the point: it makes a list of sessions readable without opening each row,
    and `revoked_at` alone decides it — so a token signed out by `logout` reads the same as one a
    rotation replaced."""
    token = RefreshToken.objects.create(user=user, jti=uuid4(), expires_at=timezone.now())

    assert str(token) == "ada@example.com refresh token (active)"

    token.revoked_at = timezone.now()
    assert str(token) == "ada@example.com refresh token (revoked)"
