"""Account models.

Physical design follows `docs/03-architecture/DATA-MODEL.md` section 2: `accounts.user` is the
custom user model the whole application authenticates against, and `accounts.address` holds the
delivery addresses `SCOPE.md` `US-2.5` manages.
"""

from __future__ import annotations

from typing import Any

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models

from core.models import TimeStampedModel


class UserManager(BaseUserManager["User"]):
    """Creates users with a normalised email and a hashed password.

    `use_in_migrations` is set because Django serialises the manager into `accounts.0001_initial`,
    the same way `AbstractUser` does: a migration that shipped without it could not be replayed.
    """

    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra: Any) -> User:
        if not email:
            raise ValueError("An email address is required.")
        user = self.model(email=self.normalize_email(email).lower(), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra: Any) -> User:
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email: str, password: str | None = None, **extra: Any) -> User:
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        if extra.get("is_staff") is not True:
            raise ValueError("A superuser must have is_staff=True.")
        if extra.get("is_superuser") is not True:
            raise ValueError("A superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra)

    def get_by_natural_key(self, username: str | None) -> User:
        """Case-insensitive lookup by email.

        `django.contrib.auth.authenticate()` reaches the user through this method, so it — not
        every caller remembering to normalise the address first — is what makes
        `Ada@Example.com` able to sign in as `ada@example.com`.

        The identifier is nullable because the base class accepts `None`; an empty one simply
        fails to match, which is what a failed sign-in should do.
        """
        return self.get(email=(username or "").strip().lower())


# `django-stubs` declares a nested `Meta` on both `AbstractBaseUser` and `PermissionsMixin` and
# types the two nominally, so every custom user model built the documented way — `AbstractBaseUser`
# plus `PermissionsMixin` — is reported as an incompatible override, whether or not it declares a
# `Meta` of its own. `RUNBOOK.md` section 8 records the limitation; the two directives below are
# its scoped cost, and neither hides a real problem.
class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):  # pyright: ignore[reportIncompatibleVariableOverride]
    """The custom user model: email is the identifier and there is no `username`.

    `DATA-MODEL.md` asks for a case-insensitively unique `email`, which Postgres expresses as a
    `citext` column. `citext` is an extension, and the test suite runs on SQLite, so the address is
    lower-cased on the way in by `UserManager` and lower-cased again on the way out by
    `get_by_natural_key`. Uniqueness then follows from an ordinary unique constraint instead of
    from an extension — one less thing that behaves differently on the two backends.

    `is_staff` is the operator flag `DATA-MODEL.md` describes. It currently selects nothing,
    because `django.contrib.admin` is not installed yet; it is here so the column exists before
    the operator console (`ADR-0007`) needs it.
    """

    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"

    class Meta(TimeStampedModel.Meta):  # pyright: ignore[reportIncompatibleVariableOverride]
        ordering = ("email",)

    def __str__(self) -> str:
        return self.email


class Address(TimeStampedModel):
    """A delivery address belonging to exactly one user (`US-2.5`).

    `label`, `line2`, `region` and `phone` are optional because real addresses do not always have
    them; `recipient` and the rest are required because checkout cannot ship without them.

    The constraint below is the "at most one default per user" partial unique index
    `DATA-MODEL.md` asks for. It is enforced in the database rather than in application code
    because a second default is a real inconsistency rather than a display problem: checkout has
    to pick one address without asking which of the two defaults won.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    label = models.CharField(max_length=60, blank=True)
    recipient = models.CharField(max_length=120)
    line1 = models.CharField(max_length=120)
    line2 = models.CharField(max_length=120, blank=True)
    city = models.CharField(max_length=120)
    region = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=32)
    country = models.CharField(max_length=2)
    phone = models.CharField(max_length=32, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta(TimeStampedModel.Meta):
        ordering = ("-is_default", "id")
        constraints = (
            models.UniqueConstraint(
                fields=("user",),
                condition=models.Q(is_default=True),
                name="unique_default_address_per_user",
            ),
        )

    def __str__(self) -> str:
        return f"{self.recipient}, {self.line1}"
