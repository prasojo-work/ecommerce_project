from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from accounts.forms import UserChangeForm, UserCreationForm
from accounts.models import Address, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    ordering = ["-date_joined"]
    list_display = ["email", "full_name", "is_staff", "is_active", "date_joined"]
    list_filter = ["is_staff", "is_active", "is_superuser"]
    search_fields = ["email", "full_name"]
    fieldsets = [
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("full_name",)}),
        (
            "Permissions",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    ]
    add_fieldsets = [
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "full_name", "password1", "password2"),
            },
        ),
    ]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["recipient", "city", "province", "is_default", "user"]
    list_filter = ["is_default", "country"]
    search_fields = ["recipient", "city", "postal_code"]
    autocomplete_fields = ["user"]
