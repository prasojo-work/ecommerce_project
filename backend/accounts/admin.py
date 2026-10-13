"""The operator console's view of accounts (`M5.1`, `ADR-0007`).

Installing `django.contrib.admin` makes the framework register *its* user model —
`django.contrib.auth.models.User`, the swapped-out default — and not `AUTH_USER_MODEL`. So there is
nothing already in the site for this module to replace or collide with: the registration below is the
first and only one of `accounts.User`.

The admin class is written out rather than inherited whole because Django's own `UserAdmin` is built
for a user with a `username`. Its list columns and fieldsets name fields this model does not have,
which Django reports as a hard `admin.E108` system-check error before a single page renders.

`is_staff` is the operator flag (`DATA-MODEL.md` section 2), so this is also where an operator is
made from the console. `M5.2`'s runbook entry records the command-line alternative.
"""

from __future__ import annotations

from typing import Any

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from accounts.models import User


class OperatorCreationForm(UserCreationForm):
    """The add form, reduced to the fields this model has — and hashing the password.

    `UserCreationForm` is what hashes it. Without it, an operator typed into the admin would be
    stored with a plain-text password, which is worse than not being able to add one at all.
    """

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email", "display_name")


class OperatorChangeForm(UserChangeForm):
    """The change form: `username` gone, `password` kept so the admin's reset link still works."""

    class Meta(UserChangeForm.Meta):
        model = User
        # `django-stubs` types the base's `Meta.fields` as `str`, because its own value is
        # `"__all__"`; Django itself accepts a sequence, so the annotation is what keeps the tuple
        # from being read as a mismatch. `RUNBOOK.md` section 8 records this class of stub gap.
        fields: Any = ("email", "display_name")


@admin.register(User)
class OperatorAdmin(DjangoUserAdmin):
    """This model's own fieldsets, and `is_staff` — the operator flag `ADR-0007` gates access on."""

    form = OperatorChangeForm
    add_form = OperatorCreationForm

    list_display = ("email", "display_name", "is_staff", "is_active", "last_login")
    list_filter = ("is_staff", "is_superuser", "is_active")
    search_fields = ("email", "display_name")
    ordering = ("email",)
    filter_horizontal = ("groups", "user_permissions")
    readonly_fields = ("last_login", "created_at", "updated_at")

    # `Any` rather than the inherited shape: Django types these as loosely as it uses them, and the
    # point of the annotation is to say "deliberately not what the base declares".
    fieldsets: Any = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("display_name",)}),
        ("Operator", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Permissions", {"fields": ("groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets: Any = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "display_name", "password1", "password2"),
            },
        ),
    )
