"""Operator console for the catalog and inventory (M5).

`UX.md` gives the store operator a dedicated "Products / Variants / Inventory"
area. The variant changelist is that inventory surface: stock is editable inline
and a stock-level filter answers the question the operator actually has, which is
"what do I need to reorder?" (`US-7.2`, avoid overselling).
"""

from __future__ import annotations

from typing import Any

from django.contrib import admin
from django.db.models import QuerySet
from django.http import HttpRequest

from catalog.models import Category, Product, ProductImage, ProductVariant

LOW_STOCK_THRESHOLD = 5


class StockLevelFilter(admin.SimpleListFilter):
    title = "stock level"
    parameter_name = "stock"

    def lookups(self, request: HttpRequest, model_admin: Any) -> list[tuple[str, str]]:
        return [
            ("out", "Out of stock (0)"),
            ("low", f"Low stock (1–{LOW_STOCK_THRESHOLD})"),
            ("ok", f"In stock (over {LOW_STOCK_THRESHOLD})"),
        ]

    def queryset(self, request: HttpRequest, queryset: QuerySet) -> QuerySet:
        value = self.value()
        if value == "out":
            return queryset.filter(stock_qty=0)
        if value == "low":
            return queryset.filter(stock_qty__gte=1, stock_qty__lte=LOW_STOCK_THRESHOLD)
        if value == "ok":
            return queryset.filter(stock_qty__gt=LOW_STOCK_THRESHOLD)
        return queryset


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "position", "is_active")
    list_filter = ("is_active",)
    list_editable = ("position", "is_active")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.action(description="Publish selected products")
def publish_products(modeladmin: Any, request: HttpRequest, queryset: QuerySet) -> None:
    updated = queryset.update(status=Product.Status.ACTIVE)
    modeladmin.message_user(request, f"{updated} product(s) published.")


@admin.action(description="Archive selected products")
def archive_products(modeladmin: Any, request: HttpRequest, queryset: QuerySet) -> None:
    updated = queryset.update(status=Product.Status.ARCHIVED)
    modeladmin.message_user(request, f"{updated} product(s) archived.")


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ("sku", "name", "price", "stock_qty", "is_active")


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "status",
        "base_price",
        "currency",
        "updated_at",
    )
    list_filter = ("status", "category", "brand", "currency")
    search_fields = ("title", "brand")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "created_at"
    actions = [publish_products, archive_products]
    inlines = [ProductVariantInline, ProductImageInline]


@admin.action(description="Mark selected variants as active")
def activate_variants(modeladmin: Any, request: HttpRequest, queryset: QuerySet) -> None:
    updated = queryset.update(is_active=True)
    modeladmin.message_user(request, f"{updated} variant(s) activated.")


@admin.action(description="Mark selected variants as inactive")
def deactivate_variants(modeladmin: Any, request: HttpRequest, queryset: QuerySet) -> None:
    updated = queryset.update(is_active=False)
    modeladmin.message_user(request, f"{updated} variant(s) deactivated.")


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    """The inventory view: stock is editable straight from the list."""

    list_display = ("sku", "product", "name", "price_display", "stock_qty", "is_active")
    list_editable = ("stock_qty", "is_active")
    list_filter = ("is_active", StockLevelFilter, "product__category")
    search_fields = ("sku", "name", "product__title")
    autocomplete_fields = ("product",)
    actions = [activate_variants, deactivate_variants]
    list_per_page = 50

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return super().get_queryset(request).select_related("product")

    @admin.display(description="Price")
    def price_display(self, variant: ProductVariant) -> int:
        return variant.effective_price


admin.site.register(ProductImage)
