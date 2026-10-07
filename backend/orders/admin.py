from django.contrib import admin

from orders.models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("number", "user", "status", "total", "currency", "created_at")
    list_filter = ("status", "currency")
    search_fields = ("number", "user__email")
    readonly_fields = (
        "number",
        "subtotal",
        "shipping_cost",
        "total",
        "shipping_address_snapshot",
        "idempotency_key",
        "created_at",
        "updated_at",
    )
    inlines = [OrderItemInline]


admin.site.register(OrderItem)
