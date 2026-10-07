"""Operator console for orders (M5).

Purchase-time snapshots are shown but never editable, and `status` is read-only:
every move goes through `orders.services.transition_order`, so the fulfilment
state machine cannot be bypassed by hand. Orders can be neither created nor
deleted here — they arrive from checkout and are kept forever (`DATA-MODEL.md`,
Phase 2 hook).
"""

from __future__ import annotations

from typing import Any

from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest

from orders.models import Order, OrderItem
from orders.services import InvalidTransitionError, cancel_order, transition_order


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    fields = (
        "product_title_snapshot",
        "variant_name_snapshot",
        "unit_price",
        "quantity",
        "line_total",
    )
    readonly_fields = fields

    def has_add_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False


def _report(modeladmin: Any, request: HttpRequest, moved: int, skipped: int, target: str) -> None:
    if moved:
        modeladmin.message_user(request, f"{moved} order(s) moved to {target}.")
    if skipped:
        modeladmin.message_user(
            request,
            f"{skipped} order(s) could not move to {target} from their current status.",
            level=messages.WARNING,
        )


def _advance(modeladmin: Any, request: HttpRequest, queryset: QuerySet, target: str) -> None:
    moved = skipped = 0
    for order in queryset:
        try:
            transition_order(order, target)
        except InvalidTransitionError:
            skipped += 1
        else:
            moved += 1
    _report(modeladmin, request, moved, skipped, target)


@admin.action(description="Mark as processing")
def mark_processing(modeladmin: Any, request: HttpRequest, queryset: QuerySet) -> None:
    _advance(modeladmin, request, queryset, "processing")


@admin.action(description="Mark as shipped")
def mark_shipped(modeladmin: Any, request: HttpRequest, queryset: QuerySet) -> None:
    _advance(modeladmin, request, queryset, "shipped")


@admin.action(description="Mark as completed")
def mark_completed(modeladmin: Any, request: HttpRequest, queryset: QuerySet) -> None:
    _advance(modeladmin, request, queryset, "completed")


@admin.action(description="Cancel selected orders and return their stock")
def cancel_orders(modeladmin: Any, request: HttpRequest, queryset: QuerySet) -> None:
    cancelled = skipped = 0
    for order in queryset:
        try:
            cancel_order(order)
        except InvalidTransitionError:
            skipped += 1
        else:
            cancelled += 1
    _report(modeladmin, request, cancelled, skipped, "cancelled")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "status", "user", "total", "currency", "created_at")
    list_filter = ("status", "currency")
    search_fields = ("number", "user__email")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    autocomplete_fields = ("user",)
    inlines = [OrderItemInline]
    actions = [mark_processing, mark_shipped, mark_completed, cancel_orders]
    readonly_fields = (
        "number",
        "status",
        "subtotal",
        "shipping_cost",
        "total",
        "currency",
        "shipping_method",
        "shipping_method_name",
        "shipping_address_snapshot",
        "idempotency_key",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (None, {"fields": ("number", "status", "user", "created_at", "updated_at")}),
        ("Money", {"fields": ("subtotal", "shipping_cost", "total", "currency")}),
        (
            "Shipping",
            {
                "fields": (
                    "shipping_method",
                    "shipping_method_name",
                    "shipping_address_snapshot",
                )
            },
        ),
        ("Integrity", {"fields": ("idempotency_key",)}),
    )

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False
