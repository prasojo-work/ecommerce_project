"""The operator console's orders (`M5.1b`, `ADR-0007`, `US-5.4`, `US-5.5`).

`US-5.4` asks the console to show orders and their details; `US-5.5` asks it to change their
status, "valid transitions only", with the change audited. The two are one page here.

An order is a receipt, so the page is read-only: what an operator *does* with an order is move
it, and moving it is `orders/services.py`'s business. Every field is therefore in
`readonly_fields`, `status` included, and the moves are the actions below — which call
`transition_order`, or `cancel_order`, the one function that also knows a cancellation is a
stock event (`ADR-0017`). That is what keeps `ALLOWED_TRANSITIONS` a rule rather than a
suggestion: the console offers no way to assign `status` at all.
"""

from __future__ import annotations

from typing import Any

from django.contrib import admin, messages
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse

from accounts.models import User
from orders.models import Order, OrderEvent, OrderItem, OrderStatus
from orders.services import InvalidTransition, cancel_order, transition_order


class OrderItemInline(admin.TabularInline):
    """`US-5.4`'s detail: the lines as they stood when the order was placed."""

    model = OrderItem
    extra = 0
    can_delete = False
    fields = ("product_name", "variant_name", "unit_price_cents", "quantity", "line_total_cents")
    readonly_fields = fields
    ordering = ("id",)

    def has_add_permission(self, request: HttpRequest, obj: Order | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Order | None = None) -> bool:
        return False


class OrderEventInline(admin.TabularInline):
    """`US-5.5`'s audit trail, visible.

    Read-only for the same reason the trail is append-only on the model: the console shows what
    happened, and the actions below are what writes the next line. `from_status` is empty on the
    one event with no previous state — the order's creation, which checkout wrote.
    """

    model = OrderEvent
    extra = 0
    can_delete = False
    fields = ("created_at", "from_status", "to_status", "actor", "note")
    readonly_fields = fields
    ordering = ("created_at", "id")

    def has_add_permission(self, request: HttpRequest, obj: Order | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Order | None = None) -> bool:
        return False


# Every column of the order, listed once, so the change page has no editable input at all.
ORDER_FIELDS = (
    "number",
    "status",
    "user",
    "email",
    "currency",
    "subtotal_cents",
    "shipping_cents",
    "total_cents",
    "shipping_recipient",
    "shipping_line1",
    "shipping_line2",
    "shipping_city",
    "shipping_region",
    "shipping_postal_code",
    "shipping_country",
    "idempotency_key",
    "created_at",
    "updated_at",
)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """`US-5.4` and `US-5.5`."""

    list_display = ("number", "status", "email", "total_cents", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("number", "email", "shipping_recipient", "shipping_city", "user__email")
    date_hierarchy = "created_at"
    inlines = (OrderItemInline, OrderEventInline)
    readonly_fields = ORDER_FIELDS
    fieldsets = (
        ("Order", {"fields": ("number", "status", "user", "email", "created_at", "updated_at")}),
        ("Totals", {"fields": ("currency", "subtotal_cents", "shipping_cents", "total_cents")}),
        (
            "Shipping address",
            {
                "fields": (
                    "shipping_recipient",
                    "shipping_line1",
                    "shipping_line2",
                    "shipping_city",
                    "shipping_region",
                    "shipping_postal_code",
                    "shipping_country",
                )
            },
        ),
        ("Idempotency", {"fields": ("idempotency_key",), "classes": ("collapse",)}),
    )
    actions = ("mark_paid", "mark_shipped", "mark_delivered", "cancel_orders")

    def has_add_permission(self, request: HttpRequest) -> bool:
        """An order is what checkout writes. There is nothing to add here."""
        return False

    def has_delete_permission(self, request: HttpRequest, obj: Order | None = None) -> bool:
        """A receipt is not a thing to remove. Cancelling is how an order is undone, and that is
        recorded."""
        return False

    def render_change_form(
        self,
        request: HttpRequest,
        context: dict[str, Any],
        add: bool = False,
        change: bool = False,
        form_url: str = "",
        obj: Order | None = None,
    ) -> HttpResponse:
        """Drop the Save button, because there is nothing here it could save.

        Every field is read-only, so a Save would be a control that appears to write and does
        not. Turning the flag off leaves the submit row reading as Close (`US-5.5` moves status
        through the actions, and this is the page saying so).
        """
        context["show_save"] = False
        context["show_save_and_continue"] = False
        return super().render_change_form(request, context, add, change, form_url, obj)

    @admin.action(description="Mark as paid", permissions=["change"])
    def mark_paid(self, request: HttpRequest, queryset: QuerySet[Order]) -> None:
        self._advance(request, queryset, OrderStatus.PAID)

    @admin.action(description="Mark as shipped", permissions=["change"])
    def mark_shipped(self, request: HttpRequest, queryset: QuerySet[Order]) -> None:
        self._advance(request, queryset, OrderStatus.SHIPPED)

    @admin.action(description="Mark as delivered", permissions=["change"])
    def mark_delivered(self, request: HttpRequest, queryset: QuerySet[Order]) -> None:
        self._advance(request, queryset, OrderStatus.DELIVERED)

    @admin.action(description="Cancel and return to stock", permissions=["change"])
    def cancel_orders(self, request: HttpRequest, queryset: QuerySet[Order]) -> None:
        """Cancels through `cancel_order`, which is the only thing that also releases the stock
        the order reserved (`ADR-0017`)."""
        moved: list[str] = []
        refused: list[str] = []
        for order in queryset.order_by("id"):
            try:
                cancel_order(order, actor=self._actor(request), note="Cancelled by an operator.")
            except InvalidTransition as exc:
                refused.append(f"{order.number} — {exc}")
            else:
                moved.append(order.number)
        self._report(request, moved, refused)

    def _advance(self, request: HttpRequest, queryset: QuerySet[Order], to_status: str) -> None:
        """Move each selected order a step, one at a time, and name the ones that would not go.

        `transition_order` raises rather than returning a flag, and a selection is not all or
        nothing: an operator who ticks two orders and finds one already shipped should be told
        which one moved and which did not, not shown an error page. The lock and the event are
        inside the service, so each order here is one transaction.
        """
        moved: list[str] = []
        refused: list[str] = []
        for order in queryset.order_by("id"):
            try:
                transition_order(order, to_status, actor=self._actor(request))
            except InvalidTransition as exc:
                refused.append(f"{order.number} — {exc}")
            else:
                moved.append(order.number)
        self._report(request, moved, refused)

    def _report(self, request: HttpRequest, moved: list[str], refused: list[str]) -> None:
        if moved:
            self.message_user(request, f"Moved: {', '.join(moved)}.", messages.SUCCESS)
        if refused:
            self.message_user(request, f"Left alone: {'; '.join(refused)}", messages.WARNING)

    def _actor(self, request: HttpRequest) -> User | None:
        """Who the trail records, from the operator the console is signed in as.

        `None` means the system did it, so this never invents one: the check is here because the
        framework types `request.user` as possibly anonymous, and behind this console's login it
        is not.
        """
        return request.user if isinstance(request.user, User) else None
