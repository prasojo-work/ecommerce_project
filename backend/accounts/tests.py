import pytest
from django.db import IntegrityError

from accounts.models import Address, User


@pytest.mark.django_db
def test_create_user_with_email():
    user = User.objects.create_user(email="shopper@example.com", password="secret-pass-123")

    assert user.email == "shopper@example.com"
    assert user.check_password("secret-pass-123")
    assert user.is_staff is False
    assert user.is_superuser is False


@pytest.mark.django_db
def test_create_superuser():
    user = User.objects.create_superuser(email="admin@example.com", password="secret-pass-123")

    assert user.is_staff is True
    assert user.is_superuser is True


@pytest.mark.django_db
def test_email_must_be_unique():
    User.objects.create_user(email="dup@example.com", password="secret-pass-123")

    with pytest.raises(IntegrityError):
        User.objects.create_user(email="dup@example.com", password="secret-pass-123")


@pytest.mark.django_db
def test_only_one_default_address_per_user():
    user = User.objects.create_user(email="shopper@example.com", password="secret-pass-123")

    first = Address.objects.create(
        user=user,
        recipient="A",
        phone="0812",
        line1="Jl. One 1",
        city="Jakarta",
        province="DKI",
        postal_code="10110",
        is_default=True,
    )
    second = Address.objects.create(
        user=user,
        recipient="B",
        phone="0813",
        line1="Jl. Two 2",
        city="Bandung",
        province="JB",
        postal_code="40111",
        is_default=True,
    )

    first.refresh_from_db()
    assert first.is_default is False
    assert second.is_default is True
